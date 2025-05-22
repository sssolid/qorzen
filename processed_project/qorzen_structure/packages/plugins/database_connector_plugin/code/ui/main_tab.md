# Module: plugins.database_connector_plugin.code.ui.main_tab

**Path:** `plugins/database_connector_plugin/code/ui/main_tab.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QPushButton, QComboBox, QLabel, QTextEdit, QPlainTextEdit, QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QMessageBox, QDialog, QFormLayout, QLineEdit, QSpinBox, QCheckBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QFrame, QScrollArea, QGridLayout
from models import DatabaseConnection, SavedQuery, ConnectionType, QueryResult
from connection_dialog import ConnectionDialog
from query_dialog import QueryDialog
```

## Classes

| Class | Description |
| --- | --- |
| `MainTab` |  |
| `SQLHighlighter` |  |

### Class: `MainTab`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `query_executed` | `    query_executed = Signal(object)  # QueryResult` |
| `operation_started` | `    operation_started = Signal(str)  # message` |
| `operation_finished` | `    operation_finished = Signal()` |
| `status_changed` | `    status_changed = Signal(str)  # message` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cleanup` |  |
| `get_current_connection_id` |  |
| `get_query_text` |  |
| `refresh` `async` |  |
| `set_query_text` |  |

##### `__init__`
```python
def __init__(self, plugin, logger, concurrency_manager, event_bus_manager, parent) -> None:
```

##### `cleanup`
```python
def cleanup(self) -> None:
```

##### `get_current_connection_id`
```python
def get_current_connection_id(self) -> Optional[str]:
```

##### `get_query_text`
```python
def get_query_text(self) -> str:
```

##### `refresh`
```python
async def refresh(self) -> None:
```

##### `set_query_text`
```python
def set_query_text(self, text) -> None:
```

### Class: `SQLHighlighter`
**Inherits from:** QSyntaxHighlighter

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `highlightBlock` |  |

##### `__init__`
```python
def __init__(self, document) -> None:
```

##### `highlightBlock`
```python
def highlightBlock(self, text) -> None:
```
