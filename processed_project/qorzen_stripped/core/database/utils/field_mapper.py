from __future__ import annotations
'\nField mapping utilities for the Database Manager.\n\nThis module provides utilities for creating and applying field mappings\nbetween database tables and standardized field names.\n'
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from sqlalchemy import text
from qorzen.utils.exceptions import DatabaseError
class FieldMapperManager:
    def __init__(self, database_manager: Any, logger: Any) -> None:
        self._db_manager = database_manager
        self._logger = logger
        self._is_initialized = False
        self._default_mapping_connection_id: Optional[str] = None
    async def initialize(self) -> None:
        try:
            config = await self._db_manager._config_manager.get('database.field_mapping', {})
            if not config.get('enabled', True):
                self._logger.info('Field mapping system disabled in configuration')
                return
            self._default_mapping_connection_id = config.get('connection_id', 'default')
            if not await self._db_manager.has_connection(self._default_mapping_connection_id):
                self._logger.warning(f"Field mapping connection '{self._default_mapping_connection_id}' not found, using default")
                self._default_mapping_connection_id = 'default'
            try:
                await self._create_mapping_tables_async()
            except Exception as e:
                self._logger.warning(f'Could not create tables with async session: {str(e)}')
                try:
                    await self._create_mapping_tables_sync()
                except Exception as e2:
                    self._logger.warning(f'Failed to create field mapping tables with sync session: {str(e2)}')
            self._is_initialized = True
            self._logger.info('Field mapper initialized', extra={'default_connection_id': self._default_mapping_connection_id})
        except Exception as e:
            self._logger.warning(f'Field mapper initialization failed but will continue: {str(e)}')
    async def _create_mapping_tables_async(self) -> None:
        statements = ['\n            CREATE TABLE IF NOT EXISTS db_field_mappings\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                table_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                description TEXT,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                UNIQUE\n            (\n                connection_id,\n                table_name\n            )\n                )\n            ', '\n            CREATE TABLE IF NOT EXISTS db_field_mapping_entries\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                mapping_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                original_field VARCHAR\n            (\n                255\n            ) NOT NULL,\n                mapped_field VARCHAR\n            (\n                255\n            ) NOT NULL,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                FOREIGN KEY\n            (\n                mapping_id\n            ) REFERENCES db_field_mappings\n            (\n                id\n            ) ON DELETE CASCADE,\n                UNIQUE\n            (\n                mapping_id,\n                original_field\n            )\n                )\n            ']
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                    for stmt in statements:
                        self._logger.debug(f'Creating field mapping table (async): {stmt[:50]}...')
                        await session.execute(text(stmt))
                self._logger.debug('Field mapping tables created or already exist (async)')
                return
            except Exception as e:
                self._logger.warning(f'Async attempt {attempt + 1}/{max_retries} failed: {str(e)}')
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(1)
                else:
                    raise
    async def _create_mapping_tables_sync(self) -> None:
        statements = ['\n            CREATE TABLE IF NOT EXISTS db_field_mappings\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                connection_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                table_name VARCHAR\n            (\n                255\n            ) NOT NULL,\n                description TEXT,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                UNIQUE\n            (\n                connection_id,\n                table_name\n            )\n                )\n            ', '\n            CREATE TABLE IF NOT EXISTS db_field_mapping_entries\n            (\n                id\n                VARCHAR\n            (\n                36\n            ) PRIMARY KEY,\n                mapping_id VARCHAR\n            (\n                36\n            ) NOT NULL,\n                original_field VARCHAR\n            (\n                255\n            ) NOT NULL,\n                mapped_field VARCHAR\n            (\n                255\n            ) NOT NULL,\n                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                FOREIGN KEY\n            (\n                mapping_id\n            ) REFERENCES db_field_mappings\n            (\n                id\n            ) ON DELETE CASCADE,\n                UNIQUE\n            (\n                mapping_id,\n                original_field\n            )\n                )\n            ']
        for stmt in statements:
            self._logger.debug(f'Creating field mapping table (sync): {stmt[:50]}...')
            try:
                await self._db_manager.execute_raw(sql=stmt, connection_name=self._default_mapping_connection_id)
            except Exception as e:
                self._logger.warning(f'Error creating table with execute_raw: {str(e)}')
                raise
        self._logger.debug('Field mapping tables created or already exist (sync)')
    @staticmethod
    def standardize_field_name(field_name: str) -> str:
        name = re.sub('[^\\w\\s]', '', field_name)
        name = re.sub('\\s+', '_', name)
        name = re.sub('([a-z0-9])([A-Z])', '\\1_\\2', name)
        name = name.lower()
        name = re.sub('_+', '_', name)
        name = name.strip('_')
        return name
    async def create_mapping_from_fields(self, connection_id: str, table_name: str, field_names: List[str], description: Optional[str]=None) -> Dict[str, Any]:
        mappings: Dict[str, str] = {}
        for field in field_names:
            standardized = self.standardize_field_name(field)
            mappings[field] = standardized
        return await self.create_mapping(connection_id=connection_id, table_name=table_name, mappings=mappings, description=description)
    async def create_mapping(self, connection_id: str, table_name: str, mappings: Dict[str, str], description: Optional[str]=None) -> Dict[str, Any]:
        if not self._is_initialized:
            raise DatabaseError(message='Field mapper not initialized', details={})
        mapping_id = str(uuid.uuid4())
        now = datetime.now()
        try:
            existing = await self.get_mapping(connection_id, table_name)
            if existing:
                return await self.update_mapping(mapping_id=existing['id'], mappings=mappings, description=description)
            insert_mapping_sql = '\n                                 INSERT INTO db_field_mappings\n                                     (id, connection_id, table_name, description, created_at, updated_at)\n                                 VALUES (:id, :connection_id, :table_name, :description, :created_at, :updated_at)                                  '
            mapping_params = {'id': mapping_id, 'connection_id': connection_id, 'table_name': table_name, 'description': description, 'created_at': now, 'updated_at': now}
            insert_entry_sql = '\n                               INSERT INTO db_field_mapping_entries\n                                   (id, mapping_id, original_field, mapped_field, created_at)\n                               VALUES (:id, :mapping_id, :original_field, :mapped_field, :created_at)                                '
            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                await session.execute(text(insert_mapping_sql), mapping_params)
                for original_field, mapped_field in mappings.items():
                    entry_params = {'id': str(uuid.uuid4()), 'mapping_id': mapping_id, 'original_field': original_field, 'mapped_field': mapped_field, 'created_at': now}
                    await session.execute(text(insert_entry_sql), entry_params)
            self._logger.info(f'Created field mapping for {connection_id}.{table_name}', extra={'connection_id': connection_id, 'table_name': table_name, 'field_count': len(mappings)})
            return {'id': mapping_id, 'connection_id': connection_id, 'table_name': table_name, 'description': description, 'mappings': mappings, 'created_at': now, 'updated_at': now}
        except Exception as e:
            self._logger.error(f'Failed to create field mapping: {str(e)}')
            raise DatabaseError(message=f'Failed to create field mapping: {str(e)}', details={'original_error': str(e)}) from e
    async def update_mapping(self, mapping_id: str, mappings: Dict[str, str], description: Optional[str]=None) -> Dict[str, Any]:
        if not self._is_initialized:
            raise DatabaseError(message='Field mapper not initialized', details={})
        now = datetime.now()
        try:
            get_mapping_sql = '\n                              SELECT *                               FROM db_field_mappings\n                              WHERE id = :id                               '
            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                result = await session.execute(text(get_mapping_sql), {'id': mapping_id})
                row = result.fetchone()
                if not row:
                    raise DatabaseError(message=f'Field mapping with ID {mapping_id} not found', details={'mapping_id': mapping_id})
                connection_id = row[1]
                table_name = row[2]
                if description is not None:
                    update_mapping_sql = '\n                                         UPDATE db_field_mappings\n                                         SET description = :description,\n                                             updated_at  = :updated_at\n                                         WHERE id = :id                                          '
                    await session.execute(text(update_mapping_sql), {'id': mapping_id, 'description': description, 'updated_at': now})
                delete_entries_sql = '\n                                     DELETE                                      FROM db_field_mapping_entries\n                                     WHERE mapping_id = :mapping_id                                      '
                await session.execute(text(delete_entries_sql), {'mapping_id': mapping_id})
                insert_entry_sql = '\n                                   INSERT INTO db_field_mapping_entries\n                                       (id, mapping_id, original_field, mapped_field, created_at)\n                                   VALUES (:id, :mapping_id, :original_field, :mapped_field, :created_at)                                    '
                for original_field, mapped_field in mappings.items():
                    entry_params = {'id': str(uuid.uuid4()), 'mapping_id': mapping_id, 'original_field': original_field, 'mapped_field': mapped_field, 'created_at': now}
                    await session.execute(text(insert_entry_sql), entry_params)
            self._logger.info(f'Updated field mapping for {connection_id}.{table_name}', extra={'mapping_id': mapping_id, 'field_count': len(mappings)})
            return {'id': mapping_id, 'connection_id': connection_id, 'table_name': table_name, 'description': description, 'mappings': mappings, 'updated_at': now}
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            self._logger.error(f'Failed to update field mapping: {str(e)}')
            raise DatabaseError(message=f'Failed to update field mapping: {str(e)}', details={'original_error': str(e)}) from e
    async def delete_mapping(self, mapping_id: str) -> bool:
        if not self._is_initialized:
            raise DatabaseError(message='Field mapper not initialized', details={})
        try:
            delete_sql = '\n                         DELETE                          FROM db_field_mappings\n                         WHERE id = :id                          '
            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                result = await session.execute(text(delete_sql), {'id': mapping_id})
            self._logger.info(f'Deleted field mapping: {mapping_id}')
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete field mapping: {str(e)}')
            raise DatabaseError(message=f'Failed to delete field mapping: {str(e)}', details={'original_error': str(e)}) from e
    async def get_mapping(self, connection_id: str, table_name: str) -> Optional[Dict[str, Any]]:
        if not self._is_initialized:
            raise DatabaseError(message='Field mapper not initialized', details={})
        try:
            mapping_sql = '\n                          SELECT *                           FROM db_field_mappings\n                          WHERE connection_id = :connection_id                             AND table_name = :table_name                           '
            entries_sql = '\n                          SELECT original_field, mapped_field                           FROM db_field_mapping_entries\n                          WHERE mapping_id = :mapping_id                           '
            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                mapping_result = await session.execute(text(mapping_sql), {'connection_id': connection_id, 'table_name': table_name})
                mapping_row = mapping_result.fetchone()
                if not mapping_row:
                    return None
                mapping_id = mapping_row[0]
                description = mapping_row[3]
                created_at = mapping_row[4]
                updated_at = mapping_row[5]
                entries_result = await session.execute(text(entries_sql), {'mapping_id': mapping_id})
                entries_rows = entries_result.fetchall()
                mappings = {row[0]: row[1] for row in entries_rows}
            return {'id': mapping_id, 'connection_id': connection_id, 'table_name': table_name, 'description': description, 'mappings': mappings, 'created_at': created_at, 'updated_at': updated_at}
        except Exception as e:
            self._logger.error(f'Failed to get field mapping: {str(e)}')
            raise DatabaseError(message=f'Failed to get field mapping: {str(e)}', details={'original_error': str(e)}) from e
    async def get_mapping_by_id(self, mapping_id: str) -> Optional[Dict[str, Any]]:
        if not self._is_initialized:
            raise DatabaseError(message='Field mapper not initialized', details={})
        try:
            mapping_sql = '\n                          SELECT *                           FROM db_field_mappings\n                          WHERE id = :id                           '
            entries_sql = '\n                          SELECT original_field, mapped_field                           FROM db_field_mapping_entries\n                          WHERE mapping_id = :mapping_id                           '
            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                mapping_result = await session.execute(text(mapping_sql), {'id': mapping_id})
                mapping_row = mapping_result.fetchone()
                if not mapping_row:
                    return None
                connection_id = mapping_row[1]
                table_name = mapping_row[2]
                description = mapping_row[3]
                created_at = mapping_row[4]
                updated_at = mapping_row[5]
                entries_result = await session.execute(text(entries_sql), {'mapping_id': mapping_id})
                entries_rows = entries_result.fetchall()
                mappings = {row[0]: row[1] for row in entries_rows}
            return {'id': mapping_id, 'connection_id': connection_id, 'table_name': table_name, 'description': description, 'mappings': mappings, 'created_at': created_at, 'updated_at': updated_at}
        except Exception as e:
            self._logger.error(f'Failed to get field mapping: {str(e)}')
            raise DatabaseError(message=f'Failed to get field mapping: {str(e)}', details={'original_error': str(e)}) from e
    async def get_all_mappings(self, connection_id: Optional[str]=None) -> List[Dict[str, Any]]:
        if not self._is_initialized:
            raise DatabaseError(message='Field mapper not initialized', details={})
        try:
            if connection_id:
                mapping_sql = '\n                              SELECT *                               FROM db_field_mappings\n                              WHERE connection_id = :connection_id\n                              ORDER BY table_name                               '
                params = {'connection_id': connection_id}
            else:
                mapping_sql = '\n                              SELECT *                               FROM db_field_mappings\n                              ORDER BY connection_id, table_name                               '
                params = {}
            mappings = []
            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                mapping_result = await session.execute(text(mapping_sql), params)
                mapping_rows = mapping_result.fetchall()
                for row in mapping_rows:
                    mapping_id = row[0]
                    connection_id = row[1]
                    table_name = row[2]
                    description = row[3]
                    created_at = row[4]
                    updated_at = row[5]
                    entries_sql = '\n                                  SELECT original_field, mapped_field                                   FROM db_field_mapping_entries\n                                  WHERE mapping_id = :mapping_id                                   '
                    entries_result = await session.execute(text(entries_sql), {'mapping_id': mapping_id})
                    entries_rows = entries_result.fetchall()
                    field_mappings = {row[0]: row[1] for row in entries_rows}
                    mappings.append({'id': mapping_id, 'connection_id': connection_id, 'table_name': table_name, 'description': description, 'mappings': field_mappings, 'created_at': created_at, 'updated_at': updated_at})
            return mappings
        except Exception as e:
            self._logger.error(f'Failed to get field mappings: {str(e)}')
            raise DatabaseError(message=f'Failed to get field mappings: {str(e)}', details={'original_error': str(e)}) from e
    async def apply_mapping_to_query(self, query: str, mapping: Dict[str, Any]) -> str:
        mappings = mapping.get('mappings', {})
        table_name = mapping.get('table_name', '')
        if query.strip() == table_name:
            return self._expand_table_to_query(query, mappings)
        if re.search('SELECT\\s+\\*\\s+FROM', query, re.IGNORECASE):
            return self._replace_select_star(query, table_name, mappings)
        return self._add_as_clauses(query, mappings)
    def _expand_table_to_query(self, table_name: str, mappings: Dict[str, str]) -> str:
        field_clauses = []
        for orig_name, mapped_name in mappings.items():
            if orig_name != mapped_name:
                field_clauses.append(f'"{orig_name}" AS "{mapped_name}"')
            else:
                field_clauses.append(f'"{orig_name}"')
        return f"SELECT {', '.join(field_clauses)} FROM {table_name}"
    def _replace_select_star(self, query: str, table_name: str, mappings: Dict[str, str]) -> str:
        match = re.search('FROM\\s+(.+)', query, re.IGNORECASE | re.DOTALL)
        if not match:
            return query
        from_clause = match.group(1)
        field_clauses = []
        for orig_name, mapped_name in mappings.items():
            if orig_name != mapped_name:
                field_clauses.append(f'"{orig_name}" AS "{mapped_name}"')
            else:
                field_clauses.append(f'"{orig_name}"')
        return f"SELECT {', '.join(field_clauses)} FROM {from_clause}"
    def _add_as_clauses(self, query: str, mappings: Dict[str, str]) -> str:
        match = re.search('SELECT\\s+(.+?)\\s+FROM', query, re.IGNORECASE | re.DOTALL)
        if not match:
            return query
        select_clause = match.group(1)
        fields = [f.strip() for f in select_clause.split(',')]
        new_fields = []
        for field in fields:
            if ' AS ' in field.upper() or ' as ' in field:
                new_fields.append(field)
                continue
            if '(' in field or '+' in field or '-' in field or ('*' in field) or ('/' in field):
                new_fields.append(field)
                continue
            if '.' in field:
                parts = field.split('.')
                table = parts[0].strip('"[]`')
                field_name = parts[1].strip('"[]`')
                if field_name in mappings and mappings[field_name] != field_name:
                    new_fields.append(f'{parts[0]}.{field_name} AS "{mappings[field_name]}"')
                else:
                    new_fields.append(field)
                continue
            field_name = field.strip('"[]`')
            if field_name in mappings and mappings[field_name] != field_name:
                new_fields.append(f'{field_name} AS "{mappings[field_name]}"')
            else:
                new_fields.append(field)
        new_select_clause = ', '.join(new_fields)
        return query.replace(select_clause, new_select_clause)
    async def apply_mapping_to_results(self, result: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        mappings = mapping.get('mappings', {})
        if not mappings:
            return result
        field_map = {}
        for column in result.get('columns', []):
            col_name = column.get('name', '')
            if col_name in mappings:
                field_map[col_name] = mappings[col_name]
            else:
                field_map[col_name] = col_name
        mapped_records = []
        for record in result.get('records', []):
            mapped_record = {}
            for field_name, value in record.items():
                mapped_field = field_map.get(field_name, field_name)
                mapped_record[mapped_field] = value
            mapped_records.append(mapped_record)
        mapped_columns = []
        for column in result.get('columns', []):
            col_name = column.get('name', '')
            mapped_name = field_map.get(col_name, col_name)
            mapped_column = dict(column)
            mapped_column['name'] = mapped_name
            mapped_columns.append(mapped_column)
        mapped_result = dict(result)
        mapped_result['records'] = mapped_records
        mapped_result['columns'] = mapped_columns
        mapped_result['mapped_fields'] = field_map
        return mapped_result
    async def shutdown(self) -> None:
        self._is_initialized = False
        self._logger.info('Field mapper shut down')
def standardize_field_name(field_name: str) -> str:
    return FieldMapperManager.standardize_field_name(field_name)