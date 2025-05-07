from __future__ import annotations

"""
System Monitor Plugin for Qorzen framework.

This plugin provides real-time monitoring of system resources and performance metrics.
It displays CPU, memory, disk, and network usage in a dedicated tab in the UI.
"""
import logging
import time
from typing import Any, Dict, List, Optional, cast
import threading

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QColor, QPalette

from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, TabComponent
from qorzen.plugin_system.interface import BasePlugin


class ResourceWidget(QWidget):
    """Widget to display a resource usage with label and progress bar."""

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        """Initialize the resource widget.

        Args:
            title: Resource title (e.g., "CPU Usage")
            parent: Parent widget
        """
        super().__init__(parent)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)

        # Title label
        self._title_label = QLabel(title)
        self._title_label.setMinimumWidth(100)
        self._layout.addWidget(self._title_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._layout.addWidget(self._progress_bar)

        # Value label
        self._value_label = QLabel("0%")
        self._value_label.setMinimumWidth(50)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._layout.addWidget(self._value_label)

    def update_value(self, value: float) -> None:
        """Update the displayed value.

        Args:
            value: Resource usage as percentage (0-100)
        """
        # Update progress bar
        progress_value = min(100, max(0, int(value)))
        self._progress_bar.setValue(progress_value)

        # Update label
        self._value_label.setText(f"{value:.1f}%")

        # Update color based on value
        self._set_color(value)

    def _set_color(self, value: float) -> None:
        """Set the color of the progress bar based on value.

        Args:
            value: Resource usage percentage
        """
        # Define color thresholds
        if value < 60:
            # Green for low usage
            self._progress_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #4CAF50; }"
            )
        elif value < 80:
            # Yellow for medium usage
            self._progress_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #FFC107; }"
            )
        else:
            # Red for high usage
            self._progress_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #F44336; }"
            )


class SystemMonitorTab(QWidget):
    """Tab component for the System Monitor plugin."""

    update_signal = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the system monitor tab.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._layout = QVBoxLayout(self)

        # Add title
        title_label = QLabel("System Resource Monitor")
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        self._layout.addWidget(title_label)

        # Add resource widgets
        self._cpu_widget = ResourceWidget("CPU Usage")
        self._memory_widget = ResourceWidget("Memory Usage")
        self._disk_widget = ResourceWidget("Disk Usage")
        self._network_widget = ResourceWidget("Network Usage")

        self._layout.addWidget(self._cpu_widget)
        self._layout.addWidget(self._memory_widget)
        self._layout.addWidget(self._disk_widget)
        self._layout.addWidget(self._network_widget)

        # Add spacer
        self._layout.addStretch()

        # Add status label
        self._status_label = QLabel("Monitoring system resources...")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._status_label)

        # Set up update timer
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_timer_tick)

        # Connect update signal
        self.update_signal.connect(self._update_ui)

        # Last update time
        self._last_update_time = time.time()

    def get_widget(self) -> QWidget:
        """Get the tab widget.

        Returns:
            The tab widget
        """
        return self

    def on_tab_selected(self) -> None:
        """Called when the tab is selected."""
        # Start updates when tab is selected
        self._update_timer.start(1000)  # Update every second

    def on_tab_deselected(self) -> None:
        """Called when the tab is deselected."""
        # Stop updates when tab is not visible
        self._update_timer.stop()

    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """Update with new metrics.

        Args:
            metrics: Dictionary with resource usage percentages
        """
        # Emit signal to update UI from the main thread
        self.update_signal.emit(metrics)

    @Slot()
    def _update_timer_tick(self) -> None:
        """Handle timer tick for UI updates."""
        now = time.time()
        elapsed = now - self._last_update_time
        self._status_label.setText(f"Last update: {elapsed:.1f} seconds ago")

    @Slot(dict)
    def _update_ui(self, metrics: Dict[str, float]) -> None:
        """Update UI with metrics from the main thread.

        Args:
            metrics: Dictionary with resource usage percentages
        """
        if 'cpu' in metrics:
            self._cpu_widget.update_value(metrics['cpu'])

        if 'memory' in metrics:
            self._memory_widget.update_value(metrics['memory'])

        if 'disk' in metrics:
            self._disk_widget.update_value(metrics['disk'])

        if 'network' in metrics:
            self._network_widget.update_value(metrics['network'])

        # Update timestamp
        self._last_update_time = time.time()
        self._status_label.setText("Last update: just now")


class SystemMonitorPlugin(BasePlugin):
    """System Resource Monitor Plugin.

    This plugin monitors and displays real-time system resource usage,
    including CPU, memory, disk, and network activity.
    """

    # Plugin metadata
    name = 'system_monitor'
    version = '1.0.0'
    description = 'Real-time system resource monitoring'
    author = 'Qorzen Team'
    dependencies = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()

        # Plugin-specific members
        self._tab: Optional[SystemMonitorTab] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._metrics: Dict[str, float] = {
            'cpu': 0.0,
            'memory': 0.0,
            'disk': 0.0,
            'network': 0.0
        }

    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any,
                   file_manager: Any, thread_manager: Any, **kwargs: Any) -> None:
        """Initialize the plugin with the provided managers.

        Args:
            event_bus: Event bus manager
            logger_provider: Logger provider
            config_provider: Configuration provider
            file_manager: File manager
            thread_manager: Thread manager
            **kwargs: Additional managers
        """
        # Call base implementation
        super().initialize(event_bus, logger_provider, config_provider,
                           file_manager, thread_manager, **kwargs)

        # Get resource manager if available
        self._resource_manager = kwargs.get('resource_manager')

        # Get logger
        self._logger = logger_provider.get_logger(self.name)
        self._logger.info(f"Initializing {self.name} v{self.version} plugin")

        # Load configuration
        self._load_config()

        # Subscribe to events
        self._event_bus.subscribe(
            event_type=EventType.SYSTEM_STARTED,
            callback=self._on_system_started,
            subscriber_id=f"{self.name}_system_started"
        )

        # Start monitoring thread
        self._start_monitoring()

        # Mark as initialized
        self._initialized = True
        self._logger.info(f"{self.name} plugin initialized")

    def _load_config(self) -> None:
        """Load plugin configuration."""
        # Sample configuration - add more as needed
        self._update_interval = self._config.get(
            f"plugins.{self.name}.update_interval",
            5.0
        )

        self._logger.debug(f"Update interval: {self._update_interval}s")

    def _on_system_started(self, event: Event) -> None:
        """Handle system started event.

        Args:
            event: Event data
        """
        self._logger.info("System started event received")

        # Publish initial metrics
        self._publish_metrics()

    def _start_monitoring(self) -> None:
        """Start the resource monitoring thread."""
        self._logger.info("Starting resource monitoring thread")

        # Create and start thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name=f"{self.name}_monitor",
            daemon=True
        )
        self._monitor_thread.start()

    def _monitoring_loop(self) -> None:
        """Resource monitoring loop."""
        try:
            while not self._stop_event.is_set():
                # Update metrics
                self._update_metrics()

                # Publish metrics
                self._publish_metrics()

                # Update UI if available
                if self._tab:
                    self._tab.update_metrics(self._metrics)

                # Wait for next update interval
                self._stop_event.wait(self._update_interval)
        except Exception as e:
            self._logger.error(f"Error in monitoring loop: {str(e)}")

    def _update_metrics(self) -> None:
        """Update resource metrics."""
        try:
            if self._resource_manager:
                # Get metrics from resource manager if available
                diagnostics = self._resource_manager.generate_diagnostic_report()
                if 'system' in diagnostics:
                    system_data = diagnostics['system']
                    if 'cpu' in system_data:
                        self._metrics['cpu'] = system_data['cpu'].get('percent', 0.0)
                    if 'memory' in system_data:
                        self._metrics['memory'] = system_data['memory'].get('percent', 0.0)
                    if 'disk' in system_data:
                        self._metrics['disk'] = system_data['disk'].get('percent', 0.0)
                    if 'network' in system_data:
                        self._metrics['network'] = system_data['network'].get('percent', 0.0)
            else:
                # Fallback to basic metrics if resource manager not available
                self._update_basic_metrics()
        except Exception as e:
            self._logger.error(f"Error updating metrics: {str(e)}")

    def _update_basic_metrics(self) -> None:
        """Update basic metrics without resource manager."""
        try:
            import psutil

            # CPU usage
            self._metrics['cpu'] = psutil.cpu_percent(interval=0.5)

            # Memory usage
            memory = psutil.virtual_memory()
            self._metrics['memory'] = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            self._metrics['disk'] = disk.percent

            # Network usage (estimated)
            # This is a placeholder; real network usage would need more complex tracking
            self._metrics['network'] = 30.0  # Example static value

        except ImportError:
            # If psutil is not available, use random values for demonstration
            import random
            self._metrics = {
                'cpu': random.uniform(20, 80),
                'memory': random.uniform(30, 70),
                'disk': random.uniform(40, 60),
                'network': random.uniform(10, 50)
            }

    def _publish_metrics(self) -> None:
        """Publish metrics to event bus."""
        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/metrics",
                source=self.name,
                payload=self._metrics.copy()
            )

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Set up UI components when UI is ready.

        Args:
            ui_integration: UI integration interface
        """
        self._logger.info("Setting up UI components")

        # Create the tab
        self._tab = SystemMonitorTab()

        # Add tab to main window
        tab_index = ui_integration.add_tab(
            plugin_id=self.name,
            tab=self._tab,
            title="System Monitor"
        )

        self._logger.debug(f"Added System Monitor tab at index {tab_index}")

        # Add toolbar button
        toolbar = ui_integration.add_toolbar(
            plugin_id=self.name,
            title="Monitor"
        )

        ui_integration.add_toolbar_action(
            plugin_id=self.name,
            toolbar=toolbar,
            text="Refresh",
            callback=self._refresh_metrics
        )

        # Add menu to Tools menu
        tools_menu = ui_integration.find_menu("&Tools")
        if tools_menu:
            monitor_menu = ui_integration.add_menu(
                plugin_id=self.name,
                title="System Monitor",
                parent_menu=tools_menu
            )

            ui_integration.add_menu_action(
                plugin_id=self.name,
                menu=monitor_menu,
                text="Refresh Metrics",
                callback=self._refresh_metrics
            )

            ui_integration.add_menu_action(
                plugin_id=self.name,
                menu=monitor_menu,
                text="Generate Report",
                callback=self._generate_report
            )

        # Initialize tab with current metrics
        self._tab.update_metrics(self._metrics)

    def _refresh_metrics(self) -> None:
        """Refresh metrics immediately."""
        self._logger.info("Manually refreshing metrics")

        # Update metrics
        self._update_metrics()

        # Update UI
        if self._tab:
            self._tab.update_metrics(self._metrics)

        # Publish metrics
        self._publish_metrics()

    def _generate_report(self) -> None:
        """Generate a system report."""
        self._logger.info("Generating system report")

        # In a real plugin, this would create a detailed report
        # For now, just log the current metrics
        report = "\n".join([f"{k.upper()}: {v:.1f}%" for k, v in self._metrics.items()])
        self._logger.info(f"System Report:\n{report}")

        # Publish report event
        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/report",
                source=self.name,
                payload={
                    'report': report,
                    'timestamp': time.time(),
                    'metrics': self._metrics.copy()
                }
            )

    def shutdown(self) -> None:
        """Shut down the plugin."""
        self._logger.info(f"Shutting down {self.name} plugin")

        # Stop monitoring thread
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f"{self.name}_system_started")

        # Call base implementation
        super().shutdown()

        self._logger.info(f"{self.name} plugin shut down successfully")

    def status(self) -> Dict[str, Any]:
        """Get plugin status.

        Returns:
            Status dictionary
        """
        status = super().status()

        # Add plugin-specific status
        status.update({
            'metrics': self._metrics,
            'update_interval': self._update_interval,
            'monitoring_active': self._monitor_thread is not None and self._monitor_thread.is_alive(),
            'ui_components': {
                'tab_created': self._tab is not None
            }
        })

        return status