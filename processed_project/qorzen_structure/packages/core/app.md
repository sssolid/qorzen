# Module: core.app

**Path:** `core/app.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import importlib
import inspect
import logging
import os
import signal
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, cast, T
from qorzen.core.base import QorzenManager, BaseManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.dependency_manager import DependencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory
from qorzen.core.plugin_isolation_manager import PluginIsolationManager, PluginIsolationLevel
from qorzen.utils.exceptions import ApplicationError
```

## Classes

| Class | Description |
| --- | --- |
| `ApplicationCore` |  |

### Class: `ApplicationCore`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_manager` |  |
| `get_manager_typed` |  |
| `get_ui_integration` |  |
| `initialize` `async` |  |
| `is_initialized` |  |
| `set_ui_integration` |  |
| `setup_signal_handlers` |  |
| `shutdown` `async` |  |
| `status` |  |
| `status_async` `async` |  |
| `submit_core_task` `async` |  |
| `wait_for_shutdown` `async` |  |

##### `__init__`
```python
def __init__(self, config_path) -> None:
```

##### `get_manager`
```python
def get_manager(self, name) -> Optional[BaseManager]:
```

##### `get_manager_typed`
```python
def get_manager_typed(self, name, manager_type) -> Optional[T]:
```

##### `get_ui_integration`
```python
def get_ui_integration(self) -> Any:
```

##### `initialize`
```python
async def initialize(self, progress_callback) -> None:
```

##### `is_initialized`
```python
def is_initialized(self) -> bool:
```

##### `set_ui_integration`
```python
def set_ui_integration(self, ui_integration) -> None:
```

##### `setup_signal_handlers`
```python
def setup_signal_handlers(self) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `status_async`
```python
async def status_async(self) -> Dict[(str, Any)]:
```

##### `submit_core_task`
```python
async def submit_core_task(self, func, name, *args, **kwargs) -> str:
```

##### `wait_for_shutdown`
```python
async def wait_for_shutdown(self) -> None:
```
