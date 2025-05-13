#!/usr/bin/env python3
# qorzen/ui/async_ui_component.py

from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from typing import Any, Callable, Dict, List, Optional, Protocol, Type, TypeVar, Union, cast, Awaitable

from PySide6.QtCore import QObject, Signal, Slot, Qt, QThread, QTimer, QEvent
from PySide6.QtWidgets import QWidget, QApplication

from qorzen.utils.exceptions import UIError


class AsyncTaskSignals(QObject):
    """Signals for async task execution and completion."""

    started = Signal()
    result_ready = Signal(object)
    error = Signal(str, str)  # error message, traceback
    finished = Signal()


class UIComponent:
    """
    Base class for UI components that need to interact with async code.

    This class provides methods for running async tasks from the UI
    and handling the results on the main thread.
    """

    def __init__(self, widget: QWidget, concurrency_manager: Optional[Any] = None) -> None:
        """
        Initialize the async UI component.

        Args:
            widget: The QWidget that this component manages
            concurrency_manager: Optional concurrency manager for running tasks
        """
        self._widget = widget
        self._concurrency_manager = concurrency_manager
        self._task_signals = AsyncTaskSignals()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._logger = logging.getLogger(f"ui.async.{self.__class__.__name__}")

        # Connect signals to slots
        self._task_signals.result_ready.connect(self._on_task_result, Qt.QueuedConnection)
        self._task_signals.error.connect(self._on_task_error, Qt.QueuedConnection)
        self._task_signals.finished.connect(self._on_task_finished, Qt.QueuedConnection)

    async def run_async_task(
            self,
            async_func: Callable[..., Awaitable[Any]],
            *args: Any,
            task_id: Optional[str] = None,
            on_result: Optional[Callable[[Any], None]] = None,
            on_error: Optional[Callable[[str, str], None]] = None,
            on_finished: Optional[Callable[[], None]] = None,
            **kwargs: Any
    ) -> str:
        """
        Run an async function as a task and handle the result on the UI thread.

        Args:
            async_func: The async function to run
            args: Positional arguments to pass to the function
            task_id: Optional ID for the task (auto-generated if not provided)
            on_result: Optional callback for when the task completes successfully
            on_error: Optional callback for when the task fails
            on_finished: Optional callback for when the task is done (success or failure)
            kwargs: Keyword arguments to pass to the function

        Returns:
            str: The ID of the task
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        # Store the callbacks
        task_callbacks = {
            'on_result': on_result,
            'on_error': on_error,
            'on_finished': on_finished,
        }

        # Create and start the task
        task = asyncio.create_task(
            self._execute_async_task(async_func, task_id, task_callbacks, *args, **kwargs),
            name=f"ui_task_{task_id}"
        )
        self._running_tasks[task_id] = task

        return task_id

    async def _execute_async_task(
            self,
            async_func: Callable[..., Awaitable[Any]],
            task_id: str,
            callbacks: Dict[str, Optional[Callable]],
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Execute an async task and emit signals with the results.

        Args:
            async_func: The async function to run
            task_id: ID of the task
            callbacks: Dictionary of callbacks to use
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
        """
        self._task_signals.started.emit()

        try:
            # Execute the async function
            result = await async_func(*args, **kwargs)

            # Emit the result signal with the result
            self._task_signals.result_ready.emit({
                'task_id': task_id,
                'result': result,
                'on_result': callbacks.get('on_result'),
            })

        except Exception as e:
            # Get the traceback
            tb = traceback.format_exc()

            # Log the error
            self._logger.error(
                f"Error in async task {task_id}: {e}",
                extra={'task_id': task_id, 'error': str(e), 'traceback': tb},
            )

            # Emit the error signal
            self._task_signals.error.emit(str(e), tb)

        finally:
            # Remove the task from running tasks
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

            # Emit the finished signal
            self._task_signals.finished.emit()

    @Slot(object)
    def _on_task_result(self, result_data: Dict[str, Any]) -> None:
        """
        Handle the result of an async task on the UI thread.

        Args:
            result_data: Dictionary containing task_id, result, and callback
        """
        task_id = result_data.get('task_id')
        result = result_data.get('result')
        on_result = result_data.get('on_result')

        if on_result is not None and callable(on_result):
            try:
                on_result(result)
            except Exception as e:
                self._logger.error(
                    f"Error in result callback for task {task_id}: {e}",
                    extra={'task_id': task_id, 'error': str(e)},
                )

    @Slot(str, str)
    def _on_task_error(self, error_msg: str, traceback_str: str) -> None:
        """
        Handle task errors on the UI thread.

        Args:
            error_msg: The error message
            traceback_str: The traceback string
        """
        on_error = self._running_tasks.get('on_error')
        if on_error is not None and callable(on_error):
            try:
                on_error(error_msg, traceback_str)
            except Exception as e:
                self._logger.error(
                    f"Error in error callback: {e}",
                    extra={'error': str(e)},
                )

    @Slot()
    def _on_task_finished(self) -> None:
        """Handle task completion on the UI thread."""
        on_finished = self._running_tasks.get('on_finished')
        if on_finished is not None and callable(on_finished):
            try:
                on_finished()
            except Exception as e:
                self._logger.error(
                    f"Error in finished callback: {e}",
                    extra={'error': str(e)},
                )

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running async task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            bool: Whether the task was successfully cancelled
        """
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False

    def cancel_all_tasks(self) -> int:
        """
        Cancel all running async tasks.

        Returns:
            int: Number of tasks that were cancelled
        """
        cancelled_count = 0
        for task_id, task in list(self._running_tasks.items()):
            if not task.done():
                task.cancel()
                cancelled_count += 1
        return cancelled_count

    def is_task_running(self, task_id: str) -> bool:
        """
        Check if a task is running.

        Args:
            task_id: ID of the task to check

        Returns:
            bool: Whether the task is running
        """
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            return not task.done()
        return False

    def get_running_tasks_count(self) -> int:
        """
        Get the number of running tasks.

        Returns:
            int: Number of running tasks
        """
        return len([t for t in self._running_tasks.values() if not t.done()])


class AsyncQWidget(QWidget):
    """
    QWidget subclass with async capabilities.

    This class provides a convenient way to create UI widgets that need
    to interact with async code.
    """

    def __init__(self, parent: Optional[QWidget] = None, concurrency_manager: Optional[Any] = None) -> None:
        """
        Initialize AsyncQWidget.

        Args:
            parent: Parent widget
            concurrency_manager: Optional concurrency manager for running tasks
        """
        super().__init__(parent)
        self._async_component = UIComponent(self, concurrency_manager)

    async def run_async_task(
            self,
            async_func: Callable[..., Awaitable[Any]],
            *args: Any,
            task_id: Optional[str] = None,
            on_result: Optional[Callable[[Any], None]] = None,
            on_error: Optional[Callable[[str, str], None]] = None,
            on_finished: Optional[Callable[[], None]] = None,
            **kwargs: Any
    ) -> str:
        """
        Run an async function as a task and handle the result on the UI thread.

        Args:
            async_func: The async function to run
            args: Positional arguments to pass to the function
            task_id: Optional ID for the task (auto-generated if not provided)
            on_result: Optional callback for when the task completes successfully
            on_error: Optional callback for when the task fails
            on_finished: Optional callback for when the task is done (success or failure)
            kwargs: Keyword arguments to pass to the function

        Returns:
            str: The ID of the task
        """
        return await self._async_component.run_async_task(
            async_func, *args,
            task_id=task_id,
            on_result=on_result,
            on_error=on_error,
            on_finished=on_finished,
            **kwargs
        )

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running async task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            bool: Whether the task was successfully cancelled
        """
        return self._async_component.cancel_task(task_id)

    def cancel_all_tasks(self) -> int:
        """
        Cancel all running async tasks.

        Returns:
            int: Number of tasks that were cancelled
        """
        return self._async_component.cancel_all_tasks()

    def closeEvent(self, event: QEvent) -> None:
        """Override of closeEvent to cancel all tasks when the widget is closed."""
        self.cancel_all_tasks()
        super().closeEvent(event)


# Helper function to run a coroutine on the event loop
def run_async(coro: Awaitable[T]) -> T:
    """
    Run a coroutine on the current event loop.

    This is useful for running async code from sync code in the UI.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Create a new event loop if there isn't one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If the loop is already running, create a Future and schedule the coroutine
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    else:
        # Otherwise, just run the coroutine on the loop
        return loop.run_until_complete(coro)


# Type variable for the run_async return type
T = TypeVar('T')