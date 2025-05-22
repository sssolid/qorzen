# Module: utils.qtasync

**Path:** `utils/qtasync.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import functools
import sys
import threading
from typing import Any, Callable, Dict, Optional, Set, Tuple, TypeVar, cast, Coroutine, Awaitable
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QEventLoop, Qt
from PySide6.QtWidgets import QApplication
```

## Global Variables
```python
T = T = TypeVar('T')
```

## Functions

| Function | Description |
| --- | --- |
| `cancel_task` |  |
| `get_bridge` |  |
| `is_main_thread` |  |
| `run_coroutine` |  |
| `run_until_complete` |  |
| `shutdown_bridge` |  |

### `cancel_task`
```python
def cancel_task(task_id) -> bool:
```

### `get_bridge`
```python
def get_bridge() -> QtAsyncBridge:
```

### `is_main_thread`
```python
def is_main_thread() -> bool:
```

### `run_coroutine`
```python
def run_coroutine(coro, task_id, on_result, on_error) -> str:
```

### `run_until_complete`
```python
def run_until_complete(coro) -> T:
```

### `shutdown_bridge`
```python
def shutdown_bridge() -> None:
```

## Classes

| Class | Description |
| --- | --- |
| `QtAsyncBridge` |  |

### Class: `QtAsyncBridge`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `task_result` | `    task_result = Signal(object)` |
| `task_error` | `    task_error = Signal(str, str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cancel_all_tasks` |  |
| `cancel_task` |  |
| `is_main_thread` |  |
| `run_coroutine` |  |
| `shutdown` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `cancel_all_tasks`
```python
def cancel_all_tasks(self) -> int:
```

##### `cancel_task`
```python
def cancel_task(self, task_id) -> bool:
```

##### `is_main_thread`
```python
def is_main_thread(self) -> bool:
```

##### `run_coroutine`
```python
def run_coroutine(self, coro, task_id, on_result, on_error) -> str:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```
