# Module: core.file_manager

**Path:** `core/file_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import hashlib
import os
import pathlib
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Optional, Set, Tuple, Union, cast, AsyncIterator
import aiofiles
import aiofiles.os
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
| `compute_file_hash` `async` |  |
| `copy_file` `async` |  |
| `create_backup` `async` |  |
| `create_temp_file` `async` |  |
| `delete_file` `async` |  |
| `ensure_directory` `async` |  |
| `file_exists` `async` |  |
| `get_file_info` `async` |  |
| `get_file_path` |  |
| `initialize` `async` |  |
| `list_files` `async` |  |
| `move_file` `async` |  |
| `read_binary` `async` |  |
| `read_text` `async` |  |
| `shutdown` `async` |  |
| `status` |  |
| `write_binary` `async` |  |
| `write_text` `async` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager) -> None:
```

##### `compute_file_hash`
```python
async def compute_file_hash(self, path, directory_type) -> str:
```

##### `copy_file`
```python
async def copy_file(self, source_path, dest_path, source_dir_type, dest_dir_type, overwrite) -> None:
```

##### `create_backup`
```python
async def create_backup(self, path, directory_type) -> str:
```

##### `create_temp_file`
```python
async def create_temp_file(self, prefix, suffix) -> Tuple[(str, BinaryIO)]:
```

##### `delete_file`
```python
async def delete_file(self, path, directory_type) -> None:
```

##### `ensure_directory`
```python
async def ensure_directory(self, path, directory_type) -> pathlib.Path:
```

##### `file_exists`
```python
async def file_exists(self, path) -> bool:
```

##### `get_file_info`
```python
async def get_file_info(self, path, directory_type) -> FileInfo:
```

##### `get_file_path`
```python
def get_file_path(self, path, directory_type) -> pathlib.Path:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `list_files`
```python
async def list_files(self, path, directory_type, recursive, include_dirs, pattern) -> List[FileInfo]:
```

##### `move_file`
```python
async def move_file(self, source_path, dest_path, source_dir_type, dest_dir_type, overwrite) -> None:
```

##### `read_binary`
```python
async def read_binary(self, path, directory_type) -> bytes:
```

##### `read_text`
```python
async def read_text(self, path, directory_type) -> str:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `write_binary`
```python
async def write_binary(self, path, content, directory_type, create_dirs) -> None:
```

##### `write_text`
```python
async def write_text(self, path, content, directory_type, create_dirs) -> None:
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
