# Module: ui.task_monitor

**Path:** `ui/task_monitor.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
from typing import Dict, Optional, Any, List
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QScrollArea, QVBoxLayout, QWidget, QMessageBox
from qorzen.ui.ui_component import AsyncTaskSignals
```

## Classes

| Class | Description |
| --- | --- |
| `TaskMonitorWidget` |  |
| `TaskProgressWidget` |  |

### Class: `TaskMonitorWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cleanup` |  |

##### `__init__`
```python
def __init__(self, event_bus_manager, parent) -> None:
```

##### `cleanup`
```python
def cleanup(self) -> None:
```

### Class: `TaskProgressWidget`
**Inherits from:** QFrame

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `mark_cancelled` |  |
| `mark_completed` |  |
| `mark_failed` |  |
| `update_progress` |  |

##### `__init__`
```python
def __init__(self, task_id, plugin_name, task_name, parent) -> None:
```

##### `mark_cancelled`
```python
def mark_cancelled(self) -> None:
```

##### `mark_completed`
```python
def mark_completed(self) -> None:
```

##### `mark_failed`
```python
def mark_failed(self, error) -> None:
```

##### `update_progress`
```python
def update_progress(self, progress, message) -> None:
```
