from __future__ import annotations

"""
SQLite database connector for the Database Connector Plugin.

This module provides a connector for SQLite databases using the DatabaseManager,
integrated with the asyncio-based architecture of the plugin.
"""
import asyncio
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from ..models import SQLiteConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
from .base import BaseDatabaseConnector


class SQLiteConnector(BaseDatabaseConnector):
    def __init__(self, config: SQLiteConnectionConfig, logger: Any, security_manager: Optional[Any] = None) -> None:
        """
        Initialize a SQLite database connector.

        Args:
            config: The SQLite connection configuration
            logger: Logger instance for recording connector activity
            security_manager: Optional security manager for access control
        """
        super().__init__(config, logger)
        self._config = config
        self._security_manager = security_manager
        self._connection: Optional[Any] = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None
        self._db_manager = None
        self._registered_connection_id: Optional[str] = None

        try:
            import sqlite3
            self._sqlite_version = sqlite3.sqlite_version
        except ImportError:
            self._logger.error('sqlite3 module is required for SQLite connections.')
            raise ImportError('sqlite3 module is required for SQLite connections.')

    async def connect(self) -> None:
        """
        Connect to the SQLite database using DatabaseManager if provided, otherwise directly.
        """
        async with self._connect_lock:
            if self._connected:
                return

            try:
                db_path = self._config.database
                self._logger.info('Connecting to SQLite database', extra={
                    'database': db_path,
                    'read_only': self._config.read_only
                })

                start_time = time.time()

                # Check if we have a database manager to use
                if hasattr(self, '_db_manager') and self._db_manager is not None:
                    # Register the connection with DatabaseManager
                    from qorzen.core.database_manager import DatabaseConnectionConfig

                    # Create a config for DatabaseManager
                    db_config = DatabaseConnectionConfig(
                        name=f"sqlite_{self._config.id}",
                        db_type="sqlite",
                        host="",
                        port=0,
                        database=db_path,
                        user="",
                        password="",
                        pool_size=1,
                        max_overflow=0,
                        pool_recycle=3600,
                        echo=False
                    )

                    # Register the connection
                    self._registered_connection_id = f"sqlite_{self._config.id}"

                    try:
                        # Check if the connection already exists
                        if await self._db_manager.has_connection(self._registered_connection_id):
                            self._logger.debug(f"Connection {self._registered_connection_id} already registered")
                        else:
                            await self._db_manager.register_connection(db_config)
                            self._logger.debug(
                                f"Registered connection with database_manager: {self._registered_connection_id}")
                    except Exception as e:
                        self._logger.warning(f"Could not register connection with database_manager: {str(e)}")
                else:
                    # Fallback to direct connection if no database_manager
                    import aiosqlite

                    if db_path == ':memory:':
                        self._connection = await aiosqlite.connect(':memory:')
                    else:
                        db_path = os.path.abspath(os.path.expanduser(db_path))
                        db_dir = os.path.dirname(db_path)
                        if not os.path.exists(db_dir):
                            os.makedirs(db_dir, exist_ok=True)

                        uri_path = f'file:{db_path}'
                        if self._config.read_only:
                            uri_path += '?mode=ro'

                        self._connection = await aiosqlite.connect(
                            uri_path,
                            uri=True,
                            timeout=self._config.connection_timeout
                        )

                    await self._connection.execute('PRAGMA foreign_keys = ON')
                    self._connection.row_factory = self._dict_factory

                self._connection_time = time.time() - start_time
                self._connected = True

                self._logger.info('Successfully connected to SQLite database', extra={
                    'database': db_path,
                    'connection_time_ms': int(self._connection_time * 1000),
                    'sqlite_version': self._sqlite_version,
                    'using_db_manager': self._registered_connection_id is not None
                })

            except Exception as e:
                error_msg = str(e)
                sanitized_error = self._sanitize_error_message(error_msg)
                self._logger.error('Failed to connect to SQLite', extra={'error': sanitized_error})

                if 'readonly' in error_msg.lower() or 'permission' in error_msg.lower():
                    raise SecurityError(
                        message=f'Security error connecting to SQLite: {sanitized_error}',
                        details={'original_error': sanitized_error}
                    ) from e
                else:
                    raise DatabaseError(
                        message=f'Failed to connect to SQLite database: {sanitized_error}',
                        details={'original_error': sanitized_error}
                    ) from e

    async def disconnect(self) -> None:
        """
        Disconnect from the SQLite database.
        """
        if not self._connected:
            return

        try:
            if self._registered_connection_id:
                # No need to explicitly disconnect with DatabaseManager
                pass
            elif self._connection:
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
            ) from e

    async def execute_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None
    ) -> QueryResult:
        """
        Execute a query against the SQLite database.

        Args:
            query: The SQL query to execute
            params: Optional parameters for the query
            limit: Optional row limit for the results

        Returns:
            QueryResult object containing the query results
        """
        if not self._connected:
            await self.connect()

        result = QueryResult(
            query=query,
            connection_id=self._config.id,
            executed_at=datetime.now()
        )

        query, table_name = self._validate_and_prepare_query(query, limit)
        self._query_cancel_event = asyncio.Event()

        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing SQLite query', extra={
                'query': sanitized_query,
                'limit': limit,
                'using_db_manager': self._registered_connection_id is not None
            })

            start_time = time.time()

            if self._registered_connection_id and hasattr(self, '_db_manager') and self._db_manager is not None:
                # Use DatabaseManager to execute the query
                prepared_params = self._prepare_params_for_db_manager(params)

                if params:
                    # For parameterized queries, use execute_raw
                    records = await self._db_manager.execute_raw(
                        sql=query,
                        params=prepared_params,
                        connection_name=self._registered_connection_id
                    )
                else:
                    # For non-parameterized queries
                    records = await self._db_manager.execute_raw(
                        sql=query,
                        connection_name=self._registered_connection_id
                    )

                # Get column metadata
                columns = await self._get_columns_metadata_from_db_manager(
                    records,
                    table_name
                )

            else:
                # Fallback to direct connection
                if params:
                    prepared_query, param_values = self._convert_to_prepared_statement(query, params)
                    cursor = await self._connection.execute(prepared_query, param_values)
                else:
                    cursor = await self._connection.execute(query)

                records = await cursor.fetchall()
                columns = await self._get_column_metadata(cursor)
                await cursor.close()

            execution_time = time.time() - start_time

            if table_name:
                self._accessed_tables.add(table_name.upper())

            result.records = records
            result.columns = columns
            result.row_count = len(records)
            result.execution_time_ms = int(execution_time * 1000)
            result.truncated = limit is not None and result.row_count >= limit

            self._logger.info('Successfully executed query on SQLite', extra={
                'record_count': result.row_count,
                'execution_time_ms': result.execution_time_ms,
                'table': table_name if table_name else None,
                'using_db_manager': self._registered_connection_id is not None
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

            if any((keyword in error_msg.lower() for keyword in ['permission', 'access denied', 'authorization'])):
                raise SecurityError(
                    message=f'Security error executing SQLite query: {sanitized_error}',
                    details={
                        'original_error': sanitized_error,
                        'query': self._sanitize_sql_for_logging(query)
                    }
                ) from e
            else:
                raise DatabaseError(
                    message=f'Failed to execute SQLite query: {sanitized_error}',
                    details={
                        'original_error': sanitized_error,
                        'query': self._sanitize_sql_for_logging(query)
                    }
                ) from e
        finally:
            self._query_cancel_event = None

    def _prepare_params_for_db_manager(self, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert named parameters to a format suitable for database_manager.

        Args:
            params: Dictionary of named parameters

        Returns:
            Dictionary of parameters formatted for DatabaseManager
        """
        if not params:
            return {}

        # DatabaseManager already handles dict parameters, so just return the dict
        return params

    async def _get_columns_metadata_from_db_manager(
            self,
            records: List[Dict[str, Any]],
            table_name: Optional[str]
    ) -> List[ColumnMetadata]:
        """
        Create column metadata based on query results from DatabaseManager.

        Args:
            records: The query result records
            table_name: Optional table name

        Returns:
            List of ColumnMetadata objects
        """
        columns = []

        if not records:
            return columns

        # Create column metadata based on the first record
        record = records[0]
        for col_name, value in record.items():
            # Determine type based on value
            type_name = self._get_type_name_from_value(value)
            columns.append(ColumnMetadata(
                name=col_name,
                type_name=type_name,
                type_code=0,  # SQLite doesn't have explicit type codes
                precision=0,
                scale=0,
                nullable=True,  # Assume nullable
                table_name=table_name
            ))

        return columns

    def _get_type_name_from_value(self, value: Any) -> str:
        """
        Determine SQLite type name from a Python value.

        Args:
            value: The Python value to analyze

        Returns:
            SQLite type name as string
        """
        if value is None:
            return "NULL"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "REAL"
        elif isinstance(value, str):
            return "TEXT"
        elif isinstance(value, bytes):
            return "BLOB"
        else:
            return "TEXT"  # Default to TEXT for other types

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        """
        Get a list of tables in the SQLite database.

        Args:
            schema: Optional schema name (ignored for SQLite)

        Returns:
            List of TableMetadata objects
        """
        if not self._connected:
            await self.connect()

        try:
            query = """
                    SELECT name, type
                    FROM sqlite_master
                    WHERE type = 'table'
                       OR type = 'view'
                    ORDER BY name \
                    """

            if self._registered_connection_id and hasattr(self, '_db_manager') and self._db_manager is not None:
                table_rows = await self._db_manager.execute_raw(
                    sql=query,
                    connection_name=self._registered_connection_id
                )
            else:
                cursor = await self._connection.execute(query)
                table_rows = await cursor.fetchall()
                await cursor.close()

            tables = []
            for row in table_rows:
                table_name = row['name']
                table_type = row['type'].upper()

                if table_name.startswith('sqlite_'):
                    continue

                columns = await self.get_table_columns(table_name)
                tables.append(TableMetadata(
                    name=table_name,
                    type=table_type,
                    remarks=None,
                    columns=columns
                ))

            return tables

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting schema information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get schema information: {sanitized_error}',
                details={'schema': schema}
            ) from e

    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnMetadata]:
        """
        Get the columns of a table in the SQLite database.

        Args:
            table_name: The name of the table
            schema: Optional schema name (ignored for SQLite)

        Returns:
            List of ColumnMetadata objects
        """
        if not self._connected:
            await self.connect()

        try:
            query = f"PRAGMA table_info('{table_name}')"

            if self._registered_connection_id and hasattr(self, '_db_manager') and self._db_manager is not None:
                column_rows = await self._db_manager.execute_raw(
                    sql=query,
                    connection_name=self._registered_connection_id
                )
            else:
                cursor = await self._connection.execute(query)
                column_rows = await cursor.fetchall()
                await cursor.close()

            columns = []
            for row in column_rows:
                col_name = row['name']
                col_type = row['type']
                nullable = row['notnull'] == 0
                precision = 0
                scale = 0

                # Parse precision and scale from type
                if 'DECIMAL' in col_type.upper() or 'NUMERIC' in col_type.upper():
                    match = re.search(r'\((\d+)(?:,(\d+))?\)', col_type)
                    if match:
                        precision = int(match.group(1))
                        if match.group(2):
                            scale = int(match.group(2))

                columns.append(ColumnMetadata(
                    name=col_name,
                    type_name=col_type,
                    type_code=99,  # SQLite doesn't have specific type codes
                    precision=precision,
                    scale=scale,
                    nullable=nullable,
                    table_name=table_name,
                    remarks=None
                ))

            return columns

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting column information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get column information: {sanitized_error}',
                details={'table': table_name}
            ) from e

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.

        Returns:
            Dictionary with connection information
        """
        info = {
            'connected': self._connected,
            'connection_id': self._config.id,
            'name': self._config.name,
            'database': self._config.database,
            'type': 'SQLite',
            'read_only': self._config.read_only,
            'version': getattr(self, '_sqlite_version', 'Unknown'),
            'using_db_manager': self._registered_connection_id is not None
        }

        if self._connection_time is not None:
            info['connection_time_ms'] = int(self._connection_time * 1000)

        if self._accessed_tables:
            info['accessed_tables'] = sorted(self._accessed_tables)

        return info

    def _convert_to_prepared_statement(self, query: str, params: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Convert a parameterized query to a prepared statement.

        Args:
            query: The SQL query with named parameters
            params: Dictionary of parameter values

        Returns:
            Tuple of (prepared query string, list of parameter values)
        """
        param_names = re.findall(r':(\w+)', query)
        param_values = []

        for name in param_names:
            if name not in params:
                raise ValueError(f"Parameter '{name}' not provided in params dictionary")

            param_values.append(params[name])
            query = query.replace(f':{name}', '?', 1)

        return (query, param_values)

    def _validate_and_prepare_query(self, query: str, limit: Optional[int]) -> Tuple[str, Optional[str]]:
        """
        Validate and prepare a query, applying security checks and limits.

        Args:
            query: The SQL query
            limit: Optional row limit

        Returns:
            Tuple of (prepared query, table name if simple query)
        """
        query = query.strip()
        table_name = None

        # Handle case where query is just a table name
        if ' ' not in query:
            table_name = query

            # Check if table is allowed
            if self._config.allowed_tables:
                if table_name.upper() not in self._config.allowed_tables:
                    raise SecurityError(
                        message=f"Access to table '{table_name}' is not allowed",
                        details={'table': table_name, 'allowed_tables': self._config.allowed_tables}
                    )

            query = f'SELECT * FROM {table_name}'
        else:
            # Check for write operations if read-only
            query_upper = query.upper()
            if self._config.read_only and any((write_op in query_upper for write_op in [
                'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE'
            ])):
                raise SecurityError(
                    message='Write operations are not allowed on read-only connection',
                    details={'query': self._sanitize_sql_for_logging(query)}
                )

            # Try to extract table name from query
            match = re.search(r'FROM\s+(["[`]?(\w+)["[\]`]?)', query_upper, re.IGNORECASE)
            if match:
                table_name = match.group(2)

                if self._config.allowed_tables and table_name.upper() not in self._config.allowed_tables:
                    raise SecurityError(
                        message=f"Access to table '{table_name}' is not allowed",
                        details={'table': table_name, 'allowed_tables': self._config.allowed_tables}
                    )

        # Add limit clause if needed
        if limit is not None and 'LIMIT' not in query.upper():
            if query.rstrip().endswith(';'):
                query = query.rstrip()[:-1]

            query = f'{query} LIMIT {limit}'

        return (query, table_name)

    async def _get_column_metadata(self, cursor: Any) -> List[ColumnMetadata]:
        """
        Get column metadata from a cursor.

        Args:
            cursor: SQLite cursor object

        Returns:
            List of ColumnMetadata objects
        """
        columns = []

        if cursor.description:
            for i, col_desc in enumerate(cursor.description):
                name = col_desc[0]

                # SQLite doesn't provide detailed type information via cursor description
                # We use generic type information
                columns.append(ColumnMetadata(
                    name=name,
                    type_name="UNKNOWN",  # Will be replaced with actual type in final result
                    type_code=0,
                    precision=0,
                    scale=0,
                    nullable=True,
                    table_name=None
                ))

        return columns

    @staticmethod
    def _dict_factory(cursor: Any, row: Any) -> Dict[str, Any]:
        """
        Convert a row to a dictionary.

        Args:
            cursor: SQLite cursor
            row: Row tuple

        Returns:
            Dictionary mapping column names to values
        """
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def set_database_manager(self, db_manager: Any) -> None:
        """
        Set the database manager for this connector.

        Args:
            db_manager: The database manager instance
        """
        self._db_manager = db_manager
        self._logger.debug(f"Database manager set for SQLite connector {self._config.id}")