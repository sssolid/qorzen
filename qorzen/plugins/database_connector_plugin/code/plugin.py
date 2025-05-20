#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Main plugin module for the Database Connector Plugin.

This module provides the main plugin class that integrates all components
of the Database Connector Plugin with the Qorzen framework.
"""

import asyncio
import json
import os
import logging
import datetime
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QMessageBox

from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from qorzen.utils.exceptions import PluginError, DatabaseError

from .models import (
    BaseConnectionConfig,
    AS400ConnectionConfig,
    ODBCConnectionConfig,
    ConnectionType,
    PluginSettings,
    SavedQuery,
    FieldMapping,
    ValidationRule,
    QueryResult
)

from .connectors import (
    BaseDatabaseConnector,
    get_connector_for_config
)

from .ui.main_tab import DatabaseConnectorTab

from .utils.mapping import apply_mapping_to_results
from .utils.history import HistoryManager
from .utils.validation import ValidationEngine


class DatabaseConnectorPlugin(BasePlugin):
    """Main plugin class for the Database Connector Plugin."""

    name = "database_connector_plugin"
    version = "1.0.0"
    description = "Connect and query various databases with field mapping and validation capabilities"
    author = "Qorzen Team"
    display_name = "Database Connector"
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()

        # Core components
        self._logger: Optional[logging.Logger] = None
        self._event_bus_manager = None
        self._config_manager = None
        self._task_manager = None
        self._database_manager = None
        self._concurrency_manager = None
        self._security_manager = None
        self._file_manager = None

        # Plugin state
        self._initialized = False
        self._connections: Dict[str, BaseConnectionConfig] = {}
        self._active_connectors: Dict[str, BaseDatabaseConnector] = {}
        self._connector_locks: Dict[str, asyncio.Lock] = {}
        self._saved_queries: Dict[str, SavedQuery] = {}
        self._field_mappings: Dict[str, FieldMapping] = {}
        self._settings: Optional[PluginSettings] = None

        # UI components
        self._main_widget: Optional[DatabaseConnectorTab] = None
        self._icon_path: Optional[str] = None

        # Utility managers
        self._history_manager: Optional[HistoryManager] = None
        self._validation_engine: Optional[ValidationEngine] = None

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin.

        Args:
            application_core: Application core instance
            **kwargs: Additional keyword arguments

        Raises:
            PluginError: If initialization fails
        """
        await super().initialize(application_core, **kwargs)

        self._logger = self._logger or logging.getLogger(self.name)
        self._logger.info(f"Initializing {self.name} plugin v{self.version}")

        # Get required managers
        self._event_bus_manager = self._event_bus_manager or application_core.get_manager("event_bus_manager")
        self._config_manager = self._config_manager or application_core.get_manager("config_manager")
        self._task_manager = self._task_manager or application_core.get_manager("task_manager")
        self._database_manager = self._database_manager or application_core.get_manager("database_manager")
        self._concurrency_manager = self._concurrency_manager or application_core.get_manager("concurrency_manager")
        self._security_manager = self._security_manager or application_core.get_manager("security_manager")
        self._file_manager = self._file_manager or application_core.get_manager("file_manager")

        # Create the history manager and validation engine
        self._history_manager = HistoryManager(self._database_manager, self._logger)
        self._validation_engine = ValidationEngine(self._database_manager, self._logger)

        # Find the plugin directory and icon
        plugin_dir = await self._find_plugin_directory()
        if plugin_dir:
            icon_path = os.path.join(plugin_dir, "resources", "icon.png")
            if os.path.exists(icon_path):
                self._icon_path = icon_path
                self._logger.debug(f"Found plugin icon at: {icon_path}")

        # Create the plugin data directory
        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type="plugin_data")
                os.makedirs(plugin_data_dir, exist_ok=True)
                self._logger.debug(f"Plugin data directory: {plugin_data_dir}")
            except Exception as e:
                self._logger.warning(f"Failed to create plugin data directory: {str(e)}")

        # Load settings and saved data
        try:
            await self._load_settings()
            await self._load_connections()
            await self._load_saved_queries()
            await self._load_field_mappings()
        except Exception as e:
            self._logger.error(f"Error loading plugin data: {str(e)}")

        # Initialize history manager if configured
        if self._settings and self._settings.history_database_connection_id:
            try:
                self._history_manager._history_connection_id = self._settings.history_database_connection_id
                await self._history_manager.initialize()
            except Exception as e:
                self._logger.error(f"Failed to initialize history manager: {str(e)}")

        # Subscribe to events
        await self._event_bus_manager.subscribe(
            event_type="config/changed",
            callback=self._on_config_changed,
            subscriber_id=f"{self.name}_config_subscriber"
        )

        self._initialized = True
        await set_plugin_state(self.name, PluginLifecycleState.INITIALIZED)
        self._logger.info(f"{self.name} plugin initialized")

        # Publish initialization event
        await self._event_bus_manager.publish(
            event_type="plugin/initialized",
            source=self.name,
            payload={
                "plugin_name": self.name,
                "version": self.version,
                "has_ui": True
            }
        )

    async def on_ui_ready(self, ui_integration: Any) -> None:
        """
        Set up UI components when the UI is ready.

        Args:
            ui_integration: UI integration instance
        """
        self._logger.info("Setting up UI components")

        current_state = await get_plugin_state(self.name)
        if current_state == PluginLifecycleState.UI_READY:
            self._logger.debug("UI setup already in progress, avoiding recursive call")
            return

        # Make sure we're on the main thread
        if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
            self._logger.debug("on_ui_ready called from non-main thread, delegating to main thread")
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self.on_ui_ready(ui_integration))
            )
            return

        # Create UI components
        try:
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)

            # Add menu items
            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Database",
                title="Manage Connections",
                callback=lambda: asyncio.create_task(self._open_connection_manager())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Database",
                title="Query Editor",
                callback=lambda: asyncio.create_task(self._open_query_editor())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Database",
                title="Field Mappings",
                callback=lambda: asyncio.create_task(self._open_field_mappings())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Database",
                title="Data Validation",
                callback=lambda: asyncio.create_task(self._open_validation())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Database",
                title="History Manager",
                callback=lambda: asyncio.create_task(self._open_history_manager())
            )

            # Create and add the main tab
            if not self._main_widget:
                self._main_widget = DatabaseConnectorTab(
                    plugin=self,
                    logger=self._logger,
                    concurrency_manager=self._concurrency_manager,
                    event_bus_manager=self._event_bus_manager
                )

            p = Path(self.plugin_info.path)
            icon_file = p / self.plugin_info.manifest.icon_path
            icon_arg = str(icon_file) if icon_file.exists() else None

            await ui_integration.add_page(
                plugin_id=self.plugin_id,
                page_component=self._main_widget,
                icon=icon_arg,
                title=self.display_name or self.name
            )

            self._logger.info("UI components set up successfully")

            # Set plugin state to active
            await set_plugin_state(self.name, PluginLifecycleState.ACTIVE)
            await signal_ui_ready(self.name)

        except Exception as e:
            self._logger.error(f"Error setting up UI: {str(e)}")
            await set_plugin_state(self.name, PluginLifecycleState.FAILED)

    async def setup_ui(self, ui_integration: Any) -> None:
        """
        Set up the UI (alias for on_ui_ready for compatibility).

        Args:
            ui_integration: UI integration instance
        """
        self._logger.info("setup_ui method called")
        await self.on_ui_ready(ui_integration)

    # Connection management methods

    async def get_connections(self) -> Dict[str, BaseConnectionConfig]:
        """
        Get all stored connections.

        Returns:
            Dictionary of connection configurations
        """
        return self._connections.copy()

    async def get_connection(self, connection_id: str) -> Optional[BaseConnectionConfig]:
        """
        Get a specific connection configuration.

        Args:
            connection_id: Connection ID

        Returns:
            Connection configuration or None if not found
        """
        return self._connections.get(connection_id)

    async def save_connection(self, config: BaseConnectionConfig) -> str:
        """
        Save a connection configuration.

        Args:
            config: Connection configuration

        Returns:
            Connection ID

        Raises:
            PluginError: If saving fails
        """
        try:
            # Save the connection
            self._connections[config.id] = config

            # Update recent connections list in settings
            if self._settings and config.id not in self._settings.recent_connections:
                if config.id in self._settings.recent_connections:
                    self._settings.recent_connections.remove(config.id)
                self._settings.recent_connections.insert(0, config.id)
                self._settings.recent_connections = self._settings.recent_connections[:10]
                await self._save_settings()

            # Save to file
            await self._save_connections()

            self._logger.info(f"Saved connection: {config.name} ({config.id})")

            # Publish event
            await self._event_bus_manager.publish(
                event_type="database_connector/connection_saved",
                source=self.name,
                payload={"connection_id": config.id, "connection_name": config.name}
            )

            return config.id

        except Exception as e:
            self._logger.error(f"Failed to save connection: {str(e)}")
            raise PluginError(f"Failed to save connection: {str(e)}")

    async def delete_connection(self, connection_id: str) -> bool:
        """
        Delete a connection configuration.

        Args:
            connection_id: Connection ID

        Returns:
            True if deleted, False if not found

        Raises:
            PluginError: If deletion fails
        """
        try:
            # Check if connection exists
            if connection_id not in self._connections:
                return False

            # Get the connection name for logging
            connection_name = self._connections[connection_id].name

            # Disconnect if connected
            if connection_id in self._active_connectors:
                await self.disconnect(connection_id)

            # Remove from active connectors
            if connection_id in self._active_connectors:
                del self._active_connectors[connection_id]

            # Remove from connectors locks
            if connection_id in self._connector_locks:
                del self._connector_locks[connection_id]

            # Remove from connections
            del self._connections[connection_id]

            # Update settings
            if self._settings:
                if connection_id in self._settings.recent_connections:
                    self._settings.recent_connections.remove(connection_id)
                if self._settings.default_connection_id == connection_id:
                    self._settings.default_connection_id = None
                await self._save_settings()

            # Save to file
            await self._save_connections()

            self._logger.info(f"Deleted connection: {connection_name} ({connection_id})")

            # Publish event
            await self._event_bus_manager.publish(
                event_type="database_connector/connection_deleted",
                source=self.name,
                payload={"connection_id": connection_id, "connection_name": connection_name}
            )

            return True

        except Exception as e:
            self._logger.error(f"Failed to delete connection: {str(e)}")
            raise PluginError(f"Failed to delete connection: {str(e)}")

    async def get_connector(
            self,
            connection_id: str
    ) -> BaseDatabaseConnector:
        """
        Get a database connector for a connection.
        Creates the connector if it doesn't exist and connects if not connected.

        Args:
            connection_id: Connection ID

        Returns:
            Database connector

        Raises:
            PluginError: If getting the connector fails
        """
        try:
            # Get the connection lock or create it
            if connection_id not in self._connector_locks:
                self._connector_locks[connection_id] = asyncio.Lock()

            # Acquire the lock to ensure only one thread is connecting
            async with self._connector_locks[connection_id]:
                # Check if we already have a connector
                if connection_id in self._active_connectors:
                    connector = self._active_connectors[connection_id]

                    # If not connected, connect
                    if not connector.is_connected:
                        await connector.connect()

                    return connector

                # Get the connection configuration
                config = self._connections.get(connection_id)
                if not config:
                    raise PluginError(f"Connection not found: {connection_id}")

                # Create the connector
                connector = get_connector_for_config(
                    config=config,
                    logger=self._logger,
                    security_manager=self._security_manager
                )

                # Connect
                await connector.connect()

                # Store the connector
                self._active_connectors[connection_id] = connector

                return connector

        except Exception as e:
            self._logger.error(f"Failed to get connector: {str(e)}")
            raise PluginError(f"Failed to get connector: {str(e)}")

    async def disconnect(self, connection_id: str) -> bool:
        """
        Disconnect from a database.

        Args:
            connection_id: Connection ID

        Returns:
            True if disconnected, False if already disconnected or not found

        Raises:
            PluginError: If disconnection fails
        """
        try:
            # Check if we have a connector
            if connection_id not in self._active_connectors:
                return False

            connector = self._active_connectors[connection_id]

            # Only disconnect if connected
            if connector.is_connected:
                await connector.disconnect()
                self._logger.info(f"Disconnected from database: {connection_id}")

                # Publish event
                await self._event_bus_manager.publish(
                    event_type="database_connector/disconnected",
                    source=self.name,
                    payload={"connection_id": connection_id}
                )

            return True

        except Exception as e:
            self._logger.error(f"Failed to disconnect: {str(e)}")
            raise PluginError(f"Failed to disconnect: {str(e)}")

    async def test_connection(
            self,
            config: BaseConnectionConfig
    ) -> Tuple[bool, Optional[str]]:
        """
        Test a database connection.

        Args:
            config: Connection configuration

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Create a temporary connector
            connector = get_connector_for_config(
                config=config,
                logger=self._logger,
                security_manager=self._security_manager
            )

            # Test the connection
            result = await connector.test_connection()

            # Try to clean up
            try:
                if connector.is_connected:
                    await connector.disconnect()
            except:
                pass

            return result

        except Exception as e:
            self._logger.error(f"Connection test failed: {str(e)}")
            return False, str(e)

    # Query management methods

    async def get_saved_queries(
            self,
            connection_id: Optional[str] = None
    ) -> Dict[str, SavedQuery]:
        """
        Get all saved queries, optionally filtered by connection.

        Args:
            connection_id: Optional connection ID filter

        Returns:
            Dictionary of saved queries
        """
        if connection_id:
            return {
                qid: query for qid, query in self._saved_queries.items()
                if query.connection_id == connection_id
            }
        else:
            return self._saved_queries.copy()

    async def get_saved_query(self, query_id: str) -> Optional[SavedQuery]:
        """
        Get a specific saved query.

        Args:
            query_id: Query ID

        Returns:
            Saved query or None if not found
        """
        return self._saved_queries.get(query_id)

    async def save_query(self, query: SavedQuery) -> str:
        """
        Save a query.

        Args:
            query: Query to save

        Returns:
            Query ID

        Raises:
            PluginError: If saving fails
        """
        try:
            # Update timestamp
            query.updated_at = datetime.datetime.now()

            # Save the query
            self._saved_queries[query.id] = query

            # Save to file
            await self._save_saved_queries()

            self._logger.info(f"Saved query: {query.name} ({query.id})")

            # Publish event
            await self._event_bus_manager.publish(
                event_type="database_connector/query_saved",
                source=self.name,
                payload={"query_id": query.id, "query_name": query.name}
            )

            return query.id

        except Exception as e:
            self._logger.error(f"Failed to save query: {str(e)}")
            raise PluginError(f"Failed to save query: {str(e)}")

    async def delete_query(self, query_id: str) -> bool:
        """
        Delete a saved query.

        Args:
            query_id: Query ID

        Returns:
            True if deleted, False if not found

        Raises:
            PluginError: If deletion fails
        """
        try:
            # Check if query exists
            if query_id not in self._saved_queries:
                return False

            # Get the query name for logging
            query_name = self._saved_queries[query_id].name

            # Remove the query
            del self._saved_queries[query_id]

            # Save to file
            await self._save_saved_queries()

            self._logger.info(f"Deleted query: {query_name} ({query_id})")

            # Publish event
            await self._event_bus_manager.publish(
                event_type="database_connector/query_deleted",
                source=self.name,
                payload={"query_id": query_id, "query_name": query_name}
            )

            return True

        except Exception as e:
            self._logger.error(f"Failed to delete query: {str(e)}")
            raise PluginError(f"Failed to delete query: {str(e)}")

    async def execute_query(
            self,
            connection_id: str,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            mapping_id: Optional[str] = None
    ) -> QueryResult:
        """
        Execute a query against a database.

        Args:
            connection_id: Connection ID
            query: SQL query
            params: Optional parameters
            limit: Optional result limit
            mapping_id: Optional field mapping ID to apply

        Returns:
            Query result

        Raises:
            PluginError: If execution fails
        """
        try:
            # Get the connector
            connector = await self.get_connector(connection_id)

            # Execute the query
            result = await connector.execute_query(
                query=query,
                params=params,
                limit=limit
            )

            # Apply field mapping if provided
            if mapping_id and mapping_id in self._field_mappings:
                mapping = self._field_mappings[mapping_id]
                result = apply_mapping_to_results(result, mapping)

            self._logger.info(
                f"Executed query on {connection_id}, returned {result.row_count} rows"
            )

            # Publish event
            await self._event_bus_manager.publish(
                event_type="database_connector/query_executed",
                source=self.name,
                payload={
                    "connection_id": connection_id,
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms
                }
            )

            return result

        except Exception as e:
            self._logger.error(f"Failed to execute query: {str(e)}")
            raise PluginError(f"Failed to execute query: {str(e)}")

    # Field mapping methods

    async def get_field_mappings(
            self,
            connection_id: Optional[str] = None,
            table_name: Optional[str] = None
    ) -> Dict[str, FieldMapping]:
        """
        Get all field mappings, optionally filtered.

        Args:
            connection_id: Optional connection ID filter
            table_name: Optional table name filter

        Returns:
            Dictionary of field mappings
        """
        if connection_id or table_name:
            filtered_mappings = {}
            for mapping_id, mapping in self._field_mappings.items():
                if connection_id and mapping.connection_id != connection_id:
                    continue
                if table_name and mapping.table_name != table_name:
                    continue
                filtered_mappings[mapping_id] = mapping
            return filtered_mappings
        else:
            return self._field_mappings.copy()

    async def get_field_mapping(
            self,
            mapping_id: str
    ) -> Optional[FieldMapping]:
        """
        Get a specific field mapping.

        Args:
            mapping_id: Mapping ID

        Returns:
            Field mapping or None if not found
        """
        return self._field_mappings.get(mapping_id)

    async def save_field_mapping(
            self,
            mapping: FieldMapping
    ) -> str:
        """
        Save a field mapping.

        Args:
            mapping: Field mapping to save

        Returns:
            Mapping ID

        Raises:
            PluginError: If saving fails
        """
        try:
            # Update timestamp
            mapping.updated_at = datetime.datetime.now()

            # Save the mapping
            self._field_mappings[mapping.id] = mapping

            # Save to file
            await self._save_field_mappings()

            self._logger.info(
                f"Saved field mapping for {mapping.table_name} on {mapping.connection_id}"
            )

            # Publish event
            await self._event_bus_manager.publish(
                event_type="database_connector/mapping_saved",
                source=self.name,
                payload={
                    "mapping_id": mapping.id,
                    "connection_id": mapping.connection_id,
                    "table_name": mapping.table_name
                }
            )

            return mapping.id

        except Exception as e:
            self._logger.error(f"Failed to save field mapping: {str(e)}")
            raise PluginError(f"Failed to save field mapping: {str(e)}")

    async def delete_field_mapping(
            self,
            mapping_id: str
    ) -> bool:
        """
        Delete a field mapping.

        Args:
            mapping_id: Mapping ID

        Returns:
            True if deleted, False if not found

        Raises:
            PluginError: If deletion fails
        """
        try:
            # Check if mapping exists
            if mapping_id not in self._field_mappings:
                return False

            # Get mapping details for logging
            mapping = self._field_mappings[mapping_id]

            # Delete the mapping
            del self._field_mappings[mapping_id]

            # Save to file
            await self._save_field_mappings()

            self._logger.info(
                f"Deleted field mapping for {mapping.table_name} on {mapping.connection_id}"
            )

            # Publish event
            await self._event_bus_manager.publish(
                event_type="database_connector/mapping_deleted",
                source=self.name,
                payload={
                    "mapping_id": mapping_id,
                    "connection_id": mapping.connection_id,
                    "table_name": mapping.table_name
                }
            )

            return True

        except Exception as e:
            self._logger.error(f"Failed to delete field mapping: {str(e)}")
            raise PluginError(f"Failed to delete field mapping: {str(e)}")

    # Validation methods

    async def get_validation_engine(self) -> ValidationEngine:
        """
        Get the validation engine.

        Returns:
            Validation engine
        """
        return self._validation_engine

    # History methods

    async def get_history_manager(self) -> HistoryManager:
        """
        Get the history manager.

        Returns:
            History manager
        """
        return self._history_manager

    # UI callback methods

    async def _open_connection_manager(self) -> None:
        """Open the connection manager dialog."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_connection_manager())
            )
            return

        if self._main_widget:
            self._main_widget.open_connection_manager()

    async def _open_query_editor(self) -> None:
        """Open the query editor tab."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_query_editor())
            )
            return

        if self._main_widget:
            self._main_widget.switch_to_query_editor()

    async def _open_field_mappings(self) -> None:
        """Open the field mappings tab."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_field_mappings())
            )
            return

        if self._main_widget:
            self._main_widget.switch_to_mapping_editor()

    async def _open_validation(self) -> None:
        """Open the validation tab."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_validation())
            )
            return

        if self._main_widget:
            self._main_widget.switch_to_validation()

    async def _open_history_manager(self) -> None:
        """Open the history manager tab."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_history_manager())
            )
            return

        if self._main_widget:
            self._main_widget.switch_to_history()

    # Utility methods

    async def _find_plugin_directory(self) -> Optional[str]:
        """
        Find the plugin directory.

        Returns:
            Plugin directory path or None if not found
        """
        import inspect
        try:
            module_path = inspect.getmodule(self).__file__
            if module_path:
                return os.path.dirname(os.path.abspath(module_path))
        except (AttributeError, TypeError):
            pass
        return None

    async def _load_settings(self) -> None:
        """
        Load plugin settings from the config manager.

        Raises:
            PluginError: If loading fails
        """
        try:
            if not self._config_manager:
                return

            settings_dict = await self._config_manager.get(
                f"plugins.{self.name}.settings",
                {}
            )

            if settings_dict:
                self._settings = PluginSettings(**settings_dict)
            else:
                self._settings = PluginSettings()

            self._logger.debug("Loaded plugin settings")

        except Exception as e:
            self._logger.error(f"Failed to load settings: {str(e)}")
            self._settings = PluginSettings()
            raise PluginError(f"Failed to load settings: {str(e)}")

    async def _save_settings(self) -> None:
        try:
            if not self._config_manager or not self._settings:
                return
            settings_dict = self._settings.dict()
            # Add debug logging
            self._logger.debug(f'Saving settings: {settings_dict}')
            await self._config_manager.set(f'plugins.{self.name}.settings', settings_dict)
            self._logger.debug('Saved plugin settings')
        except Exception as e:
            self._logger.error(f'Failed to save settings: {str(e)}')
            raise PluginError(f'Failed to save settings: {str(e)}')

    async def _load_connections(self) -> None:
        """
        Load connection configurations from storage.

        Raises:
            PluginError: If loading fails
        """
        try:
            if not self._file_manager:
                return

            file_path = f"{self.name}/connections.json"
            try:
                file_info = await self._file_manager.get_file_info(
                    file_path,
                    "plugin_data"
                )
                if not file_info:
                    return
            except:
                return

            json_data = await self._file_manager.read_text(
                file_path,
                "plugin_data"
            )

            data = json.loads(json_data)
            connections = {}

            for conn_data in data:
                try:
                    # Handle password field for SecretStr
                    if "password" in conn_data and not conn_data["password"].startswith("SecretStr"):
                        conn_data["password"] = conn_data["password"]

                    # Create the correct connection type
                    conn_type = conn_data.get("connection_type")
                    if conn_type == ConnectionType.AS400:
                        connection = AS400ConnectionConfig(**conn_data)
                    elif conn_type == ConnectionType.ODBC:
                        connection = ODBCConnectionConfig(**conn_data)
                    else:
                        # Default to base connection
                        connection = BaseConnectionConfig(**conn_data)

                    connections[connection.id] = connection
                except Exception as e:
                    self._logger.warning(f"Failed to load connection: {str(e)}")
                    continue

            self._connections = connections
            self._logger.info(f"Loaded {len(connections)} database connections")

        except Exception as e:
            self._logger.error(f"Failed to load connections: {str(e)}")
            raise PluginError(f"Failed to load connections: {str(e)}")

    async def _save_connections(self) -> None:
        """
        Save connection configurations to storage.

        Raises:
            PluginError: If saving fails
        """
        try:
            if not self._file_manager:
                return

            file_path = f"{self.name}/connections.json"
            await self._file_manager.ensure_directory(self.name, "plugin_data")

            conn_list = []
            for conn in self._connections.values():
                conn_dict = conn.dict()
                if "password" in conn_dict:
                    # Store the raw password value for saving
                    conn_dict["password"] = conn.password.get_secret_value()
                conn_list.append(conn_dict)

            json_data = json.dumps(conn_list, indent=2)
            await self._file_manager.write_text(
                file_path,
                json_data,
                "plugin_data"
            )

            self._logger.debug(f"Saved {len(conn_list)} database connections")

        except Exception as e:
            self._logger.error(f"Failed to save connections: {str(e)}")
            raise PluginError(f"Failed to save connections: {str(e)}")

    async def _load_saved_queries(self) -> None:
        """
        Load saved queries from storage.

        Raises:
            PluginError: If loading fails
        """
        try:
            if not self._file_manager:
                return

            file_path = f"{self.name}/saved_queries.json"
            try:
                file_info = await self._file_manager.get_file_info(
                    file_path,
                    "plugin_data"
                )
                if not file_info:
                    return
            except:
                return

            json_data = await self._file_manager.read_text(
                file_path,
                "plugin_data"
            )

            data = json.loads(json_data)
            queries = {}

            for query_data in data:
                try:
                    # Convert date strings to datetime objects
                    if "created_at" in query_data and isinstance(query_data["created_at"], str):
                        query_data["created_at"] = datetime.datetime.fromisoformat(query_data["created_at"])
                    if "updated_at" in query_data and isinstance(query_data["updated_at"], str):
                        query_data["updated_at"] = datetime.datetime.fromisoformat(query_data["updated_at"])

                    query = SavedQuery(**query_data)
                    queries[query.id] = query
                except Exception as e:
                    self._logger.warning(f"Failed to load query: {str(e)}")
                    continue

            self._saved_queries = queries
            self._logger.info(f"Loaded {len(queries)} saved queries")

        except Exception as e:
            self._logger.error(f"Failed to load saved queries: {str(e)}")
            raise PluginError(f"Failed to load saved queries: {str(e)}")

    async def _save_saved_queries(self) -> None:
        """
        Save queries to storage.

        Raises:
            PluginError: If saving fails
        """
        try:
            if not self._file_manager:
                return

            file_path = f"{self.name}/saved_queries.json"
            await self._file_manager.ensure_directory(self.name, "plugin_data")

            query_list = []
            for query in self._saved_queries.values():
                query_dict = query.dict()
                # Convert datetime objects to ISO format strings
                if "created_at" in query_dict and isinstance(query_dict["created_at"], datetime.datetime):
                    query_dict["created_at"] = query_dict["created_at"].isoformat()
                if "updated_at" in query_dict and isinstance(query_dict["updated_at"], datetime.datetime):
                    query_dict["updated_at"] = query_dict["updated_at"].isoformat()

                query_list.append(query_dict)

            json_data = json.dumps(query_list, indent=2)
            await self._file_manager.write_text(
                file_path,
                json_data,
                "plugin_data"
            )

            self._logger.debug(f"Saved {len(query_list)} queries")

        except Exception as e:
            self._logger.error(f"Failed to save queries: {str(e)}")
            raise PluginError(f"Failed to save queries: {str(e)}")

    async def _load_field_mappings(self) -> None:
        """
        Load field mappings from storage.

        Raises:
            PluginError: If loading fails
        """
        try:
            if not self._file_manager:
                return

            file_path = f"{self.name}/field_mappings.json"
            try:
                file_info = await self._file_manager.get_file_info(
                    file_path,
                    "plugin_data"
                )
                if not file_info:
                    return
            except:
                return

            json_data = await self._file_manager.read_text(
                file_path,
                "plugin_data"
            )

            data = json.loads(json_data)
            mappings = {}

            for mapping_data in data:
                try:
                    # Convert date strings to datetime objects
                    if "created_at" in mapping_data and isinstance(mapping_data["created_at"], str):
                        mapping_data["created_at"] = datetime.datetime.fromisoformat(mapping_data["created_at"])
                    if "updated_at" in mapping_data and isinstance(mapping_data["updated_at"], str):
                        mapping_data["updated_at"] = datetime.datetime.fromisoformat(mapping_data["updated_at"])

                    mapping = FieldMapping(**mapping_data)
                    mappings[mapping.id] = mapping
                except Exception as e:
                    self._logger.warning(f"Failed to load field mapping: {str(e)}")
                    continue

            self._field_mappings = mappings
            self._logger.info(f"Loaded {len(mappings)} field mappings")

        except Exception as e:
            self._logger.error(f"Failed to load field mappings: {str(e)}")
            raise PluginError(f"Failed to load field mappings: {str(e)}")

    async def _save_field_mappings(self) -> None:
        """
        Save field mappings to storage.

        Raises:
            PluginError: If saving fails
        """
        try:
            if not self._file_manager:
                return

            file_path = f"{self.name}/field_mappings.json"
            await self._file_manager.ensure_directory(self.name, "plugin_data")

            mapping_list = []
            for mapping in self._field_mappings.values():
                mapping_dict = mapping.dict()
                # Convert datetime objects to ISO format strings
                if "created_at" in mapping_dict and isinstance(mapping_dict["created_at"], datetime.datetime):
                    mapping_dict["created_at"] = mapping_dict["created_at"].isoformat()
                if "updated_at" in mapping_dict and isinstance(mapping_dict["updated_at"], datetime.datetime):
                    mapping_dict["updated_at"] = mapping_dict["updated_at"].isoformat()

                mapping_list.append(mapping_dict)

            json_data = json.dumps(mapping_list, indent=2)
            await self._file_manager.write_text(
                file_path,
                json_data,
                "plugin_data"
            )

            self._logger.debug(f"Saved {len(mapping_list)} field mappings")

        except Exception as e:
            self._logger.error(f"Failed to save field mappings: {str(e)}")
            raise PluginError(f"Failed to save field mappings: {str(e)}")

    async def _on_config_changed(self, event: Any) -> None:
        """
        Handle configuration changes.

        Args:
            event: Config change event
        """
        if not event.payload.get("key", "").startswith(f"plugins.{self.name}"):
            return

        self._logger.info(
            f"Configuration changed: {event.payload.get('key')} = {event.payload.get('value')}"
        )

        # Reload settings
        await self._load_settings()

        # Update the main widget if needed
        if self._main_widget:
            self._main_widget.handle_config_change(
                event.payload.get("key"),
                event.payload.get("value")
            )

    async def shutdown(self) -> None:
        """
        Shut down the plugin, cleaning up resources.

        Raises:
            PluginError: If shutdown fails
        """
        if not self._initialized:
            return

        self._logger.info(f"Shutting down {self.name} plugin")

        try:
            # Set state to disabling
            await set_plugin_state(self.name, PluginLifecycleState.DISABLING)

            # Save settings and data
            try:
                await self._save_settings()
                await self._save_connections()
                await self._save_saved_queries()
                await self._save_field_mappings()
            except Exception as e:
                self._logger.warning(f"Error saving plugin data during shutdown: {str(e)}")

            # Disconnect all active connections
            for connection_id in list(self._active_connectors.keys()):
                try:
                    await self.disconnect(connection_id)
                except Exception as e:
                    self._logger.warning(f"Error disconnecting {connection_id}: {str(e)}")

            # Clean up UI
            self._main_widget = None

            # Unsubscribe from events
            if self._event_bus_manager:
                await self._event_bus_manager.unsubscribe(subscriber_id=f"{self.name}_config_subscriber")

            # Clear data
            self._connections = {}
            self._active_connectors = {}
            self._connector_locks = {}
            self._saved_queries = {}
            self._field_mappings = {}

            # Base shutdown
            await super().shutdown()

            self._initialized = False

            # Set state to inactive
            await set_plugin_state(self.name, PluginLifecycleState.INACTIVE)

            self._logger.info(f"{self.name} plugin shutdown complete")

        except Exception as e:
            self._logger.error(f"Error during plugin shutdown: {str(e)}")
            raise PluginError(f"Error during plugin shutdown: {str(e)}")

    def status(self) -> Dict[str, Any]:
        """
        Get plugin status information.

        Returns:
            Status dictionary
        """
        status = {
            "name": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "connections": {
                "total": len(self._connections),
                "active": len(self._active_connectors)
            },
            "queries": {
                "total": len(self._saved_queries)
            },
            "mappings": {
                "total": len(self._field_mappings)
            },
            "ui_active": self._main_widget is not None
        }

        if self._settings:
            status["settings"] = {
                "recent_connections": len(self._settings.recent_connections),
                "has_default_connection": self._settings.default_connection_id is not None,
                "history_enabled": self._settings.history_database_connection_id is not None
            }

        return status