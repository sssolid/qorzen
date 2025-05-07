# left_panel.py

from __future__ import annotations

from ...config import settings

"""
Left panel for the InitialDB application.

This module provides the left panel implementation, with support for
query building, database exploration, and other navigation features.
"""

from typing import Dict, Optional

import structlog
from PySide6.QtCore import QSettings, QSize, Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ..query_panel.query_panel import MultiQueryPanel
from .panel_base import PanelBase, PanelContent

logger = structlog.get_logger(__name__)


class QueryContent(PanelContent):
    """Query builder content for the left panel."""

    query_executed = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.query_panel = MultiQueryPanel(parent)
        super().__init__(parent)
        self.query_panel.executeQueryRequested.connect(self._on_query_executed)

    def _setup_ui(self) -> None:
        layout = self.layout()
        layout.addWidget(self.query_panel)

    def _on_query_executed(self, results: object) -> None:
        self.query_executed.emit(results)

    def activate(self) -> None:
        super().activate()

    def deactivate(self) -> None:
        super().deactivate()

    def save_state(self) -> Dict:
        return {
            "filter_dtos": self.query_panel.get_all_filter_dtos_serialized()
                if hasattr(self.query_panel, "get_all_filter_dtos_serialized")
                else {}
        }

    def restore_state(self, state: Dict) -> None:
        filter_dtos = state.get("filter_dtos", {})
        if hasattr(self.query_panel, "set_all_filter_dtos"):
            self.query_panel.set_all_filter_dtos(filter_dtos)


class DatabaseExplorerContent(PanelContent):
    """Database explorer content for the left panel."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = self.layout()
        self.explorer_widget = QWidget()
        explorer_layout = QVBoxLayout(self.explorer_widget)
        explorer_layout.addWidget(QWidget())
        layout.addWidget(self.explorer_widget)


class SavedQueriesContent(PanelContent):
    """Saved queries content for the left panel."""

    query_loaded = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = self.layout()
        self.queries_widget = QWidget()
        queries_layout = QVBoxLayout(self.queries_widget)
        queries_layout.addWidget(QWidget())
        layout.addWidget(self.queries_widget)


class LeftPanel(PanelBase):
    """Left panel with query building and database exploration."""

    query_executed = Signal(object)
    query_loaded = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Navigation", parent)
        self._setup_contents()

    def _setup_contents(self) -> None:
        self.query_content = QueryContent(self)
        self.query_content.query_executed.connect(self.query_executed)
        self.add_content(
            "query",
            self.query_content,
            button_text="Query Builder" if settings.get("enable_left_panel_button_text") else None,
            icon_name="database-search",
            tooltip="Query Builder",
            activate=True
        )

        self.explorer_content = DatabaseExplorerContent(self)
        self.add_content(
            "explorer",
            self.explorer_content,
            button_text="Database Explorer" if settings.get("enable_left_panel_button_text") else None,
            icon_name="database",
            tooltip="Database Explorer"
        )

        self.saved_queries_content = SavedQueriesContent(self)
        self.saved_queries_content.query_loaded.connect(self.query_loaded)
        self.add_content(
            "saved_queries",
            self.saved_queries_content,
            button_text="Saved Queries" if settings.get("enable_left_panel_button_text") else None,
            icon_name="library-books",
            tooltip="Saved Queries"
        )

    def get_query_panel(self) -> MultiQueryPanel:
        return self.query_content.query_panel
