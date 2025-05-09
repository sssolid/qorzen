# Module: plugin_system.repository

**Path:** `plugin_system/repository.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import httpx
from qorzen.plugin_system.manifest import PluginManifest
from qorzen.plugin_system.package import PluginPackage, PackageFormat
```

## Classes

| Class | Description |
| --- | --- |
| `PluginRepository` |  |
| `PluginRepositoryError` |  |
| `PluginRepositoryManager` |  |
| `PluginSearchResult` |  |
| `PluginVersionInfo` |  |

### Class: `PluginRepository`

#### Methods

| Method | Description |
| --- | --- |
| `__del__` |  |
| `__init__` |  |
| `download_plugin` |  |
| `get_plugin_info` |  |
| `get_plugin_versions` |  |
| `log` |  |
| `publish_plugin` |  |
| `search` |  |

##### `__del__`
```python
def __del__(self) -> None:
```

##### `__init__`
```python
def __init__(self, name, url, api_key, timeout, logger) -> None:
```

##### `download_plugin`
```python
def download_plugin(self, plugin_name, version, output_path) -> Path:
```

##### `get_plugin_info`
```python
def get_plugin_info(self, plugin_name) -> Dict[(str, Any)]:
```

##### `get_plugin_versions`
```python
def get_plugin_versions(self, plugin_name) -> List[PluginVersionInfo]:
```

##### `log`
```python
def log(self, message, level) -> None:
```

##### `publish_plugin`
```python
def publish_plugin(self, package_path, release_notes, public) -> Dict[(str, Any)]:
```

##### `search`
```python
def search(self, query, tags, sort_by, limit, offset) -> List[PluginSearchResult]:
```

### Class: `PluginRepositoryError`
**Inherits from:** Exception

### Class: `PluginRepositoryManager`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_repository` |  |
| `download_plugin` |  |
| `get_repository` |  |
| `load_config` |  |
| `log` |  |
| `publish_plugin` |  |
| `remove_repository` |  |
| `save_config` |  |
| `search` |  |

##### `__init__`
```python
def __init__(self, config_file, logger) -> None:
```

##### `add_repository`
```python
def add_repository(self, repository) -> None:
```

##### `download_plugin`
```python
def download_plugin(self, plugin_name, version, repository, output_path) -> Path:
```

##### `get_repository`
```python
def get_repository(self, name) -> PluginRepository:
```

##### `load_config`
```python
def load_config(self, config_file) -> None:
```

##### `log`
```python
def log(self, message, level) -> None:
```

##### `publish_plugin`
```python
def publish_plugin(self, package_path, release_notes, public, repository) -> Dict[(str, Any)]:
```

##### `remove_repository`
```python
def remove_repository(self, name) -> bool:
```

##### `save_config`
```python
def save_config(self, config_file) -> None:
```

##### `search`
```python
def search(self, query, tags, repository, sort_by, limit, offset) -> Dict[(str, List[PluginSearchResult])]:
```

### Class: `PluginSearchResult`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `from_dict` |  |
| `to_dict` |  |

##### `__init__`
```python
def __init__(self, name, display_name, version, description, author, downloads, rating, capabilities, tags) -> None:
```

##### `from_dict`
```python
@classmethod
def from_dict(cls, data) -> PluginSearchResult:
```

##### `to_dict`
```python
def to_dict(self) -> Dict[(str, Any)]:
```

### Class: `PluginVersionInfo`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `from_dict` |  |
| `to_dict` |  |

##### `__init__`
```python
def __init__(self, name, version, release_date, release_notes, download_url, size_bytes, sha256, dependencies) -> None:
```

##### `from_dict`
```python
@classmethod
def from_dict(cls, data) -> PluginVersionInfo:
```

##### `to_dict`
```python
def to_dict(self) -> Dict[(str, Any)]:
```
