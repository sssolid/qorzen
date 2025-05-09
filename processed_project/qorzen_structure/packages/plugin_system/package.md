# Module: plugin_system.package

**Path:** `plugin_system/package.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import enum
import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, BinaryIO, Any
from qorzen.plugin_system.manifest import PluginManifest
```

## Classes

| Class | Description |
| --- | --- |
| `PackageError` |  |
| `PackageFormat` |  |
| `PluginPackage` |  |

### Class: `PackageError`
**Inherits from:** Exception

### Class: `PackageFormat`
**Inherits from:** str, enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `ZIP` | `'zip'` |
| `WHEEL` | `'wheel'` |
| `DIRECTORY` | `'directory'` |

### Class: `PluginPackage`

#### Attributes

| Name | Value |
| --- | --- |
| `MANIFEST_PATH` | `'manifest.json'` |
| `CODE_DIR` | `'code'` |
| `RESOURCES_DIR` | `'resources'` |
| `DOCS_DIR` | `'docs'` |

#### Methods

| Method | Description |
| --- | --- |
| `__del__` |  |
| `__init__` |  |
| `cleanup` |  |
| `create` |  |
| `extract` |  |
| `get_code_dir` |  |
| `get_docs_dir` |  |
| `get_resources_dir` |  |
| `load` |  |
| `verify_integrity` |  |

##### `__del__`
```python
def __del__(self) -> None:
```

##### `__init__`
```python
def __init__(self, manifest, format, path) -> None:
```

##### `cleanup`
```python
def cleanup(self) -> None:
```

##### `create`
```python
@classmethod
def create(cls, source_dir, output_path, manifest, format, include_patterns, exclude_patterns) -> PluginPackage:
```

##### `extract`
```python
def extract(self, output_dir) -> Path:
```

##### `get_code_dir`
```python
def get_code_dir(self) -> Optional[Path]:
```

##### `get_docs_dir`
```python
def get_docs_dir(self) -> Optional[Path]:
```

##### `get_resources_dir`
```python
def get_resources_dir(self) -> Optional[Path]:
```

##### `load`
```python
@classmethod
def load(cls, path) -> PluginPackage:
```

##### `verify_integrity`
```python
def verify_integrity(self) -> bool:
```
