from __future__ import annotations

"""
Base connector interface for the Database Connector Plugin.

This module provides the base interface that all database connectors must implement,
defining a consistent API for interacting with different database systems.
"""
import abc
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Protocol, TypeVar

from ..models import BaseConnectionConfig, ColumnMetadata, QueryResult, TableMetadata

TableList = List[TableMetadata]
FieldList = List[ColumnMetadata]
T = TypeVar('T', bound=BaseConnectionConfig)


class DatabaseConnectorProtocol(Protocol[T]):
    """Protocol defining the interface for database connectors."""

    @property
    def config(self) -> T:
        """Get the connection configuration."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if the database is connected."""
        ...

    async def connect(self) -> None:
        """Connect to the database."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        ...

    async def execute_query(
            self, query: str, params: Optional[Dict[str, Any]] = None, limit: Optional[int] = None
    ) -> QueryResult:
        """Execute a query against the database."""
        ...

    async def get_tables(self, schema: Optional[str] = None) -> TableList:
        """Get a list of tables from the database."""
        ...

    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> FieldList:
        """Get a list of columns for a specific table."""
        ...

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test the database connection."""
        ...

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the database connection."""
        ...

    def set_database_manager(self, db_manager: Any) -> None:
        """Set the database manager instance."""
        ...


class BaseDatabaseConnector(abc.ABC):
    """Base class for database connectors."""

    def __init__(
            self,
            config: BaseConnectionConfig,
            logger: Any,
            database_manager: Optional[Any] = None,
            security_manager: Optional[Any] = None
    ) -> None:
        """Initialize the database connector.

        Args:
            config: Connection configuration
            logger: Logger for logging messages
            database_manager: Optional database manager for centralized operations
            security_manager: Optional security manager for security checks
        """
        self._config = config
        self._logger = logger if logger else logging.getLogger(__name__)
        self._database_manager = database_manager
        self._security_manager = security_manager
        self._connected = False
        self._connect_lock = asyncio.Lock()
        self._last_error: Optional[str] = None
        self._last_connect_time: Optional[float] = None
        self._query_cancel_event: Optional[asyncio.Event] = None
        self._accessed_tables: Set[str] = set()

    @property
    def config(self) -> BaseConnectionConfig:
        """Get the connection configuration.

        Returns:
            The connection configuration
        """
        return self._config

    @property
    def is_connected(self) -> bool:
        """Check if the database is connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    @property
    def database_manager(self) -> Optional[Any]:
        """Get the database manager.

        Returns:
            The database manager instance if available, None otherwise
        """
        return self._database_manager

    @abc.abstractmethod
    async def connect(self) -> None:
        """Connect to the database.

        This method must be implemented by derived classes.

        Raises:
            DatabaseError: If connection fails
        """
        pass

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the database.

        This method must be implemented by derived classes.

        Raises:
            DatabaseError: If disconnection fails
        """
        pass

    @abc.abstractmethod
    async def execute_query(
            self, query: str, params: Optional[Dict[str, Any]] = None, limit: Optional[int] = None
    ) -> QueryResult:
        """Execute a query against the database.

        This method must be implemented by derived classes.

        Args:
            query: SQL query to execute
            params: Optional query parameters
            limit: Optional result limit

        Returns:
            Query result

        Raises:
            DatabaseError: If query execution fails
            SecurityError: If query is not allowed
        """
        pass

    @abc.abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> TableList:
        """Get a list of tables from the database.

        This method must be implemented by derived classes.

        Args:
            schema: Optional schema name

        Returns:
            List of table metadata

        Raises:
            DatabaseError: If retrieving tables fails
        """
        pass

    @abc.abstractmethod
    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> FieldList:
        """Get a list of columns for a specific table.

        This method must be implemented by derived classes.

        Args:
            table_name: Table name
            schema: Optional schema name

        Returns:
            List of column metadata

        Raises:
            DatabaseError: If retrieving columns fails
        """
        pass

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test the database connection.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not self._connected:
                await self.connect()

            await self.execute_query('SELECT 1')
            return (True, None)
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._last_error = sanitized_error
            return (False, sanitized_error)
        finally:
            if self._connected:
                await self.disconnect()

    async def cancel_query(self) -> bool:
        """Cancel a running query.

        Returns:
            True if query was canceled, False otherwise
        """
        if self._query_cancel_event is not None:
            self._query_cancel_event.set()
            return True
        return False

    @abc.abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the database connection.

        Returns:
            Dictionary of connection information
        """
        pass

    def set_database_manager(self, db_manager: Any) -> None:
        """Set the database manager.

        Args:
            db_manager: Database manager to use
        """
        self._database_manager = db_manager
        self._logger.debug(f'Database manager set for connector {self._config.id}')

    def _sanitize_error_message(self, error_message: str) -> str:
        """Sanitize error messages to remove sensitive information.

        Args:
            error_message: Original error message

        Returns:
            Sanitized error message
        """
        if hasattr(self._config, 'password') and self._config.password:
            try:
                password = self._config.password.get_secret_value()
                error_message = error_message.replace(password, '[REDACTED]')
            except Exception:
                pass

        if hasattr(self._config, 'username'):
            error_message = error_message.replace(self._config.username, '[USERNAME]')

        return error_message

    def _sanitize_sql_for_logging(self, query: str) -> str:
        """Sanitize SQL queries for logging.

        Args:
            query: SQL query

        Returns:
            Sanitized SQL query
        """
        return query.replace('\n', ' ').replace('\r', ' ')

    def _create_query_result(self, query: str) -> QueryResult:
        """Create a new QueryResult object with common fields initialized.

        Args:
            query: SQL query

        Returns:
            Initialized QueryResult object
        """
        return QueryResult(
            query=query,
            connection_id=self._config.id,
            executed_at=datetime.now()
        )

    def _register_accessed_table(self, table_name: Optional[str]) -> None:
        """Register a table as being accessed by this connection.

        Args:
            table_name: Table name that was accessed
        """
        if table_name:
            self._accessed_tables.add(table_name.upper())