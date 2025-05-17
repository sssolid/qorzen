#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Database connectors for the Database Connector Plugin.

This module provides implementations of various database connectors
that can be used to connect to and query different database systems.
"""

from typing import Dict, Type, Any

from ..models import (
    BaseConnectionConfig,
    ConnectionType,
    AS400ConnectionConfig,
    ODBCConnectionConfig,
    SQLConnectionConfig,
)
from .base import BaseDatabaseConnector, DatabaseConnectorProtocol
from .as400 import AS400Connector
from .odbc import ODBCConnector

# Export all connector classes
__all__ = [
    "BaseDatabaseConnector",
    "DatabaseConnectorProtocol",
    "AS400Connector",
    "ODBCConnector",
    "get_connector_for_config",
]

# Registry of connector classes by connection type
CONNECTOR_REGISTRY: Dict[ConnectionType, Type[BaseDatabaseConnector]] = {
    ConnectionType.AS400: AS400Connector,
    ConnectionType.ODBC: ODBCConnector,
}


def get_connector_for_config(
        config: BaseConnectionConfig,
        logger: Any,
        security_manager: Any = None
) -> BaseDatabaseConnector:
    """
    Create the appropriate connector instance for the given configuration.

    Args:
        config: Database connection configuration
        logger: Logger instance
        security_manager: Optional security manager

    Returns:
        Database connector instance

    Raises:
        ValueError: If no connector is available for the connection type
    """
    connector_class = CONNECTOR_REGISTRY.get(config.connection_type)

    if not connector_class:
        raise ValueError(
            f"No connector available for connection type: {config.connection_type}"
        )

    return connector_class(config, logger, security_manager)