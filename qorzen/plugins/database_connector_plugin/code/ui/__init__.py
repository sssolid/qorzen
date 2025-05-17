# processed_project/qorzen_stripped/plugins/database_connector_plugin/code/ui/__init__.py
from __future__ import annotations
'''
UI components for the Database Connector Plugin.

This module provides the user interface components for the Database Connector Plugin,
including the main tab, connection dialogs, query editor, field mapping, validation,
and history views.
'''

from .main_tab import DatabaseConnectorTab
from .connection_dialog import ConnectionDialog, ConnectionManagerDialog
from .query_editor import QueryEditorWidget, SQLEditor, SQLSyntaxHighlighter
from .results_view import ResultsView
from .field_mapping import FieldMappingWidget
from .mapping_dialog import FieldMappingDialog
from .validation import ValidationWidget
from .history import HistoryWidget

__all__ = [
    'DatabaseConnectorTab',
    'ConnectionDialog',
    'ConnectionManagerDialog',
    'QueryEditorWidget',
    'SQLEditor',
    'SQLSyntaxHighlighter',
    'ResultsView',
    'FieldMappingWidget',
    'FieldMappingDialog',
    'ValidationWidget',
    'HistoryWidget',
]