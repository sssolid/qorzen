# Module: ui.thread_safe_signaler

**Path:** `ui/thread_safe_signaler.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import threading
from typing import Any, Callable, Optional, TypeVar
from PySide6.QtCore import QObject, Signal, Slot, Qt
```

## Global Variables
```python
T = T = TypeVar('T')
```

## Classes

| Class | Description |
| --- | --- |
| `ThreadSafeSignaler` |  |

### Class: `ThreadSafeSignaler`
**Inherits from:** QObject

#### Attributes

| Name | Value |
| --- | --- |
| `signal_no_args` | `    signal_no_args = Signal()` |
| `signal_int` | `    signal_int = Signal(int)` |
| `signal_str` | `    signal_str = Signal(str)` |
| `signal_int_str` | `    signal_int_str = Signal(int, str)` |
| `signal_obj` | `    signal_obj = Signal(object)` |
| `signal_multi` | `    signal_multi = Signal(object, object, object)  # For up to 3 generic objects` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `emit_safely` |  |

##### `__init__`
```python
def __init__(self, thread_manager) -> None:
```

##### `emit_safely`
```python
def emit_safely(self, signal, *args) -> None:
```
