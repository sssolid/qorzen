from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast


class UIComponentRegistry:
    """
    Manages UI components for a plugin.

    Responsibilities:
    - Track UI components
    - Facilitate safe cleanup
    - Ensure main thread operations
    """

    def __init__(self, plugin_name: str, thread_manager: Optional[Any] = None):
        """
        Initialize the UI registry.

        Args:
            plugin_name: Name of the plugin this registry belongs to
            thread_manager: Thread manager for main thread operations
        """
        self.plugin_name = plugin_name
        self.thread_manager = thread_manager
        self.widgets: Set[Any] = set()
        self.menus: Set[Any] = set()
        self.actions: Set[Any] = set()
        self.dock_widgets: Set[Any] = set()
        self.dialogs: Set[Any] = set()
        self.lock = threading.RLock()

    def register(self, component: Any, component_type: str = "widget") -> Any:
        """
        Register a UI component for tracking.

        Args:
            component: The UI component to register
            component_type: Type of component (widget, menu, action, dock, dialog)

        Returns:
            The registered component (for chaining)
        """
        with self.lock:
            if component_type == "menu":
                self.menus.add(component)
            elif component_type == "action":
                self.actions.add(component)
            elif component_type == "dock":
                self.dock_widgets.add(component)
            elif component_type == "dialog":
                self.dialogs.add(component)
            else:
                self.widgets.add(component)

        return component

    def cleanup(self) -> None:
        """
        Clean up all registered UI components.

        Ensures cleanup happens on the main thread.
        """
        # Ensure on main thread
        if self.thread_manager and not self.thread_manager.is_main_thread():
            self.thread_manager.execute_on_main_thread_sync(self.cleanup)
            return

        with self.lock:
            # Remove actions first
            for action in list(self.actions):
                try:
                    # Check if action is in a menu
                    parent = action.parentWidget()
                    if parent and hasattr(parent, "removeAction"):
                        parent.removeAction(action)

                    if hasattr(action, "deleteLater"):
                        action.deleteLater()
                except Exception:
                    pass  # Ignore errors during cleanup
            self.actions.clear()

            # Remove menus
            for menu in list(self.menus):
                try:
                    # Check if menu is in a menubar
                    parent = menu.parentWidget()
                    if parent and hasattr(parent, "removeAction"):
                        parent.removeAction(menu.menuAction())

                    if hasattr(menu, "deleteLater"):
                        menu.deleteLater()
                except Exception:
                    pass
            self.menus.clear()

            # Remove dock widgets
            for dock in list(self.dock_widgets):
                try:
                    if hasattr(dock, "parentWidget") and dock.parentWidget():
                        if hasattr(dock.parentWidget(), "removeDockWidget"):
                            dock.parentWidget().removeDockWidget(dock)

                    if hasattr(dock, "deleteLater"):
                        dock.deleteLater()
                except Exception:
                    pass
            self.dock_widgets.clear()

            # Remove dialogs
            for dialog in list(self.dialogs):
                try:
                    if hasattr(dialog, "reject"):
                        dialog.reject()

                    if hasattr(dialog, "deleteLater"):
                        dialog.deleteLater()
                except Exception:
                    pass
            self.dialogs.clear()

            # Remove other widgets
            for widget in list(self.widgets):
                try:
                    # Check if widget is in a layout
                    parent = widget.parentWidget()
                    if parent and hasattr(parent, "layout") and parent.layout():
                        parent.layout().removeWidget(widget)

                    if hasattr(widget, "deleteLater"):
                        widget.deleteLater()
                except Exception:
                    pass
            self.widgets.clear()