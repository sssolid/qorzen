from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, cast, Callable
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar, QPushButton, QScrollArea, QSizePolicy, QSplitter, QStackedWidget, QToolBar, QVBoxLayout, QWidget, QDockWidget
from qorzen.ui.settings_manager import SettingsManager
from qorzen.ui.ui_component import QWidget
from qorzen.utils.exceptions import UIError
class MainWindowPluginHandler:
    def __init__(self, main_window: Any, plugin_manager: Any, logger: Any):
        self._main_window = main_window
        self._plugin_manager = plugin_manager
        self._logger = logger
        self._state_change_locks: Dict[str, asyncio.Lock] = {}
        self._processing_plugins: Set[str] = set()
    async def handle_plugin_state_change(self, plugin_id: str, enable: bool) -> None:
        from qorzen.core.plugin_manager import PluginState
        if plugin_id not in self._state_change_locks:
            self._state_change_locks[plugin_id] = asyncio.Lock()
        async with self._state_change_locks[plugin_id]:
            if plugin_id in self._processing_plugins:
                self._logger.debug(f"Plugin '{plugin_id}' is already being processed, skipping request")
                return
            self._processing_plugins.add(plugin_id)
            try:
                plugins = await self._plugin_manager.get_plugins()
                if plugin_id not in plugins:
                    self._logger.warning(f'Plugin not found: {plugin_id}')
                    return
                plugin_info = plugins[plugin_id]
                current_state = plugin_info.state
                is_active = current_state in (PluginState.ACTIVE, PluginState.LOADING)
                if enable and is_active or (not enable and (not is_active)):
                    self._logger.debug(f"Skipping redundant state change for plugin '{plugin_id}' (already {('enabled' if is_active else 'disabled')})")
                    return
                self._main_window.update_plugin_state_ui(plugin_info.name, 'loading' if enable else 'disabling')
                if enable:
                    await self._plugin_manager.enable_plugin(plugin_id)
                    await self._plugin_manager.load_plugin(plugin_id)
                else:
                    await self._plugin_manager.unload_plugin(plugin_id)
                    await self._plugin_manager.disable_plugin(plugin_id)
                updated_plugins = await self._plugin_manager.get_plugins()
                if plugin_id in updated_plugins:
                    final_plugin_info = updated_plugins[plugin_id]
                    state_val = final_plugin_info.state.value if hasattr(final_plugin_info.state, 'value') else str(final_plugin_info.state)
                    self._main_window.update_plugin_state_ui(final_plugin_info.name, state_val)
            except Exception as e:
                self._logger.error(f'Error changing plugin state: {e}', extra={'plugin_id': plugin_id, 'enable': enable, 'error': str(e)})
                plugins = await self._plugin_manager.get_plugins()
                if plugin_id in plugins:
                    self._main_window.update_plugin_state_ui(plugins[plugin_id].name, 'error')
            finally:
                self._processing_plugins.remove(plugin_id)
    async def handle_plugin_reload(self, plugin_id: str) -> None:
        if plugin_id not in self._state_change_locks:
            self._state_change_locks[plugin_id] = asyncio.Lock()
        async with self._state_change_locks[plugin_id]:
            if plugin_id in self._processing_plugins:
                self._logger.debug(f"Plugin '{plugin_id}' is already being processed, skipping reload request")
                return
            self._processing_plugins.add(plugin_id)
            try:
                plugins = await self._plugin_manager.get_plugins()
                if plugin_id in plugins:
                    plugin_name = plugins[plugin_id].name
                    self._main_window.update_plugin_state_ui(plugin_name, 'reloading')
                success = await self._plugin_manager.reload_plugin(plugin_id)
                if success:
                    self._logger.info(f'Successfully reloaded plugin: {plugin_id}')
                else:
                    self._logger.warning(f'Failed to reload plugin: {plugin_id}')
                updated_plugins = await self._plugin_manager.get_plugins()
                if plugin_id in updated_plugins:
                    final_plugin_info = updated_plugins[plugin_id]
                    state_val = final_plugin_info.state.value if hasattr(final_plugin_info.state, 'value') else str(final_plugin_info.state)
                    self._main_window.update_plugin_state_ui(final_plugin_info.name, state_val)
            except Exception as e:
                self._logger.error(f'Error reloading plugin: {e}', extra={'plugin_id': plugin_id, 'error': str(e)})
                plugins = await self._plugin_manager.get_plugins()
                if plugin_id in plugins:
                    self._main_window.update_plugin_state_ui(plugins[plugin_id].name, 'error')
            finally:
                self._processing_plugins.remove(plugin_id)
class MainWindow(QMainWindow):
    def __init__(self, app_core: Any) -> None:
        super().__init__()
        self._app_core = app_core
        self._config_manager = app_core.get_manager('config_manager')
        self._logging_manager = app_core.get_manager('logging_manager')
        self._event_bus_manager = app_core.get_manager('event_bus_manager')
        self._plugin_manager = app_core.get_manager('plugin_manager')
        self._monitoring_manager = app_core.get_manager('monitoring_manager')
        if self._logging_manager:
            self._logger = self._logging_manager.get_logger('ui.main_window')
        else:
            import logging
            self._logger = logging.getLogger('ui.main_window')
        self._menus: Dict[str, QMenu] = {}
        self._toolbars: Dict[str, QToolBar] = {}
        self._ui_elements: Dict[str, Any] = {}
        self._dock_widgets: Dict[str, QDockWidget] = {}
        self._setup_ui()
        self._subscribe_to_events()
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start(5000)
        self._plugin_handler = MainWindowPluginHandler(self, self._plugin_manager, self._logger)
        self._logger.info('Qorzen UI started')
    def _setup_ui(self) -> None:
        self.setWindowTitle('Qorzen')
        self.setMinimumSize(1024, 768)
        self._create_menu_bar()
        self.panel_layout = self._create_panel_layout()
        self.setCentralWidget(self.panel_layout)
        self._create_settings_page()
        self._create_dashboard_page()
        self._create_plugins_page()
        self._create_logs_page()
        self._create_task_monitor()
        self.statusBar().showMessage('Ready')
    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        self._menus['File'] = file_menu
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        edit_menu = menu_bar.addMenu('&Edit')
        self._menus['Edit'] = edit_menu
        preferences_action = QAction('&Preferences', self)
        preferences_action.triggered.connect(self._show_preferences)
        edit_menu.addAction(preferences_action)
        view_menu = menu_bar.addMenu('&View')
        self._menus['View'] = view_menu
        window_menu = menu_bar.addMenu('&Window')
        self._menus['Window'] = window_menu
        plugins_menu = menu_bar.addMenu('&Plugins')
        self._menus['Plugins'] = plugins_menu
        help_menu = menu_bar.addMenu('&Help')
        self._menus['Help'] = help_menu
        about_action = QAction('&About', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    def _show_preferences(self) -> None:
        self._logger.debug('Show preferences dialog')
    def _show_about(self) -> None:
        self._logger.debug('Show about dialog')
    def _create_panel_layout(self) -> QWidget:
        panel_widget = QWidget()
        main_layout = QHBoxLayout(panel_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.sidebar = self._create_sidebar()
        self.content_area = QStackedWidget()
        self.content_area.setFrameShape(QFrame.StyledPanel)
        self.content_area.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area, 1)
        return panel_widget
    def _create_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setMinimumWidth(200)
        sidebar.setMaximumWidth(200)
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setFrameShadow(QFrame.Raised)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        logo_label = QLabel('Qorzen')
        logo_label.setStyleSheet('font-size: 18px; font-weight: bold;')
        header_layout.addWidget(logo_label)
        collapse_button = QPushButton()
        collapse_button.setIcon(QIcon.fromTheme('go-previous'))
        collapse_button.setIconSize(QSize(16, 16))
        collapse_button.setFlat(True)
        collapse_button.setFixedSize(24, 24)
        collapse_button.clicked.connect(self._toggle_sidebar_collapse)
        header_layout.addWidget(collapse_button)
        layout.addWidget(header)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        buttons_container = QWidget()
        self.sidebar_buttons_layout = QVBoxLayout(buttons_container)
        self.sidebar_buttons_layout.setContentsMargins(0, 10, 0, 10)
        self.sidebar_buttons_layout.setSpacing(2)
        self.sidebar_buttons_layout.addStretch()
        layout.addWidget(buttons_container)
        self.sidebar = sidebar
        self.sidebar_collapse_button = collapse_button
        self.sidebar_buttons_container = buttons_container
        return sidebar
    def _toggle_sidebar_collapse(self) -> None:
        if self.sidebar.width() == 200:
            self.sidebar.setMinimumWidth(48)
            self.sidebar.setMaximumWidth(48)
            self.sidebar_collapse_button.setIcon(QIcon.fromTheme('go-next'))
            for i in range(self.sidebar_buttons_layout.count()):
                item = self.sidebar_buttons_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QPushButton):
                    btn = item.widget()
                    btn.setText('')
                    if hasattr(btn, 'full_text'):
                        btn.setToolTip(btn.full_text)
        else:
            self.sidebar.setMinimumWidth(200)
            self.sidebar.setMaximumWidth(200)
            self.sidebar_collapse_button.setIcon(QIcon.fromTheme('go-previous'))
            for i in range(self.sidebar_buttons_layout.count()):
                item = self.sidebar_buttons_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QPushButton):
                    btn = item.widget()
                    if hasattr(btn, 'full_text'):
                        btn.setText(btn.full_text)
                        btn.setToolTip('')
    def add_page(self, element_id: str, widget: QWidget, title: str, icon: Optional[str]=None, position: Optional[int]=None) -> None:
        widget.setObjectName(element_id)
        index = self.content_area.addWidget(widget)
        button = QPushButton(title)
        button.full_text = title
        if icon:
            button.setIcon(QIcon(icon))
        button.setIconSize(QSize(24, 24))
        button.setCheckable(True)
        button.setFlat(True)
        button.setMinimumHeight(48)
        button.setMaximumHeight(48)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setStyleSheet('\n            QPushButton {\n                text-align: left;\n                border: none;\n                border-radius: 4px;\n                padding: 8px;\n                margin: 2px 4px;\n                background-color: transparent;\n            }\n            QPushButton:hover {\n                background-color: rgba(200, 200, 200, 0.2);\n            }\n            QPushButton:checked {\n                background-color: rgba(0, 120, 215, 0.2);\n                color: #0078d7;\n            }\n        ')
        button.clicked.connect(lambda checked, idx=index: self._on_sidebar_button_clicked(idx))
        if position is not None and position < self.sidebar_buttons_layout.count() - 1:
            self.sidebar_buttons_layout.insertWidget(position, button)
        else:
            self.sidebar_buttons_layout.insertWidget(self.sidebar_buttons_layout.count() - 1, button)
        self._ui_elements[element_id] = {'type': 'page', 'widget': widget, 'button': button, 'index': index}
        self._logger.debug(f'Added page: {element_id}')
    def _on_sidebar_button_clicked(self, page_index: int) -> None:
        for element_info in self._ui_elements.values():
            if element_info['type'] == 'page' and 'button' in element_info:
                button = element_info['button']
                if hasattr(button, 'setChecked'):
                    button.setChecked(element_info['index'] == page_index)
        self.content_area.setCurrentIndex(page_index)
    def add_menu_item(self, element_id: str, title: str, callback: Callable[[], None], parent_menu: str='Plugins', icon: Optional[str]=None, position: Optional[int]=None, tooltip: Optional[str]=None) -> None:
        menu = self._menus.get(parent_menu)
        if not menu:
            self._logger.warning(f"Parent menu '{parent_menu}' not found, creating it")
            menu = self.menuBar().addMenu(parent_menu)
            self._menus[parent_menu] = menu
        action = QAction(title, self)
        if icon:
            action.setIcon(QIcon(icon))
        if tooltip:
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
        action.triggered.connect(callback)
        menu.addAction(action)
        self._ui_elements[element_id] = {'type': 'menu_item', 'action': action, 'menu': menu}
        self._logger.debug(f'Added menu item: {element_id} to {parent_menu}')
    def add_toolbar_item(self, element_id: str, title: str, callback: Callable[[], None], icon: Optional[str]=None, position: Optional[int]=None, tooltip: Optional[str]=None) -> None:
        toolbar_name = 'main_toolbar'
        if toolbar_name not in self._toolbars:
            toolbar = self.addToolBar('Main Toolbar')
            self._toolbars[toolbar_name] = toolbar
        else:
            toolbar = self._toolbars[toolbar_name]
        action = QAction(title, self)
        if icon:
            action.setIcon(QIcon(icon))
        if tooltip:
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
        action.triggered.connect(callback)
        toolbar.addAction(action)
        self._ui_elements[element_id] = {'type': 'toolbar_item', 'action': action, 'toolbar': toolbar}
        self._logger.debug(f'Added toolbar item: {element_id}')
    def add_widget(self, element_id: str, widget: QWidget, parent_id: str, title: Optional[str]=None, position: Optional[int]=None) -> None:
        if parent_id not in self._ui_elements:
            raise UIError(f'Parent container {parent_id} not found', element_id=element_id, element_type='widget', operation='add_widget')
        parent_info = self._ui_elements[parent_id]
        parent_widget = parent_info.get('widget')
        if not parent_widget or not hasattr(parent_widget, 'layout'):
            raise UIError(f'Parent {parent_id} is not a valid container', element_id=element_id, element_type='widget', operation='add_widget')
        parent_layout = parent_widget.layout()
        if not parent_layout:
            raise UIError(f'Parent {parent_id} has no layout', element_id=element_id, element_type='widget', operation='add_widget')
        if position is not None:
            parent_layout.insertWidget(position, widget)
        else:
            parent_layout.addWidget(widget)
        self._ui_elements[element_id] = {'type': 'widget', 'widget': widget, 'parent_id': parent_id}
        self._logger.debug(f'Added widget: {element_id} to parent {parent_id}')
    def add_panel(self, element_id: str, panel: QWidget, title: str, dock_area: str='right', icon: Optional[str]=None, closable: bool=True) -> None:
        dock_widget = QDockWidget(title, self)
        dock_widget.setWidget(panel)
        features = QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        if closable:
            features |= QDockWidget.DockWidgetClosable
        dock_widget.setFeatures(features)
        if icon:
            dock_widget.setWindowIcon(QIcon(icon))
        area_map = {'left': Qt.LeftDockWidgetArea, 'right': Qt.RightDockWidgetArea, 'top': Qt.TopDockWidgetArea, 'bottom': Qt.BottomDockWidgetArea}
        dock_area_enum = area_map.get(dock_area.lower(), Qt.RightDockWidgetArea)
        self.addDockWidget(dock_area_enum, dock_widget)
        view_menu = self._menus.get('View')
        if view_menu:
            view_menu.addAction(dock_widget.toggleViewAction())
        self._ui_elements[element_id] = {'type': 'panel', 'widget': panel, 'dock_widget': dock_widget, 'dock_area': dock_area}
        self._dock_widgets[element_id] = dock_widget
        self._logger.debug(f'Added panel: {element_id} to {dock_area}')
    def show_dialog(self, element_id: str, dialog: QWidget, title: str, modal: bool=True, width: int=400, height: int=300) -> None:
        dialog.setWindowTitle(title)
        dialog.resize(width, height)
        if hasattr(dialog, 'setModal'):
            dialog.setModal(modal)
        self._ui_elements[element_id] = {'type': 'dialog', 'widget': dialog, 'modal': modal}
        dialog.show()
        self._logger.debug(f'Showing dialog: {element_id}')
    def show_notification(self, message: str, title: Optional[str]=None, notification_type: str='info', duration: int=5000) -> None:
        full_message = f'{title}: {message}' if title else message
        self.statusBar().showMessage(full_message, duration)
        log_level = 'info'
        if notification_type == 'warning':
            log_level = 'warning'
        elif notification_type == 'error':
            log_level = 'error'
        log_method = getattr(self._logger, log_level, self._logger.info)
        log_method(f'Notification: {full_message}', extra={'notification_type': notification_type})
    def remove_element(self, element_id: str) -> None:
        if element_id not in self._ui_elements:
            self._logger.warning(f'Cannot remove element {element_id}: not found')
            return
        element_info = self._ui_elements[element_id]
        element_type = element_info.get('type', 'unknown')
        if element_type == 'page':
            widget = element_info.get('widget')
            button = element_info.get('button')
            index = element_info.get('index')
            if widget and index is not None:
                self.content_area.removeWidget(widget)
                widget.deleteLater()
            if button:
                self.sidebar_buttons_layout.removeWidget(button)
                button.hide()
                button.setParent(None)
                button.deleteLater()
        elif element_type == 'menu_item':
            action = element_info.get('action')
            menu = element_info.get('menu')
            if action and menu:
                menu.removeAction(action)
        elif element_type == 'toolbar_item':
            action = element_info.get('action')
            toolbar = element_info.get('toolbar')
            if action and toolbar:
                toolbar.removeAction(action)
        elif element_type == 'widget':
            widget = element_info.get('widget')
            parent_id = element_info.get('parent_id')
            if widget and parent_id and (parent_id in self._ui_elements):
                parent_widget = self._ui_elements[parent_id].get('widget')
                if parent_widget and hasattr(parent_widget, 'layout'):
                    parent_layout = parent_widget.layout()
                    if parent_layout:
                        parent_layout.removeWidget(widget)
                        widget.deleteLater()
        elif element_type == 'panel':
            dock_widget = element_info.get('dock_widget')
            if dock_widget:
                self.removeDockWidget(dock_widget)
                dock_widget.deleteLater()
            if element_id in self._dock_widgets:
                del self._dock_widgets[element_id]
        elif element_type == 'dialog':
            widget = element_info.get('widget')
            if widget and hasattr(widget, 'close'):
                widget.close()
        del self._ui_elements[element_id]
        self._logger.debug(f'Removed element: {element_id} (type: {element_type})')
    def update_element(self, element_id: str, visible: Optional[bool]=None, enabled: Optional[bool]=None, title: Optional[str]=None, icon: Optional[str]=None, tooltip: Optional[str]=None) -> None:
        if element_id not in self._ui_elements:
            self._logger.warning(f'Cannot update element {element_id}: not found')
            return
        element_info = self._ui_elements[element_id]
        element_type = element_info.get('type', 'unknown')
        if element_type in ('page', 'widget', 'panel', 'dialog'):
            widget = element_info.get('widget')
            if widget:
                if visible is not None:
                    widget.setVisible(visible)
                if enabled is not None:
                    widget.setEnabled(enabled)
                if title is not None and hasattr(widget, 'setWindowTitle'):
                    widget.setWindowTitle(title)
                if tooltip is not None and hasattr(widget, 'setToolTip'):
                    widget.setToolTip(tooltip)
                if element_type == 'page':
                    button = element_info.get('button')
                    if button:
                        if title is not None:
                            button.setText(title)
                            button.full_text = title
                        if enabled is not None:
                            button.setEnabled(enabled)
                        if visible is not None:
                            button.setVisible(visible)
                        if icon is not None:
                            button.setIcon(QIcon(icon))
                        if tooltip is not None:
                            button.setToolTip(tooltip)
                if element_type == 'panel':
                    dock_widget = element_info.get('dock_widget')
                    if dock_widget:
                        if title is not None:
                            dock_widget.setWindowTitle(title)
                        if visible is not None:
                            dock_widget.setVisible(visible)
                        if icon is not None:
                            dock_widget.setWindowIcon(QIcon(icon))
        elif element_type in ('menu_item', 'toolbar_item'):
            action = element_info.get('action')
            if action:
                if visible is not None:
                    action.setVisible(visible)
                if enabled is not None:
                    action.setEnabled(enabled)
                if title is not None:
                    action.setText(title)
                if icon is not None:
                    action.setIcon(QIcon(icon))
                if tooltip is not None:
                    action.setToolTip(tooltip)
                    action.setStatusTip(tooltip)
        self._logger.debug(f'Updated element: {element_id}')
    def get_menu(self, menu_name: str) -> Optional[QMenu]:
        return self._menus.get(menu_name)
    def _create_settings_page(self) -> None:
        from qorzen.ui.settings_manager import SettingsManager
        settings_manager = SettingsManager(self._app_core, self)
        self.add_page('settings_manager', settings_manager, 'Settings', ':/ui_icons/dashboard.svg')
    def _create_dashboard_page(self) -> None:
        from qorzen.ui.dashboard import DashboardWidget
        dashboard = DashboardWidget(self._app_core, self)
        self.add_page('dashboard', dashboard, 'Dashboard', ':/ui_icons/dashboard.svg')
    def _create_plugins_page(self) -> None:
        from qorzen.ui.plugins import PluginsView
        plugins_view = PluginsView(self._plugin_manager, self)
        if hasattr(plugins_view, 'pluginStateChangeRequested'):
            plugins_view.pluginStateChangeRequested.connect(self._on_plugin_state_change)
        if hasattr(plugins_view, 'pluginReloadRequested'):
            plugins_view.pluginReloadRequested.connect(self._on_plugin_reload)
        if hasattr(plugins_view, 'pluginInfoRequested'):
            plugins_view.pluginInfoRequested.connect(self._on_plugin_info)
        self.add_page('plugins', plugins_view, 'Plugins', ':/ui_icons/extension.svg')
    def _create_logs_page(self) -> None:
        from qorzen.ui.logs import LogsView
        logs_view = LogsView(self._event_bus_manager, self)
        self.add_page('logs', logs_view, 'Logs', ':/ui_icons/library-books.svg')
    def _create_task_monitor(self) -> None:
        from qorzen.ui.task_monitor import TaskMonitorWidget
        task_monitor = TaskMonitorWidget(self._event_bus_manager, self)
        task_dock = QDockWidget('Tasks', self)
        task_dock.setWidget(task_monitor)
        task_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, task_dock)
        view_menu = self.get_menu('View')
        if view_menu:
            view_menu.addAction(task_dock.toggleViewAction())
        self._ui_elements['task_monitor'] = {'type': 'panel', 'widget': task_monitor, 'dock_widget': task_dock, 'dock_area': 'bottom'}
        self._dock_widgets['task_monitor'] = task_dock
        self.task_monitor = task_monitor
    def _subscribe_to_events(self) -> None:
        if not self._event_bus_manager:
            return
        self._subscribe_to_events_task = asyncio.create_task(self._async_subscribe_to_events())
    async def _async_subscribe_to_events(self) -> None:
        if not self._event_bus_manager:
            return
        await self._event_bus_manager.subscribe(event_type='plugin/loaded', callback=self._on_plugin_loaded_event, subscriber_id='ui_plugin_loaded')
        await self._event_bus_manager.subscribe(event_type='plugin/unloaded', callback=self._on_plugin_unloaded_event, subscriber_id='ui_plugin_unloaded')
    async def _on_plugin_loaded_event(self, event: Any) -> None:
        payload = event.payload
        plugin_id = payload.get('plugin_id', '')
        self._logger.debug(f'Plugin loaded: {plugin_id}')
    async def _on_plugin_unloaded_event(self, event: Any) -> None:
        payload = event.payload
        plugin_id = payload.get('plugin_id', '')
        self._logger.debug(f'Plugin unloaded: {plugin_id}')
    def _on_plugin_state_change(self, plugin_id: str, enable: bool) -> None:
        asyncio.create_task(self._plugin_handler.handle_plugin_state_change(plugin_id, enable))
    async def _async_handle_plugin_state_change(self, plugin_id: str, enable: bool) -> None:
        if not self._plugin_manager:
            return
        try:
            plugins = await self._plugin_manager.get_plugins()
            if plugin_id not in plugins:
                self._logger.warning(f'Plugin not found: {plugin_id}')
                return
            plugin_info = plugins[plugin_id]
            current_state = plugin_info.state
            is_active = current_state in ('active', 'loading')
            if enable and is_active or (not enable and (not is_active)):
                self._logger.debug(f"Skipping redundant state change for plugin '{plugin_id}' (already {('enabled' if is_active else 'disabled')})")
                return
            self.update_plugin_state_ui(plugin_id, 'loading' if enable else 'disabling')
            self._processing_plugin = plugin_id
            if enable:
                await self._plugin_manager.enable_plugin(plugin_id)
                await self._plugin_manager.load_plugin(plugin_id)
            else:
                await self._plugin_manager.unload_plugin(plugin_id)
                await self._plugin_manager.disable_plugin(plugin_id)
            self._processing_plugin = None
            updated_plugins = await self._plugin_manager.get_plugins()
            if plugin_id in updated_plugins:
                final_plugin_info = updated_plugins[plugin_id]
                self.update_plugin_state_ui(plugin_id, final_plugin_info.state)
        except Exception as e:
            self._logger.error(f'Error changing plugin state: {e}', extra={'plugin_id': plugin_id, 'enable': enable, 'error': str(e)})
            self.update_plugin_state_ui(plugin_id, 'error')
            self._processing_plugin = None
    def update_plugin_state_ui(self, plugin_name: str, state: str) -> None:
        self._logger.debug(f'Plugin {plugin_name} state changed to {state}')
    def _on_plugin_reload(self, plugin_id: str) -> None:
        asyncio.create_task(self._plugin_handler.handle_plugin_reload(plugin_id))
    async def _async_handle_plugin_reload(self, plugin_name: str) -> None:
        if not self._plugin_manager:
            return
        try:
            self.update_plugin_state_ui(plugin_name, 'reloading')
            success = await self._plugin_manager.reload_plugin(plugin_name)
            if success:
                self._logger.info(f'Successfully reloaded plugin: {plugin_name}')
            else:
                self._logger.warning(f'Failed to reload plugin: {plugin_name}')
        except Exception as e:
            self._logger.error(f'Error reloading plugin: {e}', extra={'plugin_name': plugin_name, 'error': str(e)})
            self.update_plugin_state_ui(plugin_name, 'error')
    def _on_plugin_info(self, plugin_name: str) -> None:
        self._logger.debug(f'Show info for plugin: {plugin_name}')
    def _update_status(self) -> None:
        self.statusBar().showMessage(f"Ready - Last update: {time.strftime('%H:%M:%S')}")
    def select_page(self, page_name: str) -> None:
        for element_id, element_info in self._ui_elements.items():
            if element_info['type'] == 'page' and element_id == page_name:
                index = element_info.get('index')
                if index is not None:
                    self._on_sidebar_button_clicked(index)
                    return
    def closeEvent(self, event: Any) -> None:
        if hasattr(self, '_update_timer'):
            self._update_timer.stop()
        if self._event_bus_manager:
            asyncio.create_task(self._async_cleanup())
        if hasattr(self, 'task_monitor'):
            if hasattr(self.task_monitor, 'cleanup'):
                self.task_monitor.cleanup()
        if self._app_core:
            asyncio.create_task(self._app_core.shutdown())
        event.accept()
    async def _async_cleanup(self) -> None:
        if self._event_bus_manager:
            await self._event_bus_manager.unsubscribe(subscriber_id='ui_plugin_loaded')
            await self._event_bus_manager.unsubscribe(subscriber_id='ui_plugin_unloaded')