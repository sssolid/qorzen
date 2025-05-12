from __future__ import annotations

from typing import Dict, Optional, Any

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar,
    QScrollArea, QVBoxLayout, QWidget
)


class TaskMonitorWidget(QWidget):
    """
    Widget for displaying and monitoring running tasks.

    Shows all running tasks with their progress in a scrollable list.
    """

    def __init__(self, event_bus: Any, parent: Optional[QWidget] = None):
        """
        Initialize the task monitor.

        Args:
            event_bus: Event bus for task events
            parent: Parent widget
        """
        super().__init__(parent)
        self.event_bus = event_bus
        self.tasks: Dict[str, TaskProgressWidget] = {}  # task_id -> TaskProgressWidget

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Header
        header = QLabel("Running Tasks")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        # Task container (scrollable)
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

        # Empty state label
        self.empty_label = QLabel("No tasks running")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; font-style: italic;")
        self.task_layout.insertWidget(0, self.empty_label)

        # Connect to events
        self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        """Subscribe to task events"""
        self.event_bus.subscribe(
            event_type="task/started",
            callback=self._on_task_started,
            subscriber_id="task_monitor_widget"
        )

        self.event_bus.subscribe(
            event_type="task/progress",
            callback=self._on_task_progress,
            subscriber_id="task_monitor_widget"
        )

        self.event_bus.subscribe(
            event_type="task/completed",
            callback=self._on_task_completed,
            subscriber_id="task_monitor_widget"
        )

        self.event_bus.subscribe(
            event_type="task/failed",
            callback=self._on_task_failed,
            subscriber_id="task_monitor_widget"
        )

        self.event_bus.subscribe(
            event_type="task/cancelled",
            callback=self._on_task_cancelled,
            subscriber_id="task_monitor_widget"
        )

    def _on_task_started(self, event: Any) -> None:
        """Handle task started event"""
        payload = event.payload
        task_id = payload.get("task_id")
        plugin_name = payload.get("plugin_name")
        task_name = payload.get("task_name")

        # Create task widget
        task_widget = TaskProgressWidget(
            task_id, plugin_name, task_name
        )

        # Add to layout
        self.task_layout.insertWidget(0, task_widget)
        self.tasks[task_id] = task_widget

        # Update empty state
        self.empty_label.setVisible(len(self.tasks) == 0)

    def _on_task_progress(self, event: Any) -> None:
        """Handle task progress event"""
        payload = event.payload
        task_id = payload.get("task_id")
        progress = payload.get("progress", 0)
        message = payload.get("message", "")

        if task_id in self.tasks:
            self.tasks[task_id].update_progress(progress, message)

    def _on_task_completed(self, event: Any) -> None:
        """Handle task completed event"""
        payload = event.payload
        task_id = payload.get("task_id")

        if task_id in self.tasks:
            # Mark task as completed
            self.tasks[task_id].mark_completed()

            # Schedule removal
            QTimer.singleShot(3000, lambda: self._remove_task(task_id))

    def _on_task_failed(self, event: Any) -> None:
        """Handle task failed event"""
        payload = event.payload
        task_id = payload.get("task_id")
        error = payload.get("error", "Unknown error")

        if task_id in self.tasks:
            # Mark task as failed
            self.tasks[task_id].mark_failed(error)

            # Schedule removal (longer time for errors)
            QTimer.singleShot(5000, lambda: self._remove_task(task_id))

    def _on_task_cancelled(self, event: Any) -> None:
        """Handle task cancelled event"""
        payload = event.payload
        task_id = payload.get("task_id")

        if task_id in self.tasks:
            # Mark task as cancelled
            self.tasks[task_id].mark_cancelled()

            # Schedule removal
            QTimer.singleShot(3000, lambda: self._remove_task(task_id))

    def _remove_task(self, task_id: str) -> None:
        """Remove a task widget"""
        if task_id in self.tasks:
            # Remove widget
            task_widget = self.tasks[task_id]
            self.task_layout.removeWidget(task_widget)
            task_widget.deleteLater()
            del self.tasks[task_id]

            # Update empty state
            self.empty_label.setVisible(len(self.tasks) == 0)

    def cleanup(self) -> None:
        """Clean up event subscriptions"""
        self.event_bus.unsubscribe(subscriber_id="task_monitor_widget")


class TaskProgressWidget(QFrame):
    """Widget showing progress for a single task"""

    def __init__(self, task_id: str, plugin_name: str, task_name: str, parent: Optional[QWidget] = None):
        """
        Initialize task progress widget.

        Args:
            task_id: Unique ID for the task
            plugin_name: Name of the plugin
            task_name: Name of the task
            parent: Parent widget
        """
        super().__init__(parent)
        self.task_id = task_id

        # Setup appearance
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMaximumHeight(80)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Header row
        header_layout = QHBoxLayout()

        # Task label
        self.task_label = QLabel(f"{plugin_name}: {task_name}")
        self.task_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.task_label)

        # Status label
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

        # Message row
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

    def update_progress(self, progress: int, message: Optional[str] = None) -> None:
        """
        Update task progress.

        Args:
            progress: Progress value (0-100)
            message: Optional status message
        """
        self.progress_bar.setValue(progress)

        if message:
            self.message_label.setText(message)

    def mark_completed(self) -> None:
        """Mark task as completed"""
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet("color: green;")
        self.progress_bar.setValue(100)

    def mark_failed(self, error: str) -> None:
        """
        Mark task as failed.

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
        """Mark task as cancelled"""
        self.status_label.setText("Cancelled")
        self.status_label.setStyleSheet("color: orange;")
        self.progress_bar.setValue(100)