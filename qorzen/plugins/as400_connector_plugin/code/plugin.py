# Complete Thread-Safe Solution for plugin.py

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Set, cast
from pathlib import Path
from PySide6.QtWidgets import QMenu, QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import QMetaObject, Qt, Slot, QObject, Signal

from qorzen.core.event_model import EventType
from qorzen.plugins.as400_connector_plugin.code.ui.as400_tab import AS400Tab

from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration


# Thread-safe plugin implementation
class AS400ConnectorPlugin(BasePlugin):
    # Define signals for thread-safe operations
    ui_ready_signal = Signal(object)  # Signal to pass main window from event to main thread

    name = 'as400_connector_plugin'
    version = '0.1.0'
    description = 'Connect and query AS400/iSeries databases'
    author = 'Qorzen Team'
    dependencies = []

    def __init__(self) -> None:
        super().__init__()  # Initialize QObject
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
        self._tab: Optional[AS400Tab] = None
        self._tab_index: Optional[int] = None
        self._toolbar: Optional[QToolBar] = None
        self._menu: Optional[QMenu] = None
        self._actions: List[Any] = []

    def initialize(self, event_bus_manager: Any, logger_provider: Any, config_provider: Any, file_manager: Any = None,
                   thread_manager: Any = None, database_manager: Any = None, security_manager: Any = None, **kwargs: Any) -> None:
        self._event_bus = event_bus
        self._logger = logger_provider.get_logger(f'plugin.{self.name}')
        self._config = config_provider
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._security_manager = security_manager
        self._main_window = self._config.get("_app_core")
        self._logger.info(f'Initializing {self.name} plugin v{self.version}')

        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type='plugin_data')
                os.makedirs(plugin_data_dir, exist_ok=True)
                self._logger.debug(f'Plugin data directory: {plugin_data_dir}')
            except Exception as e:
                self._logger.warning(f'Failed to create plugin data directory: {str(e)}')

        self._event_bus_manager.subscribe(
            event_type='config/changed',
            callback=self._on_config_changed,
            subscriber_id=f'{self.name}_config_subscriber'
        )

        self._initialized = True
        self._logger.info(f'{self.name} plugin initialized')
        self._event_bus_manager.publish(
            event_type='plugin/initialized',
            source=self.name,
            payload={'plugin_name': self.name, 'version': self.version, 'has_ui': True}
        )

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Set up UI components when UI is ready.

        Args:
            ui_integration: The UI integration.
        """
        self._logger.info('Setting up UI components')

        # Create and add tab
        self._tab = AS400Tab(event_bus=self._event_bus, logger=self._logger, config=self._config, file_manager=self._file_manager, thread_manager=self._thread_manager)
        tab_index = ui_integration.add_tab(
            plugin_id=self.name,
            tab=self._tab,
            title='AS400 Connector'
        )
        self._logger.debug(f'Added AS400 Connector tab at index {tab_index}')

        # Add toolbar in a safe way
        try:
            self._toolbar = ui_integration.add_toolbar(
                plugin_id=self.name,
                title='AS400 Connector'
            )

            # Add toolbar action
            action = ui_integration.add_toolbar_action(
                plugin_id=self.name,
                toolbar=self._toolbar,
                text='Refresh',
                callback=self._refresh_metrics
            )
            self._actions.append(action)

        except Exception as e:
            self._logger.warning(f'Error adding toolbar: {str(e)}')

        # Try to find and add to Tools menu safely
        try:
            tools_menu = ui_integration.find_menu('&Tools')
            if tools_menu:
                # Keep a reference to the menu
                self._menu = ui_integration.add_menu(
                    plugin_id=self.name,
                    title='AS400 Connector',
                    parent_menu=tools_menu
                )

                # Add menu actions
                action1 = ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=self._menu,
                    text='Connection...',
                    callback=self._open_connection_dialog
                )

                action2 = ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=self._menu,
                    text='Manage Connections...',
                    callback=self._manage_connections
                )

                self._menu.addSeparator()

                action3 = ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=self._menu,
                    text='Import Queries...',
                    callback=self._import_queries
                )

                action4 = ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=self._menu,
                    text='Export Queries...',
                    callback=self._export_queries
                )

                self._actions.extend([action1, action2, action3, action4])

        except Exception as e:
            self._logger.warning(f'Error adding menu items: {str(e)}')

    # Keep the rest of your methods for opening connection dialog, etc.
    def _open_connection_dialog(self) -> None:
        if self._tab:
            self._tab.open_connection_dialog()
            if self._main_window and self._tab_index is not None:
                self._main_window._central_tabs.setCurrentIndex(self._tab_index)

    def _manage_connections(self) -> None:
        if self._tab:
            self._tab.open_connection_manager()
            if self._main_window and self._tab_index is not None:
                self._main_window._central_tabs.setCurrentIndex(self._tab_index)

    def _import_queries(self) -> None:
        if self._tab:
            self._tab.import_queries()

    def _export_queries(self) -> None:
        if self._tab:
            self._tab.export_queries()

    def _on_config_changed(self, event: Any) -> None:
        if not event.payload.get('key', '').startswith(f'plugins.{self.name}'):
            return
        self._logger.info(f"Configuration changed: {event.payload.get('key')} = {event.payload.get('value')}")
        if self._tab:
            self._tab.handle_config_change(event.payload.get('key'), event.payload.get('value'))

    def shutdown(self) -> None:
        if not self._initialized:
            return
        self._logger.info(f'Shutting down {self.name} plugin')
        if self._main_window:
            if self._tab and self._tab_index is not None:
                central_tabs = self._main_window._central_tabs
                if central_tabs:
                    central_tabs.removeTab(self._tab_index)
                    self._logger.debug(f'Removed AS400 tab at index {self._tab_index}')
            for action in self._menu_items:
                if action and action.menu():
                    menu = action.menu()
                    menu.clear()
                    menu.deleteLater()
                elif action and action.parent():
                    action.parent().removeAction(action)
        if self._event_bus_manager:
            if self._subscriber_id:
                self._event_bus_manager.unsubscribe(self._subscriber_id)
            self._event_bus_manager.unsubscribe(f'{self.name}_config_subscriber')
            self._event_bus_manager.publish(event_type='plugin/shutdown', source=self.name, payload={'plugin_name': self.name},
                                    synchronous=True)
        self._initialized = False
        self._logger.info(f'{self.name} plugin shut down')

    def status(self) -> Dict[str, Any]:
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