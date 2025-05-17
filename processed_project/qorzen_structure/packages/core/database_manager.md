# Module: core.database_manager

**Path:** `core/database_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import functools
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set, TypeVar, Union, cast, Callable, Awaitable, AsyncGenerator
import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import DatabaseError, ManagerInitializationError, ManagerShutdownError, DatabaseManagerInitializationError
```

## Global Variables
```python
T = T = TypeVar('T')
R = R = TypeVar('R')
```

## Classes

| Class | Description |
| --- | --- |
| `Base` |  |
| `DatabaseConnection` |  |
| `DatabaseConnectionConfig` |  |
| `DatabaseManager` |  |

### Class: `Base`
**Inherits from:** DeclarativeBase

#### Attributes

| Name | Value |
| --- | --- |
| `metadata` | `    metadata = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'
    })` |

### Class: `DatabaseConnection`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, config) -> None:
```

### Class: `DatabaseConnectionConfig`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, name, db_type, host, port, database, user, password, pool_size, max_overflow, pool_recycle, echo) -> None:
```

### Class: `DatabaseManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `async_session` `async` |  |
| `check_connection` `async` |  |
| `create_tables` `async` |  |
| `create_tables_async` `async` |  |
| `execute` `async` |  |
| `execute_async` `async` |  |
| `execute_raw` `async` |  |
| `get_async_engine` `async` |  |
| `get_connection_names` `async` |  |
| `get_engine` `async` |  |
| `has_connection` `async` |  |
| `initialize` `async` |  |
| `register_connection` `async` |  |
| `session` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `unregister_connection` `async` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager) -> None:
```

##### `async_session`
```python
@asynccontextmanager
async def async_session(self, connection_name) -> AsyncGenerator[(AsyncSession, None)]:
```

##### `check_connection`
```python
async def check_connection(self, connection_name) -> bool:
```

##### `create_tables`
```python
async def create_tables(self, connection_name) -> None:
```

##### `create_tables_async`
```python
async def create_tables_async(self, connection_name) -> None:
```

##### `execute`
```python
async def execute(self, statement, connection_name) -> List[Dict[(str, Any)]]:
```

##### `execute_async`
```python
async def execute_async(self, statement, connection_name) -> List[Dict[(str, Any)]]:
```

##### `execute_raw`
```python
async def execute_raw(self, sql, params, connection_name) -> List[Dict[(str, Any)]]:
```

##### `get_async_engine`
```python
async def get_async_engine(self, connection_name) -> Optional[AsyncEngine]:
```

##### `get_connection_names`
```python
async def get_connection_names(self) -> List[str]:
```

##### `get_engine`
```python
async def get_engine(self, connection_name) -> Optional[Engine]:
```

##### `has_connection`
```python
async def has_connection(self, name) -> bool:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `register_connection`
```python
async def register_connection(self, config) -> None:
```

##### `session`
```python
@asynccontextmanager
async def session(self, connection_name) -> AsyncGenerator[(Session, None)]:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `unregister_connection`
```python
async def unregister_connection(self, name) -> bool:
```
