# Module: plugin_debug

**Path:** `plugin_debug.py`

[Back to Project Index](../index.md)

## Imports
```python
import sys
import inspect
import logging
import traceback
from pathlib import Path
```

## Global Variables
```python
logger = logger = logging.getLogger("plugin_debugger")
operations = operations = []
```

## Functions

| Function | Description |
| --- | --- |
| `hook_lifecycle` |  |
| `hook_plugin_manager` |  |
| `hook_state_manager` |  |
| `log_operation` |  |

### `hook_lifecycle`
```python
def hook_lifecycle():
```

### `hook_plugin_manager`
```python
def hook_plugin_manager():
```

### `hook_state_manager`
```python
def hook_state_manager():
```

### `log_operation`
```python
def log_operation(op_type, **kwargs):
```
