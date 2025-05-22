# Module: plugins.database_connector_plugin.code.ui.field_mapping_tab

**Path:** `plugins/database_connector_plugin/code/ui/field_mapping_tab.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QFrame, QMenu, QInputDialog
from models import FieldMapping
```

## Classes

| Class | Description |
| --- | --- |
| `FieldMappingDialog` |  |
| `FieldMappingTab` |  |

### Class: `FieldMappingDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_mapping_data` |  |
| `set_connections` `async` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `get_mapping_data`
```python
def get_mapping_data(self) -> Tuple[(str, str, str, Dict[(str, str)])]:
```

##### `set_connections`
```python
async def set_connections(self, connections) -> None:
```

### Class: `FieldMappingTab`
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
