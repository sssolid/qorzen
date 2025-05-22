# Module: plugins.media_processor_plugin.code.plugin

**Path:** `plugins/media_processor_plugin/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
from processors.optimized_processor import OptimizedProcessor
from ui.ai_manager_dialog import AIModelManagerDialog
from utils.ai_background_remover import AIBackgroundRemover
from utils.font_manager import FontManager
import asyncio
import logging
import os
import pathlib
from typing import Any, Dict, List, Optional, Set, Union, cast
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QMessageBox, QWidget
from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.config_manager import ConfigManager
from qorzen.plugin_system.interface import BasePlugin
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from qorzen.ui.ui_integration import UIIntegration
from models.processing_config import ProcessingConfig, BackgroundRemovalConfig, OutputFormat
from ui.main_widget import MediaProcessorWidget
from ui.batch_dialog import BatchProcessingDialog
from ui.config_editor import ConfigEditorDialog
from processors.media_processor import MediaProcessor
from processors.batch_processor import BatchProcessor
from utils.exceptions import MediaProcessingError
```

## Classes

| Class | Description |
| --- | --- |
| `MediaProcessorPlugin` |  |

### Class: `MediaProcessorPlugin`
**Inherits from:** BasePlugin

#### Attributes

| Name | Value |
| --- | --- |
| `name` | `'media_processor'` |
| `version` | `'1.0.0'` |
| `description` | `'Advanced media processing with background removal, batch processing, and multiple output formats'` |
| `author` | `'Qorzen Developer'` |
| `display_name` | `'Media Processor'` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_icon` |  |
| `get_main_widget` |  |
| `initialize` `async` |  |
| `on_ui_ready` `async` |  |
| `setup_ui` `async` |  |
| `shutdown` `async` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `get_icon`
```python
def get_icon(self) -> Optional[str]:
```

##### `get_main_widget`
```python
def get_main_widget(self) -> Optional[QWidget]:
```

##### `initialize`
```python
async def initialize(self, application_core, **kwargs) -> None:
```

##### `on_ui_ready`
```python
async def on_ui_ready(self, ui_integration) -> None:
```

##### `setup_ui`
```python
async def setup_ui(self, ui_integration) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```
