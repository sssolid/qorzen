from __future__ import annotations
'\nField mapping utilities for the Database Connector Plugin.\n\nThis module provides utilities for creating and applying field mappings\nbetween database tables and standardized field names.\n'
import re
from typing import Any, Dict, List, Optional, Tuple, Set, Union, cast
from ..models import FieldMapping, QueryResult
def create_mapping_from_fields(connection_id: str, table_name: str, field_names: List[str], description: Optional[str]=None) -> FieldMapping:
    mappings: Dict[str, str] = {}
    for field in field_names:
        standardized = standardize_field_name(field)
        mappings[field] = standardized
    return FieldMapping(connection_id=connection_id, table_name=table_name, description=description, mappings=mappings)
def standardize_field_name(field_name: str) -> str:
    name = re.sub('[^\\w\\s]', '', field_name)
    name = re.sub('\\s+', '_', name)
    name = re.sub('([a-z0-9])([A-Z])', '\\1_\\2', name)
    name = name.lower()
    name = re.sub('_+', '_', name)
    name = name.strip('_')
    return name
def apply_mapping_to_query(query: str, mapping: FieldMapping) -> str:
    if query.strip() == mapping.table_name:
        return _expand_table_to_query(query, mapping)
    if re.search('SELECT\\s+\\*\\s+FROM', query, re.IGNORECASE):
        return _replace_select_star(query, mapping)
    return _add_as_clauses(query, mapping)
def apply_mapping_to_results(result: QueryResult, mapping: FieldMapping) -> QueryResult:
    mapped_records: List[Dict[str, Any]] = []
    field_map = {col.name: mapping.mappings.get(col.name, col.name) for col in result.columns}
    for record in result.records:
        mapped_record: Dict[str, Any] = {}
        for field_name, value in record.items():
            mapped_field = field_map.get(field_name, field_name)
            mapped_record[mapped_field] = value
        mapped_records.append(mapped_record)
    result.mapped_records = mapped_records
    return result
def _expand_table_to_query(table_name: str, mapping: FieldMapping) -> str:
    field_clauses = []
    for orig_name, mapped_name in mapping.mappings.items():
        if orig_name != mapped_name:
            field_clauses.append(f'"{orig_name}" AS "{mapped_name}"')
        else:
            field_clauses.append(f'"{orig_name}"')
    return f"SELECT {', '.join(field_clauses)} FROM {table_name}"
def _replace_select_star(query: str, mapping: FieldMapping) -> str:
    match = re.search('FROM\\s+(.+)', query, re.IGNORECASE | re.DOTALL)
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
def _add_as_clauses(query: str, mapping: FieldMapping) -> str:
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
            if field_name in mapping.mappings and mapping.mappings[field_name] != field_name:
                new_fields.append(f'{parts[0]}.{field_name} AS "{mapping.mappings[field_name]}"')
            else:
                new_fields.append(field)
            continue
        field_name = field.strip('"[]`')
        if field_name in mapping.mappings and mapping.mappings[field_name] != field_name:
            new_fields.append(f'{field_name} AS "{mapping.mappings[field_name]}"')
        else:
            new_fields.append(field)
    new_select_clause = ', '.join(new_fields)
    return query.replace(select_clause, new_select_clause)