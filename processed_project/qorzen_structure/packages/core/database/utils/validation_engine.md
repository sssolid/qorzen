# Module: core.database.utils.validation_engine

**Path:** `core/database/utils/validation_engine.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import datetime
import json
import re
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Callable
from sqlalchemy import text
from qorzen.utils.exceptions import DatabaseError, ValidationError
```

## Functions

| Function | Description |
| --- | --- |
| `create_enumeration_rule` |  |
| `create_length_rule` |  |
| `create_not_null_rule` |  |
| `create_pattern_rule` |  |
| `create_range_rule` |  |

### `create_enumeration_rule`
```python
async def create_enumeration_rule(validation_engine, connection_id, table_name, field_name, allowed_values, name, description, error_message) -> Dict[(str, Any)]:
```

### `create_length_rule`
```python
async def create_length_rule(validation_engine, connection_id, table_name, field_name, min_length, max_length, name, description, error_message) -> Dict[(str, Any)]:
```

### `create_not_null_rule`
```python
async def create_not_null_rule(validation_engine, connection_id, table_name, field_name, name, description, error_message) -> Dict[(str, Any)]:
```

### `create_pattern_rule`
```python
async def create_pattern_rule(validation_engine, connection_id, table_name, field_name, pattern, name, description, error_message) -> Dict[(str, Any)]:
```

### `create_range_rule`
```python
async def create_range_rule(validation_engine, connection_id, table_name, field_name, min_value, max_value, name, description, error_message) -> Dict[(str, Any)]:
```

## Classes

| Class | Description |
| --- | --- |
| `ValidationEngine` |  |
| `ValidationRuleType` |  |

### Class: `ValidationEngine`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `create_rule` `async` |  |
| `delete_rule` `async` |  |
| `get_all_rules` `async` |  |
| `get_rule` `async` |  |
| `get_validation_results` `async` |  |
| `initialize` `async` |  |
| `shutdown` `async` |  |
| `update_rule` `async` |  |
| `validate_all_rules` `async` |  |
| `validate_data` `async` |  |

##### `__init__`
```python
def __init__(self, database_manager, logger, validation_connection_id) -> None:
```

##### `create_rule`
```python
async def create_rule(self, rule_type, connection_id, table_name, field_name, parameters, error_message, name, description) -> Dict[(str, Any)]:
```

##### `delete_rule`
```python
async def delete_rule(self, rule_id) -> bool:
```

##### `get_all_rules`
```python
async def get_all_rules(self, connection_id, table_name) -> List[Dict[(str, Any)]]:
```

##### `get_rule`
```python
async def get_rule(self, rule_id) -> Optional[Dict[(str, Any)]]:
```

##### `get_validation_results`
```python
async def get_validation_results(self, rule_id, limit) -> List[Dict[(str, Any)]]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `update_rule`
```python
async def update_rule(self, rule_id, **updates) -> Dict[(str, Any)]:
```

##### `validate_all_rules`
```python
async def validate_all_rules(self, connection_id, table_name, data) -> List[Dict[(str, Any)]]:
```

##### `validate_data`
```python
async def validate_data(self, rule, data) -> Dict[(str, Any)]:
```

### Class: `ValidationRuleType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `RANGE` | `'range'` |
| `PATTERN` | `'pattern'` |
| `NOT_NULL` | `'not_null'` |
| `UNIQUE` | `'unique'` |
| `LENGTH` | `'length'` |
| `REFERENCE` | `'reference'` |
| `ENUMERATION` | `'enumeration'` |
| `CUSTOM` | `'custom'` |
