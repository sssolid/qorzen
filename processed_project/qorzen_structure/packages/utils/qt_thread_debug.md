# Module: utils.qt_thread_debug

**Path:** `utils/qt_thread_debug.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import logging
import sys
import threading
import traceback
from typing import Any, Callable, Optional, List, Dict, Set
from PySide6.QtCore import QObject
```

## Global Variables
```python
original_excepthook = original_excepthook = sys.excepthook
original_stderr_write = original_stderr_write = sys.stderr.write
logger = logger = logging.getLogger('thread_debug')
QT_THREADING_VIOLATIONS = QT_THREADING_VIOLATIONS = [
    'QObject::setParent: Cannot set parent, new parent is in a different thread',
    'QObject::startTimer: Timers can only be used with threads started with QThread',
    'QObject: Cannot create children for a parent that is in a different thread',
    'QSocketNotifier: Socket notifiers cannot be enabled or disabled from another thread',
    'QWidget::repaint: Recursive repaint detected',
    'QPixmap: It is not safe to use pixmaps outside the GUI thread',
    'Cannot send events to objects owned by a different thread',
    'QObject::connect: Cannot queue arguments of type',
    'QObject::installEventFilter: Cannot filter events for objects in a different thread'
]
```

## Functions

| Function | Description |
| --- | --- |
| `clear_tracked_warnings` |  |
| `enhanced_stderr_write` |  |
| `get_violation_statistics` |  |
| `install_enhanced_thread_debug` |  |
| `monkey_patch_qobject` |  |
| `uninstall_enhanced_thread_debug` |  |

### `clear_tracked_warnings`
```python
def clear_tracked_warnings() -> None:
```

### `enhanced_stderr_write`
```python
def enhanced_stderr_write(text) -> int:
```

### `get_violation_statistics`
```python
def get_violation_statistics() -> Dict[(str, Any)]:
```

### `install_enhanced_thread_debug`
```python
def install_enhanced_thread_debug(enable_logging) -> None:
```

### `monkey_patch_qobject`
```python
def monkey_patch_qobject() -> None:
```

### `uninstall_enhanced_thread_debug`
```python
def uninstall_enhanced_thread_debug() -> None:
```

## Classes

| Class | Description |
| --- | --- |
| `QtThreadMonitor` |  |

### Class: `QtThreadMonitor`

#### Methods

| Method | Description |
| --- | --- |
| `check_qobject_thread` |  |
| `register_qobject` |  |

##### `check_qobject_thread`
```python
@staticmethod
def check_qobject_thread(obj) -> bool:
```

##### `register_qobject`
```python
@staticmethod
def register_qobject(obj) -> None:
```
