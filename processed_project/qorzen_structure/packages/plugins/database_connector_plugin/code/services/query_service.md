# Module: plugins.database_connector_plugin.code.services.query_service

**Path:** `plugins/database_connector_plugin/code/services/query_service.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Optional
from qorzen.utils.exceptions import DatabaseError
```

## Classes

| Class | Description |
| --- | --- |
| `QueryService` |  |

### Class: `QueryService`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `estimate_result_size` |  |
| `execute_query` `async` |  |
| `extract_table_names` |  |
| `format_sql` |  |
| `get_query_type` |  |
| `get_table_columns` `async` |  |
| `get_tables` `async` |  |
| `is_read_only_query` |  |
| `suggest_query_improvements` |  |
| `test_connection` `async` |  |

##### `__init__`
```python
def __init__(self, database_manager, logger) -> None:
```

##### `estimate_result_size`
```python
def estimate_result_size(self, query) -> str:
```

##### `execute_query`
```python
async def execute_query(self, connection_name, query, parameters, limit, apply_mapping) -> Dict[(str, Any)]:
```

##### `extract_table_names`
```python
def extract_table_names(self, query) -> List[str]:
```

##### `format_sql`
```python
def format_sql(self, query) -> str:
```

##### `get_query_type`
```python
def get_query_type(self, query) -> str:
```

##### `get_table_columns`
```python
async def get_table_columns(self, connection_name, table_name, schema) -> List[Dict[(str, Any)]]:
```

##### `get_tables`
```python
async def get_tables(self, connection_name, schema) -> List[Dict[(str, Any)]]:
```

##### `is_read_only_query`
```python
def is_read_only_query(self, query) -> bool:
```

##### `suggest_query_improvements`
```python
def suggest_query_improvements(self, query) -> List[str]:
```

##### `test_connection`
```python
async def test_connection(self, connection_name) -> bool:
```
