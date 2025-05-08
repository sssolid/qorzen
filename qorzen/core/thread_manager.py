from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, cast

from PySide6.QtCore import QObject, QThread, Signal

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, ThreadManagerError

T = TypeVar('T')
R = TypeVar('R')


class TaskStatus(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


@dataclass
class TaskInfo:
    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    exception: Optional[Exception] = None
    submitter: str = 'unknown'
    priority: int = 0
    future: Optional[concurrent.futures.Future] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class QtTaskBridge(QObject):
    """Bridge to properly handle Qt threading requirements."""

    taskCompleted = Signal(str, object)  # task_id, result
    taskFailed = Signal(str, str)  # task_id, error_message
    taskProgress = Signal(str, int, str)  # task_id, progress, message

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)


class ThreadManager(QorzenManager):
    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        super().__init__(name='ThreadManager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('thread_manager')
        self._thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._max_workers = 4
        self._thread_name_prefix = 'qorzen-worker'
        self._tasks: Dict[str, TaskInfo] = {}
        self._tasks_lock = threading.RLock()
        self._periodic_tasks: Dict[str, Tuple[float, Callable, List, Dict]] = {}
        self._periodic_stop_event = threading.Event()
        self._periodic_thread: Optional[threading.Thread] = None
        self._active_tasks = 0
        self._active_tasks_lock = threading.RLock()

        # Qt-specific components
        self._qt_task_bridge = QtTaskBridge()
        self._qt_callbacks: Dict[str, Callable] = {}
        self._qt_callbacks_lock = threading.RLock()
        self._qt_task_bridge.taskCompleted.connect(self._handle_qt_task_completed)
        self._qt_task_bridge.taskFailed.connect(self._handle_qt_task_failed)

    def initialize(self) -> None:
        try:
            thread_config = self._config_manager.get('thread_pool', {})
            self._max_workers = thread_config.get('worker_threads', 4)
            self._thread_name_prefix = thread_config.get('thread_name_prefix', 'qorzen-worker')
            self._thread_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix=self._thread_name_prefix
            )
            self._periodic_thread = threading.Thread(
                target=self._periodic_task_scheduler,
                name='periodic-scheduler',
                daemon=True
            )
            self._periodic_thread.start()
            self._config_manager.register_listener('thread_pool', self._on_config_changed)
            self._logger.info(f'Thread Manager initialized with {self._max_workers} workers')
            self._initialized = True
            self._healthy = True
        except Exception as e:
            self._logger.error(f'Failed to initialize Thread Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize ThreadManager: {str(e)}',
                manager_name=self.name
            ) from e

    def submit_task(
            self,
            func: Callable[..., T],
            *args: Any,
            name: Optional[str] = None,
            submitter: str = 'unknown',
            priority: int = 0,
            metadata: Optional[Dict[str, Any]] = None,
            **kwargs: Any
    ) -> str:
        """
        Submit a task to the thread pool.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            name: Optional name for the task
            submitter: Who submitted this task
            priority: Priority (currently not used)
            metadata: Additional information about the task
            **kwargs: Keyword arguments for the function

        Returns:
            str: Task identifier
        """
        if not self._initialized or self._thread_pool is None:
            raise ThreadManagerError('Cannot submit tasks before initialization', thread_id=None)

        task_id = str(uuid.uuid4())
        task_name = name or f'task-{task_id[:8]}'
        task_info = TaskInfo(
            task_id=task_id,
            name=task_name,
            status=TaskStatus.PENDING,
            submitter=submitter,
            priority=priority,
            metadata=metadata or {}
        )

        @functools.wraps(func)
        def _task_wrapper(*args, **kwargs):
            with self._tasks_lock:
                if task_id in self._tasks:
                    self._tasks[task_id].status = TaskStatus.RUNNING
                    self._tasks[task_id].started_at = time.time()

            with self._active_tasks_lock:
                self._active_tasks += 1

            try:
                result = func(*args, **kwargs)
                with self._tasks_lock:
                    if task_id in self._tasks:
                        self._tasks[task_id].status = TaskStatus.COMPLETED
                        self._tasks[task_id].completed_at = time.time()
                return result
            except Exception as e:
                with self._tasks_lock:
                    if task_id in self._tasks:
                        self._tasks[task_id].status = TaskStatus.FAILED
                        self._tasks[task_id].exception = e
                        self._tasks[task_id].completed_at = time.time()

                self._logger.error(
                    f'Task {task_name} failed: {str(e)}',
                    extra={'task_id': task_id, 'submitter': submitter, 'error': str(e)}
                )
                raise
            finally:
                with self._active_tasks_lock:
                    self._active_tasks -= 1

        try:
            future = self._thread_pool.submit(_task_wrapper, *args, **kwargs)
            task_info.future = future
            with self._tasks_lock:
                self._tasks[task_id] = task_info

            self._logger.debug(
                f'Submitted task {task_name}',
                extra={'task_id': task_id, 'submitter': submitter, 'priority': priority}
            )
            return task_id
        except Exception as e:
            self._logger.error(
                f'Failed to submit task {task_name}: {str(e)}',
                extra={'submitter': submitter}
            )
            raise ThreadManagerError(
                f'Failed to submit task: {str(e)}',
                thread_id=task_id
            ) from e

    def submit_qt_task(
            self,
            func: Callable[..., T],
            *args: Any,
            on_completed: Optional[Callable[[T], None]] = None,
            on_failed: Optional[Callable[[str], None]] = None,
            name: Optional[str] = None,
            submitter: str = 'unknown',
            **kwargs: Any
    ) -> str:
        """
        Submit a task that safely interacts with Qt components.

        This method ensures proper thread safety when working with Qt objects.
        The callbacks will be executed on the thread that owns the Qt task bridge.

        Args:
            func: Function to execute in the thread pool
            on_completed: Callback when task completes successfully (will run in Qt thread)
            on_failed: Callback when task fails (will run in Qt thread)
            *args: Positional arguments for func
            name: Optional task name
            submitter: Who submitted this task
            **kwargs: Keyword arguments for func

        Returns:
            str: Task identifier
        """
        task_id = str(uuid.uuid4())
        task_name = name or f'qt-task-{task_id[:8]}'

        # Store callbacks with task ID
        if on_completed or on_failed:
            with self._qt_callbacks_lock:
                self._qt_callbacks[task_id] = (on_completed, on_failed)

        # Wrap the function to properly handle results/errors
        @functools.wraps(func)
        def _qt_task_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Signal completion through Qt bridge (thread-safe)
                self._qt_task_bridge.taskCompleted.emit(task_id, result)
                return result
            except Exception as e:
                self._logger.error(
                    f'Qt task {task_name} failed: {str(e)}',
                    extra={'task_id': task_id, 'submitter': submitter, 'error': str(e)}
                )
                # Signal failure through Qt bridge (thread-safe)
                self._qt_task_bridge.taskFailed.emit(task_id, str(e))
                raise

        # Submit wrapped task to thread pool
        return self.submit_task(
            _qt_task_wrapper,
            *args,
            name=task_name,
            submitter=submitter,
            metadata={'qt_task': True},
            **kwargs
        )

    def _handle_qt_task_completed(self, task_id: str, result: Any) -> None:
        """Handle task completion in the Qt thread."""
        with self._qt_callbacks_lock:
            if task_id in self._qt_callbacks:
                on_completed, _ = self._qt_callbacks[task_id]
                if on_completed:
                    try:
                        on_completed(result)
                    except Exception as e:
                        self._logger.error(
                            f'Error in Qt task completion callback: {str(e)}',
                            extra={'task_id': task_id, 'error': str(e)}
                        )
                # Clean up callback references
                del self._qt_callbacks[task_id]

    def _handle_qt_task_failed(self, task_id: str, error_message: str) -> None:
        """Handle task failure in the Qt thread."""
        with self._qt_callbacks_lock:
            if task_id in self._qt_callbacks:
                _, on_failed = self._qt_callbacks[task_id]
                if on_failed:
                    try:
                        on_failed(error_message)
                    except Exception as e:
                        self._logger.error(
                            f'Error in Qt task failure callback: {str(e)}',
                            extra={'task_id': task_id, 'error': str(e)}
                        )
                # Clean up callback references
                del self._qt_callbacks[task_id]

    def submit_async_task(
            self,
            coro_func: Callable[..., Any],
            *args: Any,
            name: Optional[str] = None,
            submitter: str = 'unknown',
            **kwargs: Any
    ) -> str:
        """
        Submit an async coroutine function to run in a dedicated event loop.

        Args:
            coro_func: Coroutine function to execute
            *args: Arguments for the coroutine function
            name: Optional task name
            submitter: Who submitted this task
            **kwargs: Keyword arguments for the coroutine function

        Returns:
            str: Task identifier
        """
        task_name = name or f'async-task-{coro_func.__name__}'

        def _run_async_task(*args, **kwargs):
            """Run coroutine in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro_func(*args, **kwargs))
            finally:
                loop.close()

        return self.submit_task(
            _run_async_task,
            *args,
            name=task_name,
            submitter=submitter,
            metadata={'async_task': True},
            **kwargs
        )

    def submit_qt_async_task(
            self,
            coro_func: Callable[..., Any],
            on_completed: Optional[Callable[[Any], None]] = None,
            on_failed: Optional[Callable[[str], None]] = None,
            *args: Any,
            name: Optional[str] = None,
            submitter: str = 'unknown',
            **kwargs: Any
    ) -> str:
        """
        Submit an async coroutine function that safely interacts with Qt components.

        Args:
            coro_func: Coroutine function to execute
            on_completed: Callback when task completes (runs in Qt thread)
            on_failed: Callback when task fails (runs in Qt thread)
            *args: Arguments for the coroutine function
            name: Optional task name
            submitter: Who submitted this task
            **kwargs: Keyword arguments for the coroutine function

        Returns:
            str: Task identifier
        """
        task_name = name or f'qt-async-task-{coro_func.__name__}'

        def _run_async_task(*args, **kwargs):
            """Run coroutine in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro_func(*args, **kwargs))
            finally:
                loop.close()

        return self.submit_qt_task(
            _run_async_task,
            on_completed=on_completed,
            on_failed=on_failed,
            *args,
            name=task_name,
            submitter=submitter,
            metadata={'async_task': True, 'qt_task': True},
            **kwargs
        )

    # All other existing methods remain the same
    def cancel_task(self, task_id: str) -> bool:
        if not self._initialized:
            return False
        with self._tasks_lock:
            if task_id not in self._tasks:
                return False
            task_info = self._tasks[task_id]
            if task_info.status != TaskStatus.PENDING:
                return False
            if task_info.future and task_info.future.cancel():
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = time.time()
                self._logger.debug(f'Cancelled task {task_info.name}')
                return True
        return False

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        if not self._initialized:
            return None
        with self._tasks_lock:
            if task_id not in self._tasks:
                return None
            task_info = self._tasks[task_id]
            result = {
                'task_id': task_info.task_id,
                'name': task_info.name,
                'status': task_info.status.value,
                'created_at': task_info.created_at,
                'started_at': task_info.started_at,
                'completed_at': task_info.completed_at,
                'submitter': task_info.submitter,
                'priority': task_info.priority,
                'metadata': task_info.metadata
            }
            if task_info.exception:
                result['error'] = str(task_info.exception)
            return result

    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        if not self._initialized:
            raise ThreadManagerError('Manager not initialized', thread_id=task_id)
        with self._tasks_lock:
            if task_id not in self._tasks:
                raise ThreadManagerError(f'Task {task_id} not found', thread_id=task_id)
            task_info = self._tasks[task_id]
            if task_info.status == TaskStatus.FAILED:
                if task_info.exception:
                    raise task_info.exception
                raise ThreadManagerError(f'Task {task_id} failed', thread_id=task_id)
            if task_info.status == TaskStatus.CANCELLED:
                raise ThreadManagerError(f'Task {task_id} was cancelled', thread_id=task_id)
            if not task_info.future:
                raise ThreadManagerError(f'Task {task_id} has no future object', thread_id=task_id)
            future = task_info.future
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise
        except Exception as e:
            raise ThreadManagerError(f'Task {task_id} failed: {str(e)}', thread_id=task_id) from e

    def schedule_periodic_task(self, interval: float, func: Callable, *args: Any, task_id: Optional[str] = None,
                               **kwargs: Any) -> str:
        if not self._initialized:
            raise ThreadManagerError('Manager not initialized', thread_id=task_id)
        if task_id is None:
            task_id = str(uuid.uuid4())
        self._periodic_tasks[task_id] = (interval, func, args, kwargs)
        self._logger.debug(f'Scheduled periodic task {task_id} with interval {interval}s')
        return task_id

    def cancel_periodic_task(self, task_id: str) -> bool:
        if not self._initialized:
            return False
        if task_id in self._periodic_tasks:
            del self._periodic_tasks[task_id]
            self._logger.debug(f'Cancelled periodic task {task_id}')
            return True
        return False

    def _periodic_task_scheduler(self) -> None:
        self._logger.debug('Periodic task scheduler started')
        last_run: Dict[str, float] = {}
        while not self._periodic_stop_event.is_set():
            try:
                current_time = time.time()
                for task_id, (interval, func, args, kwargs) in list(self._periodic_tasks.items()):
                    if task_id not in last_run or current_time - last_run[task_id] >= interval:
                        try:
                            self.submit_task(
                                func,
                                *args,
                                name=f'periodic-{task_id}',
                                submitter='periodic_scheduler',
                                metadata={'periodic': True, 'interval': interval},
                                **kwargs
                            )
                            last_run[task_id] = current_time
                        except Exception as e:
                            self._logger.error(f'Error scheduling periodic task {task_id}: {str(e)}')
                time.sleep(0.1)
            except Exception as e:
                self._logger.error(f'Error in periodic task scheduler: {str(e)}')

    def _on_config_changed(self, key: str, value: Any) -> None:
        if key == 'thread_pool.worker_threads':
            self._logger.warning(
                'Cannot change thread pool size at runtime, restart required',
                extra={'current_size': self._max_workers, 'new_size': value}
            )

    def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            self._logger.info('Shutting down Thread Manager')
            self._periodic_stop_event.set()
            if self._periodic_thread and self._periodic_thread.is_alive():
                self._periodic_thread.join(timeout=2.0)

            with self._tasks_lock:
                for task_id, task_info in list(self._tasks.items()):
                    if task_info.status == TaskStatus.PENDING:
                        if task_info.future:
                            task_info.future.cancel()
                            task_info.status = TaskStatus.CANCELLED
                            task_info.completed_at = time.time()

            if self._thread_pool is not None:
                self._thread_pool.shutdown(wait=True, cancel_futures=True)

            with self._tasks_lock:
                self._tasks.clear()

            self._periodic_tasks.clear()

            # Clear Qt callbacks
            with self._qt_callbacks_lock:
                self._qt_callbacks.clear()

            self._config_manager.unregister_listener('thread_pool', self._on_config_changed)
            self._initialized = False
            self._healthy = False
            self._logger.info('Thread Manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down Thread Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down ThreadManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        status = super().status()
        if self._initialized:
            task_counts = {status.value: 0 for status in TaskStatus}
            with self._tasks_lock:
                for task_info in self._tasks.values():
                    task_counts[task_info.status.value] += 1

            status.update({
                'thread_pool': {
                    'max_workers': self._max_workers,
                    'active_tasks': self._active_tasks
                },
                'tasks': {
                    'total': len(self._tasks),
                    'by_status': task_counts
                },
                'periodic_tasks': len(self._periodic_tasks),
                'qt_tasks': {
                    'callback_registrations': len(self._qt_callbacks)
                }
            })
        return status