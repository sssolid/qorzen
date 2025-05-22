"""
Validation tab for the Database Connector Plugin.

This module provides the validation tab UI for creating and managing
data validation rules and running validation checks on database data.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QDialog, QFormLayout,
    QDialogButtonBox, QFrame, QMenu, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTabWidget, QProgressBar, QScrollArea
)

from ..models import ValidationRule, ValidationRuleType


class ValidationRuleDialog(QDialog):
    """Dialog for creating and editing validation rules."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the validation rule dialog."""
        super().__init__(parent)

        self._rule: Optional[ValidationRule] = None

        # UI components
        self._name_edit: Optional[QLineEdit] = None
        self._description_edit: Optional[QTextEdit] = None
        self._connection_combo: Optional[QComboBox] = None
        self._table_edit: Optional[QLineEdit] = None
        self._field_edit: Optional[QLineEdit] = None
        self._rule_type_combo: Optional[QComboBox] = None
        self._error_message_edit: Optional[QLineEdit] = None
        self._active_check: Optional[QCheckBox] = None
        self._parameters_widget: Optional[QWidget] = None

        # Parameter controls (dynamically created based on rule type)
        self._parameter_controls: Dict[str, QWidget] = {}

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Validation Rule Editor")
        self.setModal(True)
        self.resize(500, 600)

        layout = QVBoxLayout(self)

        # Basic info
        basic_group = QGroupBox("Rule Information")
        basic_layout = QFormLayout(basic_group)

        # Rule name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter rule name")
        basic_layout.addRow("Name:", self._name_edit)

        # Description
        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(80)
        self._description_edit.setPlaceholderText("Enter rule description (optional)")
        basic_layout.addRow("Description:", self._description_edit)

        # Connection
        self._connection_combo = QComboBox()
        basic_layout.addRow("Connection:", self._connection_combo)

        # Table
        self._table_edit = QLineEdit()
        self._table_edit.setPlaceholderText("Table name")
        basic_layout.addRow("Table:", self._table_edit)

        # Field
        self._field_edit = QLineEdit()
        self._field_edit.setPlaceholderText("Field name")
        basic_layout.addRow("Field:", self._field_edit)

        # Rule type
        self._rule_type_combo = QComboBox()
        for rule_type in ValidationRuleType:
            self._rule_type_combo.addItem(rule_type.value.replace('_', ' ').title(), rule_type)
        self._rule_type_combo.currentTextChanged.connect(self._on_rule_type_changed)
        basic_layout.addRow("Rule Type:", self._rule_type_combo)

        # Error message
        self._error_message_edit = QLineEdit()
        self._error_message_edit.setPlaceholderText("Error message to show when validation fails")
        basic_layout.addRow("Error Message:", self._error_message_edit)

        # Active
        self._active_check = QCheckBox("Rule is active")
        self._active_check.setChecked(True)
        basic_layout.addRow("", self._active_check)

        layout.addWidget(basic_group)

        # Parameters section
        parameters_group = QGroupBox("Rule Parameters")
        parameters_layout = QVBoxLayout(parameters_group)

        # Scroll area for parameters
        scroll_area = QScrollArea()
        self._parameters_widget = QWidget()
        scroll_area.setWidget(self._parameters_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)

        parameters_layout.addWidget(scroll_area)

        layout.addWidget(parameters_group)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        # Initialize with default rule type
        self._on_rule_type_changed()

    def _on_rule_type_changed(self) -> None:
        """Handle rule type change to show appropriate parameters."""
        rule_type = self._rule_type_combo.currentData()
        if not rule_type:
            return

        # Clear existing parameters
        self._parameter_controls.clear()

        # Clear layout
        if self._parameters_widget.layout():
            while self._parameters_widget.layout().count():
                child = self._parameters_widget.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QFormLayout(self._parameters_widget)

        layout = self._parameters_widget.layout()
        if not layout:
            layout = QFormLayout(self._parameters_widget)

        # Add parameters based on rule type
        if rule_type == ValidationRuleType.RANGE:
            min_spin = QDoubleSpinBox()
            min_spin.setRange(-999999, 999999)
            min_spin.setDecimals(2)
            layout.addRow("Minimum Value:", min_spin)
            self._parameter_controls['min'] = min_spin

            max_spin = QDoubleSpinBox()
            max_spin.setRange(-999999, 999999)
            max_spin.setDecimals(2)
            layout.addRow("Maximum Value:", max_spin)
            self._parameter_controls['max'] = max_spin

        elif rule_type == ValidationRuleType.PATTERN:
            pattern_edit = QLineEdit()
            pattern_edit.setPlaceholderText("Regular expression pattern")
            layout.addRow("Pattern:", pattern_edit)
            self._parameter_controls['pattern'] = pattern_edit

        elif rule_type == ValidationRuleType.LENGTH:
            min_length_spin = QSpinBox()
            min_length_spin.setRange(0, 999999)
            layout.addRow("Minimum Length:", min_length_spin)
            self._parameter_controls['min_length'] = min_length_spin

            max_length_spin = QSpinBox()
            max_length_spin.setRange(0, 999999)
            layout.addRow("Maximum Length:", max_length_spin)
            self._parameter_controls['max_length'] = max_length_spin

        elif rule_type == ValidationRuleType.ENUMERATION:
            values_edit = QTextEdit()
            values_edit.setMaximumHeight(100)
            values_edit.setPlaceholderText("Enter allowed values, one per line")
            layout.addRow("Allowed Values:", values_edit)
            self._parameter_controls['allowed_values'] = values_edit

        elif rule_type == ValidationRuleType.CUSTOM:
            expression_edit = QTextEdit()
            expression_edit.setMaximumHeight(100)
            expression_edit.setPlaceholderText("Python expression that returns True/False (use 'value' variable)")
            layout.addRow("Expression:", expression_edit)
            self._parameter_controls['expression'] = expression_edit

        # NOT_NULL and UNIQUE don't need parameters

    def set_connections(self, connections: List[Any]) -> None:
        """Set available connections."""
        self._connection_combo.clear()
        self._connection_combo.addItem("-- Select Connection --", None)

        for connection in connections:
            self._connection_combo.addItem(connection.name, connection.id)

    def set_rule(self, rule: ValidationRule) -> None:
        """Set the rule to edit."""
        self._rule = rule

        # Populate fields
        self._name_edit.setText(rule.name)
        self._description_edit.setPlainText(rule.description or "")

        # Set connection
        conn_index = self._connection_combo.findData(rule.connection_id)
        if conn_index >= 0:
            self._connection_combo.setCurrentIndex(conn_index)

        self._table_edit.setText(rule.table_name)
        self._field_edit.setText(rule.field_name)

        # Set rule type
        type_index = self._rule_type_combo.findData(rule.rule_type)
        if type_index >= 0:
            self._rule_type_combo.setCurrentIndex(type_index)

        self._error_message_edit.setText(rule.error_message)
        self._active_check.setChecked(rule.active)

        # Set parameters
        self._set_parameters(rule.parameters)

    def _set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set parameter values."""
        for param_name, control in self._parameter_controls.items():
            if param_name in parameters:
                value = parameters[param_name]

                if isinstance(control, (QSpinBox, QDoubleSpinBox)):
                    control.setValue(value)
                elif isinstance(control, QLineEdit):
                    control.setText(str(value))
                elif isinstance(control, QTextEdit):
                    if param_name == 'allowed_values' and isinstance(value, list):
                        control.setPlainText('\n'.join(str(v) for v in value))
                    else:
                        control.setPlainText(str(value))

    def get_rule(self) -> ValidationRule:
        """Get the rule from the dialog."""
        # Validate required fields
        name = self._name_edit.text().strip()
        if not name:
            raise ValueError("Rule name is required")

        connection_id = self._connection_combo.currentData()
        if not connection_id:
            raise ValueError("Connection is required")

        table_name = self._table_edit.text().strip()
        if not table_name:
            raise ValueError("Table name is required")

        field_name = self._field_edit.text().strip()
        if not field_name:
            raise ValueError("Field name is required")

        rule_type = self._rule_type_combo.currentData()
        if not rule_type:
            raise ValueError("Rule type is required")

        error_message = self._error_message_edit.text().strip()
        if not error_message:
            raise ValueError("Error message is required")

        # Get parameters
        parameters = {}
        for param_name, control in self._parameter_controls.items():
            if isinstance(control, QSpinBox):
                parameters[param_name] = control.value()
            elif isinstance(control, QDoubleSpinBox):
                parameters[param_name] = control.value()
            elif isinstance(control, QLineEdit):
                text = control.text().strip()
                if text:
                    parameters[param_name] = text
            elif isinstance(control, QTextEdit):
                text = control.toPlainText().strip()
                if text:
                    if param_name == 'allowed_values':
                        parameters[param_name] = [line.strip() for line in text.split('\n') if line.strip()]
                    else:
                        parameters[param_name] = text

        # Create or update rule
        if self._rule:
            # Update existing rule
            self._rule.name = name
            self._rule.description = self._description_edit.toPlainText().strip() or None
            self._rule.connection_id = connection_id
            self._rule.table_name = table_name
            self._rule.field_name = field_name
            self._rule.rule_type = rule_type
            self._rule.parameters = parameters
            self._rule.error_message = error_message
            self._rule.active = self._active_check.isChecked()
            self._rule.updated_at = datetime.now()
            return self._rule
        else:
            # Create new rule
            return ValidationRule(
                name=name,
                description=self._description_edit.toPlainText().strip() or None,
                connection_id=connection_id,
                table_name=table_name,
                field_name=field_name,
                rule_type=rule_type,
                parameters=parameters,
                error_message=error_message,
                active=self._active_check.isChecked()
            )


class ValidationTab(QWidget):
    """
    Validation tab for managing data validation rules.

    Provides functionality for:
    - Creating and managing validation rules
    - Running validation checks on database data
    - Viewing validation results
    - Managing rule templates
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
        Initialize the validation tab.

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
        self._table_combo: Optional[QComboBox] = None
        self._rules_table: Optional[QTableWidget] = None
        self._results_tree: Optional[QTreeWidget] = None
        self._rule_details: Optional[QTextEdit] = None

        # State
        self._current_rules: List[Dict[str, Any]] = []
        self._connections: List[Any] = []
        self._validation_results: List[Dict[str, Any]] = []

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Create tab widget
        tab_widget = QTabWidget()

        # Rules management tab
        rules_tab = self._create_rules_tab()
        tab_widget.addTab(rules_tab, "Validation Rules")

        # Results tab
        results_tab = self._create_results_tab()
        tab_widget.addTab(results_tab, "Validation Results")

        layout.addWidget(tab_widget)

    def _create_rules_tab(self) -> QWidget:
        """Create the rules management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Toolbar
        toolbar = self._create_rules_toolbar()
        layout.addWidget(toolbar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (rules list)
        left_panel = self._create_rules_list_panel()
        splitter.addWidget(left_panel)

        # Right panel (rule details)
        right_panel = self._create_rule_details_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)

        return tab

    def _create_results_tab(self) -> QWidget:
        """Create the validation results tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Results toolbar
        results_toolbar = self._create_results_toolbar()
        layout.addWidget(results_toolbar)

        # Results tree
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout(results_group)

        self._results_tree = QTreeWidget()
        self._results_tree.setHeaderLabels([
            "Rule", "Table", "Field", "Status", "Failed Records", "Total Records", "Validated At"
        ])
        self._results_tree.setAlternatingRowColors(True)
        results_layout.addWidget(self._results_tree)

        layout.addWidget(results_group)

        return tab

    def _create_rules_toolbar(self) -> QFrame:
        """Create the rules toolbar."""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(toolbar)

        # Connection filter
        layout.addWidget(QLabel("Connection:"))

        self._connection_combo = QComboBox()
        self._connection_combo.addItem("All Connections", None)
        self._connection_combo.currentTextChanged.connect(self._on_connection_filter_changed)
        layout.addWidget(self._connection_combo)

        # Table filter
        layout.addWidget(QLabel("Table:"))

        self._table_combo = QComboBox()
        self._table_combo.addItem("All Tables", None)
        self._table_combo.currentTextChanged.connect(self._on_table_filter_changed)
        layout.addWidget(self._table_combo)

        layout.addStretch()

        # Action buttons
        new_rule_button = QPushButton("New Rule")
        new_rule_button.clicked.connect(self._create_rule)
        layout.addWidget(new_rule_button)

        edit_rule_button = QPushButton("Edit")
        edit_rule_button.clicked.connect(self._edit_rule)
        layout.addWidget(edit_rule_button)

        delete_rule_button = QPushButton("Delete")
        delete_rule_button.clicked.connect(self._delete_rule)
        layout.addWidget(delete_rule_button)

        validate_button = QPushButton("Validate Data")
        validate_button.clicked.connect(self._validate_data)
        layout.addWidget(validate_button)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: asyncio.create_task(self.refresh()))
        layout.addWidget(refresh_button)

        return toolbar

    def _create_results_toolbar(self) -> QFrame:
        """Create the results toolbar."""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(toolbar)

        layout.addWidget(QLabel("Validation Results:"))

        layout.addStretch()

        clear_results_button = QPushButton("Clear Results")
        clear_results_button.clicked.connect(self._clear_results)
        layout.addWidget(clear_results_button)

        export_results_button = QPushButton("Export Results")
        export_results_button.clicked.connect(self._export_results)
        layout.addWidget(export_results_button)

        return toolbar

    def _create_rules_list_panel(self) -> QGroupBox:
        """Create the rules list panel."""
        group = QGroupBox("Validation Rules")
        layout = QVBoxLayout(group)

        self._rules_table = QTableWidget()
        self._rules_table.setColumnCount(6)
        self._rules_table.setHorizontalHeaderLabels([
            "Name", "Connection", "Table", "Field", "Rule Type", "Active"
        ])
        self._rules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._rules_table.setAlternatingRowColors(True)
        self._rules_table.itemSelectionChanged.connect(self._on_rule_selection_changed)
        self._rules_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._rules_table.customContextMenuRequested.connect(self._show_rule_context_menu)

        # Configure headers
        header = self._rules_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._rules_table)

        return group

    def _create_rule_details_panel(self) -> QGroupBox:
        """Create the rule details panel."""
        group = QGroupBox("Rule Details")
        layout = QVBoxLayout(group)

        self._rule_details = QTextEdit()
        self._rule_details.setReadOnly(True)
        self._rule_details.setPlaceholderText("Select a rule to view details")
        layout.addWidget(self._rule_details)

        return group

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Load initial data
        asyncio.create_task(self.refresh())

    async def refresh(self) -> None:
        """Refresh all data in the tab."""
        try:
            self.operation_started.emit("Refreshing validation data...")

            # Load connections
            await self._load_connections()

            # Load validation rules
            await self._load_validation_rules()

            # Load tables for current connection
            await self._load_tables()

            self.operation_finished.emit()
            self.status_changed.emit("Validation data refreshed")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to refresh validation tab: {e}")
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

    async def _load_validation_rules(self) -> None:
        """Load validation rules."""
        try:
            connection_filter = self._connection_combo.currentData()
            table_filter = self._table_combo.currentData()

            # Convert connection ID to name if needed
            connection_name = None
            if connection_filter:
                for conn in self._connections:
                    if conn.id == connection_filter:
                        connection_name = conn.name
                        break

            rules = await self._plugin.get_validation_rules(connection_name, table_filter)
            self._current_rules = rules
            self._populate_rules_table()

        except Exception as e:
            self._logger.error(f"Failed to load validation rules: {e}")

    async def _load_tables(self) -> None:
        """Load tables for the selected connection."""
        try:
            connection_id = self._connection_combo.currentData()
            if not connection_id:
                self._table_combo.clear()
                self._table_combo.addItem("All Tables", None)
                return

            tables = await self._plugin.get_tables(connection_id)

            current_text = self._table_combo.currentText()
            self._table_combo.clear()
            self._table_combo.addItem("All Tables", None)

            for table in tables:
                self._table_combo.addItem(table['name'], table['name'])

            # Restore selection
            if current_text:
                index = self._table_combo.findText(current_text)
                if index >= 0:
                    self._table_combo.setCurrentIndex(index)

        except Exception as e:
            self._logger.error(f"Failed to load tables: {e}")

    def _populate_rules_table(self) -> None:
        """Populate the rules table."""
        try:
            self._rules_table.setRowCount(len(self._current_rules))

            for row, rule in enumerate(self._current_rules):
                # Name
                name_item = QTableWidgetItem(rule.get('name', 'Unknown'))
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._rules_table.setItem(row, 0, name_item)

                # Connection
                connection_item = QTableWidgetItem(rule.get('connection_id', 'Unknown'))
                connection_item.setFlags(connection_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._rules_table.setItem(row, 1, connection_item)

                # Table
                table_item = QTableWidgetItem(rule.get('table_name', 'Unknown'))
                table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._rules_table.setItem(row, 2, table_item)

                # Field
                field_item = QTableWidgetItem(rule.get('field_name', 'Unknown'))
                field_item.setFlags(field_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._rules_table.setItem(row, 3, field_item)

                # Rule type
                rule_type = rule.get('rule_type', 'unknown')
                rule_type_item = QTableWidgetItem(rule_type.replace('_', ' ').title())
                rule_type_item.setFlags(rule_type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._rules_table.setItem(row, 4, rule_type_item)

                # Active
                active_item = QTableWidgetItem("Yes" if rule.get('active', True) else "No")
                active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._rules_table.setItem(row, 5, active_item)

                # Store rule data
                name_item.setData(Qt.ItemDataRole.UserRole, rule)

        except Exception as e:
            self._logger.error(f"Failed to populate rules table: {e}")

    def _on_connection_filter_changed(self) -> None:
        """Handle connection filter change."""
        asyncio.create_task(self._load_tables())
        asyncio.create_task(self._load_validation_rules())

    def _on_table_filter_changed(self) -> None:
        """Handle table filter change."""
        asyncio.create_task(self._load_validation_rules())

    def _on_rule_selection_changed(self) -> None:
        """Handle rule selection change."""
        try:
            current_row = self._rules_table.currentRow()
            if current_row < 0 or current_row >= len(self._current_rules):
                self._rule_details.clear()
                return

            rule = self._current_rules[current_row]
            self._show_rule_details(rule)

        except Exception as e:
            self._logger.error(f"Error handling rule selection: {e}")

    def _show_rule_details(self, rule: Dict[str, Any]) -> None:
        """Show rule details."""
        try:
            details_parts = []

            # Basic info
            details_parts.append(f"Name: {rule.get('name', 'Unknown')}")
            details_parts.append(f"Description: {rule.get('description', 'No description')}")
            details_parts.append(f"Connection: {rule.get('connection_id', 'Unknown')}")
            details_parts.append(f"Table: {rule.get('table_name', 'Unknown')}")
            details_parts.append(f"Field: {rule.get('field_name', 'Unknown')}")
            details_parts.append(f"Rule Type: {rule.get('rule_type', 'unknown').replace('_', ' ').title()}")
            details_parts.append(f"Active: {'Yes' if rule.get('active', True) else 'No'}")
            details_parts.append("")

            # Parameters
            parameters = rule.get('parameters', {})
            if parameters:
                details_parts.append("Parameters:")
                for key, value in parameters.items():
                    details_parts.append(f"  {key}: {value}")
                details_parts.append("")

            # Error message
            details_parts.append(f"Error Message: {rule.get('error_message', 'No error message')}")
            details_parts.append("")

            # Timestamps
            if 'created_at' in rule:
                details_parts.append(f"Created: {rule['created_at']}")
            if 'updated_at' in rule:
                details_parts.append(f"Updated: {rule['updated_at']}")

            self._rule_details.setPlainText('\n'.join(details_parts))

        except Exception as e:
            self._logger.error(f"Failed to show rule details: {e}")

    def _create_rule(self) -> None:
        """Create a new validation rule."""
        dialog = ValidationRuleDialog(self)
        dialog.set_connections(self._connections)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                rule = dialog.get_rule()
                asyncio.create_task(self._create_rule_async(rule))
            except ValueError as e:
                self._show_warning("Validation Error", str(e))

    async def _create_rule_async(self, rule: ValidationRule) -> None:
        """Create rule asynchronously."""
        try:
            self.operation_started.emit("Creating validation rule...")

            await self._plugin.create_validation_rule(
                rule_type=rule.rule_type.value,
                connection_id=rule.connection_id,
                table_name=rule.table_name,
                field_name=rule.field_name,
                parameters=rule.parameters,
                error_message=rule.error_message,
                name=rule.name,
                description=rule.description
            )

            await self._load_validation_rules()

            self.operation_finished.emit()
            self.status_changed.emit(f"Created validation rule: {rule.name}")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to create validation rule: {e}")
            self._show_error("Create Error", f"Failed to create validation rule: {e}")

    def _edit_rule(self) -> None:
        """Edit the selected validation rule."""
        current_row = self._rules_table.currentRow()
        if current_row < 0:
            self._show_warning("No Selection", "Please select a rule to edit")
            return

        # For now, show details - full editing would require more implementation
        self._show_info("Edit Rule", "Rule editing would be implemented here")

    def _delete_rule(self) -> None:
        """Delete the selected validation rule."""
        current_row = self._rules_table.currentRow()
        if current_row < 0:
            self._show_warning("No Selection", "Please select a rule to delete")
            return

        rule = self._current_rules[current_row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the rule '{rule.get('name', 'Unknown')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            rule_id = rule.get('id')
            if rule_id:
                asyncio.create_task(self._delete_rule_async(rule_id))

    async def _delete_rule_async(self, rule_id: str) -> None:
        """Delete rule asynchronously."""
        try:
            self.operation_started.emit("Deleting validation rule...")

            # This would use the plugin's delete method when implemented
            # success = await self._plugin.delete_validation_rule(rule_id)

            await self._load_validation_rules()

            self.operation_finished.emit()
            self.status_changed.emit("Validation rule deleted")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to delete validation rule: {e}")
            self._show_error("Delete Error", f"Failed to delete validation rule: {e}")

    def _validate_data(self) -> None:
        """Run validation on selected data."""
        # This would implement data validation
        self._show_info("Validate Data", "Data validation would be implemented here")

    def _clear_results(self) -> None:
        """Clear validation results."""
        self._results_tree.clear()
        self._validation_results.clear()
        self.status_changed.emit("Validation results cleared")

    def _export_results(self) -> None:
        """Export validation results."""
        self._show_info("Export Results", "Results export would be implemented here")

    def _show_rule_context_menu(self, position) -> None:
        """Show context menu for rules table."""
        item = self._rules_table.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("Edit Rule")
        edit_action.triggered.connect(self._edit_rule)

        delete_action = menu.addAction("Delete Rule")
        delete_action.triggered.connect(self._delete_rule)

        menu.addSeparator()

        validate_action = menu.addAction("Validate This Rule")
        validate_action.triggered.connect(self._validate_single_rule)

        duplicate_action = menu.addAction("Duplicate Rule")
        duplicate_action.triggered.connect(self._duplicate_rule)

        menu.exec(self._rules_table.mapToGlobal(position))

    def _validate_single_rule(self) -> None:
        """Validate a single rule."""
        self._show_info("Validate Rule", "Single rule validation would be implemented here")

    def _duplicate_rule(self) -> None:
        """Duplicate the selected rule."""
        self._show_info("Duplicate Rule", "Rule duplication would be implemented here")

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
            self._current_rules.clear()
            self._connections.clear()
            self._validation_results.clear()
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")