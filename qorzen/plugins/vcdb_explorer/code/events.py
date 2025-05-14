# processed_project/qorzen_stripped/plugins/vcdb_explorer/code/events.py
from __future__ import annotations

from qorzen.core.event_model import EventType


class VCdbEventType:
    """VCdb Explorer plugin-specific event types."""

    @staticmethod
    def filter_changed() -> str:
        """Event emitted when a filter has been changed."""
        return "plugin/vcdb_explorer/filter_changed"

    @staticmethod
    def filters_refreshed() -> str:
        """Event emitted when filters have been refreshed."""
        return "plugin/vcdb_explorer/filters_refreshed"

    @staticmethod
    def query_execute() -> str:
        """Event emitted to request query execution."""
        return "plugin/vcdb_explorer/query_execute"

    @staticmethod
    def query_results() -> str:
        """Event emitted when query results are available."""
        return "plugin/vcdb_explorer/query_results"