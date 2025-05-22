# Module: plugin_system.plugin_state_manager

**Path:** `plugin_system/plugin_state_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import importlib
import inspect
import os
import pathlib
import sys
import time
import traceback
import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union, cast, Tuple
from qorzen.core.base import QorzenManager
from qorzen.core.error_handler import ErrorHandler, ErrorSeverity, create_error_boundary
from qorzen.utils.exceptions import PluginError, ManagerInitializationError, ManagerShutdownError
```

## Classes

| Class | Description |
| --- | --- |
| `PluginStateManager` |  |

### Class: `PluginStateManager`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_active_transition` `async` |  |
| `get_pending_operations` `async` |  |
| `is_transitioning` `async` |  |
| `transition` `async` |  |

##### `__init__`
```python
def __init__(self, plugin_manager, logger):
```

##### `get_active_transition`
```python
async def get_active_transition(self, plugin_id) -> Optional[str]:
```

##### `get_pending_operations`
```python
async def get_pending_operations(self, plugin_id) -> Set[str]:
```

##### `is_transitioning`
```python
async def is_transitioning(self, plugin_id) -> bool:
```

##### `transition`
```python
async def transition(self, plugin_id, target_state, current_state) -> bool:
```
