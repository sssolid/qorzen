from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from enum import Enum, auto
from functools import partial
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableView, QTextEdit,
    QToolBar, QVBoxLayout, QWidget, QMessageBox
)

from qorzen.core.event_model import EventType
from qorzen.ui.ui_component import AsyncTaskSignals


class LogLevel(Enum):
    """Enum representing log severity levels."""
    DEBUG = (QColor(108, 117, 125), "DEBUG")
    INFO = (QColor(23, 162, 184), "INFO")
    WARNING = (QColor(255, 193, 7), "WARNING")
    ERROR = (QColor(220, 53, 69), "ERROR")
    CRITICAL = (QColor(136, 14, 79), "CRITICAL")

    @classmethod
    def from_string(cls, level_str: str) -> "LogLevel":
        """
        Convert a string to a LogLevel enum value.

        Args:
            level_str: The string representation of the log level

        Returns:
            Matching LogLevel enum value, or INFO if no match
        """
        level_str = level_str.upper()
        for level in cls:
            if level.value[1] == level_str:
                return level
        return cls.INFO


class LogEntry:
    """Represents a single log entry in the application."""

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
        """
        Initialize a log entry.

        Args:
            timestamp: Time when the log was created
            level: Severity level of the log
            logger: Name of the logger that created the log
            message: The log message
            event: Associated event if any
            task: Associated task if any
            raw_data: Raw log data in dictionary form
        """
        self.timestamp = timestamp
        self.level = level
        self.logger = logger
        self.message = message
        self.event = event
        self.task = task
        self.raw_data = raw_data or {}

    @classmethod
    def from_event_payload(cls, payload: Dict[str, Any]) -> "LogEntry":
        """
        Create a LogEntry from an event payload.

        Args:
            payload: Event payload containing log information

        Returns:
            A LogEntry object populated from the payload
        """
        message_content = payload.get("message", "")
        parsed = {}

        if isinstance(message_content, str):
            try:
                parsed = json.loads(message_content)
            except json.JSONDecodeError:
                parsed = {"message": message_content}
        elif isinstance(message_content, dict):
            parsed = message_content

        combined = {**payload, **parsed}

        timestamp = combined.get(
            "timestamp",
            combined.get("asctime", time.strftime("%Y-%m-%d %H:%M:%S"))
        )
        level_str = combined.get(
            "level",
            combined.get("levelname", "INFO")
        )
        logger = combined.get(
            "name",
            combined.get("logger", "")
        )
        message = combined.get("message", "")
        event = combined.get("event", "")
        task = combined.get(
            "taskName",
            combined.get("task", "")
        )

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
    """Table model for displaying log entries."""

    COLUMNS = ["Timestamp", "Level", "Logger", "Message", "Event", "Task"]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the log table model.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._logs: List[LogEntry] = []
        self._filtered_logs: List[LogEntry] = []
        self._filter_text = ""
        self._filter_level: Optional[LogLevel] = None
        self._filter_logger = ""
        self._apply_filters()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        Args:
            parent: Parent model index

        Returns:
            Number of rows
        """
        if parent.isValid():
            return 0
        return len(self._filtered_logs)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get the number of columns in the model.

        Args:
            parent: Parent model index

        Returns:
            Number of columns
        """
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        Get data for a specific index and role.

        Args:
            index: Model index to get data for
            role: Role to get data for

        Returns:
            Data for the specified index and role
        """
        if not index.isValid() or index.row() >= len(self._filtered_logs):
            return None

        log_entry = self._filtered_logs[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
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
            if column == 1:
                return QBrush(log_entry.level.value[0])
        elif role == Qt.ToolTipRole:
            if column == 3:
                return log_entry.message
        elif role == Qt.TextAlignmentRole:
            if column == 0:
                return Qt.AlignLeft | Qt.AlignVCenter
            elif column == 1:
                return Qt.AlignCenter
            else:
                return Qt.AlignLeft | Qt.AlignVCenter
        elif role == Qt.UserRole:
            return log_entry

        return None

    def headerData(
            self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        """
        Get header data.

        Args:
            section: Section (row or column) index
            orientation: Header orientation
            role: Data role

        Returns:
            Header data for specified section, orientation and role
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def add_log(self, log_entry: LogEntry) -> None:
        """
        Add a log entry to the model.

        Args:
            log_entry: Log entry to add
        """
        self.beginInsertRows(QModelIndex(), len(self._logs), len(self._logs))
        self._logs.append(log_entry)
        self.endInsertRows()
        self._apply_filters()

    def clear_logs(self) -> None:
        """Clear all logs from the model."""
        self.beginResetModel()
        self._logs.clear()
        self._filtered_logs.clear()
        self.endResetModel()

    def set_filter_text(self, text: str) -> None:
        """
        Set text filter for logs.

        Args:
            text: Filter text
        """
        if self._filter_text != text:
            self._filter_text = text
            self._apply_filters()

    def set_filter_level(self, level: Optional[LogLevel]) -> None:
        """
        Set level filter for logs.

        Args:
            level: Log level to filter by
        """
        if self._filter_level != level:
            self._filter_level = level
            self._apply_filters()

    def set_filter_logger(self, logger: str) -> None:
        """
        Set logger filter for logs.

        Args:
            logger: Logger name to filter by
        """
        if self._filter_logger != logger:
            self._filter_logger = logger
            self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply all active filters to the logs."""
        self.beginResetModel()
        filtered = self._logs

        if self._filter_text:
            filtered = [
                log for log in filtered if (
                        self._filter_text.lower() in log.message.lower() or
                        self._filter_text.lower() in log.logger.lower() or
                        self._filter_text.lower() in log.event.lower() or
                        (self._filter_text.lower() in log.task.lower())
                )
            ]

        if self._filter_level:
            filtered = [log for log in filtered if log.level == self._filter_level]

        if self._filter_logger:
            filtered = [log for log in filtered if self._filter_logger.lower() in log.logger.lower()]

        self._filtered_logs = filtered
        self.endResetModel()

    def get_unique_loggers(self) -> List[str]:
        """
        Get a list of unique logger names.

        Returns:
            Sorted list of unique logger names
        """
        return sorted(set((log.logger for log in self._logs if log.logger)))


class LogsView(QWidget):
    """Widget for viewing and filtering application logs."""

    def __init__(
            self, event_bus_manager: Any, parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the logs view.

        Args:
            event_bus_manager: Reference to the event bus manager
            parent: Parent widget
        """
        super().__init__(parent)
        self._event_bus_manager = event_bus_manager
        self._log_subscription_id = None
        self._setup_ui()

        # Set up async handling
        self._async_signals = AsyncTaskSignals()
        self._async_signals.result_ready.connect(self._on_async_result)
        self._async_signals.error.connect(self._on_async_error)
        self._running_tasks: Dict[str, asyncio.Task] = {}

        # Subscribe to log events asynchronously
        self._start_async_task("subscribe", self._async_subscribe_to_log_events)

    def _setup_ui(self) -> None:
        """Set up the logs view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Filter toolbar
        filter_toolbar = QToolBar()
        filter_toolbar.setMovable(False)
        filter_toolbar.setFloatable(False)
        filter_toolbar.setIconSize(QSize(16, 16))
        main_layout.addWidget(filter_toolbar)

        filter_toolbar.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter logs...")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._on_filter_text_changed)
        filter_toolbar.addWidget(self._filter_edit)

        filter_toolbar.addSeparator()
        filter_toolbar.addWidget(QLabel("Level:"))
        self._level_combo = QComboBox()
        self._level_combo.addItem("All Levels", None)
        for level in LogLevel:
            self._level_combo.addItem(level.value[1], level)
        self._level_combo.currentIndexChanged.connect(self._on_level_filter_changed)
        filter_toolbar.addWidget(self._level_combo)

        filter_toolbar.addSeparator()
        filter_toolbar.addWidget(QLabel("Logger:"))
        self._logger_combo = QComboBox()
        self._logger_combo.addItem("All Loggers", "")
        self._logger_combo.setMinimumWidth(150)
        self._logger_combo.currentTextChanged.connect(self._on_logger_filter_changed)
        filter_toolbar.addWidget(self._logger_combo)

        filter_toolbar.addSeparator()
        self._auto_scroll_check = QCheckBox("Auto-scroll")
        self._auto_scroll_check.setChecked(True)
        filter_toolbar.addWidget(self._auto_scroll_check)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        filter_toolbar.addWidget(spacer)

        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self._on_clear_clicked)
        filter_toolbar.addWidget(clear_button)

        # Logs table and details view
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter, 1)

        self._log_model = LogTableModel(self)
        self._log_table = QTableView()
        self._log_table.setModel(self._log_model)
        self._log_table.setSelectionBehavior(QTableView.SelectRows)
        self._log_table.setSelectionMode(QTableView.SingleSelection)
        self._log_table.setAlternatingRowColors(True)
        self._log_table.verticalHeader().setVisible(False)
        self._log_table.setSortingEnabled(True)
        self._log_table.sortByColumn(0, Qt.AscendingOrder)

        header = self._log_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self._log_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._log_table)

        self._log_details = QTextEdit()
        self._log_details.setReadOnly(True)
        self._log_details.setMaximumHeight(200)
        splitter.addWidget(self._log_details)
        splitter.setSizes([500, 100])

    async def _async_subscribe_to_log_events(self) -> str:
        """
        Asynchronously subscribe to log events.

        Returns:
            Subscription ID
        """
        if not self._event_bus_manager:
            return ""

        return await self._event_bus_manager.subscribe(
            event_type=EventType.LOG_EVENT.value,
            callback=self._on_log_event,
            subscriber_id="logs_view"
        )

    async def _on_log_event(self, event: Any) -> None:
        """
        Handle log events from the event bus.

        Args:
            event: Log event object
        """
        log_entry = LogEntry.from_event_payload(event.payload)

        # Use signal to safely update UI from any thread
        self._async_signals.result_ready.emit({
            "task_id": "log_event",
            "result": log_entry
        })

    def _on_async_result(self, result_data: Dict[str, Any]) -> None:
        """
        Handle results from async operations.

        Args:
            result_data: Dictionary containing task ID and result
        """
        task_id = result_data.get("task_id", "")
        result = result_data.get("result")

        if task_id == "subscribe":
            self._log_subscription_id = result
        elif task_id == "log_event":
            log_entry = result
            self._log_model.add_log(log_entry)
            self._update_logger_combo()
            if self._auto_scroll_check.isChecked():
                self._log_table.scrollToBottom()

    def _on_async_error(self, error_msg: str, traceback_str: str) -> None:
        """
        Handle errors from async operations.

        Args:
            error_msg: Error message
            traceback_str: Traceback as a string
        """
        print(f"Error in logs view: {error_msg}\n{traceback_str}")

    def _update_logger_combo(self) -> None:
        """Update the logger filter combobox with current loggers."""
        current_text = self._logger_combo.currentText()

        self._logger_combo.blockSignals(True)
        self._logger_combo.clear()
        self._logger_combo.addItem("All Loggers", "")

        for logger in self._log_model.get_unique_loggers():
            self._logger_combo.addItem(logger, logger)

        index = self._logger_combo.findText(current_text)
        if index >= 0:
            self._logger_combo.setCurrentIndex(index)

        self._logger_combo.blockSignals(False)

    def _on_filter_text_changed(self, text: str) -> None:
        """
        Handle changes to the text filter.

        Args:
            text: New filter text
        """
        self._log_model.set_filter_text(text)

    def _on_level_filter_changed(self, index: int) -> None:
        """
        Handle changes to the level filter.

        Args:
            index: New selected index
        """
        level = self._level_combo.itemData(index)
        self._log_model.set_filter_level(level)

    def _on_logger_filter_changed(self, text: str) -> None:
        """
        Handle changes to the logger filter.

        Args:
            text: New logger filter text
        """
        if text == "All Loggers":
            self._log_model.set_filter_logger("")
        else:
            self._log_model.set_filter_logger(text)

    def _on_clear_clicked(self) -> None:
        """Handle clicking the clear logs button."""
        self._log_model.clear_logs()
        self._log_details.clear()

    def _on_selection_changed(self, selected: Any, deselected: Any) -> None:
        """
        Handle changes to the table selection.

        Args:
            selected: Newly selected items
            deselected: Newly deselected items
        """
        indexes = self._log_table.selectionModel().selectedIndexes()
        if not indexes:
            self._log_details.clear()
            return

        row = indexes[0].row()
        log_entry = self._log_model.data(self._log_model.index(row, 0), Qt.UserRole)
        if not log_entry:
            self._log_details.clear()
            return

        try:
            formatted_json = json.dumps(log_entry.raw_data, indent=2)
            self._log_details.setPlainText(formatted_json)
        except Exception:
            details = f"""
            Timestamp: {log_entry.timestamp}
            Level: {log_entry.level.value[1]}
            Logger: {log_entry.logger}
            Message: {log_entry.message}
            Event: {log_entry.event}
            Task: {log_entry.task}
            """
            self._log_details.setPlainText(details.strip())

    def _start_async_task(
            self,
            task_id: str,
            coroutine_func: Any,
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Start an asynchronous task.

        Args:
            task_id: Task identifier
            coroutine_func: Async function to run
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        # Cancel any existing task with same ID
        if task_id in self._running_tasks and not self._running_tasks[task_id].done():
            self._running_tasks[task_id].cancel()

        task = asyncio.create_task(self._execute_async_task(
            task_id, coroutine_func, *args, **kwargs
        ))
        self._running_tasks[task_id] = task

    async def _execute_async_task(
            self,
            task_id: str,
            coroutine_func: Any,
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Execute an asynchronous task and handle signals.

        Args:
            task_id: Task identifier
            coroutine_func: Async function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        try:
            result = await coroutine_func(*args, **kwargs)
            # Use QtCore.Qt.QueuedConnection for thread safety
            self._async_signals.result_ready.emit({
                "task_id": task_id,
                "result": result
            })
        except asyncio.CancelledError:
            # Task was cancelled, no need to emit signals
            pass
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            self._async_signals.error.emit(str(e), tb_str)
        finally:
            # Clean up the task reference
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    def showEvent(self, event: Any) -> None:
        """
        Handle widget show event.

        Args:
            event: Show event
        """
        super().showEvent(event)

    def hideEvent(self, event: Any) -> None:
        """
        Handle widget hide event.

        Args:
            event: Hide event
        """
        super().hideEvent(event)

    def closeEvent(self, event: Any) -> None:
        """
        Handle widget close event.

        Args:
            event: Close event
        """
        # Cancel all running tasks
        for task in list(self._running_tasks.values()):
            if not task.done():
                task.cancel()

        # Unsubscribe from event bus
        if self._event_bus_manager and self._log_subscription_id:
            self._start_async_task(
                "unsubscribe",
                self._event_bus_manager.unsubscribe,
                subscriber_id=self._log_subscription_id
            )

        super().closeEvent(event)