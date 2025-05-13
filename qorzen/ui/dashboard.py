from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QMessageBox
)

from qorzen.ui.ui_component import AsyncTaskSignals


class SystemStatusTreeWidget(QTreeWidget):
    """Tree widget for displaying system component status."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the system status tree widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setHeaderLabels(["Component", "Status"])
        self.setAlternatingRowColors(True)
        self.setExpandsOnDoubleClick(True)
        self.setAnimated(True)
        self.setSortingEnabled(False)

        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self._expanded_items: Dict[str, bool] = {}

    def _get_status_icon(self, status: Optional[bool]) -> QIcon:
        """
        Get an icon representing a status.

        Args:
            status: Status value (True=healthy, False=unhealthy, None=unknown)

        Returns:
            QIcon representing the status
        """
        if status is True:
            return QIcon.fromTheme("emblem-default", QIcon())
        elif status is False:
            return QIcon.fromTheme("emblem-important", QIcon())
        else:
            return QIcon.fromTheme("emblem-question", QIcon())

    def get_item_path(self, item: QTreeWidgetItem) -> str:
        """
        Get the full path of a tree item.

        Args:
            item: Tree widget item

        Returns:
            Path string representing the item's position in the tree
        """
        path = []
        current = item
        while current:
            path.insert(0, current.text(0))
            current = current.parent()
        return "/".join(path)

    def save_expanded_state(self) -> None:
        """Save the expanded state of all items."""
        self._expanded_items.clear()
        for i in range(self.topLevelItemCount()):
            self._save_expanded_state_recursive(self.topLevelItem(i))

    def _save_expanded_state_recursive(self, item: QTreeWidgetItem) -> None:
        """
        Recursively save expanded state of an item and its children.

        Args:
            item: Tree widget item
        """
        path = self.get_item_path(item)
        self._expanded_items[path] = item.isExpanded()
        for i in range(item.childCount()):
            self._save_expanded_state_recursive(item.child(i))

    def restore_expanded_state(self) -> None:
        """Restore the expanded state of all items."""
        for i in range(self.topLevelItemCount()):
            self._restore_expanded_state_recursive(self.topLevelItem(i))

    def _restore_expanded_state_recursive(self, item: QTreeWidgetItem) -> None:
        """
        Recursively restore expanded state of an item and its children.

        Args:
            item: Tree widget item
        """
        path = self.get_item_path(item)
        if path in self._expanded_items:
            item.setExpanded(self._expanded_items[path])
        for i in range(item.childCount()):
            self._restore_expanded_state_recursive(item.child(i))

    def update_system_status(self, status: Dict[str, Any]) -> None:
        """
        Update the tree with system status information.

        Args:
            status: Dictionary containing system status information
        """
        self.save_expanded_state()
        self.clear()

        app_item = QTreeWidgetItem([
            "Application Core",
            "Active" if status.get("initialized", False) else "Inactive"
        ])
        app_item.setIcon(1, self._get_status_icon(status.get("initialized", None)))
        self.addTopLevelItem(app_item)

        if "managers" in status:
            for manager_name, manager_status in status["managers"].items():
                manager_item = QTreeWidgetItem([
                    manager_name,
                    "Healthy" if manager_status.get("healthy", False) else "Unhealthy"
                ])
                manager_item.setIcon(1, self._get_status_icon(manager_status.get("healthy", None)))
                app_item.addChild(manager_item)

                for key, value in manager_status.items():
                    if key not in ("name", "initialized", "healthy"):
                        if isinstance(value, dict):
                            sub_item = QTreeWidgetItem([key, ""])
                            manager_item.addChild(sub_item)

                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, dict):
                                    sub_sub_item = QTreeWidgetItem([sub_key, ""])
                                    sub_item.addChild(sub_sub_item)

                                    for sub_sub_key, sub_sub_value in sub_value.items():
                                        sub_sub_item.addChild(QTreeWidgetItem([
                                            sub_sub_key, str(sub_sub_value)
                                        ]))
                                else:
                                    sub_item.addChild(QTreeWidgetItem([sub_key, str(sub_value)]))
                        else:
                            manager_item.addChild(QTreeWidgetItem([key, str(value)]))

        self.restore_expanded_state()


class MetricsWidget(QWidget):
    """Widget for displaying system metrics."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the metrics widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the metrics widget UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self._create_system_metrics(main_layout)
        main_layout.addStretch()

    def _create_system_metrics(self, parent_layout: QVBoxLayout) -> None:
        """
        Create the system metrics section.

        Args:
            parent_layout: Parent layout to add metrics to
        """
        section_label = QLabel("System Metrics")
        section_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        parent_layout.addWidget(section_label)

        metrics_frame = QFrame()
        metrics_frame.setFrameShape(QFrame.StyledPanel)
        metrics_frame.setFrameShadow(QFrame.Raised)
        metrics_layout = QFormLayout(metrics_frame)
        metrics_layout.setContentsMargins(10, 10, 10, 10)
        metrics_layout.setSpacing(10)

        # CPU metrics
        self._cpu_label = QLabel("N/A")
        self._cpu_progress = QProgressBar()
        self._cpu_progress.setRange(0, 100)
        self._cpu_progress.setValue(0)
        cpu_widget = QWidget()
        cpu_layout = QHBoxLayout(cpu_widget)
        cpu_layout.setContentsMargins(0, 0, 0, 0)
        cpu_layout.addWidget(self._cpu_progress)
        cpu_layout.addWidget(self._cpu_label)
        metrics_layout.addRow("CPU Usage:", cpu_widget)

        # Memory metrics
        self._memory_label = QLabel("N/A")
        self._memory_progress = QProgressBar()
        self._memory_progress.setRange(0, 100)
        self._memory_progress.setValue(0)
        memory_widget = QWidget()
        memory_layout = QHBoxLayout(memory_widget)
        memory_layout.setContentsMargins(0, 0, 0, 0)
        memory_layout.addWidget(self._memory_progress)
        memory_layout.addWidget(self._memory_label)
        metrics_layout.addRow("Memory Usage:", memory_widget)

        # Disk metrics
        self._disk_label = QLabel("N/A")
        self._disk_progress = QProgressBar()
        self._disk_progress.setRange(0, 100)
        self._disk_progress.setValue(0)
        disk_widget = QWidget()
        disk_layout = QHBoxLayout(disk_widget)
        disk_layout.setContentsMargins(0, 0, 0, 0)
        disk_layout.addWidget(self._disk_progress)
        disk_layout.addWidget(self._disk_label)
        metrics_layout.addRow("Disk Usage:", disk_widget)

        parent_layout.addWidget(metrics_frame)

    def _set_progress_color(self, progress_bar: QProgressBar, value: float) -> None:
        """
        Set progress bar color based on the value.

        Args:
            progress_bar: Progress bar to modify
            value: Current value (0-100)
        """
        if value < 60:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        elif value < 80:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
        else:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Update the metrics display.

        Args:
            metrics: Dictionary containing system metrics
        """
        if "system" in metrics:
            system_metrics = metrics["system"]

            if "cpu" in system_metrics and "percent" in system_metrics["cpu"]:
                cpu_percent = system_metrics["cpu"]["percent"]
                self._cpu_label.setText(f"{cpu_percent:.1f}%")
                self._cpu_progress.setValue(int(cpu_percent))
                self._set_progress_color(self._cpu_progress, cpu_percent)

            if "memory" in system_metrics and "percent" in system_metrics["memory"]:
                memory_percent = system_metrics["memory"]["percent"]
                self._memory_label.setText(f"{memory_percent:.1f}%")
                self._memory_progress.setValue(int(memory_percent))
                self._set_progress_color(self._memory_progress, memory_percent)

            if "disk" in system_metrics and "percent" in system_metrics["disk"]:
                disk_percent = system_metrics["disk"]["percent"]
                self._disk_label.setText(f"{disk_percent:.1f}%")
                self._disk_progress.setValue(int(disk_percent))
                self._set_progress_color(self._disk_progress, disk_percent)


class DashboardWidget(QWidget):
    """Main dashboard widget for system status and metrics."""

    def __init__(self, app_core: Any, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the dashboard widget.

        Args:
            app_core: Application core reference
            parent: Parent widget
        """
        super().__init__(parent)
        self._app_core = app_core
        self._config_manager = app_core.get_manager("config_manager")
        self._event_bus_manager = app_core.get_manager("event_bus_manager")
        self._monitoring_manager = app_core.get_manager("monitoring_manager")

        if app_core.get_manager("logging_manager"):
            self._logger = app_core.get_manager("logging_manager").get_logger("dashboard")
        else:
            import logging
            self._logger = logging.getLogger("dashboard")

        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._async_signals = AsyncTaskSignals()
        self._async_signals.result_ready.connect(self._on_async_result)
        self._async_signals.error.connect(self._on_async_error)

        self._setup_ui()

        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start(5000)

        # Initial status update
        self._update_status()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._update_timer.stop()
        # cancel any in‐flight async tasks
        for t in self._running_tasks.values():
            if not t.done():
                t.cancel()

    def _setup_ui(self) -> None:
        """Set up the dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title
        title_label = QLabel("System Dashboard")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Last update label
        self._last_update_label = QLabel("Last updated: Never")
        self._last_update_label.setAlignment(Qt.AlignRight)
        self._last_update_label.setStyleSheet("color: #666;")
        main_layout.addWidget(self._last_update_label)

        # Main splitter for status and metrics
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter, 1)

        # Status section
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)

        status_header = QLabel("System Status")
        status_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        status_layout.addWidget(status_header)

        self._status_tree = SystemStatusTreeWidget()
        self._status_tree.setMinimumHeight(300)
        status_layout.addWidget(self._status_tree, 1)

        splitter.addWidget(status_container)

        # Metrics section
        metrics_container = QWidget()
        metrics_layout = QVBoxLayout(metrics_container)
        metrics_layout.setContentsMargins(0, 0, 0, 0)

        self._metrics_widget = MetricsWidget()
        metrics_layout.addWidget(self._metrics_widget)

        splitter.addWidget(metrics_container)
        splitter.setSizes([500, 250])

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 0)

        refresh_button = QPushButton("Refresh Now")
        refresh_button.clicked.connect(self._manual_refresh)
        controls_layout.addWidget(refresh_button)

        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

    def _update_status(self) -> None:
        """Update system status and metrics displays."""
        # Start async tasks to fetch system status and metrics
        self._start_async_task("get_system_status", self._async_get_system_status)
        self._start_async_task("get_system_metrics", self._async_get_system_metrics)

    async def _async_get_system_status(self) -> Dict[str, Any]:
        """
        Asynchronously get system status.

        Returns:
            Dictionary with system status information
        """
        if not self._app_core:
            return {}

        return await self._app_core.status_async()

    async def _async_get_system_metrics(self) -> Dict[str, Any]:
        """
        Asynchronously get system metrics.

        Returns:
            Dictionary with system metrics
        """
        if not self._monitoring_manager:
            return {}

        concurrency_manager = self._app_core.get_manager("concurrency_manager")

        if concurrency_manager:
            return await concurrency_manager.run_in_thread(
                self._monitoring_manager.get_metrics
            )

        try:
            # For monitoring_manager.generate_diagnostic_report, check if it's async
            if hasattr(self._monitoring_manager, "generate_diagnostic_report_async"):
                return await self._monitoring_manager.generate_diagnostic_report_async()
            else:
                # Fallback to synchronous metrics
                return self._monitoring_manager.generate_diagnostic_report()
        except Exception as e:
            self._logger.error(f"Error getting system metrics: {str(e)}")
            raise

    def _on_async_result(self, result_data: Dict[str, Any]) -> None:
        """
        Handle results from async operations.

        Args:
            result_data: Dictionary with task ID and result
        """
        task_id = result_data.get("task_id", "")
        result = result_data.get("result")

        if task_id == "get_system_status":
            self._status_tree.update_system_status(result)
            self._last_update_label.setText(f"Last updated: {time.strftime('%H:%M:%S')}")
        elif task_id == "get_system_metrics":
            self._metrics_widget.update_metrics(result)

    def _on_async_error(self, error_msg: str, traceback_str: str) -> None:
        """
        Handle errors from async operations.

        Args:
            error_msg: Error message
            traceback_str: Exception traceback as string
        """
        self._logger.error(f"Error updating dashboard: {error_msg}\n{traceback_str}")

    def _manual_refresh(self) -> None:
        """Handle manual refresh button click."""
        self._update_status()

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

    def showEvent(self, event: Any) -> None:
        """
        Handle widget show event.

        Args:
            event: Show event
        """
        super().showEvent(event)
        self._update_status()

    def hideEvent(self, event: Any) -> None:
        """
        Handle widget hide event.

        Args:
            event: Hide event
        """
        super().hideEvent(event)

    def closeEvent(self, event: Any) -> None:
        """
        Handle widget close event.

        Args:
            event: Close event
        """
        self._update_timer.stop()

        # Cancel all running tasks
        for task in self._running_tasks.values():
            if not task.done():
                task.cancel()

        super().closeEvent(event)