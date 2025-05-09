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
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, cast
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
Field =     Field = lambda *args, **kwargs: None  # noqa
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
| `initialize` |  |
| `register_api_endpoint` |  |
| `shutdown` |  |
| `status` |  |

##### `__init__`
```python
def __init__(self, config_manager, logger_manager, security_manager, event_bus_manager, thread_manager, registry) -> None:
```

##### `initialize`
```python
def initialize(self) -> None:
```

##### `register_api_endpoint`
```python
def register_api_endpoint(self, path, method, endpoint, tags, response_model, dependencies, summary, description) -> bool:
```

##### `shutdown`
```python
def shutdown(self) -> None:
```

##### `status`
```python
def status(self) -> Dict[(str, Any)]:
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
