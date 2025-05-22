from __future__ import annotations
'\nHistory tracking utilities for the Database Manager.\n\nThis module provides functionality for tracking and managing historical\ndatabase data, including scheduling periodic data collection and storing\nthe results for later reference.\n'
import asyncio
import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from sqlalchemy import text
from qorzen.utils.exceptions import DatabaseError
class HistoryManager:
    def __init__(self, database_manager: Any, logger: Any, history_connection_id: Optional[str]=None) -> None:
        self._db_manager = database_manager
        self._logger = logger
        self._history_connection_id = history_connection_id
        self._running_schedules: Dict[str, asyncio.Task] = {}
        self._is_initialized = False
    async def initialize(self) -> None:
        if not self._history_connection_id:
            self._logger.warning('No history database connection configured')
            return
        try:
            config = await self._db_manager._config_manager.get('database.history', {})
            if not config.get('enabled', True):
                self._logger.info('History tracking system disabled in configuration')
                return
            if not self._history_connection_id:
                raise DatabaseError(message='No history database connection ID provided', details={})
            if not self._db_manager:
                raise DatabaseError(message='No database manager available', details={})
            if not await self._db_manager.has_connection(self._history_connection_id):
                raise DatabaseError(message=f'Database connection {self._history_connection_id} not found', details={'connection_id': self._history_connection_id})
            try:
                await self._create_history_tables_async()
            except Exception as e:
                self._logger.warning(f'Could not create tables with async session: {str(e)}')
                try:
                    await self._create_history_tables_sync()
                except Exception as e2:
                    self._logger.warning(f'Failed to create history tables with sync session: {str(e2)}')
            await self._load_and_start_schedules()
            self._is_initialized = True
            self._logger.info('History manager initialized')
        except Exception as e:
            self._logger.warning(f'History manager initialization failed but will continue: {str(e)}')
    async def _create_history_tables_async(self) -> None:
        statements = ['\n            CREATE TABLE IF NOT EXISTS db_history_schedules\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                description TEXT,\n                query_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                frequency VARCHAR\n            (\n                100\n            ) NOT NULL,\n                retention_days INTEGER NOT NULL DEFAULT 365,\n                active BOOLEAN NOT NULL DEFAULT TRUE,\n                last_run TIMESTAMP,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n                )\n            ', "\n            CREATE TABLE IF NOT EXISTS db_history_entries\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                schedule_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                query_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                table_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                snapshot_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                record_count INTEGER NOT NULL DEFAULT 0,\n                status VARCHAR\n            (\n                50\n            ) NOT NULL DEFAULT 'success',\n                error_message TEXT,\n                FOREIGN KEY\n            (\n                schedule_id\n            ) REFERENCES db_history_schedules\n            (\n                id\n            ) ON DELETE CASCADE\n                )\n            ", '\n            CREATE TABLE IF NOT EXISTS db_history_data\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                snapshot_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                data_json TEXT NOT NULL,\n                schema_json TEXT NOT NULL,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n                )\n            ']
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self._db_manager.async_session(self._history_connection_id) as session:
                    for stmt in statements:
                        self._logger.debug(f'Creating history table (async): {stmt[:50]}...')
                        await session.execute(text(stmt))
                self._logger.debug('History tables created or already exist (async)')
                return
            except Exception as e:
                self._logger.warning(f'Async attempt {attempt + 1}/{max_retries} failed: {str(e)}')
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(1)
                else:
                    raise
    async def _create_history_tables_sync(self) -> None:
        statements = ['\n            CREATE TABLE IF NOT EXISTS db_history_schedules\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                description TEXT,\n                query_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                frequency VARCHAR\n            (\n                100\n            ) NOT NULL,\n                retention_days INTEGER NOT NULL DEFAULT 365,\n                active BOOLEAN NOT NULL DEFAULT TRUE,\n                last_run TIMESTAMP,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n                )\n            ', "\n            CREATE TABLE IF NOT EXISTS db_history_entries\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                schedule_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                query_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                table_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                snapshot_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                record_count INTEGER NOT NULL DEFAULT 0,\n                status VARCHAR\n            (\n                50\n            ) NOT NULL DEFAULT 'success',\n                error_message TEXT,\n                FOREIGN KEY\n            (\n                schedule_id\n            ) REFERENCES db_history_schedules\n            (\n                id\n            ) ON DELETE CASCADE\n                )\n            ", '\n            CREATE TABLE IF NOT EXISTS db_history_data\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                snapshot_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                data_json TEXT NOT NULL,\n                schema_json TEXT NOT NULL,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n                )\n            ']
        for stmt in statements:
            self._logger.debug(f'Creating history table (sync): {stmt[:50]}...')
            try:
                await self._db_manager.execute_raw(sql=stmt, connection_name=self._history_connection_id)
            except Exception as e:
                self._logger.warning(f'Error creating table with execute_raw: {str(e)}')
                raise
        self._logger.debug('History tables created or already exist (sync)')
    async def _load_and_start_schedules(self) -> None:
        try:
            query = 'SELECT * FROM db_history_schedules WHERE active = TRUE'
            results = await self._db_manager.execute_raw(sql=query, connection_name=self._history_connection_id)
            schedules = []
            for row in results:
                schedule = {'id': row['id'], 'connection_id': row['connection_id'], 'name': row['name'], 'description': row['description'], 'query_id': row['query_id'], 'frequency': row['frequency'], 'retention_days': row['retention_days'], 'active': row['active'], 'last_run': row['last_run'], 'created_at': row['created_at'], 'updated_at': row['updated_at']}
                schedules.append(schedule)
            for schedule in schedules:
                await self.start_schedule(schedule)
            self._logger.info(f'Started {len(schedules)} history collection schedules')
        except Exception as e:
            self._logger.error(f'Failed to load and start schedules: {str(e)}')
            raise DatabaseError(message=f'Failed to load and start schedules: {str(e)}', details={'original_error': str(e)}) from e
    async def create_schedule(self, connection_id: str, query_id: str, frequency: str, name: str, description: Optional[str]=None, retention_days: int=365) -> Dict[str, Any]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            seconds = self._parse_frequency(frequency)
            if seconds is None:
                raise ValueError(f'Invalid frequency format: {frequency}')
            schedule_id = str(uuid.uuid4())
            now = datetime.datetime.now()
            schedule = {'id': schedule_id, 'connection_id': connection_id, 'name': name, 'description': description, 'query_id': query_id, 'frequency': frequency, 'retention_days': retention_days, 'active': True, 'last_run': None, 'created_at': now, 'updated_at': now}
            insert_sql = '\n                         INSERT INTO db_history_schedules\n                         (id, connection_id, name, description, query_id,\n                          frequency, retention_days, active, created_at, updated_at)\n                         VALUES (:id, :connection_id, :name, :description, :query_id,                                  :frequency, :retention_days, :active, :created_at, :updated_at)                          '
            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(insert_sql), schedule)
            if schedule['active']:
                await self.start_schedule(schedule)
            self._logger.info(f'Created history schedule: {name}')
            return schedule
        except Exception as e:
            self._logger.error(f'Failed to create history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to create history schedule: {str(e)}', details={'original_error': str(e)}) from e
    async def update_schedule(self, schedule_id: str, **updates: Any) -> Dict[str, Any]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            existing = await self.get_schedule(schedule_id)
            if not existing:
                raise DatabaseError(message=f'Schedule not found: {schedule_id}', details={})
            schedule = dict(existing)
            for key, value in updates.items():
                if key in schedule:
                    schedule[key] = value
            if 'frequency' in updates:
                seconds = self._parse_frequency(schedule['frequency'])
                if seconds is None:
                    raise ValueError(f"Invalid frequency format: {schedule['frequency']}")
            schedule['updated_at'] = datetime.datetime.now()
            update_sql = '\n                         UPDATE db_history_schedules\n                         SET connection_id  = :connection_id,\n                             name           = :name,\n                             description    = :description,\n                             query_id       = :query_id,\n                             frequency      = :frequency,\n                             retention_days = :retention_days,\n                             active         = :active,\n                             updated_at     = :updated_at\n                         WHERE id = :id                          '
            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(update_sql), schedule)
            if schedule_id in self._running_schedules:
                await self.stop_schedule(schedule_id)
            if schedule['active']:
                await self.start_schedule(schedule)
            self._logger.info(f"Updated history schedule: {schedule['name']}")
            return schedule
        except Exception as e:
            self._logger.error(f'Failed to update history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to update history schedule: {str(e)}', details={'original_error': str(e)}) from e
    async def delete_schedule(self, schedule_id: str) -> bool:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            if schedule_id in self._running_schedules:
                await self.stop_schedule(schedule_id)
            delete_sql = 'DELETE FROM db_history_schedules WHERE id = :id'
            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(delete_sql), {'id': schedule_id})
            self._logger.info(f'Deleted history schedule: {schedule_id}')
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to delete history schedule: {str(e)}', details={'original_error': str(e)}) from e
    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            query = 'SELECT * FROM db_history_schedules WHERE id = :id'
            async with self._db_manager.async_session(self._history_connection_id) as session:
                result = await session.execute(text(query), {'id': schedule_id})
                row = result.fetchone()
            if not row:
                return None
            return {'id': row[0], 'connection_id': row[1], 'name': row[2], 'description': row[3], 'query_id': row[4], 'frequency': row[5], 'retention_days': row[6], 'active': row[7], 'last_run': row[8], 'created_at': row[9], 'updated_at': row[10]}
        except Exception as e:
            self._logger.error(f'Failed to get history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to get history schedule: {str(e)}', details={'original_error': str(e)}) from e
    async def get_all_schedules(self) -> List[Dict[str, Any]]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            query = 'SELECT * FROM db_history_schedules ORDER BY name'
            async with self._db_manager.async_session(self._history_connection_id) as session:
                result = await session.execute(text(query))
                rows = result.fetchall()
            schedules = []
            for row in rows:
                schedule = {'id': row[0], 'connection_id': row[1], 'name': row[2], 'description': row[3], 'query_id': row[4], 'frequency': row[5], 'retention_days': row[6], 'active': row[7], 'last_run': row[8], 'created_at': row[9], 'updated_at': row[10]}
                schedules.append(schedule)
            return schedules
        except Exception as e:
            self._logger.error(f'Failed to get history schedules: {str(e)}')
            raise DatabaseError(message=f'Failed to get history schedules: {str(e)}', details={'original_error': str(e)}) from e
    async def start_schedule(self, schedule: Dict[str, Any]) -> None:
        schedule_id = schedule['id']
        if schedule_id in self._running_schedules:
            return
        try:
            seconds = self._parse_frequency(schedule['frequency'])
            if seconds is None:
                self._logger.error(f"Invalid frequency format: {schedule['frequency']}")
                return
            task = asyncio.create_task(self._run_schedule(schedule_id, seconds))
            self._running_schedules[schedule_id] = task
            self._logger.info(f"Started history schedule: {schedule['name']}")
        except Exception as e:
            self._logger.error(f'Failed to start history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to start history schedule: {str(e)}', details={'original_error': str(e)}) from e
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
            raise DatabaseError(message=f'Failed to stop history schedule: {str(e)}', details={'original_error': str(e)}) from e
    async def execute_schedule_now(self, schedule_id: str) -> Dict[str, Any]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            schedule = await self.get_schedule(schedule_id)
            if not schedule:
                raise DatabaseError(message=f'Schedule not found: {schedule_id}', details={})
            query_result = await self._db_manager.execute_raw(sql='SELECT * FROM db_saved_queries WHERE id = :id', params={'id': schedule['query_id']}, connection_name=self._history_connection_id)
            if not query_result:
                raise DatabaseError(message=f"Query not found: {schedule['query_id']}", details={})
            saved_query = query_result[0]
            snapshot_id = str(uuid.uuid4())
            result = await self._db_manager.execute_query(query=saved_query['query_text'], params=json.loads(saved_query.get('parameters', '{}')), connection_name=schedule['connection_id'])
            entry = await self._store_history_data(schedule=schedule, query=saved_query, result=result, snapshot_id=snapshot_id)
            update_sql = '\n                         UPDATE db_history_schedules\n                         SET last_run   = :last_run,\n                             updated_at = :updated_at\n                         WHERE id = :id                          '
            now = datetime.datetime.now()
            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(update_sql), {'id': schedule_id, 'last_run': now, 'updated_at': now})
            self._logger.info(f"Executed history schedule: {schedule['name']}, captured {result['row_count']} records")
            return entry
        except Exception as e:
            self._logger.error(f'Failed to execute history schedule: {str(e)}')
            raise DatabaseError(message=f'Failed to execute history schedule: {str(e)}', details={'original_error': str(e)}) from e
    async def get_history_entries(self, schedule_id: Optional[str]=None, limit: int=100) -> List[Dict[str, Any]]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            if schedule_id:
                sql = '\n                      SELECT *\n                      FROM db_history_entries\n                      WHERE schedule_id = :schedule_id\n                      ORDER BY collected_at DESC LIMIT :limit                       '
                params = {'schedule_id': schedule_id, 'limit': limit}
            else:
                sql = '\n                      SELECT *\n                      FROM db_history_entries\n                      ORDER BY collected_at DESC LIMIT :limit                       '
                params = {'limit': limit}
            async with self._db_manager.async_session(self._history_connection_id) as session:
                result = await session.execute(text(sql), params)
                rows = result.fetchall()
            entries = []
            for row in rows:
                entry = {'id': row[0], 'schedule_id': row[1], 'connection_id': row[2], 'query_id': row[3], 'table_name': row[4], 'collected_at': row[5], 'snapshot_id': row[6], 'record_count': row[7], 'status': row[8], 'error_message': row[9]}
                entries.append(entry)
            return entries
        except Exception as e:
            self._logger.error(f'Failed to get history entries: {str(e)}')
            raise DatabaseError(message=f'Failed to get history entries: {str(e)}', details={'original_error': str(e)}) from e
    async def get_history_data(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            data_sql = '\n                       SELECT *\n                       FROM db_history_data\n                       WHERE snapshot_id = :snapshot_id                        '
            entry_sql = '\n                        SELECT *\n                        FROM db_history_entries\n                        WHERE snapshot_id = :snapshot_id                         '
            async with self._db_manager.async_session(self._history_connection_id) as session:
                data_result = await session.execute(text(data_sql), {'snapshot_id': snapshot_id})
                data_row = data_result.fetchone()
                entry_result = await session.execute(text(entry_sql), {'snapshot_id': snapshot_id})
                entry_row = entry_result.fetchone()
            if not data_row or not entry_row:
                return None
            data_json = json.loads(data_row[2])
            schema_json = json.loads(data_row[3])
            metadata = {'snapshot_id': snapshot_id, 'connection_id': entry_row[2], 'query_id': entry_row[3], 'table_name': entry_row[4], 'collected_at': entry_row[5], 'record_count': entry_row[7]}
            return {'data': data_json, 'schema': schema_json, 'metadata': metadata}
        except Exception as e:
            self._logger.error(f'Failed to get history data: {str(e)}')
            raise DatabaseError(message=f'Failed to get history data: {str(e)}', details={'original_error': str(e)}) from e
    async def delete_history_data(self, snapshot_id: str) -> bool:
        if not self._history_connection_id:
            raise DatabaseError(message='No history database connection configured', details={})
        try:
            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text('DELETE FROM db_history_data WHERE snapshot_id = :snapshot_id'), {'snapshot_id': snapshot_id})
                await session.execute(text('DELETE FROM db_history_entries WHERE snapshot_id = :snapshot_id'), {'snapshot_id': snapshot_id})
            self._logger.info(f'Deleted history data for snapshot: {snapshot_id}')
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete history data: {str(e)}')
            raise DatabaseError(message=f'Failed to delete history data: {str(e)}', details={'original_error': str(e)}) from e
    async def _run_schedule(self, schedule_id: str, interval_seconds: int) -> None:
        while True:
            try:
                schedule = await self.get_schedule(schedule_id)
                if not schedule or not schedule['active']:
                    self._logger.info(f'Schedule {schedule_id} is no longer active')
                    break
                await self.execute_schedule_now(schedule_id)
                await self._cleanup_old_data(schedule['id'], schedule['retention_days'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f'Error running history schedule {schedule_id}: {str(e)}')
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
    async def _store_history_data(self, schedule: Dict[str, Any], query: Dict[str, Any], result: Dict[str, Any], snapshot_id: str) -> Dict[str, Any]:
        try:
            table_name = 'unknown'
            match = re.search('FROM\\s+(\\w+)', result['query'], re.IGNORECASE)
            if match:
                table_name = match.group(1)
            status = 'success'
            error_message = None
            if result.get('has_error', False):
                status = 'error'
                error_message = result.get('error_message')
            entry = {'id': str(uuid.uuid4()), 'schedule_id': schedule['id'], 'connection_id': schedule['connection_id'], 'query_id': schedule['query_id'], 'table_name': table_name, 'collected_at': datetime.datetime.now(), 'snapshot_id': snapshot_id, 'record_count': result.get('row_count', 0), 'status': status, 'error_message': error_message}
            entry_sql = '\n                        INSERT INTO db_history_entries\n                        (id, schedule_id, connection_id, query_id, table_name,\n                         collected_at, snapshot_id, record_count, status, error_message)\n                        VALUES (:id, :schedule_id, :connection_id, :query_id, :table_name,                                 :collected_at, :snapshot_id, :record_count, :status, :error_message)                         '
            async with self._db_manager.async_session(self._history_connection_id) as session:
                await session.execute(text(entry_sql), entry)
            if status == 'success' and result.get('records'):
                data_json = json.dumps(result['records'])
                schema = []
                for col in result.get('columns', []):
                    schema.append({'name': col['name'], 'type_name': col['type_name'], 'type_code': col['type_code'], 'precision': col['precision'], 'scale': col['scale'], 'nullable': col['nullable']})
                schema_json = json.dumps(schema)
                data_sql = '\n                           INSERT INTO db_history_data\n                               (id, snapshot_id, data_json, schema_json, created_at)\n                           VALUES (:id, :snapshot_id, :data_json, :schema_json, :created_at)                            '
                data_id = str(uuid.uuid4())
                async with self._db_manager.async_session(self._history_connection_id) as session:
                    await session.execute(text(data_sql), {'id': data_id, 'snapshot_id': snapshot_id, 'data_json': data_json, 'schema_json': schema_json, 'created_at': datetime.datetime.now()})
            return entry
        except Exception as e:
            self._logger.error(f'Failed to store history data: {str(e)}')
            raise DatabaseError(message=f'Failed to store history data: {str(e)}', details={'original_error': str(e)}) from e
    async def _cleanup_old_data(self, schedule_id: str, retention_days: int) -> None:
        if not self._history_connection_id:
            return
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
            find_sql = '\n                       SELECT snapshot_id\n                       FROM db_history_entries\n                       WHERE schedule_id = :schedule_id\n                         AND collected_at < :cutoff_date                        '
            async with self._db_manager.async_session(self._history_connection_id) as session:
                result = await session.execute(text(find_sql), {'schedule_id': schedule_id, 'cutoff_date': cutoff_date})
                snapshots = result.fetchall()
            for row in snapshots:
                snapshot_id = row[0]
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
    async def shutdown(self) -> None:
        for schedule_id in list(self._running_schedules.keys()):
            try:
                await self.stop_schedule(schedule_id)
            except Exception as e:
                self._logger.warning(f'Error stopping schedule {schedule_id}: {str(e)}')
        self._is_initialized = False
        self._logger.info('History manager shut down')