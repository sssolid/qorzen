# Module: core.database.connectors.odbc

**Path:** `core/database/connectors/odbc.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from base import BaseDatabaseConnector
```

## Classes

| Class | Description |
| --- | --- |
| `ODBCConnector` |  |

### Class: `ODBCConnector`
**Inherits from:** BaseDatabaseConnector

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `connect` `async` |  |
| `disconnect` `async` |  |
| `execute_query` `async` |  |
| `get_connection_info` |  |
| `get_table_columns` `async` |  |
| `get_tables` `async` |  |

##### `__init__`
```python
def __init__(self, config, logger, security_manager) -> None:
```

##### `connect`
```python
async def connect(self) -> None:
```

##### `disconnect`
```python
async def disconnect(self) -> None:
```

##### `execute_query`
```python
async def execute_query(self, query, params, limit) -> Dict[(str, Any)]:
```

##### `get_connection_info`
```python
def get_connection_info(self) -> Dict[(str, Any)]:
```

##### `get_table_columns`
```python
async def get_table_columns(self, table_name, schema) -> List[Dict[(str, Any)]]:
```

##### `get_tables`
```python
async def get_tables(self, schema) -> List[Dict[(str, Any)]]:
```
