from __future__ import annotations
'\nDatabase connectors for the Database Connector Plugin.\n\nThis module provides implementations of various database connectors\nthat can be used to connect to and query different database systems.\n'
from typing import Dict, Type, Any
from ..models import BaseConnectionConfig, ConnectionType, AS400ConnectionConfig, ODBCConnectionConfig, SQLConnectionConfig
from .base import BaseDatabaseConnector, DatabaseConnectorProtocol
from .as400 import AS400Connector
from .odbc import ODBCConnector
__all__ = ['BaseDatabaseConnector', 'DatabaseConnectorProtocol', 'AS400Connector', 'ODBCConnector', 'get_connector_for_config']
CONNECTOR_REGISTRY: Dict[ConnectionType, Type[BaseDatabaseConnector]] = {ConnectionType.AS400: AS400Connector, ConnectionType.ODBC: ODBCConnector}
def get_connector_for_config(config: BaseConnectionConfig, logger: Any, security_manager: Any=None) -> BaseDatabaseConnector:
    connector_class = CONNECTOR_REGISTRY.get(config.connection_type)
    if not connector_class:
        raise ValueError(f'No connector available for connection type: {config.connection_type}')
    return connector_class(config, logger, security_manager)