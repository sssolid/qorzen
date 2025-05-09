# Module: core.config_manager

**Path:** `core/config_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import json
import os
import pathlib
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, Union
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
| `get` |  |
| `initialize` |  |
| `register_listener` |  |
| `set` |  |
| `shutdown` |  |
| `status` |  |
| `unregister_listener` |  |

##### `__init__`
```python
def __init__(self, config_path, env_prefix) -> None:
```

##### `get`
```python
def get(self, key, default) -> Any:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `register_listener`
```python
def register_listener(self, key, callback) -> None:
```

##### `set`
```python
def set(self, key, value) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `unregister_listener`
```python
def unregister_listener(self, key, callback) -> None:
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
