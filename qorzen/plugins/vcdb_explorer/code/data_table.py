#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VCdb Explorer data table module.

This module provides UI components for displaying and managing query results.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, cast
import csv
import tempfile

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableView,
    QHeaderView, QAbstractItemView, QComboBox, QCheckBox, QSpinBox,
    QScrollArea, QFrame, QToolButton, QMenu, QDialog, QListWidget,
    QListWidgetItem, QDialogButtonBox, QFileDialog, QProgressBar,
    QSizePolicy, QToolBar, QLineEdit, QGroupBox, QGridLayout, QCompleter
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QAbstractTableModel, QModelIndex, QSortFilterProxyModel,
    QTimer, QSize, QRegularExpression
)
from PySide6.QtGui import QIcon, QAction, QStandardItemModel, QStandardItem

try:
    import openpyxl

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

from .database import VCdbDatabase, DatabaseError


class ColumnSelectionDialog(QDialog):
    """Dialog for selecting and ordering columns."""

    def __init__(
            self,
            available_columns: List[Dict[str, str]],
            selected_columns: List[str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the column selection dialog.

        Args:
            available_columns: List of available columns
            selected_columns: List of currently selected column IDs
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Select Columns")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)

        self._available_columns = available_columns
        self._selected_columns = selected_columns

        # Map column IDs to names
        self._column_map = {col["id"]: col["name"] for col in available_columns}

        # Set up layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Instructions
        instructions = QLabel("Select columns to display and drag to reorder:")
        layout.addWidget(instructions)

        # List widget for selected columns
        self._list_widget = QListWidget()
        self._list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        layout.addWidget(self._list_widget)

        # Add available columns to the list
        for col_id in self._column_map:
            item = QListWidgetItem(self._column_map[col_id])
            item.setData(Qt.UserRole, col_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Checked if col_id in selected_columns else Qt.Unchecked
            )
            self._list_widget.addItem(item)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_columns(self) -> List[str]:
        """Get the list of selected columns in display order.

        Returns:
            List of column IDs
        """
        result = []

        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item.checkState() == Qt.Checked:
                col_id = item.data(Qt.UserRole)
                result.append(col_id)

        return result


class QueryResultModel(QAbstractTableModel):
    """Table model for displaying query results."""

    def __init__(
            self,
            columns: List[str],
            column_map: Dict[str, str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the query result model.

        Args:
            columns: List of column IDs
            column_map: Dictionary mapping column IDs to display names
            parent: Parent widget
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
            parent: Parent index

        Returns:
            Row count
        """
        if parent.isValid():
            return 0
        return self._row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get the number of columns in the model.

        Args:
            parent: Parent index

        Returns:
            Column count
        """
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(
            self,
            index: QModelIndex,
            role: int = Qt.DisplayRole
    ) -> Any:
        """Get data for a specific index and role.

        Args:
            index: Model index
            role: Data role

        Returns:
            Requested data
        """
        if not index.isValid() or not (0 <= index.row() < self._row_count):
            return None

        row = index.row()
        col_id = self._columns[index.column()]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return str(self._data[row].get(col_id, ""))

        return None

    def headerData(
            self,
            section: int,
            orientation: Qt.Orientation,
            role: int = Qt.DisplayRole
    ) -> Any:
        """Get header data.

        Args:
            section: Row or column number
            orientation: Horizontal or vertical orientation
            role: Data role

        Returns:
            Header data
        """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal and 0 <= section < len(self._columns):
            col_id = self._columns[section]
            return self._column_map.get(col_id, col_id)

        return str(section + 1)

    def set_columns(self, columns: List[str]) -> None:
        """Set the columns to display.

        Args:
            columns: List of column IDs
        """
        self.beginResetModel()
        self._columns = columns
        self.endResetModel()

    def set_data(self, data: List[Dict[str, Any]], total_count: int) -> None:
        """Set the model data.

        Args:
            data: List of data dictionaries
            total_count: Total number of results
        """
        self.beginResetModel()
        self._data = data
        self._row_count = len(data)
        self._total_count = total_count
        self.endResetModel()

    def get_total_count(self) -> int:
        """Get the total number of results.

        Returns:
            Total result count
        """
        return self._total_count

    def get_row_data(self, row: int) -> Dict[str, Any]:
        """Get all data for a specific row.

        Args:
            row: Row index

        Returns:
            Dictionary with row data
        """
        if 0 <= row < self._row_count:
            return self._data[row].copy()
        return {}

    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all model data.

        Returns:
            List of row data dictionaries
        """
        return self._data.copy()


class TableFilterWidget(QWidget):
    """Widget for filtering table data."""

    filterChanged = Signal(dict)  # table_filters

    def __init__(
            self,
            columns: List[str],
            column_map: Dict[str, str],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the table filter widget.

        Args:
            columns: List of column IDs
            column_map: Dictionary mapping column IDs to display names
            parent: Parent widget
        """
        super().__init__(parent)
        self._columns = columns
        self._column_map = column_map
        self._filter_map: Dict[str, Any] = {}

        # Set up layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Filter header with title and buttons
        header_layout = QHBoxLayout()

        # Title
        title = QLabel("Table Filters")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add filter button
        self._add_filter_btn = QPushButton("Add Filter")
        self._add_filter_btn.clicked.connect(self._add_filter)
        header_layout.addWidget(self._add_filter_btn)

        # Clear all button
        self._clear_all_btn = QPushButton("Clear All")
        self._clear_all_btn.clicked.connect(self._clear_all_filters)
        self._clear_all_btn.setEnabled(False)
        header_layout.addWidget(self._clear_all_btn)

        self._layout.addLayout(header_layout)

        # Filter container
        self._filters_layout = QVBoxLayout()
        self._layout.addLayout(self._filters_layout)

    def set_columns(self, columns: List[str]) -> None:
        """Set the available columns.

        Args:
            columns: List of column IDs
        """
        self._columns = columns

    def get_filters(self) -> Dict[str, Any]:
        """Get the current filters.

        Returns:
            Dictionary of column ID to filter value
        """
        return self._filter_map.copy()

    def _add_filter(self) -> None:
        """Add a new filter row."""
        # Create filter row layout
        row_layout = QHBoxLayout()

        # Column selection combo
        column_combo = QComboBox()
        for col_id in self._columns:
            if col_id not in self._filter_map:  # Skip columns already filtered
                column_combo.addItem(self._column_map.get(col_id, col_id), col_id)

        if column_combo.count() == 0:
            return  # No more columns to filter

        row_layout.addWidget(column_combo)

        # Filter input (text field for now, can be customized based on column type)
        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Filter value...")
        row_layout.addWidget(filter_input)

        # Remove button
        remove_btn = QToolButton()
        remove_btn.setText("×")
        remove_btn.setToolTip("Remove filter")
        row_layout.addWidget(remove_btn)

        # Save layout and widgets
        widget_container = QWidget()
        widget_container.setLayout(row_layout)
        self._filters_layout.addWidget(widget_container)

        # Get the column ID
        col_id = column_combo.currentData()

        # Connect signals
        def update_filter() -> None:
            current_col = column_combo.currentData()
            value = filter_input.text()

            # Remove old filter if column changed
            if col_id in self._filter_map and current_col != col_id:
                del self._filter_map[col_id]

            # Store new filter
            if value:
                self._filter_map[current_col] = value
            elif current_col in self._filter_map:
                del self._filter_map[current_col]

            # Update UI
            self._clear_all_btn.setEnabled(bool(self._filter_map))

            # Emit signal
            self.filterChanged.emit(self.get_filters())

        def remove_filter() -> None:
            current_col = column_combo.currentData()
            if current_col in self._filter_map:
                del self._filter_map[current_col]

            # Remove widgets
            self._filters_layout.removeWidget(widget_container)
            widget_container.deleteLater()

            # Update UI
            self._clear_all_btn.setEnabled(bool(self._filter_map))

            # Emit signal
            self.filterChanged.emit(self.get_filters())

        column_combo.currentIndexChanged.connect(update_filter)
        filter_input.textChanged.connect(update_filter)
        remove_btn.clicked.connect(remove_filter)

    def _clear_all_filters(self) -> None:
        """Clear all filters."""
        # Clear the filter map
        self._filter_map.clear()

        # Remove all filter widgets
        while self._filters_layout.count():
            item = self._filters_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Update UI
        self._clear_all_btn.setEnabled(False)

        # Emit signal
        self.filterChanged.emit(self.get_filters())


class DataTableWidget(QWidget):
    """Widget for displaying query results in a table."""

    def __init__(
            self,
            database: VCdbDatabase,
            logger: logging.Logger,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the data table widget.

        Args:
            database: VCdb database instance
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._database = database
        self._logger = logger

        # Get available columns from database
        self._available_columns = database.get_available_columns()
        self._column_map = {col["id"]: col["name"] for col in self._available_columns}

        # Default selected columns
        self._selected_columns = ["vehicle_id", "year", "make", "model", "submodel"]

        # Pagination state
        self._current_page = 1
        self._page_size = 100
        self._total_count = 0

        # Sorting state
        self._sort_column: Optional[str] = None
        self._sort_descending = False

        # Table filters
        self._table_filters: Dict[str, Any] = {}

        # Set up layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Toolbar with actions
        self._create_toolbar()

        # Table view
        self._table_view = QTableView()
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.verticalHeader().setVisible(True)

        # Create and set the model
        self._model = QueryResultModel(self._selected_columns, self._column_map, self)
        self._table_view.setModel(self._model)

        # Connect the sort indicator changed signal
        self._table_view.horizontalHeader().sortIndicatorChanged.connect(
            self._on_sort_indicator_changed
        )

        self._layout.addWidget(self._table_view)

        # Filters and pagination in a horizontal layout
        bottom_layout = QHBoxLayout()

        # Table filters
        self._filter_widget = TableFilterWidget(
            self._selected_columns, self._column_map, self
        )
        self._filter_widget.filterChanged.connect(self._on_table_filter_changed)

        # Create a collapsible section for filters
        self._filter_group = QGroupBox("Table Filters")
        self._filter_group.setCheckable(True)
        self._filter_group.setChecked(False)  # Collapsed by default
        filter_group_layout = QVBoxLayout()
        filter_group_layout.addWidget(self._filter_widget)
        self._filter_group.setLayout(filter_group_layout)

        bottom_layout.addWidget(self._filter_group, 3)

        # Pagination controls
        pagination_widget = QWidget()
        pagination_layout = QGridLayout()
        pagination_layout.setContentsMargins(10, 5, 10, 5)

        # Page size
        pagination_layout.addWidget(QLabel("Page Size:"), 0, 0)
        self._page_size_combo = QComboBox()
        for size in [10, 25, 50, 100, 250, 500, 1000]:
            self._page_size_combo.addItem(str(size), size)
        self._page_size_combo.setCurrentText(str(self._page_size))
        self._page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        pagination_layout.addWidget(self._page_size_combo, 0, 1)

        # Page navigation
        pagination_layout.addWidget(QLabel("Page:"), 1, 0)
        nav_layout = QHBoxLayout()

        self._first_page_btn = QToolButton()
        self._first_page_btn.setText("«")
        self._first_page_btn.setToolTip("First Page")
        self._first_page_btn.clicked.connect(self._goto_first_page)
        nav_layout.addWidget(self._first_page_btn)

        self._prev_page_btn = QToolButton()
        self._prev_page_btn.setText("‹")
        self._prev_page_btn.setToolTip("Previous Page")
        self._prev_page_btn.clicked.connect(self._goto_prev_page)
        nav_layout.addWidget(self._prev_page_btn)

        self._page_label = QLabel("1 of 1")
        nav_layout.addWidget(self._page_label)

        self._next_page_btn = QToolButton()
        self._next_page_btn.setText("›")
        self._next_page_btn.setToolTip("Next Page")
        self._next_page_btn.clicked.connect(self._goto_next_page)
        nav_layout.addWidget(self._next_page_btn)

        self._last_page_btn = QToolButton()
        self._last_page_btn.setText("»")
        self._last_page_btn.setToolTip("Last Page")
        self._last_page_btn.clicked.connect(self._goto_last_page)
        nav_layout.addWidget(self._last_page_btn)

        pagination_layout.addLayout(nav_layout, 1, 1)

        # Row count
        self._count_label = QLabel("0 rows")
        pagination_layout.addWidget(self._count_label, 2, 0, 1, 2)

        pagination_widget.setLayout(pagination_layout)
        bottom_layout.addWidget(pagination_widget, 1)

        self._layout.addLayout(bottom_layout)

        # Update UI state
        self._update_pagination_ui()

    def _create_toolbar(self) -> None:
        """Create the toolbar with action buttons."""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))

        # Run Query Action
        self._run_query_action = QAction("Run Query", self)
        self._run_query_action.setToolTip("Execute the query with current filters")
        self._run_query_action.triggered.connect(self._run_query)
        toolbar.addAction(self._run_query_action)

        toolbar.addSeparator()

        # Select Columns Action
        self._select_columns_action = QAction("Select Columns", self)
        self._select_columns_action.setToolTip("Select and order table columns")
        self._select_columns_action.triggered.connect(self._show_column_selection)
        toolbar.addAction(self._select_columns_action)

        toolbar.addSeparator()

        # Export Actions
        self._export_csv_action = QAction("Export CSV", self)
        self._export_csv_action.setToolTip("Export results to CSV file")
        self._export_csv_action.triggered.connect(
            lambda: self._export_data(export_type="csv")
        )
        toolbar.addAction(self._export_csv_action)

        if EXCEL_AVAILABLE:
            self._export_excel_action = QAction("Export Excel", self)
            self._export_excel_action.setToolTip("Export results to Excel file")
            self._export_excel_action.triggered.connect(
                lambda: self._export_data(export_type="excel")
            )
            toolbar.addAction(self._export_excel_action)

        self._layout.addWidget(toolbar)

    def execute_query(self, filter_panels: List[Dict[str, List[int]]]) -> None:
        """Execute a query with the given filter panels.

        Args:
            filter_panels: List of filter dictionaries
        """
        try:
            # Reset to first page
            self._current_page = 1

            # Execute the query
            results, total_count = self._database.execute_query(
                filter_panels=filter_panels,
                columns=self._selected_columns,
                page=self._current_page,
                page_size=self._page_size,
                sort_by=self._sort_column,
                sort_desc=self._sort_descending,
                table_filters=self._table_filters
            )

            # Update the model
            self._model.set_data(results, total_count)
            self._total_count = total_count

            # Update pagination UI
            self._update_pagination_ui()

        except DatabaseError as e:
            self._logger.error(f"Query execution failed: {str(e)}")

    def _run_query(self) -> None:
        """Execute the query with current filters."""
        # This will be connected to the filter panel manager
        pass

    def set_run_query_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for the run query action.

        Args:
            callback: Function to call when run query is clicked
        """
        self._run_query = callback

    def _show_column_selection(self) -> None:
        """Show the column selection dialog."""
        dialog = ColumnSelectionDialog(
            self._available_columns,
            self._selected_columns,
            self
        )

        if dialog.exec() == QDialog.Accepted:
            # Update selected columns
            new_columns = dialog.get_selected_columns()

            # Only refresh if columns changed
            if new_columns != self._selected_columns:
                self._selected_columns = new_columns

                # Update the model
                self._model.set_columns(self._selected_columns)

                # Update the filter widget
                self._filter_widget.set_columns(self._selected_columns)

                # Re-run the query if we have data
                if self._model.rowCount() > 0:
                    self._run_query()

    def _export_data(self, export_type: str) -> None:
        """Export table data to a file.

        Args:
            export_type: Type of export ('csv' or 'excel')
        """
        # Create file dialog
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)

        if export_type == "csv":
            file_dialog.setNameFilter("CSV Files (*.csv)")
            file_dialog.setDefaultSuffix("csv")
        else:  # excel
            file_dialog.setNameFilter("Excel Files (*.xlsx)")
            file_dialog.setDefaultSuffix("xlsx")

        if not file_dialog.exec():
            return  # Canceled

        file_path = file_dialog.selectedFiles()[0]

        try:
            # Check if we should export all data or just current page
            if self._total_count > 1000:
                # Ask if user wants to export all or just current page
                pass  # Implement later

            # Get data to export
            data = self._model.get_all_data()

            if export_type == "csv":
                with open(file_path, 'w', newline='') as csv_file:
                    # Create header from selected columns
                    header = [self._column_map.get(col, col) for col in self._selected_columns]

                    # Create CSV writer
                    writer = csv.DictWriter(
                        csv_file,
                        fieldnames=self._selected_columns,
                        extrasaction='ignore'
                    )

                    # Write header with display names
                    writer.writerow({col: self._column_map.get(col, col) for col in self._selected_columns})

                    # Write data rows
                    for row in data:
                        writer.writerow(row)

            elif export_type == "excel" and EXCEL_AVAILABLE:
                # Create workbook and sheet
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "VCdb Results"

                # Add header row
                for col_idx, col_id in enumerate(self._selected_columns, 1):
                    ws.cell(row=1, column=col_idx, value=self._column_map.get(col_id, col_id))

                # Add data rows
                for row_idx, row_data in enumerate(data, 2):
                    for col_idx, col_id in enumerate(self._selected_columns, 1):
                        ws.cell(row=row_idx, column=col_idx, value=row_data.get(col_id, ""))

                # Save the workbook
                wb.save(file_path)

            self._logger.info(f"Data exported to {file_path}")

        except Exception as e:
            self._logger.error(f"Error exporting data: {str(e)}")

    def _on_page_size_changed(self) -> None:
        """Handle page size change."""
        new_size = self._page_size_combo.currentData()
        if new_size != self._page_size:
            self._page_size = new_size
            self._current_page = 1  # Reset to first page
            # Re-run query
            self._run_query()

    def _goto_first_page(self) -> None:
        """Go to the first page."""
        if self._current_page > 1:
            self._current_page = 1
            self._run_query()

    def _goto_prev_page(self) -> None:
        """Go to the previous page."""
        if self._current_page > 1:
            self._current_page -= 1
            self._run_query()

    def _goto_next_page(self) -> None:
        """Go to the next page."""
        max_page = (self._total_count + self._page_size - 1) // self._page_size
        if self._current_page < max_page:
            self._current_page += 1
            self._run_query()

    def _goto_last_page(self) -> None:
        """Go to the last page."""
        max_page = (self._total_count + self._page_size - 1) // self._page_size
        if self._current_page < max_page:
            self._current_page = max_page
            self._run_query()

    def _update_pagination_ui(self) -> None:
        """Update the pagination UI controls."""
        max_page = max(1, (self._total_count + self._page_size - 1) // self._page_size)

        # Update page label
        self._page_label.setText(f"{self._current_page} of {max_page}")

        # Update navigation buttons
        self._first_page_btn.setEnabled(self._current_page > 1)
        self._prev_page_btn.setEnabled(self._current_page > 1)
        self._next_page_btn.setEnabled(self._current_page < max_page)
        self._last_page_btn.setEnabled(self._current_page < max_page)

        # Update count label
        if self._total_count == 0:
            self._count_label.setText("No results")
        else:
            start_idx = (self._current_page - 1) * self._page_size + 1
            end_idx = min(self._current_page * self._page_size, self._total_count)
            self._count_label.setText(f"Showing {start_idx}-{end_idx} of {self._total_count} rows")

    def _on_sort_indicator_changed(self, logical_index: int, order: Qt.SortOrder) -> None:
        """Handle sort indicator change in the table header.

        Args:
            logical_index: Column index
            order: Sort order
        """
        if 0 <= logical_index < len(self._selected_columns):
            self._sort_column = self._selected_columns[logical_index]
            self._sort_descending = (order == Qt.DescendingOrder)

            # Re-run query with new sort
            self._run_query()

    def _on_table_filter_changed(self, filters: Dict[str, Any]) -> None:
        """Handle table filter changes.

        Args:
            filters: New table filters
        """
        self._table_filters = filters

        # Reset to first page
        self._current_page = 1

        # Re-run query with new filters
        self._run_query()