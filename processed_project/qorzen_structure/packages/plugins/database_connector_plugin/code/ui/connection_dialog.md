# Module: plugins.database_connector_plugin.code.ui.connection_dialog

**Path:** `plugins/database_connector_plugin/code/ui/connection_dialog.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from datetime import datetime
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit, QSpinBox, QComboBox, QCheckBox, QTextEdit, QPushButton, QDialogButtonBox, QTabWidget, QWidget, QLabel, QFileDialog, QMessageBox
from models import DatabaseConnection, ConnectionType
```

## Classes

| Class | Description |
| --- | --- |
| `ConnectionDialog` |  |

### Class: `ConnectionDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `accept` |  |
| `get_connection` |  |
| `set_connection` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `accept`
```python
def accept(self) -> None:
```

##### `get_connection`
```python
def get_connection(self) -> DatabaseConnection:
```

##### `set_connection`
```python
def set_connection(self, connection) -> None:
```
