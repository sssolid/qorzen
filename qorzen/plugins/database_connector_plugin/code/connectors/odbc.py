from __future__ import annotations

"""
Enhanced ODBC database connector for the Database Connector Plugin.

This module provides an improved connector for databases using ODBC, with specific
optimizations for FileMaker databases, integrated with the updated
asyncio-based architecture.
"""

import asyncio
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError

from ..models import ODBCConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
from .base import BaseDatabaseConnector


class ODBCConnector(BaseDatabaseConnector):
    """ODBC database connector with FileMaker support."""

    def __init__(self, config: ODBCConnectionConfig, logger: Any, security_manager: Optional[Any] = None) -> None:
        """Initialize the ODBC connector.

        Args:
            config: ODBC connection configuration
            logger: Logger instance
            security_manager: Optional security manager
        """
        super().__init__(config, logger)
        self._config = config
        self._security_manager = security_manager
        self._connection: Optional[Any] = None
        self._cursor: Optional[Any] = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None
        self._is_filemaker = False

        # Verify pyodbc is available
        try:
            import pyodbc
            self._pyodbc = pyodbc
        except ImportError:
            self._logger.error(
                "pyodbc module is required for ODBC connections. Please install it with 'pip install pyodbc'.")
            raise ImportError(
                "pyodbc module is required for ODBC connections. Please install it with 'pip install pyodbc'.")

    async def connect(self) -> None:
        """Connect to the database via ODBC."""
        async with self._connect_lock:
            if self._connected:
                return

            pyodbc = self._pyodbc
            try:
                # Build connection string
                if self._config.connection_string:
                    conn_str = self._config.connection_string
                else:
                    conn_str = f'DSN={self._config.dsn}'

                    # Add username/password if not in the connection string
                    if 'UID=' not in conn_str and 'PWD=' not in conn_str:
                        conn_str += f';UID={self._config.username};PWD={self._config.password.get_secret_value()}'

                    # Add server if specified
                    if self._config.server:
                        conn_str += f';SERVER={self._config.server}'

                    # Add port if specified
                    if self._config.port:
                        conn_str += f';PORT={self._config.port}'

                    # Add database if not already in the connection string
                    if 'DATABASE=' not in conn_str and 'DB=' not in conn_str:
                        conn_str += f';DATABASE={self._config.database}'

                self._logger.info('Connecting to database via ODBC', extra={
                    'dsn': self._config.dsn,
                    'database': self._config.database
                })

                # Connect using asyncio to avoid blocking
                loop = asyncio.get_running_loop()

                def connect_sync() -> Tuple[Any, float]:
                    start_time = time.time()
                    conn = pyodbc.connect(conn_str, timeout=self._config.connection_timeout)

                    # Set encoding if read-only
                    if self._config.read_only:
                        try:
                            conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
                            conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
                            conn.setencoding(encoding='utf-8')
                        except:
                            pass

                    connection_time = time.time() - start_time
                    return (conn, connection_time)

                conn, self._connection_time = await loop.run_in_executor(None, connect_sync)

                # Detect if this is a FileMaker database
                def detect_filemaker() -> bool:
                    cursor = conn.cursor()
                    try:
                        db_info = cursor.getinfo(pyodbc.SQL_DBMS_NAME).lower()
                        is_filemaker = 'filemaker' in db_info
                        return is_filemaker
                    except:
                        # Check for FileMaker in driver name if getinfo fails
                        try:
                            driver_info = cursor.getinfo(pyodbc.SQL_DRIVER_NAME).lower()
                            return 'filemaker' in driver_info
                        except:
                            # One more attempt - check DSN name
                            return 'filemaker' in self._config.dsn.lower()
                    finally:
                        cursor.close()

                self._is_filemaker = await loop.run_in_executor(None, detect_filemaker)

                self._connection = conn
                self._connected = True

                self._logger.info('Successfully connected to database via ODBC', extra={
                    'database': self._config.database,
                    'dsn': self._config.dsn,
                    'is_filemaker': self._is_filemaker,
                    'connection_time_ms': int(self._connection_time * 1000)
                })

            except Exception as e:
                error_msg = str(e)
                sanitized_error = self._sanitize_error_message(error_msg)
                self._logger.error('Failed to connect via ODBC', extra={'error': sanitized_error})

                # Categorize errors appropriately
                if any(keyword in error_msg.lower() for keyword in
                       ['permission', 'access denied', 'authorization', 'login', 'password']):
                    raise SecurityError(
                        message=f'Security error connecting via ODBC: {sanitized_error}',
                        details={'original_error': sanitized_error}
                    )
                else:
                    raise DatabaseError(
                        message=f'Failed to connect to database via ODBC: {sanitized_error}',
                        details={'original_error': sanitized_error}
                    )

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        if not self._connection:
            self._connected = False
            return

        try:
            loop = asyncio.get_running_loop()

            def close_sync() -> None:
                if self._cursor:
                    self._cursor.close()
                    self._cursor = None
                self._connection.close()

            await loop.run_in_executor(None, close_sync)
            self._connection = None
            self._connected = False

            self._logger.debug('ODBC connection closed')

            if self._accessed_tables:
                self._logger.info('ODBC session accessed tables', extra={
                    'tables': sorted(self._accessed_tables)
                })

        except Exception as e:
            self._logger.error('Error closing ODBC connection', extra={'error': str(e)})
            raise DatabaseError(
                message=f'Failed to close ODBC connection: {str(e)}',
                details={'original_error': str(e)}
            )

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None,
                            limit: Optional[int] = None) -> QueryResult:
        """Execute a query via ODBC.

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
                message='Not connected to database',
                details={'connection_id': self._config.id}
            )

        pyodbc = self._pyodbc
        result = QueryResult(
            query=query,
            connection_id=self._config.id,
            executed_at=time.time()
        )

        # Prepare and validate the query
        query, table_name = self._validate_and_prepare_query(query, limit)

        # Set up query cancellation support
        self._query_cancel_event = asyncio.Event()

        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing ODBC query', extra={
                'query': sanitized_query,
                'limit': limit
            })

            def execute_query_sync() -> Tuple[List[Dict[str, Any]], List[ColumnMetadata], float, int]:
                start_time = time.time()
                cursor = self._connection.cursor()
                self._cursor = cursor
                try:
                    cursor.timeout = self._config.query_timeout
                except:
                    pass
                if params:
                    prepared_query, param_values = self._convert_to_prepared_statement(query, params or {})
                    cursor.execute(prepared_query, param_values)
                else:
                    cursor.execute(query)

                # Extract column metadata
                columns = self._get_column_metadata(cursor)

                # Fetch all results
                records = []
                row_count = 0
                for row in cursor:
                    row_dict = {}
                    for idx, column in enumerate(columns):
                        row_dict[column.name] = row[idx]
                    records.append(row_dict)
                    row_count += 1

                cursor.close()
                self._cursor = None
                execution_time = time.time() - start_time

                return (records, columns, execution_time, row_count)

            # Execute query asynchronously
            loop = asyncio.get_running_loop()
            records, columns, execution_time, row_count = await loop.run_in_executor(None, execute_query_sync)

            # Track accessed tables
            if table_name:
                self._accessed_tables.add(table_name.upper())

            # Populate result object
            result.records = records
            result.columns = columns
            result.row_count = row_count
            result.execution_time_ms = int(execution_time * 1000)
            result.truncated = limit is not None and result.row_count >= limit

            self._logger.info('Successfully executed query via ODBC', extra={
                'record_count': result.row_count,
                'execution_time_ms': result.execution_time_ms,
                'table': table_name
            })

            return result

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error('Error executing query via ODBC', extra={
                'error': sanitized_error,
                'query': self._sanitize_sql_for_logging(query)
            })

            result.has_error = True
            result.error_message = sanitized_error

            # Categorize errors appropriately
            if any(keyword in error_msg.lower() for keyword in
                   ['permission', 'access denied', 'privilege']):
                raise SecurityError(
                    message=f'Security error executing ODBC query: {sanitized_error}',
                    details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}
                )
            else:
                raise DatabaseError(
                    message=f'Failed to execute ODBC query: {sanitized_error}',
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
        """Get a list of tables from the database.

        Args:
            schema: Optional schema name

        Returns:
            List of TableMetadata objects

        Raises:
            DatabaseError: If a database error occurs
        """
        if not self._connected:
            await self.connect()

        def get_tables_sync() -> List[TableMetadata]:
            cursor = self._connection.cursor()
            tables = []

            try:
                # FileMaker requires special handling
                if self._is_filemaker:
                    cursor.tables()
                elif schema:
                    cursor.tables(schema=schema)
                else:
                    cursor.tables()

                for row in cursor:
                    table_catalog = row[0]
                    table_schema = row[1]
                    table_name = row[2]
                    table_type = row[3]
                    remarks = row[4] if len(row) > 4 else None

                    # Skip system tables
                    if table_type.upper() in ('TABLE', 'VIEW') and (not table_name.startswith('sys')):
                        columns = []

                        # Get column information
                        try:
                            col_cursor = self._connection.cursor()
                            col_cursor.columns(table=table_name, schema=table_schema)

                            for col_row in col_cursor:
                                col_name = col_row[3]
                                col_type = col_row[5]
                                col_size = col_row[6]
                                col_nullable = col_row[10] == 1
                                col_remarks = col_row[11] if len(col_row) > 11 else None

                                # Get type code if available
                                col_type_code = 0
                                try:
                                    col_type_code = col_row[4]
                                except:
                                    pass

                                precision = col_size
                                scale = 0
                                try:
                                    scale = col_row[8]
                                except:
                                    pass

                                columns.append(ColumnMetadata(
                                    name=col_name,
                                    type_name=col_type,
                                    type_code=col_type_code,
                                    precision=precision,
                                    scale=scale,
                                    nullable=col_nullable,
                                    table_name=table_name,
                                    remarks=col_remarks
                                ))

                            col_cursor.close()

                        except Exception as e:
                            self._logger.warning(f'Error retrieving columns for table {table_name}: {str(e)}')

                        tables.append(TableMetadata(
                            name=table_name,
                            schema=table_schema,
                            type=table_type,
                            remarks=remarks,
                            columns=columns
                        ))

            finally:
                cursor.close()

            return tables

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, get_tables_sync)

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting tables information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get tables information: {sanitized_error}',
                details={'schema': schema}
            )

    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnMetadata]:
        """Get column information for a table.

        Args:
            table_name: The table name
            schema: Optional schema name

        Returns:
            List of ColumnMetadata objects

        Raises:
            DatabaseError: If a database error occurs
        """
        if not self._connected:
            await self.connect()

        def get_columns_sync() -> List[ColumnMetadata]:
            cursor = self._connection.cursor()
            columns = []

            try:
                cursor.columns(table=table_name, schema=schema)

                for row in cursor:
                    col_name = row[3]
                    col_type = row[5]
                    col_size = row[6]
                    col_nullable = row[10] == 1
                    col_remarks = row[11] if len(row) > 11 else None

                    # Get type code if available
                    col_type_code = 0
                    try:
                        col_type_code = row[4]
                    except:
                        pass

                    precision = col_size
                    scale = 0
                    try:
                        scale = row[8]
                    except:
                        pass

                    columns.append(ColumnMetadata(
                        name=col_name,
                        type_name=col_type,
                        type_code=col_type_code,
                        precision=precision,
                        scale=scale,
                        nullable=col_nullable,
                        table_name=table_name,
                        remarks=col_remarks
                    ))

            finally:
                cursor.close()

            return columns

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, get_columns_sync)

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting column information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get column information: {sanitized_error}',
                details={'table': table_name, 'schema': schema}
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
            'dsn': self._config.dsn,
            'server': self._config.server,
            'database': self._config.database,
            'username': self._config.username,
            'type': 'ODBC',
            'is_filemaker': self._is_filemaker,
            'read_only': self._config.read_only
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
            if self._is_filemaker:
                query = f'SELECT * FROM {table_name}'
            else:
                query = f'SELECT * FROM {table_name}'

        else:
            # For normal queries, check if this is a write operation in read-only mode
            query_upper = query.upper()
            if self._config.read_only and any(write_op in query_upper for write_op in [
                'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE'
            ]):
                raise SecurityError(
                    message='Write operations are not allowed on read-only connection',
                    details={'query': self._sanitize_sql_for_logging(query)}
                )

            # Extract table name for access control check
            match = re.search(r'FROM\s+(\w+)', query_upper)
            if match:
                table_name = match.group(1)

                # Check against allowed tables if configured
                if self._config.allowed_tables and table_name.upper() not in self._config.allowed_tables:
                    raise SecurityError(
                        message=f"Access to table '{table_name}' is not allowed",
                        details={'table': table_name, 'allowed_tables': self._config.allowed_tables}
                    )

        # Add limit clause if needed
        if limit is not None:
            # Check if query already has a limit clause
            has_limit = 'LIMIT' in query.upper()
            has_fetch = 'FETCH' in query.upper() and 'FIRST' in query.upper() and 'ROWS' in query.upper()
            has_offset = 'OFFSET' in query.upper() and 'ROWS' in query.upper()

            if not (has_limit or has_fetch):
                # Remove trailing semicolon if present
                if ';' in query:
                    query = query.rstrip(';')

                # Use appropriate syntax based on database type
                if self._is_filemaker:
                    # FileMaker's pagination syntax
                    query = f'{query} FETCH FIRST {limit} ROWS ONLY'
                else:
                    # Standard LIMIT syntax for most databases
                    query = f'{query} LIMIT {limit}'

        return query, table_name

    def _prepare_parameters(self, params: Dict[str, Any]) -> List[Any]:
        """Prepare parameters for an ODBC query.

        Args:
            params: Dictionary of parameter values

        Returns:
            List of parameter values in the order they appear in the query
        """
        return list(params.values())

    def _get_column_metadata(self, cursor: Any) -> List[ColumnMetadata]:
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
                type_code = col_desc[1]
                display_size = col_desc[2]
                internal_size = col_desc[3]
                precision = col_desc[4] or 0
                scale = col_desc[5] or 0
                nullable = col_desc[6] is True

                # Try to get type name from PyODBC if available
                type_name = 'UNKNOWN'
                try:
                    type_name = self._pyodbc.SQL_TYPE_NAME.get(type_code, 'UNKNOWN')
                except:
                    pass

                columns.append(ColumnMetadata(
                    name=name,
                    type_name=type_name,
                    type_code=type_code,
                    precision=precision,
                    scale=scale,
                    nullable=nullable
                ))

        return columns