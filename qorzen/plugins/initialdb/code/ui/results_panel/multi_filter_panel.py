from __future__ import annotations

"""
Multi-filter panel for the InitialDB application.

This module provides a panel for managing multiple filter widgets, allowing
users to add, remove, and manage filters for refining search results.
"""

from typing import Any, Dict, List, Optional, Tuple, Set, cast
import re
import structlog
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QScrollArea, QFrame, QToolButton
)

from initialdb.utils.dependency_container import resolve
from initialdb.utils.schema_registry import SchemaRegistry
from initialdb.ui.results_panel.enhanced_filter_widget import EnhancedFilterWidget, FilterType

logger = structlog.get_logger(__name__)


class MultiFilterPanel(QWidget):
    """
    A panel for managing multiple filter widgets to refine search results.

    This panel allows users to add, remove, and manage filters that are applied
    to query results after they've been retrieved from the database.
    """

    filtersChanged = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None, repository=None) -> None:
        """
        Initialize the multi-filter panel.

        Args:
            parent: Optional parent widget
            repository: Optional repository for accessing filter values
        """
        super().__init__(parent)

        self._registry = resolve(SchemaRegistry)

        self.repository = repository
        self.available_columns = self._registry.get_available_display_fields()
        self.active_filters: Dict[str, EnhancedFilterWidget] = {}
        self.filter_values: Dict[str, Any] = {}

        # Delay filter change signal to avoid too many updates
        self.filter_change_timer = QTimer(self)
        self.filter_change_timer.setSingleShot(True)
        self.filter_change_timer.setInterval(300)
        self.filter_change_timer.timeout.connect(self._emit_filters_changed)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with controls
        header_layout = QHBoxLayout()

        self.label = QLabel('Active Filters:')
        header_layout.addWidget(self.label)

        self.add_filter_btn = QPushButton('Add Filter')
        self.add_filter_btn.clicked.connect(self._show_add_filter_menu)
        header_layout.addWidget(self.add_filter_btn)

        self.clear_btn = QToolButton()
        self.clear_btn.setText('Clear All')
        self.clear_btn.setToolTip('Clear all filters')
        self.clear_btn.clicked.connect(self.clear_all_filters)
        header_layout.addWidget(self.clear_btn)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Scrollable area for filters
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.filters_container = QWidget()
        self.filters_layout = QVBoxLayout(self.filters_container)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filters_layout.addStretch()

        self.scroll_area.setWidget(self.filters_container)
        layout.addWidget(self.scroll_area)

    def _show_add_filter_menu(self) -> None:
        """Show menu for adding new filters."""
        menu = QMenu(self)

        # Get visible columns from parent or hierarchy
        visible_columns = []
        parent = self.parent()
        while parent and (not hasattr(parent, 'get_visible_columns')):
            parent = parent.parent()

        if parent and hasattr(parent, 'get_visible_columns'):
            visible_columns = parent.get_visible_columns()

        # Group available columns by category
        categories = self._group_columns_by_category(visible_columns)

        has_filters = False
        for category, columns in categories.items():
            if not columns:
                continue

            has_filters = True
            category_menu = menu.addMenu(category)

            for table, column, display_name in columns:
                # Skip if filter already active
                if self._get_column_key(table, column) in self.active_filters:
                    continue

                action = category_menu.addAction(display_name)
                action.triggered.connect(
                    lambda checked, t=table, c=column, d=display_name:
                    self._add_filter(t, c, d)
                )

        if not has_filters:
            no_filters = menu.addAction('No available filters for visible columns')
            no_filters.setEnabled(False)

        menu.exec(self.add_filter_btn.mapToGlobal(self.add_filter_btn.rect().bottomLeft()))

    def _group_columns_by_category(self, visible_columns: Optional[List[Tuple[str, str, str]]] = None) -> Dict[
        str, List[Tuple[str, str, str]]]:
        """
        Group columns by category for the filter menu.

        Args:
            visible_columns: Optional list of visible columns to filter by

        Returns:
            Dictionary mapping category names to lists of column tuples
        """
        all_categories = self._registry.group_display_fields_by_category()

        if not visible_columns:
            return all_categories

        visible_set = {(table, column) for table, column, _ in visible_columns}
        filtered_categories = {}

        for category, columns in all_categories.items():
            filtered_columns = [
                (table, column, display)
                for table, column, display in columns
                if (table, column) in visible_set
            ]

            if filtered_columns:
                filtered_categories[category] = filtered_columns

        return filtered_categories

    def _get_column_key(self, table: str, column: str) -> str:
        """
        Create a unique key for a column.

        Args:
            table: Database table name
            column: Column name

        Returns:
            Unique key string for the column
        """
        return f'{table}.{column}'

    def _get_filter_values(self, table: str, column: str) -> List[Any]:
        """
        Get list of possible values for a filter column.

        Args:
            table: Database table name
            column: Column name

        Returns:
            List of possible filter values
        """
        if not self.repository:
            return []

        try:
            is_numeric = self._is_numeric_column(column)
            value_column = column
            id_column = column

            values = self.repository._db_helper.get_filter_values_sync(
                table_name=table,
                value_column=value_column,
                id_column=id_column
            )

            return [val[0] for val in values]
        except Exception as e:
            logger.error(f'Error getting filter values for {table}.{column}: {str(e)}')
            return []

    def _is_numeric_column(self, column: str) -> bool:
        """
        Determine if a column contains numeric values.

        Args:
            column: Column name

        Returns:
            True if the column likely contains numeric values
        """
        numeric_patterns = [
            '_id$', 'year', 'num_', 'count', 'liter', 'cc',
            'cid', 'bore', 'stroke', 'power', 'horse_power', 'kilowatt'
        ]

        return any((re.search(pattern, column, re.IGNORECASE) for pattern in numeric_patterns))

    def _determine_filter_type(self, table: str, column: str) -> FilterType:
        """
        Determine the appropriate filter type for a column.

        Args:
            table: Database table name
            column: Column name

        Returns:
            Appropriate FilterType for the column
        """
        if table == 'year' and column == 'year_id':
            return FilterType.RANGE

        if self._is_numeric_column(column):
            if any((x in column for x in ['liter', 'cc', 'bore', 'stroke'])):
                return FilterType.RANGE
            return FilterType.NUMERIC

        return FilterType.SELECTION

    def _add_filter(self, table: str, column: str, display_name: str) -> None:
        """
        Add a new filter to the panel.

        Args:
            table: Database table name
            column: Column name
            display_name: Display name for the filter
        """
        column_key = self._get_column_key(table, column)
        if column_key in self.active_filters:
            return

        filter_type = self._determine_filter_type(table, column)

        # Special case for year filter in results panel
        if table == 'year' and column == 'year_id':
            filter_type = FilterType.RANGE

        filter_widget = EnhancedFilterWidget(
            column_name=column_key,
            display_name=display_name,
            filter_type=filter_type,
            parent=self
        )

        filter_widget.filterChanged.connect(self._on_filter_changed)
        filter_widget.filterRemoved.connect(self._on_filter_removed)

        self.filters_layout.insertWidget(self.filters_layout.count() - 1, filter_widget)
        self.active_filters[column_key] = filter_widget

        # Load filter values
        values = self._get_filter_values(table, column)
        filter_widget.available_values = values

    def _on_filter_changed(self, column_key: str, value: Any) -> None:
        """
        Handle filter value changes.

        Args:
            column_key: Column key
            value: New filter value
        """
        self.filter_values[column_key] = value
        self.filter_change_timer.start()

    def _on_filter_removed(self, column_key: str) -> None:
        """
        Handle filter removal.

        Args:
            column_key: Column key of removed filter
        """
        if column_key in self.active_filters:
            del self.active_filters[column_key]

        if column_key in self.filter_values:
            del self.filter_values[column_key]

        self._emit_filters_changed()

    def _emit_filters_changed(self) -> None:
        """Emit the filtersChanged signal with current filter values."""
        self.filtersChanged.emit(self.filter_values.copy())

    def clear_all_filters(self) -> None:
        """Clear all active filters."""
        column_keys = list(self.active_filters.keys())

        for column_key in column_keys:
            if column_key in self.active_filters:
                self.active_filters[column_key]._remove_filter()

        self.filter_values.clear()
        self._emit_filters_changed()

    def set_filters(self, filters: Dict[str, Any]) -> None:
        """
        Set filter values from a dictionary.

        Args:
            filters: Dictionary mapping column keys to filter values
        """
        self.clear_all_filters()

        for column_key, value in filters.items():
            if '.' in column_key:
                table, column = column_key.split('.', 1)
                display_name = column_key

                # Find proper display name
                for t, c, d in self.available_columns:
                    if t == table and c == column:
                        display_name = d
                        break

                self._add_filter(table, column, display_name)

                if column_key in self.active_filters:
                    self.active_filters[column_key].set_value(value)