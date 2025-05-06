from __future__ import annotations

"""
InitialDB Plugin for Qorzen framework.

This plugin provides access to vehicle component database information,
allowing users to query and export vehicle parts and specifications.
"""

from logging import Logger
from typing import Any, Dict, List, Optional
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

from qorzen.core import FileManager, EventBusManager, ThreadManager, ConfigManager

from .services.vehicle_service import VehicleService
from .services.export_service import ExportService
from .routes.api import register_api_routes
from qorzen.plugins.initialdb.code.config.settings import DEFAULT_CONNECTION_STRING


class InitialDBPlugin(QObject):
    """
    InitialDB Plugin for the Qorzen framework.

    This plugin provides database access and querying functionality for vehicle
    component data, with capabilities for filtering, exporting, and API access.
    """
    ui_ready_signal = Signal(object)

    # Required plugin metadata
    name = "initialdb"
    version = "0.2.0"
    description = "Vehicle Component Database Plugin"
    author = "Ryan Serra"

    # Optional metadata
    dependencies = []

    def __init__(self) -> None:
        """Initialize the plugin without external dependencies."""
        super().__init__()
        self._event_bus = None
        self._logger = None
        self._config = None
        self._file_manager = None
        self._thread_manager = None
        self._db_manager = None
        self._api_manager = None
        self._main_window = None
        self._subscriber_id = None

        self._vehicle_service = None
        self._export_service = None
        self._initialized = False

        self._menu_items: List[QAction] = []
        self._tab = None
        self._tab_index: Optional[int] = None

        # Connect signal to slot
        self.ui_ready_signal.connect(self._handle_ui_ready_on_main_thread)

    def initialize(self,
                   event_bus: Any,
                   logger_provider: Any,
                   config_provider: Any,
                   file_manager: Any,
                   thread_manager: Any,
                   **kwargs: Any) -> None:
        """
        Initialize the plugin with Qorzen core services.

        Args:
            event_bus: Event bus for publishing/subscribing to events
            logger_provider: Logging provider for creating loggers
            config_provider: Configuration provider for accessing settings
            file_manager: File system manager for file operations
            thread_manager: Thread manager for background tasks
            **kwargs: Additional dependencies including database_manager, api_manager
        """
        # Store references to core services
        self._event_bus: EventBusManager = event_bus
        self._logger: Logger = logger_provider.get_logger(self.name)
        self._config: ConfigManager = config_provider
        self._file_manager: FileManager = file_manager
        self._thread_manager: ThreadManager = thread_manager

        # Get additional dependencies
        self._db_manager = kwargs.get('database_manager')
        if not self._db_manager:
            self._logger.error("Database manager not available - plugin cannot function")
            return

        self._api_manager = kwargs.get('api_manager')
        if not self._api_manager:
            self._logger.warning("API manager not available - API routes will not be registered")

        # Create plugin data directory if needed
        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type='plugin_data')
                self._file_manager.ensure_directory(plugin_data_dir.as_posix())
                self._logger.debug(f'Plugin data directory: {plugin_data_dir}')
            except Exception as e:
                self._logger.warning(f'Failed to create plugin data directory: {str(e)}')

        # Initialize services
        self._logger.info(f"Initializing {self.name} v{self.version} plugin")

        # Load settings
        self._load_settings()

        try:
            # Initialize vehicle service
            self._vehicle_service = VehicleService(
                db_manager=self._db_manager,
                logger=self._logger,
                event_bus=self._event_bus,
                thread_manager=self._thread_manager,
                config=self._config
            )

            # Initialize export service
            self._export_service = ExportService(
                file_manager=self._file_manager,
                logger=self._logger,
                vehicle_service=self._vehicle_service,
                config=self._config
            )

            # Register API routes if API manager is available
            if self._api_manager:
                register_api_routes(
                    api_manager=self._api_manager,
                    vehicle_service=self._vehicle_service,
                    export_service=self._export_service,
                    logger=self._logger
                )
                self._logger.info("API routes registered")

            # Subscribe to events
            self._subscribe_to_events()

            self._initialized = True
            self._logger.info(f'{self.name} plugin initialized')

            # Publish initialization event
            self._event_bus.publish(
                event_type='plugin/initialized',
                source=self.name,
                payload={'plugin_name': self.name, 'version': self.version, 'has_ui': True}
            )

        except Exception as e:
            self._logger.error(f"Failed to initialize plugin: {str(e)}", exc_info=True)

    def _load_settings(self) -> None:
        """Load plugin settings from configuration."""
        try:
            # Check if connection string is already in config, if not set default
            conn_str = self._config.get(f'plugins.{self.name}.connection_string', None)
            if conn_str is None:
                self._config.set(f'plugins.{self.name}.connection_string', DEFAULT_CONNECTION_STRING)
                self._logger.info(f'Set default connection string: {DEFAULT_CONNECTION_STRING}')
        except Exception as e:
            self._logger.error(f'Error loading settings: {str(e)}')

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant system events."""
        # Subscribe to system startup event
        self._event_bus.subscribe(
            event_type="system/started",
            callback=self._on_system_started,
            subscriber_id=f"{self.name}_system_started"
        )

        # Subscribe to config changes
        self._event_bus.subscribe(
            event_type=f"config/changed",
            callback=self._on_config_changed,
            subscriber_id=f"{self.name}_config_changed"
        )

        # Subscribe to UI events
        self._subscriber_id = self._event_bus.subscribe(
            event_type='ui/ready',
            callback=self._on_ui_ready_event,
            subscriber_id=f'{self.name}_ui_subscriber'
        )

    def _on_system_started(self, event: Any) -> None:
        """Handle system startup event."""
        if not self._initialized:
            return

        self._logger.info("System started event received")

        # Validate database connection
        self._thread_manager.submit_task(
            func=self._validate_database,
            name=f"{self.name}_validate_db",
            submitter=self.name
        )

    def _validate_database(self) -> None:
        """Validate database connection and schema."""
        if not self._initialized or not self._vehicle_service:
            return

        try:
            result = self._vehicle_service.validate_database()
            if result:
                self._logger.info("Database validation successful")
                # Publish event that database is ready
                self._event_bus.publish(
                    event_type=f"{self.name}/database_ready",
                    source=self.name,
                    payload={"status": "ready"}
                )
            else:
                self._logger.error("Database validation failed")
        except Exception as e:
            self._logger.error(f"Database validation error: {str(e)}", exc_info=True)

    def _on_config_changed(self, event: Any) -> None:
        """Handle configuration changes."""
        if not self._initialized:
            return

        # Extract the changed configuration path
        config_path = event.payload.get("path", "")
        if not config_path.startswith(f"plugins.{self.name}"):
            return  # Not our config

        self._logger.info(f"Configuration changed: {config_path}")

        # Get updated configuration
        plugin_config = self._config.get(f"plugins.{self.name}", {})

        # Update service configurations if needed
        if self._vehicle_service:
            self._vehicle_service.update_config(plugin_config)

        if self._export_service:
            self._export_service.update_config(plugin_config)

    def _on_ui_ready_event(self, event: Any) -> None:
        """Handler for ui/ready event."""
        try:
            main_window = event.payload.get('main_window')
            if not main_window:
                self._logger.error('Main window not provided in event payload')
                return

            # Use signal to handle UI updates on the main thread
            self.ui_ready_signal.emit(main_window)
        except Exception as e:
            self._logger.error(f'Error in UI ready event handler: {str(e)}')

    @Slot(object)
    def _handle_ui_ready_on_main_thread(self, main_window: Any) -> None:
        """Set up UI components on the main thread."""
        try:
            self._logger.debug('Setting up UI components')
            self._main_window = main_window

            # Add plugin tab to main window
            self._add_tab_to_ui()

            # Add menu items
            self._add_menu_items()

            # Publish UI added event
            self._event_bus.publish(
                event_type=f'plugin/{self.name}/ui_added',
                source=self.name,
                payload={'tab_index': self._tab_index}
            )
        except Exception as e:
            self._logger.error(f'Error handling UI setup: {str(e)}')

    def _add_tab_to_ui(self) -> None:
        """Add a tab to the main window."""
        if not self._main_window:
            return

        try:
            # Create your tab widget here
            # Example:
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

            self._tab = QWidget()
            layout = QVBoxLayout(self._tab)
            layout.addWidget(QLabel(f"This is the {self.name} plugin tab"))

            # Add tab to main window
            central_tabs = self._main_window._central_tabs
            if central_tabs:
                self._tab_index = central_tabs.addTab(self._tab, self.name)
                self._logger.info(f'Added tab at index {self._tab_index}')
            else:
                self._logger.error('Central tabs widget not found in main window')
        except Exception as e:
            self._logger.error(f'Error adding tab to UI: {str(e)}')

    def _add_menu_items(self) -> None:
        """Add menu items to the main window."""
        if not self._main_window:
            return

        try:
            # Find Tools menu
            tools_menu = None
            for action in self._main_window.menuBar().actions():
                if action.text() == '&Tools':
                    tools_menu = action.menu()
                    break

            if tools_menu:
                # Create plugin menu
                plugin_menu = QMenu(self.name, self._main_window)

                # Add actions to the menu
                action1 = QAction('Action 1', self._main_window)
                # action1.triggered.connect(self._action1_handler)
                plugin_menu.addAction(action1)

                action2 = QAction('Action 2', self._main_window)
                # action2.triggered.connect(self._action2_handler)
                plugin_menu.addAction(action2)

                # Add separator and plugin menu to Tools menu
                tools_menu.addSeparator()
                tools_menu.addMenu(plugin_menu)

                # Store menu items for cleanup
                self._menu_items.extend([action1, action2])

                self._logger.debug('Added menu items to Tools menu')
            else:
                self._logger.warning('Tools menu not found in main window')
        except Exception as e:
            self._logger.error(f'Error adding menu items: {str(e)}')

    def _refresh_database_connection(self) -> None:
        """Handler for refreshing database connection."""
        if self._tab:
            self._tab.refresh_database_connection()
            self._logger.info('Database connection refreshed')

    def _show_connection_settings(self) -> None:
        """Handler for showing connection settings."""
        if self._tab:
            self._tab.show_connection_settings()
            self._logger.info('Connection settings shown')

    def shutdown(self) -> None:
        """Clean up resources when plugin is being unloaded."""
        if not self._initialized:
            return

        self._logger.info(f"Shutting down {self.name} plugin")

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f"{self.name}_system_started")
            self._event_bus.unsubscribe(f"{self.name}_config_changed")
            self._event_bus.unsubscribe(f"{self.name}_ui_subscriber")

        # Shutdown services
        if self._vehicle_service:
            self._vehicle_service.shutdown()

        if self._export_service:
            self._export_service.shutdown()

        # Clean up UI
        if self._main_window:
            if self._tab and self._tab_index is not None:
                central_tabs = self._main_window._central_tabs
                if central_tabs:
                    central_tabs.removeTab(self._tab_index)
                    self._logger.debug(f'Removed InitialDB tab at index {self._tab_index}')
            for action in self._menu_items:
                if action and action.menu():
                    menu = action.menu()
                    menu.clear()
                    menu.deleteLater()
                elif action and action.parent():
                    action.parent().removeAction(action)

        self._initialized = False
        self._logger.info(f"{self.name} plugin shut down successfully")

    def get_vehicle_service(self) -> Optional[VehicleService]:
        """
        Get the vehicle service instance.

        Returns:
            The VehicleService instance or None if not initialized.
        """
        return self._vehicle_service if self._initialized else None

    def get_export_service(self) -> Optional[ExportService]:
        """
        Get the export service instance.

        Returns:
            The ExportService instance or None if not initialized.
        """
        return self._export_service if self._initialized else None

    def status(self) -> Dict[str, Any]:
        """Return the status of the plugin."""
        return {
            'name': self.name,
            'version': self.version,
            'initialized': self._initialized,
            'has_ui': True,
            'ui_components': {
                'tab_added': self._tab is not None,
                'tab_index': self._tab_index,
                'menu_items_count': len(self._menu_items)
            },
            'subscriptions': ['system/started', 'config/changed', 'ui/ready']
        }