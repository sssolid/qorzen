# Module: plugin_system.tools

**Path:** `plugin_system/tools.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import datetime
import inspect
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from qorzen.plugin_system.manifest import PluginManifest, PluginAuthor, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, SigningKey
```

## Functions

| Function | Description |
| --- | --- |
| `create_plugin_signing_key` |  |
| `create_plugin_template` |  |
| `package_plugin` |  |
| `test_plugin` |  |
| `validate_plugin` |  |

### `create_plugin_signing_key`
```python
def create_plugin_signing_key(name, output_path) -> SigningKey:
```

### `create_plugin_template`
```python
def create_plugin_template(output_dir, plugin_name, display_name, description, author_name, author_email, author_url, version, license, force) -> Path:
```

### `package_plugin`
```python
def package_plugin(plugin_dir, output_path, format, signing_key, include_patterns, exclude_patterns) -> Path:
```

### `test_plugin`
```python
def test_plugin(plugin_dir, mock_env, test_pattern) -> bool:
```

### `validate_plugin`
```python
def validate_plugin(plugin_dir) -> Dict[(str, List[str])]:
```
