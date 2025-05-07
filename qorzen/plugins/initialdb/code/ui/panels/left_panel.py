from __future__ import annotations

from ...config import settings

"""
Left panel for the InitialDB application.

This module provides the left panel implementation, with support for
query building, database exploration, and other navigation features.
"""

from typing import Dict, List, Optional, Type, cast

import structlog
from PyQt6.QtCore import QSettings, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ..query_panel.query_panel import MultiQueryPanel
from .panel_base import PanelBase, PanelContent

logger = structlog.get_logger(__name__)


class QueryContent(PanelContent):
    """Query builder content for the left panel."""

    query_executed = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the query content.

        Args:
            parent: The parent widget
        """
        # Create query panel BEFORE calling super().__init__
        # This ensures it exists before _setup_ui is called
        self.query_panel = MultiQueryPanel(parent)

        # Now call super().__init__ which will call _setup_ui
        super().__init__(parent)

        # Connect signals after initialization is complete
        self.query_panel.executeQueryRequested.connect(self._on_query_executed)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = self.layout()

        # Add the query panel to layout
        if hasattr(self, 'query_panel'):
            layout.addWidget(self.query_panel)

    def _on_query_executed(self, results: object) -> None:
        """
        Handle query execution.

        Args:
            results: The query results
        """
        self.query_executed.emit(results)

    def activate(self) -> None:
        """Called when this content is activated."""
        super().activate()

    def deactivate(self) -> None:
        """Called when this content is deactivated."""
        super().deactivate()

    def save_state(self) -> Dict:
        """
        Save the content state.

        Returns:
            Dictionary with the state
        """
        return {
            "filter_dtos": self.query_panel.get_all_filter_dtos_serialized() if hasattr(self.query_panel,
                                                                                        "get_all_filter_dtos_serialized") else {}
        }

    def restore_state(self, state: Dict) -> None:
        """
        Restore the content state.

        Args:
            state: Dictionary with the state
        """
        filter_dtos = state.get("filter_dtos", {})
        if hasattr(self.query_panel, "set_all_filter_dtos"):
            self.query_panel.set_all_filter_dtos(filter_dtos)


class DatabaseExplorerContent(PanelContent):
    """Database explorer content for the left panel."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the database explorer content.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = self.layout()

        # Placeholder for database explorer
        # This would be replaced with actual database explorer implementation
        self.explorer_widget = QWidget()
        explorer_layout = QVBoxLayout(self.explorer_widget)
        explorer_layout.addWidget(QWidget())  # Placeholder

        layout.addWidget(self.explorer_widget)


class SavedQueriesContent(PanelContent):
    """Saved queries content for the left panel."""

    query_loaded = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the saved queries content.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = self.layout()

        # Placeholder for saved queries list
        # This would be replaced with actual saved queries implementation
        self.queries_widget = QWidget()
        queries_layout = QVBoxLayout(self.queries_widget)
        queries_layout.addWidget(QWidget())  # Placeholder

        layout.addWidget(self.queries_widget)


class LeftPanel(PanelBase):
    """Left panel with query building and database exploration."""

    query_executed = pyqtSignal(object)
    query_loaded = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the left panel.

        Args:
            parent: The parent widget
        """
        super().__init__("Navigation", parent)
        self._setup_contents()

    def _setup_contents(self) -> None:
        """Set up the panel contents."""
        # Query Builder content
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

        # Database Explorer content
        self.explorer_content = DatabaseExplorerContent(self)
        self.add_content(
            "explorer",
            self.explorer_content,
            button_text="Database Explorer" if settings.get("enable_left_panel_button_text") else None,
            icon_name="database",
            tooltip="Database Explorer"
        )

        # Saved Queries content
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
        """
        Get the query panel.

        Returns:
            The query panel instance
        """
        return self.query_content.query_panel