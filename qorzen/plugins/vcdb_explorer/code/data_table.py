from __future__ import annotations

import csv
import logging
import os
import tempfile
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import (
    QAbstractTableModel, QModelIndex, QRegularExpression, QSize, QSortFilterProxyModel,
    Qt, Signal, Slot, QThread, QTimer
)
from PySide6.QtGui import QAction, QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox,
    QProgressBar, QProgressDialog, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QSplitter, QTableView, QTabWidget, QToolBar, QToolButton,
    QVBoxLayout, QWidget, QGridLayout
)

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event, EventType

from .database_handler import DatabaseHandler
from .events import VCdbEventType


class ColumnSelectionDialog(QDialog):
    """Dialog for selecting and ordering table columns."""

    def __init__(
            self,
            available_columns: List[Dict[str, str]],
            selected_columns: List[str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the dialog.

        Args:
            available_columns: List of available columns with id and name
            selected_columns: List of currently selected column IDs
            parent: The parent widget
        """
        super().__init__(parent)

        self.setWindowTitle('Select Columns')
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)

        self._available_columns = available_columns
        self._selected_columns = selected_columns
        self._column_map = {col['id']: col['name'] for col in available_columns}

        layout = QVBoxLayout()
        self.setLayout(layout)

        instructions = QLabel('Select columns to display and drag to reorder:')
        layout.addWidget(instructions)

        self._list_widget = QListWidget()
        self._list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        layout.addWidget(self._list_widget)

        for col_id in self._column_map:
            item = QListWidgetItem(self._column_map[col_id])
            item.setData(Qt.ItemDataRole.UserRole, col_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if col_id in selected_columns else Qt.CheckState.Unchecked)
            self._list_widget.addItem(item)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_columns(self) -> List[str]:
        """Get the selected columns in their display order.

        Returns:
            A list of selected column IDs
        """
        result = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                col_id = item.data(Qt.ItemDataRole.UserRole)
                result.append(col_id)
        return result


class YearRangeTableFilter(QWidget):
    """A year range filter widget for table filtering."""

    filterChanged = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the year range filter.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        layout.addWidget(QLabel('Year range:'))

        self._min_year = QSpinBox()
        self._min_year.setRange(1900, 2100)
        self._min_year.setValue(1900)
        self._min_year.setPrefix('From: ')
        self._min_year.valueChanged.connect(self._on_value_changed)
        self._min_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._min_year.wheelEvent = lambda event: event.ignore()
        layout.addWidget(self._min_year)

        self._max_year = QSpinBox()
        self._max_year.setRange(1900, 2100)
        self._max_year.setValue(2100)
        self._max_year.setPrefix('To: ')
        self._max_year.valueChanged.connect(self._on_value_changed)
        self._max_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._max_year.wheelEvent = lambda event: event.ignore()
        layout.addWidget(self._max_year)

        self._clear_btn = QToolButton()
        self._clear_btn.setText('×')
        self._clear_btn.setToolTip('Clear year range filter')
        self._clear_btn.clicked.connect(self._clear_filter)
        layout.addWidget(self._clear_btn)

    def get_filter(self) -> Dict[str, Any]:
        """Get the current filter value.

        Returns:
            A dictionary with the filter or an empty dictionary if no filter
        """
        min_year = self._min_year.value()
        max_year = self._max_year.value()

        if min_year == self._min_year.minimum() and max_year == self._max_year.maximum():
            return {}

        return {'year': {'min': min_year, 'max': max_year}}

    @Slot(int)
    def _on_value_changed(self, value: int) -> None:
        """Handle value changed event.

        Args:
            value: The new value
        """
        self.filterChanged.emit(self.get_filter())

    @Slot()
    def _clear_filter(self) -> None:
        """Clear the filter."""
        self._min_year.blockSignals(True)
        self._max_year.blockSignals(True)

        self._min_year.setValue(self._min_year.minimum())
        self._max_year.setValue(self._max_year.maximum())

        self._min_year.blockSignals(False)
        self._max_year.blockSignals(False)

        self.filterChanged.emit({})


class QueryResultModel(QAbstractTableModel):
    """Model for displaying query results in a table view."""

    def __init__(
            self,
            columns: List[str],
            column_map: Dict[str, str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the model.

        Args:
            columns: List of column IDs
            column_map: Mapping of column IDs to display names
            parent: The parent widget
        """
        super().__init__(parent)

        self._columns = columns
        self._column_map = column_map
        self._data: List[Dict[str, Any]] = []
        self._row_count = 0
        self._total_count = 0

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get the number of rows in the model.

        Args:
            parent: The parent index

        Returns:
            The number of rows
        """
        if parent.isValid():
            return 0

        return self._row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get the number of columns in the model.

        Args:
            parent: The parent index

        Returns:
            The number of columns
        """
        if parent.isValid():
            return 0

        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Get the data for a cell.

        Args:
            index: The index of the cell
            role: The data role

        Returns:
            The cell data
        """
        if not index.isValid() or not 0 <= index.row() < self._row_count:
            return None

        row = index.row()
        col_id = self._columns[index.column()]

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return str(self._data[row].get(col_id, ''))

        return None

    def headerData(
            self,
            section: int,
            orientation: Qt.Orientation,
            role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """Get the header data.

        Args:
            section: The section index
            orientation: The orientation (horizontal or vertical)
            role: The data role

        Returns:
            The header data
        """
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self._columns):
            col_id = self._columns[section]
            return self._column_map.get(col_id, col_id)

        return str(section + 1)

    def set_columns(self, columns: List[str]) -> None:
        """Set the columns for the model.

        Args:
            columns: List of column IDs
        """
        self.beginResetModel()
        self._columns = columns
        self.endResetModel()

    def set_data(self, data: List[Dict[str, Any]], total_count: int) -> None:
        """Set the data for the model.

        Args:
            data: List of row data dictionaries
            total_count: The total count of rows in the dataset
        """
        self.beginResetModel()
        self._data = data
        self._row_count = len(data)
        self._total_count = total_count
        self.endResetModel()

    def get_total_count(self) -> int:
        """Get the total count of rows in the dataset.

        Returns:
            The total count
        """
        return self._total_count

    def get_row_data(self, row: int) -> Dict[str, Any]:
        """Get the data for a specific row.

        Args:
            row: The row index

        Returns:
            A dictionary with the row data
        """
        if 0 <= row < self._row_count:
            return self._data[row].copy()

        return {}

    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all data from the model.

        Returns:
            A list of row data dictionaries
        """
        return self._data.copy()


class TableFilterWidget(QWidget):
    """Widget for configuring table filters."""

    filterChanged = Signal(dict)

    def __init__(
            self,
            columns: List[str],
            column_map: Dict[str, str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the table filter widget.

        Args:
            columns: List of column IDs
            column_map: Mapping of column IDs to display names
            parent: The parent widget
        """
        super().__init__(parent)

        self._columns = columns
        self._column_map = column_map
        self._filter_map: Dict[str, Any] = {}

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        header_layout = QHBoxLayout()

        title = QLabel('Table Filters')
        title.setStyleSheet('font-weight: bold; font-size: 12px;')
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._year_range_btn = QPushButton('Add Year Range Filter')
        self._year_range_btn.clicked.connect(self._add_year_range_filter)
        header_layout.addWidget(self._year_range_btn)

        self._add_filter_btn = QPushButton('Add Column Filter')
        self._add_filter_btn.clicked.connect(self._add_filter)
        header_layout.addWidget(self._add_filter_btn)

        self._clear_all_btn = QPushButton('Clear All')
        self._clear_all_btn.clicked.connect(self._clear_all_filters)
        self._clear_all_btn.setEnabled(False)
        header_layout.addWidget(self._clear_all_btn)

        self._layout.addLayout(header_layout)

        self._filters_layout = QVBoxLayout()
        self._layout.addLayout(self._filters_layout)

        self._filter_widgets: List[QWidget] = []

    def set_columns(self, columns: List[str]) -> None:
        """Set the available columns.

        Args:
            columns: List of column IDs
        """
        self._columns = columns

    def get_filters(self) -> Dict[str, Any]:
        """Get the current filters.

        Returns:
            A dictionary of filters
        """
        return self._filter_map.copy()

    def _add_year_range_filter(self) -> None:
        """Add a year range filter."""
        # Check if we already have a year range filter
        for widget in self._filter_widgets:
            if isinstance(widget, YearRangeTableFilter):
                return

        year_range_filter = YearRangeTableFilter(self)
        year_range_filter.filterChanged.connect(self._on_year_range_filter_changed)
        self._filters_layout.addWidget(year_range_filter)
        self._filter_widgets.append(year_range_filter)
        self._clear_all_btn.setEnabled(True)

    def _add_filter(self) -> None:
        """Add a column filter."""
        row_layout = QHBoxLayout()

        column_combo = QComboBox()
        for col_id in self._columns:
            if col_id not in self._filter_map or not isinstance(self._filter_map[col_id], str):
                column_combo.addItem(self._column_map.get(col_id, col_id), col_id)

        if column_combo.count() == 0:
            return

        row_layout.addWidget(column_combo)

        filter_input = QLineEdit()
        filter_input.setPlaceholderText('Filter value...')
        row_layout.addWidget(filter_input)

        remove_btn = QToolButton()
        remove_btn.setText('×')
        remove_btn.setToolTip('Remove filter')
        row_layout.addWidget(remove_btn)

        widget_container = QWidget()
        widget_container.setLayout(row_layout)
        self._filters_layout.addWidget(widget_container)
        self._filter_widgets.append(widget_container)

        col_id = column_combo.currentData()

        def update_filter() -> None:
            """Update the filter when values change."""
            current_col = column_combo.currentData()
            value = filter_input.text()

            if col_id in self._filter_map and current_col != col_id:
                del self._filter_map[col_id]

            if value:
                self._filter_map[current_col] = value
            elif current_col in self._filter_map:
                del self._filter_map[current_col]

            self._clear_all_btn.setEnabled(bool(self._filter_map))
            self.filterChanged.emit(self.get_filters())

        def remove_filter() -> None:
            """Remove the filter."""
            current_col = column_combo.currentData()
            if current_col in self._filter_map:
                del self._filter_map[current_col]

            self._filters_layout.removeWidget(widget_container)
            self._filter_widgets.remove(widget_container)
            widget_container.deleteLater()

            self._clear_all_btn.setEnabled(bool(self._filter_map))
            self.filterChanged.emit(self.get_filters())

        column_combo.currentIndexChanged.connect(update_filter)
        filter_input.textChanged.connect(update_filter)
        remove_btn.clicked.connect(remove_filter)

    @Slot(dict)
    def _on_year_range_filter_changed(self, year_filter: Dict[str, Any]) -> None:
        """Handle year range filter changed.

        Args:
            year_filter: The year range filter
        """
        if year_filter:
            self._filter_map.update(year_filter)
        elif 'year' in self._filter_map:
            del self._filter_map['year']

        self._clear_all_btn.setEnabled(bool(self._filter_map))
        self.filterChanged.emit(self.get_filters())

    def _clear_all_filters(self) -> None:
        """Clear all filters."""
        self._filter_map.clear()

        for widget in self._filter_widgets:
            widget.deleteLater()

        self._filter_widgets.clear()
        self._clear_all_btn.setEnabled(False)

        self.filterChanged.emit(self.get_filters())


class DataTableWidget(QWidget):
    """Widget for displaying query results in a table."""

    queryStarted = Signal()
    queryFinished = Signal()

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus: EventBusManager,
            logger: logging.Logger,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the data table widget.

        Args:
            database_handler: The database handler
            event_bus: The event bus
            logger: The logger
            parent: The parent widget
        """
        super().__init__(parent)

        self._database_handler = database_handler
        self._event_bus = event_bus
        self._logger = logger

        self._available_columns = database_handler.get_available_columns()
        self._column_map = {col['id']: col['name'] for col in self._available_columns}
        self._selected_columns = ['vehicle_id', 'year', 'make', 'model', 'submodel']

        self._current_page = 1
        self._page_size = 100
        self._total_count = 0
        self._sort_column: Optional[str] = None
        self._sort_descending = False
        self._table_filters: Dict[str, Any] = {}
        self._current_filter_panels: List[Dict[str, List[int]]] = []
        self._query_running = False
        self._callback_id = f'datatable_{uuid.uuid4()}'

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_toolbar()

        self._table_view = QTableView()
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.verticalHeader().setVisible(True)

        self._model = QueryResultModel(self._selected_columns, self._column_map, self)
        self._table_view.setModel(self._model)
        self._table_view.horizontalHeader().sortIndicatorChanged.connect(self._on_sort_indicator_changed)

        self._layout.addWidget(self._table_view)

        bottom_layout = QHBoxLayout()

        self._filter_widget = TableFilterWidget(self._selected_columns, self._column_map, self)
        self._filter_widget.filterChanged.connect(self._on_table_filter_changed)

        self._filter_group = QGroupBox('Table Filters')
        self._filter_group.setCheckable(True)
        self._filter_group.setChecked(False)
        self._filter_group.toggled.connect(self._on_filter_group_toggled)

        filter_group_layout = QVBoxLayout()
        filter_group_layout.addWidget(self._filter_widget)
        self._filter_group.setLayout(filter_group_layout)

        bottom_layout.addWidget(self._filter_group, 3)

        pagination_widget = QWidget()
        pagination_layout = QGridLayout()
        pagination_layout.setContentsMargins(10, 5, 10, 5)

        pagination_layout.addWidget(QLabel('Page Size:'), 0, 0)

        self._page_size_combo = QComboBox()
        for size in [10, 25, 50, 100, 250, 500, 1000]:
            self._page_size_combo.addItem(str(size), size)
        self._page_size_combo.setCurrentText(str(self._page_size))
        self._page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        pagination_layout.addWidget(self._page_size_combo, 0, 1)

        pagination_layout.addWidget(QLabel('Page:'), 1, 0)

        nav_layout = QHBoxLayout()

        self._first_page_btn = QToolButton()
        self._first_page_btn.setText('«')
        self._first_page_btn.setToolTip('First Page')
        self._first_page_btn.clicked.connect(self._goto_first_page)
        nav_layout.addWidget(self._first_page_btn)

        self._prev_page_btn = QToolButton()
        self._prev_page_btn.setText('‹')
        self._prev_page_btn.setToolTip('Previous Page')
        self._prev_page_btn.clicked.connect(self._goto_prev_page)
        nav_layout.addWidget(self._prev_page_btn)

        self._page_input = QSpinBox()
        self._page_input.setMinimum(1)
        self._page_input.setMaximum(1)
        self._page_input.setValue(1)
        self._page_input.valueChanged.connect(self._on_page_input_changed)
        nav_layout.addWidget(self._page_input)

        self._page_label = QLabel('of 1')
        nav_layout.addWidget(self._page_label)

        self._next_page_btn = QToolButton()
        self._next_page_btn.setText('›')
        self._next_page_btn.setToolTip('Next Page')
        self._next_page_btn.clicked.connect(self._goto_next_page)
        nav_layout.addWidget(self._next_page_btn)

        self._last_page_btn = QToolButton()
        self._last_page_btn.setText('»')
        self._last_page_btn.setToolTip('Last Page')
        self._last_page_btn.clicked.connect(self._goto_last_page)
        nav_layout.addWidget(self._last_page_btn)

        pagination_layout.addLayout(nav_layout, 1, 1)

        self._count_label = QLabel('0 rows')
        pagination_layout.addWidget(self._count_label, 2, 0, 1, 2)

        pagination_widget.setLayout(pagination_layout)

        bottom_layout.addWidget(pagination_widget, 1)

        self._layout.addLayout(bottom_layout)

        self._update_pagination_ui()

        # Subscribe to query results event
        self._event_bus.subscribe(
            event_type=VCdbEventType.query_results(),
            callback=self._on_query_results,
            subscriber_id=self._callback_id
        )

    def __del__(self) -> None:
        """Clean up resources when the widget is deleted."""
        try:
            self._event_bus.unsubscribe(subscriber_id=self._callback_id)
        except Exception:
            pass

    def _create_toolbar(self) -> None:
        """Create the toolbar."""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))

        self._run_query_action = QAction('Run Query', self)
        self._run_query_action.setToolTip('Execute the query with current filters')
        self._run_query_action.triggered.connect(self._run_query)
        toolbar.addAction(self._run_query_action)

        toolbar.addSeparator()

        self._select_columns_action = QAction('Select Columns', self)
        self._select_columns_action.setToolTip('Select and order table columns')
        self._select_columns_action.triggered.connect(self._show_column_selection)
        toolbar.addAction(self._select_columns_action)

        toolbar.addSeparator()

        self._export_csv_action = QAction('Export CSV', self)
        self._export_csv_action.setToolTip('Export results to CSV file')
        self._export_csv_action.triggered.connect(lambda: self._export_data(export_type='csv'))
        toolbar.addAction(self._export_csv_action)

        if EXCEL_AVAILABLE:
            self._export_excel_action = QAction('Export Excel', self)
            self._export_excel_action.setToolTip('Export results to Excel file')
            self._export_excel_action.triggered.connect(lambda: self._export_data(export_type='excel'))
            toolbar.addAction(self._export_excel_action)

        self._layout.addWidget(toolbar)

    def get_callback_id(self) -> str:
        return self._callback_id

    def get_selected_columns(self) -> List[str]:
        """Get the selected columns.

        Returns:
            A list of column IDs
        """
        return self._selected_columns

    def get_page_size(self) -> int:
        """Get the current page size.

        Returns:
            The page size
        """
        return self._page_size

    def execute_query(self, filter_panels: List[Dict[str, List[int]]]) -> None:
        """Execute a query with the given filter panels.

        Args:
            filter_panels: The filter panels
        """
        if self._query_running:
            self._logger.warning('Query already running, ignoring request')
            return

        self._query_running = True
        self.queryStarted.emit()

        try:
            self._logger.debug('Executing query')
            self._current_filter_panels = filter_panels

            # Publish query execute event
            self._event_bus.publish(
                event_type=VCdbEventType.query_execute(),
                source='data_table_widget',
                payload={
                    'filter_panels': filter_panels,
                    'columns': self._selected_columns,
                    'page': self._current_page,
                    'page_size': self._page_size,
                    'sort_by': self._sort_column,
                    'sort_desc': self._sort_descending,
                    'table_filters': self._table_filters,
                    'callback_id': self._callback_id
                }
            )

        except Exception as e:
            self._logger.error(f'Query execution failed: {str(e)}')
            self._query_running = False
            self.queryFinished.emit()
            QMessageBox.critical(self, 'Query Error', f'Error executing query: {str(e)}')

    def _run_query(self) -> None:
        """Run the current query."""
        if not self._query_running:
            self.execute_query(self._current_filter_panels)
        else:
            self._logger.warning('Query already running')

    @Slot(Any)
    def _on_query_results(self, event: Any) -> None:
        payload = event.payload
        callback_id = payload.get('callback_id')
        self._logger.debug(f"_on_query_results called: callback_id={callback_id}, expected={self._callback_id}")

        if callback_id != self._callback_id:
            return

        results = payload.get('results', [])
        total_count = payload.get('total_count', 0)
        error = payload.get('error')

        # Since we're already on the Qt thread, just call update_ui() directly:
        if error:
            self._logger.error(f'Query error: {error}')
            QMessageBox.critical(self, 'Query Error', f'Error executing query: {error}')
        else:
            self._logger.debug(f'Query results received: {len(results)} rows of {total_count} total')
            self._model.set_data(results, total_count)
            self._table_view.reset()
            self._table_view.repaint()
            self._total_count = total_count
            self._update_pagination_ui()

        self._query_running = False
        self.queryFinished.emit()

    def _show_column_selection(self) -> None:
        """Show the column selection dialog."""
        dialog = ColumnSelectionDialog(self._available_columns, self._selected_columns, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_columns = dialog.get_selected_columns()

            if new_columns != self._selected_columns:
                self._selected_columns = new_columns
                self._model.set_columns(self._selected_columns)
                self._filter_widget.set_columns(self._selected_columns)

                if self._model.rowCount() > 0:
                    self._run_query()

    def _export_data(self, export_type: str) -> None:
        """Export the data to a file.

        Args:
            export_type: The type of export ('csv' or 'excel')
        """
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        if export_type == 'csv':
            file_dialog.setNameFilter('CSV Files (*.csv)')
            file_dialog.setDefaultSuffix('csv')
        else:
            file_dialog.setNameFilter('Excel Files (*.xlsx)')
            file_dialog.setDefaultSuffix('xlsx')

        if not file_dialog.exec():
            return

        file_path = file_dialog.selectedFiles()[0]

        try:
            if self._total_count > 1000:
                # TODO: Implement paged export for large datasets
                pass

            data = self._model.get_all_data()

            if export_type == 'csv':
                with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                    writer = csv.DictWriter(
                        csv_file,
                        fieldnames=self._selected_columns,
                        extrasaction='ignore'
                    )
                    writer.writerow({col: self._column_map.get(col, col) for col in self._selected_columns})

                    for row in data:
                        writer.writerow(row)

            elif export_type == 'excel' and EXCEL_AVAILABLE:
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = 'VCdb Results'

                for col_idx, col_id in enumerate(self._selected_columns, 1):
                    ws.cell(row=1, column=col_idx, value=self._column_map.get(col_id, col_id))

                for row_idx, row_data in enumerate(data, 2):
                    for col_idx, col_id in enumerate(self._selected_columns, 1):
                        ws.cell(row=row_idx, column=col_idx, value=row_data.get(col_id, ''))

                wb.save(file_path)

            self._logger.info(f'Data exported to {file_path}')

        except Exception as e:
            self._logger.error(f'Error exporting data: {str(e)}')
            QMessageBox.critical(self, 'Export Error', f'Error exporting data: {str(e)}')

    @Slot()
    def _on_page_size_changed(self) -> None:
        """Handle page size changed."""
        new_size = self._page_size_combo.currentData()

        if new_size != self._page_size:
            self._page_size = new_size
            self._current_page = 1
            self._run_query()

    @Slot(int)
    def _on_page_input_changed(self, page: int) -> None:
        """Handle page input changed.

        Args:
            page: The new page number
        """
        if page != self._current_page:
            self._current_page = page
            self._refresh_current_page()

    def _refresh_current_page(self) -> None:
        """Refresh the current page."""
        if not self._query_running:
            self.execute_query(self._current_filter_panels)

    @Slot()
    def _goto_first_page(self) -> None:
        """Go to the first page."""
        if self._current_page > 1:
            self._current_page = 1
            self._refresh_current_page()

    @Slot()
    def _goto_prev_page(self) -> None:
        """Go to the previous page."""
        if self._current_page > 1:
            self._current_page -= 1
            self._refresh_current_page()

    @Slot()
    def _goto_next_page(self) -> None:
        """Go to the next page."""
        max_page = max(1, (self._total_count + self._page_size - 1) // self._page_size)

        if self._current_page < max_page:
            self._current_page += 1
            self._refresh_current_page()

    @Slot()
    def _goto_last_page(self) -> None:
        """Go to the last page."""
        max_page = max(1, (self._total_count + self._page_size - 1) // self._page_size)

        if self._current_page < max_page:
            self._current_page = max_page
            self._refresh_current_page()

    def _update_pagination_ui(self) -> None:
        """Update the pagination UI."""
        max_page = max(1, (self._total_count + self._page_size - 1) // self._page_size)

        self._page_input.blockSignals(True)
        self._page_input.setRange(1, max_page)
        self._page_input.setValue(self._current_page)
        self._page_input.blockSignals(False)

        self._page_label.setText(f'of {max_page}')

        self._first_page_btn.setEnabled(self._current_page > 1)
        self._prev_page_btn.setEnabled(self._current_page > 1)
        self._next_page_btn.setEnabled(self._current_page < max_page)
        self._last_page_btn.setEnabled(self._current_page < max_page)

        if self._total_count == 0:
            self._count_label.setText('No results')
        else:
            start_idx = (self._current_page - 1) * self._page_size + 1
            end_idx = min(self._current_page * self._page_size, self._total_count)
            self._count_label.setText(f'Showing {start_idx}-{end_idx} of {self._total_count} rows')

    @Slot(int, Qt.SortOrder)
    def _on_sort_indicator_changed(self, logical_index: int, order: Qt.SortOrder) -> None:
        """Handle sort indicator changed.

        Args:
            logical_index: The column index
            order: The sort order
        """
        if 0 <= logical_index < len(self._selected_columns):
            self._sort_column = self._selected_columns[logical_index]
            self._sort_descending = order == Qt.SortOrder.DescendingOrder
            self._run_query()

    @Slot(dict)
    def _on_table_filter_changed(self, filters: Dict[str, Any]) -> None:
        """Handle table filter changed.

        Args:
            filters: The new filters
        """
        self._table_filters = filters
        self._current_page = 1
        self._run_query()

    @Slot(bool)
    def _on_filter_group_toggled(self, checked: bool) -> None:
        """Handle filter group toggled.

        Args:
            checked: Whether the group is checked
        """
        if checked and (not self._table_filters):
            self._filter_widget._add_year_range_filter()