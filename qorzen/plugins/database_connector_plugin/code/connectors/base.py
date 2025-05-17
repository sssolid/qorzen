#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Base connector interface for the Database Connector Plugin.

This module provides the base interface that all database connectors must implement,
defining a consistent API for interacting with different database systems.
"""

import abc
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Protocol, TypeVar

from ..models import (
    BaseConnectionConfig,
    ColumnMetadata,
    QueryResult,
    TableMetadata
)

# Type aliases for common return types
TableList = List[TableMetadata]
FieldList = List[ColumnMetadata]
T = TypeVar('T', bound=BaseConnectionConfig)


class DatabaseConnectorProtocol(Protocol[T]):
    """Protocol defining the interface that all database connectors must implement."""

    @property
    def config(self) -> T:
        """Return the connection configuration."""
        ...

    @property
    def is_connected(self) -> bool:
        """Return True if the connection is active."""
        ...

    async def connect(self) -> None:
        """Establish a connection to the database."""
        ...

    async def disconnect(self) -> None:
        """Close the database connection."""
        ...

    async def execute_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None
    ) -> QueryResult:
        """
        Execute a SQL query against the database.

        Args:
            query: The SQL query to execute
            params: Optional parameters to bind to the query
            limit: Optional row limit

        Returns:
            QueryResult object containing the results and metadata
        """
        ...

    async def get_tables(self, schema: Optional[str] = None) -> TableList:
        """
        Get a list of tables available in the database or schema.

        Args:
            schema: Optional schema/library name to limit results

        Returns:
            List of TableMetadata objects
        """
        ...

    async def get_table_columns(
            self,
            table_name: str,
            schema: Optional[str] = None
    ) -> FieldList:
        """
        Get a list of columns in the specified table.

        Args:
            table_name: Name of the table
            schema: Optional schema/library name

        Returns:
            List of ColumnMetadata objects
        """
        ...

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test if the connection works.

        Returns:
            Tuple of (success, error_message)
        """
        ...

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.

        Returns:
            Dictionary with connection details
        """
        ...


class BaseDatabaseConnector(abc.ABC):
    """Abstract base class for database connectors."""

    def __init__(
            self,
            config: BaseConnectionConfig,
            logger: Any
    ) -> None:
        """
        Initialize the database connector.

        Args:
            config: Connection configuration
            logger: Logger instance
        """
        self._config = config
        self._logger = logger
        self._connected = False
        self._connect_lock = asyncio.Lock()
        self._last_error: Optional[str] = None
        self._last_connect_time: Optional[float] = None
        self._query_cancel_event: Optional[asyncio.Event] = None

    @property
    def config(self) -> BaseConnectionConfig:
        """Return the connection configuration."""
        return self._config

    @property
    def is_connected(self) -> bool:
        """Return True if the connection is active."""
        return self._connected

    @abc.abstractmethod
    async def connect(self) -> None:
        """
        Establish a connection to the database.

        Raises:
            DatabaseError: If connection fails
        """
        pass

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """
        Close the database connection.

        Raises:
            DatabaseError: If closing the connection fails
        """
        pass

    @abc.abstractmethod
    async def execute_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None
    ) -> QueryResult:
        """
        Execute a SQL query against the database.

        Args:
            query: The SQL query to execute
            params: Optional parameters to bind to the query
            limit: Optional row limit

        Returns:
            QueryResult object containing the results and metadata

        Raises:
            DatabaseError: If query execution fails
            SecurityError: If query violates security constraints
        """
        pass

    @abc.abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> TableList:
        """
        Get a list of tables available in the database or schema.

        Args:
            schema: Optional schema/library name to limit results

        Returns:
            List of TableMetadata objects

        Raises:
            DatabaseError: If retrieving tables fails
        """
        pass

    @abc.abstractmethod
    async def get_table_columns(
            self,
            table_name: str,
            schema: Optional[str] = None
    ) -> FieldList:
        """
        Get a list of columns in the specified table.

        Args:
            table_name: Name of the table
            schema: Optional schema/library name

        Returns:
            List of ColumnMetadata objects

        Raises:
            DatabaseError: If retrieving columns fails
        """
        pass

    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test if the connection works.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Try to connect if not connected
            if not self._connected:
                await self.connect()
            # Execute a simple test query
            await self.execute_query("SELECT 1")
            return True, None
        except Exception as e:
            error_msg = str(e)
            self._last_error = error_msg
            return False, error_msg
        finally:
            # Make sure to disconnect if we connected just for testing
            if self._connected:
                await self.disconnect()

    async def cancel_query(self) -> bool:
        """
        Cancel the currently executing query if possible.

        Returns:
            True if cancellation was successful, False otherwise
        """
        if self._query_cancel_event is not None:
            self._query_cancel_event.set()
            return True
        return False

    @abc.abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.

        Returns:
            Dictionary with connection details
        """
        pass

    def _sanitize_error_message(self, error_message: str) -> str:
        """
        Remove sensitive information from error messages.

        Args:
            error_message: Original error message

        Returns:
            Sanitized error message
        """
        # Base implementation just removes password
        if hasattr(self._config, "password") and self._config.password:
            try:
                password = self._config.password.get_secret_value()
                error_message = error_message.replace(password, "[REDACTED]")
            except Exception:
                pass

        # Remove usernames
        if hasattr(self._config, "username"):
            error_message = error_message.replace(self._config.username, "[USERNAME]")

        return error_message

    def _sanitize_sql_for_logging(self, query: str) -> str:
        """
        Clean up SQL for logging (remove newlines, etc).

        Args:
            query: SQL query

        Returns:
            Sanitized query suitable for logging
        """
        return query.replace("\n", " ").replace("\r", " ")