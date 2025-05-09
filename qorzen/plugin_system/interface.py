from __future__ import annotations
import abc
import threading
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Generic, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from qorzen.ui.integration import UIIntegration
    from qorzen.core import (
        RemoteServicesManager, SecurityManager, APIManager, CloudManager,
        LoggingManager, ConfigManager, DatabaseManager, EventBusManager,
        FileManager, ThreadManager
    )


@runtime_checkable
class PluginInterface(Protocol):
    """Interface that all plugins must implement.

    This protocol defines the required attributes and methods
    that a plugin must have to be properly loaded by the PluginManager.
    """
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]

    def initialize(self,
                   event_bus: 'EventBusManager',
                   logger_provider: 'LoggingManager',
                   config_provider: 'ConfigManager',
                   file_manager: 'FileManager',
                   thread_manager: 'ThreadManager',
                   database_manager: 'DatabaseManager',
                   remote_services_manager: 'RemoteServicesManager',
                   security_manager: 'SecurityManager',
                   api_manager: 'APIManager',
                   cloud_manager: 'CloudManager',
                   **kwargs: Any) -> None:
        """Initialize the plugin with core services.

        Args:
            event_bus: The event bus manager for publishing/subscribing to events.
            logger_provider: The logging manager for creating loggers.
            config_provider: The configuration manager for accessing configuration.
            file_manager: The file manager for file operations.
            thread_manager: The thread manager for thread operations.
            database_manager: The database manager for database operations.
            remote_services_manager: The remote services manager for remote services.
            security_manager: The security manager for security operations.
            api_manager: The API manager for API operations.
            cloud_manager: The cloud manager for cloud operations.
            **kwargs: Additional keyword arguments.
        """
        ...

    def on_ui_ready(self, ui_integration: 'UIIntegration') -> None:
        """Called when the UI is ready and the plugin can add UI components.

        Args:
            ui_integration: The UI integration object for adding UI components.
        """
        ...

    def shutdown(self) -> None:
        """Called when the plugin is being unloaded."""
        ...


class BasePlugin(QObject):
    """Base class for all plugins.

    Implements the PluginInterface protocol and provides
    common functionality for all plugins.
    """
    # Plugin metadata
    name: str = 'base_plugin'
    version: str = '0.0.0'
    description: str = 'Base plugin'
    author: str = 'Unknown'
    display_name: Optional[str] = None
    dependencies: List[str] = []

    # Signals for plugin events
    initialized = Signal()
    ui_ready = Signal()
    shutdown_started = Signal()
    shutdown_completed = Signal()

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._initialized = False
        self._ui_initialized = False
        self._shutdown = False
        self._lock = threading.RLock()

        # Core services
        self._event_bus: Optional['EventBusManager'] = None
        self._logger: Optional[Any] = None
        self._config: Optional['ConfigManager'] = None
        self._file_manager: Optional['FileManager'] = None
        self._thread_manager: Optional['ThreadManager'] = None
        self._database_manager: Optional['DatabaseManager'] = None
        self._remote_service_manager: Optional['RemoteServicesManager'] = None
        self._security_manager: Optional['SecurityManager'] = None
        self._api_manager: Optional['APIManager'] = None
        self._cloud_manager: Optional['CloudManager'] = None

    def initialize(self,
                   event_bus: 'EventBusManager',
                   logger_provider: 'LoggingManager',
                   config_provider: 'ConfigManager',
                   file_manager: 'FileManager',
                   thread_manager: 'ThreadManager',
                   database_manager: 'DatabaseManager',
                   remote_services_manager: 'RemoteServicesManager',
                   security_manager: 'SecurityManager',
                   api_manager: 'APIManager',
                   cloud_manager: 'CloudManager',
                   **kwargs: Any) -> None:
        """Initialize the plugin with core services.

        Args:
            event_bus: The event bus manager for publishing/subscribing to events.
            logger_provider: The logging manager for creating loggers.
            config_provider: The configuration manager for accessing configuration.
            file_manager: The file manager for file operations.
            thread_manager: The thread manager for thread operations.
            database_manager: The database manager for database operations.
            remote_services_manager: The remote services manager for remote services.
            security_manager: The security manager for security operations.
            api_manager: The API manager for API operations.
            cloud_manager: The cloud manager for cloud operations.
            **kwargs: Additional keyword arguments.
        """
        with self._lock:
            # Check if already initialized
            if self._initialized:
                return

            # Store core services
            self._event_bus = event_bus

            if logger_provider:
                self._logger = logger_provider.get_logger(self.name)

            self._config = config_provider
            self._file_manager = file_manager
            self._thread_manager = thread_manager
            self._database_manager = database_manager
            self._remote_service_manager = remote_services_manager
            self._security_manager = security_manager
            self._api_manager = api_manager
            self._cloud_manager = cloud_manager

            # Mark as initialized
            self._initialized = True

        # Emit signal
        self.initialized.emit()

    def on_ui_ready(self, ui_integration: 'UIIntegration') -> None:
        """Called when the UI is ready and the plugin can add UI components.

        Args:
            ui_integration: The UI integration object for adding UI components.
        """
        with self._lock:
            # Track UI initialization
            self._ui_initialized = True

        # Emit signal
        self.ui_ready.emit()

    def shutdown(self) -> None:
        """Called when the plugin is being unloaded."""
        with self._lock:
            # Check if already shut down
            if self._shutdown:
                return

            # Mark as shutting down
            self._shutdown = True

            # Emit signal
            self.shutdown_started.emit()

            # Reset initialized state
            self._initialized = False
            self._ui_initialized = False

        # Emit completion signal
        self.shutdown_completed.emit()

    def status(self) -> Dict[str, Any]:
        """Get the status of the plugin.

        Returns:
            A dictionary with plugin status information.
        """
        with self._lock:
            return {
                'name': self.name,
                'version': self.version,
                'description': self.description,
                'initialized': self._initialized,
                'ui_initialized': self._ui_initialized,
                'shutdown': self._shutdown
            }