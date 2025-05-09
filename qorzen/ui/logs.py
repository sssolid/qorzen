from __future__ import annotations

import json
import time
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter,
    QTableView, QTextEdit, QToolBar, QVBoxLayout, QWidget
)


class LogLevel(Enum):
    """Log levels with colors."""

    DEBUG = (QColor(108, 117, 125), "DEBUG")  # Gray
    INFO = (QColor(23, 162, 184), "INFO")  # Blue
    WARNING = (QColor(255, 193, 7), "WARNING")  # Yellow
    ERROR = (QColor(220, 53, 69), "ERROR")  # Red
    CRITICAL = (QColor(136, 14, 79), "CRITICAL")  # Purple

    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """Get a log level from a string.

        Args:
            level_str: The log level string

        Returns:
            The corresponding LogLevel enum value
        """
        level_str = level_str.upper()

        for level in cls:
            if level.value[1] == level_str:
                return level

        # Default to INFO if not found
        return cls.INFO


class LogEntry:
    """Represents a log entry in the log view."""

    def __init__(
            self,
            timestamp: str,
            level: LogLevel,
            logger: str,
            message: str,
            event: str = "",
            task: str = "",
            raw_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize a log entry.

        Args:
            timestamp: The timestamp string
            level: The log level
            logger: The logger name
            message: The log message
            event: Optional event name
            task: Optional task name
            raw_data: Optional raw log data
        """
        self.timestamp = timestamp
        self.level = level
        self.logger = logger
        self.message = message
        self.event = event
        self.task = task
        self.raw_data = raw_data or {}

    @classmethod
    def from_event_payload(cls, payload: Dict[str, Any]) -> 'LogEntry':
        """Create a log entry from an event payload.

        Args:
            payload: The event payload

        Returns:
            A new LogEntry instance
        """
        # Parse the message if it's JSON
        message_content = payload.get('message', '')
        parsed = {}

        if isinstance(message_content, str):
            try:
                parsed = json.loads(message_content)
            except json.JSONDecodeError:
                parsed = {'message': message_content}
        elif isinstance(message_content, dict):
            parsed = message_content

        # Combine payload and parsed message
        combined = {**payload, **parsed}

        # Extract fields
        timestamp = combined.get('timestamp', combined.get('asctime', time.strftime('%Y-%m-%d %H:%M:%S')))
        level_str = combined.get('level', combined.get('levelname', 'INFO'))
        logger = combined.get('name', combined.get('logger', ''))
        message = combined.get('message', '')
        event = combined.get('event', '')
        task = combined.get('taskName', combined.get('task', ''))

        return cls(
            timestamp=timestamp,
            level=LogLevel.from_string(level_str),
            logger=logger,
            message=message,
            event=event,
            task=task,
            raw_data=combined
        )


class LogTableModel(QAbstractTableModel):
    """Model for the log table view."""

    COLUMNS = ['Timestamp', 'Level', 'Logger', 'Message', 'Event', 'Task']

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the log table model.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self._logs: List[LogEntry] = []
        self._filtered_logs: List[LogEntry] = []
        self._filter_text = ""
        self._filter_level: Optional[LogLevel] = None
        self._filter_logger = ""
        self._apply_filters()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get the number of rows in the model.

        Args:
            parent: The parent index

        Returns:
            The number of rows
        """
        if parent.isValid():
            return 0
        return len(self._filtered_logs)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get the number of columns in the model.

        Args:
            parent: The parent index

        Returns:
            The number of columns
        """
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Get data for a specific index and role.

        Args:
            index: The model index
            role: The data role

        Returns:
            The requested data
        """
        if not index.isValid() or index.row() >= len(self._filtered_logs):
            return None

        log_entry = self._filtered_logs[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            # Return text data for the cell
            if column == 0:
                return log_entry.timestamp
            elif column == 1:
                return log_entry.level.value[1]
            elif column == 2:
                return log_entry.logger
            elif column == 3:
                return log_entry.message
            elif column == 4:
                return log_entry.event
            elif column == 5:
                return log_entry.task

        elif role == Qt.ForegroundRole:
            # Set text color for log level
            if column == 1:
                return QBrush(log_entry.level.value[0])

        elif role == Qt.ToolTipRole:
            # Provide tooltip with more details
            if column == 3:  # Message column
                return log_entry.message

        elif role == Qt.TextAlignmentRole:
            # Align text properly
            if column == 0:  # Timestamp
                return Qt.AlignLeft | Qt.AlignVCenter
            elif column == 1:  # Level
                return Qt.AlignCenter
            else:
                return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.UserRole:
            # Return the full log entry for custom uses
            return log_entry

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """Get header data.

        Args:
            section: The section index
            orientation: The header orientation
            role: The data role

        Returns:
            The header data
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def add_log(self, log_entry: LogEntry) -> None:
        """Add a log entry to the model.

        Args:
            log_entry: The log entry to add
        """
        # Add to the full logs list
        self.beginInsertRows(QModelIndex(), len(self._logs), len(self._logs))
        self._logs.append(log_entry)
        self.endInsertRows()

        # Apply filters
        self._apply_filters()

    def clear_logs(self) -> None:
        """Clear all logs from the model."""
        self.beginResetModel()
        self._logs.clear()
        self._filtered_logs.clear()
        self.endResetModel()

    def set_filter_text(self, text: str) -> None:
        """Set the text filter.

        Args:
            text: The filter text
        """
        if self._filter_text != text:
            self._filter_text = text
            self._apply_filters()

    def set_filter_level(self, level: Optional[LogLevel]) -> None:
        """Set the level filter.

        Args:
            level: The log level filter, or None for all levels
        """
        if self._filter_level != level:
            self._filter_level = level
            self._apply_filters()

    def set_filter_logger(self, logger: str) -> None:
        """Set the logger filter.

        Args:
            logger: The logger name filter
        """
        if self._filter_logger != logger:
            self._filter_logger = logger
            self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply all filters to update the filtered logs list."""
        self.beginResetModel()

        # Start with all logs
        filtered = self._logs

        # Apply text filter
        if self._filter_text:
            filtered = [
                log for log in filtered
                if (self._filter_text.lower() in log.message.lower() or
                    self._filter_text.lower() in log.logger.lower() or
                    self._filter_text.lower() in log.event.lower() or
                    self._filter_text.lower() in log.task.lower())
            ]

        # Apply level filter
        if self._filter_level:
            filtered = [
                log for log in filtered
                if log.level == self._filter_level
            ]

        # Apply logger filter
        if self._filter_logger:
            filtered = [
                log for log in filtered
                if self._filter_logger.lower() in log.logger.lower()
            ]

        self._filtered_logs = filtered
        self.endResetModel()

    def get_unique_loggers(self) -> List[str]:
        """Get a list of unique logger names in the logs.

        Returns:
            A list of unique logger names
        """
        return sorted(set(log.logger for log in self._logs if log.logger))


class LogsView(QWidget):
    """Widget for displaying and filtering logs."""

    def __init__(
            self,
            event_bus: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the logs view.

        Args:
            event_bus: The event bus
            parent: The parent widget
        """
        super().__init__(parent)

        self._event_bus = event_bus
        self._log_subscription_id = None

        # Set up UI
        self._setup_ui()

        # Subscribe to log events
        self._subscribe_to_log_events()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Filter toolbar
        filter_toolbar = QToolBar()
        filter_toolbar.setMovable(False)
        filter_toolbar.setFloatable(False)
        filter_toolbar.setIconSize(QSize(16, 16))
        main_layout.addWidget(filter_toolbar)

        # Text filter
        filter_toolbar.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter logs...")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._on_filter_text_changed)
        filter_toolbar.addWidget(self._filter_edit)

        filter_toolbar.addSeparator()

        # Level filter
        filter_toolbar.addWidget(QLabel("Level:"))
        self._level_combo = QComboBox()
        self._level_combo.addItem("All Levels", None)
        for level in LogLevel:
            self._level_combo.addItem(level.value[1], level)
        self._level_combo.currentIndexChanged.connect(self._on_level_filter_changed)
        filter_toolbar.addWidget(self._level_combo)

        filter_toolbar.addSeparator()

        # Logger filter
        filter_toolbar.addWidget(QLabel("Logger:"))
        self._logger_combo = QComboBox()
        self._logger_combo.addItem("All Loggers", "")
        self._logger_combo.setMinimumWidth(150)
        self._logger_combo.currentTextChanged.connect(self._on_logger_filter_changed)
        filter_toolbar.addWidget(self._logger_combo)

        filter_toolbar.addSeparator()

        # Auto-scroll checkbox
        self._auto_scroll_check = QCheckBox("Auto-scroll")
        self._auto_scroll_check.setChecked(True)
        filter_toolbar.addWidget(self._auto_scroll_check)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        filter_toolbar.addWidget(spacer)

        # Clear button
        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self._on_clear_clicked)
        filter_toolbar.addWidget(clear_button)

        # Create splitter for log view and details
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter, 1)  # Give splitter stretch

        # Log table
        self._log_model = LogTableModel(self)
        self._log_table = QTableView()
        self._log_table.setModel(self._log_model)
        self._log_table.setSelectionBehavior(QTableView.SelectRows)
        self._log_table.setSelectionMode(QTableView.SingleSelection)
        self._log_table.setAlternatingRowColors(True)
        self._log_table.verticalHeader().setVisible(False)
        self._log_table.setSortingEnabled(True)
        self._log_table.sortByColumn(0, Qt.AscendingOrder)  # Sort by timestamp by default

        # Configure column widths
        header = self._log_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Message column stretches

        # Connect selection signal
        self._log_table.selectionModel().selectionChanged.connect(self._on_selection_changed)

        splitter.addWidget(self._log_table)

        # Log details view
        self._log_details = QTextEdit()
        self._log_details.setReadOnly(True)
        self._log_details.setMaximumHeight(200)
        splitter.addWidget(self._log_details)

        # Set initial splitter sizes
        splitter.setSizes([500, 100])

    def _subscribe_to_log_events(self) -> None:
        """Subscribe to log events from the event bus."""
        if not self._event_bus:
            return

        self._log_subscription_id = self._event_bus.subscribe(
            event_type='log/event',
            callback=self._on_log_event,
            subscriber_id='logs_view'
        )

    def _on_log_event(self, event: Any) -> None:
        """Handle log events.

        Args:
            event: The log event
        """
        # Create a log entry from the event payload
        log_entry = LogEntry.from_event_payload(event.payload)

        # Add to model
        self._log_model.add_log(log_entry)

        # Update logger filter combo if needed
        self._update_logger_combo()

        # Auto-scroll if enabled
        if self._auto_scroll_check.isChecked():
            self._log_table.scrollToBottom()

    def _update_logger_combo(self) -> None:
        """Update the logger filter combo box with current loggers."""
        current_text = self._logger_combo.currentText()

        # Block signals to prevent filter changes during update
        self._logger_combo.blockSignals(True)

        # Clear and rebuild
        self._logger_combo.clear()
        self._logger_combo.addItem("All Loggers", "")

        # Add all unique loggers
        for logger in self._log_model.get_unique_loggers():
            self._logger_combo.addItem(logger, logger)

        # Restore previous selection if possible
        index = self._logger_combo.findText(current_text)
        if index >= 0:
            self._logger_combo.setCurrentIndex(index)

        self._logger_combo.blockSignals(False)

    def _on_filter_text_changed(self, text: str) -> None:
        """Handle filter text changes.

        Args:
            text: The new filter text
        """
        self._log_model.set_filter_text(text)

    def _on_level_filter_changed(self, index: int) -> None:
        """Handle level filter changes.

        Args:
            index: The new combo box index
        """
        level = self._level_combo.itemData(index)
        self._log_model.set_filter_level(level)

    def _on_logger_filter_changed(self, text: str) -> None:
        """Handle logger filter changes.

        Args:
            text: The new logger filter
        """
        if text == "All Loggers":
            self._log_model.set_filter_logger("")
        else:
            self._log_model.set_filter_logger(text)

    def _on_clear_clicked(self) -> None:
        """Handle clear button clicks."""
        self._log_model.clear_logs()
        self._log_details.clear()

    def _on_selection_changed(self, selected: Any, deselected: Any) -> None:
        """Handle log entry selection changes.

        Args:
            selected: The selected indexes
            deselected: The deselected indexes
        """
        indexes = self._log_table.selectionModel().selectedIndexes()
        if not indexes:
            self._log_details.clear()
            return

        # Get the log entry from the model
        row = indexes[0].row()
        log_entry = self._log_model.data(
            self._log_model.index(row, 0),
            Qt.UserRole
        )

        if not log_entry:
            self._log_details.clear()
            return

        # Format details as JSON
        try:
            formatted_json = json.dumps(log_entry.raw_data, indent=2)
            self._log_details.setPlainText(formatted_json)
        except Exception:
            # Fallback to simple text display
            details = f"""
            Timestamp: {log_entry.timestamp}
            Level: {log_entry.level.value[1]}
            Logger: {log_entry.logger}
            Message: {log_entry.message}
            Event: {log_entry.event}
            Task: {log_entry.task}
            """
            self._log_details.setPlainText(details.strip())

    def showEvent(self, event: Any) -> None:
        """Handle widget show events.

        Args:
            event: The event
        """
        super().showEvent(event)

    def hideEvent(self, event: Any) -> None:
        """Handle widget hide events.

        Args:
            event: The event
        """
        super().hideEvent(event)

    def closeEvent(self, event: Any) -> None:
        """Handle widget close events.

        Args:
            event: The event
        """
        # Unsubscribe from log events
        if self._event_bus and self._log_subscription_id:
            self._event_bus.unsubscribe(subscriber_id=self._log_subscription_id)

        super().closeEvent(event)