# Module: plugin_system.extension

**Path:** `plugin_system/extension.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import importlib
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, Protocol, cast
from dataclasses import dataclass, field
from qorzen.plugin_system.manifest import PluginExtensionPoint, PluginManifest
```

## Global Variables
```python
extension_registry = extension_registry = ExtensionRegistry()
```

## Functions

| Function | Description |
| --- | --- |
| `call_extension_point` |  |
| `get_extension_point` |  |
| `register_extension_point` |  |
| `register_plugin_extensions` |  |
| `unregister_plugin_extensions` |  |

### `call_extension_point`
```python
def call_extension_point(provider, extension_id, *args, **kwargs) -> Dict[(str, Any)]:
```

### `get_extension_point`
```python
def get_extension_point(provider, extension_id) -> Optional[ExtensionInterface]:
```

### `register_extension_point`
```python
def register_extension_point(provider, id, name, description, interface, version, parameters, provider_instance) -> ExtensionInterface:
```

### `register_plugin_extensions`
```python
def register_plugin_extensions(plugin_name, plugin_instance, manifest) -> None:
```

### `unregister_plugin_extensions`
```python
def unregister_plugin_extensions(plugin_name) -> None:
```

## Classes

| Class | Description |
| --- | --- |
| `ExtensionImplementation` |  |
| `ExtensionInterface` |  |
| `ExtensionPointNotFoundError` |  |
| `ExtensionPointVersionError` |  |
| `ExtensionRegistry` |  |

### Class: `ExtensionImplementation`
**Inherits from:** Protocol

#### Methods

| Method | Description |
| --- | --- |
| `__call__` |  |

##### `__call__`
```python
def __call__(self, *args, **kwargs) -> Any:
```

### Class: `ExtensionInterface`

#### Methods

| Method | Description |
| --- | --- |
| `__call__` |  |
| `__init__` |  |
| `get_all_implementations` |  |
| `get_implementation` |  |
| `register_implementation` |  |
| `unregister_implementation` |  |

##### `__call__`
```python
def __call__(self, *args, **kwargs) -> Dict[(str, Any)]:
```

##### `__init__`
```python
def __init__(self, provider, extension_point, provider_instance):
```

##### `get_all_implementations`
```python
def get_all_implementations(self) -> Dict[(str, ExtensionImplementation)]:
```

##### `get_implementation`
```python
def get_implementation(self, plugin_name) -> Optional[ExtensionImplementation]:
```

##### `register_implementation`
```python
def register_implementation(self, plugin_name, implementation) -> None:
```

##### `unregister_implementation`
```python
def unregister_implementation(self, plugin_name) -> None:
```

### Class: `ExtensionPointNotFoundError`
**Inherits from:** Exception

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, provider, extension_id):
```

### Class: `ExtensionPointVersionError`
**Inherits from:** Exception

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, provider, extension_id, required, available):
```

### Class: `ExtensionRegistry`
**Decorators:**
- `@dataclass`

#### Methods

| Method | Description |
| --- | --- |
| `__post_init__` |  |
| `get_all_extension_points` |  |
| `get_extension_point` |  |
| `get_provider_extension_points` |  |
| `log` |  |
| `register_extension_point` |  |
| `register_extension_use` |  |
| `register_plugin_extensions` |  |
| `unregister_extension_point` |  |
| `unregister_extension_use` |  |
| `unregister_plugin_extensions` |  |

##### `__post_init__`
```python
def __post_init__(self) -> None:
```

##### `get_all_extension_points`
```python
def get_all_extension_points(self) -> Dict[(str, Dict[(str, ExtensionInterface)])]:
```

##### `get_extension_point`
```python
def get_extension_point(self, provider, extension_id) -> Optional[ExtensionInterface]:
```

##### `get_provider_extension_points`
```python
def get_provider_extension_points(self, provider) -> Dict[(str, ExtensionInterface)]:
```

##### `log`
```python
def log(self, message, level) -> None:
```

##### `register_extension_point`
```python
def register_extension_point(self, provider, extension_point, provider_instance) -> None:
```

##### `register_extension_use`
```python
def register_extension_use(self, consumer, consumer_id, provider, extension_id, version, implementation, required) -> None:
```

##### `register_plugin_extensions`
```python
def register_plugin_extensions(self, plugin_name, plugin_instance, manifest) -> None:
```

##### `unregister_extension_point`
```python
def unregister_extension_point(self, provider, extension_id) -> None:
```

##### `unregister_extension_use`
```python
def unregister_extension_use(self, consumer, provider, extension_id) -> None:
```

##### `unregister_plugin_extensions`
```python
def unregister_plugin_extensions(self, plugin_name) -> None:
```
