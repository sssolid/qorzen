from __future__ import annotations

import atexit
import importlib
import signal
import sys
import traceback
from pathlib import Path
import logging
from typing import Any, Dict, List, Optional, Type, cast, Callable

from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.core.service_locator import ServiceLocator, ManagerType, get_default_locator
from qorzen.ui.integration import MainWindowIntegration

logger = logging.getLogger(__name__)


class ApplicationCore:
    """
    Core application class responsible for managing the application lifecycle.

    This class initializes and manages all system managers, coordinates the
    startup process, and handles shutdown procedures.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize the application core.

        Args:
            config_path: Path to the configuration file
        """
        self._config_path = config_path
        self._managers: Dict[str, QorzenManager] = {}
        self._initialized = False
        self._logger = None
        self._main_window = None
        self._ui_integration = None

        # Initialize service locator
        self._service_locator = get_default_locator()

    def get_initialization_steps(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[
        Callable[[], None]]:
        """
        Get a list of initialization steps for the application.

        Args:
            progress_callback: Callback function for reporting initialization progress

        Returns:
            List of initialization step functions
        """
        steps = []
        total_steps = 15
        index_ref = {'index': 1}

        def wrap(step_fn: Callable[[], None], name: str) -> Callable[[], None]:
            """Wrap an initialization step with progress reporting."""

            def wrapped() -> None:
                current_index = index_ref['index']
                if progress_callback:
                    progress_callback(
                        f'Initializing {name} ({current_index}/{total_steps})',
                        int(current_index / total_steps * 100)
                    )
                step_fn()
                index_ref['index'] += 1

            return wrapped

        # Define initialization steps with progress reporting
        steps.append(wrap(lambda: self._init_config(), 'configuration manager'))
        steps.append(wrap(lambda: self._init_logging(), 'logging manager'))
        steps.append(wrap(lambda: self._init_thread_manager(), 'thread manager'))
        steps.append(wrap(lambda: self._init_event_bus(), 'event bus manager'))
        steps.append(wrap(lambda: self._init_file_manager(), 'file manager'))
        steps.append(wrap(lambda: self._init_resource_manager(), 'resource manager'))
        steps.append(wrap(lambda: self._init_database_manager(), 'database manager'))
        steps.append(wrap(lambda: self._init_remote_services_manager(), 'remote services manager'))
        steps.append(wrap(lambda: self._init_security_manager(), 'security manager'))
        steps.append(wrap(lambda: self._init_api_manager(), 'API manager'))
        steps.append(wrap(lambda: self._init_cloud_manager(), 'cloud manager'))
        steps.append(wrap(lambda: self._init_task_manager(), 'task manager'))
        steps.append(wrap(lambda: self._init_plugin_components(), 'plugin system components'))
        steps.append(wrap(lambda: self._configure_extension_registry(), 'extension registry'))
        steps.append(wrap(lambda: self._init_plugin_manager(), 'plugin manager'))

        return steps

    def finalize_initialization(self) -> None:
        """
        Finalize the initialization process.

        This method sets up signal handlers, registers the shutdown handler,
        and signals that the system is fully initialized.
        """
        import atexit
        import signal

        # Register signal handlers
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Register shutdown handler
        atexit.register(self.shutdown)

        self._initialized = True

        if self._logger:
            self._logger.info('Qorzen initialization complete')

        # Publish system started event
        event_bus_manager = self.get_manager('event_bus')
        if event_bus_manager:
            event_bus_manager.publish(
                event_type=EventType.SYSTEM_STARTED,
                source='app_core',
                payload={'version': self._get_version()}
            )

    def _init_config(self) -> None:
        """Initialize the configuration manager."""
        from qorzen.core.config_manager import ConfigManager

        config_manager = ConfigManager(config_path=self._config_path)
        config_manager.initialize()
        self._managers['config'] = config_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.CONFIG,
            config_manager,
            name='config'
        )

    def _init_logging(self) -> None:
        """Initialize the logging manager."""
        from qorzen.core.logging_manager import LoggingManager

        config = self._managers['config']
        logging_manager = LoggingManager(config)
        logging_manager.initialize()
        self._managers['logging'] = logging_manager
        self._logger = logging_manager.get_logger('app_core')

        # Register with service locator
        self._service_locator.register(
            ManagerType.LOGGING,
            logging_manager,
            name='logging'
        )

        self._logger.info('Starting Qorzen initialization')

    def _init_thread_manager(self) -> None:
        """Initialize the thread manager."""
        from qorzen.core.thread_manager import ThreadManager

        config = self._managers['config']
        logging = self._managers['logging']

        thread_manager = ThreadManager(config, logging)
        thread_manager.initialize()
        self._managers['thread_manager'] = thread_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.THREAD,
            thread_manager,
            name='thread_manager'
        )

    def _init_event_bus(self) -> None:
        """Initialize the event bus manager."""
        from qorzen.core.event_bus_manager import EventBusManager

        config = self._managers['config']
        logging = self._managers['logging']
        thread_manager = self._managers['thread_manager']

        event_bus_manager = EventBusManager(config, logging, thread_manager)
        event_bus_manager.initialize()
        self._managers['event_bus'] = event_bus_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.EVENT_BUS,
            event_bus_manager,
            name='event_bus'
        )

        # Connect event bus to logging for event-based logging
        logging.set_event_bus_manager(event_bus_manager)

    def _init_file_manager(self) -> None:
        """Initialize the file manager."""
        from qorzen.core.file_manager import FileManager

        config = self._managers['config']
        logging = self._managers['logging']

        file_manager = FileManager(config, logging)
        file_manager.initialize()
        self._managers['file_manager'] = file_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.FILE,
            file_manager,
            name='file_manager'
        )

    def _init_resource_manager(self) -> None:
        """Initialize the resource monitoring manager."""
        from qorzen.core.monitoring_manager import ResourceMonitoringManager

        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        thread = self._managers['thread_manager']

        resource_manager = ResourceMonitoringManager(config, logging, event_bus, thread)
        resource_manager.initialize()
        self._managers['resource_manager'] = resource_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.MONITORING,
            resource_manager,
            name='resource_manager'
        )

    def _init_database_manager(self) -> None:
        """Initialize the database manager."""
        from qorzen.core.database_manager import DatabaseManager

        config = self._managers['config']
        logging = self._managers['logging']

        database_manager = DatabaseManager(config, logging)
        database_manager.initialize()
        self._managers['database_manager'] = database_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.DATABASE,
            database_manager,
            name='database_manager'
        )

    def _init_remote_services_manager(self) -> None:
        """Initialize the remote services manager."""
        from qorzen.core.remote_manager import RemoteServicesManager

        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        thread = self._managers['thread_manager']

        remote_services_manager = RemoteServicesManager(config, logging, event_bus, thread)
        remote_services_manager.initialize()
        self._managers['remote_services_manager'] = remote_services_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.REMOTE_SERVICES,
            remote_services_manager,
            name='remote_services_manager'
        )

    def _init_security_manager(self) -> None:
        """Initialize the security manager."""
        from qorzen.core.security_manager import SecurityManager

        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        database = self._managers['database_manager']

        security_manager = SecurityManager(config, logging, event_bus, database)
        security_manager.initialize()
        self._managers['security_manager'] = security_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.SECURITY,
            security_manager,
            name='security_manager'
        )

    def _init_api_manager(self) -> None:
        """Initialize the API manager."""
        from qorzen.core.api_manager import APIManager

        config = self._managers['config']
        logging = self._managers['logging']
        security = self._managers['security_manager']
        event_bus = self._managers['event_bus']
        thread = self._managers['thread_manager']

        api_manager = APIManager(config, logging, security, event_bus, thread)
        api_manager.initialize()
        self._managers['api_manager'] = api_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.API,
            api_manager,
            name='api_manager'
        )

    def _init_cloud_manager(self) -> None:
        """Initialize the cloud manager."""
        from qorzen.core.cloud_manager import CloudManager

        config = self._managers['config']
        logging = self._managers['logging']
        file = self._managers['file_manager']

        cloud_manager = CloudManager(config, logging, file)
        cloud_manager.initialize()
        self._managers['cloud_manager'] = cloud_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.CLOUD,
            cloud_manager,
            name='cloud_manager'
        )

    def _init_task_manager(self) -> None:
        """Initialize the task manager."""
        from qorzen.core.task_manager import TaskManager

        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        thread = self._managers['thread_manager']

        task_manager = TaskManager(
            application_core=self,
            config_manager=config,
            logger_manager=logging,
            event_bus_manager=event_bus,
            thread_manager=thread
        )
        task_manager.initialize()
        self._managers['task_manager'] = task_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.TASK,
            task_manager,
            name='task_manager'
        )

    def _init_plugin_components(self) -> None:
        """Initialize plugin system components."""
        config = self._managers['config']
        repository_manager = self._initialize_plugin_repository(config)
        plugin_verifier = self._initialize_plugin_verifier(config)
        plugin_installer = self._initialize_plugin_installer(config, repository_manager, plugin_verifier)

        self._plugin_repository = repository_manager
        self._plugin_verifier = plugin_verifier
        self._plugin_installer = plugin_installer

    def _configure_extension_registry(self) -> None:
        """Configure the extension registry."""
        from qorzen.plugin_system.extension import extension_registry

        if self._logger:
            extension_registry.logger = lambda msg, level: self._logger.log(level.upper(), msg)

    def _init_plugin_manager(self) -> None:
        """Initialize the plugin manager."""
        from qorzen.core.plugin_manager import PluginManager

        # Create plugin manager with service locator
        plugin_manager = PluginManager(
            application_core=self,
            service_locator=self._service_locator
        )

        # Set up plugin components
        plugin_manager.repository_manager = self._plugin_repository
        plugin_manager.plugin_installer = self._plugin_installer
        plugin_manager.plugin_verifier = self._plugin_verifier

        plugin_manager.initialize()
        self._managers['plugin_manager'] = plugin_manager

        # Register with service locator
        self._service_locator.register(
            ManagerType.PLUGIN,
            plugin_manager,
            name='plugin_manager'
        )

    def _initialize_plugin_repository(self, config_manager: Any) -> Any:
        """
        Initialize the plugin repository manager.

        Args:
            config_manager: Configuration manager

        Returns:
            PluginRepositoryManager instance
        """
        from qorzen.plugin_system.repository import PluginRepositoryManager

        plugins_dir = Path(config_manager.get('plugins.directory', 'plugins'))
        repository_config_path = plugins_dir / 'repositories.json'

        logger_fn = (
            lambda msg, level: self._logger.log(level.upper(), msg)
            if self._logger
            else None
        )

        repository_manager = PluginRepositoryManager(
            config_file=repository_config_path if repository_config_path.exists() else None,
            logger=logger_fn
        )

        return repository_manager

    def _initialize_plugin_verifier(self, config_manager: Any) -> Any:
        """
        Initialize the plugin verifier.

        Args:
            config_manager: Configuration manager

        Returns:
            PluginVerifier instance
        """
        from qorzen.plugin_system.signing import PluginVerifier
        return PluginVerifier()

    def _initialize_plugin_installer(self, config_manager: Any,
                                     repository_manager: Any,
                                     verifier: Any) -> Any:
        """
        Initialize the plugin installer.

        Args:
            config_manager: Configuration manager
            repository_manager: Repository manager
            verifier: Plugin verifier

        Returns:
            IntegratedPluginInstaller instance
        """
        from qorzen.plugin_system.integration import IntegratedPluginInstaller

        plugins_dir = Path(config_manager.get('plugins.directory', 'plugins'))

        logger_fn = (
            lambda msg, level: self._logger.log(level.upper(), msg)
            if self._logger
            else None
        )

        installer = IntegratedPluginInstaller(
            plugins_dir=plugins_dir,
            repository_manager=repository_manager,
            verifier=verifier,
            logger=logger_fn,
            core_version=self._get_version()
        )

        return installer

    def _get_version(self) -> str:
        """
        Get the application version.

        Returns:
            Application version string
        """
        try:
            from qorzen.__version__ import __version__ as app_version
            return app_version
        except ImportError:
            return '0.1.0'

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig: int, frame: Any) -> None:
        """
        Signal handler for clean shutdown.

        Args:
            sig: Signal number
            frame: Current stack frame
        """
        if self._logger:
            self._logger.info(f'Received signal {sig}, shutting down')
        self.shutdown()
        sys.exit(0)

    def set_main_window(self, main_window: Any) -> None:
        """
        Set the main application window.

        Args:
            main_window: Main window instance
        """
        self._main_window = main_window
        self._ui_integration = MainWindowIntegration(main_window)

        event_bus = self.get_manager('event_bus')
        if event_bus and self._initialized:
            event_bus.publish(
                event_type=EventType.UI_READY,
                source='app_core',
                payload={'main_window': main_window}
            )

            if self._logger:
                self._logger.info('UI ready event published for plugins')

    def get_manager(self, name: str) -> Optional[QorzenManager]:
        """
        Get a manager by name.

        Args:
            name: Name of the manager to get

        Returns:
            Manager instance or None if not found
        """
        return self._managers.get(name)

    def shutdown(self) -> None:
        """
        Shutdown the application, cleaning up all resources.
        """
        if not self._initialized and (not self._managers):
            return

        if self._logger:
            self._logger.info('Shutting down Qorzen')

        # Shutdown managers in reverse initialization order
        managers = list(self._managers.items())
        managers.reverse()

        for name, manager in managers:
            try:
                if manager.initialized:
                    if self._logger:
                        self._logger.debug(f'Shutting down {name} manager')
                    manager.shutdown()
            except Exception as e:
                if self._logger:
                    self._logger.error(f'Error shutting down {name} manager: {str(e)}')

        self._managers.clear()
        self._initialized = False

        try:
            atexit.unregister(self.shutdown)
        except Exception:
            pass

        if self._logger:
            self._logger.info('Qorzen shutdown complete')
            self._logger = None

    def status(self) -> Dict[str, Any]:
        """
        Get the current status of the application.

        Returns:
            Dictionary with status information
        """
        status = {
            'name': 'ApplicationCore',
            'initialized': self._initialized,
            'managers': {},
            'version': self._get_version()
        }

        for name, manager in self._managers.items():
            try:
                status['managers'][name] = manager.status()
            except Exception as e:
                status['managers'][name] = {
                    'error': f'Failed to get status: {str(e)}',
                    'initialized': manager.initialized,
                    'healthy': False
                }

        return status