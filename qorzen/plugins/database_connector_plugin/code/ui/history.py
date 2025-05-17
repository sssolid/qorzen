# processed_project/qorzen_stripped/plugins/database_connector_plugin/code/ui/history.py
from __future__ import annotations

import uuid

'''
History UI for the Database Connector Plugin.

This module provides a user interface for managing historical database data,
including scheduling periodic data collection and viewing historical snapshots.
'''
import asyncio
import json
import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize, QPoint
from PySide6.QtGui import QFont, QIcon, QColor, QBrush
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QComboBox, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                               QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox,
                               QMessageBox, QInputDialog, QGroupBox, QMenu, QToolButton,
                               QSplitter, QTabWidget, QRadioButton, QButtonGroup, QSpinBox,
                               QTextEdit, QProgressBar, QFrame, QCalendarWidget, QTimeEdit)

from ..models import HistorySchedule, HistoryEntry, SavedQuery


class ScheduleDialog(QDialog):
    """Dialog for creating and editing history collection schedules."""

    def __init__(self, plugin: Any, logger: Any, connection_id: str,
                 parent: Optional[QWidget] = None,
                 schedule: Optional[HistorySchedule] = None) -> None:
        """Initialize the schedule dialog.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            connection_id: The current database connection ID
            parent: The parent widget
            schedule: Optional existing schedule to edit
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._connection_id = connection_id
        self._schedule = schedule
        self._queries: Dict[str, SavedQuery] = {}

        self._init_ui()

        # Load existing schedule if provided
        if schedule:
            self.setWindowTitle("Edit History Schedule")
            self._populate_from_schedule(schedule)
        else:
            self.setWindowTitle("Create History Schedule")

        # Load available queries
        self._load_queries()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)

        main_layout = QVBoxLayout(self)

        # Basic info section
        info_group = QGroupBox("Schedule Information")
        info_form = QFormLayout(info_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter a name for this schedule")

        self._description_edit = QLineEdit()
        self._description_edit.setPlaceholderText("Optional description of this schedule")

        self._query_combo = QComboBox()
        self._query_combo.setMinimumWidth(300)

        self._active_check = QCheckBox("Active")
        self._active_check.setChecked(True)

        info_form.addRow("Name:", self._name_edit)
        info_form.addRow("Description:", self._description_edit)
        info_form.addRow("Query:", self._query_combo)
        info_form.addRow("", self._active_check)

        main_layout.addWidget(info_group)

        # Schedule settings section
        schedule_group = QGroupBox("Schedule Settings")
        schedule_form = QFormLayout(schedule_group)

        # Frequency section
        freq_layout = QHBoxLayout()
        self._frequency_value = QSpinBox()
        self._frequency_value.setRange(1, 9999)
        self._frequency_value.setValue(1)

        self._frequency_unit = QComboBox()
        self._frequency_unit.addItem("Minutes", "m")
        self._frequency_unit.addItem("Hours", "h")
        self._frequency_unit.addItem("Days", "d")
        self._frequency_unit.addItem("Weeks", "w")
        self._frequency_unit.setCurrentIndex(1)  # Default to hours

        freq_layout.addWidget(self._frequency_value)
        freq_layout.addWidget(self._frequency_unit)

        # Retention period
        self._retention_days = QSpinBox()
        self._retention_days.setRange(1, 3650)
        self._retention_days.setValue(365)
        self._retention_days.setSuffix(" days")

        schedule_form.addRow("Frequency:", freq_layout)
        schedule_form.addRow("Data retention:", self._retention_days)

        main_layout.addWidget(schedule_group)

        # Status line
        status_layout = QHBoxLayout()
        self._status_label = QLabel("")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate progress
        self._progress_bar.setVisible(False)

        status_layout.addWidget(self._status_label)
        status_layout.addWidget(self._progress_bar)

        main_layout.addLayout(status_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)

    def _populate_from_schedule(self, schedule: HistorySchedule) -> None:
        """Populate the dialog with data from an existing schedule.

        Args:
            schedule: The schedule to edit
        """
        self._name_edit.setText(schedule.name)
        self._description_edit.setText(schedule.description or "")
        self._active_check.setChecked(schedule.active)
        self._retention_days.setValue(schedule.retention_days)

        # Parse frequency
        import re
        match = re.match(r'^(\d+)([smhdw])$', schedule.frequency.lower())
        if match:
            value, unit = match.groups()
            self._frequency_value.setValue(int(value))

            unit_map = {'s': 0, 'm': 0, 'h': 1, 'd': 2, 'w': 3}
            unit_index = unit_map.get(unit, 1)
            self._frequency_unit.setCurrentIndex(unit_index)

        # Query will be selected when queries are loaded
        self._query_id_to_select = schedule.query_id

    def _load_queries(self) -> None:
        """Load saved queries for the current connection."""
        self._status_label.setText("Loading queries...")
        self._progress_bar.setVisible(True)

        asyncio.create_task(self._async_load_queries())

    async def _async_load_queries(self) -> None:
        """Asynchronously load saved queries."""
        try:
            queries = await self._plugin.get_saved_queries(self._connection_id)
            self._queries = queries

            self._query_combo.clear()
            self._query_combo.addItem("Select a query...", None)

            for query_id, query in sorted(queries.items(), key=lambda q: q[1].name.lower()):
                self._query_combo.addItem(query.name, query_id)

            # Select query if editing
            if hasattr(self, '_query_id_to_select'):
                for i in range(self._query_combo.count()):
                    if self._query_combo.itemData(i) == self._query_id_to_select:
                        self._query_combo.setCurrentIndex(i)
                        break

            self._status_label.setText(f"Loaded {len(queries)} queries")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to load queries: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to load queries: {str(e)}")

    def get_schedule(self) -> HistorySchedule:
        """Get the history schedule created or edited in this dialog.

        Returns:
            The history schedule
        """
        name = self._name_edit.text().strip()
        if not name:
            raise ValueError("Name cannot be empty")

        query_id = self._query_combo.currentData()
        if not query_id:
            raise ValueError("Please select a query")

        # Construct frequency string
        frequency_value = self._frequency_value.value()
        frequency_unit = self._frequency_unit.currentData()
        frequency = f"{frequency_value}{frequency_unit}"

        schedule_id = self._schedule.id if self._schedule else str(uuid.uuid4())

        return HistorySchedule(
            id=schedule_id,
            connection_id=self._connection_id,
            name=name,
            description=self._description_edit.text().strip() or None,
            query_id=query_id,
            frequency=frequency,
            retention_days=self._retention_days.value(),
            active=self._active_check.isChecked()
        )

    def accept(self) -> None:
        """Handle dialog acceptance."""
        try:
            if not self._name_edit.text().strip():
                QMessageBox.warning(self, "Missing Name", "Please enter a name for the schedule.")
                return

            if not self._query_combo.currentData():
                QMessageBox.warning(self, "No Query Selected", "Please select a query.")
                return

            super().accept()

        except Exception as e:
            self._logger.error(f"Error in dialog accept: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")


class HistoryDataDialog(QDialog):
    """Dialog for viewing historical data snapshots."""

    def __init__(self, plugin: Any, logger: Any, history_data: Dict[str, Any],
                 parent: Optional[QWidget] = None) -> None:
        """Initialize the history data dialog.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            history_data: The historical data to display
            parent: The parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._history_data = history_data

        self._init_ui()
        self.setWindowTitle("History Data Snapshot")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        main_layout = QVBoxLayout(self)

        # Metadata section
        metadata = self._history_data.get('metadata', {})

        metadata_group = QGroupBox("Snapshot Information")
        metadata_form = QFormLayout(metadata_group)

        # Extract metadata
        snapshot_id = metadata.get('snapshot_id', 'Unknown')
        table_name = metadata.get('table_name', 'Unknown')
        collected_at = metadata.get('collected_at')
        if isinstance(collected_at, str):
            try:
                collected_at = datetime.datetime.fromisoformat(collected_at)
            except:
                pass

        record_count = metadata.get('record_count', 0)

        # Format the collected_at date
        collected_at_str = "Unknown"
        if isinstance(collected_at, datetime.datetime):
            collected_at_str = collected_at.strftime("%Y-%m-%d %H:%M:%S")

        metadata_form.addRow("Snapshot ID:", QLabel(snapshot_id))
        metadata_form.addRow("Table:", QLabel(table_name))
        metadata_form.addRow("Collected At:", QLabel(collected_at_str))
        metadata_form.addRow("Record Count:", QLabel(str(record_count)))

        main_layout.addWidget(metadata_group)

        # Data table
        self._data_table = QTableWidget()
        self._data_table.setAlternatingRowColors(True)
        self._data_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Populate table with data
        self._populate_data_table()

        main_layout.addWidget(self._data_table)

        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        export_button = QPushButton("Export Data")
        export_button.clicked.connect(self._export_data)
        export_layout.addWidget(export_button)

        main_layout.addLayout(export_layout)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)

    def _populate_data_table(self) -> None:
        """Populate the data table with the historical data."""
        data = self._history_data.get('data', [])
        schema = self._history_data.get('schema', [])

        if not data:
            return

        # Set up columns based on schema
        if schema:
            columns = [col.get('name') for col in schema]
        else:
            # If no schema, use the keys from the first data row
            columns = list(data[0].keys()) if data else []

        self._data_table.setColumnCount(len(columns))
        self._data_table.setHorizontalHeaderLabels(columns)

        # Add data rows
        self._data_table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col_name in enumerate(columns):
                value = row_data.get(col_name)

                # Format the cell value
                if value is None:
                    cell_text = "NULL"
                elif isinstance(value, (dict, list)):
                    cell_text = json.dumps(value)
                else:
                    cell_text = str(value)

                item = QTableWidgetItem(cell_text)
                self._data_table.setItem(row_idx, col_idx, item)

        # Resize columns to content
        self._data_table.resizeColumnsToContents()

        # Limit column width
        for i in range(self._data_table.columnCount()):
            if self._data_table.columnWidth(i) > 300:
                self._data_table.setColumnWidth(i, 300)

    def _export_data(self) -> None:
        """Export the historical data to a file."""
        try:
            from PySide6.QtWidgets import QFileDialog
            import csv
            import json

            file_path, filter_used = QFileDialog.getSaveFileName(
                self,
                "Export Historical Data",
                "",
                "CSV Files (*.csv);;JSON Files (*.json);;All Files (*.*)"
            )

            if not file_path:
                return

            data = self._history_data.get('data', [])

            if filter_used == "CSV Files (*.csv)" or file_path.lower().endswith('.csv'):
                if not file_path.lower().endswith('.csv'):
                    file_path += '.csv'

                # Get column headers
                if data:
                    headers = list(data[0].keys())

                    with open(file_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(data)

            elif filter_used == "JSON Files (*.json)" or file_path.lower().endswith('.json'):
                if not file_path.lower().endswith('.json'):
                    file_path += '.json'

                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Data exported to {file_path}"
            )

        except Exception as e:
            self._logger.error(f"Failed to export data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")


class HistoryWidget(QWidget):
    """Widget for managing historical database data."""

    def __init__(self, plugin: Any, logger: Any, parent: Optional[QWidget] = None) -> None:
        """Initialize the history widget.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            parent: The parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._current_connection_id: Optional[str] = None
        self._history_manager: Optional[Any] = None

        self._init_ui()

        # Get history manager
        self._get_history_manager()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Tab widget for schedules and history
        self._tab_widget = QTabWidget()

        # Schedules tab
        self._schedules_tab = QWidget()
        self._init_schedules_tab()
        self._tab_widget.addTab(self._schedules_tab, "Schedules")

        # History tab
        self._history_tab = QWidget()
        self._init_history_tab()
        self._tab_widget.addTab(self._history_tab, "History Data")

        main_layout.addWidget(self._tab_widget)

        # Status bar
        status_layout = QHBoxLayout()
        self._status_label = QLabel("Ready")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate progress
        self._progress_bar.setVisible(False)

        status_layout.addWidget(self._status_label)
        status_layout.addWidget(self._progress_bar)

        main_layout.addLayout(status_layout)

    def _init_schedules_tab(self) -> None:
        """Initialize the schedules tab."""
        layout = QVBoxLayout(self._schedules_tab)

        # Connection selection area
        conn_layout = QHBoxLayout()
        conn_label = QLabel("Connection:")
        self._schedule_connection_combo = QComboBox()
        self._schedule_connection_combo.setMinimumWidth(200)
        self._schedule_connection_combo.currentIndexChanged.connect(self._on_schedule_connection_selected)

        self._schedule_refresh_button = QPushButton("Refresh")
        self._schedule_refresh_button.setFixedWidth(100)
        self._schedule_refresh_button.clicked.connect(self._refresh_schedules)

        conn_layout.addWidget(conn_label)
        conn_layout.addWidget(self._schedule_connection_combo)
        conn_layout.addWidget(self._schedule_refresh_button)
        conn_layout.addStretch()

        layout.addLayout(conn_layout)

        # Schedules list and details splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Schedules list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        schedules_label = QLabel("Data Collection Schedules")
        schedules_label.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(schedules_label)

        self._schedules_list = QListWidget()
        self._schedules_list.itemSelectionChanged.connect(self._on_schedule_selected)
        left_layout.addWidget(self._schedules_list)

        # Schedule actions
        schedule_actions = QHBoxLayout()
        self._new_schedule_button = QPushButton("New")
        self._new_schedule_button.clicked.connect(self._create_new_schedule)

        self._edit_schedule_button = QPushButton("Edit")
        self._edit_schedule_button.clicked.connect(self._edit_current_schedule)
        self._edit_schedule_button.setEnabled(False)

        self._delete_schedule_button = QPushButton("Delete")
        self._delete_schedule_button.clicked.connect(self._delete_current_schedule)
        self._delete_schedule_button.setEnabled(False)

        schedule_actions.addWidget(self._new_schedule_button)
        schedule_actions.addWidget(self._edit_schedule_button)
        schedule_actions.addWidget(self._delete_schedule_button)

        left_layout.addLayout(schedule_actions)

        splitter.addWidget(left_widget)

        # Right panel - Schedule details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Schedule details section
        details_group = QGroupBox("Schedule Details")
        details_form = QFormLayout(details_group)

        self._schedule_name_label = QLabel("")
        self._schedule_description_label = QLabel("")
        self._schedule_query_label = QLabel("")
        self._schedule_frequency_label = QLabel("")
        self._schedule_retention_label = QLabel("")
        self._schedule_status_label = QLabel("")
        self._schedule_last_run_label = QLabel("")

        details_form.addRow("Name:", self._schedule_name_label)
        details_form.addRow("Description:", self._schedule_description_label)
        details_form.addRow("Query:", self._schedule_query_label)
        details_form.addRow("Frequency:", self._schedule_frequency_label)
        details_form.addRow("Retention:", self._schedule_retention_label)
        details_form.addRow("Status:", self._schedule_status_label)
        details_form.addRow("Last Run:", self._schedule_last_run_label)

        right_layout.addWidget(details_group)

        # Schedule actions section
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        self._run_now_button = QPushButton("Run Now")
        self._run_now_button.clicked.connect(self._run_schedule_now)
        self._run_now_button.setEnabled(False)

        self._toggle_active_button = QPushButton("Toggle Active/Inactive")
        self._toggle_active_button.clicked.connect(self._toggle_schedule_active)
        self._toggle_active_button.setEnabled(False)

        actions_layout.addWidget(self._run_now_button)
        actions_layout.addWidget(self._toggle_active_button)

        right_layout.addWidget(actions_group)

        # Recent history entries
        history_group = QGroupBox("Recent History")
        history_layout = QVBoxLayout(history_group)

        self._schedule_history_list = QListWidget()
        self._schedule_history_list.itemDoubleClicked.connect(self._view_schedule_history_item)

        history_layout.addWidget(self._schedule_history_list)

        right_layout.addWidget(history_group)

        splitter.addWidget(right_widget)

        # Set initial splitter sizes
        splitter.setSizes([200, 400])

        layout.addWidget(splitter)

    def _init_history_tab(self) -> None:
        """Initialize the history data tab."""
        layout = QVBoxLayout(self._history_tab)

        # Connection selection area
        conn_layout = QHBoxLayout()
        conn_label = QLabel("Connection:")
        self._history_connection_combo = QComboBox()
        self._history_connection_combo.setMinimumWidth(200)
        self._history_connection_combo.currentIndexChanged.connect(self._on_history_connection_selected)

        self._history_refresh_button = QPushButton("Refresh")
        self._history_refresh_button.setFixedWidth(100)
        self._history_refresh_button.clicked.connect(self._refresh_history)

        conn_layout.addWidget(conn_label)
        conn_layout.addWidget(self._history_connection_combo)
        conn_layout.addWidget(self._history_refresh_button)
        conn_layout.addStretch()

        layout.addLayout(conn_layout)

        # Search and filter area
        filter_layout = QHBoxLayout()

        table_label = QLabel("Table:")
        self._table_filter_combo = QComboBox()
        self._table_filter_combo.setMinimumWidth(150)
        self._table_filter_combo.addItem("All Tables", None)

        date_label = QLabel("Date Range:")
        self._date_from = QComboBox()
        self._date_from.setMinimumWidth(100)
        self._populate_date_ranges()

        filter_button = QPushButton("Apply Filter")
        filter_button.clicked.connect(self._apply_history_filter)

        filter_layout.addWidget(table_label)
        filter_layout.addWidget(self._table_filter_combo)
        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self._date_from)
        filter_layout.addWidget(filter_button)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # History entries table
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels(["Date", "Table", "Records", "Status", "Snapshot ID"])
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._history_table.setAlternatingRowColors(True)
        self._history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._history_table.customContextMenuRequested.connect(self._show_history_context_menu)
        self._history_table.itemDoubleClicked.connect(self._on_history_item_double_clicked)

        layout.addWidget(self._history_table)

        # Action buttons
        actions_layout = QHBoxLayout()

        self._view_history_button = QPushButton("View Data")
        self._view_history_button.clicked.connect(self._view_selected_history)
        self._view_history_button.setEnabled(False)

        self._delete_history_button = QPushButton("Delete")
        self._delete_history_button.clicked.connect(self._delete_selected_history)
        self._delete_history_button.setEnabled(False)

        self._export_history_button = QPushButton("Export")
        self._export_history_button.clicked.connect(self._export_selected_history)
        self._export_history_button.setEnabled(False)

        actions_layout.addWidget(self._view_history_button)
        actions_layout.addWidget(self._delete_history_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self._export_history_button)

        layout.addLayout(actions_layout)

    def _populate_date_ranges(self) -> None:
        """Populate the date range dropdown with common ranges."""
        self._date_from.clear()
        self._date_from.addItem("All Time", None)
        self._date_from.addItem("Today", "today")
        self._date_from.addItem("Yesterday", "yesterday")
        self._date_from.addItem("Last 7 Days", "7days")
        self._date_from.addItem("Last 30 Days", "30days")
        self._date_from.addItem("This Month", "thismonth")
        self._date_from.addItem("Last Month", "lastmonth")
        self._date_from.addItem("This Year", "thisyear")
        self._date_from.addItem("Custom...", "custom")

    def _get_history_manager(self) -> None:
        """Get the history manager from the plugin."""
        asyncio.create_task(self._async_get_history_manager())

    async def _async_get_history_manager(self) -> None:
        """Asynchronously get the history manager."""
        try:
            self._history_manager = await self._plugin.get_history_manager()
            await self._load_connections()
        except Exception as e:
            self._logger.error(f"Failed to get history manager: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")

    async def _load_connections(self) -> None:
        """Load available database connections."""
        try:
            connections = await self._plugin.get_connections()

            # For schedules tab
            schedule_conn_id = self._schedule_connection_combo.currentData()
            self._schedule_connection_combo.clear()
            self._schedule_connection_combo.addItem("Select a connection...", None)

            # For history tab
            history_conn_id = self._history_connection_combo.currentData()
            self._history_connection_combo.clear()
            self._history_connection_combo.addItem("Select a connection...", None)

            for conn_id, conn in sorted(connections.items(), key=lambda x: x[1].name.lower()):
                self._schedule_connection_combo.addItem(conn.name, conn_id)
                self._history_connection_combo.addItem(conn.name, conn_id)

            # Restore selections if possible
            if schedule_conn_id:
                for i in range(self._schedule_connection_combo.count()):
                    if self._schedule_connection_combo.itemData(i) == schedule_conn_id:
                        self._schedule_connection_combo.setCurrentIndex(i)
                        break

            if history_conn_id:
                for i in range(self._history_connection_combo.count()):
                    if self._history_connection_combo.itemData(i) == history_conn_id:
                        self._history_connection_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f"Failed to load connections: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")

    def set_connection_status(self, connection_id: str, connected: bool) -> None:
        """Update the UI based on connection status changes.

        Args:
            connection_id: The connection ID
            connected: Whether the connection is active
        """
        if connection_id == self._current_connection_id:
            self._new_schedule_button.setEnabled(connected)
            self._run_now_button.setEnabled(connected and self._schedules_list.selectedItems())

            if not connected:
                self._clear_schedule_details()
                self._edit_schedule_button.setEnabled(False)
                self._delete_schedule_button.setEnabled(False)
                self._toggle_active_button.setEnabled(False)
                self._schedules_list.clear()
                self._schedule_history_list.clear()

    async def refresh(self) -> None:
        """Refresh the history manager data."""
        await self._load_connections()

        current_tab = self._tab_widget.currentIndex()
        if current_tab == 0:  # Schedules tab
            if self._current_connection_id:
                await self._load_schedules()
        else:  # History tab
            history_conn_id = self._history_connection_combo.currentData()
            if history_conn_id:
                await self._load_history_entries(history_conn_id)

    def _on_schedule_connection_selected(self, index: int) -> None:
        """Handle schedule connection selection change.

        Args:
            index: The selected index in the combobox
        """
        connection_id = self._schedule_connection_combo.itemData(index)
        self._current_connection_id = connection_id

        self._clear_schedule_details()
        self._schedules_list.clear()
        self._schedule_history_list.clear()

        # Check if connection is active
        is_connected = False
        if connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[connection_id]
            is_connected = connector.is_connected

        self._new_schedule_button.setEnabled(is_connected)

        if connection_id and is_connected:
            asyncio.create_task(self._load_schedules())

    def _on_history_connection_selected(self, index: int) -> None:
        """Handle history connection selection change.

        Args:
            index: The selected index in the combobox
        """
        connection_id = self._history_connection_combo.currentData()

        # Clear existing data
        self._history_table.setRowCount(0)
        self._table_filter_combo.clear()
        self._table_filter_combo.addItem("All Tables", None)

        # Disable buttons
        self._view_history_button.setEnabled(False)
        self._delete_history_button.setEnabled(False)
        self._export_history_button.setEnabled(False)

        if connection_id:
            asyncio.create_task(self._load_history_entries(connection_id))
            asyncio.create_task(self._load_history_tables(connection_id))

    async def _load_schedules(self) -> None:
        """Load history collection schedules for the current connection."""
        if not self._current_connection_id or not self._history_manager:
            return

        try:
            self._status_label.setText("Loading schedules...")
            self._progress_bar.setVisible(True)

            schedules = await self._history_manager.get_all_schedules()

            # Filter schedules for the current connection
            conn_schedules = [s for s in schedules if s.connection_id == self._current_connection_id]

            self._schedules_list.clear()

            for schedule in sorted(conn_schedules, key=lambda s: s.name.lower()):
                item_text = schedule.name
                if schedule.description:
                    item_text += f" - {schedule.description}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, schedule.id)

                # Visual indicator for active/inactive schedules
                if not schedule.active:
                    item.setForeground(QBrush(QColor(120, 120, 120)))  # Gray for inactive schedules

                self._schedules_list.addItem(item)

            self._status_label.setText(f"Loaded {len(conn_schedules)} schedules")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to load schedules: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)

    async def _load_history_entries(self, connection_id: str) -> None:
        """Load history entries for the selected connection.

        Args:
            connection_id: The connection ID to load history for
        """
        if not self._history_manager:
            return

        try:
            self._status_label.setText("Loading history data...")
            self._progress_bar.setVisible(True)

            # Get all entries
            all_entries = await self._history_manager.get_history_entries(limit=1000)

            # Filter by connection
            entries = [e for e in all_entries if e.connection_id == connection_id]

            # Apply table filter if selected
            table_filter = self._table_filter_combo.currentData()
            if table_filter:
                entries = [e for e in entries if e.table_name == table_filter]

            # Apply date filter if selected
            date_filter = self._date_from.currentData()
            if date_filter:
                entries = self._apply_date_filter(entries, date_filter)

            # Sort by collected_at (newest first)
            entries.sort(key=lambda e: e.collected_at, reverse=True)

            # Populate the table
            self._history_table.setRowCount(len(entries))

            for i, entry in enumerate(entries):
                # Date column
                date_item = QTableWidgetItem(entry.collected_at.strftime("%Y-%m-%d %H:%M:%S"))
                self._history_table.setItem(i, 0, date_item)

                # Table column
                table_item = QTableWidgetItem(entry.table_name)
                self._history_table.setItem(i, 1, table_item)

                # Records column
                records_item = QTableWidgetItem(str(entry.record_count))
                self._history_table.setItem(i, 2, records_item)

                # Status column
                status_item = QTableWidgetItem(entry.status)
                if entry.status == "success":
                    status_item.setForeground(QBrush(QColor(0, 128, 0)))  # Green
                else:
                    status_item.setForeground(QBrush(QColor(255, 0, 0)))  # Red
                self._history_table.setItem(i, 3, status_item)

                # Snapshot ID column
                snapshot_item = QTableWidgetItem(entry.snapshot_id)
                snapshot_item.setData(Qt.UserRole, entry)
                self._history_table.setItem(i, 4, snapshot_item)

            self._history_table.resizeColumnsToContents()

            self._status_label.setText(f"Loaded {len(entries)} history entries")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to load history entries: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)

    async def _load_history_tables(self, connection_id: str) -> None:
        """Load tables with history data for the selected connection.

        Args:
            connection_id: The connection ID to load tables for
        """
        if not self._history_manager:
            return

        try:
            # Get all entries
            all_entries = await self._history_manager.get_history_entries(limit=1000)

            # Filter by connection and get unique table names
            tables = sorted(set(e.table_name for e in all_entries if e.connection_id == connection_id))

            # Update the table filter combo
            current_filter = self._table_filter_combo.currentData()
            self._table_filter_combo.clear()
            self._table_filter_combo.addItem("All Tables", None)

            for table_name in tables:
                self._table_filter_combo.addItem(table_name, table_name)

            # Restore selection if possible
            if current_filter:
                for i in range(self._table_filter_combo.count()):
                    if self._table_filter_combo.itemData(i) == current_filter:
                        self._table_filter_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f"Failed to load history tables: {str(e)}")

    def _apply_date_filter(self, entries: List[HistoryEntry], date_filter: str) -> List[HistoryEntry]:
        """Apply a date filter to the history entries.

        Args:
            entries: The entries to filter
            date_filter: The date filter to apply

        Returns:
            The filtered entries
        """
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if date_filter == "today":
            start_date = today
        elif date_filter == "yesterday":
            start_date = today - datetime.timedelta(days=1)
            end_date = today
        elif date_filter == "7days":
            start_date = today - datetime.timedelta(days=7)
        elif date_filter == "30days":
            start_date = today - datetime.timedelta(days=30)
        elif date_filter == "thismonth":
            start_date = today.replace(day=1)
        elif date_filter == "lastmonth":
            last_month = today.month - 1
            last_month_year = today.year
            if last_month == 0:
                last_month = 12
                last_month_year -= 1
            start_date = datetime.datetime(last_month_year, last_month, 1)
            this_month_start = today.replace(day=1)
            end_date = this_month_start
        elif date_filter == "thisyear":
            start_date = today.replace(month=1, day=1)
        elif date_filter == "custom":
            # This would typically show a date picker dialog
            # For now, just default to last 30 days
            start_date = today - datetime.timedelta(days=30)
        else:
            return entries

        # Apply the filter
        if 'end_date' in locals():
            return [e for e in entries if start_date <= e.collected_at < end_date]
        else:
            return [e for e in entries if e.collected_at >= start_date]

    def _on_schedule_selected(self) -> None:
        """Handle schedule selection change."""
        selected_items = self._schedules_list.selectedItems()

        if not selected_items:
            self._clear_schedule_details()
            self._edit_schedule_button.setEnabled(False)
            self._delete_schedule_button.setEnabled(False)
            self._toggle_active_button.setEnabled(False)
            self._run_now_button.setEnabled(False)
            return

        schedule_id = selected_items[0].data(Qt.UserRole)

        self._edit_schedule_button.setEnabled(True)
        self._delete_schedule_button.setEnabled(True)
        self._toggle_active_button.setEnabled(True)

        # Check if connection is active
        is_connected = False
        if self._current_connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[self._current_connection_id]
            is_connected = connector.is_connected

        self._run_now_button.setEnabled(is_connected)

        asyncio.create_task(self._load_schedule_details(schedule_id))
        asyncio.create_task(self._load_schedule_history(schedule_id))

    async def _load_schedule_details(self, schedule_id: str) -> None:
        """Load and display schedule details.

        Args:
            schedule_id: The ID of the schedule to display
        """
        if not self._history_manager:
            return

        try:
            schedule = await self._history_manager.get_schedule(schedule_id)
            if not schedule:
                self._clear_schedule_details()
                return

            # Get the query name
            query_name = "Unknown Query"
            try:
                query = await self._plugin.get_saved_query(schedule.query_id)
                if query:
                    query_name = query.name
            except:
                pass

            # Format frequency
            frequency_text = self._format_frequency(schedule.frequency)

            # Update schedule details
            self._schedule_name_label.setText(schedule.name)
            self._schedule_description_label.setText(schedule.description or "")
            self._schedule_query_label.setText(query_name)
            self._schedule_frequency_label.setText(frequency_text)
            self._schedule_retention_label.setText(f"{schedule.retention_days} days")

            status_text = "Active" if schedule.active else "Inactive"
            status_color = "green" if schedule.active else "red"
            self._schedule_status_label.setText(status_text)
            self._schedule_status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")

            if schedule.last_run:
                last_run = schedule.last_run.strftime("%Y-%m-%d %H:%M:%S")
            else:
                last_run = "Never"

            self._schedule_last_run_label.setText(last_run)

        except Exception as e:
            self._logger.error(f"Failed to load schedule details: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")

    async def _load_schedule_history(self, schedule_id: str) -> None:
        """Load history entries for the selected schedule.

        Args:
            schedule_id: The ID of the schedule to load history for
        """
        if not self._history_manager:
            return

        try:
            entries = await self._history_manager.get_history_entries(schedule_id)

            self._schedule_history_list.clear()

            for entry in sorted(entries, key=lambda e: e.collected_at, reverse=True):
                time_str = entry.collected_at.strftime("%Y-%m-%d %H:%M:%S")
                status = "Success" if entry.status == "success" else "Failed"

                item_text = f"{time_str} - {status} ({entry.record_count} records)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, entry)

                # Visual indicator for success/failure
                if entry.status == "success":
                    item.setForeground(QBrush(QColor(0, 128, 0)))  # Green for success
                else:
                    item.setForeground(QBrush(QColor(255, 0, 0)))  # Red for failure

                self._schedule_history_list.addItem(item)

        except Exception as e:
            self._logger.error(f"Failed to load schedule history: {str(e)}")

    def _format_frequency(self, frequency: str) -> str:
        """Format a frequency string for display.

        Args:
            frequency: The frequency string

        Returns:
            A user-friendly frequency description
        """
        import re
        match = re.match(r'^(\d+)([smhdw])$', frequency.lower())
        if not match:
            return frequency

        value, unit = match.groups()
        value = int(value)

        unit_map = {
            's': "second" if value == 1 else "seconds",
            'm': "minute" if value == 1 else "minutes",
            'h': "hour" if value == 1 else "hours",
            'd': "day" if value == 1 else "days",
            'w': "week" if value == 1 else "weeks"
        }

        return f"Every {value} {unit_map.get(unit, unit)}"

    def _clear_schedule_details(self) -> None:
        """Clear the schedule details display."""
        self._schedule_name_label.setText("")
        self._schedule_description_label.setText("")
        self._schedule_query_label.setText("")
        self._schedule_frequency_label.setText("")
        self._schedule_retention_label.setText("")
        self._schedule_status_label.setText("")
        self._schedule_last_run_label.setText("")
        self._schedule_history_list.clear()

    def _refresh_schedules(self) -> None:
        """Refresh the schedules list."""
        if self._current_connection_id:
            is_connected = False
            if self._current_connection_id in self._plugin._active_connectors:
                connector = self._plugin._active_connectors[self._current_connection_id]
                is_connected = connector.is_connected

            if is_connected:
                asyncio.create_task(self._load_schedules())

    def _refresh_history(self) -> None:
        """Refresh the history entries."""
        connection_id = self._history_connection_combo.currentData()
        if connection_id:
            asyncio.create_task(self._load_history_entries(connection_id))
            asyncio.create_task(self._load_history_tables(connection_id))

    def _create_new_schedule(self) -> None:
        """Create a new history collection schedule."""
        if not self._current_connection_id:
            QMessageBox.warning(self, "No Connection", "Please select a database connection first.")
            return

        # Check if connection is active
        is_connected = False
        if self._current_connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[self._current_connection_id]
            is_connected = connector.is_connected

        if not is_connected:
            QMessageBox.warning(self, "Not Connected",
                                "Please connect to the database before creating a schedule.")
            return

        dialog = ScheduleDialog(self._plugin, self._logger, self._current_connection_id, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                schedule = dialog.get_schedule()
                asyncio.create_task(self._save_schedule(schedule))
            except Exception as e:
                self._logger.error(f"Failed to create schedule: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to create schedule: {str(e)}")

    def _edit_current_schedule(self) -> None:
        """Edit the currently selected schedule."""
        selected_items = self._schedules_list.selectedItems()
        if not selected_items:
            return

        schedule_id = selected_items[0].data(Qt.UserRole)

        asyncio.create_task(self._edit_schedule(schedule_id))

    async def _edit_schedule(self, schedule_id: str) -> None:
        """Edit a history collection schedule.

        Args:
            schedule_id: The ID of the schedule to edit
        """
        if not self._history_manager:
            return

        try:
            schedule = await self._history_manager.get_schedule(schedule_id)
            if not schedule:
                QMessageBox.warning(self, "Schedule Not Found", "The selected schedule could not be found.")
                return

            dialog = ScheduleDialog(self._plugin, self._logger, self._current_connection_id, self, schedule)
            if dialog.exec() == QDialog.Accepted:
                updated_schedule = dialog.get_schedule()
                await self._save_schedule(updated_schedule)

        except Exception as e:
            self._logger.error(f"Failed to edit schedule: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to edit schedule: {str(e)}")

    def _delete_current_schedule(self) -> None:
        """Delete the currently selected schedule."""
        selected_items = self._schedules_list.selectedItems()
        if not selected_items:
            return

        schedule_id = selected_items[0].data(Qt.UserRole)
        schedule_name = selected_items[0].text().split(" - ")[0]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the schedule '{schedule_name}'?\n\n"
            "This will also delete all associated history data.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            asyncio.create_task(self._delete_schedule(schedule_id))

    async def _save_schedule(self, schedule: HistorySchedule) -> None:
        """Save a history collection schedule.

        Args:
            schedule: The schedule to save
        """
        if not self._history_manager:
            return

        try:
            self._status_label.setText("Saving schedule...")
            self._progress_bar.setVisible(True)

            # Save based on whether it's a new or existing schedule
            if hasattr(self._history_manager, 'get_schedule'):
                existing_schedule = await self._history_manager.get_schedule(schedule.id)
                if existing_schedule:
                    await self._history_manager.update_schedule(schedule)
                else:
                    await self._history_manager.create_schedule(schedule)
            else:
                # Fallback if manager doesn't have get_schedule method
                try:
                    await self._history_manager.update_schedule(schedule)
                except:
                    await self._history_manager.create_schedule(schedule)

            await self._load_schedules()

            # Select the saved schedule
            for i in range(self._schedules_list.count()):
                item = self._schedules_list.item(i)
                if item and item.data(Qt.UserRole) == schedule.id:
                    self._schedules_list.setCurrentItem(item)
                    break

            self._status_label.setText("Schedule saved successfully")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to save schedule: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to save schedule: {str(e)}")

    async def _delete_schedule(self, schedule_id: str) -> None:
        """Delete a history collection schedule.

        Args:
            schedule_id: The ID of the schedule to delete
        """
        if not self._history_manager:
            return

        try:
            self._status_label.setText("Deleting schedule...")
            self._progress_bar.setVisible(True)

            await self._history_manager.delete_schedule(schedule_id)

            self._clear_schedule_details()
            await self._load_schedules()

            self._status_label.setText("Schedule deleted successfully")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to delete schedule: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to delete schedule: {str(e)}")

    def _toggle_schedule_active(self) -> None:
        """Toggle the active state of the selected schedule."""
        selected_items = self._schedules_list.selectedItems()
        if not selected_items:
            return

        schedule_id = selected_items[0].data(Qt.UserRole)

        asyncio.create_task(self._toggle_active(schedule_id))

    async def _toggle_active(self, schedule_id: str) -> None:
        """Toggle the active state of a schedule.

        Args:
            schedule_id: The ID of the schedule to toggle
        """
        if not self._history_manager:
            return

        try:
            schedule = await self._history_manager.get_schedule(schedule_id)
            if not schedule:
                return

            # Toggle the active state
            schedule.active = not schedule.active

            # Update the schedule
            await self._history_manager.update_schedule(schedule)

            # Refresh the UI
            await self._load_schedule_details(schedule_id)
            await self._load_schedules()

            # Show a status message
            status = "activated" if schedule.active else "deactivated"
            self._status_label.setText(f"Schedule {status} successfully")

        except Exception as e:
            self._logger.error(f"Failed to toggle schedule active state: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to toggle schedule: {str(e)}")

    def _run_schedule_now(self) -> None:
        """Run the selected schedule immediately."""
        selected_items = self._schedules_list.selectedItems()
        if not selected_items:
            return

        schedule_id = selected_items[0].data(Qt.UserRole)

        asyncio.create_task(self._run_now(schedule_id))

    async def _run_now(self, schedule_id: str) -> None:
        """Run a schedule immediately.

        Args:
            schedule_id: The ID of the schedule to run
        """
        if not self._history_manager:
            return

        try:
            self._status_label.setText("Executing schedule...")
            self._progress_bar.setVisible(True)
            self._run_now_button.setEnabled(False)

            # Get the queries
            queries = await self._plugin.get_saved_queries()

            # Execute the schedule
            await self._history_manager.execute_schedule_now(
                schedule_id=schedule_id,
                connector_manager=self._plugin,
                saved_queries=queries
            )

            # Refresh history
            await self._load_schedule_history(schedule_id)

            self._status_label.setText("Schedule executed successfully")
            self._progress_bar.setVisible(False)
            self._run_now_button.setEnabled(True)

        except Exception as e:
            self._logger.error(f"Failed to execute schedule: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            self._run_now_button.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Failed to execute schedule: {str(e)}")

    def _view_schedule_history_item(self, item: QListWidgetItem) -> None:
        """View a history entry from the schedule history list.

        Args:
            item: The list item that was clicked
        """
        entry = item.data(Qt.UserRole)
        if not entry:
            return

        asyncio.create_task(self._view_history_data(entry.snapshot_id))

    def _view_selected_history(self) -> None:
        """View the selected history entry from the history table."""
        selected_rows = self._history_table.selectedRows()
        if not selected_rows:
            selected_items = self._history_table.selectedItems()
            if not selected_items:
                return

            # Find the row of the selected item
            row = selected_items[0].row()
        else:
            row = selected_rows[0].row()

        # Get the snapshot ID from the last column
        snapshot_item = self._history_table.item(row, 4)
        if not snapshot_item:
            return

        snapshot_id = snapshot_item.text()
        asyncio.create_task(self._view_history_data(snapshot_id))

    def _on_history_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on a history table item.

        Args:
            item: The table item that was double-clicked
        """
        row = item.row()
        snapshot_item = self._history_table.item(row, 4)
        if not snapshot_item:
            return

        snapshot_id = snapshot_item.text()
        asyncio.create_task(self._view_history_data(snapshot_id))

    def _show_history_context_menu(self, position: QPoint) -> None:
        """Show context menu for history table.

        Args:
            position: The position where to show the menu
        """
        item = self._history_table.itemAt(position)
        if not item:
            return

        row = item.row()
        snapshot_item = self._history_table.item(row, 4)
        if not snapshot_item:
            return

        menu = QMenu(self)

        view_action = menu.addAction("View Data")
        view_action.triggered.connect(lambda: asyncio.create_task(
            self._view_history_data(snapshot_item.text())
        ))

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: asyncio.create_task(
            self._delete_history_data(snapshot_item.text())
        ))

        export_action = menu.addAction("Export")
        export_action.triggered.connect(lambda: asyncio.create_task(
            self._export_history_data(snapshot_item.text())
        ))

        menu.exec_(self._history_table.mapToGlobal(position))

    async def _view_history_data(self, snapshot_id: str) -> None:
        """View historical data for a snapshot.

        Args:
            snapshot_id: The ID of the snapshot to view
        """
        if not self._history_manager:
            return

        try:
            self._status_label.setText("Loading history data...")
            self._progress_bar.setVisible(True)

            # Get the history data
            history_data = await self._history_manager.get_history_data(snapshot_id)

            if not history_data:
                self._status_label.setText("No data found for this snapshot")
                self._progress_bar.setVisible(False)
                QMessageBox.information(self, "No Data", "No data found for this snapshot.")
                return

            # Show the data dialog
            dialog = HistoryDataDialog(self._plugin, self._logger, history_data, self)
            dialog.exec()

            self._status_label.setText("Ready")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to view history data: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to view history data: {str(e)}")

    async def _delete_history_data(self, snapshot_id: str) -> None:
        """Delete historical data for a snapshot.

        Args:
            snapshot_id: The ID of the snapshot to delete
        """
        if not self._history_manager:
            return

        try:
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                "Are you sure you want to delete this historical data snapshot?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            self._status_label.setText("Deleting history data...")
            self._progress_bar.setVisible(True)

            # Delete the data
            await self._history_manager.delete_history_data(snapshot_id)

            # Refresh the history table
            connection_id = self._history_connection_combo.currentData()
            if connection_id:
                await self._load_history_entries(connection_id)

            # Also refresh the schedule history if we're on the schedules tab
            if self._schedules_list.selectedItems():
                schedule_id = self._schedules_list.selectedItems()[0].data(Qt.UserRole)
                await self._load_schedule_history(schedule_id)

            self._status_label.setText("History data deleted successfully")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to delete history data: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to delete history data: {str(e)}")

    async def _export_history_data(self, snapshot_id: str) -> None:
        """Export historical data for a snapshot.

        Args:
            snapshot_id: The ID of the snapshot to export
        """
        if not self._history_manager:
            return

        try:
            self._status_label.setText("Loading history data...")
            self._progress_bar.setVisible(True)

            # Get the history data
            history_data = await self._history_manager.get_history_data(snapshot_id)

            if not history_data:
                self._status_label.setText("No data found for this snapshot")
                self._progress_bar.setVisible(False)
                QMessageBox.information(self, "No Data", "No data found for this snapshot.")
                return

            # Show file save dialog
            from PySide6.QtWidgets import QFileDialog
            import csv
            import json

            file_path, filter_used = QFileDialog.getSaveFileName(
                self,
                "Export Historical Data",
                "",
                "CSV Files (*.csv);;JSON Files (*.json);;All Files (*.*)"
            )

            if not file_path:
                self._status_label.setText("Export cancelled")
                self._progress_bar.setVisible(False)
                return

            data = history_data.get('data', [])

            if filter_used == "CSV Files (*.csv)" or file_path.lower().endswith('.csv'):
                if not file_path.lower().endswith('.csv'):
                    file_path += '.csv'

                # Get column headers
                if data:
                    headers = list(data[0].keys())

                    with open(file_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(data)

            elif filter_used == "JSON Files (*.json)" or file_path.lower().endswith('.json'):
                if not file_path.lower().endswith('.json'):
                    file_path += '.json'

                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

            self._status_label.setText(f"Data exported to {file_path}")
            self._progress_bar.setVisible(False)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Data exported to {file_path}"
            )

        except Exception as e:
            self._logger.error(f"Failed to export history data: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to export history data: {str(e)}")

    def _delete_selected_history(self) -> None:
        """Delete the selected history entry from the history table."""
        selected_rows = self._history_table.selectedRows()
        if not selected_rows:
            selected_items = self._history_table.selectedItems()
            if not selected_items:
                return

            # Find the row of the selected item
            row = selected_items[0].row()
        else:
            row = selected_rows[0].row()

        # Get the snapshot ID from the last column
        snapshot_item = self._history_table.item(row, 4)
        if not snapshot_item:
            return

        snapshot_id = snapshot_item.text()
        asyncio.create_task(self._delete_history_data(snapshot_id))

    def _export_selected_history(self) -> None:
        """Export the selected history entry from the history table."""
        selected_rows = self._history_table.selectedRows()
        if not selected_rows:
            selected_items = self._history_table.selectedItems()
            if not selected_items:
                return

            # Find the row of the selected item
            row = selected_items[0].row()
        else:
            row = selected_rows[0].row()

        # Get the snapshot ID from the last column
        snapshot_item = self._history_table.item(row, 4)
        if not snapshot_item:
            return

        snapshot_id = snapshot_item.text()
        asyncio.create_task(self._export_history_data(snapshot_id))

    def _apply_history_filter(self) -> None:
        """Apply filters to the history table."""
        connection_id = self._history_connection_combo.currentData()
        if connection_id:
            asyncio.create_task(self._load_history_entries(connection_id))