# Module: plugins.application_launcher.code.plugin

**Path:** `plugins/application_launcher/code/plugin.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from pydantic import BaseModel, Field, validator
from PySide6.QtCore import QDir, QProcess, QProcessEnvironment, Qt, Signal, Slot, QTimer, QUrl, QObject, QFileInfo
from PySide6.QtGui import QAction, QDesktopServices, QFont, QIcon, QColor
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QPushButton, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QToolButton, QVBoxLayout, QWidget, QScrollArea
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.file_manager import FileManager
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_integration import UIIntegration
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from qorzen.utils.exceptions import PluginError
```

## Classes

| Class | Description |
| --- | --- |
| `ApplicationCard` |  |
| `ApplicationConfig` |  |
| `ApplicationConfigDialog` |  |
| `ApplicationLauncherPlugin` |  |
| `ApplicationLauncherWidget` |  |
| `ApplicationRunDialog` |  |
| `ApplicationRunner` |  |
| `ArgumentConfig` |  |
| `ArgumentInputWidget` |  |
| `ArgumentType` |  |
| `ConsoleOutputWidget` |  |
| `OutputFilesWidget` |  |
| `ProcessOutput` |  |
| `ProcessStatus` |  |

### Class: `ApplicationCard`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `launchClicked` | `    launchClicked = Signal(ApplicationConfig)` |
| `editClicked` | `    editClicked = Signal(ApplicationConfig)` |
| `deleteClicked` | `    deleteClicked = Signal(ApplicationConfig)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, app_config, parent) -> None:
```

### Class: `ApplicationConfig`
**Decorators:**
- `@dataclass`

### Class: `ApplicationConfigDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_config` |  |

##### `__init__`
```python
def __init__(self, app_config, parent) -> None:
```

##### `get_config`
```python
def get_config(self) -> ApplicationConfig:
```

### Class: `ApplicationLauncherPlugin`
**Inherits from:** BasePlugin

#### Attributes

| Name | Value |
| --- | --- |
| `name` | `'application_launcher'` |
| `version` | `'1.0.0'` |
| `description` | `'Launch external applications with configurable arguments'` |
| `author` | `'Qorzen Developer'` |
| `display_name` | `'Application Launcher'` |

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

### Class: `ApplicationLauncherWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `shutdown` `async` |  |

##### `__init__`
```python
def __init__(self, event_bus_manager, concurrency_manager, task_manager, file_manager, logger, parent) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

### Class: `ApplicationRunDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |

##### `__init__`
```python
def __init__(self, app_config, app_runner, parent) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

### Class: `ApplicationRunner`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `processStarted` | `    processStarted = Signal()` |
| `processFinished` | `    processFinished = Signal(ProcessOutput)` |
| `processError` | `    processError = Signal(str)` |
| `stdoutReceived` | `    stdoutReceived = Signal(str)` |
| `stderrReceived` | `    stderrReceived = Signal(str)` |
| `outputFilesDetected` | `    outputFilesDetected = Signal(list)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `run_application` |  |
| `terminate_process` |  |

##### `__init__`
```python
def __init__(self, concurrency_manager, file_manager, parent) -> None:
```

##### `run_application`
```python
def run_application(self, app_config, arg_values) -> None:
```

##### `terminate_process`
```python
def terminate_process(self) -> None:
```

### Class: `ArgumentConfig`
**Decorators:**
- `@dataclass`

### Class: `ArgumentInputWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `valueChanged` | `    valueChanged = Signal(str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_value` |  |

##### `__init__`
```python
def __init__(self, arg_config, parent) -> None:
```

##### `get_value`
```python
def get_value(self) -> str:
```

### Class: `ArgumentType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `STATIC` | `'static'` |
| `FILE_INPUT` | `'file_input'` |
| `FILE_OUTPUT` | `'file_output'` |
| `DIRECTORY` | `'directory'` |
| `TEXT_INPUT` | `'text_input'` |
| `ENV_VAR` | `'environment_variable'` |

### Class: `ConsoleOutputWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `append_stderr` |  |
| `append_stdout` |  |
| `clear` |  |
| `process_finished` |  |
| `process_terminated` |  |
| `start_process` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `append_stderr`
```python
def append_stderr(self, text) -> None:
```

##### `append_stdout`
```python
def append_stdout(self, text) -> None:
```

##### `clear`
```python
def clear(self) -> None:
```

##### `process_finished`
```python
def process_finished(self, exit_code) -> None:
```

##### `process_terminated`
```python
def process_terminated(self) -> None:
```

##### `start_process`
```python
def start_process(self, command_line) -> None:
```

### Class: `OutputFilesWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `fileOpened` | `    fileOpened = Signal(str)` |

#### Methods

| Method | Description |
| --- | --- |
| `set_files` |  |

##### `set_files`
```python
def set_files(self, file_paths) -> None:
```

### Class: `ProcessOutput`
**Inherits from:** BaseModel

### Class: `ProcessStatus`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `NOT_STARTED` | `'not_started'` |
| `RUNNING` | `'running'` |
| `FINISHED` | `'finished'` |
| `FAILED` | `'failed'` |
| `TERMINATED` | `'terminated'` |
