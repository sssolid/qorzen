# Module: plugins.application_launcher.code.events

**Path:** `plugins/application_launcher/code/events.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional
```

## Functions

| Function | Description |
| --- | --- |
| `create_app_added_event` |  |
| `create_app_completed_event` |  |
| `create_app_launched_event` |  |

### `create_app_added_event`
```python
def create_app_added_event(app_id, app_name) -> Dict[(str, Any)]:
```

### `create_app_completed_event`
```python
def create_app_completed_event(app_id, app_name, exit_code, runtime_seconds, output_files) -> Dict[(str, Any)]:
```

### `create_app_launched_event`
```python
def create_app_launched_event(app_id, app_name, command_line, working_dir) -> Dict[(str, Any)]:
```

## Classes

| Class | Description |
| --- | --- |
| `AppLauncherEventType` |  |

### Class: `AppLauncherEventType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `APP_ADDED` | `'application_launcher:app_added'` |
| `APP_UPDATED` | `'application_launcher:app_updated'` |
| `APP_REMOVED` | `'application_launcher:app_removed'` |
| `APP_LAUNCHED` | `'application_launcher:app_launched'` |
| `APP_TERMINATED` | `'application_launcher:app_terminated'` |
| `APP_COMPLETED` | `'application_launcher:app_completed'` |
| `OUTPUT_DETECTED` | `'application_launcher:output_detected'` |

#### Methods

| Method | Description |
| --- | --- |
| `app_added` |  |
| `app_completed` |  |
| `app_launched` |  |
| `app_removed` |  |
| `app_terminated` |  |
| `app_updated` |  |
| `output_detected` |  |

##### `app_added`
```python
@classmethod
def app_added(cls) -> str:
```

##### `app_completed`
```python
@classmethod
def app_completed(cls) -> str:
```

##### `app_launched`
```python
@classmethod
def app_launched(cls) -> str:
```

##### `app_removed`
```python
@classmethod
def app_removed(cls) -> str:
```

##### `app_terminated`
```python
@classmethod
def app_terminated(cls) -> str:
```

##### `app_updated`
```python
@classmethod
def app_updated(cls) -> str:
```

##### `output_detected`
```python
@classmethod
def output_detected(cls) -> str:
```
