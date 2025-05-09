# Module: ui.panel_ui

**Path:** `ui/panel_ui.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import os
import sys
import time
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QStackedWidget, QVBoxLayout, QWidget
```

## Classes

| Class | Description |
| --- | --- |
| `ContentArea` |  |
| `MainWindow` |  |
| `PanelLayout` |  |
| `Sidebar` |  |
| `SidebarButton` |  |

### Class: `ContentArea`
**Inherits from:** QStackedWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_page` |  |
| `get_page_by_name` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `add_page`
```python
def add_page(self, widget, name) -> int:
```

##### `get_page_by_name`
```python
def get_page_by_name(self, name) -> Optional[QWidget]:
```

### Class: `MainWindow`
**Inherits from:** QMainWindow

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |
| `get_menu` |  |

##### `__init__`
```python
def __init__(self, app_core) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

##### `get_menu`
```python
def get_menu(self, menu_name) -> Optional[QMenu]:
```

### Class: `PanelLayout`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_page` |  |
| `add_separator` |  |
| `select_page` |  |

##### `__init__`
```python
def __init__(self, parent, app_core) -> None:
```

##### `add_page`
```python
def add_page(self, widget, name, icon, text, group) -> int:
```

##### `add_separator`
```python
def add_separator(self) -> None:
```

##### `select_page`
```python
def select_page(self, page_name) -> None:
```

### Class: `Sidebar`
**Inherits from:** QFrame

#### Attributes

| Name | Value |
| --- | --- |
| `pageChangeRequested` | `    pageChangeRequested = Signal(int)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_button` |  |
| `add_separator` |  |
| `select_page` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `add_button`
```python
def add_button(self, icon, text, page_index, group, checkable) -> SidebarButton:
```

##### `add_separator`
```python
def add_separator(self) -> None:
```

##### `select_page`
```python
def select_page(self, page_index) -> None:
```

### Class: `SidebarButton`
**Inherits from:** QPushButton

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, icon, text, parent, checkable) -> None:
```
