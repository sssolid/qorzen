"""
Field mapping tab for the Database Connector Plugin.

This module provides the field mapping tab UI for creating and managing
field mappings between database columns and standardized field names.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QDialog, QFormLayout,
    QDialogButtonBox, QFrame, QMenu, QInputDialog
)

from ..models import FieldMapping


class FieldMappingDialog(QDialog):
    """Dialog for creating and editing field mappings."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the field mapping dialog."""
        super().__init__(parent)

        self._connection_id: Optional[str] = None
        self._table_name: Optional[str] = None
        self._mappings: Dict[str, str] = {}

        # UI components
        self._connection_combo: Optional[QComboBox] = None
        self._table_combo: Optional[QComboBox] = None
        self._description_edit: Optional[QTextEdit] = None
        self._mappings_table: Optional[QTableWidget] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Field Mapping Editor")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Basic info
        info_group = QGroupBox("Mapping Information")
        info_layout = QFormLayout(info_group)

        # Connection selection
        self._connection_combo = QComboBox()
        self._connection_combo.currentTextChanged.connect(self._on_connection_changed)
        info_layout.addRow("Connection:", self._connection_combo)

        # Table selection
        self._table_combo = QComboBox()
        info_layout.addRow("Table:", self._table_combo)

        # Description
        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(80)
        self._description_edit.setPlaceholderText("Enter mapping description (optional)")
        info_layout.addRow("Description:", self._description_edit)

        layout.addWidget(info_group)

        # Mappings table
        mappings_group = QGroupBox("Field Mappings")
        mappings_layout = QVBoxLayout(mappings_group)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        add_button = QPushButton("Add Mapping")
        add_button.clicked.connect(self._add_mapping)
        toolbar_layout.addWidget(add_button)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self._remove_mapping)
        toolbar_layout.addWidget(remove_button)

        auto_map_button = QPushButton("Auto Map")
        auto_map_button.clicked.connect(self._auto_map_fields)
        toolbar_layout.addWidget(auto_map_button)

        toolbar_layout.addStretch()

        mappings_layout.addLayout(toolbar_layout)

        # Mappings table
        self._mappings_table = QTableWidget()
        self._mappings_table.setColumnCount(2)
        self._mappings_table.setHorizontalHeaderLabels(["Original Field", "Mapped Field"])

        header = self._mappings_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        mappings_layout.addWidget(self._mappings_table)

        layout.addWidget(mappings_group)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    async def set_connections(self, connections: List[Dict[str, Any]]) -> None:
        """Set available connections."""
        self._connection_combo.clear()
        self._connection_combo.addItem("-- Select Connection --", None)

        for connection in connections:
            self._connection_combo.addItem(connection.name, connection.id)

    def _on_connection_changed(self) -> None:
        """Handle connection selection change."""
        # This would need to be implemented to load tables for the selected connection
        pass

    def _add_mapping(self) -> None:
        """Add a new field mapping."""
        original_field, ok = QInputDialog.getText(
            self, "Add Mapping", "Original field name:"
        )

        if not ok or not original_field.strip():
            return

        mapped_field, ok = QInputDialog.getText(
            self, "Add Mapping", "Mapped field name:"
        )

        if not ok or not mapped_field.strip():
            return

        self._add_mapping_row(original_field.strip(), mapped_field.strip())

    def _add_mapping_row(self, original_field: str, mapped_field: str) -> None:
        """Add a mapping row to the table."""
        row = self._mappings_table.rowCount()
        self._mappings_table.insertRow(row)

        original_item = QTableWidgetItem(original_field)
        mapped_item = QTableWidgetItem(mapped_field)

        self._mappings_table.setItem(row, 0, original_item)
        self._mappings_table.setItem(row, 1, mapped_item)

    def _remove_mapping(self) -> None:
        """Remove selected mapping."""
        current_row = self._mappings_table.currentRow()
        if current_row >= 0:
            self._mappings_table.removeRow(current_row)

    def _auto_map_fields(self) -> None:
        """Auto-map fields using standardization rules."""
        # This would implement automatic field mapping based on common patterns
        QMessageBox.information(
            self,
            "Auto Map",
            "Auto-mapping would apply standardization rules to convert field names"
        )

    def get_mapping_data(self) -> Tuple[str, str, str, Dict[str, str]]:
        """Get the mapping data from the dialog."""
        connection_id = self._connection_combo.currentData()
        table_name = self._table_combo.currentText()
        description = self._description_edit.toPlainText().strip()

        mappings = {}
        for row in range(self._mappings_table.rowCount()):
            original_item = self._mappings_table.item(row, 0)
            mapped_item = self._mappings_table.item(row, 1)

            if original_item and mapped_item:
                original = original_item.text().strip()
                mapped = mapped_item.text().strip()
                if original and mapped:
                    mappings[original] = mapped

        return connection_id, table_name, description, mappings


class FieldMappingTab(QWidget):
    """
    Field mapping tab for managing database field mappings.

    Provides functionality for:
    - Creating field mappings between database columns and standard names
    - Viewing and editing existing mappings
    - Applying mappings to query results
    - Bulk mapping operations
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
        Initialize the field mapping tab.

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
        self._connection_combo: Optional[QComboBox] = None
        self._mappings_table: Optional[QTableWidget] = None
        self._tables_tree: Optional[QTreeWidget] = None
        self._mapping_preview: Optional[QTextEdit] = None

        # State
        self._current_mappings: List[Dict[str, Any]] = []
        self._connections: List[Dict[str, Any]] = []

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (tables and mappings list)
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        # Right panel (mapping details)
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter proportions
        main_splitter.setSizes([400, 600])

        layout.addWidget(main_splitter)

    def _create_toolbar(self) -> QFrame:
        """Create the toolbar."""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(toolbar)

        # Connection filter
        layout.addWidget(QLabel("Connection:"))

        self._connection_combo = QComboBox()
        self._connection_combo.addItem("All Connections", None)
        self._connection_combo.currentTextChanged.connect(self._on_connection_filter_changed)
        layout.addWidget(self._connection_combo)

        layout.addStretch()

        # Action buttons
        new_button = QPushButton("New Mapping")
        new_button.clicked.connect(self._create_mapping)
        layout.addWidget(new_button)

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self._edit_mapping)
        layout.addWidget(edit_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._delete_mapping)
        layout.addWidget(delete_button)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: asyncio.create_task(self.refresh()))
        layout.addWidget(refresh_button)

        return toolbar

    def _create_left_panel(self) -> QWidget:
        """Create the left panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Database schema section
        schema_group = QGroupBox("Database Tables")
        schema_layout = QVBoxLayout(schema_group)

        self._tables_tree = QTreeWidget()
        self._tables_tree.setHeaderLabel("Tables and Columns")
        self._tables_tree.itemDoubleClicked.connect(self._on_table_double_clicked)
        schema_layout.addWidget(self._tables_tree)

        layout.addWidget(schema_group)

        # Existing mappings section
        mappings_group = QGroupBox("Existing Mappings")
        mappings_layout = QVBoxLayout(mappings_group)

        self._mappings_table = QTableWidget()
        self._mappings_table.setColumnCount(3)
        self._mappings_table.setHorizontalHeaderLabels(["Connection", "Table", "Fields"])
        self._mappings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._mappings_table.setAlternatingRowColors(True)
        self._mappings_table.itemSelectionChanged.connect(self._on_mapping_selection_changed)
        self._mappings_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._mappings_table.customContextMenuRequested.connect(self._show_mapping_context_menu)

        # Configure headers
        header = self._mappings_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        mappings_layout.addWidget(self._mappings_table)

        layout.addWidget(mappings_group)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Mapping preview
        preview_group = QGroupBox("Mapping Preview")
        preview_layout = QVBoxLayout(preview_group)

        self._mapping_preview = QTextEdit()
        self._mapping_preview.setReadOnly(True)
        self._mapping_preview.setPlaceholderText("Select a mapping to view details")
        preview_layout.addWidget(self._mapping_preview)

        layout.addWidget(preview_group)

        return panel

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Load initial data
        asyncio.create_task(self.refresh())

    async def refresh(self) -> None:
        """Refresh all data in the tab."""
        try:
            self.operation_started.emit("Refreshing field mappings...")

            # Load connections
            await self._load_connections()

            # Load mappings
            await self._load_mappings()

            # Load schema for selected connection
            await self._load_schema()

            self.operation_finished.emit()
            self.status_changed.emit("Field mappings refreshed")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to refresh field mapping tab: {e}")
            self._show_error("Refresh Error", f"Failed to refresh data: {e}")

    async def _load_connections(self) -> None:
        """Load available connections."""
        try:
            self._connections = await self._plugin.get_connections()

            # Update connection filter
            current_text = self._connection_combo.currentText()
            self._connection_combo.clear()
            self._connection_combo.addItem("All Connections", None)

            for connection in self._connections:
                self._connection_combo.addItem(connection.name, connection.id)

            # Restore selection
            if current_text:
                index = self._connection_combo.findText(current_text)
                if index >= 0:
                    self._connection_combo.setCurrentIndex(index)

        except Exception as e:
            self._logger.error(f"Failed to load connections: {e}")

    async def _load_mappings(self) -> None:
        """Load field mappings."""
        try:
            connection_filter = self._connection_combo.currentData()

            if connection_filter:
                # Get connection name for the ID
                connection_name = None
                for conn in self._connections:
                    if conn.id == connection_filter:
                        connection_name = conn.name
                        break

                if connection_name:
                    mappings = await self._plugin.get_field_mappings(connection_name)
                else:
                    mappings = []
            else:
                mappings = await self._plugin.get_field_mappings()

            self._current_mappings = mappings
            self._populate_mappings_table()

        except Exception as e:
            self._logger.error(f"Failed to load mappings: {e}")

    def _populate_mappings_table(self) -> None:
        """Populate the mappings table."""
        try:
            self._mappings_table.setRowCount(len(self._current_mappings))

            for row, mapping in enumerate(self._current_mappings):
                # Connection
                connection_item = QTableWidgetItem(mapping.get('connection_id', 'Unknown'))
                connection_item.setFlags(connection_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._mappings_table.setItem(row, 0, connection_item)

                # Table
                table_item = QTableWidgetItem(mapping.get('table_name', 'Unknown'))
                table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._mappings_table.setItem(row, 1, table_item)

                # Field count
                field_count = len(mapping.get('mappings', {}))
                fields_item = QTableWidgetItem(f"{field_count} fields")
                fields_item.setFlags(fields_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._mappings_table.setItem(row, 2, fields_item)

                # Store mapping data
                connection_item.setData(Qt.ItemDataRole.UserRole, mapping)

        except Exception as e:
            self._logger.error(f"Failed to populate mappings table: {e}")

    async def _load_schema(self) -> None:
        """Load database schema for the selected connection."""
        try:
            connection_id = self._connection_combo.currentData()
            if not connection_id:
                self._tables_tree.clear()
                return

            tables = await self._plugin.get_tables(connection_id)

            self._tables_tree.clear()

            for table in tables:
                table_item = QTreeWidgetItem([table['name']])
                table_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "table",
                    "name": table['name'],
                    "connection_id": connection_id
                })

                # Add columns as children
                for column in table.get('columns', []):
                    column_text = f"{column['name']} ({column.get('type_name', 'UNKNOWN')})"
                    column_item = QTreeWidgetItem([column_text])
                    column_item.setData(0, Qt.ItemDataRole.UserRole, {
                        "type": "column",
                        "name": column['name'],
                        "table": table['name'],
                        "connection_id": connection_id
                    })
                    table_item.addChild(column_item)

                self._tables_tree.addTopLevelItem(table_item)

            self._tables_tree.expandAll()

        except Exception as e:
            self._logger.error(f"Failed to load schema: {e}")

    def _on_connection_filter_changed(self) -> None:
        """Handle connection filter change."""
        asyncio.create_task(self._load_mappings())
        asyncio.create_task(self._load_schema())

    def _on_table_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle table double-click to create mapping."""
        try:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data["type"] != "table":
                return

            # Create mapping for this table
            self._create_mapping_for_table(data["connection_id"], data["name"])

        except Exception as e:
            self._logger.error(f"Error handling table double-click: {e}")

    def _on_mapping_selection_changed(self) -> None:
        """Handle mapping selection change."""
        try:
            current_row = self._mappings_table.currentRow()
            if current_row < 0 or current_row >= len(self._current_mappings):
                self._mapping_preview.clear()
                return

            mapping = self._current_mappings[current_row]
            self._show_mapping_preview(mapping)

        except Exception as e:
            self._logger.error(f"Error handling mapping selection: {e}")

    def _show_mapping_preview(self, mapping: Dict[str, Any]) -> None:
        """Show mapping preview."""
        try:
            preview_parts = []

            # Basic info
            preview_parts.append(f"Connection: {mapping.get('connection_id', 'Unknown')}")
            preview_parts.append(f"Table: {mapping.get('table_name', 'Unknown')}")
            preview_parts.append(f"Description: {mapping.get('description', 'No description')}")
            preview_parts.append("")

            # Creation info
            if 'created_at' in mapping:
                preview_parts.append(f"Created: {mapping['created_at']}")
            if 'updated_at' in mapping:
                preview_parts.append(f"Updated: {mapping['updated_at']}")
            preview_parts.append("")

            # Field mappings
            mappings = mapping.get('mappings', {})
            if mappings:
                preview_parts.append("Field Mappings:")
                preview_parts.append("=" * 50)

                for original, mapped in mappings.items():
                    if original == mapped:
                        preview_parts.append(f"  {original} → (no change)")
                    else:
                        preview_parts.append(f"  {original} → {mapped}")
            else:
                preview_parts.append("No field mappings defined")

            self._mapping_preview.setPlainText('\n'.join(preview_parts))

        except Exception as e:
            self._logger.error(f"Failed to show mapping preview: {e}")

    def _create_mapping(self) -> None:
        """Create a new field mapping."""
        dialog = FieldMappingDialog(self)

        # Set available connections
        asyncio.create_task(dialog.set_connections(self._connections))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            connection_id, table_name, description, mappings = dialog.get_mapping_data()

            if not connection_id or not table_name or not mappings:
                self._show_warning("Invalid Data", "Please provide connection, table, and at least one mapping")
                return

            asyncio.create_task(self._create_mapping_async(connection_id, table_name, mappings, description))

    def _create_mapping_for_table(self, connection_id: str, table_name: str) -> None:
        """Create a mapping for a specific table."""
        dialog = FieldMappingDialog(self)

        # Pre-populate with table info
        asyncio.create_task(dialog.set_connections(self._connections))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            conn_id, tbl_name, description, mappings = dialog.get_mapping_data()

            # Use the pre-selected values if not overridden
            final_connection_id = conn_id or connection_id
            final_table_name = tbl_name or table_name

            if not mappings:
                self._show_warning("No Mappings", "Please provide at least one field mapping")
                return

            asyncio.create_task(
                self._create_mapping_async(final_connection_id, final_table_name, mappings, description))

    async def _create_mapping_async(
            self,
            connection_id: str,
            table_name: str,
            mappings: Dict[str, str],
            description: Optional[str] = None
    ) -> None:
        """Create mapping asynchronously."""
        try:
            self.operation_started.emit("Creating field mapping...")

            await self._plugin.create_field_mapping(
                connection_id=connection_id,
                table_name=table_name,
                mappings=mappings,
                description=description
            )

            await self._load_mappings()

            self.operation_finished.emit()
            self.status_changed.emit(f"Created mapping for {table_name}")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to create mapping: {e}")
            self._show_error("Create Error", f"Failed to create mapping: {e}")

    def _edit_mapping(self) -> None:
        """Edit the selected mapping."""
        current_row = self._mappings_table.currentRow()
        if current_row < 0:
            self._show_warning("No Selection", "Please select a mapping to edit")
            return

        mapping = self._current_mappings[current_row]

        # For now, show details - full editing would require more complex dialog
        self._show_info("Edit Mapping", "Mapping editing would be implemented here")

    def _delete_mapping(self) -> None:
        """Delete the selected mapping."""
        current_row = self._mappings_table.currentRow()
        if current_row < 0:
            self._show_warning("No Selection", "Please select a mapping to delete")
            return

        mapping = self._current_mappings[current_row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the mapping for table '{mapping.get('table_name', 'Unknown')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            mapping_id = mapping.get('id')
            if mapping_id:
                asyncio.create_task(self._delete_mapping_async(mapping_id))

    async def _delete_mapping_async(self, mapping_id: str) -> None:
        """Delete mapping asynchronously."""
        try:
            self.operation_started.emit("Deleting field mapping...")

            success = await self._plugin.delete_field_mapping(mapping_id)

            if success:
                await self._load_mappings()
                self.status_changed.emit("Mapping deleted")
            else:
                self._show_error("Delete Error", "Failed to delete mapping")

            self.operation_finished.emit()

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to delete mapping: {e}")
            self._show_error("Delete Error", f"Failed to delete mapping: {e}")

    def _show_mapping_context_menu(self, position) -> None:
        """Show context menu for mappings table."""
        item = self._mappings_table.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("Edit Mapping")
        edit_action.triggered.connect(self._edit_mapping)

        delete_action = menu.addAction("Delete Mapping")
        delete_action.triggered.connect(self._delete_mapping)

        menu.addSeparator()

        duplicate_action = menu.addAction("Duplicate Mapping")
        duplicate_action.triggered.connect(self._duplicate_mapping)

        menu.exec(self._mappings_table.mapToGlobal(position))

    def _duplicate_mapping(self) -> None:
        """Duplicate the selected mapping."""
        current_row = self._mappings_table.currentRow()
        if current_row < 0:
            return

        mapping = self._current_mappings[current_row]

        # This would create a copy of the mapping
        self._show_info("Duplicate", "Mapping duplication would be implemented here")

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
            # Clear data to free memory
            self._current_mappings.clear()
            self._connections.clear()
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")