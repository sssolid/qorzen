from __future__ import annotations
import abc
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Generic

from PySide6.QtCore import QObject
from qorzen.ui.integration import UIIntegration


@runtime_checkable
class PluginInterface(Protocol):
    """Protocol defining the interface for Qorzen plugins.

    All plugins must implement this interface to be compatible with
    the Qorzen plugin system.
    """

    # Plugin metadata properties
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]

    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any,
                   file_manager: Any, thread_manager: Any, **kwargs: Any) -> None:
        """Initialize the plugin with the provided managers.

        Args:
            event_bus: Event bus manager for subscribing to and publishing events
            logger_provider: Logger provider for creating plugin-specific loggers
            config_provider: Configuration provider for accessing application config
            file_manager: File manager for file operations
            thread_manager: Thread manager for background tasks
            **kwargs: Additional managers
        """
        ...

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Set up UI components when UI is ready.

        This method is called by the plugin system when the UI is ready.
        Plugins should implement this method to add their UI components.

        Args:
            ui_integration: UI integration interface
        """
        ...

    def shutdown(self) -> None:
        """Shut down the plugin.

        This method is called when the plugin is being unloaded.
        Plugins should perform any necessary cleanup here.
        """
        ...


class BasePlugin(QObject):
    """Base class for Qorzen plugins.

    This class provides a base implementation of the PluginInterface
    that plugins can inherit from.
    """

    # Plugin metadata properties (must be overridden by subclasses)
    name: str = "base_plugin"
    version: str = "0.0.0"
    description: str = "Base plugin"
    author: str = "Unknown"
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._initialized = False
        self._event_bus = None
        self._logger = None
        self._config = None
        self._file_manager = None
        self._thread_manager = None
        self._database_manager = None
        self._remote_service_manager = None
        self._security_manager = None
        self._api_manager = None
        self._cloud_manager = None

    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any,
                   file_manager: Any, thread_manager: Any, database_manager: Any, remote_services_manager: Any, security_manager: Any, api_manager: Any, cloud_manager: Any) -> None:
        """Initialize the plugin with the provided managers.

        Args:
            event_bus: Event bus manager for subscribing to and publishing events
            logger_provider: Logger provider for creating plugin-specific loggers
            config_provider: Configuration provider for accessing application config
            file_manager: File manager for file operations
            thread_manager: Thread manager for background tasks
            database_manager: Database manager for database operations
            remote_services_manager: Remote services manager for remote service operations
            security_manager: Security manager for security operations
            api_manager: API manager for API operations
            cloud_manager: Cloud manager for cloud operations
            **kwargs: Additional managers
        """
        self._event_bus = event_bus
        self._logger = logger_provider.get_logger(self.name)
        self._config = config_provider
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._database_manager = database_manager
        self._remote_service_manager = remote_services_manager
        self._security_manager = security_manager
        self._api_manager = api_manager
        self._cloud_manager = cloud_manager
        self._initialized = True

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Set up UI components when UI is ready.

        This method is called by the plugin system when the UI is ready.
        Override this method to add UI components.

        Args:
            ui_integration: UI integration interface
        """
        # Base implementation does nothing
        pass

    def shutdown(self) -> None:
        """Shut down the plugin.

        This method is called when the plugin is being unloaded.
        Perform any necessary cleanup here.
        """
        self._initialized = False

    def status(self) -> Dict[str, Any]:
        """Get the status of the plugin.

        Returns:
            Dictionary with status information
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'initialized': self._initialized
        }