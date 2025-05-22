# Module: core.remote_manager

**Path:** `core/remote_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import abc
import asyncio
import importlib
import json
import urllib.parse
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError
```

## Classes

| Class | Description |
| --- | --- |
| `HTTPService` |  |
| `RemoteService` |  |
| `RemoteServicesManager` |  |
| `ServiceProtocol` |  |

### Class: `HTTPService`
**Inherits from:** RemoteService

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `check_health` `async` |  |
| `close` `async` |  |
| `delete` `async` |  |
| `get` `async` |  |
| `get_client` `async` |  |
| `initialize_client` `async` |  |
| `patch` `async` |  |
| `post` `async` |  |
| `put` `async` |  |
| `request` `async` |  |

##### `__init__`
```python
def __init__(self, name, base_url, protocol, **kwargs) -> None:
```

##### `check_health`
```python
async def check_health(self) -> bool:
```

##### `close`
```python
async def close(self) -> None:
```

##### `delete`
```python
async def delete(self, path, **kwargs) -> httpx.Response:
```

##### `get`
```python
async def get(self, path, params, **kwargs) -> httpx.Response:
```

##### `get_client`
```python
async def get_client(self) -> httpx.AsyncClient:
```

##### `initialize_client`
```python
async def initialize_client(self) -> None:
```

##### `patch`
```python
async def patch(self, path, data, json_data, **kwargs) -> httpx.Response:
```

##### `post`
```python
async def post(self, path, data, json_data, **kwargs) -> httpx.Response:
```

##### `put`
```python
async def put(self, path, data, json_data, **kwargs) -> httpx.Response:
```

##### `request`
```python
@retry(retry=retry_if_exception_type(httpx.HTTPError), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def request(self, method, path, params, data, json_data, headers, timeout) -> httpx.Response:
```

### Class: `RemoteService`
**Inherits from:** abc.ABC

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `check_health` `async` |  |
| `get_client` `async` |  |
| `initialize_client` `async` |  |
| `status` `async` |  |
| `update_metrics` `async` |  |

##### `__init__`
```python
def __init__(self, name, protocol, base_url, timeout, max_retries, retry_delay, retry_max_delay, headers, auth, config, logger) -> None:
```

##### `check_health`
```python
@abc.abstractmethod
async def check_health(self) -> bool:
```

##### `get_client`
```python
@abc.abstractmethod
async def get_client(self) -> Any:
```

##### `initialize_client`
```python
@abc.abstractmethod
async def initialize_client(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

##### `update_metrics`
```python
async def update_metrics(self, response_time, success) -> None:
```

### Class: `RemoteServicesManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `check_all_services_health` `async` |  |
| `check_service_health` `async` |  |
| `get_all_services` `async` |  |
| `get_http_service` `async` |  |
| `get_service` `async` |  |
| `initialize` `async` |  |
| `make_request` `async` |  |
| `register_service` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |
| `unregister_service` `async` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, event_bus_manager, task_manager) -> None:
```

##### `check_all_services_health`
```python
async def check_all_services_health(self) -> Dict[(str, bool)]:
```

##### `check_service_health`
```python
async def check_service_health(self, service_name) -> bool:
```

##### `get_all_services`
```python
async def get_all_services(self) -> Dict[(str, RemoteService)]:
```

##### `get_http_service`
```python
async def get_http_service(self, service_name) -> Optional[HTTPService]:
```

##### `get_service`
```python
async def get_service(self, service_name) -> Optional[RemoteService]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `make_request`
```python
async def make_request(self, service_name, method, path, **kwargs) -> Any:
```

##### `register_service`
```python
async def register_service(self, service) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

##### `unregister_service`
```python
async def unregister_service(self, service_name) -> bool:
```

### Class: `ServiceProtocol`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `HTTP` | `'http'` |
| `HTTPS` | `'https'` |
| `GRPC` | `'grpc'` |
| `SOAP` | `'soap'` |
| `CUSTOM` | `'custom'` |
