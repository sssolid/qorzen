#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from ..models import (
    AS400ConnectionConfig,
    ColumnMetadata,
    QueryResult,
    TableMetadata,
)
from .base import BaseDatabaseConnector


class AS400Connector(BaseDatabaseConnector):
    """AS400 database connector using JT400 via JPype."""

    def __init__(
            self,
            config: AS400ConnectionConfig,
            logger: Any,
            security_manager: Optional[Any] = None
    ) -> None:
        """
        Initialize the AS400 connector.

        Args:
            config: AS400 connection configuration
            logger: Logger instance
            security_manager: Optional security manager
        """
        super().__init__(config, logger)
        self._config = config  # Type specification for the config
        self._security_manager = security_manager
        self._connection: Optional[Any] = None
        self._jpype = None
        self._JException = None
        self._accessed_tables: Set[str] = set()
        self._connection_time: Optional[float] = None
        self._connection_properties: Dict[str, str] = {}

        try:
            # Import JPype lazily to avoid hard dependency
            import jpype
            from jpype.types import JException
            self._jpype = jpype
            self._JException = JException
            self._initialize_jpype()
        except ImportError:
            self._logger.error(
                "jpype module is required for AS400 connections. "
                "Please install it with 'pip install jpype1'."
            )
            raise ImportError(
                "jpype module is required for AS400 connections. "
                "Please install it with 'pip install jpype1'."
            )

    def _initialize_jpype(self) -> None:
        """Initialize the JVM for JPype if not already started."""
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
                    extra={"error": str(e)}
                )

    async def connect(self) -> None:
        """
        Establish a connection to the AS400 database.

        Raises:
            DatabaseError: If connection fails
            SecurityError: If authentication fails
        """
        async with self._connect_lock:
            if self._connected:
                return

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

                self._logger.info("Connecting to AS400 database",
                                  extra={"database": self._config.database,
                                         "server": self._config.server,
                                         "ssl": self._config.ssl})

                # Run actual connection in a thread to avoid blocking the event loop
                loop = asyncio.get_running_loop()

                # Define a function to run in a thread
                def connect_sync() -> Any:
                    start_time = time.time()
                    conn = java_sql_DriverManager.getConnection(jdbc_url, properties)
                    self._connection_time = time.time() - start_time
                    return conn

                # Run the connection operation in a thread pool
                conn = await loop.run_in_executor(None, connect_sync)

                # Configure the connection
                def configure_connection() -> None:
                    conn.setAutoCommit(True)
                    if self._config.read_only:
                        conn.setReadOnly(True)

                # Run configuration in thread pool
                await loop.run_in_executor(None, configure_connection)

                # Store connection properties (excluding password)
                self._connection_properties = {}
                prop_keys = properties.keySet().toArray()
                for key in prop_keys:
                    str_key = str(key)
                    if str_key != "password":
                        self._connection_properties[str_key] = str(properties.getProperty(str_key))

                self._connection = conn
                self._connected = True

                self._logger.info(
                    "Successfully connected to AS400 database",
                    extra={
                        "database": self._config.database,
                        "server": self._config.server,
                        "connection_time_ms": int(self._connection_time * 1000)
                    }
                )

            except JException as e:
                error_msg = str(e)
                sanitized_error = self._sanitize_error_message(error_msg)
                self._logger.error("Failed to connect to AS400", extra={"error": sanitized_error})

                if any(keyword in error_msg.lower() for keyword in
                       ["permission", "access denied", "authorization"]):
                    raise SecurityError(
                        message=f"Security error connecting to AS400: {sanitized_error}",
                        details={"original_error": sanitized_error}
                    )
                else:
                    raise DatabaseError(
                        message=f"Failed to connect to AS400 database: {sanitized_error}",
                        details={"original_error": sanitized_error}
                    )

    async def disconnect(self) -> None:
        """
        Close the AS400 database connection.

        Raises:
            DatabaseError: If closing the connection fails
        """
        if not self._connection:
            self._connected = False
            return

        try:
            # Run in thread pool to avoid blocking
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
                    extra={"tables": sorted(self._accessed_tables)}
                )

        except Exception as e:
            if isinstance(e, self._JException):
                self._logger.error("Error closing AS400 connection", extra={"error": str(e)})
                raise DatabaseError(
                    message=f"Failed to close AS400 connection: {str(e)}",
                    details={"original_error": str(e)}
                )
            else:
                # Re-raise other exceptions
                raise

    async def execute_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None
    ) -> QueryResult:
        """
        Execute a query against the AS400 database.

        Args:
            query: SQL query to execute
            params: Optional parameters for the query
            limit: Optional row limit

        Returns:
            QueryResult containing the results and metadata

        Raises:
            DatabaseError: If query execution fails
            SecurityError: If query violates security constraints
        """
        if not self._connected or not self._connection:
            await self.connect()

        if not self._connection:
            raise DatabaseError(
                message="Not connected to AS400 database",
                details={"connection_id": self._config.id}
            )

        jpype = self._jpype
        JException = self._JException

        result = QueryResult(
            query=query,
            connection_id=self._config.id,
            executed_at=time.time()
        )

        # Validate and prepare the query, detecting table name if possible
        table_name = self._validate_and_prepare_query(query, limit)

        # Set up query cancellation
        self._query_cancel_event = asyncio.Event()

        try:
            java_sql_Types = jpype.JClass("java.sql.Types")

            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug(
                "Executing AS400 query",
                extra={"query": sanitized_query, "limit": limit}
            )

            # Define a function to run in a thread
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
                return result_set, statement, execution_time

            # Run the query execution in a thread pool
            loop = asyncio.get_running_loop()
            result_set, statement, execution_time = await loop.run_in_executor(
                None, execute_query_sync
            )

            # Process the results
            def process_results() -> Tuple[List[Dict[str, Any]], List[ColumnMetadata]]:
                records, columns = self._process_result_set(result_set, java_sql_Types)
                result_set.close()
                statement.close()
                return records, columns

            # Process the results in a thread pool
            records, columns = await loop.run_in_executor(None, process_results)

            if table_name:
                self._accessed_tables.add(table_name.upper())

            # Populate the result object
            result.records = records
            result.columns = columns
            result.row_count = len(records)
            result.execution_time_ms = int(execution_time * 1000)
            result.truncated = limit is not None and result.row_count >= limit

            self._logger.info(
                "Successfully executed query on AS400",
                extra={
                    "record_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms,
                    "table": table_name if table_name else None
                }
            )

            return result

        except JException as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)

            self._logger.error(
                "Error executing query on AS400",
                extra={
                    "error": sanitized_error,
                    "query": self._sanitize_sql_for_logging(query)
                }
            )

            result.has_error = True
            result.error_message = sanitized_error

            if any(keyword in error_msg.lower() for keyword in
                   ["permission", "access denied", "authorization"]):
                raise SecurityError(
                    message=f"Security error executing AS400 query: {sanitized_error}",
                    details={
                        "original_error": sanitized_error,
                        "query": self._sanitize_sql_for_logging(query)
                    }
                )
            else:
                raise DatabaseError(
                    message=f"Failed to execute AS400 query: {sanitized_error}",
                    details={
                        "original_error": sanitized_error,
                        "query": self._sanitize_sql_for_logging(query)
                    }
                )
        finally:
            self._query_cancel_event = None

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        """
        Get a list of tables in the specified schema.

        Args:
            schema: Schema/library name (defaults to connection database)

        Returns:
            List of TableMetadata objects

        Raises:
            DatabaseError: If retrieving tables fails
        """
        if not self._connected:
            await self.connect()

        schema_name = schema or self._config.database

        # Define a function to run in a thread
        def get_tables_sync() -> List[TableMetadata]:
            metadata = self._connection.getMetaData()
            result_set = metadata.getTables(
                None, schema_name.upper(), "%", ["TABLE", "VIEW"]
            )

            tables = []
            while result_set.next():
                table_name = result_set.getString("TABLE_NAME")
                table_type = result_set.getString("TABLE_TYPE")
                remarks = result_set.getString("REMARKS")

                # Get columns for this table
                columns_rs = metadata.getColumns(
                    None, schema_name.upper(), table_name, "%"
                )

                columns = []
                while columns_rs.next():
                    column_name = columns_rs.getString("COLUMN_NAME")
                    data_type = columns_rs.getString("TYPE_NAME")
                    column_size = columns_rs.getInt("COLUMN_SIZE")
                    nullable = columns_rs.getInt("NULLABLE") == 1
                    col_remarks = columns_rs.getString("REMARKS")
                    column_type_code = columns_rs.getInt("DATA_TYPE")

                    # These might not be available in all JDBC drivers
                    precision = 0
                    scale = 0
                    try:
                        precision = columns_rs.getInt("PRECISION")
                        scale = columns_rs.getInt("SCALE")
                    except:
                        # Ignore if not available
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
                            remarks=col_remarks
                        )
                    )

                columns_rs.close()

                tables.append(
                    TableMetadata(
                        name=table_name,
                        type=table_type,
                        schema=schema_name.upper(),
                        remarks=remarks,
                        columns=columns
                    )
                )

            result_set.close()
            return tables

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, get_tables_sync)

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f"Error getting schema information: {sanitized_error}")

            raise DatabaseError(
                message=f"Failed to get schema information: {sanitized_error}",
                details={"schema": schema_name}
            )

    async def get_table_columns(
            self,
            table_name: str,
            schema: Optional[str] = None
    ) -> List[ColumnMetadata]:
        """
        Get a list of columns in the specified table.

        Args:
            table_name: Table name
            schema: Schema/library name (defaults to connection database)

        Returns:
            List of ColumnMetadata objects

        Raises:
            DatabaseError: If retrieving columns fails
        """
        if not self._connected:
            await self.connect()

        schema_name = schema or self._config.database

        # Define a function to run in a thread
        def get_columns_sync() -> List[ColumnMetadata]:
            metadata = self._connection.getMetaData()
            result_set = metadata.getColumns(
                None, schema_name.upper(), table_name, "%"
            )

            columns = []
            while result_set.next():
                column_name = result_set.getString("COLUMN_NAME")
                data_type = result_set.getString("TYPE_NAME")
                column_size = result_set.getInt("COLUMN_SIZE")
                nullable = result_set.getInt("NULLABLE") == 1
                remarks = result_set.getString("REMARKS")
                column_type_code = result_set.getInt("DATA_TYPE")

                # These might not be available in all JDBC drivers
                precision = 0
                scale = 0
                try:
                    precision = result_set.getInt("PRECISION")
                    scale = result_set.getInt("SCALE")
                except:
                    # Ignore if not available
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
                        remarks=remarks
                    )
                )

            result_set.close()
            return columns

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, get_columns_sync)

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(f"Error getting column information: {sanitized_error}")

            raise DatabaseError(
                message=f"Failed to get column information: {sanitized_error}",
                details={"table": table_name, "schema": schema_name}
            )

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.

        Returns:
            Dictionary with connection details
        """
        info = {
            "connected": self._connected,
            "connection_id": self._config.id,
            "name": self._config.name,
            "server": self._config.server,
            "database": self._config.database,
            "username": self._config.username,
            "ssl": self._config.ssl,
            "type": "AS400",
            "read_only": self._config.read_only
        }

        if self._connection_time is not None:
            info["connection_time_ms"] = int(self._connection_time * 1000)

        if self._accessed_tables:
            info["accessed_tables"] = sorted(self._accessed_tables)

        return info

    def _build_jdbc_url(self) -> str:
        """
        Build the JDBC URL for the AS400 connection.

        Returns:
            JDBC URL string
        """
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

    def _validate_and_prepare_query(
            self,
            query: str,
            limit: Optional[int]
    ) -> Optional[str]:
        """
        Validate the query for security and prepare it for execution.

        Args:
            query: SQL query
            limit: Optional row limit

        Returns:
            Table name if detected, or None

        Raises:
            SecurityError: If the query violates security constraints
        """
        # Simple case: just a table name
        if " " not in query:
            table_name = query.strip()

            # Check if table is allowed
            if self._config.allowed_tables:
                if table_name.upper() not in self._config.allowed_tables:
                    raise SecurityError(
                        message=f"Access to table '{table_name}' is not allowed",
                        details={
                            "table": table_name,
                            "allowed_tables": self._config.allowed_tables
                        }
                    )

            # Construct a SELECT * query
            full_table_name = f"{self._config.database}.{table_name}"
            limit_clause = f" FETCH FIRST {limit} ROWS ONLY" if limit is not None else ""
            query = f"SELECT * FROM {full_table_name}{limit_clause}"

            return table_name
        else:
            # More complex query
            query_upper = query.upper()

            # Check for write operations, which are not allowed in read-only mode
            if self._config.read_only and any(
                    write_op in query_upper for write_op in [
                        "INSERT", "UPDATE", "DELETE", "CREATE", "DROP",
                        "ALTER", "TRUNCATE", "GRANT", "REVOKE", "RENAME"
                    ]
            ):
                raise SecurityError(
                    message="Write operations are not allowed on read-only connection",
                    details={"query": self._sanitize_sql_for_logging(query)}
                )

            # Add limit if specified and not already present
            if (limit is not None and "LIMIT" not in query_upper and
                    "FETCH FIRST" not in query_upper):
                if ";" in query:
                    query = query.rstrip(";")
                query = f"{query} FETCH FIRST {limit} ROWS ONLY"

            return None

    def _convert_to_prepared_statement(
            self,
            query: str,
            params: Dict[str, Any]
    ) -> Tuple[str, List[Any]]:
        """
        Convert a parameterized query to a JDBC prepared statement.

        Args:
            query: Parameterized SQL query
            params: Parameter values

        Returns:
            Tuple of (prepared query, parameter values)

        Raises:
            ValueError: If a required parameter is missing
        """
        param_names = re.findall(r":(\w+)", query)
        param_values = []

        for name in param_names:
            if name not in params:
                raise ValueError(f"Parameter '{name}' not provided in params dictionary")

            param_values.append(params[name])
            query = query.replace(f":{name}", "?", 1)

        return query, param_values

    def _set_prepared_statement_parameter(
            self,
            statement: Any,
            index: int,
            value: Any,
            java_sql_Types: Any
    ) -> None:
        """
        Set a parameter in a JDBC prepared statement.

        Args:
            statement: JDBC PreparedStatement
            index: Parameter index (1-based)
            value: Parameter value
            java_sql_Types: JDBC Types class
        """
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
        elif hasattr(value, "isoformat"):  # date/time object
            if hasattr(value, "hour"):  # datetime
                timestamp = jpype.JClass("java.sql.Timestamp")
                mills = int(value.timestamp() * 1000)
                statement.setTimestamp(index, timestamp(mills))
            else:  # date
                date = jpype.JClass("java.sql.Date")
                mills = int(value.toordinal() * 86400 * 1000)
                statement.setDate(index, date(mills))
        else:
            # Fall back to string representation
            statement.setString(index, str(value))

    def _process_result_set(
            self,
            result_set: Any,
            java_sql_Types: Any
    ) -> Tuple[List[Dict[str, Any]], List[ColumnMetadata]]:
        """
        Process a JDBC result set into Python data structures.

        Args:
            result_set: JDBC ResultSet
            java_sql_Types: JDBC Types class

        Returns:
            Tuple of (records, columns)
        """
        meta = result_set.getMetaData()
        column_count = meta.getColumnCount()

        # Extract column metadata
        columns: List[ColumnMetadata] = []
        for i in range(1, column_count + 1):
            table_name = None
            try:
                table_name = meta.getTableName(i)
            except:
                # Not all drivers support this
                pass

            columns.append(
                ColumnMetadata(
                    name=meta.getColumnName(i),
                    type_name=meta.getColumnTypeName(i),
                    type_code=meta.getColumnType(i),
                    precision=meta.getPrecision(i),
                    scale=meta.getScale(i),
                    nullable=meta.isNullable(i) != 0,
                    table_name=table_name
                )
            )

        # Extract records
        records = []
        while result_set.next():
            row = {}
            for i, col in enumerate(columns, 1):
                value = self._get_result_set_value(result_set, i, col, java_sql_Types)
                row[col.name] = value
            records.append(row)

        return records, columns

    def _get_result_set_value(
            self,
            result_set: Any,
            index: int,
            column: ColumnMetadata,
            java_sql_Types: Any
    ) -> Any:
        """
        Extract a value from a JDBC result set, converting to appropriate Python type.

        Args:
            result_set: JDBC ResultSet
            index: Column index (1-based)
            column: Column metadata
            java_sql_Types: JDBC Types class

        Returns:
            Converted value
        """
        if result_set.getObject(index) is None:
            return None

        type_code = column.type_code

        # String types
        if type_code in (java_sql_Types.CHAR, java_sql_Types.VARCHAR, java_sql_Types.LONGVARCHAR):
            return result_set.getString(index)

        # Integer types
        elif type_code in (java_sql_Types.TINYINT, java_sql_Types.SMALLINT, java_sql_Types.INTEGER):
            return result_set.getInt(index)

        # Big integer
        elif type_code in (java_sql_Types.BIGINT,):
            return result_set.getLong(index)

        # Floating point types
        elif type_code in (java_sql_Types.FLOAT, java_sql_Types.DOUBLE, java_sql_Types.REAL):
            return result_set.getDouble(index)

        # Decimal types
        elif type_code in (java_sql_Types.DECIMAL, java_sql_Types.NUMERIC):
            big_decimal = result_set.getBigDecimal(index)

            # Convert to int or float based on scale
            if column.scale == 0:
                return int(big_decimal.longValue())
            else:
                return float(big_decimal.doubleValue())

        # Date type
        elif type_code == java_sql_Types.DATE:
            date = result_set.getDate(index)
            from datetime import date as py_date
            return py_date(date.getYear() + 1900, date.getMonth() + 1, date.getDate())

        # Time type
        elif type_code == java_sql_Types.TIME:
            time = result_set.getTime(index)
            from datetime import time as py_time
            return py_time(time.getHours(), time.getMinutes(), time.getSeconds())

        # Timestamp type
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
                timestamp.getNanos() // 1000
            )

        # Boolean type
        elif type_code == java_sql_Types.BOOLEAN:
            return result_set.getBoolean(index)

        # Binary types
        elif type_code in (java_sql_Types.BINARY, java_sql_Types.VARBINARY, java_sql_Types.LONGVARBINARY):
            java_bytes = result_set.getBytes(index)
            return bytes(java_bytes)

        # Default: return as string
        else:
            return str(result_set.getObject(index))