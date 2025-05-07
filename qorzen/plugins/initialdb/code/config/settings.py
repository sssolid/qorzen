from __future__ import annotations

import sys

from ..utils.dependency_container import resolve
from ..utils.schema_registry import SchemaRegistry

"""
Settings module for the InitialDB application.

This module provides access to application settings and persistent storage,
including recent queries, exports, layouts, and user preferences.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import structlog

logger = structlog.get_logger(__name__)

# Constants
APP_NAME = 'InitialDB'
APP_AUTHOR = 'Ryan Serra'

# Database connection settings
DEFAULT_CONNECTION_STRING = 'postgresql+asyncpg://initialdb:B54C3CBADDFSssALK92@192.168.10.234:5432/crown_nexus'

# Query limit settings
DEFAULT_QUERY_LIMIT = 1000
MAX_QUERY_LIMIT = 10000

# UI settings
UI_REFRESH_INTERVAL_MS = 500

# Cache settings
ENABLE_CACHING = True
CACHE_TIMEOUT_SECONDS = 300

# Export settings
DEFAULT_EXPORTS_DIR = 'exports'
DEFAULT_TEMPLATES_DIR = 'templates'

# Logging settings
DEFAULT_LOG_LEVEL = 'info'

# Paths
USER_HOME = Path.home()
APP_DIR = USER_HOME / '.initialdb'
SETTINGS_FILE = APP_DIR / 'settings.json'
LAYOUTS_DIR = APP_DIR / 'layouts'
QUERIES_DIR = APP_DIR / 'queries'
QUERIES_RECENT_DIR = QUERIES_DIR / 'recent'
EXPORTS_DIR = APP_DIR / 'exports'
TEMPLATES_DIR = APP_DIR / 'templates'

# Default settings without importing from models.schema
DEFAULT_SETTINGS = {
    'app_version': '0.1.0',
    'update_url': 'http://192.168.10.237:8000',
    'update_check_automatically': True,
    'update_check_interval_hours': 24,
    'update_download_automatically': False,
    'update_install_automatically': False,
    'update_last_check_time': None,
    'connection_string': DEFAULT_CONNECTION_STRING,
    'query_limit': DEFAULT_QUERY_LIMIT,
    'max_recent_exports': 10,
    'max_recent_queries': 20,
    'ui_refresh_interval_ms': UI_REFRESH_INTERVAL_MS,
    'default_exports_path': str(EXPORTS_DIR),
    'default_layout': 'default',
    'update_skipped_versions': [],
    # UI settings
    'enable_left_panel_button_text': False,
    'enable_bottom_panel_button_text': False,
    # Available queries
    'available_queries': {},
    # We'll set these fields after loading in initialize_display_settings()
    'visible_columns': [],
    'active_filters': [],
    # Recent exports and queries
    'recent_exports': [],
    'recent_queries': [],
}

def get_resource_path(relative: str) -> Path:
    """
    Get the absolute path to a resource file.

    Args:
        relative: The relative path to the resource

    Returns:
        The absolute path to the resource
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).parent.parent.parent / relative

class Settings:
    def __init__(self) -> None:
        """Initialize the settings object."""
        self._registry = None
        self._settings = DEFAULT_SETTINGS.copy()
        self._ensure_app_dirs()
        self._load_settings()

    def initialize_display_settings(self) -> None:
        """
        Initialize display settings after other modules are loaded.

        This method should be called after the schema registry is initialized.
        """
        self._registry = resolve(SchemaRegistry)

        # Set default visible columns if not already set
        if not self._settings.get('visible_columns'):
            self._settings['visible_columns'] = self._registry.get_default_display_fields()

        # Set default active filters if not already set
        if not self._settings.get('active_filters'):
            self._settings['active_filters'] = self._registry.get_default_filters()

        # Save settings
        self._save_settings()

    # Rest of the Settings class remains the same
    def _ensure_app_dirs(self) -> None:
        os.makedirs(APP_DIR, exist_ok=True)
        os.makedirs(LAYOUTS_DIR, exist_ok=True)
        os.makedirs(QUERIES_DIR, exist_ok=True)
        os.makedirs(QUERIES_RECENT_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        os.makedirs(TEMPLATES_DIR, exist_ok=True)

    def _load_settings(self) -> None:
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self._settings.update(loaded_settings)
                    logger.info('Settings loaded successfully')
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f'Error loading settings: {e}', exc_info=True)

    def _save_settings(self) -> None:
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, default=str)
                logger.debug('Settings saved successfully')
        except IOError as e:
            logger.error(f'Error saving settings: {e}', exc_info=True)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value
        self._save_settings()

    def add_recent_query(self, query_info: Dict[str, Any]) -> None:
        """
        Add a query to the recent queries list.

        Args:
            query_info: Information about the query
        """
        recent_queries = self._settings.get("recent_queries", [])

        # Add timestamp if not present
        if "timestamp" not in query_info:
            query_info["timestamp"] = datetime.now().isoformat()

        # Remove the query if it already exists by name
        if "name" in query_info:
            recent_queries = [q for q in recent_queries if q.get("name") != query_info.get("name")]

        # Add to beginning of list
        recent_queries.insert(0, query_info)

        # Limit number of recent queries
        if len(recent_queries) > self.get('max_recent_queries', 20):
            recent_queries = recent_queries[:self.get('max_recent_queries', 20)]

        self._settings["recent_queries"] = recent_queries
        self._save_settings()

    def add_recent_export(self, export_path: str) -> None:
        """
        Add an export to the recent exports list.

        Args:
            export_path: Path to the exported file
        """
        recent_exports = self._settings.get("recent_exports", [])

        # Remove the export if it already exists
        recent_exports = [e for e in recent_exports if e != export_path]

        # Create export info
        export_info = {
            "path": export_path,
            "filename": os.path.basename(export_path),
            "timestamp": datetime.now().isoformat()
        }

        # Add to beginning of list
        recent_exports.insert(0, export_info)

        # Limit number of recent exports
        if len(recent_exports) > self.get('max_recent_exports', 10):
            recent_exports = recent_exports[:self.get('max_recent_exports', 10)]

        self._settings["recent_exports"] = recent_exports
        self._save_settings()

    def get_new_export_path(self, prefix: str, extension: str) -> str:
        """
        Generate a new unique export file path.

        Args:
            prefix: Prefix for the filename
            extension: File extension (without dot)

        Returns:
            A complete file path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.{extension}"
        return str(Path(self._settings.get("default_exports_path", EXPORTS_DIR)) / filename)

    def save_layout(self, name: str, layout: Dict[str, Any]) -> None:
        """
        Save a layout configuration.

        Args:
            name: The layout name
            layout: The layout configuration
        """
        layout_file = LAYOUTS_DIR / f"{name}.json"
        try:
            with open(layout_file, 'w', encoding='utf-8') as f:
                json.dump(layout, f, indent=2, default=str)
                logger.debug(f"Layout '{name}' saved successfully")
        except IOError as e:
            logger.error(f"Error saving layout '{name}': {e}", exc_info=True)

    def load_layout(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a layout configuration.

        Args:
            name: The layout name

        Returns:
            The layout configuration or None if it doesn't exist
        """
        layout_file = LAYOUTS_DIR / f"{name}.json"
        if not layout_file.exists():
            logger.warning(f"Layout '{name}' does not exist")
            return None

        try:
            with open(layout_file, 'r', encoding='utf-8') as f:
                layout = json.load(f)
                logger.debug(f"Layout '{name}' loaded successfully")
                return layout
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading layout '{name}': {e}", exc_info=True)
            return None

    def get_available_layouts(self) -> List[str]:
        """
        Get a list of available layout names.

        Returns:
            List of layout names
        """
        layouts = []
        for layout_file in LAYOUTS_DIR.glob("*.json"):
            layouts.append(layout_file.stem)
        return layouts

    def save_query(self, name: str, query: Dict[str, Any]) -> None:
        """
        Save a query configuration.

        Args:
            name: The query name
            query: The query configuration
        """
        query_file = QUERIES_DIR / f"{name}.json"
        try:
            with open(query_file, 'w', encoding='utf-8') as f:
                json.dump(query, f, indent=2, default=str)
                logger.debug(f"Query '{name}' saved successfully")
        except IOError as e:
            logger.error(f"Error saving query '{name}': {e}", exc_info=True)

    def load_query(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a query configuration.

        Args:
            name: The query name

        Returns:
            The query configuration or None if it doesn't exist
        """
        query_file = QUERIES_DIR / f"{name}.json"
        if not query_file.exists():
            logger.warning(f"Query '{name}' does not exist")
            return None

        try:
            with open(query_file, 'r', encoding='utf-8') as f:
                query = json.load(f)
                logger.debug(f"Query '{name}' loaded successfully")
                return query
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading query '{name}': {e}", exc_info=True)
            return None

    def get_available_queries(self) -> List[str]:
        """
        Get a list of available query names.

        Returns:
            List of query names
        """
        queries = []
        for query_file in QUERIES_DIR.glob("*.json"):
            queries.append(query_file.stem)
        return queries

    def get_recent_queries(self) -> List[str]:
        """
        Get a list of recent query names.

        Returns:
            List of query names
        """
        queries = []
        for query_file in QUERIES_RECENT_DIR.glob("*.json"):
            queries.append(query_file.stem)
        return queries

    def reset(self) -> None:
        """
        Reset all settings to defaults.
        """
        self._settings = DEFAULT_SETTINGS.copy()
        self._save_settings()

    def reset_layout(self) -> None:
        """
        Reset layout-related settings.
        """
        self._settings["visible_columns"] = DEFAULT_SETTINGS["visible_columns"]
        self._settings["active_filters"] = DEFAULT_SETTINGS["active_filters"]
        self._save_settings()


# Create singleton instance
settings = Settings()