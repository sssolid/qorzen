# Module: models.base

**Path:** `models/base.py`

[Back to Project Index](../../index.md)

## Imports
```python
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
```

## Global Variables
```python
Base = Base = declarative_base()
```

## Classes

| Class | Description |
| --- | --- |
| `TimestampMixin` |  |

### Class: `TimestampMixin`

#### Attributes

| Name | Value |
| --- | --- |
| `created_at` | `    created_at = Column(DateTime, default=func.now(), nullable=False)` |
| `updated_at` | `    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )` |
