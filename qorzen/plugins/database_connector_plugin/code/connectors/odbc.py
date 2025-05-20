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
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from sqlalchemy import text
from ..models import ODBCConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
from .base import BaseDatabaseConnector


class ODBCConnector(BaseDatabaseConnector):
    def __init__(self, config: ODBCConnectionConfig, logger: Any, security_manager: Optional[Any] = None) -> None:
        """Initialize the ODBC connector.

        Args:
            config: ODBC connection configuration
            logger: Logger instance
            security_manager: Optional security manager
        """
        super().__init__(config, logger, security_manager)
        self._config = config
        self._connection: Optional[Any] = None
        self._cursor: Optional[Any] = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None
        self._is_filemaker = False

        try:
            import pyodbc
            self._pyodbc = pyodbc
        except ImportError:
            self._logger.error(
                "pyodbc module is required for ODBC connections. Please install it with 'pip install pyodbc'.")
            raise ImportError(
                "pyodbc module is required for ODBC connections. Please install it with 'pip install pyodbc'.")

    def _create_database_manager_config(self) -> Any:
        """Create a DatabaseConnectionConfig for ODBC.

        Returns:
            Any: A DatabaseConnectionConfig instance
        """
        from qorzen.core.database_manager import DatabaseConnectionConfig

        # Build connection string if not provided directly
        if self._config.connection_string:
            conn_str = self._config.connection_string
        else:
            conn_str = f'DSN={self._config.dsn}'

            if 'UID=' not in conn_str and 'PWD=' not in conn_str and self._config.username:
                conn_str += f';UID={self._config.username};PWD={self._config.password.get_secret_value()}'

            if self._config.server:
                conn_str += f';SERVER={self._config.server}'

            if self._config.port:
                conn_str += f';PORT={self._config.port}'

            if 'DATABASE=' not in conn_str and 'DB=' not in conn_str and self._config.database:
                conn_str += f';DATABASE={self._config.database}'

        return DatabaseConnectionConfig(
            name=self._registered_connection_id or f'odbc_{self._config.id}',
            db_type='odbc',
            host=self._config.server or '',
            port=self._config.port or 0,
            database=self._config.database,
            user=self._config.username,
            password=self._config.password.get_secret_value(),
            connection_string=conn_str,
            pool_size=1,
            max_overflow=0,
            pool_recycle=3600,
            echo=False,
            read_only=self._config.read_only,
            allowed_tables=self._config.allowed_tables,
            dsn=self._config.dsn
        )

    async def connect(self) -> None:
        """Connect to the database via ODBC."""
        async with self._connect_lock:
            if self._connected:
                return

            try:
                # Build connection string
                if self._config.connection_string:
                    conn_str = self._config.connection_string
                else:
                    conn_str = f'DSN={self._config.dsn}'

                    if 'UID=' not in conn_str and 'PWD=' not in conn_str and self._config.username:
                        conn_str += f';UID={self._config.username};PWD={self._config.password.get_secret_value()}'

                    if self._config.server:
                        conn_str += f';SERVER={self._config.server}'

                    if self._config.port:
                        conn_str += f';PORT={self._config.port}'

                    if 'DATABASE=' not in conn_str and 'DB=' not in conn_str and self._config.database:
                        conn_str += f';DATABASE={self._config.database}'

                self._logger.info('Connecting to database via ODBC', extra={
                    'dsn': self._config.dsn,
                    'database': self._config.database
                })

                start_time = time.time()

                # Try to register with database_manager if available
                if self._database_manager:
                    success = await self._register_with_database_manager()
                    if success:
                        # Test the connection
                        try:
                            test_result = await self._database_manager.execute_raw(
                                sql='SELECT 1',
                                connection_name=self._registered_connection_id
                            )

                            if not test_result:
                                raise DatabaseError(
                                    message='Failed to connect to ODBC database via database_manager',
                                    details={'connection_id': self._config.id}
                                )

                            # Try to detect if this is a FileMaker database
                            self._is_filemaker = await self._detect_filemaker_with_database_manager()

                            self._connection_time = time.time() - start_time
                            self._connected = True

                            self._logger.info('Successfully connected to database via ODBC using database_manager',
                                              extra={
                                                  'database': self._config.database,
                                                  'dsn': self._config.dsn,
                                                  'is_filemaker': self._is_filemaker,
                                                  'connection_time_ms': int(self._connection_time * 1000)
                                              })
                            return
                        except Exception as e:
                            self._logger.warning(f'Failed to test database_manager connection: {str(e)}')
                            # Continue to direct connection

                # Fall back to direct connection
                pyodbc = self._pyodbc
                loop = asyncio.get_running_loop()

                def connect_sync() -> Tuple[Any, float]:
                    start_time = time.time()
                    conn = pyodbc.connect(conn_str, timeout=self._config.connection_timeout)

                    if self._config.read_only:
                        try:
                            conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
                            conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
                            conn.setencoding(encoding='utf-8')
                        except Exception:
                            pass

                    connection_time = time.time() - start_time
                    return (conn, connection_time)

                conn, self._connection_time = await loop.run_in_executor(None, connect_sync)

                def detect_filemaker() -> bool:
                    cursor = conn.cursor()
                    try:
                        db_info = cursor.getinfo(pyodbc.SQL_DBMS_NAME).lower()
                        is_filemaker = 'filemaker' in db_info
                        return is_filemaker
                    except Exception:
                        try:
                            driver_info = cursor.getinfo(pyodbc.SQL_DRIVER_NAME).lower()
                            return 'filemaker' in driver_info
                        except Exception:
                            return 'filemaker' in self._config.dsn.lower()
                    finally:
                        cursor.close()

                self._is_filemaker = await loop.run_in_executor(None, detect_filemaker)
                self._connection = conn
                self._connected = True

                self._logger.info('Successfully connected to database via ODBC directly', extra={
                    'database': self._config.database,
                    'dsn': self._config.dsn,
                    'is_filemaker': self._is_filemaker,
                    'connection_time_ms': int(self._connection_time * 1000)
                })
            except Exception as e:
                error_msg = str(e)
                sanitized_error = self._sanitize_error_message(error_msg)
                self._logger.error('Failed to connect via ODBC', extra={'error': sanitized_error})

                if any((keyword in error_msg.lower() for keyword in [
                    'permission', 'access denied', 'authorization', 'login', 'password'
                ])):
                    raise SecurityError(
                        message=f'Security error connecting via ODBC: {sanitized_error}',
                        details={'original_error': sanitized_error}
                    ) from e
                else:
                    raise DatabaseError(
                        message=f'Failed to connect to database via ODBC: {sanitized_error}',
                        details={'original_error': sanitized_error}
                    ) from e

    async def _detect_filemaker_with_database_manager(self) -> bool:
        """Detect if the connected database is FileMaker.

        Returns:
            bool: True if FileMaker, False otherwise
        """
        try:
            info_sql = 'SELECT @@version AS version'
            try:
                result = await self._database_manager.execute_raw(
                    sql=info_sql,
                    connection_name=self._registered_connection_id
                )

                if result and result[0]:
                    version_info = str(result[0].get('version', '')).lower()
                    return 'filemaker' in version_info
            except Exception:
                pass

            # Check DSN for FileMaker
            if self._config.dsn and 'filemaker' in self._config.dsn.lower():
                return True

            return False
        except Exception:
            return False

    async def disconnect(self) -> None:
        """Disconnect from the ODBC database."""
        if not self._connected:
            return

        try:
            if self._registered_connection_id:
                # Connection is managed by database_manager, just mark it as disconnected
                self._connected = False
                self._logger.debug('ODBC database_manager connection marked as closed')
            elif self._connection:
                # Close direct connection
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
                self._logger.info('ODBC session accessed tables', extra={'tables': sorted(self._accessed_tables)})
        except Exception as e:
            self._logger.error('Error closing ODBC connection', extra={'error': str(e)})
            raise DatabaseError(
                message=f'Failed to close ODBC connection: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None,
                            limit: Optional[int] = None) -> QueryResult:
        """Execute a SQL query on the ODBC database.

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

        if not self._connection and not self._registered_connection_id:
            raise DatabaseError(
                message='Not connected to database',
                details={'connection_id': self._config.id}
            )

        result = QueryResult(query=query, connection_id=self._config.id, executed_at=datetime.now())
        query, table_name = self._validate_and_prepare_query(query, limit)
        self._query_cancel_event = asyncio.Event()

        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing ODBC query', extra={
                'query': sanitized_query,
                'limit': limit,
                'using_db_manager': self._registered_connection_id is not None
            })

            # Use database_manager if registered
            if self._registered_connection_id and self._database_manager:
                result = await self._execute_query_with_database_manager(query, params, limit)
                if table_name:
                    self._accessed_tables.add(table_name.upper())
                self._logger.info('Successfully executed query via ODBC using database_manager', extra={
                    'record_count': result.row_count,
                    'execution_time_ms': result.execution_time_ms,
                    'table': table_name if table_name else None
                })
                return result

            # Fall back to direct execution
            loop = asyncio.get_running_loop()

            def execute_query_sync() -> Tuple[List[Dict[str, Any]], List[ColumnMetadata], float, int]:
                start_time = time.time()
                cursor = self._connection.cursor()
                self._cursor = cursor

                try:
                    cursor.timeout = self._config.query_timeout
                except Exception:
                    pass

                if params:
                    prepared_query, param_values = self._convert_to_prepared_statement(query, params or {})
                    cursor.execute(prepared_query, param_values)
                else:
                    cursor.execute(query)

                columns = self._get_column_metadata(cursor)
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

            records, columns, execution_time, row_count = await loop.run_in_executor(None, execute_query_sync)

            if table_name:
                self._accessed_tables.add(table_name.upper())

            result.records = records
            result.columns = columns
            result.row_count = row_count
            result.execution_time_ms = int(execution_time * 1000)
            result.truncated = limit is not None and result.row_count >= limit

            self._logger.info('Successfully executed query via ODBC directly', extra={
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

            if any((keyword in error_msg.lower() for keyword in ['permission', 'access denied', 'privilege'])):
                raise SecurityError(
                    message=f'Security error executing ODBC query: {sanitized_error}',
                    details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}
                ) from e
            else:
                raise DatabaseError(
                    message=f'Failed to execute ODBC query: {sanitized_error}',
                    details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}
                ) from e
        finally:
            self._query_cancel_event = None

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        """Get a list of tables in the ODBC database.

        Args:
            schema: Optional schema name

        Returns:
            List[TableMetadata]: List of table metadata

        Raises:
            DatabaseError: If table retrieval fails
        """
        if not self._connected:
            await self.connect()

        try:
            # Use database_manager if registered
            if self._registered_connection_id and self._database_manager:
                return await self._get_tables_with_database_manager(schema)

            # Fall back to direct execution
            return await self._get_tables_direct(schema)
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting schema information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get schema information: {sanitized_error}',
                details={'schema': schema}
            ) from e

    async def _get_tables_with_database_manager(self, schema: Optional[str] = None) -> List[TableMetadata]:
        """Get tables using the database manager.

        Args:
            schema: Optional schema name

        Returns:
            List[TableMetadata]: List of table metadata

        Raises:
            DatabaseError: If table retrieval fails
        """
        try:
            tables = []
            sql = """
                  SELECT TABLE_NAME,
                         TABLE_TYPE,
                         TABLE_SCHEMA
                  FROM INFORMATION_SCHEMA.TABLES
                  WHERE (TABLE_TYPE = 'TABLE' OR TABLE_TYPE = 'VIEW') \
                  """

            if schema:
                sql += f" AND TABLE_SCHEMA = '{schema}'"

            sql += ' ORDER BY TABLE_NAME'

            try:
                table_rows = await self._database_manager.execute_raw(
                    sql=sql,
                    connection_name=self._registered_connection_id
                )
            except Exception:
                if self._is_filemaker:
                    tables = await self._get_filemaker_tables_with_database_manager()
                else:
                    tables = await self._get_tables_by_sampling()
                return tables

            for row in table_rows:
                if not row:
                    continue

                table_name = row.get('TABLE_NAME')
                if not table_name:
                    continue

                table_type = row.get('TABLE_TYPE', 'TABLE')
                table_schema = row.get('TABLE_SCHEMA')

                if table_name.startswith('sys') or table_name.startswith('INFORMATION_SCHEMA'):
                    continue

                try:
                    columns = await self.get_table_columns(table_name, schema)
                except Exception as e:
                    self._logger.warning(f'Failed to get columns for table {table_name}: {str(e)}')
                    columns = []

                tables.append(TableMetadata(
                    name=table_name,
                    type=table_type,
                    schema=table_schema,
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

    async def _get_filemaker_tables_with_database_manager(self) -> List[TableMetadata]:
        """Get tables for a FileMaker database.

        Returns:
            List[TableMetadata]: List of table metadata
        """
        tables = []

        try:
            layouts_sql = 'SELECT * FROM FileMaker_Tables'
            layouts = await self._database_manager.execute_raw(
                sql=layouts_sql,
                connection_name=self._registered_connection_id
            )

            for layout in layouts:
                layout_name = layout.get('TABLE_NAME', layout.get('BaseTableName'))
                if not layout_name:
                    continue

                tables.append(TableMetadata(
                    name=layout_name,
                    type='TABLE',
                    schema=None,
                    columns=[]
                ))

            return tables
        except Exception as e:
            self._logger.warning(f'Failed to get FileMaker tables with standard approach: {str(e)}')
            return await self._get_tables_by_sampling()

    async def _get_tables_by_sampling(self) -> List[TableMetadata]:
        """Get tables by sampling common table names.

        This is a fallback method when schema information is not available.

        Returns:
            List[TableMetadata]: List of table metadata
        """
        common_tables = [
            'Customers', 'Orders', 'Products', 'Employees', 'Users',
            'Invoices', 'Items', 'Categories', 'Contacts', 'Sales',
            'Transactions', 'Accounts', 'Inventory', 'Suppliers'
        ]

        tables = []

        for table_name in common_tables:
            try:
                test_sql = f'SELECT TOP 1 * FROM {table_name}'
                result = await self._database_manager.execute_raw(
                    sql=test_sql,
                    connection_name=self._registered_connection_id
                )

                if result is not None:
                    columns = []
                    if result:
                        for col_name in result[0].keys():
                            columns.append(ColumnMetadata(
                                name=col_name,
                                type_name='VARCHAR',
                                type_code=0,
                                precision=0,
                                scale=0,
                                nullable=True,
                                table_name=table_name
                            ))

                    tables.append(TableMetadata(
                        name=table_name,
                        type='TABLE',
                        schema=None,
                        columns=columns
                    ))
            except Exception:
                pass

        return tables

    async def _get_tables_direct(self, schema: Optional[str] = None) -> List[TableMetadata]:
        """Get tables using direct ODBC connection.

        Args:
            schema: Optional schema name

        Returns:
            List[TableMetadata]: List of table metadata
        """
        loop = asyncio.get_running_loop()

        def get_tables_sync() -> List[TableMetadata]:
            cursor = self._connection.cursor()
            tables = []

            try:
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

                    if table_type.upper() in ('TABLE', 'VIEW') and (not table_name.startswith('sys')):
                        columns = []

                        try:
                            col_cursor = self._connection.cursor()
                            col_cursor.columns(table=table_name, schema=table_schema)

                            for col_row in col_cursor:
                                col_name = col_row[3]
                                col_type = col_row[5]
                                col_size = col_row[6]
                                col_nullable = col_row[10] == 1
                                col_remarks = col_row[11] if len(col_row) > 11 else None
                                col_type_code = 0

                                try:
                                    col_type_code = col_row[4]
                                except Exception:
                                    pass

                                precision = col_size
                                scale = 0

                                try:
                                    scale = col_row[8]
                                except Exception:
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

        return await loop.run_in_executor(None, get_tables_sync)

    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnMetadata]:
        """Get columns for a specific table.

        Args:
            table_name: Table name
            schema: Optional schema name

        Returns:
            List[ColumnMetadata]: List of column metadata

        Raises:
            DatabaseError: If column retrieval fails
        """
        if not self._connected:
            await self.connect()

        try:
            # Use database_manager if registered
            if self._registered_connection_id and self._database_manager:
                return await self._get_table_columns_with_database_manager(table_name, schema)

            # Fall back to direct execution
            return await self._get_table_columns_direct(table_name, schema)
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting column information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get column information: {sanitized_error}',
                details={'table': table_name, 'schema': schema}
            ) from e

    async def _get_table_columns_with_database_manager(self, table_name: str, schema: Optional[str] = None) -> List[
        ColumnMetadata]:
        """Get table columns using the database manager.

        Args:
            table_name: Table name
            schema: Optional schema name

        Returns:
            List[ColumnMetadata]: List of column metadata
        """
        try:
            sql = f"""
                SELECT 
                    COLUMN_NAME, 
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
            """

            if schema:
                sql += f" AND TABLE_SCHEMA = '{schema}'"

            sql += ' ORDER BY ORDINAL_POSITION'

            try:
                columns_data = await self._database_manager.execute_raw(
                    sql=sql,
                    connection_name=self._registered_connection_id
                )

                if columns_data:
                    return self._process_information_schema_columns(columns_data, table_name)
            except Exception:
                pass

            # Try direct query if information schema fails
            sql = f'SELECT TOP 1 * FROM {table_name}'
            if self._is_filemaker:
                sql = f'SELECT * FROM {table_name} LIMIT 1'

            try:
                result = await self._database_manager.execute_raw(
                    sql=sql,
                    connection_name=self._registered_connection_id
                )

                if not result:
                    return []

                columns = []
                if result:
                    row = result[0]
                    for col_name, value in row.items():
                        type_name = self._get_type_name_from_value(value)
                        columns.append(ColumnMetadata(
                            name=col_name,
                            type_name=type_name,
                            type_code=self._get_type_code_from_name(type_name),
                            precision=10 if isinstance(value, (int, float)) else 0,
                            scale=2 if isinstance(value, float) else 0,
                            nullable=True,
                            table_name=table_name
                        ))

                return columns
            except Exception as e:
                self._logger.warning(f'Failed to get columns for table {table_name} using direct query: {str(e)}')
                return []
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting column information: {sanitized_error}')
            raise DatabaseError(
                message=f'Failed to get column information: {sanitized_error}',
                details={'table': table_name, 'schema': schema}
            ) from e

    def _process_information_schema_columns(self, columns_data: List[Dict[str, Any]], table_name: str) -> List[
        ColumnMetadata]:
        """Process column data from INFORMATION_SCHEMA.

        Args:
            columns_data: Column data from INFORMATION_SCHEMA
            table_name: Table name

        Returns:
            List[ColumnMetadata]: Processed column metadata
        """
        columns = []

        for row in columns_data:
            column_name = row.get('COLUMN_NAME')
            data_type = row.get('DATA_TYPE', 'VARCHAR')
            max_length = row.get('CHARACTER_MAXIMUM_LENGTH', 0)
            nullable = row.get('IS_NULLABLE', 'YES') == 'YES'
            precision = row.get('NUMERIC_PRECISION', 0)
            scale = row.get('NUMERIC_SCALE', 0)

            if max_length and (not precision):
                precision = max_length

            columns.append(ColumnMetadata(
                name=column_name,
                type_name=data_type,
                type_code=self._get_type_code_from_name(data_type),
                precision=precision,
                scale=scale,
                nullable=nullable,
                table_name=table_name
            ))

        return columns

    async def _get_table_columns_direct(self, table_name: str, schema: Optional[str] = None) -> List[ColumnMetadata]:
        """Get table columns using direct ODBC connection.

        Args:
            table_name: Table name
            schema: Optional schema name

        Returns:
            List[ColumnMetadata]: List of column metadata
        """
        loop = asyncio.get_running_loop()

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
                    col_type_code = 0

                    try:
                        col_type_code = row[4]
                    except Exception:
                        pass

                    precision = col_size
                    scale = 0

                    try:
                        scale = row[8]
                    except Exception:
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

        return await loop.run_in_executor(None, get_columns_sync)

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the ODBC connection.

        Returns:
            Dict[str, Any]: Connection information
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
            'read_only': self._config.read_only,
            'using_db_manager': self._registered_connection_id is not None
        }

        if self._connection_time is not None:
            info['connection_time_ms'] = int(self._connection_time * 1000)

        if self._accessed_tables:
            info['accessed_tables'] = sorted(self._accessed_tables)

        return info

    def _convert_to_prepared_statement(self, query: str, params: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Convert named parameters to positional parameters for ODBC.

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

    def _get_column_metadata(self, cursor: Any) -> List[ColumnMetadata]:
        """Extract column metadata from a cursor.

        Args:
            cursor: ODBC cursor

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

    def _get_type_code_from_name(self, type_name: str) -> int:
        """Get type code from SQL type name.

        Override with ODBC-specific type codes.

        Args:
            type_name: SQL type name

        Returns:
            int: Type code
        """
        if not hasattr(self, '_pyodbc'):
            return 0

        type_codes = {
            'NULL': 0,
            'INTEGER': self._pyodbc.SQL_INTEGER,
            'SMALLINT': self._pyodbc.SQL_SMALLINT,
            'DECIMAL': self._pyodbc.SQL_DECIMAL,
            'NUMERIC': self._pyodbc.SQL_NUMERIC,
            'REAL': self._pyodbc.SQL_REAL,
            'DOUBLE': self._pyodbc.SQL_DOUBLE,
            'FLOAT': self._pyodbc.SQL_FLOAT,
            'CHAR': self._pyodbc.SQL_CHAR,
            'VARCHAR': self._pyodbc.SQL_VARCHAR,
            'LONGVARCHAR': self._pyodbc.SQL_LONGVARCHAR,
            'DATE': self._pyodbc.SQL_DATE,
            'TIME': self._pyodbc.SQL_TIME,
            'TIMESTAMP': self._pyodbc.SQL_TIMESTAMP,
            'BINARY': self._pyodbc.SQL_BINARY,
            'VARBINARY': self._pyodbc.SQL_VARBINARY,
            'BOOLEAN': -7  # SQL_BIT
        }

        return type_codes.get(type_name, 0)