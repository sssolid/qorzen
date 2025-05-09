from __future__ import annotations
import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, cast

import sqlalchemy
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import Select

from qorzen.core.database_manager import DatabaseConnectionConfig, DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event, EventType
from qorzen.core.thread_manager import ThreadManager
from qorzen.utils.exceptions import DatabaseError

from .events import VCdbEventType
from .models import (
    Aspiration, BaseVehicle, BedConfig, BedLength, BedType, BodyNumDoors,
    BodyStyleConfig, BodyType, BrakeABS, BrakeConfig, BrakeSystem, BrakeType,
    Class, CylinderHeadType, DriveType, ElecControlled, EngineBase2, EngineBlock,
    EngineBoreStroke, EngineConfig2, EngineDesignation, EngineVersion,
    FuelDeliveryConfig, FuelDeliverySubType, FuelDeliveryType, FuelSystemControlType,
    FuelSystemDesign, FuelType, IgnitionSystemType, Make, Mfr, MfrBodyCode, Model,
    PowerOutput, PublicationStage, Region, SpringType, SpringTypeConfig,
    SteeringConfig, SteeringSystem, SteeringType, SubModel, Transmission,
    TransmissionBase, TransmissionControlType, TransmissionMfrCode,
    TransmissionNumSpeeds, TransmissionType, Valves, Vehicle, VehicleToBodyConfig,
    VehicleToBodyStyleConfig, VehicleToBedConfig, VehicleToBrakeConfig,
    VehicleToClass, VehicleToDriveType, VehicleToEngineConfig, VehicleToMfrBodyCode,
    VehicleToSpringTypeConfig, VehicleToSteeringConfig, VehicleToTransmission,
    VehicleToWheelBase, VehicleType, VehicleTypeGroup, WheelBase, Year
)


class DatabaseHandlerError(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class DatabaseHandler:
    CONNECTION_NAME = 'vcdb_explorer'

    def __init__(
            self,
            database_manager: DatabaseManager,
            event_bus: EventBusManager,
            thread_manager: ThreadManager,
            logger: logging.Logger
    ) -> None:
        self._db_manager = database_manager
        self._event_bus = event_bus
        self._thread_manager = thread_manager
        self._logger = logger
        self._initialized = False
        self._query_lock = threading.RLock()
        self._connection_config: Optional[DatabaseConnectionConfig] = None

        self._filter_map = {
            'year': (Year, 'year_id'),
            'make': (Make, 'make_name'),
            'model': (Model, 'model_name'),
            'submodel': (SubModel, 'sub_model_name'),
            'region': (Region, 'region_name'),
            'drivetype': (DriveType, 'drive_type_name'),
            'vehicletype': (VehicleType, 'vehicle_type_name'),
            'vehicletypegroup': (VehicleTypeGroup, 'vehicle_type_group_name'),
            'publicationstage': (PublicationStage, 'publication_stage_name'),
            'class': (Class, 'class_name'),
            'wheelbase': (WheelBase, 'wheel_base'),
            'bedtype': (BedType, 'bed_type_name'),
            'bedlength': (BedLength, 'bed_length'),
            'bodytype': (BodyType, 'body_type_name'),
            'bodynumdoors': (BodyNumDoors, 'body_num_doors'),
            'braketype': (BrakeType, 'brake_type_name'),
            'brakesystem': (BrakeSystem, 'brake_system_name'),
            'brakeabs': (BrakeABS, 'brake_abs_name'),
            'engineblock': (EngineBlock, 'cylinders'),
            'fueltypename': (FuelType, 'fuel_type_name')
        }

        self._event_bus.subscribe(
            event_type=VCdbEventType.filter_changed(),
            callback=self._on_filter_changed,
            subscriber_id='vcdb_explorer_handler'
        )
        self._event_bus.subscribe(
            event_type=VCdbEventType.query_execute(),
            callback=self._on_query_execute,
            subscriber_id='vcdb_explorer_handler'
        )

    def configure(
            self,
            host: str,
            port: int,
            database: str,
            user: str,
            password: str,
            db_type: str = 'postgresql',
            pool_size: int = 5,
            max_overflow: int = 10,
            pool_recycle: int = 3600,
            echo: bool = False
    ) -> None:
        self._logger.debug(f'Configuring VCdb database connection: {host}:{port}/{database}')

        # Check if connection already exists
        if self._db_manager.has_connection(self.CONNECTION_NAME):
            self._logger.info(f'Connection {self.CONNECTION_NAME} already exists, reusing it')
            self._initialized = True
            return

        self._connection_config = DatabaseConnectionConfig(
            name=self.CONNECTION_NAME,
            db_type=db_type,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            echo=echo
        )

        try:
            self._db_manager.register_connection(self._connection_config)
            self._initialized = True

            with self.session() as session:
                result = session.execute(select(func.count()).select_from(Vehicle)).scalar()
                self._logger.info(f'Connected to VCdb database. Vehicle count: {result}')

        except Exception as e:
            self._logger.error(f'Failed to initialize VCdb database connection: {str(e)}')
            self._initialized = False
            raise DatabaseHandlerError(f'Failed to initialize VCdb database connection: {str(e)}') from e

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self._db_manager.session(self.CONNECTION_NAME) as session:
                yield session
        except DatabaseError as e:
            raise DatabaseHandlerError(f'Database error: {str(e)}') from e

    def shutdown(self) -> None:
        if not self._initialized:
            return

        try:
            self._event_bus.unsubscribe(subscriber_id='vcdb_explorer_handler')

            if self._db_manager and self._db_manager.has_connection(self.CONNECTION_NAME):
                try:
                    self._db_manager.unregister_connection(self.CONNECTION_NAME)
                    self._logger.info(f'Unregistered database connection: {self.CONNECTION_NAME}')
                except Exception as e:
                    self._logger.warning(f'Error unregistering database connection: {str(e)}')

            self._initialized = False
            self._logger.info('VCdb Database Handler shut down successfully')

        except Exception as e:
            self._logger.error(f'Error shutting down VCdb Database Handler: {str(e)}')

    def _on_filter_changed(self, event: Event) -> None:
        payload = event.payload
        filter_panel_id = payload.get('panel_id')
        filter_type = payload.get('filter_type')
        values = payload.get('values', [])
        current_filters = payload.get('current_filters', {})
        auto_populate = payload.get('auto_populate', False)

        self._logger.debug(
            f'Filter changed event: panel={filter_panel_id}, type={filter_type}, values={values}, auto_populate={auto_populate}')

        if auto_populate:
            self._thread_manager.submit_task(
                self._refresh_filters,
                filter_panel_id,
                filter_type,
                current_filters,
                name=f'filter_refresh_{filter_panel_id}_{filter_type}',
                submitter='vcdb_explorer'
            )

    def _on_query_execute(self, event: Event) -> None:
        payload = event.payload
        filter_panels = payload.get('filter_panels', [])
        columns = payload.get('columns', [])
        page = payload.get('page', 1)
        page_size = payload.get('page_size', 100)
        sort_by = payload.get('sort_by')
        sort_desc = payload.get('sort_desc', False)
        table_filters = payload.get('table_filters', {})
        callback_id = payload.get('callback_id')

        self._logger.debug(f'Query execute event: panels={len(filter_panels)}, columns={columns}, page={page}')

        for i, panel in enumerate(filter_panels):
            if panel:
                self._logger.debug(f'Filter panel {i}: {panel}')
            else:
                self._logger.debug(f'Filter panel {i}: Empty')

        def _on_failed(err_msg: str = '<thread error>') -> None:
            self._event_bus.publish(
                event_type=VCdbEventType.query_results(),
                source='vcdb_explorer',
                payload={
                    'results': [],
                    'total_count': 0,
                    'error': err_msg,
                    'callback_id': callback_id
                },
                synchronous=False
            )

        self._thread_manager.submit_qt_task(
            self._execute_query_thread,
            filter_panels,
            columns,
            page,
            page_size,
            sort_by,
            sort_desc,
            table_filters,
            callback_id,
            on_completed=self._publish_query_results,
            on_failed=_on_failed,
            name=f'query_execute_{time.time()}',
            submitter='vcdb_explorer'
        )

    def _refresh_filters(self, filter_panel_id: str, changed_filter_type: str,
                         current_filters: Dict[str, List[int]]) -> None:
        self._logger.debug(f'Refreshing filters for panel {filter_panel_id} after {changed_filter_type} change')

        exclude_filters = {changed_filter_type}
        if changed_filter_type == 'year_range':
            exclude_filters.add('year')
        elif changed_filter_type == 'year':
            exclude_filters.add('year_range')

        results = {}
        with self._query_lock:
            try:
                for filter_type in self._filter_map.keys():
                    if filter_type != changed_filter_type and filter_type != 'year_range' and (filter_type != 'year'):
                        try:
                            values = self.get_filter_values(filter_type, current_filters, exclude_filters)
                            results[filter_type] = values
                            self._logger.debug(f'Refreshed {filter_type}: {len(values)} values')
                        except Exception as e:
                            self._logger.error(f'Error refreshing {filter_type}: {str(e)}')

                if changed_filter_type != 'year' and 'year' in self._filter_map:
                    try:
                        values = self.get_filter_values('year', current_filters, exclude_filters)
                        results['year'] = values
                    except Exception as e:
                        self._logger.error(f'Error refreshing year: {str(e)}')

            except Exception as e:
                self._logger.error(f'Error during filter refresh: {str(e)}')

        self._event_bus.publish(
            event_type=VCdbEventType.filters_refreshed(),
            source='vcdb_explorer',
            payload={
                'panel_id': filter_panel_id,
                'filter_values': results
            }
        )

    def _execute_query_thread(
            self,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            page: int,
            page_size: int,
            sort_by: Optional[str],
            sort_desc: bool,
            table_filters: Dict[str, Any],
            callback_id: Optional[str]
    ) -> Dict[str, Any]:
        self._logger.debug(
            f'Executing query in thread: panels={len(filter_panels)}, page={page}, page_size={page_size}')

        valid_panels = [panel for panel in filter_panels if panel]
        if not valid_panels:
            self._logger.warning('No filter conditions found in any panel')

        with self._query_lock:
            try:
                start_time = time.time()
                results, total_count = self.execute_query(
                    filter_panels,
                    columns,
                    page,
                    page_size,
                    sort_by,
                    sort_desc,
                    table_filters
                )
                duration = time.time() - start_time

                self._logger.debug(f'Query executed in {duration:.3f}s: {len(results)} rows of {total_count} total')

                return {
                    'results': results,
                    'total_count': total_count,
                    'callback_id': callback_id
                }

            except Exception as e:
                self._logger.error(f'Error executing query: {e}')
                return {
                    'results': [],
                    'total_count': 0,
                    'error': str(e),
                    'callback_id': callback_id
                }

    def _publish_query_results(self, payload: Dict[str, Any]) -> None:
        self._event_bus.publish(
            event_type=VCdbEventType.query_results(),
            source='vcdb_explorer',
            payload=payload,
            synchronous=False
        )

    def get_filter_values(
            self,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            exclude_filters: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        if exclude_filters is None:
            exclude_filters = set()

        try:
            if filter_type not in self._filter_map:
                raise DatabaseHandlerError(f'Unknown filter type: {filter_type}')

            model_class, attr_name = self._filter_map[filter_type]
            with self.session() as session:
                if filter_type == 'year':
                    query = (
                        select(
                            Year.year_id.label('id'),
                            Year.year_id.label('name'),
                            func.count(Year.year_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        .join(Year, BaseVehicle.year_id == Year.year_id)
                        .group_by(Year.year_id)
                        .order_by(Year.year_id)
                    )
                elif filter_type == 'make':
                    query = (
                        select(
                            Make.make_id.label('id'),
                            Make.make_name.label('name'),
                            func.count(Make.make_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        .join(Make, BaseVehicle.make_id == Make.make_id)
                        .group_by(Make.make_id, Make.make_name)
                        .order_by(Make.make_name)
                    )
                elif filter_type == 'model':
                    query = (
                        select(
                            Model.model_id.label('id'),
                            Model.model_name.label('name'),
                            func.count(Model.model_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        .join(Model, BaseVehicle.model_id == Model.model_id)
                        .group_by(Model.model_id, Model.model_name)
                        .order_by(Model.model_name)
                    )
                elif filter_type == 'submodel':
                    query = (
                        select(
                            SubModel.sub_model_id.label('id'),
                            SubModel.sub_model_name.label('name'),
                            func.count(SubModel.sub_model_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(SubModel, Vehicle.sub_model_id == SubModel.sub_model_id)
                        .group_by(SubModel.sub_model_id, SubModel.sub_model_name)
                        .order_by(SubModel.sub_model_name)
                    )
                elif filter_type == 'region':
                    query = (
                        select(
                            Region.region_id.label('id'),
                            Region.region_name.label('name'),
                            func.count(Region.region_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(Region, Vehicle.region_id == Region.region_id)
                        .group_by(Region.region_id, Region.region_name)
                        .order_by(Region.region_name)
                    )
                elif filter_type == 'drivetype':
                    vtdt = aliased(VehicleToDriveType)
                    dt = aliased(DriveType)
                    query = (
                        select(
                            dt.drive_type_id.label('id'),
                            dt.drive_type_name.label('name'),
                            func.count(dt.drive_type_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(vtdt, Vehicle.vehicle_id == vtdt.vehicle_id)
                        .join(dt, vtdt.drive_type_id == dt.drive_type_id)
                        .group_by(dt.drive_type_id, dt.drive_type_name)
                        .order_by(dt.drive_type_name)
                    )
                elif filter_type == 'wheelbase':
                    vtwb = aliased(VehicleToWheelBase)
                    wb = aliased(WheelBase)
                    query = (
                        select(
                            wb.wheel_base_id.label('id'),
                            wb.wheel_base.label('name'),
                            func.count(wb.wheel_base_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(vtwb, Vehicle.vehicle_id == vtwb.vehicle_id)
                        .join(wb, vtwb.wheel_base_id == wb.wheel_base_id)
                        .group_by(wb.wheel_base_id, wb.wheel_base)
                        .order_by(wb.wheel_base)
                    )
                elif filter_type == 'bedtype':
                    vtbc = aliased(VehicleToBedConfig)
                    bc = aliased(BedConfig)
                    bt = aliased(BedType)
                    query = (
                        select(
                            bt.bed_type_id.label('id'),
                            bt.bed_type_name.label('name'),
                            func.count(bt.bed_type_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                        .join(bc, vtbc.bed_config_id == bc.bed_config_id)
                        .join(bt, bc.bed_type_id == bt.bed_type_id)
                        .group_by(bt.bed_type_id, bt.bed_type_name)
                        .order_by(bt.bed_type_name)
                    )
                elif filter_type == 'bedlength':
                    vtbc = aliased(VehicleToBedConfig)
                    bc = aliased(BedConfig)
                    bl = aliased(BedLength)
                    query = (
                        select(
                            bl.bed_length_id.label('id'),
                            bl.bed_length.label('name'),
                            func.count(bl.bed_length_id).label('count')
                        )
                        .select_from(Vehicle)
                        .join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                        .join(bc, vtbc.bed_config_id == bc.bed_config_id)
                        .join(bl, bc.bed_length_id == bl.bed_length_id)
                        .group_by(bl.bed_length_id, bl.bed_length)
                        .order_by(bl.bed_length)
                    )
                else:
                    pk_column = getattr(model_class, model_class.__table__.primary_key.columns.keys()[0])
                    name_column = getattr(model_class, attr_name)
                    query = (
                        select(
                            pk_column.label('id'),
                            name_column.label('name'),
                            func.count(pk_column).label('count')
                        )
                        .select_from(Vehicle)
                    )

                query = self._apply_filters(query, current_filters, exclude_filters)
                self._logger.debug(f'Executing filter values query for {filter_type}')
                result = session.execute(query)

                values = []
                for row in result:
                    values.append({'id': row.id, 'name': str(row.name), 'count': row.count})

                return values

        except SQLAlchemyError as e:
            self._logger.error(f'Error getting filter values for {filter_type}: {str(e)}')
            raise DatabaseHandlerError(f'Error getting filter values for {filter_type}: {str(e)}') from e

    def _apply_filters(self, query: Select, filters: Dict[str, List[int]], exclude_filters: Set[str],
                       target_model: Any = None) -> Select:
        if not filters:
            self._logger.debug('No filters to apply')
            return query

        self._logger.debug(f'Applying filters: {filters}, excluding: {exclude_filters}')

        has_base_vehicle_join = False
        for clause in query._from_obj:
            if isinstance(clause, sqlalchemy.sql.elements.Join) and hasattr(clause, 'right') and (
                    clause.right == BaseVehicle.__table__):
                has_base_vehicle_join = True
                break

        for filter_type, values in filters.items():
            if not values:
                self._logger.debug(f'Skipping empty filter: {filter_type}')
                continue

            if filter_type in exclude_filters:
                self._logger.debug(f'Skipping excluded filter: {filter_type}')
                continue

            if target_model and filter_type in self._filter_map and (self._filter_map[filter_type][0] == target_model):
                self._logger.debug(f'Skipping filter for target model: {filter_type}')
                continue

            try:
                if filter_type == 'year':
                    if not has_base_vehicle_join:
                        query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        has_base_vehicle_join = True
                        self._logger.debug('Added join to BaseVehicle for year filter')

                    if len(values) == 2 and values[0] <= values[1]:
                        query = query.filter(BaseVehicle.year_id.between(values[0], values[1]))
                        self._logger.debug(f'Applied year range filter: {values[0]}-{values[1]}')
                    else:
                        query = query.filter(BaseVehicle.year_id.in_(values))
                        self._logger.debug(f'Applied specific years filter: {values}')

                elif filter_type == 'make':
                    if not has_base_vehicle_join:
                        query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        has_base_vehicle_join = True
                        self._logger.debug('Added join to BaseVehicle for make filter')

                    query = query.filter(BaseVehicle.make_id.in_(values))
                    self._logger.debug(f'Applied make filter: {values}')

                elif filter_type == 'model':
                    if not has_base_vehicle_join:
                        query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        has_base_vehicle_join = True
                        self._logger.debug('Added join to BaseVehicle for model filter')

                    query = query.filter(BaseVehicle.model_id.in_(values))
                    self._logger.debug(f'Applied model filter: {values}')

                elif filter_type == 'submodel':
                    query = query.filter(Vehicle.sub_model_id.in_(values))
                    self._logger.debug(f'Applied submodel filter: {values}')

                elif filter_type == 'region':
                    query = query.filter(Vehicle.region_id.in_(values))
                    self._logger.debug(f'Applied region filter: {values}')

                elif filter_type == 'drivetype':
                    vtdt = aliased(VehicleToDriveType)
                    dt = aliased(DriveType)
                    query = query.join(vtdt, Vehicle.vehicle_id == vtdt.vehicle_id)
                    query = query.join(dt, vtdt.drive_type_id == dt.drive_type_id)
                    query = query.filter(dt.drive_type_id.in_(values))
                    self._logger.debug(f'Applied drive type filter with joins: {values}')

                elif filter_type == 'wheelbase':
                    vtwb = aliased(VehicleToWheelBase)
                    wb = aliased(WheelBase)
                    query = query.join(vtwb, Vehicle.vehicle_id == vtwb.vehicle_id)
                    query = query.join(wb, vtwb.wheel_base_id == wb.wheel_base_id)
                    query = query.filter(wb.wheel_base_id.in_(values))
                    self._logger.debug(f'Applied wheel base filter with joins: {values}')

                elif filter_type == 'bedtype':
                    vtbc = aliased(VehicleToBedConfig)
                    bc = aliased(BedConfig)
                    bt = aliased(BedType)
                    query = query.join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                    query = query.join(bc, vtbc.bed_config_id == bc.bed_config_id)
                    query = query.join(bt, bc.bed_type_id == bt.bed_type_id)
                    query = query.filter(bt.bed_type_id.in_(values))
                    self._logger.debug(f'Applied bed type filter with joins: {values}')

                elif filter_type == 'vehicletype':
                    if not has_base_vehicle_join:
                        query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        has_base_vehicle_join = True

                    query = query.join(Model, BaseVehicle.model_id == Model.model_id)
                    query = query.join(VehicleType, Model.vehicle_type_id == VehicleType.vehicle_type_id)
                    query = query.filter(VehicleType.vehicle_type_id.in_(values))
                    self._logger.debug(f'Applied vehicle type filter with joins: {values}')

                elif filter_type == 'engineblock':
                    vtec = aliased(VehicleToEngineConfig)
                    ec = aliased(EngineConfig2)
                    eb = aliased(EngineBlock)
                    query = query.join(vtec, Vehicle.vehicle_id == vtec.vehicle_id)
                    query = query.join(ec, vtec.engine_config_id == ec.engine_config_id)
                    query = query.join(eb, ec.engine_block_id == eb.engine_block_id)
                    engine_block_ids = [int(v) if isinstance(v, str) and v.isdigit() else v for v in values]
                    query = query.filter(eb.engine_block_id.in_(engine_block_ids))
                    self._logger.debug(f'Applied engine block filter with joins: {values}')

                elif filter_type == 'fueltypename':
                    vtec = aliased(VehicleToEngineConfig)
                    ec = aliased(EngineConfig2)
                    ft = aliased(FuelType)
                    query = query.join(vtec, Vehicle.vehicle_id == vtec.vehicle_id)
                    query = query.join(ec, vtec.engine_config_id == ec.engine_config_id)
                    query = query.join(ft, ec.fuel_type_id == ft.fuel_type_id)
                    query = query.filter(ft.fuel_type_id.in_(values))
                    self._logger.debug(f'Applied fuel type filter with joins: {values}')

                elif filter_type in self._filter_map:
                    model_class, attr_name = self._filter_map[filter_type]
                    self._logger.debug(f'Using filter map for {filter_type}: {model_class.__name__}.{attr_name}')

                    if model_class == Year:
                        if not has_base_vehicle_join:
                            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                            has_base_vehicle_join = True

                        query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                        query = query.filter(getattr(Year, attr_name).in_(values))
                        self._logger.debug(f'Applied {filter_type} filter with year join: {values}')

                    elif model_class == Make:
                        if not has_base_vehicle_join:
                            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                            has_base_vehicle_join = True

                        query = query.join(Make, BaseVehicle.make_id == Make.make_id)
                        query = query.filter(getattr(Make, attr_name).in_(values))
                        self._logger.debug(f'Applied {filter_type} filter with make join: {values}')

                    elif model_class == Model:
                        if not has_base_vehicle_join:
                            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                            has_base_vehicle_join = True

                        query = query.join(Model, BaseVehicle.model_id == Model.model_id)
                        query = query.filter(getattr(Model, attr_name).in_(values))
                        self._logger.debug(f'Applied {filter_type} filter with model join: {values}')

                    else:
                        self._logger.warning(
                            f'Unimplemented filter type in map: {filter_type} ({model_class.__name__}.{attr_name})')

                else:
                    self._logger.warning(f'Unknown filter type: {filter_type}')

            except Exception as e:
                self._logger.error(f'Error applying filter {filter_type}: {str(e)}')

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
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self.session() as session:
                self._logger.debug(
                    f'Executing query: panels={len(filter_panels)}, columns={columns}, page={page}, page_size={page_size}')

                base_query = select(Vehicle.vehicle_id).select_from(Vehicle)

                if filter_panels:
                    panel_conditions = []
                    for panel in filter_panels:
                        if not panel:
                            continue

                        panel_query = select(Vehicle.vehicle_id).select_from(Vehicle)
                        panel_query = self._apply_filters(panel_query, panel, set())
                        panel_conditions.append(Vehicle.vehicle_id.in_(panel_query.scalar_subquery()))

                    if panel_conditions:
                        base_query = base_query.filter(or_(*panel_conditions))
                        self._logger.debug(f'Applied {len(panel_conditions)} panel conditions')

                count_query = select(func.count()).select_from(base_query.alias())
                total_count = session.execute(count_query).scalar() or 0
                self._logger.debug(f'Total count: {total_count}')

                query = self._build_columns_query(base_query.scalar_subquery(), columns)

                if table_filters:
                    query = self._apply_table_filters(query, table_filters)
                    self._logger.debug(f'Applied table filters: {table_filters}')

                if sort_by:
                    query = self._apply_sorting(query, sort_by, sort_desc)
                    self._logger.debug(f"Applied sorting: {sort_by} {('DESC' if sort_desc else 'ASC')}")

                if page > 0 and page_size > 0:
                    query = query.offset((page - 1) * page_size).limit(page_size)
                    self._logger.debug(f'Applied pagination: page={page}, page_size={page_size}')

                self._logger.debug('Executing final query')
                result_rows = session.execute(query).all()

                results = []
                for row in result_rows:
                    result = {}
                    for i, col in enumerate(query.columns):
                        col_name = col.name
                        value = row[i]
                        result[col_name] = value
                    results.append(result)

                self._logger.debug(f'Query returned {len(results)} rows')
                return (results, total_count)

        except SQLAlchemyError as e:
            self._logger.error(f'Error executing query: {str(e)}')
            raise DatabaseHandlerError(f'Error executing query: {str(e)}') from e

    def _build_columns_query(self, vehicle_ids: Any, columns: List[str]) -> Select:
        query = select(Vehicle.vehicle_id).select_from(Vehicle)
        query = query.filter(Vehicle.vehicle_id.in_(vehicle_ids))
        query = query.add_columns(BaseVehicle.year_id.label('year')).join(BaseVehicle,
                                                                          Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id,
                                                                          isouter=True)
        query = query.add_columns(Make.make_id.label('make_id'), Make.make_name.label('make')).join(Make,
                                                                                                    BaseVehicle.make_id == Make.make_id,
                                                                                                    isouter=True)
        query = query.add_columns(Model.model_id.label('model_id'), Model.model_name.label('model')).join(Model,
                                                                                                          BaseVehicle.model_id == Model.model_id,
                                                                                                          isouter=True)
        query = query.add_columns(SubModel.sub_model_id.label('submodel_id'),
                                  SubModel.sub_model_name.label('submodel')).join(SubModel,
                                                                                  Vehicle.sub_model_id == SubModel.sub_model_id,
                                                                                  isouter=True)

        for column in columns:
            if column == 'region':
                query = query.add_columns(Region.region_id.label('region_id'),
                                          Region.region_name.label('region')).outerjoin(Region,
                                                                                        Vehicle.region_id == Region.region_id)
            elif column == 'vehicle_type':
                query = query.add_columns(VehicleType.vehicle_type_id.label('vehicle_type_id'),
                                          VehicleType.vehicle_type_name.label('vehicle_type')).outerjoin(VehicleType,
                                                                                                         Model.vehicle_type_id == VehicleType.vehicle_type_id)
            elif column == 'drive_type':
                vtdt = aliased(VehicleToDriveType)
                dt = aliased(DriveType)
                query = query.add_columns(dt.drive_type_id.label('drive_type_id'),
                                          dt.drive_type_name.label('drive_type')).outerjoin(vtdt,
                                                                                            Vehicle.vehicle_id == vtdt.vehicle_id).outerjoin(
                    dt, vtdt.drive_type_id == dt.drive_type_id)

        return query

    def _apply_table_filters(self, query: Select, table_filters: Dict[str, Any]) -> Select:
        for column, filter_value in table_filters.items():
            if column == 'year' and isinstance(filter_value, dict):
                min_year = filter_value.get('min')
                max_year = filter_value.get('max')

                if min_year is not None and max_year is not None:
                    query = query.filter(BaseVehicle.year_id.between(min_year, max_year))
                    self._logger.debug(f'Applied year range table filter: {min_year}-{max_year}')
                elif min_year is not None:
                    query = query.filter(BaseVehicle.year_id >= min_year)
                    self._logger.debug(f'Applied min year table filter: >={min_year}')
                elif max_year is not None:
                    query = query.filter(BaseVehicle.year_id <= max_year)
                    self._logger.debug(f'Applied max year table filter: <={max_year}')

            elif column == 'make' and isinstance(filter_value, str):
                query = query.filter(Make.make_name.ilike(f'%{filter_value}%'))
                self._logger.debug(f'Applied make text table filter: {filter_value}')

            elif column == 'model' and isinstance(filter_value, str):
                query = query.filter(Model.model_name.ilike(f'%{filter_value}%'))
                self._logger.debug(f'Applied model text table filter: {filter_value}')

            elif column == 'submodel' and isinstance(filter_value, str):
                query = query.filter(SubModel.sub_model_name.ilike(f'%{filter_value}%'))
                self._logger.debug(f'Applied submodel text table filter: {filter_value}')

        return query

    def _apply_sorting(self, query: Select, sort_by: str, sort_desc: bool) -> Select:
        sort_map = {
            'vehicle_id': Vehicle.vehicle_id,
            'year': BaseVehicle.year_id,
            'make': Make.make_name,
            'model': Model.model_name,
            'submodel': SubModel.sub_model_name,
            'region': Region.region_name
        }

        if sort_by in sort_map:
            sort_col = sort_map[sort_by]
            if sort_desc:
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())

        return query

    def get_available_columns(self) -> List[Dict[str, str]]:
        return [
            {'id': 'vehicle_id', 'name': 'Vehicle ID'},
            {'id': 'year', 'name': 'Year'},
            {'id': 'make', 'name': 'Make'},
            {'id': 'model', 'name': 'Model'},
            {'id': 'submodel', 'name': 'Submodel'},
            {'id': 'region', 'name': 'Region'},
            {'id': 'vehicle_type', 'name': 'Vehicle Type'},
            {'id': 'drive_type', 'name': 'Drive Type'},
            {'id': 'brake_system', 'name': 'Brake System'},
            {'id': 'body_type', 'name': 'Body Type'},
            {'id': 'engine', 'name': 'Engine'},
            {'id': 'transmission', 'name': 'Transmission'},
            {'id': 'wheel_base', 'name': 'Wheel Base'},
            {'id': 'bed_type', 'name': 'Bed Type'},
            {'id': 'bed_length', 'name': 'Bed Length'},
            {'id': 'bed_length_metric', 'name': 'Bed Length (Metric)'}
        ]

    def get_available_filters(self) -> List[Dict[str, str]]:
        return [
            {'id': 'year', 'name': 'Year', 'mandatory': True},
            {'id': 'year_range', 'name': 'Year Range', 'mandatory': True},
            {'id': 'make', 'name': 'Make', 'mandatory': True},
            {'id': 'model', 'name': 'Model', 'mandatory': True},
            {'id': 'submodel', 'name': 'Submodel', 'mandatory': True},
            {'id': 'region', 'name': 'Region', 'mandatory': False},
            {'id': 'drivetype', 'name': 'Drive Type', 'mandatory': False},
            {'id': 'vehicletype', 'name': 'Vehicle Type', 'mandatory': False},
            {'id': 'brakesystem', 'name': 'Brake System', 'mandatory': False},
            {'id': 'bodytype', 'name': 'Body Type', 'mandatory': False},
            {'id': 'wheelbase', 'name': 'Wheel Base', 'mandatory': False},
            {'id': 'class', 'name': 'Vehicle Class', 'mandatory': False},
            {'id': 'bedtype', 'name': 'Bed Type', 'mandatory': False},
            {'id': 'bedlength', 'name': 'Bed Length', 'mandatory': False},
            {'id': 'bodynumdoors', 'name': 'Body Number of Doors', 'mandatory': False},
            {'id': 'braketype', 'name': 'Brake Type', 'mandatory': False},
            {'id': 'brakeabs', 'name': 'Brake ABS', 'mandatory': False},
            {'id': 'engineblock', 'name': 'Engine Block', 'mandatory': False},
            {'id': 'fueltypename', 'name': 'Fuel Type', 'mandatory': False}
        ]

    def export_query_all_data(
            self,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            sort_by: Optional[str] = None,
            sort_desc: bool = False,
            table_filters: Optional[Dict[str, Any]] = None,
            progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            results, total_count = self.execute_query(
                filter_panels=filter_panels,
                columns=columns,
                page=1,
                page_size=1,
                sort_by=sort_by,
                sort_desc=sort_desc,
                table_filters=table_filters
            )

            if total_count == 0:
                return []

            batch_size = 1000
            all_results = []
            total_processed = 0

            for page in range(1, (total_count + batch_size - 1) // batch_size + 1):
                batch_results, _ = self.execute_query(
                    filter_panels=filter_panels,
                    columns=columns,
                    page=page,
                    page_size=batch_size,
                    sort_by=sort_by,
                    sort_desc=sort_desc,
                    table_filters=table_filters
                )

                all_results.extend(batch_results)
                total_processed += len(batch_results)

                if progress_callback:
                    progress_callback(total_processed, total_count)

                if total_processed >= total_count:
                    break

            return all_results

        except SQLAlchemyError as e:
            self._logger.error(f'Error executing export query: {str(e)}')
            raise DatabaseHandlerError(f'Error executing export query: {str(e)}') from e