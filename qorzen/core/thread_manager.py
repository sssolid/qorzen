# qorzen/core/thread_manager.py
from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import logging
import os
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union, cast

from PySide6.QtCore import QObject, Qt, Signal, Slot, QMetaObject

from qorzen.core.base import QorzenManager
from qorzen.core.thread_safe_core import (
    ThreadDispatcher, ThreadType, TaskStatus, TaskPriority,
    run_on_main_thread, is_qt_object, ensure_main_thread
)
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, ThreadManagerError

T = TypeVar('T')
R = TypeVar('R')


class ThreadManager(QorzenManager):
    """
    Thread manager that ensures proper thread handling without Qt threading errors.

    This completely redesigned implementation ensures plugin code never has to
    worry about what thread it's running on.
    """

    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        """
        Initialize the thread manager.

        Args:
            config_manager: Configuration manager
            logger_manager: Logger manager
        """
        super().__init__(name="ThreadManager")
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('thread_manager')

        # Core components
        self._dispatcher = ThreadDispatcher.instance()

        # Configuration
        self._max_workers = 4
        self._thread_name_prefix = 'qorzen-worker'

        # Periodic tasks
        self._periodic_tasks: Dict[str, Dict[str, Any]] = {}
        self._periodic_tasks_lock = threading.RLock()
        self._periodic_stop_event = threading.Event()
        self._periodic_thread: Optional[threading.Thread] = None

        # Task tracking
        self._task_callbacks: Dict[str, Dict[str, Any]] = {}
        self._task_callbacks_lock = threading.RLock()

    def initialize(self) -> None:
        """Initialize the thread manager."""
        try:
            # Load configuration
            thread_config = self._config_manager.get('thread_pool', {})
            self._max_workers = thread_config.get('worker_threads', 4)
            self._thread_name_prefix = thread_config.get('thread_name_prefix', 'qorzen-worker')

            # Start periodic task thread
            self._periodic_thread = threading.Thread(
                target=self._periodic_task_handler,
                name='periodic-task-handler',
                daemon=True
            )
            self._periodic_thread.start()

            # Register configuration listener
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

    def is_main_thread(self) -> bool:
        """
        Check if current thread is the main thread.

        Returns:
            True if running on main thread
        """
        return self._dispatcher.is_main_thread()

    def run_on_main_thread(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Run a function on the main thread without waiting for result.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        if self.is_main_thread():
            func(*args, **kwargs)
        else:
            self._dispatcher.execute_on_thread(
                func,
                ThreadType.MAIN,
                *args,
                **kwargs
            )

    def execute_on_main_thread_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Run a function on the main thread and wait for result.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        if self.is_main_thread():
            return func(*args, **kwargs)

        future = self._dispatcher.execute_on_thread(
            func,
            ThreadType.MAIN,
            *args,
            **kwargs
        )
        return future.result()

    def submit_task(self,
                    func: Callable[..., T],
                    *args: Any,
                    name: Optional[str] = None,
                    submitter: str = 'unknown',
                    priority: Union[int, TaskPriority] = TaskPriority.NORMAL,
                    execution_context: Union[ThreadType, str, None] = None,
                    **kwargs: Any) -> str:
        """
        Submit a task for execution with proper thread handling.

        Args:
            func: Function to execute
            *args: Function arguments
            name: Task name
            submitter: Task submitter identifier
            priority: Task priority
            execution_context: Thread context to run on
            **kwargs: Function keyword arguments

        Returns:
            Task identifier
        """
        if not self._initialized:
            raise ThreadManagerError('Thread Manager not initialized', thread_id=None)

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Determine task name
        task_name = name or f'task-{task_id[:8]}'

        # Normalize priority
        if isinstance(priority, int) and not isinstance(priority, TaskPriority):
            if priority < 50:
                priority = TaskPriority.LOW
            elif priority < 100:
                priority = TaskPriority.NORMAL
            elif priority < 200:
                priority = TaskPriority.HIGH
            else:
                priority = TaskPriority.CRITICAL

        # Determine execution context
        thread_type = None

        if execution_context is not None:
            if isinstance(execution_context, ThreadType):
                thread_type = execution_context
            elif isinstance(execution_context, str):
                if execution_context.upper() == 'MAIN_THREAD':
                    thread_type = ThreadType.MAIN
                elif execution_context.upper() == 'WORKER_THREAD':
                    thread_type = ThreadType.WORKER
                elif execution_context.upper() == 'CURRENT_THREAD':
                    thread_type = ThreadType.CURRENT

        # Auto-detect UI thread requirements if not specified
        on_ui_thread = False
        if thread_type is None:
            # Try to detect if this task needs to run on UI thread
            for arg in args:
                if is_qt_object(arg):
                    on_ui_thread = True
                    break

            for arg in kwargs.values():
                if is_qt_object(arg):
                    on_ui_thread = True
                    break

            thread_type = ThreadType.MAIN if on_ui_thread else ThreadType.WORKER

        # Make sure we have a progress reporter parameter if function expects it
        has_progress_param = (
                'progress_reporter' in func.__code__.co_varnames[:func.__code__.co_argcount]
        )

        # Create task wrapper that safely handles all threading concerns
        @functools.wraps(func)
        def task_wrapper(progress_reporter: Any) -> T:
            try:
                # Execute the task function
                if has_progress_param:
                    return func(*args, progress_reporter=progress_reporter, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                self._logger.error(
                    f"Task {task_name} failed: {str(e)}",
                    extra={
                        'task_id': task_id,
                        'submitter': submitter,
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise

        # Submit the task using the dispatcher
        self._dispatcher.submit_task(
            task_wrapper,
            task_id=task_id,
            on_ui_thread=(thread_type == ThreadType.MAIN),
            has_progress=True,
            on_completed=self._handle_task_completed,
            on_failed=self._handle_task_failed,
            on_cancelled=self._handle_task_cancelled
        )

        self._logger.debug(
            f"Submitted task {task_name}",
            extra={
                'task_id': task_id,
                'submitter': submitter,
                'priority': priority.value if isinstance(priority, TaskPriority) else priority,
                'thread_type': thread_type.name if thread_type else 'AUTO'
            }
        )

        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task if possible.

        Args:
            task_id: Task to cancel

        Returns:
            Whether cancellation was successful
        """
        return self._dispatcher.cancel_task(task_id)

    def schedule_periodic_task(self,
                               interval: float,
                               func: Callable,
                               *args: Any,
                               task_id: Optional[str] = None,
                               execution_context: Optional[ThreadType] = None,
                               **kwargs: Any) -> str:
        """
        Schedule a periodic task.

        Args:
            interval: Interval in seconds
            func: Function to execute
            *args: Function arguments
            task_id: Optional task ID
            execution_context: Thread context to run in
            **kwargs: Function keyword arguments

        Returns:
            Task identifier
        """
        if not self._initialized:
            raise ThreadManagerError('Thread Manager not initialized', thread_id=None)

        # Generate task ID if not provided
        task_id = task_id or str(uuid.uuid4())

        # Detect if this needs the UI thread
        on_ui_thread = False
        if execution_context == ThreadType.MAIN:
            on_ui_thread = True
        else:
            # Auto-detect UI thread requirements
            for arg in args:
                if is_qt_object(arg):
                    on_ui_thread = True
                    break

            for arg in kwargs.values():
                if is_qt_object(arg):
                    on_ui_thread = True
                    break

        # Register periodic task
        with self._periodic_tasks_lock:
            self._periodic_tasks[task_id] = {
                'interval': interval,
                'func': func,
                'args': args,
                'kwargs': kwargs,
                'last_run': 0,  # Never run
                'on_ui_thread': on_ui_thread
            }

        self._logger.debug(f"Scheduled periodic task {task_id} with interval {interval}s")
        return task_id

    def cancel_periodic_task(self, task_id: str) -> bool:
        """
        Cancel a periodic task.

        Args:
            task_id: Task to cancel

        Returns:
            Whether cancellation was successful
        """
        with self._periodic_tasks_lock:
            if task_id in self._periodic_tasks:
                del self._periodic_tasks[task_id]
                self._logger.debug(f"Cancelled periodic task {task_id}")
                return True
        return False

    def _periodic_task_handler(self) -> None:
        """Thread that handles periodic task execution."""
        self._logger.debug("Periodic task handler started")

        while not self._periodic_stop_event.is_set():
            try:
                current_time = time.time()
                tasks_to_run = []

                # Find tasks that need to run
                with self._periodic_tasks_lock:
                    for task_id, task_info in list(self._periodic_tasks.items()):
                        # Check if it's time to run
                        interval = task_info['interval']
                        last_run = task_info['last_run']

                        if last_run == 0 or (current_time - last_run) >= interval:
                            # Mark as running now
                            task_info['last_run'] = current_time
                            tasks_to_run.append((task_id, task_info))

                # Execute tasks that need to run
                for task_id, task_info in tasks_to_run:
                    try:
                        func = task_info['func']
                        args = task_info['args']
                        kwargs = task_info['kwargs']
                        on_ui_thread = task_info['on_ui_thread']

                        # Submit for execution
                        thread_type = ThreadType.MAIN if on_ui_thread else ThreadType.WORKER
                        self.submit_task(
                            func,
                            *args,
                            name=f"periodic-{task_id}",
                            submitter="periodic_scheduler",
                            execution_context=thread_type,
                            **kwargs
                        )
                    except Exception as e:
                        self._logger.error(
                            f"Error scheduling periodic task {task_id}: {str(e)}",
                            exc_info=True
                        )

                # Sleep a bit but not too long to ensure timely execution
                time.sleep(0.1)

            except Exception as e:
                self._logger.error(
                    f"Error in periodic task handler: {str(e)}",
                    exc_info=True
                )

    def _handle_task_completed(self, task_id: str, result: Any) -> None:
        """
        Handle task completion.

        Args:
            task_id: Completed task ID
            result: Task result
        """
        self._logger.debug(f"Task {task_id} completed successfully")

    def _handle_task_failed(self, task_id: str, error_message: str,
                            error_traceback: str) -> None:
        """
        Handle task failure.

        Args:
            task_id: Failed task ID
            error_message: Error message
            error_traceback: Error traceback
        """
        self._logger.error(
            f"Task {task_id} failed: {error_message}",
            extra={
                'task_id': task_id,
                'error': error_message,
                'traceback': error_traceback
            }
        )

    def _handle_task_cancelled(self, task_id: str) -> None:
        """
        Handle task cancellation.

        Args:
            task_id: Cancelled task ID
        """
        self._logger.debug(f"Task {task_id} was cancelled")

    def _on_config_changed(self, key: str, value: Any) -> None:
        """
        Handle configuration changes.

        Args:
            key: Changed configuration key
            value: New value
        """
        if key == 'thread_pool.worker_threads':
            # qorzen/core/thread_manager.py (continued)
            self._logger.warning(
                'Thread pool size changes require restart to take effect',
                extra={
                    'current_size': self._max_workers,
                    'new_size': value
                }
            )

    def shutdown(self) -> None:
        """Shutdown the thread manager."""
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Thread Manager')

            # Stop periodic task handler
            self._periodic_stop_event.set()
            if self._periodic_thread and self._periodic_thread.is_alive():
                self._periodic_thread.join(timeout=2.0)

            # Clear periodic tasks
            with self._periodic_tasks_lock:
                self._periodic_tasks.clear()

            # Unregister config listener
            self._config_manager.unregister_listener('thread_pool', self._on_config_changed)

            # Shutdown the dispatcher
            self._dispatcher.shutdown()

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
        """
        Get thread manager status.

        Returns:
            Status information dictionary
        """
        status = super().status()

        if self._initialized:
            # Get thread dispatcher status
            with self._periodic_tasks_lock:
                status.update({
                    'thread_pool': {
                        'max_workers': self._max_workers,
                        'is_main_thread': self.is_main_thread()
                    },
                    'periodic_tasks': {
                        'count': len(self._periodic_tasks),
                        'active': self._periodic_thread is not None and self._periodic_thread.is_alive()
                    }
                })

        return status