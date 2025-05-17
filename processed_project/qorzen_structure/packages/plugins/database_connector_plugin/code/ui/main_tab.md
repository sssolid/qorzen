# Module: plugins.database_connector_plugin.code.ui.main_tab

**Path:** `plugins/database_connector_plugin/code/ui/main_tab.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import datetime
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTabWidget, QSplitter, QToolBar, QStatusBar, QMessageBox, QProgressBar, QMenu, QToolButton, QInputDialog, QFileDialog
from qorzen.utils.exceptions import DatabaseError, PluginError
from models import BaseConnectionConfig, AS400ConnectionConfig, ODBCConnectionConfig, ConnectionType, SavedQuery, FieldMapping, ValidationRule, QueryResult
from connection_dialog import ConnectionDialog, ConnectionManagerDialog
from query_editor import QueryEditorWidget
from field_mapping import FieldMappingWidget
from validation import ValidationWidget
from history import HistoryWidget
from results_view import ResultsView
```

## Classes

| Class | Description |
| --- | --- |
| `DatabaseConnectorTab` |  |

### Class: `DatabaseConnectorTab`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `connectionChanged` | `    connectionChanged = Signal(str, bool)  # connection_id, connected` |
| `queryStarted` | `    queryStarted = Signal(str)  # connection_id` |
| `queryFinished` | `    queryFinished = Signal(str, bool)  # connection_id, success` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `handle_config_change` |  |
| `open_connection_manager` |  |
| `switch_to_history` |  |
| `switch_to_mapping_editor` |  |
| `switch_to_query_editor` |  |
| `switch_to_results` |  |
| `switch_to_validation` |  |

##### `__init__`
```python
def __init__(self, plugin, logger, concurrency_manager, event_bus_manager, parent) -> None:
```

##### `handle_config_change`
```python
def handle_config_change(self, key, value) -> None:
```

##### `open_connection_manager`
```python
def open_connection_manager(self) -> None:
```

##### `switch_to_history`
```python
def switch_to_history(self) -> None:
```

##### `switch_to_mapping_editor`
```python
def switch_to_mapping_editor(self) -> None:
```

##### `switch_to_query_editor`
```python
def switch_to_query_editor(self) -> None:
```

##### `switch_to_results`
```python
def switch_to_results(self) -> None:
```

##### `switch_to_validation`
```python
def switch_to_validation(self) -> None:
```
