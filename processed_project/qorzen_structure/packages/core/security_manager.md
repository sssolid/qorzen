# Module: core.security_manager

**Path:** `core/security_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import datetime
import hashlib
import os
import re
import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Callable, Awaitable
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
| `authenticate_user` `async` |  |
| `create_user` `async` |  |
| `delete_user` `async` |  |
| `get_all_permissions` `async` |  |
| `get_all_users` `async` |  |
| `get_user_info` `async` |  |
| `has_permission` `async` |  |
| `has_role` `async` |  |
| `initialize` `async` |  |
| `refresh_token` `async` |  |
| `revoke_token` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `update_user` `async` |  |
| `verify_token` `async` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, event_bus_manager, db_manager) -> None:
```

##### `authenticate_user`
```python
async def authenticate_user(self, username_or_email, password) -> Optional[Dict[(str, Any)]]:
```

##### `create_user`
```python
async def create_user(self, username, email, password, roles, metadata) -> Optional[str]:
```

##### `delete_user`
```python
async def delete_user(self, user_id) -> bool:
```

##### `get_all_permissions`
```python
async def get_all_permissions(self) -> List[Dict[(str, Any)]]:
```

##### `get_all_users`
```python
async def get_all_users(self) -> List[Dict[(str, Any)]]:
```

##### `get_user_info`
```python
async def get_user_info(self, user_id) -> Optional[Dict[(str, Any)]]:
```

##### `has_permission`
```python
async def has_permission(self, user_id, resource, action) -> bool:
```

##### `has_role`
```python
async def has_role(self, user_id, role) -> bool:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `refresh_token`
```python
async def refresh_token(self, refresh_token) -> Optional[Dict[(str, Any)]]:
```

##### `revoke_token`
```python
async def revoke_token(self, token) -> bool:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `update_user`
```python
async def update_user(self, user_id, updates) -> bool:
```

##### `verify_token`
```python
async def verify_token(self, token) -> Optional[Dict[(str, Any)]]:
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
