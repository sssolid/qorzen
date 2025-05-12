from __future__ import annotations

import inspect
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, cast

from qorzen.core.base import QorzenManager
from qorzen.core.thread_manager import ThreadExecutionContext, TaskPriority, TaskProgressReporter
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError


@dataclass
class TaskDefinition:
    """Definition of a task that can be executed by the TaskManager."""

    name: str
    plugin_name: str
    function: Callable
    long_running: bool = True
    needs_progress: bool = True
    priority: TaskPriority = TaskPriority.NORMAL
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager(QorzenManager):
    """
    Manager responsible for executing tasks without blocking the UI.

    TaskManager allows plugins to register and execute tasks that can report
    progress and run in the background without affecting the user experience.
    """

    def __init__(self, application_core: Any, config_manager: Any,
                 logger_manager: Any, event_bus_manager: Any,
                 thread_manager: Any) -> None:
        """
        Initialize the TaskManager.

        Args:
            application_core: Core application instance
            config_manager: Configuration manager
            logger_manager: Logging manager
            event_bus_manager: Event bus manager
            thread_manager: Thread manager
        """
        super().__init__(name="TaskManager")
        self._application_core = application_core
        self._config_manager = config_manager
        self._logger_manager = logger_manager
        self._logger = logger_manager.get_logger("task_manager")
        self._event_bus = event_bus_manager
        self._thread_manager = thread_manager

        self.tasks: Dict[str, Dict[str, TaskDefinition]] = {}
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()

    def initialize(self) -> None:
        """Initialize the TaskManager."""
        try:
            self._logger.info("Task Manager initialized")
            self._initialized = True
            self._healthy = True
        except Exception as e:
            self._logger.error(f"Failed to initialize Task Manager: {str(e)}")
            raise ManagerInitializationError(
                f"Failed to initialize TaskManager: {str(e)}",
                manager_name=self.name
            ) from e

    def register_task(self, plugin_name: str, task_name: str,
                      function: Callable, **properties) -> None:
        """
        Register a task with the TaskManager.

        Args:
            plugin_name: Name of the plugin registering the task
            task_name: Name of the task
            function: Function to execute
            **properties: Additional task properties
        """
        with self.lock:
            plugin_tasks = self.tasks.get(plugin_name, {})
            task_def = TaskDefinition(
                name=task_name,
                plugin_name=plugin_name,
                function=function,
                long_running=properties.get("long_running", True),
                needs_progress=properties.get("needs_progress", True),
                priority=properties.get("priority", TaskPriority.NORMAL),
                description=properties.get("description", ""),
                metadata=properties.get("metadata", {})
            )
            plugin_tasks[task_name] = task_def
            self.tasks[plugin_name] = plugin_tasks
            self._logger.debug(f"Registered task '{task_name}' for plugin '{plugin_name}'")

    def execute_task(self, plugin_name: str, task_name: str, *args: Any, **kwargs: Any) -> str:
        """
        Execute a registered task.

        Args:
            plugin_name: Name of the plugin that registered the task
            task_name: Name of the task to execute
            *args: Arguments for the task function
            **kwargs: Keyword arguments for the task function

        Returns:
            Task ID for tracking the task

        Raises:
            ValueError: If the task is not registered
        """
        with self.lock:
            plugin_tasks = self.tasks.get(plugin_name, {})
            task_def = plugin_tasks.get(task_name)

        if not task_def:
            raise ValueError(f"Task '{task_name}' not registered for plugin '{plugin_name}'")

        task_id = f"{plugin_name}_{task_name}_{uuid.uuid4().hex[:8]}"
        execution_context = (
            ThreadExecutionContext.WORKER_THREAD
            if task_def.long_running
            else ThreadExecutionContext.MAIN_THREAD
        )

        # Ensure we publish task started event on the main thread
        def publish_task_started():
            self._event_bus.publish(
                event_type="task/started",
                source="task_manager",
                payload={
                    "task_id": task_id,
                    "plugin_name": plugin_name,
                    "task_name": task_name,
                    "properties": {
                        "long_running": task_def.long_running,
                        "needs_progress": task_def.needs_progress,
                        "priority": task_def.priority.value,
                        "description": task_def.description
                    }
                }
            )

        if self._thread_manager.is_main_thread():
            publish_task_started()
        else:
            self._thread_manager.run_on_main_thread(publish_task_started)

        # Submit the task to the thread manager
        thread_task_id = self._thread_manager.submit_task(
            self._task_wrapper,
            function=task_def.function,
            args=args,
            kwargs=kwargs,
            task_id=task_id,
            plugin_name=plugin_name,
            task_name=task_name,
            task_def=task_def,
            name=f"{plugin_name}_{task_name}",
            submitter="task_manager",
            priority=task_def.priority,
            execution_context=execution_context
        )

        with self.lock:
            self.running_tasks[task_id] = {
                "thread_task_id": thread_task_id,
                "plugin_name": plugin_name,
                "task_name": task_name,
                "start_time": time.time(),
                "definition": task_def
            }

        return task_id

    def _task_wrapper(self, function: Callable, args: tuple, kwargs: Dict[str, Any],
                      task_id: str, plugin_name: str, task_name: str,
                      task_def: TaskDefinition,
                      progress_reporter: Optional[TaskProgressReporter] = None) -> Any:
        """
        Wrapper function for executing tasks with progress reporting.

        Args:
            function: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            task_id: Task ID
            plugin_name: Plugin name
            task_name: Task name
            task_def: Task definition
            progress_reporter: Progress reporter function

        Returns:
            Result of the function call
        """
        try:
            # If progress reporting is enabled
            if progress_reporter and task_def.needs_progress:
                # Create a thread-safe progress reporting function to pass to the task
                def wrapped_reporter(progress: int, message: Optional[str] = None) -> None:
                    # Always run progress updates on the main thread
                    def update_progress():
                        # Update progress in UI
                        progress_reporter.report_progress(progress, message)

                        # Send event for task monitor
                        self._event_bus.publish(
                            event_type="task/progress",
                            source="task_manager",
                            payload={
                                "task_id": task_id,
                                "plugin_name": plugin_name,
                                "task_name": task_name,
                                "progress": progress,
                                "message": message if message else ""
                            }
                        )

                    # Ensure we're on the main thread
                    if self._thread_manager.is_main_thread():
                        update_progress()
                    else:
                        self._thread_manager.run_on_main_thread(update_progress)

                # Check if the function accepts a progress_reporter parameter
                if "progress_reporter" in inspect.signature(function).parameters:
                    result = function(*args, progress_reporter=wrapped_reporter, **kwargs)
                else:
                    result = function(*args, **kwargs)
            else:
                result = function(*args, **kwargs)

            # Publish task completion event on the main thread
            def publish_completion():
                self._event_bus.publish(
                    event_type="task/completed",
                    source="task_manager",
                    payload={
                        "task_id": task_id,
                        "plugin_name": plugin_name,
                        "task_name": task_name,
                        "result": result
                    }
                )

                with self.lock:
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]

            if self._thread_manager.is_main_thread():
                publish_completion()
            else:
                self._thread_manager.run_on_main_thread(publish_completion)

            return result

        except Exception as e:
            self._logger.error(
                f"Error executing task {task_name} for plugin {plugin_name}: {str(e)}",
                exc_info=True
            )

            # Publish task failure event on the main thread
            def publish_failure():
                self._event_bus.publish(
                    event_type="task/failed",
                    source="task_manager",
                    payload={
                        "task_id": task_id,
                        "plugin_name": plugin_name,
                        "task_name": task_name,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                )

                with self.lock:
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]

            if self._thread_manager.is_main_thread():
                publish_failure()
            else:
                self._thread_manager.run_on_main_thread(publish_failure)

            raise

    def get_running_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about currently running tasks.

        Returns:
            Dictionary mapping task IDs to task information
        """
        with self.lock:
            return {
                task_id: {
                    "plugin_name": info["plugin_name"],
                    "task_name": info["task_name"],
                    "start_time": info["start_time"],
                    "elapsed_time": time.time() - info["start_time"],
                    "properties": {
                        "long_running": info["definition"].long_running,
                        "priority": info["definition"].priority.value,
                        "description": info["definition"].description
                    }
                }
                for task_id, info in self.running_tasks.items()
            }

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            True if the task was cancelled, False otherwise
        """
        with self.lock:
            if task_id not in self.running_tasks:
                return False

            thread_task_id = self.running_tasks[task_id]["thread_task_id"]

        cancelled = self._thread_manager.cancel_task(thread_task_id)

        if cancelled:
            # Publish task cancellation event on the main thread
            def publish_cancellation():
                self._event_bus.publish(
                    event_type="task/cancelled",
                    source="task_manager",
                    payload={"task_id": task_id}
                )

            if self._thread_manager.is_main_thread():
                publish_cancellation()
            else:
                self._thread_manager.run_on_main_thread(publish_cancellation)

            with self.lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

        return cancelled

    def shutdown(self) -> None:
        """Clean up resources and prepare for shutdown."""
        if not self._initialized:
            return

        try:
            self._logger.info("Shutting down Task Manager")
            self._initialized = False
            self._healthy = False
            self._logger.info("Task Manager shut down successfully")

        except Exception as e:
            self._logger.error(f"Failed to shut down Task Manager: {str(e)}")
            raise ManagerShutdownError(
                f"Failed to shut down TaskManager: {str(e)}",
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """
        Get the current status of the task manager.

        Returns:
            Dictionary with status information
        """
        status = super().status()

        if self._initialized:
            with self.lock:
                running_count = len(self.running_tasks)
                total_registered = sum(len(tasks) for tasks in self.tasks.values())

            status.update({
                "tasks": {
                    "running": running_count,
                    "registered": total_registered,
                    "by_plugin": {
                        plugin: len(tasks)
                        for plugin, tasks in self.tasks.items()
                    }
                },
                "healthy": self._initialized and self._healthy
            })

        return status