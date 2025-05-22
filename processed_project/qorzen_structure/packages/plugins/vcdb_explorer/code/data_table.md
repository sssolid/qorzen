# Module: plugins.vcdb_explorer.code.data_table

**Path:** `plugins/vcdb_explorer/code/data_table.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import csv
import logging
import os
import tempfile
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QRegularExpression, QSize, QSortFilterProxyModel, Qt, Signal, Slot, QTimer, QPoint
from PySide6.QtGui import QAction, QClipboard, QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QProgressBar, QProgressDialog, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QTableView, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget, QGridLayout, QApplication, QRadioButton
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event
from database_handler import DatabaseHandler
from events import VCdbEventType
from export import DataExporter, ExportError
```

## Global Variables
```python
EXCEL_AVAILABLE = False
```

## Classes

| Class | Description |
| --- | --- |
| `ColumnSelectionDialog` |  |
| `DataTableWidget` |  |
| `ExportOptionsDialog` |  |
| `FilterProxyModel` |  |
| `OverlayProgressDialog` |  |
| `QueryResultModel` |  |
| `QuerySignals` |  |
| `TableFilterWidget` |  |
| `YearRangeTableFilter` |  |

### Class: `ColumnSelectionDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_selected_columns` |  |

##### `__init__`
```python
def __init__(self, available_columns, selected_columns, parent) -> None:
```

##### `get_selected_columns`
```python
def get_selected_columns(self) -> List[str]:
```

### Class: `DataTableWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `queryStarted` | `    queryStarted = Signal()` |
| `queryFinished` | `    queryFinished = Signal()` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `closeEvent` |  |
| `execute_query` |  |
| `get_callback_id` |  |
| `get_page_size` |  |
| `get_selected_columns` |  |

##### `__init__`
```python
def __init__(self, database_handler, event_bus_manager, logger, parent) -> None:
```

##### `closeEvent`
```python
def closeEvent(self, event) -> None:
```

##### `execute_query`
```python
def execute_query(self, filter_panels) -> None:
```

##### `get_callback_id`
```python
def get_callback_id(self) -> str:
```

##### `get_page_size`
```python
def get_page_size(self) -> int:
```

##### `get_selected_columns`
```python
def get_selected_columns(self) -> List[str]:
```

### Class: `ExportOptionsDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `export_all` |  |

##### `__init__`
```python
def __init__(self, format_type, current_count, total_count, parent) -> None:
```

##### `export_all`
```python
def export_all(self) -> bool:
```

### Class: `FilterProxyModel`
**Inherits from:** QSortFilterProxyModel

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `filterAcceptsRow` |  |
| `set_column_map` |  |
| `set_filters` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `filterAcceptsRow`
```python
def filterAcceptsRow(self, source_row, source_parent) -> bool:
```

##### `set_column_map`
```python
def set_column_map(self, columns) -> None:
```

##### `set_filters`
```python
def set_filters(self, filters) -> None:
```

### Class: `OverlayProgressDialog`
**Inherits from:** QDialog

#### Attributes

| Name | Value |
| --- | --- |
| `cancelled` | `    cancelled = Signal()` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `set_progress` |  |

##### `__init__`
```python
def __init__(self, title, parent) -> None:
```

##### `set_progress`
```python
def set_progress(self, value, maximum, status) -> None:
```

### Class: `QueryResultModel`
**Inherits from:** QAbstractTableModel

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `columnCount` |  |
| `data` |  |
| `get_all_data` |  |
| `get_row_data` |  |
| `get_total_count` |  |
| `headerData` |  |
| `rowCount` |  |
| `set_columns` |  |
| `set_data` |  |

##### `__init__`
```python
def __init__(self, columns, column_map, parent) -> None:
```

##### `columnCount`
```python
def columnCount(self, parent) -> int:
```

##### `data`
```python
def data(self, index, role) -> Any:
```

##### `get_all_data`
```python
def get_all_data(self) -> List[Dict[(str, Any)]]:
```

##### `get_row_data`
```python
def get_row_data(self, row) -> Dict[(str, Any)]:
```

##### `get_total_count`
```python
def get_total_count(self) -> int:
```

##### `headerData`
```python
def headerData(self, section, orientation, role) -> Any:
```

##### `rowCount`
```python
def rowCount(self, parent) -> int:
```

##### `set_columns`
```python
def set_columns(self, columns) -> None:
```

##### `set_data`
```python
def set_data(self, data, total_count) -> None:
```

### Class: `QuerySignals`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `started` | `    started = Signal()` |
| `completed` | `    completed = Signal(object)` |
| `failed` | `    failed = Signal(str)` |
| `progress` | `    progress = Signal(int, int)` |
| `cancelled` | `    cancelled = Signal()` |

### Class: `TableFilterWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `filterChanged` | `    filterChanged = Signal(dict)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_filters` |  |
| `set_columns` |  |

##### `__init__`
```python
def __init__(self, columns, column_map, parent) -> None:
```

##### `get_filters`
```python
def get_filters(self) -> Dict[(str, Any)]:
```

##### `set_columns`
```python
def set_columns(self, columns) -> None:
```

### Class: `YearRangeTableFilter`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `filterChanged` | `    filterChanged = Signal(dict)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_filter` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `get_filter`
```python
def get_filter(self) -> Dict[(str, Any)]:
```
