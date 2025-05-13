from __future__ import annotations
import asyncio
import importlib
import logging
import os
import signal
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, cast, T

from qorzen.core.base import QorzenManager, BaseManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.dependency_manager import DependencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory
from qorzen.core.plugin_isolation_manager import PluginIsolationManager, PluginIsolationLevel
from qorzen.utils.exceptions import ApplicationError


class ApplicationCore:
    """The main application core with async support.

    Manages the lifecycle of all core components and provides
    a clean architecture for plugin integration.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the application core.

        Args:
            config_path: Optional path to configuration file
        """
        self._config_path = config_path
        self._managers: Dict[str, BaseManager] = {}
        self._initialized = False
        self._logger: Optional[logging.Logger] = None
        self._dependency_manager: Optional[DependencyManager] = None
        self._shutdown_event = asyncio.Event()
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._ui_integration = None

    async def initialize(self, progress_callback: Optional[callable] = None) -> None:
        """Initialize the application core asynchronously.

        Args:
            progress_callback: Optional callback for initialization progress

        Raises:
            ApplicationError: If initialization fails
        """
        try:
            # Store the main event loop
            self._main_loop = asyncio.get_running_loop()

            # Create and initialize managers in dependency order
            await self._init_dependency_manager()
            await self._init_config_manager()
            await self._init_logging_manager()
            await self._init_concurrency_manager()
            await self._init_event_bus_manager()
            await self._init_file_manager()
            await self._init_resource_monitoring_manager()
            await self._init_database_manager()
            await self._init_security_manager()
            await self._init_api_manager()
            await self._init_cloud_manager()
            await self._init_task_manager()
            await self._init_plugin_isolation_manager()
            await self._init_plugin_manager()

            # Initialize all managers in correct dependency order
            await self._dependency_manager.initialize_all()

            self._initialized = True

            if self._logger:
                self._logger.info('Qorzen initialization complete')

            # Publish system started event
            event_bus_manager = self.get_manager('event_bus_manager')
            if event_bus_manager:
                await event_bus_manager.publish(
                    event_type='system/started',
                    source='app_core',
                    payload={'version': self._get_version()}
                )

        except Exception as e:
            if self._logger:
                self._logger.error(f'Failed to initialize Qorzen: {str(e)}', exc_info=True)
            else:
                print(f'Failed to initialize Qorzen: {str(e)}')
                traceback.print_exc()

            raise ApplicationError(f'Failed to initialize application: {str(e)}') from e

    async def _init_dependency_manager(self) -> None:
        """Initialize the dependency manager."""
        self._dependency_manager = DependencyManager()
        await self._dependency_manager.initialize()
        self._managers['dependency_manager'] = self._dependency_manager

    async def _init_config_manager(self) -> None:
        """Initialize the configuration manager."""
        # Import here to avoid circular imports
        from qorzen.core.config_manager import ConfigManager

        config_manager = ConfigManager(config_path=self._config_path)
        # Register with no dependencies
        self._dependency_manager.register_manager(config_manager)
        self._managers['config_manager'] = config_manager

    async def _init_logging_manager(self) -> None:
        """Initialize the logging manager."""
        # Import here to avoid circular imports
        from qorzen.core.logging_manager import LoggingManager

        config_manager = self.get_manager('config_manager')
        logging_manager = LoggingManager(config_manager)
        # Register with config dependency
        self._dependency_manager.register_manager(
            logging_manager,
            dependencies=['config_manager']
        )
        self._managers['logging_manager'] = logging_manager
        self._logger = logging_manager.get_logger('app_core')

    async def _init_concurrency_manager(self) -> None:
        """Initialize the concurrency manager."""
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')

        concurrency_manager = ConcurrencyManager(config_manager, logging_manager)
        # Register with config and logging dependencies
        self._dependency_manager.register_manager(
            concurrency_manager,
            dependencies=['config_manager', 'logging_manager']
        )
        self._managers['concurrency_manager'] = concurrency_manager

    async def _init_event_bus_manager(self) -> None:
        """Initialize the event bus manager."""
        # Import here to avoid circular imports
        from qorzen.core.event_bus_manager import EventBusManager

        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        concurrency_manager = self.get_manager('concurrency_manager')

        event_bus_manager = EventBusManager(
            config_manager,
            logging_manager,
            concurrency_manager
        )
        # Register with dependencies
        self._dependency_manager.register_manager(
            event_bus_manager,
            dependencies=['config_manager', 'logging_manager', 'concurrency_manager']
        )
        self._managers['event_bus_manager'] = event_bus_manager

    async def _init_file_manager(self) -> None:
        """Initialize the file manager."""
        # Import here to avoid circular imports
        from qorzen.core.file_manager import FileManager

        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')

        file_manager = FileManager(config_manager, logging_manager)
        # Register with dependencies
        self._dependency_manager.register_manager(
            file_manager,
            dependencies=['config_manager', 'logging_manager']
        )
        self._managers['file_manager'] = file_manager

    async def _init_resource_monitoring_manager(self) -> None:
        """Initialize the resource monitoring manager."""
        # Import here to avoid circular imports
        from qorzen.core.resource_monitoring_manager import ResourceMonitoringManager

        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        event_bus = self.get_manager('event_bus_manager')
        concurrency_manager = self.get_manager('concurrency_manager')

        resource_monitoring_manager = ResourceMonitoringManager(
            config_manager,
            logging_manager,
            event_bus,
            concurrency_manager
        )
        # Register with dependencies
        self._dependency_manager.register_manager(
            resource_monitoring_manager,
            dependencies=['config_manager', 'logging_manager', 'event_bus_manager', 'concurrency_manager']
        )
        self._managers['resource_monitoring_manager'] = resource_monitoring_manager

    async def _init_database_manager(self) -> None:
        """Initialize the database manager."""
        # Import here to avoid circular imports
        from qorzen.core.database_manager import DatabaseManager

        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')

        database_manager = DatabaseManager(config_manager, logging_manager)
        # Register with dependencies
        self._dependency_manager.register_manager(
            database_manager,
            dependencies=['config_manager', 'logging_manager']
        )
        self._managers['database_manager'] = database_manager

    async def _init_security_manager(self) -> None:
        """Initialize the security manager."""
        # Import here to avoid circular imports
        from qorzen.core.security_manager import SecurityManager

        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        event_bus = self.get_manager('event_bus_manager')
        database = self.get_manager('database_manager')

        security_manager = SecurityManager(
            config_manager,
            logging_manager,
            event_bus,
            database
        )
        # Register with dependencies
        self._dependency_manager.register_manager(
            security_manager,
            dependencies=['config_manager', 'logging_manager', 'event_bus_manager', 'database_manager']
        )
        self._managers['security_manager'] = security_manager

    async def _init_api_manager(self) -> None:
        """Initialize the API manager."""
        # Import here to avoid circular imports
        from qorzen.core.api_manager import APIManager

        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        security = self.get_manager('security_manager')
        event_bus = self.get_manager('event_bus_manager')
        concurrency_manager = self.get_manager('concurrency_manager')

        api_manager = APIManager(
            config_manager,
            logging_manager,
            security,
            event_bus,
            concurrency_manager
        )
        # Register with dependencies
        self._dependency_manager.register_manager(
            api_manager,
            dependencies=[
                'config_manager', 'logging_manager', 'security_manager',
                'event_bus_manager', 'concurrency_manager'
            ]
        )
        self._managers['api_manager'] = api_manager

    async def _init_cloud_manager(self) -> None:
        """Initialize the cloud manager."""
        # Import here to avoid circular imports
        from qorzen.core.cloud_manager import CloudManager

        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        file_manager = self.get_manager('file_manager')

        cloud_manager = CloudManager(
            config_manager,
            logging_manager,
            file_manager
        )
        # Register with dependencies
        self._dependency_manager.register_manager(
            cloud_manager,
            dependencies=['config_manager', 'logging_manager', 'file_manager']
        )
        self._managers['cloud_manager'] = cloud_manager

    async def _init_task_manager(self) -> None:
        """Initialize the task manager."""
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        event_bus = self.get_manager('event_bus_manager')
        concurrency_manager = self.get_manager('concurrency_manager')

        task_manager = TaskManager(
            concurrency_manager,
            event_bus,
            logging_manager,
            config_manager
        )
        # Register with dependencies
        self._dependency_manager.register_manager(
            task_manager,
            dependencies=[
                'config_manager', 'logging_manager', 'event_bus_manager', 'concurrency_manager'
            ]
        )
        self._managers['task_manager'] = task_manager

    async def _init_plugin_isolation_manager(self) -> None:
        """Initialize the plugin isolation manager."""
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        concurrency_manager = self.get_manager('concurrency_manager')

        plugin_isolation_manager = PluginIsolationManager(
            concurrency_manager,
            logging_manager,
            config_manager
        )
        # Register with dependencies
        self._dependency_manager.register_manager(
            plugin_isolation_manager,
            dependencies=['config_manager', 'logging_manager', 'concurrency_manager']
        )
        self._managers['plugin_isolation'] = plugin_isolation_manager

    async def _init_plugin_manager(self) -> None:
        """Initialize the plugin manager."""
        # Import here to avoid circular imports
        from qorzen.core.plugin_manager import PluginManager

        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        event_bus = self.get_manager('event_bus_manager')
        file_manager = self.get_manager('file_manager')
        task_manager = self.get_manager('task_manager')
        plugin_isolation = self.get_manager('plugin_isolation_manager')

        plugin_manager = PluginManager(
            application_core=self,
            config_manager=config_manager,
            logger_manager=logging_manager,
            event_bus_manager=event_bus,
            file_manager=file_manager,
            task_manager=task_manager,
            plugin_isolation_manager=plugin_isolation
        )
        # Register with dependencies
        self._dependency_manager.register_manager(
            plugin_manager,
            dependencies=[
                'config_manager', 'logging_manager', 'event_bus_manager', 'file_manager',
                'task_manager', 'plugin_isolation_manager'
            ]
        )
        self._managers['plugin_manager'] = plugin_manager

    def get_manager(self, name: str) -> Optional[BaseManager]:
        """Get a manager by name.

        Args:
            name: Name of the manager

        Returns:
            The manager or None if not found
        """
        return self._managers.get(name)

    def get_manager_typed(self, name: str, manager_type: Type[T]) -> Optional[T]:
        """Get a manager by name with type checking.

        Args:
            name: Name of the manager
            manager_type: Type of the manager

        Returns:
            The manager or None if not found
        """
        manager = self._managers.get(name)
        if manager and isinstance(manager, manager_type):
            return cast(T, manager)
        return None

    async def shutdown(self) -> None:
        """Shutdown the application core.

        Shuts down all managers in reverse dependency order.

        Raises:
            ApplicationError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            if self._logger:
                self._logger.info('Shutting down Qorzen')

            # Shutdown all managers through the dependency manager
            if self._dependency_manager:
                await self._dependency_manager.shutdown()

            self._managers.clear()
            self._initialized = False

            if self._logger:
                self._logger.info('Qorzen shutdown complete')

            self._shutdown_event.set()
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error during shutdown: {str(e)}', exc_info=True)
            else:
                print(f'Error during shutdown: {str(e)}')
                traceback.print_exc()

            raise ApplicationError(f'Failed to shutdown application: {str(e)}') from e

    def set_ui_integration(self, ui_integration: Any) -> None:
        """Set the UI integration.

        Args:
            ui_integration: UI integration object
        """
        self._ui_integration = ui_integration

        # Notify the event bus
        event_bus = self.get_manager('event_bus_manager')
        if event_bus and self._initialized:
            asyncio.create_task(
                event_bus.publish(
                    event_type='ui/ready',
                    source='app_core',
                    payload={'ui_integration': ui_integration}
                )
            )

            if self._logger:
                self._logger.info('UI ready event published for plugins')

    def get_ui_integration(self) -> Any:
        """Get the UI integration.

        Returns:
            The UI integration object
        """
        return self._ui_integration

    def is_initialized(self) -> bool:
        """Check if the application is initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    def _get_version(self) -> str:
        """Get the application version.

        Returns:
            Version string
        """
        try:
            # Import as late as possible to avoid circular imports
            from qorzen.__version__ import __version__ as app_version
            return app_version
        except ImportError:
            return '0.1.0'

    async def wait_for_shutdown(self) -> None:
        """Wait for the application to shut down."""
        await self._shutdown_event.wait()

    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        if sys.platform != 'win32':
            # Register SIGTERM handler
            signal.signal(signal.SIGTERM, lambda sig, frame: asyncio.create_task(self._signal_handler(sig)))

        # Register SIGINT handler (Ctrl+C)
        signal.signal(signal.SIGINT, lambda sig, frame: asyncio.create_task(self._signal_handler(sig)))

    async def _signal_handler(self, sig: int) -> None:
        """Handle termination signals.

        Args:
            sig: Signal number
        """
        if self._logger:
            self._logger.info(f'Received signal {sig}, shutting down')

        await self.shutdown()

    async def submit_core_task(
            self,
            func: callable,
            *args: Any,
            name: str = "core_task",
            **kwargs: Any
    ) -> str:
        """Submit a core task for execution.

        Args:
            func: Function to execute
            *args: Positional arguments
            name: Task name
            **kwargs: Keyword arguments

        Returns:
            Task ID

        Raises:
            ApplicationError: If task submission fails
        """
        if not self._initialized:
            raise ApplicationError('Application core not initialized')

        task_manager = self.get_manager('task_manager')
        if not task_manager:
            raise ApplicationError('Task manager not available')

        try:
            return await task_manager.submit_task(
                func=func,
                *args,
                name=name,
                category=TaskCategory.CORE,
                **kwargs
            )
        except Exception as e:
            if self._logger:
                self._logger.error(f'Failed to submit core task: {str(e)}', exc_info=True)
            raise ApplicationError(f'Failed to submit core task: {str(e)}') from e

    def status(self) -> Dict[str, Any]:
        """Get the application status.

        Returns:
            Status dictionary
        """
        status = {
            'name': 'AsyncApplicationCore',
            'initialized': self._initialized,
            'version': self._get_version(),
            'ui_integration': self._ui_integration is not None,
            'managers': {}
        }

        for name, manager in self._managers.items():
            try:
                status['managers'][name] = manager.status()
            except Exception as e:
                status['managers'][name] = {
                    'error': f'Failed to get status: {str(e)}',
                    'initialized': getattr(manager, 'initialized', False),
                    'healthy': getattr(manager, 'healthy', False)
                }

        return status