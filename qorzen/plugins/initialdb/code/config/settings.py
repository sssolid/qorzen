#!/usr/bin/env python3
# settings.py
from __future__ import annotations

"""
Settings module for the InitialDB plugin.

This module provides configuration constants and utilities for the InitialDB plugin,
using the Qorzen configuration system.
"""

import logging
from typing import Any, Dict, Optional, cast

# Default settings constants
DEFAULT_CONNECTION_STRING = "postgresql+asyncpg://initialdb:password@localhost:5432/crown_nexus"
DEFAULT_QUERY_LIMIT = 1000
MAX_QUERY_LIMIT = 10000
UI_REFRESH_INTERVAL_MS = 500
ENABLE_CACHING = True
CACHE_TIMEOUT_SECONDS = 300
DEFAULT_EXPORTS_DIR = "exports"
DEFAULT_TEMPLATES_DIR = "templates"
DEFAULT_LOG_LEVEL = "info"
MAX_RECENT_EXPORTS = 10
MAX_RECENT_QUERIES = 20


def get_plugin_config_namespace() -> str:
    """
    Get the plugin config namespace.

    Returns:
        str: The plugin config namespace
    """
    return "plugins.initialdb"


def setup_default_config(config_manager: Any, logger: logging.Logger) -> None:
    """
    Set up default configuration for the plugin.

    Args:
        config_manager: The Qorzen config manager
        logger: Logger for this module
    """
    default_config = {
        "connection_string": DEFAULT_CONNECTION_STRING,
        "default_query_limit": DEFAULT_QUERY_LIMIT,
        "max_query_limit": MAX_QUERY_LIMIT,
        "ui_refresh_interval_ms": UI_REFRESH_INTERVAL_MS,
        "enable_caching": ENABLE_CACHING,
        "cache_timeout": CACHE_TIMEOUT_SECONDS,
        "exports_dir": DEFAULT_EXPORTS_DIR,
        "templates_dir": DEFAULT_TEMPLATES_DIR,
        "log_level": DEFAULT_LOG_LEVEL,
        "max_recent_exports": MAX_RECENT_EXPORTS,
        "max_recent_queries": MAX_RECENT_QUERIES,
        # UI settings
        "enable_left_panel_button_text": False,
        "enable_bottom_panel_button_text": False,
    }

    namespace = get_plugin_config_namespace()
    for key, value in default_config.items():
        config_path = f"{namespace}.{key}"
        try:
            # Only set if not already present
            if config_manager.get(config_path) is None:
                config_manager.set(config_path, value)
                logger.debug(f"Set default config: {config_path}={value}")
        except Exception as e:
            logger.warning(f"Failed to set config {config_path}: {e}")

    logger.info("Default configuration set up")


def get_config_value(config_manager: Any, key: str, default: Any = None) -> Any:
    """
    Get a configuration value for the plugin.

    Args:
        config_manager: The Qorzen config manager
        key: Configuration key within the plugin namespace
        default: Default value if not found

    Returns:
        The configuration value or default
    """
    namespace = get_plugin_config_namespace()
    return config_manager.get(f"{namespace}.{key}", default)


def set_config_value(config_manager: Any, key: str, value: Any) -> None:
    """
    Set a configuration value for the plugin.

    Args:
        config_manager: The Qorzen config manager
        key: Configuration key within the plugin namespace
        value: Value to set
    """
    namespace = get_plugin_config_namespace()
    config_manager.set(f"{namespace}.{key}", value)


def add_recent_query(
        config_manager: Any, file_manager: Any, query_info: Dict[str, Any]
) -> None:
    """
    Add a query to the recent queries list.

    Args:
        config_manager: The Qorzen config manager
        file_manager: The Qorzen file manager
        query_info: Information about the query
    """
    from datetime import datetime

    namespace = get_plugin_config_namespace()
    recent_queries = config_manager.get(f"{namespace}.recent_queries", [])

    # Add timestamp if not present
    if "timestamp" not in query_info:
        query_info["timestamp"] = datetime.now().isoformat()

    # Remove the query if it already exists by name
    if "name" in query_info:
        recent_queries = [
            q for q in recent_queries if q.get("name") != query_info.get("name")
        ]

    # Add to beginning of list
    recent_queries.insert(0, query_info)

    # Limit number of recent queries
    max_recent = get_config_value(config_manager, "max_recent_queries", MAX_RECENT_QUERIES)
    if len(recent_queries) > max_recent:
        recent_queries = recent_queries[:max_recent]

    # Update configuration
    set_config_value(config_manager, "recent_queries", recent_queries)


def add_recent_export(
        config_manager: Any, file_manager: Any, export_path: str
) -> None:
    """
    Add an export to the recent exports list.

    Args:
        config_manager: The Qorzen config manager
        file_manager: The Qorzen file manager
        export_path: Path to the exported file
    """
    import os
    from datetime import datetime

    namespace = get_plugin_config_namespace()
    recent_exports = config_manager.get(f"{namespace}.recent_exports", [])

    # Remove the export if it already exists
    recent_exports = [e for e in recent_exports if e.get("path") != export_path]

    # Create export info
    export_info = {
        "path": export_path,
        "filename": os.path.basename(export_path),
        "timestamp": datetime.now().isoformat()
    }

    # Add to beginning of list
    recent_exports.insert(0, export_info)

    # Limit number of recent exports
    max_recent = get_config_value(config_manager, "max_recent_exports", MAX_RECENT_EXPORTS)
    if len(recent_exports) > max_recent:
        recent_exports = recent_exports[:max_recent]

    # Update configuration
    set_config_value(config_manager, "recent_exports", recent_exports)


def get_new_export_path(
        config_manager: Any, file_manager: Any, prefix: str, extension: str
) -> str:
    """
    Generate a new unique export file path.

    Args:
        config_manager: The Qorzen config manager
        file_manager: The Qorzen file manager
        prefix: Prefix for the filename
        extension: File extension (without dot)

    Returns:
        A complete file path
    """
    from datetime import datetime
    from pathlib import Path

    exports_dir = get_config_value(config_manager, "exports_dir", DEFAULT_EXPORTS_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.{extension}"

    return str(Path(exports_dir) / filename)