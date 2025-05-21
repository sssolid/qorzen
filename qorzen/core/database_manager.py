from __future__ import annotations

import uuid

"""
Enhanced Database Manager for Qorzen.

This module provides a centralized database connection management system that supports
multiple database types (PostgreSQL, MySQL, SQLite, AS400, ODBC) and offers features
like field mapping, history tracking, and validation.
"""

import asyncio
import functools
import importlib
import os
import time
from contextlib import asynccontextmanager
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TypeVar, Union, cast, Callable, Awaitable, AsyncGenerator, Type, \
    Protocol, runtime_checkable

import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import (
    DatabaseError,
    ManagerInitializationError,
    ManagerShutdownError,
    DatabaseManagerInitializationError,
    SecurityError,
    ConfigurationError,
    ValidationError
)

# Type variables
T = TypeVar('T')
R = TypeVar('R')


class ConnectionType(str, Enum):
    """Supported database connection types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    MSSQL = "mssql"
    AS400 = "as400"
    ODBC = "odbc"


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    metadata = MetaData(
        naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_%(constraint_name)s',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s'
        }
    )


@runtime_checkable
class DatabaseConnectorProtocol(Protocol):
    """Protocol defining the interface for database connectors."""

    @property
    def config(self) -> "DatabaseConnectionConfig":
        """Get the connection configuration."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if the connector is connected to the database."""
        ...

    async def connect(self) -> None:
        """Connect to the database."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        ...

    async def execute_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a query with parameters."""
        ...

    async def get_tables(
            self,
            schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get a list of tables in the database."""
        ...

    async def get_table_columns(
            self,
            table_name: str,
            schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get the columns of a table."""
        ...

    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test the database connection."""
        ...

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        ...

    def set_database_manager(self, db_manager: "DatabaseManager") -> None:
        """Set the database manager for this connector."""
        ...


class DatabaseConnectionConfig:
    """Configuration for a database connection."""

    def __init__(
            self,
            name: str,
            db_type: str,
            host: str = "",
            port: int = 0,
            database: str = "",
            user: str = "",
            password: str = "",
            pool_size: int = 5,
            max_overflow: int = 10,
            pool_recycle: int = 3600,
            echo: bool = False,
            connection_string: Optional[str] = None,
            url: Optional[URL] = None,
            connection_timeout: int = 10,
            properties: Optional[Dict[str, Any]] = None,
            read_only: bool = False,
            ssl: bool = False,
            allowed_tables: Optional[List[str]] = None,
            dsn: Optional[str] = None,
            jt400_jar_path: Optional[str] = None,
            mapping_enabled: bool = False,
            history_enabled: bool = False,
            validation_enabled: bool = False,
            history_connection_id: Optional[str] = None,
            validation_connection_id: Optional[str] = None,
    ) -> None:
        """Initialize a database connection configuration.

        Args:
            name: Unique name for this connection
            db_type: Type of database (postgresql, mysql, sqlite, as400, odbc, etc.)
            host: Database host address
            port: Database port number
            database: Database name or SQLite file path
            user: Database username
            password: Database password
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            pool_recycle: Connection recycling time in seconds
            echo: Enable SQLAlchemy logging
            connection_string: Full connection string (alternative to individual parameters)
            url: SQLAlchemy URL object (alternative to connection_string)
            connection_timeout: Connection timeout in seconds for SQLAlchemy engine creation
            properties: Additional connection properties
            read_only: Whether this connection is read-only
            ssl: Enable SSL for connection
            allowed_tables: Whitelist of allowed tables
            dsn: ODBC Data Source Name
            jt400_jar_path: Path to JT400 JAR file for AS/400 connections
            mapping_enabled: Enable field mapping for this connection
            history_enabled: Enable history tracking for this connection
            validation_enabled: Enable data validation for this connection
            history_connection_id: Connection ID to use for history storage
            validation_connection_id: Connection ID to use for validation storage
        """
        self.name = name
        self.db_type = db_type.lower()
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.connection_string = connection_string
        self.url = url
        self.connection_timeout = connection_timeout
        self.properties = properties or {}
        self.read_only = read_only
        self.ssl = ssl
        self.allowed_tables = allowed_tables
        self.dsn = dsn
        self.jt400_jar_path = jt400_jar_path
        self.mapping_enabled = mapping_enabled
        self.history_enabled = history_enabled
        self.validation_enabled = validation_enabled
        self.history_connection_id = history_connection_id
        self.validation_connection_id = validation_connection_id


class DatabaseConnection:
    """Represents a database connection with associated state and metrics."""

    def __init__(self, config: DatabaseConnectionConfig) -> None:
        """Initialize a database connection.

        Args:
            config: The database connection configuration
        """
        self.config = config
        self.engine: Optional[Engine] = None
        self.async_engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.async_session_factory: Optional[sessionmaker] = None
        self.initialized = False
        self.healthy = False
        self.active_sessions: Set[Session] = set()
        self.active_async_sessions: Set[AsyncSession] = set()
        self.active_sessions_lock = asyncio.Lock()
        self.queries_total = 0
        self.queries_failed = 0
        self.query_times: List[float] = []
        self.metrics_lock = asyncio.Lock()
        self.connector: Optional[DatabaseConnectorProtocol] = None


class DatabaseManager(QorzenManager):
    """Enhanced Database Manager for handling multiple database types and features."""

    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        """Initialize the database manager.

        Args:
            config_manager: The configuration manager instance
            logger_manager: The logger manager instance
        """
        super().__init__(name="database_manager")
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger("database_manager")
        self._default_connection: Optional[DatabaseConnection] = None
        self._connections: Dict[str, DatabaseConnection] = {}
        self._connections_lock = asyncio.Lock()
        self._db_type: str = "postgresql"
        self._db_url: Optional[str] = None
        self._db_async_url: Optional[str] = None
        self._pool_size: int = 5
        self._max_overflow: int = 10
        self._pool_recycle: int = 3600
        self._echo: bool = False

        # Advanced features
        self._field_mapper = None
        self._history_manager = None
        self._validation_engine = None

        # Connector registry
        self._connector_registry: Dict[str, Type[DatabaseConnectorProtocol]] = {}

    async def initialize(self) -> None:
        """Initialize the database manager.

        Raises:
            DatabaseManagerInitializationError: If initialization fails
        """
        try:
            await self._register_builtin_connectors()

            db_config = await self._config_manager.get("database", {})
            self._db_type = db_config.get("type", "postgresql").lower()
            host = db_config.get("host", "localhost")
            port = db_config.get("port", self._get_default_port(self._db_type))
            name = db_config.get("name", "qorzen")
            user = db_config.get("user", "")
            password = db_config.get("password", "")
            self._pool_size = db_config.get("pool_size", 5)
            self._max_overflow = db_config.get("max_overflow", 10)
            self._pool_recycle = db_config.get("pool_recycle", 3600)
            self._echo = db_config.get("echo", False)

            # Create default connection
            default_config = DatabaseConnectionConfig(
                name="default",
                db_type=self._db_type,
                host=host,
                port=port,
                database=name,
                user=user,
                password=password,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_recycle=self._pool_recycle,
                echo=self._echo
            )

            connection = DatabaseConnection(default_config)

            await self._init_connection(connection)

            async with self._connections_lock:
                self._default_connection = connection
                self._connections["default"] = self._default_connection
                # await self._init_connection(self._default_connection)

            await self._config_manager.register_listener("database", self._on_config_changed)

            self._initialized = True

            # Initialize advanced features if configured
            await self._init_field_mapper()
            await self._init_history_manager()
            await self._init_validation_engine()

            self._logger.info(
                f"Database Manager initialized with {self._db_type} database",
                extra={"host": host, "port": port, "database": name}
            )

            self._healthy = True
        except Exception as e:
            self._logger.error(f"Failed to initialize Database Manager: {str(e)}")
            raise DatabaseManagerInitializationError(
                f"Failed to initialize Database Manager: {str(e)}",
                manager_name=self.name
            ) from e

    async def _register_builtin_connectors(self) -> None:
        """Register built-in database connectors."""
        try:
            # Import and register connector classes
            from qorzen.core.database.connectors.sqlite import SQLiteConnector
            self.register_connector_type(ConnectionType.SQLITE, SQLiteConnector)

            try:
                from qorzen.core.database.connectors.as400 import AS400Connector
                self.register_connector_type(ConnectionType.AS400, AS400Connector)
            except ImportError:
                self._logger.debug("AS400 connector not available: required dependencies missing")

            try:
                from qorzen.core.database.connectors.odbc import ODBCConnector
                self.register_connector_type(ConnectionType.ODBC, ODBCConnector)
            except ImportError:
                self._logger.debug("ODBC connector not available: required dependencies missing")

            self._logger.debug("Built-in database connectors registered")
        except Exception as e:
            self._logger.warning(f"Error registering built-in connectors: {str(e)}")

    def register_connector_type(
            self,
            connection_type: str,
            connector_class: Type[DatabaseConnectorProtocol]
    ) -> None:
        """Register a connector class for a connection type.

        Args:
            connection_type: The connection type name
            connector_class: The connector class to register
        """
        self._connector_registry[connection_type.lower()] = connector_class
        self._logger.debug(f"Registered connector type: {connection_type}")

    async def _init_connection(self, connection: DatabaseConnection) -> None:
        """Initialize a database connection based on its configuration.

        Args:
            connection: The database connection to initialize

        Raises:
            DatabaseError: If connection initialization fails
        """
        config = connection.config

        # Handle specialized connector types
        if config.db_type in self._connector_registry:
            await self._init_specialized_connection(connection)
            return

        # Standard SQLAlchemy connection handling
        if config.url:
            db_url = config.url
            db_async_url = None
        elif config.connection_string:
            db_url = config.connection_string
            db_async_url = None
        elif config.db_type == "sqlite":
            db_url = f"sqlite:///{config.database}"
            db_async_url = f"sqlite+aiosqlite:///{config.database}"
        elif config.db_type == "postgresql":
            db_url = URL.create(
                config.db_type,
                username=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database
            )
            db_async_url = URL.create(
                "postgresql+asyncpg",
                username=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database
            )
        elif config.db_type == "mysql":
            db_url = URL.create(
                config.db_type,
                username=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database
            )
            db_async_url = URL.create(
                "mysql+aiomysql",
                username=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database
            )
        else:
            # Other database types
            db_url = URL.create(
                config.db_type,
                username=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database
            )
            db_async_url = None

        engine_args = {
            "pool_size": config.pool_size,
            "max_overflow": config.max_overflow,
            "pool_recycle": config.pool_recycle,
            "echo": config.echo
        }

        if config.ssl:
            engine_args["connect_args"] = engine_args.get("connect_args", {})
            engine_args["connect_args"]["ssl"] = True

        if config.properties:
            for key, value in config.properties.items():
                if key == "connect_args":
                    engine_args["connect_args"] = engine_args.get("connect_args", {})
                    if isinstance(value, dict):
                        engine_args["connect_args"].update(value)
                else:
                    engine_args[key] = value

        connection.engine = create_engine(db_url, **engine_args)

        if db_async_url:
            connection.async_engine = create_async_engine(
                db_async_url,
                echo=config.echo,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_recycle=config.pool_recycle
            )

        connection.session_factory = sessionmaker(
            bind=connection.engine,
            expire_on_commit=False
        )

        if connection.async_engine:
            connection.async_session_factory = sessionmaker(
                bind=connection.async_engine,
                expire_on_commit=False,
                class_=AsyncSession
            )

        event.listen(
            connection.engine,
            "before_cursor_execute",
            functools.partial(self._before_cursor_execute, connection=connection)
        )

        event.listen(
            connection.engine,
            "after_cursor_execute",
            functools.partial(self._after_cursor_execute, connection=connection)
        )

        with connection.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        connection.initialized = True
        connection.healthy = True

    async def _init_specialized_connection(self, connection: DatabaseConnection) -> None:
        """Initialize a connection using a specialized connector.

        Args:
            connection: The database connection to initialize

        Raises:
            DatabaseError: If connection initialization fails
        """
        try:
            config = connection.config
            connector_class = self._connector_registry.get(config.db_type)

            if not connector_class:
                raise DatabaseError(
                    f"No connector available for database type: {config.db_type}",
                    details={"connection_name": config.name}
                )

            connector = connector_class(config, self._logger)
            connector.set_database_manager(self)

            await connector.connect()

            connection.connector = connector
            connection.initialized = True
            connection.healthy = True

            self._logger.info(
                f"Initialized specialized connection for {config.db_type}",
                extra={"connection_name": config.name}
            )
        except Exception as e:
            self._logger.error(
                f"Failed to initialize specialized connection: {str(e)}"
            )
            raise DatabaseError(
                f"Failed to initialize specialized connection: {str(e)}"
            ) from e

    async def _init_field_mapper(self) -> None:
        """Initialize the field mapping system if configured."""
        try:
            from qorzen.core.database.utils.field_mapper import FieldMapperManager

            self._field_mapper = FieldMapperManager(self, self._logger)
            await self._field_mapper.initialize()

            self._logger.info("Field mapping system initialized")
        except Exception as e:
            self._logger.warning(f"Failed to initialize field mapping system: {str(e)}")

    async def _init_history_manager(self) -> None:
        """Initialize the history tracking system if configured."""
        try:
            from qorzen.core.database.utils.history_manager import HistoryManager

            # Get history configuration
            history_config = await self._config_manager.get("database.history", {})
            history_connection_id = history_config.get("connection_id")

            if history_connection_id:
                self._history_manager = HistoryManager(
                    self,
                    self._logger,
                    history_connection_id
                )
                await self._history_manager.initialize()

                self._logger.info(
                    "History tracking system initialized",
                    extra={"history_connection_id": history_connection_id}
                )
            else:
                self._logger.debug("History tracking system not configured")
        except Exception as e:
            self._logger.warning(f"Failed to initialize history tracking system: {str(e)}")

    async def _init_validation_engine(self) -> None:
        """Initialize the validation engine if configured."""
        try:
            from qorzen.core.database.utils.validation_engine import ValidationEngine

            # Get validation configuration
            validation_config = await self._config_manager.get("database.validation", {})
            validation_connection_id = validation_config.get("connection_id")

            if validation_connection_id:
                self._validation_engine = ValidationEngine(
                    self,
                    self._logger,
                    validation_connection_id
                )
                await self._validation_engine.initialize()

                self._logger.info(
                    "Validation engine initialized",
                    extra={"validation_connection_id": validation_connection_id}
                )
            else:
                self._logger.debug("Validation engine not configured")
        except Exception as e:
            self._logger.warning(f"Failed to initialize validation engine: {str(e)}")

    async def register_connection(self, config: DatabaseConnectionConfig) -> None:
        """Register a new database connection.

        Args:
            config: The connection configuration

        Raises:
            DatabaseError: If registration fails
        """
        if not self._initialized:
            raise DatabaseError("Database Manager not initialized")

        async with self._connections_lock:
            if config.name in self._connections:
                raise DatabaseError(f"Connection with name {config.name} already exists")

            connection = DatabaseConnection(config)

            try:
                await self._init_connection(connection)
                self._connections[config.name] = connection

                self._logger.info(
                    f"Registered new database connection: {config.name}",
                    extra={
                        "connection": config.name,
                        "type": config.db_type,
                        "host": config.host,
                        "database": config.database
                    }
                )
            except Exception as e:
                self._logger.error(
                    f"Failed to register database connection {config.name}: {str(e)}",
                    extra={"connection": config.name}
                )
                raise DatabaseError(
                    f"Failed to register database connection {config.name}: {str(e)}"
                ) from e

    async def unregister_connection(self, name: str) -> bool:
        """Unregister a database connection.

        Args:
            name: The connection name

        Returns:
            bool: True if successful, False otherwise

        Raises:
            DatabaseError: If trying to unregister the default connection
        """
        if not self._initialized:
            return False

        if name == "default":
            raise DatabaseError("Cannot unregister the default connection")

        async with self._connections_lock:
            if name not in self._connections:
                return False

            connection = self._connections[name]

            async with connection.active_sessions_lock:
                # Close active sessions
                for session in list(connection.active_sessions):
                    try:
                        session.close()
                    except Exception:
                        pass
                connection.active_sessions.clear()

                for session in list(connection.active_async_sessions):
                    try:
                        await session.close()
                    except Exception:
                        pass
                connection.active_async_sessions.clear()

            # Disconnect specialized connector if present
            if connection.connector:
                try:
                    await connection.connector.disconnect()
                except Exception as e:
                    self._logger.warning(
                        f"Error disconnecting specialized connector: {str(e)}"
                    )

            # Dispose engine
            if connection.engine:
                connection.engine.dispose()

            if connection.async_engine:
                await connection.async_engine.dispose()

            del self._connections[name]

            self._logger.info(f"Unregistered database connection: {name}")

            return True

    async def has_connection(self, name: str) -> bool:
        """Check if a connection exists.

        Args:
            name: The connection name

        Returns:
            bool: True if the connection exists
        """
        async with self._connections_lock:
            return name in self._connections

    async def get_connection_names(self) -> List[str]:
        """Get a list of connection names.

        Returns:
            List[str]: List of connection names
        """
        async with self._connections_lock:
            return list(self._connections.keys())

    async def _get_connection(self, connection_name: Optional[str] = None) -> DatabaseConnection:
        """Get a connection by name.

        Args:
            connection_name: The connection name, or None for default

        Returns:
            DatabaseConnection: The database connection

        Raises:
            DatabaseError: If connection not found or not initialized
        """
        if not self._initialized:
            raise DatabaseError("Database Manager not initialized")

        name = connection_name or "default"

        async with self._connections_lock:
            if name not in self._connections:
                raise DatabaseError(f"Database connection {name} not found")

            connection = self._connections[name]

            if not connection.initialized:
                raise DatabaseError(f"Database connection {name} not initialized")

            return connection

    def _get_default_port(self, db_type: str) -> int:
        """Get the default port for a database type.

        Args:
            db_type: The database type

        Returns:
            int: The default port number
        """
        default_ports = {
            "postgresql": 5432,
            "mysql": 3306,
            "mariadb": 3306,
            "oracle": 1521,
            "mssql": 1433,
            "sqlite": 0,
            "as400": 446,
        }
        return default_ports.get(db_type, 0)

    @asynccontextmanager
    async def session(self, connection_name: Optional[str] = None) -> AsyncGenerator[Session, None]:
        """Get a synchronous session for a connection.

        Args:
            connection_name: The connection name, or None for default

        Yields:
            Session: A SQLAlchemy session

        Raises:
            DatabaseError: If session creation fails
        """
        connection = await self._get_connection(connection_name)

        # Use specialized connector if available
        if connection.connector:
            raise DatabaseError(
                f"Synchronous sessions not supported for connector type: {connection.config.db_type}"
            )

        if not connection.session_factory:
            raise DatabaseError(
                f"Session factory not initialized for connection {connection.config.name}"
            )

        session = connection.session_factory()

        async with connection.active_sessions_lock:
            connection.active_sessions.add(session)

        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}") from e
        except Exception as e:
            session.rollback()
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f"Error during database operation: {str(e)}")
            raise
        finally:
            session.close()
            async with connection.active_sessions_lock:
                connection.active_sessions.discard(session)

    @asynccontextmanager
    async def async_session(self, connection_name: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous session for a connection.

        Args:
            connection_name: The connection name, or None for default

        Yields:
            AsyncSession: A SQLAlchemy async session

        Raises:
            DatabaseError: If session creation fails
        """
        connection = await self._get_connection(connection_name)

        # Use specialized connector if available
        if connection.connector:
            raise DatabaseError(
                f"Async sessions not supported for connector type: {connection.config.db_type}"
            )

        if not connection.async_session_factory:
            raise DatabaseError(
                f"Async session factory not initialized for connection {connection.config.name}"
            )

        session = connection.async_session_factory()

        async with connection.active_sessions_lock:
            connection.active_async_sessions.add(session)

        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}") from e
        except Exception as e:
            await session.rollback()
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f"Error during database operation: {str(e)}")
            raise
        finally:
            await session.close()
            async with connection.active_sessions_lock:
                connection.active_async_sessions.discard(session)

    async def execute(
            self,
            statement: Any,
            connection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a SQLAlchemy statement.

        Args:
            statement: The SQLAlchemy statement
            connection_name: The connection name, or None for default

        Returns:
            List[Dict[str, Any]]: The query results

        Raises:
            DatabaseError: If execution fails
        """
        connection = await self._get_connection(connection_name)

        # Use specialized connector if available
        if connection.connector:
            raise DatabaseError(
                "For specialized connectors, use execute_query instead of execute"
            )

        if not connection.engine:
            raise DatabaseError(
                f"Engine not initialized for connection {connection.config.name}"
            )

        try:
            with connection.engine.connect() as conn:
                result = conn.execute(statement)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}") from e

    async def execute_raw(
            self,
            sql: str,
            params: Optional[Dict[str, Any]] = None,
            connection_name: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL statement.

        Args:
            sql: The SQL statement
            params: Query parameters
            connection_name: The connection name, or None for default
            limit: Maximum number of rows to return

        Returns:
            List[Dict[str, Any]]: The query results

        Raises:
            DatabaseError: If execution fails
        """
        connection = await self._get_connection(connection_name)

        # Apply limit if specified and not already in query
        if limit is not None and "LIMIT" not in sql.upper():
            sql = f"{sql} LIMIT {limit}"

        # Use specialized connector if available
        if connection.connector:
            try:
                result = await connection.connector.execute_query(
                    sql,
                    params,
                    limit
                )
                return result.get("records", [])
            except Exception as e:
                self._logger.error(f"Error executing query with specialized connector: {str(e)}")
                raise DatabaseError(
                    f"Error executing query with specialized connector: {str(e)}",
                    query=sql
                ) from e

        if not connection.engine:
            raise DatabaseError(
                f"Engine not initialized for connection {connection.config.name}"
            )

        try:
            with connection.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}", query=sql) from e

    async def execute_async(
            self,
            statement: Any,
            connection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a SQLAlchemy statement asynchronously.

        Args:
            statement: The SQLAlchemy statement
            connection_name: The connection name, or None for default

        Returns:
            List[Dict[str, Any]]: The query results

        Raises:
            DatabaseError: If execution fails
        """
        connection = await self._get_connection(connection_name)

        # Use specialized connector if available
        if connection.connector:
            raise DatabaseError(
                "For specialized connectors, use execute_query instead of execute_async"
            )

        if not connection.async_engine:
            raise DatabaseError(
                f"Async engine not initialized for connection {connection.config.name}"
            )

        try:
            async with connection.async_engine.connect() as conn:
                result = await conn.execute(statement)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}") from e
        except Exception as e:
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f"Error during async database operation: {str(e)}")
            raise

    async def execute_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None,
            connection_name: Optional[str] = None,
            limit: Optional[int] = None,
            apply_mapping: bool = False
    ) -> Dict[str, Any]:
        """Execute a query with parameters.

        This is the preferred method for executing queries, especially with specialized connectors.

        Args:
            query: The SQL query
            params: Query parameters
            connection_name: The connection name, or None for default
            limit: Maximum number of rows to return
            apply_mapping: Whether to apply field mapping

        Returns:
            Dict[str, Any]: The query results

        Raises:
            DatabaseError: If execution fails
        """
        connection = await self._get_connection(connection_name)

        # Use specialized connector if available
        if connection.connector:
            try:
                original_query = query

                # Apply field mapping if requested
                if apply_mapping and self._field_mapper and connection.config.mapping_enabled:
                    try:
                        # Get the table name from the query
                        table_name = self._extract_table_name(query)
                        if table_name:
                            mapping = await self._field_mapper.get_mapping(
                                connection.config.name,
                                table_name
                            )
                            if mapping:
                                query = await self._field_mapper.apply_mapping_to_query(
                                    query,
                                    mapping
                                )
                    except Exception as e:
                        self._logger.warning(
                            f"Error applying field mapping: {str(e)}, using original query"
                        )
                        query = original_query

                result = await connection.connector.execute_query(
                    query,
                    params,
                    limit
                )

                # Apply field mapping to results if requested
                if apply_mapping and self._field_mapper and connection.config.mapping_enabled:
                    try:
                        # Get the table name from the query
                        table_name = self._extract_table_name(query)
                        if table_name:
                            mapping = await self._field_mapper.get_mapping(
                                connection.config.name,
                                table_name
                            )
                            if mapping:
                                result = await self._field_mapper.apply_mapping_to_results(
                                    result,
                                    mapping
                                )
                    except Exception as e:
                        self._logger.warning(f"Error applying field mapping to results: {str(e)}")

                return result
            except Exception as e:
                self._logger.error(f"Error executing query with specialized connector: {str(e)}")
                raise DatabaseError(
                    f"Error executing query with specialized connector: {str(e)}",
                    query=query
                ) from e

        # Fall back to standard execution
        try:
            records = await self.execute_raw(query, params, connection_name, limit)

            # Extract column metadata from first record
            columns = []
            if records:
                for key in records[0].keys():
                    columns.append({
                        "name": key,
                        "type_name": "UNKNOWN",
                        "type_code": 0,
                        "precision": 0,
                        "scale": 0,
                        "nullable": True
                    })

            result = {
                "records": records,
                "columns": columns,
                "row_count": len(records),
                "query": query,
                "connection_id": connection.config.name,
                "truncated": limit is not None and len(records) >= limit
            }

            # Apply field mapping if requested
            if apply_mapping and self._field_mapper and connection.config.mapping_enabled:
                try:
                    # Get the table name from the query
                    table_name = self._extract_table_name(query)
                    if table_name:
                        mapping = await self._field_mapper.get_mapping(
                            connection.config.name,
                            table_name
                        )
                        if mapping:
                            result = await self._field_mapper.apply_mapping_to_results(
                                result,
                                mapping
                            )
                except Exception as e:
                    self._logger.warning(f"Error applying field mapping to results: {str(e)}")

            return result
        except Exception as e:
            raise DatabaseError(f"Error executing query: {str(e)}", query=query) from e

    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract the table name from a query.

        Args:
            query: The SQL query

        Returns:
            Optional[str]: The table name, or None if not found
        """
        # Simple extraction, doesn't handle all SQL variations
        import re
        match = re.search(r'FROM\s+([^\s,;()]+)', query, re.IGNORECASE)
        if match:
            return match.group(1).strip('"`[]')
        return None

    async def get_tables(
            self,
            connection_name: Optional[str] = None,
            schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get a list of tables for a connection.

        Args:
            connection_name: The connection name, or None for default
            schema: Schema/database name to filter tables

        Returns:
            List[Dict[str, Any]]: List of table metadata

        Raises:
            DatabaseError: If operation fails
        """
        connection = await self._get_connection(connection_name)

        # Use specialized connector if available
        if connection.connector:
            try:
                return await connection.connector.get_tables(schema)
            except Exception as e:
                self._logger.error(
                    f"Error getting tables with specialized connector: {str(e)}"
                )
                raise DatabaseError(
                    f"Error getting tables with specialized connector: {str(e)}"
                ) from e

        # Fall back to generic implementation
        try:
            if connection.engine:
                metadata = MetaData()
                metadata.reflect(bind=connection.engine, schema=schema)
                tables = []

                for name, table in metadata.tables.items():
                    table_schema = table.schema
                    columns = []

                    for column in table.columns:
                        columns.append({
                            "name": column.name,
                            "type_name": str(column.type),
                            "nullable": column.nullable,
                            "primary_key": column.primary_key,
                            "default": str(column.default) if column.default else None,
                        })

                    tables.append({
                        "name": table.name,
                        "schema": table_schema,
                        "columns": columns
                    })

                return tables
            else:
                raise DatabaseError(
                    f"Engine not initialized for connection {connection.config.name}"
                )
        except Exception as e:
            self._logger.error(f"Error getting tables: {str(e)}")
            raise DatabaseError(f"Error getting tables: {str(e)}") from e

    async def get_table_columns(
            self,
            table_name: str,
            connection_name: Optional[str] = None,
            schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column information for a table.

        Args:
            table_name: The table name
            connection_name: The connection name, or None for default
            schema: Schema/database name

        Returns:
            List[Dict[str, Any]]: List of column metadata

        Raises:
            DatabaseError: If operation fails
        """
        connection = await self._get_connection(connection_name)

        # Use specialized connector if available
        if connection.connector:
            try:
                return await connection.connector.get_table_columns(table_name, schema)
            except Exception as e:
                self._logger.error(
                    f"Error getting table columns with specialized connector: {str(e)}"
                )
                raise DatabaseError(
                    f"Error getting table columns with specialized connector: {str(e)}"
                ) from e

        # Fall back to generic implementation
        try:
            if connection.engine:
                metadata = MetaData()
                table = sqlalchemy.Table(
                    table_name,
                    metadata,
                    schema=schema,
                    autoload_with=connection.engine
                )

                columns = []
                for column in table.columns:
                    columns.append({
                        "name": column.name,
                        "type_name": str(column.type),
                        "nullable": column.nullable,
                        "primary_key": column.primary_key,
                        "default": str(column.default) if column.default else None,
                    })

                return columns
            else:
                raise DatabaseError(
                    f"Engine not initialized for connection {connection.config.name}"
                )
        except Exception as e:
            self._logger.error(f"Error getting table columns: {str(e)}")
            raise DatabaseError(f"Error getting table columns: {str(e)}") from e

    async def create_tables(self, connection_name: Optional[str] = None) -> None:
        """Create all tables in the metadata.

        Args:
            connection_name: The connection name, or None for default

        Raises:
            DatabaseError: If table creation fails
        """
        connection = await self._get_connection(connection_name)

        # Specialized connectors don't support this operation
        if connection.connector:
            raise DatabaseError(
                f"create_tables not supported for connector type: {connection.config.db_type}"
            )

        if not connection.engine:
            raise DatabaseError(
                f"Engine not initialized for connection {connection.config.name}"
            )

        try:
            Base.metadata.create_all(connection.engine)
            self._logger.info(f"Created database tables for connection {connection.config.name}")
        except SQLAlchemyError as e:
            self._logger.error(f"Failed to create tables: {str(e)}")
            raise DatabaseError(f"Failed to create tables: {str(e)}") from e

    async def create_tables_async(self, connection_name: Optional[str] = None) -> None:
        """Create all tables in the metadata asynchronously.

        Args:
            connection_name: The connection name, or None for default

        Raises:
            DatabaseError: If table creation fails
        """
        connection = await self._get_connection(connection_name)

        # Specialized connectors don't support this operation
        if connection.connector:
            raise DatabaseError(
                f"create_tables_async not supported for connector type: {connection.config.db_type}"
            )

        if not connection.async_engine:
            raise DatabaseError(
                f"Async engine not initialized for connection {connection.config.name}"
            )

        try:
            async with connection.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self._logger.info(
                f"Created database tables asynchronously for connection {connection.config.name}"
            )
        except SQLAlchemyError as e:
            self._logger.error(f"Failed to create tables asynchronously: {str(e)}")
            raise DatabaseError(f"Failed to create tables asynchronously: {str(e)}") from e

    async def check_connection(self, connection_name: Optional[str] = None) -> bool:
        """Check if a connection is working.

        Args:
            connection_name: The connection name, or None for default

        Returns:
            bool: True if connection is working
        """
        try:
            connection = await self._get_connection(connection_name)

            # Use specialized connector if available
            if connection.connector:
                result, _ = await connection.connector.test_connection()
                return result

            if not connection.engine:
                return False

            with connection.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            return True
        except (DatabaseError, SQLAlchemyError):
            return False

    async def get_engine(self, connection_name: Optional[str] = None) -> Optional[Engine]:
        """Get the SQLAlchemy engine for a connection.

        Args:
            connection_name: The connection name, or None for default

        Returns:
            Optional[Engine]: The SQLAlchemy engine, or None if not available
        """
        try:
            connection = await self._get_connection(connection_name)
            return connection.engine
        except DatabaseError:
            return None

    async def get_async_engine(self, connection_name: Optional[str] = None) -> Optional[AsyncEngine]:
        """Get the SQLAlchemy async engine for a connection.

        Args:
            connection_name: The connection name, or None for default

        Returns:
            Optional[AsyncEngine]: The SQLAlchemy async engine, or None if not available
        """
        try:
            connection = await self._get_connection(connection_name)
            return connection.async_engine
        except DatabaseError:
            return None

    def _before_cursor_execute(
            self,
            conn: Connection,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
            connection: DatabaseConnection
    ) -> None:
        """Event hook called before cursor execution.

        Args:
            conn: The SQLAlchemy connection
            cursor: The cursor
            statement: The SQL statement
            parameters: The query parameters
            context: The execution context
            executemany: Whether multiple statements are executed
            connection: The database connection
        """
        context._query_start_time = time.time()

    def _after_cursor_execute(
            self,
            conn: Connection,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
            connection: DatabaseConnection
    ) -> None:
        """Event hook called after cursor execution.

        Args:
            conn: The SQLAlchemy connection
            cursor: The cursor
            statement: The SQL statement
            parameters: The query parameters
            context: The execution context
            executemany: Whether multiple statements are executed
            connection: The database connection
        """
        query_time = time.time() - context._query_start_time
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(
            self._update_query_metrics(connection, query_time, statement),
            loop
        )

    async def _update_query_metrics(
            self,
            connection: DatabaseConnection,
            query_time: float,
            statement: str
    ) -> None:
        """Update query metrics for a connection.

        Args:
            connection: The database connection
            query_time: The query execution time in seconds
            statement: The SQL statement
        """
        async with connection.metrics_lock:
            connection.queries_total += 1
            connection.query_times.append(query_time)

            if len(connection.query_times) > 100:
                connection.query_times.pop(0)

            if query_time > 1.0:
                self._logger.warning(
                    f"Slow query: {query_time:.3f}s",
                    extra={
                        "query_time": query_time,
                        "statement": statement[:1000],
                        "connection": connection.config.name
                    }
                )

    async def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: The config key
            value: The config value
        """
        if key.startswith("database."):
            self._logger.warning(
                f"Configuration change to {key} requires restart to take effect",
                extra={"key": key}
            )

    # Field mapping functionality

    async def create_field_mapping(
            self,
            connection_id: str,
            table_name: str,
            mappings: Dict[str, str],
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a field mapping for a table.

        Args:
            connection_id: The connection ID
            table_name: The table name
            mappings: Dictionary of original field names to mapped names
            description: Optional description

        Returns:
            Dict[str, Any]: The created mapping

        Raises:
            DatabaseError: If field mapping creation fails
        """
        if not self._field_mapper:
            raise DatabaseError("Field mapping system not initialized")

        return await self._field_mapper.create_mapping(
            connection_id,
            table_name,
            mappings,
            description
        )

    async def get_field_mapping(
            self,
            connection_id: str,
            table_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get a field mapping for a table.

        Args:
            connection_id: The connection ID
            table_name: The table name

        Returns:
            Optional[Dict[str, Any]]: The field mapping, or None if not found
        """
        if not self._field_mapper:
            return None

        return await self._field_mapper.get_mapping(connection_id, table_name)

    async def delete_field_mapping(
            self,
            mapping_id: str
    ) -> bool:
        """Delete a field mapping.

        Args:
            mapping_id: The mapping ID

        Returns:
            bool: True if successful
        """
        if not self._field_mapper:
            return False

        return await self._field_mapper.delete_mapping(mapping_id)

    async def get_all_field_mappings(
            self,
            connection_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all field mappings, optionally filtered by connection ID.

        Args:
            connection_id: The connection ID to filter by

        Returns:
            List[Dict[str, Any]]: List of field mappings
        """
        if not self._field_mapper:
            return []

        return await self._field_mapper.get_all_mappings(connection_id)

    # History tracking functionality

    async def create_history_schedule(
            self,
            connection_id: str,
            query_id: str,
            frequency: str,
            name: str,
            description: Optional[str] = None,
            retention_days: int = 365
    ) -> Dict[str, Any]:
        """Create a history tracking schedule.

        Args:
            connection_id: The connection ID
            query_id: The query ID to execute
            frequency: Frequency expression (e.g., '1h', '1d', '7d')
            name: Schedule name
            description: Optional description
            retention_days: Number of days to retain history

        Returns:
            Dict[str, Any]: The created schedule

        Raises:
            DatabaseError: If schedule creation fails
        """
        if not self._history_manager:
            raise DatabaseError("History tracking system not initialized")

        return await self._history_manager.create_schedule(
            connection_id,
            query_id,
            frequency,
            name,
            description,
            retention_days
        )

    async def update_history_schedule(
            self,
            schedule_id: str,
            **updates: Any
    ) -> Dict[str, Any]:
        """Update a history tracking schedule.

        Args:
            schedule_id: The schedule ID
            **updates: Fields to update

        Returns:
            Dict[str, Any]: The updated schedule

        Raises:
            DatabaseError: If schedule update fails
        """
        if not self._history_manager:
            raise DatabaseError("History tracking system not initialized")

        return await self._history_manager.update_schedule(schedule_id, **updates)

    async def delete_history_schedule(
            self,
            schedule_id: str
    ) -> bool:
        """Delete a history tracking schedule.

        Args:
            schedule_id: The schedule ID

        Returns:
            bool: True if successful

        Raises:
            DatabaseError: If schedule deletion fails
        """
        if not self._history_manager:
            raise DatabaseError("History tracking system not initialized")

        return await self._history_manager.delete_schedule(schedule_id)

    async def get_history_schedule(
            self,
            schedule_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a history tracking schedule.

        Args:
            schedule_id: The schedule ID

        Returns:
            Optional[Dict[str, Any]]: The schedule, or None if not found
        """
        if not self._history_manager:
            return None

        return await self._history_manager.get_schedule(schedule_id)

    async def get_all_history_schedules(self) -> List[Dict[str, Any]]:
        """Get all history tracking schedules.

        Returns:
            List[Dict[str, Any]]: List of schedules
        """
        if not self._history_manager:
            return []

        return await self._history_manager.get_all_schedules()

    async def execute_history_schedule_now(
            self,
            schedule_id: str
    ) -> Dict[str, Any]:
        """Execute a history tracking schedule immediately.

        Args:
            schedule_id: The schedule ID

        Returns:
            Dict[str, Any]: The execution result

        Raises:
            DatabaseError: If execution fails
        """
        if not self._history_manager:
            raise DatabaseError("History tracking system not initialized")

        return await self._history_manager.execute_schedule_now(schedule_id)

    async def get_history_entries(
            self,
            schedule_id: Optional[str] = None,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get history entries, optionally filtered by schedule ID.

        Args:
            schedule_id: The schedule ID to filter by
            limit: Maximum number of entries to return

        Returns:
            List[Dict[str, Any]]: List of history entries
        """
        if not self._history_manager:
            return []

        return await self._history_manager.get_history_entries(schedule_id, limit)

    async def get_history_data(
            self,
            snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get history data for a snapshot.

        Args:
            snapshot_id: The snapshot ID

        Returns:
            Optional[Dict[str, Any]]: The history data, or None if not found
        """
        if not self._history_manager:
            return None

        return await self._history_manager.get_history_data(snapshot_id)

    # Validation functionality

    async def create_validation_rule(
            self,
            rule_type: str,
            connection_id: str,
            table_name: str,
            field_name: str,
            parameters: Dict[str, Any],
            error_message: str,
            name: Optional[str] = None,
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a validation rule.

        Args:
            rule_type: Type of validation rule
            connection_id: The connection ID
            table_name: The table name
            field_name: The field name
            parameters: Rule parameters
            error_message: Error message when validation fails
            name: Optional rule name
            description: Optional description

        Returns:
            Dict[str, Any]: The created rule

        Raises:
            DatabaseError: If rule creation fails
        """
        if not self._validation_engine:
            raise DatabaseError("Validation system not initialized")

        return await self._validation_engine.create_rule(
            rule_type,
            connection_id,
            table_name,
            field_name,
            parameters,
            error_message,
            name,
            description
        )

    async def update_validation_rule(
            self,
            rule_id: str,
            **updates: Any
    ) -> Dict[str, Any]:
        """Update a validation rule.

        Args:
            rule_id: The rule ID
            **updates: Fields to update

        Returns:
            Dict[str, Any]: The updated rule

        Raises:
            DatabaseError: If rule update fails
        """
        if not self._validation_engine:
            raise DatabaseError("Validation system not initialized")

        return await self._validation_engine.update_rule(rule_id, **updates)

    async def delete_validation_rule(
            self,
            rule_id: str
    ) -> bool:
        """Delete a validation rule.

        Args:
            rule_id: The rule ID

        Returns:
            bool: True if successful

        Raises:
            DatabaseError: If rule deletion fails
        """
        if not self._validation_engine:
            raise DatabaseError("Validation system not initialized")

        return await self._validation_engine.delete_rule(rule_id)

    async def get_validation_rule(
            self,
            rule_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a validation rule.

        Args:
            rule_id: The rule ID

        Returns:
            Optional[Dict[str, Any]]: The rule, or None if not found
        """
        if not self._validation_engine:
            return None

        return await self._validation_engine.get_rule(rule_id)

    async def get_all_validation_rules(
            self,
            connection_id: Optional[str] = None,
            table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all validation rules, optionally filtered.

        Args:
            connection_id: The connection ID to filter by
            table_name: The table name to filter by

        Returns:
            List[Dict[str, Any]]: List of validation rules
        """
        if not self._validation_engine:
            return []

        return await self._validation_engine.get_all_rules(connection_id, table_name)

    async def validate_data(
            self,
            connection_id: str,
            table_name: str,
            data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate data against all rules for a table.

        Args:
            connection_id: The connection ID
            table_name: The table name
            data: The data to validate

        Returns:
            List[Dict[str, Any]]: Validation results

        Raises:
            ValidationError: If validation fails
        """
        if not self._validation_engine:
            raise DatabaseError("Validation system not initialized")

        return await self._validation_engine.validate_all_rules(connection_id, table_name, data)

    async def shutdown(self) -> None:
        """Shut down the database manager.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info("Shutting down Database Manager")

            # Shut down specialized services
            if self._field_mapper:
                try:
                    await self._field_mapper.shutdown()
                except Exception as e:
                    self._logger.warning(f"Error shutting down field mapper: {str(e)}")

            if self._history_manager:
                try:
                    await self._history_manager.shutdown()
                except Exception as e:
                    self._logger.warning(f"Error shutting down history manager: {str(e)}")

            if self._validation_engine:
                try:
                    await self._validation_engine.shutdown()
                except Exception as e:
                    self._logger.warning(f"Error shutting down validation engine: {str(e)}")

            async with self._connections_lock:
                for name, connection in list(self._connections.items()):
                    async with connection.active_sessions_lock:
                        for session in list(connection.active_sessions):
                            try:
                                session.close()
                            except Exception:
                                pass
                        connection.active_sessions.clear()

                        for session in list(connection.active_async_sessions):
                            try:
                                await session.close()
                            except Exception:
                                pass
                        connection.active_async_sessions.clear()

                    # Disconnect specialized connector if present
                    if connection.connector:
                        try:
                            await connection.connector.disconnect()
                        except Exception as e:
                            self._logger.warning(
                                f"Error disconnecting specialized connector: {str(e)}"
                            )

                    if connection.engine:
                        connection.engine.dispose()

                    if connection.async_engine:
                        await connection.async_engine.dispose()

                    self._logger.debug(f"Closed database connection: {name}")

                self._connections.clear()

            await self._config_manager.unregister_listener("database", self._on_config_changed)

            self._initialized = False
            self._healthy = False

            self._logger.info("Database Manager shut down successfully")
        except Exception as e:
            self._logger.error(f"Failed to shut down Database Manager: {str(e)}")
            raise ManagerShutdownError(
                f"Failed to shut down Database Manager: {str(e)}",
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the database manager.

        Returns:
            Dict[str, Any]: Status information
        """
        status = super().status()

        if self._initialized:
            connection_statuses = {}

            for name, connection in self._connections.items():
                pool_status = {}

                if connection.engine:
                    try:
                        pool = connection.engine.pool
                        pool_status = {
                            "size": pool.size(),
                            "checkedin": pool.checkedin(),
                            "checkedout": pool.checkedout(),
                            "overflow": getattr(pool, "overflow", 0)
                        }
                    except Exception:
                        pool_status = {"error": "Failed to get pool status"}

                query_stats = {
                    "total": connection.queries_total,
                    "failed": connection.queries_failed,
                    "success_rate": (
                        (connection.queries_total - connection.queries_failed)
                        / connection.queries_total * 100
                        if connection.queries_total > 0 else 100.0
                    )
                }

                if connection.query_times:
                    avg_time = sum(connection.query_times) / len(connection.query_times)
                    max_time = max(connection.query_times)
                    query_stats.update({
                        "avg_time_ms": round(avg_time * 1000, 2),
                        "max_time_ms": round(max_time * 1000, 2),
                        "last_queries": len(connection.query_times)
                    })

                connection_ok = False
                try:
                    if connection.connector:
                        result, _ = asyncio.create_task(connection.connector.test_connection())
                        connection_ok = result
                    elif connection.engine:
                        with connection.engine.connect() as conn:
                            conn.execute(text("SELECT 1"))
                            connection_ok = True
                except Exception:
                    pass

                connection_statuses[name] = {
                    "database": {
                        "type": connection.config.db_type,
                        "connection_ok": connection_ok,
                        "async_supported": (
                                connection.async_engine is not None
                                or connection.connector is not None
                        ),
                        "specialized_connector": connection.connector is not None
                    },
                    "pool": pool_status,
                    "sessions": {
                        "active_sync": len(connection.active_sessions),
                        "active_async": len(connection.active_async_sessions)
                    },
                    "queries": query_stats,
                    "features": {
                        "mapping_enabled": connection.config.mapping_enabled,
                        "history_enabled": connection.config.history_enabled,
                        "validation_enabled": connection.config.validation_enabled
                    }
                }

            # Add status for advanced features
            feature_status = {
                "field_mapping": self._field_mapper is not None,
                "history_tracking": self._history_manager is not None,
                "validation": self._validation_engine is not None
            }

            status.update({
                "connections": connection_statuses,
                "default_connection": "default",
                "features": feature_status,
                "supported_connector_types": list(self._connector_registry.keys())
            })

        return status