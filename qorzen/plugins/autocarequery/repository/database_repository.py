from __future__ import annotations

import asyncio
from functools import cache
from typing import Any, Dict, List, Optional, Tuple, cast

import structlog
from pydantic_core._pydantic_core import ValidationError
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from qorzen.plugins.autocarequery.models.data_models import (
    DatabaseConnectionError, FilterDTO, QueryExecutionError, VehicleResultDTO
)

logger = structlog.get_logger(__name__)


class DatabaseRepository:
    """Repository for database operations."""

    def __init__(self, connection_string: str) -> None:
        """
        Initialize the repository with a connection string.

        Args:
            connection_string: Database connection string
        """
        self.engine: AsyncEngine = create_async_engine(
            connection_string,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30
        )
        self.async_session = sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        self.sync_engine = create_engine(
            connection_string.replace('+asyncpg', ''),
            echo=False,
            future=True
        )
        self.metadata = MetaData()
        self._initialize_tables()
        logger.info('Database repository initialized')

    def _initialize_tables(self) -> None:
        """Load metadata for all tables."""
        try:
            self.metadata.reflect(bind=self.sync_engine, schema='vcdb')
            logger.info('Table metadata loaded')
        except Exception as e:
            logger.error('Error loading table metadata', error=str(e))
            raise DatabaseConnectionError(f'Failed to load table metadata: {str(e)}')

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
            logger.error('Connection test failed', error=str(e))
            return False

    async def get_filter_values(
            self,
            table_name: str,
            value_column: str,
            id_column: str,
            filters: Optional[FilterDTO] = None
    ) -> List[Tuple[int, str]]:
        """
        Get values for filter dropdowns based on current filters.

        Args:
            table_name: Name of the table
            value_column: Name of the column containing display values
            id_column: Name of the column containing ID values
            filters: Current filter criteria

        Returns:
            List of tuples containing (id, display_value)
        """
        try:
            async with self.async_session() as session:
                try:
                    await session.execute(text("SET LOCAL statement_timeout = '10000'"))
                except Exception as e:
                    logger.warning(f'Unable to set statement timeout: {str(e)}')

                # Handle initial loading with no filters
                if filters is None or not any([
                    filters.year_id,
                    filters.use_year_range,
                    filters.make_id,
                    filters.model_id,
                    filters.submodel_id
                ]):
                    if table_name == 'year':
                        query = 'SELECT DISTINCT year_id as id, CAST(year_id as VARCHAR) as value FROM vcdb.year ORDER BY year_id DESC'
                    elif table_name == 'make':
                        query = 'SELECT DISTINCT make_id as id, name as value FROM vcdb.make ORDER BY name'
                    elif table_name == 'model':
                        query = 'SELECT DISTINCT model_id as id, name as value FROM vcdb.model ORDER BY name'
                    elif table_name == 'submodel':
                        query = 'SELECT DISTINCT submodel_id as id, name as value FROM vcdb.submodel ORDER BY name'

                    if table_name in ['year', 'make', 'model', 'submodel']:
                        try:
                            result = await session.execute(text(query))
                            values = result.fetchall()
                            return [(row.id, row.value) for row in values]
                        except Exception as e:
                            logger.error(f'Error fetching initial values for {table_name}: {str(e)}')
                            return []

                # Build vehicle query to get valid vehicle IDs based on filters
                vehicle_query = """
                                SELECT DISTINCT v.vehicle_id
                                FROM vcdb.vehicle v
                                         JOIN vcdb.base_vehicle bv ON bv.base_vehicle_id = v.base_vehicle_id
                                """

                where_clauses = []
                if filters:
                    if filters.use_year_range and filters.year_range_start is not None and filters.year_range_end is not None:
                        where_clauses.append(
                            f'bv.year_id BETWEEN {filters.year_range_start} AND {filters.year_range_end}')
                    elif filters.year_id is not None:
                        where_clauses.append(f'bv.year_id = {filters.year_id}')

                    if filters.make_id is not None:
                        where_clauses.append(f'bv.make_id = {filters.make_id}')

                    if filters.model_id is not None:
                        where_clauses.append(f'bv.model_id = {filters.model_id}')

                    if filters.submodel_id is not None:
                        where_clauses.append(f'v.submodel_id = {filters.submodel_id}')

                # Add extra joins and where clauses for advanced filters
                extra_joins = []
                if filters:
                    # Fix for engine-related filters
                    engine_filters_needed = (
                            filters.engine_liter is not None or
                            filters.engine_cid is not None or
                            filters.cylinder_head_type_id is not None or
                            filters.valves_id is not None
                    )

                    if engine_filters_needed:
                        # Use INNER JOIN instead of LEFT JOIN for engine filters
                        extra_joins.append("""
                            INNER JOIN vcdb.vehicle_to_engine_config vtec ON vtec.vehicle_id = v.vehicle_id
                            INNER JOIN vcdb.engine_config2 ec ON ec.engine_config_id = vtec.engine_config_id
                        """)

                        if filters.engine_liter is not None:
                            extra_joins.append(
                                'INNER JOIN vcdb.engine_block eb ON eb.engine_block_id = ec.engine_block_id')
                            where_clauses.append(f"eb.liter = '{filters.engine_liter}'")
                        elif filters.engine_cid is not None:
                            extra_joins.append(
                                'INNER JOIN vcdb.engine_block eb ON eb.engine_block_id = ec.engine_block_id')
                            where_clauses.append(f"eb.cid = '{filters.engine_cid}'")

                        if filters.cylinder_head_type_id is not None:
                            extra_joins.append(
                                'INNER JOIN vcdb.cylinder_head_type cht ON cht.cylinder_head_type_id = ec.cylinder_head_type_id')
                            where_clauses.append(f'cht.cylinder_head_type_id = {filters.cylinder_head_type_id}')

                        if filters.valves_id is not None:
                            extra_joins.append('INNER JOIN vcdb.valves val ON val.valves_id = ec.valves_id')
                            where_clauses.append(f'val.valves_id = {filters.valves_id}')

                    # Other filters
                    if filters.mfr_body_code_id is not None:
                        extra_joins.append("""
                            JOIN vcdb.vehicle_to_mfr_body_code vtmbc ON vtmbc.vehicle_id = v.vehicle_id
                            JOIN vcdb.mfr_body_code mbc ON mbc.mfr_body_code_id = vtmbc.mfr_body_code_id
                        """)
                        where_clauses.append(f'mbc.mfr_body_code_id = {filters.mfr_body_code_id}')

                    if filters.body_num_doors_id is not None:
                        extra_joins.append("""
                            JOIN vcdb.vehicle_to_body_style_config vtbsc ON vtbsc.vehicle_id = v.vehicle_id
                            JOIN vcdb.body_style_config bsc ON bsc.body_style_config_id = vtbsc.body_style_config_id
                            JOIN vcdb.body_num_doors bnd ON bnd.body_num_doors_id = bsc.body_num_doors_id
                        """)
                        where_clauses.append(f'bnd.body_num_doors_id = {filters.body_num_doors_id}')

                    if filters.wheel_base_id is not None:
                        extra_joins.append("""
                            JOIN vcdb.vehicle_to_wheel_base vtwb ON vtwb.vehicle_id = v.vehicle_id
                            JOIN vcdb.wheel_base wb ON wb.wheel_base_id = vtwb.wheel_base_id
                        """)
                        where_clauses.append(f'wb.wheel_base_id = {filters.wheel_base_id}')

                    if filters.brake_abs_id is not None:
                        extra_joins.append("""
                            JOIN vcdb.vehicle_to_brake_config vtbc ON vtbc.vehicle_id = v.vehicle_id
                            JOIN vcdb.brake_config bc ON bc.brake_config_id = vtbc.brake_config_id
                            JOIN vcdb.brake_abs ba ON ba.brake_abs_id = bc.brake_abs_id
                        """)
                        where_clauses.append(f'ba.brake_abs_id = {filters.brake_abs_id}')

                    if filters.steering_system_id is not None:
                        extra_joins.append("""
                            JOIN vcdb.vehicle_to_steering_config vtsc ON vtsc.vehicle_id = v.vehicle_id
                            JOIN vcdb.steering_config sc ON sc.steering_config_id = vtsc.steering_config_id
                            JOIN vcdb.steering_system ss ON ss.steering_system_id = sc.steering_system_id
                        """)
                        where_clauses.append(f'ss.steering_system_id = {filters.steering_system_id}')

                    if filters.transmission_control_type_id is not None or filters.transmission_mfr_code_id is not None:
                        extra_joins.append("""
                            JOIN vcdb.vehicle_to_transmission vtt ON vtt.vehicle_id = v.vehicle_id
                            JOIN vcdb.transmission t ON t.transmission_id = vtt.transmission_id
                        """)

                        if filters.transmission_control_type_id is not None:
                            extra_joins.append("""
                                JOIN vcdb.transmission_base tb ON tb.transmission_base_id = t.transmission_base_id
                                JOIN vcdb.transmission_control_type tct ON tct.transmission_control_type_id = tb.transmission_control_type_id
                            """)
                            where_clauses.append(
                                f'tct.transmission_control_type_id = {filters.transmission_control_type_id}')

                        if filters.transmission_mfr_code_id is not None:
                            extra_joins.append(
                                'JOIN vcdb.transmission_mfr_code tmc ON tmc.transmission_mfr_code_id = t.transmission_mfr_code_id')
                            where_clauses.append(f'tmc.transmission_mfr_code_id = {filters.transmission_mfr_code_id}')

                    if filters.drive_type_id is not None:
                        extra_joins.append("""
                            JOIN vcdb.vehicle_to_drive_type vtdt ON vtdt.vehicle_id = v.vehicle_id
                            JOIN vcdb.drive_type dt ON dt.drive_type_id = vtdt.drive_type_id
                        """)
                        where_clauses.append(f'dt.drive_type_id = {filters.drive_type_id}')

                for join in extra_joins:
                    vehicle_query += join

                if where_clauses:
                    vehicle_query += ' WHERE ' + ' AND '.join(where_clauses)

                vehicle_query += ' LIMIT 1000'

                try:
                    vehicle_result = await session.execute(text(vehicle_query))
                    valid_vehicle_ids = [str(row[0]) for row in vehicle_result]
                except Exception as e:
                    logger.error(f'Error fetching vehicle IDs: {str(e)}')
                    return []

                if not valid_vehicle_ids:
                    return []

                # Generate the appropriate query for the requested filter
                if table_name in ['year', 'make', 'model', 'submodel']:
                    if table_name == 'year':
                        query = """
                                SELECT DISTINCT y.year_id as id, CAST(y.year_id as VARCHAR) as value
                                FROM vcdb.year y
                                    JOIN vcdb.base_vehicle bv ON bv.year_id = y.year_id
                                    JOIN vcdb.vehicle v ON v.base_vehicle_id = bv.base_vehicle_id
                                """
                    elif table_name == 'make':
                        query = """
                                SELECT DISTINCT m.make_id as id, m.name as value
                                FROM vcdb.make m
                                    JOIN vcdb.base_vehicle bv ON bv.make_id = m.make_id
                                    JOIN vcdb.vehicle v ON v.base_vehicle_id = bv.base_vehicle_id
                                """
                    elif table_name == 'model':
                        query = """
                                SELECT DISTINCT md.model_id as id, md.name as value
                                FROM vcdb.model md
                                    JOIN vcdb.base_vehicle bv ON bv.model_id = md.model_id
                                    JOIN vcdb.vehicle v ON v.base_vehicle_id = bv.base_vehicle_id
                                """
                    elif table_name == 'submodel':
                        query = """
                                SELECT DISTINCT s.submodel_id as id, s.name as value
                                FROM vcdb.submodel s
                                    JOIN vcdb.vehicle v ON v.submodel_id = s.submodel_id
                                """

                # Fix for engine_liter filter
                elif table_name == 'engine_block' and value_column == 'liter':
                    query = """
                            SELECT DISTINCT eb.liter as id, eb.liter as value
                            FROM vcdb.engine_block eb
                                JOIN vcdb.engine_config2 ec ON ec.engine_block_id = eb.engine_block_id
                                JOIN vcdb.vehicle_to_engine_config vtec ON vtec.engine_config_id = ec.engine_config_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtec.vehicle_id
                            """

                # Fix for engine_cid filter
                elif table_name == 'engine_block' and value_column == 'cid':
                    query = """
                            SELECT DISTINCT eb.cid as id, eb.cid as value
                            FROM vcdb.engine_block eb
                                JOIN vcdb.engine_config2 ec ON ec.engine_block_id = eb.engine_block_id
                                JOIN vcdb.vehicle_to_engine_config vtec ON vtec.engine_config_id = ec.engine_config_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtec.vehicle_id
                            """

                # Fix for cylinder_head_type filter
                elif table_name == 'cylinder_head_type':
                    query = """
                            SELECT DISTINCT cht.cylinder_head_type_id as id, cht.name as value
                            FROM vcdb.cylinder_head_type cht
                                JOIN vcdb.engine_config2 ec ON ec.cylinder_head_type_id = cht.cylinder_head_type_id
                                JOIN vcdb.vehicle_to_engine_config vtec ON vtec.engine_config_id = ec.engine_config_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtec.vehicle_id
                            """

                elif table_name == 'valves':
                    query = """
                            SELECT DISTINCT val.valves_id as id, val.valves_per_engine as value
                            FROM vcdb.valves val
                                JOIN vcdb.engine_config2 ec ON ec.valves_id = val.valves_id
                                JOIN vcdb.vehicle_to_engine_config vtec ON vtec.engine_config_id = ec.engine_config_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtec.vehicle_id
                            """

                elif table_name == 'mfr_body_code':
                    query = """
                            SELECT DISTINCT mbc.mfr_body_code_id as id, mbc.code as value
                            FROM vcdb.mfr_body_code mbc
                                JOIN vcdb.vehicle_to_mfr_body_code vtmbc ON vtmbc.mfr_body_code_id = mbc.mfr_body_code_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtmbc.vehicle_id
                            """

                elif table_name == 'body_num_doors':
                    query = """
                            SELECT DISTINCT bnd.body_num_doors_id as id, bnd.num_doors as value
                            FROM vcdb.body_num_doors bnd
                                JOIN vcdb.body_style_config bsc ON bsc.body_num_doors_id = bnd.body_num_doors_id
                                JOIN vcdb.vehicle_to_body_style_config vtbsc ON vtbsc.body_style_config_id = bsc.body_style_config_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtbsc.vehicle_id
                            """

                elif table_name == 'wheel_base':
                    query = """
                            SELECT DISTINCT wb.wheel_base_id as id, wb.wheel_base as value
                            FROM vcdb.wheel_base wb
                                JOIN vcdb.vehicle_to_wheel_base vtwb ON vtwb.wheel_base_id = wb.wheel_base_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtwb.vehicle_id
                            """

                elif table_name == 'brake_abs':
                    query = """
                            SELECT DISTINCT ba.brake_abs_id as id, ba.name as value
                            FROM vcdb.brake_abs ba
                                JOIN vcdb.brake_config bc ON bc.brake_abs_id = ba.brake_abs_id
                                JOIN vcdb.vehicle_to_brake_config vtbc ON vtbc.brake_config_id = bc.brake_config_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtbc.vehicle_id
                            """

                elif table_name == 'steering_system':
                    query = """
                            SELECT DISTINCT ss.steering_system_id as id, ss.name as value
                            FROM vcdb.steering_system ss
                                JOIN vcdb.steering_config sc ON sc.steering_system_id = ss.steering_system_id
                                JOIN vcdb.vehicle_to_steering_config vtsc ON vtsc.steering_config_id = sc.steering_config_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtsc.vehicle_id
                            """

                elif table_name == 'transmission_control_type':
                    query = """
                            SELECT DISTINCT tct.transmission_control_type_id as id, tct.name as value
                            FROM vcdb.transmission_control_type tct
                                JOIN vcdb.transmission_base tb ON tb.transmission_control_type_id = tct.transmission_control_type_id
                                JOIN vcdb.transmission t ON t.transmission_base_id = tb.transmission_base_id
                                JOIN vcdb.vehicle_to_transmission vtt ON vtt.transmission_id = t.transmission_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtt.vehicle_id
                            """

                elif table_name == 'transmission_mfr_code':
                    query = """
                            SELECT DISTINCT tmc.transmission_mfr_code_id as id, tmc.code as value
                            FROM vcdb.transmission_mfr_code tmc
                                JOIN vcdb.transmission t ON t.transmission_mfr_code_id = tmc.transmission_mfr_code_id
                                JOIN vcdb.vehicle_to_transmission vtt ON vtt.transmission_id = t.transmission_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtt.vehicle_id
                            """

                elif table_name == 'drive_type':
                    query = """
                            SELECT DISTINCT dt.drive_type_id as id, dt.name as value
                            FROM vcdb.drive_type dt
                                JOIN vcdb.vehicle_to_drive_type vtdt ON vtdt.drive_type_id = dt.drive_type_id
                                JOIN vcdb.vehicle v ON v.vehicle_id = vtdt.vehicle_id
                            """

                else:
                    query = f"""
                        SELECT DISTINCT {id_column} as id, {value_column} as value 
                        FROM vcdb.{table_name}
                    """

                # Add WHERE clause for valid vehicle IDs
                if table_name not in ['year', 'make', 'model', 'submodel'] or valid_vehicle_ids:
                    if len(valid_vehicle_ids) > 500:
                        vehicle_ids_str = ', '.join(valid_vehicle_ids[:500])
                    else:
                        vehicle_ids_str = ', '.join(valid_vehicle_ids)

                    if 'WHERE' in query:
                        query += f' AND v.vehicle_id IN ({vehicle_ids_str})'
                    else:
                        query += f' WHERE v.vehicle_id IN ({vehicle_ids_str})'

                query += ' ORDER BY value'

                try:
                    result = await session.execute(text(query))
                    values = result.fetchall()

                    # Handle duplicate values with same ID
                    unique_values = {}
                    for row in values:
                        id_val = row.id
                        display_val = row.value.strip() if isinstance(row.value, str) else row.value
                        if id_val not in unique_values:
                            unique_values[id_val] = display_val

                    return [(id_val, display_val) for id_val, display_val in unique_values.items()]
                except Exception as e:
                    logger.error(f'Error fetching filter values for {table_name}', error=str(e))
                    return []

        except Exception as e:
            logger.error('Error fetching filter values', table=table_name, error=str(e))
            return []

    async def execute_vehicle_query(self, filters: FilterDTO, limit: Optional[int] = 1000) -> List[VehicleResultDTO]:
        """
        Execute query for vehicles based on filter criteria.

        Args:
            filters: Filter criteria
            limit: Maximum number of results to return

        Returns:
            List of VehicleResultDTO objects
        """
        try:
            async with self.async_session() as session:
                try:
                    await session.execute(text("SET LOCAL statement_timeout = '30000'"))
                except Exception as e:
                    logger.warning(f'Unable to set statement timeout: {str(e)}')

                # Define columns to select
                select_columns = [
                    'v.vehicle_id',
                    'y.year_id as year',
                    'm.name as make',
                    'md.name as model',
                    'sm.name as submodel',
                    'eb.liter as engine_liter',
                    'eb.cylinders as engine_cylinders',
                    'eb.block_type as engine_block_type',
                    'eb.cc as engine_cc',
                    'eb.cid as engine_cid',
                    'cht.name as cylinder_head_type',
                    'val.valves_per_engine as valves',
                    'mbc.code as mfr_body_code',
                    'bnd.num_doors as body_num_doors',
                    'wb.wheel_base',
                    'wb.wheel_base_metric',
                    'ba.name as brake_abs',
                    'ss.name as steering_system',
                    'tct.name as transmission_control_type',
                    'tmc.code as transmission_mfr_code',
                    'dt.name as drive_type'
                ]

                # Build base query with FROM and JOIN clauses
                # Fix for engine-related filters by using INNER JOIN when these filters are applied
                engine_filters_applied = (
                        filters.engine_liter is not None or
                        filters.engine_cid is not None or
                        filters.cylinder_head_type_id is not None or
                        filters.valves_id is not None
                )

                # Base joins
                from_clause = """
                    FROM vcdb.vehicle v
                    JOIN vcdb.base_vehicle bv ON bv.base_vehicle_id = v.base_vehicle_id
                    JOIN vcdb.year y ON y.year_id = bv.year_id
                    JOIN vcdb.make m ON m.make_id = bv.make_id
                    JOIN vcdb.model md ON md.model_id = bv.model_id
                    JOIN vcdb.submodel sm ON sm.submodel_id = v.submodel_id
                """

                # Engine-related joins - use INNER JOIN if engine filters are applied
                if engine_filters_applied:
                    from_clause += """
                        INNER JOIN vcdb.vehicle_to_engine_config vtec ON vtec.vehicle_id = v.vehicle_id
                        INNER JOIN vcdb.engine_config2 ec ON ec.engine_config_id = vtec.engine_config_id
                        INNER JOIN vcdb.engine_block eb ON eb.engine_block_id = ec.engine_block_id
                        INNER JOIN vcdb.cylinder_head_type cht ON cht.cylinder_head_type_id = ec.cylinder_head_type_id
                        INNER JOIN vcdb.valves val ON val.valves_id = ec.valves_id
                    """
                else:
                    from_clause += """
                        LEFT JOIN vcdb.vehicle_to_engine_config vtec ON vtec.vehicle_id = v.vehicle_id
                        LEFT JOIN vcdb.engine_config2 ec ON ec.engine_config_id = vtec.engine_config_id
                        LEFT JOIN vcdb.engine_block eb ON eb.engine_block_id = ec.engine_block_id
                        LEFT JOIN vcdb.cylinder_head_type cht ON cht.cylinder_head_type_id = ec.cylinder_head_type_id
                        LEFT JOIN vcdb.valves val ON val.valves_id = ec.valves_id
                    """

                # Other joins - keep as LEFT JOIN
                from_clause += """
                    LEFT JOIN vcdb.vehicle_to_mfr_body_code vtmbc ON vtmbc.vehicle_id = v.vehicle_id
                    LEFT JOIN vcdb.mfr_body_code mbc ON mbc.mfr_body_code_id = vtmbc.mfr_body_code_id
                    LEFT JOIN vcdb.vehicle_to_body_style_config vtbsc ON vtbsc.vehicle_id = v.vehicle_id
                    LEFT JOIN vcdb.body_style_config bsc ON bsc.body_style_config_id = vtbsc.body_style_config_id
                    LEFT JOIN vcdb.body_num_doors bnd ON bnd.body_num_doors_id = bsc.body_num_doors_id
                    LEFT JOIN vcdb.vehicle_to_wheel_base vtwb ON vtwb.vehicle_id = v.vehicle_id
                    LEFT JOIN vcdb.wheel_base wb ON wb.wheel_base_id = vtwb.wheel_base_id
                    LEFT JOIN vcdb.vehicle_to_brake_config vtbc ON vtbc.vehicle_id = v.vehicle_id
                    LEFT JOIN vcdb.brake_config bc ON bc.brake_config_id = vtbc.brake_config_id
                    LEFT JOIN vcdb.brake_abs ba ON ba.brake_abs_id = bc.brake_abs_id
                    LEFT JOIN vcdb.vehicle_to_steering_config vtsc ON vtsc.vehicle_id = v.vehicle_id
                    LEFT JOIN vcdb.steering_config sc ON sc.steering_config_id = vtsc.steering_config_id
                    LEFT JOIN vcdb.steering_system ss ON ss.steering_system_id = sc.steering_system_id
                    LEFT JOIN vcdb.vehicle_to_transmission vtt ON vtt.vehicle_id = v.vehicle_id
                    LEFT JOIN vcdb.transmission t ON t.transmission_id = vtt.transmission_id
                    LEFT JOIN vcdb.transmission_base tb ON tb.transmission_base_id = t.transmission_base_id
                    LEFT JOIN vcdb.transmission_control_type tct ON tct.transmission_control_type_id = tb.transmission_control_type_id
                    LEFT JOIN vcdb.transmission_mfr_code tmc ON tmc.transmission_mfr_code_id = t.transmission_mfr_code_id
                    LEFT JOIN vcdb.vehicle_to_drive_type vtdt ON vtdt.vehicle_id = v.vehicle_id
                    LEFT JOIN vcdb.drive_type dt ON dt.drive_type_id = vtdt.drive_type_id
                """

                # Build WHERE clause based on filters
                where_clauses = []

                if filters.use_year_range and filters.year_range_start is not None and filters.year_range_end is not None:
                    where_clauses.append(f'y.year_id BETWEEN {filters.year_range_start} AND {filters.year_range_end}')
                elif filters.year_id is not None:
                    where_clauses.append(f'y.year_id = {filters.year_id}')

                if filters.make_id is not None:
                    where_clauses.append(f'm.make_id = {filters.make_id}')

                if filters.model_id is not None:
                    where_clauses.append(f'md.model_id = {filters.model_id}')

                if filters.submodel_id is not None:
                    where_clauses.append(f'sm.submodel_id = {filters.submodel_id}')

                if filters.engine_liter is not None:
                    where_clauses.append(f"eb.liter = '{filters.engine_liter}'")

                if filters.engine_cid is not None:
                    where_clauses.append(f"eb.cid = '{filters.engine_cid}'")

                if filters.cylinder_head_type_id is not None:
                    where_clauses.append(f'cht.cylinder_head_type_id = {filters.cylinder_head_type_id}')

                if filters.valves_id is not None:
                    where_clauses.append(f'val.valves_id = {filters.valves_id}')

                if filters.mfr_body_code_id is not None:
                    where_clauses.append(f'mbc.mfr_body_code_id = {filters.mfr_body_code_id}')

                if filters.body_num_doors_id is not None:
                    where_clauses.append(f'bnd.body_num_doors_id = {filters.body_num_doors_id}')

                if filters.wheel_base_id is not None:
                    where_clauses.append(f'wb.wheel_base_id = {filters.wheel_base_id}')

                if filters.brake_abs_id is not None:
                    where_clauses.append(f'ba.brake_abs_id = {filters.brake_abs_id}')

                if filters.steering_system_id is not None:
                    where_clauses.append(f'ss.steering_system_id = {filters.steering_system_id}')

                if filters.transmission_control_type_id is not None:
                    where_clauses.append(f'tct.transmission_control_type_id = {filters.transmission_control_type_id}')

                if filters.transmission_mfr_code_id is not None:
                    where_clauses.append(f'tmc.transmission_mfr_code_id = {filters.transmission_mfr_code_id}')

                if filters.drive_type_id is not None:
                    where_clauses.append(f'dt.drive_type_id = {filters.drive_type_id}')

                # Assemble the final query
                query = 'SELECT ' + ', '.join(select_columns) + from_clause

                if where_clauses:
                    query += ' WHERE ' + ' AND '.join(where_clauses)

                query += f' LIMIT {limit}'

                try:
                    result = await session.execute(text(query))
                    rows = result.fetchall()

                    vehicle_results = []
                    for row in rows:
                        row_dict = dict(row._mapping)
                        try:
                            vehicle_result = VehicleResultDTO(
                                vehicle_id=row_dict.get('vehicle_id'),
                                year=row_dict.get('year'),
                                make=row_dict.get('make'),
                                model=row_dict.get('model'),
                                submodel=row_dict.get('submodel'),
                                engine_liter=row_dict.get('engine_liter'),
                                engine_cylinders=row_dict.get('engine_cylinders'),
                                engine_block_type=row_dict.get('engine_block_type'),
                                engine_cc=row_dict.get('engine_cc'),
                                engine_cid=row_dict.get('engine_cid'),
                                cylinder_head_type=row_dict.get('cylinder_head_type'),
                                valves=row_dict.get('valves'),
                                mfr_body_code=row_dict.get('mfr_body_code'),
                                body_num_doors=row_dict.get('body_num_doors'),
                                wheel_base=row_dict.get('wheel_base'),
                                wheel_base_metric=row_dict.get('wheel_base_metric'),
                                brake_abs=row_dict.get('brake_abs'),
                                steering_system=row_dict.get('steering_system'),
                                transmission_control_type=row_dict.get('transmission_control_type'),
                                transmission_mfr_code=row_dict.get('transmission_mfr_code'),
                                drive_type=row_dict.get('drive_type')
                            )
                            vehicle_results.append(vehicle_result)
                        except ValidationError:
                            logger.warning(f'Skipping invalid row: {row_dict}')
                            continue

                    return vehicle_results
                except Exception as e:
                    logger.error('Error executing vehicle query', error=str(e))
                    raise QueryExecutionError(f'Error executing query: {str(e)}')

        except Exception as e:
            logger.error('Error executing vehicle query', error=str(e))
            raise QueryExecutionError(f'Error executing query: {str(e)}')