from __future__ import annotations

"""
History tracking utilities for the Database Connector Plugin.

This module provides functionality for tracking and managing historical
database data, including scheduling periodic data collection and storing
the results for later reference.
"""
import asyncio
import datetime
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import sqlalchemy
from sqlalchemy import select, text

from qorzen.utils.exceptions import DatabaseError
from ..models import HistoryEntry, HistorySchedule, QueryResult, SavedQuery


class HistoryManager:
    """
    Manager for database history tracking functionality.

    This class provides methods for scheduling and managing historical data
    collection from database queries, allowing for point-in-time analysis
    and comparison of database contents.
    """

    def __init__(self, database_manager: Any, logger: Any, history_connection_id: Optional[str] = None) -> None:
        """
        Initialize the history manager.

        Args:
            database_manager: The database manager instance for executing SQL
            logger: The logger instance for recording history manager activity
            history_connection_id: Optional connection ID for storing history data
        """
        self._db_manager = database_manager
        self._logger = logger
        self._history_connection_id = history_connection_id
        self._running_schedules: Dict[str, asyncio.Task] = {}

    async def initialize(self) -> None:
        """
        Initialize the history manager by creating necessary tables.

        Raises:
            DatabaseError: If initialization fails
        """
        if not self._history_connection_id:
            self._logger.warning('No history database connection configured')
            return

        try:
            if not self._history_connection_id:
                raise DatabaseError(
                    message='No history database connection ID provided',
                    details={}
                )

            if not self._db_manager:
                raise DatabaseError(
                    message='No database manager available',
                    details={}
                )

            # Check if the connection exists
            if not await self._db_manager.has_connection(self._history_connection_id):
                raise DatabaseError(
                    message=f'Database connection {self._history_connection_id} not found',
                    details={'connection_id': self._history_connection_id}
                )

            await self._create_history_tables()
            await self._load_and_start_schedules()
            self._logger.info('History manager initialized')

        except Exception as e:
            self._logger.error(f'Failed to initialize history manager: {str(e)}')
            raise DatabaseError(
                message=f'Failed to initialize history manager: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def _create_history_tables(self) -> None:
        """
        Create tables needed for history tracking.

        Raises:
            DatabaseError: If table creation fails
        """
        statements = [
            """
            CREATE TABLE IF NOT EXISTS db_history_schedules
            (
                id
                VARCHAR
            (
                36
            ) PRIMARY KEY,
                connection_id VARCHAR
            (
                36
            ) NOT NULL,
                name VARCHAR
            (
                255
            ) NOT NULL,
                description TEXT,
                query_id VARCHAR
            (
                36
            ) NOT NULL,
                frequency VARCHAR
            (
                100
            ) NOT NULL,
                retention_days INTEGER NOT NULL DEFAULT 365,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                last_run TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """,
            """
            CREATE TABLE IF NOT EXISTS db_history_entries
            (
                id
                VARCHAR
            (
                36
            ) PRIMARY KEY,
                schedule_id VARCHAR
            (
                36
            ) NOT NULL,
                connection_id VARCHAR
            (
                36
            ) NOT NULL,
                query_id VARCHAR
            (
                36
            ) NOT NULL,
                table_name VARCHAR
            (
                255
            ) NOT NULL,
                collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                snapshot_id VARCHAR
            (
                36
            ) NOT NULL,
                record_count INTEGER NOT NULL DEFAULT 0,
                status VARCHAR
            (
                50
            ) NOT NULL DEFAULT 'success',
                error_message TEXT,
                FOREIGN KEY
            (
                schedule_id
            ) REFERENCES db_history_schedules
            (
                id
            ) ON DELETE CASCADE
                )
            """,
            """
            CREATE TABLE IF NOT EXISTS db_history_data
            (
                id
                VARCHAR
            (
                36
            ) PRIMARY KEY,
                snapshot_id VARCHAR
            (
                36
            ) NOT NULL,
                data_json TEXT NOT NULL,
                schema_json TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX
            (
                snapshot_id
            )
                )
            """
        ]

        max_retries = 3

        for attempt in range(max_retries):
            try:
                async with self._db_manager.async_session(self._history_connection_id) as session:
                    for stmt in statements:
                        self._logger.debug(f'Executing SQL: {stmt[:100]}...')
                        await session.execute(text(stmt))

                self._logger.debug('History tables created or already exist')
                return

            except Exception as e:
                self._logger.warning(f'Attempt {attempt + 1}/{max_retries} failed: {str(e)}')

                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    self._logger.error(f'Failed to create history tables after {max_retries} attempts: {str(e)}')
                    raise DatabaseError(
                        message=f'Failed to create history tables: {str(e)}',
                        details={'original_error': str(e)}
                    ) from e

    async def _load_and_start_schedules(self) -> None:
        """
        Load all active schedules and start them.

        Raises:
            DatabaseError: If loading or starting schedules fails
        """
        try:
            # Query all active schedules
            query = "SELECT * FROM db_history_schedules WHERE active = TRUE"
            results = await self._db_manager.execute_raw(
                sql=query,
                connection_name=self._history_connection_id
            )

            schedules: List[HistorySchedule] = []

            for row in results:
                # Convert row to HistorySchedule
                schedule_dict = {
                    'id': row['id'],
                    'connection_id': row['connection_id'],
                    'name': row['name'],
                    'description': row['description'],
                    'query_id': row['query_id'],
                    'frequency': row['frequency'],
                    'retention_days': row['retention_days'],
                    'active': row['active'],
                    'last_run': row['last_run'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                schedules.append(HistorySchedule(**schedule_dict))

            # Start each schedule
            for schedule in schedules:
                await self.start_schedule(schedule)

            self._logger.info(f'Started {len(schedules)} history collection schedules')

        except Exception as e:
            self._logger.error(f'Failed to load and start schedules: {str(e)}')
            raise DatabaseError(
                message=f'Failed to load and start schedules: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def create_schedule(self, schedule: HistorySchedule) -> HistorySchedule:
        """
        Create a new history collection schedule.

        Args:
            schedule: The schedule to create

        Returns:
            The created schedule

        Raises:
            DatabaseError: If schedule creation fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Insert the schedule into the database
            insert_sql = """
                         INSERT INTO db_history_schedules (id, connection_id, name, description, query_id,
                                                           frequency, retention_days, active, created_at, updated_at)
                         VALUES (:id, :connection_id, :name, :description, :query_id,
                                 :frequency, :retention_days, :active, :created_at, :updated_at) \
                         """
            schedule_dict = schedule.dict()

            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(insert_sql), schedule_dict)

            # Start the schedule if active
            if schedule.active:
                await self.start_schedule(schedule)

            self._logger.info(f'Created history schedule: {schedule.name}')
            return schedule

        except Exception as e:
            self._logger.error(f'Failed to create history schedule: {str(e)}')
            raise DatabaseError(
                message=f'Failed to create history schedule: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def update_schedule(self, schedule: HistorySchedule) -> HistorySchedule:
        """
        Update an existing history collection schedule.

        Args:
            schedule: The schedule to update

        Returns:
            The updated schedule

        Raises:
            DatabaseError: If schedule update fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Update the schedule in the database
            update_sql = """
                         UPDATE db_history_schedules
                         SET connection_id  = :connection_id,
                             name           = :name,
                             description    = :description,
                             query_id       = :query_id,
                             frequency      = :frequency,
                             retention_days = :retention_days,
                             active         = :active,
                             updated_at     = :updated_at
                         WHERE id = :id \
                         """
            schedule.updated_at = datetime.datetime.now()
            schedule_dict = schedule.dict()

            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(update_sql), schedule_dict)

            # Stop the schedule if it's running
            if schedule.id in self._running_schedules:
                await self.stop_schedule(schedule.id)

            # Start the schedule if active
            if schedule.active:
                await self.start_schedule(schedule)

            self._logger.info(f'Updated history schedule: {schedule.name}')
            return schedule

        except Exception as e:
            self._logger.error(f'Failed to update history schedule: {str(e)}')
            raise DatabaseError(
                message=f'Failed to update history schedule: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a history collection schedule.

        Args:
            schedule_id: ID of the schedule to delete

        Returns:
            True if successful

        Raises:
            DatabaseError: If schedule deletion fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Stop the schedule if it's running
            if schedule_id in self._running_schedules:
                await self.stop_schedule(schedule_id)

            # Delete the schedule from the database
            delete_sql = "DELETE FROM db_history_schedules WHERE id = :id"

            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(delete_sql), {"id": schedule_id})

            self._logger.info(f'Deleted history schedule: {schedule_id}')
            return True

        except Exception as e:
            self._logger.error(f'Failed to delete history schedule: {str(e)}')
            raise DatabaseError(
                message=f'Failed to delete history schedule: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def get_schedule(self, schedule_id: str) -> Optional[HistorySchedule]:
        """
        Get a history collection schedule by ID.

        Args:
            schedule_id: ID of the schedule to retrieve

        Returns:
            The schedule if found, None otherwise

        Raises:
            DatabaseError: If retrieving the schedule fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Query the schedule from the database
            query = "SELECT * FROM db_history_schedules WHERE id = :id"

            async with self._db_manager.async_session(self._history_connection_id) as session:
                result = await session.execute(text(query), {"id": schedule_id})
                row = result.fetchone()

            if not row:
                return None

            # Convert row to HistorySchedule
            schedule_dict = {
                'id': row[0],
                'connection_id': row[1],
                'name': row[2],
                'description': row[3],
                'query_id': row[4],
                'frequency': row[5],
                'retention_days': row[6],
                'active': row[7],
                'last_run': row[8],
                'created_at': row[9],
                'updated_at': row[10]
            }

            return HistorySchedule(**schedule_dict)

        except Exception as e:
            self._logger.error(f'Failed to get history schedule: {str(e)}')
            raise DatabaseError(
                message=f'Failed to get history schedule: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def get_all_schedules(self) -> List[HistorySchedule]:
        """
        Get all history collection schedules.

        Returns:
            List of all schedules

        Raises:
            DatabaseError: If retrieving schedules fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Query all schedules from the database
            query = "SELECT * FROM db_history_schedules ORDER BY name"

            async with self._db_manager.async_session(self._history_connection_id) as session:
                result = await session.execute(text(query))
                rows = result.fetchall()

            schedules: List[HistorySchedule] = []

            for row in rows:
                # Convert row to HistorySchedule
                schedule_dict = {
                    'id': row[0],
                    'connection_id': row[1],
                    'name': row[2],
                    'description': row[3],
                    'query_id': row[4],
                    'frequency': row[5],
                    'retention_days': row[6],
                    'active': row[7],
                    'last_run': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                }
                schedules.append(HistorySchedule(**schedule_dict))

            return schedules

        except Exception as e:
            self._logger.error(f'Failed to get history schedules: {str(e)}')
            raise DatabaseError(
                message=f'Failed to get history schedules: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def start_schedule(self, schedule: HistorySchedule) -> None:
        """
        Start a history collection schedule.

        Args:
            schedule: The schedule to start

        Raises:
            DatabaseError: If starting the schedule fails
        """
        # Skip if already running
        if schedule.id in self._running_schedules:
            return

        try:
            # Parse frequency to seconds
            seconds = self._parse_frequency(schedule.frequency)

            if seconds is None:
                self._logger.error(f'Invalid frequency format: {schedule.frequency}')
                return

            # Create task to run the schedule
            task = asyncio.create_task(self._run_schedule(schedule.id, seconds))
            self._running_schedules[schedule.id] = task

            self._logger.info(f'Started history schedule: {schedule.name}')

        except Exception as e:
            self._logger.error(f'Failed to start history schedule: {str(e)}')
            raise DatabaseError(
                message=f'Failed to start history schedule: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def stop_schedule(self, schedule_id: str) -> None:
        """
        Stop a running history collection schedule.

        Args:
            schedule_id: ID of the schedule to stop

        Raises:
            DatabaseError: If stopping the schedule fails
        """
        # Skip if not running
        if schedule_id not in self._running_schedules:
            return

        try:
            # Cancel the task
            task = self._running_schedules[schedule_id]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Remove from running schedules
            del self._running_schedules[schedule_id]

            self._logger.info(f'Stopped history schedule: {schedule_id}')

        except Exception as e:
            self._logger.error(f'Failed to stop history schedule: {str(e)}')
            raise DatabaseError(
                message=f'Failed to stop history schedule: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def execute_schedule_now(
            self,
            schedule_id: str,
            connector_manager: Any,
            saved_queries: Dict[str, SavedQuery]
    ) -> HistoryEntry:
        """
        Execute a schedule immediately.

        Args:
            schedule_id: ID of the schedule to execute
            connector_manager: The database connector manager
            saved_queries: Dictionary of saved queries

        Returns:
            The history entry created

        Raises:
            DatabaseError: If execution fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Get the schedule
            schedule = await self.get_schedule(schedule_id)

            if not schedule:
                raise DatabaseError(
                    message=f'Schedule not found: {schedule_id}',
                    details={}
                )

            # Get the query
            query = saved_queries.get(schedule.query_id)

            if not query:
                raise DatabaseError(
                    message=f'Query not found: {schedule.query_id}',
                    details={}
                )

            # Generate a snapshot ID
            snapshot_id = str(uuid.uuid4())

            # Get the connector
            connector = await connector_manager.get_connector(schedule.connection_id)

            # Execute the query
            result = await connector.execute_query(query.query_text, query.parameters)

            # Store the result
            entry = await self._store_history_data(
                schedule=schedule,
                query=query,
                result=result,
                snapshot_id=snapshot_id
            )

            # Update the last run time
            update_sql = """
                         UPDATE db_history_schedules
                         SET last_run   = :last_run,
                             updated_at = :updated_at
                         WHERE id = :id \
                         """
            now = datetime.datetime.now()

            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(
                    text(update_sql),
                    {"id": schedule.id, "last_run": now, "updated_at": now}
                )

            self._logger.info(
                f'Executed history schedule: {schedule.name}, captured {result.row_count} records'
            )

            return entry

        except Exception as e:
            self._logger.error(f'Failed to execute history schedule: {str(e)}')
            raise DatabaseError(
                message=f'Failed to execute history schedule: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def get_history_entries(
            self,
            schedule_id: Optional[str] = None,
            limit: int = 100
    ) -> List[HistoryEntry]:
        """
        Get history entries, optionally filtered by schedule ID.

        Args:
            schedule_id: Optional ID of the schedule to filter by
            limit: Maximum number of entries to return

        Returns:
            List of history entries

        Raises:
            DatabaseError: If retrieving entries fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Build the query
            if schedule_id:
                sql = """
                      SELECT *
                      FROM db_history_entries
                      WHERE schedule_id = :schedule_id
                      ORDER BY collected_at DESC LIMIT :limit \
                      """
                params = {"schedule_id": schedule_id, "limit": limit}
            else:
                sql = """
                      SELECT *
                      FROM db_history_entries
                      ORDER BY collected_at DESC LIMIT :limit \
                      """
                params = {"limit": limit}

            # Execute the query
            async with self._db_manager.async_session(self._history_connection_id) as session:
                result = await session.execute(text(sql), params)
                rows = result.fetchall()

            entries: List[HistoryEntry] = []

            for row in rows:
                # Convert row to HistoryEntry
                entry_dict = {
                    'id': row[0],
                    'schedule_id': row[1],
                    'connection_id': row[2],
                    'query_id': row[3],
                    'table_name': row[4],
                    'collected_at': row[5],
                    'snapshot_id': row[6],
                    'record_count': row[7],
                    'status': row[8],
                    'error_message': row[9]
                }
                entries.append(HistoryEntry(**entry_dict))

            return entries

        except Exception as e:
            self._logger.error(f'Failed to get history entries: {str(e)}')
            raise DatabaseError(
                message=f'Failed to get history entries: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def get_history_data(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get historical data for a specific snapshot.

        Args:
            snapshot_id: ID of the snapshot to retrieve

        Returns:
            Dictionary containing the data, schema, and metadata

        Raises:
            DatabaseError: If retrieving data fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Query the data
            data_sql = """
                       SELECT *
                       FROM db_history_data
                       WHERE snapshot_id = :snapshot_id \
                       """

            # Query the entry metadata
            entry_sql = """
                        SELECT *
                        FROM db_history_entries
                        WHERE snapshot_id = :snapshot_id \
                        """

            # Execute both queries
            async with self._db_manager.async_session(self._history_connection_id) as session:
                data_result = await session.execute(text(data_sql), {"snapshot_id": snapshot_id})
                data_row = data_result.fetchone()

                entry_result = await session.execute(text(entry_sql), {"snapshot_id": snapshot_id})
                entry_row = entry_result.fetchone()

            # Return None if either query returns no results
            if not data_row or not entry_row:
                return None

            # Parse the JSON data
            data_json = json.loads(data_row[2])
            schema_json = json.loads(data_row[3])

            # Build the metadata
            metadata = {
                'snapshot_id': snapshot_id,
                'connection_id': entry_row[2],
                'query_id': entry_row[3],
                'table_name': entry_row[4],
                'collected_at': entry_row[5],
                'record_count': entry_row[7]
            }

            # Return the complete data package
            return {
                'data': data_json,
                'schema': schema_json,
                'metadata': metadata
            }

        except Exception as e:
            self._logger.error(f'Failed to get history data: {str(e)}')
            raise DatabaseError(
                message=f'Failed to get history data: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def delete_history_data(self, snapshot_id: str) -> bool:
        """
        Delete historical data for a specific snapshot.

        Args:
            snapshot_id: ID of the snapshot to delete

        Returns:
            True if successful

        Raises:
            DatabaseError: If deletion fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message='No history database connection configured',
                details={}
            )

        try:
            # Delete the data and entry
            async with self._db_manager.async_session(self._history_connection_id) as session:
                # Delete the data
                await session.execute(
                    text("DELETE FROM db_history_data WHERE snapshot_id = :snapshot_id"),
                    {"snapshot_id": snapshot_id}
                )

                # Delete the entry
                await session.execute(
                    text("DELETE FROM db_history_entries WHERE snapshot_id = :snapshot_id"),
                    {"snapshot_id": snapshot_id}
                )

            self._logger.info(f'Deleted history data for snapshot: {snapshot_id}')
            return True

        except Exception as e:
            self._logger.error(f'Failed to delete history data: {str(e)}')
            raise DatabaseError(
                message=f'Failed to delete history data: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def _run_schedule(self, schedule_id: str, interval_seconds: int) -> None:
        """
        Run a schedule at regular intervals.

        Args:
            schedule_id: ID of the schedule to run
            interval_seconds: Interval between runs in seconds
        """
        while True:
            try:
                # Get the schedule
                schedule = await self.get_schedule(schedule_id)

                # Stop if the schedule is no longer active
                if not schedule or not schedule.active:
                    self._logger.info(f'Schedule {schedule_id} is no longer active')
                    break

                # Execute the schedule
                connector_manager = self._plugin.connector_manager
                saved_queries = self._plugin.get_saved_queries()

                await self.execute_schedule_now(
                    schedule_id=schedule_id,
                    connector_manager=connector_manager,
                    saved_queries=saved_queries
                )

                # Clean up old data
                await self._cleanup_old_data(schedule.id, schedule.retention_days)

            except asyncio.CancelledError:
                # Exit the loop if the task is cancelled
                break

            except Exception as e:
                self._logger.error(f'Error running history schedule {schedule_id}: {str(e)}')

            try:
                # Wait for the next interval
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                # Exit the loop if the task is cancelled during sleep
                break

    async def _store_history_data(
            self,
            schedule: HistorySchedule,
            query: SavedQuery,
            result: QueryResult,
            snapshot_id: str
    ) -> HistoryEntry:
        """
        Store historical data from a query result.

        Args:
            schedule: The schedule that generated the data
            query: The query that was executed
            result: The query result
            snapshot_id: The snapshot ID

        Returns:
            The history entry created

        Raises:
            DatabaseError: If storing data fails
        """
        try:
            # Extract table name from query
            table_name = 'unknown'
            import re
            match = re.search(r'FROM\s+(\w+)', result.query, re.IGNORECASE)

            if match:
                table_name = match.group(1)

            # Determine status and error message
            status = 'success'
            error_message = None

            if result.has_error:
                status = 'error'
                error_message = result.error_message

            # Create the history entry
            entry = HistoryEntry(
                schedule_id=schedule.id,
                connection_id=schedule.connection_id,
                query_id=schedule.query_id,
                table_name=table_name,
                collected_at=datetime.datetime.now(),
                snapshot_id=snapshot_id,
                record_count=result.row_count,
                status=status,
                error_message=error_message
            )

            # Insert the entry into the database
            entry_sql = """
                        INSERT INTO db_history_entries (id, schedule_id, connection_id, query_id, table_name,
                                                        collected_at, snapshot_id, record_count, status, error_message)
                        VALUES (:id, :schedule_id, :connection_id, :query_id, :table_name,
                                :collected_at, :snapshot_id, :record_count, :status, :error_message)
                        """

            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(entry_sql), entry.dict())

            # Store the data if successful
            if status == 'success' and result.records:
                # Convert records to JSON
                data_json = json.dumps(result.records)

                # Create schema JSON
                schema = []

                for col in result.columns:
                    schema.append({
                        'name': col.name,
                        'type_name': col.type_name,
                        'type_code': col.type_code,
                        'precision': col.precision,
                        'scale': col.scale,
                        'nullable': col.nullable
                    })

                schema_json = json.dumps(schema)

                # Insert the data
                data_sql = """
                           INSERT INTO db_history_data (id, snapshot_id, data_json, schema_json, created_at)
                           VALUES (:id, :snapshot_id, :data_json, :schema_json, :created_at)
                           """

                data_id = str(uuid.uuid4())

                async with self._db_manager.async_session(self._history_connection_id) as session:
                    await session.execute(
                        text(data_sql),
                        {
                            'id': data_id,
                            'snapshot_id': snapshot_id,
                            'data_json': data_json,
                            'schema_json': schema_json,
                            'created_at': datetime.datetime.now()
                        }
                    )

            return entry

        except Exception as e:
            self._logger.error(f'Failed to store history data: {str(e)}')
            raise DatabaseError(
                message=f'Failed to store history data: {str(e)}',
                details={'original_error': str(e)}
            ) from e

    async def _cleanup_old_data(self, schedule_id: str, retention_days: int) -> None:
        """
        Clean up historical data older than the retention period.

        Args:
            schedule_id: ID of the schedule to clean up
            retention_days: Number of days to retain data
        """
        if not self._history_connection_id:
            return

        try:
            # Calculate cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)

            # Find snapshots to delete
            find_sql = """
                       SELECT snapshot_id
                       FROM db_history_entries
                       WHERE schedule_id = :schedule_id
                         AND collected_at < :cutoff_date \
                       """

            async with self._db_manager.async_session(self._history_connection_id) as session:
                result = await session.execute(
                    text(find_sql),
                    {"schedule_id": schedule_id, "cutoff_date": cutoff_date}
                )
                snapshots = result.fetchall()

            # Delete each snapshot
            for row in snapshots:
                snapshot_id = row[0]
                await self.delete_history_data(snapshot_id)

            self._logger.info(
                f'Cleaned up {len(snapshots)} old history snapshots for schedule {schedule_id}'
            )

        except Exception as e:
            self._logger.error(f'Failed to clean up old history data: {str(e)}')

    def _parse_frequency(self, frequency: str) -> Optional[int]:
        """
        Parse a frequency string to seconds.

        Args:
            frequency: Frequency string (e.g., "5m", "1h", "1d")

        Returns:
            Number of seconds, or None if invalid
        """
        import re
        match = re.match(r'^(\d+)([smhdw])$', frequency.lower())

        if not match:
            return None

        value, unit = match.groups()
        value = int(value)

        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 60 * 60
        elif unit == 'd':
            return value * 60 * 60 * 24
        elif unit == 'w':
            return value * 60 * 60 * 24 * 7

        return None