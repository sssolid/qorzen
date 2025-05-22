# Module: ui.ui_integration

**Path:** `ui/ui_integration.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable, Protocol, TypeVar
from pydantic import BaseModel, Field, validator
from PySide6.QtCore import QObject, Signal, Slot, Qt
from qorzen.utils.exceptions import UIError
```

## Global Variables
```python
T = T = TypeVar('T')
```

## Classes

| Class | Description |
| --- | --- |
| `UICallbackProtocol` |  |
| `UIElementInfo` |  |
| `UIElementType` |  |
| `UIIntegration` |  |
| `UIOperation` |  |
| `UIOperationModel` |  |
| `UISignals` |  |

### Class: `UICallbackProtocol`
**Inherits from:** Protocol

#### Methods

| Method | Description |
| --- | --- |
| `__call__` |  |

##### `__call__`
```python
def __call__(self, *args, **kwargs) -> Any:
```

### Class: `UIElementInfo`
**Decorators:**
- `@dataclass`

### Class: `UIElementType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `PAGE` | `'page'` |
| `WIDGET` | `'widget'` |
| `MENU_ITEM` | `'menu_item'` |
| `TOOLBAR_ITEM` | `'toolbar_item'` |
| `DIALOG` | `'dialog'` |
| `PANEL` | `'panel'` |
| `NOTIFICATION` | `'notification'` |
| `STATUS_BAR` | `'status_bar'` |
| `DOCK` | `'dock'` |

### Class: `UIIntegration`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_menu_item` `async` |  |
| `add_page` `async` |  |
| `add_panel` `async` |  |
| `add_toolbar_item` `async` |  |
| `add_widget` `async` |  |
| `clear_plugin_elements` `async` |  |
| `get_all_elements` |  |
| `get_element_info` |  |
| `get_plugin_elements` |  |
| `remove_element` `async` |  |
| `show_dialog` `async` |  |
| `show_notification` `async` |  |
| `shutdown` `async` |  |
| `update_element` `async` |  |

##### `__init__`
```python
def __init__(self, main_window, concurrency_manager, logger_manager) -> None:
```

##### `add_menu_item`
```python
async def add_menu_item(self, plugin_id, title, callback, parent_menu, icon, position, tooltip, metadata) -> str:
```

##### `add_page`
```python
async def add_page(self, plugin_id, page_component, title, icon, position, metadata) -> str:
```

##### `add_panel`
```python
async def add_panel(self, plugin_id, panel_component, title, dock_area, icon, closable, metadata) -> str:
```

##### `add_toolbar_item`
```python
async def add_toolbar_item(self, plugin_id, title, callback, icon, position, tooltip, metadata) -> str:
```

##### `add_widget`
```python
async def add_widget(self, plugin_id, widget_component, parent_id, title, position, metadata) -> str:
```

##### `clear_plugin_elements`
```python
async def clear_plugin_elements(self, plugin_id) -> int:
```

##### `get_all_elements`
```python
def get_all_elements(self) -> List[UIElementInfo]:
```

##### `get_element_info`
```python
def get_element_info(self, element_id) -> Optional[UIElementInfo]:
```

##### `get_plugin_elements`
```python
def get_plugin_elements(self, plugin_id) -> List[UIElementInfo]:
```

##### `remove_element`
```python
async def remove_element(self, element_id) -> bool:
```

##### `show_dialog`
```python
async def show_dialog(self, plugin_id, dialog_component, title, modal, width, height, metadata) -> str:
```

##### `show_notification`
```python
async def show_notification(self, plugin_id, message, title, notification_type, duration, metadata) -> str:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `update_element`
```python
async def update_element(self, element_id, visible, enabled, title, icon, tooltip, metadata) -> bool:
```

### Class: `UIOperation`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `ADD` | `'add'` |
| `REMOVE` | `'remove'` |
| `UPDATE` | `'update'` |
| `SHOW` | `'show'` |
| `HIDE` | `'hide'` |

### Class: `UIOperationModel`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_element_info` |  |

##### `validate_element_info`
```python
@validator('element_info')
def validate_element_info(cls, v) -> Dict[(str, Any)]:
```

### Class: `UISignals`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `operation_ready` | `    operation_ready = Signal(object)  # Signal emitted when an operation is ready to be executed` |
