from __future__ import annotations

import time

"""
Enhanced settings dialog for the Database Connector Plugin.

This module provides an improved dialog for configuring plugin settings,
with better handling of SQLite database creation and connection setup.
"""

import os
import asyncio
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple, Protocol, cast, TypeVar

from PySide6.QtCore import Qt, QSize, QTimer, QObject, Signal, QEventLoop
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox, QTabWidget,
    QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem,
    QMessageBox, QComboBox, QStackedWidget, QFileDialog, QProgressDialog
)

from ..models import PluginSettings, SQLiteConnectionConfig

T = TypeVar("T")


class DatabaseSetupWorker(QObject):
    """Worker that handles database setup in a separate thread."""

    finished = Signal(bool, str)
    progress = Signal(str)

    def __init__(
            self,
            plugin: Any,
            config: SQLiteConnectionConfig,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the database setup worker.

        Args:
            plugin: The database connector plugin
            config: SQLite connection configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._config = config
        self._is_running = False
        self._logger = logging.getLogger(__name__)

    async def _async_setup_database(self) -> Tuple[bool, str]:
        """
        Setup the database connection and initialize history/validation.

        Returns:
            Tuple of (success, message)
        """
        try:
            self.progress.emit("Creating database connection...")

            # Save the SQLite connection configuration
            self.progress.emit("Saving connection configuration...")
            conn_id = await self._plugin.save_connection(self._config)

            # Update plugin settings
            self.progress.emit("Updating settings...")
            if self._plugin._settings:
                self._plugin._settings.history_database_connection_id = conn_id
                await self._plugin._save_settings()

            # Get a direct connector to ensure it's registered
            self.progress.emit("Registering connection...")
            connector = await self._plugin._get_connector_direct(conn_id)

            # Make sure database manager recognizes the connection
            if not await self._plugin._database_manager.has_connection(f"sqlite_{conn_id}"):
                self.progress.emit("Re-registering connection with database manager...")
                # If the connection wasn't registered, we might need to wait
                await asyncio.sleep(1)
                # Check again
                if not await self._plugin._database_manager.has_connection(f"sqlite_{conn_id}"):
                    raise RuntimeError(
                        f"Failed to register SQLite connection with database manager"
                    )

            # Initialize history manager
            if self._plugin._history_manager:
                self.progress.emit("Initializing history manager...")
                self._plugin._history_manager._history_connection_id = conn_id

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await self._plugin._history_manager.initialize()
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            self.progress.emit(f"Retry after error: {str(e)}")
                            await asyncio.sleep(2)  # Longer wait between retries
                        else:
                            raise

            # Initialize validation engine
            if self._plugin._validation_engine:
                self.progress.emit("Initializing validation engine...")
                self._plugin._validation_engine._validation_connection_id = conn_id
                await self._plugin._validation_engine.initialize()

            return True, "Database setup completed successfully"

        except Exception as e:
            self._logger.error(f"Database setup error: {str(e)}")
            return False, str(e)

    def setup_database(self) -> None:
        """Start the database setup process."""
        if self._is_running:
            return
        self._is_running = True

        async def run_setup() -> None:
            success, message = await self._async_setup_database()
            self.finished.emit(success, message)
            self._is_running = False

        # Create a new event loop in this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run the async setup
            loop.run_until_complete(run_setup())
        finally:
            loop.close()


class SettingsDialog(QDialog):
    """Dialog for configuring the plugin settings including database setup."""

    def __init__(
            self,
            plugin: Any,
            logger: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the settings dialog.

        Args:
            plugin: The database connector plugin
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._settings = self._plugin._settings or PluginSettings()

        self._init_ui()
        self.setWindowTitle("Database Connector Settings")
        self._load_connections()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        main_layout = QVBoxLayout(self)

        # General settings
        general_group = QGroupBox("General Settings")
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

        general_layout.addRow("Maximum result rows:", self._max_rows_spin)
        general_layout.addRow("Query history limit:", self._history_limit_spin)
        general_layout.addRow("Automatically save queries:", self._auto_save_check)
        general_layout.addRow("Enable syntax highlighting:", self._syntax_highlighting_check)

        main_layout.addWidget(general_group)

        # Storage settings
        storage_group = QGroupBox("History and Validation Storage")
        storage_layout = QFormLayout(storage_group)

        self._storage_connection_combo = QComboBox()
        self._storage_connection_combo.addItem("None (Disabled)", None)
        self._storage_connection_combo.setMinimumWidth(300)

        self._create_sqlite_button = QPushButton("Create New SQLite Database")
        self._create_sqlite_button.clicked.connect(self._create_new_sqlite_db)

        help_label = QLabel(
            "Select a database connection to store history and validation data. "
            "This should be a separate database from your data sources. "
            "SQLite is recommended for most users."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")

        storage_layout.addRow("Storage Database:", self._storage_connection_combo)
        storage_layout.addRow("", self._create_sqlite_button)
        storage_layout.addRow("", help_label)

        main_layout.addWidget(storage_group)

        # Default connection
        default_group = QGroupBox("Default Connection")
        default_layout = QFormLayout(default_group)

        self._default_connection_combo = QComboBox()
        self._default_connection_combo.addItem("None", None)

        default_layout.addRow("Default Connection:", self._default_connection_combo)

        main_layout.addWidget(default_group)

        # Status message
        status_layout = QHBoxLayout()
        self._status_label = QLabel("")
        status_layout.addWidget(self._status_label)

        main_layout.addLayout(status_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)

    def _load_connections(self) -> None:
        """Load available connections into combo boxes."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._async_load_connections())
            else:
                loop.run_until_complete(self._async_load_connections())
        except Exception as e:
            self._status_label.setText(f"Error loading connections: {str(e)}")

    async def _async_load_connections(self) -> None:
        """Asynchronously load connections into combo boxes."""
        try:
            connections = await self._plugin.get_connections()

            # Track current selections
            current_storage_id = self._storage_connection_combo.currentData()
            current_default_id = self._default_connection_combo.currentData()

            # Clear and repopulate storage connection combo
            self._storage_connection_combo.clear()
            self._storage_connection_combo.addItem("None (Disabled)", None)

            # Clear and repopulate default connection combo
            self._default_connection_combo.clear()
            self._default_connection_combo.addItem("None", None)

            # Add connections to both combos
            for conn_id, conn in sorted(connections.items(), key=lambda x: x[1].name.lower()):
                conn_text = conn.name
                if conn.connection_type == "sqlite":
                    conn_text += " (SQLite - Recommended)"

                self._storage_connection_combo.addItem(conn_text, conn_id)
                self._default_connection_combo.addItem(conn.name, conn_id)

            # Set saved storage connection
            storage_id = self._settings.history_database_connection_id
            if storage_id:
                for i in range(self._storage_connection_combo.count()):
                    if self._storage_connection_combo.itemData(i) == storage_id:
                        self._storage_connection_combo.setCurrentIndex(i)
                        break
            elif current_storage_id:
                for i in range(self._storage_connection_combo.count()):
                    if self._storage_connection_combo.itemData(i) == current_storage_id:
                        self._storage_connection_combo.setCurrentIndex(i)
                        break

            # Set saved default connection
            default_id = self._settings.default_connection_id
            if default_id:
                for i in range(self._default_connection_combo.count()):
                    if self._default_connection_combo.itemData(i) == default_id:
                        self._default_connection_combo.setCurrentIndex(i)
                        break
            elif current_default_id:
                for i in range(self._default_connection_combo.count()):
                    if self._default_connection_combo.itemData(i) == current_default_id:
                        self._default_connection_combo.setCurrentIndex(i)
                        break

        except Exception as e:
            if hasattr(self, "_status_label"):
                self._status_label.setText(f"Error loading connections: {str(e)}")

    def _create_new_sqlite_db(self) -> None:
        """Create a new SQLite database for history/validation storage."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Create SQLite Database for History/Validation",
                "",
                "SQLite Databases (*.db *.sqlite *.sqlite3);;All Files (*.*)",
            )

            if not file_path:
                return

            # Ensure proper file extension
            if not any((file_path.lower().endswith(ext) for ext in [".db", ".sqlite", ".sqlite3"])):
                file_path += ".db"

            # Create parent directory if it doesn't exist
            parent_dir = os.path.dirname(os.path.abspath(file_path))
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            db_name = os.path.basename(file_path)
            connection_name = f"History DB ({db_name})"

            # Create SQLite config
            config = SQLiteConnectionConfig(
                name=connection_name,
                database=file_path,
                username="sqlite",
                password="",
                read_only=False
            )

            # Setup progress dialog
            progress_dialog = QProgressDialog(
                "Setting up database...", "Cancel", 0, 0, self
            )
            progress_dialog.setWindowTitle("Database Setup")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setAutoClose(False)
            progress_dialog.setAutoReset(False)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)

            # Create worker
            worker = DatabaseSetupWorker(self._plugin, config, self)

            # Run in thread
            thread = threading.Thread(target=worker.setup_database)
            thread.daemon = True

            # Setup callbacks
            def update_progress(message: str) -> None:
                progress_dialog.setLabelText(message)

            def on_finished(success: bool, message: str) -> None:
                progress_dialog.close()
                if success:
                    QMessageBox.information(
                        self,
                        "Database Created",
                        f"Successfully created SQLite database for history/validation storage.\n\n"
                        f"Database: {file_path}\n\n"
                        f"The database has been configured and is ready to use.",
                    )
                    self._load_connections()
                else:
                    QMessageBox.critical(
                        self, "Database Setup Failed", f"Failed to set up the database: {message}"
                    )

            worker.progress.connect(update_progress)
            worker.finished.connect(on_finished)

            thread.start()
            progress_dialog.exec()

        except Exception as e:
            QMessageBox.critical(
                self, "Error Creating Database", f"Failed to create SQLite database: {str(e)}"
            )

    def get_settings(self) -> PluginSettings:
        """
        Get the updated settings from the dialog.

        Returns:
            Updated PluginSettings object
        """
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
        """Handle the OK button click."""
        try:
            new_settings = self.get_settings()
            self._plugin._settings = new_settings
            QTimer.singleShot(0, lambda: self._save_settings_async())
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Settings", f"Failed to save settings: {str(e)}")

    def _save_settings_async(self) -> None:
        """Save settings asynchronously."""

        async def save_task() -> None:
            try:
                # Save settings
                await self._plugin._save_settings()
                self._logger.info("Settings saved successfully")

                # Initialize history/validation with new connection if changed
                if self._plugin._settings and self._plugin._settings.history_database_connection_id:
                    history_id = self._plugin._settings.history_database_connection_id

                    # Update history manager
                    if (
                            self._plugin._history_manager
                            and self._plugin._history_manager._history_connection_id != history_id
                    ):
                        self._plugin._history_manager._history_connection_id = history_id
                        await self._plugin._history_manager.initialize()

                    # Update validation engine
                    if (
                            self._plugin._validation_engine
                            and self._plugin._validation_engine._validation_connection_id != history_id
                    ):
                        self._plugin._validation_engine._validation_connection_id = history_id
                        await self._plugin._validation_engine.initialize()

            except Exception as e:
                def show_error() -> None:
                    QMessageBox.critical(None, "Error", f"Failed to save settings: {str(e)}")

                if (
                        self._plugin._concurrency_manager
                        and not self._plugin._concurrency_manager.is_main_thread()
                ):
                    await self._plugin._concurrency_manager.run_on_main_thread(show_error)
                else:
                    show_error()

        asyncio.create_task(save_task())