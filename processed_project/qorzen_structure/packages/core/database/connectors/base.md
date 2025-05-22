# Module: core.database.connectors.base

**Path:** `core/database/connectors/base.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Protocol, TypeVar, cast
```

## Global Variables
```python
T = T = TypeVar('T', bound='BaseConnectionConfig')
```

## Classes

| Class | Description |
| --- | --- |
| `BaseDatabaseConnector` |  |

### Class: `BaseDatabaseConnector`
**Inherits from:** abc.ABC

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cancel_query` `async` |  |
| `config` `@property` |  |
| `connect` `async` |  |
| `database_manager` `@property` |  |
| `disconnect` `async` |  |
| `execute_query` `async` |  |
| `get_connection_info` |  |
| `get_table_columns` `async` |  |
| `get_tables` `async` |  |
| `is_connected` `@property` |  |
| `set_database_manager` |  |
| `test_connection` `async` |  |

##### `__init__`
```python
def __init__(self, config, logger, security_manager) -> None:
```

##### `cancel_query`
```python
async def cancel_query(self) -> bool:
```

##### `config`
```python
@property
def config(self) -> Any:
```

##### `connect`
```python
@abc.abstractmethod
async def connect(self) -> None:
```

##### `database_manager`
```python
@property
def database_manager(self) -> Optional[Any]:
```

##### `disconnect`
```python
@abc.abstractmethod
async def disconnect(self) -> None:
```

##### `execute_query`
```python
@abc.abstractmethod
async def execute_query(self, query, params, limit) -> Dict[(str, Any)]:
```

##### `get_connection_info`
```python
@abc.abstractmethod
def get_connection_info(self) -> Dict[(str, Any)]:
```

##### `get_table_columns`
```python
@abc.abstractmethod
async def get_table_columns(self, table_name, schema) -> List[Dict[(str, Any)]]:
```

##### `get_tables`
```python
@abc.abstractmethod
async def get_tables(self, schema) -> List[Dict[(str, Any)]]:
```

##### `is_connected`
```python
@property
def is_connected(self) -> bool:
```

##### `set_database_manager`
```python
def set_database_manager(self, db_manager) -> None:
```

##### `test_connection`
```python
async def test_connection(self) -> Tuple[(bool, Optional[str])]:
```
