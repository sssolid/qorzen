# Module: plugins.sample_async_plugin.code.plugin

**Path:** `plugins/sample_async_plugin/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Awaitable, cast
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QProgressBar, QListWidget, QListWidgetItem
from qorzen.core.task_manager import TaskCategory, TaskPriority
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_component import AsyncQWidget
```

## Classes

| Class | Description |
| --- | --- |
| `CounterWidget` |  |
| `SampleAsyncPlugin` |  |

### Class: `CounterWidget`
**Inherits from:** AsyncQWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |

##### `__init__`
```python
def __init__(self, plugin, parent) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

### Class: `SampleAsyncPlugin`
**Inherits from:** BasePlugin

#### Attributes

| Name | Value |
| --- | --- |
| `name` | `'sample_async_plugin'` |
| `version` | `'1.0.0'` |
| `description` | `'Sample asynchronous plugin demonstrating the new plugin system'` |
| `author` | `'Qorzen'` |
| `dependencies` | `    dependencies = []` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `initialize` `async` |  |
| `on_ui_ready` `async` |  |
| `setup_ui` `async` |  |
| `shutdown` `async` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `initialize`
```python
async def initialize(self, application_core, **kwargs) -> None:
```

##### `on_ui_ready`
```python
async def on_ui_ready(self, ui_integration) -> None:
```

##### `setup_ui`
```python
async def setup_ui(self, ui_integration) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```
