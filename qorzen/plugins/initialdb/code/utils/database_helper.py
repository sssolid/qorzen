from __future__ import annotations

"""
Database helper module for managing database connections in a Qt application.

This module provides a robust approach to handling SQLAlchemy async operations
within a PyQt application, properly managing event loops and thread safety.
"""

import asyncio
import functools
import threading
import uuid
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, Protocol, TypeVar, cast
import structlog
from PySide6.QtCore import QObject, QTimer, Signal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from .async_manager import AsyncManager, async_operation

T = TypeVar('T')
R = TypeVar('R')

logger = structlog.get_logger(__name__)


class DatabaseOperationStatus(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class DatabaseOperation(Generic[T]):
    def __init__(self, operation_id: str, name: str) -> None:
        self.operation_id = operation_id
        self.name = name
        self.status = DatabaseOperationStatus.PENDING
        self.result: Optional[T] = None
        self.error: Optional[Exception] = None
        self._created_at = asyncio.get_event_loop().time() if asyncio.get_event_loop_policy().get_event_loop().is_running() else 0
        self._updated_at = self._created_at
        self._completed_at: Optional[float] = None

    def __str__(self) -> str:
        duration = None
        if self._completed_at:
            duration = round(self._completed_at - self._created_at, 2)
        return f'DatabaseOperation(id={self.operation_id}, name={self.name}, status={self.status}, duration={duration}s)'

    def mark_running(self) -> None:
        self.status = DatabaseOperationStatus.RUNNING
        try:
            self._updated_at = asyncio.get_event_loop().time()
        except RuntimeError:
            pass

    def mark_completed(self, result: T) -> None:
        self.status = DatabaseOperationStatus.COMPLETED
        self.result = result
        try:
            now = asyncio.get_event_loop().time()
            self._updated_at = now
            self._completed_at = now
        except RuntimeError:
            pass

    def mark_failed(self, error: Exception) -> None:
        self.status = DatabaseOperationStatus.FAILED
        self.error = error
        try:
            now = asyncio.get_event_loop().time()
            self._updated_at = now
            self._completed_at = now
        except RuntimeError:
            pass

    def mark_cancelled(self) -> None:
        self.status = DatabaseOperationStatus.CANCELLED
        try:
            now = asyncio.get_event_loop().time()
            self._updated_at = now
            self._completed_at = now
        except RuntimeError:
            pass


class ConnectionConfigProvider(Protocol):
    @property
    def connection_string(self) -> str:
        ...


class DatabaseHelperSignals(QObject):
    operation_completed = Signal(object)
    operation_failed = Signal(object, Exception)
    test_connection_completed = Signal(bool)
    test_connection_failed = Signal(str)


class DatabaseHelper:
    def __init__(self, connection_string: str) -> None:
        logger.debug('Initializing DatabaseHelper')
        self._connection_string = connection_string
        self._engine: Optional[AsyncEngine] = None
        self._async_session_factory: Optional[sessionmaker] = None
        self._operations: Dict[str, DatabaseOperation] = {}
        self._lock = threading.RLock()
        self.signals = DatabaseHelperSignals()
        self._async_manager = AsyncManager.instance()
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        try:
            logger.debug('Creating async engine')
            # Updated connection settings for better stability
            self._engine = create_async_engine(
                self._connection_string,
                echo=False,
                future=True,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_timeout=60.0,
                pool_recycle=300,
                # Increased timeouts for better reliability
                # connect_args={
                #     'timeout': 30.0,
                #     'command_timeout': 60.0,
                #     'options': '-c search_path=vcdb,public'  # Set search path by default
                # }
            )

            self._async_session_factory = sessionmaker(
                bind=self._engine.execution_options(asyncio=True),
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.debug('Engine and session factory created successfully')
        except Exception as e:
            logger.error(f'Error initializing engine: {e}', exc_info=True)
            self._engine = None
            self._async_session_factory = None
            raise

    async def _test_connection_async(self) -> bool:
        logger.debug('Testing database connection asynchronously')
        tries = 0
        max_tries = 3

        while tries < max_tries:
            try:
                if not self._engine:
                    logger.error('Engine not initialized')
                    return False

                if not self._async_session_factory:
                    logger.error('Session factory not initialized')
                    return False

                async_session = self._async_session_factory()

                try:
                    async with async_session as session:
                        try:
                            # First try basic connectivity
                            result = await session.execute(text('SELECT 1 AS test'))
                            test_value = result.scalar()

                            if test_value != 1:
                                logger.error('Basic connectivity test failed')
                                return False

                            # Now check schema access explicitly
                            try:
                                # Explicitly set search path
                                await session.execute(text('SET search_path TO vcdb, public'))
                                logger.debug('Search path set to vcdb, public')

                                # Test a query on a common table
                                schema_test = await session.execute(text('SELECT COUNT(*) FROM vcdb.year'))
                                count = schema_test.scalar()
                                logger.debug(f'Successfully queried vcdb.year table, found {count} rows')
                                return True

                            except Exception as schema_error:
                                logger.error(f'Error accessing vcdb schema: {schema_error}')

                                # Try with explicit schema qualification
                                try:
                                    schema_test2 = await session.execute(text('SELECT COUNT(*) FROM vcdb.year'))
                                    count = schema_test2.scalar()
                                    logger.debug(
                                        f'Successfully queried vcdb.year table with explicit schema, found {count} rows')
                                    return True

                                except Exception as schema_error2:
                                    logger.error(f'Error with explicit schema query: {schema_error2}')
                                    return False

                        except Exception as query_error:
                            logger.error(f'Query execution error: {query_error}')
                            return False

                except Exception as session_error:
                    logger.error(f'Error during session execution: {session_error}', exc_info=True)
                    tries += 1

                    if tries >= max_tries:
                        return False

                    # Wait before retrying
                    await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f'Error testing connection: {e}', exc_info=True)
                return False

        return False

    def test_connection(self) -> None:
        logger.debug('Testing database connection...')

        async def _async_test_connection() -> bool:
            try:
                result = await self._test_connection_async()
                # Use QTimer to safely emit signals across threads
                QTimer.singleShot(0, lambda: self.signals.test_connection_completed.emit(result))
                logger.debug(f'Connection test completed with result: {result}')
                return result
            except Exception as e:
                error_str = f'{type(e).__name__}: {str(e)}'
                logger.error(f'Connection test failed: {error_str}', exc_info=True)
                QTimer.singleShot(0, lambda: self.signals.test_connection_failed.emit(error_str))
                return False

        self._async_manager.run_coroutine(_async_test_connection())

    def create_session(self) -> AsyncSession:
        loop = asyncio.get_running_loop()  # Ensures session is tied to current loop
        if not self._async_session_factory:
            raise RuntimeError("Async session factory not initialized")
        return self._async_session_factory()

    def execute_async_operation(self, operation_name: str, coro_factory: Callable[[], Awaitable[T]]) -> str:
        operation_id = str(uuid.uuid4())
        operation = DatabaseOperation(operation_id, operation_name)
        logger.debug(f'Starting operation: {operation_name} (ID: {operation_id})')

        async def _wrapped_operation() -> T:
            operation.mark_running()
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                try:
                    # Initialize the session factory if needed
                    if not self._async_session_factory:
                        with self._lock:
                            if not self._async_session_factory:
                                self._initialize_engine()

                    # Execute the operation
                    result = await coro_factory()
                    operation.mark_completed(result)
                    # Use QTimer for thread-safe signal emission
                    QTimer.singleShot(0, lambda: self.signals.operation_completed.emit(operation))
                    return result

                except Exception as e:
                    retry_count += 1

                    if retry_count < max_retries:
                        logger.warning(
                            f'Operation retry {retry_count}/{max_retries}: {operation_name} (ID: {operation_id})',
                            error=str(e))
                        await asyncio.sleep(1.0 * retry_count)  # Increased wait time for retries
                    else:
                        logger.error(
                            f'Operation failed after {max_retries} attempts: {operation_name} (ID: {operation_id})',
                            error=str(e), exc_info=True)
                        operation.mark_failed(e)
                        QTimer.singleShot(0, lambda: self.signals.operation_failed.emit(operation, e))
                        raise

        self._async_manager.run_coroutine(_wrapped_operation())
        return operation_id

    async def run_operation(self, operation_name: str, coro_factory: Callable[[], Awaitable[T]]) -> T:
        logger.debug(f'Running operation directly: {operation_name}')
        return await coro_factory()

    def dispose(self) -> None:
        if not self._engine:
            return

        async def _dispose() -> None:
            if self._engine:
                logger.debug('Disposing engine')
                await self._engine.dispose()
                self._engine = None
                self._async_session_factory = None

        self._async_manager.run_coroutine(_dispose())
        logger.debug('Database helper dispose initiated')


def safe_async_operation(operation_name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> str:
            if not hasattr(self, '_db_helper') or not isinstance(self._db_helper, DatabaseHelper):
                raise AttributeError("Class must have a '_db_helper' attribute of type DatabaseHelper")

            async def async_operation() -> Any:
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    logger.error(f'Error in {operation_name}: {e}', exc_info=True)
                    raise

            return self._db_helper.execute_async_operation(operation_name, lambda: async_operation())

        return wrapper

    return decorator