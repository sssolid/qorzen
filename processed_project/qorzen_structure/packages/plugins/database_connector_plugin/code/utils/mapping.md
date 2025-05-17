# Module: plugins.database_connector_plugin.code.utils.mapping

**Path:** `plugins/database_connector_plugin/code/utils/mapping.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple, Set, Union, cast
from models import FieldMapping, QueryResult
```

## Functions

| Function | Description |
| --- | --- |
| `apply_mapping_to_query` |  |
| `apply_mapping_to_results` |  |
| `create_mapping_from_fields` |  |
| `standardize_field_name` |  |

### `apply_mapping_to_query`
```python
def apply_mapping_to_query(query, mapping) -> str:
```

### `apply_mapping_to_results`
```python
def apply_mapping_to_results(result, mapping) -> QueryResult:
```

### `create_mapping_from_fields`
```python
def create_mapping_from_fields(connection_id, table_name, field_names, description) -> FieldMapping:
```

### `standardize_field_name`
```python
def standardize_field_name(field_name) -> str:
```
