# Module: models.user

**Path:** `models/user.py`

[Back to Project Index](../../index.md)

## Imports
```python
import enum
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from qorzen.models.base import Base, TimestampMixin
```

## Global Variables
```python
user_roles = user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role", Enum(UserRole), primary_key=True),
)
```

## Classes

| Class | Description |
| --- | --- |
| `User` |  |
| `UserRole` |  |

### Class: `User`
**Inherits from:** Base, TimestampMixin

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'users'` |
| `id` | `    id = Column(Integer, primary_key=True)` |
| `username` | `    username = Column(String(32), unique=True, nullable=False)` |
| `email` | `    email = Column(String(255), unique=True, nullable=False)` |
| `hashed_password` | `    hashed_password = Column(String(255), nullable=False)` |
| `active` | `    active = Column(Boolean, default=True, nullable=False)` |
| `last_login` | `    last_login = Column(DateTime, nullable=True)` |
| `roles` | `    roles = relationship("UserRole", secondary=user_roles, backref="users")` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `UserRole`
**Inherits from:** enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `ADMIN` | `'admin'` |
| `OPERATOR` | `'operator'` |
| `USER` | `'user'` |
| `VIEWER` | `'viewer'` |
