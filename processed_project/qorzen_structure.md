# qorzen Project Structure
Generated on 2025-05-17 15:18:47

## Table of Contents
1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Packages and Modules](#packages-and-modules)

## Project Overview
- Project Name: qorzen
- Root Path: /home/runner/work/qorzen/qorzen/qorzen
- Packages: 6
- Top-level Modules: 6

## Directory Structure
```
qorzen/
├── core/
│   ├── __init__.py
│   ├── api_manager.py
│   ├── app.py
│   ├── base.py
│   ├── cloud_manager.py
│   ├── concurrency_manager.py
│   ├── config_manager.py
│   ├── database_manager.py
│   ├── dependency_manager.py
│   ├── error_handler.py
│   ├── event_bus_manager.py
│   ├── event_model.py
│   ├── file_manager.py
│   ├── logging_manager.py
│   ├── plugin_isolation_manager.py
│   ├── plugin_manager.py
│   ├── remote_manager.py
│   ├── resource_monitoring_manager.py
│   ├── security_manager.py
│   └── task_manager.py
├── models/
│   ├── __init__.py
│   ├── audit.py
│   ├── base.py
│   ├── plugin.py
│   ├── system.py
│   └── user.py
├── plugin_system/
│   ├── __init__.py
│   ├── cli.py
│   ├── config_schema.py
│   ├── dependency.py
│   ├── extension.py
│   ├── installer.py
│   ├── integration.py
│   ├── interface.py
│   ├── lifecycle.py
│   ├── manifest.py
│   ├── package.py
│   ├── plugin_state_manager.py
│   ├── repository.py
│   ├── signing.py
│   ├── tools.py
│   └── ui_registry.py
├── plugins/
│   ├── application_launcher/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   ├── events.py
│   │   │   ├── plugin.py
│   │   │   ├── presets.py
│   │   │   └── process_utils.py
│   │   ├── __init__.py
│   │   └── manifest.json
│   ├── as400_connector_plugin/
│   │   ├── code/
│   │   │   ├── ui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── as400_tab.py
│   │   │   │   ├── connection_dialog.py
│   │   │   │   ├── query_editor.py
│   │   │   │   ├── results_view.py
│   │   │   │   └── visualization.py
│   │   │   ├── __init__.py
│   │   │   ├── connector.py
│   │   │   ├── models.py
│   │   │   ├── plugin.py
│   │   │   └── utils.py
│   │   ├── queries/
│   │   │   ├── account_sales.sql
│   │   │   ├── popularity_codes.sql
│   │   │   └── table_descriptions.sql
│   │   └── __init__.py
│   ├── database_connector_plugin/
│   │   ├── code/
│   │   │   ├── connectors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── as400.py
│   │   │   │   ├── base.py
│   │   │   │   └── odbc.py
│   │   │   ├── ui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connection_dialog.py
│   │   │   │   ├── main_tab.py
│   │   │   │   ├── mapping_dialog.py
│   │   │   │   ├── query_editor.py
│   │   │   │   └── results_view.py
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── history.py
│   │   │   │   ├── mapping.py
│   │   │   │   └── validation.py
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   └── plugin.py
│   │   ├── __init__.py
│   │   └── manifest.json
│   ├── sample_async_plugin/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   └── plugin.py
│   │   ├── __init__.py
│   │   └── manifest.json
│   ├── vcdb_explorer/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   ├── data_table.py
│   │   │   ├── database_handler.py
│   │   │   ├── events.py
│   │   │   ├── export.py
│   │   │   ├── filter_panel.py
│   │   │   ├── models.py
│   │   │   └── plugin.py
│   │   ├── resources/
│   │   │   ├── ui_icons/
│   │   │   │   ├── database-search.svg
│   │   │   │   ├── database.svg
│   │   │   │   └── library-books.svg
│   │   │   ├── initialdb.ico
│   │   │   ├── initialdb.png
│   │   │   ├── initialdb_1000.png
│   │   │   ├── logo.png
│   │   │   └── splash.png
│   │   ├── README.md
│   │   ├── __init__.py
│   │   └── manifest.json
│   └── __init__.py
├── ui/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── logs.py
│   ├── main_window.py
│   ├── plugins.py
│   ├── task_monitor.py
│   ├── thread_safe_signaler.py
│   ├── ui_component.py
│   └── ui_integration.py
├── utils/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── qt_thread_debug.py
│   └── qtasync.py
├── __init__.py
├── __main__.py
├── __version__.py
├── main.py
├── plugin_debug.py
└── resources_rc.py
```

## Packages and Modules
### Top-level Modules
### Module: __init__
*Qorzen - A modular platform for the automotive aftermarket industry.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/__init__.py`

**Imports:**
```python
from qorzen.__version__ import __version__
from qorzen.core.app import ApplicationCore
```

### Module: __main__
*Entry point for the Qorzen application.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/__main__.py`

**Imports:**
```python
import sys
from qorzen.main import main
```

### Module: __version__
*Version information.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/__version__.py`

**Global Variables:**
```python
__version__ = '0.1.0'
```

### Module: main
Path: `/home/runner/work/qorzen/qorzen/qorzen/main.py`

**Imports:**
```python
from __future__ import annotations
import argparse
import asyncio
import importlib
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast
```

**Functions:**
```python
async def handle_build_command(args) -> int:
```

```python
def main() -> int:
```

```python
async def main_async() -> int:
```

```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
```

```python
async def run_headless(args) -> int:
```

```python
async def setup_environment() -> None:
    """Set up the Python environment for Qorzen."""
```

```python
async def start_ui(args) -> int:
```

### Module: plugin_debug
*Debug script to find out why plugins are unloading.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_debug.py`

**Imports:**
```python
import sys
import inspect
import logging
import traceback
from pathlib import Path
```

**Global Variables:**
```python
logger = logger = logging.getLogger("plugin_debugger")
operations = operations = []
```

**Functions:**
```python
def hook_lifecycle():
    """Hook into the lifecycle manager"""
```

```python
def hook_plugin_manager():
    """Hook into the plugin manager to track operations"""
```

```python
def hook_state_manager():
    """Hook into the state manager"""
```

```python
def log_operation(op_type, **kwargs):
    """Log an operation with its stack trace"""
```

### Module: resources_rc
Path: `/home/runner/work/qorzen/qorzen/qorzen/resources_rc.py`

**Imports:**
```python
from PySide6 import QtCore
```

**Global Variables:**
```python
qt_resource_data = b'\x00\x00\x01g<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M520-600v-240h320v240H520ZM120-440v-400h320v400H120Zm400 320v-400h320v400H520Zm-400 0v-240h320v240H120Zm80-400h160v-240H200v240Zm400 320h160v-240H600v240Zm0-480h160v-80H600v80ZM200-200h160v-80H200v80Zm160-320Zm240-160Zm0 240ZM360-280Z"/></svg>\x00\x00\x03\xe0<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M472-120q-73-1-137.5-13.5t-112-34Q175-189 147.5-218T120-280q0 33 27.5 62t75 50.5q47.5 21.5 112 34T472-120Zm-71-204q-30-3-58-8t-53.5-12q-25.5-7-48-15.5T200-379q19 11 41.5 19.5t48 15.5q25.5 7 53.5 12t58 8Zm79-275q86 0 177.5-26T760-679q-11-29-100.5-55T480-760q-91 0-178.5 25.5T200-679q15 29 104.5 54.5T480-599Zm-61 396q10 23 23 44t30 39q-73-1-137.5-13.5t-112-34Q175-189 147.5-218T120-280v-400q0-33 28.5-62t77.5-51q49-22 114.5-34.5T480-840q74 0 139.5 12.5T734-793q49 22 77.5 51t28.5 62q0 33-28.5 62T734-567q-49 22-114.5 34.5T480-520q-85 0-157-15t-123-44v101q40 37 100 54t121 22q-8 15-13 34.5t-7 43.5q-60-7-111.5-20T200-379v99q14 25 77 47t142 30ZM864-40 756-148q-22 13-46 20.5t-50 7.5q-75 0-127.5-52.5T480-300q0-75 52.5-127.5T660-480q75 0 127.5 52.5T840-300q0 26-7.5 50T812-204L920-96l-56 56ZM660-200q42 0 71-29t29-71q0-42-29-71t-71-29q-42 0-71 29t-29 71q0 42 29 71t71 29Z"/></svg>\x00\x00\x01\x96<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M400-400h160v-80H400v80Zm0-120h320v-80H400v80Zm0-120h320v-80H400v80Zm-80 400q-33 0-56.5-23.5T240-320v-480q0-33 23.5-56.5T320-880h480q33 0 56.5 23.5T880-800v480q0 33-23.5 56.5T800-240H320Zm0-80h480v-480H320v480ZM160-80q-33 0-56.5-23.5T80-160v-560h80v560h560v80H160Zm160-720v480-480Z"/></svg>\x00\x00\x02b<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M352-120H200q-33 0-56.5-23.5T120-200v-152q48 0 84-30.5t36-77.5q0-47-36-77.5T120-568v-152q0-33 23.5-56.5T200-800h160q0-42 29-71t71-29q42 0 71 29t29 71h160q33 0 56.5 23.5T800-720v160q42 0 71 29t29 71q0 42-29 71t-71 29v160q0 33-23.5 56.5T720-120H568q0-50-31.5-85T460-240q-45 0-76.5 35T352-120Zm-152-80h85q24-66 77-93t98-27q45 0 98 27t77 93h85v-240h80q8 0 14-6t6-14q0-8-6-14t-14-6h-80v-240H480v-80q0-8-6-14t-14-6q-8 0-14 6t-6 14v80H200v88q54 20 87 67t33 105q0 57-33 104t-87 68v88Zm260-260Z"/></svg>\x00\x00\x02\xd9<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M480-120q-151 0-255.5-46.5T120-280v-400q0-66 105.5-113T480-840q149 0 254.5 47T840-680v400q0 67-104.5 113.5T480-120Zm0-479q89 0 179-25.5T760-679q-11-29-100.5-55T480-760q-91 0-178.5 25.5T200-679q14 30 101.5 55T480-599Zm0 199q42 0 81-4t74.5-11.5q35.5-7.5 67-18.5t57.5-25v-120q-26 14-57.5 25t-67 18.5Q600-528 561-524t-81 4q-42 0-82-4t-75.5-11.5Q287-543 256-554t-56-25v120q25 14 56 25t66.5 18.5Q358-408 398-404t82 4Zm0 200q46 0 93.5-7t87.5-18.5q40-11.5 67-26t32-29.5v-98q-26 14-57.5 25t-67 18.5Q600-328 561-324t-81 4q-42 0-82-4t-75.5-11.5Q287-343 256-354t-56-25v99q5 15 31.5 29t66.5 25.5q40 11.5 88 18.5t94 7Z"/></svg>\x00\x00\x00\xd5<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="m136-240-56-56 296-298 160 160 208-206H640v-80h240v240h-80v-104L536-320 376-480 136-240Z"/></svg>'
qt_resource_name = b"\x00\x08\x0f_\xad3\x00u\x00i\x00_\x00i\x00c\x00o\x00n\x00s\x00\r\r\x94\x89\xc7\x00d\x00a\x00s\x00h\x00b\x00o\x00a\x00r\x00d\x00.\x00s\x00v\x00g\x00\x13\x01\xbb\x8c\xa7\x00d\x00a\x00t\x00a\x00b\x00a\x00s\x00e\x00-\x00s\x00e\x00a\x00r\x00c\x00h\x00.\x00s\x00v\x00g\x00\x11\x07)\xce'\x00l\x00i\x00b\x00r\x00a\x00r\x00y\x00-\x00b\x00o\x00o\x00k\x00s\x00.\x00s\x00v\x00g\x00\r\t\xd4\xd0G\x00e\x00x\x00t\x00e\x00n\x00s\x00i\x00o\x00n\x00.\x00s\x00v\x00g\x00\x0c\x05\xc9\x15\xc7\x00d\x00a\x00t\x00a\x00b\x00a\x00s\x00e\x00.\x00s\x00v\x00g\x00\x0f\x0cW=\xa7\x00t\x00r\x00e\x00n\x00d\x00i\x00n\x00g\x00-\x00u\x00p\x00.\x00s\x00v\x00g"
qt_resource_struct = b'\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x06\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x006\x00\x00\x00\x00\x00\x01\x00\x00\x01k\x00\x00\x01\x96\x9bo*`\x00\x00\x00\xaa\x00\x00\x00\x00\x00\x01\x00\x00\tO\x00\x00\x01\x96\x9bm\xdap\x00\x00\x00b\x00\x00\x00\x00\x00\x01\x00\x00\x05O\x00\x00\x01\x96\x9btq\xf0\x00\x00\x00\x8a\x00\x00\x00\x00\x00\x01\x00\x00\x06\xe9\x00\x00\x01\x96\xb5\xbd<@\x00\x00\x00\xc8\x00\x00\x00\x00\x00\x01\x00\x00\x0c,\x00\x00\x01\x96\xd0Y\x85\x90\x00\x00\x00\x16\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x01\x96\xb5\xa50\x00'
```

**Functions:**
```python
def qCleanupResources():
```

```python
def qInitResources():
```


### Packages
### Package: core
Path: `/home/runner/work/qorzen/qorzen/qorzen/core`

**__init__.py:**
*Core package containing the essential managers and components.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/__init__.py`

**Imports:**
```python
from qorzen.core.base import BaseManager, QorzenManager
from qorzen.core.dependency_manager import DependencyManager
from qorzen.core.cloud_manager import CloudManager
from qorzen.core.config_manager import ConfigManager
from qorzen.core.database_manager import Base, DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.file_manager import FileManager
from qorzen.core.api_manager import APIManager
from qorzen.core.logging_manager import LoggingManager
from qorzen.core.resource_monitoring_manager import ResourceMonitoringManager
from qorzen.core.plugin_manager import PluginManager
from qorzen.core.plugin_isolation_manager import PluginIsolationManager
from qorzen.core.remote_manager import RemoteServicesManager
from qorzen.core.security_manager import SecurityManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.task_manager import TaskManager
```

#### Module: api_manager
*Asynchronous API Manager for handling REST API endpoints.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/api_manager.py`

**Imports:**
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

**Global Variables:**
```python
fastapi = None
FastAPI =     FastAPI = object
APIRouter =     APIRouter = object
BaseModel =     BaseModel = object
Field =     Field = lambda *args, **kwargs: None  # noqa: E731
```

**Classes:**
```python
class APIManager(QorzenManager):
    """Manager for handling REST API endpoints."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, security_manager, event_bus_manager, concurrency_manager, registry) -> None:
        """Initialize the API manager.

Args: config_manager: Configuration manager instance logger_manager: Logger manager instance security_manager: Security manager instance event_bus_manager: Event bus manager instance concurrency_manager: Concurrency manager instance registry: Optional registry of additional services"""
```
```python
    async def initialize(self) -> None:
        """Initialize the API manager."""
```
```python
    async def register_api_endpoint(self, path, method, endpoint, tags, response_model, dependencies, summary, description) -> bool:
        """Register a custom API endpoint.

Args: path: Endpoint path method: HTTP method endpoint: Endpoint handler function tags: OpenAPI tags response_model: Pydantic response model dependencies: FastAPI dependencies summary: Endpoint summary description: Endpoint description

Returns: True if registered successfully, False otherwise"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the API manager."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """Get the status of the API manager.  Returns: Dict containing status information"""
```

```python
class AlertResponse(BaseModel):
    """Model for alert response."""
```

```python
class PluginResponse(BaseModel):
    """Model for plugin response."""
```

```python
class StatusResponse(BaseModel):
    """Model for system status response."""
```

```python
class Token(BaseModel):
    """Model for authentication token response."""
```

```python
class TokenData(BaseModel):
    """Model for token data."""
```

```python
class UserCreate(BaseModel):
    """Model for creating a new user."""
```

```python
class UserLogin(BaseModel):
    """Model for user login request."""
```

```python
class UserResponse(BaseModel):
    """Model for user response."""
```

```python
class UserUpdate(BaseModel):
    """Model for updating a user."""
```

#### Module: app
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/app.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import importlib
import inspect
import logging
import os
import signal
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, cast, T
from qorzen.core.base import QorzenManager, BaseManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.dependency_manager import DependencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory
from qorzen.core.plugin_isolation_manager import PluginIsolationManager, PluginIsolationLevel
from qorzen.utils.exceptions import ApplicationError
```

**Classes:**
```python
class ApplicationCore(object):
    """The main application core with async support.

Manages the lifecycle of all core components and provides a clean architecture for plugin integration."""
```
*Methods:*
```python
    def __init__(self, config_path) -> None:
        """Initialize the application core.  Args: config_path: Optional path to configuration file"""
```
```python
    def get_manager(self, name) -> Optional[BaseManager]:
        """Get a manager by name.  Args: name: Name of the manager  Returns: The manager or None if not found"""
```
```python
    def get_manager_typed(self, name, manager_type) -> Optional[T]:
        """Get a manager by name with type checking.

Args: name: Name of the manager manager_type: Type of the manager

Returns: The manager or None if not found"""
```
```python
    def get_ui_integration(self) -> Any:
        """Get the UI integration.  Returns: The UI integration object"""
```
```python
    async def initialize(self, progress_callback) -> None:
        """Initialize the application core asynchronously.

Args: progress_callback: Optional callback for initialization progress

Raises: ApplicationError: If initialization fails"""
```
```python
    def is_initialized(self) -> bool:
        """Check if the application is initialized.  Returns: True if initialized, False otherwise"""
```
```python
    def set_ui_integration(self, ui_integration) -> None:
        """Set the UI integration.  Args: ui_integration: UI integration object"""
```
```python
    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the application core.

Shuts down all managers in reverse dependency order.

Raises: ApplicationError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the application status.  Returns: Status dictionary"""
```
```python
    async def status_async(self) -> Dict[(str, Any)]:
        """Asynchronously collect all managers’ statuses, awaiting where needed."""
```
```python
    async def submit_core_task(self, func, name, *args, **kwargs) -> str:
        """Submit a core task for execution.

Args: func: Function to execute *args: Positional arguments name: Task name **kwargs: Keyword arguments

Returns: Task ID

Raises: ApplicationError: If task submission fails"""
```
```python
    async def wait_for_shutdown(self) -> None:
        """Wait for the application to shut down."""
```

#### Module: base
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/base.py`

**Imports:**
```python
from __future__ import annotations
import abc
import asyncio
import logging
from typing import Any, Dict, Optional, Protocol, TypeVar, runtime_checkable
```

**Global Variables:**
```python
T = T = TypeVar('T', bound='AsyncBaseManager')
```

**Classes:**
```python
@runtime_checkable
class BaseManager(Protocol):
    """Protocol defining basic async manager functionality."""
```
*Methods:*
```python
    async def initialize(self) -> None:
        """Initialize the manager asynchronously."""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the manager asynchronously."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Return the current status of the manager."""
```

```python
class QorzenManager(abc.ABC):
    """Base class for asynchronous managers in the Qorzen framework."""
```
*Methods:*
```python
    def __init__(self, name) -> None:
        """Initialize the async manager with a name.  Args: name: The name of the manager"""
```
```python
@property
    def healthy(self) -> bool:
        """Check if the manager is healthy."""
```
```python
@abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the manager asynchronously.

This method should be implemented by subclasses to perform initialization tasks like loading configuration, setting up connections, etc.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
@property
    def initialized(self) -> bool:
        """Check if the manager is initialized."""
```
```python
@property
    def name(self) -> str:
        """Get the manager's name."""
```
```python
    def set_logger(self, logger) -> None:
        """Set the logger for this manager.  Args: logger: Logger instance to use"""
```
```python
@abc.abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the manager asynchronously.

This method should be implemented by subclasses to perform cleanup tasks like closing connections, releasing resources, etc.

Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the current status of the manager.  Returns: Dictionary containing status information"""
```

#### Module: cloud_manager
*Asynchronous Cloud Manager for handling cloud storage services.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/cloud_manager.py`

**Imports:**
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

**Global Variables:**
```python
T = T = TypeVar('T')
```

**Classes:**
```python
class AWSStorageService(BaseCloudService):
    """Storage service that uses AWS S3."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """
        Initialize the AWS S3 storage service.

        Args:
            config: Service configuration dictionary
            logger: Logger instance
        """
```
```python
    async def delete_file(self, remote_path) -> bool:
        """
        Delete a file from AWS S3.

        Args:
            remote_path: Path to the file in S3

        Returns:
            True if successful, False otherwise
        """
```
```python
    async def download_file(self, remote_path, local_path) -> bool:
        """
        Download a file from AWS S3.

        Args:
            remote_path: Path to the file in S3
            local_path: Destination path on local filesystem

        Returns:
            True if successful, False otherwise
        """
```
```python
    async def initialize(self) -> None:
        """Initialize the AWS S3 storage service."""
```
```python
    async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """
        List files in AWS S3.

        Args:
            remote_path: Directory path in S3 to list

        Returns:
            List of file information dictionaries
        """
```
```python
    async def shutdown(self) -> None:
        """Shutdown the AWS S3 storage service."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """
        Get the storage service status.

        Returns:
            Dict containing service status information
        """
```
```python
    async def upload_file(self, local_path, remote_path) -> bool:
        """
        Upload a file to AWS S3.

        Args:
            local_path: Path to the local file
            remote_path: Destination path in S3

        Returns:
            True if successful, False otherwise
        """
```

```python
class AzureBlobStorageService(BaseCloudService):
    """Storage service that uses Azure Blob Storage."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """
        Initialize the Azure Blob Storage service.

        Args:
            config: Service configuration dictionary
            logger: Logger instance
        """
```
```python
    async def delete_file(self, remote_path) -> bool:
        """
        Delete a file from Azure Blob Storage.

        Args:
            remote_path: Path to the blob in storage

        Returns:
            True if successful, False otherwise
        """
```
```python
    async def download_file(self, remote_path, local_path) -> bool:
        """
        Download a file from Azure Blob Storage.

        Args:
            remote_path: Path to the blob in storage
            local_path: Destination path on local filesystem

        Returns:
            True if successful, False otherwise
        """
```
```python
    async def initialize(self) -> None:
        """Initialize the Azure Blob Storage service."""
```
```python
    async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """
        List files in Azure Blob Storage.

        Args:
            remote_path: Directory path in storage to list

        Returns:
            List of file information dictionaries
        """
```
```python
    async def shutdown(self) -> None:
        """Shutdown the Azure Blob Storage service."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """
        Get the storage service status.

        Returns:
            Dict containing service status information
        """
```
```python
    async def upload_file(self, local_path, remote_path) -> bool:
        """
        Upload a file to Azure Blob Storage.

        Args:
            local_path: Path to the local file
            remote_path: Destination path in blob storage

        Returns:
            True if successful, False otherwise
        """
```

```python
class BaseCloudService(abc.ABC):
    """Base abstract class for cloud services."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """
        Initialize the base cloud service.

        Args:
            config: Service configuration dictionary
            logger: Logger instance
        """
```
```python
@abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the cloud service."""
```
```python
@abc.abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the cloud service."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """
        Get the status of the cloud service.

        Returns:
            Dict containing service status information
        """
```

```python
class CloudManager(QorzenManager):
    """Manager for cloud storage services."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, file_manager) -> None:
        """
        Initialize the cloud manager.

        Args:
            config_manager: Configuration manager instance
            logger_manager: Logger manager instance
            file_manager: Optional file manager instance
        """
```
```python
    async def delete_file(self, remote_path) -> bool:
        """
        Delete a file from cloud storage.

        Args:
            remote_path: Path to the file in cloud storage

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If cloud manager not initialized or storage not enabled
        """
```
```python
    async def download_file(self, remote_path, local_path) -> bool:
        """
        Download a file from cloud storage.

        Args:
            remote_path: Path to the file in cloud storage
            local_path: Destination path on local filesystem

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If cloud manager not initialized or storage not enabled
        """
```
```python
    def get_cloud_provider(self) -> str:
        """
        Get the current cloud provider.

        Returns:
            Cloud provider string
        """
```
```python
    async def get_service(self, service_name) -> Optional[CloudService]:
        """
        Get a cloud service by name.

        Args:
            service_name: Name of the service

        Returns:
            CloudService instance or None if not found
        """
```
```python
    def get_storage_backend(self) -> str:
        """
        Get the current storage backend.

        Returns:
            Storage backend string
        """
```
```python
    async def initialize(self) -> None:
        """Initialize the cloud manager."""
```
```python
    def is_cloud_provider(self, provider) -> bool:
        """
        Check if the current cloud provider matches the specified provider.

        Args:
            provider: Provider to check against

        Returns:
            True if match, False otherwise
        """
```
```python
    async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """
        List files in cloud storage.

        Args:
            remote_path: Directory path in cloud storage to list

        Returns:
            List of file information dictionaries

        Raises:
            ValueError: If cloud manager not initialized or storage not enabled
        """
```
```python
    async def shutdown(self) -> None:
        """Shutdown the cloud manager."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """
        Get the status of the cloud manager.

        Returns:
            Dict containing status information
        """
```
```python
    async def upload_file(self, local_path, remote_path) -> bool:
        """
        Upload a file to cloud storage.

        Args:
            local_path: Path to the local file
            remote_path: Destination path in cloud storage

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If cloud manager not initialized or storage not enabled
        """
```

```python
class CloudProvider(str, Enum):
    """Supported cloud service providers."""
```
*Class attributes:*
```python
NONE = 'none'
AWS = 'aws'
AZURE = 'azure'
GCP = 'gcp'
```

```python
class CloudService(Protocol):
    """Protocol defining the interface for cloud services."""
```
*Methods:*
```python
    async def initialize(self) -> None:
        """Ellipsis"""
```
```python
    async def shutdown(self) -> None:
        """Ellipsis"""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """Ellipsis"""
```

```python
class CloudStorageService(Protocol):
    """Protocol defining the interface for cloud storage services."""
```
*Methods:*
```python
    async def delete_file(self, remote_path) -> bool:
        """Ellipsis"""
```
```python
    async def download_file(self, remote_path, local_path) -> bool:
        """Ellipsis"""
```
```python
    async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """Ellipsis"""
```
```python
    async def upload_file(self, local_path, remote_path) -> bool:
        """Ellipsis"""
```

```python
class GCPStorageService(BaseCloudService):
    """Storage service that uses Google Cloud Storage."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """
        Initialize the GCP Storage service.

        Args:
            config: Service configuration dictionary
            logger: Logger instance
        """
```
```python
    async def delete_file(self, remote_path) -> bool:
        """
        Delete a file from GCP Storage.

        Args:
            remote_path: Path to the blob in storage

        Returns:
            True if successful, False otherwise
        """
```
```python
    async def download_file(self, remote_path, local_path) -> bool:
        """
        Download a file from GCP Storage.

        Args:
            remote_path: Path to the blob in storage
            local_path: Destination path on local filesystem

        Returns:
            True if successful, False otherwise
        """
```
```python
    async def initialize(self) -> None:
        """Initialize the GCP Storage service."""
```
```python
    async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """
        List files in GCP Storage.

        Args:
            remote_path: Directory path in storage to list

        Returns:
            List of file information dictionaries
        """
```
```python
    async def shutdown(self) -> None:
        """Shutdown the GCP Storage service."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """
        Get the storage service status.

        Returns:
            Dict containing service status information
        """
```
```python
    async def upload_file(self, local_path, remote_path) -> bool:
        """
        Upload a file to GCP Storage.

        Args:
            local_path: Path to the local file
            remote_path: Destination path in storage

        Returns:
            True if successful, False otherwise
        """
```

```python
class LocalStorageService(BaseCloudService):
    """Storage service that uses the local filesystem."""
```
*Methods:*
```python
    def __init__(self, config, logger, file_manager) -> None:
        """
        Initialize the local storage service.

        Args:
            config: Service configuration dictionary
            logger: Logger instance
            file_manager: File manager instance
        """
```
```python
    async def delete_file(self, remote_path) -> bool:
        """
        Delete a file from the local storage.

        Args:
            remote_path: Path to the file in storage

        Returns:
            True if successful, False otherwise
        """
```
```python
    async def download_file(self, remote_path, local_path) -> bool:
        """
        Download a file from the local storage.

        Args:
            remote_path: Path to the file in storage
            local_path: Destination path on local filesystem

        Returns:
            True if successful, False otherwise
        """
```
```python
    async def initialize(self) -> None:
        """Initialize the local storage service."""
```
```python
    async def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """
        List files in the local storage.

        Args:
            remote_path: Directory path in storage to list

        Returns:
            List of file information dictionaries
        """
```
```python
    async def shutdown(self) -> None:
        """Shutdown the local storage service."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """
        Get the storage service status.

        Returns:
            Dict containing service status information
        """
```
```python
    async def upload_file(self, local_path, remote_path) -> bool:
        """
        Upload a file to the local storage.

        Args:
            local_path: Path to the local file
            remote_path: Destination path in storage

        Returns:
            True if successful, False otherwise
        """
```

```python
class StorageBackend(str, Enum):
    """Supported storage backend types."""
```
*Class attributes:*
```python
LOCAL = 'local'
S3 = 's3'
AZURE_BLOB = 'azure_blob'
GCP_STORAGE = 'gcp_storage'
```

#### Module: concurrency_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/concurrency_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import concurrent.futures
import functools
import logging
import os
import threading
import traceback
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, ThreadManagerError
```

**Global Variables:**
```python
T = T = TypeVar('T')
R = R = TypeVar('R')
```

**Classes:**
```python
class ConcurrencyManager(QorzenManager):
    """Manager for hybrid concurrency (async + threads).

This manager provides a unified interface for running tasks using both async/await and thread-based concurrency."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager) -> None:
        """Initialize the concurrency manager.

Args: config_manager: Configuration manager logger_manager: Logger manager"""
```
```python
    async def initialize(self) -> None:
        """Initialize the concurrency manager.

Sets up thread pools and process pools based on configuration.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    def is_main_thread(self) -> bool:
        """Check if the current thread is the main thread.

Returns: True if the current thread is the main thread, False otherwise"""
```
```python
    async def run_in_process(self, func, *args, **kwargs) -> T:
        """Run a function in a separate process.

This is suitable for CPU-intensive tasks that can be parallelized.

Args: func: The function to run *args: Arguments to pass to the function **kwargs: Keyword arguments to pass to the function

Returns: The result of the function call

Raises: ThreadManagerError: If the process execution fails"""
```
```python
    async def run_in_thread(self, func, *args, **kwargs) -> T:
        """Run a function in a worker thread.

This is suitable for CPU-bound tasks that would block the event loop.

Args: func: The function to run *args: Arguments to pass to the function **kwargs: Keyword arguments to pass to the function

Returns: The result of the function call

Raises: ThreadManagerError: If the thread execution fails"""
```
```python
    async def run_io_task(self, func, *args, **kwargs) -> T:
        """Run an I/O-bound function in a dedicated I/O thread pool.

This is suitable for I/O operations like file access, network calls, etc.

Args: func: The function to run *args: Arguments to pass to the function **kwargs: Keyword arguments to pass to the function

Returns: The result of the function call

Raises: ThreadManagerError: If the thread execution fails"""
```
```python
    async def run_on_main_thread(self, func, *args, **kwargs) -> T:
        """Run a function on the main thread.

This is essential for UI operations that must run on the main/UI thread.

Args: func: The function to run *args: Arguments to pass to the function **kwargs: Keyword arguments to pass to the function

Returns: The result of the function call

Raises: ThreadManagerError: If the execution fails"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the concurrency manager.

Gracefully shuts down thread pools and process pools.

Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the concurrency manager.  Returns: Dictionary containing status information"""
```

```python
class TaskPriority(int):
    """Task priority levels."""
```
*Class attributes:*
```python
LOW = 0
NORMAL = 50
HIGH = 100
CRITICAL = 200
```

#### Module: config_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/config_manager.py`

**Imports:**
```python
from __future__ import annotations
import json
import logging
import os
import pathlib
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, Union, Awaitable, cast
import aiofiles
import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ConfigurationError, ManagerInitializationError
```

**Classes:**
```python
class ConfigManager(QorzenManager):
    """Asynchronous configuration manager for the application.

This manager handles loading, validating, and providing access to configuration settings from files and environment variables.

Attributes: _config_path: Path to the configuration file _env_prefix: Prefix for environment variables _config: The loaded configuration _loaded_from_file: Whether configuration was loaded from a file _env_vars_applied: Set of applied environment variables _listeners: Dictionary of config change listeners"""
```
*Methods:*
```python
    def __init__(self, config_path, env_prefix) -> None:
        """Initialize the configuration manager.

Args: config_path: Path to the configuration file env_prefix: Prefix for environment variables"""
```
```python
    async def get(self, key, default) -> Any:
        """Get a configuration value by key.

Args: key: The configuration key (dot-separated for nested values) default: Default value if the key doesn't exist

Returns: The configuration value or default

Raises: ConfigurationError: If the manager isn't initialized"""
```
```python
    async def initialize(self) -> None:
        """Initialize the configuration manager asynchronously.

Loads configuration from default schema, file, and environment variables.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def register_listener(self, key, callback) -> None:
        """Register a listener for configuration changes.

Args: key: The configuration key to listen for callback: Async callback function to call when the key changes"""
```
```python
    async def set(self, key, value) -> None:
        """Set a configuration value by key.

Args: key: The configuration key (dot-separated for nested values) value: The value to set

Raises: ConfigurationError: If the manager isn't initialized or the value is invalid"""
```
```python
    def set_logger(self, logger) -> None:
```
```python
    async def shutdown(self) -> None:
        """Shut down the configuration manager."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the configuration manager.  Returns: Dictionary with status information"""
```
```python
    async def unregister_listener(self, key, callback) -> None:
        """Unregister a listener for configuration changes.

Args: key: The configuration key callback: The callback function to unregister"""
```

```python
class ConfigSchema(BaseModel):
    """Schema for validating configuration data.

This model defines the expected structure and default values for the application configuration."""
```
*Methods:*
```python
@model_validator(mode='after')
    def validate_api_port(self) -> 'ConfigSchema':
        """Validate that the API port is an integer."""
```
```python
@model_validator(mode='after')
    def validate_jwt_secret(self) -> 'ConfigSchema':
        """Validate that a JWT secret is set when API is enabled."""
```

#### Module: database_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import functools
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set, TypeVar, Union, cast, Callable, Awaitable, AsyncGenerator
import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import DatabaseError, ManagerInitializationError, ManagerShutdownError, DatabaseManagerInitializationError
```

**Global Variables:**
```python
T = T = TypeVar('T')
R = R = TypeVar('R')
```

**Classes:**
```python
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models.

This provides a common metadata instance with naming conventions for all models."""
```
*Class attributes:*
```python
metadata =     metadata = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'
    })
```

```python
class DatabaseConnection(object):
    """Database connection manager.

This class manages both synchronous and asynchronous connections to a database and provides session factories.

Attributes: config: Connection configuration engine: Synchronous SQLAlchemy engine async_engine: Asynchronous SQLAlchemy engine session_factory: Factory for creating synchronous sessions async_session_factory: Factory for creating asynchronous sessions initialized: Whether the connection is initialized healthy: Whether the connection is healthy active_sessions: Set of active synchronous sessions active_async_sessions: Set of active asynchronous sessions"""
```
*Methods:*
```python
    def __init__(self, config) -> None:
        """Initialize a database connection.  Args: config: Connection configuration"""
```

```python
class DatabaseConnectionConfig(object):
    """Configuration for a database connection.

Attributes: name: Name of the connection db_type: Database type (postgresql, mysql, etc.) host: Database host port: Database port database: Database name user: Database user password: Database password pool_size: Connection pool size max_overflow: Maximum overflow connections pool_recycle: Connection recycle time in seconds echo: Whether to echo SQL statements"""
```
*Methods:*
```python
    def __init__(self, name, db_type, host, port, database, user, password, pool_size, max_overflow, pool_recycle, echo) -> None:
        """Initialize database connection configuration.

Args: name: Name of the connection db_type: Database type (postgresql, mysql, etc.) host: Database host port: Database port database: Database name user: Database user password: Database password pool_size: Connection pool size max_overflow: Maximum overflow connections pool_recycle: Connection recycle time in seconds echo: Whether to echo SQL statements"""
```

```python
class DatabaseManager(QorzenManager):
    """Asynchronous database manager.

This manager provides access to database connections and sessions, supporting both synchronous and asynchronous operations.

Attributes: _config_manager: Configuration manager _logger: Logger instance _default_connection: Default database connection _connections: Dictionary of database connections"""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager) -> None:
        """Initialize the database manager.

Args: config_manager: Configuration manager logger_manager: Logging manager"""
```
```python
@asynccontextmanager
    async def async_session(self, connection_name) -> AsyncGenerator[(AsyncSession, None)]:
        """Get an asynchronous session for a connection.

Args: connection_name: Name of the connection, or None for default

Yields: A SQLAlchemy async session

Raises: DatabaseError: If the session cannot be created"""
```
```python
    async def check_connection(self, connection_name) -> bool:
        """Check if a connection is working.

Args: connection_name: Name of the connection, or None for default

Returns: True if the connection is working, False otherwise"""
```
```python
    async def create_tables(self, connection_name) -> None:
        """Create all tables for a connection synchronously.

Args: connection_name: Name of the connection, or None for default

Raises: DatabaseError: If table creation fails"""
```
```python
    async def create_tables_async(self, connection_name) -> None:
        """Create all tables for a connection asynchronously.

Args: connection_name: Name of the connection, or None for default

Raises: DatabaseError: If table creation fails"""
```
```python
    async def execute(self, statement, connection_name) -> List[Dict[(str, Any)]]:
        """Execute a SQLAlchemy statement synchronously.

Args: statement: SQLAlchemy statement to execute connection_name: Name of the connection, or None for default

Returns: List of result rows as dictionaries

Raises: DatabaseError: If execution fails"""
```
```python
    async def execute_async(self, statement, connection_name) -> List[Dict[(str, Any)]]:
        """Execute a SQLAlchemy statement asynchronously.

Args: statement: SQLAlchemy statement to execute connection_name: Name of the connection, or None for default

Returns: List of result rows as dictionaries

Raises: DatabaseError: If execution fails"""
```
```python
    async def execute_raw(self, sql, params, connection_name) -> List[Dict[(str, Any)]]:
        """Execute a raw SQL statement synchronously.

Args: sql: SQL statement to execute params: Parameters for the statement connection_name: Name of the connection, or None for default

Returns: List of result rows as dictionaries

Raises: DatabaseError: If execution fails"""
```
```python
    async def get_async_engine(self, connection_name) -> Optional[AsyncEngine]:
        """Get the asynchronous engine for a connection.

Args: connection_name: Name of the connection, or None for default

Returns: The SQLAlchemy async engine, or None if not available"""
```
```python
    async def get_connection_names(self) -> List[str]:
        """Get the names of all connections.  Returns: List of connection names"""
```
```python
    async def get_engine(self, connection_name) -> Optional[Engine]:
        """Get the synchronous engine for a connection.

Args: connection_name: Name of the connection, or None for default

Returns: The SQLAlchemy engine, or None if not available"""
```
```python
    async def has_connection(self, name) -> bool:
        """Check if a connection exists.

Args: name: Name of the connection

Returns: True if the connection exists, False otherwise"""
```
```python
    async def initialize(self) -> None:
        """Initialize the database manager asynchronously.

Sets up database connections based on configuration.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def register_connection(self, config) -> None:
        """Register a new database connection.

Args: config: Connection configuration

Raises: DatabaseError: If registration fails"""
```
```python
@asynccontextmanager
    async def session(self, connection_name) -> AsyncGenerator[(Session, None)]:
        """Get a synchronous session for a connection.

Args: connection_name: Name of the connection, or None for default

Yields: A SQLAlchemy session

Raises: DatabaseError: If the session cannot be created"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the database manager asynchronously.

Closes all connections and releases resources.

Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the database manager.  Returns: Dictionary with status information"""
```
```python
    async def unregister_connection(self, name) -> bool:
        """Unregister a database connection.

Args: name: Name of the connection to unregister

Returns: True if the connection was unregistered, False otherwise

Raises: DatabaseError: If unregistration fails"""
```

#### Module: dependency_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/dependency_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
import networkx as nx
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast
from qorzen.core.base import QorzenManager, BaseManager
from qorzen.utils.exceptions import DependencyError, ManagerInitializationError, ManagerShutdownError, DatabaseManagerInitializationError
```

**Global Variables:**
```python
T = T = TypeVar('T', bound=BaseManager)
```

**Classes:**
```python
class DependencyManager(QorzenManager):
    """Manager for handling dependencies between system components.

This manager tracks dependencies between different managers and ensures they are initialized and shut down in the correct order. It uses a directed acyclic graph (DAG) to represent dependencies."""
```
*Methods:*
```python
    def __init__(self, logger_manager) -> None:
        """Initialize the dependency manager.  Args: logger_manager: Optional logger manager for logging"""
```
```python
    def get_manager(self, name) -> Optional[BaseManager]:
        """Get a manager by name.

Args: name: The name of the manager to retrieve

Returns: The manager instance or None if not found"""
```
```python
    def get_manager_typed(self, name, manager_type) -> Optional[T]:
        """Get a manager by name with type checking.

Args: name: The name of the manager to retrieve manager_type: The expected type of the manager

Returns: The manager instance or None if not found or type doesn't match"""
```
```python
    async def initialize(self) -> None:
        """Initialize the dependency manager.  Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def initialize_all(self) -> None:
        """Initialize all managers in dependency order.

Raises: DependencyError: If there's a cycle in the dependency graph ManagerInitializationError: If a manager fails to initialize"""
```
```python
    def register_manager(self, manager, dependencies) -> None:
        """Register a manager with its dependencies.

Args: manager: The manager to register dependencies: List of manager names this manager depends on

Raises: DependencyError: If a dependency is not found or there's a circular dependency"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the dependency manager and all managed components.

Shuts down components in reverse dependency order.

Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the dependency manager.  Returns: Dictionary containing status information"""
```

#### Module: error_handler
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/error_handler.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import inspect
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast
from qorzen.utils import EventBusError
```

**Global Variables:**
```python
T = T = TypeVar('T')
```

**Functions:**
```python
def create_error_boundary(source, plugin_id, component) -> ErrorBoundary:
    """Create an error boundary using the global error handler.

Args: source: Source of errors (e.g., 'plugin', 'core') plugin_id: Optional plugin ID if from a plugin component: Optional component name

Returns: Error boundary

Raises: RuntimeError: If the global error handler is not set"""
```

```python
def get_global_error_handler() -> Optional[ErrorHandler]:
    """Get the global error handler.  Returns: Global error handler or None if not set"""
```

```python
def install_global_exception_hook() -> None:
    """Install a global exception hook to catch unhandled exceptions."""
```

```python
def safe_async(source, severity, plugin_id, component) -> Callable[([Callable[(Ellipsis, T)]], Callable[(Ellipsis, T)])]:
    """Decorator to make an async function safe using the global error handler.

Args: source: Source of errors (e.g., 'plugin', 'core') severity: Severity of errors that occur plugin_id: Optional plugin ID if from a plugin component: Optional component name

Returns: Decorator function

Raises: RuntimeError: If the global error handler is not set"""
```

```python
def safe_sync(source, severity, plugin_id, component) -> Callable[([Callable[(Ellipsis, T)]], Callable[(Ellipsis, T)])]:
    """Decorator to make a sync function safe using the global error handler.

Args: source: Source of errors (e.g., 'plugin', 'core') severity: Severity of errors that occur plugin_id: Optional plugin ID if from a plugin component: Optional component name

Returns: Decorator function

Raises: RuntimeError: If the global error handler is not set"""
```

```python
def set_global_error_handler(handler) -> None:
    """Set the global error handler.  Args: handler: Error handler to use globally"""
```

**Classes:**
```python
class ErrorBoundary(object):
    """Error boundary for async functions.

Provides a way to safely execute async functions and handle any exceptions that occur."""
```
*Methods:*
```python
    def __init__(self, error_handler, source, plugin_id, component) -> None:
        """Initialize the error boundary.

Args: error_handler: Error handler to use source: Source of errors (e.g., 'plugin', 'core') plugin_id: Optional plugin ID if from a plugin component: Optional component name"""
```
```python
    async def run(self, func, severity, *args, **kwargs) -> Optional[T]:
        """Run a function safely.

Args: func: Function to run *args: Arguments to pass to the function severity: Severity of errors that occur **kwargs: Keyword arguments to pass to the function

Returns: The result of the function or None if an error occurred

Raises: Exception: If the error handler decides to re-raise"""
```
```python
    def wrap(self, severity) -> Callable[([Callable[(Ellipsis, T)]], Callable[(Ellipsis, T)])]:
        """Create a decorator to wrap functions with error handling.

Args: severity: Severity of errors that occur

Returns: Decorator function"""
```

```python
class ErrorHandler(object):
    """Error handler for async applications.

Provides error handling services for the application, including error logging, reporting, and management."""
```
*Methods:*
```python
    def __init__(self, event_bus_manager, logger_manager, config_manager) -> None:
        """Initialize the error handler.

Args: event_bus_manager: Event bus manager logger_manager: Logger manager config_manager: Optional config manager"""
```
```python
    async def clear_errors(self, error_ids, source, plugin_id) -> int:
        """Clear errors.

Args: error_ids: Specific error IDs to clear, or None for all source: Filter by source plugin_id: Filter by plugin ID

Returns: Number of errors cleared"""
```
```python
    def create_boundary(self, source, plugin_id, component) -> ErrorBoundary:
        """Create an error boundary.

Args: source: Source of errors (e.g., 'plugin', 'core') plugin_id: Optional plugin ID if from a plugin component: Optional component name

Returns: Error boundary"""
```
```python
    async def get_error(self, error_id) -> Optional[ErrorInfo]:
        """Get information about an error.

Args: error_id: ID of the error

Returns: Error information or None if not found"""
```
```python
    async def get_errors(self, source, severity, plugin_id, component, handled, limit) -> List[ErrorInfo]:
        """Get errors matching criteria.

Args: source: Filter by source severity: Filter by severity or severities plugin_id: Filter by plugin ID component: Filter by component handled: Filter by handled status limit: Maximum number of errors to return

Returns: List of error information"""
```
```python
    async def handle_error(self, message, source, severity, plugin_id, component, traceback, metadata) -> bool:
        """Handle an error.

Args: message: Error message source: Source of the error (e.g., 'plugin', 'core') severity: Severity of the error plugin_id: Optional plugin ID if from a plugin component: Optional component name traceback: Optional traceback information metadata: Optional additional metadata

Returns: True if the error was handled, False if it should be re-raised"""
```
```python
    async def initialize(self) -> None:
```
```python
    async def register_error_strategy(self, source, strategy, plugin_id, component) -> None:
        """Register a strategy for handling errors.

Args: source: Source of errors to handle strategy: Function that takes an ErrorInfo and returns True if the error should be handled, False if it should be raised plugin_id: Optional plugin ID to limit the strategy to component: Optional component name to limit the strategy to"""
```
```python
    async def register_error_subscriber(self, subscriber) -> None:
        """Register a subscriber to be notified of errors.

Args: subscriber: Function to call with ErrorInfo when an error occurs"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the error handler.  Returns: Status information"""
```
```python
    async def unregister_error_strategy(self, source, plugin_id, component) -> bool:
        """Unregister an error strategy.

Args: source: Source of errors plugin_id: Optional plugin ID component: Optional component name

Returns: True if a strategy was unregistered, False otherwise"""
```
```python
    async def unregister_error_subscriber(self, subscriber) -> bool:
        """Unregister an error subscriber.

Args: subscriber: Subscriber to unregister

Returns: True if the subscriber was unregistered, False otherwise"""
```

```python
@dataclass
class ErrorInfo(object):
    """Information about an error."""
```

```python
class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
```
*Class attributes:*
```python
LOW = 'low'
MEDIUM = 'medium'
HIGH = 'high'
CRITICAL = 'critical'
```

#### Module: event_bus_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/event_bus_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import concurrent.futures
import inspect
import queue
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import Event, EventSubscription, EventHandler, EventType
from qorzen.utils.exceptions import EventBusError, ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
class EventBusManager(QorzenManager):
    """Asynchronous event bus manager for the application.

This manager handles event subscription, publication, and routing in an asynchronous manner. It supports filtering, prioritization, and main thread dispatching.

Attributes: _config_manager: The configuration manager _logger: The logger instance _thread_manager: The thread manager _max_queue_size: Maximum size of the event queue _publish_timeout: Timeout for event publishing _subscriptions: Dictionary of event subscriptions _event_queue: Queue for pending events _running: Flag indicating whether the manager is running _stop_event: Event to signal workers to stop"""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, thread_manager) -> None:
        """Initialize the event bus manager.

Args: config_manager: The configuration manager logger_manager: The logging manager thread_manager: The thread management system"""
```
```python
    async def initialize(self) -> None:
        """Initialize the event bus manager asynchronously.

Sets up the event queue and worker tasks.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def publish(self, event_type, source, payload, correlation_id, synchronous) -> str:
        """Publish an event asynchronously.

Args: event_type: Type of the event source: Source of the event payload: Event data correlation_id: ID for correlating related events synchronous: Whether to process the event synchronously

Returns: The event ID

Raises: EventBusError: If publishing fails"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the event bus manager asynchronously.  Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the event bus manager.  Returns: Dictionary with status information"""
```
```python
    async def subscribe(self, event_type, callback, subscriber_id, filter_criteria) -> str:
        """Subscribe to an event type asynchronously.

Args: event_type: Type of events to subscribe to callback: Callback function or coroutine for handling events subscriber_id: ID of the subscriber (generated if not provided) filter_criteria: Optional criteria for filtering events

Returns: The subscriber ID

Raises: EventBusError: If subscription fails"""
```
```python
    async def unsubscribe(self, subscriber_id, event_type) -> bool:
        """Unsubscribe from events asynchronously.

Args: subscriber_id: ID of the subscriber event_type: Optional specific event type to unsubscribe from

Returns: True if unsubscribed, False otherwise"""
```

#### Module: event_model
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/event_model.py`

**Imports:**
```python
from __future__ import annotations
import dataclasses
import datetime
import enum
import uuid
from typing import Any, Dict, Optional, Union, Callable, List, TypeVar, Generic
from pydantic import BaseModel, Field
```

**Global Variables:**
```python
T = T = TypeVar('T')
EventHandler = EventHandler = Callable[[Event], None]
```

**Classes:**
```python
class Config(object):
```
*Class attributes:*
```python
arbitrary_types_allowed = True
json_encoders =         json_encoders = {
            datetime.datetime: lambda dt: dt.isoformat(),
            uuid.UUID: lambda id: str(id)
        }
```

```python
class Event(BaseModel):
    """Event model with type information."""
```
*Methods:*
```python
    def __str__(self) -> str:
```
```python
@classmethod
    def create(cls, event_type, source, payload, correlation_id) -> Event:
        """Create a new event with the given parameters.

Args: event_type: The type of event (enum or string) source: The source component generating the event payload: Optional event data correlation_id: Optional ID for tracking related events

Returns: A new Event instance"""
```
```python
    def to_dict(self) -> Dict[(str, Any)]:
        """Convert event to dictionary."""
```

```python
class EventPayload(BaseModel, Generic[T]):
    """Base class for all event payloads with type information."""
```

```python
@dataclasses.dataclass
class EventSubscription(object):
    """Event subscription with typed handler."""
```
*Methods:*
```python
    def matches_event(self, event) -> bool:
        """Check if event matches this subscription.

Args: event: The event to check

Returns: True if the event matches this subscription"""
```

```python
class EventType(str, enum.Enum):
    """Standard event types in the system."""
```
*Class attributes:*
```python
SYSTEM_STARTED = 'system/started'
UI_READY = 'ui/ready'
UI_UPDATE = 'ui/update'
UI_COMPONENT_ADDED = 'ui/component/added'
LOG_MESSAGE = 'log/message'
LOG_ERROR = 'log/error'
LOG_EXCEPTION = 'log/exception'
LOG_WARNING = 'log/warning'
LOG_DEBUG = 'log/debug'
LOG_INFO = 'log/info'
LOG_TRACE = 'log/trace'
LOG_CRITICAL = 'log/critical'
LOG_EVENT = 'log/event'
PLUGIN_LOADED = 'plugin/loaded'
PLUGIN_UNLOADED = 'plugin/unloaded'
PLUGIN_ENABLED = 'plugin/enabled'
PLUGIN_DISABLED = 'plugin/disabled'
PLUGIN_INSTALLED = 'plugin/installed'
PLUGIN_UNINSTALLED = 'plugin/uninstalled'
PLUGIN_UPDATED = 'plugin/updated'
PLUGIN_ERROR = 'plugin/error'
PLUGIN_INITIALIZED = 'plugin/initialized'
PLUGIN_MANAGER_INITIALIZED = 'plugin_manager/initialized'
MONITORING_METRICS = 'monitoring/metrics'
MONITORING_ALERT = 'monitoring/alert'
CONFIG_CHANGED = 'config/changed'
CUSTOM = 'custom'
```
*Methods:*
```python
@classmethod
    def plugin_specific(cls, plugin_name, event_name) -> str:
        """Create a plugin-specific event type."""
```
```python
@classmethod
    def requires_main_thread(cls, event_type) -> bool:
        """Determine if an event type should be handled on the main thread."""
```

#### Module: file_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/file_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import hashlib
import os
import pathlib
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Optional, Set, Tuple, Union, cast, AsyncIterator
import aiofiles
import aiofiles.os
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import FileError, ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
@dataclass
class FileInfo(object):
    """Information about a file or directory.

Attributes: path: Absolute path to the file name: Name of the file (without directory) size: Size of the file in bytes created_at: Creation timestamp modified_at: Last modification timestamp file_type: Type of the file is_directory: Whether this is a directory content_hash: Optional hash of file contents metadata: Additional metadata"""
```

```python
class FileManager(QorzenManager):
    """Asynchronous file management system.

This manager provides asynchronous file operations with path validation, locking, and proper error handling.

Attributes: _config_manager: The configuration manager _logger: Logger instance _base_directory: Base directory for file operations _temp_directory: Directory for temporary files _plugin_data_directory: Directory for plugin data _backup_directory: Directory for backups _file_type_mapping: Mapping of file extensions to types _file_locks: Dictionary of file locks"""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager) -> None:
        """Initialize the file manager.

Args: config_manager: The configuration manager logger_manager: The logging manager"""
```
```python
    async def compute_file_hash(self, path, directory_type) -> str:
        """Compute a hash of file contents asynchronously.

Args: path: Path to the file directory_type: Type of directory

Returns: SHA-256 hash of the file contents

Raises: FileError: If hashing fails"""
```
```python
    async def copy_file(self, source_path, dest_path, source_dir_type, dest_dir_type, overwrite) -> None:
        """Copy a file asynchronously.

Args: source_path: Path to the source file dest_path: Path to the destination file source_dir_type: Type of source directory dest_dir_type: Type of destination directory overwrite: Whether to overwrite existing files

Raises: FileError: If copying fails"""
```
```python
    async def create_backup(self, path, directory_type) -> str:
        """Create a backup of a file asynchronously.

Args: path: Path to the file directory_type: Type of directory

Returns: Path to the backup file

Raises: FileError: If backup fails"""
```
```python
    async def create_temp_file(self, prefix, suffix) -> Tuple[(str, BinaryIO)]:
        """Create a temporary file asynchronously.

Args: prefix: Prefix for the temporary file name suffix: Suffix for the temporary file name

Returns: Tuple of (file path, file object)

Raises: FileError: If creation fails"""
```
```python
    async def delete_file(self, path, directory_type) -> None:
        """Delete a file asynchronously.

Args: path: Path to the file directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup')

Raises: FileError: If deletion fails"""
```
```python
    async def ensure_directory(self, path, directory_type) -> pathlib.Path:
        """Ensure a directory exists, creating it if necessary.

Args: path: Path to the directory directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup')

Returns: Absolute path to the directory

Raises: FileError: If directory creation fails"""
```
```python
    async def get_file_info(self, path, directory_type) -> FileInfo:
        """Get information about a file asynchronously.

Args: path: Path to the file directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup')

Returns: FileInfo object for the file

Raises: FileError: If getting info fails"""
```
```python
    def get_file_path(self, path, directory_type) -> pathlib.Path:
        """Get the absolute file path based on directory type.

Args: path: Relative or absolute path directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup')

Returns: Absolute path

Raises: FileError: If path is outside allowed directories or directory type is invalid"""
```
```python
    async def initialize(self) -> None:
        """Initialize the file manager asynchronously.

Creates necessary directories based on configuration.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def list_files(self, path, directory_type, recursive, include_dirs, pattern) -> List[FileInfo]:
        """List files in a directory asynchronously.

Args: path: Path to the directory directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup') recursive: Whether to list files recursively include_dirs: Whether to include directories in the results pattern: Optional glob pattern for filtering

Returns: List of FileInfo objects

Raises: FileError: If listing fails"""
```
```python
    async def move_file(self, source_path, dest_path, source_dir_type, dest_dir_type, overwrite) -> None:
        """Move a file asynchronously.

Args: source_path: Path to the source file dest_path: Path to the destination file source_dir_type: Type of source directory dest_dir_type: Type of destination directory overwrite: Whether to overwrite existing files

Raises: FileError: If moving fails"""
```
```python
    async def read_binary(self, path, directory_type) -> bytes:
        """Read binary data from a file asynchronously.

Args: path: Path to the file directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup')

Returns: The file contents as bytes

Raises: FileError: If reading fails"""
```
```python
    async def read_text(self, path, directory_type) -> str:
        """Read text from a file asynchronously.

Args: path: Path to the file directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup')

Returns: The file contents as text

Raises: FileError: If reading fails"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the file manager asynchronously.  Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the file manager.  Returns: Dictionary with status information"""
```
```python
    async def write_binary(self, path, content, directory_type, create_dirs) -> None:
        """Write binary data to a file asynchronously.

Args: path: Path to the file content: Binary content to write directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup') create_dirs: Whether to create parent directories

Raises: FileError: If writing fails"""
```
```python
    async def write_text(self, path, content, directory_type, create_dirs) -> None:
        """Write text to a file asynchronously.

Args: path: Path to the file content: Text content to write directory_type: Type of directory ('base', 'temp', 'plugin_data', 'backup') create_dirs: Whether to create parent directories

Raises: FileError: If writing fails"""
```

```python
class FileType(Enum):
    """Enum representing different file types."""
```
*Class attributes:*
```python
UNKNOWN = 'unknown'
TEXT = 'text'
BINARY = 'binary'
IMAGE = 'image'
DOCUMENT = 'document'
AUDIO = 'audio'
VIDEO = 'video'
CONFIG = 'config'
LOG = 'log'
DATA = 'data'
TEMP = 'temp'
BACKUP = 'backup'
```

#### Module: logging_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/logging_manager.py`

**Imports:**
```python
from __future__ import annotations
import atexit
import asyncio
import logging
import logging.handlers
import os
import pathlib
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, cast, Callable, Awaitable
import structlog
from pythonjsonlogger import jsonlogger
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, EventBusError
```

**Classes:**
```python
class EventBusManagerLogHandler(logging.Handler):
    """Log handler that publishes log events to an event bus.

This handler formats log records and publishes them as events to the event bus.

Args: event_bus_manager: The event bus manager to publish events to"""
```
*Methods:*
```python
    def __init__(self, event_bus_manager) -> None:
```
```python
    def emit(self, record) -> None:
        """Process a log record by putting it in the queue.  Args: record: The log record to process"""
```
```python
    async def start_processing(self) -> None:
        """Start the background task to process log events."""
```
```python
    async def stop_processing(self) -> None:
        """Stop the background processing task."""
```

```python
class ExcludeLoggerFilter(logging.Filter):
    """Filter to exclude logs from specific loggers.

Args: excluded_logger_name: The name of the logger to exclude"""
```
*Methods:*
```python
    def __init__(self, excluded_logger_name) -> None:
```
```python
    def filter(self, record) -> bool:
        """Filter out records from the excluded logger.

Args: record: The log record to check

Returns: True if the record should be included, False otherwise"""
```

```python
class LoggingManager(QorzenManager):
    """Asynchronous logging manager for the application.

This manager configures and provides access to the logging system, supporting various outputs including console, file, and event bus.

Attributes: LOG_LEVELS: Mapping of level names to logging levels"""
```
*Class attributes:*
```python
LOG_LEVELS =     LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
```
*Methods:*
```python
    def __init__(self, config_manager) -> None:
        """Initialize the logging manager.  Args: config_manager: The configuration manager"""
```
```python
    def get_logger(self, name) -> Union[(logging.Logger, Any)]:
        """Get a logger instance.

Args: name: Name for the logger

Returns: A standard logger or structlog instance"""
```
```python
    async def initialize(self) -> None:
        """Initialize the logging manager asynchronously.

Sets up logging configuration and handlers based on configuration.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def set_event_bus_manager(self, event_bus_manager) -> None:
        """Set the event bus manager and configure the event handler.

Args: event_bus_manager: The event bus manager"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the logging manager asynchronously.

Closes and flushes all handlers.

Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the logging manager.  Returns: Dictionary with status information"""
```

#### Module: plugin_isolation_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/plugin_isolation_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import importlib.util
import inspect
import os
import pathlib
import signal
import sys
import tempfile
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import PluginIsolationError, ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
@dataclass
class IsolatedPluginInfo(object):
    """Information about an isolated plugin."""
```

```python
class PluginIsolationLevel(str, Enum):
    """Isolation levels for plugins."""
```
*Class attributes:*
```python
NONE = 'none'
THREAD = 'thread'
PROCESS = 'process'
```

```python
class PluginIsolationManager(QorzenManager):
    """Manager for handling plugin isolation.

Provides a unified interface for loading, unloading, and interacting with plugins using different isolation strategies."""
```
*Methods:*
```python
    def __init__(self, concurrency_manager, logger_manager, config_manager, name) -> None:
        """Initialize the isolation manager.

Args: concurrency_manager: Manager for concurrency operations logger_manager: Manager for logging config_manager: Manager for configuration name: Name of this manager"""
```
```python
    def get_loaded_plugins(self) -> Dict[(str, PluginIsolationLevel)]:
        """Get all loaded plugins and their isolation levels.

Returns: Dictionary mapping plugin IDs to isolation levels"""
```
```python
    def get_plugin_isolation_level(self, plugin_id) -> Optional[PluginIsolationLevel]:
        """Get the isolation level of a plugin.

Args: plugin_id: ID of the plugin

Returns: The isolation level or None if the plugin is not loaded"""
```
```python
    async def initialize(self) -> None:
        """Initialize the isolation manager.

Creates and initializes isolators for different isolation levels.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    def is_plugin_loaded(self, plugin_id) -> bool:
        """Check if a plugin is loaded.

Args: plugin_id: ID of the plugin

Returns: True if the plugin is loaded"""
```
```python
    async def load_plugin(self, plugin_id, plugin_path, isolation_level) -> bool:
        """Load a plugin with the specified isolation level.

Args: plugin_id: ID to assign to the plugin plugin_path: Path to the plugin file or directory isolation_level: Isolation level to use, or None for default

Returns: True if the plugin was loaded successfully

Raises: PluginIsolationError: If loading fails"""
```
```python
    async def run_plugin_method(self, plugin_id, method_name, args, kwargs, timeout) -> Any:
        """Run a plugin method with the appropriate isolation.

Args: plugin_id: ID of the plugin method_name: Name of the method to run args: Positional arguments to pass kwargs: Keyword arguments to pass timeout: Optional timeout in seconds

Returns: Result of the method call

Raises: PluginIsolationError: If the method call fails"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the isolation manager.

Shuts down all isolators and unloads all plugins.

Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the isolation manager.  Returns: Dictionary containing status information"""
```
```python
    async def unload_plugin(self, plugin_id) -> bool:
        """Unload a plugin.

Args: plugin_id: ID of the plugin to unload

Returns: True if the plugin was unloaded successfully

Raises: PluginIsolationError: If unloading fails"""
```

```python
class PluginIsolator(ABC):
    """Base class for plugin isolators."""
```
*Methods:*
```python
@abstractmethod
    async def initialize(self) -> None:
        """Initialize the isolator."""
```
```python
@abstractmethod
    async def load_plugin(self, plugin_id, plugin_path) -> bool:
        """Load a plugin in isolation.

Args: plugin_id: ID to assign to the plugin plugin_path: Path to the plugin file or directory

Returns: True if the plugin was loaded successfully

Raises: PluginIsolationError: If loading fails"""
```
```python
@abstractmethod
    async def run_plugin_method(self, plugin_id, method_name, args, kwargs, timeout) -> Any:
        """Run a plugin method in isolation.

Args: plugin_id: ID of the plugin method_name: Name of the method to run args: Positional arguments to pass kwargs: Keyword arguments to pass timeout: Optional timeout in seconds

Returns: Result of the method call

Raises: PluginIsolationError: If the method call fails"""
```
```python
@abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the isolator."""
```
```python
@abstractmethod
    async def unload_plugin(self, plugin_id) -> bool:
        """Unload a plugin from isolation.

Args: plugin_id: ID of the plugin to unload

Returns: True if the plugin was unloaded successfully

Raises: PluginIsolationError: If unloading fails"""
```

```python
@dataclass
class PluginResourceLimits(object):
    """Resource limits for a plugin."""
```

```python
class ThreadIsolator(PluginIsolator):
    """Thread-based plugin isolator.

Provides thread-level isolation for plugins. Each plugin method runs in a separate thread with timeout support."""
```
*Methods:*
```python
    def __init__(self, concurrency_manager, logger) -> None:
        """Initialize the thread isolator.

Args: concurrency_manager: Manager for thread operations logger: Logger instance"""
```
```python
    async def initialize(self) -> None:
        """Initialize the thread isolator."""
```
```python
    async def load_plugin(self, plugin_id, plugin_path) -> bool:
        """Load a plugin in thread isolation.

Args: plugin_id: ID to assign to the plugin plugin_path: Path to the plugin file or directory

Returns: True if the plugin was loaded successfully

Raises: PluginIsolationError: If loading fails"""
```
```python
    async def run_plugin_method(self, plugin_id, method_name, args, kwargs, timeout) -> Any:
        """Run a plugin method in a thread.

Args: plugin_id: ID of the plugin method_name: Name of the method to run args: Positional arguments to pass kwargs: Keyword arguments to pass timeout: Optional timeout in seconds

Returns: Result of the method call

Raises: PluginIsolationError: If the method call fails"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the thread isolator."""
```
```python
    async def unload_plugin(self, plugin_id) -> bool:
        """Unload a plugin from thread isolation.

Args: plugin_id: ID of the plugin to unload

Returns: True if the plugin was unloaded successfully

Raises: PluginIsolationError: If unloading fails"""
```

#### Module: plugin_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/plugin_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import importlib
import inspect
import os
import pathlib
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union, cast, Tuple
from qorzen.core.base import QorzenManager
from qorzen.core.error_handler import ErrorHandler, ErrorSeverity, create_error_boundary
from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.plugin_state_manager import PluginStateManager
from qorzen.utils.exceptions import PluginError, ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
@dataclass
class PluginInfo(object):
```
*Methods:*
```python
@property
    def display_name(self) -> str:
```

```python
class PluginManager(QorzenManager):
```
*Methods:*
```python
    def __init__(self, application_core, config_manager, logger_manager, event_bus_manager, file_manager, task_manager, plugin_isolation_manager) -> None:
```
```python
    async def disable_plugin(self, plugin_id) -> bool:
```
```python
    async def enable_plugin(self, plugin_id) -> bool:
```
```python
    async def get_plugin_info(self, plugin_id) -> Optional[PluginInfo]:
```
```python
    async def get_plugin_instance(self, plugin_id) -> Optional[Any]:
```
```python
    async def get_plugins(self, state) -> Dict[(str, PluginInfo)]:
```
```python
    async def initialize(self) -> None:
```
```python
    async def load_plugin(self, plugin_id) -> bool:
```
```python
    async def reload_plugin(self, plugin_id) -> bool:
```
```python
    async def shutdown(self) -> None:
```
```python
    def status(self) -> Dict[(str, Any)]:
```
```python
    async def unload_plugin(self, plugin_id) -> bool:
```

```python
@dataclass
class PluginManifest(object):
```
*Methods:*
```python
@classmethod
    def from_dict(cls, data) -> PluginManifest:
```
```python
@classmethod
    def load(cls, path) -> Optional[PluginManifest]:
```
```python
    def to_dict(self) -> Dict[(str, Any)]:
```

```python
class PluginState(str, Enum):
```
*Class attributes:*
```python
DISCOVERED = 'discovered'
LOADING = 'loading'
ACTIVE = 'active'
INACTIVE = 'inactive'
FAILED = 'failed'
DISABLED = 'disabled'
INCOMPATIBLE = 'incompatible'
```

#### Module: remote_manager
*Asynchronous Remote Services Manager for managing external service connections.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/remote_manager.py`

**Imports:**
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

**Classes:**
```python
class HTTPService(RemoteService):
    """HTTP/HTTPS remote service."""
```
*Methods:*
```python
    def __init__(self, name, base_url, protocol, **kwargs) -> None:
        """Initialize the HTTP service.

Args: name: Service name base_url: Base URL of the service protocol: Service protocol (HTTP or HTTPS) **kwargs: Additional configuration options"""
```
```python
    async def check_health(self) -> bool:
        """Check the health of the service.  Returns: True if healthy, False otherwise"""
```
```python
    async def close(self) -> None:
        """Close the HTTP client."""
```
```python
    async def delete(self, path, **kwargs) -> httpx.Response:
        """Send a DELETE request.

Args: path: Request path **kwargs: Additional options

Returns: HTTP response"""
```
```python
    async def get(self, path, params, **kwargs) -> httpx.Response:
        """Send a GET request.

Args: path: Request path params: Query parameters **kwargs: Additional options

Returns: HTTP response"""
```
```python
    async def get_client(self) -> httpx.AsyncClient:
        """Get the HTTP client.  Returns: AsyncClient instance"""
```
```python
    async def initialize_client(self) -> None:
        """Initialize the HTTP client."""
```
```python
    async def patch(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Send a PATCH request.

Args: path: Request path data: Request data json_data: JSON request data **kwargs: Additional options

Returns: HTTP response"""
```
```python
    async def post(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Send a POST request.

Args: path: Request path data: Request data json_data: JSON request data **kwargs: Additional options

Returns: HTTP response"""
```
```python
    async def put(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Send a PUT request.

Args: path: Request path data: Request data json_data: JSON request data **kwargs: Additional options

Returns: HTTP response"""
```
```python
@retry(retry=retry_if_exception_type(httpx.HTTPError), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def request(self, method, path, params, data, json_data, headers, timeout) -> httpx.Response:
        """Send an HTTP request.

Args: method: HTTP method path: Request path params: Query parameters data: Request data json_data: JSON request data headers: Additional headers timeout: Request timeout in seconds

Returns: HTTP response

Raises: Exception: If the request fails"""
```

```python
class RemoteService(abc.ABC):
    """Base class for remote services."""
```
*Methods:*
```python
    def __init__(self, name, protocol, base_url, timeout, max_retries, retry_delay, retry_max_delay, headers, auth, config, logger) -> None:
        """Initialize the remote service.

Args: name: Service name protocol: Service protocol base_url: Base URL of the service timeout: Request timeout in seconds max_retries: Maximum number of retry attempts retry_delay: Initial delay between retries in seconds retry_max_delay: Maximum delay between retries in seconds headers: Default headers to include in requests auth: Authentication configuration config: Additional service configuration logger: Logger instance"""
```
```python
@abc.abstractmethod
    async def check_health(self) -> bool:
        """Check the health of the service.  Returns: True if healthy, False otherwise"""
```
```python
@abc.abstractmethod
    async def get_client(self) -> Any:
        """Get the service client.  Returns: Service client instance"""
```
```python
@abc.abstractmethod
    async def initialize_client(self) -> None:
        """Initialize the service client."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """Get the status of the service.  Returns: Dict containing service status information"""
```
```python
    async def update_metrics(self, response_time, success) -> None:
        """Update service metrics.

Args: response_time: Response time in seconds success: Whether the request was successful"""
```

```python
class RemoteServicesManager(QorzenManager):
    """Manager for remote services."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, event_bus_manager, task_manager) -> None:
        """Initialize the remote services manager.

Args: config_manager: Configuration manager instance logger_manager: Logger manager instance event_bus_manager: Event bus manager instance task_manager: Task manager instance"""
```
```python
    async def check_all_services_health(self) -> Dict[(str, bool)]:
        """Check the health of all services.  Returns: Dictionary of service name to health status"""
```
```python
    async def check_service_health(self, service_name) -> bool:
        """Check the health of a service.

Args: service_name: Name of the service

Returns: True if healthy, False otherwise"""
```
```python
    async def get_all_services(self) -> Dict[(str, RemoteService)]:
        """Get all registered services.  Returns: Dictionary of service name to RemoteService instance"""
```
```python
    async def get_http_service(self, service_name) -> Optional[HTTPService]:
        """Get an HTTP service by name.

Args: service_name: Name of the service

Returns: HTTPService instance or None if not found or not an HTTP service"""
```
```python
    async def get_service(self, service_name) -> Optional[RemoteService]:
        """Get a service by name.

Args: service_name: Name of the service

Returns: RemoteService instance or None if not found"""
```
```python
    async def initialize(self) -> None:
        """Initialize the remote services manager."""
```
```python
    async def make_request(self, service_name, method, path, **kwargs) -> Any:
        """Make a request to a remote service.

Args: service_name: Name of the service method: HTTP method path: Request path **kwargs: Additional request options

Returns: Response data (JSON parsed or text)

Raises: ValueError: If the service is not found or request fails"""
```
```python
    async def register_service(self, service) -> None:
        """Register a remote service.

Args: service: Remote service instance

Raises: ValueError: If the service is already registered or manager not initialized"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the remote services manager."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """Get the status of the remote services manager.  Returns: Dict containing status information"""
```
```python
    async def unregister_service(self, service_name) -> bool:
        """Unregister a remote service.

Args: service_name: Name of the service to unregister

Returns: True if successful, False otherwise"""
```

```python
class ServiceProtocol(str, Enum):
    """Supported remote service protocols."""
```
*Class attributes:*
```python
HTTP = 'http'
HTTPS = 'https'
GRPC = 'grpc'
SOAP = 'soap'
CUSTOM = 'custom'
```

#### Module: resource_monitoring_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/resource_monitoring_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import datetime
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, cast
import psutil
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
@dataclass
class Alert(object):
    """System alert information.

Attributes: id: Unique alert ID level: Alert severity level message: Alert message source: Alert source timestamp: When the alert was created metric_name: Optional name of the related metric metric_value: Optional value of the related metric threshold: Optional threshold that triggered the alert resolved: Whether the alert is resolved resolved_at: When the alert was resolved metadata: Additional metadata"""
```

```python
class AlertLevel(Enum):
    """Alert severity levels.

Attributes: INFO: Informational alert WARNING: Warning alert ERROR: Error alert CRITICAL: Critical alert"""
```
*Class attributes:*
```python
INFO = 'info'
WARNING = 'warning'
ERROR = 'error'
CRITICAL = 'critical'
```

```python
class ResourceMonitoringManager(QorzenManager):
    """Asynchronous resource monitoring manager.

This manager monitors system resources, collects metrics, and generates alerts when thresholds are exceeded.

Attributes: _config_manager: Configuration manager _logger: Logger instance _event_bus_manager: Event bus manager _thread_manager: Thread management system _metrics: Dictionary of prometheus metrics _prometheus_server_port: Port for the prometheus server _alert_thresholds: Threshold values for alerts _alerts: Dictionary of active alerts _resolved_alerts: Queue of resolved alerts"""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, event_bus_manager, thread_manager) -> None:
        """Initialize the resource monitoring manager.

Args: config_manager: Configuration manager logger_manager: Logging manager event_bus_manager: Event bus manager thread_manager: Thread management system"""
```
```python
    async def generate_diagnostic_report(self) -> Dict[(str, Any)]:
        """Generate a diagnostic report of system status.  Returns: Dictionary with diagnostic information"""
```
```python
    async def get_alerts(self, include_resolved, level, metric_name) -> List[Dict[(str, Any)]]:
        """Get alerts matching criteria.

Args: include_resolved: Whether to include resolved alerts level: Optional filter by alert level metric_name: Optional filter by metric name

Returns: List of alerts as dictionaries"""
```
```python
    async def initialize(self) -> None:
        """Initialize the resource monitoring manager asynchronously.

Sets up metrics collection and prometheus server.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def register_counter(self, name, description, labels) -> Any:
        """Register a new counter metric.

Args: name: Metric name description: Metric description labels: Optional label names

Returns: The created counter

Raises: ValueError: If registration fails"""
```
```python
    async def register_gauge(self, name, description, labels) -> Any:
        """Register a new gauge metric.

Args: name: Metric name description: Metric description labels: Optional label names

Returns: The created gauge

Raises: ValueError: If registration fails"""
```
```python
    async def register_histogram(self, name, description, labels, buckets) -> Any:
        """Register a new histogram metric.

Args: name: Metric name description: Metric description labels: Optional label names buckets: Optional histogram buckets

Returns: The created histogram

Raises: ValueError: If registration fails"""
```
```python
    async def register_summary(self, name, description, labels) -> Any:
        """Register a new summary metric.

Args: name: Metric name description: Metric description labels: Optional label names

Returns: The created summary

Raises: ValueError: If registration fails"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the resource monitoring manager asynchronously.

Cancels collection tasks and unregisters listeners.

Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the resource monitoring manager.  Returns: Dictionary with status information"""
```

#### Module: security_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/security_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import datetime
import hashlib
import os
import re
import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Callable, Awaitable
import jwt
from passlib.context import CryptContext
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, SecurityError
```

**Classes:**
```python
@dataclass
class AuthToken(object):
    """Authentication token information.

Attributes: token: The token string token_type: Type of token (access, refresh) user_id: User ID the token belongs to expires_at: When the token expires issued_at: When the token was issued jti: Unique token identifier metadata: Additional metadata"""
```

```python
@dataclass
class Permission(object):
    """Permission definition.

Attributes: id: Unique permission ID name: Permission name description: Permission description resource: Resource being protected action: Action being controlled roles: Roles that have this permission"""
```

```python
class SecurityManager(QorzenManager):
    """Asynchronous security manager.

This manager handles authentication, authorization, user management, and token management.

Attributes: _config_manager: Configuration manager _logger: Logger instance _event_bus_manager: Event bus manager _db_manager: Database manager _pwd_context: Password hashing context _users: Dictionary of users _username_to_id: Mapping of usernames to user IDs _email_to_id: Mapping of emails to user IDs _permissions: Dictionary of permissions _token_blacklist: Set of blacklisted token JTIs _active_tokens: Dictionary of active tokens by user ID"""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, event_bus_manager, db_manager) -> None:
        """Initialize the security manager.

Args: config_manager: Configuration manager logger_manager: Logging manager event_bus_manager: Event bus manager db_manager: Optional database manager"""
```
```python
    async def authenticate_user(self, username_or_email, password) -> Optional[Dict[(str, Any)]]:
        """Authenticate a user with username/email and password.

Args: username_or_email: Username or email address password: Password

Returns: Dictionary with user info and tokens if authentication succeeded, None otherwise"""
```
```python
    async def create_user(self, username, email, password, roles, metadata) -> Optional[str]:
        """Create a new user.

Args: username: Username email: Email address password: Password roles: User roles metadata: Additional metadata

Returns: The user ID if creation was successful, None otherwise

Raises: SecurityError: If user creation fails"""
```
```python
    async def delete_user(self, user_id) -> bool:
        """Delete a user.

Args: user_id: User ID

Returns: True if deletion was successful, False otherwise

Raises: SecurityError: If deletion fails"""
```
```python
    async def get_all_permissions(self) -> List[Dict[(str, Any)]]:
        """Get information about all permissions.  Returns: List of dictionaries with permission information"""
```
```python
    async def get_all_users(self) -> List[Dict[(str, Any)]]:
        """Get information about all users.  Returns: List of dictionaries with user information"""
```
```python
    async def get_user_info(self, user_id) -> Optional[Dict[(str, Any)]]:
        """Get information about a user.

Args: user_id: User ID

Returns: Dictionary with user information if found, None otherwise"""
```
```python
    async def has_permission(self, user_id, resource, action) -> bool:
        """Check if a user has a specific permission.

Args: user_id: User ID resource: Resource being accessed action: Action being performed

Returns: True if the user has the permission, False otherwise"""
```
```python
    async def has_role(self, user_id, role) -> bool:
        """Check if a user has a specific role.

Args: user_id: User ID role: Role to check

Returns: True if the user has the role, False otherwise"""
```
```python
    async def initialize(self) -> None:
        """Initialize the security manager asynchronously.

Sets up JWT configuration, permissions, and default users.

Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def refresh_token(self, refresh_token) -> Optional[Dict[(str, Any)]]:
        """Refresh an access token using a refresh token.

Args: refresh_token: The refresh token

Returns: Dictionary with new access token if successful, None otherwise"""
```
```python
    async def revoke_token(self, token) -> bool:
        """Revoke a token.

Args: token: The token to revoke

Returns: True if revocation was successful, False otherwise"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the security manager asynchronously.  Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the security manager.  Returns: Dictionary with status information"""
```
```python
    async def update_user(self, user_id, updates) -> bool:
        """Update a user.

Args: user_id: User ID updates: Dictionary of fields to update

Returns: True if update was successful, False otherwise

Raises: SecurityError: If update fails"""
```
```python
    async def verify_token(self, token) -> Optional[Dict[(str, Any)]]:
        """Verify a token.  Args: token: The token to verify  Returns: Token payload if valid, None otherwise"""
```

```python
@dataclass
class User(object):
    """User information.

Attributes: id: Unique user ID username: Username email: Email address hashed_password: Hashed password roles: List of user roles active: Whether the user is active created_at: When the user was created last_login: When the user last logged in metadata: Additional metadata"""
```

```python
class UserRole(Enum):
    """User roles in the system.

Attributes: ADMIN: Administrator role with full access OPERATOR: Operator role with system management access USER: Regular user with limited access VIEWER: Read-only user"""
```
*Class attributes:*
```python
ADMIN = 'admin'
OPERATOR = 'operator'
USER = 'user'
VIEWER = 'viewer'
```

#### Module: task_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/task_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, TaskError
```

**Global Variables:**
```python
T = T = TypeVar('T')
```

**Classes:**
```python
class TaskCategory(str, Enum):
    """Categories of tasks."""
```
*Class attributes:*
```python
CORE = 'core'
PLUGIN = 'plugin'
UI = 'ui'
IO = 'io'
BACKGROUND = 'background'
USER = 'user'
```

```python
@dataclass
class TaskInfo(object):
    """Information about a task."""
```

```python
class TaskManager(QorzenManager):
    """Manager for handling tasks asynchronously.

This manager provides a unified interface for running both synchronous and asynchronous tasks with progress reporting and error handling."""
```
*Methods:*
```python
    def __init__(self, concurrency_manager, event_bus_manager, logger_manager, config_manager) -> None:
        """Initialize the task manager.

Args: concurrency_manager: Manager for concurrency operations event_bus_manager: Manager for event bus operations logger_manager: Manager for logging config_manager: Manager for configuration"""
```
```python
    async def cancel_task(self, task_id) -> bool:
        """Cancel a running task.

Args: task_id: ID of the task to cancel

Returns: True if the task was cancelled, False otherwise

Raises: TaskError: If the task can't be cancelled"""
```
```python
    async def get_task_info(self, task_id) -> Optional[TaskInfo]:
        """Get information about a task.

Args: task_id: ID of the task

Returns: Task information or None if not found"""
```
```python
    async def get_tasks(self, status, category, plugin_id, limit) -> List[TaskInfo]:
        """Get tasks matching the specified criteria.

Args: status: Filter by task status category: Filter by task category plugin_id: Filter by plugin ID limit: Maximum number of tasks to return

Returns: List of task information objects"""
```
```python
    async def initialize(self) -> None:
        """Initialize the task manager.  Raises: ManagerInitializationError: If initialization fails"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the task manager.

Cancels all running tasks and cleans up resources.

Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the task manager.  Returns: Dictionary containing status information"""
```
```python
    async def submit_async_task(self, func, name, category, plugin_id, priority, metadata, timeout, cancellable, *args, **kwargs) -> str:
        """Submit an asynchronous task to be executed.

This is a convenience wrapper around submit_task that ensures the function is treated as asynchronous.

Args: func: The async function to execute *args: Positional arguments to pass to the function name: Name of the task category: Category of the task plugin_id: ID of the plugin if this is a plugin task priority: Priority of the task metadata: Additional metadata for the task timeout: Timeout in seconds, or None for default cancellable: Whether the task can be cancelled **kwargs: Keyword arguments to pass to the function

Returns: ID of the submitted task

Raises: TaskError: If submission fails or the function is not async"""
```
```python
    async def submit_task(self, func, name, category, plugin_id, priority, metadata, timeout, cancellable, *args, **kwargs) -> str:
        """Submit a task to be executed.

Args: func: The function to execute *args: Positional arguments to pass to the function name: Name of the task category: Category of the task plugin_id: ID of the plugin if this is a plugin task priority: Priority of the task metadata: Additional metadata for the task timeout: Timeout in seconds, or None for default cancellable: Whether the task can be cancelled **kwargs: Keyword arguments to pass to the function

Returns: ID of the submitted task

Raises: TaskError: If submission fails"""
```
```python
    async def wait_for_task(self, task_id, timeout) -> TaskInfo:
        """Wait for a task to complete.

Args: task_id: ID of the task to wait for timeout: Timeout in seconds, or None to wait indefinitely

Returns: Task information

Raises: TaskError: If the task is not found or waiting times out"""
```

```python
class TaskPriority(int, Enum):
    """Priority levels for tasks."""
```
*Class attributes:*
```python
LOW = 0
NORMAL = 50
HIGH = 100
CRITICAL = 200
```

```python
@dataclass
class TaskProgress(object):
    """Progress information for a task."""
```

```python
class TaskStatus(str, Enum):
    """Status of a task."""
```
*Class attributes:*
```python
PENDING = 'pending'
RUNNING = 'running'
COMPLETED = 'completed'
FAILED = 'failed'
CANCELLED = 'cancelled'
```

### Package: models
Path: `/home/runner/work/qorzen/qorzen/qorzen/models`

**__init__.py:**
*Database models for the Qorzen platform.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/models/__init__.py`

**Imports:**
```python
from qorzen.models.audit import AuditLog
from qorzen.models.base import Base, TimestampMixin
from qorzen.models.plugin import Plugin
from qorzen.models.system import SystemSetting
from qorzen.models.user import User, UserRole
```

#### Module: audit
*Audit log model for tracking system events and user actions.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/models/audit.py`

**Imports:**
```python
import enum
from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.sql import func
from qorzen.models.base import Base
```

**Classes:**
```python
class AuditActionType(enum.Enum):
    """Types of actions that can be audited."""
```
*Class attributes:*
```python
CREATE = 'create'
READ = 'read'
UPDATE = 'update'
DELETE = 'delete'
LOGIN = 'login'
LOGOUT = 'logout'
EXPORT = 'export'
IMPORT = 'import'
CONFIG = 'config'
SYSTEM = 'system'
PLUGIN = 'plugin'
CUSTOM = 'custom'
```

```python
class AuditLog(Base):
    """Audit log model for tracking system events and user actions."""
```
*Class attributes:*
```python
__tablename__ = 'audit_logs'
id =     id = Column(Integer, primary_key=True)
timestamp =     timestamp = Column(DateTime, default=func.now(), nullable=False)
user_id =     user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
user_name =     user_name = Column(String(32), nullable=True)
action_type =     action_type = Column(Enum(AuditActionType), nullable=False)
resource_type =     resource_type = Column(String(64), nullable=False)
resource_id =     resource_id = Column(String(64), nullable=True)
description =     description = Column(String(255), nullable=True)
ip_address =     ip_address = Column(String(45), nullable=True)  # IPv6 compatible
user_agent =     user_agent = Column(String(255), nullable=True)
details =     details = Column(JSON, nullable=True)
```
*Methods:*
```python
    def __repr__(self) -> str:
```

#### Module: base
*Base classes for database models.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/models/base.py`

**Imports:**
```python
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
```

**Global Variables:**
```python
Base = Base = declarative_base()
```

**Classes:**
```python
class TimestampMixin(object):
    """Mixin that adds created_at and updated_at columns to a model."""
```
*Class attributes:*
```python
created_at =     created_at = Column(DateTime, default=func.now(), nullable=False)
updated_at =     updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
```

#### Module: plugin
*Plugin model for storing plugin information.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/models/plugin.py`

**Imports:**
```python
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from qorzen.models.base import Base, TimestampMixin
```

**Classes:**
```python
class Plugin(Base, TimestampMixin):
    """Plugin model for storing plugin metadata and configuration."""
```
*Class attributes:*
```python
__tablename__ = 'plugins'
id =     id = Column(Integer, primary_key=True)
name =     name = Column(String(64), unique=True, nullable=False)
version =     version = Column(String(32), nullable=False)
description =     description = Column(String(255), nullable=True)
author =     author = Column(String(128), nullable=True)
enabled =     enabled = Column(Boolean, default=True, nullable=False)
installed_path =     installed_path = Column(String(255), nullable=True)
configuration =     configuration = Column(JSON, nullable=True)
```
*Methods:*
```python
    def __repr__(self) -> str:
```

#### Module: system
*System settings model for persistent configuration.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/models/system.py`

**Imports:**
```python
from sqlalchemy import JSON, Boolean, Column, Integer, String
from sqlalchemy.orm import validates
from qorzen.models.base import Base, TimestampMixin
```

**Classes:**
```python
class SystemSetting(Base, TimestampMixin):
    """System settings model for storing persistent configuration values."""
```
*Class attributes:*
```python
__tablename__ = 'system_settings'
id =     id = Column(Integer, primary_key=True)
key =     key = Column(String(128), unique=True, nullable=False, index=True)
value =     value = Column(JSON, nullable=True)
description =     description = Column(String(255), nullable=True)
is_secret =     is_secret = Column(Boolean, default=False, nullable=False)
is_editable =     is_editable = Column(Boolean, default=True, nullable=False)
```
*Methods:*
```python
    def __repr__(self) -> str:
```
```python
@validates('key')
    def validate_key(self, key, value):
        """Validate that the key is in a valid format."""
```

#### Module: user
*User model for authentication and authorization.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/models/user.py`

**Imports:**
```python
import enum
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from qorzen.models.base import Base, TimestampMixin
```

**Global Variables:**
```python
user_roles = user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role", Enum(UserRole), primary_key=True),
)
```

**Classes:**
```python
class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
```
*Class attributes:*
```python
__tablename__ = 'users'
id =     id = Column(Integer, primary_key=True)
username =     username = Column(String(32), unique=True, nullable=False)
email =     email = Column(String(255), unique=True, nullable=False)
hashed_password =     hashed_password = Column(String(255), nullable=False)
active =     active = Column(Boolean, default=True, nullable=False)
last_login =     last_login = Column(DateTime, nullable=True)
roles =     roles = relationship("UserRole", secondary=user_roles, backref="users")
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class UserRole(enum.Enum):
    """User roles for role-based access control."""
```
*Class attributes:*
```python
ADMIN = 'admin'
OPERATOR = 'operator'
USER = 'user'
VIEWER = 'viewer'
```

### Package: plugin_system
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/__init__.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.plugin_system.manifest import PluginManifest, PluginAuthor, PluginDependency, PluginCapability, PluginExtensionPoint, PluginExtensionUse
from qorzen.plugin_system.installer import PluginInstaller, InstalledPlugin
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.repository import PluginRepositoryManager
from qorzen.plugin_system.dependency import DependencyResolver
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.interface import PluginInterface, BasePlugin
from qorzen.plugin_system.lifecycle import PluginLifecycleState, LifecycleManager, get_lifecycle_manager, set_thread_manager, set_plugin_manager, execute_hook, set_plugin_state, get_plugin_state
from qorzen.plugin_system.ui_registry import UIComponentRegistry
from qorzen.plugin_system.integration import IntegratedPluginInstaller, PluginIntegrationError
```

#### Module: cli
*Command-line interface for the Qorzen plugin system.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/cli.py`

**Imports:**
```python
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from qorzen.plugin_system.manifest import PluginManifest, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, PluginVerifier
from qorzen.plugin_system.tools import create_plugin_template, package_plugin, test_plugin, validate_plugin, create_plugin_signing_key
import tempfile
```

**Functions:**
```python
def create_command(args) -> int:
    """Handle the create command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def disable_command(args) -> int:
    """Handle the disable command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def enable_command(args) -> int:
    """Handle the enable command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def generate_key_command(args) -> int:
    """Handle the generate-key command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def install_command(args) -> int:
    """Handle the install command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def list_command(args) -> int:
    """Handle the list command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def main(args) -> int:
    """Main entry point for the command-line interface.

Args: args: Command-line arguments (defaults to sys.argv[1:])

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def package_command(args) -> int:
    """Handle the package command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def sign_command(args) -> int:
    """Handle the sign command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def test_command(args) -> int:
    """Handle the test command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def uninstall_command(args) -> int:
    """Handle the uninstall command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def validate_command(args) -> int:
    """Handle the validate command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

```python
def verify_command(args) -> int:
    """Handle the verify command.

Args: args: Command-line arguments

Returns: Exit code (0 for success, non-zero for failure)"""
```

#### Module: config_schema
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/config_schema.py`

**Imports:**
```python
from __future__ import annotations
import enum
from typing import Any, Dict, List, Literal, Optional, Union, TypedDict, get_args, get_origin
import pydantic
from pydantic import Field, validator
```

**Functions:**
```python
def convert_pydantic_to_schema(model_class) -> ConfigSchema:
    """Convert a pydantic model class to a ConfigSchema.

This allows plugin developers to define their configuration as Pydantic models and automatically convert them to config schemas.

Args: model_class: A pydantic model class

Returns: A ConfigSchema representing the model"""
```

**Classes:**
```python
class ConfigField(pydantic.BaseModel):
    """Configuration field definition."""
```
*Methods:*
```python
@validator('default_value')
    def validate_default_value(cls, v, values):
        """Validate that default value is appropriate for the field type."""
```
```python
@validator('options')
    def validate_options(cls, v, values):
        """Validate that options are provided for select and multiselect fields."""
```

```python
class ConfigFieldType(str, enum.Enum):
    """Enumeration of supported configuration field types."""
```
*Class attributes:*
```python
STRING = 'string'
INTEGER = 'integer'
FLOAT = 'float'
BOOLEAN = 'boolean'
SELECT = 'select'
MULTISELECT = 'multiselect'
COLOR = 'color'
FILE = 'file'
DIRECTORY = 'directory'
PASSWORD = 'password'
JSON = 'json'
CODE = 'code'
DATETIME = 'datetime'
DATE = 'date'
TIME = 'time'
```

```python
class ConfigGroup(pydantic.BaseModel):
    """Group of configuration fields."""
```

```python
class ConfigSchema(pydantic.BaseModel):
    """Schema for plugin configuration."""
```
*Methods:*
```python
    def get_default_values(self) -> Dict[(str, Any)]:
        """Get the default values for all fields."""
```
```python
    def to_dict(self) -> Dict[(str, Any)]:
        """Convert the schema to a dictionary representation."""
```
```python
    def validate_config(self, config) -> Dict[(str, Any)]:
        """Validate the configuration against the schema."""
```

```python
class ValidationRule(pydantic.BaseModel):
    """Validation rule for configuration fields."""
```

#### Module: dependency
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/dependency.py`

**Imports:**
```python
from __future__ import annotations
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from qorzen.plugin_system.manifest import PluginManifest, PluginDependency
from qorzen.plugin_system.repository import PluginRepositoryManager
```

**Classes:**
```python
class CircularDependencyError(DependencyError):
    """Error raised when a circular dependency is detected."""
```
*Methods:*
```python
    def __init__(self, dependency_chain):
```

```python
class DependencyError(Exception):
    """Base class for dependency resolution errors."""
```

```python
@dataclass
class DependencyGraph(object):
    """Dependency graph for resolving plugin dependencies."""
```
*Methods:*
```python
    def add_edge(self, from_node, to_node) -> None:
        """Add an edge between nodes."""
```
```python
    def add_node(self, node) -> None:
        """Add a node to the graph."""
```
```python
    def get_dependencies(self, node_name) -> List[str]:
        """Get the dependencies of a node."""
```
```python
    def resolve(self) -> List[str]:
        """Resolve the dependency graph, returning the nodes in dependency order."""
```

```python
@dataclass
class DependencyNode(object):
    """Node in the dependency graph."""
```
*Methods:*
```python
@property
    def is_core(self) -> bool:
        """Check if the plugin is the core system."""
```
```python
@property
    def is_local(self) -> bool:
        """Check if the plugin is available locally."""
```

```python
class DependencyResolver(object):
    """Resolver for plugin dependencies."""
```
*Methods:*
```python
    def __init__(self, repository_manager, logger):
```
```python
    def get_dependency_graph(self, plugin_manifests) -> DependencyGraph:
        """Build a dependency graph for multiple plugins.

Args: plugin_manifests: A dictionary mapping plugin names to manifests

Returns: A dependency graph"""
```
```python
    def log(self, message, level) -> None:
        """Log a message."""
```
```python
    def resolve_dependencies(self, plugin_manifest, resolve_transitives, fetch_missing) -> List[Tuple[(str, str, bool)]]:
        """Resolve plugin dependencies.

Args: plugin_manifest: The manifest of the plugin to resolve dependencies for resolve_transitives: Whether to resolve transitive dependencies fetch_missing: Whether to fetch missing dependencies from repositories

Returns: A list of tuples (plugin_name, version, is_local) for dependencies in the order they should be loaded

Raises: DependencyError: If there's an error resolving dependencies"""
```
```python
    def resolve_plugin_order(self, plugin_manifests) -> List[str]:
        """Resolve the order in which plugins should be loaded.

Args: plugin_manifests: A dictionary mapping plugin names to manifests

Returns: A list of plugin names in the order they should be loaded

Raises: CircularDependencyError: If a circular dependency is detected"""
```
```python
    def set_core_version(self, version) -> None:
        """Set the core version."""
```
```python
    def set_installed_plugins(self, plugins) -> None:
        """Set the installed plugins."""
```
```python
    def set_plugins_dir(self, plugins_dir) -> None:
        """Set the plugins directory."""
```

```python
class IncompatibleVersionError(DependencyError):
    """Error raised when a dependency has an incompatible version."""
```
*Methods:*
```python
    def __init__(self, plugin_name, dependency_name, required_version, available_version):
```

```python
class MissingDependencyError(DependencyError):
    """Error raised when a required dependency is missing."""
```
*Methods:*
```python
    def __init__(self, plugin_name, dependency_name, required_version):
```

#### Module: extension
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/extension.py`

**Imports:**
```python
from __future__ import annotations
import importlib
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, Protocol, cast
from dataclasses import dataclass, field
from qorzen.plugin_system.manifest import PluginExtensionPoint, PluginManifest
```

**Global Variables:**
```python
extension_registry = extension_registry = ExtensionRegistry()
```

**Functions:**
```python
def call_extension_point(provider, extension_id, *args, **kwargs) -> Dict[(str, Any)]:
    """Call all implementations of an extension point.

Args: provider: The name of the plugin providing the extension point extension_id: The unique identifier for the extension point *args: Positional arguments to pass to the implementations **kwargs: Keyword arguments to pass to the implementations

Returns: A dictionary mapping plugin names to results

Raises: ExtensionPointNotFoundError: If the extension point is not found"""
```

```python
def get_extension_point(provider, extension_id) -> Optional[ExtensionInterface]:
    """Get an extension point.

Args: provider: The name of the plugin providing the extension point extension_id: The unique identifier for the extension point

Returns: The extension interface, or None if not found"""
```

```python
def register_extension_point(provider, id, name, description, interface, version, parameters, provider_instance) -> ExtensionInterface:
    """Register an extension point.

Args: provider: The name of the plugin providing the extension point id: The unique identifier for the extension point name: The human-readable name of the extension point description: A description of the extension point interface: The interface definition (e.g., function signature or class) version: The version of the extension point parameters: Additional parameters for the extension point provider_instance: The instance of the provider plugin

Returns: The registered extension interface"""
```

```python
def register_plugin_extensions(plugin_name, plugin_instance, manifest) -> None:
    """Register all extension points and uses for a plugin.

Args: plugin_name: The name of the plugin plugin_instance: The instance of the plugin manifest: The plugin manifest"""
```

```python
def unregister_plugin_extensions(plugin_name) -> None:
    """Unregister all extension points and uses for a plugin.  Args: plugin_name: The name of the plugin"""
```

**Classes:**
```python
class ExtensionImplementation(Protocol):
    """Protocol defining the interface for an extension implementation."""
```
*Methods:*
```python
    def __call__(self, *args, **kwargs) -> Any:
        """Execute the extension implementation."""
```

```python
class ExtensionInterface(object):
    """Represents an extension point interface that plugins can implement."""
```
*Methods:*
```python
    def __call__(self, *args, **kwargs) -> Dict[(str, Any)]:
        """Call all implementations and return the results."""
```
```python
    def __init__(self, provider, extension_point, provider_instance):
```
```python
    def get_all_implementations(self) -> Dict[(str, ExtensionImplementation)]:
        """Get all implementations for this extension point."""
```
```python
    def get_implementation(self, plugin_name) -> Optional[ExtensionImplementation]:
        """Get a specific implementation by plugin name."""
```
```python
    def register_implementation(self, plugin_name, implementation) -> None:
        """Register an implementation for this extension point."""
```
```python
    def unregister_implementation(self, plugin_name) -> None:
        """Unregister an implementation for this extension point."""
```

```python
class ExtensionPointNotFoundError(Exception):
    """Exception raised when an extension point is not found."""
```
*Methods:*
```python
    def __init__(self, provider, extension_id):
```

```python
class ExtensionPointVersionError(Exception):
    """Exception raised when there's a version incompatibility with an extension point."""
```
*Methods:*
```python
    def __init__(self, provider, extension_id, required, available):
```

```python
@dataclass
class ExtensionRegistry(object):
    """Registry of all extension points and their implementations."""
```
*Methods:*
```python
    def __post_init__(self) -> None:
        """Initialize the registry."""
```
```python
    def get_all_extension_points(self) -> Dict[(str, Dict[(str, ExtensionInterface)])]:
        """Get all registered extension points."""
```
```python
    def get_extension_point(self, provider, extension_id) -> Optional[ExtensionInterface]:
        """Get an extension point by provider and ID."""
```
```python
    def get_provider_extension_points(self, provider) -> Dict[(str, ExtensionInterface)]:
        """Get all extension points for a specific provider."""
```
```python
    def log(self, message, level) -> None:
        """Log a message."""
```
```python
    def register_extension_point(self, provider, extension_point, provider_instance) -> None:
        """Register an extension point."""
```
```python
    def register_extension_use(self, consumer, consumer_id, provider, extension_id, version, implementation, required) -> None:
        """Register a plugin's use of an extension point."""
```
```python
    def register_plugin_extensions(self, plugin_name, plugin_instance, manifest) -> None:
        """Register all extension points and uses for a plugin."""
```
```python
    def unregister_extension_point(self, provider, extension_id) -> None:
        """Unregister an extension point."""
```
```python
    def unregister_extension_use(self, consumer, provider, extension_id) -> None:
        """Unregister a plugin's use of an extension point."""
```
```python
    def unregister_plugin_extensions(self, plugin_name) -> None:
        """Unregister all extension points and uses for a plugin."""
```

#### Module: installer
*Plugin installation and management.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/installer.py`

**Imports:**
```python
from __future__ import annotations
import datetime
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from qorzen.plugin_system.manifest import PluginManifest, PluginDependency
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginVerifier
```

**Classes:**
```python
@dataclass
class InstalledPlugin(object):
    """Information about an installed plugin.

Attributes: manifest: Plugin manifest install_path: Path to the installed plugin directory installed_at: When the plugin was installed enabled: Whether the plugin is enabled plugin_data: Plugin-specific data"""
```
*Methods:*
```python
    def __post_init__(self) -> None:
        """Initialize default values."""
```
```python
@classmethod
    def from_dict(cls, data) -> InstalledPlugin:
        """Create an InstalledPlugin from a dictionary.

Args: data: Dictionary with installed plugin data

Returns: InstalledPlugin instance"""
```
```python
    def to_dict(self) -> Dict[(str, Any)]:
        """Convert to a dictionary.  Returns: Dictionary representation of the installed plugin"""
```

```python
class PluginInstallationError(Exception):
    """Exception raised for errors during plugin installation."""
```

```python
class PluginInstaller(object):
    """Handler for installing and managing plugins.

This class provides utilities for installing, updating, and removing plugin packages in the Qorzen system.

Attributes: plugins_dir: Directory where plugins are installed verifier: Plugin verifier for signature verification installed_plugins: Dictionary of installed plugins by name"""
```
*Methods:*
```python
    def __init__(self, plugins_dir, verifier, logger) -> None:
        """Initialize the plugin installer.

Args: plugins_dir: Directory where plugins will be installed verifier: Plugin verifier for signature verification logger: Logger function for recording installation events"""
```
```python
    def disable_plugin(self, plugin_name) -> bool:
        """Disable a plugin.

Args: plugin_name: Name of the plugin to disable

Returns: True if the plugin was disabled, False otherwise"""
```
```python
    def enable_plugin(self, plugin_name) -> bool:
        """Enable a plugin.

Args: plugin_name: Name of the plugin to enable

Returns: True if the plugin was enabled, False otherwise"""
```
```python
    def get_enabled_plugins(self) -> Dict[(str, InstalledPlugin)]:
        """Get information about enabled plugins.  Returns: Dictionary of enabled plugins by name"""
```
```python
    def get_installed_plugin(self, plugin_name) -> Optional[InstalledPlugin]:
        """Get information about an installed plugin.

Args: plugin_name: Name of the plugin

Returns: Installed plugin information, or None if not installed"""
```
```python
    def get_installed_plugins(self) -> Dict[(str, InstalledPlugin)]:
        """Get information about all installed plugins.  Returns: Dictionary of installed plugins by name"""
```
```python
    def get_plugin_dir(self, plugin_name) -> Path:
        """Get the directory for a plugin.

Args: plugin_name: Name of the plugin

Returns: Path to the plugin directory"""
```
```python
    def install_plugin(self, package_path, force, skip_verification, enable) -> InstalledPlugin:
        """Install a plugin from a package.

Args: package_path: Path to the plugin package force: Whether to force installation (overwrite existing) skip_verification: Whether to skip signature verification enable: Whether to enable the plugin after installation

Returns: Installed plugin information

Raises: PluginInstallationError: If installation fails"""
```
```python
    def is_plugin_installed(self, plugin_name) -> bool:
        """Check if a plugin is installed.

Args: plugin_name: Name of the plugin to check

Returns: True if the plugin is installed, False otherwise"""
```
```python
    def load_installed_plugins(self) -> None:
        """Load information about installed plugins.

This reads the installed plugins metadata file and populates the installed_plugins dictionary."""
```
```python
    def log(self, message, level) -> None:
        """Log a message.  Args: message: Message to log level: Log level (info, warning, error, debug)"""
```
```python
    def resolve_dependencies(self, package_path, repository_url) -> Dict[(str, Union[(str, bool)])]:
        """Resolve dependencies for a plugin package.

Args: package_path: Path to the plugin package repository_url: URL of the plugin repository

Returns: Dictionary mapping dependency names to status or package path

Raises: PluginInstallationError: If dependency resolution fails"""
```
```python
    def save_installed_plugins(self) -> None:
        """Save information about installed plugins.

This writes the installed plugins metadata to the metadata file."""
```
```python
    def uninstall_plugin(self, plugin_name, keep_data) -> bool:
        """Uninstall a plugin.

Args: plugin_name: Name of the plugin to uninstall keep_data: Whether to keep plugin data

Returns: True if the plugin was uninstalled, False otherwise

Raises: PluginInstallationError: If uninstallation fails"""
```
```python
    def update_plugin(self, package_path, skip_verification) -> InstalledPlugin:
        """Update an installed plugin.

Args: package_path: Path to the updated plugin package skip_verification: Whether to skip signature verification

Returns: Updated plugin information

Raises: PluginInstallationError: If update fails"""
```

#### Module: integration
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/integration.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import os
import tempfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, cast
import re
import semver
from qorzen.plugin_system.dependency import DependencyResolver, DependencyError
from qorzen.plugin_system.installer import PluginInstaller, PluginInstallationError, InstalledPlugin
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook, PluginDependency
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.repository import PluginRepositoryManager, PluginRepositoryError
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.lifecycle import execute_hook, LifecycleHookError, PluginLifecycleState, set_plugin_state
```

**Classes:**
```python
class IntegratedPluginInstaller(object):
    """Handles plugin installation, updates, and dependency management asynchronously. Integrates with the plugin lifecycle system."""
```
*Methods:*
```python
    def __init__(self, plugins_dir, repository_manager, verifier, logger, core_version):
        """Initialize the async integrated plugin installer.

Args: plugins_dir: Directory where plugins are installed repository_manager: Optional repository manager for downloading plugins verifier: Optional verifier for plugin package verification logger: Optional logger function core_version: The core application version"""
```
```python
    async def disable_plugin(self, plugin_name) -> bool:
        """Disable a plugin.

Args: plugin_name: The name of the plugin

Returns: bool: True if the plugin was disabled"""
```
```python
    async def enable_plugin(self, plugin_name) -> bool:
        """Enable a plugin.

Args: plugin_name: The name of the plugin

Returns: bool: True if the plugin was enabled"""
```
```python
    def get_enabled_plugins(self) -> Dict[(str, InstalledPlugin)]:
        """Get all enabled plugins.  Returns: Dict[str, InstalledPlugin]: Dictionary of enabled plugins"""
```
```python
    def get_installed_plugin(self, plugin_name) -> Optional[InstalledPlugin]:
        """Get information about an installed plugin.

Args: plugin_name: The name of the plugin

Returns: Optional[InstalledPlugin]: The installed plugin if found, None otherwise"""
```
```python
    def get_installed_plugins(self) -> Dict[(str, InstalledPlugin)]:
        """Get all installed plugins.  Returns: Dict[str, InstalledPlugin]: Dictionary of installed plugins"""
```
```python
    async def get_loading_order(self) -> List[str]:
        """Get the order in which plugins should be loaded based on dependencies.

Returns: List[str]: Ordered list of plugin names"""
```
```python
    async def install_plugin(self, package_path, force, skip_verification, enable, resolve_dependencies, install_dependencies) -> InstalledPlugin:
        """Install a plugin from a package.

Args: package_path: Path to the plugin package force: Force installation even if already installed skip_verification: Skip package verification enable: Enable the plugin after installation resolve_dependencies: Resolve plugin dependencies install_dependencies: Install missing dependencies

Returns: InstalledPlugin: Information about the installed plugin

Raises: PluginInstallationError: If installation fails"""
```
```python
    def is_plugin_installed(self, plugin_name) -> bool:
        """Check if a plugin is installed.

Args: plugin_name: The name of the plugin

Returns: bool: True if the plugin is installed"""
```
```python
    def log(self, message, level) -> None:
        """Log a message with the specified level."""
```
```python
    async def resolve_dependencies(self, package_path, repository_url) -> Dict[(str, Union[(str, bool)])]:
        """Resolve dependencies for a plugin package.

Args: package_path: Path to the plugin package repository_url: Optional specific repository URL

Returns: Dict[str, Union[str, bool]]: Dictionary of dependencies and their status

Raises: PluginInstallationError: If dependency resolution fails"""
```
```python
    async def uninstall_plugin(self, plugin_name, keep_data, check_dependents) -> bool:
        """Uninstall a plugin.

Args: plugin_name: The name of the plugin keep_data: Keep plugin data after uninstallation check_dependents: Check for and prevent uninstallation if other plugins depend on this one

Returns: bool: True if the plugin was uninstalled

Raises: PluginInstallationError: If uninstallation fails"""
```
```python
    async def update_plugin(self, package_path, skip_verification, resolve_dependencies, install_dependencies) -> InstalledPlugin:
        """Update a plugin from a package.

Args: package_path: Path to the plugin package skip_verification: Skip package verification resolve_dependencies: Resolve plugin dependencies install_dependencies: Install missing dependencies

Returns: InstalledPlugin: Information about the updated plugin

Raises: PluginInstallationError: If update fails"""
```

```python
class PluginIntegrationError(Exception):
    """Exception raised for errors in the plugin integration process.

Attributes: message: The error message plugin_name: Optional name of the affected plugin cause: Optional original exception that caused this error"""
```
*Methods:*
```python
    def __init__(self, message, plugin_name, cause):
```

#### Module: interface
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/interface.py`

**Imports:**
```python
from __future__ import annotations
import abc
import asyncio
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Set, Callable, Awaitable
from PySide6.QtCore import QObject
```

**Classes:**
```python
class BasePlugin(QObject):
    """Base class for plugins providing common functionality."""
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the plugin."""
```
```python
    async def execute_task(self, task_name, *args, **kwargs) -> Optional[str]:
        """Execute a registered task.

Args: task_name: The name of the task to execute *args: Positional arguments for the task **kwargs: Keyword arguments for the task

Returns: Optional[str]: The task ID if execution was successful, None otherwise"""
```
```python
    def get_registered_tasks(self) -> Set[str]:
        """Get the set of registered tasks.  Returns: Set[str]: The set of registered task names"""
```
```python
    async def initialize(self, application_core, **kwargs) -> None:
```
```python
    async def on_ui_ready(self, ui_integration) -> None:
        """Called when the UI is ready for plugin integration.

Args: ui_integration: The UI integration instance"""
```
```python
    async def register_task(self, task_name, function, **properties) -> None:
        """Register a task with the task manager.

Args: task_name: The name of the task function: The function to execute **properties: Additional task properties"""
```
```python
    async def register_ui_component(self, component, component_type) -> Any:
        """Register a UI component.

Args: component: The UI component to register component_type: The type of component

Returns: Any: The registered component"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the plugin asynchronously."""
```
```python
    async def status(self) -> Dict[(str, Any)]:
        """Get the current status of the plugin.  Returns: Dict[str, Any]: The plugin status information"""
```

```python
@runtime_checkable
class PluginInterface(Protocol):
    """Protocol defining the expected interface for plugins."""
```
*Methods:*
```python
    async def initialize(self, application_core) -> None:
        """Initialize the plugin asynchronously."""
```
```python
    async def on_ui_ready(self, ui_integration) -> None:
        """Called when the UI is ready for plugin integration."""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the plugin asynchronously."""
```

#### Module: lifecycle
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/lifecycle.py`

**Imports:**
```python
from __future__ import annotations
import abc
import asyncio
import importlib
import inspect
import weakref
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
from qorzen.plugin_system.manifest import PluginLifecycleHook, PluginManifest
from qorzen.ui.ui_integration import UIIntegration
from qorzen.core.dependency_manager import DependencyManager
```

**Functions:**
```python
async def cleanup_ui(plugin_name) -> bool:
    """Clean up UI components for a plugin using the global lifecycle manager."""
```

```python
async def execute_hook(hook, plugin_name, manifest, plugin_instance, context, **kwargs) -> Any:
    """Execute a lifecycle hook for a plugin using the global lifecycle manager.

Args: hook: The lifecycle hook to execute plugin_name: The name of the plugin manifest: The plugin manifest plugin_instance: Optional plugin instance context: Optional context dictionary **kwargs: Additional context parameters

Returns: Any: The result of the hook execution"""
```

```python
async def find_plugin_hooks(plugin_instance) -> Dict[(PluginLifecycleHook, str)]:
    """Find hooks defined in a plugin instance using the global lifecycle manager."""
```

```python
def get_lifecycle_manager() -> LifecycleManager:
    """Get the global lifecycle manager instance. Creates a new instance if one doesn't exist.

Returns: AsyncLifecycleManager: The global lifecycle manager instance"""
```

```python
async def get_plugin_state(plugin_name) -> PluginLifecycleState:
    """Get the current state of a plugin using the global lifecycle manager."""
```

```python
async def get_ui_integration(plugin_name) -> Optional[UIIntegration]:
    """Get the UI integration for a plugin using the global lifecycle manager."""
```

```python
async def register_ui_integration(plugin_name, ui_integration, main_window) -> None:
    """Register a UI integration for a plugin using the global lifecycle manager."""
```

```python
def set_logger(logger) -> None:
    """Set the logger for the global lifecycle manager."""
```

```python
def set_plugin_manager(plugin_manager) -> None:
    """Set the plugin manager for the global lifecycle manager."""
```

```python
async def set_plugin_state(plugin_name, state) -> None:
    """Set the state of a plugin using the global lifecycle manager."""
```

```python
def set_thread_manager(thread_manager) -> None:
    """Set the thread manager for the global lifecycle manager."""
```

```python
async def signal_ui_ready(plugin_name) -> None:
    """Signal that the UI is ready for a plugin using the global lifecycle manager."""
```

```python
async def wait_for_ui_ready(plugin_name, timeout) -> bool:
    """Wait for the UI to be ready for a plugin using the global lifecycle manager."""
```

**Classes:**
```python
class LifecycleHookError(Exception):
    """Exception raised when a lifecycle hook fails."""
```
*Methods:*
```python
    def __init__(self, hook, plugin_name, message):
```

```python
class LifecycleManager(object):
    """Manages the lifecycle of plugins asynchronously. Handles state transitions, UI integration, and lifecycle hooks."""
```
*Methods:*
```python
    def __init__(self, logger_manager):
        """Initialize the async lifecycle manager.  Args: logger_manager: Optional logger manager for logging"""
```
```python
    async def cleanup_ui(self, plugin_name) -> bool:
        """Clean up UI components for a plugin.

Args: plugin_name: The name of the plugin

Returns: bool: True if cleanup was successful"""
```
```python
    async def execute_hook(self, hook, plugin_name, manifest, plugin_instance, context) -> Any:
        """Execute a lifecycle hook for a plugin.

Args: hook: The lifecycle hook to execute plugin_name: The name of the plugin manifest: The plugin manifest plugin_instance: Optional plugin instance context: Optional context dictionary

Returns: Any: The result of the hook execution

Raises: LifecycleHookError: If the hook execution fails"""
```
```python
    async def find_plugin_hooks(self, plugin_instance) -> Dict[(PluginLifecycleHook, str)]:
        """Find hooks defined in a plugin instance.

Args: plugin_instance: The plugin instance

Returns: Dict[PluginLifecycleHook, str]: Dictionary mapping hooks to method names"""
```
```python
    async def get_plugin_state(self, plugin_name) -> PluginLifecycleState:
        """Get the current state of a plugin.

Args: plugin_name: The name of the plugin

Returns: PluginLifecycleState: The current state of the plugin"""
```
```python
    async def get_ui_integration(self, plugin_name) -> Optional[UIIntegration]:
        """Get the UI integration for a plugin.

Args: plugin_name: The name of the plugin

Returns: Optional[UIIntegration]: The UI integration instance if found"""
```
```python
    def log(self, message, level) -> None:
        """Log a message with the specified level."""
```
```python
    async def register_ui_integration(self, plugin_name, ui_integration, main_window) -> None:
        """Register a UI integration for a plugin.

Args: plugin_name: The name of the plugin ui_integration: The UI integration instance main_window: Optional main window reference"""
```
```python
    def set_logger(self, logger) -> None:
        """Set the logger instance."""
```
```python
    def set_plugin_manager(self, plugin_manager) -> None:
        """Set the plugin manager reference."""
```
```python
    async def set_plugin_state(self, plugin_name, state) -> None:
        """Set the state of a plugin.  Args: plugin_name: The name of the plugin state: The new state to set"""
```
```python
    def set_thread_manager(self, thread_manager) -> None:
        """Set the thread manager used for main thread operations."""
```
```python
    async def signal_ui_ready(self, plugin_name) -> None:
        """Signal that the UI is ready for a plugin.  Args: plugin_name: The name of the plugin"""
```
```python
    async def wait_for_ui_ready(self, plugin_name, timeout) -> bool:
        """Wait for the UI to be ready for a plugin.

Args: plugin_name: The name of the plugin timeout: Optional timeout in seconds

Returns: bool: True if the UI is ready, False if timed out"""
```

```python
class PluginLifecycleState(Enum):
    """States in a plugin's lifecycle."""
```
*Class attributes:*
```python
DISCOVERED =     DISCOVERED = auto()
LOADING =     LOADING = auto()
INITIALIZING =     INITIALIZING = auto()
INITIALIZED =     INITIALIZED = auto()
UI_READY =     UI_READY = auto()
ACTIVE =     ACTIVE = auto()
DISABLING =     DISABLING = auto()
INACTIVE =     INACTIVE = auto()
FAILED =     FAILED = auto()
```

#### Module: manifest
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/manifest.py`

**Imports:**
```python
from __future__ import annotations
import enum
import datetime
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, TYPE_CHECKING
import pydantic
from pydantic import Field, validator
from qorzen.plugin_system.config_schema import ConfigSchema
```

**Classes:**
```python
class PluginAuthor(pydantic.BaseModel):
```
*Methods:*
```python
@validator('email')
    def validate_email(cls, v) -> str:
```
```python
@validator('url')
    def validate_url(cls, v) -> Optional[str]:
```

```python
class PluginCapability(str, enum.Enum):
```
*Class attributes:*
```python
CONFIG_READ = 'config.read'
CONFIG_WRITE = 'config.write'
UI_EXTEND = 'ui.extend'
EVENT_SUBSCRIBE = 'event.subscribe'
EVENT_PUBLISH = 'event.publish'
FILE_READ = 'file.read'
FILE_WRITE = 'file.write'
NETWORK_CONNECT = 'network.connect'
DATABASE_READ = 'database.read'
DATABASE_WRITE = 'database.write'
SYSTEM_EXEC = 'system.exec'
SYSTEM_MONITOR = 'system.monitor'
PLUGIN_COMMUNICATE = 'plugin.communicate'
```
*Methods:*
```python
@classmethod
    def get_description(cls, capability) -> str:
```
```python
@classmethod
    def get_risk_level(cls, capability) -> str:
```

```python
class PluginDependency(pydantic.BaseModel):
```
*Methods:*
```python
@validator('version')
    def validate_version(cls, v) -> str:
```

```python
class PluginExtensionPoint(pydantic.BaseModel):
    """Definition of an extension point provided by the plugin."""
```
*Methods:*
```python
@validator('id')
    def validate_id(cls, v) -> str:
```
```python
@validator('version')
    def validate_version(cls, v) -> str:
```

```python
class PluginExtensionUse(pydantic.BaseModel):
    """Definition of an extension point that the plugin uses."""
```
*Methods:*
```python
@validator('version')
    def validate_version(cls, v) -> str:
```

```python
class PluginLifecycleHook(str, enum.Enum):
    """Enumeration of plugin lifecycle hooks."""
```
*Class attributes:*
```python
PRE_INSTALL = 'pre_install'
POST_INSTALL = 'post_install'
PRE_UNINSTALL = 'pre_uninstall'
POST_UNINSTALL = 'post_uninstall'
PRE_ENABLE = 'pre_enable'
POST_ENABLE = 'post_enable'
PRE_DISABLE = 'pre_disable'
POST_DISABLE = 'post_disable'
PRE_UPDATE = 'pre_update'
POST_UPDATE = 'post_update'
```

```python
class PluginManifest(pydantic.BaseModel):
```
*Methods:*
```python
    def get_capability_risks(self) -> Dict[(str, List[str])]:
```
```python
    def get_extension_point(self, extension_id) -> Optional[PluginExtensionPoint]:
        """Get an extension point by ID."""
```
```python
    def has_extension_point(self, extension_id) -> bool:
        """Check if the plugin provides a specific extension point."""
```
```python
    def is_compatible_with_core(self, core_version) -> bool:
```
```python
@classmethod
    def load(cls, path) -> PluginManifest:
```
```python
    def satisfies_dependency(self, dependency) -> bool:
```
```python
    def save(self, path) -> None:
```
```python
    def set_config_schema(self, schema) -> None:
        """Set the configuration schema for the plugin."""
```
```python
    def to_dict(self) -> Dict[(str, Any)]:
```
```python
    def to_json(self) -> str:
```
```python
@validator('min_core_version', 'max_core_version')
    def validate_core_version(cls, v) -> Optional[str]:
```
```python
@validator('license')
    def validate_license(cls, v) -> str:
```
```python
@validator('lifecycle_hooks')
    def validate_lifecycle_hooks(cls, v) -> Dict[(PluginLifecycleHook, str)]:
        """Validate that lifecycle hook values are valid callable paths."""
```
```python
@validator('name')
    def validate_name(cls, v) -> str:
```
```python
@validator('version')
    def validate_version(cls, v) -> str:
```

#### Module: package
*Plugin package management for Qorzen.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/package.py`

**Imports:**
```python
from __future__ import annotations
import enum
import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, BinaryIO, Any
from qorzen.plugin_system.manifest import PluginManifest
```

**Classes:**
```python
class PackageError(Exception):
    """Exception raised for errors in plugin packaging."""
```

```python
class PackageFormat(str, enum.Enum):
    """Format for plugin packages.  These formats determine how the plugin is packaged and distributed."""
```
*Class attributes:*
```python
ZIP = 'zip'
WHEEL = 'wheel'
DIRECTORY = 'directory'
```

```python
class PluginPackage(object):
    """Plugin package handler.

This class provides methods for creating, extracting, and managing plugin packages.

Attributes: manifest: Plugin manifest format: Package format path: Path to the package file or directory"""
```
*Class attributes:*
```python
MANIFEST_PATH = 'manifest.json'
CODE_DIR = 'code'
RESOURCES_DIR = 'resources'
DOCS_DIR = 'docs'
```
*Methods:*
```python
    def __del__(self) -> None:
        """Clean up temporary files when the object is destroyed."""
```
```python
    def __init__(self, manifest, format, path) -> None:
        """Initialize a plugin package.

Args: manifest: Plugin manifest format: Package format path: Path to the package file or directory"""
```
```python
    def cleanup(self) -> None:
        """Clean up temporary files."""
```
```python
@classmethod
    def create(cls, source_dir, output_path, manifest, format, include_patterns, exclude_patterns) -> PluginPackage:
        """Create a plugin package from a source directory.

Args: source_dir: Directory containing the plugin source code output_path: Path where the package will be created manifest: Plugin manifest (if None, will be loaded from source_dir) format: Package format include_patterns: Glob patterns for files to include exclude_patterns: Glob patterns for files to exclude

Returns: Created plugin package

Raises: PackageError: If package creation fails"""
```
```python
    def extract(self, output_dir) -> Path:
        """Extract the package to a directory.

Args: output_dir: Directory where the package will be extracted

Returns: Path to the extracted package

Raises: PackageError: If package extraction fails"""
```
```python
    def get_code_dir(self) -> Optional[Path]:
        """Get the path to the code directory in the extracted package.

Returns: Path to the code directory, or None if not extracted"""
```
```python
    def get_docs_dir(self) -> Optional[Path]:
        """Get the path to the docs directory in the extracted package.

Returns: Path to the docs directory, or None if not extracted"""
```
```python
    def get_resources_dir(self) -> Optional[Path]:
        """Get the path to the resources directory in the extracted package.

Returns: Path to the resources directory, or None if not extracted"""
```
```python
@classmethod
    def load(cls, path) -> PluginPackage:
        """Load a plugin package from a file or directory.

Args: path: Path to the package file or directory

Returns: Loaded plugin package

Raises: PackageError: If package loading fails"""
```
```python
    def verify_integrity(self) -> bool:
        """Verify the integrity of the package files.

This checks that all files in the package match their expected hashes.

Returns: True if all files match their hashes, False otherwise"""
```

#### Module: plugin_state_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/plugin_state_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import importlib
import inspect
import os
import pathlib
import sys
import time
import traceback
import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union, cast, Tuple
from qorzen.core.base import QorzenManager
from qorzen.core.error_handler import ErrorHandler, ErrorSeverity, create_error_boundary
from qorzen.utils.exceptions import PluginError, ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
class PluginStateManager(object):
    """Helper class to manage plugin state transitions and avoid race conditions. This class acts as a state machine coordinator for plugins, ensuring that state transitions are atomic and consistent."""
```
*Methods:*
```python
    def __init__(self, plugin_manager, logger):
        """Initialize the plugin state manager.

Args: plugin_manager: Reference to the plugin manager instance logger: Optional logger instance for logging state transitions"""
```
```python
    async def get_active_transition(self, plugin_id) -> Optional[str]:
        """Get the name of the active transition for a plugin, if any.

Args: plugin_id: Unique identifier of the plugin

Returns: Optional[str]: Transition name or None if not transitioning"""
```
```python
    async def get_pending_operations(self, plugin_id) -> Set[str]:
        """Get the set of pending operations for a plugin.

Args: plugin_id: Unique identifier of the plugin

Returns: Set[str]: Set of operation names"""
```
```python
    async def is_transitioning(self, plugin_id) -> bool:
        """Check if a plugin is currently in a state transition.

Args: plugin_id: Unique identifier of the plugin

Returns: bool: True if transitioning, False otherwise"""
```
```python
    async def transition(self, plugin_id, target_state, current_state) -> bool:
        """Safely transition a plugin to the target state, handling all intermediate states.

Args: plugin_id: Unique identifier of the plugin target_state: The desired final state current_state: Optional current state if known; will be retrieved if not provided

Returns: bool: True if transition succeeded, False otherwise"""
```

#### Module: repository
*Plugin repository client and management.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/repository.py`

**Imports:**
```python
from __future__ import annotations
import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import httpx
from qorzen.plugin_system.manifest import PluginManifest
from qorzen.plugin_system.package import PluginPackage, PackageFormat
```

**Classes:**
```python
class PluginRepository(object):
    """Client for interacting with a plugin repository.

This class provides methods for searching, downloading, and publishing plugins to a repository.

Attributes: name: Repository name url: Repository URL api_key: Optional API key for authenticated operations timeout: Request timeout in seconds"""
```
*Methods:*
```python
    def __del__(self) -> None:
        """Clean up resources when the object is destroyed."""
```
```python
    def __init__(self, name, url, api_key, timeout, logger) -> None:
        """Initialize a plugin repository client.

Args: name: Repository name url: Repository URL api_key: Optional API key for authenticated operations timeout: Request timeout in seconds logger: Logger function for recording repository events"""
```
```python
    def download_plugin(self, plugin_name, version, output_path) -> Path:
        """Download a plugin package from the repository.

Args: plugin_name: Name of the plugin version: Specific version to download (default: latest) output_path: Path where the package will be saved

Returns: Path to the downloaded package

Raises: PluginRepositoryError: If the download fails"""
```
```python
    def get_plugin_info(self, plugin_name) -> Dict[(str, Any)]:
        """Get detailed information about a plugin.

Args: plugin_name: Name of the plugin

Returns: Dictionary with plugin information

Raises: PluginRepositoryError: If the request fails"""
```
```python
    def get_plugin_versions(self, plugin_name) -> List[PluginVersionInfo]:
        """Get version information for a plugin.

Args: plugin_name: Name of the plugin

Returns: List of version information

Raises: PluginRepositoryError: If the request fails"""
```
```python
    def log(self, message, level) -> None:
        """Log a message.  Args: message: Message to log level: Log level (info, warning, error, debug)"""
```
```python
    def publish_plugin(self, package_path, release_notes, public) -> Dict[(str, Any)]:
        """Publish a plugin package to the repository.

Args: package_path: Path to the plugin package release_notes: Release notes for this version public: Whether the plugin should be public

Returns: Dictionary with publish response

Raises: PluginRepositoryError: If the publish fails"""
```
```python
    def search(self, query, tags, sort_by, limit, offset) -> List[PluginSearchResult]:
        """Search for plugins in the repository.

Args: query: Search query tags: List of tags to filter by sort_by: Sort order (relevance, downloads, rating, name) limit: Maximum number of results offset: Result offset for pagination

Returns: List of search results

Raises: PluginRepositoryError: If the search fails"""
```

```python
class PluginRepositoryError(Exception):
    """Exception raised for errors in repository operations."""
```

```python
class PluginRepositoryManager(object):
    """Manager for multiple plugin repositories.

This class provides a unified interface for searching and downloading plugins from multiple repositories.

Attributes: repositories: Dictionary of repository clients by name default_repository: Name of the default repository"""
```
*Methods:*
```python
    def __init__(self, config_file, logger) -> None:
        """Initialize a plugin repository manager.

Args: config_file: Path to a repository configuration file logger: Logger function for recording repository events"""
```
```python
    def add_repository(self, repository) -> None:
        """Add a repository to the manager.

Args: repository: Repository client to add

Raises: PluginRepositoryError: If a repository with the same name already exists"""
```
```python
    def download_plugin(self, plugin_name, version, repository, output_path) -> Path:
        """Download a plugin package from a repository.

Args: plugin_name: Name of the plugin version: Specific version to download (default: latest) repository: Name of the repository to download from output_path: Path where the package will be saved

Returns: Path to the downloaded package

Raises: PluginRepositoryError: If the download fails"""
```
```python
    def get_repository(self, name) -> PluginRepository:
        """Get a repository client by name or the default repository.

Args: name: Name of the repository to get (default: default repository)

Returns: Repository client

Raises: PluginRepositoryError: If the repository does not exist"""
```
```python
    def load_config(self, config_file) -> None:
        """Load repository configuration from a file.

Args: config_file: Path to a repository configuration file

Raises: PluginRepositoryError: If the configuration cannot be loaded"""
```
```python
    def log(self, message, level) -> None:
        """Log a message.  Args: message: Message to log level: Log level (info, warning, error, debug)"""
```
```python
    def publish_plugin(self, package_path, release_notes, public, repository) -> Dict[(str, Any)]:
        """Publish a plugin package to a repository.

Args: package_path: Path to the plugin package release_notes: Release notes for this version public: Whether the plugin should be public repository: Name of the repository to publish to

Returns: Dictionary with publish response

Raises: PluginRepositoryError: If the publish fails"""
```
```python
    def remove_repository(self, name) -> bool:
        """Remove a repository from the manager.

Args: name: Name of the repository to remove

Returns: True if the repository was removed, False if not found"""
```
```python
    def save_config(self, config_file) -> None:
        """Save repository configuration to a file.

Args: config_file: Path where the configuration will be saved

Raises: PluginRepositoryError: If the configuration cannot be saved"""
```
```python
    def search(self, query, tags, repository, sort_by, limit, offset) -> Dict[(str, List[PluginSearchResult])]:
        """Search for plugins across repositories.

Args: query: Search query tags: List of tags to filter by repository: Name of the repository to search (default: all repositories) sort_by: Sort order (relevance, downloads, rating, name) limit: Maximum number of results per repository offset: Result offset for pagination

Returns: Dictionary mapping repository names to search results

Raises: PluginRepositoryError: If no repositories are available"""
```

```python
class PluginSearchResult(object):
    """Result of a plugin search in a repository.

Attributes: name: Plugin name display_name: Human-readable name version: Latest version description: Brief description author: Author name downloads: Number of downloads rating: Average rating (0-5) capabilities: List of requested capabilities tags: List of tags"""
```
*Methods:*
```python
    def __init__(self, name, display_name, version, description, author, downloads, rating, capabilities, tags) -> None:
        """Initialize a plugin search result.

Args: name: Plugin name display_name: Human-readable name version: Latest version description: Brief description author: Author name downloads: Number of downloads rating: Average rating (0-5) capabilities: List of requested capabilities tags: List of tags"""
```
```python
@classmethod
    def from_dict(cls, data) -> PluginSearchResult:
        """Create a search result from a dictionary.

Args: data: Dictionary with search result data

Returns: PluginSearchResult instance"""
```
```python
    def to_dict(self) -> Dict[(str, Any)]:
        """Convert to a dictionary.  Returns: Dictionary representation of the search result"""
```

```python
class PluginVersionInfo(object):
    """Information about a plugin version.

Attributes: name: Plugin name version: Version string release_date: Release date release_notes: Release notes download_url: URL to download the package size_bytes: Package size in bytes sha256: SHA-256 hash of the package dependencies: List of dependencies"""
```
*Methods:*
```python
    def __init__(self, name, version, release_date, release_notes, download_url, size_bytes, sha256, dependencies) -> None:
        """Initialize a plugin version info.

Args: name: Plugin name version: Version string release_date: Release date release_notes: Release notes download_url: URL to download the package size_bytes: Package size in bytes sha256: SHA-256 hash of the package dependencies: List of dependencies"""
```
```python
@classmethod
    def from_dict(cls, data) -> PluginVersionInfo:
        """Create a version info from a dictionary.

Args: data: Dictionary with version info data

Returns: PluginVersionInfo instance"""
```
```python
    def to_dict(self) -> Dict[(str, Any)]:
        """Convert to a dictionary.  Returns: Dictionary representation of the version info"""
```

#### Module: signing
*Plugin signing and verification utilities.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/signing.py`

**Imports:**
```python
from __future__ import annotations
import base64
import datetime
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from qorzen.plugin_system.manifest import PluginManifest
from qorzen.plugin_system.package import PluginPackage
```

**Classes:**
```python
class PluginSigner(object):
    """Tool for signing plugin packages.

This class provides methods for generating signing keys and signing plugin packages.

Attributes: key: Signing key"""
```
*Methods:*
```python
    def __init__(self, key) -> None:
        """Initialize a plugin signer.  Args: key: Signing key to use (if None, a new key will be generated)"""
```
```python
@staticmethod
    def generate_key(name) -> SigningKey:
        """Generate a new signing key.

Args: name: Name for the key

Returns: Generated signing key

Raises: SigningError: If key generation fails"""
```
```python
@staticmethod
    def load_key(path) -> SigningKey:
        """Load a signing key from a file.

Args: path: Path to the key file

Returns: Loaded signing key

Raises: SigningError: If key loading fails"""
```
```python
    def save_key(self, path, include_private) -> None:
        """Save the signing key to a file.

Args: path: Path where the key will be saved include_private: Whether to include the private key

Raises: SigningError: If key saving fails"""
```
```python
    def sign_manifest(self, manifest) -> None:
        """Sign a plugin manifest.

This adds a signature to the manifest that can be verified later.

Args: manifest: Plugin manifest to sign

Raises: SigningError: If signing fails"""
```
```python
    def sign_package(self, package) -> None:
        """Sign a plugin package.

This signs the package manifest and updates the package.

Args: package: Plugin package to sign

Raises: SigningError: If signing fails"""
```

```python
class PluginVerifier(object):
    """Tool for verifying signed plugin packages.

This class provides methods for verifying plugin signatures and managing trusted keys.

Attributes: trusted_keys: List of trusted public keys for verification"""
```
*Methods:*
```python
    def __init__(self, trusted_keys) -> None:
        """Initialize a plugin verifier.  Args: trusted_keys: List of trusted keys for verification"""
```
```python
    def add_trusted_key(self, key) -> None:
        """Add a trusted key for verification.  Args: key: Key to add to the trusted keys list"""
```
```python
    def load_trusted_keys(self, directory) -> int:
        """Load trusted keys from a directory.

Args: directory: Directory containing key files

Returns: Number of keys loaded

Raises: VerificationError: If key loading fails"""
```
```python
    def remove_trusted_key(self, fingerprint) -> bool:
        """Remove a trusted key.

Args: fingerprint: Fingerprint of the key to remove

Returns: True if the key was removed, False if not found"""
```
```python
    def verify_manifest(self, manifest) -> bool:
        """Verify a signed plugin manifest.

Args: manifest: Plugin manifest to verify

Returns: True if the manifest signature is valid, False otherwise

Raises: VerificationError: If verification fails due to an error"""
```
```python
    def verify_package(self, package) -> bool:
        """Verify a signed plugin package.

This verifies both the manifest signature and file integrity.

Args: package: Plugin package to verify

Returns: True if the package is valid, False otherwise

Raises: VerificationError: If verification fails due to an error"""
```

```python
class SigningError(Exception):
    """Exception raised for errors in plugin signing."""
```

```python
@dataclass
class SigningKey(object):
    """Key pair for signing and verifying plugins.

Attributes: name: Name of the key private_key: Private key (used for signing) public_key: Public key (used for verification) created_at: When the key was created fingerprint: Key fingerprint"""
```

```python
class VerificationError(Exception):
    """Exception raised for errors in plugin verification."""
```

#### Module: tools
*Developer tools for Qorzen plugins.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/tools.py`

**Imports:**
```python
from __future__ import annotations
import datetime
import inspect
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from qorzen.plugin_system.manifest import PluginManifest, PluginAuthor, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, SigningKey
```

**Functions:**
```python
def create_plugin_signing_key(name, output_path) -> SigningKey:
    """Create a new plugin signing key.

Args: name: Name for the key output_path: Path where the key will be saved

Returns: Created signing key"""
```

```python
def create_plugin_template(output_dir, plugin_name, display_name, description, author_name, author_email, author_url, version, license, force) -> Path:
    """Create a new plugin template.

This generates a basic plugin structure with the necessary files for a Qorzen plugin.

Args: output_dir: Directory where the plugin template will be created plugin_name: Unique identifier for the plugin display_name: Human-readable name for the plugin description: Brief description of the plugin author_name: Plugin author's name author_email: Plugin author's email author_url: Plugin author's website URL version: Initial plugin version license: License identifier force: Whether to overwrite existing files

Returns: Path to the created plugin template directory

Raises: ValueError: If the plugin name is invalid or output directory exists"""
```

```python
def package_plugin(plugin_dir, output_path, format, signing_key, include_patterns, exclude_patterns) -> Path:
    """Package a plugin directory into a distributable package.

Args: plugin_dir: Directory containing the plugin output_path: Path where the package will be created format: Package format signing_key: Signing key or path to a key file include_patterns: Glob patterns for files to include exclude_patterns: Glob patterns for files to exclude

Returns: Path to the created package

Raises: ValueError: If plugin directory is invalid"""
```

```python
def test_plugin(plugin_dir, mock_env, test_pattern) -> bool:
    """Run tests for a plugin.

Args: plugin_dir: Directory containing the plugin mock_env: Whether to use a mocked Qorzen environment test_pattern: Pattern for test files

Returns: True if all tests pass, False otherwise"""
```

```python
def validate_plugin(plugin_dir) -> Dict[(str, List[str])]:
    """Validate a plugin directory.

This checks for common issues and best practices.

Args: plugin_dir: Directory containing the plugin

Returns: Dictionary of validation issues by category (errors, warnings, info)"""
```

#### Module: ui_registry
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/ui_registry.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
```

**Classes:**
```python
class UIComponentRegistry(object):
    """Registry for UI components. Manages UI elements added by plugins and handles cleanup when plugins are unloaded."""
```
*Methods:*
```python
    def __init__(self, plugin_name, thread_manager) -> None:
        """Initialize the UI component registry.

Args: plugin_name: The name of the plugin this registry belongs to thread_manager: Optional thread manager for main thread operations"""
```
```python
    async def cleanup(self) -> None:
        """Clean up all registered UI components asynchronously. This removes components from the UI and clears all registries."""
```
```python
    def register(self, component, component_type) -> Any:
        """Register a UI component.

Args: component: The UI component to register component_type: The type of component

Returns: Any: The registered component"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the registry and clean up all components."""
```

### Package: plugins
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins`

**__init__.py:**
*Plugin system for extending the Qorzen platform functionality.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/__init__.py`

**Imports:**
```python
from importlib.metadata import entry_points
```

#### Package: application_launcher
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/application_launcher`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/application_launcher/__init__.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.plugins.application_launcher.code.plugin import ApplicationLauncherPlugin
```

**Global Variables:**
```python
__version__ = '1.0.0'
__all__ = __all__ = ['ApplicationLauncherPlugin']
```

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/application_launcher/code`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/application_launcher/code/__init__.py`

**Imports:**
```python
from __future__ import annotations
```

###### Module: events
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/application_launcher/code/events.py`

**Imports:**
```python
from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional
```

**Functions:**
```python
def create_app_added_event(app_id, app_name) -> Dict[(str, Any)]:
    """Create payload for app added event.

Args: app_id: The application ID app_name: The application name

Returns: Event payload dictionary"""
```

```python
def create_app_completed_event(app_id, app_name, exit_code, runtime_seconds, output_files) -> Dict[(str, Any)]:
    """Create payload for app completed event.

Args: app_id: The application ID app_name: The application name exit_code: The process exit code runtime_seconds: Runtime in seconds output_files: List of output files produced

Returns: Event payload dictionary"""
```

```python
def create_app_launched_event(app_id, app_name, command_line, working_dir) -> Dict[(str, Any)]:
    """Create payload for app launched event.

Args: app_id: The application ID app_name: The application name command_line: The command line used to launch the app working_dir: Working directory, if specified

Returns: Event payload dictionary"""
```

**Classes:**
```python
class AppLauncherEventType(str, Enum):
    """Event types for the Application Launcher plugin."""
```
*Class attributes:*
```python
APP_ADDED = 'application_launcher:app_added'
APP_UPDATED = 'application_launcher:app_updated'
APP_REMOVED = 'application_launcher:app_removed'
APP_LAUNCHED = 'application_launcher:app_launched'
APP_TERMINATED = 'application_launcher:app_terminated'
APP_COMPLETED = 'application_launcher:app_completed'
OUTPUT_DETECTED = 'application_launcher:output_detected'
```
*Methods:*
```python
@classmethod
    def app_added(cls) -> str:
        """Get app added event type."""
```
```python
@classmethod
    def app_completed(cls) -> str:
        """Get app completed event type."""
```
```python
@classmethod
    def app_launched(cls) -> str:
        """Get app launched event type."""
```
```python
@classmethod
    def app_removed(cls) -> str:
        """Get app removed event type."""
```
```python
@classmethod
    def app_terminated(cls) -> str:
        """Get app terminated event type."""
```
```python
@classmethod
    def app_updated(cls) -> str:
        """Get app updated event type."""
```
```python
@classmethod
    def output_detected(cls) -> str:
        """Get output detected event type."""
```

###### Module: plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/application_launcher/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from pydantic import BaseModel, Field, validator
from PySide6.QtCore import QDir, QProcess, QProcessEnvironment, Qt, Signal, Slot, QTimer, QUrl, QObject, QFileInfo
from PySide6.QtGui import QAction, QDesktopServices, QFont, QIcon, QColor
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QPushButton, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QToolButton, QVBoxLayout, QWidget, QScrollArea
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.file_manager import FileManager
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_integration import UIIntegration
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from qorzen.utils.exceptions import PluginError
```

**Classes:**
```python
class ApplicationCard(QWidget):
    """Card widget displaying an application that can be launched."""
```
*Class attributes:*
```python
launchClicked =     launchClicked = Signal(ApplicationConfig)
editClicked =     editClicked = Signal(ApplicationConfig)
deleteClicked =     deleteClicked = Signal(ApplicationConfig)
```
*Methods:*
```python
    def __init__(self, app_config, parent) -> None:
        """Initialize the application card.

Args: app_config: The application configuration parent: Parent widget"""
```

```python
@dataclass
class ApplicationConfig(object):
    """Configuration for an external application."""
```

```python
class ApplicationConfigDialog(QDialog):
    """Dialog for configuring an application."""
```
*Methods:*
```python
    def __init__(self, app_config, parent) -> None:
        """Initialize the application configuration dialog.

Args: app_config: Existing application configuration to edit, or None for new parent: Parent widget"""
```
```python
    def get_config(self) -> ApplicationConfig:
        """Get the updated application configuration from the dialog."""
```

```python
class ApplicationLauncherPlugin(BasePlugin):
    """Plugin for launching external applications with configurable arguments.

This plugin allows users to configure and launch external applications, specifying command line arguments and viewing the console output and output files."""
```
*Class attributes:*
```python
name = 'application_launcher'
version = '1.0.0'
description = 'Launch external applications with configurable arguments'
author = 'Qorzen Developer'
display_name = 'Application Launcher'
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the application launcher plugin."""
```
```python
    def get_icon(self) -> Optional[str]:
        """Get the plugin icon path.  Returns: The icon path or None if not set"""
```
```python
    def get_main_widget(self) -> Optional[QWidget]:
        """Get the main widget instance.  Returns: The main widget or None if not created"""
```
```python
    async def initialize(self, application_core, **kwargs) -> None:
        """Initialize the plugin.

Args: application_core: The application core instance **kwargs: Additional keyword arguments"""
```
```python
    async def on_ui_ready(self, ui_integration) -> None:
        """Set up UI components when UI is ready.  Args: ui_integration: The UI integration instance"""
```
```python
    async def setup_ui(self, ui_integration) -> None:
        """Set up UI components (legacy method).  Args: ui_integration: The UI integration instance"""
```
```python
    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
```

```python
class ApplicationLauncherWidget(QWidget):
    """Main widget for the Application Launcher plugin."""
```
*Methods:*
```python
    def __init__(self, event_bus_manager, concurrency_manager, task_manager, file_manager, logger, parent) -> None:
        """Initialize the application launcher widget.

Args: event_bus_manager: Event bus manager for pub/sub events concurrency_manager: Concurrency manager for async tasks task_manager: Task manager for background tasks file_manager: File manager for file operations logger: Logger instance parent: Parent widget"""
```
```python
    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
```

```python
class ApplicationRunDialog(QDialog):
    """Dialog for configuring arguments and running an application."""
```
*Methods:*
```python
    def __init__(self, app_config, app_runner, parent) -> None:
        """Initialize the application run dialog.

Args: app_config: The application configuration app_runner: The application runner to use parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
```

```python
class ApplicationRunner(QObject):
    """Handles running external applications and capturing their output."""
```
*Class attributes:*
```python
processStarted =     processStarted = Signal()
processFinished =     processFinished = Signal(ProcessOutput)
processError =     processError = Signal(str)
stdoutReceived =     stdoutReceived = Signal(str)
stderrReceived =     stderrReceived = Signal(str)
outputFilesDetected =     outputFilesDetected = Signal(list)
```
*Methods:*
```python
    def __init__(self, concurrency_manager, file_manager, parent) -> None:
        """Initialize the application runner.

Args: concurrency_manager: The concurrency manager for running async tasks file_manager: The file manager for handling files parent: Parent QObject"""
```
```python
    def run_application(self, app_config, arg_values) -> None:
        """Run an application with the given configuration and arguments.

Args: app_config: The application configuration arg_values: Dictionary of argument values"""
```
```python
    def terminate_process(self) -> None:
        """Terminate the current process if running."""
```

```python
@dataclass
class ArgumentConfig(object):
    """Configuration for a command-line argument."""
```

```python
class ArgumentInputWidget(QWidget):
    """Widget for configuring a single command line argument."""
```
*Class attributes:*
```python
valueChanged =     valueChanged = Signal(str)
```
*Methods:*
```python
    def __init__(self, arg_config, parent) -> None:
        """Initialize the argument input widget.

Args: arg_config: The configuration for this argument parent: Parent widget"""
```
```python
    def get_value(self) -> str:
        """Get the current argument value."""
```

```python
class ArgumentType(str, Enum):
    """Type of command line argument."""
```
*Class attributes:*
```python
STATIC = 'static'
FILE_INPUT = 'file_input'
FILE_OUTPUT = 'file_output'
DIRECTORY = 'directory'
TEXT_INPUT = 'text_input'
ENV_VAR = 'environment_variable'
```

```python
class ConsoleOutputWidget(QWidget):
    """Widget for displaying process console output."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the console output widget.  Args: parent: Parent widget"""
```
```python
    def append_stderr(self, text) -> None:
        """Append text to stderr display.  Args: text: Text to append"""
```
```python
    def append_stdout(self, text) -> None:
        """Append text to stdout display.  Args: text: Text to append"""
```
```python
    def clear(self) -> None:
        """Clear all output and reset display."""
```
```python
    def process_finished(self, exit_code) -> None:
        """Update UI when process finishes.  Args: exit_code: Process exit code"""
```
```python
    def process_terminated(self) -> None:
        """Update UI when process is terminated."""
```
```python
    def start_process(self, command_line) -> None:
        """Start displaying output for a new process.  Args: command_line: The command line being executed"""
```

```python
class OutputFilesWidget(QWidget):
    """Widget for displaying and interacting with output files."""
```
*Class attributes:*
```python
fileOpened =     fileOpened = Signal(str)
```
*Methods:*
```python
    def set_files(self, file_paths) -> None:
        """Update the files display with the given paths.  Args: file_paths: List of file paths to display"""
```

```python
class ProcessOutput(BaseModel):
    """Model for process execution output."""
```

```python
class ProcessStatus(str, Enum):
    """Status of the process execution."""
```
*Class attributes:*
```python
NOT_STARTED = 'not_started'
RUNNING = 'running'
FINISHED = 'finished'
FAILED = 'failed'
TERMINATED = 'terminated'
```

###### Module: presets
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/application_launcher/code/presets.py`

**Imports:**
```python
from __future__ import annotations
import os
import platform
import shutil
from typing import Dict, List, Optional, Any
from plugin import ApplicationConfig, ArgumentConfig, ArgumentType
```

**Functions:**
```python
def create_custom_script_app(script_type, script_content, name, description, category) -> ApplicationConfig:
    """Create an application configuration for a custom script.

Args: script_type: Type of script ('bash', 'batch', 'python', etc.) script_content: Content of the script name: Name of the application description: Description of the application category: Category for the application

Returns: ApplicationConfig for the script"""
```

```python
def get_common_applications() -> List[ApplicationConfig]:
    """Get a list of common application presets based on the current platform.

Returns: List of ApplicationConfig objects for common applications"""
```

###### Module: process_utils
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/application_launcher/code/process_utils.py`

**Imports:**
```python
from __future__ import annotations
import os
import re
import platform
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any
```

**Classes:**
```python
@dataclass
class ProcessInfo(object):
    """Information about a running process."""
```

```python
class ProcessMonitor(object):
    """Monitor and manage external processes."""
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the process monitor."""
```
```python
@staticmethod
    def build_command_line(executable, arguments, environment) -> Tuple[(str, Dict[(str, str)])]:
        """Build a command line string and environment dictionary for process execution.

Args: executable: Path to the executable arguments: List of command line arguments environment: Optional environment variables dictionary

Returns: Tuple of (command_line_string, environment_dict)"""
```
```python
@staticmethod
    def create_temporary_script(script_content, script_type) -> Tuple[(str, str)]:
        """Create a temporary script file.

Args: script_content: The script content script_type: Type of script ('bash', 'batch', 'python', etc.)

Returns: Tuple of (file_path, executable)"""
```
```python
    def find_output_files(self, working_dir, patterns, base_timestamp) -> List[str]:
        """Find output files matching the given patterns that were modified after the base timestamp.

Args: working_dir: Working directory to search in patterns: List of glob patterns to match base_timestamp: Base timestamp to filter files by modification time

Returns: List of matching file paths"""
```
```python
    def get_process_info(self, pid) -> Optional[ProcessInfo]:
        """Get information about a specific process.

Args: pid: Process ID

Returns: ProcessInfo object or None if process not found"""
```
```python
    def limit_process_resources(self, pid, max_memory_mb) -> bool:
        """Apply resource limits to a running process.

Args: pid: Process ID max_memory_mb: Maximum memory limit in MB (None for no limit)

Returns: True if limits were applied successfully, False otherwise"""
```

#### Package: as400_connector_plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/__init__.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.plugins.as400_connector_plugin.code.plugin import AS400ConnectorPlugin
```

**Global Variables:**
```python
__version__ = '0.2.0'
__author__ = 'Ryan Serra'
__all__ = __all__ = ["__version__", "__author__", "AS400ConnectorPlugin"]
```

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/__init__.py`

###### Module: connector
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/connector.py`

**Imports:**
```python
from __future__ import annotations
import os
import re
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from functools import cache
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, ColumnMetadata, QueryResult
```

**Classes:**
```python
class AS400Connector(object):
    """Secure connector for AS400/iSeries databases using JT400 via JPype.

Implements multiple security layers: 1. SecretStr for password handling 2. Whitelist for allowed tables and schemas 3. Read-only operations only 4. SSL/TLS encryption when available 5. Timeouts to prevent hanging connections 6. Detailed audit logging"""
```
*Methods:*
```python
    def __init__(self, config, logger, security_manager) -> None:
        """Initialize the AS400 connector with secure configuration.

Args: config: Configuration for the AS400 connection logger: Logger for logging events security_manager: Optional security manager for encryption"""
```
```python
    async def close(self) -> None:
        """Safely close the AS400 connection.  Raises: DatabaseError: If closing the connection fails"""
```
```python
    async def connect(self) -> None:
        """Establish a secure connection to the AS400 database using JT400.

Raises: SecurityError: If security requirements aren't met DatabaseError: If connection fails ConfigurationError: If configuration is invalid"""
```
```python
    async def execute_query(self, query, limit, **params) -> QueryResult:
        """Securely execute a query on the AS400 system.

Args: query: SQL query or table name limit: Maximum number of records to return **params: Query parameters

Returns: QueryResult object containing the query results

Raises: SecurityError: If the query attempts to access unauthorized tables DatabaseError: If the query fails to execute"""
```
```python
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get information about the current connection.  Returns: Dictionary with connection information"""
```
```python
    async def get_schema_info(self, schema) -> List[Dict[(str, Any)]]:
        """Get schema information from the database.

Args: schema: Optional schema name, defaults to the configured database

Returns: List of tables in the schema with their details"""
```
```python
    def is_connected(self) -> bool:
        """Check if currently connected to the AS400 database.  Returns: True if connected, False otherwise"""
```

###### Module: models
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/models.py`

**Imports:**
```python
from __future__ import annotations
import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, cast
from pydantic import BaseModel, Field, SecretStr, validator, root_validator
```

**Classes:**
```python
class AS400ConnectionConfig(BaseModel):
    """Configuration for connecting to AS400/iSeries databases securely using JT400."""
```
*Methods:*
```python
@validator('allowed_tables', 'allowed_schemas')
    def validate_allowed_lists(cls, v) -> Optional[List[str]]:
        """Validate and normalize allowed lists."""
```
```python
@validator('port')
    def validate_port(cls, v) -> Optional[int]:
        """Validate port is within allowed range."""
```

```python
@dataclass
class ColumnMetadata(object):
    """Type definition for column metadata."""
```

```python
class Config(object):
    """Pydantic config."""
```
*Class attributes:*
```python
validate_assignment = True
use_enum_values = True
```

```python
class PluginSettings(BaseModel):
    """Plugin settings model."""
```

```python
class QueryHistoryEntry(BaseModel):
    """Model for tracking query execution history."""
```

```python
@dataclass
class QueryResult(object):
    """Container for query results."""
```

```python
class QueryResultsFormat(str, Enum):
    """Enumeration of available query result formats."""
```
*Class attributes:*
```python
TABLE = 'table'
JSON = 'json'
CSV = 'csv'
XML = 'xml'
```

```python
class SavedQuery(BaseModel):
    """Model for a saved SQL query with metadata."""
```

###### Module: plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Set, cast
from pathlib import Path
from PySide6.QtWidgets import QMenu, QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import QMetaObject, Qt, Slot, QObject, Signal
from qorzen.core.event_model import EventType
from qorzen.plugins.as400_connector_plugin.code.ui.as400_tab import AS400Tab
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration
```

**Classes:**
```python
class AS400ConnectorPlugin(BasePlugin):
```
*Class attributes:*
```python
ui_ready_signal =     ui_ready_signal = Signal(object)  # Signal to pass main window from event to main thread
name = 'as400_connector_plugin'
version = '0.1.0'
description = 'Connect and query AS400/iSeries databases'
author = 'Qorzen Team'
dependencies =     dependencies = []
```
*Methods:*
```python
    def __init__(self) -> None:
```
```python
    def initialize(self, event_bus_manager, logger_provider, config_provider, file_manager, thread_manager, database_manager, security_manager, **kwargs) -> None:
```
```python
    def on_ui_ready(self, ui_integration) -> None:
        """Set up UI components when UI is ready.  Args: ui_integration: The UI integration."""
```
```python
    def shutdown(self) -> None:
```
```python
    def status(self) -> Dict[(str, Any)]:
```

###### Module: utils
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/utils.py`

**Imports:**
```python
from __future__ import annotations
import os
import json
import re
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set, cast
from PySide6.QtCore import QSettings, QByteArray
from PySide6.QtGui import QColor
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, SavedQuery, QueryHistoryEntry, PluginSettings
```

**Functions:**
```python
def detect_query_parameters(query) -> List[str]:
    """Detect named parameters in a SQL query.

Args: query: SQL query text

Returns: List of parameter names"""
```

```python
def format_execution_time(ms) -> str:
    """Format execution time in milliseconds to a human-readable string.

Args: ms: Execution time in milliseconds

Returns: Formatted time string"""
```

```python
def format_value_for_display(value) -> str:
    """Format a value for display in the UI.

Args: value: The value to format

Returns: Formatted string representation of the value"""
```

```python
def get_sql_keywords() -> List[str]:
    """Get a list of SQL keywords for syntax highlighting.  Returns: List of SQL keywords"""
```

```python
def get_syntax_highlighting_colors() -> Dict[(str, QColor)]:
    """Get colors for SQL syntax highlighting.  Returns: Dictionary mapping syntax elements to colors"""
```

```python
def guess_jar_locations() -> List[str]:
    """Guess potential locations for the JT400 JAR file.  Returns: List of potential file paths"""
```

```python
def load_connections(file_manager) -> Dict[(str, AS400ConnectionConfig)]:
    """Load saved AS400 connection configurations.

Args: file_manager: Qorzen file manager for file operations

Returns: Dictionary of connection configurations by ID"""
```

```python
def load_plugin_settings(config_manager) -> PluginSettings:
    """Load plugin settings from the configuration manager.

Args: config_manager: Qorzen configuration manager

Returns: Plugin settings object"""
```

```python
def load_query_history(file_manager, limit) -> List[QueryHistoryEntry]:
    """Load query execution history.

Args: file_manager: Qorzen file manager for file operations limit: Maximum number of history entries to return

Returns: List of query history entries, newest first"""
```

```python
def load_saved_queries(file_manager) -> Dict[(str, SavedQuery)]:
    """Load saved SQL queries.

Args: file_manager: Qorzen file manager for file operations

Returns: Dictionary of saved queries by ID"""
```

```python
def save_connections(connections, file_manager) -> bool:
    """Save AS400 connection configurations.

Args: connections: Dictionary of connection configurations by ID file_manager: Qorzen file manager for file operations

Returns: True if successful, False otherwise"""
```

```python
def save_plugin_settings(settings, config_manager) -> bool:
    """Save plugin settings to the configuration manager.

Args: settings: Plugin settings object config_manager: Qorzen configuration manager

Returns: True if successful, False otherwise"""
```

```python
def save_queries(queries, file_manager) -> bool:
    """Save SQL queries.

Args: queries: Dictionary of saved queries by ID file_manager: Qorzen file manager for file operations

Returns: True if successful, False otherwise"""
```

```python
def save_query_history(history, file_manager, limit) -> bool:
    """Save query execution history.

Args: history: List of query history entries file_manager: Qorzen file manager for file operations limit: Maximum number of history entries to save

Returns: True if successful, False otherwise"""
```

###### Package: ui
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/ui`

**__init__.py:**
*UI components for the AS400 Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/ui/__init__.py`

**Imports:**
```python
from qorzen.plugins.as400_connector_plugin.code.ui.as400_tab import AS400Tab
```

**Global Variables:**
```python
__all__ = __all__ = ["AS400Tab"]
```

####### Module: as400_tab
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/ui/as400_tab.py`

**Imports:**
```python
from __future__ import annotations
import uuid
import os
import datetime
import json
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, QSize, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont, QTextCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit, QTextEdit, QToolBar, QStatusBar, QFileDialog, QMessageBox, QDialog, QGroupBox, QFormLayout, QCheckBox, QSpinBox, QDialogButtonBox, QMenu, QToolButton, QProgressBar, QListWidget, QListWidgetItem, QInputDialog, QRadioButton, QButtonGroup, QScrollArea
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig, SavedQuery, QueryHistoryEntry, PluginSettings, QueryResult
from qorzen.plugins.as400_connector_plugin.code.connector import AS400Connector
from qorzen.plugins.as400_connector_plugin.code.utils import load_connections, save_connections, load_saved_queries, save_queries, load_query_history, save_query_history, load_plugin_settings, save_plugin_settings, format_value_for_display, detect_query_parameters
from qorzen.plugins.as400_connector_plugin.code.ui.results_view import ResultsView
from qorzen.plugins.as400_connector_plugin.code.ui.visualization import VisualizationView
```

**Classes:**
```python
class AS400Tab(QWidget):
    """Main tab for the AS400 Connector Plugin.

Provides a complete UI for connecting to AS400 databases, executing SQL queries, and viewing results."""
```
*Class attributes:*
```python
queryStarted =     queryStarted = Signal(str)
queryFinished =     queryFinished = Signal(str, bool)
connectionChanged =     connectionChanged = Signal(str, bool)
```
*Methods:*
```python
    def __init__(self, event_bus_manager, logger, config, file_manager, thread_manager, security_manager, parent) -> None:
        """Initialize the AS400 tab.

Args: event_bus_manager: The event bus manager for event handling logger: Logger for logging events config: Configuration manager for settings file_manager: Optional file manager for file operations thread_manager: Optional thread manager for background tasks security_manager: Optional security manager for security operations parent: Optional parent widget"""
```
```python
    def export_queries(self) -> None:
        """Export saved queries to a file."""
```
```python
    def handle_config_change(self, key, value) -> None:
        """Handle configuration changes.  Args: key: The configuration key that changed value: The new value"""
```
```python
    def import_queries(self) -> None:
        """Import saved queries from a file."""
```
```python
    def open_connection_dialog(self) -> None:
        """Open the connection dialog."""
```
```python
    def open_connection_manager(self) -> None:
        """Open the connection management dialog."""
```

####### Module: connection_dialog
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/ui/connection_dialog.py`

**Imports:**
```python
from __future__ import annotations
import os
import uuid
from typing import Any, Dict, List, Optional, Set, cast
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox, QTabWidget, QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QSizePolicy, QComboBox
from qorzen.plugins.as400_connector_plugin.code.models import AS400ConnectionConfig
from qorzen.plugins.as400_connector_plugin.code.utils import guess_jar_locations
```

**Classes:**
```python
class ConnectionDialog(QDialog):
    """Dialog for creating or editing an AS400 connection.

Provides a form for configuring all AS400 connection parameters and testing the connection before saving."""
```
*Methods:*
```python
    def __init__(self, parent, file_manager, connection) -> None:
        """Initialize the connection dialog.

Args: parent: Parent widget file_manager: Optional file manager for file operations connection: Optional existing connection for editing"""
```
```python
    def get_connection_config(self) -> AS400ConnectionConfig:
        """Get the connection configuration from the dialog fields.

Returns: The AS400 connection configuration

Raises: ValueError: If any required fields are missing or invalid"""
```

```python
class ConnectionManagerDialog(QDialog):
    """Dialog for managing multiple AS400 connections.

Provides a list of connections with options to add, edit, delete, and set a default connection."""
```
*Methods:*
```python
    def __init__(self, connections, parent, file_manager) -> None:
        """Initialize the connection manager dialog.

Args: connections: Dictionary of existing connections by ID parent: Parent widget file_manager: Optional file manager for file operations"""
```
```python
    def get_connections(self) -> Dict[(str, AS400ConnectionConfig)]:
        """Get the updated connections.  Returns: Dictionary of connections by ID"""
```

####### Module: query_editor
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/ui/query_editor.py`

**Imports:**
```python
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import Qt, QRegularExpression, QSize
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter, QTextCursor, QKeyEvent, QTextDocument
from PySide6.QtWidgets import QTextEdit, QWidget, QCompleter, QAbstractItemView
from qorzen.plugins.as400_connector_plugin.code.utils import get_sql_keywords, get_syntax_highlighting_colors, detect_query_parameters
```

**Classes:**
```python
class SQLQueryEditor(QTextEdit):
    """Custom text editor for SQL queries with syntax highlighting.

Features include: - SQL syntax highlighting - Auto-indentation - Parameter highlighting - Auto-completion for SQL keywords"""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the SQL query editor.  Args: parent: Parent widget"""
```
```python
    def format_sql(self) -> None:
        """Format the SQL text with proper indentation and case."""
```
```python
    def get_detected_parameters(self) -> List[str]:
        """Get parameters detected in the current query.  Returns: List of parameter names"""
```
```python
    def keyPressEvent(self, event) -> None:
        """Handle key press events for special editor behavior.  Args: event: The key event"""
```
```python
    def set_dark_mode(self, enabled) -> None:
        """Toggle dark mode for the editor.  Args: enabled: Whether dark mode should be enabled"""
```

```python
class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for SQL in the query editor.

Highlights SQL keywords, strings, numbers, functions, comments, and query parameters."""
```
*Methods:*
```python
    def __init__(self, document) -> None:
        """Initialize the syntax highlighter.  Args: document: The text document to highlight"""
```
```python
    def highlightBlock(self, text) -> None:
        """Highlight a block of text according to the rules.  Args: text: The text to highlight"""
```

####### Module: results_view
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/ui/results_view.py`

**Imports:**
```python
from __future__ import annotations
import csv
import datetime
import io
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QAbstractTableModel, QEvent, QItemSelectionModel, QModelIndex, QObject, QPoint, QSortFilterProxyModel, Qt, Signal, Slot, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QContextMenuEvent, QFont, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QTableView, QToolBar, QVBoxLayout, QWidget
from qorzen.plugins.as400_connector_plugin.code.models import ColumnMetadata, QueryResult
from qorzen.plugins.as400_connector_plugin.code.utils import format_value_for_display
```

**Classes:**
```python
class DataPreviewDialog(QDialog):
    """Dialog for displaying a preview of a row's data.

This dialog shows all fields of a record in a vertical layout, making it easier to view large text fields or complex data."""
```
*Methods:*
```python
    def __init__(self, record, columns, parent) -> None:
        """Initialize the data preview dialog.

Args: record: The record to display columns: The column metadata for the record parent: Optional parent widget"""
```

```python
class QueryResultsTableModel(QAbstractTableModel):
    """Table model for displaying AS400 query results.

This model works with the QueryResult data structure and provides additional functionality like sorting, custom data formatting, and data type-specific rendering."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the table model.  Args: parent: Optional parent object"""
```
```python
    def columnCount(self, parent) -> int:
        """Return the number of columns in the model."""
```
```python
    def data(self, index, role) -> Any:
        """Return data for the given index and role.

Args: index: The model index to get data for role: The data role (display, edit, etc.)

Returns: The requested data or None if not available"""
```
```python
    def flags(self, index) -> Qt.ItemFlags:
        """Return the item flags for the given index."""
```
```python
    def getAllRecords(self) -> List[Dict[(str, Any)]]:
        """Return all records."""
```
```python
    def getColumnMetadata(self, column) -> Optional[ColumnMetadata]:
        """Return the metadata for the given column."""
```
```python
    def getColumnType(self, column) -> Optional[str]:
        """Return the data type for the given column."""
```
```python
    def getRecord(self, row) -> Optional[Dict[(str, Any)]]:
        """Return the record for the given row."""
```
```python
    def headerData(self, section, orientation, role) -> Any:
        """Return header data for the given section and orientation.

Args: section: The row or column number orientation: Qt.Horizontal or Qt.Vertical role: The data role

Returns: The header data or None if not available"""
```
```python
    def rowCount(self, parent) -> int:
        """Return the number of rows in the model."""
```
```python
    def setQueryResult(self, result) -> None:
        """Set the query result to be displayed in the model.

Args: result: The QueryResult instance containing data to display"""
```

```python
class ResultsFilterHeader(QHeaderView):
    """A custom header view that includes filter widgets.

This header adds filter input fields to allow filtering the table contents by column values."""
```
*Class attributes:*
```python
filterChanged =     filterChanged = Signal(int, str)
```
*Methods:*
```python
    def __init__(self, orientation, parent) -> None:
        """Initialize the filter header.

Args: orientation: The header orientation (horizontal or vertical) parent: Optional parent widget"""
```
```python
    def adjustPositions(self) -> None:
        """Adjust the positions of the filter boxes."""
```
```python
    def eventFilter(self, obj, event) -> bool:
        """Filter events to handle mouse events in the header."""
```
```python
    def sectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex) -> None:
        """Handle section move events."""
```
```python
    def sectionResized(self, logicalIndex, oldSize, newSize) -> None:
        """Handle section resize events."""
```
```python
    def setFilterBoxes(self, count) -> None:
        """Create filter boxes for each column.  Args: count: The number of columns to create filter boxes for"""
```
```python
    def sizeHint(self) -> QSize:
        """Return the size hint for the header."""
```
```python
    def updateCursor(self, pos) -> None:
        """Update the cursor based on the mouse position."""
```

```python
class ResultsFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering and sorting query results.

This model sits between the QueryResultsTableModel and the view, adding filtering and sorting capabilities."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the proxy model."""
```
```python
    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        """Determine if a row should be shown based on the current filters.

Args: source_row: The row in the source model source_parent: The parent index in the source model

Returns: True if the row should be shown, False otherwise"""
```
```python
    def setFilterText(self, column, text) -> None:
        """Set the filter text for a specific column.

Args: column: The column to filter text: The filter text"""
```

```python
class ResultsView(QWidget):
    """A view for displaying AS400 query results.

This widget provides a table view with sorting, filtering, and other features for working with query results."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the results view."""
```
```python
    def get_filtered_data(self) -> List[Dict[(str, Any)]]:
        """Get the data after applying filters.  Returns: List of records that pass the current filters"""
```
```python
    def get_query_result(self) -> Optional[QueryResult]:
        """Get the current query result.  Returns: The current QueryResult or None if no result is loaded"""
```
```python
    def set_query_result(self, result) -> None:
        """Set the query result to display.  Args: result: The QueryResult to display"""
```

####### Module: visualization
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/as400_connector_plugin/code/ui/visualization.py`

**Imports:**
```python
from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QAbstractTableModel, QItemSelection, QItemSelectionModel, QModelIndex, QObject, QPoint, QSize, Qt, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFrame, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSizePolicy, QSpinBox, QSplitter, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget
from qorzen.plugins.as400_connector_plugin.code.models import ColumnMetadata, QueryResult
```

**Classes:**
```python
class ChartConfigWidget(QWidget):
    """Widget for configuring chart settings.

This widget allows users to select columns for X and Y axes, chart type, and other visualization settings."""
```
*Class attributes:*
```python
chartConfigChanged =     chartConfigChanged = Signal()
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the chart configuration widget."""
```
```python
    def get_aggregation(self) -> str:
        """Return the selected aggregation method."""
```
```python
    def get_chart_type(self) -> str:
        """Return the selected chart type."""
```
```python
    def get_data_limit(self) -> int:
        """Return the maximum number of data points to display."""
```
```python
    def get_x_axis(self) -> str:
        """Return the selected X-axis column."""
```
```python
    def get_y_axis(self) -> str:
        """Return the selected Y-axis column."""
```
```python
    def set_columns(self, columns) -> None:
        """Set the available columns for chart configuration.

Args: columns: The list of columns from the query result"""
```
```python
    def show_data_labels(self) -> bool:
        """Return whether to show data labels."""
```
```python
    def show_legend(self) -> bool:
        """Return whether to show the legend."""
```

```python
class ChartWidget(QWidget):
    """Widget for displaying a chart.  This widget renders the chart based on the configuration and data."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the chart widget."""
```
```python
    def paintEvent(self, event) -> None:
        """Paint the chart.  Args: event: The paint event"""
```
```python
    def set_config(self, chart_type, x_axis, y_axis, aggregation, show_legend, show_data_labels, data_limit) -> None:
        """Set the chart configuration.

Args: chart_type: The type of chart to display x_axis: The column to use for X-axis y_axis: The column to use for Y-axis aggregation: The aggregation method to apply show_legend: Whether to show the legend show_data_labels: Whether to show data labels data_limit: Maximum number of data points to display"""
```
```python
    def set_data(self, result) -> None:
        """Set the data for the chart.  Args: result: The query result containing the data"""
```

```python
class VisualizationView(QWidget):
    """Main view for data visualization.

This widget combines the chart configuration panel and the chart display."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the visualization view."""
```
```python
    def set_query_result(self, result) -> None:
        """Set the query result to visualize.  Args: result: The QueryResult to visualize"""
```

#### Package: database_connector_plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/__init__.py`

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/__init__.py`

###### Module: models
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/models.py`

**Imports:**
```python
from __future__ import annotations
import datetime
import enum
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union, cast, Literal
from pydantic import BaseModel, Field, SecretStr, validator, root_validator
```

**Classes:**
```python
class AS400ConnectionConfig(BaseConnectionConfig):
    """AS400-specific connection configuration."""
```
*Methods:*
```python
@validator('allowed_tables', 'allowed_libraries')
    def validate_allowed_lists(cls, v) -> Optional[List[str]]:
```
```python
@validator('port')
    def validate_port(cls, v) -> Optional[int]:
```

```python
class BaseConnectionConfig(BaseModel):
    """Base configuration for all database connections."""
```

```python
@dataclass
class ColumnMetadata(object):
    """Metadata about a database column."""
```

```python
class Config(object):
```
*Class attributes:*
```python
validate_assignment = True
```

```python
class ConnectionType(str, enum.Enum):
    """Supported database connection types."""
```
*Class attributes:*
```python
AS400 = 'as400'
ODBC = 'odbc'
MYSQL = 'mysql'
POSTGRES = 'postgres'
SQLITE = 'sqlite'
ORACLE = 'oracle'
MSSQL = 'mssql'
```

```python
class FieldMapping(BaseModel):
    """Mapping of database fields to standardized names."""
```

```python
class HistoryEntry(BaseModel):
    """Historical data point."""
```

```python
class HistorySchedule(BaseModel):
    """Schedule for automatically collecting historical data."""
```

```python
class ODBCConnectionConfig(BaseConnectionConfig):
    """ODBC-specific connection configuration."""
```
*Methods:*
```python
@root_validator
    def validate_connection_info(cls, values) -> Dict[(str, Any)]:
```
```python
@validator('port')
    def validate_port(cls, v) -> Optional[int]:
```

```python
class PluginSettings(BaseModel):
    """Plugin settings and configuration."""
```

```python
class QueryHistoryEntry(BaseModel):
    """Record of a previously executed query."""
```

```python
@dataclass
class QueryResult(object):
    """Results of a database query."""
```

```python
class SQLConnectionConfig(BaseConnectionConfig):
    """Configuration for SQL-based databases (MySQL, PostgreSQL, etc.)."""
```
*Methods:*
```python
@validator('port')
    def validate_port(cls, v) -> Optional[int]:
```

```python
class SavedQuery(BaseModel):
    """Saved query configuration."""
```

```python
@dataclass
class TableMetadata(object):
    """Metadata about a database table."""
```

```python
class ValidationResult(BaseModel):
    """Result of a validation run."""
```

```python
class ValidationRule(BaseModel):
    """Rule for validating field data."""
```

```python
class ValidationRuleType(str, enum.Enum):
    """Types of validation rules that can be applied to data."""
```
*Class attributes:*
```python
RANGE = 'range'
PATTERN = 'pattern'
NOT_NULL = 'not_null'
UNIQUE = 'unique'
LENGTH = 'length'
REFERENCE = 'reference'
ENUMERATION = 'enumeration'
CUSTOM = 'custom'
```

###### Module: plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import json
import os
import logging
import datetime
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QMessageBox
from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from qorzen.utils.exceptions import PluginError, DatabaseError
from models import BaseConnectionConfig, AS400ConnectionConfig, ODBCConnectionConfig, ConnectionType, PluginSettings, SavedQuery, FieldMapping, ValidationRule, QueryResult
from connectors import BaseDatabaseConnector, get_connector_for_config
from ui.main_tab import DatabaseConnectorTab
from utils.mapping import apply_mapping_to_results
from utils.history import HistoryManager
from utils.validation import ValidationEngine
```

**Classes:**
```python
class DatabaseConnectorPlugin(BasePlugin):
    """Main plugin class for the Database Connector Plugin."""
```
*Class attributes:*
```python
name = 'database_connector_plugin'
version = '1.0.0'
description = 'Connect and query various databases with field mapping and validation capabilities'
author = 'Qorzen Team'
display_name = 'Database Connector'
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the plugin."""
```
```python
    async def delete_connection(self, connection_id) -> bool:
        """Delete a connection configuration.

Args: connection_id: Connection ID

Returns: True if deleted, False if not found

Raises: PluginError: If deletion fails"""
```
```python
    async def delete_field_mapping(self, mapping_id) -> bool:
        """Delete a field mapping.

Args: mapping_id: Mapping ID

Returns: True if deleted, False if not found

Raises: PluginError: If deletion fails"""
```
```python
    async def delete_query(self, query_id) -> bool:
        """Delete a saved query.

Args: query_id: Query ID

Returns: True if deleted, False if not found

Raises: PluginError: If deletion fails"""
```
```python
    async def disconnect(self, connection_id) -> bool:
        """Disconnect from a database.

Args: connection_id: Connection ID

Returns: True if disconnected, False if already disconnected or not found

Raises: PluginError: If disconnection fails"""
```
```python
    async def execute_query(self, connection_id, query, params, limit, mapping_id) -> QueryResult:
        """Execute a query against a database.

Args: connection_id: Connection ID query: SQL query params: Optional parameters limit: Optional result limit mapping_id: Optional field mapping ID to apply

Returns: Query result

Raises: PluginError: If execution fails"""
```
```python
    async def get_connection(self, connection_id) -> Optional[BaseConnectionConfig]:
        """Get a specific connection configuration.

Args: connection_id: Connection ID

Returns: Connection configuration or None if not found"""
```
```python
    async def get_connections(self) -> Dict[(str, BaseConnectionConfig)]:
        """Get all stored connections.  Returns: Dictionary of connection configurations"""
```
```python
    async def get_connector(self, connection_id) -> BaseDatabaseConnector:
        """Get a database connector for a connection. Creates the connector if it doesn't exist and connects if not connected.

Args: connection_id: Connection ID

Returns: Database connector

Raises: PluginError: If getting the connector fails"""
```
```python
    async def get_field_mapping(self, mapping_id) -> Optional[FieldMapping]:
        """Get a specific field mapping.

Args: mapping_id: Mapping ID

Returns: Field mapping or None if not found"""
```
```python
    async def get_field_mappings(self, connection_id, table_name) -> Dict[(str, FieldMapping)]:
        """Get all field mappings, optionally filtered.

Args: connection_id: Optional connection ID filter table_name: Optional table name filter

Returns: Dictionary of field mappings"""
```
```python
    async def get_history_manager(self) -> HistoryManager:
        """Get the history manager.  Returns: History manager"""
```
```python
    async def get_saved_queries(self, connection_id) -> Dict[(str, SavedQuery)]:
        """Get all saved queries, optionally filtered by connection.

Args: connection_id: Optional connection ID filter

Returns: Dictionary of saved queries"""
```
```python
    async def get_saved_query(self, query_id) -> Optional[SavedQuery]:
        """Get a specific saved query.  Args: query_id: Query ID  Returns: Saved query or None if not found"""
```
```python
    async def get_validation_engine(self) -> ValidationEngine:
        """Get the validation engine.  Returns: Validation engine"""
```
```python
    async def initialize(self, application_core, **kwargs) -> None:
        """Initialize the plugin.

Args: application_core: Application core instance **kwargs: Additional keyword arguments

Raises: PluginError: If initialization fails"""
```
```python
    async def on_ui_ready(self, ui_integration) -> None:
        """Set up UI components when the UI is ready.  Args: ui_integration: UI integration instance"""
```
```python
    async def save_connection(self, config) -> str:
        """Save a connection configuration.

Args: config: Connection configuration

Returns: Connection ID

Raises: PluginError: If saving fails"""
```
```python
    async def save_field_mapping(self, mapping) -> str:
        """Save a field mapping.

Args: mapping: Field mapping to save

Returns: Mapping ID

Raises: PluginError: If saving fails"""
```
```python
    async def save_query(self, query) -> str:
        """Save a query.  Args: query: Query to save  Returns: Query ID  Raises: PluginError: If saving fails"""
```
```python
    async def setup_ui(self, ui_integration) -> None:
        """Set up the UI (alias for on_ui_ready for compatibility).

Args: ui_integration: UI integration instance"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the plugin, cleaning up resources.  Raises: PluginError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get plugin status information.  Returns: Status dictionary"""
```
```python
    async def test_connection(self, config) -> Tuple[(bool, Optional[str])]:
        """Test a database connection.

Args: config: Connection configuration

Returns: Tuple of (success, error_message)"""
```

###### Package: connectors
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/connectors`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/connectors/__init__.py`

**Imports:**
```python
from __future__ import annotations
from typing import Dict, Type, Any
from models import BaseConnectionConfig, ConnectionType, AS400ConnectionConfig, ODBCConnectionConfig, SQLConnectionConfig
from base import BaseDatabaseConnector, DatabaseConnectorProtocol
from as400 import AS400Connector
from odbc import ODBCConnector
```

**Global Variables:**
```python
__all__ = __all__ = [
    "BaseDatabaseConnector",
    "DatabaseConnectorProtocol",
    "AS400Connector",
    "ODBCConnector",
    "get_connector_for_config",
]
```

**Functions:**
```python
def get_connector_for_config(config, logger, security_manager) -> BaseDatabaseConnector:
    """Create the appropriate connector instance for the given configuration.

Args: config: Database connection configuration logger: Logger instance security_manager: Optional security manager

Returns: Database connector instance

Raises: ValueError: If no connector is available for the connection type"""
```

####### Module: as400
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/connectors/as400.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import os
import re
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from models import AS400ConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
from base import BaseDatabaseConnector
```

**Classes:**
```python
class AS400Connector(BaseDatabaseConnector):
    """AS400 database connector using JT400 via JPype."""
```
*Methods:*
```python
    def __init__(self, config, logger, security_manager) -> None:
        """Initialize the AS400 connector.

Args: config: AS400 connection configuration logger: Logger instance security_manager: Optional security manager"""
```
```python
    async def connect(self) -> None:
        """Establish a connection to the AS400 database.

Raises: DatabaseError: If connection fails SecurityError: If authentication fails"""
```
```python
    async def disconnect(self) -> None:
        """Close the AS400 database connection.  Raises: DatabaseError: If closing the connection fails"""
```
```python
    async def execute_query(self, query, params, limit) -> QueryResult:
        """Execute a query against the AS400 database.

Args: query: SQL query to execute params: Optional parameters for the query limit: Optional row limit

Returns: QueryResult containing the results and metadata

Raises: DatabaseError: If query execution fails SecurityError: If query violates security constraints"""
```
```python
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get information about the current connection.  Returns: Dictionary with connection details"""
```
```python
    async def get_table_columns(self, table_name, schema) -> List[ColumnMetadata]:
        """Get a list of columns in the specified table.

Args: table_name: Table name schema: Schema/library name (defaults to connection database)

Returns: List of ColumnMetadata objects

Raises: DatabaseError: If retrieving columns fails"""
```
```python
    async def get_tables(self, schema) -> List[TableMetadata]:
        """Get a list of tables in the specified schema.

Args: schema: Schema/library name (defaults to connection database)

Returns: List of TableMetadata objects

Raises: DatabaseError: If retrieving tables fails"""
```

####### Module: base
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/connectors/base.py`

**Imports:**
```python
from __future__ import annotations
import abc
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Protocol, TypeVar
from models import BaseConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
```

**Global Variables:**
```python
TableList = TableList = List[TableMetadata]
FieldList = FieldList = List[ColumnMetadata]
T = T = TypeVar('T', bound=BaseConnectionConfig)
```

**Classes:**
```python
class BaseDatabaseConnector(abc.ABC):
    """Abstract base class for database connectors."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """Initialize the database connector.  Args: config: Connection configuration logger: Logger instance"""
```
```python
    async def cancel_query(self) -> bool:
        """Cancel the currently executing query if possible.

Returns: True if cancellation was successful, False otherwise"""
```
```python
@property
    def config(self) -> BaseConnectionConfig:
        """Return the connection configuration."""
```
```python
@abc.abstractmethod
    async def connect(self) -> None:
        """Establish a connection to the database.  Raises: DatabaseError: If connection fails"""
```
```python
@abc.abstractmethod
    async def disconnect(self) -> None:
        """Close the database connection.  Raises: DatabaseError: If closing the connection fails"""
```
```python
@abc.abstractmethod
    async def execute_query(self, query, params, limit) -> QueryResult:
        """Execute a SQL query against the database.

Args: query: The SQL query to execute params: Optional parameters to bind to the query limit: Optional row limit

Returns: QueryResult object containing the results and metadata

Raises: DatabaseError: If query execution fails SecurityError: If query violates security constraints"""
```
```python
@abc.abstractmethod
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get information about the current connection.  Returns: Dictionary with connection details"""
```
```python
@abc.abstractmethod
    async def get_table_columns(self, table_name, schema) -> FieldList:
        """Get a list of columns in the specified table.

Args: table_name: Name of the table schema: Optional schema/library name

Returns: List of ColumnMetadata objects

Raises: DatabaseError: If retrieving columns fails"""
```
```python
@abc.abstractmethod
    async def get_tables(self, schema) -> TableList:
        """Get a list of tables available in the database or schema.

Args: schema: Optional schema/library name to limit results

Returns: List of TableMetadata objects

Raises: DatabaseError: If retrieving tables fails"""
```
```python
@property
    def is_connected(self) -> bool:
        """Return True if the connection is active."""
```
```python
    async def test_connection(self) -> Tuple[(bool, Optional[str])]:
        """Test if the connection works.  Returns: Tuple of (success, error_message)"""
```

```python
class DatabaseConnectorProtocol(Protocol[T]):
    """Protocol defining the interface that all database connectors must implement."""
```
*Methods:*
```python
@property
    def config(self) -> T:
        """Return the connection configuration."""
```
```python
    async def connect(self) -> None:
        """Establish a connection to the database."""
```
```python
    async def disconnect(self) -> None:
        """Close the database connection."""
```
```python
    async def execute_query(self, query, params, limit) -> QueryResult:
        """Execute a SQL query against the database.

Args: query: The SQL query to execute params: Optional parameters to bind to the query limit: Optional row limit

Returns: QueryResult object containing the results and metadata"""
```
```python
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get information about the current connection.  Returns: Dictionary with connection details"""
```
```python
    async def get_table_columns(self, table_name, schema) -> FieldList:
        """Get a list of columns in the specified table.

Args: table_name: Name of the table schema: Optional schema/library name

Returns: List of ColumnMetadata objects"""
```
```python
    async def get_tables(self, schema) -> TableList:
        """Get a list of tables available in the database or schema.

Args: schema: Optional schema/library name to limit results

Returns: List of TableMetadata objects"""
```
```python
@property
    def is_connected(self) -> bool:
        """Return True if the connection is active."""
```
```python
    async def test_connection(self) -> Tuple[(bool, Optional[str])]:
        """Test if the connection works.  Returns: Tuple of (success, error_message)"""
```

####### Module: odbc
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/connectors/odbc.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from models import ODBCConnectionConfig, ColumnMetadata, QueryResult, TableMetadata
from base import BaseDatabaseConnector
```

**Classes:**
```python
class ODBCConnector(BaseDatabaseConnector):
    """ODBC database connector for FileMaker and other databases."""
```
*Methods:*
```python
    def __init__(self, config, logger, security_manager) -> None:
        """Initialize the ODBC connector.

Args: config: ODBC connection configuration logger: Logger instance security_manager: Optional security manager"""
```
```python
    async def connect(self) -> None:
        """Establish a connection to the database via ODBC.

Raises: DatabaseError: If connection fails SecurityError: If authentication fails"""
```
```python
    async def disconnect(self) -> None:
        """Close the database connection.  Raises: DatabaseError: If closing the connection fails"""
```
```python
    async def execute_query(self, query, params, limit) -> QueryResult:
        """Execute a query against the database.

Args: query: SQL query to execute params: Optional parameters for the query limit: Optional row limit

Returns: QueryResult containing the results and metadata

Raises: DatabaseError: If query execution fails SecurityError: If query violates security constraints"""
```
```python
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get information about the current connection.  Returns: Dictionary with connection details"""
```
```python
    async def get_table_columns(self, table_name, schema) -> List[ColumnMetadata]:
        """Get a list of columns in the specified table.

Args: table_name: Table name schema: Optional schema name

Returns: List of ColumnMetadata objects

Raises: DatabaseError: If retrieving columns fails"""
```
```python
    async def get_tables(self, schema) -> List[TableMetadata]:
        """Get a list of tables in the database.

Args: schema: Optional schema name

Returns: List of TableMetadata objects

Raises: DatabaseError: If retrieving tables fails"""
```

###### Package: ui
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/__init__.py`

####### Module: connection_dialog
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/connection_dialog.py`

**Imports:**
```python
from __future__ import annotations
import os
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox, QTabWidget, QWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem, QMessageBox, QToolButton, QSizePolicy, QComboBox, QStackedWidget, QFileDialog, QFrame
from models import BaseConnectionConfig, AS400ConnectionConfig, ODBCConnectionConfig, ConnectionType
```

**Functions:**
```python
def guess_jar_locations() -> List[str]:
    """Guess common locations for the jt400.jar file.  Returns: List of possible file paths"""
```

**Classes:**
```python
class ConnectionDialog(QDialog):
    """Dialog for creating or editing a database connection."""
```
*Methods:*
```python
    def __init__(self, parent, connection) -> None:
        """Initialize the connection dialog.

Args: parent: Parent widget connection: Optional existing connection to edit"""
```
```python
    def get_connection_config(self) -> BaseConnectionConfig:
        """Get the connection configuration from dialog fields.

Returns: Connection configuration

Raises: ValueError: If required fields are missing or invalid"""
```

```python
class ConnectionManagerDialog(QDialog):
    """Dialog for managing multiple database connections."""
```
*Methods:*
```python
    def __init__(self, connections, parent) -> None:
        """Initialize the connection manager dialog.

Args: connections: Dictionary of connection configurations parent: Parent widget"""
```
```python
    def get_connections(self) -> Dict[(str, BaseConnectionConfig)]:
        """Get the updated connection configurations.  Returns: Dictionary of connection configurations"""
```

####### Module: main_tab
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/main_tab.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import datetime
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTabWidget, QSplitter, QToolBar, QStatusBar, QMessageBox, QProgressBar, QMenu, QToolButton, QInputDialog, QFileDialog
from qorzen.utils.exceptions import DatabaseError, PluginError
from models import BaseConnectionConfig, AS400ConnectionConfig, ODBCConnectionConfig, ConnectionType, SavedQuery, FieldMapping, ValidationRule, QueryResult
from connection_dialog import ConnectionDialog, ConnectionManagerDialog
from query_editor import QueryEditorWidget
from field_mapping import FieldMappingWidget
from validation import ValidationWidget
from history import HistoryWidget
from results_view import ResultsView
```

**Classes:**
```python
class DatabaseConnectorTab(QWidget):
    """Main tab widget for the Database Connector Plugin."""
```
*Class attributes:*
```python
connectionChanged =     connectionChanged = Signal(str, bool)  # connection_id, connected
queryStarted =     queryStarted = Signal(str)  # connection_id
queryFinished =     queryFinished = Signal(str, bool)  # connection_id, success
```
*Methods:*
```python
    def __init__(self, plugin, logger, concurrency_manager, event_bus_manager, parent) -> None:
        """Initialize the Database Connector Tab.

Args: plugin: Plugin instance logger: Logger instance concurrency_manager: Concurrency manager for thread safety event_bus_manager: Event bus manager for event handling parent: Optional parent widget"""
```
```python
    def handle_config_change(self, key, value) -> None:
        """Handle configuration changes.  Args: key: Config key value: New value"""
```
```python
    def open_connection_manager(self) -> None:
        """Open the connection manager dialog."""
```
```python
    def switch_to_history(self) -> None:
        """Switch to the history tab."""
```
```python
    def switch_to_mapping_editor(self) -> None:
        """Switch to the field mapping tab."""
```
```python
    def switch_to_query_editor(self) -> None:
        """Switch to the query editor tab."""
```
```python
    def switch_to_results(self) -> None:
        """Switch to the results tab."""
```
```python
    def switch_to_validation(self) -> None:
        """Switch to the validation tab."""
```

####### Module: mapping_dialog
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/mapping_dialog.py`

####### Module: query_editor
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/query_editor.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, QRegularExpression, Signal, Slot, QSize
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter, QTextCursor, QKeyEvent, QTextDocument
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTextEdit, QListWidget, QListWidgetItem, QToolBar, QSpinBox, QFormLayout, QLineEdit, QInputDialog, QMessageBox, QMenu, QSplitter, QGroupBox, QTabWidget, QScrollArea, QFileDialog
from models import SavedQuery, FieldMapping
```

**Classes:**
```python
class QueryEditorWidget(QWidget):
    """Widget for editing and managing SQL queries."""
```
*Class attributes:*
```python
executeQueryRequested =     executeQueryRequested = Signal()
saveQueryRequested =     saveQueryRequested = Signal()
```
*Methods:*
```python
    def __init__(self, plugin, logger, parent) -> None:
        """Initialize the query editor widget.

Args: plugin: Plugin instance logger: Logger instance parent: Parent widget"""
```
```python
    def get_current_query_id(self) -> Optional[str]:
        """Get the ID of the currently displayed query.  Returns: Query ID or None if no query is displayed"""
```
```python
    def get_current_query_name(self) -> str:
        """Get the name of the currently displayed query.

Returns: Query name or empty string if no query is displayed"""
```
```python
    def get_limit(self) -> Optional[int]:
        """Get the result limit.  Returns: Limit or None if no limit"""
```
```python
    def get_mapping_id(self) -> Optional[str]:
        """Get the selected field mapping ID.  Returns: Field mapping ID or None if no mapping selected"""
```
```python
    def get_parameters(self) -> Dict[(str, Any)]:
        """Get the query parameters.  Returns: Dictionary of parameter name/value pairs"""
```
```python
    def get_query_text(self) -> str:
        """Get the current query text.  Returns: Query text"""
```
```python
    async def refresh(self) -> None:
        """Refresh the query editor content."""
```
```python
    async def reload_queries(self) -> None:
        """Reload the list of saved queries."""
```
```python
    def set_connection_status(self, connection_id, connected) -> None:
        """Update the connection status.

Args: connection_id: Connection ID connected: Whether the connection is active"""
```

```python
class SQLEditor(QTextEdit):
    """SQL editor with syntax highlighting and auto-completion."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the SQL editor.  Args: parent: Parent widget"""
```
```python
    def format_sql(self) -> None:
        """Format the SQL query with proper indentation and capitalization."""
```
```python
    def keyPressEvent(self, event) -> None:
        """Handle key press events.  Args: event: Key press event"""
```

```python
class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for SQL queries."""
```
*Methods:*
```python
    def __init__(self, document) -> None:
        """Initialize the syntax highlighter.  Args: document: Document to highlight"""
```
```python
    def highlightBlock(self, text) -> None:
        """Highlight a block of text.  Args: text: Text to highlight"""
```

####### Module: results_view
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/results_view.py`

###### Package: utils
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/utils`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/utils/__init__.py`

####### Module: history
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/utils/history.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import datetime
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple, cast
from qorzen.utils.exceptions import DatabaseError
from models import HistoryEntry, HistorySchedule, QueryResult, SavedQuery
```

**Classes:**
```python
class HistoryManager(object):
    """Manager for database history collection and storage."""
```
*Methods:*
```python
    def __init__(self, database_manager, logger, history_connection_id) -> None:
        """Initialize the history manager.

Args: database_manager: Qorzen database manager instance logger: Logger instance history_connection_id: Database connection ID for history storage"""
```
```python
    async def create_schedule(self, schedule) -> HistorySchedule:
        """Create a new history collection schedule.

Args: schedule: History schedule to create

Returns: Created schedule with updated ID

Raises: DatabaseError: If schedule creation fails"""
```
```python
    async def delete_history_data(self, snapshot_id) -> bool:
        """Delete historical data for a snapshot.

Args: snapshot_id: Snapshot ID

Returns: True if the data was deleted

Raises: DatabaseError: If deleting data fails"""
```
```python
    async def delete_schedule(self, schedule_id) -> bool:
        """Delete a history collection schedule.

Args: schedule_id: ID of the schedule to delete

Returns: True if the schedule was deleted

Raises: DatabaseError: If schedule deletion fails"""
```
```python
    async def execute_schedule_now(self, schedule_id, connector_manager, saved_queries) -> HistoryEntry:
        """Execute a history collection schedule immediately.

Args: schedule_id: Schedule ID connector_manager: Database connector manager saved_queries: Dictionary of saved queries

Returns: History entry for the executed schedule

Raises: DatabaseError: If executing the schedule fails"""
```
```python
    async def get_all_schedules(self) -> List[HistorySchedule]:
        """Get all history collection schedules.

Returns: List of history schedules

Raises: DatabaseError: If fetching schedules fails"""
```
```python
    async def get_history_data(self, snapshot_id) -> Optional[Dict[(str, Any)]]:
        """Get historical data for a snapshot.

Args: snapshot_id: Snapshot ID

Returns: Dictionary with 'data', 'schema', and 'metadata' keys, or None if not found

Raises: DatabaseError: If fetching data fails"""
```
```python
    async def get_history_entries(self, schedule_id, limit) -> List[HistoryEntry]:
        """Get history entries, optionally filtered by schedule.

Args: schedule_id: Optional schedule ID to filter by limit: Maximum number of entries to return

Returns: List of history entries

Raises: DatabaseError: If fetching entries fails"""
```
```python
    async def get_schedule(self, schedule_id) -> Optional[HistorySchedule]:
        """Get a specific history collection schedule.

Args: schedule_id: Schedule ID

Returns: History schedule or None if not found

Raises: DatabaseError: If fetching the schedule fails"""
```
```python
    async def initialize(self) -> None:
        """Initialize the history manager, creating necessary database tables.

Raises: DatabaseError: If initialization fails"""
```
```python
    async def start_schedule(self, schedule) -> None:
        """Start a history collection schedule.

Args: schedule: History schedule to start

Raises: DatabaseError: If starting the schedule fails"""
```
```python
    async def stop_schedule(self, schedule_id) -> None:
        """Stop a running history collection schedule.

Args: schedule_id: ID of the schedule to stop

Raises: DatabaseError: If stopping the schedule fails"""
```
```python
    async def update_schedule(self, schedule) -> HistorySchedule:
        """Update an existing history collection schedule.

Args: schedule: Updated history schedule

Returns: Updated schedule

Raises: DatabaseError: If schedule update fails"""
```

####### Module: mapping
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/utils/mapping.py`

**Imports:**
```python
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple, Set, Union, cast
from models import FieldMapping, QueryResult
```

**Functions:**
```python
def apply_mapping_to_query(query, mapping) -> str:
    """Apply field mapping to a SQL query by transforming SELECT * or adding AS clauses to field references.

Args: query: Original SQL query mapping: Field mapping to apply

Returns: Transformed SQL query with mapped fields"""
```

```python
def apply_mapping_to_results(result, mapping) -> QueryResult:
    """Apply field mapping to query results.

Args: result: Original query result mapping: Field mapping to apply

Returns: New query result with mapped field names"""
```

```python
def create_mapping_from_fields(connection_id, table_name, field_names, description) -> FieldMapping:
    """Create a new field mapping for a table.

Args: connection_id: Database connection ID table_name: Table name field_names: List of field names description: Optional description

Returns: FieldMapping object with default mappings"""
```

```python
def standardize_field_name(field_name) -> str:
    """Convert a field name to standardized format (snake_case).

Args: field_name: Original field name

Returns: Standardized field name"""
```

####### Module: validation
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/utils/validation.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, ValidationError
from models import ValidationRule, ValidationRuleType, ValidationResult, QueryResult
```

**Functions:**
```python
def create_custom_rule(connection_id, table_name, field_name, expression, name, description, error_message) -> ValidationRule:
    """Create a custom validation rule.

Args: connection_id: Database connection ID table_name: Table name field_name: Field name expression: Python expression that evaluates to a boolean name: Rule name (defaults to "Custom check for {field_name}") description: Rule description error_message: Error message (defaults to "Value failed custom validation")

Returns: ValidationRule object"""
```

```python
def create_enumeration_rule(connection_id, table_name, field_name, allowed_values, name, description, error_message) -> ValidationRule:
    """Create an enumeration validation rule.

Args: connection_id: Database connection ID table_name: Table name field_name: Field name allowed_values: List of allowed values name: Rule name (defaults to "Enumeration check for {field_name}") description: Rule description error_message: Error message (defaults to "Value must be one of: {values}")

Returns: ValidationRule object"""
```

```python
def create_length_rule(connection_id, table_name, field_name, min_length, max_length, name, description, error_message) -> ValidationRule:
    """Create a length validation rule.

Args: connection_id: Database connection ID table_name: Table name field_name: Field name min_length: Minimum allowed length max_length: Maximum allowed length name: Rule name (defaults to "Length check for {field_name}") description: Rule description error_message: Error message (defaults to "Length must be between {min} and {max}")

Returns: ValidationRule object"""
```

```python
def create_not_null_rule(connection_id, table_name, field_name, name, description, error_message) -> ValidationRule:
    """Create a not-null validation rule.

Args: connection_id: Database connection ID table_name: Table name field_name: Field name name: Rule name (defaults to "Not null check for {field_name}") description: Rule description error_message: Error message (defaults to "Value cannot be null")

Returns: ValidationRule object"""
```

```python
def create_pattern_rule(connection_id, table_name, field_name, pattern, name, description, error_message) -> ValidationRule:
    """Create a pattern validation rule.

Args: connection_id: Database connection ID table_name: Table name field_name: Field name pattern: Regex pattern name: Rule name (defaults to "Pattern check for {field_name}") description: Rule description error_message: Error message (defaults to "Value must match pattern: {pattern}")

Returns: ValidationRule object"""
```

```python
def create_range_rule(connection_id, table_name, field_name, name, description, min_value, max_value, error_message) -> ValidationRule:
    """Create a range validation rule.

Args: connection_id: Database connection ID table_name: Table name field_name: Field name name: Rule name (defaults to "Range check for {field_name}") description: Rule description min_value: Minimum allowed value max_value: Maximum allowed value error_message: Error message (defaults to "Value must be between {min} and {max}")

Returns: ValidationRule object"""
```

```python
def create_unique_rule(connection_id, table_name, field_name, name, description, error_message) -> ValidationRule:
    """Create a uniqueness validation rule.

Args: connection_id: Database connection ID table_name: Table name field_name: Field name name: Rule name (defaults to "Uniqueness check for {field_name}") description: Rule description error_message: Error message (defaults to "Value must be unique")

Returns: ValidationRule object"""
```

**Classes:**
```python
class ValidationEngine(object):
    """Engine for validating database data against defined rules."""
```
*Methods:*
```python
    def __init__(self, database_manager, logger, validation_connection_id) -> None:
        """Initialize the validation engine.

Args: database_manager: Qorzen database manager instance logger: Logger instance validation_connection_id: Database connection ID for validation storage"""
```
```python
    async def create_rule(self, rule) -> ValidationRule:
        """Create a new validation rule.

Args: rule: Validation rule to create

Returns: Created rule with updated ID

Raises: DatabaseError: If rule creation fails"""
```
```python
    async def delete_rule(self, rule_id) -> bool:
        """Delete a validation rule.

Args: rule_id: ID of the rule to delete

Returns: True if the rule was deleted

Raises: DatabaseError: If rule deletion fails"""
```
```python
    async def get_all_rules(self, connection_id, table_name) -> List[ValidationRule]:
        """Get all validation rules, optionally filtered.

Args: connection_id: Optional connection ID to filter by table_name: Optional table name to filter by

Returns: List of validation rules

Raises: DatabaseError: If fetching rules fails"""
```
```python
    async def get_rule(self, rule_id) -> Optional[ValidationRule]:
        """Get a specific validation rule.

Args: rule_id: Rule ID

Returns: Validation rule or None if not found

Raises: DatabaseError: If fetching the rule fails"""
```
```python
    async def get_validation_results(self, rule_id, limit) -> List[ValidationResult]:
        """Get validation results, optionally filtered by rule.

Args: rule_id: Optional rule ID to filter by limit: Maximum number of results to return

Returns: List of validation results

Raises: DatabaseError: If fetching results fails"""
```
```python
    async def initialize(self) -> None:
        """Initialize the validation engine, creating necessary database tables.

Raises: DatabaseError: If initialization fails"""
```
```python
    async def update_rule(self, rule) -> ValidationRule:
        """Update an existing validation rule.

Args: rule: Updated validation rule

Returns: Updated rule

Raises: DatabaseError: If rule update fails"""
```
```python
    async def validate_all_rules(self, connection_id, table_name, data) -> List[ValidationResult]:
        """Validate data against all active rules for a table.

Args: connection_id: Connection ID table_name: Table name data: Query result to validate

Returns: List of validation results

Raises: ValidationError: If validation fails"""
```
```python
    async def validate_data(self, rule, data) -> ValidationResult:
        """Validate data against a rule.

Args: rule: Validation rule to apply data: Query result to validate

Returns: Validation result

Raises: ValidationError: If validation fails"""
```

#### Package: sample_async_plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/sample_async_plugin`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/sample_async_plugin/__init__.py`

**Imports:**
```python
from code.plugin import SampleAsyncPlugin
```

**Global Variables:**
```python
__all__ = __all__ = ["SampleAsyncPlugin"]
```

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/sample_async_plugin/code`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/sample_async_plugin/code/__init__.py`

###### Module: plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/sample_async_plugin/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Awaitable, cast
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QProgressBar, QListWidget, QListWidgetItem
from qorzen.core.task_manager import TaskCategory, TaskPriority
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_component import AsyncQWidget
```

**Classes:**
```python
class CounterWidget(AsyncQWidget):
    """Widget for displaying the counter information from the sample plugin."""
```
*Methods:*
```python
    def __init__(self, plugin, parent) -> None:
        """Initialize the counter widget.

Args: plugin: The sample plugin instance parent: Optional parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle widget close event.  Args: event: The close event"""
```

```python
class SampleAsyncPlugin(BasePlugin):
    """Sample asynchronous plugin demonstrating the new plugin system."""
```
*Class attributes:*
```python
name = 'sample_async_plugin'
version = '1.0.0'
description = 'Sample asynchronous plugin demonstrating the new plugin system'
author = 'Qorzen'
dependencies =     dependencies = []
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the sample plugin."""
```
```python
    async def initialize(self, application_core, **kwargs) -> None:
        """Initialize the plugin.  Args: application_core: The application core **kwargs: Additional arguments"""
```
```python
    async def on_ui_ready(self, ui_integration) -> None:
        """Handle UI ready event.  Args: ui_integration: The UI integration instance"""
```
```python
    async def setup_ui(self, ui_integration) -> None:
        """Set up the UI components.  Args: ui_integration: The UI integration instance"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the plugin."""
```

#### Package: vcdb_explorer
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer`

**__init__.py:**
*VCdb Explorer Plugin for Qorzen.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/__init__.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.plugins.vcdb_explorer.code.plugin import VCdbExplorerPlugin
```

**Global Variables:**
```python
__version__ = '1.0.0'
__all__ = __all__ = ["VCdbExplorerPlugin"]
```

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code`

**__init__.py:**
*VCdb Explorer code package.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/__init__.py`

**Imports:**
```python
from __future__ import annotations
```

###### Module: data_table
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/data_table.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import csv
import logging
import os
import tempfile
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QRegularExpression, QSize, QSortFilterProxyModel, Qt, Signal, Slot, QTimer, QPoint
from PySide6.QtGui import QAction, QClipboard, QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QProgressBar, QProgressDialog, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QTableView, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget, QGridLayout, QApplication, QRadioButton
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event
from database_handler import DatabaseHandler
from events import VCdbEventType
from export import DataExporter, ExportError
```

**Global Variables:**
```python
EXCEL_AVAILABLE = False
```

**Classes:**
```python
class ColumnSelectionDialog(QDialog):
    """Dialog for selecting and ordering table columns."""
```
*Methods:*
```python
    def __init__(self, available_columns, selected_columns, parent) -> None:
        """Initialize the dialog.

Args: available_columns: List of available columns with 'id' and 'name' keys selected_columns: List of currently selected column IDs parent: Parent widget"""
```
```python
    def get_selected_columns(self) -> List[str]:
        """Get the selected columns in the order shown in the list.  Returns: List of selected column IDs"""
```

```python
class DataTableWidget(QWidget):
    """Widget for displaying and interacting with query results."""
```
*Class attributes:*
```python
queryStarted =     queryStarted = Signal()
queryFinished =     queryFinished = Signal()
```
*Methods:*
```python
    def __init__(self, database_handler, event_bus_manager, logger, parent) -> None:
        """Initialize the data table widget.

Args: database_handler: Handler for database operations event_bus_manager: Manager for event bus operations logger: Logger instance parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle the close event by unsubscribing from events."""
```
```python
    def execute_query(self, filter_panels) -> None:
        """Execute a query with the specified filters.

Args: filter_panels: List of filter dictionaries from multiple panels"""
```
```python
    def get_callback_id(self) -> str:
        """Get the callback ID for this widget.  Returns: Unique callback ID"""
```
```python
    def get_page_size(self) -> int:
        """Get the current page size.  Returns: Number of rows per page"""
```
```python
    def get_selected_columns(self) -> List[str]:
        """Get the currently selected columns.  Returns: List of column IDs"""
```

```python
class ExportOptionsDialog(QDialog):
    """Dialog for configuring export options."""
```
*Methods:*
```python
    def __init__(self, format_type, current_count, total_count, parent) -> None:
        """Initialize the dialog.

Args: format_type: Export format (e.g., 'csv', 'excel') current_count: Number of rows in current view total_count: Total number of matching rows parent: Parent widget"""
```
```python
    def export_all(self) -> bool:
        """Check if all results should be exported.

Returns: True to export all results, False to export only the current page"""
```

```python
class FilterProxyModel(QSortFilterProxyModel):
    """Proxy model for client-side filtering of query results."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the proxy model.  Args: parent: Parent widget"""
```
```python
    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        """Determine if a row should be included in the filtered results.

Args: source_row: Row index in the source model source_parent: Parent index

Returns: True if the row should be included, False otherwise"""
```
```python
    def set_column_map(self, columns) -> None:
        """Set the column mapping.  Args: columns: List of column IDs"""
```
```python
    def set_filters(self, filters) -> None:
        """Set the active filters.  Args: filters: Dictionary of filter values by column"""
```

```python
class OverlayProgressDialog(QDialog):
    """Dialog showing progress as an overlay on the parent window."""
```
*Class attributes:*
```python
cancelled =     cancelled = Signal()
```
*Methods:*
```python
    def __init__(self, title, parent) -> None:
        """Initialize the dialog.  Args: title: Title for the progress dialog parent: Parent widget"""
```
```python
    def set_progress(self, value, maximum, status) -> None:
        """Update the progress display.

Args: value: Current progress value maximum: Maximum progress value status: Optional status message"""
```

```python
class QueryResultModel(QAbstractTableModel):
    """Model for displaying query results in a table view."""
```
*Methods:*
```python
    def __init__(self, columns, column_map, parent) -> None:
        """Initialize the model.

Args: columns: List of column IDs column_map: Mapping from column IDs to display names parent: Parent widget"""
```
```python
    def columnCount(self, parent) -> int:
        """Get the number of columns in the model.  Args: parent: Parent index  Returns: Number of columns"""
```
```python
    def data(self, index, role) -> Any:
        """Get the data at the specified index.  Args: index: Model index role: Data role  Returns: Data value"""
```
```python
    def get_all_data(self) -> List[Dict[(str, Any)]]:
        """Get all data rows.  Returns: List of all data dictionaries"""
```
```python
    def get_row_data(self, row) -> Dict[(str, Any)]:
        """Get the data for a specific row.  Args: row: Row index  Returns: Row data dictionary"""
```
```python
    def get_total_count(self) -> int:
        """Get the total record count.  Returns: Total count"""
```
```python
    def headerData(self, section, orientation, role) -> Any:
        """Get the header data for a section.

Args: section: Section index orientation: Header orientation role: Data role

Returns: Header data"""
```
```python
    def rowCount(self, parent) -> int:
        """Get the number of rows in the model.  Args: parent: Parent index  Returns: Number of rows"""
```
```python
    def set_columns(self, columns) -> None:
        """Set the model columns.  Args: columns: New list of column IDs"""
```
```python
    def set_data(self, data, total_count) -> None:
        """Set the model data.  Args: data: List of data dictionaries total_count: Total count of all records"""
```

```python
class QuerySignals(QWidget):
    """Signal class for query operations."""
```
*Class attributes:*
```python
started =     started = Signal()
completed =     completed = Signal(object)
failed =     failed = Signal(str)
progress =     progress = Signal(int, int)
cancelled =     cancelled = Signal()
```

```python
class TableFilterWidget(QWidget):
    """Widget for client-side filtering of table data."""
```
*Class attributes:*
```python
filterChanged =     filterChanged = Signal(dict)
```
*Methods:*
```python
    def __init__(self, columns, column_map, parent) -> None:
        """Initialize the filter widget.

Args: columns: List of column IDs column_map: Mapping from column IDs to display names parent: Parent widget"""
```
```python
    def get_filters(self) -> Dict[(str, Any)]:
        """Get the current filter settings.  Returns: Dictionary of filter values by column"""
```
```python
    def set_columns(self, columns) -> None:
        """Set the available columns.  Args: columns: List of column IDs"""
```

```python
class YearRangeTableFilter(QWidget):
    """Widget for filtering by year range."""
```
*Class attributes:*
```python
filterChanged =     filterChanged = Signal(dict)
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the year range filter.  Args: parent: Parent widget"""
```
```python
    def get_filter(self) -> Dict[(str, Any)]:
        """Get the current filter settings.  Returns: Dictionary with year range filter settings"""
```

###### Module: database_handler
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/database_handler.py`

**Imports:**
```python
from __future__ import annotations
from sqlalchemy.orm.util import AliasedInsp, AliasedClass
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable
from functools import lru_cache
import sqlalchemy
from sqlalchemy import func, or_, select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Join
from qorzen.core.database_manager import DatabaseConnectionConfig, DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.utils.exceptions import DatabaseError, TaskError
from events import VCdbEventType
from models import Aspiration, BaseVehicle, BedConfig, BedLength, BedType, BodyNumDoors, BodyStyleConfig, BodyType, BrakeABS, BrakeConfig, BrakeSystem, BrakeType, Class, CylinderHeadType, DriveType, ElecControlled, EngineBase2, EngineBlock, EngineBoreStroke, EngineConfig2, EngineDesignation, EngineVersion, FuelDeliveryConfig, FuelDeliverySubType, FuelDeliveryType, FuelSystemControlType, FuelSystemDesign, FuelType, IgnitionSystemType, Make, Mfr, MfrBodyCode, Model, PowerOutput, PublicationStage, Region, SpringType, SpringTypeConfig, SteeringConfig, SteeringSystem, SteeringType, SubModel, Transmission, TransmissionBase, TransmissionControlType, TransmissionMfrCode, TransmissionNumSpeeds, TransmissionType, Valves, Vehicle, VehicleToBodyConfig, VehicleToBodyStyleConfig, VehicleToBedConfig, VehicleToBrakeConfig, VehicleToClass, VehicleToDriveType, VehicleToEngineConfig, VehicleToMfrBodyCode, VehicleToSpringTypeConfig, VehicleToSteeringConfig, VehicleToTransmission, VehicleToWheelBase, VehicleType, VehicleTypeGroup, WheelBase, Year
```

**Classes:**
```python
class DatabaseHandler(object):
    """Handler for database operations on the VCdb database."""
```
*Class attributes:*
```python
CONNECTION_NAME = 'vcdb_explorer'
```
*Methods:*
```python
    def __init__(self, database_manager, event_bus_manager, task_manager, concurrency_manager, logger) -> None:
        """Initialize the database handler.

Args: database_manager: Manager for database connections event_bus_manager: Manager for event bus operations task_manager: Manager for background tasks concurrency_manager: Manager for concurrency operations logger: Logger instance"""
```
```python
    async def cancel_query(self, callback_id) -> bool:
        """Cancel a running query.

Args: callback_id: The ID of the query to cancel

Returns: True if cancellation was requested, False otherwise"""
```
```python
    async def configure(self, host, port, database, user, password, db_type, pool_size, max_overflow, pool_recycle, echo) -> None:
        """Configure the database connection.

Args: host: Database host port: Database port database: Database name user: Database user password: Database password db_type: Database type (e.g., 'postgresql') pool_size: Connection pool size max_overflow: Maximum number of connections to create pool_recycle: Connection recycle time in seconds echo: Whether to echo SQL statements"""
```
```python
    def get_available_columns(self) -> List[Dict[(str, str)]]:
        """Get the list of available columns for query results.

Returns: List of column dictionaries with 'id' and 'name' keys"""
```
```python
    def get_available_filters(self) -> List[Dict[(str, Any)]]:
        """Get the list of available filters.

Returns: List of filter dictionaries with 'id', 'name', and 'mandatory' keys"""
```
```python
    async def get_filter_values(self, filter_type, current_filters, exclude_filters) -> List[Dict[(str, Any)]]:
        """Get available values for a filter type, filtered by current selections.

Args: filter_type: Type of filter to get values for current_filters: Currently selected filter values exclude_filters: Filter types to exclude

Returns: List of value dictionaries with 'id', 'name', and 'count' keys"""
```
```python
    async def initialize(self) -> None:
        """Initialize the database handler by subscribing to events."""
```
```python
    async def shutdown(self) -> None:
        """Shut down the database handler."""
```

```python
class DatabaseHandlerError(Exception):
    """Exception raised for errors in the DatabaseHandler."""
```
*Methods:*
```python
    def __init__(self, message, details) -> None:
        """Initialize the exception.  Args: message: Error message details: Additional details about the error"""
```

###### Module: events
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/events.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.core.event_model import EventType
```

**Classes:**
```python
class VCdbEventType(object):
    """Event types for the VCdb Explorer plugin."""
```
*Methods:*
```python
@staticmethod
    def filter_changed() -> str:
        """Event when a filter selection changes.  Returns: Event type identifier"""
```
```python
@staticmethod
    def filters_refreshed() -> str:
        """Event when filters are refreshed.  Returns: Event type identifier"""
```
```python
@staticmethod
    def query_execute() -> str:
        """Event to trigger query execution.  Returns: Event type identifier"""
```
```python
@staticmethod
    def query_results() -> str:
        """Event when query results are available.  Returns: Event type identifier"""
```

###### Module: export
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/export.py`

**Imports:**
```python
from __future__ import annotations
import csv
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Awaitable
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
```

**Global Variables:**
```python
EXCEL_AVAILABLE = False
```

**Classes:**
```python
class DataExporter(object):
    """Handles exporting of data to various file formats."""
```
*Methods:*
```python
    def __init__(self, logger) -> None:
        """Initialize the exporter.  Args: logger: Logger instance"""
```
```python
    async def export_all_data(self, database_callback, filter_panels, columns, column_map, file_path, format_type, max_rows, table_filters, sort_by, sort_desc, progress_callback) -> int:
        """Export all matching data to a file.

Args: database_callback: Function to call for retrieving data filter_panels: List of filter dictionaries from multiple panels columns: List of column IDs to include column_map: Mapping from column IDs to display names file_path: Path to the output file format_type: Export format (e.g., 'csv', 'excel') max_rows: Maximum number of rows to export (0 for all) table_filters: Additional table filters sort_by: Column to sort by sort_desc: Whether to sort in descending order progress_callback: Optional callback for reporting progress

Returns: Number of rows exported

Raises: ExportError: If the export fails"""
```
```python
    async def export_csv(self, data, columns, column_map, file_path) -> None:
        """Export data to a CSV file.

Args: data: List of data dictionaries columns: List of column IDs to include column_map: Mapping from column IDs to display names file_path: Path to the output file

Raises: ExportError: If the export fails"""
```
```python
    async def export_excel(self, data, columns, column_map, file_path, sheet_name) -> None:
        """Export data to an Excel file.

Args: data: List of data dictionaries columns: List of column IDs to include column_map: Mapping from column IDs to display names file_path: Path to the output file sheet_name: Optional name for the worksheet

Raises: ExportError: If the export fails or Excel support is not available"""
```

```python
class ExportError(Exception):
    """Exception raised for errors during data export."""
```
*Methods:*
```python
    def __init__(self, message, details) -> None:
        """Initialize the exception.  Args: message: Error message details: Additional details about the error"""
```

###### Module: filter_panel
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/filter_panel.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, cast
from qasync import asyncSlot
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel, QMenu, QPushButton, QSizePolicy, QSpinBox, QTabWidget, QToolButton, QVBoxLayout, QWidget, QProgressBar, QApplication
from qorzen.core.event_bus_manager import EventBusManager
from database_handler import DatabaseHandler
from events import VCdbEventType
```

**Classes:**
```python
class ComboBoxFilter(FilterWidget):
    """Filter widget using a combo box for selection."""
```
*Methods:*
```python
    def __init__(self, filter_type, filter_name, parent) -> None:
        """Initialize the combo box filter.

Args: filter_type: The type identifier for this filter filter_name: The display name of the filter parent: The parent widget"""
```
```python
@Slot()
    def clear(self) -> None:
        """Clear the selection by setting it to the 'Any' option."""
```
```python
    def get_selected_values(self) -> List[int]:
        """Get the currently selected value ID from the combo box."""
```
```python
    def set_available_values(self, values) -> None:
        """Set the available values in the combo box.

Args: values: List of value dictionaries with 'id', 'name', and 'count' keys"""
```
```python
    def set_loading(self, loading) -> None:
        """Set the loading state and update the loading indicator."""
```

```python
class FilterPanel(QGroupBox):
    """A panel containing multiple filters that can be applied together."""
```
*Class attributes:*
```python
filterChanged =     filterChanged = Signal(str, str, list)
removeRequested =     removeRequested = Signal(str)
```
*Methods:*
```python
    def __init__(self, panel_id, database_handler, event_bus_manager, logger, parent) -> None:
        """Initialize the filter panel.

Args: panel_id: Unique identifier for this panel database_handler: Handler for database operations event_bus_manager: Manager for event bus operations logger: Logger instance parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle the close event by unsubscribing from events."""
```
```python
    def get_current_values(self) -> Dict[(str, List[int])]:
        """Get the current filter values for all filters in this panel."""
```
```python
    def get_panel_id(self) -> str:
        """Get the panel's unique identifier."""
```
```python
    async def initialize(self) -> None:
        """Initialize the panel by adding mandatory filters and subscribing to events."""
```
```python
    def refresh_all_filters(self) -> None:
```
```python
    async def set_filter_values(self, filter_type, values) -> None:
        """Set the available values for a specific filter.

Args: filter_type: The type of filter to update values: The available values for the filter"""
```
```python
    async def update_filter_values(self, filter_values) -> None:
```

```python
class FilterPanelManager(QWidget):
    """Manager for multiple filter panels working together."""
```
*Class attributes:*
```python
filtersChanged =     filtersChanged = Signal()
```
*Methods:*
```python
    def __init__(self, database_handler, event_bus_manager, logger, max_panels, parent) -> None:
        """Initialize the filter panel manager.

Args: database_handler: Handler for database operations event_bus_manager: Manager for event bus operations logger: Logger instance max_panels: Maximum number of filter panels allowed parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle the close event by unsubscribing from events."""
```
```python
    def get_all_filters(self) -> List[Dict[(str, List[int])]]:
        """Get all current filter values from all panels.

Returns: A list of filter dictionaries, one per panel"""
```
```python
    def refresh_all_panels(self) -> None:
        """Refresh all filter panels."""
```
```python
    async def update_filter_values(self, panel_id, filter_values) -> None:
        """Update filter values for a specific panel.

Args: panel_id: The ID of the panel to update filter_values: The new filter values"""
```

```python
class FilterWidget(QWidget):
    """Base class for filter widgets that allow selecting values for filtering."""
```
*Class attributes:*
```python
valueChanged =     valueChanged = Signal(str, list)
```
*Methods:*
```python
    def __init__(self, filter_type, filter_name, parent) -> None:
        """Initialize the filter widget.

Args: filter_type: The type identifier for this filter filter_name: The display name of the filter parent: The parent widget"""
```
```python
@Slot()
    def clear(self) -> None:
        """Clear the current filter selection."""
```
```python
    def get_filter_name(self) -> str:
        """Get the display name of the filter."""
```
```python
    def get_filter_type(self) -> str:
        """Get the filter type identifier."""
```
```python
    def get_selected_values(self) -> List[int]:
        """Get the currently selected values for this filter."""
```
```python
    def set_available_values(self, values) -> None:
        """Set the available values for this filter.

Args: values: List of value dictionaries with 'id', 'name', and 'count' keys"""
```
```python
    def set_loading(self, loading) -> None:
        """Set the loading state of the filter.

Args: loading: True if the filter is loading data, False otherwise"""
```

```python
class YearRangeFilter(FilterWidget):
    """Filter widget for selecting a year range."""
```
*Methods:*
```python
    def __init__(self, filter_type, filter_name, parent) -> None:
        """Initialize the year range filter.

Args: filter_type: The type identifier for this filter filter_name: The display name of the filter parent: The parent widget"""
```
```python
@Slot()
    def clear(self) -> None:
        """Reset the year range to the full available range."""
```
```python
    def get_selected_values(self) -> List[int]:
        """Get the selected year range as a list of two integers.

Returns: A list containing [start_year, end_year] or an empty list if invalid"""
```
```python
    def set_available_values(self, values) -> None:
        """Set the available years for the range spinboxes.

Args: values: List of value dictionaries with 'id', 'name', and 'count' keys"""
```

###### Module: models
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/models.py`

**Imports:**
```python
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from sqlalchemy.sql import func
import uuid
```

**Global Variables:**
```python
VCdbBase = VCdbBase = declarative_base()
```

**Classes:**
```python
class Abbreviation(VCdbBase):
    """Abbreviation model representing abbreviations used in the system."""
```
*Class attributes:*
```python
__tablename__ = 'abbreviation'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Aspiration(VCdbBase):
    """Aspiration model representing engine aspiration methods."""
```
*Class attributes:*
```python
__tablename__ = 'aspiration'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Attachment(VCdbBase):
    """Attachment model representing file attachments."""
```
*Class attributes:*
```python
__tablename__ = 'attachment'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class AttachmentType(VCdbBase):
    """AttachmentType model representing types of attachments."""
```
*Class attributes:*
```python
__tablename__ = 'attachment_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BaseVehicle(VCdbBase):
    """BaseVehicle model representing base vehicle configurations."""
```
*Class attributes:*
```python
__tablename__ = 'base_vehicle'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BedConfig(VCdbBase):
    """BedConfig model representing complete bed configurations."""
```
*Class attributes:*
```python
__tablename__ = 'bed_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BedLength(VCdbBase):
    """BedLength model representing lengths of vehicle beds."""
```
*Class attributes:*
```python
__tablename__ = 'bed_length'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BedType(VCdbBase):
    """BedType model representing types of vehicle beds."""
```
*Class attributes:*
```python
__tablename__ = 'bed_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BodyNumDoors(VCdbBase):
    """BodyNumDoors model representing number of doors on vehicle bodies."""
```
*Class attributes:*
```python
__tablename__ = 'body_num_doors'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BodyStyleConfig(VCdbBase):
    """BodyStyleConfig model representing complete body style configurations."""
```
*Class attributes:*
```python
__tablename__ = 'body_style_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BodyType(VCdbBase):
    """BodyType model representing types of vehicle bodies."""
```
*Class attributes:*
```python
__tablename__ = 'body_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BrakeABS(VCdbBase):
    """BrakeABS model representing anti-lock brake systems."""
```
*Class attributes:*
```python
__tablename__ = 'brake_abs'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BrakeConfig(VCdbBase):
    """BrakeConfig model representing complete brake system configurations."""
```
*Class attributes:*
```python
__tablename__ = 'brake_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BrakeSystem(VCdbBase):
    """BrakeSystem model representing brake system configurations."""
```
*Class attributes:*
```python
__tablename__ = 'brake_system'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class BrakeType(VCdbBase):
    """BrakeType model representing types of brake systems."""
```
*Class attributes:*
```python
__tablename__ = 'brake_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class ChangeAttributeStates(VCdbBase):
    """ChangeAttributeStates model representing states of attribute changes."""
```
*Class attributes:*
```python
__tablename__ = 'change_attribute_states'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class ChangeDetails(VCdbBase):
    """ChangeDetails model representing details of changes."""
```
*Class attributes:*
```python
__tablename__ = 'change_details'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class ChangeReasons(VCdbBase):
    """ChangeReasons model representing reasons for changes."""
```
*Class attributes:*
```python
__tablename__ = 'change_reasons'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class ChangeTableNames(VCdbBase):
    """ChangeTableNames model representing names of tables that can be changed."""
```
*Class attributes:*
```python
__tablename__ = 'change_table_names'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Changes(VCdbBase):
    """Changes model representing change records."""
```
*Class attributes:*
```python
__tablename__ = 'changes'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Class(VCdbBase):
    """Class model representing vehicle classifications."""
```
*Class attributes:*
```python
__tablename__ = 'class'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class ConfigurationError(Exception):
    """Raised when there is an error in the configuration."""
```

```python
class CylinderHeadType(VCdbBase):
    """CylinderHeadType model representing types of cylinder heads in engines."""
```
*Class attributes:*
```python
__tablename__ = 'cylinder_head_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class DatabaseConnectionError(Exception):
    """Raised when a database connection cannot be established."""
```

```python
class DriveType(VCdbBase):
    """DriveType model representing types of drive systems."""
```
*Class attributes:*
```python
__tablename__ = 'drive_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class ElecControlled(VCdbBase):
    """ElecControlled model representing electrically controlled components."""
```
*Class attributes:*
```python
__tablename__ = 'elec_controlled'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineBase(VCdbBase):
    """EngineBase model representing base engine specifications for ACES 3."""
```
*Class attributes:*
```python
__tablename__ = 'engine_base'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineBase2(VCdbBase):
    """EngineBase2 model representing base engine specifications for ACES 4."""
```
*Class attributes:*
```python
__tablename__ = 'engine_base2'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineBlock(VCdbBase):
    """EngineBlock model representing engine block specifications."""
```
*Class attributes:*
```python
__tablename__ = 'engine_block'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineBoreStroke(VCdbBase):
    """EngineBoreStroke model representing engine bore and stroke specifications."""
```
*Class attributes:*
```python
__tablename__ = 'engine_bore_stroke'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineConfig(VCdbBase):
    """EngineConfig model representing complete engine configurations for ACES 3."""
```
*Class attributes:*
```python
__tablename__ = 'engine_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineConfig2(VCdbBase):
    """EngineConfig2 model representing complete engine configurations for ACES 4."""
```
*Class attributes:*
```python
__tablename__ = 'engine_config2'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineDesignation(VCdbBase):
    """EngineDesignation model representing engine designation specifications."""
```
*Class attributes:*
```python
__tablename__ = 'engine_designation'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineVIN(VCdbBase):
    """EngineVIN model representing engine VIN codes."""
```
*Class attributes:*
```python
__tablename__ = 'engine_vin'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EngineVersion(VCdbBase):
    """EngineVersion model representing engine version specifications."""
```
*Class attributes:*
```python
__tablename__ = 'engine_version'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class EnglishPhrase(VCdbBase):
    """EnglishPhrase model representing English phrases for translation."""
```
*Class attributes:*
```python
__tablename__ = 'english_phrase'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class ExportError(Exception):
    """Raised when an export operation fails."""
```

```python
class FuelDeliveryConfig(VCdbBase):
    """FuelDeliveryConfig model representing complete fuel delivery system configurations."""
```
*Class attributes:*
```python
__tablename__ = 'fuel_delivery_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class FuelDeliverySubType(VCdbBase):
    """FuelDeliverySubType model representing subtypes of fuel delivery systems."""
```
*Class attributes:*
```python
__tablename__ = 'fuel_delivery_sub_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class FuelDeliveryType(VCdbBase):
    """FuelDeliveryType model representing types of fuel delivery systems."""
```
*Class attributes:*
```python
__tablename__ = 'fuel_delivery_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class FuelSystemControlType(VCdbBase):
    """FuelSystemControlType model representing types of fuel system control mechanisms."""
```
*Class attributes:*
```python
__tablename__ = 'fuel_system_control_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class FuelSystemDesign(VCdbBase):
    """FuelSystemDesign model representing designs of fuel systems."""
```
*Class attributes:*
```python
__tablename__ = 'fuel_system_design'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class FuelType(VCdbBase):
    """FuelType model representing types of fuel used in engines."""
```
*Class attributes:*
```python
__tablename__ = 'fuel_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class IgnitionSystemType(VCdbBase):
    """IgnitionSystemType model representing types of ignition systems."""
```
*Class attributes:*
```python
__tablename__ = 'ignition_system_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class InvalidFilterError(Exception):
    """Raised when an invalid filter is provided."""
```

```python
class Language(VCdbBase):
    """Language model representing languages for translation."""
```
*Class attributes:*
```python
__tablename__ = 'language'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class LanguageTranslation(VCdbBase):
    """LanguageTranslation model representing translations of phrases into different languages."""
```
*Class attributes:*
```python
__tablename__ = 'language_translation'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class LanguageTranslationAttachment(VCdbBase):
    """LanguageTranslationAttachment model representing attachments for language translations."""
```
*Class attributes:*
```python
__tablename__ = 'language_translation_attachment'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Make(VCdbBase):
    """Make model representing vehicle manufacturers."""
```
*Class attributes:*
```python
__tablename__ = 'make'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Mfr(VCdbBase):
    """Mfr model representing manufacturers."""
```
*Class attributes:*
```python
__tablename__ = 'mfr'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class MfrBodyCode(VCdbBase):
    """MfrBodyCode model representing manufacturer-specific body codes."""
```
*Class attributes:*
```python
__tablename__ = 'mfr_body_code'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Model(VCdbBase):
    """Model model representing vehicle models."""
```
*Class attributes:*
```python
__tablename__ = 'model'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class PowerOutput(VCdbBase):
    """PowerOutput model representing engine power output specifications."""
```
*Class attributes:*
```python
__tablename__ = 'power_output'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class PublicationStage(VCdbBase):
    """PublicationStage model representing stages of publication."""
```
*Class attributes:*
```python
__tablename__ = 'publication_stage'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class QueryExecutionError(Exception):
    """Raised when a query fails to execute."""
```

```python
class Region(VCdbBase):
    """Region model representing geographical regions."""
```
*Class attributes:*
```python
__tablename__ = 'region'
__table_args__ =     __table_args__ = (
        UniqueConstraint("region_id", name="uq_region_id"),
        {"schema": "vcdb"}
    )
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class SpringType(VCdbBase):
    """SpringType model representing types of vehicle springs."""
```
*Class attributes:*
```python
__tablename__ = 'spring_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class SpringTypeConfig(VCdbBase):
    """SpringTypeConfig model representing complete spring type configurations."""
```
*Class attributes:*
```python
__tablename__ = 'spring_type_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class SteeringConfig(VCdbBase):
    """SteeringConfig model representing complete steering configurations."""
```
*Class attributes:*
```python
__tablename__ = 'steering_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class SteeringSystem(VCdbBase):
    """SteeringSystem model representing steering system configurations."""
```
*Class attributes:*
```python
__tablename__ = 'steering_system'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class SteeringType(VCdbBase):
    """SteeringType model representing types of steering systems."""
```
*Class attributes:*
```python
__tablename__ = 'steering_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class SubModel(VCdbBase):
    """SubModel model representing vehicle sub_models."""
```
*Class attributes:*
```python
__tablename__ = 'sub_model'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Transmission(VCdbBase):
    """Transmission model representing complete transmission configurations."""
```
*Class attributes:*
```python
__tablename__ = 'transmission'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class TransmissionBase(VCdbBase):
    """TransmissionBase model representing base transmission configurations."""
```
*Class attributes:*
```python
__tablename__ = 'transmission_base'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class TransmissionControlType(VCdbBase):
    """TransmissionControlType model representing types of transmission control systems."""
```
*Class attributes:*
```python
__tablename__ = 'transmission_control_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class TransmissionMfrCode(VCdbBase):
    """TransmissionMfrCode model representing manufacturer codes for transmissions."""
```
*Class attributes:*
```python
__tablename__ = 'transmission_mfr_code'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class TransmissionNumSpeeds(VCdbBase):
    """TransmissionNumSpeeds model representing number of speeds in transmissions."""
```
*Class attributes:*
```python
__tablename__ = 'transmission_num_speeds'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class TransmissionType(VCdbBase):
    """TransmissionType model representing types of transmissions."""
```
*Class attributes:*
```python
__tablename__ = 'transmission_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VCdbChanges(VCdbBase):
    """VCdbChanges model representing changes to the VCdb."""
```
*Class attributes:*
```python
__tablename__ = 'vcdb_changes'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Valves(VCdbBase):
    """Valves model representing engine valve configurations."""
```
*Class attributes:*
```python
__tablename__ = 'valves'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Vehicle(VCdbBase):
    """Vehicle model representing specific vehicle configurations."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```
```python
@property
    def make(self) -> Make:
        """Get the make of the vehicle."""
```
```python
@property
    def model(self) -> str:
        """Get the model name of the vehicle."""
```
```python
@property
    def year(self) -> Optional[int]:
        """Get the year of the vehicle."""
```

```python
class VehicleToBedConfig(VCdbBase):
    """VehicleToBedConfig model representing the relationship between vehicles and bed configurations."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_bed_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToBodyConfig(VCdbBase):
    """VehicleToBodyConfig model representing the relationship between vehicles and body configurations."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_body_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToBodyStyleConfig(VCdbBase):
    """VehicleToBodyStyleConfig model representing the relationship between vehicles and body style configurations."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_body_style_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToBrakeConfig(VCdbBase):
    """VehicleToBrakeConfig model representing the relationship between vehicles and brake configurations."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_brake_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToClass(VCdbBase):
    """VehicleToClass model representing the relationship between vehicles and classes."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_class'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToDriveType(VCdbBase):
    """VehicleToDriveType model representing the relationship between vehicles and drive types."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_drive_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToEngineConfig(VCdbBase):
    """VehicleToEngineConfig model representing the relationship between vehicles and engine configurations."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_engine_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToMfrBodyCode(VCdbBase):
    """VehicleToMfrBodyCode model representing the relationship between vehicles and manufacturer body codes."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_mfr_body_code'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToSpringTypeConfig(VCdbBase):
    """VehicleToSpringTypeConfig model representing the relationship between vehicles and spring type configurations."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_spring_type_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToSteeringConfig(VCdbBase):
    """VehicleToSteeringConfig model representing the relationship between vehicles and steering configurations."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_steering_config'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToTransmission(VCdbBase):
    """VehicleToTransmission model representing the relationship between vehicles and transmissions."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_transmission'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleToWheelBase(VCdbBase):
    """VehicleToWheelBase model representing the relationship between vehicles and wheel bases."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_to_wheel_base'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleType(VCdbBase):
    """VehicleType model representing types of vehicles."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_type'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class VehicleTypeGroup(VCdbBase):
    """VehicleTypeGroup model representing groups of vehicle types."""
```
*Class attributes:*
```python
__tablename__ = 'vehicle_type_group'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Version(VCdbBase):
    """Version model representing VCdb version information."""
```
*Class attributes:*
```python
__tablename__ = 'version'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class WheelBase(VCdbBase):
    """WheelBase model representing wheel base specifications."""
```
*Class attributes:*
```python
__tablename__ = 'wheel_base'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

```python
class Year(VCdbBase):
    """Year model representing vehicle production years."""
```
*Class attributes:*
```python
__tablename__ = 'year'
__table_args__ =     __table_args__ = {"schema": "vcdb"}
```
*Methods:*
```python
    def __repr__(self) -> str:
```

###### Module: plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QMessageBox, QProgressDialog, QPushButton, QSplitter, QVBoxLayout, QWidget, QFrame, QProgressBar
from PySide6.QtGui import QAction, QIcon
from qorzen.core.remote_manager import RemoteServicesManager
from qorzen.core.security_manager import SecurityManager
from qorzen.core.api_manager import APIManager
from qorzen.core.cloud_manager import CloudManager
from qorzen.core.logging_manager import LoggingManager
from qorzen.core.config_manager import ConfigManager
from qorzen.core.database_manager import DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.file_manager import FileManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_integration import UIIntegration
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from database_handler import DatabaseHandler
from data_table import DataTableWidget
from events import VCdbEventType
from export import DataExporter
from filter_panel import FilterPanelManager
```

**Classes:**
```python
class VCdbExplorerPlugin(BasePlugin):
    """VCdb Explorer plugin for querying and exploring the Vehicle Component Database."""
```
*Class attributes:*
```python
name = 'vcdb_explorer'
version = '1.0.0'
description = 'Advanced query tool for exploring Vehicle Component Database'
author = 'Qorzen Developer'
display_name = 'VCdb Explorer'
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the plugin."""
```
```python
    def get_icon(self) -> Optional[str]:
        """Get the icon path.  Returns: Icon path or None"""
```
```python
    def get_main_widget(self) -> Optional[QWidget]:
        """Get the main widget.  Returns: Main widget or None"""
```
```python
    async def initialize(self, application_core, **kwargs) -> None:
        """Initialize the plugin.

Args: application_core: Core application instance **kwargs: Additional initialization parameters"""
```
```python
    async def on_ui_ready(self, ui_integration) -> None:
        """Set up UI components when the UI is ready.  Args: ui_integration: UI integration instance"""
```
```python
    async def setup_ui(self, ui_integration) -> None:
        """Set up UI components.  Args: ui_integration: UI integration instance"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the plugin."""
```

```python
class VCdbExplorerWidget(QWidget):
    """Main widget for the VCdb Explorer plugin."""
```
*Methods:*
```python
    def __init__(self, database_handler, event_bus_manager, concurrency_manager, task_manager, logger, export_settings, parent) -> None:
        """Initialize the widget.

Args: database_handler: Handler for database operations event_bus_manager: Manager for event bus operations concurrency_manager: Manager for concurrency operations task_manager: Manager for task manager operations logger: Logger instance export_settings: Export configuration settings parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle the close event by unsubscribing from events."""
```
```python
@Slot()
    def refresh_filters(self) -> None:
        """Refresh all filters."""
```

### Package: ui
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui`

**__init__.py:**
*User interface components for the Qorzen platform.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/__init__.py`

**Imports:**
```python
from qorzen.ui.main_window import MainWindow
```

#### Module: dashboard
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/dashboard.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QMessageBox
from qorzen.ui.ui_component import AsyncQWidget
```

**Classes:**
```python
class DashboardWidget(AsyncQWidget):
    """Main dashboard widget for system monitoring."""
```
*Methods:*
```python
    def __init__(self, app_core, parent) -> None:
        """Initialize the dashboard widget."""
```
```python
    def hideEvent(self, event) -> None:
        """Handle widget hide event."""
```
```python
    def showEvent(self, event) -> None:
        """Handle widget show event."""
```

```python
class MetricsWidget(QWidget):
    """Widget for displaying system metrics."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the metrics widget."""
```
```python
    def update_metrics(self, metrics) -> None:
        """Update the displayed metrics."""
```

```python
class SystemStatusTreeWidget(QTreeWidget):
    """Tree widget for displaying system status information."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the system status tree widget."""
```
```python
    def get_item_path(self, item) -> str:
        """Get the full path of a tree item."""
```
```python
    def restore_expanded_state(self) -> None:
        """Restore the previously saved expanded state."""
```
```python
    def save_expanded_state(self) -> None:
        """Save the expanded state of all items."""
```
```python
    def update_system_status(self, status) -> None:
        """Update the tree with system status information."""
```

#### Module: logs
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/logs.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import json
import time
from datetime import datetime
from enum import Enum, auto
from functools import partial
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableView, QTextEdit, QToolBar, QVBoxLayout, QWidget, QMessageBox
from qorzen.core.event_model import EventType
from qorzen.ui.ui_component import AsyncTaskSignals
```

**Classes:**
```python
class LogEntry(object):
    """Represents a single log entry in the application."""
```
*Methods:*
```python
    def __init__(self, timestamp, level, logger, message, event, task, raw_data) -> None:
        """Initialize a log entry.

Args: timestamp: Time when the log was created level: Severity level of the log logger: Name of the logger that created the log message: The log message event: Associated event if any task: Associated task if any raw_data: Raw log data in dictionary form"""
```
```python
@classmethod
    def from_event_payload(cls, payload) -> 'LogEntry':
        """Create a LogEntry from an event payload.

Args: payload: Event payload containing log information

Returns: A LogEntry object populated from the payload"""
```

```python
class LogLevel(Enum):
    """Enum representing log severity levels."""
```
*Class attributes:*
```python
DEBUG =     DEBUG = (QColor(108, 117, 125), "DEBUG")
INFO =     INFO = (QColor(23, 162, 184), "INFO")
WARNING =     WARNING = (QColor(255, 193, 7), "WARNING")
ERROR =     ERROR = (QColor(220, 53, 69), "ERROR")
CRITICAL =     CRITICAL = (QColor(136, 14, 79), "CRITICAL")
```
*Methods:*
```python
@classmethod
    def from_string(cls, level_str) -> 'LogLevel':
        """Convert a string to a LogLevel enum value.

Args: level_str: The string representation of the log level

Returns: Matching LogLevel enum value, or INFO if no match"""
```

```python
class LogTableModel(QAbstractTableModel):
    """Table model for displaying log entries."""
```
*Class attributes:*
```python
COLUMNS =     COLUMNS = ["Timestamp", "Level", "Logger", "Message", "Event", "Task"]
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the log table model.  Args: parent: Parent widget"""
```
```python
    def add_log(self, log_entry) -> None:
        """Add a log entry to the model.  Args: log_entry: Log entry to add"""
```
```python
    def clear_logs(self) -> None:
        """Clear all logs from the model."""
```
```python
    def columnCount(self, parent) -> int:
        """Get the number of columns in the model.

Args: parent: Parent model index

Returns: Number of columns"""
```
```python
    def data(self, index, role) -> Any:
        """Get data for a specific index and role.

Args: index: Model index to get data for role: Role to get data for

Returns: Data for the specified index and role"""
```
```python
    def get_unique_loggers(self) -> List[str]:
        """Get a list of unique logger names.  Returns: Sorted list of unique logger names"""
```
```python
    def headerData(self, section, orientation, role) -> Any:
        """Get header data.

Args: section: Section (row or column) index orientation: Header orientation role: Data role

Returns: Header data for specified section, orientation and role"""
```
```python
    def rowCount(self, parent) -> int:
        """Get the number of rows in the model.  Args: parent: Parent model index  Returns: Number of rows"""
```
```python
    def set_filter_level(self, level) -> None:
        """Set level filter for logs.  Args: level: Log level to filter by"""
```
```python
    def set_filter_logger(self, logger) -> None:
        """Set logger filter for logs.  Args: logger: Logger name to filter by"""
```
```python
    def set_filter_text(self, text) -> None:
        """Set text filter for logs.  Args: text: Filter text"""
```

```python
class LogsView(QWidget):
    """Widget for viewing and filtering application logs."""
```
*Methods:*
```python
    def __init__(self, event_bus_manager, parent) -> None:
        """Initialize the logs view.

Args: event_bus_manager: Reference to the event bus manager parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle widget close event.  Args: event: Close event"""
```
```python
    def hideEvent(self, event) -> None:
        """Handle widget hide event.  Args: event: Hide event"""
```
```python
    def showEvent(self, event) -> None:
        """Handle widget show event.  Args: event: Show event"""
```

#### Module: main_window
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/main_window.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, cast, Callable
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar, QPushButton, QScrollArea, QSizePolicy, QSplitter, QStackedWidget, QToolBar, QVBoxLayout, QWidget, QDockWidget
from qorzen.ui.ui_component import QWidget
from qorzen.utils.exceptions import UIError
```

**Classes:**
```python
class MainWindow(QMainWindow):
    """Main window class with support for async operations.

This class provides a main window for the Qorzen application with support for async operations and integration with the backend systems."""
```
*Methods:*
```python
    def __init__(self, app_core) -> None:
        """Initialize AsyncMainWindow.  Args: app_core: The application core"""
```
```python
    def add_menu_item(self, element_id, title, callback, parent_menu, icon, position, tooltip) -> None:
        """Add a menu item to a menu.

Args: element_id: ID of the menu item title: Text for the menu item callback: Function to call when the menu item is activated parent_menu: Name of the parent menu icon: Icon for the menu item position: Position in the menu tooltip: Tooltip text"""
```
```python
    def add_page(self, element_id, widget, title, icon, position) -> None:
        """Add a page to the main window.

Args: element_id: ID of the page widget: The page widget title: Title of the page icon: Icon for the page position: Position in the page list"""
```
```python
    def add_panel(self, element_id, panel, title, dock_area, icon, closable) -> None:
        """Add a panel to the main window.

Args: element_id: ID of the panel panel: The panel widget title: Title of the panel dock_area: Area to dock the panel (left, right, top, bottom) icon: Icon for the panel closable: Whether the panel can be closed"""
```
```python
    def add_toolbar_item(self, element_id, title, callback, icon, position, tooltip) -> None:
        """Add a toolbar item to the main window.

Args: element_id: ID of the toolbar item title: Text for the toolbar item callback: Function to call when the toolbar item is activated icon: Icon for the toolbar item position: Position in the toolbar tooltip: Tooltip text"""
```
```python
    def add_widget(self, element_id, widget, parent_id, title, position) -> None:
        """Add a widget to a parent container.

Args: element_id: ID of the widget widget: The widget to add parent_id: ID of the parent container title: Title of the widget position: Position in the container"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle the window close event.  Args: event: Close event"""
```
```python
    def get_menu(self, menu_name) -> Optional[QMenu]:
        """Get a menu by name.

Args: menu_name: Name of the menu

Returns: Optional[QMenu]: The menu object or None if not found"""
```
```python
    def remove_element(self, element_id) -> None:
        """Remove a UI element.  Args: element_id: ID of the element to remove"""
```
```python
    def select_page(self, page_name) -> None:
        """Select a page by name.  Args: page_name: Name of the page to select"""
```
```python
    def show_dialog(self, element_id, dialog, title, modal, width, height) -> None:
        """Show a dialog window.

Args: element_id: ID of the dialog dialog: The dialog widget title: Title of the dialog modal: Whether the dialog is modal width: Width of the dialog height: Height of the dialog"""
```
```python
    def show_notification(self, message, title, notification_type, duration) -> None:
        """Show a notification message.

Args: message: Message text title: Title of the notification notification_type: Type of notification (info, warning, error, success) duration: Duration in milliseconds"""
```
```python
    def update_element(self, element_id, visible, enabled, title, icon, tooltip) -> None:
        """Update a UI element's properties.

Args: element_id: ID of the element to update visible: Whether the element is visible enabled: Whether the element is enabled title: New title for the element icon: New icon for the element tooltip: New tooltip for the element"""
```
```python
    def update_plugin_state_ui(self, plugin_name, state) -> None:
        """Update the UI to reflect a plugin's state.

Args: plugin_name: Name of the plugin state: New state of the plugin"""
```

```python
class MainWindowPluginHandler(object):
```
*Methods:*
```python
    def __init__(self, main_window, plugin_manager, logger):
```
```python
    async def handle_plugin_reload(self, plugin_id) -> None:
```
```python
    async def handle_plugin_state_change(self, plugin_id, enable) -> None:
```

#### Module: plugins
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/plugins.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot, QObject
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget, QFileDialog, QMessageBox
from qorzen.core.plugin_manager import PluginInfo, PluginState
```

**Classes:**
```python
class AsyncTaskSignals(QObject):
```
*Class attributes:*
```python
started =     started = Signal()
result_ready =     result_ready = Signal(object)
error =     error = Signal(str, str)
finished =     finished = Signal()
```

```python
class PluginCard(QFrame):
```
*Class attributes:*
```python
stateChangeRequested =     stateChangeRequested = Signal(str, bool)
reloadRequested =     reloadRequested = Signal(str)
infoRequested =     infoRequested = Signal(str)
```
*Methods:*
```python
    def __init__(self, plugin_id, plugin_info, parent) -> None:
```
```python
    def update_info(self, plugin_info) -> None:
```

```python
class PluginsView(QWidget):
```
*Class attributes:*
```python
pluginStateChangeRequested =     pluginStateChangeRequested = Signal(str, bool)
pluginReloadRequested =     pluginReloadRequested = Signal(str)
pluginInfoRequested =     pluginInfoRequested = Signal(str)
```
*Methods:*
```python
    def __init__(self, plugin_manager, parent) -> None:
```
```python
    def cleanup(self) -> None:
```
```python
    def update_plugin_state_ui(self, plugin_name, state) -> None:
        """Update the UI state of a plugin by its name."""
```

#### Module: task_monitor
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/task_monitor.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
from typing import Dict, Optional, Any, List
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QScrollArea, QVBoxLayout, QWidget, QMessageBox
from qorzen.ui.ui_component import AsyncTaskSignals
```

**Classes:**
```python
class TaskMonitorWidget(QWidget):
    """Widget for monitoring all running tasks."""
```
*Methods:*
```python
    def __init__(self, event_bus_manager, parent) -> None:
        """Initialize the task monitor widget.

Args: event_bus_manager: Reference to the event bus manager parent: Parent widget"""
```
```python
    def cleanup(self) -> None:
        """Clean up resources when the widget is being destroyed."""
```

```python
class TaskProgressWidget(QFrame):
    """Widget for displaying a task's progress."""
```
*Methods:*
```python
    def __init__(self, task_id, plugin_name, task_name, parent) -> None:
        """Initialize a task progress widget.

Args: task_id: Unique task identifier plugin_name: Name of the plugin that owns the task task_name: Display name of the task parent: Parent widget"""
```
```python
    def mark_cancelled(self) -> None:
        """Mark the task as cancelled."""
```
```python
    def mark_completed(self) -> None:
        """Mark the task as completed."""
```
```python
    def mark_failed(self, error) -> None:
        """Mark the task as failed.  Args: error: Error message"""
```
```python
    def update_progress(self, progress, message) -> None:
        """Update the task progress.

Args: progress: Progress percentage (0-100) message: Optional progress message"""
```

#### Module: thread_safe_signaler
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/thread_safe_signaler.py`

**Imports:**
```python
from __future__ import annotations
import threading
from typing import Any, Callable, Optional, TypeVar
from PySide6.QtCore import QObject, Signal, Slot, Qt
```

**Global Variables:**
```python
T = T = TypeVar('T')
```

**Classes:**
```python
class ThreadSafeSignaler(QObject):
    """A utility class that helps safely emit Qt signals across threads. Always create this object on the main thread, then pass it to worker threads."""
```
*Class attributes:*
```python
signal_no_args =     signal_no_args = Signal()
signal_int =     signal_int = Signal(int)
signal_str =     signal_str = Signal(str)
signal_int_str =     signal_int_str = Signal(int, str)
signal_obj =     signal_obj = Signal(object)
signal_multi =     signal_multi = Signal(object, object, object)  # For up to 3 generic objects
```
*Methods:*
```python
    def __init__(self, thread_manager) -> None:
        """Initialize with a thread manager to ensure main thread execution.

Args: thread_manager: The ThreadManager instance for main thread delegation"""
```
```python
    def emit_safely(self, signal, *args) -> None:
        """Safely emit a signal, ensuring it happens on the main thread.

Args: signal: The signal to emit *args: Arguments to pass to the signal"""
```

#### Module: ui_component
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/ui_component.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
import traceback
import uuid
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union, cast, Awaitable
from PySide6.QtCore import QObject, Signal, Slot, Qt, QEvent
from PySide6.QtWidgets import QWidget
```

**Global Variables:**
```python
T = T = TypeVar('T')
```

**Functions:**
```python
def run_async(coro) -> T:
    """Run a coroutine synchronously.

This function is meant for simple, one-off async operations that need to be run synchronously from a UI event handler.

Args: coro: The coroutine to run

Returns: The result of the coroutine"""
```

**Classes:**
```python
class AsyncQWidget(QWidget):
    """Base widget class with async task support."""
```
*Methods:*
```python
    def __init__(self, parent, concurrency_manager) -> None:
        """Initialize AsyncQWidget."""
```
```python
    def cancel_all_tasks(self) -> int:
        """Cancel all running tasks."""
```
```python
    def cancel_task(self, task_id) -> bool:
        """Cancel a running task by ID."""
```
```python
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
```
```python
    def get_running_tasks_count(self) -> int:
        """Get the number of running tasks."""
```
```python
    def is_task_running(self, task_id) -> bool:
        """Check if a task is running."""
```
```python
    def run_async_task(self, coroutine_func, task_id, on_result, on_error, on_finished, *args, **kwargs) -> str:
        """Run an async task from a UI component.

This method is synchronous and returns immediately, running the coroutine in the background. The task is tracked and automatically managed.

Args: coroutine_func: The coroutine function to run *args: Arguments to pass to the coroutine task_id: Optional ID for the task on_result: Optional callback for when the task completes successfully on_error: Optional callback for when the task fails on_finished: Optional callback for when the task finishes (success or failure) **kwargs: Keyword arguments to pass to the coroutine

Returns: The task ID"""
```

```python
class AsyncTaskSignals(QObject):
    """Signals for async task communication."""
```
*Class attributes:*
```python
started =     started = Signal()
result_ready =     result_ready = Signal(object)
error =     error = Signal(str, str)
finished =     finished = Signal()
```

#### Module: ui_integration
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/ui_integration.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable, Protocol, TypeVar
from pydantic import BaseModel, Field, validator
from PySide6.QtCore import QObject, Signal, Slot, Qt
from qorzen.utils.exceptions import UIError
```

**Global Variables:**
```python
T = T = TypeVar('T')
```

**Classes:**
```python
class UICallbackProtocol(Protocol):
    """Protocol for UI callbacks that may be async or sync."""
```
*Methods:*
```python
    def __call__(self, *args, **kwargs) -> Any:
        """Ellipsis"""
```

```python
@dataclass
class UIElementInfo(object):
    """Information about a UI element."""
```

```python
class UIElementType(str, Enum):
    """Types of UI elements that can be managed by the UI integration system."""
```
*Class attributes:*
```python
PAGE = 'page'
WIDGET = 'widget'
MENU_ITEM = 'menu_item'
TOOLBAR_ITEM = 'toolbar_item'
DIALOG = 'dialog'
PANEL = 'panel'
NOTIFICATION = 'notification'
STATUS_BAR = 'status_bar'
DOCK = 'dock'
```

```python
class UIIntegration(object):
    """
    Asynchronous UI integration system that bridges between async backend and UI components.

    This class manages UI elements and handles interactions between plugins and the UI.
    It ensures that UI operations are executed on the main thread while allowing
    async operations to run in the background.
    """
```
*Methods:*
```python
    def __init__(self, main_window, concurrency_manager, logger_manager) -> None:
        """
        Initialize AsyncUIIntegration.

        Args:
            main_window: The main window of the application
            concurrency_manager: Manager for handling concurrency
            logger_manager: Manager for logging
        """
```
```python
    async def add_menu_item(self, plugin_id, title, callback, parent_menu, icon, position, tooltip, metadata) -> str:
        """
        Add a menu item to a menu.

        Args:
            plugin_id: ID of the plugin adding the menu item
            title: Text for the menu item
            callback: Function to call when the menu item is activated
            parent_menu: Name of the parent menu
            icon: Icon for the menu item
            position: Position in the menu
            tooltip: Tooltip text
            metadata: Additional metadata

        Returns:
            str: ID of the created menu item element
        """
```
```python
    async def add_page(self, plugin_id, page_component, title, icon, position, metadata) -> str:
        """
        Add a page to the main window.

        Args:
            plugin_id: ID of the plugin adding the page
            page_component: The page widget to add
            title: Title of the page
            icon: Icon for the page
            position: Position in the page list
            metadata: Additional metadata

        Returns:
            str: ID of the created page element
        """
```
```python
    async def add_panel(self, plugin_id, panel_component, title, dock_area, icon, closable, metadata) -> str:
        """
        Add a panel to the main window.

        Args:
            plugin_id: ID of the plugin adding the panel
            panel_component: The panel widget to add
            title: Title of the panel
            dock_area: Area to dock the panel (left, right, top, bottom)
            icon: Icon for the panel
            closable: Whether the panel can be closed
            metadata: Additional metadata

        Returns:
            str: ID of the created panel element
        """
```
```python
    async def add_toolbar_item(self, plugin_id, title, callback, icon, position, tooltip, metadata) -> str:
        """
        Add a toolbar item to the main window.

        Args:
            plugin_id: ID of the plugin adding the toolbar item
            title: Text for the toolbar item
            callback: Function to call when the toolbar item is activated
            icon: Icon for the toolbar item
            position: Position in the toolbar
            tooltip: Tooltip text
            metadata: Additional metadata

        Returns:
            str: ID of the created toolbar item element
        """
```
```python
    async def add_widget(self, plugin_id, widget_component, parent_id, title, position, metadata) -> str:
        """
        Add a widget to a parent container.

        Args:
            plugin_id: ID of the plugin adding the widget
            widget_component: The widget to add
            parent_id: ID of the parent container
            title: Title of the widget
            position: Position in the container
            metadata: Additional metadata

        Returns:
            str: ID of the created widget element
        """
```
```python
    async def clear_plugin_elements(self, plugin_id) -> int:
        """
        Remove all UI elements created by a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            int: Number of elements removed
        """
```
```python
    def get_all_elements(self) -> List[UIElementInfo]:
        """
        Get all UI elements.

        Returns:
            List[UIElementInfo]: List of all UI elements
        """
```
```python
    def get_element_info(self, element_id) -> Optional[UIElementInfo]:
        """
        Get information about a UI element.

        Args:
            element_id: ID of the element

        Returns:
            Optional[UIElementInfo]: Information about the element or None if not found
        """
```
```python
    def get_plugin_elements(self, plugin_id) -> List[UIElementInfo]:
        """
        Get all UI elements created by a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            List[UIElementInfo]: List of elements created by the plugin
        """
```
```python
    async def remove_element(self, element_id) -> bool:
        """
        Remove a UI element.

        Args:
            element_id: ID of the element to remove

        Returns:
            bool: Whether the element was successfully removed
        """
```
```python
    async def show_dialog(self, plugin_id, dialog_component, title, modal, width, height, metadata) -> str:
        """
        Show a dialog window.

        Args:
            plugin_id: ID of the plugin showing the dialog
            dialog_component: The dialog widget to show
            title: Title of the dialog
            modal: Whether the dialog is modal
            width: Width of the dialog
            height: Height of the dialog
            metadata: Additional metadata

        Returns:
            str: ID of the created dialog element
        """
```
```python
    async def show_notification(self, plugin_id, message, title, notification_type, duration, metadata) -> str:
        """
        Show a notification message.

        Args:
            plugin_id: ID of the plugin showing the notification
            message: Message text
            title: Title of the notification
            notification_type: Type of notification (info, warning, error, success)
            duration: Duration in milliseconds
            metadata: Additional metadata

        Returns:
            str: ID of the created notification element
        """
```
```python
    async def shutdown(self) -> None:
        """Shut down the UI integration system."""
```
```python
    async def update_element(self, element_id, visible, enabled, title, icon, tooltip, metadata) -> bool:
        """
        Update a UI element's properties.

        Args:
            element_id: ID of the element to update
            visible: Whether the element is visible
            enabled: Whether the element is enabled
            title: New title for the element
            icon: New icon for the element
            tooltip: New tooltip for the element
            metadata: Additional metadata to update

        Returns:
            bool: Whether the element was successfully updated
        """
```

```python
class UIOperation(str, Enum):
    """Operations that can be performed on UI elements."""
```
*Class attributes:*
```python
ADD = 'add'
REMOVE = 'remove'
UPDATE = 'update'
SHOW = 'show'
HIDE = 'hide'
```

```python
class UIOperationModel(BaseModel):
    """Model for UI operations to be executed on the main thread."""
```
*Methods:*
```python
@validator('element_info')
    def validate_element_info(cls, v) -> Dict[(str, Any)]:
        """Validate that element_info contains required fields."""
```

```python
class UISignals(QObject):
    """QObject to hold signals for UI operations."""
```
*Class attributes:*
```python
operation_ready =     operation_ready = Signal(object)  # Signal emitted when an operation is ready to be executed
```

### Package: utils
Path: `/home/runner/work/qorzen/qorzen/qorzen/utils`

**__init__.py:**
*Utility functions and classes for the Qorzen platform.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/utils/__init__.py`

**Imports:**
```python
from qorzen.utils.exceptions import APIError, ConfigurationError, DatabaseError, EventBusError, FileError, ManagerError, ManagerInitializationError, ManagerShutdownError, QorzenError, PluginError, SecurityError, ThreadManagerError
```

#### Module: exceptions
Path: `/home/runner/work/qorzen/qorzen/qorzen/utils/exceptions.py`

**Imports:**
```python
from __future__ import annotations
from typing import Any, Dict, Optional
```

**Classes:**
```python
class APIError(QorzenError):
    """Exception raised for API-related errors."""
```
*Methods:*
```python
    def __init__(self, message, status_code, endpoint, *args, **kwargs) -> None:
        """Initialize an APIError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. status_code: The HTTP status code associated with the error. endpoint: The API endpoint that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class ApplicationError(QorzenError):
    """Exception raised for application-related errors."""
```
*Methods:*
```python
    def __init__(self, message, *args, **kwargs) -> None:
        """Initialize an ApplicationError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. config_key: The configuration key that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class AsyncOperationError(QorzenError):
    """Exception raised for errors in asynchronous operations."""
```
*Methods:*
```python
    def __init__(self, message, operation, operation_id, *args, **kwargs) -> None:
        """Initialize AsyncOperationError.

Args: message: Error message *args: Additional positional arguments operation: The asynchronous operation that caused the error operation_id: The ID of the asynchronous operation **kwargs: Additional keyword arguments"""
```

```python
class ConfigurationError(QorzenError):
    """Exception raised for configuration-related errors."""
```
*Methods:*
```python
    def __init__(self, message, config_key, *args, **kwargs) -> None:
        """Initialize a ConfigurationError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. config_key: The configuration key that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class DatabaseError(QorzenError):
    """Exception raised for database-related errors."""
```
*Methods:*
```python
    def __init__(self, message, query, *args, **kwargs) -> None:
        """Initialize a DatabaseError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. query: The database query that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class DatabaseManagerInitializationError(ManagerError):
    """Exception raised when a database manager fails to initialize."""
```

```python
class DependencyError(QorzenError):
    """Exception raised for dependency manager errors."""
```
*Methods:*
```python
    def __init__(self, message, *args, **kwargs) -> None:
        """Initialize a DependencyError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. config_key: The configuration key that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class EventBusError(QorzenError):
    """Exception raised for event bus-related errors."""
```
*Methods:*
```python
    def __init__(self, message, event_type, *args, **kwargs) -> None:
        """Initialize an EventBusError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. event_type: The event type that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class FileError(QorzenError):
    """Exception raised for file-related errors."""
```
*Methods:*
```python
    def __init__(self, message, file_path, *args, **kwargs) -> None:
        """Initialize a FileError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. file_path: The path of the file that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class ManagerError(QorzenError):
    """Base exception for manager-related errors."""
```
*Methods:*
```python
    def __init__(self, message, manager_name, **kwargs) -> None:
        """Initialize manager error.

Args: message: Error message manager_name: Name of the affected manager **kwargs: Additional error information"""
```
```python
    def __str__(self) -> str:
        """String representation."""
```

```python
class ManagerInitializationError(ManagerError):
    """Exception raised when a manager fails to initialize."""
```

```python
class ManagerShutdownError(ManagerError):
    """Exception raised when a manager fails to shut down cleanly."""
```

```python
class PluginError(QorzenError):
    """Exception raised for plugin-related errors."""
```
*Methods:*
```python
    def __init__(self, message, plugin_name, *args, **kwargs) -> None:
        """Initialize a PluginError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. plugin_name: The name of the plugin that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class PluginIsolationError(QorzenError):
    """Exception raised when a plugin fails to isolate itself.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. plugin_name: The name of the plugin that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```
*Methods:*
```python
    def __init__(self, message, plugin_name, *args, **kwargs) -> None:
        """Initialize a PluginIsolationError."""
```

```python
class QorzenError(Exception):
    """Base exception for all Qorzen errors."""
```
*Methods:*
```python
    def __init__(self, message, **kwargs) -> None:
        """Initialize exception.  Args: message: Error message **kwargs: Additional error information"""
```
```python
    def __str__(self) -> str:
        """String representation."""
```

```python
class SecurityError(QorzenError):
    """Exception raised for security-related errors."""
```
*Methods:*
```python
    def __init__(self, message, user_id, permission, *args, **kwargs) -> None:
        """Initialize a SecurityError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. user_id: The ID of the user related to the security error. permission: The permission that was being checked. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

```python
class TaskError(QorzenError):
    """Error related to task execution."""
```
*Methods:*
```python
    def __init__(self, message, task_name, **kwargs) -> None:
        """Initialize threading error.

Args: message: Error message task_name: Name of affected thread **kwargs: Additional error information"""
```
```python
    def __str__(self) -> str:
        """String representation."""
```

```python
class ThreadManagerError(ManagerError):
    """Error in thread manager."""
```
*Methods:*
```python
    def __init__(self, message, thread_id, **kwargs) -> None:
        """Initialize thread manager error.

Args: message: Error message thread_id: Identifier of affected thread **kwargs: Additional error information"""
```
```python
    def __str__(self) -> str:
        """String representation."""
```

```python
class ThreadingError(QorzenError):
    """Error related to threading."""
```
*Methods:*
```python
    def __init__(self, message, thread_name, **kwargs) -> None:
        """Initialize threading error.

Args: message: Error message thread_name: Name of affected thread **kwargs: Additional error information"""
```
```python
    def __str__(self) -> str:
        """String representation."""
```

```python
class UIError(QorzenError):
    """Exception raised for UI-related errors."""
```
*Methods:*
```python
    def __init__(self, message, element_id, element_type, operation, *args, **kwargs) -> None:
        """Initialize UIError.

Args: message: Error message *args: Additional positional arguments element_id: The ID of the UI element where the error occurred element_type: The type of the UI element where the error occurred operation: The UI operation that caused the error **kwargs: Additional keyword arguments"""
```

```python
class WrongThreadError(ThreadingError):
    """Error when accessing UI elements from wrong thread."""
```
*Methods:*
```python
    def __init__(self, message, **kwargs) -> None:
        """Initialize wrong thread error.  Args: message: Error message **kwargs: Additional error information"""
```

#### Module: qt_thread_debug
Path: `/home/runner/work/qorzen/qorzen/qorzen/utils/qt_thread_debug.py`

**Imports:**
```python
from __future__ import annotations
import logging
import sys
import threading
import traceback
from typing import Any, Callable, Optional, List, Dict, Set
from PySide6.QtCore import QObject
```

**Global Variables:**
```python
original_excepthook = original_excepthook = sys.excepthook
original_stderr_write = original_stderr_write = sys.stderr.write
logger = logger = logging.getLogger('thread_debug')
QT_THREADING_VIOLATIONS = QT_THREADING_VIOLATIONS = [
    'QObject::setParent: Cannot set parent, new parent is in a different thread',
    'QObject::startTimer: Timers can only be used with threads started with QThread',
    'QObject: Cannot create children for a parent that is in a different thread',
    'QSocketNotifier: Socket notifiers cannot be enabled or disabled from another thread',
    'QWidget::repaint: Recursive repaint detected',
    'QPixmap: It is not safe to use pixmaps outside the GUI thread',
    'Cannot send events to objects owned by a different thread',
    'QObject::connect: Cannot queue arguments of type',
    'QObject::installEventFilter: Cannot filter events for objects in a different thread'
]
```

**Functions:**
```python
def clear_tracked_warnings() -> None:
    """Clear the stored warnings."""
```

```python
def enhanced_stderr_write(text) -> int:
    """Enhanced stderr handler that tracks Qt threading violations."""
```

```python
def get_violation_statistics() -> Dict[(str, Any)]:
    """Get statistics about threading violations."""
```

```python
def install_enhanced_thread_debug(enable_logging) -> None:
    """Install enhanced Qt thread debugging."""
```

```python
def monkey_patch_qobject() -> None:
    """Monkey patch QObject to track thread violations."""
```

```python
def uninstall_enhanced_thread_debug() -> None:
    """Remove enhanced thread debugging."""
```

**Classes:**
```python
class QtThreadMonitor(object):
    """Enhanced monitoring of Qt threading violations."""
```
*Methods:*
```python
@staticmethod
    def check_qobject_thread(obj) -> bool:
        """Check if a QObject is being accessed from its creation thread."""
```
```python
@staticmethod
    def register_qobject(obj) -> None:
        """Register a QObject and its creation thread."""
```

#### Module: qtasync
Path: `/home/runner/work/qorzen/qorzen/qorzen/utils/qtasync.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import functools
import sys
import threading
from typing import Any, Callable, Dict, Optional, Set, Tuple, TypeVar, cast, Coroutine, Awaitable
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QEventLoop, Qt
from PySide6.QtWidgets import QApplication
```

**Global Variables:**
```python
T = T = TypeVar('T')
```

**Functions:**
```python
def cancel_task(task_id) -> bool:
    """Cancel a task by ID.

Args: task_id: The ID of the task to cancel

Returns: True if the task was cancelled, False otherwise"""
```

```python
def get_bridge() -> QtAsyncBridge:
    """Get the global bridge instance, creating it if necessary.  Returns: The QtAsyncBridge instance"""
```

```python
def is_main_thread() -> bool:
    """Check if the current code is running in the main thread.

Returns: True if in main thread, False otherwise"""
```

```python
def run_coroutine(coro, task_id, on_result, on_error) -> str:
    """Helper function to run a coroutine through the bridge.

Args: coro: The coroutine to run task_id: Optional ID for the task (auto-generated if None) on_result: Optional callback for the result on_error: Optional callback for errors

Returns: The task ID"""
```

```python
def run_until_complete(coro) -> T:
    """Run a coroutine to completion, blocking until it finishes.

This should only be used for initialization or shutdown tasks, not from the UI thread during normal operation.

Args: coro: The coroutine to run

Returns: The result of the coroutine"""
```

```python
def shutdown_bridge() -> None:
    """Shutdown the bridge and cancel all tasks."""
```

**Classes:**
```python
class QtAsyncBridge(QObject):
    """Bridge between Qt and asyncio event loops.

This class provides utilities to run async code within Qt applications without blocking the UI thread and properly handling task cancellation."""
```
*Class attributes:*
```python
task_result =     task_result = Signal(object)
task_error =     task_error = Signal(str, str)
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the bridge."""
```
```python
    def cancel_all_tasks(self) -> int:
        """Cancel all running tasks.  Returns: The number of tasks that were cancelled"""
```
```python
    def cancel_task(self, task_id) -> bool:
        """Cancel a running task by ID.

Args: task_id: The ID of the task to cancel

Returns: True if the task was found and cancelled, False otherwise"""
```
```python
    def is_main_thread(self) -> bool:
        """Check if the current code is running in the main thread.

Returns: True if in main thread, False otherwise"""
```
```python
    def run_coroutine(self, coro, task_id, on_result, on_error) -> str:
        """Run a coroutine from the Qt event loop.

Args: coro: The coroutine to run task_id: Optional ID for the task (auto-generated if None) on_result: Optional callback for the result on_error: Optional callback for errors

Returns: The task ID"""
```
```python
    def shutdown(self) -> None:
        """Clean up resources on shutdown."""
```

