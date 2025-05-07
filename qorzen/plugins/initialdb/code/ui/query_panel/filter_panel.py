from __future__ import annotations

from copy import deepcopy

from ...services.vehicle_service import VehicleService

"""
Filter panel component for the InitialDB application.

This module provides a panel with multi-selection filters for querying vehicle data,
allowing users to select multiple values for each filter criterion, with proper
async loading and thread safety.
"""

import asyncio
import threading
import uuid
from typing import Any, Dict, List, Optional, Tuple, Set, cast

import structlog
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ...adapters.vehicle_service_adapter import VehicleServiceAdapter
from ...models.schema import FilterDTO, SavedQueryDTO
from ...utils.async_manager import AsyncManager, async_slot
from ...utils.dependency_container import resolve
from ...utils.schema_registry import SchemaRegistry
from .filter_selection_dialog import FilterSelectionDialog
from .multi_selection_widget import MultiSelectionWidget

logger = structlog.get_logger(__name__)


class FilterPanel(QWidget):
    """Panel for filtering query results."""

    filterChanged = pyqtSignal(FilterDTO)
    executeQueryRequested = pyqtSignal()
    filterSelectionChanged = pyqtSignal(list)
    saveQueryRequested = pyqtSignal(FilterDTO, list, str, str)
    loadQueryRequested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the filter panel.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        # Get registry via the migration helper or dependency injection
        self._registry = resolve(SchemaRegistry)

        # Initialize variables
        self.all_available_filters = self._registry.get_available_filters()
        self.selected_filters = []

        # Add required filters
        required_filters = [
            ("year", "year_id", "Year"),
            ("make", "make_id", "Make"),
            ("model", "model_id", "Model"),
            ("sub_model", "sub_model_id", "Submodel"),
        ]
        for filter_tuple in required_filters:
            actual_filter = next(
                (
                    af
                    for af in self.all_available_filters
                    if af[0] == filter_tuple[0] and af[1] == filter_tuple[1]
                ),
                None,
            )
            self.selected_filters.append(actual_filter if actual_filter else filter_tuple)

        # Initialize service adapter
        self.service_adapter = VehicleServiceAdapter()

        # Create filter DTO
        self.filter_dto = FilterDTO()

        # Other state variables
        self.filter_values: Dict[Tuple[str, str], List[Tuple[Any, str]]] = {}
        self.pending_filters: List[Tuple[str, str]] = []
        self._pending_filter_requests: Dict[str, Tuple[str, str]] = {}
        self.filter_widgets: Dict[Tuple[str, str], MultiSelectionWidget] = {}
        self._loading_filters = False
        self._pending_dto_update: Optional[FilterDTO] = None
        self._saved_queries: Dict[str, SavedQueryDTO] = {}
        self._ui_initialized = False
        self._filters_initialized = False
        self._load_in_progress = False

        # Initialize UI
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Delay actual filter initialization to avoid freeze
        QTimer.singleShot(100, self._delayed_init)

    def _connect_signals(self) -> None:
        """Connect adapter signals."""
        self.service_adapter.signals.filterValuesLoaded.connect(self._on_filter_values_loaded)

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header frame
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header_frame)

        # Header with title and add filter button
        title_layout = QHBoxLayout()
        title_label = QLabel("Filters")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        add_filter_btn = QPushButton("Add Filter")
        add_filter_btn.clicked.connect(self._show_filter_selection_dialog)
        title_layout.addWidget(add_filter_btn)

        header_layout.addLayout(title_layout)
        main_layout.addWidget(header_frame)

        # Scroll area for filters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_widget = QWidget()
        self.filters_layout = QVBoxLayout(self.scroll_widget)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filters_layout.setSpacing(8)

        # Create category frames
        self.category_frames = {}
        self.category_layouts = {}
        categories = [
            "Basic Vehicle Info",
            "Engine",
            "Transmission",
            "Body",
            "Chassis",
            "Brakes",
            "Fuel System",
        ]

        for category in categories:
            category_frame = QGroupBox(category)
            category_frame.setCheckable(True)
            category_frame.setChecked(True)
            category_frame.toggled.connect(self._toggle_category)

            category_layout = QVBoxLayout(category_frame)
            category_layout.setContentsMargins(10, 20, 10, 10)
            category_layout.setSpacing(10)

            self.category_frames[category] = category_frame
            self.category_layouts[category] = category_layout

            self.filters_layout.addWidget(category_frame)

        self.filters_layout.addStretch()
        scroll_area.setWidget(self.scroll_widget)
        main_layout.addWidget(scroll_area)

        # Controls frame with auto-execute checkbox and buttons
        controls_frame = QFrame()
        controls_frame.setFrameShape(QFrame.Shape.StyledPanel)
        controls_layout = QHBoxLayout(controls_frame)

        self.auto_execute_checkbox = QCheckBox("Auto-Execute")
        self.auto_execute_checkbox.setChecked(False)
        controls_layout.addWidget(self.auto_execute_checkbox)

        controls_layout.addStretch()

        reset_btn = QPushButton("Reset Filters")
        reset_btn.clicked.connect(self._reset_filters)
        controls_layout.addWidget(reset_btn)

        execute_btn = QPushButton("Execute Query")
        execute_btn.clicked.connect(self._execute_query)
        execute_btn.setDefault(True)
        controls_layout.addWidget(execute_btn)

        main_layout.addWidget(controls_frame)

        # Create filter widgets
        self._create_filter_widgets()

        self._ui_initialized = True

    def _delayed_init(self) -> None:
        """Initialize filters after UI is shown."""
        if not self._filters_initialized:
            self._filters_initialized = True
            self._start_loading_filters()

    def _toggle_category(self, expanded: bool) -> None:
        """
        Toggle visibility of a category.

        Args:
            expanded: Whether the category is expanded
        """
        sender = self.sender()
        if not isinstance(sender, QGroupBox):
            return

        for i in range(sender.layout().count()):
            item = sender.layout().itemAt(i)
            if item and item.widget():
                item.widget().setVisible(expanded)

    def _create_filter_widgets(self) -> None:
        """Create filter widgets based on selected filters."""
        self.filter_widgets.clear()

        # Group filters by category
        filter_categories = self._group_filters_by_category()

        # Clear all category layouts
        for layout in self.category_layouts.values():
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # Add filter widgets to each category
        for category, filters in filter_categories.items():
            if category not in self.category_layouts:
                continue

            layout = self.category_layouts[category]

            # For Basic Vehicle Info, ensure standard order
            if category == "Basic Vehicle Info":
                ordered_columns = ["year_id", "make_id", "model_id", "sub_model_id"]
                ordered_filters = []

                for col in ordered_columns:
                    for filter_tuple in filters:
                        if filter_tuple[1] == col:
                            ordered_filters.append(filter_tuple)
                            break

                for filter_tuple in filters:
                    if filter_tuple[1] not in ordered_columns:
                        ordered_filters.append(filter_tuple)

                filters = ordered_filters

            # Create widgets for each filter
            for table, column, display_name in filters:
                friendly_name = self._registry.get_display_name(table, column)

                if column == "year_id":
                    self._add_year_filter_widget(table, column, friendly_name, layout)
                else:
                    self._add_filter_widget(table, column, friendly_name, layout)

            # Hide empty categories
            if layout.count() == 0:
                self.category_frames[category].setVisible(False)
            else:
                self.category_frames[category].setVisible(True)

    def _add_filter_widget(
            self, table: str, column: str, display_name: str, layout: QVBoxLayout
    ) -> None:
        """
        Add a standard filter widget.

        Args:
            table: The table name
            column: The column name
            display_name: The display name
            layout: The layout to add the widget to
        """
        widget = QWidget()
        widget_layout = QHBoxLayout(widget)
        widget_layout.setContentsMargins(0, 0, 0, 0)

        # Label
        label = QLabel(f"{display_name}:")
        label.setMinimumWidth(120)
        widget_layout.addWidget(label)

        # Multi-select widget
        multi_select = MultiSelectionWidget(f"Select {display_name}")
        multi_select.setProperty("id_column", column)
        multi_select.setProperty("table", table)
        multi_select.selectionChanged.connect(
            lambda values, t=table, c=column: self._on_filter_changed(t, c, values)
        )
        widget_layout.addWidget(multi_select, 1)

        # Is this a required filter?
        is_required = column in ["year_id", "make_id", "model_id", "sub_model_id"]

        # Clear button
        clear_btn = QToolButton()
        clear_btn.setText("✕")
        clear_btn.setFixedSize(20, 20)
        clear_btn.setToolTip(f"Clear {display_name} filter")
        clear_btn.clicked.connect(lambda checked=False, ms=multi_select: ms.clear())
        widget_layout.addWidget(clear_btn)

        # Remove button (for non-required filters)
        if not is_required:
            remove_btn = QToolButton()
            remove_btn.setText("✕")
            remove_btn.setFixedSize(20, 20)
            remove_btn.setStyleSheet("background-color: #d9534f; color: white;")
            remove_btn.setToolTip(f"Remove {display_name} filter")
            remove_btn.clicked.connect(
                lambda checked=False, t=table, c=column, d=display_name: self._remove_filter(
                    t, c, d
                )
            )
            widget_layout.addWidget(remove_btn)

        layout.addWidget(widget)
        self.filter_widgets[table, column] = multi_select

    def _add_year_filter_widget(
            self, table: str, column: str, display_name: str, layout: QVBoxLayout
    ) -> None:
        """
        Add a year filter widget with additional range functionality.

        Args:
            table: The table name
            column: The column name
            display_name: The display name
            layout: The layout to add the widget to
        """
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        # Year list selection
        year_widget = QWidget()
        year_layout = QHBoxLayout(year_widget)
        year_layout.setContentsMargins(0, 0, 0, 0)

        year_label = QLabel(f"{display_name}:")
        year_label.setMinimumWidth(120)
        year_layout.addWidget(year_label)

        year_multi_select = MultiSelectionWidget(f"Select {display_name}")
        year_multi_select.setProperty("id_column", column)
        year_multi_select.setProperty("table", table)
        year_multi_select.selectionChanged.connect(
            lambda values: self._on_filter_changed(table, column, values)
        )
        year_layout.addWidget(year_multi_select, 1)

        clear_btn = QToolButton()
        clear_btn.setText("✕")
        clear_btn.setFixedSize(20, 20)
        clear_btn.setToolTip(f"Clear {display_name} filter")
        clear_btn.clicked.connect(lambda checked=False, ms=year_multi_select: ms.clear())
        year_layout.addWidget(clear_btn)

        container_layout.addWidget(year_widget)

        # Year range selection
        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)

        range_check = QCheckBox("Year Range:")
        range_check.setMinimumWidth(120)
        range_check.stateChanged.connect(self._on_year_range_toggled)
        range_layout.addWidget(range_check)

        start_year = QSpinBox()
        start_year.setRange(1900, 2100)
        start_year.setValue(2000)
        start_year.setEnabled(False)
        start_year.valueChanged.connect(self._on_year_range_changed)
        range_layout.addWidget(start_year)

        to_label = QLabel("to")
        range_layout.addWidget(to_label)

        end_year = QSpinBox()
        end_year.setRange(1900, 2100)
        end_year.setValue(2023)
        end_year.setEnabled(False)
        end_year.valueChanged.connect(self._on_year_range_changed)
        range_layout.addWidget(end_year)

        range_layout.addStretch()

        container_layout.addWidget(range_widget)

        layout.addWidget(container)

        # Store widgets for later access
        self.filter_widgets[table, column] = year_multi_select
        self.year_range_check = range_check
        self.year_range_start = start_year
        self.year_range_end = end_year

    def _group_filters_by_category(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """
        Group filters by category.

        Returns:
            A dictionary mapping category names to lists of filters
        """
        categories = self._registry.group_filters_by_category()
        result = {}

        for category, filters in categories.items():
            result[category] = [f for f in filters if f in self.selected_filters]

        return result

    def _on_year_range_toggled(self, state: int) -> None:
        """
        Handle year range checkbox toggle.

        Args:
            state: The checkbox state (checked or unchecked)
        """
        enabled = state == Qt.CheckState.Checked.value
        self.year_range_start.setEnabled(enabled)
        self.year_range_end.setEnabled(enabled)
        self.filter_dto.use_year_range = enabled

        if enabled:
            # Use year range
            self.filter_dto.year_range_start = self.year_range_start.value()
            self.filter_dto.year_range_end = self.year_range_end.value()

            # Disable year selection
            year_widget = self.filter_widgets.get(("year", "year_id"))
            if year_widget:
                year_widget.blockSignals(True)
                year_widget.set_selected_values([])
                year_widget.setEnabled(False)
                year_widget.blockSignals(False)
                self.filter_dto.year_ids = []
        else:
            # Don't use year range
            self.filter_dto.year_range_start = None
            self.filter_dto.year_range_end = None

            # Enable year selection
            year_widget = self.filter_widgets.get(("year", "year_id"))
            if year_widget:
                year_widget.setEnabled(True)

        self.filterChanged.emit(self.filter_dto)
        self._start_loading_filters()

        if self.auto_execute_checkbox.isChecked():
            self.executeQueryRequested.emit()

    def _on_year_range_changed(self) -> None:
        """Handle year range value changes."""
        if not hasattr(self, "year_range_check") or not self.year_range_check.isChecked():
            return

        self.filter_dto.year_range_start = self.year_range_start.value()
        self.filter_dto.year_range_end = self.year_range_end.value()

        self.filterChanged.emit(self.filter_dto)
        self._start_loading_filters()

        if self.auto_execute_checkbox.isChecked():
            self.executeQueryRequested.emit()

    def _on_filter_changed(self, table: str, column: str, values: List[Any]) -> None:
        """
        Handle filter value changes.

        Args:
            table: The table name
            column: The column name
            values: The selected values
        """
        if self._loading_filters:
            return

        logger.debug(f"Filter changed: {table}.{column} = {values}")

        # Convert the column name to filter DTO attribute name
        attr_name = self._get_filter_dto_attribute_name(table, column)
        if attr_name.endswith("_id"):
            attr_name = f"{attr_name}s"

        # Update the filter DTO
        if hasattr(self.filter_dto, attr_name):
            current_values = getattr(self.filter_dto, attr_name, [])
            if current_values != values:
                setattr(self.filter_dto, attr_name, values)

                # Also set singular attribute if applicable
                if column.endswith("_id") and values:
                    single_attr = column
                    setattr(self.filter_dto, single_attr, values[0] if values else None)

                logger.debug(f"Updated filter {attr_name} to {values}")

                # Handle cascading resets
                self._handle_cascading_reset(table, column)

                dto_copy = deepcopy(self.filter_dto)
                self.filterChanged.emit(dto_copy)
                self._start_loading_filters_for_dependency(table, column, dto_copy)

                # Auto-execute if enabled
                if self.auto_execute_checkbox.isChecked():
                    self.executeQueryRequested.emit()
        else:
            logger.warning(f"Cannot set attribute {attr_name} on FilterDTO")

    def _get_filter_dto_attribute_name(self, table: str, column: str) -> str:
        """
        Get the attribute name for a filter in the FilterDTO.

        Args:
            table: The table name
            column: The column name

        Returns:
            The attribute name
        """
        attr_name = column

        # Handle special cases
        if column == "name":
            if table == "make":
                attr_name = "make_id"
            elif table == "model":
                attr_name = "model_id"
            elif table == "sub_model":
                attr_name = "sub_model_id"

        return attr_name

    def _handle_cascading_reset(self, changed_table: str, changed_column: str) -> None:
        """
        Reset dependent filters when a parent filter changes.

        Args:
            changed_table: The table of the changed filter
            changed_column: The column of the changed filter
        """
        # Define filter hierarchy
        hierarchy = [
            ("year", "year_id"),
            ("make", "make_id"),
            ("model", "model_id"),
            ("sub_model", "sub_model_id"),
        ]

        # Find the position of the changed filter in the hierarchy
        changed_idx = -1
        for i, (table, column) in enumerate(hierarchy):
            if table == changed_table and column == changed_column:
                changed_idx = i
                break

        # Reset all filters that depend on the changed filter
        if changed_idx >= 0:
            filters_to_reset = hierarchy[changed_idx + 1:]

            for table, column in filters_to_reset:
                # Reset in filter DTO
                attr_name = self._get_filter_dto_attribute_name(table, column)
                if hasattr(self.filter_dto, attr_name):
                    setattr(self.filter_dto, attr_name, None)

                # Reset plural attribute
                plural_attr = f"{attr_name}s"
                if hasattr(self.filter_dto, plural_attr):
                    setattr(self.filter_dto, plural_attr, [])

                # Reset widget
                widget = self.filter_widgets.get((table, column))
                if widget:
                    widget.blockSignals(True)
                    widget.set_items([])
                    widget.set_selected_values([])
                    widget.blockSignals(False)

                logger.debug(f"Reset dependent filter: {table}.{column}")

    @pyqtSlot()
    def _execute_query(self) -> None:
        """Execute the query."""
        logger.debug("Execute query requested")
        self.executeQueryRequested.emit()

    @pyqtSlot()
    def _reset_filters(self) -> None:
        """Reset all filters."""
        self.filter_dto = FilterDTO()
        was_loading = self._loading_filters
        self._loading_filters = True

        try:
            # Reset filter widgets
            for (table, column), widget in self.filter_widgets.items():
                widget.blockSignals(True)
                widget.set_items([])
                widget.set_selected_values([])
                widget.blockSignals(False)

            # Reset year range
            if hasattr(self, "year_range_check"):
                self.year_range_check.blockSignals(True)
                self.year_range_check.setChecked(False)
                self.year_range_check.blockSignals(False)

                self.year_range_start.blockSignals(True)
                self.year_range_start.setValue(2000)
                self.year_range_start.setEnabled(False)
                self.year_range_start.blockSignals(False)

                self.year_range_end.blockSignals(True)
                self.year_range_end.setValue(2023)
                self.year_range_end.setEnabled(False)
                self.year_range_end.blockSignals(False)

                year_widget = self.filter_widgets.get(("year", "year_id"))
                if year_widget:
                    year_widget.setEnabled(True)
        finally:
            self._loading_filters = was_loading

        self.filterChanged.emit(self.filter_dto)
        self._start_loading_filters()

    def _start_loading_filters(self) -> None:
        """Start loading filter values."""
        if self._load_in_progress:
            return

        self.pending_filters = [(table, column) for table, column, _ in self.selected_filters]
        self._prioritize_filters()
        self._load_in_progress = True

        # Process the first filter
        QTimer.singleShot(0, self._load_next_filter)

    def _start_loading_filters_for_dependency(self, changed_table: str, changed_column: str, filters: FilterDTO) -> None:
        """
        Start loading filter values that depend on a changed filter.

        Args:
            changed_table: The table of the changed filter
            changed_column: The column of the changed filter
        """
        self._current_filter_dto = filters

        if self._load_in_progress:
            return

        # Define filter hierarchy
        hierarchy = [
            ("year", "year_id"),
            ("make", "make_id"),
            ("model", "model_id"),
            ("sub_model", "sub_model_id"),
        ]

        # Find the position of the changed filter in the hierarchy
        changed_idx = -1
        for i, (table, column) in enumerate(hierarchy):
            if table == changed_table and column == changed_column:
                changed_idx = i
                break

        # Load all filters that depend on the changed filter
        if changed_idx >= 0:
            self.pending_filters = hierarchy[changed_idx + 1:]
        else:
            self.pending_filters = []

        if not self.pending_filters:
            return

        self._load_in_progress = True

        # Process the first filter
        QTimer.singleShot(0, self._load_next_filter)

    def _prioritize_filters(self) -> None:
        """Prioritize filters for loading."""
        # Define priority order
        hierarchy = [
            ("year", "year_id"),
            ("make", "make_id"),
            ("model", "model_id"),
            ("sub_model", "sub_model_id"),
        ]

        # Reorder filters
        all_filters = self.pending_filters.copy()
        self.pending_filters = []

        # First add the priority filters in order
        for priority_filter in hierarchy:
            if priority_filter in all_filters:
                self.pending_filters.append(priority_filter)
                all_filters.remove(priority_filter)

        # Then add the rest
        self.pending_filters.extend(all_filters)

    def _load_next_filter(self):
        if not self.pending_filters:
            self._load_in_progress = False
            return

        table, column = self.pending_filters.pop(0)
        widget = self.filter_widgets.get((table, column))
        if not widget:
            logger.warning(f"No widget found for filter {table}.{column}")
            return

        logger.debug(f"Loading values for dependent filter: {table}.{column}")
        filters = deepcopy(self.filter_dto)
        self._load_filter_values(table, column, filters)

    def _load_filter_values(self, table: str, column: str, filters: FilterDTO) -> None:
        self._current_filter_dto = filters
        self._loading_filters = True

        filter_name = column

        if (table, column) in self.filter_values:
            values = self.filter_values[table, column]
            QTimer.singleShot(0, lambda: self._update_filter_widget(table, column, values))
            return

        try:
            operation_id = self.service_adapter.load_filter_values(filter_name, filters)
            self._pending_filter_requests[operation_id] = (table, column)
        except Exception as e:
            logger.error(f"Error loading filter values for {table}.{column}: {e}")
            self._loading_filters = False
            self._load_next_filter()

    @pyqtSlot(str, list)
    def _on_filter_values_loaded(self, operation_id: str, values: List[Tuple[Any, str]]) -> None:
        """
        Handle filter values loaded.

        Args:
            operation_id: The operation ID
            values: The loaded values
        """
        if operation_id not in self._pending_filter_requests:
            logger.warning(f"No filter request for operation_id={operation_id}")
            self._loading_filters = False
            self._load_next_filter()
            return

        table, column = self._pending_filter_requests.pop(operation_id)

        # Update the widget
        self._update_filter_widget(table, column, values)

    def _update_filter_widget(self, table: str, column: str, values: List[Tuple[Any, str]]) -> None:
        """
        Update a filter widget with values.

        Args:
            table: The table name
            column: The column name
            values: The filter values
        """
        try:
            logger.debug(f"Updating filter widget for {table}.{column} with {len(values)} values")

            # Cache the values
            self.filter_values[table, column] = values

            # Get the widget
            widget = self.filter_widgets.get((table, column))
            if not widget:
                logger.debug(f"No widget found for {table}.{column}")
                QTimer.singleShot(0, self._load_next_filter)
                return

            # Get the current values from the filter DTO
            attr_name = self._get_filter_dto_attribute_name(table, column)
            if attr_name.endswith("_id"):
                attr_name = f"{attr_name}s"

            current_values = (
                getattr(self.filter_dto, attr_name, [])
                if hasattr(self.filter_dto, attr_name)
                else []
            )

            # Update the widget
            self._loading_filters = True
            try:
                widget.blockSignals(True)
                widget.set_items(values)

                # Keep only valid values
                valid_values = {value_id for value_id, _ in values}
                valid_current_values = [v for v in current_values if v in valid_values]

                # Update the filter DTO if values have changed
                if valid_current_values != current_values:
                    if hasattr(self.filter_dto, attr_name):
                        setattr(self.filter_dto, attr_name, valid_current_values)

                    # Update singular attribute
                    single_attr = attr_name.rstrip("s")
                    if hasattr(self.filter_dto, single_attr):
                        setattr(
                            self.filter_dto,
                            single_attr,
                            valid_current_values[0] if valid_current_values else None,
                        )

                # Update widget selection
                widget.set_selected_values(valid_current_values)

            finally:
                widget.blockSignals(False)
                self._loading_filters = False

            # Process the next filter
            QTimer.singleShot(0, self._load_next_filter)

        except Exception as e:
            logger.error(f"Error updating filter widget for {table}.{column}: {e}")
            self._loading_filters = False
            QTimer.singleShot(0, self._load_next_filter)

    def _remove_filter(self, table: str, column: str, display_name: str) -> None:
        """
        Remove a filter.

        Args:
            table: The table name
            column: The column name
            display_name: The display name
        """
        filter_tuple = (table, column, display_name)

        # Remove from selected filters
        if filter_tuple in self.selected_filters:
            self.selected_filters.remove(filter_tuple)

        # Reset filter DTO attributes
        attr_name = self._get_filter_dto_attribute_name(table, column)
        if hasattr(self.filter_dto, attr_name):
            setattr(self.filter_dto, attr_name, None)

        plural_attr = f"{attr_name}s"
        if hasattr(self.filter_dto, plural_attr):
            setattr(self.filter_dto, plural_attr, [])

        # Emit signals
        self.filterChanged.emit(self.filter_dto)
        self.filterSelectionChanged.emit(self.selected_filters)

        # Recreate widgets
        self._create_filter_widgets()
        self._start_loading_filters()

    def _show_filter_selection_dialog(self) -> None:
        """Show the filter selection dialog."""
        dialog = FilterSelectionDialog(self.all_available_filters, self.selected_filters, self)

        if dialog.exec() == FilterSelectionDialog.DialogCode.Accepted:
            self.selected_filters = dialog.get_selected_filters()
            self.filterSelectionChanged.emit(self.selected_filters)
            self._create_filter_widgets()
            self._start_loading_filters()

    def set_selected_filters(self, filters: List[Tuple[str, str, str]]) -> None:
        """
        Set the selected filters.

        Args:
            filters: The list of filters to select
        """
        self.selected_filters = filters
        self._create_filter_widgets()
        self._start_loading_filters()

    def get_filter_dto(self) -> FilterDTO:
        """
        Get the current filter DTO.

        Returns:
            The filter DTO
        """
        return self.filter_dto

    def set_filter_dto(self, filter_dto: FilterDTO) -> None:
        """
        Set the filter DTO.

        Args:
            filter_dto: The filter DTO to set
        """
        # Convert dictionary if needed
        if isinstance(filter_dto, dict):
            filter_dto = FilterDTO(**filter_dto)
        elif not isinstance(filter_dto, FilterDTO):
            raise TypeError(f"Expected FilterDTO or dict, got {type(filter_dto)}")

        self.filter_dto = filter_dto

        # Update year range widgets
        self._loading_filters = True
        try:
            if hasattr(self, "year_range_check"):
                self.year_range_check.blockSignals(True)
                self.year_range_start.blockSignals(True)
                self.year_range_end.blockSignals(True)

                use_range = filter_dto.use_year_range
                self.year_range_check.setChecked(use_range)

                if filter_dto.year_range_start is not None:
                    self.year_range_start.setValue(filter_dto.year_range_start)
                else:
                    self.year_range_start.setValue(2000)

                if filter_dto.year_range_end is not None:
                    self.year_range_end.setValue(filter_dto.year_range_end)
                else:
                    self.year_range_end.setValue(2023)

                self.year_range_start.setEnabled(use_range)
                self.year_range_end.setEnabled(use_range)

                self.year_range_check.blockSignals(False)
                self.year_range_start.blockSignals(False)
                self.year_range_end.blockSignals(False)

                year_widget = self.filter_widgets.get(("year", "year_id"))
                if year_widget:
                    year_widget.setEnabled(not use_range)
        finally:
            self._loading_filters = False

        # Schedule loading filter values and updating widgets
        QTimer.singleShot(50, lambda: self._start_loading_filters_with_dto(filter_dto))

    def _start_loading_filters_with_dto(self, filter_dto: FilterDTO) -> None:
        """
        Start loading filter values with a new DTO.

        Args:
            filter_dto: The filter DTO
        """
        self._pending_filters = [(table, column) for table, column, _ in self.selected_filters]
        self._prioritize_filters()
        self._pending_dto_update = filter_dto
        self._load_in_progress = True

        # Process the first filter
        QTimer.singleShot(50, self._load_next_filter_nonblocking)

    def _load_next_filter_nonblocking(self) -> None:
        """Load the next filter without blocking."""
        if not hasattr(self, "_pending_filters") or not self._pending_filters:
            self._load_in_progress = False

            # Apply any pending DTO update
            if self._pending_dto_update:
                dto = self._pending_dto_update
                self._pending_dto_update = None
                self._update_widget_values(dto)

            return

        # Get the next filter
        table, column = self._pending_filters.pop(0)
        key = (table, column)

        # Check if we have cached values
        if key in self.filter_values:
            widget = self.filter_widgets.get(key)
            if widget:
                widget.blockSignals(True)
                widget.set_items(self.filter_values[key])

                # Apply pending DTO values if available
                if self._pending_dto_update:
                    attr_name = self._get_filter_dto_attribute_name(table, column)
                    if attr_name.endswith("_id"):
                        attr_name = f"{attr_name}s"

                    if hasattr(self._pending_dto_update, attr_name):
                        values = getattr(self._pending_dto_update, attr_name, [])
                        if values:
                            widget.set_selected_values(values)

                widget.blockSignals(False)

            # Process next filter
            QTimer.singleShot(50, self._load_next_filter_nonblocking)
        else:
            # Load values for this filter
            QTimer.singleShot(50, lambda: self._load_filter_values_safely(table, column))

    def _load_filter_values_safely(self, table: str, column: str) -> None:
        """
        Load filter values safely in the background.

        Args:
            table: The table name
            column: The column name
        """
        try:
            # Create a worker thread to load the values
            worker_thread = threading.Thread(
                target=self._load_filter_values_worker,
                args=(table, column),
                daemon=True,
            )
            worker_thread.start()

        except Exception as e:
            logger.error(f"Error setting up filter value loading for {table}.{column}: {e}")
            QTimer.singleShot(50, self._load_next_filter_nonblocking)

    def _load_filter_values_worker(self, table: str, column: str) -> None:
        """
        Worker function for loading filter values.

        Args:
            table: The table name
            column: The column name
        """
        try:
            # Get filter values
            filter_name = column
            values = self.service_adapter.get_filter_values_sync(table, column, column)

            # Store values
            self.filter_values[table, column] = values

            # Schedule UI update
            QTimer.singleShot(0, lambda: self._update_filter_widget_from_thread(table, column))

        except Exception as e:
            logger.error(f"Error loading filter values for {table}.{column}: {e}")
            self.filter_values[table, column] = []

            # Continue with next filter
            QTimer.singleShot(0, self._continue_filter_loading)

    @pyqtSlot(str, str)
    def _update_filter_widget_from_thread(self, table: str, column: str) -> None:
        """
        Update a filter widget from a worker thread.

        Args:
            table: The table name
            column: The column name
        """
        try:
            widget = self.filter_widgets.get((table, column))
            if widget and (table, column) in self.filter_values:
                values = self.filter_values[table, column]

                widget.blockSignals(True)
                widget.set_items(values)

                # Apply pending DTO values if available
                if self._pending_dto_update:
                    attr_name = self._get_filter_dto_attribute_name(table, column)
                    if attr_name.endswith("_id"):
                        attr_name = f"{attr_name}s"

                    if hasattr(self._pending_dto_update, attr_name):
                        dto_values = getattr(self._pending_dto_update, attr_name, [])
                        if dto_values:
                            valid_values = {value_id for value_id, _ in values}
                            valid_dto_values = [v for v in dto_values if v in valid_values]
                            widget.set_selected_values(valid_dto_values)

                widget.blockSignals(False)

        except Exception as e:
            logger.error(f"Error updating filter widget for {table}.{column} from thread: {e}")

        # Continue with next filter
        self._continue_filter_loading()

    @pyqtSlot()
    def _continue_filter_loading(self) -> None:
        """Continue loading filters."""
        QTimer.singleShot(50, self._load_next_filter_nonblocking)

    def _update_widget_values(self, filter_dto: FilterDTO) -> None:
        """
        Update widget values from a filter DTO.

        Args:
            filter_dto: The filter DTO
        """
        self._loading_filters = True
        try:
            # Update all widgets
            for (table, column), widget in self.filter_widgets.items():
                attr_name = self._get_filter_dto_attribute_name(table, column)
                if attr_name.endswith("_id"):
                    attr_name = f"{attr_name}s"

                if hasattr(filter_dto, attr_name):
                    values = getattr(filter_dto, attr_name, [])
                    if values:
                        widget.set_selected_values(values)
        finally:
            self._loading_filters = False
            self.filterChanged.emit(self.filter_dto)

    def show_filter_selection_dialog(self) -> None:
        """Show the filter selection dialog."""
        self._show_filter_selection_dialog()

    @async_slot
    async def save_current_query(self, name: str, description: str = "") -> bool:
        """
        Save the current query.

        Args:
            name: The name of the query
            description: An optional description

        Returns:
            True if the query was saved successfully, False otherwise
        """
        try:
            # Create query DTO
            query = SavedQueryDTO(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                filters=self.filter_dto,
                visible_columns=[],
                is_multi_query=False,
            )

            # Get service via migration helper or dependency injection
            self._vehicle_service = resolve(VehicleService)

            # Save the query
            result = await self._vehicle_service.save_query(query)

            if result:
                self._saved_queries[name] = query
                self.saveQueryRequested.emit(
                    self.filter_dto, self.selected_filters, name, description
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error saving query: {e}")
            return False

    @async_slot
    async def load_saved_query(self, query_name: str) -> bool:
        """
        Load a saved query.

        Args:
            query_name: The name of the query to load

        Returns:
            True if the query was loaded successfully, False otherwise
        """
        try:
            # Get service via migration helper or dependency injection
            self._vehicle_service = resolve(VehicleService)

            # Load the query
            query = await self._vehicle_service.load_query(query_name)

            if not query:
                return False

            # Set the filter DTO
            self.set_filter_dto(query.filters)

            # Emit signal
            self.loadQueryRequested.emit(query_name)

            return True

        except Exception as e:
            logger.error(f"Error loading query: {e}")
            return False

    @async_slot
    async def update_saved_queries(self) -> None:
        """Update the list of saved queries."""
        try:
            # Get service via migration helper or dependency injection
            self._vehicle_service = resolve(VehicleService)

            # Get saved queries
            self._saved_queries = await self._vehicle_service.get_saved_queries()

        except Exception as e:
            logger.error(f"Error loading saved queries: {e}")