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
        """Initialize the SQLite connector.

        Args:
            config: SQLite connection configuration
            logger: Logger instance
            security_manager: Optional security manager
        """
        super().__init__(config, logger, security_manager)
        self._config = config
        self._connection: Optional[Any] = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None

        try:
            import sqlite3
            self._sqlite_version = sqlite3.sqlite_version
        except ImportError:
            self._logger.error('sqlite3 module is required for SQLite connections.')
            raise ImportError('sqlite3 module is required for SQLite connections.')

    def _create_database_manager_config(self) -> Any:
        """Create a DatabaseConnectionConfig for SQLite.

        Returns:
            Any: A DatabaseConnectionConfig instance
        """
        from qorzen.core.database_manager import DatabaseConnectionConfig

        db_path = self._config.database

        return DatabaseConnectionConfig(
            name=self._registered_connection_id or f'sqlite_{self._config.id}',
            db_type='sqlite',
            host='',
            port=0,
            database=db_path,
            user='',
            password='',
            pool_size=1,
            max_overflow=0,
            pool_recycle=3600,
            echo=False,
            read_only=self._config.read_only,
            allowed_tables=self._config.allowed_tables
        )

    async def connect(self) -> None:
        """Connect to the SQLite database."""
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

                # Try to register with database_manager if available
                if self._database_manager:
                    success = await self._register_with_database_manager()
                    if success:
                        # Test the connection
                        try:
                            await self._database_manager.execute_raw(
                                sql='SELECT 1',
                                connection_name=self._registered_connection_id
                            )
                            self._connection_time = time.time() - start_time
                            self._connected = True
                            self._logger.info('Successfully connected to SQLite database via database_manager', extra={
                                'database': db_path,
                                'connection_time_ms': int(self._connection_time * 1000),
                                'sqlite_version': self._sqlite_version
                            })
                            return
                        except Exception as e:
                            self._logger.warning(f'Failed to test database_manager connection: {str(e)}')
                            # Continue to direct connection

                # Fall back to direct connection
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

                self._logger.info('Successfully connected to SQLite database directly', extra={
                    'database': db_path,
                    'connection_time_ms': int(self._connection_time * 1000),
                    'sqlite_version': self._sqlite_version
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
        """Disconnect from the SQLite database."""
        if not self._connected:
            return

        try:
            if self._registered_connection_id:
                # Connection is managed by database_manager, just mark it as disconnected
                self._connected = False
                self._logger.debug('SQLite database_manager connection marked as closed')
            elif self._connection:
                # Close direct connection
                await self._connection.close()
                self._connection = None
                self._connected = False
                self._logger.debug('SQLite connection closed')

            if self._accessed_tables:
                self._logger.info('SQLite session accessed tables', extra={'tables': sorted(self._accessed_tables)})
        except Exception as e:
            self._logger.error('Error closing SQLite connection', extra={'error': str(e)})
            raise DatabaseError(
                message=f'Failed to close SQLite connection: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None,
                            limit: Optional[int] = None) -> QueryResult:
        """Execute a SQL query on the SQLite database.

        Args:
            query: SQL query
            params: Optional query parameters
            limit: Optional result limit

        Returns:
            QueryResult: Query execution result

        Raises:
            DatabaseError: If query execution fails
            SecurityError: If query violates security restrictions
        """
        if not self._connected:
            await self.connect()

        result = QueryResult(query=query, connection_id=self._config.id, executed_at=datetime.now())
        query, table_name = self._validate_and_prepare_query(query, limit)
        self._query_cancel_event = asyncio.Event()

        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing SQLite query', extra={
                'query': sanitized_query,
                'limit': limit,
                'using_db_manager': self._registered_connection_id is not None
            })

            # Use database_manager if registered
            if self._registered_connection_id and self._database_manager:
                result = await self._execute_query_with_database_manager(query, params, limit)
                if table_name:
                    self._accessed_tables.add(table_name.upper())
                self._logger.info('Successfully executed query on SQLite via database_manager', extra={
                    'record_count': result.row_count,
                    'execution_time_ms': result.execution_time_ms,
                    'table': table_name if table_name else None
                })
                return result

            # Fall back to direct execution
            start_time = time.time()

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

            self._logger.info('Successfully executed query on SQLite directly', extra={
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

            if any((keyword in error_msg.lower() for keyword in ['permission', 'access denied', 'authorization'])):
                raise SecurityError(
                    message=f'Security error executing SQLite query: {sanitized_error}',
                    details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}
                ) from e
            else:
                raise DatabaseError(
                    message=f'Failed to execute SQLite query: {sanitized_error}',
                    details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}
                ) from e
        finally:
            self._query_cancel_event = None

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        """Get a list of tables in the SQLite database.

        Args:
            schema: Optional schema name (not used for SQLite)

        Returns:
            List[TableMetadata]: List of table metadata

        Raises:
            DatabaseError: If table retrieval fails
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

            # Try to use database_manager if registered
            if self._registered_connection_id and self._database_manager:
                table_rows = await self._database_manager.execute_raw(
                    sql=query,
                    connection_name=self._registered_connection_id
                )
            else:
                # Use direct connection
                cursor = await self._connection.execute(query)
                table_rows = await cursor.fetchall()
                await cursor.close()

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
        """Get columns for a specific table.

        Args:
            table_name: Table name
            schema: Optional schema name (not used for SQLite)

        Returns:
            List[ColumnMetadata]: List of column metadata

        Raises:
            DatabaseError: If column retrieval fails
        """
        if not self._connected:
            await self.connect()

        try:
            query = f"PRAGMA table_info('{table_name}')"

            # Try to use database_manager if registered
            if self._registered_connection_id and self._database_manager:
                column_rows = await self._database_manager.execute_raw(
                    sql=query,
                    connection_name=self._registered_connection_id
                )
            else:
                # Use direct connection
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

                # Parse precision and scale for decimal types
                if 'DECIMAL' in col_type.upper() or 'NUMERIC' in col_type.upper():
                    match = re.search(r'\((\d+)(?:,(\d+))?\)', col_type)
                    if match:
                        precision = int(match.group(1))
                        if match.group(2):
                            scale = int(match.group(2))

                columns.append(ColumnMetadata(
                    name=col_name,
                    type_name=col_type,
                    type_code=99,  # SQLite doesn't have standard type codes
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
        """Get information about the SQLite connection.

        Returns:
            Dict[str, Any]: Connection information
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
        """Convert named parameters to positional parameters for SQLite.

        Args:
            query: SQL query with named parameters
            params: Parameter values

        Returns:
            Tuple[str, List[Any]]: Query with positional parameters and parameter values

        Raises:
            ValueError: If a parameter is missing
        """
        param_names = re.findall(r':(\w+)', query)
        param_values = []

        for name in param_names:
            if name not in params:
                raise ValueError(f"Parameter '{name}' not provided in params dictionary")

            param_values.append(params[name])
            query = query.replace(f':{name}', '?', 1)

        return (query, param_values)

    async def _get_column_metadata(self, cursor: Any) -> List[ColumnMetadata]:
        """Extract column metadata from a cursor.

        Args:
            cursor: SQLite cursor

        Returns:
            List[ColumnMetadata]: Column metadata
        """
        columns = []

        if cursor.description:
            for i, col_desc in enumerate(cursor.description):
                name = col_desc[0]

                columns.append(ColumnMetadata(
                    name=name,
                    type_name='UNKNOWN',  # We don't have type information from cursor
                    type_code=0,
                    precision=0,
                    scale=0,
                    nullable=True,
                    table_name=None
                ))

        return columns

    @staticmethod
    def _dict_factory(cursor: Any, row: Any) -> Dict[str, Any]:
        """Convert a row to a dictionary.

        Args:
            cursor: SQLite cursor
            row: Row tuple

        Returns:
            Dict[str, Any]: Row as a dictionary
        """
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}