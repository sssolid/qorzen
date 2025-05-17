from __future__ import annotations

"""
SQL query editor with syntax highlighting for the AS400 Connector Plugin.

This module provides a customized text editor for SQL queries with AS400-specific
syntax highlighting and auto-completion features.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import Qt, QRegularExpression, QSize
from PySide6.QtGui import (
    QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter,
    QTextCursor, QKeyEvent, QTextDocument
)
from PySide6.QtWidgets import (
    QTextEdit, QWidget, QCompleter, QAbstractItemView
)

from qorzen.plugins.as400_connector_plugin.code.utils import (
    get_sql_keywords, get_syntax_highlighting_colors, detect_query_parameters
)


class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for SQL in the query editor.

    Highlights SQL keywords, strings, numbers, functions, comments, and
    query parameters.
    """

    def __init__(self, document: QTextDocument) -> None:
        """
        Initialize the syntax highlighter.

        Args:
            document: The text document to highlight
        """
        super().__init__(document)

        # Load colors from utils
        self.colors = get_syntax_highlighting_colors()

        # Create highlighting rules
        self.highlighting_rules: List[Tuple[QRegularExpression, QTextCharFormat]] = []

        # Keywords format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors.get("keyword", QColor(0, 0, 255)))
        keyword_format.setFontWeight(QFont.Bold)

        # Add SQL keywords
        keywords = get_sql_keywords()
        keyword_patterns = [f"\\b{keyword}\\b" for keyword in keywords]
        for pattern in keyword_patterns:
            regexp = QRegularExpression(pattern)
            regexp.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((regexp, keyword_format))

        # Single-line string format (single quotes)
        single_quote_format = QTextCharFormat()
        single_quote_format.setForeground(self.colors.get("string", QColor(0, 128, 0)))
        self.highlighting_rules.append((
            QRegularExpression("'[^']*'"),
            single_quote_format
        ))

        # Numbers format
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors.get("number", QColor(128, 0, 128)))
        self.highlighting_rules.append((
            QRegularExpression("\\b\\d+(\\.\\d+)?\\b"),
            number_format
        ))

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(self.colors.get("function", QColor(255, 128, 0)))
        function_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((
            QRegularExpression("\\b[A-Za-z0-9_]+(?=\\()"),
            function_format
        ))

        # Comment format (--comment)
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors.get("comment", QColor(128, 128, 128)))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((
            QRegularExpression("--[^\n]*"),
            comment_format
        ))

        # Parameter format (:param)
        parameter_format = QTextCharFormat()
        parameter_format.setForeground(self.colors.get("parameter", QColor(0, 128, 128)))
        parameter_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((
            QRegularExpression(":[A-Za-z0-9_]+"),
            parameter_format
        ))

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of text according to the rules.

        Args:
            text: The text to highlight
        """
        # Apply normal rules
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        # Multiline comment handling (/* ... */)
        # Note: This is a simplified implementation and may not handle nested comments correctly
        self.setCurrentBlockState(0)  # Default - not inside comment

        comment_start = QRegularExpression("/\\*")
        comment_end = QRegularExpression("\\*/")

        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors.get("comment", QColor(128, 128, 128)))
        comment_format.setFontItalic(True)

        start_index = 0
        if self.previousBlockState() != 1:  # If not already in a comment
            start_index = comment_start.match(text).capturedStart()

        while start_index >= 0:
            # Find the end of the comment
            end_match = comment_end.match(text, start_index)
            end_index = end_match.capturedStart()

            # Determine comment length
            if end_index == -1:  # Comment continues
                self.setCurrentBlockState(1)  # Inside comment state
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + end_match.capturedLength()

            # Apply format
            self.setFormat(start_index, comment_length, comment_format)

            # Look for next comment
            start_index = comment_start.match(text, start_index + comment_length).capturedStart()


class SQLQueryEditor(QTextEdit):
    """
    Custom text editor for SQL queries with syntax highlighting.

    Features include:
    - SQL syntax highlighting
    - Auto-indentation
    - Parameter highlighting
    - Auto-completion for SQL keywords
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the SQL query editor.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Configure editor properties
        self.setFont(QFont("Courier New", 10))
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.NoWrap)

        # Add syntax highlighter
        self._highlighter = SQLSyntaxHighlighter(self.document())

        # Configure auto-completion
        self._setup_auto_completion()

        # Current line highlighting
        self._highlight_current_line()
        self.cursorPositionChanged.connect(self._highlight_current_line)

    def _setup_auto_completion(self) -> None:
        """Set up keyword auto-completion."""
        # Create completer
        self._completer = QCompleter(get_sql_keywords(), self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setMaxVisibleItems(10)

        # Connect completer signals
        self._completer.activated.connect(self._insert_completion)

    def _insert_completion(self, completion: str) -> None:
        """
        Insert the selected completion at the cursor position.

        Args:
            completion: The completion text to insert
        """
        # Get text cursor
        tc = self.textCursor()

        # Delete the partial word
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(self._completer.completionPrefix()))
        tc.insertText(completion)

        # Move cursor to end of inserted word
        self.setTextCursor(tc)

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
        Handle key press events for special editor behavior.

        Args:
            event: The key event
        """
        # Handle completer
        if self._completer and self._completer.popup() and self._completer.popup().isVisible():
            if event.key() in (
                    Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape,
                    Qt.Key_Tab, Qt.Key_Backtab
            ):
                event.ignore()
                return

        # Auto-indent after newline
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Get current line text
            cursor = self.textCursor()
            cursor.select(QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()

            # Calculate indentation
            indentation = ""
            for char in current_line:
                if char in (" ", "\t"):
                    indentation += char
                else:
                    break

            # Check for increased indentation triggers
            if any(current_line.strip().upper().endswith(keyword) for keyword in (
                    "BEGIN", "THEN", "ELSE", "DO", "CASE", "SELECT", "FROM", "WHERE", "HAVING", "ORDER BY", "GROUP BY"
            )):
                indentation += "    "

            # Call original implementation
            super().keyPressEvent(event)

            # Insert indentation
            if indentation:
                self.insertPlainText(indentation)
            return

        # Auto-completion
        if event.key() == Qt.Key_Tab:
            # Get current word
            cursor = self.textCursor()
            cursor.select(QTextCursor.WordUnderCursor)
            current_word = cursor.selectedText()

            if current_word and len(current_word) >= 2:
                # Show completions
                self._completer.setCompletionPrefix(current_word)

                if self._completer.completionCount() > 0:
                    popup = self._completer.popup()
                    popup.setCurrentIndex(self._completer.completionModel().index(0, 0))

                    # Calculate popup position
                    cursor_rect = self.cursorRect()
                    cursor_rect.setWidth(
                        self._completer.popup().sizeHintForColumn(0) +
                        self._completer.popup().verticalScrollBar().sizeHint().width()
                    )
                    self._completer.complete(cursor_rect)
                    return

        # Auto-closing parens, quotes, etc.
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

        # Check whether to show completions
        if (event.key() == Qt.Key_Period or (
                event.key() >= Qt.Key_A and event.key() <= Qt.Key_Z and
                len(self.toPlainText()) > 0
        )):
            # Only show completions for words
            cursor = self.textCursor()
            cursor.select(QTextCursor.WordUnderCursor)
            current_word = cursor.selectedText()

            if not current_word or len(current_word) < 2:
                return

            # Show completions
            self._completer.setCompletionPrefix(current_word)

            if self._completer.completionCount() > 0:
                popup = self._completer.popup()
                popup.setCurrentIndex(self._completer.completionModel().index(0, 0))

                # Calculate popup position
                cursor_rect = self.cursorRect()
                cursor_rect.setWidth(
                    self._completer.popup().sizeHintForColumn(0) +
                    self._completer.popup().verticalScrollBar().sizeHint().width()
                )
                self._completer.complete(cursor_rect)

    def get_detected_parameters(self) -> List[str]:
        """
        Get parameters detected in the current query.

        Returns:
            List of parameter names
        """
        return detect_query_parameters(self.toPlainText())

    def format_sql(self) -> None:
        """Format the SQL text with proper indentation and case."""
        try:
            # Try to import sqlparse
            import sqlparse
        except ImportError:
            return

        # Get current text
        sql_text = self.toPlainText()
        if not sql_text.strip():
            return

        # Format the SQL
        formatted_sql = sqlparse.format(
            sql_text,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower',
            indent_width=4
        )

        # Set the formatted text
        self.setPlainText(formatted_sql)

    def set_dark_mode(self, enabled: bool) -> None:
        """
        Toggle dark mode for the editor.

        Args:
            enabled: Whether dark mode should be enabled
        """
        if enabled:
            # Configure dark mode colors
            self.setStyleSheet("""
                QTextEdit {
                    background-color: #2b2b2b;
                    color: #e6e6e6;
                }
            """)

            # Update highlighter colors
            self._highlighter.colors.update({
                "keyword": QColor(86, 156, 214),  # Blue
                "function": QColor(220, 220, 170),  # Yellow
                "string": QColor(206, 145, 120),  # Red-orange
                "number": QColor(181, 206, 168),  # Light green
                "operator": QColor(180, 180, 180),  # Light gray
                "comment": QColor(106, 153, 85),  # Green
                "parameter": QColor(156, 220, 254),  # Light blue
                "identifier": QColor(220, 220, 220),  # Off-white
                "background": QColor(43, 43, 43),  # Dark gray
                "current_line": QColor(44, 50, 60)  # Slightly lighter gray
            })
        else:
            # Reset to light mode
            self.setStyleSheet("")

            # Reset highlighter colors
            self._highlighter.colors = get_syntax_highlighting_colors()

        # Force rehighlight
        self._highlighter.rehighlight()