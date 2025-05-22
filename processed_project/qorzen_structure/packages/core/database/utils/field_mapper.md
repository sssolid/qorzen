# Module: core.database.utils.field_mapper

**Path:** `core/database/utils/field_mapper.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from sqlalchemy import text
from qorzen.utils.exceptions import DatabaseError
```

## Functions

| Function | Description |
| --- | --- |
| `standardize_field_name` |  |

### `standardize_field_name`
```python
def standardize_field_name(field_name) -> str:
```

## Classes

| Class | Description |
| --- | --- |
| `FieldMapperManager` |  |

### Class: `FieldMapperManager`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `apply_mapping_to_query` `async` |  |
| `apply_mapping_to_results` `async` |  |
| `create_mapping` `async` |  |
| `create_mapping_from_fields` `async` |  |
| `delete_mapping` `async` |  |
| `get_all_mappings` `async` |  |
| `get_mapping` `async` |  |
| `get_mapping_by_id` `async` |  |
| `initialize` `async` |  |
| `shutdown` `async` |  |
| `standardize_field_name` |  |
| `update_mapping` `async` |  |

##### `__init__`
```python
def __init__(self, database_manager, logger) -> None:
```

##### `apply_mapping_to_query`
```python
async def apply_mapping_to_query(self, query, mapping) -> str:
```

##### `apply_mapping_to_results`
```python
async def apply_mapping_to_results(self, result, mapping) -> Dict[(str, Any)]:
```

##### `create_mapping`
```python
async def create_mapping(self, connection_id, table_name, mappings, description) -> Dict[(str, Any)]:
```

##### `create_mapping_from_fields`
```python
async def create_mapping_from_fields(self, connection_id, table_name, field_names, description) -> Dict[(str, Any)]:
```

##### `delete_mapping`
```python
async def delete_mapping(self, mapping_id) -> bool:
```

##### `get_all_mappings`
```python
async def get_all_mappings(self, connection_id) -> List[Dict[(str, Any)]]:
```

##### `get_mapping`
```python
async def get_mapping(self, connection_id, table_name) -> Optional[Dict[(str, Any)]]:
```

##### `get_mapping_by_id`
```python
async def get_mapping_by_id(self, mapping_id) -> Optional[Dict[(str, Any)]]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `standardize_field_name`
```python
@staticmethod
def standardize_field_name(field_name) -> str:
```

##### `update_mapping`
```python
async def update_mapping(self, mapping_id, mappings, description) -> Dict[(str, Any)]:
```
