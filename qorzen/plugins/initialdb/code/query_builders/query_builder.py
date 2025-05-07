#!/usr/bin/env python3
# query_builder.py
from __future__ import annotations

"""
SQL query builder for the InitialDB plugin.

This module provides functionality to build SQL queries for vehicle data,
with support for complex filtering and joining tables.
"""

from typing import Any, Dict, List, Optional, Tuple, Union, cast
from sqlalchemy import select, and_, or_, func, text, Table, Column, MetaData
from sqlalchemy.sql import Select

from ..models.schema import FilterDTO
from ..exceptions import QueryExecutionError


class VehicleQueryBuilder:
    """Builder for creating SQL queries against the vehicle database."""

    def __init__(self) -> None:
        """Initialize the query builder."""
        self.metadata = MetaData(schema="vcdb")

    def build_vehicle_query(
        self,
        filters: FilterDTO,
        display_fields: List[Tuple[str, str, str]],
        limit: Optional[int] = None
    ) -> Select:
        """Build a SQL query for vehicles based on filter criteria.

        Args:
            filters: Filter criteria
            display_fields: Display fields as (table, column, label) tuples
            limit: Maximum number of records to return

        Returns:
            SQLAlchemy Select object

        Raises:
            QueryExecutionError: If query building fails
        """
        try:
            # Start with base query
            base_query = select()

            # Add selected columns based on display fields
            for table_name, column_name, label in display_fields:
                base_query = base_query.add_columns(
                    text(f"{table_name}.{column_name}").label(label)
                )

            # Set up joins
            base_query = base_query.select_from(text("vcdb.vehicle"))

            # Add standard joins
            standard_joins = [
                "LEFT JOIN vcdb.year ON vehicle.year_id = year.year_id",
                "LEFT JOIN vcdb.make ON vehicle.make_id = make.make_id",
                "LEFT JOIN vcdb.model ON vehicle.model_id = model.model_id",
                "LEFT JOIN vcdb.sub_model ON vehicle.sub_model_id = sub_model.sub_model_id",
                "LEFT JOIN vcdb.region ON vehicle.region_id = region.region_id",
                "LEFT JOIN vcdb.engine_block ON vehicle.engine_block_id = engine_block.engine_block_id",
                "LEFT JOIN vcdb.fuel_type ON vehicle.fuel_type_id = fuel_type.fuel_type_id",
                "LEFT JOIN vcdb.aspiration ON vehicle.aspiration_id = aspiration.aspiration_id",
                "LEFT JOIN vcdb.body_type ON vehicle.body_type_id = body_type.body_type_id",
                "LEFT JOIN vcdb.drive_type ON vehicle.drive_type_id = drive_type.drive_type_id",
                "LEFT JOIN vcdb.brake_system ON vehicle.brake_system_id = brake_system.brake_system_id"
            ]

            for join_clause in standard_joins:
                base_query = base_query.join_from(None, text(join_clause))

            # Add filter criteria
            where_clauses = []

            # Basic vehicle filters
            if filters.year_ids:
                where_clauses.append(text("year.year_id IN :year_ids"))

            if filters.use_year_range and filters.year_range_start and filters.year_range_end:
                where_clauses.append(text("year.year_id BETWEEN :year_range_start AND :year_range_end"))

            if filters.make_ids:
                where_clauses.append(text("make.make_id IN :make_ids"))

            if filters.model_ids:
                where_clauses.append(text("model.model_id IN :model_ids"))

            if filters.sub_model_ids:
                where_clauses.append(text("sub_model.sub_model_id IN :sub_model_ids"))

            if filters.region_ids:
                where_clauses.append(text("region.region_id IN :region_ids"))

            # Engine filters
            if filters.engine_block_ids:
                where_clauses.append(text("engine_block.engine_block_id IN :engine_block_ids"))

            if filters.fuel_type_ids:
                where_clauses.append(text("fuel_type.fuel_type_id IN :fuel_type_ids"))

            if filters.aspiration_ids:
                where_clauses.append(text("aspiration.aspiration_id IN :aspiration_ids"))

            # Engine specific values
            if filters.engine_liters:
                where_clauses.append(text("engine_block.liter IN :engine_liters"))

            if filters.engine_cylinders:
                where_clauses.append(text("engine_block.cylinders IN :engine_cylinders"))

            # Body filters
            if filters.body_type_ids:
                where_clauses.append(text("body_type.body_type_id IN :body_type_ids"))

            # Apply all filter conditions
            if where_clauses:
                for clause in where_clauses:
                    base_query = base_query.where(clause)

            # Add parameters
            params = {}
            for attr_name, attr_value in filters.__dict__.items():
                if attr_name.startswith('_'):
                    continue
                if attr_value is not None and not (isinstance(attr_value, list) and len(attr_value) == 0):
                    params[attr_name] = attr_value

            # Apply limit
            if limit is not None:
                base_query = base_query.limit(limit)

            # Add parameter binds
            for param_name, param_value in params.items():
                base_query = base_query.params(**{param_name: param_value})

            return base_query
        except Exception as e:
            raise QueryExecutionError(f"Error building vehicle query: {e}") from e

    def build_filter_value_query(
        self,
        table_name: str,
        id_column: str,
        value_column: str,
        filters: Optional[FilterDTO] = None
    ) -> Select:
        """Build a query to get filter values from a table.

        Args:
            table_name: Database table name
            id_column: ID column name
            value_column: Display value column name
            filters: Optional filters to apply

        Returns:
            SQLAlchemy Select object

        Raises:
            QueryExecutionError: If query building fails
        """
        try:
            # Basic query to get values
            query = select(
                text(f"{table_name}.{id_column}"),
                text(f"{table_name}.{value_column}")
            ).select_from(text(f"vcdb.{table_name}"))

            # Apply filters if provided
            if filters:
                query = self._apply_dependent_filters(query, table_name, filters)

            # Add sorting
            query = query.order_by(text(f"{table_name}.{value_column}"))

            return query
        except Exception as e:
            raise QueryExecutionError(f"Error building filter value query: {e}") from e

    def _apply_dependent_filters(
        self,
        query: Select,
        target_table: str,
        filters: FilterDTO
    ) -> Select:
        """Apply dependent filters based on the target table.

        Args:
            query: Base query
            target_table: Target table being filtered
            filters: Filter criteria

        Returns:
            Updated query with dependent filters
        """
        # Dependencies between tables
        dependencies = {
            "make": [("year", "year_id")],
            "model": [("year", "year_id"), ("make", "make_id")],
            "sub_model": [("year", "year_id"), ("make", "make_id"), ("model", "model_id")],
            "engine_block": [("year", "year_id"), ("make", "make_id"), ("model", "model_id")],
            "body_type": [("year", "year_id"), ("make", "make_id"), ("model", "model_id")]
        }

        if target_table in dependencies:
            # Get joins and filters for this table
            for dep_table, dep_column in dependencies[target_table]:
                # Check if we have a filter value for this dependency
                filter_field = f"{dep_column}s"
                filter_values = getattr(filters, filter_field, [])

                if filter_values:
                    # Add join if needed
                    query = query.join(
                        text(f"vcdb.{dep_table}"),
                        text(f"{target_table}.{dep_column} = {dep_table}.{dep_column}"),
                        isouter=True
                    )

                    # Add where clause
                    query = query.where(text(f"{dep_table}.{dep_column} IN :{filter_field}"))

                    # Add parameter
                    query = query.params(**{filter_field: filter_values})

        return query


# Create singleton instance
query_builder = VehicleQueryBuilder()