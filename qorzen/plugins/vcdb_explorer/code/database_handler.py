from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Callable, Generator
from contextlib import contextmanager
import threading
import time

from sqlalchemy import select, func, and_, or_, between, text
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError

from .models import (
    Vehicle, Year, Make, Model, SubModel, DriveType, BrakeConfig, BrakeType, BrakeSystem, BrakeABS,
    BedConfig, BedType, BedLength, BodyStyleConfig, BodyType, BodyNumDoors,
    MfrBodyCode, EngineConfig2, EngineBlock, EngineBoreStroke, EngineBase2, Aspiration,
    FuelType, CylinderHeadType, EngineDesignation, EngineVIN, EngineVersion, Valves,
    FuelDeliveryConfig, FuelDeliveryType, FuelDeliverySubType, FuelSystemControlType, FuelSystemDesign,
    PowerOutput, Mfr, IgnitionSystemType,
    SpringTypeConfig, SpringType, SteeringConfig, SteeringType, SteeringSystem,
    Transmission, TransmissionBase, TransmissionType, TransmissionNumSpeeds, TransmissionControlType,
    TransmissionMfrCode, ElecControlled,
    WheelBase, Class, Region, BaseVehicle, VehicleTypeGroup, VehicleType, PublicationStage,
    VehicleToBodyConfig, VehicleToDriveType, VehicleToBrakeConfig, VehicleToSteeringConfig,
    VehicleToTransmission, VehicleToWheelBase, VehicleToEngineConfig, VehicleToBedConfig,
    VehicleToBodyStyleConfig, VehicleToMfrBodyCode, VehicleToSpringTypeConfig, VehicleToClass
)


class DatabaseError(Exception):
    """Exception raised for database operation errors."""
    pass


class DatabaseHandler:
    """
    Database handler that integrates with Qorzen's DatabaseManager.
    """

    def __init__(
            self,
            database_manager: Any,
            event_bus: Any,
            thread_manager: Any,
            logger: logging.Logger
    ) -> None:
        """
        Initialize the database handler.

        Args:
            database_manager: Qorzen's DatabaseManager instance
            event_bus: Qorzen's EventBus instance
            thread_manager: Qorzen's ThreadManager instance
            logger: Logger instance
        """
        self._db_manager = database_manager
        self._event_bus = event_bus
        self._thread_manager = thread_manager
        self._logger = logger
        self._initialized = False
        self._query_lock = threading.Lock()

        # Map of filter type to (model class, attribute name)
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

        # Register events
        self._event_bus.register('vcdb_explorer:filter_changed', self._on_filter_changed)
        self._event_bus.register('vcdb_explorer:query_execute', self._on_query_execute)

        self._initialize()

    def _initialize(self) -> None:
        """Initialize the database handler."""
        try:
            # If using the database manager
            if self._db_manager:
                # Test the database connection
                with self._db_manager.session() as session:
                    result = session.execute(select(func.count()).select_from(Vehicle)).scalar()
                    self._logger.info(f'Connected to database via DatabaseManager. Vehicle count: {result}')

                self._initialized = True
            else:
                # Direct connection using SQLAlchemy
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker

                if not hasattr(self, '_connection_params'):
                    raise DatabaseError("Database connection parameters not configured")

                conn_str = f"postgresql://{self._connection_params['user']}:{self._connection_params['password']}@{self._connection_params['host']}:{self._connection_params['port']}/{self._connection_params['database']}"

                self._logger.debug(
                    f"Connecting to database at {self._connection_params['host']}:{self._connection_params['port']}")

                self._engine = create_engine(
                    conn_str,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10,
                    pool_recycle=3600
                )

                self._session_factory = sessionmaker(bind=self._engine)

                # Test the connection
                with self.session() as session:
                    result = session.execute(select(func.count()).select_from(Vehicle)).scalar()
                    self._logger.info(f'Connected to database directly. Vehicle count: {result}')

                self._initialized = True

            self._logger.info('DatabaseHandler initialized successfully')

        except Exception as e:
            self._logger.error(f'Failed to initialize DatabaseHandler: {str(e)}')
            raise DatabaseError(f'Failed to initialize DatabaseHandler: {str(e)}') from e

    def configure(self, host: str, port: int, database: str, user: str, password: str) -> None:
        """
        Configure the database connection parameters.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database username
            password: Database password
        """
        self._connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }

        self._logger.debug(f"Database connection parameters configured: {host}:{port}/{database}")

        # Initialize if not already initialized
        if not self._initialized:
            self._initialize()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Create a session context manager."""
        if not self._initialized:
            raise DatabaseError('DatabaseHandler not initialized')

        if self._db_manager:
            # Use the database manager's session
            with self._db_manager.session() as session:
                yield session
        else:
            # Use our own session
            if not hasattr(self, '_session_factory'):
                raise DatabaseError('Session factory not initialized')

            session = self._session_factory()
            try:
                yield session
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                self._logger.error(f'Database error: {str(e)}')
                raise DatabaseError(f'Database error: {str(e)}') from e
            finally:
                session.close()

    def shutdown(self) -> None:
        """Shut down the database handler."""
        if self._initialized:
            # Unregister events
            self._event_bus.unregister('vcdb_explorer:filter_changed', self._on_filter_changed)
            self._event_bus.unregister('vcdb_explorer:query_execute', self._on_query_execute)

            self._initialized = False
            self._logger.info('DatabaseHandler shut down successfully')

    def _on_filter_changed(self, filter_panel_id: str, filter_type: str, values: List[int],
                           current_filters: Dict[str, List[int]], auto_populate: bool) -> None:
        """
        Handle filter changed events.

        Args:
            filter_panel_id: ID of the filter panel
            filter_type: Type of filter that changed
            values: New filter values
            current_filters: All current filter values
            auto_populate: Whether auto-populate is enabled
        """
        self._logger.debug(
            f"Filter changed event: panel={filter_panel_id}, type={filter_type}, values={values}, auto_populate={auto_populate}")

        if auto_populate:
            # Run the filter refresh query in a background thread
            self._thread_manager.run_in_thread(
                f"filter_refresh_{filter_panel_id}_{filter_type}",
                self._refresh_filters,
                filter_panel_id,
                filter_type,
                current_filters
            )

    def _on_query_execute(self, filter_panels: List[Dict[str, List[int]]], columns: List[str], page: int,
                          page_size: int, sort_by: Optional[str], sort_desc: bool, table_filters: Dict[str, Any],
                          callback: Callable) -> None:
        """
        Handle query execute events.

        Args:
            filter_panels: List of filter panels to apply
            columns: Columns to include in result
            page: Page number
            page_size: Number of items per page
            sort_by: Column to sort by
            sort_desc: Sort in descending order
            table_filters: Additional table filters
            callback: Callback function to call with results
        """
        self._logger.debug(f"Query execute event: panels={len(filter_panels)}, columns={columns}, page={page}")

        # Run the query in a background thread
        self._thread_manager.run_in_thread(
            f"query_execute_{time.time()}",
            self._execute_query_thread,
            filter_panels,
            columns,
            page,
            page_size,
            sort_by,
            sort_desc,
            table_filters,
            callback
        )

    def _refresh_filters(self, filter_panel_id: str, changed_filter_type: str,
                         current_filters: Dict[str, List[int]]) -> None:
        """
        Refresh filter values for a filter panel.

        Args:
            filter_panel_id: ID of the filter panel
            changed_filter_type: Type of filter that changed
            current_filters: All current filter values
        """
        self._logger.debug(f"Refreshing filters for panel {filter_panel_id} after {changed_filter_type} change")

        exclude_filters = {changed_filter_type}

        # Handle year/year_range exclusive relationship
        if changed_filter_type == 'year_range':
            exclude_filters.add('year')
        elif changed_filter_type == 'year':
            exclude_filters.add('year_range')

        results = {}

        with self._query_lock:
            try:
                # Refresh each filter type
                for filter_type in self._filter_map.keys():
                    if filter_type != changed_filter_type and filter_type != 'year_range' and filter_type != 'year':
                        try:
                            values = self.get_filter_values(filter_type, current_filters, exclude_filters)
                            results[filter_type] = values
                            self._logger.debug(f"Refreshed {filter_type}: {len(values)} values")
                        except Exception as e:
                            self._logger.error(f"Error refreshing {filter_type}: {str(e)}")

                # Special handling for year/year_range
                if changed_filter_type != 'year' and 'year' in self._filter_map:
                    try:
                        values = self.get_filter_values('year', current_filters, exclude_filters)
                        results['year'] = values
                    except Exception as e:
                        self._logger.error(f"Error refreshing year: {str(e)}")

            except Exception as e:
                self._logger.error(f"Error during filter refresh: {str(e)}")

        # Emit event with results
        self._event_bus.emit('vcdb_explorer:filters_refreshed', filter_panel_id, results)

    def _execute_query_thread(
            self,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            page: int,
            page_size: int,
            sort_by: Optional[str],
            sort_desc: bool,
            table_filters: Dict[str, Any],
            callback: Callable
    ) -> None:
        """
        Execute a query in a background thread.

        Args:
            filter_panels: List of filter panels to apply
            columns: Columns to include in result
            page: Page number
            page_size: Number of items per page
            sort_by: Column to sort by
            sort_desc: Sort in descending order
            table_filters: Additional table filters
            callback: Callback function to call with results
        """
        self._logger.debug(
            f"Executing query in thread: panels={len(filter_panels)}, page={page}, page_size={page_size}")

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

                self._logger.debug(f"Query executed in {duration:.3f}s: {len(results)} results of {total_count} total")

                # Call the callback with results
                callback(results, total_count)

            except Exception as e:
                self._logger.error(f"Error executing query: {str(e)}")
                callback([], 0)  # Return empty results on error

    def get_filter_values(
            self,
            filter_type: str,
            current_filters: Dict[str, List[int]],
            exclude_filters: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available filter values based on current filter selections.

        Args:
            filter_type: Type of filter
            current_filters: Currently selected filters
            exclude_filters: Filters to exclude from the query

        Returns:
            List of filter values with counts
        """
        if not self._initialized:
            raise DatabaseError('DatabaseHandler not initialized')

        if exclude_filters is None:
            exclude_filters = set()

        try:
            if filter_type not in self._filter_map:
                raise DatabaseError(f'Unknown filter type: {filter_type}')

            model_class, attr_name = self._filter_map[filter_type]

            with self._db_manager.session() as session:
                # Start with a base query on the Vehicle table
                if filter_type == 'year':
                    # Special case for year
                    query = select(
                        Year.year_id.label('id'),
                        Year.year_id.label('name'),
                        func.count(Year.year_id).label('count')
                    ).select_from(Vehicle)

                    # Join to BaseVehicle and Year
                    query = query.join(
                        BaseVehicle,
                        Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Year,
                        BaseVehicle.year_id == Year.year_id
                    )

                    # Group and order
                    query = query.group_by(Year.year_id).order_by(Year.year_id)

                elif filter_type == 'make':
                    query = select(
                        Make.make_id.label('id'),
                        Make.make_name.label('name'),
                        func.count(Make.make_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        BaseVehicle,
                        Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Make,
                        BaseVehicle.make_id == Make.make_id
                    )

                    query = query.group_by(Make.make_id, Make.make_name).order_by(Make.make_name)

                elif filter_type == 'model':
                    query = select(
                        Model.model_id.label('id'),
                        Model.model_name.label('name'),
                        func.count(Model.model_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        BaseVehicle,
                        Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id
                    ).join(
                        Model,
                        BaseVehicle.model_id == Model.model_id
                    )

                    query = query.group_by(Model.model_id, Model.model_name).order_by(Model.model_name)

                elif filter_type == 'submodel':
                    query = select(
                        SubModel.sub_model_id.label('id'),
                        SubModel.sub_model_name.label('name'),
                        func.count(SubModel.sub_model_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        SubModel,
                        Vehicle.sub_model_id == SubModel.sub_model_id
                    )

                    query = query.group_by(
                        SubModel.sub_model_id,
                        SubModel.sub_model_name
                    ).order_by(SubModel.sub_model_name)

                elif filter_type == 'region':
                    query = select(
                        Region.region_id.label('id'),
                        Region.region_name.label('name'),
                        func.count(Region.region_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        Region,
                        Vehicle.region_id == Region.region_id
                    )

                    query = query.group_by(Region.region_id, Region.region_name).order_by(Region.region_name)

                elif filter_type == 'drivetype':
                    # Use explicit aliasing for relation tables
                    vtdt = aliased(VehicleToDriveType)
                    dt = aliased(DriveType)

                    query = select(
                        dt.drive_type_id.label('id'),
                        dt.drive_type_name.label('name'),
                        func.count(dt.drive_type_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        vtdt,
                        Vehicle.vehicle_id == vtdt.vehicle_id
                    ).join(
                        dt,
                        vtdt.drive_type_id == dt.drive_type_id
                    )

                    query = query.group_by(dt.drive_type_id, dt.drive_type_name).order_by(dt.drive_type_name)

                elif filter_type == 'wheelbase':
                    vtwb = aliased(VehicleToWheelBase)
                    wb = aliased(WheelBase)

                    query = select(
                        wb.wheel_base_id.label('id'),
                        wb.wheel_base.label('name'),
                        func.count(wb.wheel_base_id).label('count')
                    ).select_from(Vehicle)

                    query = query.join(
                        vtwb,
                        Vehicle.vehicle_id == vtwb.vehicle_id
                    ).join(
                        wb,
                        vtwb.wheel_base_id == wb.wheel_base_id
                    )

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

                    query = query.join(
                        vtbc,
                        Vehicle.vehicle_id == vtbc.vehicle_id
                    ).join(
                        bc,
                        vtbc.bed_config_id == bc.bed_config_id
                    ).join(
                        bt,
                        bc.bed_type_id == bt.bed_type_id
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

                    query = query.join(
                        vtbc,
                        Vehicle.vehicle_id == vtbc.vehicle_id
                    ).join(
                        bc,
                        vtbc.bed_config_id == bc.bed_config_id
                    ).join(
                        bl,
                        bc.bed_length_id == bl.bed_length_id
                    )

                    query = query.group_by(bl.bed_length_id, bl.bed_length).order_by(bl.bed_length)

                else:
                    # Generic case - build a basic query for other filter types
                    # Get the primary key and name column
                    pk_column = getattr(model_class, model_class.__table__.primary_key.columns.keys()[0])
                    name_column = getattr(model_class, attr_name)

                    # Create base query
                    query = select(
                        pk_column.label('id'),
                        name_column.label('name'),
                        func.count(pk_column).label('count')
                    ).select_from(Vehicle)

                    # Add appropriate joins based on the filter type
                    # This is simplified - in a real implementation, you'd need to add all necessary joins

                # Apply current filters
                query = self._apply_filters(query, current_filters, exclude_filters)

                # Execute query and convert results
                self._logger.debug(f"Executing filter values query for {filter_type}")
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
            raise DatabaseError(f'Error getting filter values for {filter_type}: {str(e)}') from e

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
            query: Base query
            filters: Filters to apply
            exclude_filters: Filters to exclude
            target_model: Target model class

        Returns:
            Modified query with filters applied
        """
        if not filters:
            return query

        # Log the filters being applied
        self._logger.debug(f"Applying filters: {filters}, excluding: {exclude_filters}")

        # Process each filter
        for filter_type, values in filters.items():
            if not values or filter_type in exclude_filters:
                continue

            # Skip if this is the target model we're querying for
            if target_model and filter_type in self._filter_map and (self._filter_map[filter_type][0] == target_model):
                continue

            # Apply the filter based on type
            if filter_type == 'year':
                if len(values) == 2 and values[0] <= values[1]:
                    # Year range
                    query = query.filter(BaseVehicle.year_id.between(values[0], values[1]))
                    self._logger.debug(f"Applied year range filter: {values[0]}-{values[1]}")
                else:
                    # Specific years
                    query = query.filter(BaseVehicle.year_id.in_(values))
                    self._logger.debug(f"Applied year filter: {values}")

            elif filter_type == 'make':
                query = query.filter(BaseVehicle.make_id.in_(values))
                self._logger.debug(f"Applied make filter: {values}")

            elif filter_type == 'model':
                query = query.filter(BaseVehicle.model_id.in_(values))
                self._logger.debug(f"Applied model filter: {values}")

            elif filter_type == 'submodel':
                query = query.filter(Vehicle.sub_model_id.in_(values))
                self._logger.debug(f"Applied submodel filter: {values}")

            elif filter_type == 'region':
                query = query.filter(Vehicle.region_id.in_(values))
                self._logger.debug(f"Applied region filter: {values}")

            elif filter_type == 'drivetype':
                # Use specific join and filter for drive type
                vtdt = aliased(VehicleToDriveType)
                dt = aliased(DriveType)

                query = query.join(
                    vtdt,
                    Vehicle.vehicle_id == vtdt.vehicle_id
                ).join(
                    dt,
                    vtdt.drive_type_id == dt.drive_type_id
                ).filter(dt.drive_type_id.in_(values))

                self._logger.debug(f"Applied drive type filter: {values}")

            elif filter_type == 'wheelbase':
                vtwb = aliased(VehicleToWheelBase)
                wb = aliased(WheelBase)

                query = query.join(
                    vtwb,
                    Vehicle.vehicle_id == vtwb.vehicle_id
                ).join(
                    wb,
                    vtwb.wheel_base_id == wb.wheel_base_id
                ).filter(wb.wheel_base_id.in_(values))

                self._logger.debug(f"Applied wheel base filter: {values}")

            # Add other specific filter types as needed

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
        Execute a query with the given filter panels and columns.

        Args:
            filter_panels: List of filter panels to apply (ORed together)
            columns: Columns to include in the result
            page: Page number (1-based)
            page_size: Number of results per page
            sort_by: Column to sort by
            sort_desc: Sort descending if True
            table_filters: Additional table filters

        Returns:
            Tuple of (results, total_count)
        """
        if not self._initialized:
            raise DatabaseError('DatabaseHandler not initialized')

        try:
            with self._db_manager.session() as session:
                # Log the query parameters
                self._logger.debug(
                    f"Executing query: panels={len(filter_panels)}, columns={columns}, page={page}, page_size={page_size}")

                # Start with a base query for vehicle IDs that match the filters
                base_query = select(Vehicle.vehicle_id).select_from(Vehicle)

                if filter_panels:
                    panel_conditions = []
                    for panel in filter_panels:
                        if not panel:
                            continue

                        # Create a subquery for each panel
                        panel_query = select(Vehicle.vehicle_id).select_from(Vehicle)
                        panel_query = self._apply_filters(panel_query, panel, set())

                        # Add the panel condition
                        panel_conditions.append(Vehicle.vehicle_id.in_(panel_query.scalar_subquery()))

                    # Combine panel conditions with OR
                    if panel_conditions:
                        base_query = base_query.filter(or_(*panel_conditions))
                        self._logger.debug(f"Applied {len(panel_conditions)} panel conditions")

                # Get the total count
                count_query = select(func.count()).select_from(base_query.alias())
                total_count = session.execute(count_query).scalar() or 0
                self._logger.debug(f"Total count: {total_count}")

                # Build the query with the requested columns
                query = self._build_columns_query(base_query.scalar_subquery(), columns)

                # Apply table filters
                if table_filters:
                    query = self._apply_table_filters(query, table_filters)
                    self._logger.debug(f"Applied table filters: {table_filters}")

                # Apply sorting
                if sort_by:
                    query = self._apply_sorting(query, sort_by, sort_desc)
                    self._logger.debug(f"Applied sorting: {sort_by} {'DESC' if sort_desc else 'ASC'}")

                # Apply pagination
                if page > 0 and page_size > 0:
                    query = query.offset((page - 1) * page_size).limit(page_size)
                    self._logger.debug(f"Applied pagination: page={page}, page_size={page_size}")

                # Execute the query
                self._logger.debug("Executing final query")
                result_rows = session.execute(query).all()

                # Convert to dictionaries
                results = []
                for row in result_rows:
                    result = {}
                    for i, col in enumerate(query.columns):
                        col_name = col.name
                        value = row[i]
                        result[col_name] = value
                    results.append(result)

                self._logger.debug(f"Query returned {len(results)} rows")
                return (results, total_count)

        except SQLAlchemyError as e:
            self._logger.error(f'Error executing query: {str(e)}')
            raise DatabaseError(f'Error executing query: {str(e)}') from e

    def _build_columns_query(self, vehicle_ids: Any, columns: List[str]) -> Select:
        """
        Build a query with the requested columns.

        Args:
            vehicle_ids: Subquery or expression containing vehicle IDs
            columns: List of column names to include

        Returns:
            Query with all requested columns
        """
        # Start with base query
        query = select(Vehicle.vehicle_id).select_from(Vehicle)
        query = query.filter(Vehicle.vehicle_id.in_(vehicle_ids))

        # Add basic vehicle information
        # These are always included
        query = query.add_columns(
            BaseVehicle.year_id.label('year')
        ).join(
            BaseVehicle,
            Vehicle.base_vehicle_id == BaseVehicle.base_vehicle_id,
            isouter=True
        )

        query = query.add_columns(
            Make.make_id.label('make_id'),
            Make.make_name.label('make')
        ).join(
            Make,
            BaseVehicle.make_id == Make.make_id,
            isouter=True
        )

        query = query.add_columns(
            Model.model_id.label('model_id'),
            Model.model_name.label('model')
        ).join(
            Model,
            BaseVehicle.model_id == Model.model_id,
            isouter=True
        )

        query = query.add_columns(
            SubModel.sub_model_id.label('submodel_id'),
            SubModel.sub_model_name.label('submodel')
        ).join(
            SubModel,
            Vehicle.sub_model_id == SubModel.sub_model_id,
            isouter=True
        )

        # Add optional columns
        for column in columns:
            if column == 'region':
                query = query.add_columns(
                    Region.region_id.label('region_id'),
                    Region.region_name.label('region')
                ).outerjoin(
                    Region,
                    Vehicle.region_id == Region.region_id
                )

            elif column == 'vehicle_type':
                query = query.add_columns(
                    VehicleType.vehicle_type_id.label('vehicle_type_id'),
                    VehicleType.vehicle_type_name.label('vehicle_type')
                ).outerjoin(
                    VehicleType,
                    Model.vehicle_type_id == VehicleType.vehicle_type_id
                )

            elif column == 'drive_type':
                vtdt = aliased(VehicleToDriveType)
                dt = aliased(DriveType)

                query = query.add_columns(
                    dt.drive_type_id.label('drive_type_id'),
                    dt.drive_type_name.label('drive_type')
                ).outerjoin(
                    vtdt,
                    Vehicle.vehicle_id == vtdt.vehicle_id
                ).outerjoin(
                    dt,
                    vtdt.drive_type_id == dt.drive_type_id
                )

            # Additional columns omitted for brevity

        return query

    def _apply_table_filters(self, query: Select, table_filters: Dict[str, Any]) -> Select:
        """
        Apply table filters to a query.

        Args:
            query: Base query
            table_filters: Filters to apply

        Returns:
            Modified query with table filters applied
        """
        for column, filter_value in table_filters.items():
            if column == 'year' and isinstance(filter_value, dict):
                min_year = filter_value.get('min')
                max_year = filter_value.get('max')

                if min_year is not None and max_year is not None:
                    query = query.filter(BaseVehicle.year_id.between(min_year, max_year))
                    self._logger.debug(f"Applied year range table filter: {min_year}-{max_year}")
                elif min_year is not None:
                    query = query.filter(BaseVehicle.year_id >= min_year)
                    self._logger.debug(f"Applied min year table filter: >={min_year}")
                elif max_year is not None:
                    query = query.filter(BaseVehicle.year_id <= max_year)
                    self._logger.debug(f"Applied max year table filter: <={max_year}")

            elif column == 'make' and isinstance(filter_value, str):
                query = query.filter(Make.make_name.ilike(f'%{filter_value}%'))
                self._logger.debug(f"Applied make text table filter: {filter_value}")

            elif column == 'model' and isinstance(filter_value, str):
                query = query.filter(Model.model_name.ilike(f'%{filter_value}%'))
                self._logger.debug(f"Applied model text table filter: {filter_value}")

            elif column == 'submodel' and isinstance(filter_value, str):
                query = query.filter(SubModel.sub_model_name.ilike(f'%{filter_value}%'))
                self._logger.debug(f"Applied submodel text table filter: {filter_value}")

        return query

    def _apply_sorting(self, query: Select, sort_by: str, sort_desc: bool) -> Select:
        """
        Apply sorting to a query.

        Args:
            query: Base query
            sort_by: Column to sort by
            sort_desc: Sort descending if True

        Returns:
            Query with sorting applied
        """
        sort_map = {
            'vehicle_id': Vehicle.vehicle_id,
            'year': BaseVehicle.year_id,
            'make': Make.make_name,
            'model': Model.model_name,
            'submodel': SubModel.sub_model_name,
            'region': Region.region_name,
        }

        if sort_by in sort_map:
            sort_col = sort_map[sort_by]

            if sort_desc:
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())

        return query

    def get_available_columns(self) -> List[Dict[str, str]]:
        """Get the list of available columns for the query builder."""
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
        """Get the list of available filters for the query builder."""
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