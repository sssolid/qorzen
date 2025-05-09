from __future__ import annotations
import abc
import threading
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Set, TypeVar, Generic, Union, cast
from PySide6.QtWidgets import QWidget, QMenu, QToolBar, QDockWidget
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt


class UIComponent(Protocol):
    """Interface for UI components."""

    def get_widget(self) -> QWidget:
        ...


class MenuComponent(UIComponent):
    """Interface for menu components."""

    def get_actions(self) -> List[QAction]:
        ...


class ToolbarComponent(UIComponent):
    """Interface for toolbar components."""

    def get_actions(self) -> List[QAction]:
        ...


class DockComponent(UIComponent):
    """Interface for dock components."""

    def get_dock_widget(self) -> QWidget:
        ...


T = TypeVar('T')


class ComponentTracker(Generic[T]):
    """Thread-safe tracker for UI components."""

    def __init__(self) -> None:
        self._components: Dict[str, Dict[str, List[T]]] = {}
        self._lock = threading.RLock()

    def add(self, plugin_id: str, component_type: str, component: T) -> None:
        """Add a component to the tracker."""
        with self._lock:
            if plugin_id not in self._components:
                self._components[plugin_id] = {}
            if component_type not in self._components[plugin_id]:
                self._components[plugin_id][component_type] = []
            self._components[plugin_id][component_type].append(component)

    def get_all(self, plugin_id: str) -> Dict[str, List[T]]:
        """Get all components for a plugin."""
        with self._lock:
            return self._components.get(plugin_id, {}).copy()

    def get_by_type(self, plugin_id: str, component_type: str) -> List[T]:
        """Get components of a specific type for a plugin."""
        with self._lock:
            return self._components.get(plugin_id, {}).get(component_type, []).copy()

    def remove_all(self, plugin_id: str) -> None:
        """Remove all components for a plugin."""
        with self._lock:
            if plugin_id in self._components:
                del self._components[plugin_id]

    def has_plugin(self, plugin_id: str) -> bool:
        """Check if a plugin has any components."""
        with self._lock:
            return plugin_id in self._components


class UIIntegration(abc.ABC):
    """UI Integration interface for plugins to interact with the main UI."""

    @abc.abstractmethod
    def find_menu(self, menu_title: str) -> Optional[QMenu]:
        """Find a menu by title."""
        ...

    @abc.abstractmethod
    def add_menu(self, plugin_id: str, title: str, parent_menu: Optional[Union[str, QMenu]] = None) -> QMenu:
        """Add a menu to the menu bar or a parent menu."""
        ...

    @abc.abstractmethod
    def add_menu_action(self, plugin_id: str, menu: Union[str, QMenu], text: str, callback: Callable[[], None],
                        icon: Optional[QIcon] = None) -> QAction:
        """Add an action to a menu."""
        ...

    @abc.abstractmethod
    def add_toolbar(self, plugin_id: str, title: str) -> QToolBar:
        """Add a toolbar to the main window."""
        ...

    @abc.abstractmethod
    def add_toolbar_action(self, plugin_id: str, toolbar: QToolBar, text: str, callback: Callable[[], None],
                           icon: Optional[QIcon] = None) -> QAction:
        """Add an action to a toolbar."""
        ...

    @abc.abstractmethod
    def add_dock_widget(self, plugin_id: str, dock: Union[DockComponent, QWidget], title: str,
                        area: str = 'right') -> QDockWidget:
        """Add a dock widget to the main window."""
        ...

    @abc.abstractmethod
    def add_page(self, plugin_id: str, widget: QWidget, name: str, icon: QIcon, text: str,
                 group: Optional[str] = None) -> int:
        """Add a page to the panel layout."""
        ...

    @abc.abstractmethod
    def remove_page(self, plugin_id: str, name: str) -> None:
        """Remove a page from the panel layout."""
        ...

    @abc.abstractmethod
    def select_page(self, name: str) -> None:
        """Select a page in the panel layout."""
        ...

    @abc.abstractmethod
    def cleanup_plugin(self, plugin_id: str) -> None:
        """Clean up all UI components for a plugin."""
        ...


class MainWindowIntegration(UIIntegration):
    """Implementation of UIIntegration for the MainWindow."""

    def __init__(self, main_window: Any) -> None:
        self.main_window = main_window
        self._logger = getattr(main_window, '_logger', None)
        self._menu_components = ComponentTracker[QMenu]()
        self._action_components = ComponentTracker[Tuple[QAction, Optional[QMenu]]]()
        self._toolbar_components = ComponentTracker[QToolBar]()
        self._dock_components = ComponentTracker[QDockWidget]()
        self._page_components = ComponentTracker[Tuple[str, QWidget]]()
        self._menus: Dict[str, QMenu] = {}
        self._actions: Dict[str, List[QAction]] = {}
        self._lock = threading.RLock()

        if hasattr(main_window, '_menus') and isinstance(main_window._menus, dict):
            with self._lock:
                self._menus.update(main_window._menus)
        else:
            try:
                menu_bar = main_window.menuBar()
                for action in menu_bar.actions():
                    menu = action.menu()
                    if menu:
                        with self._lock:
                            self._menus[action.text()] = menu
            except Exception as e:
                if self._logger:
                    self._logger.warning(f'Failed to copy menus from main window: {str(e)}')

    def find_menu(self, menu_title: str) -> Optional[QMenu]:
        """Find a menu by title."""
        with self._lock:
            if menu_title in self._menus:
                return self._menus[menu_title]

        if hasattr(self.main_window, 'get_menu') and callable(self.main_window.get_menu):
            menu = self.main_window.get_menu(menu_title)
            if menu:
                with self._lock:
                    self._menus[menu_title] = menu
                return menu

        try:
            menu_bar = self.main_window.menuBar()
            for action in menu_bar.actions():
                if action.text() == menu_title:
                    menu = action.menu()
                    if menu:
                        with self._lock:
                            self._menus[menu_title] = menu
                        return menu
        except Exception as e:
            if self._logger:
                self._logger.warning(f"Error finding menu '{menu_title}': {str(e)}")

        return None

    def add_menu(self, plugin_id: str, title: str, parent_menu: Optional[Union[str, QMenu]] = None) -> QMenu:
        """Add a menu to the menu bar or a parent menu."""
        with self._lock:
            for menu in self._menu_components.get_by_type(plugin_id, 'menus'):
                if menu.title() == title:
                    return menu

        menu_bar = self.main_window.menuBar()
        parent = None
        if parent_menu:
            if isinstance(parent_menu, str):
                parent = self.find_menu(parent_menu)
                if not parent:
                    if self._logger:
                        self._logger.warning(f"Parent menu '{parent_menu}' not found, creating at top level")
            else:
                parent = parent_menu

        menu = QMenu(title, self.main_window)
        if parent:
            parent.addMenu(menu)
        else:
            menu_bar.addMenu(menu)

        with self._lock:
            self._menu_components.add(plugin_id, 'menus', menu)
            self._menus[title] = menu

        if self._logger:
            parent_name = parent.title() if parent else 'menu bar'
            self._logger.debug(f"Added menu '{title}' for plugin '{plugin_id}' to {parent_name}")

        return menu

    def add_menu_action(self, plugin_id: str, menu: Union[str, QMenu], text: str, callback: Callable[[], None],
                        icon: Optional[QIcon] = None) -> QAction:
        """Add an action to a menu."""
        target_menu = None
        if isinstance(menu, str):
            target_menu = self.find_menu(menu)
            if not target_menu:
                if self._logger:
                    self._logger.warning(f"Menu '{menu}' not found, creating it")
                target_menu = self.add_menu(plugin_id, menu)
        else:
            target_menu = menu

        with self._lock:
            for action, parent_menu in self._action_components.get_by_type(plugin_id, 'actions'):
                if action.text() == text and parent_menu == target_menu:
                    return action

        action = QAction(text, self.main_window)
        if icon:
            action.setIcon(icon)
        action.triggered.connect(callback)
        target_menu.addAction(action)

        with self._lock:
            self._action_components.add(plugin_id, 'actions', (action, target_menu))
            if plugin_id not in self._actions:
                self._actions[plugin_id] = []
            self._actions[plugin_id].append(action)

        if self._logger:
            menu_name = target_menu.title() if target_menu else 'unknown menu'
            self._logger.debug(f"Added action '{text}' for plugin '{plugin_id}' to menu '{menu_name}'")

        return action

    def add_toolbar(self, plugin_id: str, title: str) -> QToolBar:
        """Add a toolbar to the main window."""
        toolbar = self.main_window.addToolBar(title)

        with self._lock:
            self._toolbar_components.add(plugin_id, 'toolbars', toolbar)
            if hasattr(self.main_window, '_toolbars') and isinstance(self.main_window._toolbars, dict):
                self.main_window._toolbars[title] = toolbar

        if self._logger:
            self._logger.debug(f"Added toolbar '{title}' for plugin '{plugin_id}'")

        return toolbar

    def add_toolbar_action(self, plugin_id: str, toolbar: QToolBar, text: str, callback: Callable[[], None],
                           icon: Optional[QIcon] = None) -> QAction:
        """Add an action to a toolbar."""
        action = QAction(text, self.main_window)
        if icon:
            action.setIcon(icon)
        action.triggered.connect(callback)
        toolbar.addAction(action)

        with self._lock:
            self._action_components.add(plugin_id, 'actions', (action, None))
            if plugin_id not in self._actions:
                self._actions[plugin_id] = []
            self._actions[plugin_id].append(action)

        if self._logger:
            self._logger.debug(f"Added toolbar action '{text}' for plugin '{plugin_id}'")

        return action

    def add_dock_widget(self, plugin_id: str, dock: Union[DockComponent, QWidget], title: str,
                        area: str = 'right') -> QDockWidget:
        """Add a dock widget to the main window."""
        if isinstance(dock, QWidget):
            widget = dock
        else:
            widget = dock.get_dock_widget()

        dock_widget = QDockWidget(title, self.main_window)
        dock_widget.setWidget(widget)

        area_map = {
            'left': Qt.LeftDockWidgetArea,
            'right': Qt.RightDockWidgetArea,
            'top': Qt.TopDockWidgetArea,
            'bottom': Qt.BottomDockWidgetArea
        }
        dock_area = area_map.get(area.lower(), Qt.RightDockWidgetArea)
        self.main_window.addDockWidget(dock_area, dock_widget)

        with self._lock:
            self._dock_components.add(plugin_id, 'docks', dock_widget)

        if self._logger:
            self._logger.debug(f"Added dock widget '{title}' for plugin '{plugin_id}' in area '{area}'")

        return dock_widget

    def add_page(self, plugin_id: str, widget: QWidget, name: str, icon: QIcon, text: str,
                 group: Optional[str] = None) -> int:
        """Add a page to the panel layout."""
        # Check if panel_layout exists
        if not hasattr(self.main_window, 'panel_layout'):
            if self._logger:
                self._logger.error(f"Cannot add page '{name}': main window has no panel_layout")
            return -1

        # Add page to panel layout
        page_index = self.main_window.panel_layout.add_page(widget, name, icon, text, group)

        with self._lock:
            self._page_components.add(plugin_id, 'pages', (name, widget))

        if self._logger:
            self._logger.debug(f"Added page '{name}' for plugin '{plugin_id}'")

        return page_index

    def remove_page(self, plugin_id: str, name: str) -> None:
        """Remove a page from the panel layout."""
        if not hasattr(self.main_window, 'panel_layout'):
            return

        self.main_window.panel_layout.select_page('dashboard')  # Switch to dashboard first

        page = self.main_window.panel_layout.content_area.get_page_by_name(name)
        if page:
            index = self.main_window.panel_layout.content_area.indexOf(page)
            if index >= 0:
                self.main_window.panel_layout.content_area.removeWidget(page)
                page.deleteLater()

                if self._logger:
                    self._logger.debug(f"Removed page '{name}' for plugin '{plugin_id}'")

    def select_page(self, name: str) -> None:
        """Select a page in the panel layout."""
        if hasattr(self.main_window, 'panel_layout'):
            self.main_window.panel_layout.select_page(name)

    def cleanup_plugin(self, plugin_id: str) -> None:
        """Clean up all UI components for a plugin."""
        if self._logger:
            self._logger.debug(f"Cleaning up UI components for plugin '{plugin_id}'")

        # Clean up pages
        with self._lock:
            page_components = self._page_components.get_by_type(plugin_id, 'pages')

        for name, widget in page_components:
            try:
                self.remove_page(plugin_id, name)
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing page '{name}' for plugin '{plugin_id}': {str(e)}")

        # Clean up actions
        with self._lock:
            action_components = self._action_components.get_by_type(plugin_id, 'actions')

        for action, parent_menu in action_components:
            try:
                if parent_menu:
                    parent_menu.removeAction(action)
                action.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing action for plugin '{plugin_id}': {str(e)}")

        # Clean up menus
        with self._lock:
            menu_components = self._menu_components.get_by_type(plugin_id, 'menus')

        for menu in menu_components:
            try:
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
        with self._lock:
            toolbar_components = self._toolbar_components.get_by_type(plugin_id, 'toolbars')

        for toolbar in toolbar_components:
            try:
                self.main_window.removeToolBar(toolbar)
                toolbar.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing toolbar for plugin '{plugin_id}': {str(e)}")

        # Clean up dock widgets
        with self._lock:
            dock_components = self._dock_components.get_by_type(plugin_id, 'docks')

        for dock_widget in dock_components:
            try:
                self.main_window.removeDockWidget(dock_widget)
                dock_widget.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error removing dock widget for plugin '{plugin_id}': {str(e)}")

        # Clean up tracking data
        with self._lock:
            self._page_components.remove_all(plugin_id)
            self._menu_components.remove_all(plugin_id)
            self._action_components.remove_all(plugin_id)
            self._toolbar_components.remove_all(plugin_id)
            self._dock_components.remove_all(plugin_id)
            if plugin_id in self._actions:
                del self._actions[plugin_id]

        if self._logger:
            self._logger.info(f"UI cleanup complete for plugin '{plugin_id}'")