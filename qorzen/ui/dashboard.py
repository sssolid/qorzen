from __future__ import annotations

import asyncio
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QMessageBox
)

from qorzen.ui.ui_component import AsyncQWidget


class SystemStatusTreeWidget(QTreeWidget):
    """Tree widget for displaying system status information."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the system status tree widget."""
        super().__init__(parent)
        self.setHeaderLabels(['Component', 'Status'])
        self.setAlternatingRowColors(True)
        self.setExpandsOnDoubleClick(True)
        self.setAnimated(True)
        self.setSortingEnabled(False)

        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self._expanded_items: Dict[str, bool] = {}

    def _get_status_icon(self, status: Optional[bool]) -> QIcon:
        """Get the icon for a status value."""
        if status is True:
            return QIcon.fromTheme('emblem-default', QIcon())
        elif status is False:
            return QIcon.fromTheme('emblem-important', QIcon())
        else:
            return QIcon.fromTheme('emblem-question', QIcon())

    def get_item_path(self, item: QTreeWidgetItem) -> str:
        """Get the full path of a tree item."""
        path = []
        current = item
        while current:
            path.insert(0, current.text(0))
            current = current.parent()
        return '/'.join(path)

    def save_expanded_state(self) -> None:
        """Save the expanded state of all items."""
        self._expanded_items.clear()
        for i in range(self.topLevelItemCount()):
            self._save_expanded_state_recursive(self.topLevelItem(i))

    def _save_expanded_state_recursive(self, item: QTreeWidgetItem) -> None:
        """Recursively save the expanded state of an item and its children."""
        path = self.get_item_path(item)
        self._expanded_items[path] = item.isExpanded()
        for i in range(item.childCount()):
            self._save_expanded_state_recursive(item.child(i))

    def restore_expanded_state(self) -> None:
        """Restore the previously saved expanded state."""
        for i in range(self.topLevelItemCount()):
            self._restore_expanded_state_recursive(self.topLevelItem(i))

    def _restore_expanded_state_recursive(self, item: QTreeWidgetItem) -> None:
        """Recursively restore the expanded state of an item and its children."""
        path = self.get_item_path(item)
        if path in self._expanded_items:
            item.setExpanded(self._expanded_items[path])
        for i in range(item.childCount()):
            self._restore_expanded_state_recursive(item.child(i))

    def update_system_status(self, status: Dict[str, Any]) -> None:
        """Update the tree with system status information."""
        # Save the current expanded state
        self.save_expanded_state()

        # Clear and rebuild the tree
        self.clear()

        # Add application core item
        app_item = QTreeWidgetItem(['Application Core', 'Active' if status.get('initialized', False) else 'Inactive'])
        app_item.setIcon(1, self._get_status_icon(status.get('initialized', None)))
        self.addTopLevelItem(app_item)

        # Add manager items
        if 'managers' in status:
            for manager_name, manager_status in status['managers'].items():
                # Create manager item
                manager_item = QTreeWidgetItem([
                    manager_name,
                    'Healthy' if manager_status.get('healthy', False) else 'Unhealthy'
                ])
                manager_item.setIcon(1, self._get_status_icon(manager_status.get('healthy', None)))
                app_item.addChild(manager_item)

                # Add manager details
                for key, value in manager_status.items():
                    if key not in ('name', 'initialized', 'healthy'):
                        if isinstance(value, dict):
                            # Add sub-dictionary as a tree node
                            sub_item = QTreeWidgetItem([key, ''])
                            manager_item.addChild(sub_item)

                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, dict):
                                    # Handle nested dictionaries
                                    sub_sub_item = QTreeWidgetItem([sub_key, ''])
                                    sub_item.addChild(sub_sub_item)

                                    for sub_sub_key, sub_sub_value in sub_value.items():
                                        sub_sub_item.addChild(QTreeWidgetItem([
                                            sub_sub_key,
                                            str(sub_sub_value)
                                        ]))
                                else:
                                    # Add simple key-value item
                                    sub_item.addChild(QTreeWidgetItem([
                                        sub_key,
                                        str(sub_value)
                                    ]))
                        else:
                            # Add simple key-value item
                            manager_item.addChild(QTreeWidgetItem([
                                key,
                                str(value)
                            ]))

        # Restore the expanded state
        self.restore_expanded_state()


class MetricsWidget(QWidget):
    """Widget for displaying system metrics."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the metrics widget."""
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self._create_system_metrics(main_layout)

        main_layout.addStretch()

    def _create_system_metrics(self, parent_layout: QVBoxLayout) -> None:
        """Create the system metrics section."""
        # Add section label
        section_label = QLabel('System Metrics')
        section_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        parent_layout.addWidget(section_label)

        # Create the metrics frame
        metrics_frame = QFrame()
        metrics_frame.setFrameShape(QFrame.StyledPanel)
        metrics_frame.setFrameShadow(QFrame.Raised)
        metrics_layout = QFormLayout(metrics_frame)
        metrics_layout.setContentsMargins(10, 10, 10, 10)
        metrics_layout.setSpacing(10)

        # CPU metrics
        self._cpu_label = QLabel('N/A')
        self._cpu_progress = QProgressBar()
        self._cpu_progress.setRange(0, 100)
        self._cpu_progress.setValue(0)

        cpu_widget = QWidget()
        cpu_layout = QHBoxLayout(cpu_widget)
        cpu_layout.setContentsMargins(0, 0, 0, 0)
        cpu_layout.addWidget(self._cpu_progress)
        cpu_layout.addWidget(self._cpu_label)

        metrics_layout.addRow('CPU Usage:', cpu_widget)

        # Memory metrics
        self._memory_label = QLabel('N/A')
        self._memory_progress = QProgressBar()
        self._memory_progress.setRange(0, 100)
        self._memory_progress.setValue(0)

        memory_widget = QWidget()
        memory_layout = QHBoxLayout(memory_widget)
        memory_layout.setContentsMargins(0, 0, 0, 0)
        memory_layout.addWidget(self._memory_progress)
        memory_layout.addWidget(self._memory_label)

        metrics_layout.addRow('Memory Usage:', memory_widget)

        # Disk metrics
        self._disk_label = QLabel('N/A')
        self._disk_progress = QProgressBar()
        self._disk_progress.setRange(0, 100)
        self._disk_progress.setValue(0)

        disk_widget = QWidget()
        disk_layout = QHBoxLayout(disk_widget)
        disk_layout.setContentsMargins(0, 0, 0, 0)
        disk_layout.addWidget(self._disk_progress)
        disk_layout.addWidget(self._disk_label)

        metrics_layout.addRow('Disk Usage:', disk_widget)

        parent_layout.addWidget(metrics_frame)

    def _set_progress_color(self, progress_bar: QProgressBar, value: float) -> None:
        """Set the color of a progress bar based on value."""
        if value < 60:
            progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #4CAF50; }')
        elif value < 80:
            progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #FFC107; }')
        else:
            progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #F44336; }')

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update the displayed metrics."""
        if 'system' in metrics:
            system_metrics = metrics['system']

            # Update CPU metrics
            if 'cpu' in system_metrics and 'percent' in system_metrics['cpu']:
                cpu_percent = system_metrics['cpu']['percent']
                self._cpu_label.setText(f'{cpu_percent:.1f}%')
                self._cpu_progress.setValue(int(cpu_percent))
                self._set_progress_color(self._cpu_progress, cpu_percent)

            # Update memory metrics
            if 'memory' in system_metrics and 'percent' in system_metrics['memory']:
                memory_percent = system_metrics['memory']['percent']
                self._memory_label.setText(f'{memory_percent:.1f}%')
                self._memory_progress.setValue(int(memory_percent))
                self._set_progress_color(self._memory_progress, memory_percent)

            # Update disk metrics
            if 'disk' in system_metrics and 'percent' in system_metrics['disk']:
                disk_percent = system_metrics['disk']['percent']
                self._disk_label.setText(f'{disk_percent:.1f}%')
                self._disk_progress.setValue(int(disk_percent))
                self._set_progress_color(self._disk_progress, disk_percent)


class DashboardWidget(AsyncQWidget):
    """Main dashboard widget for system monitoring."""

    def __init__(self, app_core: Any, parent: Optional[QWidget] = None) -> None:
        """Initialize the dashboard widget."""
        concurrency_manager = app_core.get_manager('concurrency_manager')
        super().__init__(parent, concurrency_manager)

        self._app_core = app_core
        self._config_manager = app_core.get_manager('config_manager')
        self._event_bus_manager = app_core.get_manager('event_bus_manager')
        self._monitoring_manager = app_core.get_manager('monitoring_manager')

        # Get logger
        if app_core.get_manager('logging_manager'):
            self._logger = app_core.get_manager('logging_manager').get_logger('dashboard')
        else:
            self._logger = logging.getLogger('dashboard')

        # Set up UI
        self._setup_ui()

        # Set up update timer - 10 seconds is reasonable for system metrics
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)

        # Start with 10 seconds interval
        self._update_timer.start(10000)

        # Initial update
        self._update_status()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Add title
        title_label = QLabel('System Dashboard')
        title_label.setStyleSheet('font-size: 20px; font-weight: bold;')
        main_layout.addWidget(title_label)

        # Add last update label
        self._last_update_label = QLabel('Last updated: Never')
        self._last_update_label.setAlignment(Qt.AlignRight)
        self._last_update_label.setStyleSheet('color: #666;')
        main_layout.addWidget(self._last_update_label)

        # Create splitter for status and metrics
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter, 1)

        # Status section
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)

        status_header = QLabel('System Status')
        status_header.setStyleSheet('font-size: 16px; font-weight: bold;')
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

        # Set relative sizes
        splitter.setSizes([500, 250])

        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 0)

        refresh_button = QPushButton('Refresh Now')
        refresh_button.clicked.connect(self._manual_refresh)
        controls_layout.addWidget(refresh_button)

        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

    def _update_status(self) -> None:
        """Update the status and metrics displays."""
        # Start system status fetch
        self.run_async_task(
            self._async_get_system_status,
            task_id='get_system_status',
            on_result=self._on_system_status,
            on_error=self._on_task_error
        )

        # Start system metrics fetch
        self.run_async_task(
            self._async_get_system_metrics,
            task_id='get_system_metrics',
            on_result=self._on_system_metrics,
            on_error=self._on_task_error
        )

    async def _async_get_system_status(self) -> Dict[str, Any]:
        """Fetch system status information asynchronously."""
        if not self._app_core:
            return {}

        return await self._app_core.status_async()

    async def _async_get_system_metrics(self) -> Dict[str, Any]:
        """Fetch system metrics information asynchronously."""
        if not self._monitoring_manager:
            return {}

        # Try to run on a separate thread if possible
        concurrency_manager = self._app_core.get_manager('concurrency_manager')
        if concurrency_manager:
            return await concurrency_manager.run_in_thread(self._monitoring_manager.get_metrics)

        # Fallback to direct call
        try:
            if hasattr(self._monitoring_manager, 'generate_diagnostic_report_async'):
                return await self._monitoring_manager.generate_diagnostic_report_async()
            else:
                return self._monitoring_manager.generate_diagnostic_report()
        except Exception as e:
            self._logger.error(f'Error getting system metrics: {str(e)}')
            raise

    def _on_system_status(self, status: Dict[str, Any]) -> None:
        """Handle system status result."""
        self._status_tree.update_system_status(status)
        self._last_update_label.setText(f"Last updated: {time.strftime('%H:%M:%S')}")

    def _on_system_metrics(self, metrics: Dict[str, Any]) -> None:
        """Handle system metrics result."""
        self._metrics_widget.update_metrics(metrics)

    def _on_task_error(self, error_msg: str, traceback_str: str) -> None:
        """Handle task error."""
        self._logger.error(f'Error updating dashboard: {error_msg}\n{traceback_str}')

    def _manual_refresh(self) -> None:
        """Handle manual refresh button click."""
        self._update_status()

    def showEvent(self, event: Any) -> None:
        """Handle widget show event."""
        super().showEvent(event)

        # Update immediately when shown
        self._update_status()

        # Restart timer if it's not running
        if not self._update_timer.isActive():
            self._update_timer.start()

    def hideEvent(self, event: Any) -> None:
        """Handle widget hide event."""
        super().hideEvent(event)

        # Stop timer when hidden to reduce resource usage
        self._update_timer.stop()