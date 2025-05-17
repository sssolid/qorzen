# Module: ui.plugins

**Path:** `ui/plugins.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot, QObject
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget, QFileDialog, QMessageBox
from qorzen.core.plugin_manager import PluginInfo, PluginState
```

## Classes

| Class | Description |
| --- | --- |
| `AsyncTaskSignals` |  |
| `PluginCard` |  |
| `PluginsView` |  |

### Class: `AsyncTaskSignals`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `started` | `    started = Signal()` |
| `result_ready` | `    result_ready = Signal(object)` |
| `error` | `    error = Signal(str, str)` |
| `finished` | `    finished = Signal()` |

### Class: `PluginCard`
**Inherits from:** QFrame

#### Attributes

| Name | Value |
| --- | --- |
| `stateChangeRequested` | `    stateChangeRequested = Signal(str, bool)` |
| `reloadRequested` | `    reloadRequested = Signal(str)` |
| `infoRequested` | `    infoRequested = Signal(str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `update_info` |  |

##### `__init__`
```python
def __init__(self, plugin_id, plugin_info, parent) -> None:
```

##### `update_info`
```python
def update_info(self, plugin_info) -> None:
```

### Class: `PluginsView`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `pluginStateChangeRequested` | `    pluginStateChangeRequested = Signal(str, bool)` |
| `pluginReloadRequested` | `    pluginReloadRequested = Signal(str)` |
| `pluginInfoRequested` | `    pluginInfoRequested = Signal(str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cleanup` |  |
| `update_plugin_state_ui` |  |

##### `__init__`
```python
def __init__(self, plugin_manager, parent) -> None:
```

##### `cleanup`
```python
def cleanup(self) -> None:
```

##### `update_plugin_state_ui`
```python
def update_plugin_state_ui(self, plugin_name, state) -> None:
```
