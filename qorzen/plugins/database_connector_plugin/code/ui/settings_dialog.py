from __future__ import annotations

"""
Settings dialog for the Database Connector Plugin.

This module provides a dialog for configuring plugin settings, including
database connections for storing history and validation data.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox, QTabWidget,
    QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem,
    QMessageBox, QComboBox, QStackedWidget, QFileDialog
)

from ..models import PluginSettings


class SettingsDialog(QDialog):
    """Dialog for configuring plugin settings."""

    def __init__(self, plugin: Any, parent: Optional[QWidget] = None) -> None:
        """Initialize the settings dialog.

        Args:
            plugin: The database connector plugin
            parent: Parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._settings = self._plugin._settings
        self._init_ui()
        self.setWindowTitle('Database Connector Settings')

        # Load connections for the history/validation database selection
        self._load_connections()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)

        main_layout = QVBoxLayout(self)

        # Main settings
        general_group = QGroupBox('General Settings')
        general_layout = QFormLayout(general_group)

        self._max_rows_spin = QSpinBox()
        self._max_rows_spin.setRange(100, 1000000)
        self._max_rows_spin.setSingleStep(1000)
        self._max_rows_spin.setValue(self._settings.max_result_rows if self._settings else 10000)

        self._history_limit_spin = QSpinBox()
        self._history_limit_spin.setRange(10, 1000)
        self._history_limit_spin.setValue(self._settings.query_history_limit if self._settings else 100)

        self._auto_save_check = QCheckBox()
        self._auto_save_check.setChecked(self._settings.auto_save_queries if self._settings else True)

        self._syntax_highlighting_check = QCheckBox()
        self._syntax_highlighting_check.setChecked(self._settings.syntax_highlighting if self._settings else True)

        general_layout.addRow('Maximum result rows:', self._max_rows_spin)
        general_layout.addRow('Query history limit:', self._history_limit_spin)
        general_layout.addRow('Automatically save queries:', self._auto_save_check)
        general_layout.addRow('Enable syntax highlighting:', self._syntax_highlighting_check)

        main_layout.addWidget(general_group)

        # History and validation database settings
        storage_group = QGroupBox('History and Validation Storage')
        storage_layout = QFormLayout(storage_group)

        # Connection selection for history/validation storage
        self._storage_connection_combo = QComboBox()
        self._storage_connection_combo.addItem('None (Disabled)', None)
        self._storage_connection_combo.setMinimumWidth(300)

        # Create a new SQLite database option
        self._create_sqlite_button = QPushButton('Create New SQLite Database')
        self._create_sqlite_button.clicked.connect(self._create_new_sqlite_db)

        # Help text
        help_label = QLabel(
            "Select a database connection to store history and validation data. "
            "This should be a separate database from your data sources. "
            "SQLite is recommended for most users."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")

        storage_layout.addRow('Storage Database:', self._storage_connection_combo)
        storage_layout.addRow('', self._create_sqlite_button)
        storage_layout.addRow('', help_label)

        main_layout.addWidget(storage_group)

        # Default connection settings
        default_group = QGroupBox('Default Connection')
        default_layout = QFormLayout(default_group)

        self._default_connection_combo = QComboBox()
        self._default_connection_combo.addItem('None', None)

        default_layout.addRow('Default Connection:', self._default_connection_combo)

        main_layout.addWidget(default_group)

        # Status area
        status_layout = QHBoxLayout()
        self._status_label = QLabel('')
        status_layout.addWidget(self._status_label)
        main_layout.addLayout(status_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)

    def _load_connections(self) -> None:
        """Load available connections into the combo boxes."""
        asyncio.create_task(self._async_load_connections())

    async def _async_load_connections(self) -> None:
        """Asynchronously load connections."""
        try:
            connections = await self._plugin.get_connections()

            # Save current selections
            current_storage_id = self._storage_connection_combo.currentData()
            current_default_id = self._default_connection_combo.currentData()

            # Clear and repopulate combos
            self._storage_connection_combo.clear()
            self._default_connection_combo.clear()

            # Add None option
            self._storage_connection_combo.addItem('None (Disabled)', None)
            self._default_connection_combo.addItem('None', None)

            # Add all connections
            for conn_id, conn in sorted(connections.items(), key=lambda x: x[1].name.lower()):
                # Add a tag for SQLite connections which are ideal for storage
                conn_text = conn.name
                if conn.connection_type == 'sqlite':
                    conn_text += ' (SQLite - Recommended)'

                self._storage_connection_combo.addItem(conn_text, conn_id)
                self._default_connection_combo.addItem(conn.name, conn_id)

            # Restore previous selections if they still exist
            # For storage connection
            storage_id = self._settings.history_database_connection_id if self._settings else None
            storage_index = 0

            if storage_id:
                for i in range(self._storage_connection_combo.count()):
                    if self._storage_connection_combo.itemData(i) == storage_id:
                        storage_index = i
                        break

            self._storage_connection_combo.setCurrentIndex(storage_index)

            # For default connection
            default_id = self._settings.default_connection_id if self._settings else None
            default_index = 0

            if default_id:
                for i in range(self._default_connection_combo.count()):
                    if self._default_connection_combo.itemData(i) == default_id:
                        default_index = i
                        break

            self._default_connection_combo.setCurrentIndex(default_index)

        except Exception as e:
            self._status_label.setText(f'Error loading connections: {str(e)}')

    def _create_new_sqlite_db(self) -> None:
        """Create a new SQLite database for history/validation storage."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'Create SQLite Database for History/Validation', '',
                'SQLite Databases (*.db *.sqlite *.sqlite3);;All Files (*.*)'
            )

            if not file_path:
                return

            # Add .db extension if none specified
            if not any(file_path.lower().endswith(ext) for ext in ['.db', '.sqlite', '.sqlite3']):
                file_path += '.db'

            # Create a unique name for this connection
            db_name = os.path.basename(file_path)
            connection_name = f"History DB ({db_name})"

            # Create a new SQLite connection config
            from ..models import SQLiteConnectionConfig

            config = SQLiteConnectionConfig(
                name=connection_name,
                database=file_path,
                username="sqlite",
                password="",
                read_only=False  # We need write access for storing history
            )

            # Save the connection
            asyncio.create_task(self._save_connection_and_update(config))

        except Exception as e:
            QMessageBox.critical(
                self, 'Error Creating Database',
                f'Failed to create SQLite database: {str(e)}'
            )

    async def _save_connection_and_update(self, config: Any) -> None:
        """Save a new connection and update the UI.

        Args:
            config: Connection configuration to save
        """
        try:
            conn_id = await self._plugin.save_connection(config)

            # Reload connections and select the new one
            await self._async_load_connections()

            # Find and select the new connection
            for i in range(self._storage_connection_combo.count()):
                if self._storage_connection_combo.itemData(i) == conn_id:
                    self._storage_connection_combo.setCurrentIndex(i)
                    break

            QMessageBox.information(
                self, 'Database Created',
                f'Successfully created SQLite database for history/validation storage.\n\n'
                f'This database has been added as connection "{config.name}" and selected as your storage database.'
            )

        except Exception as e:
            QMessageBox.critical(
                self, 'Error Saving Connection',
                f'Failed to save new connection: {str(e)}'
            )

    def get_settings(self) -> PluginSettings:
        """Create a settings object from dialog values.

        Returns:
            Updated plugin settings
        """
        if not self._settings:
            self._settings = PluginSettings()

        self._settings.max_result_rows = self._max_rows_spin.value()
        self._settings.query_history_limit = self._history_limit_spin.value()
        self._settings.auto_save_queries = self._auto_save_check.isChecked()
        self._settings.syntax_highlighting = self._syntax_highlighting_check.isChecked()
        self._settings.history_database_connection_id = self._storage_connection_combo.currentData()
        self._settings.default_connection_id = self._default_connection_combo.currentData()

        return self._settings

    def accept(self) -> None:
        """Handle dialog acceptance by saving settings."""
        try:
            settings = self.get_settings()

            # If history database changed, show a warning about restart
            if self._settings.history_database_connection_id != self._storage_connection_combo.currentData():
                QMessageBox.information(
                    self, 'Settings Updated',
                    'You have changed the history/validation storage database. '
                    'This change will take effect after restarting the application.'
                )

            asyncio.create_task(self._save_settings(settings))
            super().accept()

        except Exception as e:
            QMessageBox.critical(
                self, 'Error Saving Settings',
                f'Failed to save settings: {str(e)}'
            )

    async def _save_settings(self, settings: PluginSettings) -> None:
        """Save settings to the plugin configuration.

        Args:
            settings: Settings to save
        """
        await self._plugin._save_settings()