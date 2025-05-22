from __future__ import annotations
'\nBase connector interface for the Database Manager.\n\nThis module provides the base interface that all database connectors must implement,\ndefining a consistent API for interacting with different database systems.\n'
import abc
import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Protocol, TypeVar, cast
T = TypeVar('T', bound='BaseConnectionConfig')
class BaseDatabaseConnector(abc.ABC):
    def __init__(self, config: Any, logger: Any, security_manager: Optional[Any]=None) -> None:
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
    def config(self) -> Any:
        return self._config
    @property
    def is_connected(self) -> bool:
        return self._connected
    @property
    def database_manager(self) -> Optional[Any]:
        return self._database_manager
    @abc.abstractmethod
    async def connect(self) -> None:
        pass
    @abc.abstractmethod
    async def disconnect(self) -> None:
        pass
    @abc.abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]]=None, limit: Optional[int]=None) -> Dict[str, Any]:
        pass
    @abc.abstractmethod
    async def get_tables(self, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        pass
    @abc.abstractmethod
    async def get_table_columns(self, table_name: str, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        pass
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
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
        if self._query_cancel_event is not None:
            self._query_cancel_event.set()
            return True
        return False
    @abc.abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        pass
    def set_database_manager(self, db_manager: Any) -> None:
        self._database_manager = db_manager
        self._logger.debug(f'Database manager set for connector {self._config.name}')
    def _sanitize_error_message(self, error_message: str) -> str:
        if hasattr(self._config, 'password') and self._config.password:
            try:
                password = self._config.password
                error_message = error_message.replace(password, '[REDACTED]')
            except Exception:
                pass
        if hasattr(self._config, 'user'):
            error_message = error_message.replace(self._config.user, '[USER]')
        return error_message
    def _sanitize_sql_for_logging(self, query: str) -> str:
        return query.replace('\n', ' ').replace('\r', ' ')
    def _create_query_result(self, query: str) -> Dict[str, Any]:
        return {'query': query, 'connection_id': self._config.name, 'executed_at': datetime.now(), 'records': [], 'columns': [], 'row_count': 0, 'execution_time_ms': 0, 'has_error': False, 'error_message': None, 'truncated': False}
    def _register_accessed_table(self, table_name: Optional[str]) -> None:
        if table_name:
            self._accessed_tables.add(table_name.upper())
    async def _register_with_database_manager(self) -> bool:
        if not self._database_manager:
            self._logger.info('Database manager not set, cannot register connection')
            return False
        try:
            self._registered_connection_id = f'{self._config.db_type}_{self._config.name}'
            if await self._database_manager.has_connection(self._registered_connection_id):
                self._logger.debug(f'Connection {self._registered_connection_id} already registered')
                return True
            db_config = self._create_database_manager_config()
            await self._database_manager.register_connection(db_config)
            self._logger.debug(f'Registered connection with database_manager: {self._registered_connection_id}')
            return True
        except Exception as e:
            self._logger.warning(f'Could not register connection with database_manager: {str(e)}')
            return False
    def _create_database_manager_config(self) -> Any:
        pass
    async def _execute_query_with_database_manager(self, query: str, params: Optional[Dict[str, Any]]=None, limit: Optional[int]=None) -> Dict[str, Any]:
        from qorzen.utils.exceptions import DatabaseError
        if not self._database_manager or not self._registered_connection_id:
            raise DatabaseError(message='Cannot execute query with database manager: not registered', details={'connection_id': self._config.name})
        start_time = time.time()
        try:
            if params:
                prepared_params = self._prepare_params_for_database_manager(params)
                records = await self._database_manager.execute_raw(sql=query, params=prepared_params, connection_name=self._registered_connection_id)
            else:
                records = await self._database_manager.execute_raw(sql=query, connection_name=self._registered_connection_id)
            table_name = None
            match = re.search('FROM\\s+(["\\\\[\\\\]`]?\\w+["\\\\[\\\\]`]?)', query.upper())
            if match:
                table_name = match.group(1).strip('"[]`')
                if table_name:
                    self._accessed_tables.add(table_name.upper())
            columns = self._extract_columns_from_records(records, table_name)
            execution_time = time.time() - start_time
            result = {'query': query, 'connection_id': self._config.name, 'executed_at': datetime.now(), 'records': records, 'columns': columns, 'row_count': len(records), 'execution_time_ms': int(execution_time * 1000), 'truncated': limit is not None and len(records) >= limit, 'has_error': False, 'error_message': None}
            return result
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error executing query with database manager: {sanitized_error}', extra={'query': self._sanitize_sql_for_logging(query)})
            result = {'query': query, 'connection_id': self._config.name, 'executed_at': datetime.now(), 'records': [], 'columns': [], 'row_count': 0, 'execution_time_ms': 0, 'has_error': True, 'error_message': sanitized_error, 'truncated': False}
            raise DatabaseError(message=f'Failed to execute query: {sanitized_error}', details={'original_error': sanitized_error, 'query': self._sanitize_sql_for_logging(query)}) from e
    def _prepare_params_for_database_manager(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return params
    def _extract_columns_from_records(self, records: List[Dict[str, Any]], table_name: Optional[str]) -> List[Dict[str, Any]]:
        columns = []
        if not records:
            return columns
        record = records[0]
        for name, value in record.items():
            type_name = self._get_type_name_from_value(value)
            type_code = self._get_type_code_from_name(type_name)
            precision = 0
            scale = 0
            if isinstance(value, (int, float)):
                precision = 10
                if isinstance(value, float):
                    scale = 2
            columns.append({'name': name, 'type_name': type_name, 'type_code': type_code, 'precision': precision, 'scale': scale, 'nullable': True, 'table_name': table_name})
        return columns
    def _get_type_name_from_value(self, value: Any) -> str:
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
        elif hasattr(value, 'isoformat'):
            if hasattr(value, 'hour'):
                return 'TIMESTAMP'
            else:
                return 'DATE'
        else:
            return 'VARCHAR'
    def _get_type_code_from_name(self, type_name: str) -> int:
        type_codes = {'NULL': 0, 'INTEGER': 4, 'SMALLINT': 5, 'DECIMAL': 3, 'NUMERIC': 2, 'FLOAT': 6, 'REAL': 7, 'DOUBLE': 8, 'CHAR': 1, 'VARCHAR': 12, 'LONGVARCHAR': -1, 'DATE': 91, 'TIME': 92, 'TIMESTAMP': 93, 'BINARY': -2, 'VARBINARY': -3, 'BOOLEAN': 16}
        return type_codes.get(type_name, 0)