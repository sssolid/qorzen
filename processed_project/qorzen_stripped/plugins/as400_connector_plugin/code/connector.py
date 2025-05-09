from __future__ import annotations
'\nAS400 connector for Qorzen.\n\nThis module provides a secure connector for extracting data from AS400/iSeries\ndatabases using the JTOpen (JT400) Java library via JPype, integrated with the\nQorzen framework.\n'
import os
import re
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from functools import cache
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, ColumnMetadata, QueryResult
class AS400Connector:
    def __init__(self, config: AS400ConnectionConfig, logger: Any, security_manager: Optional[Any]=None) -> None:
        self.config = config
        self._logger = logger
        self._security_manager = security_manager
        self._connection: Optional[Any] = None
        self._connection_properties: Dict[str, str] = {}
        self._accessed_tables: Set[str] = set()
        self._jpype = None
        self._JException = None
        self._connection_time: Optional[float] = None
        try:
            import jpype
            from jpype.types import JException
            self._jpype = jpype
            self._JException = JException
            self._initialize_jpype()
        except ImportError:
            self._logger.error("jpype module is required for JT400 connections. Please install it with 'pip install jpype1'.")
            raise ImportError("jpype module is required for JT400 connections. Please install it with 'pip install jpype1'.")
        self._logger.debug('AS400Connector initialized', extra={'server': config.server, 'database': config.database})
    @cache
    def _initialize_jpype(self) -> None:
        jpype = self._jpype
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[self.config.jt400_jar_path], convertStrings=True)
            self._logger.debug('JVM started for JT400 access')
            try:
                driver_class = jpype.JClass('com.ibm.as400.access.AS400JDBCDriver')
                driver = driver_class()
                jpype.JClass('java.sql.DriverManager').registerDriver(driver)
                self._logger.debug('AS400 JDBC driver registered successfully')
            except Exception as e:
                self._logger.warning('Could not register AS400 JDBC driver explicitly', extra={'error': str(e)})
    async def connect(self) -> None:
        jpype = self._jpype
        JException = self._JException
        try:
            java_sql_DriverManager = jpype.JClass('java.sql.DriverManager')
            java_util_Properties = jpype.JClass('java.util.Properties')
            jdbc_url = self._build_jdbc_url()
            properties = java_util_Properties()
            properties.setProperty('user', self.config.username)
            properties.setProperty('password', self.config.password.get_secret_value())
            properties.setProperty('secure', 'true' if self.config.ssl else 'false')
            properties.setProperty('prompt', 'false')
            properties.setProperty('libraries', self.config.database)
            properties.setProperty('login timeout', str(self.config.connection_timeout))
            properties.setProperty('query timeout', str(self.config.query_timeout))
            properties.setProperty('transaction isolation', 'read committed')
            properties.setProperty('date format', 'iso')
            properties.setProperty('errors', 'full')
            properties.setProperty('access', 'read only')
            self._logger.info('Connecting to AS400 database', extra={'database': self.config.database, 'server': self.config.server, 'ssl': self.config.ssl})
            start_time = time.time()
            conn = java_sql_DriverManager.getConnection(jdbc_url, properties)
            self._connection_time = time.time() - start_time
            conn.setAutoCommit(True)
            conn.setReadOnly(True)
            self._connection_properties = {}
            prop_keys = properties.keySet().toArray()
            for key in prop_keys:
                str_key = str(key)
                if str_key != 'password':
                    self._connection_properties[str_key] = str(properties.getProperty(str_key))
            self._connection = conn
            self._logger.info('Successfully connected to AS400 database', extra={'database': self.config.database, 'server': self.config.server, 'connection_time_ms': int(self._connection_time * 1000)})
        except JException as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error('Failed to connect to AS400', extra={'error': sanitized_error})
            if 'permission' in error_msg.lower() or 'access denied' in error_msg.lower() or 'authorization' in error_msg.lower():
                raise SecurityError(message=f'Security error connecting to AS400: {sanitized_error}', details={'original_error': sanitized_error})
            else:
                raise DatabaseError(message=f'Failed to connect to AS400 database: {sanitized_error}', details={'original_error': sanitized_error})
    async def execute_query(self, query: str, limit: Optional[int]=None, **params: Any) -> QueryResult:
        if not self._connection:
            await self.connect()
        if not self._connection:
            raise DatabaseError(message='Not connected to AS400 database', details={'connection_id': self.config.id})
        jpype = self._jpype
        JException = self._JException
        result = QueryResult(query=query, connection_id=self.config.id, executed_at=time.time())
        table_name = self._validate_and_prepare_query(query, limit)
        try:
            java_sql_Types = jpype.JClass('java.sql.Types')
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing AS400 query', extra={'query': sanitized_query, 'limit': limit})
            start_time = time.time()
            if params:
                query, param_values = self._convert_to_prepared_statement(query, params)
                statement = self._connection.prepareStatement(query)
                for i, value in enumerate(param_values):
                    self._set_prepared_statement_parameter(statement, i + 1, value, java_sql_Types)
                statement.setQueryTimeout(self.config.query_timeout)
                result_set = statement.executeQuery()
            else:
                statement = self._connection.createStatement()
                statement.setQueryTimeout(self.config.query_timeout)
                result_set = statement.executeQuery(query)
            if table_name:
                self._accessed_tables.add(table_name.upper())
            records, columns = self._process_result_set(result_set, java_sql_Types)
            execution_time = time.time() - start_time
            result.records = records
            result.columns = columns
            result.row_count = len(records)
            result.execution_time_ms = int(execution_time * 1000)
            result.truncated = limit is not None and result.row_count >= limit
            result_set.close()
            statement.close()
            self._logger.info('Successfully executed query on AS400', extra={'record_count': result.row_count, 'execution_time_ms': result.execution_time_ms, 'table': table_name if table_name else None})
            return result
        except JException as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error('Error executing query on AS400', extra={'error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)})
            result.has_error = True
            result.error_message = sanitized_error
            if 'permission' in error_msg.lower() or 'access denied' in error_msg.lower() or 'authorization' in error_msg.lower():
                raise SecurityError(message=f'Security error executing AS400 query: {sanitized_error}', details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)})
            else:
                raise DatabaseError(message=f'Failed to execute AS400 query: {sanitized_error}', details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)})
    async def close(self) -> None:
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                self._logger.debug('AS400 connection closed')
                if self._accessed_tables:
                    self._logger.info('AS400 session accessed tables', extra={'tables': sorted(self._accessed_tables)})
            except self._JException as e:
                self._logger.error('Error closing AS400 connection', extra={'error': str(e)})
                raise DatabaseError(message=f'Failed to close AS400 connection: {str(e)}', details={'original_error': str(e)})
    def _build_jdbc_url(self) -> str:
        jdbc_url = f'jdbc:as400://{self.config.server}'
        if self.config.port:
            jdbc_url += f':{self.config.port}'
        params = []
        if self.config.database:
            params.append(f'libraries={self.config.database}')
        if self.config.ssl:
            params.append('secure=true')
        if params:
            jdbc_url += ';' + ';'.join(params)
        return jdbc_url
    def _validate_and_prepare_query(self, query: str, limit: Optional[int]) -> Optional[str]:
        if ' ' not in query:
            table_name = query.strip()
            if self.config.allowed_tables:
                if table_name.upper() not in self.config.allowed_tables:
                    raise SecurityError(message=f"Access to table '{table_name}' is not allowed", details={'table': table_name, 'allowed_tables': self.config.allowed_tables})
            full_table_name = f'{self.config.database}.{table_name}'
            limit_clause = f' FETCH FIRST {limit} ROWS ONLY' if limit is not None else ''
            query = f'SELECT * FROM {full_table_name}{limit_clause}'
            return table_name
        else:
            query_upper = query.upper()
            if any((write_op in query_upper for write_op in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 'RENAME'])):
                raise SecurityError(message='Write operations are not allowed on AS400 connection', details={'query': self._sanitize_sql_for_logging(query)})
            if limit is not None and 'LIMIT' not in query_upper and ('FETCH FIRST' not in query_upper):
                if ';' in query:
                    query = query.rstrip(';')
                query = f'{query} FETCH FIRST {limit} ROWS ONLY'
            return None
    def _convert_to_prepared_statement(self, query: str, params: Dict[str, Any]) -> tuple[str, List[Any]]:
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
    def _process_result_set(self, result_set: Any, java_sql_Types: Any) -> Tuple[List[Dict[str, Any]], List[ColumnMetadata]]:
        meta = result_set.getMetaData()
        column_count = meta.getColumnCount()
        columns: List[ColumnMetadata] = []
        for i in range(1, column_count + 1):
            columns.append(ColumnMetadata(name=meta.getColumnName(i), type_name=meta.getColumnTypeName(i), type_code=meta.getColumnType(i), precision=meta.getPrecision(i), scale=meta.getScale(i), nullable=meta.isNullable(i) != 0))
        records = []
        while result_set.next():
            row = {}
            for i, col in enumerate(columns, 1):
                value = self._get_result_set_value(result_set, i, col, java_sql_Types)
                row[col.name] = value
            records.append(row)
        return (records, columns)
    def _get_result_set_value(self, result_set: Any, index: int, column: ColumnMetadata, java_sql_Types: Any) -> Any:
        if result_set.getObject(index) is None:
            return None
        type_code = column.type_code
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
            if column.scale == 0:
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
    def _sanitize_sql_for_logging(self, query: str) -> str:
        return query.replace('\n', ' ').replace('\r', ' ')
    def _sanitize_error_message(self, error_message: str) -> str:
        sanitized = error_message.replace(self.config.password.get_secret_value(), '[REDACTED]')
        sanitized = sanitized.replace(self.config.username, '[USERNAME]')
        return sanitized
    def is_connected(self) -> bool:
        if not self._connection:
            return False
        try:
            statement = self._connection.createStatement()
            statement.setQueryTimeout(5)
            result_set = statement.executeQuery('SELECT 1 FROM SYSIBM.SYSDUMMY1')
            result_set.close()
            statement.close()
            return True
        except Exception:
            self._connection = None
            return False
    def get_connection_info(self) -> Dict[str, Any]:
        info = {'connected': self.is_connected(), 'connection_id': self.config.id, 'name': self.config.name, 'server': self.config.server, 'database': self.config.database, 'username': self.config.username, 'ssl': self.config.ssl}
        if self._connection_time is not None:
            info['connection_time_ms'] = int(self._connection_time * 1000)
        if self._accessed_tables:
            info['accessed_tables'] = sorted(self._accessed_tables)
        return info
    async def get_schema_info(self, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        schema_name = schema or self.config.database
        if not self._connection:
            await self.connect()
        try:
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
                    remarks = columns_rs.getString('REMARKS')
                    columns.append({'name': column_name, 'type': data_type, 'size': column_size, 'nullable': nullable, 'remarks': remarks})
                columns_rs.close()
                tables.append({'name': table_name, 'type': table_type, 'schema': schema_name.upper(), 'remarks': remarks, 'columns': columns})
            result_set.close()
            return tables
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting schema information: {sanitized_error}')
            raise DatabaseError(message=f'Failed to get schema information: {sanitized_error}', details={'schema': schema_name})