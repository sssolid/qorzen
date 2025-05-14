from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast, Awaitable, Union

import sqlalchemy
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased

from qorzen.core.database_manager import DatabaseConnectionConfig, DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.utils.exceptions import DatabaseError, TaskError

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
    TransmissionControlType, TransmissionMfrCode, TransmissionNumSpeeds, TransmissionType,
    Valves, Vehicle, VehicleToBodyConfig, VehicleToBodyStyleConfig, VehicleToBedConfig,
    VehicleToBrakeConfig, VehicleToClass, VehicleToDriveType, VehicleToEngineConfig,
    VehicleToMfrBodyCode, VehicleToSpringTypeConfig, VehicleToSteeringConfig,
    VehicleToTransmission, VehicleToWheelBase, VehicleType, VehicleTypeGroup, WheelBase, Year
)


class DatabaseHandlerError(Exception):
    """Exception raised for database handler errors.

    Attributes:
        message: Error message
        details: Additional error details
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class DatabaseHandler:
    """Handler for database operations related to the VCdb Explorer plugin."""

    CONNECTION_NAME = 'vcdb_explorer'

    def __init__(
            self,
            database_manager: DatabaseManager,
            event_bus_manager: EventBusManager,
            task_manager: TaskManager,
            concurrency_manager: ConcurrencyManager,
            logger: logging.Logger
    ) -> None:
        """Initialize the DatabaseHandler.

        Args:
            database_manager: Database manager instance
            event_bus_manager: Event bus manager instance
            task_manager: Task manager instance
            concurrency_manager: Concurrency manager instance
            logger: Logger instance
        """
        self._db_manager = database_manager
        self._event_bus_manager = event_bus_manager
        self._task_manager = task_manager
        self._concurrency_manager = concurrency_manager
        self._logger = logger
        self._initialized = False
        self._connection_config: Optional[DatabaseConnectionConfig] = None
        self._shutting_down = False

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

    async def initialize(self) -> None:
        """Initialize the database handler and subscribe to events."""
        try:
            await self._event_bus_manager.subscribe(
                event_type=VCdbEventType.filter_changed(),
                callback=self._on_filter_changed,
                subscriber_id='vcdb_explorer_handler'
            )

            await self._event_bus_manager.subscribe(
                event_type=VCdbEventType.query_execute(),
                callback=self._on_query_execute,
                subscriber_id='vcdb_explorer_handler'
            )

            self._logger.info("Database handler initialized and subscribed to events")
        except Exception as e:
            self._logger.error(f"Failed to initialize database handler: {str(e)}")
            raise DatabaseHandlerError(f"Failed to initialize database handler: {str(e)}") from e

    async def configure(
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
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            db_type: Database type
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to overflow
            pool_recycle: Number of seconds after which a connection is recycled
            echo: Whether to echo SQL statements

        Raises:
            DatabaseHandlerError: If database connection fails
        """
        self._logger.debug(f'Configuring VCdb database connection: {host}:{port}/{database}')

        try:
            has_connection = await self._db_manager.has_connection(self.CONNECTION_NAME)
            if has_connection:
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

            await self._db_manager.register_connection(self._connection_config)

            # Verify connection by executing a simple query
            async with self._db_manager.async_session(self.CONNECTION_NAME) as session:
                result = await session.execute(select(func.count()).select_from(Vehicle))
                vehicle_count = result.scalar()
                self._logger.info(f'Connected to VCdb database. Vehicle count: {vehicle_count}')

            self._initialized = True
        except Exception as e:
            self._logger.error(f'Failed to initialize VCdb database connection: {str(e)}')
            raise DatabaseHandlerError(f'Failed to initialize VCdb database connection: {str(e)}') from e

    async def _on_filter_changed(self, event: Event) -> None:
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
            f'Filter changed event: panel={filter_panel_id}, type={filter_type}, values={values}, auto_populate={auto_populate}')

        if auto_populate:
            try:
                await self._task_manager.submit_async_task(
                    func=self._refresh_filters,
                    filter_panel_id=filter_panel_id,
                    filter_type=filter_type,
                    current_filters=current_filters,
                    name=f'filter_refresh_{filter_panel_id}_{filter_type}',
                    category=TaskCategory.PLUGIN,
                    plugin_id='vcdb_explorer'
                )
            except TaskError as e:
                self._logger.error(f"Failed to submit refresh filters task: {str(e)}")

    async def _on_query_execute(self, event: Event) -> None:
        """Handle query execute events.

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

        self._logger.debug(f'Query execute event: panels={len(filter_panels)}, columns={columns}, page={page}')

        for i, panel in enumerate(filter_panels):
            if panel:
                self._logger.debug(f'Filter panel {i}: {panel}')
            else:
                self._logger.debug(f'Filter panel {i}: Empty')

        try:
            task_id = await self._task_manager.submit_async_task(
                func=self._execute_query,
                filter_panels=filter_panels,
                columns=columns,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_desc=sort_desc,
                table_filters=table_filters,
                callback_id=callback_id,
                name=f'vcdb_query_execute',
                category=TaskCategory.PLUGIN,
                plugin_id='vcdb_explorer'
            )
            self._logger.debug(f"Submitted query execution task with ID: {task_id}")
        except TaskError as e:
            self._logger.error(f"Failed to submit query execution task: {str(e)}")
            await self._event_bus_manager.publish(
                event_type=VCdbEventType.query_results(),
                source='vcdb_explorer',
                payload={
                    'results': [],
                    'total_count': 0,
                    'error': str(e),
                    'callback_id': callback_id
                }
            )

    async def _refresh_filters(
            self,
            filter_panel_id: str,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            progress_reporter: Any = None
    ) -> Dict[str, Any]:
        """Refresh filter values based on current filter selections.

        Args:
            filter_panel_id: ID of the filter panel
            filter_type: Type of filter that changed
            current_filters: Current filter selections
            progress_reporter: Progress reporter for task progress updates

        Returns:
            Dictionary with refresh results
        """
        self._logger.debug(f'Refreshing filters for panel {filter_panel_id} after {filter_type} change')

        exclude_filters = {filter_type}
        if filter_type == 'year_range':
            exclude_filters.add('year')
        elif filter_type == 'year':
            exclude_filters.add('year_range')

        results = {}

        try:
            if progress_reporter:
                await progress_reporter.report_progress(10, f'Processing filters')

            filter_types = list(self._filter_map.keys())
            total_filters = len(filter_types)

            for i, filter_type_to_refresh in enumerate(filter_types):
                if filter_type_to_refresh != filter_type and filter_type_to_refresh != 'year_range' and (
                        filter_type_to_refresh != 'year'):
                    try:
                        if progress_reporter:
                            await progress_reporter.report_progress(
                                int(10 + 80 * i / total_filters),
                                f'Processing {filter_type_to_refresh} filter'
                            )

                        values = await self.get_filter_values(filter_type_to_refresh, current_filters, exclude_filters)
                        results[filter_type_to_refresh] = values
                        self._logger.debug(f'Refreshed {filter_type_to_refresh}: {len(values)} values')
                    except Exception as e:
                        self._logger.error(f'Error refreshing {filter_type_to_refresh}: {str(e)}')

            # Handle year separately
            if filter_type != 'year' and 'year' in self._filter_map:
                try:
                    values = await self.get_filter_values('year', current_filters, exclude_filters)
                    results['year'] = values
                except Exception as e:
                    self._logger.error(f'Error refreshing year: {str(e)}')

            if progress_reporter:
                await progress_reporter.report_progress(95, f'Publishing filter refresh event')

            # Publish the filter refresh event
            await self._event_bus_manager.publish(
                event_type=VCdbEventType.filters_refreshed(),
                source='vcdb_explorer',
                payload={
                    'panel_id': filter_panel_id,
                    'filter_values': results
                }
            )

            if progress_reporter:
                await progress_reporter.report_progress(100, f'Filter refresh complete')

            return {'success': True, 'filter_count': len(results)}
        except Exception as e:
            self._logger.error(f'Error during filter refresh: {str(e)}')
            return {'success': False, 'error': str(e)}

    async def _execute_query(
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
    ) -> None:
        """Execute query and publish results.

        Args:
            filter_panels: List of filter panels with their selections
            columns: List of columns to include in results
            page: Page number
            page_size: Page size
            sort_by: Column to sort by
            sort_desc: Whether to sort in descending order
            table_filters: Additional table filters
            callback_id: Callback ID for response
            progress_reporter: Progress reporter for task progress
        """
        self._logger.debug(f'Executing query: panels={len(filter_panels)}, page={page}, page_size={page_size}')

        valid_panels = [panel for panel in filter_panels if panel]
        if not valid_panels:
            self._logger.warning('No filter conditions found in any panel')

        try:
            if progress_reporter:
                await progress_reporter.report_progress(10, 'Starting query execution')

            # Use concurrency manager to run the database query in a separate thread
            result = await self._concurrency_manager.run_in_thread(
                self._execute_query_sync,
                filter_panels,
                columns,
                page,
                page_size,
                sort_by,
                sort_desc,
                table_filters
            )

            results, total_count = result

            if progress_reporter:
                await progress_reporter.report_progress(90, 'Query completed, preparing results')

            self._logger.debug(f'Query executed: {len(results)} rows of {total_count} total')

            # Publish results
            await self._event_bus_manager.publish(
                event_type=VCdbEventType.query_results(),
                source='vcdb_explorer',
                payload={
                    'results': results,
                    'total_count': total_count,
                    'callback_id': callback_id
                }
            )

            if progress_reporter:
                await progress_reporter.report_progress(100, 'Results published')

        except Exception as e:
            self._logger.error(f'Error executing query: {str(e)}')
            await self._event_bus_manager.publish(
                event_type=VCdbEventType.query_results(),
                source='vcdb_explorer',
                payload={
                    'results': [],
                    'total_count': 0,
                    'error': str(e),
                    'callback_id': callback_id
                }
            )

    def _execute_query_sync(
            self,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            page: int,
            page_size: int,
            sort_by: Optional[str],
            sort_desc: bool,
            table_filters: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Synchronous execution of database query to be run in a separate thread.

        Args:
            filter_panels: List of filter panels with their selections
            columns: List of columns to include in results
            page: Page number
            page_size: Page size
            sort_by: Column to sort by
            sort_desc: Whether to sort in descending order
            table_filters: Additional table filters

        Returns:
            Tuple of (results list, total count)
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            with self._db_manager.session(self.CONNECTION_NAME) as session:
                self._logger.debug(
                    f'Executing query: panels={len(filter_panels)}, columns={columns}, page={page}, page_size={page_size}')

                # Build base query
                base_query = select(Vehicle.vehicle_id).select_from(Vehicle)

                # Apply filter panels
                if filter_panels:
                    panel_conditions = []
                    for panel in filter_panels:
                        if not panel:
                            continue
                        panel_query = select(Vehicle.vehicle_id).select_from(Vehicle)
                        panel_query = self._apply_filters(panel_query, panel, set(), session)
                        panel_conditions.append(Vehicle.vehicle_id.in_(panel_query.scalar_subquery()))

                    if panel_conditions:
                        base_query = base_query.filter(or_(*panel_conditions))
                        self._logger.debug(f'Applied {len(panel_conditions)} panel conditions')

                # Get total count
                count_query = select(func.count()).select_from(base_query.alias())
                total_count = session.execute(count_query).scalar() or 0
                self._logger.debug(f'Total count: {total_count}')

                # Build columns query
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
                result_rows = session.execute(query).all()

                # Convert rows to dicts
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
            self._logger.error(f'Database error executing query: {str(e)}')
            raise DatabaseHandlerError(f'Database error executing query: {str(e)}') from e
        except Exception as e:
            self._logger.error(f'Error executing query: {str(e)}')
            raise DatabaseHandlerError(f'Error executing query: {str(e)}') from e

    async def get_filter_values(
            self,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            exclude_filters: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get available filter values based on current filter selections.

        Args:
            filter_type: Type of filter to get values for
            current_filters: Current filter selections
            exclude_filters: Filters to exclude from consideration

        Returns:
            List of filter values with id, name, and count

        Raises:
            DatabaseHandlerError: If database error occurs
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        if exclude_filters is None:
            exclude_filters = set()

        # Run this in a thread since it uses synchronous SQLAlchemy operations
        try:
            return await self._concurrency_manager.run_in_thread(
                self._get_filter_values_sync,
                filter_type,
                current_filters,
                exclude_filters
            )
        except Exception as e:
            self._logger.error(f'Error getting filter values for {filter_type}: {str(e)}')
            raise DatabaseHandlerError(f'Error getting filter values for {filter_type}: {str(e)}') from e

    def _get_filter_values_sync(
            self,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            exclude_filters: Set[str]
    ) -> List[Dict[str, Any]]:
        """Synchronous version of get_filter_values to run in a thread.

        Args:
            filter_type: Type of filter to get values for
            current_filters: Current filter selections
            exclude_filters: Filters to exclude from consideration

        Returns:
            List of filter values with id, name, and count

        Raises:
            DatabaseHandlerError: If database error occurs
        """
        try:
            if filter_type not in self._filter_map:
                raise DatabaseHandlerError(f'Unknown filter type: {filter_type}')

            model_class, attr_name = self._filter_map[filter_type]

            with self._db_manager.session(self.CONNECTION_NAME) as session:
                # Build appropriate query based on filter type
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
                    # Generic query for other filter types
                    pk_column = getattr(model_class, model_class.__table__.primary_key.columns.keys()[0])
                    name_column = getattr(model_class, attr_name)
                    query = select(
                        pk_column.label('id'),
                        name_column.label('name'),
                        func.count(pk_column).label('count')
                    ).select_from(Vehicle)

                # Apply existing filters to query
                query = self._apply_filters(query, current_filters, exclude_filters, session)

                self._logger.debug(f'Executing filter values query for {filter_type}')
                result = session.execute(query)

                # Convert result to list of dicts
                values = []
                for row in result:
                    values.append({
                        'id': row.id,
                        'name': str(row.name),
                        'count': row.count
                    })

                return values
        except SQLAlchemyError as e:
            self._logger.error(f'Database error getting filter values for {filter_type}: {str(e)}')
            raise DatabaseHandlerError(f'Database error getting filter values for {filter_type}: {str(e)}') from e
        except Exception as e:
            self._logger.error(f'Error getting filter values for {filter_type}: {str(e)}')
            raise DatabaseHandlerError(f'Error getting filter values for {filter_type}: {str(e)}') from e

    def _apply_filters(
            self,
            query: Any,
            filters: Dict[str, List[int]],
            exclude_filters: Set[str],
            session: Optional[Session] = None,
            target_model: Any = None
    ) -> Any:
        """Apply filters to a query.

        Args:
            query: SQLAlchemy query object
            filters: Dictionary of filters to apply
            exclude_filters: Set of filter types to exclude
            session: Database session
            target_model: Target model if filtering for a specific model

        Returns:
            Updated query with filters applied
        """
        if not filters:
            self._logger.debug('No filters to apply')
            return query

        self._logger.debug(f'Applying filters: {filters}, excluding: {exclude_filters}')

        # Check if base vehicle is already joined
        has_base_vehicle_join = False
        for clause in getattr(query, '_from_obj', []):
            if isinstance(clause, sqlalchemy.sql.elements.Join) and hasattr(clause, 'right') and (
                    clause.right == BaseVehicle.__table__):
                has_base_vehicle_join = True
                break

        # Apply each filter
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
                # Apply specific filter based on type
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

                    # Ensure values are integers
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
                    # Generic filter application
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

    def _build_columns_query(self, vehicle_ids: Any, columns: List[str]) -> Any:
        """Build a query with the specified columns.

        Args:
            vehicle_ids: Vehicle IDs subquery or scalar subquery
            columns: List of columns to include

        Returns:
            SQLAlchemy query object
        """
        query = select(Vehicle.vehicle_id).select_from(Vehicle)
        query = query.filter(Vehicle.vehicle_id.in_(vehicle_ids))

        # Join with base tables and add common columns
        query = query.add_columns(BaseVehicle.year_id.label('year')).join(
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

        # Add requested columns
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

    def _apply_table_filters(self, query: Any, table_filters: Dict[str, Any]) -> Any:
        """Apply additional table filters to a query.

        Args:
            query: SQLAlchemy query object
            table_filters: Dictionary of table filters

        Returns:
            Updated query with filters applied
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

    def _apply_sorting(self, query: Any, sort_by: str, sort_desc: bool) -> Any:
        """Apply sorting to a query.

        Args:
            query: SQLAlchemy query object
            sort_by: Column to sort by
            sort_desc: Whether to sort in descending order

        Returns:
            Updated query with sorting applied
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
        """Get list of available columns for display.

        Returns:
            List of column definitions with id and name
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
        """Get list of available filters.

        Returns:
            List of filter definitions with id, name, and mandatory flag
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

    async def shutdown(self) -> None:
        """Shut down the database handler and clean up resources."""
        if not self._initialized:
            return

        if hasattr(self, '_shutting_down') and self._shutting_down:
            self._logger.debug('Shutdown already in progress, skipping duplicate call')
            return

        self._shutting_down = True

        try:
            # Unsubscribe from events
            await self._event_bus_manager.unsubscribe(subscriber_id='vcdb_explorer_handler')

            # Unregister database connection if needed
            if self._db_manager and await self._db_manager.has_connection(self.CONNECTION_NAME):
                try:
                    await self._db_manager.unregister_connection(self.CONNECTION_NAME)
                    self._logger.info(f'Unregistered database connection: {self.CONNECTION_NAME}')
                except Exception as e:
                    self._logger.warning(f'Error unregistering database connection: {str(e)}')

            self._initialized = False
            self._logger.info('VCdb Database Handler shut down successfully')
        finally:
            self._shutting_down = False