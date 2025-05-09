# Module: core.file_manager

**Path:** `core/file_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import hashlib
import os
import pathlib
import shutil
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import FileError, ManagerInitializationError, ManagerShutdownError
```

## Classes

| Class | Description |
| --- | --- |
| `FileInfo` |  |
| `FileManager` |  |
| `FileType` |  |

### Class: `FileInfo`
**Decorators:**
- `@dataclass`

### Class: `FileManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `compute_file_hash` |  |
| `copy_file` |  |
| `create_backup` |  |
| `create_temp_file` |  |
| `delete_file` |  |
| `ensure_directory` |  |
| `get_file_info` |  |
| `get_file_path` |  |
| `initialize` |  |
| `list_files` |  |
| `move_file` |  |
| `read_binary` |  |
| `read_text` |  |
| `shutdown` |  |
| `status` |  |
| `write_binary` |  |
| `write_text` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager) -> None:
```

##### `compute_file_hash`
```python
def compute_file_hash(self, path, directory_type) -> str:
```

##### `copy_file`
```python
def copy_file(self, source_path, dest_path, source_dir_type, dest_dir_type, overwrite) -> None:
```

##### `create_backup`
```python
def create_backup(self, path, directory_type) -> str:
```

##### `create_temp_file`
```python
def create_temp_file(self, prefix, suffix) -> Tuple[(str, BinaryIO)]:
```

##### `delete_file`
```python
def delete_file(self, path, directory_type) -> None:
```

##### `ensure_directory`
```python
def ensure_directory(self, path, directory_type) -> pathlib.Path:
```

##### `get_file_info`
```python
def get_file_info(self, path, directory_type) -> FileInfo:
```

##### `get_file_path`
```python
def get_file_path(self, path, directory_type) -> pathlib.Path:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `list_files`
```python
def list_files(self, path, directory_type, recursive, include_dirs, pattern) -> List[FileInfo]:
```

##### `move_file`
```python
def move_file(self, source_path, dest_path, source_dir_type, dest_dir_type, overwrite) -> None:
```

##### `read_binary`
```python
def read_binary(self, path, directory_type) -> bytes:
```

##### `read_text`
```python
def read_text(self, path, directory_type) -> str:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `write_binary`
```python
def write_binary(self, path, content, directory_type, create_dirs) -> None:
```

##### `write_text`
```python
def write_text(self, path, content, directory_type, create_dirs) -> None:
```

### Class: `FileType`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `UNKNOWN` | `'unknown'` |
| `TEXT` | `'text'` |
| `BINARY` | `'binary'` |
| `IMAGE` | `'image'` |
| `DOCUMENT` | `'document'` |
| `AUDIO` | `'audio'` |
| `VIDEO` | `'video'` |
| `CONFIG` | `'config'` |
| `LOG` | `'log'` |
| `DATA` | `'data'` |
| `TEMP` | `'temp'` |
| `BACKUP` | `'backup'` |
