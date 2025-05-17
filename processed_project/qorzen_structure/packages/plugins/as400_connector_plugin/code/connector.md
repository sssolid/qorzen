# Module: plugins.as400_connector_plugin.code.connector

**Path:** `plugins/as400_connector_plugin/code/connector.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import re
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from functools import cache
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, ColumnMetadata, QueryResult
```

## Classes

| Class | Description |
| --- | --- |
| `AS400Connector` |  |

### Class: `AS400Connector`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `close` `async` |  |
| `connect` `async` |  |
| `execute_query` `async` |  |
| `get_connection_info` |  |
| `get_schema_info` `async` |  |
| `is_connected` |  |

##### `__init__`
```python
def __init__(self, config, logger, security_manager) -> None:
```

##### `close`
```python
async def close(self) -> None:
```

##### `connect`
```python
async def connect(self) -> None:
```

##### `execute_query`
```python
async def execute_query(self, query, limit, **params) -> QueryResult:
```

##### `get_connection_info`
```python
def get_connection_info(self) -> Dict[(str, Any)]:
```

##### `get_schema_info`
```python
async def get_schema_info(self, schema) -> List[Dict[(str, Any)]]:
```

##### `is_connected`
```python
def is_connected(self) -> bool:
```
