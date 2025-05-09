# Module: plugins.vcdb_explorer.code.plugin

**Path:** `plugins/vcdb_explorer/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from PySide6.QtCore import Qt, QThread, Slot, QTimer
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QMessageBox, QProgressDialog, QPushButton, QSplitter, QVBoxLayout, QWidget
from PySide6.QtGui import QAction, QIcon
from qorzen.core import RemoteServicesManager, SecurityManager, APIManager, CloudManager, LoggingManager, ConfigManager, DatabaseManager, EventBusManager, FileManager, ThreadManager
from qorzen.core.thread_manager import ThreadExecutionContext, TaskResult
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration
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
| `initialize` |  |
| `on_ui_ready` |  |
| `shutdown` |  |

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
def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, database_manager, remote_services_manager, security_manager, api_manager, cloud_manager, **kwargs) -> None:
```

##### `on_ui_ready`
```python
def on_ui_ready(self, ui_integration) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

### Class: `VCdbExplorerWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__del__` |  |
| `__init__` |  |
| `refresh_filters` |  |

##### `__del__`
```python
def __del__(self) -> None:
```

##### `__init__`
```python
def __init__(self, database_handler, event_bus, thread_manager, logger, export_settings, parent) -> None:
```

##### `refresh_filters`
```python
def refresh_filters(self) -> None:
```
