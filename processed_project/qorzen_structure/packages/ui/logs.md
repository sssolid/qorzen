# Module: ui.logs

**Path:** `ui/logs.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import json
import time
from datetime import datetime
from enum import Enum, auto
from functools import partial
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableView, QTextEdit, QToolBar, QVBoxLayout, QWidget, QMessageBox
from qorzen.core.event_model import EventType
from qorzen.ui.ui_component import AsyncTaskSignals
```

## Classes

| Class | Description |
| --- | --- |
| `LogEntry` |  |
| `LogLevel` |  |
| `LogTableModel` |  |
| `LogsView` |  |

### Class: `LogEntry`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `from_event_payload` |  |

##### `__init__`
```python
def __init__(self, timestamp, level, logger, message, event, task, raw_data) -> None:
```

##### `from_event_payload`
```python
@classmethod
def from_event_payload(cls, payload) -> 'LogEntry':
```

### Class: `LogLevel`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `DEBUG` | `    DEBUG = (QColor(108, 117, 125), "DEBUG")` |
| `INFO` | `    INFO = (QColor(23, 162, 184), "INFO")` |
| `WARNING` | `    WARNING = (QColor(255, 193, 7), "WARNING")` |
| `ERROR` | `    ERROR = (QColor(220, 53, 69), "ERROR")` |
| `CRITICAL` | `    CRITICAL = (QColor(136, 14, 79), "CRITICAL")` |

#### Methods

| Method | Description |
| --- | --- |
| `from_string` |  |

##### `from_string`
```python
@classmethod
def from_string(cls, level_str) -> 'LogLevel':
```

### Class: `LogTableModel`
**Inherits from:** QAbstractTableModel

#### Attributes

| Name | Value |
| --- | --- |
| `COLUMNS` | `    COLUMNS = ["Timestamp", "Level", "Logger", "Message", "Event", "Task"]` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_log` |  |
| `clear_logs` |  |
| `columnCount` |  |
| `data` |  |
| `get_unique_loggers` |  |
| `headerData` |  |
| `rowCount` |  |
| `set_filter_level` |  |
| `set_filter_logger` |  |
| `set_filter_text` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `add_log`
```python
def add_log(self, log_entry) -> None:
```

##### `clear_logs`
```python
def clear_logs(self) -> None:
```

##### `columnCount`
```python
def columnCount(self, parent) -> int:
```

##### `data`
```python
def data(self, index, role) -> Any:
```

##### `get_unique_loggers`
```python
def get_unique_loggers(self) -> List[str]:
```

##### `headerData`
```python
def headerData(self, section, orientation, role) -> Any:
```

##### `rowCount`
```python
def rowCount(self, parent) -> int:
```

##### `set_filter_level`
```python
def set_filter_level(self, level) -> None:
```

##### `set_filter_logger`
```python
def set_filter_logger(self, logger) -> None:
```

##### `set_filter_text`
```python
def set_filter_text(self, text) -> None:
```

### Class: `LogsView`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |
| `hideEvent` |  |
| `showEvent` |  |

##### `__init__`
```python
def __init__(self, event_bus_manager, parent) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

##### `hideEvent`
```python
def hideEvent(self, event) -> None:
```

##### `showEvent`
```python
def showEvent(self, event) -> None:
```
