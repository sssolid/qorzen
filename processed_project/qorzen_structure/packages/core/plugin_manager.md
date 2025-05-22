# Module: core.plugin_manager

**Path:** `core/plugin_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import importlib
import inspect
import os
import pathlib
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union, cast, Tuple
from qorzen.core.base import QorzenManager
from qorzen.core.error_handler import ErrorHandler, ErrorSeverity, create_error_boundary
from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.plugin_state_manager import PluginStateManager
from qorzen.utils.exceptions import PluginError, ManagerInitializationError, ManagerShutdownError
```

## Classes

| Class | Description |
| --- | --- |
| `PluginInfo` |  |
| `PluginManager` |  |
| `PluginManifest` |  |
| `PluginState` |  |

### Class: `PluginInfo`
**Decorators:**
- `@dataclass`

#### Methods

| Method | Description |
| --- | --- |
| `display_name` `@property` |  |

##### `display_name`
```python
@property
def display_name(self) -> str:
```

### Class: `PluginManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `disable_plugin` `async` |  |
| `enable_plugin` `async` |  |
| `get_plugin_info` `async` |  |
| `get_plugin_instance` `async` |  |
| `get_plugins` `async` |  |
| `initialize` `async` |  |
| `load_plugin` `async` |  |
| `reload_plugin` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `unload_plugin` `async` |  |

##### `__init__`
```python
def __init__(self, application_core, config_manager, logger_manager, event_bus_manager, file_manager, task_manager, plugin_isolation_manager) -> None:
```

##### `disable_plugin`
```python
async def disable_plugin(self, plugin_id) -> bool:
```

##### `enable_plugin`
```python
async def enable_plugin(self, plugin_id) -> bool:
```

##### `get_plugin_info`
```python
async def get_plugin_info(self, plugin_id) -> Optional[PluginInfo]:
```

##### `get_plugin_instance`
```python
async def get_plugin_instance(self, plugin_id) -> Optional[Any]:
```

##### `get_plugins`
```python
async def get_plugins(self, state) -> Dict[(str, PluginInfo)]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `load_plugin`
```python
async def load_plugin(self, plugin_id) -> bool:
```

##### `reload_plugin`
```python
async def reload_plugin(self, plugin_id) -> bool:
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

### Class: `PluginManifest`
**Decorators:**
- `@dataclass`

#### Methods

| Method | Description |
| --- | --- |
| `from_dict` |  |
| `load` |  |
| `to_dict` |  |

##### `from_dict`
```python
@classmethod
def from_dict(cls, data) -> PluginManifest:
```

##### `load`
```python
@classmethod
def load(cls, path) -> Optional[PluginManifest]:
```

##### `to_dict`
```python
def to_dict(self) -> Dict[(str, Any)]:
```

### Class: `PluginState`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `DISCOVERED` | `'discovered'` |
| `LOADING` | `'loading'` |
| `ACTIVE` | `'active'` |
| `INACTIVE` | `'inactive'` |
| `FAILED` | `'failed'` |
| `DISABLED` | `'disabled'` |
| `INCOMPATIBLE` | `'incompatible'` |
