from __future__ import annotations

"""
Database diagnostics utility for InitialDB.

This module provides tools to diagnose database connection and query issues,
with comprehensive testing and reporting capabilities.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import structlog
from sqlalchemy import text, Table, select, Column, MetaData, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from ..config.settings import settings

logger = structlog.get_logger(__name__)


async def run_basic_connectivity_test(connection_string: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a basic connectivity test to check database connection.

    Args:
        connection_string: Optional connection string override

    Returns:
        Dict with test results including success flag, timings, and error info
    """
    if not connection_string:
        connection_string = settings.get("connection_string")
        if not connection_string:
            return {
                "success": False,
                "error": "No database connection string configured",
                "details": None
            }

    start_time = time.time()
    result = {
        "success": False,
        "connection_string": _mask_connection_string(connection_string),
        "timings": {},
        "error": None,
        "details": None
    }

    try:
        # Create engine with minimal pool for testing
        engine = create_async_engine(
            connection_string,
            echo=False,
            pool_size=1,
            max_overflow=0,
            pool_timeout=10.0,
            # connect_args={"timeout": 10.0},
        )

        engine_creation_time = time.time() - start_time
        result["timings"]["engine_creation"] = f"{engine_creation_time:.3f}s"

        # Test basic connection and simple query
        try:
            connection_start = time.time()
            async with engine.connect() as conn:
                connection_time = time.time() - connection_start
                result["timings"]["connection"] = f"{connection_time:.3f}s"

                # Execute simple query
                query_start = time.time()
                res = await conn.execute(text("SELECT 1 AS test"))
                row = res.fetchone()
                query_time = time.time() - query_start
                result["timings"]["simple_query"] = f"{query_time:.3f}s"

                if row and row[0] == 1:
                    result["success"] = True
                    result["details"] = "Basic connectivity test passed"
                else:
                    result["error"] = f"Unexpected result from basic query: {row}"
        except Exception as e:
            result["error"] = f"Connection test failed: {str(e)}"
            result["details"] = str(e)

        # Dispose engine to clean up resources
        await engine.dispose()

    except Exception as e:
        result["error"] = f"Error creating engine: {str(e)}"
        result["details"] = str(e)

    result["timings"]["total"] = f"{time.time() - start_time:.3f}s"
    return result


async def run_table_diagnostics(tables: List[str], connection_string: Optional[str] = None) -> Dict[str, Any]:
    """
    Run diagnostics on specific tables to check query performance.

    Args:
        tables: List of table names to test
        connection_string: Optional connection string override

    Returns:
        Dict with test results for each table
    """
    if not connection_string:
        connection_string = settings.get("connection_string")
        if not connection_string:
            return {"success": False, "error": "No database connection string configured"}

    result = {
        "success": False,
        "tables": {},
        "timings": {},
        "error": None
    }

    start_time = time.time()

    try:
        # Create engine with minimal pool for testing
        engine = create_async_engine(
            connection_string,
            echo=False,
            pool_size=1,
            max_overflow=0,
            pool_timeout=10.0,
            # connect_args={"timeout": 10.0},
        )

        # Test each table
        async with engine.connect() as conn:
            metadata = MetaData()

            def do_reflect(sync_conn):
                metadata.reflect(bind=sync_conn, only=tables)

            await conn.run_sync(do_reflect)

            for table_name in tables:
                table_result = {
                    "success": False,
                    "count": None,
                    "sample": None,
                    "error": None,
                    "timings": {}
                }

                try:
                    if table_name not in metadata.tables:
                        table_result["error"] = f"Table {table_name} not found in database"
                        result["tables"][table_name] = table_result
                        continue

                    table = metadata.tables[table_name]

                    # Count rows
                    count_start = time.time()
                    stmt = select(func.count()).select_from(table)
                    count_res = await conn.execute(stmt)
                    count = count_res.scalar()
                    table_result["count"] = count
                    table_result["timings"]["count_query"] = f"{time.time() - count_start:.3f}s"

                    # Fetch sample (first 5 rows)
                    sample_start = time.time()
                    stmt = select(table).limit(5)
                    sample_res = await conn.execute(stmt)
                    sample_rows = sample_res.fetchall()
                    table_result["timings"]["sample_query"] = f"{time.time() - sample_start:.3f}s"

                    # Format sample data
                    if sample_rows:
                        sample_data = []
                        for row in sample_rows:
                            sample_data.append(dict(row._mapping))
                        table_result["sample"] = sample_data

                    table_result["success"] = True

                except Exception as e:
                    table_result["error"] = str(e)

                result["tables"][table_name] = table_result

        # Only consider success if all tables were queried successfully
        result["success"] = all(table_result["success"] for table_result in result["tables"].values())

        # Dispose engine to clean up resources
        await engine.dispose()

    except Exception as e:
        result["error"] = f"Error running table diagnostics: {str(e)}"

    result["timings"]["total"] = f"{time.time() - start_time:.3f}s"
    return result


async def run_specific_query_test(query: str, params: Optional[Dict[str, Any]] = None,
                                  connection_string: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a specific SQL query and return timing and result information.

    Args:
        query: SQL query to execute (use :param syntax for parameters)
        params: Optional parameters for the query
        connection_string: Optional connection string override

    Returns:
        Dict with test results including success flag, timing, and result data
    """
    if not connection_string:
        connection_string = settings.get("connection_string")
        if not connection_string:
            return {"success": False, "error": "No database connection string configured"}

    result = {
        "success": False,
        "rowcount": 0,
        "results": None,
        "timings": {},
        "error": None
    }

    start_time = time.time()

    try:
        # Create engine with minimal pool for testing
        engine = create_async_engine(
            connection_string,
            echo=False,
            pool_size=1,
            max_overflow=0,
            pool_timeout=15.0,
            # connect_args={"timeout": 15.0},
        )

        # Execute the query
        async with engine.connect() as conn:
            query_start = time.time()
            res = await conn.execute(text(query), params or {})
            rows = res.fetchall()
            query_time = time.time() - query_start
            result["timings"]["query"] = f"{query_time:.3f}s"

            # Format results
            result["rowcount"] = len(rows)
            if rows:
                formatted_rows = []
                for row in rows:
                    formatted_rows.append(dict(row._mapping))
                result["results"] = formatted_rows[:10]  # Limit to first 10 rows

                if len(rows) > 10:
                    result["results_truncated"] = True

            result["success"] = True

        # Dispose engine to clean up resources
        await engine.dispose()

    except Exception as e:
        result["error"] = f"Error executing query: {str(e)}"

    result["timings"]["total"] = f"{time.time() - start_time:.3f}s"
    return result


def _mask_connection_string(conn_string: str) -> str:
    """
    Mask sensitive information in the connection string.

    Args:
        conn_string: The connection string to mask

    Returns:
        A masked version of the connection string
    """
    if '@' in conn_string:
        parts = conn_string.split('@')
        if ':' in parts[0]:
            auth_parts = parts[0].split(':')
            if len(auth_parts) > 2:
                auth_parts[-1] = '********'
                parts[0] = ':'.join(auth_parts)
                return '@'.join(parts)

    return conn_string


async def run_full_diagnostic_suite() -> Dict[str, Any]:
    """
    Run a full diagnostic suite on the database.

    Returns:
        Dict with comprehensive test results
    """
    result = {
        "connectivity": None,
        "key_tables": None,
        "year_query": None,
        "make_query": None,
        "submodel_query": None
    }

    # Test basic connectivity
    result["connectivity"] = await run_basic_connectivity_test()

    if not result["connectivity"]["success"]:
        # Skip further tests if basic connectivity fails
        return result

    # Test key tables
    result["key_tables"] = await run_table_diagnostics(["year", "make", "model", "sub_model"])

    # Test specific queries that are used for filters
    result["year_query"] = await run_specific_query_test(
        "SELECT year_id FROM vcdb.year ORDER BY year_id LIMIT 100"
    )

    result["make_query"] = await run_specific_query_test(
        "SELECT make_id, make_name FROM vcdb.make ORDER BY make_name LIMIT 100"
    )

    result["submodel_query"] = await run_specific_query_test(
        "SELECT DISTINCT s.sub_model_id, s.sub_model_name " +
        "FROM vcdb.sub_model s " +
        "JOIN vcdb.vehicle v ON v.sub_model_id = s.sub_model_id " +
        "LIMIT 100"
    )

    return result


# Convenience function to run diagnostics and print results
async def print_diagnostics():
    """Run database diagnostics and print formatted results."""
    print("Running database diagnostics...")
    results = await run_full_diagnostic_suite()

    # Print basic connectivity results
    conn = results["connectivity"]
    print("\n--- CONNECTIVITY TEST ---")
    print(f"Success: {conn['success']}")
    if conn["error"]:
        print(f"Error: {conn['error']}")
    print("Timings:")
    for timing_name, timing_value in conn.get("timings", {}).items():
        print(f"  {timing_name}: {timing_value}")

    # Only continue if connectivity succeeds
    if not conn["success"]:
        print("\nCould not connect to database. Please check your connection settings.")
        return

    # Print table test results
    print("\n--- TABLE TESTS ---")
    tables = results.get("key_tables", {}).get("tables", {})
    for table_name, table_result in tables.items():
        print(f"\nTable: {table_name}")
        print(f"  Success: {table_result['success']}")
        print(f"  Row count: {table_result['count']}")
        if table_result["error"]:
            print(f"  Error: {table_result['error']}")
        print("  Timings:")
        for timing_name, timing_value in table_result.get("timings", {}).items():
            print(f"    {timing_name}: {timing_value}")

    # Print query test results
    print("\n--- QUERY TESTS ---")
    for query_name in ["year_query", "make_query", "submodel_query"]:
        query_result = results.get(query_name, {})
        print(f"\n{query_name.replace('_', ' ').title()}:")
        print(f"  Success: {query_result.get('success', False)}")
        print(f"  Row count: {query_result.get('rowcount', 0)}")
        if query_result.get("error"):
            print(f"  Error: {query_result['error']}")
        print("  Timings:")
        for timing_name, timing_value in query_result.get("timings", {}).items():
            print(f"    {timing_name}: {timing_value}")

    print("\nDiagnostics complete.")


# Run diagnostics if this module is executed directly
if __name__ == "__main__":
    asyncio.run(print_diagnostics())