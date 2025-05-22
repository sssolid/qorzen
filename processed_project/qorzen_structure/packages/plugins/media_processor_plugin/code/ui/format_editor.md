# Module: plugins.media_processor_plugin.code.ui.format_editor

**Path:** `plugins/media_processor_plugin/code/ui/format_editor.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from format_preview_widget import FormatPreviewWidget
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QColor, QIcon, QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton, QTabWidget, QWidget, QColorDialog, QFileDialog, QDialogButtonBox, QGroupBox, QRadioButton, QButtonGroup, QScrollArea, QSizePolicy, QSlider, QToolButton, QFrame, QSplitter
from models.processing_config import OutputFormat, ImageFormat, ResizeMode, WatermarkType, WatermarkPosition
```

## Classes

| Class | Description |
| --- | --- |
| `ColorButton` |  |
| `FormatEditorDialog` |  |

### Class: `ColorButton`
**Inherits from:** QPushButton

#### Attributes

| Name | Value |
| --- | --- |
| `colorChanged` | `    colorChanged = Signal(QColor)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_color` |  |
| `get_hex_color` |  |
| `set_color` |  |

##### `__init__`
```python
def __init__(self, color, parent) -> None:
```

##### `get_color`
```python
def get_color(self) -> QColor:
```

##### `get_hex_color`
```python
def get_hex_color(self) -> str:
```

##### `set_color`
```python
def set_color(self, color) -> None:
```

### Class: `FormatEditorDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `accept` |  |
| `get_format` |  |
| `showEvent` |  |

##### `__init__`
```python
def __init__(self, format_config, logger, parent) -> None:
```

##### `accept`
```python
def accept(self) -> None:
```

##### `get_format`
```python
def get_format(self) -> OutputFormat:
```

##### `showEvent`
```python
def showEvent(self, event) -> None:
```
