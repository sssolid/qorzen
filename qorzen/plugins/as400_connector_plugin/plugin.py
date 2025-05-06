# Complete Thread-Safe Solution for plugin.py

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Set, cast
from pathlib import Path
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QMetaObject, Qt, Slot, QObject, Signal

from qorzen.plugins.as400_connector_plugin.ui.as400_tab import AS400Tab


# Thread-safe plugin implementation
class AS400ConnectorPlugin(QObject):
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

        # Connect signal to slot for thread-safe handling
        self.ui_ready_signal.connect(self._handle_ui_ready_on_main_thread)

    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any, file_manager: Any = None,
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

        # Subscribe to the UI ready event
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
        self._event_bus.publish(
            event_type='plugin/initialized',
            source=self.name,
            payload={'plugin_name': self.name, 'version': self.version, 'has_ui': True}
        )

    def _on_ui_ready_event(self, event: Any) -> None:
        """Handle UI ready event from any thread by emitting a signal."""
        try:
            main_window = event.payload.get('main_window', self._config.get("_app_core"))
            if not main_window:
                self._logger.error('Main window not provided in event payload')
                return

            # Emit signal to handle this on the main thread
            self.ui_ready_signal.emit(main_window)

        except Exception as e:
            self._logger.error(f'Error in UI ready event handler: {str(e)}')

    @Slot(object)
    def _handle_ui_ready_on_main_thread(self, main_window: Any) -> None:
        """
        Handle UI ready event on the main thread.
        This slot is connected to the signal and runs on the main thread.
        """
        try:
            self._logger.debug('Handling UI ready on main thread')
            self._main_window = main_window

            # These operations now run on the main thread
            self._add_tab_to_ui()
            self._add_menu_items()

            self._event_bus.publish(
                event_type=f'plugin/{self.name}/ui_added',
                source=self.name,
                payload={'tab_index': self._tab_index}
            )

        except Exception as e:
            self._logger.error(f'Error handling UI ready on main thread: {str(e)}')

    def _add_tab_to_ui(self) -> None:
        """Add the AS400 tab to the main UI."""
        if not self._main_window:
            return
        try:
            self._logger.info('Creating AS400Tab')
            self._tab = AS400Tab(
                event_bus=self._event_bus,
                logger=self._logger,
                config=self._config,
                file_manager=self._file_manager,
                thread_manager=self._thread_manager,
                security_manager=self._security_manager,
                parent=self._main_window
            )

            central_tabs = self._main_window._central_tabs
            if central_tabs:
                self._tab_index = central_tabs.addTab(self._tab, 'AS400 Connector')
                self._logger.info(f'Added AS400 tab at index {self._tab_index}')
            else:
                self._logger.error('Central tabs widget not found in main window')
        except Exception as e:
            self._logger.error(f'Error adding AS400 tab to UI: {str(e)}')

    def _add_menu_items(self) -> None:
        """Add menu items to the main UI."""
        if not self._main_window:
            return
        try:
            tools_menu = None
            for action in self._main_window.menuBar().actions():
                if action.text() == '&Tools':
                    tools_menu = action.menu()
                    break

            if tools_menu:
                as400_menu = QMenu('AS400 Connector', self._main_window)

                connect_action = QAction('Connect to AS400...', self._main_window)
                connect_action.triggered.connect(self._open_connection_dialog)
                as400_menu.addAction(connect_action)

                manage_connections_action = QAction('Manage Connections', self._main_window)
                manage_connections_action.triggered.connect(self._manage_connections)
                as400_menu.addAction(manage_connections_action)

                as400_menu.addSeparator()

                import_action = QAction('Import Queries...', self._main_window)
                import_action.triggered.connect(self._import_queries)
                as400_menu.addAction(import_action)

                export_action = QAction('Export Queries...', self._main_window)
                export_action.triggered.connect(self._export_queries)
                as400_menu.addAction(export_action)

                tools_menu.addSeparator()
                tools_menu.addMenu(as400_menu)

                self._menu_items.extend([connect_action, manage_connections_action, import_action, export_action])
                self._logger.debug('Added AS400 menu items to Tools menu')
            else:
                self._logger.warning('Tools menu not found in main window')
        except Exception as e:
            self._logger.error(f'Error adding menu items: {str(e)}')

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
        if self._event_bus:
            if self._subscriber_id:
                self._event_bus.unsubscribe(self._subscriber_id)
            self._event_bus.unsubscribe(f'{self.name}_config_subscriber')
            self._event_bus.publish(event_type='plugin/shutdown', source=self.name, payload={'plugin_name': self.name},
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