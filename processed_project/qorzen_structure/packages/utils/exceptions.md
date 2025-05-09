# Module: utils.exceptions

**Path:** `utils/exceptions.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
from typing import Any, Dict, Optional
```

## Classes

| Class | Description |
| --- | --- |
| `APIError` |  |
| `ConfigurationError` |  |
| `DatabaseError` |  |
| `EventBusError` |  |
| `FileError` |  |
| `ManagerError` |  |
| `ManagerInitializationError` |  |
| `ManagerShutdownError` |  |
| `PluginError` |  |
| `QorzenError` |  |
| `SecurityError` |  |
| `ThreadManagerError` |  |

### Class: `APIError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, status_code, endpoint, *args, **kwargs) -> None:
```

### Class: `ConfigurationError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, config_key, *args, **kwargs) -> None:
```

### Class: `DatabaseError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, query, *args, **kwargs) -> None:
```

### Class: `EventBusError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, event_type, *args, **kwargs) -> None:
```

### Class: `FileError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, file_path, *args, **kwargs) -> None:
```

### Class: `ManagerError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, manager_name, *args, **kwargs) -> None:
```

### Class: `ManagerInitializationError`
**Inherits from:** ManagerError

### Class: `ManagerShutdownError`
**Inherits from:** ManagerError

### Class: `PluginError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, plugin_name, *args, **kwargs) -> None:
```

### Class: `QorzenError`
**Inherits from:** Exception

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, code, details, *args, **kwargs) -> None:
```

### Class: `SecurityError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, user_id, permission, *args, **kwargs) -> None:
```

### Class: `ThreadManagerError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, thread_id, *args, **kwargs) -> None:
```
