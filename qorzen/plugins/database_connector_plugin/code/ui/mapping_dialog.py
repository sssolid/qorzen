# processed_project/qorzen_stripped/plugins/database_connector_plugin/code/ui/mapping_dialog.py
from __future__ import annotations

import uuid

'''
Field mapping dialog for the Database Connector Plugin.

This module provides a dialog for creating and editing field mappings between
database tables and standardized field names for consistent data access.
'''
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout,
    QLineEdit, QDialogButtonBox, QMessageBox, QCheckBox, QProgressBar, QWidget
)

from ..models import FieldMapping, ColumnMetadata, TableMetadata
from ..utils.mapping import standardize_field_name


async def load_tables_optimized(connector: Any, logger: Any, progress_callback: Optional[callable] = None) -> List[str]:
    """Load tables optimized for large databases."""
    try:
        # Try different approaches to get table count efficiently
        table_count = None
        try:
            # Try generic query that works on many databases
            result = await connector.execute_query(
                "SELECT COUNT(*) AS table_count FROM information_schema.tables "
                "WHERE table_type IN ('BASE TABLE', 'TABLE', 'VIEW')"
            )
            if result.records and 'table_count' in result.records[0]:
                table_count = result.records[0]['table_count']
        except Exception:
            pass

        # Log the table count if we found it
        if table_count:
            logger.debug(f"Database has approximately {table_count} tables")

        # Let's load all tables - for very large databases, we might want to
        # implement pagination or filtering here
        tables = await connector.get_tables()
        table_names = [table.name for table in tables]
        table_names.sort(key=str.lower)

        return table_names

    except Exception as e:
        logger.error(f"Failed to load tables: {str(e)}")
        return []


class FieldMappingDialog(QDialog):
    """Dialog for creating and editing field mappings."""

    def __init__(
            self,
            plugin: Any,
            logger: Any,
            connection_id: str,
            parent: Optional[QWidget] = None,
            mapping: Optional[FieldMapping] = None
    ) -> None:
        """Initialize the field mapping dialog.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            connection_id: The current database connection ID
            parent: The parent widget
            mapping: Optional existing mapping to edit
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._connection_id = connection_id
        self._mapping = mapping
        self._tables: List[TableMetadata] = []
        self._columns: List[ColumnMetadata] = []

        self._init_ui()

        # Set window title
        if mapping:
            self.setWindowTitle(f"Edit Field Mapping - {mapping.table_name}")
        else:
            self.setWindowTitle("Create New Field Mapping")

        # Load tables
        self._load_tables()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # Add search functionality above the table combo
        search_layout = QHBoxLayout()
        search_label = QLabel("Search tables:")
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to filter tables...")
        self._search_button = QPushButton("Find")
        self._search_button.clicked.connect(self._search_tables)
        self._search_input.returnPressed.connect(self._search_tables)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_input, 1)
        search_layout.addWidget(self._search_button)

        # Information section
        info_group = QGroupBox("Mapping Information")
        info_form = QFormLayout(info_group)

        self._table_combo = QComboBox()
        form_layout = self._table_combo.parent().layout()
        if form_layout:
            # Insert search layout at the beginning
            form_layout.insertRow(0, '', QWidget())  # Add a placeholder
            form_layout_item = form_layout.itemAt(0, QFormLayout.FieldRole)
            if form_layout_item and form_layout_item.widget():
                search_widget = QWidget()
                search_widget.setLayout(search_layout)
                form_layout.setWidget(0, QFormLayout.FieldRole, search_widget)

        self._table_combo.setMinimumWidth(300)
        self._table_combo.currentIndexChanged.connect(self._on_table_selected)

        self._description_edit = QLineEdit()
        self._description_edit.setPlaceholderText("Optional description for this mapping")

        info_form.addRow("Table:", self._table_combo)
        info_form.addRow("Description:", self._description_edit)

        layout.addWidget(info_group)

        # Mapping options
        options_group = QGroupBox("Mapping Options")
        options_layout = QVBoxLayout(options_group)

        options_form = QFormLayout()

        self._standardize_check = QCheckBox("Standardize field names")
        self._standardize_check.setChecked(True)
        self._standardize_check.stateChanged.connect(self._update_mappings)

        self._lowercase_check = QCheckBox("Convert to lowercase")
        self._lowercase_check.setChecked(True)
        self._lowercase_check.stateChanged.connect(self._update_mappings)

        self._remove_spaces_check = QCheckBox("Replace spaces with underscores")
        self._remove_spaces_check.setChecked(True)
        self._remove_spaces_check.stateChanged.connect(self._update_mappings)

        self._remove_special_check = QCheckBox("Remove special characters")
        self._remove_special_check.setChecked(True)
        self._remove_special_check.stateChanged.connect(self._update_mappings)

        self._snake_case_check = QCheckBox("Convert camelCase to snake_case")
        self._snake_case_check.setChecked(True)
        self._snake_case_check.stateChanged.connect(self._update_mappings)

        options_form.addRow("", self._standardize_check)
        options_form.addRow("", self._lowercase_check)
        options_form.addRow("", self._remove_spaces_check)
        options_form.addRow("", self._remove_special_check)
        options_form.addRow("", self._snake_case_check)

        options_layout.addLayout(options_form)

        # Auto-generate and reset buttons
        buttons_layout = QHBoxLayout()

        self._auto_button = QPushButton("Auto-Generate Mappings")
        self._auto_button.clicked.connect(self._auto_generate_mappings)

        self._reset_button = QPushButton("Reset to Original")
        self._reset_button.clicked.connect(self._reset_mappings)

        buttons_layout.addWidget(self._auto_button)
        buttons_layout.addWidget(self._reset_button)
        buttons_layout.addStretch()

        options_layout.addLayout(buttons_layout)

        layout.addWidget(options_group)

        # Fields mapping table
        self._fields_table = QTableWidget()
        self._fields_table.setColumnCount(3)
        self._fields_table.setHorizontalHeaderLabels(["Original Field", "Mapped Field", "Type"])
        self._fields_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._fields_table.setAlternatingRowColors(True)

        layout.addWidget(self._fields_table, 1)  # Give the table more vertical space

        # Status line
        status_layout = QHBoxLayout()
        self._status_label = QLabel("")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate progress
        self._progress_bar.setVisible(False)

        status_layout.addWidget(self._status_label)
        status_layout.addWidget(self._progress_bar)

        layout.addLayout(status_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def _load_tables(self) -> None:
        """Load database tables."""
        self._status_label.setText("Loading tables...")
        self._progress_bar.setVisible(True)
        self._table_combo.setEnabled(False)

        asyncio.create_task(self._async_load_tables())

    async def _async_load_tables(self) -> None:
        try:
            connector = await self._plugin.get_connector(self._connection_id)

            # Use optimized table loading
            self._tables = await load_tables_optimized(connector, self._logger)

            # Update UI on main thread
            self._table_combo.clear()
            self._table_combo.addItem('Select a table...', None)

            for table_name in self._tables:
                self._table_combo.addItem(table_name, table_name)

            if self._mapping:
                for i in range(self._table_combo.count()):
                    if self._table_combo.itemData(i) == self._mapping.table_name:
                        self._table_combo.setCurrentIndex(i)
                        self._description_edit.setText(self._mapping.description or '')
                        break

            self._status_label.setText(f'Loaded {len(self._tables)} tables')
            self._progress_bar.setVisible(False)
            self._table_combo.setEnabled(True)

            # If table search is enabled, make sure it's functional
            if hasattr(self, '_search_input'):
                self._search_input.setEnabled(True)
            if hasattr(self, '_search_button'):
                self._search_button.setEnabled(True)

        except Exception as e:
            self._logger.error(f'Failed to load tables: {str(e)}')
            self._status_label.setText(f'Error: {str(e)}')
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, 'Error', f'Failed to load tables: {str(e)}')

    def _search_tables(self) -> None:
        """Search and filter tables in the combo box."""
        search_text = self._search_input.text().strip().lower()
        if not search_text:
            # If search is empty, just show the dropdown
            self._table_combo.showPopup()
            return

        # Filter items in the combo box
        filtered_count = 0
        for i in range(1, self._table_combo.count()):  # Skip the first "Select a table" item
            table_name = self._table_combo.itemText(i).lower()
            if search_text in table_name:
                self._table_combo.setItemData(i, True, Qt.UserRole + 1)
                filtered_count += 1
            else:
                self._table_combo.setItemData(i, False, Qt.UserRole + 1)

        if filtered_count > 0:
            # Show the dropdown with filtered results
            self._table_combo.showPopup()
        else:
            QMessageBox.information(
                self,
                "No Matches",
                f"No tables found matching '{search_text}'"
            )

    def _on_table_selected(self, index: int) -> None:
        """Handle table selection change.

        Args:
            index: The index of the selected item
        """
        table_name = self._table_combo.itemData(index)
        if not table_name:
            self._fields_table.setRowCount(0)
            return

        self._status_label.setText(f"Loading columns for {table_name}...")
        self._progress_bar.setVisible(True)

        asyncio.create_task(self._async_load_columns(table_name))

    async def _async_load_columns(self, table_name: str) -> None:
        """Asynchronously load columns for the selected table.

        Args:
            table_name: The name of the table to load columns for
        """
        try:
            connector = await self._plugin.get_connector(self._connection_id)
            self._columns = await connector.get_table_columns(table_name)

            # Sort columns by name
            self._columns.sort(key=lambda c: c.name.lower())

            # Update the field mapping table
            self._populate_fields_table()

            self._status_label.setText(f"Loaded {len(self._columns)} columns")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to load columns: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to load columns: {str(e)}")

    def _populate_fields_table(self) -> None:
        """Populate the fields table with column data."""
        self._fields_table.clearContents()
        self._fields_table.setRowCount(len(self._columns))

        # Get existing mappings if editing
        existing_mappings = {}
        if self._mapping and self._mapping.table_name == self._table_combo.currentData():
            existing_mappings = self._mapping.mappings

        for i, column in enumerate(self._columns):
            # Original field name
            original_item = QTableWidgetItem(column.name)
            original_item.setFlags(original_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable
            self._fields_table.setItem(i, 0, original_item)

            # Mapped field name (use existing mapping or generate a new one)
            mapped_name = ""
            if column.name in existing_mappings:
                mapped_name = existing_mappings[column.name]
            else:
                mapped_name = self._generate_mapped_name(column.name)

            mapped_item = QTableWidgetItem(mapped_name)
            mapped_item.setFlags(mapped_item.flags() | Qt.ItemIsEditable)  # Make editable
            self._fields_table.setItem(i, 1, mapped_item)

            # Column type
            type_info = f"{column.type_name}"
            if column.precision > 0 or column.scale > 0:
                type_info += f" ({column.precision}"
                if column.scale > 0:
                    type_info += f",{column.scale}"
                type_info += ")"

            type_item = QTableWidgetItem(type_info)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)  # Make non-editable
            self._fields_table.setItem(i, 2, type_item)

        self._fields_table.resizeColumnsToContents()

    def _generate_mapped_name(self, field_name: str) -> str:
        """Generate a standardized field name based on the options selected.

        Args:
            field_name: The original field name

        Returns:
            The standardized field name
        """
        if not self._standardize_check.isChecked():
            return field_name

        import re

        result = field_name

        # Remove special characters if selected
        if self._remove_special_check.isChecked():
            result = re.sub(r'[^\w\s]', '', result)

        # Convert camelCase to snake_case if selected
        if self._snake_case_check.isChecked():
            result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', result)

        # Replace spaces with underscores if selected
        if self._remove_spaces_check.isChecked():
            result = re.sub(r'\s+', '_', result)

        # Convert to lowercase if selected
        if self._lowercase_check.isChecked():
            result = result.lower()

        # Clean up multiple underscores
        result = re.sub(r'_+', '_', result)
        result = result.strip('_')

        return result

    def _update_mappings(self) -> None:
        """Update the mapped field names based on the current options."""
        if self._standardize_check.isChecked():
            self._lowercase_check.setEnabled(True)
            self._remove_spaces_check.setEnabled(True)
            self._remove_special_check.setEnabled(True)
            self._snake_case_check.setEnabled(True)
        else:
            self._lowercase_check.setEnabled(False)
            self._remove_spaces_check.setEnabled(False)
            self._remove_special_check.setEnabled(False)
            self._snake_case_check.setEnabled(False)

        # Don't update if no table is selected
        if self._table_combo.currentData() is None:
            return

        self._auto_generate_mappings()

    def _auto_generate_mappings(self) -> None:
        """Auto-generate field mappings based on the current options."""
        for i in range(self._fields_table.rowCount()):
            original_item = self._fields_table.item(i, 0)
            if not original_item:
                continue

            original_name = original_item.text()
            mapped_name = self._generate_mapped_name(original_name)

            mapped_item = QTableWidgetItem(mapped_name)
            mapped_item.setFlags(mapped_item.flags() | Qt.ItemIsEditable)  # Make editable
            self._fields_table.setItem(i, 1, mapped_item)

    def _reset_mappings(self) -> None:
        """Reset all field mappings to the original field names."""
        for i in range(self._fields_table.rowCount()):
            original_item = self._fields_table.item(i, 0)
            if not original_item:
                continue

            original_name = original_item.text()

            mapped_item = QTableWidgetItem(original_name)
            mapped_item.setFlags(mapped_item.flags() | Qt.ItemIsEditable)  # Make editable
            self._fields_table.setItem(i, 1, mapped_item)

    def get_mapping(self) -> FieldMapping:
        """Get the field mapping created or edited in this dialog.

        Returns:
            The field mapping
        """
        table_name = self._table_combo.currentData()
        if not table_name:
            raise ValueError("No table selected")

        mappings = {}
        for i in range(self._fields_table.rowCount()):
            original_item = self._fields_table.item(i, 0)
            mapped_item = self._fields_table.item(i, 1)

            if original_item and mapped_item:
                original_name = original_item.text()
                mapped_name = mapped_item.text().strip()

                # Skip if mapped name is empty
                if not mapped_name:
                    continue

                mappings[original_name] = mapped_name

        # Use existing mapping ID if editing, or generate a new one
        mapping_id = self._mapping.id if self._mapping else str(uuid.uuid4())

        return FieldMapping(
            id=mapping_id,
            connection_id=self._connection_id,
            table_name=table_name,
            description=self._description_edit.text().strip() or None,
            mappings=mappings
        )

    def accept(self) -> None:
        """Handle dialog acceptance."""
        try:
            table_name = self._table_combo.currentData()
            if not table_name:
                QMessageBox.warning(self, "No Table Selected", "Please select a table.")
                return

            # Check for empty mappings
            has_mappings = False
            for i in range(self._fields_table.rowCount()):
                mapped_item = self._fields_table.item(i, 1)
                if mapped_item and mapped_item.text().strip():
                    has_mappings = True
                    break

            if not has_mappings:
                QMessageBox.warning(self, "No Mappings", "Please define at least one field mapping.")
                return

            # Check for empty mapped names
            for i in range(self._fields_table.rowCount()):
                original_item = self._fields_table.item(i, 0)
                mapped_item = self._fields_table.item(i, 1)

                if original_item and mapped_item:
                    original_name = original_item.text()
                    mapped_name = mapped_item.text().strip()

                    if mapped_name and not mapped_name.strip():
                        QMessageBox.warning(
                            self,
                            "Empty Mapped Name",
                            f"The mapped name for field '{original_name}' cannot be empty."
                        )
                        return

            super().accept()

        except Exception as e:
            self._logger.error(f"Error in dialog accept: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")