from __future__ import annotations

"""
Field mapping utilities for the Database Manager.

This module provides utilities for creating and applying field mappings
between database tables and standardized field names.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from sqlalchemy import text

from qorzen.utils.exceptions import DatabaseError


class FieldMapperManager:
    """Manager for field mapping operations."""

    def __init__(self, database_manager: Any, logger: Any) -> None:
        """Initialize the field mapper manager.

        Args:
            database_manager: The database manager instance
            logger: Logger instance
        """
        self._db_manager = database_manager
        self._logger = logger
        self._is_initialized = False
        self._default_mapping_connection_id: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the field mapper.

        This method sets up the field mapper and creates necessary tables.
        It gracefully handles cases where async sessions aren't supported.

        Raises:
            DatabaseError: If initialization fails and is critical.
        """
        try:
            # Check if field mapping is enabled
            config = await self._db_manager._config_manager.get('database.field_mapping', {})
            if not config.get('enabled', True):
                self._logger.info('Field mapping system disabled in configuration')
                return

            self._default_mapping_connection_id = config.get('connection_id', 'default')

            if not await self._db_manager.has_connection(self._default_mapping_connection_id):
                self._logger.warning(
                    f"Field mapping connection '{self._default_mapping_connection_id}' not found, using default")
                self._default_mapping_connection_id = 'default'

            # Try to create tables with async session first
            try:
                await self._create_mapping_tables_async()
            except Exception as e:
                self._logger.warning(f"Could not create tables with async session: {str(e)}")
                # Fall back to synchronous session if async fails
                try:
                    await self._create_mapping_tables_sync()
                except Exception as e2:
                    self._logger.warning(f"Failed to create field mapping tables with sync session: {str(e2)}")
                    # Don't raise an exception here - we'll proceed without field mapping

            self._is_initialized = True
            self._logger.info('Field mapper initialized',
                              extra={'default_connection_id': self._default_mapping_connection_id})

        except Exception as e:
            self._logger.warning(f'Field mapper initialization failed but will continue: {str(e)}')
            # Don't propagate this exception up to prevent blocking application startup

    async def _create_mapping_tables_async(self) -> None:
        """Create mapping tables using async session."""
        statements = [
            '''
            CREATE TABLE IF NOT EXISTS db_field_mappings
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
                table_name VARCHAR
            (
                255
            ) NOT NULL,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE
            (
                connection_id,
                table_name
            )
                )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS db_field_mapping_entries
            (
                id
                VARCHAR
            (
                36
            ) PRIMARY KEY,
                mapping_id VARCHAR
            (
                36
            ) NOT NULL,
                original_field VARCHAR
            (
                255
            ) NOT NULL,
                mapped_field VARCHAR
            (
                255
            ) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY
            (
                mapping_id
            ) REFERENCES db_field_mappings
            (
                id
            ) ON DELETE CASCADE,
                UNIQUE
            (
                mapping_id,
                original_field
            )
                )
            '''
        ]

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
        """Create mapping tables using synchronous execution.

        This is a fallback for database systems that don't support async sessions.
        """
        statements = [
            '''
            CREATE TABLE IF NOT EXISTS db_field_mappings
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
                table_name VARCHAR
            (
                255
            ) NOT NULL,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE
            (
                connection_id,
                table_name
            )
                )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS db_field_mapping_entries
            (
                id
                VARCHAR
            (
                36
            ) PRIMARY KEY,
                mapping_id VARCHAR
            (
                36
            ) NOT NULL,
                original_field VARCHAR
            (
                255
            ) NOT NULL,
                mapped_field VARCHAR
            (
                255
            ) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY
            (
                mapping_id
            ) REFERENCES db_field_mappings
            (
                id
            ) ON DELETE CASCADE,
                UNIQUE
            (
                mapping_id,
                original_field
            )
                )
            '''
        ]

        for stmt in statements:
            self._logger.debug(f'Creating field mapping table (sync): {stmt[:50]}...')
            try:
                await self._db_manager.execute_raw(
                    sql=stmt,
                    connection_name=self._default_mapping_connection_id
                )
            except Exception as e:
                self._logger.warning(f'Error creating table with execute_raw: {str(e)}')
                raise

        self._logger.debug('Field mapping tables created or already exist (sync)')

    @staticmethod
    def standardize_field_name(field_name: str) -> str:
        """Convert a field name to a standardized format.

        This converts camelCase or other formats to snake_case.

        Args:
            field_name: The original field name

        Returns:
            str: The standardized field name
        """
        # Remove non-alphanumeric characters
        name = re.sub(r'[^\w\s]', '', field_name)

        # Replace spaces with underscores
        name = re.sub(r'\s+', '_', name)

        # Convert camelCase to snake_case
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)

        # Convert to lowercase
        name = name.lower()

        # Remove duplicate underscores
        name = re.sub(r'_+', '_', name)

        # Remove leading/trailing underscores
        name = name.strip('_')

        return name

    async def create_mapping_from_fields(
            self,
            connection_id: str,
            table_name: str,
            field_names: List[str],
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a field mapping from a list of field names.

        Args:
            connection_id: The database connection ID
            table_name: The table name
            field_names: List of field names to map
            description: Optional description

        Returns:
            Dict[str, Any]: The created mapping

        Raises:
            DatabaseError: If mapping creation fails
        """
        mappings: Dict[str, str] = {}

        for field in field_names:
            standardized = self.standardize_field_name(field)
            mappings[field] = standardized

        return await self.create_mapping(
            connection_id=connection_id,
            table_name=table_name,
            mappings=mappings,
            description=description
        )

    async def create_mapping(
            self,
            connection_id: str,
            table_name: str,
            mappings: Dict[str, str],
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a field mapping.

        Args:
            connection_id: The database connection ID
            table_name: The table name
            mappings: Dictionary of original field names to mapped names
            description: Optional description

        Returns:
            Dict[str, Any]: The created mapping

        Raises:
            DatabaseError: If mapping creation fails
        """
        if not self._is_initialized:
            raise DatabaseError(
                message="Field mapper not initialized",
                details={}
            )

        mapping_id = str(uuid.uuid4())
        now = datetime.now()

        try:
            # Check if mapping already exists
            existing = await self.get_mapping(connection_id, table_name)

            if existing:
                # Update existing mapping
                return await self.update_mapping(
                    mapping_id=existing["id"],
                    mappings=mappings,
                    description=description
                )

            # Create new mapping
            insert_mapping_sql = """
                                 INSERT INTO db_field_mappings
                                     (id, connection_id, table_name, description, created_at, updated_at)
                                 VALUES (:id, :connection_id, :table_name, :description, :created_at, :updated_at) \
                                 """

            mapping_params = {
                "id": mapping_id,
                "connection_id": connection_id,
                "table_name": table_name,
                "description": description,
                "created_at": now,
                "updated_at": now
            }

            insert_entry_sql = """
                               INSERT INTO db_field_mapping_entries
                                   (id, mapping_id, original_field, mapped_field, created_at)
                               VALUES (:id, :mapping_id, :original_field, :mapped_field, :created_at) \
                               """

            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                await session.execute(text(insert_mapping_sql), mapping_params)

                for original_field, mapped_field in mappings.items():
                    entry_params = {
                        "id": str(uuid.uuid4()),
                        "mapping_id": mapping_id,
                        "original_field": original_field,
                        "mapped_field": mapped_field,
                        "created_at": now
                    }
                    await session.execute(text(insert_entry_sql), entry_params)

            self._logger.info(
                f"Created field mapping for {connection_id}.{table_name}",
                extra={
                    "connection_id": connection_id,
                    "table_name": table_name,
                    "field_count": len(mappings)
                }
            )

            return {
                "id": mapping_id,
                "connection_id": connection_id,
                "table_name": table_name,
                "description": description,
                "mappings": mappings,
                "created_at": now,
                "updated_at": now
            }

        except Exception as e:
            self._logger.error(f"Failed to create field mapping: {str(e)}")
            raise DatabaseError(
                message=f"Failed to create field mapping: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def update_mapping(
            self,
            mapping_id: str,
            mappings: Dict[str, str],
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing field mapping.

        Args:
            mapping_id: The mapping ID
            mappings: Dictionary of original field names to mapped names
            description: Optional description

        Returns:
            Dict[str, Any]: The updated mapping

        Raises:
            DatabaseError: If mapping update fails
        """
        if not self._is_initialized:
            raise DatabaseError(
                message="Field mapper not initialized",
                details={}
            )

        now = datetime.now()

        try:
            # Get existing mapping
            get_mapping_sql = """
                              SELECT * \
                              FROM db_field_mappings
                              WHERE id = :id \
                              """

            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                result = await session.execute(text(get_mapping_sql), {"id": mapping_id})
                row = result.fetchone()

                if not row:
                    raise DatabaseError(
                        message=f"Field mapping with ID {mapping_id} not found",
                        details={"mapping_id": mapping_id}
                    )

                connection_id = row[1]
                table_name = row[2]

                # Update mapping description if provided
                if description is not None:
                    update_mapping_sql = """
                                         UPDATE db_field_mappings
                                         SET description = :description,
                                             updated_at  = :updated_at
                                         WHERE id = :id \
                                         """

                    await session.execute(
                        text(update_mapping_sql),
                        {"id": mapping_id, "description": description, "updated_at": now}
                    )

                # Delete existing entries
                delete_entries_sql = """
                                     DELETE \
                                     FROM db_field_mapping_entries
                                     WHERE mapping_id = :mapping_id \
                                     """

                await session.execute(text(delete_entries_sql), {"mapping_id": mapping_id})

                # Insert new entries
                insert_entry_sql = """
                                   INSERT INTO db_field_mapping_entries
                                       (id, mapping_id, original_field, mapped_field, created_at)
                                   VALUES (:id, :mapping_id, :original_field, :mapped_field, :created_at) \
                                   """

                for original_field, mapped_field in mappings.items():
                    entry_params = {
                        "id": str(uuid.uuid4()),
                        "mapping_id": mapping_id,
                        "original_field": original_field,
                        "mapped_field": mapped_field,
                        "created_at": now
                    }
                    await session.execute(text(insert_entry_sql), entry_params)

            self._logger.info(
                f"Updated field mapping for {connection_id}.{table_name}",
                extra={
                    "mapping_id": mapping_id,
                    "field_count": len(mappings)
                }
            )

            return {
                "id": mapping_id,
                "connection_id": connection_id,
                "table_name": table_name,
                "description": description,
                "mappings": mappings,
                "updated_at": now
            }

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise

            self._logger.error(f"Failed to update field mapping: {str(e)}")
            raise DatabaseError(
                message=f"Failed to update field mapping: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def delete_mapping(self, mapping_id: str) -> bool:
        """Delete a field mapping.

        Args:
            mapping_id: The mapping ID

        Returns:
            bool: True if successful

        Raises:
            DatabaseError: If mapping deletion fails
        """
        if not self._is_initialized:
            raise DatabaseError(
                message="Field mapper not initialized",
                details={}
            )

        try:
            delete_sql = """
                         DELETE \
                         FROM db_field_mappings
                         WHERE id = :id \
                         """

            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                result = await session.execute(text(delete_sql), {"id": mapping_id})

            self._logger.info(f"Deleted field mapping: {mapping_id}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to delete field mapping: {str(e)}")
            raise DatabaseError(
                message=f"Failed to delete field mapping: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def get_mapping(
            self,
            connection_id: str,
            table_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get a field mapping for a table.

        Args:
            connection_id: The database connection ID
            table_name: The table name

        Returns:
            Optional[Dict[str, Any]]: The mapping, or None if not found

        Raises:
            DatabaseError: If operation fails
        """
        if not self._is_initialized:
            raise DatabaseError(
                message="Field mapper not initialized",
                details={}
            )

        try:
            mapping_sql = """
                          SELECT * \
                          FROM db_field_mappings
                          WHERE connection_id = :connection_id \
                            AND table_name = :table_name \
                          """

            entries_sql = """
                          SELECT original_field, mapped_field \
                          FROM db_field_mapping_entries
                          WHERE mapping_id = :mapping_id \
                          """

            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                mapping_result = await session.execute(
                    text(mapping_sql),
                    {"connection_id": connection_id, "table_name": table_name}
                )
                mapping_row = mapping_result.fetchone()

                if not mapping_row:
                    return None

                mapping_id = mapping_row[0]
                description = mapping_row[3]
                created_at = mapping_row[4]
                updated_at = mapping_row[5]

                entries_result = await session.execute(
                    text(entries_sql),
                    {"mapping_id": mapping_id}
                )
                entries_rows = entries_result.fetchall()

                mappings = {row[0]: row[1] for row in entries_rows}

            return {
                "id": mapping_id,
                "connection_id": connection_id,
                "table_name": table_name,
                "description": description,
                "mappings": mappings,
                "created_at": created_at,
                "updated_at": updated_at
            }

        except Exception as e:
            self._logger.error(f"Failed to get field mapping: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get field mapping: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def get_mapping_by_id(self, mapping_id: str) -> Optional[Dict[str, Any]]:
        """Get a field mapping by ID.

        Args:
            mapping_id: The mapping ID

        Returns:
            Optional[Dict[str, Any]]: The mapping, or None if not found

        Raises:
            DatabaseError: If operation fails
        """
        if not self._is_initialized:
            raise DatabaseError(
                message="Field mapper not initialized",
                details={}
            )

        try:
            mapping_sql = """
                          SELECT * \
                          FROM db_field_mappings
                          WHERE id = :id \
                          """

            entries_sql = """
                          SELECT original_field, mapped_field \
                          FROM db_field_mapping_entries
                          WHERE mapping_id = :mapping_id \
                          """

            async with self._db_manager.async_session(self._default_mapping_connection_id) as session:
                mapping_result = await session.execute(
                    text(mapping_sql),
                    {"id": mapping_id}
                )
                mapping_row = mapping_result.fetchone()

                if not mapping_row:
                    return None

                connection_id = mapping_row[1]
                table_name = mapping_row[2]
                description = mapping_row[3]
                created_at = mapping_row[4]
                updated_at = mapping_row[5]

                entries_result = await session.execute(
                    text(entries_sql),
                    {"mapping_id": mapping_id}
                )
                entries_rows = entries_result.fetchall()

                mappings = {row[0]: row[1] for row in entries_rows}

            return {
                "id": mapping_id,
                "connection_id": connection_id,
                "table_name": table_name,
                "description": description,
                "mappings": mappings,
                "created_at": created_at,
                "updated_at": updated_at
            }

        except Exception as e:
            self._logger.error(f"Failed to get field mapping: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get field mapping: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def get_all_mappings(
            self,
            connection_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all field mappings.

        Args:
            connection_id: Optional connection ID to filter by

        Returns:
            List[Dict[str, Any]]: List of mappings

        Raises:
            DatabaseError: If operation fails
        """
        if not self._is_initialized:
            raise DatabaseError(
                message="Field mapper not initialized",
                details={}
            )

        try:
            if connection_id:
                mapping_sql = """
                              SELECT * \
                              FROM db_field_mappings
                              WHERE connection_id = :connection_id
                              ORDER BY table_name \
                              """
                params = {"connection_id": connection_id}
            else:
                mapping_sql = """
                              SELECT * \
                              FROM db_field_mappings
                              ORDER BY connection_id, table_name \
                              """
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

                    entries_sql = """
                                  SELECT original_field, mapped_field \
                                  FROM db_field_mapping_entries
                                  WHERE mapping_id = :mapping_id \
                                  """

                    entries_result = await session.execute(
                        text(entries_sql),
                        {"mapping_id": mapping_id}
                    )
                    entries_rows = entries_result.fetchall()

                    field_mappings = {row[0]: row[1] for row in entries_rows}

                    mappings.append({
                        "id": mapping_id,
                        "connection_id": connection_id,
                        "table_name": table_name,
                        "description": description,
                        "mappings": field_mappings,
                        "created_at": created_at,
                        "updated_at": updated_at
                    })

            return mappings

        except Exception as e:
            self._logger.error(f"Failed to get field mappings: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get field mappings: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def apply_mapping_to_query(
            self,
            query: str,
            mapping: Dict[str, Any]
    ) -> str:
        """Apply a mapping to a SQL query.

        Args:
            query: The SQL query
            mapping: The field mapping

        Returns:
            str: The modified query with field mappings applied
        """
        mappings = mapping.get("mappings", {})
        table_name = mapping.get("table_name", "")

        # If query is just the table name, expand it to SELECT with mapped fields
        if query.strip() == table_name:
            return self._expand_table_to_query(query, mappings)

        # If query is a SELECT *, replace the * with mapped fields
        if re.search(r'SELECT\s+\*\s+FROM', query, re.IGNORECASE):
            return self._replace_select_star(query, table_name, mappings)

        # For other queries, add AS clauses for mapped fields
        return self._add_as_clauses(query, mappings)

    def _expand_table_to_query(self, table_name: str, mappings: Dict[str, str]) -> str:
        """Expand a table name to a SELECT query with mapped fields.

        Args:
            table_name: The table name
            mappings: The field mappings

        Returns:
            str: The expanded query
        """
        field_clauses = []

        for orig_name, mapped_name in mappings.items():
            if orig_name != mapped_name:
                field_clauses.append(f'"{orig_name}" AS "{mapped_name}"')
            else:
                field_clauses.append(f'"{orig_name}"')

        return f"SELECT {', '.join(field_clauses)} FROM {table_name}"

    def _replace_select_star(
            self,
            query: str,
            table_name: str,
            mappings: Dict[str, str]
    ) -> str:
        """Replace a SELECT * with mapped fields.

        Args:
            query: The SQL query
            table_name: The table name
            mappings: The field mappings

        Returns:
            str: The modified query
        """
        match = re.search(r'FROM\s+(.+)', query, re.IGNORECASE | re.DOTALL)

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
        """Add AS clauses to a query for mapped fields.

        Args:
            query: The SQL query
            mappings: The field mappings

        Returns:
            str: The modified query
        """
        match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)

        if not match:
            return query

        select_clause = match.group(1)
        fields = [f.strip() for f in select_clause.split(',')]
        new_fields = []

        for field in fields:
            # Skip fields that already have AS clauses
            if ' AS ' in field.upper() or ' as ' in field:
                new_fields.append(field)
                continue

            # Skip expressions
            if '(' in field or '+' in field or '-' in field or '*' in field or '/' in field:
                new_fields.append(field)
                continue

            # Handle qualified fields (with table name)
            if '.' in field:
                parts = field.split('.')
                table = parts[0].strip('"[]`')
                field_name = parts[1].strip('"[]`')

                if field_name in mappings and mappings[field_name] != field_name:
                    new_fields.append(f'{parts[0]}.{field_name} AS "{mappings[field_name]}"')
                else:
                    new_fields.append(field)
                continue

            # Handle simple fields
            field_name = field.strip('"[]`')

            if field_name in mappings and mappings[field_name] != field_name:
                new_fields.append(f'{field_name} AS "{mappings[field_name]}"')
            else:
                new_fields.append(field)

        new_select_clause = ', '.join(new_fields)

        return query.replace(select_clause, new_select_clause)

    async def apply_mapping_to_results(
            self,
            result: Dict[str, Any],
            mapping: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a mapping to query results.

        Args:
            result: The query result
            mapping: The field mapping

        Returns:
            Dict[str, Any]: The modified result with mapped field names
        """
        mappings = mapping.get("mappings", {})

        if not mappings:
            return result

        # Create field map from column names to mapped names
        field_map = {}
        for column in result.get("columns", []):
            col_name = column.get("name", "")
            if col_name in mappings:
                field_map[col_name] = mappings[col_name]
            else:
                field_map[col_name] = col_name

        # Map records
        mapped_records = []
        for record in result.get("records", []):
            mapped_record = {}
            for field_name, value in record.items():
                mapped_field = field_map.get(field_name, field_name)
                mapped_record[mapped_field] = value
            mapped_records.append(mapped_record)

        # Map columns
        mapped_columns = []
        for column in result.get("columns", []):
            col_name = column.get("name", "")
            mapped_name = field_map.get(col_name, col_name)

            mapped_column = dict(column)
            mapped_column["name"] = mapped_name
            mapped_columns.append(mapped_column)

        # Create new result with mapped data
        mapped_result = dict(result)
        mapped_result["records"] = mapped_records
        mapped_result["columns"] = mapped_columns
        mapped_result["mapped_fields"] = field_map

        return mapped_result

    async def shutdown(self) -> None:
        """Shut down the field mapper system."""
        self._is_initialized = False
        self._logger.info("Field mapper shut down")


# Standalone functions for simpler API access

def standardize_field_name(field_name: str) -> str:
    """Convert a field name to a standardized format.

    This converts camelCase or other formats to snake_case.

    Args:
        field_name: The original field name

    Returns:
        str: The standardized field name
    """
    return FieldMapperManager.standardize_field_name(field_name)