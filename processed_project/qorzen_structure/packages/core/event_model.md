# Module: core.event_model

**Path:** `core/event_model.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import dataclasses
import datetime
import enum
import uuid
from typing import Any, Dict, Optional, Union, Callable, List, TypeVar, Generic
from pydantic import BaseModel, Field
```

## Global Variables
```python
T = T = TypeVar('T')
EventHandler = EventHandler = Callable[[Event], None]
```

## Classes

| Class | Description |
| --- | --- |
| `Config` |  |
| `Event` |  |
| `EventPayload` |  |
| `EventSubscription` |  |
| `EventType` |  |

### Class: `Config`

#### Attributes

| Name | Value |
| --- | --- |
| `arbitrary_types_allowed` | `True` |
| `json_encoders` | `        json_encoders = {
            datetime.datetime: lambda dt: dt.isoformat(),
            uuid.UUID: lambda id: str(id)
        }` |

### Class: `Event`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `__str__` |  |
| `create` |  |
| `to_dict` |  |

##### `__str__`
```python
def __str__(self) -> str:
```

##### `create`
```python
@classmethod
def create(cls, event_type, source, payload, correlation_id) -> Event:
```

##### `to_dict`
```python
def to_dict(self) -> Dict[(str, Any)]:
```

### Class: `EventPayload`
**Inherits from:** BaseModel, Generic[T]

### Class: `EventSubscription`
**Decorators:**
- `@dataclasses.dataclass`

#### Methods

| Method | Description |
| --- | --- |
| `matches_event` |  |

##### `matches_event`
```python
def matches_event(self, event) -> bool:
```

### Class: `EventType`
**Inherits from:** str, enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `SYSTEM_STARTED` | `'system/started'` |
| `UI_READY` | `'ui/ready'` |
| `UI_UPDATE` | `'ui/update'` |
| `UI_COMPONENT_ADDED` | `'ui/component/added'` |
| `LOG_MESSAGE` | `'log/message'` |
| `LOG_ERROR` | `'log/error'` |
| `LOG_EXCEPTION` | `'log/exception'` |
| `LOG_WARNING` | `'log/warning'` |
| `LOG_DEBUG` | `'log/debug'` |
| `LOG_INFO` | `'log/info'` |
| `LOG_TRACE` | `'log/trace'` |
| `LOG_CRITICAL` | `'log/critical'` |
| `LOG_EVENT` | `'log/event'` |
| `PLUGIN_LOADED` | `'plugin/loaded'` |
| `PLUGIN_UNLOADED` | `'plugin/unloaded'` |
| `PLUGIN_ENABLED` | `'plugin/enabled'` |
| `PLUGIN_DISABLED` | `'plugin/disabled'` |
| `PLUGIN_INSTALLED` | `'plugin/installed'` |
| `PLUGIN_UNINSTALLED` | `'plugin/uninstalled'` |
| `PLUGIN_UPDATED` | `'plugin/updated'` |
| `PLUGIN_ERROR` | `'plugin/error'` |
| `PLUGIN_INITIALIZED` | `'plugin/initialized'` |
| `PLUGIN_MANAGER_INITIALIZED` | `'plugin_manager/initialized'` |
| `MONITORING_METRICS` | `'monitoring/metrics'` |
| `MONITORING_ALERT` | `'monitoring/alert'` |
| `CONFIG_CHANGED` | `'config/changed'` |
| `CUSTOM` | `'custom'` |

#### Methods

| Method | Description |
| --- | --- |
| `plugin_specific` |  |
| `requires_main_thread` |  |

##### `plugin_specific`
```python
@classmethod
def plugin_specific(cls, plugin_name, event_name) -> str:
```

##### `requires_main_thread`
```python
@classmethod
def requires_main_thread(cls, event_type) -> bool:
```
