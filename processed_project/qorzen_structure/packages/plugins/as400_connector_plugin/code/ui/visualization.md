# Module: plugins.as400_connector_plugin.code.ui.visualization

**Path:** `plugins/as400_connector_plugin/code/ui/visualization.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QAbstractTableModel, QItemSelection, QItemSelectionModel, QModelIndex, QObject, QPoint, QSize, Qt, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFrame, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSizePolicy, QSpinBox, QSplitter, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget
from qorzen.plugins.as400_connector_plugin.code.models import ColumnMetadata, QueryResult
```

## Classes

| Class | Description |
| --- | --- |
| `ChartConfigWidget` |  |
| `ChartWidget` |  |
| `VisualizationView` |  |

### Class: `ChartConfigWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `chartConfigChanged` | `    chartConfigChanged = Signal()` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_aggregation` |  |
| `get_chart_type` |  |
| `get_data_limit` |  |
| `get_x_axis` |  |
| `get_y_axis` |  |
| `set_columns` |  |
| `show_data_labels` |  |
| `show_legend` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `get_aggregation`
```python
def get_aggregation(self) -> str:
```

##### `get_chart_type`
```python
def get_chart_type(self) -> str:
```

##### `get_data_limit`
```python
def get_data_limit(self) -> int:
```

##### `get_x_axis`
```python
def get_x_axis(self) -> str:
```

##### `get_y_axis`
```python
def get_y_axis(self) -> str:
```

##### `set_columns`
```python
def set_columns(self, columns) -> None:
```

##### `show_data_labels`
```python
def show_data_labels(self) -> bool:
```

##### `show_legend`
```python
def show_legend(self) -> bool:
```

### Class: `ChartWidget`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `paintEvent` |  |
| `set_config` |  |
| `set_data` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `paintEvent`
```python
def paintEvent(self, event) -> None:
```

##### `set_config`
```python
def set_config(self, chart_type, x_axis, y_axis, aggregation, show_legend, show_data_labels, data_limit) -> None:
```

##### `set_data`
```python
def set_data(self, result) -> None:
```

### Class: `VisualizationView`
**Inherits from:** QWidget

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `set_query_result` |  |

##### `__init__`
```python
def __init__(self, parent) -> None:
```

##### `set_query_result`
```python
def set_query_result(self, result) -> None:
```
