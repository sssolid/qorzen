#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VCdb Explorer database operations module.

This module handles all database operations for the VCdb Explorer plugin,
including connection setup, querying, and filter value retrieval.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import create_engine, select, func, and_, or_, between, text
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError

# Import VCdb models
from .models import (
    Vehicle, Year, Make, Model, SubModel, DriveType, BrakeConfig, BedConfig,
    BodyStyleConfig, MfrBodyCode, EngineConfig2, SpringTypeConfig,
    SteeringConfig, Transmission, WheelBase, Class, Region, BaseVehicle,
    VehicleTypeGroup, VehicleType, PublicationStage
)


@dataclass
class FilterValue:
    """Represents a single filter value."""
    id: int
    name: str
    count: int = 0


class DatabaseError(Exception):
    """Exception raised for database errors."""
    pass


class VCdbDatabase:
    """VCdb database operations manager.

    Handles database connections, queries, and filter operations for VCdb data.
    """

    def __init__(
            self,
            host: str,
            port: int,
            database: str,
            user: str,
            password: str,
            logger: logging.Logger
    ) -> None:
        """Initialize the VCdb database manager.

        Args:
            host: Database server hostname
            port: Database server port
            database: Database name
            user: Database username
            password: Database password
            logger: Logger instance
        """
        self._logger = logger
        self._connection_string = (
            f"postgresql://{user}:{password}@{host}:{port}/{database}"
        )
        self._engine = None
        self._initialized = False

        # Dictionary mapping filter types to their model and column
        self._filter_map = {
            "year": (Year, "year_id"),
            "make": (Make, "make_name"),
            "model": (Model, "model_name"),
            "submodel": (SubModel, "sub_model_name"),
            "region": (Region, "region_name"),
            "drivetype": (DriveType, "drive_type_name"),
            "vehicletype": (VehicleType, "vehicle_type_name"),
            "vehicletypegroup": (VehicleTypeGroup, "vehicle_type_group_name"),
            "publicationstage": (PublicationStage, "publication_stage_name"),
            "class": (Class, "class_name"),
            "wheelbase": (WheelBase, "wheel_base"),
        }

    def initialize(self) -> None:
        """Initialize the database connection."""
        if self._initialized:
            return

        try:
            self._engine = create_engine(
                self._connection_string,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
            )
            # Test connection
            with self.session() as session:
                # Quick test query
                result = session.execute(select(func.count()).select_from(Vehicle)).scalar()
                self._logger.info(f"Connected to database. Vehicle count: {result}")

            self._initialized = True
        except Exception as e:
            self._logger.error(f"Failed to connect to database: {str(e)}")
            raise DatabaseError(f"Failed to connect to database: {str(e)}") from e

    def shutdown(self) -> None:
        """Shut down the database connection."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        self._initialized = False

    @contextmanager
    def session(self) -> Session:
        """Create a database session context manager.

        Yields:
            A SQLAlchemy session object

        Raises:
            DatabaseError: If a database error occurs
        """
        if not self._engine:
            raise DatabaseError("Database not initialized")

        session = Session(self._engine)
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            self._logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}") from e
        finally:
            session.close()

    def get_filter_values(
            self,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            exclude_filters: Optional[Set[str]] = None
    ) -> List[FilterValue]:
        """Get available values for a specific filter type based on current filters.

        Args:
            filter_type: The type of filter to get values for
            current_filters: Dictionary of currently selected filter values
            exclude_filters: Set of filter types to exclude when applying constraints

        Returns:
            List of FilterValue objects containing available values

        Raises:
            DatabaseError: If a database error occurs
        """
        if not self._initialized:
            raise DatabaseError("Database not initialized")

        if exclude_filters is None:
            exclude_filters = set()

        try:
            # Get the model and attribute name for this filter type
            if filter_type not in self._filter_map:
                raise DatabaseError(f"Unknown filter type: {filter_type}")

            model_class, attr_name = self._filter_map[filter_type]

            with self.session() as session:
                # Start building the query
                if filter_type == "year":
                    # For years, we want the year_id directly from BaseVehicle
                    query = (
                        select(
                            Year.year_id.label("id"),
                            Year.year_id.label("name"),
                            func.count(Year.year_id).label("count")
                        )
                        .join(BaseVehicle, BaseVehicle.year_id == Year.year_id)
                        .join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        .group_by(Year.year_id)
                        .order_by(Year.year_id)
                    )
                elif filter_type == "make":
                    # For makes, join through BaseVehicle
                    query = (
                        select(
                            Make.make_id.label("id"),
                            Make.make_name.label("name"),
                            func.count(Make.make_id).label("count")
                        )
                        .join(BaseVehicle, BaseVehicle.make_id == Make.make_id)
                        .join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        .group_by(Make.make_id, Make.make_name)
                        .order_by(Make.make_name)
                    )
                elif filter_type == "model":
                    # For models, join through BaseVehicle
                    query = (
                        select(
                            Model.model_id.label("id"),
                            Model.model_name.label("name"),
                            func.count(Model.model_id).label("count")
                        )
                        .join(BaseVehicle, BaseVehicle.model_id == Model.model_id)
                        .join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        .group_by(Model.model_id, Model.model_name)
                        .order_by(Model.model_name)
                    )
                elif filter_type == "submodel":
                    # For submodels, join directly to Vehicle
                    query = (
                        select(
                            SubModel.sub_model_id.label("id"),
                            SubModel.sub_model_name.label("name"),
                            func.count(SubModel.sub_model_id).label("count")
                        )
                        .join(Vehicle, Vehicle.sub_model_id == SubModel.sub_model_id)
                        .group_by(SubModel.sub_model_id, SubModel.sub_model_name)
                        .order_by(SubModel.sub_model_name)
                    )
                elif filter_type == "region":
                    # For regions, join directly to Vehicle
                    query = (
                        select(
                            Region.region_id.label("id"),
                            Region.region_name.label("name"),
                            func.count(Region.region_id).label("count")
                        )
                        .join(Vehicle, Vehicle.region_id == Region.region_id)
                        .group_by(Region.region_id, Region.region_name)
                        .order_by(Region.region_name)
                    )
                elif filter_type == "drivetype":
                    # For drive types, join through the many-to-many relationship
                    query = (
                        select(
                            DriveType.drive_type_id.label("id"),
                            DriveType.drive_type_name.label("name"),
                            func.count(DriveType.drive_type_id).label("count")
                        )
                        .join(Vehicle.drive_types)
                        .group_by(DriveType.drive_type_id, DriveType.drive_type_name)
                        .order_by(DriveType.drive_type_name)
                    )
                else:
                    # Generic handling for other filter types
                    query = (
                        select(
                            getattr(model_class, model_class.__table__.primary_key.columns.keys()[0]).label("id"),
                            getattr(model_class, attr_name).label("name"),
                            func.count(getattr(model_class, model_class.__table__.primary_key.columns.keys()[0])).label(
                                "count")
                        )
                        .group_by(
                            getattr(model_class, model_class.__table__.primary_key.columns.keys()[0]),
                            getattr(model_class, attr_name)
                        )
                        .order_by(getattr(model_class, attr_name))
                    )

                # Apply current filters to constrain the query
                query = self._apply_filters(query, current_filters, exclude_filters, model_class)

                # Execute query and convert results
                results = []
                for row in session.execute(query).all():
                    results.append(FilterValue(
                        id=row.id,
                        name=str(row.name),
                        count=row.count
                    ))

                return results

        except SQLAlchemyError as e:
            self._logger.error(f"Error getting filter values for {filter_type}: {str(e)}")
            raise DatabaseError(f"Error getting filter values for {filter_type}: {str(e)}") from e

    def _apply_filters(
            self,
            query: Select,
            filters: Dict[str, List[int]],
            exclude_filters: Set[str],
            target_model: Any = None
    ) -> Select:
        """Apply filters to a query.

        Args:
            query: The base SQLAlchemy query
            filters: Dictionary of filter type to list of selected values
            exclude_filters: Set of filter types to exclude from query
            target_model: Optional model class that this query is targeting

        Returns:
            Modified SQLAlchemy query with filters applied
        """
        if not filters:
            return query

        for filter_type, values in filters.items():
            if not values or filter_type in exclude_filters:
                continue

            # Skip if this is the target model we're querying for
            if target_model and filter_type in self._filter_map and self._filter_map[filter_type][0] == target_model:
                continue

            if filter_type == "year":
                # Year filter affects BaseVehicle
                if BaseVehicle not in [mapper.class_ for mapper in query._from_obj]:
                    query = query.join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                    query = query.join(BaseVehicle, BaseVehicle.base_vehicle_id == Vehicle.base_vehicle_id)

                # Handle year range
                if len(values) == 2 and values[0] <= values[1]:
                    query = query.filter(BaseVehicle.year_id.between(values[0], values[1]))
                else:
                    query = query.filter(BaseVehicle.year_id.in_(values))

            elif filter_type == "make":
                # Make filter affects BaseVehicle
                if BaseVehicle not in [mapper.class_ for mapper in query._from_obj]:
                    query = query.join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                    query = query.join(BaseVehicle, BaseVehicle.base_vehicle_id == Vehicle.base_vehicle_id)

                query = query.filter(BaseVehicle.make_id.in_(values))

            elif filter_type == "model":
                # Model filter affects BaseVehicle
                if BaseVehicle not in [mapper.class_ for mapper in query._from_obj]:
                    query = query.join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                    query = query.join(BaseVehicle, BaseVehicle.base_vehicle_id == Vehicle.base_vehicle_id)

                query = query.filter(BaseVehicle.model_id.in_(values))

            elif filter_type == "submodel":
                # Submodel filter directly affects Vehicle
                query = query.filter(Vehicle.sub_model_id.in_(values))

            elif filter_type == "region":
                # Region filter directly affects Vehicle
                query = query.filter(Vehicle.region_id.in_(values))

            elif filter_type == "drivetype":
                # Drive type is a many-to-many relationship
                drive_type_alias = aliased(DriveType)
                query = query.join(drive_type_alias, Vehicle.drive_types)
                query = query.filter(drive_type_alias.drive_type_id.in_(values))

            # Other filters would follow similar patterns...

        return query

    def execute_query(
            self,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            page: int = 1,
            page_size: int = 100,
            sort_by: Optional[str] = None,
            sort_desc: bool = False,
            table_filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Execute a query with the given filters and return paginated results.

        Args:
            filter_panels: List of filter dictionaries (one per panel)
            columns: List of column names to include in results
            page: Page number (1-indexed)
            page_size: Number of results per page
            sort_by: Column to sort by
            sort_desc: Whether to sort in descending order
            table_filters: Additional filters to apply to the result table

        Returns:
            Tuple of (results list, total count)

        Raises:
            DatabaseError: If a database error occurs
        """
        if not self._initialized:
            raise DatabaseError("Database not initialized")

        try:
            with self.session() as session:
                # Start with a base query for Vehicle IDs
                base_query = select(Vehicle.vehicle_id)

                # Apply filter panels using OR between panels and AND within each panel
                if filter_panels:
                    panel_conditions = []
                    for panel in filter_panels:
                        if not panel:  # Skip empty panels
                            continue

                        panel_query = select(Vehicle.vehicle_id)
                        panel_query = self._apply_filters(panel_query, panel, set())
                        panel_conditions.append(Vehicle.vehicle_id.in_(panel_query.scalar_subquery()))

                    if panel_conditions:
                        base_query = base_query.filter(or_(*panel_conditions))

                # Count total results
                count_query = select(func.count()).select_from(base_query.alias())
                total_count = session.execute(count_query).scalar() or 0

                # Prepare the main query with all requested columns
                query = self._build_columns_query(base_query, columns)

                # Apply table filters
                if table_filters:
                    query = self._apply_table_filters(query, table_filters)

                # Apply sorting
                if sort_by:
                    query = self._apply_sorting(query, sort_by, sort_desc)

                # Apply pagination
                query = query.offset((page - 1) * page_size).limit(page_size)

                # Execute query and format results
                result_rows = session.execute(query).all()
                results = []

                for row in result_rows:
                    # Convert row to dictionary
                    result = {}
                    for i, col in enumerate(query.columns):
                        col_name = col.name
                        value = row[i]
                        result[col_name] = value
                    results.append(result)

                return results, total_count

        except SQLAlchemyError as e:
            self._logger.error(f"Error executing query: {str(e)}")
            raise DatabaseError(f"Error executing query: {str(e)}") from e

    def _build_columns_query(self, base_query: Select, columns: List[str]) -> Select:
        """Build a query with the requested columns.

        Args:
            base_query: Base query with vehicle IDs
            columns: List of column names to include

        Returns:
            SQLAlchemy query with columns added
        """
        # Always include vehicle_id
        vehicle_subq = base_query.scalar_subquery()
        query = select(Vehicle.vehicle_id)
        query = query.filter(Vehicle.vehicle_id.in_(vehicle_subq))

        # Add the make relationship
        query = query.add_columns(
            Make.make_id.label("make_id"),
            Make.make_name.label("make")
        ).join(
            BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
        ).join(
            Make, BaseVehicle.make_id == Make.make_id
        )

        # Add year
        query = query.add_columns(
            Year.year_id.label("year")
        ).join(
            Year, BaseVehicle.year_id == Year.year_id
        )

        # Add model
        query = query.add_columns(
            Model.model_id.label("model_id"),
            Model.model_name.label("model")
        ).join(
            Model, BaseVehicle.model_id == Model.model_id
        )

        # Add submodel
        query = query.add_columns(
            SubModel.sub_model_id.label("submodel_id"),
            SubModel.sub_model_name.label("submodel")
        ).join(
            SubModel, Vehicle.sub_model_id == SubModel.sub_model_id
        )

        # Add additional columns based on user selection
        for column in columns:
            if column == "region":
                query = query.add_columns(
                    Region.region_id.label("region_id"),
                    Region.region_name.label("region")
                ).outerjoin(
                    Region, Vehicle.region_id == Region.region_id
                )
            elif column == "vehicle_type":
                query = query.add_columns(
                    VehicleType.vehicle_type_id.label("vehicle_type_id"),
                    VehicleType.vehicle_type_name.label("vehicle_type")
                ).outerjoin(
                    VehicleType, Model.vehicle_type_id == VehicleType.vehicle_type_id
                )
            # Add more column handling as needed

        return query

    def _apply_table_filters(self, query: Select, table_filters: Dict[str, Any]) -> Select:
        """Apply additional filters to the result table.

        Args:
            query: Base query with columns
            table_filters: Dictionary of column-based filters

        Returns:
            SQLAlchemy query with table filters applied
        """
        for column, filter_value in table_filters.items():
            if column == "year" and isinstance(filter_value, dict):
                # Handle year range
                min_year = filter_value.get("min")
                max_year = filter_value.get("max")
                if min_year is not None and max_year is not None:
                    query = query.filter(Year.year_id.between(min_year, max_year))
                elif min_year is not None:
                    query = query.filter(Year.year_id >= min_year)
                elif max_year is not None:
                    query = query.filter(Year.year_id <= max_year)
            elif column == "make" and isinstance(filter_value, str):
                # Text search on make
                query = query.filter(Make.make_name.ilike(f"%{filter_value}%"))
            elif column == "model" and isinstance(filter_value, str):
                # Text search on model
                query = query.filter(Model.model_name.ilike(f"%{filter_value}%"))
            elif column == "submodel" and isinstance(filter_value, str):
                # Text search on submodel
                query = query.filter(SubModel.sub_model_name.ilike(f"%{filter_value}%"))

        return query

    def _apply_sorting(self, query: Select, sort_by: str, sort_desc: bool) -> Select:
        """Apply sorting to the query.

        Args:
            query: Base query with columns
            sort_by: Column name to sort by
            sort_desc: Whether to sort in descending order

        Returns:
            SQLAlchemy query with sorting applied
        """
        # Map column names to their SQLAlchemy column objects
        sort_map = {
            "vehicle_id": Vehicle.vehicle_id,
            "year": Year.year_id,
            "make": Make.make_name,
            "model": Model.model_name,
            "submodel": SubModel.sub_model_name,
            "region": Region.region_name,
        }

        if sort_by in sort_map:
            sort_col = sort_map[sort_by]
            if sort_desc:
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())

        return query

    def get_available_columns(self) -> List[Dict[str, str]]:
        """Get a list of available columns that can be selected for the result table.

        Returns:
            List of dictionaries with column id and name
        """
        return [
            {"id": "vehicle_id", "name": "Vehicle ID"},
            {"id": "year", "name": "Year"},
            {"id": "make", "name": "Make"},
            {"id": "model", "name": "Model"},
            {"id": "submodel", "name": "Submodel"},
            {"id": "region", "name": "Region"},
            {"id": "vehicle_type", "name": "Vehicle Type"},
            {"id": "drive_type", "name": "Drive Type"},
            {"id": "brake_system", "name": "Brake System"},
            {"id": "body_type", "name": "Body Type"},
            {"id": "engine", "name": "Engine"},
            {"id": "transmission", "name": "Transmission"},
            {"id": "wheel_base", "name": "Wheel Base"},
        ]

    def get_available_filters(self) -> List[Dict[str, str]]:
        """Get a list of available filters that can be added to the filter panel.

        Returns:
            List of dictionaries with filter id and name
        """
        return [
            {"id": "year", "name": "Year", "mandatory": True},
            {"id": "year_range", "name": "Year Range", "mandatory": True},
            {"id": "make", "name": "Make", "mandatory": True},
            {"id": "model", "name": "Model", "mandatory": True},
            {"id": "submodel", "name": "Submodel", "mandatory": True},
            {"id": "region", "name": "Region", "mandatory": False},
            {"id": "drivetype", "name": "Drive Type", "mandatory": False},
            {"id": "vehicletype", "name": "Vehicle Type", "mandatory": False},
            {"id": "brakesystem", "name": "Brake System", "mandatory": False},
            {"id": "bodytype", "name": "Body Type", "mandatory": False},
            {"id": "wheelbase", "name": "Wheel Base", "mandatory": False},
            {"id": "class", "name": "Vehicle Class", "mandatory": False},
        ]