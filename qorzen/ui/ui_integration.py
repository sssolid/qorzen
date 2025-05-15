#!/usr/bin/env python3
# qorzen/ui/async_ui_integration.py

from __future__ import annotations

import asyncio
import logging
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable, Protocol, TypeVar

from pydantic import BaseModel, Field, validator
from PySide6.QtCore import QObject, Signal, Slot, Qt

from qorzen.utils.exceptions import UIError

T = TypeVar('T')


class UIElementType(str, Enum):
    """Types of UI elements that can be managed by the UI integration system."""

    PAGE = 'page'
    WIDGET = 'widget'
    MENU_ITEM = 'menu_item'
    TOOLBAR_ITEM = 'toolbar_item'
    DIALOG = 'dialog'
    PANEL = 'panel'
    NOTIFICATION = 'notification'
    STATUS_BAR = 'status_bar'
    DOCK = 'dock'


class UIOperation(str, Enum):
    """Operations that can be performed on UI elements."""

    ADD = 'add'
    REMOVE = 'remove'
    UPDATE = 'update'
    SHOW = 'show'
    HIDE = 'hide'


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


class UIOperationModel(BaseModel):
    """Model for UI operations to be executed on the main thread."""

    operation: UIOperation
    element_info: Dict[str, Any]
    component: Optional[Any] = None
    callback: Optional[Callable[..., Any]] = None
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)

    @validator('element_info')
    def validate_element_info(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that element_info contains required fields."""
        required_fields = ['element_id', 'element_type', 'title', 'plugin_id']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Missing required field '{field}' in element_info")
        return v


class UICallbackProtocol(Protocol):
    """Protocol for UI callbacks that may be async or sync."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...


class UISignals(QObject):
    """QObject to hold signals for UI operations."""

    operation_ready = Signal(object)  # Signal emitted when an operation is ready to be executed


class UIIntegration:
    """
    Asynchronous UI integration system that bridges between async backend and UI components.

    This class manages UI elements and handles interactions between plugins and the UI.
    It ensures that UI operations are executed on the main thread while allowing
    async operations to run in the background.
    """

    def __init__(self, main_window: Any, concurrency_manager: Any, logger_manager: Any) -> None:
        """
        Initialize AsyncUIIntegration.

        Args:
            main_window: The main window of the application
            concurrency_manager: Manager for handling concurrency
            logger_manager: Manager for logging
        """
        self._main_window = main_window
        self._concurrency_manager = concurrency_manager
        self._logger = logger_manager.get_logger('ui_integration')

        # UI elements and tracking
        self._elements: Dict[str, UIElementInfo] = {}
        self._element_instances: Dict[str, Any] = {}
        self._plugin_elements: Dict[str, Set[str]] = {}
        self._element_lock = asyncio.Lock()

        # Operations queue and processing
        self._ui_queue: asyncio.Queue[UIOperationModel] = asyncio.Queue()
        self._worker_task = asyncio.create_task(self._ui_worker())
        self._main_thread_id = threading.get_ident()

        # Qt signals for thread-safe operations
        self._signals = UISignals()
        self._signals.operation_ready.connect(self._execute_ui_operation_on_main_thread, Qt.QueuedConnection)

    async def add_page(
            self,
            plugin_id: str,
            page_component: Any,
            title: str,
            icon: Optional[str] = None,
            position: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a page to the main window.

        Args:
            plugin_id: ID of the plugin adding the page
            page_component: The page widget to add
            title: Title of the page
            icon: Icon for the page
            position: Position in the page list
            metadata: Additional metadata

        Returns:
            str: ID of the created page element
        """
        element_id = f'page_{plugin_id}_{uuid.uuid4().hex[:8]}'
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.PAGE,
            title=title,
            plugin_id=plugin_id,
            position=position,
            icon=icon,
            metadata=metadata or {},
        )
        await self._queue_ui_operation(
            operation=UIOperation.ADD,
            element_info=element_info,
            component=page_component
        )
        await self._register_element(element_info, page_component)
        return element_id

    async def add_menu_item(
            self,
            plugin_id: str,
            title: str,
            callback: Callable[[], Any],
            parent_menu: str = 'Plugins',
            icon: Optional[str] = None,
            position: Optional[int] = None,
            tooltip: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a menu item to a menu.

        Args:
            plugin_id: ID of the plugin adding the menu item
            title: Text for the menu item
            callback: Function to call when the menu item is activated
            parent_menu: Name of the parent menu
            icon: Icon for the menu item
            position: Position in the menu
            tooltip: Tooltip text
            metadata: Additional metadata

        Returns:
            str: ID of the created menu item element
        """
        element_id = f'menu_{plugin_id}_{uuid.uuid4().hex[:8]}'
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.MENU_ITEM,
            title=title,
            plugin_id=plugin_id,
            parent_id=parent_menu,
            position=position,
            icon=icon,
            tooltip=tooltip,
            metadata=metadata or {},
        )

        # Create a callback wrapper that will run the callback in an async task
        wrapped_callback = lambda: asyncio.create_task(self._run_ui_callback(plugin_id, callback))

        await self._queue_ui_operation(
            operation=UIOperation.ADD,
            element_info=element_info,
            callback=wrapped_callback
        )
        await self._register_element(element_info, wrapped_callback)
        return element_id

    async def add_toolbar_item(
            self,
            plugin_id: str,
            title: str,
            callback: Callable[[], Any],
            icon: Optional[str] = None,
            position: Optional[int] = None,
            tooltip: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a toolbar item to the main window.

        Args:
            plugin_id: ID of the plugin adding the toolbar item
            title: Text for the toolbar item
            callback: Function to call when the toolbar item is activated
            icon: Icon for the toolbar item
            position: Position in the toolbar
            tooltip: Tooltip text
            metadata: Additional metadata

        Returns:
            str: ID of the created toolbar item element
        """
        element_id = f'toolbar_{plugin_id}_{uuid.uuid4().hex[:8]}'
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.TOOLBAR_ITEM,
            title=title,
            plugin_id=plugin_id,
            position=position,
            icon=icon,
            tooltip=tooltip,
            metadata=metadata or {},
        )

        # Create a callback wrapper that will run the callback in an async task
        wrapped_callback = lambda: asyncio.create_task(self._run_ui_callback(plugin_id, callback))

        await self._queue_ui_operation(
            operation=UIOperation.ADD,
            element_info=element_info,
            callback=wrapped_callback
        )
        await self._register_element(element_info, wrapped_callback)
        return element_id

    async def add_widget(
            self,
            plugin_id: str,
            widget_component: Any,
            parent_id: str,
            title: Optional[str] = None,
            position: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a widget to a parent container.

        Args:
            plugin_id: ID of the plugin adding the widget
            widget_component: The widget to add
            parent_id: ID of the parent container
            title: Title of the widget
            position: Position in the container
            metadata: Additional metadata

        Returns:
            str: ID of the created widget element
        """
        element_id = f'widget_{plugin_id}_{uuid.uuid4().hex[:8]}'
        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.WIDGET,
            title=title or f'Widget {element_id}',
            plugin_id=plugin_id,
            parent_id=parent_id,
            position=position,
            metadata=metadata or {},
        )
        await self._queue_ui_operation(
            operation=UIOperation.ADD,
            element_info=element_info,
            component=widget_component
        )
        await self._register_element(element_info, widget_component)
        return element_id

    async def add_panel(
            self,
            plugin_id: str,
            panel_component: Any,
            title: str,
            dock_area: str = 'right',
            icon: Optional[str] = None,
            closable: bool = True,
            metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a panel to the main window.

        Args:
            plugin_id: ID of the plugin adding the panel
            panel_component: The panel widget to add
            title: Title of the panel
            dock_area: Area to dock the panel (left, right, top, bottom)
            icon: Icon for the panel
            closable: Whether the panel can be closed
            metadata: Additional metadata

        Returns:
            str: ID of the created panel element
        """
        element_id = f'panel_{plugin_id}_{uuid.uuid4().hex[:8]}'

        # Ensure we have metadata with the closable property
        panel_metadata = metadata or {}
        panel_metadata['closable'] = closable

        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.PANEL,
            title=title,
            plugin_id=plugin_id,
            parent_id=dock_area,
            icon=icon,
            metadata=panel_metadata,
        )
        await self._queue_ui_operation(
            operation=UIOperation.ADD,
            element_info=element_info,
            component=panel_component
        )
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
            metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Show a dialog window.

        Args:
            plugin_id: ID of the plugin showing the dialog
            dialog_component: The dialog widget to show
            title: Title of the dialog
            modal: Whether the dialog is modal
            width: Width of the dialog
            height: Height of the dialog
            metadata: Additional metadata

        Returns:
            str: ID of the created dialog element
        """
        element_id = f'dialog_{plugin_id}_{uuid.uuid4().hex[:8]}'

        # Ensure we have metadata with the dialog properties
        dialog_metadata = metadata or {}
        dialog_metadata.update({
            'modal': modal,
            'width': width,
            'height': height
        })

        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.DIALOG,
            title=title,
            plugin_id=plugin_id,
            metadata=dialog_metadata,
        )
        await self._queue_ui_operation(
            operation=UIOperation.SHOW,
            element_info=element_info,
            component=dialog_component
        )
        await self._register_element(element_info, dialog_component)
        return element_id

    async def show_notification(
            self,
            plugin_id: str,
            message: str,
            title: Optional[str] = None,
            notification_type: str = 'info',
            duration: int = 5000,
            metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Show a notification message.

        Args:
            plugin_id: ID of the plugin showing the notification
            message: Message text
            title: Title of the notification
            notification_type: Type of notification (info, warning, error, success)
            duration: Duration in milliseconds
            metadata: Additional metadata

        Returns:
            str: ID of the created notification element
        """
        element_id = f'notification_{plugin_id}_{uuid.uuid4().hex[:8]}'

        # Ensure we have metadata with the notification properties
        notification_metadata = metadata or {}
        notification_metadata.update({
            'type': notification_type,
            'duration': duration,
            'message': message
        })

        element_info = UIElementInfo(
            element_id=element_id,
            element_type=UIElementType.NOTIFICATION,
            title=title or f'Notification from {plugin_id}',
            plugin_id=plugin_id,
            metadata=notification_metadata,
        )
        await self._queue_ui_operation(
            operation=UIOperation.SHOW,
            element_info=element_info
        )
        await self._register_element(element_info, None)
        return element_id

    async def remove_element(self, element_id: str) -> bool:
        """
        Remove a UI element.

        Args:
            element_id: ID of the element to remove

        Returns:
            bool: Whether the element was successfully removed
        """
        async with self._element_lock:
            if element_id not in self._elements:
                return False
            element_info = self._elements[element_id]

        await self._queue_ui_operation(
            operation=UIOperation.REMOVE,
            element_info=element_info
        )
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
            metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update a UI element's properties.

        Args:
            element_id: ID of the element to update
            visible: Whether the element is visible
            enabled: Whether the element is enabled
            title: New title for the element
            icon: New icon for the element
            tooltip: New tooltip for the element
            metadata: Additional metadata to update

        Returns:
            bool: Whether the element was successfully updated
        """
        async with self._element_lock:
            if element_id not in self._elements:
                return False
            element_info = self._elements[element_id]

            # Update the element properties
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

        await self._queue_ui_operation(
            operation=UIOperation.UPDATE,
            element_info=element_info
        )
        return True

    async def clear_plugin_elements(self, plugin_id: str) -> int:
        """
        Remove all UI elements created by a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            int: Number of elements removed
        """
        async with self._element_lock:
            if plugin_id not in self._plugin_elements:
                return 0
            element_ids = list(self._plugin_elements[plugin_id])

        removed_count = 0
        for element_id in element_ids:
            if await self.remove_element(element_id):
                removed_count += 1

        return removed_count

    async def _register_element(self, element_info: UIElementInfo, element: Any) -> None:
        """
        Register a UI element in the internal tracking.

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
        """
        Unregister a UI element from the internal tracking.

        Args:
            element_id: ID of the element to unregister
        """
        async with self._element_lock:
            if element_id not in self._elements:
                return

            element_info = self._elements[element_id]
            plugin_id = element_info.plugin_id

            del self._elements[element_id]
            if element_id in self._element_instances:
                del self._element_instances[element_id]

            if plugin_id in self._plugin_elements:
                self._plugin_elements[plugin_id].discard(element_id)
                if not self._plugin_elements[plugin_id]:
                    del self._plugin_elements[plugin_id]

    async def _queue_ui_operation(
            self,
            operation: UIOperation,
            element_info: UIElementInfo,
            component: Any = None,
            callback: Optional[Callable[..., Any]] = None,
    ) -> None:
        """
        Queue a UI operation to be executed on the main thread.

        Args:
            operation: The operation to perform
            element_info: Information about the element
            component: The UI component (if applicable)
            callback: A callback function (if applicable)
        """
        # Convert the element_info to a dict for the model
        element_info_dict = {
            'element_id': element_info.element_id,
            'element_type': element_info.element_type.value,
            'title': element_info.title,
            'plugin_id': element_info.plugin_id,
            'position': element_info.position,
            'parent_id': element_info.parent_id,
            'icon': element_info.icon,
            'tooltip': element_info.tooltip,
            'visible': element_info.visible,
            'enabled': element_info.enabled,
            'metadata': element_info.metadata,
        }

        # Create the operation model
        op_model = UIOperationModel(
            operation=operation,
            element_info=element_info_dict,
            component=component,
            callback=callback,
        )

        # Put it in the queue for processing
        await self._ui_queue.put(op_model)

    async def _ui_worker(self) -> None:
        """Background worker that processes UI operations from the queue."""
        while True:
            try:
                # Get an operation from the queue
                op_model = await self._ui_queue.get()

                try:
                    # Execute the operation on the main thread
                    if threading.get_ident() == self._main_thread_id:
                        # If we're already on the main thread, execute directly
                        self._execute_ui_operation_on_main_thread(op_model)
                    else:
                        # Otherwise, use signals to execute on the main thread
                        self._signals.operation_ready.emit(op_model)

                except Exception as e:
                    self._logger.error(
                        f"Error executing UI operation {op_model.operation}: {e}",
                        extra={'error': str(e), 'traceback': traceback.format_exc()},
                    )
                finally:
                    self._ui_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(
                    f"Error in UI worker: {e}",
                    extra={'error': str(e), 'traceback': traceback.format_exc()},
                )

    @Slot(object)
    def _execute_ui_operation_on_main_thread(self, op_model: UIOperationModel) -> None:
        """
        Execute a UI operation on the main thread.

        Args:
            op_model: The operation model to execute
        """
        try:
            # Extract information from the model
            operation = op_model.operation
            element_info_dict = op_model.element_info
            component = op_model.component
            callback = op_model.callback

            # Create an UIElementInfo from the dict
            element_info = UIElementInfo(
                element_id=element_info_dict['element_id'],
                element_type=UIElementType(element_info_dict['element_type']),
                title=element_info_dict['title'],
                plugin_id=element_info_dict['plugin_id'],
                position=element_info_dict['position'],
                parent_id=element_info_dict['parent_id'],
                icon=element_info_dict['icon'],
                tooltip=element_info_dict['tooltip'],
                visible=element_info_dict['visible'],
                enabled=element_info_dict['enabled'],
                metadata=element_info_dict['metadata'],
            )

            # Execute the operation based on its type
            if operation == UIOperation.ADD:
                if element_info.element_type == UIElementType.PAGE:
                    self._add_page_on_main_thread(element_info, component)
                elif element_info.element_type == UIElementType.MENU_ITEM:
                    self._add_menu_item_on_main_thread(element_info, callback)
                elif element_info.element_type == UIElementType.TOOLBAR_ITEM:
                    self._add_toolbar_item_on_main_thread(element_info, callback)
                elif element_info.element_type == UIElementType.WIDGET:
                    self._add_widget_on_main_thread(element_info, component)
                elif element_info.element_type == UIElementType.PANEL:
                    self._add_panel_on_main_thread(element_info, component)

            elif operation == UIOperation.REMOVE:
                self._remove_element_on_main_thread(element_info)

            elif operation == UIOperation.UPDATE:
                self._update_element_on_main_thread(element_info)

            elif operation == UIOperation.SHOW:
                if element_info.element_type == UIElementType.DIALOG:
                    self._show_dialog_on_main_thread(element_info, component)
                elif element_info.element_type == UIElementType.NOTIFICATION:
                    self._show_notification_on_main_thread(element_info)

        except Exception as e:
            self._logger.error(
                f"Error executing UI operation on main thread: {e}",
                extra={'error': str(e), 'traceback': traceback.format_exc()},
            )

    def _add_page_on_main_thread(self, element_info: UIElementInfo, component: Any) -> None:
        """Add a page to the main window on the main thread."""
        try:
            if not hasattr(self._main_window, 'add_page'):
                self._logger.warning(
                    f"Main window does not have an add_page method, cannot add page: {element_info.element_id}"
                )
                return

            self._main_window.add_page(
                element_info.element_id,
                component,
                element_info.title,
                element_info.icon,
                element_info.position,
            )

            self._logger.debug(
                f"Added page: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id},
            )
        except Exception as e:
            self._logger.error(
                f"Error adding page {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    def _add_menu_item_on_main_thread(self, element_info: UIElementInfo, callback: Optional[Callable]) -> None:
        """Add a menu item to the main window on the main thread."""
        try:
            if not hasattr(self._main_window, 'add_menu_item'):
                self._logger.warning(
                    f"Main window does not have an add_menu_item method, cannot add menu item: {element_info.element_id}"
                )
                return

            if not callback:
                self._logger.warning(
                    f"No callback provided for menu item: {element_info.element_id}"
                )
                return

            self._main_window.add_menu_item(
                element_info.element_id,
                element_info.title,
                callback,
                element_info.parent_id or 'plugins',
                element_info.icon,
                element_info.position,
                element_info.tooltip,
            )

            self._logger.debug(
                f"Added menu item: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id, 'parent': element_info.parent_id},
            )
        except Exception as e:
            self._logger.error(
                f"Error adding menu item {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    def _add_toolbar_item_on_main_thread(self, element_info: UIElementInfo, callback: Optional[Callable]) -> None:
        """Add a toolbar item to the main window on the main thread."""
        try:
            if not hasattr(self._main_window, 'add_toolbar_item'):
                self._logger.warning(
                    f"Main window does not have an add_toolbar_item method, cannot add toolbar item: {element_info.element_id}"
                )
                return

            if not callback:
                self._logger.warning(
                    f"No callback provided for toolbar item: {element_info.element_id}"
                )
                return

            self._main_window.add_toolbar_item(
                element_info.element_id,
                element_info.title,
                callback,
                element_info.icon,
                element_info.position,
                element_info.tooltip,
            )

            self._logger.debug(
                f"Added toolbar item: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id},
            )
        except Exception as e:
            self._logger.error(
                f"Error adding toolbar item {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    def _add_widget_on_main_thread(self, element_info: UIElementInfo, component: Any) -> None:
        """Add a widget to a container on the main thread."""
        try:
            if not hasattr(self._main_window, 'add_widget'):
                self._logger.warning(
                    f"Main window does not have an add_widget method, cannot add widget: {element_info.element_id}"
                )
                return

            self._main_window.add_widget(
                element_info.element_id,
                component,
                element_info.parent_id,
                element_info.title,
                element_info.position,
            )

            self._logger.debug(
                f"Added widget: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id, 'parent': element_info.parent_id},
            )
        except Exception as e:
            self._logger.error(
                f"Error adding widget {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    def _add_panel_on_main_thread(self, element_info: UIElementInfo, component: Any) -> None:
        """Add a panel to the main window on the main thread."""
        try:
            if not hasattr(self._main_window, 'add_panel'):
                self._logger.warning(
                    f"Main window does not have an add_panel method, cannot add panel: {element_info.element_id}"
                )
                return

            closable = element_info.metadata.get('closable', True)

            self._main_window.add_panel(
                element_info.element_id,
                component,
                element_info.title,
                element_info.parent_id or 'right',
                element_info.icon,
                closable,
            )

            self._logger.debug(
                f"Added panel: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id, 'dock_area': element_info.parent_id},
            )
        except Exception as e:
            self._logger.error(
                f"Error adding panel {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    def _show_dialog_on_main_thread(self, element_info: UIElementInfo, component: Any) -> None:
        """Show a dialog on the main thread."""
        try:
            if not hasattr(self._main_window, 'show_dialog'):
                self._logger.warning(
                    f"Main window does not have a show_dialog method, cannot show dialog: {element_info.element_id}"
                )
                return

            modal = element_info.metadata.get('modal', True)
            width = element_info.metadata.get('width', 400)
            height = element_info.metadata.get('height', 300)

            self._main_window.show_dialog(
                element_info.element_id,
                component,
                element_info.title,
                modal,
                width,
                height,
            )

            self._logger.debug(
                f"Showed dialog: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id},
            )
        except Exception as e:
            self._logger.error(
                f"Error showing dialog {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    def _show_notification_on_main_thread(self, element_info: UIElementInfo) -> None:
        """Show a notification on the main thread."""
        try:
            if not hasattr(self._main_window, 'show_notification'):
                self._logger.warning(
                    f"Main window does not have a show_notification method, cannot show notification: {element_info.element_id}"
                )
                return

            message = element_info.metadata.get('message', '')
            notification_type = element_info.metadata.get('type', 'info')
            duration = element_info.metadata.get('duration', 5000)

            self._main_window.show_notification(
                message,
                element_info.title,
                notification_type,
                duration,
            )

            self._logger.debug(
                f"Showed notification: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id},
            )
        except Exception as e:
            self._logger.error(
                f"Error showing notification {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    def _remove_element_on_main_thread(self, element_info: UIElementInfo) -> None:
        """Remove a UI element on the main thread."""
        try:
            if not hasattr(self._main_window, 'remove_element'):
                self._logger.warning(
                    f"Main window does not have a remove_element method, cannot remove element: {element_info.element_id}"
                )
                return

            self._main_window.remove_element(element_info.element_id)

            self._logger.debug(
                f"Removed element: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id, 'type': element_info.element_type},
            )
        except Exception as e:
            self._logger.error(
                f"Error removing element {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    def _update_element_on_main_thread(self, element_info: UIElementInfo) -> None:
        """Update a UI element on the main thread."""
        try:
            if not hasattr(self._main_window, 'update_element'):
                self._logger.warning(
                    f"Main window does not have an update_element method, cannot update element: {element_info.element_id}"
                )
                return

            self._main_window.update_element(
                element_info.element_id,
                element_info.visible,
                element_info.enabled,
                element_info.title,
                element_info.icon,
                element_info.tooltip,
            )

            self._logger.debug(
                f"Updated element: {element_info.element_id}",
                extra={'plugin_id': element_info.plugin_id},
            )
        except Exception as e:
            self._logger.error(
                f"Error updating element {element_info.element_id}: {e}",
                extra={'plugin_id': element_info.plugin_id, 'error': str(e)},
            )

    async def _run_ui_callback(self, plugin_id: str, callback: UICallbackProtocol) -> None:
        """
        Run a UI callback safely, potentially on a background thread if it's async.

        Args:
            plugin_id: ID of the plugin that owns the callback
            callback: The callback function to run
        """
        try:
            # Check if the callback is an async function
            if asyncio.iscoroutinefunction(callback):
                # Run async function directly
                await callback()
            else:
                # Run synchronous function in a thread
                await self._concurrency_manager.run_in_thread(callback)

        except Exception as e:
            self._logger.error(
                f"Error in UI callback from plugin {plugin_id}: {e}",
                extra={'plugin_id': plugin_id, 'error': str(e), 'traceback': traceback.format_exc()},
            )

    async def shutdown(self) -> None:
        """Shut down the UI integration system."""
        # Cancel the worker task
        if hasattr(self, '_worker_task') and self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Clear all plugin elements
        async with self._element_lock:
            for plugin_id in list(self._plugin_elements.keys()):
                await self.clear_plugin_elements(plugin_id)

            self._elements.clear()
            self._element_instances.clear()
            self._plugin_elements.clear()

        self._logger.info("UI integration system shut down")

    def get_element_info(self, element_id: str) -> Optional[UIElementInfo]:
        """
        Get information about a UI element.

        Args:
            element_id: ID of the element

        Returns:
            Optional[UIElementInfo]: Information about the element or None if not found
        """
        return self._elements.get(element_id)

    def get_plugin_elements(self, plugin_id: str) -> List[UIElementInfo]:
        """
        Get all UI elements created by a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            List[UIElementInfo]: List of elements created by the plugin
        """
        element_ids = self._plugin_elements.get(plugin_id, set())
        return [self._elements[element_id] for element_id in element_ids if element_id in self._elements]

    def get_all_elements(self) -> List[UIElementInfo]:
        """
        Get all UI elements.

        Returns:
            List[UIElementInfo]: List of all UI elements
        """
        return list(self._elements.values())