from __future__ import annotations
"""
Configuration settings for the InitialDB plugin.

This module defines default configuration values for the plugin.
"""

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