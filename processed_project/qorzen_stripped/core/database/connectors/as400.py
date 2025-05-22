from __future__ import annotations
'\nAS400 database connector for the Database Manager.\n\nThis module provides a connector for AS400/iSeries databases using the\nJTOpen (JT400) Java library via JPype, integrated with the asyncio-based architecture.\n'
import asyncio
import os
import re
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from .base import BaseDatabaseConnector
class AS400Connector(BaseDatabaseConnector):
    def __init__(self, config: Any, logger: Any, security_manager: Optional[Any]=None) -> None:
        super().__init__(config, logger, security_manager)
        self._config = config
        self._connection: Optional[Any] = None
        self._jpype = None
        self._JException = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None
        self._connection_properties: Dict[str, str] = {}
        try:
            import jpype
            from jpype.types import JException
            self._jpype = jpype
            self._JException = JException
            self._initialize_jpype()
        except ImportError:
            self._logger.error("jpype module is required for AS400 connections. Please install it with 'pip install jpype1'.")
            raise ImportError("jpype module is required for AS400 connections. Please install it with 'pip install jpype1'.")
    def _initialize_jpype(self) -> None:
        jpype = self._jpype
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[self._config.jt400_jar_path], convertStrings=True)
            self._logger.debug('JVM started for AS400 access')
            try:
                driver_class = jpype.JClass('com.ibm.as400.access.AS400JDBCDriver')
                driver = driver_class()
                jpype.JClass('java.sql.DriverManager').registerDriver(driver)
                self._logger.debug('AS400 JDBC driver registered successfully')
            except Exception as e:
                self._logger.warning('Could not register AS400 JDBC driver explicitly', extra={'error': str(e)})
    def _create_database_manager_config(self) -> Any:
        from qorzen.core.database_manager import DatabaseConnectionConfig
        jdbc_url = self._build_jdbc_url()
        properties = {'user': self._config.user, 'password': self._config.password, 'secure': 'true' if self._config.ssl else 'false', 'prompt': 'false', 'libraries': self._config.database, 'login timeout': str(self._config.connection_timeout), 'query timeout': str(self._config.query_timeout), 'transaction isolation': 'read committed', 'date format': 'iso', 'errors': 'full'}
        if self._config.read_only:
            properties['access'] = 'read only'
        return DatabaseConnectionConfig(name=self._registered_connection_id or f'as400_{self._config.name}', db_type='jdbc', host=self._config.host, port=self._config.port or 446, database=self._config.database, user=self._config.user, password=self._config.password, pool_size=1, max_overflow=0, url=jdbc_url, properties=properties, read_only=self._config.read_only, ssl=self._config.ssl, allowed_tables=self._config.allowed_tables, jt400_jar_path=self._config.jt400_jar_path)
    async def connect(self) -> None:
        async with self._connect_lock:
            if self._connected:
                return
            if self._database_manager:
                try:
                    await self._connect_with_database_manager()
                    return
                except Exception as e:
                    self._logger.warning(f'Failed to connect with database_manager: {str(e)}')
            await self._connect_direct()
    async def _connect_with_database_manager(self) -> None:
        try:
            self._logger.info('Connecting to AS400 database via database_manager', extra={'database': self._config.database, 'server': self._config.server, 'ssl': self._config.ssl})
            start_time = time.time()
            success = await self._register_with_database_manager()
            if not success:
                raise DatabaseError(message=f'Failed to register AS400 connection with database_manager', details={'connection_id': self._config.name})
            test_result = await self._database_manager.execute_raw(sql='SELECT 1 FROM SYSIBM.SYSDUMMY1', connection_name=self._registered_connection_id)
            if not test_result:
                raise DatabaseError(message='Failed to connect to AS400 database via database_manager', details={'connection_id': self._config.name})
            self._connection_time = time.time() - start_time
            self._connected = True
            jdbc_url = self._build_jdbc_url()
            self._connection_properties = {'user': self._config.user, 'secure': 'true' if self._config.ssl else 'false', 'prompt': 'false', 'libraries': self._config.database, 'login timeout': str(self._config.connection_timeout), 'query timeout': str(self._config.query_timeout), 'transaction isolation': 'read committed', 'date format': 'iso', 'errors': 'full'}
            if self._config.read_only:
                self._connection_properties['access'] = 'read only'
            self._logger.info('Successfully connected to AS400 database via database_manager', extra={'database': self._config.database, 'server': self._config.server, 'connection_time_ms': int(self._connection_time * 1000)})
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error('Failed to connect to AS400 via database_manager', extra={'error': sanitized_error})
            if any((keyword in error_msg.lower() for keyword in ['permission', 'access denied', 'authorization'])):
                raise SecurityError(message=f'Security error connecting to AS400: {sanitized_error}', details={'original_error': sanitized_error}) from e
            else:
                raise DatabaseError(message=f'Failed to connect to AS400 database: {sanitized_error}', details={'original_error': sanitized_error}) from e
    async def _connect_direct(self) -> None:
        jpype = self._jpype
        JException = self._JException
        try:
            java_sql_DriverManager = jpype.JClass('java.sql.DriverManager')
            java_util_Properties = jpype.JClass('java.util.Properties')
            jdbc_url = self._build_jdbc_url()
            properties = java_util_Properties()
            properties.setProperty('user', self._config.user)
            properties.setProperty('password', self._config.password)
            properties.setProperty('secure', 'true' if self._config.ssl else 'false')
            properties.setProperty('prompt', 'false')
            properties.setProperty('libraries', self._config.database)
            properties.setProperty('login timeout', str(self._config.connection_timeout))
            properties.setProperty('query timeout', str(self._config.query_timeout))
            properties.setProperty('transaction isolation', 'read committed')
            properties.setProperty('date format', 'iso')
            properties.setProperty('errors', 'full')
            if self._config.read_only:
                properties.setProperty('access', 'read only')
            self._logger.info('Connecting to AS400 database directly', extra={'database': self._config.database, 'server': self._config.server, 'ssl': self._config.ssl})
            loop = asyncio.get_running_loop()
            def connect_sync() -> Any:
                start_time = time.time()
                conn = java_sql_DriverManager.getConnection(jdbc_url, properties)
                self._connection_time = time.time() - start_time
                return conn
            conn = await loop.run_in_executor(None, connect_sync)
            def configure_connection() -> None:
                conn.setAutoCommit(True)
                if self._config.read_only:
                    conn.setReadOnly(True)
            await loop.run_in_executor(None, configure_connection)
            self._connection_properties = {}
            prop_keys = properties.keySet().toArray()
            for key in prop_keys:
                str_key = str(key)
                if str_key != 'password':
                    self._connection_properties[str_key] = str(properties.getProperty(str_key))
            self._connection = conn
            self._connected = True
            self._logger.info('Successfully connected to AS400 database directly', extra={'database': self._config.database, 'server': self._config.server, 'connection_time_ms': int(self._connection_time * 1000)})
        except JException as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error('Failed to connect to AS400 directly', extra={'error': sanitized_error})
            if any((keyword in error_msg.lower() for keyword in ['permission', 'access denied', 'authorization'])):
                raise SecurityError(message=f'Security error connecting to AS400: {sanitized_error}', details={'original_error': sanitized_error}) from e
            else:
                raise DatabaseError(message=f'Failed to connect to AS400 database: {sanitized_error}', details={'original_error': sanitized_error}) from e
    async def disconnect(self) -> None:
        if not self._connection and (not self._registered_connection_id):
            self._connected = False
            return
        try:
            if self._registered_connection_id:
                self._connected = False
                self._logger.debug('AS400 database_manager connection marked as closed')
                if self._accessed_tables:
                    self._logger.info('AS400 session accessed tables', extra={'tables': sorted(self._accessed_tables)})
                return
            loop = asyncio.get_running_loop()
            def close_sync() -> None:
                self._connection.close()
            await loop.run_in_executor(None, close_sync)
            self._connection = None
            self._connected = False
            self._logger.debug('AS400 connection closed')
            if self._accessed_tables:
                self._logger.info('AS400 session accessed tables', extra={'tables': sorted(self._accessed_tables)})
        except Exception as e:
            if isinstance(e, self._JException):
                self._logger.error('Error closing AS400 connection', extra={'error': str(e)})
                raise DatabaseError(message=f'Failed to close AS400 connection: {str(e)}', details={'original_error': str(e)}) from e
            else:
                raise
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]]=None, limit: Optional[int]=None) -> Dict[str, Any]:
        if not self._connected:
            await self.connect()
        if not self._connected:
            raise DatabaseError(message='Not connected to AS400 database', details={'connection_id': self._config.name})
        result = self._create_query_result(query)
        table_name = self._validate_and_prepare_query(query, limit)
        self._query_cancel_event = asyncio.Event()
        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing AS400 query', extra={'query': sanitized_query, 'limit': limit, 'using_db_manager': self._registered_connection_id is not None})
            if self._registered_connection_id and self._database_manager:
                result = await self._execute_query_with_database_manager(query, params, limit)
                if table_name:
                    self._accessed_tables.add(table_name.upper())
                self._logger.info('Successfully executed query on AS400 via database_manager', extra={'record_count': result['row_count'], 'execution_time_ms': result['execution_time_ms'], 'table': table_name if table_name else None})
                return result
            jpype = self._jpype
            JException = self._JException
            result = self._create_query_result(query)
            java_sql_Types = jpype.JClass('java.sql.Types')
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing AS400 query directly', extra={'query': sanitized_query, 'limit': limit})
            loop = asyncio.get_running_loop()
            def execute_query_sync() -> Tuple[Any, Any, float]:
                start_time = time.time()
                if params:
                    prepared_query, param_values = self._convert_to_prepared_statement(query, params or {})
                    statement = self._connection.prepareStatement(prepared_query)
                    for i, value in enumerate(param_values):
                        self._set_prepared_statement_parameter(statement, i + 1, value, java_sql_Types)
                    statement.setQueryTimeout(self._config.query_timeout)
                    result_set = statement.executeQuery()
                else:
                    statement = self._connection.createStatement()
                    statement.setQueryTimeout(self._config.query_timeout)
                    result_set = statement.executeQuery(query)
                execution_time = time.time() - start_time
                return (result_set, statement, execution_time)
            result_set, statement, execution_time = await loop.run_in_executor(None, execute_query_sync)
            def process_results() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
                records, columns = self._process_result_set(result_set, java_sql_Types)
                result_set.close()
                statement.close()
                return (records, columns)
            records, columns = await loop.run_in_executor(None, process_results)
            if table_name:
                self._accessed_tables.add(table_name.upper())
            result['records'] = records
            result['columns'] = columns
            result['row_count'] = len(records)
            result['execution_time_ms'] = int(execution_time * 1000)
            result['truncated'] = limit is not None and result['row_count'] >= limit
            self._logger.info('Successfully executed query on AS400 directly', extra={'record_count': result['row_count'], 'execution_time_ms': result['execution_time_ms'], 'table': table_name if table_name else None})
            return result
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error('Error executing query on AS400', extra={'error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)})
            result['has_error'] = True
            result['error_message'] = sanitized_error
            if any((keyword in error_msg.lower() for keyword in ['permission', 'access denied', 'authorization'])):
                raise SecurityError(message=f'Security error executing AS400 query: {sanitized_error}', details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}) from e
            else:
                raise DatabaseError(message=f'Failed to execute AS400 query: {sanitized_error}', details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}) from e
        finally:
            self._query_cancel_event = None
    async def get_tables(self, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        if not self._connected:
            await self.connect()
        try:
            if self._registered_connection_id and self._database_manager:
                return await self._get_tables_with_database_manager(schema)
            return await self._get_tables_direct(schema)
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting schema information: {sanitized_error}')
            raise DatabaseError(message=f'Failed to get schema information: {sanitized_error}', details={'schema': schema}) from e
    async def _get_tables_with_database_manager(self, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        schema_name = schema or self._config.database
        tables = []
        try:
            sql = f"\n                SELECT \n                    TABLE_NAME, \n                    TABLE_TYPE,\n                    REMARKS \n                FROM SYSIBM.TABLES \n                WHERE TABLE_SCHEMA = '{schema_name.upper()}'\n                AND (TABLE_TYPE = 'TABLE' OR TABLE_TYPE = 'VIEW')\n                ORDER BY TABLE_NAME\n            "
            table_rows = await self._database_manager.execute_raw(sql=sql, connection_name=self._registered_connection_id)
            for row in table_rows:
                table_name = row['TABLE_NAME']
                table_type = row['TABLE_TYPE']
                remarks = row.get('REMARKS', None)
                columns = await self.get_table_columns(table_name, schema)
                tables.append({'name': table_name, 'type': table_type, 'schema': schema_name.upper(), 'remarks': remarks, 'columns': columns})
            return tables
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting schema information: {sanitized_error}')
            raise DatabaseError(message=f'Failed to get schema information: {sanitized_error}', details={'schema': schema_name}) from e
    async def _get_tables_direct(self, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        schema_name = schema or self._config.database
        def get_tables_sync() -> List[Dict[str, Any]]:
            metadata = self._connection.getMetaData()
            result_set = metadata.getTables(None, schema_name.upper(), '%', ['TABLE', 'VIEW'])
            tables = []
            while result_set.next():
                table_name = result_set.getString('TABLE_NAME')
                table_type = result_set.getString('TABLE_TYPE')
                remarks = result_set.getString('REMARKS')
                columns_rs = metadata.getColumns(None, schema_name.upper(), table_name, '%')
                columns = []
                while columns_rs.next():
                    column_name = columns_rs.getString('COLUMN_NAME')
                    data_type = columns_rs.getString('TYPE_NAME')
                    column_size = columns_rs.getInt('COLUMN_SIZE')
                    nullable = columns_rs.getInt('NULLABLE') == 1
                    col_remarks = columns_rs.getString('REMARKS')
                    column_type_code = columns_rs.getInt('DATA_TYPE')
                    precision = 0
                    scale = 0
                    try:
                        precision = columns_rs.getInt('PRECISION')
                        scale = columns_rs.getInt('SCALE')
                    except Exception:
                        pass
                    columns.append({'name': column_name, 'type_name': data_type, 'type_code': column_type_code, 'precision': precision, 'scale': scale, 'nullable': nullable, 'table_name': table_name, 'remarks': col_remarks})
                columns_rs.close()
                tables.append({'name': table_name, 'type': table_type, 'schema': schema_name.upper(), 'remarks': remarks, 'columns': columns})
            result_set.close()
            return tables
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, get_tables_sync)
    async def get_table_columns(self, table_name: str, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        if not self._connected:
            await self.connect()
        try:
            if self._registered_connection_id and self._database_manager:
                return await self._get_table_columns_with_database_manager(table_name, schema)
            return await self._get_table_columns_direct(table_name, schema)
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting column information: {sanitized_error}')
            raise DatabaseError(message=f'Failed to get column information: {sanitized_error}', details={'table': table_name, 'schema': schema}) from e
    async def _get_table_columns_with_database_manager(self, table_name: str, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        schema_name = schema or self._config.database
        try:
            sql = f"\n                SELECT \n                    COLUMN_NAME, \n                    TYPE_NAME,\n                    COLUMN_SIZE,\n                    NULLABLE,\n                    REMARKS,\n                    DATA_TYPE,\n                    DECIMAL_DIGITS\n                FROM SYSIBM.COLUMNS \n                WHERE TABLE_SCHEMA = '{schema_name.upper()}'\n                AND TABLE_NAME = '{table_name.upper()}'\n                ORDER BY ORDINAL_POSITION\n            "
            columns_data = await self._database_manager.execute_raw(sql=sql, connection_name=self._registered_connection_id)
            columns = []
            for row in columns_data:
                column_name = row['COLUMN_NAME']
                data_type = row['TYPE_NAME']
                column_size = row.get('COLUMN_SIZE', 0)
                nullable = row.get('NULLABLE', 1) == 1
                col_remarks = row.get('REMARKS')
                column_type_code = row.get('DATA_TYPE', 0)
                precision = column_size
                scale = row.get('DECIMAL_DIGITS', 0)
                columns.append({'name': column_name, 'type_name': data_type, 'type_code': column_type_code, 'precision': precision, 'scale': scale, 'nullable': nullable, 'table_name': table_name, 'remarks': col_remarks})
            return columns
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting column information: {sanitized_error}')
            raise DatabaseError(message=f'Failed to get column information: {sanitized_error}', details={'table': table_name, 'schema': schema_name}) from e
    async def _get_table_columns_direct(self, table_name: str, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        schema_name = schema or self._config.database
        def get_columns_sync() -> List[Dict[str, Any]]:
            metadata = self._connection.getMetaData()
            result_set = metadata.getColumns(None, schema_name.upper(), table_name, '%')
            columns = []
            while result_set.next():
                column_name = result_set.getString('COLUMN_NAME')
                data_type = result_set.getString('TYPE_NAME')
                column_size = result_set.getInt('COLUMN_SIZE')
                nullable = result_set.getInt('NULLABLE') == 1
                remarks = result_set.getString('REMARKS')
                column_type_code = result_set.getInt('DATA_TYPE')
                precision = 0
                scale = 0
                try:
                    precision = result_set.getInt('PRECISION')
                    scale = result_set.getInt('SCALE')
                except Exception:
                    pass
                columns.append({'name': column_name, 'type_name': data_type, 'type_code': column_type_code, 'precision': precision, 'scale': scale, 'nullable': nullable, 'table_name': table_name, 'remarks': remarks})
            result_set.close()
            return columns
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, get_columns_sync)
    def get_connection_info(self) -> Dict[str, Any]:
        info = {'connected': self._connected, 'connection_id': self._config.name, 'name': self._config.name, 'server': self._config.server, 'database': self._config.database, 'user': self._config.user, 'ssl': self._config.ssl, 'type': 'AS400', 'read_only': self._config.read_only, 'using_db_manager': self._registered_connection_id is not None}
        if self._connection_time is not None:
            info['connection_time_ms'] = int(self._connection_time * 1000)
        if self._accessed_tables:
            info['accessed_tables'] = sorted(self._accessed_tables)
        return info
    def _build_jdbc_url(self) -> str:
        jdbc_url = f'jdbc:as400://{self._config.server}'
        if self._config.port:
            jdbc_url += f':{self._config.port}'
        params = []
        if self._config.database:
            params.append(f'libraries={self._config.database}')
        if self._config.ssl:
            params.append('secure=true')
        if params:
            jdbc_url += ';' + ';'.join(params)
        return jdbc_url
    def _validate_and_prepare_query(self, query: str, limit: Optional[int]=None) -> Optional[str]:
        if ' ' not in query:
            table_name = query.strip()
            if self._config.allowed_tables:
                if table_name.upper() not in self._config.allowed_tables:
                    raise SecurityError(message=f"Access to table '{table_name}' is not allowed", details={'table': table_name, 'allowed_tables': self._config.allowed_tables})
            full_table_name = f'{self._config.database}.{table_name}'
            limit_clause = f' FETCH FIRST {limit} ROWS ONLY' if limit is not None else ''
            query = f'SELECT * FROM {full_table_name}{limit_clause}'
            return table_name
        else:
            query_upper = query.upper()
            if self._config.read_only and any((write_op in query_upper for write_op in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 'RENAME'])):
                raise SecurityError(message='Write operations are not allowed on read-only connection', details={'query': self._sanitize_sql_for_logging(query)})
            if limit is not None and 'LIMIT' not in query_upper and ('FETCH FIRST' not in query_upper):
                if ';' in query:
                    query = query.rstrip(';')
                query = f'{query} FETCH FIRST {limit} ROWS ONLY'
            return None
    def _convert_to_prepared_statement(self, query: str, params: Dict[str, Any]) -> Tuple[str, List[Any]]:
        param_names = re.findall(':(\\w+)', query)
        param_values = []
        for name in param_names:
            if name not in params:
                raise ValueError(f"Parameter '{name}' not provided in params dictionary")
            param_values.append(params[name])
            query = query.replace(f':{name}', '?', 1)
        return (query, param_values)
    def _set_prepared_statement_parameter(self, statement: Any, index: int, value: Any, java_sql_Types: Any) -> None:
        jpype = self._jpype
        if value is None:
            statement.setNull(index, java_sql_Types.NULL)
            return
        if isinstance(value, str):
            statement.setString(index, value)
        elif isinstance(value, int):
            statement.setInt(index, value)
        elif isinstance(value, float):
            statement.setDouble(index, value)
        elif isinstance(value, bool):
            statement.setBoolean(index, value)
        elif hasattr(value, 'isoformat'):
            if hasattr(value, 'hour'):
                timestamp = jpype.JClass('java.sql.Timestamp')
                mills = int(value.timestamp() * 1000)
                statement.setTimestamp(index, timestamp(mills))
            else:
                date = jpype.JClass('java.sql.Date')
                mills = int(value.toordinal() * 86400 * 1000)
                statement.setDate(index, date(mills))
        else:
            statement.setString(index, str(value))
    def _process_result_set(self, result_set: Any, java_sql_Types: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        meta = result_set.getMetaData()
        column_count = meta.getColumnCount()
        columns: List[Dict[str, Any]] = []
        for i in range(1, column_count + 1):
            table_name = None
            try:
                table_name = meta.getTableName(i)
            except Exception:
                pass
            columns.append({'name': meta.getColumnName(i), 'type_name': meta.getColumnTypeName(i), 'type_code': meta.getColumnType(i), 'precision': meta.getPrecision(i), 'scale': meta.getScale(i), 'nullable': meta.isNullable(i) != 0, 'table_name': table_name, 'remarks': None})
        records = []
        while result_set.next():
            row = {}
            for i, col in enumerate(columns, 1):
                value = self._get_result_set_value(result_set, i, col, java_sql_Types)
                row[col['name']] = value
            records.append(row)
        return (records, columns)
    def _get_result_set_value(self, result_set: Any, index: int, column: Dict[str, Any], java_sql_Types: Any) -> Any:
        if result_set.getObject(index) is None:
            return None
        type_code = column['type_code']
        if type_code in (java_sql_Types.CHAR, java_sql_Types.VARCHAR, java_sql_Types.LONGVARCHAR):
            return result_set.getString(index)
        elif type_code in (java_sql_Types.TINYINT, java_sql_Types.SMALLINT, java_sql_Types.INTEGER):
            return result_set.getInt(index)
        elif type_code in (java_sql_Types.BIGINT,):
            return result_set.getLong(index)
        elif type_code in (java_sql_Types.FLOAT, java_sql_Types.DOUBLE, java_sql_Types.REAL):
            return result_set.getDouble(index)
        elif type_code in (java_sql_Types.DECIMAL, java_sql_Types.NUMERIC):
            big_decimal = result_set.getBigDecimal(index)
            if column['scale'] == 0:
                return int(big_decimal.longValue())
            else:
                return float(big_decimal.doubleValue())
        elif type_code == java_sql_Types.DATE:
            date = result_set.getDate(index)
            from datetime import date as py_date
            return py_date(date.getYear() + 1900, date.getMonth() + 1, date.getDate())
        elif type_code == java_sql_Types.TIME:
            time = result_set.getTime(index)
            from datetime import time as py_time
            return py_time(time.getHours(), time.getMinutes(), time.getSeconds())
        elif type_code == java_sql_Types.TIMESTAMP:
            timestamp = result_set.getTimestamp(index)
            from datetime import datetime
            return datetime(timestamp.getYear() + 1900, timestamp.getMonth() + 1, timestamp.getDate(), timestamp.getHours(), timestamp.getMinutes(), timestamp.getSeconds(), timestamp.getNanos() // 1000)
        elif type_code == java_sql_Types.BOOLEAN:
            return result_set.getBoolean(index)
        elif type_code in (java_sql_Types.BINARY, java_sql_Types.VARBINARY, java_sql_Types.LONGVARBINARY):
            java_bytes = result_set.getBytes(index)
            return bytes(java_bytes)
        else:
            return str(result_set.getObject(index))