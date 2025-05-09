from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from PySide6.QtCore import Qt, QThread, Slot, QTimer
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QMessageBox, QProgressDialog,
    QPushButton, QSplitter, QVBoxLayout, QWidget
)
from PySide6.QtGui import QAction, QIcon

from qorzen.core import (
    RemoteServicesManager, SecurityManager, APIManager, CloudManager,
    LoggingManager, ConfigManager, DatabaseManager, EventBusManager,
    FileManager, ThreadManager
)
from qorzen.core.thread_manager import ThreadExecutionContext, TaskResult
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration

from .database_handler import DatabaseHandler
from .data_table import DataTableWidget
from .events import VCdbEventType
from .export import DataExporter
from .filter_panel import FilterPanelManager


class VCdbExplorerWidget(QWidget):
    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus: EventBusManager,
            thread_manager: ThreadManager,
            logger: logging.Logger,
            export_settings: Dict[str, Any],
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the VCDB Explorer widget.

        Args:
            database_handler: The database handler for VCDB operations
            event_bus: The event bus for inter-component communication
            thread_manager: The thread manager for handling background tasks
            logger: The logger instance for this widget
            export_settings: Settings for data export operations
            parent: The parent widget
        """
        super().__init__(parent)
        self._database_handler = database_handler
        self._event_bus = event_bus
        self._thread_manager = thread_manager
        self._logger = logger
        self._export_settings = export_settings
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        title = QLabel('VCdb Explorer')
        title.setStyleSheet('font-weight: bold; font-size: 18px;')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(title)

        self._exporter = DataExporter(logger)
        self._event_bus.subscribe(
            event_type=VCdbEventType.filters_refreshed(),
            callback=self._on_filters_refreshed,
            subscriber_id='vcdb_explorer_widget'
        )

        self._create_ui_components()
        self._connect_signals()

    def __del__(self) -> None:
        try:
            self._event_bus.unsubscribe(subscriber_id='vcdb_explorer_widget')
        except Exception:
            pass

    def _create_ui_components(self) -> None:
        """Create and arrange UI components."""
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)
        self._filter_panel_manager = FilterPanelManager(
            self._database_handler,
            self._event_bus,
            self._logger,
            max_panels=self._export_settings.get('max_filter_panels', 5)
        )

        filter_section = QWidget()
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(self._filter_panel_manager)

        query_button_layout = QHBoxLayout()
        query_button_layout.addStretch()
        self._run_query_btn = QPushButton('Run Query')
        self._run_query_btn.setMinimumWidth(150)
        self._run_query_btn.clicked.connect(self._execute_query)
        query_button_layout.addWidget(self._run_query_btn)
        query_button_layout.addStretch()
        filter_layout.addLayout(query_button_layout)
        filter_section.setLayout(filter_layout)

        self._data_table = DataTableWidget(
            self._database_handler,
            self._event_bus,
            self._logger,
            self
        )

        self._main_splitter.addWidget(filter_section)
        self._main_splitter.addWidget(self._data_table)
        self._main_splitter.setSizes([400, 600])
        self._layout.addWidget(self._main_splitter)

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        self._filter_panel_manager.filtersChanged.connect(self._on_filters_changed)

    @Slot()
    def _on_filters_changed(self) -> None:
        """Handle filters changed event."""
        self._logger.debug('Filters changed in UI')

    @Slot(Any)
    def _on_filters_refreshed(self, event: Any) -> None:
        """
        Handle filters refreshed event.

        Args:
            event: The event containing filter data
        """
        # Make sure we handle this on the main thread
        if not self._thread_manager.is_main_thread():
            self._thread_manager.run_on_main_thread(
                lambda: self._on_filters_refreshed(event)
            )
            return

        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})
        self._logger.debug(f'Filters refreshed event received for panel {panel_id}')
        self._filter_panel_manager.update_filter_values(panel_id, filter_values)

    @Slot()
    def _execute_query(self) -> None:
        """Execute the query with the current filter settings."""
        try:
            # Make sure we execute on the main thread
            if not self._thread_manager.is_main_thread():
                self._thread_manager.run_on_main_thread(self._execute_query)
                return

            self._logger.debug('Execute query triggered')
            self._run_query_btn.setEnabled(False)
            filter_panels = self._filter_panel_manager.get_all_filters()
            self._logger.debug(f'Collected filter panels: {filter_panels}')

            if not any((panel for panel in filter_panels if panel)):
                if QMessageBox.question(
                        self,
                        'No Filters',
                        "You haven't set any filters. This could return a large number of results. Continue?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                ) != QMessageBox.StandardButton.Yes:
                    self._run_query_btn.setEnabled(True)
                    return

            # Use thread manager instead of direct query execution
            self._thread_manager.submit_task(
                self._database_handler._execute_query_thread,
                filter_panels=filter_panels,
                columns=self._data_table.get_selected_columns(),
                page=1,
                page_size=self._data_table.get_page_size(),
                sort_by=None,
                sort_desc=False,
                table_filters={},
                callback_id=self._data_table.get_callback_id(),
                name=f"query_execution",
                submitter="vcdb_explorer",
                result_handler=self._handle_query_result
            )

        except Exception as e:
            self._logger.error(f'Query execution error: {str(e)}')
            QMessageBox.critical(self, 'Query Error', f'Error executing query: {str(e)}')
            self._run_query_btn.setEnabled(True)

    def _handle_query_result(self, result: TaskResult) -> None:
        """
        Handle the query execution result.

        Args:
            result: The task result
        """
        # Make sure we handle this on the main thread
        if not self._thread_manager.is_main_thread():
            self._thread_manager.run_on_main_thread(
                lambda: self._handle_query_result(result)
            )
            return

        self._run_query_btn.setEnabled(True)

        if not result.success:
            self._logger.error(f'Query failed: {result.error}')
            QMessageBox.critical(self, 'Query Error', f'Error executing query: {result.error}')
            return

        self._logger.debug('Query executed successfully')

    def refresh_filters(self) -> None:
        """Refresh all filter panels."""
        if hasattr(self, '_filter_panel_manager'):
            self._filter_panel_manager.refresh_all_panels()
            QMessageBox.information(self, 'Filters Refreshed', 'All filters have been refreshed.')


class VCdbExplorerPlugin(BasePlugin):
    name = 'vcdb_explorer'
    version = '1.0.0'
    description = 'Advanced query tool for exploring Vehicle Component Database'
    author = 'Qorzen Developer'
    # Required property for panel integration
    display_name = 'VCdb Explorer'
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the plugin instance."""
        super().__init__()
        self._main_widget: Optional[VCdbExplorerWidget] = None
        self._database_handler: Optional[DatabaseHandler] = None
        self._logger: Optional[logging.Logger] = None
        self._event_bus: Optional[EventBusManager] = None
        self._thread_manager: Optional[ThreadManager] = None
        self._db_config: Dict[str, Any] = {}
        self._ui_config: Dict[str, Any] = {}
        self._export_config: Dict[str, Any] = {}
        self._connection_registered = False
        self._initialization_complete = False
        self._icon_path: Optional[str] = None

    def initialize(
            self,
            event_bus: EventBusManager,
            logger_provider: LoggingManager,
            config_provider: ConfigManager,
            file_manager: FileManager,
            thread_manager: ThreadManager,
            database_manager: DatabaseManager,
            remote_services_manager: RemoteServicesManager,
            security_manager: SecurityManager,
            api_manager: APIManager,
            cloud_manager: CloudManager,
            **kwargs: Any
    ) -> None:
        """
        Initialize the plugin with required managers.

        Args:
            event_bus: Event bus manager
            logger_provider: Logger manager
            config_provider: Configuration manager
            file_manager: File manager
            thread_manager: Thread manager
            database_manager: Database manager
            remote_services_manager: Remote services manager
            security_manager: Security manager
            api_manager: API manager
            cloud_manager: Cloud manager
            **kwargs: Additional keyword arguments
        """
        super().initialize(
            event_bus,
            logger_provider,
            config_provider,
            file_manager,
            thread_manager,
            database_manager,
            remote_services_manager,
            security_manager,
            api_manager,
            cloud_manager,
            **kwargs
        )

        self._logger = logger_provider.get_logger(self.name)
        self._logger.info(f'Initializing {self.name} plugin')
        self._thread_manager = thread_manager
        self._event_bus = event_bus
        self._load_config()

        # Find plugin directory and icon path
        plugin_dir = self._find_plugin_directory()
        if plugin_dir:
            icon_path = os.path.join(plugin_dir, 'resources', 'icon.png')
            if os.path.exists(icon_path):
                self._icon_path = icon_path
                self._logger.debug(f'Found plugin icon at: {icon_path}')

        # Gracefully handle database initialization
        if not database_manager:
            self._logger.error('DatabaseManager is required but was not provided')
            self._database_handler = None
            self._connection_registered = False
        else:
            try:
                if self._thread_manager.is_main_thread():
                    self._init_database_connection(database_manager)
                else:
                    self._thread_manager.execute_on_main_thread_sync(self._init_database_connection,
                                                                     database_manager)
            except Exception as e:
                self._logger.error(f'Failed to initialize database connection: {str(e)}')
                # Don't let the exception propagate, handle it here
                self._database_handler = None
                self._connection_registered = False

        self._event_bus.subscribe(
            event_type='vcdb_explorer:log_message',
            callback=self._on_log_message,
            subscriber_id='vcdb_explorer_plugin'
        )

        self._initialization_complete = True
        self._logger.info(f'{self.name} plugin initialized successfully')

    def _find_plugin_directory(self) -> Optional[str]:
        """Find the plugin's directory."""
        import inspect
        try:
            # Get the path of the current module file
            module_path = inspect.getmodule(self).__file__
            if module_path:
                # Get directory containing the module
                return os.path.dirname(os.path.abspath(module_path))
        except (AttributeError, TypeError):
            pass
        return None

    def _init_database_connection(self, database_manager: DatabaseManager) -> None:
        """
        Initialize the database connection on the main thread.

        Args:
            database_manager: The database manager instance
        """
        try:
            self._database_handler = DatabaseHandler(database_manager, self._event_bus, self._thread_manager,
                                                     self._logger)

            existing_connections = database_manager.get_connection_names()
            if DatabaseHandler.CONNECTION_NAME not in existing_connections:
                try:
                    self._database_handler.configure(
                        self._db_config.get('host', 'localhost'),
                        self._db_config.get('port', 5432),
                        self._db_config.get('database', 'vcdb'),
                        self._db_config.get('user', 'postgres'),
                        self._db_config.get('password', '')
                    )
                    self._connection_registered = True
                except Exception as e:
                    self._logger.error(f'Failed to configure database connection: {str(e)}')
                    # Don't let the exception propagate
                    self._connection_registered = False
            else:
                self._logger.warning(
                    f'Connection "{DatabaseHandler.CONNECTION_NAME}" already exists, reusing existing connection')
                self._connection_registered = True
        except Exception as e:
            self._logger.error(f'Failed to initialize database handler: {str(e)}')
            # Don't let the exception propagate
            self._database_handler = None
            self._connection_registered = False

    def _load_config(self) -> None:
        """Load plugin configuration from the config provider."""
        if not self._config:
            return

        self._db_config = {
            'host': self._config.get(f'plugins.{self.name}.database.host', 'localhost'),
            'port': self._config.get(f'plugins.{self.name}.database.port', 5432),
            'database': self._config.get(f'plugins.{self.name}.database.name', 'vcdb'),
            'user': self._config.get(f'plugins.{self.name}.database.user', 'postgres'),
            'password': self._config.get(f'plugins.{self.name}.database.password', '')
        }

        self._ui_config = {
            'max_filter_panels': self._config.get(f'plugins.{self.name}.ui.max_filter_panels', 5),
            'default_page_size': self._config.get(f'plugins.{self.name}.ui.default_page_size', 100)
        }

        self._export_config = {
            'max_rows': self._config.get(f'plugins.{self.name}.export.max_rows', 0)
        }

        if self._logger:
            self._logger.debug('Configuration loaded')

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """
        Set up UI components when the main UI is ready.

        Args:
            ui_integration: The UI integration instance
        """
        if self._logger:
            self._logger.info('Setting up UI components')

            # Set flag to prevent concurrent UI setup
        if hasattr(self, '_ui_setup_in_progress') and self._ui_setup_in_progress:
            self._logger.warning('UI setup already in progress, skipping duplicate call')
            return

            # Set up in progress flag
        self._ui_setup_in_progress = True

        try:
            # Ensure we're on the main thread
            if not self._thread_manager.is_main_thread():
                self._logger.warning("on_ui_ready called from non-main thread, delegating to main thread")
                self._thread_manager.execute_on_main_thread_sync(
                    self.on_ui_ready,
                    ui_integration
                )
                return

            # Prevent duplicate UI component creation
            if hasattr(self, '_ui_components_created') and self._ui_components_created:
                self._logger.warning('UI components already created, skipping duplicate creation')
                return

            # Add menu items to the Plugins menu
            plugins_menu = ui_integration.find_menu('Plugins')
            if not plugins_menu:
                plugins_menu = ui_integration.add_menu(self.name, 'Plugins')

            vcdb_menu = None
            for action in plugins_menu.actions():
                if action.text() == 'VCdb Explorer' and action.menu():
                    vcdb_menu = action.menu()
                    self._logger.debug('Found existing VCdb Explorer menu')
                    break

            if not vcdb_menu:
                vcdb_menu = ui_integration.add_menu(self.name, 'VCdb Explorer', plugins_menu)

            # TODO: Add menu action checking
            ui_integration.add_menu_action(self.name, vcdb_menu, 'Run Query',
                                           lambda: self._thread_manager.run_on_main_thread(self._run_query))
            ui_integration.add_menu_action(self.name, vcdb_menu, 'Refresh Filters',
                                           lambda: self._thread_manager.run_on_main_thread(self._refresh_filters))
            ui_integration.add_menu_action(self.name, vcdb_menu, 'Documentation',
                                           lambda: self._thread_manager.run_on_main_thread(self._open_documentation))
            ui_integration.add_menu_action(self.name, vcdb_menu, 'Configuration',
                                           lambda: self._thread_manager.run_on_main_thread(self._open_configuration))

            if not self._database_handler or not getattr(self._database_handler, '_initialized', False):
                self._main_widget = self._create_error_widget()
                self._logger.warning('Added error widget due to database connection failure')
            else:
                try:
                    if not self._main_widget:  # Only create if not already created
                        self._main_widget = VCdbExplorerWidget(self._database_handler,
                                                               self._event_bus,
                                                               self._thread_manager,
                                                               self._logger,
                                                               self._export_config,
                                                               None)
                    if self._logger:
                        self._logger.info('UI components set up successfully')
                except Exception as e:
                    if self._logger:
                        self._logger.error(f'Failed to set up UI components: {str(e)}')
                    self._main_widget = self._create_error_widget(str(e))
            self._ui_components_created = True
        finally:
            self._ui_setup_in_progress = False

    def _create_error_widget(self, error_message: Optional[str] = None) -> QWidget:
        """
        Create an error widget to display when database connection fails.
        Must be called from the main thread.

        Args:
            error_message: Optional specific error message to display

        Returns:
            QWidget displaying the error
        """
        error_widget = QWidget()
        error_layout = QVBoxLayout()
        error_widget.setLayout(error_layout)

        error_label = QLabel('Database Connection Error')
        error_label.setStyleSheet('font-weight: bold; color: red; font-size: 16px;')
        error_layout.addWidget(error_label)

        message_text = error_message or 'Could not connect to the VCdb database. Check your configuration or database server status.'
        message = QLabel(message_text)
        message.setWordWrap(True)
        error_layout.addWidget(message)

        button_layout = QHBoxLayout()
        config_btn = QPushButton('Open Configuration')
        config_btn.clicked.connect(lambda: self._thread_manager.run_on_main_thread(self._open_configuration))
        button_layout.addWidget(config_btn)

        error_layout.addLayout(button_layout)
        error_layout.addStretch()

        return error_widget

    def _on_log_message(self, event: Any) -> None:
        """
        Handle log message events from the plugin.

        Args:
            event: The log message event
        """
        if not self._logger:
            return

        payload = event.payload
        level = payload.get('level', 'info')
        message = payload.get('message', '')

        if level == 'debug':
            self._logger.debug(message)
        elif level == 'info':
            self._logger.info(message)
        elif level == 'warning':
            self._logger.warning(message)
        elif level == 'error':
            self._logger.error(message)
        else:
            self._logger.info(f'[{level}] {message}')

    def _refresh_filters(self) -> None:
        """Refresh all filter panels."""
        if self._main_widget and hasattr(self._main_widget, 'refresh_filters'):
            self._main_widget.refresh_filters()

    def _run_query(self) -> None:
        """Run the query using the current filter settings."""
        if self._main_widget and hasattr(self._main_widget, '_execute_query'):
            self._main_widget._execute_query()

    def _open_documentation(self) -> None:
        """Show documentation information."""
        if self._logger:
            self._logger.info('Documentation requested')

        QMessageBox.information(
            None,
            'Documentation',
            'The VCdb Explorer plugin provides an interface to query and explore the Vehicle Component Database.\n\n'
            'For more information, please refer to the online documentation.'
        )

    def _open_configuration(self) -> None:
        """Show configuration information."""
        QMessageBox.information(
            None,
            'Configuration',
            'To configure the VCdb Explorer plugin, edit the configuration file and restart the application.'
        )

    def get_main_widget(self) -> Optional[QWidget]:
        """
        Return the main widget for this plugin.

        Returns:
            The main VCdb Explorer widget
        """
        return self._main_widget

    def get_icon(self) -> Optional[str]:
        """
        Return the path to the plugin icon.

        Returns:
            Path to icon or None if no icon is available
        """
        return self._icon_path

    def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        if self._logger:
            self._logger.info(f'Shutting down {self.name} plugin')

        if self._event_bus:
            self._event_bus.unsubscribe(subscriber_id='vcdb_explorer_plugin')

        if self._database_handler and self._connection_registered:
            try:
                self._database_handler.shutdown()
                self._connection_registered = False
            except Exception as e:
                if self._logger:
                    self._logger.error(f'Error shutting down database handler: {str(e)}')

        self._main_widget = None

        if self._logger:
            self._logger.info(f'{self.name} plugin shutdown complete')