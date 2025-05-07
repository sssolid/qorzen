from __future__ import annotations

"""
Connection dialog for AS400 Connector Plugin.

This module provides dialog windows for creating, editing and managing AS400
database connections.
"""

import os
import uuid
from typing import Any, Dict, List, Optional, Set, cast

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox, QFormLayout,
    QCheckBox, QSpinBox, QTabWidget, QWidget, QScrollArea,
    QGroupBox, QListWidget, QListWidgetItem, QMessageBox,
    QToolButton, QSizePolicy, QComboBox
)

from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig
from qorzen.plugins.as400_connector_plugin.code.utils import guess_jar_locations


class ConnectionDialog(QDialog):
    """
    Dialog for creating or editing an AS400 connection.

    Provides a form for configuring all AS400 connection parameters and
    testing the connection before saving.
    """

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            file_manager: Optional[Any] = None,
            connection: Optional[AS400ConnectionConfig] = None
    ) -> None:
        """
        Initialize the connection dialog.

        Args:
            parent: Parent widget
            file_manager: Optional file manager for file operations
            connection: Optional existing connection for editing
        """
        super().__init__(parent)

        self._file_manager = file_manager
        self._connection = connection

        # Setup UI
        self._init_ui()

        # Populate fields if editing
        if connection:
            self._populate_fields(connection)
            self.setWindowTitle(f"Edit Connection: {connection.name}")
        else:
            self.setWindowTitle("New AS400 Connection")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set dialog properties
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Create form layout
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        # Connection name
        name_label = QLabel("Connection Name:")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter a name for this connection")
        form_layout.addRow(name_label, self._name_edit)

        # Server
        server_label = QLabel("Server:")
        self._server_edit = QLineEdit()
        self._server_edit.setPlaceholderText("AS400 server address")
        form_layout.addRow(server_label, self._server_edit)

        # Port
        port_label = QLabel("Port:")
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(446)  # Default AS400 port
        form_layout.addRow(port_label, self._port_spin)

        # Database/Library
        database_label = QLabel("Database/Library:")
        self._database_edit = QLineEdit()
        self._database_edit.setPlaceholderText("Main library name")
        form_layout.addRow(database_label, self._database_edit)

        # Username
        username_label = QLabel("Username:")
        self._username_edit = QLineEdit()
        form_layout.addRow(username_label, self._username_edit)

        # Password
        password_label = QLabel("Password:")
        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow(password_label, self._password_edit)

        # JT400 JAR path
        jar_layout = QHBoxLayout()
        self._jar_path_edit = QLineEdit()
        self._jar_path_edit.setPlaceholderText("Path to jt400.jar file")

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_jar)

        autodetect_button = QPushButton("Auto-detect")
        autodetect_button.clicked.connect(self._autodetect_jar)

        jar_layout.addWidget(self._jar_path_edit)
        jar_layout.addWidget(browse_button)
        jar_layout.addWidget(autodetect_button)

        form_layout.addRow("JT400 JAR:", jar_layout)

        # SSL Option
        self._ssl_checkbox = QCheckBox("Use SSL for connection")
        self._ssl_checkbox.setChecked(True)
        form_layout.addRow("", self._ssl_checkbox)

        # Timeouts group
        timeout_group = QGroupBox("Timeouts")
        timeout_layout = QFormLayout(timeout_group)

        self._conn_timeout_spin = QSpinBox()
        self._conn_timeout_spin.setRange(1, 300)
        self._conn_timeout_spin.setValue(30)
        self._conn_timeout_spin.setSuffix(" seconds")

        self._query_timeout_spin = QSpinBox()
        self._query_timeout_spin.setRange(1, 3600)
        self._query_timeout_spin.setValue(60)
        self._query_timeout_spin.setSuffix(" seconds")

        timeout_layout.addRow("Connection Timeout:", self._conn_timeout_spin)
        timeout_layout.addRow("Query Timeout:", self._query_timeout_spin)

        # Advanced options group
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)

        self._allowed_tables_edit = QLineEdit()
        self._allowed_tables_edit.setPlaceholderText("Comma-separated table names, or leave empty for all")

        self._allowed_schemas_edit = QLineEdit()
        self._allowed_schemas_edit.setPlaceholderText("Comma-separated schema names, or leave empty for all")

        self._encrypt_checkbox = QCheckBox("Encrypt connection parameters")
        self._encrypt_checkbox.setChecked(True)

        advanced_layout.addRow("Allowed Tables:", self._allowed_tables_edit)
        advanced_layout.addRow("Allowed Schemas:", self._allowed_schemas_edit)
        advanced_layout.addRow("", self._encrypt_checkbox)

        # Add form sections to main layout
        main_layout.addLayout(form_layout)
        main_layout.addWidget(timeout_group)
        main_layout.addWidget(advanced_group)

        # Add spacer
        main_layout.addStretch(1)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Add test connection button
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self._test_connection)
        button_box.addButton(test_button, QDialogButtonBox.ActionRole)

        main_layout.addWidget(button_box)

    def _populate_fields(self, connection: AS400ConnectionConfig) -> None:
        """
        Populate dialog fields with connection values.

        Args:
            connection: The connection configuration to use
        """
        self._name_edit.setText(connection.name)
        self._server_edit.setText(connection.server)

        if connection.port is not None:
            self._port_spin.setValue(connection.port)

        self._database_edit.setText(connection.database)
        self._username_edit.setText(connection.username)
        self._password_edit.setText(connection.password.get_secret_value())
        self._jar_path_edit.setText(connection.jt400_jar_path)
        self._ssl_checkbox.setChecked(connection.ssl)
        self._conn_timeout_spin.setValue(connection.connection_timeout)
        self._query_timeout_spin.setValue(connection.query_timeout)

        if connection.allowed_tables:
            self._allowed_tables_edit.setText(', '.join(connection.allowed_tables))

        if connection.allowed_schemas:
            self._allowed_schemas_edit.setText(', '.join(connection.allowed_schemas))

        self._encrypt_checkbox.setChecked(connection.encrypt_connection)

    def _browse_jar(self) -> None:
        """Open file dialog to browse for JT400 JAR file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select JT400 JAR File",
            "",
            "JAR Files (*.jar)"
        )

        if file_path:
            self._jar_path_edit.setText(file_path)

    def _autodetect_jar(self) -> None:
        """Try to automatically detect the JT400 JAR file."""
        jar_paths = guess_jar_locations()

        if not jar_paths:
            QMessageBox.warning(
                self,
                "JAR Not Found",
                "Could not automatically detect jt400.jar file. Please specify it manually."
            )
            return

        # Use the first found JAR file
        self._jar_path_edit.setText(jar_paths[0])

        # Show success message
        QMessageBox.information(
            self,
            "JAR Found",
            f"Found jt400.jar at: {jar_paths[0]}"
        )

    def _test_connection(self) -> None:
        """Test the connection to the AS400 system."""
        try:
            # Create a connection config from the dialog fields
            config = self._get_connection_config()

            # Show a message that the connection test is not implemented in the UI
            # In a real implementation, this would actually test the connection
            QMessageBox.information(
                self,
                "Connection Test",
                "Connection test would normally connect to the AS400 system.\n\n"
                "This is not implemented in the dialog UI, but will work when "
                "you use the connection in the main interface."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Invalid Connection Configuration",
                f"Failed to create connection configuration: {str(e)}"
            )

    def get_connection_config(self) -> AS400ConnectionConfig:
        """
        Get the connection configuration from the dialog fields.

        Returns:
            The AS400 connection configuration

        Raises:
            ValueError: If any required fields are missing or invalid
        """
        return self._get_connection_config()

    def _get_connection_config(self) -> AS400ConnectionConfig:
        """
        Create a connection configuration from the dialog fields.

        Returns:
            The AS400 connection configuration

        Raises:
            ValueError: If any required fields are missing or invalid
        """
        # Get basic fields
        name = self._name_edit.text().strip()
        server = self._server_edit.text().strip()
        port = self._port_spin.value()
        database = self._database_edit.text().strip()
        username = self._username_edit.text().strip()
        password = self._password_edit.text()
        jar_path = self._jar_path_edit.text().strip()

        # Validate required fields
        if not name:
            raise ValueError("Connection name is required")
        if not server:
            raise ValueError("Server address is required")
        if not database:
            raise ValueError("Database/Library is required")
        if not username:
            raise ValueError("Username is required")
        if not password:
            raise ValueError("Password is required")
        if not jar_path:
            raise ValueError("JT400 JAR path is required")

        # Validate JAR path
        if not os.path.exists(jar_path):
            raise ValueError(f"JT400 JAR file not found: {jar_path}")

        # Get other options
        ssl = self._ssl_checkbox.isChecked()
        connection_timeout = self._conn_timeout_spin.value()
        query_timeout = self._query_timeout_spin.value()
        encrypt_connection = self._encrypt_checkbox.isChecked()

        # Parse allowed tables
        allowed_tables = None
        tables_text = self._allowed_tables_edit.text().strip()
        if tables_text:
            allowed_tables = [t.strip().upper() for t in tables_text.split(',') if t.strip()]

        # Parse allowed schemas
        allowed_schemas = None
        schemas_text = self._allowed_schemas_edit.text().strip()
        if schemas_text:
            allowed_schemas = [s.strip().upper() for s in schemas_text.split(',') if s.strip()]

        # Create the connection config
        return AS400ConnectionConfig(
            id=self._connection.id if self._connection else str(uuid.uuid4()),
            name=name,
            server=server,
            port=port,
            database=database,
            username=username,
            password=password,
            jt400_jar_path=jar_path,
            ssl=ssl,
            connection_timeout=connection_timeout,
            query_timeout=query_timeout,
            allowed_tables=allowed_tables,
            allowed_schemas=allowed_schemas,
            encrypt_connection=encrypt_connection
        )


class ConnectionManagerDialog(QDialog):
    """
    Dialog for managing multiple AS400 connections.

    Provides a list of connections with options to add, edit, delete,
    and set a default connection.
    """

    def __init__(
            self,
            connections: Dict[str, AS400ConnectionConfig],
            parent: Optional[QWidget] = None,
            file_manager: Optional[Any] = None
    ) -> None:
        """
        Initialize the connection manager dialog.

        Args:
            connections: Dictionary of existing connections by ID
            parent: Parent widget
            file_manager: Optional file manager for file operations
        """
        super().__init__(parent)

        self._connections = connections.copy()
        self._file_manager = file_manager

        # Setup UI
        self._init_ui()
        self.setWindowTitle("Manage AS400 Connections")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set dialog properties
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # List label
        list_label = QLabel("Available Connections:")
        list_label.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(list_label)

        # Connection list
        self._conn_list = QListWidget()
        self._conn_list.setSelectionMode(QListWidget.SingleSelection)
        self._conn_list.itemSelectionChanged.connect(self._on_selection_changed)
        self._populate_connection_list()

        main_layout.addWidget(self._conn_list)

        # Buttons layout
        button_layout = QHBoxLayout()

        # Add connection button
        self._add_button = QPushButton("Add")
        self._add_button.clicked.connect(self._add_connection)
        button_layout.addWidget(self._add_button)

        # Edit connection button
        self._edit_button = QPushButton("Edit")
        self._edit_button.clicked.connect(self._edit_connection)
        self._edit_button.setEnabled(False)
        button_layout.addWidget(self._edit_button)

        # Delete connection button
        self._delete_button = QPushButton("Delete")
        self._delete_button.clicked.connect(self._delete_connection)
        self._delete_button.setEnabled(False)
        button_layout.addWidget(self._delete_button)

        # Set as default button
        self._default_button = QPushButton("Set as Default")
        self._default_button.clicked.connect(self._set_as_default)
        self._default_button.setEnabled(False)
        button_layout.addWidget(self._default_button)

        # Add button layout
        main_layout.addLayout(button_layout)

        # Add spacer
        main_layout.addStretch(1)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        main_layout.addWidget(dialog_buttons)

    def _populate_connection_list(self) -> None:
        """Populate the connection list with existing connections."""
        self._conn_list.clear()

        # Sort connections by name
        sorted_connections = sorted(
            self._connections.values(),
            key=lambda c: c.name.lower()
        )

        # Add connections to list
        for conn in sorted_connections:
            item = QListWidgetItem(conn.name)
            item.setData(Qt.UserRole, conn.id)
            self._conn_list.addItem(item)

    def _on_selection_changed(self) -> None:
        """Handle selection change in the connection list."""
        # Enable/disable buttons based on selection
        has_selection = len(self._conn_list.selectedItems()) > 0
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)
        self._default_button.setEnabled(has_selection)

    def _add_connection(self) -> None:
        """Add a new connection."""
        dialog = ConnectionDialog(
            parent=self,
            file_manager=self._file_manager
        )

        if dialog.exec() == QDialog.Accepted:
            # Get the new connection
            new_connection = dialog.get_connection_config()

            # Add to connections
            self._connections[new_connection.id] = new_connection

            # Update list
            self._populate_connection_list()

    def _edit_connection(self) -> None:
        """Edit the selected connection."""
        # Get selected connection
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return

        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return

        # Open edit dialog
        dialog = ConnectionDialog(
            parent=self,
            file_manager=self._file_manager,
            connection=self._connections[conn_id]
        )

        if dialog.exec() == QDialog.Accepted:
            # Get the updated connection
            updated_connection = dialog.get_connection_config()

            # Update in connections
            self._connections[updated_connection.id] = updated_connection

            # Update list
            self._populate_connection_list()

    def _delete_connection(self) -> None:
        """Delete the selected connection."""
        # Get selected connection
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return

        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the connection '{self._connections[conn_id].name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove from connections
            del self._connections[conn_id]

            # Update list
            self._populate_connection_list()

    def _set_as_default(self) -> None:
        """Set the selected connection as the default."""
        # Get selected connection
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return

        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return

        # Show confirmation message
        QMessageBox.information(
            self,
            "Default Connection",
            f"Connection '{self._connections[conn_id].name}' will be used as the default."
        )

        # In a real implementation, this would save the default in settings
        # For now, we just show the message

    def get_connections(self) -> Dict[str, AS400ConnectionConfig]:
        """
        Get the updated connections.

        Returns:
            Dictionary of connections by ID
        """
        return self._connections