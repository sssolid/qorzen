# Module: plugins.media_processor_plugin.code.utils.font_manager

**Path:** `plugins/media_processor_plugin/code/utils/font_manager.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import sys
import platform
from typing import Dict, List, Optional, Set, Tuple, Any, Union, cast
from pathlib import Path
import asyncio
from PIL import ImageFont, Image, ImageDraw
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem, QFileDialog, QLineEdit, QDialog, QTabWidget, QScrollArea, QGroupBox, QFormLayout, QSpinBox
```

## Classes

| Class | Description |
| --- | --- |
| `FontManager` |  |
| `FontSelector` |  |
| `FontSelectorDialog` |  |

### Class: `FontManager`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_custom_font` |  |
| `get_custom_fonts` |  |
| `get_font` |  |
| `get_system_fonts` |  |
| `remove_custom_font` |  |
| `render_font_preview` |  |

##### `__init__`
```python
def __init__(self, logger) -> None:
```

##### `add_custom_font`
```python
def add_custom_font(self, name, path) -> bool:
```

##### `get_custom_fonts`
```python
def get_custom_fonts(self) -> Dict[(str, str)]:
```

##### `get_font`
```python
def get_font(self, font_name, size) -> ImageFont.FreeTypeFont:
```

##### `get_system_fonts`
```python
def get_system_fonts(self) -> List[str]:
```

##### `remove_custom_font`
```python
def remove_custom_font(self, name) -> bool:
```

##### `render_font_preview`
```python
def render_font_preview(self, font_name, size, text, width, height, color, background) -> Optional[bytes]:
```

### Class: `FontSelector`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `fontSelected` | `    fontSelected = Signal(str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_selected_font` |  |

##### `__init__`
```python
def __init__(self, font_manager, logger, initial_font, parent) -> None:
```

##### `get_selected_font`
```python
def get_selected_font(self) -> str:
```

### Class: `FontSelectorDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_selected_font` |  |

##### `__init__`
```python
def __init__(self, font_manager, logger, initial_font, parent) -> None:
```

##### `get_selected_font`
```python
def get_selected_font(self) -> str:
```
