# Module: core.database_manager

**Path:** `core/database_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import uuid
import asyncio
import functools
import importlib
import os
import time
from contextlib import asynccontextmanager
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TypeVar, Union, cast, Callable, Awaitable, AsyncGenerator, Type, Protocol, runtime_checkable, Tuple
import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import DatabaseError, ManagerInitializationError, ManagerShutdownError, DatabaseManagerInitializationError, SecurityError, ConfigurationError, ValidationError
```

## Global Variables
```python
T = T = TypeVar('T')
R = R = TypeVar('R')
```

## Functions

| Function | Description |
| --- | --- |
| `create_connection_config` |  |

### `create_connection_config`
```python
def create_connection_config(self, name, db_type, **kwargs) -> DatabaseConnectionConfig:
```

## Classes

| Class | Description |
| --- | --- |
| `Base` |  |
| `ConnectionType` |  |
| `DatabaseConnection` |  |
| `DatabaseConnectionConfig` |  |
| `DatabaseConnectorProtocol` |  |
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

### Class: `ConnectionType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `POSTGRESQL` | `'postgresql'` |
| `MYSQL` | `'mysql'` |
| `SQLITE` | `'sqlite'` |
| `ORACLE` | `'oracle'` |
| `MSSQL` | `'mssql'` |
| `AS400` | `'as400'` |
| `ODBC` | `'odbc'` |

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
def __init__(self, name, db_type, host, port, database, user, password, pool_size, max_overflow, pool_recycle, echo, connection_string, url, connection_timeout, properties, read_only, ssl, allowed_tables, dsn, jt400_jar_path, mapping_enabled, history_enabled, validation_enabled, history_connection_id, validation_connection_id) -> None:
```

### Class: `DatabaseConnectorProtocol`
**Inherits from:** Protocol
**Decorators:**
- `@runtime_checkable`

#### Methods

| Method | Description |
| --- | --- |
| `config` `@property` |  |
| `connect` `async` |  |
| `disconnect` `async` |  |
| `execute_query` `async` |  |
| `get_connection_info` |  |
| `get_table_columns` `async` |  |
| `get_tables` `async` |  |
| `is_connected` `@property` |  |
| `set_database_manager` |  |
| `test_connection` `async` |  |

##### `config`
```python
@property
def config(self) -> 'DatabaseConnectionConfig':
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
async def test_connection(self) -> tuple[(bool, Optional[str])]:
```

### Class: `DatabaseManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `async_session` `async` |  |
| `check_connection` `async` |  |
| `create_field_mapping` `async` |  |
| `create_history_schedule` `async` |  |
| `create_tables` `async` |  |
| `create_tables_async` `async` |  |
| `create_validation_rule` `async` |  |
| `delete_field_mapping` `async` |  |
| `delete_history_schedule` `async` |  |
| `delete_validation_rule` `async` |  |
| `execute` `async` |  |
| `execute_async` `async` |  |
| `execute_history_schedule_now` `async` |  |
| `execute_query` `async` |  |
| `execute_raw` `async` |  |
| `get_all_field_mappings` `async` |  |
| `get_all_history_schedules` `async` |  |
| `get_all_validation_rules` `async` |  |
| `get_async_engine` `async` |  |
| `get_connection_names` `async` |  |
| `get_engine` `async` |  |
| `get_field_mapping` `async` |  |
| `get_history_data` `async` |  |
| `get_history_entries` `async` |  |
| `get_history_schedule` `async` |  |
| `get_supported_connection_types` |  |
| `get_table_columns` `async` |  |
| `get_tables` `async` |  |
| `get_validation_rule` `async` |  |
| `has_connection` `async` |  |
| `initialize` `async` |  |
| `register_connection` `async` |  |
| `register_connector_type` |  |
| `session` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `test_connection_config` `async` |  |
| `unregister_connection` `async` |  |
| `update_history_schedule` `async` |  |
| `update_validation_rule` `async` |  |
| `validate_connection_config` |  |
| `validate_data` `async` |  |

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

##### `create_field_mapping`
```python
async def create_field_mapping(self, connection_id, table_name, mappings, description) -> Dict[(str, Any)]:
```

##### `create_history_schedule`
```python
async def create_history_schedule(self, connection_id, query_id, frequency, name, description, retention_days) -> Dict[(str, Any)]:
```

##### `create_tables`
```python
async def create_tables(self, connection_name) -> None:
```

##### `create_tables_async`
```python
async def create_tables_async(self, connection_name) -> None:
```

##### `create_validation_rule`
```python
async def create_validation_rule(self, rule_type, connection_id, table_name, field_name, parameters, error_message, name, description) -> Dict[(str, Any)]:
```

##### `delete_field_mapping`
```python
async def delete_field_mapping(self, mapping_id) -> bool:
```

##### `delete_history_schedule`
```python
async def delete_history_schedule(self, schedule_id) -> bool:
```

##### `delete_validation_rule`
```python
async def delete_validation_rule(self, rule_id) -> bool:
```

##### `execute`
```python
async def execute(self, statement, connection_name) -> List[Dict[(str, Any)]]:
```

##### `execute_async`
```python
async def execute_async(self, statement, connection_name) -> List[Dict[(str, Any)]]:
```

##### `execute_history_schedule_now`
```python
async def execute_history_schedule_now(self, schedule_id) -> Dict[(str, Any)]:
```

##### `execute_query`
```python
async def execute_query(self, query, params, connection_name, limit, apply_mapping) -> Dict[(str, Any)]:
```

##### `execute_raw`
```python
async def execute_raw(self, sql, params, connection_name, limit) -> List[Dict[(str, Any)]]:
```

##### `get_all_field_mappings`
```python
async def get_all_field_mappings(self, connection_id) -> List[Dict[(str, Any)]]:
```

##### `get_all_history_schedules`
```python
async def get_all_history_schedules(self) -> List[Dict[(str, Any)]]:
```

##### `get_all_validation_rules`
```python
async def get_all_validation_rules(self, connection_id, table_name) -> List[Dict[(str, Any)]]:
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

##### `get_field_mapping`
```python
async def get_field_mapping(self, connection_id, table_name) -> Optional[Dict[(str, Any)]]:
```

##### `get_history_data`
```python
async def get_history_data(self, snapshot_id) -> Optional[Dict[(str, Any)]]:
```

##### `get_history_entries`
```python
async def get_history_entries(self, schedule_id, limit) -> List[Dict[(str, Any)]]:
```

##### `get_history_schedule`
```python
async def get_history_schedule(self, schedule_id) -> Optional[Dict[(str, Any)]]:
```

##### `get_supported_connection_types`
```python
def get_supported_connection_types(self) -> List[str]:
```

##### `get_table_columns`
```python
async def get_table_columns(self, table_name, connection_name, schema) -> List[Dict[(str, Any)]]:
```

##### `get_tables`
```python
async def get_tables(self, connection_name, schema) -> List[Dict[(str, Any)]]:
```

##### `get_validation_rule`
```python
async def get_validation_rule(self, rule_id) -> Optional[Dict[(str, Any)]]:
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

##### `register_connector_type`
```python
def register_connector_type(self, connection_type, connector_class) -> None:
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

##### `test_connection_config`
```python
async def test_connection_config(self, config) -> Tuple[(bool, Optional[str])]:
```

##### `unregister_connection`
```python
async def unregister_connection(self, name) -> bool:
```

##### `update_history_schedule`
```python
async def update_history_schedule(self, schedule_id, **updates) -> Dict[(str, Any)]:
```

##### `update_validation_rule`
```python
async def update_validation_rule(self, rule_id, **updates) -> Dict[(str, Any)]:
```

##### `validate_connection_config`
```python
def validate_connection_config(self, config) -> Tuple[(bool, Optional[str])]:
```

##### `validate_data`
```python
async def validate_data(self, connection_id, table_name, data) -> List[Dict[(str, Any)]]:
```
