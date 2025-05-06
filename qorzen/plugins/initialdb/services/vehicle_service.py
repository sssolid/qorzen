from __future__ import annotations

"""
Vehicle service for accessing and querying vehicle data.

This module provides a high-level service for interacting with vehicle data,
abstracting away the database access details and providing a clean API for
filtering and retrieving vehicle information.
"""

import asyncio
from dataclasses import asdict
import logging
from typing import Any, Dict, List, Optional, Tuple, cast

from sqlalchemy import inspect, text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..models.vehicle import (
    Base, BaseVehicle, DatabaseConnectionError, Make, Model,
    QueryExecutionError, Vehicle, Year
)
from ..query.builder import FilterParams, query_builder


class VehicleService:
    """
    Service for accessing and querying vehicle data.

    This service provides methods for retrieving vehicles with filtering,
    executing custom queries, and performing database validations.
    """

    def __init__(self,
                 db_manager: Any,
                 logger: Any,
                 event_bus: Any,
                 thread_manager: Any,
                 config: Any) -> None:
        """
        Initialize the vehicle service.

        Args:
            db_manager: Database manager for database access
            logger: Logger for logging
            event_bus: Event bus for publishing/subscribing to events
            thread_manager: Thread manager for background tasks
            config: Configuration provider
        """
        self._db_manager = db_manager
        self._logger = logger
        self._event_bus = event_bus
        self._thread_manager = thread_manager
        self._config = config

        # Get plugin-specific configuration
        self._plugin_config = self._config.get("plugins.initialdb", {})
        self._default_limit = self._plugin_config.get("default_query_limit", 1000)
        self._max_limit = self._plugin_config.get("max_query_limit", 10000)

        self._logger.info("Vehicle service initialized")

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update service configuration.

        Args:
            config: New configuration dictionary
        """
        self._plugin_config = config
        self._default_limit = config.get("default_query_limit", 1000)
        self._max_limit = config.get("max_query_limit", 10000)
        self._logger.debug(f"Configuration updated: default_limit={self._default_limit}, max_limit={self._max_limit}")

    def validate_database(self) -> bool:
        """
        Validate database connection and schema.

        Returns:
            True if validation successful, False otherwise
        """
        try:
            with self._db_manager.session() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1 AS test"))
                test_value = result.scalar()
                if test_value != 1:
                    self._logger.error("Basic connectivity test failed")
                    return False

                # Test schema access
                try:
                    session.execute(text("SET search_path TO vcdb, public"))
                    self._logger.debug("Search path set to vcdb, public")
                except Exception as e:
                    self._logger.error(f"Failed to set search path: {e}")
                    return False

                # Test key tables
                core_tables = ["year", "make", "model", "vehicle"]
                for table in core_tables:
                    try:
                        count = session.execute(text(f"SELECT COUNT(*) FROM vcdb.{table}")).scalar()
                        self._logger.debug(f"Table {table} count: {count}")
                        if count is None or count < 1:
                            self._logger.warning(f"Table {table} appears to be empty")
                    except Exception as e:
                        self._logger.error(f"Failed to query table {table}: {e}")
                        return False

                self._logger.info("Database validation successful")
                return True

        except Exception as e:
            self._logger.error(f"Database validation failed: {e}", exc_info=True)
            return False

    def get_vehicles(self,
                     filters: FilterParams,
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get vehicles based on filter criteria.

        Args:
            filters: Filter parameters
            limit: Maximum number of results (defaults to configured default_limit)

        Returns:
            List of vehicle dictionaries

        Raises:
            DatabaseConnectionError: If database connection fails
            QueryExecutionError: If query execution fails
        """
        try:
            # Apply limit constraints
            if limit is None:
                limit = self._default_limit
            elif limit > self._max_limit:
                limit = self._max_limit

            # Build query
            query = query_builder.build_vehicle_query(filters, limit=limit)

            # Execute query
            with self._db_manager.session() as session:
                result = session.execute(query)
                vehicles = result.scalars().all()

                # Convert to dictionaries
                return [vehicle.to_dict() for vehicle in vehicles]

        except Exception as e:
            self._logger.error(f"Error getting vehicles: {e}", exc_info=True)
            raise QueryExecutionError(f"Failed to execute vehicle query: {e}") from e

    async def get_vehicles_async(self,
                                 filters: FilterParams,
                                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get vehicles asynchronously based on filter criteria.

        Args:
            filters: Filter parameters
            limit: Maximum number of results (defaults to configured default_limit)

        Returns:
            List of vehicle dictionaries

        Raises:
            DatabaseConnectionError: If database connection fails
            QueryExecutionError: If query execution fails
        """
        try:
            # Apply limit constraints
            if limit is None:
                limit = self._default_limit
            elif limit > self._max_limit:
                limit = self._max_limit

            # Build query
            query = query_builder.build_vehicle_query(filters, limit=limit)

            # Execute query
            async with await self._db_manager.async_session() as session:
                result = await session.execute(query)
                vehicles = result.scalars().all()

                # Convert to dictionaries
                return [vehicle.to_dict() for vehicle in vehicles]

        except Exception as e:
            self._logger.error(f"Error getting vehicles async: {e}", exc_info=True)
            raise QueryExecutionError(f"Failed to execute async vehicle query: {e}") from e

    def get_filter_values(self,
                          table_name: str,
                          id_column: str,
                          value_column: str,
                          filters: Optional[FilterParams] = None) -> List[Tuple[Any, str]]:
        """
        Get distinct values for a column, optionally filtered.

        This is used for populating filter dropdown values.

        Args:
            table_name: Name of the table
            id_column: Name of the ID column
            value_column: Name of the value column to display
            filters: Optional filter parameters to apply

        Returns:
            List of (id, value) tuples

        Raises:
            DatabaseConnectionError: If database connection fails
            QueryExecutionError: If query execution fails
        """
        try:
            # Build query
            query = query_builder.build_filter_values_query(
                table_name=table_name,
                id_column=id_column,
                value_column=value_column,
                filters=filters
            )

            # Execute query
            with self._db_manager.session() as session:
                result = session.execute(query)
                rows = result.all()

                # Convert and return
                return [(row[0], str(row[1])) for row in rows]

        except Exception as e:
            self._logger.error(f"Error getting filter values: {e}", exc_info=True)
            raise QueryExecutionError(f"Failed to execute filter values query: {e}") from e

    async def get_filter_values_async(self,
                                      table_name: str,
                                      id_column: str,
                                      value_column: str,
                                      filters: Optional[FilterParams] = None) -> List[Tuple[Any, str]]:
        """
        Get distinct values for a column asynchronously, optionally filtered.

        This is used for populating filter dropdown values.

        Args:
            table_name: Name of the table
            id_column: Name of the ID column
            value_column: Name of the value column to display
            filters: Optional filter parameters to apply

        Returns:
            List of (id, value) tuples

        Raises:
            DatabaseConnectionError: If database connection fails
            QueryExecutionError: If query execution fails
        """
        try:
            # Build query
            query = query_builder.build_filter_values_query(
                table_name=table_name,
                id_column=id_column,
                value_column=value_column,
                filters=filters
            )

            # Execute query
            async with await self._db_manager.async_session() as session:
                result = await session.execute(query)
                rows = result.all()

                # Convert and return
                return [(row[0], str(row[1])) for row in rows]

        except Exception as e:
            self._logger.error(f"Error getting filter values async: {e}", exc_info=True)
            raise QueryExecutionError(f"Failed to execute async filter values query: {e}") from e

    def create_filter_params_from_dict(self, data: Dict[str, Any]) -> FilterParams:
        """
        Create FilterParams from a dictionary.

        This is useful for converting API request data to filter parameters.

        Args:
            data: Dictionary containing filter criteria

        Returns:
            FilterParams object
        """
        # Create a new FilterParams with only the fields that exist in the data
        kwargs = {}
        for field in FilterParams.__dataclass_fields__:
            if field in data:
                kwargs[field] = data[field]

        return FilterParams(**kwargs)

    def get_available_filter_fields(self) -> List[Dict[str, Any]]:
        """
        Get a list of available filter fields.

        Returns:
            List of dictionaries with filter field information
        """
        filter_fields = [
            {"name": "year", "label": "Year", "type": "multi", "table": "year", "id_column": "year_id",
             "value_column": "year_id"},
            {"name": "make", "label": "Make", "type": "multi", "table": "make", "id_column": "make_id",
             "value_column": "make_name"},
            {"name": "model", "label": "Model", "type": "multi", "table": "model", "id_column": "model_id",
             "value_column": "model_name"},
            {"name": "sub_model", "label": "Sub-Model", "type": "multi", "table": "sub_model",
             "id_column": "sub_model_id", "value_column": "sub_model_name"},
            {"name": "region", "label": "Region", "type": "multi", "table": "region", "id_column": "region_id",
             "value_column": "region_name"},
            {"name": "engine_liter", "label": "Engine Size (L)", "type": "multi", "table": "engine_block",
             "id_column": "engine_block_id", "value_column": "liter"},
            {"name": "engine_cylinders", "label": "Cylinders", "type": "multi", "table": "engine_block",
             "id_column": "engine_block_id", "value_column": "cylinders"},
            {"name": "fuel_type", "label": "Fuel Type", "type": "multi", "table": "fuel_type",
             "id_column": "fuel_type_id", "value_column": "fuel_type_name"},
            {"name": "aspiration", "label": "Aspiration", "type": "multi", "table": "aspiration",
             "id_column": "aspiration_id", "value_column": "aspiration_name"},
            {"name": "body_type", "label": "Body Type", "type": "multi", "table": "body_type",
             "id_column": "body_type_id", "value_column": "body_type_name"},
            {"name": "transmission_type", "label": "Transmission Type", "type": "multi", "table": "transmission_type",
             "id_column": "transmission_type_id", "value_column": "transmission_type_name"},
        ]

        return filter_fields

    def get_available_display_fields(self) -> List[Dict[str, Any]]:
        """
        Get a list of available display fields.

        Returns:
            List of dictionaries with display field information
        """
        display_fields = [
            {"name": "vehicle_id", "label": "Vehicle ID", "visible": False},
            {"name": "year", "label": "Year", "visible": True},
            {"name": "make", "label": "Make", "visible": True},
            {"name": "model", "label": "Model", "visible": True},
            {"name": "sub_model", "label": "Sub-Model", "visible": True},
            {"name": "region", "label": "Region", "visible": False},
            {"name": "engine_liter", "label": "Engine (L)", "visible": True},
            {"name": "engine_cylinders", "label": "Cylinders", "visible": True},
            {"name": "fuel_type", "label": "Fuel", "visible": False},
            {"name": "aspiration", "label": "Aspiration", "visible": False},
            {"name": "body_type", "label": "Body Type", "visible": False},
        ]

        return display_fields

    def execute_custom_query(self, query_sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query.

        Args:
            query_sql: SQL query string
            params: Optional query parameters

        Returns:
            List of result dictionaries

        Raises:
            DatabaseConnectionError: If database connection fails
            QueryExecutionError: If query execution fails
        """
        try:
            # Execute query
            with self._db_manager.session() as session:
                result = session.execute(text(query_sql), params or {})
                rows = result.all()

                # Get column names from result
                column_names = result.keys()

                # Convert to list of dictionaries
                return [dict(zip(column_names, row)) for row in rows]

        except Exception as e:
            self._logger.error(f"Error executing custom query: {e}", exc_info=True)
            raise QueryExecutionError(f"Failed to execute custom query: {e}") from e

    async def execute_custom_query_async(self, query_sql: str, params: Optional[Dict[str, Any]] = None) -> List[
        Dict[str, Any]]:
        """
        Execute a custom SQL query asynchronously.

        Args:
            query_sql: SQL query string
            params: Optional query parameters

        Returns:
            List of result dictionaries

        Raises:
            DatabaseConnectionError: If database connection fails
            QueryExecutionError: If query execution fails
        """
        try:
            # Execute query
            async with await self._db_manager.async_session() as session:
                result = await session.execute(text(query_sql), params or {})
                rows = result.all()

                # Get column names from result
                column_names = result.keys()

                # Convert to list of dictionaries
                return [dict(zip(column_names, row)) for row in rows]

        except Exception as e:
            self._logger.error(f"Error executing custom query async: {e}", exc_info=True)
            raise QueryExecutionError(f"Failed to execute async custom query: {e}") from e

    def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        self._logger.info("Vehicle service shutting down")
        # Nothing to clean up at the moment