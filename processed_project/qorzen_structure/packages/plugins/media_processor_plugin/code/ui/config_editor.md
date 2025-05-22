# Module: plugins.media_processor_plugin.code.ui.config_editor

**Path:** `plugins/media_processor_plugin/code/ui/config_editor.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import time
from typing import Any, Dict, List, Optional, Set, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox, QPushButton, QTabWidget, QWidget, QListView, QDialogButtonBox, QGroupBox, QFrame, QScrollArea, QSizePolicy, QSlider, QToolButton, QMessageBox, QFileDialog
from models.processing_config import ProcessingConfig, BackgroundRemovalConfig, BackgroundRemovalMethod, OutputFormat
from format_editor import FormatEditorDialog
from processors.media_processor import MediaProcessor
```

## Classes

| Class | Description |
| --- | --- |
| `ConfigEditorDialog` |  |

### Class: `ConfigEditorDialog`
**Inherits from:** QDialog

#### Attributes

| Name | Value |
| --- | --- |
| `configUpdated` | `    configUpdated = Signal(str)  # config_id` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `accept` |  |
| `get_config` |  |
| `reject` |  |

##### `__init__`
```python
def __init__(self, media_processor, file_manager, logger, plugin_config, config, parent) -> None:
```

##### `accept`
```python
def accept(self) -> None:
```

##### `get_config`
```python
def get_config(self) -> ProcessingConfig:
```

##### `reject`
```python
def reject(self) -> None:
```
