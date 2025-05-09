from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import logging
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union, cast

from PySide6.QtCore import QMetaObject, QObject, Qt, Signal, Slot
from pydantic import BaseModel, Field

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, ThreadManagerError

T = TypeVar("T")
R = TypeVar("R")


class ThreadExecutionContext(Enum):
    """Defines where a task should be executed."""

    WORKER_THREAD = auto()  # Execute in worker thread pool
    MAIN_THREAD = auto()  # Execute in the main Qt thread
    CURRENT_THREAD = auto()  # Execute in the current thread


class TaskStatus(str, Enum):
    """Represents the current status of a task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Priority levels for task execution."""

    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


class TaskResult(BaseModel):
    """Represents the result of a completed task."""

    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


@dataclass
class TaskInfo:
    """Information about a task being executed."""

    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    exception: Optional[Exception] = None
    error_traceback: Optional[str] = None
    submitter: str = "unknown"
    priority: TaskPriority = TaskPriority.NORMAL
    future: Optional[concurrent.futures.Future] = None
    execution_context: ThreadExecutionContext = ThreadExecutionContext.WORKER_THREAD
    is_ui_task: bool = False
    is_async_task: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class QtTaskBridge(QObject):
    """Bridges between threaded tasks and Qt's signal/slot system."""

    # Signal emitted when a task completes successfully
    taskCompleted = Signal(str, object)

    # Signal emitted when a task fails
    taskFailed = Signal(str, str, str)  # task_id, error_message, error_traceback

    # Signal emitted to report task progress
    taskProgress = Signal(str, int, str)  # task_id, progress_percent, status_message

    # Signal to execute a function on the main thread
    executeOnMainThread = Signal(object, tuple, dict, object)  # func, args, kwargs, callback_event

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize the Qt task bridge.

        Args:
            parent: The parent QObject
        """
        super().__init__(parent)
        # Use DirectConnection to ensure immediate execution in the thread of the receiver
        self.executeOnMainThread.connect(
            self._execute_on_main_thread,
            Qt.ConnectionType.QueuedConnection
        )

    @Slot(object, tuple, dict, object)
    def _execute_on_main_thread(
            self, func: Callable, args: tuple, kwargs: dict, callback_event: Optional[threading.Event]
    ) -> None:
        """Execute a function on the main thread.

        Args:
            func: The function to execute
            args: The positional arguments for the function
            kwargs: The keyword arguments for the function
            callback_event: Event to set when execution is complete
        """
        try:
            func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error executing function on main thread: {str(e)}")
            logging.error(traceback.format_exc())
        finally:
            if callback_event:
                callback_event.set()


class TaskProgressReporter:
    """Helper class for reporting task progress."""

    def __init__(
            self,
            task_id: str,
            task_bridge: QtTaskBridge,
            execution_context: ThreadExecutionContext,
            thread_manager: ThreadManager
    ) -> None:
        """Initialize the progress reporter.

        Args:
            task_id: The ID of the task
            task_bridge: The Qt task bridge
            execution_context: The execution context of the task
            thread_manager: The thread manager
        """
        self.task_id = task_id
        self.task_bridge = task_bridge
        self.execution_context = execution_context
        self.thread_manager = thread_manager

    def report_progress(self, percent: int, message: str = "") -> None:
        """Report task progress.

        Args:
            percent: The progress percentage (0-100)
            message: Optional status message
        """
        if self.thread_manager.is_main_thread():
            self.task_bridge.taskProgress.emit(self.task_id, percent, message)
        else:
            self.thread_manager.run_on_main_thread(
                lambda: self.task_bridge.taskProgress.emit(self.task_id, percent, message))


class ThreadManager(QorzenManager):
    """Manages thread execution for background processing and UI updates."""

    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        """Initialize the thread manager.

        Args:
            config_manager: The configuration manager
            logger_manager: The logger manager
        """
        super().__init__(name="ThreadManager")
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger("thread_manager")
        self._thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._max_workers = 4
        self._thread_name_prefix = "qorzen-worker"
        self._tasks: Dict[str, TaskInfo] = {}
        self._tasks_lock = threading.RLock()
        self._periodic_tasks: Dict[str, Tuple[float, Callable, List, Dict]] = {}
        self._periodic_stop_event = threading.Event()
        self._periodic_thread: Optional[threading.Thread] = None
        self._active_tasks = 0
        self._active_tasks_lock = threading.RLock()
        self._qt_task_bridge = QtTaskBridge()
        self._qt_callbacks: Dict[str, Tuple[Optional[Callable], Optional[Callable]]] = {}
        self._qt_callbacks_lock = threading.RLock()

        # Connect signals to slots with QueuedConnection to ensure execution on the main thread
        self._qt_task_bridge.taskCompleted.connect(
            self._handle_qt_task_completed,
            Qt.ConnectionType.QueuedConnection
        )
        self._qt_task_bridge.taskFailed.connect(
            self._handle_qt_task_failed,
            Qt.ConnectionType.QueuedConnection
        )

        # Store main thread ID for thread safety checks
        self._main_thread_id = threading.get_ident()
        self._logger.debug(f"Main thread ID: {self._main_thread_id}")

        # Task result handlers
        self._task_result_handlers: Dict[str, Callable[[TaskResult], None]] = {}
        self._task_result_handlers_lock = threading.RLock()

    def initialize(self) -> None:
        """Initialize the thread manager."""
        try:
            thread_config = self._config_manager.get("thread_pool", {})
            self._max_workers = thread_config.get("worker_threads", 4)
            self._thread_name_prefix = thread_config.get("thread_name_prefix", "qorzen-worker")

            # Initialize thread pool
            self._thread_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix=self._thread_name_prefix
            )

            # Start periodic task scheduler thread
            self._periodic_thread = threading.Thread(
                target=self._periodic_task_scheduler,
                name="periodic-scheduler",
                daemon=True
            )
            self._periodic_thread.start()

            # Register config change listener
            self._config_manager.register_listener("thread_pool", self._on_config_changed)

            self._logger.info(f"Thread Manager initialized with {self._max_workers} workers")
            self._initialized = True
            self._healthy = True
        except Exception as e:
            self._logger.error(f"Failed to initialize Thread Manager: {str(e)}")
            raise ManagerInitializationError(
                f"Failed to initialize ThreadManager: {str(e)}",
                manager_name=self.name
            ) from e

    def is_main_thread(self) -> bool:
        """Check if the current thread is the main Qt thread.

        Returns:
            True if called from the main thread, False otherwise
        """
        return threading.get_ident() == self._main_thread_id

    def run_on_main_thread(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Run a function on the main Qt thread.

        Args:
            func: The function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        if self.is_main_thread():
            # Already on main thread, just execute
            func(*args, **kwargs)
        else:
            # Need to queue for execution on main thread
            self._qt_task_bridge.executeOnMainThread.emit(func, args, kwargs, None)

    def execute_on_main_thread_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function on the main thread and wait for its completion.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function call

        Raises:
            Any exception raised by the function
        """
        if self.is_main_thread():
            # Already on main thread, execute directly
            return func(*args, **kwargs)

        # Prepare containers for result and exception
        event = threading.Event()
        result_container = [None]
        error_container = [None]
        traceback_container = [None]

        def main_thread_executor() -> None:
            try:
                result_container[0] = func(*args, **kwargs)
            except Exception as e:
                error_container[0] = e
                traceback_container[0] = traceback.format_exc()

        # Emit signal to execute on main thread
        self._qt_task_bridge.executeOnMainThread.emit(main_thread_executor, (), {}, event)

        # Wait for execution to complete
        event.wait()

        # Handle exceptions
        if error_container[0] is not None:
            self._logger.error(
                f"Error executing function on main thread: {str(error_container[0])}\n"
                f"{traceback_container[0]}"
            )
            raise error_container[0]

        return result_container[0]

    def submit_task(
            self,
            func: Callable[..., T],
            *args: Any,
            name: Optional[str] = None,
            submitter: str = "unknown",
            priority: Union[int, TaskPriority] = TaskPriority.NORMAL,
            execution_context: ThreadExecutionContext = ThreadExecutionContext.WORKER_THREAD,
            metadata: Optional[Dict[str, Any]] = None,
            result_handler: Optional[Callable[[TaskResult], None]] = None,
            **kwargs: Any
    ) -> str:
        """Submit a task for execution.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            name: Optional name for the task
            submitter: Identifier for who submitted the task
            priority: Task priority
            execution_context: Where to execute the task
            metadata: Additional metadata for the task
            result_handler: Optional callback for handling the task result
            **kwargs: Keyword arguments for the function

        Returns:
            The task ID

        Raises:
            ThreadManagerError: If the thread manager is not initialized
        """
        if not self._initialized or self._thread_pool is None:
            raise ThreadManagerError("Cannot submit tasks before initialization", thread_id=None)

        # Generate task ID and name
        task_id = str(uuid.uuid4())
        task_name = name or f"task-{task_id[:8]}"

        # Convert priority to TaskPriority enum if it's an int
        if isinstance(priority, int) and not isinstance(priority, TaskPriority):
            try:
                priority = TaskPriority(priority)
            except ValueError:
                # Find the closest TaskPriority
                if priority < TaskPriority.NORMAL:
                    priority = TaskPriority.LOW
                elif priority < TaskPriority.HIGH:
                    priority = TaskPriority.NORMAL
                elif priority < TaskPriority.CRITICAL:
                    priority = TaskPriority.HIGH
                else:
                    priority = TaskPriority.CRITICAL

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            name=task_name,
            status=TaskStatus.PENDING,
            submitter=submitter,
            priority=priority,
            execution_context=execution_context,
            metadata=metadata or {},
        )

        # Register result handler if provided
        if result_handler:
            with self._task_result_handlers_lock:
                self._task_result_handlers[task_id] = result_handler

        # Create a progress reporter for this task
        progress_reporter = TaskProgressReporter(
            task_id,
            self._qt_task_bridge,
            execution_context,
            self
        )

        @functools.wraps(func)
        def _task_wrapper(*args, **kwargs):
            # Update task status to running
            with self._tasks_lock:
                if task_id in self._tasks:
                    self._tasks[task_id].status = TaskStatus.RUNNING
                    self._tasks[task_id].started_at = time.time()

            # Track active tasks
            with self._active_tasks_lock:
                self._active_tasks += 1

            try:
                # Add progress reporter to kwargs
                kwargs["progress_reporter"] = progress_reporter

                # Execute the function
                result = func(*args, **kwargs)

                # Update task status to completed
                with self._tasks_lock:
                    if task_id in self._tasks:
                        self._tasks[task_id].status = TaskStatus.COMPLETED
                        self._tasks[task_id].completed_at = time.time()

                # Handle task result
                task_result = TaskResult(success=True, result=result)
                self._process_task_result(task_id, task_result)

                return result
            except Exception as e:
                # Capture the traceback
                tb_str = traceback.format_exc()

                # Update task status to failed
                with self._tasks_lock:
                    if task_id in self._tasks:
                        self._tasks[task_id].status = TaskStatus.FAILED
                        self._tasks[task_id].exception = e
                        self._tasks[task_id].error_traceback = tb_str
                        self._tasks[task_id].completed_at = time.time()

                self._logger.error(
                    f"Task {task_name} failed: {str(e)}",
                    extra={
                        "task_id": task_id,
                        "submitter": submitter,
                        "error": str(e),
                        "traceback": tb_str
                    }
                )

                # Handle task failure
                task_result = TaskResult(
                    success=False,
                    error=str(e),
                    error_traceback=tb_str
                )
                self._process_task_result(task_id, task_result)

                # Re-raise the exception
                raise
            finally:
                # Decrement active task count
                with self._active_tasks_lock:
                    self._active_tasks -= 1

        try:
            # Handle based on execution context
            if execution_context == ThreadExecutionContext.MAIN_THREAD:
                if self.is_main_thread():
                    # Already on main thread, execute directly
                    future = concurrent.futures.Future()
                    try:
                        result = _task_wrapper(*args, **kwargs)
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                else:
                    # Queue for execution on main thread
                    future = concurrent.futures.Future()

                    def main_thread_executor():
                        try:
                            result = _task_wrapper(*args, **kwargs)
                            future.set_result(result)
                        except Exception as e:
                            future.set_exception(e)

                    self.run_on_main_thread(main_thread_executor)
            elif execution_context == ThreadExecutionContext.CURRENT_THREAD:
                # Execute in current thread
                future = concurrent.futures.Future()
                try:
                    result = _task_wrapper(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
            else:
                # Execute in worker thread pool
                future = self._thread_pool.submit(_task_wrapper, *args, **kwargs)

            # Store future in task info
            task_info.future = future

            # Store task info
            with self._tasks_lock:
                self._tasks[task_id] = task_info

            self._logger.debug(
                f"Submitted task {task_name}",
                extra={
                    "task_id": task_id,
                    "submitter": submitter,
                    "priority": str(priority),
                    "execution_context": execution_context.name
                }
            )

            return task_id
        except Exception as e:
            self._logger.error(
                f"Failed to submit task {task_name}: {str(e)}",
                extra={"submitter": submitter, "traceback": traceback.format_exc()}
            )
            # Clean up any registered result handler
            with self._task_result_handlers_lock:
                if task_id in self._task_result_handlers:
                    del self._task_result_handlers[task_id]

            raise ThreadManagerError(f"Failed to submit task: {str(e)}", thread_id=task_id) from e

    def _process_task_result(self, task_id: str, result: TaskResult) -> None:
        """Process the result of a task.

        Args:
            task_id: The ID of the task
            result: The task result
        """
        # Check for a registered result handler
        with self._task_result_handlers_lock:
            if task_id in self._task_result_handlers:
                handler = self._task_result_handlers[task_id]
                del self._task_result_handlers[task_id]

                # Execute handler on appropriate thread based on task context
                with self._tasks_lock:
                    if task_id in self._tasks:
                        task_info = self._tasks[task_id]
                        if task_info.execution_context == ThreadExecutionContext.MAIN_THREAD:
                            # Already on main thread, execute directly
                            if self.is_main_thread():
                                handler(result)
                            else:
                                # Queue for execution on main thread
                                self.run_on_main_thread(handler, result)
                        else:
                            # Execute in current thread (already in appropriate thread)
                            handler(result)

    def submit_qt_task(
            self,
            func: Callable[..., T],
            *args: Any,
            on_completed: Optional[Callable[[T], None]] = None,
            on_failed: Optional[Callable[[str, str], None]] = None,
            name: Optional[str] = None,
            submitter: str = "unknown",
            priority: Union[int, TaskPriority] = TaskPriority.NORMAL,
            **kwargs: Any
    ) -> str:
        """Submit a task that updates the UI when complete.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            on_completed: Callback for when the task completes successfully
            on_failed: Callback for when the task fails
            name: Optional name for the task
            submitter: Identifier for who submitted the task
            priority: Task priority
            **kwargs: Keyword arguments for the function

        Returns:
            The task ID
        """
        task_id = str(uuid.uuid4())
        task_name = name or f"qt-task-{task_id[:8]}"

        # Register callbacks if provided
        if on_completed or on_failed:
            with self._qt_callbacks_lock:
                self._qt_callbacks[task_id] = (on_completed, on_failed)

        @functools.wraps(func)
        def _qt_task_wrapper(*args, **kwargs):
            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Emit signal for task completion
                if self.is_main_thread():
                    self._qt_task_bridge.taskCompleted.emit(task_id, result)
                else:
                    # Need to emit the signal on the main thread
                    self.run_on_main_thread(
                        lambda: self._qt_task_bridge.taskCompleted.emit(task_id, result)
                    )

                return result
            except Exception as e:
                # Capture traceback
                tb_str = traceback.format_exc()

                self._logger.error(
                    f"Qt task {task_name} failed: {str(e)}",
                    extra={
                        "task_id": task_id,
                        "submitter": submitter,
                        "error": str(e),
                        "traceback": tb_str
                    }
                )

                # Emit signal for task failure
                if self.is_main_thread():
                    self._qt_task_bridge.taskFailed.emit(task_id, str(e), tb_str)
                else:
                    # Need to emit the signal on the main thread
                    self.run_on_main_thread(
                        lambda: self._qt_task_bridge.taskFailed.emit(task_id, str(e), tb_str)
                    )

                raise

        # Submit the wrapped task to be executed in a worker thread
        return self.submit_task(
            _qt_task_wrapper,
            *args,
            name=task_name,
            submitter=submitter,
            priority=priority,
            metadata={"qt_task": True},
            execution_context=ThreadExecutionContext.WORKER_THREAD,
            **kwargs
        )

    def submit_main_thread_task(
            self,
            func: Callable[..., T],
            *args: Any,
            on_completed: Optional[Callable[[T], None]] = None,
            on_failed: Optional[Callable[[str, str], None]] = None,
            name: Optional[str] = None,
            priority: Union[int, TaskPriority] = TaskPriority.NORMAL,
            **kwargs: Any
    ) -> str:
        """Submit a task to be executed on the main thread.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            on_completed: Callback for when the task completes successfully
            on_failed: Callback for when the task fails
            name: Optional name for the task
            priority: Task priority
            **kwargs: Keyword arguments for the function

        Returns:
            The task ID
        """
        task_id = str(uuid.uuid4())
        task_name = name or f"main-thread-task-{task_id[:8]}"

        # Define executor function
        def main_thread_executor():
            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Call completion callback if provided
                if on_completed:
                    on_completed(result)

                return result
            except Exception as e:
                # Capture traceback
                tb_str = traceback.format_exc()

                self._logger.error(
                    f"Main thread task {task_name} failed: {str(e)}",
                    extra={
                        "task_id": task_id,
                        "error": str(e),
                        "traceback": tb_str
                    }
                )

                # Call failure callback if provided
                if on_failed:
                    on_failed(str(e), tb_str)

                raise

        # Submit task to be executed on the main thread
        return self.submit_task(
            main_thread_executor,
            name=task_name,
            priority=priority,
            execution_context=ThreadExecutionContext.MAIN_THREAD,
            metadata={"main_thread_task": True}
        )

    @Slot(str, object)
    def _handle_qt_task_completed(self, task_id: str, result: Any) -> None:
        """Handle when a Qt task completes successfully.

        Args:
            task_id: The ID of the task
            result: The result of the task
        """
        with self._qt_callbacks_lock:
            if task_id in self._qt_callbacks:
                on_completed, _ = self._qt_callbacks[task_id]
                if on_completed:
                    try:
                        on_completed(result)
                    except Exception as e:
                        self._logger.error(
                            f"Error in Qt task completion callback: {str(e)}",
                            extra={
                                "task_id": task_id,
                                "error": str(e),
                                "traceback": traceback.format_exc()
                            }
                        )
                # Remove callbacks
                del self._qt_callbacks[task_id]

    @Slot(str, str, str)
    def _handle_qt_task_failed(self, task_id: str, error_message: str, error_traceback: str) -> None:
        """Handle when a Qt task fails.

        Args:
            task_id: The ID of the task
            error_message: The error message
            error_traceback: The error traceback
        """
        with self._qt_callbacks_lock:
            if task_id in self._qt_callbacks:
                _, on_failed = self._qt_callbacks[task_id]
                if on_failed:
                    try:
                        on_failed(error_message, error_traceback)
                    except Exception as e:
                        self._logger.error(
                            f"Error in Qt task failure callback: {str(e)}",
                            extra={
                                "task_id": task_id,
                                "error": str(e),
                                "traceback": traceback.format_exc()
                            }
                        )
                # Remove callbacks
                del self._qt_callbacks[task_id]

    def submit_async_task(
            self,
            coro_func: Callable[..., Any],
            *args: Any,
            name: Optional[str] = None,
            submitter: str = "unknown",
            priority: Union[int, TaskPriority] = TaskPriority.NORMAL,
            on_completed: Optional[Callable[[Any], None]] = None,
            on_failed: Optional[Callable[[str, str], None]] = None,
            **kwargs: Any
    ) -> str:
        """Submit an async task for execution.

        Args:
            coro_func: The async coroutine function to execute
            *args: Positional arguments for the function
            name: Optional name for the task
            submitter: Identifier for who submitted the task
            priority: Task priority
            on_completed: Callback for when the task completes successfully
            on_failed: Callback for when the task fails
            **kwargs: Keyword arguments for the function

        Returns:
            The task ID
        """
        task_name = name or f"async-task-{coro_func.__name__}"

        def _run_async_task(*args, **kwargs):
            """Run an async task in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Execute the coroutine in the loop
                return loop.run_until_complete(coro_func(*args, **kwargs))
            finally:
                # Clean up the loop
                loop.close()

        # If callbacks are provided, use submit_qt_task
        if on_completed or on_failed:
            return self.submit_qt_task(
                _run_async_task,
                *args,
                on_completed=on_completed,
                on_failed=on_failed,
                name=task_name,
                submitter=submitter,
                priority=priority,
                metadata={"async_task": True, "qt_task": True},
                **kwargs
            )
        else:
            # Otherwise use regular submit_task
            return self.submit_task(
                _run_async_task,
                *args,
                name=task_name,
                submitter=submitter,
                priority=priority,
                metadata={"async_task": True},
                **kwargs
            )

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task.

        Args:
            task_id: The ID of the task to cancel

        Returns:
            True if the task was cancelled, False otherwise
        """
        if not self._initialized:
            return False

        with self._tasks_lock:
            if task_id not in self._tasks:
                return False

            task_info = self._tasks[task_id]

            # Can only cancel pending tasks
            if task_info.status != TaskStatus.PENDING:
                return False

            # Attempt to cancel the future
            if task_info.future and task_info.future.cancel():
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = time.time()
                self._logger.debug(f"Cancelled task {task_info.name}")

                # Clean up any registered callbacks
                with self._qt_callbacks_lock:
                    if task_id in self._qt_callbacks:
                        del self._qt_callbacks[task_id]

                # Clean up any registered result handlers
                with self._task_result_handlers_lock:
                    if task_id in self._task_result_handlers:
                        del self._task_result_handlers[task_id]

                return True

        return False

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a task.

        Args:
            task_id: The ID of the task

        Returns:
            A dictionary of task information, or None if the task is not found
        """
        if not self._initialized:
            return None

        with self._tasks_lock:
            if task_id not in self._tasks:
                return None

            task_info = self._tasks[task_id]

            result = {
                "task_id": task_info.task_id,
                "name": task_info.name,
                "status": task_info.status.value,
                "created_at": task_info.created_at,
                "started_at": task_info.started_at,
                "completed_at": task_info.completed_at,
                "submitter": task_info.submitter,
                "priority": task_info.priority.value if isinstance(task_info.priority,
                                                                   TaskPriority) else task_info.priority,
                "execution_context": task_info.execution_context.name,
                "is_ui_task": task_info.is_ui_task,
                "is_async_task": task_info.is_async_task,
                "metadata": task_info.metadata
            }

            if task_info.exception:
                result["error"] = str(task_info.exception)
                result["error_traceback"] = task_info.error_traceback

            return result

    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Get the result of a completed task.

        Args:
            task_id: The ID of the task
            timeout: Optional timeout in seconds

        Returns:
            The result of the task

        Raises:
            ThreadManagerError: If the task is not found, failed, cancelled, or has no future
            concurrent.futures.TimeoutError: If the timeout is reached
        """
        if not self._initialized:
            raise ThreadManagerError("Manager not initialized", thread_id=task_id)

        with self._tasks_lock:
            if task_id not in self._tasks:
                raise ThreadManagerError(f"Task {task_id} not found", thread_id=task_id)

            task_info = self._tasks[task_id]

            if task_info.status == TaskStatus.FAILED:
                if task_info.exception:
                    raise task_info.exception
                raise ThreadManagerError(f"Task {task_id} failed", thread_id=task_id)

            if task_info.status == TaskStatus.CANCELLED:
                raise ThreadManagerError(f"Task {task_id} was cancelled", thread_id=task_id)

            if not task_info.future:
                raise ThreadManagerError(f"Task {task_id} has no future object", thread_id=task_id)

            future = task_info.future

        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise
        except Exception as e:
            raise ThreadManagerError(f"Task {task_id} failed: {str(e)}", thread_id=task_id) from e

    def schedule_periodic_task(
            self,
            interval: float,
            func: Callable,
            *args: Any,
            task_id: Optional[str] = None,
            **kwargs: Any
    ) -> str:
        """Schedule a task to run periodically.

        Args:
            interval: The interval in seconds between executions
            func: The function to execute periodically
            *args: Positional arguments for the function
            task_id: Optional task ID (one will be generated if not provided)
            **kwargs: Keyword arguments for the function

        Returns:
            The task ID

        Raises:
            ThreadManagerError: If the thread manager is not initialized
        """
        if not self._initialized:
            raise ThreadManagerError("Manager not initialized", thread_id=task_id)

        # Generate task ID if not provided
        if task_id is None:
            task_id = str(uuid.uuid4())

        # Store the periodic task
        self._periodic_tasks[task_id] = (interval, func, args, kwargs)

        self._logger.debug(f"Scheduled periodic task {task_id} with interval {interval}s")

        return task_id

    def cancel_periodic_task(self, task_id: str) -> bool:
        """Cancel a periodic task.

        Args:
            task_id: The ID of the periodic task

        Returns:
            True if the task was cancelled, False otherwise
        """
        if not self._initialized:
            return False

        if task_id in self._periodic_tasks:
            del self._periodic_tasks[task_id]
            self._logger.debug(f"Cancelled periodic task {task_id}")
            return True

        return False

    def _periodic_task_scheduler(self) -> None:
        """Scheduler for periodic tasks."""
        self._logger.debug("Periodic task scheduler started")

        # Track the last run time for each task
        last_run: Dict[str, float] = {}

        while not self._periodic_stop_event.is_set():
            try:
                current_time = time.time()

                # Check each task
                for task_id, (interval, func, args, kwargs) in list(self._periodic_tasks.items()):
                    # Run task if it's due
                    if task_id not in last_run or current_time - last_run[task_id] >= interval:
                        try:
                            # Submit task for execution
                            self.submit_task(
                                func,
                                *args,
                                name=f"periodic-{task_id}",
                                submitter="periodic_scheduler",
                                metadata={"periodic": True, "interval": interval},
                                **kwargs
                            )

                            # Update last run time
                            last_run[task_id] = current_time
                        except Exception as e:
                            self._logger.error(
                                f"Error scheduling periodic task {task_id}: {str(e)}",
                                extra={"traceback": traceback.format_exc()}
                            )

                # Sleep to avoid busy waiting
                time.sleep(0.1)
            except Exception as e:
                self._logger.error(
                    f"Error in periodic task scheduler: {str(e)}",
                    extra={"traceback": traceback.format_exc()}
                )

    def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: The configuration key that changed
            value: The new value
        """
        if key == "thread_pool.worker_threads":
            self._logger.warning(
                "Cannot change thread pool size at runtime, restart required",
                extra={"current_size": self._max_workers, "new_size": value}
            )

    def shutdown(self) -> None:
        """Shut down the thread manager."""
        if not self._initialized:
            return

        try:
            self._logger.info("Shutting down Thread Manager")

            # Stop periodic task scheduler
            self._periodic_stop_event.set()
            if self._periodic_thread and self._periodic_thread.is_alive():
                self._periodic_thread.join(timeout=2.0)

            # Cancel pending tasks
            with self._tasks_lock:
                for task_id, task_info in list(self._tasks.items()):
                    if task_info.status == TaskStatus.PENDING:
                        if task_info.future:
                            task_info.future.cancel()
                            task_info.status = TaskStatus.CANCELLED
                            task_info.completed_at = time.time()

            # Shut down thread pool
            if self._thread_pool is not None:
                self._thread_pool.shutdown(wait=True, cancel_futures=True)

            # Clear data structures
            with self._tasks_lock:
                self._tasks.clear()

            self._periodic_tasks.clear()

            with self._qt_callbacks_lock:
                self._qt_callbacks.clear()

            with self._task_result_handlers_lock:
                self._task_result_handlers.clear()

            # Unregister config change listener
            self._config_manager.unregister_listener("thread_pool", self._on_config_changed)

            self._initialized = False
            self._healthy = False

            self._logger.info("Thread Manager shut down successfully")
        except Exception as e:
            self._logger.error(f"Failed to shut down Thread Manager: {str(e)}")
            raise ManagerShutdownError(
                f"Failed to shut down ThreadManager: {str(e)}",
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the thread manager.

        Returns:
            A dictionary containing status information
        """
        status = super().status()

        if self._initialized:
            # Count tasks by status
            task_counts = {status.value: 0 for status in TaskStatus}

            with self._tasks_lock:
                for task_info in self._tasks.values():
                    task_counts[task_info.status.value] += 1

            # Add status information
            status.update({
                "thread_pool": {
                    "max_workers": self._max_workers,
                    "active_tasks": self._active_tasks
                },
                "tasks": {
                    "total": len(self._tasks),
                    "by_status": task_counts
                },
                "periodic_tasks": len(self._periodic_tasks),
                "qt_tasks": {
                    "callback_registrations": len(self._qt_callbacks)
                },
                "main_thread_id": self._main_thread_id,
                "current_thread_id": threading.get_ident(),
                "is_current_main_thread": self.is_main_thread()
            })

        return status