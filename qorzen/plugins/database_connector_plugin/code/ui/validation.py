# processed_project/qorzen_stripped/plugins/database_connector_plugin/code/ui/validation.py
from __future__ import annotations

'''
Validation UI for the Database Connector Plugin.

This module provides a user interface for creating, managing, and running
data validation rules against database fields, enabling data quality control.
'''
import asyncio
import uuid
import json
import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QBrush
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QComboBox, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                               QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox,
                               QMessageBox, QInputDialog, QGroupBox, QMenu, QToolButton,
                               QSplitter, QTabWidget, QRadioButton, QButtonGroup, QSpinBox,
                               QTextEdit, QProgressBar, QFrame)

from ..models import ValidationRule, ValidationRuleType, ValidationResult, QueryResult
from ..utils.validation import (
    create_range_rule, create_pattern_rule, create_not_null_rule,
    create_unique_rule, create_length_rule, create_enumeration_rule,
    create_custom_rule
)


class RuleDialog(QDialog):
    """Dialog for creating and editing validation rules."""

    def __init__(self, plugin: Any, logger: Any, connection_id: str,
                 parent: Optional[QWidget] = None,
                 rule: Optional[ValidationRule] = None) -> None:
        """Initialize the validation rule dialog.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            connection_id: The current database connection ID
            parent: The parent widget
            rule: Optional existing rule to edit
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._connection_id = connection_id
        self._rule = rule
        self._tables: List[str] = []
        self._fields: List[str] = []

        self._init_ui()

        # Load existing rule if provided
        if rule:
            self.setWindowTitle("Edit Validation Rule")
            self._populate_from_rule(rule)
        else:
            self.setWindowTitle("Create Validation Rule")

        # Load tables from database
        self._load_tables()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(600)
        self.setMinimumHeight(550)

        main_layout = QVBoxLayout(self)

        # Basic info section
        info_group = QGroupBox("Rule Information")
        info_form = QFormLayout(info_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter a name for this validation rule")

        self._description_edit = QLineEdit()
        self._description_edit.setPlaceholderText("Optional description of what this rule validates")

        self._table_combo = QComboBox()
        self._table_combo.setMinimumWidth(250)
        self._table_combo.currentIndexChanged.connect(self._on_table_selected)

        self._field_combo = QComboBox()
        self._field_combo.setMinimumWidth(250)

        self._active_check = QCheckBox("Active")
        self._active_check.setChecked(True)

        info_form.addRow("Name:", self._name_edit)
        info_form.addRow("Description:", self._description_edit)
        info_form.addRow("Table:", self._table_combo)
        info_form.addRow("Field:", self._field_combo)
        info_form.addRow("", self._active_check)

        main_layout.addWidget(info_group)

        # Rule type section
        rule_group = QGroupBox("Rule Type")
        rule_layout = QVBoxLayout(rule_group)

        self._rule_type_combo = QComboBox()
        self._rule_type_combo.addItem("Range Check", ValidationRuleType.RANGE)
        self._rule_type_combo.addItem("Pattern Match", ValidationRuleType.PATTERN)
        self._rule_type_combo.addItem("Not Null", ValidationRuleType.NOT_NULL)
        self._rule_type_combo.addItem("Unique Values", ValidationRuleType.UNIQUE)
        self._rule_type_combo.addItem("Length Check", ValidationRuleType.LENGTH)
        self._rule_type_combo.addItem("Reference Check", ValidationRuleType.REFERENCE)
        self._rule_type_combo.addItem("Enumeration Check", ValidationRuleType.ENUMERATION)
        self._rule_type_combo.addItem("Custom Expression", ValidationRuleType.CUSTOM)

        self._rule_type_combo.currentIndexChanged.connect(self._on_rule_type_changed)

        rule_layout.addWidget(self._rule_type_combo)

        # Stacked widget for rule parameters
        self._params_container = QWidget()
        self._params_layout = QFormLayout(self._params_container)

        rule_layout.addWidget(self._params_container)

        main_layout.addWidget(rule_group)

        # Error message section
        message_group = QGroupBox("Error Message")
        message_layout = QVBoxLayout(message_group)

        self._error_message_edit = QTextEdit()
        self._error_message_edit.setPlaceholderText("Error message to display when validation fails")
        self._error_message_edit.setMaximumHeight(100)

        message_layout.addWidget(self._error_message_edit)

        main_layout.addWidget(message_group)

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

        # Initial rule type setup
        self._on_rule_type_changed(0)

    def _populate_from_rule(self, rule: ValidationRule) -> None:
        """Populate the dialog with data from an existing rule.

        Args:
            rule: The rule to edit
        """
        self._name_edit.setText(rule.name)
        self._description_edit.setText(rule.description or "")
        self._active_check.setChecked(rule.active)
        self._error_message_edit.setText(rule.error_message)

        # Rule type, table, and field will be selected when data is loaded
        self._rule_type_to_select = rule.rule_type
        self._table_name_to_select = rule.table_name
        self._field_name_to_select = rule.field_name
        self._parameters_to_set = rule.parameters

    def _load_tables(self) -> None:
        """Load database tables."""
        self._status_label.setText("Loading tables...")
        self._progress_bar.setVisible(True)
        self._table_combo.setEnabled(False)

        asyncio.create_task(self._async_load_tables())

    async def _async_load_tables(self) -> None:
        """Asynchronously load database tables."""
        try:
            connector = await self._plugin.get_connector(self._connection_id)
            tables = await connector.get_tables()

            # Extract table names and sort
            self._tables = sorted([table.name for table in tables])

            # Update UI
            self._table_combo.clear()
            self._table_combo.addItem("Select a table...", None)

            for table_name in self._tables:
                self._table_combo.addItem(table_name, table_name)

            # Select table if editing existing rule
            if hasattr(self, '_table_name_to_select'):
                for i in range(self._table_combo.count()):
                    if self._table_combo.itemData(i) == self._table_name_to_select:
                        self._table_combo.setCurrentIndex(i)
                        break

            self._status_label.setText(f"Loaded {len(self._tables)} tables")
            self._progress_bar.setVisible(False)
            self._table_combo.setEnabled(True)

            # Set rule type if editing
            if hasattr(self, '_rule_type_to_select'):
                for i in range(self._rule_type_combo.count()):
                    if self._rule_type_combo.itemData(i) == self._rule_type_to_select:
                        self._rule_type_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f"Failed to load tables: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to load tables: {str(e)}")

    def _on_table_selected(self, index: int) -> None:
        """Handle table selection changes.

        Args:
            index: The index of the selected table
        """
        table_name = self._table_combo.itemData(index)

        if not table_name:
            self._field_combo.clear()
            return

        self._status_label.setText(f"Loading columns for {table_name}...")
        self._progress_bar.setVisible(True)
        self._field_combo.setEnabled(False)

        asyncio.create_task(self._async_load_columns(table_name))

    async def _async_load_columns(self, table_name: str) -> None:
        """Asynchronously load columns for the selected table.

        Args:
            table_name: The name of the table to load columns for
        """
        try:
            connector = await self._plugin.get_connector(self._connection_id)
            columns = await connector.get_table_columns(table_name)

            # Sort columns by name
            columns.sort(key=lambda c: c.name.lower())

            # Extract field names
            self._fields = [column.name for column in columns]

            # Update UI
            self._field_combo.clear()
            self._field_combo.addItem("Select a field...", None)

            for field_name in self._fields:
                self._field_combo.addItem(field_name, field_name)

            # Select field if editing existing rule
            if hasattr(self, '_field_name_to_select') and self._table_name_to_select == table_name:
                for i in range(self._field_combo.count()):
                    if self._field_combo.itemData(i) == self._field_name_to_select:
                        self._field_combo.setCurrentIndex(i)
                        break

            self._status_label.setText(f"Loaded {len(columns)} columns")
            self._progress_bar.setVisible(False)
            self._field_combo.setEnabled(True)

            # Set parameters if editing
            if hasattr(self, '_parameters_to_set') and self._rule and self._rule.table_name == table_name:
                self._set_rule_parameters(self._parameters_to_set)

        except Exception as e:
            self._logger.error(f"Failed to load columns: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to load columns: {str(e)}")

    def _on_rule_type_changed(self, index: int) -> None:
        """Handle rule type selection changes.

        Args:
            index: The index of the selected rule type
        """
        rule_type = self._rule_type_combo.itemData(index)

        # Clear existing parameters
        while self._params_layout.count() > 0:
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create parameters UI based on rule type
        if rule_type == ValidationRuleType.RANGE:
            self._create_range_parameters()
        elif rule_type == ValidationRuleType.PATTERN:
            self._create_pattern_parameters()
        elif rule_type == ValidationRuleType.NOT_NULL:
            self._create_not_null_parameters()
        elif rule_type == ValidationRuleType.UNIQUE:
            self._create_unique_parameters()
        elif rule_type == ValidationRuleType.LENGTH:
            self._create_length_parameters()
        elif rule_type == ValidationRuleType.REFERENCE:
            self._create_reference_parameters()
        elif rule_type == ValidationRuleType.ENUMERATION:
            self._create_enumeration_parameters()
        elif rule_type == ValidationRuleType.CUSTOM:
            self._create_custom_parameters()

        # Update default error message
        self._update_default_error_message()

        # Set parameters if editing
        if hasattr(self, '_parameters_to_set') and self._rule and self._rule.rule_type == rule_type:
            self._set_rule_parameters(self._parameters_to_set)

    def _create_range_parameters(self) -> None:
        """Create UI for range validation parameters."""
        min_label = QLabel("Minimum Value:")
        self._min_value_edit = QLineEdit()
        self._min_value_edit.setPlaceholderText("Optional")

        max_label = QLabel("Maximum Value:")
        self._max_value_edit = QLineEdit()
        self._max_value_edit.setPlaceholderText("Optional")

        self._params_layout.addRow(min_label, self._min_value_edit)
        self._params_layout.addRow(max_label, self._max_value_edit)

        # Connect to update error message
        self._min_value_edit.textChanged.connect(self._update_default_error_message)
        self._max_value_edit.textChanged.connect(self._update_default_error_message)

    def _create_pattern_parameters(self) -> None:
        """Create UI for pattern validation parameters."""
        pattern_label = QLabel("Regular Expression Pattern:")
        self._pattern_edit = QLineEdit()
        self._pattern_edit.setPlaceholderText("e.g. ^[A-Z0-9]{5,10}$")

        example_label = QLabel("Examples:")
        examples = QLabel(
            "Email: ^[\\w.-]+@[\\w.-]+\\.[a-zA-Z]{2,}$\nPhone: ^\\d{3}-\\d{3}-\\d{4}$\nAlphanumeric: ^[a-zA-Z0-9]+$")
        examples.setStyleSheet("color: gray; font-size: 10pt;")

        self._params_layout.addRow(pattern_label, self._pattern_edit)
        self._params_layout.addRow(example_label, examples)

        # Connect to update error message
        self._pattern_edit.textChanged.connect(self._update_default_error_message)

    def _create_not_null_parameters(self) -> None:
        """Create UI for not null validation parameters."""
        info_label = QLabel("This rule checks that values are not NULL.")
        self._params_layout.addRow("", info_label)

    def _create_unique_parameters(self) -> None:
        """Create UI for unique validation parameters."""
        info_label = QLabel("This rule validates that all values are unique.")
        self._params_layout.addRow("", info_label)

    def _create_length_parameters(self) -> None:
        """Create UI for length validation parameters."""
        min_label = QLabel("Minimum Length:")
        self._min_length_edit = QSpinBox()
        self._min_length_edit.setRange(0, 9999)
        self._min_length_edit.setValue(0)
        self._min_length_edit.setSpecialValueText("No minimum")

        max_label = QLabel("Maximum Length:")
        self._max_length_edit = QSpinBox()
        self._max_length_edit.setRange(0, 9999)
        self._max_length_edit.setValue(0)
        self._max_length_edit.setSpecialValueText("No maximum")

        self._params_layout.addRow(min_label, self._min_length_edit)
        self._params_layout.addRow(max_label, self._max_length_edit)

        # Connect to update error message
        self._min_length_edit.valueChanged.connect(self._update_default_error_message)
        self._max_length_edit.valueChanged.connect(self._update_default_error_message)

    def _create_reference_parameters(self) -> None:
        """Create UI for reference validation parameters."""
        info_label = QLabel("This rule validates that values exist in a reference list.")

        values_label = QLabel("Reference Values:")
        self._reference_values_edit = QTextEdit()
        self._reference_values_edit.setPlaceholderText("Enter values, one per line")
        self._reference_values_edit.setMaximumHeight(100)

        load_button = QPushButton("Load from Query")
        load_button.clicked.connect(self._load_reference_values)

        self._params_layout.addRow("", info_label)
        self._params_layout.addRow(values_label, self._reference_values_edit)
        self._params_layout.addRow("", load_button)

    def _create_enumeration_parameters(self) -> None:
        """Create UI for enumeration validation parameters."""
        info_label = QLabel("This rule validates that values are in a allowed list.")

        values_label = QLabel("Allowed Values:")
        self._enum_values_edit = QTextEdit()
        self._enum_values_edit.setPlaceholderText("Enter allowed values, one per line")
        self._enum_values_edit.setMaximumHeight(100)

        self._params_layout.addRow("", info_label)
        self._params_layout.addRow(values_label, self._enum_values_edit)

    def _create_custom_parameters(self) -> None:
        """Create UI for custom validation parameters."""
        info_label = QLabel("This rule uses a custom Python expression to validate values.")

        help_label = QLabel("In the expression, use 'value' to reference the field value.")
        help_label.setStyleSheet("color: gray;")

        expression_label = QLabel("Expression:")
        self._expression_edit = QTextEdit()
        self._expression_edit.setPlaceholderText("e.g. value > 0 and value < 100")
        self._expression_edit.setMaximumHeight(100)

        examples_label = QLabel("Examples:")
        examples = QLabel(
            "Numeric range: value >= 10 and value <= 20\nString pattern: re.match(r'^[A-Z][a-z]+$', value)\nDate check: value.year >= 2020")
        examples.setStyleSheet("color: gray; font-size: 10pt;")

        self._params_layout.addRow("", info_label)
        self._params_layout.addRow("", help_label)
        self._params_layout.addRow(expression_label, self._expression_edit)
        self._params_layout.addRow(examples_label, examples)

    def _load_reference_values(self) -> None:
        """Load reference values from a database query."""
        QMessageBox.information(
            self,
            "Load Reference Values",
            "This feature would allow loading reference values from a query.\n"
            "For now, please enter the values manually."
        )

    def _update_default_error_message(self) -> None:
        """Update the default error message based on the current rule settings."""
        rule_type = self._rule_type_combo.currentData()
        field_name = self._field_combo.currentText()

        if field_name == "Select a field...":
            field_name = "field"

        message = ""

        if rule_type == ValidationRuleType.RANGE:
            min_value = self._min_value_edit.text().strip()
            max_value = self._max_value_edit.text().strip()

            if min_value and max_value:
                message = f"Value must be between {min_value} and {max_value}"
            elif min_value:
                message = f"Value must be at least {min_value}"
            elif max_value:
                message = f"Value must be at most {max_value}"
            else:
                message = "Value is outside the allowed range"

        elif rule_type == ValidationRuleType.PATTERN:
            pattern = self._pattern_edit.text().strip()
            if pattern:
                message = f"Value must match pattern: {pattern}"
            else:
                message = "Value does not match the required pattern"

        elif rule_type == ValidationRuleType.NOT_NULL:
            message = f"{field_name} cannot be NULL"

        elif rule_type == ValidationRuleType.UNIQUE:
            message = f"{field_name} must be unique"

        elif rule_type == ValidationRuleType.LENGTH:
            min_length = self._min_length_edit.value()
            max_length = self._max_length_edit.value()

            if min_length > 0 and max_length > 0:
                message = f"Length must be between {min_length} and {max_length} characters"
            elif min_length > 0:
                message = f"Length must be at least {min_length} characters"
            elif max_length > 0:
                message = f"Length must be at most {max_length} characters"
            else:
                message = "Length is outside the allowed range"

        elif rule_type == ValidationRuleType.REFERENCE:
            message = f"{field_name} must reference a valid value"

        elif rule_type == ValidationRuleType.ENUMERATION:
            message = f"{field_name} must be one of the allowed values"

        elif rule_type == ValidationRuleType.CUSTOM:
            message = f"{field_name} failed custom validation"

        # Only set if the user hasn't modified it
        if not self._error_message_edit.toPlainText() or (
                hasattr(self, '_last_rule_type') and self._last_rule_type != rule_type
        ):
            self._error_message_edit.setText(message)

        self._last_rule_type = rule_type

    def _set_rule_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set the parameter controls based on the rule parameters.

        Args:
            parameters: The rule parameters
        """
        rule_type = self._rule_type_combo.currentData()

        if rule_type == ValidationRuleType.RANGE:
            if 'min' in parameters:
                self._min_value_edit.setText(str(parameters['min']))
            if 'max' in parameters:
                self._max_value_edit.setText(str(parameters['max']))

        elif rule_type == ValidationRuleType.PATTERN:
            if 'pattern' in parameters:
                self._pattern_edit.setText(parameters['pattern'])

        elif rule_type == ValidationRuleType.LENGTH:
            if 'min_length' in parameters:
                self._min_length_edit.setValue(parameters['min_length'])
            if 'max_length' in parameters:
                self._max_length_edit.setValue(parameters['max_length'])

        elif rule_type == ValidationRuleType.REFERENCE:
            if 'reference_values' in parameters:
                values = '\n'.join(str(v) for v in parameters['reference_values'])
                self._reference_values_edit.setText(values)

        elif rule_type == ValidationRuleType.ENUMERATION:
            if 'allowed_values' in parameters:
                values = '\n'.join(str(v) for v in parameters['allowed_values'])
                self._enum_values_edit.setText(values)

        elif rule_type == ValidationRuleType.CUSTOM:
            if 'expression' in parameters:
                self._expression_edit.setText(parameters['expression'])


    def get_rule(self) -> ValidationRule:
        """Get the validation rule created or edited in this dialog.

        Returns:
            The validation rule
        """
        if not self._field_combo.currentData():
            raise ValueError("No field selected")

        table_name = self._table_combo.currentData()
        field_name = self._field_combo.currentData()
        rule_type = self._rule_type_combo.currentData()

        # Extract parameters based on rule type
        parameters = {}

        if rule_type == ValidationRuleType.RANGE:
            min_value = self._min_value_edit.text().strip()
            max_value = self._max_value_edit.text().strip()

            if min_value:
                try:
                    if '.' in min_value:
                        parameters['min'] = float(min_value)
                    else:
                        parameters['min'] = int(min_value)
                except ValueError:
                    raise ValueError(f"Invalid minimum value: {min_value}")

            if max_value:
                try:
                    if '.' in max_value:
                        parameters['max'] = float(max_value)
                    else:
                        parameters['max'] = int(max_value)
                except ValueError:
                    raise ValueError(f"Invalid maximum value: {max_value}")

        elif rule_type == ValidationRuleType.PATTERN:
            pattern = self._pattern_edit.text().strip()
            if not pattern:
                raise ValueError("Pattern cannot be empty")
            parameters['pattern'] = pattern

        elif rule_type == ValidationRuleType.NOT_NULL:
            # No parameters needed
            pass

        elif rule_type == ValidationRuleType.UNIQUE:
            # Parameters will be populated at runtime
            pass

        elif rule_type == ValidationRuleType.LENGTH:
            min_length = self._min_length_edit.value()
            max_length = self._max_length_edit.value()

            if min_length > 0:
                parameters['min_length'] = min_length

            if max_length > 0:
                parameters['max_length'] = max_length

        elif rule_type == ValidationRuleType.REFERENCE:
            values_text = self._reference_values_edit.toPlainText().strip()
            if not values_text:
                raise ValueError("Reference values cannot be empty")

            values = [line.strip() for line in values_text.split('\n') if line.strip()]
            parameters['reference_values'] = values

        elif rule_type == ValidationRuleType.ENUMERATION:
            values_text = self._enum_values_edit.toPlainText().strip()
            if not values_text:
                raise ValueError("Allowed values cannot be empty")

            values = [line.strip() for line in values_text.split('\n') if line.strip()]
            parameters['allowed_values'] = values

        elif rule_type == ValidationRuleType.CUSTOM:
            expression = self._expression_edit.toPlainText().strip()
            if not expression:
                raise ValueError("Expression cannot be empty")

            parameters['expression'] = expression

        rule_id = self._rule.id if self._rule else str(uuid.uuid4())

        return ValidationRule(
            id=rule_id,
            name=self._name_edit.text().strip(),
            description=self._description_edit.text().strip() or None,
            connection_id=self._connection_id,
            table_name=table_name,
            field_name=field_name,
            rule_type=rule_type,
            parameters=parameters,
            error_message=self._error_message_edit.toPlainText().strip(),
            active=self._active_check.isChecked()
        )

    def accept(self) -> None:
        """Handle dialog acceptance."""
        try:
            if not self._name_edit.text().strip():
                QMessageBox.warning(self, "Missing Name", "Please enter a name for the rule.")
                return

            if not self._table_combo.currentData():
                QMessageBox.warning(self, "No Table Selected", "Please select a table.")
                return

            if not self._field_combo.currentData():
                QMessageBox.warning(self, "No Field Selected", "Please select a field.")
                return

            if not self._error_message_edit.toPlainText().strip():
                QMessageBox.warning(self, "Missing Error Message", "Please enter an error message.")
                return

            # Validate rule-specific parameters
            rule_type = self._rule_type_combo.currentData()

            if rule_type == ValidationRuleType.RANGE:
                min_value = self._min_value_edit.text().strip()
                max_value = self._max_value_edit.text().strip()

                if not min_value and not max_value:
                    QMessageBox.warning(
                        self,
                        "Missing Range",
                        "Please enter at least one range limit (minimum or maximum)."
                    )
                    return

            elif rule_type == ValidationRuleType.PATTERN:
                if not self._pattern_edit.text().strip():
                    QMessageBox.warning(self, "Missing Pattern", "Please enter a pattern.")
                    return

                # Validate pattern is a valid regex
                try:
                    import re
                    re.compile(self._pattern_edit.text().strip())
                except re.error as e:
                    QMessageBox.warning(
                        self,
                        "Invalid Pattern",
                        f"The pattern is not a valid regular expression: {str(e)}"
                    )
                    return

            super().accept()

        except Exception as e:
            self._logger.error(f"Error in dialog accept: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

class ValidationResultDialog(QDialog):
    """Dialog for displaying validation results."""

    def __init__(self, plugin: Any, logger: Any, result: ValidationResult,
                 parent: Optional[QWidget] = None) -> None:
        """Initialize the validation result dialog.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            result: The validation result to display
            parent: The parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._result = result

        self._init_ui()
        self.setWindowTitle("Validation Results")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        main_layout = QVBoxLayout(self)

        # Result summary
        summary_group = QGroupBox("Validation Summary")
        summary_form = QFormLayout(summary_group)

        status_label = QLabel("Success" if self._result.success else "Failed")
        status_label.setStyleSheet(
            f"font-weight: bold; color: {'green' if self._result.success else 'red'}"
        )

        total_label = QLabel(f"{self._result.total_records}")
        failed_label = QLabel(f"{self._result.failed_records}")
        fail_percent = 0 if self._result.total_records == 0 else (
                self._result.failed_records / self._result.total_records * 100
        )
        percent_label = QLabel(f"{fail_percent:.2f}%")

        if self._result.validated_at:
            time_label = QLabel(self._result.validated_at.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            time_label = QLabel("Unknown")

        summary_form.addRow("Status:", status_label)
        summary_form.addRow("Total Records:", total_label)
        summary_form.addRow("Failed Records:", failed_label)
        summary_form.addRow("Failure Rate:", percent_label)
        summary_form.addRow("Validated At:", time_label)

        main_layout.addWidget(summary_group)

        # Failures table
        if self._result.failures:
            failures_group = QGroupBox("Validation Failures")
            failures_layout = QVBoxLayout(failures_group)

            self._failures_table = QTableWidget()
            self._failures_table.setColumnCount(3)
            self._failures_table.setHorizontalHeaderLabels(["Row", "Value", "Error"])
            self._failures_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self._failures_table.setAlternatingRowColors(True)

            # Populate failures
            self._failures_table.setRowCount(len(self._result.failures))
            for i, failure in enumerate(self._result.failures):
                row_item = QTableWidgetItem(str(failure.get('row', i)))

                # Format the value based on type
                value = failure.get('value')
                if value is None:
                    value_text = "NULL"
                elif isinstance(value, (dict, list)):
                    value_text = json.dumps(value)
                else:
                    value_text = str(value)

                value_item = QTableWidgetItem(value_text)
                error_item = QTableWidgetItem(failure.get('error', 'Unknown error'))

                self._failures_table.setItem(i, 0, row_item)
                self._failures_table.setItem(i, 1, value_item)
                self._failures_table.setItem(i, 2, error_item)

            failures_layout.addWidget(self._failures_table)

            # Export button
            export_button = QPushButton("Export Failures")
            export_button.clicked.connect(self._export_failures)
            failures_layout.addWidget(export_button)

            main_layout.addWidget(failures_group)
        else:
            # No failures message
            no_failures_label = QLabel("No validation failures found! All data passed validation.")
            no_failures_label.setStyleSheet("color: green; font-weight: bold; padding: 20px;")
            no_failures_label.setAlignment(Qt.AlignCenter)

            main_layout.addWidget(no_failures_label)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)

    def _export_failures(self) -> None:
        """Export validation failures to a file."""
        try:
            from PySide6.QtWidgets import QFileDialog
            import csv

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Validation Failures",
                "",
                "CSV Files (*.csv);;All Files (*.*)"
            )

            if not file_path:
                return

            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'

            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Row', 'Value', 'Error'])

                for failure in self._result.failures:
                    row = failure.get('row', '')
                    value = failure.get('value', '')
                    error = failure.get('error', 'Unknown error')

                    writer.writerow([row, value, error])

            QMessageBox.information(
                self,
                "Export Successful",
                f"Validation failures exported to {file_path}"
            )

        except Exception as e:
            self._logger.error(f"Failed to export failures: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export failures: {str(e)}")

class ValidationWidget(QWidget):
    """Widget for managing and running data validation rules."""

    def __init__(self, plugin: Any, logger: Any, parent: Optional[QWidget] = None) -> None:
        """Initialize the validation widget.

        Args:
            plugin: The database connector plugin instance
            logger: The logger instance
            parent: The parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._current_connection_id: Optional[str] = None
        self._validation_engine: Optional[Any] = None

        self._init_ui()

        # Get validation engine
        self._get_validation_engine()

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
        self._refresh_button.clicked.connect(self._refresh_rules)

        conn_layout.addWidget(conn_label)
        conn_layout.addWidget(self._connection_combo)
        conn_layout.addWidget(self._refresh_button)
        conn_layout.addStretch()

        main_layout.addLayout(conn_layout)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Rules list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        rules_label = QLabel("Validation Rules")
        rules_label.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(rules_label)

        self._rules_list = QListWidget()
        self._rules_list.itemSelectionChanged.connect(self._on_rule_selected)
        left_layout.addWidget(self._rules_list)

        # Rule actions
        rule_actions = QHBoxLayout()
        self._new_rule_button = QPushButton("New")
        self._new_rule_button.clicked.connect(self._create_new_rule)

        self._edit_rule_button = QPushButton("Edit")
        self._edit_rule_button.clicked.connect(self._edit_current_rule)
        self._edit_rule_button.setEnabled(False)

        self._delete_rule_button = QPushButton("Delete")
        self._delete_rule_button.clicked.connect(self._delete_current_rule)
        self._delete_rule_button.setEnabled(False)

        rule_actions.addWidget(self._new_rule_button)
        rule_actions.addWidget(self._edit_rule_button)
        rule_actions.addWidget(self._delete_rule_button)

        left_layout.addLayout(rule_actions)

        splitter.addWidget(left_widget)

        # Right panel - Rule details and execution
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Rule details section
        details_group = QGroupBox("Rule Details")
        details_form = QFormLayout(details_group)

        self._rule_name_label = QLabel("")
        self._rule_description_label = QLabel("")
        self._rule_table_label = QLabel("")
        self._rule_field_label = QLabel("")
        self._rule_type_label = QLabel("")
        self._rule_status_label = QLabel("")

        details_form.addRow("Name:", self._rule_name_label)
        details_form.addRow("Description:", self._rule_description_label)
        details_form.addRow("Table:", self._rule_table_label)
        details_form.addRow("Field:", self._rule_field_label)
        details_form.addRow("Type:", self._rule_type_label)
        details_form.addRow("Status:", self._rule_status_label)

        right_layout.addWidget(details_group)

        # Validation execution section
        execution_group = QGroupBox("Run Validation")
        execution_layout = QVBoxLayout(execution_group)

        # Table selection (if different from rule table)
        self._use_rule_table_check = QCheckBox("Use rule's table")
        self._use_rule_table_check.setChecked(True)
        self._use_rule_table_check.stateChanged.connect(self._on_use_rule_table_changed)

        table_layout = QHBoxLayout()
        table_label = QLabel("Table:")
        self._table_combo = QComboBox()
        self._table_combo.setEnabled(False)

        table_layout.addWidget(table_label)
        table_layout.addWidget(self._table_combo)

        execution_layout.addWidget(self._use_rule_table_check)
        execution_layout.addLayout(table_layout)

        # Limit records
        limit_layout = QHBoxLayout()
        limit_label = QLabel("Limit records:")
        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(0, 100000)
        self._limit_spin.setValue(1000)
        self._limit_spin.setSpecialValueText("No limit")

        limit_layout.addWidget(limit_label)
        limit_layout.addWidget(self._limit_spin)
        limit_layout.addStretch()

        execution_layout.addLayout(limit_layout)

        # Run button
        self._run_button = QPushButton("Run Validation")
        self._run_button.clicked.connect(self._run_validation)
        self._run_button.setEnabled(False)

        execution_layout.addWidget(self._run_button)

        right_layout.addWidget(execution_group)

        # Results section
        results_group = QGroupBox("Results History")
        results_layout = QVBoxLayout(results_group)

        self._results_list = QListWidget()
        self._results_list.itemDoubleClicked.connect(self._view_result)

        results_layout.addWidget(self._results_list)

        # Results actions
        results_actions = QHBoxLayout()
        self._view_result_button = QPushButton("View")
        self._view_result_button.clicked.connect(self._view_selected_result)
        self._view_result_button.setEnabled(False)

        self._delete_result_button = QPushButton("Delete")
        self._delete_result_button.clicked.connect(self._delete_selected_result)
        self._delete_result_button.setEnabled(False)

        results_actions.addWidget(self._view_result_button)
        results_actions.addWidget(self._delete_result_button)
        results_actions.addStretch()

        results_layout.addLayout(results_actions)

        right_layout.addWidget(results_group)

        splitter.addWidget(right_widget)

        # Set initial splitter sizes
        splitter.setSizes([200, 400])

        main_layout.addWidget(splitter)

        # Status bar
        status_layout = QHBoxLayout()
        self._status_label = QLabel("Ready")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate progress
        self._progress_bar.setVisible(False)

        status_layout.addWidget(self._status_label)
        status_layout.addWidget(self._progress_bar)

        main_layout.addLayout(status_layout)

    def _get_validation_engine(self) -> None:
        """Get the validation engine from the plugin."""
        asyncio.create_task(self._async_get_validation_engine())

    async def _async_get_validation_engine(self) -> None:
        """Asynchronously get the validation engine."""
        try:
            self._validation_engine = await self._plugin.get_validation_engine()
            await self._load_connections()
        except Exception as e:
            self._logger.error(f"Failed to get validation engine: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")

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
            self._status_label.setText(f"Error: {str(e)}")

    def set_connection_status(self, connection_id: str, connected: bool) -> None:
        """Update the UI based on connection status changes.

        Args:
            connection_id: The connection ID
            connected: Whether the connection is active
        """
        if connection_id == self._current_connection_id:
            self._new_rule_button.setEnabled(connected)
            self._run_button.setEnabled(connected and bool(self._rules_list.selectedItems()))

            if not connected:
                self._clear_rule_details()
                self._edit_rule_button.setEnabled(False)
                self._delete_rule_button.setEnabled(False)
                self._rules_list.clear()
                self._results_list.clear()

    async def refresh(self) -> None:
        """Refresh the validation rules list."""
        await self._load_connections()
        if self._current_connection_id:
            await self._load_rules()

    def _on_connection_selected(self, index: int) -> None:
        """Handle connection selection change.

        Args:
            index: The selected index in the combobox
        """
        connection_id = self._connection_combo.itemData(index)
        self._current_connection_id = connection_id

        self._clear_rule_details()
        self._rules_list.clear()
        self._results_list.clear()

        # Check if connection is active
        is_connected = False
        if connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[connection_id]
            is_connected = connector.is_connected

        self._new_rule_button.setEnabled(is_connected)

        if connection_id and is_connected:
            asyncio.create_task(self._load_rules())
            asyncio.create_task(self._load_tables())

    async def _load_rules(self) -> None:
        """Load validation rules for the current connection."""
        if not self._current_connection_id or not self._validation_engine:
            return

        try:
            self._status_label.setText("Loading validation rules...")
            self._progress_bar.setVisible(True)

            rules = await self._validation_engine.get_all_rules(self._current_connection_id)

            self._rules_list.clear()

            for rule in sorted(rules, key=lambda r: r.name.lower()):
                item_text = rule.name
                if rule.description:
                    item_text += f" - {rule.description}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, rule.id)

                # Visual indicator for active/inactive rules
                if not rule.active:
                    item.setForeground(QBrush(QColor(120, 120, 120)))  # Gray for inactive rules

                self._rules_list.addItem(item)

            self._status_label.setText(f"Loaded {len(rules)} validation rules")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to load rules: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to load rules: {str(e)}")

    async def _load_tables(self) -> None:
        """Load tables for the current connection."""
        if not self._current_connection_id:
            return

        try:
            connector = await self._plugin.get_connector(self._current_connection_id)
            tables = await connector.get_tables()

            self._table_combo.clear()

            for table in sorted(tables, key=lambda t: t.name.lower()):
                self._table_combo.addItem(table.name, table.name)

        except Exception as e:
            self._logger.error(f"Failed to load tables: {str(e)}")

    def _on_rule_selected(self) -> None:
        """Handle rule selection change."""
        selected_items = self._rules_list.selectedItems()

        if not selected_items:
            self._clear_rule_details()
            self._edit_rule_button.setEnabled(False)
            self._delete_rule_button.setEnabled(False)
            self._run_button.setEnabled(False)
            return

        rule_id = selected_items[0].data(Qt.UserRole)

        self._edit_rule_button.setEnabled(True)
        self._delete_rule_button.setEnabled(True)

        # Check if connection is active
        is_connected = False
        if self._current_connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[self._current_connection_id]
            is_connected = connector.is_connected

        self._run_button.setEnabled(is_connected)

        asyncio.create_task(self._load_rule_details(rule_id))
        asyncio.create_task(self._load_rule_results(rule_id))

    async def _load_rule_details(self, rule_id: str) -> None:
        """Load and display rule details.

        Args:
            rule_id: The ID of the rule to display
        """
        if not self._validation_engine:
            return

        try:
            rule = await self._validation_engine.get_rule(rule_id)
            if not rule:
                self._clear_rule_details()
                return

            # Update rule details
            self._rule_name_label.setText(rule.name)
            self._rule_description_label.setText(rule.description or "")
            self._rule_table_label.setText(rule.table_name)
            self._rule_field_label.setText(rule.field_name)
            self._rule_type_label.setText(self._get_rule_type_name(rule.rule_type))

            status_text = "Active" if rule.active else "Inactive"
            status_color = "green" if rule.active else "red"
            self._rule_status_label.setText(status_text)
            self._rule_status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")

            # Update table combo if 'use rule table' is checked
            if self._use_rule_table_check.isChecked():
                # Find and select the rule's table
                for i in range(self._table_combo.count()):
                    if self._table_combo.itemData(i) == rule.table_name:
                        self._table_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f"Failed to load rule details: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")

    async def _load_rule_results(self, rule_id: str) -> None:
        """Load validation results for the selected rule.

        Args:
            rule_id: The ID of the rule to load results for
        """
        if not self._validation_engine:
            return

        try:
            results = await self._validation_engine.get_validation_results(rule_id)

            self._results_list.clear()
            self._view_result_button.setEnabled(False)
            self._delete_result_button.setEnabled(False)

            for result in results:
                status = "Success" if result.success else "Failed"
                time_str = result.validated_at.strftime("%Y-%m-%d %H:%M:%S")

                item_text = f"{time_str} - {status} ({result.failed_records}/{result.total_records} failed)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, result)

                # Visual indicator for success/failure
                if result.success:
                    item.setForeground(QBrush(QColor(0, 128, 0)))  # Green for success
                else:
                    item.setForeground(QBrush(QColor(255, 0, 0)))  # Red for failure

                self._results_list.addItem(item)

        except Exception as e:
            self._logger.error(f"Failed to load validation results: {str(e)}")

    def _clear_rule_details(self) -> None:
        """Clear the rule details display."""
        self._rule_name_label.setText("")
        self._rule_description_label.setText("")
        self._rule_table_label.setText("")
        self._rule_field_label.setText("")
        self._rule_type_label.setText("")
        self._rule_status_label.setText("")
        self._results_list.clear()

    def _refresh_rules(self) -> None:
        """Refresh the rules list."""
        if self._current_connection_id:
            is_connected = False
            if self._current_connection_id in self._plugin._active_connectors:
                connector = self._plugin._active_connectors[self._current_connection_id]
                is_connected = connector.is_connected

            if is_connected:
                asyncio.create_task(self._load_rules())

    def _create_new_rule(self) -> None:
        """Create a new validation rule."""
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
                                "Please connect to the database before creating a rule.")
            return

        dialog = RuleDialog(self._plugin, self._logger, self._current_connection_id, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                rule = dialog.get_rule()
                asyncio.create_task(self._save_rule(rule))
            except Exception as e:
                self._logger.error(f"Failed to create rule: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to create rule: {str(e)}")

    def _edit_current_rule(self) -> None:
        """Edit the currently selected rule."""
        selected_items = self._rules_list.selectedItems()
        if not selected_items:
            return

        rule_id = selected_items[0].data(Qt.UserRole)

        asyncio.create_task(self._edit_rule(rule_id))

    async def _edit_rule(self, rule_id: str) -> None:
        """Edit a validation rule.

        Args:
            rule_id: The ID of the rule to edit
        """
        if not self._validation_engine:
            return

        try:
            rule = await self._validation_engine.get_rule(rule_id)
            if not rule:
                QMessageBox.warning(self, "Rule Not Found", "The selected rule could not be found.")
                return

            dialog = RuleDialog(self._plugin, self._logger, self._current_connection_id, self, rule)
            if dialog.exec() == QDialog.Accepted:
                updated_rule = dialog.get_rule()
                await self._save_rule(updated_rule)

        except Exception as e:
            self._logger.error(f"Failed to edit rule: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to edit rule: {str(e)}")

    def _delete_current_rule(self) -> None:
        """Delete the currently selected rule."""
        selected_items = self._rules_list.selectedItems()
        if not selected_items:
            return

        rule_id = selected_items[0].data(Qt.UserRole)
        rule_name = selected_items[0].text().split(" - ")[0]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the rule '{rule_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            asyncio.create_task(self._delete_rule(rule_id))

    async def _save_rule(self, rule: ValidationRule) -> None:
        """Save a validation rule.

        Args:
            rule: The rule to save
        """
        if not self._validation_engine:
            return

        try:
            self._status_label.setText("Saving rule...")
            self._progress_bar.setVisible(True)

            # Save based on whether it's a new or existing rule
            if hasattr(self._validation_engine, 'get_rule'):
                existing_rule = await self._validation_engine.get_rule(rule.id)
                if existing_rule:
                    await self._validation_engine.update_rule(rule)
                else:
                    await self._validation_engine.create_rule(rule)
            else:
                # Fallback if engine doesn't have get_rule method
                try:
                    await self._validation_engine.update_rule(rule)
                except:
                    await self._validation_engine.create_rule(rule)

            await self._load_rules()

            # Select the saved rule
            for i in range(self._rules_list.count()):
                item = self._rules_list.item(i)
                if item and item.data(Qt.UserRole) == rule.id:
                    self._rules_list.setCurrentItem(item)
                    break

            self._status_label.setText("Rule saved successfully")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to save rule: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to save rule: {str(e)}")

    async def _delete_rule(self, rule_id: str) -> None:
        """Delete a validation rule.

        Args:
            rule_id: The ID of the rule to delete
        """
        if not self._validation_engine:
            return

        try:
            self._status_label.setText("Deleting rule...")
            self._progress_bar.setVisible(True)

            await self._validation_engine.delete_rule(rule_id)

            self._clear_rule_details()
            await self._load_rules()

            self._status_label.setText("Rule deleted successfully")
            self._progress_bar.setVisible(False)

        except Exception as e:
            self._logger.error(f"Failed to delete rule: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to delete rule: {str(e)}")

    def _on_use_rule_table_changed(self, state: int) -> None:
        """Handle changes to the 'use rule table' checkbox.

        Args:
            state: The checkbox state
        """
        use_rule_table = state == Qt.Checked
        self._table_combo.setEnabled(not use_rule_table)

        # If checked and we have a rule selected, set the table combo to the rule's table
        if use_rule_table:
            table_name = self._rule_table_label.text()
            if table_name:
                for i in range(self._table_combo.count()):
                    if self._table_combo.itemData(i) == table_name:
                        self._table_combo.setCurrentIndex(i)
                        break

    def _run_validation(self) -> None:
        """Run validation for the selected rule."""
        selected_items = self._rules_list.selectedItems()
        if not selected_items:
            return

        rule_id = selected_items[0].data(Qt.UserRole)

        # Get table name
        if self._use_rule_table_check.isChecked():
            table_name = self._rule_table_label.text()
        else:
            table_name = self._table_combo.currentData()

        if not table_name:
            QMessageBox.warning(self, "No Table", "Please select a table to validate.")
            return

        # Get limit
        limit = self._limit_spin.value() if self._limit_spin.value() > 0 else None

        asyncio.create_task(self._run_validation_task(rule_id, table_name, limit))

    async def _run_validation_task(self, rule_id: str, table_name: str, limit: Optional[int]) -> None:
        """Run a validation task.

        Args:
            rule_id: The ID of the rule to run
            table_name: The table to validate
            limit: Optional record limit
        """
        if not self._validation_engine or not self._current_connection_id:
            return

        try:
            self._status_label.setText(f"Running validation on {table_name}...")
            self._progress_bar.setVisible(True)
            self._run_button.setEnabled(False)

            # Get the rule
            rule = await self._validation_engine.get_rule(rule_id)
            if not rule:
                raise ValueError("Rule not found")

            # Get data to validate
            connector = await self._plugin.get_connector(self._current_connection_id)
            query = f"SELECT {rule.field_name} FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"

            data = await connector.execute_query(query)

            # Run validation
            result = await self._validation_engine.validate_data(rule, data)

            # Display result
            dialog = ValidationResultDialog(self._plugin, self._logger, result, self)
            dialog.exec()

            # Refresh results
            await self._load_rule_results(rule_id)

            self._status_label.setText("Validation complete")
            self._progress_bar.setVisible(False)
            self._run_button.setEnabled(True)

        except Exception as e:
            self._logger.error(f"Failed to run validation: {str(e)}")
            self._status_label.setText(f"Error: {str(e)}")
            self._progress_bar.setVisible(False)
            self._run_button.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Failed to run validation: {str(e)}")

    def _view_selected_result(self) -> None:
        """View the selected validation result."""
        selected_items = self._results_list.selectedItems()
        if not selected_items:
            return

        result = selected_items[0].data(Qt.UserRole)
        dialog = ValidationResultDialog(self._plugin, self._logger, result, self)
        dialog.exec()

    def _view_result(self, item: QListWidgetItem) -> None:
        """View a validation result from the list.

        Args:
            item: The list item that was clicked
        """
        result = item.data(Qt.UserRole)
        dialog = ValidationResultDialog(self._plugin, self._logger, result, self)
        dialog.exec()

    def _delete_selected_result(self) -> None:
        """Delete the selected validation result."""
        # This would typically call a method on the validation engine to delete the result
        # For now, just remove from the list
        selected_items = self._results_list.selectedItems()
        if not selected_items:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this validation result?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._results_list.takeItem(self._results_list.row(selected_items[0]))
            self._view_result_button.setEnabled(False)
            self._delete_result_button.setEnabled(False)

    def _get_rule_type_name(self, rule_type: ValidationRuleType) -> str:
        """Get a user-friendly name for a rule type.

        Args:
            rule_type: The rule type

        Returns:
            A user-friendly name for the rule type
        """
        return {
            ValidationRuleType.RANGE: "Range Check",
            ValidationRuleType.PATTERN: "Pattern Match",
            ValidationRuleType.NOT_NULL: "Not Null",
            ValidationRuleType.UNIQUE: "Unique Values",
            ValidationRuleType.LENGTH: "Length Check",
            ValidationRuleType.REFERENCE: "Reference Check",
            ValidationRuleType.ENUMERATION: "Enumeration Check",
            ValidationRuleType.CUSTOM: "Custom Expression",
        }.get(rule_type, str(rule_type))