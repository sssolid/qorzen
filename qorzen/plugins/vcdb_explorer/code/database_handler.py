from __future__ import annotations

import logging
import threading
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
from qorzen.core.thread_manager import ThreadManager, TaskResult
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
    """Exception raised for errors in the DatabaseHandler."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the error with a message and optional details.

        Args:
            message: The error message
            details: Optional details about the error
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class DatabaseHandler:
    """Handler for VCDB database operations."""

    CONNECTION_NAME = 'vcdb_explorer'

    def __init__(
            self,
            database_manager: DatabaseManager,
            event_bus: EventBusManager,
            thread_manager: ThreadManager,
            logger: logging.Logger
    ) -> None:
        """
        Initialize the DatabaseHandler.

        Args:
            database_manager: Database manager for connection handling
            event_bus: Event bus for inter-component communication
            thread_manager: Thread manager for background tasks
            logger: Logger for this component
        """
        self._db_manager = database_manager
        self._event_bus = event_bus
        self._thread_manager = thread_manager
        self._logger = logger
        self._initialized = False
        self._query_lock = threading.RLock()
        self._connection_config: Optional[DatabaseConnectionConfig] = None

        # Map of filter types to database models and attribute names
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
        """
        Configure the database connection.

        Args:
            host: Database host address
            port: Database port
            database: Database name
            user: Database username
            password: Database password
            db_type: Database type (default: postgresql)
            pool_size: Connection pool size (default: 5)
            max_overflow: Maximum pool overflow (default: 10)
            pool_recycle: Connection recycle time in seconds (default: 3600)
            echo: Whether to echo SQL statements (default: False)
        """
        self._logger.debug(f'Configuring VCdb database connection: {host}:{port}/{database}')

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
        """
        Create a database session context manager.

        Yields:
            A database session

        Raises:
            DatabaseHandlerError: If not initialized or a database error occurs
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self._db_manager.session(self.CONNECTION_NAME) as session:
                yield session
        except DatabaseError as e:
            raise DatabaseHandlerError(f'Database error: {str(e)}') from e

    def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
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
        """
        Handle filter changed events.

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
            f'Filter changed event: panel={filter_panel_id}, type={filter_type}, '
            f'values={values}, auto_populate={auto_populate}'
        )

        # Use thread manager for filter refresh
        if auto_populate:
            self._thread_manager.submit_task(
                self._refresh_filters,
                filter_panel_id=filter_panel_id,
                filter_type=filter_type,
                current_filters=current_filters,
                name=f'filter_refresh_{filter_panel_id}_{filter_type}',
                submitter='vcdb_explorer'
            )

    def _on_query_execute(self, event: Event) -> None:
        """
        Handle query execute events.

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

        for i, panel in enumerate(filter_panels):
            if panel:
                self._logger.debug(f'Filter panel {i}: {panel}')
            else:
                self._logger.debug(f'Filter panel {i}: Empty')

        # Define error handler for failed tasks
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

        # Submit the query task using thread manager
        self._thread_manager.submit_task(
            self._execute_query_thread,
            filter_panels=filter_panels,
            columns=columns,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_desc=sort_desc,
            table_filters=table_filters,
            callback_id=callback_id,
            name=f'query_execute',
            submitter='vcdb_explorer',
            result_handler=self._handle_query_result
        )

    def _refresh_filters(
            self,
            filter_panel_id: str,
            changed_filter_type: str,
            current_filters: Dict[str, List[int]],
            progress_reporter: Any = None
    ) -> Dict[str, Any]:
        """
        Refresh filter values based on currently selected filters.

        Args:
            filter_panel_id: ID of the filter panel
            changed_filter_type: Type of filter that was changed
            current_filters: Currently selected filter values
            progress_reporter: Progress reporter for the task

        Returns:
            Dictionary containing refresh results
        """
        self._logger.debug(f'Refreshing filters for panel {filter_panel_id} after {changed_filter_type} change')

        exclude_filters = {changed_filter_type}
        if changed_filter_type == 'year_range':
            exclude_filters.add('year')
        elif changed_filter_type == 'year':
            exclude_filters.add('year_range')

        results = {}

        with self._query_lock:
            try:
                # Process standard filters
                for filter_type in self._filter_map.keys():
                    if filter_type != changed_filter_type and filter_type != 'year_range' and (filter_type != 'year'):
                        try:
                            if progress_reporter:
                                progress_reporter.report_progress(
                                    int(10 + (80 * len(results) / len(self._filter_map))),
                                    f"Processing {filter_type} filter"
                                )

                            values = self.get_filter_values(filter_type, current_filters, exclude_filters)
                            results[filter_type] = values
                            self._logger.debug(f'Refreshed {filter_type}: {len(values)} values')

                        except Exception as e:
                            self._logger.error(f'Error refreshing {filter_type}: {str(e)}')

                # Specifically handle the year filter if not the one that changed
                if changed_filter_type != 'year' and 'year' in self._filter_map:
                    try:
                        values = self.get_filter_values('year', current_filters, exclude_filters)
                        results['year'] = values
                    except Exception as e:
                        self._logger.error(f'Error refreshing year: {str(e)}')

            except Exception as e:
                self._logger.error(f'Error during filter refresh: {str(e)}')
                return {"success": False, "error": str(e)}

        # Publish results through event bus
        self._event_bus.publish(
            event_type=VCdbEventType.filters_refreshed(),
            source='vcdb_explorer',
            payload={
                'panel_id': filter_panel_id,
                'filter_values': results
            }
        )

        return {
            "success": True,
            "filter_count": len(results)
        }

    def _handle_query_result(self, result: TaskResult) -> None:
        """
        Handle the query execution task result.

        Args:
            result: The task result
        """
        if not result.success or not result.result:
            self._logger.error(f'Query failed: {result.error}')
            return

        data = result.result
        callback_id = data.get('callback_id')

        # If there was an error, publish the error
        if 'error' in data:
            self._event_bus.publish(
                event_type=VCdbEventType.query_results(),
                source='vcdb_explorer',
                payload={
                    'results': [],
                    'total_count': 0,
                    'error': data['error'],
                    'callback_id': callback_id
                },
                synchronous=False
            )
            return

    def _execute_query_thread(
            self,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            page: int,
            page_size: int,
            sort_by: Optional[str],
            sort_desc: bool,
            table_filters: Dict[str, Any],
            callback_id: Optional[str],
            progress_reporter: Any = None
    ) -> Dict[str, Any]:
        """
        Execute a query in a background thread.

        Args:
            filter_panels: Filter panel configurations
            columns: Columns to include in the result
            page: Page number
            page_size: Page size
            sort_by: Column to sort by
            sort_desc: Sort direction (descending if True)
            table_filters: Additional table filters
            callback_id: Callback ID for result identification
            progress_reporter: Progress reporter for the task

        Returns:
            Dictionary with query results
        """
        self._logger.debug(
            f'Executing query in thread: panels={len(filter_panels)}, '
            f'page={page}, page_size={page_size}'
        )

        valid_panels = [panel for panel in filter_panels if panel]
        if not valid_panels:
            self._logger.warning('No filter conditions found in any panel')

        with self._query_lock:
            try:
                if progress_reporter:
                    progress_reporter.report_progress(10, "Starting query execution")

                results, total_count = self.execute_query(
                    filter_panels, columns, page, page_size, sort_by, sort_desc, table_filters
                )

                if progress_reporter:
                    progress_reporter.report_progress(90, "Query completed, preparing results")

                self._logger.debug(f'Query executed: {len(results)} rows of {total_count} total')

                # Return results to be published
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

    # Rest of the methods remain largely unchanged
    def get_filter_values(
            self,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            exclude_filters: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get available values for a specific filter type."""
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        if exclude_filters is None:
            exclude_filters = set()

        try:
            if filter_type not in self._filter_map:
                raise DatabaseHandlerError(f'Unknown filter type: {filter_type}')

            model_class, attr_name = self._filter_map[filter_type]

            with self.session() as session:
                # Build the appropriate query based on filter type
                if filter_type == 'year':
                    query = select(
                        Year.year_id.label('id'),
                        Year.year_id.label('name'),
                        func.count(Year.year_id).label('count')
                    ).select_from(Vehicle).join(
                        BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Year, BaseVehicle.year_id == Year.year_id
                    ).group_by(Year.year_id).order_by(Year.year_id)

                elif filter_type == 'make':
                    query = select(
                        Make.make_id.label('id'),
                        Make.make_name.label('name'),
                        func.count(Make.make_id).label('count')
                    ).select_from(Vehicle).join(
                        BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Make, BaseVehicle.make_id == Make.make_id
                    ).group_by(Make.make_id, Make.make_name).order_by(Make.make_name)

                elif filter_type == 'model':
                    query = select(
                        Model.model_id.label('id'),
                        Model.model_name.label('name'),
                        func.count(Model.model_id).label('count')
                    ).select_from(Vehicle).join(
                        BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Model, BaseVehicle.model_id == Model.model_id
                    ).group_by(Model.model_id, Model.model_name).order_by(Model.model_name)

                elif filter_type == 'submodel':
                    query = select(
                        SubModel.sub_model_id.label('id'),
                        SubModel.sub_model_name.label('name'),
                        func.count(SubModel.sub_model_id).label('count')
                    ).select_from(Vehicle).join(
                        SubModel, Vehicle.sub_model_id == SubModel.sub_model_id
                    ).group_by(SubModel.sub_model_id, SubModel.sub_model_name).order_by(SubModel.sub_model_name)

                elif filter_type == 'region':
                    query = select(
                        Region.region_id.label('id'),
                        Region.region_name.label('name'),
                        func.count(Region.region_id).label('count')
                    ).select_from(Vehicle).join(
                        Region, Vehicle.region_id == Region.region_id
                    ).group_by(Region.region_id, Region.region_name).order_by(Region.region_name)

                elif filter_type == 'drivetype':
                    vtdt = aliased(VehicleToDriveType)
                    dt = aliased(DriveType)
                    query = select(
                        dt.drive_type_id.label('id'),
                        dt.drive_type_name.label('name'),
                        func.count(dt.drive_type_id).label('count')
                    ).select_from(Vehicle).join(
                        vtdt, Vehicle.vehicle_id == vtdt.vehicle_id
                    ).join(
                        dt, vtdt.drive_type_id == dt.drive_type_id
                    ).group_by(dt.drive_type_id, dt.drive_type_name).order_by(dt.drive_type_name)

                elif filter_type == 'wheelbase':
                    vtwb = aliased(VehicleToWheelBase)
                    wb = aliased(WheelBase)
                    query = select(
                        wb.wheel_base_id.label('id'),
                        wb.wheel_base.label('name'),
                        func.count(wb.wheel_base_id).label('count')
                    ).select_from(Vehicle).join(
                        vtwb, Vehicle.vehicle_id == vtwb.vehicle_id
                    ).join(
                        wb, vtwb.wheel_base_id == wb.wheel_base_id
                    ).group_by(wb.wheel_base_id, wb.wheel_base).order_by(wb.wheel_base)

                elif filter_type == 'bedtype':
                    vtbc = aliased(VehicleToBedConfig)
                    bc = aliased(BedConfig)
                    bt = aliased(BedType)
                    query = select(
                        bt.bed_type_id.label('id'),
                        bt.bed_type_name.label('name'),
                        func.count(bt.bed_type_id).label('count')
                    ).select_from(Vehicle).join(
                        vtbc, Vehicle.vehicle_id == vtbc.vehicle_id
                    ).join(
                        bc, vtbc.bed_config_id == bc.bed_config_id
                    ).join(
                        bt, bc.bed_type_id == bt.bed_type_id
                    ).group_by(bt.bed_type_id, bt.bed_type_name).order_by(bt.bed_type_name)

                elif filter_type == 'bedlength':
                    vtbc = aliased(VehicleToBedConfig)
                    bc = aliased(BedConfig)
                    bl = aliased(BedLength)
                    query = select(
                        bl.bed_length_id.label('id'),
                        bl.bed_length.label('name'),
                        func.count(bl.bed_length_id).label('count')
                    ).select_from(Vehicle).join(
                        vtbc, Vehicle.vehicle_id == vtbc.vehicle_id
                    ).join(
                        bc, vtbc.bed_config_id == bc.bed_config_id
                    ).join(
                        bl, bc.bed_length_id == bl.bed_length_id
                    ).group_by(bl.bed_length_id, bl.bed_length).order_by(bl.bed_length)

                else:
                    # Generic case for other filter types
                    pk_column = getattr(model_class, model_class.__table__.primary_key.columns.keys()[0])
                    name_column = getattr(model_class, attr_name)
                    query = select(
                        pk_column.label('id'),
                        name_column.label('name'),
                        func.count(pk_column).label('count')
                    ).select_from(Vehicle)

                # Apply filters from current selection
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
        """
        Apply filters to a query.

        Args:
            query: The base query
            filters: Dictionary of filter type to values
            exclude_filters: Set of filter types to exclude
            target_model: Optional target model for specialized filtering

        Returns:
            The modified query with filters applied
        """
        if not filters:
            self._logger.debug('No filters to apply')
            return query

        self._logger.debug(f'Applying filters: {filters}, excluding: {exclude_filters}')

        # Check if the query already has a join to BaseVehicle
        has_base_vehicle_join = False
        for clause in query._from_obj:
            if isinstance(clause, sqlalchemy.sql.elements.Join) and hasattr(clause, 'right') and (
                    clause.right == BaseVehicle.__table__
            ):
                has_base_vehicle_join = True
                break

        # Process each filter
        for filter_type, values in filters.items():
            if not values:
                self._logger.debug(f'Skipping empty filter: {filter_type}')
                continue

            if filter_type in exclude_filters:
                self._logger.debug(f'Skipping excluded filter: {filter_type}')
                continue

            if target_model and filter_type in self._filter_map and (
                    self._filter_map[filter_type][0] == target_model
            ):
                self._logger.debug(f'Skipping filter for target model: {filter_type}')
                continue

            try:
                # Apply filter based on type
                if filter_type == 'year':
                    if not has_base_vehicle_join:
                        query = query.join(
                            BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                        )
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
                        query = query.join(
                            BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                        )
                        has_base_vehicle_join = True
                        self._logger.debug('Added join to BaseVehicle for make filter')

                    query = query.filter(BaseVehicle.make_id.in_(values))
                    self._logger.debug(f'Applied make filter: {values}')

                elif filter_type == 'model':
                    if not has_base_vehicle_join:
                        query = query.join(
                            BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                        )
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
                        query = query.join(
                            BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                        )
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
                    engine_block_ids = [
                        int(v) if isinstance(v, str) and v.isdigit() else v for v in values
                    ]
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
                            query = query.join(
                                BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                            )
                            has_base_vehicle_join = True

                        query = query.join(Year, BaseVehicle.year_id == Year.year_id)
                        query = query.filter(getattr(Year, attr_name).in_(values))
                        self._logger.debug(f'Applied {filter_type} filter with year join: {values}')

                    elif model_class == Make:
                        if not has_base_vehicle_join:
                            query = query.join(
                                BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                            )
                            has_base_vehicle_join = True

                        query = query.join(Make, BaseVehicle.make_id == Make.make_id)
                        query = query.filter(getattr(Make, attr_name).in_(values))
                        self._logger.debug(f'Applied {filter_type} filter with make join: {values}')

                    elif model_class == Model:
                        if not has_base_vehicle_join:
                            query = query.join(
                                BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                            )
                            has_base_vehicle_join = True

                        query = query.join(Model, BaseVehicle.model_id == Model.model_id)
                        query = query.filter(getattr(Model, attr_name).in_(values))
                        self._logger.debug(f'Applied {filter_type} filter with model join: {values}')

                    else:
                        self._logger.warning(
                            f'Unimplemented filter type in map: {filter_type} '
                            f'({model_class.__name__}.{attr_name})'
                        )

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
        """
        Execute a query with the given parameters.

        Args:
            filter_panels: Filter panel configurations
            columns: Columns to include in the result
            page: Page number (default: 1)
            page_size: Page size (default: 100)
            sort_by: Column to sort by (default: None)
            sort_desc: Sort direction (default: False)
            table_filters: Additional table filters (default: None)

        Returns:
            Tuple of (results, total_count)

        Raises:
            DatabaseHandlerError: If not initialized or a database error occurs
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self.session() as session:
                self._logger.debug(
                    f'Executing query: panels={len(filter_panels)}, columns={columns}, '
                    f'page={page}, page_size={page_size}'
                )

                # Start with base query
                base_query = select(Vehicle.vehicle_id).select_from(Vehicle)

                # Apply filter panel conditions
                if filter_panels:
                    panel_conditions = []
                    for panel in filter_panels:
                        if not panel:
                            continue

                        panel_query = select(Vehicle.vehicle_id).select_from(Vehicle)
                        panel_query = self._apply_filters(panel_query, panel, set())
                        panel_conditions.append(
                            Vehicle.vehicle_id.in_(panel_query.scalar_subquery())
                        )

                    if panel_conditions:
                        base_query = base_query.filter(or_(*panel_conditions))
                        self._logger.debug(f'Applied {len(panel_conditions)} panel conditions')

                # Get total count
                count_query = select(func.count()).select_from(base_query.alias())
                total_count = session.execute(count_query).scalar() or 0
                self._logger.debug(f'Total count: {total_count}')

                # Build query with selected columns
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

                # Execute query
                self._logger.debug('Executing final query')
                result_rows = session.execute(query).all()

                # Process results
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

    # Rest of the methods remain largely unchanged
    def _build_columns_query(self, vehicle_ids: Any, columns: List[str]) -> Select:
        """Build a query with the requested columns."""
        query = select(Vehicle.vehicle_id).select_from(Vehicle)
        query = query.filter(Vehicle.vehicle_id.in_(vehicle_ids))

        # Add standard joins and columns
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

        # Add optional columns
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
        """Apply additional table filters to the query."""
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
        """Apply sorting to the query."""
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
        """Get available columns for query results."""
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
        """Get available filter types."""
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