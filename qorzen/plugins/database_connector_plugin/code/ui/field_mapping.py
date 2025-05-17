# processed_project/qorzen_stripped/plugins/database_connector_plugin/code/ui/field_mapping.py
from __future__ import annotations

'''
Field mapping UI for the Database Connector Plugin.

This module provides a user interface for creating and managing field mappings
between database tables and standardized field names, enabling consistent data access.
'''
import asyncio
import uuid
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QComboBox, QListWidget, QListWidgetItem, QSplitter,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                               QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox,
                               QMessageBox, QInputDialog, QGroupBox, QMenu, QToolButton,
                               QRadioButton, QButtonGroup, QTabWidget)

from ..models import FieldMapping, BaseConnectionConfig, TableMetadata, ColumnMetadata
from ..utils.mapping import standardize_field_name, create_mapping_from_fields
from .mapping_dialog import FieldMappingDialog


class FieldMappingWidget(QWidget):
    """Widget for managing field mappings between database tables and standardized field names."""

    mappingChanged = Signal(str)

    def __init__(self, plugin: Any, logger: Any, parent: Optional[QWidget] = None) -> None:
        """Initialize the field mapping widget.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            parent: The parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._current_connection_id: Optional[str] = None
        self._current_mapping_id: Optional[str] = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Connection selection area
        conn_layout = QHBoxLayout()
        conn_label = QLabel("Connection:")
        self._connection_combo = QComboBox()
        self._connection_combo.setMinimumWidth(200)
        self._connection_combo.currentIndexChanged.connect(self._on_connection_selected)

        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.setFixedWidth(100)
        self._refresh_button.clicked.connect(self._refresh_mappings)

        conn_layout.addWidget(conn_label)
        conn_layout.addWidget(self._connection_combo)
        conn_layout.addWidget(self._refresh_button)
        conn_layout.addStretch()

        main_layout.addLayout(conn_layout)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Mappings list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        mapping_label = QLabel("Field Mappings")
        mapping_label.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(mapping_label)

        self._mappings_list = QListWidget()
        self._mappings_list.itemSelectionChanged.connect(self._on_mapping_selected)
        left_layout.addWidget(self._mappings_list)

        # Mapping actions
        mapping_actions = QHBoxLayout()
        self._new_mapping_button = QPushButton("New")
        self._new_mapping_button.clicked.connect(self._create_new_mapping)

        self._edit_mapping_button = QPushButton("Edit")
        self._edit_mapping_button.clicked.connect(self._edit_current_mapping)
        self._edit_mapping_button.setEnabled(False)

        self._delete_mapping_button = QPushButton("Delete")
        self._delete_mapping_button.clicked.connect(self._delete_current_mapping)
        self._delete_mapping_button.setEnabled(False)

        mapping_actions.addWidget(self._new_mapping_button)
        mapping_actions.addWidget(self._edit_mapping_button)
        mapping_actions.addWidget(self._delete_mapping_button)

        left_layout.addLayout(mapping_actions)

        splitter.addWidget(left_widget)

        # Right panel - Mapping details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        details_label = QLabel("Mapping Details")
        details_label.setFont(QFont("Arial", 10, QFont.Bold))
        right_layout.addWidget(details_label)

        # Mapping info section
        info_group = QGroupBox("Information")
        info_layout = QFormLayout(info_group)

        self._table_name_label = QLabel("")
        self._description_label = QLabel("")
        self._fields_count_label = QLabel("")
        self._created_at_label = QLabel("")
        self._updated_at_label = QLabel("")

        info_layout.addRow("Table:", self._table_name_label)
        info_layout.addRow("Description:", self._description_label)
        info_layout.addRow("Fields:", self._fields_count_label)
        info_layout.addRow("Created:", self._created_at_label)
        info_layout.addRow("Updated:", self._updated_at_label)

        right_layout.addWidget(info_group)

        # Mapping fields table
        self._fields_table = QTableWidget()
        self._fields_table.setColumnCount(2)
        self._fields_table.setHorizontalHeaderLabels(["Original Field", "Mapped Field"])
        self._fields_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._fields_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._fields_table.setAlternatingRowColors(True)
        self._fields_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        right_layout.addWidget(self._fields_table)

        # Actions section
        actions_layout = QHBoxLayout()

        self._export_button = QPushButton("Export Mapping")
        self._export_button.clicked.connect(self._export_mapping)
        self._export_button.setEnabled(False)

        self._import_button = QPushButton("Import Mapping")
        self._import_button.clicked.connect(self._import_mapping)

        self._apply_button = QPushButton("Use in Query")
        self._apply_button.clicked.connect(self._apply_mapping_to_query)
        self._apply_button.setEnabled(False)

        actions_layout.addWidget(self._export_button)
        actions_layout.addWidget(self._import_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self._apply_button)

        right_layout.addLayout(actions_layout)

        splitter.addWidget(right_widget)

        # Set initial splitter sizes
        splitter.setSizes([200, 400])

        main_layout.addWidget(splitter)

    def set_connection_status(self, connection_id: str, connected: bool) -> None:
        """Update the UI based on connection status changes.

        Args:
            connection_id: The connection ID
            connected: Whether the connection is active
        """
        if connection_id == self._current_connection_id:
            self._new_mapping_button.setEnabled(connected)
            if not connected:
                self._clear_mapping_details()
                self._edit_mapping_button.setEnabled(False)
                self._delete_mapping_button.setEnabled(False)
                self._export_button.setEnabled(False)
                self._apply_button.setEnabled(False)
                self._mappings_list.clear()

    async def refresh(self) -> None:
        """Refresh the field mappings list."""
        await self._load_connections()
        if self._current_connection_id:
            await self._load_mappings()

    async def _load_connections(self) -> None:
        """Load available database connections."""
        try:
            connections = await self._plugin.get_connections()
            current_id = self._connection_combo.currentData()

            self._connection_combo.clear()
            self._connection_combo.addItem("Select a connection...", None)

            for conn_id, conn in sorted(connections.items(), key=lambda x: x[1].name.lower()):
                self._connection_combo.addItem(conn.name, conn_id)

            if current_id:
                for i in range(self._connection_combo.count()):
                    if self._connection_combo.itemData(i) == current_id:
                        self._connection_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f"Failed to load connections: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load connections: {str(e)}")

    async def _load_mappings(self) -> None:
        """Load field mappings for the current connection."""
        if not self._current_connection_id:
            return

        try:
            mappings = await self._plugin.get_field_mappings(self._current_connection_id)

            self._mappings_list.clear()

            for mapping_id, mapping in sorted(mappings.items(), key=lambda x: x[1].table_name.lower()):
                item_text = f"{mapping.table_name}"
                if mapping.description:
                    item_text += f" - {mapping.description}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, mapping_id)
                self._mappings_list.addItem(item)

            # Restore selection if possible
            if self._current_mapping_id:
                for i in range(self._mappings_list.count()):
                    item = self._mappings_list.item(i)
                    if item and item.data(Qt.UserRole) == self._current_mapping_id:
                        self._mappings_list.setCurrentItem(item)
                        break

        except Exception as e:
            self._logger.error(f"Failed to load mappings: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load mappings: {str(e)}")

    def _on_connection_selected(self, index: int) -> None:
        """Handle connection selection change.

        Args:
            index: The selected index in the combobox
        """
        connection_id = self._connection_combo.itemData(index)
        self._current_connection_id = connection_id

        self._clear_mapping_details()
        self._mappings_list.clear()

        # Check if connection is active
        is_connected = False
        if connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[connection_id]
            is_connected = connector.is_connected

        self._new_mapping_button.setEnabled(is_connected)

        if connection_id and is_connected:
            asyncio.create_task(self._load_mappings())

    def _on_mapping_selected(self) -> None:
        """Handle mapping selection change."""
        selected_items = self._mappings_list.selectedItems()

        if not selected_items:
            self._clear_mapping_details()
            self._current_mapping_id = None
            self._edit_mapping_button.setEnabled(False)
            self._delete_mapping_button.setEnabled(False)
            self._export_button.setEnabled(False)
            self._apply_button.setEnabled(False)
            return

        mapping_id = selected_items[0].data(Qt.UserRole)
        self._current_mapping_id = mapping_id

        self._edit_mapping_button.setEnabled(True)
        self._delete_mapping_button.setEnabled(True)
        self._export_button.setEnabled(True)
        self._apply_button.setEnabled(True)

        asyncio.create_task(self._load_mapping_details(mapping_id))

    async def _load_mapping_details(self, mapping_id: str) -> None:
        """Load and display mapping details.

        Args:
            mapping_id: The ID of the mapping to display
        """
        try:
            mapping = await self._plugin.get_field_mapping(mapping_id)
            if not mapping:
                self._clear_mapping_details()
                return

            # Update information section
            self._table_name_label.setText(mapping.table_name)
            self._description_label.setText(mapping.description or "")
            self._fields_count_label.setText(str(len(mapping.mappings)))

            if mapping.created_at:
                self._created_at_label.setText(mapping.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                self._created_at_label.setText("")

            if mapping.updated_at:
                self._updated_at_label.setText(mapping.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                self._updated_at_label.setText("")

            # Update fields table
            self._fields_table.setRowCount(0)
            for i, (orig_field, mapped_field) in enumerate(sorted(mapping.mappings.items())):
                self._fields_table.insertRow(i)
                self._fields_table.setItem(i, 0, QTableWidgetItem(orig_field))
                self._fields_table.setItem(i, 1, QTableWidgetItem(mapped_field))

                # Highlight if field name changed
                if orig_field != mapped_field:
                    self._fields_table.item(i, 1).setForeground(Qt.blue)

            self._fields_table.resizeColumnsToContents()

            # Emit signal that mapping was changed
            self.mappingChanged.emit(mapping_id)

        except Exception as e:
            self._logger.error(f"Failed to load mapping details: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load mapping details: {str(e)}")

    def _clear_mapping_details(self) -> None:
        """Clear the mapping details display."""
        self._table_name_label.setText("")
        self._description_label.setText("")
        self._fields_count_label.setText("")
        self._created_at_label.setText("")
        self._updated_at_label.setText("")
        self._fields_table.setRowCount(0)

    def _refresh_mappings(self) -> None:
        """Refresh the mappings list."""
        if self._current_connection_id:
            is_connected = False
            if self._current_connection_id in self._plugin._active_connectors:
                connector = self._plugin._active_connectors[self._current_connection_id]
                is_connected = connector.is_connected

            if is_connected:
                asyncio.create_task(self._load_mappings())

    def _create_new_mapping(self) -> None:
        """Create a new field mapping."""
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
                                "Please connect to the database before creating a mapping.")
            return

        dialog = FieldMappingDialog(self._plugin, self._logger, self._current_connection_id, self)
        if dialog.exec() == QDialog.Accepted:
            mapping = dialog.get_mapping()
            asyncio.create_task(self._save_mapping(mapping))

    def _edit_current_mapping(self) -> None:
        """Edit the currently selected mapping."""
        if not self._current_mapping_id:
            return

        mapping_task = asyncio.create_task(self._plugin.get_field_mapping(self._current_mapping_id))

        def continue_with_mapping(task):
            try:
                mapping = task.result()
                if mapping:
                    dialog = FieldMappingDialog(
                        self._plugin,
                        self._logger,
                        self._current_connection_id,
                        self,
                        mapping
                    )
                    if dialog.exec() == QDialog.Accepted:
                        updated_mapping = dialog.get_mapping()
                        asyncio.create_task(self._save_mapping(updated_mapping))
            except Exception as e:
                self._logger.error(f"Failed to edit mapping: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to edit mapping: {str(e)}")

        mapping_task.add_done_callback(continue_with_mapping)

    def _delete_current_mapping(self) -> None:
        """Delete the currently selected mapping."""
        if not self._current_mapping_id:
            return

        # Get the mapping name
        selected_items = self._mappings_list.selectedItems()
        if not selected_items:
            return

        mapping_name = selected_items[0].text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the mapping for '{mapping_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        asyncio.create_task(self._delete_mapping(self._current_mapping_id))

    async def _save_mapping(self, mapping: FieldMapping) -> None:
        """Save a field mapping.

        Args:
            mapping: The mapping to save
        """
        try:
            await self._plugin.save_field_mapping(mapping)
            await self._load_mappings()

            # Select the saved mapping
            for i in range(self._mappings_list.count()):
                item = self._mappings_list.item(i)
                if item and item.data(Qt.UserRole) == mapping.id:
                    self._mappings_list.setCurrentItem(item)
                    break

        except Exception as e:
            self._logger.error(f"Failed to save mapping: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save mapping: {str(e)}")

    async def _delete_mapping(self, mapping_id: str) -> None:
        """Delete a field mapping.

        Args:
            mapping_id: The ID of the mapping to delete
        """
        try:
            await self._plugin.delete_field_mapping(mapping_id)
            self._current_mapping_id = None
            self._clear_mapping_details()
            await self._load_mappings()

        except Exception as e:
            self._logger.error(f"Failed to delete mapping: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to delete mapping: {str(e)}")

    def _export_mapping(self) -> None:
        """Export the current mapping to a file."""
        if not self._current_mapping_id:
            return

        try:
            from PySide6.QtWidgets import QFileDialog
            import json

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Field Mapping",
                "",
                "JSON Files (*.json);;All Files (*.*)"
            )

            if not file_path:
                return

            if not file_path.lower().endswith('.json'):
                file_path += '.json'

            # Get the mapping
            mapping_task = asyncio.create_task(self._plugin.get_field_mapping(self._current_mapping_id))

            def save_mapping_to_file(task):
                try:
                    mapping = task.result()
                    if mapping:
                        mapping_dict = mapping.dict()

                        # Convert datetime objects to strings
                        if 'created_at' in mapping_dict and mapping_dict['created_at']:
                            mapping_dict['created_at'] = mapping_dict['created_at'].isoformat()

                        if 'updated_at' in mapping_dict and mapping_dict['updated_at']:
                            mapping_dict['updated_at'] = mapping_dict['updated_at'].isoformat()

                        with open(file_path, 'w') as f:
                            json.dump(mapping_dict, f, indent=2)

                        QMessageBox.information(
                            self,
                            "Export Successful",
                            f"Field mapping exported to {file_path}"
                        )
                except Exception as e:
                    self._logger.error(f"Failed to export mapping: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to export mapping: {str(e)}")

            mapping_task.add_done_callback(save_mapping_to_file)

        except Exception as e:
            self._logger.error(f"Failed to export mapping: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export mapping: {str(e)}")

    def _import_mapping(self) -> None:
        """Import a field mapping from a file."""
        if not self._current_connection_id:
            QMessageBox.warning(self, "No Connection", "Please select a database connection first.")
            return

        try:
            from PySide6.QtWidgets import QFileDialog
            import json
            import datetime

            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Field Mapping",
                "",
                "JSON Files (*.json);;All Files (*.*)"
            )

            if not file_path:
                return

            with open(file_path, 'r') as f:
                mapping_dict = json.load(f)

            # Update the connection ID to the current one
            mapping_dict['connection_id'] = self._current_connection_id

            # Generate a new ID
            mapping_dict['id'] = str(uuid.uuid4())

            # Update timestamps
            now = datetime.datetime.now()
            mapping_dict['created_at'] = now
            mapping_dict['updated_at'] = now

            # Convert string dates to datetime objects
            if isinstance(mapping_dict.get('created_at'), str):
                mapping_dict['created_at'] = datetime.datetime.fromisoformat(mapping_dict['created_at'])

            if isinstance(mapping_dict.get('updated_at'), str):
                mapping_dict['updated_at'] = datetime.datetime.fromisoformat(mapping_dict['updated_at'])

            mapping = FieldMapping(**mapping_dict)

            asyncio.create_task(self._save_mapping(mapping))

        except Exception as e:
            self._logger.error(f"Failed to import mapping: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to import mapping: {str(e)}")

    def _apply_mapping_to_query(self) -> None:
        """Apply the current mapping to a query editor."""
        if not self._current_mapping_id:
            return

        # Find the main tab widget
        parent = self.parent()
        while parent and not isinstance(parent, QTabWidget):
            parent = parent.parent()

        if parent and isinstance(parent, QTabWidget):
            # Find the query editor tab
            for i in range(parent.count()):
                if parent.tabText(i) == "Query Editor":
                    parent.setCurrentIndex(i)
                    break

            # Set the mapping in the query editor
            main_tab = parent.parent()
            if hasattr(main_tab, "_query_editor"):
                query_editor = main_tab._query_editor

                # Find the mapping combo box and set it
                if hasattr(query_editor, "_mapping_combo"):
                    for i in range(query_editor._mapping_combo.count()):
                        if query_editor._mapping_combo.itemData(i) == self._current_mapping_id:
                            query_editor._mapping_combo.setCurrentIndex(i)
                            break