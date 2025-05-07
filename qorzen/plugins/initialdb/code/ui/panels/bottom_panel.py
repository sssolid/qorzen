# bottom_panel.py

from __future__ import annotations

"""
Bottom panel for the InitialDB application.

This module provides the bottom panel implementation, with tabs for logs,
console output, and other information displays.
"""

from typing import Dict, List, Optional, Type, cast

import structlog
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget, QTextEdit, QPlainTextEdit, QLabel,
    QHBoxLayout, QPushButton, QSplitter
)

from .panel_base import PanelBase, PanelContent

logger = structlog.get_logger(__name__)


class ConsoleContent(PanelContent):
    """Console output content for the bottom panel."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = self.layout()
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(1000)
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.console.setPlainText("Application console output will appear here.")
        self.console.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.console.setMinimumHeight(50)
        self.console.setMaximumHeight(200)
        layout.addWidget(self.console)

    def append_text(self, text: str) -> None:
        self.console.appendPlainText(text)


class LogContent(PanelContent):
    """Log output content for the bottom panel."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = self.layout()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_view.setPlainText("Application logs will appear here.")
        self.log_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.log_view.setMinimumHeight(50)
        self.log_view.setMaximumHeight(200)
        layout.addWidget(self.log_view)

    def append_log(self, text: str) -> None:
        self.log_view.append(text)


class BottomPanel(PanelBase):
    """Bottom panel with console, logs, and update status."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Information", parent)
        self._setup_contents()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setMinimumHeight(100)
        self.setMaximumHeight(300)
        self.setFeatures(self.features() & ~self.DockWidgetFeature.DockWidgetFloatable)
        for content in self._contents.values():
            content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def _setup_contents(self) -> None:
        self.console_content = ConsoleContent(self)
        self.add_content("console", self.console_content, button_text="Console", icon_name="console", tooltip="Console Output", activate=True)

        self.log_content = LogContent(self)
        self.add_content("log", self.log_content, button_text="Logs", icon_name="log-list", tooltip="Application Logs")

    def append_console(self, text: str) -> None:
        self.console_content.append_text(text)

    def append_log(self, text: str) -> None:
        self.log_content.append_log(text)
