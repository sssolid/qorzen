# Module: core.cloud_manager

**Path:** `core/cloud_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import importlib
import inspect
import os
import sys
import asyncio
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError
```

## Global Variables
```python
T = T = TypeVar('T')
```

## Classes

| Class | Description |
| --- | --- |
| `AWSStorageService` |  |
| `AzureBlobStorageService` |  |
| `BaseCloudService` |  |
| `CloudManager` |  |
| `CloudProvider` |  |
| `CloudService` |  |
| `CloudStorageService` |  |
| `GCPStorageService` |  |
| `LocalStorageService` |  |
| `StorageBackend` |  |

### Class: `AWSStorageService`
**Inherits from:** BaseCloudService

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `delete_file` `async` |  |
| `download_file` `async` |  |
| `initialize` `async` |  |
| `list_files` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |
| `upload_file` `async` |  |

##### `__init__`
```python
def __init__(self, config, logger) -> None:
```

##### `delete_file`
```python
async def delete_file(self, remote_path) -> bool:
```

##### `download_file`
```python
async def download_file(self, remote_path, local_path) -> bool:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `list_files`
```python
async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

##### `upload_file`
```python
async def upload_file(self, local_path, remote_path) -> bool:
```

### Class: `AzureBlobStorageService`
**Inherits from:** BaseCloudService

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `delete_file` `async` |  |
| `download_file` `async` |  |
| `initialize` `async` |  |
| `list_files` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |
| `upload_file` `async` |  |

##### `__init__`
```python
def __init__(self, config, logger) -> None:
```

##### `delete_file`
```python
async def delete_file(self, remote_path) -> bool:
```

##### `download_file`
```python
async def download_file(self, remote_path, local_path) -> bool:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `list_files`
```python
async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

##### `upload_file`
```python
async def upload_file(self, local_path, remote_path) -> bool:
```

### Class: `BaseCloudService`
**Inherits from:** abc.ABC

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `initialize` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |

##### `__init__`
```python
def __init__(self, config, logger) -> None:
```

##### `initialize`
```python
@abc.abstractmethod
async def initialize(self) -> None:
```

##### `shutdown`
```python
@abc.abstractmethod
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

### Class: `CloudManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `delete_file` `async` |  |
| `download_file` `async` |  |
| `get_cloud_provider` |  |
| `get_service` `async` |  |
| `get_storage_backend` |  |
| `initialize` `async` |  |
| `is_cloud_provider` |  |
| `list_files` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |
| `upload_file` `async` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, file_manager) -> None:
```

##### `delete_file`
```python
async def delete_file(self, remote_path) -> bool:
```

##### `download_file`
```python
async def download_file(self, remote_path, local_path) -> bool:
```

##### `get_cloud_provider`
```python
def get_cloud_provider(self) -> str:
```

##### `get_service`
```python
async def get_service(self, service_name) -> Optional[CloudService]:
```

##### `get_storage_backend`
```python
def get_storage_backend(self) -> str:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `is_cloud_provider`
```python
def is_cloud_provider(self, provider) -> bool:
```

##### `list_files`
```python
async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

##### `upload_file`
```python
async def upload_file(self, local_path, remote_path) -> bool:
```

### Class: `CloudProvider`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `NONE` | `'none'` |
| `AWS` | `'aws'` |
| `AZURE` | `'azure'` |
| `GCP` | `'gcp'` |

### Class: `CloudService`
**Inherits from:** Protocol

#### Methods

| Method | Description |
| --- | --- |
| `initialize` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

### Class: `CloudStorageService`
**Inherits from:** Protocol

#### Methods

| Method | Description |
| --- | --- |
| `delete_file` `async` |  |
| `download_file` `async` |  |
| `list_files` `async` |  |
| `upload_file` `async` |  |

##### `delete_file`
```python
async def delete_file(self, remote_path) -> bool:
```

##### `download_file`
```python
async def download_file(self, remote_path, local_path) -> bool:
```

##### `list_files`
```python
async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
```

##### `upload_file`
```python
async def upload_file(self, local_path, remote_path) -> bool:
```

### Class: `GCPStorageService`
**Inherits from:** BaseCloudService

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `delete_file` `async` |  |
| `download_file` `async` |  |
| `initialize` `async` |  |
| `list_files` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |
| `upload_file` `async` |  |

##### `__init__`
```python
def __init__(self, config, logger) -> None:
```

##### `delete_file`
```python
async def delete_file(self, remote_path) -> bool:
```

##### `download_file`
```python
async def download_file(self, remote_path, local_path) -> bool:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `list_files`
```python
async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

##### `upload_file`
```python
async def upload_file(self, local_path, remote_path) -> bool:
```

### Class: `LocalStorageService`
**Inherits from:** BaseCloudService

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `delete_file` `async` |  |
| `download_file` `async` |  |
| `initialize` `async` |  |
| `list_files` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |
| `upload_file` `async` |  |

##### `__init__`
```python
def __init__(self, config, logger, file_manager) -> None:
```

##### `delete_file`
```python
async def delete_file(self, remote_path) -> bool:
```

##### `download_file`
```python
async def download_file(self, remote_path, local_path) -> bool:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `list_files`
```python
async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

##### `upload_file`
```python
async def upload_file(self, local_path, remote_path) -> bool:
```

### Class: `StorageBackend`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `LOCAL` | `'local'` |
| `S3` | `'s3'` |
| `AZURE_BLOB` | `'azure_blob'` |
| `GCP_STORAGE` | `'gcp_storage'` |
