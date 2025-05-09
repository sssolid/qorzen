# Module: ui.plugins

**Path:** `ui/plugins.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget
from qorzen.core.plugin_manager import PluginInfo
```

## Classes

| Class | Description |
| --- | --- |
| `PluginCard` |  |
| `PluginState` |  |
| `PluginsView` |  |

### Class: `PluginCard`
**Inherits from:** QFrame

#### Attributes

| Name | Value |
| --- | --- |
| `stateChangeRequested` | `    stateChangeRequested = Signal(str, bool)  # plugin_name, enable` |
| `reloadRequested` | `    reloadRequested = Signal(str)  # plugin_name` |
| `infoRequested` | `    infoRequested = Signal(str)  # plugin_name` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `update_info` |  |

##### `__init__`
```python
def __init__(self, plugin_name, plugin_info, parent) -> None:
```

##### `update_info`
```python
def update_info(self, plugin_info) -> None:
```

### Class: `PluginState`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `DISCOVERED` | `    DISCOVERED = auto()  # Plugin is discovered but not loaded` |
| `LOADED` | `    LOADED = auto()  # Plugin is loaded and ready` |
| `ACTIVE` | `    ACTIVE = auto()  # Plugin is active and running` |
| `INACTIVE` | `    INACTIVE = auto()  # Plugin is loaded but not active` |
| `FAILED` | `    FAILED = auto()  # Plugin failed to load or crashed` |
| `DISABLED` | `    DISABLED = auto()  # Plugin is explicitly disabled` |

### Class: `PluginsView`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `pluginStateChangeRequested` | `    pluginStateChangeRequested = Signal(str, bool)  # plugin_name, enable` |
| `pluginReloadRequested` | `    pluginReloadRequested = Signal(str)  # plugin_name` |
| `pluginInfoRequested` | `    pluginInfoRequested = Signal(str)  # plugin_name` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cleanup` |  |
| `update_plugin_state` |  |

##### `__init__`
```python
def __init__(self, plugin_manager, parent) -> None:
```

##### `cleanup`
```python
def cleanup(self) -> None:
```

##### `update_plugin_state`
```python
def update_plugin_state(self, plugin_name, state) -> None:
```
