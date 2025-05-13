from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union, cast, Awaitable

from PySide6.QtCore import QObject, Signal, Slot, Qt, QEvent
from PySide6.QtWidgets import QWidget


class AsyncTaskSignals(QObject):
    """Signal class for handling asynchronous task results in Qt."""

    started = Signal()
    result_ready = Signal(object)
    error = Signal(str, str)
    finished = Signal()


class AsyncQWidget(QWidget):
    """
    A QWidget with built-in async support.

    This widget makes it easier to run async operations and interact with
    the widget from asynchronous code. It wraps the complexity of dealing
    with Qt's thread model when using async/await.
    """

    def __init__(self, parent: Optional[QWidget] = None, concurrency_manager: Optional[Any] = None) -> None:
        """
        Initialize AsyncQWidget.

        Args:
            parent: Parent widget
            concurrency_manager: Optional concurrency manager for thread handling
        """
        super().__init__(parent)

        # Set up async task handling
        self._signals = AsyncTaskSignals()
        self._signals.result_ready.connect(self._on_task_result, Qt.QueuedConnection)
        self._signals.error.connect(self._on_task_error, Qt.QueuedConnection)
        self._signals.finished.connect(self._on_task_finished, Qt.QueuedConnection)

        # For logging
        self._logger = logging.getLogger(f"ui.async.{self.__class__.__name__}")

        # Running task tracking
        self._running_tasks: Dict[str, asyncio.Task] = {}

        # Keep a reference to the concurrency manager if provided
        self._concurrency_manager = concurrency_manager

    async def run_async_task(
            self,
            coroutine_func: Callable[..., Awaitable[Any]],
            *args: Any,
            task_id: Optional[str] = None,
            on_result: Optional[Callable[[Any], None]] = None,
            on_error: Optional[Callable[[str, str], None]] = None,
            on_finished: Optional[Callable[[], None]] = None,
            **kwargs: Any
    ) -> str:
        """
        Run an asynchronous task and handle the result with callbacks.

        Args:
            coroutine_func: Async function to run
            *args: Positional arguments to pass to the function
            task_id: Optional task identifier (generated if not provided)
            on_result: Optional callback for successful result
            on_error: Optional callback for error handling
            on_finished: Optional callback when task completes (success or failure)
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Task identifier
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        # Create a dictionary of callbacks
        callbacks = {
            "on_result": on_result,
            "on_error": on_error,
            "on_finished": on_finished
        }

        # Start the task
        task = asyncio.create_task(
            self._execute_async_task(coroutine_func, task_id, callbacks, *args, **kwargs),
            name=f"ui_task_{task_id}"
        )
        self._running_tasks[task_id] = task

        return task_id

    async def _execute_async_task(
            self,
            coroutine_func: Callable[..., Awaitable[Any]],
            task_id: str,
            callbacks: Dict[str, Optional[Callable]],
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Execute an async task and emit appropriate signals.

        Args:
            coroutine_func: Async function to execute
            task_id: Task identifier
            callbacks: Dictionary of callback functions
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        self._signals.started.emit()

        try:
            # Execute the coroutine
            result = await coroutine_func(*args, **kwargs)

            # Emit success signal with result and callback
            self._signals.result_ready.emit({
                "task_id": task_id,
                "result": result,
                "on_result": callbacks.get("on_result")
            })
        except asyncio.CancelledError:
            # Task was cancelled, don't emit error
            pass
        except Exception as e:
            # Get traceback
            tb = traceback.format_exc()

            # Log the error
            self._logger.error(
                f"Error in async task {task_id}: {e}",
                extra={"task_id": task_id, "error": str(e), "traceback": tb}
            )

            # Emit error signal
            self._signals.error.emit(str(e), tb)

            # Call error callback if provided
            error_callback = callbacks.get("on_error")
            if error_callback and callable(error_callback):
                try:
                    error_callback(str(e), tb)
                except Exception as callback_error:
                    self._logger.error(
                        f"Error in error callback: {callback_error}",
                        extra={"error": str(callback_error)}
                    )
        finally:
            # Clean up task reference
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

            # Emit finished signal
            self._signals.finished.emit()

            # Call finished callback if provided
            finished_callback = callbacks.get("on_finished")
            if finished_callback and callable(finished_callback):
                try:
                    finished_callback()
                except Exception as callback_error:
                    self._logger.error(
                        f"Error in finished callback: {callback_error}",
                        extra={"error": str(callback_error)}
                    )

    @Slot(object)
    def _on_task_result(self, result_data: Dict[str, Any]) -> None:
        """
        Handle a successful task result.

        Args:
            result_data: Dictionary containing task result data
        """
        task_id = result_data.get("task_id")
        result = result_data.get("result")
        on_result = result_data.get("on_result")

        if on_result is not None and callable(on_result):
            try:
                on_result(result)
            except Exception as e:
                self._logger.error(
                    f"Error in result callback for task {task_id}: {e}",
                    extra={"task_id": task_id, "error": str(e)}
                )

    @Slot(str, str)
    def _on_task_error(self, error_msg: str, traceback_str: str) -> None:
        """
        Handle a task error.

        Args:
            error_msg: Error message
            traceback_str: Formatted traceback
        """
        # Base implementation doesn't do anything beyond what's handled in _execute_async_task
        # Subclasses can override this for additional error handling
        pass

    @Slot()
    def _on_task_finished(self) -> None:
        """Handle task completion."""
        # Base implementation doesn't do anything beyond what's handled in _execute_async_task
        # Subclasses can override this for additional finish handling
        pass

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: Task identifier

        Returns:
            True if the task was cancelled, False if it was not found or already done
        """
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False

    def cancel_all_tasks(self) -> int:
        """
        Cancel all running tasks.

        Returns:
            Number of tasks cancelled
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
            task_id: Task identifier

        Returns:
            True if the task is running, False otherwise
        """
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            return not task.done()
        return False

    def get_running_tasks_count(self) -> int:
        """
        Get the number of currently running tasks.

        Returns:
            Number of running tasks
        """
        return len([t for t in self._running_tasks.values() if not t.done()])

    def closeEvent(self, event: QEvent) -> None:
        """
        Handle the close event by cancelling all running tasks.

        Args:
            event: Close event
        """
        self.cancel_all_tasks()
        super().closeEvent(event)


T = TypeVar('T')


def run_async(coro: Awaitable[T]) -> T:
    """
    Run an async coroutine from synchronous code.

    Args:
        coro: Coroutine to run

    Returns:
        Result of the coroutine
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    else:
        return loop.run_until_complete(coro)