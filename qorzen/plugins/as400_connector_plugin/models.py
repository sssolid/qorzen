from __future__ import annotations

"""
Data models for the AS400 Connector Plugin.

This module provides Pydantic models for AS400 connection configuration,
saved queries, and other data structures used by the plugin.
"""

import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, cast

from pydantic import BaseModel, Field, SecretStr, validator, root_validator


class AS400ConnectionConfig(BaseModel):
    """Configuration for connecting to AS400/iSeries databases securely using JT400."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this connection")
    name: str = Field(..., description="User-friendly name for this connection")
    jt400_jar_path: str = Field(
        ..., description="Path to the jt400.jar file for Java connection"
    )
    server: str = Field(..., description="AS400 server address")
    username: str = Field(..., description="AS400 username (read-only account)")
    password: SecretStr = Field(..., description="AS400 password")
    database: str = Field(..., description="AS400 database/library name")
    port: Optional[int] = Field(None, description="AS400 server port (default: 446)")
    ssl: bool = Field(True, description="Use SSL for connection")
    allowed_tables: Optional[List[str]] = Field(
        None, description="Whitelist of allowed tables"
    )
    allowed_schemas: Optional[List[str]] = Field(
        None, description="Whitelist of allowed schemas/libraries"
    )
    connection_timeout: int = Field(30, description="Connection timeout in seconds")
    query_timeout: int = Field(60, description="Query timeout in seconds")
    encrypt_connection: bool = Field(True, description="Encrypt connection parameters")

    @validator("port")
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        """Validate port is within allowed range."""
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("allowed_tables", "allowed_schemas")
    def validate_allowed_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and normalize allowed lists."""
        if v is not None:
            return [item.upper() for item in v]
        return v

    class Config:
        """Pydantic config."""
        validate_assignment = True
        extra = "forbid"


class SavedQuery(BaseModel):
    """Model for a saved SQL query with metadata."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this query")
    name: str = Field(..., description="User-friendly name for this query")
    description: Optional[str] = Field(None, description="Optional description of the query's purpose")
    query_text: str = Field(..., description="The SQL query text")
    connection_id: Optional[str] = Field(None, description="ID of the connection this query is associated with")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this query was created")
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                          description="When this query was last updated")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters if any")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing queries")
    is_favorite: bool = Field(False, description="Whether this query is marked as a favorite")

    class Config:
        """Pydantic config."""
        validate_assignment = True
        extra = "forbid"


class QueryHistoryEntry(BaseModel):
    """Model for tracking query execution history."""

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
        """Pydantic config."""
        validate_assignment = True
        extra = "forbid"


class QueryResultsFormat(str, Enum):
    """Enumeration of available query result formats."""

    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    XML = "xml"


class PluginSettings(BaseModel):
    """Plugin settings model."""

    recent_connections: List[str] = Field(default_factory=list, description="Recently used connection IDs")
    default_connection_id: Optional[str] = Field(None, description="Default connection ID")
    results_format: QueryResultsFormat = Field(QueryResultsFormat.TABLE, description="Default results display format")
    max_result_rows: int = Field(1000, description="Maximum number of rows to display")
    query_history_limit: int = Field(100, description="Maximum number of entries in query history")
    auto_save_queries: bool = Field(True, description="Automatically save executed queries")
    syntax_highlighting: bool = Field(True, description="Enable SQL syntax highlighting")

    class Config:
        """Pydantic config."""
        validate_assignment = True
        use_enum_values = True


@dataclass
class ColumnMetadata:
    """Type definition for column metadata."""

    name: str
    type_name: str
    type_code: int
    precision: int
    scale: int
    nullable: bool


@dataclass
class QueryResult:
    """Container for query results."""

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