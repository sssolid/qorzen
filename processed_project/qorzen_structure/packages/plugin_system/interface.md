# Module: plugin_system.interface

**Path:** `plugin_system/interface.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import threading
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Generic, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from qorzen.ui.integration import UIIntegration
from qorzen.core import RemoteServicesManager, SecurityManager, APIManager, CloudManager, LoggingManager, ConfigManager, DatabaseManager, EventBusManager, FileManager, ThreadManager
```

## Classes

| Class | Description |
| --- | --- |
| `BasePlugin` |  |
| `PluginInterface` |  |

### Class: `BasePlugin`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `initialized` | `    initialized = Signal()` |
| `ui_ready` | `    ui_ready = Signal()` |
| `shutdown_started` | `    shutdown_started = Signal()` |
| `shutdown_completed` | `    shutdown_completed = Signal()` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `initialize` |  |
| `on_ui_ready` |  |
| `shutdown` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `initialize`
```python
def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, database_manager, remote_services_manager, security_manager, api_manager, cloud_manager, **kwargs) -> None:
```

##### `on_ui_ready`
```python
def on_ui_ready(self, ui_integration) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

### Class: `PluginInterface`
**Inherits from:** Protocol
**Decorators:**
- `@runtime_checkable`

#### Methods

| Method | Description |
| --- | --- |
| `initialize` |  |
| `on_ui_ready` |  |
| `shutdown` |  |

##### `initialize`
```python
def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, database_manager, remote_services_manager, security_manager, api_manager, cloud_manager, **kwargs) -> None:
```

##### `on_ui_ready`
```python
def on_ui_ready(self, ui_integration) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```
