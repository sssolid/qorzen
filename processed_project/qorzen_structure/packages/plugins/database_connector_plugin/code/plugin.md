# Module: plugins.database_connector_plugin.code.plugin

**Path:** `plugins/database_connector_plugin/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import json
import os
import logging
import datetime
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QMessageBox
from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from qorzen.utils.exceptions import PluginError, DatabaseError
from models import BaseConnectionConfig, AS400ConnectionConfig, ODBCConnectionConfig, ConnectionType, PluginSettings, SavedQuery, FieldMapping, ValidationRule, QueryResult
from connectors import BaseDatabaseConnector, get_connector_for_config
from ui.main_tab import DatabaseConnectorTab
from utils.mapping import apply_mapping_to_results
from utils.history import HistoryManager
from utils.validation import ValidationEngine
```

## Classes

| Class | Description |
| --- | --- |
| `DatabaseConnectorPlugin` |  |

### Class: `DatabaseConnectorPlugin`
**Inherits from:** BasePlugin

#### Attributes

| Name | Value |
| --- | --- |
| `name` | `'database_connector_plugin'` |
| `version` | `'1.0.0'` |
| `description` | `'Connect and query various databases with field mapping and validation capabilities'` |
| `author` | `'Qorzen Team'` |
| `display_name` | `'Database Connector'` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `delete_connection` `async` |  |
| `delete_field_mapping` `async` |  |
| `delete_query` `async` |  |
| `disconnect` `async` |  |
| `execute_query` `async` |  |
| `get_connection` `async` |  |
| `get_connections` `async` |  |
| `get_connector` `async` |  |
| `get_field_mapping` `async` |  |
| `get_field_mappings` `async` |  |
| `get_history_manager` `async` |  |
| `get_saved_queries` `async` |  |
| `get_saved_query` `async` |  |
| `get_validation_engine` `async` |  |
| `initialize` `async` |  |
| `on_ui_ready` `async` |  |
| `save_connection` `async` |  |
| `save_field_mapping` `async` |  |
| `save_query` `async` |  |
| `setup_ui` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `test_connection` `async` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `delete_connection`
```python
async def delete_connection(self, connection_id) -> bool:
```

##### `delete_field_mapping`
```python
async def delete_field_mapping(self, mapping_id) -> bool:
```

##### `delete_query`
```python
async def delete_query(self, query_id) -> bool:
```

##### `disconnect`
```python
async def disconnect(self, connection_id) -> bool:
```

##### `execute_query`
```python
async def execute_query(self, connection_id, query, params, limit, mapping_id) -> QueryResult:
```

##### `get_connection`
```python
async def get_connection(self, connection_id) -> Optional[BaseConnectionConfig]:
```

##### `get_connections`
```python
async def get_connections(self) -> Dict[(str, BaseConnectionConfig)]:
```

##### `get_connector`
```python
async def get_connector(self, connection_id) -> BaseDatabaseConnector:
```

##### `get_field_mapping`
```python
async def get_field_mapping(self, mapping_id) -> Optional[FieldMapping]:
```

##### `get_field_mappings`
```python
async def get_field_mappings(self, connection_id, table_name) -> Dict[(str, FieldMapping)]:
```

##### `get_history_manager`
```python
async def get_history_manager(self) -> HistoryManager:
```

##### `get_saved_queries`
```python
async def get_saved_queries(self, connection_id) -> Dict[(str, SavedQuery)]:
```

##### `get_saved_query`
```python
async def get_saved_query(self, query_id) -> Optional[SavedQuery]:
```

##### `get_validation_engine`
```python
async def get_validation_engine(self) -> ValidationEngine:
```

##### `initialize`
```python
async def initialize(self, application_core, **kwargs) -> None:
```

##### `on_ui_ready`
```python
async def on_ui_ready(self, ui_integration) -> None:
```

##### `save_connection`
```python
async def save_connection(self, config) -> str:
```

##### `save_field_mapping`
```python
async def save_field_mapping(self, mapping) -> str:
```

##### `save_query`
```python
async def save_query(self, query) -> str:
```

##### `setup_ui`
```python
async def setup_ui(self, ui_integration) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `test_connection`
```python
async def test_connection(self, config) -> Tuple[(bool, Optional[str])]:
```
