#!/usr/bin/env python3
# vehicle_service.py
from __future__ import annotations

"""
Vehicle service for accessing and querying vehicle data.

This module provides a high-level service for interacting with vehicle data,
abstracting away the database access details and providing a clean API for
filtering and retrieving vehicle information.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, cast
from sqlalchemy import text, select

from ..models.schema import FilterDTO
from ..exceptions import DatabaseConnectionError, QueryExecutionError
from ..settings import get_plugin_config_namespace


class VehicleService:
    """Service for accessing vehicle database information.

    This service provides methods to query and filter vehicle data from
    the underlying database.
    """

    def __init__(self, db_manager: Any, logger: logging.Logger, config: Any) -> None:
        """Initialize the vehicle service.

        Args:
            db_manager: Database manager from Qorzen
            logger: Logger for this service
            config: Config provider from Qorzen
        """
        self._db_manager = db_manager
        self._logger = logger
        self._config = config

        # Get configuration values using Qorzen's config manager
        namespace = get_plugin_config_namespace()
        self._default_limit = self._config.get(f"{namespace}.default_query_limit", 1000)
        self._max_limit = self._config.get(f"{namespace}.max_query_limit", 10000)
        self._enable_caching = self._config.get(f"{namespace}.enable_caching", True)
        self._cache_timeout = self._config.get(f"{namespace}.cache_timeout", 300)

        self._logger.info("Vehicle service initialized")

    def update_config(self, config: Any) -> None:
        """Update service configuration.

        Args:
            config: Config provider from Qorzen
        """
        self._config = config

        # Update configuration from the provider
        namespace = get_plugin_config_namespace()
        self._default_limit = self._config.get(f"{namespace}.default_query_limit", 1000)
        self._max_limit = self._config.get(f"{namespace}.max_query_limit", 10000)
        self._enable_caching = self._config.get(f"{namespace}.enable_caching", True)
        self._cache_timeout = self._config.get(f"{namespace}.cache_timeout", 300)

        self._logger.debug(
            f"Configuration updated: default_limit={self._default_limit}, "
            f"max_limit={self._max_limit}, enable_caching={self._enable_caching}, "
            f"cache_timeout={self._cache_timeout}"
        )

    def validate_database(self) -> bool:
        """Validate the database connection.

        Returns:
            True if connected, False otherwise
        """
        try:
            with self._db_manager.session() as session:
                # Simple connectivity test
                result = session.execute(text("SELECT 1 AS test"))
                test_value = result.scalar()
                if test_value != 1:
                    self._logger.error("Basic connectivity test failed")
                    return False

                # Try setting search path for PostgreSQL
                try:
                    session.execute(text("SET search_path TO vcdb, public"))
                except Exception as e:
                    self._logger.warning(f"Failed to set search path: {e}")

                # Check essential tables
                for table in ["year", "make", "model", "vehicle"]:
                    try:
                        count = session.execute(text(f"SELECT COUNT(*) FROM vcdb.{table}")).scalar()
                        if count is None or count < 1:
                            self._logger.warning(f"Table {table} appears to be empty")
                    except Exception as e:
                        self._logger.error(f"Failed to query table {table}: {e}")
                        return False

                return True
        except Exception as e:
            self._logger.error(f"Database validation failed: {e}")
            return False

    def get_vehicles(self, filters: FilterDTO, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get vehicles matching the given filters.

        Args:
            filters: Filter criteria
            limit: Maximum number of records to return

        Returns:
            List of vehicle dictionaries

        Raises:
            QueryExecutionError: If query execution fails
        """
        try:
            # Apply limit constraints
            if limit is None:
                limit = self._default_limit
            elif limit > self._max_limit:
                limit = self._max_limit

            from ..query_builders.query_builder import query_builder

            # Build query
            display_fields = self.get_available_display_fields()
            field_tuples = [(field["table"], field["name"], field["label"])
                            for field in display_fields]

            query = query_builder.build_vehicle_query(filters, field_tuples, limit=limit)

            # Execute query
            with self._db_manager.session() as session:
                result = session.execute(query)
                rows = result.all()

            # Convert to dictionaries
            vehicles = []
            for row in rows:
                if hasattr(row, "_mapping"):
                    vehicles.append({key: value for key, value in row._mapping.items()})
                elif hasattr(row, "_asdict"):
                    vehicles.append(row._asdict())
                else:
                    # Fallback for other result types
                    vehicles.append({col: getattr(row, col) for col in row._fields})

            return vehicles
        except Exception as e:
            self._logger.error(f"Error getting vehicles: {e}")
            raise QueryExecutionError(f"Failed to execute vehicle query: {e}") from e

    def get_filter_values(self, table_name: str, id_column: str, value_column: str,
                          filters: Optional[FilterDTO] = None) -> List[Tuple[Any, str]]:
        """Get possible filter values from a table.

        Args:
            table_name: Database table name
            id_column: ID column name
            value_column: Display value column name
            filters: Optional filters to apply

        Returns:
            List of (id, value) tuples

        Raises:
            QueryExecutionError: If query execution fails
        """
        try:
            from ..query_builders.query_builder import query_builder

            query = query_builder.build_filter_value_query(
                table_name=table_name,
                id_column=id_column,
                value_column=value_column,
                filters=filters
            )

            with self._db_manager.session() as session:
                result = session.execute(query)
                rows = result.all()
                return [(row[0], str(row[1])) for row in rows]
        except Exception as e:
            self._logger.error(f"Error getting filter values: {e}")
            raise QueryExecutionError(f"Failed to execute filter values query: {e}") from e

    def get_available_filter_fields(self) -> List[Dict[str, Any]]:
        """Get available filter fields.

        Returns:
            List of filter field definitions
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
             "id_column": "transmission_type_id", "value_column": "transmission_type_name"}
        ]
        return filter_fields

    def get_available_display_fields(self) -> List[Dict[str, Any]]:
        """Get available display fields.

        Returns:
            List of display field definitions
        """
        display_fields = [
            {"name": "vehicle_id", "label": "Vehicle ID", "visible": False, "table": "vehicle"},
            {"name": "year_id", "label": "Year", "visible": True, "table": "year"},
            {"name": "make_name", "label": "Make", "visible": True, "table": "make"},
            {"name": "model_name", "label": "Model", "visible": True, "table": "model"},
            {"name": "sub_model_name", "label": "Sub-Model", "visible": True, "table": "sub_model"},
            {"name": "region_name", "label": "Region", "visible": False, "table": "region"},
            {"name": "liter", "label": "Engine (L)", "visible": True, "table": "engine_block"},
            {"name": "cylinders", "label": "Cylinders", "visible": True, "table": "engine_block"},
            {"name": "fuel_type_name", "label": "Fuel", "visible": False, "table": "fuel_type"},
            {"name": "aspiration_name", "label": "Aspiration", "visible": False, "table": "aspiration"},
            {"name": "body_type_name", "label": "Body Type", "visible": False, "table": "body_type"}
        ]
        return display_fields

    def execute_custom_query(self, query_sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a custom SQL query.

        Args:
            query_sql: SQL query string
            params: Query parameters

        Returns:
            List of result dictionaries

        Raises:
            QueryExecutionError: If query execution fails
        """
        try:
            with self._db_manager.session() as session:
                result = session.execute(text(query_sql), params or {})
                rows = result.all()

                # Get column names from result
                column_names = result.keys()

                # Convert to dictionaries
                return [dict(zip(column_names, row)) for row in rows]
        except Exception as e:
            self._logger.error(f"Error executing custom query: {e}")
            raise QueryExecutionError(f"Failed to execute custom query: {e}") from e

    def shutdown(self) -> None:
        """Shut down the service."""
        self._logger.info("Vehicle service shutting down")