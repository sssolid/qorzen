from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Optional
from qorzen.utils.exceptions import DatabaseError
class QueryService:
    def __init__(self, database_manager: Any, logger: logging.Logger) -> None:
        self._database_manager = database_manager
        self._logger = logger
    async def execute_query(self, connection_name: str, query: str, parameters: Optional[Dict[str, Any]]=None, limit: Optional[int]=None, apply_mapping: bool=False) -> Dict[str, Any]:
        try:
            self._logger.debug(f"Executing query on connection '{connection_name}'")
            self._validate_query(query)
            result = await self._database_manager.execute_query(query=query, params=parameters, connection_name=connection_name, limit=limit, apply_mapping=apply_mapping)
            self._logger.info(f"Query executed successfully: {result.get('row_count', 0)} rows in {result.get('execution_time_ms', 0)}ms")
            return result
        except Exception as e:
            self._logger.error(f'Query execution failed: {e}')
            raise DatabaseError(f'Query execution failed: {e}') from e
    async def get_tables(self, connection_name: str, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        try:
            return await self._database_manager.get_tables(connection_name, schema)
        except Exception as e:
            self._logger.error(f'Failed to get tables: {e}')
            raise DatabaseError(f'Failed to get tables: {e}') from e
    async def get_table_columns(self, connection_name: str, table_name: str, schema: Optional[str]=None) -> List[Dict[str, Any]]:
        try:
            return await self._database_manager.get_table_columns(table_name, connection_name, schema)
        except Exception as e:
            self._logger.error(f'Failed to get table columns: {e}')
            raise DatabaseError(f'Failed to get table columns: {e}') from e
    def _validate_query(self, query: str) -> None:
        if not query or not query.strip():
            raise ValueError('Query cannot be empty')
        cleaned_query = self._clean_query(query)
        dangerous_keywords = ['\\bDROP\\s+DATABASE\\b', '\\bDROP\\s+SCHEMA\\b', '\\bTRUNCATE\\s+TABLE\\b', '\\bDELETE\\s+FROM\\s+\\w+\\s*(?:WHERE\\s+1\\s*=\\s*1|$)', '\\bUPDATE\\s+\\w+\\s+SET\\s+.*(?:WHERE\\s+1\\s*=\\s*1|$)']
        for pattern in dangerous_keywords:
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                raise ValueError(f'Potentially dangerous query detected: {pattern}')
    def _clean_query(self, query: str) -> str:
        query = re.sub('--.*$', '', query, flags=re.MULTILINE)
        query = re.sub('/\\*.*?\\*/', '', query, flags=re.DOTALL)
        query = re.sub('\\s+', ' ', query).strip()
        return query
    def format_sql(self, query: str) -> str:
        try:
            query = query.strip()
            keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'ON', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT', 'OFFSET', 'UNION', 'UNION ALL', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS NULL', 'IS NOT NULL', 'AS', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END']
            major_keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY']
            for keyword in major_keywords:
                pattern = f'(?<!^)\\s+({re.escape(keyword)})\\b'
                query = re.sub(pattern, '\\n\\1', query, flags=re.IGNORECASE)
            join_keywords = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']
            for join in join_keywords:
                pattern = f'\\s+({re.escape(join)})\\b'
                query = re.sub(pattern, '\\n\\1', query, flags=re.IGNORECASE)
            lines = query.split('\n')
            formatted_lines = []
            indent_level = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(')'):
                    indent_level = max(0, indent_level - 1)
                if line.upper().startswith(('SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY')):
                    formatted_lines.append(line)
                elif line.upper().startswith(('JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN')):
                    formatted_lines.append('    ' + line)
                elif line.upper().startswith('ON'):
                    formatted_lines.append('        ' + line)
                else:
                    formatted_lines.append('    ' * indent_level + line)
                if line.endswith('('):
                    indent_level += 1
            return '\n'.join(formatted_lines)
        except Exception as e:
            self._logger.warning(f'Failed to format SQL: {e}')
            return query
    def extract_table_names(self, query: str) -> List[str]:
        try:
            table_names = []
            cleaned_query = self._clean_query(query)
            patterns = ['\\bFROM\\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\\.[a-zA-Z_][a-zA-Z0-9_]*)?)', '\\bJOIN\\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\\.[a-zA-Z_][a-zA-Z0-9_]*)?)', '\\bUPDATE\\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\\.[a-zA-Z_][a-zA-Z0-9_]*)?)', '\\bINSERT\\s+INTO\\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\\.[a-zA-Z_][a-zA-Z0-9_]*)?)', '\\bDELETE\\s+FROM\\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\\.[a-zA-Z_][a-zA-Z0-9_]*)?)']
            for pattern in patterns:
                matches = re.findall(pattern, cleaned_query, re.IGNORECASE)
                table_names.extend(matches)
            unique_tables = list(set(table_names))
            clean_tables = []
            for table in unique_tables:
                if '.' in table:
                    clean_tables.append(table.split('.')[-1])
                else:
                    clean_tables.append(table)
            return list(set(clean_tables))
        except Exception as e:
            self._logger.warning(f'Failed to extract table names: {e}')
            return []
    def get_query_type(self, query: str) -> str:
        try:
            cleaned_query = self._clean_query(query).upper()
            if cleaned_query.startswith('SELECT'):
                return 'SELECT'
            elif cleaned_query.startswith('INSERT'):
                return 'INSERT'
            elif cleaned_query.startswith('UPDATE'):
                return 'UPDATE'
            elif cleaned_query.startswith('DELETE'):
                return 'DELETE'
            elif cleaned_query.startswith('CREATE'):
                return 'CREATE'
            elif cleaned_query.startswith('ALTER'):
                return 'ALTER'
            elif cleaned_query.startswith('DROP'):
                return 'DROP'
            elif cleaned_query.startswith('TRUNCATE'):
                return 'TRUNCATE'
            elif cleaned_query.startswith('GRANT'):
                return 'GRANT'
            elif cleaned_query.startswith('REVOKE'):
                return 'REVOKE'
            elif cleaned_query.startswith('SHOW'):
                return 'SHOW'
            elif cleaned_query.startswith('DESCRIBE') or cleaned_query.startswith('DESC'):
                return 'DESCRIBE'
            elif cleaned_query.startswith('EXPLAIN'):
                return 'EXPLAIN'
            else:
                return 'UNKNOWN'
        except Exception as e:
            self._logger.warning(f'Failed to determine query type: {e}')
            return 'UNKNOWN'
    def is_read_only_query(self, query: str) -> bool:
        try:
            query_type = self.get_query_type(query)
            read_only_types = ['SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN']
            return query_type in read_only_types
        except Exception:
            return False
    def estimate_result_size(self, query: str) -> str:
        try:
            cleaned_query = self._clean_query(query).upper()
            limit_match = re.search('\\bLIMIT\\s+(\\d+)', cleaned_query)
            if limit_match:
                limit_value = int(limit_match.group(1))
                if limit_value <= 100:
                    return 'Small (< 100 rows)'
                elif limit_value <= 1000:
                    return 'Medium (< 1,000 rows)'
                else:
                    return f'Large (~{limit_value:,} rows)'
            if re.search('\\b(COUNT|SUM|AVG|MIN|MAX)\\s*\\(', cleaned_query):
                return 'Small (aggregated)'
            if 'GROUP BY' in cleaned_query:
                return 'Medium (grouped)'
            if 'WHERE' in cleaned_query:
                return 'Medium (filtered)'
            return 'Unknown (potentially large)'
        except Exception as e:
            self._logger.warning(f'Failed to estimate result size: {e}')
            return 'Unknown'
    def suggest_query_improvements(self, query: str) -> List[str]:
        suggestions = []
        try:
            cleaned_query = self._clean_query(query).upper()
            if re.search('\\bSELECT\\s+\\*', cleaned_query):
                suggestions.append('Consider specifying exact columns instead of SELECT *')
            if cleaned_query.startswith('SELECT') and 'LIMIT' not in cleaned_query:
                suggestions.append('Consider adding a LIMIT clause to prevent large result sets')
            if re.search('\\bWHERE\\s+1\\s*=\\s*1\\b', cleaned_query):
                suggestions.append('WHERE 1=1 condition may return all rows - verify this is intended')
            if cleaned_query.startswith(('UPDATE', 'DELETE')) and 'WHERE' not in cleaned_query:
                suggestions.append('UPDATE/DELETE without WHERE clause will affect all rows')
            like_matches = re.findall("\\bLIKE\\s+'([^']*)'", cleaned_query)
            for match in like_matches:
                if '%' not in match and '_' not in match:
                    suggestions.append(f"LIKE '{match}' can be replaced with = '{match}' for better performance")
            if 'ORDER BY' in cleaned_query and 'LIMIT' not in cleaned_query:
                suggestions.append('ORDER BY without LIMIT may sort unnecessary rows')
        except Exception as e:
            self._logger.warning(f'Failed to generate suggestions: {e}')
        return suggestions
    async def test_connection(self, connection_name: str) -> bool:
        try:
            return await self._database_manager.check_connection(connection_name)
        except Exception as e:
            self._logger.error(f'Connection test failed: {e}')
            return False