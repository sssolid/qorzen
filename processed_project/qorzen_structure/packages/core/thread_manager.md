# Module: core.thread_manager

**Path:** `core/thread_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import concurrent.futures
import functools
import logging
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union, cast
from PySide6.QtCore import QMetaObject, QObject, Qt, Signal, Slot
from pydantic import BaseModel, Field
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, ThreadManagerError
```

## Global Variables
```python
T = T = TypeVar("T")
R = R = TypeVar("R")
```

## Classes

| Class | Description |
| --- | --- |
| `Config` |  |
| `QtTaskBridge` |  |
| `TaskInfo` |  |
| `TaskPriority` |  |
| `TaskProgressReporter` |  |
| `TaskResult` |  |
| `TaskStatus` |  |
| `ThreadExecutionContext` |  |
| `ThreadManager` |  |

### Class: `Config`

#### Attributes

| Name | Value |
| --- | --- |
| `arbitrary_types_allowed` | `True` |

### Class: `QtTaskBridge`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `taskCompleted` | `    taskCompleted = Signal(str, object)` |
| `taskFailed` | `    taskFailed = Signal(str, str, str)  # task_id, error_message, error_traceback` |
| `taskProgress` | `    taskProgress = Signal(str, int, str)  # task_id, progress_percent, status_message` |
| `executeOnMainThread` | `    executeOnMainThread = Signal(object, tuple, dict, object)  # func, args, kwargs, callback_event` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

### Class: `TaskInfo`
**Decorators:**
- `@dataclass`

### Class: `TaskPriority`
**Inherits from:** int, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `LOW` | `0` |
| `NORMAL` | `50` |
| `HIGH` | `100` |
| `CRITICAL` | `200` |

### Class: `TaskProgressReporter`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `report_progress` |  |

##### `__init__`
```python
def __init__(self, task_id, task_bridge, execution_context, thread_manager) -> None:
```

##### `report_progress`
```python
def report_progress(self, percent, message) -> None:
```

### Class: `TaskResult`
**Inherits from:** BaseModel

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

### Class: `ThreadExecutionContext`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `WORKER_THREAD` | `    WORKER_THREAD = auto()  # Execute in worker thread pool` |
| `MAIN_THREAD` | `    MAIN_THREAD = auto()  # Execute in the main Qt thread` |
| `CURRENT_THREAD` | `    CURRENT_THREAD = auto()  # Execute in the current thread` |

### Class: `ThreadManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cancel_periodic_task` |  |
| `cancel_task` |  |
| `execute_on_main_thread_sync` |  |
| `get_task_info` |  |
| `get_task_result` |  |
| `initialize` |  |
| `is_main_thread` |  |
| `run_on_main_thread` |  |
| `schedule_periodic_task` |  |
| `shutdown` |  |
| `status` |  |
| `submit_async_task` |  |
| `submit_main_thread_task` |  |
| `submit_qt_task` |  |
| `submit_task` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager) -> None:
```

##### `cancel_periodic_task`
```python
def cancel_periodic_task(self, task_id) -> bool:
```

##### `cancel_task`
```python
def cancel_task(self, task_id) -> bool:
```

##### `execute_on_main_thread_sync`
```python
def execute_on_main_thread_sync(self, func, *args, **kwargs) -> T:
```

##### `get_task_info`
```python
def get_task_info(self, task_id) -> Optional[Dict[(str, Any)]]:
```

##### `get_task_result`
```python
def get_task_result(self, task_id, timeout) -> Any:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `is_main_thread`
```python
def is_main_thread(self) -> bool:
```

##### `run_on_main_thread`
```python
def run_on_main_thread(self, func, *args, **kwargs) -> None:
```

##### `schedule_periodic_task`
```python
def schedule_periodic_task(self, interval, func, task_id, *args, **kwargs) -> str:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `submit_async_task`
```python
def submit_async_task(self, coro_func, name, submitter, priority, on_completed, on_failed, *args, **kwargs) -> str:
```

##### `submit_main_thread_task`
```python
def submit_main_thread_task(self, func, on_completed, on_failed, name, priority, *args, **kwargs) -> str:
```

##### `submit_qt_task`
```python
def submit_qt_task(self, func, on_completed, on_failed, name, submitter, priority, *args, **kwargs) -> str:
```

##### `submit_task`
```python
def submit_task(self, func, name, submitter, priority, execution_context, metadata, result_handler, *args, **kwargs) -> str:
```
