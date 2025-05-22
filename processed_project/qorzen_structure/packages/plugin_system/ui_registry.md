# Module: plugin_system.ui_registry

**Path:** `plugin_system/ui_registry.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
```

## Classes

| Class | Description |
| --- | --- |
| `UIComponentRegistry` |  |

### Class: `UIComponentRegistry`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cleanup` `async` |  |
| `register` |  |
| `shutdown` `async` |  |

##### `__init__`
```python
def __init__(self, plugin_name, thread_manager) -> None:
```

##### `cleanup`
```python
async def cleanup(self) -> None:
```

##### `register`
```python
def register(self, component, component_type) -> Any:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```
