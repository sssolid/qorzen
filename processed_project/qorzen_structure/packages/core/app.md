# Module: core.app

**Path:** `core/app.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import atexit
import importlib
import signal
import sys
import traceback
from pathlib import Path
import logging
from typing import Any, Dict, List, Optional, Type, cast, Callable
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.ui.integration import MainWindowIntegration
from qorzen.core import ResourceMonitoringManager
from qorzen.core import APIManager
from qorzen.core import ConfigManager
from qorzen.core import EventBusManager
from qorzen.core import LoggingManager
from qorzen.core import ThreadManager
from qorzen.core import FileManager
from qorzen.core import DatabaseManager
from qorzen.core import PluginManager
from qorzen.core import RemoteServicesManager
from qorzen.core import SecurityManager
from qorzen.core import CloudManager
from qorzen.plugin_system.integration import IntegratedPluginInstaller
from qorzen.plugin_system.repository import PluginRepositoryManager
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.extension import extension_registry
from qorzen.plugin_system.lifecycle import set_logger as set_lifecycle_logger
from qorzen.utils.exceptions import ManagerInitializationError, QorzenError
```

## Global Variables
```python
logger = logger = logging.getLogger(__name__)
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
| `finalize_initialization` |  |
| `get_initialization_steps` |  |
| `get_manager` |  |
| `set_main_window` |  |
| `shutdown` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self, config_path) -> None:
```

##### `finalize_initialization`
```python
def finalize_initialization(self):
```

##### `get_initialization_steps`
```python
def get_initialization_steps(self, progress_callback):
```

##### `get_manager`
```python
def get_manager(self, name) -> Optional[QorzenManager]:
```

##### `set_main_window`
```python
def set_main_window(self, main_window) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```
