# Module: plugins.system_monitor.code.plugin

**Path:** `plugins/system_monitor/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import logging
import time
import threading
from typing import Any, Dict, List, Optional, cast
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QMenu, QToolBar
from PySide6.QtCore import QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QColor, QPalette
from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, TabComponent
from qorzen.plugin_system.interface import BasePlugin
```

## Classes

| Class | Description |
| --- | --- |
| `ResourceWidget` |  |
| `SystemMonitorPlugin` |  |
| `SystemMonitorTab` |  |

### Class: `ResourceWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `update_value` |  |

##### `__init__`
```python
def __init__(self, title, parent) -> None:
```

##### `update_value`
```python
def update_value(self, value) -> None:
```

### Class: `SystemMonitorPlugin`
**Inherits from:** BasePlugin

#### Attributes

| Name | Value |
| --- | --- |
| `name` | `'system_monitor'` |
| `version` | `'1.0.0'` |
| `description` | `'Real-time system resource monitoring'` |
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
def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs) -> None:
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

### Class: `SystemMonitorTab`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `update_signal` | `    update_signal = Signal(dict)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_widget` |  |
| `on_tab_deselected` |  |
| `on_tab_selected` |  |
| `update_metrics` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `get_widget`
```python
def get_widget(self) -> QWidget:
```

##### `on_tab_deselected`
```python
def on_tab_deselected(self) -> None:
```

##### `on_tab_selected`
```python
def on_tab_selected(self) -> None:
```

##### `update_metrics`
```python
def update_metrics(self, metrics) -> None:
```
