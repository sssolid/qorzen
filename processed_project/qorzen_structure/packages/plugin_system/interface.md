# Module: plugin_system.interface

**Path:** `plugin_system/interface.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import asyncio
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Set, Callable, Awaitable
from PySide6.QtCore import QObject
```

## Classes

| Class | Description |
| --- | --- |
| `BasePlugin` |  |
| `PluginInterface` |  |

### Class: `BasePlugin`
**Inherits from:** QObject

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `execute_task` `async` |  |
| `get_registered_tasks` |  |
| `initialize` `async` |  |
| `on_ui_ready` `async` |  |
| `register_task` `async` |  |
| `register_ui_component` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `execute_task`
```python
async def execute_task(self, task_name, *args, **kwargs) -> Optional[str]:
```

##### `get_registered_tasks`
```python
def get_registered_tasks(self) -> Set[str]:
```

##### `initialize`
```python
async def initialize(self, application_core, **kwargs) -> None:
```

##### `on_ui_ready`
```python
async def on_ui_ready(self, ui_integration) -> None:
```

##### `register_task`
```python
async def register_task(self, task_name, function, **properties) -> None:
```

##### `register_ui_component`
```python
async def register_ui_component(self, component, component_type) -> Any:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

### Class: `PluginInterface`
**Inherits from:** Protocol
**Decorators:**
- `@runtime_checkable`

#### Methods

| Method | Description |
| --- | --- |
| `initialize` `async` |  |
| `on_ui_ready` `async` |  |
| `shutdown` `async` |  |

##### `initialize`
```python
async def initialize(self, application_core) -> None:
```

##### `on_ui_ready`
```python
async def on_ui_ready(self, ui_integration) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```
