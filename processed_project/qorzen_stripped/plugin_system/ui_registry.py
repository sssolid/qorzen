from __future__ import annotations
import asyncio
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
class UIComponentRegistry:
    def __init__(self, plugin_name: str, thread_manager: Optional[Any]=None) -> None:
        self.plugin_name = plugin_name
        self.thread_manager = thread_manager
        self.widgets: Set[Any] = set()
        self.menus: Set[Any] = set()
        self.actions: Set[Any] = set()
        self.dock_widgets: Set[Any] = set()
        self.dialogs: Set[Any] = set()
        self.sidebar_buttons: Set[Any] = set()
        self.lock = threading.RLock()
    def register(self, component: Any, component_type: str='widget') -> Any:
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
        if self.thread_manager and (not self.thread_manager.is_main_thread()):
            await self.thread_manager.run_on_main_thread(self._cleanup_sync)
            return
        self._cleanup_sync()
    def _cleanup_sync(self) -> None:
        with self.lock:
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
            for dialog in list(self.dialogs):
                try:
                    if hasattr(dialog, 'reject'):
                        dialog.reject()
                    if hasattr(dialog, 'deleteLater'):
                        dialog.deleteLater()
                except Exception:
                    pass
            self.dialogs.clear()
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
        await self.cleanup()