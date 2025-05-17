# Module: plugins.database_connector_plugin.code.ui.query_editor

**Path:** `plugins/database_connector_plugin/code/ui/query_editor.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, QRegularExpression, Signal, Slot, QSize
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter, QTextCursor, QKeyEvent, QTextDocument
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTextEdit, QListWidget, QListWidgetItem, QToolBar, QSpinBox, QFormLayout, QLineEdit, QInputDialog, QMessageBox, QMenu, QSplitter, QGroupBox, QTabWidget, QScrollArea, QFileDialog
from models import SavedQuery, FieldMapping
```

## Classes

| Class | Description |
| --- | --- |
| `QueryEditorWidget` |  |
| `SQLEditor` |  |
| `SQLSyntaxHighlighter` |  |

### Class: `QueryEditorWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `executeQueryRequested` | `    executeQueryRequested = Signal()` |
| `saveQueryRequested` | `    saveQueryRequested = Signal()` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_current_query_id` |  |
| `get_current_query_name` |  |
| `get_limit` |  |
| `get_mapping_id` |  |
| `get_parameters` |  |
| `get_query_text` |  |
| `refresh` `async` |  |
| `reload_queries` `async` |  |
| `set_connection_status` |  |

##### `__init__`
```python
def __init__(self, plugin, logger, parent) -> None:
```

##### `get_current_query_id`
```python
def get_current_query_id(self) -> Optional[str]:
```

##### `get_current_query_name`
```python
def get_current_query_name(self) -> str:
```

##### `get_limit`
```python
def get_limit(self) -> Optional[int]:
```

##### `get_mapping_id`
```python
def get_mapping_id(self) -> Optional[str]:
```

##### `get_parameters`
```python
def get_parameters(self) -> Dict[(str, Any)]:
```

##### `get_query_text`
```python
def get_query_text(self) -> str:
```

##### `refresh`
```python
async def refresh(self) -> None:
```

##### `reload_queries`
```python
async def reload_queries(self) -> None:
```

##### `set_connection_status`
```python
def set_connection_status(self, connection_id, connected) -> None:
```

### Class: `SQLEditor`
**Inherits from:** QTextEdit

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `format_sql` |  |
| `keyPressEvent` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `format_sql`
```python
def format_sql(self) -> None:
```

##### `keyPressEvent`
```python
def keyPressEvent(self, event) -> None:
```

### Class: `SQLSyntaxHighlighter`
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
