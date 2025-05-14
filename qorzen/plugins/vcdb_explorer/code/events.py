from __future__ import annotations

from qorzen.core.event_model import EventType


class VCdbEventType:
    """Event types for the VCdb Explorer plugin."""

    @staticmethod
    def filter_changed() -> str:
        """Event when a filter selection changes.

        Returns:
            Event type identifier
        """
        return 'plugin/vcdb_explorer/filter_changed'

    @staticmethod
    def filters_refreshed() -> str:
        """Event when filters are refreshed.

        Returns:
            Event type identifier
        """
        return 'plugin/vcdb_explorer/filters_refreshed'

    @staticmethod
    def query_execute() -> str:
        """Event to trigger query execution.

        Returns:
            Event type identifier
        """
        return 'plugin/vcdb_explorer/query_execute'

    @staticmethod
    def query_results() -> str:
        """Event when query results are available.

        Returns:
            Event type identifier
        """
        return 'plugin/vcdb_explorer/query_results'