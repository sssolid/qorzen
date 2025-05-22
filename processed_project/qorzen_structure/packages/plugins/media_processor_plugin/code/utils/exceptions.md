# Module: plugins.media_processor_plugin.code.utils.exceptions

**Path:** `plugins/media_processor_plugin/code/utils/exceptions.py`

[Back to Project Index](../../../../../index.md)

## Imports
```python
from __future__ import annotations
from typing import Optional
```

## Classes

| Class | Description |
| --- | --- |
| `BackgroundRemovalError` |  |
| `BatchProcessingError` |  |
| `ConfigurationError` |  |
| `FileIOError` |  |
| `ImageProcessingError` |  |
| `MediaProcessingError` |  |
| `OutputFormatError` |  |

### Class: `BackgroundRemovalError`
**Inherits from:** ImageProcessingError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, file_path, method) -> None:
```

### Class: `BatchProcessingError`
**Inherits from:** MediaProcessingError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, job_id) -> None:
```

### Class: `ConfigurationError`
**Inherits from:** MediaProcessingError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, config_id) -> None:
```

### Class: `FileIOError`
**Inherits from:** MediaProcessingError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, file_path, is_input) -> None:
```

### Class: `ImageProcessingError`
**Inherits from:** MediaProcessingError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, file_path, format_id) -> None:
```

### Class: `MediaProcessingError`
**Inherits from:** Exception

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, file_path) -> None:
```

### Class: `OutputFormatError`
**Inherits from:** ImageProcessingError

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, file_path, format_id, format_name) -> None:
```
