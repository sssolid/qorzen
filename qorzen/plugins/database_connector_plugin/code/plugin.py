from __future__ import annotations

from .ui import DatabaseConnectorTab

"""
Main plugin module for the Database Connector Plugin.

This module provides a UI layer over the core DatabaseManager functionality,
allowing users to manage database connections, execute queries, and view results.
"""

import asyncio
import json
import logging
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QMessageBox

from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.lifecycle import (
    get_plugin_state,
    set_plugin_state,
    PluginLifecycleState,
    signal_ui_ready
)
from qorzen.utils.exceptions import PluginError, DatabaseError
from qorzen.core.database_manager import DatabaseConnectionConfig, ConnectionType

from .models import SavedQuery, PluginSettings


class DatabaseConnectorPlugin(BasePlugin):
    """
    Database Connector Plugin for Qorzen.

    Provides a user interface layer over the core DatabaseManager functionality.
    This plugin does NOT duplicate database functionality - it delegates all
    database operations to the core DatabaseManager.
    """

    name = "database_connector_plugin"
    version = "1.1.0"
    description = "UI for database connectivity and query execution via core DatabaseManager"
    author = "Qorzen Team"
    display_name = "Database Connector"
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the Database Connector Plugin."""
        super().__init__()

        # Core managers
        self._logger: Optional[logging.Logger] = None
        self._event_bus_manager: Any = None
        self._config_manager: Any = None
        self._task_manager: Any = None
        self._database_manager: Any = None
        self._concurrency_manager: Any = None
        self._security_manager: Any = None
        self._file_manager: Any = None

        # Plugin-specific state (UI layer only)
        self._initialized = False
        self._saved_queries: Dict[str, SavedQuery] = {}
        self._settings: Optional[PluginSettings] = None
        self._main_widget: Optional[QWidget] = None  # Will be DatabaseConnectorTab when UI implemented
        self._icon_path: Optional[str] = None

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin with application core managers.

        Args:
            application_core: The application core instance
            **kwargs: Additional initialization parameters
        """
        await super().initialize(application_core, **kwargs)

        self._logger = logging.getLogger(self.name)
        self._logger.info(f"Initializing {self.name} plugin v{self.version}")

        # Get core managers
        self._event_bus_manager = application_core.get_manager("event_bus_manager")
        self._config_manager = application_core.get_manager("config_manager")
        self._task_manager = application_core.get_manager("task_manager")
        self._database_manager = application_core.get_manager("database_manager")
        self._concurrency_manager = application_core.get_manager("concurrency_manager")
        self._security_manager = application_core.get_manager("security_manager")
        self._file_manager = application_core.get_manager("file_manager")

        # Validate required managers
        if not self._database_manager:
            raise PluginError("DatabaseManager is required but not available")
        if not self._file_manager:
            raise PluginError("FileManager is required but not available")

        # Setup plugin icon
        plugin_dir = await self._find_plugin_directory()
        if plugin_dir:
            icon_path = plugin_dir / "resources" / "icon.png"
            if icon_path.exists():
                self._icon_path = str(icon_path)
                self._logger.debug(f"Found plugin icon at: {icon_path}")

        # Setup plugin data directory
        try:
            await self._file_manager.ensure_directory(self.name, "plugin_data")
            self._logger.debug(f"Plugin data directory ensured: {self.name}")
        except Exception as e:
            self._logger.warning(f"Failed to create plugin data directory: {e}")

        # Load plugin-specific data (UI preferences, saved queries)
        try:
            await self._load_settings()
            await self._load_saved_queries()
        except Exception as e:
            self._logger.error(f"Error loading plugin data: {e}")

        # Subscribe to events
        if self._event_bus_manager:
            await self._event_bus_manager.subscribe(
                event_type="config/changed",
                callback=self._on_config_changed,
                subscriber_id=f"{self.name}_config_subscriber"
            )

        self._initialized = True
        await set_plugin_state(self.name, PluginLifecycleState.INITIALIZED)
        self._logger.info(f"{self.name} plugin initialized")

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
        """Setup UI components when UI system is ready."""
        self._logger.info("Setting up UI components")

        current_state = await get_plugin_state(self.name)
        if current_state == PluginLifecycleState.UI_READY:
            self._logger.debug("UI setup already in progress, avoiding recursive call")
            return

        if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
            self._logger.debug("on_ui_ready called from non-main thread, delegating to main thread")
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self.on_ui_ready(ui_integration))
            )
            return

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

            if not self._main_widget:
                self._main_widget = DatabaseConnectorTab(
                    plugin=self,
                    logger=self._logger,
                    concurrency_manager=self._concurrency_manager,
                    event_bus_manager=self._event_bus_manager
                )

            # Setup plugin icon
            icon_arg = None
            if self.plugin_info and self.plugin_info.path:
                p = Path(self.plugin_info.path)
                if hasattr(self.plugin_info, 'manifest') and hasattr(self.plugin_info.manifest, 'icon_path'):
                    icon_file = p / self.plugin_info.manifest.icon_path
                    if icon_file.exists():
                        icon_arg = str(icon_file)

            await ui_integration.add_page(
                plugin_id=self.plugin_id,
                page_component=self._main_widget,
                icon=icon_arg,
                title=self.display_name or self.name
            )

            self._logger.info("UI components set up successfully")
            await set_plugin_state(self.name, PluginLifecycleState.ACTIVE)
            await signal_ui_ready(self.name)

        except Exception as e:
            self._logger.error(f"Error setting up UI: {e}")
            await set_plugin_state(self.name, PluginLifecycleState.FAILED)

    async def setup_ui(self, ui_integration: Any) -> None:
        """Legacy UI setup method."""
        self._logger.info("setup_ui method called")
        await self.on_ui_ready(ui_integration)

    # ============================================================================
    # DATABASE CONNECTION METHODS (delegate to core DatabaseManager)
    # ============================================================================

    async def get_connections(self) -> List[str]:
        """Get list of registered database connection names."""
        if not self._database_manager:
            return []
        return await self._database_manager.get_connection_names()

    async def register_connection(self, config: DatabaseConnectionConfig) -> str:
        """
        Register a new database connection with the core DatabaseManager.

        Args:
            config: Database connection configuration

        Returns:
            Connection name/ID
        """
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            await self._database_manager.register_connection(config)

            # Update recent connections in UI settings
            if self._settings:
                if config.name in self._settings.recent_connections:
                    self._settings.recent_connections.remove(config.name)
                self._settings.recent_connections.insert(0, config.name)
                self._settings.recent_connections = self._settings.recent_connections[
                                                    :self._settings.max_recent_connections]
                await self._save_settings()

            self._logger.info(f"Registered connection: {config.name}")

            # Publish event
            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/connection_registered",
                    source=self.name,
                    payload={"connection_name": config.name}
                )

            return config.name

        except Exception as e:
            self._logger.error(f"Failed to register connection: {e}")
            raise PluginError(f"Failed to register connection: {e}") from e

    async def unregister_connection(self, connection_name: str) -> bool:
        """
        Unregister a database connection from the core DatabaseManager.

        Args:
            connection_name: Name of connection to unregister

        Returns:
            True if successful
        """
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            success = await self._database_manager.unregister_connection(connection_name)

            if success:
                # Remove from recent connections
                if self._settings and connection_name in self._settings.recent_connections:
                    self._settings.recent_connections.remove(connection_name)
                    await self._save_settings()

                self._logger.info(f"Unregistered connection: {connection_name}")

                # Publish event
                if self._event_bus_manager:
                    await self._event_bus_manager.publish(
                        event_type="database_connector/connection_unregistered",
                        source=self.name,
                        payload={"connection_name": connection_name}
                    )

            return success

        except Exception as e:
            self._logger.error(f"Failed to unregister connection: {e}")
            raise PluginError(f"Failed to unregister connection: {e}") from e

    async def test_connection(self, connection_name: str) -> Tuple[bool, Optional[str]]:
        """
        Test a database connection using the core DatabaseManager.

        Args:
            connection_name: Name of connection to test

        Returns:
            Tuple of (success, error_message)
        """
        if not self._database_manager:
            return (False, "DatabaseManager not available")

        try:
            is_connected = await self._database_manager.check_connection(connection_name)
            return (is_connected, None if is_connected else "Connection failed")
        except Exception as e:
            error_msg = str(e)
            self._logger.error(f"Connection test failed: {error_msg}")
            return (False, error_msg)

    async def execute_query(
            self,
            connection_name: str,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            apply_mapping: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a query using the core DatabaseManager.

        Args:
            connection_name: Database connection to use
            query: SQL query to execute
            params: Query parameters
            limit: Result limit
            apply_mapping: Whether to apply field mappings

        Returns:
            Query result dictionary
        """
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            # Use the query limit from settings if not specified
            if limit is None and self._settings:
                limit = self._settings.query_limit

            result = await self._database_manager.execute_query(
                query=query,
                params=params,
                connection_name=connection_name,
                limit=limit,
                apply_mapping=apply_mapping
            )

            self._logger.info(f"Executed query on {connection_name}, returned {result.get('row_count', 0)} rows")

            # Publish event
            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/query_executed",
                    source=self.name,
                    payload={
                        "connection_name": connection_name,
                        "row_count": result.get("row_count", 0),
                        "execution_time_ms": result.get("execution_time_ms", 0)
                    }
                )

            return result

        except Exception as e:
            self._logger.error(f"Failed to execute query: {e}")
            raise PluginError(f"Failed to execute query: {e}") from e

    async def get_tables(self, connection_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get table list using core DatabaseManager."""
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            return await self._database_manager.get_tables(connection_name, schema)
        except Exception as e:
            self._logger.error(f"Failed to get tables: {e}")
            raise PluginError(f"Failed to get tables: {e}") from e

    async def get_table_columns(self, connection_name: str, table_name: str, schema: Optional[str] = None) -> List[
        Dict[str, Any]]:
        """Get table columns using core DatabaseManager."""
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            return await self._database_manager.get_table_columns(table_name, connection_name, schema)
        except Exception as e:
            self._logger.error(f"Failed to get table columns: {e}")
            raise PluginError(f"Failed to get table columns: {e}") from e

    # ============================================================================
    # FIELD MAPPING METHODS (delegate to core DatabaseManager)
    # ============================================================================

    async def get_field_mappings(self, connection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get field mappings using core DatabaseManager."""
        if not self._database_manager:
            return []

        try:
            return await self._database_manager.get_all_field_mappings(connection_id)
        except Exception as e:
            self._logger.error(f"Failed to get field mappings: {e}")
            return []

    async def create_field_mapping(self, connection_id: str, table_name: str, mappings: Dict[str, str],
                                   description: Optional[str] = None) -> Dict[str, Any]:
        """Create field mapping using core DatabaseManager."""
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            return await self._database_manager.create_field_mapping(connection_id, table_name, mappings, description)
        except Exception as e:
            self._logger.error(f"Failed to create field mapping: {e}")
            raise PluginError(f"Failed to create field mapping: {e}") from e

    async def delete_field_mapping(self, mapping_id: str) -> bool:
        """Delete field mapping using core DatabaseManager."""
        if not self._database_manager:
            return False

        try:
            return await self._database_manager.delete_field_mapping(mapping_id)
        except Exception as e:
            self._logger.error(f"Failed to delete field mapping: {e}")
            return False

    # ============================================================================
    # VALIDATION METHODS (delegate to core DatabaseManager)
    # ============================================================================

    async def get_validation_rules(self, connection_id: Optional[str] = None, table_name: Optional[str] = None) -> List[
        Dict[str, Any]]:
        """Get validation rules using core DatabaseManager."""
        if not self._database_manager:
            return []

        try:
            return await self._database_manager.get_all_validation_rules(connection_id, table_name)
        except Exception as e:
            self._logger.error(f"Failed to get validation rules: {e}")
            return []

    async def create_validation_rule(self, rule_type: str, connection_id: str, table_name: str, field_name: str,
                                     parameters: Dict[str, Any], error_message: str, name: Optional[str] = None,
                                     description: Optional[str] = None) -> Dict[str, Any]:
        """Create validation rule using core DatabaseManager."""
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            return await self._database_manager.create_validation_rule(
                rule_type, connection_id, table_name, field_name,
                parameters, error_message, name, description
            )
        except Exception as e:
            self._logger.error(f"Failed to create validation rule: {e}")
            raise PluginError(f"Failed to create validation rule: {e}") from e

    async def validate_data(self, connection_id: str, table_name: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate data using core DatabaseManager."""
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            return await self._database_manager.validate_data(connection_id, table_name, data)
        except Exception as e:
            self._logger.error(f"Failed to validate data: {e}")
            raise PluginError(f"Failed to validate data: {e}") from e

    # ============================================================================
    # HISTORY METHODS (delegate to core DatabaseManager)
    # ============================================================================

    async def get_history_schedules(self) -> List[Dict[str, Any]]:
        """Get history schedules using core DatabaseManager."""
        if not self._database_manager:
            return []

        try:
            return await self._database_manager.get_all_history_schedules()
        except Exception as e:
            self._logger.error(f"Failed to get history schedules: {e}")
            return []

    async def create_history_schedule(self, connection_id: str, query_id: str, frequency: str, name: str,
                                      description: Optional[str] = None, retention_days: int = 365) -> Dict[str, Any]:
        """Create history schedule using core DatabaseManager."""
        if not self._database_manager:
            raise PluginError("DatabaseManager not available")

        try:
            return await self._database_manager.create_history_schedule(
                connection_id, query_id, frequency, name, description, retention_days
            )
        except Exception as e:
            self._logger.error(f"Failed to create history schedule: {e}")
            raise PluginError(f"Failed to create history schedule: {e}") from e

    # ============================================================================
    # SAVED QUERIES (Plugin-specific UI functionality)
    # ============================================================================

    async def get_saved_queries(self, connection_id: Optional[str] = None) -> Dict[str, SavedQuery]:
        """Get saved queries (plugin-specific UI feature)."""
        if connection_id:
            return {
                qid: query for qid, query in self._saved_queries.items()
                if query.connection_id == connection_id
            }
        return self._saved_queries.copy()

    async def get_saved_query(self, query_id: str) -> Optional[SavedQuery]:
        """Get a specific saved query."""
        return self._saved_queries.get(query_id)

    async def save_query(self, query: SavedQuery) -> str:
        """Save a query (plugin-specific UI feature)."""
        try:
            query.updated_at = datetime.datetime.now()
            self._saved_queries[query.id] = query
            await self._save_saved_queries()

            self._logger.info(f"Saved query: {query.name} ({query.id})")

            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/query_saved",
                    source=self.name,
                    payload={"query_id": query.id, "query_name": query.name}
                )

            return query.id

        except Exception as e:
            self._logger.error(f"Failed to save query: {e}")
            raise PluginError(f"Failed to save query: {e}") from e

    async def delete_query(self, query_id: str) -> bool:
        """Delete a saved query."""
        try:
            if query_id not in self._saved_queries:
                return False

            query_name = self._saved_queries[query_id].name
            del self._saved_queries[query_id]
            await self._save_saved_queries()

            self._logger.info(f"Deleted query: {query_name} ({query_id})")

            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/query_deleted",
                    source=self.name,
                    payload={"query_id": query_id, "query_name": query_name}
                )

            return True

        except Exception as e:
            self._logger.error(f"Failed to delete query: {e}")
            raise PluginError(f"Failed to delete query: {e}") from e

    # ============================================================================
    # UI EVENT HANDLERS (placeholders for when UI is implemented)
    # ============================================================================

    async def _open_connection_manager(self) -> None:
        """Open connection manager UI."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_connection_manager())
            )
            return

        # TODO: Implement when UI is ready
        self._logger.info("Connection manager requested (UI not yet implemented)")

    async def _open_query_editor(self) -> None:
        """Open query editor UI."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_query_editor())
            )
            return

        # TODO: Implement when UI is ready
        self._logger.info("Query editor requested (UI not yet implemented)")

    async def _open_field_mappings(self) -> None:
        """Open field mappings UI."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_field_mappings())
            )
            return

        # TODO: Implement when UI is ready
        self._logger.info("Field mappings requested (UI not yet implemented)")

    async def _open_validation(self) -> None:
        """Open validation UI."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_validation())
            )
            return

        # TODO: Implement when UI is ready
        self._logger.info("Validation UI requested (UI not yet implemented)")

    async def _open_history_manager(self) -> None:
        """Open history manager UI."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_history_manager())
            )
            return

        # TODO: Implement when UI is ready
        self._logger.info("History manager requested (UI not yet implemented)")

    # ============================================================================
    # PLUGIN DATA MANAGEMENT (settings and saved queries in plugin_data)
    # ============================================================================

    async def _find_plugin_directory(self) -> Optional[Path]:
        """Find the plugin directory."""
        import inspect
        try:
            module_path = inspect.getmodule(self).__file__
            if module_path:
                return Path(module_path).parent.parent
        except (AttributeError, TypeError):
            pass
        return None

    async def _load_settings(self) -> None:
        """Load plugin settings from plugin_data directory."""
        try:
            file_path = f"{self.name}/settings.json"
            try:
                file_info = await self._file_manager.get_file_info(file_path, "plugin_data")
                if not file_info:
                    # Create default settings
                    self._settings = PluginSettings()
                    await self._save_settings()
                    return
            except Exception:
                self._settings = PluginSettings()
                return

            json_data = await self._file_manager.read_text(file_path, "plugin_data")
            settings_dict = json.loads(json_data)
            self._settings = PluginSettings(**settings_dict)

            self._logger.debug("Loaded plugin settings")

        except Exception as e:
            self._logger.error(f"Failed to load settings: {e}")
            self._settings = PluginSettings()

    async def _save_settings(self) -> None:
        """Save plugin settings to plugin_data directory."""
        try:
            if not self._settings:
                return

            file_path = f"{self.name}/settings.json"
            await self._file_manager.ensure_directory(self.name, "plugin_data")

            settings_dict = self._settings.model_dump()
            json_data = json.dumps(settings_dict, indent=2, default=str)

            await self._file_manager.write_text(file_path, json_data, "plugin_data")
            self._logger.debug("Saved plugin settings")

        except Exception as e:
            self._logger.error(f"Failed to save settings: {e}")
            raise PluginError(f"Failed to save settings: {e}") from e

    async def _load_saved_queries(self) -> None:
        """Load saved queries from plugin_data directory."""
        try:
            file_path = f"{self.name}/saved_queries.json"
            try:
                file_info = await self._file_manager.get_file_info(file_path, "plugin_data")
                if not file_info:
                    return
            except Exception:
                return

            json_data = await self._file_manager.read_text(file_path, "plugin_data")
            data = json.loads(json_data)

            queries = {}
            for query_data in data:
                try:
                    # Handle datetime fields
                    if "created_at" in query_data and isinstance(query_data["created_at"], str):
                        query_data["created_at"] = datetime.datetime.fromisoformat(query_data["created_at"])
                    if "updated_at" in query_data and isinstance(query_data["updated_at"], str):
                        query_data["updated_at"] = datetime.datetime.fromisoformat(query_data["updated_at"])

                    query = SavedQuery(**query_data)
                    queries[query.id] = query
                except Exception as e:
                    self._logger.warning(f"Failed to load query: {e}")
                    continue

            self._saved_queries = queries
            self._logger.info(f"Loaded {len(queries)} saved queries")

        except Exception as e:
            self._logger.error(f"Failed to load saved queries: {e}")
            raise PluginError(f"Failed to load saved queries: {e}") from e

    async def _save_saved_queries(self) -> None:
        """Save queries to plugin_data directory."""
        try:
            file_path = f"{self.name}/saved_queries.json"
            await self._file_manager.ensure_directory(self.name, "plugin_data")

            query_list = []
            for query in self._saved_queries.values():
                query_dict = query.model_dump()
                # Convert datetime to ISO string
                if "created_at" in query_dict and isinstance(query_dict["created_at"], datetime.datetime):
                    query_dict["created_at"] = query_dict["created_at"].isoformat()
                if "updated_at" in query_dict and isinstance(query_dict["updated_at"], datetime.datetime):
                    query_dict["updated_at"] = query_dict["updated_at"].isoformat()
                query_list.append(query_dict)

            json_data = json.dumps(query_list, indent=2)
            await self._file_manager.write_text(file_path, json_data, "plugin_data")

            self._logger.debug(f"Saved {len(query_list)} queries")

        except Exception as e:
            self._logger.error(f"Failed to save queries: {e}")
            raise PluginError(f"Failed to save queries: {e}") from e

    async def _on_config_changed(self, event: Any) -> None:
        """Handle configuration changes."""
        if not event.payload.get("key", "").startswith(f"plugins.{self.name}"):
            return

        self._logger.info(f"Configuration changed: {event.payload.get('key')} = {event.payload.get('value')}")
        await self._load_settings()

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        if not self._initialized:
            return

        self._logger.info(f"Shutting down {self.name} plugin")

        try:
            await set_plugin_state(self.name, PluginLifecycleState.DISABLING)

            # Save plugin data
            try:
                await self._save_settings()
                await self._save_saved_queries()
            except Exception as e:
                self._logger.warning(f"Error saving plugin data during shutdown: {e}")

            # Clean up UI
            self._main_widget = None

            # Unsubscribe from events
            if self._event_bus_manager:
                await self._event_bus_manager.unsubscribe(
                    subscriber_id=f"{self.name}_config_subscriber"
                )

            # Clear state
            self._saved_queries = {}

            await super().shutdown()
            self._initialized = False
            await set_plugin_state(self.name, PluginLifecycleState.INACTIVE)
            self._logger.info(f"{self.name} plugin shutdown complete")

        except Exception as e:
            self._logger.error(f"Error during plugin shutdown: {e}")
            raise PluginError(f"Error during plugin shutdown: {e}") from e

    def status(self) -> Dict[str, Any]:
        """Get plugin status."""
        connection_count = 0
        if self._database_manager:
            try:
                connection_names = asyncio.create_task(self._database_manager.get_connection_names())
                connection_count = len(connection_names.result()) if connection_names.done() else 0
            except Exception:
                pass

        status = {
            "name": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "database_manager_available": self._database_manager is not None,
            "connections": {"available": connection_count},
            "queries": {"saved": len(self._saved_queries)},
            "ui_active": self._main_widget is not None,
        }

        if self._settings:
            status["settings"] = {
                "recent_connections": len(self._settings.recent_connections),
                "has_default_connection": self._settings.default_connection_id is not None,
                "query_limit": self._settings.query_limit,
            }

        return status