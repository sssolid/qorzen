"""
Data models for the Database Connector Plugin.

This module defines Pydantic models for plugin configuration, saved queries,
connections, and other data structures used throughout the plugin.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ExportFormat(str, Enum):
    """Supported export formats for query results."""

    CSV = "csv"
    JSON = "json"
    XML = "xml"
    EXCEL = "excel"
    TSV = "tsv"
    HTML = "html"


class ConnectionType(str, Enum):
    """Supported database connection types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    MSSQL = "mssql"
    AS400 = "as400"
    ODBC = "odbc"


class SavedQuery(BaseModel):
    """Model for saved database queries."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    connection_id: str
    query_text: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    execution_count: int = 0

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate query name is not empty."""
        if not v.strip():
            raise ValueError("Query name cannot be empty")
        return v.strip()

    @validator('query_text')
    def validate_query_text(cls, v: str) -> str:
        """Validate query text is not empty."""
        if not v.strip():
            raise ValueError("Query text cannot be empty")
        return v.strip()


class DatabaseConnection(BaseModel):
    """Model for database connection configuration."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    connection_type: ConnectionType
    host: str = ""
    port: Optional[int] = None
    database: str = ""
    user: str = ""
    password: str = ""
    connection_string: Optional[str] = None
    ssl: bool = False
    read_only: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600
    connection_timeout: int = 10
    query_timeout: int = 30
    allowed_tables: Optional[List[str]] = None
    dsn: Optional[str] = None  # For ODBC connections
    jt400_jar_path: Optional[str] = None  # For AS400 connections
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_tested: Optional[datetime] = None
    is_active: bool = True

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate connection name is not empty."""
        if not v.strip():
            raise ValueError("Connection name cannot be empty")
        return v.strip()

    @validator('port')
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate port is in valid range."""
        if v is not None and (v <= 0 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class QueryResult(BaseModel):
    """Model for query execution results."""

    query_id: Optional[str] = None
    connection_id: str
    query: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    records: List[Dict[str, Any]] = Field(default_factory=list)
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0
    executed_at: datetime = Field(default_factory=datetime.now)
    has_error: bool = False
    error_message: Optional[str] = None
    truncated: bool = False
    applied_mapping: bool = False


class FieldMapping(BaseModel):
    """Model for database field mappings."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    table_name: str
    description: Optional[str] = None
    mappings: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('table_name')
    def validate_table_name(cls, v: str) -> str:
        """Validate table name is not empty."""
        if not v.strip():
            raise ValueError("Table name cannot be empty")
        return v.strip()


class ValidationRuleType(str, Enum):
    """Types of validation rules."""

    RANGE = "range"
    PATTERN = "pattern"
    NOT_NULL = "not_null"
    UNIQUE = "unique"
    LENGTH = "length"
    REFERENCE = "reference"
    ENUMERATION = "enumeration"
    CUSTOM = "custom"


class ValidationRule(BaseModel):
    """Model for data validation rules."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    connection_id: str
    table_name: str
    field_name: str
    rule_type: ValidationRuleType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    error_message: str
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate rule name is not empty."""
        if not v.strip():
            raise ValueError("Rule name cannot be empty")
        return v.strip()

    @validator('field_name')
    def validate_field_name(cls, v: str) -> str:
        """Validate field name is not empty."""
        if not v.strip():
            raise ValueError("Field name cannot be empty")
        return v.strip()


class HistorySchedule(BaseModel):
    """Model for history collection schedules."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    connection_id: str
    query_id: str
    frequency: str  # Format: "1h", "30m", "1d", etc.
    retention_days: int = 365
    active: bool = True
    last_run: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate schedule name is not empty."""
        if not v.strip():
            raise ValueError("Schedule name cannot be empty")
        return v.strip()

    @validator('frequency')
    def validate_frequency(cls, v: str) -> str:
        """Validate frequency format."""
        import re
        if not re.match(r'^\d+[smhdw]$', v.lower()):
            raise ValueError("Frequency must be in format: number + unit (s/m/h/d/w)")
        return v.lower()

    @validator('retention_days')
    def validate_retention_days(cls, v: int) -> int:
        """Validate retention days is positive."""
        if v <= 0:
            raise ValueError("Retention days must be positive")
        return v


class ExportSettings(BaseModel):
    """Model for export configuration settings."""

    format: ExportFormat = ExportFormat.CSV
    include_headers: bool = True
    delimiter: str = ","  # For CSV/TSV
    quote_char: str = '"'  # For CSV/TSV
    encoding: str = "utf-8"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    null_value: str = ""
    max_rows: Optional[int] = None
    file_prefix: str = "query_result"
    compress: bool = False


class PluginSettings(BaseModel):
    """Model for plugin configuration settings."""

    version: str = "1.0.0"
    default_connection_id: Optional[str] = None
    recent_connections: List[str] = Field(default_factory=list)
    max_recent_connections: int = 10
    query_limit: int = 1000
    auto_limit_queries: bool = True
    syntax_highlighting: bool = True
    auto_format_queries: bool = False
    show_query_execution_time: bool = True
    default_export_format: ExportFormat = ExportFormat.CSV
    export_settings: ExportSettings = Field(default_factory=ExportSettings)
    font_family: str = "Consolas"
    font_size: int = 11
    theme: str = "default"
    auto_save_queries: bool = True
    confirm_delete: bool = True
    show_row_numbers: bool = True
    word_wrap: bool = False

    @validator('query_limit')
    def validate_query_limit(cls, v: int) -> int:
        """Validate query limit is positive."""
        if v <= 0:
            raise ValueError("Query limit must be positive")
        return v

    @validator('max_recent_connections')
    def validate_max_recent_connections(cls, v: int) -> int:
        """Validate max recent connections is positive."""
        if v <= 0:
            raise ValueError("Max recent connections must be positive")
        return v


class TableInfo(BaseModel):
    """Model for database table information."""

    name: str
    db_schema: Optional[str] = None
    type: str = "TABLE"  # TABLE, VIEW, etc.
    remarks: Optional[str] = None
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: Optional[int] = None


class ColumnInfo(BaseModel):
    """Model for database column information."""

    name: str
    type_name: str
    type_code: int = 0
    precision: int = 0
    scale: int = 0
    nullable: bool = True
    table_name: Optional[str] = None
    remarks: Optional[str] = None
    is_primary_key: bool = False
    default_value: Optional[str] = None