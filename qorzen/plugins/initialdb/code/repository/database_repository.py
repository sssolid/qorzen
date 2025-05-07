from __future__ import annotations

"""
Database repository for the InitialDB application.

This module provides the core database interaction layer, handling connections,
queries, and data conversion between SQLAlchemy models and Pydantic schemas.
"""

import asyncio
import traceback
from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast
import structlog
from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from PyQt6.QtCore import QObject, pyqtSignal

from ..models.base_class import Base
from ..models.schema import FilterDTO, SavedQueryDTO, VehicleResultDTO
from ..utils.database_helper import DatabaseHelper, safe_async_operation
from ..utils.schema_registry import SchemaRegistry
from ..query_builders.query_builder import query_builder

logger = structlog.get_logger(__name__)


class DatabaseOperationResult:
    """Result of a database operation."""

    def __init__(self, operation_id: str, result: Any = None):
        self.operation_id = operation_id
        self.result = result


class DatabaseRepositorySignals(QObject):
    """Signals for database repository operations."""

    operationCompleted = pyqtSignal(object)
    operationFailed = pyqtSignal(object, Exception)
    testConnectionCompleted = pyqtSignal(bool)
    testConnectionFailed = pyqtSignal(str)


class DatabaseConnectionError(Exception):
    """Exception raised when a database connection fails."""
    pass


class QueryExecutionError(Exception):
    """Exception raised when a query execution fails."""
    pass


class InvalidFilterError(Exception):
    """Exception raised when a filter is invalid."""
    pass


class DatabaseRepository:
    """
    Repository for database interactions.

    This class provides a high-level interface for database operations,
    using QueryBuilder to construct queries and DatabaseHelper for
    executing them.
    """

    def __init__(self, connection_string: str) -> None:
        """
        Initialize the database repository.

        Args:
            connection_string: The database connection string
        """
        self._connection_string = connection_string
        self.disposed = False
        self.signals = DatabaseRepositorySignals()

        try:
            masked_connection = self._mask_connection_string(connection_string)
            logger.debug(f'Initializing database repository with connection: {masked_connection}')

            self._db_helper = DatabaseHelper(connection_string)
            self._db_helper.signals.operation_completed.connect(self._on_operation_completed)
            self._db_helper.signals.operation_failed.connect(self._on_operation_failed)
            self._db_helper.signals.test_connection_completed.connect(self.signals.testConnectionCompleted)
            self._db_helper.signals.test_connection_failed.connect(self.signals.testConnectionFailed)

            logger.info('Database repository initialized')
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Error initializing database repository: {str(e)}\n{error_details}')
            raise DatabaseConnectionError(f'Failed to connect to database: {str(e)}') from e

    def _mask_connection_string(self, conn_string: str) -> str:
        """
        Mask sensitive information in the connection string.

        Args:
            conn_string: The connection string to mask

        Returns:
            A masked version of the connection string
        """
        if '@' in conn_string:
            parts = conn_string.split('@')
            if ':' in parts[0]:
                auth_parts = parts[0].split(':')
                if len(auth_parts) > 2:
                    auth_parts[-1] = '********'
                    parts[0] = ':'.join(auth_parts)
                    return '@'.join(parts)

        return conn_string

    def _on_operation_completed(self, operation: Any) -> None:
        """
        Handle completion of a database operation.

        Args:
            operation: The completed operation
        """
        logger.debug(f'Operation completed: {operation.operation_id}')
        result = DatabaseOperationResult(str(operation.operation_id), operation.result)
        self.signals.operationCompleted.emit(result)

    def _on_operation_failed(self, operation: Any, error: Exception) -> None:
        """
        Handle failure of a database operation.

        Args:
            operation: The failed operation
            error: The error that occurred
        """
        logger.error(f'Operation failed: {operation.operation_id}, Error: {str(error)}')
        result = DatabaseOperationResult(str(operation.operation_id))
        self.signals.operationFailed.emit(result, error)

    async def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if the connection was successful, False otherwise
        """
        try:
            logger.debug('Testing database connection...')
            event = asyncio.Event()
            result_container = {'result': False, 'error': None}

            def on_completed(success: bool) -> None:
                logger.debug(f'Connection test completed with result: {success}')
                result_container['result'] = success
                event.set()

            def on_failed(error_msg: str) -> None:
                logger.error(f'Connection test failed: {error_msg}')
                result_container['error'] = error_msg
                event.set()

            self._db_helper.signals.testConnectionCompleted.connect(on_completed)
            self._db_helper.signals.testConnectionFailed.connect(on_failed)

            try:
                self._db_helper.test_connection()
                await asyncio.wait_for(event.wait(), timeout=10.0)
            finally:
                try:
                    self._db_helper.signals.testConnectionCompleted.disconnect(on_completed)
                    self._db_helper.signals.testConnectionFailed.disconnect(on_failed)
                except Exception as e:
                    logger.warning(f'Error disconnecting signals: {str(e)}')

            if result_container['error']:
                logger.error(f"Connection error: {result_container['error']}")

            return result_container['result']
        except asyncio.TimeoutError:
            logger.error('Connection test timed out after 10 seconds')
            return False
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Connection test exception: {str(e)}\n{error_details}')
            return False

    @safe_async_operation('get_filter_values')
    async def get_filter_values(self, table_name: str, id_column: str, value_column: str,
                                filters: Optional[FilterDTO] = None) -> List[Tuple[Any, str]]:
        """
        Get filter values for a specific filter, optionally applying existing filters.

        Args:
            table_name: The name of the table containing the filter values
            id_column: The ID column for the filter
            value_column: The display value column for the filter
            filters: Optional filters to apply

        Returns:
            A list of (id, display_value) tuples
        """
        # Build the query using the QueryBuilder
        stmt = query_builder.build_filter_value_query(
            table_name=table_name,
            id_column=id_column,
            value_column=value_column,
            filters=filters
        )

        # Execute the query
        session = self._db_helper.create_session()
        async with session as session:
            result = await session.execute(stmt)
            rows = result.all()

        # Format the results
        return [(row[0], str(row[1])) for row in rows]

    def build_filter_value_query(self, table_name: str, id_column: str, value_column: str,
                                 filters: Optional[FilterDTO] = None) -> Select:
        """
        Build a query for retrieving filter values.

        Args:
            table_name: Name of the table
            id_column: Name of the ID column
            value_column: Name of the value column
            filters: Optional filters to apply

        Returns:
            Select: SQLAlchemy select statement
        """
        return query_builder.build_filter_value_query(
            table_name=table_name,
            id_column=id_column,
            value_column=value_column,
            filters=filters
        )

    def build_vehicle_query(self, filters: FilterDTO, display_fields: List[Tuple[str, str, str]],
                            limit: Optional[int] = 1000) -> Select:
        """
        Builds a query to fetch vehicle data based on specified filters, fields to display, and a limit
        on the number of results. The resulting query is tailored for vehicle information retrieval
        based on the provided input criteria.

        Args:
            filters: An object of FilterDTO that encapsulates the filtering logic and criteria
                for vehicle data.
            display_fields: A list of tuples, where each tuple contains three strings representing
                the field name, alias, and type to be included in the query.
            limit: An optional integer specifying the maximum number of results to retrieve from the
                query. Defaults to 1000 if not provided.

        Returns:
            A Select query object constructed to fetch vehicle data as per defined filters and fields.
        """
        return query_builder.build_vehicle_query(filters=filters, display_fields=display_fields, limit=limit)

    @safe_async_operation('execute_vehicle_query')
    async def execute_vehicle_query(self, filters: FilterDTO, display_fields: List[Tuple[str, str, str]],
                                    limit: Optional[int] = 1000) -> List[Dict[str, Any]]:
        """
        Execute a vehicle query with the given filters and display fields.

        Args:
            filters: The filter criteria
            display_fields: Fields to include in the results
            limit: Maximum number of results to return

        Returns:
            A list of vehicle dictionaries matching the filters

        Raises:
            QueryExecutionError: If the query execution fails
        """
        try:
            logger.debug(f'Executing vehicle query with {len(display_fields)} display fields')

            # Build the query using the QueryBuilder
            stmt = query_builder.build_vehicle_query(filters=filters, display_fields=display_fields, limit=limit)

            # Execute the query
            session = self._db_helper.create_session()
            async with session as session:
                result = await session.execute(stmt)
                rows = result.fetchall()

            # Extract column labels from the query
            column_labels = []
            for column in stmt._raw_columns:
                if hasattr(column, '_label'):
                    column_labels.append(column._label)
                else:
                    column_labels.append(f'col_{len(column_labels)}')

            logger.debug(f'Column labels from query: {column_labels}')

            # Convert rows to dictionaries
            result_dicts = []
            for row in rows:
                row_dict = {}
                for i, col_key in enumerate(column_labels):
                    if i < len(row):
                        row_dict[col_key] = row[i]

                # Log the first row for debugging
                if len(result_dicts) == 0:
                    logger.debug(f'First row data: {row_dict}')

                result_dicts.append(row_dict)

            logger.info(f'Query executed successfully, returned {len(result_dicts)} results')
            return result_dicts

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Error executing vehicle query: {str(e)}\n{error_details}')
            raise QueryExecutionError(f'Failed to execute vehicle query: {str(e)}') from e

    @safe_async_operation('execute_multiple_vehicle_queries')
    async def execute_multiple_vehicle_queries(self, filter_dtos: Dict[str, FilterDTO],
                                               display_fields: List[Tuple[str, str, str]],
                                               limit: Optional[int] = 1000) -> List[Dict[str, Any]]:
        """
        Execute multiple vehicle queries and combine the results.

        Args:
            filter_dtos: A dictionary of filter sets, keyed by section ID
            display_fields: Fields to include in the results
            limit: Maximum number of results to return

        Returns:
            A list of unique vehicle dictionaries matching any of the filter sets

        Raises:
            QueryExecutionError: If the query execution fails
        """
        try:
            if not filter_dtos:
                logger.warning('No filters provided to execute_multiple_vehicle_queries')
                return []

            # Convert keys to strings if needed
            string_filter_dtos = {str(key): value for key, value in filter_dtos.items()}

            # Collect unique results from all queries
            all_results = []
            vehicle_ids = set()

            for section_id, filter_dto in string_filter_dtos.items():
                try:
                    if not isinstance(filter_dto, FilterDTO):
                        logger.warning(f'Section {section_id} contains invalid FilterDTO. Skipping.')
                        continue

                    logger.debug(f'Executing query for section {section_id}')

                    # Execute the query for this filter set
                    section_results = await DatabaseRepository.execute_vehicle_query.__wrapped__(
                        self,
                        filters=filter_dto,
                        display_fields=display_fields,
                        limit=limit
                    )

                    # Add unique results
                    for result in section_results:
                        if 'vehicle_id' in result and result['vehicle_id'] not in vehicle_ids:
                            vehicle_ids.add(result['vehicle_id'])
                            all_results.append(result)

                            # Check if we've reached the limit
                            if len(all_results) >= limit:
                                break

                except Exception as section_error:
                    logger.error(f'Error executing query for section {section_id}: {str(section_error)}')

                # Check if we've reached the limit
                if len(all_results) >= limit:
                    break

            logger.info(f'Multiple queries executed successfully, returned {len(all_results)} combined results')
            return all_results[:limit]

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Error executing multiple vehicle queries: {str(e)}\n{error_details}')
            raise QueryExecutionError(f'Failed to execute multiple vehicle queries: {str(e)}') from e

    @safe_async_operation('save_query')
    async def save_query(self, query_dto: SavedQueryDTO) -> bool:
        """
        Save a query configuration.

        Args:
            query_dto: The query to save

        Returns:
            True if the query was saved successfully, False otherwise
        """
        try:
            from ..config.settings import settings

            if not hasattr(query_dto, 'name') or not query_dto.name:
                logger.error('Cannot save query: missing name')
                return False

            logger.debug(f'Saving query: {query_dto.name}')

            # Convert to dictionary
            query_dict = query_dto.model_dump() if hasattr(query_dto, 'model_dump') else query_dto.dict()

            # Save to settings
            settings.save_query(query_dto.name, query_dict)

            return True

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Failed to save query: {str(e)}\n{error_details}')
            return False

    @safe_async_operation('load_query')
    async def load_query(self, query_name: str) -> Optional[SavedQueryDTO]:
        """
        Load a saved query.

        Args:
            query_name: The name of the query to load

        Returns:
            The loaded query, or None if not found
        """
        try:
            from ..config.settings import settings

            logger.debug(f'Loading query: {query_name}')

            # Load from settings
            query_dict = settings.load_query(query_name)

            if not query_dict:
                logger.warning(f'Query not found: {query_name}')
                return None

            # Convert to SavedQueryDTO
            return SavedQueryDTO(**query_dict)

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Failed to load query: {str(e)}\n{error_details}')
            return None

    @safe_async_operation('get_saved_queries')
    async def get_saved_queries(self) -> Dict[str, SavedQueryDTO]:
        """
        Get all saved queries.

        Returns:
            A dictionary mapping query names to SavedQueryDTO objects
        """
        try:
            from ..config.settings import settings

            logger.debug('Getting all saved queries')

            # Get query names from settings
            query_names = settings.get_available_queries()
            result = {}

            # Load each query
            for name in query_names:
                query_dict = settings.load_query(name)
                if query_dict:
                    result[name] = SavedQueryDTO(**query_dict)

            logger.debug(f'Found {len(result)} saved queries')
            return result

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Failed to get saved queries: {str(e)}\n{error_details}')
            return {}

    @safe_async_operation('get_recent_queries')
    async def get_recent_queries(self) -> Dict[str, SavedQueryDTO]:
        """
        Get recently used queries.

        Returns:
            A dictionary mapping query names to SavedQueryDTO objects
        """
        try:
            from ..config.settings import settings

            logger.debug('Getting all recent queries')

            # Get query names from settings
            query_names = settings.get_available_queries()
            result = {}

            # Load each query
            for name in query_names:
                query_dict = settings.load_query(name)
                if query_dict:
                    result[name] = SavedQueryDTO(**query_dict)

            logger.debug(f'Found {len(result)} recent queries')
            return result

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Failed to get recent queries: {str(e)}\n{error_details}')
            return {}

    @safe_async_operation('delete_query')
    async def delete_query(self, query_name: str) -> bool:
        """
        Delete a saved query.

        Args:
            query_name: The name of the query to delete

        Returns:
            True if the query was deleted successfully, False otherwise
        """
        try:
            from ..config.settings import settings

            logger.debug(f'Deleting query: {query_name}')

            # Delete from settings
            settings.delete_query(query_name)

            return True

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f'Failed to delete query: {str(e)}\n{error_details}')
            return False

    def dispose(self) -> None:
        """Clean up resources."""
        if getattr(self, 'disposed', False):
            return

        self.disposed = True

        if hasattr(self, '_db_helper'):
            try:
                # Disconnect signals
                self._db_helper.signals.operationCompleted.disconnect(self._on_operation_completed)
                self._db_helper.signals.operationFailed.disconnect(self._on_operation_failed)
                self._db_helper.signals.testConnectionCompleted.disconnect(self.signals.testConnectionCompleted)
                self._db_helper.signals.testConnectionFailed.disconnect(self.signals.testConnectionFailed)
            except Exception:
                pass

            # Dispose database helper
            self._db_helper.dispose()

            logger.debug('Database repository disposed')