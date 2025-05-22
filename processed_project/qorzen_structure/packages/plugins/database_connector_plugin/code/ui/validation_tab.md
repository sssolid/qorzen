# Module: plugins.database_connector_plugin.code.ui.validation_tab

**Path:** `plugins/database_connector_plugin/code/ui/validation_tab.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QFrame, QMenu, QSpinBox, QDoubleSpinBox, QCheckBox, QTabWidget, QProgressBar, QScrollArea
from models import ValidationRule, ValidationRuleType
```

## Classes

| Class | Description |
| --- | --- |
| `ValidationRuleDialog` |  |
| `ValidationTab` |  |

### Class: `ValidationRuleDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_rule` |  |
| `set_connections` |  |
| `set_rule` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `get_rule`
```python
def get_rule(self) -> ValidationRule:
```

##### `set_connections`
```python
def set_connections(self, connections) -> None:
```

##### `set_rule`
```python
def set_rule(self, rule) -> None:
```

### Class: `ValidationTab`
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
