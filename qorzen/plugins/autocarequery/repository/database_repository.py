from __future__ import annotations

import asyncio
import logging
from functools import cache
from typing import Any, Dict, List, Optional, Tuple, cast

import structlog
from pydantic import ValidationError
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from qorzen.plugins.autocarequery.models.data_models import (
    DatabaseConnectionError,
    FilterDTO,
    QueryExecutionError,
    VehicleResultDTO,
)

logger = structlog.get_logger(__name__)


class DatabaseRepository:
    """Repository for interacting with the vehicle database."""

    def __init__(self, connection_string: str) -> None:
        """
        Initialize the DatabaseRepository with the given connection string.

        Args:
            connection_string: Database connection string
        """
        self._connection_string = connection_string
        self._create_engine()
        self.metadata = MetaData()
        try:
            self._initialize_tables()
            logger.info("Database repository initialized")
        except Exception as e:
            logger.error("Error initializing database repository", error=str(e))
            self._cleanup_connections()
            raise

    def _create_engine(self) -> None:
        """Create SQLAlchemy engine instances for async and sync operations."""
        self.engine = create_async_engine(
            self._connection_string,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=1,
            max_overflow=0,
            pool_timeout=30,
        )
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        # Create a sync engine for metadata operations
        self.sync_engine = create_engine(
            self._connection_string.replace("+asyncpg", ""),
            echo=False,
            future=True,
            poolclass=None,
        )

    def _initialize_tables(self) -> None:
        """Initialize table metadata by reflecting from the database."""
        try:
            self.metadata.reflect(bind=self.sync_engine, schema="vcdb")
            logger.info("Table metadata loaded")
        except Exception as e:
            logger.error("Error loading table metadata", error=str(e))
            raise DatabaseConnectionError(f"Failed to load table metadata: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            async with self.async_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return False
        finally:
            await self.engine.dispose()

    async def get_filter_values(
            self, table_name: str, value_column: str, id_column: str, filters: Optional[FilterDTO] = None
    ) -> List[Tuple[int, str]]:
        """
        Get distinct values for a given table column with applied filters.

        Args:
            table_name: Name of the table
            value_column: Display value column
            id_column: ID column
            filters: Optional filter criteria

        Returns:
            List of tuples containing (id, display_value)
        """
        try:
            async with self.async_session() as session:
                try:
                    try:
                        await session.execute(text("SET LOCAL statement_timeout = '10000'"))
                    except Exception as e:
                        logger.warning(f"Unable to set statement timeout: {str(e)}")

                    # Basic queries for main dropdowns without filters
                    if filters is None or not any(
                            [
                                filters.year_id,
                                filters.use_year_range,
                                filters.make_id,
                                filters.model_id,
                                filters.submodel_id,
                            ]
                    ):
                        query_sql = ""

                        if table_name == "year":
                            query_sql = """
                                        SELECT DISTINCT year_id as id, CAST(year_id as VARCHAR) as value
                                        FROM vcdb.year
                                        ORDER BY year_id DESC
                                        """
                        elif table_name == "make":
                            query_sql = """
                                        SELECT DISTINCT make_id as id, name as value
                                        FROM vcdb.make
                                        ORDER BY name
                                        """
                        elif table_name == "model":
                            query_sql = """
                                        SELECT DISTINCT model_id as id, name as value
                                        FROM vcdb.model
                                        ORDER BY name
                                        """
                        elif table_name == "submodel":
                            query_sql = """
                                        SELECT DISTINCT submodel_id as id, name as value
                                        FROM vcdb.submodel
                                        ORDER BY name
                                        """
                        else:
                            query_sql = f"""
                            SELECT DISTINCT {id_column} as id, {value_column} as value 
                            FROM vcdb.{table_name}
                            """

                        result = await session.execute(text(query_sql))
                        values = result.fetchall()
                        return [(row.id, row.value) for row in values]

                    # Build filtered queries based on current filter selections
                    params: Dict[str, Any] = {}

                    # Build the appropriate filter query based on current selections
                    # This is a simple implementation - should be expanded based on actual database schema
                    filter_conditions = []
                    from_tables = [f"vcdb.{table_name}"]
                    join_conditions = []

                    # Add appropriate join tables and conditions based on current filters
                    if filters.year_id is not None:
                        if table_name != "year":
                            from_tables.append("vcdb.year")
                            from_tables.append("vcdb.base_vehicle")
                            join_conditions.append("base_vehicle.year_id = year.year_id")
                        filter_conditions.append("year.year_id = :year_id")
                        params["year_id"] = filters.year_id

                    elif filters.use_year_range and filters.year_range_start and filters.year_range_end:
                        if table_name != "year":
                            from_tables.append("vcdb.year")
                            from_tables.append("vcdb.base_vehicle")
                            join_conditions.append("base_vehicle.year_id = year.year_id")
                        filter_conditions.append("year.year_id BETWEEN :year_start AND :year_end")
                        params["year_start"] = filters.year_range_start
                        params["year_end"] = filters.year_range_end

                    if filters.make_id is not None:
                        if table_name != "make":
                            from_tables.append("vcdb.make")
                            from_tables.append("vcdb.base_vehicle")
                            join_conditions.append("base_vehicle.make_id = make.make_id")
                        filter_conditions.append("make.make_id = :make_id")
                        params["make_id"] = filters.make_id

                    if filters.model_id is not None:
                        if table_name != "model":
                            from_tables.append("vcdb.model")
                            from_tables.append("vcdb.base_vehicle")
                            join_conditions.append("base_vehicle.model_id = model.model_id")
                        filter_conditions.append("model.model_id = :model_id")
                        params["model_id"] = filters.model_id

                    if filters.submodel_id is not None:
                        if table_name != "submodel":
                            from_tables.append("vcdb.submodel")
                            from_tables.append("vcdb.vehicle")
                            join_conditions.append("vehicle.submodel_id = submodel.submodel_id")
                        filter_conditions.append("submodel.submodel_id = :submodel_id")
                        params["submodel_id"] = filters.submodel_id

                    # Handle more complex filtering for other dropdown types
                    if table_name == "year":
                        query = f"""
                        SELECT DISTINCT year.year_id as id, CAST(year.year_id as VARCHAR) as value
                        FROM {', '.join(set(from_tables))}
                        """
                        if join_conditions:
                            query += f" WHERE {' AND '.join(join_conditions)}"
                        if filter_conditions:
                            query += f" AND {' AND '.join(filter_conditions)}" if join_conditions else f" WHERE {' AND '.join(filter_conditions)}"
                        query += " ORDER BY year.year_id DESC"

                    elif table_name == "make":
                        query = f"""
                        SELECT DISTINCT make.make_id as id, make.name as value
                        FROM {', '.join(set(from_tables))}
                        """
                        if join_conditions:
                            query += f" WHERE {' AND '.join(join_conditions)}"
                        if filter_conditions:
                            query += f" AND {' AND '.join(filter_conditions)}" if join_conditions else f" WHERE {' AND '.join(filter_conditions)}"
                        query += " ORDER BY make.name"

                    elif table_name == "model":
                        query = f"""
                        SELECT DISTINCT model.model_id as id, model.name as value
                        FROM {', '.join(set(from_tables))}
                        """
                        if join_conditions:
                            query += f" WHERE {' AND '.join(join_conditions)}"
                        if filter_conditions:
                            query += f" AND {' AND '.join(filter_conditions)}" if join_conditions else f" WHERE {' AND '.join(filter_conditions)}"
                        query += " ORDER BY model.name"

                    elif table_name == "submodel":
                        query = f"""
                        SELECT DISTINCT submodel.submodel_id as id, submodel.name as value
                        FROM {', '.join(set(from_tables))}
                        """
                        if join_conditions:
                            query += f" WHERE {' AND '.join(join_conditions)}"
                        if filter_conditions:
                            query += f" AND {' AND '.join(filter_conditions)}" if join_conditions else f" WHERE {' AND '.join(filter_conditions)}"
                        query += " ORDER BY submodel.name"

                    else:
                        # Generic query for other filter types
                        query = f"""
                        SELECT DISTINCT {table_name}.{id_column} as id, {table_name}.{value_column} as value
                        FROM {', '.join(set(from_tables))}
                        """
                        if join_conditions:
                            query += f" WHERE {' AND '.join(join_conditions)}"
                        if filter_conditions:
                            query += f" AND {' AND '.join(filter_conditions)}" if join_conditions else f" WHERE {' AND '.join(filter_conditions)}"
                        query += f" ORDER BY {table_name}.{value_column}"

                    # Execute the query with params
                    result = await session.execute(text(query), params)
                    values = result.fetchall()
                    return [(row.id, row.value) for row in values]

                except Exception as e:
                    logger.error(f"Error in get_filter_values", error=str(e))
                    return []
        except Exception as e:
            logger.error("Error fetching filter values", table=table_name, error=str(e))
            return []
        finally:
            await self.engine.dispose()

    async def execute_vehicle_query(
            self, filters: FilterDTO, limit: Optional[int] = 1000
    ) -> List[VehicleResultDTO]:
        """
        Execute vehicle query with the given filters.

        Args:
            filters: Filter criteria
            limit: Maximum number of results to return

        Returns:
            List of VehicleResultDTO objects

        Raises:
            QueryExecutionError: If query execution fails
        """
        try:
            async with self.async_session() as session:
                try:
                    await session.execute(text("SET LOCAL statement_timeout = '30000'"))
                except Exception as e:
                    logger.warning(f"Unable to set statement timeout: {str(e)}")

                # Build query with proper joins and filters
                query_parts = []
                params: Dict[str, Any] = {}

                # Start with base query that joins all necessary tables
                base_query = """
                             SELECT v.vehicle_id, \
                                    y.year_id as year,
                    m.name as make,
                    md.name as model,
                    sm.name as submodel,
                    eb.liter as engine_liter,
                    eb.cylinders as engine_cylinders,
                    eb.block_type as engine_block_type,
                    eb.cc as engine_cc,
                    eb.cid as engine_cid,
                    cht.name as cylinder_head_type,
                    val.valves_per_engine as valves,
                    mbc.code as mfr_body_code,
                    bnd.num_doors as body_num_doors,
                    wb.wheel_base as wheel_base,
                    wb.wheel_base_metric as wheel_base_metric,
                    ba.name as brake_abs,
                    ss.name as steering_system,
                    tct.name as transmission_control_type,
                    tmc.code as transmission_mfr_code,
                    dt.name as drive_type
                             FROM vcdb.vehicle v
                                 JOIN vcdb.base_vehicle bv \
                             ON v.base_vehicle_id = bv.base_vehicle_id
                                 JOIN vcdb.year y ON bv.year_id = y.year_id
                                 JOIN vcdb.make m ON bv.make_id = m.make_id
                                 JOIN vcdb.model md ON bv.model_id = md.model_id
                                 JOIN vcdb.submodel sm ON v.submodel_id = sm.submodel_id
                                 LEFT JOIN vcdb.vehicle_to_engine_config vtec ON v.vehicle_id = vtec.vehicle_id
                                 LEFT JOIN vcdb.engine_block eb ON eb.engine_block_id = vtec.engine_config_id
                                 LEFT JOIN vcdb.cylinder_head_type cht ON cht.cylinder_head_type_id = vtec.engine_config_id
                                 LEFT JOIN vcdb.valves val ON val.valves_id = vtec.engine_config_id
                                 LEFT JOIN vcdb.vehicle_to_mfr_body_code vtmbc ON v.vehicle_id = vtmbc.vehicle_id
                                 LEFT JOIN vcdb.mfr_body_code mbc ON vtmbc.mfr_body_code_id = mbc.mfr_body_code_id
                                 LEFT JOIN vcdb.vehicle_to_body_style_config vtbsc ON v.vehicle_id = vtbsc.vehicle_id
                                 LEFT JOIN vcdb.body_num_doors bnd ON bnd.body_num_doors_id = vtbsc.body_style_config_id
                                 LEFT JOIN vcdb.vehicle_to_wheel_base vtwb ON v.vehicle_id = vtwb.vehicle_id
                                 LEFT JOIN vcdb.wheel_base wb ON vtwb.wheel_base_id = wb.wheel_base_id
                                 LEFT JOIN vcdb.vehicle_to_brake_config vtbc ON v.vehicle_id = vtbc.vehicle_id
                                 LEFT JOIN vcdb.brake_abs ba ON ba.brake_abs_id = vtbc.brake_config_id
                                 LEFT JOIN vcdb.vehicle_to_steering_config vtsc ON v.vehicle_id = vtsc.vehicle_id
                                 LEFT JOIN vcdb.steering_system ss ON ss.steering_system_id = vtsc.steering_config_id
                                 LEFT JOIN vcdb.vehicle_to_transmission vtt ON v.vehicle_id = vtt.vehicle_id
                                 LEFT JOIN vcdb.transmission_control_type tct ON tct.transmission_control_type_id = vtt.transmission_id
                                 LEFT JOIN vcdb.transmission_mfr_code tmc ON tmc.transmission_mfr_code_id = vtt.transmission_id
                                 LEFT JOIN vcdb.vehicle_to_drive_type vtdt ON v.vehicle_id = vtdt.vehicle_id
                                 LEFT JOIN vcdb.drive_type dt ON vtdt.drive_type_id = dt.drive_type_id \
                             """

                # Add WHERE clause filters based on filter criteria
                where_conditions = []

                # Year filter
                if filters.use_year_range and filters.year_range_start and filters.year_range_end:
                    where_conditions.append("y.year_id BETWEEN :year_start AND :year_end")
                    params["year_start"] = filters.year_range_start
                    params["year_end"] = filters.year_range_end
                elif filters.year_id is not None:
                    where_conditions.append("y.year_id = :year_id")
                    params["year_id"] = filters.year_id

                # Make filter
                if filters.make_id is not None:
                    where_conditions.append("m.make_id = :make_id")
                    params["make_id"] = filters.make_id

                # Model filter
                if filters.model_id is not None:
                    where_conditions.append("md.model_id = :model_id")
                    params["model_id"] = filters.model_id

                # Submodel filter
                if filters.submodel_id is not None:
                    where_conditions.append("sm.submodel_id = :submodel_id")
                    params["submodel_id"] = filters.submodel_id

                # Engine filters
                if filters.engine_liter is not None:
                    where_conditions.append("eb.liter = :engine_liter")
                    params["engine_liter"] = filters.engine_liter

                if filters.engine_cid is not None:
                    where_conditions.append("eb.cid = :engine_cid")
                    params["engine_cid"] = filters.engine_cid

                # Add more filter conditions for other filter types
                if filters.cylinder_head_type_id is not None:
                    where_conditions.append("cht.cylinder_head_type_id = :cylinder_head_type_id")
                    params["cylinder_head_type_id"] = filters.cylinder_head_type_id

                if filters.valves_id is not None:
                    where_conditions.append("val.valves_id = :valves_id")
                    params["valves_id"] = filters.valves_id

                if filters.mfr_body_code_id is not None:
                    where_conditions.append("mbc.mfr_body_code_id = :mfr_body_code_id")
                    params["mfr_body_code_id"] = filters.mfr_body_code_id

                if filters.body_num_doors_id is not None:
                    where_conditions.append("bnd.body_num_doors_id = :body_num_doors_id")
                    params["body_num_doors_id"] = filters.body_num_doors_id

                if filters.wheel_base_id is not None:
                    where_conditions.append("wb.wheel_base_id = :wheel_base_id")
                    params["wheel_base_id"] = filters.wheel_base_id

                if filters.brake_abs_id is not None:
                    where_conditions.append("ba.brake_abs_id = :brake_abs_id")
                    params["brake_abs_id"] = filters.brake_abs_id

                if filters.steering_system_id is not None:
                    where_conditions.append("ss.steering_system_id = :steering_system_id")
                    params["steering_system_id"] = filters.steering_system_id

                if filters.transmission_control_type_id is not None:
                    where_conditions.append("tct.transmission_control_type_id = :transmission_control_type_id")
                    params["transmission_control_type_id"] = filters.transmission_control_type_id

                if filters.transmission_mfr_code_id is not None:
                    where_conditions.append("tmc.transmission_mfr_code_id = :transmission_mfr_code_id")
                    params["transmission_mfr_code_id"] = filters.transmission_mfr_code_id

                if filters.drive_type_id is not None:
                    where_conditions.append("dt.drive_type_id = :drive_type_id")
                    params["drive_type_id"] = filters.drive_type_id

                # Complete the query with WHERE clause and LIMIT
                full_query = base_query
                if where_conditions:
                    full_query += " WHERE " + " AND ".join(where_conditions)
                full_query += " LIMIT :limit"
                params["limit"] = limit

                # Execute query and process results
                try:
                    result = await session.execute(text(full_query), params)
                    rows = result.fetchall()

                    # Convert rows to VehicleResultDTO objects
                    vehicles = []
                    for row in rows:
                        try:
                            vehicle_dict = {
                                "vehicle_id": row.vehicle_id,
                                "year": row.year,
                                "make": row.make,
                                "model": row.model,
                                "submodel": row.submodel,
                                "engine_liter": row.engine_liter,
                                "engine_cylinders": row.engine_cylinders,
                                "engine_block_type": row.engine_block_type,
                                "engine_cc": row.engine_cc,
                                "engine_cid": row.engine_cid,
                                "cylinder_head_type": row.cylinder_head_type,
                                "valves": row.valves,
                                "mfr_body_code": row.mfr_body_code,
                                "body_num_doors": row.body_num_doors,
                                "wheel_base": row.wheel_base,
                                "wheel_base_metric": row.wheel_base_metric,
                                "brake_abs": row.brake_abs,
                                "steering_system": row.steering_system,
                                "transmission_control_type": row.transmission_control_type,
                                "transmission_mfr_code": row.transmission_mfr_code,
                                "drive_type": row.drive_type
                            }
                            vehicles.append(VehicleResultDTO(**vehicle_dict))
                        except ValidationError as ve:
                            logger.warning(f"Validation error for vehicle {row.vehicle_id}: {str(ve)}")
                            continue

                    logger.info(f"Query returned {len(vehicles)} results")
                    return vehicles

                except Exception as e:
                    logger.error("Error executing vehicle query", error=str(e))
                    raise QueryExecutionError(f"Error executing query: {str(e)}")
        except Exception as e:
            logger.error("Error executing vehicle query", error=str(e))
            raise QueryExecutionError(f"Error executing query: {str(e)}")
        finally:
            await self.engine.dispose()

    def _cleanup_connections(self) -> None:
        """Clean up synchronous database connections."""
        if hasattr(self, "sync_engine"):
            self.sync_engine.dispose()

    async def cleanup_async_connections(self) -> None:
        """Clean up asynchronous database connections."""
        if hasattr(self, "engine"):
            await self.engine.dispose()