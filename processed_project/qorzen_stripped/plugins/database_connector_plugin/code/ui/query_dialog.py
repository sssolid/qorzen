from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit, QTextEdit, QPlainTextEdit, QPushButton, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QMessageBox, QSplitter, QWidget
from ..models import SavedQuery
class QueryDialog(QDialog):
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._query: Optional[SavedQuery] = None
        self._connection_id: Optional[str] = None
        self._name_edit: Optional[QLineEdit] = None
        self._description_edit: Optional[QTextEdit] = None
        self._query_edit: Optional[QPlainTextEdit] = None
        self._tags_edit: Optional[QLineEdit] = None
        self._tags_list: Optional[QListWidget] = None
        self._setup_ui()
    def _setup_ui(self) -> None:
        self.setWindowTitle('Query Editor')
        self.setModal(True)
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Vertical)
        metadata_widget = self._create_metadata_section()
        splitter.addWidget(metadata_widget)
        query_widget = self._create_query_section()
        splitter.addWidget(query_widget)
        splitter.setSizes([200, 400])
        layout.addWidget(splitter)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    def _create_metadata_section(self) -> QGroupBox:
        group = QGroupBox('Query Information')
        layout = QVBoxLayout(group)
        form_layout = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText('Enter query name')
        form_layout.addRow('Name:', self._name_edit)
        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(80)
        self._description_edit.setPlaceholderText('Enter query description (optional)')
        form_layout.addRow('Description:', self._description_edit)
        layout.addLayout(form_layout)
        tags_layout = QVBoxLayout()
        tags_layout.addWidget(QLabel('Tags:'))
        tag_input_layout = QHBoxLayout()
        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText('Enter tag and press Add')
        self._tags_edit.returnPressed.connect(self._add_tag)
        tag_input_layout.addWidget(self._tags_edit)
        add_tag_button = QPushButton('Add')
        add_tag_button.clicked.connect(self._add_tag)
        tag_input_layout.addWidget(add_tag_button)
        tags_layout.addLayout(tag_input_layout)
        self._tags_list = QListWidget()
        self._tags_list.setMaximumHeight(100)
        self._tags_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tags_list.customContextMenuRequested.connect(self._show_tag_context_menu)
        tags_layout.addWidget(self._tags_list)
        layout.addLayout(tags_layout)
        return group
    def _create_query_section(self) -> QGroupBox:
        group = QGroupBox('SQL Query')
        layout = QVBoxLayout(group)
        toolbar_layout = QHBoxLayout()
        format_button = QPushButton('Format')
        format_button.clicked.connect(self._format_query)
        toolbar_layout.addWidget(format_button)
        validate_button = QPushButton('Validate')
        validate_button.clicked.connect(self._validate_query)
        toolbar_layout.addWidget(validate_button)
        clear_button = QPushButton('Clear')
        clear_button.clicked.connect(self._clear_query)
        toolbar_layout.addWidget(clear_button)
        toolbar_layout.addStretch()
        self._char_count_label = QLabel('0 characters')
        toolbar_layout.addWidget(self._char_count_label)
        layout.addLayout(toolbar_layout)
        self._query_edit = QPlainTextEdit()
        self._query_edit.setFont(QFont('Consolas', 11))
        self._query_edit.setPlaceholderText('Enter your SQL query here...')
        self._query_edit.textChanged.connect(self._on_query_text_changed)
        layout.addWidget(self._query_edit)
        return group
    def _add_tag(self) -> None:
        tag_text = self._tags_edit.text().strip()
        if not tag_text:
            return
        for i in range(self._tags_list.count()):
            if self._tags_list.item(i).text() == tag_text:
                self._tags_edit.clear()
                return
        item = QListWidgetItem(tag_text)
        self._tags_list.addItem(item)
        self._tags_edit.clear()
    def _remove_tag(self) -> None:
        current_item = self._tags_list.currentItem()
        if current_item:
            row = self._tags_list.row(current_item)
            self._tags_list.takeItem(row)
    def _show_tag_context_menu(self, position) -> None:
        from PySide6.QtWidgets import QMenu
        item = self._tags_list.itemAt(position)
        if not item:
            return
        menu = QMenu(self)
        remove_action = menu.addAction('Remove Tag')
        remove_action.triggered.connect(self._remove_tag)
        menu.exec(self._tags_list.mapToGlobal(position))
    def _format_query(self) -> None:
        query_text = self._query_edit.toPlainText()
        if not query_text.strip():
            return
        try:
            formatted_query = self._basic_sql_format(query_text)
            self._query_edit.setPlainText(formatted_query)
        except Exception as e:
            QMessageBox.warning(self, 'Format Error', f'Failed to format query: {e}')
    def _basic_sql_format(self, query: str) -> str:
        import re
        query = re.sub('\\s+', ' ', query.strip())
        keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT']
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            query = re.sub(pattern, f'\n{keyword}', query, flags=re.IGNORECASE)
        join_keywords = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']
        for join in join_keywords:
            pattern = f'\\b{join}\\b'
            query = re.sub(pattern, f'\n{join}', query, flags=re.IGNORECASE)
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
        query_text = self._query_edit.toPlainText().strip()
        if not query_text:
            QMessageBox.warning(self, 'Validation', 'Please enter a query to validate')
            return
        errors = []
        if not query_text:
            errors.append('Query cannot be empty')
        open_parens = query_text.count('(')
        close_parens = query_text.count(')')
        if open_parens != close_parens:
            errors.append(f'Unbalanced parentheses: {open_parens} open, {close_parens} close')
        single_quotes = query_text.count("'")
        if single_quotes % 2 != 0:
            errors.append('Unbalanced single quotes')
        double_quotes = query_text.count('"')
        if double_quotes % 2 != 0:
            errors.append('Unbalanced double quotes')
        dangerous_patterns = [';\\s*DROP\\s+TABLE', ';\\s*DELETE\\s+FROM\\s+\\w+\\s*;', ';\\s*UPDATE\\s+\\w+\\s+SET\\s+.*\\s*;']
        for pattern in dangerous_patterns:
            if re.search(pattern, query_text, re.IGNORECASE):
                errors.append(f'Potentially dangerous pattern detected: {pattern}')
        if errors:
            error_text = '\n'.join((f'• {error}' for error in errors))
            QMessageBox.warning(self, 'Validation Errors', f'The following issues were found:\n\n{error_text}')
        else:
            QMessageBox.information(self, 'Validation', 'Query appears to be valid!')
    def _clear_query(self) -> None:
        reply = QMessageBox.question(self, 'Confirm Clear', 'Are you sure you want to clear the query text?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._query_edit.clear()
    def _on_query_text_changed(self) -> None:
        text = self._query_edit.toPlainText()
        char_count = len(text)
        self._char_count_label.setText(f'{char_count:,} characters')
    def set_query(self, query: SavedQuery) -> None:
        self._query = query
        self._connection_id = query.connection_id
        self._name_edit.setText(query.name)
        self._description_edit.setPlainText(query.description or '')
        self._query_edit.setPlainText(query.query_text)
        self._tags_list.clear()
        for tag in query.tags:
            item = QListWidgetItem(tag)
            self._tags_list.addItem(item)
    def set_query_text(self, query_text: str) -> None:
        self._query_edit.setPlainText(query_text)
    def set_connection_id(self, connection_id: str) -> None:
        self._connection_id = connection_id
    def get_query(self) -> SavedQuery:
        name = self._name_edit.text().strip()
        if not name:
            raise ValueError('Query name is required')
        query_text = self._query_edit.toPlainText().strip()
        if not query_text:
            raise ValueError('Query text is required')
        if not self._connection_id:
            raise ValueError('Connection ID is required')
        tags = []
        for i in range(self._tags_list.count()):
            tags.append(self._tags_list.item(i).text())
        if self._query:
            self._query.name = name
            self._query.description = self._description_edit.toPlainText().strip() or None
            self._query.query_text = query_text
            self._query.tags = tags
            self._query.updated_at = datetime.now()
            return self._query
        else:
            return SavedQuery(name=name, description=self._description_edit.toPlainText().strip() or None, connection_id=self._connection_id, query_text=query_text, tags=tags)
    def accept(self) -> None:
        try:
            query = self.get_query()
            super().accept()
        except ValueError as e:
            QMessageBox.warning(self, 'Validation Error', str(e))
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')