# Module: core.plugin_isolation_manager

**Path:** `core/plugin_isolation_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import importlib.util
import inspect
import os
import pathlib
import signal
import sys
import tempfile
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import PluginIsolationError, ManagerInitializationError, ManagerShutdownError
```

## Classes

| Class | Description |
| --- | --- |
| `IsolatedPluginInfo` |  |
| `PluginIsolationLevel` |  |
| `PluginIsolationManager` |  |
| `PluginIsolator` |  |
| `PluginResourceLimits` |  |
| `ThreadIsolator` |  |

### Class: `IsolatedPluginInfo`
**Decorators:**
- `@dataclass`

### Class: `PluginIsolationLevel`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `NONE` | `'none'` |
| `THREAD` | `'thread'` |
| `PROCESS` | `'process'` |

### Class: `PluginIsolationManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_loaded_plugins` |  |
| `get_plugin_isolation_level` |  |
| `initialize` `async` |  |
| `is_plugin_loaded` |  |
| `load_plugin` `async` |  |
| `run_plugin_method` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `unload_plugin` `async` |  |

##### `__init__`
```python
def __init__(self, concurrency_manager, logger_manager, config_manager, name) -> None:
```

##### `get_loaded_plugins`
```python
def get_loaded_plugins(self) -> Dict[(str, PluginIsolationLevel)]:
```

##### `get_plugin_isolation_level`
```python
def get_plugin_isolation_level(self, plugin_id) -> Optional[PluginIsolationLevel]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `is_plugin_loaded`
```python
def is_plugin_loaded(self, plugin_id) -> bool:
```

##### `load_plugin`
```python
async def load_plugin(self, plugin_id, plugin_path, isolation_level) -> bool:
```

##### `run_plugin_method`
```python
async def run_plugin_method(self, plugin_id, method_name, args, kwargs, timeout) -> Any:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `unload_plugin`
```python
async def unload_plugin(self, plugin_id) -> bool:
```

### Class: `PluginIsolator`
**Inherits from:** ABC

#### Methods

| Method | Description |
| --- | --- |
| `initialize` `async` |  |
| `load_plugin` `async` |  |
| `run_plugin_method` `async` |  |
| `shutdown` `async` |  |
| `unload_plugin` `async` |  |

##### `initialize`
```python
@abstractmethod
async def initialize(self) -> None:
```

##### `load_plugin`
```python
@abstractmethod
async def load_plugin(self, plugin_id, plugin_path) -> bool:
```

##### `run_plugin_method`
```python
@abstractmethod
async def run_plugin_method(self, plugin_id, method_name, args, kwargs, timeout) -> Any:
```

##### `shutdown`
```python
@abstractmethod
async def shutdown(self) -> None:
```

##### `unload_plugin`
```python
@abstractmethod
async def unload_plugin(self, plugin_id) -> bool:
```

### Class: `PluginResourceLimits`
**Decorators:**
- `@dataclass`

### Class: `ThreadIsolator`
**Inherits from:** PluginIsolator

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `initialize` `async` |  |
| `load_plugin` `async` |  |
| `run_plugin_method` `async` |  |
| `shutdown` `async` |  |
| `unload_plugin` `async` |  |

##### `__init__`
```python
def __init__(self, concurrency_manager, logger) -> None:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `load_plugin`
```python
async def load_plugin(self, plugin_id, plugin_path) -> bool:
```

##### `run_plugin_method`
```python
async def run_plugin_method(self, plugin_id, method_name, args, kwargs, timeout) -> Any:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `unload_plugin`
```python
async def unload_plugin(self, plugin_id) -> bool:
```
