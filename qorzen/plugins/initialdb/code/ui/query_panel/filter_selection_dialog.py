from __future__ import annotations

from ...config.settings import DEFAULT_SETTINGS
from ...utils.dependency_container import resolve
from ...utils.schema_registry import SchemaRegistry

"""
Filter selection dialog for the InitialDB application.

This module provides a dialog for selecting which filters to display in the filter panel.
"""

from typing import Any, Dict, List, Optional, Tuple, Set
import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QDialogButtonBox, QCheckBox
)

logger = structlog.get_logger(__name__)


class FilterSelectionDialog(QDialog):
    def __init__(
            self,
            all_filters: List[Tuple[str, str, str]],
            selected_filters: List[Tuple[str, str, str]],
            parent=None
    ) -> None:
        super().__init__(parent)

        self._registry = resolve(SchemaRegistry)

        self.setWindowTitle('Select Filters')
        self.resize(600, 500)

        self.all_filters = all_filters
        self.selected_filters = selected_filters.copy()
        self.selected_filter_set = {(table, col) for table, col, _ in selected_filters}

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        intro_label = QLabel('Select filters to display in the filter panel:')
        layout.addWidget(intro_label)

        # Create main filters list
        self.filters_list = QListWidget()
        self.filters_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        # Group filters by category
        grouped_filters = self._group_filters_by_category()

        # Populate the list
        for category, filters in grouped_filters.items():
            # Add category header
            category_item = QListWidgetItem(category)
            category_item.setFlags(Qt.ItemFlag.NoItemFlags)
            category_item.setBackground(self.filters_list.palette().alternateBase())
            font = category_item.font()
            font.setBold(True)
            category_item.setFont(font)
            self.filters_list.addItem(category_item)

            # Add filters in this category
            for table, column, display_name in filters:
                item = QListWidgetItem(display_name)
                item.setData(Qt.ItemDataRole.UserRole, (table, column, display_name))

                check_state = Qt.CheckState.Checked if (table,
                                                        column) in self.selected_filter_set else Qt.CheckState.Unchecked
                item.setCheckState(check_state)

                # Make year, make, model, and sub_model filters required and unchangeable
                if column in ['year_id', 'make_id', 'model_id', 'sub_model_id']:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Checked)
                    # item.setBackground(self.filters_list.palette().alternateBase().color().lighter(120))

                    # Add "Required" to display name
                    item.setText(f"{display_name} (Required)")

                self.filters_list.addItem(item)

        layout.addWidget(self.filters_list)

        # Controls section
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

        # Standard dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._on_accepted)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _group_filters_by_category(self) -> Dict[str, List[Tuple[str, str, str]]]:
        # Use registry directly to group filters by category
        return self._registry.group_filters_by_category()

    def _select_all(self) -> None:
        for i in range(self.filters_list.count()):
            item = self.filters_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self) -> None:
        for i in range(self.filters_list.count()):
            item = self.filters_list.item(i)
            # Don't uncheck the required filters
            if (item.flags() & Qt.ItemFlag.ItemIsUserCheckable and
                    item.data(Qt.ItemDataRole.UserRole) and
                    item.data(Qt.ItemDataRole.UserRole)[1] not in ['year_id', 'make_id', 'model_id', 'sub_model_id']):
                item.setCheckState(Qt.CheckState.Unchecked)

    def _reset_to_default(self) -> None:
        # Reference settings DEFAULT_SETTINGS
        default_filter_columns = [col for _, col, _ in DEFAULT_SETTINGS['active_filters']]

        for i in range(self.filters_list.count()):
            item = self.filters_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    _, column, _ = data
                    if column in ['year_id', 'make_id', 'model_id', 'sub_model_id']:
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(
                            Qt.CheckState.Checked if column in default_filter_columns else Qt.CheckState.Unchecked)

    def _on_accepted(self) -> None:
        """
        Update the selected filters when OK is clicked.
        """
        self.selected_filters = []
        self.selected_filter_set = set()

        # Always include the required filters
        required_filters = [
            filter_tuple for filter_tuple in self.all_filters
            if filter_tuple[1] in ['year_id', 'make_id', 'model_id', 'sub_model_id']
        ]

        for required_filter in required_filters:
            table, column, display_name = required_filter
            self.selected_filters.append((table, column, display_name))
            self.selected_filter_set.add((table, column))

        # Add the selected optional filters
        for i in range(self.filters_list.count()):
            item = self.filters_list.item(i)
            if (item.flags() & Qt.ItemFlag.ItemIsUserCheckable and
                    item.checkState() == Qt.CheckState.Checked):
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    table, column, display_name = data
                    if (table, column) not in self.selected_filter_set:
                        self.selected_filters.append((table, column, display_name))
                        self.selected_filter_set.add((table, column))

        self.accept()

    def get_selected_filters(self) -> List[Tuple[str, str, str]]:
        return self.selected_filters