# Module: plugins.media_processor_plugin.code.utils.ai_background_remover

**Path:** `plugins/media_processor_plugin/code/utils/ai_background_remover.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import os
import asyncio
import urllib.request
import zipfile
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union, cast, Callable
from enum import Enum
import numpy as np
from pathlib import Path
import json
from PIL import Image, ImageFilter
import torch
import torchvision.transforms as transforms
from models.processing_config import BackgroundRemovalConfig
from utils.exceptions import BackgroundRemovalError
```

## Classes

| Class | Description |
| --- | --- |
| `AIBackgroundRemover` |  |
| `ModelDetails` |  |
| `ModelType` |  |

### Class: `AIBackgroundRemover`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `download_model` `async` |  |
| `get_model_info` `async` |  |
| `initialize` `async` |  |
| `is_model_downloaded` `async` |  |
| `remove_background` `async` |  |

##### `__init__`
```python
def __init__(self, file_manager, config_manager, logger):
```

##### `download_model`
```python
async def download_model(self, model_id, progress_callback) -> bool:
```

##### `get_model_info`
```python
async def get_model_info(self, model_id) -> Dict[(str, Any)]:
```

##### `initialize`
```python
async def initialize(self) -> bool:
```

##### `is_model_downloaded`
```python
async def is_model_downloaded(self, model_id) -> bool:
```

##### `remove_background`
```python
async def remove_background(self, image, config) -> Image.Image:
```

### Class: `ModelDetails`

#### Attributes

| Name | Value |
| --- | --- |
| `MODELS` | `    MODELS = {
        ModelType.U2NET: {
            "name": "U2Net",
            "description": "Original U2Net model for salient object detection",
            "url": "https://github.com/xuebinqin/U-2-Net/releases/download/U2NetHumanSeg/u2net_human_seg.pth",
            "size": 173475292,  # ~173MB
            "hash": "bc788c85e60baed816ffd6e2b2c6ae8a2b0afa57e335a14cc323cf1edf79abde"
        },
        ModelType.U2NETP: {
            "name": "U2Net-Lite",
            "description": "Lightweight version of U2Net (4.7MB)",
            "url": "https://github.com/xuebinqin/U-2-Net/releases/download/U2NetP/u2netp.pth",
            "size": 4710256,  # ~4.7MB
            "hash": "8cb63ecf8d9a4b62be6abf8e5c8a52d9ebeb7fcb9c64d4a561b5682f2a734af6"
        },
        ModelType.ISNET: {
            "name": "ISNet",
            "description": "ISNet for high-quality human segmentation",
            "url": "https://github.com/xuebinqin/DIS/releases/download/1.1/isnet.pth",
            "size": 176320856,  # ~176MB
            "hash": "a1ca63c02e6c4e371a0a3e6a75223ca2e1b1755caa095f6b334f17f6b4292969"
        },
        ModelType.MODNET: {
            "name": "MODNet",
            "description": "MODNet for real-time portrait matting",
            "url": "https://github.com/ZHKKKe/MODNet/releases/download/v1.0/modnet_photographic_portrait_matting.pth",
            "size": 24002228,  # ~24MB
            "hash": "815b64834ba6942c84c7b1c7ea36ebcbcb80b3e2c88b2d3eb25e7cc3fdb9453c"
        }
    }` |

### Class: `ModelType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `U2NET` | `'u2net'` |
| `U2NETP` | `'u2netp'` |
| `ISNET` | `'isnet'` |
| `MODNET` | `'modnet'` |
