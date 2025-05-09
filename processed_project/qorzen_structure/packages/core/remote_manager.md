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
import threading
import time
import urllib.parse
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from qorzen.core.base import QorzenManager
from qorzen.core.thread_manager import TaskProgressReporter
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError
```

## Classes

| Class | Description |
| --- | --- |
| `AsyncHTTPService` |  |
| `HTTPService` |  |
| `RemoteService` |  |
| `RemoteServicesManager` |  |
| `ServiceProtocol` |  |

### Class: `AsyncHTTPService`
**Inherits from:** RemoteService

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `check_health` |  |
| `check_health_async` `async` |  |
| `close` |  |
| `close_async` `async` |  |
| `delete` `async` |  |
| `get` `async` |  |
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
def check_health(self) -> bool:
```

##### `check_health_async`
```python
async def check_health_async(self) -> bool:
```

##### `close`
```python
def close(self) -> None:
```

##### `close_async`
```python
async def close_async(self) -> None:
```

##### `delete`
```python
async def delete(self, path, **kwargs) -> httpx.Response:
```

##### `get`
```python
async def get(self, path, params, **kwargs) -> httpx.Response:
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

### Class: `HTTPService`
**Inherits from:** RemoteService

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `check_health` |  |
| `close` |  |
| `delete` |  |
| `get` |  |
| `patch` |  |
| `post` |  |
| `put` |  |
| `request` |  |

##### `__init__`
```python
def __init__(self, name, base_url, protocol, **kwargs) -> None:
```

##### `check_health`
```python
def check_health(self) -> bool:
```

##### `close`
```python
def close(self) -> None:
```

##### `delete`
```python
def delete(self, path, **kwargs) -> httpx.Response:
```

##### `get`
```python
def get(self, path, params, **kwargs) -> httpx.Response:
```

##### `patch`
```python
def patch(self, path, data, json_data, **kwargs) -> httpx.Response:
```

##### `post`
```python
def post(self, path, data, json_data, **kwargs) -> httpx.Response:
```

##### `put`
```python
def put(self, path, data, json_data, **kwargs) -> httpx.Response:
```

##### `request`
```python
@retry(retry=retry_if_exception_type(httpx.HTTPError), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def request(self, method, path, params, data, json_data, headers, timeout) -> httpx.Response:
```

### Class: `RemoteService`

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `check_health` |  |
| `get_client` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self, name, protocol, base_url, timeout, max_retries, retry_delay, retry_max_delay, headers, auth, config, logger) -> None:
```

##### `check_health`
```python
def check_health(self) -> bool:
```

##### `get_client`
```python
def get_client(self) -> Any:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

### Class: `RemoteServicesManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `check_all_services_health` |  |
| `check_service_health` |  |
| `get_all_services` |  |
| `get_async_http_service` |  |
| `get_http_service` |  |
| `get_service` |  |
| `initialize` |  |
| `make_request` |  |
| `make_request_async` `async` |  |
| `register_service` |  |
| `shutdown` |  |
| `status` |  |
| `unregister_service` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, event_bus_manager, thread_manager) -> None:
```

##### `check_all_services_health`
```python
def check_all_services_health(self) -> Dict[(str, bool)]:
```

##### `check_service_health`
```python
def check_service_health(self, service_name) -> bool:
```

##### `get_all_services`
```python
def get_all_services(self) -> Dict[(str, RemoteService)]:
```

##### `get_async_http_service`
```python
def get_async_http_service(self, service_name) -> Optional[AsyncHTTPService]:
```

##### `get_http_service`
```python
def get_http_service(self, service_name) -> Optional[HTTPService]:
```

##### `get_service`
```python
def get_service(self, service_name) -> Optional[RemoteService]:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `make_request`
```python
def make_request(self, service_name, method, path, **kwargs) -> Any:
```

##### `make_request_async`
```python
async def make_request_async(self, service_name, method, path, **kwargs) -> Any:
```

##### `register_service`
```python
def register_service(self, service) -> None:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
```

##### `unregister_service`
```python
def unregister_service(self, service_name) -> bool:
```

### Class: `ServiceProtocol`
**Inherits from:** Enum

#### Attributes

| Name | Value |
| --- | --- |
| `HTTP` | `'http'` |
| `HTTPS` | `'https'` |
| `GRPC` | `'grpc'` |
| `SOAP` | `'soap'` |
| `CUSTOM` | `'custom'` |
