from __future__ import annotations

"""
Right panel for the InitialDB application.

This module provides the right panel implementation with a tab-based interface
for displaying query results, data visualizations, and other content.
"""

from typing import Dict, List, Optional, Type, cast

import structlog
from PyQt6.QtCore import QSettings, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout, QTabBar, QTabWidget, QVBoxLayout, QWidget
)

from ...utils.schema_registry import SchemaRegistry
from ..results_panel import ResultsPanel
from .panel_base import PanelBase, PanelContent

logger = structlog.get_logger(__name__)


class RightPanel(PanelBase):
    """Right panel with tabbed interface for results and other content."""

    tab_added = pyqtSignal(str, str)
    tab_closed = pyqtSignal(str)
    tab_selected = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the right panel.

        Args:
            parent: The parent widget
        """
        super().__init__("Results", parent)
        self._setup_ui()

        # Track tabs
        self._tab_count = 0
        self._tabs: Dict[str, QWidget] = {}
        self._tab_titles: Dict[str, str] = {}

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Override the default layout setup
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        # Main layout
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._tab_changed)

        self.main_layout.addWidget(self.tab_widget)

    def add_tab(
            self,
            widget: QWidget,
            title: str,
            tab_id: Optional[str] = None,
            icon: Optional[QIcon] = None
    ) -> str:
        """
        Add a new tab with the specified widget.

        Args:
            widget: The widget to add as tab content
            title: The tab title
            tab_id: Optional custom tab ID, or auto-generated if None
            icon: Optional tab icon

        Returns:
            The tab ID
        """
        if tab_id is None:
            self._tab_count += 1
            tab_id = f"tab_{self._tab_count}"

        index = self.tab_widget.addTab(widget, title)
        if icon:
            self.tab_widget.setTabIcon(index, icon)

        self._tabs[tab_id] = widget
        self._tab_titles[tab_id] = title

        # Switch to the new tab
        self.tab_widget.setCurrentIndex(index)

        # Emit signal
        self.tab_added.emit(tab_id, title)

        return tab_id

    def get_tab(self, tab_id: str) -> Optional[QWidget]:
        """
        Get a tab widget by ID.

        Args:
            tab_id: The tab ID

        Returns:
            The tab widget or None
        """
        return self._tabs.get(tab_id)

    def get_tab_by_index(self, index: int) -> Optional[tuple[str, QWidget]]:
        """
        Get a tab by index.

        Args:
            index: The tab index

        Returns:
            Tuple of (tab_id, widget) or None
        """
        if 0 <= index < self.tab_widget.count():
            widget = self.tab_widget.widget(index)
            for tab_id, tab_widget in self._tabs.items():
                if tab_widget == widget:
                    return tab_id, widget
        return None

    def get_current_tab(self) -> Optional[tuple[str, QWidget]]:
        """
        Get the currently selected tab.

        Returns:
            Tuple of (tab_id, widget) or None
        """
        index = self.tab_widget.currentIndex()
        return self.get_tab_by_index(index)

    def select_tab(self, tab_id: str) -> bool:
        """
        Select a tab by ID.

        Args:
            tab_id: The tab ID

        Returns:
            True if the tab was found and selected, False otherwise
        """
        if tab_id not in self._tabs:
            return False

        widget = self._tabs[tab_id]
        index = self.tab_widget.indexOf(widget)
        if index >= 0:
            self.tab_widget.setCurrentIndex(index)
            return True
        return False

    def rename_tab(self, tab_id: str, new_title: str) -> bool:
        """
        Rename a tab.

        Args:
            tab_id: The tab ID
            new_title: The new tab title

        Returns:
            True if the tab was found and renamed, False otherwise
        """
        if tab_id not in self._tabs:
            return False

        widget = self._tabs[tab_id]
        index = self.tab_widget.indexOf(widget)
        if index >= 0:
            self.tab_widget.setTabText(index, new_title)
            self._tab_titles[tab_id] = new_title
            return True
        return False

    def _close_tab(self, index: int) -> None:
        """
        Close a tab by index.

        Args:
            index: The tab index
        """
        tab_info = self.get_tab_by_index(index)
        if tab_info:
            tab_id, widget = tab_info
            self.tab_widget.removeTab(index)
            self._tabs.pop(tab_id, None)
            self._tab_titles.pop(tab_id, None)
            self.tab_closed.emit(tab_id)

    def _tab_changed(self, index: int) -> None:
        """
        Handle tab selection change.

        Args:
            index: The new tab index
        """
        tab_info = self.get_tab_by_index(index)
        if tab_info:
            tab_id, _ = tab_info
            self.tab_selected.emit(tab_id)

    def close_all_tabs(self) -> None:
        """Close all open tabs."""
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        self._tabs.clear()
        self._tab_titles.clear()

    def save_state(self) -> Dict:
        """
        Save the panel state.

        Returns:
            Dictionary with the state
        """
        tab_states = {}
        active_tab_id = None

        current_tab = self.get_current_tab()
        if current_tab:
            active_tab_id = current_tab[0]

        # Save individual tab states
        for tab_id, widget in self._tabs.items():
            if hasattr(widget, "save_state") and callable(getattr(widget, "save_state")):
                tab_states[tab_id] = {
                    "title": self._tab_titles.get(tab_id, ""),
                    "state": widget.save_state()
                }

        return {
            "active_tab_id": active_tab_id,
            "tab_states": tab_states
        }

    def restore_state(self, state: Dict) -> None:
        """
        Restore the panel state.

        Args:
            state: Dictionary with the state
        """
        # This is a simplified implementation - in a real application,
        # you would need to recreate tabs based on their type and restore
        # their individual states

        active_tab_id = state.get("active_tab_id")
        if active_tab_id and active_tab_id in self._tabs:
            self.select_tab(active_tab_id)

    def create_results_tab(self, title: Optional[str] = None) -> tuple[str, ResultsPanel]:
        """
        Create a new results tab.

        Args:
            title: Optional tab title, defaults to "Results"

        Returns:
            Tuple of (tab_id, results_panel)
        """
        if title is None:
            self._tab_count += 1
            title = f"Results {self._tab_count}"

        # Create results panel
        results_panel = ResultsPanel(parent=self)

        # Add to tabs
        tab_id = self.add_tab(results_panel, title)

        return tab_id, results_panel