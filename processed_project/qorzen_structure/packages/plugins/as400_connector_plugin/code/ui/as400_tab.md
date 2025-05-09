# Module: plugins.as400_connector_plugin.code.ui.as400_tab

**Path:** `plugins/as400_connector_plugin/code/ui/as400_tab.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import uuid
import os
import datetime
import json
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, QSize, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont, QTextCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit, QTextEdit, QToolBar, QStatusBar, QFileDialog, QMessageBox, QDialog, QGroupBox, QFormLayout, QCheckBox, QSpinBox, QDialogButtonBox, QMenu, QToolButton, QProgressBar, QListWidget, QListWidgetItem, QInputDialog, QRadioButton, QButtonGroup, QScrollArea
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, SavedQuery, QueryHistoryEntry, PluginSettings, QueryResult
from qorzen.plugins.as400_connector_plugin.code.connector import AS400Connector
from qorzen.plugins.as400_connector_plugin.code.utils import load_connections, save_connections, load_saved_queries, save_queries, load_query_history, save_query_history, load_plugin_settings, save_plugin_settings, format_value_for_display, detect_query_parameters
from qorzen.plugins.as400_connector_plugin.code.ui.results_view import ResultsView
from qorzen.plugins.as400_connector_plugin.code.ui.visualization import VisualizationView
```

## Classes

| Class | Description |
| --- | --- |
| `AS400Tab` |  |

### Class: `AS400Tab`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `queryStarted` | `    queryStarted = Signal(str)` |
| `queryFinished` | `    queryFinished = Signal(str, bool)` |
| `connectionChanged` | `    connectionChanged = Signal(str, bool)` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `export_queries` |  |
| `handle_config_change` |  |
| `import_queries` |  |
| `open_connection_dialog` |  |
| `open_connection_manager` |  |

##### `__init__`
```python
def __init__(self, event_bus, logger, config, file_manager, thread_manager, security_manager, parent) -> None:
```

##### `export_queries`
```python
def export_queries(self) -> None:
```

##### `handle_config_change`
```python
def handle_config_change(self, key, value) -> None:
```

##### `import_queries`
```python
def import_queries(self) -> None:
```

##### `open_connection_dialog`
```python
def open_connection_dialog(self) -> None:
```

##### `open_connection_manager`
```python
def open_connection_manager(self) -> None:
```
