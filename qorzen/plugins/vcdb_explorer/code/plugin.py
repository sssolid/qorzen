from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QMessageBox, QProgressDialog,
    QPushButton, QSplitter, QVBoxLayout, QWidget
)

from qorzen.core import (
    RemoteServicesManager, SecurityManager, APIManager, CloudManager,
    LoggingManager, ConfigManager, DatabaseManager, EventBusManager,
    FileManager, ThreadManager
)
from qorzen.plugin_system.interface import PluginInterface
from qorzen.ui.integration import UIIntegration, TabComponent

from .database_handler import DatabaseHandler
from .data_table import DataTableWidget
from .events import VCdbEventType
from .export import DataExporter
from .filter_panel import FilterPanelManager


class VCdbExplorerTab(QWidget):
    """Main tab for VCdb Explorer."""

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus: EventBusManager,
            logger: logging.Logger,
            export_settings: Dict[str, Any],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize VCdb Explorer tab.

        Args:
            database_handler: Database handler for queries
            event_bus: Event bus for communication
            logger: Logger instance
            export_settings: Export configuration settings
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

        # Subscribe to filter refresh events
        self._event_bus.subscribe(
            event_type=VCdbEventType.filters_refreshed(),
            callback=self._on_filters_refreshed,
            subscriber_id='vcdb_explorer_tab'
        )

        self._create_ui_components()
        self._connect_signals()

    def __del__(self) -> None:
        """Clean up event subscriptions."""
        try:
            self._event_bus.unsubscribe(subscriber_id='vcdb_explorer_tab')
        except Exception:
            pass

    def get_widget(self) -> QWidget:
        """Get the main widget.

        Returns:
            The tab widget
        """
        return self

    def on_tab_selected(self) -> None:
        """Handle tab selection."""
        pass

    def on_tab_deselected(self) -> None:
        """Handle tab deselection."""
        pass

    def _create_ui_components(self) -> None:
        """Create UI components."""
        # Main splitter for filter panel and data table
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Filter panel
        self._filter_panel_manager = FilterPanelManager(
            self._database_handler,
            self._event_bus,
            self._logger,
            max_panels=self._export_settings.get('max_filter_panels', 5)
        )

        # Filter section with query button
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

        # Data table
        self._data_table = DataTableWidget(
            self._database_handler,
            self._event_bus,
            self._logger,
            self
        )

        # Add components to splitter
        self._main_splitter.addWidget(filter_section)
        self._main_splitter.addWidget(self._data_table)
        self._main_splitter.setSizes([400, 600])

        self._layout.addWidget(self._main_splitter)

    def _connect_signals(self) -> None:
        """Connect signal/slot connections."""
        self._filter_panel_manager.filtersChanged.connect(self._on_filters_changed)

    @Slot()
    def _on_filters_changed(self) -> None:
        """Handle filter changes in UI."""
        self._logger.debug('Filters changed in UI')

    @Slot(Any)
    def _on_filters_refreshed(self, event: Any) -> None:
        """Handle filters refreshed event.

        Args:
            event: Filters refreshed event
        """
        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})

        self._logger.debug(f'Filters refreshed event received for panel {panel_id}')
        self._filter_panel_manager.update_filter_values(panel_id, filter_values)

    @Slot()
    def _execute_query(self) -> None:
        """Handle execution of the query when the user clicks the Run Query button."""
        try:
            self._logger.debug('Execute query triggered')
            self._run_query_btn.setEnabled(False)

            # Get all filter panels data
            filter_panels = self._filter_panel_manager.get_all_filters()
            self._logger.debug(f'Collected filter panels: {filter_panels}')

            # Check if any filters are set
            if not any(panel for panel in filter_panels if panel):
                # No filters set, confirm with user
                if QMessageBox.question(
                        self,
                        'No Filters',
                        "You haven't set any filters. This could return a large number of results. Continue?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                ) != QMessageBox.StandardButton.Yes:
                    self._run_query_btn.setEnabled(True)
                    return

            # Execute the query directly using the DataTableWidget's new method
            self._data_table.execute_query(filter_panels)

            # Re-enable the button after a delay
            QTimer.singleShot(1000, lambda: self._run_query_btn.setEnabled(True))

        except Exception as e:
            self._logger.error(f'Query execution error: {str(e)}')
            QMessageBox.critical(self, 'Query Error', f'Error executing query: {str(e)}')
            self._run_query_btn.setEnabled(True)


class VCdbExplorerPlugin(PluginInterface):
    """VCdb Explorer plugin main class."""

    name = 'vcdb_explorer'
    version = '1.0.0'
    description = 'Advanced query tool for exploring Vehicle Component Database'
    author = 'Qorzen Developer'
    dependencies = []

    def __init__(self) -> None:
        """Initialize plugin."""
        super().__init__()
        self._tab: Optional[VCdbExplorerTab] = None
        self._database_handler: Optional[DatabaseHandler] = None
        self._logger: Optional[logging.Logger] = None
        self._event_bus: Optional[EventBusManager] = None
        self._config: Optional[ConfigManager] = None
        self._thread_manager: Optional[ThreadManager] = None
        self._file_manager: Optional[FileManager] = None
        self._database_manager: Optional[DatabaseManager] = None
        self._remote_services_manager: Optional[RemoteServicesManager] = None
        self._security_manager: Optional[SecurityManager] = None
        self._api_manager: Optional[APIManager] = None
        self._cloud_manager: Optional[CloudManager] = None
        self._db_config: Dict[str, Any] = {}
        self._ui_config: Dict[str, Any] = {}
        self._export_config: Dict[str, Any] = {}

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
            event_bus: Event bus for communication
            logger_provider: Logger provider
            config_provider: Configuration provider
            file_manager: File manager for file operations
            thread_manager: Thread manager for async operations
            database_manager: Database manager for database connections
            remote_services_manager: Remote services manager
            security_manager: Security manager
            api_manager: API manager
            cloud_manager: Cloud manager
            **kwargs: Additional keyword arguments
        """
        self._logger = logger_provider.get_logger(self.name)
        self._logger.info(f'Initializing {self.name} plugin')

        self._event_bus = event_bus
        self._config = config_provider
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._database_manager = database_manager
        self._remote_services_manager = remote_services_manager
        self._security_manager = security_manager
        self._api_manager = api_manager
        self._cloud_manager = cloud_manager

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

        # Configure database connection
        try:
            self._database_handler.configure(
                self._db_config.get('host', 'localhost'),
                self._db_config.get('port', 5432),
                self._db_config.get('database', 'vcdb'),
                self._db_config.get('user', 'postgres'),
                self._db_config.get('password', '')
            )
        except Exception as e:
            self._logger.error(f'Failed to configure database connection: {str(e)}')

        # Subscribe to log messages
        self._event_bus.subscribe(
            event_type='vcdb_explorer:log_message',
            callback=self._on_log_message,
            subscriber_id='vcdb_explorer_plugin'
        )

        self._logger.info(f'{self.name} plugin initialized successfully')

    def _on_log_message(self, event: Any) -> None:
        """Handle log message events.

        Args:
            event: Log message event
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

    def _load_config(self) -> None:
        """Load configuration settings."""
        if not self._config:
            return

        # Database configuration
        self._db_config = {
            'host': self._config.get(f'plugins.{self.name}.database.host', 'localhost'),
            'port': self._config.get(f'plugins.{self.name}.database.port', 5432),
            'database': self._config.get(f'plugins.{self.name}.database.name', 'vcdb'),
            'user': self._config.get(f'plugins.{self.name}.database.user', 'postgres'),
            'password': self._config.get(f'plugins.{self.name}.database.password', '')
        }

        # UI configuration
        self._ui_config = {
            'max_filter_panels': self._config.get(f'plugins.{self.name}.ui.max_filter_panels', 5),
            'default_page_size': self._config.get(f'plugins.{self.name}.ui.default_page_size', 100)
        }

        # Export configuration
        self._export_config = {
            'max_rows': self._config.get(f'plugins.{self.name}.export.max_rows', 0)
        }

        if self._logger:
            self._logger.debug('Configuration loaded')

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Set up UI components when UI is ready.

        Args:
            ui_integration: UI integration interface
        """
        if self._logger:
            self._logger.info('Setting up UI components')

        # Check database connection
        if not self._database_handler or not getattr(self._database_handler, '_initialized', False):
            # Show error widget if database connection failed
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

            # ui_integration.add_tab(plugin_id=self.name, tab=error_widget, title='VCdb Explorer')

            if self._logger:
                self._logger.warning('Added error tab due to database connection failure')

            return

        try:
            # Create main tab
            self._tab = VCdbExplorerTab(
                self._database_handler,
                self._event_bus,
                self._logger,
                self._export_config,
                None
            )

            # ui_integration.add_tab(plugin_id=self.name, tab=self._tab, title='VCdb Explorer')

            # Add menu items
            # tools_menu = ui_integration.find_menu('&Tools')
            # if tools_menu:
            #     menu = ui_integration.add_menu(
            #         plugin_id=self.name,
            #         title='VCdb Explorer',
            #         parent_menu=tools_menu
            #     )
            #
            #     ui_integration.add_menu_action(
            #         plugin_id=self.name,
            #         menu=menu,
            #         text='Run Query',
            #         callback=self._run_query
            #     )
            #
            #     ui_integration.add_menu_action(
            #         plugin_id=self.name,
            #         menu=menu,
            #         text='Open Documentation',
            #         callback=self._open_documentation
            #     )
            #
            #     ui_integration.add_menu_action(
            #         plugin_id=self.name,
            #         menu=menu,
            #         text='Refresh Filters',
            #         callback=self._refresh_filters
            #     )

            if self._logger:
                self._logger.info('UI components set up successfully')

        except Exception as e:
            if self._logger:
                self._logger.error(f'Failed to set up UI components: {str(e)}')

            # Show error widget
            error_widget = QWidget()
            error_layout = QVBoxLayout()

            error_label = QLabel('UI Initialization Error')
            error_label.setStyleSheet('font-weight: bold; color: red; font-size: 16px;')
            error_layout.addWidget(error_label)

            message = QLabel(f'An error occurred while setting up the UI: {str(e)}')
            error_layout.addWidget(message)

            retry_btn = QPushButton('Retry')
            retry_btn.clicked.connect(lambda: self._retry_ui_setup(ui_integration))
            error_layout.addWidget(retry_btn)

            error_layout.addStretch()

            error_widget.setLayout(error_layout)

            ui_integration.add_tab(plugin_id=self.name, tab=error_widget, title='VCdb Explorer')

    def _retry_ui_setup(self, ui_integration: UIIntegration) -> None:
        """Retry UI setup after failure.

        Args:
            ui_integration: UI integration interface
        """
        self.on_ui_ready(ui_integration)

    def _refresh_filters(self) -> None:
        """Refresh all filters."""
        if self._tab and hasattr(self._tab, '_filter_panel_manager'):
            self._tab._filter_panel_manager.refresh_all_panels()
            QMessageBox.information(None, 'Filters Refreshed', 'All filters have been refreshed.')

    def _run_query(self) -> None:
        """Run query with current filters."""
        if self._tab:
            self._tab._execute_query()

    def _open_documentation(self) -> None:
        """Show documentation."""
        if self._logger:
            self._logger.info('Documentation requested')

        QMessageBox.information(
            None,
            'Documentation',
            'The VCdb Explorer plugin provides an interface to query and explore the Vehicle Component Database.\n\n'
            'For more information, please refer to the online documentation.'
        )

    def _open_configuration(self) -> None:
        """Open configuration dialog."""
        QMessageBox.information(
            None,
            'Configuration',
            'To configure the VCdb Explorer plugin, edit the configuration file and restart the application.'
        )

    def shutdown(self) -> None:
        """Shut down the plugin and clean up resources."""
        if self._logger:
            self._logger.info(f'Shutting down {self.name} plugin')

        if self._event_bus:
            self._event_bus.unsubscribe(subscriber_id='vcdb_explorer_plugin')

        if self._database_handler:
            try:
                self._database_handler.shutdown()
            except Exception as e:
                if self._logger:
                    self._logger.error(f'Error shutting down database handler: {str(e)}')

        self._tab = None

        if self._logger:
            self._logger.info(f'{self.name} plugin shutdown complete')