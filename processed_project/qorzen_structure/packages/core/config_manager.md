# Module: core.config_manager

**Path:** `core/config_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import json
import logging
import os
import pathlib
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, Union, Awaitable, cast
import aiofiles
import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ConfigurationError, ManagerInitializationError
```

## Classes

| Class | Description |
| --- | --- |
| `ConfigManager` |  |
| `ConfigSchema` |  |

### Class: `ConfigManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get` `async` |  |
| `initialize` `async` |  |
| `register_listener` `async` |  |
| `set` `async` |  |
| `set_logger` |  |
| `shutdown` `async` |  |
| `status` |  |
| `unregister_listener` `async` |  |

##### `__init__`
```python
def __init__(self, config_path, env_prefix) -> None:
```

##### `get`
```python
async def get(self, key, default) -> Any:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `register_listener`
```python
async def register_listener(self, key, callback) -> None:
```

##### `set`
```python
async def set(self, key, value) -> None:
```

##### `set_logger`
```python
def set_logger(self, logger) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `unregister_listener`
```python
async def unregister_listener(self, key, callback) -> None:
```

### Class: `ConfigSchema`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_api_port` |  |
| `validate_jwt_secret` |  |

##### `validate_api_port`
```python
@model_validator(mode='after')
def validate_api_port(self) -> 'ConfigSchema':
```

##### `validate_jwt_secret`
```python
@model_validator(mode='after')
def validate_jwt_secret(self) -> 'ConfigSchema':
```
