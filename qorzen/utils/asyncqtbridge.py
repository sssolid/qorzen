from __future__ import annotations

import asyncio
import functools
import threading
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, cast, Generic

from PySide6.QtCore import QObject, Signal, Slot, QMetaObject, Qt, Q_ARG

T = TypeVar('T')
U = TypeVar('U')


class AsyncQtBridge(QObject, Generic[T, U]):
    """
    Bridge class to safely execute async coroutines and update Qt UI.

    This class provides a safe way to execute async coroutines in a background thread
    and then update Qt UI components on the main thread. It handles the thread transitions
    and properly marshals results or exceptions back to the main thread.

    Generic parameters:
        T: The result type of the async operation
        U: The progress update type

    Signals:
        resultReady: Emitted when the async operation completes successfully
        errorOccurred: Emitted when the async operation fails with an exception
        progressUpdated: Emitted to report progress during the async operation
    """

    resultReady = Signal(object)  # T
    errorOccurred = Signal(str)  # Exception message
    progressUpdated = Signal(object)  # U

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Initialize the AsyncQtBridge.

        Args:
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._current_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

    def execute(
            self,
            coro_func: Callable[..., Awaitable[T]],
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Execute an async coroutine function in a background thread.

        The result or exception will be properly marshaled back to the
        main Qt thread via signals.

        Args:
            coro_func: The coroutine function to execute
            *args: Positional arguments to pass to the coroutine function
            **kwargs: Keyword arguments to pass to the coroutine function
        """
        with self._lock:
            if self._running:
                raise RuntimeError("AsyncQtBridge is already running a task")

            self._running = True

        # Start a new thread for the asyncio event loop
        self._thread = threading.Thread(
            target=self._run_async_task,
            args=(coro_func, args, kwargs),
            daemon=True,
            name=f"AsyncQtBridge-{id(self)}"
        )
        self._thread.start()

    def _run_async_task(
            self,
            coro_func: Callable[..., Awaitable[T]],
            args: tuple,
            kwargs: dict
    ) -> None:
        """
        Run the async task in a dedicated thread with its own event loop.

        Args:
            coro_func: The coroutine function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
        """
        try:
            # Create a new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # Create and run the coroutine
            coro = coro_func(*args, **kwargs)
            self._current_task = self._loop.create_task(coro)

            # Add done callback to handle result or exception
            self._current_task.add_done_callback(self._on_task_done)

            # Run the event loop until the task completes
            self._loop.run_until_complete(self._current_task)
        except Exception as e:
            # Handle any unexpected exceptions in the task execution
            self.errorOccurred.emit(str(e))
        finally:
            # Clean up resources
            if self._loop:
                self._loop.close()
                self._loop = None

            self._current_task = None
            with self._lock:
                self._running = False

    def _on_task_done(self, task: asyncio.Task) -> None:
        """
        Handle task completion.

        This is called when the task completes, either successfully or with an exception.
        It will emit the appropriate signal based on the outcome.

        Args:
            task: The completed asyncio.Task
        """
        try:
            # Get the result (will raise exception if the task failed)
            result = task.result()
            # Emit the result signal
            self.resultReady.emit(result)
        except asyncio.CancelledError:
            # Task was cancelled
            self.errorOccurred.emit("Task was cancelled")
        except Exception as e:
            # Task failed with an exception
            self.errorOccurred.emit(str(e))

    def cancel(self) -> bool:
        """
        Cancel the currently running task.

        Returns:
            bool: True if a task was cancelled, False otherwise
        """
        with self._lock:
            if not self._running or not self._current_task or not self._loop:
                return False

            if self._current_task.done():
                return False

            self._current_task.cancel()
            return True

    def is_running(self) -> bool:
        """
        Check if the bridge is currently running a task.

        Returns:
            bool: True if a task is running, False otherwise
        """
        with self._lock:
            return self._running

    def update_progress(self, progress: U) -> None:
        """
        Update progress from within the async operation.

        This can be called from the async coroutine to report progress back to the UI.

        Args:
            progress: The progress data to report
        """
        self.progressUpdated.emit(progress)


class AsyncQtHelper:
    """
    Helper class with static methods for async-Qt integration.
    """

    @staticmethod
    def run_in_main_thread(
            target_object: QObject,
            method_name: str,
            *args: Any,
            connection_type: Qt.ConnectionType = Qt.ConnectionType.QueuedConnection
    ) -> None:
        """
        Run a method on a QObject in the main Qt thread.

        Args:
            target_object: The QObject instance that owns the method
            method_name: The name of the method to call
            *args: Arguments to pass to the method
            connection_type: The Qt connection type to use (default: QueuedConnection)
        """
        q_args = [Q_ARG(type(arg), arg) for arg in args]
        QMetaObject.invokeMethod(
            target_object,
            method_name,
            connection_type,
            *q_args
        )

    @staticmethod
    def create_bridge_for_method(
            target_object: QObject,
            method_name: str,
            error_method: Optional[str] = None,
            progress_method: Optional[str] = None
    ) -> AsyncQtBridge:
        """
        Create an AsyncQtBridge and connect it to methods on a target object.

        This is a convenience method to create a bridge and connect its signals
        to methods on a target object.

        Args:
            target_object: The QObject that will receive the results
            method_name: The method to call with the result
            error_method: Optional method to call on error
            progress_method: Optional method to call for progress updates

        Returns:
            AsyncQtBridge: A configured bridge instance
        """
        bridge = AsyncQtBridge(target_object)

        # Connect the result signal
        bridge.resultReady.connect(
            getattr(target_object, method_name)
        )

        # Connect the error signal if provided
        if error_method:
            bridge.errorOccurred.connect(
                getattr(target_object, error_method)
            )

        # Connect the progress signal if provided
        if progress_method:
            bridge.progressUpdated.connect(
                getattr(target_object, progress_method)
            )

        return bridge


# Example usage

class ExampleWidget(QObject):
    """Example showing how to use the AsyncQtBridge."""

    def __init__(self) -> None:
        super().__init__()

        # Create a bridge for a specific task
        self.search_bridge = AsyncQtHelper.create_bridge_for_method(
            self,
            '_on_search_complete',
            '_on_search_error',
            '_on_search_progress'
        )

    def start_search(self, query: str) -> None:
        """Start an async search operation."""
        self.search_bridge.execute(self._perform_search, query)

    async def _perform_search(self, query: str) -> list[str]:
        """Perform an async search operation."""
        # Simulate an async operation
        await asyncio.sleep(1)

        # Update progress
        self.search_bridge.update_progress("Searching...")

        await asyncio.sleep(1)

        # Return results
        return [f"{query} result {i}" for i in range(5)]

    @Slot(object)
    def _on_search_complete(self, results: list[str]) -> None:
        """Handle search results in the main thread."""
        print("Search complete with results:", results)

    @Slot(str)
    def _on_search_error(self, error: str) -> None:
        """Handle search errors in the main thread."""
        print("Search error:", error)

    @Slot(object)
    def _on_search_progress(self, progress: str) -> None:
        """Handle search progress updates in the main thread."""
        print("Search progress:", progress)