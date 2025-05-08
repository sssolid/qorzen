from __future__ import annotations

import csv
import logging
import os
import tempfile
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import (
    QAbstractTableModel, QModelIndex, QRegularExpression, QSize,
    QSortFilterProxyModel, Qt, Signal, Slot, QThread, QTimer, QPoint, QObject
)
from PySide6.QtGui import QAction, QClipboard, QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox,
    QProgressBar, QProgressDialog, QPushButton, QScrollArea,
    QSizePolicy, QSpinBox, QSplitter, QTableView, QTabWidget,
    QToolBar, QToolButton, QVBoxLayout, QWidget, QGridLayout, QApplication, QRadioButton
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
from .export import DataExporter, ExportError


# New signal class for thread-safe communication
class QuerySignals(QObject):
    # Signal when query starts
    started = Signal()
    # Signal when query completes with results
    completed = Signal(object)
    # Signal when query fails with error
    failed = Signal(str)
    # Signal when progress updates
    progress = Signal(int, int)


class ColumnSelectionDialog(QDialog):
    """Dialog for selecting and ordering table columns."""

    def __init__(
            self,
            available_columns: List[Dict[str, str]],
            selected_columns: List[str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize column selection dialog.

        Args:
            available_columns: List of available columns with id and name
            selected_columns: List of currently selected column IDs
            parent: Parent widget
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

        # Add items to list
        for col_id in self._column_map:
            item = QListWidgetItem(self._column_map[col_id])
            item.setData(Qt.ItemDataRole.UserRole, col_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if col_id in selected_columns
                else Qt.CheckState.Unchecked
            )
            self._list_widget.addItem(item)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_columns(self) -> List[str]:
        """Get selected column IDs in displayed order.

        Returns:
            List of selected column IDs
        """
        result = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                col_id = item.data(Qt.ItemDataRole.UserRole)
                result.append(col_id)
        return result


class YearRangeTableFilter(QWidget):
    """Widget for filtering by year range."""

    filterChanged = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize year range filter widget.

        Args:
            parent: Parent widget
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
        # Disable mouse wheel to prevent accidental changes
        self._min_year.wheelEvent = lambda event: event.ignore()
        layout.addWidget(self._min_year)

        self._max_year = QSpinBox()
        self._max_year.setRange(1900, 2100)
        self._max_year.setValue(2100)
        self._max_year.setPrefix('To: ')
        self._max_year.valueChanged.connect(self._on_value_changed)
        self._max_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Disable mouse wheel to prevent accidental changes
        self._max_year.wheelEvent = lambda event: event.ignore()
        layout.addWidget(self._max_year)

        self._clear_btn = QToolButton()
        self._clear_btn.setText('×')
        self._clear_btn.setToolTip('Clear year range filter')
        self._clear_btn.clicked.connect(self._clear_filter)
        layout.addWidget(self._clear_btn)

    def get_filter(self) -> Dict[str, Any]:
        """Get current filter values.

        Returns:
            Filter dictionary or empty dict if no filter active
        """
        min_year = self._min_year.value()
        max_year = self._max_year.value()

        if min_year == self._min_year.minimum() and max_year == self._max_year.maximum():
            return {}

        return {'year': {'min': min_year, 'max': max_year}}

    @Slot(int)
    def _on_value_changed(self, value: int) -> None:
        """Handle value change.

        Args:
            value: New value
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
    """Table model for query results."""

    def __init__(
            self,
            columns: List[str],
            column_map: Dict[str, str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize query result model.

        Args:
            columns: List of column IDs
            column_map: Mapping from column IDs to display names
            parent: Parent widget
        """
        super().__init__(parent)
        self._columns = columns
        self._column_map = column_map
        self._data: List[Dict[str, Any]] = []
        self._row_count = 0
        self._total_count = 0

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of rows.

        Args:
            parent: Parent index

        Returns:
            Number of rows
        """
        if parent.isValid():
            return 0
        return self._row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of columns.

        Args:
            parent: Parent index

        Returns:
            Number of columns
        """
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Get data for a cell.

        Args:
            index: Cell index
            role: Data role

        Returns:
            Cell data for the requested role
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
        """Get header data.

        Args:
            section: Section index
            orientation: Header orientation
            role: Data role

        Returns:
            Header data for the requested role
        """
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self._columns):
            col_id = self._columns[section]
            return self._column_map.get(col_id, col_id)

        return str(section + 1)

    def set_columns(self, columns: List[str]) -> None:
        """Set columns for the model.

        Args:
            columns: List of column IDs
        """
        self.beginResetModel()
        self._columns = columns
        self.endResetModel()

    def set_data(self, data: List[Dict[str, Any]], total_count: int) -> None:
        """Set data for the model.

        Args:
            data: List of row data dictionaries
            total_count: Total number of matching rows (may be more than visible)
        """
        self.beginResetModel()
        self._data = data
        self._row_count = len(data)
        self._total_count = total_count
        self.endResetModel()

    def get_total_count(self) -> int:
        """Get total row count (may include non-visible rows).

        Returns:
            Total row count
        """
        return self._total_count

    def get_row_data(self, row: int) -> Dict[str, Any]:
        """Get data for a specific row.

        Args:
            row: Row index

        Returns:
            Row data dictionary
        """
        if 0 <= row < self._row_count:
            return self._data[row].copy()
        return {}

    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all visible data.

        Returns:
            List of all visible row data dictionaries
        """
        return self._data.copy()


class TableFilterWidget(QWidget):
    """Widget for filtering table data."""

    filterChanged = Signal(dict)

    def __init__(
            self,
            columns: List[str],
            column_map: Dict[str, str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize table filter widget.

        Args:
            columns: List of column IDs
            column_map: Mapping from column IDs to display names
            parent: Parent widget
        """
        super().__init__(parent)

        self._columns = columns
        self._column_map = column_map
        self._filter_map: Dict[str, Any] = {}

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Header
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

        # Filters layout
        self._filters_layout = QVBoxLayout()
        self._layout.addLayout(self._filters_layout)

        self._filter_widgets: List[QWidget] = []

    def set_columns(self, columns: List[str]) -> None:
        """Set available columns.

        Args:
            columns: List of column IDs
        """
        self._columns = columns

    def get_filters(self) -> Dict[str, Any]:
        """Get current filters.

        Returns:
            Dictionary of current filters
        """
        return self._filter_map.copy()

    def _add_year_range_filter(self) -> None:
        """Add a year range filter."""
        # Check if one already exists
        for widget in self._filter_widgets:
            if isinstance(widget, YearRangeTableFilter):
                return

        year_range_filter = YearRangeTableFilter(self)
        year_range_filter.filterChanged.connect(self._on_year_range_filter_changed)
        self._filters_layout.addWidget(year_range_filter)
        self._filter_widgets.append(year_range_filter)
        self._clear_all_btn.setEnabled(True)

    def _add_filter(self) -> None:
        """Add a column text filter."""
        row_layout = QHBoxLayout()

        # Column selector
        column_combo = QComboBox()
        for col_id in self._columns:
            if col_id not in self._filter_map or not isinstance(self._filter_map[col_id], str):
                column_combo.addItem(self._column_map.get(col_id, col_id), col_id)

        if column_combo.count() == 0:
            return

        row_layout.addWidget(column_combo)

        # Filter input
        filter_input = QLineEdit()
        filter_input.setPlaceholderText('Filter value...')
        row_layout.addWidget(filter_input)

        # Remove button
        remove_btn = QToolButton()
        remove_btn.setText('×')
        remove_btn.setToolTip('Remove filter')
        row_layout.addWidget(remove_btn)

        # Create container widget
        widget_container = QWidget()
        widget_container.setLayout(row_layout)
        self._filters_layout.addWidget(widget_container)
        self._filter_widgets.append(widget_container)

        col_id = column_combo.currentData()

        def update_filter() -> None:
            """Update filter when inputs change."""
            current_col = column_combo.currentData()
            value = filter_input.text()

            # If column changed, remove old filter
            if col_id in self._filter_map and current_col != col_id:
                del self._filter_map[col_id]

            # Set new filter or remove if empty
            if value:
                self._filter_map[current_col] = value
            elif current_col in self._filter_map:
                del self._filter_map[current_col]

            self._clear_all_btn.setEnabled(bool(self._filter_map))
            self.filterChanged.emit(self.get_filters())

        def remove_filter() -> None:
            """Remove this filter."""
            current_col = column_combo.currentData()
            if current_col in self._filter_map:
                del self._filter_map[current_col]

            self._filters_layout.removeWidget(widget_container)
            self._filter_widgets.remove(widget_container)
            widget_container.deleteLater()

            self._clear_all_btn.setEnabled(bool(self._filter_map))
            self.filterChanged.emit(self.get_filters())

        # Connect signals
        column_combo.currentIndexChanged.connect(update_filter)
        filter_input.textChanged.connect(update_filter)
        remove_btn.clicked.connect(remove_filter)

    @Slot(dict)
    def _on_year_range_filter_changed(self, year_filter: Dict[str, Any]) -> None:
        """Handle year range filter change.

        Args:
            year_filter: New year filter dictionary
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


class ExportOptionsDialog(QDialog):
    """Dialog for export options."""

    def __init__(
            self,
            format_type: str,
            current_count: int,
            total_count: int,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize export options dialog.

        Args:
            format_type: Export format type ("csv" or "excel")
            current_count: Number of records in current page
            total_count: Total number of records matching query
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle(f'Export {format_type.upper()} Options')
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Export scope options
        scope_group = QGroupBox('Export Scope')
        scope_layout = QVBoxLayout()
        scope_group.setLayout(scope_layout)

        self._current_page_radio = QRadioButton(f'Current page only ({current_count} rows)')
        self._current_page_radio.setChecked(True)
        scope_layout.addWidget(self._current_page_radio)

        self._all_results_radio = QRadioButton(f'All matching results ({total_count} rows)')
        scope_layout.addWidget(self._all_results_radio)

        # Disable all results option if not applicable
        if current_count >= total_count:
            self._all_results_radio.setEnabled(False)
            self._all_results_radio.setText('All matching results (already showing all)')

        layout.addWidget(scope_group)

        # Warning for large exports
        if total_count > 5000:
            warning = QLabel(f'Warning: Exporting all {total_count} rows may take some time.')
            warning.setStyleSheet('color: #CC0000;')
            layout.addWidget(warning)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def export_all(self) -> bool:
        """Check if all results should be exported.

        Returns:
            True if all results should be exported, False for current page only
        """
        return self._all_results_radio.isChecked()


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
        """Initialize data table widget.

        Args:
            database_handler: Database handler for queries
            event_bus: Event bus for communication
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)

        # Create signals object for thread-safe communication
        self._signals = QuerySignals()

        # Connect signals to slots with appropriate connection types
        self._signals.started.connect(self._on_query_started, Qt.ConnectionType.QueuedConnection)
        self._signals.completed.connect(self._on_query_completed, Qt.ConnectionType.QueuedConnection)
        self._signals.failed.connect(self._on_query_failed, Qt.ConnectionType.QueuedConnection)
        self._signals.progress.connect(self._on_query_progress, Qt.ConnectionType.QueuedConnection)

        # Progress dialog reference - initialize to None
        self._progress_dialog = None

        # Thread reference - initialize to None
        self._query_thread = None

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
        self._exporter = DataExporter(logger)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_toolbar()

        # Table view
        self._table_view = QTableView()
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.verticalHeader().setVisible(True)
        self._table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Create model
        self._model = QueryResultModel(self._selected_columns, self._column_map, self)
        self._table_view.setModel(self._model)
        self._table_view.horizontalHeader().sortIndicatorChanged.connect(self._on_sort_indicator_changed)

        self._layout.addWidget(self._table_view)

        # Bottom layout with filters and pagination
        bottom_layout = QHBoxLayout()

        # Table filters
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

        # Pagination controls
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

        # Navigation buttons
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

        # Subscribe to query results events
        self._event_bus.subscribe(
            event_type=VCdbEventType.query_results(),
            callback=self._on_query_results,
            subscriber_id=self._callback_id
        )

    def __del__(self) -> None:
        """Clean up event subscriptions."""
        try:
            self._event_bus.unsubscribe(subscriber_id=self._callback_id)
        except Exception:
            pass

    def _create_toolbar(self) -> None:
        """Create the toolbar with actions."""
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
        """Get callback ID for event subscription.

        Returns:
            Callback ID
        """
        return self._callback_id

    def get_selected_columns(self) -> List[str]:
        """Get currently selected columns.

        Returns:
            List of selected column IDs
        """
        return self._selected_columns

    def get_page_size(self) -> int:
        """Get current page size.

        Returns:
            Page size
        """
        return self._page_size

    def execute_query(self, filter_panels: List[Dict[str, List[int]]]) -> None:
        """
        Execute a query with the given filter panels.
        All UI operations must happen on the main thread.

        Args:
            filter_panels: List of filter criteria from filter panels
        """
        if self._query_running:
            self._logger.warning('Query already running, ignoring request')
            return

        self._query_running = True
        self._current_filter_panels = filter_panels

        # Emit the started signal - this will trigger UI updates on the main thread
        self._signals.started.emit()

        # Create a thread to run the actual query
        self._query_thread = threading.Thread(
            target=self._run_query_in_thread,
            args=(filter_panels,),
            daemon=True
        )

        # Start the thread
        self._query_thread.start()

    def _run_query_in_thread(self, filter_panels: List[Dict[str, List[int]]]) -> None:
        """
        Run the query in a background thread.
        No UI operations should happen here.

        Args:
            filter_panels: List of filter criteria
        """
        try:
            # Log the operation
            self._logger.debug(f"Running query in thread with {len(filter_panels)} filter panels")

            # Call the database handler directly
            results, total_count = self._database_handler.execute_query(
                filter_panels=filter_panels,
                columns=self._selected_columns,
                page=self._current_page,
                page_size=self._page_size,
                sort_by=self._sort_column,
                sort_desc=self._sort_descending,
                table_filters=self._table_filters
            )

            # Successfully got results, emit completed signal
            self._signals.completed.emit({
                'results': results,
                'total_count': total_count
            })

        except Exception as e:
            # Query failed, emit failed signal
            self._logger.error(f"Query failed: {str(e)}")
            self._signals.failed.emit(str(e))

    @Slot()
    def _on_query_started(self) -> None:
        """
        Handle query started event on the main thread.
        Create and show the progress dialog.
        """
        # Create progress dialog on the main thread
        self._progress_dialog = QProgressDialog('Executing query...', 'Cancel', 0, 0, self)
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setAutoClose(True)
        self._progress_dialog.setMinimumDuration(500)
        self._progress_dialog.setCancelButton(None)  # No cancel button to simplify
        self._progress_dialog.setRange(0, 0)  # Indeterminate progress
        self._progress_dialog.show()

    @Slot(object)
    def _on_query_completed(self, data: Dict[str, Any]) -> None:
        """
        Handle query completed event on the main thread.
        Update the UI with the results.

        Args:
            data: Dictionary with query results
        """
        # Update the model with results
        results = data.get('results', [])
        total_count = data.get('total_count', 0)

        # Update the model on the main thread
        self._model.set_data(results, total_count)

        # Reset the table view
        self._table_view.reset()

        # Store the total count
        self._total_count = total_count

        # Update pagination UI
        self._update_pagination_ui()

        # Close the progress dialog if it exists
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

        # Reset query running state
        self._query_running = False

        # Log completion
        self._logger.debug(f"Query completed: {len(results)} results of {total_count} total")

    @Slot(str)
    def _on_query_failed(self, error_message: str) -> None:
        """
        Handle query failed event on the main thread.
        Show error message to user.

        Args:
            error_message: The error message to display
        """
        # Close the progress dialog if it exists
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

        # Reset query running state
        self._query_running = False

        # Show error message
        QMessageBox.critical(self, 'Query Error', f'Error executing query: {error_message}')

        # Log the error
        self._logger.error(f"Query failed: {error_message}")

    @Slot(int, int)
    def _on_query_progress(self, current: int, total: int) -> None:
        """
        Handle query progress event on the main thread.
        Update the progress dialog.

        Args:
            current: Current progress value
            total: Total expected progress
        """
        # Update progress dialog if it exists
        if self._progress_dialog:
            if self._progress_dialog.maximum() == 0 and total > 0:
                self._progress_dialog.setRange(0, total)
            self._progress_dialog.setValue(current)

    def _run_query(self) -> None:
        """Run the current query."""
        if not self._query_running:
            self.execute_query(self._current_filter_panels)
        else:
            self._logger.warning('Query already running')

    @Slot(Any)
    def _on_query_results(self, event: Any) -> None:
        """Handle query results event.

        Args:
            event: Query results event
        """
        payload = event.payload
        callback_id = payload.get('callback_id')

        self._logger.debug(f'_on_query_results called: callback_id={callback_id}, expected={self._callback_id}')

        if callback_id != self._callback_id:
            return

        results = payload.get('results', [])
        total_count = payload.get('total_count', 0)
        error = payload.get('error')

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
        """Show dialog to select and order columns."""
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
        """Export data to file.

        Args:
            export_type: Export format ("csv" or "excel")
        """
        # Show file dialog
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

        # Show export options dialog
        current_count = self._model.rowCount()
        total_count = self._model.get_total_count()
        options_dialog = ExportOptionsDialog(export_type, current_count, total_count, self)

        if not options_dialog.exec():
            return

        export_all = options_dialog.export_all() and total_count > current_count

        try:
            # Export current page only
            if not export_all:
                data = self._model.get_all_data()

                if export_type == 'csv':
                    self._exporter.export_csv(
                        data=data,
                        columns=self._selected_columns,
                        column_map=self._column_map,
                        file_path=file_path
                    )
                elif export_type == 'excel' and EXCEL_AVAILABLE:
                    self._exporter.export_excel(
                        data=data,
                        columns=self._selected_columns,
                        column_map=self._column_map,
                        file_path=file_path
                    )

                QMessageBox.information(
                    self,
                    'Export Complete',
                    f'Successfully exported {len(data)} rows to {export_type.upper()} file.'
                )
            # Export all matching results
            else:
                progress = QProgressDialog("Exporting data...", "Cancel", 0, total_count, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.setAutoClose(True)
                progress.setAutoReset(True)
                progress.show()

                # Define progress callback
                def update_progress(current: int, total: int) -> None:
                    progress.setValue(current)
                    QApplication.processEvents()

                # Run export operation
                rows_exported = self._exporter.export_all_data(
                    database_callback=lambda filter_panels, columns, page, page_size, sort_by, sort_desc, table_filters:
                    self._database_handler.execute_query(
                        filter_panels=filter_panels,
                        columns=columns,
                        page=page,
                        page_size=page_size,
                        sort_by=sort_by,
                        sort_desc=sort_desc,
                        table_filters=table_filters
                    ),
                    filter_panels=self._current_filter_panels,
                    columns=self._selected_columns,
                    column_map=self._column_map,
                    file_path=file_path,
                    format_type=export_type,
                    sort_by=self._sort_column,
                    sort_desc=self._sort_descending,
                    table_filters=self._table_filters,
                    progress_callback=update_progress
                )

                if not progress.wasCanceled():
                    QMessageBox.information(
                        self,
                        'Export Complete',
                        f'Successfully exported {rows_exported} rows to {export_type.upper()} file.'
                    )

                progress.close()

            self._logger.info(f'Data exported to {file_path}')
        except Exception as e:
            self._logger.error(f'Error exporting data: {str(e)}')
            QMessageBox.critical(self, 'Export Error', f'Error exporting data: {str(e)}')

    @Slot()
    def _on_page_size_changed(self) -> None:
        """Handle page size change."""
        new_size = self._page_size_combo.currentData()
        if new_size != self._page_size:
            self._page_size = new_size
            self._current_page = 1
            self._run_query()

    @Slot(int)
    def _on_page_input_changed(self, page: int) -> None:
        """Handle page input change.

        Args:
            page: New page number
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
        """Update pagination UI controls."""
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
        """Handle sort indicator change.

        Args:
            logical_index: Column index
            order: Sort order
        """
        if 0 <= logical_index < len(self._selected_columns):
            self._sort_column = self._selected_columns[logical_index]
            self._sort_descending = order == Qt.SortOrder.DescendingOrder
            self._run_query()

    @Slot(dict)
    def _on_table_filter_changed(self, filters: Dict[str, Any]) -> None:
        """Handle table filter change.

        Args:
            filters: New filters
        """
        self._table_filters = filters
        self._current_page = 1
        self._run_query()

    @Slot(bool)
    def _on_filter_group_toggled(self, checked: bool) -> None:
        """Handle filter group toggle.

        Args:
            checked: Whether the group is checked
        """
        if checked and (not self._table_filters):
            self._filter_widget._add_year_range_filter()

    @Slot(QPoint)
    def _show_context_menu(self, pos: 'QPoint') -> None:
        """Show context menu for table.

        Args:
            pos: Position for the menu
        """
        # Get selected rows
        selected_indexes = self._table_view.selectionModel().selectedRows()
        has_selection = len(selected_indexes) > 0

        # Create context menu
        context_menu = QMenu(self)

        # Copy selected rows action
        copy_selected_action = QAction('Copy Selected Row(s)', self)
        copy_selected_action.triggered.connect(self._copy_selected_rows)
        copy_selected_action.setEnabled(has_selection)
        context_menu.addAction(copy_selected_action)

        # Copy all visible rows action
        copy_all_action = QAction('Copy All Visible Rows', self)
        copy_all_action.triggered.connect(self._copy_all_rows)
        copy_all_action.setEnabled(self._model.rowCount() > 0)
        context_menu.addAction(copy_all_action)

        # Export actions
        context_menu.addSeparator()

        export_csv_action = QAction('Export to CSV...', self)
        export_csv_action.triggered.connect(lambda: self._export_data('csv'))
        context_menu.addAction(export_csv_action)

        if EXCEL_AVAILABLE:
            export_excel_action = QAction('Export to Excel...', self)
            export_excel_action.triggered.connect(lambda: self._export_data('excel'))
            context_menu.addAction(export_excel_action)

        # Show the menu
        context_menu.popup(self._table_view.viewport().mapToGlobal(pos))

    def _copy_selected_rows(self) -> None:
        """Copy selected rows to clipboard as tab-separated text."""
        selected_indexes = self._table_view.selectionModel().selectedRows()

        if not selected_indexes:
            return

        # Sort by row index to preserve order
        selected_indexes.sort(key=lambda idx: idx.row())

        rows_data = []

        # Add header row
        header_row = []
        for col_idx, col_id in enumerate(self._selected_columns):
            header_row.append(self._column_map.get(col_id, col_id))
        rows_data.append('\t'.join(header_row))

        # Add data rows
        for idx in selected_indexes:
            row_idx = idx.row()
            row_data = []
            for col_idx, col_id in enumerate(self._selected_columns):
                cell_value = str(self._model.data(
                    self._model.index(row_idx, col_idx),
                    Qt.ItemDataRole.DisplayRole
                ) or '')
                row_data.append(cell_value)
            rows_data.append('\t'.join(row_data))

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(rows_data))

        self._logger.debug(f'Copied {len(selected_indexes)} rows to clipboard')

    def _copy_all_rows(self) -> None:
        """Copy all visible rows to clipboard as tab-separated text."""
        row_count = self._model.rowCount()

        if row_count == 0:
            return

        rows_data = []

        # Add header row
        header_row = []
        for col_idx, col_id in enumerate(self._selected_columns):
            header_row.append(self._column_map.get(col_id, col_id))
        rows_data.append('\t'.join(header_row))

        # Add data rows
        for row_idx in range(row_count):
            row_data = []
            for col_idx, col_id in enumerate(self._selected_columns):
                cell_value = str(self._model.data(
                    self._model.index(row_idx, col_idx),
                    Qt.ItemDataRole.DisplayRole
                ) or '')
                row_data.append(cell_value)
            rows_data.append('\t'.join(row_data))

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(rows_data))

        self._logger.debug(f'Copied all {row_count} rows to clipboard')