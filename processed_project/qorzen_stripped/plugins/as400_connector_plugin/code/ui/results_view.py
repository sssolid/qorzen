from __future__ import annotations
'\nResults view for AS400 Connector Plugin.\n\nThis module provides a customizable view for displaying and working with AS400 \nquery results, including features for sorting, filtering, exporting, and data visualization.\n'
import csv
import datetime
import io
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QAbstractTableModel, QEvent, QItemSelectionModel, QModelIndex, QObject, QPoint, QSortFilterProxyModel, Qt, Signal, Slot, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QContextMenuEvent, QFont, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QTableView, QToolBar, QVBoxLayout, QWidget
from qorzen.plugins.as400_connector_plugin.code.models import ColumnMetadata, QueryResult
from qorzen.plugins.as400_connector_plugin.code.utils import format_value_for_display
class QueryResultsTableModel(QAbstractTableModel):
    def __init__(self, parent: Optional[QObject]=None) -> None:
        super().__init__(parent)
        self._result: Optional[QueryResult] = None
        self._columns: List[ColumnMetadata] = []
        self._records: List[Dict[str, Any]] = []
        self._column_names: List[str] = []
    def setQueryResult(self, result: QueryResult) -> None:
        self.beginResetModel()
        self._result = result
        self._columns = result.columns
        self._records = result.records
        self._column_names = [col.name for col in self._columns]
        self.endResetModel()
    def rowCount(self, parent: QModelIndex=QModelIndex()) -> int:
        if parent.isValid() or not self._records:
            return 0
        return len(self._records)
    def columnCount(self, parent: QModelIndex=QModelIndex()) -> int:
        if parent.isValid() or not self._columns:
            return 0
        return len(self._columns)
    def data(self, index: QModelIndex, role: int=Qt.DisplayRole) -> Any:
        if not index.isValid() or not self._records:
            return None
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._records) or col < 0 or (col >= len(self._columns)):
            return None
        column_name = self._column_names[col]
        value = self._records[row].get(column_name)
        if role == Qt.DisplayRole:
            return format_value_for_display(value)
        elif role == Qt.EditRole:
            return value
        elif role == Qt.TextAlignmentRole:
            if isinstance(value, (int, float, complex)) or (isinstance(value, str) and value.isdigit()):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        elif role == Qt.BackgroundRole:
            if value is None:
                return QBrush(QColor(240, 240, 240))
            return None
        elif role == Qt.ForegroundRole:
            if value is None:
                return QBrush(QColor(120, 120, 120))
            return None
        elif role == Qt.ToolTipRole:
            if value is not None:
                display_value = format_value_for_display(value)
                if len(display_value) > 50:
                    return display_value
            return None
        return None
    def headerData(self, section: int, orientation: Qt.Orientation, role: int=Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal and section < len(self._columns):
                col = self._columns[section]
                return f'{col.name} ({col.type_name})'
            elif orientation == Qt.Vertical:
                return str(section + 1)
        elif role == Qt.ToolTipRole:
            if orientation == Qt.Horizontal and section < len(self._columns):
                col = self._columns[section]
                nullable = 'NULL allowed' if col.nullable else 'NOT NULL'
                return f'Name: {col.name}\nType: {col.type_name}\nPrecision: {col.precision}\nScale: {col.scale}\n{nullable}'
        return None
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    def getColumnType(self, column: int) -> Optional[str]:
        if column < 0 or column >= len(self._columns):
            return None
        return self._columns[column].type_name
    def getRecord(self, row: int) -> Optional[Dict[str, Any]]:
        if row < 0 or row >= len(self._records):
            return None
        return self._records[row]
    def getAllRecords(self) -> List[Dict[str, Any]]:
        return self._records
    def getColumnMetadata(self, column: int) -> Optional[ColumnMetadata]:
        if column < 0 or column >= len(self._columns):
            return None
        return self._columns[column]
class ResultsFilterHeader(QHeaderView):
    filterChanged = Signal(int, str)
    def __init__(self, orientation: Qt.Orientation, parent: Optional[QWidget]=None) -> None:
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setSortIndicatorShown(True)
        self._filter_widgets: Dict[int, QLineEdit] = {}
        self._filter_boxes: Dict[int, QWidget] = {}
        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)
    def setFilterBoxes(self, count: int) -> None:
        for widget in self._filter_boxes.values():
            widget.deleteLater()
        self._filter_widgets = {}
        self._filter_boxes = {}
        for i in range(count):
            filter_box = QWidget(self)
            layout = QHBoxLayout(filter_box)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(0)
            filter_edit = QLineEdit(filter_box)
            filter_edit.setPlaceholderText('Filter...')
            filter_edit.setClearButtonEnabled(True)
            filter_edit.textChanged.connect(lambda text, col=i: self.filterChanged.emit(col, text))
            layout.addWidget(filter_edit)
            self._filter_widgets[i] = filter_edit
            self._filter_boxes[i] = filter_box
        self.adjustPositions()
    def adjustPositions(self) -> None:
        for column, widget in self._filter_boxes.items():
            x_pos = self.sectionViewportPosition(column)
            width = self.sectionSize(column) - 2
            widget.setGeometry(x_pos, self.height() - 25, width, 23)
    def sectionResized(self, logicalIndex: int, oldSize: int, newSize: int) -> None:
        super().sectionResized(logicalIndex, oldSize, newSize)
        self.adjustPositions()
    def sectionMoved(self, logicalIndex: int, oldVisualIndex: int, newVisualIndex: int) -> None:
        super().sectionMoved(logicalIndex, oldVisualIndex, newVisualIndex)
        self.adjustPositions()
    def sizeHint(self) -> QSize:
        size = super().sizeHint()
        size.setHeight(size.height() + 25)
        return size
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj == self.viewport():
            if event.type() == QEvent.MouseMove:
                self.updateCursor(event.pos())
            return False
        return super().eventFilter(obj, event)
    def updateCursor(self, pos: QPoint) -> None:
        pass
class ResultsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: Optional[QObject]=None) -> None:
        super().__init__(parent)
        self._column_filters: Dict[int, str] = {}
    def setFilterText(self, column: int, text: str) -> None:
        if not text:
            if column in self._column_filters:
                del self._column_filters[column]
        else:
            self._column_filters[column] = text
        self.invalidateFilter()
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._column_filters:
            return True
        source_model = self.sourceModel()
        for column, filter_text in self._column_filters.items():
            if not filter_text:
                continue
            index = source_model.index(source_row, column, source_parent)
            data = source_model.data(index, Qt.DisplayRole)
            if data is None:
                data = 'NULL'
            else:
                data = str(data).lower()
            if filter_text.lower() not in data:
                return False
        return True
class DataPreviewDialog(QDialog):
    def __init__(self, record: Dict[str, Any], columns: List[ColumnMetadata], parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Record Preview')
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        for column in columns:
            name = column.name
            value = record.get(name)
            display_value = format_value_for_display(value)
            field_layout = QHBoxLayout()
            name_label = QLabel(f'{name}:')
            name_label.setMinimumWidth(150)
            name_label.setMaximumWidth(150)
            name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            name_label.setFont(QFont('Monospace', 10, QFont.Bold))
            value_label = QLabel(display_value)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            value_label.setWordWrap(True)
            if value is None:
                value_label.setStyleSheet('color: gray;')
            field_layout.addWidget(name_label)
            field_layout.addWidget(value_label)
            layout.addLayout(field_layout)
        layout.addStretch()
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
class ResultsView(QWidget):
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._result: Optional[QueryResult] = None
        self._init_ui()
    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        export_action = QAction('Export', self)
        export_action.setToolTip('Export results to file')
        export_action.triggered.connect(self._export_results)
        toolbar.addAction(export_action)
        copy_action = QAction('Copy Selected', self)
        copy_action.setToolTip('Copy selected cells to clipboard')
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self._copy_selected)
        toolbar.addAction(copy_action)
        toolbar.addSeparator()
        clear_filters_action = QAction('Clear Filters', self)
        clear_filters_action.setToolTip('Clear all column filters')
        clear_filters_action.triggered.connect(self._clear_filters)
        toolbar.addAction(clear_filters_action)
        toolbar.addSeparator()
        self._status_label = QLabel('Ready')
        toolbar.addWidget(self._status_label)
        main_layout.addWidget(toolbar)
        self._model = QueryResultsTableModel(self)
        self._proxy_model = ResultsFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._table_view = QTableView()
        self._table_view.setModel(self._proxy_model)
        self._table_view.setSortingEnabled(True)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.customContextMenuRequested.connect(self._show_context_menu)
        self._table_view.doubleClicked.connect(self._on_cell_double_clicked)
        self._header = ResultsFilterHeader(Qt.Horizontal, self._table_view)
        self._header.filterChanged.connect(self._on_filter_changed)
        self._table_view.setHorizontalHeader(self._header)
        main_layout.addWidget(self._table_view)
    def set_query_result(self, result: QueryResult) -> None:
        self._result = result
        self._model.setQueryResult(result)
        self._header.setFilterBoxes(len(result.columns))
        self._table_view.resizeColumnsToContents()
        self._status_label.setText(f'{result.row_count} rows returned in {result.execution_time_ms} ms')
        if result.truncated:
            self._status_label.setText(f'{self._status_label.text()} (Results truncated)')
    def get_query_result(self) -> Optional[QueryResult]:
        return self._result
    def get_filtered_data(self) -> List[Dict[str, Any]]:
        if not self._result:
            return []
        filtered_data = []
        for row in range(self._proxy_model.rowCount()):
            source_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()
            record = self._model.getRecord(source_row)
            if record:
                filtered_data.append(record)
        return filtered_data
    def _on_filter_changed(self, column: int, text: str) -> None:
        self._proxy_model.setFilterText(column, text)
        visible_rows = self._proxy_model.rowCount()
        total_rows = self._result.row_count if self._result else 0
        if visible_rows < total_rows:
            self._status_label.setText(f'Showing {visible_rows} of {total_rows} rows')
        else:
            self._status_label.setText(f'{total_rows} rows returned in {self._result.execution_time_ms} ms' if self._result else 'No results')
    def _clear_filters(self) -> None:
        for i in range(len(self._result.columns) if self._result else 0):
            widget = self._header._filter_widgets.get(i)
            if widget:
                widget.clear()
    def _export_results(self) -> None:
        if not self._result or not self._result.records:
            QMessageBox.warning(self, 'No Results', 'There are no results to export.')
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(self, 'Export Results', '', 'CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx)')
        if not file_path:
            return
        try:
            if file_path.endswith('.csv'):
                self._export_as_csv(file_path)
            elif file_path.endswith('.json'):
                self._export_as_json(file_path)
            elif file_path.endswith('.xlsx'):
                self._export_as_excel(file_path)
            else:
                if not file_path.endswith('.csv'):
                    file_path += '.csv'
                self._export_as_csv(file_path)
            self._status_label.setText(f'Results exported to {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Export Error', f'Failed to export results: {str(e)}')
    def _export_as_csv(self, file_path: str) -> None:
        with open(file_path, 'w', newline='') as f:
            headers = [col.name for col in self._result.columns]
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in range(self._proxy_model.rowCount()):
                source_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()
                record = self._model.getRecord(source_row)
                if record:
                    row_data = {k: '' if v is None else v for k, v in record.items()}
                    writer.writerow(row_data)
    def _export_as_json(self, file_path: str) -> None:
        records = []
        for row in range(self._proxy_model.rowCount()):
            source_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()
            record = self._model.getRecord(source_row)
            if record:
                records.append(record)
        export_data = {'query': self._result.query, 'executed_at': self._result.executed_at.isoformat(), 'execution_time_ms': self._result.execution_time_ms, 'row_count': len(records), 'records': records}
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    def _export_as_excel(self, file_path: str) -> None:
        try:
            import openpyxl
            from openpyxl import Workbook
        except ImportError:
            QMessageBox.critical(self, 'Missing Dependency', "Excel export requires the openpyxl package. Please install it with 'pip install openpyxl'.")
            return
        wb = Workbook()
        ws = wb.active
        ws.title = 'Query Results'
        headers = [col.name for col in self._result.columns]
        ws.append(headers)
        for row in range(self._proxy_model.rowCount()):
            source_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()
            record = self._model.getRecord(source_row)
            if record:
                ws.append([record.get(col) for col in headers])
        wb.save(file_path)
    def _copy_selected(self) -> None:
        selection = self._table_view.selectionModel()
        if not selection.hasSelection():
            return
        indexes = selection.selectedIndexes()
        if not indexes:
            return
        rows = {}
        for idx in indexes:
            row = idx.row()
            if row not in rows:
                rows[row] = []
            rows[row].append(idx)
        for row in rows.values():
            row.sort(key=lambda x: x.column())
        row_keys = sorted(rows.keys())
        text_buffer = io.StringIO()
        for row_idx in row_keys:
            row_data = []
            for idx in rows[row_idx]:
                value = self._proxy_model.data(idx, Qt.DisplayRole)
                cell_text = str(value) if value is not None else ''
                if '\t' in cell_text or '\n' in cell_text:
                    cell_text = f'"{cell_text}"'
                row_data.append(cell_text)
            text_buffer.write('\t'.join(row_data))
            text_buffer.write('\n')
        QApplication.clipboard().setText(text_buffer.getvalue())
        self._status_label.setText(f'Copied {len(indexes)} cells to clipboard')
    def _show_context_menu(self, pos: QPoint) -> None:
        index = self._table_view.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        copy_action = menu.addAction('Copy Cell')
        copy_action.triggered.connect(lambda: self._copy_cell(index))
        copy_row_action = menu.addAction('Copy Row')
        copy_row_action.triggered.connect(lambda: self._copy_row(index.row()))
        menu.addSeparator()
        preview_action = menu.addAction('Preview Record')
        preview_action.triggered.connect(lambda: self._preview_record(index.row()))
        menu.addSeparator()
        exclude_action = menu.addAction('Filter: Exclude This Value')
        exclude_action.triggered.connect(lambda: self._filter_exclude_value(index))
        include_action = menu.addAction('Filter: Only This Value')
        include_action.triggered.connect(lambda: self._filter_include_value(index))
        clear_filter_action = menu.addAction('Clear Filter for This Column')
        clear_filter_action.triggered.connect(lambda: self._clear_column_filter(index.column()))
        menu.exec_(self._table_view.viewport().mapToGlobal(pos))
    def _copy_cell(self, index: QModelIndex) -> None:
        value = self._proxy_model.data(index, Qt.DisplayRole)
        if value is not None:
            QApplication.clipboard().setText(str(value))
            self._status_label.setText('Cell copied to clipboard')
    def _copy_row(self, row: int) -> None:
        if row < 0 or row >= self._proxy_model.rowCount():
            return
        text_buffer = io.StringIO()
        for col in range(self._proxy_model.columnCount()):
            index = self._proxy_model.index(row, col)
            value = self._proxy_model.data(index, Qt.DisplayRole)
            cell_text = str(value) if value is not None else ''
            if '\t' in cell_text or '\n' in cell_text:
                cell_text = f'"{cell_text}"'
            text_buffer.write(cell_text)
            if col < self._proxy_model.columnCount() - 1:
                text_buffer.write('\t')
        QApplication.clipboard().setText(text_buffer.getvalue())
        self._status_label.setText('Row copied to clipboard')
    def _preview_record(self, row: int) -> None:
        if row < 0 or row >= self._proxy_model.rowCount():
            return
        source_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()
        record = self._model.getRecord(source_row)
        if record and self._result:
            dialog = DataPreviewDialog(record, self._result.columns, self)
            dialog.exec_()
    def _filter_exclude_value(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        value = self._proxy_model.data(index, Qt.DisplayRole)
        if value is None:
            value = 'NULL'
        else:
            value = str(value)
        column = index.column()
        widget = self._header._filter_widgets.get(column)
        if widget:
            current_text = widget.text()
            if current_text and (not current_text.startswith('!')):
                widget.setText(f'!{value}')
            else:
                widget.setText(f'!{value}')
    def _filter_include_value(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        value = self._proxy_model.data(index, Qt.DisplayRole)
        if value is None:
            value = 'NULL'
        else:
            value = str(value)
        column = index.column()
        widget = self._header._filter_widgets.get(column)
        if widget:
            widget.setText(value)
    def _clear_column_filter(self, column: int) -> None:
        widget = self._header._filter_widgets.get(column)
        if widget:
            widget.clear()
    def _on_cell_double_clicked(self, index: QModelIndex) -> None:
        self._preview_record(index.row())