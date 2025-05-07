from __future__ import annotations

"""
Query builder for the InitialDB application.

This module provides a unified query builder for constructing database queries
in a structured and maintainable way, with optimizations for the vehicle database.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, cast
import functools
import structlog
from sqlalchemy import Column, and_, or_, select, join, outerjoin, func, text, case
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import aliased
from sqlalchemy.sql.selectable import Select

from ..models.base_class import Base
from ..models.schema import FilterDTO
from ..utils.dependency_container import resolve
from ..utils.schema_registry import SchemaRegistry

logger = structlog.get_logger(__name__)


class JoinTracker:
    def __init__(self) -> None:
        self.joined_tables: Set[str] = set()
        self.join_aliases: Dict[str, Any] = {}

    def is_joined(self, table_name: str) -> bool:
        return table_name in self.joined_tables

    def mark_joined(self, table_name: str) -> None:
        self.joined_tables.add(table_name)

    def get_alias(self, alias_name: str) -> Optional[Any]:
        return self.join_aliases.get(alias_name)

    def add_alias(self, alias_name: str, alias: Any) -> None:
        self.join_aliases[alias_name] = alias


class QueryBuilder:
    # Explicitly set schema name
    SCHEMA_NAME = 'vcdb'

    def __init__(self) -> None:
        from ..models import models
        self._registry = resolve(SchemaRegistry)
        self._models = models
        logger.debug(f'QueryBuilder initialized with schema name: {self.SCHEMA_NAME}')

    def _get_table(self, table_name: str) -> Any:
        model_class = self._registry.get_model_for_table(table_name)
        if not model_class:
            logger.error(f'Model not found for table: {table_name}')
            return None

        try:
            schema = getattr(model_class.__table__, 'schema', None)
            full_name = getattr(model_class.__table__, 'fullname', None)
            # Always ensure schema is set
            if not schema:
                setattr(model_class.__table__, 'schema', self.SCHEMA_NAME)

            logger.debug(f'Found model for {table_name}: schema={self.SCHEMA_NAME}, fullname={full_name}')
        except Exception as e:
            logger.warning(f'Error accessing model attributes: {e}')

        return model_class.__table__

    def _build_make_filter_query(self, filters: Optional[FilterDTO], id_attr: Any, value_attr: Any) -> Select:
        Make = self._registry.get_model_for_table('make')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')
        Year = self._registry.get_model_for_table('year')

        # Explicitly build query with schema qualification
        query = select(id_attr, value_attr).distinct()

        if filters:
            if filters.year_ids:
                query = query.join(BaseVehicle, BaseVehicle.make_id == Make.make_id)
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                query = query.where(Year.year_id.in_(filters.year_ids))
            elif filters.use_year_range and filters.year_range_start is not None and (
                    filters.year_range_end is not None):
                query = query.join(BaseVehicle, BaseVehicle.make_id == Make.make_id)
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                query = query.where(Year.year_id.between(filters.year_range_start, filters.year_range_end))

        return query.order_by(value_attr)

    def _build_model_filter_query(self, filters: Optional[FilterDTO], id_attr: Any, value_attr: Any) -> Select:
        Model = self._registry.get_model_for_table('model')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')
        Make = self._registry.get_model_for_table('make')
        Year = self._registry.get_model_for_table('year')

        query = select(id_attr, value_attr).distinct()
        query = query.join(BaseVehicle, BaseVehicle.model_id == Model.model_id)

        conditions = []
        if filters:
            if filters.make_ids:
                query = query.join(Make, BaseVehicle.make_id == Make.make_id)
                conditions.append(Make.make_id.in_(filters.make_ids))
            if filters.year_ids:
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                conditions.append(Year.year_id.in_(filters.year_ids))
            elif filters.use_year_range and filters.year_range_start is not None and (
                    filters.year_range_end is not None):
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                conditions.append(Year.year_id.between(filters.year_range_start, filters.year_range_end))

        if conditions:
            query = query.where(and_(*conditions))

        return query.order_by(value_attr)

    def _build_submodel_filter_query(self, filters: Optional[FilterDTO], id_attr: Any, value_attr: Any) -> Select:
        SubModel = self._registry.get_model_for_table('sub_model')
        Vehicle = self._registry.get_model_for_table('vehicle')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')
        Model = self._registry.get_model_for_table('model')
        Make = self._registry.get_model_for_table('make')
        Year = self._registry.get_model_for_table('year')

        query = select(id_attr, value_attr).distinct()

        if filters and self._should_apply_filters(filters):
            query = query.select_from(SubModel)
            query = query.join(Vehicle, Vehicle.sub_model_id == SubModel.sub_model_id)
            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

            conditions = []
            if filters.model_ids:
                query = query.join(Model, BaseVehicle.model_id == Model.model_id)
                conditions.append(Model.model_id.in_(filters.model_ids))
            if filters.make_ids:
                query = query.join(Make, BaseVehicle.make_id == Make.make_id)
                conditions.append(Make.make_id.in_(filters.make_ids))
            if filters.year_ids:
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                conditions.append(Year.year_id.in_(filters.year_ids))
            elif filters.use_year_range and filters.year_range_start is not None and (
                    filters.year_range_end is not None):
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                conditions.append(Year.year_id.between(filters.year_range_start, filters.year_range_end))

            if conditions:
                query = query.where(and_(*conditions))

        return query.order_by(value_attr)

    def _build_engine_block_filter_query(self, filters: Optional[FilterDTO], id_attr: Any, value_attr: Any) -> Select:
        EngineBlock = self._registry.get_model_for_table('engine_block')
        EngineConfig2 = self._registry.get_model_for_table('engine_config2')
        VehicleToEngineConfig = self._registry.get_model_for_table('vehicle_to_engine_config')
        Vehicle = self._registry.get_model_for_table('vehicle')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')
        Year = self._registry.get_model_for_table('year')
        Make = self._registry.get_model_for_table('make')
        Model = self._registry.get_model_for_table('model')
        SubModel = self._registry.get_model_for_table('sub_model')

        query = select(id_attr, value_attr).distinct()

        if filters and self._should_apply_filters(filters):
            query = query.select_from(EngineBlock)
            query = query.join(EngineConfig2, EngineConfig2.engine_block_id == EngineBlock.engine_block_id)
            query = query.join(VehicleToEngineConfig,
                               VehicleToEngineConfig.engine_config_id == EngineConfig2.engine_config_id)
            query = query.join(Vehicle, Vehicle.vehicle_id == VehicleToEngineConfig.vehicle_id)
            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

            conditions = []
            if filters.year_ids:
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                conditions.append(Year.year_id.in_(filters.year_ids))
            elif filters.use_year_range and filters.year_range_start is not None and (
                    filters.year_range_end is not None):
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                conditions.append(Year.year_id.between(filters.year_range_start, filters.year_range_end))
            if filters.make_ids:
                query = query.join(Make, BaseVehicle.make_id == Make.make_id)
                conditions.append(Make.make_id.in_(filters.make_ids))
            if filters.model_ids:
                query = query.join(Model, BaseVehicle.model_id == Model.model_id)
                conditions.append(Model.model_id.in_(filters.model_ids))
            if filters.sub_model_ids:
                query = query.join(SubModel, Vehicle.sub_model_id == SubModel.sub_model_id)
                conditions.append(SubModel.sub_model_id.in_(filters.sub_model_ids))

            if conditions:
                query = query.where(and_(*conditions))

        return query.order_by(value_attr)

    def _build_fuel_type_filter_query(self, filters: Optional[FilterDTO], id_attr: Any, value_attr: Any) -> Select:
        FuelType = self._registry.get_model_for_table('fuel_type')
        EngineConfig2 = self._registry.get_model_for_table('engine_config2')
        VehicleToEngineConfig = self._registry.get_model_for_table('vehicle_to_engine_config')
        Vehicle = self._registry.get_model_for_table('vehicle')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')

        query = select(id_attr, value_attr).distinct()

        if filters and self._should_apply_filters(filters):
            query = query.select_from(FuelType)
            query = query.join(EngineConfig2, EngineConfig2.fuel_type_id == FuelType.fuel_type_id)
            query = query.join(VehicleToEngineConfig,
                               VehicleToEngineConfig.engine_config_id == EngineConfig2.engine_config_id)
            query = query.join(Vehicle, Vehicle.vehicle_id == VehicleToEngineConfig.vehicle_id)
            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

            conditions = self._build_filter_conditions(filters)
            if conditions:
                query = query.where(and_(*conditions))

        return query.order_by(value_attr)

    def _build_aspiration_filter_query(self, filters: Optional[FilterDTO], id_attr: Any, value_attr: Any) -> Select:
        Aspiration = self._registry.get_model_for_table('aspiration')
        EngineConfig2 = self._registry.get_model_for_table('engine_config2')
        VehicleToEngineConfig = self._registry.get_model_for_table('vehicle_to_engine_config')
        Vehicle = self._registry.get_model_for_table('vehicle')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')

        query = select(id_attr, value_attr).distinct()

        if filters and self._should_apply_filters(filters):
            query = query.select_from(Aspiration)
            query = query.join(EngineConfig2, EngineConfig2.aspiration_id == Aspiration.aspiration_id)
            query = query.join(VehicleToEngineConfig,
                               VehicleToEngineConfig.engine_config_id == EngineConfig2.engine_config_id)
            query = query.join(Vehicle, Vehicle.vehicle_id == VehicleToEngineConfig.vehicle_id)
            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

            conditions = self._build_filter_conditions(filters)
            if conditions:
                query = query.where(and_(*conditions))

        return query.order_by(value_attr)

    def _build_body_type_filter_query(self, filters: Optional[FilterDTO], id_attr: Any, value_attr: Any) -> Select:
        BodyType = self._registry.get_model_for_table('body_type')
        BodyStyleConfig = self._registry.get_model_for_table('body_style_config')
        VehicleToBodyStyleConfig = self._registry.get_model_for_table('vehicle_to_body_style_config')
        Vehicle = self._registry.get_model_for_table('vehicle')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')

        query = select(id_attr, value_attr).distinct()

        if filters and self._should_apply_filters(filters):
            query = query.select_from(BodyType)
            query = query.join(BodyStyleConfig, BodyStyleConfig.body_type_id == BodyType.body_type_id)
            query = query.join(VehicleToBodyStyleConfig,
                               VehicleToBodyStyleConfig.body_style_config_id == BodyStyleConfig.body_style_config_id)
            query = query.join(Vehicle, Vehicle.vehicle_id == VehicleToBodyStyleConfig.vehicle_id)
            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

            conditions = self._build_filter_conditions(filters)
            if conditions:
                query = query.where(and_(*conditions))

        return query.order_by(value_attr)

    def _build_transmission_type_filter_query(self, filters: Optional[FilterDTO], id_attr: Any,
                                              value_attr: Any) -> Select:
        TransmissionType = self._registry.get_model_for_table('transmission_type')
        TransmissionBase = self._registry.get_model_for_table('transmission_base')
        Transmission = self._registry.get_model_for_table('transmission')
        VehicleToTransmission = self._registry.get_model_for_table('vehicle_to_transmission')
        Vehicle = self._registry.get_model_for_table('vehicle')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')

        query = select(id_attr, value_attr).distinct()

        if filters and self._should_apply_filters(filters):
            query = query.select_from(TransmissionType)
            query = query.join(TransmissionBase,
                               TransmissionBase.transmission_type_id == TransmissionType.transmission_type_id)
            query = query.join(Transmission, Transmission.transmission_base_id == TransmissionBase.transmission_base_id)
            query = query.join(VehicleToTransmission,
                               VehicleToTransmission.transmission_id == Transmission.transmission_id)
            query = query.join(Vehicle, Vehicle.vehicle_id == VehicleToTransmission.vehicle_id)
            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)

            conditions = self._build_filter_conditions(filters)
            if conditions:
                query = query.where(and_(*conditions))

        return query.order_by(value_attr)

    def build_filter_value_query(self, table_name: str, id_column: str, value_column: str,
                                 filters: Optional[FilterDTO] = None) -> Select:
        logger.debug('Building filter value query', table=table_name, value_column=value_column, id_column=id_column)

        model_class = self._registry.get_model_for_table(table_name)
        if not model_class:
            logger.error(f'No model found for table {table_name}')
            # Return an empty query rather than None
            return select(text("1")).where(text("1=0"))

        # Always ensure schema is set
        if not hasattr(model_class.__table__, 'schema') or not model_class.__table__.schema:
            model_class.__table__.schema = self.SCHEMA_NAME

        logger.debug(f'Building query for table {table_name}, schema={model_class.__table__.schema}')

        id_attr = getattr(model_class, id_column)
        value_attr = getattr(model_class, value_column)

        if table_name == 'year':
            # Simplify year query for better performance
            query = select(id_attr, id_attr).distinct().order_by(id_attr)
            logger.debug(f'Generated SQL for year query: {query}')
            return query

        # Special handling for common tables
        if table_name == 'make':
            query = self._build_make_filter_query(filters, id_attr, value_attr)
            logger.debug(f'Generated SQL for make query: {query}')
            return query

        elif table_name == 'model':
            query = self._build_model_filter_query(filters, id_attr, value_attr)
            logger.debug(f"Generated SQL for model query: {query}")
            return query

        elif table_name == 'sub_model':
            query = self._build_submodel_filter_query(filters, id_attr, value_attr)
            logger.debug(f"Generated SQL for sub_model query: {query}")
            return query

        elif table_name == 'engine_block':
            query = self._build_engine_block_filter_query(filters, id_attr, value_attr)
            logger.debug(f"Generated SQL for engine_block query: {query}")
            return query

        elif table_name == 'fuel_type':
            query = self._build_fuel_type_filter_query(filters, id_attr, value_attr)
            logger.debug(f"Generated SQL for fuel_type query: {query}")
            return query

        elif table_name == 'aspiration':
            query = self._build_aspiration_filter_query(filters, id_attr, value_attr)
            logger.debug(f"Generated SQL for aspiration query: {query}")
            return query

        elif table_name == 'body_type':
            query = self._build_body_type_filter_query(filters, id_attr, value_attr)
            logger.debug(f"Generated SQL for body_type query: {query}")
            return query

        elif table_name == 'transmission_type':
            query = self._build_transmission_type_filter_query(filters, id_attr, value_attr)
            logger.debug(f"Generated SQL for transmission_type query: {query}")
            return query

        else:
            query = select(id_attr, value_attr).distinct()

            if filters and self._should_apply_filters(filters):
                try:
                    # Add explicit schema qualification to the query
                    primary_key = self._registry.get_primary_key(table_name)
                    Vehicle = self._registry.get_model_for_table('vehicle')
                    BaseVehicle = self._registry.get_model_for_table('base_vehicle')

                    # Ensure schema is set for these tables too
                    if not hasattr(Vehicle.__table__, 'schema') or not Vehicle.__table__.schema:
                        Vehicle.__table__.schema = self.SCHEMA_NAME
                    if not hasattr(BaseVehicle.__table__, 'schema') or not BaseVehicle.__table__.schema:
                        BaseVehicle.__table__.schema = self.SCHEMA_NAME

                    join_path = self._registry.get_join_path(table_name, primary_key) or []

                    if 'vehicle' in join_path or 'base_vehicle' in join_path:
                        query = query.select_from(model_class)

                        if 'vehicle' in join_path:
                            if table_name.startswith('vehicle_to_'):
                                query = query.join(Vehicle, getattr(model_class, 'vehicle_id') == Vehicle.vehicle_id)
                            else:
                                query = query.join(Vehicle)

                        if 'base_vehicle' in join_path:
                            if 'vehicle' in join_path:
                                query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                            else:
                                query = query.join(BaseVehicle)

                        conditions = self._build_filter_conditions(filters)
                        if conditions:
                            query = query.where(and_(*conditions))
                except Exception as e:
                    logger.warning(f'Failed to build filtered query for {table_name}: {str(e)}')

            logger.debug(f'Generated SQL for {table_name} query: {query}')
            return query.order_by(value_attr)

    def _build_filter_conditions(self, filters: Optional[FilterDTO]) -> List[Any]:
        if not filters:
            return []

        Year = self._registry.get_model_for_table('year')
        Make = self._registry.get_model_for_table('make')
        Model = self._registry.get_model_for_table('model')
        SubModel = self._registry.get_model_for_table('sub_model')

        # Ensure schema is set for these tables
        for model in [Year, Make, Model, SubModel]:
            if not hasattr(model.__table__, 'schema') or not model.__table__.schema:
                model.__table__.schema = self.SCHEMA_NAME

        conditions = []
        if filters.year_ids:
            conditions.append(Year.year_id.in_(filters.year_ids))
        elif filters.use_year_range and filters.year_range_start is not None and (filters.year_range_end is not None):
            conditions.append(Year.year_id.between(filters.year_range_start, filters.year_range_end))

        if filters.make_ids:
            conditions.append(Make.make_id.in_(filters.make_ids))

        if filters.model_ids:
            conditions.append(Model.model_id.in_(filters.model_ids))

        if filters.sub_model_ids:
            conditions.append(SubModel.sub_model_id.in_(filters.sub_model_ids))

        return conditions

    def _should_apply_filters(self, filters: FilterDTO) -> bool:
        has_year_filter = filters.year_ids or (filters.use_year_range and filters.year_range_start is not None and (
                    filters.year_range_end is not None))
        has_make_filter = bool(filters.make_ids)
        has_model_filter = bool(filters.model_ids)
        has_sub_model_filter = bool(filters.sub_model_ids)

        return has_year_filter or has_make_filter or has_model_filter or has_sub_model_filter

    def _build_engine_filters(self, filters: FilterDTO) -> List[Any]:
        EngineBlock = self._registry.get_model_for_table('engine_block')
        EngineConfig2 = self._registry.get_model_for_table('engine_config2')
        FuelType = self._registry.get_model_for_table('fuel_type')

        conditions = []

        if filters.engine_liters:
            conditions.append(EngineBlock.liter.in_(filters.engine_liters))

        if filters.engine_ccs:
            conditions.append(EngineBlock.cc.in_(filters.engine_ccs))

        if filters.engine_cids:
            conditions.append(EngineBlock.cid.in_(filters.engine_cids))

        if filters.engine_cylinders:
            conditions.append(EngineBlock.cylinders.in_(filters.engine_cylinders))

        if filters.engine_block_types:
            conditions.append(EngineBlock.block_type.in_(filters.engine_block_types))

        if filters.fuel_type_ids:
            conditions.append(FuelType.fuel_type_id.in_(filters.fuel_type_ids))

        return conditions

    def _apply_engine_filters(self, query: Select, conditions: List[Any], join_tracker: JoinTracker) -> Select:
        Vehicle = self._registry.get_model_for_table('vehicle')
        VehicleToEngineConfig = self._registry.get_model_for_table('vehicle_to_engine_config')
        EngineConfig2 = self._registry.get_model_for_table('engine_config2')
        EngineBlock = self._registry.get_model_for_table('engine_block')
        FuelType = self._registry.get_model_for_table('fuel_type')

        if 'vehicle_to_engine_config' not in join_tracker.joined_tables:
            query = query.join(VehicleToEngineConfig, Vehicle.vehicle_id == VehicleToEngineConfig.vehicle_id)
            join_tracker.mark_joined('vehicle_to_engine_config')

        if 'engine_config2' not in join_tracker.joined_tables:
            query = query.join(EngineConfig2, VehicleToEngineConfig.engine_config_id == EngineConfig2.engine_config_id)
            join_tracker.mark_joined('engine_config2')

        if 'engine_block' not in join_tracker.joined_tables:
            query = query.join(EngineBlock, EngineConfig2.engine_block_id == EngineBlock.engine_block_id)
            join_tracker.mark_joined('engine_block')

        if any(('fuel_type' in str(cond) for cond in conditions)) and 'fuel_type' not in join_tracker.joined_tables:
            query = query.join(FuelType, EngineConfig2.fuel_type_id == FuelType.fuel_type_id)
            join_tracker.mark_joined('fuel_type')

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def build_vehicle_query(self, filters: FilterDTO, display_fields: List[Tuple[str, str, str]],
                            limit: Optional[int] = 1000) -> Select:
        logger.debug(f'Building vehicle query with {len(display_fields)} display fields')

        Vehicle = self._registry.get_model_for_table('vehicle')
        if not Vehicle:
            logger.error('Vehicle model not found')
            return select()

        # Log the table schemas for debugging
        logger.debug(f"Vehicle table schema: {Vehicle.__table__.schema}")

        query = select().select_from(Vehicle)
        join_tracker = JoinTracker()
        join_tracker.mark_joined('vehicle')

        selected_columns = [Vehicle.vehicle_id.label('vehicle_id')]
        vehicle_id_included = True

        engine_tables = {'engine_block', 'engine_config2', 'engine_base2', 'engine_bore_stroke', 'fuel_type',
                         'aspiration', 'cylinder_head_type', 'engine_designation', 'engine_vin', 'valves',
                         'engine_version', 'ignition_system_type', 'power_output'}
        needs_engine_tables = any((table in engine_tables for table, _, _ in display_fields))

        for table, column, display_name in display_fields:
            if table == 'vehicle' and column == 'vehicle_id':
                continue

            model_class = self._registry.get_model_for_table(table)
            if not model_class:
                logger.warning(f'Unknown model for table: {table}')
                continue

            if table != 'vehicle' and (not join_tracker.is_joined(table)):
                if table in engine_tables:
                    # Handle engine-related tables
                    if not join_tracker.is_joined('vehicle_to_engine_config'):
                        VehicleToEngineConfig = self._registry.get_model_for_table('vehicle_to_engine_config')
                        query = query.join(VehicleToEngineConfig,
                                           Vehicle.vehicle_id == VehicleToEngineConfig.vehicle_id)
                        join_tracker.mark_joined('vehicle_to_engine_config')

                    if not join_tracker.is_joined('engine_config2'):
                        EngineConfig2 = self._registry.get_model_for_table('engine_config2')
                        VehicleToEngineConfig = self._registry.get_model_for_table('vehicle_to_engine_config')
                        query = query.join(EngineConfig2,
                                           VehicleToEngineConfig.engine_config_id == EngineConfig2.engine_config_id)
                        join_tracker.mark_joined('engine_config2')

                    if table != 'engine_config2' and (not join_tracker.is_joined(table)):
                        field_name = f'{table}_id'
                        if table == 'engine_block':
                            EngineConfig2 = self._registry.get_model_for_table('engine_config2')
                            query = query.join(model_class,
                                               EngineConfig2.engine_block_id == model_class.engine_block_id)

                        elif hasattr(self._registry.get_model_for_table('engine_config2'), field_name):
                            EngineConfig2 = self._registry.get_model_for_table('engine_config2')
                            query = query.join(model_class, getattr(EngineConfig2, field_name) == getattr(model_class,
                                                                                                          self._registry.get_primary_key(
                                                                                                              table)))

                        else:
                            logger.warning(f'No explicit join condition for engine_config2 to {table}')
                            query = query.join(model_class)

                        join_tracker.mark_joined(table)
                else:
                    # Handle other tables with join paths
                    join_path = self._registry.get_join_path(table, column)
                    if join_path:
                        for path_table in join_path:
                            if join_tracker.is_joined(path_table):
                                continue

                            path_model = self._registry.get_model_for_table(path_table)
                            if not path_model:
                                logger.warning(f'No model found for path table: {path_table}')
                                continue

                            if path_table == 'base_vehicle':
                                BaseVehicle = self._registry.get_model_for_table('base_vehicle')
                                query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                                join_tracker.mark_joined('base_vehicle')

                            elif path_table.startswith('vehicle_to_'):
                                query = query.join(path_model, Vehicle.vehicle_id == path_model.vehicle_id)
                                join_tracker.mark_joined(path_table)

                            else:
                                prev_tables = [t for t in join_path if join_tracker.is_joined(t)]
                                if prev_tables:
                                    prev_table = prev_tables[-1]
                                    prev_model = self._registry.get_model_for_table(prev_table)
                                    rel_col = f'{path_table}_id'

                                    if hasattr(prev_model, rel_col):
                                        target_pk = self._registry.get_primary_key(path_table)
                                        query = query.join(path_model,
                                                           getattr(prev_model, rel_col) == getattr(path_model,
                                                                                                   target_pk))
                                        join_tracker.mark_joined(path_table)
                                        continue

                                    rel_col = f'{prev_table}_id'
                                    if hasattr(path_model, rel_col):
                                        prev_pk = self._registry.get_primary_key(prev_table)
                                        query = query.join(path_model,
                                                           getattr(prev_model, prev_pk) == getattr(path_model, rel_col))
                                        join_tracker.mark_joined(path_table)
                                        continue

                                logger.warning(f'Using default join logic for {path_table}')
                                query = query.join(path_model)
                                join_tracker.mark_joined(path_table)
                    else:
                        logger.warning(f'No join path defined for {table}.{column}')
                        continue

            column_attr = getattr(model_class, column)
            selected_columns.append(column_attr.label(display_name))

        query = query.with_only_columns(*selected_columns)
        query = self._apply_vehicle_filters(query, filters, join_tracker)

        if limit:
            query = query.limit(limit)

        # Log the final query for debugging
        logger.debug(f"Generated vehicle query SQL: {query}")

        return query

    def _apply_vehicle_filters(self, query: Select, filters: FilterDTO, join_tracker: JoinTracker) -> Select:
        Vehicle = self._registry.get_model_for_table('vehicle')
        BaseVehicle = self._registry.get_model_for_table('base_vehicle')
        Year = self._registry.get_model_for_table('year')
        Make = self._registry.get_model_for_table('make')
        Model = self._registry.get_model_for_table('model')
        SubModel = self._registry.get_model_for_table('sub_model')

        if not self._should_apply_filters(filters):
            return query

        if 'base_vehicle' not in join_tracker.joined_tables:
            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
            join_tracker.mark_joined('base_vehicle')

        conditions = []

        if filters.year_ids:
            if 'year' not in join_tracker.joined_tables:
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                join_tracker.mark_joined('year')
            conditions.append(Year.year_id.in_(filters.year_ids))

        elif filters.use_year_range and filters.year_range_start is not None and (filters.year_range_end is not None):
            if 'year' not in join_tracker.joined_tables:
                query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                join_tracker.mark_joined('year')
            conditions.append(Year.year_id.between(filters.year_range_start, filters.year_range_end))

        if filters.make_ids:
            if 'make' not in join_tracker.joined_tables:
                query = query.join(Make, BaseVehicle.make_id == Make.make_id)
                join_tracker.mark_joined('make')
            conditions.append(Make.make_id.in_(filters.make_ids))

        if filters.model_ids:
            if 'model' not in join_tracker.joined_tables:
                query = query.join(Model, BaseVehicle.model_id == Model.model_id)
                join_tracker.mark_joined('model')
            conditions.append(Model.model_id.in_(filters.model_ids))

        if filters.sub_model_ids:
            if 'sub_model' not in join_tracker.joined_tables:
                query = query.join(SubModel, Vehicle.sub_model_id == SubModel.sub_model_id)
                join_tracker.mark_joined('sub_model')
            conditions.append(SubModel.sub_model_id.in_(filters.sub_model_ids))

        engine_filters = self._build_engine_filters(filters)
        if engine_filters:
            query = self._apply_engine_filters(query, engine_filters, join_tracker)

        body_filters = self._build_body_filters(filters)
        if body_filters:
            query = self._apply_body_filters(query, body_filters, join_tracker)

        transmission_filters = self._build_transmission_filters(filters)
        if transmission_filters:
            query = self._apply_transmission_filters(query, transmission_filters, join_tracker)

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def _build_body_filters(self, filters: FilterDTO) -> List[Any]:
        BodyType = self._registry.get_model_for_table('body_type')
        BodyNumDoors = self._registry.get_model_for_table('body_num_doors')

        conditions = []

        if filters.body_type_ids:
            conditions.append(BodyType.body_type_id.in_(filters.body_type_ids))

        if filters.body_num_doors_ids:
            conditions.append(BodyNumDoors.body_num_doors_id.in_(filters.body_num_doors_ids))

        return conditions

    def _apply_body_filters(self, query: Select, conditions: List[Any], join_tracker: JoinTracker) -> Select:
        Vehicle = self._registry.get_model_for_table('vehicle')
        VehicleToBodyStyleConfig = self._registry.get_model_for_table('vehicle_to_body_style_config')
        BodyStyleConfig = self._registry.get_model_for_table('body_style_config')
        BodyType = self._registry.get_model_for_table('body_type')
        BodyNumDoors = self._registry.get_model_for_table('body_num_doors')

        if 'vehicle_to_body_style_config' not in join_tracker.joined_tables:
            query = query.join(VehicleToBodyStyleConfig, Vehicle.vehicle_id == VehicleToBodyStyleConfig.vehicle_id)
            join_tracker.mark_joined('vehicle_to_body_style_config')

        if 'body_style_config' not in join_tracker.joined_tables:
            query = query.join(BodyStyleConfig,
                               VehicleToBodyStyleConfig.body_style_config_id == BodyStyleConfig.body_style_config_id)
            join_tracker.mark_joined('body_style_config')

        if 'body_type' not in join_tracker.joined_tables:
            query = query.join(BodyType, BodyStyleConfig.body_type_id == BodyType.body_type_id)
            join_tracker.mark_joined('body_type')

        if 'body_num_doors' not in join_tracker.joined_tables:
            query = query.join(BodyNumDoors, BodyStyleConfig.body_num_doors_id == BodyNumDoors.body_num_doors_id)
            join_tracker.mark_joined('body_num_doors')

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def _build_transmission_filters(self, filters: FilterDTO) -> List[Any]:
        TransmissionType = self._registry.get_model_for_table('transmission_type')
        TransmissionNumSpeeds = self._registry.get_model_for_table('transmission_num_speeds')
        TransmissionControlType = self._registry.get_model_for_table('transmission_control_type')

        conditions = []

        if filters.transmission_type_ids:
            conditions.append(TransmissionType.transmission_type_id.in_(filters.transmission_type_ids))

        if filters.transmission_num_speeds_ids:
            conditions.append(TransmissionNumSpeeds.transmission_num_speeds_id.in_(filters.transmission_num_speeds_ids))

        if filters.transmission_control_type_ids:
            conditions.append(
                TransmissionControlType.transmission_control_type_id.in_(filters.transmission_control_type_ids))

        return conditions

    def _apply_transmission_filters(self, query: Select, conditions: List[Any], join_tracker: JoinTracker) -> Select:
        Vehicle = self._registry.get_model_for_table('vehicle')
        VehicleToTransmission = self._registry.get_model_for_table('vehicle_to_transmission')
        Transmission = self._registry.get_model_for_table('transmission')
        TransmissionBase = self._registry.get_model_for_table('transmission_base')
        TransmissionType = self._registry.get_model_for_table('transmission_type')
        TransmissionNumSpeeds = self._registry.get_model_for_table('transmission_num_speeds')
        TransmissionControlType = self._registry.get_model_for_table('transmission_control_type')

        if 'vehicle_to_transmission' not in join_tracker.joined_tables:
            query = query.join(VehicleToTransmission, Vehicle.vehicle_id == VehicleToTransmission.vehicle_id)
            join_tracker.mark_joined('vehicle_to_transmission')

        if 'transmission' not in join_tracker.joined_tables:
            query = query.join(Transmission, VehicleToTransmission.transmission_id == Transmission.transmission_id)
            join_tracker.mark_joined('transmission')

        if 'transmission_base' not in join_tracker.joined_tables:
            query = query.join(TransmissionBase,
                               Transmission.transmission_base_id == TransmissionBase.transmission_base_id)
            join_tracker.mark_joined('transmission_base')

        if 'transmission_type' not in join_tracker.joined_tables:
            query = query.join(TransmissionType,
                               TransmissionBase.transmission_type_id == TransmissionType.transmission_type_id)
            join_tracker.mark_joined('transmission_type')

        if 'transmission_num_speeds' not in join_tracker.joined_tables:
            query = query.join(TransmissionNumSpeeds,
                               TransmissionBase.transmission_num_speeds_id == TransmissionNumSpeeds.transmission_num_speeds_id)
            join_tracker.mark_joined('transmission_num_speeds')

        if 'transmission_control_type' not in join_tracker.joined_tables:
            query = query.join(TransmissionControlType,
                               TransmissionBase.transmission_control_type_id == TransmissionControlType.transmission_control_type_id)
            join_tracker.mark_joined('transmission_control_type')

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def build_multiple_vehicle_queries(self, filter_dtos: Dict[str, FilterDTO],
                                       display_fields: List[Tuple[str, str, str]], limit: Optional[int] = 1000) -> Dict[
        str, Select]:
        queries = {}
        for section_id, filter_dto in filter_dtos.items():
            queries[section_id] = self.build_vehicle_query(filters=filter_dto, display_fields=display_fields,
                                                           limit=limit)
        return queries


query_builder = QueryBuilder()