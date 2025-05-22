# Module: core.database.utils.history_manager

**Path:** `core/database/utils/history_manager.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from sqlalchemy import text
from qorzen.utils.exceptions import DatabaseError
```

## Classes

| Class | Description |
| --- | --- |
| `HistoryManager` |  |

### Class: `HistoryManager`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `create_schedule` `async` |  |
| `delete_history_data` `async` |  |
| `delete_schedule` `async` |  |
| `execute_schedule_now` `async` |  |
| `get_all_schedules` `async` |  |
| `get_history_data` `async` |  |
| `get_history_entries` `async` |  |
| `get_schedule` `async` |  |
| `initialize` `async` |  |
| `shutdown` `async` |  |
| `start_schedule` `async` |  |
| `stop_schedule` `async` |  |
| `update_schedule` `async` |  |

##### `__init__`
```python
def __init__(self, database_manager, logger, history_connection_id) -> None:
```

##### `create_schedule`
```python
async def create_schedule(self, connection_id, query_id, frequency, name, description, retention_days) -> Dict[(str, Any)]:
```

##### `delete_history_data`
```python
async def delete_history_data(self, snapshot_id) -> bool:
```

##### `delete_schedule`
```python
async def delete_schedule(self, schedule_id) -> bool:
```

##### `execute_schedule_now`
```python
async def execute_schedule_now(self, schedule_id) -> Dict[(str, Any)]:
```

##### `get_all_schedules`
```python
async def get_all_schedules(self) -> List[Dict[(str, Any)]]:
```

##### `get_history_data`
```python
async def get_history_data(self, snapshot_id) -> Optional[Dict[(str, Any)]]:
```

##### `get_history_entries`
```python
async def get_history_entries(self, schedule_id, limit) -> List[Dict[(str, Any)]]:
```

##### `get_schedule`
```python
async def get_schedule(self, schedule_id) -> Optional[Dict[(str, Any)]]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `start_schedule`
```python
async def start_schedule(self, schedule) -> None:
```

##### `stop_schedule`
```python
async def stop_schedule(self, schedule_id) -> None:
```

##### `update_schedule`
```python
async def update_schedule(self, schedule_id, **updates) -> Dict[(str, Any)]:
```
