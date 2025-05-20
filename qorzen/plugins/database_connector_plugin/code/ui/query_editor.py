from __future__ import annotations

"""
Enhanced SQL query editor for the Database Connector Plugin.

This module provides a specialized editor for writing and executing SQL queries,
with syntax highlighting, parameter support (with descriptions/tooltips), and field mapping integration.
"""
import asyncio
import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, QRegularExpression, Signal, Slot, QSize, QPoint, QTimer
from PySide6.QtGui import (
    QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter,
    QTextCursor, QKeyEvent, QTextDocument, QIcon
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTextEdit, QListWidget, QListWidgetItem, QToolBar, QSpinBox, QFormLayout,
    QLineEdit, QInputDialog, QMessageBox, QMenu, QSplitter, QGroupBox,
    QTabWidget, QScrollArea, QFileDialog, QToolTip
)

from ..models import SavedQuery, FieldMapping, ParameterDescription
from ..utils.mapping import FieldMappingManager

# Regular expression for detecting parameters in SQL queries
PARAMETER_PATTERN = r':([A-Za-z0-9_\-\.]+)(?:\{([^}]*)\})?'


class QueryParameterManager:
    """Manager for handling query parameters and descriptions."""

    def __init__(self, logger: Optional[Any] = None) -> None:
        """Initialize the parameter manager.

        Args:
            logger: Optional logger for logging parameter information
        """
        self._logger = logger or logging.getLogger(__name__)

    def detect_parameters(self, query: str) -> List[ParameterDescription]:
        """Detect parameters in a SQL query.

        Args:
            query: SQL query text

        Returns:
            List of detected parameters with descriptions
        """
        matches = re.finditer(PARAMETER_PATTERN, query)
        param_descriptions: List[ParameterDescription] = []
        seen_params = set()

        for match in matches:
            param_name = match.group(1)
            description = match.group(2) or ''

            if param_name not in seen_params:
                self._logger.debug(f'Detected parameter: {param_name} with description: {description}')
                param_descriptions.append(
                    ParameterDescription(name=param_name, description=description.strip())
                )
                seen_params.add(param_name)

        return param_descriptions


class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for SQL queries in the editor."""

    def __init__(self, document: QTextDocument) -> None:
        """Initialize the syntax highlighter.

        Args:
            document: Text document to highlight
        """
        super().__init__(document)
        self.colors = self._get_syntax_highlighting_colors()
        self.highlighting_rules: List[Tuple[QRegularExpression, QTextCharFormat]] = []

        # SQL keywords highlighting
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors.get('keyword', QColor(0, 0, 255)))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = self._get_sql_keywords()
        keyword_patterns = [f'\\b{keyword}\\b' for keyword in keywords]

        for pattern in keyword_patterns:
            regexp = QRegularExpression(pattern)
            regexp.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            self.highlighting_rules.append((regexp, keyword_format))

        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors.get('string', QColor(0, 128, 0)))
        self.highlighting_rules.append((QRegularExpression("'[^']*'"), string_format))

        # Number literals
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors.get('number', QColor(128, 0, 128)))
        self.highlighting_rules.append((QRegularExpression('\\b\\d+(\\.\\d+)?\\b'), number_format))

        # Function calls
        function_format = QTextCharFormat()
        function_format.setForeground(self.colors.get('function', QColor(255, 128, 0)))
        function_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression('\\b[A-Za-z0-9_]+(?=\\()'), function_format))

        # SQL comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors.get('comment', QColor(128, 128, 128)))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression('--[^\\n]*'), comment_format))

        # Parameter highlighting
        parameter_format = QTextCharFormat()
        parameter_format.setForeground(self.colors.get('parameter', QColor(0, 128, 128)))
        parameter_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(':[A-Za-z0-9_]+(\\{[^}]*\\})?'), parameter_format)
        )

    def highlightBlock(self, text: str) -> None:
        """Highlight a block of text.

        Args:
            text: Text to highlight
        """
        # Apply all highlighting rules
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        # Handle multi-line comments
        self.setCurrentBlockState(0)
        comment_start = QRegularExpression('/\\*')
        comment_end = QRegularExpression('\\*/')
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors.get('comment', QColor(128, 128, 128)))
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
        """Get the colors for syntax highlighting.

        Returns:
            Dictionary mapping syntax elements to colors
        """
        return {
            'keyword': QColor(0, 128, 255),
            'function': QColor(255, 128, 0),
            'string': QColor(0, 170, 0),
            'number': QColor(170, 0, 170),
            'operator': QColor(170, 0, 0),
            'comment': QColor(128, 128, 128),
            'parameter': QColor(0, 170, 170),
            'identifier': QColor(0, 0, 0),
            'background': QColor(255, 255, 255),
            'current_line': QColor(232, 242, 254)
        }

    def _get_sql_keywords(self) -> List[str]:
        """Get the list of SQL keywords to highlight.

        Returns:
            List of SQL keywords
        """
        return [
            'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE',
            'ORDER', 'BY', 'GROUP', 'HAVING', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
            'ON', 'AS', 'UNION', 'ALL', 'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
            'IS', 'NULL', 'CREATE', 'TABLE', 'VIEW', 'INDEX', 'UNIQUE', 'PRIMARY', 'KEY',
            'FOREIGN', 'REFERENCES', 'CONSTRAINT', 'DEFAULT', 'ALTER', 'ADD', 'DROP',
            'TRUNCATE', 'DELETE', 'UPDATE', 'SET', 'INSERT', 'INTO', 'VALUES', 'EXISTS',
            'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'WITH', 'RECURSIVE',
            'LIMIT', 'OFFSET', 'FETCH', 'FIRST', 'NEXT', 'ROWS', 'ONLY',

            # Data types
            'INT', 'INTEGER', 'SMALLINT', 'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL',
            'CHAR', 'VARCHAR', 'TEXT', 'DATE', 'TIME', 'TIMESTAMP', 'DATETIME', 'BOOLEAN',
            'BINARY', 'VARBINARY', 'BLOB', 'CLOB',

            # Functions
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'IFNULL', 'CAST', 'UPPER',
            'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'SUBSTRING', 'LENGTH', 'CONCAT', 'REPLACE',
            'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP', 'EXTRACT', 'TO_CHAR',
            'TO_DATE', 'DATEADD', 'DATEDIFF'
        ]


class SQLEditor(QTextEdit):
    """Enhanced text editor for SQL queries with syntax highlighting and auto-indentation."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the SQL editor.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Set up editor appearance
        self.setFont(QFont('Courier New', 10))
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.NoWrap)

        # Add SQL syntax highlighting
        self._highlighter = SQLSyntaxHighlighter(self.document())

        # Highlight current line
        self._highlight_current_line()
        self.cursorPositionChanged.connect(self._highlight_current_line)

    def _highlight_current_line(self) -> None:
        """Highlight the current line in the editor."""
        selection = QTextEdit.ExtraSelection()
        line_color = QColor(144, 238, 144, 40)  # Light green with transparency

        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        self.setExtraSelections([selection])

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events.

        Implements auto-indentation and parentheses/quotes auto-completion.

        Args:
            event: Key event
        """
        # Auto-indentation
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            cursor = self.textCursor()
            cursor.select(QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()

            # Extract indentation from current line
            indentation = ''
            for char in current_line:
                if char in (' ', '\t'):
                    indentation += char
                else:
                    break

            # Add extra indentation after certain keywords
            if any(current_line.strip().upper().endswith(keyword) for keyword in (
                    'BEGIN', 'THEN', 'ELSE', 'DO', 'CASE', 'SELECT', 'FROM', 'WHERE',
                    'HAVING', 'ORDER BY', 'GROUP BY'
            )):
                indentation += '    '

            # Insert new line with indentation
            super().keyPressEvent(event)
            if indentation:
                self.insertPlainText(indentation)
            return

        # Auto-insert closing parenthesis
        if event.key() == Qt.Key_ParenLeft:
            super().keyPressEvent(event)
            self.insertPlainText(')')
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
            return

        # Auto-insert closing double quote
        if event.key() == Qt.Key_QuoteDbl:
            super().keyPressEvent(event)
            self.insertPlainText('"')
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
            return

        # Auto-insert closing single quote
        if event.key() == Qt.Key_Apostrophe:
            super().keyPressEvent(event)
            self.insertPlainText("'")
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
            return

        # Default handling for other keys
        super().keyPressEvent(event)

    def format_sql(self) -> None:
        """Format the SQL query with proper indentation and keyword casing."""
        try:
            import sqlparse
        except ImportError:
            return

        sql_text = self.toPlainText()
        if not sql_text.strip():
            return

        formatted_sql = sqlparse.format(
            sql_text,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower',
            indent_width=4
        )

        self.setPlainText(formatted_sql)


class ParameterWidget(QWidget):
    """Widget for displaying and editing a query parameter."""

    valueChanged = Signal(str, object)  # Parameter name, new value

    def __init__(
            self, param_name: str, description: str = '',
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the parameter widget.

        Args:
            param_name: Parameter name
            description: Parameter description
            parent: Parent widget
        """
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.param_name = param_name
        self.description = description

        # Input field for parameter value
        self.input_field = QLineEdit()
        self.input_field.setObjectName(f'param_{param_name}')

        if description:
            self.input_field.setPlaceholderText(description)
            self.input_field.setToolTip(description)
        else:
            self.input_field.setPlaceholderText('Enter value')

        self.input_field.textChanged.connect(self._on_value_changed)
        layout.addWidget(self.input_field)

        # Help button for parameter description
        self.help_button = None
        if description:
            self.help_button = QPushButton('?')
            self.help_button.setFixedSize(24, 24)
            self.help_button.setToolTip(description)
            self.help_button.clicked.connect(self._show_help)
            layout.addWidget(self.help_button)

    def _show_help(self) -> None:
        """Show parameter description in a tooltip."""
        if self.description and self.help_button:
            pos = self.help_button.mapToGlobal(QPoint(0, self.help_button.height()))
            QToolTip.showText(pos, self.description, self.help_button)

    def _on_value_changed(self, text: str) -> None:
        """Handle value changes and emit signal.

        Args:
            text: New parameter value
        """
        value = self._convert_value(text)
        self.valueChanged.emit(self.param_name, value)

    def get_value(self) -> Any:
        """Get the parameter value with appropriate type conversion.

        Returns:
            Converted parameter value
        """
        return self._convert_value(self.input_field.text())

    def _convert_value(self, text: str) -> Any:
        """Convert text to appropriate type.

        Args:
            text: Text to convert

        Returns:
            Converted value with appropriate type
        """
        if not text or text.lower() == 'null':
            return None
        elif text.isdigit():
            return int(text)
        elif text.replace('.', '', 1).isdigit():
            return float(text)
        elif text.lower() in ('true', 'false'):
            return text.lower() == 'true'
        else:
            return text

    def set_value(self, value: Any) -> None:
        """Set the parameter value.

        Args:
            value: Parameter value
        """
        if value is None:
            self.input_field.setText('NULL')
        else:
            self.input_field.setText(str(value))


class QueryEditorWidget(QWidget):
    """Widget for editing and executing SQL queries."""

    executeQueryRequested = Signal()
    saveQueryRequested = Signal()

    def __init__(self, plugin: Any, logger: Any, parent: Optional[QWidget] = None) -> None:
        """Initialize the query editor widget.

        Args:
            plugin: Plugin instance
            logger: Logger for logging messages
            parent: Parent widget
        """
        super().__init__(parent)

        self._plugin = plugin
        self._logger = logger
        self._current_connection_id: Optional[str] = None
        self._current_query_id: Optional[str] = None
        self._current_mapping_id: Optional[str] = None
        self._parameter_widgets: Dict[str, ParameterWidget] = {}
        self._parameter_values: Dict[str, Any] = {}
        self._parameter_manager = QueryParameterManager(logger)
        self._mapping_manager = FieldMappingManager(logger=logger)

        self._logger.debug('Initializing QueryEditorWidget')
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Toolbar with actions
        toolbar = QToolBar('Query Tools')
        toolbar.setIconSize(QSize(16, 16))

        # New/Save Query actions
        new_action = toolbar.addAction('New Query')
        new_action.triggered.connect(self._on_new_query)

        save_action = toolbar.addAction('Save Query')
        save_action.triggered.connect(self._on_save_query)

        toolbar.addSeparator()

        # Format SQL action
        format_action = toolbar.addAction('Format SQL')
        format_action.triggered.connect(self._on_format_sql)

        toolbar.addSeparator()

        # Results limit control
        limit_label = QLabel('Limit results:')
        toolbar.addWidget(limit_label)

        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(0, 100000)
        self._limit_spin.setValue(1000)
        self._limit_spin.setSpecialValueText('No limit')
        self._limit_spin.setFixedWidth(80)
        toolbar.addWidget(self._limit_spin)

        toolbar.addSeparator()

        # Field mapping selector
        mapping_label = QLabel('Apply field mapping:')
        toolbar.addWidget(mapping_label)

        self._mapping_combo = QComboBox()
        self._mapping_combo.addItem('None', None)
        self._mapping_combo.setMinimumWidth(150)
        toolbar.addWidget(self._mapping_combo)

        main_layout.addWidget(toolbar)

        # Main splitter with query list and editor
        splitter = QSplitter(Qt.Horizontal)

        # Saved queries panel
        queries_widget = QWidget()
        queries_layout = QVBoxLayout(queries_widget)
        queries_layout.setContentsMargins(0, 0, 0, 0)

        queries_label = QLabel('Saved Queries')
        queries_label.setFont(QFont('Arial', 10, QFont.Bold))
        queries_layout.addWidget(queries_label)

        self._queries_list = QListWidget()
        self._queries_list.itemDoubleClicked.connect(self._on_query_double_clicked)
        queries_layout.addWidget(self._queries_list)

        # Query list actions
        query_list_toolbar = QToolBar()

        load_action = query_list_toolbar.addAction('Load')
        load_action.triggered.connect(self._on_load_query)

        delete_action = query_list_toolbar.addAction('Delete')
        delete_action.triggered.connect(self._on_delete_query)

        query_list_toolbar.addSeparator()

        import_action = query_list_toolbar.addAction('Import')
        import_action.triggered.connect(self._on_import_queries)

        export_action = query_list_toolbar.addAction('Export')
        export_action.triggered.connect(self._on_export_queries)

        queries_layout.addWidget(query_list_toolbar)
        splitter.addWidget(queries_widget)

        # SQL Editor panel
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        editor_label = QLabel('SQL Query')
        editor_label.setFont(QFont('Arial', 10, QFont.Bold))
        editor_layout.addWidget(editor_label)

        self._editor = SQLEditor()
        editor_layout.addWidget(self._editor)

        # Parameters panel
        self._params_group = QGroupBox('Query Parameters')
        self._params_layout = QFormLayout(self._params_group)

        params_scroll = QScrollArea()
        params_scroll.setWidgetResizable(True)
        params_scroll.setWidget(self._params_group)
        params_scroll.setMaximumHeight(150)

        editor_layout.addWidget(params_scroll)
        splitter.addWidget(editor_widget)

        # Set initial splitter sizes
        splitter.setSizes([150, 450])
        main_layout.addWidget(splitter)

        # Execute button
        execute_layout = QHBoxLayout()
        execute_layout.addStretch()

        self._execute_button = QPushButton('Execute Query')
        self._execute_button.setMinimumWidth(150)
        self._execute_button.clicked.connect(self._on_execute_query)
        self._execute_button.setEnabled(False)

        execute_layout.addWidget(self._execute_button)
        execute_layout.addStretch()
        main_layout.addLayout(execute_layout)

        # Hide parameters initially
        self._params_group.setVisible(False)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        self._editor.textChanged.connect(self._on_query_text_changed)

    async def refresh(self) -> None:
        """Refresh the editor content and state."""
        await self.reload_queries()

        if self._current_connection_id:
            await self._load_field_mappings()

    async def reload_queries(self) -> None:
        """Reload the list of saved queries."""
        try:
            if not self._current_connection_id:
                self._queries_list.clear()
                return

            saved_queries = await self._plugin.get_saved_queries(self._current_connection_id)
            self._queries_list.clear()

            # Sort queries by name
            sorted_queries = sorted(saved_queries.values(), key=lambda q: q.name.lower())

            # Add favorites first
            for query in [q for q in sorted_queries if q.is_favorite]:
                item = QListWidgetItem(f'⭐ {query.name}')
                item.setData(Qt.UserRole, query.id)
                self._queries_list.addItem(item)

            # Add non-favorites
            for query in [q for q in sorted_queries if not q.is_favorite]:
                item = QListWidgetItem(query.name)
                item.setData(Qt.UserRole, query.id)
                self._queries_list.addItem(item)

        except Exception as e:
            self._logger.error(f'Failed to load saved queries: {str(e)}')

    async def _load_field_mappings(self) -> None:
        """Load field mappings for the current connection."""
        try:
            if not self._current_connection_id:
                self._mapping_combo.clear()
                self._mapping_combo.addItem('None', None)
                return

            field_mappings = await self._plugin.get_field_mappings(self._current_connection_id)
            current_id = self._mapping_combo.currentData()

            self._mapping_combo.clear()
            self._mapping_combo.addItem('None', None)

            # Sort mappings by table name and description
            sorted_mappings = sorted(
                field_mappings.values(),
                key=lambda m: f"{m.table_name}_{m.description or ''}"
            )

            # Add all mappings to combo box
            for mapping in sorted_mappings:
                display_text = mapping.table_name
                if mapping.description:
                    display_text += f' ({mapping.description})'
                self._mapping_combo.addItem(display_text, mapping.id)

            # Restore previous selection if possible
            if current_id:
                for i in range(self._mapping_combo.count()):
                    if self._mapping_combo.itemData(i) == current_id:
                        self._mapping_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f'Failed to load field mappings: {str(e)}')

    def set_connection_status(self, connection_id: str, connected: bool) -> None:
        """Update UI based on connection status.

        Args:
            connection_id: Connection ID
            connected: Whether connection is established
        """
        if connected:
            self._current_connection_id = connection_id
            self._execute_button.setEnabled(True)
            asyncio.create_task(self.reload_queries())
            asyncio.create_task(self._load_field_mappings())
        elif self._current_connection_id == connection_id:
            self._current_connection_id = None
            self._execute_button.setEnabled(False)

    def get_query_text(self) -> str:
        """Get the current query text.

        Returns:
            Current SQL query text
        """
        return self._editor.toPlainText()

    def get_parameters(self) -> Dict[str, Any]:
        """Get the current parameter values.

        Returns:
            Dictionary of parameter values
        """
        params = {}
        for param_name, widget in self._parameter_widgets.items():
            params[param_name] = widget.get_value()
        return params

    def get_limit(self) -> Optional[int]:
        """Get the current result limit.

        Returns:
            Result limit or None for no limit
        """
        if self._limit_spin.value() == 0:
            return None
        return self._limit_spin.value()

    def get_mapping_id(self) -> Optional[str]:
        """Get the selected field mapping ID.

        Returns:
            Field mapping ID or None if no mapping selected
        """
        return self._mapping_combo.currentData()

    def get_current_query_id(self) -> Optional[str]:
        """Get the ID of the currently edited query.

        Returns:
            Query ID or None if editing a new query
        """
        return self._current_query_id

    def get_current_query_name(self) -> str:
        """Get the name of the currently edited query.

        Returns:
            Query name or empty string if unknown
        """
        selected_items = self._queries_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            query_id = item.data(Qt.UserRole)
            if query_id == self._current_query_id:
                name = item.text()
                if name.startswith('⭐ '):
                    return name[2:]
                return name
        return ''

    def _on_query_text_changed(self) -> None:
        """Handle query text changes."""
        # Use debouncing to avoid excessive parameter updates
        if hasattr(self, '_param_update_timer'):
            self._param_update_timer.stop()
        else:
            self._param_update_timer = QTimer(self)
            self._param_update_timer.setSingleShot(True)
            self._param_update_timer.timeout.connect(self._update_parameters_debounced)

        self._param_update_timer.start(500)

    def _update_parameters_debounced(self) -> None:
        """Update parameter controls after debounce delay."""
        query_text = self._editor.toPlainText()
        self._logger.debug(f'Query changed, length: {len(query_text)}')

        # Detect parameters in query
        params = self._parameter_manager.detect_parameters(query_text)
        self._logger.debug(f'Detected {len(params)} parameters')

        # Update parameter controls
        self._update_parameter_controls(params)

    def _update_parameter_controls(self, param_descriptions: List[ParameterDescription]) -> None:
        """Update parameter input controls based on detected parameters.

        Args:
            param_descriptions: List of parameter descriptions
        """
        # Save current values
        current_values = {}
        current_descriptions = {}

        for param_name, widget in self._parameter_widgets.items():
            current_values[param_name] = widget.input_field.text()
            current_descriptions[param_name] = getattr(widget, 'description', '')

        # Clear existing controls
        self._clear_parameter_controls()

        # If no parameters, hide the panel
        if not param_descriptions:
            self._params_group.setVisible(False)
            return

        # Show parameters panel
        self._params_group.setVisible(True)

        # Create parameter widgets
        self._logger.debug(f'Creating parameters: {[p.name for p in param_descriptions]}')

        for param in param_descriptions:
            # Get description from saved query if available
            description = param.description
            if (self._current_query_id and
                    self._current_query_id in self._plugin._saved_queries and
                    hasattr(self._plugin._saved_queries[self._current_query_id], 'parameter_descriptions')):

                saved_desc = self._plugin._saved_queries[self._current_query_id].parameter_descriptions.get(
                    param.name, ''
                )
                if saved_desc:
                    description = saved_desc

            # Create parameter widget
            widget = ParameterWidget(param.name, description)

            # Restore previous value if exists
            if param.name in current_values:
                widget.input_field.setText(current_values[param.name])

            # Add to form layout
            self._params_layout.addRow(f'{param.name}:', widget)

            # Store widget and connect signals
            self._parameter_widgets[param.name] = widget
            widget.valueChanged.connect(self._on_parameter_value_changed)

            # Add context menu for editing description
            self._add_parameter_context_menu(widget)

    def _on_parameter_value_changed(self, param_name: str, value: Any) -> None:
        """Handle parameter value changes.

        Args:
            param_name: Name of the parameter
            value: New value
        """
        self._parameter_values[param_name] = value
        self._logger.debug(f'Parameter {param_name} changed to {value}')

    def _add_parameter_context_menu(self, param_widget: ParameterWidget) -> None:
        """Add context menu to parameter widget.

        Args:
            param_widget: Parameter widget
        """
        input_field = param_widget.input_field
        input_field.setContextMenuPolicy(Qt.CustomContextMenu)

        def show_context_menu(pos: QPoint) -> None:
            menu = QMenu()
            edit_desc_action = menu.addAction('Edit Description')
            edit_desc_action.triggered.connect(
                lambda: self._edit_parameter_description(param_widget)
            )
            menu.exec_(input_field.mapToGlobal(pos))

        input_field.customContextMenuRequested.connect(show_context_menu)

    def _edit_parameter_description(self, param_widget: ParameterWidget) -> None:
        """Edit parameter description.

        Args:
            param_widget: Parameter widget
        """
        description, ok = QInputDialog.getText(
            self,
            f'Edit Parameter Description',
            f'Enter description for parameter {param_widget.param_name}:',
            text=param_widget.description
        )

        if ok:
            # Update widget
            param_widget.description = description
            param_widget.input_field.setPlaceholderText(description)
            param_widget.input_field.setToolTip(description)

            # Update help button
            if param_widget.help_button:
                param_widget.help_button.setToolTip(description)
            elif description:
                # Create help button if it doesn't exist
                layout = param_widget.layout()
                param_widget.help_button = QPushButton('?')
                param_widget.help_button.setFixedSize(24, 24)
                param_widget.help_button.setToolTip(description)
                param_widget.help_button.clicked.connect(param_widget._show_help)
                layout.addWidget(param_widget.help_button)

            # Update saved query
            if self._current_query_id and self._current_query_id in self._plugin._saved_queries:
                query = self._plugin._saved_queries[self._current_query_id]
                if not hasattr(query, 'parameter_descriptions'):
                    query.parameter_descriptions = {}

                if description:
                    query.parameter_descriptions[param_widget.param_name] = description
                elif param_widget.param_name in query.parameter_descriptions:
                    del query.parameter_descriptions[param_widget.param_name]

                asyncio.create_task(self._plugin.save_query(query))

    def _clear_parameter_controls(self) -> None:
        """Clear all parameter controls."""
        self._parameter_widgets.clear()

        # Create new layout for parameters
        new_layout = QFormLayout()
        parent = self._params_group
        old_layout = parent.layout()

        if old_layout:
            # Remove all widgets from old layout
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Set new layout
            parent.setLayout(None)
            old_layout.deleteLater()

        parent.setLayout(new_layout)
        self._params_layout = new_layout

    def _on_new_query(self) -> None:
        """Create a new query."""
        self._editor.clear()
        self._current_query_id = None
        self._queries_list.clearSelection()
        self._clear_parameter_controls()
        self._params_group.setVisible(False)

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
        """Load query when double-clicked in the list.

        Args:
            item: Selected list item
        """
        query_id = item.data(Qt.UserRole)
        if not query_id:
            return

        asyncio.create_task(self._load_query_by_id(query_id))

    def _on_load_query(self) -> None:
        """Load the selected query."""
        selected_items = self._queries_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'No Query Selected', 'Please select a query to load.')
            return

        query_id = selected_items[0].data(Qt.UserRole)
        if not query_id:
            return

        asyncio.create_task(self._load_query_by_id(query_id))

    async def _load_query_by_id(self, query_id: str) -> None:
        """Load a query by ID.

        Args:
            query_id: Query ID
        """
        try:
            query = await self._plugin.get_saved_query(query_id)
            if not query:
                self._logger.warning(f'Query not found: {query_id}')
                return

            self._logger.debug(f'Loading query: {query.name} with text length: {len(query.query_text)}')

            # Store the query ID and update the editor
            self._current_query_id = query_id
            self._editor.setText(query.query_text)

            # Short delay to ensure text change event is processed
            await asyncio.sleep(0.1)

            # Set parameter values
            self._logger.debug(f'Query parameters: {query.parameters}')
            if query.parameters:
                self._set_parameter_values(query.parameters)

            # Set field mapping
            if query.field_mapping_id:
                self._logger.debug(f'Setting field mapping: {query.field_mapping_id}')
                for i in range(self._mapping_combo.count()):
                    if self._mapping_combo.itemData(i) == query.field_mapping_id:
                        self._mapping_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            self._logger.error(f'Failed to load query: {str(e)}')

    def _set_parameter_values(self, params: Dict[str, Any]) -> None:
        """Set parameter values.

        Args:
            params: Parameter values
        """
        for param_name, value in params.items():
            if param_name in self._parameter_widgets:
                self._parameter_widgets[param_name].set_value(value)

    def _on_delete_query(self) -> None:
        """Delete the selected query."""
        selected_items = self._queries_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'No Query Selected', 'Please select a query to delete.')
            return

        item = selected_items[0]
        query_id = item.data(Qt.UserRole)
        if not query_id:
            return

        reply = QMessageBox.question(
            self,
            'Confirm Deletion',
            f'Are you sure you want to delete this query?\n\n{item.text()}',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        asyncio.create_task(self._delete_query(query_id))

    async def _delete_query(self, query_id: str) -> None:
        """Delete a query.

        Args:
            query_id: Query ID
        """
        try:
            success = await self._plugin.delete_query(query_id)
            if success:
                if query_id == self._current_query_id:
                    self._editor.clear()
                    self._current_query_id = None
                    self._clear_parameter_controls()
                    self._params_group.setVisible(False)

                await self.reload_queries()

        except Exception as e:
            self._logger.error(f'Failed to delete query: {str(e)}')
            QMessageBox.critical(self, 'Delete Error', f'Failed to delete query: {str(e)}')

    def _on_import_queries(self) -> None:
        """Import queries from file."""
        if not self._current_connection_id:
            QMessageBox.warning(
                self,
                'No Connection Selected',
                'Please connect to a database before importing queries.'
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import Queries', '', 'JSON Files (*.json);;All Files (*.*)'
        )

        if file_path:
            asyncio.create_task(self._import_queries_from_file(file_path))

    async def _import_queries_from_file(self, file_path: str) -> None:
        """Import queries from a file.

        Args:
            file_path: Path to the file
        """
        try:
            import json
            import uuid
            import datetime

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError('Invalid file format: Expected a list of queries')

            imported_count = 0
            for item in data:
                try:
                    if not isinstance(item, dict):
                        continue

                    # Set new ID and connection ID
                    item['id'] = str(uuid.uuid4())
                    item['connection_id'] = self._current_connection_id

                    # Convert date strings to datetime objects
                    if 'created_at' in item and isinstance(item['created_at'], str):
                        item['created_at'] = datetime.datetime.fromisoformat(item['created_at'])

                    if 'updated_at' in item and isinstance(item['updated_at'], str):
                        item['updated_at'] = datetime.datetime.fromisoformat(item['updated_at'])

                    # Create and save query
                    query = SavedQuery(**item)
                    await self._plugin.save_query(query)
                    imported_count += 1

                except Exception as e:
                    self._logger.warning(f'Failed to import query: {str(e)}')

            # Reload query list
            await self.reload_queries()

            QMessageBox.information(
                self, 'Import Successful', f'Imported {imported_count} queries.'
            )

        except Exception as e:
            self._logger.error(f'Failed to import queries: {str(e)}')
            QMessageBox.critical(self, 'Import Error', f'Failed to import queries: {str(e)}')

    def _on_export_queries(self) -> None:
        """Export queries to file."""
        if not self._current_connection_id:
            QMessageBox.warning(
                self,
                'No Connection Selected',
                'Please connect to a database before exporting queries.'
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export Queries', '', 'JSON Files (*.json);;All Files (*.*)'
        )

        if not file_path:
            return

        if not file_path.endswith('.json'):
            file_path += '.json'

        asyncio.create_task(self._export_queries_to_file(file_path))

    async def _export_queries_to_file(self, file_path: str) -> None:
        """Export queries to a file.

        Args:
            file_path: Path to the file
        """
        try:
            import json
            import datetime

            queries = await self._plugin.get_saved_queries(self._current_connection_id)
            if not queries:
                QMessageBox.warning(self, 'No Queries', 'There are no queries to export.')
                return

            query_list = []
            for query in queries.values():
                query_dict = query.dict()

                # Convert datetime objects to ISO format strings
                if 'created_at' in query_dict and isinstance(query_dict['created_at'], datetime.datetime):
                    query_dict['created_at'] = query_dict['created_at'].isoformat()

                if 'updated_at' in query_dict and isinstance(query_dict['updated_at'], datetime.datetime):
                    query_dict['updated_at'] = query_dict['updated_at'].isoformat()

                query_list.append(query_dict)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(query_list, f, indent=2)

            QMessageBox.information(
                self,
                'Export Successful',
                f'Exported {len(query_list)} queries to {file_path}'
            )

        except Exception as e:
            self._logger.error(f'Failed to export queries: {str(e)}')
            QMessageBox.critical(self, 'Export Error', f'Failed to export queries: {str(e)}')