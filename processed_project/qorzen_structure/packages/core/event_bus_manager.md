# Module: core.event_bus_manager

**Path:** `core/event_bus_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import concurrent.futures
import queue
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
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
| `initialize` |  |
| `publish` |  |
| `shutdown` |  |
| `status` |  |
| `subscribe` |  |
| `unsubscribe` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, thread_manager) -> None:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `publish`
```python
def publish(self, event_type, source, payload, correlation_id, synchronous) -> str:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `subscribe`
```python
def subscribe(self, event_type, callback, subscriber_id, filter_criteria) -> str:
```

##### `unsubscribe`
```python
def unsubscribe(self, subscriber_id, event_type) -> bool:
```
