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
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from .base import BaseDatabaseConnector


class SQLiteConnector(BaseDatabaseConnector):
    """Connector for SQLite databases."""

    def __init__(self, config: Any, logger: Any, security_manager: Optional[Any] = None) -> None:
        """Initialize the SQLite connector.

        Args:
            config: The connection configuration
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
            self._logger.error("sqlite3 module is required for SQLite connections.")
            raise ImportError("sqlite3 module is required for SQLite connections.")

    def _create_database_manager_config(self) -> Any:
        """Create a configuration object for the database manager.

        Returns:
            Any: The database manager configuration
        """
        # Import lazily to avoid circular imports
        from qorzen.core.database_manager import DatabaseConnectionConfig

        db_path = self._config.database

        return DatabaseConnectionConfig(
            name=self._registered_connection_id or f"sqlite_{self._config.name}",
            db_type="sqlite",
            host="",
            port=0,
            database=db_path,
            user="",
            password="",
            pool_size=1,
            max_overflow=0,
            pool_recycle=3600,
            echo=False,
            read_only=self._config.read_only,
            allowed_tables=self._config.allowed_tables
        )

    async def connect(self) -> None:
        """Connect to the SQLite database.

        Raises:
            DatabaseError: If connection fails
            SecurityError: If connection is denied due to permissions
        """
        async with self._connect_lock:
            if self._connected:
                return

            try:
                db_path = self._config.database
                self._logger.info(
                    "Connecting to SQLite database",
                    extra={"database": db_path, "read_only": self._config.read_only}
                )

                start_time = time.time()

                if self._database_manager:
                    success = await self._register_with_database_manager()
                    if success:
                        try:
                            await self._database_manager.execute_raw(
                                sql="SELECT 1",
                                connection_name=self._registered_connection_id
                            )
                            self._connection_time = time.time() - start_time
                            self._connected = True
                            self._logger.info(
                                "Successfully connected to SQLite database via database_manager",
                                extra={
                                    "database": db_path,
                                    "connection_time_ms": int(self._connection_time * 1000),
                                    "sqlite_version": self._sqlite_version
                                }
                            )
                            return
                        except Exception as e:
                            self._logger.warning(f"Failed to test database_manager connection: {str(e)}")

                # If database_manager connection failed or is not available, connect directly
                import aiosqlite

                if db_path == ':memory:':
                    self._connection = await aiosqlite.connect(':memory:')
                else:
                    db_path = os.path.abspath(os.path.expanduser(db_path))
                    db_dir = os.path.dirname(db_path)

                    if not os.path.exists(db_dir):
                        os.makedirs(db_dir, exist_ok=True)

                    uri_path = f"file:{db_path}"

                    if self._config.read_only:
                        uri_path += "?mode=ro"

                    self._connection = await aiosqlite.connect(
                        uri_path,
                        uri=True,
                        timeout=self._config.connection_timeout
                    )

                await self._connection.execute("PRAGMA foreign_keys = ON")
                self._connection.row_factory = self._dict_factory

                self._connection_time = time.time() - start_time
                self._connected = True

                self._logger.info(
                    "Successfully connected to SQLite database directly",
                    extra={
                        "database": db_path,
                        "connection_time_ms": int(self._connection_time * 1000),
                        "sqlite_version": self._sqlite_version
                    }
                )

            except Exception as e:
                error_msg = str(e)
                sanitized_error = self._sanitize_error_message(error_msg)
                self._logger.error("Failed to connect to SQLite", extra={"error": sanitized_error})

                if 'readonly' in error_msg.lower() or 'permission' in error_msg.lower():
                    raise SecurityError(
                        message=f"Security error connecting to SQLite: {sanitized_error}",
                        details={"original_error": sanitized_error}
                    ) from e
                else:
                    raise DatabaseError(
                        message=f"Failed to connect to SQLite database: {sanitized_error}",
                        details={"original_error": sanitized_error}
                    ) from e

    async def disconnect(self) -> None:
        """Disconnect from the SQLite database.

        Raises:
            DatabaseError: If disconnection fails
        """
        if not self._connected:
            return

        try:
            if self._registered_connection_id:
                self._connected = False
                self._logger.debug("SQLite database_manager connection marked as closed")
            elif self._connection:
                await self._connection.close()
                self._connection = None
                self._connected = False
                self._logger.debug("SQLite connection closed")

            if self._accessed_tables:
                self._logger.info(
                    "SQLite session accessed tables",
                    extra={"tables": sorted(self._accessed_tables)}
                )

        except Exception as e:
            self._logger.error("Error closing SQLite connection", extra={"error": str(e)})
            raise DatabaseError(
                message=f"Failed to close SQLite connection: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def execute_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a query with parameters.

        Args:
            query: The SQL query
            params: Query parameters
            limit: Maximum number of rows to return

        Returns:
            Dict[str, Any]: The query results

        Raises:
            DatabaseError: If query execution fails
            SecurityError: If query execution is denied due to permissions
        """
        if not self._connected:
            await self.connect()

        result = self._create_query_result(query)
        query, table_name = self._validate_and_prepare_query(query, limit)
        self._query_cancel_event = asyncio.Event()

        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug(
                "Executing SQLite query",
                extra={
                    "query": sanitized_query,
                    "limit": limit,
                    "using_db_manager": self._registered_connection_id is not None
                }
            )

            if self._registered_connection_id and self._database_manager:
                result = await self._execute_query_with_database_manager(query, params, limit)

                if table_name:
                    self._accessed_tables.add(table_name.upper())

                self._logger.info(
                    "Successfully executed query on SQLite via database_manager",
                    extra={
                        "record_count": result["row_count"],
                        "execution_time_ms": result["execution_time_ms"],
                        "table": table_name if table_name else None
                    }
                )

                return result

            # Direct execution with aiosqlite
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

            result["records"] = records
            result["columns"] = columns
            result["row_count"] = len(records)
            result["execution_time_ms"] = int(execution_time * 1000)
            result["truncated"] = limit is not None and result["row_count"] >= limit

            self._logger.info(
                "Successfully executed query on SQLite directly",
                extra={
                    "record_count": result["row_count"],
                    "execution_time_ms": result["execution_time_ms"],
                    "table": table_name if table_name else None
                }
            )

            return result

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)

            self._logger.error(
                "Error executing query on SQLite",
                extra={
                    "error": sanitized_error,
                    "query": self._sanitize_sql_for_logging(query)
                }
            )

            result["has_error"] = True
            result["error_message"] = sanitized_error

            if any((keyword in error_msg.lower() for keyword in [
                'permission', 'access denied', 'authorization'
            ])):
                raise SecurityError(
                    message=f"Security error executing SQLite query: {sanitized_error}",
                    details={
                        "original_error": sanitized_error,
                        "query": self._sanitize_sql_for_logging(query)
                    }
                ) from e
            else:
                raise DatabaseError(
                    message=f"Failed to execute SQLite query: {sanitized_error}",
                    details={
                        "original_error": sanitized_error,
                        "query": self._sanitize_sql_for_logging(query)
                    }
                ) from e

        finally:
            self._query_cancel_event = None

    async def get_tables(self, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get a list of tables in the database.

        Args:
            schema: Schema/database name (not used for SQLite)

        Returns:
            List[Dict[str, Any]]: List of table metadata

        Raises:
            DatabaseError: If operation fails
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

            if self._registered_connection_id and self._database_manager:
                table_rows = await self._database_manager.execute_raw(
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

                tables.append({
                    "name": table_name,
                    "type": table_type,
                    "schema": None,
                    "remarks": None,
                    "columns": columns
                })

            return tables

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f"Error getting schema information: {sanitized_error}")
            raise DatabaseError(
                message=f"Failed to get schema information: {sanitized_error}",
                details={"schema": schema}
            ) from e

    async def get_table_columns(
            self,
            table_name: str,
            schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get the columns of a table.

        Args:
            table_name: The table name
            schema: Schema/database name (not used for SQLite)

        Returns:
            List[Dict[str, Any]]: List of column metadata

        Raises:
            DatabaseError: If operation fails
        """
        if not self._connected:
            await self.connect()

        try:
            query = f"PRAGMA table_info('{table_name}')"

            if self._registered_connection_id and self._database_manager:
                column_rows = await self._database_manager.execute_raw(
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

                if 'DECIMAL' in col_type.upper() or 'NUMERIC' in col_type.upper():
                    match = re.search(r'\((\d+)(?:,(\d+))?\)', col_type)
                    if match:
                        precision = int(match.group(1))
                        if match.group(2):
                            scale = int(match.group(2))

                columns.append({
                    "name": col_name,
                    "type_name": col_type,
                    "type_code": 99,  # SQLite-specific code
                    "precision": precision,
                    "scale": scale,
                    "nullable": nullable,
                    "table_name": table_name,
                    "remarks": None
                })

            return columns

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f"Error getting column information: {sanitized_error}")
            raise DatabaseError(
                message=f"Failed to get column information: {sanitized_error}",
                details={"table": table_name}
            ) from e

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information.

        Returns:
            Dict[str, Any]: Connection information
        """
        info = {
            "connected": self._connected,
            "connection_id": self._config.name,
            "name": self._config.name,
            "database": self._config.database,
            "type": "SQLite",
            "read_only": self._config.read_only,
            "version": getattr(self, "_sqlite_version", "Unknown"),
            "using_db_manager": self._registered_connection_id is not None
        }

        if self._connection_time is not None:
            info["connection_time_ms"] = int(self._connection_time * 1000)

        if self._accessed_tables:
            info["accessed_tables"] = sorted(self._accessed_tables)

        return info

    def _convert_to_prepared_statement(
            self,
            query: str,
            params: Dict[str, Any]
    ) -> Tuple[str, List[Any]]:
        """Convert a parameterized query to a prepared statement.

        Args:
            query: The SQL query with named parameters
            params: The parameter values

        Returns:
            Tuple[str, List[Any]]: The prepared statement and parameter values

        Raises:
            ValueError: If a parameter is missing
        """
        param_names = re.findall(r':(\w+)', query)
        param_values = []

        for name in param_names:
            if name not in params:
                raise ValueError(f"Parameter '{name}' not provided in params dictionary")

            param_values.append(params[name])
            query = query.replace(f":{name}", "?", 1)

        return (query, param_values)

    async def _get_column_metadata(self, cursor: Any) -> List[Dict[str, Any]]:
        """Extract column metadata from a cursor.

        Args:
            cursor: The aiosqlite cursor

        Returns:
            List[Dict[str, Any]]: Column metadata
        """
        columns = []

        if cursor.description:
            for i, col_desc in enumerate(cursor.description):
                name = col_desc[0]
                columns.append({
                    "name": name,
                    "type_name": "UNKNOWN",
                    "type_code": 0,
                    "precision": 0,
                    "scale": 0,
                    "nullable": True,
                    "table_name": None
                })

        return columns

    def _validate_and_prepare_query(
            self,
            query: str,
            limit: Optional[int] = None
    ) -> Tuple[str, Optional[str]]:
        """Validate and prepare a query for execution.

        Args:
            query: The SQL query
            limit: Maximum number of rows to return

        Returns:
            Tuple[str, Optional[str]]: The prepared query and extracted table name

        Raises:
            SecurityError: If the query is not allowed
        """
        table_name = None

        # If query is just a table name, expand it to SELECT *
        if ' ' not in query:
            table_name = query.strip()

            # Check if table is allowed
            if self._config.allowed_tables and table_name.upper() not in [t.upper() for t in
                                                                          self._config.allowed_tables]:
                raise SecurityError(
                    message=f"Access to table '{table_name}' is not allowed",
                    details={"table": table_name, "allowed_tables": self._config.allowed_tables}
                )

            # Expand to SELECT * with optional LIMIT
            limit_clause = f" LIMIT {limit}" if limit is not None else ""
            query = f"SELECT * FROM {table_name}{limit_clause}"

            return query, table_name

        # Normal query processing
        query_upper = query.upper()

        # Enforce read-only if configured
        if self._config.read_only and any((write_op in query_upper for write_op in [
            'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE'
        ])):
            raise SecurityError(
                message="Write operations are not allowed on read-only connection",
                details={"query": self._sanitize_sql_for_logging(query)}
            )

        # Extract the main table name if possible
        match = re.search(r'FROM\s+([^\s,;()]+)', query_upper)
        if match:
            table_name = match.group(1).strip('"`[]')

            # Check if table is allowed
            if self._config.allowed_tables and table_name.upper() not in [t.upper() for t in
                                                                          self._config.allowed_tables]:
                raise SecurityError(
                    message=f"Access to table '{table_name}' is not allowed",
                    details={"table": table_name, "allowed_tables": self._config.allowed_tables}
                )

        # Add LIMIT clause if not present
        if limit is not None and 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        return query, table_name

    @staticmethod
    def _dict_factory(cursor: Any, row: Any) -> Dict[str, Any]:
        """Convert a row to a dictionary.

        Args:
            cursor: The aiosqlite cursor
            row: The row data

        Returns:
            Dict[str, Any]: Row as a dictionary
        """
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}