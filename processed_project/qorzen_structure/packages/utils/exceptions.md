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
| `ApplicationError` |  |
| `AsyncOperationError` |  |
| `ConfigurationError` |  |
| `DatabaseError` |  |
| `DatabaseManagerInitializationError` |  |
| `DependencyError` |  |
| `EventBusError` |  |
| `FileError` |  |
| `ManagerError` |  |
| `ManagerInitializationError` |  |
| `ManagerShutdownError` |  |
| `PluginError` |  |
| `PluginIsolationError` |  |
| `QorzenError` |  |
| `SecurityError` |  |
| `TaskError` |  |
| `ThreadManagerError` |  |
| `ThreadingError` |  |
| `UIError` |  |
| `ValidationError` |  |
| `WrongThreadError` |  |

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

### Class: `ApplicationError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, *args, **kwargs) -> None:
```

### Class: `AsyncOperationError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, operation, operation_id, *args, **kwargs) -> None:
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

### Class: `DatabaseManagerInitializationError`
**Inherits from:** ManagerError

### Class: `DependencyError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, *args, **kwargs) -> None:
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
| `__str__` |  |

##### `__init__`
```python
def __init__(self, message, manager_name, **kwargs) -> None:
```

##### `__str__`
```python
def __str__(self) -> str:
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

### Class: `PluginIsolationError`
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
| `__str__` |  |

##### `__init__`
```python
def __init__(self, message, **kwargs) -> None:
```

##### `__str__`
```python
def __str__(self) -> str:
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

### Class: `TaskError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `__str__` |  |

##### `__init__`
```python
def __init__(self, message, task_name, **kwargs) -> None:
```

##### `__str__`
```python
def __str__(self) -> str:
```

### Class: `ThreadManagerError`
**Inherits from:** ManagerError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `__str__` |  |

##### `__init__`
```python
def __init__(self, message, thread_id, **kwargs) -> None:
```

##### `__str__`
```python
def __str__(self) -> str:
```

### Class: `ThreadingError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `__str__` |  |

##### `__init__`
```python
def __init__(self, message, thread_name, **kwargs) -> None:
```

##### `__str__`
```python
def __str__(self) -> str:
```

### Class: `UIError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, element_id, element_type, operation, *args, **kwargs) -> None:
```

### Class: `ValidationError`
**Inherits from:** QorzenError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, *args, **kwargs) -> None:
```

### Class: `WrongThreadError`
**Inherits from:** ThreadingError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, **kwargs) -> None:
```
