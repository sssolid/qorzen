# Module: ui.main_window

**Path:** `ui/main_window.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, cast, Callable
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar, QPushButton, QScrollArea, QSizePolicy, QSplitter, QStackedWidget, QToolBar, QVBoxLayout, QWidget, QDockWidget
from qorzen.ui.settings_manager import SettingsManager
from qorzen.ui.ui_component import QWidget
from qorzen.utils.exceptions import UIError
```

## Classes

| Class | Description |
| --- | --- |
| `MainWindow` |  |
| `MainWindowPluginHandler` |  |

### Class: `MainWindow`
**Inherits from:** QMainWindow

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_menu_item` |  |
| `add_page` |  |
| `add_panel` |  |
| `add_toolbar_item` |  |
| `add_widget` |  |
| `closeEvent` |  |
| `get_menu` |  |
| `remove_element` |  |
| `select_page` |  |
| `show_dialog` |  |
| `show_notification` |  |
| `update_element` |  |
| `update_plugin_state_ui` |  |

##### `__init__`
```python
def __init__(self, app_core) -> None:
```

##### `add_menu_item`
```python
def add_menu_item(self, element_id, title, callback, parent_menu, icon, position, tooltip) -> None:
```

##### `add_page`
```python
def add_page(self, element_id, widget, title, icon, position) -> None:
```

##### `add_panel`
```python
def add_panel(self, element_id, panel, title, dock_area, icon, closable) -> None:
```

##### `add_toolbar_item`
```python
def add_toolbar_item(self, element_id, title, callback, icon, position, tooltip) -> None:
```

##### `add_widget`
```python
def add_widget(self, element_id, widget, parent_id, title, position) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

##### `get_menu`
```python
def get_menu(self, menu_name) -> Optional[QMenu]:
```

##### `remove_element`
```python
def remove_element(self, element_id) -> None:
```

##### `select_page`
```python
def select_page(self, page_name) -> None:
```

##### `show_dialog`
```python
def show_dialog(self, element_id, dialog, title, modal, width, height) -> None:
```

##### `show_notification`
```python
def show_notification(self, message, title, notification_type, duration) -> None:
```

##### `update_element`
```python
def update_element(self, element_id, visible, enabled, title, icon, tooltip) -> None:
```

##### `update_plugin_state_ui`
```python
def update_plugin_state_ui(self, plugin_name, state) -> None:
```

### Class: `MainWindowPluginHandler`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `handle_plugin_reload` `async` |  |
| `handle_plugin_state_change` `async` |  |

##### `__init__`
```python
def __init__(self, main_window, plugin_manager, logger):
```

##### `handle_plugin_reload`
```python
async def handle_plugin_reload(self, plugin_id) -> None:
```

##### `handle_plugin_state_change`
```python
async def handle_plugin_state_change(self, plugin_id, enable) -> None:
```
