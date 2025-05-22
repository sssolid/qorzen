# Module: plugin_system.manifest

**Path:** `plugin_system/manifest.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import enum
import datetime
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, TYPE_CHECKING
import pydantic
from pydantic import Field, validator
from qorzen.plugin_system.config_schema import ConfigSchema
```

## Classes

| Class | Description |
| --- | --- |
| `PluginAuthor` |  |
| `PluginCapability` |  |
| `PluginDependency` |  |
| `PluginExtensionPoint` |  |
| `PluginExtensionUse` |  |
| `PluginLifecycleHook` |  |
| `PluginManifest` |  |

### Class: `PluginAuthor`
**Inherits from:** pydantic.BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_email` |  |
| `validate_url` |  |

##### `validate_email`
```python
@validator('email')
def validate_email(cls, v) -> str:
```

##### `validate_url`
```python
@validator('url')
def validate_url(cls, v) -> Optional[str]:
```

### Class: `PluginCapability`
**Inherits from:** str, enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `CONFIG_READ` | `'config.read'` |
| `CONFIG_WRITE` | `'config.write'` |
| `UI_EXTEND` | `'ui.extend'` |
| `EVENT_SUBSCRIBE` | `'event.subscribe'` |
| `EVENT_PUBLISH` | `'event.publish'` |
| `FILE_READ` | `'file.read'` |
| `FILE_WRITE` | `'file.write'` |
| `NETWORK_CONNECT` | `'network.connect'` |
| `DATABASE_READ` | `'database.read'` |
| `DATABASE_WRITE` | `'database.write'` |
| `SYSTEM_EXEC` | `'system.exec'` |
| `SYSTEM_MONITOR` | `'system.monitor'` |
| `PLUGIN_COMMUNICATE` | `'plugin.communicate'` |

#### Methods

| Method | Description |
| --- | --- |
| `get_description` |  |
| `get_risk_level` |  |

##### `get_description`
```python
@classmethod
def get_description(cls, capability) -> str:
```

##### `get_risk_level`
```python
@classmethod
def get_risk_level(cls, capability) -> str:
```

### Class: `PluginDependency`
**Inherits from:** pydantic.BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_version` |  |

##### `validate_version`
```python
@validator('version')
def validate_version(cls, v) -> str:
```

### Class: `PluginExtensionPoint`
**Inherits from:** pydantic.BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_id` |  |
| `validate_version` |  |

##### `validate_id`
```python
@validator('id')
def validate_id(cls, v) -> str:
```

##### `validate_version`
```python
@validator('version')
def validate_version(cls, v) -> str:
```

### Class: `PluginExtensionUse`
**Inherits from:** pydantic.BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_version` |  |

##### `validate_version`
```python
@validator('version')
def validate_version(cls, v) -> str:
```

### Class: `PluginLifecycleHook`
**Inherits from:** str, enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `PRE_INSTALL` | `'pre_install'` |
| `POST_INSTALL` | `'post_install'` |
| `PRE_UNINSTALL` | `'pre_uninstall'` |
| `POST_UNINSTALL` | `'post_uninstall'` |
| `PRE_ENABLE` | `'pre_enable'` |
| `POST_ENABLE` | `'post_enable'` |
| `PRE_DISABLE` | `'pre_disable'` |
| `POST_DISABLE` | `'post_disable'` |
| `PRE_UPDATE` | `'pre_update'` |
| `POST_UPDATE` | `'post_update'` |

### Class: `PluginManifest`
**Inherits from:** pydantic.BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `get_capability_risks` |  |
| `get_extension_point` |  |
| `has_extension_point` |  |
| `is_compatible_with_core` |  |
| `load` |  |
| `satisfies_dependency` |  |
| `save` |  |
| `set_config_schema` |  |
| `to_dict` |  |
| `to_json` |  |
| `validate_core_version` |  |
| `validate_license` |  |
| `validate_lifecycle_hooks` |  |
| `validate_name` |  |
| `validate_version` |  |

##### `get_capability_risks`
```python
def get_capability_risks(self) -> Dict[(str, List[str])]:
```

##### `get_extension_point`
```python
def get_extension_point(self, extension_id) -> Optional[PluginExtensionPoint]:
```

##### `has_extension_point`
```python
def has_extension_point(self, extension_id) -> bool:
```

##### `is_compatible_with_core`
```python
def is_compatible_with_core(self, core_version) -> bool:
```

##### `load`
```python
@classmethod
def load(cls, path) -> PluginManifest:
```

##### `satisfies_dependency`
```python
def satisfies_dependency(self, dependency) -> bool:
```

##### `save`
```python
def save(self, path) -> None:
```

##### `set_config_schema`
```python
def set_config_schema(self, schema) -> None:
```

##### `to_dict`
```python
def to_dict(self) -> Dict[(str, Any)]:
```

##### `to_json`
```python
def to_json(self) -> str:
```

##### `validate_core_version`
```python
@validator('min_core_version', 'max_core_version')
def validate_core_version(cls, v) -> Optional[str]:
```

##### `validate_license`
```python
@validator('license')
def validate_license(cls, v) -> str:
```

##### `validate_lifecycle_hooks`
```python
@validator('lifecycle_hooks')
def validate_lifecycle_hooks(cls, v) -> Dict[(PluginLifecycleHook, str)]:
```

##### `validate_name`
```python
@validator('name')
def validate_name(cls, v) -> str:
```

##### `validate_version`
```python
@validator('version')
def validate_version(cls, v) -> str:
```
