"""
Asynchronous Remote Services Manager for managing external service connections.

This module provides classes for managing connections to various remote services
with support for different protocols and asynchronous operations.
"""

from __future__ import annotations

import abc
import asyncio
import importlib
import json
import urllib.parse
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError


class ServiceProtocol(str, Enum):
    """Supported remote service protocols."""
    HTTP = 'http'
    HTTPS = 'https'
    GRPC = 'grpc'
    SOAP = 'soap'
    CUSTOM = 'custom'


class RemoteService(abc.ABC):
    """Base class for remote services."""

    def __init__(
            self,
            name: str,
            protocol: ServiceProtocol,
            base_url: str,
            timeout: float = 30.0,
            max_retries: int = 3,
            retry_delay: float = 1.0,
            retry_max_delay: float = 60.0,
            headers: Optional[Dict[str, str]] = None,
            auth: Optional[Dict[str, Any]] = None,
            config: Optional[Dict[str, Any]] = None,
            logger: Any = None
    ) -> None:
        """
        Initialize the remote service.

        Args:
            name: Service name
            protocol: Service protocol
            base_url: Base URL of the service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            retry_max_delay: Maximum delay between retries in seconds
            headers: Default headers to include in requests
            auth: Authentication configuration
            config: Additional service configuration
            logger: Logger instance
        """
        self.name = name
        self.protocol = protocol
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_max_delay = retry_max_delay
        self.headers = headers or {}
        self.auth = auth or {}
        self.config = config or {}
        self._logger = logger
        self._client: Any = None
        self._healthy = False
        self._last_check_time = 0
        self._avg_response_time = 0
        self._request_count = 0
        self._error_count = 0
        self._lock = asyncio.Lock()

    @abc.abstractmethod
    async def get_client(self) -> Any:
        """
        Get the service client.

        Returns:
            Service client instance
        """
        pass

    @abc.abstractmethod
    async def initialize_client(self) -> None:
        """Initialize the service client."""
        pass

    @abc.abstractmethod
    async def check_health(self) -> bool:
        """
        Check the health of the service.

        Returns:
            True if healthy, False otherwise
        """
        pass

    async def status(self) -> Dict[str, Any]:
        """
        Get the status of the service.

        Returns:
            Dict containing service status information
        """
        async with self._lock:
            return {
                'name': self.name,
                'protocol': self.protocol.value,
                'base_url': self.base_url,
                'healthy': self._healthy,
                'avg_response_time': self._avg_response_time,
                'request_count': self._request_count,
                'error_count': self._error_count,
                'error_rate': self._error_count / self._request_count if self._request_count > 0 else 0,
                'last_check_time': self._last_check_time
            }

    async def update_metrics(self, response_time: Optional[float] = None, success: bool = True) -> None:
        """
        Update service metrics.

        Args:
            response_time: Response time in seconds
            success: Whether the request was successful
        """
        async with self._lock:
            self._request_count += 1
            if not success:
                self._error_count += 1
            if response_time is not None:
                if self._avg_response_time == 0:
                    self._avg_response_time = response_time
                else:
                    self._avg_response_time = 0.7 * self._avg_response_time + 0.3 * response_time
            self._last_check_time = time.time()


class HTTPService(RemoteService):
    """HTTP/HTTPS remote service."""

    def __init__(
            self,
            name: str,
            base_url: str,
            protocol: ServiceProtocol = ServiceProtocol.HTTPS,
            **kwargs: Any
    ) -> None:
        """
        Initialize the HTTP service.

        Args:
            name: Service name
            base_url: Base URL of the service
            protocol: Service protocol (HTTP or HTTPS)
            **kwargs: Additional configuration options
        """
        super().__init__(name, protocol, base_url, **kwargs)
        self.health_check_path = kwargs.get('health_check_path', '/health')
        self.verify_ssl = kwargs.get('verify_ssl', True)
        self.follow_redirects = kwargs.get('follow_redirects', True)

    async def get_client(self) -> httpx.AsyncClient:
        """
        Get the HTTP client.

        Returns:
            AsyncClient instance
        """
        if self._client is None:
            await self.initialize_client()
        return self._client

    async def initialize_client(self) -> None:
        """Initialize the HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
            verify=self.verify_ssl,
            headers=self.headers
        )

        if self.auth:
            auth_type = self.auth.get('type', '').lower()
            if auth_type == 'basic':
                self._client.auth = (self.auth.get('username', ''), self.auth.get('password', ''))
            elif auth_type == 'bearer':
                token = self.auth.get('token', '')
                self._client.headers['Authorization'] = f'Bearer {token}'

    async def check_health(self) -> bool:
        """
        Check the health of the service.

        Returns:
            True if healthy, False otherwise
        """
        try:
            client = await self.get_client()
            start_time = time.time()
            response = await client.get(self.health_check_path)
            response_time = time.time() - start_time

            await self.update_metrics(response_time, response.is_success)
            self._healthy = response.is_success

            if not self._healthy and self._logger:
                self._logger.warning(
                    f'Health check failed for {self.name}',
                    extra={
                        'service': self.name,
                        'status_code': response.status_code,
                        'response': response.text[:1000]
                    }
                )

            return self._healthy
        except Exception as e:
            await self.update_metrics(None, False)
            if self._logger:
                self._logger.error(
                    f'Health check error for {self.name}: {str(e)}',
                    extra={'service': self.name, 'error': str(e)}
                )
            self._healthy = False
            return False

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def request(
            self,
            method: str,
            path: str,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Any] = None,
            json_data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Send an HTTP request.

        Args:
            method: HTTP method
            path: Request path
            params: Query parameters
            data: Request data
            json_data: JSON request data
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response

        Raises:
            Exception: If the request fails
        """
        client = await self.get_client()
        kwargs = {}

        if params is not None:
            kwargs['params'] = params
        if data is not None:
            kwargs['data'] = data
        if json_data is not None:
            kwargs['json'] = json_data
        if headers is not None:
            kwargs['headers'] = headers
        if timeout is not None:
            kwargs['timeout'] = timeout

        start_time = time.time()
        try:
            response = await client.request(method, path, **kwargs)
            response_time = time.time() - start_time
            await self.update_metrics(response_time, response.is_success)
            return response
        except Exception as e:
            await self.update_metrics(None, False)
            if self._logger:
                self._logger.error(
                    f'Request error for {self.name}: {str(e)}',
                    extra={
                        'service': self.name,
                        'method': method,
                        'path': path,
                        'error': str(e)
                    }
                )
            raise

    async def get(
            self,
            path: str,
            params: Optional[Dict[str, Any]] = None,
            **kwargs: Any
    ) -> httpx.Response:
        """
        Send a GET request.

        Args:
            path: Request path
            params: Query parameters
            **kwargs: Additional options

        Returns:
            HTTP response
        """
        return await self.request('GET', path, params=params, **kwargs)

    async def post(
            self,
            path: str,
            data: Optional[Any] = None,
            json_data: Optional[Dict[str, Any]] = None,
            **kwargs: Any
    ) -> httpx.Response:
        """
        Send a POST request.

        Args:
            path: Request path
            data: Request data
            json_data: JSON request data
            **kwargs: Additional options

        Returns:
            HTTP response
        """
        return await self.request('POST', path, data=data, json_data=json_data, **kwargs)

    async def put(
            self,
            path: str,
            data: Optional[Any] = None,
            json_data: Optional[Dict[str, Any]] = None,
            **kwargs: Any
    ) -> httpx.Response:
        """
        Send a PUT request.

        Args:
            path: Request path
            data: Request data
            json_data: JSON request data
            **kwargs: Additional options

        Returns:
            HTTP response
        """
        return await self.request('PUT', path, data=data, json_data=json_data, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """
        Send a DELETE request.

        Args:
            path: Request path
            **kwargs: Additional options

        Returns:
            HTTP response
        """
        return await self.request('DELETE', path, **kwargs)

    async def patch(
            self,
            path: str,
            data: Optional[Any] = None,
            json_data: Optional[Dict[str, Any]] = None,
            **kwargs: Any
    ) -> httpx.Response:
        """
        Send a PATCH request.

        Args:
            path: Request path
            data: Request data
            json_data: JSON request data
            **kwargs: Additional options

        Returns:
            HTTP response
        """
        return await self.request('PATCH', path, data=data, json_data=json_data, **kwargs)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class RemoteServicesManager(QorzenManager):
    """Manager for remote services."""

    def __init__(
            self,
            config_manager: Any,
            logger_manager: Any,
            event_bus_manager: Any,
            task_manager: Any
    ) -> None:
        """
        Initialize the remote services manager.

        Args:
            config_manager: Configuration manager instance
            logger_manager: Logger manager instance
            event_bus_manager: Event bus manager instance
            task_manager: Task manager instance
        """
        super().__init__(name='remote_services_manager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('remote_services_manager')
        self._event_bus_manager = event_bus_manager
        self._task_manager = task_manager
        self._services: Dict[str, RemoteService] = {}
        self._services_lock = asyncio.Lock()
        self._health_check_interval = 60.0
        self._health_check_task_id: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the remote services manager."""
        try:
            remote_config = await self._config_manager.get('remote_services', {})
            if not remote_config:
                self._logger.error("Remote configuration not found in configuration")

            if not hasattr(remote_config, 'services'):
                self._logger.warning("Remote configuration does not contain 'services' key")
            if not hasattr(remote_config, 'health_check_interval'):
                self._logger.warning("Remote configuration does not contain 'health_check_interval' key")

            services_config = remote_config.get('services', {})
            self._health_check_interval = remote_config.get('health_check_interval', 60.0)

            if not hasattr(services_config, 'enabled'):
                self._logger.warning("Remote configuration does not contain 'enabled' key for services")

            for service_name, service_config in services_config.items():
                if not service_config.get('enabled', True):
                    continue

                try:
                    await self._register_service_from_config(service_name, service_config)
                except Exception as e:
                    self._logger.error(
                        f'Failed to register service {service_name}: {str(e)}',
                        extra={'service': service_name, 'error': str(e)}
                    )

            await self._event_bus_manager.subscribe(
                event_type='remote_service/register',
                callback=self._on_service_register_event,
                subscriber_id='remote_manager'
            )

            await self._event_bus_manager.subscribe(
                event_type='remote_service/unregister',
                callback=self._on_service_unregister_event,
                subscriber_id='remote_manager'
            )

            await self._config_manager.register_listener(
                'remote_services',
                self._on_config_changed
            )

            await self._schedule_health_checks()

            self._initialized = True
            self._healthy = True
            self._logger.info(f'Remote Services Manager initialized with {len(self._services)} services')
        except Exception as e:
            self._logger.error(f'Failed to initialize Remote Services Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize RemoteServicesManager: {str(e)}',
                manager_name=self.name
            ) from e

    async def _register_service_from_config(
            self,
            service_name: str,
            service_config: Dict[str, Any]
    ) -> None:
        """
        Register a service from configuration.

        Args:
            service_name: Service name
            service_config: Service configuration dictionary

        Raises:
            ValueError: If service configuration is invalid
        """
        service_type = service_config.get('type', 'http').lower()
        protocol_str = service_config.get('protocol', 'https').lower()

        try:
            protocol = ServiceProtocol(protocol_str)
        except ValueError:
            self._logger.warning(
                f"Invalid protocol '{protocol_str}' for service {service_name}, defaulting to HTTPS"
            )
            protocol = ServiceProtocol.HTTPS

        base_url = service_config.get('base_url')
        if not base_url:
            raise ValueError(f'No base URL provided for service {service_name}')

        if service_type == 'http':
            service = HTTPService(
                name=service_name,
                base_url=base_url,
                protocol=protocol,
                timeout=service_config.get('timeout', 30.0),
                max_retries=service_config.get('max_retries', 3),
                retry_delay=service_config.get('retry_delay', 1.0),
                retry_max_delay=service_config.get('retry_max_delay', 60.0),
                headers=service_config.get('headers'),
                auth=service_config.get('auth'),
                config=service_config,
                logger=self._logger,
                health_check_path=service_config.get('health_check_path', '/health'),
                verify_ssl=service_config.get('verify_ssl', True),
                follow_redirects=service_config.get('follow_redirects', True)
            )
        else:
            raise ValueError(f'Unsupported service type: {service_type}')

        await self.register_service(service)

    async def register_service(self, service: RemoteService) -> None:
        """
        Register a remote service.

        Args:
            service: Remote service instance

        Raises:
            ValueError: If the service is already registered or manager not initialized
        """
        if not self._initialized:
            raise ValueError('Remote Services Manager not initialized')

        async with self._services_lock:
            if service.name in self._services:
                raise ValueError(f"Service '{service.name}' is already registered")
            self._services[service.name] = service

        self._logger.info(f"Registered service '{service.name}' with URL {service.base_url}")

        await self._event_bus_manager.publish(
            event_type='remote_service/registered',
            source='remote_manager',
            payload={
                'service_name': service.name,
                'protocol': service.protocol.value,
                'base_url': service.base_url
            }
        )

    async def unregister_service(self, service_name: str) -> bool:
        """
        Unregister a remote service.

        Args:
            service_name: Name of the service to unregister

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            return False

        async with self._services_lock:
            if service_name not in self._services:
                return False

            service = self._services.pop(service_name)
            await service.close()

        self._logger.info(f"Unregistered service '{service_name}'")

        await self._event_bus_manager.publish(
            event_type='remote_service/unregistered',
            source='remote_manager',
            payload={'service_name': service_name}
        )

        return True

    async def get_service(self, service_name: str) -> Optional[RemoteService]:
        """
        Get a service by name.

        Args:
            service_name: Name of the service

        Returns:
            RemoteService instance or None if not found
        """
        if not self._initialized:
            return None

        async with self._services_lock:
            return self._services.get(service_name)

    async def get_http_service(self, service_name: str) -> Optional[HTTPService]:
        """
        Get an HTTP service by name.

        Args:
            service_name: Name of the service

        Returns:
            HTTPService instance or None if not found or not an HTTP service
        """
        service = await self.get_service(service_name)
        if service is None or not isinstance(service, HTTPService):
            return None
        return service

    async def get_all_services(self) -> Dict[str, RemoteService]:
        """
        Get all registered services.

        Returns:
            Dictionary of service name to RemoteService instance
        """
        if not self._initialized:
            return {}

        async with self._services_lock:
            return dict(self._services)

    async def check_service_health(self, service_name: str) -> bool:
        """
        Check the health of a service.

        Args:
            service_name: Name of the service

        Returns:
            True if healthy, False otherwise
        """
        if not self._initialized:
            return False

        service = await self.get_service(service_name)
        if service is None:
            return False

        try:
            return await service.check_health()
        except Exception as e:
            self._logger.error(
                f"Error checking health of service '{service_name}': {str(e)}",
                extra={'service': service_name, 'error': str(e)}
            )
            return False

    async def check_all_services_health(self) -> Dict[str, bool]:
        """
        Check the health of all services.

        Returns:
            Dictionary of service name to health status
        """
        if not self._initialized:
            return {}

        result = {}
        services = await self.get_all_services()

        for service_name, service in services.items():
            result[service_name] = await self.check_service_health(service_name)

        return result

    async def _health_check_task(self) -> None:
        """Periodic task to check the health of all services."""
        if not self._initialized:
            return

        try:
            health_statuses = await self.check_all_services_health()
            healthy_count = sum(1 for status in health_statuses.values() if status)
            unhealthy_count = len(health_statuses) - healthy_count

            self._logger.debug(f'Health check completed: {healthy_count} healthy, {unhealthy_count} unhealthy')

            await self._event_bus_manager.publish(
                event_type='remote_service/health_check',
                source='remote_manager',
                payload={
                    'services': {
                        name: {'healthy': status} for name, status in health_statuses.items()
                    },
                    'healthy_count': healthy_count,
                    'unhealthy_count': unhealthy_count,
                    'timestamp': time.time()
                }
            )
        except Exception as e:
            self._logger.error(f'Error in health check task: {str(e)}', extra={'error': str(e)})

    async def _schedule_health_checks(self) -> None:
        """Schedule periodic health checks."""
        if self._health_check_task_id is not None:
            await self._task_manager.cancel_task(self._health_check_task_id)

        self._health_check_task_id = await self._task_manager.submit_periodic_task(
            self._health_check_task,
            interval=self._health_check_interval,
            name='service_health_check'
        )

        self._logger.debug(f'Scheduled service health checks with interval {self._health_check_interval}s')

    async def _on_service_register_event(self, event: Any) -> None:
        """
        Handle service registration events.

        Args:
            event: Event instance
        """
        payload = event.payload
        if not isinstance(payload, dict):
            self._logger.error('Invalid service registration event payload')
            return

        service_config = payload.get('service_config')
        service_name = payload.get('service_name')

        if not service_config or not service_name:
            self._logger.error('Missing service_config or service_name in registration event')
            return

        try:
            await self._register_service_from_config(service_name, service_config)
        except Exception as e:
            self._logger.error(
                f"Failed to register service '{service_name}' from event: {str(e)}",
                extra={'service': service_name, 'error': str(e)}
            )

    async def _on_service_unregister_event(self, event: Any) -> None:
        """
        Handle service unregistration events.

        Args:
            event: Event instance
        """
        payload = event.payload
        if not isinstance(payload, dict):
            self._logger.error('Invalid service unregistration event payload')
            return

        service_name = payload.get('service_name')
        if not service_name:
            self._logger.error('Missing service_name in unregistration event')
            return

        await self.unregister_service(service_name)

    async def _on_config_changed(self, key: str, value: Any) -> None:
        """
        Handle configuration changes.

        Args:
            key: Configuration key
            value: New configuration value
        """
        if key == 'remote_services.health_check_interval' and isinstance(value, (int, float)):
            self._health_check_interval = float(value)
            self._logger.info(f'Updated health check interval to {self._health_check_interval}s')
            await self._schedule_health_checks()
        elif key.startswith('remote_services.services.'):
            parts = key.split('.')
            if len(parts) >= 3:
                service_name = parts[2]
                self._logger.warning(
                    f"Service configuration for '{service_name}' changed, restart required for changes to take effect",
                    extra={'service': service_name}
                )

    async def make_request(
            self,
            service_name: str,
            method: str,
            path: str,
            **kwargs: Any
    ) -> Any:
        """
        Make a request to a remote service.

        Args:
            service_name: Name of the service
            method: HTTP method
            path: Request path
            **kwargs: Additional request options

        Returns:
            Response data (JSON parsed or text)

        Raises:
            ValueError: If the service is not found or request fails
        """
        if not self._initialized:
            raise ValueError('Remote Services Manager not initialized')

        service = await self.get_http_service(service_name)
        if service is None:
            raise ValueError(f"Service '{service_name}' not found or not an HTTP service")

        try:
            method = method.upper()

            if method == 'GET':
                response = await service.get(path, **kwargs)
            elif method == 'POST':
                response = await service.post(path, **kwargs)
            elif method == 'PUT':
                response = await service.put(path, **kwargs)
            elif method == 'DELETE':
                response = await service.delete(path, **kwargs)
            elif method == 'PATCH':
                response = await service.patch(path, **kwargs)
            else:
                response = await service.request(method, path, **kwargs)

            response.raise_for_status()

            try:
                return response.json()
            except:
                return response.text
        except Exception as e:
            self._logger.error(
                f"Error calling service '{service_name}': {str(e)}",
                extra={'service': service_name, 'method': method, 'path': path, 'error': str(e)}
            )
            raise ValueError(f"Request to service '{service_name}' failed: {str(e)}")

    async def shutdown(self) -> None:
        """Shutdown the remote services manager."""
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Remote Services Manager')

            if self._health_check_task_id is not None:
                await self._task_manager.cancel_task(self._health_check_task_id)
                self._health_check_task_id = None

            async with self._services_lock:
                for service_name, service in list(self._services.items()):
                    try:
                        await service.close()
                        self._logger.debug(f"Closed connections to service '{service_name}'")
                    except Exception as e:
                        self._logger.error(
                            f"Error closing connections to service '{service_name}': {str(e)}",
                            extra={'service': service_name, 'error': str(e)}
                        )
                self._services.clear()

            await self._event_bus_manager.unsubscribe(subscriber_id='remote_manager')
            await self._config_manager.unregister_listener('remote_services', self._on_config_changed)

            self._initialized = False
            self._healthy = False
            self._logger.info('Remote Services Manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down Remote Services Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down RemoteServicesManager: {str(e)}',
                manager_name=self.name
            ) from e

    async def status(self) -> Dict[str, Any]:
        """
        Get the status of the remote services manager.

        Returns:
            Dict containing status information
        """
        status = await super().status()

        if self._initialized:
            service_statuses = {}

            async with self._services_lock:
                for service_name, service in self._services.items():
                    service_statuses[service_name] = await service.status()

            status.update({
                'services': {
                    'count': len(self._services),
                    'statuses': service_statuses
                },
                'health_check': {
                    'interval': self._health_check_interval,
                    'task_id': self._health_check_task_id
                }
            })

        return status