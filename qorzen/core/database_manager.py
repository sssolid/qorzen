from __future__ import annotations

import asyncio
import functools
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set, TypeVar, Union, cast, Callable, Awaitable, AsyncGenerator

import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import DatabaseError, ManagerInitializationError, ManagerShutdownError, \
    DatabaseManagerInitializationError

T = TypeVar('T')
R = TypeVar('R')


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models.

    This provides a common metadata instance with naming conventions for all models.
    """
    metadata = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'
    })


class DatabaseConnectionConfig:
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
            properties: Optional[Dict[str, Any]] = None,
            read_only: bool = False,
            ssl: bool = False,
            allowed_tables: Optional[List[str]] = None,
            dsn: Optional[str] = None,
            jt400_jar_path: Optional[str] = None,
    ) -> None:
        """Initialize a database connection configuration.

        Args:
            name: Unique name for the connection
            db_type: Type of database (postgresql, mysql, sqlite, odbc, etc.)
            host: Database server hostname or IP
            port: Database server port
            database: Database name or path
            user: Database username
            password: Database password
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to overflow
            pool_recycle: Seconds before connections are recycled
            echo: Whether to echo SQL statements
            connection_string: Full connection string (alternative to individual parameters)
            url: SQLAlchemy URL object (alternative to connection_string)
            properties: Additional connection properties
            read_only: Whether this connection is read-only
            ssl: Whether to use SSL for connection
            allowed_tables: List of allowed tables (for security restrictions)
            dsn: ODBC data source name
            jt400_jar_path: Path to JT400 JAR file for AS400 connections
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
        self.properties = properties or {}
        self.read_only = read_only
        self.ssl = ssl
        self.allowed_tables = allowed_tables
        self.dsn = dsn
        self.jt400_jar_path = jt400_jar_path


class DatabaseConnection:
    """Database connection manager.

    This class manages both synchronous and asynchronous connections
    to a database and provides session factories.

    Attributes:
        config: Connection configuration
        engine: Synchronous SQLAlchemy engine
        async_engine: Asynchronous SQLAlchemy engine
        session_factory: Factory for creating synchronous sessions
        async_session_factory: Factory for creating asynchronous sessions
        initialized: Whether the connection is initialized
        healthy: Whether the connection is healthy
        active_sessions: Set of active synchronous sessions
        active_async_sessions: Set of active asynchronous sessions
    """

    def __init__(self, config: DatabaseConnectionConfig) -> None:
        """Initialize a database connection.

        Args:
            config: Connection configuration
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


class DatabaseManager(QorzenManager):
    """Asynchronous database manager.

    This manager provides access to database connections and sessions,
    supporting both synchronous and asynchronous operations.

    Attributes:
        _config_manager: Configuration manager
        _logger: Logger instance
        _default_connection: Default database connection
        _connections: Dictionary of database connections
    """

    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        """Initialize the database manager.

        Args:
            config_manager: Configuration manager
            logger_manager: Logging manager
        """
        super().__init__(name='database_manager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('database_manager')
        self._default_connection: Optional[DatabaseConnection] = None
        self._connections: Dict[str, DatabaseConnection] = {}
        self._connections_lock = asyncio.Lock()
        self._db_type: str = 'postgresql'
        self._db_url: Optional[str] = None
        self._db_async_url: Optional[str] = None
        self._pool_size: int = 5
        self._max_overflow: int = 10
        self._pool_recycle: int = 3600
        self._echo: bool = False

    async def initialize(self) -> None:
        """Initialize the database manager asynchronously.

        Sets up database connections based on configuration.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            db_config = await self._config_manager.get('database', {})

            # Get database configuration
            self._db_type = db_config.get('type', 'postgresql').lower()
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', self._get_default_port(self._db_type))
            name = db_config.get('name', 'qorzen')
            user = db_config.get('user', '')
            password = db_config.get('password', '')
            self._pool_size = db_config.get('pool_size', 5)
            self._max_overflow = db_config.get('max_overflow', 10)
            self._pool_recycle = db_config.get('pool_recycle', 3600)
            self._echo = db_config.get('echo', False)

            # Create default connection config
            default_config = DatabaseConnectionConfig(
                name='default',
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

            # Initialize the default connection
            async with self._connections_lock:
                self._default_connection = DatabaseConnection(default_config)
                self._connections['default'] = self._default_connection
                await self._init_connection(self._default_connection)

            # Register configuration listener
            await self._config_manager.register_listener('database', self._on_config_changed)

            self._logger.info(
                f'Database Manager initialized with {self._db_type} database',
                extra={'host': host, 'port': port, 'database': name}
            )

            self._initialized = True
            self._healthy = True

        except Exception as e:
            self._logger.error(f'Failed to initialize Database Manager: {str(e)}')
            raise DatabaseManagerInitializationError(
                f'Failed to initialize AsyncDatabaseManager: {str(e)}',
                manager_name=self.name
            ) from e

    async def _init_connection(self, connection: DatabaseConnection) -> None:
        config = connection.config

        # Handle connection through URL or connection string first
        if config.url:
            db_url = config.url
            db_async_url = None  # Will be determined later if possible
        elif config.connection_string:
            # For database types using direct connection strings (ODBC, etc.)
            db_url = config.connection_string
            db_async_url = None
        elif config.db_type == 'sqlite':
            db_url = f'sqlite:///{config.database}'
            db_async_url = f'sqlite+aiosqlite:///{config.database}'
        elif config.db_type == 'odbc':
            # Construct ODBC connection string if not provided directly
            if not config.connection_string:
                conn_str = f'DRIVER={{ODBC}};'
                if config.dsn:
                    conn_str += f'DSN={config.dsn};'
                if config.host:
                    conn_str += f'SERVER={config.host};'
                if config.port:
                    conn_str += f'PORT={config.port};'
                if config.database:
                    conn_str += f'DATABASE={config.database};'
                if config.user:
                    conn_str += f'UID={config.user};'
                if config.password:
                    conn_str += f'PWD={config.password};'
                db_url = f'odbc://{conn_str}'
            else:
                db_url = f'odbc://{config.connection_string}'
            db_async_url = None
        elif config.db_type == 'jdbc':
            # For JDBC connections (like AS400)
            if not config.connection_string:
                # Construct a JDBC URL if not provided
                db_url = f'jdbc:{config.db_type}://{config.host}'
                if config.port:
                    db_url += f':{config.port}'
                if config.database:
                    db_url += f'/{config.database}'
            else:
                db_url = config.connection_string
            db_async_url = None
        else:
            # For standard SQL databases, create URL from components
            db_url = URL.create(
                config.db_type,
                username=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database
            )

            # Set up async URL for supported database types
            if config.db_type == 'postgresql':
                db_async_url = URL.create(
                    'postgresql+asyncpg',
                    username=config.user,
                    password=config.password,
                    host=config.host,
                    port=config.port,
                    database=config.database
                )
            elif config.db_type == 'mysql':
                db_async_url = URL.create(
                    'mysql+aiomysql',
                    username=config.user,
                    password=config.password,
                    host=config.host,
                    port=config.port,
                    database=config.database
                )
            else:
                db_async_url = None

        # Create engine with additional properties if provided
        engine_args = {
            'pool_size': config.pool_size,
            'max_overflow': config.max_overflow,
            'pool_recycle': config.pool_recycle,
            'echo': config.echo
        }

        # Add SSL settings if specified
        if config.ssl:
            engine_args['connect_args'] = engine_args.get('connect_args', {})
            engine_args['connect_args']['ssl'] = True

        # Add any additional properties from the config
        if config.properties:
            for key, value in config.properties.items():
                if key == 'connect_args':
                    engine_args['connect_args'] = engine_args.get('connect_args', {})
                    if isinstance(value, dict):
                        engine_args['connect_args'].update(value)
                else:
                    engine_args[key] = value

        # Create the engines
        connection.engine = create_engine(db_url, **engine_args)

        if db_async_url:
            connection.async_engine = create_async_engine(
                db_async_url,
                echo=config.echo,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_recycle=config.pool_recycle
            )

        # Set up session factories
        connection.session_factory = sessionmaker(bind=connection.engine, expire_on_commit=False)

        if connection.async_engine:
            connection.async_session_factory = sessionmaker(
                bind=connection.async_engine,
                expire_on_commit=False,
                class_=AsyncSession
            )

        # Set up event listeners
        event.listen(
            connection.engine,
            'before_cursor_execute',
            functools.partial(self._before_cursor_execute, connection=connection)
        )
        event.listen(
            connection.engine,
            'after_cursor_execute',
            functools.partial(self._after_cursor_execute, connection=connection)
        )

        # Test the connection
        with connection.engine.connect() as conn:
            conn.execute(sqlalchemy.text('SELECT 1'))

        connection.initialized = True
        connection.healthy = True

    async def register_connection(self, config: DatabaseConnectionConfig) -> None:
        """Register a new database connection.

        Args:
            config: Connection configuration

        Raises:
            DatabaseError: If registration fails
        """
        if not self._initialized:
            raise DatabaseError('Database Manager not initialized')

        async with self._connections_lock:
            if config.name in self._connections:
                raise DatabaseError(f'Connection with name {config.name} already exists')

            connection = DatabaseConnection(config)
            try:
                await self._init_connection(connection)
                self._connections[config.name] = connection
                self._logger.info(
                    f'Registered new database connection: {config.name}',
                    extra={
                        'connection': config.name,
                        'type': config.db_type,
                        'host': config.host,
                        'database': config.database
                    }
                )
            except Exception as e:
                self._logger.error(
                    f'Failed to register database connection {config.name}: {str(e)}',
                    extra={'connection': config.name}
                )
                raise DatabaseError(
                    f'Failed to register database connection {config.name}: {str(e)}'
                ) from e

    async def unregister_connection(self, name: str) -> bool:
        """Unregister a database connection.

        Args:
            name: Name of the connection to unregister

        Returns:
            True if the connection was unregistered, False otherwise

        Raises:
            DatabaseError: If unregistration fails
        """
        if not self._initialized:
            return False

        if name == 'default':
            raise DatabaseError('Cannot unregister the default connection')

        async with self._connections_lock:
            if name not in self._connections:
                return False

            connection = self._connections[name]

            # Close active sessions
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

            # Dispose engines
            if connection.engine:
                connection.engine.dispose()

            if connection.async_engine:
                await connection.async_engine.dispose()

            del self._connections[name]

            self._logger.info(f'Unregistered database connection: {name}')
            return True

    async def has_connection(self, name: str) -> bool:
        """Check if a connection exists.

        Args:
            name: Name of the connection

        Returns:
            True if the connection exists, False otherwise
        """
        async with self._connections_lock:
            return name in self._connections

    async def get_connection_names(self) -> List[str]:
        """Get the names of all connections.

        Returns:
            List of connection names
        """
        async with self._connections_lock:
            return list(self._connections.keys())

    async def _get_connection(self, connection_name: Optional[str] = None) -> DatabaseConnection:
        """Get a database connection.

        Args:
            connection_name: Name of the connection, or None for default

        Returns:
            The database connection

        Raises:
            DatabaseError: If the connection is not found or not initialized
        """
        if not self._initialized:
            raise DatabaseError('Database Manager not initialized')

        name = connection_name or 'default'

        async with self._connections_lock:
            if name not in self._connections:
                raise DatabaseError(f'Database connection {name} not found')

            connection = self._connections[name]
            if not connection.initialized:
                raise DatabaseError(f'Database connection {name} not initialized')

            return connection

    def _get_default_port(self, db_type: str) -> int:
        """Get the default port for a database type.

        Args:
            db_type: Database type

        Returns:
            Default port for the database type
        """
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'mariadb': 3306,
            'oracle': 1521,
            'mssql': 1433,
            'sqlite': 0
        }
        return default_ports.get(db_type, 0)

    @asynccontextmanager
    async def session(
            self,
            connection_name: Optional[str] = None
    ) -> AsyncGenerator[Session, None]:
        """Get a synchronous session for a connection.

        Args:
            connection_name: Name of the connection, or None for default

        Yields:
            A SQLAlchemy session

        Raises:
            DatabaseError: If the session cannot be created
        """
        connection = await self._get_connection(connection_name)

        if not connection.session_factory:
            raise DatabaseError(
                f'Session factory not initialized for connection {connection.config.name}'
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
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}') from e
        except Exception as e:
            session.rollback()
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Error during database operation: {str(e)}')
            raise
        finally:
            session.close()
            async with connection.active_sessions_lock:
                connection.active_sessions.discard(session)

    @asynccontextmanager
    async def async_session(
            self,
            connection_name: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous session for a connection.

        Args:
            connection_name: Name of the connection, or None for default

        Yields:
            A SQLAlchemy async session

        Raises:
            DatabaseError: If the session cannot be created
        """
        connection = await self._get_connection(connection_name)

        if not connection.async_session_factory:
            raise DatabaseError(
                f'Async session factory not initialized for connection {connection.config.name}'
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
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}') from e
        except Exception as e:
            await session.rollback()
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Error during database operation: {str(e)}')
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
        """Execute a SQLAlchemy statement synchronously.

        Args:
            statement: SQLAlchemy statement to execute
            connection_name: Name of the connection, or None for default

        Returns:
            List of result rows as dictionaries

        Raises:
            DatabaseError: If execution fails
        """
        connection = await self._get_connection(connection_name)

        if not connection.engine:
            raise DatabaseError(
                f'Engine not initialized for connection {connection.config.name}'
            )

        try:
            with connection.engine.connect() as conn:
                result = conn.execute(statement)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}') from e

    async def execute_raw(
            self,
            sql: str,
            params: Optional[Dict[str, Any]] = None,
            connection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL statement synchronously.

        Args:
            sql: SQL statement to execute
            params: Parameters for the statement
            connection_name: Name of the connection, or None for default

        Returns:
            List of result rows as dictionaries

        Raises:
            DatabaseError: If execution fails
        """
        connection = await self._get_connection(connection_name)

        if not connection.engine:
            raise DatabaseError(
                f'Engine not initialized for connection {connection.config.name}'
            )

        try:
            with connection.engine.connect() as conn:
                result = conn.execute(sqlalchemy.text(sql), params or {})
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}', query=sql) from e

    async def execute_async(
            self,
            statement: Any,
            connection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a SQLAlchemy statement asynchronously.

        Args:
            statement: SQLAlchemy statement to execute
            connection_name: Name of the connection, or None for default

        Returns:
            List of result rows as dictionaries

        Raises:
            DatabaseError: If execution fails
        """
        connection = await self._get_connection(connection_name)

        if not connection.async_engine:
            raise DatabaseError(
                f'Async engine not initialized for connection {connection.config.name}'
            )

        try:
            async with connection.async_engine.connect() as conn:
                result = await conn.execute(statement)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}') from e
        except Exception as e:
            async with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Error during async database operation: {str(e)}')
            raise

    async def create_tables(self, connection_name: Optional[str] = None) -> None:
        """Create all tables for a connection synchronously.

        Args:
            connection_name: Name of the connection, or None for default

        Raises:
            DatabaseError: If table creation fails
        """
        connection = await self._get_connection(connection_name)

        if not connection.engine:
            raise DatabaseError(
                f'Engine not initialized for connection {connection.config.name}'
            )

        try:
            Base.metadata.create_all(connection.engine)
            self._logger.info(f'Created database tables for connection {connection.config.name}')
        except SQLAlchemyError as e:
            self._logger.error(f'Failed to create tables: {str(e)}')
            raise DatabaseError(f'Failed to create tables: {str(e)}') from e

    async def create_tables_async(self, connection_name: Optional[str] = None) -> None:
        """Create all tables for a connection asynchronously.

        Args:
            connection_name: Name of the connection, or None for default

        Raises:
            DatabaseError: If table creation fails
        """
        connection = await self._get_connection(connection_name)

        if not connection.async_engine:
            raise DatabaseError(
                f'Async engine not initialized for connection {connection.config.name}'
            )

        try:
            async with connection.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._logger.info(f'Created database tables asynchronously for connection {connection.config.name}')
        except SQLAlchemyError as e:
            self._logger.error(f'Failed to create tables asynchronously: {str(e)}')
            raise DatabaseError(f'Failed to create tables asynchronously: {str(e)}') from e

    async def check_connection(self, connection_name: Optional[str] = None) -> bool:
        """Check if a connection is working.

        Args:
            connection_name: Name of the connection, or None for default

        Returns:
            True if the connection is working, False otherwise
        """
        try:
            connection = await self._get_connection(connection_name)

            if not connection.engine:
                return False

            with connection.engine.connect() as conn:
                conn.execute(sqlalchemy.text('SELECT 1'))

            return True
        except (DatabaseError, SQLAlchemyError):
            return False

    async def get_engine(self, connection_name: Optional[str] = None) -> Optional[Engine]:
        """Get the synchronous engine for a connection.

        Args:
            connection_name: Name of the connection, or None for default

        Returns:
            The SQLAlchemy engine, or None if not available
        """
        try:
            connection = await self._get_connection(connection_name)
            return connection.engine
        except DatabaseError:
            return None

    async def get_async_engine(self, connection_name: Optional[str] = None) -> Optional[AsyncEngine]:
        """Get the asynchronous engine for a connection.

        Args:
            connection_name: Name of the connection, or None for default

        Returns:
            The SQLAlchemy async engine, or None if not available
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
        """Event handler for before cursor execute.

        Records the start time of a query for metrics.

        Args:
            conn: Connection
            cursor: Cursor
            statement: SQL statement
            parameters: Statement parameters
            context: Context object
            executemany: Whether this is an executemany call
            connection: Database connection
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
        """Event handler for after cursor execute.

        Records query metrics.

        Args:
            conn: Connection
            cursor: Cursor
            statement: SQL statement
            parameters: Statement parameters
            context: Context object
            executemany: Whether this is an executemany call
            connection: Database connection
        """
        query_time = time.time() - context._query_start_time

        # We need to use run_coroutine_threadsafe here since this is called from a sync context
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
        """Update query metrics asynchronously.

        Args:
            connection: Database connection
            query_time: Query execution time
            statement: SQL statement
        """
        async with connection.metrics_lock:
            connection.queries_total += 1
            connection.query_times.append(query_time)

            if len(connection.query_times) > 100:
                connection.query_times.pop(0)

            if query_time > 1.0:
                self._logger.warning(
                    f'Slow query: {query_time:.3f}s',
                    extra={
                        'query_time': query_time,
                        'statement': statement[:1000],
                        'connection': connection.config.name
                    }
                )

    async def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: Configuration key
            value: New value
        """
        if key.startswith('database.'):
            self._logger.warning(
                f'Configuration change to {key} requires restart to take effect',
                extra={'key': key}
            )

    async def shutdown(self) -> None:
        """Shut down the database manager asynchronously.

        Closes all connections and releases resources.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Database Manager')

            async with self._connections_lock:
                for name, connection in list(self._connections.items()):
                    # Close active sessions
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

                    # Dispose engines
                    if connection.engine:
                        connection.engine.dispose()

                    if connection.async_engine:
                        await connection.async_engine.dispose()

                    self._logger.debug(f'Closed database connection: {name}')

                self._connections.clear()

            # Unregister config listener
            await self._config_manager.unregister_listener('database', self._on_config_changed)

            self._initialized = False
            self._healthy = False

            self._logger.info('Database Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Database Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down AsyncDatabaseManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the database manager.

        Returns:
            Dictionary with status information
        """
        status = super().status()

        if self._initialized:
            # Get sync connection status info
            connection_statuses = {}

            for name, connection in self._connections.items():
                pool_status = {}

                if connection.engine:
                    try:
                        pool = connection.engine.pool
                        pool_status = {
                            'size': pool.size(),
                            'checkedin': pool.checkedin(),
                            'checkedout': pool.checkedout(),
                            'overflow': getattr(pool, 'overflow', 0)
                        }
                    except Exception:
                        pool_status = {'error': 'Failed to get pool status'}

                query_stats = {
                    'total': connection.queries_total,
                    'failed': connection.queries_failed,
                    'success_rate': (
                        (connection.queries_total - connection.queries_failed)
                        / connection.queries_total * 100
                        if connection.queries_total > 0 else 100.0
                    )
                }

                if connection.query_times:
                    avg_time = sum(connection.query_times) / len(connection.query_times)
                    max_time = max(connection.query_times)
                    query_stats.update({
                        'avg_time_ms': round(avg_time * 1000, 2),
                        'max_time_ms': round(max_time * 1000, 2),
                        'last_queries': len(connection.query_times)
                    })

                # We'll use a sync version of check_connection for status
                # This is safe because it's only for status reporting
                connection_ok = False
                try:
                    if connection.engine:
                        with connection.engine.connect() as conn:
                            conn.execute(sqlalchemy.text('SELECT 1'))
                            connection_ok = True
                except Exception:
                    pass

                connection_statuses[name] = {
                    'database': {
                        'type': connection.config.db_type,
                        'connection_ok': connection_ok,
                        'async_supported': connection.async_engine is not None
                    },
                    'pool': pool_status,
                    'sessions': {
                        'active_sync': len(connection.active_sessions),
                        'active_async': len(connection.active_async_sessions)
                    },
                    'queries': query_stats
                }

            status.update({
                'connections': connection_statuses,
                'default_connection': 'default'
            })

        return status