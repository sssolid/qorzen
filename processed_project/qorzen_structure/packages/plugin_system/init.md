# Module: plugin_system

**Path:** `plugin_system/__init__.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
from qorzen.plugin_system.manifest import PluginManifest, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, PluginVerifier
from qorzen.plugin_system.installer import PluginInstaller
from qorzen.plugin_system.tools import create_plugin_template, package_plugin
```

## Global Variables
```python
__all__ = __all__ = [
    "PluginManifest",
    "PluginCapability",
    "PluginPackage",
    "PackageFormat",
    "PluginSigner",
    "PluginVerifier",
    "PluginInstaller",
    "create_plugin_template",
    "package_plugin",
]
```
