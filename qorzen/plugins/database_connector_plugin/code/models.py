from __future__ import annotations

"""
Data models for the Database Connector Plugin.

This module provides Pydantic models for database connection configuration,
field mappings, saved queries, validation rules, and other data structures
used by the plugin.
"""
import datetime
import enum
import os
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, cast, Literal, ClassVar

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    validator,
    model_validator,
    field_validator,
    field_serializer
)


class ConnectionType(str, enum.Enum):
    """Enumeration of supported database connection types."""

    AS400 = 'as400'
    ODBC = 'odbc'
    MYSQL = 'mysql'
    POSTGRES = 'postgres'
    SQLITE = 'sqlite'
    ORACLE = 'oracle'
    MSSQL = 'mssql'


class BaseConnectionConfig(BaseModel):
    """Base model for database connection configuration."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description='Unique identifier for this connection'
    )
    name: str = Field(
        ...,
        description='User-friendly name for this connection'
    )
    connection_type: ConnectionType = Field(
        ...,
        description='Type of database connection'
    )
    database: str = Field(
        ...,
        description='Database name'
    )
    username: str = Field(
        ...,
        description='Database username (read-only account recommended)'
    )
    password: SecretStr = Field(
        ...,
        description='Database password'
    )
    connection_timeout: int = Field(
        30,
        description='Connection timeout in seconds',
        ge=1,
        le=300
    )
    query_timeout: int = Field(
        60,
        description='Query timeout in seconds',
        ge=1,
        le=3600
    )
    encrypt_connection: bool = Field(
        True,
        description='Encrypt connection parameters'
    )
    allowed_tables: Optional[List[str]] = Field(
        None,
        description='Whitelist of allowed tables'
    )
    read_only: bool = Field(
        True,
        description='Whether this connection is read-only'
    )

    class Config:
        validate_assignment = True
        extra = 'forbid'


class ParameterDescription(BaseModel):
    """Model for SQL query parameter descriptions."""

    name: str = Field(
        ...,
        description='Parameter name'
    )
    description: str = Field(
        '',
        description='Parameter description/help text'
    )


class SQLiteConnectionConfig(BaseConnectionConfig):
    """Configuration for SQLite database connections."""

    connection_type: Literal[ConnectionType.SQLITE] = Field(
        ConnectionType.SQLITE,
        description='Connection type'
    )
    database: str = Field(
        ...,
        description='SQLite database file path (or :memory: for in-memory database)'
    )
    username: str = Field(
        'sqlite',
        description='Username (not used for SQLite but required by base model)'
    )
    password: SecretStr = Field(
        SecretStr(''),
        description='Password (not used for SQLite but required by base model)'
    )

    @field_validator('database')
    def validate_database(cls, v: str) -> str:
        """Validate SQLite database path.

        Args:
            v: Database path

        Returns:
            Valid database path

        Raises:
            ValueError: If database path is invalid
        """
        if v == ':memory:':
            return v

        db_path = os.path.abspath(os.path.expanduser(v))

        if os.path.exists(db_path):
            return db_path

        parent_dir = os.path.dirname(db_path)
        if not os.path.exists(parent_dir):
            raise ValueError(f'Database directory does not exist: {parent_dir}')

        return db_path


class AS400ConnectionConfig(BaseConnectionConfig):
    """Configuration for AS400/iSeries database connections."""

    connection_type: Literal[ConnectionType.AS400] = Field(
        ConnectionType.AS400,
        description='Connection type'
    )
    jt400_jar_path: str = Field(
        ...,
        description='Path to the jt400.jar file for Java connection'
    )
    server: str = Field(
        ...,
        description='AS400 server address'
    )
    port: Optional[int] = Field(
        446,
        description='AS400 server port (default: 446)'
    )
    ssl: bool = Field(
        True,
        description='Use SSL for connection'
    )
    allowed_libraries: Optional[List[str]] = Field(
        None,
        description='Whitelist of allowed libraries/schemas'
    )

    @field_validator('port')
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate port number.

        Args:
            v: Port number

        Returns:
            Valid port number

        Raises:
            ValueError: If port number is invalid
        """
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v

    @field_validator('allowed_tables', 'allowed_libraries')
    def validate_allowed_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Standardize list items to uppercase.

        Args:
            v: List of table/library names

        Returns:
            Uppercase list of names
        """
        if v is not None:
            return [item.upper() for item in v]
        return v

    @field_validator('jt400_jar_path')
    def validate_jar_path(cls, v: str) -> str:
        """Validate JT400 JAR file path.

        Args:
            v: JAR file path

        Returns:
            Valid JAR file path

        Raises:
            ValueError: If JAR file does not exist
        """
        path = os.path.abspath(os.path.expanduser(v))
        if not os.path.isfile(path):
            raise ValueError(f'JT400 JAR file not found: {path}')
        return path


class ODBCConnectionConfig(BaseConnectionConfig):
    """Configuration for ODBC database connections."""

    connection_type: Literal[ConnectionType.ODBC] = Field(
        ConnectionType.ODBC,
        description='Connection type'
    )
    dsn: str = Field(
        ...,
        description='ODBC Data Source Name'
    )
    server: Optional[str] = Field(
        None,
        description='Server address (if not in DSN)'
    )
    port: Optional[int] = Field(
        None,
        description='Server port (if not in DSN)'
    )
    connection_string: Optional[str] = Field(
        None,
        description='Full ODBC connection string (alternative to DSN)'
    )

    @field_validator('port')
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate port number.

        Args:
            v: Port number

        Returns:
            Valid port number

        Raises:
            ValueError: If port number is invalid
        """
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v

    @model_validator(mode='before')
    def validate_connection_info(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that either DSN or connection_string is provided.

        Args:
            values: Connection configuration values

        Returns:
            Validated values

        Raises:
            ValueError: If neither DSN nor connection_string is provided
        """
        dsn = values.get('dsn')
        conn_string = values.get('connection_string')

        if not dsn and not conn_string:
            raise ValueError('Either DSN or connection_string must be provided')

        return values


class SQLConnectionConfig(BaseConnectionConfig):
    """Base configuration for SQL-based database connections."""

    server: str = Field(
        ...,
        description='Database server address'
    )
    port: Optional[int] = Field(
        None,
        description='Database server port'
    )

    @field_validator('port')
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate port number.

        Args:
            v: Port number

        Returns:
            Valid port number

        Raises:
            ValueError: If port number is invalid
        """
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v


class FieldMapping(BaseModel):
    """Model for field name mappings between database and application."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description='Unique identifier for this mapping'
    )
    connection_id: str = Field(
        ...,
        description='ID of the connection this mapping is for'
    )
    table_name: str = Field(
        ...,
        description='Database table name'
    )
    description: Optional[str] = Field(
        None,
        description='Optional description of the mapping'
    )
    mappings: Dict[str, str] = Field(
        ...,
        description='Map of original field names to mapped names'
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this mapping was created'
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this mapping was last updated'
    )

    class Config:
        validate_assignment = True

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime.datetime, _info):
        """Serialize datetime fields for JSON serialization.

        Args:
            dt: Datetime to serialize

        Returns:
            ISO-formatted datetime string
        """
        return dt.isoformat()


class SavedQuery(BaseModel):
    """Model for saved database queries."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description='Unique identifier for this query'
    )
    name: str = Field(
        ...,
        description='User-friendly name for this query'
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the query's purpose"
    )
    query_text: str = Field(
        ...,
        description='The SQL query text'
    )
    connection_id: str = Field(
        ...,
        description='ID of the connection this query is associated with'
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this query was created'
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this query was last updated'
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description='Query parameters if any'
    )
    parameter_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description='Descriptions for parameters'
    )
    tags: List[str] = Field(
        default_factory=list,
        description='Tags for categorizing queries'
    )
    is_favorite: bool = Field(
        False,
        description='Whether this query is marked as a favorite'
    )
    field_mapping_id: Optional[str] = Field(
        None,
        description='ID of field mapping to apply to results'
    )

    class Config:
        validate_assignment = True

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime.datetime, _info):
        """Serialize datetime fields for JSON serialization.

        Args:
            dt: Datetime to serialize

        Returns:
            ISO-formatted datetime string
        """
        return dt.isoformat()

    @field_validator('query_text')
    def validate_query_text(cls, v: str) -> str:
        """Validate query text is not empty.

        Args:
            v: Query text

        Returns:
            Valid query text

        Raises:
            ValueError: If query text is empty
        """
        if not v.strip():
            raise ValueError('Query text cannot be empty')
        return v


class QueryHistoryEntry(BaseModel):
    """Model for recording query execution history."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description='Unique identifier for this history entry'
    )
    query_id: Optional[str] = Field(
        None,
        description='ID of the saved query if applicable'
    )
    query_text: str = Field(
        ...,
        description='The executed SQL query text'
    )
    connection_id: str = Field(
        ...,
        description='ID of the connection used'
    )
    executed_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this query was executed'
    )
    execution_time_ms: Optional[int] = Field(
        None,
        description='Query execution time in milliseconds'
    )
    row_count: Optional[int] = Field(
        None,
        description='Number of rows returned'
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description='Parameters used in the query'
    )
    status: str = Field(
        'success',
        description='Execution status (success, error)'
    )
    error_message: Optional[str] = Field(
        None,
        description='Error message if query failed'
    )

    class Config:
        validate_assignment = True

    @field_serializer('executed_at')
    def serialize_datetime(self, dt: datetime.datetime, _info):
        """Serialize datetime fields for JSON serialization.

        Args:
            dt: Datetime to serialize

        Returns:
            ISO-formatted datetime string
        """
        return dt.isoformat()


class ValidationRuleType(str, enum.Enum):
    """Enumeration of supported validation rule types."""

    RANGE = 'range'
    PATTERN = 'pattern'
    NOT_NULL = 'not_null'
    UNIQUE = 'unique'
    LENGTH = 'length'
    REFERENCE = 'reference'
    ENUMERATION = 'enumeration'
    CUSTOM = 'custom'


class ValidationRule(BaseModel):
    """Model for data validation rules."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description='Unique identifier for this rule'
    )
    name: str = Field(
        ...,
        description='User-friendly name for this validation rule'
    )
    description: Optional[str] = Field(
        None,
        description='Description of what this rule validates'
    )
    connection_id: str = Field(
        ...,
        description='ID of the connection this rule is for'
    )
    table_name: str = Field(
        ...,
        description='Database table name'
    )
    field_name: str = Field(
        ...,
        description='Field to validate'
    )
    rule_type: ValidationRuleType = Field(
        ...,
        description='Type of validation rule'
    )
    parameters: Dict[str, Any] = Field(
        ...,
        description='Parameters for the validation rule'
    )
    error_message: str = Field(
        ...,
        description='Message to show when validation fails'
    )
    active: bool = Field(
        True,
        description='Whether this rule is active'
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this rule was created'
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this rule was last updated'
    )

    class Config:
        validate_assignment = True

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime.datetime, _info):
        """Serialize datetime fields for JSON serialization.

        Args:
            dt: Datetime to serialize

        Returns:
            ISO-formatted datetime string
        """
        return dt.isoformat()

    @model_validator(mode='after')
    def validate_rule_parameters(self) -> 'ValidationRule':
        """Validate that the parameters match the rule type.

        Returns:
            Validated rule

        Raises:
            ValueError: If parameters don't match rule type
        """
        rule_type = self.rule_type
        params = self.parameters

        if rule_type == ValidationRuleType.RANGE:
            has_min = 'min' in params
            has_max = 'max' in params
            if not has_min and not has_max:
                raise ValueError('Range rule must have min or max parameter')

        elif rule_type == ValidationRuleType.PATTERN:
            if 'pattern' not in params or not params['pattern']:
                raise ValueError('Pattern rule must have pattern parameter')

            # Test pattern validity
            try:
                re.compile(params['pattern'])
            except re.error as e:
                raise ValueError(f'Invalid regular expression: {str(e)}')

        elif rule_type == ValidationRuleType.LENGTH:
            has_min = 'min_length' in params
            has_max = 'max_length' in params
            if not has_min and not has_max:
                raise ValueError('Length rule must have min_length or max_length parameter')

        elif rule_type == ValidationRuleType.ENUMERATION:
            if 'allowed_values' not in params or not params['allowed_values']:
                raise ValueError('Enumeration rule must have allowed_values parameter')

        elif rule_type == ValidationRuleType.REFERENCE:
            if 'reference_values' not in params or not params['reference_values']:
                raise ValueError('Reference rule must have reference_values parameter')

        elif rule_type == ValidationRuleType.CUSTOM:
            if 'expression' not in params or not params['expression']:
                raise ValueError('Custom rule must have expression parameter')

        return self


class ValidationResult(BaseModel):
    """Model for storing validation results."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description='Unique identifier for this validation result'
    )
    rule_id: str = Field(
        ...,
        description='ID of the validation rule'
    )
    table_name: str = Field(
        ...,
        description='Database table name'
    )
    field_name: str = Field(
        ...,
        description='Field that was validated'
    )
    validated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When validation was performed'
    )
    success: bool = Field(
        ...,
        description='Whether validation passed'
    )
    failures: List[Dict[str, Any]] = Field(
        default_factory=list,
        description='List of validation failures'
    )
    total_records: int = Field(
        ...,
        description='Total number of records validated'
    )
    failed_records: int = Field(
        ...,
        description='Number of records that failed validation'
    )

    class Config:
        validate_assignment = True

    @field_serializer('validated_at')
    def serialize_datetime(self, dt: datetime.datetime, _info):
        """Serialize datetime fields for JSON serialization.

        Args:
            dt: Datetime to serialize

        Returns:
            ISO-formatted datetime string
        """
        return dt.isoformat()


class HistorySchedule(BaseModel):
    """Model for scheduling regular data collection."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description='Unique identifier for this schedule'
    )
    connection_id: str = Field(
        ...,
        description='Connection ID for the source data'
    )
    name: str = Field(
        ...,
        description='User-friendly name for this schedule'
    )
    description: Optional[str] = Field(
        None,
        description='Purpose of this historical data collection'
    )
    query_id: str = Field(
        ...,
        description='ID of the saved query to execute'
    )
    frequency: str = Field(
        ...,
        description='Cron-style schedule frequency'
    )
    retention_days: int = Field(
        365,
        description='Number of days to retain historical data',
        ge=1,
        le=3650
    )
    active: bool = Field(
        True,
        description='Whether this schedule is active'
    )
    last_run: Optional[datetime.datetime] = Field(
        None,
        description='When this schedule was last executed'
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this schedule was created'
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When this schedule was last updated'
    )

    class Config:
        validate_assignment = True

    @field_serializer('last_run', 'created_at', 'updated_at')
    def serialize_datetime(self, dt: Optional[datetime.datetime], _info):
        """Serialize datetime fields for JSON serialization.

        Args:
            dt: Datetime to serialize

        Returns:
            ISO-formatted datetime string or None
        """
        if dt is None:
            return None
        return dt.isoformat()

    @field_validator('frequency')
    def validate_frequency(cls, v: str) -> str:
        """Validate schedule frequency format.

        Args:
            v: Frequency string

        Returns:
            Valid frequency string

        Raises:
            ValueError: If frequency format is invalid
        """
        pattern = r'^\d+[smhdw]$'
        if not re.match(pattern, v.lower()):
            raise ValueError(
                "Invalid frequency format. Use format like '5m', '1h', '7d', '2w' "
                "where the letter represents minutes, hours, days, or weeks."
            )
        return v


class HistoryEntry(BaseModel):
    """Model for historical data collection entries."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description='Unique identifier for this history entry'
    )
    schedule_id: str = Field(
        ...,
        description='ID of the history schedule that created this entry'
    )
    connection_id: str = Field(
        ...,
        description='ID of the connection used'
    )
    query_id: str = Field(
        ...,
        description='ID of the query used'
    )
    table_name: str = Field(
        ...,
        description='Source table name'
    )
    collected_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='When data was collected'
    )
    snapshot_id: str = Field(
        ...,
        description='Unique identifier for this snapshot of data'
    )
    record_count: int = Field(
        ...,
        description='Number of records in this snapshot',
        ge=0
    )
    status: str = Field(
        'success',
        description='Status of data collection'
    )
    error_message: Optional[str] = Field(
        None,
        description='Error message if collection failed'
    )

    class Config:
        validate_assignment = True

    @field_serializer('collected_at')
    def serialize_datetime(self, dt: datetime.datetime, _info):
        """Serialize datetime fields for JSON serialization.

        Args:
            dt: Datetime to serialize

        Returns:
            ISO-formatted datetime string
        """
        return dt.isoformat()


class PluginSettings(BaseModel):
    """Settings for the database connector plugin."""

    recent_connections: List[str] = Field(
        default_factory=list,
        description='Recently used connection IDs'
    )
    default_connection_id: Optional[str] = Field(
        None,
        description='Default connection ID'
    )
    max_result_rows: int = Field(
        10000,
        description='Maximum number of rows to display/fetch',
        ge=100,
        le=1000000
    )
    query_history_limit: int = Field(
        100,
        description='Maximum number of entries in query history',
        ge=10,
        le=1000
    )
    auto_save_queries: bool = Field(
        True,
        description='Automatically save executed queries'
    )
    syntax_highlighting: bool = Field(
        True,
        description='Enable SQL syntax highlighting'
    )
    history_database_connection_id: Optional[str] = Field(
        None,
        description='Connection ID for history storage'
    )

    class Config:
        validate_assignment = True


@dataclass
class ColumnMetadata:
    """Metadata for database table columns."""

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
    """Metadata for database tables."""

    name: str
    schema: Optional[str] = None
    type: Optional[str] = None
    remarks: Optional[str] = None
    columns: List[ColumnMetadata] = field(default_factory=list)


@dataclass
class QueryResult:
    """Results from a database query execution."""

    records: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[ColumnMetadata] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0
    query: str = ''
    connection_id: str = ''
    executed_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    truncated: bool = False
    has_error: bool = False
    error_message: Optional[str] = None
    mapped_records: Optional[List[Dict[str, Any]]] = field(default=None)