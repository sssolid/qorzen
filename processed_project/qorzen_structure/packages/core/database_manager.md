# Module: core.database_manager

**Path:** `core/database_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import contextlib
import functools
import threading
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, TypeVar, Union, cast
import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import DatabaseError, ManagerInitializationError, ManagerShutdownError
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
| `metadata` | `    metadata = MetaData(
        naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_%(constraint_name)s',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s'
        }
    )` |

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
| `check_connection` |  |
| `create_tables` |  |
| `create_tables_async` `async` |  |
| `execute` |  |
| `execute_async` `async` |  |
| `execute_raw` |  |
| `get_async_engine` |  |
| `get_connection_names` |  |
| `get_engine` |  |
| `has_connection` |  |
| `initialize` |  |
| `register_connection` |  |
| `session` |  |
| `shutdown` |  |
| `status` |  |
| `unregister_connection` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager) -> None:
```

##### `async_session`
```python
async def async_session(self, connection_name) -> AsyncSession:
```

##### `check_connection`
```python
def check_connection(self, connection_name) -> bool:
```

##### `create_tables`
```python
def create_tables(self, connection_name) -> None:
```

##### `create_tables_async`
```python
async def create_tables_async(self, connection_name) -> None:
```

##### `execute`
```python
def execute(self, statement, connection_name) -> List[Dict[(str, Any)]]:
```

##### `execute_async`
```python
async def execute_async(self, statement, connection_name) -> List[Dict[(str, Any)]]:
```

##### `execute_raw`
```python
def execute_raw(self, sql, params, connection_name) -> List[Dict[(str, Any)]]:
```

##### `get_async_engine`
```python
def get_async_engine(self, connection_name) -> Optional[AsyncEngine]:
```

##### `get_connection_names`
```python
def get_connection_names(self) -> List[str]:
```

##### `get_engine`
```python
def get_engine(self, connection_name) -> Optional[Engine]:
```

##### `has_connection`
```python
def has_connection(self, name) -> bool:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `register_connection`
```python
def register_connection(self, config) -> None:
```

##### `session`
```python
@contextlib.contextmanager
def session(self, connection_name) -> Generator[(Session, None, None)]:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `unregister_connection`
```python
def unregister_connection(self, name) -> bool:
```
