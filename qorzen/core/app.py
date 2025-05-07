from __future__ import annotations
import atexit
import importlib
import signal
import sys
import traceback
from pathlib import Path
import logging
from typing import Any, Dict, List, Optional, Type, cast

from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
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

    def initialize(self) -> None:
        """Initialize the application.

        Initializes all managers and sets up signal handlers.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            # Initialize configuration manager
            config_manager = ConfigManager(config_path=self._config_path)
            config_manager.initialize()
            self._managers['config'] = config_manager

            # Initialize logging manager
            logging_manager = LoggingManager(config_manager)
            logging_manager.initialize()
            self._managers['logging'] = logging_manager
            self._logger = logging_manager.get_logger('app_core')

            self._logger.info('Starting Qorzen initialization')

            # Initialize event bus manager
            event_bus_manager = EventBusManager(config_manager, logging_manager)
            event_bus_manager.initialize()
            self._managers['event_bus'] = event_bus_manager

            # Initialize thread manager
            thread_manager = ThreadManager(config_manager, logging_manager)
            thread_manager.initialize()
            self._managers['thread_manager'] = thread_manager

            # Initialize file manager
            file_manager = FileManager(config_manager, logging_manager)
            file_manager.initialize()
            self._managers['file_manager'] = file_manager

            # Initialize resource manager
            resource_manager = ResourceMonitoringManager(
                config_manager,
                logging_manager,
                event_bus_manager,
                thread_manager
            )
            resource_manager.initialize()
            self._managers['resource_manager'] = resource_manager

            # Initialize database manager
            database_manager = DatabaseManager(config_manager, logging_manager)
            database_manager.initialize()
            self._managers['database_manager'] = database_manager

            # Initialize remote services manager
            remote_services_manager = RemoteServicesManager(
                config_manager,
                logging_manager,
                event_bus_manager,
                thread_manager
            )
            remote_services_manager.initialize()
            self._managers['remote_services_manager'] = remote_services_manager

            # Initialize security manager
            security_manager = SecurityManager(
                config_manager,
                logging_manager,
                event_bus_manager,
                database_manager
            )
            security_manager.initialize()
            self._managers['security_manager'] = security_manager

            # Initialize API manager
            api_manager = APIManager(
                config_manager,
                logging_manager,
                security_manager,
                event_bus_manager,
                thread_manager
            )
            api_manager.initialize()
            self._managers['api_manager'] = api_manager

            # Initialize cloud manager
            cloud_manager = CloudManager(config_manager, logging_manager, file_manager)
            cloud_manager.initialize()
            self._managers['cloud_manager'] = cloud_manager

            # Initialize plugin system components
            repository_manager = self._initialize_plugin_repository(config_manager)
            plugin_verifier = self._initialize_plugin_verifier(config_manager)
            plugin_installer = self._initialize_plugin_installer(
                config_manager,
                repository_manager,
                plugin_verifier
            )

            # Configure extension registry logger
            extension_registry.logger = lambda msg, level: self._logger.log(
                level.upper(),
                msg
            ) if self._logger else None

            # Initialize plugin manager
            plugin_manager = PluginManager(
                application_core=self,
                config_manager=config_manager,
                logger_manager=logging_manager,
                event_bus_manager=event_bus_manager,
                file_manager=file_manager,
                thread_manager=thread_manager,
                database_manager=database_manager,
                remote_service_manager=remote_services_manager,
                security_manager=security_manager,
                api_manager=api_manager,
                cloud_manager=cloud_manager
            )
            plugin_manager.repository_manager = repository_manager
            plugin_manager.plugin_installer = plugin_installer
            plugin_manager.plugin_verifier = plugin_verifier
            plugin_manager.initialize()
            self._managers['plugin_manager'] = plugin_manager

            # Set up signal handlers
            self._setup_signal_handlers()

            # Register shutdown handler
            atexit.register(self.shutdown)

            # Mark as initialized
            self._initialized = True

            self._logger.info('Qorzen initialization complete')

            # Publish system started event
            event_bus_manager.publish(
                event_type=EventType.SYSTEM_STARTED,
                source='app_core',
                payload={'version': self._get_version()}
            )

        except Exception as e:
            if self._logger:
                self._logger.error(f'Initialization failed: {str(e)}')
                self._logger.debug(f'Initialization error details: {traceback.format_exc()}')

            self.shutdown()

            if isinstance(e, QorzenError):
                raise
            else:
                raise ManagerInitializationError(
                    f'Failed to initialize Qorzen: {str(e)}',
                    manager_name='ApplicationCore'
                ) from e

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