"""processed_project/qorzen_stripped/ui/settings_manager.py

Settings Manager UI for Qorzen Application.

This module provides a comprehensive settings interface that allows users to configure
all application settings through a professional GUI. The settings are organized by
category and include search functionality for easy navigation.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, TypedDict, Protocol

from PySide6.QtCore import (
    QAbstractItemModel, QModelIndex, QPersistentModelIndex, QTimer, Qt, Signal, QThread, QObject
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QScrollArea, QSpinBox, QSplitter,
    QStackedWidget, QTabWidget, QTextEdit, QTreeView, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QMessageBox, QProgressBar,
    QSlider, QFileDialog, QColorDialog, QFontDialog
)


class SettingType(str, Enum):
    """Types of settings that can be configured."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    PATH = "path"
    COLOR = "color"
    FONT = "font"
    PASSWORD = "password"
    CHOICE = "choice"
    JSON = "json"


class SettingCategory(str, Enum):
    """Categories for organizing settings."""
    APPLICATION = "Application"
    DATABASE = "Database"
    LOGGING = "Logging"
    SECURITY = "Security"
    API = "API"
    PLUGINS = "Plugins"
    MONITORING = "Monitoring"
    FILES = "Files"
    CLOUD = "Cloud"
    NETWORKING = "Networking"
    PERFORMANCE = "Performance"
    UI = "User Interface"
    ADVANCED = "Advanced"


@dataclass
class SettingDefinition:
    """Definition of a configurable setting."""
    key: str
    name: str
    description: str
    setting_type: SettingType
    category: SettingCategory
    default_value: Any
    current_value: Any = None
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    validation_func: Optional[Callable[[Any], bool]] = None
    requires_restart: bool = False
    is_advanced: bool = False
    tooltip: Optional[str] = None
    placeholder: Optional[str] = None
    file_filter: Optional[str] = None  # For file path settings


class SettingWidget(QWidget):
    """Base class for setting input widgets."""

    valueChanged = Signal(object)

    def __init__(self, setting_def: SettingDefinition, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setting_def = setting_def
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the widget UI."""
        raise NotImplementedError

    def get_value(self) -> Any:
        """Get the current value from the widget."""
        raise NotImplementedError

    def set_value(self, value: Any) -> None:
        """Set the value in the widget."""
        raise NotImplementedError

    def validate(self) -> tuple[bool, str]:
        """Validate the current value."""
        value = self.get_value()

        if self.setting_def.validation_func:
            try:
                if not self.setting_def.validation_func(value):
                    return False, "Value failed custom validation"
            except Exception as e:
                return False, f"Validation error: {str(e)}"

        if self.setting_def.min_value is not None and isinstance(value, (int, float)):
            if value < self.setting_def.min_value:
                return False, f"Value must be at least {self.setting_def.min_value}"

        if self.setting_def.max_value is not None and isinstance(value, (int, float)):
            if value > self.setting_def.max_value:
                return False, f"Value must be at most {self.setting_def.max_value}"

        return True, ""


class StringSettingWidget(SettingWidget):
    """Widget for string settings."""

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        if self.setting_def.setting_type == SettingType.PASSWORD:
            self.line_edit = QLineEdit()
            self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            self.line_edit = QLineEdit()

        if self.setting_def.placeholder:
            self.line_edit.setPlaceholderText(self.setting_def.placeholder)

        self.line_edit.textChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.line_edit)

    def get_value(self) -> str:
        return self.line_edit.text()

    def set_value(self, value: Any) -> None:
        self.line_edit.setText(str(value) if value is not None else "")


class IntegerSettingWidget(SettingWidget):
    """Widget for integer settings."""

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        self.spin_box = QSpinBox()
        self.spin_box.setRange(
            self.setting_def.min_value or -2147483648,
            self.setting_def.max_value or 2147483647
        )
        self.spin_box.valueChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.spin_box)

    def get_value(self) -> int:
        return self.spin_box.value()

    def set_value(self, value: Any) -> None:
        try:
            self.spin_box.setValue(int(value) if value is not None else 0)
        except (ValueError, TypeError):
            self.spin_box.setValue(0)


class FloatSettingWidget(SettingWidget):
    """Widget for float settings."""

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(
            self.setting_def.min_value or -1e308,
            self.setting_def.max_value or 1e308
        )
        self.spin_box.setDecimals(3)
        self.spin_box.valueChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.spin_box)

    def get_value(self) -> float:
        return self.spin_box.value()

    def set_value(self, value: Any) -> None:
        try:
            self.spin_box.setValue(float(value) if value is not None else 0.0)
        except (ValueError, TypeError):
            self.spin_box.setValue(0.0)


class BooleanSettingWidget(SettingWidget):
    """Widget for boolean settings."""

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        self.check_box = QCheckBox()
        self.check_box.toggled.connect(self.valueChanged.emit)
        layout.addWidget(self.check_box)

    def get_value(self) -> bool:
        return self.check_box.isChecked()

    def set_value(self, value: Any) -> None:
        self.check_box.setChecked(bool(value) if value is not None else False)


class ChoiceSettingWidget(SettingWidget):
    """Widget for choice settings."""

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        self.combo_box = QComboBox()
        if self.setting_def.choices:
            for choice in self.setting_def.choices:
                self.combo_box.addItem(str(choice), choice)

        self.combo_box.currentTextChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.combo_box)

    def get_value(self) -> Any:
        return self.combo_box.currentData()

    def set_value(self, value: Any) -> None:
        index = self.combo_box.findData(value)
        if index >= 0:
            self.combo_box.setCurrentIndex(index)


class PathSettingWidget(SettingWidget):
    """Widget for file/directory path settings."""

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.valueChanged.emit)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_path)

        layout.addWidget(self.line_edit)
        layout.addWidget(self.browse_button)

    def _browse_path(self) -> None:
        current_path = self.line_edit.text()
        file_filter = self.setting_def.file_filter or "All Files (*)"

        if "directory" in self.setting_def.description.lower():
            from PySide6.QtWidgets import QFileDialog
            path = QFileDialog.getExistingDirectory(
                self, f"Select {self.setting_def.name}", current_path
            )
        else:
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(
                self, f"Select {self.setting_def.name}", current_path, file_filter
            )

        if path:
            self.line_edit.setText(path)

    def get_value(self) -> str:
        return self.line_edit.text()

    def set_value(self, value: Any) -> None:
        self.line_edit.setText(str(value) if value is not None else "")


class JsonSettingWidget(SettingWidget):
    """Widget for JSON/dict settings."""

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(120)
        self.text_edit.textChanged.connect(self._on_text_changed)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: red;")

        layout.addWidget(self.text_edit)
        layout.addWidget(self.status_label)

    def _on_text_changed(self) -> None:
        try:
            json.loads(self.text_edit.toPlainText())
            self.status_label.setText("")
            self.valueChanged.emit(self.get_value())
        except json.JSONDecodeError as e:
            self.status_label.setText(f"JSON Error: {str(e)}")

    def get_value(self) -> Any:
        try:
            return json.loads(self.text_edit.toPlainText())
        except json.JSONDecodeError:
            return {}

    def set_value(self, value: Any) -> None:
        try:
            json_str = json.dumps(value, indent=2) if value is not None else "{}"
            self.text_edit.setPlainText(json_str)
        except (TypeError, ValueError):
            self.text_edit.setPlainText("{}")


class SettingsManager(QWidget):
    """Main settings manager widget."""

    settingChanged = Signal(str, object)  # key, value
    settingsSaved = Signal()

    def __init__(self, app_core: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.config_manager = self.app_core.get_manager('config_manager')
        self.logger = logging.getLogger("settings_manager")

        # Store settings definitions and widgets
        self.setting_definitions: Dict[str, SettingDefinition] = {}
        self.setting_widgets: Dict[str, SettingWidget] = {}
        self.category_widgets: Dict[SettingCategory, QWidget] = {}

        # UI components
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)

        self.setup_ui()
        self.load_setting_definitions()
        asyncio.create_task(self.load_current_values())

    def setup_ui(self) -> None:
        """Setup the main UI layout."""
        layout = QVBoxLayout(self)

        # Header with search
        header_layout = QHBoxLayout()

        header_label = QLabel("Application Settings")
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search settings...")
        self.search_edit.textChanged.connect(self._on_search_changed)

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Search:"))
        header_layout.addWidget(self.search_edit)

        layout.addLayout(header_layout)

        # Main content area
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Category tree
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("Categories")
        self.category_tree.setMaximumWidth(250)
        self.category_tree.itemClicked.connect(self._on_category_selected)

        # Settings content area
        self.content_stack = QStackedWidget()

        splitter.addWidget(self.category_tree)
        splitter.addWidget(self.content_stack)
        splitter.setSizes([250, 600])

        layout.addWidget(splitter)

        # Action buttons
        button_layout = QHBoxLayout()

        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_settings)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_settings)
        self.save_button.setDefault(True)

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def load_setting_definitions(self) -> None:
        """Load all setting definitions from the managers."""
        # Application settings
        self._add_app_settings()

        # Database settings
        self._add_database_settings()

        # Logging settings
        self._add_logging_settings()

        # Security settings
        self._add_security_settings()

        # API settings
        self._add_api_settings()

        # Plugin settings
        self._add_plugin_settings()

        # Monitoring settings
        self._add_monitoring_settings()

        # File settings
        self._add_file_settings()

        # Cloud settings
        self._add_cloud_settings()

        # Performance settings
        self._add_performance_settings()

        # Advanced settings
        self._add_advanced_settings()

        self._create_category_widgets()

    def _add_app_settings(self) -> None:
        """Add application-level settings."""
        settings = [
            SettingDefinition(
                key="app.name",
                name="Application Name",
                description="Name of the application",
                setting_type=SettingType.STRING,
                category=SettingCategory.APPLICATION,
                default_value="Qorzen",
                placeholder="Enter application name"
            ),
            SettingDefinition(
                key="app.version",
                name="Version",
                description="Application version",
                setting_type=SettingType.STRING,
                category=SettingCategory.APPLICATION,
                default_value="0.1.0",
                placeholder="x.y.z"
            ),
            SettingDefinition(
                key="app.environment",
                name="Environment",
                description="Runtime environment",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.APPLICATION,
                default_value="development",
                choices=["development", "testing", "staging", "production"]
            ),
            SettingDefinition(
                key="app.debug",
                name="Debug Mode",
                description="Enable debug mode for development",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.APPLICATION,
                default_value=True
            ),
            SettingDefinition(
                key="app.ui.enabled",
                name="UI Enabled",
                description="Enable the user interface",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.UI,
                default_value=True
            ),
            SettingDefinition(
                key="app.ui.theme",
                name="UI Theme",
                description="User interface theme",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.UI,
                default_value="light",
                choices=["light", "dark", "system"]
            ),
            SettingDefinition(
                key="app.ui.language",
                name="Language",
                description="Interface language",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.UI,
                default_value="en",
                choices=["en", "es", "fr", "de", "zh", "ja"]
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_database_settings(self) -> None:
        """Add database-related settings."""
        settings = [
            SettingDefinition(
                key="database.enabled",
                name="Database Enabled",
                description="Enable database connections",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.DATABASE,
                default_value=True
            ),
            SettingDefinition(
                key="database.type",
                name="Database Type",
                description="Type of database to use",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.DATABASE,
                default_value="postgresql",
                choices=["postgresql", "mysql", "sqlite", "oracle", "mssql"]
            ),
            SettingDefinition(
                key="database.host",
                name="Database Host",
                description="Database server hostname or IP address",
                setting_type=SettingType.STRING,
                category=SettingCategory.DATABASE,
                default_value="localhost",
                placeholder="localhost or IP address"
            ),
            SettingDefinition(
                key="database.port",
                name="Database Port",
                description="Database server port number",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.DATABASE,
                default_value=5432,
                min_value=1,
                max_value=65535
            ),
            SettingDefinition(
                key="database.name",
                name="Database Name",
                description="Name of the database to connect to",
                setting_type=SettingType.STRING,
                category=SettingCategory.DATABASE,
                default_value="qorzen",
                placeholder="Database name"
            ),
            SettingDefinition(
                key="database.user",
                name="Database User",
                description="Username for database authentication",
                setting_type=SettingType.STRING,
                category=SettingCategory.DATABASE,
                default_value="postgres",
                placeholder="Username"
            ),
            SettingDefinition(
                key="database.password",
                name="Database Password",
                description="Password for database authentication",
                setting_type=SettingType.PASSWORD,
                category=SettingCategory.DATABASE,
                default_value="",
                placeholder="Password"
            ),
            SettingDefinition(
                key="database.pool_size",
                name="Connection Pool Size",
                description="Number of connections to maintain in the pool",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.DATABASE,
                default_value=5,
                min_value=1,
                max_value=100
            ),
            SettingDefinition(
                key="database.max_overflow",
                name="Max Pool Overflow",
                description="Maximum number of connections beyond pool size",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.DATABASE,
                default_value=10,
                min_value=0,
                max_value=100
            ),
            SettingDefinition(
                key="database.pool_recycle",
                name="Pool Recycle Time",
                description="Time in seconds to recycle connections",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.DATABASE,
                default_value=3600,
                min_value=300,
                max_value=86400
            ),
            SettingDefinition(
                key="database.echo",
                name="Echo SQL",
                description="Log all SQL statements for debugging",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.DATABASE,
                default_value=False
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_logging_settings(self) -> None:
        """Add logging-related settings."""
        settings = [
            SettingDefinition(
                key="logging.level",
                name="Log Level",
                description="Minimum level of log messages to capture",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.LOGGING,
                default_value="INFO",
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            ),
            SettingDefinition(
                key="logging.format",
                name="Log Format",
                description="Format for log messages",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.LOGGING,
                default_value="json",
                choices=["json", "text"]
            ),
            SettingDefinition(
                key="logging.file.enabled",
                name="File Logging Enabled",
                description="Enable logging to file",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.LOGGING,
                default_value=True
            ),
            SettingDefinition(
                key="logging.file.path",
                name="Log File Path",
                description="Path to the log file",
                setting_type=SettingType.PATH,
                category=SettingCategory.LOGGING,
                default_value="logs/qorzen.log",
                file_filter="Log Files (*.log);;All Files (*)"
            ),
            SettingDefinition(
                key="logging.file.rotation_size",
                name="Log File Rotation",
                description="Log file rotation size",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.LOGGING,
                default_value=10,
                placeholder="e.g., 10 (MB)"
            ),
            SettingDefinition(
                key="logging.file.retention_size",
                name="Log File Retention",
                description="How long to keep log files",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.LOGGING,
                default_value=30, # days
                placeholder="e.g., 30 (days)"
            ),
            SettingDefinition(
                key="logging.console.enabled",
                name="Console Logging Enabled",
                description="Enable logging to console",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.LOGGING,
                default_value=True
            ),
            SettingDefinition(
                key="logging.console.level",
                name="Console Log Level",
                description="Minimum level for console logging",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.LOGGING,
                default_value="INFO",
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_security_settings(self) -> None:
        """Add security-related settings."""
        settings = [
            SettingDefinition(
                key="security.jwt.secret",
                name="JWT Secret Key",
                description="Secret key for JWT token signing",
                setting_type=SettingType.PASSWORD,
                category=SettingCategory.SECURITY,
                default_value="your-secret-key-change-in-production",
                requires_restart=True
            ),
            SettingDefinition(
                key="security.jwt.algorithm",
                name="JWT Algorithm",
                description="Algorithm used for JWT token signing",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.SECURITY,
                default_value="HS256",
                choices=["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
            ),
            SettingDefinition(
                key="security.jwt.access_token_expire_minutes",
                name="Access Token Expiry",
                description="Access token expiration time in minutes",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.SECURITY,
                default_value=30,
                min_value=5,
                max_value=1440
            ),
            SettingDefinition(
                key="security.jwt.refresh_token_expire_days",
                name="Refresh Token Expiry",
                description="Refresh token expiration time in days",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.SECURITY,
                default_value=7,
                min_value=1,
                max_value=365
            ),
            SettingDefinition(
                key="security.password_policy.min_length",
                name="Minimum Password Length",
                description="Minimum required password length",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.SECURITY,
                default_value=8,
                min_value=4,
                max_value=128
            ),
            SettingDefinition(
                key="security.password_policy.require_uppercase",
                name="Require Uppercase",
                description="Require at least one uppercase letter",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.SECURITY,
                default_value=True
            ),
            SettingDefinition(
                key="security.password_policy.require_lowercase",
                name="Require Lowercase",
                description="Require at least one lowercase letter",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.SECURITY,
                default_value=True
            ),
            SettingDefinition(
                key="security.password_policy.require_digit",
                name="Require Digit",
                description="Require at least one numeric digit",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.SECURITY,
                default_value=True
            ),
            SettingDefinition(
                key="security.password_policy.require_special",
                name="Require Special Character",
                description="Require at least one special character",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.SECURITY,
                default_value=True
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_api_settings(self) -> None:
        """Add API-related settings."""
        settings = [
            SettingDefinition(
                key="api.enabled",
                name="API Enabled",
                description="Enable the REST API server",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.API,
                default_value=True,
                requires_restart=True
            ),
            SettingDefinition(
                key="api.host",
                name="API Host",
                description="Host address for the API server",
                setting_type=SettingType.STRING,
                category=SettingCategory.API,
                default_value="0.0.0.0",
                placeholder="0.0.0.0 or localhost",
                requires_restart=True
            ),
            SettingDefinition(
                key="api.port",
                name="API Port",
                description="Port number for the API server",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.API,
                default_value=8000,
                min_value=1024,
                max_value=65535,
                requires_restart=True
            ),
            SettingDefinition(
                key="api.workers",
                name="API Workers",
                description="Number of worker processes for the API",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.API,
                default_value=4,
                min_value=1,
                max_value=32,
                requires_restart=True
            ),
            SettingDefinition(
                key="api.cors.origins",
                name="CORS Origins",
                description="Allowed origins for CORS requests",
                setting_type=SettingType.JSON,
                category=SettingCategory.API,
                default_value=["*"],
                requires_restart=True
            ),
            SettingDefinition(
                key="api.cors.methods",
                name="CORS Methods",
                description="Allowed HTTP methods for CORS",
                setting_type=SettingType.JSON,
                category=SettingCategory.API,
                default_value=["*"],
                requires_restart=True
            ),
            SettingDefinition(
                key="api.cors.headers",
                name="CORS Headers",
                description="Allowed headers for CORS requests",
                setting_type=SettingType.JSON,
                category=SettingCategory.API,
                default_value=["*"],
                requires_restart=True
            ),
            SettingDefinition(
                key="api.rate_limit.enabled",
                name="Rate Limiting Enabled",
                description="Enable API rate limiting",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.API,
                default_value=True
            ),
            SettingDefinition(
                key="api.rate_limit.requests_per_minute",
                name="Requests Per Minute",
                description="Maximum requests per minute per client",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.API,
                default_value=100,
                min_value=1,
                max_value=10000
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_plugin_settings(self) -> None:
        """Add plugin-related settings."""
        settings = [
            SettingDefinition(
                key="plugins.directory",
                name="Plugin Directory",
                description="Directory containing plugins",
                setting_type=SettingType.PATH,
                category=SettingCategory.PLUGINS,
                default_value="plugins",
                requires_restart=True
            ),
            SettingDefinition(
                key="plugins.autoload",
                name="Auto-load Plugins",
                description="Automatically load enabled plugins at startup",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.PLUGINS,
                default_value=True
            ),
            SettingDefinition(
                key="plugins.enabled",
                name="Enabled Plugins",
                description="List of enabled plugin names",
                setting_type=SettingType.JSON,
                category=SettingCategory.PLUGINS,
                default_value=[]
            ),
            SettingDefinition(
                key="plugins.disabled",
                name="Disabled Plugins",
                description="List of disabled plugin names",
                setting_type=SettingType.JSON,
                category=SettingCategory.PLUGINS,
                default_value=[]
            ),
            SettingDefinition(
                key="plugins.isolation.default_level",
                name="Default Isolation Level",
                description="Default isolation level for plugins",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.PLUGINS,
                default_value="thread",
                choices=["none", "thread", "process"],
                is_advanced=True
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_monitoring_settings(self) -> None:
        """Add monitoring-related settings."""
        settings = [
            SettingDefinition(
                key="monitoring.enabled",
                name="Monitoring Enabled",
                description="Enable system monitoring",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.MONITORING,
                default_value=True
            ),
            SettingDefinition(
                key="monitoring.prometheus.enabled",
                name="Prometheus Enabled",
                description="Enable Prometheus metrics endpoint",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.MONITORING,
                default_value=True
            ),
            SettingDefinition(
                key="monitoring.prometheus.port",
                name="Prometheus Port",
                description="Port for Prometheus metrics endpoint",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.MONITORING,
                default_value=9090,
                min_value=1024,
                max_value=65535
            ),
            SettingDefinition(
                key="monitoring.alert_thresholds.cpu_percent",
                name="CPU Alert Threshold",
                description="CPU usage percentage threshold for alerts",
                setting_type=SettingType.FLOAT,
                category=SettingCategory.MONITORING,
                default_value=80.0,
                min_value=10.0,
                max_value=95.0
            ),
            SettingDefinition(
                key="monitoring.alert_thresholds.memory_percent",
                name="Memory Alert Threshold",
                description="Memory usage percentage threshold for alerts",
                setting_type=SettingType.FLOAT,
                category=SettingCategory.MONITORING,
                default_value=80.0,
                min_value=10.0,
                max_value=95.0
            ),
            SettingDefinition(
                key="monitoring.alert_thresholds.disk_percent",
                name="Disk Alert Threshold",
                description="Disk usage percentage threshold for alerts",
                setting_type=SettingType.FLOAT,
                category=SettingCategory.MONITORING,
                default_value=90.0,
                min_value=10.0,
                max_value=98.0
            ),
            SettingDefinition(
                key="monitoring.metrics_interval_seconds",
                name="Metrics Collection Interval",
                description="Interval in seconds for metrics collection",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.MONITORING,
                default_value=10,
                min_value=1,
                max_value=300
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_file_settings(self) -> None:
        """Add file management settings."""
        settings = [
            SettingDefinition(
                key="files.base_directory",
                name="Base Directory",
                description="Base directory for application data",
                setting_type=SettingType.PATH,
                category=SettingCategory.FILES,
                default_value="data",
                requires_restart=True
            ),
            SettingDefinition(
                key="files.temp_directory",
                name="Temporary Directory",
                description="Directory for temporary files",
                setting_type=SettingType.PATH,
                category=SettingCategory.FILES,
                default_value="data/temp",
                requires_restart=True
            ),
            SettingDefinition(
                key="files.plugin_data_directory",
                name="Plugin Data Directory",
                description="Directory for plugin data storage",
                setting_type=SettingType.PATH,
                category=SettingCategory.FILES,
                default_value="data/plugins",
                requires_restart=True
            ),
            SettingDefinition(
                key="files.backup_directory",
                name="Backup Directory",
                description="Directory for backup files",
                setting_type=SettingType.PATH,
                category=SettingCategory.FILES,
                default_value="data/backups",
                requires_restart=True
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_cloud_settings(self) -> None:
        """Add cloud provider settings."""
        settings = [
            SettingDefinition(
                key="cloud.provider",
                name="Cloud Provider",
                description="Cloud service provider",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.CLOUD,
                default_value="none",
                choices=["none", "aws", "azure", "gcp"]
            ),
            SettingDefinition(
                key="cloud.storage.enabled",
                name="Cloud Storage Enabled",
                description="Enable cloud storage integration",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.CLOUD,
                default_value=False
            ),
            SettingDefinition(
                key="cloud.storage.type",
                name="Storage Type",
                description="Type of cloud storage to use",
                setting_type=SettingType.CHOICE,
                category=SettingCategory.CLOUD,
                default_value="local",
                choices=["local", "s3", "azure_blob", "gcp_storage"]
            ),
            SettingDefinition(
                key="cloud.storage.bucket",
                name="Storage Bucket",
                description="Name of the storage bucket/container",
                setting_type=SettingType.STRING,
                category=SettingCategory.CLOUD,
                default_value="",
                placeholder="bucket-name"
            ),
            SettingDefinition(
                key="cloud.storage.prefix",
                name="Storage Prefix",
                description="Prefix for stored files",
                setting_type=SettingType.STRING,
                category=SettingCategory.CLOUD,
                default_value="",
                placeholder="folder/prefix"
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_performance_settings(self) -> None:
        """Add performance-related settings."""
        settings = [
            SettingDefinition(
                key="thread_pool.worker_threads",
                name="Worker Threads",
                description="Number of worker threads for CPU-bound tasks",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.PERFORMANCE,
                default_value=4,
                min_value=1,
                max_value=32,
                requires_restart=True
            ),
            SettingDefinition(
                key="thread_pool.io_threads",
                name="I/O Threads",
                description="Number of threads for I/O-bound operations",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.PERFORMANCE,
                default_value=8,
                min_value=1,
                max_value=64,
                requires_restart=True
            ),
            SettingDefinition(
                key="thread_pool.process_workers",
                name="Process Workers",
                description="Number of process workers for parallel processing",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.PERFORMANCE,
                default_value=2,
                min_value=1,
                max_value=16,
                requires_restart=True
            ),
            SettingDefinition(
                key="event_bus_manager.thread_pool_size",
                name="Event Bus Thread Pool",
                description="Thread pool size for event processing",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.PERFORMANCE,
                default_value=4,
                min_value=1,
                max_value=16,
                requires_restart=True
            ),
            SettingDefinition(
                key="event_bus_manager.max_queue_size",
                name="Event Queue Size",
                description="Maximum size of the event queue",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.PERFORMANCE,
                default_value=1000,
                min_value=100,
                max_value=10000,
                requires_restart=True
            ),
            SettingDefinition(
                key="event_bus_manager.publish_timeout",
                name="Event Publish Timeout",
                description="Timeout in seconds for event publishing",
                setting_type=SettingType.FLOAT,
                category=SettingCategory.PERFORMANCE,
                default_value=5.0,
                min_value=1.0,
                max_value=60.0
            ),
            SettingDefinition(
                key="tasks.max_concurrent_tasks",
                name="Max Concurrent Tasks",
                description="Maximum number of concurrent tasks",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.PERFORMANCE,
                default_value=20,
                min_value=1,
                max_value=100
            ),
            SettingDefinition(
                key="tasks.default_timeout",
                name="Default Task Timeout",
                description="Default timeout for tasks in seconds",
                setting_type=SettingType.FLOAT,
                category=SettingCategory.PERFORMANCE,
                default_value=300.0,
                min_value=10.0,
                max_value=3600.0
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _add_advanced_settings(self) -> None:
        """Add advanced/expert settings."""
        settings = [
            SettingDefinition(
                key="thread_pool.enable_process_pool",
                name="Enable Process Pool",
                description="Enable process pool for CPU-intensive tasks",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.ADVANCED,
                default_value=True,
                is_advanced=True,
                requires_restart=True
            ),
            SettingDefinition(
                key="database.non_blocking",
                name="Non-blocking Database",
                description="Use non-blocking database operations",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.ADVANCED,
                default_value=True,
                is_advanced=True,
                requires_restart=True
            ),
            SettingDefinition(
                key="logging.elk.enabled",
                name="ELK Stack Logging",
                description="Enable logging to ELK stack",
                setting_type=SettingType.BOOLEAN,
                category=SettingCategory.ADVANCED,
                default_value=False,
                is_advanced=True
            ),
            SettingDefinition(
                key="logging.elk.host",
                name="ELK Host",
                description="Elasticsearch host for ELK logging",
                setting_type=SettingType.STRING,
                category=SettingCategory.ADVANCED,
                default_value="localhost",
                is_advanced=True
            ),
            SettingDefinition(
                key="logging.elk.port",
                name="ELK Port",
                description="Elasticsearch port for ELK logging",
                setting_type=SettingType.INTEGER,
                category=SettingCategory.ADVANCED,
                default_value=9200,
                min_value=1,
                max_value=65535,
                is_advanced=True
            ),
            SettingDefinition(
                key="logging.elk.index",
                name="ELK Index",
                description="Elasticsearch index name for logs",
                setting_type=SettingType.STRING,
                category=SettingCategory.ADVANCED,
                default_value="qorzen",
                is_advanced=True
            )
        ]

        for setting in settings:
            self.setting_definitions[setting.key] = setting

    def _create_category_widgets(self) -> None:
        """Create UI widgets for each category."""
        # Group settings by category
        categories: Dict[SettingCategory, List[SettingDefinition]] = {}
        for setting_def in self.setting_definitions.values():
            if setting_def.category not in categories:
                categories[setting_def.category] = []
            categories[setting_def.category].append(setting_def)

        # Create category tree items and content widgets
        for category, settings in categories.items():
            # Create tree item
            tree_item = QTreeWidgetItem([category.value])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, category)
            self.category_tree.addTopLevelItem(tree_item)

            # Create content widget
            content_widget = self._create_category_content(category, settings)
            self.category_widgets[category] = content_widget
            self.content_stack.addWidget(content_widget)

        # Select first category by default
        if self.category_tree.topLevelItemCount() > 0:
            self.category_tree.setCurrentItem(self.category_tree.topLevelItem(0))
            self._on_category_selected(self.category_tree.topLevelItem(0), 0)

    def _create_category_content(self, category: SettingCategory, settings: List[SettingDefinition]) -> QWidget:
        """Create content widget for a category."""
        widget = QWidget()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)

        # Category header
        header = QLabel(f"{category.value} Settings")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # Group settings (basic and advanced)
        basic_settings = [s for s in settings if not s.is_advanced]
        advanced_settings = [s for s in settings if s.is_advanced]

        if basic_settings:
            basic_group = self._create_settings_group("Basic Settings", basic_settings)
            layout.addWidget(basic_group)

        if advanced_settings:
            advanced_group = self._create_settings_group("Advanced Settings", advanced_settings)
            layout.addWidget(advanced_group)

        layout.addStretch()

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        main_layout = QVBoxLayout(widget)
        main_layout.addWidget(scroll_area)

        return widget

    def _create_settings_group(self, title: str, settings: List[SettingDefinition]) -> QGroupBox:
        """Create a group box for settings."""
        group = QGroupBox(title)
        layout = QFormLayout(group)

        for setting_def in sorted(settings, key=lambda s: s.name):
            # Create setting widget
            widget = self._create_setting_widget(setting_def)
            self.setting_widgets[setting_def.key] = widget

            # Create label with tooltip
            label = QLabel(setting_def.name)
            if setting_def.tooltip:
                label.setToolTip(setting_def.tooltip)
            elif setting_def.description:
                label.setToolTip(setting_def.description)

            # Add restart indicator
            if setting_def.requires_restart:
                restart_label = QLabel(" (restart required)")
                restart_label.setStyleSheet("color: orange; font-style: italic;")
                label_layout = QHBoxLayout()
                label_layout.addWidget(label)
                label_layout.addWidget(restart_label)
                label_layout.addStretch()
                label_widget = QWidget()
                label_widget.setLayout(label_layout)
                layout.addRow(label_widget, widget)
            else:
                layout.addRow(label, widget)

            # Connect value changed signal
            widget.valueChanged.connect(
                lambda value, key=setting_def.key: self._on_setting_changed(key, value)
            )

        return group

    def _create_setting_widget(self, setting_def: SettingDefinition) -> SettingWidget:
        """Create appropriate widget for a setting type."""
        if setting_def.setting_type == SettingType.BOOLEAN:
            return BooleanSettingWidget(setting_def)
        elif setting_def.setting_type == SettingType.INTEGER:
            return IntegerSettingWidget(setting_def)
        elif setting_def.setting_type == SettingType.FLOAT:
            return FloatSettingWidget(setting_def)
        elif setting_def.setting_type == SettingType.CHOICE:
            return ChoiceSettingWidget(setting_def)
        elif setting_def.setting_type == SettingType.PATH:
            return PathSettingWidget(setting_def)
        elif setting_def.setting_type in (SettingType.LIST, SettingType.DICT, SettingType.JSON):
            return JsonSettingWidget(setting_def)
        else:  # STRING, PASSWORD
            return StringSettingWidget(setting_def)

    async def load_current_values(self) -> None:
        """Load current values from configuration."""
        if not self.config_manager:
            return

        for key, setting_def in self.setting_definitions.items():
            try:
                current_value = await self.config_manager.get(key, setting_def.default_value)
                setting_def.current_value = current_value

                # Update widget if it exists
                if key in self.setting_widgets:
                    self.setting_widgets[key].set_value(current_value)

            except Exception as e:
                self.logger.warning(f"Failed to load setting {key}: {e}")
                setting_def.current_value = setting_def.default_value

    def _on_category_selected(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle category selection."""
        category = item.data(0, Qt.ItemDataRole.UserRole)
        if category in self.category_widgets:
            self.content_stack.setCurrentWidget(self.category_widgets[category])

    def _on_search_changed(self, text: str) -> None:
        """Handle search text changes."""
        self.search_timer.stop()
        self.search_timer.start(300)  # Debounce search

    def _perform_search(self) -> None:
        """Perform the actual search filtering."""
        search_text = self.search_edit.text().lower().strip()

        if not search_text:
            # Show all categories
            for i in range(self.category_tree.topLevelItemCount()):
                self.category_tree.topLevelItem(i).setHidden(False)
            return

        # Filter categories and settings
        for i in range(self.category_tree.topLevelItemCount()):
            item = self.category_tree.topLevelItem(i)
            category = item.data(0, Qt.ItemDataRole.UserRole)

            # Check if category name matches
            category_matches = search_text in category.lower()

            # Check if any settings in this category match
            settings_match = False
            if category in self.category_widgets:
                for key, setting_def in self.setting_definitions.items():
                    if setting_def.category == category:
                        if (search_text in setting_def.name.lower() or
                                search_text in setting_def.description.lower() or
                                search_text in str(setting_def.current_value).lower() or
                                search_text in key.lower()):
                            settings_match = True
                            break

            # Show/hide category based on matches
            item.setHidden(not (category_matches or settings_match))

    def _on_setting_changed(self, key: str, value: Any) -> None:
        """Handle setting value changes."""
        if key in self.setting_definitions:
            self.setting_definitions[key].current_value = value
            self.settingChanged.emit(key, value)

    def _reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for key, setting_def in self.setting_definitions.items():
                setting_def.current_value = setting_def.default_value
                if key in self.setting_widgets:
                    self.setting_widgets[key].set_value(setting_def.default_value)

    def _apply_settings(self) -> None:
        """Apply current settings without saving to file."""
        asyncio.create_task(self._apply_settings_async())

    async def _apply_settings_async(self) -> None:
        """Apply settings asynchronously."""
        try:
            for key, setting_def in self.setting_definitions.items():
                if key in self.setting_widgets:
                    # Validate setting
                    widget = self.setting_widgets[key]
                    is_valid, error_msg = widget.validate()
                    if not is_valid:
                        QMessageBox.warning(
                            self, "Validation Error",
                            f"Invalid value for {setting_def.name}: {error_msg}"
                        )
                        return

                    # Get current value from widget
                    current_value = widget.get_value()
                    setting_def.current_value = current_value

                    # Apply to config manager (without saving to file)
                    try:
                        await self.config_manager.set(key, current_value)
                    except Exception as e:
                        self.logger.error(f"Failed to apply setting {key}: {e}")

            QMessageBox.information(self, "Settings Applied", "Settings have been applied successfully.")

        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")

    def _save_settings(self) -> None:
        """Save current settings to configuration file."""
        asyncio.create_task(self._save_settings_async())

    async def _save_settings_async(self) -> None:
        """Save settings asynchronously."""
        try:
            # First apply settings
            await self._apply_settings_async()

            # Check for settings that require restart
            restart_required = []
            for key, setting_def in self.setting_definitions.items():
                if setting_def.requires_restart and key in self.setting_widgets:
                    widget = self.setting_widgets[key]
                    if widget.get_value() != setting_def.default_value:
                        restart_required.append(setting_def.name)

            # Show restart warning if needed
            if restart_required:
                restart_list = "\n".join(f"• {name}" for name in restart_required)
                QMessageBox.information(
                    self, "Restart Required",
                    f"The following settings require an application restart to take effect:\n\n{restart_list}"
                )

            self.settingsSaved.emit()
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")


# Static values that should be extracted to configuration:

"""
EXTRACTED VALUES FOR CONFIGURATION:

From various manager files, the following hardcoded values should be made configurable:

1. **EventBusManager** (qorzen_stripped/core/event_bus_manager.py):
   - Line ~25: `_max_queue_size: int = 1000` → `event_bus_manager.max_queue_size`
   - Line ~26: `_publish_timeout: float = 5.0` → `event_bus_manager.publish_timeout`
   - Line ~41: `thread_pool_size = event_bus_config.get('thread_pool_size', 4)` → `event_bus_manager.thread_pool_size`

2. **ConcurrencyManager** (qorzen_stripped/core/concurrency_manager.py):
   - Line ~25: `_max_workers: int = 4` → `thread_pool.worker_threads`
   - Line ~26: `_max_io_workers: int = 8` → `thread_pool.io_threads`
   - Line ~27: `_max_process_workers: int = 2` → `thread_pool.process_workers`

3. **ResourceMonitoringManager** (qorzen_stripped/core/resource_monitoring_manager.py):
   - Line ~35: `_alert_thresholds: Dict[str, float] = {'cpu_percent': 80.0, 'memory_percent': 80.0, 'disk_percent': 90.0}` → `monitoring.alert_thresholds.*`
   - Line ~38: `_metrics_interval_seconds = 10` → `monitoring.metrics_interval_seconds`

4. **SecurityManager** (qorzen_stripped/core/security_manager.py):
   - Line ~45: `bcrypt__rounds=12` → `security.password_policy.bcrypt_rounds`
   - Line ~54: `_access_token_expire_minutes = 30` → `security.jwt.access_token_expire_minutes`
   - Line ~55: `_refresh_token_expire_days = 7` → `security.jwt.refresh_token_expire_days`

5. **TaskManager** (qorzen_stripped/core/task_manager.py):
   - Line ~65: `_max_concurrent_tasks = 20` → `tasks.max_concurrent_tasks`
   - Line ~66: `_keep_completed_tasks = 100` → `tasks.keep_completed_tasks`
   - Line ~67: `_task_timeout = 300.0` → `tasks.default_timeout`

6. **DatabaseManager** (qorzen_stripped/core/database_manager.py):
   - Line ~85: `_pool_size: int = 5` → `database.pool_size`
   - Line ~86: `_max_overflow: int = 10` → `database.max_overflow`
   - Line ~87: `_pool_recycle: int = 3600` → `database.pool_recycle`

7. **APIManager** (qorzen_stripped/core/api_manager.py):
   - Line ~125: `_host = '0.0.0.0'` → `api.host`
   - Line ~126: `_port = 8000` → `api.port`
   - Line ~127: `_workers = 4` → `api.workers`
   - Line ~131: `_rate_limit_requests = 100` → `api.rate_limit.requests_per_minute`

Replace these hardcoded values with calls to `await self._config_manager.get()` with the suggested configuration keys.
"""