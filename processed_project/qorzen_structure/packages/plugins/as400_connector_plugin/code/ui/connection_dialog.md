# Module: plugins.as400_connector_plugin.code.ui.connection_dialog

**Path:** `plugins/as400_connector_plugin/code/ui/connection_dialog.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import uuid
from typing import Any, Dict, List, Optional, Set, cast
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox, QTabWidget, QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QSizePolicy, QComboBox
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig
from qorzen.plugins.as400_connector_plugin.code.utils import guess_jar_locations
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
def __init__(self, parent, file_manager, connection) -> None:
```

##### `get_connection_config`
```python
def get_connection_config(self) -> AS400ConnectionConfig:
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
def __init__(self, connections, parent, file_manager) -> None:
```

##### `get_connections`
```python
def get_connections(self) -> Dict[(str, AS400ConnectionConfig)]:
```
