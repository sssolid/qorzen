from __future__ import annotations

"""
Settings dialog for the Database Connector Plugin.

This module provides a dialog for configuring plugin settings, including
database connections for storing history and validation data.
"""
import os
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, \
    QFormLayout, QCheckBox, QSpinBox, QTabWidget, QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem, \
    QMessageBox, QComboBox, QStackedWidget, QFileDialog
from ..models import PluginSettings, SQLiteConnectionConfig


class SettingsDialog(QDialog):
    def __init__(self, plugin: Any, logger: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._settings = self._plugin._settings or PluginSettings()
        self._init_ui()
        self.setWindowTitle('Database Connector Settings')
        self._load_connections()

    def _init_ui(self) -> None:
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        main_layout = QVBoxLayout(self)

        general_group = QGroupBox('General Settings')
        general_layout = QFormLayout(general_group)

        self._max_rows_spin = QSpinBox()
        self._max_rows_spin.setRange(100, 1000000)
        self._max_rows_spin.setSingleStep(1000)
        self._max_rows_spin.setValue(self._settings.max_result_rows)

        self._history_limit_spin = QSpinBox()
        self._history_limit_spin.setRange(10, 1000)
        self._history_limit_spin.setValue(self._settings.query_history_limit)

        self._auto_save_check = QCheckBox()
        self._auto_save_check.setChecked(self._settings.auto_save_queries)

        self._syntax_highlighting_check = QCheckBox()
        self._syntax_highlighting_check.setChecked(self._settings.syntax_highlighting)

        general_layout.addRow('Maximum result rows:', self._max_rows_spin)
        general_layout.addRow('Query history limit:', self._history_limit_spin)
        general_layout.addRow('Automatically save queries:', self._auto_save_check)
        general_layout.addRow('Enable syntax highlighting:', self._syntax_highlighting_check)

        main_layout.addWidget(general_group)

        storage_group = QGroupBox('History and Validation Storage')
        storage_layout = QFormLayout(storage_group)

        self._storage_connection_combo = QComboBox()
        self._storage_connection_combo.addItem('None (Disabled)', None)
        self._storage_connection_combo.setMinimumWidth(300)

        self._create_sqlite_button = QPushButton('Create New SQLite Database')
        self._create_sqlite_button.clicked.connect(self._create_new_sqlite_db)

        help_label = QLabel(
            'Select a database connection to store history and validation data. This should be a separate database from your data sources. SQLite is recommended for most users.')
        help_label.setWordWrap(True)
        help_label.setStyleSheet('color: #666; font-size: 11px;')

        storage_layout.addRow('Storage Database:', self._storage_connection_combo)
        storage_layout.addRow('', self._create_sqlite_button)
        storage_layout.addRow('', help_label)

        main_layout.addWidget(storage_group)

        default_group = QGroupBox('Default Connection')
        default_layout = QFormLayout(default_group)

        self._default_connection_combo = QComboBox()
        self._default_connection_combo.addItem('None', None)

        default_layout.addRow('Default Connection:', self._default_connection_combo)

        main_layout.addWidget(default_group)

        status_layout = QHBoxLayout()
        self._status_label = QLabel('')
        status_layout.addWidget(self._status_label)

        main_layout.addLayout(status_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)

    def _load_connections(self) -> None:
        try:
            # Run the async method in a synchronous way
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a task
                asyncio.create_task(self._async_load_connections())
            else:
                # Otherwise, run the task to completion
                loop.run_until_complete(self._async_load_connections())
        except Exception as e:
            self._status_label.setText(f'Error loading connections: {str(e)}')

    async def _async_load_connections(self) -> None:
        try:
            connections = await self._plugin.get_connections()

            # Remember current selections
            current_storage_id = self._storage_connection_combo.currentData()
            current_default_id = self._default_connection_combo.currentData()

            # Clear and refill dropdowns
            self._storage_connection_combo.clear()
            self._default_connection_combo.clear()

            self._storage_connection_combo.addItem('None (Disabled)', None)
            self._default_connection_combo.addItem('None', None)

            for conn_id, conn in sorted(connections.items(), key=lambda x: x[1].name.lower()):
                conn_text = conn.name
                if conn.connection_type == 'sqlite':
                    conn_text += ' (SQLite - Recommended)'
                self._storage_connection_combo.addItem(conn_text, conn_id)
                self._default_connection_combo.addItem(conn.name, conn_id)

            # Set selected items based on current settings
            storage_id = self._settings.history_database_connection_id
            if storage_id:
                for i in range(self._storage_connection_combo.count()):
                    if self._storage_connection_combo.itemData(i) == storage_id:
                        self._storage_connection_combo.setCurrentIndex(i)
                        break

            default_id = self._settings.default_connection_id
            if default_id:
                for i in range(self._default_connection_combo.count()):
                    if self._default_connection_combo.itemData(i) == default_id:
                        self._default_connection_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            if hasattr(self, '_status_label'):
                self._status_label.setText(f'Error loading connections: {str(e)}')

    def _create_new_sqlite_db(self) -> None:
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                'Create SQLite Database for History/Validation',
                '',
                'SQLite Databases (*.db *.sqlite *.sqlite3);;All Files (*.*)'
            )

            if not file_path:
                return

            if not any((file_path.lower().endswith(ext) for ext in ['.db', '.sqlite', '.sqlite3'])):
                file_path += '.db'

            db_name = os.path.basename(file_path)
            connection_name = f'History DB ({db_name})'

            # Create the config object but don't try to save it yet
            config = SQLiteConnectionConfig(
                name=connection_name,
                database=file_path,
                username='sqlite',
                password='',
                read_only=False
            )

            # Store the config to use when dialog is accepted
            self._new_sqlite_config = config

            # Tell the user what will happen when they click OK
            QMessageBox.information(
                self,
                'Database Ready',
                f'SQLite database configured and will be created when you click OK.\n\n'
                f'The database will be added as connection "{connection_name}" '
                f'and set as your storage database.'
            )

        except Exception as e:
            QMessageBox.critical(self, 'Error Creating Database', f'Failed to create SQLite database: {str(e)}')

    def _save_connection_sync(self, config: SQLiteConnectionConfig) -> None:
        try:
            # Save connection in a synchronous way
            loop = asyncio.get_event_loop()
            conn_id = loop.run_until_complete(self._plugin.save_connection(config))

            # Update the current setting directly
            if self._settings:
                self._settings.history_database_connection_id = conn_id

            # Reload connections
            self._load_connections()

            # Show success message
            QMessageBox.information(
                self,
                'Database Created',
                f'Successfully created SQLite database for history/validation storage.\n\n'
                f'This database has been added as connection "{config.name}" '
                f'and will be set as your storage database when you click OK.'
            )

        except Exception as e:
            QMessageBox.critical(self, 'Error Saving Connection', f'Failed to save new connection: {str(e)}')

    def get_settings(self) -> PluginSettings:
        # Create a new settings object with the current values
        settings = PluginSettings(
            max_result_rows=self._max_rows_spin.value(),
            query_history_limit=self._history_limit_spin.value(),
            auto_save_queries=self._auto_save_check.isChecked(),
            syntax_highlighting=self._syntax_highlighting_check.isChecked(),
            history_database_connection_id=self._storage_connection_combo.currentData(),
            default_connection_id=self._default_connection_combo.currentData(),
            recent_connections=self._settings.recent_connections
        )
        return settings

    def accept(self) -> None:
        try:
            # Get updated settings
            new_settings = self.get_settings()

            # Check if we have a new database to add
            if hasattr(self, '_new_sqlite_config'):
                # Defer this work to after dialog closes
                QTimer.singleShot(0, lambda: self._finish_setup(new_settings))
                super().accept()
                return

            # Otherwise, do normal settings update
            self._plugin._settings = new_settings

            # Use a timer to perform async operations after dialog closes
            QTimer.singleShot(0, lambda: self._save_settings_async())

            # Accept the dialog
            super().accept()

        except Exception as e:
            QMessageBox.critical(self, 'Error Saving Settings', f'Failed to save settings: {str(e)}')

    def _save_settings_async(self):
        """Save settings asynchronously after dialog closes."""

        async def save_task():
            try:
                await self._plugin._save_settings()
                self._logger.info("Settings saved successfully")
            except Exception as e:
                QMessageBox.critical(None, 'Error', f'Failed to save settings: {str(e)}')

        # Create and start the task
        asyncio.create_task(save_task())

    def _finish_setup(self, settings):
        """Complete the database setup after dialog closes."""

        async def setup_task():
            try:
                # First save the connection
                conn_id = await self._plugin.save_connection(self._new_sqlite_config)
                self._logger.info(f"Created new database connection: {conn_id}")

                # Update and save settings to use this connection
                settings.history_database_connection_id = conn_id
                self._plugin._settings = settings
                await self._plugin._save_settings()
                self._logger.info(f"Updated settings with new history database: {conn_id}")

                # Initialize services
                if self._plugin._history_manager:
                    self._plugin._history_manager._history_connection_id = conn_id
                    await self._plugin._history_manager.initialize()

                if self._plugin._validation_engine:
                    self._plugin._validation_engine._validation_connection_id = conn_id
                    await self._plugin._validation_engine.initialize()

                QMessageBox.information(None, 'Success',
                                        'Database configured successfully.\n\n'
                                        'History and validation features are now available.')
            except Exception as e:
                QMessageBox.critical(None, 'Error', f'Failed to complete setup: {str(e)}')

        # Create and start the task
        asyncio.create_task(setup_task())