from __future__ import annotations
from qorzen.core.event_model import EventType
class VCdbEventType:
    @staticmethod
    def filter_changed() -> str:
        return 'plugin/vcdb_explorer/filter_changed'
    @staticmethod
    def filters_refreshed() -> str:
        return 'plugin/vcdb_explorer/filters_refreshed'
    @staticmethod
    def query_execute() -> str:
        return 'plugin/vcdb_explorer/query_execute'
    @staticmethod
    def query_results() -> str:
        return 'plugin/vcdb_explorer/query_results'