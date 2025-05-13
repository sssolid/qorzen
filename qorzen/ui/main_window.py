from __future__ import annotations
import os
import sys
import time
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QStackedWidget,
    QVBoxLayout, QWidget, QDockWidget, QToolBar
)

from qorzen.ui.task_monitor import TaskMonitorWidget


class SidebarButton(QPushButton):
    def __init__(self, icon: QIcon, text: str, parent: Optional[QWidget] = None, checkable: bool = True) -> None:
        super().__init__(parent)
        self.text = text
        self.setText(self.text)
        self.setIcon(icon)
        self.setIconSize(QSize(24, 24))
        self.setCheckable(checkable)
        self.setFlat(True)
        self.setMinimumHeight(48)
        self.setMaximumHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet('''
            QPushButton {
                text-align: left;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin: 2px 4px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 0.2);
            }
            QPushButton:checked {
                background-color: rgba(0, 120, 215, 0.2);
                color: #0078d7;
            }
        ''')


class Sidebar(QFrame):
    pageChangeRequested = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setMaximumWidth(200)
        self._collapsed = False
        self._buttons: List[SidebarButton] = []
        self._button_group: Dict[str, List[SidebarButton]] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)

        logo_label = QLabel('Qorzen')
        logo_label.setStyleSheet('font-size: 18px; font-weight: bold;')
        header_layout.addWidget(logo_label)

        self.collapse_button = QPushButton()
        self.collapse_button.setIcon(QIcon.fromTheme('go-previous'))
        self.collapse_button.setIconSize(QSize(16, 16))
        self.collapse_button.setFlat(True)
        self.collapse_button.setFixedSize(24, 24)
        self.collapse_button.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.collapse_button)

        self._layout.addWidget(header)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self._layout.addWidget(separator)

        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 10, 0, 10)
        self.buttons_layout.setSpacing(2)
        self.buttons_layout.addStretch()

        self._layout.addWidget(self.buttons_container)

    def add_button(self, icon: QIcon, text: str, page_index: int, group: Optional[str] = None,
                   checkable: bool = True) -> SidebarButton:
        button = SidebarButton(icon, text, self, checkable)
        button.clicked.connect(lambda checked, idx=page_index: self._on_button_clicked(idx))
        self.buttons_layout.insertWidget(self.buttons_layout.count() - 1, button)
        self._buttons.append(button)

        if group:
            if group not in self._button_group:
                self._button_group[group] = []
            self._button_group[group].append(button)

        return button

    def remove_button(self, button_index: int) -> None:
        """
        Remove a button from the sidebar.

        Args:
            button_index: Index of the button to remove
        """
        if 0 <= button_index < len(self._buttons):
            button = self._buttons[button_index]
            self.buttons_layout.removeWidget(button)
            button.deleteLater()
            self._buttons.pop(button_index)

    def add_separator(self) -> None:
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.buttons_layout.insertWidget(self.buttons_layout.count() - 1, separator)

    def _on_button_clicked(self, page_index: int) -> None:
        for button in self._buttons:
            if button.isCheckable():
                button.setChecked(False)

        sender = self.sender()
        if sender and isinstance(sender, SidebarButton) and sender.isCheckable():
            sender.setChecked(True)

        self.pageChangeRequested.emit(page_index)

    def _toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed

        if self._collapsed:
            self.setMinimumWidth(48)
            self.setMaximumWidth(48)
            self.collapse_button.setIcon(QIcon.fromTheme('go-next'))
            for button in self._buttons:
                button.setText('')
                button.setToolTip(button.text)
        else:
            self.setMinimumWidth(200)
            self.setMaximumWidth(200)
            self.collapse_button.setIcon(QIcon.fromTheme('go-previous'))
            for button in self._buttons:
                button.setText(button.text)

    def select_page(self, page_index: int) -> None:
        for button in self._buttons:
            if button.isCheckable():
                button.setChecked(False)

        for i, button in enumerate(self._buttons):
            if i == page_index and button.isCheckable():
                button.setChecked(True)
                break


class ContentArea(QStackedWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)

    def add_page(self, widget: QWidget, name: str) -> int:
        index = self.addWidget(widget)
        widget.setObjectName(name)
        return index

    def get_page_by_name(self, name: str) -> Optional[QWidget]:
        for i in range(self.count()):
            widget = self.widget(i)
            if widget and widget.objectName() == name:
                return widget
        return None


class PanelLayout(QWidget):
    def __init__(self, parent: Optional[QWidget] = None, app_core: Optional[Any] = None) -> None:
        super().__init__(parent)
        self._app_core = app_core
        self._pages: Dict[str, QWidget] = {}
        self._page_names: List[str] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar(self)
        self.content_area = ContentArea(self)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area, 1)

        self.sidebar.pageChangeRequested.connect(self.content_area.setCurrentIndex)

    def add_page(self, widget: QWidget, name: str, icon: QIcon, text: str, group: Optional[str] = None) -> int:
        index = self.content_area.add_page(widget, name)
        self.sidebar.add_button(icon, text, index, group)
        self._pages[name] = widget
        self._page_names.append(name)
        return index

    def remove_page(self, page_name: str) -> None:
        """
        Remove a page and its sidebar button.

        Args:
            page_name: Name of the page to remove
        """
        if page_name in self._page_names:
            index = self._page_names.index(page_name)
            self._page_names.remove(page_name)

            # Remove the sidebar button
            self.sidebar.remove_button(index)

            # Remove from the pages dictionary
            if page_name in self._pages:
                del self._pages[page_name]

    def add_separator(self) -> None:
        self.sidebar.add_separator()

    def select_page(self, page_name: str) -> None:
        for i, name in enumerate(self._page_names):
            if name == page_name:
                self.sidebar.select_page(i)
                self.content_area.setCurrentIndex(i)
                break


class MainWindow(QMainWindow):
    def __init__(self, app_core: Any) -> None:
        super().__init__()
        self._app_core = app_core
        self._config_manager = app_core.get_manager('config_manager')
        self._logging_manager = app_core.get_manager('logging_manager')
        self._event_bus = app_core.get_manager('event_bus_manager')
        self._plugin_manager = app_core.get_manager('plugin_manager')
        self._monitoring_manager = app_core.get_manager('resource_monitoring_manager')

        if self._logging_manager:
            self._logger = self._logging_manager.get_logger('ui')
        else:
            import logging
            self._logger = logging.getLogger('ui')

        # Add _menus dictionary to store menu references
        self._menus: Dict[str, QMenu] = {}
        self._toolbars: Dict[str, QToolBar] = {}

        self._setup_ui()
        self._subscribe_to_events()

        from ..core.plugin_error_handler import PluginErrorHandler
        self._plugin_error_handler = PluginErrorHandler(self._event_bus, self._plugin_manager, self)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start(5000)

        self._logger.info('Qorzen UI started')

    def _setup_ui(self) -> None:
        self.setWindowTitle('Qorzen')
        self.setMinimumSize(1024, 768)

        # Create menu bar
        self._create_menu_bar()

        self.panel_layout = PanelLayout(self, self._app_core)
        self.setCentralWidget(self.panel_layout)

        self._create_dashboard_page()
        self._create_plugins_page()
        self._create_logs_page()

        # Create task monitor dock widget
        self.task_monitor = TaskMonitorWidget(self._event_bus)
        self.task_dock = QDockWidget("Tasks", self)
        self.task_dock.setWidget(self.task_monitor)
        self.task_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.task_dock)

        # Add task monitor toggle to view menu
        view_menu = self.menuBar().findChild(QMenu, "View")
        if view_menu:
            view_menu.addAction(self.task_dock.toggleViewAction())

        self.panel_layout.add_separator()
        self.statusBar().showMessage('Ready')

    def _create_menu_bar(self) -> None:
        """Create the main menu bar with standard menu items."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu('&File')
        self._menus['File'] = file_menu

        # Add some common file actions
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu('&Edit')
        self._menus['Edit'] = edit_menu

        # Add some common edit actions
        preferences_action = QAction('&Preferences', self)
        preferences_action.triggered.connect(self._show_preferences)
        edit_menu.addAction(preferences_action)

        # View Menu
        view_menu = menu_bar.addMenu('&View')
        self._menus['View'] = view_menu

        # Window Menu
        window_menu = menu_bar.addMenu('&Window')
        self._menus['Window'] = window_menu

        # Plugins Menu - will be populated by plugins
        plugins_menu = menu_bar.addMenu('&Plugins')
        self._menus['Plugins'] = plugins_menu

        # Help Menu
        help_menu = menu_bar.addMenu('&Help')
        self._menus['Help'] = help_menu

        # Add some common help actions
        about_action = QAction('&About', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # Store _central_tabs for UI integration
        self._central_tabs = None

    def _show_preferences(self) -> None:
        """Show the preferences dialog."""
        self._logger.debug("Show preferences dialog")
        # Implement preferences dialog

    def _show_about(self) -> None:
        """Show the about dialog."""
        self._logger.debug("Show about dialog")
        # Implement about dialog

    def get_menu(self, menu_name: str) -> Optional[QMenu]:
        """Get a menu by name, if it exists."""
        return self._menus.get(menu_name)

    def _create_dashboard_page(self) -> None:
        from qorzen.ui.dashboard import DashboardWidget
        dashboard = DashboardWidget(self._app_core, self)
        self.panel_layout.add_page(dashboard, 'dashboard', QIcon(':/ui_icons/dashboard.svg'), 'Dashboard', 'system')

    def _create_plugins_page(self) -> None:
        from qorzen.ui.plugins import PluginsView
        plugins_view = PluginsView(self._plugin_manager, self)
        plugins_view.pluginStateChangeRequested.connect(self._on_plugin_state_change)
        plugins_view.pluginReloadRequested.connect(self._on_plugin_reload)
        plugins_view.pluginInfoRequested.connect(self._on_plugin_info)
        self.panel_layout.add_page(plugins_view, 'plugins', QIcon(':/ui_icons/extension.svg'), 'Plugins', 'system')

    def _create_logs_page(self) -> None:
        from qorzen.ui.logs import LogsView
        logs_view = LogsView(self._event_bus, self)
        self.panel_layout.add_page(logs_view, 'logs', QIcon(':/ui_icons/library-books.svg'), 'Logs', 'system')

    def _subscribe_to_events(self) -> None:
        if not self._event_bus:
            return

        self._event_bus.subscribe(
            event_type='plugin/loaded',
            callback=self._on_plugin_loaded_event,
            subscriber_id='ui_plugin_loaded'
        )

        self._event_bus.subscribe(
            event_type='plugin/unloaded',
            callback=self._on_plugin_unloaded_event,
            subscriber_id='ui_plugin_unloaded'
        )

    def _update_status(self) -> None:
        self.statusBar().showMessage(f"Ready - Last update: {time.strftime('%H:%M:%S')}")

    def _on_plugin_state_change(self, plugin_name: str, enable: bool) -> None:
        """
        Handle plugin state change request from the UI.

        Args:
            plugin_name: Name of the plugin to enable/disable
            enable: Whether to enable (True) or disable (False) the plugin
        """
        if not self._plugin_manager:
            return

        try:
            # First make UI changes to reflect the pending change
            plugins_view = self.panel_layout.content_area.get_page_by_name('plugins')
            if plugins_view and hasattr(plugins_view, '_plugin_cards'):
                if plugin_name in plugins_view._plugin_cards:
                    card = plugins_view._plugin_cards[plugin_name]
                    # Keep the checkbox checked/unchecked based on user action
                    card.enable_checkbox.setChecked(enable)
                    if enable:
                        card.status_label.setText('Status: Loading...')
                        card.status_label.setStyleSheet('font-weight: bold; color: #17a2b8;')

            # Then process the state change
            if enable:
                # Enable the plugin but load it asynchronously
                self._plugin_manager.enable_plugin(plugin_name)

                # Create a wrapper function that ignores the progress_reporter
                def load_plugin_wrapper(plugin_name_to_load, progress_reporter=None):
                    return self._plugin_manager.load_plugin(plugin_name_to_load)

                # Submit asynchronous task to load the plugin
                thread_manager = self._app_core.get_manager('thread_manager')
                if thread_manager:
                    thread_manager.submit_task(
                        load_plugin_wrapper,
                        plugin_name,
                        name=f'load_plugin_{plugin_name}',
                        submitter='main_window'
                    )
            elif self._plugin_manager.unload_plugin(plugin_name):
                self._plugin_manager.disable_plugin(plugin_name)

        except Exception as e:
            self._logger.error(f'Error changing plugin state: {str(e)}',
                               extra={'plugin_name': plugin_name, 'enable': enable})

            # Revert UI state on error
            plugins_view = self.panel_layout.content_area.get_page_by_name('plugins')
            if plugins_view and hasattr(plugins_view, '_plugin_cards'):
                if plugin_name in plugins_view._plugin_cards:
                    card = plugins_view._plugin_cards[plugin_name]
                    card.enable_checkbox.setChecked(not enable)

    def _on_plugin_reload(self, plugin_name: str) -> None:
        if not self._plugin_manager:
            return

        try:
            success = self._plugin_manager.reload_plugin(plugin_name)
            if success:
                self._logger.info(f'Successfully reloaded plugin: {plugin_name}')
            else:
                self._logger.warning(f'Failed to reload plugin: {plugin_name}')
        except Exception as e:
            self._logger.error(
                f'Error reloading plugin: {str(e)}',
                extra={'plugin_name': plugin_name}
            )

    def _on_plugin_info(self, plugin_name: str) -> None:
        pass

    def _on_plugin_loaded_event(self, event: Any) -> None:
        from qorzen.core.plugin_manager import PluginInfo

        payload = event.payload
        plugin_name = payload.get('plugin_name', '')

        if not plugin_name:
            return

        if not self._plugin_manager:
            return

        plugins = self._plugin_manager.get_all_plugins()
        plugin_info: PluginInfo = plugins.get(plugin_name)

        if not plugin_info:
            return

        instance = plugin_info.metadata.get('instance')

        if not instance:
            return

        self._add_plugin_ui_components(plugin_name, instance)

    def _on_plugin_unloaded_event(self, event: Any) -> None:
        payload = event.payload
        plugin_name = payload.get('plugin_name', '')

        if not plugin_name:
            return

        self._remove_plugin_ui_components(plugin_name)

    def _add_plugin_ui_components(self, plugin_name: str, instance: Any) -> None:
        if not hasattr(instance, 'get_main_widget'):
            return

        try:
            # Check if page already exists
            page_name = f'plugin_{plugin_name}'
            existing_page = self.panel_layout.content_area.get_page_by_name(page_name)
            if existing_page:
                self._logger.debug(f"UI components for plugin '{plugin_name}' already exist")
                return

            widget = instance.get_main_widget()

            if not widget:
                return

            icon = QIcon()
            if hasattr(instance, 'get_icon') and callable(instance.get_icon):
                icon_path = instance.get_icon()
                if icon_path and os.path.exists(icon_path):
                    icon = QIcon(icon_path)

            display_name = plugin_name
            if hasattr(instance, 'display_name'):
                display_name = instance.display_name

            self.panel_layout.add_page(widget, f'plugin_{plugin_name}', icon, display_name, 'plugins')
            self._logger.info(f'Added UI components for plugin: {plugin_name}')

        except Exception as e:
            self._logger.error(
                f'Error adding UI components for plugin {plugin_name}: {str(e)}',
                extra={'plugin_name': plugin_name}
            )

    def _remove_plugin_ui_components(self, plugin_name: str) -> None:
        """
        Remove UI components for a plugin.

        Args:
            plugin_name: Name of the plugin to remove components for
        """
        # First find and remove the panel page
        page_name = f"plugin_{plugin_name}"
        self.panel_layout.select_page("dashboard")  # Select default page

        # Remove the page
        page = self.panel_layout.content_area.get_page_by_name(page_name)
        if page:
            index = self.panel_layout.content_area.indexOf(page)
            if index >= 0:
                self.panel_layout.content_area.removeWidget(page)
                page.deleteLater()

                # Also remove the button from sidebar
                self.panel_layout.remove_page(page_name)

                self._logger.info(f"Removed UI components for plugin: {plugin_name}")

    def closeEvent(self, event: Any) -> None:
        self._update_timer.stop()

        if self._event_bus:
            self._event_bus.unsubscribe(subscriber_id='ui_plugin_loaded')
            self._event_bus.unsubscribe(subscriber_id='ui_plugin_unloaded')

        if hasattr(self, '_plugin_error_handler') and self._plugin_error_handler:
            self._plugin_error_handler.cleanup()

        # Clean up task monitor
        if hasattr(self, 'task_monitor'):
            self.task_monitor.cleanup()

        if self._app_core:
            self._app_core.shutdown()

        event.accept()