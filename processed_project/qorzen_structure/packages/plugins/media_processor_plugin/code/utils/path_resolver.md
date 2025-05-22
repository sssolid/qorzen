# Module: plugins.media_processor_plugin.code.utils.path_resolver

**Path:** `plugins/media_processor_plugin/code/utils/path_resolver.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from exceptions import MediaProcessingError
```

## Functions

| Function | Description |
| --- | --- |
| `generate_batch_folder_name` |  |
| `generate_filename` |  |
| `get_unique_output_path` |  |
| `resolve_output_path` |  |

### `generate_batch_folder_name`
```python
def generate_batch_folder_name(template) -> str:
```

### `generate_filename`
```python
def generate_filename(template, base_name, extension, prefix, suffix) -> str:
```

### `get_unique_output_path`
```python
def get_unique_output_path(base_path) -> str:
```

### `resolve_output_path`
```python
def resolve_output_path(input_path, output_dir, format_config, file_exists_handler) -> str:
```
