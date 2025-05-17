#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
SQL query editor for the Database Connector Plugin.

This module provides a specialized editor for writing and executing SQL queries,
with syntax highlighting, parameter support, and field mapping integration.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, QRegularExpression, Signal, Slot, QSize
from PySide6.QtGui import (
    QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter,
    QTextCursor, QKeyEvent, QTextDocument
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTextEdit, QListWidget, QListWidgetItem, QToolBar, QSpinBox,
    QFormLayout, QLineEdit, QInputDialog, QMessageBox, QMenu, QSplitter,
    QGroupBox, QTabWidget, QScrollArea, QFileDialog
)

from ..models import SavedQuery, FieldMapping


class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for SQL queries."""

    def __init__(self, document: QTextDocument) -> None:
        """
        Initialize the syntax highlighter.

        Args:
            document: Document to highlight
        """
        super().__init__(document)

        self.colors = self._get_syntax_highlighting_colors()
        self.highlighting_rules: List[Tuple[QRegularExpression, QTextCharFormat]] = []

        # SQL keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors.get("keyword", QColor(0, 0, 255)))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = self._get_sql_keywords()
        keyword_patterns = [f"\\b{keyword}\\b" for keyword in keywords]

        for pattern in keyword_patterns:
            regexp = QRegularExpression(pattern)
            regexp.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((regexp, keyword_format))

        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors.get("string", QColor(0, 128, 0)))
        self.highlighting_rules.append((QRegularExpression("'[^']*'"), string_format))

        # Numeric literals
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors.get("number", QColor(128, 0, 128)))
        self.highlighting_rules.append(
            (QRegularExpression("\\b\\d+(\\.\\d+)?\\b"), number_format)
        )

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(self.colors.get("function", QColor(255, 128, 0)))
        function_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append(
            (QRegularExpression("\\b[A-Za-z0-9_]+(?=\\()"), function_format)
        )

        # Single-line comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors.get("comment", QColor(128, 128, 128)))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(
            (QRegularExpression("--[^\n]*"), comment_format)
        )

        # Parameters (e.g., :param_name)
        parameter_format = QTextCharFormat()
        parameter_format.setForeground(self.colors.get("parameter", QColor(0, 128, 128)))
        parameter_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(":[A-Za-z0-9_]+"), parameter_format)
        )

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of text.

        Args:
            text: Text to highlight
        """
        # Apply highlighting rules
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        # Handle multi-line comments
        self.setCurrentBlockState(0)

        comment_start = QRegularExpression("/\\*")
        comment_end = QRegularExpression("\\*/")
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors.get("comment", QColor(128, 128, 128)))
        comment_format.setFontItalic(True)

        start_index = 0
        if self.previousBlockState() != 1:
            start_match = comment_start.match(text)
            start_index = start_match.capturedStart()

        while start_index >= 0:
            end_match = comment_end.match(text, start_index)
            end_index = end_match.capturedStart()

            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + end_match.capturedLength()

            self.setFormat(start_index, comment_length, comment_format)

            start_match = comment_start.match(text, start_index + comment_length)
            start_index = start_match.capturedStart()

    def _get_syntax_highlighting_colors(self) -> Dict[str, QColor]:
        """
        Get syntax highlighting colors.

        Returns:
            Dictionary of color names to QColor objects
        """
        return {
            "keyword": QColor(0, 128, 255),
            "function": QColor(255, 128, 0),
            "string": QColor(0, 170, 0),
            "number": QColor(170, 0, 170),
            "operator": QColor(170, 0, 0),
            "comment": QColor(128, 128, 128),
            "parameter": QColor(0, 170, 170),
            "identifier": QColor(0, 0, 0),
            "background": QColor(255, 255, 255),
            "current_line": QColor(232, 242, 254)
        }

    def _get_sql_keywords(self) -> List[str]:
        """
        Get list of SQL keywords for syntax highlighting.

        Returns:
            List of SQL keywords
        """
        return [
            "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "BETWEEN", "LIKE",
            "ORDER", "BY", "GROUP", "HAVING", "JOIN", "INNER", "LEFT", "RIGHT", "OUTER",
            "ON", "AS", "UNION", "ALL", "DISTINCT", "CASE", "WHEN", "THEN", "ELSE", "END",
            "IS", "NULL", "CREATE", "TABLE", "VIEW", "INDEX", "UNIQUE", "PRIMARY", "KEY",
            "FOREIGN", "REFERENCES", "CONSTRAINT", "DEFAULT", "ALTER", "ADD", "DROP",
            "TRUNCATE", "DELETE", "UPDATE", "SET", "INSERT", "INTO", "VALUES", "EXISTS",
            "GRANT", "REVOKE", "COMMIT", "ROLLBACK", "TRANSACTION", "WITH", "RECURSIVE",
            "LIMIT", "OFFSET", "FETCH", "FIRST", "NEXT", "ROWS", "ONLY",
            # Data types
            "INT", "INTEGER", "SMALLINT", "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL",
            "CHAR", "VARCHAR", "TEXT", "DATE", "TIME", "TIMESTAMP", "DATETIME", "BOOLEAN",
            "BINARY", "VARBINARY", "BLOB", "CLOB",
            # Functions
            "COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "IFNULL", "CAST", "UPPER",
            "LOWER", "TRIM", "LTRIM", "RTRIM", "SUBSTRING", "LENGTH", "CONCAT", "REPLACE",
            "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP", "EXTRACT", "TO_CHAR",
            "TO_DATE", "DATEADD", "DATEDIFF"
        ]


class SQLEditor(QTextEdit):
    """SQL editor with syntax highlighting and auto-completion."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the SQL editor.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Set the font to a monospace font
        self.setFont(QFont("Courier New", 10))
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.NoWrap)

        # Set up syntax highlighting
        self._highlighter = SQLSyntaxHighlighter(self.document())

        # Highlight current line
        self._highlight_current_line()
        self.cursorPositionChanged.connect(self._highlight_current_line)

    def _highlight_current_line(self) -> None:
        """Highlight the current line."""
        selection = QTextEdit.ExtraSelection()
        line_color = self._highlighter.colors.get("current_line", QColor(232, 242, 254))
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        self.setExtraSelections([selection])

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handle key press events.

        Args:
            event: Key press event
        """
        # Auto-indentation
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            cursor = self.textCursor()
            cursor.select(QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()

            # Get the indentation of the current line
            indentation = ""
            for char in current_line:
                if char in (" ", "\t"):
                    indentation += char
                else:
                    break

            # Add extra indentation after certain keywords
            if any(
                    current_line.strip().upper().endswith(keyword)
                    for keyword in (
                            "BEGIN", "THEN", "ELSE", "DO", "CASE", "SELECT",
                            "FROM", "WHERE", "HAVING", "ORDER BY", "GROUP BY"
                    )
            ):
                indentation += "    "

            # Insert the newline and indentation
            super().keyPressEvent(event)
            if indentation:
                self.insertPlainText(indentation)
            return

        # Auto-completion for parentheses, quotes, etc.
        if event.key() == Qt.Key_ParenLeft:
            super().keyPressEvent(event)
            self.insertPlainText(")")
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
            return

        if event.key() == Qt.Key_QuoteDbl:
            super().keyPressEvent(event)
            self.insertPlainText('"')
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
            return

        if event.key() == Qt.Key_Apostrophe:
            super().keyPressEvent(event)
            self.insertPlainText("'")
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
            return

        # Default handling
        super().keyPressEvent(event)

    def format_sql(self) -> None:
        """Format the SQL query with proper indentation and capitalization."""
        try:
            import sqlparse
        except ImportError:
            # If sqlparse is not available, just ignore
            return

        sql_text = self.toPlainText()
        if not sql_text.strip():
            return

        formatted_sql = sqlparse.format(
            sql_text,
            reindent=True,
            keyword_case="upper",
            identifier_case="lower",
            indent_width=4
        )

        self.setPlainText(formatted_sql)


class QueryEditorWidget(QWidget):
    """Widget for editing and managing SQL queries."""

    # Signals
    executeQueryRequested = Signal()
    saveQueryRequested = Signal()

    def __init__(
            self,
            plugin: Any,
            logger: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the query editor widget.

        Args:
            plugin: Plugin instance
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)

        self._plugin = plugin
        self._logger = logger

        self._current_connection_id: Optional[str] = None
        self._current_query_id: Optional[str] = None
        self._current_mapping_id: Optional[str] = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)

        # Top toolbar
        toolbar = QToolBar("Query Tools")
        toolbar.setIconSize(QSize(16, 16))

        # Query management actions
        new_action = toolbar.addAction("New Query")
        new_action.triggered.connect(self._on_new_query)

        save_action = toolbar.addAction("Save Query")
        save_action.triggered.connect(self._on_save_query)

        toolbar.addSeparator()

        # Format and execution actions
        format_action = toolbar.addAction("Format SQL")
        format_action.triggered.connect(self._on_format_sql)

        toolbar.addSeparator()

        # Limit control
        limit_label = QLabel("Limit results:")
        toolbar.addWidget(limit_label)

        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(0, 100000)
        self._limit_spin.setValue(1000)
        self._limit_spin.setSpecialValueText("No limit")
        self._limit_spin.setFixedWidth(80)
        toolbar.addWidget(self._limit_spin)

        # Field mapping
        toolbar.addSeparator()

        mapping_label = QLabel("Apply field mapping:")
        toolbar.addWidget(mapping_label)

        self._mapping_combo = QComboBox()
        self._mapping_combo.addItem("None", None)
        self._mapping_combo.setMinimumWidth(150)
        toolbar.addWidget(self._mapping_combo)

        main_layout.addWidget(toolbar)

        # Main editor area - split view
        splitter = QSplitter(Qt.Horizontal)

        # Saved queries panel (left)
        queries_widget = QWidget()
        queries_layout = QVBoxLayout(queries_widget)
        queries_layout.setContentsMargins(0, 0, 0, 0)

        # List of saved queries
        queries_label = QLabel("Saved Queries")
        queries_label.setFont(QFont("Arial", 10, QFont.Bold))
        queries_layout.addWidget(queries_label)

        self._queries_list = QListWidget()
        self._queries_list.itemDoubleClicked.connect(self._on_query_double_clicked)
        queries_layout.addWidget(self._queries_list)

        # Query list toolbar
        query_list_toolbar = QToolBar()

        load_action = query_list_toolbar.addAction("Load")
        load_action.triggered.connect(self._on_load_query)

        delete_action = query_list_toolbar.addAction("Delete")
        delete_action.triggered.connect(self._on_delete_query)

        query_list_toolbar.addSeparator()

        import_action = query_list_toolbar.addAction("Import")
        import_action.triggered.connect(self._on_import_queries)

        export_action = query_list_toolbar.addAction("Export")
        export_action.triggered.connect(self._on_export_queries)

        queries_layout.addWidget(query_list_toolbar)

        # Add the queries panel to the splitter
        splitter.addWidget(queries_widget)

        # Editor panel (right)
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        # SQL editor
        editor_label = QLabel("SQL Query")
        editor_label.setFont(QFont("Arial", 10, QFont.Bold))
        editor_layout.addWidget(editor_label)

        self._editor = SQLEditor()
        editor_layout.addWidget(self._editor)

        # Parameters panel
        params_label = QLabel("Query Parameters")
        params_label.setFont(QFont("Arial", 10, QFont.Bold))
        editor_layout.addWidget(params_label)

        self._params_widget = QWidget()
        self._params_layout = QFormLayout(self._params_widget)

        # Add a scroll area for parameters
        params_scroll = QScrollArea()
        params_scroll.setWidgetResizable(True)
        params_scroll.setWidget(self._params_widget)
        params_scroll.setMaximumHeight(150)

        editor_layout.addWidget(params_scroll)

        # Add the editor panel to the splitter
        splitter.addWidget(editor_widget)

        # Set the size ratio between the panels (1:3)
        splitter.setSizes([150, 450])

        main_layout.addWidget(splitter)

        # Execute button
        execute_layout = QHBoxLayout()
        execute_layout.addStretch()

        self._execute_button = QPushButton("Execute Query")
        self._execute_button.setMinimumWidth(150)
        self._execute_button.clicked.connect(self._on_execute_query)
        execute_layout.addWidget(self._execute_button)

        execute_layout.addStretch()
        main_layout.addLayout(execute_layout)

        # Initial state
        self._execute_button.setEnabled(False)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        # Text change in the editor triggers parameter detection
        self._editor.textChanged.connect(self._on_query_text_changed)

    async def refresh(self) -> None:
        """Refresh the query editor content."""
        # Reload saved queries
        await self.reload_queries()

        # Reload field mappings if a connection is selected
        if self._current_connection_id:
            await self._load_field_mappings()

    async def reload_queries(self) -> None:
        """Reload the list of saved queries."""
        try:
            if not self._current_connection_id:
                # No connection, clear the list
                self._queries_list.clear()
                return

            # Get saved queries for this connection
            saved_queries = await self._plugin.get_saved_queries(self._current_connection_id)

            # Clear and repopulate the list
            self._queries_list.clear()

            # Sort by name
            sorted_queries = sorted(saved_queries.values(), key=lambda q: q.name.lower())

            # Add favorites first
            for query in [q for q in sorted_queries if q.is_favorite]:
                item = QListWidgetItem(f"⭐ {query.name}")
                item.setData(Qt.UserRole, query.id)
                self._queries_list.addItem(item)

            # Then add non-favorites
            for query in [q for q in sorted_queries if not q.is_favorite]:
                item = QListWidgetItem(query.name)
                item.setData(Qt.UserRole, query.id)
                self._queries_list.addItem(item)

        except Exception as e:
            self._logger.error(f"Failed to load saved queries: {str(e)}")

    async def _load_field_mappings(self) -> None:
        """Load field mappings for the current connection."""
        try:
            if not self._current_connection_id:
                # No connection, clear the combo
                self._mapping_combo.clear()
                self._mapping_combo.addItem("None", None)
                return

            # Get field mappings for this connection
            field_mappings = await self._plugin.get_field_mappings(self._current_connection_id)

            # Save current selection if possible
            current_id = self._mapping_combo.currentData()

            # Clear and repopulate the combo
            self._mapping_combo.clear()
            self._mapping_combo.addItem("None", None)

            # Sort by table name and description
            sorted_mappings = sorted(
                field_mappings.values(),
                key=lambda m: f"{m.table_name}_{m.description or ''}"
            )

            for mapping in sorted_mappings:
                display_text = mapping.table_name
                if mapping.description:
                    display_text += f" ({mapping.description})"

                self._mapping_combo.addItem(display_text, mapping.id)

            # Restore selection if it still exists
            if current_id:
                for i in range(self._mapping_combo.count()):
                    if self._mapping_combo.itemData(i) == current_id:
                        self._mapping_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f"Failed to load field mappings: {str(e)}")

    def set_connection_status(
            self,
            connection_id: str,
            connected: bool
    ) -> None:
        """
        Update the connection status.

        Args:
            connection_id: Connection ID
            connected: Whether the connection is active
        """
        if connected:
            self._current_connection_id = connection_id
            self._execute_button.setEnabled(True)

            # Reload queries for this connection
            asyncio.create_task(self.reload_queries())

            # Load field mappings for this connection
            asyncio.create_task(self._load_field_mappings())
        else:
            if self._current_connection_id == connection_id:
                self._current_connection_id = None
                self._execute_button.setEnabled(False)

    def get_query_text(self) -> str:
        """
        Get the current query text.

        Returns:
            Query text
        """
        return self._editor.toPlainText()

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get the query parameters.

        Returns:
            Dictionary of parameter name/value pairs
        """
        params = {}

        for i in range(self._params_layout.rowCount()):
            label_item = self._params_layout.itemAt(i * 2)
            field_item = self._params_layout.itemAt(i * 2 + 1)

            if not label_item or not field_item:
                continue

            label = label_item.widget()
            field = field_item.widget()

            if not isinstance(label, QLabel) or not isinstance(field, QLineEdit):
                continue

            param_name = label.text().rstrip(":")
            param_value = field.text()

            # Convert values to appropriate types
            if param_value.lower() == "null":
                params[param_name] = None
            elif param_value.isdigit():
                params[param_name] = int(param_value)
            elif param_value.replace(".", "", 1).isdigit():
                params[param_name] = float(param_value)
            elif param_value.lower() in ("true", "false"):
                params[param_name] = param_value.lower() == "true"
            else:
                params[param_name] = param_value

        return params

    def get_limit(self) -> Optional[int]:
        """
        Get the result limit.

        Returns:
            Limit or None if no limit
        """
        if self._limit_spin.value() == 0:
            return None
        return self._limit_spin.value()

    def get_mapping_id(self) -> Optional[str]:
        """
        Get the selected field mapping ID.

        Returns:
            Field mapping ID or None if no mapping selected
        """
        return self._mapping_combo.currentData()

    def get_current_query_id(self) -> Optional[str]:
        """
        Get the ID of the currently displayed query.

        Returns:
            Query ID or None if no query is displayed
        """
        return self._current_query_id

    def get_current_query_name(self) -> str:
        """
        Get the name of the currently displayed query.

        Returns:
            Query name or empty string if no query is displayed
        """
        # Check if a query is selected in the list
        selected_items = self._queries_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            query_id = item.data(Qt.UserRole)

            # Check if this is the current query
            if query_id == self._current_query_id:
                name = item.text()
                # Remove star prefix if it's a favorite
                if name.startswith("⭐ "):
                    return name[2:]
                return name

        return ""

    def _on_query_text_changed(self) -> None:
        """Handle query text changes to detect parameters."""
        query_text = self._editor.toPlainText()
        params = self._detect_query_parameters(query_text)
        self._update_parameter_controls(params)

    def _detect_query_parameters(self, query: str) -> List[str]:
        """
        Detect parameter placeholders in a query.

        Args:
            query: SQL query

        Returns:
            List of parameter names
        """
        param_names = re.findall(r":(\w+)", query)
        # Remove duplicates while preserving order
        return list(dict.fromkeys(param_names))

    def _update_parameter_controls(self, param_names: List[str]) -> None:
        """
        Update the parameter input controls.

        Args:
            param_names: List of parameter names
        """
        # Clear existing parameters
        while self._params_layout.count() > 0:
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not param_names:
            self._params_widget.setVisible(False)
            return

        self._params_widget.setVisible(True)

        for param_name in param_names:
            label = QLabel(f"{param_name}:")
            input_field = QLineEdit()
            input_field.setObjectName(f"param_{param_name}")

            self._params_layout.addRow(label, input_field)

    def _on_new_query(self) -> None:
        """Create a new query."""
        # Clear the editor
        self._editor.clear()
        self._current_query_id = None

        # Deselect any selected query
        self._queries_list.clearSelection()

    def _on_save_query(self) -> None:
        """Save the current query."""
        self.saveQueryRequested.emit()

    def _on_format_sql(self) -> None:
        """Format the SQL query."""
        self._editor.format_sql()

    def _on_execute_query(self) -> None:
        """Execute the current query."""
        self.executeQueryRequested.emit()

    def _on_query_double_clicked(self, item: QListWidgetItem) -> None:
        """
        Handle double-click on a saved query.

        Args:
            item: Clicked list item
        """
        query_id = item.data(Qt.UserRole)
        if not query_id:
            return

        asyncio.create_task(self._load_query_by_id(query_id))

    def _on_load_query(self) -> None:
        """Load the selected query."""
        selected_items = self._queries_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Query Selected",
                "Please select a query to load."
            )
            return

        query_id = selected_items[0].data(Qt.UserRole)
        if not query_id:
            return

        asyncio.create_task(self._load_query_by_id(query_id))

    async def _load_query_by_id(self, query_id: str) -> None:
        """
        Load a query by ID.

        Args:
            query_id: Query ID
        """
        try:
            # Get the query
            query = await self._plugin.get_saved_query(query_id)
            if not query:
                return

            # Set the query ID
            self._current_query_id = query_id

            # Set the text
            self._editor.setText(query.query_text)

            # Set parameters if any
            if query.parameters:
                self._set_parameter_values(query.parameters)

            # Set field mapping if any
            if query.field_mapping_id:
                for i in range(self._mapping_combo.count()):
                    if self._mapping_combo.itemData(i) == query.field_mapping_id:
                        self._mapping_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f"Failed to load query: {str(e)}")

    def _set_parameter_values(self, params: Dict[str, Any]) -> None:
        """
        Set parameter values in the UI controls.

        Args:
            params: Dictionary of parameter name/value pairs
        """
        for i in range(self._params_layout.rowCount()):
            label_item = self._params_layout.itemAt(i * 2)
            field_item = self._params_layout.itemAt(i * 2 + 1)

            if not label_item or not field_item:
                continue

            label = label_item.widget()
            field = field_item.widget()

            if not isinstance(label, QLabel) or not isinstance(field, QLineEdit):
                continue

            param_name = label.text().rstrip(":")

            if param_name in params:
                value = params[param_name]

                if value is None:
                    field.setText("NULL")
                else:
                    field.setText(str(value))

    def _on_delete_query(self) -> None:
        """Delete the selected query."""
        selected_items = self._queries_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Query Selected",
                "Please select a query to delete."
            )
            return

        item = selected_items[0]
        query_id = item.data(Qt.UserRole)

        if not query_id:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this query?\n\n{item.text()}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Delete the query
        asyncio.create_task(self._delete_query(query_id))

    async def _delete_query(self, query_id: str) -> None:
        """
        Delete a query.

        Args:
            query_id: Query ID
        """
        try:
            # Delete the query
            success = await self._plugin.delete_query(query_id)

            if success:
                # Clear the editor if this was the current query
                if query_id == self._current_query_id:
                    self._editor.clear()
                    self._current_query_id = None

                # Reload the query list
                await self.reload_queries()

        except Exception as e:
            self._logger.error(f"Failed to delete query: {str(e)}")

            # Show error message
            QMessageBox.critical(
                self,
                "Delete Error",
                f"Failed to delete query: {str(e)}"
            )

    def _on_import_queries(self) -> None:
        """Import queries from a file."""
        if not self._current_connection_id:
            QMessageBox.warning(
                self,
                "No Connection Selected",
                "Please connect to a database before importing queries."
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Queries",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        asyncio.create_task(self._import_queries_from_file(file_path))

    async def _import_queries_from_file(self, file_path: str) -> None:
        """
        Import queries from a file.

        Args:
            file_path: Path to the file
        """
        try:
            import json
            import uuid

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("Invalid file format: Expected a list of queries")

            imported_count = 0

            for item in data:
                try:
                    # Skip invalid items
                    if not isinstance(item, dict):
                        continue

                    # Create a new ID for the imported query
                    item["id"] = str(uuid.uuid4())

                    # Set the connection ID to the current connection
                    item["connection_id"] = self._current_connection_id

                    # Convert date strings to datetime objects
                    if "created_at" in item and isinstance(item["created_at"], str):
                        item["created_at"] = datetime.datetime.fromisoformat(item["created_at"])

                    if "updated_at" in item and isinstance(item["updated_at"], str):
                        item["updated_at"] = datetime.datetime.fromisoformat(item["updated_at"])

                    # Create a SavedQuery object
                    query = SavedQuery(**item)

                    # Save the query
                    await self._plugin.save_query(query)
                    imported_count += 1

                except Exception as e:
                    self._logger.warning(f"Failed to import query: {str(e)}")

            # Reload the query list
            await self.reload_queries()

            QMessageBox.information(
                self,
                "Import Successful",
                f"Imported {imported_count} queries."
            )

        except Exception as e:
            self._logger.error(f"Failed to import queries: {str(e)}")

            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import queries: {str(e)}"
            )

    def _on_export_queries(self) -> None:
        """Export queries to a file."""
        if not self._current_connection_id:
            QMessageBox.warning(
                self,
                "No Connection Selected",
                "Please connect to a database before exporting queries."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Queries",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        # Add .json extension if missing
        if not file_path.endswith(".json"):
            file_path += ".json"

        asyncio.create_task(self._export_queries_to_file(file_path))

    async def _export_queries_to_file(self, file_path: str) -> None:
        """
        Export queries to a file.

        Args:
            file_path: Path to the file
        """
        try:
            import json
            import datetime

            # Get all queries for the current connection
            queries = await self._plugin.get_saved_queries(self._current_connection_id)

            if not queries:
                QMessageBox.warning(
                    self,
                    "No Queries",
                    "There are no queries to export."
                )
                return

            # Convert to serializable format
            query_list = []

            for query in queries.values():
                query_dict = query.dict()

                # Convert datetime objects to ISO format strings
                if "created_at" in query_dict and isinstance(query_dict["created_at"], datetime.datetime):
                    query_dict["created_at"] = query_dict["created_at"].isoformat()

                if "updated_at" in query_dict and isinstance(query_dict["updated_at"], datetime.datetime):
                    query_dict["updated_at"] = query_dict["updated_at"].isoformat()

                query_list.append(query_dict)

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(query_list, f, indent=2)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(query_list)} queries to {file_path}"
            )

        except Exception as e:
            self._logger.error(f"Failed to export queries: {str(e)}")

            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export queries: {str(e)}"
            )