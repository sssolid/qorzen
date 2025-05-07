from __future__ import annotations

from initialdb.utils.dependency_container import resolve
from initialdb.utils.schema_registry import SchemaRegistry

"""
Column selection dialog for the InitialDB application.

This module provides a dialog for selecting which columns to display in the results panel,
filtered to match the available filters shown in the query panel.
"""

from typing import Any, Dict, List, Optional, Tuple, Set
import structlog
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QDialogButtonBox, QCheckBox
)

from initialdb.config.settings import DEFAULT_SETTINGS

logger = structlog.get_logger(__name__)


class ColumnSelectionDialog(QDialog):
    """
    Dialog for selecting which columns to display in the results panel.

    Shows a filtered list of columns matching those available in the filter panel.
    """

    def __init__(
            self,
            all_columns: List[Tuple[str, str, str]],
            visible_columns: List[Tuple[str, str, str]],
            parent=None
    ) -> None:
        """
        Initialize the column selection dialog.

        Args:
            all_columns: List of all available columns as (table, column, display) tuples
            visible_columns: List of currently visible columns
            parent: Parent widget
        """
        super().__init__(parent)

        self._registry = resolve(SchemaRegistry)

        self.setWindowTitle('Select Columns to Display')
        self.resize(600, 500)

        # Get available filters to filter the column list
        self.available_filters = self._registry.get_available_filters()
        self.available_filter_keys = {(table, column) for table, column, _ in self.available_filters}

        # Filter all_columns to match available filters
        self.all_columns = [
            col for col in all_columns
            if (col[0], col[1]) in self.available_filter_keys
        ]

        self.visible_columns = visible_columns.copy()
        self.visible_column_set = {(table, col) for table, col, _ in visible_columns}

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        layout = QVBoxLayout(self)

        intro_label = QLabel('Select columns to display in the results table:')
        layout.addWidget(intro_label)

        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        grouped_columns = self._group_columns_by_category()

        for category, columns in grouped_columns.items():
            # Add category header
            category_item = QListWidgetItem(category)
            category_item.setFlags(Qt.ItemFlag.NoItemFlags)
            category_item.setBackground(self.columns_list.palette().alternateBase())
            font = category_item.font()
            font.setBold(True)
            category_item.setFont(font)
            self.columns_list.addItem(category_item)

            # Add columns in this category
            for table, column, display_name in columns:
                item = QListWidgetItem(display_name)
                item.setData(Qt.ItemDataRole.UserRole, (table, column, display_name))

                # Check if column is visible
                check_state = Qt.CheckState.Checked if (table,
                                                        column) in self.visible_column_set else Qt.CheckState.Unchecked
                item.setCheckState(check_state)

                self.columns_list.addItem(item)

        layout.addWidget(self.columns_list)

        # Control buttons
        controls_layout = QHBoxLayout()

        select_all_btn = QPushButton('Select All')
        select_all_btn.clicked.connect(self._select_all)
        controls_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton('Deselect All')
        deselect_all_btn.clicked.connect(self._deselect_all)
        controls_layout.addWidget(deselect_all_btn)

        reset_btn = QPushButton('Reset to Default')
        reset_btn.clicked.connect(self._reset_to_default)
        controls_layout.addWidget(reset_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._on_accepted)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _group_columns_by_category(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """
        Group columns by category for the UI.

        Returns:
            Dictionary mapping category names to lists of column tuples
        """
        return self._registry.group_display_fields_by_category()

    def _select_all(self) -> None:
        """Select all columns."""
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self) -> None:
        """Deselect all columns."""
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _reset_to_default(self) -> None:
        """Reset column selection to default settings."""
        default_column_set = {col for _, col, _ in DEFAULT_SETTINGS['visible_columns']}

        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    _, column, _ = data
                    item.setCheckState(
                        Qt.CheckState.Checked if column in default_column_set
                        else Qt.CheckState.Unchecked
                    )

    def _on_accepted(self) -> None:
        """Handle dialog acceptance."""
        self.visible_columns = []
        self.visible_column_set = set()

        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if (item.flags() & Qt.ItemFlag.ItemIsUserCheckable and
                    item.checkState() == Qt.CheckState.Checked):

                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    table, column, display_name = data
                    self.visible_columns.append((table, column, display_name))
                    self.visible_column_set.add((table, column))

        self.accept()

    def get_visible_columns(self) -> List[Tuple[str, str, str]]:
        """
        Get the selected visible columns.

        Returns:
            List of (table, column, display_name) tuples for visible columns
        """
        return self.visible_columns