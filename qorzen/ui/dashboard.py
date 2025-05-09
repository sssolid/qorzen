from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)


class SystemStatusTreeWidget(QTreeWidget):
    """Tree widget for displaying system status information."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the system status tree widget.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        # Configure tree widget
        self.setHeaderLabels(['Component', 'Status'])
        self.setAlternatingRowColors(True)
        self.setExpandsOnDoubleClick(True)
        self.setAnimated(True)
        self.setSortingEnabled(False)

        # Set resizing behavior
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        # Track expanded items
        self._expanded_items: Dict[str, bool] = {}

    def _get_status_icon(self, status: Optional[bool]) -> QIcon:
        """Get an icon representing a status.

        Args:
            status: The status (True for healthy, False for unhealthy, None for unknown)

        Returns:
            An icon representing the status
        """
        if status is True:
            return QIcon.fromTheme("emblem-default", QIcon())
        elif status is False:
            return QIcon.fromTheme("emblem-important", QIcon())
        else:
            return QIcon.fromTheme("emblem-question", QIcon())

    def get_item_path(self, item: QTreeWidgetItem) -> str:
        """Get the path of an item in the tree.

        Args:
            item: The tree widget item

        Returns:
            A string representing the item's path
        """
        path = []

        # Walk up the tree to the root
        current = item
        while current:
            path.insert(0, current.text(0))
            current = current.parent()

        return '/'.join(path)

    def save_expanded_state(self) -> None:
        """Save the expanded state of items in the tree."""
        self._expanded_items.clear()

        # Process all top-level items
        for i in range(self.topLevelItemCount()):
            self._save_expanded_state_recursive(self.topLevelItem(i))

    def _save_expanded_state_recursive(self, item: QTreeWidgetItem) -> None:
        """Recursively save the expanded state of an item and its children.

        Args:
            item: The tree widget item
        """
        # Save this item's state
        path = self.get_item_path(item)
        self._expanded_items[path] = item.isExpanded()

        # Process children
        for i in range(item.childCount()):
            self._save_expanded_state_recursive(item.child(i))

    def restore_expanded_state(self) -> None:
        """Restore the expanded state of items in the tree."""
        # Process all top-level items
        for i in range(self.topLevelItemCount()):
            self._restore_expanded_state_recursive(self.topLevelItem(i))

    def _restore_expanded_state_recursive(self, item: QTreeWidgetItem) -> None:
        """Recursively restore the expanded state of an item and its children.

        Args:
            item: The tree widget item
        """
        # Restore this item's state
        path = self.get_item_path(item)
        if path in self._expanded_items:
            item.setExpanded(self._expanded_items[path])

        # Process children
        for i in range(item.childCount()):
            self._restore_expanded_state_recursive(item.child(i))

    def update_system_status(self, status: Dict[str, Any]) -> None:
        """Update the system status display.

        Args:
            status: The system status information
        """
        # Save expanded state
        self.save_expanded_state()

        # Clear the tree
        self.clear()

        # Create app item
        app_item = QTreeWidgetItem(['Application Core', 'Active' if status.get('initialized', False) else 'Inactive'])
        app_item.setIcon(1, self._get_status_icon(status.get('initialized', None)))
        self.addTopLevelItem(app_item)

        # Add manager items
        if 'managers' in status:
            for manager_name, manager_status in status['managers'].items():
                # Add manager item
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
                            # Create a sub-item for this section
                            sub_item = QTreeWidgetItem([key, ''])
                            manager_item.addChild(sub_item)

                            # Add child items for each key-value pair
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, dict):
                                    # Another nested level
                                    sub_sub_item = QTreeWidgetItem([sub_key, ''])
                                    sub_item.addChild(sub_sub_item)

                                    for sub_sub_key, sub_sub_value in sub_value.items():
                                        sub_sub_item.addChild(QTreeWidgetItem([
                                            sub_sub_key,
                                            str(sub_sub_value)
                                        ]))
                                else:
                                    # Add as a leaf node
                                    sub_item.addChild(QTreeWidgetItem([
                                        sub_key,
                                        str(sub_value)
                                    ]))
                        else:
                            # Add as a leaf node
                            manager_item.addChild(QTreeWidgetItem([
                                key,
                                str(value)
                            ]))

        # Restore expanded state
        self.restore_expanded_state()


class MetricsWidget(QWidget):
    """Widget for displaying system metrics."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the metrics widget.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        # Set up UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create metrics sections
        self._create_system_metrics(main_layout)

        # Add stretch to push content to the top
        main_layout.addStretch()

    def _create_system_metrics(self, parent_layout: QVBoxLayout) -> None:
        """Create the system metrics section.

        Args:
            parent_layout: The parent layout
        """
        # Create section label
        section_label = QLabel("System Metrics")
        section_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        parent_layout.addWidget(section_label)

        # Create frame
        metrics_frame = QFrame()
        metrics_frame.setFrameShape(QFrame.StyledPanel)
        metrics_frame.setFrameShadow(QFrame.Raised)
        metrics_layout = QFormLayout(metrics_frame)
        metrics_layout.setContentsMargins(10, 10, 10, 10)
        metrics_layout.setSpacing(10)

        # CPU usage
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

        # Memory usage
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

        # Disk usage
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

        # Add to parent layout
        parent_layout.addWidget(metrics_frame)

    def _set_progress_color(self, progress_bar: QProgressBar, value: float) -> None:
        """Set the color of a progress bar based on its value.

        Args:
            progress_bar: The progress bar to update
            value: The current value (0-100)
        """
        if value < 60:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")  # Green
        elif value < 80:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")  # Yellow
        else:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")  # Red

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update the displayed metrics.

        Args:
            metrics: The metrics data
        """
        # Update system metrics
        if 'system' in metrics:
            system_metrics = metrics['system']

            # CPU usage
            if 'cpu' in system_metrics and 'percent' in system_metrics['cpu']:
                cpu_percent = system_metrics['cpu']['percent']
                self._cpu_label.setText(f"{cpu_percent:.1f}%")
                self._cpu_progress.setValue(int(cpu_percent))
                self._set_progress_color(self._cpu_progress, cpu_percent)

            # Memory usage
            if 'memory' in system_metrics and 'percent' in system_metrics['memory']:
                memory_percent = system_metrics['memory']['percent']
                self._memory_label.setText(f"{memory_percent:.1f}%")
                self._memory_progress.setValue(int(memory_percent))
                self._set_progress_color(self._memory_progress, memory_percent)

            # Disk usage
            if 'disk' in system_metrics and 'percent' in system_metrics['disk']:
                disk_percent = system_metrics['disk']['percent']
                self._disk_label.setText(f"{disk_percent:.1f}%")
                self._disk_progress.setValue(int(disk_percent))
                self._set_progress_color(self._disk_progress, disk_percent)


class DashboardWidget(QWidget):
    """Main dashboard widget displaying system status and metrics."""

    def __init__(
            self,
            app_core: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the dashboard widget.

        Args:
            app_core: The application core
            parent: The parent widget
        """
        super().__init__(parent)

        self._app_core = app_core
        self._config_manager = app_core.get_manager('config')
        self._event_bus = app_core.get_manager('event_bus')
        self._monitoring_manager = app_core.get_manager('monitoring')

        if app_core.get_manager('logging'):
            self._logger = app_core.get_manager('logging').get_logger('dashboard')
        else:
            import logging
            self._logger = logging.getLogger('dashboard')

        # Set up UI
        self._setup_ui()

        # Set up update timer
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start(5000)  # Update every 5 seconds

        # Initial update
        self._update_status()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title label
        title_label = QLabel("System Dashboard")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Last update label
        self._last_update_label = QLabel("Last updated: Never")
        self._last_update_label.setAlignment(Qt.AlignRight)
        self._last_update_label.setStyleSheet("color: #666;")
        main_layout.addWidget(self._last_update_label)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter, 1)  # Give splitter stretch

        # System status section
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)

        status_header = QLabel("System Status")
        status_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        status_layout.addWidget(status_header)

        self._status_tree = SystemStatusTreeWidget()
        self._status_tree.setMinimumHeight(300)
        status_layout.addWidget(self._status_tree, 1)  # Give tree stretch

        splitter.addWidget(status_container)

        # Metrics section
        metrics_container = QWidget()
        metrics_layout = QVBoxLayout(metrics_container)
        metrics_layout.setContentsMargins(0, 0, 0, 0)

        self._metrics_widget = MetricsWidget()
        metrics_layout.addWidget(self._metrics_widget)

        splitter.addWidget(metrics_container)

        # Set initial splitter sizes
        splitter.setSizes([500, 250])

        # Controls section
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 0)

        refresh_button = QPushButton("Refresh Now")
        refresh_button.clicked.connect(self._manual_refresh)
        controls_layout.addWidget(refresh_button)

        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

    def _update_status(self) -> None:
        """Update the status and metrics displays."""
        try:
            # Get system status
            if self._app_core:
                status = self._app_core.status()
                self._status_tree.update_system_status(status)

            # Get system metrics
            if self._monitoring_manager:
                diagnostics = self._monitoring_manager.generate_diagnostic_report()
                self._metrics_widget.update_metrics(diagnostics)

            # Update last update time
            self._last_update_label.setText(f"Last updated: {time.strftime('%H:%M:%S')}")

        except Exception as e:
            self._logger.error(f"Error updating dashboard: {str(e)}")

    def _manual_refresh(self) -> None:
        """Handle manual refresh button click."""
        self._update_status()

    def showEvent(self, event: Any) -> None:
        """Handle widget show events.

        Args:
            event: The event
        """
        super().showEvent(event)

        # Refresh when shown
        self._update_status()

    def hideEvent(self, event: Any) -> None:
        """Handle widget hide events.

        Args:
            event: The event
        """
        super().hideEvent(event)

    def closeEvent(self, event: Any) -> None:
        """Handle widget close events.

        Args:
            event: The event
        """
        # Stop timer
        self._update_timer.stop()

        super().closeEvent(event)