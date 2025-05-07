from __future__ import annotations

import json
import sys
import threading
import time
from typing import Any, Dict, List, Optional, cast, ClassVar

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QFont, QIcon, QColor, QBrush
from PySide6.QtWidgets import (
    QApplication, QDockWidget, QFormLayout, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton,
    QStatusBar, QTabWidget, QTextEdit, QToolBar, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem
)

from qorzen.core.event_model import EventType


class QorzenMainWindow(QMainWindow):
    """Main window for the Qorzen application."""

    update_signal = Signal(str, object)

    def __init__(self, app_core: Any) -> None:
        """Initialize the main window.

        Args:
            app_core: The application core.
        """
        super().__init__()
        self._app_core = app_core
        self._config_manager = app_core.get_manager('config')
        self._logging_manager = app_core.get_manager('logging')
        self._event_bus = app_core.get_manager('event_bus')
        self._plugin_manager = app_core.get_manager('plugin_manager')
        self._monitoring_manager = app_core.get_manager('monitoring')

        if self._logging_manager:
            self._logger = self._logging_manager.get_logger('ui')
        else:
            import logging
            self._logger = logging.getLogger('ui')

        self._status_bar: Optional[QStatusBar] = None
        self._central_tabs: Optional[QTabWidget] = None
        self._log_table = QTableWidget()
        self._log_table.setColumnCount(6)
        self._log_table.setHorizontalHeaderLabels([
            "Timestamp", "Level", "Logger", "Event", "Message", "Task"
        ])
        self._log_table.setSortingEnabled(True)
        self._log_table.horizontalHeader().setStretchLastSection(True)
        self._system_status_widget: Optional[QTreeWidget] = None
        self._plugin_tree: Optional[QTreeWidget] = None
        self._metrics_widget: Optional[QWidget] = None
        self._event_subscriptions: List[str] = []

        # Store references to menus
        self._menus: Dict[str, QMenu] = {}
        self._menu_actions: Dict[str, List[QAction]] = {}
        self._toolbars: Dict[str, QToolBar] = {}

        self._setup_ui()

        self.update_signal.connect(self._handle_update_signal)

        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start(5000)

        self._subscribe_to_events()
        self._update_status()

        self._logger.info('Qorzen UI started')

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle('Qorzen')
        self.setMinimumSize(1024, 768)

        self._central_tabs = QTabWidget()
        self.setCentralWidget(self._central_tabs)

        self._create_dashboard_tab()
        self._create_plugins_tab()
        self._create_logs_tab()

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.addPermanentWidget(QLabel('Ready'))

        self._create_menu_bar()
        self._create_tool_bar()

    def _create_menu_bar(self) -> None:
        """Create the menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu('&File')
        self._menus['&File'] = file_menu
        self._menu_actions['&File'] = []

        refresh_action = QAction('&Refresh', self)
        refresh_action.triggered.connect(self._update_status)
        file_menu.addAction(refresh_action)
        self._menu_actions['&File'].append(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction('E&xit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        self._menu_actions['&File'].append(exit_action)

        # Tools menu
        tools_menu = self.menuBar().addMenu('&Tools')
        self._menus['&Tools'] = tools_menu
        self._menu_actions['&Tools'] = []

        reload_plugins_action = QAction('&Reload Plugins', self)
        reload_plugins_action.triggered.connect(self._reload_plugins)
        tools_menu.addAction(reload_plugins_action)
        self._menu_actions['&Tools'].append(reload_plugins_action)

        # Help menu
        help_menu = self.menuBar().addMenu('&Help')
        self._menus['&Help'] = help_menu
        self._menu_actions['&Help'] = []

        about_action = QAction('&About', self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        self._menu_actions['&Help'].append(about_action)

    def _create_tool_bar(self) -> None:
        """Create the main toolbar."""
        tool_bar = QToolBar('Main Toolbar')
        tool_bar.setMovable(False)
        self.addToolBar(tool_bar)
        self._toolbars['Main Toolbar'] = tool_bar

        refresh_action = QAction('Refresh', self)
        refresh_action.triggered.connect(self._update_status)
        tool_bar.addAction(refresh_action)

    def _create_dashboard_tab(self) -> None:
        """Create the dashboard tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)

        title_label = QLabel('Qorzen Dashboard')
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title_label)

        status_group_label = QLabel('System Status')
        status_group_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(status_group_label)

        self._system_status_widget = QTreeWidget()
        self._system_status_widget.setHeaderLabels(['Component', 'Status'])
        self._system_status_widget.setMinimumHeight(200)
        layout.addWidget(self._system_status_widget)

        metrics_label = QLabel('System Metrics')
        metrics_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(metrics_label)

        self._metrics_widget = QWidget()
        metrics_layout = QFormLayout(self._metrics_widget)

        self._cpu_label = QLabel('N/A')
        self._memory_label = QLabel('N/A')
        self._disk_label = QLabel('N/A')

        self._cpu_progress = QProgressBar()
        self._cpu_progress.setRange(0, 100)
        self._cpu_progress.setValue(0)

        self._memory_progress = QProgressBar()
        self._memory_progress.setRange(0, 100)
        self._memory_progress.setValue(0)

        self._disk_progress = QProgressBar()
        self._disk_progress.setRange(0, 100)
        self._disk_progress.setValue(0)

        cpu_widget = QWidget()
        cpu_layout = QHBoxLayout(cpu_widget)
        cpu_layout.setContentsMargins(0, 0, 0, 0)
        cpu_layout.addWidget(self._cpu_progress)
        cpu_layout.addWidget(self._cpu_label)

        memory_widget = QWidget()
        memory_layout = QHBoxLayout(memory_widget)
        memory_layout.setContentsMargins(0, 0, 0, 0)
        memory_layout.addWidget(self._memory_progress)
        memory_layout.addWidget(self._memory_label)

        disk_widget = QWidget()
        disk_layout = QHBoxLayout(disk_widget)
        disk_layout.setContentsMargins(0, 0, 0, 0)
        disk_layout.addWidget(self._disk_progress)
        disk_layout.addWidget(self._disk_label)

        metrics_layout.addRow('CPU Usage:', cpu_widget)
        metrics_layout.addRow('Memory Usage:', memory_widget)
        metrics_layout.addRow('Disk Usage:', disk_widget)

        layout.addWidget(self._metrics_widget)
        layout.addStretch()

        self._central_tabs.addTab(dashboard_widget, 'Dashboard')

    def _create_plugins_tab(self) -> None:
        """Create the plugins tab."""
        plugins_widget = QWidget()
        layout = QVBoxLayout(plugins_widget)

        title_label = QLabel('Plugins')
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title_label)

        controls_layout = QHBoxLayout()

        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self._refresh_plugins)
        controls_layout.addWidget(refresh_button)

        load_button = QPushButton('Load Selected')
        load_button.clicked.connect(self._load_selected_plugin)
        controls_layout.addWidget(load_button)

        unload_button = QPushButton('Unload Selected')
        unload_button.clicked.connect(self._unload_selected_plugin)
        controls_layout.addWidget(unload_button)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        self._plugin_tree = QTreeWidget()
        self._plugin_tree.setHeaderLabels(['Name', 'Version', 'State', 'Description'])
        self._plugin_tree.setColumnWidth(0, 150)
        self._plugin_tree.setColumnWidth(1, 100)
        self._plugin_tree.setColumnWidth(2, 100)
        layout.addWidget(self._plugin_tree)

        self._central_tabs.addTab(plugins_widget, 'Plugins')

    def _create_logs_tab(self) -> None:
        """Create the logs tab."""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)

        title_label = QLabel('Logs')
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title_label)

        layout.addWidget(self._log_table)

        controls_layout = QHBoxLayout()

        clear_button = QPushButton('Clear')
        clear_button.clicked.connect(self._clear_logs)
        controls_layout.addWidget(clear_button)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        self._central_tabs.addTab(logs_widget, 'Logs')

    def _subscribe_to_events(self) -> None:
        """Subscribe to events."""
        if not self._event_bus:
            return

        self._event_subscriptions.append(
            self._event_bus.subscribe(
                event_type=EventType.LOG_EVENT,
                callback=self._on_log_event,
                subscriber_id='ui_log_subscriber'
            )
        )

        self._event_subscriptions.append(
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_LOADED,
                callback=self._on_plugin_event,
                subscriber_id='ui_plugin_subscriber'
            )
        )

        self._event_subscriptions.append(
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_UNLOADED,
                callback=self._on_plugin_event,
                subscriber_id='ui_plugin_subscriber'
            )
        )

        self._event_subscriptions.append(
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_ERROR,
                callback=self._on_plugin_event,
                subscriber_id='ui_plugin_subscriber'
            )
        )

        self._event_subscriptions.append(
            self._event_bus.subscribe(
                event_type=EventType.MONITORING_METRICS,
                callback=self._on_metrics_event,
                subscriber_id='ui_monitoring_subscriber'
            )
        )

        self._event_subscriptions.append(
            self._event_bus.subscribe(
                event_type=EventType.MONITORING_ALERT,
                callback=self._on_alert_event,
                subscriber_id='ui_alert_subscriber'
            )
        )

    @Slot(str, object)
    def _handle_update_signal(self, signal_type: str, data: Any) -> None:
        """Handle update signals from other threads.

        Args:
            signal_type: The type of signal.
            data: The signal data.
        """
        if signal_type == 'log':
            self._update_logs_table(data)
        elif signal_type == 'plugin':
            self._refresh_plugins()
        elif signal_type == 'metrics':
            self._update_metrics(data)
        elif signal_type == 'alert':
            self._show_alert(data)

    def _update_status(self) -> None:
        """Update status information."""
        if not self._app_core:
            return

        status = self._app_core.status()

        if self._system_status_widget:
            self._system_status_widget.clear()

            app_item = QTreeWidgetItem([
                'Application Core',
                'Active' if status['initialized'] else 'Inactive'
            ])
            app_item.setIcon(1, self._get_status_icon(status['initialized']))
            self._system_status_widget.addTopLevelItem(app_item)

            if 'managers' in status:
                for manager_name, manager_status in status['managers'].items():
                    manager_item = QTreeWidgetItem([
                        manager_name,
                        'Healthy' if manager_status.get('healthy', False) else 'Unhealthy'
                    ])
                    manager_item.setIcon(
                        1, self._get_status_icon(manager_status.get('healthy', False))
                    )
                    app_item.addChild(manager_item)

                    for key, value in manager_status.items():
                        if key not in ('name', 'initialized', 'healthy'):
                            if isinstance(value, dict):
                                sub_item = QTreeWidgetItem([key, ''])
                                manager_item.addChild(sub_item)

                                for sub_key, sub_value in value.items():
                                    sub_item.addChild(QTreeWidgetItem([sub_key, str(sub_value)]))
                            else:
                                manager_item.addChild(QTreeWidgetItem([key, str(value)]))

            app_item.setExpanded(True)
            self._system_status_widget.resizeColumnToContents(0)

        self._refresh_metrics()

    def _refresh_metrics(self) -> None:
        """Refresh system metrics."""
        if self._monitoring_manager:
            try:
                diagnostics = self._monitoring_manager.generate_diagnostic_report()

                if 'system' in diagnostics:
                    cpu_percent = diagnostics['system']['cpu']['percent']
                    self._cpu_label.setText(f'{cpu_percent:.1f}%')
                    self._cpu_progress.setValue(int(cpu_percent))
                    self._set_progress_color(self._cpu_progress, cpu_percent)

                    memory_percent = diagnostics['system']['memory']['percent']
                    self._memory_label.setText(f'{memory_percent:.1f}%')
                    self._memory_progress.setValue(int(memory_percent))
                    self._set_progress_color(self._memory_progress, memory_percent)

                    disk_percent = diagnostics['system']['disk']['percent']
                    self._disk_label.setText(f'{disk_percent:.1f}%')
                    self._disk_progress.setValue(int(disk_percent))
                    self._set_progress_color(self._disk_progress, disk_percent)

            except Exception as e:
                self._logger.error(f'Error refreshing metrics: {str(e)}')

    def _refresh_plugins(self) -> None:
        """Refresh the plugins list."""
        if not self._plugin_manager or not self._plugin_tree:
            return

        try:
            self._plugin_tree.clear()
            plugins = self._plugin_manager.get_all_plugins()

            from qorzen.core.plugin_manager import PluginInfo
            for name, info in plugins.items():
                info: PluginInfo = info

                item = QTreeWidgetItem([
                    name, info.version, info.state, info.description
                ])

                state = info.state
                if state == 'active':
                    item.setIcon(2, self._get_status_icon(True))
                elif state == 'loaded':
                    item.setIcon(2, self._get_status_icon(True))
                elif state == 'failed':
                    item.setIcon(2, self._get_status_icon(False))
                else:
                    item.setIcon(2, self._get_status_icon(None))

                self._plugin_tree.addTopLevelItem(item)

            for i in range(4):
                self._plugin_tree.resizeColumnToContents(i)

        except Exception as e:
            self._logger.error(f'Error refreshing plugins: {str(e)}')

    def _load_selected_plugin(self) -> None:
        """Load the selected plugin."""
        if not self._plugin_manager or not self._plugin_tree:
            return

        selected_items = self._plugin_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, 'No Selection', 'Please select a plugin to load.')
            return

        plugin_name = selected_items[0].text(0)

        try:
            success = self._plugin_manager.load_plugin(plugin_name)

            if success:
                QMessageBox.information(
                    self,
                    'Plugin Loaded',
                    f"Plugin '{plugin_name}' loaded successfully."
                )
                self._refresh_plugins()
            else:
                QMessageBox.warning(
                    self,
                    'Load Failed',
                    f"Failed to load plugin '{plugin_name}'."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Error',
                f"Error loading plugin '{plugin_name}': {str(e)}"
            )

    def _unload_selected_plugin(self) -> None:
        """Unload the selected plugin."""
        if not self._plugin_manager or not self._plugin_tree:
            return

        selected_items = self._plugin_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, 'No Selection', 'Please select a plugin to unload.')
            return

        plugin_name = selected_items[0].text(0)

        try:
            success = self._plugin_manager.unload_plugin(plugin_name)

            if success:
                QMessageBox.information(
                    self,
                    'Plugin Unloaded',
                    f"Plugin '{plugin_name}' unloaded successfully."
                )
                self._refresh_plugins()
            else:
                QMessageBox.warning(
                    self,
                    'Unload Failed',
                    f"Failed to unload plugin '{plugin_name}'."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Error',
                f"Error unloading plugin '{plugin_name}': {str(e)}"
            )

    def _reload_plugins(self) -> None:
        """Reload all active plugins."""
        if not self._plugin_manager:
            return

        try:
            plugins = self._plugin_manager.get_all_plugins()
            active_plugins = [p['name'] for p in plugins if p['state'] == 'active']

            for plugin_name in active_plugins:
                try:
                    self._plugin_manager.unload_plugin(plugin_name)
                    self._plugin_manager.load_plugin(plugin_name)
                except Exception as e:
                    self._logger.error(f"Error reloading plugin '{plugin_name}': {str(e)}")

            self._refresh_plugins()

            QMessageBox.information(
                self,
                'Plugins Reloaded',
                f'Reloaded {len(active_plugins)} active plugins.'
            )

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error reloading plugins: {str(e)}')

    def _update_logs_table(self, payload: dict) -> None:
        row_position = self._log_table.rowCount()
        self._log_table.insertRow(row_position)

        timestamp = payload.get('asctime') or payload.get('timestamp', '')
        level = payload.get('levelname') or payload.get('level', '')
        logger_name = payload.get('name') or payload.get('logger', '')
        event = payload.get('event', '')
        message = payload.get('message', '')
        task = payload.get('taskName', '')

        self._log_table.setItem(row_position, 0, QTableWidgetItem(str(timestamp)))
        level_color = None
        if str(level).upper() == 'ERROR':
            level_color = QColor('red')
        elif str(level).upper() == 'WARNING':
            level_color = QColor('orange')
        elif str(level).upper() == 'INFO':
            level_color = QColor('blue')
        elif str(level).upper() == 'DEBUG':
            level_color = QColor('gray')
        item = QTableWidgetItem(str(level))
        item.setForeground(QBrush(level_color))
        self._log_table.setItem(row_position, 1, item)
        self._log_table.setItem(row_position, 2, QTableWidgetItem(str(logger_name)))
        self._log_table.setItem(row_position, 3, QTableWidgetItem(str(event)))
        self._log_table.setItem(row_position, 4, QTableWidgetItem(str(message)))
        self._log_table.setItem(row_position, 5, QTableWidgetItem(str(task)))

        self._log_table.scrollToBottom()

    def _clear_logs(self) -> None:
        """Clear the log table display."""
        if self._log_table:
            self._log_table.setRowCount(0)

    def _update_metrics(self, metrics_data: Dict[str, Any]) -> None:
        """Update metrics display.

        Args:
            metrics_data: The metrics data.
        """
        if 'cpu_percent' in metrics_data:
            cpu_percent = metrics_data['cpu_percent']
            self._cpu_label.setText(f'{cpu_percent:.1f}%')
            self._cpu_progress.setValue(int(cpu_percent))
            self._set_progress_color(self._cpu_progress, cpu_percent)

        if 'memory_percent' in metrics_data:
            memory_percent = metrics_data['memory_percent']
            self._memory_label.setText(f'{memory_percent:.1f}%')
            self._memory_progress.setValue(int(memory_percent))
            self._set_progress_color(self._memory_progress, memory_percent)

        if 'disk_percent' in metrics_data:
            disk_percent = metrics_data['disk_percent']
            self._disk_label.setText(f'{disk_percent:.1f}%')
            self._disk_progress.setValue(int(disk_percent))
            self._set_progress_color(self._disk_progress, disk_percent)

    def _show_alert(self, alert_data: Dict[str, Any]) -> None:
        """Show an alert message.

        Args:
            alert_data: The alert data.
        """
        level = alert_data.get('level', 'info')
        message = alert_data.get('message', 'No message')

        if level == 'critical':
            QMessageBox.critical(self, 'Critical Alert', message)
        elif level == 'error':
            QMessageBox.critical(self, 'Error Alert', message)
        elif level == 'warning':
            QMessageBox.warning(self, 'Warning Alert', message)
        else:
            QMessageBox.information(self, 'Information Alert', message)

    def _on_log_event(self, event: Any) -> None:
        """Handle log events.

        Args:
            event: The event.
        """
        payload = event.payload

        # Unpack message if it's a JSON string
        message_content = payload.get('message', '')
        if isinstance(message_content, str):
            try:
                parsed = json.loads(message_content)
            except json.JSONDecodeError:
                parsed = {'message': message_content}
        else:
            parsed = message_content

        # Combine outer payload fields with parsed inner fields
        combined = {**payload, **parsed}

        self.update_signal.emit('log', combined)

    def _on_plugin_event(self, event: Any) -> None:
        """Handle plugin events.

        Args:
            event: The event.
        """
        self.update_signal.emit('plugin', None)

    def _on_metrics_event(self, event: Any) -> None:
        """Handle metrics events.

        Args:
            event: The event.
        """
        self.update_signal.emit('metrics', event.payload)

    def _on_alert_event(self, event: Any) -> None:
        """Handle alert events.

        Args:
            event: The event.
        """
        self.update_signal.emit('alert', event.payload)

    def _show_about_dialog(self) -> None:
        """Show the about dialog."""
        version = self._app_core.status().get('version', '0.1.0')

        QMessageBox.about(
            self,
            'About Qorzen',
            f'<h1>Qorzen</h1>'
            f'<p>Version: {version}</p>'
            f'<p>A modular, extensible platform for the automotive aftermarket industry.</p>'
            f'<p>Copyright &copy; 2025</p>'
        )

    def _get_status_icon(self, status: Optional[bool]) -> QIcon:
        """Get a status icon based on status.

        Args:
            status: The status value.

        Returns:
            A QIcon for the status.
        """
        if status is True:
            return QIcon()
        elif status is False:
            return QIcon()
        else:
            return QIcon()

    def _set_progress_color(self, progress_bar: QProgressBar, value: float) -> None:
        """Set the color of a progress bar based on value.

        Args:
            progress_bar: The progress bar.
            value: The value (0-100).
        """
        if value < 60:
            progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #4CAF50; }')
        elif value < 80:
            progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #FFC107; }')
        else:
            progress_bar.setStyleSheet('QProgressBar::chunk { background-color: #F44336; }')

    def closeEvent(self, event: Any) -> None:
        """Handle window close event.

        Args:
            event: The close event.
        """
        if self._event_bus:
            for subscription_id in self._event_subscriptions:
                self._event_bus.unsubscribe(subscription_id)

        self._update_timer.stop()

        if self._app_core:
            self._app_core.shutdown()

        event.accept()

    # Public methods for UI integration

    def get_menu(self, menu_title: str) -> Optional[QMenu]:
        """Get a menu by title.

        Args:
            menu_title: The menu title.

        Returns:
            The menu, or None if not found.
        """
        return self._menus.get(menu_title)

    def get_menubar(self) -> Any:
        """Get the menu bar.

        Returns:
            The menu bar.
        """
        return self.menuBar()


def start_ui(app_core: Any, debug: bool = False) -> None:
    """Start the UI.

    Args:
        app_core: The application core.
        debug: Whether to enable debug mode.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    main_window = QorzenMainWindow(app_core)
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    class MockAppCore:
        def __init__(self):
            self._managers = {}

        def get_manager(self, name):
            return self._managers.get(name)

        def status(self):
            return {
                'name': 'Application Core',
                'initialized': True,
                'healthy': True,
                'version': '0.1.0',
                'managers': {}
            }

        def shutdown(self):
            print('MockAppCore.shutdown() called')


    start_ui(MockAppCore(), True)