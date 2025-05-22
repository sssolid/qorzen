# Module: plugins.media_processor_plugin.code.ui.batch_dialog

**Path:** `plugins/media_processor_plugin/code/ui/batch_dialog.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from output_preview_table import OutputPreviewTable
import asyncio
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea, QWidget, QCheckBox, QGroupBox
from models.processing_config import ProcessingConfig
from processors.batch_processor import BatchProcessor
from utils.exceptions import BatchProcessingError
```

## Classes

| Class | Description |
| --- | --- |
| `BatchProcessingDialog` |  |

### Class: `BatchProcessingDialog`
**Inherits from:** QDialog

#### Attributes

| Name | Value |
| --- | --- |
| `processingComplete` | `    processingComplete = Signal(dict)  # results dictionary` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |

##### `__init__`
```python
def __init__(self, batch_processor, file_paths, config, output_dir, overwrite, logger, parent) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```
