# Module: core.concurrency_manager

**Path:** `core/concurrency_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import concurrent.futures
import functools
import logging
import os
import threading
import traceback
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, ThreadManagerError
```

## Global Variables
```python
T = T = TypeVar('T')
R = R = TypeVar('R')
```

## Classes

| Class | Description |
| --- | --- |
| `ConcurrencyManager` |  |
| `TaskPriority` |  |

### Class: `ConcurrencyManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `initialize` `async` |  |
| `is_main_thread` |  |
| `run_in_process` `async` |  |
| `run_in_thread` `async` |  |
| `run_io_task` `async` |  |
| `run_on_main_thread` `async` |  |
| `shutdown` `async` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager) -> None:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `is_main_thread`
```python
def is_main_thread(self) -> bool:
```

##### `run_in_process`
```python
async def run_in_process(self, func, *args, **kwargs) -> T:
```

##### `run_in_thread`
```python
async def run_in_thread(self, func, *args, **kwargs) -> T:
```

##### `run_io_task`
```python
async def run_io_task(self, func, *args, **kwargs) -> T:
```

##### `run_on_main_thread`
```python
async def run_on_main_thread(self, func, *args, **kwargs) -> T:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

### Class: `TaskPriority`
**Inherits from:** int

#### Attributes

| Name | Value |
| --- | --- |
| `LOW` | `0` |
| `NORMAL` | `50` |
| `HIGH` | `100` |
| `CRITICAL` | `200` |
