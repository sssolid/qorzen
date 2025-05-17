# Module: core.task_manager

**Path:** `core/task_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, TaskError
```

## Global Variables
```python
T = T = TypeVar('T')
```

## Classes

| Class | Description |
| --- | --- |
| `TaskCategory` |  |
| `TaskInfo` |  |
| `TaskManager` |  |
| `TaskPriority` |  |
| `TaskProgress` |  |
| `TaskStatus` |  |

### Class: `TaskCategory`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `CORE` | `'core'` |
| `PLUGIN` | `'plugin'` |
| `UI` | `'ui'` |
| `IO` | `'io'` |
| `BACKGROUND` | `'background'` |
| `USER` | `'user'` |

### Class: `TaskInfo`
**Decorators:**
- `@dataclass`

### Class: `TaskManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cancel_task` `async` |  |
| `get_task_info` `async` |  |
| `get_tasks` `async` |  |
| `initialize` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `submit_async_task` `async` |  |
| `submit_task` `async` |  |
| `wait_for_task` `async` |  |

##### `__init__`
```python
def __init__(self, concurrency_manager, event_bus_manager, logger_manager, config_manager) -> None:
```

##### `cancel_task`
```python
async def cancel_task(self, task_id) -> bool:
```

##### `get_task_info`
```python
async def get_task_info(self, task_id) -> Optional[TaskInfo]:
```

##### `get_tasks`
```python
async def get_tasks(self, status, category, plugin_id, limit) -> List[TaskInfo]:
```

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

##### `submit_async_task`
```python
async def submit_async_task(self, func, name, category, plugin_id, priority, metadata, timeout, cancellable, *args, **kwargs) -> str:
```

##### `submit_task`
```python
async def submit_task(self, func, name, category, plugin_id, priority, metadata, timeout, cancellable, *args, **kwargs) -> str:
```

##### `wait_for_task`
```python
async def wait_for_task(self, task_id, timeout) -> TaskInfo:
```

### Class: `TaskPriority`
**Inherits from:** int, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `LOW` | `0` |
| `NORMAL` | `50` |
| `HIGH` | `100` |
| `CRITICAL` | `200` |

### Class: `TaskProgress`
**Decorators:**
- `@dataclass`

### Class: `TaskStatus`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `PENDING` | `'pending'` |
| `RUNNING` | `'running'` |
| `COMPLETED` | `'completed'` |
| `FAILED` | `'failed'` |
| `CANCELLED` | `'cancelled'` |
