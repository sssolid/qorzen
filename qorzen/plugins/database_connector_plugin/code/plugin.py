"""
Main plugin module for the Database Connector Plugin.

This module provides a comprehensive UI layer over the core DatabaseManager 
functionality, allowing users to manage database connections, execute queries, 
view results, manage field mappings, validation rules, and history schedules.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from qorzen.core.database_manager import DatabaseConnectionConfig, ConnectionType
from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.lifecycle import (
    PluginLifecycleState,
    get_plugin_state,
    set_plugin_state,
    signal_ui_ready
)
from qorzen.utils.exceptions import PluginError

from .models import (
    DatabaseConnection,
    SavedQuery,
    PluginSettings,
    QueryResult,
    FieldMapping,
    ValidationRule,
    HistorySchedule,
    ExportSettings,
    ExportFormat
)
from .ui.main_widget import DatabasePluginWidget
from .services.export_service import ExportService
from .services.query_service import QueryService


class DatabaseConnectorPlugin(BasePlugin):
    """
    Advanced Database Connector Plugin.

    Provides comprehensive database management capabilities including:
    - Connection management with multiple database types
    - Advanced query editor with syntax highlighting
    - Results visualization and export
    - Field mapping management
    - Data validation rules
    - Historical data tracking
    """

    name = "database_connector_plugin"
    version = "2.0.0"
    description = "Advanced database connectivity and management plugin"
    author = "Qorzen Team"
    display_name = "Database Connector"
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._logger: Optional[logging.Logger] = None
        self._event_bus_manager: Any = None
        self._config_manager: Any = None
        self._task_manager: Any = None
        self._database_manager: Any = None
        self._concurrency_manager: Any = None
        self._security_manager: Any = None
        self._file_manager: Any = None

        # Plugin state
        self._initialized = False
        self._settings: Optional[PluginSettings] = None
        self._main_widget: Optional[QWidget] = None

        # Data storage
        self._connections: Dict[str, DatabaseConnection] = {}
        self._saved_queries: Dict[str, SavedQuery] = {}

        # Services
        self._export_service: Optional[ExportService] = None
        self._query_service: Optional[QueryService] = None

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin with application core services.

        Args:
            application_core: The application core instance
            **kwargs: Additional initialization parameters
        """
        await super().initialize(application_core, **kwargs)

        self._logger = logging.getLogger(self.name)
        self._logger.info(f"Initializing {self.name} plugin v{self.version}")

        # Get required managers
        self._event_bus_manager = application_core.get_manager("event_bus_manager")
        self._config_manager = application_core.get_manager("config_manager")
        self._task_manager = application_core.get_manager("task_manager")
        self._database_manager = application_core.get_manager("database_manager")
        self._concurrency_manager = application_core.get_manager("concurrency_manager")
        self._security_manager = application_core.get_manager("security_manager")
        self._file_manager = application_core.get_manager("file_manager")

        # Validate required dependencies
        if not self._database_manager:
            raise PluginError("DatabaseManager is required but not available")
        if not self._file_manager:
            raise PluginError("FileManager is required but not available")
        if not self._concurrency_manager:
            raise PluginError("ConcurrencyManager is required but not available")

        # Setup plugin data directory
        try:
            await self._file_manager.ensure_directory(self.name, "plugin_data")
            self._logger.debug(f"Plugin data directory ensured: {self.name}")
        except Exception as e:
            self._logger.warning(f"Failed to create plugin data directory: {e}")

        # Initialize services
        self._export_service = ExportService(self._file_manager, self._logger)
        self._query_service = QueryService(self._database_manager, self._logger)

        # Load plugin data
        try:
            await self._load_settings()
            await self._load_connections()
            await self._load_saved_queries()
        except Exception as e:
            self._logger.error(f"Error loading plugin data: {e}")

        # Setup event listeners
        if self._event_bus_manager:
            await self._event_bus_manager.subscribe(
                event_type="config/changed",
                callback=self._on_config_changed,
                subscriber_id=f"{self.name}_config_subscriber"
            )

        self._initialized = True
        await set_plugin_state(self.name, PluginLifecycleState.INITIALIZED)
        self._logger.info(f"{self.name} plugin initialized successfully")

        # Publish initialization event
        if self._event_bus_manager:
            await self._event_bus_manager.publish(
                event_type="plugin/initialized",
                source=self.name,
                payload={
                    "plugin_name": self.name,
                    "version": self.version,
                    "has_ui": True,
                    "features": [
                        "connection_management",
                        "query_editor",
                        "results_export",
                        "field_mapping",
                        "data_validation",
                        "history_tracking"
                    ]
                }
            )

    async def on_ui_ready(self, ui_integration: Any) -> None:
        """
        Setup UI components when the UI is ready.

        Args:
            ui_integration: The UI integration interface
        """
        self._logger.info("Setting up UI components")

        # Check current state to avoid recursive calls
        current_state = await get_plugin_state(self.name)
        if current_state == PluginLifecycleState.UI_READY:
            self._logger.debug("UI setup already in progress, avoiding recursive call")
            return

        # Ensure we're on the main thread
        if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
            self._logger.debug("on_ui_ready called from non-main thread, delegating to main thread")
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self.on_ui_ready(ui_integration))
            )
            return

        try:
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)

            # Create main widget
            if not self._main_widget:
                self._main_widget = DatabasePluginWidget(
                    plugin=self,
                    logger=self._logger,
                    concurrency_manager=self._concurrency_manager,
                    event_bus_manager=self._event_bus_manager
                )

            # Add menu items
            await self._setup_menu_items(ui_integration)

            # Get icon path
            icon_arg = None
            if self.plugin_info and self.plugin_info.path:
                plugin_path = Path(self.plugin_info.path)
                if hasattr(self.plugin_info, "manifest") and hasattr(self.plugin_info.manifest, "icon_path"):
                    icon_file = plugin_path / self.plugin_info.manifest.icon_path
                    if icon_file.exists():
                        icon_arg = str(icon_file)
                else:
                    # Try default icon location
                    icon_file = plugin_path / "resources" / "icon.png"
                    if icon_file.exists():
                        icon_arg = str(icon_file)

            # Add main page
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
            raise

    async def setup_ui(self, ui_integration: Any) -> None:
        """
        Set up UI components (legacy method).

        Args:
            ui_integration: The UI integration instance
        """
        if self._logger:
            self._logger.info("setup_ui method called")
        await self.on_ui_ready(ui_integration)

    async def _setup_menu_items(self, ui_integration: Any) -> None:
        """Setup menu items for the plugin."""
        await ui_integration.add_menu_item(
            plugin_id=self.plugin_id,
            parent_menu="Database",
            title="Connection Manager",
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

    # Connection Management
    async def get_connections(self) -> List[DatabaseConnection]:
        """Get all saved database connections."""
        return list(self._connections.values())

    async def create_connection(self, connection: DatabaseConnection) -> str:
        """
        Create a new database connection.

        Args:
            connection: The connection configuration

        Returns:
            The connection ID
        """
        try:
            # Convert to database manager config
            config = self._convert_to_db_config(connection)

            # Test the connection first
            is_valid, error = await self._database_manager.test_connection_config(config)
            if not is_valid:
                raise PluginError(f"Connection test failed: {error}")

            # Register with database manager
            await self._database_manager.register_connection(config)

            # Save locally
            connection.updated_at = connection.created_at
            self._connections[connection.id] = connection
            await self._save_connections()

            # Update recent connections
            if self._settings:
                if connection.id in self._settings.recent_connections:
                    self._settings.recent_connections.remove(connection.id)
                self._settings.recent_connections.insert(0, connection.id)
                self._settings.recent_connections = self._settings.recent_connections[
                                                    :self._settings.max_recent_connections]
                await self._save_settings()

            self._logger.info(f"Created connection: {connection.name}")

            # Publish event
            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/connection_created",
                    source=self.name,
                    payload={"connection_id": connection.id, "connection_name": connection.name}
                )

            return connection.id

        except Exception as e:
            self._logger.error(f"Failed to create connection: {e}")
            raise PluginError(f"Failed to create connection: {e}") from e

    async def update_connection(self, connection: DatabaseConnection) -> None:
        """
        Update an existing database connection.

        Args:
            connection: The updated connection configuration
        """
        try:
            if connection.id not in self._connections:
                raise PluginError(f"Connection {connection.id} not found")

            # Test the connection first
            config = self._convert_to_db_config(connection)
            is_valid, error = await self._database_manager.test_connection_config(config)
            if not is_valid:
                raise PluginError(f"Connection test failed: {error}")

            # Unregister old connection
            await self._database_manager.unregister_connection(connection.name)

            # Register updated connection
            await self._database_manager.register_connection(config)

            # Update locally
            from datetime import datetime
            connection.updated_at = datetime.now()
            self._connections[connection.id] = connection
            await self._save_connections()

            self._logger.info(f"Updated connection: {connection.name}")

            # Publish event
            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/connection_updated",
                    source=self.name,
                    payload={"connection_id": connection.id, "connection_name": connection.name}
                )

        except Exception as e:
            self._logger.error(f"Failed to update connection: {e}")
            raise PluginError(f"Failed to update connection: {e}") from e

    async def delete_connection(self, connection_id: str) -> bool:
        """
        Delete a database connection.

        Args:
            connection_id: The connection ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            if connection_id not in self._connections:
                return False

            connection = self._connections[connection_id]

            # Unregister from database manager
            try:
                await self._database_manager.unregister_connection(connection.name)
            except Exception as e:
                self._logger.warning(f"Failed to unregister connection from database manager: {e}")

            # Remove locally
            del self._connections[connection_id]
            await self._save_connections()

            # Remove from recent connections
            if self._settings and connection_id in self._settings.recent_connections:
                self._settings.recent_connections.remove(connection_id)
                await self._save_settings()

            self._logger.info(f"Deleted connection: {connection.name}")

            # Publish event
            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/connection_deleted",
                    source=self.name,
                    payload={"connection_id": connection_id, "connection_name": connection.name}
                )

            return True

        except Exception as e:
            self._logger.error(f"Failed to delete connection: {e}")
            return False

    async def test_connection(self, connection_id: str) -> Tuple[bool, Optional[str]]:
        """
        Test a database connection.

        Args:
            connection_id: The connection ID to test

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if connection_id not in self._connections:
                return (False, "Connection not found")

            connection = self._connections[connection_id]
            config = self._convert_to_db_config(connection)

            is_connected, error = await self._database_manager.test_connection_config(config)

            # Update last tested time
            from datetime import datetime
            connection.last_tested = datetime.now()
            await self._save_connections()

            return (is_connected, error)

        except Exception as e:
            error_msg = str(e)
            self._logger.error(f"Connection test failed: {error_msg}")
            return (False, error_msg)

    # Query Management
    async def get_saved_queries(self, connection_id: Optional[str] = None) -> List[SavedQuery]:
        """Get saved queries, optionally filtered by connection."""
        if connection_id:
            return [q for q in self._saved_queries.values() if q.connection_id == connection_id]
        return list(self._saved_queries.values())

    async def save_query(self, query: SavedQuery) -> str:
        """
        Save a database query.

        Args:
            query: The query to save

        Returns:
            The query ID
        """
        try:
            from datetime import datetime
            query.updated_at = datetime.now()
            self._saved_queries[query.id] = query
            await self._save_saved_queries()

            self._logger.info(f"Saved query: {query.name}")

            # Publish event
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
        """
        Delete a saved query.

        Args:
            query_id: The query ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            if query_id not in self._saved_queries:
                return False

            query_name = self._saved_queries[query_id].name
            del self._saved_queries[query_id]
            await self._save_saved_queries()

            self._logger.info(f"Deleted query: {query_name}")

            # Publish event
            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/query_deleted",
                    source=self.name,
                    payload={"query_id": query_id, "query_name": query_name}
                )

            return True

        except Exception as e:
            self._logger.error(f"Failed to delete query: {e}")
            return False

    # Query Execution
    async def execute_query(
            self,
            connection_id: str,
            query: str,
            parameters: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            apply_mapping: bool = False
    ) -> QueryResult:
        """
        Execute a database query.

        Args:
            connection_id: The connection ID to use
            query: The SQL query to execute
            parameters: Query parameters
            limit: Row limit for results
            apply_mapping: Whether to apply field mappings

        Returns:
            Query execution results
        """
        try:
            if connection_id not in self._connections:
                raise PluginError(f"Connection {connection_id} not found")

            connection = self._connections[connection_id]

            # Use query service to execute
            result = await self._query_service.execute_query(
                connection_name=connection.name,
                query=query,
                parameters=parameters or {},
                limit=limit or (self._settings.query_limit if self._settings else 1000),
                apply_mapping=apply_mapping
            )

            # Convert to QueryResult model
            query_result = QueryResult(
                connection_id=connection_id,
                query=query,
                parameters=parameters or {},
                records=result.get("records", []),
                columns=result.get("columns", []),
                row_count=result.get("row_count", 0),
                execution_time_ms=result.get("execution_time_ms", 0),
                has_error=result.get("has_error", False),
                error_message=result.get("error_message"),
                truncated=result.get("truncated", False),
                applied_mapping=apply_mapping
            )

            self._logger.info(f"Executed query on {connection.name}, returned {query_result.row_count} rows")

            # Publish event
            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/query_executed",
                    source=self.name,
                    payload={
                        "connection_id": connection_id,
                        "row_count": query_result.row_count,
                        "execution_time_ms": query_result.execution_time_ms
                    }
                )

            return query_result

        except Exception as e:
            self._logger.error(f"Failed to execute query: {e}")
            raise PluginError(f"Failed to execute query: {e}") from e

    # Export functionality
    async def export_results(
            self,
            results: QueryResult,
            format: ExportFormat,
            file_path: str,
            settings: Optional[ExportSettings] = None
    ) -> str:
        """
        Export query results to a file.

        Args:
            results: The query results to export
            format: The export format
            file_path: The output file path
            settings: Export settings

        Returns:
            The exported file path
        """
        try:
            export_settings = settings or (self._settings.export_settings if self._settings else ExportSettings())

            return await self._export_service.export_results(
                results=results,
                format=format,
                file_path=file_path,
                settings=export_settings
            )

        except Exception as e:
            self._logger.error(f"Failed to export results: {e}")
            raise PluginError(f"Failed to export results: {e}") from e

    # Database introspection
    async def get_tables(self, connection_id: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tables from a database connection."""
        try:
            if connection_id not in self._connections:
                raise PluginError(f"Connection {connection_id} not found")

            connection = self._connections[connection_id]
            return await self._database_manager.get_tables(connection.name, schema)

        except Exception as e:
            self._logger.error(f"Failed to get tables: {e}")
            raise PluginError(f"Failed to get tables: {e}") from e

    async def get_table_columns(
            self,
            connection_id: str,
            table_name: str,
            schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get columns from a database table."""
        try:
            if connection_id not in self._connections:
                raise PluginError(f"Connection {connection_id} not found")

            connection = self._connections[connection_id]
            return await self._database_manager.get_table_columns(table_name, connection.name, schema)

        except Exception as e:
            self._logger.error(f"Failed to get table columns: {e}")
            raise PluginError(f"Failed to get table columns: {e}") from e

    # Field Mapping Management
    async def get_field_mappings(self, connection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get field mappings."""
        try:
            return await self._database_manager.get_all_field_mappings(connection_id)
        except Exception as e:
            self._logger.error(f"Failed to get field mappings: {e}")
            return []

    async def create_field_mapping(
            self,
            connection_id: str,
            table_name: str,
            mappings: Dict[str, str],
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a field mapping."""
        try:
            if connection_id not in self._connections:
                raise PluginError(f"Connection {connection_id} not found")

            connection = self._connections[connection_id]
            return await self._database_manager.create_field_mapping(
                connection.name, table_name, mappings, description
            )

        except Exception as e:
            self._logger.error(f"Failed to create field mapping: {e}")
            raise PluginError(f"Failed to create field mapping: {e}") from e

    async def delete_field_mapping(self, mapping_id: str) -> bool:
        """Delete a field mapping."""
        try:
            return await self._database_manager.delete_field_mapping(mapping_id)
        except Exception as e:
            self._logger.error(f"Failed to delete field mapping: {e}")
            return False

    # Validation Management
    async def get_validation_rules(
            self,
            connection_id: Optional[str] = None,
            table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get validation rules."""
        try:
            connection_name = None
            if connection_id and connection_id in self._connections:
                connection_name = self._connections[connection_id].name

            return await self._database_manager.get_all_validation_rules(connection_name, table_name)
        except Exception as e:
            self._logger.error(f"Failed to get validation rules: {e}")
            return []

    async def create_validation_rule(
            self,
            rule_type: str,
            connection_id: str,
            table_name: str,
            field_name: str,
            parameters: Dict[str, Any],
            error_message: str,
            name: Optional[str] = None,
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a validation rule."""
        try:
            if connection_id not in self._connections:
                raise PluginError(f"Connection {connection_id} not found")

            connection = self._connections[connection_id]
            return await self._database_manager.create_validation_rule(
                rule_type, connection.name, table_name, field_name,
                parameters, error_message, name, description
            )

        except Exception as e:
            self._logger.error(f"Failed to create validation rule: {e}")
            raise PluginError(f"Failed to create validation rule: {e}") from e

    async def validate_data(
            self,
            connection_id: str,
            table_name: str,
            data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate data against rules."""
        try:
            if connection_id not in self._connections:
                raise PluginError(f"Connection {connection_id} not found")

            connection = self._connections[connection_id]
            return await self._database_manager.validate_data(connection.name, table_name, data)

        except Exception as e:
            self._logger.error(f"Failed to validate data: {e}")
            raise PluginError(f"Failed to validate data: {e}") from e

    # History Management
    async def get_history_schedules(self) -> List[Dict[str, Any]]:
        """Get history schedules."""
        try:
            return await self._database_manager.get_all_history_schedules()
        except Exception as e:
            self._logger.error(f"Failed to get history schedules: {e}")
            return []

    async def create_history_schedule(
            self,
            connection_id: str,
            query_id: str,
            frequency: str,
            name: str,
            description: Optional[str] = None,
            retention_days: int = 365
    ) -> Dict[str, Any]:
        """Create a history schedule."""
        try:
            if connection_id not in self._connections:
                raise PluginError(f"Connection {connection_id} not found")

            connection = self._connections[connection_id]
            return await self._database_manager.create_history_schedule(
                connection.name, query_id, frequency, name, description, retention_days
            )

        except Exception as e:
            self._logger.error(f"Failed to create history schedule: {e}")
            raise PluginError(f"Failed to create history schedule: {e}") from e

    # Settings and Configuration
    async def get_settings(self) -> PluginSettings:
        """Get plugin settings."""
        return self._settings or PluginSettings()

    async def update_settings(self, settings: PluginSettings) -> None:
        """Update plugin settings."""
        try:
            self._settings = settings
            await self._save_settings()

            self._logger.info("Plugin settings updated")

            # Publish event
            if self._event_bus_manager:
                await self._event_bus_manager.publish(
                    event_type="database_connector/settings_updated",
                    source=self.name,
                    payload={"settings": settings.model_dump()}
                )

        except Exception as e:
            self._logger.error(f"Failed to update settings: {e}")
            raise PluginError(f"Failed to update settings: {e}") from e

    # Helper Methods
    def _convert_to_db_config(self, connection: DatabaseConnection) -> DatabaseConnectionConfig:
        """Convert plugin connection to database manager config."""
        return DatabaseConnectionConfig(
            name=connection.name,
            db_type=connection.connection_type.value,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            user=connection.user,
            password=connection.password,
            connection_string=connection.connection_string,
            ssl=connection.ssl,
            read_only=connection.read_only,
            pool_size=connection.pool_size,
            max_overflow=connection.max_overflow,
            pool_recycle=connection.pool_recycle,
            connection_timeout=connection.connection_timeout,
            properties=connection.properties,
            allowed_tables=connection.allowed_tables,
            dsn=connection.dsn,
            jt400_jar_path=connection.jt400_jar_path
        )

    # Menu handlers
    async def _open_connection_manager(self) -> None:
        """Open connection manager."""
        if self._main_widget:
            # Switch to connections tab
            self._main_widget.switch_to_tab(0)

    async def _open_query_editor(self) -> None:
        """Open query editor."""
        if self._main_widget:
            # Switch to main tab
            self._main_widget.switch_to_tab(0)

    async def _open_field_mappings(self) -> None:
        """Open field mappings."""
        if self._main_widget:
            # Switch to field mapping tab
            self._main_widget.switch_to_tab(2)

    async def _open_validation(self) -> None:
        """Open validation."""
        if self._main_widget:
            # Switch to validation tab
            self._main_widget.switch_to_tab(3)

    async def _open_history_manager(self) -> None:
        """Open history manager."""
        if self._main_widget:
            # Switch to history tab
            self._main_widget.switch_to_tab(4)

    # Data persistence
    async def _load_settings(self) -> None:
        """Load plugin settings from file."""
        try:
            file_path = f"{self.name}/settings.json"

            try:
                file_info = await self._file_manager.get_file_info(file_path, "plugin_data")
                if not file_info:
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
        """Save plugin settings to file."""
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

    async def _load_connections(self) -> None:
        """Load database connections from file."""
        try:
            file_path = f"{self.name}/connections.json"

            try:
                file_info = await self._file_manager.get_file_info(file_path, "plugin_data")
                if not file_info:
                    return
            except Exception:
                return

            json_data = await self._file_manager.read_text(file_path, "plugin_data")
            data = json.loads(json_data)

            connections = {}
            for conn_data in data:
                try:
                    # Handle datetime fields
                    if "created_at" in conn_data and isinstance(conn_data["created_at"], str):
                        from datetime import datetime
                        conn_data["created_at"] = datetime.fromisoformat(conn_data["created_at"])
                    if "updated_at" in conn_data and isinstance(conn_data["updated_at"], str):
                        from datetime import datetime
                        conn_data["updated_at"] = datetime.fromisoformat(conn_data["updated_at"])
                    if "last_tested" in conn_data and isinstance(conn_data["last_tested"], str):
                        from datetime import datetime
                        conn_data["last_tested"] = datetime.fromisoformat(conn_data["last_tested"])

                    connection = DatabaseConnection(**conn_data)
                    connections[connection.id] = connection

                except Exception as e:
                    self._logger.warning(f"Failed to load connection: {e}")
                    continue

            self._connections = connections
            self._logger.info(f"Loaded {len(connections)} database connections")

        except Exception as e:
            self._logger.error(f"Failed to load connections: {e}")

    async def _save_connections(self) -> None:
        """Save database connections to file."""
        try:
            file_path = f"{self.name}/connections.json"
            await self._file_manager.ensure_directory(self.name, "plugin_data")

            connection_list = []
            for connection in self._connections.values():
                conn_dict = connection.model_dump()

                # Handle datetime fields
                if "created_at" in conn_dict and hasattr(conn_dict["created_at"], "isoformat"):
                    conn_dict["created_at"] = conn_dict["created_at"].isoformat()
                if "updated_at" in conn_dict and hasattr(conn_dict["updated_at"], "isoformat"):
                    conn_dict["updated_at"] = conn_dict["updated_at"].isoformat()
                if "last_tested" in conn_dict and conn_dict["last_tested"] and hasattr(conn_dict["last_tested"],
                                                                                       "isoformat"):
                    conn_dict["last_tested"] = conn_dict["last_tested"].isoformat()

                connection_list.append(conn_dict)

            json_data = json.dumps(connection_list, indent=2)
            await self._file_manager.write_text(file_path, json_data, "plugin_data")

            self._logger.debug(f"Saved {len(connection_list)} connections")

        except Exception as e:
            self._logger.error(f"Failed to save connections: {e}")
            raise PluginError(f"Failed to save connections: {e}") from e

    async def _load_saved_queries(self) -> None:
        """Load saved queries from file."""
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
                        from datetime import datetime
                        query_data["created_at"] = datetime.fromisoformat(query_data["created_at"])
                    if "updated_at" in query_data and isinstance(query_data["updated_at"], str):
                        from datetime import datetime
                        query_data["updated_at"] = datetime.fromisoformat(query_data["updated_at"])
                    if "last_executed" in query_data and isinstance(query_data["last_executed"], str):
                        from datetime import datetime
                        query_data["last_executed"] = datetime.fromisoformat(query_data["last_executed"])

                    query = SavedQuery(**query_data)
                    queries[query.id] = query

                except Exception as e:
                    self._logger.warning(f"Failed to load query: {e}")
                    continue

            self._saved_queries = queries
            self._logger.info(f"Loaded {len(queries)} saved queries")

        except Exception as e:
            self._logger.error(f"Failed to load saved queries: {e}")

    async def _save_saved_queries(self) -> None:
        """Save queries to file."""
        try:
            file_path = f"{self.name}/saved_queries.json"
            await self._file_manager.ensure_directory(self.name, "plugin_data")

            query_list = []
            for query in self._saved_queries.values():
                query_dict = query.model_dump()

                # Handle datetime fields
                if "created_at" in query_dict and hasattr(query_dict["created_at"], "isoformat"):
                    query_dict["created_at"] = query_dict["created_at"].isoformat()
                if "updated_at" in query_dict and hasattr(query_dict["updated_at"], "isoformat"):
                    query_dict["updated_at"] = query_dict["updated_at"].isoformat()
                if "last_executed" in query_dict and query_dict["last_executed"] and hasattr(
                        query_dict["last_executed"], "isoformat"):
                    query_dict["last_executed"] = query_dict["last_executed"].isoformat()

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

            # Save all data
            try:
                await self._save_settings()
                await self._save_connections()
                await self._save_saved_queries()
            except Exception as e:
                self._logger.warning(f"Error saving plugin data during shutdown: {e}")

            # Cleanup UI
            self._main_widget = None

            # Unsubscribe from events
            if self._event_bus_manager:
                await self._event_bus_manager.unsubscribe(
                    subscriber_id=f"{self.name}_config_subscriber"
                )

            # Clear data
            self._connections = {}
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
        status = {
            "name": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "database_manager_available": self._database_manager is not None,
            "connections": {
                "total": len(self._connections),
                "active": len([c for c in self._connections.values() if c.is_active])
            },
            "queries": {
                "saved": len(self._saved_queries)
            },
            "ui_active": self._main_widget is not None,
            "services": {
                "export_service": self._export_service is not None,
                "query_service": self._query_service is not None
            }
        }

        if self._settings:
            status["settings"] = {
                "default_connection": self._settings.default_connection_id,
                "recent_connections": len(self._settings.recent_connections),
                "query_limit": self._settings.query_limit,
                "auto_limit_queries": self._settings.auto_limit_queries
            }

        return status