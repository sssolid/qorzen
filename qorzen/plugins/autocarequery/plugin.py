from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Set, cast
from pathlib import Path

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QObject, Signal, Slot

from qorzen.plugins.autocarequery.ui.query_tab import AutocareQueryTab
from qorzen.plugins.autocarequery.config.settings import DEFAULT_CONNECTION_STRING


class AutocareQueryPlugin(QObject):
    ui_ready_signal = Signal(object)

    # Plugin metadata - required
    name = "autocarequery"  # Must match directory name
    version = "0.1.0"
    description = "Database query tool for automotive vehicle data"
    author = "Qorzen Team"
    dependencies = []  # List other plugin names if needed

    def __init__(self) -> None:
        super().__init__()
        self._event_bus = None
        self._logger = None
        self._config = None
        self._file_manager = None
        self._thread_manager = None
        self._security_manager = None
        self._main_window = None
        self._subscriber_id = None
        self._initialized = False
        self._menu_items: List[QAction] = []
        self._tab = None
        self._tab_index: Optional[int] = None

        # Connect signal to slot
        self.ui_ready_signal.connect(self._handle_ui_ready_on_main_thread)

    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any,
                   file_manager: Any = None, thread_manager: Any = None, security_manager: Any = None) -> None:
        """
        Initialize the plugin with core services.

        Args:
            event_bus: The event bus for publishing and subscribing to events
            logger_provider: Provider for getting loggers
            config_provider: Provider for accessing configuration
            file_manager: Manager for file operations
            thread_manager: Manager for thread operations
            security_manager: Manager for security operations
        """
        self._event_bus = event_bus
        self._logger = logger_provider.get_logger(f'plugin.{self.name}')
        self._config = config_provider
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._security_manager = security_manager

        self._logger.info(f'Initializing {self.name} plugin v{self.version}')

        # Create plugin data directory if needed
        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type='plugin_data')
                os.makedirs(plugin_data_dir, exist_ok=True)
                self._logger.debug(f'Plugin data directory: {plugin_data_dir}')
            except Exception as e:
                self._logger.warning(f'Failed to create plugin data directory: {str(e)}')

        # Load settings
        self._load_settings()

        # Subscribe to events
        self._subscriber_id = self._event_bus.subscribe(
            event_type='ui/ready',
            callback=self._on_ui_ready_event,
            subscriber_id=f'{self.name}_ui_subscriber'
        )

        self._event_bus.subscribe(
            event_type='config/changed',
            callback=self._on_config_changed,
            subscriber_id=f'{self.name}_config_subscriber'
        )

        self._initialized = True
        self._logger.info(f'{self.name} plugin initialized')

        # Publish initialization event
        self._event_bus.publish(
            event_type='plugin/initialized',
            source=self.name,
            payload={'plugin_name': self.name, 'version': self.version, 'has_ui': True}
        )

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
            # Create the query tab
            connection_string = self._config.get(
                f'plugins.{self.name}.connection_string',
                DEFAULT_CONNECTION_STRING
            )

            self._tab = AutocareQueryTab(
                event_bus=self._event_bus,
                logger=self._logger,
                config=self._config,
                file_manager=self._file_manager,
                thread_manager=self._thread_manager,
                connection_string=connection_string,
                parent=self._main_window
            )

            # Add tab to main window
            central_tabs = self._main_window._central_tabs
            if central_tabs:
                self._tab_index = central_tabs.addTab(self._tab, "Vehicle Database")
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
                plugin_menu = QMenu("Vehicle Database", self._main_window)

                # Add actions to the menu
                refresh_action = QAction('Refresh Database Connection', self._main_window)
                refresh_action.triggered.connect(self._refresh_database_connection)
                plugin_menu.addAction(refresh_action)

                settings_action = QAction('Connection Settings', self._main_window)
                settings_action.triggered.connect(self._show_connection_settings)
                plugin_menu.addAction(settings_action)

                export_action = QAction('Export Default Queries', self._main_window)
                export_action.triggered.connect(self._export_default_queries)
                plugin_menu.addAction(export_action)

                # Add separator and plugin menu to Tools menu
                tools_menu.addSeparator()
                tools_menu.addMenu(plugin_menu)

                # Store menu items for cleanup
                self._menu_items.extend([refresh_action, settings_action, export_action])

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

    def _export_default_queries(self) -> None:
        """Handler for exporting default queries."""
        if self._tab:
            self._tab.export_default_queries()
            self._logger.info('Default queries exported')

    def _on_config_changed(self, event: Any) -> None:
        """Handler for configuration changes."""
        key = event.payload.get('key', '')
        if not key.startswith(f'plugins.{self.name}'):
            return

        value = event.payload.get('value')
        self._logger.info(f"Configuration changed: {key} = {value}")

        # Handle connection string change
        if key == f'plugins.{self.name}.connection_string' and self._tab:
            try:
                self._tab.update_connection_string(value)
            except Exception as e:
                self._logger.error(f'Error updating connection string: {str(e)}')

    def shutdown(self) -> None:
        """
        Clean up resources when the plugin is unloaded.
        """
        if not self._initialized:
            return

        self._logger.info(f'Shutting down {self.name} plugin')

        # Remove UI components
        if self._main_window:
            # Remove tab
            if self._tab and self._tab_index is not None:
                central_tabs = self._main_window._central_tabs
                if central_tabs:
                    central_tabs.removeTab(self._tab_index)
                    self._logger.debug(f'Removed tab at index {self._tab_index}')

            # Remove menu items
            for action in self._menu_items:
                if action and action.menu():
                    menu = action.menu()
                    menu.clear()
                    menu.deleteLater()
                elif action and action.parent():
                    action.parent().removeAction(action)

        # Cleanup tab resources
        if self._tab:
            self._tab.cleanup()

        # Unsubscribe from events
        if self._event_bus:
            if self._subscriber_id:
                self._event_bus.unsubscribe(self._subscriber_id)
            self._event_bus.unsubscribe(f'{self.name}_config_subscriber')

            # Publish shutdown event
            self._event_bus.publish(
                event_type='plugin/shutdown',
                source=self.name,
                payload={'plugin_name': self.name},
                synchronous=True
            )

        self._initialized = False
        self._logger.info(f'{self.name} plugin shut down')

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
            'subscriptions': ['ui/ready', 'config/changed']
        }