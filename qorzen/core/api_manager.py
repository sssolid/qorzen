"""
Asynchronous API Manager for handling REST API endpoints.

This module provides a FastAPI-based REST API server with authentication,
rate limiting, and various API endpoints.
"""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, cast, Awaitable

try:
    import fastapi
    import pydantic
    import uvicorn
    from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.routing import APIRouter
    from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
    from pydantic import BaseModel, Field
except ImportError as e:
    fastapi = None
    FastAPI = object
    APIRouter = object
    BaseModel = object
    Field = lambda *args, **kwargs: None  # noqa: E731

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import APIError, ManagerInitializationError, ManagerShutdownError

# Define Pydantic models for API request/response if FastAPI is available
if fastapi:
    class UserLogin(BaseModel):
        """Model for user login request."""
        username: str = Field(..., description='Username or email')
        password: str = Field(..., description='User password')


    class Token(BaseModel):
        """Model for authentication token response."""
        access_token: str = Field(..., description='JWT access token')
        token_type: str = Field(..., description='Token type')
        expires_in: int = Field(..., description='Token expiration in seconds')
        refresh_token: Optional[str] = Field(None, description='JWT refresh token')


    class TokenData(BaseModel):
        """Model for token data."""
        user_id: str = Field(..., description='User ID')
        username: Optional[str] = Field(None, description='Username')
        roles: List[str] = Field(default_factory=list, description='User roles')


    class UserCreate(BaseModel):
        """Model for creating a new user."""
        username: str = Field(..., description='Username')
        email: str = Field(..., description='Email address')
        password: str = Field(..., description='Password')
        roles: List[str] = Field(default_factory=list, description='User roles')
        metadata: Optional[Dict[str, Any]] = Field(None, description='Additional metadata')


    class UserUpdate(BaseModel):
        """Model for updating a user."""
        username: Optional[str] = Field(None, description='Username')
        email: Optional[str] = Field(None, description='Email address')
        password: Optional[str] = Field(None, description='Password')
        roles: Optional[List[str]] = Field(None, description='User roles')
        active: Optional[bool] = Field(None, description='User active status')
        metadata: Optional[Dict[str, Any]] = Field(None, description='Additional metadata')


    class UserResponse(BaseModel):
        """Model for user response."""
        id: str = Field(..., description='User ID')
        username: str = Field(..., description='Username')
        email: str = Field(..., description='Email address')
        roles: List[str] = Field(default_factory=list, description='User roles')
        active: bool = Field(..., description='User active status')
        created_at: str = Field(..., description='Creation timestamp')
        last_login: Optional[str] = Field(None, description='Last login timestamp')
        metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata')


    class PluginResponse(BaseModel):
        """Model for plugin response."""
        name: str = Field(..., description='Plugin name')
        version: str = Field(..., description='Plugin version')
        description: str = Field(..., description='Plugin description')
        author: str = Field(..., description='Plugin author')
        state: str = Field(..., description='Plugin state')
        enabled: bool = Field(..., description='Whether the plugin is enabled')
        dependencies: List[str] = Field(default_factory=list, description='Plugin dependencies')
        metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata')


    class StatusResponse(BaseModel):
        """Model for system status response."""
        name: str = Field(..., description='Component name')
        initialized: bool = Field(..., description='Whether the component is initialized')
        healthy: bool = Field(..., description='Whether the component is healthy')
        managers: Dict[str, Any] = Field(default_factory=dict, description='Manager statuses')
        version: str = Field(..., description='System version')


    class AlertResponse(BaseModel):
        """Model for alert response."""
        id: str = Field(..., description='Alert ID')
        level: str = Field(..., description='Alert level')
        message: str = Field(..., description='Alert message')
        source: str = Field(..., description='Alert source')
        timestamp: str = Field(..., description='Alert timestamp')
        metric_name: Optional[str] = Field(None, description='Metric name')
        metric_value: Optional[float] = Field(None, description='Metric value')
        threshold: Optional[float] = Field(None, description='Alert threshold')
        resolved: bool = Field(..., description='Whether the alert is resolved')
        resolved_at: Optional[str] = Field(None, description='When the alert was resolved')
        metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata')


class APIManager(QorzenManager):
    """Manager for handling REST API endpoints."""

    def __init__(
            self,
            config_manager: Any,
            logger_manager: Any,
            security_manager: Any,
            event_bus_manager: Any,
            concurrency_manager: Any,
            registry: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the API manager.

        Args:
            config_manager: Configuration manager instance
            logger_manager: Logger manager instance
            security_manager: Security manager instance
            event_bus_manager: Event bus manager instance
            concurrency_manager: Concurrency manager instance
            registry: Optional registry of additional services
        """
        super().__init__(name='api_manager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('api_manager')
        self._security_manager = security_manager
        self._event_bus_manager = event_bus_manager
        self._concurrency_manager = concurrency_manager
        self._registry = registry or {}
        self._enabled = True
        self._host = '0.0.0.0'
        self._port = 8000
        self._workers = 4
        self._cors_origins = ['*']
        self._cors_methods = ['*']
        self._cors_headers = ['*']
        self._rate_limit_enabled = True
        self._rate_limit_requests = 100
        self._app: Optional[FastAPI] = None
        self._routers: Dict[str, APIRouter] = {}
        self._oauth2_scheme: Optional[Any] = None
        self._server_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize the API manager."""
        try:
            if not fastapi:
                raise ManagerInitializationError(
                    'FastAPI is not installed. Cannot initialize API Manager.',
                    manager_name=self.name
                )

            api_config = await self._config_manager.get('api', {})
            if not api_config:
                self._logger.error("API configuration not found in configuration")

            self._enabled = api_config.get('enabled', True)

            if not self._enabled:
                self._logger.info('API is disabled in configuration')
                self._initialized = True
                return

            if not hasattr(api_config, 'host'):
                self._logger.warning('Missing "host" configuration for API')
            if not hasattr(api_config, 'port'):
                self._logger.warning('Missing "port" configuration for API')
            if not hasattr(api_config, 'workers'):
                self._logger.warning('Missing "workers" configuration for API')

            self._host = api_config.get('host', '0.0.0.0')
            self._port = api_config.get('port', 8000)
            self._workers = api_config.get('workers', 4)

            cors_config = api_config.get('cors', {})
            if not hasattr(cors_config, 'origins'):
                self._logger.warning('Missing "origins" configuration for API cors')
            if not hasattr(cors_config, 'methods'):
                self._logger.warning('Missing "methods" configuration for API cors')
            if not hasattr(cors_config, 'headers'):
                self._logger.warning('Missing "headers" configuration for API cors')
            self._cors_origins = cors_config.get('origins', ['*'])
            self._cors_methods = cors_config.get('methods', ['*'])
            self._cors_headers = cors_config.get('headers', ['*'])

            rate_limit_config = api_config.get('rate_limit', {})
            if not hasattr(rate_limit_config, 'enabled'):
                self._logger.warning('Missing "enabled" configuration for API rate limit')
            if not hasattr(rate_limit_config, 'requests'):
                self._logger.warning('Missing "requests_per_minute" configuration for API rate limit')
            self._rate_limit_enabled = rate_limit_config.get('enabled', True)
            self._rate_limit_requests = rate_limit_config.get('requests_per_minute', 100)

            self._app = FastAPI(
                title='Qorzen API',
                description='API for the Qorzen platform',
                version='0.1.0',
                docs_url='/api/docs',
                redoc_url='/api/redoc',
                openapi_url='/api/openapi.json'
            )

            self._app.add_middleware(
                CORSMiddleware,
                allow_origins=self._cors_origins,
                allow_methods=self._cors_methods,
                allow_headers=self._cors_headers,
                allow_credentials=True
            )

            if self._rate_limit_enabled:
                await self._add_rate_limiting_middleware()

            self._oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/token')

            await self._register_api_routes()
            await self._setup_exception_handlers()

            await self._config_manager.register_listener('api', self._on_config_changed)

            await self._start_api_server()

            self._initialized = True
            self._healthy = True

            self._logger.info(
                f'API Manager initialized and server running on http://{self._host}:{self._port}'
            )

            await self._event_bus_manager.publish(
                event_type='api/started',
                source='api_manager',
                payload={
                    'host': self._host,
                    'port': self._port,
                    'url': f'http://{self._host}:{self._port}/api'
                }
            )
        except Exception as e:
            self._logger.error(f'Failed to initialize API Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize APIManager: {str(e)}',
                manager_name=self.name
            ) from e

    async def _add_rate_limiting_middleware(self) -> None:
        """Add rate limiting middleware to the API."""
        if not self._app:
            return

        rate_limits: Dict[str, List[float]] = {}
        rate_limit_window = 60.0

        @self._app.middleware('http')
        async def rate_limit_middleware(request: Request, call_next: Callable) -> Any:
            client_ip = request.client.host if request.client else 'unknown'

            if request.url.path.startswith(('/api/docs', '/api/redoc', '/api/openapi.json')):
                return await call_next(request)

            now = time.time()

            if client_ip in rate_limits:
                rate_limits[client_ip] = [
                    ts for ts in rate_limits[client_ip] if now - ts < rate_limit_window
                ]
            else:
                rate_limits[client_ip] = []

            if len(rate_limits[client_ip]) >= self._rate_limit_requests:
                self._logger.warning(
                    f'Rate limit exceeded for {client_ip}',
                    extra={'client_ip': client_ip, 'path': request.url.path}
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        'detail': 'Rate limit exceeded. Please try again later.',
                        'remaining': 0,
                        'reset_after': int(rate_limit_window - (now - rate_limits[client_ip][0]))
                    }
                )

            rate_limits[client_ip].append(now)
            return await call_next(request)

    async def _setup_exception_handlers(self) -> None:
        """Set up exception handlers for the API."""
        if not self._app:
            return

        @self._app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
            self._logger.error(
                f'Unhandled exception in API request: {str(exc)}',
                extra={'path': request.url.path, 'method': request.method, 'error': str(exc)}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={'detail': 'An internal server error occurred. Please try again later.'}
            )

    async def _register_api_routes(self) -> None:
        """Register API routes."""
        if not self._app:
            return

        v1_router = APIRouter(prefix='/api/v1')
        self._routers['v1'] = v1_router

        auth_router = await self._create_auth_router()
        v1_router.include_router(auth_router, prefix='/auth', tags=['Authentication'])

        users_router = await self._create_users_router()
        v1_router.include_router(users_router, prefix='/users', tags=['Users'])

        system_router = await self._create_system_router()
        v1_router.include_router(system_router, prefix='/system', tags=['System'])

        plugins_router = await self._create_plugins_router()
        v1_router.include_router(plugins_router, prefix='/plugins', tags=['Plugins'])

        monitoring_router = await self._create_monitoring_router()
        v1_router.include_router(monitoring_router, prefix='/monitoring', tags=['Monitoring'])

        self._app.include_router(v1_router)

        @self._app.get('/', include_in_schema=False)
        async def root() -> Dict[str, str]:
            return {'name': 'Qorzen API', 'version': '0.1.0', 'docs_url': '/api/docs'}

        @self._app.get('/health', tags=['Health'])
        async def health_check() -> Dict[str, bool]:
            return {'status': 'ok', 'healthy': True}

    async def _create_auth_router(self) -> APIRouter:
        """
        Create authentication router.

        Returns:
            APIRouter instance for authentication routes
        """
        router = APIRouter()

        @router.post('/token', response_model=Token)
        async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
            user_data = await self._security_manager.authenticate_user(
                form_data.username,
                form_data.password
            )
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Incorrect username or password',
                    headers={'WWW-Authenticate': 'Bearer'}
                )
            return {
                'access_token': user_data['access_token'],
                'token_type': user_data['token_type'],
                'expires_in': user_data['expires_in'],
                'refresh_token': user_data['refresh_token']
            }

        @router.post('/refresh', response_model=Token)
        async def refresh(refresh_token: str) -> Dict[str, Any]:
            token_data = await self._security_manager.refresh_token(refresh_token)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid or expired refresh token',
                    headers={'WWW-Authenticate': 'Bearer'}
                )
            return token_data

        @router.post('/revoke')
        async def revoke(token: str) -> Dict[str, bool]:
            success = await self._security_manager.revoke_token(token)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Failed to revoke token'
                )
            return {'success': True}

        @router.get('/me', response_model=UserResponse)
        async def read_users_me(
                current_user: Dict[str, Any] = Depends(self._get_current_user)
        ) -> Dict[str, Any]:
            return current_user

        return router

    async def _create_users_router(self) -> APIRouter:
        """
        Create users router.

        Returns:
            APIRouter instance for user management routes
        """
        router = APIRouter()

        @router.get('/', response_model=List[UserResponse])
        async def get_users(
                current_user: Dict[str, Any] = Depends(self._get_current_admin_user)
        ) -> List[Dict[str, Any]]:
            return await self._security_manager.get_all_users()

        @router.post('/', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
        async def create_user(
                user: UserCreate,
                current_user: Dict[str, Any] = Depends(self._get_current_admin_user)
        ) -> Dict[str, Any]:
            try:
                user_id = await self._security_manager.create_user(
                    username=user.username,
                    email=user.email,
                    password=user.password,
                    roles=[await self._get_user_role(role) for role in user.roles],
                    metadata=user.metadata
                )
                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail='Failed to create user'
                    )
                return await self._security_manager.get_user_info(user_id)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @router.get('/{user_id}', response_model=UserResponse)
        async def get_user(
                user_id: str,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('users.view')
                )
        ) -> Dict[str, Any]:
            user = await self._security_manager.get_user_info(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'User with ID {user_id} not found'
                )
            return user

        @router.put('/{user_id}', response_model=UserResponse)
        async def update_user(
                user_id: str,
                user_update: UserUpdate,
                current_user: Dict[str, Any] = Depends(self._get_current_admin_user)
        ) -> Dict[str, Any]:
            update_data = user_update.dict(exclude_unset=True)
            if 'roles' in update_data:
                update_data['roles'] = [
                    await self._get_user_role(role) for role in update_data['roles']
                ]
            try:
                success = await self._security_manager.update_user(user_id, update_data)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f'Failed to update user {user_id}'
                    )
                return await self._security_manager.get_user_info(user_id)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
        async def delete_user(
                user_id: str,
                current_user: Dict[str, Any] = Depends(self._get_current_admin_user)
        ) -> None:
            try:
                success = await self._security_manager.delete_user(user_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f'Failed to delete user {user_id}'
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        return router

    async def _create_system_router(self) -> APIRouter:
        """
        Create system router.

        Returns:
            APIRouter instance for system management routes
        """
        router = APIRouter()

        @router.get('/status', response_model=StatusResponse)
        async def get_system_status(
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('system.view')
                )
        ) -> Dict[str, Any]:
            if 'app_core' in self._registry:
                return await self._registry['app_core'].status()
            return {
                'name': 'Qorzen',
                'initialized': True,
                'healthy': True,
                'managers': {},
                'version': '0.1.0'
            }

        @router.get('/config/{path:path}')
        async def get_config(
                path: str,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('system.view')
                )
        ) -> Dict[str, Any]:
            if 'config' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Configuration Manager not available'
                )
            value = await self._registry['config'].get(path)
            if value is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'Configuration path {path} not found'
                )
            return {'path': path, 'value': value}

        @router.put('/config/{path:path}')
        async def update_config(
                path: str,
                value: Any,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('system.manage')
                )
        ) -> Dict[str, Any]:
            if 'config' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Configuration Manager not available'
                )
            try:
                await self._registry['config'].set(path, value)
                return {'path': path, 'value': value, 'updated': True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        return router

    async def _create_plugins_router(self) -> APIRouter:
        """
        Create plugins router.

        Returns:
            APIRouter instance for plugin management routes
        """
        router = APIRouter()

        @router.get('/', response_model=List[PluginResponse])
        async def get_plugins(
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('plugins.view')
                )
        ) -> List[Dict[str, Any]]:
            if 'plugin_manager' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Plugin Manager not available'
                )
            return await self._registry['plugin_manager'].get_plugins()

        @router.get('/{plugin_name}', response_model=PluginResponse)
        async def get_plugin(
                plugin_name: str,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('plugins.view')
                )
        ) -> Dict[str, Any]:
            if 'plugin_manager' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Plugin Manager not available'
                )
            plugin = await self._registry['plugin_manager'].get_plugin_info(plugin_name)
            if not plugin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'Plugin {plugin_name} not found'
                )
            return plugin

        @router.post('/{plugin_name}/load')
        async def load_plugin(
                plugin_name: str,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('plugins.manage')
                )
        ) -> Dict[str, Any]:
            if 'plugin_manager' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Plugin Manager not available'
                )
            try:
                success = await self._registry['plugin_manager'].load_plugin(plugin_name)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f'Failed to load plugin {plugin_name}'
                    )
                return {'plugin': plugin_name, 'loaded': True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @router.post('/{plugin_name}/unload')
        async def unload_plugin(
                plugin_name: str,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('plugins.manage')
                )
        ) -> Dict[str, Any]:
            if 'plugin_manager' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Plugin Manager not available'
                )
            try:
                success = await self._registry['plugin_manager'].unload_plugin(plugin_name)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f'Failed to unload plugin {plugin_name}'
                    )
                return {'plugin': plugin_name, 'unloaded': True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @router.post('/{plugin_name}/enable')
        async def enable_plugin(
                plugin_name: str,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('plugins.manage')
                )
        ) -> Dict[str, Any]:
            if 'plugin_manager' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Plugin Manager not available'
                )
            try:
                success = await self._registry['plugin_manager'].enable_plugin(plugin_name)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f'Failed to enable plugin {plugin_name}'
                    )
                return {'plugin': plugin_name, 'enabled': True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @router.post('/{plugin_name}/disable')
        async def disable_plugin(
                plugin_name: str,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('plugins.manage')
                )
        ) -> Dict[str, Any]:
            if 'plugin_manager' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Plugin Manager not available'
                )
            try:
                success = await self._registry['plugin_manager'].disable_plugin(plugin_name)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f'Failed to disable plugin {plugin_name}'
                    )
                return {'plugin': plugin_name, 'disabled': True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        return router

    async def _create_monitoring_router(self) -> APIRouter:
        """
        Create monitoring router.

        Returns:
            APIRouter instance for monitoring routes
        """
        router = APIRouter()

        @router.get('/alerts', response_model=List[AlertResponse])
        async def get_alerts(
                include_resolved: bool = False,
                level: Optional[str] = None,
                metric_name: Optional[str] = None,
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('system.view')
                )
        ) -> List[Dict[str, Any]]:
            if 'monitoring' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Monitoring Manager not available'
                )
            alert_level = None
            if level:
                try:
                    alert_level = getattr(self._registry['monitoring'], 'AlertLevel')(level)
                except (ValueError, AttributeError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f'Invalid alert level: {level}'
                    )
            return await self._registry['monitoring'].get_alerts(
                include_resolved=include_resolved,
                level=alert_level,
                metric_name=metric_name
            )

        @router.get('/diagnostics')
        async def get_diagnostics(
                current_user: Dict[str, Any] = Depends(
                    self._get_current_user_with_permission('system.view')
                )
        ) -> Dict[str, Any]:
            if 'monitoring' not in self._registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='Monitoring Manager not available'
                )
            report = await self._registry['monitoring'].generate_diagnostic_report()
            if 'error' in report:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=report['error']
                )
            return report

        return router

    async def _get_current_user_data(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl='/api/v1/auth/token'))) -> \
    Dict[str, Any]:
        """
        Get current user data from token.

        Args:
            token: JWT token

        Returns:
            User data dictionary

        Raises:
            HTTPException: If token validation fails
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'}
        )
        payload = await self._security_manager.verify_token(token)
        if not payload:
            raise credentials_exception
        user_id = payload.get('sub')
        if not user_id:
            raise credentials_exception
        user_info = await self._security_manager.get_user_info(user_id)
        if not user_info:
            raise credentials_exception
        return user_info

    async def _get_current_user(self, user_data: Dict[str, Any] = Depends(_get_current_user_data)) -> Dict[str, Any]:
        """
        Get current user after validation.

        Args:
            user_data: User data dictionary

        Returns:
            Validated user data

        Raises:
            HTTPException: If user is inactive
        """
        if not user_data.get('active', True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Inactive user',
                headers={'WWW-Authenticate': 'Bearer'}
            )
        return user_data

    async def _get_current_admin_user(self, current_user: Dict[str, Any] = Depends(_get_current_user)) -> Dict[
        str, Any]:
        """
        Get current user and verify admin role.

        Args:
            current_user: Current user data

        Returns:
            User data if admin

        Raises:
            HTTPException: If user is not an admin
        """
        if 'admin' not in current_user.get('roles', []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not enough permissions'
            )
        return current_user

    def _get_current_user_with_permission(self, permission: str) -> Callable:
        """
        Create a dependency for checking user permissions.

        Args:
            permission: Required permission string

        Returns:
            Dependency function
        """

        async def has_permission(
                current_user: Dict[str, Any] = Depends(self._get_current_user)
        ) -> Dict[str, Any]:
            resource, action = permission.split('.')
            user_id = current_user['id']

            if not await self._security_manager.has_permission(user_id, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f'Not enough permissions: {permission}'
                )

            return current_user

        return has_permission

    async def _get_user_role(self, role_name: str) -> Any:
        """
        Get user role by name.

        Args:
            role_name: Role name string

        Returns:
            UserRole enum value

        Raises:
            ValueError: If role is invalid
        """
        try:
            return getattr(self._security_manager.__class__, 'UserRole')(role_name)
        except (ValueError, AttributeError):
            raise ValueError(f'Invalid role: {role_name}')

    async def _run_server(self) -> None:
        """Run the Uvicorn server for the API."""
        if not self._app:
            return

        config = uvicorn.Config(
            app=self._app,
            host=self._host,
            port=self._port,
            log_level='info',
            loop='asyncio'
        )

        server = uvicorn.Server(config)

        # Patch the server shutdown method to set our event
        original_shutdown = server.shutdown

        async def patched_shutdown() -> None:
            await original_shutdown()
            self._shutdown_event.set()

        server.shutdown = patched_shutdown

        # Run the server
        await server.serve()

    async def _start_api_server(self) -> None:
        """Start the API server in a background task."""
        if not self._app:
            return

        self._server_task = asyncio.create_task(self._run_server())

        # We don't await the task here, as it would block until the server is stopped
        # Instead, the task will be awaited during shutdown

    async def _on_config_changed(self, key: str, value: Any) -> None:
        """
        Handle configuration changes.

        Args:
            key: Configuration key
            value: New configuration value
        """
        if key == 'api.enabled':
            self._logger.warning(
                'Changing api.enabled requires restart to take effect',
                extra={'enabled': value}
            )
        elif key == 'api.host' or key == 'api.port' or key == 'api.workers':
            self._logger.warning(
                f'Changing {key} requires restart to take effect',
                extra={key.split('.')[-1]: value}
            )
        elif key.startswith('api.cors.'):
            self._logger.warning(
                f'Changing {key} requires restart to take effect',
                extra={key.split('.')[-1]: value}
            )
        elif key.startswith('api.rate_limit.'):
            self._logger.warning(
                f'Changing {key} requires restart to take effect',
                extra={key.split('.')[-1]: value}
            )

    async def register_api_endpoint(
            self,
            path: str,
            method: str,
            endpoint: Callable,
            tags: Optional[List[str]] = None,
            response_model: Optional[Any] = None,
            dependencies: Optional[List[Any]] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None
    ) -> bool:
        """
        Register a custom API endpoint.

        Args:
            path: Endpoint path
            method: HTTP method
            endpoint: Endpoint handler function
            tags: OpenAPI tags
            response_model: Pydantic response model
            dependencies: FastAPI dependencies
            summary: Endpoint summary
            description: Endpoint description

        Returns:
            True if registered successfully, False otherwise
        """
        if not self._initialized or not self._app:
            return False

        router = self._routers.get('v1', None)
        if not router:
            self._logger.error('Cannot register endpoint: No router available')
            return False

        try:
            kwargs = {}
            if response_model:
                kwargs['response_model'] = response_model
            if dependencies:
                kwargs['dependencies'] = dependencies
            if summary:
                kwargs['summary'] = summary
            if description:
                kwargs['description'] = description

            getattr(router, method.lower())(path, tags=tags or [], **kwargs)(endpoint)

            self._logger.info(
                f'Registered API endpoint: {method} {path}',
                extra={'method': method, 'path': path, 'tags': tags}
            )

            return True
        except Exception as e:
            self._logger.error(
                f'Failed to register API endpoint: {str(e)}',
                extra={'method': method, 'path': path}
            )

            return False

    async def shutdown(self) -> None:
        """Shutdown the API manager."""
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down API Manager')

            # Signal the server to shutdown
            self._shutdown_event.set()

            # If we have a server task, wait for it to complete
            if self._server_task and not self._server_task.done():
                try:
                    await asyncio.wait_for(self._server_task, timeout=5.0)
                except asyncio.TimeoutError:
                    self._logger.warning('API server task did not exit gracefully')
                    self._server_task.cancel()
                    try:
                        await self._server_task
                    except asyncio.CancelledError:
                        pass

            await self._config_manager.unregister_listener('api', self._on_config_changed)

            self._routers.clear()
            self._app = None

            self._initialized = False
            self._healthy = False

            self._logger.info('API Manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down API Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down APIManager: {str(e)}',
                manager_name=self.name
            ) from e

    async def status(self) -> Dict[str, Any]:
        """
        Get the status of the API manager.

        Returns:
            Dict containing status information
        """
        status = await super().status()

        if self._initialized:
            is_server_running = (
                    self._server_task is not None and
                    not self._server_task.done() and
                    not self._shutdown_event.is_set()
            )

            status.update({
                'api': {
                    'enabled': self._enabled,
                    'running': is_server_running,
                    'host': self._host,
                    'port': self._port,
                    'url': f'http://{self._host}:{self._port}/api'
                },
                'endpoints': {
                    'count': sum(len(router.routes) for router in self._routers.values()) if self._routers else 0
                },
                'rate_limit': {
                    'enabled': self._rate_limit_enabled,
                    'requests_per_minute': self._rate_limit_requests
                }
            })

        return status