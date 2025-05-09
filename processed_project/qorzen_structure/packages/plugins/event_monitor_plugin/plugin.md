# Module: plugins.event_monitor_plugin.plugin

**Path:** `plugins/event_monitor_plugin/plugin.py`

[Back to Project Index](../../../index.md)

## Imports
```python
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox, QCheckBox, QTabWidget
```

## Classes

| Class | Description |
| --- | --- |
| `EventMonitorPlugin` |  |

### Class: `EventMonitorPlugin`

#### Attributes

| Name | Value |
| --- | --- |
| `name` | `'event_monitor'` |
| `version` | `'1.0.0'` |
| `description` | `'Monitors events and helps diagnose plugin integration issues'` |
| `author` | `'Support'` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `initialize` |  |
| `shutdown` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `initialize`
```python
def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```
