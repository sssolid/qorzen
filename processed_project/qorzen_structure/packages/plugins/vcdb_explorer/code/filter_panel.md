# Module: plugins.vcdb_explorer.code.filter_panel

**Path:** `plugins/vcdb_explorer/code/filter_panel.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel, QMenu, QPushButton, QSizePolicy, QSpinBox, QTabWidget, QToolButton, QVBoxLayout, QWidget
from qorzen.core.event_bus_manager import EventBusManager
from database_handler import DatabaseHandler
from events import VCdbEventType
```

## Classes

| Class | Description |
| --- | --- |
| `ComboBoxFilter` |  |
| `FilterPanel` |  |
| `FilterPanelManager` |  |
| `FilterWidget` |  |
| `YearRangeFilter` |  |

### Class: `ComboBoxFilter`
**Inherits from:** FilterWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `clear` |  |
| `get_selected_values` |  |
| `set_available_values` |  |

##### `__init__`
```python
def __init__(self, filter_type, filter_name, parent) -> None:
```

##### `clear`
```python
@Slot()
def clear(self) -> None:
```

##### `get_selected_values`
```python
def get_selected_values(self) -> List[int]:
```

##### `set_available_values`
```python
def set_available_values(self, values) -> None:
```

### Class: `FilterPanel`
**Inherits from:** QGroupBox

#### Attributes

| Name | Value |
| --- | --- |
| `filterChanged` | `    filterChanged = Signal(str, str, list)` |
| `removeRequested` | `    removeRequested = Signal(str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__del__` |  |
| `__init__` |  |
| `get_current_values` |  |
| `get_panel_id` |  |
| `refresh_all_filters` |  |
| `set_filter_values` |  |
| `update_filter_values` |  |

##### `__del__`
```python
def __del__(self) -> None:
```

##### `__init__`
```python
def __init__(self, panel_id, database_handler, event_bus, logger, parent) -> None:
```

##### `get_current_values`
```python
def get_current_values(self) -> Dict[(str, List[int])]:
```

##### `get_panel_id`
```python
def get_panel_id(self) -> str:
```

##### `refresh_all_filters`
```python
def refresh_all_filters(self) -> None:
```

##### `set_filter_values`
```python
def set_filter_values(self, filter_type, values) -> None:
```

##### `update_filter_values`
```python
def update_filter_values(self, filter_values) -> None:
```

### Class: `FilterPanelManager`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `filtersChanged` | `    filtersChanged = Signal()` |

#### Methods

| Method | Description |
| --- | --- |
| `__del__` |  |
| `__init__` |  |
| `get_all_filters` |  |
| `refresh_all_panels` |  |
| `update_filter_values` |  |

##### `__del__`
```python
def __del__(self) -> None:
```

##### `__init__`
```python
def __init__(self, database_handler, event_bus, logger, max_panels, parent) -> None:
```

##### `get_all_filters`
```python
def get_all_filters(self) -> List[Dict[(str, List[int])]]:
```

##### `refresh_all_panels`
```python
def refresh_all_panels(self) -> None:
```

##### `update_filter_values`
```python
def update_filter_values(self, panel_id, filter_values) -> None:
```

### Class: `FilterWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `valueChanged` | `    valueChanged = Signal(str, list)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `clear` |  |
| `get_filter_name` |  |
| `get_filter_type` |  |
| `get_selected_values` |  |
| `set_available_values` |  |

##### `__init__`
```python
def __init__(self, filter_type, filter_name, parent) -> None:
```

##### `clear`
```python
@Slot()
def clear(self) -> None:
```

##### `get_filter_name`
```python
def get_filter_name(self) -> str:
```

##### `get_filter_type`
```python
def get_filter_type(self) -> str:
```

##### `get_selected_values`
```python
def get_selected_values(self) -> List[int]:
```

##### `set_available_values`
```python
def set_available_values(self, values) -> None:
```

### Class: `YearRangeFilter`
**Inherits from:** FilterWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `clear` |  |
| `get_selected_values` |  |
| `set_available_values` |  |

##### `__init__`
```python
def __init__(self, filter_type, filter_name, parent) -> None:
```

##### `clear`
```python
@Slot()
def clear(self) -> None:
```

##### `get_selected_values`
```python
def get_selected_values(self) -> List[int]:
```

##### `set_available_values`
```python
def set_available_values(self, values) -> None:
```
