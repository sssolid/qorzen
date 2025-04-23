from __future__ import annotations

import atexit
import importlib
import signal
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, cast

from qorzen.core import QorzenManager
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
from qorzen.utils.exceptions import ManagerInitializationError, QorzenError


class ApplicationCore:
    """Core application controller for Qorzen.

    The Application Core is responsible for initializing and managing all the core
    managers that make up the Qorzen system. It handles startup, shutdown,
    and provides access to initialized managers.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the Application Core.

        Args:
            config_path: Optional path to the configuration file. If not provided,
                        the default configuration path will be used.
        """
        self._config_path = config_path
        self._managers: Dict[str, QorzenManager] = {}
        self._initialized = False
        self._logger = None
        self._main_window = None

    def initialize(self) -> None:
        """Initialize the Application Core and all managers.

        Initializes managers in the correct order to handle dependencies.

        Raises:
            ManagerInitializationError: If initialization of any manager fails.
        """
        try:
            # Initialize Configuration Manager first
            config_manager = ConfigManager(config_path=self._config_path)
            config_manager.initialize()
            self._managers["config"] = config_manager

            # Initialize Logging Manager second
            logging_manager = LoggingManager(config_manager)
            logging_manager.initialize()
            self._managers["logging"] = logging_manager

            # Get logger for Application Core
            self._logger = logging_manager.get_logger("app_core")
            self._logger.info("Starting Qorzen initialization")

            # Initialize Event Bus Manager third
            event_bus_manager = EventBusManager(config_manager, logging_manager)
            event_bus_manager.initialize()
            self._managers["event_bus"] = event_bus_manager

            thread_manager = ThreadManager(config_manager, logging_manager)
            thread_manager.initialize()
            self._managers["thread_manager"] = thread_manager

            file_manager = FileManager(config_manager, logging_manager)
            file_manager.initialize()
            self._managers["file_manager"] = file_manager

            resource_manager = ResourceMonitoringManager(config_manager, logging_manager, event_bus_manager, thread_manager)
            resource_manager.initialize()
            self._managers["resource_manager"] = resource_manager

            database_manager = DatabaseManager(config_manager, logging_manager)
            database_manager.initialize()
            self._managers["database_manager"] = database_manager

            remote_services_manager = RemoteServicesManager(config_manager, logging_manager, event_bus_manager, thread_manager)
            remote_services_manager.initialize()
            self._managers["remote_services_manager"] = remote_services_manager

            security_manager = SecurityManager(config_manager, logging_manager, event_bus_manager, database_manager)
            security_manager.initialize()
            self._managers["security_manager"] = security_manager

            api_manager = APIManager(config_manager, logging_manager, security_manager, event_bus_manager, thread_manager)
            api_manager.initialize()
            self._managers["api_manager"] = api_manager

            cloud_manager = CloudManager(config_manager, logging_manager, file_manager)
            cloud_manager.initialize()
            self._managers["cloud_manager"] = cloud_manager

            plugin_manager = PluginManager(config_manager, logging_manager, event_bus_manager, file_manager)
            plugin_manager.initialize()
            self._managers["plugin_manager"] = plugin_manager

            # For example:
            # - Thread Manager
            # - File Manager
            # - Resource Manager
            # - Database Manager
            # - Plugin Manager
            # - Remote Services Manager
            # - Monitoring Manager
            # - Security Manager
            # - API Manager
            # - Cloud Manager

            # Set up signal handlers
            self._setup_signal_handlers()

            # Register shutdown function with atexit
            atexit.register(self.shutdown)

            self._initialized = True
            self._logger.info("Qorzen initialization complete")

        except Exception as e:
            # If logging is initialized, log the error
            if self._logger:
                self._logger.error(f"Initialization failed: {str(e)}")
                self._logger.debug(
                    f"Initialization error details: {traceback.format_exc()}"
                )

            # Shut down any initialized managers
            self.shutdown()

            # Re-raise the exception
            if isinstance(e, QorzenError):
                raise
            else:
                raise ManagerInitializationError(
                    f"Failed to initialize Qorzen: {str(e)}",
                    manager_name="ApplicationCore",
                ) from e

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            # Handle SIGTERM and SIGINT on Unix-like systems
            signal.signal(signal.SIGTERM, self._signal_handler)

        # Handle SIGINT (Ctrl+C) on all platforms
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig: int, frame: Any) -> None:
        """Handle signals for graceful shutdown.

        Args:
            sig: The signal number.
            frame: The current stack frame.
        """
        if self._logger:
            self._logger.info(f"Received signal {sig}, shutting down")

        self.shutdown()
        sys.exit(0)

    def set_main_window(self, main_window: Any) -> None:
        """Set the main window reference and notify plugins.

        Args:
            main_window: The main window instance.
        """
        self._main_window = main_window

        # Publish UI ready event for plugins
        event_bus = self.get_manager("event_bus")
        if event_bus and self._initialized:
            event_bus.publish(
                event_type="ui/ready",
                source="app_core",
                payload={"main_window": main_window}
            )
            if self._logger:
                self._logger.info("UI ready event published for plugins")

    def get_manager(self, name: str) -> Optional[QorzenManager]:
        """Get a manager by name.

        Args:
            name: The name of the manager to retrieve.

        Returns:
            Optional[QorzenManager]: The requested manager, or None if not found.
        """
        return self._managers.get(name)

    def shutdown(self) -> None:
        """Shut down all managers in the reverse order of initialization."""
        if not self._initialized and not self._managers:
            return

        if self._logger:
            self._logger.info("Shutting down Qorzen")

        # Get a list of managers in reverse order for proper shutdown sequence
        managers = list(self._managers.items())
        managers.reverse()

        for name, manager in managers:
            try:
                if manager.initialized:
                    if self._logger:
                        self._logger.debug(f"Shutting down {name} manager")
                    manager.shutdown()
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error shutting down {name} manager: {str(e)}")

        # Clear the managers dictionary
        self._managers.clear()
        self._initialized = False

        # Remove the atexit handler
        try:
            atexit.unregister(self.shutdown)
        except:
            pass

        if self._logger:
            self._logger.info("Qorzen shutdown complete")
            # The logger is now unavailable
            self._logger = None

    def status(self) -> Dict[str, Any]:
        """Get the status of the Application Core and all managers.

        Returns:
            Dict[str, Any]: Status information about the Application Core and all managers.
        """
        status = {
            "name": "ApplicationCore",
            "initialized": self._initialized,
            "managers": {},
        }

        for name, manager in self._managers.items():
            try:
                status["managers"][name] = manager.status()
            except Exception as e:
                status["managers"][name] = {
                    "error": f"Failed to get status: {str(e)}",
                    "initialized": manager.initialized,
                    "healthy": False,
                }

        return status
