# Module: core.plugin_manager

**Path:** `core/plugin_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import importlib
import importlib.metadata
import importlib.util
import inspect
import os
import pathlib
import pkgutil
import sys
import threading
import time
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType, Event
from qorzen.core.thread_manager import ThreadExecutionContext, TaskProgressReporter
from qorzen.ui.integration import UIIntegration, MainWindowIntegration
from qorzen.plugin_system.interface import PluginInterface
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook
from qorzen.plugin_system.lifecycle import execute_hook, set_logger as set_lifecycle_logger, get_lifecycle_manager, register_ui_integration, cleanup_ui, get_plugin_state, set_plugin_state, PluginLifecycleState, wait_for_ui_ready, signal_ui_ready, set_thread_manager
from qorzen.plugin_system.extension import register_plugin_extensions, unregister_plugin_extensions, extension_registry
from qorzen.plugin_system.config_schema import ConfigSchema
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, PluginError
```

## Classes

| Class | Description |
| --- | --- |
| `PluginInfo` |  |
| `PluginManager` |  |
| `PluginState` |  |

### Class: `PluginInfo`
**Decorators:**
- `@dataclass`

#### Methods

| Method | Description |
| --- | --- |
| `__post_init__` |  |

##### `__post_init__`
```python
def __post_init__(self) -> None:
```

### Class: `PluginManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `disable_plugin` |  |
| `enable_plugin` |  |
| `get_all_plugins` |  |
| `initialize` |  |
| `install_plugin` |  |
| `load_plugin` |  |
| `reload_plugin` |  |
| `shutdown` |  |
| `status` |  |
| `uninstall_plugin` |  |
| `unload_plugin` |  |
| `update_plugin` |  |

##### `__init__`
```python
def __init__(self, application_core, config_manager, logger_manager, event_bus_manager, file_manager, thread_manager, database_manager, remote_service_manager, security_manager, api_manager, cloud_manager) -> None:
```

##### `disable_plugin`
```python
def disable_plugin(self, plugin_name) -> bool:
```

##### `enable_plugin`
```python
def enable_plugin(self, plugin_name) -> bool:
```

##### `get_all_plugins`
```python
def get_all_plugins(self) -> Dict[(str, PluginInfo)]:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `install_plugin`
```python
def install_plugin(self, package_path, force, skip_verification, enable, resolve_dependencies, install_dependencies) -> bool:
```

##### `load_plugin`
```python
def load_plugin(self, plugin_name) -> bool:
```

##### `reload_plugin`
```python
def reload_plugin(self, plugin_name) -> bool:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `uninstall_plugin`
```python
def uninstall_plugin(self, plugin_name, keep_data, check_dependents) -> bool:
```

##### `unload_plugin`
```python
def unload_plugin(self, plugin_name) -> bool:
```

##### `update_plugin`
```python
def update_plugin(self, package_path, skip_verification, resolve_dependencies, install_dependencies) -> bool:
```

### Class: `PluginState`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `DISCOVERED` | `'discovered'` |
| `LOADED` | `'loaded'` |
| `ACTIVE` | `'active'` |
| `INACTIVE` | `'inactive'` |
| `FAILED` | `'failed'` |
| `DISABLED` | `'disabled'` |
