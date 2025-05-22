# Module: plugins.media_processor_plugin.code.ui.format_preview_widget

**Path:** `plugins/media_processor_plugin/code/ui/format_preview_widget.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import time
from typing import Optional, Dict, Any, Callable, Union
from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox, QPushButton, QProgressBar, QFrame, QSizePolicy
from models.processing_config import OutputFormat, BackgroundRemovalConfig
from utils.exceptions import MediaProcessingError
from ui.preview_widget import ImagePreviewWidget
```

## Classes

| Class | Description |
| --- | --- |
| `FormatPreviewWidget` |  |

### Class: `FormatPreviewWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `previewRequested` | `    previewRequested = Signal()` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `set_background_removal` |  |
| `set_format` |  |
| `set_preview_image` |  |
| `sizeHint` |  |

##### `__init__`
```python
def __init__(self, media_processor, logger, preview_file_path, parent) -> None:
```

##### `set_background_removal`
```python
def set_background_removal(self, bg_removal_config) -> None:
```

##### `set_format`
```python
def set_format(self, format_config) -> None:
```

##### `set_preview_image`
```python
def set_preview_image(self, file_path) -> None:
```

##### `sizeHint`
```python
def sizeHint(self) -> QSize:
```
