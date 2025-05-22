from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QSpinBox, QCheckBox, QTextEdit, QSplitter, QFrame, QMessageBox, QFileDialog, QProgressBar, QMenu
from ..models import QueryResult, ExportFormat, ExportSettings
class ResultsTab(QWidget):
    operation_started = Signal(str)
    operation_finished = Signal()
    status_changed = Signal(str)
    def __init__(self, plugin: Any, logger: logging.Logger, concurrency_manager: Any, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._concurrency_manager = concurrency_manager
        self._results_table: Optional[QTableWidget] = None
        self._info_text: Optional[QTextEdit] = None
        self._export_format_combo: Optional[QComboBox] = None
        self._include_headers_check: Optional[QCheckBox] = None
        self._max_rows_spin: Optional[QSpinBox] = None
        self._row_count_label: Optional[QLabel] = None
        self._execution_time_label: Optional[QLabel] = None
        self._connection_label: Optional[QLabel] = None
        self._current_result: Optional[QueryResult] = None
        self._setup_ui()
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        info_panel = self._create_info_panel()
        layout.addWidget(info_panel)
        splitter = QSplitter(Qt.Orientation.Vertical)
        table_widget = self._create_results_table()
        splitter.addWidget(table_widget)
        query_info_widget = self._create_query_info_panel()
        splitter.addWidget(query_info_widget)
        splitter.setSizes([800, 200])
        layout.addWidget(splitter)
        export_panel = self._create_export_panel()
        layout.addWidget(export_panel)
    def _create_info_panel(self) -> QFrame:
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(60)
        layout = QHBoxLayout(panel)
        self._connection_label = QLabel('Connection: None')
        layout.addWidget(self._connection_label)
        layout.addStretch()
        self._row_count_label = QLabel('Rows: 0')
        layout.addWidget(self._row_count_label)
        self._execution_time_label = QLabel('Time: 0ms')
        layout.addWidget(self._execution_time_label)
        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(lambda: asyncio.create_task(self.refresh()))
        layout.addWidget(refresh_button)
        return panel
    def _create_results_table(self) -> QGroupBox:
        group = QGroupBox('Query Results')
        layout = QVBoxLayout(group)
        self._results_table = QTableWidget()
        self._results_table.setAlternatingRowColors(True)
        self._results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._results_table.customContextMenuRequested.connect(self._show_table_context_menu)
        header = self._results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self._results_table)
        return group
    def _create_query_info_panel(self) -> QGroupBox:
        group = QGroupBox('Query Information')
        layout = QVBoxLayout(group)
        self._info_text = QTextEdit()
        self._info_text.setReadOnly(True)
        self._info_text.setMaximumHeight(150)
        layout.addWidget(self._info_text)
        return group
    def _create_export_panel(self) -> QGroupBox:
        group = QGroupBox('Export Results')
        layout = QHBoxLayout(group)
        layout.addWidget(QLabel('Format:'))
        self._export_format_combo = QComboBox()
        for format in ExportFormat:
            self._export_format_combo.addItem(format.value.upper(), format)
        layout.addWidget(self._export_format_combo)
        self._include_headers_check = QCheckBox('Include Headers')
        self._include_headers_check.setChecked(True)
        layout.addWidget(self._include_headers_check)
        layout.addWidget(QLabel('Max Rows:'))
        self._max_rows_spin = QSpinBox()
        self._max_rows_spin.setRange(0, 1000000)
        self._max_rows_spin.setValue(0)
        self._max_rows_spin.setSpecialValueText('All')
        layout.addWidget(self._max_rows_spin)
        layout.addStretch()
        export_button = QPushButton('Export...')
        export_button.clicked.connect(self._export_results)
        layout.addWidget(export_button)
        return group
    def show_results(self, result: QueryResult) -> None:
        try:
            self._current_result = result
            self._update_info_labels()
            self._populate_results_table()
            self._update_query_info()
            self.status_changed.emit(f'Showing {result.row_count} rows')
        except Exception as e:
            self._logger.error(f'Failed to show results: {e}')
            self._show_error('Display Error', f'Failed to display results: {e}')
    def _update_info_labels(self) -> None:
        if not self._current_result:
            self._connection_label.setText('Connection: None')
            self._row_count_label.setText('Rows: 0')
            self._execution_time_label.setText('Time: 0ms')
            return
        result = self._current_result
        self._connection_label.setText(f'Connection: {result.connection_id}')
        row_text = f'Rows: {result.row_count:,}'
        if result.truncated:
            row_text += ' (truncated)'
        self._row_count_label.setText(row_text)
        self._execution_time_label.setText(f'Time: {result.execution_time_ms:,}ms')
    def _populate_results_table(self) -> None:
        if not self._current_result:
            self._results_table.setRowCount(0)
            self._results_table.setColumnCount(0)
            return
        try:
            result = self._current_result
            records = result.records
            columns = result.columns
            if not records or not columns:
                self._results_table.setRowCount(0)
                self._results_table.setColumnCount(0)
                return
            self._results_table.setRowCount(len(records))
            self._results_table.setColumnCount(len(columns))
            column_names = [col.get('name', f'Column {i + 1}') for i, col in enumerate(columns)]
            self._results_table.setHorizontalHeaderLabels(column_names)
            for row_idx, record in enumerate(records):
                for col_idx, column in enumerate(columns):
                    column_name = column.get('name', f'Column {col_idx + 1}')
                    value = record.get(column_name, '')
                    display_value = self._format_cell_value(value)
                    item = QTableWidgetItem(str(display_value))
                    item.setToolTip(str(display_value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self._results_table.setItem(row_idx, col_idx, item)
            self._results_table.resizeColumnsToContents()
            header = self._results_table.horizontalHeader()
            for i in range(self._results_table.columnCount()):
                if header.sectionSize(i) > 300:
                    header.resizeSection(i, 300)
        except Exception as e:
            self._logger.error(f'Failed to populate results table: {e}')
            self._show_error('Table Error', f'Failed to populate table: {e}')
    def _format_cell_value(self, value: Any) -> str:
        if value is None:
            return '<NULL>'
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                return f'{value:.6g}'
            return str(value)
        elif isinstance(value, str):
            if len(value) > 1000:
                return value[:1000] + '...'
            return value
        else:
            return str(value)
    def _update_query_info(self) -> None:
        if not self._current_result:
            self._info_text.clear()
            return
        result = self._current_result
        info_parts = []
        info_parts.append(f"Query executed at: {result.executed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        info_parts.append(f'Connection: {result.connection_id}')
        info_parts.append(f'Rows returned: {result.row_count:,}')
        info_parts.append(f'Execution time: {result.execution_time_ms:,} ms')
        if result.truncated:
            info_parts.append('⚠️ Results were truncated due to row limit')
        if result.applied_mapping:
            info_parts.append('✓ Field mappings were applied')
        if result.has_error:
            info_parts.append(f'❌ Error: {result.error_message}')
        if result.columns:
            info_parts.append('')
            info_parts.append('Columns:')
            for i, column in enumerate(result.columns, 1):
                col_info = f"  {i}. {column.get('name', 'Unknown')} ({column.get('type_name', 'Unknown')})"
                if not column.get('nullable', True):
                    col_info += ' NOT NULL'
                info_parts.append(col_info)
        if result.query:
            info_parts.append('')
            info_parts.append('Query:')
            query_lines = result.query.split('\n')
            if len(query_lines) > 10:
                info_parts.extend(query_lines[:10])
                info_parts.append('... (truncated)')
            else:
                info_parts.extend(query_lines)
        self._info_text.setPlainText('\n'.join(info_parts))
    def _export_results(self) -> None:
        if not self._current_result or not self._current_result.records:
            self._show_warning('No Data', 'No data to export')
            return
        export_format = self._export_format_combo.currentData()
        if not export_format:
            self._show_error('Export Error', 'Please select an export format')
            return
        if hasattr(self._plugin, '_export_service') and self._plugin._export_service:
            file_ext = self._plugin._export_service.get_file_extension(export_format)
        else:
            file_ext = '.txt'
        file_path, _ = QFileDialog.getSaveFileName(self, 'Export Results', f'query_results{file_ext}', f'{export_format.value.upper()} Files (*{file_ext});;All Files (*)')
        if not file_path:
            return
        asyncio.create_task(self._export_results_async(file_path, export_format))
    async def _export_results_async(self, file_path: str, export_format: ExportFormat) -> None:
        try:
            self.operation_started.emit('Exporting results...')
            settings = ExportSettings(format=export_format, include_headers=self._include_headers_check.isChecked(), max_rows=self._max_rows_spin.value() if self._max_rows_spin.value() > 0 else None)
            actual_path = await self._plugin.export_results(results=self._current_result, format=export_format, file_path=file_path, settings=settings)
            self.operation_finished.emit()
            exported_rows = min(len(self._current_result.records), settings.max_rows or len(self._current_result.records))
            self._show_info('Export Complete', f'Successfully exported {exported_rows:,} rows to:\n{actual_path}')
            self.status_changed.emit(f'Exported {exported_rows:,} rows to {export_format.value}')
        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f'Export failed: {e}')
            self._show_error('Export Error', f'Failed to export results: {e}')
    def _show_table_context_menu(self, position) -> None:
        if not self._current_result or not self._current_result.records:
            return
        menu = QMenu(self)
        copy_cell_action = menu.addAction('Copy Cell')
        copy_cell_action.triggered.connect(self._copy_cell)
        copy_row_action = menu.addAction('Copy Row')
        copy_row_action.triggered.connect(self._copy_row)
        copy_column_action = menu.addAction('Copy Column')
        copy_column_action.triggered.connect(self._copy_column)
        menu.addSeparator()
        export_visible_action = menu.addAction('Export Visible Data')
        export_visible_action.triggered.connect(self._export_results)
        menu.exec(self._results_table.mapToGlobal(position))
    def _copy_cell(self) -> None:
        current_item = self._results_table.currentItem()
        if current_item:
            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(current_item.text())
    def _copy_row(self) -> None:
        current_row = self._results_table.currentRow()
        if current_row >= 0:
            row_data = []
            for col in range(self._results_table.columnCount()):
                item = self._results_table.item(current_row, col)
                row_data.append(item.text() if item else '')
            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText('\t'.join(row_data))
    def _copy_column(self) -> None:
        current_col = self._results_table.currentColumn()
        if current_col >= 0:
            col_data = []
            header_item = self._results_table.horizontalHeaderItem(current_col)
            if header_item:
                col_data.append(header_item.text())
            for row in range(self._results_table.rowCount()):
                item = self._results_table.item(row, current_col)
                col_data.append(item.text() if item else '')
            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText('\n'.join(col_data))
    async def refresh(self) -> None:
        try:
            if self._current_result:
                self._populate_results_table()
                self._update_query_info()
                self.status_changed.emit('Results refreshed')
        except Exception as e:
            self._logger.error(f'Failed to refresh results: {e}')
            self._show_error('Refresh Error', f'Failed to refresh results: {e}')
    def clear_results(self) -> None:
        self._current_result = None
        self._results_table.setRowCount(0)
        self._results_table.setColumnCount(0)
        self._info_text.clear()
        self._update_info_labels()
        self.status_changed.emit('Results cleared')
    def get_current_result(self) -> Optional[QueryResult]:
        return self._current_result
    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
    def _show_warning(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
    def _show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)
    def cleanup(self) -> None:
        try:
            self.clear_results()
        except Exception as e:
            self._logger.error(f'Error during cleanup: {e}')