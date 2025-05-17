# Module: plugin_system.dependency

**Path:** `plugin_system/dependency.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from qorzen.plugin_system.manifest import PluginManifest, PluginDependency
from qorzen.plugin_system.repository import PluginRepositoryManager
```

## Classes

| Class | Description |
| --- | --- |
| `CircularDependencyError` |  |
| `DependencyError` |  |
| `DependencyGraph` |  |
| `DependencyNode` |  |
| `DependencyResolver` |  |
| `IncompatibleVersionError` |  |
| `MissingDependencyError` |  |

### Class: `CircularDependencyError`
**Inherits from:** DependencyError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, dependency_chain):
```

### Class: `DependencyError`
**Inherits from:** Exception

### Class: `DependencyGraph`
**Decorators:**
- `@dataclass`

#### Methods

| Method | Description |
| --- | --- |
| `add_edge` |  |
| `add_node` |  |
| `get_dependencies` |  |
| `resolve` |  |

##### `add_edge`
```python
def add_edge(self, from_node, to_node) -> None:
```

##### `add_node`
```python
def add_node(self, node) -> None:
```

##### `get_dependencies`
```python
def get_dependencies(self, node_name) -> List[str]:
```

##### `resolve`
```python
def resolve(self) -> List[str]:
```

### Class: `DependencyNode`
**Decorators:**
- `@dataclass`

#### Methods

| Method | Description |
| --- | --- |
| `is_core` `@property` |  |
| `is_local` `@property` |  |

##### `is_core`
```python
@property
def is_core(self) -> bool:
```

##### `is_local`
```python
@property
def is_local(self) -> bool:
```

### Class: `DependencyResolver`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `get_dependency_graph` |  |
| `log` |  |
| `resolve_dependencies` |  |
| `resolve_plugin_order` |  |
| `set_core_version` |  |
| `set_installed_plugins` |  |
| `set_plugins_dir` |  |

##### `__init__`
```python
def __init__(self, repository_manager, logger):
```

##### `get_dependency_graph`
```python
def get_dependency_graph(self, plugin_manifests) -> DependencyGraph:
```

##### `log`
```python
def log(self, message, level) -> None:
```

##### `resolve_dependencies`
```python
def resolve_dependencies(self, plugin_manifest, resolve_transitives, fetch_missing) -> List[Tuple[(str, str, bool)]]:
```

##### `resolve_plugin_order`
```python
def resolve_plugin_order(self, plugin_manifests) -> List[str]:
```

##### `set_core_version`
```python
def set_core_version(self, version) -> None:
```

##### `set_installed_plugins`
```python
def set_installed_plugins(self, plugins) -> None:
```

##### `set_plugins_dir`
```python
def set_plugins_dir(self, plugins_dir) -> None:
```

### Class: `IncompatibleVersionError`
**Inherits from:** DependencyError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, plugin_name, dependency_name, required_version, available_version):
```

### Class: `MissingDependencyError`
**Inherits from:** DependencyError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, plugin_name, dependency_name, required_version):
```
