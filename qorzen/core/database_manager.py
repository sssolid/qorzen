from __future__ import annotations

import contextlib
import functools
import threading
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, TypeVar, Union, cast

import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import DatabaseError, ManagerInitializationError, ManagerShutdownError

T = TypeVar('T')
R = TypeVar('R')


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


class DatabaseConnectionConfig:
    """Configuration for a database connection."""

    def __init__(
            self,
            name: str,
            db_type: str,
            host: str,
            port: int,
            database: str,
            user: str,
            password: str,
            pool_size: int = 5,
            max_overflow: int = 10,
            pool_recycle: int = 3600,
            echo: bool = False
    ) -> None:
        """Initialize database connection configuration.

        Args:
            name: The name of the connection
            db_type: The database type (postgresql, mysql, sqlite, etc.)
            host: The database host
            port: The database port
            database: The database name
            user: The database user
            password: The database password
            pool_size: The connection pool size
            max_overflow: The maximum overflow connections
            pool_recycle: The connection recycle time in seconds
            echo: Whether to echo SQL statements
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


class DatabaseConnection:
    """A database connection instance."""

    def __init__(self, config: DatabaseConnectionConfig) -> None:
        """Initialize a database connection.

        Args:
            config: The connection configuration
        """
        self.config = config
        self.engine: Optional[Engine] = None
        self.async_engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.async_session_factory: Optional[sessionmaker] = None
        self.initialized = False
        self.healthy = False
        self.active_sessions: Set[Session] = set()
        self.active_sessions_lock = threading.RLock()
        self.queries_total = 0
        self.queries_failed = 0
        self.query_times: List[float] = []
        self.metrics_lock = threading.RLock()


class DatabaseManager(QorzenManager):
    """Manager for database connections and operations."""

    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        """Initialize the database manager.

        Args:
            config_manager: The configuration manager
            logger_manager: The logger manager
        """
        super().__init__(name='DatabaseManager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('database_manager')

        self._default_connection: Optional[DatabaseConnection] = None
        self._connections: Dict[str, DatabaseConnection] = {}
        self._connections_lock = threading.RLock()

        self._db_type: str = 'postgresql'
        self._db_url: Optional[str] = None
        self._db_async_url: Optional[str] = None
        self._pool_size: int = 5
        self._max_overflow: int = 10
        self._pool_recycle: int = 3600
        self._echo: bool = False

    def initialize(self) -> None:
        """Initialize the database manager."""
        try:
            db_config = self._config_manager.get('database', {})

            # Configure the default connection
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

            # Create and initialize the default connection
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

            with self._connections_lock:
                self._default_connection = DatabaseConnection(default_config)
                self._connections['default'] = self._default_connection
                self._init_connection(self._default_connection)

            self._config_manager.register_listener('database', self._on_config_changed)

            self._logger.info(
                f'Database Manager initialized with {self._db_type} database',
                extra={'host': host, 'port': port, 'database': name}
            )

            self._initialized = True
            self._healthy = True

        except Exception as e:
            self._logger.error(f'Failed to initialize Database Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize DatabaseManager: {str(e)}',
                manager_name=self.name
            ) from e

    def _init_connection(self, connection: DatabaseConnection) -> None:
        """Initialize a database connection.

        Args:
            connection: The connection to initialize

        Raises:
            DatabaseError: If there's an error initializing the connection
        """
        config = connection.config

        # Build the connection URLs
        if config.db_type == 'sqlite':
            db_url = f'sqlite:///{config.database}'
            db_async_url = f'sqlite+aiosqlite:///{config.database}'
        else:
            db_url = URL.create(
                config.db_type,
                username=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database
            )

            if config.db_type == 'postgresql':
                db_async_url = URL.create(
                    'postgresql+asyncpg',
                    username=config.user,
                    password=config.password,
                    host=config.host,
                    port=config.port,
                    database=config.database
                )
            else:
                db_async_url = None

        # Create the engine
        connection.engine = create_engine(
            db_url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_recycle=config.pool_recycle,
            echo=config.echo
        )

        # Create async engine if supported
        if db_async_url:
            connection.async_engine = create_async_engine(
                db_async_url,
                echo=config.echo,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_recycle=config.pool_recycle
            )

        # Create session factories
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

        # Add event listeners for metrics
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

    def register_connection(self, config: DatabaseConnectionConfig) -> None:
        """Register a new database connection.

        Args:
            config: The connection configuration

        Raises:
            DatabaseError: If there's an error registering the connection
        """
        if not self._initialized:
            raise DatabaseError('Database Manager not initialized')

        with self._connections_lock:
            if config.name in self._connections:
                raise DatabaseError(f'Connection with name {config.name} already exists')

            connection = DatabaseConnection(config)
            try:
                self._init_connection(connection)
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

    def unregister_connection(self, name: str) -> bool:
        """Unregister a database connection.

        Args:
            name: The name of the connection to unregister

        Returns:
            True if the connection was unregistered, False otherwise

        Raises:
            DatabaseError: If attempting to unregister the default connection
        """
        if not self._initialized:
            return False

        if name == 'default':
            raise DatabaseError('Cannot unregister the default connection')

        with self._connections_lock:
            if name not in self._connections:
                return False

            connection = self._connections[name]

            # Close all active sessions
            with connection.active_sessions_lock:
                for session in list(connection.active_sessions):
                    try:
                        session.close()
                    except Exception:
                        pass
                connection.active_sessions.clear()

            # Dispose the engines
            if connection.engine:
                connection.engine.dispose()

            # Remove the connection
            del self._connections[name]

            self._logger.info(f'Unregistered database connection: {name}')
            return True

    def _get_connection(self, connection_name: Optional[str] = None) -> DatabaseConnection:
        """Get a database connection.

        Args:
            connection_name: The name of the connection to get, or None for the default

        Returns:
            The database connection

        Raises:
            DatabaseError: If the connection doesn't exist or is not initialized
        """
        if not self._initialized:
            raise DatabaseError('Database Manager not initialized')

        name = connection_name or 'default'

        with self._connections_lock:
            if name not in self._connections:
                raise DatabaseError(f'Database connection {name} not found')

            connection = self._connections[name]

            if not connection.initialized:
                raise DatabaseError(f'Database connection {name} not initialized')

            return connection

    def _get_default_port(self, db_type: str) -> int:
        """Get the default port for a database type.

        Args:
            db_type: The database type

        Returns:
            The default port
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

    @contextlib.contextmanager
    def session(self, connection_name: Optional[str] = None) -> Generator[Session, None, None]:
        """Get a database session.

        Args:
            connection_name: The name of the connection to use, or None for the default

        Yields:
            A SQLAlchemy session

        Raises:
            DatabaseError: If there's an error getting the session
        """
        connection = self._get_connection(connection_name)

        if not connection.session_factory:
            raise DatabaseError(f'Session factory not initialized for connection {connection.config.name}')

        session = connection.session_factory()

        with connection.active_sessions_lock:
            connection.active_sessions.add(session)

        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}') from e
        except Exception as e:
            session.rollback()
            with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Error during database operation: {str(e)}')
            raise
        finally:
            session.close()
            with connection.active_sessions_lock:
                connection.active_sessions.discard(session)

    async def async_session(self, connection_name: Optional[str] = None) -> AsyncSession:
        """Get an async database session.

        Args:
            connection_name: The name of the connection to use, or None for the default

        Returns:
            An async SQLAlchemy session

        Raises:
            DatabaseError: If there's an error getting the session
        """
        connection = self._get_connection(connection_name)

        if not connection.async_session_factory:
            raise DatabaseError(f'Async session factory not initialized for connection {connection.config.name}')

        return connection.async_session_factory()

    def execute(
            self,
            statement: Any,
            connection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a database statement.

        Args:
            statement: The statement to execute
            connection_name: The name of the connection to use, or None for the default

        Returns:
            A list of result rows as dictionaries

        Raises:
            DatabaseError: If there's an error executing the statement
        """
        connection = self._get_connection(connection_name)

        if not connection.engine:
            raise DatabaseError(f'Engine not initialized for connection {connection.config.name}')

        try:
            with connection.engine.connect() as conn:
                result = conn.execute(statement)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}') from e

    def execute_raw(
            self,
            sql: str,
            params: Optional[Dict[str, Any]] = None,
            connection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL statement.

        Args:
            sql: The SQL statement to execute
            params: Parameters for the statement
            connection_name: The name of the connection to use, or None for the default

        Returns:
            A list of result rows as dictionaries

        Raises:
            DatabaseError: If there's an error executing the statement
        """
        connection = self._get_connection(connection_name)

        if not connection.engine:
            raise DatabaseError(f'Engine not initialized for connection {connection.config.name}')

        try:
            with connection.engine.connect() as conn:
                result = conn.execute(sqlalchemy.text(sql), params or {})
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}', query=sql) from e

    async def execute_async(
            self,
            statement: Any,
            connection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a database statement asynchronously.

        Args:
            statement: The statement to execute
            connection_name: The name of the connection to use, or None for the default

        Returns:
            A list of result rows as dictionaries

        Raises:
            DatabaseError: If there's an error executing the statement
        """
        connection = self._get_connection(connection_name)

        if not connection.async_engine:
            raise DatabaseError(f'Async engine not initialized for connection {connection.config.name}')

        try:
            async with connection.async_engine.connect() as conn:
                result = await conn.execute(statement)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Database error: {str(e)}')
            raise DatabaseError(f'Database error: {str(e)}') from e
        except Exception as e:
            with connection.metrics_lock:
                connection.queries_failed += 1
            self._logger.error(f'Error during async database operation: {str(e)}')
            raise

    def create_tables(self, connection_name: Optional[str] = None) -> None:
        """Create database tables for the Base metadata.

        Args:
            connection_name: The name of the connection to use, or None for the default

        Raises:
            DatabaseError: If there's an error creating the tables
        """
        connection = self._get_connection(connection_name)

        if not connection.engine:
            raise DatabaseError(f'Engine not initialized for connection {connection.config.name}')

        try:
            Base.metadata.create_all(connection.engine)
            self._logger.info(f'Created database tables for connection {connection.config.name}')
        except SQLAlchemyError as e:
            self._logger.error(f'Failed to create tables: {str(e)}')
            raise DatabaseError(f'Failed to create tables: {str(e)}') from e

    async def create_tables_async(self, connection_name: Optional[str] = None) -> None:
        """Create database tables for the Base metadata asynchronously.

        Args:
            connection_name: The name of the connection to use, or None for the default

        Raises:
            DatabaseError: If there's an error creating the tables
        """
        connection = self._get_connection(connection_name)

        if not connection.async_engine:
            raise DatabaseError(f'Async engine not initialized for connection {connection.config.name}')

        try:
            async with connection.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._logger.info(f'Created database tables asynchronously for connection {connection.config.name}')
        except SQLAlchemyError as e:
            self._logger.error(f'Failed to create tables asynchronously: {str(e)}')
            raise DatabaseError(f'Failed to create tables asynchronously: {str(e)}') from e

    def check_connection(self, connection_name: Optional[str] = None) -> bool:
        """Check if a database connection is healthy.

        Args:
            connection_name: The name of the connection to check, or None for the default

        Returns:
            True if the connection is healthy, False otherwise
        """
        try:
            connection = self._get_connection(connection_name)

            if not connection.engine:
                return False

            with connection.engine.connect() as conn:
                conn.execute(sqlalchemy.text('SELECT 1'))

            return True
        except (DatabaseError, SQLAlchemyError):
            return False

    def get_engine(self, connection_name: Optional[str] = None) -> Optional[Engine]:
        """Get the database engine for a connection.

        Args:
            connection_name: The name of the connection, or None for the default

        Returns:
            The database engine, or None if not available
        """
        try:
            connection = self._get_connection(connection_name)
            return connection.engine
        except DatabaseError:
            return None

    def get_async_engine(self, connection_name: Optional[str] = None) -> Optional[AsyncEngine]:
        """Get the async database engine for a connection.

        Args:
            connection_name: The name of the connection, or None for the default

        Returns:
            The async database engine, or None if not available
        """
        try:
            connection = self._get_connection(connection_name)
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

        Args:
            conn: The connection
            cursor: The cursor
            statement: The SQL statement
            parameters: The parameters
            context: The context
            executemany: Whether this is an executemany operation
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
        """Event handler for after cursor execute.

        Args:
            conn: The connection
            cursor: The cursor
            statement: The SQL statement
            parameters: The parameters
            context: The context
            executemany: Whether this is an executemany operation
            connection: The database connection
        """
        query_time = time.time() - context._query_start_time

        with connection.metrics_lock:
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

    def _on_config_changed(self, key: str, value: Any) -> None:
        """Event handler for configuration changes.

        Args:
            key: The configuration key
            value: The new value
        """
        if key.startswith('database.'):
            self._logger.warning(
                f'Configuration change to {key} requires restart to take effect',
                extra={'key': key}
            )

    def shutdown(self) -> None:
        """Shut down the database manager."""
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Database Manager')

            # Close all connections
            with self._connections_lock:
                for name, connection in list(self._connections.items()):
                    # Close all active sessions
                    with connection.active_sessions_lock:
                        for session in list(connection.active_sessions):
                            try:
                                session.close()
                            except Exception:
                                pass
                        connection.active_sessions.clear()

                    # Dispose the engines
                    if connection.engine:
                        connection.engine.dispose()

                    self._logger.debug(f'Closed database connection: {name}')

                self._connections.clear()

            self._config_manager.unregister_listener('database', self._on_config_changed)

            self._initialized = False
            self._healthy = False

            self._logger.info('Database Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Database Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down DatabaseManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the database manager.

        Returns:
            A dictionary with status information
        """
        status = super().status()

        if self._initialized:
            connection_statuses = {}

            with self._connections_lock:
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

                    with connection.metrics_lock:
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

                    connection_ok = self.check_connection(name)

                    connection_statuses[name] = {
                        'database': {
                            'type': connection.config.db_type,
                            'connection_ok': connection_ok,
                            'async_supported': connection.async_engine is not None
                        },
                        'pool': pool_status,
                        'sessions': {
                            'active': len(connection.active_sessions)
                        },
                        'queries': query_stats
                    }

            status.update({
                'connections': connection_statuses,
                'default_connection': 'default'
            })

        return status