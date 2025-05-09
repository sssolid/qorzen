# Module: core.plugin_error_handler

**Path:** `core/plugin_error_handler.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import logging
import sys
import traceback
import threading
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox
from qorzen.core.event_model import Event, EventType
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState
```

## Classes

| Class | Description |
| --- | --- |
| `PluginErrorHandler` |  |
| `PluginErrorSeverity` |  |

### Class: `PluginErrorHandler`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `pluginError` | `    pluginError = Signal(str, str, object, str)  # plugin_name, error_message, severity, traceback` |
| `pluginReloadRequested` | `    pluginReloadRequested = Signal(str)  # plugin_name` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cleanup` |  |
| `clear_plugin_errors` |  |
| `get_plugin_errors` |  |

##### `__init__`
```python
def __init__(self, event_bus_manager, plugin_manager, parent) -> None:
```

##### `cleanup`
```python
def cleanup(self) -> None:
```

##### `clear_plugin_errors`
```python
def clear_plugin_errors(self, plugin_name) -> None:
```

##### `get_plugin_errors`
```python
def get_plugin_errors(self, plugin_name) -> Dict[(str, List[Dict[(str, Any)]])]:
```

### Class: `PluginErrorSeverity`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `LOW` | `    LOW = auto()` |
| `MEDIUM` | `    MEDIUM = auto()` |
| `HIGH` | `    HIGH = auto()` |
| `CRITICAL` | `    CRITICAL = auto()` |
