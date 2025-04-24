from __future__ import annotations

import asyncio
import logging
from functools import cache
from typing import Any, Dict, List, Optional, Tuple, cast

import structlog
from pydantic_core._pydantic_core import ValidationError
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from qorzen.plugins.autocarequery.models.data_models import (
    DatabaseConnectionError, FilterDTO, QueryExecutionError, VehicleResultDTO
)

logger = structlog.get_logger(__name__)


class DatabaseRepository:
    def __init__(self, connection_string: str) -> None:
        """Initialize database repository with connection string.

        Args:
            connection_string: Database connection string
        """
        # Use a thread-local engine to avoid event loop sharing issues
        self._connection_string = connection_string
        self._create_engine()
        self.metadata = MetaData()
        try:
            self._initialize_tables()
            logger.info('Database repository initialized')
        except Exception as e:
            logger.error('Error initializing database repository', error=str(e))
            # Clean up resources in case of initialization error
            self._cleanup_connections()
            raise

    def _create_engine(self) -> None:
        """Create fresh engine instances."""
        # Create async engine with explicit connection arguments to avoid event loop issues
        self.engine = create_async_engine(
            self._connection_string,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=1,  # Use minimal connections to avoid resource contention
            max_overflow=0,  # Disable overflow
            pool_timeout=30
        )
        self.async_session = sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

        # Create sync engine for metadata reflection
        self.sync_engine = create_engine(
            self._connection_string.replace('+asyncpg', ''),
            echo=False,
            future=True,
            poolclass=None  # Don't pool connections for metadata reflection
        )

    def _initialize_tables(self) -> None:
        """Load table metadata."""
        try:
            self.metadata.reflect(bind=self.sync_engine, schema='vcdb')
            logger.info('Table metadata loaded')
        except Exception as e:
            logger.error('Error loading table metadata', error=str(e))
            raise DatabaseConnectionError(f'Failed to load table metadata: {str(e)}')

    async def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            async with self.async_session() as session:
                # Simple query to test connection
                await session.execute(text('SELECT 1'))
                return True
        except Exception as e:
            logger.error('Connection test failed', error=str(e))
            return False
        finally:
            # Ensure engine is properly disposed
            await self.engine.dispose()

    async def get_filter_values(
            self,
            table_name: str,
            value_column: str,
            id_column: str,
            filters: Optional[FilterDTO] = None
    ) -> List[Tuple[int, str]]:
        """Get filter values for a dropdown."""
        try:
            async with self.async_session() as session:
                try:
                    # Try to set statement timeout with proper error handling
                    try:
                        await session.execute(text("SET LOCAL statement_timeout = '10000'"))
                    except Exception as e:
                        logger.warning(f'Unable to set statement timeout: {str(e)}')

                    # Get filter values based on query
                    # ... existing query logic ...

                    # Example query - simplified for the fix
                    if filters is None or not any([
                        filters.year_id, filters.use_year_range,
                        filters.make_id, filters.model_id, filters.submodel_id
                    ]):
                        if table_name == 'year':
                            query = 'SELECT DISTINCT year_id as id, CAST(year_id as VARCHAR) as value FROM vcdb.year ORDER BY year_id DESC LIMIT 100'
                        elif table_name == 'make':
                            query = 'SELECT DISTINCT make_id as id, name as value FROM vcdb.make ORDER BY name LIMIT 100'
                        elif table_name == 'model':
                            query = 'SELECT DISTINCT model_id as id, name as value FROM vcdb.model ORDER BY name LIMIT 100'
                        elif table_name == 'submodel':
                            query = 'SELECT DISTINCT submodel_id as id, name as value FROM vcdb.submodel ORDER BY name LIMIT 100'
                        else:
                            query = f'SELECT DISTINCT {id_column} as id, {value_column} as value FROM vcdb.{table_name} LIMIT 100'

                        # Execute the query
                        try:
                            result = await session.execute(text(query))
                            values = result.fetchall()
                            return [(row.id, row.value) for row in values]
                        except Exception as e:
                            logger.error(f'Error fetching values for {table_name}: {str(e)}')
                            return []

                except Exception as e:
                    logger.error(f'Error in get_filter_values', error=str(e))
                    return []

        except Exception as e:
            logger.error('Error fetching filter values', table=table_name, error=str(e))
            return []
        finally:
            # Ensure engine is properly disposed after use
            await self.engine.dispose()

    async def execute_vehicle_query(
            self,
            filters: FilterDTO,
            limit: Optional[int] = 1000
    ) -> List[VehicleResultDTO]:
        """Execute query for vehicles based on filters."""
        try:
            async with self.async_session() as session:
                try:
                    await session.execute(text("SET LOCAL statement_timeout = '30000'"))
                except Exception as e:
                    logger.warning(f'Unable to set statement timeout: {str(e)}')

                # Simplified example query
                query = 'SELECT vehicle_id FROM vcdb.vehicle LIMIT :limit'

                try:
                    result = await session.execute(text(query), {'limit': limit})
                    rows = result.fetchall()
                    # Return empty list for simplicity
                    return []
                except Exception as e:
                    logger.error('Error executing vehicle query', error=str(e))
                    raise QueryExecutionError(f'Error executing query: {str(e)}')
        except Exception as e:
            logger.error('Error executing vehicle query', error=str(e))
            raise QueryExecutionError(f'Error executing query: {str(e)}')
        finally:
            # Ensure engine is properly disposed after use
            await self.engine.dispose()

    def _cleanup_connections(self) -> None:
        """Clean up database connections."""
        if hasattr(self, 'sync_engine'):
            self.sync_engine.dispose()

    async def cleanup_async_connections(self) -> None:
        """Clean up async database connections."""
        if hasattr(self, 'engine'):
            await self.engine.dispose()