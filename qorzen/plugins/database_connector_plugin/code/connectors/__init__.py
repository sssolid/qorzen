from __future__ import annotations

"""
Database connectors for the Database Connector Plugin.

This module provides implementations of various database connectors
that can be used to connect to and query different database systems.
"""

from typing import Dict, Type, Any

from ..models import (
    BaseConnectionConfig, ConnectionType, AS400ConnectionConfig,
    ODBCConnectionConfig, SQLiteConnectionConfig, SQLConnectionConfig
)
from .base import BaseDatabaseConnector, DatabaseConnectorProtocol
from .as400 import AS400Connector
from .odbc import ODBCConnector
from .sqlite import SQLiteConnector  # Import the new SQLite connector

__all__ = [
    'BaseDatabaseConnector', 'DatabaseConnectorProtocol',
    'AS400Connector', 'ODBCConnector', 'SQLiteConnector',
    'get_connector_for_config'
]

# Register all available connectors
CONNECTOR_REGISTRY: Dict[ConnectionType, Type[BaseDatabaseConnector]] = {
    ConnectionType.AS400: AS400Connector,
    ConnectionType.ODBC: ODBCConnector,
    ConnectionType.SQLITE: SQLiteConnector,  # Register SQLite connector
}


def get_connector_for_config(
        config: BaseConnectionConfig,
        logger: Any,
        security_manager: Any = None
) -> BaseDatabaseConnector:
    """Get the appropriate connector instance for a connection configuration.

    Args:
        config: Connection configuration
        logger: Logger instance
        security_manager: Optional security manager

    Returns:
        An initialized database connector

    Raises:
        ValueError: If no connector is available for the connection type
    """
    connector_class = CONNECTOR_REGISTRY.get(config.connection_type)
    if not connector_class:
        raise ValueError(f'No connector available for connection type: {config.connection_type}')

    return connector_class(config, logger, security_manager)