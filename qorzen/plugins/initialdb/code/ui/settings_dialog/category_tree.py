from __future__ import annotations

"""
Tree view for displaying and navigating settings categories.

This module provides a specialized tree widget for showing settings categories
with proper styling and search functionality.
"""

from typing import Dict, List, Optional, Set

import structlog
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from .models import SettingsCategory, SettingsRegistry

logger = structlog.get_logger(__name__)


class CategoryTree(QWidget):
    """Widget for displaying and selecting settings categories."""

    category_selected = Signal(str)  # Emits the ID of the selected category

    def __init__(
            self,
            settings_registry: SettingsRegistry,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the category tree widget.

        Args:
            settings_registry: The registry containing all settings categories
            parent: The parent widget
        """
        super().__init__(parent)
        self.settings_registry = settings_registry

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search settings...")
        self.search_edit.textChanged.connect(self._filter_categories)
        layout.addWidget(self.search_edit)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIconSize(QSize(20, 20))
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.tree)

        self._items_by_id: Dict[str, QTreeWidgetItem] = {}
        self._expanded_items: Set[str] = set()

        # Populate tree with categories
        self._populate_tree()

    def _populate_tree(self) -> None:
        """Populate the tree with categories from the registry."""
        self.tree.clear()
        self._items_by_id.clear()

        # Add all top-level categories
        for category in self.settings_registry.categories:
            self._add_category(category, None)

        # Expand all top-level categories by default
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setExpanded(True)

    def _add_category(self, category: SettingsCategory, parent: Optional[QTreeWidgetItem]) -> QTreeWidgetItem:
        """
        Add a category to the tree.

        Args:
            category: The category to add
            parent: The parent tree item, or None for top-level categories

        Returns:
            The created tree item
        """
        if not category.visible:
            return None

        # Create the tree item
        item = QTreeWidgetItem(parent or self.tree)
        item.setText(0, category.name)
        item.setData(0, Qt.ItemDataRole.UserRole, category.id)

        # Set icon if available
        if category.icon_name and hasattr(QIcon, "fromTheme"):
            icon = QIcon.fromTheme(category.icon_name)
            if not icon.isNull():
                item.setIcon(0, icon)

        # Add all subcategories
        for subcategory in category.subcategories:
            self._add_category(subcategory, item)

        # Store the item by category ID for lookup
        self._items_by_id[category.id] = item

        return item

    def _on_selection_changed(self) -> None:
        """Handle selection change in the tree."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        category_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.category_selected.emit(category_id)

    def select_category(self, category_id: str) -> bool:
        """
        Select a category by ID.

        Args:
            category_id: The ID of the category to select

        Returns:
            True if the category was found and selected, False otherwise
        """
        if category_id in self._items_by_id:
            item = self._items_by_id[category_id]
            self.tree.setCurrentItem(item)
            return True
        return False

    def _filter_categories(self, search_text: str) -> None:
        """
        Filter the categories based on search text.

        Args:
            search_text: The text to search for
        """
        # Remember expanded items
        self._expanded_items.clear()
        for category_id, item in self._items_by_id.items():
            if item.isExpanded():
                self._expanded_items.add(category_id)

        # Clear and repopulate the tree
        self.tree.clear()
        self._items_by_id.clear()

        if not search_text:
            # No search, show all categories
            for category in self.settings_registry.categories:
                self._add_category(category, None)

            # Restore expanded state
            for category_id, item in self._items_by_id.items():
                if category_id in self._expanded_items:
                    item.setExpanded(True)
        else:
            # Search for matching categories
            search_text = search_text.lower()
            self._add_matching_categories(self.settings_registry.categories, search_text)

            # Expand all items for better visibility
            for i in range(self.tree.topLevelItemCount()):
                self._expand_all(self.tree.topLevelItem(i))

    def _add_matching_categories(self, categories: List[SettingsCategory], search_text: str) -> None:
        """
        Add categories that match the search text.

        Args:
            categories: List of categories to check
            search_text: The text to search for
        """
        for category in categories:
            if not category.visible:
                continue

            # Check if this category or any subcategory matches
            category_matches = (
                    search_text in category.name.lower() or
                    search_text in category.description.lower()
            )

            # Add the category if it matches
            if category_matches:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, category.name)
                item.setData(0, Qt.ItemDataRole.UserRole, category.id)
                self._items_by_id[category.id] = item

                # Also add all subcategories
                for subcategory in category.subcategories:
                    if subcategory.visible:
                        subitem = QTreeWidgetItem(item)
                        subitem.setText(0, subcategory.name)
                        subitem.setData(0, Qt.ItemDataRole.UserRole, subcategory.id)
                        self._items_by_id[subcategory.id] = subitem
            else:
                # Check subcategories separately
                self._add_matching_categories(category.subcategories, search_text)

    def _expand_all(self, item: QTreeWidgetItem) -> None:
        """
        Recursively expand an item and all its children.

        Args:
            item: The item to expand
        """
        item.setExpanded(True)
        for i in range(item.childCount()):
            self._expand_all(item.child(i))