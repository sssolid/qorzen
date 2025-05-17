# Module: plugins.database_connector_plugin.code.connectors

**Path:** `plugins/database_connector_plugin/code/connectors/__init__.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from typing import Dict, Type, Any
from models import BaseConnectionConfig, ConnectionType, AS400ConnectionConfig, ODBCConnectionConfig, SQLConnectionConfig
from base import BaseDatabaseConnector, DatabaseConnectorProtocol
from as400 import AS400Connector
from odbc import ODBCConnector
```

## Global Variables
```python
__all__ = __all__ = [
    "BaseDatabaseConnector",
    "DatabaseConnectorProtocol",
    "AS400Connector",
    "ODBCConnector",
    "get_connector_for_config",
]
```

## Functions

| Function | Description |
| --- | --- |
| `get_connector_for_config` |  |

### `get_connector_for_config`
```python
def get_connector_for_config(config, logger, security_manager) -> BaseDatabaseConnector:
```
