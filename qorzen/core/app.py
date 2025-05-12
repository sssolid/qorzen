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
from qorzen.core.task_manager import TaskManager
from qorzen.ui.integration import MainWindowIntegration

# Import managers
from qorzen.core import ResourceMonitoringManager
from qorzen.core import APIManager
from qorzen.core import ConfigManager
from qorzen.core import EventBusManager
from qorzen.core import LoggingManager
from qorzen.core import ThreadManager
from qorzen.core import FileManager
from qorzen.core import DatabaseManager
from qorzen.core import PluginManager
from qorzen.core import RemoteServicesManager
from qorzen.core import SecurityManager
from qorzen.core import CloudManager

# Import plugin system components
from qorzen.plugin_system.integration import IntegratedPluginInstaller
from qorzen.plugin_system.repository import PluginRepositoryManager
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.extension import extension_registry
from qorzen.plugin_system.lifecycle import set_logger as set_lifecycle_logger

from qorzen.utils.exceptions import ManagerInitializationError, QorzenError

logger = logging.getLogger(__name__)


class ApplicationCore:
    """Core application class for Qorzen.

    This class manages the lifecycle of the application, initializing and
    shutting down all managers and providing access to them.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the application core.

        Args:
            config_path: Optional path to configuration file
        """
        self._config_path = config_path
        self._managers: Dict[str, QorzenManager] = {}
        self._initialized = False
        self._logger = None
        self._main_window = None
        self._ui_integration = None

    def get_initialization_steps(self, progress_callback):
        steps = []
        total_steps = 15
        index_ref = {'index': 1}  # Use mutable reference to avoid scoping issues

        def wrap(step_fn, name):
            def wrapped():
                current_index = index_ref['index']
                if progress_callback:
                    progress_callback(f'Initializing {name} ({current_index}/{total_steps})',
                                      int(current_index / total_steps * 100))
                step_fn()
                index_ref['index'] += 1

            return wrapped

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

    def finalize_initialization(self):
        import atexit
        import signal

        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        atexit.register(self.shutdown)
        self._initialized = True

        if self._logger:
            self._logger.info('Qorzen initialization complete')

        event_bus_manager = self.get_manager('event_bus')
        if event_bus_manager:
            event_bus_manager.publish(
                event_type=EventType.SYSTEM_STARTED,
                source='app_core',
                payload={'version': self._get_version()}
            )

    def _init_config(self):
        config_manager = ConfigManager(config_path=self._config_path)
        config_manager.initialize()
        self._managers['config'] = config_manager

    def _init_logging(self):
        config = self._managers['config']
        logging_manager = LoggingManager(config)
        logging_manager.initialize()
        self._managers['logging'] = logging_manager
        self._logger = logging_manager.get_logger('app_core')
        self._logger.info('Starting Qorzen initialization')

    def _init_thread_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        thread_manager = ThreadManager(config, logging)
        thread_manager.initialize()
        self._managers['thread_manager'] = thread_manager

    def _init_event_bus(self):
        config = self._managers['config']
        logging = self._managers['logging']
        thread_manager = self._managers['thread_manager']
        event_bus_manager = EventBusManager(config, logging, thread_manager)
        event_bus_manager.initialize()
        self._managers['event_bus'] = event_bus_manager
        logging.set_event_bus_manager(event_bus_manager)

    def _init_file_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        file_manager = FileManager(config, logging)
        file_manager.initialize()
        self._managers['file_manager'] = file_manager

    def _init_resource_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        thread = self._managers['thread_manager']
        resource_manager = ResourceMonitoringManager(config, logging, event_bus, thread)
        resource_manager.initialize()
        self._managers['resource_manager'] = resource_manager

    def _init_database_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        database_manager = DatabaseManager(config, logging)
        database_manager.initialize()
        self._managers['database_manager'] = database_manager

    def _init_remote_services_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        thread = self._managers['thread_manager']
        remote_services_manager = RemoteServicesManager(config, logging, event_bus, thread)
        remote_services_manager.initialize()
        self._managers['remote_services_manager'] = remote_services_manager

    def _init_security_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        database = self._managers['database_manager']
        security_manager = SecurityManager(config, logging, event_bus, database)
        security_manager.initialize()
        self._managers['security_manager'] = security_manager

    def _init_api_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        security = self._managers['security_manager']
        event_bus = self._managers['event_bus']
        thread = self._managers['thread_manager']
        api_manager = APIManager(config, logging, security, event_bus, thread)
        api_manager.initialize()
        self._managers['api_manager'] = api_manager

    def _init_cloud_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        file = self._managers['file_manager']
        cloud_manager = CloudManager(config, logging, file)
        cloud_manager.initialize()
        self._managers['cloud_manager'] = cloud_manager

    def _init_task_manager(self) -> None:
        """Initialize the task management system"""
        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        thread = self._managers['thread_manager']
        task_manager = TaskManager(application_core=self, logger_manager=logging, config_manager=config, thread_manager=thread, event_bus_manager=event_bus)
        task_manager.initialize()
        self._managers['task_manager'] = task_manager

    def _init_plugin_components(self):
        config = self._managers['config']
        repository_manager = self._initialize_plugin_repository(config)
        plugin_verifier = self._initialize_plugin_verifier(config)
        plugin_installer = self._initialize_plugin_installer(config, repository_manager, plugin_verifier)
        self._plugin_repository = repository_manager
        self._plugin_verifier = plugin_verifier
        self._plugin_installer = plugin_installer

    def _configure_extension_registry(self):
        if self._logger:
            extension_registry.logger = lambda msg, level: self._logger.log(level.upper(), msg)

    def _init_plugin_manager(self):
        config = self._managers['config']
        logging = self._managers['logging']
        event_bus = self._managers['event_bus']
        file = self._managers['file_manager']
        thread = self._managers['thread_manager']
        database = self._managers['database_manager']
        remote = self._managers['remote_services_manager']
        security = self._managers['security_manager']
        api = self._managers['api_manager']
        cloud = self._managers['cloud_manager']
        task_manager = self._managers['task_manager']

        plugin_manager = PluginManager(
            application_core=self,
            config_manager=config,
            logger_manager=logging,
            event_bus_manager=event_bus,
            file_manager=file,
            thread_manager=thread,
            database_manager=database,
            remote_service_manager=remote,
            security_manager=security,
            api_manager=api,
            cloud_manager=cloud,
            task_manager=task_manager
        )
        plugin_manager.repository_manager = self._plugin_repository
        plugin_manager.plugin_installer = self._plugin_installer
        plugin_manager.plugin_verifier = self._plugin_verifier
        plugin_manager.initialize()
        self._managers['plugin_manager'] = plugin_manager

    def _initialize_plugin_repository(self, config_manager: ConfigManager) -> PluginRepositoryManager:
        """Initialize the plugin repository manager.

        Args:
            config_manager: Configuration manager

        Returns:
            Plugin repository manager
        """
        plugins_dir = Path(config_manager.get('plugins.directory', 'plugins'))
        repository_config_path = plugins_dir / 'repositories.json'

        repository_manager = PluginRepositoryManager(
            config_file=repository_config_path if repository_config_path.exists() else None,
            logger=lambda msg, level: self._logger.log(level.upper(), msg) if self._logger else None
        )

        return repository_manager

    def _initialize_plugin_verifier(self, config_manager: ConfigManager) -> PluginVerifier:
        """Initialize the plugin verifier.

        Args:
            config_manager: Configuration manager

        Returns:
            Plugin verifier
        """
        return PluginVerifier()

    def _initialize_plugin_installer(self, config_manager: ConfigManager,
                                     repository_manager: PluginRepositoryManager,
                                     verifier: PluginVerifier) -> IntegratedPluginInstaller:
        """Initialize the plugin installer.

        Args:
            config_manager: Configuration manager
            repository_manager: Repository manager
            verifier: Plugin verifier

        Returns:
            Plugin installer
        """
        plugins_dir = Path(config_manager.get('plugins.directory', 'plugins'))

        installer = IntegratedPluginInstaller(
            plugins_dir=plugins_dir,
            repository_manager=repository_manager,
            verifier=verifier,
            logger=lambda msg, level: self._logger.log(level.upper(), msg) if self._logger else None,
            core_version=self._get_version()
        )

        return installer

    def _get_version(self) -> str:
        """Get the application version.

        Returns:
            Version string
        """
        try:
            from qorzen.__version__ import __version__ as app_version
            return app_version
        except ImportError:
            return "0.1.0"

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, self._signal_handler)

        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig: int, frame: Any) -> None:
        """Handle signals for graceful shutdown.

        Args:
            sig: Signal number
            frame: Current stack frame
        """
        if self._logger:
            self._logger.info(f'Received signal {sig}, shutting down')

        self.shutdown()
        sys.exit(0)

    def set_main_window(self, main_window: Any) -> None:
        """Set the main window and publish UI ready event.

        Args:
            main_window: Main window instance
        """
        self._main_window = main_window

        # Create UI integration
        self._ui_integration = MainWindowIntegration(main_window)

        # Publish UI ready event
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
        """Get a manager by name.

        Args:
            name: Manager name

        Returns:
            Manager instance or None if not found
        """
        return self._managers.get(name)

    def shutdown(self) -> None:
        """Shut down the application.

        Shuts down all managers in reverse initialization order.
        """
        if not self._initialized and (not self._managers):
            return

        if self._logger:
            self._logger.info('Shutting down Qorzen')

        # Shut down managers in reverse order
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

        # Clear managers
        self._managers.clear()
        self._initialized = False

        # Unregister shutdown handler
        try:
            atexit.unregister(self.shutdown)
        except Exception:
            pass

        if self._logger:
            self._logger.info('Qorzen shutdown complete')
            self._logger = None

    def status(self) -> Dict[str, Any]:
        """Get application status.

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