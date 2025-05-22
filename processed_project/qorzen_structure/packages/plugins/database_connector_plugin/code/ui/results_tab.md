# Module: plugins.database_connector_plugin.code.ui.results_tab

**Path:** `plugins/database_connector_plugin/code/ui/results_tab.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QSpinBox, QCheckBox, QTextEdit, QSplitter, QFrame, QMessageBox, QFileDialog, QProgressBar, QMenu
from models import QueryResult, ExportFormat, ExportSettings
```

## Classes

| Class | Description |
| --- | --- |
| `ResultsTab` |  |

### Class: `ResultsTab`
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
| `clear_results` |  |
| `get_current_result` |  |
| `refresh` `async` |  |
| `show_results` |  |

##### `__init__`
```python
def __init__(self, plugin, logger, concurrency_manager, parent) -> None:
```

##### `cleanup`
```python
def cleanup(self) -> None:
```

##### `clear_results`
```python
def clear_results(self) -> None:
```

##### `get_current_result`
```python
def get_current_result(self) -> Optional[QueryResult]:
```

##### `refresh`
```python
async def refresh(self) -> None:
```

##### `show_results`
```python
def show_results(self, result) -> None:
```
