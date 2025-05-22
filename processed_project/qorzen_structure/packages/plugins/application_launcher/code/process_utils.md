# Module: plugins.application_launcher.code.process_utils

**Path:** `plugins/application_launcher/code/process_utils.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import re
import platform
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any
```

## Classes

| Class | Description |
| --- | --- |
| `ProcessInfo` |  |
| `ProcessMonitor` |  |

### Class: `ProcessInfo`
**Decorators:**
- `@dataclass`

### Class: `ProcessMonitor`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `build_command_line` |  |
| `create_temporary_script` |  |
| `find_output_files` |  |
| `get_process_info` |  |
| `limit_process_resources` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `build_command_line`
```python
@staticmethod
def build_command_line(executable, arguments, environment) -> Tuple[(str, Dict[(str, str)])]:
```

##### `create_temporary_script`
```python
@staticmethod
def create_temporary_script(script_content, script_type) -> Tuple[(str, str)]:
```

##### `find_output_files`
```python
def find_output_files(self, working_dir, patterns, base_timestamp) -> List[str]:
```

##### `get_process_info`
```python
def get_process_info(self, pid) -> Optional[ProcessInfo]:
```

##### `limit_process_resources`
```python
def limit_process_resources(self, pid, max_memory_mb) -> bool:
```
