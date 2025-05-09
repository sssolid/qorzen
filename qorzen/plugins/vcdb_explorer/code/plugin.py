from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from PySide6.QtCore import Qt, Slot, QTimer
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
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration

from .database_handler import DatabaseHandler
from .data_table import DataTableWidget
from .events import VCdbEventType
from .export import DataExporter
from .filter_panel import FilterPanelManager


class VCdbExplorerWidget(QWidget):
    """Main widget for VCdb Explorer plugin."""

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus: EventBusManager,
            logger: logging.Logger,
            export_settings: Dict[str, Any],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize VCdbExplorerWidget.

        Args:
            database_handler: Handler for database operations
            event_bus: System event bus for publishing/subscribing to events
            logger: Logger instance for this component
            export_settings: Settings for data export operations
            parent: Parent widget
        """
        super().__init__(parent)
        self._database_handler = database_handler
        self._event_bus = event_bus
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
        """Create and setup all UI components."""
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Create filter panel
        self._filter_panel_manager = FilterPanelManager(
            self._database_handler,
            self._event_bus,
            self._logger,
            max_panels=self._export_settings.get('max_filter_panels', 5)
        )

        # Create filter section
        filter_section = QWidget()
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(self._filter_panel_manager)

        # Add Run Query button
        query_button_layout = QHBoxLayout()
        query_button_layout.addStretch()
        self._run_query_btn = QPushButton('Run Query')
        self._run_query_btn.setMinimumWidth(150)
        self._run_query_btn.clicked.connect(self._execute_query)
        query_button_layout.addWidget(self._run_query_btn)
        query_button_layout.addStretch()
        filter_layout.addLayout(query_button_layout)
        filter_section.setLayout(filter_layout)

        # Create data table
        self._data_table = DataTableWidget(self._database_handler, self._event_bus, self._logger, self)

        # Add components to splitter
        self._main_splitter.addWidget(filter_section)
        self._main_splitter.addWidget(self._data_table)
        self._main_splitter.setSizes([400, 600])

        self._layout.addWidget(self._main_splitter)

    def _connect_signals(self) -> None:
        """Connect all signals to their respective slots."""
        self._filter_panel_manager.filtersChanged.connect(self._on_filters_changed)

    @Slot()
    def _on_filters_changed(self) -> None:
        """Handle when filters are changed in the UI."""
        self._logger.debug('Filters changed in UI')

    @Slot(Any)
    def _on_filters_refreshed(self, event: Any) -> None:
        """Handle when filters are refreshed.

        Args:
            event: The event data containing filter information
        """
        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})
        self._logger.debug(f'Filters refreshed event received for panel {panel_id}')
        self._filter_panel_manager.update_filter_values(panel_id, filter_values)

    @Slot()
    def _execute_query(self) -> None:
        """Execute the current query based on filter settings."""
        try:
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

            self._data_table.execute_query(filter_panels)
            QTimer.singleShot(1000, lambda: self._run_query_btn.setEnabled(True))

        except Exception as e:
            self._logger.error(f'Query execution error: {str(e)}')
            QMessageBox.critical(self, 'Query Error', f'Error executing query: {str(e)}')
            self._run_query_btn.setEnabled(True)


class VCdbExplorerPlugin(BasePlugin):
    """VCdb Explorer plugin for exploring Vehicle Component Database."""

    name = 'vcdb_explorer'
    version = '1.0.0'
    description = 'Advanced query tool for exploring Vehicle Component Database'
    author = 'Qorzen Developer'
    dependencies = []

    def __init__(self) -> None:
        """Initialize the VCdbExplorerPlugin."""
        super().__init__()
        self._main_widget: Optional[VCdbExplorerWidget] = None
        self._database_handler: Optional[DatabaseHandler] = None
        self._logger: Optional[logging.Logger] = None
        self._event_bus: Optional[EventBusManager] = None
        self._db_config: Dict[str, Any] = {}
        self._ui_config: Dict[str, Any] = {}
        self._export_config: Dict[str, Any] = {}
        self._connection_registered = False

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
        """Initialize the plugin with required services.

        Args:
            event_bus: System event bus for publishing/subscribing to events
            logger_provider: Provider for logger instances
            config_provider: Provider for configuration values
            file_manager: Manager for file operations
            thread_manager: Manager for thread operations
            database_manager: Manager for database connections
            remote_services_manager: Manager for remote service operations
            security_manager: Manager for security operations
            api_manager: Manager for API operations
            cloud_manager: Manager for cloud operations
            **kwargs: Additional keyword arguments
        """
        super().initialize(
            event_bus, logger_provider, config_provider, file_manager,
            thread_manager, database_manager, remote_services_manager,
            security_manager, api_manager, cloud_manager, **kwargs
        )

        self._logger = logger_provider.get_logger(self.name)
        self._logger.info(f'Initializing {self.name} plugin')

        self._load_config()

        if not self._database_manager:
            self._logger.error('DatabaseManager is required but was not provided')
            return

        self._database_handler = DatabaseHandler(
            self._database_manager,
            self._event_bus,
            self._thread_manager,
            self._logger
        )

        # Check if connection already exists
        existing_connections = self._database_manager.get_connection_names()
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
        else:
            self._logger.warning(
                f'Connection "{DatabaseHandler.CONNECTION_NAME}" already exists, reusing existing connection')
            self._connection_registered = True

        self._event_bus.subscribe(
            event_type='vcdb_explorer:log_message',
            callback=self._on_log_message,
            subscriber_id='vcdb_explorer_plugin'
        )

        self._logger.info(f'{self.name} plugin initialized successfully')

    def _load_config(self) -> None:
        """Load configuration settings from the config manager."""
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
        """Handle UI integration when the main UI is ready.

        Args:
            ui_integration: Interface for integrating with the main UI
        """
        if self._logger:
            self._logger.info('Setting up UI components')

        # Create menus
        plugins_menu = ui_integration.find_menu("Plugins")
        if not plugins_menu:
            plugins_menu = ui_integration.add_menu(self.name, "Plugins")

        vcdb_menu = ui_integration.add_menu(self.name, "VCdb Explorer", plugins_menu)

        # Add menu actions
        ui_integration.add_menu_action(
            self.name,
            vcdb_menu,
            "Run Query",
            self._run_query
        )

        ui_integration.add_menu_action(
            self.name,
            vcdb_menu,
            "Refresh Filters",
            self._refresh_filters
        )

        ui_integration.add_menu_action(
            self.name,
            vcdb_menu,
            "Documentation",
            self._open_documentation
        )

        ui_integration.add_menu_action(
            self.name,
            vcdb_menu,
            "Configuration",
            self._open_configuration
        )

        # Check if database is properly initialized
        if not self._database_handler or not getattr(self._database_handler, '_initialized', False):
            error_widget = QWidget()
            error_layout = QVBoxLayout()

            error_label = QLabel('Database Connection Error')
            error_label.setStyleSheet('font-weight: bold; color: red; font-size: 16px;')
            error_layout.addWidget(error_label)

            message = QLabel(
                'Could not connect to the VCdb database. Check your configuration or database server status.')
            error_layout.addWidget(message)

            button_layout = QHBoxLayout()
            config_btn = QPushButton('Open Configuration')
            config_btn.clicked.connect(self._open_configuration)
            button_layout.addWidget(config_btn)

            error_layout.addLayout(button_layout)
            error_layout.addStretch()
            error_widget.setLayout(error_layout)

            if self._logger:
                self._logger.warning('Added error widget due to database connection failure')

            self._main_widget = None
            return

        # Create main widget if database is connected
        try:
            self._main_widget = VCdbExplorerWidget(
                self._database_handler,
                self._event_bus,
                self._logger,
                self._export_config
            )

            if self._logger:
                self._logger.info('UI components set up successfully')

        except Exception as e:
            if self._logger:
                self._logger.error(f'Failed to set up UI components: {str(e)}')

    def _on_log_message(self, event: Any) -> None:
        """Handle log messages from the plugin.

        Args:
            event: The log event containing message information
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
        """Refresh all filters in the UI."""
        if self._main_widget and hasattr(self._main_widget, '_filter_panel_manager'):
            self._main_widget._filter_panel_manager.refresh_all_panels()
            QMessageBox.information(None, 'Filters Refreshed', 'All filters have been refreshed.')

    def _run_query(self) -> None:
        """Execute the current query from the menu."""
        if self._main_widget:
            self._main_widget._execute_query()

    def _open_documentation(self) -> None:
        """Show documentation for the plugin."""
        if self._logger:
            self._logger.info('Documentation requested')

        QMessageBox.information(
            None,
            'Documentation',
            'The VCdb Explorer plugin provides an interface to query and explore the Vehicle Component Database.\n\n'
            'For more information, please refer to the online documentation.'
        )

    def _open_configuration(self) -> None:
        """Show configuration options for the plugin."""
        QMessageBox.information(
            None,
            'Configuration',
            'To configure the VCdb Explorer plugin, edit the configuration file and restart the application.'
        )

    def shutdown(self) -> None:
        """Clean up resources and prepare for shutdown."""
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