#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Field mapping utilities for the Database Connector Plugin.

This module provides utilities for creating and applying field mappings
between database tables and standardized field names.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Set, Union, cast

from ..models import FieldMapping, QueryResult


def create_mapping_from_fields(
        connection_id: str,
        table_name: str,
        field_names: List[str],
        description: Optional[str] = None
) -> FieldMapping:
    """
    Create a new field mapping for a table.

    Args:
        connection_id: Database connection ID
        table_name: Table name
        field_names: List of field names
        description: Optional description

    Returns:
        FieldMapping object with default mappings
    """
    # Create default mappings (field_name -> standardized_name)
    mappings: Dict[str, str] = {}

    for field in field_names:
        # Generate a standardized field name (snake_case)
        standardized = standardize_field_name(field)
        mappings[field] = standardized

    return FieldMapping(
        connection_id=connection_id,
        table_name=table_name,
        description=description,
        mappings=mappings
    )


def standardize_field_name(field_name: str) -> str:
    """
    Convert a field name to standardized format (snake_case).

    Args:
        field_name: Original field name

    Returns:
        Standardized field name
    """
    # Remove any non-alphanumeric characters except underscores
    name = re.sub(r'[^\w\s]', '', field_name)

    # Replace any whitespace with underscores
    name = re.sub(r'\s+', '_', name)

    # Handle camelCase or PascalCase
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)

    # Convert to lowercase
    name = name.lower()

    # Remove any duplicate underscores
    name = re.sub(r'_+', '_', name)

    # Remove leading or trailing underscores
    name = name.strip('_')

    return name


def apply_mapping_to_query(
        query: str,
        mapping: FieldMapping
) -> str:
    """
    Apply field mapping to a SQL query by transforming SELECT * or
    adding AS clauses to field references.

    Args:
        query: Original SQL query
        mapping: Field mapping to apply

    Returns:
        Transformed SQL query with mapped fields
    """
    # If it's a simple table query, expand it with mappings
    if query.strip() == mapping.table_name:
        return _expand_table_to_query(query, mapping)

    # For 'SELECT * FROM...' queries, replace * with mapped fields
    if re.search(r'SELECT\s+\*\s+FROM', query, re.IGNORECASE):
        return _replace_select_star(query, mapping)

    # For other queries, try to add AS clauses for mapped fields
    return _add_as_clauses(query, mapping)


def apply_mapping_to_results(
        result: QueryResult,
        mapping: FieldMapping
) -> QueryResult:
    """
    Apply field mapping to query results.

    Args:
        result: Original query result
        mapping: Field mapping to apply

    Returns:
        New query result with mapped field names
    """
    # Create a copy of the result to avoid modifying the original
    mapped_records: List[Dict[str, Any]] = []

    # Create a mapping from original field names to mapped field names
    # Some columns might not be in the mapping, so keep those unchanged
    field_map = {col.name: mapping.mappings.get(col.name, col.name) for col in result.columns}

    # Apply the mapping to each record
    for record in result.records:
        mapped_record: Dict[str, Any] = {}
        for field_name, value in record.items():
            mapped_field = field_map.get(field_name, field_name)
            mapped_record[mapped_field] = value
        mapped_records.append(mapped_record)

    # Store the mapped records in the result
    result.mapped_records = mapped_records

    return result


def _expand_table_to_query(table_name: str, mapping: FieldMapping) -> str:
    """
    Expand a simple table name to a full SELECT query with mapped fields.

    Args:
        table_name: Table name
        mapping: Field mapping

    Returns:
        Full SELECT query with mapped fields
    """
    field_clauses = []

    for orig_name, mapped_name in mapping.mappings.items():
        if orig_name != mapped_name:
            field_clauses.append(f'"{orig_name}" AS "{mapped_name}"')
        else:
            field_clauses.append(f'"{orig_name}"')

    return f'SELECT {", ".join(field_clauses)} FROM {table_name}'


def _replace_select_star(query: str, mapping: FieldMapping) -> str:
    """
    Replace 'SELECT * FROM...' with a full list of mapped fields.

    Args:
        query: Original query with SELECT *
        mapping: Field mapping

    Returns:
        Query with * replaced by mapped fields
    """
    # Extract the 'FROM' part and everything after it
    match = re.search(r'FROM\s+(.+)', query, re.IGNORECASE | re.DOTALL)
    if not match:
        return query  # Shouldn't happen if there's a valid 'SELECT * FROM...'

    from_clause = match.group(1)

    # Create the field list with mappings
    field_clauses = []
    for orig_name, mapped_name in mapping.mappings.items():
        if orig_name != mapped_name:
            field_clauses.append(f'"{orig_name}" AS "{mapped_name}"')
        else:
            field_clauses.append(f'"{orig_name}"')

    return f'SELECT {", ".join(field_clauses)} FROM {from_clause}'


def _add_as_clauses(query: str, mapping: FieldMapping) -> str:
    """
    Add AS clauses to field references in a SELECT query.
    This is a more complex transformation that attempts to modify
    field references throughout the query.

    Args:
        query: Original SQL query
        mapping: Field mapping

    Returns:
        Transformed SQL query with mapped fields
    """
    # This is a simplified implementation that only handles basic SELECT queries
    # A full implementation would need to parse the SQL and transform it properly

    # For now, we'll focus on the SELECT clause only
    match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
    if not match:
        return query  # Not a standard SELECT query

    select_clause = match.group(1)
    fields = [f.strip() for f in select_clause.split(',')]

    # Transform each field reference
    new_fields = []
    for field in fields:
        # Check if it's already mapped or has an AS clause
        if ' AS ' in field.upper() or ' as ' in field:
            new_fields.append(field)
            continue

        # Check if it's a function or expression
        if '(' in field or '+' in field or '-' in field or '*' in field or '/' in field:
            new_fields.append(field)
            continue

        # Check if it's a qualified field (table.field)
        if '.' in field:
            parts = field.split('.')
            table = parts[0].strip('"[]`')
            field_name = parts[1].strip('"[]`')

            if field_name in mapping.mappings and mapping.mappings[field_name] != field_name:
                new_fields.append(f'{parts[0]}.{field_name} AS "{mapping.mappings[field_name]}"')
            else:
                new_fields.append(field)
            continue

        # Simple field reference
        field_name = field.strip('"[]`')
        if field_name in mapping.mappings and mapping.mappings[field_name] != field_name:
            new_fields.append(f'{field_name} AS "{mapping.mappings[field_name]}"')
        else:
            new_fields.append(field)

    # Reconstruct the query
    new_select_clause = ', '.join(new_fields)
    return query.replace(select_clause, new_select_clause)