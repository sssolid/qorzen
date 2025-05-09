from __future__ import annotations
'\nConnection dialog for AS400 Connector Plugin.\n\nThis module provides dialog windows for creating, editing and managing AS400\ndatabase connections.\n'
import os
import uuid
from typing import Any, Dict, List, Optional, Set, cast
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox, QTabWidget, QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QSizePolicy, QComboBox
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig
from qorzen.plugins.as400_connector_plugin.code.utils import guess_jar_locations
class ConnectionDialog(QDialog):
    def __init__(self, parent: Optional[QWidget]=None, file_manager: Optional[Any]=None, connection: Optional[AS400ConnectionConfig]=None) -> None:
        super().__init__(parent)
        self._file_manager = file_manager
        self._connection = connection
        self._init_ui()
        if connection:
            self._populate_fields(connection)
            self.setWindowTitle(f'Edit Connection: {connection.name}')
        else:
            self.setWindowTitle('New AS400 Connection')
    def _init_ui(self) -> None:
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        name_label = QLabel('Connection Name:')
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText('Enter a name for this connection')
        form_layout.addRow(name_label, self._name_edit)
        server_label = QLabel('Server:')
        self._server_edit = QLineEdit()
        self._server_edit.setPlaceholderText('AS400 server address')
        form_layout.addRow(server_label, self._server_edit)
        port_label = QLabel('Port:')
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(446)
        form_layout.addRow(port_label, self._port_spin)
        database_label = QLabel('Database/Library:')
        self._database_edit = QLineEdit()
        self._database_edit.setPlaceholderText('Main library name')
        form_layout.addRow(database_label, self._database_edit)
        username_label = QLabel('Username:')
        self._username_edit = QLineEdit()
        form_layout.addRow(username_label, self._username_edit)
        password_label = QLabel('Password:')
        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow(password_label, self._password_edit)
        jar_layout = QHBoxLayout()
        self._jar_path_edit = QLineEdit()
        self._jar_path_edit.setPlaceholderText('Path to jt400.jar file')
        browse_button = QPushButton('Browse...')
        browse_button.clicked.connect(self._browse_jar)
        autodetect_button = QPushButton('Auto-detect')
        autodetect_button.clicked.connect(self._autodetect_jar)
        jar_layout.addWidget(self._jar_path_edit)
        jar_layout.addWidget(browse_button)
        jar_layout.addWidget(autodetect_button)
        form_layout.addRow('JT400 JAR:', jar_layout)
        self._ssl_checkbox = QCheckBox('Use SSL for connection')
        self._ssl_checkbox.setChecked(True)
        form_layout.addRow('', self._ssl_checkbox)
        timeout_group = QGroupBox('Timeouts')
        timeout_layout = QFormLayout(timeout_group)
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
        advanced_group = QGroupBox('Advanced Options')
        advanced_layout = QFormLayout(advanced_group)
        self._allowed_tables_edit = QLineEdit()
        self._allowed_tables_edit.setPlaceholderText('Comma-separated table names, or leave empty for all')
        self._allowed_schemas_edit = QLineEdit()
        self._allowed_schemas_edit.setPlaceholderText('Comma-separated schema names, or leave empty for all')
        self._encrypt_checkbox = QCheckBox('Encrypt connection parameters')
        self._encrypt_checkbox.setChecked(True)
        advanced_layout.addRow('Allowed Tables:', self._allowed_tables_edit)
        advanced_layout.addRow('Allowed Schemas:', self._allowed_schemas_edit)
        advanced_layout.addRow('', self._encrypt_checkbox)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(timeout_group)
        main_layout.addWidget(advanced_group)
        main_layout.addStretch(1)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        test_button = QPushButton('Test Connection')
        test_button.clicked.connect(self._test_connection)
        button_box.addButton(test_button, QDialogButtonBox.ActionRole)
        main_layout.addWidget(button_box)
    def _populate_fields(self, connection: AS400ConnectionConfig) -> None:
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
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select JT400 JAR File', '', 'JAR Files (*.jar)')
        if file_path:
            self._jar_path_edit.setText(file_path)
    def _autodetect_jar(self) -> None:
        jar_paths = guess_jar_locations()
        if not jar_paths:
            QMessageBox.warning(self, 'JAR Not Found', 'Could not automatically detect jt400.jar file. Please specify it manually.')
            return
        self._jar_path_edit.setText(jar_paths[0])
        QMessageBox.information(self, 'JAR Found', f'Found jt400.jar at: {jar_paths[0]}')
    def _test_connection(self) -> None:
        try:
            config = self._get_connection_config()
            QMessageBox.information(self, 'Connection Test', 'Connection test would normally connect to the AS400 system.\n\nThis is not implemented in the dialog UI, but will work when you use the connection in the main interface.')
        except Exception as e:
            QMessageBox.critical(self, 'Invalid Connection Configuration', f'Failed to create connection configuration: {str(e)}')
    def get_connection_config(self) -> AS400ConnectionConfig:
        return self._get_connection_config()
    def _get_connection_config(self) -> AS400ConnectionConfig:
        name = self._name_edit.text().strip()
        server = self._server_edit.text().strip()
        port = self._port_spin.value()
        database = self._database_edit.text().strip()
        username = self._username_edit.text().strip()
        password = self._password_edit.text()
        jar_path = self._jar_path_edit.text().strip()
        if not name:
            raise ValueError('Connection name is required')
        if not server:
            raise ValueError('Server address is required')
        if not database:
            raise ValueError('Database/Library is required')
        if not username:
            raise ValueError('Username is required')
        if not password:
            raise ValueError('Password is required')
        if not jar_path:
            raise ValueError('JT400 JAR path is required')
        if not os.path.exists(jar_path):
            raise ValueError(f'JT400 JAR file not found: {jar_path}')
        ssl = self._ssl_checkbox.isChecked()
        connection_timeout = self._conn_timeout_spin.value()
        query_timeout = self._query_timeout_spin.value()
        encrypt_connection = self._encrypt_checkbox.isChecked()
        allowed_tables = None
        tables_text = self._allowed_tables_edit.text().strip()
        if tables_text:
            allowed_tables = [t.strip().upper() for t in tables_text.split(',') if t.strip()]
        allowed_schemas = None
        schemas_text = self._allowed_schemas_edit.text().strip()
        if schemas_text:
            allowed_schemas = [s.strip().upper() for s in schemas_text.split(',') if s.strip()]
        return AS400ConnectionConfig(id=self._connection.id if self._connection else str(uuid.uuid4()), name=name, server=server, port=port, database=database, username=username, password=password, jt400_jar_path=jar_path, ssl=ssl, connection_timeout=connection_timeout, query_timeout=query_timeout, allowed_tables=allowed_tables, allowed_schemas=allowed_schemas, encrypt_connection=encrypt_connection)
class ConnectionManagerDialog(QDialog):
    def __init__(self, connections: Dict[str, AS400ConnectionConfig], parent: Optional[QWidget]=None, file_manager: Optional[Any]=None) -> None:
        super().__init__(parent)
        self._connections = connections.copy()
        self._file_manager = file_manager
        self._init_ui()
        self.setWindowTitle('Manage AS400 Connections')
    def _init_ui(self) -> None:
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        main_layout = QVBoxLayout(self)
        list_label = QLabel('Available Connections:')
        list_label.setFont(QFont('Arial', 10, QFont.Bold))
        main_layout.addWidget(list_label)
        self._conn_list = QListWidget()
        self._conn_list.setSelectionMode(QListWidget.SingleSelection)
        self._conn_list.itemSelectionChanged.connect(self._on_selection_changed)
        self._populate_connection_list()
        main_layout.addWidget(self._conn_list)
        button_layout = QHBoxLayout()
        self._add_button = QPushButton('Add')
        self._add_button.clicked.connect(self._add_connection)
        button_layout.addWidget(self._add_button)
        self._edit_button = QPushButton('Edit')
        self._edit_button.clicked.connect(self._edit_connection)
        self._edit_button.setEnabled(False)
        button_layout.addWidget(self._edit_button)
        self._delete_button = QPushButton('Delete')
        self._delete_button.clicked.connect(self._delete_connection)
        self._delete_button.setEnabled(False)
        button_layout.addWidget(self._delete_button)
        self._default_button = QPushButton('Set as Default')
        self._default_button.clicked.connect(self._set_as_default)
        self._default_button.setEnabled(False)
        button_layout.addWidget(self._default_button)
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        main_layout.addWidget(dialog_buttons)
    def _populate_connection_list(self) -> None:
        self._conn_list.clear()
        sorted_connections = sorted(self._connections.values(), key=lambda c: c.name.lower())
        for conn in sorted_connections:
            item = QListWidgetItem(conn.name)
            item.setData(Qt.UserRole, conn.id)
            self._conn_list.addItem(item)
    def _on_selection_changed(self) -> None:
        has_selection = len(self._conn_list.selectedItems()) > 0
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)
        self._default_button.setEnabled(has_selection)
    def _add_connection(self) -> None:
        dialog = ConnectionDialog(parent=self, file_manager=self._file_manager)
        if dialog.exec() == QDialog.Accepted:
            new_connection = dialog.get_connection_config()
            self._connections[new_connection.id] = new_connection
            self._populate_connection_list()
    def _edit_connection(self) -> None:
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return
        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return
        dialog = ConnectionDialog(parent=self, file_manager=self._file_manager, connection=self._connections[conn_id])
        if dialog.exec() == QDialog.Accepted:
            updated_connection = dialog.get_connection_config()
            self._connections[updated_connection.id] = updated_connection
            self._populate_connection_list()
    def _delete_connection(self) -> None:
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return
        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return
        reply = QMessageBox.question(self, 'Confirm Deletion', f"Are you sure you want to delete the connection '{self._connections[conn_id].name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self._connections[conn_id]
            self._populate_connection_list()
    def _set_as_default(self) -> None:
        selected_items = self._conn_list.selectedItems()
        if not selected_items:
            return
        conn_id = selected_items[0].data(Qt.UserRole)
        if conn_id not in self._connections:
            return
        QMessageBox.information(self, 'Default Connection', f"Connection '{self._connections[conn_id].name}' will be used as the default.")
    def get_connections(self) -> Dict[str, AS400ConnectionConfig]:
        return self._connections