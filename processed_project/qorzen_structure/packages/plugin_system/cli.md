# Module: plugin_system.cli

**Path:** `plugin_system/cli.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from qorzen.plugin_system.manifest import PluginManifest, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, PluginVerifier
from qorzen.plugin_system.tools import create_plugin_template, package_plugin, test_plugin, validate_plugin, create_plugin_signing_key
import tempfile
```

## Functions

| Function | Description |
| --- | --- |
| `create_command` |  |
| `disable_command` |  |
| `enable_command` |  |
| `generate_key_command` |  |
| `install_command` |  |
| `list_command` |  |
| `main` |  |
| `package_command` |  |
| `sign_command` |  |
| `test_command` |  |
| `uninstall_command` |  |
| `validate_command` |  |
| `verify_command` |  |

### `create_command`
```python
def create_command(args) -> int:
```

### `disable_command`
```python
def disable_command(args) -> int:
```

### `enable_command`
```python
def enable_command(args) -> int:
```

### `generate_key_command`
```python
def generate_key_command(args) -> int:
```

### `install_command`
```python
def install_command(args) -> int:
```

### `list_command`
```python
def list_command(args) -> int:
```

### `main`
```python
def main(args) -> int:
```

### `package_command`
```python
def package_command(args) -> int:
```

### `sign_command`
```python
def sign_command(args) -> int:
```

### `test_command`
```python
def test_command(args) -> int:
```

### `uninstall_command`
```python
def uninstall_command(args) -> int:
```

### `validate_command`
```python
def validate_command(args) -> int:
```

### `verify_command`
```python
def verify_command(args) -> int:
```
