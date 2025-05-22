from __future__ import annotations

"""
UI-specific data models for the Database Connector Plugin.

This module provides models for UI-specific functionality that don't belong
in the core database system (saved queries, UI preferences, etc.).
Core database functionality uses models from qorzen.core.database_manager.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SavedQuery(BaseModel):
    """UI-specific saved query model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Query name")
    description: Optional[str] = Field(default=None, description="Query description")
    connection_id: str = Field(..., description="Target connection ID")
    query_text: str = Field(..., description="SQL query text")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    tags: List[str] = Field(default_factory=list, description="Query tags")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class PluginSettings(BaseModel):
    """Plugin UI preferences and settings."""

    default_connection_id: Optional[str] = Field(
        default=None,
        description="Default connection for new queries"
    )
    recent_connections: List[str] = Field(
        default_factory=list,
        description="Recently used connection IDs"
    )
    query_limit: int = Field(
        default=1000,
        description="Default query result limit"
    )
    auto_save_queries: bool = Field(
        default=True,
        description="Automatically save executed queries"
    )
    show_system_tables: bool = Field(
        default=False,
        description="Show system tables in schema browser"
    )
    max_recent_connections: int = Field(
        default=10,
        description="Maximum number of recent connections to remember"
    )