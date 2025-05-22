# Module: ui.ui_component

**Path:** `ui/ui_component.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
import traceback
import uuid
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union, cast, Awaitable
from PySide6.QtCore import QObject, Signal, Slot, Qt, QEvent
from PySide6.QtWidgets import QWidget
```

## Global Variables
```python
T = T = TypeVar('T')
```

## Functions

| Function | Description |
| --- | --- |
| `run_async` |  |

### `run_async`
```python
def run_async(coro) -> T:
```

## Classes

| Class | Description |
| --- | --- |
| `AsyncQWidget` |  |
| `AsyncTaskSignals` |  |

### Class: `AsyncQWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cancel_all_tasks` |  |
| `cancel_task` |  |
| `closeEvent` |  |
| `get_running_tasks_count` |  |
| `is_task_running` |  |
| `run_async_task` |  |

##### `__init__`
```python
def __init__(self, parent, concurrency_manager) -> None:
```

##### `cancel_all_tasks`
```python
def cancel_all_tasks(self) -> int:
```

##### `cancel_task`
```python
def cancel_task(self, task_id) -> bool:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

##### `get_running_tasks_count`
```python
def get_running_tasks_count(self) -> int:
```

##### `is_task_running`
```python
def is_task_running(self, task_id) -> bool:
```

##### `run_async_task`
```python
def run_async_task(self, coroutine_func, task_id, on_result, on_error, on_finished, *args, **kwargs) -> str:
```

### Class: `AsyncTaskSignals`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `started` | `    started = Signal()` |
| `result_ready` | `    result_ready = Signal(object)` |
| `error` | `    error = Signal(str, str)` |
| `finished` | `    finished = Signal()` |
