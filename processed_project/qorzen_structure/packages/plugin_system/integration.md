# Module: plugin_system.integration

**Path:** `plugin_system/integration.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import os
import tempfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, cast
import re
import semver
from qorzen.plugin_system.dependency import DependencyResolver, DependencyError
from qorzen.plugin_system.installer import PluginInstaller, PluginInstallationError, InstalledPlugin
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook, PluginDependency
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.repository import PluginRepositoryManager, PluginRepositoryError
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.lifecycle import execute_hook, LifecycleHookError, PluginLifecycleState, set_plugin_state
```

## Classes

| Class | Description |
| --- | --- |
| `IntegratedPluginInstaller` |  |
| `PluginIntegrationError` |  |

### Class: `IntegratedPluginInstaller`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `disable_plugin` `async` |  |
| `enable_plugin` `async` |  |
| `get_enabled_plugins` |  |
| `get_installed_plugin` |  |
| `get_installed_plugins` |  |
| `get_loading_order` `async` |  |
| `install_plugin` `async` |  |
| `is_plugin_installed` |  |
| `log` |  |
| `resolve_dependencies` `async` |  |
| `uninstall_plugin` `async` |  |
| `update_plugin` `async` |  |

##### `__init__`
```python
def __init__(self, plugins_dir, repository_manager, verifier, logger, core_version):
```

##### `disable_plugin`
```python
async def disable_plugin(self, plugin_name) -> bool:
```

##### `enable_plugin`
```python
async def enable_plugin(self, plugin_name) -> bool:
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

##### `get_loading_order`
```python
async def get_loading_order(self) -> List[str]:
```

##### `install_plugin`
```python
async def install_plugin(self, package_path, force, skip_verification, enable, resolve_dependencies, install_dependencies) -> InstalledPlugin:
```

##### `is_plugin_installed`
```python
def is_plugin_installed(self, plugin_name) -> bool:
```

##### `log`
```python
def log(self, message, level) -> None:
```

##### `resolve_dependencies`
```python
async def resolve_dependencies(self, package_path, repository_url) -> Dict[(str, Union[(str, bool)])]:
```

##### `uninstall_plugin`
```python
async def uninstall_plugin(self, plugin_name, keep_data, check_dependents) -> bool:
```

##### `update_plugin`
```python
async def update_plugin(self, package_path, skip_verification, resolve_dependencies, install_dependencies) -> InstalledPlugin:
```

### Class: `PluginIntegrationError`
**Inherits from:** Exception

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, plugin_name, cause):
```
