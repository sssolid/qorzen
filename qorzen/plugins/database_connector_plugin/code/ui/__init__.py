"""
Database Connector Plugin User Interface Components.

This module contains all the UI components for the database connector plugin
including main widget, tabs, dialogs, and other interface elements.
"""

from __future__ import annotations

from .main_widget import DatabasePluginWidget
from .main_tab import MainTab
from .results_tab import ResultsTab
from .field_mapping_tab import FieldMappingTab
from .validation_tab import ValidationTab
from .history_tab import HistoryTab
from .connection_dialog import ConnectionDialog
from .query_dialog import QueryDialog

__all__ = [
    "DatabasePluginWidget",
    "MainTab",
    "ResultsTab",
    "FieldMappingTab",
    "ValidationTab",
    "HistoryTab",
    "ConnectionDialog",
    "QueryDialog"
]