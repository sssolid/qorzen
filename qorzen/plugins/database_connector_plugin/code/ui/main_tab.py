"""
Main tab for the Database Connector Plugin.

This module provides the main tab UI containing connection management
and query editor functionality.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QPushButton, QComboBox, QLabel, QTextEdit, QPlainTextEdit,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QFrame, QScrollArea, QGridLayout
)

from ..models import DatabaseConnection, SavedQuery, ConnectionType, QueryResult
from .connection_dialog import ConnectionDialog
from .query_dialog import QueryDialog


class SQLHighlighter(QSyntaxHighlighter):
    """SQL syntax highlighter for the query editor."""

    def __init__(self, document: QTextDocument) -> None:
        """Initialize the highlighter."""
        super().__init__(document)

        # Define highlighting rules
        self._highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.GlobalColor.blue)
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = [
            "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL",
            "ON", "GROUP", "BY", "HAVING", "ORDER", "LIMIT", "OFFSET", "UNION",
            "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TABLE",
            "INDEX", "VIEW", "PROCEDURE", "FUNCTION", "TRIGGER", "DATABASE",
            "SCHEMA", "AND", "OR", "NOT", "IN", "EXISTS", "BETWEEN", "LIKE",
            "IS", "NULL", "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX",
            "CASE", "WHEN", "THEN", "ELSE", "END", "IF", "WHILE", "FOR"
        ]

        for keyword in keywords:
            pattern = f"\\b{keyword}\\b"
            self._highlighting_rules.append((pattern, keyword_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(Qt.GlobalColor.darkMagenta)
        function_pattern = r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()"
        self._highlighting_rules.append((function_pattern, function_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(Qt.GlobalColor.darkGreen)
        string_pattern = r"'[^']*'"
        self._highlighting_rules.append((string_pattern, string_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(Qt.GlobalColor.darkCyan)
        number_pattern = r"\b\d+\.?\d*\b"
        self._highlighting_rules.append((number_pattern, number_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(Qt.GlobalColor.gray)
        comment_format.setFontItalic(True)
        comment_pattern = r"--[^\n]*"
        self._highlighting_rules.append((comment_pattern, comment_format))

    def highlightBlock(self, text: str) -> None:
        """Highlight a block of text."""
        import re

        for pattern, format in self._highlighting_rules:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)


class MainTab(QWidget):
    """
    Main tab containing connection management and query editor.

    Provides functionality for:
    - Managing database connections
    - Query editor with syntax highlighting
    - Query execution and management
    - Database schema browsing
    """

    # Signals
    query_executed = Signal(object)  # QueryResult
    operation_started = Signal(str)  # message
    operation_finished = Signal()
    status_changed = Signal(str)  # message

    def __init__(
            self,
            plugin: Any,
            logger: logging.Logger,
            concurrency_manager: Any,
            event_bus_manager: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the main tab.

        Args:
            plugin: The plugin instance
            logger: Logger instance
            concurrency_manager: Concurrency manager
            event_bus_manager: Event bus manager
            parent: Parent widget
        """
        super().__init__(parent)

        self._plugin = plugin
        self._logger = logger
        self._concurrency_manager = concurrency_manager
        self._event_bus_manager = event_bus_manager

        # UI components
        self._connection_combo: Optional[QComboBox] = None
        self._query_editor: Optional[QPlainTextEdit] = None
        self._schema_tree: Optional[QTreeWidget] = None
        self._saved_queries_list: Optional[QListWidget] = None
        self._execute_button: Optional[QPushButton] = None
        self._format_button: Optional[QPushButton] = None
        self._save_query_button: Optional[QPushButton] = None

        # State
        self._current_connection_id: Optional[str] = None
        self._current_query_result: Optional[QueryResult] = None

        self._setup_ui()
        self._setup_connections()

        # Auto-refresh timer
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(lambda: asyncio.create_task(self._refresh_schema()))
        self._refresh_timer.start(30000)  # Refresh every 30 seconds

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Connection toolbar
        self._create_connection_toolbar()
        layout.addWidget(self._connection_toolbar)

        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (schema and saved queries)
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        # Right panel (query editor)
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter proportions (30% left, 70% right)
        main_splitter.setSizes([300, 700])

        layout.addWidget(main_splitter)

    def _create_connection_toolbar(self) -> None:
        """Create the connection toolbar."""
        self._connection_toolbar = QFrame()
        self._connection_toolbar.setFrameStyle(QFrame.Shape.StyledPanel)

        toolbar_layout = QHBoxLayout(self._connection_toolbar)

        # Connection selection
        toolbar_layout.addWidget(QLabel("Connection:"))

        self._connection_combo = QComboBox()
        self._connection_combo.setMinimumWidth(200)
        self._connection_combo.currentTextChanged.connect(self._on_connection_changed)
        toolbar_layout.addWidget(self._connection_combo)

        # Connection buttons
        new_conn_button = QPushButton("New")
        new_conn_button.clicked.connect(self._create_connection)
        toolbar_layout.addWidget(new_conn_button)

        edit_conn_button = QPushButton("Edit")
        edit_conn_button.clicked.connect(self._edit_connection)
        toolbar_layout.addWidget(edit_conn_button)

        test_conn_button = QPushButton("Test")
        test_conn_button.clicked.connect(self._test_connection)
        toolbar_layout.addWidget(test_conn_button)

        delete_conn_button = QPushButton("Delete")
        delete_conn_button.clicked.connect(self._delete_connection)
        toolbar_layout.addWidget(delete_conn_button)

        toolbar_layout.addStretch()

        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: asyncio.create_task(self.refresh()))
        toolbar_layout.addWidget(refresh_button)

    def _create_left_panel(self) -> QWidget:
        """Create the left panel with schema and saved queries."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Tab widget for schema and queries
        tab_widget = QTabWidget()

        # Schema tab
        schema_tab = QWidget()
        schema_layout = QVBoxLayout(schema_tab)

        schema_layout.addWidget(QLabel("Database Schema:"))

        self._schema_tree = QTreeWidget()
        self._schema_tree.setHeaderLabel("Tables and Columns")
        self._schema_tree.itemDoubleClicked.connect(self._on_schema_item_double_clicked)
        schema_layout.addWidget(self._schema_tree)

        tab_widget.addTab(schema_tab, "Schema")

        # Saved queries tab
        queries_tab = QWidget()
        queries_layout = QVBoxLayout(queries_tab)

        queries_layout.addWidget(QLabel("Saved Queries:"))

        self._saved_queries_list = QListWidget()
        self._saved_queries_list.itemDoubleClicked.connect(self._on_saved_query_double_clicked)
        self._saved_queries_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._saved_queries_list.customContextMenuRequested.connect(self._show_query_context_menu)
        queries_layout.addWidget(self._saved_queries_list)

        # Query management buttons
        query_buttons_layout = QHBoxLayout()

        new_query_button = QPushButton("New")
        new_query_button.clicked.connect(self._create_query)
        query_buttons_layout.addWidget(new_query_button)

        edit_query_button = QPushButton("Edit")
        edit_query_button.clicked.connect(self._edit_query)
        query_buttons_layout.addWidget(edit_query_button)

        delete_query_button = QPushButton("Delete")
        delete_query_button.clicked.connect(self._delete_query)
        query_buttons_layout.addWidget(delete_query_button)

        queries_layout.addLayout(query_buttons_layout)

        tab_widget.addTab(queries_tab, "Queries")

        layout.addWidget(tab_widget)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with query editor."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Query editor group
        editor_group = QGroupBox("Query Editor")
        editor_layout = QVBoxLayout(editor_group)

        # Query editor toolbar
        editor_toolbar = QHBoxLayout()

        self._execute_button = QPushButton("Execute")
        self._execute_button.clicked.connect(self._execute_query)
        self._execute_button.setEnabled(False)
        editor_toolbar.addWidget(self._execute_button)

        self._format_button = QPushButton("Format")
        self._format_button.clicked.connect(self._format_query)
        editor_toolbar.addWidget(self._format_button)

        self._save_query_button = QPushButton("Save Query")
        self._save_query_button.clicked.connect(self._save_current_query)
        editor_toolbar.addWidget(self._save_query_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self._clear_query)
        editor_toolbar.addWidget(clear_button)

        editor_toolbar.addStretch()

        editor_layout.addLayout(editor_toolbar)

        # Query editor text area
        self._query_editor = QPlainTextEdit()
        self._query_editor.setFont(QFont("Consolas", 11))
        self._query_editor.setPlaceholderText("Enter your SQL query here...")
        self._query_editor.textChanged.connect(self._on_query_text_changed)

        # Apply syntax highlighting
        self._highlighter = SQLHighlighter(self._query_editor.document())

        editor_layout.addWidget(self._query_editor)

        layout.addWidget(editor_group)

        return panel

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Load initial data
        asyncio.create_task(self.refresh())

    async def refresh(self) -> None:
        """Refresh all data in the tab."""
        try:
            self.operation_started.emit("Refreshing connections and queries...")

            # Refresh connections
            await self._refresh_connections()

            # Refresh saved queries
            await self._refresh_saved_queries()

            # Refresh schema if connection is selected
            if self._current_connection_id:
                await self._refresh_schema()

            self.operation_finished.emit()
            self.status_changed.emit("Refreshed successfully")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to refresh main tab: {e}")
            self._show_error("Refresh Error", f"Failed to refresh data: {e}")

    async def _refresh_connections(self) -> None:
        """Refresh the connections list."""
        try:
            connections = await self._plugin.get_connections()

            current_text = self._connection_combo.currentText()
            self._connection_combo.clear()
            self._connection_combo.addItem("-- Select Connection --", None)

            for connection in connections:
                self._connection_combo.addItem(connection.name, connection.id)

            # Restore selection if possible
            if current_text:
                index = self._connection_combo.findText(current_text)
                if index >= 0:
                    self._connection_combo.setCurrentIndex(index)

        except Exception as e:
            self._logger.error(f"Failed to refresh connections: {e}")

    async def _refresh_saved_queries(self) -> None:
        """Refresh the saved queries list."""
        try:
            queries = await self._plugin.get_saved_queries(self._current_connection_id)

            self._saved_queries_list.clear()

            for query in queries:
                item = QListWidgetItem(query.name)
                item.setData(Qt.ItemDataRole.UserRole, query.id)
                item.setToolTip(f"Description: {query.description or 'No description'}\n"
                                f"Created: {query.created_at.strftime('%Y-%m-%d %H:%M')}")
                self._saved_queries_list.addItem(item)

        except Exception as e:
            self._logger.error(f"Failed to refresh saved queries: {e}")

    async def _refresh_schema(self) -> None:
        """Refresh the database schema tree."""
        try:
            if not self._current_connection_id:
                self._schema_tree.clear()
                return

            tables = await self._plugin.get_tables(self._current_connection_id)

            self._schema_tree.clear()

            for table in tables:
                table_item = QTreeWidgetItem([table["name"]])
                table_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "table", "name": table["name"]})

                # Add columns as children
                for column in table.get("columns", []):
                    column_text = f"{column['name']} ({column.get('type_name', 'UNKNOWN')})"
                    if not column.get('nullable', True):
                        column_text += " NOT NULL"

                    column_item = QTreeWidgetItem([column_text])
                    column_item.setData(0, Qt.ItemDataRole.UserRole, {
                        "type": "column",
                        "name": column['name'],
                        "table": table["name"]
                    })
                    table_item.addChild(column_item)

                self._schema_tree.addTopLevelItem(table_item)

            self._schema_tree.expandAll()

        except Exception as e:
            self._logger.error(f"Failed to refresh schema: {e}")

    def _on_connection_changed(self, connection_name: str) -> None:
        """Handle connection selection change."""
        try:
            connection_id = self._connection_combo.currentData()
            self._current_connection_id = connection_id

            # Enable/disable execute button
            self._execute_button.setEnabled(connection_id is not None)

            # Refresh dependent data
            asyncio.create_task(self._refresh_saved_queries())
            asyncio.create_task(self._refresh_schema())

            self.status_changed.emit(f"Connected to: {connection_name}" if connection_id else "No connection selected")

        except Exception as e:
            self._logger.error(f"Error changing connection: {e}")

    def _on_schema_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on schema item."""
        try:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data:
                return

            if data["type"] == "table":
                # Insert table name
                table_name = data["name"]
                self._query_editor.insertPlainText(table_name)
            elif data["type"] == "column":
                # Insert column name
                column_name = data["name"]
                self._query_editor.insertPlainText(column_name)

        except Exception as e:
            self._logger.error(f"Error handling schema item click: {e}")

    def _on_saved_query_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on saved query."""
        try:
            query_id = item.data(Qt.ItemDataRole.UserRole)
            if not query_id:
                return

            # Load query into editor
            asyncio.create_task(self._load_query(query_id))

        except Exception as e:
            self._logger.error(f"Error loading saved query: {e}")

    async def _load_query(self, query_id: str) -> None:
        """Load a saved query into the editor."""
        try:
            queries = await self._plugin.get_saved_queries()
            query = next((q for q in queries if q.id == query_id), None)

            if query:
                self._query_editor.setPlainText(query.query_text)
                self.status_changed.emit(f"Loaded query: {query.name}")
            else:
                self._show_error("Query Not Found", f"Query with ID {query_id} not found")

        except Exception as e:
            self._logger.error(f"Failed to load query: {e}")
            self._show_error("Load Error", f"Failed to load query: {e}")

    def _on_query_text_changed(self) -> None:
        """Handle query text changes."""
        # Enable/disable buttons based on text content
        has_text = bool(self._query_editor.toPlainText().strip())
        has_connection = self._current_connection_id is not None

        self._execute_button.setEnabled(has_text and has_connection)
        self._format_button.setEnabled(has_text)
        self._save_query_button.setEnabled(has_text)

    def _execute_query(self) -> None:
        """Execute the current query."""
        if not self._current_connection_id:
            self._show_error("No Connection", "Please select a database connection first")
            return

        query_text = self._query_editor.toPlainText().strip()
        if not query_text:
            self._show_error("No Query", "Please enter a query to execute")
            return

        asyncio.create_task(self._execute_query_async(query_text))

    async def _execute_query_async(self, query_text: str) -> None:
        """Execute query asynchronously."""
        try:
            self.operation_started.emit("Executing query...")

            # Get settings for query execution
            settings = await self._plugin.get_settings()
            limit = settings.query_limit if settings.auto_limit_queries else None

            # Execute query
            result = await self._plugin.execute_query(
                connection_id=self._current_connection_id,
                query=query_text,
                limit=limit
            )

            self._current_query_result = result

            self.operation_finished.emit()

            # Emit signal to show results in results tab
            self.query_executed.emit(result)

            self.status_changed.emit(
                f"Query executed: {result.row_count} rows in {result.execution_time_ms}ms"
            )

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Query execution failed: {e}")
            self._show_error("Query Error", f"Failed to execute query: {e}")

    def _format_query(self) -> None:
        """Format the current query."""
        try:
            query_text = self._query_editor.toPlainText()
            if not query_text.strip():
                return

            # Use query service to format SQL
            if hasattr(self._plugin, '_query_service') and self._plugin._query_service:
                formatted_query = self._plugin._query_service.format_sql(query_text)
                self._query_editor.setPlainText(formatted_query)
                self.status_changed.emit("Query formatted")
            else:
                self._show_warning("Format Unavailable", "SQL formatting service not available")

        except Exception as e:
            self._logger.error(f"Failed to format query: {e}")
            self._show_error("Format Error", f"Failed to format query: {e}")

    def _save_current_query(self) -> None:
        """Save the current query."""
        query_text = self._query_editor.toPlainText().strip()
        if not query_text:
            self._show_error("No Query", "Please enter a query to save")
            return

        if not self._current_connection_id:
            self._show_error("No Connection", "Please select a connection first")
            return

        # Show query dialog for saving
        dialog = QueryDialog(self)
        dialog.set_query_text(query_text)
        dialog.set_connection_id(self._current_connection_id)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            query = dialog.get_query()
            asyncio.create_task(self._save_query_async(query))

    async def _save_query_async(self, query: SavedQuery) -> None:
        """Save query asynchronously."""
        try:
            await self._plugin.save_query(query)
            await self._refresh_saved_queries()
            self.status_changed.emit(f"Query saved: {query.name}")

        except Exception as e:
            self._logger.error(f"Failed to save query: {e}")
            self._show_error("Save Error", f"Failed to save query: {e}")

    def _clear_query(self) -> None:
        """Clear the query editor."""
        self._query_editor.clear()
        self.status_changed.emit("Query cleared")

    def _create_connection(self) -> None:
        """Create a new database connection."""
        dialog = ConnectionDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            connection = dialog.get_connection()
            asyncio.create_task(self._create_connection_async(connection))

    async def _create_connection_async(self, connection: DatabaseConnection) -> None:
        """Create connection asynchronously."""
        try:
            self.operation_started.emit("Creating connection...")

            await self._plugin.create_connection(connection)
            await self._refresh_connections()

            # Select the new connection
            index = self._connection_combo.findText(connection.name)
            if index >= 0:
                self._connection_combo.setCurrentIndex(index)

            self.operation_finished.emit()
            self.status_changed.emit(f"Connection created: {connection.name}")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to create connection: {e}")
            self._show_error("Connection Error", f"Failed to create connection: {e}")

    def _edit_connection(self) -> None:
        """Edit the current connection."""
        if not self._current_connection_id:
            self._show_error("No Connection", "Please select a connection to edit")
            return

        asyncio.create_task(self._edit_connection_async())

    async def _edit_connection_async(self) -> None:
        """Edit connection asynchronously."""
        try:
            # Get current connection
            connections = await self._plugin.get_connections()
            connection = next((c for c in connections if c.id == self._current_connection_id), None)

            if not connection:
                self._show_error("Connection Not Found", "Selected connection not found")
                return

            dialog = ConnectionDialog(self)
            dialog.set_connection(connection)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_connection = dialog.get_connection()

                self.operation_started.emit("Updating connection...")

                await self._plugin.update_connection(updated_connection)
                await self._refresh_connections()

                self.operation_finished.emit()
                self.status_changed.emit(f"Connection updated: {updated_connection.name}")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to edit connection: {e}")
            self._show_error("Edit Error", f"Failed to edit connection: {e}")

    def _test_connection(self) -> None:
        """Test the current connection."""
        if not self._current_connection_id:
            self._show_error("No Connection", "Please select a connection to test")
            return

        asyncio.create_task(self._test_connection_async())

    async def _test_connection_async(self) -> None:
        """Test connection asynchronously."""
        try:
            self.operation_started.emit("Testing connection...")

            success, error = await self._plugin.test_connection(self._current_connection_id)

            self.operation_finished.emit()

            if success:
                self._show_info("Connection Test", "Connection test successful!")
                self.status_changed.emit("Connection test successful")
            else:
                self._show_error("Connection Test Failed", f"Connection test failed: {error}")

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Connection test failed: {e}")
            self._show_error("Test Error", f"Connection test failed: {e}")

    def _delete_connection(self) -> None:
        """Delete the current connection."""
        if not self._current_connection_id:
            self._show_error("No Connection", "Please select a connection to delete")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this connection?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            asyncio.create_task(self._delete_connection_async())

    async def _delete_connection_async(self) -> None:
        """Delete connection asynchronously."""
        try:
            self.operation_started.emit("Deleting connection...")

            success = await self._plugin.delete_connection(self._current_connection_id)

            if success:
                await self._refresh_connections()
                self._current_connection_id = None
                self.status_changed.emit("Connection deleted")
            else:
                self._show_error("Delete Error", "Failed to delete connection")

            self.operation_finished.emit()

        except Exception as e:
            self.operation_finished.emit()
            self._logger.error(f"Failed to delete connection: {e}")
            self._show_error("Delete Error", f"Failed to delete connection: {e}")

    def _create_query(self) -> None:
        """Create a new saved query."""
        if not self._current_connection_id:
            self._show_error("No Connection", "Please select a connection first")
            return

        dialog = QueryDialog(self)
        dialog.set_connection_id(self._current_connection_id)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            query = dialog.get_query()
            asyncio.create_task(self._save_query_async(query))

    def _edit_query(self) -> None:
        """Edit the selected saved query."""
        current_item = self._saved_queries_list.currentItem()
        if not current_item:
            self._show_error("No Query Selected", "Please select a query to edit")
            return

        query_id = current_item.data(Qt.ItemDataRole.UserRole)
        asyncio.create_task(self._edit_query_async(query_id))

    async def _edit_query_async(self, query_id: str) -> None:
        """Edit query asynchronously."""
        try:
            # Get current query
            queries = await self._plugin.get_saved_queries()
            query = next((q for q in queries if q.id == query_id), None)

            if not query:
                self._show_error("Query Not Found", "Selected query not found")
                return

            dialog = QueryDialog(self)
            dialog.set_query(query)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_query = dialog.get_query()

                await self._plugin.save_query(updated_query)
                await self._refresh_saved_queries()

                self.status_changed.emit(f"Query updated: {updated_query.name}")

        except Exception as e:
            self._logger.error(f"Failed to edit query: {e}")
            self._show_error("Edit Error", f"Failed to edit query: {e}")

    def _delete_query(self) -> None:
        """Delete the selected saved query."""
        current_item = self._saved_queries_list.currentItem()
        if not current_item:
            self._show_error("No Query Selected", "Please select a query to delete")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the query '{current_item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            query_id = current_item.data(Qt.ItemDataRole.UserRole)
            asyncio.create_task(self._delete_query_async(query_id))

    async def _delete_query_async(self, query_id: str) -> None:
        """Delete query asynchronously."""
        try:
            success = await self._plugin.delete_query(query_id)

            if success:
                await self._refresh_saved_queries()
                self.status_changed.emit("Query deleted")
            else:
                self._show_error("Delete Error", "Failed to delete query")

        except Exception as e:
            self._logger.error(f"Failed to delete query: {e}")
            self._show_error("Delete Error", f"Failed to delete query: {e}")

    def _show_query_context_menu(self, position) -> None:
        """Show context menu for saved queries."""
        item = self._saved_queries_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        load_action = menu.addAction("Load Query")
        load_action.triggered.connect(lambda: self._on_saved_query_double_clicked(item))

        edit_action = menu.addAction("Edit Query")
        edit_action.triggered.connect(self._edit_query)

        delete_action = menu.addAction("Delete Query")
        delete_action.triggered.connect(self._delete_query)

        menu.exec(self._saved_queries_list.mapToGlobal(position))

    def _show_error(self, title: str, message: str) -> None:
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)

    def _show_info(self, title: str, message: str) -> None:
        """Show information message dialog."""
        QMessageBox.information(self, title, message)

    def _show_warning(self, title: str, message: str) -> None:
        """Show warning message dialog."""
        QMessageBox.warning(self, title, message)

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self._refresh_timer:
                self._refresh_timer.stop()
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")

    # Public API
    def get_current_connection_id(self) -> Optional[str]:
        """Get the current connection ID."""
        return self._current_connection_id

    def set_query_text(self, text: str) -> None:
        """Set the query editor text."""
        if self._query_editor:
            self._query_editor.setPlainText(text)

    def get_query_text(self) -> str:
        """Get the query editor text."""
        return self._query_editor.toPlainText() if self._query_editor else ""