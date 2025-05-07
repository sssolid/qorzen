#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VCdb Explorer filter panel module.

This module provides UI components for creating and managing query filter panels.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, cast
from uuid import uuid4

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QScrollArea, QFrame, QSplitter, QToolButton, QMenu, QSizePolicy,
    QCheckBox, QGroupBox, QGridLayout, QSpinBox
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon

from .database import VCdbDatabase, FilterValue


class FilterWidget(QWidget):
    """Base class for filter widgets."""

    valueChanged = Signal(str, list)  # filter_type, selected_values

    def __init__(
            self,
            filter_type: str,
            filter_name: str,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the filter widget.

        Args:
            filter_type: Internal type identifier for this filter
            filter_name: Display name for this filter
            parent: Parent widget
        """
        super().__init__(parent)
        self._filter_type = filter_type
        self._filter_name = filter_name
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # Label
        self._label = QLabel(filter_name)
        self._label.setMinimumWidth(100)
        self._layout.addWidget(self._label)

        # Clear button
        self._clear_btn = QToolButton()
        self._clear_btn.setText("×")
        self._clear_btn.setToolTip(f"Clear {filter_name} filter")
        self._clear_btn.clicked.connect(self.clear)

        # Add clear button at the end
        self._layout.addWidget(self._clear_btn)

    def get_filter_type(self) -> str:
        """Get the filter type identifier.

        Returns:
            Filter type string
        """
        return self._filter_type

    def get_filter_name(self) -> str:
        """Get the filter display name.

        Returns:
            Filter name string
        """
        return self._filter_name

    def get_selected_values(self) -> List[int]:
        """Get the currently selected filter values.

        Returns:
            List of selected value IDs
        """
        return []

    def set_available_values(self, values: List[FilterValue]) -> None:
        """Set the available values for this filter.

        Args:
            values: List of available filter values
        """
        pass

    @Slot()
    def clear(self) -> None:
        """Clear the current filter selection."""
        pass


class ComboBoxFilter(FilterWidget):
    """Filter widget with a single-select dropdown."""

    def __init__(
            self,
            filter_type: str,
            filter_name: str,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the combo box filter.

        Args:
            filter_type: Internal type identifier for this filter
            filter_name: Display name for this filter
            parent: Parent widget
        """
        super().__init__(filter_type, filter_name, parent)

        # Combo box
        self._combo = QComboBox()
        self._combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._combo.setMinimumWidth(150)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)

        # Add combo box before the clear button
        self._layout.insertWidget(1, self._combo)

    def get_selected_values(self) -> List[int]:
        """Get the currently selected filter values.

        Returns:
            List containing the selected value ID
        """
        if self._combo.currentIndex() <= 0:
            return []

        value_id = self._combo.currentData(Qt.UserRole)
        if value_id is not None:
            return [int(value_id)]
        return []

    def set_available_values(self, values: List[FilterValue]) -> None:
        """Set the available values for this filter.

        Args:
            values: List of available filter values
        """
        current_id = None
        if self._combo.currentIndex() > 0:
            current_id = self._combo.currentData(Qt.UserRole)

        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem("Any", None)

        for value in values:
            self._combo.addItem(f"{value.name} ({value.count})", value.id)

        if current_id is not None:
            # Try to restore previous selection
            index = self._combo.findData(current_id)
            if index > 0:
                self._combo.setCurrentIndex(index)
            else:
                self._combo.setCurrentIndex(0)
        else:
            self._combo.setCurrentIndex(0)

        self._combo.blockSignals(False)

    @Slot(int)
    def _on_selection_changed(self, index: int) -> None:
        """Handle combo box selection changes.

        Args:
            index: New selected index
        """
        selected_values = self.get_selected_values()
        self.valueChanged.emit(self._filter_type, selected_values)

    @Slot()
    def clear(self) -> None:
        """Clear the current filter selection."""
        self._combo.setCurrentIndex(0)


class YearRangeFilter(FilterWidget):
    """Filter widget with min and max year inputs."""

    def __init__(
            self,
            filter_type: str,
            filter_name: str,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the year range filter.

        Args:
            filter_type: Internal type identifier for this filter
            filter_name: Display name for this filter
            parent: Parent widget
        """
        super().__init__(filter_type, filter_name, parent)

        # Start year spinner
        self._start_label = QLabel("From:")
        self._start_year = QSpinBox()
        self._start_year.setRange(1900, 2100)
        self._start_year.setValue(1900)
        self._start_year.valueChanged.connect(self._on_value_changed)

        # End year spinner
        self._end_label = QLabel("To:")
        self._end_year = QSpinBox()
        self._end_year.setRange(1900, 2100)
        self._end_year.setValue(2100)
        self._end_year.valueChanged.connect(self._on_value_changed)

        # Add widgets before the clear button
        self._layout.insertWidget(1, self._start_label)
        self._layout.insertWidget(2, self._start_year)
        self._layout.insertWidget(3, self._end_label)
        self._layout.insertWidget(4, self._end_year)

    def get_selected_values(self) -> List[int]:
        """Get the currently selected filter values.

        Returns:
            List containing [start_year, end_year]
        """
        start_year = self._start_year.value()
        end_year = self._end_year.value()

        if start_year > end_year:
            return []

        return [start_year, end_year]

    def set_available_values(self, values: List[FilterValue]) -> None:
        """Set the available years for this filter.

        Args:
            values: List of available year values
        """
        if not values:
            return

        # Find min and max years
        min_year = min(int(v.name) for v in values)
        max_year = max(int(v.name) for v in values)

        self._start_year.blockSignals(True)
        self._end_year.blockSignals(True)

        # Update spinner ranges
        self._start_year.setRange(min_year, max_year)
        self._end_year.setRange(min_year, max_year)

        # Only update values if they're outside the new range
        if self._start_year.value() < min_year or self._start_year.value() > max_year:
            self._start_year.setValue(min_year)

        if self._end_year.value() < min_year or self._end_year.value() > max_year:
            self._end_year.setValue(max_year)

        self._start_year.blockSignals(False)
        self._end_year.blockSignals(False)

    @Slot(int)
    def _on_value_changed(self, value: int) -> None:
        """Handle spinner value changes.

        Args:
            value: New spinner value
        """
        selected_values = self.get_selected_values()
        self.valueChanged.emit(self._filter_type, selected_values)

    @Slot()
    def clear(self) -> None:
        """Reset the year range to default values."""
        self._start_year.blockSignals(True)
        self._end_year.blockSignals(True)

        min_value = self._start_year.minimum()
        max_value = self._end_year.maximum()

        self._start_year.setValue(min_value)
        self._end_year.setValue(max_value)

        self._start_year.blockSignals(False)
        self._end_year.blockSignals(False)

        self.valueChanged.emit(self._filter_type, self.get_selected_values())


class FilterPanel(QGroupBox):
    """Panel containing a set of filter widgets.

    This panel represents a single query filter condition.
    """

    filterChanged = Signal(str, str, list)  # panel_id, filter_type, values
    removeRequested = Signal(str)  # panel_id

    def __init__(
            self,
            panel_id: str,
            database: VCdbDatabase,
            available_filters: List[Dict[str, Any]],
            logger: logging.Logger,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the filter panel.

        Args:
            panel_id: Unique identifier for this panel
            database: VCdb database instance
            available_filters: List of available filter definitions
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._panel_id = panel_id
        self._database = database
        self._logger = logger
        self._available_filters = available_filters
        self._filters: Dict[str, FilterWidget] = {}
        self._current_values: Dict[str, List[int]] = {}

        # Set up layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Header with title and buttons
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Panel title
        self.setTitle(f"Filter Group {panel_id[-4:]}")

        # Add filter button
        self._add_filter_btn = QPushButton("Add Filter")
        self._add_filter_btn.clicked.connect(self._show_add_filter_menu)
        header_layout.addWidget(self._add_filter_btn)

        # Clear all button
        self._clear_all_btn = QPushButton("Clear All")
        self._clear_all_btn.clicked.connect(self._clear_all_filters)
        header_layout.addWidget(self._clear_all_btn)

        # Remove panel button
        self._remove_btn = QPushButton("Remove Group")
        self._remove_btn.clicked.connect(self._remove_panel)
        header_layout.addWidget(self._remove_btn)

        header_layout.addStretch()
        self._layout.addLayout(header_layout)

        # Filter container
        self._filters_layout = QVBoxLayout()
        self._filters_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._filters_layout)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self._layout.addWidget(line)

        # Add mandatory filters
        for filter_def in self._available_filters:
            if filter_def.get("mandatory", False):
                self._add_filter(filter_def["id"], filter_def["name"])

    def get_panel_id(self) -> str:
        """Get the panel ID.

        Returns:
            Panel ID string
        """
        return self._panel_id

    def get_current_values(self) -> Dict[str, List[int]]:
        """Get the current filter values.

        Returns:
            Dictionary of filter_type to selected values
        """
        return self._current_values.copy()

    def _add_filter(self, filter_type: str, filter_name: str) -> None:
        """Add a new filter widget to the panel.

        Args:
            filter_type: Filter type identifier
            filter_name: Display name for the filter
        """
        if filter_type in self._filters:
            return

        # Create appropriate filter widget based on type
        if filter_type == "year_range":
            filter_widget = YearRangeFilter(filter_type, filter_name, self)
        else:
            filter_widget = ComboBoxFilter(filter_type, filter_name, self)

        # Connect signals
        filter_widget.valueChanged.connect(self._on_filter_value_changed)

        # Add to layout
        self._filters_layout.addWidget(filter_widget)
        self._filters[filter_type] = filter_widget

        # Refresh available values for this filter
        self._refresh_filter_values(filter_type)

    def _refresh_filter_values(self, filter_type: str) -> None:
        """Refresh the available values for a filter.

        Args:
            filter_type: Filter type to refresh
        """
        if filter_type not in self._filters:
            return

        filter_widget = self._filters[filter_type]

        try:
            # Get values from database excluding this filter's constraints
            exclude_filters = {filter_type}

            # For year_range, also exclude year filter and vice versa
            if filter_type == "year_range":
                exclude_filters.add("year")
            elif filter_type == "year":
                exclude_filters.add("year_range")

            values = self._database.get_filter_values(
                filter_type if filter_type != "year_range" else "year",
                self._current_values,
                exclude_filters
            )

            # Update the widget
            filter_widget.set_available_values(values)

        except Exception as e:
            self._logger.error(f"Error refreshing filter values for {filter_type}: {str(e)}")

    def refresh_all_filters(self) -> None:
        """Refresh all filter values in the panel."""
        for filter_type in self._filters:
            self._refresh_filter_values(filter_type)

    @Slot(str, list)
    def _on_filter_value_changed(self, filter_type: str, values: List[int]) -> None:
        """Handle filter value changes.

        Args:
            filter_type: Type of filter that changed
            values: New selected values
        """
        if not values:
            if filter_type in self._current_values:
                del self._current_values[filter_type]
        else:
            self._current_values[filter_type] = values

        # Notify parent
        self.filterChanged.emit(self._panel_id, filter_type, values)

        # Refresh all other filters
        for other_type in self._filters:
            if other_type != filter_type:
                self._refresh_filter_values(other_type)

    @Slot()
    def _show_add_filter_menu(self) -> None:
        """Show menu to add a new filter."""
        menu = QMenu(self)

        for filter_def in self._available_filters:
            filter_id = filter_def["id"]

            # Skip already added filters
            if filter_id in self._filters:
                continue

            action = menu.addAction(filter_def["name"])
            action.setData(filter_id)

        if not menu.isEmpty():
            # Connect the triggered signal using a lambda to capture the action
            menu.triggered.connect(
                lambda action: self._add_filter(action.data(), action.text())
            )
            menu.popup(self._add_filter_btn.mapToGlobal(
                self._add_filter_btn.rect().bottomLeft()
            ))

    @Slot()
    def _clear_all_filters(self) -> None:
        """Clear all filter selections."""
        for filter_widget in self._filters.values():
            filter_widget.clear()

    @Slot()
    def _remove_panel(self) -> None:
        """Request removal of this panel."""
        self.removeRequested.emit(self._panel_id)


class FilterPanelManager(QWidget):
    """Manager for multiple filter panels.

    This widget organizes and coordinates multiple filter panels.
    """

    filtersChanged = Signal()  # Emitted when any filter changes

    def __init__(
            self,
            database: VCdbDatabase,
            logger: logging.Logger,
            max_panels: int = 5,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the filter panel manager.

        Args:
            database: VCdb database instance
            logger: Logger instance
            max_panels: Maximum number of filter panels allowed
            parent: Parent widget
        """
        super().__init__(parent)
        self._database = database
        self._logger = logger
        self._max_panels = max_panels
        self._panels: Dict[str, FilterPanel] = {}

        # Get available filters from database
        self._available_filters = database.get_available_filters()

        # Set up layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Header with title and buttons
        header_layout = QHBoxLayout()

        # Title
        title = QLabel("Query Filters")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add panel button
        self._add_panel_btn = QPushButton("Add Filter Group")
        self._add_panel_btn.clicked.connect(self._add_panel)
        header_layout.addWidget(self._add_panel_btn)

        self._layout.addLayout(header_layout)

        # Scroll area for panels
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)

        # Container widget for panels
        self._panels_container = QWidget()
        self._panels_layout = QVBoxLayout()
        self._panels_layout.setContentsMargins(0, 0, 0, 0)
        self._panels_layout.addStretch()
        self._panels_container.setLayout(self._panels_layout)

        self._scroll_area.setWidget(self._panels_container)
        self._layout.addWidget(self._scroll_area)

        # Add first panel by default
        self._add_panel()

    def _add_panel(self) -> None:
        """Add a new filter panel."""
        if len(self._panels) >= self._max_panels:
            self._logger.warning(f"Maximum number of filter panels ({self._max_panels}) reached")
            return

        # Generate unique panel ID
        panel_id = str(uuid4())

        # Create the panel
        panel = FilterPanel(
            panel_id,
            self._database,
            self._available_filters,
            self._logger,
            self._panels_container
        )

        # Connect signals
        panel.filterChanged.connect(self._on_filter_changed)
        panel.removeRequested.connect(self._remove_panel)

        # Add to layout (before the stretch)
        self._panels_layout.insertWidget(self._panels_layout.count() - 1, panel)
        self._panels[panel_id] = panel

        # Update the add panel button
        self._add_panel_btn.setEnabled(len(self._panels) < self._max_panels)

    def _remove_panel(self, panel_id: str) -> None:
        """Remove a filter panel.

        Args:
            panel_id: ID of the panel to remove
        """
        if panel_id not in self._panels:
            return

        # Don't allow removing the last panel
        if len(self._panels) <= 1:
            return

        # Remove from layout and delete
        panel = self._panels[panel_id]
        self._panels_layout.removeWidget(panel)
        panel.deleteLater()

        # Remove from dictionary
        del self._panels[panel_id]

        # Update the add panel button
        self._add_panel_btn.setEnabled(len(self._panels) < self._max_panels)

        # Emit filter change signal
        self.filtersChanged.emit()

    @Slot(str, str, list)
    def _on_filter_changed(self, panel_id: str, filter_type: str, values: List[int]) -> None:
        """Handle filter value changes.

        Args:
            panel_id: ID of the panel containing the changed filter
            filter_type: Type of filter that changed
            values: New selected values
        """
        # Emit filter change signal
        self.filtersChanged.emit()

    def get_all_filters(self) -> List[Dict[str, List[int]]]:
        """Get all filter values from all panels.

        Returns:
            List of filter dictionaries (one per panel)
        """
        return [panel.get_current_values() for panel in self._panels.values()]

    def refresh_all_panels(self) -> None:
        """Refresh all filter panels."""
        for panel in self._panels.values():
            panel.refresh_all_filters()