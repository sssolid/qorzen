# Module: plugins.example_plugin.code.plugin

**Path:** `plugins/example_plugin/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
from PySide6.QtCore import Qt, QObject, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QTabWidget, QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QColorDialog, QFileDialog
from PySide6.QtGui import QColor, QIcon
from qorzen.plugin_system.extension import register_extension_point, call_extension_point, get_extension_point
```

## Classes

| Class | Description |
| --- | --- |
| `ExamplePlugin` |  |

### Class: `ExamplePlugin`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `name` | `'example_plugin'` |
| `version` | `'1.0.0'` |
| `description` | `'An example plugin showcasing the enhanced plugin system features'` |
| `author` | `'Qorzen Team'` |
| `ui_update_signal` | `    ui_update_signal = Signal(dict)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `example_plugin_text_transform` |  |
| `initialize` |  |
| `on_post_disable` |  |
| `on_post_enable` |  |
| `on_pre_disable` |  |
| `on_pre_enable` |  |
| `shutdown` |  |
| `text_transform` |  |
| `ui_widget` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `example_plugin_text_transform`
```python
def example_plugin_text_transform(self, text, options) -> str:
```

##### `initialize`
```python
def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs) -> None:
```

##### `on_post_disable`
```python
def on_post_disable(self, context) -> None:
```

##### `on_post_enable`
```python
def on_post_enable(self, context) -> None:
```

##### `on_pre_disable`
```python
def on_pre_disable(self, context) -> None:
```

##### `on_pre_enable`
```python
def on_pre_enable(self, context) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `text_transform`
```python
def text_transform(self, text, options) -> str:
```

##### `ui_widget`
```python
def ui_widget(self, parent) -> QWidget:
```
