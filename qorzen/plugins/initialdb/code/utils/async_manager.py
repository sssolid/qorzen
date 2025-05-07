from __future__ import annotations

"""
Async manager for the InitialDB application.

This module provides robust asynchronous operation management with proper
event loop handling to prevent the "attached to a different loop" errors
that were occurring in the application.
"""

import asyncio
import functools
import inspect
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, cast

import structlog
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

T = TypeVar("T")
logger = structlog.get_logger(__name__)


class AsyncOperationResult:
    """Result of an asynchronous operation."""

    def __init__(self, operation_id: str) -> None:
        self.operation_id = operation_id
        self.is_completed = False
        self.is_error = False
        self.result: Optional[Any] = None
        self.error: Optional[Exception] = None


class AsyncManagerSignals(QObject):
    """Qt signals for async operations."""

    operation_completed = pyqtSignal(str, object)
    operation_failed = pyqtSignal(str, Exception)


class AsyncManager:
    """
    Manages asynchronous operations safely within a PyQt application.

    This class ensures that async operations are executed on the correct
    event loop, preventing the "attached to a different loop" errors.
    """

    _instance: Optional["AsyncManager"] = None
    _lock = threading.RLock()

    @classmethod
    def instance(cls) -> "AsyncManager":
        """Get the singleton instance of the AsyncManager."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = AsyncManager()
            return cls._instance

    def __init__(self) -> None:
        """Initialize the AsyncManager."""
        self._initialized = False
        self._main_thread_id = threading.get_ident()
        self._signals = AsyncManagerSignals()
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread_loops: Dict[int, asyncio.AbstractEventLoop] = {}
        self._operations: Dict[str, asyncio.Future] = {}
        self._thread_executors: Dict[int, ThreadPoolExecutor] = {}
        self._shutting_down = False
        self._initialized = True
        logger.info("AsyncManager initialized")

    def initialize(self) -> None:
        """Initialize the main event loop."""
        if self._main_loop is None:
            try:
                self._main_loop = asyncio.get_event_loop()
            except RuntimeError:
                self._main_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._main_loop)
            logger.debug(f"Main event loop initialized: {id(self._main_loop)}")

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get the appropriate event loop for the current thread.

        Returns:
            An event loop that can be used in the current thread.
        """
        thread_id = threading.get_ident()

        # For the main thread, return the main loop
        if thread_id == self._main_thread_id:
            if self._main_loop is None:
                self.initialize()
            assert self._main_loop is not None
            return self._main_loop

        # For worker threads, get or create a thread-specific loop
        with self._lock:
            if thread_id in self._thread_loops:
                loop = self._thread_loops[thread_id]
                # Make sure the loop is still usable
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    self._thread_loops[thread_id] = loop
            else:
                loop = asyncio.new_event_loop()
                self._thread_loops[thread_id] = loop

            # Set this loop as the current event loop for this thread
            asyncio.set_event_loop(loop)
            return loop

    def get_thread_executor(self) -> ThreadPoolExecutor:
        """Get a thread executor for the current thread."""
        thread_id = threading.get_ident()
        with self._lock:
            if thread_id not in self._thread_executors:
                self._thread_executors[thread_id] = ThreadPoolExecutor(
                    max_workers=4,
                    thread_name_prefix=f"async-worker-{thread_id}-",
                )
            return self._thread_executors[thread_id]

    def run_coroutine(self, coro: Awaitable[T]) -> str:
        """
        Run a coroutine in the appropriate event loop.

        Args:
            coro: The coroutine to run

        Returns:
            The operation ID that can be used to track the operation
        """
        operation_id = str(uuid.uuid4())
        thread_id = threading.get_ident()

        if thread_id == self._main_thread_id:
            self._run_in_main_thread(coro, operation_id)
        else:
            self._run_in_worker_thread(coro, operation_id)

        return operation_id

    def _run_in_main_thread(self, coro: Awaitable[T], operation_id: str) -> None:
        """
        Run a coroutine in the main thread.

        Args:
            coro: The coroutine to run
            operation_id: The operation ID
        """
        if self._main_loop is None:
            self.initialize()
        assert self._main_loop is not None

        loop = self._main_loop

        async def _wrapped_coro() -> T:
            try:
                result = await coro
                self._signals.operation_completed.emit(operation_id, result)
                return result
            except Exception as e:
                logger.error(f"Operation {operation_id} failed: {e}", exc_info=True)
                self._signals.operation_failed.emit(operation_id, e)
                raise

        future = asyncio.run_coroutine_threadsafe(_wrapped_coro(), loop)
        self._operations[operation_id] = future

    def _run_in_worker_thread(self, coro: Awaitable[T], operation_id: str) -> None:
        """
        Run a coroutine in a worker thread.

        Args:
            coro: The coroutine to run
            operation_id: The operation ID
        """
        executor = self.get_thread_executor()

        def _worker() -> None:
            loop = self.get_event_loop()
            try:
                result = loop.run_until_complete(coro)
                # Use QTimer to safely emit signals from non-GUI threads
                QTimer.singleShot(0, lambda: self._signals.operation_completed.emit(operation_id, result))
            except Exception as e:
                logger.error(f"Worker operation {operation_id} failed: {e}", exc_info=True)
                QTimer.singleShot(0, lambda: self._signals.operation_failed.emit(operation_id, e))

        executor.submit(_worker)

    async def wait_for_operation(self, operation_id: str, timeout: float = 60.0) -> Any:
        """
        Wait for an operation to complete.

        Args:
            operation_id: The operation ID to wait for
            timeout: Maximum time to wait in seconds (increased from 30.0 to 60.0)

        Returns:
            The result of the operation

        Raises:
            asyncio.TimeoutError: If the operation times out
            Exception: Any exception raised by the operation
        """
        loop = self.get_event_loop()
        future = asyncio.Future()

        def on_completed(op_id: str, result: Any) -> None:
            if op_id == operation_id and not future.done():
                future.set_result(result)

        def on_failed(op_id: str, error: Exception) -> None:
            if op_id == operation_id and not future.done():
                future.set_exception(error)

        # Connect signals
        self._signals.operation_completed.connect(on_completed)
        self._signals.operation_failed.connect(on_failed)

        try:
            # Check if the operation is already completed
            if operation_id in self._operations and self._operations[operation_id].done():
                try:
                    return self._operations[operation_id].result()
                except Exception as e:
                    # If the operation failed, raise the exception
                    raise e

            # Wait for the operation with an increased timeout
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            logger.error(f"Operation {operation_id} timed out after {timeout} seconds")
            # Cancel the operation if it's still running
            self.cancel_operation(operation_id)
            # Re-raise with more context
            raise asyncio.TimeoutError(f"Operation {operation_id} timed out after {timeout} seconds") from None
        finally:
            # Disconnect signals
            try:
                self._signals.operation_completed.disconnect(on_completed)
                self._signals.operation_failed.disconnect(on_failed)
            except Exception:
                pass

    def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel an operation.

        Args:
            operation_id: The operation ID to cancel

        Returns:
            True if the operation was cancelled, False otherwise
        """
        if operation_id in self._operations:
            future = self._operations[operation_id]
            if not future.done():
                future.cancel()
                return True
        return False

    def connect_operation_signals(
            self,
            on_completed: Callable[[str, Any], None],
            on_failed: Callable[[str, Exception], None]
    ) -> None:
        """
        Connect operation signals.

        Args:
            on_completed: Function to call when an operation completes
            on_failed: Function to call when an operation fails
        """
        self._signals.operation_completed.connect(on_completed)
        self._signals.operation_failed.connect(on_failed)

    def disconnect_operation_signals(
            self,
            on_completed: Optional[Callable[[str, Any], None]] = None,
            on_failed: Optional[Callable[[str, Exception], None]] = None
    ) -> None:
        """
        Disconnect operation signals.

        Args:
            on_completed: Function previously connected to operation_completed
            on_failed: Function previously connected to operation_failed
        """
        if on_completed:
            try:
                self._signals.operation_completed.disconnect(on_completed)
            except (TypeError, RuntimeError):
                pass

        if on_failed:
            try:
                self._signals.operation_failed.disconnect(on_failed)
            except (TypeError, RuntimeError):
                pass

    def cleanup(self) -> None:
        """Clean up resources used by the AsyncManager."""
        if self._shutting_down:
            return

        self._shutting_down = True
        logger.info("Cleaning up AsyncManager")

        # Cancel all pending operations
        for operation_id, future in list(self._operations.items()):
            if not future.done():
                future.cancel()
        self._operations.clear()

        # Shut down all thread executors
        for executor in self._thread_executors.values():
            executor.shutdown(wait=False)
        self._thread_executors.clear()

        # Close all thread-specific event loops
        for thread_id, loop in list(self._thread_loops.items()):
            if not loop.is_closed():
                try:
                    if not loop.is_running():
                        loop.close()
                except Exception as e:
                    logger.error(f"Error closing thread loop: {e}")
        self._thread_loops.clear()

        # Close the main event loop if we own it
        if self._main_loop and not self._main_loop.is_closed():
            try:
                if not self._main_loop.is_running():
                    self._main_loop.close()
            except Exception as e:
                logger.error(f"Error closing main loop: {e}")

        logger.info("AsyncManager cleaned up")


def async_operation(func: Callable[..., Awaitable[T]]) -> Callable[..., str]:
    """
    Decorator for asynchronous operations.

    Args:
        func: The coroutine function to decorate

    Returns:
        A function that runs the coroutine and returns an operation ID
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        coro = func(*args, **kwargs)
        return AsyncManager.instance().run_coroutine(coro)

    return wrapper


class AsyncSlot:
    """
    Descriptor for async slot methods in PyQt.

    This allows class methods to be used as Qt slots while running async code.
    """

    def __init__(self, slot_function: Callable[..., Awaitable[Any]]) -> None:
        self.slot_function = slot_function
        functools.update_wrapper(self, slot_function)

    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Callable[..., None]:
        if obj is None:
            return self

        @functools.wraps(self.slot_function)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            try:
                coro = self.slot_function(obj, *args, **kwargs)
                AsyncManager.instance().run_coroutine(coro)
            except Exception as e:
                logger.error(f"Error in async slot {self.slot_function.__name__}: {e}", exc_info=True)

        return wrapper


def async_slot(func: Callable[..., Awaitable[Any]]) -> AsyncSlot:
    """
    Decorator for async slot methods.

    Args:
        func: The coroutine function to use as a slot

    Returns:
        An AsyncSlot descriptor
    """
    return AsyncSlot(func)