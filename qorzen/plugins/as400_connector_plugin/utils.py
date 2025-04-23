from __future__ import annotations

"""
Utility functions for the AS400 Connector Plugin.

This module provides helper functions for working with AS400 connections,
SQL queries, and other plugin-specific functionality.
"""

import os
import json
import re
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set, cast

from PySide6.QtCore import QSettings, QByteArray
from PySide6.QtGui import QColor

from qorzen.plugins.as400_connector_plugin.models import (
    AS400ConnectionConfig,
    SavedQuery,
    QueryHistoryEntry,
    PluginSettings,
)


def load_connections(file_manager: Any) -> Dict[str, AS400ConnectionConfig]:
    """
    Load saved AS400 connection configurations.

    Args:
        file_manager: Qorzen file manager for file operations

    Returns:
        Dictionary of connection configurations by ID
    """
    try:
        # Get the connections file path
        file_path = "as400_connector_plugin/connections.json"

        # Check if the file exists
        try:
            file_info = file_manager.get_file_info(file_path, "plugin_data")
            if not file_info:
                return {}
        except:
            return {}

        # Load the connections file
        json_data = file_manager.read_text(file_path, "plugin_data")
        data = json.loads(json_data)

        # Convert to connection configs
        connections = {}
        for conn_data in data:
            try:
                # Ensure password is properly loaded as SecretStr
                if "password" in conn_data and not conn_data["password"].startswith("SecretStr"):
                    conn_data["password"] = conn_data["password"]

                # Create the connection config
                connection = AS400ConnectionConfig(**conn_data)
                connections[connection.id] = connection
            except Exception as e:
                # Skip invalid connections
                continue

        return connections
    except Exception:
        # If anything goes wrong, return empty dict
        return {}


def save_connections(
        connections: Dict[str, AS400ConnectionConfig], file_manager: Any
) -> bool:
    """
    Save AS400 connection configurations.

    Args:
        connections: Dictionary of connection configurations by ID
        file_manager: Qorzen file manager for file operations

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the connections file path
        file_path = "as400_connector_plugin/connections.json"

        # Create parent directory if needed
        file_manager.ensure_directory("as400_connector_plugin", "plugin_data")

        # Convert connections to JSON serializable format
        conn_list = []
        for conn in connections.values():
            # Convert to dict with special handling for SecretStr
            conn_dict = conn.dict()
            if "password" in conn_dict:
                # Store password as plain string (caution: sensitive)
                conn_dict["password"] = conn.password.get_secret_value()
            conn_list.append(conn_dict)

        # Save to file
        json_data = json.dumps(conn_list, indent=2)
        file_manager.write_text(file_path, json_data, "plugin_data")
        return True
    except Exception:
        return False


def load_saved_queries(file_manager: Any) -> Dict[str, SavedQuery]:
    """
    Load saved SQL queries.

    Args:
        file_manager: Qorzen file manager for file operations

    Returns:
        Dictionary of saved queries by ID
    """
    try:
        # Get the queries file path
        file_path = "as400_connector_plugin/saved_queries.json"

        # Check if the file exists
        try:
            file_info = file_manager.get_file_info(file_path, "plugin_data")
            if not file_info:
                return {}
        except:
            return {}

        # Load the queries file
        json_data = file_manager.read_text(file_path, "plugin_data")
        data = json.loads(json_data)

        # Convert to saved queries
        queries = {}
        for query_data in data:
            try:
                # Handle datetime fields
                if "created_at" in query_data and isinstance(query_data["created_at"], str):
                    query_data["created_at"] = datetime.datetime.fromisoformat(query_data["created_at"])
                if "updated_at" in query_data and isinstance(query_data["updated_at"], str):
                    query_data["updated_at"] = datetime.datetime.fromisoformat(query_data["updated_at"])

                # Create the saved query
                query = SavedQuery(**query_data)
                queries[query.id] = query
            except Exception as e:
                # Skip invalid queries
                continue

        return queries
    except Exception:
        # If anything goes wrong, return empty dict
        return {}


def save_queries(queries: Dict[str, SavedQuery], file_manager: Any) -> bool:
    """
    Save SQL queries.

    Args:
        queries: Dictionary of saved queries by ID
        file_manager: Qorzen file manager for file operations

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the queries file path
        file_path = "as400_connector_plugin/saved_queries.json"

        # Create parent directory if needed
        file_manager.ensure_directory("as400_connector_plugin", "plugin_data")

        # Convert queries to JSON serializable format
        query_list = []
        for query in queries.values():
            query_dict = query.dict()

            # Convert datetime to ISO format for JSON serialization
            if "created_at" in query_dict and isinstance(query_dict["created_at"], datetime.datetime):
                query_dict["created_at"] = query_dict["created_at"].isoformat()
            if "updated_at" in query_dict and isinstance(query_dict["updated_at"], datetime.datetime):
                query_dict["updated_at"] = query_dict["updated_at"].isoformat()

            query_list.append(query_dict)

        # Save to file
        json_data = json.dumps(query_list, indent=2)
        file_manager.write_text(file_path, json_data, "plugin_data")
        return True
    except Exception:
        return False


def load_query_history(file_manager: Any, limit: int = 100) -> List[QueryHistoryEntry]:
    """
    Load query execution history.

    Args:
        file_manager: Qorzen file manager for file operations
        limit: Maximum number of history entries to return

    Returns:
        List of query history entries, newest first
    """
    try:
        # Get the history file path
        file_path = "as400_connector_plugin/query_history.json"

        # Check if the file exists
        try:
            file_info = file_manager.get_file_info(file_path, "plugin_data")
            if not file_info:
                return []
        except:
            return []

        # Load the history file
        json_data = file_manager.read_text(file_path, "plugin_data")
        data = json.loads(json_data)

        # Convert to history entries
        history = []
        for entry_data in data:
            try:
                # Handle datetime fields
                if "executed_at" in entry_data and isinstance(entry_data["executed_at"], str):
                    entry_data["executed_at"] = datetime.datetime.fromisoformat(entry_data["executed_at"])

                # Create the history entry
                entry = QueryHistoryEntry(**entry_data)
                history.append(entry)
            except Exception:
                # Skip invalid entries
                continue

        # Sort by executed_at descending (newest first)
        history.sort(key=lambda x: x.executed_at, reverse=True)

        # Apply limit
        return history[:limit]
    except Exception:
        # If anything goes wrong, return empty list
        return []


def save_query_history(history: List[QueryHistoryEntry], file_manager: Any, limit: int = 100) -> bool:
    """
    Save query execution history.

    Args:
        history: List of query history entries
        file_manager: Qorzen file manager for file operations
        limit: Maximum number of history entries to save

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the history file path
        file_path = "as400_connector_plugin/query_history.json"

        # Create parent directory if needed
        file_manager.ensure_directory("as400_connector_plugin", "plugin_data")

        # Sort by executed_at descending (newest first)
        sorted_history = sorted(
            history,
            key=lambda x: x.executed_at,
            reverse=True
        )[:limit]

        # Convert history to JSON serializable format
        history_list = []
        for entry in sorted_history:
            entry_dict = entry.dict()

            # Convert datetime to ISO format for JSON serialization
            if "executed_at" in entry_dict and isinstance(entry_dict["executed_at"], datetime.datetime):
                entry_dict["executed_at"] = entry_dict["executed_at"].isoformat()

            history_list.append(entry_dict)

        # Save to file
        json_data = json.dumps(history_list, indent=2)
        file_manager.write_text(file_path, json_data, "plugin_data")
        return True
    except Exception:
        return False


def load_plugin_settings(config_manager: Any) -> PluginSettings:
    """
    Load plugin settings from the configuration manager.

    Args:
        config_manager: Qorzen configuration manager

    Returns:
        Plugin settings object
    """
    try:
        settings_dict = config_manager.get("plugins.as400_connector_plugin.settings", {})
        return PluginSettings(**settings_dict)
    except Exception:
        return PluginSettings()


def save_plugin_settings(settings: PluginSettings, config_manager: Any) -> bool:
    """
    Save plugin settings to the configuration manager.

    Args:
        settings: Plugin settings object
        config_manager: Qorzen configuration manager

    Returns:
        True if successful, False otherwise
    """
    try:
        settings_dict = settings.dict()
        config_manager.set("plugins.as400_connector_plugin.settings", settings_dict)
        return True
    except Exception:
        return False


def format_value_for_display(value: Any) -> str:
    """
    Format a value for display in the UI.

    Args:
        value: The value to format

    Returns:
        Formatted string representation of the value
    """
    if value is None:
        return "NULL"

    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        return value.isoformat()

    if isinstance(value, bool):
        return str(value).upper()

    if isinstance(value, bytes):
        # Format as hex string for binary data
        if len(value) > 20:
            return f"0x{value[:20].hex()}... ({len(value)} bytes)"
        else:
            return f"0x{value.hex()}"

    return str(value)


def detect_query_parameters(query: str) -> List[str]:
    """
    Detect named parameters in a SQL query.

    Args:
        query: SQL query text

    Returns:
        List of parameter names
    """
    # Look for parameters in the format :param_name
    param_names = re.findall(r":(\w+)", query)

    # Return unique parameter names
    return list(dict.fromkeys(param_names))


def get_sql_keywords() -> List[str]:
    """
    Get a list of SQL keywords for syntax highlighting.

    Returns:
        List of SQL keywords
    """
    return [
        # Common SQL keywords
        "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "BETWEEN", "LIKE",
        "ORDER", "BY", "GROUP", "HAVING", "JOIN", "INNER", "LEFT", "RIGHT", "OUTER",
        "ON", "AS", "UNION", "ALL", "DISTINCT", "CASE", "WHEN", "THEN", "ELSE", "END",
        "IS", "NULL", "CREATE", "TABLE", "VIEW", "INDEX", "UNIQUE", "PRIMARY", "KEY",
        "FOREIGN", "REFERENCES", "CONSTRAINT", "DEFAULT", "ALTER", "ADD", "DROP",
        "TRUNCATE", "DELETE", "UPDATE", "SET", "INSERT", "INTO", "VALUES", "EXISTS",

        # Data types
        "INT", "INTEGER", "SMALLINT", "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE",
        "REAL", "CHAR", "VARCHAR", "TEXT", "DATE", "TIME", "TIMESTAMP", "DATETIME",
        "BOOLEAN", "BINARY", "VARBINARY", "BLOB", "CLOB",

        # Functions
        "COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "IFNULL", "CAST",
        "UPPER", "LOWER", "TRIM", "LTRIM", "RTRIM", "SUBSTRING", "LENGTH",
        "CONCAT", "REPLACE", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP",
        "EXTRACT", "TO_CHAR", "TO_DATE", "DATEADD", "DATEDIFF",

        # DB2/AS400 specific
        "WITH", "FETCH", "FIRST", "ROWS", "ONLY", "OPTIMIZE", "FOR", "RRN",
        "LISTAGG", "OVER", "PARTITION", "DENSE_RANK", "ROW_NUMBER", "RANK",
        "SUBSTR", "POSITION", "LOCATE", "VALUE", "GET_CURRENT_CONNECTION",
        "DAYS", "MICROSECOND", "QUARTER", "RID", "NODENAME", "NODENUMBER",
    ]


def get_syntax_highlighting_colors() -> Dict[str, QColor]:
    """
    Get colors for SQL syntax highlighting.

    Returns:
        Dictionary mapping syntax elements to colors
    """
    return {
        "keyword": QColor(0, 128, 255),  # Blue
        "function": QColor(255, 128, 0),  # Orange
        "string": QColor(0, 170, 0),  # Green
        "number": QColor(170, 0, 170),  # Purple
        "operator": QColor(170, 0, 0),  # Red
        "comment": QColor(128, 128, 128),  # Gray
        "parameter": QColor(0, 170, 170),  # Teal
        "identifier": QColor(0, 0, 0),  # Black
        "background": QColor(255, 255, 255),  # White
        "current_line": QColor(232, 242, 254),  # Light blue
    }


def guess_jar_locations() -> List[str]:
    """
    Guess potential locations for the JT400 JAR file.

    Returns:
        List of potential file paths
    """
    potential_paths = []

    # Common locations on different platforms
    if os.name == "nt":  # Windows
        # Common program files locations
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

        for base in [program_files, program_files_x86]:
            potential_paths.extend([
                os.path.join(base, "IBM", "JTOpen", "lib", "jt400.jar"),
                os.path.join(base, "IBM", "Client Access", "jt400.jar"),
            ])

        # User downloads folder
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        potential_paths.append(os.path.join(downloads, "jt400.jar"))

    else:  # Linux/Mac
        # Common installation locations
        potential_paths.extend([
            "/opt/jt400/lib/jt400.jar",
            "/usr/local/lib/jt400.jar",
            "/usr/lib/jt400.jar",
            os.path.join(os.path.expanduser("~"), "lib", "jt400.jar"),
            os.path.join(os.path.expanduser("~"), "Downloads", "jt400.jar"),
        ])

    # Project directory paths
    project_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    potential_paths.extend([
        os.path.join(project_dir, "lib", "jt400.jar"),
        os.path.join(project_dir, "jars", "jt400.jar"),
        os.path.join(project_dir, "external", "jt400.jar"),
    ])

    # Filter out non-existent paths
    return [path for path in potential_paths if os.path.exists(path)]


def format_execution_time(ms: int) -> str:
    """
    Format execution time in milliseconds to a human-readable string.

    Args:
        ms: Execution time in milliseconds

    Returns:
        Formatted time string
    """
    if ms < 1000:
        return f"{ms} ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f} sec"
    else:
        minutes = ms // 60000
        seconds = (ms % 60000) / 1000
        return f"{minutes} min {seconds:.2f} sec"