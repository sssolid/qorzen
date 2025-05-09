# Module: core.logging_manager

**Path:** `core/logging_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import atexit
import logging
import logging.handlers
import os
import pathlib
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, cast
import structlog
from pythonjsonlogger import jsonlogger
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, EventBusError
```

## Classes

| Class | Description |
| --- | --- |
| `EventBusLogHandler` |  |
| `ExcludeLoggerFilter` |  |
| `LoggingManager` |  |

### Class: `EventBusLogHandler`
**Inherits from:** logging.Handler

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `emit` |  |

##### `__init__`
```python
def __init__(self, event_bus_manager):
```

##### `emit`
```python
def emit(self, record):
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
def __init__(self, excluded_logger_name):
```

##### `filter`
```python
def filter(self, record):
```

### Class: `LoggingManager`
**Inherits from:** QorzenManager

#### Attributes

| Name | Value |
| --- | --- |
| `LOG_LEVELS` | `    LOG_LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_logger` |  |
| `initialize` |  |
| `set_event_bus_manager` |  |
| `shutdown` |  |
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
def initialize(self) -> None:
```

##### `set_event_bus_manager`
```python
def set_event_bus_manager(self, event_bus_manager):
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```
