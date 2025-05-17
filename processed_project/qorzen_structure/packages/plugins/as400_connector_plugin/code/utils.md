# Module: plugins.as400_connector_plugin.code.utils

**Path:** `plugins/as400_connector_plugin/code/utils.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import json
import re
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set, cast
from PySide6.QtCore import QSettings, QByteArray
from PySide6.QtGui import QColor
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, SavedQuery, QueryHistoryEntry, PluginSettings
```

## Functions

| Function | Description |
| --- | --- |
| `detect_query_parameters` |  |
| `format_execution_time` |  |
| `format_value_for_display` |  |
| `get_sql_keywords` |  |
| `get_syntax_highlighting_colors` |  |
| `guess_jar_locations` |  |
| `load_connections` |  |
| `load_plugin_settings` |  |
| `load_query_history` |  |
| `load_saved_queries` |  |
| `save_connections` |  |
| `save_plugin_settings` |  |
| `save_queries` |  |
| `save_query_history` |  |

### `detect_query_parameters`
```python
def detect_query_parameters(query) -> List[str]:
```

### `format_execution_time`
```python
def format_execution_time(ms) -> str:
```

### `format_value_for_display`
```python
def format_value_for_display(value) -> str:
```

### `get_sql_keywords`
```python
def get_sql_keywords() -> List[str]:
```

### `get_syntax_highlighting_colors`
```python
def get_syntax_highlighting_colors() -> Dict[(str, QColor)]:
```

### `guess_jar_locations`
```python
def guess_jar_locations() -> List[str]:
```

### `load_connections`
```python
def load_connections(file_manager) -> Dict[(str, AS400ConnectionConfig)]:
```

### `load_plugin_settings`
```python
def load_plugin_settings(config_manager) -> PluginSettings:
```

### `load_query_history`
```python
def load_query_history(file_manager, limit) -> List[QueryHistoryEntry]:
```

### `load_saved_queries`
```python
def load_saved_queries(file_manager) -> Dict[(str, SavedQuery)]:
```

### `save_connections`
```python
def save_connections(connections, file_manager) -> bool:
```

### `save_plugin_settings`
```python
def save_plugin_settings(settings, config_manager) -> bool:
```

### `save_queries`
```python
def save_queries(queries, file_manager) -> bool:
```

### `save_query_history`
```python
def save_query_history(history, file_manager, limit) -> bool:
```
