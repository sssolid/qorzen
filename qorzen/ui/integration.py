from __future__ import annotations
import abc
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Set, TypeVar, Generic, Union, cast
from PySide6.QtWidgets import QWidget, QMenu, QToolBar, QDockWidget
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt


class UIComponent(Protocol):
    """Interface for UI components."""

    def get_widget(self) -> QWidget:
        """Get the underlying widget."""
        ...


class TabComponent(UIComponent):
    """Interface for tab components."""

    def on_tab_selected(self) -> None:
        """Called when tab is selected."""
        ...

    def on_tab_deselected(self) -> None:
        """Called when tab is deselected."""
        ...


class MenuComponent(UIComponent):
    """Interface for menu components."""

    def get_actions(self) -> List[QAction]:
        """Get menu actions."""
        ...


class ToolbarComponent(UIComponent):
    """Interface for toolbar components."""

    def get_actions(self) -> List[QAction]:
        """Get toolbar actions."""
        ...


class DockComponent(UIComponent):
    """Interface for dock components."""

    def get_dock_widget(self) -> QWidget:
        """Get dock widget."""
        ...


T = TypeVar('T')


class ComponentTracker(Generic[T]):
    """Tracks components owned by plugins."""

    def __init__(self) -> None:
        self._components: Dict[str, Dict[str, List[T]]] = {}

    def add(self, plugin_id: str, component_type: str, component: T) -> None:
        """Track a component for a plugin."""
        if plugin_id not in self._components:
            self._components[plugin_id] = {}

        if component_type not in self._components[plugin_id]:
            self._components[plugin_id][component_type] = []

        self._components[plugin_id][component_type].append(component)

    def get_all(self, plugin_id: str) -> Dict[str, List[T]]:
        """Get all components for a plugin."""
        return self._components.get(plugin_id, {})

    def get_by_type(self, plugin_id: str, component_type: str) -> List[T]:
        """Get components of a specific type for a plugin."""
        return self._components.get(plugin_id, {}).get(component_type, [])

    def remove_all(self, plugin_id: str) -> None:
        """Remove all components for a plugin."""
        if plugin_id in self._components:
            del self._components[plugin_id]

    def has_plugin(self, plugin_id: str) -> bool:
        """Check if plugin has any components."""
        return plugin_id in self._components


class UIIntegration(abc.ABC):
    """Interface for UI integration."""

    @abc.abstractmethod
    def add_tab(self, plugin_id: str, tab: Union[TabComponent, QWidget], title: str,
                icon: Optional[QIcon] = None) -> int:
        """Add a tab to the main window."""
        ...

    @abc.abstractmethod
    def remove_tab(self, tab_index: int) -> None:
        """Remove a tab from the main window."""
        ...

    @abc.abstractmethod
    def find_menu(self, menu_title: str) -> Optional[QMenu]:
        """Find a menu by title."""
        ...

    @abc.abstractmethod
    def add_menu(self, plugin_id: str, title: str, parent_menu: Optional[Union[str, QMenu]] = None) -> QMenu:
        """Add a menu to the main window."""
        ...

    @abc.abstractmethod
    def add_menu_action(self, plugin_id: str, menu: Union[str, QMenu], text: str,
                        callback: Callable[[], None], icon: Optional[QIcon] = None) -> QAction:
        """Add an action to a menu."""
        ...

    @abc.abstractmethod
    def add_toolbar(self, plugin_id: str, title: str) -> QToolBar:
        """Add a toolbar to the main window."""
        ...

    @abc.abstractmethod
    def add_toolbar_action(self, plugin_id: str, toolbar: QToolBar, text: str,
                           callback: Callable[[], None], icon: Optional[QIcon] = None) -> QAction:
        """Add an action to a toolbar."""
        ...

    @abc.abstractmethod
    def add_dock_widget(self, plugin_id: str, dock: Union[DockComponent, QWidget], title: str,
                        area: str = "right") -> QDockWidget:
        """Add a dock widget to the main window."""
        ...

    @abc.abstractmethod
    def cleanup_plugin(self, plugin_id: str) -> None:
        """Remove all UI components for a plugin."""
        ...


class MainWindowIntegration(UIIntegration):
    """UI integration for the main Qorzen window."""

    def __init__(self, main_window: Any) -> None:
        """Initialize with main window instance."""
        self.main_window = main_window
        self._logger = getattr(main_window, '_logger', None)

        # Component trackers
        self._tab_components = ComponentTracker[Tuple[int, Union[TabComponent, QWidget]]]()
        self._menu_components = ComponentTracker[QMenu]()
        self._action_components = ComponentTracker[Tuple[QAction, Optional[QMenu]]]()
        self._toolbar_components = ComponentTracker[QToolBar]()
        self._dock_components = ComponentTracker[QDockWidget]()

    def add_tab(self, plugin_id: str, tab: Union[TabComponent, QWidget], title: str,
                icon: Optional[QIcon] = None) -> int:
        """Add a tab to the main window."""
        central_tabs = self.main_window._central_tabs
        if not central_tabs:
            raise ValueError("Central tabs widget not found in main window")

        # Get the widget to add - more robustly
        if hasattr(tab, 'get_widget') and callable(tab.get_widget):
            widget = tab.get_widget()
        else:
            widget = tab

        # Add the tab to the UI
        tab_index = central_tabs.addTab(widget, title)
        if icon:
            central_tabs.setTabIcon(tab_index, icon)

        # Track the component
        self._tab_components.add(plugin_id, "tabs", (tab_index, tab))

        if self._logger:
            self._logger.debug(f"Added tab '{title}' for plugin '{plugin_id}' at index {tab_index}")

        return tab_index

    def remove_tab(self, tab_index: int) -> None:
        """Remove a tab from the main window."""
        central_tabs = self.main_window._central_tabs
        if not central_tabs:
            return

        central_tabs.removeTab(tab_index)

        if self._logger:
            self._logger.debug(f"Removed tab at index {tab_index}")

    def find_menu(self, menu_title: str) -> Optional[QMenu]:
        """Find a menu by title."""
        menu_bar = self.main_window.menuBar()

        for action in menu_bar.actions():
            if action.text() == menu_title:
                return action.menu()

        return None

    def add_menu(self, plugin_id: str, title: str, parent_menu: Optional[Union[str, QMenu]] = None) -> QMenu:
        """Add a menu to the main window."""
        menu_bar = self.main_window.menuBar()

        # Handle parent menu
        parent = None
        if parent_menu:
            if isinstance(parent_menu, str):
                parent = self.find_menu(parent_menu)
                if not parent:
                    raise ValueError(f"Parent menu '{parent_menu}' not found")
            else:
                parent = parent_menu

        # Create the menu
        menu = QMenu(title, self.main_window)

        # Add the menu to the parent or menu bar
        if parent:
            parent.addMenu(menu)
        else:
            menu_bar.addMenu(menu)

        # Track the component
        self._menu_components.add(plugin_id, "menus", menu)

        if self._logger:
            parent_name = parent.title() if parent else "menu bar"
            self._logger.debug(f"Added menu '{title}' for plugin '{plugin_id}' to {parent_name}")

        return menu

    def add_menu_action(self, plugin_id: str, menu: Union[str, QMenu], text: str,
                        callback: Callable[[], None], icon: Optional[QIcon] = None) -> QAction:
        """Add an action to a menu."""
        # Get the menu to add the action to
        target_menu = None
        if isinstance(menu, str):
            target_menu = self.find_menu(menu)
            if not target_menu:
                raise ValueError(f"Menu '{menu}' not found")
        else:
            target_menu = menu

        # Create the action
        action = QAction(text, self.main_window)
        if icon:
            action.setIcon(icon)

        # Connect the callback
        action.triggered.connect(callback)

        # Add the action to the menu
        target_menu.addAction(action)

        # Track the component
        self._action_components.add(plugin_id, "actions", (action, target_menu))

        if self._logger:
            menu_name = target_menu.title() if target_menu else "unknown menu"
            self._logger.debug(f"Added action '{text}' for plugin '{plugin_id}' to menu '{menu_name}'")

        return action

    def add_toolbar(self, plugin_id: str, title: str) -> QToolBar:
        """Add a toolbar to the main window."""
        toolbar = self.main_window.addToolBar(title)

        # Track the component
        self._toolbar_components.add(plugin_id, "toolbars", toolbar)

        if self._logger:
            self._logger.debug(f"Added toolbar '{title}' for plugin '{plugin_id}'")

        return toolbar

    def add_toolbar_action(self, plugin_id: str, toolbar: QToolBar, text: str,
                           callback: Callable[[], None], icon: Optional[QIcon] = None) -> QAction:
        """Add an action to a toolbar."""
        # Create the action
        action = QAction(text, self.main_window)
        if icon:
            action.setIcon(icon)

        # Connect the callback
        action.triggered.connect(callback)

        # Add the action to the toolbar
        toolbar.addAction(action)

        # Track the component
        self._action_components.add(plugin_id, "actions", (action, None))

        if self._logger:
            self._logger.debug(f"Added toolbar action '{text}' for plugin '{plugin_id}'")

        return action

    def add_dock_widget(self, plugin_id: str, dock: Union[DockComponent, QWidget], title: str,
                        area: str = "right") -> QDockWidget:
        """Add a dock widget to the main window."""
        # Get the widget to add
        if isinstance(dock, QWidget):
            widget = dock
        else:
            widget = dock.get_dock_widget()

        # Create the dock widget
        dock_widget = QDockWidget(title, self.main_window)
        dock_widget.setWidget(widget)

        # Map the area string to Qt dock area
        area_map = {
            "left": Qt.LeftDockWidgetArea,
            "right": Qt.RightDockWidgetArea,
            "top": Qt.TopDockWidgetArea,
            "bottom": Qt.BottomDockWidgetArea
        }

        dock_area = area_map.get(area.lower(), Qt.RightDockWidgetArea)

        # Add the dock widget to the main window
        self.main_window.addDockWidget(dock_area, dock_widget)

        # Track the component
        self._dock_components.add(plugin_id, "docks", dock_widget)

        if self._logger:
            self._logger.debug(f"Added dock widget '{title}' for plugin '{plugin_id}' in area '{area}'")

        return dock_widget

    def cleanup_plugin(self, plugin_id: str) -> None:
        """Remove all UI components for a plugin."""
        if self._logger:
            self._logger.debug(f"Cleaning up UI components for plugin '{plugin_id}'")

        # Clean up tabs
        for tab_index, tab in self._tab_components.get_by_type(plugin_id, "tabs"):
            try:
                self.remove_tab(tab_index)
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing tab for plugin '{plugin_id}': {str(e)}")

        # Clean up actions
        for action, parent_menu in self._action_components.get_by_type(plugin_id, "actions"):
            try:
                if parent_menu:
                    parent_menu.removeAction(action)
                action.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing action for plugin '{plugin_id}': {str(e)}")

        # Clean up menus
        for menu in self._menu_components.get_by_type(plugin_id, "menus"):
            try:
                # Remove from parent menu or menu bar
                parent = menu.parentWidget()
                if isinstance(parent, QMenu):
                    parent.removeAction(menu.menuAction())
                else:
                    menu_bar = self.main_window.menuBar()
                    menu_bar.removeAction(menu.menuAction())
                menu.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing menu for plugin '{plugin_id}': {str(e)}")

        # Clean up toolbars
        for toolbar in self._toolbar_components.get_by_type(plugin_id, "toolbars"):
            try:
                self.main_window.removeToolBar(toolbar)
                toolbar.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing toolbar for plugin '{plugin_id}': {str(e)}")

        # Clean up dock widgets
        for dock_widget in self._dock_components.get_by_type(plugin_id, "docks"):
            try:
                self.main_window.removeDockWidget(dock_widget)
                dock_widget.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing dock widget for plugin '{plugin_id}': {str(e)}")

        # Clear component trackers
        self._tab_components.remove_all(plugin_id)
        self._menu_components.remove_all(plugin_id)
        self._action_components.remove_all(plugin_id)
        self._toolbar_components.remove_all(plugin_id)
        self._dock_components.remove_all(plugin_id)

        if self._logger:
            self._logger.info(f"UI cleanup complete for plugin '{plugin_id}'")