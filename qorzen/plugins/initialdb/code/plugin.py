from __future__ import annotations

"""
InitialDB Plugin for Qorzen framework.

This plugin provides access to vehicle component database information,
allowing users to query and export vehicle parts and specifications.
"""

import logging
from typing import Any, Dict, List, Optional, Union, cast

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget, QMenu
from PySide6.QtGui import QAction

from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, TabComponent
from qorzen.core.config_manager import ConfigManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.file_manager import FileManager
from qorzen.core.thread_manager import ThreadManager
from qorzen.plugin_system.interface import BasePlugin


# Import these conditionally in the methods that use them
# to avoid import errors if modules are missing
# from .services.vehicle_service import VehicleService
# from .services.export_service import ExportService
# from .routes.api import register_api_routes
# from .config.settings import DEFAULT_CONNECTION_STRING


class InitialDBTab(TabComponent):
    """Tab component for the InitialDB plugin."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the InitialDB tab.

        Args:
            parent: The parent widget.
        """
        self._widget = QWidget(parent)
        self._layout = QVBoxLayout(self._widget)
        self._layout.addWidget(QLabel('This is the InitialDB plugin tab'))

    def get_widget(self) -> QWidget:
        """Get the widget for this tab.

        Returns:
            The widget for this tab.
        """
        return self._widget

    def on_tab_selected(self) -> None:
        """Called when this tab is selected."""
        pass

    def on_tab_deselected(self) -> None:
        """Called when this tab is deselected."""
        pass


class InitialDBPlugin(BasePlugin):
    """Vehicle Component Database Plugin."""

    name = 'initialdb'
    version = '0.2.0'
    description = 'Vehicle Component Database Plugin'
    author = 'Ryan Serra'
    dependencies = []

    def __init__(self) -> None:
        """Initialize the InitialDB plugin."""
        super().__init__()
        self._event_bus: Optional[EventBusManager] = None
        self._logger: Optional[logging.Logger] = None
        self._config: Optional[ConfigManager] = None
        self._file_manager: Optional[FileManager] = None
        self._thread_manager: Optional[ThreadManager] = None
        self._db_manager: Optional[Any] = None
        self._api_manager: Optional[Any] = None
        self._vehicle_service: Optional[Any] = None
        self._export_service: Optional[Any] = None

        self._tab: Optional[InitialDBTab] = None
        self._tab_index: Optional[int] = None

        # Keep strong references to Qt objects
        self._menu_items: List[QAction] = []
        self._plugin_menu: Optional[QMenu] = None
        self._tools_menu: Optional[QMenu] = None

        self._initialized = False

    def initialize(
            self,
            event_bus: Any,
            logger_provider: Any,
            config_provider: Any,
            file_manager: Any,
            thread_manager: Any,
            **kwargs: Any
    ) -> None:
        """Initialize the plugin with required components.

        Args:
            event_bus: The event bus.
            logger_provider: The logger provider.
            config_provider: The configuration provider.
            file_manager: The file manager.
            thread_manager: The thread manager.
            **kwargs: Additional components.
        """
        self._event_bus = cast(EventBusManager, event_bus)
        self._logger = logger_provider.get_logger(self.name)
        self._config = cast(ConfigManager, config_provider)
        self._file_manager = cast(FileManager, file_manager)
        self._thread_manager = cast(ThreadManager, thread_manager)
        self._db_manager = kwargs.get('database_manager')
        self._api_manager = kwargs.get('api_manager')

        if not self._db_manager:
            self._logger.error('Database manager not available - plugin cannot function')
            return

        if not self._api_manager:
            self._logger.warning('API manager not available - API routes will not be registered')

        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(
                    self.name, directory_type='plugin_data'
                )
                self._file_manager.ensure_directory(plugin_data_dir.as_posix())
                self._logger.debug(f'Plugin data directory: {plugin_data_dir}')
            except Exception as e:
                self._logger.warning(f'Failed to create plugin data directory: {str(e)}')

        self._logger.info(f'Initializing {self.name} v{self.version} plugin')

        # Load settings
        try:
            self._load_settings()
        except Exception as e:
            self._logger.error(f'Error loading settings: {str(e)}')

        try:
            # Import services dynamically to avoid import errors at module level
            from .services.vehicle_service import VehicleService
            from .services.export_service import ExportService
            from .routes.api import register_api_routes

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

            if self._api_manager:
                register_api_routes(
                    api_manager=self._api_manager,
                    vehicle_service=self._vehicle_service,
                    export_service=self._export_service,
                    logger=self._logger
                )
                self._logger.info('API routes registered')

            self._subscribe_to_events()
            self._initialized = True
            self._logger.info(f'{self.name} plugin initialized')

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
        """Load plugin settings."""
        try:
            from .config.settings import DEFAULT_CONNECTION_STRING

            conn_str = self._config.get(f'plugins.{self.name}.connection_string', None)
            if conn_str is None:
                self._config.set(f'plugins.{self.name}.connection_string', DEFAULT_CONNECTION_STRING)
                self._logger.info(f'Set default connection string: {DEFAULT_CONNECTION_STRING}')

        except Exception as e:
            self._logger.error(f'Error loading settings: {str(e)}')
            # Use a fallback connection string if import fails
            DEFAULT_CONN_STR = 'sqlite:///data/initialdb/vehicles.db'
            conn_str = self._config.get(f'plugins.{self.name}.connection_string', None)
            if conn_str is None:
                self._config.set(f'plugins.{self.name}.connection_string', DEFAULT_CONN_STR)
                self._logger.info(f'Set fallback connection string: {DEFAULT_CONN_STR}')

    def _subscribe_to_events(self) -> None:
        """Subscribe to events."""
        if not self._event_bus:
            return

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
            event: The event.
        """
        if not self._initialized:
            return

        self._logger.info('System started event received')

        if self._thread_manager:
            self._thread_manager.submit_task(
                func=self._validate_database,
                name=f'{self.name}_validate_db',
                submitter=self.name
            )

    def _validate_database(self) -> None:
        """Validate the database."""
        if not self._initialized or not self._vehicle_service:
            return

        try:
            result = self._vehicle_service.validate_database()
            if result:
                self._logger.info('Database validation successful')
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
        """Handle configuration change event.

        Args:
            event: The event.
        """
        if not self._initialized:
            return

        config_path = event.payload.get('path', '')
        if not config_path.startswith(f'plugins.{self.name}'):
            return

        self._logger.info(f'Configuration changed: {config_path}')
        plugin_config = self._config.get(f'plugins.{self.name}', {})

        if self._vehicle_service:
            self._vehicle_service.update_config(plugin_config)

        if self._export_service:
            self._export_service.update_config(plugin_config)

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Set up UI components when UI is ready.

        Args:
            ui_integration: The UI integration.
        """
        try:
            self._logger.debug('Setting up UI components')

            # Create and add tab
            self._tab = InitialDBTab()
            self._tab_index = ui_integration.add_tab(
                plugin_id=self.name,
                tab=self._tab,
                title=self.name.capitalize()
            )

            # Add menu items safely with exception handling for each step
            try:
                # Find or create Tools menu
                self._tools_menu = ui_integration.find_menu('&Tools')
                if not self._tools_menu:
                    self._tools_menu = ui_integration.add_menu(
                        plugin_id=self.name,
                        title='&Tools'
                    )

                # Create plugin submenu
                if self._tools_menu:
                    self._plugin_menu = ui_integration.add_menu(
                        plugin_id=self.name,
                        title=self.name.capitalize(),
                        parent_menu=self._tools_menu
                    )

                    # Add actions to the plugin menu
                    if self._plugin_menu:
                        # Add "Refresh Database" action
                        action1 = ui_integration.add_menu_action(
                            plugin_id=self.name,
                            menu=self._plugin_menu,
                            text='Refresh Database',
                            callback=self._refresh_database_connection
                        )
                        self._menu_items.append(action1)

                        # Add "Connection Settings" action
                        action2 = ui_integration.add_menu_action(
                            plugin_id=self.name,
                            menu=self._plugin_menu,
                            text='Connection Settings',
                            callback=self._show_connection_settings
                        )
                        self._menu_items.append(action2)

                        self._logger.debug('Added menu items to Tools menu')

            except Exception as e:
                self._logger.error(f'Error adding menu items: {str(e)}')

            # Publish UI added event
            if self._event_bus:
                self._event_bus.publish(
                    event_type=f'{self.name}/ui_added',
                    source=self.name,
                    payload={'tab_index': self._tab_index}
                )

        except Exception as e:
            self._logger.error(f'Error setting up UI components: {str(e)}')

    def _refresh_database_connection(self) -> None:
        """Refresh the database connection."""
        self._logger.info('Refreshing database connection')
        if self._thread_manager and self._vehicle_service:
            self._thread_manager.submit_task(
                func=self._validate_database,
                name=f'{self.name}_validate_db',
                submitter=self.name
            )

    def _show_connection_settings(self) -> None:
        """Show the connection settings dialog."""
        self._logger.info('Showing connection settings')
        # Implementation would go here

    def shutdown(self) -> None:
        """Shutdown the plugin and clean up resources."""
        if not self._initialized:
            return

        self._logger.info(f'Shutting down {self.name} plugin')

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f'{self.name}_system_started')
            self._event_bus.unsubscribe(f'{self.name}_config_changed')

        # Shutdown services
        if self._vehicle_service:
            self._vehicle_service.shutdown()

        if self._export_service:
            self._export_service.shutdown()

        # Clear UI references
        self._menu_items.clear()
        self._plugin_menu = None
        self._tools_menu = None

        self._initialized = False
        self._logger.info(f'{self.name} plugin shut down successfully')

    def get_vehicle_service(self) -> Optional[Any]:
        """Get the vehicle service.

        Returns:
            The vehicle service, or None if not initialized.
        """
        return self._vehicle_service if self._initialized else None

    def get_export_service(self) -> Optional[Any]:
        """Get the export service.

        Returns:
            The export service, or None if not initialized.
        """
        return self._export_service if self._initialized else None

    def status(self) -> Dict[str, Any]:
        """Get the plugin status.

        Returns:
            The plugin status dictionary.
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