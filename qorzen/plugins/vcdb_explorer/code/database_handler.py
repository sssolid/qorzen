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
    Class, CylinderHeadType, DriveType, ElecControlled, EngineBase2,
    EngineBlock, EngineBoreStroke, EngineConfig2, EngineDesignation,
    EngineVersion, FuelDeliveryConfig, FuelDeliverySubType, FuelDeliveryType,
    FuelSystemControlType, FuelSystemDesign, FuelType, IgnitionSystemType,
    Make, Mfr, MfrBodyCode, Model, PowerOutput, PublicationStage, Region,
    SpringType, SpringTypeConfig, SteeringConfig, SteeringSystem, SteeringType,
    SubModel, Transmission, TransmissionBase, TransmissionControlType,
    TransmissionMfrCode, TransmissionNumSpeeds, TransmissionType, Valves,
    Vehicle, VehicleToBodyConfig, VehicleToBodyStyleConfig, VehicleToBedConfig,
    VehicleToBrakeConfig, VehicleToClass, VehicleToDriveType,
    VehicleToEngineConfig, VehicleToMfrBodyCode, VehicleToSpringTypeConfig,
    VehicleToSteeringConfig, VehicleToTransmission, VehicleToWheelBase,
    VehicleType, VehicleTypeGroup, WheelBase, Year
)


class DatabaseHandlerError(Exception):
    """Exception raised for errors in the DatabaseHandler."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class DatabaseHandler:
    """Handler for VCdb database operations."""

    CONNECTION_NAME = 'vcdb_explorer'

    def __init__(
            self,
            database_manager: DatabaseManager,
            event_bus: EventBusManager,
            thread_manager: ThreadManager,
            logger: logging.Logger
    ) -> None:
        """Initialize the DatabaseHandler.

        Args:
            database_manager: The database manager
            event_bus: The event bus for publishing events
            thread_manager: The thread manager for async operations
            logger: The logger instance
        """
        self._db_manager = database_manager
        self._event_bus = event_bus
        self._thread_manager = thread_manager
        self._logger = logger
        self._initialized = False
        self._query_lock = threading.RLock()
        self._connection_config: Optional[DatabaseConnectionConfig] = None

        # Map filter types to database models and attributes
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

        # Subscribe to events
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
            host: Database server hostname
            port: Database server port
            database: Database name
            user: Database username
            password: Database password
            db_type: Database type (default: postgresql)
            pool_size: Connection pool size (default: 5)
            max_overflow: Maximum overflow connections (default: 10)
            pool_recycle: Time in seconds to recycle connections (default: 3600)
            echo: Whether to echo SQL statements (default: False)

        Raises:
            DatabaseHandlerError: If connection fails
        """
        self._logger.debug(f'Configuring VCdb database connection: {host}:{port}/{database}')
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
        """Get a database session.

        Yields:
            Session: A SQLAlchemy session

        Raises:
            DatabaseHandlerError: If the handler is not initialized or database error occurs
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self._db_manager.session(self.CONNECTION_NAME) as session:
                yield session
        except DatabaseError as e:
            raise DatabaseHandlerError(f'Database error: {str(e)}') from e

    def shutdown(self) -> None:
        """Shut down the database handler and clean up resources."""
        if not self._initialized:
            return

        try:
            self._event_bus.unsubscribe(subscriber_id='vcdb_explorer_handler')

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
        """Handle filter changed event.

        Args:
            event: The filter changed event
        """
        payload = event.payload
        filter_panel_id = payload.get('panel_id')
        filter_type = payload.get('filter_type')
        values = payload.get('values', [])
        current_filters = payload.get('current_filters', {})
        auto_populate = payload.get('auto_populate', False)

        self._logger.debug(
            f'Filter changed event: panel={filter_panel_id}, type={filter_type}, values={values}, auto_populate={auto_populate}')

        # Only submit task if auto_populate is True to avoid unnecessary processing
        if auto_populate:
            # Use submit_task (not submit_qt_task) since this is a background operation,
            # not UI update. Qt objects should not be used in this method.
            self._thread_manager.submit_task(
                self._refresh_filters,
                filter_panel_id,
                filter_type,
                current_filters,
                name=f'filter_refresh_{filter_panel_id}_{filter_type}',
                submitter='vcdb_explorer'
            )

    def _on_query_execute(self, event: Event) -> None:
        """Handle query execute event.

        Args:
            event: The query execute event
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

        self._logger.debug(f'Query execute event: panels={len(filter_panels)}, columns={columns}, page={page}')

        def _on_failed(err_msg: str = '<thread error>') -> None:
            """Handle query execution failure.

            Args:
                err_msg: Error message
            """
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

        # Use submit_qt_task as we need to publish results back to UI thread
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

    def _refresh_filters(
            self,
            filter_panel_id: str,
            changed_filter_type: str,
            current_filters: Dict[str, List[int]]
    ) -> None:
        """Refresh filter values based on current filter selections.

        Args:
            filter_panel_id: ID of the filter panel
            changed_filter_type: Type of filter that was changed
            current_filters: Current filter values
        """
        self._logger.debug(f'Refreshing filters for panel {filter_panel_id} after {changed_filter_type} change')

        # Exclude the changed filter and related filters
        exclude_filters = {changed_filter_type}
        if changed_filter_type == 'year_range':
            exclude_filters.add('year')
        elif changed_filter_type == 'year':
            exclude_filters.add('year_range')

        results = {}
        with self._query_lock:  # Prevent concurrent filter refreshes
            try:
                # Process standard filters first
                for filter_type in self._filter_map.keys():
                    if (filter_type != changed_filter_type and
                            filter_type != 'year_range' and
                            filter_type != 'year'):
                        try:
                            values = self.get_filter_values(filter_type, current_filters, exclude_filters)
                            results[filter_type] = values
                            self._logger.debug(f'Refreshed {filter_type}: {len(values)} values')
                        except Exception as e:
                            self._logger.error(f'Error refreshing {filter_type}: {str(e)}')

                # Process year filter if needed
                if changed_filter_type != 'year' and 'year' in self._filter_map:
                    try:
                        values = self.get_filter_values('year', current_filters, exclude_filters)
                        results['year'] = values
                    except Exception as e:
                        self._logger.error(f'Error refreshing year: {str(e)}')
            except Exception as e:
                self._logger.error(f'Error during filter refresh: {str(e)}')

        # Publish results through event bus
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
        """Execute query in a separate thread.

        Args:
            filter_panels: List of filter panel selections
            columns: Columns to include in results
            page: Page number
            page_size: Page size
            sort_by: Column to sort by
            sort_desc: Sort descending if True
            table_filters: Additional table filters
            callback_id: Callback ID for result identification

        Returns:
            Dict containing query results
        """
        self._logger.debug(
            f'Executing query in thread: panels={len(filter_panels)}, page={page}, page_size={page_size}')

        with self._query_lock:  # Prevent concurrent queries
            try:
                start_time = time.time()
                results, total_count = self.execute_query(
                    filter_panels, columns, page, page_size, sort_by, sort_desc, table_filters
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
        """Publish query results through event bus.

        Args:
            payload: Query results payload
        """
        # This method runs in the main thread via Qt signal/slot connection
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
        """Get available values for a filter type based on current selections.

        Args:
            filter_type: Type of filter
            current_filters: Current filter selections
            exclude_filters: Filter types to exclude

        Returns:
            List of filter values with id, name, and count

        Raises:
            DatabaseHandlerError: If database error occurs
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
                # Build query based on filter type
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
                    # Generic approach for other filter types
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

                # Apply current filters to the query
                query = self._apply_filters(query, current_filters, exclude_filters)

                self._logger.debug(f'Executing filter values query for {filter_type}')

                # Execute query and format results
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
            query: Base query
            filters: Filter values to apply
            exclude_filters: Filter types to exclude
            target_model: Target model if filtering for a specific model

        Returns:
            Modified query with filters applied
        """
        if not filters:
            return query

        self._logger.debug(f'Applying filters: {filters}, excluding: {exclude_filters}')

        # Process each filter
        for filter_type, values in filters.items():
            # Skip empty filters or excluded filters
            if not values or filter_type in exclude_filters:
                continue

            # Skip if filtering for target model
            if (target_model and filter_type in self._filter_map and
                    (self._filter_map[filter_type][0] == target_model)):
                continue

            # Apply filter based on filter type
            if filter_type == 'year':
                if len(values) == 2 and values[0] <= values[1]:
                    # Year range filter
                    query = query.filter(BaseVehicle.year_id.between(values[0], values[1]))
                    self._logger.debug(f'Applied year range filter: {values[0]}-{values[1]}')
                else:
                    # Specific years filter
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
                # Ensure we don't create duplicate joins
                query = query.join(
                    vtdt, Vehicle.vehicle_id == vtdt.vehicle_id, isouter=True
                ).join(
                    dt, vtdt.drive_type_id == dt.drive_type_id, isouter=True
                ).filter(dt.drive_type_id.in_(values))
                self._logger.debug(f'Applied drive type filter: {values}')
            elif filter_type == 'wheelbase':
                vtwb = aliased(VehicleToWheelBase)
                wb = aliased(WheelBase)
                # Ensure we don't create duplicate joins
                query = query.join(
                    vtwb, Vehicle.vehicle_id == vtwb.vehicle_id, isouter=True
                ).join(
                    wb, vtwb.wheel_base_id == wb.wheel_base_id, isouter=True
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
        """Execute a query with filtering and pagination.

        Args:
            filter_panels: List of filter panel selections
            columns: Columns to include in results
            page: Page number (default: 1)
            page_size: Page size (default: 100)
            sort_by: Column to sort by (default: None)
            sort_desc: Sort descending if True (default: False)
            table_filters: Additional table filters (default: None)

        Returns:
            Tuple of (results, total_count)

        Raises:
            DatabaseHandlerError: If database error occurs
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self.session() as session:
                self._logger.debug(
                    f'Executing query: panels={len(filter_panels)}, '
                    f'columns={columns}, page={page}, page_size={page_size}'
                )

                # Start with base query for vehicle IDs
                base_query = select(Vehicle.vehicle_id).select_from(Vehicle)

                # Apply filter panels as OR conditions (vehicles matching any panel)
                if filter_panels:
                    panel_conditions = []

                    for panel in filter_panels:
                        if not panel:
                            continue

                        # Create subquery for this panel's conditions
                        panel_query = select(Vehicle.vehicle_id).select_from(Vehicle)
                        panel_query = self._apply_filters(panel_query, panel, set())
                        panel_conditions.append(Vehicle.vehicle_id.in_(panel_query.scalar_subquery()))

                    # Add panel conditions as OR
                    if panel_conditions:
                        base_query = base_query.filter(or_(*panel_conditions))
                        self._logger.debug(f'Applied {len(panel_conditions)} panel conditions')

                # Get total count first
                count_query = select(func.count()).select_from(base_query.alias())
                total_count = session.execute(count_query).scalar() or 0
                self._logger.debug(f'Total count: {total_count}')

                # Build full query with selected columns
                query = self._build_columns_query(base_query.scalar_subquery(), columns)

                # Apply table filters
                if table_filters:
                    query = self._apply_table_filters(query, table_filters)
                    self._logger.debug(f'Applied table filters: {table_filters}')

                # Apply sorting
                if sort_by:
                    query = self._apply_sorting(query, sort_by, sort_desc)
                    self._logger.debug(f"Applied sorting: {sort_by} {('DESC' if sort_desc else 'ASC')}")

                # Apply pagination
                if page > 0 and page_size > 0:
                    query = query.offset((page - 1) * page_size).limit(page_size)
                    self._logger.debug(f'Applied pagination: page={page}, page_size={page_size}')

                self._logger.debug('Executing final query')

                # Execute query and format results
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
        """Build a query with selected columns.

        Args:
            vehicle_ids: Subquery or list of vehicle IDs
            columns: Columns to include in results

        Returns:
            Query with selected columns
        """
        # Start with vehicle ID and standard joins
        query = select(Vehicle.vehicle_id).select_from(Vehicle)
        query = query.filter(Vehicle.vehicle_id.in_(vehicle_ids))

        # Add basic columns always needed
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

        # Add additional columns based on selection
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
        """Apply additional table filters to query.

        Args:
            query: Base query
            table_filters: Table filters to apply

        Returns:
            Modified query with table filters applied
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
        """Apply sorting to query.

        Args:
            query: Base query
            sort_by: Column to sort by
            sort_desc: Sort descending if True

        Returns:
            Modified query with sorting applied
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
        """Get available columns for queries.

        Returns:
            List of column definitions
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
        """Get available filters for queries.

        Returns:
            List of filter definitions
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

    def export_query_all_data(
            self,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            sort_by: Optional[str] = None,
            sort_desc: bool = False,
            table_filters: Optional[Dict[str, Any]] = None,
            progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query to get all matching data for export.

        Args:
            filter_panels: List of filter panel selections
            columns: Columns to include in results
            sort_by: Column to sort by (default: None)
            sort_desc: Sort descending if True (default: False)
            table_filters: Additional table filters (default: None)
            progress_callback: Callback for progress updates (default: None)

        Returns:
            List of all matching records

        Raises:
            DatabaseHandlerError: If database error occurs
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            # Get total count first to estimate batches
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

            # Use batching to avoid loading too much at once
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