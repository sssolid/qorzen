from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast


class UIComponentRegistry:
    """
    Registry for UI components.
    Manages UI elements added by plugins and handles cleanup when plugins are unloaded.
    """

    def __init__(self, plugin_name: str, thread_manager: Optional[Any] = None) -> None:
        """
        Initialize the UI component registry.

        Args:
            plugin_name: The name of the plugin this registry belongs to
            thread_manager: Optional thread manager for main thread operations
        """
        self.plugin_name = plugin_name
        self.thread_manager = thread_manager
        self.widgets: Set[Any] = set()
        self.menus: Set[Any] = set()
        self.actions: Set[Any] = set()
        self.dock_widgets: Set[Any] = set()
        self.dialogs: Set[Any] = set()
        self.sidebar_buttons: Set[Any] = set()
        self.lock = threading.RLock()  # Keep thread lock for backward compatibility

    def register(self, component: Any, component_type: str = 'widget') -> Any:
        """
        Register a UI component.

        Args:
            component: The UI component to register
            component_type: The type of component

        Returns:
            Any: The registered component
        """
        with self.lock:
            if component_type == 'menu':
                self.menus.add(component)
            elif component_type == 'action':
                self.actions.add(component)
            elif component_type == 'dock':
                self.dock_widgets.add(component)
            elif component_type == 'dialog':
                self.dialogs.add(component)
            elif component_type == 'sidebar_button':
                self.sidebar_buttons.add(component)
            else:
                self.widgets.add(component)
        return component

    async def cleanup(self) -> None:
        """
        Clean up all registered UI components asynchronously.
        This removes components from the UI and clears all registries.
        """
        if self.thread_manager and not self.thread_manager.is_main_thread():
            await self.thread_manager.run_on_main_thread(self._cleanup_sync)
            return

        self._cleanup_sync()

    def _cleanup_sync(self) -> None:
        """Synchronous implementation of cleanup for main thread execution."""
        with self.lock:
            # Clean up actions
            for action in list(self.actions):
                try:
                    parent = action.parentWidget()
                    if parent and hasattr(parent, 'removeAction'):
                        parent.removeAction(action)
                    if hasattr(action, 'deleteLater'):
                        action.deleteLater()
                except Exception:
                    pass
            self.actions.clear()

            # Clean up menus
            for menu in list(self.menus):
                try:
                    parent = menu.parentWidget()
                    if parent and hasattr(parent, 'removeAction'):
                        parent.removeAction(menu.menuAction())
                    if hasattr(menu, 'deleteLater'):
                        menu.deleteLater()
                except Exception:
                    pass
            self.menus.clear()

            # Clean up dock widgets
            for dock in list(self.dock_widgets):
                try:
                    if hasattr(dock, 'parentWidget') and dock.parentWidget():
                        if hasattr(dock.parentWidget(), 'removeDockWidget'):
                            dock.parentWidget().removeDockWidget(dock)
                    if hasattr(dock, 'deleteLater'):
                        dock.deleteLater()
                except Exception:
                    pass
            self.dock_widgets.clear()

            # Clean up dialogs
            for dialog in list(self.dialogs):
                try:
                    if hasattr(dialog, 'reject'):
                        dialog.reject()
                    if hasattr(dialog, 'deleteLater'):
                        dialog.deleteLater()
                except Exception:
                    pass
            self.dialogs.clear()

            # Clean up sidebar buttons
            for button in list(self.sidebar_buttons):
                try:
                    parent = button.parentWidget()
                    if parent and hasattr(parent, 'layout') and parent.layout():
                        parent.layout().removeWidget(button)
                    if hasattr(button, 'deleteLater'):
                        button.deleteLater()
                except Exception:
                    pass
            self.sidebar_buttons.clear()

            # Clean up widgets
            for widget in list(self.widgets):
                try:
                    parent = widget.parentWidget()
                    if parent and hasattr(parent, 'layout') and parent.layout():
                        parent.layout().removeWidget(widget)
                    if hasattr(widget, 'deleteLater'):
                        widget.deleteLater()
                except Exception:
                    pass
            self.widgets.clear()

    async def shutdown(self) -> None:
        """Shutdown the registry and clean up all components."""
        await self.cleanup()