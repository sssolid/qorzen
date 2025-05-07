from __future__ import annotations

"""
InitialDB Plugin for Qorzen framework.

This plugin provides access to vehicle component database information,
allowing users to query and export vehicle parts and specifications.
"""
import logging
from typing import Any, Dict, List, Optional, Union, cast

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget, QMenu, QProgressBar, QHBoxLayout
from PySide6.QtGui import QAction, QIcon

from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, TabComponent
from qorzen.core.config_manager import ConfigManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.file_manager import FileManager
from qorzen.core.thread_manager import ThreadManager
from qorzen.plugin_system.interface import BasePlugin


class DatabaseStatusWidget(QWidget):
    """Widget to display database connection status."""

    update_signal = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the database status widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)

        self._status_label = QLabel("Database Status:")
        self._status_label.setMinimumWidth(120)
        self._layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._layout.addWidget(self._progress_bar)

        self._connection_label = QLabel("Disconnected")
        self._connection_label.setMinimumWidth(100)
        self._layout.addWidget(self._connection_label)

        self.update_signal.connect(self._update_ui)

    def update_status(self, status: Dict[str, Any]) -> None:
        """Update the status display.

        Args:
            status: Status information
        """
        self.update_signal.emit(status)

    @Slot(dict)
    def _update_ui(self, status: Dict[str, Any]) -> None:
        """Update UI with new status.

        Args:
            status: Status information
        """
        connected = status.get("connected", False)
        if connected:
            self._progress_bar.setValue(100)
            self._connection_label.setText("Connected")
            self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        else:
            self._progress_bar.setValue(0)
            self._connection_label.setText("Disconnected")
            self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")


class InitialDBTab(TabComponent):
    """Main tab for the InitialDB plugin."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the InitialDB tab.

        Args:
            parent: Parent widget
        """
        self._widget = QWidget(parent)
        self._layout = QVBoxLayout(self._widget)

        title_label = QLabel("Vehicle Component Database")
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        self._layout.addWidget(title_label)

        self._db_status = DatabaseStatusWidget()
        self._layout.addWidget(self._db_status)

        self._tab_widget = QTabWidget()
        self._layout.addWidget(self._tab_widget)

        self._layout.addStretch()

        self._info_label = QLabel("Use the menu options to query and export vehicle data.")
        self._layout.addWidget(self._info_label)

    def get_widget(self) -> QWidget:
        """Get the widget for this component.

        Returns:
            The widget
        """
        return self._widget

    def on_tab_selected(self) -> None:
        """Called when the tab is selected."""
        pass

    def on_tab_deselected(self) -> None:
        """Called when the tab is deselected."""
        pass

    def update_database_status(self, status: Dict[str, Any]) -> None:
        """Update the database status display.

        Args:
            status: Status information
        """
        self._db_status.update_status(status)


class InitialDBPlugin(BasePlugin):
    """Vehicle Component Database Plugin for Qorzen.

    This plugin provides access to vehicle component database information,
    allowing users to query and export vehicle data.
    """

    name = "initialdb"
    version = "0.2.0"
    description = "Vehicle Component Database Plugin"
    author = "Ryan Serra"
    dependencies = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._event_bus: Optional[EventBusManager] = None
        self._logger: Optional[logging.Logger] = None
        self._config: Optional[ConfigManager] = None
        self._file_manager: Optional[FileManager] = None
        self._thread_manager: Optional[ThreadManager] = None
        self._db_manager: Optional[Any] = None
        self._api_manager: Optional[Any] = None
        self._vehicle_service: Optional[Any] = None
        self._export_service: Optional[Any] = None
        self._tab: Optional[InitialDBTab] = None
        self._tab_index: Optional[int] = None
        self._menu_items: List[QAction] = []
        self._plugin_menu: Optional[QMenu] = None
        self._tools_menu: Optional[QMenu] = None
        self._initialized = False
        self._db_connection_timer = None

    def initialize(
            self,
            event_bus: Any,
            logger_provider: Any,
            config_provider: Any,
            file_manager: Any,
            thread_manager: Any,
            **kwargs: Any
    ) -> None:
        """Initialize the plugin with the provided managers.

        Args:
            event_bus: Event bus for pub/sub
            logger_provider: For creating loggers
            config_provider: Access to configuration
            file_manager: File system operations
            thread_manager: Task scheduling
            **kwargs: Additional dependencies
        """
        self._event_bus = cast(EventBusManager, event_bus)
        self._logger = logger_provider.get_logger(self.name)
        self._config = cast(ConfigManager, config_provider)
        self._file_manager = cast(FileManager, file_manager)
        self._thread_manager = cast(ThreadManager, thread_manager)
        self._db_manager = kwargs.get("database_manager")
        self._api_manager = kwargs.get("api_manager")

        if not self._db_manager:
            self._logger.error("Database manager not available - plugin cannot function")
            return

        if not self._api_manager:
            self._logger.warning("API manager not available - API routes will not be registered")

        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type="plugin_data")
                self._file_manager.ensure_directory(plugin_data_dir.as_posix())
                self._logger.debug(f"Plugin data directory: {plugin_data_dir}")
            except Exception as e:
                self._logger.warning(f"Failed to create plugin data directory: {str(e)}")

        self._logger.info(f"Initializing {self.name} v{self.version} plugin")

        try:
            self._load_settings()
        except Exception as e:
            self._logger.error(f"Error loading settings: {str(e)}")

        try:
            from .services.vehicle_service import VehicleService
            from .services.export_service import ExportService
            from .routes.api import register_api_routes

            self._vehicle_service = VehicleService(
                db_manager=self._db_manager,
                logger=self._logger,
                event_bus=self._event_bus,
                thread_manager=self._thread_manager,
                config=self._config
            )

            self._export_service = ExportService(
                file_manager=self._file_manager,
                logger=self._logger,
                vehicle_service=self._vehicle_service,
                config=self._config
            )

            if self._api_manager:
                register_api_routes(
                    api_manager=self._api_manager,
                    vehicle_service=self._vehicle_service,
                    export_service=self._export_service,
                    logger=self._logger
                )
                self._logger.info("API routes registered")

            self._subscribe_to_events()

            # Schedule periodic database validation
            self._setup_periodic_tasks()

            self._initialized = True
            self._logger.info(f"{self.name} plugin initialized")

            self._event_bus.publish(
                event_type=EventType.PLUGIN_INITIALIZED.value,
                source=self.name,
                payload={
                    "plugin_name": self.name,
                    "version": self.version,
                    "has_ui": True
                }
            )
        except Exception as e:
            self._logger.error(f"Failed to initialize plugin: {str(e)}", exc_info=True)

    def _load_settings(self) -> None:
        """Load plugin settings from configuration."""
        try:
            from .config.settings import DEFAULT_CONNECTION_STRING, DEFAULT_QUERY_LIMIT, MAX_QUERY_LIMIT

            conn_str = self._config.get(f"plugins.{self.name}.connection_string", None)
            if conn_str is None:
                self._config.set(f"plugins.{self.name}.connection_string", DEFAULT_CONNECTION_STRING)
                self._logger.info(f"Set default connection string: {DEFAULT_CONNECTION_STRING}")

            query_limit = self._config.get(f"plugins.{self.name}.default_query_limit", None)
            if query_limit is None:
                self._config.set(f"plugins.{self.name}.default_query_limit", DEFAULT_QUERY_LIMIT)
                self._logger.info(f"Set default query limit: {DEFAULT_QUERY_LIMIT}")

            max_limit = self._config.get(f"plugins.{self.name}.max_query_limit", None)
            if max_limit is None:
                self._config.set(f"plugins.{self.name}.max_query_limit", MAX_QUERY_LIMIT)
                self._logger.info(f"Set maximum query limit: {MAX_QUERY_LIMIT}")

        except Exception as e:
            self._logger.error(f"Error loading settings: {str(e)}")
            DEFAULT_CONN_STR = "sqlite:///data/initialdb/vehicles.db"
            conn_str = self._config.get(f"plugins.{self.name}.connection_string", None)
            if conn_str is None:
                self._config.set(f"plugins.{self.name}.connection_string", DEFAULT_CONN_STR)
                self._logger.info(f"Set fallback connection string: {DEFAULT_CONN_STR}")

    def _setup_periodic_tasks(self) -> None:
        """Set up periodic tasks."""
        if self._thread_manager:
            # Schedule periodic database validation (every 5 minutes)
            self._db_connection_timer = self._thread_manager.schedule_periodic_task(
                interval=300.0,  # 5 minutes
                func=self._validate_database,
                task_id=f"{self.name}_validate_db_periodic"
            )
            self._logger.debug("Scheduled periodic database validation")

    def _subscribe_to_events(self) -> None:
        """Subscribe to system events."""
        if not self._event_bus:
            return

        self._event_bus.subscribe(
            event_type=EventType.SYSTEM_STARTED.value,
            callback=self._on_system_started,
            subscriber_id=f"{self.name}_system_started"
        )

        self._event_bus.subscribe(
            event_type=EventType.CONFIG_CHANGED.value,
            callback=self._on_config_changed,
            subscriber_id=f"{self.name}_config_changed"
        )

    def _on_system_started(self, event: Event) -> None:
        """Handle system started event.

        Args:
            event: Event object
        """
        if not self._initialized:
            return

        self._logger.info("System started event received")

        if self._thread_manager:
            self._thread_manager.submit_task(
                func=self._validate_database,
                name=f"{self.name}_validate_db",
                submitter=self.name
            )

    def _validate_database(self) -> None:
        """Validate database connection."""
        if not self._initialized or not self._vehicle_service:
            return

        try:
            result = self._vehicle_service.validate_database()

            # Publish database status event
            if self._event_bus:
                self._event_bus.publish(
                    event_type=f"{self.name}/database_status",
                    source=self.name,
                    payload={"connected": result}
                )

            # Update UI if available
            if self._tab:
                self._tab.update_database_status({"connected": result})

            if result:
                self._logger.info("Database validation successful")
                if self._event_bus:
                    self._event_bus.publish(
                        event_type=f"{self.name}/database_ready",
                        source=self.name,
                        payload={"status": "ready"}
                    )
            else:
                self._logger.error("Database validation failed")
                if self._event_bus:
                    self._event_bus.publish(
                        event_type=f"{self.name}/database_error",
                        source=self.name,
                        payload={"status": "error", "message": "Validation failed"}
                    )
        except Exception as e:
            self._logger.error(f"Database validation error: {str(e)}", exc_info=True)
            if self._event_bus:
                self._event_bus.publish(
                    event_type=f"{self.name}/database_error",
                    source=self.name,
                    payload={"status": "error", "message": str(e)}
                )

    def _on_config_changed(self, event: Event) -> None:
        """Handle configuration change event.

        Args:
            event: Event object
        """
        if not self._initialized:
            return

        config_path = event.payload.get("path", "")
        if not config_path.startswith(f"plugins.{self.name}"):
            return

        self._logger.info(f"Configuration changed: {config_path}")

        plugin_config = self._config.get(f"plugins.{self.name}", {})

        if self._vehicle_service:
            self._vehicle_service.update_config(plugin_config)

        if self._export_service:
            self._export_service.update_config(plugin_config)

        # Publish config updated event
        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/config_updated",
                source=self.name,
                payload={"config_path": config_path}
            )

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Set up UI components.

        Args:
            ui_integration: Interface for adding UI components
        """
        try:
            self._logger.debug("Setting up UI components")

            # Create and add the tab
            self._tab = InitialDBTab()
            self._tab_index = ui_integration.add_tab(
                plugin_id=self.name,
                tab=self._tab,
                title="Vehicle Database"
            )

            # Add menu items
            try:
                self._tools_menu = ui_integration.find_menu("&Tools")
                if not self._tools_menu:
                    self._tools_menu = ui_integration.add_menu(
                        plugin_id=self.name,
                        title="&Tools"
                    )

                if self._tools_menu:
                    self._plugin_menu = ui_integration.add_menu(
                        plugin_id=self.name,
                        title="Vehicle Database",
                        parent_menu=self._tools_menu
                    )

                    if self._plugin_menu:
                        action1 = ui_integration.add_menu_action(
                            plugin_id=self.name,
                            menu=self._plugin_menu,
                            text="Refresh Database Connection",
                            callback=self._refresh_database_connection
                        )
                        self._menu_items.append(action1)

                        action2 = ui_integration.add_menu_action(
                            plugin_id=self.name,
                            menu=self._plugin_menu,
                            text="Connection Settings",
                            callback=self._show_connection_settings
                        )
                        self._menu_items.append(action2)

                        action3 = ui_integration.add_menu_action(
                            plugin_id=self.name,
                            menu=self._plugin_menu,
                            text="Export Data",
                            callback=self._show_export_dialog
                        )
                        self._menu_items.append(action3)

                        self._logger.debug("Added menu items to Tools menu")
            except Exception as e:
                self._logger.error(f"Error adding menu items: {str(e)}")

            # Update initial database status
            if self._initialized and self._vehicle_service:
                self._thread_manager.submit_task(
                    func=self._validate_database,
                    name=f"{self.name}_initial_validate_db",
                    submitter=self.name
                )

            if self._event_bus:
                self._event_bus.publish(
                    event_type=f"{self.name}/ui_added",
                    source=self.name,
                    payload={"tab_index": self._tab_index}
                )
        except Exception as e:
            self._logger.error(f"Error setting up UI components: {str(e)}")

    def _refresh_database_connection(self) -> None:
        """Refresh database connection."""
        self._logger.info("Refreshing database connection")
        if self._thread_manager and self._vehicle_service:
            self._thread_manager.submit_task(
                func=self._validate_database,
                name=f"{self.name}_validate_db",
                submitter=self.name
            )

    def _show_connection_settings(self) -> None:
        """Show database connection settings dialog."""
        self._logger.info("Showing connection settings")
        # This would launch a settings dialog in a full implementation

        # Publish event for UI notification
        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/show_settings",
                source=self.name,
                payload={}
            )

    def _show_export_dialog(self) -> None:
        """Show export dialog."""
        self._logger.info("Showing export dialog")
        # This would launch an export dialog in a full implementation

        # Publish event for UI notification
        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/show_export",
                source=self.name,
                payload={}
            )

    def shutdown(self) -> None:
        """Shut down the plugin.

        Clean up resources when the plugin is being unloaded.
        """
        if not self._initialized:
            return

        self._logger.info(f"Shutting down {self.name} plugin")

        # Cancel background tasks
        if self._thread_manager and self._db_connection_timer:
            self._thread_manager.cancel_task(self._db_connection_timer)

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f"{self.name}_system_started")
            self._event_bus.unsubscribe(f"{self.name}_config_changed")

        # Shut down services
        if self._vehicle_service:
            self._vehicle_service.shutdown()

        if self._export_service:
            self._export_service.shutdown()

        # Clean up UI resources
        self._menu_items.clear()
        self._plugin_menu = None
        self._tools_menu = None

        self._initialized = False
        self._logger.info(f"{self.name} plugin shut down successfully")

    def get_vehicle_service(self) -> Optional[Any]:
        """Get the vehicle service.

        Returns:
            Vehicle service instance or None if not initialized
        """
        return self._vehicle_service if self._initialized else None

    def get_export_service(self) -> Optional[Any]:
        """Get the export service.

        Returns:
            Export service instance or None if not initialized
        """
        return self._export_service if self._initialized else None

    def status(self) -> Dict[str, Any]:
        """Get plugin status information.

        Returns:
            Status dictionary
        """
        status = {
            "name": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "has_ui": True,
            "ui_components": {
                "tab_added": self._tab is not None,
                "tab_index": self._tab_index,
                "menu_items_count": len(self._menu_items)
            },
            "services": {
                "vehicle_service": self._vehicle_service is not None,
                "export_service": self._export_service is not None
            },
            "subscriptions": ["system/started", "config/changed"]
        }

        # Add database connection status if available
        if self._initialized and self._vehicle_service:
            try:
                status["database"] = {
                    "connected": self._vehicle_service.validate_database(),
                    "connection_string": self._config.get(f"plugins.{self.name}.connection_string", "")
                }
            except Exception:
                status["database"] = {
                    "connected": False,
                    "connection_string": self._config.get(f"plugins.{self.name}.connection_string", "")
                }

        return status