# Module: plugins.database_connector_plugin.code.services.export_service

**Path:** `plugins/database_connector_plugin/code/services/export_service.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import csv
import io
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional
from models import QueryResult, ExportSettings, ExportFormat
```

## Classes

| Class | Description |
| --- | --- |
| `ExportService` |  |

### Class: `ExportService`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `export_results` `async` |  |
| `get_file_extension` |  |
| `get_mime_type` |  |
| `get_supported_formats` |  |

##### `__init__`
```python
def __init__(self, file_manager, logger) -> None:
```

##### `export_results`
```python
async def export_results(self, results, format, file_path, settings) -> str:
```

##### `get_file_extension`
```python
def get_file_extension(self, format) -> str:
```

##### `get_mime_type`
```python
def get_mime_type(self, format) -> str:
```

##### `get_supported_formats`
```python
def get_supported_formats(self) -> List[ExportFormat]:
```
