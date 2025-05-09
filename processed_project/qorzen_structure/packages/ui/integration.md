# Module: ui.integration

**Path:** `ui/integration.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import threading
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Set, TypeVar, Generic, Union, cast
from PySide6.QtWidgets import QWidget, QMenu, QToolBar, QDockWidget
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
```

## Global Variables
```python
T = T = TypeVar('T')
```

## Classes

| Class | Description |
| --- | --- |
| `ComponentTracker` |  |
| `DockComponent` |  |
| `MainWindowIntegration` |  |
| `MenuComponent` |  |
| `ToolbarComponent` |  |
| `UIComponent` |  |
| `UIIntegration` |  |

### Class: `ComponentTracker`
**Inherits from:** Generic[T]

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add` |  |
| `get_all` |  |
| `get_by_type` |  |
| `has_plugin` |  |
| `remove_all` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `add`
```python
def add(self, plugin_id, component_type, component) -> None:
```

##### `get_all`
```python
def get_all(self, plugin_id) -> Dict[(str, List[T])]:
```

##### `get_by_type`
```python
def get_by_type(self, plugin_id, component_type) -> List[T]:
```

##### `has_plugin`
```python
def has_plugin(self, plugin_id) -> bool:
```

##### `remove_all`
```python
def remove_all(self, plugin_id) -> None:
```

### Class: `DockComponent`
**Inherits from:** UIComponent

#### Methods

| Method | Description |
| --- | --- |
| `get_dock_widget` |  |

##### `get_dock_widget`
```python
def get_dock_widget(self) -> QWidget:
```

### Class: `MainWindowIntegration`
**Inherits from:** UIIntegration

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_dock_widget` |  |
| `add_menu` |  |
| `add_menu_action` |  |
| `add_page` |  |
| `add_toolbar` |  |
| `add_toolbar_action` |  |
| `cleanup_plugin` |  |
| `find_menu` |  |
| `remove_page` |  |
| `select_page` |  |

##### `__init__`
```python
def __init__(self, main_window) -> None:
```

##### `add_dock_widget`
```python
def add_dock_widget(self, plugin_id, dock, title, area) -> QDockWidget:
```

##### `add_menu`
```python
def add_menu(self, plugin_id, title, parent_menu) -> QMenu:
```

##### `add_menu_action`
```python
def add_menu_action(self, plugin_id, menu, text, callback, icon) -> QAction:
```

##### `add_page`
```python
def add_page(self, plugin_id, widget, name, icon, text, group) -> int:
```

##### `add_toolbar`
```python
def add_toolbar(self, plugin_id, title) -> QToolBar:
```

##### `add_toolbar_action`
```python
def add_toolbar_action(self, plugin_id, toolbar, text, callback, icon) -> QAction:
```

##### `cleanup_plugin`
```python
def cleanup_plugin(self, plugin_id) -> None:
```

##### `find_menu`
```python
def find_menu(self, menu_title) -> Optional[QMenu]:
```

##### `remove_page`
```python
def remove_page(self, plugin_id, name) -> None:
```

##### `select_page`
```python
def select_page(self, name) -> None:
```

### Class: `MenuComponent`
**Inherits from:** UIComponent

#### Methods

| Method | Description |
| --- | --- |
| `get_actions` |  |

##### `get_actions`
```python
def get_actions(self) -> List[QAction]:
```

### Class: `ToolbarComponent`
**Inherits from:** UIComponent

#### Methods

| Method | Description |
| --- | --- |
| `get_actions` |  |

##### `get_actions`
```python
def get_actions(self) -> List[QAction]:
```

### Class: `UIComponent`
**Inherits from:** Protocol

#### Methods

| Method | Description |
| --- | --- |
| `get_widget` |  |

##### `get_widget`
```python
def get_widget(self) -> QWidget:
```

### Class: `UIIntegration`
**Inherits from:** abc.ABC

#### Methods

| Method | Description |
| --- | --- |
| `add_dock_widget` |  |
| `add_menu` |  |
| `add_menu_action` |  |
| `add_page` |  |
| `add_toolbar` |  |
| `add_toolbar_action` |  |
| `cleanup_plugin` |  |
| `find_menu` |  |
| `remove_page` |  |
| `select_page` |  |

##### `add_dock_widget`
```python
@abc.abstractmethod
def add_dock_widget(self, plugin_id, dock, title, area) -> QDockWidget:
```

##### `add_menu`
```python
@abc.abstractmethod
def add_menu(self, plugin_id, title, parent_menu) -> QMenu:
```

##### `add_menu_action`
```python
@abc.abstractmethod
def add_menu_action(self, plugin_id, menu, text, callback, icon) -> QAction:
```

##### `add_page`
```python
@abc.abstractmethod
def add_page(self, plugin_id, widget, name, icon, text, group) -> int:
```

##### `add_toolbar`
```python
@abc.abstractmethod
def add_toolbar(self, plugin_id, title) -> QToolBar:
```

##### `add_toolbar_action`
```python
@abc.abstractmethod
def add_toolbar_action(self, plugin_id, toolbar, text, callback, icon) -> QAction:
```

##### `cleanup_plugin`
```python
@abc.abstractmethod
def cleanup_plugin(self, plugin_id) -> None:
```

##### `find_menu`
```python
@abc.abstractmethod
def find_menu(self, menu_title) -> Optional[QMenu]:
```

##### `remove_page`
```python
@abc.abstractmethod
def remove_page(self, plugin_id, name) -> None:
```

##### `select_page`
```python
@abc.abstractmethod
def select_page(self, name) -> None:
```
