from __future__ import annotations

"""
Field mapping utilities for the Database Connector Plugin.

This module provides utilities for creating and applying field mappings
between database tables and standardized field names.
"""
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from ..models import FieldMapping, QueryResult


class FieldMappingManager:
    """Manager for creating and applying field mappings between database tables and standardized field names."""

    def __init__(self, database_manager: Optional[Any] = None, logger: Optional[Any] = None) -> None:
        """Initialize the field mapping manager.

        Args:
            database_manager: Database manager for database operations
            logger: Logger for logging messages
        """
        self._db_manager = database_manager
        self._logger = logger

    def create_mapping_from_fields(
            self, connection_id: str, table_name: str, field_names: List[str],
            description: Optional[str] = None
    ) -> FieldMapping:
        """Create a field mapping from a list of field names.

        Args:
            connection_id: ID of the database connection
            table_name: Name of the database table
            field_names: List of field names to map
            description: Optional description of the mapping

        Returns:
            A new FieldMapping object
        """
        mappings: Dict[str, str] = {}
        for field in field_names:
            standardized = self.standardize_field_name(field)
            mappings[field] = standardized

        return FieldMapping(
            connection_id=connection_id,
            table_name=table_name,
            description=description,
            mappings=mappings
        )

    @staticmethod
    def standardize_field_name(field_name: str) -> str:
        """Standardize a field name by converting to snake_case and lowercase.

        Args:
            field_name: Original field name

        Returns:
            Standardized field name
        """
        name = re.sub(r'[^\w\s]', '', field_name)
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
        name = name.lower()
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')
        return name

    def apply_mapping_to_query(self, query: str, mapping: FieldMapping) -> str:
        """Apply field mapping to a SQL query.

        Args:
            query: SQL query to transform
            mapping: Field mapping to apply

        Returns:
            Transformed SQL query with mapped field names
        """
        if query.strip() == mapping.table_name:
            return self._expand_table_to_query(query, mapping)

        if re.search(r'SELECT\s+\*\s+FROM', query, re.IGNORECASE):
            return self._replace_select_star(query, mapping)

        return self._add_as_clauses(query, mapping)

    def apply_mapping_to_results(self, result: QueryResult, mapping: FieldMapping) -> QueryResult:
        """Apply field mapping to query results.

        Args:
            result: Query result to transform
            mapping: Field mapping to apply

        Returns:
            Transformed query result with mapped field names
        """
        mapped_records: List[Dict[str, Any]] = []
        field_map = {
            col.name: mapping.mappings.get(col.name, col.name)
            for col in result.columns
        }

        for record in result.records:
            mapped_record: Dict[str, Any] = {}
            for field_name, value in record.items():
                mapped_field = field_map.get(field_name, field_name)
                mapped_record[mapped_field] = value
            mapped_records.append(mapped_record)

        result.mapped_records = mapped_records
        return result

    def _expand_table_to_query(self, table_name: str, mapping: FieldMapping) -> str:
        """Expand a table name to a full query with field mappings.

        Args:
            table_name: Table name
            mapping: Field mapping to apply

        Returns:
            Expanded SQL query
        """
        field_clauses = []
        for orig_name, mapped_name in mapping.mappings.items():
            if orig_name != mapped_name:
                field_clauses.append(f'"{orig_name}" AS "{mapped_name}"')
            else:
                field_clauses.append(f'"{orig_name}"')

        return f"SELECT {', '.join(field_clauses)} FROM {table_name}"

    def _replace_select_star(self, query: str, mapping: FieldMapping) -> str:
        """Replace SELECT * with explicit column references and mapping.

        Args:
            query: SQL query containing SELECT *
            mapping: Field mapping to apply

        Returns:
            SQL query with explicit column mappings
        """
        match = re.search(r'FROM\s+(.+)', query, re.IGNORECASE | re.DOTALL)
        if not match:
            return query

        from_clause = match.group(1)
        field_clauses = []

        for orig_name, mapped_name in mapping.mappings.items():
            if orig_name != mapped_name:
                field_clauses.append(f'"{orig_name}" AS "{mapped_name}"')
            else:
                field_clauses.append(f'"{orig_name}"')

        return f"SELECT {', '.join(field_clauses)} FROM {from_clause}"

    def _add_as_clauses(self, query: str, mapping: FieldMapping) -> str:
        """Add AS clauses to field references in a SELECT query.

        Args:
            query: SQL query
            mapping: Field mapping to apply

        Returns:
            SQL query with added AS clauses
        """
        match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
        if not match:
            return query

        select_clause = match.group(1)
        fields = [f.strip() for f in select_clause.split(',')]
        new_fields = []

        for field in fields:
            # Skip fields already having AS clauses
            if ' AS ' in field.upper() or ' as ' in field:
                new_fields.append(field)
                continue

            # Skip expressions and functions
            if '(' in field or '+' in field or '-' in field or ('*' in field) or ('/' in field):
                new_fields.append(field)
                continue

            # Handle qualified fields (table.field)
            if '.' in field:
                parts = field.split('.')
                table = parts[0].strip('"[]`')
                field_name = parts[1].strip('"[]`')

                if field_name in mapping.mappings and mapping.mappings[field_name] != field_name:
                    new_fields.append(f'{parts[0]}.{field_name} AS "{mapping.mappings[field_name]}"')
                else:
                    new_fields.append(field)
                continue

            # Handle regular fields
            field_name = field.strip('"[]`')
            if field_name in mapping.mappings and mapping.mappings[field_name] != field_name:
                new_fields.append(f'{field_name} AS "{mapping.mappings[field_name]}"')
            else:
                new_fields.append(field)

        new_select_clause = ', '.join(new_fields)
        return query.replace(select_clause, new_select_clause)


# Create standalone functions that delegate to the FieldMappingManager for backward compatibility
_default_manager = FieldMappingManager()


def create_mapping_from_fields(
        connection_id: str, table_name: str, field_names: List[str],
        description: Optional[str] = None
) -> FieldMapping:
    """Create a field mapping from a list of field names.

    This is a backward-compatibility function that delegates to FieldMappingManager.

    Args:
        connection_id: ID of the database connection
        table_name: Name of the database table
        field_names: List of field names to map
        description: Optional description of the mapping

    Returns:
        A new FieldMapping object
    """
    return _default_manager.create_mapping_from_fields(
        connection_id=connection_id,
        table_name=table_name,
        field_names=field_names,
        description=description
    )


def standardize_field_name(field_name: str) -> str:
    """Standardize a field name by converting to snake_case and lowercase.

    This is a backward-compatibility function that delegates to FieldMappingManager.

    Args:
        field_name: Original field name

    Returns:
        Standardized field name
    """
    return FieldMappingManager.standardize_field_name(field_name)


def apply_mapping_to_query(query: str, mapping: FieldMapping) -> str:
    """Apply field mapping to a SQL query.

    This is a backward-compatibility function that delegates to FieldMappingManager.

    Args:
        query: SQL query to transform
        mapping: Field mapping to apply

    Returns:
        Transformed SQL query with mapped field names
    """
    return _default_manager.apply_mapping_to_query(query, mapping)


def apply_mapping_to_results(result: QueryResult, mapping: FieldMapping) -> QueryResult:
    """Apply field mapping to query results.

    This is a backward-compatibility function that delegates to FieldMappingManager.

    Args:
        result: Query result to transform
        mapping: Field mapping to apply

    Returns:
        Transformed query result with mapped field names
    """
    return _default_manager.apply_mapping_to_results(result, mapping)


# Expose the private methods for backward compatibility
def _expand_table_to_query(table_name: str, mapping: FieldMapping) -> str:
    return _default_manager._expand_table_to_query(table_name, mapping)


def _replace_select_star(query: str, mapping: FieldMapping) -> str:
    return _default_manager._replace_select_star(query, mapping)


def _add_as_clauses(query: str, mapping: FieldMapping) -> str:
    return _default_manager._add_as_clauses(query, mapping)