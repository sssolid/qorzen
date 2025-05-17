# Module: plugins.database_connector_plugin.code.connectors.base

**Path:** `plugins/database_connector_plugin/code/connectors/base.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Protocol, TypeVar
from models import BaseConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
```

## Global Variables
```python
TableList = TableList = List[TableMetadata]
FieldList = FieldList = List[ColumnMetadata]
T = T = TypeVar('T', bound=BaseConnectionConfig)
```

## Classes

| Class | Description |
| --- | --- |
| `BaseDatabaseConnector` |  |
| `DatabaseConnectorProtocol` |  |

### Class: `BaseDatabaseConnector`
**Inherits from:** abc.ABC

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cancel_query` `async` |  |
| `config` `@property` |  |
| `connect` `async` |  |
| `disconnect` `async` |  |
| `execute_query` `async` |  |
| `get_connection_info` |  |
| `get_table_columns` `async` |  |
| `get_tables` `async` |  |
| `is_connected` `@property` |  |
| `test_connection` `async` |  |

##### `__init__`
```python
def __init__(self, config, logger) -> None:
```

##### `cancel_query`
```python
async def cancel_query(self) -> bool:
```

##### `config`
```python
@property
def config(self) -> BaseConnectionConfig:
```

##### `connect`
```python
@abc.abstractmethod
async def connect(self) -> None:
```

##### `disconnect`
```python
@abc.abstractmethod
async def disconnect(self) -> None:
```

##### `execute_query`
```python
@abc.abstractmethod
async def execute_query(self, query, params, limit) -> QueryResult:
```

##### `get_connection_info`
```python
@abc.abstractmethod
def get_connection_info(self) -> Dict[(str, Any)]:
```

##### `get_table_columns`
```python
@abc.abstractmethod
async def get_table_columns(self, table_name, schema) -> FieldList:
```

##### `get_tables`
```python
@abc.abstractmethod
async def get_tables(self, schema) -> TableList:
```

##### `is_connected`
```python
@property
def is_connected(self) -> bool:
```

##### `test_connection`
```python
async def test_connection(self) -> Tuple[(bool, Optional[str])]:
```

### Class: `DatabaseConnectorProtocol`
**Inherits from:** Protocol[T]

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
| `test_connection` `async` |  |

##### `config`
```python
@property
def config(self) -> T:
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
async def execute_query(self, query, params, limit) -> QueryResult:
```

##### `get_connection_info`
```python
def get_connection_info(self) -> Dict[(str, Any)]:
```

##### `get_table_columns`
```python
async def get_table_columns(self, table_name, schema) -> FieldList:
```

##### `get_tables`
```python
async def get_tables(self, schema) -> TableList:
```

##### `is_connected`
```python
@property
def is_connected(self) -> bool:
```

##### `test_connection`
```python
async def test_connection(self) -> Tuple[(bool, Optional[str])]:
```
