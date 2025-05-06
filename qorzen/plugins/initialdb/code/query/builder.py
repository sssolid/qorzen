from __future__ import annotations

"""
Query builder for vehicle database.

This module provides a simplified query building system for filtering and
retrieving vehicle data, with a focus on maintainability and type safety.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from sqlalchemy import and_, func, or_, select
from sqlalchemy.sql.selectable import Select

from ..models.vehicle import (
    Aspiration, Base, BaseVehicle, BodyStyleConfig, BodyType, EngineBlock,
    EngineConfig, FuelType, Make, Model, Region, SubModel, Transmission,
    Vehicle, VehicleToBodyStyleConfig, VehicleToEngineConfig, Year
)


@dataclass
class FilterParams:
    """
    Data class for filter parameters.

    This simplifies passing around filter criteria and makes it clear
    what fields are available for filtering.
    """
    year_ids: List[int] = field(default_factory=list)
    year_range_start: Optional[int] = None
    year_range_end: Optional[int] = None
    make_ids: List[int] = field(default_factory=list)
    model_ids: List[int] = field(default_factory=list)
    sub_model_ids: List[int] = field(default_factory=list)
    region_ids: List[int] = field(default_factory=list)

    # Engine filters
    engine_block_ids: List[int] = field(default_factory=list)
    engine_liters: List[str] = field(default_factory=list)
    engine_cylinders: List[str] = field(default_factory=list)
    fuel_type_ids: List[int] = field(default_factory=list)
    aspiration_ids: List[int] = field(default_factory=list)

    # Body filters
    body_type_ids: List[int] = field(default_factory=list)

    # Transmission filters
    transmission_type_ids: List[int] = field(default_factory=list)

    def has_filters(self) -> bool:
        """
        Check if any filters are active.

        Returns:
            bool: True if any filters are set, False otherwise
        """
        # Check normal ID lists
        for attr_name in dir(self):
            if attr_name.endswith('_ids') and isinstance(getattr(self, attr_name), list):
                if getattr(self, attr_name):
                    return True

        # Check engine attribute lists
        if self.engine_liters or self.engine_cylinders:
            return True

        # Check year range
        if self.year_range_start is not None and self.year_range_end is not None:
            return True

        return False

    def has_basic_vehicle_filters(self) -> bool:
        """
        Check if basic vehicle filters (year, make, model, submodel) are active.

        Returns:
            bool: True if any basic vehicle filters are set
        """
        if self.year_ids or self.make_ids or self.model_ids or self.sub_model_ids:
            return True

        if self.year_range_start is not None and self.year_range_end is not None:
            return True

        return False

    def has_engine_filters(self) -> bool:
        """
        Check if any engine-related filters are active.

        Returns:
            bool: True if any engine filters are set
        """
        return bool(
            self.engine_block_ids or
            self.engine_liters or
            self.engine_cylinders or
            self.fuel_type_ids or
            self.aspiration_ids
        )

    def has_body_filters(self) -> bool:
        """
        Check if any body-related filters are active.

        Returns:
            bool: True if any body filters are set
        """
        return bool(self.body_type_ids)

    def has_transmission_filters(self) -> bool:
        """
        Check if any transmission-related filters are active.

        Returns:
            bool: True if any transmission filters are set
        """
        return bool(self.transmission_type_ids)


class QueryBuilder:
    """
    Builder for vehicle database queries.

    This class provides a simplified interface for building SQLAlchemy queries
    against the vehicle database, with support for common filtering patterns.
    """

    def __init__(self) -> None:
        """Initialize the query builder."""
        pass

    def build_vehicle_query(self,
                            filters: FilterParams,
                            limit: Optional[int] = 1000) -> Select:
        """
        Build a query for retrieving vehicles based on filter criteria.

        Args:
            filters: Filter parameters
            limit: Maximum number of results to return (default: 1000)

        Returns:
            SQLAlchemy Select query
        """
        # Start with base vehicle query
        query = select(Vehicle)

        # Keep track of joined tables to avoid duplicate joins
        joined_tables: Set[str] = set()

        # Apply basic vehicle filters (year, make, model, submodel)
        if filters.has_basic_vehicle_filters():
            if "base_vehicle" not in joined_tables:
                query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                joined_tables.add("base_vehicle")

            # Apply year filters
            if filters.year_ids:
                if "year" not in joined_tables:
                    query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                    joined_tables.add("year")
                query = query.filter(Year.year_id.in_(filters.year_ids))
            elif filters.year_range_start is not None and filters.year_range_end is not None:
                if "year" not in joined_tables:
                    query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                    joined_tables.add("year")
                query = query.filter(Year.year_id.between(filters.year_range_start, filters.year_range_end))

            # Apply make filter
            if filters.make_ids:
                if "make" not in joined_tables:
                    query = query.join(Make, BaseVehicle.make_id == Make.make_id)
                    joined_tables.add("make")
                query = query.filter(Make.make_id.in_(filters.make_ids))

            # Apply model filter
            if filters.model_ids:
                if "model" not in joined_tables:
                    query = query.join(Model, BaseVehicle.model_id == Model.model_id)
                    joined_tables.add("model")
                query = query.filter(Model.model_id.in_(filters.model_ids))

            # Apply submodel filter
            if filters.sub_model_ids:
                query = query.filter(Vehicle.sub_model_id.in_(filters.sub_model_ids))

        # Apply region filter
        if filters.region_ids:
            query = query.filter(Vehicle.region_id.in_(filters.region_ids))

        # Apply engine filters
        if filters.has_engine_filters():
            engine_conditions = []

            # Join to engine tables
            query = query.join(
                VehicleToEngineConfig,
                Vehicle.vehicle_id == VehicleToEngineConfig.vehicle_id
            )
            query = query.join(
                EngineConfig,
                VehicleToEngineConfig.engine_config_id == EngineConfig.engine_config_id
            )
            joined_tables.add("engine_config")

            # Engine block filters
            if filters.engine_block_ids or filters.engine_liters or filters.engine_cylinders:
                if "engine_block" not in joined_tables:
                    query = query.join(
                        EngineBlock,
                        EngineConfig.engine_block_id == EngineBlock.engine_block_id
                    )
                    joined_tables.add("engine_block")

                if filters.engine_block_ids:
                    engine_conditions.append(EngineBlock.engine_block_id.in_(filters.engine_block_ids))
                if filters.engine_liters:
                    engine_conditions.append(EngineBlock.liter.in_(filters.engine_liters))
                if filters.engine_cylinders:
                    engine_conditions.append(EngineBlock.cylinders.in_(filters.engine_cylinders))

            # Fuel type filters
            if filters.fuel_type_ids:
                if "fuel_type" not in joined_tables:
                    query = query.join(
                        FuelType,
                        EngineConfig.fuel_type_id == FuelType.fuel_type_id
                    )
                    joined_tables.add("fuel_type")
                engine_conditions.append(FuelType.fuel_type_id.in_(filters.fuel_type_ids))

            # Aspiration filters
            if filters.aspiration_ids:
                if "aspiration" not in joined_tables:
                    query = query.join(
                        Aspiration,
                        EngineConfig.aspiration_id == Aspiration.aspiration_id
                    )
                    joined_tables.add("aspiration")
                engine_conditions.append(Aspiration.aspiration_id.in_(filters.aspiration_ids))

            # Apply engine conditions if any
            if engine_conditions:
                query = query.filter(and_(*engine_conditions))

        # Apply body filters
        if filters.has_body_filters():
            body_conditions = []

            # Join to body tables
            query = query.join(
                VehicleToBodyStyleConfig,
                Vehicle.vehicle_id == VehicleToBodyStyleConfig.vehicle_id
            )
            query = query.join(
                BodyStyleConfig,
                VehicleToBodyStyleConfig.body_style_config_id == BodyStyleConfig.body_style_config_id
            )
            joined_tables.add("body_style_config")

            # Body type filters
            if filters.body_type_ids:
                if "body_type" not in joined_tables:
                    query = query.join(
                        BodyType,
                        BodyStyleConfig.body_type_id == BodyType.body_type_id
                    )
                    joined_tables.add("body_type")
                body_conditions.append(BodyType.body_type_id.in_(filters.body_type_ids))

            # Apply body conditions if any
            if body_conditions:
                query = query.filter(and_(*body_conditions))

        # Apply limit
        if limit is not None:
            query = query.limit(limit)

        return query

    def build_filter_values_query(self,
                                  table_name: str,
                                  id_column: str,
                                  value_column: str,
                                  filters: Optional[FilterParams] = None) -> Select:
        """
        Build a query for retrieving filter values.

        This method creates a query that returns distinct values for a specific
        column, optionally filtered based on other criteria.

        Args:
            table_name: Name of the table
            id_column: Name of the ID column
            value_column: Name of the value column to display
            filters: Optional filter parameters to apply

        Returns:
            SQLAlchemy Select query
        """
        # Handle special cases with optimized queries
        if table_name == "year":
            query = select(Year.year_id, Year.year_id).distinct().order_by(Year.year_id)
            return query

        if table_name == "make":
            return self._build_make_values_query(filters)

        if table_name == "model":
            return self._build_model_values_query(filters)

        if table_name == "sub_model":
            return self._build_submodel_values_query(filters)

        # For other tables, use a generic approach
        model_class = self._get_model_class(table_name)
        if not model_class:
            # Return an empty query if table not found
            return select(1).where(1 == 0)

        id_attr = getattr(model_class, id_column)
        value_attr = getattr(model_class, value_column)

        query = select(id_attr, value_attr).distinct().order_by(value_attr)

        # Apply filters if they exist and are relevant
        if filters and filters.has_filters():
            query = self._apply_relevant_filters(query, model_class, filters)

        return query

    def _build_make_values_query(self, filters: Optional[FilterParams]) -> Select:
        """Build an optimized query for retrieving make values."""
        query = select(Make.make_id, Make.make_name).distinct().order_by(Make.make_name)

        # Apply filters if they exist and are relevant
        if filters and filters.year_ids:
            query = query.join(BaseVehicle, Make.make_id == BaseVehicle.make_id)
            query = query.join(Year, BaseVehicle.year_id == Year.year_id)
            query = query.filter(Year.year_id.in_(filters.year_ids))
        elif filters and filters.year_range_start is not None and filters.year_range_end is not None:
            query = query.join(BaseVehicle, Make.make_id == BaseVehicle.make_id)
            query = query.join(Year, BaseVehicle.year_id == Year.year_id)
            query = query.filter(Year.year_id.between(filters.year_range_start, filters.year_range_end))

        return query

    def _build_model_values_query(self, filters: Optional[FilterParams]) -> Select:
        """Build an optimized query for retrieving model values."""
        query = select(Model.model_id, Model.model_name).distinct().order_by(Model.model_name)

        # Apply filters if they exist and are relevant
        if filters and (filters.year_ids or filters.make_ids):
            query = query.join(BaseVehicle, Model.model_id == BaseVehicle.model_id)

            if filters.make_ids:
                query = query.filter(BaseVehicle.make_id.in_(filters.make_ids))

            if filters.year_ids:
                query = query.filter(BaseVehicle.year_id.in_(filters.year_ids))
            elif filters.year_range_start is not None and filters.year_range_end is not None:
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                query = query.filter(Year.year_id.between(filters.year_range_start, filters.year_range_end))

        return query

    def _build_submodel_values_query(self, filters: Optional[FilterParams]) -> Select:
        """Build an optimized query for retrieving submodel values."""
        query = select(SubModel.sub_model_id, SubModel.sub_model_name).distinct().order_by(SubModel.sub_model_name)

        # Apply filters if they exist and are relevant
        if filters and (filters.year_ids or filters.make_ids or filters.model_ids):
            query = query.join(Vehicle, SubModel.sub_model_id == Vehicle.sub_model_id)
            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

            if filters.make_ids:
                query = query.filter(BaseVehicle.make_id.in_(filters.make_ids))

            if filters.model_ids:
                query = query.filter(BaseVehicle.model_id.in_(filters.model_ids))

            if filters.year_ids:
                query = query.filter(BaseVehicle.year_id.in_(filters.year_ids))
            elif filters.year_range_start is not None and filters.year_range_end is not None:
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                query = query.filter(Year.year_id.between(filters.year_range_start, filters.year_range_end))

        return query

    def _get_model_class(self, table_name: str) -> Optional[type]:
        """Get the SQLAlchemy model class for a table name."""
        models = {
            "year": Year,
            "make": Make,
            "model": Model,
            "sub_model": SubModel,
            "base_vehicle": BaseVehicle,
            "vehicle": Vehicle,
            "region": Region,
            "engine_block": EngineBlock,
            "engine_config": EngineConfig,
            "fuel_type": FuelType,
            "aspiration": Aspiration,
            "body_type": BodyType,
            "body_style_config": BodyStyleConfig,
            "transmission": Transmission,
        }

        return models.get(table_name)

    def _apply_relevant_filters(self,
                                query: Select,
                                model_class: type,
                                filters: FilterParams) -> Select:
        """
        Apply relevant filters to a query.

        This method determines what filters are relevant to the query based on
        the model class and applies them.

        Args:
            query: SQLAlchemy Select query
            model_class: SQLAlchemy model class
            filters: Filter parameters

        Returns:
            Updated SQLAlchemy Select query
        """
        # For engine-related tables
        if model_class in [EngineBlock, EngineConfig, FuelType, Aspiration]:
            if filters.has_basic_vehicle_filters():
                query = query.join(
                    EngineConfig,
                    getattr(model_class, f"{model_class.__tablename__}_id") == EngineConfig.engine_block_id
                    if model_class == EngineBlock else
                    getattr(EngineConfig, f"{model_class.__tablename__}_id") == getattr(model_class,
                                                                                        f"{model_class.__tablename__}_id")
                )
                query = query.join(VehicleToEngineConfig,
                                   EngineConfig.engine_config_id == VehicleToEngineConfig.engine_config_id)
                query = query.join(Vehicle, VehicleToEngineConfig.vehicle_id == Vehicle.vehicle_id)
                query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

                if filters.year_ids:
                    query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                    query = query.filter(Year.year_id.in_(filters.year_ids))
                elif filters.year_range_start is not None and filters.year_range_end is not None:
                    query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                    query = query.filter(Year.year_id.between(filters.year_range_start, filters.year_range_end))

                if filters.make_ids:
                    query = query.filter(BaseVehicle.make_id.in_(filters.make_ids))

                if filters.model_ids:
                    query = query.filter(BaseVehicle.model_id.in_(filters.model_ids))

                if filters.sub_model_ids:
                    query = query.filter(Vehicle.sub_model_id.in_(filters.sub_model_ids))

        # For body-related tables
        elif model_class in [BodyType, BodyStyleConfig]:
            if filters.has_basic_vehicle_filters():
                query = query.join(
                    BodyStyleConfig,
                    getattr(model_class, f"{model_class.__tablename__}_id") == BodyStyleConfig.body_type_id
                    if model_class == BodyType else
                    True
                )
                query = query.join(VehicleToBodyStyleConfig,
                                   BodyStyleConfig.body_style_config_id == VehicleToBodyStyleConfig.body_style_config_id)
                query = query.join(Vehicle, VehicleToBodyStyleConfig.vehicle_id == Vehicle.vehicle_id)
                query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

                if filters.year_ids:
                    query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                    query = query.filter(Year.year_id.in_(filters.year_ids))
                elif filters.year_range_start is not None and filters.year_range_end is not None:
                    query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                    query = query.filter(Year.year_id.between(filters.year_range_start, filters.year_range_end))

                if filters.make_ids:
                    query = query.filter(BaseVehicle.make_id.in_(filters.make_ids))

                if filters.model_ids:
                    query = query.filter(BaseVehicle.model_id.in_(filters.model_ids))

                if filters.sub_model_ids:
                    query = query.filter(Vehicle.sub_model_id.in_(filters.sub_model_ids))

        return query


# Create a singleton instance
query_builder = QueryBuilder()