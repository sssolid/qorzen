from __future__ import annotations
import uuid
'\nMain tab UI component for the AS400 Connector Plugin.\n\nThis module provides the main UI tab for the AS400 Connector Plugin,\ncontaining the query editor, connection management, and results display.\n'
import os
import datetime
import json
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, QSize, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont, QTextCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit, QTextEdit, QToolBar, QStatusBar, QFileDialog, QMessageBox, QDialog, QGroupBox, QFormLayout, QCheckBox, QSpinBox, QDialogButtonBox, QMenu, QToolButton, QProgressBar, QListWidget, QListWidgetItem, QInputDialog, QRadioButton, QButtonGroup, QScrollArea
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, SavedQuery, QueryHistoryEntry, PluginSettings, QueryResult
from qorzen.plugins.as400_connector_plugin.code.connector import AS400Connector
from qorzen.plugins.as400_connector_plugin.code.utils import load_connections, save_connections, load_saved_queries, save_queries, load_query_history, save_query_history, load_plugin_settings, save_plugin_settings, format_value_for_display, detect_query_parameters
from qorzen.plugins.as400_connector_plugin.code.ui.results_view import ResultsView
from qorzen.plugins.as400_connector_plugin.code.ui.visualization import VisualizationView
class AS400Tab(QWidget):
    queryStarted = Signal(str)
    queryFinished = Signal(str, bool)
    connectionChanged = Signal(str, bool)
    def __init__(self, event_bus: Any, logger: Any, config: Any, file_manager: Any=None, thread_manager: Any=None, security_manager: Any=None, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._event_bus = event_bus
        self._logger = logger
        self._config = config
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._security_manager = security_manager
        self._connections: Dict[str, AS400ConnectionConfig] = {}
        self._saved_queries: Dict[str, SavedQuery] = {}
        self._query_history: List[QueryHistoryEntry] = []
        self._settings = PluginSettings()
        self._current_connection_id: Optional[str] = None
        self._active_connector: Optional[AS400Connector] = None
        self._current_query_result: Optional[QueryResult] = None
        self._init_ui()
        self._load_data()
        self._update_connection_combo()
        self._update_saved_queries_list()
        self._update_history_list()
    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QToolBar('AS400 Tools')
        toolbar.setIconSize(QSize(16, 16))
        connection_label = QLabel('Connection:')
        self._connection_combo = QComboBox()
        self._connection_combo.setMinimumWidth(200)
        self._connection_combo.currentIndexChanged.connect(self._on_connection_selected)
        self._connect_button = QPushButton('Connect')
        self._connect_button.clicked.connect(self._on_connect_button_clicked)
        self._manage_connections_button = QToolButton()
        self._manage_connections_button.setText('...')
        self._manage_connections_button.setPopupMode(QToolButton.InstantPopup)
        connections_menu = QMenu(self)
        new_conn_action = connections_menu.addAction('New Connection...')
        new_conn_action.triggered.connect(self._on_new_connection)
        edit_conn_action = connections_menu.addAction('Edit Current Connection...')
        edit_conn_action.triggered.connect(self._on_edit_connection)
        delete_conn_action = connections_menu.addAction('Delete Current Connection')
        delete_conn_action.triggered.connect(self._on_delete_connection)
        self._manage_connections_button.setMenu(connections_menu)
        self._execute_button = QPushButton('Execute')
        self._execute_button.setShortcut(QKeySequence('F5'))
        self._execute_button.clicked.connect(self._execute_current_query)
        toolbar.addWidget(connection_label)
        toolbar.addWidget(self._connection_combo)
        toolbar.addWidget(self._connect_button)
        toolbar.addWidget(self._manage_connections_button)
        toolbar.addSeparator()
        toolbar.addWidget(self._execute_button)
        toolbar.addSeparator()
        limit_label = QLabel('Limit:')
        toolbar.addWidget(limit_label)
        self._limit_spin = QSpinBox()
        self._limit_spin.setMinimum(1)
        self._limit_spin.setMaximum(100000)
        self._limit_spin.setValue(1000)
        self._limit_spin.setFixedWidth(80)
        toolbar.addWidget(self._limit_spin)
        main_layout.addWidget(toolbar)
        self._main_splitter = QSplitter(Qt.Vertical)
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)
        upper_layout.setContentsMargins(5, 5, 5, 5)
        left_tabs = QTabWidget()
        saved_queries_widget = QWidget()
        saved_queries_layout = QVBoxLayout(saved_queries_widget)
        self._saved_queries_list = QListWidget()
        self._saved_queries_list.itemDoubleClicked.connect(self._on_saved_query_double_clicked)
        saved_queries_toolbar = QToolBar()
        saved_queries_toolbar.setIconSize(QSize(16, 16))
        new_query_action = saved_queries_toolbar.addAction('New')
        new_query_action.triggered.connect(self._on_new_query)
        save_query_action = saved_queries_toolbar.addAction('Save')
        save_query_action.triggered.connect(self._on_save_query)
        delete_query_action = saved_queries_toolbar.addAction('Delete')
        delete_query_action.triggered.connect(self._on_delete_query)
        saved_queries_layout.addWidget(saved_queries_toolbar)
        saved_queries_layout.addWidget(self._saved_queries_list)
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        self._history_list = QListWidget()
        self._history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        history_toolbar = QToolBar()
        history_toolbar.setIconSize(QSize(16, 16))
        clear_history_action = history_toolbar.addAction('Clear')
        clear_history_action.triggered.connect(self._on_clear_history)
        save_history_action = history_toolbar.addAction('Save as Query')
        save_history_action.triggered.connect(self._on_save_history_as_query)
        history_layout.addWidget(history_toolbar)
        history_layout.addWidget(self._history_list)
        left_tabs.addTab(saved_queries_widget, 'Saved Queries')
        left_tabs.addTab(history_widget, 'History')
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_label = QLabel('SQL Query:')
        self._query_editor = QTextEdit()
        self._query_editor.setFont(QFont('Courier New', 10))
        self._query_editor.setAcceptRichText(False)
        self._query_editor.setLineWrapMode(QTextEdit.NoWrap)
        editor_toolbar = QToolBar()
        editor_toolbar.setIconSize(QSize(16, 16))
        clear_editor_action = editor_toolbar.addAction('Clear')
        clear_editor_action.triggered.connect(self._query_editor.clear)
        format_query_action = editor_toolbar.addAction('Format SQL')
        format_query_action.triggered.connect(self._format_sql)
        editor_layout.addWidget(editor_label)
        editor_layout.addWidget(editor_toolbar)
        editor_layout.addWidget(self._query_editor)
        params_label = QLabel('Query Parameters:')
        self._params_widget = QWidget()
        self._params_layout = QFormLayout(self._params_widget)
        editor_layout.addWidget(params_label)
        editor_layout.addWidget(self._params_widget)
        upper_splitter = QSplitter(Qt.Horizontal)
        upper_splitter.addWidget(left_tabs)
        upper_splitter.addWidget(editor_widget)
        upper_splitter.setStretchFactor(0, 1)
        upper_splitter.setStretchFactor(1, 3)
        upper_layout.addWidget(upper_splitter)
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(5, 5, 5, 5)
        results_label = QLabel('Results:')
        results_layout.addWidget(results_label)
        results_tabs = QTabWidget()
        self._results_view = ResultsView()
        results_tabs.addTab(self._results_view, 'Data')
        self._viz_view = VisualizationView()
        results_tabs.addTab(self._viz_view, 'Visualization')
        results_layout.addWidget(results_tabs)
        self._main_splitter.addWidget(upper_widget)
        self._main_splitter.addWidget(results_widget)
        self._main_splitter.setStretchFactor(0, 1)
        self._main_splitter.setStretchFactor(1, 2)
        main_layout.addWidget(self._main_splitter)
        self._status_bar = QStatusBar()
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setFixedWidth(100)
        self._progress_bar.setVisible(False)
        self._status_label = QLabel('Ready')
        self._status_bar.addWidget(self._status_label, 1)
        self._status_bar.addPermanentWidget(self._progress_bar)
        main_layout.addWidget(self._status_bar)
        self._query_editor.textChanged.connect(self._on_query_text_changed)
        self.queryStarted.connect(self._on_query_started)
        self.queryFinished.connect(self._on_query_finished)
        self.connectionChanged.connect(self._on_connection_status_changed)
    def _load_data(self) -> None:
        if self._file_manager:
            self._connections = load_connections(self._file_manager)
            self._saved_queries = load_saved_queries(self._file_manager)
            self._query_history = load_query_history(self._file_manager)
        self._settings = load_plugin_settings(self._config)
        if self._settings.default_connection_id in self._connections:
            self._current_connection_id = self._settings.default_connection_id
    def _update_connection_combo(self) -> None:
        self._connection_combo.clear()
        self._connection_combo.addItem('Select a connection...', None)
        for conn_id, conn in self._connections.items():
            self._connection_combo.addItem(conn.name, conn_id)
        if self._current_connection_id:
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == self._current_connection_id:
                    self._connection_combo.setCurrentIndex(i)
                    break
    def _update_saved_queries_list(self) -> None:
        self._saved_queries_list.clear()
        sorted_queries = sorted(self._saved_queries.values(), key=lambda q: q.name.lower())
        for query in [q for q in sorted_queries if q.is_favorite]:
            item = QListWidgetItem(f'⭐ {query.name}')
            item.setData(Qt.UserRole, query.id)
            self._saved_queries_list.addItem(item)
        for query in [q for q in sorted_queries if not q.is_favorite]:
            item = QListWidgetItem(query.name)
            item.setData(Qt.UserRole, query.id)
            self._saved_queries_list.addItem(item)
    def _update_history_list(self) -> None:
        self._history_list.clear()
        for entry in self._query_history:
            display_text = entry.query_text.strip()
            if len(display_text) > 50:
                display_text = display_text[:47] + '...'
            timestamp = entry.executed_at.strftime('%Y-%m-%d %H:%M:%S')
            item = QListWidgetItem(f'{timestamp} - {display_text}')
            item.setData(Qt.UserRole, entry.id)
            if entry.status != 'success':
                item.setForeground(Qt.red)
            self._history_list.addItem(item)
    def _on_connection_selected(self, index: int) -> None:
        conn_id = self._connection_combo.itemData(index)
        if conn_id is None:
            self._current_connection_id = None
            self._connect_button.setText('Connect')
            self._connect_button.setEnabled(False)
            return
        self._current_connection_id = conn_id
        if self._active_connector and self._active_connector.is_connected():
            self._connect_button.setText('Disconnect')
        else:
            self._connect_button.setText('Connect')
        self._connect_button.setEnabled(True)
        if self._settings.recent_connections and self._settings.recent_connections[0] != conn_id:
            if conn_id in self._settings.recent_connections:
                self._settings.recent_connections.remove(conn_id)
            self._settings.recent_connections.insert(0, conn_id)
            self._settings.recent_connections = self._settings.recent_connections[:10]
            save_plugin_settings(self._settings, self._config)
    def _on_connect_button_clicked(self) -> None:
        if self._active_connector and self._active_connector.is_connected():
            self._disconnect_from_as400()
        else:
            self._connect_to_as400()
    def _connect_to_as400(self) -> None:
        if not self._current_connection_id or self._current_connection_id not in self._connections:
            self._status_label.setText('No connection selected')
            return
        conn_config = self._connections[self._current_connection_id]
        self._status_label.setText(f'Connecting to {conn_config.server}...')
        self._progress_bar.setVisible(True)
        self._connect_button.setEnabled(False)
        self._active_connector = AS400Connector(config=conn_config, logger=self._logger, security_manager=self._security_manager)
        if self._thread_manager:
            self._thread_manager.submit_task(func=self._connect_async, name=f'as400_connect_{conn_config.id}', submitter='as400_plugin')
        else:
            import threading
            thread = threading.Thread(target=self._connect_async, daemon=True)
            thread.start()
    def _connect_async(self) -> None:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._active_connector.connect())
            self.connectionChanged.emit(self._current_connection_id, True)
        except Exception as e:
            self._logger.error(f'AS400 connection error: {str(e)}', extra={'traceback': traceback.format_exc()})
            self.connectionChanged.emit(self._current_connection_id, False)
            QMessageBox.critical(self, 'Connection Error', f'Failed to connect to AS400: {str(e)}')
        finally:
            loop.close()
    def _disconnect_from_as400(self) -> None:
        if not self._active_connector:
            return
        self._status_label.setText('Disconnecting...')
        self._progress_bar.setVisible(True)
        self._connect_button.setEnabled(False)
        if self._thread_manager:
            self._thread_manager.submit_task(func=self._disconnect_async, name='as400_disconnect', submitter='as400_plugin')
        else:
            import threading
            thread = threading.Thread(target=self._disconnect_async, daemon=True)
            thread.start()
    def _disconnect_async(self) -> None:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._active_connector.close())
            self.connectionChanged.emit(self._current_connection_id, False)
        except Exception as e:
            self._logger.error(f'AS400 disconnection error: {str(e)}', extra={'traceback': traceback.format_exc()})
            self.connectionChanged.emit(self._current_connection_id, False)
        finally:
            loop.close()
    def _on_connection_status_changed(self, connection_id: str, connected: bool) -> None:
        if connected:
            self._status_label.setText(f'Connected to {self._connections[connection_id].server}')
            self._connect_button.setText('Disconnect')
            conn_name = self._connections[connection_id].name
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == connection_id:
                    self._connection_combo.setItemText(i, f'{conn_name} (Connected)')
                    break
        else:
            self._status_label.setText('Disconnected')
            self._connect_button.setText('Connect')
            self._active_connector = None
            if connection_id in self._connections:
                conn_name = self._connections[connection_id].name
                for i in range(self._connection_combo.count()):
                    if self._connection_combo.itemData(i) == connection_id:
                        self._connection_combo.setItemText(i, conn_name)
                        break
        self._progress_bar.setVisible(False)
        self._connect_button.setEnabled(True)
        self._execute_button.setEnabled(connected)
    def _on_new_connection(self) -> None:
        from qorzen.plugins.as400_connector_plugin.code.ui.connection_dialog import ConnectionDialog
        dialog = ConnectionDialog(parent=self, file_manager=self._file_manager)
        if dialog.exec() == QDialog.Accepted:
            new_connection = dialog.get_connection_config()
            self._connections[new_connection.id] = new_connection
            if self._file_manager:
                save_connections(self._connections, self._file_manager)
            self._update_connection_combo()
            self._current_connection_id = new_connection.id
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == new_connection.id:
                    self._connection_combo.setCurrentIndex(i)
                    break
            self._status_label.setText(f'Created new connection: {new_connection.name}')
    def _on_edit_connection(self) -> None:
        if not self._current_connection_id or self._current_connection_id not in self._connections:
            QMessageBox.warning(self, 'No Connection Selected', 'Please select a connection to edit.')
            return
        if self._active_connector and self._active_connector.is_connected():
            QMessageBox.warning(self, 'Connection Active', 'Please disconnect before editing the connection.')
            return
        from qorzen.plugins.as400_connector_plugin.ui.connection_dialog import ConnectionDialog
        dialog = ConnectionDialog(parent=self, file_manager=self._file_manager, connection=self._connections[self._current_connection_id])
        if dialog.exec() == QDialog.Accepted:
            updated_connection = dialog.get_connection_config()
            self._connections[updated_connection.id] = updated_connection
            if self._file_manager:
                save_connections(self._connections, self._file_manager)
            self._update_connection_combo()
            self._status_label.setText(f'Updated connection: {updated_connection.name}')
    def _on_delete_connection(self) -> None:
        if not self._current_connection_id or self._current_connection_id not in self._connections:
            QMessageBox.warning(self, 'No Connection Selected', 'Please select a connection to delete.')
            return
        if self._active_connector and self._active_connector.is_connected():
            QMessageBox.warning(self, 'Connection Active', 'Please disconnect before deleting the connection.')
            return
        conn_name = self._connections[self._current_connection_id].name
        reply = QMessageBox.question(self, 'Confirm Deletion', f"Are you sure you want to delete the connection '{conn_name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self._connections[self._current_connection_id]
            if self._file_manager:
                save_connections(self._connections, self._file_manager)
            self._update_connection_combo()
            self._status_label.setText(f'Deleted connection: {conn_name}')
            self._current_connection_id = None
    def _on_query_text_changed(self) -> None:
        query_text = self._query_editor.toPlainText()
        params = detect_query_parameters(query_text)
        self._update_parameter_controls(params)
    def _update_parameter_controls(self, param_names: List[str]) -> None:
        while self._params_layout.count() > 0:
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not param_names:
            self._params_widget.setVisible(False)
            return
        self._params_widget.setVisible(True)
        for param_name in param_names:
            label = QLabel(f'{param_name}:')
            input_field = QLineEdit()
            input_field.setObjectName(f'param_{param_name}')
            self._params_layout.addRow(label, input_field)
    def _get_query_parameters(self) -> Dict[str, Any]:
        params = {}
        for i in range(self._params_layout.rowCount()):
            label_item = self._params_layout.itemAt(i * 2)
            field_item = self._params_layout.itemAt(i * 2 + 1)
            if not label_item or not field_item:
                continue
            label = label_item.widget()
            field = field_item.widget()
            if not isinstance(label, QLabel) or not isinstance(field, QLineEdit):
                continue
            param_name = label.text().rstrip(':')
            param_value = field.text()
            if param_value.lower() == 'null':
                params[param_name] = None
            elif param_value.isdigit():
                params[param_name] = int(param_value)
            elif param_value.replace('.', '', 1).isdigit():
                params[param_name] = float(param_value)
            elif param_value.lower() in ('true', 'false'):
                params[param_name] = param_value.lower() == 'true'
            else:
                params[param_name] = param_value
        return params
    def _execute_current_query(self) -> None:
        if not self._active_connector or not self._active_connector.is_connected():
            QMessageBox.warning(self, 'Not Connected', 'Please connect to an AS400 database first.')
            return
        query_text = self._query_editor.toPlainText().strip()
        if not query_text:
            QMessageBox.warning(self, 'Empty Query', 'Please enter an SQL query to execute.')
            return
        params = self._get_query_parameters()
        limit = self._limit_spin.value()
        self.queryStarted.emit(query_text)
        if self._thread_manager:
            self._thread_manager.submit_task(func=self._execute_query_async, query=query_text, limit=limit, params=params, name='as400_execute_query', submitter='as400_plugin')
        else:
            import threading
            thread = threading.Thread(target=self._execute_query_async, args=(query_text, limit, params), daemon=True)
            thread.start()
    def _execute_query_async(self, query: str, limit: int, params: Dict[str, Any]) -> None:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._active_connector.execute_query(query=query, limit=limit, **params))
            self._current_query_result = result
            self.queryFinished.emit(query, True)
            self._add_to_query_history(query=query, params=params, result=result)
        except Exception as e:
            self._logger.error(f'AS400 query error: {str(e)}', extra={'query': query, 'traceback': traceback.format_exc()})
            self.queryFinished.emit(query, False)
            error_result = QueryResult(query=query, connection_id=self._current_connection_id, has_error=True, error_message=str(e))
            self._add_to_query_history(query=query, params=params, result=error_result)
            QMessageBox.critical(self, 'Query Execution Error', f'Failed to execute query: {str(e)}')
        finally:
            loop.close()
    def _on_query_started(self, query: str) -> None:
        self._status_label.setText('Executing query...')
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
        history_entry = QueryHistoryEntry(query_text=query, connection_id=self._current_connection_id, executed_at=datetime.datetime.now(), execution_time_ms=result.execution_time_ms, row_count=result.row_count, parameters=params, status='error' if result.has_error else 'success', error_message=result.error_message)
        self._query_history.insert(0, history_entry)
        self._query_history = self._query_history[:self._settings.query_history_limit]
        if self._file_manager:
            save_query_history(self._query_history, self._file_manager)
        self._update_history_list()
    def _display_query_results(self, result: QueryResult) -> None:
        if not result.records or not result.columns:
            return
        self._results_view.set_query_result(result)
        self._viz_view.set_query_result(result)
    def _on_saved_query_double_clicked(self, item: QListWidgetItem) -> None:
        query_id = item.data(Qt.UserRole)
        if not query_id or query_id not in self._saved_queries:
            return
        query = self._saved_queries[query_id]
        self._query_editor.setText(query.query_text)
        if query.parameters:
            QTimer.singleShot(100, lambda: self._set_parameter_values(query.parameters))
    def _set_parameter_values(self, params: Dict[str, Any]) -> None:
        for i in range(self._params_layout.rowCount()):
            label_item = self._params_layout.itemAt(i * 2)
            field_item = self._params_layout.itemAt(i * 2 + 1)
            if not label_item or not field_item:
                continue
            label = label_item.widget()
            field = field_item.widget()
            if not isinstance(label, QLabel) or not isinstance(field, QLineEdit):
                continue
            param_name = label.text().rstrip(':')
            if param_name in params:
                value = params[param_name]
                if value is None:
                    field.setText('NULL')
                else:
                    field.setText(str(value))
    def _on_history_item_double_clicked(self, item: QListWidgetItem) -> None:
        entry_id = item.data(Qt.UserRole)
        entry = None
        for hist_entry in self._query_history:
            if hist_entry.id == entry_id:
                entry = hist_entry
                break
        if not entry:
            return
        self._query_editor.setText(entry.query_text)
        if entry.parameters:
            QTimer.singleShot(100, lambda: self._set_parameter_values(entry.parameters))
    def _on_new_query(self) -> None:
        self._query_editor.clear()
        name, ok = QInputDialog.getText(self, 'New Query', 'Enter a name for the new query:')
        if ok and name:
            query = SavedQuery(name=name, query_text='')
            self._saved_queries[query.id] = query
            if self._file_manager:
                save_queries(self._saved_queries, self._file_manager)
            self._update_saved_queries_list()
            self._status_label.setText(f'Created new query: {name}')
    def _on_save_query(self) -> None:
        query_text = self._query_editor.toPlainText().strip()
        if not query_text:
            QMessageBox.warning(self, 'Empty Query', 'Cannot save an empty query.')
            return
        name, ok = QInputDialog.getText(self, 'Save Query', 'Enter a name for the query:', text=self._get_current_query_name())
        if ok and name:
            params = self._get_query_parameters()
            query_id = self._get_current_query_id()
            if query_id and query_id in self._saved_queries:
                query = self._saved_queries[query_id]
                query.name = name
                query.query_text = query_text
                query.parameters = params
                query.updated_at = datetime.datetime.now()
                if self._current_connection_id:
                    query.connection_id = self._current_connection_id
            else:
                query = SavedQuery(name=name, query_text=query_text, parameters=params, connection_id=self._current_connection_id)
                self._saved_queries[query.id] = query
            if self._file_manager:
                save_queries(self._saved_queries, self._file_manager)
            self._update_saved_queries_list()
            self._status_label.setText(f'Saved query: {name}')
    def _get_current_query_name(self) -> str:
        selected_items = self._saved_queries_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            query_id = item.data(Qt.UserRole)
            if query_id in self._saved_queries:
                query_name = self._saved_queries[query_id].name
                if query_name.startswith('⭐ '):
                    return query_name[2:]
                return query_name
        return ''
    def _get_current_query_id(self) -> Optional[str]:
        selected_items = self._saved_queries_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            return item.data(Qt.UserRole)
        return None
    def _on_delete_query(self) -> None:
        selected_items = self._saved_queries_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'No Query Selected', 'Please select a query to delete.')
            return
        item = selected_items[0]
        query_id = item.data(Qt.UserRole)
        if query_id not in self._saved_queries:
            return
        query = self._saved_queries[query_id]
        reply = QMessageBox.question(self, 'Confirm Deletion', f"Are you sure you want to delete the query '{query.name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self._saved_queries[query_id]
            if self._file_manager:
                save_queries(self._saved_queries, self._file_manager)
            self._update_saved_queries_list()
            self._status_label.setText(f'Deleted query: {query.name}')
    def _on_clear_history(self) -> None:
        reply = QMessageBox.question(self, 'Confirm Clear History', 'Are you sure you want to clear the query history?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._query_history = []
            if self._file_manager:
                save_query_history(self._query_history, self._file_manager)
            self._update_history_list()
            self._status_label.setText('Query history cleared')
    def _on_save_history_as_query(self) -> None:
        selected_items = self._history_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'No History Item Selected', 'Please select a history item to save as a query.')
            return
        item = selected_items[0]
        entry_id = item.data(Qt.UserRole)
        entry = None
        for hist_entry in self._query_history:
            if hist_entry.id == entry_id:
                entry = hist_entry
                break
        if not entry:
            return
        name, ok = QInputDialog.getText(self, 'Save as Query', 'Enter a name for the query:')
        if ok and name:
            query = SavedQuery(name=name, query_text=entry.query_text, parameters=entry.parameters, connection_id=entry.connection_id)
            self._saved_queries[query.id] = query
            if self._file_manager:
                save_queries(self._saved_queries, self._file_manager)
            self._update_saved_queries_list()
            self._status_label.setText(f'Saved history item as query: {name}')
    def _export_results(self) -> None:
        if not self._current_query_result or not self._current_query_result.records:
            QMessageBox.warning(self, 'No Results', 'There are no results to export.')
            return
        file_path, _ = QFileDialog.getSaveFileName(self, 'Export Results', '', 'CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx)')
        if not file_path:
            return
        try:
            if file_path.endswith('.csv'):
                self._export_as_csv(file_path)
            elif file_path.endswith('.json'):
                self._export_as_json(file_path)
            elif file_path.endswith('.xlsx'):
                self._export_as_excel(file_path)
            else:
                if not file_path.endswith('.csv'):
                    file_path += '.csv'
                self._export_as_csv(file_path)
            self._status_label.setText(f'Results exported to {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Export Error', f'Failed to export results: {str(e)}')
    def _export_as_csv(self, file_path: str) -> None:
        import csv
        with open(file_path, 'w', newline='') as f:
            headers = [col.name for col in self._current_query_result.columns]
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for record in self._current_query_result.records:
                row = {k: '' if v is None else v for k, v in record.items()}
                writer.writerow(row)
    def _export_as_json(self, file_path: str) -> None:
        export_data = {'query': self._current_query_result.query, 'executed_at': self._current_query_result.executed_at.isoformat(), 'execution_time_ms': self._current_query_result.execution_time_ms, 'row_count': self._current_query_result.row_count, 'records': self._current_query_result.records}
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    def _export_as_excel(self, file_path: str) -> None:
        try:
            import openpyxl
            from openpyxl import Workbook
        except ImportError:
            QMessageBox.critical(self, 'Missing Dependency', "Excel export requires the openpyxl package. Please install it with 'pip install openpyxl'.")
            return
        wb = Workbook()
        ws = wb.active
        ws.title = 'Query Results'
        headers = [col.name for col in self._current_query_result.columns]
        ws.append(headers)
        for record in self._current_query_result.records:
            row = [record.get(col) for col in headers]
            ws.append(row)
        wb.save(file_path)
    def _copy_selected_results(self) -> None:
        selected_ranges = self._results_table.selectedRanges()
        if not selected_ranges:
            return
        clipboard_text = ''
        for range_idx, cell_range in enumerate(selected_ranges):
            for row in range(cell_range.topRow(), cell_range.bottomRow() + 1):
                row_text = []
                for col in range(cell_range.leftColumn(), cell_range.rightColumn() + 1):
                    item = self._results_table.item(row, col)
                    if item:
                        cell_text = item.text()
                        if '\t' in cell_text or '\n' in cell_text:
                            cell_text = f'"{cell_text}"'
                        row_text.append(cell_text)
                    else:
                        row_text.append('')
                clipboard_text += '\t'.join(row_text)
                clipboard_text += '\n'
            if range_idx < len(selected_ranges) - 1:
                clipboard_text += '\n'
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(clipboard_text)
        self._status_label.setText(f'Copied {len(selected_ranges)} selection(s) to clipboard')
    def _format_sql(self) -> None:
        try:
            import sqlparse
        except ImportError:
            QMessageBox.warning(self, 'Missing Dependency', "SQL formatting requires the sqlparse package. Please install it with 'pip install sqlparse'.")
            return
        query_text = self._query_editor.toPlainText()
        if not query_text.strip():
            return
        formatted_query = sqlparse.format(query_text, reindent=True, keyword_case='upper', identifier_case='lower', indent_width=4)
        self._query_editor.setText(formatted_query)
        self._status_label.setText('SQL query formatted')
    def open_connection_dialog(self) -> None:
        self._on_new_connection()
    def open_connection_manager(self) -> None:
        from qorzen.plugins.as400_connector_plugin.code.ui.connection_dialog import ConnectionManagerDialog
        dialog = ConnectionManagerDialog(self._connections, parent=self, file_manager=self._file_manager)
        if dialog.exec() == QDialog.Accepted:
            self._connections = dialog.get_connections()
            if self._file_manager:
                save_connections(self._connections, self._file_manager)
            self._update_connection_combo()
            self._status_label.setText('Connection list updated')
    def import_queries(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, 'Import Queries', '', 'JSON Files (*.json)')
        if not file_path:
            return
        try:
            with open(file_path, 'r') as f:
                imported_data = json.load(f)
            if not isinstance(imported_data, list):
                raise ValueError('Invalid query collection format')
            imported_count = 0
            for query_data in imported_data:
                try:
                    if 'created_at' in query_data and isinstance(query_data['created_at'], str):
                        query_data['created_at'] = datetime.datetime.fromisoformat(query_data['created_at'])
                    if 'updated_at' in query_data and isinstance(query_data['updated_at'], str):
                        query_data['updated_at'] = datetime.datetime.fromisoformat(query_data['updated_at'])
                    if 'id' in query_data:
                        query_data['id'] = str(uuid.uuid4())
                    query = SavedQuery(**query_data)
                    self._saved_queries[query.id] = query
                    imported_count += 1
                except Exception:
                    continue
            if self._file_manager and imported_count > 0:
                save_queries(self._saved_queries, self._file_manager)
            self._update_saved_queries_list()
            self._status_label.setText(f'Imported {imported_count} queries')
        except Exception as e:
            QMessageBox.critical(self, 'Import Error', f'Failed to import queries: {str(e)}')
    def export_queries(self) -> None:
        if not self._saved_queries:
            QMessageBox.warning(self, 'No Queries', 'There are no saved queries to export.')
            return
        file_path, _ = QFileDialog.getSaveFileName(self, 'Export Queries', '', 'JSON Files (*.json)')
        if not file_path:
            return
        try:
            if not file_path.endswith('.json'):
                file_path += '.json'
            query_list = []
            for query in self._saved_queries.values():
                query_dict = query.dict()
                if 'created_at' in query_dict and isinstance(query_dict['created_at'], datetime.datetime):
                    query_dict['created_at'] = query_dict['created_at'].isoformat()
                if 'updated_at' in query_dict and isinstance(query_dict['updated_at'], datetime.datetime):
                    query_dict['updated_at'] = query_dict['updated_at'].isoformat()
                query_list.append(query_dict)
            with open(file_path, 'w') as f:
                json.dump(query_list, f, indent=2)
            self._status_label.setText(f'Exported {len(query_list)} queries to {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Export Error', f'Failed to export queries: {str(e)}')
    def handle_config_change(self, key: str, value: Any) -> None:
        if key == 'plugins.as400_connector_plugin.settings':
            self._settings = load_plugin_settings(self._config)