# processed_project/qorzen_stripped/plugins/database_connector_plugin/code/ui/results_view.py
from __future__ import annotations

'''
Results view for the Database Connector Plugin.

This module provides a specialized view for displaying query results,
with support for exporting, filtering, and visualizing data.
'''
import asyncio
import json
import csv
import io
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize, QSortFilterProxyModel, QAbstractTableModel, QModelIndex, QPoint
from PySide6.QtGui import QFont, QKeySequence, QAction, QBrush, QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
                               QTableView, QHeaderView, QMenu, QCheckBox, QLineEdit, QSplitter,
                               QToolBar, QStatusBar, QFileDialog, QMessageBox, QApplication, QTabWidget)

from ..models import QueryResult, ColumnMetadata, FieldMapping


class ResultsTableModel(QAbstractTableModel):
    """Model for displaying database query results in a table view."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the results table model.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
        self._columns: List[ColumnMetadata] = []
        self._display_headers: List[str] = []
        self._changed_columns: Dict[str, bool] = {}
        self._highlight_changes: bool = True

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model."""
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns in the model."""
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return the data at the given index for the specified role."""
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None

        column_name = self._columns[index.column()].name
        value = self._data[index.row()].get(column_name)

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if value is None:
                return "NULL"
            elif isinstance(value, (dict, list)):
                return json.dumps(value, default=str)
            else:
                return str(value)

        elif role == Qt.TextAlignmentRole:
            if isinstance(value, (int, float)):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.ForegroundRole:
            if self._highlight_changes and column_name in self._changed_columns:
                return QBrush(QColor(0, 0, 255))  # Blue for changed columns

        elif role == Qt.BackgroundRole:
            if value is None:
                return QBrush(QColor(245, 245, 245))  # Light gray for NULL values

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """Return the header data for the given section and orientation."""
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal and 0 <= section < len(self._display_headers):
            return self._display_headers[section]

        if orientation == Qt.Vertical and 0 <= section < len(self._data):
            return section + 1

        return None

    def setQueryResult(self, result: QueryResult) -> None:
        """Set the query result data for the model.

        Args:
            result: The query result to display
        """
        self.beginResetModel()
        self._data = result.mapped_records if result.mapped_records else result.records
        self._columns = result.columns

        # Set display headers
        self._display_headers = []
        for col in self._columns:
            # Display both original and mapped names if mapping was applied
            if result.mapped_records and col.name in result.records[0] and col.name != result.mapped_records[0].get(
                    col.name, col.name):
                original = col.name
                mapped = next((k for k, v in result.records[0].items() if v == result.mapped_records[0].get(original)),
                              original)
                self._display_headers.append(f"{mapped} ({original})")
            else:
                self._display_headers.append(col.name)

        self._changed_columns = {}
        self.endResetModel()

    def setHighlightChanges(self, highlight: bool) -> None:
        """Set whether to highlight changed columns.

        Args:
            highlight: Whether to highlight changes
        """
        self._highlight_changes = highlight
        self.dataChanged.emit(self.index(0, 0),
                              self.index(self.rowCount() - 1, self.columnCount() - 1))

    def markColumnChanged(self, column_name: str) -> None:
        """Mark a column as changed (for highlighting).

        Args:
            column_name: The name of the changed column
        """
        self._changed_columns[column_name] = True

    def getColumnNames(self) -> List[str]:
        """Get the list of column names."""
        return [col.name for col in self._columns]

    def getColumnTypes(self) -> Dict[str, str]:
        """Get a dictionary mapping column names to their data types."""
        return {col.name: col.type_name for col in self._columns}

    def getDataFrame(self) -> Any:
        """Convert the data to a pandas DataFrame if pandas is available."""
        try:
            import pandas as pd
            return pd.DataFrame(self._data)
        except ImportError:
            return None

    def getValueAt(self, row: int, column: int) -> Any:
        """Get the raw value at the specified row and column indices."""
        if 0 <= row < len(self._data) and 0 <= column < len(self._columns):
            column_name = self._columns[column].name
            return self._data[row].get(column_name)
        return None


class ResultsView(QWidget):
    """Widget for displaying and interacting with database query results."""

    exportRequested = Signal(str)

    def __init__(self, plugin: Any, logger: Any, parent: Optional[QWidget] = None) -> None:
        """Initialize the results view.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            parent: The parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._current_result: Optional[QueryResult] = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QToolBar("Results Tools")
        toolbar.setIconSize(QSize(16, 16))

        self._export_menu = QMenu("Export")
        export_csv_action = self._export_menu.addAction("Export as CSV")
        export_csv_action.triggered.connect(lambda: self.exportRequested.emit("csv"))
        export_json_action = self._export_menu.addAction("Export as JSON")
        export_json_action.triggered.connect(lambda: self.exportRequested.emit("json"))
        export_excel_action = self._export_menu.addAction("Export as Excel")
        export_excel_action.triggered.connect(lambda: self.exportRequested.emit("excel"))

        export_button = QPushButton("Export")
        export_button.setMenu(self._export_menu)
        toolbar.addWidget(export_button)

        toolbar.addSeparator()

        filter_label = QLabel("Filter:")
        toolbar.addWidget(filter_label)

        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter results...")
        self._filter_edit.textChanged.connect(self._apply_filter)
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.setFixedWidth(200)
        toolbar.addWidget(self._filter_edit)

        toolbar.addSeparator()

        self._column_combo = QComboBox()
        self._column_combo.setMinimumWidth(150)
        toolbar.addWidget(self._column_combo)

        toolbar.addSeparator()

        self._stats_button = QPushButton("Show Statistics")
        self._stats_button.clicked.connect(self._show_statistics)
        toolbar.addWidget(self._stats_button)

        main_layout.addWidget(toolbar)

        # Results table
        self._table_view = QTableView()
        self._table_view.setSortingEnabled(True)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSelectionBehavior(QTableView.SelectRows)
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.customContextMenuRequested.connect(self._show_context_menu)

        self._table_model = ResultsTableModel()
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._table_model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._table_view.setModel(self._proxy_model)

        main_layout.addWidget(self._table_view)

        # Status bar
        status_layout = QHBoxLayout()
        self._record_count_label = QLabel("No results")
        self._selection_label = QLabel("")
        status_layout.addWidget(self._record_count_label)
        status_layout.addStretch()
        status_layout.addWidget(self._selection_label)
        main_layout.addLayout(status_layout)

        # Connect signals
        self._table_view.selectionModel().selectionChanged.connect(self._update_selection_info)

    def set_query_result(self, result: QueryResult) -> None:
        """Set and display the query result.

        Args:
            result: The query result to display
        """
        self._current_result = result
        self._table_model.setQueryResult(result)

        # Update column filter combo
        self._column_combo.clear()
        self._column_combo.addItem("All Columns", None)
        for col in result.columns:
            self._column_combo.addItem(col.name, col.name)

        # Resize columns to content
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Update record count
        if result.truncated:
            self._record_count_label.setText(f"Showing {result.row_count} rows (result truncated)")
        else:
            self._record_count_label.setText(f"{result.row_count} rows")

        # Auto-resize columns, but with a maximum width
        for i in range(self._table_model.columnCount()):
            width = self._table_view.horizontalHeader().sectionSize(i)
            if width > 300:
                self._table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)
                self._table_view.horizontalHeader().resizeSection(i, 300)

        # Clear filter
        self._filter_edit.clear()

    def get_query_result(self) -> Optional[QueryResult]:
        """Get the current query result."""
        return self._current_result

    def _apply_filter(self, text: str) -> None:
        """Apply a filter to the results table.

        Args:
            text: The filter text
        """
        column_idx = -1  # All columns
        column_data = self._column_combo.currentData()

        if column_data:
            column_names = self._table_model.getColumnNames()
            if column_data in column_names:
                column_idx = column_names.index(column_data)

        self._proxy_model.setFilterKeyColumn(column_idx)
        self._proxy_model.setFilterFixedString(text)

        filtered_count = self._proxy_model.rowCount()
        total_count = self._table_model.rowCount()

        if text and filtered_count < total_count:
            self._record_count_label.setText(f"Showing {filtered_count} of {total_count} rows")
        elif self._current_result and self._current_result.truncated:
            self._record_count_label.setText(f"Showing {total_count} rows (result truncated)")
        else:
            self._record_count_label.setText(f"{total_count} rows")

    def _show_context_menu(self, pos: QPoint) -> None:
        """Show the context menu for the results table.

        Args:
            pos: The position where the menu should be shown
        """
        index = self._table_view.indexAt(pos)
        if not index.isValid():
            return

        global_pos = self._table_view.mapToGlobal(pos)
        menu = QMenu(self)

        copy_action = menu.addAction("Copy Cell")
        copy_action.triggered.connect(lambda: self._copy_cell_to_clipboard(index))

        copy_row_action = menu.addAction("Copy Row")
        copy_row_action.triggered.connect(lambda: self._copy_row_to_clipboard(index.row()))

        copy_all_action = menu.addAction("Copy All")
        copy_all_action.triggered.connect(self._copy_all_to_clipboard)

        menu.exec_(global_pos)

    def _copy_cell_to_clipboard(self, index: QModelIndex) -> None:
        """Copy the cell value at the given index to the clipboard.

        Args:
            index: The model index of the cell to copy
        """
        if not index.isValid():
            return

        source_index = self._proxy_model.mapToSource(index)
        value = self._table_model.data(source_index, Qt.DisplayRole)

        if value:
            QApplication.clipboard().setText(str(value))

    def _copy_row_to_clipboard(self, row: int) -> None:
        """Copy the entire row to the clipboard as tab-separated values.

        Args:
            row: The row index to copy
        """
        source_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()

        values = []
        for col in range(self._table_model.columnCount()):
            value = self._table_model.data(self._table_model.index(source_row, col), Qt.DisplayRole)
            values.append(str(value) if value else "")

        QApplication.clipboard().setText("\t".join(values))

    def _copy_all_to_clipboard(self) -> None:
        """Copy all visible data to the clipboard as tab-separated values."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter="\t")

        # Write headers
        headers = [self._table_model.headerData(col, Qt.Horizontal)
                   for col in range(self._table_model.columnCount())]
        writer.writerow(headers)

        # Write data
        for row in range(self._proxy_model.rowCount()):
            source_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()
            values = []
            for col in range(self._table_model.columnCount()):
                value = self._table_model.data(self._table_model.index(source_row, col), Qt.DisplayRole)
                values.append(str(value) if value else "")
            writer.writerow(values)

        QApplication.clipboard().setText(output.getvalue())

    def _update_selection_info(self) -> None:
        """Update the selection information in the status bar."""
        selection = self._table_view.selectionModel().selectedRows()
        if selection:
            self._selection_label.setText(f"{len(selection)} row(s) selected")
        else:
            self._selection_label.setText("")

    def _show_statistics(self) -> None:
        """Show basic statistics for the selected column."""
        column_data = self._column_combo.currentData()
        if not column_data or not self._current_result:
            QMessageBox.information(self, "No Column Selected",
                                    "Please select a column to view statistics.")
            return

        try:
            column_idx = self._table_model.getColumnNames().index(column_data)
            column_type = self._table_model.getColumnTypes().get(column_data, "Unknown")

            # Extract values for the selected column
            values = []
            for row in range(self._proxy_model.rowCount()):
                source_row = self._proxy_model.mapToSource(self._proxy_model.index(row, 0)).row()
                value = self._table_model.getValueAt(source_row, column_idx)
                if value is not None:
                    values.append(value)

            # Calculate statistics
            stats_text = f"Column: {column_data}\n"
            stats_text += f"Type: {column_type}\n"
            stats_text += f"Count: {len(values)}\n"
            stats_text += f"NULL Count: {self._table_model.rowCount() - len(values)}\n"

            # Numeric statistics
            if all(isinstance(v, (int, float)) for v in values) and values:
                stats_text += f"Sum: {sum(values)}\n"
                stats_text += f"Min: {min(values)}\n"
                stats_text += f"Max: {max(values)}\n"
                stats_text += f"Avg: {sum(values) / len(values):.2f}\n"

                # Count unique values if not too many
                if len(set(values)) <= 20:
                    value_counts = {}
                    for v in values:
                        value_counts[v] = value_counts.get(v, 0) + 1
                    stats_text += "\nValue Counts:\n"
                    for v, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
                        stats_text += f"{v}: {count}\n"

            # String statistics
            elif all(isinstance(v, str) for v in values) and values:
                stats_text += f"Min Length: {min(len(v) for v in values)}\n"
                stats_text += f"Max Length: {max(len(v) for v in values)}\n"
                stats_text += f"Avg Length: {sum(len(v) for v in values) / len(values):.2f}\n"

                # Count unique values if not too many
                if len(set(values)) <= 20:
                    value_counts = {}
                    for v in values:
                        value_counts[v] = value_counts.get(v, 0) + 1
                    stats_text += "\nValue Counts:\n"
                    for v, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
                        if len(v) > 50:  # Truncate long strings
                            v = v[:47] + "..."
                        stats_text += f"{v}: {count}\n"

            QMessageBox.information(self, "Column Statistics", stats_text)

        except Exception as e:
            self._logger.error(f"Error calculating statistics: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error calculating statistics: {str(e)}")