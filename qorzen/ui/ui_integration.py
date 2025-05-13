from __future__ import annotations
import asyncio
import logging
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast


class UIElementType(str, Enum):
    """Types of UI elements that can be integrated."""
    PAGE = "page"
    WIDGET = "widget"
    MENU_ITEM = "menu_item"
    TOOLBAR_ITEM = "toolbar_item"
    DIALOG = "dialog"
    PANEL = "panel"
    NOTIFICATION = "notification"
    STATUS_BAR = "status_bar"
    DOCK = "dock"


@dataclass
class UIElementInfo:
    """Information about a UI element."""
    element_id: str
    element_type: UIElementType
    title: str
    plugin_id: str
    position: Optional[int] = None
    parent_id: Optional[str] = None
    icon: Optional[str] = None
    tooltip: Optional[str] = None
    visible: bool = True
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class UIIntegration:
    """Asynchronous UI integration for plugins.

    This class provides a bridge between the core application and plugins
    for UI integration. It allows plugins to add and remove UI elements
    asynchronously without freezing the UI.
    """

    def __init__(
            self,
            main_window: Any,
            concurrency_manager: Any,
            logger_manager: Any
    ) -> None:
        """Initialize the UI integration.

        Args:
            main_window: The main application window
            concurrency_manager: Concurrency manager for thread operations
            logger_manager: Logger manager
        """
        self._main_window = main_window
        self._concurrency_manager = concurrency_manager
        self._logger = logger_manager.get_logger('ui_integration')

        self._elements: Dict[str, UIElementInfo] = {}
        self._element_instances: Dict[str, Any] = {}
        self._plugin_elements: Dict[str, Set[str]] = {}
        self._element_lock = asyncio.Lock()

        # UI operation queue and worker
        self._ui_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task = asyncio.create_task(self._ui_worker())

    async def add_page(
            self,
            plugin_id: str,
            page_component: Any,
            title: str,
            icon: Optional[str] = None,
            position: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a page to the main UI.

        Args:
            plugin_id: ID of the plugin adding the page
            page_component: The page component to add
            title: Title of the page
            icon: Icon for the page
            position: Position in the page list
            metadata: Additional metadata

        Returns:
            ID of the added page

        Raises:
            RuntimeError: If adding the page fails
        """
        element_id = f"page_{plugin_id}_{uuid.uuid4().hex[:8]}"

        # Create element info
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.PAGE,
            title=title,
            plugin_id=plugin_id,
            position=position,
            icon=icon,
            metadata=metadata or {}
        )

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='add_page',
            element_info=element_info,
            component=page_component
        )

        # Register the element
        await self._register_element(element_info, page_component)

        return element_id

    async def add_menu_item(
            self,
            plugin_id: str,
            title: str,
            callback: Callable,
            parent_menu: str = "plugins",
            icon: Optional[str] = None,
            position: Optional[int] = None,
            tooltip: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a menu item to the application menu.

        Args:
            plugin_id: ID of the plugin adding the menu item
            title: Title of the menu item
            callback: Function to call when the menu item is clicked
            parent_menu: Parent menu to add the item to
            icon: Icon for the menu item
            position: Position in the menu
            tooltip: Tooltip text
            metadata: Additional metadata

        Returns:
            ID of the added menu item

        Raises:
            RuntimeError: If adding the menu item fails
        """
        element_id = f"menu_{plugin_id}_{uuid.uuid4().hex[:8]}"

        # Create element info
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.MENU_ITEM,
            title=title,
            plugin_id=plugin_id,
            parent_id=parent_menu,
            position=position,
            icon=icon,
            tooltip=tooltip,
            metadata=metadata or {}
        )

        # Wrap the callback to ensure it runs in the correct context
        wrapped_callback = lambda: asyncio.create_task(
            self._run_ui_callback(plugin_id, callback)
        )

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='add_menu_item',
            element_info=element_info,
            callback=wrapped_callback
        )

        # Register the element
        await self._register_element(element_info, wrapped_callback)

        return element_id

    async def add_toolbar_item(
            self,
            plugin_id: str,
            title: str,
            callback: Callable,
            icon: Optional[str] = None,
            position: Optional[int] = None,
            tooltip: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add an item to the toolbar.

        Args:
            plugin_id: ID of the plugin adding the toolbar item
            title: Title of the toolbar item
            callback: Function to call when the toolbar item is clicked
            icon: Icon for the toolbar item
            position: Position in the toolbar
            tooltip: Tooltip text
            metadata: Additional metadata

        Returns:
            ID of the added toolbar item

        Raises:
            RuntimeError: If adding the toolbar item fails
        """
        element_id = f"toolbar_{plugin_id}_{uuid.uuid4().hex[:8]}"

        # Create element info
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.TOOLBAR_ITEM,
            title=title,
            plugin_id=plugin_id,
            position=position,
            icon=icon,
            tooltip=tooltip,
            metadata=metadata or {}
        )

        # Wrap the callback to ensure it runs in the correct context
        wrapped_callback = lambda: asyncio.create_task(
            self._run_ui_callback(plugin_id, callback)
        )

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='add_toolbar_item',
            element_info=element_info,
            callback=wrapped_callback
        )

        # Register the element
        await self._register_element(element_info, wrapped_callback)

        return element_id

    async def add_widget(
            self,
            plugin_id: str,
            widget_component: Any,
            parent_id: str,
            title: Optional[str] = None,
            position: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a widget to a container.

        Args:
            plugin_id: ID of the plugin adding the widget
            widget_component: The widget component to add
            parent_id: ID of the parent container
            title: Optional title for the widget
            position: Position in the container
            metadata: Additional metadata

        Returns:
            ID of the added widget

        Raises:
            RuntimeError: If adding the widget fails
        """
        element_id = f"widget_{plugin_id}_{uuid.uuid4().hex[:8]}"

        # Create element info
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.WIDGET,
            title=title or f"Widget {element_id}",
            plugin_id=plugin_id,
            parent_id=parent_id,
            position=position,
            metadata=metadata or {}
        )

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='add_widget',
            element_info=element_info,
            component=widget_component
        )

        # Register the element
        await self._register_element(element_info, widget_component)

        return element_id

    async def add_panel(
            self,
            plugin_id: str,
            panel_component: Any,
            title: str,
            dock_area: str = "right",
            icon: Optional[str] = None,
            closable: bool = True,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a dockable panel to the UI.

        Args:
            plugin_id: ID of the plugin adding the panel
            panel_component: The panel component to add
            title: Title of the panel
            dock_area: Dock area ('left', 'right', 'bottom')
            icon: Icon for the panel
            closable: Whether the panel can be closed
            metadata: Additional metadata

        Returns:
            ID of the added panel

        Raises:
            RuntimeError: If adding the panel fails
        """
        element_id = f"panel_{plugin_id}_{uuid.uuid4().hex[:8]}"

        # Create element info
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.PANEL,
            title=title,
            plugin_id=plugin_id,
            parent_id=dock_area,
            icon=icon,
            metadata={
                **({'closable': closable} if metadata is None else metadata),
                'closable': closable
            }
        )

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='add_panel',
            element_info=element_info,
            component=panel_component
        )

        # Register the element
        await self._register_element(element_info, panel_component)

        return element_id

    async def show_dialog(
            self,
            plugin_id: str,
            dialog_component: Any,
            title: str,
            modal: bool = True,
            width: int = 400,
            height: int = 300,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Show a dialog.

        Args:
            plugin_id: ID of the plugin showing the dialog
            dialog_component: The dialog component to show
            title: Title of the dialog
            modal: Whether the dialog is modal
            width: Width of the dialog
            height: Height of the dialog
            metadata: Additional metadata

        Returns:
            ID of the shown dialog

        Raises:
            RuntimeError: If showing the dialog fails
        """
        element_id = f"dialog_{plugin_id}_{uuid.uuid4().hex[:8]}"

        # Create element info
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.DIALOG,
            title=title,
            plugin_id=plugin_id,
            metadata={
                **({'modal': modal, 'width': width, 'height': height}
                   if metadata is None else metadata),
                'modal': modal,
                'width': width,
                'height': height
            }
        )

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='show_dialog',
            element_info=element_info,
            component=dialog_component
        )

        # Register the element
        await self._register_element(element_info, dialog_component)

        return element_id

    async def show_notification(
            self,
            plugin_id: str,
            message: str,
            title: Optional[str] = None,
            type: str = "info",
            duration: int = 5000,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Show a notification.

        Args:
            plugin_id: ID of the plugin showing the notification
            message: Message to show
            title: Optional title for the notification
            type: Type of notification ('info', 'warning', 'error', 'success')
            duration: Duration in milliseconds
            metadata: Additional metadata

        Returns:
            ID of the shown notification

        Raises:
            RuntimeError: If showing the notification fails
        """
        element_id = f"notification_{plugin_id}_{uuid.uuid4().hex[:8]}"

        # Create element info
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.NOTIFICATION,
            title=title or f"Notification from {plugin_id}",
            plugin_id=plugin_id,
            metadata={
                **({'type': type, 'duration': duration, 'message': message}
                   if metadata is None else metadata),
                'type': type,
                'duration': duration,
                'message': message
            }
        )

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='show_notification',
            element_info=element_info
        )

        # Register the element
        await self._register_element(element_info, None)

        return element_id

    async def remove_element(self, element_id: str) -> bool:
        """Remove a UI element.

        Args:
            element_id: ID of the element to remove

        Returns:
            True if the element was removed, False otherwise

        Raises:
            RuntimeError: If removing the element fails
        """
        async with self._element_lock:
            if element_id not in self._elements:
                return False

            element_info = self._elements[element_id]

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='remove_element',
            element_info=element_info
        )

        # Unregister the element
        await self._unregister_element(element_id)

        return True

    async def update_element(
            self,
            element_id: str,
            visible: Optional[bool] = None,
            enabled: Optional[bool] = None,
            title: Optional[str] = None,
            icon: Optional[str] = None,
            tooltip: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a UI element.

        Args:
            element_id: ID of the element to update
            visible: New visibility state
            enabled: New enabled state
            title: New title
            icon: New icon
            tooltip: New tooltip
            metadata: New metadata to merge

        Returns:
            True if the element was updated, False otherwise

        Raises:
            RuntimeError: If updating the element fails
        """
        async with self._element_lock:
            if element_id not in self._elements:
                return False

            element_info = self._elements[element_id]

            # Update element info
            if visible is not None:
                element_info.visible = visible
            if enabled is not None:
                element_info.enabled = enabled
            if title is not None:
                element_info.title = title
            if icon is not None:
                element_info.icon = icon
            if tooltip is not None:
                element_info.tooltip = tooltip
            if metadata is not None:
                element_info.metadata.update(metadata)

        # Queue the UI operation
        await self._queue_ui_operation(
            operation='update_element',
            element_info=element_info
        )

        return True

    async def clear_plugin_elements(self, plugin_id: str) -> int:
        """Remove all UI elements for a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            Number of elements removed

        Raises:
            RuntimeError: If removing elements fails
        """
        async with self._element_lock:
            if plugin_id not in self._plugin_elements:
                return 0

            element_ids = list(self._plugin_elements[plugin_id])

        # Remove each element
        removed_count = 0
        for element_id in element_ids:
            if await self.remove_element(element_id):
                removed_count += 1

        return removed_count

    async def _register_element(self, element_info: UIElementInfo, element: Any) -> None:
        """Register a UI element.

        Args:
            element_info: Information about the element
            element: The element instance
        """
        async with self._element_lock:
            element_id = element_info.element_id
            plugin_id = element_info.plugin_id

            self._elements[element_id] = element_info
            self._element_instances[element_id] = element

            if plugin_id not in self._plugin_elements:
                self._plugin_elements[plugin_id] = set()

            self._plugin_elements[plugin_id].add(element_id)

    async def _unregister_element(self, element_id: str) -> None:
        """Unregister a UI element.

        Args:
            element_id: ID of the element to unregister
        """
        async with self._element_lock:
            if element_id not in self._elements:
                return

            element_info = self._elements[element_id]
            plugin_id = element_info.plugin_id

            # Remove from dictionaries
            del self._elements[element_id]
            if element_id in self._element_instances:
                del self._element_instances[element_id]

            # Remove from plugin elements
            if plugin_id in self._plugin_elements:
                self._plugin_elements[plugin_id].discard(element_id)

                # Clean up empty sets
                if not self._plugin_elements[plugin_id]:
                    del self._plugin_elements[plugin_id]

    async def _queue_ui_operation(
            self,
            operation: str,
            element_info: UIElementInfo,
            **kwargs: Any
    ) -> None:
        """Queue a UI operation to be executed on the main thread.

        Args:
            operation: Name of the operation
            element_info: Information about the element
            **kwargs: Additional arguments for the operation
        """
        await self._ui_queue.put({
            'operation': operation,
            'element_info': element_info,
            **kwargs
        })

    async def _ui_worker(self) -> None:
        """Worker task for processing UI operations."""
        while True:
            try:
                # Get an operation from the queue
                operation = await self._ui_queue.get()

                try:
                    # Execute the operation on the main thread
                    await self._execute_ui_operation(operation)
                except Exception as e:
                    self._logger.error(
                        f"Error executing UI operation {operation['operation']}: {e}",
                        exc_info=True
                    )
                finally:
                    # Mark the operation as done
                    self._ui_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in UI worker: {e}", exc_info=True)

    async def _execute_ui_operation(self, operation: Dict[str, Any]) -> None:
        """Execute a UI operation on the main thread.

        Args:
            operation: The operation to execute
        """
        op_type = operation['operation']
        element_info = operation['element_info']

        try:
            if op_type == 'add_page':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.add_page,
                    element_info.element_id,
                    operation['component'],
                    element_info.title,
                    element_info.icon,
                    element_info.position
                )
            elif op_type == 'add_menu_item':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.add_menu_item,
                    element_info.element_id,
                    element_info.title,
                    operation['callback'],
                    element_info.parent_id,
                    element_info.icon,
                    element_info.position,
                    element_info.tooltip
                )
            elif op_type == 'add_toolbar_item':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.add_toolbar_item,
                    element_info.element_id,
                    element_info.title,
                    operation['callback'],
                    element_info.icon,
                    element_info.position,
                    element_info.tooltip
                )
            elif op_type == 'add_widget':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.add_widget,
                    element_info.element_id,
                    operation['component'],
                    element_info.parent_id,
                    element_info.title,
                    element_info.position
                )
            elif op_type == 'add_panel':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.add_panel,
                    element_info.element_id,
                    operation['component'],
                    element_info.title,
                    element_info.parent_id,  # dock area
                    element_info.icon,
                    element_info.metadata.get('closable', True)
                )
            elif op_type == 'show_dialog':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.show_dialog,
                    element_info.element_id,
                    operation['component'],
                    element_info.title,
                    element_info.metadata.get('modal', True),
                    element_info.metadata.get('width', 400),
                    element_info.metadata.get('height', 300)
                )
            elif op_type == 'show_notification':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.show_notification,
                    element_info.metadata.get('message', ''),
                    element_info.title,
                    element_info.metadata.get('type', 'info'),
                    element_info.metadata.get('duration', 5000)
                )
            elif op_type == 'remove_element':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.remove_element,
                    element_info.element_id
                )
            elif op_type == 'update_element':
                await self._concurrency_manager.run_on_main_thread(
                    self._main_window.update_element,
                    element_info.element_id,
                    element_info.visible,
                    element_info.enabled,
                    element_info.title,
                    element_info.icon,
                    element_info.tooltip
                )
            else:
                self._logger.warning(f"Unknown UI operation: {op_type}")
        except Exception as e:
            self._logger.error(
                f"Error executing UI operation {op_type} for {element_info.element_id}: {e}",
                exc_info=True
            )
            raise

    async def _run_ui_callback(self, plugin_id: str, callback: Callable) -> None:
        """Run a UI callback safely.

        Args:
            plugin_id: ID of the plugin
            callback: Callback to run
        """
        try:
            # Check if the callback is async
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                # Run sync callback in a thread to avoid blocking
                await self._concurrency_manager.run_in_thread(callback)
        except Exception as e:
            self._logger.error(
                f"Error in UI callback from plugin {plugin_id}: {e}",
                exc_info=True
            )

    async def shutdown(self) -> None:
        """Shutdown the UI integration."""
        # Cancel the worker task
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Clear all elements
        async with self._element_lock:
            for plugin_id in list(self._plugin_elements.keys()):
                await self.clear_plugin_elements(plugin_id)

        self._elements.clear()
        self._element_instances.clear()
        self._plugin_elements.clear()

    def get_element_info(self, element_id: str) -> Optional[UIElementInfo]:
        """Get information about a UI element.

        Args:
            element_id: ID of the element

        Returns:
            Element information or None if not found
        """
        return self._elements.get(element_id)

    def get_plugin_elements(self, plugin_id: str) -> List[UIElementInfo]:
        """Get all UI elements for a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            List of element information
        """
        element_ids = self._plugin_elements.get(plugin_id, set())
        return [self._elements[element_id] for element_id in element_ids
                if element_id in self._elements]

    def get_all_elements(self) -> List[UIElementInfo]:
        """Get all registered UI elements.

        Returns:
            List of all element information
        """
        return list(self._elements.values())