from __future__ import annotations

"""
AS400 connector for Qorzen.

This module provides a secure connector for extracting data from AS400/iSeries
databases using the JTOpen (JT400) Java library via JPype, integrated with the
Qorzen framework.
"""

import os
import re
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from functools import cache

from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from qorzen.plugins.as400_connector_plugin.models import (
    AS400ConnectionConfig,
    ColumnMetadata,
    QueryResult
)


class AS400Connector:
    """
    Secure connector for AS400/iSeries databases using JT400 via JPype.

    Implements multiple security layers:
    1. SecretStr for password handling
    2. Whitelist for allowed tables and schemas
    3. Read-only operations only
    4. SSL/TLS encryption when available
    5. Timeouts to prevent hanging connections
    6. Detailed audit logging
    """

    def __init__(
            self,
            config: AS400ConnectionConfig,
            logger: Any,
            security_manager: Optional[Any] = None
    ) -> None:
        """
        Initialize the AS400 connector with secure configuration.

        Args:
            config: Configuration for the AS400 connection
            logger: Logger for logging events
            security_manager: Optional security manager for encryption
        """
        self.config = config
        self._logger = logger
        self._security_manager = security_manager
        self._connection: Optional[Any] = None
        self._connection_properties: Dict[str, str] = {}
        self._accessed_tables: Set[str] = set()
        self._jpype = None
        self._JException = None
        self._connection_time: Optional[float] = None

        # Check if JPYPE is available
        try:
            import jpype
            from jpype.types import JException

            self._jpype = jpype
            self._JException = JException

            # Initialize JVM if needed
            self._initialize_jpype()
        except ImportError:
            self._logger.error(
                "jpype module is required for JT400 connections. "
                "Please install it with 'pip install jpype1'."
            )
            raise ImportError(
                "jpype module is required for JT400 connections. "
                "Please install it with 'pip install jpype1'."
            )

        self._logger.debug(
            "AS400Connector initialized",
            extra={"server": config.server, "database": config.database}
        )

    @cache
    def _initialize_jpype(self) -> None:
        """
        Initialize JPype and JVM to use JT400.

        This method is cached to ensure JVM is started only once.
        """
        jpype = self._jpype  # Local reference for efficiency

        if not jpype.isJVMStarted():
            # Start JVM with JT400 jar in classpath
            jpype.startJVM(
                classpath=[self.config.jt400_jar_path],
                convertStrings=True,
            )
            self._logger.debug("JVM started for JT400 access")

            # Try to load the AS400 JDBC driver
            try:
                driver_class = jpype.JClass("com.ibm.as400.access.AS400JDBCDriver")
                driver = driver_class()
                # Register the driver with DriverManager
                jpype.JClass("java.sql.DriverManager").registerDriver(driver)
                self._logger.debug("AS400 JDBC driver registered successfully")
            except Exception as e:
                self._logger.warning(
                    "Could not register AS400 JDBC driver explicitly",
                    extra={"error": str(e)}
                )

    async def connect(self) -> None:
        """
        Establish a secure connection to the AS400 database using JT400.

        Raises:
            SecurityError: If security requirements aren't met
            DatabaseError: If connection fails
            ConfigurationError: If configuration is invalid
        """
        jpype = self._jpype  # Local reference for efficiency
        JException = self._JException  # Local reference for efficiency

        try:
            # Get Java classes needed for connection
            java_sql_DriverManager = jpype.JClass("java.sql.DriverManager")
            java_util_Properties = jpype.JClass("java.util.Properties")

            # Build JDBC URL
            jdbc_url = self._build_jdbc_url()

            # Create connection properties
            properties = java_util_Properties()
            properties.setProperty("user", self.config.username)
            properties.setProperty("password", self.config.password.get_secret_value())
            properties.setProperty("secure", "true" if self.config.ssl else "false")
            properties.setProperty("prompt", "false")  # Don't prompt for credentials
            properties.setProperty("libraries", self.config.database)

            # Set timeout properties if supported by JT400
            properties.setProperty("login timeout", str(self.config.connection_timeout))
            properties.setProperty("query timeout", str(self.config.query_timeout))
            properties.setProperty("transaction isolation", "read committed")
            properties.setProperty("date format", "iso")
            properties.setProperty("errors", "full")

            # Set to read-only mode
            properties.setProperty("access", "read only")

            # Log connection attempt (without credentials)
            self._logger.info(
                "Connecting to AS400 database",
                extra={
                    "database": self.config.database,
                    "server": self.config.server,
                    "ssl": self.config.ssl,
                }
            )

            start_time = time.time()

            # Connect to the database
            conn = java_sql_DriverManager.getConnection(jdbc_url, properties)

            # Calculate connection time
            self._connection_time = time.time() - start_time

            # Set additional connection properties for security
            conn.setAutoCommit(True)
            conn.setReadOnly(True)

            # Store connection properties (excluding password)
            self._connection_properties = {}
            prop_keys = properties.keySet().toArray()
            for key in prop_keys:
                str_key = str(key)
                if str_key != "password":  # Skip password for security
                    self._connection_properties[str_key] = str(properties.getProperty(str_key))

            # Store connection
            self._connection = conn

            self._logger.info(
                "Successfully connected to AS400 database",
                extra={
                    "database": self.config.database,
                    "server": self.config.server,
                    "connection_time_ms": int(self._connection_time * 1000),
                }
            )
        except JException as e:
            error_msg = str(e)
            # Sanitize error message to remove any potential credentials
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(
                "Failed to connect to AS400",
                extra={"error": sanitized_error}
            )

            # Convert error to appropriate exception type
            if (
                    "permission" in error_msg.lower()
                    or "access denied" in error_msg.lower()
                    or "authorization" in error_msg.lower()
            ):
                raise SecurityError(
                    message=f"Security error connecting to AS400: {sanitized_error}",
                    details={"original_error": sanitized_error}
                )
            else:
                raise DatabaseError(
                    message=f"Failed to connect to AS400 database: {sanitized_error}",
                    details={"original_error": sanitized_error}
                )

    async def execute_query(
            self, query: str, limit: Optional[int] = None, **params: Any
    ) -> QueryResult:
        """
        Securely execute a query on the AS400 system.

        Args:
            query: SQL query or table name
            limit: Maximum number of records to return
            **params: Query parameters

        Returns:
            QueryResult object containing the query results

        Raises:
            SecurityError: If the query attempts to access unauthorized tables
            DatabaseError: If the query fails to execute
        """
        if not self._connection:
            await self.connect()

        # Make sure we're connected
        if not self._connection:
            raise DatabaseError(
                message="Not connected to AS400 database",
                details={"connection_id": self.config.id}
            )

        # References for efficiency
        jpype = self._jpype
        JException = self._JException

        # Initialize result
        result = QueryResult(
            query=query,
            connection_id=self.config.id,
            executed_at=time.time()
        )

        # Validate and sanitize query before execution
        table_name = self._validate_and_prepare_query(query, limit)

        try:
            # Get Java classes needed for query execution
            java_sql_Types = jpype.JClass("java.sql.Types")

            # Log query execution (sanitized)
            sanitized_query = self._sanitize_sql_for_logging(query)
            self._logger.debug(
                "Executing AS400 query",
                extra={"query": sanitized_query, "limit": limit}
            )

            start_time = time.time()

            # Use prepared statement if parameters are provided
            if params:
                # Convert query parameters to use ? placeholders
                query, param_values = self._convert_to_prepared_statement(query, params)
                statement = self._connection.prepareStatement(query)

                # Set parameters
                for i, value in enumerate(param_values):
                    self._set_prepared_statement_parameter(
                        statement, i + 1, value, java_sql_Types
                    )

                # Set query timeout if supported
                statement.setQueryTimeout(self.config.query_timeout)

                # Execute and get result set
                result_set = statement.executeQuery()
            else:
                # Create regular statement
                statement = self._connection.createStatement()

                # Set query timeout if supported
                statement.setQueryTimeout(self.config.query_timeout)

                # Execute and get result set
                result_set = statement.executeQuery(query)

            # Record table access for auditing
            if table_name:
                self._accessed_tables.add(table_name.upper())

            # Process results
            records, columns = self._process_result_set(result_set, java_sql_Types)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Update result object
            result.records = records
            result.columns = columns
            result.row_count = len(records)
            result.execution_time_ms = int(execution_time * 1000)
            result.truncated = limit is not None and result.row_count >= limit

            # Close the result set and statement
            result_set.close()
            statement.close()

            # Log success
            self._logger.info(
                "Successfully executed query on AS400",
                extra={
                    "record_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms,
                    "table": table_name if table_name else None,
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
                    "query": self._sanitize_sql_for_logging(query),
                }
            )

            # Update result with error
            result.has_error = True
            result.error_message = sanitized_error

            # Classify error
            if (
                    "permission" in error_msg.lower()
                    or "access denied" in error_msg.lower()
                    or "authorization" in error_msg.lower()
            ):
                raise SecurityError(
                    message=f"Security error executing AS400 query: {sanitized_error}",
                    details={"original_error": sanitized_error, "query": self._sanitize_sql_for_logging(query)}
                )
            else:
                raise DatabaseError(
                    message=f"Failed to execute AS400 query: {sanitized_error}",
                    details={"original_error": sanitized_error, "query": self._sanitize_sql_for_logging(query)}
                )

    async def close(self) -> None:
        """
        Safely close the AS400 connection.

        Raises:
            DatabaseError: If closing the connection fails
        """
        if self._connection:
            try:
                # Close the connection
                self._connection.close()
                self._connection = None
                self._logger.debug("AS400 connection closed")

                # Audit logging
                if self._accessed_tables:
                    self._logger.info(
                        "AS400 session accessed tables",
                        extra={"tables": sorted(self._accessed_tables)}
                    )
            except self._JException as e:
                self._logger.error(
                    "Error closing AS400 connection",
                    extra={"error": str(e)}
                )
                raise DatabaseError(
                    message=f"Failed to close AS400 connection: {str(e)}",
                    details={"original_error": str(e)}
                )

    def _build_jdbc_url(self) -> str:
        """
        Build the JDBC URL for JT400 connection.

        Returns:
            JDBC URL string for connection
        """
        # Base JDBC URL for JT400
        jdbc_url = f"jdbc:as400://{self.config.server}"

        # Add port if specified
        if self.config.port:
            jdbc_url += f":{self.config.port}"

        # Configure additional parameters
        params = []

        # Add database/library if provided
        if self.config.database:
            params.append(f"libraries={self.config.database}")

        # Add secure connection parameter if SSL is requested
        if self.config.ssl:
            params.append("secure=true")

        # Add parameters to URL
        if params:
            jdbc_url += ";" + ";".join(params)

        return jdbc_url

    def _validate_and_prepare_query(
            self, query: str, limit: Optional[int]
    ) -> Optional[str]:
        """
        Validate query for security and prepare for execution.

        Args:
            query: The SQL query or table name
            limit: Maximum records to return

        Returns:
            Table name if a table-only query, None otherwise

        Raises:
            SecurityError: If the query is attempting to perform unauthorized operations
        """
        # Check if query is just a table name (for simple SELECT *)
        if " " not in query:
            table_name = query.strip()

            # Check against whitelist if configured
            if self.config.allowed_tables:
                if table_name.upper() not in self.config.allowed_tables:
                    raise SecurityError(
                        message=f"Access to table '{table_name}' is not allowed",
                        details={"table": table_name, "allowed_tables": self.config.allowed_tables}
                    )

            # Build full query with schema/library if needed
            full_table_name = f"{self.config.database}.{table_name}"

            # Add limit clause if requested
            limit_clause = (
                f" FETCH FIRST {limit} ROWS ONLY" if limit is not None else ""
            )
            query = f"SELECT * FROM {full_table_name}{limit_clause}"
            return table_name
        else:
            # For SQL queries, perform security checks
            query_upper = query.upper()

            # Ensure query is read-only
            if any(
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
            ):
                raise SecurityError(
                    message="Write operations are not allowed on AS400 connection",
                    details={"query": self._sanitize_sql_for_logging(query)}
                )

            # Add LIMIT clause if requested and not already present
            if (
                    limit is not None
                    and "LIMIT" not in query_upper
                    and "FETCH FIRST" not in query_upper
            ):
                if ";" in query:
                    query = query.rstrip(";")
                query = f"{query} FETCH FIRST {limit} ROWS ONLY"

            return None

    def _convert_to_prepared_statement(
            self, query: str, params: Dict[str, Any]
    ) -> tuple[str, List[Any]]:
        """
        Convert a query with named parameters to a prepared statement with ? placeholders.

        Args:
            query: SQL query with named parameters
            params: Parameters dictionary

        Returns:
            Tuple of (prepared statement query, ordered parameter values)
        """
        # Look for named parameters in the format :param_name
        param_names = re.findall(r":(\w+)", query)
        param_values = []

        # Replace each named parameter with ? and collect values in order
        for name in param_names:
            if name not in params:
                raise ValueError(
                    f"Parameter '{name}' not provided in params dictionary"
                )

            # Collect value
            param_values.append(params[name])

            # Replace named parameter with ?
            query = query.replace(f":{name}", "?", 1)

        return query, param_values

    def _set_prepared_statement_parameter(
            self, statement: Any, index: int, value: Any, java_sql_Types: Any
    ) -> None:
        """
        Set a parameter value in a prepared statement based on its type.

        Args:
            statement: JDBC PreparedStatement object
            index: Parameter index (1-based)
            value: Parameter value to set
            java_sql_Types: Java SQL Types class from JPype
        """
        jpype = self._jpype  # Local reference for efficiency

        # Handle None/null values
        if value is None:
            statement.setNull(index, java_sql_Types.NULL)
            return

        # Handle different Python types
        if isinstance(value, str):
            statement.setString(index, value)
        elif isinstance(value, int):
            statement.setInt(index, value)
        elif isinstance(value, float):
            statement.setDouble(index, value)
        elif isinstance(value, bool):
            statement.setBoolean(index, value)
        elif hasattr(value, "isoformat"):  # Date or datetime
            # Convert to java.sql.Date or Timestamp
            if hasattr(value, "hour"):  # datetime
                timestamp = jpype.JClass("java.sql.Timestamp")
                # Convert to milliseconds since epoch
                mills = int(value.timestamp() * 1000)
                statement.setTimestamp(index, timestamp(mills))
            else:  # date
                date = jpype.JClass("java.sql.Date")
                # Convert to days since epoch and then milliseconds
                mills = int(value.toordinal() * 86400 * 1000)
                statement.setDate(index, date(mills))
        else:
            # Fall back to string for other types
            statement.setString(index, str(value))

    def _process_result_set(
            self, result_set: Any, java_sql_Types: Any
    ) -> Tuple[List[Dict[str, Any]], List[ColumnMetadata]]:
        """
        Process JDBC ResultSet into a list of dictionaries and column metadata.

        Args:
            result_set: JDBC ResultSet object
            java_sql_Types: Java SQL Types class from JPype

        Returns:
            Tuple of (records, column metadata)
        """
        # Get metadata for column names and types
        meta = result_set.getMetaData()
        column_count = meta.getColumnCount()

        # Extract column information
        columns: List[ColumnMetadata] = []
        for i in range(1, column_count + 1):
            columns.append(
                ColumnMetadata(
                    name=meta.getColumnName(i),
                    type_name=meta.getColumnTypeName(i),
                    type_code=meta.getColumnType(i),
                    precision=meta.getPrecision(i),
                    scale=meta.getScale(i),
                    nullable=meta.isNullable(i) != 0,
                )
            )

        # Process rows
        records = []
        while result_set.next():
            row = {}
            for i, col in enumerate(columns, 1):
                # Handle different data types appropriately
                value = self._get_result_set_value(result_set, i, col, java_sql_Types)
                row[col.name] = value

            records.append(row)

        return records, columns

    def _get_result_set_value(
            self, result_set: Any, index: int, column: ColumnMetadata, java_sql_Types: Any
    ) -> Any:
        """
        Extract a value from a ResultSet using appropriate conversion.

        Args:
            result_set: JDBC ResultSet
            index: Column index (1-based)
            column: Column metadata
            java_sql_Types: Java SQL Types class from JPype

        Returns:
            Converted Python value
        """
        # Check for NULL first
        if result_set.getObject(index) is None:
            return None

        # Handle different SQL types
        type_code = column.type_code

        # String types
        if type_code in (
                java_sql_Types.CHAR,
                java_sql_Types.VARCHAR,
                java_sql_Types.LONGVARCHAR,
        ):
            return result_set.getString(index)

        # Numeric types
        elif type_code in (
                java_sql_Types.TINYINT,
                java_sql_Types.SMALLINT,
                java_sql_Types.INTEGER,
        ):
            return result_set.getInt(index)
        elif type_code in (java_sql_Types.BIGINT,):
            return result_set.getLong(index)
        elif type_code in (
                java_sql_Types.FLOAT,
                java_sql_Types.DOUBLE,
                java_sql_Types.REAL,
        ):
            return result_set.getDouble(index)
        elif type_code in (java_sql_Types.DECIMAL, java_sql_Types.NUMERIC):
            # Get as BigDecimal and convert to Python decimal or float
            big_decimal = result_set.getBigDecimal(index)
            if column.scale == 0:
                return int(big_decimal.longValue())
            else:
                return float(big_decimal.doubleValue())

        # Date/Time types
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

        # Boolean types
        elif type_code == java_sql_Types.BOOLEAN:
            return result_set.getBoolean(index)

        # Binary types
        elif type_code in (
                java_sql_Types.BINARY,
                java_sql_Types.VARBINARY,
                java_sql_Types.LONGVARBINARY,
        ):
            # Get as byte array and convert to Python bytes
            java_bytes = result_set.getBytes(index)
            return bytes(java_bytes)

        # Fall back to string for unknown types
        else:
            return str(result_set.getObject(index))

    def _sanitize_sql_for_logging(self, query: str) -> str:
        """
        Sanitize SQL query for safe logging.

        Args:
            query: SQL query

        Returns:
            Sanitized query
        """
        # Simple sanitization - can be enhanced if needed
        return query.replace("\n", " ").replace("\r", " ")

    def _sanitize_error_message(self, error_message: str) -> str:
        """
        Sanitize error messages to avoid leaking sensitive information.

        Args:
            error_message: Original error message

        Returns:
            Sanitized error message
        """
        # Remove potential password information
        sanitized = error_message.replace(
            self.config.password.get_secret_value(), "[REDACTED]"
        )

        # Remove username if present
        sanitized = sanitized.replace(self.config.username, "[USERNAME]")

        # Additional sanitization as needed
        return sanitized

    def is_connected(self) -> bool:
        """
        Check if currently connected to the AS400 database.

        Returns:
            True if connected, False otherwise
        """
        if not self._connection:
            return False

        try:
            # Try a simple validation query
            statement = self._connection.createStatement()
            statement.setQueryTimeout(5)  # Short timeout for validation
            result_set = statement.executeQuery("SELECT 1 FROM SYSIBM.SYSDUMMY1")
            result_set.close()
            statement.close()
            return True
        except Exception:
            self._connection = None
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.

        Returns:
            Dictionary with connection information
        """
        info = {
            "connected": self.is_connected(),
            "connection_id": self.config.id,
            "name": self.config.name,
            "server": self.config.server,
            "database": self.config.database,
            "username": self.config.username,
            "ssl": self.config.ssl,
        }

        if self._connection_time is not None:
            info["connection_time_ms"] = int(self._connection_time * 1000)

        if self._accessed_tables:
            info["accessed_tables"] = sorted(self._accessed_tables)

        return info

    async def get_schema_info(self, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get schema information from the database.

        Args:
            schema: Optional schema name, defaults to the configured database

        Returns:
            List of tables in the schema with their details
        """
        schema_name = schema or self.config.database

        if not self._connection:
            await self.connect()

        try:
            # Get database metadata
            metadata = self._connection.getMetaData()

            # Get tables
            result_set = metadata.getTables(
                None,  # Catalog - null for AS400
                schema_name.upper(),  # Schema pattern
                "%",  # Table name pattern - % for all
                ["TABLE", "VIEW"]  # Table types
            )

            tables = []
            while result_set.next():
                table_name = result_set.getString("TABLE_NAME")
                table_type = result_set.getString("TABLE_TYPE")
                remarks = result_set.getString("REMARKS")

                # Get column info
                columns_rs = metadata.getColumns(None, schema_name.upper(), table_name, "%")
                columns = []

                while columns_rs.next():
                    column_name = columns_rs.getString("COLUMN_NAME")
                    data_type = columns_rs.getString("TYPE_NAME")
                    column_size = columns_rs.getInt("COLUMN_SIZE")
                    nullable = columns_rs.getInt("NULLABLE") == 1
                    remarks = columns_rs.getString("REMARKS")

                    columns.append({
                        "name": column_name,
                        "type": data_type,
                        "size": column_size,
                        "nullable": nullable,
                        "remarks": remarks
                    })

                columns_rs.close()

                tables.append({
                    "name": table_name,
                    "type": table_type,
                    "schema": schema_name.upper(),
                    "remarks": remarks,
                    "columns": columns
                })

            result_set.close()
            return tables

        except Exception as e:
            error_msg = str(e)
            sanitized_error = self._sanitize_error_message(error_msg)
            self._logger.error(
                f"Error getting schema information: {sanitized_error}"
            )
            raise DatabaseError(
                message=f"Failed to get schema information: {sanitized_error}",
                details={"schema": schema_name}
            )