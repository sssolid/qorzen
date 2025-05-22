# Module: plugins.media_processor_plugin.code.processors.optimized_processor

**Path:** `plugins/media_processor_plugin/code/processors/optimized_processor.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import tempfile
from typing import Dict, List, Optional, Set, Tuple, Any, Union, cast
from pathlib import Path
import asyncio
from PIL import Image
from models.processing_config import ProcessingConfig, BackgroundRemovalConfig, OutputFormat
from utils.exceptions import MediaProcessingError
```

## Classes

| Class | Description |
| --- | --- |
| `OptimizedProcessor` |  |
| `ProcessingOptimizer` |  |

### Class: `OptimizedProcessor`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `batch_process_images` `async` |  |
| `enable_intermediate_images` |  |
| `process_image` `async` |  |

##### `__init__`
```python
def __init__(self, media_processor, logger, use_intermediate) -> None:
```

##### `batch_process_images`
```python
async def batch_process_images(self, image_paths, config, output_dir, overwrite, progress_callback) -> Dict[(str, List[str])]:
```

##### `enable_intermediate_images`
```python
def enable_intermediate_images(self, enabled) -> None:
```

##### `process_image`
```python
async def process_image(self, image_path, config, output_dir, overwrite) -> List[str]:
```

### Class: `ProcessingOptimizer`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `should_use_intermediate` |  |

##### `__init__`
```python
def __init__(self, logger) -> None:
```

##### `should_use_intermediate`
```python
def should_use_intermediate(self, config) -> bool:
```
