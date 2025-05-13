from __future__ import annotations

import uuid

"""
Main tab UI component for the AS400 Connector Plugin.

This module provides the main UI tab for the AS400 Connector Plugin,
containing the query editor, connection management, and results display.
"""

import os
import datetime
import json
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, QSize, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
    QLineEdit, QTextEdit, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QDialog, QGroupBox, QFormLayout, QCheckBox,
    QSpinBox, QDialogButtonBox, QMenu, QToolButton, QProgressBar,
    QListWidget, QListWidgetItem, QInputDialog, QRadioButton,
    QButtonGroup, QScrollArea
)

from qorzen.plugins.as400_connector_plugin.code.models import (
    AS400ConnectionConfig,
    SavedQuery,
    QueryHistoryEntry,
    PluginSettings,
    QueryResult
)
from qorzen.plugins.as400_connector_plugin.code.connector import AS400Connector
from qorzen.plugins.as400_connector_plugin.code.utils import (
    load_connections,
    save_connections,
    load_saved_queries,
    save_queries,
    load_query_history,
    save_query_history,
    load_plugin_settings,
    save_plugin_settings,
    format_value_for_display,
    detect_query_parameters
)
from qorzen.plugins.as400_connector_plugin.code.ui.results_view import ResultsView
from qorzen.plugins.as400_connector_plugin.code.ui.visualization import VisualizationView


class AS400Tab(QWidget):
    """
    Main tab for the AS400 Connector Plugin.

    Provides a complete UI for connecting to AS400 databases,
    executing SQL queries, and viewing results.
    """

    queryStarted = Signal(str)
    queryFinished = Signal(str, bool)
    connectionChanged = Signal(str, bool)

    def __init__(
            self,
            event_bus_manager: Any,
            logger: Any,
            config: Any,
            file_manager: Any = None,
            thread_manager: Any = None,
            security_manager: Any = None,
            parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the AS400 tab.

        Args:
            event_bus_manager: The event bus manager for event handling
            logger: Logger for logging events
            config: Configuration manager for settings
            file_manager: Optional file manager for file operations
            thread_manager: Optional thread manager for background tasks
            security_manager: Optional security manager for security operations
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._event_bus = event_bus
        self._logger = logger
        self._config = config
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._security_manager = security_manager

        # Data
        self._connections: Dict[str, AS400ConnectionConfig] = {}
        self._saved_queries: Dict[str, SavedQuery] = {}
        self._query_history: List[QueryHistoryEntry] = []
        self._settings = PluginSettings()
        self._current_connection_id: Optional[str] = None
        self._active_connector: Optional[AS400Connector] = None
        self._current_query_result: Optional[QueryResult] = None

        # Initialize UI
        self._init_ui()

        # Load data
        self._load_data()

        # Update UI based on loaded data
        self._update_connection_combo()
        self._update_saved_queries_list()
        self._update_history_list()

    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QToolBar("AS400 Tools")
        toolbar.setIconSize(QSize(16, 16))

        # Connection controls
        connection_label = QLabel("Connection:")
        self._connection_combo = QComboBox()
        self._connection_combo.setMinimumWidth(200)
        self._connection_combo.currentIndexChanged.connect(self._on_connection_selected)

        # Connection management buttons
        self._connect_button = QPushButton("Connect")
        self._connect_button.clicked.connect(self._on_connect_button_clicked)

        self._manage_connections_button = QToolButton()
        self._manage_connections_button.setText("...")
        self._manage_connections_button.setPopupMode(QToolButton.InstantPopup)

        # Connection management menu
        connections_menu = QMenu(self)
        new_conn_action = connections_menu.addAction("New Connection...")
        new_conn_action.triggered.connect(self._on_new_connection)

        edit_conn_action = connections_menu.addAction("Edit Current Connection...")
        edit_conn_action.triggered.connect(self._on_edit_connection)

        delete_conn_action = connections_menu.addAction("Delete Current Connection")
        delete_conn_action.triggered.connect(self._on_delete_connection)

        self._manage_connections_button.setMenu(connections_menu)

        # Query execution button
        self._execute_button = QPushButton("Execute")
        self._execute_button.setShortcut(QKeySequence("F5"))
        self._execute_button.clicked.connect(self._execute_current_query)

        # Add widgets to toolbar
        toolbar.addWidget(connection_label)
        toolbar.addWidget(self._connection_combo)
        toolbar.addWidget(self._connect_button)
        toolbar.addWidget(self._manage_connections_button)
        toolbar.addSeparator()
        toolbar.addWidget(self._execute_button)

        # Add query options
        toolbar.addSeparator()
        limit_label = QLabel("Limit:")
        toolbar.addWidget(limit_label)

        self._limit_spin = QSpinBox()
        self._limit_spin.setMinimum(1)
        self._limit_spin.setMaximum(100000)
        self._limit_spin.setValue(1000)
        self._limit_spin.setFixedWidth(80)
        toolbar.addWidget(self._limit_spin)

        # Add toolbar to layout
        main_layout.addWidget(toolbar)

        # Create main splitter
        self._main_splitter = QSplitter(Qt.Vertical)

        # Upper section - Query editor and saved queries
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)
        upper_layout.setContentsMargins(5, 5, 5, 5)

        # Left side - Saved queries and history
        left_tabs = QTabWidget()

        # Saved queries tab
        saved_queries_widget = QWidget()
        saved_queries_layout = QVBoxLayout(saved_queries_widget)

        # Saved queries list
        self._saved_queries_list = QListWidget()
        self._saved_queries_list.itemDoubleClicked.connect(self._on_saved_query_double_clicked)

        # Saved queries toolbar
        saved_queries_toolbar = QToolBar()
        saved_queries_toolbar.setIconSize(QSize(16, 16))

        new_query_action = saved_queries_toolbar.addAction("New")
        new_query_action.triggered.connect(self._on_new_query)

        save_query_action = saved_queries_toolbar.addAction("Save")
        save_query_action.triggered.connect(self._on_save_query)

        delete_query_action = saved_queries_toolbar.addAction("Delete")
        delete_query_action.triggered.connect(self._on_delete_query)

        saved_queries_layout.addWidget(saved_queries_toolbar)
        saved_queries_layout.addWidget(self._saved_queries_list)

        # History tab
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)

        self._history_list = QListWidget()
        self._history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)

        # History toolbar
        history_toolbar = QToolBar()
        history_toolbar.setIconSize(QSize(16, 16))

        clear_history_action = history_toolbar.addAction("Clear")
        clear_history_action.triggered.connect(self._on_clear_history)

        save_history_action = history_toolbar.addAction("Save as Query")
        save_history_action.triggered.connect(self._on_save_history_as_query)

        history_layout.addWidget(history_toolbar)
        history_layout.addWidget(self._history_list)

        # Add tabs to left side
        left_tabs.addTab(saved_queries_widget, "Saved Queries")
        left_tabs.addTab(history_widget, "History")

        # Right side - Query editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        editor_label = QLabel("SQL Query:")
        self._query_editor = QTextEdit()
        self._query_editor.setFont(QFont("Courier New", 10))
        self._query_editor.setAcceptRichText(False)
        self._query_editor.setLineWrapMode(QTextEdit.NoWrap)

        # Query editor toolbar
        editor_toolbar = QToolBar()
        editor_toolbar.setIconSize(QSize(16, 16))

        clear_editor_action = editor_toolbar.addAction("Clear")
        clear_editor_action.triggered.connect(self._query_editor.clear)

        format_query_action = editor_toolbar.addAction("Format SQL")
        format_query_action.triggered.connect(self._format_sql)

        editor_layout.addWidget(editor_label)
        editor_layout.addWidget(editor_toolbar)
        editor_layout.addWidget(self._query_editor)

        # Add query params section
        params_label = QLabel("Query Parameters:")
        self._params_widget = QWidget()
        self._params_layout = QFormLayout(self._params_widget)

        editor_layout.addWidget(params_label)
        editor_layout.addWidget(self._params_widget)

        # Add left and right sides to upper layout
        upper_splitter = QSplitter(Qt.Horizontal)
        upper_splitter.addWidget(left_tabs)
        upper_splitter.addWidget(editor_widget)
        upper_splitter.setStretchFactor(0, 1)
        upper_splitter.setStretchFactor(1, 3)

        upper_layout.addWidget(upper_splitter)

        # Lower section - Results
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(5, 5, 5, 5)

        results_label = QLabel('Results:')
        results_layout.addWidget(results_label)

        # Create tabbed interface for results and visualization
        results_tabs = QTabWidget()

        # Results view tab
        self._results_view = ResultsView()
        results_tabs.addTab(self._results_view, "Data")

        # Visualization tab
        self._viz_view = VisualizationView()
        results_tabs.addTab(self._viz_view, "Visualization")

        results_layout.addWidget(results_tabs)

        # Add sections to main splitter
        self._main_splitter.addWidget(upper_widget)
        self._main_splitter.addWidget(results_widget)
        self._main_splitter.setStretchFactor(0, 1)
        self._main_splitter.setStretchFactor(1, 2)

        # Add main splitter to layout
        main_layout.addWidget(self._main_splitter)

        # Status bar
        self._status_bar = QStatusBar()
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setFixedWidth(100)
        self._progress_bar.setVisible(False)

        self._status_label = QLabel("Ready")
        self._status_bar.addWidget(self._status_label, 1)
        self._status_bar.addPermanentWidget(self._progress_bar)

        main_layout.addWidget(self._status_bar)

        # Connect signals
        self._query_editor.textChanged.connect(self._on_query_text_changed)
        self.queryStarted.connect(self._on_query_started)
        self.queryFinished.connect(self._on_query_finished)
        self.connectionChanged.connect(self._on_connection_status_changed)

    def _load_data(self) -> None:
        """Load saved data for the plugin."""
        # Load connections
        if self._file_manager:
            self._connections = load_connections(self._file_manager)
            self._saved_queries = load_saved_queries(self._file_manager)
            self._query_history = load_query_history(self._file_manager)

        # Load settings
        self._settings = load_plugin_settings(self._config)

        # Set default connection if available
        if self._settings.default_connection_id in self._connections:
            self._current_connection_id = self._settings.default_connection_id

    def _update_connection_combo(self) -> None:
        """Update the connections dropdown."""
        self._connection_combo.clear()

        # Add "Select a connection" placeholder
        self._connection_combo.addItem("Select a connection...", None)

        # Add all connections
        for conn_id, conn in self._connections.items():
            self._connection_combo.addItem(conn.name, conn_id)

        # Set current connection if any
        if self._current_connection_id:
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == self._current_connection_id:
                    self._connection_combo.setCurrentIndex(i)
                    break

    def _update_saved_queries_list(self) -> None:
        """Update the saved queries list."""
        self._saved_queries_list.clear()

        # Sort queries by name
        sorted_queries = sorted(
            self._saved_queries.values(),
            key=lambda q: q.name.lower()
        )

        # Add favorites first
        for query in [q for q in sorted_queries if q.is_favorite]:
            item = QListWidgetItem(f"⭐ {query.name}")
            item.setData(Qt.UserRole, query.id)
            self._saved_queries_list.addItem(item)

        # Add non-favorites
        for query in [q for q in sorted_queries if not q.is_favorite]:
            item = QListWidgetItem(query.name)
            item.setData(Qt.UserRole, query.id)
            self._saved_queries_list.addItem(item)

    def _update_history_list(self) -> None:
        """Update the query history list."""
        self._history_list.clear()

        # Add history items
        for entry in self._query_history:
            # Create display text
            display_text = entry.query_text.strip()
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."

            # Format timestamp
            timestamp = entry.executed_at.strftime("%Y-%m-%d %H:%M:%S")

            # Create item
            item = QListWidgetItem(f"{timestamp} - {display_text}")
            item.setData(Qt.UserRole, entry.id)

            # Color based on status
            if entry.status != "success":
                item.setForeground(Qt.red)

            self._history_list.addItem(item)

    def _on_connection_selected(self, index: int) -> None:
        """
        Handle selection of a connection from the dropdown.

        Args:
            index: The selected index
        """
        # Get connection ID
        conn_id = self._connection_combo.itemData(index)

        # Handle "Select a connection" placeholder
        if conn_id is None:
            self._current_connection_id = None
            self._connect_button.setText("Connect")
            self._connect_button.setEnabled(False)
            return

        # Set current connection
        self._current_connection_id = conn_id

        # Update connect button
        if self._active_connector and self._active_connector.is_connected():
            self._connect_button.setText("Disconnect")
        else:
            self._connect_button.setText("Connect")

        self._connect_button.setEnabled(True)

        # Update settings with the last used connection
        if self._settings.recent_connections and self._settings.recent_connections[0] != conn_id:
            # Add to recent list or move to front if already there
            if conn_id in self._settings.recent_connections:
                self._settings.recent_connections.remove(conn_id)
            self._settings.recent_connections.insert(0, conn_id)

            # Trim list to max 10 items
            self._settings.recent_connections = self._settings.recent_connections[:10]

            # Save settings
            save_plugin_settings(self._settings, self._config)

    def _on_connect_button_clicked(self) -> None:
        """Handle the connect/disconnect button click."""
        # Check if currently connected
        if self._active_connector and self._active_connector.is_connected():
            # Disconnect
            self._disconnect_from_as400()
        else:
            # Connect
            self._connect_to_as400()

    def _connect_to_as400(self) -> None:
        """Connect to the AS400 system using the current connection."""
        if not self._current_connection_id or self._current_connection_id not in self._connections:
            self._status_label.setText("No connection selected")
            return

        # Get the connection config
        conn_config = self._connections[self._current_connection_id]

        # Update UI to connecting state
        self._status_label.setText(f"Connecting to {conn_config.server}...")
        self._progress_bar.setVisible(True)
        self._connect_button.setEnabled(False)

        # Create the AS400 connector
        self._active_connector = AS400Connector(
            config=conn_config,
            logger=self._logger,
            security_manager=self._security_manager
        )

        # Start the connection in a background thread
        if self._thread_manager:
            # Use thread manager if available
            self._thread_manager.submit_task(
                func=self._connect_async,
                name=f"as400_connect_{conn_config.id}",
                submitter="as400_plugin"
            )
        else:
            # Fallback to simple thread for connection
            import threading
            thread = threading.Thread(
                target=self._connect_async,
                daemon=True
            )
            thread.start()

    def _connect_async(self) -> None:
        """Asynchronous connection function for background thread."""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Connect to the AS400 system
            loop.run_until_complete(self._active_connector.connect())

            # Signal successful connection
            self.connectionChanged.emit(self._current_connection_id, True)
        except Exception as e:
            # Log the error
            self._logger.error(
                f"AS400 connection error: {str(e)}",
                extra={"traceback": traceback.format_exc()}
            )

            # Signal connection failure
            self.connectionChanged.emit(self._current_connection_id, False)

            # Show error message to user
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect to AS400: {str(e)}"
            )
        finally:
            loop.close()

    def _disconnect_from_as400(self) -> None:
        """Disconnect from the AS400 system."""
        if not self._active_connector:
            return

        # Update UI
        self._status_label.setText("Disconnecting...")
        self._progress_bar.setVisible(True)
        self._connect_button.setEnabled(False)

        # Perform disconnect in background thread
        if self._thread_manager:
            self._thread_manager.submit_task(
                func=self._disconnect_async,
                name="as400_disconnect",
                submitter="as400_plugin"
            )
        else:
            # Fallback to simple thread
            import threading
            thread = threading.Thread(
                target=self._disconnect_async,
                daemon=True
            )
            thread.start()

    def _disconnect_async(self) -> None:
        """Asynchronous disconnection function for background thread."""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Disconnect from the AS400 system
            loop.run_until_complete(self._active_connector.close())

            # Signal successful disconnection
            self.connectionChanged.emit(self._current_connection_id, False)
        except Exception as e:
            # Log the error
            self._logger.error(
                f"AS400 disconnection error: {str(e)}",
                extra={"traceback": traceback.format_exc()}
            )

            # Signal disconnection anyway
            self.connectionChanged.emit(self._current_connection_id, False)
        finally:
            loop.close()

    def _on_connection_status_changed(self, connection_id: str, connected: bool) -> None:
        """
        Handle connection status changes.

        Args:
            connection_id: The ID of the connection
            connected: Whether the connection is established
        """
        # Update UI based on connection status
        if connected:
            self._status_label.setText(f"Connected to {self._connections[connection_id].server}")
            self._connect_button.setText("Disconnect")

            # Update connection label with connected state
            conn_name = self._connections[connection_id].name
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == connection_id:
                    self._connection_combo.setItemText(i, f"{conn_name} (Connected)")
                    break
        else:
            self._status_label.setText("Disconnected")
            self._connect_button.setText("Connect")

            # Reset active connector
            self._active_connector = None

            # Update connection label to remove connected state
            if connection_id in self._connections:
                conn_name = self._connections[connection_id].name
                for i in range(self._connection_combo.count()):
                    if self._connection_combo.itemData(i) == connection_id:
                        self._connection_combo.setItemText(i, conn_name)
                        break

        # Update UI controls
        self._progress_bar.setVisible(False)
        self._connect_button.setEnabled(True)
        self._execute_button.setEnabled(connected)

    def _on_new_connection(self) -> None:
        """Handle creating a new connection."""
        # Import connection dialog here to avoid circular imports
        from qorzen.plugins.as400_connector_plugin.code.ui.connection_dialog import ConnectionDialog

        # Create the dialog
        dialog = ConnectionDialog(
            parent=self,
            file_manager=self._file_manager
        )

        # Show the dialog
        if dialog.exec() == QDialog.Accepted:
            # Get the new connection config
            new_connection = dialog.get_connection_config()

            # Add to connections dictionary
            self._connections[new_connection.id] = new_connection

            # Save connections
            if self._file_manager:
                save_connections(self._connections, self._file_manager)

            # Update connection combo
            self._update_connection_combo()

            # Set as current connection
            self._current_connection_id = new_connection.id
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == new_connection.id:
                    self._connection_combo.setCurrentIndex(i)
                    break

            # Show success message
            self._status_label.setText(f"Created new connection: {new_connection.name}")

    def _on_edit_connection(self) -> None:
        """Handle editing the current connection."""
        if not self._current_connection_id or self._current_connection_id not in self._connections:
            QMessageBox.warning(
                self,
                "No Connection Selected",
                "Please select a connection to edit."
            )
            return

        # Check if currently connected
        if self._active_connector and self._active_connector.is_connected():
            QMessageBox.warning(
                self,
                "Connection Active",
                "Please disconnect before editing the connection."
            )
            return

        # Import connection dialog here to avoid circular imports
        from qorzen.plugins.as400_connector_plugin.ui.connection_dialog import ConnectionDialog

        # Create the dialog with existing connection
        dialog = ConnectionDialog(
            parent=self,
            file_manager=self._file_manager,
            connection=self._connections[self._current_connection_id]
        )

        # Show the dialog
        if dialog.exec() == QDialog.Accepted:
            # Get the updated connection config
            updated_connection = dialog.get_connection_config()

            # Update in connections dictionary
            self._connections[updated_connection.id] = updated_connection

            # Save connections
            if self._file_manager:
                save_connections(self._connections, self._file_manager)

            # Update connection combo
            self._update_connection_combo()

            # Show success message
            self._status_label.setText(f"Updated connection: {updated_connection.name}")

    def _on_delete_connection(self) -> None:
        """Handle deleting the current connection."""
        if not self._current_connection_id or self._current_connection_id not in self._connections:
            QMessageBox.warning(
                self,
                "No Connection Selected",
                "Please select a connection to delete."
            )
            return

        # Check if currently connected
        if self._active_connector and self._active_connector.is_connected():
            QMessageBox.warning(
                self,
                "Connection Active",
                "Please disconnect before deleting the connection."
            )
            return

        # Get connection name
        conn_name = self._connections[self._current_connection_id].name

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the connection '{conn_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove from connections dictionary
            del self._connections[self._current_connection_id]

            # Save connections
            if self._file_manager:
                save_connections(self._connections, self._file_manager)

            # Update UI
            self._update_connection_combo()
            self._status_label.setText(f"Deleted connection: {conn_name}")

            # Reset current connection
            self._current_connection_id = None

    def _on_query_text_changed(self) -> None:
        """Handle changes to the query text."""
        # Get the query text
        query_text = self._query_editor.toPlainText()

        # Detect parameters
        params = detect_query_parameters(query_text)

        # Update parameter controls
        self._update_parameter_controls(params)

    def _update_parameter_controls(self, param_names: List[str]) -> None:
        """
        Update the parameter input controls based on detected parameters.

        Args:
            param_names: List of parameter names detected in the query
        """
        # Clear existing parameters
        while self._params_layout.count() > 0:
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # If no parameters, hide the params widget
        if not param_names:
            self._params_widget.setVisible(False)
            return

        # Show parameters widget
        self._params_widget.setVisible(True)

        # Add input fields for each parameter
        for param_name in param_names:
            label = QLabel(f"{param_name}:")
            input_field = QLineEdit()
            input_field.setObjectName(f"param_{param_name}")

            self._params_layout.addRow(label, input_field)

    def _get_query_parameters(self) -> Dict[str, Any]:
        """
        Get parameter values from the input fields.

        Returns:
            Dictionary of parameter names and values
        """
        params = {}

        # Go through parameter input fields
        for i in range(self._params_layout.rowCount()):
            # Get the label and input widget
            label_item = self._params_layout.itemAt(i * 2)
            field_item = self._params_layout.itemAt(i * 2 + 1)

            if not label_item or not field_item:
                continue

            label = label_item.widget()
            field = field_item.widget()

            if not isinstance(label, QLabel) or not isinstance(field, QLineEdit):
                continue

            # Get parameter name from label
            param_name = label.text().rstrip(":")

            # Get parameter value from field
            param_value = field.text()

            # Try to convert to appropriate type
            if param_value.lower() == "null":
                params[param_name] = None
            elif param_value.isdigit():
                params[param_name] = int(param_value)
            elif param_value.replace(".", "", 1).isdigit():
                params[param_name] = float(param_value)
            elif param_value.lower() in ("true", "false"):
                params[param_name] = param_value.lower() == "true"
            else:
                params[param_name] = param_value

        return params

    def _execute_current_query(self) -> None:
        """Execute the current query in the editor."""
        # Check if connected
        if not self._active_connector or not self._active_connector.is_connected():
            QMessageBox.warning(
                self,
                "Not Connected",
                "Please connect to an AS400 database first."
            )
            return

        # Get the query text
        query_text = self._query_editor.toPlainText().strip()
        if not query_text:
            QMessageBox.warning(
                self,
                "Empty Query",
                "Please enter an SQL query to execute."
            )
            return

        # Get query parameters
        params = self._get_query_parameters()

        # Get limit
        limit = self._limit_spin.value()

        # Signal query start
        self.queryStarted.emit(query_text)

        # Execute the query in a background thread
        if self._thread_manager:
            self._thread_manager.submit_task(
                func=self._execute_query_async,
                query=query_text,
                limit=limit,
                params=params,
                name="as400_execute_query",
                submitter="as400_plugin"
            )
        else:
            # Fallback to simple thread
            import threading
            thread = threading.Thread(
                target=self._execute_query_async,
                args=(query_text, limit, params),
                daemon=True
            )
            thread.start()

    def _execute_query_async(self, query: str, limit: int, params: Dict[str, Any]) -> None:
        """
        Asynchronous query execution function for background thread.

        Args:
            query: SQL query text
            limit: Maximum number of results to return
            params: Query parameters
        """
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Execute the query
            result = loop.run_until_complete(
                self._active_connector.execute_query(
                    query=query,
                    limit=limit,
                    **params
                )
            )

            # Store the result
            self._current_query_result = result

            # Signal successful execution
            self.queryFinished.emit(query, True)

            # Add to query history
            self._add_to_query_history(
                query=query,
                params=params,
                result=result
            )
        except Exception as e:
            # Log the error
            self._logger.error(
                f"AS400 query error: {str(e)}",
                extra={"query": query, "traceback": traceback.format_exc()}
            )

            # Signal query failure
            self.queryFinished.emit(query, False)

            # Add to query history with error
            error_result = QueryResult(
                query=query,
                connection_id=self._current_connection_id,
                has_error=True,
                error_message=str(e)
            )
            self._add_to_query_history(
                query=query,
                params=params,
                result=error_result
            )

            # Show error message
            QMessageBox.critical(
                self,
                "Query Execution Error",
                f"Failed to execute query: {str(e)}"
            )
        finally:
            loop.close()

    def _on_query_started(self, query: str) -> None:
        """
        Handle query execution start.

        Args:
            query: The query being executed
        """
        # Update UI to show query in progress
        self._status_label.setText("Executing query...")
        self._progress_bar.setVisible(True)
        self._execute_button.setEnabled(False)

    def _on_query_finished(self, query: str, success: bool) -> None:
        self._progress_bar.setVisible(False)
        self._execute_button.setEnabled(True)
        if success and self._current_query_result:
            self._display_query_results(self._current_query_result)
            execution_time = self._current_query_result.execution_time_ms
            row_count = self._current_query_result.row_count
            self._status_label.setText(f'Query executed successfully in {execution_time} ms, {row_count} rows returned')
        else:
            self._status_label.setText('Query execution failed')

    def _add_to_query_history(self, query: str, params: Dict[str, Any], result: QueryResult) -> None:
        """
        Add an executed query to the history.

        Args:
            query: The SQL query text
            params: The query parameters
            result: The query execution result
        """
        # Create history entry
        history_entry = QueryHistoryEntry(
            query_text=query,
            connection_id=self._current_connection_id,
            executed_at=datetime.datetime.now(),
            execution_time_ms=result.execution_time_ms,
            row_count=result.row_count,
            parameters=params,
            status="error" if result.has_error else "success",
            error_message=result.error_message
        )

        # Add to history list
        self._query_history.insert(0, history_entry)

        # Trim history to limit
        self._query_history = self._query_history[:self._settings.query_history_limit]

        # Save history
        if self._file_manager:
            save_query_history(self._query_history, self._file_manager)

        # Update history list
        self._update_history_list()

    def _display_query_results(self, result: QueryResult) -> None:
        if not result.records or not result.columns:
            return
        self._results_view.set_query_result(result)
        self._viz_view.set_query_result(result)

    def _on_saved_query_double_clicked(self, item: QListWidgetItem) -> None:
        """
        Handle double-clicking a saved query.

        Args:
            item: The clicked list item
        """
        # Get query ID
        query_id = item.data(Qt.UserRole)
        if not query_id or query_id not in self._saved_queries:
            return

        # Get the query
        query = self._saved_queries[query_id]

        # Set query text in editor
        self._query_editor.setText(query.query_text)

        # If query has parameters, set them in the parameter fields
        if query.parameters:
            # Wait for parameter fields to update
            QTimer.singleShot(100, lambda: self._set_parameter_values(query.parameters))

    def _set_parameter_values(self, params: Dict[str, Any]) -> None:
        """
        Set parameter values in the parameter input fields.

        Args:
            params: The parameter values to set
        """
        # Iterate through parameter fields
        for i in range(self._params_layout.rowCount()):
            # Get the label and input widget
            label_item = self._params_layout.itemAt(i * 2)
            field_item = self._params_layout.itemAt(i * 2 + 1)

            if not label_item or not field_item:
                continue

            label = label_item.widget()
            field = field_item.widget()

            if not isinstance(label, QLabel) or not isinstance(field, QLineEdit):
                continue

            # Get parameter name from label
            param_name = label.text().rstrip(":")

            # Set parameter value if it exists
            if param_name in params:
                value = params[param_name]
                if value is None:
                    field.setText("NULL")
                else:
                    field.setText(str(value))

    def _on_history_item_double_clicked(self, item: QListWidgetItem) -> None:
        """
        Handle double-clicking a history item.

        Args:
            item: The clicked list item
        """
        # Get history entry ID
        entry_id = item.data(Qt.UserRole)

        # Find the entry
        entry = None
        for hist_entry in self._query_history:
            if hist_entry.id == entry_id:
                entry = hist_entry
                break

        if not entry:
            return

        # Set query text in editor
        self._query_editor.setText(entry.query_text)

        # If entry has parameters, set them in the parameter fields
        if entry.parameters:
            # Wait for parameter fields to update
            QTimer.singleShot(100, lambda: self._set_parameter_values(entry.parameters))

    def _on_new_query(self) -> None:
        """Handle creating a new query."""
        # Clear the query editor
        self._query_editor.clear()

        # Show dialog for query name
        name, ok = QInputDialog.getText(
            self,
            "New Query",
            "Enter a name for the new query:"
        )

        if ok and name:
            # Create a new saved query
            query = SavedQuery(
                name=name,
                query_text=""
            )

            # Add to saved queries
            self._saved_queries[query.id] = query

            # Save queries
            if self._file_manager:
                save_queries(self._saved_queries, self._file_manager)

            # Update UI
            self._update_saved_queries_list()

            # Show success message
            self._status_label.setText(f"Created new query: {name}")

    def _on_save_query(self) -> None:
        """Handle saving the current query."""
        # Get the query text
        query_text = self._query_editor.toPlainText().strip()
        if not query_text:
            QMessageBox.warning(
                self,
                "Empty Query",
                "Cannot save an empty query."
            )
            return

        # Show dialog for query name
        name, ok = QInputDialog.getText(
            self,
            "Save Query",
            "Enter a name for the query:",
            text=self._get_current_query_name()
        )

        if ok and name:
            # Get parameters
            params = self._get_query_parameters()

            # Create or update saved query
            query_id = self._get_current_query_id()

            if query_id and query_id in self._saved_queries:
                # Update existing query
                query = self._saved_queries[query_id]
                query.name = name
                query.query_text = query_text
                query.parameters = params
                query.updated_at = datetime.datetime.now()

                if self._current_connection_id:
                    query.connection_id = self._current_connection_id
            else:
                # Create new query
                query = SavedQuery(
                    name=name,
                    query_text=query_text,
                    parameters=params,
                    connection_id=self._current_connection_id
                )
                self._saved_queries[query.id] = query

            # Save queries
            if self._file_manager:
                save_queries(self._saved_queries, self._file_manager)

            # Update UI
            self._update_saved_queries_list()

            # Show success message
            self._status_label.setText(f"Saved query: {name}")

    def _get_current_query_name(self) -> str:
        """
        Get the name of the currently selected query.

        Returns:
            Query name or empty string
        """
        # Check if a saved query is selected
        selected_items = self._saved_queries_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            query_id = item.data(Qt.UserRole)
            if query_id in self._saved_queries:
                query_name = self._saved_queries[query_id].name
                # Remove favorite star if present
                if query_name.startswith("⭐ "):
                    return query_name[2:]
                return query_name

        # Default to empty string
        return ""

    def _get_current_query_id(self) -> Optional[str]:
        """
        Get the ID of the currently selected query.

        Returns:
            Query ID or None
        """
        # Check if a saved query is selected
        selected_items = self._saved_queries_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            return item.data(Qt.UserRole)
        return None

    def _on_delete_query(self) -> None:
        """Handle deleting the selected query."""
        # Check if a query is selected
        selected_items = self._saved_queries_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Query Selected",
                "Please select a query to delete."
            )
            return

        # Get the query
        item = selected_items[0]
        query_id = item.data(Qt.UserRole)

        if query_id not in self._saved_queries:
            return

        query = self._saved_queries[query_id]

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the query '{query.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove from saved queries
            del self._saved_queries[query_id]

            # Save queries
            if self._file_manager:
                save_queries(self._saved_queries, self._file_manager)

            # Update UI
            self._update_saved_queries_list()

            # Show success message
            self._status_label.setText(f"Deleted query: {query.name}")

    def _on_clear_history(self) -> None:
        """Handle clearing the query history."""
        # Confirm clearing
        reply = QMessageBox.question(
            self,
            "Confirm Clear History",
            "Are you sure you want to clear the query history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Clear history
            self._query_history = []

            # Save history
            if self._file_manager:
                save_query_history(self._query_history, self._file_manager)

            # Update UI
            self._update_history_list()

            # Show success message
            self._status_label.setText("Query history cleared")

    def _on_save_history_as_query(self) -> None:
        """Handle saving a history item as a saved query."""
        # Check if a history item is selected
        selected_items = self._history_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No History Item Selected",
                "Please select a history item to save as a query."
            )
            return

        # Get the history entry
        item = selected_items[0]
        entry_id = item.data(Qt.UserRole)

        # Find the entry
        entry = None
        for hist_entry in self._query_history:
            if hist_entry.id == entry_id:
                entry = hist_entry
                break

        if not entry:
            return

        # Show dialog for query name
        name, ok = QInputDialog.getText(
            self,
            "Save as Query",
            "Enter a name for the query:"
        )

        if ok and name:
            # Create new saved query
            query = SavedQuery(
                name=name,
                query_text=entry.query_text,
                parameters=entry.parameters,
                connection_id=entry.connection_id
            )

            # Add to saved queries
            self._saved_queries[query.id] = query

            # Save queries
            if self._file_manager:
                save_queries(self._saved_queries, self._file_manager)

            # Update UI
            self._update_saved_queries_list()

            # Show success message
            self._status_label.setText(f"Saved history item as query: {name}")

    def _export_results(self) -> None:
        """Handle exporting query results."""
        # Check if there are results to export
        if not self._current_query_result or not self._current_query_result.records:
            QMessageBox.warning(
                self,
                "No Results",
                "There are no results to export."
            )
            return

        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            # Determine export format
            if file_path.endswith(".csv"):
                self._export_as_csv(file_path)
            elif file_path.endswith(".json"):
                self._export_as_json(file_path)
            elif file_path.endswith(".xlsx"):
                self._export_as_excel(file_path)
            else:
                # Default to CSV
                if not file_path.endswith(".csv"):
                    file_path += ".csv"
                self._export_as_csv(file_path)

            # Show success message
            self._status_label.setText(f"Results exported to {file_path}")
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export results: {str(e)}"
            )

    def _export_as_csv(self, file_path: str) -> None:
        """
        Export results as CSV.

        Args:
            file_path: Path to save the CSV file
        """
        import csv

        with open(file_path, 'w', newline='') as f:
            # Get column names
            headers = [col.name for col in self._current_query_result.columns]

            # Create CSV writer
            writer = csv.DictWriter(f, fieldnames=headers)

            # Write header
            writer.writeheader()

            # Write data
            for record in self._current_query_result.records:
                # Convert None to empty string for CSV
                row = {k: "" if v is None else v for k, v in record.items()}
                writer.writerow(row)

    def _export_as_json(self, file_path: str) -> None:
        """
        Export results as JSON.

        Args:
            file_path: Path to save the JSON file
        """
        # Create export data
        export_data = {
            "query": self._current_query_result.query,
            "executed_at": self._current_query_result.executed_at.isoformat(),
            "execution_time_ms": self._current_query_result.execution_time_ms,
            "row_count": self._current_query_result.row_count,
            "records": self._current_query_result.records
        }

        # Write to file
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

    def _export_as_excel(self, file_path: str) -> None:
        """
        Export results as Excel.

        Args:
            file_path: Path to save the Excel file
        """
        try:
            import openpyxl
            from openpyxl import Workbook
        except ImportError:
            QMessageBox.critical(
                self,
                "Missing Dependency",
                "Excel export requires the openpyxl package. Please install it with 'pip install openpyxl'."
            )
            return

        # Create workbook
        wb = Workbook()
        ws = wb.active

        # Add title
        ws.title = "Query Results"

        # Add headers
        headers = [col.name for col in self._current_query_result.columns]
        ws.append(headers)

        # Add data
        for record in self._current_query_result.records:
            # Get values in column order
            row = [record.get(col) for col in headers]
            ws.append(row)

        # Save workbook
        wb.save(file_path)

    def _copy_selected_results(self) -> None:
        """Copy selected results to clipboard."""
        # Get selected cells
        selected_ranges = self._results_table.selectedRanges()
        if not selected_ranges:
            return

        # Build text for clipboard
        clipboard_text = ""

        for range_idx, cell_range in enumerate(selected_ranges):
            # Process each row in the range
            for row in range(cell_range.topRow(), cell_range.bottomRow() + 1):
                # Process each column in the range
                row_text = []
                for col in range(cell_range.leftColumn(), cell_range.rightColumn() + 1):
                    item = self._results_table.item(row, col)
                    if item:
                        cell_text = item.text()
                        # Quote if contains tab or newline
                        if '\t' in cell_text or '\n' in cell_text:
                            cell_text = f'"{cell_text}"'
                        row_text.append(cell_text)
                    else:
                        row_text.append("")

                # Add row to clipboard text
                clipboard_text += '\t'.join(row_text)
                clipboard_text += '\n'

            # Add extra newline between ranges
            if range_idx < len(selected_ranges) - 1:
                clipboard_text += '\n'

        # Copy to clipboard
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(clipboard_text)

        # Show success message
        self._status_label.setText(f"Copied {len(selected_ranges)} selection(s) to clipboard")

    def _format_sql(self) -> None:
        """Format the SQL query in the editor."""
        try:
            # Try to import sqlparse
            import sqlparse
        except ImportError:
            QMessageBox.warning(
                self,
                "Missing Dependency",
                "SQL formatting requires the sqlparse package. Please install it with 'pip install sqlparse'."
            )
            return

        # Get the query text
        query_text = self._query_editor.toPlainText()
        if not query_text.strip():
            return

        # Format the query
        formatted_query = sqlparse.format(
            query_text,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower',
            indent_width=4
        )

        # Set the formatted query
        self._query_editor.setText(formatted_query)

        # Show success message
        self._status_label.setText("SQL query formatted")

    def open_connection_dialog(self) -> None:
        """Open the connection dialog."""
        self._on_new_connection()

    def open_connection_manager(self) -> None:
        """Open the connection management dialog."""
        # Import here to avoid circular imports
        from qorzen.plugins.as400_connector_plugin.code.ui.connection_dialog import ConnectionManagerDialog

        # Create and show the dialog
        dialog = ConnectionManagerDialog(
            self._connections,
            parent=self,
            file_manager=self._file_manager
        )

        if dialog.exec() == QDialog.Accepted:
            # Get updated connections
            self._connections = dialog.get_connections()

            # Save connections
            if self._file_manager:
                save_connections(self._connections, self._file_manager)

            # Update UI
            self._update_connection_combo()

            # Show success message
            self._status_label.setText("Connection list updated")

    def import_queries(self) -> None:
        """Import saved queries from a file."""
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Queries",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Read the file
            with open(file_path, 'r') as f:
                imported_data = json.load(f)

            # Check if it's a valid query collection
            if not isinstance(imported_data, list):
                raise ValueError("Invalid query collection format")

            # Import queries
            imported_count = 0
            for query_data in imported_data:
                try:
                    # Convert datetime strings to datetime objects
                    if "created_at" in query_data and isinstance(query_data["created_at"], str):
                        query_data["created_at"] = datetime.datetime.fromisoformat(query_data["created_at"])
                    if "updated_at" in query_data and isinstance(query_data["updated_at"], str):
                        query_data["updated_at"] = datetime.datetime.fromisoformat(query_data["updated_at"])

                    # Create new ID to avoid duplicates
                    if "id" in query_data:
                        query_data["id"] = str(uuid.uuid4())

                    # Create the saved query
                    query = SavedQuery(**query_data)
                    self._saved_queries[query.id] = query
                    imported_count += 1
                except Exception:
                    # Skip invalid queries
                    continue

            # Save queries
            if self._file_manager and imported_count > 0:
                save_queries(self._saved_queries, self._file_manager)

            # Update UI
            self._update_saved_queries_list()

            # Show success message
            self._status_label.setText(f"Imported {imported_count} queries")
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import queries: {str(e)}"
            )

    def export_queries(self) -> None:
        """Export saved queries to a file."""
        if not self._saved_queries:
            QMessageBox.warning(
                self,
                "No Queries",
                "There are no saved queries to export."
            )
            return

        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Queries",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Ensure file has .json extension
            if not file_path.endswith('.json'):
                file_path += '.json'

            # Convert queries to JSON serializable format
            query_list = []
            for query in self._saved_queries.values():
                query_dict = query.dict()

                # Convert datetime to ISO format for JSON serialization
                if "created_at" in query_dict and isinstance(query_dict["created_at"], datetime.datetime):
                    query_dict["created_at"] = query_dict["created_at"].isoformat()
                if "updated_at" in query_dict and isinstance(query_dict["updated_at"], datetime.datetime):
                    query_dict["updated_at"] = query_dict["updated_at"].isoformat()

                query_list.append(query_dict)

            # Write to file
            with open(file_path, 'w') as f:
                json.dump(query_list, f, indent=2)

            # Show success message
            self._status_label.setText(f"Exported {len(query_list)} queries to {file_path}")
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export queries: {str(e)}"
            )

    def handle_config_change(self, key: str, value: Any) -> None:
        """
        Handle configuration changes.

        Args:
            key: The configuration key that changed
            value: The new value
        """
        # Update settings if needed
        if key == "plugins.as400_connector_plugin.settings":
            self._settings = load_plugin_settings(self._config)