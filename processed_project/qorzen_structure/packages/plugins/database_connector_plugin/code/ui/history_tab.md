# Module: plugins.database_connector_plugin.code.ui.history_tab

**Path:** `plugins/database_connector_plugin/code/ui/history_tab.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QFrame, QMenu, QSpinBox, QTabWidget, QProgressBar, QCheckBox, QCalendarWidget, QDateEdit
from models import HistorySchedule
```

## Classes

| Class | Description |
| --- | --- |
| `HistoryScheduleDialog` |  |
| `HistoryTab` |  |

### Class: `HistoryScheduleDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_schedule` |  |
| `set_connections` |  |
| `set_queries` |  |
| `set_schedule` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `get_schedule`
```python
def get_schedule(self) -> HistorySchedule:
```

##### `set_connections`
```python
def set_connections(self, connections) -> None:
```

##### `set_queries`
```python
def set_queries(self, queries) -> None:
```

##### `set_schedule`
```python
def set_schedule(self, schedule) -> None:
```

### Class: `HistoryTab`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `operation_started` | `    operation_started = Signal(str)  # message` |
| `operation_finished` | `    operation_finished = Signal()` |
| `status_changed` | `    status_changed = Signal(str)  # message` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cleanup` |  |
| `refresh` `async` |  |

##### `__init__`
```python
def __init__(self, plugin, logger, concurrency_manager, parent) -> None:
```

##### `cleanup`
```python
def cleanup(self) -> None:
```

##### `refresh`
```python
async def refresh(self) -> None:
```
