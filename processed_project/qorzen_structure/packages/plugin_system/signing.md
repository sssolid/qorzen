# Module: plugin_system.signing

**Path:** `plugin_system/signing.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import base64
import datetime
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from qorzen.plugin_system.manifest import PluginManifest
from qorzen.plugin_system.package import PluginPackage
```

## Classes

| Class | Description |
| --- | --- |
| `PluginSigner` |  |
| `PluginVerifier` |  |
| `SigningError` |  |
| `SigningKey` |  |
| `VerificationError` |  |

### Class: `PluginSigner`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `generate_key` |  |
| `load_key` |  |
| `save_key` |  |
| `sign_manifest` |  |
| `sign_package` |  |

##### `__init__`
```python
def __init__(self, key) -> None:
```

##### `generate_key`
```python
@staticmethod
def generate_key(name) -> SigningKey:
```

##### `load_key`
```python
@staticmethod
def load_key(path) -> SigningKey:
```

##### `save_key`
```python
def save_key(self, path, include_private) -> None:
```

##### `sign_manifest`
```python
def sign_manifest(self, manifest) -> None:
```

##### `sign_package`
```python
def sign_package(self, package) -> None:
```

### Class: `PluginVerifier`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_trusted_key` |  |
| `load_trusted_keys` |  |
| `remove_trusted_key` |  |
| `verify_manifest` |  |
| `verify_package` |  |

##### `__init__`
```python
def __init__(self, trusted_keys) -> None:
```

##### `add_trusted_key`
```python
def add_trusted_key(self, key) -> None:
```

##### `load_trusted_keys`
```python
def load_trusted_keys(self, directory) -> int:
```

##### `remove_trusted_key`
```python
def remove_trusted_key(self, fingerprint) -> bool:
```

##### `verify_manifest`
```python
def verify_manifest(self, manifest) -> bool:
```

##### `verify_package`
```python
def verify_package(self, package) -> bool:
```

### Class: `SigningError`
**Inherits from:** Exception

### Class: `SigningKey`
**Decorators:**
- `@dataclass`

### Class: `VerificationError`
**Inherits from:** Exception
