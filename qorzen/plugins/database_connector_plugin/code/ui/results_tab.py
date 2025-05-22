"""
Results tab for the Database Connector Plugin.

This module provides the results tab UI for displaying query results
and exporting data to various formats.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QComboBox, QSpinBox, QCheckBox, QTextEdit, QSplitter,
    QFrame, QMessageBox, QFileDialog, QProgressBar, QMenu
)

from ..models import QueryResult, ExportFormat, ExportSettings


class ResultsTab(QWidget):
    """
    Results tab for displaying query results and export functionality.

    Provides:
    - Query results display in table format
    - Export to multiple formats
    - Result statistics and metadata
    - Row count and execution time display
    """

    # Signals
    operation_started = Signal(str)  # message
    operation_finished = Signal()
    status_changed = Signal(str)  # message

    def __init__(
            self,
            plugin: Any,
            logger: logging.Logger,
            concurrency_manager: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the results tab.

        Args:
            plugin: The plugin instance
            logger: Logger instance
            concurrency_manager: Concurrency manager
            parent: Parent widget
        """
        super().__init__(parent)

        self._plugin = plugin
        self._logger = logger
        self._concurrency_manager = concurrency_manager

        # UI components
        self._results_table: Optional[QTableWidget] = None
        self._info_text: Optional[QTextEdit] = None
        self._export_format_combo: Optional[QComboBox] = None
        self._include_headers_check: Optional[QCheckBox] = None
        self._max_rows_spin: Optional[QSpinBox] = None
        self._row_count_label: Optional[QLabel] = None
        self._execution_time_label: Optional[QLabel] = None
        self._connection_label: Optional[QLabel] = None

        # State
        self._current_result: Optional[QueryResult] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Results info panel
        info_panel = self._create_info_panel()
        layout.addWidget(info_panel)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Results table
        table_widget = self._create_results_table()
        splitter.addWidget(table_widget)

        # Query info panel
        query_info_widget = self._create_query_info_panel()
        splitter.addWidget(query_info_widget)

        # Set splitter proportions (80% table, 20% info)
        splitter.setSizes([800, 200])

        layout.addWidget(splitter)

        # Export panel
        export_panel = self._create_export_panel()
        layout.addWidget(export_panel)

    def _create_info_panel(self) -> QFrame:
        """Create the information panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(60)

        layout = QHBoxLayout(panel)

        # Connection info
        self._connection_label = QLabel("Connection: None")
        layout.addWidget(self._connection_label)

        # Spacer
        layout.addStretch()

        # Row count
        self._row_count_label = QLabel("Rows: 0")
        layout.addWidget(self._row_count_label)

        # Execution time
        self._execution_time_label = QLabel("Time: 0ms")
        layout.addWidget(self._execution_time_label)

        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: asyncio.create_task(self.refresh()))
        layout.addWidget(refresh_button)

        return panel

    def _create_results_table(self) -> QGroupBox:
        """Create the results table widget."""
        group = QGroupBox("Query Results")
        layout = QVBoxLayout(group)

        # Table widget
        self._results_table = QTableWidget()
        self._results_table.setAlternatingRowColors(True)
        self._results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._results_table.customContextMenuRequested.connect(self._show_table_context_menu)

        # Configure headers
        header = self._results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        layout.addWidget(self._results_table)

        return group

    def _create_query_info_panel(self) -> QGroupBox:
        """Create the query information panel."""
        group = QGroupBox("Query Information")
        layout = QVBoxLayout(group)

        self._info_text = QTextEdit()
        self._info_text.setReadOnly(True)
        self._info_text.setMaximumHeight(150)
        layout.addWidget(self._info_text)

        return group

    def _create_export_panel(self) -> QGroupBox:
        """Create the export configuration panel."""
        group = QGroupBox("Export Results")
        layout = QHBoxLayout(group)

        # Export format
        layout.addWidget(QLabel("Format:"))
        self._export_format_combo = QComboBox()
        for format in ExportFormat:
            self._export_format_combo.addItem(format.value.upper(), format)
        layout.addWidget(self._export_format_combo)

        # Include headers
        self._include_headers_check = QCheckBox("Include Headers")
        self._include_headers_check.setChecked(True)
        layout.addWidget(self._include_headers_check)

        # Max rows
        layout.addWidget(QLabel("Max Rows:"))
        self._max_rows_spin = QSpinBox()
        self._max_rows_spin.setRange(0, 1000000)
        self._max_rows_spin.setValue(0)  # 0 = all rows
        self._max_rows_spin.setSpecialValueText("All")
        layout.addWidget(self._max_rows_spin)

        # Spacer
        layout.addStretch()

        # Export button
        export_button = QPushButton("Export...")
        export_button.clicked.connect(self._export_results)
        layout.addWidget(export_button)

        return group

    def show_results(self, result: QueryResult) -> None:
        """
        Display query results.

        Args:
            result: The query result to display
        """
        try:
            self._current_result = result

            # Update info labels
            self._update_info_labels()

            # Populate results table
            self._populate_results_table()

            # Update query info
            self._update_query_info()

            self.status_changed.emit(f"Showing {result.row_count} rows")

        except Exception as e:
            self._logger.error(f"Failed to show results: {e}")
            self._show_error("Display Error", f"Failed to display results: {e}")

    def _update_info_labels(self) -> None:
        """Update the information labels."""
        if not self._current_result:
            self._connection_label.setText("Connection: None")
            self._row_count_label.setText("Rows: 0")
            self._execution_time_label.setText("Time: 0ms")
            return

        result = self._current_result

        self._connection_label.setText(f"Connection: {result.connection_id}")

        row_text = f"Rows: {result.row_count:,}"
        if result.truncated:
            row_text += " (truncated)"
        self._row_count_label.setText(row_text)

        self._execution_time_label.setText(f"Time: {result.execution_time_ms:,}ms")

    def _populate_results_table(self) -> None:
        """Populate the results table with data."""
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

            # Set table dimensions
            self._results_table.setRowCount(len(records))
            self._results_table.setColumnCount(len(columns))

            # Set column headers
            column_names = [col.get('name', f'Column {i + 1}') for i, col in enumerate(columns)]
            self._results_table.setHorizontalHeaderLabels(column_names)

            # Populate data
            for row_idx, record in enumerate(records):
                for col_idx, column in enumerate(columns):
                    column_name = column.get('name', f'Column {col_idx + 1}')
                    value = record.get(column_name, '')

                    # Format value for display
                    display_value = self._format_cell_value(value)

                    item = QTableWidgetItem(str(display_value))
                    item.setToolTip(str(display_value))

                    # Make read-only
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self._results_table.setItem(row_idx, col_idx, item)

            # Auto-resize columns to content
            self._results_table.resizeColumnsToContents()

            # Limit column width
            header = self._results_table.horizontalHeader()
            for i in range(self._results_table.columnCount()):
                if header.sectionSize(i) > 300:
                    header.resizeSection(i, 300)

        except Exception as e:
            self._logger.error(f"Failed to populate results table: {e}")
            self._show_error("Table Error", f"Failed to populate table: {e}")

    def _format_cell_value(self, value: Any) -> str:
        """
        Format a cell value for display.

        Args:
            value: The value to format

        Returns:
            Formatted string value
        """
        if value is None:
            return "<NULL>"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                return f"{value:.6g}"  # Remove unnecessary trailing zeros
            return str(value)
        elif isinstance(value, str):
            # Truncate very long strings
            if len(value) > 1000:
                return value[:1000] + "..."
            return value
        else:
            return str(value)

    def _update_query_info(self) -> None:
        """Update the query information panel."""
        if not self._current_result:
            self._info_text.clear()
            return

        result = self._current_result

        info_parts = []

        # Basic info
        info_parts.append(f"Query executed at: {result.executed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        info_parts.append(f"Connection: {result.connection_id}")
        info_parts.append(f"Rows returned: {result.row_count:,}")
        info_parts.append(f"Execution time: {result.execution_time_ms:,} ms")

        if result.truncated:
            info_parts.append("⚠️ Results were truncated due to row limit")

        if result.applied_mapping:
            info_parts.append("✓ Field mappings were applied")

        if result.has_error:
            info_parts.append(f"❌ Error: {result.error_message}")

        # Column information
        if result.columns:
            info_parts.append("")
            info_parts.append("Columns:")
            for i, column in enumerate(result.columns, 1):
                col_info = f"  {i}. {column.get('name', 'Unknown')} ({column.get('type_name', 'Unknown')})"
                if not column.get('nullable', True):
                    col_info += " NOT NULL"
                info_parts.append(col_info)

        # Query text (truncated)
        if result.query:
            info_parts.append("")
            info_parts.append("Query:")
            query_lines = result.query.split('\n')
            if len(query_lines) > 10:
                info_parts.extend(query_lines[:10])
                info_parts.append("... (truncated)")
            else:
                info_parts.extend(query_lines)

        self._info_text.setPlainText('\n'.join(info_parts))

    def _export_results(self) -> None:
        """Export the current results."""
        if not self._current_result or not self._current_result.records:
            self._show_warning("No Data", "No data to export")
            return

        # Get export settings
        export_format = self._export_format_combo.currentData()
        if not export_format:
            self._show_error("Export Error", "Please select an export format")
            return

        # Get file extension
        if hasattr(self._plugin, '_export_service') and self._plugin._export_service:
            file_ext = self._plugin._export_service.get_file_extension(export_format)
        else:
            file_ext = ".txt"

        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            f"query_results{file_ext}",
            f"{export_format.value.upper()} Files (*{file_ext});;All Files (*)"
        )

        if not file_path:
            return

        # Start export
        asyncio.create_task(self._export_results_async(file_path, export_format))

    async def _export_results_async(self, file_path: str, export_format: ExportFormat) -> None:
        """
        Export results asynchronously.

        Args:
            file_path: The output file path
            export_format: The export format
        """
        try:
            self.operation_started.emit("Exporting results...")

            # Create export settings
            settings = ExportSettings(
                format=export_format,
                include_headers=self._include_headers_check.isChecked(),
                max_rows=self._max_rows_spin.value() if self._max_rows_spin.value() > 0 else None
            )

            # Export using plugin service
            actual_path = await self._plugin.export_results(
                results=self._current_result,
                format=export_format,
                file_path=file_path,
                settings=settings
            )

            self.operation_finished.emit()

            # Show success message
            exported_rows = min(len(self._current_result.records),
                                settings.max_rows or len(self._current_result.records))
            self._show_info(
                "Export Complete",
                f"Successfully exported {exported_rows:,} rows to:\n{actual_path}"
            )

            self.status_changed.emit(f"Exported {exported_rows:,} rows to {export_format.value}")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Export failed: {e}")
            self._show_error("Export Error", f"Failed to export results: {e}")

    def _show_table_context_menu(self, position) -> None:
        """Show context menu for the results table."""
        if not self._current_result or not self._current_result.records:
            return

        menu = QMenu(self)

        # Copy cell action
        copy_cell_action = menu.addAction("Copy Cell")
        copy_cell_action.triggered.connect(self._copy_cell)

        # Copy row action
        copy_row_action = menu.addAction("Copy Row")
        copy_row_action.triggered.connect(self._copy_row)

        # Copy column action
        copy_column_action = menu.addAction("Copy Column")
        copy_column_action.triggered.connect(self._copy_column)

        menu.addSeparator()

        # Export visible action
        export_visible_action = menu.addAction("Export Visible Data")
        export_visible_action.triggered.connect(self._export_results)

        menu.exec(self._results_table.mapToGlobal(position))

    def _copy_cell(self) -> None:
        """Copy the current cell to clipboard."""
        current_item = self._results_table.currentItem()
        if current_item:
            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(current_item.text())

    def _copy_row(self) -> None:
        """Copy the current row to clipboard."""
        current_row = self._results_table.currentRow()
        if current_row >= 0:
            row_data = []
            for col in range(self._results_table.columnCount()):
                item = self._results_table.item(current_row, col)
                row_data.append(item.text() if item else "")

            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText('\t'.join(row_data))

    def _copy_column(self) -> None:
        """Copy the current column to clipboard."""
        current_col = self._results_table.currentColumn()
        if current_col >= 0:
            col_data = []

            # Add header
            header_item = self._results_table.horizontalHeaderItem(current_col)
            if header_item:
                col_data.append(header_item.text())

            # Add data
            for row in range(self._results_table.rowCount()):
                item = self._results_table.item(row, current_col)
                col_data.append(item.text() if item else "")

            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText('\n'.join(col_data))

    async def refresh(self) -> None:
        """Refresh the current results display."""
        try:
            if self._current_result:
                # Re-populate the table with current result
                self._populate_results_table()
                self._update_query_info()
                self.status_changed.emit("Results refreshed")

        except Exception as e:
            self._logger.error(f"Failed to refresh results: {e}")
            self._show_error("Refresh Error", f"Failed to refresh results: {e}")

    def clear_results(self) -> None:
        """Clear the current results."""
        self._current_result = None
        self._results_table.setRowCount(0)
        self._results_table.setColumnCount(0)
        self._info_text.clear()
        self._update_info_labels()
        self.status_changed.emit("Results cleared")

    def get_current_result(self) -> Optional[QueryResult]:
        """Get the current query result."""
        return self._current_result

    def _show_error(self, title: str, message: str) -> None:
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)

    def _show_warning(self, title: str, message: str) -> None:
        """Show warning message dialog."""
        QMessageBox.warning(self, title, message)

    def _show_info(self, title: str, message: str) -> None:
        """Show information message dialog."""
        QMessageBox.information(self, title, message)

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Clear results to free memory
            self.clear_results()
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")