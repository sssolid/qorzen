"""
Query service for the Database Connector Plugin.

This module provides functionality for executing database queries,
formatting SQL, and managing query execution state.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from qorzen.utils.exceptions import DatabaseError


class QueryService:
    """
    Service for executing and managing database queries.

    Provides functionality for query execution, SQL formatting,
    query validation, and execution state management.
    """

    def __init__(self, database_manager: Any, logger: logging.Logger) -> None:
        """
        Initialize the query service.

        Args:
            database_manager: The database manager instance
            logger: Logger instance
        """
        self._database_manager = database_manager
        self._logger = logger

    async def execute_query(
            self,
            connection_name: str,
            query: str,
            parameters: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            apply_mapping: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a database query.

        Args:
            connection_name: The connection name to use
            query: The SQL query to execute
            parameters: Query parameters
            limit: Row limit for results
            apply_mapping: Whether to apply field mappings

        Returns:
            Query execution results

        Raises:
            DatabaseError: If query execution fails
        """
        try:
            self._logger.debug(f"Executing query on connection '{connection_name}'")

            # Validate query
            self._validate_query(query)

            # Execute query through database manager
            result = await self._database_manager.execute_query(
                query=query,
                params=parameters,
                connection_name=connection_name,
                limit=limit,
                apply_mapping=apply_mapping
            )

            self._logger.info(
                f"Query executed successfully: {result.get('row_count', 0)} rows in "
                f"{result.get('execution_time_ms', 0)}ms"
            )

            return result

        except Exception as e:
            self._logger.error(f"Query execution failed: {e}")
            raise DatabaseError(f"Query execution failed: {e}") from e

    async def get_tables(
            self,
            connection_name: str,
            schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tables from a database connection.

        Args:
            connection_name: The connection name
            schema: Optional schema name

        Returns:
            List of table information
        """
        try:
            return await self._database_manager.get_tables(connection_name, schema)
        except Exception as e:
            self._logger.error(f"Failed to get tables: {e}")
            raise DatabaseError(f"Failed to get tables: {e}") from e

    async def get_table_columns(
            self,
            connection_name: str,
            table_name: str,
            schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get columns from a database table.

        Args:
            connection_name: The connection name
            table_name: The table name
            schema: Optional schema name

        Returns:
            List of column information
        """
        try:
            return await self._database_manager.get_table_columns(
                table_name, connection_name, schema
            )
        except Exception as e:
            self._logger.error(f"Failed to get table columns: {e}")
            raise DatabaseError(f"Failed to get table columns: {e}") from e

    def _validate_query(self, query: str) -> None:
        """
        Validate a SQL query for basic safety.

        Args:
            query: The SQL query to validate

        Raises:
            ValueError: If query is invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Remove comments and normalize whitespace
        cleaned_query = self._clean_query(query)

        # Check for dangerous operations (basic safety check)
        dangerous_keywords = [
            r'\bDROP\s+DATABASE\b',
            r'\bDROP\s+SCHEMA\b',
            r'\bTRUNCATE\s+TABLE\b',
            r'\bDELETE\s+FROM\s+\w+\s*(?:WHERE\s+1\s*=\s*1|$)',  # DELETE without WHERE or WHERE 1=1
            r'\bUPDATE\s+\w+\s+SET\s+.*(?:WHERE\s+1\s*=\s*1|$)',  # UPDATE without WHERE or WHERE 1=1
        ]

        for pattern in dangerous_keywords:
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                raise ValueError(f"Potentially dangerous query detected: {pattern}")

    def _clean_query(self, query: str) -> str:
        """
        Clean a SQL query by removing comments and normalizing whitespace.

        Args:
            query: The SQL query to clean

        Returns:
            Cleaned query
        """
        # Remove single-line comments (-- comment)
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)

        # Remove multi-line comments (/* comment */)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)

        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()

        return query

    def format_sql(self, query: str) -> str:
        """
        Format a SQL query for better readability.

        Args:
            query: The SQL query to format

        Returns:
            Formatted SQL query
        """
        try:
            # Basic SQL formatting
            query = query.strip()

            # Keywords to format
            keywords = [
                'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER JOIN', 'LEFT JOIN',
                'RIGHT JOIN', 'FULL JOIN', 'ON', 'GROUP BY', 'HAVING',
                'ORDER BY', 'LIMIT', 'OFFSET', 'UNION', 'UNION ALL',
                'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
                'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE',
                'IS NULL', 'IS NOT NULL', 'AS', 'DISTINCT', 'COUNT',
                'SUM', 'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
            ]

            # Add line breaks before major keywords
            major_keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY']
            for keyword in major_keywords:
                # Add newline before keyword (but not at the start)
                pattern = rf'(?<!^)\s+({re.escape(keyword)})\b'
                query = re.sub(pattern, r'\n\1', query, flags=re.IGNORECASE)

            # Format JOIN clauses
            join_keywords = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']
            for join in join_keywords:
                pattern = rf'\s+({re.escape(join)})\b'
                query = re.sub(pattern, r'\n\1', query, flags=re.IGNORECASE)

            # Add proper indentation
            lines = query.split('\n')
            formatted_lines = []
            indent_level = 0

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Decrease indent for closing parentheses
                if line.startswith(')'):
                    indent_level = max(0, indent_level - 1)

                # Add indentation
                if line.upper().startswith(('SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY')):
                    formatted_lines.append(line)
                elif line.upper().startswith(('JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN')):
                    formatted_lines.append('    ' + line)
                elif line.upper().startswith('ON'):
                    formatted_lines.append('        ' + line)
                else:
                    formatted_lines.append('    ' * indent_level + line)

                # Increase indent for opening parentheses
                if line.endswith('('):
                    indent_level += 1

            return '\n'.join(formatted_lines)

        except Exception as e:
            self._logger.warning(f"Failed to format SQL: {e}")
            return query  # Return original if formatting fails

    def extract_table_names(self, query: str) -> List[str]:
        """
        Extract table names from a SQL query.

        Args:
            query: The SQL query

        Returns:
            List of table names found in the query
        """
        try:
            table_names = []
            cleaned_query = self._clean_query(query)

            # Pattern to match table names after FROM, JOIN, UPDATE, INSERT INTO, DELETE FROM
            patterns = [
                r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, cleaned_query, re.IGNORECASE)
                table_names.extend(matches)

            # Remove duplicates and clean up
            unique_tables = list(set(table_names))

            # Remove schema prefixes for simplicity (keep just table name)
            clean_tables = []
            for table in unique_tables:
                if '.' in table:
                    clean_tables.append(table.split('.')[-1])
                else:
                    clean_tables.append(table)

            return list(set(clean_tables))  # Remove duplicates again

        except Exception as e:
            self._logger.warning(f"Failed to extract table names: {e}")
            return []

    def get_query_type(self, query: str) -> str:
        """
        Determine the type of SQL query.

        Args:
            query: The SQL query

        Returns:
            Query type (SELECT, INSERT, UPDATE, DELETE, etc.)
        """
        try:
            cleaned_query = self._clean_query(query).upper()

            # Check for common query types
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
            self._logger.warning(f"Failed to determine query type: {e}")
            return 'UNKNOWN'

    def is_read_only_query(self, query: str) -> bool:
        """
        Check if a query is read-only (doesn't modify data).

        Args:
            query: The SQL query

        Returns:
            True if query is read-only
        """
        try:
            query_type = self.get_query_type(query)
            read_only_types = ['SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN']
            return query_type in read_only_types
        except Exception:
            return False

    def estimate_result_size(self, query: str) -> str:
        """
        Provide a rough estimate of result size based on query structure.

        Args:
            query: The SQL query

        Returns:
            Size estimate description
        """
        try:
            cleaned_query = self._clean_query(query).upper()

            # Check for LIMIT clause
            limit_match = re.search(r'\bLIMIT\s+(\d+)', cleaned_query)
            if limit_match:
                limit_value = int(limit_match.group(1))
                if limit_value <= 100:
                    return "Small (< 100 rows)"
                elif limit_value <= 1000:
                    return "Medium (< 1,000 rows)"
                else:
                    return f"Large (~{limit_value:,} rows)"

            # Check for aggregation functions
            if re.search(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', cleaned_query):
                return "Small (aggregated)"

            # Check for GROUP BY
            if 'GROUP BY' in cleaned_query:
                return "Medium (grouped)"

            # Check for WHERE clause
            if 'WHERE' in cleaned_query:
                return "Medium (filtered)"

            # No filtering or limiting
            return "Unknown (potentially large)"

        except Exception as e:
            self._logger.warning(f"Failed to estimate result size: {e}")
            return "Unknown"

    def suggest_query_improvements(self, query: str) -> List[str]:
        """
        Suggest improvements for a SQL query.

        Args:
            query: The SQL query

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        try:
            cleaned_query = self._clean_query(query).upper()

            # Check for SELECT *
            if re.search(r'\bSELECT\s+\*', cleaned_query):
                suggestions.append("Consider specifying exact columns instead of SELECT *")

            # Check for missing LIMIT
            if cleaned_query.startswith('SELECT') and 'LIMIT' not in cleaned_query:
                suggestions.append("Consider adding a LIMIT clause to prevent large result sets")

            # Check for potentially dangerous WHERE clauses
            if re.search(r'\bWHERE\s+1\s*=\s*1\b', cleaned_query):
                suggestions.append("WHERE 1=1 condition may return all rows - verify this is intended")

            # Check for missing WHERE in UPDATE/DELETE
            if cleaned_query.startswith(('UPDATE', 'DELETE')) and 'WHERE' not in cleaned_query:
                suggestions.append("UPDATE/DELETE without WHERE clause will affect all rows")

            # Check for LIKE without wildcards
            like_matches = re.findall(r"\bLIKE\s+'([^']*)'", cleaned_query)
            for match in like_matches:
                if '%' not in match and '_' not in match:
                    suggestions.append(f"LIKE '{match}' can be replaced with = '{match}' for better performance")

            # Check for ORDER BY without LIMIT
            if 'ORDER BY' in cleaned_query and 'LIMIT' not in cleaned_query:
                suggestions.append("ORDER BY without LIMIT may sort unnecessary rows")

        except Exception as e:
            self._logger.warning(f"Failed to generate suggestions: {e}")

        return suggestions

    async def test_connection(self, connection_name: str) -> bool:
        """
        Test if a database connection is working.

        Args:
            connection_name: The connection name to test

        Returns:
            True if connection is working
        """
        try:
            return await self._database_manager.check_connection(connection_name)
        except Exception as e:
            self._logger.error(f"Connection test failed: {e}")
            return False