# Module: core.logging_manager

**Path:** `core/logging_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import atexit
import asyncio
import logging
import logging.handlers
import os
import pathlib
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, cast, Callable, Awaitable
import structlog
from pythonjsonlogger import jsonlogger
from colorlog import ColoredFormatter
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, EventBusError
```

## Classes

| Class | Description |
| --- | --- |
| `ClickablePathFormatter` |  |
| `EventBusManagerLogHandler` |  |
| `ExcludeLoggerFilter` |  |
| `LoggingManager` |  |

### Class: `ClickablePathFormatter`
**Inherits from:** ColoredFormatter

#### Methods

| Method | Description |
| --- | --- |
| `format` |  |

##### `format`
```python
def format(self, record):
```

### Class: `EventBusManagerLogHandler`
**Inherits from:** logging.Handler

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `emit` |  |
| `start_processing` `async` |  |
| `stop_processing` `async` |  |

##### `__init__`
```python
def __init__(self, event_bus_manager) -> None:
```

##### `emit`
```python
def emit(self, record) -> None:
```

##### `start_processing`
```python
async def start_processing(self) -> None:
```

##### `stop_processing`
```python
async def stop_processing(self) -> None:
```

### Class: `ExcludeLoggerFilter`
**Inherits from:** logging.Filter

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `filter` |  |

##### `__init__`
```python
def __init__(self, excluded_logger_name) -> None:
```

##### `filter`
```python
def filter(self, record) -> bool:
```

### Class: `LoggingManager`
**Inherits from:** QorzenManager

#### Attributes

| Name | Value |
| --- | --- |
| `LOG_LEVELS` | `    LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_logger` |  |
| `initialize` `async` |  |
| `set_event_bus_manager` `async` |  |
| `shutdown` `async` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self, config_manager) -> None:
```

##### `get_logger`
```python
def get_logger(self, name) -> Union[(logging.Logger, Any)]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `set_event_bus_manager`
```python
async def set_event_bus_manager(self, event_bus_manager) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```
