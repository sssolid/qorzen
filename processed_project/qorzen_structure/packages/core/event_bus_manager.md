# Module: core.event_bus_manager

**Path:** `core/event_bus_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import concurrent.futures
import inspect
import queue
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import Event, EventSubscription, EventHandler, EventType
from qorzen.utils.exceptions import EventBusError, ManagerInitializationError, ManagerShutdownError
```

## Classes

| Class | Description |
| --- | --- |
| `EventBusManager` |  |

### Class: `EventBusManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `initialize` `async` |  |
| `publish` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `subscribe` `async` |  |
| `unsubscribe` `async` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, thread_manager) -> None:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `publish`
```python
async def publish(self, event_type, source, payload, correlation_id, synchronous) -> str:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `subscribe`
```python
async def subscribe(self, event_type, callback, subscriber_id, filter_criteria) -> str:
```

##### `unsubscribe`
```python
async def unsubscribe(self, subscriber_id, event_type) -> bool:
```
