from __future__ import annotations

"""
Application Launcher plugin module.

This module provides the main plugin class for the Application Launcher, which allows
users to configure, launch, and monitor external applications with configurable arguments.
"""

import asyncio
import logging
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

from pydantic import BaseModel, Field, validator

from PySide6.QtCore import QDir, QProcess, QProcessEnvironment, Qt, Signal, Slot, QTimer, QUrl, QObject, QFileInfo
from PySide6.QtGui import QAction, QDesktopServices, QFont, QIcon, QColor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QMessageBox, QPushButton, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QToolButton, QVBoxLayout, QWidget, QScrollArea
)

from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.file_manager import FileManager
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_integration import UIIntegration
from qorzen.plugin_system.lifecycle import (
    get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
)
from qorzen.utils.exceptions import PluginError


# --- Data Models ---

class ArgumentType(str, Enum):
    """Type of command line argument."""

    STATIC = "static"
    FILE_INPUT = "file_input"
    FILE_OUTPUT = "file_output"
    DIRECTORY = "directory"
    TEXT_INPUT = "text_input"
    ENV_VAR = "environment_variable"


class ProcessStatus(str, Enum):
    """Status of the process execution."""

    NOT_STARTED = "not_started"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class ArgumentConfig:
    """Configuration for a command-line argument."""

    name: str
    arg_type: ArgumentType = ArgumentType.STATIC
    value: str = ""
    description: str = ""
    required: bool = False
    file_filter: str = ""  # For file inputs/outputs
    prefix: str = ""  # Command line prefix (e.g., '--input=')
    current_value: str = ""  # Value used in current/last execution


@dataclass
class ApplicationConfig:
    """Configuration for an external application."""

    id: str
    name: str
    executable_path: str
    working_directory: Optional[str] = None
    arguments: List[ArgumentConfig] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    show_console_output: bool = True
    category: str = "General"
    description: str = ""
    icon_path: Optional[str] = None
    output_patterns: List[str] = field(default_factory=list)  # Patterns to identify output files
    auto_open_output: bool = False


class ProcessOutput(BaseModel):
    """Model for process execution output."""

    status: ProcessStatus = ProcessStatus.NOT_STARTED
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    output_files: List[str] = Field(default_factory=list)
    command_line: str = ""


# --- UI Components ---

class ArgumentInputWidget(QWidget):
    """Widget for configuring a single command line argument."""

    valueChanged = Signal(str)

    def __init__(
            self,
            arg_config: ArgumentConfig,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the argument input widget.

        Args:
            arg_config: The configuration for this argument
            parent: Parent widget
        """
        super().__init__(parent)
        self.arg_config = arg_config
        self._value = arg_config.value

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        if arg_config.prefix:
            prefix_label = QLabel(arg_config.prefix)
            self._layout.addWidget(prefix_label)

        if arg_config.arg_type == ArgumentType.STATIC:
            self._input = QLineEdit(arg_config.value)
            self._input.setPlaceholderText("Static value")
            self._input.textChanged.connect(self._on_value_changed)
            self._layout.addWidget(self._input)

        elif arg_config.arg_type == ArgumentType.TEXT_INPUT:
            self._input = QLineEdit(arg_config.value)
            self._input.setPlaceholderText("Enter text...")
            self._input.textChanged.connect(self._on_value_changed)
            self._layout.addWidget(self._input)

        elif arg_config.arg_type == ArgumentType.FILE_INPUT:
            self._input = QLineEdit(arg_config.value)
            self._input.setPlaceholderText("Select input file...")
            self._input.textChanged.connect(self._on_value_changed)
            self._layout.addWidget(self._input)

            browse_btn = QPushButton("Browse...")
            browse_btn.clicked.connect(self._browse_input_file)
            self._layout.addWidget(browse_btn)

        elif arg_config.arg_type == ArgumentType.FILE_OUTPUT:
            self._input = QLineEdit(arg_config.value)
            self._input.setPlaceholderText("Select output file...")
            self._input.textChanged.connect(self._on_value_changed)
            self._layout.addWidget(self._input)

            browse_btn = QPushButton("Browse...")
            browse_btn.clicked.connect(self._browse_output_file)
            self._layout.addWidget(browse_btn)

        elif arg_config.arg_type == ArgumentType.DIRECTORY:
            self._input = QLineEdit(arg_config.value)
            self._input.setPlaceholderText("Select directory...")
            self._input.textChanged.connect(self._on_value_changed)
            self._layout.addWidget(self._input)

            browse_btn = QPushButton("Browse...")
            browse_btn.clicked.connect(self._browse_directory)
            self._layout.addWidget(browse_btn)

        elif arg_config.arg_type == ArgumentType.ENV_VAR:
            self._input = QLineEdit(arg_config.value)
            self._input.setPlaceholderText("Environment variable value")
            self._input.textChanged.connect(self._on_value_changed)
            self._layout.addWidget(self._input)

    def get_value(self) -> str:
        """Get the current argument value."""
        return self._value

    def _on_value_changed(self, value: str) -> None:
        """Handle value changes."""
        self._value = value
        self.valueChanged.emit(value)

    def _browse_input_file(self) -> None:
        """Open file dialog for input file selection."""
        file_filter = self.arg_config.file_filter or "All Files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", file_filter
        )
        if file_path:
            self._input.setText(file_path)

    def _browse_output_file(self) -> None:
        """Open file dialog for output file selection."""
        file_filter = self.arg_config.file_filter or "All Files (*.*)"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output File", "", file_filter
        )
        if file_path:
            self._input.setText(file_path)

    def _browse_directory(self) -> None:
        """Open directory dialog."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Directory", "", QFileDialog.ShowDirsOnly
        )
        if dir_path:
            self._input.setText(dir_path)


class ApplicationConfigDialog(QDialog):
    """Dialog for configuring an application."""

    def __init__(
            self,
            app_config: Optional[ApplicationConfig] = None,
            parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the application configuration dialog.

        Args:
            app_config: Existing application configuration to edit, or None for new
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Configure Application")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.app_config = app_config or ApplicationConfig(
            id=f"app_{os.urandom(4).hex()}",
            name="New Application",
            executable_path="",
        )

        self.argument_widgets: List[Tuple[ArgumentConfig, QWidget]] = []

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the dialog UI components."""
        layout = QVBoxLayout(self)

        # Basic info group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QVBoxLayout(basic_group)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(self.app_config.name)
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)

        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_edit = QLineEdit(self.app_config.category)
        category_layout.addWidget(self.category_edit)
        basic_layout.addLayout(category_layout)

        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.desc_edit = QLineEdit(self.app_config.description)
        desc_layout.addWidget(self.desc_edit)
        basic_layout.addLayout(desc_layout)

        exe_layout = QHBoxLayout()
        exe_layout.addWidget(QLabel("Executable:"))
        self.exe_edit = QLineEdit(self.app_config.executable_path)
        exe_layout.addWidget(self.exe_edit)
        exe_browse = QPushButton("Browse...")
        exe_browse.clicked.connect(self._browse_executable)
        exe_layout.addWidget(exe_browse)
        basic_layout.addLayout(exe_layout)

        working_dir_layout = QHBoxLayout()
        working_dir_layout.addWidget(QLabel("Working Directory:"))
        self.working_dir_edit = QLineEdit(self.app_config.working_directory or "")
        working_dir_layout.addWidget(self.working_dir_edit)
        working_dir_browse = QPushButton("Browse...")
        working_dir_browse.clicked.connect(self._browse_working_dir)
        working_dir_layout.addWidget(working_dir_browse)
        basic_layout.addLayout(working_dir_layout)

        icon_layout = QHBoxLayout()
        icon_layout.addWidget(QLabel("Icon:"))
        self.icon_edit = QLineEdit(self.app_config.icon_path or "")
        icon_layout.addWidget(self.icon_edit)
        icon_browse = QPushButton("Browse...")
        icon_browse.clicked.connect(self._browse_icon)
        icon_layout.addWidget(icon_browse)
        basic_layout.addLayout(icon_layout)

        layout.addWidget(basic_group)

        # Arguments group
        args_group = QGroupBox("Command Line Arguments")
        args_layout = QVBoxLayout(args_group)

        self.args_table = QTableWidget(0, 5)
        self.args_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Required", "Description", "Value"]
        )
        self.args_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.args_table.verticalHeader().setVisible(False)
        self.args_table.setSelectionBehavior(QTableWidget.SelectRows)

        args_layout.addWidget(self.args_table)

        args_buttons_layout = QHBoxLayout()
        add_arg_btn = QPushButton("Add Argument")
        add_arg_btn.clicked.connect(self._add_argument)
        args_buttons_layout.addWidget(add_arg_btn)

        edit_arg_btn = QPushButton("Edit Argument")
        edit_arg_btn.clicked.connect(self._edit_argument)
        args_buttons_layout.addWidget(edit_arg_btn)

        remove_arg_btn = QPushButton("Remove Argument")
        remove_arg_btn.clicked.connect(self._remove_argument)
        args_buttons_layout.addWidget(remove_arg_btn)

        args_layout.addLayout(args_buttons_layout)
        layout.addWidget(args_group)

        # Environment variables group
        env_group = QGroupBox("Environment Variables")
        env_layout = QVBoxLayout(env_group)

        self.env_table = QTableWidget(0, 2)
        self.env_table.setHorizontalHeaderLabels(["Name", "Value"])
        self.env_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.env_table.verticalHeader().setVisible(False)
        self.env_table.setSelectionBehavior(QTableWidget.SelectRows)

        env_layout.addWidget(self.env_table)

        env_buttons_layout = QHBoxLayout()
        add_env_btn = QPushButton("Add Variable")
        add_env_btn.clicked.connect(self._add_env_var)
        env_buttons_layout.addWidget(add_env_btn)

        edit_env_btn = QPushButton("Edit Variable")
        edit_env_btn.clicked.connect(self._edit_env_var)
        env_buttons_layout.addWidget(edit_env_btn)

        remove_env_btn = QPushButton("Remove Variable")
        remove_env_btn.clicked.connect(self._remove_env_var)
        env_buttons_layout.addWidget(remove_env_btn)

        env_layout.addLayout(env_buttons_layout)
        layout.addWidget(env_group)

        # Output files group
        output_group = QGroupBox("Output Files")
        output_layout = QVBoxLayout(output_group)

        self.output_patterns_table = QTableWidget(0, 1)
        self.output_patterns_table.setHorizontalHeaderLabels(["File Pattern"])
        self.output_patterns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.output_patterns_table.verticalHeader().setVisible(False)

        output_layout.addWidget(self.output_patterns_table)

        output_buttons_layout = QHBoxLayout()
        add_pattern_btn = QPushButton("Add Pattern")
        add_pattern_btn.clicked.connect(self._add_output_pattern)
        output_buttons_layout.addWidget(add_pattern_btn)

        remove_pattern_btn = QPushButton("Remove Pattern")
        remove_pattern_btn.clicked.connect(self._remove_output_pattern)
        output_buttons_layout.addWidget(remove_pattern_btn)

        output_layout.addLayout(output_buttons_layout)

        self.auto_open_check = QCheckBox("Automatically open output files")
        self.auto_open_check.setChecked(self.app_config.auto_open_output)
        output_layout.addWidget(self.auto_open_check)

        layout.addWidget(output_group)

        # Dialog buttons
        buttons_layout = QHBoxLayout()
        self.console_output_check = QCheckBox("Show console output")
        self.console_output_check.setChecked(self.app_config.show_console_output)
        buttons_layout.addWidget(self.console_output_check)

        buttons_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

        # Load existing configuration
        self._load_config()

    def _load_config(self) -> None:
        """Load existing configuration into the UI."""
        # Load arguments
        self.args_table.setRowCount(len(self.app_config.arguments))
        for i, arg in enumerate(self.app_config.arguments):
            self.args_table.setItem(i, 0, QTableWidgetItem(arg.name))
            self.args_table.setItem(i, 1, QTableWidgetItem(arg.arg_type))
            self.args_table.setItem(i, 2, QTableWidgetItem("Yes" if arg.required else "No"))
            self.args_table.setItem(i, 3, QTableWidgetItem(arg.description))
            self.args_table.setItem(i, 4, QTableWidgetItem(arg.value))

        # Load environment variables
        self.env_table.setRowCount(len(self.app_config.environment_variables))
        for i, (name, value) in enumerate(self.app_config.environment_variables.items()):
            self.env_table.setItem(i, 0, QTableWidgetItem(name))
            self.env_table.setItem(i, 1, QTableWidgetItem(value))

        # Load output patterns
        self.output_patterns_table.setRowCount(len(self.app_config.output_patterns))
        for i, pattern in enumerate(self.app_config.output_patterns):
            self.output_patterns_table.setItem(i, 0, QTableWidgetItem(pattern))

    def get_config(self) -> ApplicationConfig:
        """Get the updated application configuration from the dialog."""
        # Update basic info
        self.app_config.name = self.name_edit.text()
        self.app_config.category = self.category_edit.text()
        self.app_config.description = self.desc_edit.text()
        self.app_config.executable_path = self.exe_edit.text()
        self.app_config.working_directory = self.working_dir_edit.text() or None
        self.app_config.icon_path = self.icon_edit.text() or None
        self.app_config.show_console_output = self.console_output_check.isChecked()
        self.app_config.auto_open_output = self.auto_open_check.isChecked()

        # Store original arguments and build a lookup dict for them
        original_arguments = {arg.name: arg for arg in self.app_config.arguments}

        # Update arguments
        updated_arguments = []
        for row in range(self.args_table.rowCount()):
            name = self.args_table.item(row, 0).text()
            arg_type = ArgumentType(self.args_table.item(row, 1).text())
            required = self.args_table.item(row, 2).text() == "Yes"
            description = self.args_table.item(row, 3).text()
            value = self.args_table.item(row, 4).text()

            # Find the original argument to preserve prefix and file_filter
            original_arg = original_arguments.get(name)

            if original_arg:
                # Create a new argument preserving the original prefix and file_filter
                arg = ArgumentConfig(
                    name=name,
                    arg_type=arg_type,
                    value=value,
                    description=description,
                    required=required,
                    file_filter=original_arg.file_filter,
                    prefix=original_arg.prefix
                )
            else:
                # New argument with default empty prefix and file_filter
                arg = ArgumentConfig(
                    name=name,
                    arg_type=arg_type,
                    value=value,
                    description=description,
                    required=required,
                    file_filter="",
                    prefix=""
                )

            updated_arguments.append(arg)

        self.app_config.arguments = updated_arguments

        # Update environment variables
        self.app_config.environment_variables = {}
        for row in range(self.env_table.rowCount()):
            name = self.env_table.item(row, 0).text()
            value = self.env_table.item(row, 1).text()
            self.app_config.environment_variables[name] = value

        # Update output patterns
        self.app_config.output_patterns = []
        for row in range(self.output_patterns_table.rowCount()):
            pattern = self.output_patterns_table.item(row, 0).text()
            self.app_config.output_patterns.append(pattern)

        return self.app_config

    def _browse_executable(self) -> None:
        """Open file dialog for executable selection."""
        file_filter = "Executable Files (*.exe);;All Files (*.*)" if sys.platform == "win32" else "All Files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Executable", "", file_filter
        )
        if file_path:
            self.exe_edit.setText(file_path)

    def _browse_working_dir(self) -> None:
        """Open directory dialog for working directory selection."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Working Directory", "", QFileDialog.ShowDirsOnly
        )
        if dir_path:
            self.working_dir_edit.setText(dir_path)

    def _browse_icon(self) -> None:
        """Open file dialog for icon selection."""
        file_filter = "Image Files (*.png *.jpg *.jpeg *.ico);;All Files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon", "", file_filter
        )
        if file_path:
            self.icon_edit.setText(file_path)

    def _add_argument(self) -> None:
        """Add a new argument row."""
        row = self.args_table.rowCount()
        self.args_table.insertRow(row)

        self.args_table.setItem(row, 0, QTableWidgetItem(f"arg{row + 1}"))
        self.args_table.setItem(row, 1, QTableWidgetItem(ArgumentType.STATIC))
        self.args_table.setItem(row, 2, QTableWidgetItem("No"))
        self.args_table.setItem(row, 3, QTableWidgetItem(""))
        self.args_table.setItem(row, 4, QTableWidgetItem(""))

    def _edit_argument(self) -> None:
        """Edit the selected argument."""
        rows = self.args_table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()

        # Get current values
        name = self.args_table.item(row, 0).text()
        arg_type = ArgumentType(self.args_table.item(row, 1).text())
        required = self.args_table.item(row, 2).text() == "Yes"
        description = self.args_table.item(row, 3).text()
        value = self.args_table.item(row, 4).text()

        # Find the original argument to get file_filter and prefix
        original_arg = None
        for arg in self.app_config.arguments:
            if arg.name == name:
                original_arg = arg
                break

        file_filter = original_arg.file_filter if original_arg else ""
        prefix = original_arg.prefix if original_arg else ""

        # Create and show dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Argument")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        form_layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = QLineEdit(name)
        name_layout.addWidget(name_edit)
        form_layout.addLayout(name_layout)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        type_combo = QComboBox()
        for arg_type_value in ArgumentType:
            type_combo.addItem(arg_type_value.value)
        type_combo.setCurrentText(arg_type.value)
        type_layout.addWidget(type_combo)
        form_layout.addLayout(type_layout)

        req_layout = QHBoxLayout()
        req_layout.addWidget(QLabel("Required:"))
        req_check = QCheckBox()
        req_check.setChecked(required)
        req_layout.addWidget(req_check)
        form_layout.addLayout(req_layout)

        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        desc_edit = QLineEdit(description)
        desc_layout.addWidget(desc_edit)
        form_layout.addLayout(desc_layout)

        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Default Value:"))
        value_edit = QLineEdit(value)
        value_layout.addWidget(value_edit)
        form_layout.addLayout(value_layout)

        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Prefix:"))
        prefix_edit = QLineEdit(prefix)
        prefix_edit.setPlaceholderText("e.g., --input= or -i ")
        prefix_layout.addWidget(prefix_edit)
        form_layout.addLayout(prefix_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("File Filter:"))
        filter_edit = QLineEdit(file_filter)
        filter_edit.setPlaceholderText("e.g., Images (*.png *.jpg)")
        filter_layout.addWidget(filter_edit)
        form_layout.addLayout(filter_layout)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        buttons_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

        if dialog.exec() == QDialog.Accepted:
            # Update the table
            self.args_table.setItem(row, 0, QTableWidgetItem(name_edit.text()))
            self.args_table.setItem(row, 1, QTableWidgetItem(type_combo.currentText()))
            self.args_table.setItem(row, 2, QTableWidgetItem("Yes" if req_check.isChecked() else "No"))
            self.args_table.setItem(row, 3, QTableWidgetItem(desc_edit.text()))
            self.args_table.setItem(row, 4, QTableWidgetItem(value_edit.text()))

            # IMPORTANT: Find the argument in our app_config and update it directly
            # This ensures prefix and file_filter are preserved during serialization
            for i, arg in enumerate(self.app_config.arguments):
                if arg.name == name:
                    # Update the existing argument
                    arg.name = name_edit.text()
                    arg.arg_type = ArgumentType(type_combo.currentText())
                    arg.required = req_check.isChecked()
                    arg.description = desc_edit.text()
                    arg.value = value_edit.text()
                    arg.file_filter = filter_edit.text()
                    arg.prefix = prefix_edit.text()

                    # Update the app_config's arguments list directly
                    self.app_config.arguments[i] = arg
                    break
            else:
                # If we didn't find it (should never happen), add a new one
                self.app_config.arguments.append(
                    ArgumentConfig(
                        name=name_edit.text(),
                        arg_type=ArgumentType(type_combo.currentText()),
                        value=value_edit.text(),
                        description=desc_edit.text(),
                        required=req_check.isChecked(),
                        file_filter=filter_edit.text(),
                        prefix=prefix_edit.text()
                    )
                )

    def _remove_argument(self) -> None:
        """Remove the selected argument."""
        rows = self.args_table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()
        self.args_table.removeRow(row)

    def _add_env_var(self) -> None:
        """Add a new environment variable row."""
        row = self.env_table.rowCount()
        self.env_table.insertRow(row)

        self.env_table.setItem(row, 0, QTableWidgetItem("ENV_VAR"))
        self.env_table.setItem(row, 1, QTableWidgetItem(""))

    def _edit_env_var(self) -> None:
        """Edit the selected environment variable."""
        rows = self.env_table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Environment Variable")

        layout = QVBoxLayout(dialog)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = QLineEdit(self.env_table.item(row, 0).text())
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)

        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        value_edit = QLineEdit(self.env_table.item(row, 1).text())
        value_layout.addWidget(value_edit)
        layout.addLayout(value_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        buttons_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

        if dialog.exec() == QDialog.Accepted:
            self.env_table.setItem(row, 0, QTableWidgetItem(name_edit.text()))
            self.env_table.setItem(row, 1, QTableWidgetItem(value_edit.text()))

    def _remove_env_var(self) -> None:
        """Remove the selected environment variable."""
        rows = self.env_table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()
        self.env_table.removeRow(row)

    def _add_output_pattern(self) -> None:
        """Add a new output pattern row."""
        row = self.output_patterns_table.rowCount()
        self.output_patterns_table.insertRow(row)

        self.output_patterns_table.setItem(row, 0, QTableWidgetItem("*.txt"))

    def _remove_output_pattern(self) -> None:
        """Remove the selected output pattern."""
        rows = self.output_patterns_table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()
        self.output_patterns_table.removeRow(row)


class ConsoleOutputWidget(QWidget):
    """Widget for displaying process console output."""

    def __init__(
            self,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the console output widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._layout = QVBoxLayout(self)

        # Status bar
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Not Started")
        self.status_layout.addWidget(self.status_label)

        self.runtime_label = QLabel("Runtime: 0s")
        self.status_layout.addWidget(self.runtime_label)

        self.status_layout.addStretch()

        self.exit_code_label = QLabel("")
        self.status_layout.addWidget(self.exit_code_label)

        self._layout.addLayout(self.status_layout)

        # Command line
        command_layout = QHBoxLayout()
        command_layout.addWidget(QLabel("Command:"))

        # Use a scroll area for the command to prevent window resizing
        command_scroll = QScrollArea()
        command_scroll.setWidgetResizable(True)
        command_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        command_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        command_scroll.setFrameShape(QFrame.NoFrame)
        command_scroll.setMaximumHeight(60)

        command_container = QWidget()
        command_container_layout = QHBoxLayout(command_container)
        command_container_layout.setContentsMargins(0, 0, 0, 0)

        self.command_label = QLabel("")
        self.command_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.command_label.setWordWrap(True)
        command_container_layout.addWidget(self.command_label)

        command_scroll.setWidget(command_container)
        command_layout.addWidget(command_scroll)

        self._layout.addLayout(command_layout)

        # Output tabs
        self.output_tabs = QTabWidget()

        self.stdout_text = QTextEdit()
        self.stdout_text.setReadOnly(True)
        self.stdout_text.setFont(QFont("Courier New", 10))
        self.output_tabs.addTab(self.stdout_text, "Standard Output")

        self.stderr_text = QTextEdit()
        self.stderr_text.setReadOnly(True)
        self.stderr_text.setFont(QFont("Courier New", 10))
        self.output_tabs.addTab(self.stderr_text, "Standard Error")

        self._layout.addWidget(self.output_tabs)

        # Timer for updating runtime
        self._start_time = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_runtime)
        self._timer.setInterval(1000)  # Update every second

        # Clear console when starting new process
        self.clear()

    def start_process(self, command_line: str) -> None:
        """
        Start displaying output for a new process.

        Args:
            command_line: The command line being executed
        """
        self.clear()
        self.command_label.setText(command_line)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("color: blue;")

        import time
        self._start_time = time.time()
        self._timer.start()

    def append_stdout(self, text: str) -> None:
        """
        Append text to stdout display.

        Args:
            text: Text to append
        """
        self.stdout_text.append(text)
        # Scroll to bottom
        self.stdout_text.verticalScrollBar().setValue(
            self.stdout_text.verticalScrollBar().maximum()
        )

    def append_stderr(self, text: str) -> None:
        """
        Append text to stderr display.

        Args:
            text: Text to append
        """
        self.stderr_text.append(text)
        # Scroll to bottom
        self.stderr_text.verticalScrollBar().setValue(
            self.stderr_text.verticalScrollBar().maximum()
        )

        # Switch to stderr tab if there's error output
        if text.strip():
            self.output_tabs.setCurrentWidget(self.stderr_text)

    def process_finished(self, exit_code: int) -> None:
        """
        Update UI when process finishes.

        Args:
            exit_code: Process exit code
        """
        self._timer.stop()

        self.exit_code_label.setText(f"Exit Code: {exit_code}")

        if exit_code == 0:
            self.status_label.setText("Status: Completed Successfully")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Status: Failed")
            self.status_label.setStyleSheet("color: red;")

    def process_terminated(self) -> None:
        """Update UI when process is terminated."""
        self._timer.stop()

        self.status_label.setText("Status: Terminated")
        self.status_label.setStyleSheet("color: orange;")

    def clear(self) -> None:
        """Clear all output and reset display."""
        self.stdout_text.clear()
        self.stderr_text.clear()
        self.command_label.setText("")
        self.status_label.setText("Status: Not Started")
        self.status_label.setStyleSheet("")
        self.runtime_label.setText("Runtime: 0s")
        self.exit_code_label.setText("")
        self._timer.stop()

    def _update_runtime(self) -> None:
        """Update the runtime display."""
        import time
        runtime = time.time() - self._start_time
        self.runtime_label.setText(f"Runtime: {int(runtime)}s")


class OutputFilesWidget(QWidget):
    """Widget for displaying and interacting with output files."""

    fileOpened = Signal(str)

    def _init_ui(self) -> None:
        """Initialize the widget UI components."""
        self._layout = QVBoxLayout(self)

        # Add output directory section
        self._output_dirs_layout = QHBoxLayout()
        self._output_dirs_layout.addWidget(QLabel("Output Directories:"))
        self._output_dirs_combo = QComboBox()
        self._output_dirs_layout.addWidget(self._output_dirs_combo)

        self._open_dir_btn = QPushButton("Open Directory")
        self._open_dir_btn.clicked.connect(self._open_selected_directory)
        self._output_dirs_layout.addWidget(self._open_dir_btn)

        self._layout.addLayout(self._output_dirs_layout)

        # Add instructions label
        self._instructions_label = QLabel(
            "Note: Output directories are automatically detected from output file locations and displayed in the dropdown above.")
        self._instructions_label.setWordWrap(True)
        self._instructions_label.setStyleSheet("color: #666666; font-style: italic;")
        self._layout.addWidget(self._instructions_label)

        # Files table
        self.files_table = QTableWidget(0, 5)
        self.files_table.setHorizontalHeaderLabels(
            ["Filename", "Size", "Modified", "Path", "Actions"]
        )
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.files_table.verticalHeader().setVisible(False)
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)

        self._layout.addWidget(self.files_table)

        # No files message
        self.no_files_label = QLabel("No output files detected.")
        self.no_files_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.no_files_label)

        # Initially hide the table until we have files
        self.files_table.setVisible(False)
        self._output_dirs_combo.setVisible(False)
        self._open_dir_btn.setVisible(False)
        self._instructions_label.setVisible(False)

    def set_files(self, file_paths: List[str]) -> None:
        """
        Update the files display with the given paths.

        Args:
            file_paths: List of file paths to display
        """
        self.files_table.setRowCount(0)

        if not file_paths:
            self.no_files_label.setVisible(True)
            self.files_table.setVisible(False)
            self._output_dirs_combo.setVisible(False)
            self._open_dir_btn.setVisible(False)
            self._instructions_label.setVisible(False)
            return

        self.no_files_label.setVisible(False)
        self.files_table.setVisible(True)

        # Collect unique directories
        directories = set()
        for file_path in file_paths:
            directory = os.path.dirname(file_path)
            directories.add(directory)

        # Update directories combo
        self._output_dirs_combo.clear()
        for directory in sorted(directories):
            self._output_dirs_combo.addItem(directory)

        # Show directory controls if we have directories
        self._output_dirs_combo.setVisible(bool(directories))
        self._open_dir_btn.setVisible(bool(directories))
        self._instructions_label.setVisible(True)

        # Add files to table
        for file_path in file_paths:
            self._add_file(file_path)

    def _add_file(self, file_path: str) -> None:
        """
        Add a file to the table.

        Args:
            file_path: Path to the file
        """
        file_info = QFileInfo(file_path)
        if not file_info.exists():
            return

        row = self.files_table.rowCount()
        self.files_table.insertRow(row)

        # Filename
        filename_item = QTableWidgetItem(file_info.fileName())
        filename_item.setData(Qt.UserRole, file_path)
        self.files_table.setItem(row, 0, filename_item)

        # Size
        size_bytes = file_info.size()
        size_text = self._format_file_size(size_bytes)
        self.files_table.setItem(row, 1, QTableWidgetItem(size_text))

        # Modified date
        modified_date = file_info.lastModified().toString("yyyy-MM-dd HH:mm:ss")
        self.files_table.setItem(row, 2, QTableWidgetItem(modified_date))

        # Path
        path_item = QTableWidgetItem(os.path.dirname(file_path))
        path_item.setToolTip(file_path)
        self.files_table.setItem(row, 3, path_item)

        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 2, 4, 2)

        # Create a menu button for open options
        open_menu_btn = QPushButton("Open with...")
        open_menu = QMenu(open_menu_btn)

        # Default action
        default_action = QAction("Default Application", open_menu)
        default_action.triggered.connect(lambda: self._open_file(file_path))
        open_menu.addAction(default_action)

        # Check file type and add specific options
        file_ext = file_info.suffix().lower()

        # Text-based files
        if file_ext in ('txt', 'csv', 'json', 'xml', 'log', 'py', 'js', 'html', 'css', 'md'):
            text_action = QAction("Text Editor", open_menu)
            text_action.triggered.connect(lambda: self._open_file_with(file_path, 'text'))
            open_menu.addAction(text_action)

        # Image files
        if file_ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg'):
            image_action = QAction("Image Viewer", open_menu)
            image_action.triggered.connect(lambda: self._open_file_with(file_path, 'image'))
            open_menu.addAction(image_action)

        # Media files
        if file_ext in ('mp3', 'wav', 'ogg', 'mp4', 'avi', 'mkv', 'mov'):
            media_action = QAction("Media Player", open_menu)
            media_action.triggered.connect(lambda: self._open_file_with(file_path, 'media'))
            open_menu.addAction(media_action)

        open_menu_btn.setMenu(open_menu)
        actions_layout.addWidget(open_menu_btn)

        show_btn = QPushButton("Show in Folder")
        show_btn.clicked.connect(lambda: self._show_in_folder(file_path))
        actions_layout.addWidget(show_btn)

        self.files_table.setCellWidget(row, 4, actions_widget)

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable form.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _open_file(self, file_path: str) -> None:
        """
        Open the file using the system's default application.

        Args:
            file_path: Path to the file
        """
        url = QUrl.fromLocalFile(file_path)
        if QDesktopServices.openUrl(url):
            self.fileOpened.emit(file_path)
        else:
            QMessageBox.warning(
                self,
                "Open Failed",
                f"Failed to open file: {file_path}"
            )

    def _open_file_with(self, file_path: str, file_type: str) -> None:
        """
        Open the file with a specific application type.

        Args:
            file_path: Path to the file
            file_type: Type of application to use ('text', 'image', 'media', etc.)
        """
        # For platform-specific implementations of opening with specific apps
        import platform
        system = platform.system()

        try:
            if system == "Windows":
                if file_type == "text":
                    # Try Notepad
                    subprocess.Popen(["notepad.exe", file_path])
                elif file_type == "image":
                    # Try Paint
                    subprocess.Popen(["mspaint.exe", file_path])
                elif file_type == "media":
                    # Try Windows Media Player
                    subprocess.Popen(["wmplayer.exe", file_path])
                else:
                    # Default fallback
                    self._open_file(file_path)

            elif system == "Darwin":  # macOS
                if file_type == "text":
                    # Try TextEdit
                    subprocess.Popen(["open", "-a", "TextEdit", file_path])
                elif file_type == "image":
                    # Try Preview
                    subprocess.Popen(["open", "-a", "Preview", file_path])
                elif file_type == "media":
                    # Try QuickTime
                    subprocess.Popen(["open", "-a", "QuickTime Player", file_path])
                else:
                    # Default fallback
                    self._open_file(file_path)

            else:  # Linux and others
                if file_type == "text":
                    # Try common text editors
                    for editor in ["gedit", "kate", "kwrite", "leafpad"]:
                        try:
                            subprocess.Popen([editor, file_path])
                            break
                        except FileNotFoundError:
                            continue
                    else:
                        self._open_file(file_path)
                elif file_type == "image":
                    # Try common image viewers
                    for viewer in ["eog", "gwenview", "gthumb"]:
                        try:
                            subprocess.Popen([viewer, file_path])
                            break
                        except FileNotFoundError:
                            continue
                    else:
                        self._open_file(file_path)
                elif file_type == "media":
                    # Try common media players
                    for player in ["vlc", "totem", "smplayer"]:
                        try:
                            subprocess.Popen([player, file_path])
                            break
                        except FileNotFoundError:
                            continue
                    else:
                        self._open_file(file_path)
                else:
                    # Default fallback
                    self._open_file(file_path)

            self.fileOpened.emit(file_path)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Open Failed",
                f"Failed to open file with specified application: {str(e)}"
            )
            # Try fallback to default
            self._open_file(file_path)

    def _show_in_folder(self, file_path: str) -> None:
        """
        Show the file in its folder using the system's file manager.

        Args:
            file_path: Path to the file
        """
        # Get the directory containing the file
        directory = os.path.dirname(file_path)
        url = QUrl.fromLocalFile(directory)
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(
                self,
                "Show in Folder Failed",
                f"Failed to open folder: {directory}"
            )

    def _open_selected_directory(self) -> None:
        """Open the currently selected directory in the combo box."""
        directory = self._output_dirs_combo.currentText()
        if directory:
            url = QUrl.fromLocalFile(directory)
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(
                    self,
                    "Open Directory Failed",
                    f"Failed to open directory: {directory}"
                )


class ApplicationRunner(QObject):
    """Handles running external applications and capturing their output."""

    processStarted = Signal()
    processFinished = Signal(ProcessOutput)
    processError = Signal(str)
    stdoutReceived = Signal(str)
    stderrReceived = Signal(str)
    outputFilesDetected = Signal(list)

    def __init__(
            self,
            concurrency_manager: ConcurrencyManager,
            file_manager: FileManager,
            parent: Optional[QObject] = None
    ) -> None:
        """
        Initialize the application runner.

        Args:
            concurrency_manager: The concurrency manager for running async tasks
            file_manager: The file manager for handling files
            parent: Parent QObject
        """
        super().__init__(parent)
        self._concurrency_manager = concurrency_manager
        self._file_manager = file_manager
        self._current_process: Optional[QProcess] = None
        self._output = ProcessOutput()
        self._working_dir: Optional[str] = None
        self._output_patterns: List[str] = []
        self._current_process_args: List[ArgumentConfig] = []

    def run_application(
            self,
            app_config: ApplicationConfig,
            arg_values: Dict[str, str]
    ) -> None:
        """
        Run an application with the given configuration and arguments.

        Args:
            app_config: The application configuration
            arg_values: Dictionary of argument values
        """
        if self._current_process and self._current_process.state() == QProcess.Running:
            self.processError.emit("Another process is already running.")
            return

        executable = app_config.executable_path
        if not os.path.exists(executable):
            self.processError.emit(f"Executable not found: {executable}")
            return

        # Create a new process
        self._current_process = QProcess(self)
        self._current_process.readyReadStandardOutput.connect(self._read_stdout)
        self._current_process.readyReadStandardError.connect(self._read_stderr)
        self._current_process.finished.connect(self._process_finished)
        self._current_process.errorOccurred.connect(self._process_error)

        # Set working directory
        self._working_dir = app_config.working_directory or os.path.dirname(executable)
        if self._working_dir:
            self._current_process.setWorkingDirectory(self._working_dir)

        # Set output patterns
        self._output_patterns = app_config.output_patterns

        # Set environment
        if app_config.environment_variables:
            process_env = QProcessEnvironment.systemEnvironment()
            for name, value in app_config.environment_variables.items():
                process_env.insert(name, value)
            self._current_process.setProcessEnvironment(process_env)

        # Store current argument values
        self._current_process_args = []
        for arg_config in app_config.arguments:
            # Create a copy to avoid modifying the original
            arg_copy = ArgumentConfig(
                name=arg_config.name,
                arg_type=arg_config.arg_type,
                value=arg_config.value,
                description=arg_config.description,
                required=arg_config.required,
                file_filter=arg_config.file_filter,
                prefix=arg_config.prefix
            )
            # Add the current value
            arg_copy.current_value = arg_values.get(arg_config.name, arg_config.value)
            self._current_process_args.append(arg_copy)

        # Build arguments
        args = []
        cmd_display_args = []  # For display in the command line
        for arg_config in app_config.arguments:
            value = arg_values.get(arg_config.name, arg_config.value)
            if not value and arg_config.required:
                self.processError.emit(f"Required argument '{arg_config.name}' is missing.")
                return

            if value:  # Only add non-empty arguments
                # Handle prefix correctly
                if arg_config.prefix:
                    # For command line display
                    cmd_display_args.append(f"{arg_config.prefix}{value}")

                    # Check if prefix should be a separate argument or joined
                    if arg_config.prefix.endswith("=") or arg_config.prefix.endswith(":"):
                        # Joined prefix like "--input="
                        args.append(f"{arg_config.prefix}{value}")
                    else:
                        # Separate prefix like "-i "
                        prefix = arg_config.prefix.strip()
                        args.append(prefix)
                        args.append(value)
                else:
                    args.append(value)
                    cmd_display_args.append(value)

        # Build command line for display
        cmd_args = " ".join(shlex.quote(arg) for arg in cmd_display_args)
        command_line = f"{shlex.quote(executable)} {cmd_args}"

        # Initialize output
        import time
        self._output = ProcessOutput(
            status=ProcessStatus.RUNNING,
            stdout="",
            stderr="",
            start_time=time.time(),
            command_line=command_line,
        )

        # Start the process
        self._current_process.start(executable, args)
        self.processStarted.emit()

        # Start monitoring for output files
        timer = QTimer(self)
        timer.timeout.connect(lambda: self._check_for_output_files(app_config))
        timer.start(2000)  # Check every 2 seconds

    def terminate_process(self) -> None:
        """Terminate the current process if running."""
        if self._current_process and self._current_process.state() == QProcess.Running:
            self._current_process.terminate()

            # Give it some time to terminate gracefully
            if not self._current_process.waitForFinished(3000):
                self._current_process.kill()

    def _read_stdout(self) -> None:
        """Read and process stdout data from the process."""
        if not self._current_process:
            return

        data = self._current_process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self._output.stdout += text
        self.stdoutReceived.emit(text)

    def _read_stderr(self) -> None:
        """Read and process stderr data from the process."""
        if not self._current_process:
            return

        data = self._current_process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="replace")
        self._output.stderr += text
        self.stderrReceived.emit(text)

    def _process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """
        Handle process completion.

        Args:
            exit_code: The process exit code
            exit_status: The exit status (normal or crash)
        """
        import time
        self._output.end_time = time.time()
        self._output.exit_code = exit_code

        if exit_status == QProcess.NormalExit:
            self._output.status = ProcessStatus.FINISHED if exit_code == 0 else ProcessStatus.FAILED
        else:
            self._output.status = ProcessStatus.FAILED

        # Final check for output files
        self._find_output_files()

        self.processFinished.emit(self._output)

    def _process_error(self, error: QProcess.ProcessError) -> None:
        """
        Handle process errors.

        Args:
            error: The process error
        """
        error_messages = {
            QProcess.FailedToStart: "Failed to start process. Make sure the executable exists and you have permission to run it.",
            QProcess.Crashed: "Process crashed.",
            QProcess.Timedout: "Process timed out.",
            QProcess.WriteError: "Error writing to process.",
            QProcess.ReadError: "Error reading from process.",
            QProcess.UnknownError: "Unknown process error."
        }

        self.processError.emit(error_messages.get(error, "Process error occurred."))

        if error == QProcess.Crashed:
            import time
            self._output.end_time = time.time()
            self._output.status = ProcessStatus.FAILED
            self.processFinished.emit(self._output)

    def _check_for_output_files(self, app_config: ApplicationConfig) -> None:
        """
        Check for output files produced by the application.

        Args:
            app_config: The application configuration with output patterns
        """
        if not self._current_process or self._current_process.state() != QProcess.Running:
            return

        self._find_output_files()

    def _find_output_files(self) -> None:
        """Find output files matching the configured patterns."""
        if not self._working_dir or not self._output_patterns:
            return

        import glob
        import os

        output_files = []
        for pattern in self._output_patterns:
            # If pattern is absolute path, use it directly
            if os.path.isabs(pattern):
                matching_files = glob.glob(pattern)
            else:
                # Otherwise look in working directory
                matching_files = glob.glob(os.path.join(self._working_dir, pattern))

            output_files.extend(matching_files)

        # Filter for existing files and sort
        output_files = [f for f in output_files if os.path.isfile(f)]
        output_files.sort()

        if output_files:
            self._output.output_files = output_files
            self.outputFilesDetected.emit(output_files)


class ApplicationCard(QWidget):
    """Card widget displaying an application that can be launched."""

    launchClicked = Signal(ApplicationConfig)
    editClicked = Signal(ApplicationConfig)
    deleteClicked = Signal(ApplicationConfig)

    def __init__(
            self,
            app_config: ApplicationConfig,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the application card.

        Args:
            app_config: The application configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.app_config = app_config

        self.setObjectName("ApplicationCard")
        self.setStyleSheet("""
            #ApplicationCard {
                background-color: #f5f5f5;
                border-radius: 6px;
                border: 1px solid #ddd;
            }

            #ApplicationCard:hover {
                background-color: #e9e9e9;
            }

            QLabel#app_name {
                font-weight: bold;
                font-size: 14px;
            }

            QLabel#app_description {
                color: #666;
            }
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)

        # Header with name and action buttons
        header_layout = QHBoxLayout()

        # App icon
        if app_config.icon_path and os.path.exists(app_config.icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(app_config.icon_path).pixmap(32, 32))
            header_layout.addWidget(icon_label)

        # App name
        self.name_label = QLabel(app_config.name)
        self.name_label.setObjectName("app_name")
        header_layout.addWidget(self.name_label)

        header_layout.addStretch()

        # Action buttons
        self.launch_btn = QPushButton("Launch")
        self.launch_btn.clicked.connect(self._on_launch_clicked)
        header_layout.addWidget(self.launch_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        header_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        header_layout.addWidget(self.delete_btn)

        self._layout.addLayout(header_layout)

        # Description
        if app_config.description:
            self.desc_label = QLabel(app_config.description)
            self.desc_label.setObjectName("app_description")
            self.desc_label.setWordWrap(True)
            self._layout.addWidget(self.desc_label)

        # Path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Path:"))
        path_label = QLabel(app_config.executable_path)
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_layout.addWidget(path_label)
        path_layout.addStretch()
        self._layout.addLayout(path_layout)

        # Arguments summary
        if app_config.arguments:
            args_layout = QHBoxLayout()
            args_layout.addWidget(QLabel("Arguments:"))
            args_count = len(app_config.arguments)
            args_label = QLabel(f"{args_count} argument{'s' if args_count != 1 else ''}")
            args_layout.addWidget(args_label)
            args_layout.addStretch()
            self._layout.addLayout(args_layout)

    def _on_launch_clicked(self) -> None:
        """Handle launch button click."""
        self.launchClicked.emit(self.app_config)

    def _on_edit_clicked(self) -> None:
        """Handle edit button click."""
        self.editClicked.emit(self.app_config)

    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        self.deleteClicked.emit(self.app_config)


class ApplicationRunDialog(QDialog):
    """Dialog for configuring arguments and running an application."""

    def __init__(
            self,
            app_config: ApplicationConfig,
            app_runner: ApplicationRunner,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the application run dialog.

        Args:
            app_config: The application configuration
            app_runner: The application runner to use
            parent: Parent widget
        """
        super().__init__(parent)
        self.app_config = app_config
        self.app_runner = app_runner

        self.arg_widgets: Dict[str, ArgumentInputWidget] = {}
        self.arg_values: Dict[str, str] = {}

        self.resize(800, 600)
        self.setWindowTitle(f"Run {app_config.name}")

        # Make the dialog non-modal
        self.setModal(False)

        # State tracking
        self._minimized = False
        self._process_running = False
        self._process_complete = False
        self._exit_code = 0
        self._process_start_time = 0.0

        self._init_ui()
        self._update_command_preview()

        # Connect signals
        self.app_runner.processStarted.connect(self._on_process_started)
        self.app_runner.processFinished.connect(self._on_process_finished)
        self.app_runner.processError.connect(self._on_process_error)
        self.app_runner.stdoutReceived.connect(self._on_stdout_received)
        self.app_runner.stderrReceived.connect(self._on_stderr_received)
        self.app_runner.outputFilesDetected.connect(self._on_output_files_detected)

    def _init_ui(self) -> None:
        """Initialize the dialog UI components."""
        self._layout = QVBoxLayout(self)

        # Create the minimized status bar
        self._status_bar = QWidget()
        self._status_bar_layout = QHBoxLayout(self._status_bar)
        self._status_bar_layout.setContentsMargins(10, 5, 10, 5)

        self._status_app_label = QLabel(f"<b>{self.app_config.name}</b>")
        self._status_bar_layout.addWidget(self._status_app_label)

        self._status_indicator = QLabel("Not Started")
        self._status_bar_layout.addWidget(self._status_indicator)

        self._status_runtime = QLabel("")
        self._status_bar_layout.addWidget(self._status_runtime)

        self._status_bar_layout.addStretch()

        self._restore_btn = QPushButton("Restore")
        self._restore_btn.clicked.connect(self._toggle_minimize)
        self._status_bar_layout.addWidget(self._restore_btn)

        self._layout.addWidget(self._status_bar)
        self._status_bar.setVisible(False)  # Initially hidden

        # Create main content area
        self._main_content = QWidget()
        self._main_content_layout = QVBoxLayout(self._main_content)
        self._main_content_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._main_content)

        # Add header with minimize button
        header_layout = QHBoxLayout()
        header_label = QLabel(f"<b>Configure and Run: {self.app_config.name}</b>")
        header_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        self._minimize_btn = QPushButton("Minimize")
        self._minimize_btn.setToolTip("Minimize to status bar")
        self._minimize_btn.clicked.connect(self._toggle_minimize)
        header_layout.addWidget(self._minimize_btn)

        self._main_content_layout.addLayout(header_layout)

        # Create top section for arguments
        self._args_widget = QWidget()
        self._args_layout = QVBoxLayout(self._args_widget)
        self._args_layout.setContentsMargins(0, 0, 0, 0)

        args_group = QGroupBox("Arguments")
        args_group_layout = QVBoxLayout(args_group)

        for arg_config in self.app_config.arguments:
            arg_layout = QHBoxLayout()

            # Label with name and description
            label_text = arg_config.name
            if arg_config.description:
                label_text += f" - {arg_config.description}"
            if arg_config.required:
                label_text += " (Required)"

            arg_label = QLabel(label_text)
            arg_layout.addWidget(arg_label)

            # Input widget for the argument
            arg_input = ArgumentInputWidget(arg_config, self)
            arg_input.valueChanged.connect(
                lambda value, name=arg_config.name: self._on_arg_value_changed(name, value)
            )
            arg_layout.addWidget(arg_input)

            # Add buttons for file/directory arguments
            if arg_config.arg_type in (ArgumentType.FILE_INPUT, ArgumentType.FILE_OUTPUT, ArgumentType.DIRECTORY):
                open_btn = QPushButton("Open")
                open_btn.setToolTip("Open the file or directory")
                open_btn.clicked.connect(lambda checked=False, name=arg_config.name:
                                         self._open_path(self.arg_values.get(name, arg_config.value)))
                arg_layout.addWidget(open_btn)

            args_group_layout.addLayout(arg_layout)

            # Store the widget for later access
            self.arg_widgets[arg_config.name] = arg_input
            self.arg_values[arg_config.name] = arg_config.value

        # If no arguments, show a message
        if not self.app_config.arguments:
            args_group_layout.addWidget(QLabel("No configurable arguments for this application."))

        self._args_layout.addWidget(args_group)

        # Add command preview
        command_group = QGroupBox("Command")
        command_layout = QVBoxLayout(command_group)

        self._command_preview = QTextEdit()
        self._command_preview.setReadOnly(True)
        self._command_preview.setMaximumHeight(60)
        self._command_preview.setLineWrapMode(QTextEdit.WidgetWidth)

        # Copy button for command
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_command_to_clipboard)

        command_layout.addWidget(self._command_preview)
        command_layout.addWidget(copy_btn)

        self._args_layout.addWidget(command_group)
        self._main_content_layout.addWidget(self._args_widget)

        # Add working directory controls
        if self.app_config.working_directory:
            working_dir_layout = QHBoxLayout()
            working_dir_layout.addWidget(QLabel("Working Directory:"))

            dir_label = QLabel(self.app_config.working_directory)
            dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            working_dir_layout.addWidget(dir_label)

            open_dir_btn = QPushButton("Open")
            open_dir_btn.clicked.connect(lambda: self._open_path(self.app_config.working_directory))
            working_dir_layout.addWidget(open_dir_btn)

            self._main_content_layout.addLayout(working_dir_layout)

        # Create splitter for output
        self._output_splitter = QSplitter(Qt.Vertical)

        # Console output
        self._console_output = ConsoleOutputWidget()
        self._output_splitter.addWidget(self._console_output)

        # Output files
        self._output_files = OutputFilesWidget()
        self._output_splitter.addWidget(self._output_files)

        # Initially hide output if configured
        if self.app_config.show_console_output:
            self._main_content_layout.addWidget(self._output_splitter)
        else:
            self._output_splitter.setVisible(False)

        # Action buttons
        self._button_layout = QHBoxLayout()

        self._run_button = QPushButton("Run")
        self._run_button.clicked.connect(self._on_run_clicked)
        self._button_layout.addWidget(self._run_button)

        self._stop_button = QPushButton("Stop")
        self._stop_button.clicked.connect(self._on_stop_clicked)
        self._stop_button.setEnabled(False)
        self._button_layout.addWidget(self._stop_button)

        self._button_layout.addStretch()

        self._close_button = QPushButton("Close")
        self._close_button.clicked.connect(self.close)
        self._button_layout.addWidget(self._close_button)

        self._main_content_layout.addLayout(self._button_layout)

        # Update timer for status
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(1000)  # Update every second
        self._status_timer.timeout.connect(self._update_status)

    def _toggle_minimize(self) -> None:
        """Toggle between minimized and full view."""
        self._minimized = not self._minimized

        if self._minimized:
            # Switch to minimized view
            self._main_content.setVisible(False)
            self._status_bar.setVisible(True)
            self.setFixedHeight(60)  # Small fixed height
            self.setWindowTitle(f"Run: {self.app_config.name} (Minimized)")
        else:
            # Switch to full view
            self._status_bar.setVisible(False)
            self._main_content.setVisible(True)
            self.setMinimumHeight(300)
            self.setFixedHeight(self.sizeHint().height())
            self.setWindowTitle(f"Run {self.app_config.name}")

        self._update_status()

    def _update_status(self) -> None:
        """Update status indicators."""
        # Update runtime if process is running
        if self._process_running and self._process_start_time > 0:
            import time
            runtime = time.time() - self._process_start_time
            runtime_str = f"Runtime: {int(runtime)}s"
            self._status_runtime.setText(runtime_str)

        # Update status indicator
        if self._process_running:
            self._status_indicator.setText("Running")
            self._status_indicator.setStyleSheet("color: blue; font-weight: bold;")
        elif self._process_complete:
            if self._exit_code == 0:
                self._status_indicator.setText("Completed Successfully")
                self._status_indicator.setStyleSheet("color: green; font-weight: bold;")
            else:
                self._status_indicator.setText(f"Failed (Exit Code: {self._exit_code})")
                self._status_indicator.setStyleSheet("color: red; font-weight: bold;")
        else:
            self._status_indicator.setText("Not Started")
            self._status_indicator.setStyleSheet("")

    def _update_command_preview(self) -> None:
        """Update the command preview based on current argument values."""
        executable = self.app_config.executable_path

        # Build display arguments
        cmd_display_args = []
        for arg_config in self.app_config.arguments:
            value = self.arg_values.get(arg_config.name, arg_config.value)
            if value:  # Only add non-empty arguments
                if arg_config.prefix:
                    cmd_display_args.append(f"{arg_config.prefix}{value}")
                else:
                    cmd_display_args.append(value)

        # Build command line for display
        import shlex
        cmd_args = " ".join(shlex.quote(arg) for arg in cmd_display_args)
        command_line = f"{shlex.quote(executable)} {cmd_args}"

        # Update preview
        self._command_preview.setText(command_line)

    def _copy_command_to_clipboard(self) -> None:
        """Copy the command to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._command_preview.toPlainText())

    def _on_arg_value_changed(self, name: str, value: str) -> None:
        """
        Handle argument value changes.

        Args:
            name: Argument name
            value: New argument value
        """
        self.arg_values[name] = value
        self._update_command_preview()

    def _open_path(self, path: str) -> None:
        """
        Open a file or directory.

        Args:
            path: Path to open
        """
        if not path:
            return

        # Resolve relative paths against working directory
        if not os.path.isabs(path) and self.app_config.working_directory:
            resolved_path = os.path.join(self.app_config.working_directory, path)
        else:
            resolved_path = path

        # Check if the path exists
        if not os.path.exists(resolved_path):
            QMessageBox.warning(
                self,
                "Path Not Found",
                f"The path does not exist: {resolved_path}"
            )
            return

        # Open the file or directory
        url = QUrl.fromLocalFile(resolved_path)
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(
                self,
                "Open Failed",
                f"Failed to open: {resolved_path}"
            )

    def _on_run_clicked(self) -> None:
        """Handle run button click."""
        # Check required arguments
        missing_args = []
        for arg_config in self.app_config.arguments:
            if arg_config.required and not self.arg_values.get(arg_config.name):
                missing_args.append(arg_config.name)

        if missing_args:
            QMessageBox.warning(
                self,
                "Missing Arguments",
                f"The following required arguments are missing: {', '.join(missing_args)}",
            )
            return

        # Run the application
        self.app_runner.run_application(self.app_config, self.arg_values)

    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.app_runner.terminate_process()

    def _on_process_started(self) -> None:
        """Handle process started event."""
        # Update UI
        self._run_button.setEnabled(False)
        self._stop_button.setEnabled(True)
        self._args_widget.setEnabled(False)

        # Show output if not already visible
        if not self._output_splitter.isVisible():
            self._output_splitter.setVisible(True)

        # Update console
        cmd_line = self.app_runner._output.command_line
        self._console_output.start_process(cmd_line)

        # Update status tracking
        self._process_running = True
        self._process_complete = False
        import time
        self._process_start_time = time.time()

        # Start status timer
        self._status_timer.start()

        # Update status display
        self._update_status()

        # Auto-minimize for long-running processes if appropriate
        if len(self.app_config.arguments) > 3 or self.app_config.description.lower().find("long") >= 0:
            if not self._minimized:
                self._toggle_minimize()

    def _on_process_finished(self, output: ProcessOutput) -> None:
        """
        Handle process finished event.

        Args:
            output: Process output data
        """
        # Update UI
        self._run_button.setEnabled(True)
        self._stop_button.setEnabled(False)
        self._args_widget.setEnabled(True)

        # Update console
        self._exit_code = output.exit_code or 0
        self._console_output.process_finished(self._exit_code)

        # Update status tracking
        self._process_running = False
        self._process_complete = True
        self._status_timer.stop()

        # Final status update
        self._update_status()

        # Auto-open output files if configured
        if self.app_config.auto_open_output and output.output_files:
            first_file = output.output_files[0]
            QDesktopServices.openUrl(QUrl.fromLocalFile(first_file))

    def _on_process_error(self, error_message: str) -> None:
        """
        Handle process error event.

        Args:
            error_message: Error message
        """
        QMessageBox.critical(self, "Process Error", error_message)

        # Update UI
        self._run_button.setEnabled(True)
        self._stop_button.setEnabled(False)
        self._args_widget.setEnabled(True)

        # Update status tracking
        self._process_running = False
        self._process_complete = True
        self._exit_code = 1  # Assume error
        self._status_timer.stop()

        # Final status update
        self._update_status()

    def _on_stdout_received(self, text: str) -> None:
        """
        Handle stdout received event.

        Args:
            text: Stdout text
        """
        self._console_output.append_stdout(text)

    def _on_stderr_received(self, text: str) -> None:
        """
        Handle stderr received event.

        Args:
            text: Stderr text
        """
        self._console_output.append_stderr(text)

    def _on_output_files_detected(self, file_paths: List[str]) -> None:
        """
        Handle output files detected event.

        Args:
            file_paths: List of detected output file paths
        """
        self._output_files.set_files(file_paths)

    def closeEvent(self, event: Any) -> None:
        """Handle dialog close event."""
        # Stop the process if running
        self.app_runner.terminate_process()
        self._status_timer.stop()
        super().closeEvent(event)


class ApplicationLauncherWidget(QWidget):
    """Main widget for the Application Launcher plugin."""

    def __init__(
            self,
            event_bus_manager: EventBusManager,
            concurrency_manager: ConcurrencyManager,
            task_manager: TaskManager,
            file_manager: FileManager,
            logger: logging.Logger,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the application launcher widget.

        Args:
            event_bus_manager: Event bus manager for pub/sub events
            concurrency_manager: Concurrency manager for async tasks
            task_manager: Task manager for background tasks
            file_manager: File manager for file operations
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._event_bus_manager = event_bus_manager
        self._concurrency_manager = concurrency_manager
        self._task_manager = task_manager
        self._file_manager = file_manager
        self._logger = logger

        # Application configurations
        self._app_configs: Dict[str, ApplicationConfig] = {}

        # Application runner
        self._app_runner = ApplicationRunner(concurrency_manager, file_manager, self)

        # Set up UI
        self._init_ui()

        # Load saved applications
        asyncio.create_task(self._load_applications())

    def _init_ui(self) -> None:
        """Initialize the widget UI components."""
        self._layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Application Launcher")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header_label)

        self._add_app_btn = QPushButton("Add Application")
        self._add_app_btn.clicked.connect(self._on_add_app_clicked)
        header_layout.addWidget(self._add_app_btn)

        self._layout.addLayout(header_layout)

        # Search and filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search applications...")
        self._search_edit.textChanged.connect(self._on_search_text_changed)
        filter_layout.addWidget(self._search_edit)

        filter_layout.addWidget(QLabel("Category:"))
        self._category_combo = QComboBox()
        self._category_combo.addItem("All Categories")
        self._category_combo.currentTextChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self._category_combo)

        self._layout.addLayout(filter_layout)

        # Applications container
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)

        self._apps_container = QWidget()
        self._apps_layout = QVBoxLayout(self._apps_container)
        self._apps_layout.setAlignment(Qt.AlignTop)
        self._scroll_area.setWidget(self._apps_container)

        self._layout.addWidget(self._scroll_area)

        # No applications message
        self._no_apps_label = QLabel("No applications configured. Click 'Add Application' to create one.")
        self._no_apps_label.setAlignment(Qt.AlignCenter)
        self._no_apps_label.setStyleSheet("color: #666; margin: 20px;")
        self._apps_layout.addWidget(self._no_apps_label)

    async def _load_applications(self) -> None:
        """Load saved applications from configuration."""
        try:
            if not self._file_manager:
                self._logger.error("File manager not available, cannot load applications")
                return

            config_dir = "application_launcher"
            await self._file_manager.ensure_directory(config_dir, "plugin_data")

            config_path = "apps.json"
            full_path = config_dir + "/" + config_path

            try:
                data = await self._file_manager.read_text(full_path, "plugin_data")
                import json
                apps_dict = json.loads(data)

                for app_id, app_data in apps_dict.items():
                    arguments = []
                    for arg_data in app_data.get("arguments", []):
                        arguments.append(ArgumentConfig(
                            name=arg_data.get("name", ""),
                            arg_type=ArgumentType(arg_data.get("arg_type", ArgumentType.STATIC)),
                            value=arg_data.get("value", ""),
                            description=arg_data.get("description", ""),
                            required=arg_data.get("required", False),
                            file_filter=arg_data.get("file_filter", ""),
                            prefix=arg_data.get("prefix", "")
                        ))

                    app_config = ApplicationConfig(
                        id=app_id,
                        name=app_data.get("name", "Unknown"),
                        executable_path=app_data.get("executable_path", ""),
                        working_directory=app_data.get("working_directory"),
                        arguments=arguments,
                        environment_variables=app_data.get("environment_variables", {}),
                        show_console_output=app_data.get("show_console_output", True),
                        category=app_data.get("category", "General"),
                        description=app_data.get("description", ""),
                        icon_path=app_data.get("icon_path"),
                        output_patterns=app_data.get("output_patterns", []),
                        auto_open_output=app_data.get("auto_open_output", False)
                    )

                    self._app_configs[app_id] = app_config

                await self._concurrency_manager.run_on_main_thread(
                    self._update_applications_ui
                )

                self._logger.info(f"Loaded {len(self._app_configs)} applications")
            except FileNotFoundError:
                self._logger.info("No saved applications found")
            except json.JSONDecodeError:
                self._logger.error("Invalid applications configuration file")
        except Exception as e:
            self._logger.error(f"Error loading applications: {str(e)}")

    async def _save_applications(self) -> None:
        """Save applications to configuration."""
        try:
            if not self._file_manager:
                self._logger.error("File manager not available, cannot save applications")
                return

            config_dir = "application_launcher"
            await self._file_manager.ensure_directory(config_dir, "plugin_data")

            config_path = "apps.json"
            full_path = config_dir + "/" + config_path

            # Convert to serializable format
            apps_dict = {}
            for app_id, app_config in self._app_configs.items():
                arguments = []
                for arg in app_config.arguments:
                    arguments.append({
                        "name": arg.name,
                        "arg_type": arg.arg_type,
                        "value": arg.value,
                        "description": arg.description,
                        "required": arg.required,
                        "file_filter": arg.file_filter,
                        "prefix": arg.prefix
                    })

                apps_dict[app_id] = {
                    "name": app_config.name,
                    "executable_path": app_config.executable_path,
                    "working_directory": app_config.working_directory,
                    "arguments": arguments,
                    "environment_variables": app_config.environment_variables,
                    "show_console_output": app_config.show_console_output,
                    "category": app_config.category,
                    "description": app_config.description,
                    "icon_path": app_config.icon_path,
                    "output_patterns": app_config.output_patterns,
                    "auto_open_output": app_config.auto_open_output
                }

            import json
            data = json.dumps(apps_dict, indent=2)
            await self._file_manager.write_text(full_path, data, "plugin_data")

            self._logger.info(f"Saved {len(self._app_configs)} applications")
        except Exception as e:
            self._logger.error(f"Error saving applications: {str(e)}")

    def _update_applications_ui(self) -> None:
        """Update the UI with the current applications."""
        # Clear existing widgets
        while self._apps_layout.count() > 0:
            item = self._apps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get current filter
        search_text = self._search_edit.text().lower()
        category_filter = self._category_combo.currentText()
        if category_filter == "All Categories":
            category_filter = ""

        # Update category list
        categories = set(["All Categories"])
        for app_config in self._app_configs.values():
            categories.add(app_config.category)

        # Update category combobox while preserving selection
        current_category = self._category_combo.currentText()
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        for category in sorted(categories):
            self._category_combo.addItem(category)

        # Restore selection if possible
        index = self._category_combo.findText(current_category)
        if index >= 0:
            self._category_combo.setCurrentIndex(index)
        self._category_combo.blockSignals(False)

        # Add application cards
        filtered_apps = []
        for app_id, app_config in self._app_configs.items():
            # Apply filters
            if search_text and not (
                    search_text in app_config.name.lower() or
                    search_text in app_config.description.lower()
            ):
                continue

            if category_filter and app_config.category != category_filter:
                continue

            filtered_apps.append(app_config)

        # Sort by name
        filtered_apps.sort(key=lambda app: app.name.lower())

        # Create a new no apps label each time instead of reusing it
        no_apps_label = QLabel()
        no_apps_label.setAlignment(Qt.AlignCenter)
        no_apps_label.setStyleSheet("color: #666; margin: 20px;")

        # Show message if no apps
        if not filtered_apps:
            if search_text or category_filter:
                no_apps_label.setText("No applications match the current filter.")
            else:
                no_apps_label.setText("No applications configured. Click 'Add Application' to create one.")
            self._apps_layout.addWidget(no_apps_label)
            self._no_apps_label = no_apps_label
        else:
            for app_config in filtered_apps:
                card = ApplicationCard(app_config, self)
                card.launchClicked.connect(self._on_launch_app)
                card.editClicked.connect(self._on_edit_app)
                card.deleteClicked.connect(self._on_delete_app)
                self._apps_layout.addWidget(card)

        # Add stretch at the end
        self._apps_layout.addStretch()

    def _on_add_app_clicked(self) -> None:
        """Handle add application button click."""
        dialog = ApplicationConfigDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            app_config = dialog.get_config()
            self._app_configs[app_config.id] = app_config
            self._update_applications_ui()
            asyncio.create_task(self._save_applications())

    def _on_edit_app(self, app_config: ApplicationConfig) -> None:
        """
        Handle edit application button click.

        Args:
            app_config: Application configuration to edit
        """
        dialog = ApplicationConfigDialog(app_config, parent=self)
        if dialog.exec() == QDialog.Accepted:
            updated_config = dialog.get_config()
            self._app_configs[updated_config.id] = updated_config
            self._update_applications_ui()
            asyncio.create_task(self._save_applications())

    def _on_delete_app(self, app_config: ApplicationConfig) -> None:
        """
        Handle delete application button click.

        Args:
            app_config: Application configuration to delete
        """
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{app_config.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if app_config.id in self._app_configs:
                del self._app_configs[app_config.id]
                self._update_applications_ui()
                asyncio.create_task(self._save_applications())

    def _on_launch_app(self, app_config: ApplicationConfig) -> None:
        """
        Handle launch application button click.

        Args:
            app_config: Application configuration to launch
        """
        dialog = ApplicationRunDialog(app_config, self._app_runner, parent=self)
        # Show the dialog non-modally
        dialog.show()

    def _on_search_text_changed(self, text: str) -> None:
        """
        Handle search text changes.

        Args:
            text: New search text
        """
        self._update_applications_ui()

    def _on_category_changed(self, category: str) -> None:
        """
        Handle category filter changes.

        Args:
            category: New category filter
        """
        self._update_applications_ui()

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        try:
            # Stop any running processes
            if hasattr(self, "_app_runner"):
                self._app_runner.terminate_process()

            # Save applications
            await self._save_applications()

            self._logger.info("Application launcher widget shut down")
        except Exception as e:
            self._logger.error(f"Error during widget shutdown: {str(e)}")


class ApplicationLauncherPlugin(BasePlugin):
    """
    Plugin for launching external applications with configurable arguments.

    This plugin allows users to configure and launch external applications,
    specifying command line arguments and viewing the console output and output files.
    """

    name = "application_launcher"
    version = "1.0.0"
    description = "Launch external applications with configurable arguments"
    author = "Qorzen Developer"
    display_name = "Application Launcher"
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the application launcher plugin."""
        super().__init__()
        self._main_widget: Optional[ApplicationLauncherWidget] = None
        self._logger: Optional[logging.Logger] = None
        self._event_bus_manager: Optional[EventBusManager] = None
        self._concurrency_manager: Optional[ConcurrencyManager] = None
        self._task_manager: Optional[TaskManager] = None
        self._file_manager: Optional[FileManager] = None
        self._icon_path: Optional[str] = None
        self._ui_components_created = False

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin.

        Args:
            application_core: The application core instance
            **kwargs: Additional keyword arguments
        """
        await super().initialize(application_core, **kwargs)
        self._logger = self._logger or logging.getLogger(self.name)
        self._logger.info(f"Initializing {self.name} plugin")

        self._concurrency_manager = self._concurrency_manager or application_core.get_manager("concurrency_manager")
        self._event_bus_manager = self._event_bus_manager or application_core.get_manager("event_bus_manager")
        self._task_manager = self._task_manager or application_core.get_manager("task_manager")
        self._file_manager = self._file_manager or application_core.get_manager("file_manager")

        # Find plugin directory and icon
        plugin_dir = await self._find_plugin_directory()
        if plugin_dir:
            icon_path = os.path.join(plugin_dir, "resources", "icon.png")
            if os.path.exists(icon_path):
                self._icon_path = icon_path
                self._logger.debug(f"Found plugin icon at: {icon_path}")

        await self._event_bus_manager.subscribe(
            event_type="application_launcher:log_message",
            callback=self._on_log_message,
            subscriber_id="application_launcher_plugin"
        )

        await set_plugin_state(self.name, PluginLifecycleState.INITIALIZED)
        self._logger.info(f"{self.name} plugin initialized successfully")

    async def _find_plugin_directory(self) -> Optional[str]:
        """
        Find the plugin directory.

        Returns:
            The plugin directory path or None if not found
        """
        import inspect
        try:
            module_path = inspect.getmodule(self).__file__
            if module_path:
                return os.path.dirname(os.path.abspath(module_path))
        except (AttributeError, TypeError):
            pass
        return None

    async def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """
        Set up UI components when UI is ready.

        Args:
            ui_integration: The UI integration instance
        """
        if self._logger:
            self._logger.info("Setting up UI components")

        current_state = await get_plugin_state(self.name)
        if current_state == PluginLifecycleState.UI_READY:
            self._logger.debug("UI setup already in progress, avoiding recursive call")
            return

        if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
            self._logger.debug("on_ui_ready called from non-main thread, delegating to main thread")
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self.on_ui_ready(ui_integration))
            )
            return

        if hasattr(self, "_ui_components_created") and self._ui_components_created:
            self._logger.debug("UI components already created, skipping duplicate creation")
            await signal_ui_ready(self.name)
            return

        try:
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)

            # Add menu items
            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Tools",
                title="Application Launcher",
                callback=lambda: asyncio.create_task(self._open_application_launcher()),
                icon=self._icon_path
            )

            # Create main widget
            if not self._main_widget:
                self._main_widget = ApplicationLauncherWidget(
                    self._event_bus_manager,
                    self._concurrency_manager,
                    self._task_manager,
                    self._file_manager,
                    self._logger,
                    None
                )

            # Add page
            await ui_integration.add_page(
                plugin_id=self.plugin_id,
                page_component=self._main_widget,
                icon=self._icon_path,
                title=self.display_name or self.name
            )

            self._ui_components_created = True
            await set_plugin_state(self.name, PluginLifecycleState.ACTIVE)
            await signal_ui_ready(self.name)

            if self._logger:
                self._logger.info("UI components set up successfully")
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to set up UI components: {str(e)}")
            await set_plugin_state(self.name, PluginLifecycleState.FAILED)

    async def setup_ui(self, ui_integration: Any) -> None:
        """
        Set up UI components (legacy method).

        Args:
            ui_integration: The UI integration instance
        """
        if self._logger:
            self._logger.info("setup_ui method called")
        await self.on_ui_ready(ui_integration)

    async def _on_log_message(self, event: Any) -> None:
        """
        Handle log message events.

        Args:
            event: The log event
        """
        if not self._logger:
            return

        payload = event.payload
        level = payload.get("level", "info")
        message = payload.get("message", "")

        if level == "debug":
            self._logger.debug(message)
        elif level == "info":
            self._logger.info(message)
        elif level == "warning":
            self._logger.warning(message)
        elif level == "error":
            self._logger.error(message)
        else:
            self._logger.info(f"[{level}] {message}")

    async def _open_application_launcher(self) -> None:
        """Open the application launcher page."""
        # This is a placeholder for a callback - the page is already opened by ui_integration
        pass

    def get_main_widget(self) -> Optional[QWidget]:
        """
        Get the main widget instance.

        Returns:
            The main widget or None if not created
        """
        return self._main_widget

    def get_icon(self) -> Optional[str]:
        """
        Get the plugin icon path.

        Returns:
            The icon path or None if not set
        """
        return self._icon_path

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        if self._logger:
            self._logger.info(f"Shutting down {self.name} plugin")

        await set_plugin_state(self.name, PluginLifecycleState.DISABLING)

        if self._event_bus_manager:
            await self._event_bus_manager.unsubscribe(subscriber_id="application_launcher_plugin")

        if self._main_widget:
            try:
                await self._main_widget.shutdown()
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error shutting down main widget: {str(e)}")
            self._main_widget = None

        await super().shutdown()
        await set_plugin_state(self.name, PluginLifecycleState.INACTIVE)

        if self._logger:
            self._logger.info(f"{self.name} plugin shutdown complete")