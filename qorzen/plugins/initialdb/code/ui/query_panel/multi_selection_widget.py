from __future__ import annotations

from PySide6 import sip

"""
Multi-selection widget component for the InitialDB application.

This module provides a custom widget for selecting multiple values from a list,
replacing the standard QComboBox with a more flexible selection interface.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, cast

import structlog
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QScrollArea,
    QLineEdit,
    QFrame,
    QDialog,
    QToolButton,
    QApplication
)
from PySide6.QtGui import QIcon, QFont, QColor

logger = structlog.get_logger(__name__)


class MultiSelectionDialog(QDialog):
    """Dialog for selecting multiple items from a list."""

    selectionChanged = Signal(list)

    def __init__(
            self,
            title: str,
            items: List[Tuple[Any, str]],
            selected_values: List[Any] = None,
            parent: Optional[QWidget] = None,
            searchable: bool = True,
    ) -> None:
        """
        Initialize the multi-selection dialog.

        Args:
            title: The title of the dialog
            items: The list of (value, display_text) tuples to select from
            selected_values: The currently selected values
            parent: The parent widget
            searchable: Whether the dialog should be searchable
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 500)
        self.items = items
        self.selected_values = selected_values or []
        self.searchable = searchable
        self._init_ui()
        self._populate_list()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Add search field if searchable
        if self.searchable:
            search_layout = QHBoxLayout()
            search_label = QLabel("Search:")
            self.search_field = QLineEdit()
            self.search_field.setPlaceholderText("Type to filter items...")
            self.search_field.textChanged.connect(self._filter_items)
            search_layout.addWidget(search_label)
            search_layout.addWidget(self.search_field)
            layout.addLayout(search_layout)

        # Selection count label
        self.count_label = QLabel("0 items selected")
        layout.addWidget(self.count_label)

        # List widget for items
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget)

        # Selection buttons
        selection_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        selection_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        selection_layout.addWidget(deselect_all_btn)

        invert_btn = QPushButton("Invert Selection")
        invert_btn.clicked.connect(self._invert_selection)
        selection_layout.addWidget(invert_btn)

        layout.addLayout(selection_layout)

        # Dialog buttons
        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def _populate_list(self) -> None:
        """Populate the list with items."""
        if sip.isdeleted(self.list_widget):
            logger.warning("QListWidget is deleted — skipping _populate_list")
            return

        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        logger.debug(f"Populating list with {len(self.items)} items")
        if self.items:
            logger.debug(f"First 5 items: {self.items[:5]}")
            logger.debug(f"Currently selected values: {self.selected_values}")

        for i, item_data in enumerate(self.items):
            if sip.isdeleted(self.list_widget):
                logger.warning("QListWidget was deleted mid-loop — exiting")
                return
            try:
                if not isinstance(item_data, tuple) or len(item_data) < 2:
                    logger.warning(f"Invalid item format at index {i}: {item_data}")
                    continue

                value_id, display_text = item_data

                if not isinstance(display_text, str):
                    display_text = str(display_text)

                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, value_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

                if value_id in self.selected_values:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)

                self.list_widget.addItem(item)

            except Exception as e:
                logger.error(f"Error adding item {i}: {str(e)}")

        self.list_widget.blockSignals(False)
        self._update_count_label()

    def _filter_items(self, text: str) -> None:
        """
        Filter the items by text.

        Args:
            text: The text to filter by
        """
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item:
                continue

            should_show = True
            if text:
                item_text = item.text().lower()
                should_show = text.lower() in item_text

            self.list_widget.setRowHidden(i, not should_show)

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        """
        Handle item changed events.

        Args:
            item: The item that changed
        """
        value = item.data(Qt.ItemDataRole.UserRole)
        is_checked = item.checkState() == Qt.CheckState.Checked

        if is_checked and value not in self.selected_values:
            self.selected_values.append(value)
        elif not is_checked and value in self.selected_values:
            self.selected_values.remove(value)

        self._update_count_label()

    def _select_all(self) -> None:
        """Select all visible items."""
        self.list_widget.blockSignals(True)
        self.selected_values.clear()

        for i in range(self.list_widget.count()):
            if self.list_widget.isRowHidden(i):
                continue

            item = self.list_widget.item(i)
            if not item:
                continue

            item.setCheckState(Qt.CheckState.Checked)
            value = item.data(Qt.ItemDataRole.UserRole)
            if value not in self.selected_values:
                self.selected_values.append(value)

        self.list_widget.blockSignals(False)
        self._update_count_label()

    def _deselect_all(self) -> None:
        """Deselect all visible items."""
        self.list_widget.blockSignals(True)
        visible_values = []

        for i in range(self.list_widget.count()):
            if self.list_widget.isRowHidden(i):
                continue

            item = self.list_widget.item(i)
            if not item:
                continue

            item.setCheckState(Qt.CheckState.Unchecked)
            value = item.data(Qt.ItemDataRole.UserRole)
            visible_values.append(value)

        self.selected_values = [v for v in self.selected_values if v not in visible_values]
        self.list_widget.blockSignals(False)
        self._update_count_label()

    def _invert_selection(self) -> None:
        """Invert the selection of all visible items."""
        self.list_widget.blockSignals(True)

        for i in range(self.list_widget.count()):
            if self.list_widget.isRowHidden(i):
                continue

            item = self.list_widget.item(i)
            if not item:
                continue

            value = item.data(Qt.ItemDataRole.UserRole)

            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)
                if value in self.selected_values:
                    self.selected_values.remove(value)
            else:
                item.setCheckState(Qt.CheckState.Checked)
                if value not in self.selected_values:
                    self.selected_values.append(value)

        self.list_widget.blockSignals(False)
        self._update_count_label()

    def _update_count_label(self) -> None:
        """Update the count label with the number of selected items."""
        count = len(self.selected_values)
        self.count_label.setText(f"{count} item{('s' if count != 1 else '')} selected")

    def get_selected_values(self) -> List[Any]:
        """
        Get the selected values.

        Returns:
            A list of selected values
        """
        return self.selected_values


class MultiSelectionWidget(QWidget):
    """Widget for selecting multiple values."""

    selectionChanged = Signal(list)

    def __init__(
            self, title: str, parent: Optional[QWidget] = None, searchable: bool = True
    ) -> None:
        """
        Initialize the multi-selection widget.

        Args:
            title: The title of the widget
            parent: The parent widget
            searchable: Whether the selection dialog should be searchable
        """
        super().__init__(parent)
        self.title = title
        self.searchable = searchable
        self.items: List[Tuple[Any, str]] = []
        self.selected_values: List[Any] = []
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Display label for the selection
        self.selection_display = QLabel("Any")
        layout.addWidget(self.selection_display)

        # Button to open the selection dialog
        self.select_button = QPushButton("...")
        self.select_button.setFixedWidth(30)
        self.select_button.clicked.connect(self._show_selection_dialog)
        layout.addWidget(self.select_button)

        # Button to clear the selection
        self.clear_button = QToolButton()
        self.clear_button.setText("X")
        self.clear_button.setFixedWidth(20)
        self.clear_button.clicked.connect(self._clear_selection)
        layout.addWidget(self.clear_button)
        self.dialog = None

    def _show_selection_dialog(self) -> None:
        """Show the selection dialog."""
        logger.debug(f"Opening selection dialog with {len(self.items)} items")
        if self.items:
            logger.debug(f"First 5 items: {self.items[:5]}")
            logger.debug(f"Currently selected values: {self.selected_values}")

        if self.dialog:
            self.dialog.close()
        # Create and show the dialog
        self.dialog = MultiSelectionDialog(
            self.title, self.items, self.selected_values, None, self.searchable  # parent=None
        )
        self.dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        # Process the result
        try:
            if self.dialog.exec() == QDialog.DialogCode.Accepted:
                new_selected = self.dialog.get_selected_values()
                if new_selected != self.selected_values:
                    self.selected_values = new_selected
                    self._update_display()
                    self.selectionChanged.emit(self.selected_values)
        finally:
            self.dialog = None

    def _clear_selection(self) -> None:
        """Clear the selection."""
        if self.selected_values:
            self.selected_values.clear()
            self._update_display()
            self.selectionChanged.emit(self.selected_values)

    def _update_display(self) -> None:
        """Update the displayed selection."""
        if not self.selected_values:
            self.selection_display.setText("Any")
            self.selection_display.setToolTip("")
            return

        # Build the display text
        display_values = []
        found_display = set()

        for value in self.selected_values:
            found = False
            for item_id, item_display in self.items:
                if item_id == value:
                    display_values.append(str(item_display))
                    found_display.add(value)
                    found = True
                    break

            if not found:
                display_values.append(str(value))

        # Format the display text
        if len(display_values) <= 2:
            text = ", ".join(display_values)
        else:
            text = f"{display_values[0]}, {display_values[1]} + {len(display_values) - 2} more"

        self.selection_display.setText(text)
        self.selection_display.setToolTip("\n".join(display_values))

    def set_items(self, items: List[Tuple[Any, str]]) -> None:
        """
        Set the available items.

        Args:
            items: A list of (value, display_text) tuples
        """
        logger.debug(f"Setting {len(items)} items")
        if items:
            logger.debug(f"First 5 items: {items[:5]}")

        validated_items = []

        # Validate each item
        for i, item in enumerate(items):
            if not isinstance(item, tuple) or len(item) < 2:
                logger.warning(f"Invalid item format at index {i}: {item}, converting to tuple")
                if isinstance(item, (int, str, float)):
                    validated_items.append((item, str(item)))
                else:
                    continue
            else:
                id_val, display_val = item
                if not isinstance(display_val, str):
                    display_val = str(display_val)
                validated_items.append((id_val, display_val))

        self.items = validated_items

        # Filter selected values to keep only those that are in the new items
        valid_values = {id_val for id_val, _ in self.items}
        self.selected_values = [v for v in self.selected_values if v in valid_values]

        self._update_display()

    def set_selected_values(self, values: List[Any]) -> None:
        """
        Set the selected values.

        Args:
            values: A list of values to select
        """
        if values != self.selected_values:
            self.selected_values = values
            self._update_display()
            self.selectionChanged.emit(self.selected_values)

    def get_selected_values(self) -> List[Any]:
        """
        Get the selected values.

        Returns:
            A list of selected values
        """
        return self.selected_values

    def clear(self) -> None:
        """Clear the widget."""
        self.items.clear()
        self.selected_values.clear()
        self.selection_display.setText("Any")
        self.selection_display.setToolTip("")