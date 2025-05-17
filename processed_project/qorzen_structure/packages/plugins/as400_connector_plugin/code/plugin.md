# Module: plugins.as400_connector_plugin.code.plugin

**Path:** `plugins/as400_connector_plugin/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Set, cast
from pathlib import Path
from PySide6.QtWidgets import QMenu, QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import QMetaObject, Qt, Slot, QObject, Signal
from qorzen.core.event_model import EventType
from qorzen.plugins.as400_connector_plugin.code.ui.as400_tab import AS400Tab
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration
```

## Classes

| Class | Description |
| --- | --- |
| `AS400ConnectorPlugin` |  |

### Class: `AS400ConnectorPlugin`
**Inherits from:** BasePlugin

#### Attributes

| Name | Value |
| --- | --- |
| `ui_ready_signal` | `    ui_ready_signal = Signal(object)  # Signal to pass main window from event to main thread` |
| `name` | `'as400_connector_plugin'` |
| `version` | `'0.1.0'` |
| `description` | `'Connect and query AS400/iSeries databases'` |
| `author` | `'Qorzen Team'` |
| `dependencies` | `    dependencies = []` |

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
def initialize(self, event_bus_manager, logger_provider, config_provider, file_manager, thread_manager, database_manager, security_manager, **kwargs) -> None:
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
