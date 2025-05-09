from __future__ import annotations
'\nSQL query editor with syntax highlighting for the AS400 Connector Plugin.\n\nThis module provides a customized text editor for SQL queries with AS400-specific\nsyntax highlighting and auto-completion features.\n'
import re
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import Qt, QRegularExpression, QSize
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter, QTextCursor, QKeyEvent, QTextDocument
from PySide6.QtWidgets import QTextEdit, QWidget, QCompleter, QAbstractItemView
from qorzen.plugins.as400_connector_plugin.code.utils import get_sql_keywords, get_syntax_highlighting_colors, detect_query_parameters
class SQLSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self.colors = get_syntax_highlighting_colors()
        self.highlighting_rules: List[Tuple[QRegularExpression, QTextCharFormat]] = []
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors.get('keyword', QColor(0, 0, 255)))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = get_sql_keywords()
        keyword_patterns = [f'\\b{keyword}\\b' for keyword in keywords]
        for pattern in keyword_patterns:
            regexp = QRegularExpression(pattern)
            regexp.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((regexp, keyword_format))
        single_quote_format = QTextCharFormat()
        single_quote_format.setForeground(self.colors.get('string', QColor(0, 128, 0)))
        self.highlighting_rules.append((QRegularExpression("'[^']*'"), single_quote_format))
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors.get('number', QColor(128, 0, 128)))
        self.highlighting_rules.append((QRegularExpression('\\b\\d+(\\.\\d+)?\\b'), number_format))
        function_format = QTextCharFormat()
        function_format.setForeground(self.colors.get('function', QColor(255, 128, 0)))
        function_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression('\\b[A-Za-z0-9_]+(?=\\()'), function_format))
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors.get('comment', QColor(128, 128, 128)))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression('--[^\n]*'), comment_format))
        parameter_format = QTextCharFormat()
        parameter_format.setForeground(self.colors.get('parameter', QColor(0, 128, 128)))
        parameter_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(':[A-Za-z0-9_]+'), parameter_format))
    def highlightBlock(self, text: str) -> None:
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        self.setCurrentBlockState(0)
        comment_start = QRegularExpression('/\\*')
        comment_end = QRegularExpression('\\*/')
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors.get('comment', QColor(128, 128, 128)))
        comment_format.setFontItalic(True)
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = comment_start.match(text).capturedStart()
        while start_index >= 0:
            end_match = comment_end.match(text, start_index)
            end_index = end_match.capturedStart()
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + end_match.capturedLength()
            self.setFormat(start_index, comment_length, comment_format)
            start_index = comment_start.match(text, start_index + comment_length).capturedStart()
class SQLQueryEditor(QTextEdit):
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self.setFont(QFont('Courier New', 10))
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self._highlighter = SQLSyntaxHighlighter(self.document())
        self._setup_auto_completion()
        self._highlight_current_line()
        self.cursorPositionChanged.connect(self._highlight_current_line)
    def _setup_auto_completion(self) -> None:
        self._completer = QCompleter(get_sql_keywords(), self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setMaxVisibleItems(10)
        self._completer.activated.connect(self._insert_completion)
    def _insert_completion(self, completion: str) -> None:
        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(self._completer.completionPrefix()))
        tc.insertText(completion)
        self.setTextCursor(tc)
    def _highlight_current_line(self) -> None:
        selection = QTextEdit.ExtraSelection()
        line_color = self._highlighter.colors.get('current_line', QColor(232, 242, 254))
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._completer and self._completer.popup() and self._completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            cursor = self.textCursor()
            cursor.select(QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()
            indentation = ''
            for char in current_line:
                if char in (' ', '\t'):
                    indentation += char
                else:
                    break
            if any((current_line.strip().upper().endswith(keyword) for keyword in ('BEGIN', 'THEN', 'ELSE', 'DO', 'CASE', 'SELECT', 'FROM', 'WHERE', 'HAVING', 'ORDER BY', 'GROUP BY'))):
                indentation += '    '
            super().keyPressEvent(event)
            if indentation:
                self.insertPlainText(indentation)
            return
        if event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            cursor.select(QTextCursor.WordUnderCursor)
            current_word = cursor.selectedText()
            if current_word and len(current_word) >= 2:
                self._completer.setCompletionPrefix(current_word)
                if self._completer.completionCount() > 0:
                    popup = self._completer.popup()
                    popup.setCurrentIndex(self._completer.completionModel().index(0, 0))
                    cursor_rect = self.cursorRect()
                    cursor_rect.setWidth(self._completer.popup().sizeHintForColumn(0) + self._completer.popup().verticalScrollBar().sizeHint().width())
                    self._completer.complete(cursor_rect)
                    return
        if event.key() == Qt.Key_ParenLeft:
            super().keyPressEvent(event)
            self.insertPlainText(')')
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
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Period or (event.key() >= Qt.Key_A and event.key() <= Qt.Key_Z and (len(self.toPlainText()) > 0)):
            cursor = self.textCursor()
            cursor.select(QTextCursor.WordUnderCursor)
            current_word = cursor.selectedText()
            if not current_word or len(current_word) < 2:
                return
            self._completer.setCompletionPrefix(current_word)
            if self._completer.completionCount() > 0:
                popup = self._completer.popup()
                popup.setCurrentIndex(self._completer.completionModel().index(0, 0))
                cursor_rect = self.cursorRect()
                cursor_rect.setWidth(self._completer.popup().sizeHintForColumn(0) + self._completer.popup().verticalScrollBar().sizeHint().width())
                self._completer.complete(cursor_rect)
    def get_detected_parameters(self) -> List[str]:
        return detect_query_parameters(self.toPlainText())
    def format_sql(self) -> None:
        try:
            import sqlparse
        except ImportError:
            return
        sql_text = self.toPlainText()
        if not sql_text.strip():
            return
        formatted_sql = sqlparse.format(sql_text, reindent=True, keyword_case='upper', identifier_case='lower', indent_width=4)
        self.setPlainText(formatted_sql)
    def set_dark_mode(self, enabled: bool) -> None:
        if enabled:
            self.setStyleSheet('\n                QTextEdit {\n                    background-color: #2b2b2b;\n                    color: #e6e6e6;\n                }\n            ')
            self._highlighter.colors.update({'keyword': QColor(86, 156, 214), 'function': QColor(220, 220, 170), 'string': QColor(206, 145, 120), 'number': QColor(181, 206, 168), 'operator': QColor(180, 180, 180), 'comment': QColor(106, 153, 85), 'parameter': QColor(156, 220, 254), 'identifier': QColor(220, 220, 220), 'background': QColor(43, 43, 43), 'current_line': QColor(44, 50, 60)})
        else:
            self.setStyleSheet('')
            self._highlighter.colors = get_syntax_highlighting_colors()
        self._highlighter.rehighlight()