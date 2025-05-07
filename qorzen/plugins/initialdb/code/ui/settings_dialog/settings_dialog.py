from __future__ import annotations

"""
Settings dialog for the InitialDB application.

This module provides a comprehensive settings dialog with a tree view
for category navigation and specialized editors for different setting types.
"""

import os
from typing import Any, Dict, List, Optional, Set, cast

import structlog
from PyQt6.QtCore import QSettings, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFrame, QHBoxLayout,
    QLabel, QMessageBox, QPushButton, QSizePolicy, QSplitter,
    QVBoxLayout, QWidget
)

from ...config.settings import settings as app_settings
from .category_tree import CategoryTree
from .models import Setting, SettingType, SettingsCategory, SettingsRegistry
from .widgets import CategorySettingsWidget

logger = structlog.get_logger(__name__)


class SettingsDialog(QDialog):
    """Comprehensive settings dialog with category tree and settings panels."""

    settings_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the settings dialog.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(900, 600)

        # Initialize the registry and populate with settings
        self.registry = self._create_settings_registry()

        # Setup UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Select initial category
        if self.registry.categories:
            first_category = self.registry.categories[0]
            self.category_tree.select_category(first_category.id)

    def _setup_ui(self) -> None:
        """Set up the user interface for the dialog."""
        layout = QVBoxLayout(self)

        # Create splitter for tree and settings panel
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Category tree on the left
        self.category_tree = CategoryTree(self.registry)
        self.category_tree.setMinimumWidth(200)
        self.splitter.addWidget(self.category_tree)

        # Settings panel on the right
        self.settings_panel = QWidget()
        settings_layout = QVBoxLayout(self.settings_panel)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        # Header area
        self.header_widget = QWidget()
        header_layout = QVBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        self.category_title = QLabel()
        self.category_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.category_title)

        self.category_description = QLabel()
        self.category_description.setWordWrap(True)
        header_layout.addWidget(self.category_description)

        settings_layout.addWidget(self.header_widget)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        settings_layout.addWidget(separator)

        # Settings content
        self.settings_widget = CategorySettingsWidget()
        settings_layout.addWidget(self.settings_widget)

        self.splitter.addWidget(self.settings_panel)

        # Set initial sizes
        self.splitter.setSizes([250, 650])
        layout.addWidget(self.splitter)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Reset
        )

        # Connect button signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_settings)
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._reset_settings)

        layout.addWidget(self.button_box)

        # Track changes
        self.original_values: Dict[str, Any] = {}
        self.changed_values: Dict[str, Any] = {}

    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        self.category_tree.category_selected.connect(self._on_category_selected)
        self.settings_widget.value_changed.connect(self._on_setting_value_changed)

    def _create_settings_registry(self) -> SettingsRegistry:
        """
        Create and populate the settings registry with all application settings.

        Returns:
            The populated settings registry
        """
        registry = SettingsRegistry()

        # General category
        general = SettingsCategory(
            id="general",
            name="General",
            description="General application settings",
            icon_name="preferences-system",
        )

        general.add_setting(Setting(
            key="app_name",
            name="Application Name",
            description="Display name for the application",
            setting_type=SettingType.STRING,
            default_value="InitialDB",
            current_value=app_settings.get("app_name", "InitialDB"),
        ))

        general.add_setting(Setting(
            key="ui_refresh_interval_ms",
            name="UI Refresh Interval",
            description="Interval for refreshing UI components (milliseconds)",
            setting_type=SettingType.INT,
            default_value=500,
            current_value=app_settings.get("ui_refresh_interval_ms", 500),
            validator=lambda v: (v >= 100, "Refresh interval must be at least 100ms"),
        ))

        registry.add_category(general)

        # Database category
        database = SettingsCategory(
            id="database",
            name="Database",
            description="Database connection settings",
            icon_name="server-database",
        )

        db_types = [
            ("postgresql+asyncpg", "PostgreSQL"),
            ("mysql+aiomysql", "MySQL"),
            ("sqlite+aiosqlite", "SQLite"),
            ("mssql+aioodbc", "Microsoft SQL Server")
        ]

        database.add_setting(Setting(
            key="db_type",
            name="Database Type",
            description="Type of database to connect to",
            setting_type=SettingType.CHOICE,
            default_value="postgresql+asyncpg",
            current_value="postgresql+asyncpg",
            choices=db_types,
            restart_required=True,
        ))

        database.add_setting(Setting(
            key="db_host",
            name="Host",
            description="Database server hostname or IP address",
            setting_type=SettingType.STRING,
            default_value="localhost",
            current_value="localhost",
            restart_required=True,
        ))

        database.add_setting(Setting(
            key="db_port",
            name="Port",
            description="Database server port",
            setting_type=SettingType.INT,
            default_value=5432,
            current_value=5432,
            restart_required=True,
            validator=lambda v: (0 < v < 65536, "Port must be between 1 and 65535"),
        ))

        database.add_setting(Setting(
            key="db_name",
            name="Database Name",
            description="Name of the database",
            setting_type=SettingType.STRING,
            default_value="initialdb",
            current_value="initialdb",
            restart_required=True,
        ))

        database.add_setting(Setting(
            key="db_user",
            name="Username",
            description="Database username",
            setting_type=SettingType.STRING,
            default_value="initialdb",
            current_value="initialdb",
            restart_required=True,
        ))

        database.add_setting(Setting(
            key="db_password",
            name="Password",
            description="Database password",
            setting_type=SettingType.PASSWORD,
            default_value="",
            current_value="",
            restart_required=True,
        ))

        database.add_setting(Setting(
            key="query_limit",
            name="Query Result Limit",
            description="Maximum number of records to return in a query",
            setting_type=SettingType.INT,
            default_value=1000,
            current_value=app_settings.get("query_limit", 1000),
            validator=lambda v: (v > 0, "Limit must be greater than 0"),
        ))

        # Build full connection string from parts
        def validate_connection_string(value: str) -> tuple[bool, str]:
            if not value:
                return False, "Connection string cannot be empty"
            return True, ""

        database.add_setting(Setting(
            key="connection_string",
            name="Connection String",
            description="Full database connection string (advanced)",
            setting_type=SettingType.STRING,
            default_value=app_settings.get("connection_string", ""),
            current_value=app_settings.get("connection_string", ""),
            restart_required=True,
            validator=validate_connection_string,
            advanced=True,
        ))

        registry.add_category(database)

        # Update Settings
        updates = SettingsCategory(
            id="updates",
            name="Updates",
            description="Application update settings",
            icon_name="system-software-update",
        )

        updates.add_setting(Setting(
            key="update_url",
            name="Update Server URL",
            description="URL of the update server",
            setting_type=SettingType.STRING,
            default_value=app_settings.get("update_url", "http://localhost:5000"),
            current_value=app_settings.get("update_url", "http://localhost:5000"),
        ))

        updates.add_setting(Setting(
            key="update_check_automatically",
            name="Check for Updates Automatically",
            description="Automatically check for updates on startup",
            setting_type=SettingType.BOOL,
            default_value=True,
            current_value=app_settings.get("update_check_automatically", True),
        ))

        updates.add_setting(Setting(
            key="update_check_interval_hours",
            name="Update Check Interval",
            description="Hours between automatic update checks",
            setting_type=SettingType.INT,
            default_value=24,
            current_value=app_settings.get("update_check_interval_hours", 24),
            validator=lambda v: (v >= 1, "Interval must be at least 1 hour"),
        ))

        updates.add_setting(Setting(
            key="update_download_automatically",
            name="Download Updates Automatically",
            description="Automatically download available updates",
            setting_type=SettingType.BOOL,
            default_value=False,
            current_value=app_settings.get("update_download_automatically", False),
        ))

        updates.add_setting(Setting(
            key="update_install_automatically",
            name="Install Updates Automatically",
            description="Automatically install downloaded updates",
            setting_type=SettingType.BOOL,
            default_value=False,
            current_value=app_settings.get("update_install_automatically", False),
        ))

        updates.add_setting(Setting(
            key="update_allow_beta_updates",
            name="Allow Beta Updates",
            description="Include beta versions in update checks",
            setting_type=SettingType.BOOL,
            default_value=False,
            current_value=app_settings.get("update_allow_beta_updates", False),
        ))

        registry.add_category(updates)

        # Interface Settings
        interface = SettingsCategory(
            id="interface",
            name="Interface",
            description="User interface settings",
            icon_name="preferences-desktop",
        )

        # Theme settings
        theme = SettingsCategory(
            id="theme",
            name="Theme",
            description="Visual theme settings",
            icon_name="preferences-desktop-theme",
        )

        theme_choices = [
            ("system", "System Default"),
            ("light", "Light"),
            ("dark", "Dark"),
            ("custom", "Custom"),
        ]

        theme.add_setting(Setting(
            key="theme",
            name="Theme",
            description="Application visual theme",
            setting_type=SettingType.CHOICE,
            default_value="system",
            current_value=app_settings.get("theme", "system"),
            choices=theme_choices,
        ))

        theme.add_setting(Setting(
            key="custom_style_sheet",
            name="Custom Style Sheet",
            description="Custom CSS style sheet (for Custom theme)",
            setting_type=SettingType.STRING,
            default_value="",
            current_value=app_settings.get("custom_style_sheet", ""),
            advanced=True,
        ))

        theme.add_setting(Setting(
            key="accent_color",
            name="Accent Color",
            description="Main accent color for UI elements",
            setting_type=SettingType.COLOR,
            default_value="#1a73e8",
            current_value=app_settings.get("accent_color", "#1a73e8"),
        ))

        interface.add_subcategory(theme)

        # Layout settings
        layout = SettingsCategory(
            id="layout",
            name="Layout",
            description="Window layout settings",
            icon_name="preferences-desktop-display",
        )

        layout.add_setting(Setting(
            key="remember_window_size",
            name="Remember Window Size",
            description="Remember and restore the window size on startup",
            setting_type=SettingType.BOOL,
            default_value=True,
            current_value=app_settings.get("remember_window_size", True),
        ))

        layout.add_setting(Setting(
            key="remember_window_position",
            name="Remember Window Position",
            description="Remember and restore the window position on startup",
            setting_type=SettingType.BOOL,
            default_value=True,
            current_value=app_settings.get("remember_window_position", True),
        ))

        layout.add_setting(Setting(
            key="remember_window_state",
            name="Remember Window State",
            description="Remember and restore the window state (maximized, etc.) on startup",
            setting_type=SettingType.BOOL,
            default_value=True,
            current_value=app_settings.get("remember_window_state", True),
        ))

        interface.add_subcategory(layout)

        # Font settings
        fonts = SettingsCategory(
            id="fonts",
            name="Fonts",
            description="Application font settings",
            icon_name="preferences-desktop-font",
        )

        fonts.add_setting(Setting(
            key="application_font",
            name="Application Font",
            description="Main font for the application UI",
            setting_type=SettingType.FONT,
            default_value=QApplication.font().toString(),
            current_value=app_settings.get("application_font", QApplication.font().toString()),
        ))

        fonts.add_setting(Setting(
            key="code_font",
            name="Code Font",
            description="Font for code and monospaced text",
            setting_type=SettingType.FONT,
            default_value="Monospace, 10",
            current_value=app_settings.get("code_font", "Monospace, 10"),
        ))

        interface.add_subcategory(fonts)

        registry.add_category(interface)

        # Export/Import Settings
        export = SettingsCategory(
            id="export",
            name="Export/Import",
            description="Settings for data export and import",
            icon_name="document-save",
        )

        export.add_setting(Setting(
            key="default_exports_path",
            name="Default Export Directory",
            description="Default directory for exported files",
            setting_type=SettingType.PATH,
            default_value=str(app_settings.get("default_exports_path", "")),
            current_value=str(app_settings.get("default_exports_path", "")),
        ))

        export.add_setting(Setting(
            key="max_recent_exports",
            name="Max Recent Exports",
            description="Maximum number of recent exports to remember",
            setting_type=SettingType.INT,
            default_value=10,
            current_value=app_settings.get("max_recent_exports", 10),
            validator=lambda v: (v >= 0, "Value must be at least 0"),
        ))

        registry.add_category(export)

        # Query Settings
        queries = SettingsCategory(
            id="queries",
            name="Queries",
            description="Settings for database queries",
            icon_name="edit-find",
        )

        queries.add_setting(Setting(
            key="max_recent_queries",
            name="Max Recent Queries",
            description="Maximum number of recent queries to remember",
            setting_type=SettingType.INT,
            default_value=20,
            current_value=app_settings.get("max_recent_queries", 20),
            validator=lambda v: (v >= 0, "Value must be at least 0"),
        ))

        queries.add_setting(Setting(
            key="auto_execute_on_filter_change",
            name="Auto-Execute on Filter Change",
            description="Automatically execute queries when filters change",
            setting_type=SettingType.BOOL,
            default_value=False,
            current_value=app_settings.get("auto_execute_on_filter_change", False),
        ))

        registry.add_category(queries)

        # Advanced Settings
        advanced = SettingsCategory(
            id="advanced",
            name="Advanced",
            description="Advanced application settings",
            icon_name="preferences-system-advanced",
        )

        advanced.add_setting(Setting(
            key="logging_level",
            name="Logging Level",
            description="Detail level for application logs",
            setting_type=SettingType.CHOICE,
            default_value="INFO",
            current_value=app_settings.get("logging_level", "INFO"),
            choices=[
                ("DEBUG", "Debug"),
                ("INFO", "Info"),
                ("WARNING", "Warning"),
                ("ERROR", "Error"),
                ("CRITICAL", "Critical"),
            ],
        ))

        advanced.add_setting(Setting(
            key="log_file_path",
            name="Log File Path",
            description="Path to the application log file",
            setting_type=SettingType.PATH,
            default_value=os.path.expanduser("~/initialdb.log"),
            current_value=app_settings.get("log_file_path", os.path.expanduser("~/initialdb.log")),
        ))

        advanced.add_setting(Setting(
            key="developer_mode",
            name="Developer Mode",
            description="Enable developer features",
            setting_type=SettingType.BOOL,
            default_value=False,
            current_value=app_settings.get("developer_mode", False),
        ))

        registry.add_category(advanced)

        return registry

    def _on_category_selected(self, category_id: str) -> None:
        """
        Handle category selection in the tree view.

        Args:
            category_id: The ID of the selected category
        """
        category = self.registry.find_category(category_id)
        if not category:
            return

        # Update header
        self.category_title.setText(category.name)
        self.category_description.setText(category.description)

        # Store original values before displaying new category
        self._store_current_values()

        # Set settings for this category
        self.settings_widget.set_settings(category.settings)

        # Restore changed values if we've visited this category before
        changed_values = {k: v for k, v in self.changed_values.items()
                          if k in [s.key for s in category.settings]}
        if changed_values:
            self.settings_widget.set_values(changed_values)

    def _on_setting_value_changed(self, key: str, value: Any) -> None:
        """
        Handle setting value changes.

        Args:
            key: The setting key
            value: The new value
        """
        # Store the changed value
        self.changed_values[key] = value

        # Enable apply button if there are changes
        apply_btn = self.button_box.button(QDialogButtonBox.StandardButton.Apply)
        apply_btn.setEnabled(bool(self.changed_values))

    def _store_current_values(self) -> None:
        """Store the current values from the settings widget."""
        for key, value in self.settings_widget.get_values().items():
            if key not in self.original_values:
                # Only store the first time we see this key
                setting = self.registry.get_setting(key)
                if setting:
                    self.original_values[key] = setting.current_value

            # Update the changed value
            self.changed_values[key] = value

    def _apply_settings(self) -> None:
        """Apply the changed settings."""
        # Validate all settings
        if not self.settings_widget.validate_all():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Some settings have invalid values. Please correct them before applying.",
                QMessageBox.StandardButton.Ok
            )
            return

        # Store the current panel's values
        self._store_current_values()

        # Apply changes to the application settings
        restart_required = False
        for key, value in self.changed_values.items():
            setting = self.registry.get_setting(key)
            if setting:
                app_settings.set(key, value)
                setting.current_value = value
                restart_required = restart_required or setting.restart_required

        # Clear changed values
        self.changed_values.clear()

        # Disable apply button
        apply_btn = self.button_box.button(QDialogButtonBox.StandardButton.Apply)
        apply_btn.setEnabled(False)

        # Emit settings changed signal
        self.settings_changed.emit()

        # Show restart message if needed
        if restart_required:
            QMessageBox.information(
                self,
                "Restart Required",
                "Some of the changed settings require a restart to take effect.",
                QMessageBox.StandardButton.Ok
            )

    def _reset_settings(self) -> None:
        """Reset the current category's settings to their default values."""
        current_category = None
        selected_items = self.category_tree.tree.selectedItems()
        if selected_items:
            category_id = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            current_category = self.registry.find_category(category_id)

        if not current_category:
            return

        # Confirm reset
        result = QMessageBox.question(
            self,
            "Reset Settings",
            f"Reset all settings in '{current_category.name}' to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        # Reset to defaults
        reset_values = {}
        for setting in current_category.settings:
            reset_values[setting.key] = setting.default_value
            self.changed_values[setting.key] = setting.default_value

        # Update the UI
        self.settings_widget.set_values(reset_values)

        # Enable apply button
        apply_btn = self.button_box.button(QDialogButtonBox.StandardButton.Apply)
        apply_btn.setEnabled(True)

    def accept(self) -> None:
        """Handle the dialog acceptance (OK button)."""
        # Apply any pending changes
        self._apply_settings()

        # Close the dialog
        super().accept()