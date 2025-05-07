from __future__ import annotations

from qorzen.plugin_system.interface import BasePlugin

"""
InitialDB Plugin for Qorzen framework.

This plugin provides access to vehicle component database information,
allowing users to query and export vehicle parts and specifications.
"""
import logging
from typing import Any, Dict, List, Optional, Union, cast

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget

from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, TabComponent
from qorzen.core.config_manager import ConfigManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.file_manager import FileManager
from qorzen.core.thread_manager import ThreadManager

from .services.vehicle_service import VehicleService
from .services.export_service import ExportService
from .routes.api import register_api_routes
from .config.settings import DEFAULT_CONNECTION_STRING


class InitialDBTab(TabComponent):
    """Tab component for the InitialDB plugin."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the tab component.

        Args:
            parent: Optional parent widget
        """
        self._widget = QWidget(parent)
        self._layout = QVBoxLayout(self._widget)
        self._layout.addWidget(QLabel("This is the InitialDB plugin tab"))

        # Add more UI components as needed

    def get_widget(self) -> QWidget:
        """Get the underlying widget.

        Returns:
            The tab widget
        """
        return self._widget

    def on_tab_selected(self) -> None:
        """Called when the tab is selected."""
        # Handle tab selection if needed
        pass

    def on_tab_deselected(self) -> None:
        """Called when the tab is deselected."""
        # Handle tab deselection if needed
        pass


class InitialDBPlugin(BasePlugin):
    """Vehicle Component Database Plugin.

    This plugin provides access to vehicle component database information,
    allowing users to query and export vehicle parts and specifications.
    """

    # Signal to handle UI ready event on the main thread
    ui_ready_signal = Signal(object)

    # Plugin metadata
    name = 'initialdb'
    version = '0.2.0'
    description = 'Vehicle Component Database Plugin'
    author = 'Ryan Serra'
    dependencies = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()

        # Core managers
        self._event_bus: Optional[EventBusManager] = None
        self._logger: Optional[logging.Logger] = None
        self._config: Optional[ConfigManager] = None
        self._file_manager: Optional[FileManager] = None
        self._thread_manager: Optional[ThreadManager] = None
        self._db_manager: Optional[Any] = None
        self._api_manager: Optional[Any] = None

        # Plugin services
        self._vehicle_service: Optional[VehicleService] = None
        self._export_service: Optional[ExportService] = None

        # UI components
        self._tab: Optional[InitialDBTab] = None
        self._tab_index: Optional[int] = None
        self._menu_items: List[Any] = []

        # State
        self._initialized = False

        # Connect signal
        self.ui_ready_signal.connect(self._handle_ui_ready_on_main_thread)

    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any,
                   file_manager: Any, thread_manager: Any, **kwargs: Any) -> None:
        """Initialize the plugin with the provided managers.

        Args:
            event_bus: Event bus manager for subscribing to and publishing events
            logger_provider: Logger provider for creating plugin-specific loggers
            config_provider: Configuration provider for accessing application config
            file_manager: File manager for file operations
            thread_manager: Thread manager for background tasks
            **kwargs: Additional managers
        """
        # Store core managers
        self._event_bus = cast(EventBusManager, event_bus)
        self._logger = logger_provider.get_logger(self.name)
        self._config = cast(ConfigManager, config_provider)
        self._file_manager = cast(FileManager, file_manager)
        self._thread_manager = cast(ThreadManager, thread_manager)

        # Get additional managers
        self._db_manager = kwargs.get('database_manager')
        self._api_manager = kwargs.get('api_manager')

        # Validate required managers
        if not self._db_manager:
            self._logger.error('Database manager not available - plugin cannot function')
            return

        if not self._api_manager:
            self._logger.warning('API manager not available - API routes will not be registered')

        # Create plugin data directory
        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type='plugin_data')
                self._file_manager.ensure_directory(plugin_data_dir.as_posix())
                self._logger.debug(f'Plugin data directory: {plugin_data_dir}')
            except Exception as e:
                self._logger.warning(f'Failed to create plugin data directory: {str(e)}')

        # Log initialization
        self._logger.info(f'Initializing {self.name} v{self.version} plugin')

        # Load settings
        self._load_settings()

        try:
            # Initialize services
            self._vehicle_service = VehicleService(
                db_manager=self._db_manager,
                logger=self._logger,
                event_bus=self._event_bus,
                thread_manager=self._thread_manager,
                config=self._config
            )

            self._export_service = ExportService(
                file_manager=self._file_manager,
                logger=self._logger,
                vehicle_service=self._vehicle_service,
                config=self._config
            )

            # Register API routes
            if self._api_manager:
                register_api_routes(
                    api_manager=self._api_manager,
                    vehicle_service=self._vehicle_service,
                    export_service=self._export_service,
                    logger=self._logger
                )
                self._logger.info('API routes registered')

            # Subscribe to events
            self._subscribe_to_events()

            # Mark as initialized
            self._initialized = True
            self._logger.info(f'{self.name} plugin initialized')

            # Publish initialization event
            self._event_bus.publish(
                event_type=EventType.PLUGIN_INITIALIZED.value,
                source=self.name,
                payload={
                    'plugin_name': self.name,
                    'version': self.version,
                    'has_ui': True
                }
            )

        except Exception as e:
            self._logger.error(f'Failed to initialize plugin: {str(e)}', exc_info=True)

    def _load_settings(self) -> None:
        """Load plugin settings from configuration."""
        try:
            conn_str = self._config.get(f'plugins.{self.name}.connection_string', None)
            if conn_str is None:
                self._config.set(f'plugins.{self.name}.connection_string', DEFAULT_CONNECTION_STRING)
                self._logger.info(f'Set default connection string: {DEFAULT_CONNECTION_STRING}')
        except Exception as e:
            self._logger.error(f'Error loading settings: {str(e)}')

    def _subscribe_to_events(self) -> None:
        """Subscribe to system events."""
        if not self._event_bus:
            return

        # Subscribe to system events
        self._event_bus.subscribe(
            event_type=EventType.SYSTEM_STARTED.value,
            callback=self._on_system_started,
            subscriber_id=f'{self.name}_system_started'
        )

        self._event_bus.subscribe(
            event_type=EventType.CONFIG_CHANGED.value,
            callback=self._on_config_changed,
            subscriber_id=f'{self.name}_config_changed'
        )

    def _on_system_started(self, event: Event) -> None:
        """Handle system started event.

        Args:
            event: The event object
        """
        if not self._initialized:
            return

        self._logger.info('System started event received')

        # Validate database in a background thread
        if self._thread_manager:
            self._thread_manager.submit_task(
                func=self._validate_database,
                name=f'{self.name}_validate_db',
                submitter=self.name
            )

    def _validate_database(self) -> None:
        """Validate database connection and schema."""
        if not self._initialized or not self._vehicle_service:
            return

        try:
            result = self._vehicle_service.validate_database()
            if result:
                self._logger.info('Database validation successful')

                # Publish database ready event
                if self._event_bus:
                    self._event_bus.publish(
                        event_type=f'{self.name}/database_ready',
                        source=self.name,
                        payload={'status': 'ready'}
                    )
            else:
                self._logger.error('Database validation failed')
        except Exception as e:
            self._logger.error(f'Database validation error: {str(e)}', exc_info=True)

    def _on_config_changed(self, event: Event) -> None:
        """Handle configuration changed event.

        Args:
            event: The event object
        """
        if not self._initialized:
            return

        # Get the changed configuration path
        config_path = event.payload.get('path', '')

        # Only process changes to this plugin's configuration
        if not config_path.startswith(f'plugins.{self.name}'):
            return

        self._logger.info(f'Configuration changed: {config_path}')

        # Get the updated plugin configuration
        plugin_config = self._config.get(f'plugins.{self.name}', {})

        # Update services with new configuration
        if self._vehicle_service:
            self._vehicle_service.update_config(plugin_config)

        if self._export_service:
            self._export_service.update_config(plugin_config)

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Set up UI components when UI is ready.

        This method is called by the plugin system when the UI is ready.

        Args:
            ui_integration: UI integration interface
        """
        try:
            self._logger.debug('Setting up UI components')

            # Add tab
            self._tab = InitialDBTab()
            self._tab_index = ui_integration.add_tab(
                plugin_id=self.name,
                tab=self._tab,
                title=self.name.capitalize()
            )

            # Add menu items
            try:
                # Find or create Tools menu
                tools_menu = ui_integration.find_menu('&Tools')
                if not tools_menu:
                    tools_menu = ui_integration.add_menu(
                        plugin_id=self.name,
                        title='&Tools'
                    )

                # Add plugin-specific menu
                plugin_menu = ui_integration.add_menu(
                    plugin_id=self.name,
                    title=self.name.capitalize(),
                    parent_menu=tools_menu
                )

                # Add actions
                action1 = ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=plugin_menu,
                    text='Refresh Database',
                    callback=self._refresh_database_connection
                )

                action2 = ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=plugin_menu,
                    text='Connection Settings',
                    callback=self._show_connection_settings
                )

                # Store references to menu items
                self._menu_items = [action1, action2]

                self._logger.debug('Added menu items to Tools menu')
            except Exception as e:
                self._logger.error(f'Error adding menu items: {str(e)}')

            # Publish event that UI components have been added
            if self._event_bus:
                self._event_bus.publish(
                    event_type=f'{self.name}/ui_added',
                    source=self.name,
                    payload={'tab_index': self._tab_index}
                )

        except Exception as e:
            self._logger.error(f'Error setting up UI components: {str(e)}')

    @Slot(object)
    def _handle_ui_ready_on_main_thread(self, main_window: Any) -> None:
        """Legacy method to handle UI ready events on the main thread.

        This is maintained for backward compatibility.

        Args:
            main_window: The main window instance
        """
        # This is now just a fallback for backward compatibility
        pass

    def _refresh_database_connection(self) -> None:
        """Refresh the database connection."""
        self._logger.info('Refreshing database connection')

        # Run database validation in a background thread
        if self._thread_manager and self._vehicle_service:
            self._thread_manager.submit_task(
                func=self._validate_database,
                name=f'{self.name}_validate_db',
                submitter=self.name
            )

    def _show_connection_settings(self) -> None:
        """Show connection settings dialog."""
        self._logger.info('Showing connection settings')
        # Implement settings dialog

    def shutdown(self) -> None:
        """Shut down the plugin."""
        if not self._initialized:
            return

        self._logger.info(f'Shutting down {self.name} plugin')

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f'{self.name}_system_started')
            self._event_bus.unsubscribe(f'{self.name}_config_changed')

        # Shut down services
        if self._vehicle_service:
            self._vehicle_service.shutdown()

        if self._export_service:
            self._export_service.shutdown()

        # UI components are cleaned up by the LifecycleManager via cleanup_ui()

        # Mark as not initialized
        self._initialized = False
        self._logger.info(f'{self.name} plugin shut down successfully')

    def get_vehicle_service(self) -> Optional[VehicleService]:
        """Get the vehicle service.

        Returns:
            Vehicle service instance or None if not initialized
        """
        return self._vehicle_service if self._initialized else None

    def get_export_service(self) -> Optional[ExportService]:
        """Get the export service.

        Returns:
            Export service instance or None if not initialized
        """
        return self._export_service if self._initialized else None

    def status(self) -> Dict[str, Any]:
        """Get plugin status.

        Returns:
            Plugin status information
        """
        return {
            'name': self.name,
            'version': self.version,
            'initialized': self._initialized,
            'has_ui': True,
            'ui_components': {
                'tab_added': self._tab is not None,
                'tab_index': self._tab_index,
                'menu_items_count': len(self._menu_items)
            },
            'services': {
                'vehicle_service': self._vehicle_service is not None,
                'export_service': self._export_service is not None
            },
            'subscriptions': ['system/started', 'config/changed']
        }