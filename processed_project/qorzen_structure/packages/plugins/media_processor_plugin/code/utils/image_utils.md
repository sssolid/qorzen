# Module: plugins.media_processor_plugin.code.utils.image_utils

**Path:** `plugins/media_processor_plugin/code/utils/image_utils.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from PIL.Image import Resampling
import io
import os
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageOps, ImageFilter
from io import BytesIO
```

## Functions

| Function | Description |
| --- | --- |
| `apply_threshold_mask` |  |
| `auto_contrast_mask` |  |
| `convert_to_format` |  |
| `create_gradient_mask` |  |
| `fit_image_to_size` |  |
| `generate_thumbnail` |  |
| `get_image_info` |  |
| `is_transparent` |  |

### `apply_threshold_mask`
```python
def apply_threshold_mask(image, threshold_min, threshold_max, feather) -> Image.Image:
```

### `auto_contrast_mask`
```python
def auto_contrast_mask(mask, cutoff) -> Image.Image:
```

### `convert_to_format`
```python
def convert_to_format(image, format_name, quality, transparent) -> bytes:
```

### `create_gradient_mask`
```python
def create_gradient_mask(width, height, center_opacity, edge_opacity, radius_factor) -> Image.Image:
```

### `fit_image_to_size`
```python
def fit_image_to_size(image, max_width, max_height, maintain_aspect) -> Image.Image:
```

### `generate_thumbnail`
```python
def generate_thumbnail(image, size, maintain_aspect) -> Image.Image:
```

### `get_image_info`
```python
def get_image_info(file_path) -> Dict[(str, Any)]:
```

### `is_transparent`
```python
def is_transparent(image) -> bool:
```
