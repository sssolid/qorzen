# Module: plugins.media_processor_plugin.code.models.isnet_model

**Path:** `plugins/media_processor_plugin/code/models/isnet_model.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F
```

## Functions

| Function | Description |
| --- | --- |
| `conv_bn_relu` |  |

### `conv_bn_relu`
```python
def conv_bn_relu(in_ch, out_ch, kernel_size, stride, padding, dilation) -> nn.Sequential:
```

## Classes

| Class | Description |
| --- | --- |
| `ISNetDIS` |  |
| `ISNetDecoder` |  |
| `ISNetEncoder` |  |
| `ResidualConv` |  |

### Class: `ISNetDIS`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, out_ch, depth) -> None:
```

##### `forward`
```python
def forward(self, x) -> tuple:
```

### Class: `ISNetDecoder`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, depth) -> None:
```

##### `forward`
```python
def forward(self, features) -> torch.Tensor:
```

### Class: `ISNetEncoder`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, depth) -> None:
```

##### `forward`
```python
def forward(self, x) -> tuple:
```

### Class: `ResidualConv`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, out_ch) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```
