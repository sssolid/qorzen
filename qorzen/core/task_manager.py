# qorzen/core/task_manager.py
from __future__ import annotations

import inspect
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, cast, Union

from qorzen.core.base import QorzenManager
from qorzen.core.thread_safe_core import (
    ThreadType, TaskPriority, ProgressReporter, ThreadDispatcher, ensure_main_thread
)
from qorzen.core.thread_manager import ThreadManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError


@dataclass
class TaskDefinition:
    """Definition of a task that can be executed."""
    name: str
    plugin_name: str
    function: Callable
    long_running: bool = True
    needs_progress: bool = True
    priority: TaskPriority = TaskPriority.NORMAL
    description: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager(QorzenManager):
    """
    Task manager for handling plugin tasks with proper thread management.

    This implementation ensures plugins never have to worry about what thread they're
    running on, and properly handles all Qt threading concerns automatically.
    """

    def __init__(self,
                 application_core: Any,
                 config_manager: Any,
                 logger_manager: Any,
                 event_bus_manager: Any,
                 thread_manager: ThreadManager) -> None:
        """
        Initialize task manager.

        Args:
            application_core: Application core
            config_manager: Configuration manager
            logger_manager: Logger manager
            event_bus_manager: Event bus manager
            thread_manager: Thread manager
        """
        super().__init__(name="TaskManager")
        self._application_core = application_core
        self._config_manager = config_manager
        self._logger_manager = logger_manager
        self._logger = logger_manager.get_logger('task_manager')
        self._event_bus = event_bus_manager
        self._thread_manager = thread_manager

        # Task registry
        self.tasks: Dict[str, Dict[str, TaskDefinition]] = {}
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()

        # Thread dispatcher
        self._dispatcher = ThreadDispatcher.instance()

    def initialize(self) -> None:
        """Initialize the task manager."""
        try:
            self._logger.info('Task Manager initialized')
            self._initialized = True
            self._healthy = True
        except Exception as e:
            self._logger.error(f'Failed to initialize Task Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize TaskManager: {str(e)}',
                manager_name=self.name
            ) from e

    def register_task(self,
                      plugin_name: str,
                      task_name: str,
                      function: Callable,
                      **properties) -> None:
        """
        Register a task for future execution.

        Args:
            plugin_name: Plugin that owns the task
            task_name: Task name
            function: Task function
            **properties: Additional task properties
        """
        with self.lock:
            plugin_tasks = self.tasks.get(plugin_name, {})

            task_def = TaskDefinition(
                name=task_name,
                plugin_name=plugin_name,
                function=function,
                long_running=properties.get('long_running', True),
                needs_progress=properties.get('needs_progress', True),
                priority=properties.get('priority', TaskPriority.NORMAL),
                description=properties.get('description', ''),
                metadata=properties.get('metadata', {})
            )

            plugin_tasks[task_name] = task_def
            self.tasks[plugin_name] = plugin_tasks

            self._logger.debug(f"Registered task '{task_name}' for plugin '{plugin_name}'")

    def execute_task(self,
                     plugin_name: str,
                     task_name: str,
                     *args: Any,
                     **kwargs: Any) -> str:
        """
        Execute a registered task.

        Args:
            plugin_name: Plugin that owns the task
            task_name: Task to execute
            *args: Task arguments
            **kwargs: Task keyword arguments

        Returns:
            Task identifier
        """
        if not self._initialized:
            raise ValueError("Task Manager not initialized")

        with self.lock:
            plugin_tasks = self.tasks.get(plugin_name, {})
            task_def = plugin_tasks.get(task_name)

            if not task_def:
                raise ValueError(f"Task '{task_name}' not registered for plugin '{plugin_name}'")

        # Generate task ID
        task_id = f'{plugin_name}_{task_name}_{uuid.uuid4().hex[:8]}'

        # Determine execution context
        thread_type = ThreadType.WORKER if task_def.long_running else ThreadType.MAIN

        # Create wrapped task that handles progress reporting and event publishing
        def task_wrapper(progress_reporter: ProgressReporter) -> Any:
            # Publish task started event
            self._event_bus.publish(
                event_type='task/started',
                source='task_manager',
                payload={
                    'task_id': task_id,
                    'plugin_name': plugin_name,
                    'task_name': task_name,
                    'properties': {
                        'long_running': task_def.long_running,
                        'needs_progress': task_def.needs_progress,
                        'priority': task_def.priority.value,
                        'description': task_def.description
                    }
                }
            )

            try:
                # Execute task with progress reporting if needed
                if task_def.needs_progress:
                    if 'progress_reporter' in inspect.signature(task_def.function).parameters:
                        result = task_def.function(*args, progress_reporter=progress_reporter, **kwargs)
                    else:
                        result = task_def.function(*args, **kwargs)
                else:
                    result = task_def.function(*args, **kwargs)

                # Task completed successfully
                with self.lock:
                    if task_id in self.running_tasks:
                        self.running_tasks[task_id]['end_time'] = time.time()
                        self.running_tasks[task_id]['completed'] = True

                # Publish task completed event
                self._event_bus.publish(
                    event_type='task/completed',
                    source='task_manager',
                    payload={
                        'task_id': task_id,
                        'plugin_name': plugin_name,
                        'task_name': task_name,
                        'result': result
                    }
                )

                return result

            except Exception as e:
                # Task failed
                error_traceback = traceback.format_exc()

                with self.lock:
                    if task_id in self.running_tasks:
                        self.running_tasks[task_id]['end_time'] = time.time()
                        self.running_tasks[task_id]['error'] = str(e)
                        self.running_tasks[task_id]['traceback'] = error_traceback

                # Publish task failed event
                self._event_bus.publish(
                    event_type='task/failed',
                    source='task_manager',
                    payload={
                        'task_id': task_id,
                        'plugin_name': plugin_name,
                        'task_name': task_name,
                        'error': str(e),
                        'traceback': error_traceback
                    }
                )

                # Re-raise exception
                raise

        # Submit task
        internal_task_id = self._dispatcher.submit_task(
            task_wrapper,
            task_id=task_id,
            on_ui_thread=(thread_type == ThreadType.MAIN),
            has_progress=task_def.needs_progress,
            on_completed=self._on_task_completed,
            on_failed=self._on_task_failed,
            on_cancelled=self._on_task_cancelled
        )

        # Track running task
        with self.lock:
            self.running_tasks[task_id] = {
                'id': task_id,
                'internal_id': internal_task_id,
                'plugin_name': plugin_name,
                'task_name': task_name,
                'start_time': time.time(),
                'definition': task_def,
                'completed': False
            }

        return task_id

    def _on_task_completed(self, task_id: str, result: Any) -> None:
        """
        Handle task completion.

        Args:
            task_id: Task identifier
            result: Task result
        """
        with self.lock:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def _on_task_failed(self, task_id: str, error_message: str,
                        error_traceback: str) -> None:
        """
        Handle task failure.

        Args:
            task_id: Task identifier
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

        with self.lock:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def _on_task_cancelled(self, task_id: str) -> None:
        """
        Handle task cancellation.

        Args:
            task_id: Task identifier
        """
        with self.lock:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

        # Publish task cancelled event
        self._event_bus.publish(
            event_type='task/cancelled',
            source='task_manager',
            payload={'task_id': task_id}
        )

    def get_running_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about currently running tasks.

        Returns:
            Dictionary of running task information
        """
        with self.lock:
            return {
                task_id: {
                    'plugin_name': info['plugin_name'],
                    'task_name': info['task_name'],
                    'start_time': info['start_time'],
                    'elapsed_time': time.time() - info['start_time'],
                    'properties': {
                        'long_running': info['definition'].long_running,
                        'priority': info['definition'].priority.value,
                        'description': info['definition'].description
                    }
                }
                for task_id, info in self.running_tasks.items()
            }

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: Task to cancel

        Returns:
            Whether cancellation was successful
        """
        with self.lock:
            if task_id not in self.running_tasks:
                return False

            # Get internal task ID
            internal_id = self.running_tasks[task_id].get('internal_id')

        # Cancel task with dispatcher
        cancelled = self._dispatcher.cancel_task(task_id)

        if cancelled:
            # Publish task cancelled event
            self._event_bus.publish(
                event_type='task/cancelled',
                source='task_manager',
                payload={'task_id': task_id}
            )

            with self.lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

        return cancelled

    def shutdown(self) -> None:
        """Shutdown the task manager."""
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Task Manager')

            # Cancel all running tasks
            with self.lock:
                for task_id in list(self.running_tasks.keys()):
                    self.cancel_task(task_id)

            self._initialized = False
            self._healthy = False
            self._logger.info('Task Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Task Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down TaskManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """
        Get task manager status.

        Returns:
            Status information dictionary
        """
        status = super().status()

        if self._initialized:
            with self.lock:
                running_count = len(self.running_tasks)
                total_registered = sum(len(tasks) for tasks in self.tasks.values())

            status.update({
                'tasks': {
                    'running': running_count,
                    'registered': total_registered,
                    'by_plugin': {
                        plugin: len(tasks)
                        for plugin, tasks in self.tasks.items()
                    }
                },
                'healthy': self._initialized and self._healthy
            })

        return status