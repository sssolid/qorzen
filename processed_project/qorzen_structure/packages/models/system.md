# Module: models.system

**Path:** `models/system.py`

[Back to Project Index](../../index.md)

## Imports
```python
from sqlalchemy import JSON, Boolean, Column, Integer, String
from sqlalchemy.orm import validates
from qorzen.models.base import Base, TimestampMixin
```

## Classes

| Class | Description |
| --- | --- |
| `SystemSetting` |  |

### Class: `SystemSetting`
**Inherits from:** Base, TimestampMixin

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'system_settings'` |
| `id` | `    id = Column(Integer, primary_key=True)` |
| `key` | `    key = Column(String(128), unique=True, nullable=False, index=True)` |
| `value` | `    value = Column(JSON, nullable=True)` |
| `description` | `    description = Column(String(255), nullable=True)` |
| `is_secret` | `    is_secret = Column(Boolean, default=False, nullable=False)` |
| `is_editable` | `    is_editable = Column(Boolean, default=True, nullable=False)` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |
| `validate_key` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

##### `validate_key`
```python
@validates('key')
def validate_key(self, key, value):
```
