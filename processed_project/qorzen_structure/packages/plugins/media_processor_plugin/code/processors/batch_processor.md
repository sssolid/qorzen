# Module: plugins.media_processor_plugin.code.processors.batch_processor

**Path:** `plugins/media_processor_plugin/code/processors/batch_processor.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import datetime
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from models.processing_config import ProcessingConfig
from utils.exceptions import MediaProcessingError, BatchProcessingError
from utils.path_resolver import generate_batch_folder_name
from media_processor import MediaProcessor
```

## Classes

| Class | Description |
| --- | --- |
| `BatchProcessor` |  |

### Class: `BatchProcessor`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cancel_job` `async` |  |
| `get_active_jobs` `async` |  |
| `get_job_status` `async` |  |
| `start_batch_job` `async` |  |

##### `__init__`
```python
def __init__(self, media_processor, task_manager, event_bus_manager, concurrency_manager, logger, processing_config) -> None:
```

##### `cancel_job`
```python
async def cancel_job(self, job_id) -> bool:
```

##### `get_active_jobs`
```python
async def get_active_jobs(self) -> List[str]:
```

##### `get_job_status`
```python
async def get_job_status(self, job_id) -> Dict[(str, Any)]:
```

##### `start_batch_job`
```python
async def start_batch_job(self, file_paths, config, output_dir, overwrite) -> str:
```
