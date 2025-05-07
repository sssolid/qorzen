from __future__ import annotations

"""
Bottom panel for the InitialDB application.

This module provides the bottom panel implementation, with tabs for logs,
console output, and other information displays.
"""

from typing import Dict, List, Optional, Type, cast

import structlog
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget, QTextEdit, QPlainTextEdit, QLabel,
    QHBoxLayout, QPushButton, QSplitter
)

from ...utils.update_manager import UpdateManager
from .panel_base import PanelBase, PanelContent

logger = structlog.get_logger(__name__)


class ConsoleContent(PanelContent):
    """Console output content for the bottom panel."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the console content.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = self.layout()

        # Console output
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(1000)  # Limit to prevent memory issues
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Add text with instructions
        self.console.setPlainText(
            "Application console output will appear here."
        )

        # Set size policy to allow shrinking
        self.console.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        # Set minimum and maximum height
        self.console.setMinimumHeight(50)
        self.console.setMaximumHeight(200)

        layout.addWidget(self.console)

    def append_text(self, text: str) -> None:
        """
        Append text to the console.

        Args:
            text: Text to append
        """
        self.console.appendPlainText(text)


class LogContent(PanelContent):
    """Log output content for the bottom panel."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the log content.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = self.layout()

        # Log output
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Add text with instructions
        self.log_view.setPlainText(
            "Application logs will appear here."
        )

        # Set size policy to allow shrinking
        self.log_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        # Set minimum and maximum height
        self.log_view.setMinimumHeight(50)
        self.log_view.setMaximumHeight(200)

        layout.addWidget(self.log_view)

    def append_log(self, text: str) -> None:
        """
        Append a log entry.

        Args:
            text: Log text to append
        """
        self.log_view.append(text)


class UpdateContent(PanelContent):
    """Update status content for the bottom panel."""

    def __init__(self, update_manager: UpdateManager, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the update content.

        Args:
            update_manager: The update manager instance
            parent: The parent widget
        """
        self.update_manager = update_manager
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = self.layout()

        # Update status
        status_layout = QHBoxLayout()

        self.status_label = QLabel("No updates available")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.check_button = QPushButton("Check for Updates")
        self.check_button.clicked.connect(
            lambda: self.update_manager.check_for_updates(force=True)
        )
        status_layout.addWidget(self.check_button)

        widget = QWidget()
        widget.setLayout(status_layout)

        # Set size policy to allow shrinking
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        widget.setMaximumHeight(100)  # Limit maximum height

        layout.addWidget(widget)


class BottomPanel(PanelBase):
    """Bottom panel with console, logs, and update status."""

    def __init__(self, update_manager: UpdateManager, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the bottom panel.

        Args:
            update_manager: The update manager instance
            parent: The parent widget
        """
        super().__init__("Information", parent)
        self.update_manager = update_manager
        self._setup_contents()

        # Critical: Set correct size policies to allow proper resizing
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Set reasonable minimum height and limit maximum height
        self.setMinimumHeight(100)
        self.setMaximumHeight(300)

        # Prevent panel from floating to reduce layout issues
        self.setFeatures(self.features() & ~self.DockWidgetFeature.DockWidgetFloatable)

        # Ensure all content widgets have proper size policies too
        for content in self._contents.values():
            content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def _setup_contents(self) -> None:
        """Set up the panel contents."""
        # Console content
        self.console_content = ConsoleContent(self)
        self.add_content(
            "console",
            self.console_content,
            button_text="Console",
            icon_name="console",
            tooltip="Console Output",
            activate=True
        )

        # Log content
        self.log_content = LogContent(self)
        self.add_content(
            "log",
            self.log_content,
            button_text="Logs",
            icon_name="log-list",
            tooltip="Application Logs"
        )

        # Update content
        self.update_content = UpdateContent(self.update_manager, self)
        self.add_content(
            "update",
            self.update_content,
            button_text="Updates",
            icon_name="update",
            tooltip="Update Status"
        )

    def append_console(self, text: str) -> None:
        """
        Append text to the console.

        Args:
            text: Text to append
        """
        self.console_content.append_text(text)

    def append_log(self, text: str) -> None:
        """
        Append a log entry.

        Args:
            text: Log text to append
        """
        self.log_content.append_log(text)