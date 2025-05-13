from __future__ import annotations

import asyncio
import functools
import sys
import threading
from typing import Any, Callable, Dict, Optional, Set, Tuple, TypeVar, cast, Coroutine, Awaitable

from PySide6.QtCore import QObject, Signal, Slot, QTimer, QEventLoop, Qt
from PySide6.QtWidgets import QApplication

T = TypeVar('T')


class QtAsyncBridge(QObject):
    """Bridge between Qt and asyncio event loops.

    This class provides utilities to run async code within Qt applications
    without blocking the UI thread and properly handling task cancellation.
    """

    # Signals
    task_result = Signal(object)
    task_error = Signal(str, str)

    def __init__(self) -> None:
        """Initialize the bridge."""
        super().__init__()

        # Store the main thread ID for thread safety checks
        self._main_thread_id = threading.get_ident()

        # Track running tasks to ensure proper cleanup
        self._running_tasks: Dict[str, asyncio.Task] = {}

        # Setup a timer for processing asyncio events in Qt
        self._setup_event_processor()

    def _setup_event_processor(self) -> None:
        """Setup the event processor to integrate asyncio with Qt event loop."""
        self._event_timer = QTimer()
        self._event_timer.timeout.connect(self._process_events)

        # 5ms is generally a good balance - responsive but not CPU intensive
        self._event_timer.start(5)

    @Slot()
    def _process_events(self) -> None:
        """Process pending asyncio events without blocking Qt."""
        loop = asyncio.get_event_loop()
        loop.call_soon(lambda: None)  # Ensure the loop wakes up

    def run_coroutine(
            self,
            coro: Coroutine[Any, Any, T],
            task_id: Optional[str] = None,
            on_result: Optional[Callable[[T], None]] = None,
            on_error: Optional[Callable[[str, str], None]] = None
    ) -> str:
        """Run a coroutine from the Qt event loop.

        Args:
            coro: The coroutine to run
            task_id: Optional ID for the task (auto-generated if None)
            on_result: Optional callback for the result
            on_error: Optional callback for errors

        Returns:
            The task ID
        """
        if task_id is None:
            import uuid
            task_id = str(uuid.uuid4())

        # Cancel existing task with the same ID if it exists
        if task_id in self._running_tasks and not self._running_tasks[task_id].done():
            self._running_tasks[task_id].cancel()

        # Create callback handlers
        result_handler = on_result or (lambda x: None)
        error_handler = on_error or (lambda e, tb: None)

        # Connect default signals if callbacks are not provided
        if not on_result:
            self.task_result.connect(
                lambda result_data: result_handler(result_data)
                if result_data.get('task_id') == task_id else None
            )

        if not on_error:
            self.task_error.connect(
                lambda err, tb, tid=task_id: error_handler(err, tb)
                if tid == task_id else None
            )

        # Create and store the task
        task = asyncio.create_task(
            self._task_wrapper(coro, task_id, result_handler, error_handler),
            name=f"qt_async_{task_id}"
        )
        self._running_tasks[task_id] = task

        return task_id

    async def _task_wrapper(
            self,
            coro: Coroutine[Any, Any, T],
            task_id: str,
            result_handler: Callable[[T], None],
            error_handler: Callable[[str, str], None]
    ) -> None:
        """Wrap a coroutine with proper error handling and signal emission.

        Args:
            coro: The coroutine to wrap
            task_id: The task ID
            result_handler: Callback for the result
            error_handler: Callback for errors
        """
        try:
            result = await coro

            # Emit result through Qt signal system
            self.task_result.emit({'task_id': task_id, 'result': result})

            # Call the result handler directly
            try:
                result_handler(result)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                self.task_error.emit(str(e), tb)

        except asyncio.CancelledError:
            # Task was cancelled, clean up silently
            pass

        except Exception as e:
            # Handle any other exceptions
            import traceback
            tb = traceback.format_exc()
            self.task_error.emit(str(e), tb)

            try:
                error_handler(str(e), tb)
            except Exception:
                pass  # Prevent cascading errors

        finally:
            # Always clean up the task reference
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task by ID.

        Args:
            task_id: The ID of the task to cancel

        Returns:
            True if the task was found and cancelled, False otherwise
        """
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False

    def cancel_all_tasks(self) -> int:
        """Cancel all running tasks.

        Returns:
            The number of tasks that were cancelled
        """
        cancelled = 0
        for task_id, task in list(self._running_tasks.items()):
            if not task.done():
                task.cancel()
                cancelled += 1
        return cancelled

    def is_main_thread(self) -> bool:
        """Check if the current code is running in the main thread.

        Returns:
            True if in main thread, False otherwise
        """
        return threading.get_ident() == self._main_thread_id

    def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        # Stop the event timer
        if hasattr(self, '_event_timer'):
            self._event_timer.stop()

        # Cancel all tasks
        self.cancel_all_tasks()


# Global instance for convenience
_bridge: Optional[QtAsyncBridge] = None


def get_bridge() -> QtAsyncBridge:
    """Get the global bridge instance, creating it if necessary.

    Returns:
        The QtAsyncBridge instance
    """
    global _bridge

    if _bridge is None:
        _bridge = QtAsyncBridge()

    return _bridge


def run_coroutine(
        coro: Coroutine[Any, Any, T],
        task_id: Optional[str] = None,
        on_result: Optional[Callable[[T], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None
) -> str:
    """Helper function to run a coroutine through the bridge.

    Args:
        coro: The coroutine to run
        task_id: Optional ID for the task (auto-generated if None)
        on_result: Optional callback for the result
        on_error: Optional callback for errors

    Returns:
        The task ID
    """
    bridge = get_bridge()
    return bridge.run_coroutine(coro, task_id, on_result, on_error)


def cancel_task(task_id: str) -> bool:
    """Cancel a task by ID.

    Args:
        task_id: The ID of the task to cancel

    Returns:
        True if the task was cancelled, False otherwise
    """
    bridge = get_bridge()
    return bridge.cancel_task(task_id)


def is_main_thread() -> bool:
    """Check if the current code is running in the main thread.

    Returns:
        True if in main thread, False otherwise
    """
    bridge = get_bridge()
    return bridge.is_main_thread()


def shutdown_bridge() -> None:
    """Shutdown the bridge and cancel all tasks."""
    global _bridge

    if _bridge is not None:
        _bridge.shutdown()
        _bridge = None


def run_until_complete(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine to completion, blocking until it finishes.

    This should only be used for initialization or shutdown tasks,
    not from the UI thread during normal operation.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    if QApplication.instance() and is_main_thread():
        # We're in the Qt main thread, use QEventLoop to avoid blocking UI
        loop = QEventLoop()
        result: Optional[T] = None
        error: Optional[Exception] = None

        def on_done(task: asyncio.Task) -> None:
            nonlocal result, error
            try:
                result = task.result()
            except Exception as e:
                error = e
            finally:
                loop.quit()

        task = asyncio.create_task(coro)
        task.add_done_callback(on_done)

        # Run the event loop until the coroutine is done
        loop.exec()

        if error:
            raise error
        return result
    else:
        # Not in the Qt main thread, use asyncio directly
        return asyncio.run(coro)