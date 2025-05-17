# Module: plugins.as400_connector_plugin.code.ui.query_editor

**Path:** `plugins/as400_connector_plugin/code/ui/query_editor.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import Qt, QRegularExpression, QSize
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter, QTextCursor, QKeyEvent, QTextDocument
from PySide6.QtWidgets import QTextEdit, QWidget, QCompleter, QAbstractItemView
from qorzen.plugins.as400_connector_plugin.code.utils import get_sql_keywords, get_syntax_highlighting_colors, detect_query_parameters
```

## Classes

| Class | Description |
| --- | --- |
| `SQLQueryEditor` |  |
| `SQLSyntaxHighlighter` |  |

### Class: `SQLQueryEditor`
**Inherits from:** QTextEdit

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `format_sql` |  |
| `get_detected_parameters` |  |
| `keyPressEvent` |  |
| `set_dark_mode` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `format_sql`
```python
def format_sql(self) -> None:
```

##### `get_detected_parameters`
```python
def get_detected_parameters(self) -> List[str]:
```

##### `keyPressEvent`
```python
def keyPressEvent(self, event) -> None:
```

##### `set_dark_mode`
```python
def set_dark_mode(self, enabled) -> None:
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
