from __future__ import annotations

import os
import sys
import time
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QStackedWidget,
    QVBoxLayout, QWidget
)


class SidebarButton(QPushButton):
    """Custom button for the navigation sidebar."""

    def __init__(
            self,
            icon: QIcon,
            text: str,
            parent: Optional[QWidget] = None,
            checkable: bool = True
    ) -> None:
        """Initialize the sidebar button.

        Args:
            icon: The button icon
            text: The button text
            parent: The parent widget
            checkable: Whether the button is checkable
        """
        super().__init__(parent)
        self.text = text
        self.setText(self.text)
        self.setIcon(icon)
        self.setIconSize(QSize(24, 24))
        self.setCheckable(checkable)
        self.setFlat(True)

        # Set fixed height but flexible width
        self.setMinimumHeight(48)
        self.setMaximumHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Set style
        self.setStyleSheet("""
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
        """)


class Sidebar(QFrame):
    """Navigation sidebar with collapsible buttons."""

    # Signal emitted when the current page changes
    pageChangeRequested = Signal(int)  # page_index

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the sidebar.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        # Set fixed width
        self.setMinimumWidth(200)
        self.setMaximumWidth(200)

        # Track whether the sidebar is collapsed
        self._collapsed = False
        self._buttons: List[SidebarButton] = []
        self._button_group: Dict[str, List[SidebarButton]] = {}

        # Set up UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        # Main layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Header with logo
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # Logo
        logo_label = QLabel("Qorzen")
        logo_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(logo_label)

        # Collapse button
        self.collapse_button = QPushButton()
        self.collapse_button.setIcon(QIcon.fromTheme("go-previous"))
        self.collapse_button.setIconSize(QSize(16, 16))
        self.collapse_button.setFlat(True)
        self.collapse_button.setFixedSize(24, 24)
        self.collapse_button.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.collapse_button)

        self._layout.addWidget(header)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self._layout.addWidget(separator)

        # Container for buttons
        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 10, 0, 10)
        self.buttons_layout.setSpacing(2)

        # Add stretch to push buttons to the top
        self.buttons_layout.addStretch()

        self._layout.addWidget(self.buttons_container)

    def add_button(
            self,
            icon: QIcon,
            text: str,
            page_index: int,
            group: Optional[str] = None,
            checkable: bool = True
    ) -> SidebarButton:
        """Add a button to the sidebar.

        Args:
            icon: The button icon
            text: The button text
            page_index: The index of the page to show when clicked
            group: Optional group name for the button
            checkable: Whether the button is checkable

        Returns:
            The created button
        """
        button = SidebarButton(icon, text, self, checkable)
        button.clicked.connect(lambda checked, idx=page_index: self._on_button_clicked(idx))

        # Add to layout (before the stretch)
        self.buttons_layout.insertWidget(self.buttons_layout.count() - 1, button)

        # Store reference
        self._buttons.append(button)

        # Add to group if specified
        if group:
            if group not in self._button_group:
                self._button_group[group] = []
            self._button_group[group].append(button)

        return button

    def add_separator(self) -> None:
        """Add a separator line to the sidebar."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Add to layout (before the stretch)
        self.buttons_layout.insertWidget(self.buttons_layout.count() - 1, separator)

    def _on_button_clicked(self, page_index: int) -> None:
        """Handle button clicks.

        Args:
            page_index: The index of the page to show
        """
        # Uncheck all buttons
        for button in self._buttons:
            if button.isCheckable():
                button.setChecked(False)

        # Check the clicked button
        sender = self.sender()
        if sender and isinstance(sender, SidebarButton) and sender.isCheckable():
            sender.setChecked(True)

        # Emit signal to change page
        self.pageChangeRequested.emit(page_index)

    def _toggle_collapse(self) -> None:
        """Toggle the collapsed state of the sidebar."""
        self._collapsed = not self._collapsed

        if self._collapsed:
            # Collapse
            self.setMinimumWidth(48)
            self.setMaximumWidth(48)
            self.collapse_button.setIcon(QIcon.fromTheme("go-next"))

            # Hide text on buttons
            for button in self._buttons:
                button.setText("")
                button.setToolTip(button.text)
        else:
            # Expand
            self.setMinimumWidth(200)
            self.setMaximumWidth(200)
            self.collapse_button.setIcon(QIcon.fromTheme("go-previous"))

            # Show text on buttons
            for button in self._buttons:
                button.setText(button.text)

    def select_page(self, page_index: int) -> None:
        """Select a page by index.

        Args:
            page_index: The index of the page to select
        """
        # Find and check the button for the given page
        for button in self._buttons:
            if button.isCheckable():
                button.setChecked(False)

        # Find the button for this page
        for i, button in enumerate(self._buttons):
            if i == page_index and button.isCheckable():
                button.setChecked(True)
                break


class ContentArea(QStackedWidget):
    """Stacked widget for displaying content pages."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the content area.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        # Set style
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)

    def add_page(self, widget: QWidget, name: str) -> int:
        """Add a page to the content area.

        Args:
            widget: The widget to add
            name: The name of the page

        Returns:
            The index of the added page
        """
        # Add the widget to the stacked widget
        index = self.addWidget(widget)

        # Set object name for later reference
        widget.setObjectName(name)

        return index

    def get_page_by_name(self, name: str) -> Optional[QWidget]:
        """Get a page by name.

        Args:
            name: The name of the page

        Returns:
            The page widget, or None if not found
        """
        # Search for a widget with the given name
        for i in range(self.count()):
            widget = self.widget(i)
            if widget and widget.objectName() == name:
                return widget

        return None


class PanelLayout(QWidget):
    """Main panel-based layout with sidebar and content area."""

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            app_core: Optional[Any] = None
    ) -> None:
        """Initialize the panel layout.

        Args:
            parent: The parent widget
            app_core: The application core
        """
        super().__init__(parent)

        self._app_core = app_core
        self._pages: Dict[str, QWidget] = {}
        self._page_names: List[str] = []

        # Setup UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        self.sidebar = Sidebar(self)

        # Create content area
        self.content_area = ContentArea(self)

        # Add widgets to layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area, 1)  # Give content area more stretch

        # Connect sidebar signals
        self.sidebar.pageChangeRequested.connect(self.content_area.setCurrentIndex)

    def add_page(
            self,
            widget: QWidget,
            name: str,
            icon: QIcon,
            text: str,
            group: Optional[str] = None
    ) -> int:
        """Add a page to the layout.

        Args:
            widget: The widget to add
            name: The name of the page
            icon: The icon for the sidebar button
            text: The text for the sidebar button
            group: Optional group name for the button

        Returns:
            The index of the added page
        """
        # Add page to content area
        index = self.content_area.add_page(widget, name)

        # Add button to sidebar
        self.sidebar.add_button(icon, text, index, group)

        # Store reference
        self._pages[name] = widget
        self._page_names.append(name)

        return index

    def add_separator(self) -> None:
        """Add a separator to the sidebar."""
        self.sidebar.add_separator()

    def select_page(self, page_name: str) -> None:
        """Select a page by name.

        Args:
            page_name: The name of the page to select
        """
        for i, name in enumerate(self._page_names):
            if name == page_name:
                self.sidebar.select_page(i)
                self.content_area.setCurrentIndex(i)
                break


class MainWindow(QMainWindow):
    """Main application window with panel-based layout."""

    def __init__(self, app_core: Any) -> None:
        """Initialize the main window.

        Args:
            app_core: The application core
        """
        super().__init__()

        self._app_core = app_core
        self._config_manager = app_core.get_manager('config')
        self._logging_manager = app_core.get_manager('logging')
        self._event_bus = app_core.get_manager('event_bus')
        self._plugin_manager = app_core.get_manager('plugin_manager')
        self._monitoring_manager = app_core.get_manager('monitoring')

        if self._logging_manager:
            self._logger = self._logging_manager.get_logger('ui')
        else:
            import logging
            self._logger = logging.getLogger('ui')

        # Set up the UI
        self._setup_ui()

        # Subscribe to events
        self._subscribe_to_events()

        # Initialize plugin error handler
        from ..core.plugin_error_handler import PluginErrorHandler
        self._plugin_error_handler = PluginErrorHandler(
            self._event_bus,
            self._plugin_manager,
            self
        )

        # Start update timer
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start(5000)  # Update every 5 seconds

        self._logger.info('Qorzen UI started')

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Set window properties
        self.setWindowTitle('Qorzen')
        self.setMinimumSize(1024, 768)

        # Create panel layout
        self.panel_layout = PanelLayout(self, self._app_core)
        self.setCentralWidget(self.panel_layout)

        # Create standard system pages
        self._create_dashboard_page()
        self._create_plugins_page()
        self._create_logs_page()

        # Add separator for plugin pages
        self.panel_layout.add_separator()

        # Create status bar
        self.statusBar().showMessage('Ready')

    def _create_dashboard_page(self) -> None:
        """Create the dashboard page."""
        # Import dashboard widget
        from qorzen.ui.dashboard import DashboardWidget

        # Create dashboard
        dashboard = DashboardWidget(self._app_core, self)

        # Add to panel layout
        self.panel_layout.add_page(
            dashboard,
            'dashboard',
            QIcon(":/ui_icons/dashboard.svg"),
            'Dashboard',
            'system'
        )

    def _create_plugins_page(self) -> None:
        """Create the plugins page."""
        # Import plugins view
        from qorzen.ui.plugins import PluginsView

        # Create plugins view
        plugins_view = PluginsView(self._plugin_manager, self)

        # Connect signals
        plugins_view.pluginStateChangeRequested.connect(self._on_plugin_state_change)
        plugins_view.pluginReloadRequested.connect(self._on_plugin_reload)
        plugins_view.pluginInfoRequested.connect(self._on_plugin_info)

        # Add to panel layout
        self.panel_layout.add_page(
            plugins_view,
            'plugins',
            QIcon(":/ui_icons/extension.svg"),
            'Plugins',
            'system'
        )

    def _create_logs_page(self) -> None:
        """Create the logs page."""
        # Import logs view
        from qorzen.ui.logs import LogsView

        # Create logs view
        logs_view = LogsView(self._event_bus, self)

        # Add to panel layout
        self.panel_layout.add_page(
            logs_view,
            'logs',
            QIcon(":/ui_icons/library-books.svg"),
            'Logs',
            'system'
        )

    def _subscribe_to_events(self) -> None:
        """Subscribe to events from the event bus."""
        if not self._event_bus:
            return

        # Subscribe to plugin loaded/unloaded events
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
        """Update status information."""
        # Update status bar
        self.statusBar().showMessage(f'Ready - Last update: {time.strftime("%H:%M:%S")}')

    def _on_plugin_state_change(self, plugin_name: str, enable: bool) -> None:
        """Handle plugin state change requests.

        Args:
            plugin_name: The name of the plugin
            enable: Whether to enable or disable the plugin
        """
        if not self._plugin_manager:
            return

        try:
            if enable:
                # Try to enable and load the plugin
                success = self._plugin_manager.enable_plugin(plugin_name)
                if success:
                    self._plugin_manager.load_plugin(plugin_name)
            else:
                # Try to disable and unload the plugin
                if self._plugin_manager.unload_plugin(plugin_name):
                    self._plugin_manager.disable_plugin(plugin_name)
        except Exception as e:
            self._logger.error(
                f"Error changing plugin state: {str(e)}",
                extra={"plugin_name": plugin_name, "enable": enable}
            )

    def _on_plugin_reload(self, plugin_name: str) -> None:
        """Handle plugin reload requests.

        Args:
            plugin_name: The name of the plugin
        """
        if not self._plugin_manager:
            return

        try:
            # Try to reload the plugin
            success = self._plugin_manager.reload_plugin(plugin_name)

            if success:
                self._logger.info(f"Successfully reloaded plugin: {plugin_name}")
            else:
                self._logger.warning(f"Failed to reload plugin: {plugin_name}")
        except Exception as e:
            self._logger.error(
                f"Error reloading plugin: {str(e)}",
                extra={"plugin_name": plugin_name}
            )

    def _on_plugin_info(self, plugin_name: str) -> None:
        """Handle plugin info requests.

        Args:
            plugin_name: The name of the plugin
        """
        # Show plugin details dialog
        pass

    def _on_plugin_loaded_event(self, event: Any) -> None:
        """Handle plugin loaded events.

        Args:
            event: The event
        """
        from qorzen.core.plugin_manager import PluginInfo

        # Get plugin information
        payload = event.payload
        plugin_name = payload.get('plugin_name', '')

        if not plugin_name:
            return

        # Get plugin instance
        if not self._plugin_manager:
            return

        plugins = self._plugin_manager.get_all_plugins()
        plugin_info: PluginInfo = plugins.get(plugin_name)

        if not plugin_info:
            return

        # Check if plugin has UI components
        instance = plugin_info.metadata.get('instance')

        if not instance:
            return

        # Add plugin UI components to the panel layout
        self._add_plugin_ui_components(plugin_name, instance)

    def _on_plugin_unloaded_event(self, event: Any) -> None:
        """Handle plugin unloaded events.

        Args:
            event: The event
        """
        # Get plugin information
        payload = event.payload
        plugin_name = payload.get('plugin_name', '')

        if not plugin_name:
            return

        # Remove plugin UI components
        self._remove_plugin_ui_components(plugin_name)

    def _add_plugin_ui_components(self, plugin_name: str, instance: Any) -> None:
        """Add plugin UI components to the panel layout.

        Args:
            plugin_name: The name of the plugin
            instance: The plugin instance
        """
        # Check if the plugin has a get_main_widget method
        if not hasattr(instance, 'get_main_widget'):
            return

        try:
            # Get the main widget from the plugin
            widget = instance.get_main_widget()

            if not widget:
                return

            # Get plugin metadata
            icon = QIcon()
            if hasattr(instance, 'get_icon') and callable(instance.get_icon):
                icon_path = instance.get_icon()
                if icon_path and os.path.exists(icon_path):
                    icon = QIcon(icon_path)

            # Get display name
            display_name = plugin_name
            if hasattr(instance, 'display_name'):
                display_name = instance.display_name

            # Add to panel layout
            self.panel_layout.add_page(
                widget,
                f"plugin_{plugin_name}",
                icon,
                display_name,
                'plugins'
            )

            self._logger.info(f"Added UI components for plugin: {plugin_name}")

        except Exception as e:
            self._logger.error(
                f"Error adding UI components for plugin {plugin_name}: {str(e)}",
                extra={"plugin_name": plugin_name}
            )

    def _remove_plugin_ui_components(self, plugin_name: str) -> None:
        """Remove plugin UI components from the panel layout.

        Args:
            plugin_name: The name of the plugin
        """
        # Find and remove the plugin page
        page_name = f"plugin_{plugin_name}"

        # First select a system page (dashboard)
        self.panel_layout.select_page('dashboard')

        # Then remove the plugin page
        page = self.panel_layout.content_area.get_page_by_name(page_name)

        if page:
            index = self.panel_layout.content_area.indexOf(page)
            if index >= 0:
                self.panel_layout.content_area.removeWidget(page)
                page.deleteLater()

                self._logger.info(f"Removed UI components for plugin: {plugin_name}")

    def closeEvent(self, event: Any) -> None:
        """Handle window close events.

        Args:
            event: The event
        """
        # Stop update timer
        self._update_timer.stop()

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(subscriber_id='ui_plugin_loaded')
            self._event_bus.unsubscribe(subscriber_id='ui_plugin_unloaded')

        # Clean up plugin error handler
        if hasattr(self, '_plugin_error_handler') and self._plugin_error_handler:
            self._plugin_error_handler.cleanup()

        # Shut down app core
        if self._app_core:
            self._app_core.shutdown()

        # Accept the event
        event.accept()