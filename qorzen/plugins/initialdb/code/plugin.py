#!/usr/bin/env python3
# plugin.py
from __future__ import annotations

"""
Vehicle Component Database (InitialDB) Plugin for Qorzen framework.

This plugin provides access to vehicle component database information,
allowing users to query and export vehicle parts and specifications.
"""

import logging
from typing import Any, Dict, List, Optional, cast

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget, QProgressBar, QHBoxLayout, QApplication, \
    QMessageBox, QSplitter, QStatusBar

from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, TabComponent
from qorzen.plugin_system.interface import BasePlugin

# Import local settings module
from .config.settings import (
    setup_default_config,
    get_plugin_config_namespace,
)

from .ui.panels import LeftPanel, RightPanel, BottomPanel
from .ui.settings_dialog import SettingsDialog


class DatabaseStatusWidget(QWidget):
    """Widget showing the status of the database connection."""

    update_signal = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the status widget.

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
        """Update the widget with new status.

        Args:
            status: Status information with 'connected' boolean
        """
        self.update_signal.emit(status)

    @Slot(dict)
    def _update_ui(self, status: Dict[str, Any]) -> None:
        """Update UI elements based on status.

        Args:
            status: Status information dictionary
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


class VehicleDatabaseTab(QWidget):
    """Main tab for the Vehicle Database plugin."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the tab.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Vehicle Component Database")
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(title_label)

        # Database status
        self._db_status = DatabaseStatusWidget()
        self._layout.addWidget(self._db_status)

        # Tab widget for sub-tabs
        self._tab_widget = QTabWidget()
        self._layout.addWidget(self._tab_widget)

        # Info label
        self._info_label = QLabel("Use the menu options to query and export vehicle data.")
        self._info_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._info_label)

    def get_widget(self) -> QWidget:
        """Return the widget for this tab.

        Returns:
            This widget
        """
        return self

    def on_tab_selected(self) -> None:
        """Called when this tab is selected."""
        pass

    def on_tab_deselected(self) -> None:
        """Called when this tab is deselected."""
        pass

    def update_database_status(self, status: Dict[str, Any]) -> None:
        """Update the database status widget.

        Args:
            status: Status information with 'connected' boolean
        """
        self._db_status.update_status(status)


class InitialDBPlugin(BasePlugin):
    """Vehicle Component Database Plugin for Qorzen.

    This plugin provides access to vehicle database information,
    allowing users to query and export vehicle parts and specifications.
    """

    name = "initialdb"
    version = "0.2.0"
    description = "Vehicle Component Database Plugin"
    author = "Ryan Serra"
    dependencies = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._logger: Optional[logging.Logger] = None
        self._db_manager: Optional[Any] = None
        self._vehicle_service: Optional[Any] = None
        self._export_service: Optional[Any] = None
        self._tab: Optional[VehicleDatabaseTab] = None
        self._menu_items: List[Any] = []
        self._initialized = False
        self._db_connection_timer = None
        self._validate_db_task = None

    def initialize(
            self,
            event_bus: Any,
            logger_provider: Any,
            config_provider: Any,
            file_manager: Any,
            thread_manager: Any,
            **kwargs: Any
    ) -> None:
        """Initialize the plugin with core services.

        Args:
            event_bus: Event bus for pub/sub
            logger_provider: For creating loggers
            config_provider: Access to configuration
            file_manager: File system operations
            thread_manager: Task scheduling
            **kwargs: Additional dependencies including DatabaseManager
        """
        self._event_bus = cast(Any, event_bus)
        self._logger = logger_provider.get_logger(self.name)
        self._config = cast(Any, config_provider)
        self._file_manager = cast(Any, file_manager)
        self._thread_manager = cast(Any, thread_manager)
        self._db_manager = kwargs.get("database_manager")
        self._api_manager = kwargs.get("api_manager")

        if not self._db_manager:
            self._logger.error("Database manager not available")
            return

        self._logger.info(f"Initializing {self.name} v{self.version} plugin")

        # Ensure the config namespace exists and set defaults
        setup_default_config(self._config, self._logger)

        # Create plugin directories
        self._create_plugin_directories()

        # Initialize services
        self._initialize_services()

        # Subscribe to events
        self._subscribe_to_events()

        # Set up periodic tasks
        self._setup_periodic_tasks()

        self._initialized = True
        self._logger.info(f"{self.name} plugin initialized")

    def _create_plugin_directories(self) -> None:
        """Create necessary directories for the plugin."""
        from .config.settings import get_config_value

        exports_dir = get_config_value(self._config, "exports_dir", "exports")
        templates_dir = get_config_value(self._config, "templates_dir", "templates")

        try:
            self._file_manager.ensure_directory(exports_dir, directory_type="plugin_data")
            self._file_manager.ensure_directory(templates_dir, directory_type="plugin_data")
            self._logger.debug(f"Created plugin directories: {exports_dir}, {templates_dir}")
        except Exception as e:
            self._logger.error(f"Failed to create plugin directories: {str(e)}")

    def _initialize_services(self) -> None:
        """Initialize the plugin services."""
        try:
            from .services.vehicle_service import VehicleService
            from .services.export_service import ExportService

            # Get plugin config
            namespace = get_plugin_config_namespace()
            plugin_config = self._config.get(namespace, {})

            self._vehicle_service = VehicleService(
                db_manager=self._db_manager,
                logger=self._logger,
                config=self._config
            )

            self._export_service = ExportService(
                file_manager=self._file_manager,
                logger=self._logger,
                vehicle_service=self._vehicle_service,
                config=self._config
            )

            # Register API routes if API manager is available
            if self._api_manager:
                from .api.routes import register_api_routes
                register_api_routes(
                    api_manager=self._api_manager,
                    vehicle_service=self._vehicle_service,
                    export_service=self._export_service,
                    logger=self._logger
                )
                self._logger.info("API routes registered")

            self._logger.debug("Services initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize services: {str(e)}")

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

        self._logger.debug("Subscribed to events")

    def _setup_periodic_tasks(self) -> None:
        """Set up periodic tasks using the thread manager."""
        if self._thread_manager:
            self._db_connection_timer = self._thread_manager.schedule_periodic_task(
                interval=300.0,  # Check every 5 minutes
                func=self._validate_database,
                task_id=f"{self.name}_validate_db_periodic"
            )
            self._logger.debug("Scheduled periodic database validation")

    def _on_system_started(self, event: Event) -> None:
        """Handle system started event.

        Args:
            event: System started event
        """
        if not self._initialized:
            return

        self._logger.info("System started event received")

        # Validate database connection
        if self._thread_manager:
            self._validate_db_task = self._thread_manager.submit_task(
                func=self._validate_database,
                name=f"{self.name}_validate_db",
                submitter=self.name
            )

    def _validate_database(self) -> None:
        """Validate the database connection."""
        if not self._initialized or not self._vehicle_service:
            return

        try:
            result = self._vehicle_service.validate_database()

            # Publish event with database status
            if self._event_bus:
                self._event_bus.publish(
                    event_type=f"{self.name}/database_status",
                    source=self.name,
                    payload={"connected": result}
                )

            # Update UI if tab exists
            if self._tab:
                self._tab.update_database_status({"connected": result})

            if result:
                self._logger.info("Database validation successful")
            else:
                self._logger.error("Database validation failed")
        except Exception as e:
            self._logger.error(f"Database validation error: {str(e)}")

    def _on_config_changed(self, event: Event) -> None:
        """Handle configuration change event.

        Args:
            event: Configuration changed event
        """
        if not self._initialized:
            return

        config_path = event.payload.get("path", "")
        namespace = get_plugin_config_namespace()
        if not config_path.startswith(namespace):
            return

        self._logger.info(f"Configuration changed: {config_path}")

        # Update services with new configuration
        if self._vehicle_service:
            self._vehicle_service.update_config(self._config)

        if self._export_service:
            self._export_service.update_config(self._config)

        # Publish event about configuration update
        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/config_updated",
                source=self.name,
                payload={"config_path": config_path}
            )

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Handle UI integration when the Qorzen UI is ready."""
        self._logger.info("Setting up InitialDB UI components")

        try:
            # Create the main widget that will contain our UI
            self._main_widget = QWidget()
            layout = QVBoxLayout(self._main_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Create the main splitter
            self._main_splitter = QSplitter(Qt.Orientation.Horizontal)

            # Create and add the left panel
            self._left_panel = LeftPanel()
            self._main_splitter.addWidget(self._left_panel)

            # Create right side container with vertical layout
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            right_layout.setContentsMargins(0, 0, 0, 0)

            # Create and add the right panel
            self._right_panel = RightPanel()
            right_layout.addWidget(self._right_panel, 1)

            # Create and add the bottom panel
            self._bottom_panel = BottomPanel()
            right_layout.addWidget(self._bottom_panel)

            # Add the right container to the main splitter
            self._main_splitter.addWidget(right_widget)

            # Add the splitter to the main layout
            layout.addWidget(self._main_splitter, 1)

            # Create and add status bar
            self._status_bar = QStatusBar()
            layout.addWidget(self._status_bar)

            # Configure splitter sizes
            self._main_splitter.setSizes([300, 700])

            # Connect signals between components
            self._left_panel.query_executed.connect(self._on_query_results)
            self._right_panel.tab_added.connect(self._on_tab_added)

            # Initialize status bar
            self._status_bar.showMessage("Ready")

            # Create initial results tab
            self._create_results_tab('Query Results')

            # Add the main widget as a tab in the Qorzen UI
            tab_id = ui_integration.add_tab(
                plugin_id=self.name,
                tab=self._main_widget,
                title="InitialDB"
            )

            # Add toolbar and actions
            toolbar = ui_integration.add_toolbar(
                plugin_id=self.name,
                title="InitialDB"
            )

            ui_integration.add_toolbar_action(
                plugin_id=self.name,
                toolbar=toolbar,
                text="Execute Query",
                callback=self._execute_query
            )

            ui_integration.add_toolbar_action(
                plugin_id=self.name,
                toolbar=toolbar,
                text="Reset Filters",
                callback=self._reset_filters
            )

            ui_integration.add_toolbar_action(
                plugin_id=self.name,
                toolbar=toolbar,
                text="New Query",
                callback=self._new_query
            )

            # Add menu items
            tools_menu = ui_integration.find_menu("&Tools")
            if tools_menu:
                menu = ui_integration.add_menu(
                    plugin_id=self.name,
                    title="InitialDB",
                    parent_menu=tools_menu
                )

                ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=menu,
                    text="Execute Query",
                    callback=self._execute_query
                )

                ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=menu,
                    text="Reset Filters",
                    callback=self._reset_filters
                )

                ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=menu,
                    text="New Query",
                    callback=self._new_query
                )

                ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=menu,
                    text="Settings",
                    callback=self._show_settings
                )

            self._logger.info("InitialDB UI components initialized")

        except Exception as e:
            self._logger.error(f"Error setting up UI: {str(e)}")

    def _on_query_results(self, results: Any) -> None:
        """Handle query results."""
        tab_info = self._right_panel.get_current_tab()
        results_panel = None

        if tab_info:
            tab_id, widget = tab_info
            if hasattr(widget, 'set_results'):
                results_panel = widget

        if not results_panel:
            tab_id, results_panel = self._create_results_tab('Query Results')

        results_panel.set_results(results)
        self._status_bar.showMessage(f'Query completed: {len(results)} results')

    def _on_tab_added(self, tab_id: str, title: str) -> None:
        """Handle tab added event."""
        self._status_bar.showMessage(f'Tab added: {title}', 3000)

    def _create_results_tab(self, title: Optional[str] = None) -> tuple:
        """Create a results tab and return its id and widget."""
        return self._right_panel.create_results_tab(title)

    def _execute_query(self) -> None:
        """Execute the current query."""
        query_panel = self._left_panel.get_query_panel()
        query_panel._execute_all_queries()

    def _reset_filters(self) -> None:
        """Reset all filters."""
        query_panel = self._left_panel.get_query_panel()
        query_panel._reset_all_filters()
        self._status_bar.showMessage('Filters reset', 3000)

    def _new_query(self) -> None:
        """Create a new query."""
        result = QMessageBox.question(
            QApplication.activeWindow(),
            'New Query',
            'This will clear all current queries and filters. Continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        query_panel = self._left_panel.get_query_panel()
        query_panel._reset_all_filters()
        tab_id, results_panel = self._create_results_tab('New Query')
        self._status_bar.showMessage('New query created', 3000)

    def _show_export_dialog(self) -> None:
        """Show the export dialog."""
        self._logger.info("Showing export dialog")

        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/show_export",
                source=self.name,
                payload={}
            )

    def _show_query_dialog(self) -> None:
        """Show the query dialog."""
        self._logger.info("Showing query dialog")

        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/show_query",
                source=self.name,
                payload={}
            )

    def _show_settings(self) -> None:
        """Show the settings dialog."""
        dialog = SettingsDialog(QApplication.activeWindow())
        dialog.exec()

    def shutdown(self) -> None:
        """Clean up resources and shut down the plugin."""
        if not self._initialized:
            return

        self._logger.info(f"Shutting down {self.name} plugin")

        # Cancel periodic tasks
        if self._thread_manager and self._db_connection_timer:
            self._thread_manager.cancel_task(self._db_connection_timer)

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f"{self.name}_system_started")
            self._event_bus.unsubscribe(f"{self.name}_config_changed")

        # Shut down services
        if hasattr(self, "_vehicle_service") and self._vehicle_service:
            self._vehicle_service.shutdown()

        if hasattr(self, "_export_service") and self._export_service:
            self._export_service.shutdown()

        # Clean up UI connections
        if self._left_panel and self._right_panel:
            try:
                self._left_panel.query_executed.disconnect(self._on_query_results)
                self._right_panel.tab_added.disconnect(self._on_tab_added)
            except:
                pass

            # Close all tabs
            self._right_panel.close_all_tabs()

        # Clear references
        self._main_widget = None
        self._left_panel = None
        self._right_panel = None
        self._bottom_panel = None
        self._status_bar = None
        self._main_splitter = None

        # Clean up UI references
        self._menu_items.clear()
        self._tab = None

        self._initialized = False
        self._logger.info(f"{self.name} plugin shut down successfully")

    def get_vehicle_service(self) -> Optional[Any]:
        """Get the vehicle service.

        Returns:
            Vehicle service instance if initialized, None otherwise
        """
        return self._vehicle_service if self._initialized else None

    def get_export_service(self) -> Optional[Any]:
        """Get the export service.

        Returns:
            Export service instance if initialized, None otherwise
        """
        return self._export_service if self._initialized else None

    def status(self) -> Dict[str, Any]:
        """Get plugin status information.

        Returns:
            Status dictionary with plugin information
        """
        status = {
            "name": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "has_ui": True,
            "ui_components": {
                "tab_added": self._tab is not None,
                "menu_items_count": len(self._menu_items)
            },
            "services": {
                "vehicle_service": self._vehicle_service is not None,
                "export_service": self._export_service is not None
            },
            "subscriptions": ["system/started", "config/changed"]
        }

        if self._initialized and self._vehicle_service:
            try:
                namespace = get_plugin_config_namespace()
                status["database"] = {
                    "connected": self._vehicle_service.validate_database(),
                    "connection_string": self._config.get(f"{namespace}.connection_string", "")
                }
            except Exception:
                status["database"] = {
                    "connected": False,
                    "connection_string": self._config.get(f"{namespace}.connection_string", "")
                }

        return status