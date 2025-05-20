from __future__ import annotations

import re
import time

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

    class BaseDatabaseConnector(abc.ABC):
        def __init__(self, config: BaseConnectionConfig, logger: Any, security_manager: Optional[Any] = None) -> None:
            self._config = config
            self._logger = logger if logger else logging.getLogger(__name__)
            self._security_manager = security_manager
            self._database_manager: Optional[Any] = None
            self._connected = False
            self._connect_lock = asyncio.Lock()
            self._last_error: Optional[str] = None
            self._last_connect_time: Optional[float] = None
            self._query_cancel_event: Optional[asyncio.Event] = None
            self._accessed_tables: Set[str] = set()
            self._registered_connection_id: Optional[str] = None

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

    async def _register_with_database_manager(self) -> bool:
        """Register this connector with the database manager.

        Returns:
            bool: True if registration was successful, False otherwise
        """
        if not self._database_manager:
            return False

        try:
            # Create a unique connection ID for this connector
            self._registered_connection_id = f"{self._config.connection_type}_{self._config.id}"

            # Check if already registered
            if await self._database_manager.has_connection(self._registered_connection_id):
                self._logger.debug(f'Connection {self._registered_connection_id} already registered')
                return True

            # Create configuration for database manager
            db_config = self._create_database_manager_config()

            # Register the connection
            await self._database_manager.register_connection(db_config)
            self._logger.debug(f'Registered connection with database_manager: {self._registered_connection_id}')
            return True
        except Exception as e:
            self._logger.warning(f'Could not register connection with database_manager: {str(e)}')
            return False

    def _create_database_manager_config(self) -> Any:
        """Create a DatabaseConnectionConfig from this connector's config.

        This method should be overridden by subclasses for specific database types.

        Returns:
            Any: A DatabaseConnectionConfig instance
        """
        from qorzen.core.database_manager import DatabaseConnectionConfig

        return DatabaseConnectionConfig(
            name=self._registered_connection_id or f"{self._config.connection_type}_{self._config.id}",
            db_type=str(self._config.connection_type),
            host=getattr(self._config, 'host', getattr(self._config, 'server', '')),
            port=getattr(self._config, 'port', 0),
            database=self._config.database,
            user=getattr(self._config, 'username', ''),
            password=getattr(self._config, 'password', '').get_secret_value(),
            pool_size=1,
            max_overflow=0,
            pool_recycle=3600,
            echo=False,
            read_only=getattr(self._config, 'read_only', False)
        )

    async def _execute_query_with_database_manager(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None
    ) -> QueryResult:
        """Execute a query using the database manager.

        Args:
            query: SQL query to execute
            params: Query parameters
            limit: Maximum number of rows to return

        Returns:
            QueryResult: Query result

        Raises:
            DatabaseError: If query execution fails
        """
        from qorzen.utils.exceptions import DatabaseError

        if not self._database_manager or not self._registered_connection_id:
            raise DatabaseError(
                message="Cannot execute query with database manager: not registered",
                details={'connection_id': self._config.id}
            )

        start_time = time.time()

        try:
            # Execute the query
            if params:
                prepared_params = self._prepare_params_for_database_manager(params)
                records = await self._database_manager.execute_raw(
                    sql=query,
                    params=prepared_params,
                    connection_name=self._registered_connection_id
                )
            else:
                records = await self._database_manager.execute_raw(
                    sql=query,
                    connection_name=self._registered_connection_id
                )

            # Extract table name from query if possible
            table_name = None
            match = re.search(r'FROM\s+(["\[\]`]?\w+["\[\]`]?)', query.upper())
            if match:
                table_name = match.group(1).strip('"[]`')
                if table_name:
                    self._accessed_tables.add(table_name.upper())

            # Get column metadata from records
            columns = self._extract_columns_from_records(records, table_name)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Create and return the result
            result = QueryResult(
                query=query,
                connection_id=self._config.id,
                executed_at=datetime.now(),
                records=records,
                columns=columns,
                row_count=len(records),
                execution_time_ms=int(execution_time * 1000),
                truncated=limit is not None and len(records) >= limit
            )

            return result
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(
                f'Error executing query with database manager: {sanitized_error}',
                extra={'query': self._sanitize_sql_for_logging(query)}
            )

            # Create an error result
            result = QueryResult(
                query=query,
                connection_id=self._config.id,
                executed_at=datetime.now(),
                has_error=True,
                error_message=sanitized_error
            )

            # Re-raise the exception
            raise DatabaseError(
                message=f'Failed to execute query: {sanitized_error}',
                details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}
            ) from e

    def _prepare_params_for_database_manager(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for the database manager.

        This method can be overridden by subclasses for specific parameter conversion.

        Args:
            params: Parameters to prepare

        Returns:
            Dict[str, Any]: Prepared parameters
        """
        return params

    def _extract_columns_from_records(
            self,
            records: List[Dict[str, Any]],
            table_name: Optional[str]
    ) -> List[ColumnMetadata]:
        """Extract column metadata from query results.

        Args:
            records: Query result records
            table_name: Optional table name

        Returns:
            List[ColumnMetadata]: Column metadata
        """
        columns = []

        if not records:
            return columns

        # Get the first record to extract column information
        record = records[0]

        # Create column metadata for each field
        for name, value in record.items():
            type_name = self._get_type_name_from_value(value)
            type_code = self._get_type_code_from_name(type_name)

            precision = 0
            scale = 0

            if isinstance(value, (int, float)):
                precision = 10
                if isinstance(value, float):
                    scale = 2

            columns.append(ColumnMetadata(
                name=name,
                type_name=type_name,
                type_code=type_code,
                precision=precision,
                scale=scale,
                nullable=True,
                table_name=table_name
            ))

        return columns

    def _get_type_name_from_value(self, value: Any) -> str:
        """Get SQL type name from a Python value.

        Args:
            value: Value to get type for

        Returns:
            str: SQL type name
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'REAL'
        elif isinstance(value, str):
            return 'VARCHAR'
        elif isinstance(value, bytes):
            return 'BINARY'
        elif isinstance(value, bool):
            return 'BOOLEAN'
        elif hasattr(value, 'isoformat'):  # datetime or date
            if hasattr(value, 'hour'):  # datetime
                return 'TIMESTAMP'
            else:  # date
                return 'DATE'
        else:
            return 'VARCHAR'

    def _get_type_code_from_name(self, type_name: str) -> int:
        """Get type code from SQL type name.

        Args:
            type_name: SQL type name

        Returns:
            int: Type code
        """
        # Default implementation - subclasses can override
        type_codes = {
            'NULL': 0,
            'INTEGER': 4,
            'SMALLINT': 5,
            'DECIMAL': 3,
            'NUMERIC': 2,
            'FLOAT': 6,
            'REAL': 7,
            'DOUBLE': 8,
            'CHAR': 1,
            'VARCHAR': 12,
            'LONGVARCHAR': -1,
            'DATE': 91,
            'TIME': 92,
            'TIMESTAMP': 93,
            'BINARY': -2,
            'VARBINARY': -3,
            'BOOLEAN': 16
        }

        return type_codes.get(type_name, 0)