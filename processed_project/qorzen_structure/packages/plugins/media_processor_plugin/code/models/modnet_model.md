# Module: plugins.media_processor_plugin.code.models.modnet_model

**Path:** `plugins/media_processor_plugin/code/models/modnet_model.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from typing import Union
import torch
import torch.nn as nn
import torch.nn.functional as F
```

## Classes

| Class | Description |
| --- | --- |
| `ConvBlock` |  |
| `IBNorm` |  |
| `MODNet` |  |
| `MODNetBackbone` |  |
| `MODNetDecoder` |  |
| `ResBlock` |  |

### Class: `ConvBlock`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_channels, out_channels, kernel_size, stride, padding, dilation, groups, bias, norm, activation) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `IBNorm`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, dim) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `MODNet`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `forward`
```python
def forward(self, x, inference) -> Union[(torch.Tensor, tuple)]:
```

### Class: `MODNetBackbone`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `forward`
```python
def forward(self, x) -> tuple:
```

### Class: `MODNetDecoder`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self) -> None:
```

##### `forward`
```python
def forward(self, features) -> torch.Tensor:
```

### Class: `ResBlock`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_channels, out_channels, stride, padding, dilation, norm) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```
