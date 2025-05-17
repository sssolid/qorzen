# Module: plugins.application_launcher.code.presets

**Path:** `plugins/application_launcher/code/presets.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import platform
import shutil
from typing import Dict, List, Optional, Any
from plugin import ApplicationConfig, ArgumentConfig, ArgumentType
```

## Functions

| Function | Description |
| --- | --- |
| `create_custom_script_app` |  |
| `get_common_applications` |  |

### `create_custom_script_app`
```python
def create_custom_script_app(script_type, script_content, name, description, category) -> ApplicationConfig:
```

### `get_common_applications`
```python
def get_common_applications() -> List[ApplicationConfig]:
```
