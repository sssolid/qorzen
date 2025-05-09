# Module: core.base

**Path:** `core/base.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import abc
from typing import Any, Dict, Optional, Protocol, TypeVar, runtime_checkable
```

## Global Variables
```python
T = T = TypeVar("T", bound="BaseManager")
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
| `initialize` |  |
| `shutdown` |  |
| `status` |  |

##### `initialize`
```python
def initialize(self) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
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
| `initialize` |  |
| `initialized` `@property` |  |
| `name` `@property` |  |
| `shutdown` |  |
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
def initialize(self) -> None:
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

##### `shutdown`
```python
@abc.abstractmethod
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```
