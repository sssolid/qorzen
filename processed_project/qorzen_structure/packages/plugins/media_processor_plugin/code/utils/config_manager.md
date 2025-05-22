# Module: plugins.media_processor_plugin.code.utils.config_manager

**Path:** `plugins/media_processor_plugin/code/utils/config_manager.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from pathlib import Path
from models.processing_config import ProcessingConfig
```

## Classes

| Class | Description |
| --- | --- |
| `ConfigManager` |  |

### Class: `ConfigManager`

#### Attributes

| Name | Value |
| --- | --- |
| `CONFIG_DIR` | `'media_processor'` |
| `FORMATS_FILE` | `'format_configs.json'` |
| `SETTINGS_FILE` | `'settings.json'` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `add_or_update_config` |  |
| `get_all_configs` |  |
| `get_config` |  |
| `get_setting` |  |
| `initialize` `async` |  |
| `load_configurations` `async` |  |
| `load_settings` `async` |  |
| `remove_config` |  |
| `save_configurations` `async` |  |
| `save_settings` `async` |  |
| `set_setting` |  |

##### `__init__`
```python
def __init__(self, file_manager, logger):
```

##### `add_or_update_config`
```python
def add_or_update_config(self, config) -> bool:
```

##### `get_all_configs`
```python
def get_all_configs(self) -> Dict[(str, ProcessingConfig)]:
```

##### `get_config`
```python
def get_config(self, config_id) -> Optional[ProcessingConfig]:
```

##### `get_setting`
```python
def get_setting(self, key, default) -> Any:
```

##### `initialize`
```python
async def initialize(self) -> bool:
```

##### `load_configurations`
```python
async def load_configurations(self) -> Dict[(str, ProcessingConfig)]:
```

##### `load_settings`
```python
async def load_settings(self) -> Dict[(str, Any)]:
```

##### `remove_config`
```python
def remove_config(self, config_id) -> bool:
```

##### `save_configurations`
```python
async def save_configurations(self) -> bool:
```

##### `save_settings`
```python
async def save_settings(self) -> bool:
```

##### `set_setting`
```python
def set_setting(self, key, value) -> bool:
```
