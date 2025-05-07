from __future__ import annotations

"""
Enhanced filter widget for the InitialDB application.

This module provides a flexible filter widget that supports various filter types
including text, selection, and range filters.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, TypeVar, Generic, cast
from enum import Enum, auto
import structlog
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QCompleter, QToolButton, QSlider, QSpinBox, QDoubleSpinBox,
    QSizePolicy, QToolTip, QMenu, QFrame
)

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class FilterType(Enum):
    """Types of filters supported by the widget."""
    TEXT = auto()
    SELECTION = auto()
    RANGE = auto()
    NUMERIC = auto()


class EnhancedFilterWidget(QWidget):
    """
    Enhanced filter widget supporting various filter types.

    This widget provides UI components for filtering data with text search,
    selection from a list, numeric comparisons, or value ranges.
    """

    filterChanged = Signal(str, object)
    filterRemoved = Signal(str)

    def __init__(
            self,
            column_name: str,
            display_name: str,
            filter_type: FilterType = FilterType.TEXT,
            available_values: Optional[List[Any]] = None,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the filter widget.

        Args:
            column_name: Database column name
            display_name: Human-readable display name
            filter_type: Type of filter (text, selection, range, numeric)
            available_values: List of available values for selection
            parent: Parent widget
        """
        super().__init__(parent)
        self.column_name = column_name
        self.display_name = display_name
        self.filter_type = filter_type
        self.available_values = available_values or []
        self._current_value: Any = None
        self._range_values: Tuple[Optional[float], Optional[float]] = (None, None)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(f'{self.display_name}:')
        layout.addWidget(self.label)

        # Create filter UI based on type
        if self.filter_type == FilterType.TEXT:
            self._init_text_filter(layout)
        elif self.filter_type == FilterType.SELECTION:
            self._init_selection_filter(layout)
        elif self.filter_type == FilterType.RANGE:
            self._init_range_filter(layout)
        elif self.filter_type == FilterType.NUMERIC:
            self._init_numeric_filter(layout)

        # Add remove button
        self.remove_btn = QToolButton()
        self.remove_btn.setText('✕')
        self.remove_btn.setToolTip(f'Remove {self.display_name} filter')
        self.remove_btn.clicked.connect(self._remove_filter)
        layout.addWidget(self.remove_btn)

    def _init_text_filter(self, layout: QHBoxLayout) -> None:
        """
        Initialize a text-based filter.

        Args:
            layout: Layout to add the filter to
        """
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(f'Filter by {self.display_name.lower()}...')
        self.filter_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.filter_edit, 1)

        # Add auto-complete if values are available
        if self.available_values:
            completer = QCompleter([str(val) for val in self.available_values])
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.filter_edit.setCompleter(completer)

        # Add dropdown for available values
        if self.available_values:
            self.dropdown_btn = QToolButton()
            self.dropdown_btn.setText('▼')
            self.dropdown_btn.setToolTip('Show available values')
            self.dropdown_btn.clicked.connect(self._show_values_menu)
            layout.addWidget(self.dropdown_btn)

    def _init_selection_filter(self, layout: QHBoxLayout) -> None:
        """
        Initialize a selection-based filter with dropdown.

        Args:
            layout: Layout to add the filter to
        """
        self.filter_combo = QComboBox()
        self.filter_combo.setEditable(True)
        self.filter_combo.addItem('')

        if self.available_values:
            for value in self.available_values:
                self.filter_combo.addItem(str(value))

        self.filter_combo.currentTextChanged.connect(self._on_selection_changed)
        layout.addWidget(self.filter_combo, 1)

    def _init_range_filter(self, layout: QHBoxLayout) -> None:
        """
        Initialize a range-based filter with min/max inputs.

        Args:
            layout: Layout to add the filter to
        """
        range_layout = QHBoxLayout()

        # Determine min/max values from available data
        min_val, max_val = (0, 100)
        if self.available_values:
            # Extract numeric values
            numeric_values = [
                float(val) for val in self.available_values
                if str(val).replace('.', '', 1).isdigit()
            ]
            if numeric_values:
                min_val, max_val = (min(numeric_values), max(numeric_values))

        # From value
        self.from_label = QLabel('From:')
        range_layout.addWidget(self.from_label)

        if isinstance(min_val, int) and isinstance(max_val, int):
            self.from_spin = QSpinBox()
            self.from_spin.setRange(min_val, max_val)
            self.to_spin = QSpinBox()
            self.to_spin.setRange(min_val, max_val)
            self.to_spin.setValue(max_val)
        else:
            self.from_spin = QDoubleSpinBox()
            self.from_spin.setRange(min_val, max_val)
            self.from_spin.setDecimals(2)
            self.to_spin = QDoubleSpinBox()
            self.to_spin.setRange(min_val, max_val)
            self.to_spin.setDecimals(2)
            self.to_spin.setValue(max_val)

        self.from_spin.valueChanged.connect(self._on_range_changed)
        range_layout.addWidget(self.from_spin)

        # To value
        self.to_label = QLabel('To:')
        range_layout.addWidget(self.to_label)

        self.to_spin.valueChanged.connect(self._on_range_changed)
        range_layout.addWidget(self.to_spin)

        layout.addLayout(range_layout)

    def _init_numeric_filter(self, layout: QHBoxLayout) -> None:
        """
        Initialize a numeric filter with operator selection.

        Args:
            layout: Layout to add the filter to
        """
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(f'Filter by {self.display_name.lower()}...')
        self.filter_edit.textChanged.connect(self._on_numeric_changed)
        layout.addWidget(self.filter_edit, 1)

        # Operator dropdown
        self.op_btn = QToolButton()
        self.op_btn.setText('=')
        self.op_btn.setToolTip('Set comparison operator')

        op_menu = QMenu(self)
        for op in ['=', '>', '<', '>=', '<=', '≠']:
            action = op_menu.addAction(op)
            action.triggered.connect(lambda checked, o=op: self._set_operator(o))

        self.op_btn.setMenu(op_menu)
        self.op_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        layout.insertWidget(1, self.op_btn)

        self.current_operator = '='

    def _set_operator(self, operator: str) -> None:
        """
        Set the numeric comparison operator.

        Args:
            operator: Comparison operator (=, >, <, etc.)
        """
        self.current_operator = operator
        self.op_btn.setText(operator)
        self._on_numeric_changed(self.filter_edit.text())

    def _on_text_changed(self, text: str) -> None:
        """
        Handle text filter value changes.

        Args:
            text: New filter text
        """
        self._current_value = text
        self.filterChanged.emit(self.column_name, text)

    def _on_selection_changed(self, text: str) -> None:
        """
        Handle selection filter value changes.

        Args:
            text: Selected item text
        """
        self._current_value = text
        self.filterChanged.emit(self.column_name, text)

    def _on_range_changed(self) -> None:
        """Handle range filter value changes."""
        from_val = self.from_spin.value()
        to_val = self.to_spin.value()

        # Ensure from <= to
        if from_val > to_val:
            if self.sender() == self.from_spin:
                self.to_spin.setValue(from_val)
            else:
                self.from_spin.setValue(to_val)

        self._range_values = (from_val, to_val)
        self.filterChanged.emit(self.column_name, self._range_values)

    def _on_numeric_changed(self, text: str) -> None:
        """
        Handle numeric filter value changes.

        Args:
            text: New numeric text
        """
        if not text:
            self._current_value = None
            self.filterChanged.emit(self.column_name, None)
            return

        try:
            value = float(text)
            self._current_value = (self.current_operator, value)
            self.filterChanged.emit(self.column_name, self._current_value)
        except ValueError:
            pass

    def _show_values_menu(self) -> None:
        """Show dropdown menu with available filter values."""
        if not self.available_values:
            return

        menu = QMenu(self)
        for value in self.available_values:
            str_value = str(value)
            action = menu.addAction(str_value)
            action.triggered.connect(lambda checked, v=str_value: self._select_value(v))

        menu.exec(self.dropdown_btn.mapToGlobal(self.dropdown_btn.rect().bottomLeft()))

    def _select_value(self, value: str) -> None:
        """
        Select a value from the dropdown.

        Args:
            value: Selected value as string
        """
        if self.filter_type == FilterType.TEXT:
            self.filter_edit.setText(value)
        elif self.filter_type == FilterType.SELECTION:
            self.filter_combo.setCurrentText(value)

    def _remove_filter(self) -> None:
        """Remove this filter widget."""
        self.filterRemoved.emit(self.column_name)
        self.setParent(None)
        self.deleteLater()

    def get_value(self) -> Any:
        """
        Get the current filter value.

        Returns:
            Current filter value
        """
        if self.filter_type == FilterType.RANGE:
            return self._range_values
        return self._current_value

    def set_value(self, value: Any) -> None:
        """
        Set the filter value.

        Args:
            value: New filter value
        """
        if value is None:
            return

        if self.filter_type == FilterType.TEXT:
            self.filter_edit.setText(str(value))
        elif self.filter_type == FilterType.SELECTION:
            self.filter_combo.setCurrentText(str(value))
        elif self.filter_type == FilterType.RANGE:
            if isinstance(value, tuple) and len(value) == 2:
                from_val, to_val = value
                if from_val is not None:
                    self.from_spin.setValue(from_val)
                if to_val is not None:
                    self.to_spin.setValue(to_val)
        elif self.filter_type == FilterType.NUMERIC:
            if isinstance(value, tuple) and len(value) == 2:
                operator, num_value = value
                self._set_operator(operator)
                self.filter_edit.setText(str(num_value))
            else:
                self.filter_edit.setText(str(value))