from __future__ import annotations

"""
Enhanced connection dialogs for the Database Connector Plugin.

This module provides improved dialog windows for creating, editing, and managing
database connections of various types, with added support for SQLite.
"""

import os
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox, QTabWidget,
    QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem,
    QMessageBox, QToolButton, QSizePolicy, QComboBox, QStackedWidget,
    QFileDialog, QFrame
)

from ..models import (
    BaseConnectionConfig, AS400ConnectionConfig, ODBCConnectionConfig,
    SQLiteConnectionConfig, ConnectionType
)


def guess_jar_locations() -> List[str]:
    """Find potential locations for the JT400 jar file.

    Returns:
        List of potential jar file paths that exist
    """
    potential_paths = []

    if os.name == 'nt':  # Windows
        program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
        program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')

        for base in [program_files, program_files_x86]:
            potential_paths.extend([
                os.path.join(base, 'IBM', 'JTOpen', 'lib', 'jt400.jar'),
                os.path.join(base, 'IBM', 'Client Access', 'jt400.jar')
            ])

        downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        potential_paths.append(os.path.join(downloads, 'jt400.jar'))

    else:  # Unix/Linux/Mac
        potential_paths.extend([
            '/opt/jt400/lib/jt400.jar',
            '/usr/local/lib/jt400.jar',
            '/usr/lib/jt400.jar',
            os.path.join(os.path.expanduser('~'), 'lib', 'jt400.jar'),
            os.path.join(os.path.expanduser('~'), 'Downloads', 'jt400.jar')
        ])

    # Check project directories
    project_dir = os.path.abspath(os.getcwd())
    potential_paths.extend([
        os.path.join(project_dir, 'lib', 'jt400.jar'),
        os.path.join(project_dir, 'jars', 'jt400.jar'),
        os.path.join(project_dir, 'external', 'jt400.jar')
    ])

    # Return only paths that actually exist
    return [path for path in potential_paths if os.path.exists(path)]


class ConnectionDialog(QDialog):
    """Dialog for creating or editing a database connection."""

    def __init__(self, parent: Optional[QWidget] = None, connection: Optional[BaseConnectionConfig] = None) -> None:
        """Initialize the connection dialog.

        Args:
            parent: Parent widget
            connection: Optional existing connection to edit
        """
        super().__init__(parent)
        self._connection = connection
        self._init_ui()

        if connection:
            self._populate_fields(connection)
            self.setWindowTitle(f'Edit Connection: {connection.name}')
        else:
            self.setWindowTitle('New Database Connection')

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        main_layout = QVBoxLayout(self)

        # Connection type selection
        type_layout = QHBoxLayout()
        type_label = QLabel('Connection Type:')
        self._type_combo = QComboBox()
        self._type_combo.addItem('AS400/iSeries', ConnectionType.AS400)
        self._type_combo.addItem('ODBC (FileMaker, etc.)', ConnectionType.ODBC)
        self._type_combo.addItem('SQLite', ConnectionType.SQLITE)  # Add SQLite option
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)

        type_layout.addWidget(type_label)
        type_layout.addWidget(self._type_combo, 1)
        main_layout.addLayout(type_layout)

        # Basic connection info
        basic_group = QGroupBox('Connection Info')
        basic_layout = QFormLayout(basic_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText('Enter a name for this connection')
        basic_layout.addRow('Connection Name:', self._name_edit)

        self._username_edit = QLineEdit()
        basic_layout.addRow('Username:', self._username_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.Password)
        basic_layout.addRow('Password:', self._password_edit)

        self._database_edit = QLineEdit()
        self._database_edit.setPlaceholderText('Database/Library name')
        basic_layout.addRow('Database:', self._database_edit)

        self._readonly_checkbox = QCheckBox('Read-only connection (recommended)')
        self._readonly_checkbox.setChecked(True)
        basic_layout.addRow('', self._readonly_checkbox)

        main_layout.addWidget(basic_group)

        # Connection type specific settings
        self._settings_stack = QStackedWidget()

        # AS400 settings
        as400_widget = QWidget()
        as400_layout = QFormLayout(as400_widget)

        self._as400_server_edit = QLineEdit()
        self._as400_server_edit.setPlaceholderText('AS400 server address')
        as400_layout.addRow('Server:', self._as400_server_edit)

        self._as400_port_spin = QSpinBox()
        self._as400_port_spin.setRange(1, 65535)
        self._as400_port_spin.setValue(446)
        as400_layout.addRow('Port:', self._as400_port_spin)

        self._as400_ssl_checkbox = QCheckBox('Use SSL for connection')
        self._as400_ssl_checkbox.setChecked(True)
        as400_layout.addRow('', self._as400_ssl_checkbox)

        jar_layout = QHBoxLayout()
        self._as400_jar_edit = QLineEdit()
        self._as400_jar_edit.setPlaceholderText('Path to jt400.jar file')

        browse_button = QPushButton('Browse...')
        browse_button.clicked.connect(self._browse_jar)

        autodetect_button = QPushButton('Auto-detect')
        autodetect_button.clicked.connect(self._autodetect_jar)

        jar_layout.addWidget(self._as400_jar_edit, 1)
        jar_layout.addWidget(browse_button)
        jar_layout.addWidget(autodetect_button)

        as400_layout.addRow('JT400 JAR:', jar_layout)

        self._as400_allowed_libraries_edit = QLineEdit()
        self._as400_allowed_libraries_edit.setPlaceholderText('Comma-separated library names, or leave empty for all')
        as400_layout.addRow('Allowed Libraries:', self._as400_allowed_libraries_edit)

        self._settings_stack.addWidget(as400_widget)

        # ODBC settings
        odbc_widget = QWidget()
        odbc_layout = QFormLayout(odbc_widget)

        self._odbc_dsn_edit = QLineEdit()
        self._odbc_dsn_edit.setPlaceholderText('ODBC Data Source Name')
        odbc_layout.addRow('DSN:', self._odbc_dsn_edit)

        self._odbc_server_edit = QLineEdit()
        self._odbc_server_edit.setPlaceholderText('Optional server address')
        odbc_layout.addRow('Server:', self._odbc_server_edit)

        self._odbc_port_spin = QSpinBox()
        self._odbc_port_spin.setRange(1, 65535)
        self._odbc_port_spin.setValue(0)
        odbc_layout.addRow('Port:', self._odbc_port_spin)

        self._odbc_connection_string_edit = QLineEdit()
        self._odbc_connection_string_edit.setPlaceholderText('Optional full connection string (alternative to DSN)')
        odbc_layout.addRow('Connection String:', self._odbc_connection_string_edit)

        self._settings_stack.addWidget(odbc_widget)

        # SQLite settings
        sqlite_widget = QWidget()
        sqlite_layout = QFormLayout(sqlite_widget)

        self._sqlite_db_path_layout = QHBoxLayout()
        self._sqlite_db_path_edit = QLineEdit()
        self._sqlite_db_path_edit.setPlaceholderText('Path to SQLite database file or :memory: for in-memory DB')

        self._sqlite_browse_button = QPushButton('Browse...')
        self._sqlite_browse_button.clicked.connect(self._browse_sqlite_db)

        self._sqlite_db_path_layout.addWidget(self._sqlite_db_path_edit, 1)
        self._sqlite_db_path_layout.addWidget(self._sqlite_browse_button)

        sqlite_layout.addRow('Database File:', self._sqlite_db_path_layout)

        # SQLite version info (will be populated at runtime)
        self._sqlite_version_label = QLabel('SQLite version information will be shown after connection')
        sqlite_layout.addRow('SQLite Version:', self._sqlite_version_label)

        self._sqlite_in_memory_checkbox = QCheckBox('Use in-memory database')
        self._sqlite_in_memory_checkbox.setChecked(False)
        self._sqlite_in_memory_checkbox.stateChanged.connect(self._on_in_memory_toggled)
        sqlite_layout.addRow('', self._sqlite_in_memory_checkbox)

        self._settings_stack.addWidget(sqlite_widget)

        main_layout.addWidget(self._settings_stack)

        # Advanced settings
        advanced_group = QGroupBox('Advanced Settings')
        advanced_layout = QFormLayout(advanced_group)

        self._timeout_group = QGroupBox('Timeouts')
        timeout_layout = QFormLayout(self._timeout_group)

        self._conn_timeout_spin = QSpinBox()
        self._conn_timeout_spin.setRange(1, 300)
        self._conn_timeout_spin.setValue(30)
        self._conn_timeout_spin.setSuffix(' seconds')

        self._query_timeout_spin = QSpinBox()
        self._query_timeout_spin.setRange(1, 3600)
        self._query_timeout_spin.setValue(60)
        self._query_timeout_spin.setSuffix(' seconds')

        timeout_layout.addRow('Connection Timeout:', self._conn_timeout_spin)
        timeout_layout.addRow('Query Timeout:', self._query_timeout_spin)

        self._allowed_tables_edit = QLineEdit()
        self._allowed_tables_edit.setPlaceholderText('Comma-separated table names, or leave empty for all')

        self._encrypt_checkbox = QCheckBox('Encrypt connection parameters')
        self._encrypt_checkbox.setChecked(True)

        advanced_layout.addWidget(self._timeout_group)
        advanced_layout.addRow('Allowed Tables:', self._allowed_tables_edit)
        advanced_layout.addRow('', self._encrypt_checkbox)

        main_layout.addWidget(advanced_group)

        # Buttons
        button_layout = QHBoxLayout()

        self._test_button = QPushButton('Test Connection')
        self._test_button.clicked.connect(self._test_connection)

        button_layout.addWidget(self._test_button)
        button_layout.addStretch()

        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        button_layout.addWidget(self._button_box)

        main_layout.addLayout(button_layout)

        # Select the appropriate connection type
        if self._connection:
            index = self._type_combo.findData(self._connection.connection_type)
            if index >= 0:
                self._type_combo.setCurrentIndex(index)
        else:
            self._type_combo.setCurrentIndex(0)
            self._on_type_changed(0)

    def _on_type_changed(self, index: int) -> None:
        """Handle connection type changes.

        Args:
            index: Selected combo box index
        """
        conn_type = self._type_combo.itemData(index)
        self._settings_stack.setCurrentIndex(index)

        # Update database label based on connection type
        database_label = 'Database:'

        if conn_type == ConnectionType.AS400:
            database_label = 'Library:'

            # Make username/password visible
            self._username_edit.setEnabled(True)
            self._password_edit.setEnabled(True)

        elif conn_type == ConnectionType.ODBC:
            database_label = 'Database/File:'

            # Make username/password visible
            self._username_edit.setEnabled(True)
            self._password_edit.setEnabled(True)

        elif conn_type == ConnectionType.SQLITE:
            database_label = 'Database Name:'

            # For SQLite, username/password aren't necessary
            self._username_edit.setText('sqlite')
            self._username_edit.setEnabled(False)
            self._password_edit.setText('')
            self._password_edit.setEnabled(False)

        # Update the database label
        for i in range(self._settings_stack.parentWidget().layout().count()):
            label_item = self._settings_stack.parentWidget().layout().itemAt(i)
            if label_item and isinstance(label_item.widget(), QLabel):
                label = label_item.widget()
                if label.text().startswith('Database:'):
                    label.setText(database_label)
                    break

    def _on_in_memory_toggled(self, state: int) -> None:
        """Handle in-memory database toggle.

        Args:
            state: Checkbox state
        """
        if state == Qt.Checked:
            # Save the current path
            self._old_sqlite_path = self._sqlite_db_path_edit.text()
            self._sqlite_db_path_edit.setText(':memory:')
            self._sqlite_db_path_edit.setEnabled(False)
            self._sqlite_browse_button.setEnabled(False)
        else:
            # Restore the saved path or use empty string
            self._sqlite_db_path_edit.setText(getattr(self, '_old_sqlite_path', ''))
            self._sqlite_db_path_edit.setEnabled(True)
            self._sqlite_browse_button.setEnabled(True)

    def _populate_fields(self, connection: BaseConnectionConfig) -> None:
        """Populate dialog fields from a connection config.

        Args:
            connection: Connection configuration
        """
        self._name_edit.setText(connection.name)
        self._username_edit.setText(connection.username)
        self._password_edit.setText(connection.password.get_secret_value())
        self._database_edit.setText(connection.database)
        self._readonly_checkbox.setChecked(connection.read_only)
        self._conn_timeout_spin.setValue(connection.connection_timeout)
        self._query_timeout_spin.setValue(connection.query_timeout)
        self._encrypt_checkbox.setChecked(connection.encrypt_connection)

        if connection.allowed_tables:
            self._allowed_tables_edit.setText(', '.join(connection.allowed_tables))

        # Populate type-specific fields
        if isinstance(connection, AS400ConnectionConfig):
            self._as400_server_edit.setText(connection.server)
            if connection.port is not None:
                self._as400_port_spin.setValue(connection.port)
            self._as400_ssl_checkbox.setChecked(connection.ssl)
            self._as400_jar_edit.setText(connection.jt400_jar_path)
            if connection.allowed_libraries:
                self._as400_allowed_libraries_edit.setText(', '.join(connection.allowed_libraries))

        elif isinstance(connection, ODBCConnectionConfig):
            self._odbc_dsn_edit.setText(connection.dsn)
            if connection.server:
                self._odbc_server_edit.setText(connection.server)
            if connection.port:
                self._odbc_port_spin.setValue(connection.port)
            if connection.connection_string:
                self._odbc_connection_string_edit.setText(connection.connection_string)

        elif isinstance(connection, SQLiteConnectionConfig):
            if connection.database == ':memory:':
                self._sqlite_in_memory_checkbox.setChecked(True)
                self._old_sqlite_path = ''  # Store empty path as backup
            else:
                self._sqlite_in_memory_checkbox.setChecked(False)
                self._sqlite_db_path_edit.setText(connection.database)

    def _browse_jar(self) -> None:
        """Show file dialog to browse for JT400 JAR file."""
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select JT400 JAR File', '', 'JAR Files (*.jar)')
        if file_path:
            self._as400_jar_edit.setText(file_path)

    def _autodetect_jar(self) -> None:
        """Try to automatically detect the JT400 JAR file."""
        jar_paths = guess_jar_locations()
        if not jar_paths:
            QMessageBox.warning(
                self, 'JAR Not Found',
                'Could not automatically detect jt400.jar file. Please specify it manually.'
            )
            return

        self._as400_jar_edit.setText(jar_paths[0])
        QMessageBox.information(self, 'JAR Found', f'Found jt400.jar at: {jar_paths[0]}')

    def _browse_sqlite_db(self) -> None:
        """Show file dialog to browse for SQLite database file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Select or Create SQLite Database File', '',
            'SQLite Databases (*.db *.sqlite *.sqlite3);;All Files (*.*)'
        )

        if file_path:
            self._sqlite_db_path_edit.setText(file_path)

    def _test_connection(self) -> None:
        """Test the database connection."""
        try:
            config = self.get_connection_config()
            QMessageBox.information(
                self, 'Connection Test',
                'Connection test would normally connect to the database.\n\nPlease click OK to proceed with the test.'
            )

            # Perform actual connection test
            import asyncio
            plugin = self.parent().parent()._plugin
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                success, error = loop.run_until_complete(plugin.test_connection(config))
                if success:
                    QMessageBox.information(self, 'Connection Test', 'Connection test successful!')
                else:
                    QMessageBox.critical(self, 'Connection Test Failed', f'Connection test failed: {error}')
            finally:
                loop.close()

        except Exception as e:
            QMessageBox.critical(
                self, 'Invalid Connection Configuration',
                f'Failed to create connection configuration: {str(e)}'
            )

    def get_connection_config(self) -> BaseConnectionConfig:
        """Create a connection configuration from dialog fields.

        Returns:
            Connection configuration object

        Raises:
            ValueError: If invalid input is provided
        """
        connection_type = self._type_combo.currentData()

        # Common parameters for all connection types
        common_params = {
            'id': self._connection.id if self._connection else str(uuid.uuid4()),
            'name': self._name_edit.text().strip(),
            'connection_type': connection_type,
            'database': self._database_edit.text().strip(),
            'username': self._username_edit.text().strip(),
            'password': self._password_edit.text(),
            'connection_timeout': self._conn_timeout_spin.value(),
            'query_timeout': self._query_timeout_spin.value(),
            'encrypt_connection': self._encrypt_checkbox.isChecked(),
            'read_only': self._readonly_checkbox.isChecked()
        }

        # Validate common parameters
        if not common_params['name']:
            raise ValueError('Connection name is required')

        if not common_params['database'] and connection_type != ConnectionType.SQLITE:
            raise ValueError('Database name is required')

        if not common_params['username'] and connection_type != ConnectionType.SQLITE:
            raise ValueError('Username is required')

        if not common_params['password'] and connection_type != ConnectionType.SQLITE:
            raise ValueError('Password is required')

        # Process allowed tables
        allowed_tables_text = self._allowed_tables_edit.text().strip()
        if allowed_tables_text:
            common_params['allowed_tables'] = [
                t.strip().upper() for t in allowed_tables_text.split(',') if t.strip()
            ]

        # Type-specific parameters
        if connection_type == ConnectionType.AS400:
            as400_params = {
                'server': self._as400_server_edit.text().strip(),
                'port': self._as400_port_spin.value(),
                'ssl': self._as400_ssl_checkbox.isChecked(),
                'jt400_jar_path': self._as400_jar_edit.text().strip()
            }

            # Validate AS400-specific parameters
            if not as400_params['server']:
                raise ValueError('Server address is required')

            if not as400_params['jt400_jar_path']:
                raise ValueError('JT400 JAR path is required')

            if not os.path.exists(as400_params['jt400_jar_path']):
                raise ValueError(f"JT400 JAR file not found: {as400_params['jt400_jar_path']}")

            # Process allowed libraries
            allowed_libs_text = self._as400_allowed_libraries_edit.text().strip()
            if allowed_libs_text:
                as400_params['allowed_libraries'] = [
                    lib.strip().upper() for lib in allowed_libs_text.split(',') if lib.strip()
                ]

            return AS400ConnectionConfig(**common_params, **as400_params)

        elif connection_type == ConnectionType.ODBC:
            odbc_params = {
                'dsn': self._odbc_dsn_edit.text().strip(),
                'server': self._odbc_server_edit.text().strip() or None,
                'port': self._odbc_port_spin.value() if self._odbc_port_spin.value() > 0 else None,
                'connection_string': self._odbc_connection_string_edit.text().strip() or None
            }

            # Validate ODBC-specific parameters
            if not odbc_params['dsn'] and (not odbc_params['connection_string']):
                raise ValueError('Either DSN or connection string is required')

            return ODBCConnectionConfig(**common_params, **odbc_params)

        elif connection_type == ConnectionType.SQLITE:
            sqlite_params = {}

            # For SQLite, handle in-memory or file database
            if self._sqlite_in_memory_checkbox.isChecked():
                sqlite_params['database'] = ':memory:'
            else:
                db_path = self._sqlite_db_path_edit.text().strip()
                if not db_path:
                    raise ValueError('SQLite database path is required')
                sqlite_params['database'] = db_path

            # Username and password are not used for SQLite but required by model,
            # so we provide default values if they're empty
            if not common_params['username']:
                common_params['username'] = 'sqlite'

            if not common_params['password']:
                common_params['password'] = ''

            return SQLiteConnectionConfig(**common_params, **sqlite_params)

        # Default case (should not happen with proper UI constraints)
        return BaseConnectionConfig(**common_params)


class ConnectionManagerDialog(QDialog):
    """Dialog for managing multiple database connections."""

    def __init__(self, connections: Dict[str, BaseConnectionConfig], parent: Optional[QWidget] = None) -> None:
        """Initialize the connection manager dialog.

        Args:
            connections: Dictionary of available connections
            parent: Parent widget
        """
        super().__init__(parent)
        self._connections = connections.copy()
        self._init_ui()
        self.setWindowTitle('Manage Database Connections')

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        main_layout = QVBoxLayout(self)

        # Connections list
        list_label = QLabel('Available Connections:')
        list_label.setFont(QFont('Arial', 10, QFont.Bold))
        main_layout.addWidget(list_label)

        self._conn_list = QListWidget()
        self._conn_list.setSelectionMode(QListWidget.SingleSelection)
        self._conn_list.itemSelectionChanged.connect(self._on_selection_changed)
        self._populate_connection_list()
        main_layout.addWidget(self._conn_list)

        # Connection details
        details_group = QGroupBox('Connection Details')
        details_layout = QFormLayout(details_group)

        self._details_type = QLabel('')
        self._details_server = QLabel('')
        self._details_database = QLabel('')
        self._details_username = QLabel('')

        details_layout.addRow('Type:', self._details_type)
        details_layout.addRow('Server:', self._details_server)
        details_layout.addRow('Database:', self._details_database)
        details_layout.addRow('Username:', self._details_username)

        main_layout.addWidget(details_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self._add_button = QPushButton('Add')
        self._add_button.clicked.connect(self._add_connection)

        self._edit_button = QPushButton('Edit')
        self._edit_button.clicked.connect(self._edit_connection)
        self._edit_button.setEnabled(False)

        self._delete_button = QPushButton('Delete')
        self._delete_button.clicked.connect(self._delete_connection)
        self._delete_button.setEnabled(False)

        self._test_button = QPushButton('Test')
        self._test_button.clicked.connect(self._test_connection)
        self._test_button.setEnabled(False)

        button_layout.addWidget(self._add_button)
        button_layout.addWidget(self._edit_button)
        button_layout.addWidget(self._delete_button)
        button_layout.addWidget(self._test_button)
        button_layout.addStretch()

        self._default_button = QPushButton('Set as Default')
        self._default_button.clicked.connect(self._set_as_default)
        self._default_button.setEnabled(False)

        button_layout.addWidget(self._default_button)

        main_layout.addLayout(button_layout)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)

        main_layout.addWidget(dialog_buttons)

    def _populate_connection_list(self) -> None:
        """Populate the connections list."""
        self._conn_list.clear()
        sorted_connections = sorted(self._connections.values(), key=lambda c: c.name.lower())

        for conn in sorted_connections:
            item = QListWidgetItem(conn.name)
            item.setData(Qt.UserRole, conn.id)
            self._conn_list.addItem(item)

    def _on_selection_changed(self) -> None:
        """Handle list selection changes."""
        has_selection = len(self._conn_list.selectedItems()) > 0
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)
        self._test_button.setEnabled(has_selection)
        self._default_button.setEnabled(has_selection)

        if has_selection:
            self._update_details()
        else:
            self._clear_details()

    def _update_details(self) -> None:
        """Update detail fields with selected connection info."""
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return

        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return

        conn = self._connections[conn_id]
        self._details_type.setText(str(conn.connection_type))

        # Handle different connection types
        if conn.connection_type == ConnectionType.SQLITE:
            self._details_server.setText('Local SQLite')

        elif hasattr(conn, 'server'):
            server = getattr(conn, 'server', '')
            port = getattr(conn, 'port', None)
            self._details_server.setText(f"{server}{(':' + str(port) if port else '')}")

        elif hasattr(conn, 'dsn'):
            self._details_server.setText(f'DSN: {conn.dsn}')

        else:
            self._details_server.setText('N/A')

        self._details_database.setText(conn.database)
        self._details_username.setText(conn.username)

    def _clear_details(self) -> None:
        """Clear detail fields."""
        self._details_type.setText('')
        self._details_server.setText('')
        self._details_database.setText('')
        self._details_username.setText('')

    def _add_connection(self) -> None:
        """Add a new connection."""
        dialog = ConnectionDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_connection = dialog.get_connection_config()
            self._connections[new_connection.id] = new_connection
            self._populate_connection_list()

            # Select the new connection
            for i in range(self._conn_list.count()):
                item = self._conn_list.item(i)
                if item and item.data(Qt.UserRole) == new_connection.id:
                    self._conn_list.setCurrentItem(item)
                    break

    def _edit_connection(self) -> None:
        """Edit the selected connection."""
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return

        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return

        dialog = ConnectionDialog(parent=self, connection=self._connections[conn_id])
        if dialog.exec() == QDialog.Accepted:
            updated_connection = dialog.get_connection_config()
            self._connections[updated_connection.id] = updated_connection
            self._populate_connection_list()

            # Reselect the edited connection
            for i in range(self._conn_list.count()):
                item = self._conn_list.item(i)
                if item and item.data(Qt.UserRole) == updated_connection.id:
                    self._conn_list.setCurrentItem(item)
                    break

    def _delete_connection(self) -> None:
        """Delete the selected connection."""
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return

        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return

        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f"Are you sure you want to delete the connection '{self._connections[conn_id].name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self._connections[conn_id]
            self._populate_connection_list()
            self._clear_details()

    def _test_connection(self) -> None:
        """Test the selected connection."""
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return

        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return

        conn = self._connections[conn_id]
        QMessageBox.information(
            self, 'Connection Test',
            f'Testing connection to {conn.name}...\n\nPlease click OK to proceed with the test.'
        )

        # Perform actual connection test
        import asyncio
        plugin = self.parent().parent()._plugin
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            success, error = loop.run_until_complete(plugin.test_connection(conn))
            if success:
                QMessageBox.information(self, 'Connection Test', 'Connection test successful!')
            else:
                QMessageBox.critical(self, 'Connection Test Failed', f'Connection test failed: {error}')
        finally:
            loop.close()

    def _set_as_default(self) -> None:
        """Set the selected connection as the default."""
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return

        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return

        import asyncio
        plugin = self.parent().parent()._plugin

        if plugin._settings:
            plugin._settings.default_connection_id = conn_id
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(plugin._save_settings())
                QMessageBox.information(
                    self, 'Default Connection',
                    f"Connection '{self._connections[conn_id].name}' will be used as the default."
                )
            finally:
                loop.close()

    def get_connections(self) -> Dict[str, BaseConnectionConfig]:
        """Get the updated connections.

        Returns:
            Dictionary of connection configurations
        """
        return self._connections.copy()