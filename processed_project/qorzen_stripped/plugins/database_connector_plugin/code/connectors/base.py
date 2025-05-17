from __future__ import annotations
'\nBase connector interface for the Database Connector Plugin.\n\nThis module provides the base interface that all database connectors must implement,\ndefining a consistent API for interacting with different database systems.\n'
import abc
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Protocol, TypeVar
from ..models import BaseConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
TableList = List[TableMetadata]
FieldList = List[ColumnMetadata]
T = TypeVar('T', bound=BaseConnectionConfig)
class DatabaseConnectorProtocol(Protocol[T]):
    @property
    def config(self) -> T:
        ...
    @property
    def is_connected(self) -> bool:
        ...
    async def connect(self) -> None:
        ...
    async def disconnect(self) -> None:
        ...
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]]=None, limit: Optional[int]=None) -> QueryResult:
        ...
    async def get_tables(self, schema: Optional[str]=None) -> TableList:
        ...
    async def get_table_columns(self, table_name: str, schema: Optional[str]=None) -> FieldList:
        ...
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        ...
    def get_connection_info(self) -> Dict[str, Any]:
        ...
class BaseDatabaseConnector(abc.ABC):
    def __init__(self, config: BaseConnectionConfig, logger: Any) -> None:
        self._config = config
        self._logger = logger
        self._connected = False
        self._connect_lock = asyncio.Lock()
        self._last_error: Optional[str] = None
        self._last_connect_time: Optional[float] = None
        self._query_cancel_event: Optional[asyncio.Event] = None
    @property
    def config(self) -> BaseConnectionConfig:
        return self._config
    @property
    def is_connected(self) -> bool:
        return self._connected
    @abc.abstractmethod
    async def connect(self) -> None:
        pass
    @abc.abstractmethod
    async def disconnect(self) -> None:
        pass
    @abc.abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]]=None, limit: Optional[int]=None) -> QueryResult:
        pass
    @abc.abstractmethod
    async def get_tables(self, schema: Optional[str]=None) -> TableList:
        pass
    @abc.abstractmethod
    async def get_table_columns(self, table_name: str, schema: Optional[str]=None) -> FieldList:
        pass
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        try:
            if not self._connected:
                await self.connect()
            await self.execute_query('SELECT 1')
            return (True, None)
        except Exception as e:
            error_msg = str(e)
            self._last_error = error_msg
            return (False, error_msg)
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
    def _sanitize_error_message(self, error_message: str) -> str:
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
        return query.replace('\n', ' ').replace('\r', ' ')