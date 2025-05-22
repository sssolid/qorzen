# Module: plugins.media_processor_plugin.code.models.processing_config

**Path:** `plugins/media_processor_plugin/code/models/processing_config.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field, model_validator, field_validator
```

## Classes

| Class | Description |
| --- | --- |
| `BackgroundRemovalConfig` |  |
| `BackgroundRemovalMethod` |  |
| `ImageFormat` |  |
| `OutputFormat` |  |
| `ProcessingConfig` |  |
| `ResizeMode` |  |
| `WatermarkConfig` |  |
| `WatermarkPosition` |  |
| `WatermarkType` |  |

### Class: `BackgroundRemovalConfig`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `as_dict` `@property` |  |
| `validate_chroma_color` |  |

##### `as_dict`
```python
@property
def as_dict(self) -> Dict[(str, Any)]:
```

##### `validate_chroma_color`
```python
@field_validator('chroma_color')
def validate_chroma_color(cls, v) -> Optional[str]:
```

### Class: `BackgroundRemovalMethod`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `CHROMA_KEY` | `'chroma_key'` |
| `ALPHA_MATTING` | `'alpha_matting'` |
| `ML_MODEL` | `'ml_model'` |
| `SMART_SELECTION` | `'smart_selection'` |
| `MANUAL_MASK` | `'manual_mask'` |
| `NONE` | `'none'` |

### Class: `ImageFormat`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `JPEG` | `'jpeg'` |
| `PNG` | `'png'` |
| `TIFF` | `'tiff'` |
| `BMP` | `'bmp'` |
| `WEBP` | `'webp'` |
| `PSD` | `'psd'` |
| `PDF` | `'pdf'` |

### Class: `OutputFormat`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `as_dict` `@property` |  |
| `validate_colors` |  |
| `validate_resize_mode_requirements` |  |

##### `as_dict`
```python
@property
def as_dict(self) -> Dict[(str, Any)]:
```

##### `validate_colors`
```python
@field_validator('background_color', 'padding_color')
def validate_colors(cls, v) -> Optional[str]:
```

##### `validate_resize_mode_requirements`
```python
@model_validator(mode='before')
def validate_resize_mode_requirements(cls, values) -> Dict[(str, Any)]:
```

### Class: `ProcessingConfig`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `as_dict` `@property` |  |
| `set_updated_time` |  |
| `validate_output_formats` |  |

##### `as_dict`
```python
@property
def as_dict(self) -> Dict[(str, Any)]:
```

##### `set_updated_time`
```python
@model_validator(mode='before')
def set_updated_time(cls, values) -> Dict[(str, Any)]:
```

##### `validate_output_formats`
```python
@field_validator('output_formats')
def validate_output_formats(cls, v) -> List[OutputFormat]:
```

### Class: `ResizeMode`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `NONE` | `'none'` |
| `WIDTH` | `'width'` |
| `HEIGHT` | `'height'` |
| `EXACT` | `'exact'` |
| `MAX_DIMENSION` | `'max_dimension'` |
| `MIN_DIMENSION` | `'min_dimension'` |
| `PERCENTAGE` | `'percentage'` |

### Class: `WatermarkConfig`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `check_watermark_type_requirements` |  |

##### `check_watermark_type_requirements`
```python
@model_validator(mode='before')
def check_watermark_type_requirements(cls, values) -> Dict[(str, Any)]:
```

### Class: `WatermarkPosition`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `TOP_LEFT` | `'top_left'` |
| `TOP_CENTER` | `'top_center'` |
| `TOP_RIGHT` | `'top_right'` |
| `MIDDLE_LEFT` | `'middle_left'` |
| `MIDDLE_CENTER` | `'middle_center'` |
| `MIDDLE_RIGHT` | `'middle_right'` |
| `BOTTOM_LEFT` | `'bottom_left'` |
| `BOTTOM_CENTER` | `'bottom_center'` |
| `BOTTOM_RIGHT` | `'bottom_right'` |
| `TILED` | `'tiled'` |
| `CUSTOM` | `'custom'` |

### Class: `WatermarkType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `NONE` | `'none'` |
| `TEXT` | `'text'` |
| `IMAGE` | `'image'` |
