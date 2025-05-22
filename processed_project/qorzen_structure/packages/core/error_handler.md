# Module: core.error_handler

**Path:** `core/error_handler.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import inspect
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast
from qorzen.utils import EventBusError
```

## Global Variables
```python
T = T = TypeVar('T')
```

## Functions

| Function | Description |
| --- | --- |
| `create_error_boundary` |  |
| `get_global_error_handler` |  |
| `install_global_exception_hook` |  |
| `safe_async` |  |
| `safe_sync` |  |
| `set_global_error_handler` |  |

### `create_error_boundary`
```python
def create_error_boundary(source, plugin_id, component) -> ErrorBoundary:
```

### `get_global_error_handler`
```python
def get_global_error_handler() -> Optional[ErrorHandler]:
```

### `install_global_exception_hook`
```python
def install_global_exception_hook() -> None:
```

### `safe_async`
```python
def safe_async(source, severity, plugin_id, component) -> Callable[([Callable[(Ellipsis, T)]], Callable[(Ellipsis, T)])]:
```

### `safe_sync`
```python
def safe_sync(source, severity, plugin_id, component) -> Callable[([Callable[(Ellipsis, T)]], Callable[(Ellipsis, T)])]:
```

### `set_global_error_handler`
```python
def set_global_error_handler(handler) -> None:
```

## Classes

| Class | Description |
| --- | --- |
| `ErrorBoundary` |  |
| `ErrorHandler` |  |
| `ErrorInfo` |  |
| `ErrorSeverity` |  |

### Class: `ErrorBoundary`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `run` `async` |  |
| `wrap` |  |

##### `__init__`
```python
def __init__(self, error_handler, source, plugin_id, component) -> None:
```

##### `run`
```python
async def run(self, func, severity, *args, **kwargs) -> Optional[T]:
```

##### `wrap`
```python
def wrap(self, severity) -> Callable[([Callable[(Ellipsis, T)]], Callable[(Ellipsis, T)])]:
```

### Class: `ErrorHandler`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `clear_errors` `async` |  |
| `create_boundary` |  |
| `get_error` `async` |  |
| `get_errors` `async` |  |
| `handle_error` `async` |  |
| `initialize` `async` |  |
| `register_error_strategy` `async` |  |
| `register_error_subscriber` `async` |  |
| `status` |  |
| `unregister_error_strategy` `async` |  |
| `unregister_error_subscriber` `async` |  |

##### `__init__`
```python
def __init__(self, event_bus_manager, logger_manager, config_manager) -> None:
```

##### `clear_errors`
```python
async def clear_errors(self, error_ids, source, plugin_id) -> int:
```

##### `create_boundary`
```python
def create_boundary(self, source, plugin_id, component) -> ErrorBoundary:
```

##### `get_error`
```python
async def get_error(self, error_id) -> Optional[ErrorInfo]:
```

##### `get_errors`
```python
async def get_errors(self, source, severity, plugin_id, component, handled, limit) -> List[ErrorInfo]:
```

##### `handle_error`
```python
async def handle_error(self, message, source, severity, plugin_id, component, traceback, metadata) -> bool:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `register_error_strategy`
```python
async def register_error_strategy(self, source, strategy, plugin_id, component) -> None:
```

##### `register_error_subscriber`
```python
async def register_error_subscriber(self, subscriber) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `unregister_error_strategy`
```python
async def unregister_error_strategy(self, source, plugin_id, component) -> bool:
```

##### `unregister_error_subscriber`
```python
async def unregister_error_subscriber(self, subscriber) -> bool:
```

### Class: `ErrorInfo`
**Decorators:**
- `@dataclass`

### Class: `ErrorSeverity`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `LOW` | `'low'` |
| `MEDIUM` | `'medium'` |
| `HIGH` | `'high'` |
| `CRITICAL` | `'critical'` |
