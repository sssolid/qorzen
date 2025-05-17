# Module: ui.dashboard

**Path:** `ui/dashboard.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QMessageBox
from qorzen.ui.ui_component import AsyncQWidget
```

## Classes

| Class | Description |
| --- | --- |
| `DashboardWidget` |  |
| `MetricsWidget` |  |
| `SystemStatusTreeWidget` |  |

### Class: `DashboardWidget`
**Inherits from:** AsyncQWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `hideEvent` |  |
| `showEvent` |  |

##### `__init__`
```python
def __init__(self, app_core, parent) -> None:
```

##### `hideEvent`
```python
def hideEvent(self, event) -> None:
```

##### `showEvent`
```python
def showEvent(self, event) -> None:
```

### Class: `MetricsWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `update_metrics` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `update_metrics`
```python
def update_metrics(self, metrics) -> None:
```

### Class: `SystemStatusTreeWidget`
**Inherits from:** QTreeWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_item_path` |  |
| `restore_expanded_state` |  |
| `save_expanded_state` |  |
| `update_system_status` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `get_item_path`
```python
def get_item_path(self, item) -> str:
```

##### `restore_expanded_state`
```python
def restore_expanded_state(self) -> None:
```

##### `save_expanded_state`
```python
def save_expanded_state(self) -> None:
```

##### `update_system_status`
```python
def update_system_status(self, status) -> None:
```
