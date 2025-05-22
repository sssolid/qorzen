# Module: plugins.media_processor_plugin.code.ui.output_preview_table

**Path:** `plugins/media_processor_plugin/code/ui/output_preview_table.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize, QPoint
from PySide6.QtGui import QColor, QIcon, QStandardItemModel, QStandardItem, QAction
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeView, QHeaderView, QCheckBox, QFrame, QSplitter, QWidget, QFileDialog, QMessageBox, QMenu, QProgressBar
from models.processing_config import ProcessingConfig
from utils.path_resolver import resolve_output_path
```

## Classes

| Class | Description |
| --- | --- |
| `OutputPreviewTable` |  |
| `OutputStatus` |  |

### Class: `OutputPreviewTable`
**Inherits from:** QDialog

#### Attributes

| Name | Value |
| --- | --- |
| `processingConfirmed` | `    processingConfirmed = Signal(bool)  # True if confirmed, False if cancelled` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_output_dir` |  |
| `get_overwrite` |  |
| `reject` |  |

##### `__init__`
```python
def __init__(self, file_paths, config, output_dir, overwrite, logger, parent) -> None:
```

##### `get_output_dir`
```python
def get_output_dir(self) -> str:
```

##### `get_overwrite`
```python
def get_overwrite(self) -> bool:
```

##### `reject`
```python
def reject(self) -> None:
```

### Class: `OutputStatus`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `NEW` | `'new'` |
| `OVERWRITE` | `'overwrite'` |
| `INCREMENT` | `'increment'` |
