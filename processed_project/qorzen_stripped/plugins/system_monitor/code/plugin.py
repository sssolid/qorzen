from __future__ import annotations
'\nSystem Monitor Plugin for Qorzen framework.\n\nThis plugin provides real-time monitoring of system resources and performance metrics.\nIt displays CPU, memory, disk, and network usage in a dedicated tab in the UI.\n'
import logging
import time
import threading
from typing import Any, Dict, List, Optional, cast
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QMenu, QToolBar
from PySide6.QtCore import QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QColor, QPalette
from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, TabComponent
from qorzen.plugin_system.interface import BasePlugin
class ResourceWidget(QWidget):
    def __init__(self, title: str, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._title_label = QLabel(title)
        self._title_label.setMinimumWidth(100)
        self._layout.addWidget(self._title_label)
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._layout.addWidget(self._progress_bar)
        self._value_label = QLabel('0%')
        self._value_label.setMinimumWidth(50)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._layout.addWidget(self._value_label)
    def update_value(self, value: float) -> None:
        progress_value = min(100, max(0, int(value)))
        self._progress_bar.setValue(progress_value)
        self._value_label.setText(f'{value:.1f}%')
        self._set_color(value)
    def _set_color(self, value: float) -> None:
        if value < 60:
            self._progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #4CAF50; }')
        elif value < 80:
            self._progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #FFC107; }')
        else:
            self._progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #F44336; }')
class SystemMonitorTab(QWidget):
    update_signal = Signal(dict)
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        title_label = QLabel('System Resource Monitor')
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        self._layout.addWidget(title_label)
        self._cpu_widget = ResourceWidget('CPU Usage')
        self._memory_widget = ResourceWidget('Memory Usage')
        self._disk_widget = ResourceWidget('Disk Usage')
        self._network_widget = ResourceWidget('Network Usage')
        self._layout.addWidget(self._cpu_widget)
        self._layout.addWidget(self._memory_widget)
        self._layout.addWidget(self._disk_widget)
        self._layout.addWidget(self._network_widget)
        self._layout.addStretch()
        self._status_label = QLabel('Monitoring system resources...')
        self._status_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._status_label)
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_timer_tick)
        self.update_signal.connect(self._update_ui)
        self._last_update_time = time.time()
    def get_widget(self) -> QWidget:
        return self
    def on_tab_selected(self) -> None:
        self._update_timer.start(1000)
    def on_tab_deselected(self) -> None:
        self._update_timer.stop()
    def update_metrics(self, metrics: Dict[str, float]) -> None:
        self.update_signal.emit(metrics)
    @Slot()
    def _update_timer_tick(self) -> None:
        now = time.time()
        elapsed = now - self._last_update_time
        self._status_label.setText(f'Last update: {elapsed:.1f} seconds ago')
    @Slot(dict)
    def _update_ui(self, metrics: Dict[str, float]) -> None:
        if 'cpu' in metrics:
            self._cpu_widget.update_value(metrics['cpu'])
        if 'memory' in metrics:
            self._memory_widget.update_value(metrics['memory'])
        if 'disk' in metrics:
            self._disk_widget.update_value(metrics['disk'])
        if 'network' in metrics:
            self._network_widget.update_value(metrics['network'])
        self._last_update_time = time.time()
        self._status_label.setText('Last update: just now')
class SystemMonitorPlugin(BasePlugin):
    name = 'system_monitor'
    version = '1.0.0'
    description = 'Real-time system resource monitoring'
    author = 'Qorzen Team'
    dependencies = []
    def __init__(self) -> None:
        super().__init__()
        self._tab: Optional[SystemMonitorTab] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._metrics: Dict[str, float] = {'cpu': 0.0, 'memory': 0.0, 'disk': 0.0, 'network': 0.0}
        self._toolbar: Optional[QToolBar] = None
        self._menu: Optional[QMenu] = None
        self._actions: List[Any] = []
    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any, file_manager: Any, thread_manager: Any, **kwargs: Any) -> None:
        super().initialize(event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs)
        self._resource_manager = kwargs.get('resource_manager')
        self._logger = logger_provider.get_logger(self.name)
        self._logger.info(f'Initializing {self.name} v{self.version} plugin')
        self._load_config()
        self._event_bus.subscribe(event_type=EventType.SYSTEM_STARTED, callback=self._on_system_started, subscriber_id=f'{self.name}_system_started')
        self._start_monitoring()
        self._initialized = True
        self._logger.info(f'{self.name} plugin initialized')
    def _load_config(self) -> None:
        self._update_interval = self._config.get(f'plugins.{self.name}.update_interval', 5.0)
        self._logger.debug(f'Update interval: {self._update_interval}s')
    def _on_system_started(self, event: Event) -> None:
        self._logger.info('System started event received')
        self._publish_metrics()
    def _start_monitoring(self) -> None:
        self._logger.info('Starting resource monitoring thread')
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, name=f'{self.name}_monitor', daemon=True)
        self._monitor_thread.start()
    def _monitoring_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                self._update_metrics()
                self._publish_metrics()
                if self._tab:
                    self._tab.update_metrics(self._metrics)
                self._stop_event.wait(self._update_interval)
        except Exception as e:
            self._logger.error(f'Error in monitoring loop: {str(e)}')
    def _update_metrics(self) -> None:
        try:
            if self._resource_manager:
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
                self._update_basic_metrics()
        except Exception as e:
            self._logger.error(f'Error updating metrics: {str(e)}')
    def _update_basic_metrics(self) -> None:
        try:
            import psutil
            self._metrics['cpu'] = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            self._metrics['memory'] = memory.percent
            disk = psutil.disk_usage('/')
            self._metrics['disk'] = disk.percent
            self._metrics['network'] = 30.0
        except ImportError:
            import random
            self._metrics = {'cpu': random.uniform(20, 80), 'memory': random.uniform(30, 70), 'disk': random.uniform(40, 60), 'network': random.uniform(10, 50)}
    def _publish_metrics(self) -> None:
        if self._event_bus:
            self._event_bus.publish(event_type=f'{self.name}/metrics', source=self.name, payload=self._metrics.copy())
    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        self._logger.info('Setting up UI components')
        self._tab = SystemMonitorTab()
        tab_index = ui_integration.add_tab(plugin_id=self.name, tab=self._tab, title='System Monitor')
        self._logger.debug(f'Added System Monitor tab at index {tab_index}')
        try:
            self._toolbar = ui_integration.add_toolbar(plugin_id=self.name, title='Monitor')
            action = ui_integration.add_toolbar_action(plugin_id=self.name, toolbar=self._toolbar, text='Refresh', callback=self._refresh_metrics)
            self._actions.append(action)
        except Exception as e:
            self._logger.warning(f'Error adding toolbar: {str(e)}')
        try:
            tools_menu = ui_integration.find_menu('&Tools')
            if tools_menu:
                self._menu = ui_integration.add_menu(plugin_id=self.name, title='System Monitor', parent_menu=tools_menu)
                action1 = ui_integration.add_menu_action(plugin_id=self.name, menu=self._menu, text='Refresh Metrics', callback=self._refresh_metrics)
                action2 = ui_integration.add_menu_action(plugin_id=self.name, menu=self._menu, text='Generate Report', callback=self._generate_report)
                self._actions.extend([action1, action2])
        except Exception as e:
            self._logger.warning(f'Error adding menu items: {str(e)}')
        self._tab.update_metrics(self._metrics)
    def _refresh_metrics(self) -> None:
        self._logger.info('Manually refreshing metrics')
        self._update_metrics()
        if self._tab:
            self._tab.update_metrics(self._metrics)
        self._publish_metrics()
    def _generate_report(self) -> None:
        self._logger.info('Generating system report')
        report = '\n'.join([f'{k.upper()}: {v:.1f}%' for k, v in self._metrics.items()])
        self._logger.info(f'System Report:\n{report}')
        if self._event_bus:
            self._event_bus.publish(event_type=f'{self.name}/report', source=self.name, payload={'report': report, 'timestamp': time.time(), 'metrics': self._metrics.copy()})
    def shutdown(self) -> None:
        self._logger.info(f'Shutting down {self.name} plugin')
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        if self._event_bus:
            self._event_bus.unsubscribe(f'{self.name}_system_started')
        self._toolbar = None
        self._menu = None
        self._actions.clear()
        super().shutdown()
        self._logger.info(f'{self.name} plugin shut down successfully')
    def status(self) -> Dict[str, Any]:
        status = super().status()
        status.update({'metrics': self._metrics, 'update_interval': self._update_interval, 'monitoring_active': self._monitor_thread is not None and self._monitor_thread.is_alive(), 'ui_components': {'tab_created': self._tab is not None}})
        return status