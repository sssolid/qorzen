# Module: models.plugin

**Path:** `models/plugin.py`

[Back to Project Index](../../index.md)

## Imports
```python
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from qorzen.models.base import Base, TimestampMixin
```

## Classes

| Class | Description |
| --- | --- |
| `Plugin` |  |

### Class: `Plugin`
**Inherits from:** Base, TimestampMixin

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'plugins'` |
| `id` | `    id = Column(Integer, primary_key=True)` |
| `name` | `    name = Column(String(64), unique=True, nullable=False)` |
| `version` | `    version = Column(String(32), nullable=False)` |
| `description` | `    description = Column(String(255), nullable=True)` |
| `author` | `    author = Column(String(128), nullable=True)` |
| `enabled` | `    enabled = Column(Boolean, default=True, nullable=False)` |
| `installed_path` | `    installed_path = Column(String(255), nullable=True)` |
| `configuration` | `    configuration = Column(JSON, nullable=True)` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```
