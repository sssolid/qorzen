# Module: plugins.media_processor_plugin.code.ui.preview_widget

**Path:** `plugins/media_processor_plugin/code/ui/preview_widget.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import io
import os
from typing import Optional, Union
from PySide6.QtCore import Qt, Signal, Slot, QSize, QRectF, QPointF, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QBrush, QColor, QResizeEvent, QPaintEvent, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy
```

## Classes

| Class | Description |
| --- | --- |
| `ImagePreviewWidget` |  |

### Class: `ImagePreviewWidget`
**Inherits from:** QWidget

#### Attributes

| Name | Value |
| --- | --- |
| `zoomChanged` | `    zoomChanged = Signal(float)  # Current zoom level` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `clear` |  |
| `get_image` |  |
| `load_image` |  |
| `load_image_data` |  |
| `mouseMoveEvent` |  |
| `mousePressEvent` |  |
| `mouseReleaseEvent` |  |
| `paintEvent` |  |
| `reset_view` |  |
| `resizeEvent` |  |
| `set_error` |  |
| `set_loading` |  |
| `set_status` |  |
| `set_zoom` |  |
| `sizeHint` |  |
| `wheelEvent` |  |

##### `__init__`
```python
def __init__(self, logger, parent) -> None:
```

##### `clear`
```python
def clear(self) -> None:
```

##### `get_image`
```python
def get_image(self) -> Optional[QImage]:
```

##### `load_image`
```python
def load_image(self, file_path) -> bool:
```

##### `load_image_data`
```python
def load_image_data(self, data) -> bool:
```

##### `mouseMoveEvent`
```python
def mouseMoveEvent(self, event) -> None:
```

##### `mousePressEvent`
```python
def mousePressEvent(self, event) -> None:
```

##### `mouseReleaseEvent`
```python
def mouseReleaseEvent(self, event) -> None:
```

##### `paintEvent`
```python
def paintEvent(self, event) -> None:
```

##### `reset_view`
```python
def reset_view(self) -> None:
```

##### `resizeEvent`
```python
def resizeEvent(self, event) -> None:
```

##### `set_error`
```python
def set_error(self, error_text) -> None:
```

##### `set_loading`
```python
def set_loading(self, loading) -> None:
```

##### `set_status`
```python
def set_status(self, status_text) -> None:
```

##### `set_zoom`
```python
def set_zoom(self, zoom_factor) -> None:
```

##### `sizeHint`
```python
def sizeHint(self) -> QSize:
```

##### `wheelEvent`
```python
def wheelEvent(self, event) -> None:
```
