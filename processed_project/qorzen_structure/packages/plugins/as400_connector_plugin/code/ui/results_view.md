# Module: plugins.as400_connector_plugin.code.ui.results_view

**Path:** `plugins/as400_connector_plugin/code/ui/results_view.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import csv
import datetime
import io
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QAbstractTableModel, QEvent, QItemSelectionModel, QModelIndex, QObject, QPoint, QSortFilterProxyModel, Qt, Signal, Slot, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QContextMenuEvent, QFont, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QTableView, QToolBar, QVBoxLayout, QWidget
from qorzen.plugins.as400_connector_plugin.code.models import ColumnMetadata, QueryResult
from qorzen.plugins.as400_connector_plugin.code.utils import format_value_for_display
```

## Classes

| Class | Description |
| --- | --- |
| `DataPreviewDialog` |  |
| `QueryResultsTableModel` |  |
| `ResultsFilterHeader` |  |
| `ResultsFilterProxyModel` |  |
| `ResultsView` |  |

### Class: `DataPreviewDialog`
**Inherits from:** QDialog

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, record, columns, parent) -> None:
```

### Class: `QueryResultsTableModel`
**Inherits from:** QAbstractTableModel

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `columnCount` |  |
| `data` |  |
| `flags` |  |
| `getAllRecords` |  |
| `getColumnMetadata` |  |
| `getColumnType` |  |
| `getRecord` |  |
| `headerData` |  |
| `rowCount` |  |
| `setQueryResult` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `columnCount`
```python
def columnCount(self, parent) -> int:
```

##### `data`
```python
def data(self, index, role) -> Any:
```

##### `flags`
```python
def flags(self, index) -> Qt.ItemFlags:
```

##### `getAllRecords`
```python
def getAllRecords(self) -> List[Dict[(str, Any)]]:
```

##### `getColumnMetadata`
```python
def getColumnMetadata(self, column) -> Optional[ColumnMetadata]:
```

##### `getColumnType`
```python
def getColumnType(self, column) -> Optional[str]:
```

##### `getRecord`
```python
def getRecord(self, row) -> Optional[Dict[(str, Any)]]:
```

##### `headerData`
```python
def headerData(self, section, orientation, role) -> Any:
```

##### `rowCount`
```python
def rowCount(self, parent) -> int:
```

##### `setQueryResult`
```python
def setQueryResult(self, result) -> None:
```

### Class: `ResultsFilterHeader`
**Inherits from:** QHeaderView

#### Attributes

| Name | Value |
| --- | --- |
| `filterChanged` | `    filterChanged = Signal(int, str)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `adjustPositions` |  |
| `eventFilter` |  |
| `sectionMoved` |  |
| `sectionResized` |  |
| `setFilterBoxes` |  |
| `sizeHint` |  |
| `updateCursor` |  |

##### `__init__`
```python
def __init__(self, orientation, parent) -> None:
```

##### `adjustPositions`
```python
def adjustPositions(self) -> None:
```

##### `eventFilter`
```python
def eventFilter(self, obj, event) -> bool:
```

##### `sectionMoved`
```python
def sectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex) -> None:
```

##### `sectionResized`
```python
def sectionResized(self, logicalIndex, oldSize, newSize) -> None:
```

##### `setFilterBoxes`
```python
def setFilterBoxes(self, count) -> None:
```

##### `sizeHint`
```python
def sizeHint(self) -> QSize:
```

##### `updateCursor`
```python
def updateCursor(self, pos) -> None:
```

### Class: `ResultsFilterProxyModel`
**Inherits from:** QSortFilterProxyModel

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `filterAcceptsRow` |  |
| `setFilterText` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `filterAcceptsRow`
```python
def filterAcceptsRow(self, source_row, source_parent) -> bool:
```

##### `setFilterText`
```python
def setFilterText(self, column, text) -> None:
```

### Class: `ResultsView`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_filtered_data` |  |
| `get_query_result` |  |
| `set_query_result` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `get_filtered_data`
```python
def get_filtered_data(self) -> List[Dict[(str, Any)]]:
```

##### `get_query_result`
```python
def get_query_result(self) -> Optional[QueryResult]:
```

##### `set_query_result`
```python
def set_query_result(self, result) -> None:
```
