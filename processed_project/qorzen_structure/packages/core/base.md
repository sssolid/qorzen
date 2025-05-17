# Module: core.base

**Path:** `core/base.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import asyncio
import logging
from typing import Any, Dict, Optional, Protocol, TypeVar, runtime_checkable
```

## Global Variables
```python
T = T = TypeVar('T', bound='AsyncBaseManager')
```

## Classes

| Class | Description |
| --- | --- |
| `BaseManager` |  |
| `QorzenManager` |  |

### Class: `BaseManager`
**Inherits from:** Protocol
**Decorators:**
- `@runtime_checkable`

#### Methods

| Method | Description |
| --- | --- |
| `initialize` `async` |  |
| `shutdown` `async` |  |
| `status` |  |

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

### Class: `QorzenManager`
**Inherits from:** abc.ABC

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `healthy` `@property` |  |
| `initialize` `async` |  |
| `initialized` `@property` |  |
| `name` `@property` |  |
| `set_logger` |  |
| `shutdown` `async` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self, name) -> None:
```

##### `healthy`
```python
@property
def healthy(self) -> bool:
```

##### `initialize`
```python
@abc.abstractmethod
async def initialize(self) -> None:
```

##### `initialized`
```python
@property
def initialized(self) -> bool:
```

##### `name`
```python
@property
def name(self) -> str:
```

##### `set_logger`
```python
def set_logger(self, logger) -> None:
```

##### `shutdown`
```python
@abc.abstractmethod
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```
