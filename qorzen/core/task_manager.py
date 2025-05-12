from __future__ import annotations

import inspect
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

from qorzen.core import QorzenManager
from qorzen.core.thread_manager import ThreadExecutionContext, TaskPriority, TaskProgressReporter
from qorzen.core.event_model import EventType
from qorzen.utils import ManagerInitializationError, ManagerShutdownError


@dataclass
class TaskDefinition:
    """Defines a plugin task with execution properties."""
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
    Central system for task registration and execution.

    Responsibilities:
    - Task registration and tracking
    - Thread selection and execution
    - Progress reporting and events
    - Error handling
    """

    def __init__(self, application_core: Any,
                 config_manager: Any,
                 logger_manager: Any,
                 event_bus_manager: Any,
                 thread_manager: Any) -> None:
        """
        Initialize the task manager.

        Args:
            application_core: ApplicationCore for application-wide services
            config_manager: ConfigurationManager for configuration management
            thread_manager: ThreadManager for task execution
            event_bus_manager: EventBusManager for events
            logger_manager: LoggingManager for logging
        """
        super().__init__(name='TaskManager')
        # Core service references
        self._application_core = application_core
        self._config_manager = config_manager
        self._logger_manager = logger_manager
        self._logger = logger_manager.get_logger('task_manager')
        self._event_bus = event_bus_manager
        self._thread_manager = thread_manager

        self.tasks: Dict[str, Dict[str, TaskDefinition]] = {}  # {plugin_name: {task_name: TaskDefinition}}
        self.running_tasks: Dict[str, Dict[str, Any]] = {}  # {task_id: task_info}
        self.lock = threading.RLock()

    def initialize(self) -> None:
        try:
            # TODO: Add more
            plugin_config = self._config_manager.get('plugins', {})
        except Exception as e:
            self._logger.error(f'Failed to initialize Task Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize TaskManager: {str(e)}',
                manager_name=self.name
            ) from e

    def register_task(self, plugin_name: str, task_name: str, function: Callable, **properties) -> None:
        """
        Register a task definition.

        Args:
            plugin_name: Name of the plugin registering the task
            task_name: Name of the task
            function: Function to execute
            **properties: Task properties including:
                - long_running: If True, runs on worker thread
                - needs_progress: If True, provides progress reporting
                - priority: Task priority (LOW, NORMAL, HIGH, CRITICAL)
                - description: Human-readable description
                - metadata: Additional task metadata
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

            self._logger.debug(
                f"Registered task '{task_name}' for plugin '{plugin_name}'"
            )

    def execute_task(self, plugin_name: str, task_name: str, *args: Any, **kwargs: Any) -> str:
        """
        Execute a registered task with appropriate thread selection.

        Args:
            plugin_name: Name of the plugin
            task_name: Name of the registered task
            *args: Arguments for the task
            **kwargs: Keyword arguments for the task

        Returns:
            str: Task ID for the running task

        Raises:
            ValueError: If the task is not registered
        """
        with self.lock:
            plugin_tasks = self.tasks.get(plugin_name, {})
            task_def = plugin_tasks.get(task_name)

        if not task_def:
            raise ValueError(f"Task '{task_name}' not registered for plugin '{plugin_name}'")

        # Create unique task ID
        task_id = f"{plugin_name}_{task_name}_{uuid.uuid4().hex[:8]}"

        # Determine execution context based on task properties
        execution_context = (
            ThreadExecutionContext.WORKER_THREAD
            if task_def.long_running
            else ThreadExecutionContext.MAIN_THREAD
        )

        # Publish task started event
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

        # Submit task to thread manager
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

        # Track running task
        with self.lock:
            self.running_tasks[task_id] = {
                "thread_task_id": thread_task_id,
                "plugin_name": plugin_name,
                "task_name": task_name,
                "start_time": time.time(),
                "definition": task_def
            }

        return task_id

    def _task_wrapper(self, function: Callable, args: Tuple, kwargs: Dict[str, Any],
                      task_id: str, plugin_name: str, task_name: str,
                      task_def: TaskDefinition, progress_reporter: Optional[TaskProgressReporter] = None) -> Any:
        """
        Wrapper for task execution with progress reporting and events.

        Args:
            function: The task function to execute
            args: Arguments for the function
            kwargs: Keyword arguments for the function
            task_id: Unique ID for this task execution
            plugin_name: Name of the plugin
            task_name: Name of the task
            task_def: Task definition
            progress_reporter: Progress reporter from thread manager

        Returns:
            Any: Result of the task function

        Raises:
            Exception: Any exception from the task function
        """
        try:
            # Set up progress reporting if needed
            if progress_reporter and task_def.needs_progress:
                # Create a progress reporter that publishes events
                def wrapped_reporter(progress: int, message: Optional[str] = None) -> None:
                    # Report to thread manager
                    progress_reporter.report_progress(progress, message)

                    # Publish progress event
                    self._event_bus.publish(
                        event_type="task/progress",
                        source="task_manager",
                        payload={
                            "task_id": task_id,
                            "plugin_name": plugin_name,
                            "task_name": task_name,
                            "progress": progress,
                            "message": message
                        }
                    )

                # Check if function accepts progress_reporter parameter
                if "progress_reporter" in inspect.signature(function).parameters:
                    # Execute with progress reporting
                    result = function(*args, progress_reporter=wrapped_reporter, **kwargs)
                else:
                    # Execute without progress reporting
                    result = function(*args, **kwargs)
            else:
                # Execute without progress reporting
                result = function(*args, **kwargs)

            # Publish completion event
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

            # Remove from running tasks
            with self.lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

            return result

        except Exception as e:
            # Log error
            self._logger.error(
                f"Error executing task {task_name} for plugin {plugin_name}: {str(e)}",
                exc_info=True
            )

            # Publish error event
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

            # Remove from running tasks
            with self.lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

            # Re-raise exception
            raise

    def get_running_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about currently running tasks.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping task IDs to task info
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
            bool: True if the task was cancelled, False otherwise
        """
        with self.lock:
            if task_id not in self.running_tasks:
                return False

            thread_task_id = self.running_tasks[task_id]["thread_task_id"]

        # Try to cancel the task
        cancelled = self._thread_manager.cancel_task(thread_task_id)

        if cancelled:
            # Publish task cancelled event
            self._event_bus.publish(
                event_type="task/cancelled",
                source="task_manager",
                payload={"task_id": task_id}
            )

            # Remove from running tasks
            with self.lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

        return cancelled

    def shutdown(self) -> None:
        """Shut down the Task Manager.



        Raises:
            ManagerShutdownError: If shutdown fails.
        """
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
                manager_name=self.name,
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the Task Manager.

        Returns:
            Dict[str, Any]: Status information about the Task Manager.
        """
        status = super().status()

        if self._initialized:
            status.update(
                {
                    "tasks": {
                        "running": str(len(self.running_tasks.items())),
                    }
                }
            )

        return status
