from __future__ import annotations

import asyncio
from typing import Dict, Optional, Any, List

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QScrollArea,
    QVBoxLayout, QWidget, QMessageBox
)

from qorzen.ui.ui_component import AsyncTaskSignals


class TaskProgressWidget(QFrame):
    """Widget for displaying a task's progress."""

    def __init__(
            self,
            task_id: str,
            plugin_name: str,
            task_name: str,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize a task progress widget.

        Args:
            task_id: Unique task identifier
            plugin_name: Name of the plugin that owns the task
            task_name: Display name of the task
            parent: Parent widget
        """
        super().__init__(parent)
        self.task_id = task_id
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMaximumHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Header with task name and status
        header_layout = QHBoxLayout()

        self.task_label = QLabel(f"{plugin_name}: {task_name}")
        self.task_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.task_label)

        self.status_label = QLabel("Running")
        self.status_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Message label
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

    def update_progress(self, progress: int, message: Optional[str] = None) -> None:
        """
        Update the task progress.

        Args:
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        self.progress_bar.setValue(progress)
        if message:
            self.message_label.setText(message)

    def mark_completed(self) -> None:
        """Mark the task as completed."""
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet("color: green;")
        self.progress_bar.setValue(100)

    def mark_failed(self, error: str) -> None:
        """
        Mark the task as failed.

        Args:
            error: Error message
        """
        self.status_label.setText("Failed")
        self.status_label.setStyleSheet("color: red;")
        self.progress_bar.setValue(100)
        if error:
            self.message_label.setText(f"Error: {error}")
            self.message_label.setStyleSheet("color: red;")

    def mark_cancelled(self) -> None:
        """Mark the task as cancelled."""
        self.status_label.setText("Cancelled")
        self.status_label.setStyleSheet("color: orange;")
        self.progress_bar.setValue(100)


class TaskMonitorWidget(QWidget):
    """Widget for monitoring all running tasks."""

    def __init__(self, event_bus_manager: Any, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the task monitor widget.

        Args:
            event_bus_manager: Reference to the event bus manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.event_bus_manager = event_bus_manager
        self.tasks: Dict[str, TaskProgressWidget] = {}

        # Set up the UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        header = QLabel("Running Tasks")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(2, 2, 2, 2)
        self.task_layout.setSpacing(2)
        self.task_layout.addStretch()

        scroll_area.setWidget(self.task_container)
        layout.addWidget(scroll_area)

        # "No tasks" label
        self.empty_label = QLabel("No tasks running")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; font-style: italic;")
        self.task_layout.insertWidget(0, self.empty_label)

        # Set up async handling
        self._async_signals = AsyncTaskSignals()
        self._async_signals.result_ready.connect(self._on_async_result)
        self._async_signals.error.connect(self._on_async_error)
        self._running_tasks: Dict[str, asyncio.Task] = {}

        # Subscribe to events
        self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        """Subscribe to task-related events from the event bus."""
        self._start_async_task("subscribe_events", self._async_subscribe_to_events)

    async def _async_subscribe_to_events(self) -> List[str]:
        """
        Asynchronously subscribe to all task-related events.

        Returns:
            List of subscription IDs
        """
        if not self.event_bus_manager:
            return []

        try:
            subscription_ids = []

            subscription_ids.append(
                await self.event_bus_manager.subscribe(
                    event_type="task/started",
                    callback=self._on_task_started,
                    subscriber_id="task_monitor_widget_started"
                )
            )

            subscription_ids.append(
                await self.event_bus_manager.subscribe(
                    event_type="task/progress",
                    callback=self._on_task_progress,
                    subscriber_id="task_monitor_widget_progress"
                )
            )

            subscription_ids.append(
                await self.event_bus_manager.subscribe(
                    event_type="task/completed",
                    callback=self._on_task_completed,
                    subscriber_id="task_monitor_widget_completed"
                )
            )

            subscription_ids.append(
                await self.event_bus_manager.subscribe(
                    event_type="task/failed",
                    callback=self._on_task_failed,
                    subscriber_id="task_monitor_widget_failed"
                )
            )

            subscription_ids.append(
                await self.event_bus_manager.subscribe(
                    event_type="task/cancelled",
                    callback=self._on_task_cancelled,
                    subscriber_id="task_monitor_widget_cancelled"
                )
            )

            return subscription_ids

        except Exception as e:
            print(f"Error subscribing to task events: {str(e)}")
            raise

    async def _on_task_started(self, event: Any) -> None:
        """
        Handle task started event.

        Args:
            event: Task started event
        """
        payload = event.payload
        task_id = payload.get("task_id")

        if not task_id:
            return

        # Send to UI thread via signals
        self._async_signals.result_ready.emit({
            "task_id": "task_started",
            "result": {
                "task_id": task_id,
                "plugin_name": payload.get("plugin_id"),
                "task_name": payload.get("name", "Task")
            }
        })

    async def _on_task_progress(self, event: Any) -> None:
        """
        Handle task progress event.

        Args:
            event: Task progress event
        """
        payload = event.payload
        task_id = payload.get("task_id")

        if not task_id:
            return

        # Send to UI thread via signals
        self._async_signals.result_ready.emit({
            "task_id": "task_progress",
            "result": {
                "task_id": task_id,
                "progress": payload.get("progress", 0),
                "message": payload.get("message", "")
            }
        })

    async def _on_task_completed(self, event: Any) -> None:
        """
        Handle task completed event.

        Args:
            event: Task completed event
        """
        payload = event.payload
        task_id = payload.get("task_id")

        if not task_id:
            return

        # Send to UI thread via signals
        self._async_signals.result_ready.emit({
            "task_id": "task_completed",
            "result": {
                "task_id": task_id
            }
        })

    async def _on_task_failed(self, event: Any) -> None:
        """
        Handle task failed event.

        Args:
            event: Task failed event
        """
        payload = event.payload
        task_id = payload.get("task_id")

        if not task_id:
            return

        # Send to UI thread via signals
        self._async_signals.result_ready.emit({
            "task_id": "task_failed",
            "result": {
                "task_id": task_id,
                "error": payload.get("error", "Unknown error")
            }
        })

    async def _on_task_cancelled(self, event: Any) -> None:
        """
        Handle task cancelled event.

        Args:
            event: Task cancelled event
        """
        payload = event.payload
        task_id = payload.get("task_id")

        if not task_id:
            return

        # Send to UI thread via signals
        self._async_signals.result_ready.emit({
            "task_id": "task_cancelled",
            "result": {
                "task_id": task_id
            }
        })

    def _on_async_result(self, result_data: Dict[str, Any]) -> None:
        """
        Handle results from async operations.

        Args:
            result_data: Dictionary with task ID and result
        """
        task_id = result_data.get("task_id", "")
        result = result_data.get("result", {})

        if task_id == "task_started":
            self._handle_task_started(
                result.get("task_id", ""),
                result.get("plugin_name", "Unknown"),
                result.get("task_name", "Task")
            )
        elif task_id == "task_progress":
            self._handle_task_progress(
                result.get("task_id", ""),
                result.get("progress", 0),
                result.get("message", "")
            )
        elif task_id == "task_completed":
            self._handle_task_completed(result.get("task_id", ""))
        elif task_id == "task_failed":
            self._handle_task_failed(
                result.get("task_id", ""),
                result.get("error", "Unknown error")
            )
        elif task_id == "task_cancelled":
            self._handle_task_cancelled(result.get("task_id", ""))

    def _on_async_error(self, error_msg: str, traceback_str: str) -> None:
        """
        Handle errors from async operations.

        Args:
            error_msg: Error message
            traceback_str: Exception traceback as string
        """
        print(f"Task monitor error: {error_msg}\n{traceback_str}")

    def _handle_task_started(self, task_id: str, plugin_name: str, task_name: str) -> None:
        """
        Handle task started in the UI thread.

        Args:
            task_id: Task ID
            plugin_name: Plugin name
            task_name: Task name
        """
        task_widget = TaskProgressWidget(task_id, plugin_name, task_name)
        self.task_layout.insertWidget(0, task_widget)
        self.tasks[task_id] = task_widget
        self.empty_label.setVisible(len(self.tasks) == 0)

    def _handle_task_progress(self, task_id: str, progress: int, message: str) -> None:
        """
        Handle task progress in the UI thread.

        Args:
            task_id: Task ID
            progress: Progress percentage
            message: Progress message
        """
        if task_id not in self.tasks:
            return

        self.tasks[task_id].update_progress(progress, message)

    def _handle_task_completed(self, task_id: str) -> None:
        """
        Handle task completed in the UI thread.

        Args:
            task_id: Task ID
        """
        if task_id not in self.tasks:
            return

        self.tasks[task_id].mark_completed()
        QTimer.singleShot(3000, lambda: self._remove_task(task_id))

    def _handle_task_failed(self, task_id: str, error: str) -> None:
        """
        Handle task failed in the UI thread.

        Args:
            task_id: Task ID
            error: Error message
        """
        if task_id not in self.tasks:
            return

        self.tasks[task_id].mark_failed(error)
        QTimer.singleShot(5000, lambda: self._remove_task(task_id))

    def _handle_task_cancelled(self, task_id: str) -> None:
        """
        Handle task cancelled in the UI thread.

        Args:
            task_id: Task ID
        """
        if task_id not in self.tasks:
            return

        self.tasks[task_id].mark_cancelled()
        QTimer.singleShot(3000, lambda: self._remove_task(task_id))

    def _remove_task(self, task_id: str) -> None:
        """
        Remove a task widget from the display.

        Args:
            task_id: Task ID to remove
        """
        if task_id not in self.tasks:
            return

        task_widget = self.tasks[task_id]
        self.task_layout.removeWidget(task_widget)
        task_widget.deleteLater()
        del self.tasks[task_id]
        self.empty_label.setVisible(len(self.tasks) == 0)

    def _start_async_task(
            self,
            task_id: str,
            coroutine_func: Any,
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Start an asynchronous task.

        Args:
            task_id: Task identifier
            coroutine_func: Async function to run
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        # Cancel existing task with same ID if it exists
        if task_id in self._running_tasks and not self._running_tasks[task_id].done():
            self._running_tasks[task_id].cancel()

        task = asyncio.create_task(self._execute_async_task(
            task_id, coroutine_func, *args, **kwargs
        ))
        self._running_tasks[task_id] = task

    async def _execute_async_task(
            self,
            task_id: str,
            coroutine_func: Any,
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Execute an asynchronous task and handle signals.

        Args:
            task_id: Task identifier
            coroutine_func: Async function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        try:
            result = await coroutine_func(*args, **kwargs)
            # Use QtCore.Qt.QueuedConnection for thread safety
            self._async_signals.result_ready.emit({
                "task_id": task_id,
                "result": result
            })
        except asyncio.CancelledError:
            # Task was cancelled, no need to emit signals
            pass
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            self._async_signals.error.emit(str(e), tb_str)
        finally:
            # Clean up the task reference
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    def cleanup(self) -> None:
        """Clean up resources when the widget is being destroyed."""
        # Cancel all running tasks
        for task in list(self._running_tasks.values()):
            if not task.done():
                task.cancel()

        # Unsubscribe from event bus
        if self.event_bus_manager:
            self._start_async_task(
                "unsubscribe",
                self._async_unsubscribe_from_events
            )

    async def _async_unsubscribe_from_events(self) -> None:
        """Asynchronously unsubscribe from all task events."""
        if self.event_bus_manager:
            try:
                await self.event_bus_manager.unsubscribe(subscriber_id="task_monitor_widget_started")
                await self.event_bus_manager.unsubscribe(subscriber_id="task_monitor_widget_progress")
                await self.event_bus_manager.unsubscribe(subscriber_id="task_monitor_widget_completed")
                await self.event_bus_manager.unsubscribe(subscriber_id="task_monitor_widget_failed")
                await self.event_bus_manager.unsubscribe(subscriber_id="task_monitor_widget_cancelled")
            except Exception as e:
                print(f"Error unsubscribing from task events: {str(e)}")