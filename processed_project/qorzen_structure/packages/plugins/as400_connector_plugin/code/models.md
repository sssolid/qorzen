# Module: plugins.as400_connector_plugin.code.models

**Path:** `plugins/as400_connector_plugin/code/models.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, cast
from pydantic import BaseModel, Field, SecretStr, validator, root_validator
```

## Classes

| Class | Description |
| --- | --- |
| `AS400ConnectionConfig` |  |
| `ColumnMetadata` |  |
| `Config` |  |
| `PluginSettings` |  |
| `QueryHistoryEntry` |  |
| `QueryResult` |  |
| `QueryResultsFormat` |  |
| `SavedQuery` |  |

### Class: `AS400ConnectionConfig`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_allowed_lists` |  |
| `validate_port` |  |

##### `validate_allowed_lists`
```python
@validator('allowed_tables', 'allowed_schemas')
def validate_allowed_lists(cls, v) -> Optional[List[str]]:
```

##### `validate_port`
```python
@validator('port')
def validate_port(cls, v) -> Optional[int]:
```

### Class: `ColumnMetadata`
**Decorators:**
- `@dataclass`

### Class: `Config`

#### Attributes

| Name | Value |
| --- | --- |
| `validate_assignment` | `True` |
| `use_enum_values` | `True` |

### Class: `PluginSettings`
**Inherits from:** BaseModel

### Class: `QueryHistoryEntry`
**Inherits from:** BaseModel

### Class: `QueryResult`
**Decorators:**
- `@dataclass`

### Class: `QueryResultsFormat`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `TABLE` | `'table'` |
| `JSON` | `'json'` |
| `CSV` | `'csv'` |
| `XML` | `'xml'` |

### Class: `SavedQuery`
**Inherits from:** BaseModel
