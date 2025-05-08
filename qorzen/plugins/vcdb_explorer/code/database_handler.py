from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, cast

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
    EngineBoreStroke, EngineConfig2, EngineDesignation, EngineVersion, FuelDeliveryConfig,
    FuelDeliverySubType, FuelDeliveryType, FuelSystemControlType, FuelSystemDesign,
    FuelType, IgnitionSystemType, Make, Mfr, MfrBodyCode, Model, PowerOutput,
    PublicationStage, Region, SpringType, SpringTypeConfig, SteeringConfig,
    SteeringSystem, SteeringType, SubModel, Transmission, TransmissionBase,
    TransmissionControlType, TransmissionMfrCode, TransmissionNumSpeeds,
    TransmissionType, Valves, Vehicle, VehicleToBodyConfig, VehicleToBodyStyleConfig,
    VehicleToBedConfig, VehicleToBrakeConfig, VehicleToClass, VehicleToDriveType,
    VehicleToEngineConfig, VehicleToMfrBodyCode, VehicleToSpringTypeConfig,
    VehicleToSteeringConfig, VehicleToTransmission, VehicleToWheelBase,
    VehicleType, VehicleTypeGroup, WheelBase, Year
)


class DatabaseHandlerError(Exception):
    """Base exception for database handler errors."""
    pass


class DatabaseHandler:
    """Handler for database operations in the VCdb Explorer plugin.

    This class integrates with the core DatabaseManager to provide
    specialized queries for the VCdb Explorer plugin.
    """

    # Connection name used for the VCdb database
    CONNECTION_NAME = "vcdb_explorer"

    def __init__(
            self,
            database_manager: DatabaseManager,
            event_bus: EventBusManager,
            thread_manager: ThreadManager,
            logger: logging.Logger
    ) -> None:
        """Initialize the database handler.

        Args:
            database_manager: The core database manager
            event_bus: The core event bus manager
            thread_manager: The core thread manager
            logger: The logger instance
        """
        self._db_manager = database_manager
        self._event_bus = event_bus
        self._thread_manager = thread_manager
        self._logger = logger
        self._initialized = False
        self._query_lock = threading.RLock()
        self._connection_config: Optional[DatabaseConnectionConfig] = None

        # Map filter types to model classes and attribute names
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

        # Subscribe to event handlers
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
        """Configure the database connection.

        Args:
            host: The database host
            port: The database port
            database: The database name
            user: The database user
            password: The database password
            db_type: The database type
            pool_size: The connection pool size
            max_overflow: Maximum connection overflow
            pool_recycle: Connection recycle time in seconds
            echo: Whether to echo SQL
        """
        self._logger.debug(f'Configuring VCdb database connection: {host}:{port}/{database}')

        # Create connection configuration
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

        # Register the connection with the database manager
        try:
            self._db_manager.register_connection(self._connection_config)
            self._initialized = True

            # Test the connection
            with self.session() as session:
                result = session.execute(select(func.count()).select_from(Vehicle)).scalar()
                self._logger.info(f'Connected to VCdb database. Vehicle count: {result}')

        except Exception as e:
            self._logger.error(f'Failed to initialize VCdb database connection: {str(e)}')
            self._initialized = False
            raise DatabaseHandlerError(f'Failed to initialize VCdb database connection: {str(e)}') from e

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a database session for the VCdb database.

        Yields:
            A SQLAlchemy session

        Raises:
            DatabaseHandlerError: If the database handler is not initialized
            or if a database error occurs
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self._db_manager.session(self.CONNECTION_NAME) as session:
                yield session
        except DatabaseError as e:
            raise DatabaseHandlerError(f'Database error: {str(e)}') from e

    def shutdown(self) -> None:
        """Shut down the database handler."""
        if not self._initialized:
            return

        try:
            # Unsubscribe from events
            self._event_bus.unsubscribe(subscriber_id='vcdb_explorer_handler')

            # Unregister the connection from the database manager
            if self._db_manager:
                try:
                    self._db_manager.unregister_connection(self.CONNECTION_NAME)
                except Exception as e:
                    self._logger.warning(f'Error unregistering database connection: {str(e)}')

            self._initialized = False
            self._logger.info('VCdb Database Handler shut down successfully')

        except Exception as e:
            self._logger.error(f'Error shutting down VCdb Database Handler: {str(e)}')

    def _on_filter_changed(self, event: Event) -> None:
        """Handle filter changed events.

        Args:
            event: The event containing filter change information
        """
        payload = event.payload
        filter_panel_id = payload.get('panel_id')
        filter_type = payload.get('filter_type')
        values = payload.get('values', [])
        current_filters = payload.get('current_filters', {})
        auto_populate = payload.get('auto_populate', False)

        self._logger.debug(
            f'Filter changed event: panel={filter_panel_id}, '
            f'type={filter_type}, values={values}, auto_populate={auto_populate}'
        )

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
        """Handle query execution events.

        Args:
            event: The event containing query execution parameters
        """
        payload = event.payload
        filter_panels = payload.get('filter_panels', [])
        columns = payload.get('columns', [])
        page = payload.get('page', 1)
        page_size = payload.get('page_size', 100)
        sort_by = payload.get('sort_by')
        sort_desc = payload.get('sort_desc', False)
        table_filters = payload.get('table_filters', {})
        callback_id = payload.get('callback_id')

        self._logger.debug(
            f'Query execute event: panels={len(filter_panels)}, '
            f'columns={columns}, page={page}'
        )

        # Local failure callback matching (str) -> None
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
            on_completed=self._publish_query_results,  # already (Dict)->None
            on_failed=_on_failed,                     # now ()->None or (str)->None
            name=f'query_execute_{time.time()}',
            submitter='vcdb_explorer'
        )

    def _refresh_filters(
            self,
            filter_panel_id: str,
            changed_filter_type: str,
            current_filters: Dict[str, List[int]]
    ) -> None:
        """Refresh filter values based on current selections.

        Args:
            filter_panel_id: The ID of the filter panel
            changed_filter_type: The type of filter that changed
            current_filters: The current filter values
        """
        self._logger.debug(
            f'Refreshing filters for panel {filter_panel_id} after {changed_filter_type} change'
        )

        exclude_filters = {changed_filter_type}
        if changed_filter_type == 'year_range':
            exclude_filters.add('year')
        elif changed_filter_type == 'year':
            exclude_filters.add('year_range')

        results = {}
        with self._query_lock:
            try:
                for filter_type in self._filter_map.keys():
                    if filter_type != changed_filter_type and filter_type != 'year_range' and filter_type != 'year':
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

        # Publish filter refresh results
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
        """
        Execute a query in a worker thread and return the results dict.
        """
        self._logger.debug(
            f'Executing query in thread: panels={len(filter_panels)}, page={page}, page_size={page_size}'
        )
        with self._query_lock:
            try:
                start_time = time.time()
                results, total_count = self.execute_query(
                    filter_panels, columns, page, page_size, sort_by, sort_desc, table_filters
                )
                duration = time.time() - start_time
                self._logger.debug(
                    f'Query executed in {duration:.3f}s: {len(results)} rows of {total_count} total'
                )
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
        """Runs on the Qt thread: fire the query_results event."""
        self._event_bus.publish(
            event_type=VCdbEventType.query_results(),
            source='vcdb_explorer',
            payload=payload,
            synchronous=False
        )

    def _publish_query_failed(self, err: Exception) -> None:
        """Runs on the Qt thread if the thread errors."""
        callback_id = getattr(err, 'callback_id', '<unknown>')
        self._event_bus.publish(
            event_type=VCdbEventType.query_results(),
            source='vcdb_explorer',
            payload={
                'results': [],
                'total_count': 0,
                'error': str(err),
                'callback_id': callback_id
            },
            synchronous=False
        )

    def get_filter_values(
            self,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            exclude_filters: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get values for a specific filter type.

        Args:
            filter_type: The type of filter
            current_filters: The current filter values
            exclude_filters: Filters to exclude from the query

        Returns:
            A list of filter values with id, name, and count

        Raises:
            DatabaseHandlerError: If the database handler is not initialized
            or if a database error occurs
        """
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
                    query = select(
                        Year.year_id.label('id'),
                        Year.year_id.label('name'),
                        func.count(Year.year_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Year, BaseVehicle.year_id == Year.year_id
                    )

                    query = query.group_by(Year.year_id).order_by(Year.year_id)

                elif filter_type == 'make':
                    query = select(
                        Make.make_id.label('id'),
                        Make.make_name.label('name'),
                        func.count(Make.make_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Make, BaseVehicle.make_id == Make.make_id
                    )

                    query = query.group_by(Make.make_id, Make.make_name).order_by(Make.make_name)

                elif filter_type == 'model':
                    query = select(
                        Model.model_id.label('id'),
                        Model.model_name.label('name'),
                        func.count(Model.model_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Model, BaseVehicle.model_id == Model.model_id
                    )

                    query = query.group_by(Model.model_id, Model.model_name).order_by(Model.model_name)

                elif filter_type == 'submodel':
                    query = select(
                        SubModel.sub_model_id.label('id'),
                        SubModel.sub_model_name.label('name'),
                        func.count(SubModel.sub_model_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(SubModel, Vehicle.sub_model_id == SubModel.sub_model_id)
                    query = query.group_by(SubModel.sub_model_id, SubModel.sub_model_name).order_by(
                        SubModel.sub_model_name)

                elif filter_type == 'region':
                    query = select(
                        Region.region_id.label('id'),
                        Region.region_name.label('name'),
                        func.count(Region.region_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(Region, Vehicle.region_id == Region.region_id)
                    query = query.group_by(Region.region_id, Region.region_name).order_by(Region.region_name)

                elif filter_type == 'drivetype':
                    vtdt = aliased(VehicleToDriveType)
                    dt = aliased(DriveType)

                    query = select(
                        dt.drive_type_id.label('id'),
                        dt.drive_type_name.label('name'),
                        func.count(dt.drive_type_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(vtdt, Vehicle.vehicle_id == vtdt.vehicle_id).join(dt,
                                                                                         vtdt.drive_type_id == dt.drive_type_id)
                    query = query.group_by(dt.drive_type_id, dt.drive_type_name).order_by(dt.drive_type_name)

                elif filter_type == 'wheelbase':
                    vtwb = aliased(VehicleToWheelBase)
                    wb = aliased(WheelBase)

                    query = select(
                        wb.wheel_base_id.label('id'),
                        wb.wheel_base.label('name'),
                        func.count(wb.wheel_base_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(vtwb, Vehicle.vehicle_id == vtwb.vehicle_id).join(wb,
                                                                                         vtwb.wheel_base_id == wb.wheel_base_id)
                    query = query.group_by(wb.wheel_base_id, wb.wheel_base).order_by(wb.wheel_base)

                elif filter_type == 'bedtype':
                    vtbc = aliased(VehicleToBedConfig)
                    bc = aliased(BedConfig)
                    bt = aliased(BedType)

                    query = select(
                        bt.bed_type_id.label('id'),
                        bt.bed_type_name.label('name'),
                        func.count(bt.bed_type_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id).join(
                        bc, vtbc.bed_config_id == bc.bed_config_id
                    ).join(
                        bt, bc.bed_type_id == bt.bed_type_id
                    )

                    query = query.group_by(bt.bed_type_id, bt.bed_type_name).order_by(bt.bed_type_name)

                elif filter_type == 'bedlength':
                    vtbc = aliased(VehicleToBedConfig)
                    bc = aliased(BedConfig)
                    bl = aliased(BedLength)

                    query = select(
                        bl.bed_length_id.label('id'),
                        bl.bed_length.label('name'),
                        func.count(bl.bed_length_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id).join(
                        bc, vtbc.bed_config_id == bc.bed_config_id
                    ).join(
                        bl, bc.bed_length_id == bl.bed_length_id
                    )

                    query = query.group_by(bl.bed_length_id, bl.bed_length).order_by(bl.bed_length)

                else:
                    pk_column = getattr(model_class, model_class.__table__.primary_key.columns.keys()[0])
                    name_column = getattr(model_class, attr_name)

                    query = select(
                        pk_column.label('id'),
                        name_column.label('name'),
                        func.count(pk_column).label('count')
                    ).select_from(Vehicle)

                query = self._apply_filters(query, current_filters, exclude_filters)

                self._logger.debug(f'Executing filter values query for {filter_type}')
                result = session.execute(query)

                values = []
                for row in result:
                    values.append({
                        'id': row.id,
                        'name': str(row.name),
                        'count': row.count
                    })

                return values

        except SQLAlchemyError as e:
            self._logger.error(f'Error getting filter values for {filter_type}: {str(e)}')
            raise DatabaseHandlerError(f'Error getting filter values for {filter_type}: {str(e)}') from e

    def _apply_filters(
            self,
            query: Select,
            filters: Dict[str, List[int]],
            exclude_filters: Set[str],
            target_model: Any = None
    ) -> Select:
        """Apply filters to a query.

        Args:
            query: The query to apply filters to
            filters: The filters to apply
            exclude_filters: Filters to exclude
            target_model: The target model

        Returns:
            The modified query
        """
        if not filters:
            return query

        self._logger.debug(f'Applying filters: {filters}, excluding: {exclude_filters}')

        for filter_type, values in filters.items():
            if not values or filter_type in exclude_filters:
                continue

            if target_model and filter_type in self._filter_map and self._filter_map[filter_type][0] == target_model:
                continue

            if filter_type == 'year':
                if len(values) == 2 and values[0] <= values[1]:
                    query = query.filter(BaseVehicle.year_id.between(values[0], values[1]))
                    self._logger.debug(f'Applied year range filter: {values[0]}-{values[1]}')
                else:
                    query = query.filter(BaseVehicle.year_id.in_(values))
                    self._logger.debug(f'Applied year filter: {values}')

            elif filter_type == 'make':
                query = query.filter(BaseVehicle.make_id.in_(values))
                self._logger.debug(f'Applied make filter: {values}')

            elif filter_type == 'model':
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

                query = query.join(
                    vtdt, Vehicle.vehicle_id == vtdt.vehicle_id
                ).join(
                    dt, vtdt.drive_type_id == dt.drive_type_id
                ).filter(dt.drive_type_id.in_(values))

                self._logger.debug(f'Applied drive type filter: {values}')

            elif filter_type == 'wheelbase':
                vtwb = aliased(VehicleToWheelBase)
                wb = aliased(WheelBase)

                query = query.join(
                    vtwb, Vehicle.vehicle_id == vtwb.vehicle_id
                ).join(
                    wb, vtwb.wheel_base_id == wb.wheel_base_id
                ).filter(wb.wheel_base_id.in_(values))

                self._logger.debug(f'Applied wheel base filter: {values}')

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
        """Execute a query with the given parameters.

        Args:
            filter_panels: The filter panel configurations
            columns: The columns to include in the results
            page: The page number
            page_size: The page size
            sort_by: The column to sort by
            sort_desc: Whether to sort in descending order
            table_filters: Additional table filters

        Returns:
            A tuple of (results, total_count)

        Raises:
            DatabaseHandlerError: If the database handler is not initialized
            or if a database error occurs
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self.session() as session:
                self._logger.debug(
                    f'Executing query: panels={len(filter_panels)}, columns={columns}, '
                    f'page={page}, page_size={page_size}'
                )

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
        """Build a query for the specified columns.

        Args:
            vehicle_ids: The vehicle IDs subquery
            columns: The columns to include in the results

        Returns:
            The constructed query
        """
        query = select(Vehicle.vehicle_id).select_from(Vehicle)
        query = query.filter(Vehicle.vehicle_id.in_(vehicle_ids))

        # Always include basic vehicle information
        query = query.add_columns(
            BaseVehicle.year_id.label('year')
        ).join(
            BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id, isouter=True
        )

        query = query.add_columns(
            Make.make_id.label('make_id'),
            Make.make_name.label('make')
        ).join(
            Make, BaseVehicle.make_id == Make.make_id, isouter=True
        )

        query = query.add_columns(
            Model.model_id.label('model_id'),
            Model.model_name.label('model')
        ).join(
            Model, BaseVehicle.model_id == Model.model_id, isouter=True
        )

        query = query.add_columns(
            SubModel.sub_model_id.label('submodel_id'),
            SubModel.sub_model_name.label('submodel')
        ).join(
            SubModel, Vehicle.sub_model_id == SubModel.sub_model_id, isouter=True
        )

        # Add optional columns based on request
        for column in columns:
            if column == 'region':
                query = query.add_columns(
                    Region.region_id.label('region_id'),
                    Region.region_name.label('region')
                ).outerjoin(
                    Region, Vehicle.region_id == Region.region_id
                )

            elif column == 'vehicle_type':
                query = query.add_columns(
                    VehicleType.vehicle_type_id.label('vehicle_type_id'),
                    VehicleType.vehicle_type_name.label('vehicle_type')
                ).outerjoin(
                    VehicleType, Model.vehicle_type_id == VehicleType.vehicle_type_id
                )

            elif column == 'drive_type':
                vtdt = aliased(VehicleToDriveType)
                dt = aliased(DriveType)

                query = query.add_columns(
                    dt.drive_type_id.label('drive_type_id'),
                    dt.drive_type_name.label('drive_type')
                ).outerjoin(
                    vtdt, Vehicle.vehicle_id == vtdt.vehicle_id
                ).outerjoin(
                    dt, vtdt.drive_type_id == dt.drive_type_id
                )

        return query

    def _apply_table_filters(self, query: Select, table_filters: Dict[str, Any]) -> Select:
        """Apply table filters to a query.

        Args:
            query: The query to apply filters to
            table_filters: The filters to apply

        Returns:
            The modified query
        """
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
        """Apply sorting to a query.

        Args:
            query: The query to apply sorting to
            sort_by: The column to sort by
            sort_desc: Whether to sort in descending order

        Returns:
            The modified query
        """
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
        """Get the available columns for queries.

        Returns:
            A list of column definitions with id and name
        """
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
        """Get the available filters for queries.

        Returns:
            A list of filter definitions with id, name, and mandatory flag
        """
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