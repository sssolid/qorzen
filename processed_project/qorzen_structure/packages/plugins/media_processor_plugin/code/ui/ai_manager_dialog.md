# Module: plugins.media_processor_plugin.code.ui.ai_manager_dialog

**Path:** `plugins/media_processor_plugin/code/ui/ai_manager_dialog.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import asyncio
from typing import Dict, List, Optional, Any, cast
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QListWidget, QListWidgetItem, QTabWidget, QWidget, QMessageBox, QGroupBox, QFormLayout, QSpacerItem, QSizePolicy, QCheckBox
from utils.ai_background_remover import AIBackgroundRemover, ModelDetails, ModelType
```

## Classes

| Class | Description |
| --- | --- |
| `AIModelManagerDialog` |  |
| `ModelDownloadWorker` |  |

### Class: `AIModelManagerDialog`
**Inherits from:** QDialog

#### Attributes

| Name | Value |
| --- | --- |
| `modelDownloaded` | `    modelDownloaded = Signal(str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |

##### `__init__`
```python
def __init__(self, ai_background_remover, config_manager, logger, parent) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

### Class: `ModelDownloadWorker`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `progressChanged` | `    progressChanged = Signal(int, str)` |
| `finished` | `    finished = Signal(bool, str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `download` `async` |  |

##### `__init__`
```python
def __init__(self, ai_background_remover, model_id) -> None:
```

##### `download`
```python
@Slot()
async def download(self) -> None:
```
