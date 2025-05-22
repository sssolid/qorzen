# Module: models.audit

**Path:** `models/audit.py`

[Back to Project Index](../../index.md)

## Imports
```python
import enum
from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.sql import func
from qorzen.models.base import Base
```

## Classes

| Class | Description |
| --- | --- |
| `AuditActionType` |  |
| `AuditLog` |  |

### Class: `AuditActionType`
**Inherits from:** enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `CREATE` | `'create'` |
| `READ` | `'read'` |
| `UPDATE` | `'update'` |
| `DELETE` | `'delete'` |
| `LOGIN` | `'login'` |
| `LOGOUT` | `'logout'` |
| `EXPORT` | `'export'` |
| `IMPORT` | `'import'` |
| `CONFIG` | `'config'` |
| `SYSTEM` | `'system'` |
| `PLUGIN` | `'plugin'` |
| `CUSTOM` | `'custom'` |

### Class: `AuditLog`
**Inherits from:** Base

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'audit_logs'` |
| `id` | `    id = Column(Integer, primary_key=True)` |
| `timestamp` | `    timestamp = Column(DateTime, default=func.now(), nullable=False)` |
| `user_id` | `    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)` |
| `user_name` | `    user_name = Column(String(32), nullable=True)` |
| `action_type` | `    action_type = Column(Enum(AuditActionType), nullable=False)` |
| `resource_type` | `    resource_type = Column(String(64), nullable=False)` |
| `resource_id` | `    resource_id = Column(String(64), nullable=True)` |
| `description` | `    description = Column(String(255), nullable=True)` |
| `ip_address` | `    ip_address = Column(String(45), nullable=True)  # IPv6 compatible` |
| `user_agent` | `    user_agent = Column(String(255), nullable=True)` |
| `details` | `    details = Column(JSON, nullable=True)` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```
