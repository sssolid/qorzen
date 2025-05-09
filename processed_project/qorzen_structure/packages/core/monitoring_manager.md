# Module: core.monitoring_manager

**Path:** `core/monitoring_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import datetime
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
import psutil
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
from qorzen.core.base import QorzenManager
from qorzen.core.thread_manager import TaskProgressReporter, ThreadExecutionContext
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError
```

## Classes

| Class | Description |
| --- | --- |
| `Alert` |  |
| `AlertLevel` |  |
| `ResourceMonitoringManager` |  |

### Class: `Alert`
**Decorators:**
- `@dataclass`

### Class: `AlertLevel`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `INFO` | `'info'` |
| `WARNING` | `'warning'` |
| `ERROR` | `'error'` |
| `CRITICAL` | `'critical'` |

### Class: `ResourceMonitoringManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `generate_diagnostic_report` |  |
| `get_alerts` |  |
| `initialize` |  |
| `register_counter` |  |
| `register_gauge` |  |
| `register_histogram` |  |
| `register_summary` |  |
| `shutdown` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, event_bus_manager, thread_manager) -> None:
```

##### `generate_diagnostic_report`
```python
def generate_diagnostic_report(self) -> Dict[(str, Any)]:
```

##### `get_alerts`
```python
def get_alerts(self, include_resolved, level, metric_name) -> List[Dict[(str, Any)]]:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `register_counter`
```python
def register_counter(self, name, description, labels) -> Any:
```

##### `register_gauge`
```python
def register_gauge(self, name, description, labels) -> Any:
```

##### `register_histogram`
```python
def register_histogram(self, name, description, labels, buckets) -> Any:
```

##### `register_summary`
```python
def register_summary(self, name, description, labels) -> Any:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```
