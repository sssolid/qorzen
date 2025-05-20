#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Data models for the Database Connector Plugin.

This module provides Pydantic models for database connection configuration,
field mappings, saved queries, validation rules, and other data structures
used by the plugin.
"""

import datetime
import enum
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union, cast, Literal

from pydantic import BaseModel, Field, SecretStr, validator, model_validator, field_validator


class ConnectionType(str, enum.Enum):
    """Supported database connection types."""
    AS400 = "as400"
    ODBC = "odbc"
    MYSQL = "mysql"
    POSTGRES = "postgres"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    MSSQL = "mssql"


class BaseConnectionConfig(BaseModel):
    """Base configuration for all database connections."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this connection")
    name: str = Field(..., description="User-friendly name for this connection")
    connection_type: ConnectionType = Field(..., description="Type of database connection")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username (read-only account recommended)")
    password: SecretStr = Field(..., description="Database password")
    connection_timeout: int = Field(30, description="Connection timeout in seconds")
    query_timeout: int = Field(60, description="Query timeout in seconds")
    encrypt_connection: bool = Field(True, description="Encrypt connection parameters")
    allowed_tables: Optional[List[str]] = Field(None, description="Whitelist of allowed tables")
    read_only: bool = Field(True, description="Whether this connection is read-only")

    class Config:
        validate_assignment = True
        extra = "forbid"


class ParameterDescription(BaseModel):
    """Model for a query parameter with optional description."""

    name: str = Field(..., description='Parameter name')
    description: str = Field("", description='Parameter description/help text')


class SQLiteConnectionConfig(BaseConnectionConfig):
    """Configuration model for SQLite database connections."""

    connection_type: Literal[ConnectionType.SQLITE] = Field(
        ConnectionType.SQLITE,
        description='Connection type'
    )
    database: str = Field(
        ...,
        description='SQLite database file path (or :memory: for in-memory database)'
    )
    username: str = Field(
        "sqlite",
        description='Username (not used for SQLite but required by base model)'
    )
    password: SecretStr = Field(
        SecretStr(""),
        description='Password (not used for SQLite but required by base model)'
    )

    @field_validator('database')
    def validate_database(cls, v: str) -> str:
        """Validate the database path.

        Args:
            v: The database path

        Returns:
            The validated database path

        Raises:
            ValueError: If the database path is invalid
        """
        import os
        # Allow :memory: database
        if v == ':memory:':
            return v

        # Check if path exists or parent directory exists
        db_path = os.path.abspath(os.path.expanduser(v))
        if os.path.exists(db_path):
            return db_path

        parent_dir = os.path.dirname(db_path)
        if not os.path.exists(parent_dir):
            raise ValueError(f"Database directory does not exist: {parent_dir}")

        # Path is valid but file doesn't exist yet - will be created
        return db_path


class AS400ConnectionConfig(BaseConnectionConfig):
    """AS400-specific connection configuration."""
    connection_type: Literal[ConnectionType.AS400] = Field(ConnectionType.AS400, description="Connection type")
    jt400_jar_path: str = Field(..., description="Path to the jt400.jar file for Java connection")
    server: str = Field(..., description="AS400 server address")
    port: Optional[int] = Field(446, description="AS400 server port (default: 446)")
    ssl: bool = Field(True, description="Use SSL for connection")
    allowed_libraries: Optional[List[str]] = Field(None, description="Whitelist of allowed libraries/schemas")

    @field_validator("port")
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("allowed_tables", "allowed_libraries")
    def validate_allowed_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            return [item.upper() for item in v]
        return v


class ODBCConnectionConfig(BaseConnectionConfig):
    """ODBC-specific connection configuration."""
    connection_type: Literal[ConnectionType.ODBC] = Field(ConnectionType.ODBC, description="Connection type")
    dsn: str = Field(..., description="ODBC Data Source Name")
    server: Optional[str] = Field(None, description="Server address (if not in DSN)")
    port: Optional[int] = Field(None, description="Server port (if not in DSN)")
    connection_string: Optional[str] = Field(None, description="Full ODBC connection string (alternative to DSN)")

    @field_validator("port")
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

    @model_validator(mode="before")
    def validate_connection_info(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        dsn = values.get("dsn")
        conn_string = values.get("connection_string")
        if not dsn and not conn_string:
            raise ValueError("Either DSN or connection_string must be provided")
        return values


class SQLConnectionConfig(BaseConnectionConfig):
    """Configuration for SQL-based databases (MySQL, PostgreSQL, etc.)."""
    server: str = Field(..., description="Database server address")
    port: Optional[int] = Field(None, description="Database server port")

    @field_validator("port")
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class FieldMapping(BaseModel):
    """Mapping of database fields to standardized names."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this mapping")
    connection_id: str = Field(..., description="ID of the connection this mapping is for")
    table_name: str = Field(..., description="Database table name")
    description: Optional[str] = Field(None, description="Optional description of the mapping")
    mappings: Dict[str, str] = Field(..., description="Map of original field names to mapped names")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this mapping was created")
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this mapping was last updated")

    class Config:
        validate_assignment = True


class SavedQuery(BaseModel):
    """Saved query configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this query")
    name: str = Field(..., description="User-friendly name for this query")
    description: Optional[str] = Field(None, description="Optional description of the query's purpose")
    query_text: str = Field(..., description="The SQL query text")
    connection_id: str = Field(..., description="ID of the connection this query is associated with")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this query was created")
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this query was last updated")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters if any")
    parameter_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description='Descriptions for parameters'
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing queries")
    is_favorite: bool = Field(False, description="Whether this query is marked as a favorite")
    field_mapping_id: Optional[str] = Field(None, description="ID of field mapping to apply to results")

    class Config:
        validate_assignment = True


class QueryHistoryEntry(BaseModel):
    """Record of a previously executed query."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this history entry")
    query_id: Optional[str] = Field(None, description="ID of the saved query if applicable")
    query_text: str = Field(..., description="The executed SQL query text")
    connection_id: str = Field(..., description="ID of the connection used")
    executed_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                           description="When this query was executed")
    execution_time_ms: Optional[int] = Field(None, description="Query execution time in milliseconds")
    row_count: Optional[int] = Field(None, description="Number of rows returned")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters used in the query")
    status: str = Field("success", description="Execution status (success, error)")
    error_message: Optional[str] = Field(None, description="Error message if query failed")

    class Config:
        validate_assignment = True


class ValidationRuleType(str, enum.Enum):
    """Types of validation rules that can be applied to data."""
    RANGE = "range"  # Value must be within a specified range
    PATTERN = "pattern"  # Value must match a specified regex pattern
    NOT_NULL = "not_null"  # Value must not be null
    UNIQUE = "unique"  # Value must be unique
    LENGTH = "length"  # Value must have a specific length
    REFERENCE = "reference"  # Value must reference another field/table
    ENUMERATION = "enumeration"  # Value must be one of a list of options
    CUSTOM = "custom"  # Custom validation with supplied expression


class ValidationRule(BaseModel):
    """Rule for validating field data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this rule")
    name: str = Field(..., description="User-friendly name for this validation rule")
    description: Optional[str] = Field(None, description="Description of what this rule validates")
    connection_id: str = Field(..., description="ID of the connection this rule is for")
    table_name: str = Field(..., description="Database table name")
    field_name: str = Field(..., description="Field to validate")
    rule_type: ValidationRuleType = Field(..., description="Type of validation rule")
    parameters: Dict[str, Any] = Field(..., description="Parameters for the validation rule")
    error_message: str = Field(..., description="Message to show when validation fails")
    active: bool = Field(True, description="Whether this rule is active")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this rule was created")
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this rule was last updated")

    class Config:
        validate_assignment = True


class ValidationResult(BaseModel):
    """Result of a validation run."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                    description="Unique identifier for this validation result")
    rule_id: str = Field(..., description="ID of the validation rule")
    table_name: str = Field(..., description="Database table name")
    field_name: str = Field(..., description="Field that was validated")
    validated_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                            description="When validation was performed")
    success: bool = Field(..., description="Whether validation passed")
    failures: List[Dict[str, Any]] = Field(default_factory=list, description="List of validation failures")
    total_records: int = Field(..., description="Total number of records validated")
    failed_records: int = Field(..., description="Number of records that failed validation")

    class Config:
        validate_assignment = True


class HistorySchedule(BaseModel):
    """Schedule for automatically collecting historical data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this schedule")
    connection_id: str = Field(..., description="Connection ID for the source data")
    name: str = Field(..., description="User-friendly name for this schedule")
    description: Optional[str] = Field(None, description="Purpose of this historical data collection")
    query_id: str = Field(..., description="ID of the saved query to execute")
    frequency: str = Field(..., description="Cron-style schedule frequency")
    retention_days: int = Field(365, description="Number of days to retain historical data")
    active: bool = Field(True, description="Whether this schedule is active")
    last_run: Optional[datetime.datetime] = Field(None, description="When this schedule was last executed")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this schedule was created")
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this schedule was last updated")

    class Config:
        validate_assignment = True


class HistoryEntry(BaseModel):
    """Historical data point."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this history entry")
    schedule_id: str = Field(..., description="ID of the history schedule that created this entry")
    connection_id: str = Field(..., description="ID of the connection used")
    query_id: str = Field(..., description="ID of the query used")
    table_name: str = Field(..., description="Source table name")
    collected_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                            description="When data was collected")
    snapshot_id: str = Field(..., description="Unique identifier for this snapshot of data")
    record_count: int = Field(..., description="Number of records in this snapshot")
    status: str = Field("success", description="Status of data collection")
    error_message: Optional[str] = Field(None, description="Error message if collection failed")

    class Config:
        validate_assignment = True


class PluginSettings(BaseModel):
    """Plugin settings and configuration."""
    recent_connections: List[str] = Field(default_factory=list, description="Recently used connection IDs")
    default_connection_id: Optional[str] = Field(None, description="Default connection ID")
    max_result_rows: int = Field(10000, description="Maximum number of rows to display/fetch")
    query_history_limit: int = Field(100, description="Maximum number of entries in query history")
    auto_save_queries: bool = Field(True, description="Automatically save executed queries")
    syntax_highlighting: bool = Field(True, description="Enable SQL syntax highlighting")
    history_database_connection_id: Optional[str] = Field(None, description="Connection ID for history storage")

    class Config:
        validate_assignment = True


@dataclass
class ColumnMetadata:
    """Metadata about a database column."""
    name: str
    type_name: str
    type_code: int
    precision: int
    scale: int
    nullable: bool
    table_name: Optional[str] = None
    remarks: Optional[str] = None


@dataclass
class TableMetadata:
    """Metadata about a database table."""
    name: str
    schema: Optional[str] = None
    type: Optional[str] = None
    remarks: Optional[str] = None
    columns: List[ColumnMetadata] = field(default_factory=list)


@dataclass
class QueryResult:
    """Results of a database query."""
    records: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[ColumnMetadata] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0
    query: str = ""
    connection_id: str = ""
    executed_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    truncated: bool = False
    has_error: bool = False
    error_message: Optional[str] = None
    mapped_records: Optional[List[Dict[str, Any]]] = field(default=None)