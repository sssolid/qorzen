# Module: plugins.media_processor_plugin.code.processors.media_processor

**Path:** `plugins/media_processor_plugin/code/processors/media_processor.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import io
from io import BytesIO
from PIL.Image import Resampling
from blib2to3.pygram import initialize
from utils.ai_background_remover import AIBackgroundRemover
from utils.config_manager import ConfigManager
from utils.font_manager import FontManager
import os
import pathlib
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, BinaryIO, cast
import PIL
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import piexif
from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager
from models.processing_config import ProcessingConfig, BackgroundRemovalConfig, BackgroundRemovalMethod, OutputFormat, ResizeMode, ImageFormat, WatermarkType, WatermarkPosition
from utils.exceptions import MediaProcessingError, ImageProcessingError
from utils.path_resolver import resolve_output_path, generate_filename
```

## Classes

| Class | Description |
| --- | --- |
| `MediaProcessor` |  |

### Class: `MediaProcessor`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `apply_format` `async` |  |
| `create_preview` `async` |  |
| `create_preview_from_image` `async` |  |
| `load_image` `async` |  |
| `load_image_from_bytes` `async` |  |
| `load_processing_config` `async` |  |
| `process_image` `async` |  |
| `remove_background` `async` |  |
| `save_image` `async` |  |
| `save_processing_config` `async` |  |

##### `__init__`
```python
def __init__(self, file_manager, task_manager, logger, processing_config, background_removal_config) -> None:
```

##### `apply_format`
```python
async def apply_format(self, image, format_config) -> Image.Image:
```

##### `create_preview`
```python
async def create_preview(self, image_path, config, size) -> bytes:
```

##### `create_preview_from_image`
```python
async def create_preview_from_image(self, image, format_config, size) -> bytes:
```

##### `load_image`
```python
async def load_image(self, image_path) -> Image.Image:
```

##### `load_image_from_bytes`
```python
async def load_image_from_bytes(self, image_data) -> Image.Image:
```

##### `load_processing_config`
```python
async def load_processing_config(self, config_path) -> ProcessingConfig:
```

##### `process_image`
```python
async def process_image(self, image_path, config, output_dir, overwrite) -> List[str]:
```

##### `remove_background`
```python
async def remove_background(self, image, config) -> Image.Image:
```

##### `save_image`
```python
async def save_image(self, image, output_path, format_config, overwrite) -> str:
```

##### `save_processing_config`
```python
async def save_processing_config(self, config, config_path) -> str:
```
