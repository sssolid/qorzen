from __future__ import annotations

"""
Template manager dialog for the InitialDB application.

This module provides a dialog for managing data export templates,
allowing users to create, edit, and delete templates.
"""

import os
import json
from typing import Dict, Optional
import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QListWidget, QListWidgetItem, QDialogButtonBox,
    QSplitter, QLineEdit, QMessageBox, QInputDialog,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout
)

from ...services.export_service import TemplateManager, FieldMapping

logger = structlog.get_logger(__name__)


class TemplateManagerDialog(QDialog):
    """Dialog for managing export templates."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the template manager dialog.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.setWindowTitle('Template Manager')
        self.resize(900, 700)
        self.template_manager = TemplateManager()
        self.templates = self.template_manager.templates.copy()
        self.current_template: Optional[str] = None
        self.current_template_data: Optional[Dict[str, FieldMapping]] = None
        self.modified = False
        self._init_ui()
        self._populate_template_list()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (template list and actions)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        left_layout.addWidget(QLabel('Available Templates:'))
        left_layout.addWidget(self.template_list)

        # Template action buttons
        template_actions = QHBoxLayout()
        self.new_btn = QPushButton('New')
        self.new_btn.clicked.connect(self._create_new_template)
        template_actions.addWidget(self.new_btn)

        self.rename_btn = QPushButton('Rename')
        self.rename_btn.clicked.connect(self._rename_template)
        self.rename_btn.setEnabled(False)
        template_actions.addWidget(self.rename_btn)

        self.duplicate_btn = QPushButton('Duplicate')
        self.duplicate_btn.clicked.connect(self._duplicate_template)
        self.duplicate_btn.setEnabled(False)
        template_actions.addWidget(self.duplicate_btn)

        self.delete_btn = QPushButton('Delete')
        self.delete_btn.clicked.connect(self._delete_template)
        self.delete_btn.setEnabled(False)
        template_actions.addWidget(self.delete_btn)

        left_layout.addLayout(template_actions)

        # Import/export buttons
        import_export = QHBoxLayout()
        self.import_btn = QPushButton('Import...')
        self.import_btn.clicked.connect(self._import_template)
        import_export.addWidget(self.import_btn)

        self.export_btn = QPushButton('Export...')
        self.export_btn.clicked.connect(self._export_template)
        self.export_btn.setEnabled(False)
        import_export.addWidget(self.export_btn)

        left_layout.addLayout(import_export)

        # Right panel (template details and mappings)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Template details section
        details_group = QGroupBox('Template Details')
        details_layout = QFormLayout(details_group)

        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        details_layout.addRow('Name:', self.name_edit)

        self.description_edit = QLineEdit()
        self.description_edit.textChanged.connect(self._mark_as_modified)
        details_layout.addRow('Description:', self.description_edit)

        right_layout.addWidget(details_group)

        # Field mappings section
        mapping_group = QGroupBox('Field Mappings')
        mapping_layout = QVBoxLayout(mapping_group)

        self.mapping_table = QTableWidget(0, 3)
        self.mapping_table.setHorizontalHeaderLabels(['Field Name', 'Model', 'Attribute'])
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.cellChanged.connect(self._on_mapping_changed)
        self.mapping_table.itemSelectionChanged.connect(self._update_field_buttons)

        mapping_layout.addWidget(self.mapping_table)

        # Table action buttons
        table_actions = QHBoxLayout()

        self.add_field_btn = QPushButton('Add Field')
        self.add_field_btn.clicked.connect(self._add_field)
        self.add_field_btn.setEnabled(False)
        table_actions.addWidget(self.add_field_btn)

        self.delete_field_btn = QPushButton('Delete Field')
        self.delete_field_btn.clicked.connect(self._delete_field)
        self.delete_field_btn.setEnabled(False)
        table_actions.addWidget(self.delete_field_btn)

        self.move_up_btn = QPushButton('Move Up')
        self.move_up_btn.clicked.connect(lambda: self._move_field(-1))
        self.move_up_btn.setEnabled(False)
        table_actions.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton('Move Down')
        self.move_down_btn.clicked.connect(lambda: self._move_field(1))
        self.move_down_btn.setEnabled(False)
        table_actions.addWidget(self.move_down_btn)

        mapping_layout.addLayout(table_actions)
        right_layout.addWidget(mapping_group)

        # Add panels to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 600])
        layout.addWidget(splitter)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('Save')
        self.save_btn.clicked.connect(self._save_changes)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self._handle_close)
        btn_layout.addWidget(button_box)

        layout.addLayout(btn_layout)

    def _populate_template_list(self) -> None:
        """Populate the template list with available templates."""
        self.template_list.clear()
        for name in sorted(self.templates.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.template_list.addItem(item)

        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)

    def _on_template_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """
        Handle template selection change.

        Args:
            current: The currently selected item
            previous: The previously selected item
        """
        if self.modified and previous is not None:
            save_result = QMessageBox.question(
                self, 'Save Changes',
                f"Save changes to template '{self.current_template}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if save_result == QMessageBox.StandardButton.Yes:
                self._save_changes()
            elif save_result == QMessageBox.StandardButton.Cancel:
                self.template_list.setCurrentItem(previous)
                return

        if current:
            template_name = current.data(Qt.ItemDataRole.UserRole)
            self.current_template = template_name
            self.current_template_data = self.templates.get(template_name, {}).copy()

            self.rename_btn.setEnabled(True)
            self.duplicate_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.add_field_btn.setEnabled(True)

            self.name_edit.setText(template_name)
            self.description_edit.setText('')

            self._update_mapping_table()
        else:
            self.current_template = None
            self.current_template_data = None

            self.rename_btn.setEnabled(False)
            self.duplicate_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.add_field_btn.setEnabled(False)
            self.delete_field_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            self.save_btn.setEnabled(False)

            self.name_edit.setText('')
            self.description_edit.setText('')
            self.mapping_table.setRowCount(0)

        self.modified = False

    def _update_mapping_table(self) -> None:
        """Update the mapping table with current template data."""
        self.mapping_table.blockSignals(True)
        self.mapping_table.setRowCount(0)

        if not self.current_template_data:
            self.mapping_table.blockSignals(False)
            return

        for row, (field_name, mapping) in enumerate(self.current_template_data.items()):
            self.mapping_table.insertRow(row)

            # Field name column
            field_item = QTableWidgetItem(field_name)
            self.mapping_table.setItem(row, 0, field_item)

            # Create a selector widget for model and attribute
            model_value = mapping.get('model', '')
            attribute_value = mapping.get('attribute', '')

            # Add model and attribute as text items initially
            model_item = QTableWidgetItem(model_value if model_value else '')
            self.mapping_table.setItem(row, 1, model_item)

            attribute_item = QTableWidgetItem(attribute_value if attribute_value else '')
            self.mapping_table.setItem(row, 2, attribute_item)

            # Create and set the field selector for this row when the user clicks
            self.mapping_table.cellClicked.connect(lambda r, c: self._show_field_selector(r, c))

        self.mapping_table.blockSignals(False)
        self._update_field_buttons()

    def _show_field_selector(self, row: int, column: int) -> None:
        """
        Show the field selector when a model or attribute cell is clicked.

        Args:
            row: The clicked row
            column: The clicked column
        """
        # Only show field selector for model or attribute columns
        if column != 1 and column != 2:
            return

        # Get the current field name, model and attribute values
        field_item = self.mapping_table.item(row, 0)
        model_item = self.mapping_table.item(row, 1)
        attribute_item = self.mapping_table.item(row, 2)

        if not field_item:
            return

        field_name = field_item.text()
        model_value = model_item.text() if model_item else ''
        attribute_value = attribute_item.text() if attribute_item else ''

        # Create a field selector dialog
        from ...ui.template_manager.template_field_selector import FieldSelectorDialog

        selector_dialog = FieldSelectorDialog(
            self,
            initial_model=model_value,
            initial_attribute=attribute_value
        )
        selector_dialog.setWindowTitle(f"Select Field Mapping for '{field_name}'")

        # If the dialog is accepted, update the cell values
        if selector_dialog.exec() == QDialog.DialogCode.Accepted:
            model, attribute = selector_dialog.get_values()

            self.mapping_table.blockSignals(True)

            if model_item:
                model_item.setText(model)
            else:
                model_item = QTableWidgetItem(model)
                self.mapping_table.setItem(row, 1, model_item)

            if attribute_item:
                attribute_item.setText(attribute)
            else:
                attribute_item = QTableWidgetItem(attribute)
                self.mapping_table.setItem(row, 2, attribute_item)

            self.mapping_table.blockSignals(False)

            # Update the underlying data
            if field_name in self.current_template_data:
                self.current_template_data[field_name]['model'] = model if model else None
                self.current_template_data[field_name]['attribute'] = attribute if attribute else None
                self._mark_as_modified()

    def _update_field_buttons(self) -> None:
        """Update the state of the field-related buttons based on the current selection."""
        has_selection = len(self.mapping_table.selectedItems()) > 0
        has_rows = self.mapping_table.rowCount() > 0

        self.delete_field_btn.setEnabled(has_selection)
        self.move_up_btn.setEnabled(has_selection and has_rows > 1)
        self.move_down_btn.setEnabled(has_selection and has_rows > 1)

    def _on_mapping_changed(self, row: int, column: int) -> None:
        """
        Handle changes to the mapping table cells.

        Args:
            row: The changed row
            column: The changed column
        """
        if not self.current_template or not self.current_template_data:
            return

        field_names = []
        for r in range(self.mapping_table.rowCount()):
            field_item = self.mapping_table.item(r, 0)
            if field_item:
                field_names.append(field_item.text())

        updated_data = {}
        for r in range(self.mapping_table.rowCount()):
            field_item = self.mapping_table.item(r, 0)
            model_item = self.mapping_table.item(r, 1)
            attribute_item = self.mapping_table.item(r, 2)

            if field_item and field_item.text():
                field_name = field_item.text()
                model = model_item.text() if model_item else ''
                attribute = attribute_item.text() if attribute_item else ''

                updated_data[field_name] = {
                    'model': model if model else None,
                    'attribute': attribute if attribute else None
                }

        self.current_template_data = updated_data
        self._mark_as_modified()
        self._update_field_buttons()

    def _add_field(self) -> None:
        """Add a new field to the template."""
        if not self.current_template_data:
            return

        base_name = 'NewField'
        field_name = base_name
        counter = 1

        while field_name in self.current_template_data:
            field_name = f'{base_name}{counter}'
            counter += 1

        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)

        field_item = QTableWidgetItem(field_name)
        self.mapping_table.setItem(row, 0, field_item)

        model_item = QTableWidgetItem('')
        self.mapping_table.setItem(row, 1, model_item)

        attribute_item = QTableWidgetItem('')
        self.mapping_table.setItem(row, 2, attribute_item)

        self.mapping_table.selectRow(row)
        self.current_template_data[field_name] = {'model': None, 'attribute': None}

        self._mark_as_modified()
        self._update_field_buttons()

        # Immediately show the field selector for the new row
        self._show_field_selector(row, 1)

    def _delete_field(self) -> None:
        """Delete the selected field(s) from the template."""
        if not self.current_template_data:
            return

        selected_rows = set(index.row() for index in self.mapping_table.selectedIndexes())
        if not selected_rows:
            return

        if len(selected_rows) > 1:
            confirm = QMessageBox.question(
                self, 'Confirm Deletion',
                f'Delete {len(selected_rows)} fields?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:
            row = list(selected_rows)[0]
            field_item = self.mapping_table.item(row, 0)
            field_name = field_item.text() if field_item else 'this field'
            confirm = QMessageBox.question(
                self, 'Confirm Deletion',
                f"Delete field '{field_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        for row in sorted(selected_rows, reverse=True):
            field_item = self.mapping_table.item(row, 0)
            if field_item and field_item.text() in self.current_template_data:
                del self.current_template_data[field_item.text()]
            self.mapping_table.removeRow(row)

        self._mark_as_modified()
        self._update_field_buttons()

    def _move_field(self, direction: int) -> None:
        """
        Move the selected field up or down.

        Args:
            direction: The direction to move (-1 for up, 1 for down)
        """
        if not self.current_template_data:
            return

        selected_rows = set(index.row() for index in self.mapping_table.selectedIndexes())
        if len(selected_rows) != 1:
            return

        row = list(selected_rows)[0]
        target_row = row + direction

        if target_row < 0 or target_row >= self.mapping_table.rowCount():
            return

        self.mapping_table.blockSignals(True)

        # Swap the data in the table
        for col in range(self.mapping_table.columnCount()):
            current_item = self.mapping_table.takeItem(row, col)
            target_item = self.mapping_table.takeItem(target_row, col)

            self.mapping_table.setItem(target_row, col, current_item)
            self.mapping_table.setItem(row, col, target_item)

        self.mapping_table.blockSignals(False)

        # Update the selection
        self.mapping_table.clearSelection()
        self.mapping_table.selectRow(target_row)

        # Update the internal data structure
        new_template_data = {}
        for r in range(self.mapping_table.rowCount()):
            field_item = self.mapping_table.item(r, 0)
            model_item = self.mapping_table.item(r, 1)
            attribute_item = self.mapping_table.item(r, 2)

            if field_item and field_item.text():
                field_name = field_item.text()
                model = model_item.text() if model_item else ''
                attribute = attribute_item.text() if attribute_item else ''

                new_template_data[field_name] = {
                    'model': model if model else None,
                    'attribute': attribute if attribute else None
                }

        self.current_template_data = new_template_data
        self._mark_as_modified()

    def _mark_as_modified(self) -> None:
        """Mark the current template as modified and enable the save button."""
        self.modified = True
        self.save_btn.setEnabled(True)

    def _save_changes(self) -> None:
        """Save changes to the current template."""
        if not self.current_template or not self.current_template_data:
            return

        try:
            os.makedirs(TEMPLATES_DIR, exist_ok=True)
            template_path = os.path.join(TEMPLATES_DIR, f'{self.current_template}.json')

            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_template_data, f, indent=2)

            self.templates[self.current_template] = self.current_template_data
            self.template_manager = TemplateManager()

            self.modified = False
            self.save_btn.setEnabled(False)

            QMessageBox.information(
                self, 'Save Successful',
                f"Template '{self.current_template}' saved successfully."
            )
        except Exception as e:
            logger.error(f'Error saving template: {str(e)}')
            QMessageBox.critical(
                self, 'Save Error',
                f"Error saving template '{self.current_template}':\n{str(e)}"
            )

    def _create_new_template(self) -> None:
        """Create a new template."""
        if self.modified:
            save_result = QMessageBox.question(
                self, 'Save Changes',
                f"Save changes to template '{self.current_template}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if save_result == QMessageBox.StandardButton.Yes:
                self._save_changes()
            elif save_result == QMessageBox.StandardButton.Cancel:
                return

        name, ok = QInputDialog.getText(
            self, 'New Template',
            'Enter template name:',
            QLineEdit.EchoMode.Normal
        )

        if not ok or not name:
            return

        if name in self.templates:
            confirm = QMessageBox.question(
                self, 'Template Exists',
                f"Template '{name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        self.templates[name] = {}
        self.current_template = name
        self.current_template_data = {}
        self.modified = True

        self._populate_template_list()

        # Select the new template in the list
        for i in range(self.template_list.count()):
            item = self.template_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                self.template_list.setCurrentItem(item)
                break

        self.name_edit.setText(name)
        self.description_edit.setText('')
        self.mapping_table.setRowCount(0)
        self.save_btn.setEnabled(True)
        self.add_field_btn.setEnabled(True)

    def _rename_template(self) -> None:
        """Rename the current template."""
        if not self.current_template:
            return

        new_name, ok = QInputDialog.getText(
            self, 'Rename Template',
            'Enter new name:',
            QLineEdit.EchoMode.Normal,
            self.current_template
        )

        if not ok or not new_name or new_name == self.current_template:
            return

        if new_name in self.templates:
            confirm = QMessageBox.question(
                self, 'Template Exists',
                f"Template '{new_name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        try:
            old_path = os.path.join(TEMPLATES_DIR, f'{self.current_template}.json')
            new_path = os.path.join(TEMPLATES_DIR, f'{new_name}.json')

            with open(new_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_template_data, f, indent=2)

            if os.path.exists(old_path):
                os.remove(old_path)

            self.templates[new_name] = self.current_template_data
            if self.current_template in self.templates:
                del self.templates[self.current_template]

            self.current_template = new_name
            self.name_edit.setText(new_name)

            self._populate_template_list()

            # Select the renamed template in the list
            for i in range(self.template_list.count()):
                item = self.template_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == new_name:
                    self.template_list.setCurrentItem(item)
                    break

            self.template_manager = TemplateManager()
            self.modified = False
            self.save_btn.setEnabled(False)
        except Exception as e:
            logger.error(f'Error renaming template: {str(e)}')
            QMessageBox.critical(
                self, 'Rename Error',
                f"Error renaming template to '{new_name}':\n{str(e)}"
            )

    def _duplicate_template(self) -> None:
        """Create a duplicate of the current template."""
        if not self.current_template or not self.current_template_data:
            return

        new_name, ok = QInputDialog.getText(
            self, 'Duplicate Template',
            'Enter name for duplicate:',
            QLineEdit.EchoMode.Normal,
            f'Copy of {self.current_template}'
        )

        if not ok or not new_name:
            return

        if new_name in self.templates:
            confirm = QMessageBox.question(
                self, 'Template Exists',
                f"Template '{new_name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        try:
            self.templates[new_name] = self.current_template_data.copy()
            template_path = os.path.join(TEMPLATES_DIR, f'{new_name}.json')

            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_template_data, f, indent=2)

            self._populate_template_list()

            # Select the new template in the list
            for i in range(self.template_list.count()):
                item = self.template_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == new_name:
                    self.template_list.setCurrentItem(item)
                    break

            self.template_manager = TemplateManager()
        except Exception as e:
            logger.error(f'Error duplicating template: {str(e)}')
            QMessageBox.critical(
                self, 'Duplication Error',
                f"Error duplicating template to '{new_name}':\n{str(e)}"
            )

    def _delete_template(self) -> None:
        """Delete the current template."""
        if not self.current_template:
            return

        confirm = QMessageBox.question(
            self, 'Confirm Deletion',
            f"Delete template '{self.current_template}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            template_path = os.path.join(TEMPLATES_DIR, f'{self.current_template}.json')
            if os.path.exists(template_path):
                os.remove(template_path)

            if self.current_template in self.templates:
                del self.templates[self.current_template]

            self.current_template = None
            self.current_template_data = None
            self.modified = False

            self._populate_template_list()

            self.name_edit.setText('')
            self.description_edit.setText('')
            self.mapping_table.setRowCount(0)

            self.rename_btn.setEnabled(False)
            self.duplicate_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.add_field_btn.setEnabled(False)
            self.delete_field_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            self.save_btn.setEnabled(False)

            self.template_manager = TemplateManager()
        except Exception as e:
            logger.error(f'Error deleting template: {str(e)}')
            QMessageBox.critical(
                self, 'Deletion Error',
                f"Error deleting template '{self.current_template}':\n{str(e)}"
            )

    def _import_template(self) -> None:
        """Import a template from a file."""
        if self.modified:
            save_result = QMessageBox.question(
                self, 'Save Changes',
                f"Save changes to template '{self.current_template}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if save_result == QMessageBox.StandardButton.Yes:
                self._save_changes()
            elif save_result == QMessageBox.StandardButton.Cancel:
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import Template', '', 'JSON Files (*.json)'
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)

            if not isinstance(template_data, dict):
                raise ValueError('Invalid template format: not a dictionary')

            base_name = os.path.basename(file_path)
            name = os.path.splitext(base_name)[0]

            if name in self.templates:
                name, ok = QInputDialog.getText(
                    self, 'Template Name',
                    f"A template named '{name}' already exists.\nEnter a new name or confirm overwrite:",
                    QLineEdit.EchoMode.Normal,
                    name
                )
                if not ok or not name:
                    return

            self.templates[name] = template_data
            self.current_template = name
            self.current_template_data = template_data

            template_path = os.path.join(TEMPLATES_DIR, f'{name}.json')
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2)

            self._populate_template_list()

            # Select the imported template in the list
            for i in range(self.template_list.count()):
                item = self.template_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == name:
                    self.template_list.setCurrentItem(item)
                    break

            self.template_manager = TemplateManager()

            QMessageBox.information(
                self, 'Import Successful',
                f"Template '{name}' imported successfully."
            )
        except Exception as e:
            logger.error(f'Error importing template: {str(e)}')
            QMessageBox.critical(
                self, 'Import Error',
                f'Error importing template:\n{str(e)}'
            )

    def _export_template(self) -> None:
        """Export the current template to a file."""
        if not self.current_template or not self.current_template_data:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export Template',
            f'{self.current_template}.json',
            'JSON Files (*.json)'
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_template_data, f, indent=2)

            QMessageBox.information(
                self, 'Export Successful',
                f"Template '{self.current_template}' exported successfully."
            )
        except Exception as e:
            logger.error(f'Error exporting template: {str(e)}')
            QMessageBox.critical(
                self, 'Export Error',
                f"Error exporting template '{self.current_template}':\n{str(e)}"
            )

    def _handle_close(self) -> None:
        """Handle the close button click, asking to save changes if needed."""
        if self.modified:
            save_result = QMessageBox.question(
                self, 'Save Changes',
                f"Save changes to template '{self.current_template}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if save_result == QMessageBox.StandardButton.Yes:
                self._save_changes()
                self.accept()
            elif save_result == QMessageBox.StandardButton.No:
                self.reject()
        else:
            self.reject()