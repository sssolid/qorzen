from __future__ import annotations

"""
Export dialog for the InitialDB application.

This module provides a dialog for selecting export options, including format,
file path, and template options for specialized exports.
"""

import os
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QGroupBox,
    QRadioButton, QWidget, QTabWidget, QFormLayout, QSpacerItem, QSizePolicy
)

from initialdb.config.settings import EXPORTS_DIR, settings
from initialdb.utils.template_manager import TemplateManager


class ExportFormat(Enum):
    """Enum defining supported export formats."""
    CSV = auto()
    EXCEL = auto()


class ExportMode(Enum):
    """Enum defining export modes."""
    STANDARD = auto()
    TEMPLATE = auto()


class ExportDialog(QDialog):
    """
    Dialog for configuring export options.

    Allows selection of export format, output path, and additional options
    including templates for specialized export formats.
    """

    def __init__(
            self,
            has_excel: bool = True,
            has_selection: bool = False,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the export dialog.

        Args:
            has_excel: Whether Excel export is available
            has_selection: Whether there are selected rows to export
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle('Export Data')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.has_excel = has_excel
        self.has_selection = has_selection

        self.export_format = ExportFormat.CSV
        self.export_mode = ExportMode.STANDARD
        self.export_path = os.path.join(
            settings.get('default_exports_path', str(EXPORTS_DIR)),
            'vehicle_query_results.csv'
        )
        self.export_selected_only = False
        self.include_headers = True

        # Template-specific options
        self.template_manager = TemplateManager()
        self.available_templates = self.template_manager.get_template_names()
        self.selected_template = self.available_templates[0] if self.available_templates else ""

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the dialog UI components."""
        layout = QVBoxLayout(self)

        # Create tab widget for different export modes
        self.tab_widget = QTabWidget()
        self.standard_tab = QWidget()
        self.template_tab = QWidget()

        self.tab_widget.addTab(self.standard_tab, "Standard Export")
        self.tab_widget.addTab(self.template_tab, "Template Export")
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Setup standard export tab
        self._setup_standard_tab()

        # Setup template export tab
        self._setup_template_tab()

        layout.addWidget(self.tab_widget)

        # Common file path selector
        file_group = QGroupBox('Export File')
        file_layout = QVBoxLayout(file_group)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('File:'))
        self.path_edit = QLineEdit(self.export_path)
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton('Browse...')
        browse_btn.clicked.connect(self._browse_for_file)
        path_layout.addWidget(browse_btn)

        file_layout.addLayout(path_layout)
        layout.addWidget(file_group)

        # Common export options
        options_group = QGroupBox('Export Options')
        options_layout = QVBoxLayout(options_group)

        self.headers_check = QCheckBox('Include column headers')
        self.headers_check.setChecked(True)
        options_layout.addWidget(self.headers_check)

        self.selected_check = QCheckBox('Export only selected rows')
        self.selected_check.setEnabled(self.has_selection)
        self.selected_check.setChecked(False)
        options_layout.addWidget(self.selected_check)

        layout.addWidget(options_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _setup_standard_tab(self) -> None:
        """Set up the standard export tab UI."""
        layout = QVBoxLayout(self.standard_tab)

        format_group = QGroupBox('Export Format')
        format_layout = QVBoxLayout(format_group)

        self.csv_radio = QRadioButton('CSV (Comma Separated Values)')
        self.csv_radio.setChecked(True)
        self.csv_radio.toggled.connect(self._on_format_changed)
        format_layout.addWidget(self.csv_radio)

        self.excel_radio = QRadioButton('Excel Workbook (.xlsx)')
        self.excel_radio.setEnabled(self.has_excel)
        self.excel_radio.toggled.connect(self._on_format_changed)
        format_layout.addWidget(self.excel_radio)

        layout.addWidget(format_group)
        layout.addStretch()

    def _setup_template_tab(self) -> None:
        """Set up the template export tab UI."""
        layout = QVBoxLayout(self.template_tab)

        # Template selection
        template_group = QGroupBox('Template')
        template_layout = QVBoxLayout(template_group)

        template_form = QFormLayout()
        self.template_combo = QComboBox()
        self.template_combo.addItems(self.available_templates)
        if self.available_templates:
            self.template_combo.setCurrentText(self.selected_template)
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        template_form.addRow("Select Template:", self.template_combo)

        template_layout.addLayout(template_form)
        layout.addWidget(template_group)

        # Format options for template export
        format_group = QGroupBox('Export Format')
        format_layout = QVBoxLayout(format_group)

        self.template_csv_radio = QRadioButton('CSV (Comma Separated Values)')
        self.template_csv_radio.setChecked(True)
        self.template_csv_radio.toggled.connect(self._on_template_format_changed)
        format_layout.addWidget(self.template_csv_radio)

        self.template_excel_radio = QRadioButton('Excel Workbook (.xlsx)')
        self.template_excel_radio.setEnabled(self.has_excel)
        self.template_excel_radio.toggled.connect(self._on_template_format_changed)
        format_layout.addWidget(self.template_excel_radio)

        layout.addWidget(format_group)
        layout.addStretch()

    def _on_tab_changed(self, index: int) -> None:
        """
        Handle tab change events.

        Args:
            index: Index of the newly selected tab
        """
        self.export_mode = ExportMode.TEMPLATE if index == 1 else ExportMode.STANDARD
        self._update_file_path()

    def _on_template_changed(self, template_name: str) -> None:
        """
        Handle template selection change.

        Args:
            template_name: Name of the newly selected template
        """
        self.selected_template = template_name
        self._update_file_path()

    def _on_format_changed(self) -> None:
        """Handle format change events in standard export tab."""
        if self.csv_radio.isChecked():
            self.export_format = ExportFormat.CSV
        else:
            self.export_format = ExportFormat.EXCEL

        self._update_file_path()

    def _on_template_format_changed(self) -> None:
        """Handle format change events in template export tab."""
        if self.template_csv_radio.isChecked():
            self.export_format = ExportFormat.CSV
        else:
            self.export_format = ExportFormat.EXCEL

        self._update_file_path()

    def _update_file_path(self) -> None:
        """Update the file path based on current settings."""
        path = Path(self.path_edit.text())
        dir_path = path.parent

        # Base filename without extension
        base_name = "vehicle_query_results"

        # Add template name if in template mode
        if self.export_mode == ExportMode.TEMPLATE and self.selected_template:
            base_name = f"{base_name}_{self.selected_template}"

        # Add appropriate extension
        extension = ".xlsx" if self.export_format == ExportFormat.EXCEL else ".csv"

        new_path = dir_path / f"{base_name}{extension}"
        self.path_edit.setText(str(new_path))

    def _browse_for_file(self) -> None:
        """Open a file dialog to select the export file path."""
        file_filter = 'CSV Files (*.csv)' if self.export_format == ExportFormat.CSV else 'Excel Files (*.xlsx)'
        file_ext = '.csv' if self.export_format == ExportFormat.CSV else '.xlsx'

        export_dir = os.path.dirname(self.path_edit.text())
        if not os.path.exists(export_dir):
            export_dir = settings.get('default_exports_path', str(EXPORTS_DIR))
            if not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)

        # Base filename without extension
        base_name = "vehicle_query_results"

        # Add template name if in template mode
        if self.export_mode == ExportMode.TEMPLATE and self.selected_template:
            base_name = f"{base_name}_{self.selected_template}"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Export Data',
            os.path.join(export_dir, f'{base_name}{file_ext}'),
            file_filter
        )

        if filename:
            self.path_edit.setText(filename)

    def get_export_options(self) -> Tuple[str, str, bool, bool, Optional[str]]:
        """
        Get the selected export options.

        Returns:
            Tuple containing:
            - Export format ('csv' or 'excel')
            - File path
            - Whether to export selected rows only
            - Whether to include headers
            - Template name (or None for standard export)
        """
        format_type = 'excel' if (
                (self.export_mode == ExportMode.STANDARD and self.excel_radio.isChecked()) or
                (self.export_mode == ExportMode.TEMPLATE and self.template_excel_radio.isChecked())
        ) else 'csv'

        template = self.selected_template if self.export_mode == ExportMode.TEMPLATE else None

        return (
            format_type,
            self.path_edit.text(),
            self.selected_check.isChecked(),
            self.headers_check.isChecked(),
            template
        )