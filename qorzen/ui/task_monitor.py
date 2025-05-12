from __future__ import annotations

from typing import Dict, Optional, Any
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QScrollArea, QVBoxLayout, QWidget


class TaskProgressWidget(QFrame):
    """Widget to display information about a running task."""

    def __init__(self, task_id: str, plugin_name: str, task_name: str, parent: Optional[QWidget] = None):
        """
        Initialize a task progress widget.

        Args:
            task_id: The ID of the task
            plugin_name: The name of the plugin that owns the task
            task_name: The name of the task
            parent: The parent widget
        """
        super().__init__(parent)
        self.task_id = task_id

        # Configure the frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMaximumHeight(80)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Header layout with task name and status
        header_layout = QHBoxLayout()

        self.task_label = QLabel(f'{plugin_name}: {task_name}')
        self.task_label.setStyleSheet('font-weight: bold;')
        header_layout.addWidget(self.task_label)

        self.status_label = QLabel('Running')
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
        self.message_label = QLabel('')
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

    def update_progress(self, progress: int, message: Optional[str] = None) -> None:
        """
        Update the progress display.

        Args:
            progress: Progress percentage (0-100)
            message: Optional status message
        """
        self.progress_bar.setValue(progress)
        if message:
            self.message_label.setText(message)

    def mark_completed(self) -> None:
        """Mark the task as completed."""
        self.status_label.setText('Completed')
        self.status_label.setStyleSheet('color: green;')
        self.progress_bar.setValue(100)

    def mark_failed(self, error: str) -> None:
        """
        Mark the task as failed.

        Args:
            error: Error message
        """
        self.status_label.setText('Failed')
        self.status_label.setStyleSheet('color: red;')
        self.progress_bar.setValue(100)
        if error:
            self.message_label.setText(f'Error: {error}')
            self.message_label.setStyleSheet('color: red;')

    def mark_cancelled(self) -> None:
        """Mark the task as cancelled."""
        self.status_label.setText('Cancelled')
        self.status_label.setStyleSheet('color: orange;')
        self.progress_bar.setValue(100)


class TaskMonitorWidget(QWidget):
    """Widget to display and monitor running tasks."""

    def __init__(self, event_bus: Any, parent: Optional[QWidget] = None):
        """
        Initialize the task monitor widget.

        Args:
            event_bus: The event bus for subscribing to task events
            parent: The parent widget
        """
        super().__init__(parent)
        self.event_bus = event_bus
        self.tasks: Dict[str, TaskProgressWidget] = {}

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Header
        header = QLabel('Running Tasks')
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet('font-weight: bold;')
        layout.addWidget(header)

        # Create a scrollable area for tasks
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

        # Empty state message
        self.empty_label = QLabel('No tasks running')
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet('color: gray; font-style: italic;')
        self.task_layout.insertWidget(0, self.empty_label)

        # Subscribe to task events
        self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        """Subscribe to task-related events."""
        # Make sure the event_bus is not None
        if not self.event_bus:
            return

        try:
            # Subscribe to task events
            self.event_bus.subscribe(
                event_type='task/started',
                callback=self._on_task_started,
                subscriber_id='task_monitor_widget_started'
            )

            self.event_bus.subscribe(
                event_type='task/progress',
                callback=self._on_task_progress,
                subscriber_id='task_monitor_widget_progress'
            )

            self.event_bus.subscribe(
                event_type='task/completed',
                callback=self._on_task_completed,
                subscriber_id='task_monitor_widget_completed'
            )

            self.event_bus.subscribe(
                event_type='task/failed',
                callback=self._on_task_failed,
                subscriber_id='task_monitor_widget_failed'
            )

            self.event_bus.subscribe(
                event_type='task/cancelled',
                callback=self._on_task_cancelled,
                subscriber_id='task_monitor_widget_cancelled'
            )
        except Exception as e:
            print(f"Error subscribing to task events: {str(e)}")

    def _on_task_started(self, event: Any) -> None:
        """
        Handle task started event.

        Args:
            event: The task started event
        """
        # Extract information from the event
        payload = event.payload
        task_id = payload.get('task_id')

        # Make sure we have a valid task ID
        if not task_id:
            return

        # Get task details
        plugin_name = payload.get('plugin_name', 'Unknown')
        task_name = payload.get('task_name', 'Task')

        # Create a task widget
        task_widget = TaskProgressWidget(task_id, plugin_name, task_name)

        # Add it to the layout
        self.task_layout.insertWidget(0, task_widget)

        # Store it for future updates
        self.tasks[task_id] = task_widget

        # Update the empty state
        self.empty_label.setVisible(len(self.tasks) == 0)

    def _on_task_progress(self, event: Any) -> None:
        """
        Handle task progress event.

        Args:
            event: The task progress event
        """
        # Extract information from the event
        payload = event.payload
        task_id = payload.get('task_id')

        # Make sure we have a valid task ID and it's in our tracking
        if not task_id or task_id not in self.tasks:
            return

        # Update the progress
        progress = payload.get('progress', 0)
        message = payload.get('message', '')
        self.tasks[task_id].update_progress(progress, message)

    def _on_task_completed(self, event: Any) -> None:
        """
        Handle task completed event.

        Args:
            event: The task completed event
        """
        # Extract information from the event
        payload = event.payload
        task_id = payload.get('task_id')

        # Make sure we have a valid task ID and it's in our tracking
        if not task_id or task_id not in self.tasks:
            return

        # Mark the task as completed
        self.tasks[task_id].mark_completed()

        # Schedule the task for removal
        QTimer.singleShot(3000, lambda: self._remove_task(task_id))

    def _on_task_failed(self, event: Any) -> None:
        """
        Handle task failed event.

        Args:
            event: The task failed event
        """
        # Extract information from the event
        payload = event.payload
        task_id = payload.get('task_id')

        # Make sure we have a valid task ID and it's in our tracking
        if not task_id or task_id not in self.tasks:
            return

        # Mark the task as failed
        error = payload.get('error', 'Unknown error')
        self.tasks[task_id].mark_failed(error)

        # Schedule the task for removal (after a longer delay)
        QTimer.singleShot(5000, lambda: self._remove_task(task_id))

    def _on_task_cancelled(self, event: Any) -> None:
        """
        Handle task cancelled event.

        Args:
            event: The task cancelled event
        """
        # Extract information from the event
        payload = event.payload
        task_id = payload.get('task_id')

        # Make sure we have a valid task ID and it's in our tracking
        if not task_id or task_id not in self.tasks:
            return

        # Mark the task as cancelled
        self.tasks[task_id].mark_cancelled()

        # Schedule the task for removal
        QTimer.singleShot(3000, lambda: self._remove_task(task_id))

    def _remove_task(self, task_id: str) -> None:
        """
        Remove a task from the display.

        Args:
            task_id: The ID of the task to remove
        """
        if task_id not in self.tasks:
            return

        # Get the widget
        task_widget = self.tasks[task_id]

        # Remove it from the layout
        self.task_layout.removeWidget(task_widget)

        # Delete the widget
        task_widget.deleteLater()

        # Remove it from tracking
        del self.tasks[task_id]

        # Update the empty state
        self.empty_label.setVisible(len(self.tasks) == 0)

    def cleanup(self) -> None:
        """Clean up resources and unsubscribe from events."""
        # Unsubscribe from events
        if self.event_bus:
            self.event_bus.unsubscribe(subscriber_id='task_monitor_widget_started')
            self.event_bus.unsubscribe(subscriber_id='task_monitor_widget_progress')
            self.event_bus.unsubscribe(subscriber_id='task_monitor_widget_completed')
            self.event_bus.unsubscribe(subscriber_id='task_monitor_widget_failed')
            self.event_bus.unsubscribe(subscriber_id='task_monitor_widget_cancelled')