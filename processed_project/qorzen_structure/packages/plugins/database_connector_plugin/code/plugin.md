# Module: plugins.database_connector_plugin.code.plugin

**Path:** `plugins/database_connector_plugin/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qorzen.core.database_manager import DatabaseConnectionConfig, ConnectionType
from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.lifecycle import PluginLifecycleState, get_plugin_state, set_plugin_state, signal_ui_ready
from qorzen.utils.exceptions import PluginError
from models import DatabaseConnection, SavedQuery, PluginSettings, QueryResult, FieldMapping, ValidationRule, HistorySchedule, ExportSettings, ExportFormat
from ui.main_widget import DatabasePluginWidget
from services.export_service import ExportService
from services.query_service import QueryService
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
| `version` | `'2.0.0'` |
| `description` | `'Advanced database connectivity and management plugin'` |
| `author` | `'Qorzen Team'` |
| `display_name` | `'Database Connector'` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `create_connection` `async` |  |
| `create_field_mapping` `async` |  |
| `create_history_schedule` `async` |  |
| `create_validation_rule` `async` |  |
| `delete_connection` `async` |  |
| `delete_field_mapping` `async` |  |
| `delete_query` `async` |  |
| `execute_query` `async` |  |
| `export_results` `async` |  |
| `get_connections` `async` |  |
| `get_field_mappings` `async` |  |
| `get_history_schedules` `async` |  |
| `get_saved_queries` `async` |  |
| `get_settings` `async` |  |
| `get_table_columns` `async` |  |
| `get_tables` `async` |  |
| `get_validation_rules` `async` |  |
| `initialize` `async` |  |
| `on_ui_ready` `async` |  |
| `save_query` `async` |  |
| `setup_ui` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `test_connection` `async` |  |
| `update_connection` `async` |  |
| `update_settings` `async` |  |
| `validate_data` `async` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `create_connection`
```python
async def create_connection(self, connection) -> str:
```

##### `create_field_mapping`
```python
async def create_field_mapping(self, connection_id, table_name, mappings, description) -> Dict[(str, Any)]:
```

##### `create_history_schedule`
```python
async def create_history_schedule(self, connection_id, query_id, frequency, name, description, retention_days) -> Dict[(str, Any)]:
```

##### `create_validation_rule`
```python
async def create_validation_rule(self, rule_type, connection_id, table_name, field_name, parameters, error_message, name, description) -> Dict[(str, Any)]:
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

##### `execute_query`
```python
async def execute_query(self, connection_id, query, parameters, limit, apply_mapping) -> QueryResult:
```

##### `export_results`
```python
async def export_results(self, results, format, file_path, settings) -> str:
```

##### `get_connections`
```python
async def get_connections(self) -> List[DatabaseConnection]:
```

##### `get_field_mappings`
```python
async def get_field_mappings(self, connection_id) -> List[Dict[(str, Any)]]:
```

##### `get_history_schedules`
```python
async def get_history_schedules(self) -> List[Dict[(str, Any)]]:
```

##### `get_saved_queries`
```python
async def get_saved_queries(self, connection_id) -> List[SavedQuery]:
```

##### `get_settings`
```python
async def get_settings(self) -> PluginSettings:
```

##### `get_table_columns`
```python
async def get_table_columns(self, connection_id, table_name, schema) -> List[Dict[(str, Any)]]:
```

##### `get_tables`
```python
async def get_tables(self, connection_id, schema) -> List[Dict[(str, Any)]]:
```

##### `get_validation_rules`
```python
async def get_validation_rules(self, connection_id, table_name) -> List[Dict[(str, Any)]]:
```

##### `initialize`
```python
async def initialize(self, application_core, **kwargs) -> None:
```

##### `on_ui_ready`
```python
async def on_ui_ready(self, ui_integration) -> None:
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
async def test_connection(self, connection_id) -> Tuple[(bool, Optional[str])]:
```

##### `update_connection`
```python
async def update_connection(self, connection) -> None:
```

##### `update_settings`
```python
async def update_settings(self, settings) -> None:
```

##### `validate_data`
```python
async def validate_data(self, connection_id, table_name, data) -> List[Dict[(str, Any)]]:
```
