# Module: core.dependency_manager

**Path:** `core/dependency_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
import networkx as nx
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast
from qorzen.core.base import QorzenManager, BaseManager
from qorzen.utils.exceptions import DependencyError, ManagerInitializationError, ManagerShutdownError, DatabaseManagerInitializationError
```

## Global Variables
```python
T = T = TypeVar('T', bound=BaseManager)
```

## Classes

| Class | Description |
| --- | --- |
| `DependencyManager` |  |

### Class: `DependencyManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_manager` |  |
| `get_manager_typed` |  |
| `initialize` `async` |  |
| `initialize_all` `async` |  |
| `register_manager` |  |
| `shutdown` `async` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self, logger_manager) -> None:
```

##### `get_manager`
```python
def get_manager(self, name) -> Optional[BaseManager]:
```

##### `get_manager_typed`
```python
def get_manager_typed(self, name, manager_type) -> Optional[T]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `initialize_all`
```python
async def initialize_all(self) -> None:
```

##### `register_manager`
```python
def register_manager(self, manager, dependencies) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```
