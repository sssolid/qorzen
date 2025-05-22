# Module: core.database.connectors.sqlite

**Path:** `core/database/connectors/sqlite.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, AsyncGenerator
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from base import BaseDatabaseConnector
```

## Classes

| Class | Description |
| --- | --- |
| `AsyncCompatibleSession` |  |
| `SQLiteConnector` |  |

### Class: `AsyncCompatibleSession`

#### Methods

| Method | Description |
| --- | --- |
| `__aenter__` `async` |  |
| `__aexit__` `async` |  |
| `__init__` |  |
| `close` `async` |  |
| `commit` `async` |  |
| `execute` `async` |  |
| `rollback` `async` |  |

##### `__aenter__`
```python
async def __aenter__(self) -> 'AsyncCompatibleSession':
```

##### `__aexit__`
```python
async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
```

##### `__init__`
```python
def __init__(self, sync_session, loop) -> None:
```

##### `close`
```python
async def close(self) -> None:
```

##### `commit`
```python
async def commit(self) -> None:
```

##### `execute`
```python
async def execute(self, statement, *args, **kwargs) -> Any:
```

##### `rollback`
```python
async def rollback(self) -> None:
```

### Class: `SQLiteConnector`
**Inherits from:** BaseDatabaseConnector

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `async_session` `async` |  |
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

##### `async_session`
```python
async def async_session(self) -> AsyncGenerator[(AsyncCompatibleSession, None)]:
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
