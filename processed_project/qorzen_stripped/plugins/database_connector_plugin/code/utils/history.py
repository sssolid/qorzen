from __future__ import annotations
'\nHistory tracking utilities for the Database Connector Plugin.\n\nThis module provides functionality for tracking and managing historical\ndatabase data, including scheduling periodic data collection and storing\nthe results for later reference.\n'
import asyncio
import datetime
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple, cast
from qorzen.utils.exceptions import DatabaseError
from ..models import HistoryEntry, HistorySchedule, QueryResult, SavedQuery
class HistoryManager:
    def __init__(self, database_manager: Any, logger: Any, history_connection_id: Optional[str]=None) -> None:
        self._db_manager = database_manager
        self._logger = logger
        self._history_connection_id = history_connection_id
        self._running_schedules: Dict[str, asyncio.Task] = {}
    async def initialize(self) -> None:
        if not self._history_connection_id:
            self._logger.warning('No history database connection configured')
            return
        try:
            await self._create_history_tables()
            await self._load_and_start_schedules()
            self._logger.info('History manager initialized')
        except Exception as e:
            self._logger.error(f'Failed to initialize history manager: {str(e)}')
            raise DatabaseError(message=f'Failed to initialize history manager: {str(e)}', details={'original_error': str(e)})
    async def _create_history_tables(self) -> None:
        statements = ['\n            CREATE TABLE IF NOT EXISTS db_history_schedules\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                description TEXT,\n                query_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                frequency VARCHAR\n            (\n                100\n            ) NOT NULL,\n                retention_days INTEGER NOT NULL DEFAULT 365,\n                active BOOLEAN NOT NULL DEFAULT TRUE,\n                last_run TIMESTAMP,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n                )\n            ', "\n            CREATE TABLE IF NOT EXISTS db_history_entries\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                schedule_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                query_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                table_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                snapshot_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                record_count INTEGER NOT NULL DEFAULT 0,\n                status VARCHAR\n            (\n                50\n            ) NOT NULL DEFAULT 'success',\n                error_message TEXT,\n                FOREIGN KEY\n            (\n                schedule_id\n            ) REFERENCES db_history_schedules\n            (\n                id\n            ) ON DELETE CASCADE\n                )\n            ", '\n            CREATE TABLE IF NOT EXISTS db_history_data\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                snapshot_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                data_json TEXT NOT NULL,\n                schema_json TEXT NOT NULL,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                INDEX\n            (\n                snapshot_id\n            )\n                )\n            ']
        try:
            for stmt in statements:
                await self._db_manager.execute_raw(sql=stmt, connection_name=self._history_connection_id)
            self._logger.debug('History tables created or already exist')
        except Exception as e:
            self._logger.error(f'Failed to create history tables: {str(e)}')
            raise DatabaseError(message=f'Failed to create history tables: {str(e)}', details={'original_error': str(e)})
    async def _load_and_start_schedules(self) -> None:
        try:
            results = await self._db_manager.execute_raw(sql='SELECT * FROM db_history_schedules WHERE active = TRUE', connection_name=self._history_connection_id)
            schedules: List[HistorySchedule] = []
            for row in results:
                schedule_dict = {'id': row['id'], 'connection_id': row['connection_id'], 'name': row['name'], 'description': row['description'], 'query_id': row['query_id'], 'frequency': row['frequency'], 'retention_days': row['retention_days'], 'active': row['active'], 'last_run': row['last_run'], 'created_at': row['created_at'], 'updated_at': row['updated_at']}
                schedules.append(HistorySchedule(**schedule_dict))
            for schedule in schedules:
                await self.start_schedule(schedule)
            self._logger.info(f'Started {len(schedules)} history collection schedules')
        except Exception as e:
            self._logger.error(f'Failed to load and start schedules: {str(e)}')
            raise DatabaseError(message=f'Failed to load and start schedules: {str(e)}', details={'original_error': str(e)})
    async def create_schedule(self, schedule: HistorySchedule) -> HistorySchedule:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            insert_sql = '\n                         INSERT INTO db_history_schedules (id, connection_id, name, description, query_id,                                                            frequency, retention_days, active, created_at, updated_at)                          VALUES (:id, :connection_id, :name, :description, :query_id,                                  :frequency, :retention_days, :active, :created_at, :updated_at)                          '
            schedule_dict = schedule.dict()
            await self._db_manager.execute_raw(sql=insert_sql, params=schedule_dict, connection_name=self._history_connection_id)
            if schedule.active:
                await self.start_schedule(schedule)
            self._logger.info(f'Created history schedule: {schedule.name}')
            return schedule
        except Exception as e:
            self._logger.error(f'Failed to create history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to create history schedule: {str(e)}', details={'original_error': str(e)})
    async def update_schedule(self, schedule: HistorySchedule) -> HistorySchedule:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            update_sql = '\n                         UPDATE db_history_schedules                          SET connection_id  = :connection_id,                              name           = :name,                              description    = :description,                              query_id       = :query_id,                              frequency      = :frequency,                              retention_days = :retention_days,                              active         = :active,                              updated_at     = :updated_at\n                         WHERE id = :id                          '
            schedule.updated_at = datetime.datetime.now()
            schedule_dict = schedule.dict()
            await self._db_manager.execute_raw(sql=update_sql, params=schedule_dict, connection_name=self._history_connection_id)
            if schedule.id in self._running_schedules:
                await self.stop_schedule(schedule.id)
            if schedule.active:
                await self.start_schedule(schedule)
            self._logger.info(f'Updated history schedule: {schedule.name}')
            return schedule
        except Exception as e:
            self._logger.error(f'Failed to update history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to update history schedule: {str(e)}', details={'original_error': str(e)})
    async def delete_schedule(self, schedule_id: str) -> bool:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            if schedule_id in self._running_schedules:
                await self.stop_schedule(schedule_id)
            delete_sql = 'DELETE FROM db_history_schedules WHERE id = :id'
            await self._db_manager.execute_raw(sql=delete_sql, params={'id': schedule_id}, connection_name=self._history_connection_id)
            self._logger.info(f'Deleted history schedule: {schedule_id}')
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to delete history schedule: {str(e)}', details={'original_error': str(e)})
    async def get_schedule(self, schedule_id: str) -> Optional[HistorySchedule]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            results = await self._db_manager.execute_raw(sql='SELECT * FROM db_history_schedules WHERE id = :id', params={'id': schedule_id}, connection_name=self._history_connection_id)
            if not results:
                return None
            row = results[0]
            schedule_dict = {'id': row['id'], 'connection_id': row['connection_id'], 'name': row['name'], 'description': row['description'], 'query_id': row['query_id'], 'frequency': row['frequency'], 'retention_days': row['retention_days'], 'active': row['active'], 'last_run': row['last_run'], 'created_at': row['created_at'], 'updated_at': row['updated_at']}
            return HistorySchedule(**schedule_dict)
        except Exception as e:
            self._logger.error(f'Failed to get history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to get history schedule: {str(e)}', details={'original_error': str(e)})
    async def get_all_schedules(self) -> List[HistorySchedule]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            results = await self._db_manager.execute_raw(sql='SELECT * FROM db_history_schedules ORDER BY name', connection_name=self._history_connection_id)
            schedules: List[HistorySchedule] = []
            for row in results:
                schedule_dict = {'id': row['id'], 'connection_id': row['connection_id'], 'name': row['name'], 'description': row['description'], 'query_id': row['query_id'], 'frequency': row['frequency'], 'retention_days': row['retention_days'], 'active': row['active'], 'last_run': row['last_run'], 'created_at': row['created_at'], 'updated_at': row['updated_at']}
                schedules.append(HistorySchedule(**schedule_dict))
            return schedules
        except Exception as e:
            self._logger.error(f'Failed to get history schedules: {str(e)}')
            raise DatabaseError(message=f'Failed to get history schedules: {str(e)}', details={'original_error': str(e)})
    async def start_schedule(self, schedule: HistorySchedule) -> None:
        if schedule.id in self._running_schedules:
            return
        try:
            seconds = self._parse_frequency(schedule.frequency)
            if seconds is None:
                self._logger.error(f'Invalid frequency format: {schedule.frequency}')
                return
            task = asyncio.create_task(self._run_schedule(schedule.id, seconds))
            self._running_schedules[schedule.id] = task
            self._logger.info(f'Started history schedule: {schedule.name}')
        except Exception as e:
            self._logger.error(f'Failed to start history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to start history schedule: {str(e)}', details={'original_error': str(e)})
    async def stop_schedule(self, schedule_id: str) -> None:
        if schedule_id not in self._running_schedules:
            return
        try:
            task = self._running_schedules[schedule_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._running_schedules[schedule_id]
            self._logger.info(f'Stopped history schedule: {schedule_id}')
        except Exception as e:
            self._logger.error(f'Failed to stop history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to stop history schedule: {str(e)}', details={'original_error': str(e)})
    async def execute_schedule_now(self, schedule_id: str, connector_manager: Any, saved_queries: Dict[str, SavedQuery]) -> HistoryEntry:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            schedule = await self.get_schedule(schedule_id)
            if not schedule:
                raise DatabaseError(message=f'Schedule not found: {schedule_id}', details={})
            query = saved_queries.get(schedule.query_id)
            if not query:
                raise DatabaseError(message=f'Query not found: {schedule.query_id}', details={})
            snapshot_id = str(uuid.uuid4())
            connector = await connector_manager.get_connector(schedule.connection_id)
            result = await connector.execute_query(query.query_text, query.parameters)
            entry = await self._store_history_data(schedule=schedule, query=query, result=result, snapshot_id=snapshot_id)
            update_sql = '\n                         UPDATE db_history_schedules\n                         SET last_run   = :last_run,                              updated_at = :updated_at\n                         WHERE id = :id                          '
            now = datetime.datetime.now()
            await self._db_manager.execute_raw(sql=update_sql, params={'id': schedule.id, 'last_run': now, 'updated_at': now}, connection_name=self._history_connection_id)
            self._logger.info(f'Executed history schedule: {schedule.name}, captured {result.row_count} records')
            return entry
        except Exception as e:
            self._logger.error(f'Failed to execute history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to execute history schedule: {str(e)}', details={'original_error': str(e)})
    async def get_history_entries(self, schedule_id: Optional[str]=None, limit: int=100) -> List[HistoryEntry]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            if schedule_id:
                sql = '\n                      SELECT *                       FROM db_history_entries\n                      WHERE schedule_id = :schedule_id\n                      ORDER BY collected_at DESC LIMIT :limit                       '
                params = {'schedule_id': schedule_id, 'limit': limit}
            else:
                sql = '\n                      SELECT *                       FROM db_history_entries\n                      ORDER BY collected_at DESC LIMIT :limit                       '
                params = {'limit': limit}
            results = await self._db_manager.execute_raw(sql=sql, params=params, connection_name=self._history_connection_id)
            entries: List[HistoryEntry] = []
            for row in results:
                entry_dict = {'id': row['id'], 'schedule_id': row['schedule_id'], 'connection_id': row['connection_id'], 'query_id': row['query_id'], 'table_name': row['table_name'], 'collected_at': row['collected_at'], 'snapshot_id': row['snapshot_id'], 'record_count': row['record_count'], 'status': row['status'], 'error_message': row['error_message']}
                entries.append(HistoryEntry(**entry_dict))
            return entries
        except Exception as e:
            self._logger.error(f'Failed to get history entries: {str(e)}')
            raise DatabaseError(message=f'Failed to get history entries: {str(e)}', details={'original_error': str(e)})
    async def get_history_data(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            data_results = await self._db_manager.execute_raw(sql='\n                    SELECT *\n                    FROM db_history_data\n                    WHERE snapshot_id = :snapshot_id\n                    ', params={'snapshot_id': snapshot_id}, connection_name=self._history_connection_id)
            if not data_results:
                return None
            entry_results = await self._db_manager.execute_raw(sql='\n                    SELECT *\n                    FROM db_history_entries\n                    WHERE snapshot_id = :snapshot_id\n                    ', params={'snapshot_id': snapshot_id}, connection_name=self._history_connection_id)
            if not entry_results:
                return None
            data_row = data_results[0]
            entry_row = entry_results[0]
            data_json = json.loads(data_row['data_json'])
            schema_json = json.loads(data_row['schema_json'])
            metadata = {'snapshot_id': snapshot_id, 'connection_id': entry_row['connection_id'], 'query_id': entry_row['query_id'], 'table_name': entry_row['table_name'], 'collected_at': entry_row['collected_at'], 'record_count': entry_row['record_count']}
            return {'data': data_json, 'schema': schema_json, 'metadata': metadata}
        except Exception as e:
            self._logger.error(f'Failed to get history data: {str(e)}')
            raise DatabaseError(message=f'Failed to get history data: {str(e)}', details={'original_error': str(e)})
    async def delete_history_data(self, snapshot_id: str) -> bool:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            await self._db_manager.execute_raw(sql='DELETE FROM db_history_data WHERE snapshot_id = :snapshot_id', params={'snapshot_id': snapshot_id}, connection_name=self._history_connection_id)
            await self._db_manager.execute_raw(sql='DELETE FROM db_history_entries WHERE snapshot_id = :snapshot_id', params={'snapshot_id': snapshot_id}, connection_name=self._history_connection_id)
            self._logger.info(f'Deleted history data for snapshot: {snapshot_id}')
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete history data: {str(e)}')
            raise DatabaseError(message=f'Failed to delete history data: {str(e)}', details={'original_error': str(e)})
    async def _run_schedule(self, schedule_id: str, interval_seconds: int) -> None:
        while True:
            try:
                schedule = await self.get_schedule(schedule_id)
                if not schedule or not schedule.active:
                    self._logger.info(f'Schedule {schedule_id} is no longer active')
                    break
                connector_manager = self._plugin.connector_manager
                saved_queries = self._plugin.get_saved_queries()
                await self.execute_schedule_now(schedule_id=schedule_id, connector_manager=connector_manager, saved_queries=saved_queries)
                await self._cleanup_old_data(schedule.id, schedule.retention_days)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f'Error running history schedule {schedule_id}: {str(e)}')
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
    async def _store_history_data(self, schedule: HistorySchedule, query: SavedQuery, result: QueryResult, snapshot_id: str) -> HistoryEntry:
        try:
            table_name = 'unknown'
            import re
            match = re.search('FROM\\s+(\\w+)', result.query, re.IGNORECASE)
            if match:
                table_name = match.group(1)
            status = 'success'
            error_message = None
            if result.has_error:
                status = 'error'
                error_message = result.error_message
            entry = HistoryEntry(schedule_id=schedule.id, connection_id=schedule.connection_id, query_id=schedule.query_id, table_name=table_name, collected_at=datetime.datetime.now(), snapshot_id=snapshot_id, record_count=result.row_count, status=status, error_message=error_message)
            entry_sql = '\n                        INSERT INTO db_history_entries (id, schedule_id, connection_id, query_id, table_name,                                                         collected_at, snapshot_id, record_count, status, error_message)                         VALUES (:id, :schedule_id, :connection_id, :query_id, :table_name,                                 :collected_at, :snapshot_id, :record_count, :status, :error_message)                         '
            await self._db_manager.execute_raw(sql=entry_sql, params=entry.dict(), connection_name=self._history_connection_id)
            if status == 'success' and result.records:
                data_json = json.dumps(result.records)
                schema = []
                for col in result.columns:
                    schema.append({'name': col.name, 'type_name': col.type_name, 'type_code': col.type_code, 'precision': col.precision, 'scale': col.scale, 'nullable': col.nullable})
                schema_json = json.dumps(schema)
                data_sql = '\n                           INSERT INTO db_history_data (id, snapshot_id, data_json, schema_json, created_at)                            VALUES (:id, :snapshot_id, :data_json, :schema_json, :created_at)                            '
                data_id = str(uuid.uuid4())
                await self._db_manager.execute_raw(sql=data_sql, params={'id': data_id, 'snapshot_id': snapshot_id, 'data_json': data_json, 'schema_json': schema_json, 'created_at': datetime.datetime.now()}, connection_name=self._history_connection_id)
            return entry
        except Exception as e:
            self._logger.error(f'Failed to store history data: {str(e)}')
            raise DatabaseError(message=f'Failed to store history data: {str(e)}', details={'original_error': str(e)})
    async def _cleanup_old_data(self, schedule_id: str, retention_days: int) -> None:
        if not self._history_connection_id:
            return
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
            find_sql = '\n                       SELECT snapshot_id                        FROM db_history_entries\n                       WHERE schedule_id = :schedule_id                          AND collected_at < :cutoff_date                        '
            snapshots = await self._db_manager.execute_raw(sql=find_sql, params={'schedule_id': schedule_id, 'cutoff_date': cutoff_date}, connection_name=self._history_connection_id)
            if not snapshots:
                return
            for row in snapshots:
                snapshot_id = row['snapshot_id']
                await self.delete_history_data(snapshot_id)
            self._logger.info(f'Cleaned up {len(snapshots)} old history snapshots for schedule {schedule_id}')
        except Exception as e:
            self._logger.error(f'Failed to clean up old history data: {str(e)}')
    def _parse_frequency(self, frequency: str) -> Optional[int]:
        import re
        match = re.match('^(\\d+)([smhdw])$', frequency.lower())
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