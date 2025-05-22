# Module: ui.settings_manager

**Path:** `ui/settings_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, TypedDict, Protocol
from PySide6.QtCore import QAbstractItemModel, QModelIndex, QPersistentModelIndex, QTimer, Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont, QIcon, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSpinBox, QSplitter, QStackedWidget, QTabWidget, QTextEdit, QTreeView, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QMessageBox, QProgressBar, QSlider, QFileDialog, QColorDialog, QFontDialog
```

## Classes

| Class | Description |
| --- | --- |
| `BooleanSettingWidget` |  |
| `ChoiceSettingWidget` |  |
| `FloatSettingWidget` |  |
| `IntegerSettingWidget` |  |
| `JsonSettingWidget` |  |
| `PathSettingWidget` |  |
| `SettingCategory` |  |
| `SettingDefinition` |  |
| `SettingType` |  |
| `SettingWidget` |  |
| `SettingsManager` |  |
| `StringSettingWidget` |  |

### Class: `BooleanSettingWidget`
**Inherits from:** SettingWidget

#### Methods

| Method | Description |
| --- | --- |
| `get_value` |  |
| `set_value` |  |
| `setup_ui` |  |

##### `get_value`
```python
def get_value(self) -> bool:
```

##### `set_value`
```python
def set_value(self, value) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```

### Class: `ChoiceSettingWidget`
**Inherits from:** SettingWidget

#### Methods

| Method | Description |
| --- | --- |
| `get_value` |  |
| `set_value` |  |
| `setup_ui` |  |

##### `get_value`
```python
def get_value(self) -> Any:
```

##### `set_value`
```python
def set_value(self, value) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```

### Class: `FloatSettingWidget`
**Inherits from:** SettingWidget

#### Methods

| Method | Description |
| --- | --- |
| `get_value` |  |
| `set_value` |  |
| `setup_ui` |  |

##### `get_value`
```python
def get_value(self) -> float:
```

##### `set_value`
```python
def set_value(self, value) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```

### Class: `IntegerSettingWidget`
**Inherits from:** SettingWidget

#### Methods

| Method | Description |
| --- | --- |
| `get_value` |  |
| `set_value` |  |
| `setup_ui` |  |

##### `get_value`
```python
def get_value(self) -> int:
```

##### `set_value`
```python
def set_value(self, value) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```

### Class: `JsonSettingWidget`
**Inherits from:** SettingWidget

#### Methods

| Method | Description |
| --- | --- |
| `get_value` |  |
| `set_value` |  |
| `setup_ui` |  |

##### `get_value`
```python
def get_value(self) -> Any:
```

##### `set_value`
```python
def set_value(self, value) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```

### Class: `PathSettingWidget`
**Inherits from:** SettingWidget

#### Methods

| Method | Description |
| --- | --- |
| `get_value` |  |
| `set_value` |  |
| `setup_ui` |  |

##### `get_value`
```python
def get_value(self) -> str:
```

##### `set_value`
```python
def set_value(self, value) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```

### Class: `SettingCategory`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `APPLICATION` | `'Application'` |
| `DATABASE` | `'Database'` |
| `LOGGING` | `'Logging'` |
| `SECURITY` | `'Security'` |
| `API` | `'API'` |
| `PLUGINS` | `'Plugins'` |
| `MONITORING` | `'Monitoring'` |
| `FILES` | `'Files'` |
| `CLOUD` | `'Cloud'` |
| `NETWORKING` | `'Networking'` |
| `PERFORMANCE` | `'Performance'` |
| `UI` | `'User Interface'` |
| `ADVANCED` | `'Advanced'` |

### Class: `SettingDefinition`
**Decorators:**
- `@dataclass`

### Class: `SettingType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `STRING` | `'string'` |
| `INTEGER` | `'integer'` |
| `FLOAT` | `'float'` |
| `BOOLEAN` | `'boolean'` |
| `LIST` | `'list'` |
| `DICT` | `'dict'` |
| `PATH` | `'path'` |
| `COLOR` | `'color'` |
| `FONT` | `'font'` |
| `PASSWORD` | `'password'` |
| `CHOICE` | `'choice'` |
| `JSON` | `'json'` |

### Class: `SettingWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `valueChanged` | `    valueChanged = Signal(object)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_value` |  |
| `set_value` |  |
| `setup_ui` |  |
| `validate` |  |

##### `__init__`
```python
def __init__(self, setting_def, parent):
```

##### `get_value`
```python
def get_value(self) -> Any:
```

##### `set_value`
```python
def set_value(self, value) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```

##### `validate`
```python
def validate(self) -> tuple[(bool, str)]:
```

### Class: `SettingsManager`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `settingChanged` | `    settingChanged = Signal(str, object)  # key, value` |
| `settingsSaved` | `    settingsSaved = Signal()` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `load_current_values` `async` |  |
| `load_setting_definitions` |  |
| `setup_ui` |  |

##### `__init__`
```python
def __init__(self, app_core, parent):
```

##### `load_current_values`
```python
async def load_current_values(self) -> None:
```

##### `load_setting_definitions`
```python
def load_setting_definitions(self) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```

### Class: `StringSettingWidget`
**Inherits from:** SettingWidget

#### Methods

| Method | Description |
| --- | --- |
| `get_value` |  |
| `set_value` |  |
| `setup_ui` |  |

##### `get_value`
```python
def get_value(self) -> str:
```

##### `set_value`
```python
def set_value(self, value) -> None:
```

##### `setup_ui`
```python
def setup_ui(self) -> None:
```
