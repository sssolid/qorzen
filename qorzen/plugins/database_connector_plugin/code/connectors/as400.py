from __future__ import annotations

"""
AS400 database connector for the Database Connector Plugin.

This module provides a connector for AS400/iSeries databases using the
JTOpen (JT400) Java library via JPype, integrated with the updated
asyncio-based architecture.
"""

import asyncio
import os
import re
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError

from ..models import AS400ConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
from .base import BaseDatabaseConnector


class AS400Connector(BaseDatabaseConnector):
    def __init__(
            self,
            config: AS400ConnectionConfig,
            logger: Any,
            security_manager: Optional[Any] = None,
            database_manager: Optional[Any] = None,
    ) -> None:
        super().__init__(config, logger)
        self._config = config
        self._security_manager = security_manager
        self._db_manager = database_manager
        self._connection: Optional[Any] = None
        self._jpype = None
        self._JException = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None
        self._connection_properties: Dict[str, str] = {}
        self._registered_connection_id: Optional[str] = None

        try:
            import jpype
            from jpype.types import JException

            self._jpype = jpype
            self._JException = JException
            self._initialize_jpype()
        except ImportError:
            self._logger.error(
                "jpype module is required for AS400 connections. Please install it with 'pip install jpype1'."
            )
            raise ImportError(
                "jpype module is required for AS400 connections. Please install it with 'pip install jpype1'."
            )

    def _initialize_jpype(self) -> None:
        jpype = self._jpype
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[self._config.jt400_jar_path], convertStrings=True)
            self._logger.debug("JVM started for AS400 access")
            try:
                driver_class = jpype.JClass("com.ibm.as400.access.AS400JDBCDriver")
                driver = driver_class()
                jpype.JClass("java.sql.DriverManager").registerDriver(driver)
                self._logger.debug("AS400 JDBC driver registered successfully")
            except Exception as e:
                self._logger.warning(
                    "Could not register AS400 JDBC driver explicitly",
                    extra={"error": str(e)},
                )

    async def connect(self) -> None:
        async with self._connect_lock:
            if self._connected:
                return

            # Check if we can use the database_manager
            if self._db_manager is not None:
                await self._connect_with_db_manager()
                return

            # Fallback to direct connection
            await self._connect_direct()

    async def _connect_with_db_manager(self) -> None:
        """Connect to AS400 database using the database_manager"""
        try:
            self._logger.info(
                "Connecting to AS400 database via database_manager",
                extra={
                    "database": self._config.database,
                    "server": self._config.server,
                    "ssl": self._config.ssl,
                },
            )

            from qorzen.core.database_manager import DatabaseConnectionConfig

            # Create JDBC URL
            jdbc_url = self._build_jdbc_url()

            # Create a unique ID for this connection
            self._registered_connection_id = f"as400_{self._config.id}"

            # Configure connection properties
            properties = {
                "user": self._config.username,
                "password": self._config.password.get_secret_value(),
                "secure": "true" if self._config.ssl else "false",
                "prompt": "false",
                "libraries": self._config.database,
                "login timeout": str(self._config.connection_timeout),
                "query timeout": str(self._config.query_timeout),
                "transaction isolation": "read committed",
                "date format": "iso",
                "errors": "full",
            }

            if self._config.read_only:
                properties["access"] = "read only"

            # Create JDBC connection config
            start_time = time.time()
            db_config = DatabaseConnectionConfig(
                name=self._registered_connection_id,
                db_type="jdbc",
                url=jdbc_url,
                host=self._config.server,
                port=self._config.port or 446,
                database=self._config.database,
                user=self._config.username,
                password=self._config.password.get_secret_value(),
                pool_size=1,
                max_overflow=0,
                properties=properties,
                jt400_jar_path=self._config.jt400_jar_path,
            )

            if await self._db_manager.has_connection(self._registered_connection_id):
                self._logger.debug(
                    f"Connection {self._registered_connection_id} already registered"
                )
            else:
                await self._db_manager.register_connection(db_config)
                self._logger.debug(
                    f"Registered connection with database_manager: {self._registered_connection_id}"
                )

            # Test connection
            test_result = await self._db_manager.execute_raw(
                sql="SELECT 1 FROM SYSIBM.SYSDUMMY1",
                connection_name=self._registered_connection_id,
            )
            if not test_result:
                raise DatabaseError(
                    message="Failed to connect to AS400 database via database_manager",
                    details={"connection_id": self._config.id},
                )

            self._connection_time = time.time() - start_time
            self._connected = True
            self._connection_properties = properties

            self._logger.info(
                "Successfully connected to AS400 database via database_manager",
                extra={
                    "database": self._config.database,
                    "server": self._config.server,
                    "connection_time_ms": int(self._connection_time * 1000),
                },
            )
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(
                "Failed to connect to AS400 via database_manager",
                extra={"error": sanitized_error},
            )

            if any(
                    (
                            keyword in error_msg.lower()
                            for keyword in ["permission", "access denied", "authorization"]
                    )
            ):
                raise SecurityError(
                    message=f"Security error connecting to AS400: {sanitized_error}",
                    details={"original_error": sanitized_error},
                ) from e
            else:
                raise DatabaseError(
                    message=f"Failed to connect to AS400 database: {sanitized_error}",
                    details={"original_error": sanitized_error},
                ) from e

    async def _connect_direct(self) -> None:
        """Connect directly to AS400 database using JPype"""
        jpype = self._jpype
        JException = self._JException
        try:
            java_sql_DriverManager = jpype.JClass("java.sql.DriverManager")
            java_util_Properties = jpype.JClass("java.util.Properties")

            jdbc_url = self._build_jdbc_url()
            properties = java_util_Properties()
            properties.setProperty("user", self._config.username)
            properties.setProperty("password", self._config.password.get_secret_value())
            properties.setProperty("secure", "true" if self._config.ssl else "false")
            properties.setProperty("prompt", "false")
            properties.setProperty("libraries", self._config.database)
            properties.setProperty("login timeout", str(self._config.connection_timeout))
            properties.setProperty("query timeout", str(self._config.query_timeout))
            properties.setProperty("transaction isolation", "read committed")
            properties.setProperty("date format", "iso")
            properties.setProperty("errors", "full")

            if self._config.read_only:
                properties.setProperty("access", "read only")

            self._logger.info(
                "Connecting to AS400 database directly",
                extra={
                    "database": self._config.database,
                    "server": self._config.server,
                    "ssl": self._config.ssl,
                },
            )

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
                if str_key != "password":
                    self._connection_properties[str_key] = str(
                        properties.getProperty(str_key)
                    )

            self._connection = conn
            self._connected = True
            self._logger.info(
                "Successfully connected to AS400 database directly",
                extra={
                    "database": self._config.database,
                    "server": self._config.server,
                    "connection_time_ms": int(self._connection_time * 1000),
                },
            )
        except JException as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(
                "Failed to connect to AS400 directly", extra={"error": sanitized_error}
            )
            if any(
                    (
                            keyword in error_msg.lower()
                            for keyword in ["permission", "access denied", "authorization"]
                    )
            ):
                raise SecurityError(
                    message=f"Security error connecting to AS400: {sanitized_error}",
                    details={"original_error": sanitized_error},
                ) from e
            else:
                raise DatabaseError(
                    message=f"Failed to connect to AS400 database: {sanitized_error}",
                    details={"original_error": sanitized_error},
                ) from e

    async def disconnect(self) -> None:
        if not self._connection and not self._registered_connection_id:
            self._connected = False
            return

        try:
            # If we are using database_manager, we don't need to close the connection
            if self._registered_connection_id:
                self._connected = False
                self._logger.debug("AS400 database_manager connection marked as closed")
                if self._accessed_tables:
                    self._logger.info(
                        "AS400 session accessed tables",
                        extra={"tables": sorted(self._accessed_tables)},
                    )
                return

            # Otherwise close the direct connection
            loop = asyncio.get_running_loop()

            def close_sync() -> None:
                self._connection.close()

            await loop.run_in_executor(None, close_sync)
            self._connection = None
            self._connected = False
            self._logger.debug("AS400 connection closed")
            if self._accessed_tables:
                self._logger.info(
                    "AS400 session accessed tables",
                    extra={"tables": sorted(self._accessed_tables)},
                )
        except Exception as e:
            if isinstance(e, self._JException):
                self._logger.error(
                    "Error closing AS400 connection", extra={"error": str(e)}
                )
                raise DatabaseError(
                    message=f"Failed to close AS400 connection: {str(e)}",
                    details={"original_error": str(e)},
                ) from e
            else:
                raise

    async def execute_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
    ) -> QueryResult:
        if not self._connected:
            await self.connect()

        if not self._connected:
            raise DatabaseError(
                message="Not connected to AS400 database",
                details={"connection_id": self._config.id},
            )

        result = QueryResult(
            query=query, connection_id=self._config.id, executed_at=time.time()
        )
        table_name = self._validate_and_prepare_query(query, limit)
        self._query_cancel_event = asyncio.Event()

        try:
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug(
                "Executing AS400 query",
                extra={
                    "query": sanitized_query,
                    "limit": limit,
                    "using_db_manager": self._registered_connection_id is not None,
                },
            )

            # If using database_manager, use that for execution
            if self._registered_connection_id and self._db_manager:
                return await self._execute_query_with_db_manager(query, params, limit, table_name)

            # Otherwise execute directly
            return await self._execute_query_direct(query, params, limit, table_name)

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(
                "Error executing query on AS400",
                extra={"error": sanitized_error, "query": self._sanitize_sql_for_logging(query)},
            )
            result.has_error = True
            result.error_message = sanitized_error
            if any(
                    (
                            keyword in error_msg.lower()
                            for keyword in ["permission", "access denied", "authorization"]
                    )
            ):
                raise SecurityError(
                    message=f"Security error executing AS400 query: {sanitized_error}",
                    details={
                        "original_error": sanitized_error,
                        "query": self._sanitize_sql_for_logging(query),
                    },
                ) from e
            else:
                raise DatabaseError(
                    message=f"Failed to execute AS400 query: {sanitized_error}",
                    details={
                        "original_error": sanitized_error,
                        "query": self._sanitize_sql_for_logging(query),
                    },
                ) from e
        finally:
            self._query_cancel_event = None

    async def _execute_query_with_db_manager(
            self, query: str, params: Optional[Dict[str, Any]], limit: Optional[int], table_name: Optional[str]
    ) -> QueryResult:
        """Execute query using database_manager"""
        start_time = time.time()
        prepared_params = self._prepare_params_for_db_manager(params)

        if params:
            records = await self._db_manager.execute_raw(
                sql=query,
                params=prepared_params,
                connection_name=self._registered_connection_id,
            )
        else:
            records = await self._db_manager.execute_raw(
                sql=query, connection_name=self._registered_connection_id
            )

        # Get column metadata
        columns = await self._get_columns_metadata_from_db_manager(records, table_name)
        execution_time = time.time() - start_time

        if table_name:
            self._accessed_tables.add(table_name.upper())

        result = QueryResult(
            query=query, connection_id=self._config.id, executed_at=time.time()
        )
        result.records = records
        result.columns = columns
        result.row_count = len(records)
        result.execution_time_ms = int(execution_time * 1000)
        result.truncated = limit is not None and result.row_count >= limit

        self._logger.info(
            "Successfully executed query on AS400 via database_manager",
            extra={
                "record_count": result.row_count,
                "execution_time_ms": result.execution_time_ms,
                "table": table_name if table_name else None,
            },
        )

        return result

    def _prepare_params_for_db_manager(
            self, params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare parameters for database_manager execution"""
        if not params:
            return {}
        return params

    async def _get_columns_metadata_from_db_manager(
            self, records: List[Dict[str, Any]], table_name: Optional[str]
    ) -> List[ColumnMetadata]:
        """Extract column metadata from records returned by database_manager"""
        columns = []
        if not records:
            return columns

        record = records[0]
        for col_name, value in record.items():
            type_name = self._get_type_name_from_value(value)
            type_code = self._get_type_code_from_name(type_name)
            precision = 0
            scale = 0

            if isinstance(value, (int, float)):
                precision = 10
                if isinstance(value, float):
                    scale = 2

            columns.append(
                ColumnMetadata(
                    name=col_name,
                    type_name=type_name,
                    type_code=type_code,
                    precision=precision,
                    scale=scale,
                    nullable=True,
                    table_name=table_name,
                )
            )

        return columns

    def _get_type_name_from_value(self, value: Any) -> str:
        """Determine SQL type name from Python value"""
        if value is None:
            return "NULL"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "DECIMAL"
        elif isinstance(value, str):
            return "VARCHAR"
        elif isinstance(value, bytes):
            return "BINARY"
        elif isinstance(value, bool):
            return "BOOLEAN"
        elif hasattr(value, "isoformat"):  # datetime, date, time
            if hasattr(value, "hour"):
                return "TIMESTAMP"
            else:
                return "DATE"
        else:
            return "VARCHAR"

    def _get_type_code_from_name(self, type_name: str) -> int:
        """Convert type name to JDBC type code"""
        # These are approximate mappings
        type_codes = {
            "NULL": 0,
            "INTEGER": 4,
            "SMALLINT": 5,
            "DECIMAL": 3,
            "NUMERIC": 2,
            "FLOAT": 6,
            "REAL": 7,
            "DOUBLE": 8,
            "CHAR": 1,
            "VARCHAR": 12,
            "LONGVARCHAR": -1,
            "DATE": 91,
            "TIME": 92,
            "TIMESTAMP": 93,
            "BINARY": -2,
            "VARBINARY": -3,
            "BOOLEAN": 16,
        }
        return type_codes.get(type_name, 0)

    async def _execute_query_direct(
            self, query: str, params: Optional[Dict[str, Any]], limit: Optional[int], table_name: Optional[str]
    ) -> QueryResult:
        """Execute query directly using JPype connection"""
        jpype = self._jpype
        JException = self._JException
        result = QueryResult(
            query=query, connection_id=self._config.id, executed_at=time.time()
        )

        java_sql_Types = jpype.JClass("java.sql.Types")
        sanitized_query = self._sanitize_sql_for_logging(query)
        self._logger.debug(
            "Executing AS400 query directly", extra={"query": sanitized_query, "limit": limit}
        )

        loop = asyncio.get_running_loop()

        def execute_query_sync() -> Tuple[Any, Any, float]:
            start_time = time.time()
            if params:
                prepared_query, param_values = self._convert_to_prepared_statement(
                    query, params or {}
                )
                statement = self._connection.prepareStatement(prepared_query)
                for i, value in enumerate(param_values):
                    self._set_prepared_statement_parameter(
                        statement, i + 1, value, java_sql_Types
                    )
                statement.setQueryTimeout(self._config.query_timeout)
                result_set = statement.executeQuery()
            else:
                statement = self._connection.createStatement()
                statement.setQueryTimeout(self._config.query_timeout)
                result_set = statement.executeQuery(query)
            execution_time = time.time() - start_time
            return (result_set, statement, execution_time)

        result_set, statement, execution_time = await loop.run_in_executor(
            None, execute_query_sync
        )

        def process_results() -> Tuple[List[Dict[str, Any]], List[ColumnMetadata]]:
            records, columns = self._process_result_set(result_set, java_sql_Types)
            result_set.close()
            statement.close()
            return (records, columns)

        records, columns = await loop.run_in_executor(None, process_results)

        if table_name:
            self._accessed_tables.add(table_name.upper())

        result.records = records
        result.columns = columns
        result.row_count = len(records)
        result.execution_time_ms = int(execution_time * 1000)
        result.truncated = limit is not None and result.row_count >= limit

        self._logger.info(
            "Successfully executed query on AS400 directly",
            extra={
                "record_count": result.row_count,
                "execution_time_ms": result.execution_time_ms,
                "table": table_name if table_name else None,
            },
        )

        return result

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        if not self._connected:
            await self.connect()

        # Use database_manager if available
        if self._registered_connection_id and self._db_manager:
            return await self._get_tables_with_db_manager(schema)

        # Otherwise use direct connection
        return await self._get_tables_direct(schema)

    async def _get_tables_with_db_manager(
            self, schema: Optional[str] = None
    ) -> List[TableMetadata]:
        """Get tables using database_manager"""
        schema_name = schema or self._config.database
        tables = []

        try:
            # Query to get tables
            sql = f"""
                SELECT 
                    TABLE_NAME, 
                    TABLE_TYPE,
                    REMARKS 
                FROM SYSIBM.TABLES 
                WHERE TABLE_SCHEMA = '{schema_name.upper()}'
                AND (TABLE_TYPE = 'TABLE' OR TABLE_TYPE = 'VIEW')
                ORDER BY TABLE_NAME
            """

            table_rows = await self._db_manager.execute_raw(
                sql=sql, connection_name=self._registered_connection_id
            )

            for row in table_rows:
                table_name = row["TABLE_NAME"]
                table_type = row["TABLE_TYPE"]
                remarks = row.get("REMARKS", None)

                # Get columns for this table
                columns = await self.get_table_columns(table_name, schema)

                tables.append(
                    TableMetadata(
                        name=table_name,
                        type=table_type,
                        schema=schema_name.upper(),
                        remarks=remarks,
                        columns=columns,
                    )
                )

            return tables
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f"Error getting schema information: {sanitized_error}")
            raise DatabaseError(
                message=f"Failed to get schema information: {sanitized_error}",
                details={"schema": schema_name},
            ) from e

    async def _get_tables_direct(self, schema: Optional[str] = None) -> List[TableMetadata]:
        """Get tables using direct connection"""
        schema_name = schema or self._config.database

        def get_tables_sync() -> List[TableMetadata]:
            metadata = self._connection.getMetaData()
            result_set = metadata.getTables(None, schema_name.upper(), "%", ["TABLE", "VIEW"])
            tables = []
            while result_set.next():
                table_name = result_set.getString("TABLE_NAME")
                table_type = result_set.getString("TABLE_TYPE")
                remarks = result_set.getString("REMARKS")
                columns_rs = metadata.getColumns(None, schema_name.upper(), table_name, "%")
                columns = []
                while columns_rs.next():
                    column_name = columns_rs.getString("COLUMN_NAME")
                    data_type = columns_rs.getString("TYPE_NAME")
                    column_size = columns_rs.getInt("COLUMN_SIZE")
                    nullable = columns_rs.getInt("NULLABLE") == 1
                    col_remarks = columns_rs.getString("REMARKS")
                    column_type_code = columns_rs.getInt("DATA_TYPE")
                    precision = 0
                    scale = 0
                    try:
                        precision = columns_rs.getInt("PRECISION")
                        scale = columns_rs.getInt("SCALE")
                    except:
                        pass
                    columns.append(
                        ColumnMetadata(
                            name=column_name,
                            type_name=data_type,
                            type_code=column_type_code,
                            precision=precision,
                            scale=scale,
                            nullable=nullable,
                            table_name=table_name,
                            remarks=col_remarks,
                        )
                    )
                columns_rs.close()
                tables.append(
                    TableMetadata(
                        name=table_name,
                        type=table_type,
                        schema=schema_name.upper(),
                        remarks=remarks,
                        columns=columns,
                    )
                )
            result_set.close()
            return tables

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, get_tables_sync)
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f"Error getting schema information: {sanitized_error}")
            raise DatabaseError(
                message=f"Failed to get schema information: {sanitized_error}",
                details={"schema": schema_name},
            ) from e

    async def get_table_columns(
            self, table_name: str, schema: Optional[str] = None
    ) -> List[ColumnMetadata]:
        if not self._connected:
            await self.connect()

        # Use database_manager if available
        if self._registered_connection_id and self._db_manager:
            return await self._get_table_columns_with_db_manager(table_name, schema)

        # Otherwise use direct connection
        return await self._get_table_columns_direct(table_name, schema)

    async def _get_table_columns_with_db_manager(
            self, table_name: str, schema: Optional[str] = None
    ) -> List[ColumnMetadata]:
        """Get table columns using database_manager"""
        schema_name = schema or self._config.database
        try:
            # Query to get columns
            sql = f"""
                SELECT 
                    COLUMN_NAME, 
                    TYPE_NAME,
                    COLUMN_SIZE,
                    NULLABLE,
                    REMARKS,
                    DATA_TYPE,
                    DECIMAL_DIGITS
                FROM SYSIBM.COLUMNS 
                WHERE TABLE_SCHEMA = '{schema_name.upper()}'
                AND TABLE_NAME = '{table_name.upper()}'
                ORDER BY ORDINAL_POSITION
            """

            columns_data = await self._db_manager.execute_raw(
                sql=sql, connection_name=self._registered_connection_id
            )

            columns = []
            for row in columns_data:
                column_name = row["COLUMN_NAME"]
                data_type = row["TYPE_NAME"]
                column_size = row.get("COLUMN_SIZE", 0)
                nullable = row.get("NULLABLE", 1) == 1
                col_remarks = row.get("REMARKS")
                column_type_code = row.get("DATA_TYPE", 0)
                precision = column_size
                scale = row.get("DECIMAL_DIGITS", 0)

                columns.append(
                    ColumnMetadata(
                        name=column_name,
                        type_name=data_type,
                        type_code=column_type_code,
                        precision=precision,
                        scale=scale,
                        nullable=nullable,
                        table_name=table_name,
                        remarks=col_remarks,
                    )
                )

            return columns
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f"Error getting column information: {sanitized_error}")
            raise DatabaseError(
                message=f"Failed to get column information: {sanitized_error}",
                details={"table": table_name, "schema": schema_name},
            ) from e

    async def _get_table_columns_direct(
            self, table_name: str, schema: Optional[str] = None
    ) -> List[ColumnMetadata]:
        """Get table columns using direct connection"""
        schema_name = schema or self._config.database

        def get_columns_sync() -> List[ColumnMetadata]:
            metadata = self._connection.getMetaData()
            result_set = metadata.getColumns(None, schema_name.upper(), table_name, "%")
            columns = []
            while result_set.next():
                column_name = result_set.getString("COLUMN_NAME")
                data_type = result_set.getString("TYPE_NAME")
                column_size = result_set.getInt("COLUMN_SIZE")
                nullable = result_set.getInt("NULLABLE") == 1
                remarks = result_set.getString("REMARKS")
                column_type_code = result_set.getInt("DATA_TYPE")
                precision = 0
                scale = 0
                try:
                    precision = result_set.getInt("PRECISION")
                    scale = result_set.getInt("SCALE")
                except:
                    pass
                columns.append(
                    ColumnMetadata(
                        name=column_name,
                        type_name=data_type,
                        type_code=column_type_code,
                        precision=precision,
                        scale=scale,
                        nullable=nullable,
                        table_name=table_name,
                        remarks=remarks,
                    )
                )
            result_set.close()
            return columns

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, get_columns_sync)
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f"Error getting column information: {sanitized_error}")
            raise DatabaseError(
                message=f"Failed to get column information: {sanitized_error}",
                details={"table": table_name, "schema": schema_name},
            ) from e

    def get_connection_info(self) -> Dict[str, Any]:
        info = {
            "connected": self._connected,
            "connection_id": self._config.id,
            "name": self._config.name,
            "server": self._config.server,
            "database": self._config.database,
            "username": self._config.username,
            "ssl": self._config.ssl,
            "type": "AS400",
            "read_only": self._config.read_only,
            "using_db_manager": self._registered_connection_id is not None,
        }
        if self._connection_time is not None:
            info["connection_time_ms"] = int(self._connection_time * 1000)
        if self._accessed_tables:
            info["accessed_tables"] = sorted(self._accessed_tables)
        return info

    def _build_jdbc_url(self) -> str:
        jdbc_url = f"jdbc:as400://{self._config.server}"
        if self._config.port:
            jdbc_url += f":{self._config.port}"

        params = []
        if self._config.database:
            params.append(f"libraries={self._config.database}")
        if self._config.ssl:
            params.append("secure=true")

        if params:
            jdbc_url += ";" + ";".join(params)

        return jdbc_url

    def _validate_and_prepare_query(self, query: str, limit: Optional[int]) -> Optional[str]:
        if " " not in query:
            table_name = query.strip()
            if self._config.allowed_tables:
                if table_name.upper() not in self._config.allowed_tables:
                    raise SecurityError(
                        message=f"Access to table '{table_name}' is not allowed",
                        details={"table": table_name, "allowed_tables": self._config.allowed_tables},
                    )
            full_table_name = f"{self._config.database}.{table_name}"
            limit_clause = f" FETCH FIRST {limit} ROWS ONLY" if limit is not None else ""
            query = f"SELECT * FROM {full_table_name}{limit_clause}"
            return table_name
        else:
            query_upper = query.upper()
            if self._config.read_only and any(
                    (
                            write_op in query_upper
                            for write_op in [
                        "INSERT",
                        "UPDATE",
                        "DELETE",
                        "CREATE",
                        "DROP",
                        "ALTER",
                        "TRUNCATE",
                        "GRANT",
                        "REVOKE",
                        "RENAME",
                    ]
                    )
            ):
                raise SecurityError(
                    message="Write operations are not allowed on read-only connection",
                    details={"query": self._sanitize_sql_for_logging(query)},
                )

            if limit is not None and "LIMIT" not in query_upper and ("FETCH FIRST" not in query_upper):
                if ";" in query:
                    query = query.rstrip(";")
                query = f"{query} FETCH FIRST {limit} ROWS ONLY"
            return None

    def _convert_to_prepared_statement(
            self, query: str, params: Dict[str, Any]
    ) -> Tuple[str, List[Any]]:
        param_names = re.findall(r":(\w+)", query)
        param_values = []
        for name in param_names:
            if name not in params:
                raise ValueError(f"Parameter '{name}' not provided in params dictionary")
            param_values.append(params[name])
            query = query.replace(f":{name}", "?", 1)
        return (query, param_values)

    def _set_prepared_statement_parameter(
            self, statement: Any, index: int, value: Any, java_sql_Types: Any
    ) -> None:
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
        elif hasattr(value, "isoformat"):
            if hasattr(value, "hour"):
                timestamp = jpype.JClass("java.sql.Timestamp")
                mills = int(value.timestamp() * 1000)
                statement.setTimestamp(index, timestamp(mills))
            else:
                date = jpype.JClass("java.sql.Date")
                mills = int(value.toordinal() * 86400 * 1000)
                statement.setDate(index, date(mills))
        else:
            statement.setString(index, str(value))

    def _process_result_set(
            self, result_set: Any, java_sql_Types: Any
    ) -> Tuple[List[Dict[str, Any]], List[ColumnMetadata]]:
        meta = result_set.getMetaData()
        column_count = meta.getColumnCount()
        columns: List[ColumnMetadata] = []

        for i in range(1, column_count + 1):
            table_name = None
            try:
                table_name = meta.getTableName(i)
            except:
                pass
            columns.append(
                ColumnMetadata(
                    name=meta.getColumnName(i),
                    type_name=meta.getColumnTypeName(i),
                    type_code=meta.getColumnType(i),
                    precision=meta.getPrecision(i),
                    scale=meta.getScale(i),
                    nullable=meta.isNullable(i) != 0,
                    table_name=table_name,
                )
            )

        records = []
        while result_set.next():
            row = {}
            for i, col in enumerate(columns, 1):
                value = self._get_result_set_value(result_set, i, col, java_sql_Types)
                row[col.name] = value
            records.append(row)

        return (records, columns)

    def _get_result_set_value(
            self, result_set: Any, index: int, column: ColumnMetadata, java_sql_Types: Any
    ) -> Any:
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
            return datetime(
                timestamp.getYear() + 1900,
                timestamp.getMonth() + 1,
                timestamp.getDate(),
                timestamp.getHours(),
                timestamp.getMinutes(),
                timestamp.getSeconds(),
                timestamp.getNanos() // 1000,
            )
        elif type_code == java_sql_Types.BOOLEAN:
            return result_set.getBoolean(index)
        elif type_code in (
                java_sql_Types.BINARY,
                java_sql_Types.VARBINARY,
                java_sql_Types.LONGVARBINARY,
        ):
            java_bytes = result_set.getBytes(index)
            return bytes(java_bytes)
        else:
            return str(result_set.getObject(index))

    def set_database_manager(self, db_manager: Any) -> None:
        """Set the database manager to be used by this connector"""
        self._db_manager = db_manager
        self._logger.debug(f"Database manager set for AS400 connector {self._config.id}")