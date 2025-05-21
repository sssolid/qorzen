from __future__ import annotations

"""
SQLite database connector for the Database Manager.

This module provides a connector for SQLite databases, integrated with the
asyncio-based architecture of the database manager.
"""

import asyncio
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, AsyncGenerator

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from .base import BaseDatabaseConnector


class AsyncCompatibleSession:
    """A wrapper around synchronous SQLite session to provide async interface."""

    def __init__(self, sync_session: Session, loop: asyncio.AbstractEventLoop) -> None:
        """Initialize the async-compatible session wrapper.

        Args:
            sync_session: The synchronous SQLite session
            loop: The asyncio event loop for executing synchronous operations
        """
        self._session = sync_session
        self._loop = loop

    async def __aenter__(self) -> "AsyncCompatibleSession":
        """Async context manager entry point."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit point."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self.close()

    async def execute(self, statement, *args, **kwargs) -> Any:
        """Execute a statement asynchronously.

        Args:
            statement: The SQL statement to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the execution
        """
        return await self._loop.run_in_executor(
            None,
            lambda: self._session.execute(statement, *args, **kwargs)
        )

    async def commit(self) -> None:
        """Commit the session asynchronously."""
        await self._loop.run_in_executor(None, self._session.commit)

    async def rollback(self) -> None:
        """Rollback the session asynchronously."""
        await self._loop.run_in_executor(None, self._session.rollback)

    async def close(self) -> None:
        """Close the session asynchronously."""
        await self._loop.run_in_executor(None, self._session.close)


class SQLiteConnector(BaseDatabaseConnector):
    def __init__(self, config: Any, logger: Any, security_manager: Optional[Any] = None) -> None:
        super().__init__(config, logger, security_manager)
        self._config = config
        self._connection: Optional[Any] = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

        try:
            import sqlite3
            self._sqlite_version = sqlite3.sqlite_version
        except ImportError:
            self._logger.error('sqlite3 module is required for SQLite connections.')
            raise ImportError('sqlite3 module is required for SQLite connections.')

    def _create_database_manager_config(self) -> Any:
        from qorzen.core.database_manager import DatabaseConnectionConfig
        db_path = self._config.database
        return DatabaseConnectionConfig(
            name=self._registered_connection_id or f'sqlite_{self._config.name}',
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

                if self._database_manager:
                    success = await self._register_with_database_manager()
                    if success:
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

                # Direct connection approach - use traditional SQLite for file-based databases
                try:
                    from sqlalchemy import create_engine

                    if db_path == ':memory:':
                        # For in-memory databases
                        uri_path = 'sqlite:///:memory:'
                    else:
                        # For file-based databases
                        db_path = os.path.abspath(os.path.expanduser(db_path))
                        db_dir = os.path.dirname(db_path)

                        if not os.path.exists(db_dir):
                            os.makedirs(db_dir, exist_ok=True)

                        uri_path = f'sqlite:///{db_path}'
                        if self._config.read_only:
                            uri_path += '?mode=ro'

                    self._engine = create_engine(
                        uri_path,
                        connect_args={'timeout': getattr(self._config, 'connection_timeout', 10)},
                        echo=False
                    )
                    self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

                    # Test the connection
                    with self._engine.connect() as conn:
                        conn.execute(text('PRAGMA foreign_keys = ON'))
                        conn.execute(text('SELECT 1'))

                    self._connection_time = time.time() - start_time
                    self._connected = True
                    self._logger.info('Successfully connected to SQLite database directly', extra={
                        'database': db_path,
                        'connection_time_ms': int(self._connection_time * 1000),
                        'sqlite_version': self._sqlite_version
                    })

                except ImportError:
                    # Fall back to aiosqlite if SQLAlchemy is not available
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
                        self._connection = await aiosqlite.connect(uri_path, uri=True,
                                                                   timeout=getattr(self._config, 'connection_timeout',
                                                                                   10))

                    await self._connection.execute('PRAGMA foreign_keys = ON')
                    self._connection.row_factory = self._dict_factory
                    self._connection_time = time.time() - start_time
                    self._connected = True
                    self._logger.info('Successfully connected to SQLite database using aiosqlite', extra={
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
        if not self._connected:
            return

        try:
            if self._registered_connection_id:
                self._connected = False
                self._logger.debug('SQLite database_manager connection marked as closed')
            elif self._connection:
                await self._connection.close()
                self._connection = None
                self._connected = False
                self._logger.debug('SQLite connection closed')
            elif self._engine:
                self._engine.dispose()
                self._engine = None
                self._session_factory = None
                self._connected = False
                self._logger.debug('SQLite engine disposed')

            if self._accessed_tables:
                self._logger.info('SQLite session accessed tables', extra={'tables': sorted(self._accessed_tables)})

        except Exception as e:
            self._logger.error('Error closing SQLite connection', extra={'error': str(e)})
            raise DatabaseError(
                message=f'Failed to close SQLite connection: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> \
    Dict[str, Any]:
        if not self._connected:
            await self.connect()

        result = self._create_query_result(query)
        query, table_name = self._validate_and_prepare_query(query, limit)
        self._query_cancel_event = asyncio.Event()

        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug('Executing SQLite query', extra={
                'query': sanitized_query,
                'limit': limit,
                'using_db_manager': self._registered_connection_id is not None
            })

            if self._registered_connection_id and self._database_manager:
                result = await self._execute_query_with_database_manager(query, params, limit)
                if table_name:
                    self._accessed_tables.add(table_name.upper())
                self._logger.info('Successfully executed query on SQLite via database_manager', extra={
                    'record_count': result['row_count'],
                    'execution_time_ms': result['execution_time_ms'],
                    'table': table_name if table_name else None
                })
                return result

            start_time = time.time()

            if self._engine and self._session_factory:
                # Use SQLAlchemy for query execution
                loop = asyncio.get_running_loop()

                def execute_sync():
                    with self._session_factory() as session:
                        if params:
                            stmt = text(query)
                            rs = session.execute(stmt, params or {})
                        else:
                            rs = session.execute(text(query))

                        # Get column info
                        columns = [col[0] for col in rs.cursor.description] if rs.cursor.description else []

                        # Convert to list of dicts
                        records = [dict(zip(columns, row)) for row in rs.fetchall()]
                        return records, columns

                records, column_names = await loop.run_in_executor(None, execute_sync)

                # Create column metadata
                columns = [
                    {
                        'name': name,
                        'type_name': 'UNKNOWN',
                        'type_code': 0,
                        'precision': 0,
                        'scale': 0,
                        'nullable': True,
                        'table_name': None
                    }
                    for name in column_names
                ]

            elif self._connection:
                # Use direct aiosqlite connection
                if params:
                    prepared_query, param_values = self._convert_to_prepared_statement(query, params)
                    cursor = await self._connection.execute(prepared_query, param_values)
                else:
                    cursor = await self._connection.execute(query)

                records = await cursor.fetchall()
                columns = await self._get_column_metadata(cursor)
                await cursor.close()
            else:
                raise DatabaseError(
                    message="No database connection available",
                    details={"query": sanitized_query}
                )

            execution_time = time.time() - start_time

            if table_name:
                self._accessed_tables.add(table_name.upper())

            result['records'] = records
            result['columns'] = columns
            result['row_count'] = len(records)
            result['execution_time_ms'] = int(execution_time * 1000)
            result['truncated'] = limit is not None and result['row_count'] >= limit

            self._logger.info('Successfully executed query on SQLite directly', extra={
                'record_count': result['row_count'],
                'execution_time_ms': result['execution_time_ms'],
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

            result['has_error'] = True
            result['error_message'] = sanitized_error

            if any(keyword in error_msg.lower() for keyword in ['permission', 'access denied', 'authorization']):
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

    async def get_tables(self, schema: Optional[str] = None) -> List[Dict[str, Any]]:
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

            if self._registered_connection_id and self._database_manager:
                table_rows = await self._database_manager.execute_raw(
                    sql=query,
                    connection_name=self._registered_connection_id
                )
            elif self._engine and self._session_factory:
                loop = asyncio.get_running_loop()

                def execute_sync():
                    with self._session_factory() as session:
                        rs = session.execute(text(query))
                        return [dict(zip(['name', 'type'], row)) for row in rs.fetchall()]

                table_rows = await loop.run_in_executor(None, execute_sync)
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
                tables.append({
                    'name': table_name,
                    'type': table_type,
                    'schema': None,
                    'remarks': None,
                    'columns': columns
                })

            return tables

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f'Error getting schema information: {sanitized_error}')

            raise DatabaseError(
                message=f'Failed to get schema information: {sanitized_error}',
                details={'schema': schema}
            ) from e

    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self._connected:
            await self.connect()

        try:
            query = f"PRAGMA table_info('{table_name}')"

            if self._registered_connection_id and self._database_manager:
                column_rows = await self._database_manager.execute_raw(
                    sql=query,
                    connection_name=self._registered_connection_id
                )
            elif self._engine and self._session_factory:
                loop = asyncio.get_running_loop()

                def execute_sync():
                    with self._session_factory() as session:
                        rs = session.execute(text(query))
                        columns = ['cid', 'name', 'type', 'notnull', 'default_value', 'pk']
                        return [dict(zip(columns, row)) for row in rs.fetchall()]

                column_rows = await loop.run_in_executor(None, execute_sync)
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

                if 'DECIMAL' in col_type.upper() or 'NUMERIC' in col_type.upper():
                    match = re.search('\\((\\d+)(?:,(\\d+))?\\)', col_type)
                    if match:
                        precision = int(match.group(1))
                        if match.group(2):
                            scale = int(match.group(2))

                columns.append({
                    'name': col_name,
                    'type_name': col_type,
                    'type_code': 99,
                    'precision': precision,
                    'scale': scale,
                    'nullable': nullable,
                    'table_name': table_name,
                    'remarks': None
                })

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
        info = {
            'connected': self._connected,
            'connection_id': self._config.name,
            'name': self._config.name,
            'database': self._config.database,
            'type': 'SQLite',
            'read_only': self._config.read_only,
            'version': getattr(self, '_sqlite_version', 'Unknown'),
            'using_db_manager': self._registered_connection_id is not None,
            'using_sqlalchemy': self._engine is not None
        }

        if self._connection_time is not None:
            info['connection_time_ms'] = int(self._connection_time * 1000)

        if self._accessed_tables:
            info['accessed_tables'] = sorted(self._accessed_tables)

        return info

    # Key addition: Support for async sessions
    async def async_session(self) -> AsyncGenerator[AsyncCompatibleSession, None]:
        """Provide an async-compatible session for SQLite.

        This method bridges the gap between synchronous SQLite and async code
        by wrapping a synchronous session in an async-compatible interface.

        Yields:
            AsyncCompatibleSession: An async-compatible session wrapper

        Raises:
            DatabaseError: If the connection is not initialized or session creation fails
        """
        if not self._connected:
            await self.connect()

        if not self._engine or not self._session_factory:
            raise DatabaseError(
                message="SQLite engine or session factory not initialized",
                details={"connection_name": self._config.name}
            )

        loop = asyncio.get_running_loop()
        session = self._session_factory()

        try:
            wrapper = AsyncCompatibleSession(session, loop)
            yield wrapper
        except Exception as e:
            await loop.run_in_executor(None, session.rollback)
            await loop.run_in_executor(None, session.close)
            raise DatabaseError(
                message=f"Error during SQLite async session: {str(e)}",
                details={"original_error": str(e)}
            ) from e
        finally:
            await loop.run_in_executor(None, session.close)

    def _convert_to_prepared_statement(self, query: str, params: Dict[str, Any]) -> Tuple[str, List[Any]]:
        param_names = re.findall(':(\\w+)', query)
        param_values = []

        for name in param_names:
            if name not in params:
                raise ValueError(f"Parameter '{name}' not provided in params dictionary")

            param_values.append(params[name])
            query = query.replace(f':{name}', '?', 1)

        return (query, param_values)

    async def _get_column_metadata(self, cursor: Any) -> List[Dict[str, Any]]:
        columns = []

        if cursor.description:
            for i, col_desc in enumerate(cursor.description):
                name = col_desc[0]
                columns.append({
                    'name': name,
                    'type_name': 'UNKNOWN',
                    'type_code': 0,
                    'precision': 0,
                    'scale': 0,
                    'nullable': True,
                    'table_name': None
                })

        return columns

    def _validate_and_prepare_query(self, query: str, limit: Optional[int] = None) -> Tuple[str, Optional[str]]:
        table_name = None

        if ' ' not in query:
            table_name = query.strip()

            if self._config.allowed_tables and table_name.upper() not in [t.upper() for t in
                                                                          self._config.allowed_tables]:
                raise SecurityError(
                    message=f"Access to table '{table_name}' is not allowed",
                    details={'table': table_name, 'allowed_tables': self._config.allowed_tables}
                )

            limit_clause = f' LIMIT {limit}' if limit is not None else ''
            query = f'SELECT * FROM {table_name}{limit_clause}'
            return (query, table_name)

        query_upper = query.upper()

        if self._config.read_only and any(write_op in query_upper for write_op in
                                          ['INSERT', 'UPDATE', 'DELETE', 'CREATE',
                                           'DROP', 'ALTER', 'TRUNCATE']):
            raise SecurityError(
                message='Write operations are not allowed on read-only connection',
                details={'query': self._sanitize_sql_for_logging(query)}
            )

        match = re.search('FROM\\s+([^\\s,;()]+)', query_upper)
        if match:
            table_name = match.group(1).strip('"`[]')

            if self._config.allowed_tables and table_name.upper() not in [t.upper() for t in
                                                                          self._config.allowed_tables]:
                raise SecurityError(
                    message=f"Access to table '{table_name}' is not allowed",
                    details={'table': table_name, 'allowed_tables': self._config.allowed_tables}
                )

        if limit is not None and 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        return (query, table_name)

    @staticmethod
    def _dict_factory(cursor: Any, row: Any) -> Dict[str, Any]:
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}