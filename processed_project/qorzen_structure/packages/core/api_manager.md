# Module: core.api_manager

**Path:** `core/api_manager.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import asyncio
import inspect
import os
import sys
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, cast, Awaitable
import fastapi
import pydantic
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import APIError, ManagerInitializationError, ManagerShutdownError
```

## Global Variables
```python
fastapi = None
FastAPI =     FastAPI = object
APIRouter =     APIRouter = object
BaseModel =     BaseModel = object
Field =     Field = lambda *args, **kwargs: None  # noqa: E731
```

## Classes

| Class | Description |
| --- | --- |
| `APIManager` |  |
| `AlertResponse` |  |
| `PluginResponse` |  |
| `StatusResponse` |  |
| `Token` |  |
| `TokenData` |  |
| `UserCreate` |  |
| `UserLogin` |  |
| `UserResponse` |  |
| `UserUpdate` |  |

### Class: `APIManager`
**Inherits from:** QorzenManager

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `initialize` `async` |  |
| `register_api_endpoint` `async` |  |
| `shutdown` `async` |  |
| `status` `async` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, security_manager, event_bus_manager, concurrency_manager, registry) -> None:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `register_api_endpoint`
```python
async def register_api_endpoint(self, path, method, endpoint, tags, response_model, dependencies, summary, description) -> bool:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

##### `status`
```python
async def status(self) -> Dict[(str, Any)]:
```

### Class: `AlertResponse`
**Inherits from:** BaseModel

### Class: `PluginResponse`
**Inherits from:** BaseModel

### Class: `StatusResponse`
**Inherits from:** BaseModel

### Class: `Token`
**Inherits from:** BaseModel

### Class: `TokenData`
**Inherits from:** BaseModel

### Class: `UserCreate`
**Inherits from:** BaseModel

### Class: `UserLogin`
**Inherits from:** BaseModel

### Class: `UserResponse`
**Inherits from:** BaseModel

### Class: `UserUpdate`
**Inherits from:** BaseModel
