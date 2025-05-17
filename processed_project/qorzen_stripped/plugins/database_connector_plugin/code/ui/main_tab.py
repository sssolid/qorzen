from __future__ import annotations
'\nMain UI tab for the Database Connector Plugin.\n\nThis module provides the main UI tab that users interact with, containing\nall the functionality for connecting to databases, executing queries,\nmanaging field mappings, and validating data.\n'
import asyncio
import datetime
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTabWidget, QSplitter, QToolBar, QStatusBar, QMessageBox, QProgressBar, QMenu, QToolButton, QInputDialog, QFileDialog
from qorzen.utils.exceptions import DatabaseError, PluginError
from ..models import BaseConnectionConfig, AS400ConnectionConfig, ODBCConnectionConfig, ConnectionType, SavedQuery, FieldMapping, ValidationRule, QueryResult
from .connection_dialog import ConnectionDialog, ConnectionManagerDialog
from .query_editor import QueryEditorWidget
from .field_mapping import FieldMappingWidget
from .validation import ValidationWidget
from .history import HistoryWidget
from .results_view import ResultsView
class DatabaseConnectorTab(QWidget):
    connectionChanged = Signal(str, bool)
    queryStarted = Signal(str)
    queryFinished = Signal(str, bool)
    def __init__(self, plugin: Any, logger: Any, concurrency_manager: Any, event_bus_manager: Any, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._concurrency_manager = concurrency_manager
        self._event_bus_manager = event_bus_manager
        self._current_connection_id: Optional[str] = None
        self._query_running = False
        self._current_query_result: Optional[QueryResult] = None
        self._init_ui()
        self._connect_signals()
        self._load_recent_connections()
    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QToolBar('Database Tools')
        toolbar.setIconSize(QSize(16, 16))
        connection_label = QLabel('Connection:')
        toolbar.addWidget(connection_label)
        self._connection_combo = QComboBox()
        self._connection_combo.setMinimumWidth(200)
        self._connection_combo.currentIndexChanged.connect(self._on_connection_selected)
        toolbar.addWidget(self._connection_combo)
        self._connect_button = QPushButton('Connect')
        self._connect_button.clicked.connect(self._on_connect_button_clicked)
        toolbar.addWidget(self._connect_button)
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
        connections_menu.addSeparator()
        manage_all_action = connections_menu.addAction('Manage All Connections...')
        manage_all_action.triggered.connect(self.open_connection_manager)
        self._manage_connections_button.setMenu(connections_menu)
        toolbar.addWidget(self._manage_connections_button)
        toolbar.addSeparator()
        self._execute_action = QAction('Execute Query', self)
        self._execute_action.setShortcut(QKeySequence('F5'))
        self._execute_action.triggered.connect(self._execute_current_query)
        toolbar.addAction(self._execute_action)
        self._cancel_action = QAction('Cancel Query', self)
        self._cancel_action.setShortcut(QKeySequence('Esc'))
        self._cancel_action.triggered.connect(self._cancel_current_query)
        self._cancel_action.setEnabled(False)
        toolbar.addAction(self._cancel_action)
        toolbar.addSeparator()
        self._export_action = QAction('Export Results', self)
        self._export_action.triggered.connect(self._export_results)
        self._export_action.setEnabled(False)
        toolbar.addAction(self._export_action)
        main_layout.addWidget(toolbar)
        self._tab_widget = QTabWidget()
        self._query_editor = QueryEditorWidget(self._plugin, self._logger)
        self._tab_widget.addTab(self._query_editor, 'Query Editor')
        self._results_view = ResultsView(self._plugin, self._logger)
        self._tab_widget.addTab(self._results_view, 'Results')
        self._field_mapping = FieldMappingWidget(self._plugin, self._logger)
        self._tab_widget.addTab(self._field_mapping, 'Field Mappings')
        self._validation = ValidationWidget(self._plugin, self._logger)
        self._tab_widget.addTab(self._validation, 'Data Validation')
        self._history = HistoryWidget(self._plugin, self._logger)
        self._tab_widget.addTab(self._history, 'History')
        main_layout.addWidget(self._tab_widget)
        self._status_bar = QStatusBar()
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setFixedWidth(100)
        self._progress_bar.setVisible(False)
        self._status_label = QLabel('Ready')
        self._status_bar.addWidget(self._status_label, 1)
        self._status_bar.addPermanentWidget(self._progress_bar)
        main_layout.addWidget(self._status_bar)
    def _connect_signals(self) -> None:
        self.connectionChanged.connect(self._on_connection_status_changed)
        self.queryStarted.connect(self._on_query_started)
        self.queryFinished.connect(self._on_query_finished)
        self._query_editor.executeQueryRequested.connect(self._execute_current_query)
        self._query_editor.saveQueryRequested.connect(self._on_save_query)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
    def _load_recent_connections(self) -> None:
        self._connection_combo.clear()
        self._connection_combo.addItem('Select a connection...', None)
        asyncio.create_task(self._async_load_connections())
    async def _async_load_connections(self) -> None:
        try:
            connections = await self._plugin.get_connections()
            settings = self._plugin._settings
            connection_ids = []
            if settings and settings.recent_connections:
                for conn_id in settings.recent_connections:
                    if conn_id in connections:
                        connection_ids.append(conn_id)
            for conn_id in connections:
                if conn_id not in connection_ids:
                    connection_ids.append(conn_id)
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._populate_connection_combo(connection_ids, connections))
            else:
                self._populate_connection_combo(connection_ids, connections)
            if settings and settings.default_connection_id:
                default_id = settings.default_connection_id
                if default_id in connections:
                    if not self._concurrency_manager.is_main_thread():
                        await self._concurrency_manager.run_on_main_thread(lambda: self._set_default_connection(default_id))
                    else:
                        self._set_default_connection(default_id)
        except Exception as e:
            self._logger.error(f'Error loading connections: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._show_connection_error(str(e)))
            else:
                self._show_connection_error(str(e))
    def _populate_connection_combo(self, connection_ids: List[str], connections: Dict[str, BaseConnectionConfig]) -> None:
        current_id = self._connection_combo.currentData()
        self._connection_combo.clear()
        self._connection_combo.addItem('Select a connection...', None)
        for conn_id in connection_ids:
            conn = connections[conn_id]
            self._connection_combo.addItem(conn.name, conn_id)
        if current_id:
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == current_id:
                    self._connection_combo.setCurrentIndex(i)
                    break
    def _set_default_connection(self, connection_id: str) -> None:
        for i in range(self._connection_combo.count()):
            if self._connection_combo.itemData(i) == connection_id:
                self._connection_combo.setCurrentIndex(i)
                break
    def _show_connection_error(self, error_message: str) -> None:
        self._status_label.setText(f'Error: {error_message}')
        QMessageBox.critical(self, 'Connection Error', f'Failed to load connections: {error_message}')
    def _on_connection_selected(self, index: int) -> None:
        conn_id = self._connection_combo.itemData(index)
        if conn_id is None:
            self._current_connection_id = None
            self._connect_button.setText('Connect')
            self._connect_button.setEnabled(False)
            return
        self._current_connection_id = conn_id
        self._connect_button.setEnabled(True)
        asyncio.create_task(self._check_connection_status(conn_id))
    async def _check_connection_status(self, connection_id: str) -> None:
        try:
            connector = None
            if connection_id in self._plugin._active_connectors:
                connector = self._plugin._active_connectors[connection_id]
            if connector and connector.is_connected:
                if not self._concurrency_manager.is_main_thread():
                    await self._concurrency_manager.run_on_main_thread(lambda: self._update_ui_connected(connection_id, True))
                else:
                    self._update_ui_connected(connection_id, True)
            elif not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._update_ui_connected(connection_id, False))
            else:
                self._update_ui_connected(connection_id, False)
        except Exception as e:
            self._logger.error(f'Error checking connection status: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._update_ui_connected(connection_id, False))
            else:
                self._update_ui_connected(connection_id, False)
    def _update_ui_connected(self, connection_id: str, connected: bool) -> None:
        if connected:
            self._connect_button.setText('Disconnect')
            self.connectionChanged.emit(connection_id, True)
        else:
            self._connect_button.setText('Connect')
            self.connectionChanged.emit(connection_id, False)
    def _on_connect_button_clicked(self) -> None:
        if not self._current_connection_id:
            return
        if self._connect_button.text() == 'Disconnect':
            self._disconnect_from_database()
        else:
            self._connect_to_database()
    def _connect_to_database(self) -> None:
        if not self._current_connection_id:
            self._status_label.setText('No connection selected')
            return
        self._status_label.setText('Connecting...')
        self._progress_bar.setVisible(True)
        self._connect_button.setEnabled(False)
        asyncio.create_task(self._async_connect())
    async def _async_connect(self) -> None:
        if not self._current_connection_id:
            return
        try:
            await self._plugin.get_connector(self._current_connection_id)
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self.connectionChanged.emit(self._current_connection_id, True))
            else:
                self.connectionChanged.emit(self._current_connection_id, True)
            await self._refresh_current_view()
        except Exception as e:
            self._logger.error(f'Connection error: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._handle_connection_error(str(e)))
            else:
                self._handle_connection_error(str(e))
    def _handle_connection_error(self, error_message: str) -> None:
        self.connectionChanged.emit(self._current_connection_id, False)
        QMessageBox.critical(self, 'Connection Error', f'Failed to connect to database: {error_message}')
    def _disconnect_from_database(self) -> None:
        if not self._current_connection_id:
            return
        self._status_label.setText('Disconnecting...')
        self._progress_bar.setVisible(True)
        self._connect_button.setEnabled(False)
        asyncio.create_task(self._async_disconnect())
    async def _async_disconnect(self) -> None:
        if not self._current_connection_id:
            return
        try:
            await self._plugin.disconnect(self._current_connection_id)
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self.connectionChanged.emit(self._current_connection_id, False))
            else:
                self.connectionChanged.emit(self._current_connection_id, False)
        except Exception as e:
            self._logger.error(f'Disconnection error: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._handle_disconnection_error(str(e)))
            else:
                self._handle_disconnection_error(str(e))
    def _handle_disconnection_error(self, error_message: str) -> None:
        self.connectionChanged.emit(self._current_connection_id, False)
        QMessageBox.warning(self, 'Disconnection Warning', f'Warning during disconnection: {error_message}')
    def _on_connection_status_changed(self, connection_id: str, connected: bool) -> None:
        if connected:
            self._status_label.setText(f'Connected')
            self._connect_button.setText('Disconnect')
            conn_name = 'Unknown'
            conn = self._plugin._connections.get(connection_id)
            if conn:
                conn_name = conn.name
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == connection_id:
                    self._connection_combo.setItemText(i, f'{conn_name} (Connected)')
                    break
        else:
            self._status_label.setText('Disconnected')
            self._connect_button.setText('Connect')
            conn_name = 'Unknown'
            conn = self._plugin._connections.get(connection_id)
            if conn:
                conn_name = conn.name
            for i in range(self._connection_combo.count()):
                if self._connection_combo.itemData(i) == connection_id:
                    self._connection_combo.setItemText(i, conn_name)
                    break
        self._progress_bar.setVisible(False)
        self._connect_button.setEnabled(True)
        self._execute_action.setEnabled(connected)
        self._query_editor.set_connection_status(connection_id, connected)
        self._field_mapping.set_connection_status(connection_id, connected)
        self._validation.set_connection_status(connection_id, connected)
        self._history.set_connection_status(connection_id, connected)
    def _on_new_connection(self) -> None:
        dialog = ConnectionDialog(parent=self)
        if dialog.exec() == ConnectionDialog.Accepted:
            new_connection = dialog.get_connection_config()
            asyncio.create_task(self._async_save_connection(new_connection))
    async def _async_save_connection(self, connection: BaseConnectionConfig) -> None:
        try:
            await self._plugin.save_connection(connection)
            await self._async_load_connections()
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._select_connection(connection.id))
            else:
                self._select_connection(connection.id)
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._status_label.setText(f'Created new connection: {connection.name}'))
            else:
                self._status_label.setText(f'Created new connection: {connection.name}')
        except Exception as e:
            self._logger.error(f'Failed to save connection: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.critical(self, 'Connection Error', f'Failed to save connection: {str(e)}'))
            else:
                QMessageBox.critical(self, 'Connection Error', f'Failed to save connection: {str(e)}')
    def _select_connection(self, connection_id: str) -> None:
        for i in range(self._connection_combo.count()):
            if self._connection_combo.itemData(i) == connection_id:
                self._connection_combo.setCurrentIndex(i)
                break
    def _on_edit_connection(self) -> None:
        if not self._current_connection_id:
            QMessageBox.warning(self, 'No Connection Selected', 'Please select a connection to edit.')
            return
        is_connected = False
        if self._current_connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[self._current_connection_id]
            is_connected = connector.is_connected
        if is_connected:
            QMessageBox.warning(self, 'Connection Active', 'Please disconnect before editing the connection.')
            return
        conn_config = self._plugin._connections.get(self._current_connection_id)
        if not conn_config:
            QMessageBox.warning(self, 'Connection Not Found', 'The selected connection could not be found.')
            return
        dialog = ConnectionDialog(parent=self, connection=conn_config)
        if dialog.exec() == ConnectionDialog.Accepted:
            updated_connection = dialog.get_connection_config()
            asyncio.create_task(self._async_save_connection(updated_connection))
    def _on_delete_connection(self) -> None:
        if not self._current_connection_id:
            QMessageBox.warning(self, 'No Connection Selected', 'Please select a connection to delete.')
            return
        is_connected = False
        if self._current_connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[self._current_connection_id]
            is_connected = connector.is_connected
        if is_connected:
            QMessageBox.warning(self, 'Connection Active', 'Please disconnect before deleting the connection.')
            return
        conn_name = 'the selected connection'
        conn_config = self._plugin._connections.get(self._current_connection_id)
        if conn_config:
            conn_name = conn_config.name
        reply = QMessageBox.question(self, 'Confirm Deletion', f"Are you sure you want to delete the connection '{conn_name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        asyncio.create_task(self._async_delete_connection(self._current_connection_id))
    async def _async_delete_connection(self, connection_id: str) -> None:
        try:
            conn_name = 'Connection'
            conn_config = self._plugin._connections.get(connection_id)
            if conn_config:
                conn_name = conn_config.name
            await self._plugin.delete_connection(connection_id)
            await self._async_load_connections()
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._status_label.setText(f'Deleted connection: {conn_name}'))
            else:
                self._status_label.setText(f'Deleted connection: {conn_name}')
        except Exception as e:
            self._logger.error(f'Failed to delete connection: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.critical(self, 'Connection Error', f'Failed to delete connection: {str(e)}'))
            else:
                QMessageBox.critical(self, 'Connection Error', f'Failed to delete connection: {str(e)}')
    def open_connection_manager(self) -> None:
        dialog = ConnectionManagerDialog(self._plugin._connections, parent=self)
        if dialog.exec() == ConnectionManagerDialog.Accepted:
            updated_connections = dialog.get_connections()
            asyncio.create_task(self._async_save_all_connections(updated_connections))
    async def _async_save_all_connections(self, connections: Dict[str, BaseConnectionConfig]) -> None:
        try:
            for connection in connections.values():
                await self._plugin.save_connection(connection)
            await self._async_load_connections()
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._status_label.setText('Connections updated'))
            else:
                self._status_label.setText('Connections updated')
        except Exception as e:
            self._logger.error(f'Failed to save connections: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.critical(self, 'Connection Error', f'Failed to save connections: {str(e)}'))
            else:
                QMessageBox.critical(self, 'Connection Error', f'Failed to save connections: {str(e)}')
    def _execute_current_query(self) -> None:
        if self._query_running:
            self._logger.warning('Query already running, ignoring request')
            return
        if not self._current_connection_id:
            QMessageBox.warning(self, 'No Active Connection', 'Please connect to a database before executing a query.')
            return
        is_connected = False
        if self._current_connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[self._current_connection_id]
            is_connected = connector.is_connected
        if not is_connected:
            QMessageBox.warning(self, 'Not Connected', 'Please connect to the database before executing a query.')
            return
        query_text = self._query_editor.get_query_text()
        if not query_text.strip():
            QMessageBox.warning(self, 'Empty Query', 'Please enter a SQL query to execute.')
            return
        params = self._query_editor.get_parameters()
        limit = self._query_editor.get_limit()
        mapping_id = self._query_editor.get_mapping_id()
        self.queryStarted.emit(self._current_connection_id)
        asyncio.create_task(self._async_execute_query(self._current_connection_id, query_text, params, limit, mapping_id))
    async def _async_execute_query(self, connection_id: str, query: str, params: Optional[Dict[str, Any]]=None, limit: Optional[int]=None, mapping_id: Optional[str]=None) -> None:
        try:
            result = await self._plugin.execute_query(connection_id=connection_id, query=query, params=params, limit=limit, mapping_id=mapping_id)
            self._current_query_result = result
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._update_results(result))
            else:
                self._update_results(result)
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self.queryFinished.emit(connection_id, True))
            else:
                self.queryFinished.emit(connection_id, True)
        except Exception as e:
            self._logger.error(f'Query execution error: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._handle_query_error(connection_id, str(e)))
            else:
                self._handle_query_error(connection_id, str(e))
    def _update_results(self, result: QueryResult) -> None:
        self._results_view.set_query_result(result)
        self._tab_widget.setCurrentWidget(self._results_view)
        self._export_action.setEnabled(True)
    def _handle_query_error(self, connection_id: str, error_message: str) -> None:
        self.queryFinished.emit(connection_id, False)
        QMessageBox.critical(self, 'Query Error', f'Failed to execute query: {error_message}')
    def _cancel_current_query(self) -> None:
        if not self._query_running:
            return
        if not self._current_connection_id:
            return
        self._logger.debug('Cancelling query')
        connector = None
        if self._current_connection_id in self._plugin._active_connectors:
            connector = self._plugin._active_connectors[self._current_connection_id]
        if connector:
            asyncio.create_task(connector.cancel_query())
    def _on_query_started(self, connection_id: str) -> None:
        self._query_running = True
        self._status_label.setText('Executing query...')
        self._progress_bar.setVisible(True)
        self._execute_action.setEnabled(False)
        self._cancel_action.setEnabled(True)
    def _on_query_finished(self, connection_id: str, success: bool) -> None:
        self._query_running = False
        self._progress_bar.setVisible(False)
        self._execute_action.setEnabled(True)
        self._cancel_action.setEnabled(False)
        if success and self._current_query_result:
            execution_time = self._current_query_result.execution_time_ms
            row_count = self._current_query_result.row_count
            self._status_label.setText(f'Query executed successfully in {execution_time} ms, {row_count} rows returned')
        else:
            self._status_label.setText('Query execution failed')
    def _on_save_query(self) -> None:
        if not self._current_connection_id:
            QMessageBox.warning(self, 'No Connection Selected', 'Please select a connection before saving a query.')
            return
        query_text = self._query_editor.get_query_text()
        if not query_text.strip():
            QMessageBox.warning(self, 'Empty Query', 'Cannot save an empty query.')
            return
        name, ok = QInputDialog.getText(self, 'Save Query', 'Enter a name for the query:', text=self._query_editor.get_current_query_name())
        if not ok or not name:
            return
        params = self._query_editor.get_parameters()
        query_id = self._query_editor.get_current_query_id()
        mapping_id = self._query_editor.get_mapping_id()
        if query_id and query_id in self._plugin._saved_queries:
            query = self._plugin._saved_queries[query_id]
            query.name = name
            query.query_text = query_text
            query.parameters = params
            query.connection_id = self._current_connection_id
            query.updated_at = datetime.datetime.now()
            query.field_mapping_id = mapping_id
        else:
            query = SavedQuery(name=name, query_text=query_text, parameters=params, connection_id=self._current_connection_id, field_mapping_id=mapping_id)
        asyncio.create_task(self._async_save_query(query))
    async def _async_save_query(self, query: SavedQuery) -> None:
        try:
            await self._plugin.save_query(query)
            await self._query_editor.reload_queries()
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: self._status_label.setText(f'Saved query: {query.name}'))
            else:
                self._status_label.setText(f'Saved query: {query.name}')
        except Exception as e:
            self._logger.error(f'Failed to save query: {str(e)}')
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.critical(self, 'Query Error', f'Failed to save query: {str(e)}'))
            else:
                QMessageBox.critical(self, 'Query Error', f'Failed to save query: {str(e)}')
    def _export_results(self) -> None:
        if not self._current_query_result or not self._current_query_result.records:
            QMessageBox.warning(self, 'No Results', 'There are no results to export.')
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(self, 'Export Results', '', 'CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx)')
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
            self._logger.error(f'Export error: {str(e)}')
            QMessageBox.critical(self, 'Export Error', f'Failed to export results: {str(e)}')
    def _export_as_csv(self, file_path: str) -> None:
        import csv
        with open(file_path, 'w', newline='') as f:
            headers = [col.name for col in self._current_query_result.columns]
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            records = self._current_query_result.mapped_records if self._current_query_result.mapped_records else self._current_query_result.records
            for record in records:
                row = {k: '' if v is None else v for k, v in record.items()}
                writer.writerow(row)
    def _export_as_json(self, file_path: str) -> None:
        records = self._current_query_result.mapped_records if self._current_query_result.mapped_records else self._current_query_result.records
        export_data = {'query': self._current_query_result.query, 'executed_at': self._current_query_result.executed_at.isoformat(), 'execution_time_ms': self._current_query_result.execution_time_ms, 'row_count': self._current_query_result.row_count, 'records': records}
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
        records = self._current_query_result.mapped_records if self._current_query_result.mapped_records else self._current_query_result.records
        for record in records:
            ws.append([record.get(col) for col in headers])
        wb.save(file_path)
    def _on_tab_changed(self, index: int) -> None:
        current_widget = self._tab_widget.widget(index)
        self._execute_action.setEnabled(current_widget == self._query_editor and self._current_connection_id and (self._current_connection_id in self._plugin._active_connectors) and self._plugin._active_connectors[self._current_connection_id].is_connected)
        self._export_action.setEnabled(current_widget == self._results_view and self._current_query_result is not None and self._current_query_result.records)
    async def _refresh_current_view(self) -> None:
        current_widget = self._tab_widget.currentWidget()
        if current_widget == self._query_editor:
            await self._query_editor.refresh()
        elif current_widget == self._field_mapping:
            await self._field_mapping.refresh()
        elif current_widget == self._validation:
            await self._validation.refresh()
        elif current_widget == self._history:
            await self._history.refresh()
    def switch_to_query_editor(self) -> None:
        self._tab_widget.setCurrentWidget(self._query_editor)
    def switch_to_results(self) -> None:
        self._tab_widget.setCurrentWidget(self._results_view)
    def switch_to_mapping_editor(self) -> None:
        self._tab_widget.setCurrentWidget(self._field_mapping)
    def switch_to_validation(self) -> None:
        self._tab_widget.setCurrentWidget(self._validation)
    def switch_to_history(self) -> None:
        self._tab_widget.setCurrentWidget(self._history)
    def handle_config_change(self, key: str, value: Any) -> None:
        if key == f'plugins.{self._plugin.name}.settings':
            self._load_recent_connections()