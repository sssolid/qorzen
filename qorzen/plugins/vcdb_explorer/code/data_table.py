from __future__ import annotations

"""
VCdb data table module.

This module provides UI components for displaying and filtering query results,
including data models, filter widgets, and export functionality.
"""

import asyncio
import csv
import logging
import os
import tempfile
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import (
    QAbstractTableModel, QModelIndex, QRegularExpression, QSize,
    QSortFilterProxyModel, Qt, Signal, Slot, QTimer, QPoint
)
from PySide6.QtGui import (
    QAction, QClipboard, QIcon, QStandardItem, QStandardItemModel
)
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox,
    QProgressBar, QProgressDialog, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QSplitter, QTableView, QTabWidget, QToolBar, QToolButton,
    QVBoxLayout, QWidget, QGridLayout, QApplication, QRadioButton
)

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event

from .database_handler import DatabaseHandler
from .events import VCdbEventType
from .export import DataExporter, ExportError


class QuerySignals(QWidget):
    """Signal class for query operations."""

    started = Signal()
    completed = Signal(object)
    failed = Signal(str)
    progress = Signal(int, int)
    cancelled = Signal()


class ColumnSelectionDialog(QDialog):
    """Dialog for selecting and ordering table columns."""

    def __init__(
            self,
            available_columns: List[Dict[str, str]],
            selected_columns: List[str],
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the dialog.

        Args:
            available_columns: List of available columns with 'id' and 'name' keys
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

        # Instructions
        instructions = QLabel('Select columns to display and drag to reorder:')
        layout.addWidget(instructions)

        # List widget for columns
        self._list_widget = QListWidget()
        self._list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        layout.addWidget(self._list_widget)

        # Add all columns to the list
        for col_id in self._column_map:
            item = QListWidgetItem(self._column_map[col_id])
            item.setData(Qt.ItemDataRole.UserRole, col_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if col_id in selected_columns
                else Qt.CheckState.Unchecked
            )
            self._list_widget.addItem(item)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_columns(self) -> List[str]:
        """
        Get the selected columns in the order shown in the list.

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
        """
        Initialize the year range filter.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        layout.addWidget(QLabel('Year range:'))

        # Minimum year spinbox
        self._min_year = QSpinBox()
        self._min_year.setRange(1900, 2100)
        self._min_year.setValue(1900)
        self._min_year.setPrefix('From: ')
        self._min_year.valueChanged.connect(self._on_value_changed)
        self._min_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._min_year.wheelEvent = lambda event: event.ignore()  # type: ignore
        layout.addWidget(self._min_year)

        # Maximum year spinbox
        self._max_year = QSpinBox()
        self._max_year.setRange(1900, 2100)
        self._max_year.setValue(2100)
        self._max_year.setPrefix('To: ')
        self._max_year.valueChanged.connect(self._on_value_changed)
        self._max_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._max_year.wheelEvent = lambda event: event.ignore()  # type: ignore
        layout.addWidget(self._max_year)

        # Clear button
        self._clear_btn = QToolButton()
        self._clear_btn.setText('×')
        self._clear_btn.setToolTip('Clear year range filter')
        self._clear_btn.clicked.connect(self._clear_filter)
        layout.addWidget(self._clear_btn)

    def get_filter(self) -> Dict[str, Any]:
        """
        Get the current filter settings.

        Returns:
            Dictionary with year range filter settings
        """
        min_year = self._min_year.value()
        max_year = self._max_year.value()

        if min_year == self._min_year.minimum() and max_year == self._max_year.maximum():
            return {}

        return {'year': {'min': min_year, 'max': max_year}}

    @Slot(int)
    def _on_value_changed(self, value: int) -> None:
        """Handle value changes in either spinbox."""
        self.filterChanged.emit(self.get_filter())

    @Slot()
    def _clear_filter(self) -> None:
        """Clear the filter by resetting to default values."""
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
        """
        Initialize the model.

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
        """
        Get the number of rows in the model.

        Args:
            parent: Parent index

        Returns:
            Number of rows
        """
        if parent.isValid():
            return 0
        return self._row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get the number of columns in the model.

        Args:
            parent: Parent index

        Returns:
            Number of columns
        """
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get the data at the specified index.

        Args:
            index: Model index
            role: Data role

        Returns:
            Data value
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
        """
        Get the header data for a section.

        Args:
            section: Section index
            orientation: Header orientation
            role: Data role

        Returns:
            Header data
        """
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self._columns):
            col_id = self._columns[section]
            return self._column_map.get(col_id, col_id)

        return str(section + 1)

    def set_columns(self, columns: List[str]) -> None:
        """
        Set the model columns.

        Args:
            columns: New list of column IDs
        """
        self.beginResetModel()
        self._columns = columns
        self.endResetModel()

    def set_data(self, data: List[Dict[str, Any]], total_count: int) -> None:
        """
        Set the model data.

        Args:
            data: List of data dictionaries
            total_count: Total count of all records
        """
        self.beginResetModel()
        self._data = data
        self._row_count = len(data)
        self._total_count = total_count
        self.endResetModel()

    def get_total_count(self) -> int:
        """
        Get the total record count.

        Returns:
            Total count
        """
        return self._total_count

    def get_row_data(self, row: int) -> Dict[str, Any]:
        """
        Get the data for a specific row.

        Args:
            row: Row index

        Returns:
            Row data dictionary
        """
        if 0 <= row < self._row_count:
            return self._data[row].copy()
        return {}

    def get_all_data(self) -> List[Dict[str, Any]]:
        """
        Get all data rows.

        Returns:
            List of all data dictionaries
        """
        return self._data.copy()


class FilterProxyModel(QSortFilterProxyModel):
    """Proxy model for client-side filtering of query results."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the proxy model.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._filters: Dict[str, Any] = {}
        self._column_map: Dict[int, str] = {}

    def set_filters(self, filters: Dict[str, Any]) -> None:
        """
        Set the active filters.

        Args:
            filters: Dictionary of filter values by column
        """
        self._filters = filters
        self.invalidateFilter()

    def set_column_map(self, columns: List[str]) -> None:
        """
        Set the column mapping.

        Args:
            columns: List of column IDs
        """
        self._column_map = {i: col_id for i, col_id in enumerate(columns)}

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Determine if a row should be included in the filtered results.

        Args:
            source_row: Row index in the source model
            source_parent: Parent index

        Returns:
            True if the row should be included, False otherwise
        """
        if not self._filters:
            return True

        source_model = self.sourceModel()
        if not source_model:
            return True

        # Get row data for filtering
        row_data = {}
        for col, col_id in self._column_map.items():
            idx = source_model.index(source_row, col, source_parent)
            value = source_model.data(idx, Qt.ItemDataRole.DisplayRole)
            row_data[col_id] = value

        # Apply text filters
        for col_id, filter_value in self._filters.items():
            if col_id == 'year':
                continue  # Handled separately

            if isinstance(filter_value, str) and col_id in row_data:
                row_value = str(row_data.get(col_id, '')).lower()
                if filter_value.lower() not in row_value:
                    return False

        # Apply year range filter
        if 'year' in self._filters and isinstance(self._filters['year'], dict):
            year_filter = self._filters['year']
            min_year = year_filter.get('min')
            max_year = year_filter.get('max')

            try:
                if row_data.get('year') is not None:
                    row_year = int(row_data['year'])

                    if min_year is not None and row_year < min_year:
                        return False

                    if max_year is not None and row_year > max_year:
                        return False
            except (ValueError, TypeError):
                pass  # Skip filtering if year isn't a valid integer

        return True


class TableFilterWidget(QWidget):
    """Widget for client-side filtering of table data."""

    filterChanged = Signal(dict)

    def __init__(
            self,
            columns: List[str],
            column_map: Dict[str, str],
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the filter widget.

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

        # Header with controls
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

        # Container for filter widgets
        self._filters_layout = QVBoxLayout()
        self._layout.addLayout(self._filters_layout)

        self._filter_widgets: List[QWidget] = []

    def set_columns(self, columns: List[str]) -> None:
        """
        Set the available columns.

        Args:
            columns: List of column IDs
        """
        self._columns = columns

    def get_filters(self) -> Dict[str, Any]:
        """
        Get the current filter settings.

        Returns:
            Dictionary of filter values by column
        """
        return self._filter_map.copy()

    def _add_year_range_filter(self) -> None:
        """Add a year range filter widget."""
        # Check if a year range filter already exists
        for widget in self._filter_widgets:
            if isinstance(widget, YearRangeTableFilter):
                return

        # Create and add the year range filter
        year_range_filter = YearRangeTableFilter(self)
        year_range_filter.filterChanged.connect(self._on_year_range_filter_changed)
        self._filters_layout.addWidget(year_range_filter)
        self._filter_widgets.append(year_range_filter)

        # Update UI state
        self._clear_all_btn.setEnabled(True)

    def _add_filter(self) -> None:
        """Add a text-based column filter."""
        # Create layout for the new filter
        row_layout = QHBoxLayout()

        # Column selection dropdown
        column_combo = QComboBox()
        for col_id in self._columns:
            if col_id not in self._filter_map or not isinstance(self._filter_map[col_id], str):
                column_combo.addItem(self._column_map.get(col_id, col_id), col_id)

        if column_combo.count() == 0:
            return  # No available columns to filter on

        row_layout.addWidget(column_combo)

        # Filter input field
        filter_input = QLineEdit()
        filter_input.setPlaceholderText('Filter value...')
        row_layout.addWidget(filter_input)

        # Remove button
        remove_btn = QToolButton()
        remove_btn.setText('×')
        remove_btn.setToolTip('Remove filter')
        row_layout.addWidget(remove_btn)

        # Create widget container
        widget_container = QWidget()
        widget_container.setLayout(row_layout)
        self._filters_layout.addWidget(widget_container)
        self._filter_widgets.append(widget_container)

        # Get initial column ID
        col_id = column_combo.currentData()

        # Define update handler
        def update_filter() -> None:
            nonlocal col_id

            # Get current values
            current_col = column_combo.currentData()
            value = filter_input.text().strip()

            # Remove old value if column changed
            if col_id in self._filter_map and current_col != col_id:
                del self._filter_map[col_id]

            # Update filter map
            if value:
                self._filter_map[current_col] = value
            elif current_col in self._filter_map:
                del self._filter_map[current_col]

            # Update col_id for next change
            col_id = current_col

            # Update UI state
            self._clear_all_btn.setEnabled(bool(self._filter_map))

            # Notify of changes with slight delay to allow typing
            QTimer.singleShot(200, lambda: self.filterChanged.emit(self.get_filters()))

        # Define remove handler
        def remove_filter() -> None:
            current_col = column_combo.currentData()

            # Remove filter from map
            if current_col in self._filter_map:
                del self._filter_map[current_col]

            # Remove widget
            self._filters_layout.removeWidget(widget_container)
            self._filter_widgets.remove(widget_container)
            widget_container.deleteLater()

            # Update UI state
            self._clear_all_btn.setEnabled(bool(self._filter_map))

            # Notify of changes
            self.filterChanged.emit(self.get_filters())

        # Connect signals
        column_combo.currentIndexChanged.connect(update_filter)
        filter_input.textChanged.connect(update_filter)
        remove_btn.clicked.connect(remove_filter)

    @Slot(dict)
    def _on_year_range_filter_changed(self, year_filter: Dict[str, Any]) -> None:
        """
        Handle changes to the year range filter.

        Args:
            year_filter: The new year filter settings
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

        # Remove all filter widgets
        for widget in self._filter_widgets:
            widget.deleteLater()

        self._filter_widgets.clear()

        # Update UI state
        self._clear_all_btn.setEnabled(False)

        # Notify of changes
        self.filterChanged.emit(self.get_filters())


class ExportOptionsDialog(QDialog):
    """Dialog for configuring export options."""

    def __init__(
            self,
            format_type: str,
            current_count: int,
            total_count: int,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the dialog.

        Args:
            format_type: Export format (e.g., 'csv', 'excel')
            current_count: Number of rows in current view
            total_count: Total number of matching rows
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

        # Disable all results option if already showing all
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
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def export_all(self) -> bool:
        """
        Check if all results should be exported.

        Returns:
            True to export all results, False to export only the current page
        """
        return self._all_results_radio.isChecked()


class OverlayProgressDialog(QDialog):
    """Dialog showing progress as an overlay on the parent window."""

    cancelled = Signal()

    def __init__(
            self,
            title: str,
            parent: QWidget
    ) -> None:
        """
        Initialize the dialog.

        Args:
            title: Title for the progress dialog
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)

        # Set up UI
        layout = QVBoxLayout()

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

        # Status label
        self._status_label = QLabel("Starting...")
        layout.addWidget(self._status_label)

        # Cancel button
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(self._cancel_button, 0, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

        # Size and position
        self.resize(400, 150)
        self._center_on_parent()

    def _center_on_parent(self) -> None:
        """Center the dialog on the parent widget."""
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.center().x() - self.width() // 2,
                parent_rect.center().y() - self.height() // 2
            )

    def set_progress(self, value: int, maximum: int = 100, status: Optional[str] = None) -> None:
        """
        Update the progress display.

        Args:
            value: Current progress value
            maximum: Maximum progress value
            status: Optional status message
        """
        if maximum > 0:
            self._progress_bar.setMaximum(maximum)
            self._progress_bar.setValue(value)
        else:
            # Indeterminate progress
            self._progress_bar.setMaximum(0)

        if status:
            self._status_label.setText(status)

    @Slot()
    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.cancelled.emit()


class DataTableWidget(QWidget):
    """Widget for displaying and interacting with query results."""

    queryStarted = Signal()
    queryFinished = Signal()

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus_manager: EventBusManager,
            logger: logging.Logger,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the data table widget.

        Args:
            database_handler: Handler for database operations
            event_bus_manager: Manager for event bus operations
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)

        # Set up signals for cross-thread communication
        self._signals = QuerySignals()
        self._signals.started.connect(
            self._on_query_started,
            Qt.ConnectionType.QueuedConnection
        )
        self._signals.completed.connect(
            self._on_query_completed,
            Qt.ConnectionType.QueuedConnection
        )
        self._signals.failed.connect(
            self._on_query_failed,
            Qt.ConnectionType.QueuedConnection
        )
        self._signals.progress.connect(
            self._on_query_progress,
            Qt.ConnectionType.QueuedConnection
        )
        self._signals.cancelled.connect(
            self._on_query_cancelled,
            Qt.ConnectionType.QueuedConnection
        )

        self._overlay_progress = None
        self._query_running = False

        self._database_handler = database_handler
        self._event_bus_manager = event_bus_manager
        self._logger = logger

        # Get available columns
        try:
            self._available_columns = database_handler.get_available_columns()
        except Exception as e:
            self._logger.error(f'Error getting available columns: {str(e)}')
            self._available_columns = []
        self._column_map = {col['id']: col['name'] for col in self._available_columns}

        # Default columns
        self._selected_columns = ['vehicle_id', 'year', 'make', 'model', 'submodel']

        # Pagination state
        self._current_page = 1
        self._page_size = 100
        self._total_count = 0

        # Sorting state
        self._sort_column: Optional[str] = None
        self._sort_descending = False

        # Filtering state
        self._table_filters: Dict[str, Any] = {}
        self._current_filter_panels: List[Dict[str, List[int]]] = []

        # Unique callback ID
        self._callback_id = f'datatable_{uuid.uuid4()}'

        # Export handler
        self._exporter = DataExporter(logger)

        # Set up UI
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

        # Create models
        self._model = QueryResultModel(self._selected_columns, self._column_map, self)
        self._proxy_model = FilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.set_column_map(self._selected_columns)

        # Set up table view with proxy model
        self._table_view.setModel(self._proxy_model)
        self._table_view.horizontalHeader().sortIndicatorChanged.connect(
            self._on_sort_indicator_changed
        )

        self._layout.addWidget(self._table_view)

        # Bottom section with filters and pagination
        bottom_layout = QHBoxLayout()

        # Filters
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

        # Initialize pagination UI
        self._update_pagination_ui()

        # Subscribe to events
        asyncio.create_task(self._subscribe_to_events())

    def closeEvent(self, event: Any) -> None:
        """Handle the close event by unsubscribing from events."""
        self._event_bus_manager.unsubscribe(subscriber_id=self._callback_id)

    async def _subscribe_to_events(self) -> None:
        """Subscribe to query results events."""
        await self._event_bus_manager.subscribe(
            event_type=VCdbEventType.query_results(),
            callback=self._on_query_results,
            subscriber_id=self._callback_id
        )

    def _create_toolbar(self) -> None:
        """Create the toolbar with actions."""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))

        # Run query action
        self._run_query_action = QAction('Run Query', self)
        self._run_query_action.setToolTip('Execute the query with current filters')
        self._run_query_action.triggered.connect(self._run_query)
        toolbar.addAction(self._run_query_action)

        toolbar.addSeparator()

        # Select columns action
        self._select_columns_action = QAction('Select Columns', self)
        self._select_columns_action.setToolTip('Select and order table columns')
        self._select_columns_action.triggered.connect(self._show_column_selection)
        toolbar.addAction(self._select_columns_action)

        toolbar.addSeparator()

        # Export actions
        self._export_csv_action = QAction('Export CSV', self)
        self._export_csv_action.setToolTip('Export results to CSV file')
        self._export_csv_action.triggered.connect(lambda: self._export_data(export_type='csv'))
        toolbar.addAction(self._export_csv_action)

        if EXCEL_AVAILABLE:
            self._export_excel_action = QAction('Export Excel', self)
            self._export_excel_action.setToolTip('Export results to Excel file')
            self._export_excel_action.triggered.connect(
                lambda: self._export_data(export_type='excel')
            )
            toolbar.addAction(self._export_excel_action)

        self._layout.addWidget(toolbar)

    def get_callback_id(self) -> str:
        """
        Get the callback ID for this widget.

        Returns:
            Unique callback ID
        """
        return self._callback_id

    def get_selected_columns(self) -> List[str]:
        """
        Get the currently selected columns.

        Returns:
            List of column IDs
        """
        return self._selected_columns

    def get_page_size(self) -> int:
        """
        Get the current page size.

        Returns:
            Number of rows per page
        """
        return self._page_size

    def execute_query(self, filter_panels: List[Dict[str, List[int]]]) -> None:
        """
        Execute a query with the specified filters.

        Args:
            filter_panels: List of filter dictionaries from multiple panels
        """
        if self._query_running:
            self._logger.warning('Query already running, ignoring request')
            return

        self._query_running = True
        self._current_filter_panels = filter_panels

        # Update UI for query state
        self._set_ui_state_for_query(True)

        # Signal query start
        self._signals.started.emit()

        # Publish query execute event
        asyncio.create_task(self._event_bus_manager.publish(
            event_type=VCdbEventType.query_execute(),
            source='vcdb_explorer',
            payload={
                'filter_panels': filter_panels,
                'columns': self._selected_columns,
                'page': self._current_page,
                'page_size': self._page_size,
                'sort_by': self._sort_column,
                'sort_desc': self._sort_descending,
                'table_filters': {},  # No server-side table filters
                'callback_id': self._callback_id
            }
        ))

    def _set_ui_state_for_query(self, running: bool) -> None:
        """
        Update the UI state based on query status.

        Args:
            running: True if a query is running, False otherwise
        """
        self._run_query_action.setEnabled(not running)
        self._select_columns_action.setEnabled(not running)
        self._export_csv_action.setEnabled(not running)

        if EXCEL_AVAILABLE:
            self._export_excel_action.setEnabled(not running)

        self._filter_group.setEnabled(not running)
        self._page_size_combo.setEnabled(not running)
        self._page_input.setEnabled(not running)

        self._first_page_btn.setEnabled(not running and self._current_page > 1)
        self._prev_page_btn.setEnabled(not running and self._current_page > 1)
        self._next_page_btn.setEnabled(not running and self._current_page < self._get_max_page())
        self._last_page_btn.setEnabled(not running and self._current_page < self._get_max_page())

    def _get_max_page(self) -> int:
        """
        Calculate the maximum page number based on total count and page size.

        Returns:
            Maximum page number
        """
        return max(1, (self._total_count + self._page_size - 1) // self._page_size)

    @Slot()
    def _on_query_started(self) -> None:
        """Handle query started signal."""
        # Create and show overlay progress dialog
        if not self._overlay_progress:
            self._overlay_progress = OverlayProgressDialog("Executing query...", self)
            self._overlay_progress.cancelled.connect(self._cancel_query)
            self._overlay_progress.show()

        self.queryStarted.emit()

    @Slot(object)
    def _on_query_completed(self, data: Dict[str, Any]) -> None:
        """
        Handle query completed signal.

        Args:
            data: Query results data
        """
        results = data.get('results', [])
        total_count = data.get('total_count', 0)

        # Update model with results
        self._model.set_data(results, total_count)
        self._table_view.reset()

        # Update state
        self._total_count = total_count
        self._update_pagination_ui()

        # Close progress dialog
        if self._overlay_progress:
            self._overlay_progress.close()
            self._overlay_progress = None

        self._query_running = False
        self._set_ui_state_for_query(False)

        self._logger.debug(f'Query completed: {len(results)} results of {total_count} total')

        # Apply table filters if active
        if self._filter_group.isChecked() and self._table_filters:
            self._proxy_model.set_filters(self._table_filters)

        self.queryFinished.emit()

    @Slot(str)
    def _on_query_failed(self, error_message: str) -> None:
        """
        Handle query failed signal.

        Args:
            error_message: Error message
        """
        # Close progress dialog
        if self._overlay_progress:
            self._overlay_progress.close()
            self._overlay_progress = None

        self._query_running = False
        self._set_ui_state_for_query(False)

        # Show error message
        QMessageBox.critical(self, 'Query Error', f'Error executing query: {error_message}')

        self._logger.error(f'Query failed: {error_message}')
        self.queryFinished.emit()

    @Slot()
    def _on_query_cancelled(self) -> None:
        """Handle query cancelled signal."""
        # Close progress dialog
        if self._overlay_progress:
            self._overlay_progress.close()
            self._overlay_progress = None

        self._query_running = False
        self._set_ui_state_for_query(False)

        self._logger.debug('Query cancelled')
        self.queryFinished.emit()

    @Slot(int, int)
    def _on_query_progress(self, current: int, total: int) -> None:
        """
        Handle query progress signal.

        Args:
            current: Current progress value
            total: Maximum progress value
        """
        if self._overlay_progress:
            if total > 0:
                self._overlay_progress.set_progress(
                    current,
                    total,
                    f"Processing {current} of {total}..."
                )
            else:
                self._overlay_progress.set_progress(0, 0, "Processing...")

    @Slot()
    def _run_query(self) -> None:
        """Run a query with the current filters."""
        if not self._query_running:
            self.execute_query(self._current_filter_panels)
        else:
            self._logger.warning('Query already running')

    @Slot()
    def _cancel_query(self) -> None:
        """Cancel the current query."""
        if self._query_running:
            self._logger.debug('Cancelling query')
            asyncio.create_task(self._database_handler.cancel_query(self._callback_id))

    async def _on_query_results(self, event: Any) -> None:
        """
        Handle query results event.

        Args:
            event: Query results event
        """
        payload = event.payload
        callback_id = payload.get('callback_id')

        self._logger.debug(
            f'_on_query_results called: callback_id={callback_id}, expected={self._callback_id}'
        )

        # Check that the callback ID matches this widget
        if callback_id != self._callback_id:
            return

        results = payload.get('results', [])
        total_count = payload.get('total_count', 0)
        error = payload.get('error')
        cancelled = payload.get('cancelled', False)

        if cancelled:
            self._signals.cancelled.emit()
        elif error:
            self._logger.error(f'Query error: {error}')
            self._signals.failed.emit(error)
        else:
            self._logger.debug(f'Query results received: {len(results)} rows of {total_count} total')
            self._signals.completed.emit({'results': results, 'total_count': total_count})

    def _show_column_selection(self) -> None:
        """Show the column selection dialog."""
        dialog = ColumnSelectionDialog(self._available_columns, self._selected_columns, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_columns = dialog.get_selected_columns()

            if new_columns != self._selected_columns:
                self._selected_columns = new_columns
                self._model.set_columns(self._selected_columns)
                self._proxy_model.set_column_map(self._selected_columns)
                self._filter_widget.set_columns(self._selected_columns)

                if self._model.rowCount() > 0:
                    # Run the query again to get the new columns
                    self._run_query()

    async def _export_to_file(
            self,
            export_type: str,
            data: List[Dict[str, Any]],
            file_path: str
    ) -> None:
        """
        Export data to a file asynchronously.

        Args:
            export_type: Export format (e.g., 'csv', 'excel')
            data: Data to export
            file_path: Path to export file
        """
        try:
            if export_type == 'csv':
                await self._exporter.export_csv(
                    data=data,
                    columns=self._selected_columns,
                    column_map=self._column_map,
                    file_path=file_path
                )
            elif export_type == 'excel' and EXCEL_AVAILABLE:
                await self._exporter.export_excel(
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

        except Exception as e:
            self._logger.error(f'Error exporting data: {str(e)}')
            QMessageBox.critical(self, 'Export Error', f'Error exporting data: {str(e)}')

    async def _export_all_to_file(
            self,
            export_type: str,
            file_path: str,
            progress_dialog: QProgressDialog
    ) -> None:
        """
        Export all matching data to a file asynchronously.

        Args:
            export_type: Export format (e.g., 'csv', 'excel')
            file_path: Path to export file
            progress_dialog: Progress dialog to update
        """
        try:
            # Define progress update function
            async def update_progress(current: int, total: int) -> Optional[bool]:
                if progress_dialog.wasCanceled():
                    return False
                progress_dialog.setValue(current)
                QApplication.processEvents()
                return None

            # Export all data
            rows_exported = await self._exporter.export_all_data(
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
                table_filters={},  # No server-side table filters
                progress_callback=update_progress
            )

            if not progress_dialog.wasCanceled():
                QMessageBox.information(
                    self,
                    'Export Complete',
                    f'Successfully exported {rows_exported} rows to {export_type.upper()} file.'
                )

        except Exception as e:
            self._logger.error(f'Error exporting data: {str(e)}')
            QMessageBox.critical(self, 'Export Error', f'Error exporting data: {str(e)}')

    def _export_data(self, export_type: str) -> None:
        """
        Export data to a file.

        Args:
            export_type: Export format (e.g., 'csv', 'excel')
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

        # Get current data counts
        current_count = self._proxy_model.rowCount()
        total_count = self._model.get_total_count()

        # Show export options dialog
        options_dialog = ExportOptionsDialog(export_type, current_count, total_count, self)

        if not options_dialog.exec():
            return

        export_all = options_dialog.export_all() and total_count > current_count

        try:
            if not export_all:
                # Get filtered data
                if self._filter_group.isChecked() and self._table_filters:
                    # Get data from proxy model for filtered results
                    data = []
                    for row in range(self._proxy_model.rowCount()):
                        model_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()
                        data.append(self._model.get_row_data(model_row))
                else:
                    # Get all data from model
                    data = self._model.get_all_data()

                # Execute the export asynchronously
                asyncio.create_task(self._export_to_file(export_type, data, file_path))

            else:
                # Create progress dialog for full export
                progress = QProgressDialog('Exporting data...', 'Cancel', 0, total_count, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.setAutoClose(True)
                progress.setAutoReset(True)
                progress.show()

                # Execute full export asynchronously
                asyncio.create_task(self._export_all_to_file(export_type, file_path, progress))

            self._logger.info(f'Started data export to {file_path}')

        except Exception as e:
            self._logger.error(f'Error starting export: {str(e)}')
            QMessageBox.critical(self, 'Export Error', f'Error starting export: {str(e)}')

    @Slot()
    def _on_page_size_changed(self) -> None:
        """Handle page size changes."""
        new_size = self._page_size_combo.currentData()

        if new_size != self._page_size:
            self._page_size = new_size
            self._current_page = 1
            self._run_query()

    @Slot(int)
    def _on_page_input_changed(self, page: int) -> None:
        """
        Handle page input changes.

        Args:
            page: New page number
        """
        if page != self._current_page:
            self._current_page = page
            self._refresh_current_page()

    def _refresh_current_page(self) -> None:
        """Refresh the current page of results."""
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
        max_page = self._get_max_page()

        if self._current_page < max_page:
            self._current_page += 1
            self._refresh_current_page()

    @Slot()
    def _goto_last_page(self) -> None:
        """Go to the last page."""
        max_page = self._get_max_page()

        if self._current_page < max_page:
            self._current_page = max_page
            self._refresh_current_page()

    def _update_pagination_ui(self) -> None:
        """Update the pagination UI based on current state."""
        max_page = self._get_max_page()

        # Update page spinbox
        self._page_input.blockSignals(True)
        self._page_input.setRange(1, max_page)
        self._page_input.setValue(self._current_page)
        self._page_input.blockSignals(False)

        # Update page label
        self._page_label.setText(f'of {max_page}')

        # Update navigation buttons
        self._first_page_btn.setEnabled(not self._query_running and self._current_page > 1)
        self._prev_page_btn.setEnabled(not self._query_running and self._current_page > 1)
        self._next_page_btn.setEnabled(not self._query_running and self._current_page < max_page)
        self._last_page_btn.setEnabled(not self._query_running and self._current_page < max_page)

        # Update count label
        if self._total_count == 0:
            self._count_label.setText('No results')
        else:
            start_idx = (self._current_page - 1) * self._page_size + 1
            end_idx = min(self._current_page * self._page_size, self._total_count)

            # If filtering is active, show filtered count
            if self._filter_group.isChecked() and self._table_filters:
                filtered_count = self._proxy_model.rowCount()
                if filtered_count < end_idx - start_idx + 1:
                    self._count_label.setText(
                        f'Showing {filtered_count} of {self._total_count} rows (filtered)'
                    )
                else:
                    self._count_label.setText(f'Showing {start_idx}-{end_idx} of {self._total_count} rows')
            else:
                self._count_label.setText(f'Showing {start_idx}-{end_idx} of {self._total_count} rows')

    @Slot(int, Qt.SortOrder)
    def _on_sort_indicator_changed(self, logical_index: int, order: Qt.SortOrder) -> None:
        """
        Handle changes to the sort indicator in the header.

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
        """
        Handle changes to table filters.

        Args:
            filters: New filter values
        """
        self._table_filters = filters

        if self._filter_group.isChecked():
            # Apply filters to proxy model
            self._proxy_model.set_filters(filters)

            # Update pagination UI to show filtered counts
            self._update_pagination_ui()

    @Slot(bool)
    def _on_filter_group_toggled(self, checked: bool) -> None:
        """
        Handle toggling of the filter group.

        Args:
            checked: True if the group is checked, False otherwise
        """
        if checked:
            # Add year range filter if no filters exist
            if not self._table_filters:
                self._filter_widget._add_year_range_filter()

            # Apply existing filters
            self._proxy_model.set_filters(self._table_filters)
        else:
            # Clear proxy model filters
            self._proxy_model.set_filters({})

        # Update pagination UI
        self._update_pagination_ui()

    @Slot(QPoint)
    def _show_context_menu(self, pos: QPoint) -> None:
        """
        Show the context menu for the table view.

        Args:
            pos: Position where the menu should be shown
        """
        selected_indexes = self._table_view.selectionModel().selectedRows()
        has_selection = len(selected_indexes) > 0

        context_menu = QMenu(self)

        # Copy selected rows action
        copy_selected_action = QAction('Copy Selected Row(s)', self)
        copy_selected_action.triggered.connect(self._copy_selected_rows)
        copy_selected_action.setEnabled(has_selection)
        context_menu.addAction(copy_selected_action)

        # Copy all rows action
        copy_all_action = QAction('Copy All Visible Rows', self)
        copy_all_action.triggered.connect(self._copy_all_rows)
        copy_all_action.setEnabled(self._proxy_model.rowCount() > 0)
        context_menu.addAction(copy_all_action)

        context_menu.addSeparator()

        # Export actions
        export_csv_action = QAction('Export to CSV...', self)
        export_csv_action.triggered.connect(lambda: self._export_data('csv'))
        context_menu.addAction(export_csv_action)

        if EXCEL_AVAILABLE:
            export_excel_action = QAction('Export to Excel...', self)
            export_excel_action.triggered.connect(lambda: self._export_data('excel'))
            context_menu.addAction(export_excel_action)

        context_menu.popup(self._table_view.viewport().mapToGlobal(pos))

    def _copy_selected_rows(self) -> None:
        """Copy selected rows to the clipboard."""
        selected_indexes = self._table_view.selectionModel().selectedRows()

        if not selected_indexes:
            return

        selected_indexes.sort(key=lambda idx: idx.row())

        rows_data = []

        # Add header row
        header_row = []
        for col_idx, col_id in enumerate(self._selected_columns):
            header_row.append(self._column_map.get(col_id, col_id))
        rows_data.append('\t'.join(header_row))

        # Add data rows
        for idx in selected_indexes:
            proxy_row = idx.row()
            source_row = self._proxy_model.mapToSource(idx).row()

            row_data = []
            for col_idx, col_id in enumerate(self._selected_columns):
                cell_value = str(
                    self._model.data(self._model.index(source_row, col_idx), Qt.ItemDataRole.DisplayRole) or ''
                )
                row_data.append(cell_value)

            rows_data.append('\t'.join(row_data))

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(rows_data))

        self._logger.debug(f'Copied {len(selected_indexes)} rows to clipboard')

    def _copy_all_rows(self) -> None:
        """Copy all visible rows to the clipboard."""
        row_count = self._proxy_model.rowCount()

        if row_count == 0:
            return

        rows_data = []

        # Add header row
        header_row = []
        for col_idx, col_id in enumerate(self._selected_columns):
            header_row.append(self._column_map.get(col_id, col_id))
        rows_data.append('\t'.join(header_row))

        # Add data rows
        for proxy_row in range(row_count):
            source_row = self._proxy_model.mapToSource(self._proxy_model.index(proxy_row, 0)).row()

            row_data = []
            for col_idx, col_id in enumerate(self._selected_columns):
                cell_value = str(
                    self._model.data(self._model.index(source_row, col_idx), Qt.ItemDataRole.DisplayRole) or ''
                )
                row_data.append(cell_value)

            rows_data.append('\t'.join(row_data))

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(rows_data))

        self._logger.debug(f'Copied all {row_count} rows to clipboard')