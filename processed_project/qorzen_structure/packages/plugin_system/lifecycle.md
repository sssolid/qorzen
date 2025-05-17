# Module: plugin_system.lifecycle

**Path:** `plugin_system/lifecycle.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import asyncio
import importlib
import inspect
import weakref
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
from qorzen.plugin_system.manifest import PluginLifecycleHook, PluginManifest
from qorzen.ui.ui_integration import UIIntegration
from qorzen.core.dependency_manager import DependencyManager
```

## Functions

| Function | Description |
| --- | --- |
| `cleanup_ui` |  |
| `execute_hook` |  |
| `find_plugin_hooks` |  |
| `get_lifecycle_manager` |  |
| `get_plugin_state` |  |
| `get_ui_integration` |  |
| `register_ui_integration` |  |
| `set_logger` |  |
| `set_plugin_manager` |  |
| `set_plugin_state` |  |
| `set_thread_manager` |  |
| `signal_ui_ready` |  |
| `wait_for_ui_ready` |  |

### `cleanup_ui`
```python
async def cleanup_ui(plugin_name) -> bool:
```

### `execute_hook`
```python
async def execute_hook(hook, plugin_name, manifest, plugin_instance, context, **kwargs) -> Any:
```

### `find_plugin_hooks`
```python
async def find_plugin_hooks(plugin_instance) -> Dict[(PluginLifecycleHook, str)]:
```

### `get_lifecycle_manager`
```python
def get_lifecycle_manager() -> LifecycleManager:
```

### `get_plugin_state`
```python
async def get_plugin_state(plugin_name) -> PluginLifecycleState:
```

### `get_ui_integration`
```python
async def get_ui_integration(plugin_name) -> Optional[UIIntegration]:
```

### `register_ui_integration`
```python
async def register_ui_integration(plugin_name, ui_integration, main_window) -> None:
```

### `set_logger`
```python
def set_logger(logger) -> None:
```

### `set_plugin_manager`
```python
def set_plugin_manager(plugin_manager) -> None:
```

### `set_plugin_state`
```python
async def set_plugin_state(plugin_name, state) -> None:
```

### `set_thread_manager`
```python
def set_thread_manager(thread_manager) -> None:
```

### `signal_ui_ready`
```python
async def signal_ui_ready(plugin_name) -> None:
```

### `wait_for_ui_ready`
```python
async def wait_for_ui_ready(plugin_name, timeout) -> bool:
```

## Classes

| Class | Description |
| --- | --- |
| `LifecycleHookError` |  |
| `LifecycleManager` |  |
| `PluginLifecycleState` |  |

### Class: `LifecycleHookError`
**Inherits from:** Exception

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, hook, plugin_name, message):
```

### Class: `LifecycleManager`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cleanup_ui` `async` |  |
| `execute_hook` `async` |  |
| `find_plugin_hooks` `async` |  |
| `get_plugin_state` `async` |  |
| `get_ui_integration` `async` |  |
| `log` |  |
| `register_ui_integration` `async` |  |
| `set_logger` |  |
| `set_plugin_manager` |  |
| `set_plugin_state` `async` |  |
| `set_thread_manager` |  |
| `signal_ui_ready` `async` |  |
| `wait_for_ui_ready` `async` |  |

##### `__init__`
```python
def __init__(self, logger_manager):
```

##### `cleanup_ui`
```python
async def cleanup_ui(self, plugin_name) -> bool:
```

##### `execute_hook`
```python
async def execute_hook(self, hook, plugin_name, manifest, plugin_instance, context) -> Any:
```

##### `find_plugin_hooks`
```python
async def find_plugin_hooks(self, plugin_instance) -> Dict[(PluginLifecycleHook, str)]:
```

##### `get_plugin_state`
```python
async def get_plugin_state(self, plugin_name) -> PluginLifecycleState:
```

##### `get_ui_integration`
```python
async def get_ui_integration(self, plugin_name) -> Optional[UIIntegration]:
```

##### `log`
```python
def log(self, message, level) -> None:
```

##### `register_ui_integration`
```python
async def register_ui_integration(self, plugin_name, ui_integration, main_window) -> None:
```

##### `set_logger`
```python
def set_logger(self, logger) -> None:
```

##### `set_plugin_manager`
```python
def set_plugin_manager(self, plugin_manager) -> None:
```

##### `set_plugin_state`
```python
async def set_plugin_state(self, plugin_name, state) -> None:
```

##### `set_thread_manager`
```python
def set_thread_manager(self, thread_manager) -> None:
```

##### `signal_ui_ready`
```python
async def signal_ui_ready(self, plugin_name) -> None:
```

##### `wait_for_ui_ready`
```python
async def wait_for_ui_ready(self, plugin_name, timeout) -> bool:
```

### Class: `PluginLifecycleState`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `DISCOVERED` | `    DISCOVERED = auto()` |
| `LOADING` | `    LOADING = auto()` |
| `INITIALIZING` | `    INITIALIZING = auto()` |
| `INITIALIZED` | `    INITIALIZED = auto()` |
| `UI_READY` | `    UI_READY = auto()` |
| `ACTIVE` | `    ACTIVE = auto()` |
| `DISABLING` | `    DISABLING = auto()` |
| `INACTIVE` | `    INACTIVE = auto()` |
| `FAILED` | `    FAILED = auto()` |
