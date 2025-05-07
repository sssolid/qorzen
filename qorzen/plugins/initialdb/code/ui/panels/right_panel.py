# right_panel.py

from __future__ import annotations

"""
Right panel for the InitialDB application.

This module provides the right panel implementation with a tab-based interface
for displaying query results, data visualizations, and other content.
"""

from typing import Dict, Optional

import structlog
from PySide6.QtCore import QSettings, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QTabBar, QTabWidget, QVBoxLayout, QWidget

from ...utils.schema_registry import SchemaRegistry
from ..results_panel import ResultsPanel
from .panel_base import PanelBase, PanelContent

logger = structlog.get_logger(__name__)


class RightPanel(PanelBase):
    """Right panel with tabbed interface for results and other content."""

    tab_added = Signal(str, str)
    tab_closed = Signal(str)
    tab_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Results", parent)
        self._setup_ui()
        self._tab_count = 0
        self._tabs: Dict[str, QWidget] = {}
        self._tab_titles: Dict[str, str] = {}

    def _setup_ui(self) -> None:
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._tab_changed)
        self.main_layout.addWidget(self.tab_widget)

    def add_tab(self, widget: QWidget, title: str, tab_id: Optional[str] = None, icon: Optional[QIcon] = None) -> str:
        if tab_id is None:
            self._tab_count += 1
            tab_id = f"tab_{self._tab_count}"
        index = self.tab_widget.addTab(widget, title)
        if icon:
            self.tab_widget.setTabIcon(index, icon)
        self._tabs[tab_id] = widget
        self._tab_titles[tab_id] = title
        self.tab_widget.setCurrentIndex(index)
        self.tab_added.emit(tab_id, title)
        return tab_id

    def get_tab(self, tab_id: str) -> Optional[QWidget]:
        return self._tabs.get(tab_id)

    def get_tab_by_index(self, index: int) -> Optional[tuple[str, QWidget]]:
        if 0 <= index < self.tab_widget.count():
            widget = self.tab_widget.widget(index)
            for tid, w in self._tabs.items():
                if w == widget:
                    return tid, w
        return None

    def get_current_tab(self) -> Optional[tuple[str, QWidget]]:
        return self.get_tab_by_index(self.tab_widget.currentIndex())

    def select_tab(self, tab_id: str) -> bool:
        widget = self._tabs.get(tab_id)
        if widget:
            idx = self.tab_widget.indexOf(widget)
            if idx >= 0:
                self.tab_widget.setCurrentIndex(idx)
                return True
        return False

    def rename_tab(self, tab_id: str, new_title: str) -> bool:
        widget = self._tabs.get(tab_id)
        if widget:
            idx = self.tab_widget.indexOf(widget)
            if idx >= 0:
                self.tab_widget.setTabText(idx, new_title)
                self._tab_titles[tab_id] = new_title
                return True
        return False

    def _close_tab(self, index: int) -> None:
        info = self.get_tab_by_index(index)
        if info:
            tid, _ = info
            self.tab_widget.removeTab(index)
            self._tabs.pop(tid, None)
            self._tab_titles.pop(tid, None)
            self.tab_closed.emit(tid)

    def _tab_changed(self, index: int) -> None:
        info = self.get_tab_by_index(index)
        if info:
            tid, _ = info
            self.tab_selected.emit(tid)

    def close_all_tabs(self) -> None:
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        self._tabs.clear()
        self._tab_titles.clear()

    def save_state(self) -> Dict:
        tab_states = {}
        for tid, widget in self._tabs.items():
            if hasattr(widget, "save_state"):
                tab_states[tid] = {
                    "title": self._tab_titles.get(tid, ""),
                    "state": widget.save_state()
                }
        active = self.get_current_tab()
        active_id = active[0] if active else None
        return {"active_tab_id": active_id, "tab_states": tab_states}

    def restore_state(self, state: Dict) -> None:
        active = state.get("active_tab_id")
        if active:
            self.select_tab(active)

    def create_results_tab(self, title: Optional[str] = None) -> tuple[str, ResultsPanel]:
        if title is None:
            self._tab_count += 1
            title = f"Results {self._tab_count}"
        results_panel = ResultsPanel(parent=self)
        tab_id = self.add_tab(results_panel, title)
        return tab_id, results_panel
