# Module: plugins.media_processor_plugin.code.ui.main_widget

**Path:** `plugins/media_processor_plugin/code/ui/main_widget.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QSplitter, QListWidget, QListWidgetItem, QFileDialog, QComboBox, QGroupBox, QCheckBox, QMessageBox, QScrollArea, QToolButton, QMenu, QApplication, QFrame, QDialog
from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from models.processing_config import ProcessingConfig, OutputFormat, BackgroundRemovalConfig
from processors.media_processor import MediaProcessor
from processors.batch_processor import BatchProcessor
from utils.exceptions import MediaProcessingError
from batch_dialog import BatchProcessingDialog
from config_editor import ConfigEditorDialog
from format_editor import FormatEditorDialog
from preview_widget import ImagePreviewWidget
```

## Classes

| Class | Description |
| --- | --- |
| `MediaProcessorWidget` |  |

### Class: `MediaProcessorWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `processingStarted` | `    processingStarted = Signal()` |
| `processingFinished` | `    processingFinished = Signal(bool, str)  # success, message` |
| `configChanged` | `    configChanged = Signal(str)  # config_id` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `dragEnterEvent` |  |
| `dropEvent` |  |

##### `__init__`
```python
def __init__(self, media_processor, batch_processor, file_manager, event_bus_manager, concurrency_manager, task_manager, logger, plugin_config, parent) -> None:
```

##### `dragEnterEvent`
```python
def dragEnterEvent(self, event) -> None:
```

##### `dropEvent`
```python
def dropEvent(self, event) -> None:
```
