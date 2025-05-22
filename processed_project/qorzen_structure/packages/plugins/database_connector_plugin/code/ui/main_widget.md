# Module: plugins.database_connector_plugin.code.ui.main_widget

**Path:** `plugins/database_connector_plugin/code/ui/main_widget.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QMessageBox, QProgressBar, QLabel, QHBoxLayout, QFrame
from main_tab import MainTab
from results_tab import ResultsTab
from field_mapping_tab import FieldMappingTab
from validation_tab import ValidationTab
from history_tab import HistoryTab
```

## Classes

| Class | Description |
| --- | --- |
| `DatabasePluginWidget` |  |

### Class: `DatabasePluginWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |
| `get_current_tab_index` |  |
| `get_field_mapping_tab` |  |
| `get_history_tab` |  |
| `get_main_tab` |  |
| `get_results_tab` |  |
| `get_validation_tab` |  |
| `refresh_all_tabs` `async` |  |
| `switch_to_tab` |  |

##### `__init__`
```python
def __init__(self, plugin, logger, concurrency_manager, event_bus_manager, parent) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

##### `get_current_tab_index`
```python
def get_current_tab_index(self) -> int:
```

##### `get_field_mapping_tab`
```python
def get_field_mapping_tab(self) -> Optional[FieldMappingTab]:
```

##### `get_history_tab`
```python
def get_history_tab(self) -> Optional[HistoryTab]:
```

##### `get_main_tab`
```python
def get_main_tab(self) -> Optional[MainTab]:
```

##### `get_results_tab`
```python
def get_results_tab(self) -> Optional[ResultsTab]:
```

##### `get_validation_tab`
```python
def get_validation_tab(self) -> Optional[ValidationTab]:
```

##### `refresh_all_tabs`
```python
async def refresh_all_tabs(self) -> None:
```

##### `switch_to_tab`
```python
def switch_to_tab(self, index) -> None:
```
