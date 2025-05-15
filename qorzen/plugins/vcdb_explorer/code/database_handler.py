from __future__ import annotations

from sqlalchemy.orm.util import AliasedInsp, AliasedClass

"""
VCdb database handler module.

This module provides functionality for querying and interacting with the VCdb database,
including filtering and retrieving vehicle component data.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable
from functools import lru_cache

import sqlalchemy
from sqlalchemy import func, or_, select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Join

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
        Initialize the exception.

        Args:
            message: Error message
            details: Additional details about the error
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class DatabaseHandler:
    """Handler for database operations on the VCdb database."""

    CONNECTION_NAME = 'vcdb_explorer'

    def __init__(
            self,
            database_manager: DatabaseManager,
            event_bus_manager: EventBusManager,
            task_manager: TaskManager,
            concurrency_manager: ConcurrencyManager,
            logger: logging.Logger
    ) -> None:
        """
        Initialize the database handler.

        Args:
            database_manager: Manager for database connections
            event_bus_manager: Manager for event bus operations
            task_manager: Manager for background tasks
            concurrency_manager: Manager for concurrency operations
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
        self._query_cancellation_tokens: Dict[str, asyncio.Event] = {}

        # Mapping of filter types to model classes and attributes
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

        # Cache for frequently accessed data
        self._available_columns_cache: Optional[List[Dict[str, str]]] = None
        self._available_filters_cache: Optional[List[Dict[str, Any]]] = None

    async def initialize(self) -> None:
        """Initialize the database handler by subscribing to events."""
        try:
            # Subscribe to filter changed events
            await self._event_bus_manager.subscribe(
                event_type=VCdbEventType.filter_changed(),
                callback=self._on_filter_changed,
                subscriber_id='vcdb_explorer_handler'
            )

            # Subscribe to query execute events
            await self._event_bus_manager.subscribe(
                event_type=VCdbEventType.query_execute(),
                callback=self._on_query_execute,
                subscriber_id='vcdb_explorer_handler'
            )

            self._logger.info('Database handler initialized and subscribed to events')
        except Exception as e:
            self._logger.error(f'Failed to initialize database handler: {str(e)}')
            raise DatabaseHandlerError(f'Failed to initialize database handler: {str(e)}') from e

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
        """
        Configure the database connection.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            db_type: Database type (e.g., 'postgresql')
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to create
            pool_recycle: Connection recycle time in seconds
            echo: Whether to echo SQL statements
        """
        self._logger.debug(f'Configuring VCdb database connection: {host}:{port}/{database}')

        try:
            # Check if connection already exists
            has_connection = await self._db_manager.has_connection(self.CONNECTION_NAME)
            if has_connection:
                self._logger.info(f'Connection {self.CONNECTION_NAME} already exists, reusing it')
                self._initialized = True
                return

            # Create a new connection
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

            # Test the connection
            async with self._db_manager.async_session(self.CONNECTION_NAME) as session:
                result = await session.execute(select(func.count()).select_from(Vehicle))
                vehicle_count = result.scalar()
                self._logger.info(f'Connected to VCdb database. Vehicle count: {vehicle_count}')

            self._initialized = True

        except Exception as e:
            self._logger.error(f'Failed to initialize VCdb database connection: {str(e)}')
            raise DatabaseHandlerError(f'Failed to initialize VCdb database connection: {str(e)}') from e

    async def _on_filter_changed(self, event: Event) -> None:
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

        # Only refresh filters if auto-populate is enabled and we have some filters applied
        if auto_populate and current_filters:
            try:
                # Submit a task to refresh the filters
                task_id = await self._task_manager.submit_async_task(
                    func=self._refresh_filters,
                    filter_panel_id=filter_panel_id,
                    filter_type=filter_type,
                    current_filters=current_filters,
                    name=f'filter_refresh_{filter_panel_id}_{filter_type}',
                    category=TaskCategory.PLUGIN,
                    plugin_id='vcdb_explorer'
                )
                self._logger.debug(f'Submitted filter refresh task with ID: {task_id}')
            except TaskError as e:
                self._logger.error(f'Failed to submit refresh filters task: {str(e)}')

    async def _on_query_execute(self, event: Event) -> None:
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

        # Log filter panels for debugging
        for i, panel in enumerate(filter_panels):
            if panel:
                self._logger.debug(f'Filter panel {i}: {panel}')
            else:
                self._logger.debug(f'Filter panel {i}: Empty')

        try:
            # Set up cancellation token
            query_token = f'query_{callback_id}'
            self._query_cancellation_tokens[query_token] = asyncio.Event()

            # Submit query task
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
                cancellation_token=query_token,
                name=f'vcdb_query_execute',
                category=TaskCategory.PLUGIN,
                plugin_id='vcdb_explorer'
            )

            self._logger.debug(f'Submitted query execution task with ID: {task_id}')

        except TaskError as e:
            self._logger.error(f'Failed to submit query execution task: {str(e)}')

            # Publish error results
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

    async def cancel_query(self, callback_id: str) -> bool:
        """
        Cancel a running query.

        Args:
            callback_id: The ID of the query to cancel

        Returns:
            True if cancellation was requested, False otherwise
        """
        query_token = f'query_{callback_id}'
        if query_token in self._query_cancellation_tokens:
            self._query_cancellation_tokens[query_token].set()
            self._logger.debug(f'Cancellation requested for query {callback_id}')
            return True
        return False

    async def _refresh_filters(
            self,
            filter_panel_id: str,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            progress_reporter: Any = None,
            cancellation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refresh filter values based on current selections.

        Args:
            filter_panel_id: ID of the filter panel
            filter_type: Type of filter that changed
            current_filters: Current filter values
            progress_reporter: Reporter for task progress
            cancellation_token: Token for cancellation

        Returns:
            Dictionary with refresh results
        """
        self._logger.debug(f'Refreshing filters for panel {filter_panel_id} after {filter_type} change')

        # Determine which filters to exclude
        exclude_filters = {filter_type}
        if filter_type == 'year_range':
            exclude_filters.add('year')
        elif filter_type == 'year':
            exclude_filters.add('year_range')

        results = {}

        try:
            if progress_reporter:
                await progress_reporter.report_progress(10, f'Processing filters')

            # Get all filter types to refresh
            filter_types = list(self._filter_map.keys())
            total_filters = len(filter_types)

            # Determine which filters to refresh (skip the one that just changed + year/year_range)
            to_refresh = [
                ft for ft in self._filter_map.keys()
                if ft not in {filter_type, 'year', 'year_range'}
            ]

            # Throttle to your pool size
            pool_size = self._connection_config.pool_size if self._connection_config else 5
            sem = asyncio.BoundedSemaphore(pool_size)

            async def _fetch(ft):
                async with sem:
                    return await self.get_filter_values(ft, current_filters, exclude_filters)

            for ft in to_refresh + (['year'] if 'year' not in to_refresh else []):
                try:
                    results[ft] = await self.get_filter_values(ft, current_filters, exclude_filters)
                except Exception as e:
                    self._logger.error(f'Error refreshing {ft}: {str(e)}')

            # Mirror year to year_range
            if 'year' in results:
                results['year_range'] = results['year']

            if progress_reporter:
                await progress_reporter.report_progress(95, f'Publishing filter refresh event')

            # Publish the results
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
            progress_reporter: Any = None,
            cancellation_token: Optional[str] = None
    ) -> None:
        """
        Execute a query with the specified filters and parameters.

        Args:
            filter_panels: List of filter dictionaries from multiple panels
            columns: List of columns to include in the results
            page: Page number for pagination
            page_size: Number of rows per page
            sort_by: Column to sort by
            sort_desc: Whether to sort in descending order
            table_filters: Additional table filters
            callback_id: ID for callback
            progress_reporter: Reporter for task progress
            cancellation_token: Token for cancellation
        """
        self._logger.debug(f'Executing query: panels={len(filter_panels)}, page={page}, page_size={page_size}')

        # Filter out empty panels
        valid_panels = [panel for panel in filter_panels if panel]
        if not valid_panels:
            self._logger.warning('No filter conditions found in any panel')

        try:
            if progress_reporter:
                await progress_reporter.report_progress(10, 'Starting query execution')

            # Execute the query
            async with self._db_manager.async_session(self.CONNECTION_NAME) as session:
                results, total_count = await self._execute_query_async(
                    session,
                    filter_panels,
                    columns,
                    page,
                    page_size,
                    sort_by,
                    sort_desc,
                    table_filters,
                    progress_reporter,
                    cancellation_token
                )

            # Check if cancelled
            if cancellation_token and cancellation_token in self._query_cancellation_tokens:
                if self._query_cancellation_tokens[cancellation_token].is_set():
                    self._logger.debug(f'Query execution cancelled for {callback_id}')

                    # Publish cancelled results
                    await self._event_bus_manager.publish(
                        event_type=VCdbEventType.query_results(),
                        source='vcdb_explorer',
                        payload={
                            'results': [],
                            'total_count': 0,
                            'cancelled': True,
                            'callback_id': callback_id
                        }
                    )
                    return

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

            # Publish error results
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

        finally:
            # Clean up cancellation token
            if cancellation_token and cancellation_token in self._query_cancellation_tokens:
                del self._query_cancellation_tokens[cancellation_token]

    async def _execute_query_async(
            self,
            session: AsyncSession,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            page: int,
            page_size: int,
            sort_by: Optional[str],
            sort_desc: bool,
            table_filters: Dict[str, Any],
            progress_reporter: Any = None,
            cancellation_token: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Execute a query asynchronously and return the results.

        Args:
            session: Database session
            filter_panels: List of filter dictionaries from multiple panels
            columns: List of columns to include in the results
            page: Page number for pagination
            page_size: Number of rows per page
            sort_by: Column to sort by
            sort_desc: Whether to sort in descending order
            table_filters: Additional table filters
            progress_reporter: Reporter for task progress
            cancellation_token: Token for cancellation

        Returns:
            Tuple of (results, total_count)
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        try:
            self._logger.debug(
                f'Executing async query: panels={len(filter_panels)}, '
                f'columns={columns}, page={page}, page_size={page_size}'
            )

            # Start with a base query for vehicle IDs
            base_query = select(Vehicle.vehicle_id).select_from(Vehicle)

            # Apply filter panels
            if filter_panels:
                panel_conditions = []

                for panel in filter_panels:
                    if not panel:
                        continue

                    # Create a subquery for each panel
                    panel_query = select(Vehicle.vehicle_id).select_from(Vehicle)
                    panel_query = self._apply_filters(panel_query, panel, set())

                    # Add panel condition
                    panel_conditions.append(Vehicle.vehicle_id.in_(panel_query.scalar_subquery()))

                # Combine panel conditions with OR
                if panel_conditions:
                    base_query = base_query.filter(or_(*panel_conditions))
                    self._logger.debug(f'Applied {len(panel_conditions)} panel conditions')

            if progress_reporter:
                await progress_reporter.report_progress(30, 'Counting matching records')

            # Get total count
            count_query = select(func.count()).select_from(base_query.alias())
            count_result = await session.execute(count_query)
            total_count = count_result.scalar() or 0

            self._logger.debug(f'Total count: {total_count}')

            # Build query with columns
            query = self._build_columns_query(base_query.scalar_subquery(), columns)

            # Apply table filters - removed for client-side filtering

            # Apply sorting
            if sort_by:
                query = self._apply_sorting(query, sort_by, sort_desc)
                self._logger.debug(f"Applied sorting: {sort_by} {('DESC' if sort_desc else 'ASC')}")

            # Apply pagination
            if page > 0 and page_size > 0:
                query = query.offset((page - 1) * page_size).limit(page_size)
                self._logger.debug(f'Applied pagination: page={page}, page_size={page_size}')

            # Check for cancellation
            if cancellation_token and cancellation_token in self._query_cancellation_tokens:
                if self._query_cancellation_tokens[cancellation_token].is_set():
                    self._logger.debug(f'Query cancelled before execution')
                    return ([], 0)

            if progress_reporter:
                await progress_reporter.report_progress(60, 'Executing query')

            self._logger.debug('Executing final query')

            # Execute the query
            rows = await session.execute(query)
            result_rows = rows.all()

            if progress_reporter:
                await progress_reporter.report_progress(80, 'Processing results')

            # Convert rows to dictionaries
            results = []
            for row in result_rows:
                d: Dict[str, Any] = {}
                for idx, col in enumerate(query.columns):
                    d[col.name] = row[idx]
                results.append(d)

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
        """
        Get available values for a filter type, filtered by current selections.

        Args:
            filter_type: Type of filter to get values for
            current_filters: Currently selected filter values
            exclude_filters: Filter types to exclude

        Returns:
            List of value dictionaries with 'id', 'name', and 'count' keys
        """
        if not self._initialized:
            raise DatabaseHandlerError('DatabaseHandler not initialized')

        if exclude_filters is None:
            exclude_filters = set()

        if filter_type not in self._filter_map:
            raise DatabaseHandlerError(f'Unknown filter type: {filter_type}')

        # Get the model class and attribute name for this filter type
        model_class, attr_name = self._filter_map[filter_type]

        async with self._db_manager.async_session(self.CONNECTION_NAME) as session:
            # Build a query based on the filter type
            if filter_type == 'year':
                query = (
                    select(
                        Year.year_id.label('id'),
                        Year.year_id.label('name'),
                        func.count(Year.year_id).label('count')
                    )
                    .select_from(Year)
                    .join(BaseVehicle, BaseVehicle.year_id == Year.year_id)
                    .join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                )
                query = query.group_by(Year.year_id).order_by(Year.year_id)

            elif filter_type == 'make':
                query = (
                    select(
                        Make.make_id.label('id'),
                        Make.make_name.label('name'),
                        func.count(Make.make_id).label('count')
                    )
                    .select_from(Make)
                    .join(BaseVehicle, BaseVehicle.make_id == Make.make_id)
                    .join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                )
                query = query.group_by(Make.make_id, Make.make_name).order_by(Make.make_name)

            elif filter_type == 'model':
                query = (
                    select(
                        Model.model_id.label('id'),
                        Model.model_name.label('name'),
                        func.count(Model.model_id).label('count')
                    )
                    .select_from(Model)
                    .join(BaseVehicle, BaseVehicle.model_id == Model.model_id)
                    .join(Vehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                )
                query = query.group_by(Model.model_id, Model.model_name).order_by(Model.model_name)

            elif filter_type == 'submodel':
                query = (
                    select(
                        SubModel.sub_model_id.label('id'),
                        SubModel.sub_model_name.label('name'),
                        func.count(SubModel.sub_model_id).label('count')
                    )
                    .select_from(SubModel)
                    .join(Vehicle, Vehicle.sub_model_id == SubModel.sub_model_id)
                )
                query = query.group_by(SubModel.sub_model_id, SubModel.sub_model_name).order_by(SubModel.sub_model_name)

            elif filter_type == 'region':
                query = (
                    select(
                        Region.region_id.label('id'),
                        Region.region_name.label('name'),
                        func.count(Region.region_id).label('count')
                    )
                    .select_from(Region)
                    .join(Vehicle, Vehicle.region_id == Region.region_id)
                )
                query = query.group_by(Region.region_id, Region.region_name).order_by(Region.region_name)

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
                )
                query = query.group_by(dt.drive_type_id, dt.drive_type_name).order_by(dt.drive_type_name)

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
                )
                query = query.group_by(wb.wheel_base_id, wb.wheel_base).order_by(wb.wheel_base)

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
                )
                query = query.group_by(bt.bed_type_id, bt.bed_type_name).order_by(bt.bed_type_name)

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
                )
                query = query.group_by(bl.bed_length_id, bl.bed_length).order_by(bl.bed_length)

            elif filter_type == 'bodytype':
                vtbc = aliased(VehicleToBodyConfig)
                bsc = aliased(BodyStyleConfig)
                bt = aliased(BodyType)
                query = (
                    select(
                        bsc.body_type_id.label('id'),
                        bt.body_type_name.label('name'),
                        func.count(bt.body_type_id).label('count')
                    )
                    .select_from(Vehicle)
                    .join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                    .join(bsc, vtbc.body_style_config_id == bsc.body_style_config_id)
                    .join(bt, bt.body_type_id == bsc.body_type_id)
                )
                query = query.group_by(bsc.body_type_id, bt.body_type_id).order_by(bt.body_type_name)

            elif filter_type == 'bodynumdoors':
                vtbc = aliased(VehicleToBodyConfig)
                bsc = aliased(BodyStyleConfig)
                bnd = aliased(BodyNumDoors)
                query = (
                    select(
                        bsc.body_num_doors_id.label('id'),
                        bnd.body_num_doors.label('name'),
                        func.count(bnd.body_num_doors_id).label('count')
                    )
                    .select_from(Vehicle)
                    .join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                    .join(bsc, vtbc.body_style_config_id == bsc.body_style_config_id)
                    .join(bnd, bnd.body_num_doors_id == bsc.body_type_id)
                )
                query = query.group_by(bsc.body_num_doors_id, bnd.body_num_doors_id).order_by(bnd.body_num_doors)

            elif filter_type == 'engineblock':
                vtec = aliased(VehicleToEngineConfig)
                ec = aliased(EngineConfig2)
                eb = aliased(EngineBlock)
                query = (
                    select(
                        eb.engine_block_id.label('id'),
                        eb.cylinders.label('name'),
                        func.count(eb.engine_block_id).label('count')
                    )
                    .select_from(Vehicle)
                    .join(vtec, Vehicle.vehicle_id == vtec.vehicle_id)
                    .join(ec, vtec.engine_config_id == ec.engine_config_id)
                    .join(eb, ec.engine_block_id == eb.engine_block_id)
                )
                query = query.group_by(eb.engine_block_id, eb.cylinders).order_by(eb.cylinders)

            elif filter_type == 'fueltypename':
                vtec = aliased(VehicleToEngineConfig)
                ec = aliased(EngineConfig2)
                ft = aliased(FuelType)
                query = (
                    select(
                        ft.fuel_type_id.label('id'),
                        ft.fuel_type_name.label('name'),
                        func.count(ft.fuel_type_id).label('count')
                    )
                    .select_from(Vehicle)
                    .join(vtec, Vehicle.vehicle_id == vtec.vehicle_id)
                    .join(ec, vtec.engine_config_id == ec.engine_config_id)
                    .join(ft, ec.fuel_type_id == ft.fuel_type_id)
                )
                query = query.group_by(ft.fuel_type_id, ft.fuel_type_name).order_by(ft.fuel_type_name)

            elif filter_type == 'vehicletypegroup':
                bv = aliased(BaseVehicle)
                m = aliased(Model)
                vt = aliased(VehicleType)
                vtg = aliased(VehicleTypeGroup)

                query = (
                    select(
                        vtg.vehicle_type_group_id.label('id'),
                        vtg.vehicle_type_group_name.label('name'),
                        func.count(vtg.vehicle_type_group_id).label('count')
                    )
                    .select_from(Vehicle)
                    .join(bv, Vehicle.base_vehicle_id == bv.base_vehicle_id)
                    .join(m, bv.model_id == m.model_id)
                    .join(vt, m.vehicle_type_id == vt.vehicle_type_id)
                    .join(vtg, vt.vehicle_type_group_id == vtg.vehicle_type_group_id)
                    .group_by(vtg.vehicle_type_group_id, vtg.vehicle_type_group_name)
                    .order_by(vtg.vehicle_type_group_name)
                )

            else:
                # Generic handling for other filter types
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

                # Add joins based on model type
                if model_class == VehicleType:
                    query = (
                        query
                        .join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        .join(Model, BaseVehicle.model_id == Model.model_id)
                        .join(VehicleType, Model.vehicle_type_id == VehicleType.vehicle_type_id)
                    )
                elif model_class == PublicationStage:
                    query = query.join(PublicationStage,
                                       Vehicle.publication_stage_id == PublicationStage.publication_stage_id)
                elif model_class == BrakeType:
                    vtbc = aliased(VehicleToBrakeConfig)
                    bc = aliased(BrakeConfig)
                    query = (
                        query
                        .join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                        .join(bc, vtbc.brake_config_id == bc.brake_config_id)
                        .join(BrakeType, or_(bc.front_brake_type_id == BrakeType.brake_type_id,
                                             bc.rear_brake_type_id == BrakeType.brake_type_id))
                    )
                elif model_class == BrakeSystem:
                    vtbc = aliased(VehicleToBrakeConfig)
                    bc = aliased(BrakeConfig)
                    query = (
                        query
                        .join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                        .join(bc, vtbc.brake_config_id == bc.brake_config_id)
                        .join(BrakeSystem, bc.brake_system_id == BrakeSystem.brake_system_id)
                    )
                elif model_class == BrakeABS:
                    vtbc = aliased(VehicleToBrakeConfig)
                    bc = aliased(BrakeConfig)
                    query = (
                        query
                        .join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                        .join(bc, vtbc.brake_config_id == bc.brake_config_id)
                        .join(BrakeABS, bc.brake_abs_id == BrakeABS.brake_abs_id)
                    )
                elif model_class == Class:
                    vtc = aliased(VehicleToClass)
                    query = (
                        query
                        .join(vtc, Vehicle.vehicle_id == vtc.vehicle_id)
                        .join(Class, vtc.class_id == Class.class_id)
                    )

                query = query.group_by(pk_column, name_column).order_by(name_column)

            # Apply filters based on current selections
            query = self._apply_filters(
                query,
                current_filters,
                exclude_filters,
                target_model=model_class
            )

            self._logger.debug(f'Executing filter values query for {filter_type}')

            # Execute the query
            result = await session.execute(query)
            rows = result.all()

            # Convert rows to dictionaries
            return [{'id': row.id, 'name': str(row.name), 'count': row.count} for row in rows]

    def _apply_filters(
            self,
            query: Any,
            filters: Dict[str, List[int]],
            exclude_filters: Set[str],
            target_model: Any = None
    ) -> Any:
        """
        Apply filters to a query.

        Args:
            query: The query to apply filters to
            filters: Dictionary of filter values by filter type
            exclude_filters: Set of filter types to exclude
            target_model: Target model for filtering

        Returns:
            The modified query with filters applied
        """
        if not filters:
            self._logger.debug('No filters to apply')
            return query

        self._logger.debug(f'Applying filters: {filters}, excluding: {exclude_filters}')

        def _contains_base_vehicle(clause) -> bool:
            if isinstance(clause, Join):
                return _contains_base_vehicle(clause.left) or _contains_base_vehicle(clause.right)
            # direct table
            if getattr(clause, 'name', None) == BaseVehicle.__tablename__:
                return True
            # if it's an aliased mapper
            if isinstance(clause, AliasedInsp) and clause.original is BaseVehicle:
                return True
            return False

        has_base_vehicle_join = any(
            _contains_base_vehicle(f) for f in query.get_final_froms()
        )

        # Process each filter
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
                # Apply filter based on type
                if filter_type == 'year':
                    if not has_base_vehicle_join:
                        query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        has_base_vehicle_join = True
                        self._logger.debug('Added join to BaseVehicle for year filter')

                    if len(values) == 2 and values[0] <= values[1]:
                        # Year range filter
                        query = query.filter(BaseVehicle.year_id.between(values[0], values[1]))
                        self._logger.debug(f'Applied year range filter: {values[0]}-{values[1]}')
                    else:
                        # Specific years filter
                        query = query.filter(BaseVehicle.year_id.in_(values))
                        self._logger.debug(f'Applied specific years filter: {values}')

                elif filter_type == 'year_range':
                    # Handle year_range specially
                    if not has_base_vehicle_join:
                        query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        has_base_vehicle_join = True
                        self._logger.debug('Added join to BaseVehicle for year_range filter')

                    if len(values) == 2 and values[0] <= values[1]:
                        query = query.filter(BaseVehicle.year_id.between(values[0], values[1]))
                        self._logger.debug(f'Applied year_range filter: {values[0]}-{values[1]}')

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

                    # Check if joins already exist
                    has_join = False
                    for clause in getattr(query, '_from_obj', []):
                        if isinstance(clause, Join) and hasattr(clause, 'right') and (clause.right == vtdt.__table__):
                            has_join = True
                            break

                    if not has_join:
                        query = query.join(vtdt, Vehicle.vehicle_id == vtdt.vehicle_id)
                        query = query.join(dt, vtdt.drive_type_id == dt.drive_type_id)

                    query = query.filter(dt.drive_type_id.in_(values))
                    self._logger.debug(f'Applied drive type filter: {values}')

                elif filter_type == 'wheelbase':
                    vtwb = aliased(VehicleToWheelBase)
                    wb = aliased(WheelBase)

                    # Check if joins already exist
                    has_join = False
                    for clause in getattr(query, '_from_obj', []):
                        if isinstance(clause, Join) and hasattr(clause, 'right') and (clause.right == vtwb.__table__):
                            has_join = True
                            break

                    if not has_join:
                        query = query.join(vtwb, Vehicle.vehicle_id == vtwb.vehicle_id)
                        query = query.join(wb, vtwb.wheel_base_id == wb.wheel_base_id)

                    query = query.filter(wb.wheel_base_id.in_(values))
                    self._logger.debug(f'Applied wheel base filter: {values}')

                elif filter_type == 'bedtype':
                    vtbc = aliased(VehicleToBedConfig)
                    bc = aliased(BedConfig)
                    bt = aliased(BedType)

                    # Check if joins already exist
                    has_join = False
                    for clause in getattr(query, '_from_obj', []):
                        if isinstance(clause, Join) and hasattr(clause, 'right') and (clause.right == vtbc.__table__):
                            has_join = True
                            break

                    if not has_join:
                        query = query.join(vtbc, Vehicle.vehicle_id == vtbc.vehicle_id)
                        query = query.join(bc, vtbc.bed_config_id == bc.bed_config_id)
                        query = query.join(bt, bc.bed_type_id == bt.bed_type_id)

                    query = query.filter(bt.bed_type_id.in_(values))
                    self._logger.debug(f'Applied bed type filter: {values}')

                elif filter_type == 'vehicletype':
                    if not has_base_vehicle_join:
                        query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                        has_base_vehicle_join = True

                    # Check if model and vehicle type joins already exist
                    has_model_join = False
                    has_vehicle_type_join = False
                    for clause in getattr(query, '_from_obj', []):
                        if isinstance(clause, Join):
                            if hasattr(clause, 'right') and clause.right == Model.__table__:
                                has_model_join = True
                            elif hasattr(clause, 'right') and clause.right == VehicleType.__table__:
                                has_vehicle_type_join = True

                    if not has_model_join:
                        query = query.join(Model, BaseVehicle.model_id == Model.model_id)

                    if not has_vehicle_type_join:
                        query = query.join(VehicleType, Model.vehicle_type_id == VehicleType.vehicle_type_id)

                    query = query.filter(VehicleType.vehicle_type_id.in_(values))
                    self._logger.debug(f'Applied vehicle type filter: {values}')

                elif filter_type == 'engineblock':
                    vtec = aliased(VehicleToEngineConfig)
                    ec = aliased(EngineConfig2)
                    eb = aliased(EngineBlock)

                    # Check if joins already exist
                    has_vtec_join = False
                    has_ec_join = False
                    has_eb_join = False
                    for clause in getattr(query, '_from_obj', []):
                        if isinstance(clause, Join) and hasattr(clause, 'right'):
                            if clause.right == vtec.__table__:
                                has_vtec_join = True
                            elif clause.right == ec.__table__:
                                has_ec_join = True
                            elif clause.right == eb.__table__:
                                has_eb_join = True

                    if not has_vtec_join:
                        query = query.join(vtec, Vehicle.vehicle_id == vtec.vehicle_id)

                    if not has_ec_join:
                        query = query.join(ec, vtec.engine_config_id == ec.engine_config_id)

                    if not has_eb_join:
                        query = query.join(eb, ec.engine_block_id == eb.engine_block_id)

                    # Convert string values to integers if needed
                    engine_block_ids = [int(v) if isinstance(v, str) and v.isdigit() else v for v in values]
                    query = query.filter(eb.engine_block_id.in_(engine_block_ids))
                    self._logger.debug(f'Applied engine block filter: {values}')

                elif filter_type == 'fueltypename':
                    vtec = aliased(VehicleToEngineConfig)
                    ec = aliased(EngineConfig2)
                    ft = aliased(FuelType)

                    # Check if joins already exist
                    has_vtec_join = False
                    has_ec_join = False
                    has_ft_join = False
                    for clause in getattr(query, '_from_obj', []):
                        if isinstance(clause, Join) and hasattr(clause, 'right'):
                            if clause.right == vtec.__table__:
                                has_vtec_join = True
                            elif clause.right == ec.__table__:
                                has_ec_join = True
                            elif clause.right == ft.__table__:
                                has_ft_join = True

                    if not has_vtec_join:
                        query = query.join(vtec, Vehicle.vehicle_id == vtec.vehicle_id)

                    if not has_ec_join:
                        query = query.join(ec, vtec.engine_config_id == ec.engine_config_id)

                    if not has_ft_join:
                        query = query.join(ft, ec.fuel_type_id == ft.fuel_type_id)

                    query = query.filter(ft.fuel_type_id.in_(values))
                    self._logger.debug(f'Applied fuel type filter: {values}')

                elif filter_type in self._filter_map:
                    model_class, attr_name = self._filter_map[filter_type]
                    self._logger.debug(f'Using filter map for {filter_type}: {model_class.__name__}.{attr_name}')

                    # Apply filters for different model types
                    if model_class == Year:
                        if not has_base_vehicle_join:
                            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                            has_base_vehicle_join = True

                        # Check if year join already exists
                        has_year_join = False
                        for clause in getattr(query, '_from_obj', []):
                            if (isinstance(clause, Join) and
                                    hasattr(clause, 'right') and
                                    (clause.right == Year.__table__)):
                                has_year_join = True
                                break

                        if not has_year_join:
                            query = query.join(Year, BaseVehicle.year_id == Year.year_id)

                        query = query.filter(getattr(Year, attr_name).in_(values))
                        self._logger.debug(f'Applied {filter_type} filter with year join: {values}')

                    elif model_class == Make:
                        if not has_base_vehicle_join:
                            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                            has_base_vehicle_join = True

                        # Check if make join already exists
                        has_make_join = False
                        for clause in getattr(query, '_from_obj', []):
                            if (isinstance(clause, Join) and
                                    hasattr(clause, 'right') and
                                    (clause.right == Make.__table__)):
                                has_make_join = True
                                break

                        if not has_make_join:
                            query = query.join(Make, BaseVehicle.make_id == Make.make_id)

                        query = query.filter(getattr(Make, attr_name).in_(values))
                        self._logger.debug(f'Applied {filter_type} filter with make join: {values}')

                    elif model_class == Model:
                        if not has_base_vehicle_join:
                            query = query.join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id)
                            has_base_vehicle_join = True

                        # Check if model join already exists
                        has_model_join = False
                        for clause in getattr(query, '_from_obj', []):
                            if (isinstance(clause, Join) and
                                    hasattr(clause, 'right') and
                                    (clause.right == Model.__table__)):
                                has_model_join = True
                                break

                        if not has_model_join:
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

    def _build_columns_query(self, vehicle_ids: Any, columns: List[str]) -> Any:
        """
        Build a query with the specified columns.

        Args:
            vehicle_ids: Subquery providing vehicle IDs
            columns: List of columns to include

        Returns:
            The query with columns added
        """
        # Base query with vehicle ID
        query = select(Vehicle.vehicle_id).select_from(Vehicle)
        query = query.filter(Vehicle.vehicle_id.in_(vehicle_ids))

        # Add common joins and columns
        query = (
            query.add_columns(BaseVehicle.year_id.label('year'))
            .join(BaseVehicle, Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id, isouter=True)
        )

        query = (
            query
            .add_columns(Make.make_id.label('make_id'), Make.make_name.label('make'))
            .join(Make, BaseVehicle.make_id == Make.make_id, isouter=True)
        )

        query = (
            query
            .add_columns(Model.model_id.label('model_id'), Model.model_name.label('model'))
            .join(Model, BaseVehicle.model_id == Model.model_id, isouter=True)
        )

        query = (
            query
            .add_columns(SubModel.sub_model_id.label('submodel_id'), SubModel.sub_model_name.label('submodel'))
            .join(SubModel, Vehicle.sub_model_id == SubModel.sub_model_id, isouter=True)
        )

        # Add additional columns based on request
        for column in columns:
            if column == 'region':
                query = (
                    query
                    .add_columns(Region.region_id.label('region_id'), Region.region_name.label('region'))
                    .outerjoin(Region, Vehicle.region_id == Region.region_id)
                )

            elif column == 'vehicle_type':
                query = (
                    query
                    .add_columns(
                        VehicleType.vehicle_type_id.label('vehicle_type_id'),
                        VehicleType.vehicle_type_name.label('vehicle_type')
                    )
                    .outerjoin(VehicleType, Model.vehicle_type_id == VehicleType.vehicle_type_id)
                )

            elif column == 'drive_type':
                vtdt = aliased(VehicleToDriveType)
                dt = aliased(DriveType)

                query = (
                    query
                    .add_columns(
                        dt.drive_type_id.label('drive_type_id'),
                        dt.drive_type_name.label('drive_type')
                    )
                    .outerjoin(vtdt, Vehicle.vehicle_id == vtdt.vehicle_id)
                    .outerjoin(dt, vtdt.drive_type_id == dt.drive_type_id)
                )

        return query

    def _apply_table_filters(self, query: Any, table_filters: Dict[str, Any]) -> Any:
        """
        Apply table filters to a query.

        Args:
            query: The query to apply filters to
            table_filters: Dictionary of table filters

        Returns:
            The modified query with table filters applied
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
        """
        Apply sorting to a query.

        Args:
            query: The query to apply sorting to
            sort_by: Column to sort by
            sort_desc: Whether to sort in descending order

        Returns:
            The modified query with sorting applied
        """
        # Map of column names to SQLAlchemy column objects
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
        """
        Get the list of available columns for query results.

        Returns:
            List of column dictionaries with 'id' and 'name' keys
        """
        # Use cached value if available
        if self._available_columns_cache is not None:
            return self._available_columns_cache

        # Define available columns
        columns = [
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

        # Cache the result
        self._available_columns_cache = columns
        return columns

    def get_available_filters(self) -> List[Dict[str, Any]]:
        """
        Get the list of available filters.

        Returns:
            List of filter dictionaries with 'id', 'name', and 'mandatory' keys
        """
        # Use cached value if available
        if self._available_filters_cache is not None:
            return self._available_filters_cache

        # Define available filters
        filters = [
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

        # Cache the result
        self._available_filters_cache = filters
        return filters

    async def shutdown(self) -> None:
        """Shut down the database handler."""
        if not self._initialized:
            return

        if hasattr(self, '_shutting_down') and self._shutting_down:
            self._logger.debug('Shutdown already in progress, skipping duplicate call')
            return

        self._shutting_down = True

        try:
            # Unsubscribe from events
            await self._event_bus_manager.unsubscribe(subscriber_id='vcdb_explorer_handler')

            # Unregister database connection
            if self._db_manager and await self._db_manager.has_connection(self.CONNECTION_NAME):
                try:
                    await self._db_manager.unregister_connection(self.CONNECTION_NAME)
                    self._logger.info(f'Unregistered database connection: {self.CONNECTION_NAME}')
                except Exception as e:
                    self._logger.warning(f'Error unregistering database connection: {str(e)}')

            # Clean up resources
            self._query_cancellation_tokens.clear()
            self._initialized = False

            self._logger.info('VCdb Database Handler shut down successfully')
        finally:
            self._shutting_down = False
