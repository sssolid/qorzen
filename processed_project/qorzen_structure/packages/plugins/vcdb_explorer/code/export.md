# Module: plugins.vcdb_explorer.code.export

**Path:** `plugins/vcdb_explorer/code/export.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import csv
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
```

## Global Variables
```python
EXCEL_AVAILABLE = False
```

## Classes

| Class | Description |
| --- | --- |
| `DataExporter` |  |
| `ExportError` |  |

### Class: `DataExporter`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `export_all_data` |  |
| `export_csv` |  |
| `export_excel` |  |

##### `__init__`
```python
def __init__(self, logger) -> None:
```

##### `export_all_data`
```python
def export_all_data(self, database_callback, filter_panels, columns, column_map, file_path, format_type, max_rows, table_filters, sort_by, sort_desc, progress_callback) -> int:
```

##### `export_csv`
```python
def export_csv(self, data, columns, column_map, file_path) -> None:
```

##### `export_excel`
```python
def export_excel(self, data, columns, column_map, file_path, sheet_name) -> None:
```

### Class: `ExportError`
**Inherits from:** Exception

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, details) -> None:
```
