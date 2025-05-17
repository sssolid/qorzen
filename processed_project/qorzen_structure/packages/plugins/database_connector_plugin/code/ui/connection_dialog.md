# Module: plugins.database_connector_plugin.code.ui.connection_dialog

**Path:** `plugins/database_connector_plugin/code/ui/connection_dialog.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox, QTabWidget, QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QSizePolicy, QComboBox, QStackedWidget, QFileDialog, QFrame
from models import BaseConnectionConfig, AS400ConnectionConfig, ODBCConnectionConfig, ConnectionType
```

## Functions

| Function | Description |
| --- | --- |
| `guess_jar_locations` |  |

### `guess_jar_locations`
```python
def guess_jar_locations() -> List[str]:
```

## Classes

| Class | Description |
| --- | --- |
| `ConnectionDialog` |  |
| `ConnectionManagerDialog` |  |

### Class: `ConnectionDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_connection_config` |  |

##### `__init__`
```python
def __init__(self, parent, connection) -> None:
```

##### `get_connection_config`
```python
def get_connection_config(self) -> BaseConnectionConfig:
```

### Class: `ConnectionManagerDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_connections` |  |

##### `__init__`
```python
def __init__(self, connections, parent) -> None:
```

##### `get_connections`
```python
def get_connections(self) -> Dict[(str, BaseConnectionConfig)]:
```
