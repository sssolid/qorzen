# Module: core.security_manager

**Path:** `core/security_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import datetime
import hashlib
import os
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
import jwt
from passlib.context import CryptContext
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, SecurityError
```

## Classes

| Class | Description |
| --- | --- |
| `AuthToken` |  |
| `Permission` |  |
| `SecurityManager` |  |
| `User` |  |
| `UserRole` |  |

### Class: `AuthToken`
**Decorators:**
- `@dataclass`

### Class: `Permission`
**Decorators:**
- `@dataclass`

### Class: `SecurityManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `authenticate_user` |  |
| `create_user` |  |
| `delete_user` |  |
| `get_all_permissions` |  |
| `get_all_users` |  |
| `get_user_info` |  |
| `has_permission` |  |
| `has_role` |  |
| `initialize` |  |
| `refresh_token` |  |
| `revoke_token` |  |
| `shutdown` |  |
| `status` |  |
| `update_user` |  |
| `verify_token` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, event_bus_manager, db_manager) -> None:
```

##### `authenticate_user`
```python
def authenticate_user(self, username_or_email, password) -> Optional[Dict[(str, Any)]]:
```

##### `create_user`
```python
def create_user(self, username, email, password, roles, metadata) -> Optional[str]:
```

##### `delete_user`
```python
def delete_user(self, user_id) -> bool:
```

##### `get_all_permissions`
```python
def get_all_permissions(self) -> List[Dict[(str, Any)]]:
```

##### `get_all_users`
```python
def get_all_users(self) -> List[Dict[(str, Any)]]:
```

##### `get_user_info`
```python
def get_user_info(self, user_id) -> Optional[Dict[(str, Any)]]:
```

##### `has_permission`
```python
def has_permission(self, user_id, resource, action) -> bool:
```

##### `has_role`
```python
def has_role(self, user_id, role) -> bool:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `refresh_token`
```python
def refresh_token(self, refresh_token) -> Optional[Dict[(str, Any)]]:
```

##### `revoke_token`
```python
def revoke_token(self, token) -> bool:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `update_user`
```python
def update_user(self, user_id, updates) -> bool:
```

##### `verify_token`
```python
def verify_token(self, token) -> Optional[Dict[(str, Any)]]:
```

### Class: `User`
**Decorators:**
- `@dataclass`

### Class: `UserRole`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `ADMIN` | `'admin'` |
| `OPERATOR` | `'operator'` |
| `USER` | `'user'` |
| `VIEWER` | `'viewer'` |
