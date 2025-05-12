# qorzen/core/thread_safe_core.py
from __future__ import annotations

import asyncio
import functools
import inspect
import queue
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union, cast

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt, QMetaObject, QTimer, QEvent
from PySide6.QtWidgets import QWidget, QApplication

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class ThreadType(Enum):
    """Thread types supported by the system."""
    MAIN = auto()  # Qt main thread (UI thread)
    WORKER = auto()  # Background worker thread
    IO = auto()  # I/O-bound operations thread
    CURRENT = auto()  # Whatever thread is currently running


class ThreadBridge(QObject):
    """Bridge between threads using Qt signals for safe execution."""

    # Signal to execute a function on the main thread
    execute_signal = Signal(object, tuple, dict, object)

    def __init__(self) -> None:
        """Initialize the thread bridge."""
        super().__init__()
        # Connect signal to slot using queued connection to ensure thread safety
        self.execute_signal.connect(
            self._execute_on_main,
            type=Qt.ConnectionType.QueuedConnection
        )
        self._main_thread_id = threading.get_ident()

    def is_main_thread(self) -> bool:
        """Check if current thread is the main thread."""
        return threading.get_ident() == self._main_thread_id

    def execute_on_main(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> Optional[T]:
        """
        Execute function on the main thread.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result if waited, None otherwise
        """
        if self.is_main_thread():
            # Already on main thread, execute directly
            return func(*args, **kwargs)

        # Need thread-safe execution
        result_container: List[Any] = [None]
        error_container: List[Optional[Exception]] = [None]
        event = threading.Event()

        def wrapper() -> None:
            try:
                result_container[0] = func(*args, **kwargs)
            except Exception as e:
                error_container[0] = e
            finally:
                event.set()

        # Emit signal to execute on main thread
        self.execute_signal.emit(wrapper, (), {}, None)

        # Wait for completion
        event.wait()

        # Check for error
        if error_container[0] is not None:
            raise error_container[0]

        return result_container[0]

    def execute_on_main_async(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Execute function on main thread without waiting for result.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        if self.is_main_thread():
            # Already on main thread, execute directly
            func(*args, **kwargs)
            return

        # Need thread-safe execution without waiting
        self.execute_signal.emit(func, args, kwargs, None)

    @Slot(object, tuple, dict, object)
    def _execute_on_main(self, func: Callable, args: tuple, kwargs: dict,
                         callback_event: Optional[threading.Event]) -> None:
        """Execute function on the main thread (slot implementation)."""
        try:
            func(*args, **kwargs)
        except Exception:
            traceback.print_exc()
        finally:
            if callback_event:
                callback_event.set()


# Global thread bridge instance
_THREAD_BRIDGE = ThreadBridge()


def run_on_main_thread(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to ensure a function runs on the main Qt thread.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that always runs on main thread
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return _THREAD_BRIDGE.execute_on_main(func, *args, **kwargs)

    return wrapper


def is_qt_object(obj: Any) -> bool:
    """
    Check if an object is a Qt object that should run on the main thread.

    Args:
        obj: Object to check

    Returns:
        True if object is a Qt object requiring main thread
    """
    return (isinstance(obj, (QObject, QWidget)) or
            hasattr(obj, 'metaObject') or
            hasattr(obj, 'pyqtSignal') or
            hasattr(obj, 'pyqtSlot'))


class ThreadSafeProxy:
    """
    Proxy that ensures Qt object methods are called on the main thread.
    """

    def __init__(self, target: Any) -> None:
        """
        Initialize with target Qt object.

        Args:
            target: Qt object to proxy
        """
        self._target = target

    def __getattr__(self, name: str) -> Any:
        """
        Get attribute from target, ensuring methods run on main thread.

        Args:
            name: Attribute name

        Returns:
            Attribute or thread-safe wrapper for methods
        """
        attr = getattr(self._target, name)

        # If it's a callable, ensure it runs on main thread
        if callable(attr) and not name.startswith('_'):
            @functools.wraps(attr)
            def thread_safe_method(*args: Any, **kwargs: Any) -> Any:
                return _THREAD_BRIDGE.execute_on_main(attr, *args, **kwargs)

            return thread_safe_method

        # Return attribute directly (possibly wrapping Qt objects)
        if is_qt_object(attr):
            return ThreadSafeProxy(attr)
        return attr

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ThreadSafeProxy({self._target!r})"

    def unwrap(self) -> Any:
        """Unwrap the proxy to get the original object."""
        return self._target


def ensure_main_thread(obj: T) -> Union[T, ThreadSafeProxy]:
    """
    Ensure object is safe to use by possibly creating a proxy.

    Args:
        obj: Object to check

    Returns:
        Original object or thread-safe proxy
    """
    if is_qt_object(obj):
        return ThreadSafeProxy(obj)
    return obj


# Task execution components
class TaskStatus(str, Enum):
    """Status of task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Priority levels for tasks."""
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


@dataclass
class ProgressReporter:
    """Thread-safe progress reporting for tasks."""

    task_id: str
    update_callback: Callable[[str, int, Optional[str]], None]

    def report_progress(self, percent: int, message: Optional[str] = None) -> None:
        """
        Report task progress.

        Args:
            percent: Progress percentage (0-100)
            message: Optional progress message
        """
        # Always ensure callback runs on main thread
        _THREAD_BRIDGE.execute_on_main_async(
            self.update_callback,
            self.task_id,
            percent,
            message
        )


class TaskBridge(QObject):
    """Bridge for task events using Qt signals."""

    # Task-related signals
    task_progress = Signal(str, int, str)  # task_id, percent, message
    task_completed = Signal(str, object)  # task_id, result
    task_failed = Signal(str, str, str)  # task_id, error_message, traceback
    task_cancelled = Signal(str)  # task_id

    def __init__(self) -> None:
        """Initialize task bridge."""
        super().__init__()

        # Connect signals to main thread slots using queued connections
        self.task_progress.connect(self._on_task_progress,
                                   type=Qt.ConnectionType.QueuedConnection)
        self.task_completed.connect(self._on_task_completed,
                                    type=Qt.ConnectionType.QueuedConnection)
        self.task_failed.connect(self._on_task_failed,
                                 type=Qt.ConnectionType.QueuedConnection)
        self.task_cancelled.connect(self._on_task_cancelled,
                                    type=Qt.ConnectionType.QueuedConnection)

        # Callbacks registered by task manager
        self._progress_callbacks: Dict[str, List[Callable[[str, int, str], None]]] = {}
        self._completion_callbacks: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._failure_callbacks: Dict[str, List[Callable[[str, str, str], None]]] = {}
        self._cancellation_callbacks: Dict[str, List[Callable[[str], None]]] = {}
        self._lock = threading.RLock()

    def register_callbacks(self,
                           task_id: str,
                           on_progress: Optional[Callable[[str, int, str], None]] = None,
                           on_completed: Optional[Callable[[str, Any], None]] = None,
                           on_failed: Optional[Callable[[str, str, str], None]] = None,
                           on_cancelled: Optional[Callable[[str], None]] = None) -> None:
        """
        Register callbacks for a task.

        Args:
            task_id: Task identifier
            on_progress: Progress callback
            on_completed: Completion callback
            on_failed: Failure callback
            on_cancelled: Cancellation callback
        """
        with self._lock:
            if on_progress:
                if task_id not in self._progress_callbacks:
                    self._progress_callbacks[task_id] = []
                self._progress_callbacks[task_id].append(on_progress)

            if on_completed:
                if task_id not in self._completion_callbacks:
                    self._completion_callbacks[task_id] = []
                self._completion_callbacks[task_id].append(on_completed)

            if on_failed:
                if task_id not in self._failure_callbacks:
                    self._failure_callbacks[task_id] = []
                self._failure_callbacks[task_id].append(on_failed)

            if on_cancelled:
                if task_id not in self._cancellation_callbacks:
                    self._cancellation_callbacks[task_id] = []
                self._cancellation_callbacks[task_id].append(on_cancelled)

    def unregister_callbacks(self, task_id: str) -> None:
        """
        Unregister all callbacks for a task.

        Args:
            task_id: Task identifier
        """
        with self._lock:
            if task_id in self._progress_callbacks:
                del self._progress_callbacks[task_id]
            if task_id in self._completion_callbacks:
                del self._completion_callbacks[task_id]
            if task_id in self._failure_callbacks:
                del self._failure_callbacks[task_id]
            if task_id in self._cancellation_callbacks:
                del self._cancellation_callbacks[task_id]

    @Slot(str, int, str)
    def _on_task_progress(self, task_id: str, percent: int, message: str) -> None:
        """Handle task progress signal."""
        with self._lock:
            if task_id in self._progress_callbacks:
                for callback in self._progress_callbacks[task_id]:
                    try:
                        callback(task_id, percent, message)
                    except Exception:
                        traceback.print_exc()

    @Slot(str, object)
    def _on_task_completed(self, task_id: str, result: Any) -> None:
        """Handle task completion signal."""
        with self._lock:
            if task_id in self._completion_callbacks:
                for callback in self._completion_callbacks[task_id]:
                    try:
                        callback(task_id, result)
                    except Exception:
                        traceback.print_exc()
            self.unregister_callbacks(task_id)

    @Slot(str, str, str)
    def _on_task_failed(self, task_id: str, error_message: str,
                        error_traceback: str) -> None:
        """Handle task failure signal."""
        with self._lock:
            if task_id in self._failure_callbacks:
                for callback in self._failure_callbacks[task_id]:
                    try:
                        callback(task_id, error_message, error_traceback)
                    except Exception:
                        traceback.print_exc()
            self.unregister_callbacks(task_id)

    @Slot(str)
    def _on_task_cancelled(self, task_id: str) -> None:
        """Handle task cancellation signal."""
        with self._lock:
            if task_id in self._cancellation_callbacks:
                for callback in self._cancellation_callbacks[task_id]:
                    try:
                        callback(task_id)
                    except Exception:
                        traceback.print_exc()
            self.unregister_callbacks(task_id)


# Global task bridge instance
_TASK_BRIDGE = TaskBridge()


class ThreadDispatcher:
    """
    Central dispatcher for thread management and task execution.
    Ensures code runs on appropriate threads and provides task scheduling.
    """
    _instance: Optional[ThreadDispatcher] = None

    @classmethod
    def instance(cls) -> ThreadDispatcher:
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ThreadDispatcher()
        return cls._instance

    def __init__(self) -> None:
        """Initialize thread dispatcher."""
        self._thread_bridge = _THREAD_BRIDGE
        self._task_bridge = _TASK_BRIDGE
        self._main_thread_id = threading.get_ident()

        # Thread pools
        self._worker_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="worker")
        self._io_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="io")

        # Task tracking
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._tasks_lock = threading.RLock()

        # Cancellation tracking
        self._futures: Dict[str, 'Future'] = {}
        self._futures_lock = threading.RLock()

    def is_main_thread(self) -> bool:
        """Check if current thread is the main thread."""
        return threading.get_ident() == self._main_thread_id

    def execute_on_thread(self,
                          func: Callable[..., T],
                          thread_type: ThreadType,
                          *args: Any,
                          task_id: Optional[str] = None,
                          **kwargs: Any) -> 'Future[T]':
        """
        Execute function on specified thread type.

        Args:
            func: Function to execute
            thread_type: Type of thread to run on
            *args: Function arguments
            task_id: Optional task identifier
            **kwargs: Function keyword arguments

        Returns:
            Future representing pending result
        """
        from concurrent.futures import Future

        # Execute in current thread if requested
        if thread_type == ThreadType.CURRENT:
            future: Future = Future()
            try:
                result = func(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            return future

        # Execute on main thread if requested
        elif thread_type == ThreadType.MAIN:
            future = Future()

            # If already on main thread, execute directly
            if self.is_main_thread():
                try:
                    result = func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
            else:
                # Need to execute on main thread
                def main_thread_wrapper() -> None:
                    try:
                        result = func(*args, **kwargs)
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)

                self._thread_bridge.execute_on_main_async(main_thread_wrapper)

            return future

        # Execute on worker thread
        elif thread_type == ThreadType.WORKER:
            future = self._worker_pool.submit(func, *args, **kwargs)

        # Execute on IO thread
        elif thread_type == ThreadType.IO:
            future = self._io_pool.submit(func, *args, **kwargs)

        else:
            raise ValueError(f"Unknown thread type: {thread_type}")

        # Track future if task_id provided
        if task_id:
            with self._futures_lock:
                self._futures[task_id] = future

        return future

    def submit_task(self,
                    func: Callable[..., T],
                    *args: Any,
                    task_id: Optional[str] = None,
                    on_ui_thread: bool = False,
                    has_progress: bool = True,
                    on_completed: Optional[Callable[[str, T], None]] = None,
                    on_failed: Optional[Callable[[str, str, str], None]] = None,
                    on_cancelled: Optional[Callable[[str], None]] = None,
                    **kwargs: Any) -> str:
        """
        Submit a task for execution with proper thread management.

        Args:
            func: Task function
            *args: Function arguments
            task_id: Optional task ID
            on_ui_thread: Whether to run on UI thread
            has_progress: Whether task reports progress
            on_completed: Completion callback
            on_failed: Failure callback
            on_cancelled: Cancellation callback
            **kwargs: Function keyword arguments

        Returns:
            Task identifier
        """
        task_id = task_id or str(uuid.uuid4())

        # Create progress reporter if needed
        progress_reporter = None
        if has_progress:
            def update_progress(task_id: str,
                                percent: int,
                                message: Optional[str]) -> None:
                self._task_bridge.task_progress.emit(
                    task_id,
                    percent,
                    message or ""
                )

            progress_reporter = ProgressReporter(
                task_id=task_id,
                update_callback=update_progress
            )

        # Register callbacks
        self._task_bridge.register_callbacks(
            task_id,
            None,  # Progress handled through reporter
            on_completed,
            on_failed,
            on_cancelled
        )

        # Keep track of the task
        with self._tasks_lock:
            self._tasks[task_id] = {
                "id": task_id,
                "start_time": time.time(),
                "status": TaskStatus.PENDING,
                "on_ui_thread": on_ui_thread,
                "has_progress": has_progress
            }

        # Create task wrapper
        def task_wrapper() -> T:
            try:
                with self._tasks_lock:
                    if task_id in self._tasks:
                        self._tasks[task_id]["status"] = TaskStatus.RUNNING

                # Execute task function with progress reporter if needed
                if progress_reporter and has_progress:
                    if "progress_reporter" in inspect.signature(func).parameters:
                        result = func(*args, progress_reporter=progress_reporter, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                with self._tasks_lock:
                    if task_id in self._tasks:
                        self._tasks[task_id]["status"] = TaskStatus.COMPLETED
                        self._tasks[task_id]["end_time"] = time.time()

                # Signal completion
                self._task_bridge.task_completed.emit(task_id, result)
                return result

            except Exception as e:
                tb_str = traceback.format_exc()

                with self._tasks_lock:
                    if task_id in self._tasks:
                        self._tasks[task_id]["status"] = TaskStatus.FAILED
                        self._tasks[task_id]["error"] = str(e)
                        self._tasks[task_id]["traceback"] = tb_str
                        self._tasks[task_id]["end_time"] = time.time()

                # Signal failure
                self._task_bridge.task_failed.emit(
                    task_id,
                    str(e),
                    tb_str
                )
                raise
            finally:
                # Clean up tracking
                with self._futures_lock:
                    if task_id in self._futures:
                        del self._futures[task_id]

        # Determine thread type
        thread_type = ThreadType.MAIN if on_ui_thread else ThreadType.WORKER

        # Execute the task
        future = self.execute_on_thread(
            task_wrapper,
            thread_type=thread_type,
            task_id=task_id
        )

        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: Task to cancel

        Returns:
            Whether cancellation was successful
        """
        with self._tasks_lock:
            if task_id not in self._tasks:
                return False

            task_info = self._tasks[task_id]
            if task_info["status"] not in (TaskStatus.PENDING, TaskStatus.RUNNING):
                return False

            task_info["status"] = TaskStatus.CANCELLED
            task_info["end_time"] = time.time()

        # Cancel future if available
        cancelled = False
        with self._futures_lock:
            if task_id in self._futures:
                future = self._futures[task_id]
                cancelled = future.cancel()
                del self._futures[task_id]

        # Signal cancellation
        if cancelled:
            self._task_bridge.task_cancelled.emit(task_id)

        return cancelled

    def shutdown(self) -> None:
        """Shutdown the thread dispatcher."""
        # Cancel all tasks
        with self._tasks_lock:
            for task_id in list(self._tasks.keys()):
                self.cancel_task(task_id)

        # Shutdown thread pools
        self._worker_pool.shutdown(wait=True, cancel_futures=True)
        self._io_pool.shutdown(wait=True, cancel_futures=True)


# ThreadPoolExecutor implementation with features matching standard library
class ThreadPoolExecutor:
    """Thread pool executor that matches the interface of concurrent.futures."""

    def __init__(self, max_workers: int = None, thread_name_prefix: str = "") -> None:
        """
        Initialize thread pool.

        Args:
            max_workers: Maximum number of worker threads
            thread_name_prefix: Prefix for thread names
        """
        self._max_workers = max_workers or (max(32, (os.cpu_count() or 1) + 4))
        self._thread_name_prefix = thread_name_prefix
        self._shutdown = False
        self._shutdown_lock = threading.RLock()
        self._threads: Set[threading.Thread] = set()
        self._work_queue: queue.Queue = queue.Queue()
        self._thread_count = 0
        self._thread_name_counter = 0

    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> 'Future[T]':
        """
        Submit a callable for execution.

        Args:
            fn: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Future representing pending completion
        """
        from concurrent.futures import Future

        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')

            future = Future()

            # Create work item
            def work_item() -> None:
                if not future.set_running_or_notify_cancel():
                    return

                try:
                    result = fn(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)

            # Put work item in queue
            self._work_queue.put(work_item)

            # Ensure we have enough threads
            self._adjust_thread_count()

            return future

    def _adjust_thread_count(self) -> None:
        """Adjust thread count based on queue size."""
        # If we need more threads and haven't hit the limit, create them
        if (self._thread_count < self._max_workers and
                self._work_queue.qsize() > self._thread_count):
            # Create new thread
            thread_name = f"{self._thread_name_prefix}-{self._thread_name_counter}"
            self._thread_name_counter += 1

            thread = threading.Thread(
                name=thread_name,
                target=self._worker_thread,
                daemon=True
            )
            thread.start()

            self._threads.add(thread)
            self._thread_count += 1

    def _worker_thread(self) -> None:
        """Worker thread implementation."""
        while True:
            try:
                # Get work item
                try:
                    work_item = self._work_queue.get(block=True, timeout=0.1)
                except queue.Empty:
                    # Check for shutdown
                    with self._shutdown_lock:
                        if self._shutdown and self._work_queue.empty():
                            break
                    continue

                # Execute work item
                work_item()

            except Exception:
                traceback.print_exc()

    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
        """
        Shutdown the executor.

        Args:
            wait: Whether to wait for completion
            cancel_futures: Whether to cancel pending futures
        """
        with self._shutdown_lock:
            self._shutdown = True

            if cancel_futures:
                # Empty the work queue
                while True:
                    try:
                        self._work_queue.get_nowait()
                    except queue.Empty:
                        break

        if wait:
            # Wait for all threads to complete
            for thread in list(self._threads):
                thread.join(timeout=5.0)


# Import needed for typing (inside function only to avoid circular imports)
import os
from concurrent.futures import Future