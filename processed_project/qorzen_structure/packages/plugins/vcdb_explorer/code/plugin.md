# Module: plugins.vcdb_explorer.code.plugin

**Path:** `plugins/vcdb_explorer/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QMessageBox, QProgressDialog, QPushButton, QSplitter, QVBoxLayout, QWidget, QFrame, QProgressBar
from PySide6.QtGui import QAction, QIcon
from qorzen.core.remote_manager import RemoteServicesManager
from qorzen.core.security_manager import SecurityManager
from qorzen.core.api_manager import APIManager
from qorzen.core.cloud_manager import CloudManager
from qorzen.core.logging_manager import LoggingManager
from qorzen.core.config_manager import ConfigManager
from qorzen.core.database_manager import DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.file_manager import FileManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_integration import UIIntegration
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from database_handler import DatabaseHandler
from data_table import DataTableWidget
from events import VCdbEventType
from export import DataExporter
from filter_panel import FilterPanelManager
```

## Classes

| Class | Description |
| --- | --- |
| `VCdbExplorerPlugin` |  |
| `VCdbExplorerWidget` |  |

### Class: `VCdbExplorerPlugin`
**Inherits from:** BasePlugin

#### Attributes

| Name | Value |
| --- | --- |
| `name` | `'vcdb_explorer'` |
| `version` | `'1.0.0'` |
| `description` | `'Advanced query tool for exploring Vehicle Component Database'` |
| `author` | `'Qorzen Developer'` |
| `display_name` | `'VCdb Explorer'` |

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

### Class: `VCdbExplorerWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |
| `refresh_filters` |  |

##### `__init__`
```python
def __init__(self, database_handler, event_bus_manager, concurrency_manager, task_manager, logger, export_settings, parent) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

##### `refresh_filters`
```python
@Slot()
def refresh_filters(self) -> None:
```
