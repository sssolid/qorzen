from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QFrame, QMenu, QSpinBox, QTabWidget, QProgressBar, QCheckBox, QCalendarWidget, QDateEdit
from ..models import HistorySchedule
class HistoryScheduleDialog(QDialog):
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._schedule: Optional[HistorySchedule] = None
        self._name_edit: Optional[QLineEdit] = None
        self._description_edit: Optional[QTextEdit] = None
        self._connection_combo: Optional[QComboBox] = None
        self._query_combo: Optional[QComboBox] = None
        self._frequency_edit: Optional[QLineEdit] = None
        self._retention_spin: Optional[QSpinBox] = None
        self._active_check: Optional[QCheckBox] = None
        self._setup_ui()
    def _setup_ui(self) -> None:
        self.setWindowTitle('History Schedule Editor')
        self.setModal(True)
        self.resize(500, 400)
        layout = QVBoxLayout(self)
        basic_group = QGroupBox('Schedule Information')
        basic_layout = QFormLayout(basic_group)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText('Enter schedule name')
        basic_layout.addRow('Name:', self._name_edit)
        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(80)
        self._description_edit.setPlaceholderText('Enter schedule description (optional)')
        basic_layout.addRow('Description:', self._description_edit)
        self._connection_combo = QComboBox()
        basic_layout.addRow('Connection:', self._connection_combo)
        self._query_combo = QComboBox()
        basic_layout.addRow('Query:', self._query_combo)
        layout.addWidget(basic_group)
        settings_group = QGroupBox('Schedule Settings')
        settings_layout = QFormLayout(settings_group)
        freq_layout = QHBoxLayout()
        self._frequency_edit = QLineEdit()
        self._frequency_edit.setPlaceholderText('e.g., 1h, 30m, 1d')
        freq_layout.addWidget(self._frequency_edit)
        freq_help = QLabel('Format: number + unit (s/m/h/d/w)')
        freq_help.setStyleSheet('color: gray; font-size: 10px;')
        freq_layout.addWidget(freq_help)
        settings_layout.addRow('Frequency:', freq_layout)
        self._retention_spin = QSpinBox()
        self._retention_spin.setRange(1, 3650)
        self._retention_spin.setValue(365)
        self._retention_spin.setSuffix(' days')
        settings_layout.addRow('Retention Period:', self._retention_spin)
        self._active_check = QCheckBox('Schedule is active')
        self._active_check.setChecked(True)
        settings_layout.addRow('', self._active_check)
        layout.addWidget(settings_group)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    def set_connections(self, connections: List[Any]) -> None:
        self._connection_combo.clear()
        self._connection_combo.addItem('-- Select Connection --', None)
        for connection in connections:
            self._connection_combo.addItem(connection.name, connection.id)
    def set_queries(self, queries: List[Any]) -> None:
        self._query_combo.clear()
        self._query_combo.addItem('-- Select Query --', None)
        for query in queries:
            self._query_combo.addItem(query.name, query.id)
    def set_schedule(self, schedule: HistorySchedule) -> None:
        self._schedule = schedule
        self._name_edit.setText(schedule.name)
        self._description_edit.setPlainText(schedule.description or '')
        conn_index = self._connection_combo.findData(schedule.connection_id)
        if conn_index >= 0:
            self._connection_combo.setCurrentIndex(conn_index)
        query_index = self._query_combo.findData(schedule.query_id)
        if query_index >= 0:
            self._query_combo.setCurrentIndex(query_index)
        self._frequency_edit.setText(schedule.frequency)
        self._retention_spin.setValue(schedule.retention_days)
        self._active_check.setChecked(schedule.active)
    def get_schedule(self) -> HistorySchedule:
        name = self._name_edit.text().strip()
        if not name:
            raise ValueError('Schedule name is required')
        connection_id = self._connection_combo.currentData()
        if not connection_id:
            raise ValueError('Connection is required')
        query_id = self._query_combo.currentData()
        if not query_id:
            raise ValueError('Query is required')
        frequency = self._frequency_edit.text().strip()
        if not frequency:
            raise ValueError('Frequency is required')
        if self._schedule:
            self._schedule.name = name
            self._schedule.description = self._description_edit.toPlainText().strip() or None
            self._schedule.connection_id = connection_id
            self._schedule.query_id = query_id
            self._schedule.frequency = frequency
            self._schedule.retention_days = self._retention_spin.value()
            self._schedule.active = self._active_check.isChecked()
            self._schedule.updated_at = datetime.now()
            return self._schedule
        else:
            return HistorySchedule(name=name, description=self._description_edit.toPlainText().strip() or None, connection_id=connection_id, query_id=query_id, frequency=frequency, retention_days=self._retention_spin.value(), active=self._active_check.isChecked())
class HistoryTab(QWidget):
    operation_started = Signal(str)
    operation_finished = Signal()
    status_changed = Signal(str)
    def __init__(self, plugin: Any, logger: logging.Logger, concurrency_manager: Any, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._concurrency_manager = concurrency_manager
        self._schedules_table: Optional[QTableWidget] = None
        self._history_tree: Optional[QTreeWidget] = None
        self._schedule_details: Optional[QTextEdit] = None
        self._snapshot_details: Optional[QTextEdit] = None
        self._current_schedules: List[Dict[str, Any]] = []
        self._current_entries: List[Dict[str, Any]] = []
        self._connections: List[Any] = []
        self._queries: List[Any] = []
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(lambda: asyncio.create_task(self._refresh_schedules()))
        self._refresh_timer.start(60000)
        self._setup_ui()
        self._setup_connections()
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        schedules_tab = self._create_schedules_tab()
        tab_widget.addTab(schedules_tab, 'History Schedules')
        history_tab = self._create_history_tab()
        tab_widget.addTab(history_tab, 'Historical Data')
        analytics_tab = self._create_analytics_tab()
        tab_widget.addTab(analytics_tab, 'Analytics')
        layout.addWidget(tab_widget)
    def _create_schedules_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        toolbar = self._create_schedules_toolbar()
        layout.addWidget(toolbar)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = self._create_schedules_list_panel()
        splitter.addWidget(left_panel)
        right_panel = self._create_schedule_details_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)
        return tab
    def _create_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        history_toolbar = self._create_history_toolbar()
        layout.addWidget(history_toolbar)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = self._create_history_tree_panel()
        splitter.addWidget(left_panel)
        right_panel = self._create_snapshot_details_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)
        return tab
    def _create_analytics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        placeholder = QLabel('Historical data analytics would be implemented here')
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet('color: gray; font-size: 14px;')
        layout.addWidget(placeholder)
        return tab
    def _create_schedules_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(toolbar)
        layout.addWidget(QLabel('History Schedules:'))
        layout.addStretch()
        new_schedule_button = QPushButton('New Schedule')
        new_schedule_button.clicked.connect(self._create_schedule)
        layout.addWidget(new_schedule_button)
        edit_schedule_button = QPushButton('Edit')
        edit_schedule_button.clicked.connect(self._edit_schedule)
        layout.addWidget(edit_schedule_button)
        run_now_button = QPushButton('Run Now')
        run_now_button.clicked.connect(self._run_schedule_now)
        layout.addWidget(run_now_button)
        delete_schedule_button = QPushButton('Delete')
        delete_schedule_button.clicked.connect(self._delete_schedule)
        layout.addWidget(delete_schedule_button)
        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(lambda: asyncio.create_task(self.refresh()))
        layout.addWidget(refresh_button)
        return toolbar
    def _create_history_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(toolbar)
        layout.addWidget(QLabel('Historical Data:'))
        layout.addStretch()
        view_data_button = QPushButton('View Data')
        view_data_button.clicked.connect(self._view_snapshot_data)
        layout.addWidget(view_data_button)
        export_data_button = QPushButton('Export Data')
        export_data_button.clicked.connect(self._export_snapshot_data)
        layout.addWidget(export_data_button)
        delete_snapshot_button = QPushButton('Delete Snapshot')
        delete_snapshot_button.clicked.connect(self._delete_snapshot)
        layout.addWidget(delete_snapshot_button)
        return toolbar
    def _create_schedules_list_panel(self) -> QGroupBox:
        group = QGroupBox('History Schedules')
        layout = QVBoxLayout(group)
        self._schedules_table = QTableWidget()
        self._schedules_table.setColumnCount(6)
        self._schedules_table.setHorizontalHeaderLabels(['Name', 'Connection', 'Query', 'Frequency', 'Last Run', 'Active'])
        self._schedules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._schedules_table.setAlternatingRowColors(True)
        self._schedules_table.itemSelectionChanged.connect(self._on_schedule_selection_changed)
        self._schedules_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._schedules_table.customContextMenuRequested.connect(self._show_schedule_context_menu)
        header = self._schedules_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._schedules_table)
        return group
    def _create_schedule_details_panel(self) -> QGroupBox:
        group = QGroupBox('Schedule Details')
        layout = QVBoxLayout(group)
        self._schedule_details = QTextEdit()
        self._schedule_details.setReadOnly(True)
        self._schedule_details.setPlaceholderText('Select a schedule to view details')
        layout.addWidget(self._schedule_details)
        return group
    def _create_history_tree_panel(self) -> QGroupBox:
        group = QGroupBox('Historical Data')
        layout = QVBoxLayout(group)
        self._history_tree = QTreeWidget()
        self._history_tree.setHeaderLabels(['Schedule', 'Table', 'Collected At', 'Records', 'Status'])
        self._history_tree.setAlternatingRowColors(True)
        self._history_tree.itemSelectionChanged.connect(self._on_history_selection_changed)
        layout.addWidget(self._history_tree)
        return group
    def _create_snapshot_details_panel(self) -> QGroupBox:
        group = QGroupBox('Snapshot Details')
        layout = QVBoxLayout(group)
        self._snapshot_details = QTextEdit()
        self._snapshot_details.setReadOnly(True)
        self._snapshot_details.setPlaceholderText('Select a snapshot to view details')
        layout.addWidget(self._snapshot_details)
        return group
    def _setup_connections(self) -> None:
        asyncio.create_task(self.refresh())
    async def refresh(self) -> None:
        try:
            self.operation_started.emit('Refreshing history data...')
            await self._load_connections()
            await self._load_queries()
            await self._refresh_schedules()
            await self._refresh_history()
            self.operation_finished.emit()
            self.status_changed.emit('History data refreshed')
        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f'Failed to refresh history tab: {e}')
            self._show_error('Refresh Error', f'Failed to refresh data: {e}')
    async def _load_connections(self) -> None:
        try:
            self._connections = await self._plugin.get_connections()
        except Exception as e:
            self._logger.error(f'Failed to load connections: {e}')
    async def _load_queries(self) -> None:
        try:
            self._queries = await self._plugin.get_saved_queries()
        except Exception as e:
            self._logger.error(f'Failed to load queries: {e}')
    async def _refresh_schedules(self) -> None:
        try:
            schedules = await self._plugin.get_history_schedules()
            self._current_schedules = schedules
            self._populate_schedules_table()
        except Exception as e:
            self._logger.error(f'Failed to refresh schedules: {e}')
    async def _refresh_history(self) -> None:
        try:
            self._current_entries = []
            self._populate_history_tree()
        except Exception as e:
            self._logger.error(f'Failed to refresh history: {e}')
    def _populate_schedules_table(self) -> None:
        try:
            self._schedules_table.setRowCount(len(self._current_schedules))
            for row, schedule in enumerate(self._current_schedules):
                name_item = QTableWidgetItem(schedule.get('name', 'Unknown'))
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._schedules_table.setItem(row, 0, name_item)
                connection_item = QTableWidgetItem(schedule.get('connection_id', 'Unknown'))
                connection_item.setFlags(connection_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._schedules_table.setItem(row, 1, connection_item)
                query_item = QTableWidgetItem(schedule.get('query_id', 'Unknown'))
                query_item.setFlags(query_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._schedules_table.setItem(row, 2, query_item)
                frequency_item = QTableWidgetItem(schedule.get('frequency', 'Unknown'))
                frequency_item.setFlags(frequency_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._schedules_table.setItem(row, 3, frequency_item)
                last_run = schedule.get('last_run')
                last_run_text = last_run.strftime('%Y-%m-%d %H:%M') if last_run else 'Never'
                last_run_item = QTableWidgetItem(last_run_text)
                last_run_item.setFlags(last_run_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._schedules_table.setItem(row, 4, last_run_item)
                active_item = QTableWidgetItem('Yes' if schedule.get('active', True) else 'No')
                active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._schedules_table.setItem(row, 5, active_item)
                name_item.setData(Qt.ItemDataRole.UserRole, schedule)
        except Exception as e:
            self._logger.error(f'Failed to populate schedules table: {e}')
    def _populate_history_tree(self) -> None:
        try:
            self._history_tree.clear()
            entries_by_schedule = {}
            for entry in self._current_entries:
                schedule_id = entry.get('schedule_id', 'Unknown')
                if schedule_id not in entries_by_schedule:
                    entries_by_schedule[schedule_id] = []
                entries_by_schedule[schedule_id].append(entry)
            for schedule_id, entries in entries_by_schedule.items():
                schedule_item = QTreeWidgetItem([schedule_id, '', '', '', ''])
                for entry in entries:
                    entry_item = QTreeWidgetItem(['', entry.get('table_name', 'Unknown'), entry.get('collected_at', '').strftime('%Y-%m-%d %H:%M') if entry.get('collected_at') else '', str(entry.get('record_count', 0)), entry.get('status', 'Unknown')])
                    entry_item.setData(0, Qt.ItemDataRole.UserRole, entry)
                    schedule_item.addChild(entry_item)
                self._history_tree.addTopLevelItem(schedule_item)
            self._history_tree.expandAll()
        except Exception as e:
            self._logger.error(f'Failed to populate history tree: {e}')
    def _on_schedule_selection_changed(self) -> None:
        try:
            current_row = self._schedules_table.currentRow()
            if current_row < 0 or current_row >= len(self._current_schedules):
                self._schedule_details.clear()
                return
            schedule = self._current_schedules[current_row]
            self._show_schedule_details(schedule)
        except Exception as e:
            self._logger.error(f'Error handling schedule selection: {e}')
    def _on_history_selection_changed(self) -> None:
        try:
            current_item = self._history_tree.currentItem()
            if not current_item:
                self._snapshot_details.clear()
                return
            entry = current_item.data(0, Qt.ItemDataRole.UserRole)
            if entry:
                self._show_snapshot_details(entry)
        except Exception as e:
            self._logger.error(f'Error handling history selection: {e}')
    def _show_schedule_details(self, schedule: Dict[str, Any]) -> None:
        try:
            details_parts = []
            details_parts.append(f"Name: {schedule.get('name', 'Unknown')}")
            details_parts.append(f"Description: {schedule.get('description', 'No description')}")
            details_parts.append(f"Connection: {schedule.get('connection_id', 'Unknown')}")
            details_parts.append(f"Query: {schedule.get('query_id', 'Unknown')}")
            details_parts.append(f"Frequency: {schedule.get('frequency', 'Unknown')}")
            details_parts.append(f"Retention: {schedule.get('retention_days', 0)} days")
            details_parts.append(f"Active: {('Yes' if schedule.get('active', True) else 'No')}")
            details_parts.append('')
            last_run = schedule.get('last_run')
            if last_run:
                details_parts.append(f"Last Run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                details_parts.append('Last Run: Never')
            if 'created_at' in schedule:
                details_parts.append(f"Created: {schedule['created_at']}")
            if 'updated_at' in schedule:
                details_parts.append(f"Updated: {schedule['updated_at']}")
            self._schedule_details.setPlainText('\n'.join(details_parts))
        except Exception as e:
            self._logger.error(f'Failed to show schedule details: {e}')
    def _show_snapshot_details(self, entry: Dict[str, Any]) -> None:
        try:
            details_parts = []
            details_parts.append(f"Schedule: {entry.get('schedule_id', 'Unknown')}")
            details_parts.append(f"Table: {entry.get('table_name', 'Unknown')}")
            details_parts.append(f"Records: {entry.get('record_count', 0):,}")
            details_parts.append(f"Status: {entry.get('status', 'Unknown')}")
            details_parts.append('')
            collected_at = entry.get('collected_at')
            if collected_at:
                details_parts.append(f"Collected At: {collected_at.strftime('%Y-%m-%d %H:%M:%S')}")
            snapshot_id = entry.get('snapshot_id')
            if snapshot_id:
                details_parts.append(f'Snapshot ID: {snapshot_id}')
            error_message = entry.get('error_message')
            if error_message:
                details_parts.append('')
                details_parts.append(f'Error: {error_message}')
            self._snapshot_details.setPlainText('\n'.join(details_parts))
        except Exception as e:
            self._logger.error(f'Failed to show snapshot details: {e}')
    def _create_schedule(self) -> None:
        dialog = HistoryScheduleDialog(self)
        dialog.set_connections(self._connections)
        dialog.set_queries(self._queries)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                schedule = dialog.get_schedule()
                asyncio.create_task(self._create_schedule_async(schedule))
            except ValueError as e:
                self._show_warning('Validation Error', str(e))
    async def _create_schedule_async(self, schedule: HistorySchedule) -> None:
        try:
            self.operation_started.emit('Creating history schedule...')
            await self._plugin.create_history_schedule(connection_id=schedule.connection_id, query_id=schedule.query_id, frequency=schedule.frequency, name=schedule.name, description=schedule.description, retention_days=schedule.retention_days)
            await self._refresh_schedules()
            self.operation_finished.emit()
            self.status_changed.emit(f'Created history schedule: {schedule.name}')
        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f'Failed to create history schedule: {e}')
            self._show_error('Create Error', f'Failed to create history schedule: {e}')
    def _edit_schedule(self) -> None:
        current_row = self._schedules_table.currentRow()
        if current_row < 0:
            self._show_warning('No Selection', 'Please select a schedule to edit')
            return
        self._show_info('Edit Schedule', 'Schedule editing would be implemented here')
    def _run_schedule_now(self) -> None:
        current_row = self._schedules_table.currentRow()
        if current_row < 0:
            self._show_warning('No Selection', 'Please select a schedule to run')
            return
        schedule = self._current_schedules[current_row]
        schedule_id = schedule.get('id')
        if schedule_id:
            asyncio.create_task(self._run_schedule_async(schedule_id))
    async def _run_schedule_async(self, schedule_id: str) -> None:
        try:
            self.operation_started.emit('Running history schedule...')
            await self._refresh_schedules()
            await self._refresh_history()
            self.operation_finished.emit()
            self.status_changed.emit('History schedule executed')
        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f'Failed to run history schedule: {e}')
            self._show_error('Execution Error', f'Failed to run history schedule: {e}')
    def _delete_schedule(self) -> None:
        current_row = self._schedules_table.currentRow()
        if current_row < 0:
            self._show_warning('No Selection', 'Please select a schedule to delete')
            return
        schedule = self._current_schedules[current_row]
        reply = QMessageBox.question(self, 'Confirm Deletion', f"Are you sure you want to delete the schedule '{schedule.get('name', 'Unknown')}'?\n\nThis will also delete all associated historical data.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            schedule_id = schedule.get('id')
            if schedule_id:
                asyncio.create_task(self._delete_schedule_async(schedule_id))
    async def _delete_schedule_async(self, schedule_id: str) -> None:
        try:
            self.operation_started.emit('Deleting history schedule...')
            await self._refresh_schedules()
            await self._refresh_history()
            self.operation_finished.emit()
            self.status_changed.emit('History schedule deleted')
        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f'Failed to delete history schedule: {e}')
            self._show_error('Delete Error', f'Failed to delete history schedule: {e}')
    def _view_snapshot_data(self) -> None:
        self._show_info('View Data', 'Snapshot data viewing would be implemented here')
    def _export_snapshot_data(self) -> None:
        self._show_info('Export Data', 'Snapshot data export would be implemented here')
    def _delete_snapshot(self) -> None:
        self._show_info('Delete Snapshot', 'Snapshot deletion would be implemented here')
    def _show_schedule_context_menu(self, position) -> None:
        item = self._schedules_table.itemAt(position)
        if not item:
            return
        menu = QMenu(self)
        edit_action = menu.addAction('Edit Schedule')
        edit_action.triggered.connect(self._edit_schedule)
        run_action = menu.addAction('Run Now')
        run_action.triggered.connect(self._run_schedule_now)
        menu.addSeparator()
        enable_action = menu.addAction('Enable/Disable')
        enable_action.triggered.connect(self._toggle_schedule)
        delete_action = menu.addAction('Delete Schedule')
        delete_action.triggered.connect(self._delete_schedule)
        menu.exec(self._schedules_table.mapToGlobal(position))
    def _toggle_schedule(self) -> None:
        self._show_info('Toggle Schedule', 'Schedule enable/disable would be implemented here')
    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
    def _show_warning(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
    def _show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)
    def cleanup(self) -> None:
        try:
            if self._refresh_timer:
                self._refresh_timer.stop()
            self._current_schedules.clear()
            self._current_entries.clear()
            self._connections.clear()
            self._queries.clear()
        except Exception as e:
            self._logger.error(f'Error during cleanup: {e}')