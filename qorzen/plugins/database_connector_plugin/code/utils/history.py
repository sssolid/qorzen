#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from typing import Any, Dict, List, Optional, Tuple, cast

from qorzen.utils.exceptions import DatabaseError

from ..models import (
    HistoryEntry,
    HistorySchedule,
    QueryResult,
    SavedQuery
)


class HistoryManager:
    """Manager for database history collection and storage."""

    def __init__(
            self,
            database_manager: Any,
            logger: Any,
            history_connection_id: Optional[str] = None
    ) -> None:
        """
        Initialize the history manager.

        Args:
            database_manager: Qorzen database manager instance
            logger: Logger instance
            history_connection_id: Database connection ID for history storage
        """
        self._db_manager = database_manager
        self._logger = logger
        self._history_connection_id = history_connection_id
        self._running_schedules: Dict[str, asyncio.Task] = {}

    async def initialize(self) -> None:
        """
        Initialize the history manager, creating necessary database tables.

        Raises:
            DatabaseError: If initialization fails
        """
        if not self._history_connection_id:
            self._logger.warning("No history database connection configured")
            return

        try:
            # Create history tables if they don't exist
            await self._create_history_tables()

            # Load and start all active schedules
            await self._load_and_start_schedules()

            self._logger.info("History manager initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize history manager: {str(e)}")
            raise DatabaseError(
                message=f"Failed to initialize history manager: {str(e)}",
                details={"original_error": str(e)}
            )

    async def _create_history_tables(self) -> None:
        """
        Create the necessary tables for storing history data.

        Raises:
            DatabaseError: If table creation fails
        """
        statements = [
            # Table for history schedules
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

            # Table for history entries
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

            # Table for storing the actual historical data
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

        try:
            for stmt in statements:
                await self._db_manager.execute_raw(
                    sql=stmt,
                    connection_name=self._history_connection_id
                )

            self._logger.debug("History tables created or already exist")
        except Exception as e:
            self._logger.error(f"Failed to create history tables: {str(e)}")
            raise DatabaseError(
                message=f"Failed to create history tables: {str(e)}",
                details={"original_error": str(e)}
            )

    async def _load_and_start_schedules(self) -> None:
        """
        Load all active schedules from the database and start them.

        Raises:
            DatabaseError: If loading schedules fails
        """
        try:
            # Fetch all active schedules
            results = await self._db_manager.execute_raw(
                sql="SELECT * FROM db_history_schedules WHERE active = TRUE",
                connection_name=self._history_connection_id
            )

            # Convert to HistorySchedule objects
            schedules: List[HistorySchedule] = []
            for row in results:
                schedule_dict = {
                    "id": row["id"],
                    "connection_id": row["connection_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "query_id": row["query_id"],
                    "frequency": row["frequency"],
                    "retention_days": row["retention_days"],
                    "active": row["active"],
                    "last_run": row["last_run"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                schedules.append(HistorySchedule(**schedule_dict))

            # Start each schedule
            for schedule in schedules:
                await self.start_schedule(schedule)

            self._logger.info(f"Started {len(schedules)} history collection schedules")
        except Exception as e:
            self._logger.error(f"Failed to load and start schedules: {str(e)}")
            raise DatabaseError(
                message=f"Failed to load and start schedules: {str(e)}",
                details={"original_error": str(e)}
            )

    async def create_schedule(
            self,
            schedule: HistorySchedule
    ) -> HistorySchedule:
        """
        Create a new history collection schedule.

        Args:
            schedule: History schedule to create

        Returns:
            Created schedule with updated ID

        Raises:
            DatabaseError: If schedule creation fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Insert the schedule into the database
            insert_sql = """
                         INSERT INTO db_history_schedules (id, connection_id, name, description, query_id, \
                                                           frequency, retention_days, active, created_at, updated_at) \
                         VALUES (:id, :connection_id, :name, :description, :query_id, \
                                 :frequency, :retention_days, :active, :created_at, :updated_at) \
                         """

            schedule_dict = schedule.dict()

            await self._db_manager.execute_raw(
                sql=insert_sql,
                params=schedule_dict,
                connection_name=self._history_connection_id
            )

            # Start the schedule if it's active
            if schedule.active:
                await self.start_schedule(schedule)

            self._logger.info(f"Created history schedule: {schedule.name}")
            return schedule

        except Exception as e:
            self._logger.error(f"Failed to create history schedule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to create history schedule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def update_schedule(
            self,
            schedule: HistorySchedule
    ) -> HistorySchedule:
        """
        Update an existing history collection schedule.

        Args:
            schedule: Updated history schedule

        Returns:
            Updated schedule

        Raises:
            DatabaseError: If schedule update fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Update the schedule in the database
            update_sql = """
                         UPDATE db_history_schedules \
                         SET connection_id  = :connection_id, \
                             name           = :name, \
                             description    = :description, \
                             query_id       = :query_id, \
                             frequency      = :frequency, \
                             retention_days = :retention_days, \
                             active         = :active, \
                             updated_at     = :updated_at
                         WHERE id = :id \
                         """

            # Update the timestamp
            schedule.updated_at = datetime.datetime.now()
            schedule_dict = schedule.dict()

            await self._db_manager.execute_raw(
                sql=update_sql,
                params=schedule_dict,
                connection_name=self._history_connection_id
            )

            # Stop the schedule if it's already running
            if schedule.id in self._running_schedules:
                await self.stop_schedule(schedule.id)

            # Start the schedule if it's active
            if schedule.active:
                await self.start_schedule(schedule)

            self._logger.info(f"Updated history schedule: {schedule.name}")
            return schedule

        except Exception as e:
            self._logger.error(f"Failed to update history schedule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to update history schedule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a history collection schedule.

        Args:
            schedule_id: ID of the schedule to delete

        Returns:
            True if the schedule was deleted

        Raises:
            DatabaseError: If schedule deletion fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Stop the schedule if it's running
            if schedule_id in self._running_schedules:
                await self.stop_schedule(schedule_id)

            # Delete the schedule from the database
            delete_sql = "DELETE FROM db_history_schedules WHERE id = :id"

            await self._db_manager.execute_raw(
                sql=delete_sql,
                params={"id": schedule_id},
                connection_name=self._history_connection_id
            )

            self._logger.info(f"Deleted history schedule: {schedule_id}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to delete history schedule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to delete history schedule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def get_schedule(self, schedule_id: str) -> Optional[HistorySchedule]:
        """
        Get a specific history collection schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            History schedule or None if not found

        Raises:
            DatabaseError: If fetching the schedule fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Fetch the schedule from the database
            results = await self._db_manager.execute_raw(
                sql="SELECT * FROM db_history_schedules WHERE id = :id",
                params={"id": schedule_id},
                connection_name=self._history_connection_id
            )

            if not results:
                return None

            # Convert to HistorySchedule
            row = results[0]
            schedule_dict = {
                "id": row["id"],
                "connection_id": row["connection_id"],
                "name": row["name"],
                "description": row["description"],
                "query_id": row["query_id"],
                "frequency": row["frequency"],
                "retention_days": row["retention_days"],
                "active": row["active"],
                "last_run": row["last_run"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

            return HistorySchedule(**schedule_dict)

        except Exception as e:
            self._logger.error(f"Failed to get history schedule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get history schedule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def get_all_schedules(self) -> List[HistorySchedule]:
        """
        Get all history collection schedules.

        Returns:
            List of history schedules

        Raises:
            DatabaseError: If fetching schedules fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Fetch all schedules from the database
            results = await self._db_manager.execute_raw(
                sql="SELECT * FROM db_history_schedules ORDER BY name",
                connection_name=self._history_connection_id
            )

            # Convert to HistorySchedule objects
            schedules: List[HistorySchedule] = []
            for row in results:
                schedule_dict = {
                    "id": row["id"],
                    "connection_id": row["connection_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "query_id": row["query_id"],
                    "frequency": row["frequency"],
                    "retention_days": row["retention_days"],
                    "active": row["active"],
                    "last_run": row["last_run"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                schedules.append(HistorySchedule(**schedule_dict))

            return schedules

        except Exception as e:
            self._logger.error(f"Failed to get history schedules: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get history schedules: {str(e)}",
                details={"original_error": str(e)}
            )

    async def start_schedule(self, schedule: HistorySchedule) -> None:
        """
        Start a history collection schedule.

        Args:
            schedule: History schedule to start

        Raises:
            DatabaseError: If starting the schedule fails
        """
        if schedule.id in self._running_schedules:
            # Already running
            return

        try:
            # Parse the frequency string (cron-like format)
            seconds = self._parse_frequency(schedule.frequency)
            if seconds is None:
                self._logger.error(
                    f"Invalid frequency format: {schedule.frequency}"
                )
                return

            # Create a task for this schedule
            task = asyncio.create_task(
                self._run_schedule(schedule.id, seconds)
            )

            self._running_schedules[schedule.id] = task
            self._logger.info(f"Started history schedule: {schedule.name}")

        except Exception as e:
            self._logger.error(f"Failed to start history schedule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to start history schedule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def stop_schedule(self, schedule_id: str) -> None:
        """
        Stop a running history collection schedule.

        Args:
            schedule_id: ID of the schedule to stop

        Raises:
            DatabaseError: If stopping the schedule fails
        """
        if schedule_id not in self._running_schedules:
            # Not running
            return

        try:
            # Cancel the task
            task = self._running_schedules[schedule_id]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            del self._running_schedules[schedule_id]
            self._logger.info(f"Stopped history schedule: {schedule_id}")

        except Exception as e:
            self._logger.error(f"Failed to stop history schedule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to stop history schedule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def execute_schedule_now(
            self,
            schedule_id: str,
            connector_manager: Any,
            saved_queries: Dict[str, SavedQuery]
    ) -> HistoryEntry:
        """
        Execute a history collection schedule immediately.

        Args:
            schedule_id: Schedule ID
            connector_manager: Database connector manager
            saved_queries: Dictionary of saved queries

        Returns:
            History entry for the executed schedule

        Raises:
            DatabaseError: If executing the schedule fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Get the schedule
            schedule = await self.get_schedule(schedule_id)
            if not schedule:
                raise DatabaseError(
                    message=f"Schedule not found: {schedule_id}",
                    details={}
                )

            # Get the saved query
            query = saved_queries.get(schedule.query_id)
            if not query:
                raise DatabaseError(
                    message=f"Query not found: {schedule.query_id}",
                    details={}
                )

            # Create a unique snapshot ID
            snapshot_id = str(uuid.uuid4())

            # Execute the query
            connector = await connector_manager.get_connector(schedule.connection_id)
            result = await connector.execute_query(query.query_text, query.parameters)

            # Store the results
            entry = await self._store_history_data(
                schedule=schedule,
                query=query,
                result=result,
                snapshot_id=snapshot_id
            )

            # Update the schedule's last_run timestamp
            update_sql = """
                         UPDATE db_history_schedules
                         SET last_run   = :last_run, \
                             updated_at = :updated_at
                         WHERE id = :id \
                         """

            now = datetime.datetime.now()
            await self._db_manager.execute_raw(
                sql=update_sql,
                params={
                    "id": schedule.id,
                    "last_run": now,
                    "updated_at": now
                },
                connection_name=self._history_connection_id
            )

            self._logger.info(
                f"Executed history schedule: {schedule.name}, "
                f"captured {result.row_count} records"
            )

            return entry

        except Exception as e:
            self._logger.error(f"Failed to execute history schedule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to execute history schedule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def get_history_entries(
            self,
            schedule_id: Optional[str] = None,
            limit: int = 100
    ) -> List[HistoryEntry]:
        """
        Get history entries, optionally filtered by schedule.

        Args:
            schedule_id: Optional schedule ID to filter by
            limit: Maximum number of entries to return

        Returns:
            List of history entries

        Raises:
            DatabaseError: If fetching entries fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Build the SQL query
            if schedule_id:
                sql = """
                      SELECT * \
                      FROM db_history_entries
                      WHERE schedule_id = :schedule_id
                      ORDER BY collected_at DESC LIMIT :limit \
                      """
                params = {"schedule_id": schedule_id, "limit": limit}
            else:
                sql = """
                      SELECT * \
                      FROM db_history_entries
                      ORDER BY collected_at DESC LIMIT :limit \
                      """
                params = {"limit": limit}

            # Execute the query
            results = await self._db_manager.execute_raw(
                sql=sql,
                params=params,
                connection_name=self._history_connection_id
            )

            # Convert to HistoryEntry objects
            entries: List[HistoryEntry] = []
            for row in results:
                entry_dict = {
                    "id": row["id"],
                    "schedule_id": row["schedule_id"],
                    "connection_id": row["connection_id"],
                    "query_id": row["query_id"],
                    "table_name": row["table_name"],
                    "collected_at": row["collected_at"],
                    "snapshot_id": row["snapshot_id"],
                    "record_count": row["record_count"],
                    "status": row["status"],
                    "error_message": row["error_message"]
                }
                entries.append(HistoryEntry(**entry_dict))

            return entries

        except Exception as e:
            self._logger.error(f"Failed to get history entries: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get history entries: {str(e)}",
                details={"original_error": str(e)}
            )

    async def get_history_data(
            self,
            snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical data for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with 'data', 'schema', and 'metadata' keys, or None if not found

        Raises:
            DatabaseError: If fetching data fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Fetch the history data
            data_results = await self._db_manager.execute_raw(
                sql="""
                    SELECT *
                    FROM db_history_data
                    WHERE snapshot_id = :snapshot_id
                    """,
                params={"snapshot_id": snapshot_id},
                connection_name=self._history_connection_id
            )

            if not data_results:
                return None

            # Fetch the entry metadata
            entry_results = await self._db_manager.execute_raw(
                sql="""
                    SELECT *
                    FROM db_history_entries
                    WHERE snapshot_id = :snapshot_id
                    """,
                params={"snapshot_id": snapshot_id},
                connection_name=self._history_connection_id
            )

            if not entry_results:
                return None

            # Parse the JSON data
            data_row = data_results[0]
            entry_row = entry_results[0]

            data_json = json.loads(data_row["data_json"])
            schema_json = json.loads(data_row["schema_json"])

            # Build the metadata
            metadata = {
                "snapshot_id": snapshot_id,
                "connection_id": entry_row["connection_id"],
                "query_id": entry_row["query_id"],
                "table_name": entry_row["table_name"],
                "collected_at": entry_row["collected_at"],
                "record_count": entry_row["record_count"]
            }

            return {
                "data": data_json,
                "schema": schema_json,
                "metadata": metadata
            }

        except Exception as e:
            self._logger.error(f"Failed to get history data: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get history data: {str(e)}",
                details={"original_error": str(e)}
            )

    async def delete_history_data(
            self,
            snapshot_id: str
    ) -> bool:
        """
        Delete historical data for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            True if the data was deleted

        Raises:
            DatabaseError: If deleting data fails
        """
        if not self._history_connection_id:
            raise DatabaseError(
                message="No history database connection configured",
                details={}
            )

        try:
            # Delete the data
            await self._db_manager.execute_raw(
                sql="DELETE FROM db_history_data WHERE snapshot_id = :snapshot_id",
                params={"snapshot_id": snapshot_id},
                connection_name=self._history_connection_id
            )

            # Delete the entry
            await self._db_manager.execute_raw(
                sql="DELETE FROM db_history_entries WHERE snapshot_id = :snapshot_id",
                params={"snapshot_id": snapshot_id},
                connection_name=self._history_connection_id
            )

            self._logger.info(f"Deleted history data for snapshot: {snapshot_id}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to delete history data: {str(e)}")
            raise DatabaseError(
                message=f"Failed to delete history data: {str(e)}",
                details={"original_error": str(e)}
            )

    async def _run_schedule(self, schedule_id: str, interval_seconds: int) -> None:
        """
        Background task to run a schedule at the specified interval.

        Args:
            schedule_id: Schedule ID
            interval_seconds: Interval in seconds
        """
        while True:
            try:
                # Get the current schedule (it might have been updated)
                schedule = await self.get_schedule(schedule_id)
                if not schedule or not schedule.active:
                    self._logger.info(f"Schedule {schedule_id} is no longer active")
                    break

                # Get the connector manager and saved queries
                # Note: In actual implementation, we'd need to pass these in from the plugin
                connector_manager = self._plugin.connector_manager
                saved_queries = self._plugin.get_saved_queries()

                # Execute the schedule
                await self.execute_schedule_now(
                    schedule_id=schedule_id,
                    connector_manager=connector_manager,
                    saved_queries=saved_queries
                )

                # Clean up old data based on retention policy
                await self._cleanup_old_data(schedule.id, schedule.retention_days)

            except asyncio.CancelledError:
                # Schedule was cancelled
                break

            except Exception as e:
                self._logger.error(
                    f"Error running history schedule {schedule_id}: {str(e)}"
                )

            # Wait for the next execution
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                # Schedule was cancelled during sleep
                break

    async def _store_history_data(
            self,
            schedule: HistorySchedule,
            query: SavedQuery,
            result: QueryResult,
            snapshot_id: str
    ) -> HistoryEntry:
        """
        Store the results of a history collection.

        Args:
            schedule: History schedule
            query: Saved query
            result: Query result
            snapshot_id: Snapshot ID

        Returns:
            History entry

        Raises:
            DatabaseError: If storing data fails
        """
        try:
            # Extract table name from the query if possible
            table_name = "unknown"
            import re
            match = re.search(r"FROM\s+(\w+)", result.query, re.IGNORECASE)
            if match:
                table_name = match.group(1)

            # Determine status
            status = "success"
            error_message = None
            if result.has_error:
                status = "error"
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

            # Insert the entry
            entry_sql = """
                        INSERT INTO db_history_entries (id, schedule_id, connection_id, query_id, table_name, \
                                                        collected_at, snapshot_id, record_count, status, error_message) \
                        VALUES (:id, :schedule_id, :connection_id, :query_id, :table_name, \
                                :collected_at, :snapshot_id, :record_count, :status, :error_message) \
                        """

            await self._db_manager.execute_raw(
                sql=entry_sql,
                params=entry.dict(),
                connection_name=self._history_connection_id
            )

            # Store the actual data and schema
            if status == "success" and result.records:
                # Convert data to JSON
                data_json = json.dumps(result.records)

                # Create a schema representation
                schema = []
                for col in result.columns:
                    schema.append({
                        "name": col.name,
                        "type_name": col.type_name,
                        "type_code": col.type_code,
                        "precision": col.precision,
                        "scale": col.scale,
                        "nullable": col.nullable
                    })
                schema_json = json.dumps(schema)

                # Insert the data
                data_sql = """
                           INSERT INTO db_history_data (id, snapshot_id, data_json, schema_json, created_at) \
                           VALUES (:id, :snapshot_id, :data_json, :schema_json, :created_at) \
                           """

                data_id = str(uuid.uuid4())
                await self._db_manager.execute_raw(
                    sql=data_sql,
                    params={
                        "id": data_id,
                        "snapshot_id": snapshot_id,
                        "data_json": data_json,
                        "schema_json": schema_json,
                        "created_at": datetime.datetime.now()
                    },
                    connection_name=self._history_connection_id
                )

            return entry

        except Exception as e:
            self._logger.error(f"Failed to store history data: {str(e)}")
            raise DatabaseError(
                message=f"Failed to store history data: {str(e)}",
                details={"original_error": str(e)}
            )

    async def _cleanup_old_data(
            self,
            schedule_id: str,
            retention_days: int
    ) -> None:
        """
        Clean up old history data based on retention policy.

        Args:
            schedule_id: Schedule ID
            retention_days: Number of days to retain data
        """
        if not self._history_connection_id:
            return

        try:
            # Calculate the cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)

            # Find snapshots to delete
            find_sql = """
                       SELECT snapshot_id \
                       FROM db_history_entries
                       WHERE schedule_id = :schedule_id \
                         AND collected_at < :cutoff_date \
                       """

            snapshots = await self._db_manager.execute_raw(
                sql=find_sql,
                params={
                    "schedule_id": schedule_id,
                    "cutoff_date": cutoff_date
                },
                connection_name=self._history_connection_id
            )

            if not snapshots:
                return

            # Delete each snapshot
            for row in snapshots:
                snapshot_id = row["snapshot_id"]
                await self.delete_history_data(snapshot_id)

            self._logger.info(
                f"Cleaned up {len(snapshots)} old history snapshots for schedule {schedule_id}"
            )

        except Exception as e:
            self._logger.error(f"Failed to clean up old history data: {str(e)}")

    def _parse_frequency(self, frequency: str) -> Optional[int]:
        """
        Parse a frequency string into seconds.

        Args:
            frequency: Frequency string (e.g., "1h", "30m", "1d")

        Returns:
            Interval in seconds, or None if invalid
        """
        # Simple format: number + unit (e.g., "1h", "30m", "1d")
        import re
        match = re.match(r"^(\d+)([smhdw])$", frequency.lower())

        if not match:
            return None

        value, unit = match.groups()
        value = int(value)

        # Convert to seconds
        if unit == "s":
            return value
        elif unit == "m":
            return value * 60
        elif unit == "h":
            return value * 60 * 60
        elif unit == "d":
            return value * 60 * 60 * 24
        elif unit == "w":
            return value * 60 * 60 * 24 * 7

        return None