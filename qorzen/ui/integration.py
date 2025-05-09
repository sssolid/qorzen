from __future__ import annotations

import abc
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Set, TypeVar, Generic, Union, cast

from PySide6.QtWidgets import QWidget, QMenu, QToolBar, QDockWidget
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt


class UIComponent(Protocol):
    """Interface for UI components."""

    def get_widget(self) -> QWidget:
        """Get the widget for this component.

        Returns:
            The widget for this component.
        """
        ...


class TabComponent(UIComponent):
    """Interface for tab components."""

    def on_tab_selected(self) -> None:
        """Called when this tab is selected."""
        ...

    def on_tab_deselected(self) -> None:
        """Called when this tab is deselected."""
        ...


class MenuComponent(UIComponent):
    """Interface for menu components."""

    def get_actions(self) -> List[QAction]:
        """Get actions for this menu component.

        Returns:
            The list of actions.
        """
        ...


class ToolbarComponent(UIComponent):
    """Interface for toolbar components."""

    def get_actions(self) -> List[QAction]:
        """Get actions for this toolbar component.

        Returns:
            The list of actions.
        """
        ...


class DockComponent(UIComponent):
    """Interface for dock components."""

    def get_dock_widget(self) -> QWidget:
        """Get the dock widget for this component.

        Returns:
            The dock widget.
        """
        ...


T = TypeVar('T')


class ComponentTracker(Generic[T]):
    """Tracks components by plugin ID and component type."""

    def __init__(self) -> None:
        """Initialize the component tracker."""
        self._components: Dict[str, Dict[str, List[T]]] = {}

    def add(self, plugin_id: str, component_type: str, component: T) -> None:
        """Add a component.

        Args:
            plugin_id: The plugin ID.
            component_type: The component type.
            component: The component.
        """
        if plugin_id not in self._components:
            self._components[plugin_id] = {}

        if component_type not in self._components[plugin_id]:
            self._components[plugin_id][component_type] = []

        self._components[plugin_id][component_type].append(component)

    def get_all(self, plugin_id: str) -> Dict[str, List[T]]:
        """Get all components for a plugin.

        Args:
            plugin_id: The plugin ID.

        Returns:
            A dictionary of component types to lists of components.
        """
        return self._components.get(plugin_id, {})

    def get_by_type(self, plugin_id: str, component_type: str) -> List[T]:
        """Get components of a specific type for a plugin.

        Args:
            plugin_id: The plugin ID.
            component_type: The component type.

        Returns:
            A list of components.
        """
        return self._components.get(plugin_id, {}).get(component_type, [])

    def remove_all(self, plugin_id: str) -> None:
        """Remove all components for a plugin.

        Args:
            plugin_id: The plugin ID.
        """
        if plugin_id in self._components:
            del self._components[plugin_id]

    def has_plugin(self, plugin_id: str) -> bool:
        """Check if a plugin has any components.

        Args:
            plugin_id: The plugin ID.

        Returns:
            True if the plugin has components, False otherwise.
        """
        return plugin_id in self._components


class UIIntegration(abc.ABC):
    """Interface for UI integration."""

    @abc.abstractmethod
    def add_tab(
            self,
            plugin_id: str,
            tab: Union[TabComponent, QWidget],
            title: str,
            icon: Optional[QIcon] = None
    ) -> int:
        """Add a tab.

        Args:
            plugin_id: The plugin ID.
            tab: The tab component or widget.
            title: The tab title.
            icon: The tab icon.

        Returns:
            The tab index.
        """
        ...

    @abc.abstractmethod
    def remove_tab(self, tab_index: int) -> None:
        """Remove a tab.

        Args:
            tab_index: The tab index.
        """
        ...

    @abc.abstractmethod
    def find_menu(self, menu_title: str) -> Optional[QMenu]:
        """Find a menu by title.

        Args:
            menu_title: The menu title.

        Returns:
            The menu, or None if not found.
        """
        ...

    @abc.abstractmethod
    def add_menu(
            self,
            plugin_id: str,
            title: str,
            parent_menu: Optional[Union[str, QMenu]] = None
    ) -> QMenu:
        """Add a menu.

        Args:
            plugin_id: The plugin ID.
            title: The menu title.
            parent_menu: The parent menu or its title.

        Returns:
            The created menu.
        """
        ...

    @abc.abstractmethod
    def add_menu_action(
            self,
            plugin_id: str,
            menu: Union[str, QMenu],
            text: str,
            callback: Callable[[], None],
            icon: Optional[QIcon] = None
    ) -> QAction:
        """Add an action to a menu.

        Args:
            plugin_id: The plugin ID.
            menu: The menu or its title.
            text: The action text.
            callback: The action callback.
            icon: The action icon.

        Returns:
            The created action.
        """
        ...

    @abc.abstractmethod
    def add_toolbar(self, plugin_id: str, title: str) -> QToolBar:
        """Add a toolbar.

        Args:
            plugin_id: The plugin ID.
            title: The toolbar title.

        Returns:
            The created toolbar.
        """
        ...

    @abc.abstractmethod
    def add_toolbar_action(
            self,
            plugin_id: str,
            toolbar: QToolBar,
            text: str,
            callback: Callable[[], None],
            icon: Optional[QIcon] = None
    ) -> QAction:
        """Add an action to a toolbar.

        Args:
            plugin_id: The plugin ID.
            toolbar: The toolbar.
            text: The action text.
            callback: The action callback.
            icon: The action icon.

        Returns:
            The created action.
        """
        ...

    @abc.abstractmethod
    def add_dock_widget(
            self,
            plugin_id: str,
            dock: Union[DockComponent, QWidget],
            title: str,
            area: str = 'right'
    ) -> QDockWidget:
        """Add a dock widget.

        Args:
            plugin_id: The plugin ID.
            dock: The dock component or widget.
            title: The dock title.
            area: The dock area ('left', 'right', 'top', 'bottom').

        Returns:
            The created dock widget.
        """
        ...

    @abc.abstractmethod
    def cleanup_plugin(self, plugin_id: str) -> None:
        """Clean up UI components for a plugin.

        Args:
            plugin_id: The plugin ID.
        """
        ...


class MainWindowIntegration(UIIntegration):
    """UI integration for the main window."""

    def __init__(self, main_window: Any) -> None:
        """Initialize the main window integration.

        Args:
            main_window: The main window.
        """
        self.main_window = main_window
        self._logger = getattr(main_window, '_logger', None)

        # Track components
        self._tab_components = ComponentTracker[Tuple[int, Union[TabComponent, QWidget]]]()
        self._menu_components = ComponentTracker[QMenu]()
        self._action_components = ComponentTracker[Tuple[QAction, Optional[QMenu]]]()
        self._toolbar_components = ComponentTracker[QToolBar]()
        self._dock_components = ComponentTracker[QDockWidget]()

        # Keep strong references to menus and actions
        self._menus: Dict[str, QMenu] = {}
        self._actions: Dict[str, List[QAction]] = {}

        # Copy any existing menus from the main window
        if hasattr(main_window, '_menus') and isinstance(main_window._menus, dict):
            self._menus.update(main_window._menus)
        else:
            # Try to find menus from the menu bar
            try:
                menu_bar = main_window.menuBar()
                for action in menu_bar.actions():
                    menu = action.menu()
                    if menu:
                        self._menus[action.text()] = menu
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Failed to copy menus from main window: {str(e)}")

    def add_tab(
            self,
            plugin_id: str,
            tab: Union[TabComponent, QWidget],
            title: str,
            icon: Optional[QIcon] = None
    ) -> int:
        """Add a tab.

        Args:
            plugin_id: The plugin ID.
            tab: The tab component or widget.
            title: The tab title.
            icon: The tab icon.

        Returns:
            The tab index.
        """
        central_tabs = self.main_window._central_tabs
        if not central_tabs:
            raise ValueError('Central tabs widget not found in main window')

        if hasattr(tab, 'get_widget') and callable(tab.get_widget):
            widget = tab.get_widget()
        else:
            widget = tab

        tab_index = central_tabs.addTab(widget, title)

        if icon:
            central_tabs.setTabIcon(tab_index, icon)

        self._tab_components.add(plugin_id, 'tabs', (tab_index, tab))

        if self._logger:
            self._logger.debug(
                f"Added tab '{title}' for plugin '{plugin_id}' at index {tab_index}"
            )

        return tab_index

    def remove_tab(self, tab_index: int) -> None:
        """Remove a tab.

        Args:
            tab_index: The tab index.
        """
        central_tabs = self.main_window._central_tabs
        if not central_tabs:
            return

        central_tabs.removeTab(tab_index)

        if self._logger:
            self._logger.debug(f'Removed tab at index {tab_index}')

    def find_menu(self, menu_title: str) -> Optional[QMenu]:
        """Find a menu by title.

        Args:
            menu_title: The menu title.

        Returns:
            The menu, or None if not found.
        """
        # First check our cached menus
        if menu_title in self._menus:
            return self._menus[menu_title]

        # Check if the main window has a get_menu method
        if hasattr(self.main_window, 'get_menu') and callable(self.main_window.get_menu):
            menu = self.main_window.get_menu(menu_title)
            if menu:
                self._menus[menu_title] = menu
                return menu

        # Fall back to searching the menu bar
        try:
            menu_bar = self.main_window.menuBar()
            for action in menu_bar.actions():
                if action.text() == menu_title:
                    menu = action.menu()
                    if menu:
                        self._menus[menu_title] = menu
                        return menu
        except Exception as e:
            if self._logger:
                self._logger.warning(f"Error finding menu '{menu_title}': {str(e)}")

        return None

    def add_menu(
            self,
            plugin_id: str,
            title: str,
            parent_menu: Optional[Union[str, QMenu]] = None
    ) -> QMenu:
        """Add a menu.

        Args:
            plugin_id: The plugin ID.
            title: The menu title.
            parent_menu: The parent menu or its title.

        Returns:
            The created menu.
        """
        # Check if menu already exists
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
                        self._logger.warning(
                            f"Parent menu '{parent_menu}' not found, creating at top level"
                        )
            else:
                parent = parent_menu

        # Create the menu
        menu = QMenu(title, self.main_window)

        # Add it to the parent or menu bar
        if parent:
            parent.addMenu(menu)
        else:
            menu_bar.addMenu(menu)

        # Store references
        self._menu_components.add(plugin_id, 'menus', menu)
        self._menus[title] = menu

        if self._logger:
            parent_name = parent.title() if parent else 'menu bar'
            self._logger.debug(
                f"Added menu '{title}' for plugin '{plugin_id}' to {parent_name}"
            )

        return menu

    def add_menu_action(
            self,
            plugin_id: str,
            menu: Union[str, QMenu],
            text: str,
            callback: Callable[[], None],
            icon: Optional[QIcon] = None
    ) -> QAction:
        """Add an action to a menu.

        Args:
            plugin_id: The plugin ID.
            menu: The menu or its title.
            text: The action text.
            callback: The action callback.
            icon: The action icon.

        Returns:
            The created action.
        """
        target_menu = None

        if isinstance(menu, str):
            target_menu = self.find_menu(menu)
            if not target_menu:
                if self._logger:
                    self._logger.warning(f"Menu '{menu}' not found, creating it")
                target_menu = self.add_menu(plugin_id, menu)
        else:
            target_menu = menu

        for action, parent_menu in self._action_components.get_by_type(plugin_id, 'actions'):
            if action.text() == text and parent_menu == target_menu:
                return action

        # Create the action
        action = QAction(text, self.main_window)

        if icon:
            action.setIcon(icon)

        action.triggered.connect(callback)
        target_menu.addAction(action)

        # Store references
        self._action_components.add(plugin_id, 'actions', (action, target_menu))

        if plugin_id not in self._actions:
            self._actions[plugin_id] = []
        self._actions[plugin_id].append(action)

        if self._logger:
            menu_name = target_menu.title() if target_menu else 'unknown menu'
            self._logger.debug(
                f"Added action '{text}' for plugin '{plugin_id}' to menu '{menu_name}'"
            )

        return action

    def add_toolbar(self, plugin_id: str, title: str) -> QToolBar:
        """Add a toolbar.

        Args:
            plugin_id: The plugin ID.
            title: The toolbar title.

        Returns:
            The created toolbar.
        """
        toolbar = self.main_window.addToolBar(title)

        # Store references
        self._toolbar_components.add(plugin_id, 'toolbars', toolbar)

        if hasattr(self.main_window, '_toolbars') and isinstance(self.main_window._toolbars, dict):
            self.main_window._toolbars[title] = toolbar

        if self._logger:
            self._logger.debug(f"Added toolbar '{title}' for plugin '{plugin_id}'")

        return toolbar

    def add_toolbar_action(
            self,
            plugin_id: str,
            toolbar: QToolBar,
            text: str,
            callback: Callable[[], None],
            icon: Optional[QIcon] = None
    ) -> QAction:
        """Add an action to a toolbar.

        Args:
            plugin_id: The plugin ID.
            toolbar: The toolbar.
            text: The action text.
            callback: The action callback.
            icon: The action icon.

        Returns:
            The created action.
        """
        # Create the action
        action = QAction(text, self.main_window)

        if icon:
            action.setIcon(icon)

        action.triggered.connect(callback)
        toolbar.addAction(action)

        # Store references
        self._action_components.add(plugin_id, 'actions', (action, None))

        if plugin_id not in self._actions:
            self._actions[plugin_id] = []
        self._actions[plugin_id].append(action)

        if self._logger:
            self._logger.debug(f"Added toolbar action '{text}' for plugin '{plugin_id}'")

        return action

    def add_dock_widget(
            self,
            plugin_id: str,
            dock: Union[DockComponent, QWidget],
            title: str,
            area: str = 'right'
    ) -> QDockWidget:
        """Add a dock widget.

        Args:
            plugin_id: The plugin ID.
            dock: The dock component or widget.
            title: The dock title.
            area: The dock area ('left', 'right', 'top', 'bottom').

        Returns:
            The created dock widget.
        """
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

        # Store references
        self._dock_components.add(plugin_id, 'docks', dock_widget)

        if self._logger:
            self._logger.debug(
                f"Added dock widget '{title}' for plugin '{plugin_id}' in area '{area}'"
            )

        return dock_widget

    def cleanup_plugin(self, plugin_id: str) -> None:
        """Clean up UI components for a plugin.

        Args:
            plugin_id: The plugin ID.
        """
        if self._logger:
            self._logger.debug(f"Cleaning up UI components for plugin '{plugin_id}'")

        # Clean up tabs
        for tab_index, tab in self._tab_components.get_by_type(plugin_id, 'tabs'):
            try:
                self.remove_tab(tab_index)
            except Exception as e:
                if self._logger:
                    self._logger.warning(
                        f"Error removing tab for plugin '{plugin_id}': {str(e)}"
                    )

        # Clean up actions
        for action, parent_menu in self._action_components.get_by_type(plugin_id, 'actions'):
            try:
                if parent_menu:
                    parent_menu.removeAction(action)
                action.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(
                        f"Error removing action for plugin '{plugin_id}': {str(e)}"
                    )

        # Clean up menus
        for menu in self._menu_components.get_by_type(plugin_id, 'menus'):
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
                    self._logger.warning(
                        f"Error removing menu for plugin '{plugin_id}': {str(e)}"
                    )

        # Clean up toolbars
        for toolbar in self._toolbar_components.get_by_type(plugin_id, 'toolbars'):
            try:
                self.main_window.removeToolBar(toolbar)
                toolbar.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(
                        f"Error removing toolbar for plugin '{plugin_id}': {str(e)}"
                    )

        # Clean up dock widgets
        for dock_widget in self._dock_components.get_by_type(plugin_id, 'docks'):
            try:
                self.main_window.removeDockWidget(dock_widget)
                dock_widget.deleteLater()
            except Exception as e:
                if self._logger:
                    self._logger.warning(
                        f"Error removing dock widget for plugin '{plugin_id}': {str(e)}"
                    )

        # Clean up stored references
        self._tab_components.remove_all(plugin_id)
        self._menu_components.remove_all(plugin_id)
        self._action_components.remove_all(plugin_id)
        self._toolbar_components.remove_all(plugin_id)
        self._dock_components.remove_all(plugin_id)

        # Clean up action references
        if plugin_id in self._actions:
            del self._actions[plugin_id]

        if self._logger:
            self._logger.info(f"UI cleanup complete for plugin '{plugin_id}'")