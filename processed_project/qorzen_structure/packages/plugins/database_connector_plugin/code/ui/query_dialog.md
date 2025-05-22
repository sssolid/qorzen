# Module: plugins.database_connector_plugin.code.ui.query_dialog

**Path:** `plugins/database_connector_plugin/code/ui/query_dialog.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit, QTextEdit, QPlainTextEdit, QPushButton, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QMessageBox, QSplitter, QWidget
from models import SavedQuery
```

## Classes

| Class | Description |
| --- | --- |
| `QueryDialog` |  |

### Class: `QueryDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `accept` |  |
| `get_query` |  |
| `set_connection_id` |  |
| `set_query` |  |
| `set_query_text` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `accept`
```python
def accept(self) -> None:
```

##### `get_query`
```python
def get_query(self) -> SavedQuery:
```

##### `set_connection_id`
```python
def set_connection_id(self, connection_id) -> None:
```

##### `set_query`
```python
def set_query(self, query) -> None:
```

##### `set_query_text`
```python
def set_query_text(self, query_text) -> None:
```
