# Module: plugins.database_connector_plugin.code.utils.validation

**Path:** `plugins/database_connector_plugin/code/utils/validation.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, ValidationError
from models import ValidationRule, ValidationRuleType, ValidationResult, QueryResult
```

## Functions

| Function | Description |
| --- | --- |
| `create_custom_rule` |  |
| `create_enumeration_rule` |  |
| `create_length_rule` |  |
| `create_not_null_rule` |  |
| `create_pattern_rule` |  |
| `create_range_rule` |  |
| `create_unique_rule` |  |

### `create_custom_rule`
```python
def create_custom_rule(connection_id, table_name, field_name, expression, name, description, error_message) -> ValidationRule:
```

### `create_enumeration_rule`
```python
def create_enumeration_rule(connection_id, table_name, field_name, allowed_values, name, description, error_message) -> ValidationRule:
```

### `create_length_rule`
```python
def create_length_rule(connection_id, table_name, field_name, min_length, max_length, name, description, error_message) -> ValidationRule:
```

### `create_not_null_rule`
```python
def create_not_null_rule(connection_id, table_name, field_name, name, description, error_message) -> ValidationRule:
```

### `create_pattern_rule`
```python
def create_pattern_rule(connection_id, table_name, field_name, pattern, name, description, error_message) -> ValidationRule:
```

### `create_range_rule`
```python
def create_range_rule(connection_id, table_name, field_name, name, description, min_value, max_value, error_message) -> ValidationRule:
```

### `create_unique_rule`
```python
def create_unique_rule(connection_id, table_name, field_name, name, description, error_message) -> ValidationRule:
```

## Classes

| Class | Description |
| --- | --- |
| `ValidationEngine` |  |

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
| `update_rule` `async` |  |
| `validate_all_rules` `async` |  |
| `validate_data` `async` |  |

##### `__init__`
```python
def __init__(self, database_manager, logger, validation_connection_id) -> None:
```

##### `create_rule`
```python
async def create_rule(self, rule) -> ValidationRule:
```

##### `delete_rule`
```python
async def delete_rule(self, rule_id) -> bool:
```

##### `get_all_rules`
```python
async def get_all_rules(self, connection_id, table_name) -> List[ValidationRule]:
```

##### `get_rule`
```python
async def get_rule(self, rule_id) -> Optional[ValidationRule]:
```

##### `get_validation_results`
```python
async def get_validation_results(self, rule_id, limit) -> List[ValidationResult]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `update_rule`
```python
async def update_rule(self, rule) -> ValidationRule:
```

##### `validate_all_rules`
```python
async def validate_all_rules(self, connection_id, table_name, data) -> List[ValidationResult]:
```

##### `validate_data`
```python
async def validate_data(self, rule, data) -> ValidationResult:
```
