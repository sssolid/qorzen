from __future__ import annotations

"""
VCdb Explorer plugin module.

This module provides the main plugin class for the VCdb Explorer, which allows
users to query and interact with the Vehicle Component Database.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union, cast

from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QMessageBox, QProgressDialog,
    QPushButton, QSplitter, QVBoxLayout, QWidget, QFrame, QProgressBar
)
from PySide6.QtGui import QAction, QIcon

from qorzen.core.remote_manager import RemoteServicesManager
from qorzen.core.security_manager import SecurityManager
from qorzen.core.api_manager import APIManager
from qorzen.core.cloud_manager import CloudManager
from qorzen.core.logging_manager import LoggingManager
from qorzen.core.config_manager import ConfigManager
from qorzen.core.database_manager import DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.file_manager import FileManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_integration import UIIntegration
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready

from .database_handler import DatabaseHandler
from .data_table import DataTableWidget
from .events import VCdbEventType
from .export import DataExporter
from .filter_panel import FilterPanelManager


class VCdbExplorerWidget(QWidget):
    """Main widget for the VCdb Explorer plugin."""

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus_manager: EventBusManager,
            concurrency_manager: ConcurrencyManager,
            task_manager: TaskManager,
            logger: logging.Logger,
            export_settings: Dict[str, Any],
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the widget.

        Args:
            database_handler: Handler for database operations
            event_bus_manager: Manager for event bus operations
            concurrency_manager: Manager for concurrency operations
            task_manager: Manager for task manager operations
            logger: Logger instance
            export_settings: Export configuration settings
            parent: Parent widget
        """
        super().__init__(parent)

        self._database_handler = database_handler
        self._event_bus_manager = event_bus_manager
        self._concurrency_manager = concurrency_manager
        self._task_manager = task_manager
        self._logger = logger
        self._export_settings = export_settings

        self._query_running = False

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Title
        title = QLabel('VCdb Explorer')
        title.setStyleSheet('font-weight: bold; font-size: 18px;')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(title)

        # Create export handler
        self._exporter = DataExporter(logger)

        # Subscribe to events
        asyncio.create_task(self._subscribe_to_events())

        # Create UI components
        self._create_ui_components()

        # Connect signals
        self._connect_signals()

    def closeEvent(self, event: Any) -> None:
        """Handle the close event by unsubscribing from events."""
        self._event_bus_manager.unsubscribe(subscriber_id='vcdb_explorer_widget')

    async def _subscribe_to_events(self) -> None:
        """Subscribe to filters refreshed events."""
        await self._event_bus_manager.subscribe(
            event_type=VCdbEventType.filters_refreshed(),
            callback=self._on_filters_refreshed,
            subscriber_id='vcdb_explorer_widget'
        )

    def _create_ui_components(self) -> None:
        """Create the UI components."""
        # Main splitter for filter panel and data table
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Filter panel section
        self._filter_panel_manager = FilterPanelManager(
            self._database_handler,
            self._event_bus_manager,
            self._logger,
            max_panels=self._export_settings.get('max_filter_panels', 5)
        )

        filter_section = QWidget()
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(self._filter_panel_manager)

        # Query button
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
            self._event_bus_manager,
            self._logger,
            self
        )

        # Add to splitter
        self._main_splitter.addWidget(filter_section)
        self._main_splitter.addWidget(self._data_table)
        self._main_splitter.setSizes([400, 600])

        self._layout.addWidget(self._main_splitter)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._filter_panel_manager.filtersChanged.connect(self._on_filters_changed)
        self._data_table.queryStarted.connect(self._on_query_started)
        self._data_table.queryFinished.connect(self._on_query_finished)

    @Slot()
    def _on_filters_changed(self) -> None:
        """Handle changes to filters."""
        self._logger.debug('Filters changed in UI')

    @Slot()
    def _on_query_started(self) -> None:
        """Handle query started signal."""
        self._query_running = True
        self._update_ui_state()

    @Slot()
    def _on_query_finished(self) -> None:
        """Handle query finished signal."""
        self._query_running = False
        self._update_ui_state()

    def _update_ui_state(self) -> None:
        """Update UI state based on query status."""
        self._run_query_btn.setEnabled(not self._query_running)

    async def _on_filters_refreshed(self, event: Any) -> None:
        """
        Handle filters refreshed event.

        Args:
            event: Filters refreshed event
        """
        # Ensure we're on the main thread
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._on_filters_refreshed(event))
            )
            return

        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})

        self._logger.debug(f'Filters refreshed event received for panel {panel_id}')

        # Update filter values
        await self._filter_panel_manager.update_filter_values(panel_id, filter_values)

    @Slot()
    def _execute_query(self) -> None:
        """Execute a query with the current filters."""
        if self._query_running:
            self._logger.warning('Query already running, ignoring request')
            return

        # Get filters from all panels
        filter_panels = self._filter_panel_manager.get_all_filters()
        self._logger.debug(f'Collected filter panels: {filter_panels}')

        # Confirm if no filters are set
        if not any((panel for panel in filter_panels if panel)):
            if QMessageBox.question(
                    self,
                    'No Filters',
                    "You haven't set any filters. This could return a large number of results. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
            ) != QMessageBox.StandardButton.Yes:
                return

        # Execute the query
        asyncio.create_task(self._execute_query_async(filter_panels))

    @Slot()
    def _cancel_query(self) -> None:
        """Cancel the current query."""
        if not self._query_running:
            return

        self._logger.debug('Cancelling query')
        asyncio.create_task(self._database_handler.cancel_query(self._data_table.get_callback_id()))

    async def _execute_query_async(self, filter_panels: List[Dict[str, List[int]]]) -> None:
        """
        Execute a query asynchronously.

        Args:
            filter_panels: List of filter dictionaries from multiple panels
        """
        try:
            self._logger.debug('Execute async query triggered')
            self._data_table.execute_query(filter_panels)
        except Exception as e:
            self._logger.error(f'Query execution error: {str(e)}')

            # Ensure error messages are shown in the main thread
            if not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(
                    lambda: QMessageBox.critical(self, 'Query Error', f'Error executing query: {str(e)}')
                )
            else:
                QMessageBox.critical(self, 'Query Error', f'Error executing query: {str(e)}')

            self._query_running = False
            self._update_ui_state()

    @Slot()
    def refresh_filters(self) -> None:
        """Refresh all filters."""
        if hasattr(self, '_filter_panel_manager'):
            self._filter_panel_manager.refresh_all_panels()
            QMessageBox.information(self, 'Filters Refreshed', 'All filters have been refreshed.')


class VCdbExplorerPlugin(BasePlugin):
    """VCdb Explorer plugin for querying and exploring the Vehicle Component Database."""

    name = 'vcdb_explorer'
    version = '1.0.0'
    description = 'Advanced query tool for exploring Vehicle Component Database'
    author = 'Qorzen Developer'
    display_name = 'VCdb Explorer'
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()

        self._main_widget: Optional[VCdbExplorerWidget] = None
        self._database_handler: Optional[DatabaseHandler] = None
        self._logger: Optional[logging.Logger] = None
        self._event_bus_manager: Optional[EventBusManager] = None
        self._concurrency_manager: Optional[ConcurrencyManager] = None
        self._task_manager: Optional[TaskManager] = None

        self._db_config: Dict[str, Any] = {}
        self._ui_config: Dict[str, Any] = {}
        self._export_config: Dict[str, Any] = {}

        self._connection_registered = False
        self._icon_path: Optional[str] = None
        self._ui_components_created = False

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin.

        Args:
            application_core: Core application instance
            **kwargs: Additional initialization parameters
        """
        await super().initialize(application_core, **kwargs)

        # Set up logger
        self._logger = self._logger or logging.getLogger(self.name)
        self._logger.info(f'Initializing {self.name} plugin')

        # Get required managers
        self._concurrency_manager = self._concurrency_manager or application_core.get_manager('concurrency_manager')
        self._event_bus_manager = self._event_bus_manager or application_core.get_manager('event_bus_manager')
        self._task_manager = self._task_manager or application_core.get_manager('task_manager')
        database_manager = kwargs.get('database_manager') or application_core.get_manager('database_manager')

        # Load configuration
        await self._load_config()

        # Find plugin directory and icon
        plugin_dir = await self._find_plugin_directory()
        if plugin_dir:
            icon_path = os.path.join(plugin_dir, 'resources', 'icon.png')
            if os.path.exists(icon_path):
                self._icon_path = icon_path
                self._logger.debug(f'Found plugin icon at: {icon_path}')

        # Initialize database handler
        if not database_manager:
            self._logger.error('DatabaseManager is required but was not provided')
            self._database_handler = None
            self._connection_registered = False
        else:
            try:
                self._database_handler = DatabaseHandler(
                    database_manager,
                    self._event_bus_manager,
                    self._task_manager,
                    self._concurrency_manager,
                    self._logger
                )

                await self._database_handler.initialize()

                await self._database_handler.configure(
                    self._db_config.get('host', 'localhost'),
                    self._db_config.get('port', 5432),
                    self._db_config.get('database', 'vcdb'),
                    self._db_config.get('user', 'postgres'),
                    self._db_config.get('password', '')
                )

                self._connection_registered = True
                self._logger.info('Database handler initialized and configured successfully')

            except Exception as e:
                self._logger.error(f'Failed to initialize database connection: {str(e)}')
                self._database_handler = None
                self._connection_registered = False

        # Subscribe to log messages
        await self._event_bus_manager.subscribe(
            event_type='vcdb_explorer:log_message',
            callback=self._on_log_message,
            subscriber_id='vcdb_explorer_plugin'
        )

        # Set plugin state
        await set_plugin_state(self.name, PluginLifecycleState.INITIALIZED)
        self._logger.info(f'{self.name} plugin initialized successfully')

    async def _find_plugin_directory(self) -> Optional[str]:
        """
        Find the plugin directory.

        Returns:
            Path to the plugin directory, or None if not found
        """
        import inspect

        try:
            module_path = inspect.getmodule(self).__file__
            if module_path:
                return os.path.dirname(os.path.abspath(module_path))
        except (AttributeError, TypeError):
            pass

        return None

    async def _load_config(self) -> None:
        """Load plugin configuration."""
        if not self._config_manager:
            return

        # Database configuration
        self._db_config = {
            'host': await self._config_manager.get(f'plugins.{self.name}.database.host', 'localhost'),
            'port': await self._config_manager.get(f'plugins.{self.name}.database.port', 5432),
            'database': await self._config_manager.get(f'plugins.{self.name}.database.name', 'vcdb'),
            'user': await self._config_manager.get(f'plugins.{self.name}.database.user', 'postgres'),
            'password': await self._config_manager.get(f'plugins.{self.name}.database.password', '')
        }

        # UI configuration
        self._ui_config = {
            'max_filter_panels': await self._config_manager.get(f'plugins.{self.name}.ui.max_filter_panels', 5),
            'default_page_size': await self._config_manager.get(f'plugins.{self.name}.ui.default_page_size', 100)
        }

        # Export configuration
        self._export_config = {
            'max_rows': await self._config_manager.get(f'plugins.{self.name}.export.max_rows', 0)
        }

        if self._logger:
            self._logger.debug('Configuration loaded')

    async def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """
        Set up UI components when the UI is ready.

        Args:
            ui_integration: UI integration instance
        """
        if self._logger:
            self._logger.info('Setting up UI components')

        # Check for recursive calls
        current_state = await get_plugin_state(self.name)
        if current_state == PluginLifecycleState.UI_READY:
            self._logger.debug('UI setup already in progress, avoiding recursive call')
            return

        # Ensure we're on the main thread
        if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
            self._logger.debug('on_ui_ready called from non-main thread, delegating to main thread')
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self.on_ui_ready(ui_integration))
            )
            return

        # Check if UI components already created
        if hasattr(self, '_ui_components_created') and self._ui_components_created:
            self._logger.debug('UI components already created, skipping duplicate creation')
            await signal_ui_ready(self.name)
            return

        try:
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)

            # Add menu items
            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu='VCdb',
                title='Run Query',
                callback=lambda: asyncio.create_task(self._run_query())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu='VCdb',
                title='Refresh Filters',
                callback=lambda: asyncio.create_task(self._refresh_filters())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu='VCdb',
                title='Documentation',
                callback=lambda: asyncio.create_task(self._open_documentation())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu='VCdb',
                title='Configuration',
                callback=lambda: asyncio.create_task(self._open_configuration())
            )

            # Create main widget
            if not self._database_handler or not getattr(self._database_handler, '_initialized', False):
                self._main_widget = await self._create_error_widget()
                self._logger.warning('Added error widget due to database connection failure')
            else:
                try:
                    if not self._main_widget:
                        self._main_widget = VCdbExplorerWidget(
                            self._database_handler,
                            self._event_bus_manager,
                            self._concurrency_manager,
                            self._task_manager,
                            self._logger,
                            self._export_config,
                            None
                        )

                    # Add page to UI
                    await ui_integration.add_page(
                        plugin_id=self.plugin_id,
                        page_component=self._main_widget,
                        icon=self._icon_path,
                        title=self.display_name or self.name
                    )

                    if self._logger:
                        self._logger.info('UI components set up successfully')

                except Exception as e:
                    if self._logger:
                        self._logger.error(f'Failed to set up UI components: {str(e)}')
                    self._main_widget = await self._create_error_widget(str(e))

            self._ui_components_created = True

            # Signal completion
            await set_plugin_state(self.name, PluginLifecycleState.ACTIVE)
            await signal_ui_ready(self.name)

        except Exception as e:
            self._logger.error(f'Error setting up UI: {str(e)}')
            await set_plugin_state(self.name, PluginLifecycleState.FAILED)

    async def setup_ui(self, ui_integration: Any) -> None:
        """
        Set up UI components.

        Args:
            ui_integration: UI integration instance
        """
        if self._logger:
            self._logger.info('setup_ui method called')
        await self.on_ui_ready(ui_integration)

    async def _create_error_widget(self, error_message: Optional[str] = None) -> QWidget:
        """
        Create a widget to display error information.

        Args:
            error_message: Optional error message

        Returns:
            Error widget
        """
        error_widget = QWidget()
        error_layout = QVBoxLayout()
        error_widget.setLayout(error_layout)

        # Error title
        error_label = QLabel('Database Connection Error')
        error_label.setStyleSheet('font-weight: bold; color: red; font-size: 16px;')
        error_layout.addWidget(error_label)

        # Error message
        message_text = error_message or 'Could not connect to the VCdb database. Check your configuration or database server status.'
        message = QLabel(message_text)
        message.setWordWrap(True)
        error_layout.addWidget(message)

        # Configuration button
        button_layout = QHBoxLayout()
        config_btn = QPushButton('Open Configuration')
        config_btn.clicked.connect(lambda: asyncio.create_task(self._open_configuration()))
        button_layout.addWidget(config_btn)

        error_layout.addLayout(button_layout)
        error_layout.addStretch()

        return error_widget

    async def _on_log_message(self, event: Any) -> None:
        """
        Handle log message events.

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

    async def _refresh_filters(self) -> None:
        """Refresh all filters."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._refresh_filters())
            )
            return

        if self._main_widget and hasattr(self._main_widget, 'refresh_filters'):
            self._main_widget.refresh_filters()

    async def _run_query(self) -> None:
        """Run a query with current filters."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._run_query())
            )
            return

        if self._main_widget and hasattr(self._main_widget, '_execute_query'):
            self._main_widget._execute_query()

    async def _open_documentation(self) -> None:
        """Show documentation information."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_documentation())
            )
            return

        if self._logger:
            self._logger.info('Documentation requested')

        QMessageBox.information(
            None,
            'Documentation',
            'The VCdb Explorer plugin provides an interface to query and explore the Vehicle Component Database.\n\n'
            'For more information, please refer to the online documentation.'
        )

    async def _open_configuration(self) -> None:
        """Show configuration information."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_configuration())
            )
            return

        QMessageBox.information(
            None,
            'Configuration',
            'To configure the VCdb Explorer plugin, edit the configuration file and restart the application.'
        )

    def get_main_widget(self) -> Optional[QWidget]:
        """
        Get the main widget.

        Returns:
            Main widget or None
        """
        return self._main_widget

    def get_icon(self) -> Optional[str]:
        """
        Get the icon path.

        Returns:
            Icon path or None
        """
        return self._icon_path

    async def shutdown(self) -> None:
        """Shut down the plugin."""
        if self._logger:
            self._logger.info(f'Shutting down {self.name} plugin')

        await set_plugin_state(self.name, PluginLifecycleState.DISABLING)

        # Unsubscribe from events
        if self._event_bus_manager:
            await self._event_bus_manager.unsubscribe(subscriber_id='vcdb_explorer_plugin')

        # Shut down database handler
        if self._database_handler and self._connection_registered:
            try:
                await self._database_handler.shutdown()
                self._connection_registered = False
            except Exception as e:
                if self._logger:
                    self._logger.error(f'Error shutting down database handler: {str(e)}')

        # Clean up resources
        self._main_widget = None

        # Complete shutdown
        await super().shutdown()
        await set_plugin_state(self.name, PluginLifecycleState.INACTIVE)

        if self._logger:
            self._logger.info(f'{self.name} plugin shutdown complete')