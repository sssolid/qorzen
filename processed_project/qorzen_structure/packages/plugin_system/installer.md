# Module: plugin_system.installer

**Path:** `plugin_system/installer.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import datetime
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from qorzen.plugin_system.manifest import PluginManifest, PluginDependency
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginVerifier
```

## Classes

| Class | Description |
| --- | --- |
| `InstalledPlugin` |  |
| `PluginInstallationError` |  |
| `PluginInstaller` |  |

### Class: `InstalledPlugin`
**Decorators:**
- `@dataclass`

#### Methods

| Method | Description |
| --- | --- |
| `__post_init__` |  |
| `from_dict` |  |
| `to_dict` |  |

##### `__post_init__`
```python
def __post_init__(self) -> None:
```

##### `from_dict`
```python
@classmethod
def from_dict(cls, data) -> InstalledPlugin:
```

##### `to_dict`
```python
def to_dict(self) -> Dict[(str, Any)]:
```

### Class: `PluginInstallationError`
**Inherits from:** Exception

### Class: `PluginInstaller`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `disable_plugin` |  |
| `enable_plugin` |  |
| `get_enabled_plugins` |  |
| `get_installed_plugin` |  |
| `get_installed_plugins` |  |
| `get_plugin_dir` |  |
| `install_plugin` |  |
| `is_plugin_installed` |  |
| `load_installed_plugins` |  |
| `log` |  |
| `resolve_dependencies` |  |
| `save_installed_plugins` |  |
| `uninstall_plugin` |  |
| `update_plugin` |  |

##### `__init__`
```python
def __init__(self, plugins_dir, verifier, logger) -> None:
```

##### `disable_plugin`
```python
def disable_plugin(self, plugin_name) -> bool:
```

##### `enable_plugin`
```python
def enable_plugin(self, plugin_name) -> bool:
```

##### `get_enabled_plugins`
```python
def get_enabled_plugins(self) -> Dict[(str, InstalledPlugin)]:
```

##### `get_installed_plugin`
```python
def get_installed_plugin(self, plugin_name) -> Optional[InstalledPlugin]:
```

##### `get_installed_plugins`
```python
def get_installed_plugins(self) -> Dict[(str, InstalledPlugin)]:
```

##### `get_plugin_dir`
```python
def get_plugin_dir(self, plugin_name) -> Path:
```

##### `install_plugin`
```python
def install_plugin(self, package_path, force, skip_verification, enable) -> InstalledPlugin:
```

##### `is_plugin_installed`
```python
def is_plugin_installed(self, plugin_name) -> bool:
```

##### `load_installed_plugins`
```python
def load_installed_plugins(self) -> None:
```

##### `log`
```python
def log(self, message, level) -> None:
```

##### `resolve_dependencies`
```python
def resolve_dependencies(self, package_path, repository_url) -> Dict[(str, Union[(str, bool)])]:
```

##### `save_installed_plugins`
```python
def save_installed_plugins(self) -> None:
```

##### `uninstall_plugin`
```python
def uninstall_plugin(self, plugin_name, keep_data) -> bool:
```

##### `update_plugin`
```python
def update_plugin(self, package_path, skip_verification) -> InstalledPlugin:
```
