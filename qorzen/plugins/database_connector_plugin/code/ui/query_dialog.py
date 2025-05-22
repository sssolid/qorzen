"""
Query dialog for the Database Connector Plugin.

This module provides a dialog for creating and editing saved queries
with metadata and tagging support.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QTextEdit, QPlainTextEdit, QPushButton, QDialogButtonBox,
    QLabel, QListWidget, QListWidgetItem, QMessageBox, QSplitter, QWidget
)

from ..models import SavedQuery


class QueryDialog(QDialog):
    """
    Dialog for creating and editing saved queries.

    Provides interface for:
    - Query metadata (name, description)
    - SQL query text with basic formatting
    - Tag management
    - Query validation
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the query dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._query: Optional[SavedQuery] = None
        self._connection_id: Optional[str] = None

        # UI components
        self._name_edit: Optional[QLineEdit] = None
        self._description_edit: Optional[QTextEdit] = None
        self._query_edit: Optional[QPlainTextEdit] = None
        self._tags_edit: Optional[QLineEdit] = None
        self._tags_list: Optional[QListWidget] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Query Editor")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section: Metadata
        metadata_widget = self._create_metadata_section()
        splitter.addWidget(metadata_widget)

        # Bottom section: Query text
        query_widget = self._create_query_section()
        splitter.addWidget(query_widget)

        # Set splitter proportions (30% metadata, 70% query)
        splitter.setSizes([200, 400])

        layout.addWidget(splitter)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def _create_metadata_section(self) -> QGroupBox:
        """Create the metadata section."""
        group = QGroupBox("Query Information")
        layout = QVBoxLayout(group)

        # Form layout for basic info
        form_layout = QFormLayout()

        # Query name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter query name")
        form_layout.addRow("Name:", self._name_edit)

        # Description
        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(80)
        self._description_edit.setPlaceholderText("Enter query description (optional)")
        form_layout.addRow("Description:", self._description_edit)

        layout.addLayout(form_layout)

        # Tags section
        tags_layout = QVBoxLayout()
        tags_layout.addWidget(QLabel("Tags:"))

        # Tag input and buttons
        tag_input_layout = QHBoxLayout()

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("Enter tag and press Add")
        self._tags_edit.returnPressed.connect(self._add_tag)
        tag_input_layout.addWidget(self._tags_edit)

        add_tag_button = QPushButton("Add")
        add_tag_button.clicked.connect(self._add_tag)
        tag_input_layout.addWidget(add_tag_button)

        tags_layout.addLayout(tag_input_layout)

        # Tags list
        self._tags_list = QListWidget()
        self._tags_list.setMaximumHeight(100)
        self._tags_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tags_list.customContextMenuRequested.connect(self._show_tag_context_menu)
        tags_layout.addWidget(self._tags_list)

        layout.addLayout(tags_layout)

        return group

    def _create_query_section(self) -> QGroupBox:
        """Create the query text section."""
        group = QGroupBox("SQL Query")
        layout = QVBoxLayout(group)

        # Query editor toolbar
        toolbar_layout = QHBoxLayout()

        format_button = QPushButton("Format")
        format_button.clicked.connect(self._format_query)
        toolbar_layout.addWidget(format_button)

        validate_button = QPushButton("Validate")
        validate_button.clicked.connect(self._validate_query)
        toolbar_layout.addWidget(validate_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self._clear_query)
        toolbar_layout.addWidget(clear_button)

        toolbar_layout.addStretch()

        # Character count label
        self._char_count_label = QLabel("0 characters")
        toolbar_layout.addWidget(self._char_count_label)

        layout.addLayout(toolbar_layout)

        # Query text editor
        self._query_edit = QPlainTextEdit()
        self._query_edit.setFont(QFont("Consolas", 11))
        self._query_edit.setPlaceholderText("Enter your SQL query here...")
        self._query_edit.textChanged.connect(self._on_query_text_changed)

        layout.addWidget(self._query_edit)

        return group

    def _add_tag(self) -> None:
        """Add a tag to the list."""
        tag_text = self._tags_edit.text().strip()
        if not tag_text:
            return

        # Check if tag already exists
        for i in range(self._tags_list.count()):
            if self._tags_list.item(i).text() == tag_text:
                self._tags_edit.clear()
                return

        # Add new tag
        item = QListWidgetItem(tag_text)
        self._tags_list.addItem(item)
        self._tags_edit.clear()

    def _remove_tag(self) -> None:
        """Remove selected tag."""
        current_item = self._tags_list.currentItem()
        if current_item:
            row = self._tags_list.row(current_item)
            self._tags_list.takeItem(row)

    def _show_tag_context_menu(self, position) -> None:
        """Show context menu for tags."""
        from PySide6.QtWidgets import QMenu

        item = self._tags_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        remove_action = menu.addAction("Remove Tag")
        remove_action.triggered.connect(self._remove_tag)

        menu.exec(self._tags_list.mapToGlobal(position))

    def _format_query(self) -> None:
        """Format the SQL query."""
        query_text = self._query_edit.toPlainText()
        if not query_text.strip():
            return

        try:
            # Basic SQL formatting
            formatted_query = self._basic_sql_format(query_text)
            self._query_edit.setPlainText(formatted_query)
        except Exception as e:
            QMessageBox.warning(self, "Format Error", f"Failed to format query: {e}")

    def _basic_sql_format(self, query: str) -> str:
        """Apply basic SQL formatting."""
        # This is a simplified formatter - in a real implementation,
        # you might want to use a proper SQL parser/formatter
        import re

        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())

        # Add line breaks before major keywords
        keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT']
        for keyword in keywords:
            pattern = rf'\b{keyword}\b'
            query = re.sub(pattern, f'\n{keyword}', query, flags=re.IGNORECASE)

        # Format JOIN clauses
        join_keywords = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']
        for join in join_keywords:
            pattern = rf'\b{join}\b'
            query = re.sub(pattern, f'\n{join}', query, flags=re.IGNORECASE)

        # Clean up and add proper indentation
        lines = [line.strip() for line in query.split('\n') if line.strip()]
        formatted_lines = []

        for line in lines:
            if line.upper().startswith(('SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT')):
                formatted_lines.append(line)
            elif line.upper().startswith(('JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN')):
                formatted_lines.append('    ' + line)
            elif line.upper().startswith('ON'):
                formatted_lines.append('        ' + line)
            else:
                formatted_lines.append('    ' + line)

        return '\n'.join(formatted_lines)

    def _validate_query(self) -> None:
        """Validate the SQL query."""
        query_text = self._query_edit.toPlainText().strip()
        if not query_text:
            QMessageBox.warning(self, "Validation", "Please enter a query to validate")
            return

        # Basic validation
        errors = []

        # Check for empty query
        if not query_text:
            errors.append("Query cannot be empty")

        # Check for balanced parentheses
        open_parens = query_text.count('(')
        close_parens = query_text.count(')')
        if open_parens != close_parens:
            errors.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")

        # Check for balanced quotes
        single_quotes = query_text.count("'")
        if single_quotes % 2 != 0:
            errors.append("Unbalanced single quotes")

        double_quotes = query_text.count('"')
        if double_quotes % 2 != 0:
            errors.append("Unbalanced double quotes")

        # Check for potential SQL injection patterns (basic)
        dangerous_patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM\s+\w+\s*;',
            r';\s*UPDATE\s+\w+\s+SET\s+.*\s*;'
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, query_text, re.IGNORECASE):
                errors.append(f"Potentially dangerous pattern detected: {pattern}")

        # Show results
        if errors:
            error_text = "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(self, "Validation Errors", f"The following issues were found:\n\n{error_text}")
        else:
            QMessageBox.information(self, "Validation", "Query appears to be valid!")

    def _clear_query(self) -> None:
        """Clear the query text."""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear the query text?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._query_edit.clear()

    def _on_query_text_changed(self) -> None:
        """Handle query text changes."""
        text = self._query_edit.toPlainText()
        char_count = len(text)
        self._char_count_label.setText(f"{char_count:,} characters")

    def set_query(self, query: SavedQuery) -> None:
        """
        Set the query to edit.

        Args:
            query: The query to edit
        """
        self._query = query
        self._connection_id = query.connection_id

        # Populate fields
        self._name_edit.setText(query.name)
        self._description_edit.setPlainText(query.description or "")
        self._query_edit.setPlainText(query.query_text)

        # Add tags
        self._tags_list.clear()
        for tag in query.tags:
            item = QListWidgetItem(tag)
            self._tags_list.addItem(item)

    def set_query_text(self, query_text: str) -> None:
        """
        Set the query text.

        Args:
            query_text: The SQL query text
        """
        self._query_edit.setPlainText(query_text)

    def set_connection_id(self, connection_id: str) -> None:
        """
        Set the connection ID.

        Args:
            connection_id: The connection ID
        """
        self._connection_id = connection_id

    def get_query(self) -> SavedQuery:
        """
        Get the query from the dialog.

        Returns:
            The configured query

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        name = self._name_edit.text().strip()
        if not name:
            raise ValueError("Query name is required")

        query_text = self._query_edit.toPlainText().strip()
        if not query_text:
            raise ValueError("Query text is required")

        if not self._connection_id:
            raise ValueError("Connection ID is required")

        # Get tags
        tags = []
        for i in range(self._tags_list.count()):
            tags.append(self._tags_list.item(i).text())

        # Create or update query object
        if self._query:
            # Update existing query
            self._query.name = name
            self._query.description = self._description_edit.toPlainText().strip() or None
            self._query.query_text = query_text
            self._query.tags = tags
            self._query.updated_at = datetime.now()
            return self._query
        else:
            # Create new query
            return SavedQuery(
                name=name,
                description=self._description_edit.toPlainText().strip() or None,
                connection_id=self._connection_id,
                query_text=query_text,
                tags=tags
            )

    def accept(self) -> None:
        """Accept the dialog after validation."""
        try:
            # Validate query
            query = self.get_query()
            super().accept()

        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")