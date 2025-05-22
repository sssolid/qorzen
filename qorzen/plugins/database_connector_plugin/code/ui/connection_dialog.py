"""
Connection dialog for the Database Connector Plugin.

This module provides a dialog for creating and editing database connections
with support for various database types and connection parameters.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QTextEdit,
    QPushButton, QDialogButtonBox, QTabWidget, QWidget,
    QLabel, QFileDialog, QMessageBox
)

from ..models import DatabaseConnection, ConnectionType


class ConnectionDialog(QDialog):
    """
    Dialog for creating and editing database connections.

    Provides a comprehensive interface for configuring database connections
    with support for various database types and advanced settings.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the connection dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._connection: Optional[DatabaseConnection] = None

        # UI components
        self._name_edit: Optional[QLineEdit] = None
        self._type_combo: Optional[QComboBox] = None
        self._host_edit: Optional[QLineEdit] = None
        self._port_spin: Optional[QSpinBox] = None
        self._database_edit: Optional[QLineEdit] = None
        self._user_edit: Optional[QLineEdit] = None
        self._password_edit: Optional[QLineEdit] = None
        self._connection_string_edit: Optional[QTextEdit] = None
        self._ssl_check: Optional[QCheckBox] = None
        self._read_only_check: Optional[QCheckBox] = None
        self._pool_size_spin: Optional[QSpinBox] = None
        self._max_overflow_spin: Optional[QSpinBox] = None
        self._pool_recycle_spin: Optional[QSpinBox] = None
        self._connection_timeout_spin: Optional[QSpinBox] = None
        self._query_timeout_spin: Optional[QSpinBox] = None
        self._dsn_edit: Optional[QLineEdit] = None
        self._jt400_path_edit: Optional[QLineEdit] = None
        self._allowed_tables_edit: Optional[QTextEdit] = None

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Database Connection")
        self.setModal(True)
        self.resize(500, 600)

        layout = QVBoxLayout(self)

        # Tab widget for different sections
        tab_widget = QTabWidget()

        # Basic settings tab
        basic_tab = self._create_basic_tab()
        tab_widget.addTab(basic_tab, "Basic")

        # Advanced settings tab
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")

        # Security settings tab
        security_tab = self._create_security_tab()
        tab_widget.addTab(security_tab, "Security")

        layout.addWidget(tab_widget)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def _create_basic_tab(self) -> QWidget:
        """Create the basic settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Connection details group
        details_group = QGroupBox("Connection Details")
        details_layout = QFormLayout(details_group)

        # Connection name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter connection name")
        details_layout.addRow("Name:", self._name_edit)

        # Database type
        self._type_combo = QComboBox()
        for conn_type in ConnectionType:
            self._type_combo.addItem(conn_type.value.upper(), conn_type)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        details_layout.addRow("Type:", self._type_combo)

        # Host
        self._host_edit = QLineEdit()
        self._host_edit.setPlaceholderText("localhost")
        details_layout.addRow("Host:", self._host_edit)

        # Port
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(5432)  # Default PostgreSQL port
        details_layout.addRow("Port:", self._port_spin)

        # Database
        self._database_edit = QLineEdit()
        self._database_edit.setPlaceholderText("Database name or file path")
        details_layout.addRow("Database:", self._database_edit)

        layout.addWidget(details_group)

        # Authentication group
        auth_group = QGroupBox("Authentication")
        auth_layout = QFormLayout(auth_group)

        # Username
        self._user_edit = QLineEdit()
        auth_layout.addRow("Username:", self._user_edit)

        # Password
        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addRow("Password:", self._password_edit)

        layout.addWidget(auth_group)

        # Connection string group (for advanced users)
        conn_str_group = QGroupBox("Connection String (Optional)")
        conn_str_layout = QVBoxLayout(conn_str_group)

        conn_str_layout.addWidget(QLabel("Override individual settings with a custom connection string:"))

        self._connection_string_edit = QTextEdit()
        self._connection_string_edit.setMaximumHeight(100)
        self._connection_string_edit.setPlaceholderText("e.g., postgresql://user:password@host:port/database")
        conn_str_layout.addWidget(self._connection_string_edit)

        layout.addWidget(conn_str_group)

        layout.addStretch()

        return tab

    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Pool settings group
        pool_group = QGroupBox("Connection Pool")
        pool_layout = QFormLayout(pool_group)

        # Pool size
        self._pool_size_spin = QSpinBox()
        self._pool_size_spin.setRange(1, 100)
        self._pool_size_spin.setValue(5)
        pool_layout.addRow("Pool Size:", self._pool_size_spin)

        # Max overflow
        self._max_overflow_spin = QSpinBox()
        self._max_overflow_spin.setRange(0, 100)
        self._max_overflow_spin.setValue(10)
        pool_layout.addRow("Max Overflow:", self._max_overflow_spin)

        # Pool recycle
        self._pool_recycle_spin = QSpinBox()
        self._pool_recycle_spin.setRange(300, 86400)  # 5 minutes to 1 day
        self._pool_recycle_spin.setValue(3600)
        self._pool_recycle_spin.setSuffix(" seconds")
        pool_layout.addRow("Pool Recycle:", self._pool_recycle_spin)

        layout.addWidget(pool_group)

        # Timeout settings group
        timeout_group = QGroupBox("Timeouts")
        timeout_layout = QFormLayout(timeout_group)

        # Connection timeout
        self._connection_timeout_spin = QSpinBox()
        self._connection_timeout_spin.setRange(1, 300)  # 1 second to 5 minutes
        self._connection_timeout_spin.setValue(10)
        self._connection_timeout_spin.setSuffix(" seconds")
        timeout_layout.addRow("Connection Timeout:", self._connection_timeout_spin)

        # Query timeout
        self._query_timeout_spin = QSpinBox()
        self._query_timeout_spin.setRange(1, 3600)  # 1 second to 1 hour
        self._query_timeout_spin.setValue(30)
        self._query_timeout_spin.setSuffix(" seconds")
        timeout_layout.addRow("Query Timeout:", self._query_timeout_spin)

        layout.addWidget(timeout_group)

        # Database-specific settings
        db_specific_group = QGroupBox("Database-Specific Settings")
        db_specific_layout = QFormLayout(db_specific_group)

        # DSN (for ODBC)
        self._dsn_edit = QLineEdit()
        self._dsn_edit.setPlaceholderText("Data Source Name for ODBC connections")
        db_specific_layout.addRow("DSN:", self._dsn_edit)

        # JT400 JAR path (for AS400)
        jt400_layout = QHBoxLayout()
        self._jt400_path_edit = QLineEdit()
        self._jt400_path_edit.setPlaceholderText("Path to JT400.jar file")
        jt400_layout.addWidget(self._jt400_path_edit)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_jt400_jar)
        jt400_layout.addWidget(browse_button)

        db_specific_layout.addRow("JT400 JAR:", jt400_layout)

        layout.addWidget(db_specific_group)

        layout.addStretch()

        return tab

    def _create_security_tab(self) -> QWidget:
        """Create the security settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Security options group
        security_group = QGroupBox("Security Options")
        security_layout = QVBoxLayout(security_group)

        # SSL
        self._ssl_check = QCheckBox("Use SSL/TLS encryption")
        security_layout.addWidget(self._ssl_check)

        # Read-only
        self._read_only_check = QCheckBox("Read-only connection")
        self._read_only_check.setToolTip("Prevents data modification operations")
        security_layout.addWidget(self._read_only_check)

        layout.addWidget(security_group)

        # Access control group
        access_group = QGroupBox("Access Control")
        access_layout = QVBoxLayout(access_group)

        access_layout.addWidget(QLabel("Allowed Tables (one per line, leave empty for all):"))

        self._allowed_tables_edit = QTextEdit()
        self._allowed_tables_edit.setMaximumHeight(150)
        self._allowed_tables_edit.setPlaceholderText("table1\ntable2\ntable3")
        access_layout.addWidget(self._allowed_tables_edit)

        layout.addWidget(access_group)

        layout.addStretch()

        return tab

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        # Update default port when database type changes
        self._on_type_changed()

    def _on_type_changed(self) -> None:
        """Handle database type change."""
        try:
            db_type = self._type_combo.currentData()
            if not db_type:
                return

            # Set default ports
            default_ports = {
                ConnectionType.POSTGRESQL: 5432,
                ConnectionType.MYSQL: 3306,
                ConnectionType.SQLITE: 0,
                ConnectionType.ORACLE: 1521,
                ConnectionType.MSSQL: 1433,
                ConnectionType.AS400: 446,
                ConnectionType.ODBC: 0
            }

            if db_type in default_ports:
                self._port_spin.setValue(default_ports[db_type])

            # Update UI based on database type
            is_file_based = db_type == ConnectionType.SQLITE

            # Disable host/port for file-based databases
            self._host_edit.setEnabled(not is_file_based)
            self._port_spin.setEnabled(not is_file_based)

            # Update database field placeholder
            if is_file_based:
                self._database_edit.setPlaceholderText("Path to database file (e.g., /path/to/database.db)")
            else:
                self._database_edit.setPlaceholderText("Database name")

            # Show/hide database-specific settings
            dsn_visible = db_type == ConnectionType.ODBC
            self._dsn_edit.setVisible(dsn_visible)

            jt400_visible = db_type == ConnectionType.AS400
            self._jt400_path_edit.setVisible(jt400_visible)

        except Exception as e:
            # Log error but don't show dialog to avoid recursion
            print(f"Error updating UI for database type: {e}")

    def _browse_jt400_jar(self) -> None:
        """Browse for JT400 JAR file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select JT400 JAR File",
            "",
            "JAR Files (*.jar);;All Files (*)"
        )

        if file_path:
            self._jt400_path_edit.setText(file_path)

    def set_connection(self, connection: DatabaseConnection) -> None:
        """
        Set the connection to edit.

        Args:
            connection: The connection to edit
        """
        self._connection = connection

        # Populate fields
        self._name_edit.setText(connection.name)

        # Set connection type
        type_index = self._type_combo.findData(connection.connection_type)
        if type_index >= 0:
            self._type_combo.setCurrentIndex(type_index)

        self._host_edit.setText(connection.host)
        self._port_spin.setValue(connection.port or 0)
        self._database_edit.setText(connection.database)
        self._user_edit.setText(connection.user)
        self._password_edit.setText(connection.password)

        if connection.connection_string:
            self._connection_string_edit.setPlainText(connection.connection_string)

        self._ssl_check.setChecked(connection.ssl)
        self._read_only_check.setChecked(connection.read_only)

        # Advanced settings
        self._pool_size_spin.setValue(connection.pool_size)
        self._max_overflow_spin.setValue(connection.max_overflow)
        self._pool_recycle_spin.setValue(connection.pool_recycle)
        self._connection_timeout_spin.setValue(connection.connection_timeout)
        self._query_timeout_spin.setValue(connection.query_timeout)

        # Database-specific settings
        if connection.dsn:
            self._dsn_edit.setText(connection.dsn)

        if connection.jt400_jar_path:
            self._jt400_path_edit.setText(connection.jt400_jar_path)

        if connection.allowed_tables:
            self._allowed_tables_edit.setPlainText('\n'.join(connection.allowed_tables))

    def get_connection(self) -> DatabaseConnection:
        """
        Get the connection from the dialog.

        Returns:
            The configured connection

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        name = self._name_edit.text().strip()
        if not name:
            raise ValueError("Connection name is required")

        db_type = self._type_combo.currentData()
        if not db_type:
            raise ValueError("Database type is required")

        # Get allowed tables
        allowed_tables = None
        tables_text = self._allowed_tables_edit.toPlainText().strip()
        if tables_text:
            allowed_tables = [table.strip() for table in tables_text.split('\n') if table.strip()]

        # Create connection object
        if self._connection:
            # Update existing connection
            connection = self._connection
            connection.name = name
            connection.connection_type = db_type
            connection.host = self._host_edit.text().strip()
            connection.port = self._port_spin.value() if self._port_spin.value() > 0 else None
            connection.database = self._database_edit.text().strip()
            connection.user = self._user_edit.text().strip()
            connection.password = self._password_edit.text()
            connection.connection_string = self._connection_string_edit.toPlainText().strip() or None
            connection.ssl = self._ssl_check.isChecked()
            connection.read_only = self._read_only_check.isChecked()
            connection.pool_size = self._pool_size_spin.value()
            connection.max_overflow = self._max_overflow_spin.value()
            connection.pool_recycle = self._pool_recycle_spin.value()
            connection.connection_timeout = self._connection_timeout_spin.value()
            connection.query_timeout = self._query_timeout_spin.value()
            connection.dsn = self._dsn_edit.text().strip() or None
            connection.jt400_jar_path = self._jt400_path_edit.text().strip() or None
            connection.allowed_tables = allowed_tables
            connection.updated_at = datetime.now()
        else:
            # Create new connection
            connection = DatabaseConnection(
                name=name,
                connection_type=db_type,
                host=self._host_edit.text().strip(),
                port=self._port_spin.value() if self._port_spin.value() > 0 else None,
                database=self._database_edit.text().strip(),
                user=self._user_edit.text().strip(),
                password=self._password_edit.text(),
                connection_string=self._connection_string_edit.toPlainText().strip() or None,
                ssl=self._ssl_check.isChecked(),
                read_only=self._read_only_check.isChecked(),
                pool_size=self._pool_size_spin.value(),
                max_overflow=self._max_overflow_spin.value(),
                pool_recycle=self._pool_recycle_spin.value(),
                connection_timeout=self._connection_timeout_spin.value(),
                query_timeout=self._query_timeout_spin.value(),
                dsn=self._dsn_edit.text().strip() or None,
                jt400_jar_path=self._jt400_path_edit.text().strip() or None,
                allowed_tables=allowed_tables
            )

        return connection

    def accept(self) -> None:
        """Accept the dialog after validation."""
        try:
            # Validate connection
            connection = self.get_connection()

            # Basic validation
            if connection.connection_type != ConnectionType.SQLITE:
                if not connection.host:
                    QMessageBox.warning(self, "Validation Error", "Host is required for this database type")
                    return

                if not connection.database:
                    QMessageBox.warning(self, "Validation Error", "Database name is required")
                    return
            else:
                if not connection.database:
                    QMessageBox.warning(self, "Validation Error", "Database file path is required")
                    return

            # ODBC-specific validation
            if connection.connection_type == ConnectionType.ODBC and not connection.dsn and not connection.connection_string:
                QMessageBox.warning(self, "Validation Error",
                                    "DSN or connection string is required for ODBC connections")
                return

            # AS400-specific validation
            if connection.connection_type == ConnectionType.AS400 and connection.jt400_jar_path:
                import os
                if not os.path.exists(connection.jt400_jar_path):
                    QMessageBox.warning(self, "Validation Error", "JT400 JAR file not found at specified path")
                    return

            super().accept()

        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")