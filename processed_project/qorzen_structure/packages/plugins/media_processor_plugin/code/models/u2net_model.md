# Module: plugins.media_processor_plugin.code.models.u2net_model

**Path:** `plugins/media_processor_plugin/code/models/u2net_model.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
```

## Classes

| Class | Description |
| --- | --- |
| `ConvBNReLU` |  |
| `REBNCONV` |  |
| `RSU4` |  |
| `RSU4F` |  |
| `RSU5` |  |
| `RSU6` |  |
| `RSU7` |  |
| `U2NET` |  |
| `U2NETP` |  |

### Class: `ConvBNReLU`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, out_ch, kernel_size, dilation) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `REBNCONV`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, out_ch, kernel_size, dilation, stride, padding) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `RSU4`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, mid_ch, out_ch) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `RSU4F`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, mid_ch, out_ch) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `RSU5`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, mid_ch, out_ch) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `RSU6`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, mid_ch, out_ch) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `RSU7`
**Inherits from:** nn.Module

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `forward` |  |

##### `__init__`
```python
def __init__(self, in_ch, mid_ch, out_ch) -> None:
```

##### `forward`
```python
def forward(self, x) -> torch.Tensor:
```

### Class: `U2NET`
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
def forward(self, x) -> tuple:
```

### Class: `U2NETP`
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
def forward(self, x) -> tuple:
```
