from __future__ import annotations

"""
SQLite database connector for the Database Connector Plugin.

This module provides a connector for SQLite databases using aiosqlite,
integrated with the asyncio-based architecture of the plugin.
"""

import asyncio
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import aiosqlite

from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError

from ..models import SQLiteConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
from .base import BaseDatabaseConnector


class SQLiteConnector(BaseDatabaseConnector):
    """SQLite database connector implementation."""

    def __init__(self, config: SQLiteConnectionConfig, logger: Any, security_manager: Optional[Any] = None) -> None:
        """Initialize SQLite connector.

        Args:
            config: The SQLite connection configuration
            logger: Logger for recording operations
            security_manager: Optional security manager
        """
        super().__init__(config, logger)
        self._config = config
        self._security_manager = security_manager
        self._connection: Optional[aiosqlite.Connection] = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None

        # Verify SQLite is available
        try:
            import sqlite3
            self._sqlite_version = sqlite3.sqlite_version
        except ImportError:
            self._logger.error("sqlite3 module is required for SQLite connections.")
            raise ImportError("sqlite3 module is required for SQLite connections.")

        # Verify aiosqlite is available
        try:
            import aiosqlite
        except ImportError:
            self._logger.error(
                "aiosqlite module is required for SQLite connections. Please install it with 'pip install aiosqlite'.")
            raise ImportError(
                "aiosqlite module is required for SQLite connections. Please install it with 'pip install aiosqlite'.")

    async def connect(self) -> None:
        """Connect to the SQLite database."""
        async with self._connect_lock:
            if self._connected:
                return

            try:
                db_path = self._config.database

                # Log connection attempt
                self._logger.info('Connecting to SQLite database', extra={
                    'database': db_path,
                    'read_only': self._config.read_only
                })

                start_time = time.time()

                # Handle in-memory database
                if db_path == ':memory:':
                    self._connection = await aiosqlite.connect(':memory:')
                else:
                    # Handle file path
                    db_path = os.path.abspath(os.path.expanduser(db_path))

                    # Check if path exists and create parent directories if needed
                    db_dir = os.path.dirname(db_path)
                    if not os.path.exists(db_dir):
                        os.makedirs(db_dir, exist_ok=True)

                    # Open connection with read-only flag if configured
                    uri_path = f"file:{db_path}"
                    if self._config.read_only:
                        uri_path += "?mode=ro"

                    self._connection = await aiosqlite.connect(
                        uri_path,
                        uri=True,
                        timeout=self._config.connection_timeout
                    )

                # Configure the connection
                await self._connection.execute("PRAGMA foreign_keys = ON")

                # Set row factory to return dictionaries
                self._connection.row_factory = self._dict_factory

                self._connection_time = time.time() - start_time
                self._connected = True

                # Log successful connection
                self._logger.info('Successfully connected to SQLite database', extra={
                    'database': db_path,
                    'connection_time_ms': int(self._connection_time * 1000),
                    'sqlite_version': self._sqlite_version
                })

            except Exception as e:
                error_msg = str(e)
                sanitized_error = self._sanitize_error_message(error_msg)
                self._logger.error('Failed to connect to SQLite', extra={'error': sanitized_error})

                # Categorize errors appropriately
                if 'readonly' in error_msg.lower() or 'permission' in error_msg.lower():
                    raise SecurityError(
                        message=f'Security error connecting to SQLite: {sanitized_error}',
                        details={'original_error': sanitized_error}
                    )
                else:
                    raise DatabaseError(
                        message=f'Failed to connect to SQLite database: {sanitized_error}',
                        details={'original_error': sanitized_error}
                    )

    async def disconnect(self) -> None:
        """Disconnect from the SQLite database."""
        if not self._connection:
            self._connected = False
            return

        try:
            await self._connection.close()
            self._connection = None
            self._connected = False
            self._logger.debug('SQLite connection closed')

            if self._accessed_tables:
                self._logger.info('SQLite session accessed tables', extra={
                    'tables': sorted(self._accessed_tables)
                })

        except Exception as e:
            self._logger.error('Error closing SQLite connection', extra={'error': str(e)})
            raise DatabaseError(
                message=f'Failed to close SQLite connection: {str(e)}',
                details={'original_error': str(e)}
            )

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None,
                            limit: Optional[int] = None) -> QueryResult:
        """Execute a query against the SQLite database.

        Args:
            query: The SQL query to execute
            params: Optional parameters for the query
            limit: Optional result limit

        Returns:
            QueryResult containing the query results

        Raises:
            DatabaseError: If a database error occurs
            SecurityError: If a security violation is detected
        """
        if not self._connected or not self._connection:
            await self.connect()

        if not self._connection:
            raise DatabaseError(
                message='Not connected to SQLite database',
                details={'connection_id': self._config.id}
            )

        result = QueryResult(
            query=query,
            connection_id=self._config.id,
            executed_at=datetime.now()
        )

        # Prepare and validate the query
        query, table_name = self._validate_and_prepare_query(query, limit)

        # Set up query cancellation support
        self._query_cancel_event = asyncio.Event()

        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing SQLite query', extra={
                'query': sanitized_query,
                'limit': limit
            })

            start_time = time.time()

            # Execute the query
            if params:
                prepared_query, param_values = self._convert_to_prepared_statement(query, params)
                cursor = await self._connection.execute(prepared_query, param_values)
            else:
                cursor = await self._connection.execute(query)

            # Fetch results
            records = await cursor.fetchall()

            # Get column information
            columns = await self._get_column_metadata(cursor)

            execution_time = time.time() - start_time

            # Close the cursor
            await cursor.close()

            # Update accessed tables tracking
            if table_name:
                self._accessed_tables.add(table_name.upper())

            # Populate result object
            result.records = records
            result.columns = columns
            result.row_count = len(records)
            result.execution_time_ms = int(execution_time * 1000)
            result.truncated = limit is not None and result.row_count >= limit

            self._logger.info('Successfully executed query on SQLite', extra={
                'record_count': result.row_count,
                'execution_time_ms': result.execution_time_ms,
                'table': table_name if table_name else None
            })

            return result

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error('Error executing query on SQLite', extra={
                'error': sanitized_error,
                'query': self._sanitize_sql_for_logging(query)
            })

            result.has_error = True
            result.error_message = sanitized_error

            # Categorize errors appropriately
            if any(keyword in error_msg.lower() for keyword in ['permission', 'access denied', 'authorization']):
                raise SecurityError(
                    message=f'Security error executing SQLite query: {sanitized_error}',
                    details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}
                )
            else:
                raise DatabaseError(
                    message=f'Failed to execute SQLite query: {sanitized_error}',
                    details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}
                )

        finally:
            self._query_cancel_event = None

    def _convert_to_prepared_statement(self, query: str, params: Dict[str, Any]) -> Tuple[str, List[Any]]:
        param_names = re.findall(':(\\w+)', query)
        param_values = []
        for name in param_names:
            if name not in params:
                raise ValueError(f"Parameter '{name}' not provided in params dictionary")
            param_values.append(params[name])
            query = query.replace(f':{name}', '?', 1)
        return (query, param_values)

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        """Get a list of tables in the database.

        Args:
            schema: Optional schema name (ignored for SQLite)

        Returns:
            List of TableMetadata objects

        Raises:
            DatabaseError: If a database error occurs
        """
        if not self._connected:
            await self.connect()

        try:
            # Query to get all tables and views
            query = """
                    SELECT name, type
                    FROM sqlite_master
                    WHERE type = 'table' \
                       OR type = 'view'
                    ORDER BY name \
                    """

            cursor = await self._connection.execute(query)
            table_rows = await cursor.fetchall()

            tables = []
            for row in table_rows:
                table_name = row['name']
                table_type = row['type'].upper()

                # Skip SQLite system tables
                if table_name.startswith('sqlite_'):
                    continue

                # Get columns for this table
                columns = await self.get_table_columns(table_name)

                tables.append(TableMetadata(
                    name=table_name,
                    type=table_type,
                    remarks=None,
                    columns=columns
                ))

            await cursor.close()
            return tables

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting schema information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get schema information: {sanitized_error}',
                details={'schema': schema}
            )

    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnMetadata]:
        """Get column information for a table.

        Args:
            table_name: The table name
            schema: Optional schema name (ignored for SQLite)

        Returns:
            List of ColumnMetadata objects

        Raises:
            DatabaseError: If a database error occurs
        """
        if not self._connected:
            await self.connect()

        try:
            # Query to get column information using PRAGMA
            query = f"PRAGMA table_info('{table_name}')"
            cursor = await self._connection.execute(query)
            column_rows = await cursor.fetchall()

            columns = []
            for row in column_rows:
                col_name = row['name']
                col_type = row['type']

                # In SQLite, the notnull field is 0 for nullable, 1 for NOT NULL
                nullable = row['notnull'] == 0

                # For columns with DECIMAL/NUMERIC types, try to extract precision and scale
                precision = 0
                scale = 0
                if 'DECIMAL' in col_type.upper() or 'NUMERIC' in col_type.upper():
                    # Try to extract precision and scale from type definition like DECIMAL(10,2)
                    match = re.search(r'\((\d+)(?:,(\d+))?\)', col_type)
                    if match:
                        precision = int(match.group(1))
                        if match.group(2):
                            scale = int(match.group(2))

                columns.append(ColumnMetadata(
                    name=col_name,
                    type_name=col_type,
                    type_code=99,  # SQLite doesn't have standardized type codes like JDBC
                    precision=precision,
                    scale=scale,
                    nullable=nullable,
                    table_name=table_name,
                    remarks=None
                ))

            await cursor.close()
            return columns

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting column information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get column information: {sanitized_error}',
                details={'table': table_name}
            )

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current connection.

        Returns:
            A dictionary with connection information
        """
        info = {
            'connected': self._connected,
            'connection_id': self._config.id,
            'name': self._config.name,
            'database': self._config.database,
            'type': 'SQLite',
            'read_only': self._config.read_only,
            'version': getattr(self, '_sqlite_version', 'Unknown')
        }

        if self._connection_time is not None:
            info['connection_time_ms'] = int(self._connection_time * 1000)

        if self._accessed_tables:
            info['accessed_tables'] = sorted(self._accessed_tables)

        return info

    def _validate_and_prepare_query(self, query: str, limit: Optional[int]) -> Tuple[str, Optional[str]]:
        """Validate and prepare a query for execution.

        Args:
            query: The original query
            limit: Optional limit for result rows

        Returns:
            Tuple of (modified query, table name or None)

        Raises:
            SecurityError: If the query violates security rules
        """
        query = query.strip()
        table_name = None

        # Handle case where query is just a table name
        if ' ' not in query:
            table_name = query

            # Check against allowed tables if configured
            if self._config.allowed_tables:
                if table_name.upper() not in self._config.allowed_tables:
                    raise SecurityError(
                        message=f"Access to table '{table_name}' is not allowed",
                        details={'table': table_name, 'allowed_tables': self._config.allowed_tables}
                    )

            # Expand to full SELECT query
            query = f'SELECT * FROM {table_name}'

        else:
            # For normal queries, check if this is a write operation in read-only mode
            query_upper = query.upper()
            if self._config.read_only and any(write_op in query_upper for write_op in [
                'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE'
            ]):
                raise SecurityError(
                    message='Write operations are not allowed on read-only connection',
                    details={'query': self._sanitize_sql_for_logging(query)}
                )

            # Try to extract table name for access control check
            match = re.search(r'FROM\s+(["\[]?(\w+)["\]]?)', query_upper)
            if match:
                table_name = match.group(2)

                # Check against allowed tables if configured
                if self._config.allowed_tables and table_name.upper() not in self._config.allowed_tables:
                    raise SecurityError(
                        message=f"Access to table '{table_name}' is not allowed",
                        details={'table': table_name, 'allowed_tables': self._config.allowed_tables}
                    )

        # Add LIMIT clause if needed
        if limit is not None and 'LIMIT' not in query.upper():
            # Remove trailing semicolon if present
            if query.rstrip().endswith(';'):
                query = query.rstrip()[:-1]

            query = f"{query} LIMIT {limit}"

        return query, table_name

    def _prepare_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for a SQLite query.

        Args:
            params: Original parameters dictionary

        Returns:
            Transformed parameters for SQLite
        """
        # Convert named parameters from :name format to :name format (already correct)
        # This is a no-op for SQLite, but kept for consistency with other connectors
        return params

    async def _get_column_metadata(self, cursor: aiosqlite.Cursor) -> List[ColumnMetadata]:
        """Extract column metadata from a cursor.

        Args:
            cursor: Database cursor with active result set

        Returns:
            List of ColumnMetadata objects
        """
        columns = []

        if cursor.description:
            for i, col_desc in enumerate(cursor.description):
                name = col_desc[0]
                type_code = 0

                # Get SQLite type name based on declared type
                # Note: This isn't perfect as SQLite has dynamic typing
                if col_desc[1] is not None:
                    type_name = str(col_desc[1]).upper()
                else:
                    # Get type based on column name via table schema
                    type_name = "UNKNOWN"

                columns.append(ColumnMetadata(
                    name=name,
                    type_name=type_name,
                    type_code=type_code,
                    precision=0,  # Not directly available from cursor
                    scale=0,  # Not directly available from cursor
                    nullable=True,  # SQLite doesn't expose nullability via cursor
                    table_name=None  # Not directly available from cursor
                ))

        return columns

    @staticmethod
    def _dict_factory(cursor: Any, row: Any) -> Dict[str, Any]:
        """Factory function to return rows as dictionaries.

        Args:
            cursor: The database cursor
            row: A database row

        Returns:
            Dictionary representation of the row
        """
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}