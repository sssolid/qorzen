from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSplitter, QFrame,
    QMessageBox, QProgressDialog, QFileDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QEventLoop

from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration, TabComponent

from .database_handler import DatabaseHandler
from .filter_panel import FilterPanelManager
from .data_table import DataTableWidget
from .export import DataExporter, ExportError


class VCdbExplorerTab(QWidget):
    """Main tab widget for the VCdb Explorer."""

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus: Any,
            logger: logging.Logger,
            export_settings: Dict[str, Any],
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the VCdb Explorer tab.

        Args:
            database_handler: Database handler for database operations
            event_bus: Event bus for component communication
            logger: Logger instance
            export_settings: Export settings
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
        title.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(title)

        self._exporter = DataExporter(logger)

        # Register event handlers
        self._event_bus.register('vcdb_explorer:filters_refreshed', self._on_filters_refreshed)

        self._create_ui_components()
        self._connect_signals()

    def get_widget(self) -> QWidget:
        """Get the widget to display in the tab."""
        return self

    def on_tab_selected(self) -> None:
        """Handle tab selection."""
        pass

    def on_tab_deselected(self) -> None:
        """Handle tab deselection."""
        pass

    def _create_ui_components(self) -> None:
        """Create the UI components."""
        self._main_splitter = QSplitter(Qt.Vertical)

        # Filter panel section
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

        # Data table section
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
        """Connect signals and slots."""
        self._filter_panel_manager.filtersChanged.connect(self._on_filters_changed)

    @Slot()
    def _on_filters_changed(self) -> None:
        """Handle filter changes."""
        self._logger.debug("Filters changed in UI")
        # This event is informational only - no action needed here

    @Slot(str, dict)
    def _on_filters_refreshed(self, panel_id: str, filter_values: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Handle filters refreshed event.

        Args:
            panel_id: ID of the filter panel
            filter_values: Dictionary of filter values by type
        """
        self._logger.debug(f"Filters refreshed event received for panel {panel_id}")
        self._filter_panel_manager.update_filter_values(panel_id, filter_values)

    @Slot()
    def _execute_query(self) -> None:
        """Execute the query with current filters."""
        try:
            self._logger.debug("Execute query triggered")

            # Disable the button to prevent multiple clicks
            self._run_query_btn.setEnabled(False)

            # Get the current filter values
            filter_panels = self._filter_panel_manager.get_all_filters()

            # Confirm if no filters are set
            if not any(filter_panels):
                if QMessageBox.question(
                        self,
                        'No Filters',
                        "You haven't set any filters. This could return a large number of results. Continue?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                ) != QMessageBox.Yes:
                    self._run_query_btn.setEnabled(True)
                    return

            # Show a busy indicator
            progress = QProgressDialog("Executing query...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            progress.setMinimumDuration(500)  # Only show for queries taking more than 500ms
            progress.setValue(0)

            # Execute the query (this will happen in background through event_bus)
            self._data_table.execute_query(filter_panels)

            # Re-enable the button after a short delay
            QTimer.singleShot(1000, lambda: self._run_query_btn.setEnabled(True))

        except Exception as e:
            self._logger.error(f'Query execution error: {str(e)}')
            QMessageBox.critical(self, 'Query Error', f'Error executing query: {str(e)}')
            self._run_query_btn.setEnabled(True)


class VCdbExplorerPlugin(BasePlugin):
    """VCdb Explorer plugin for Qorzen."""

    name = 'vcdb_explorer'
    version = '1.0.0'
    description = 'Advanced query tool for exploring Vehicle Component Database'
    author = 'Qorzen Developer'
    dependencies = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._tab: Optional[VCdbExplorerTab] = None
        self._database_handler: Optional[DatabaseHandler] = None

    def initialize(
            self,
            event_bus: Any,
            logger_provider: Any,
            config_provider: Any,
            file_manager: Any,
            thread_manager: Any,
            **kwargs: Any
    ) -> None:
        """
        Initialize the plugin with enhanced core system integration.

        Args:
            event_bus: Event bus for component communication
            logger_provider: Logger provider for logging
            config_provider: Configuration provider
            file_manager: File manager
            thread_manager: Thread manager
            **kwargs: Additional arguments
        """
        super().initialize(
            event_bus,
            logger_provider,
            config_provider,
            file_manager,
            thread_manager,
            **kwargs
        )

        self._logger = logger_provider.get_logger(self.name)
        self._logger.info(f'Initializing {self.name} plugin')

        # Load configuration
        self._load_config()

        # Initialize critical subsystems with retry logic
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                # Get the database manager from kwargs or try to get from the application
                database_manager = kwargs.get('database_manager')
                if not database_manager and 'app' in kwargs:
                    try:
                        database_manager = kwargs['app'].get_manager('database_manager')
                        self._logger.info("Found database_manager in application")
                    except Exception as e:
                        self._logger.warning(f"Could not get database_manager from application: {str(e)}")

                # Initialize the database handler
                self._database_handler = DatabaseHandler(
                    database_manager if database_manager else None,
                    event_bus,
                    thread_manager,
                    self._logger
                )

                # Configure the database handler with connection parameters if needed
                if not database_manager:
                    self._logger.info("Using direct database connection")
                    self._database_handler.configure(
                        host=self._db_config['host'],
                        port=self._db_config['port'],
                        database=self._db_config['database'],
                        user=self._db_config['user'],
                        password=self._db_config['password']
                    )

                # Register essential event handlers
                event_bus.register('vcdb_explorer:log_message', self._on_log_message)

                # Setup completed successfully
                self._logger.info(f'{self.name} plugin initialized successfully')
                break

            except Exception as e:
                self._logger.error(f'Initialization attempt {attempt} failed: {str(e)}')

                if attempt < max_retries:
                    self._logger.info(f'Retrying in {retry_delay} seconds...')
                    time.sleep(retry_delay)
                else:
                    self._logger.error(f'Failed to initialize after {max_retries} attempts')
                    # We'll continue and show an error in the UI

    def _on_log_message(self, level: str, message: str) -> None:
        """
        Handle log messages from components.

        Args:
            level: Log level
            message: Log message
        """
        if level == 'debug':
            self._logger.debug(message)
        elif level == 'info':
            self._logger.info(message)
        elif level == 'warning':
            self._logger.warning(message)
        elif level == 'error':
            self._logger.error(message)
        else:
            self._logger.info(f"[{level}] {message}")

    def _load_config(self) -> None:
        """Load configuration settings."""
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
            'max_rows': self._config.get(f'plugins.{self.name}.export.max_rows', 10000)
        }

        self._logger.debug('Configuration loaded')

    def on_ui_ready(self, ui_integration: Any) -> None:
        """
        Handle UI ready event with enhanced error handling.

        Args:
            ui_integration: UI integration instance
        """
        self._logger.info('Setting up UI components')

        # Check if database initialization was successful
        if not self._database_handler or not getattr(self._database_handler, '_initialized', False):
            # Create error widget with retry button
            error_widget = QWidget()
            error_layout = QVBoxLayout()

            error_label = QLabel('Database Connection Error')
            error_label.setStyleSheet('font-weight: bold; color: red; font-size: 16px;')
            error_layout.addWidget(error_label)

            message = QLabel(
                'Could not connect to the VCdb database. Check your configuration or database server status.'
            )
            error_layout.addWidget(message)

            # Add buttons
            button_layout = QHBoxLayout()

            retry_btn = QPushButton('Retry Connection')
            retry_btn.clicked.connect(self._retry_database_connection)
            button_layout.addWidget(retry_btn)

            config_btn = QPushButton('Open Configuration')
            config_btn.clicked.connect(self._open_configuration)
            button_layout.addWidget(config_btn)

            error_layout.addLayout(button_layout)
            error_layout.addStretch()
            error_widget.setLayout(error_layout)

            ui_integration.add_tab(plugin_id=self.name, tab=error_widget, title='VCdb Explorer')
            self._logger.warning('Added error tab due to database connection failure')
            return

        # Create main tab with retry mechanism for component creation
        try:
            self._tab = VCdbExplorerTab(
                self._database_handler,
                self._event_bus,
                self._logger,
                self._export_config,
                None
            )

            ui_integration.add_tab(plugin_id=self.name, tab=self._tab, title='VCdb Explorer')

            # Add menu items
            tools_menu = ui_integration.find_menu('&Tools')
            if tools_menu:
                menu = ui_integration.add_menu(plugin_id=self.name, title='VCdb Explorer', parent_menu=tools_menu)
                ui_integration.add_menu_action(plugin_id=self.name, menu=menu, text='Run Query',
                                               callback=self._run_query)
                ui_integration.add_menu_action(plugin_id=self.name, menu=menu, text='Open Documentation',
                                               callback=self._open_documentation)
                ui_integration.add_menu_action(plugin_id=self.name, menu=menu, text='Refresh Filters',
                                               callback=self._refresh_filters)

            self._logger.info('UI components set up successfully')

        except Exception as e:
            self._logger.error(f'Failed to set up UI components: {str(e)}')

            # Create error widget
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

    def _retry_database_connection(self) -> None:
        """Retry the database connection."""
        progress = QProgressDialog("Retrying database connection...", "Cancel", 0, 0, None)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(500)
        progress.setValue(0)

        def perform_retry():
            try:
                # Re-configure the database handler
                if self._database_handler:
                    self._database_handler.configure(
                        host=self._db_config['host'],
                        port=self._db_config['port'],
                        database=self._db_config['database'],
                        user=self._db_config['user'],
                        password=self._db_config['password']
                    )

                    # Test if the connection was successful
                    if getattr(self._database_handler, '_initialized', False):
                        QMessageBox.information(
                            None,
                            "Connection Successful",
                            "Database connection established. Please restart the application to load VCdb Explorer."
                        )
                    else:
                        QMessageBox.critical(
                            None,
                            "Connection Failed",
                            "Failed to connect to the database. Please check your configuration."
                        )
                else:
                    QMessageBox.critical(
                        None,
                        "Error",
                        "Database handler not available. Please restart the application."
                    )

            except Exception as e:
                self._logger.error(f"Error retrying database connection: {str(e)}")
                QMessageBox.critical(
                    None,
                    "Connection Error",
                    f"An error occurred while connecting to the database: {str(e)}"
                )

            finally:
                progress.cancel()

        # Run in a thread to keep UI responsive
        threading.Thread(target=perform_retry, daemon=True).start()

    def _retry_ui_setup(self, ui_integration: Any) -> None:
        """
        Retry setting up the UI components.

        Args:
            ui_integration: UI integration instance
        """
        self.on_ui_ready(ui_integration)

    def _refresh_filters(self) -> None:
        """Refresh all filters in all panels."""
        if self._tab and hasattr(self._tab, '_filter_panel_manager'):
            self._tab._filter_panel_manager.refresh_all_panels()
            QMessageBox.information(None, "Filters Refreshed", "All filters have been refreshed.")

    def _run_query(self) -> None:
        """Run the query (menu action callback)."""
        if self._tab:
            self._tab._execute_query()

    def _open_documentation(self) -> None:
        """Open documentation (menu action callback)."""
        self._logger.info('Documentation requested')
        # Implementation for opening documentation would go here

    def shutdown(self) -> None:
        """Shut down the plugin."""
        self._logger.info(f'Shutting down {self.name} plugin')

        if self._database_handler:
            try:
                self._database_handler.shutdown()
            except Exception as e:
                self._logger.error(f'Error shutting down database handler: {str(e)}')

        self._tab = None

        super().shutdown()

        self._logger.info(f'{self.name} plugin shutdown complete')