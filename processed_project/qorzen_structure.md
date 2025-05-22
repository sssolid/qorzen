# qorzen Project Structure
Generated on 2025-05-22 20:41:04

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
│   ├── database/
│   │   ├── connectors/
│   │   │   ├── __init__.py
│   │   │   ├── as400.py
│   │   │   ├── base.py
│   │   │   ├── odbc.py
│   │   │   └── sqlite.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── field_mapper.py
│   │   │   ├── history_manager.py
│   │   │   └── validation_engine.py
│   │   └── __init__.py
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
│   ├── database_connector_plugin/
│   │   ├── code/
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── export_service.py
│   │   │   │   └── query_service.py
│   │   │   ├── ui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connection_dialog.py
│   │   │   │   ├── field_mapping_tab.py
│   │   │   │   ├── history_tab.py
│   │   │   │   ├── main_tab.py
│   │   │   │   ├── main_widget.py
│   │   │   │   ├── query_dialog.py
│   │   │   │   ├── results_tab.py
│   │   │   │   └── validation_tab.py
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   └── plugin.py
│   │   ├── README.md
│   │   ├── __init__.py
│   │   └── manifest.json
│   ├── media_processor_plugin/
│   │   ├── code/
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── isnet_model.py
│   │   │   │   ├── modnet_model.py
│   │   │   │   ├── processing_config.py
│   │   │   │   └── u2net_model.py
│   │   │   ├── processors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── batch_processor.py
│   │   │   │   ├── media_processor.py
│   │   │   │   └── optimized_processor.py
│   │   │   ├── ui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ai_manager_dialog.py
│   │   │   │   ├── batch_dialog.py
│   │   │   │   ├── config_editor.py
│   │   │   │   ├── format_editor.py
│   │   │   │   ├── format_preview_widget.py
│   │   │   │   ├── main_widget.py
│   │   │   │   ├── output_preview_table.py
│   │   │   │   └── preview_widget.py
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ai_background_remover.py
│   │   │   │   ├── config_manager.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── font_manager.py
│   │   │   │   ├── image_utils.py
│   │   │   │   └── path_resolver.py
│   │   │   ├── __init__.py
│   │   │   └── plugin.py
│   │   ├── DOCUMENTATION.md
│   │   ├── README.md
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
│   ├── settings_manager.py
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
        """Shut down the application core.

This method ensures a clean shutdown of all managers and resources. It uses timeouts to prevent hanging on problematic components."""
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
import uuid
import asyncio
import functools
import importlib
import os
import time
from contextlib import asynccontextmanager
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TypeVar, Union, cast, Callable, Awaitable, AsyncGenerator, Type, Protocol, runtime_checkable, Tuple
import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import DatabaseError, ManagerInitializationError, ManagerShutdownError, DatabaseManagerInitializationError, SecurityError, ConfigurationError, ValidationError
```

**Global Variables:**
```python
T = T = TypeVar('T')
R = R = TypeVar('R')
```

**Functions:**
```python
def create_connection_config(self, name, db_type, **kwargs) -> DatabaseConnectionConfig:
    """Create a database connection configuration with validation.

Args: name: Connection name db_type: Database type **kwargs: Additional configuration parameters

Returns: Validated DatabaseConnectionConfig instance

Raises: ConfigurationError: If configuration is invalid"""
```

**Classes:**
```python
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
```
*Class attributes:*
```python
metadata =     metadata = MetaData(
        naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_%(constraint_name)s',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s'
        }
    )
```

```python
class ConnectionType(str, Enum):
    """Supported database connection types."""
```
*Class attributes:*
```python
POSTGRESQL = 'postgresql'
MYSQL = 'mysql'
SQLITE = 'sqlite'
ORACLE = 'oracle'
MSSQL = 'mssql'
AS400 = 'as400'
ODBC = 'odbc'
```

```python
class DatabaseConnection(object):
    """Represents a database connection with associated state and metrics."""
```
*Methods:*
```python
    def __init__(self, config) -> None:
        """Initialize a database connection.  Args: config: The database connection configuration"""
```

```python
class DatabaseConnectionConfig(object):
    """Configuration for a database connection."""
```
*Methods:*
```python
    def __init__(self, name, db_type, host, port, database, user, password, pool_size, max_overflow, pool_recycle, echo, connection_string, url, connection_timeout, properties, read_only, ssl, allowed_tables, dsn, jt400_jar_path, mapping_enabled, history_enabled, validation_enabled, history_connection_id, validation_connection_id) -> None:
        """Initialize a database connection configuration.

Args: name: Unique name for this connection db_type: Type of database (postgresql, mysql, sqlite, as400, odbc, etc.) host: Database host address port: Database port number database: Database name or SQLite file path user: Database username password: Database password pool_size: Connection pool size max_overflow: Maximum overflow connections pool_recycle: Connection recycling time in seconds echo: Enable SQLAlchemy logging connection_string: Full connection string (alternative to individual parameters) url: SQLAlchemy URL object (alternative to connection_string) connection_timeout: Connection timeout in seconds for SQLAlchemy engine creation properties: Additional connection properties read_only: Whether this connection is read-only ssl: Enable SSL for connection allowed_tables: Whitelist of allowed tables dsn: ODBC Data Source Name jt400_jar_path: Path to JT400 JAR file for AS/400 connections mapping_enabled: Enable field mapping for this connection history_enabled: Enable history tracking for this connection validation_enabled: Enable data validation for this connection history_connection_id: Connection ID to use for history storage validation_connection_id: Connection ID to use for validation storage"""
```

```python
@runtime_checkable
class DatabaseConnectorProtocol(Protocol):
    """Protocol defining the interface for database connectors."""
```
*Methods:*
```python
@property
    def config(self) -> 'DatabaseConnectionConfig':
        """Get the connection configuration."""
```
```python
    async def connect(self) -> None:
        """Connect to the database."""
```
```python
    async def disconnect(self) -> None:
        """Disconnect from the database."""
```
```python
    async def execute_query(self, query, params, limit) -> Dict[(str, Any)]:
        """Execute a query with parameters."""
```
```python
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get connection information."""
```
```python
    async def get_table_columns(self, table_name, schema) -> List[Dict[(str, Any)]]:
        """Get the columns of a table."""
```
```python
    async def get_tables(self, schema) -> List[Dict[(str, Any)]]:
        """Get a list of tables in the database."""
```
```python
@property
    def is_connected(self) -> bool:
        """Check if the connector is connected to the database."""
```
```python
    def set_database_manager(self, db_manager) -> None:
        """Set the database manager for this connector."""
```
```python
    async def test_connection(self) -> tuple[(bool, Optional[str])]:
        """Test the database connection."""
```

```python
class DatabaseManager(QorzenManager):
    """Enhanced Database Manager for handling multiple database types and features."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager) -> None:
        """Initialize the database manager.

Args: config_manager: The configuration manager instance logger_manager: The logger manager instance"""
```
```python
@asynccontextmanager
    async def async_session(self, connection_name) -> AsyncGenerator[(AsyncSession, None)]:
        """Get an asynchronous session for a connection.

Args: connection_name: The connection name, or None for default

Yields: AsyncSession: A SQLAlchemy async session

Raises: DatabaseError: If session creation fails"""
```
```python
    async def check_connection(self, connection_name) -> bool:
        """Check if a connection is working.

Args: connection_name: The connection name, or None for default

Returns: bool: True if connection is working"""
```
```python
    async def create_field_mapping(self, connection_id, table_name, mappings, description) -> Dict[(str, Any)]:
        """Create a field mapping for a table.

Args: connection_id: The connection ID table_name: The table name mappings: Dictionary of original field names to mapped names description: Optional description

Returns: Dict[str, Any]: The created mapping

Raises: DatabaseError: If field mapping creation fails"""
```
```python
    async def create_history_schedule(self, connection_id, query_id, frequency, name, description, retention_days) -> Dict[(str, Any)]:
        """Create a history tracking schedule.

Args: connection_id: The connection ID query_id: The query ID to execute frequency: Frequency expression (e.g., '1h', '1d', '7d') name: Schedule name description: Optional description retention_days: Number of days to retain history

Returns: Dict[str, Any]: The created schedule

Raises: DatabaseError: If schedule creation fails"""
```
```python
    async def create_tables(self, connection_name) -> None:
        """Create all tables in the metadata.

Args: connection_name: The connection name, or None for default

Raises: DatabaseError: If table creation fails"""
```
```python
    async def create_tables_async(self, connection_name) -> None:
        """Create all tables in the metadata asynchronously.

Args: connection_name: The connection name, or None for default

Raises: DatabaseError: If table creation fails"""
```
```python
    async def create_validation_rule(self, rule_type, connection_id, table_name, field_name, parameters, error_message, name, description) -> Dict[(str, Any)]:
        """Create a validation rule.

Args: rule_type: Type of validation rule connection_id: The connection ID table_name: The table name field_name: The field name parameters: Rule parameters error_message: Error message when validation fails name: Optional rule name description: Optional description

Returns: Dict[str, Any]: The created rule

Raises: DatabaseError: If rule creation fails"""
```
```python
    async def delete_field_mapping(self, mapping_id) -> bool:
        """Delete a field mapping.  Args: mapping_id: The mapping ID  Returns: bool: True if successful"""
```
```python
    async def delete_history_schedule(self, schedule_id) -> bool:
        """Delete a history tracking schedule.

Args: schedule_id: The schedule ID

Returns: bool: True if successful

Raises: DatabaseError: If schedule deletion fails"""
```
```python
    async def delete_validation_rule(self, rule_id) -> bool:
        """Delete a validation rule.

Args: rule_id: The rule ID

Returns: bool: True if successful

Raises: DatabaseError: If rule deletion fails"""
```
```python
    async def execute(self, statement, connection_name) -> List[Dict[(str, Any)]]:
        """Execute a SQLAlchemy statement.

Args: statement: The SQLAlchemy statement connection_name: The connection name, or None for default

Returns: List[Dict[str, Any]]: The query results

Raises: DatabaseError: If execution fails"""
```
```python
    async def execute_async(self, statement, connection_name) -> List[Dict[(str, Any)]]:
        """Execute a SQLAlchemy statement asynchronously.

Args: statement: The SQLAlchemy statement connection_name: The connection name, or None for default

Returns: List[Dict[str, Any]]: The query results

Raises: DatabaseError: If execution fails"""
```
```python
    async def execute_history_schedule_now(self, schedule_id) -> Dict[(str, Any)]:
        """Execute a history tracking schedule immediately.

Args: schedule_id: The schedule ID

Returns: Dict[str, Any]: The execution result

Raises: DatabaseError: If execution fails"""
```
```python
    async def execute_query(self, query, params, connection_name, limit, apply_mapping) -> Dict[(str, Any)]:
        """Execute a query with parameters.

This is the preferred method for executing queries, especially with specialized connectors.

Args: query: The SQL query params: Query parameters connection_name: The connection name, or None for default limit: Maximum number of rows to return apply_mapping: Whether to apply field mapping

Returns: Dict[str, Any]: The query results

Raises: DatabaseError: If execution fails"""
```
```python
    async def execute_raw(self, sql, params, connection_name, limit) -> List[Dict[(str, Any)]]:
        """Execute a raw SQL statement.

Args: sql: The SQL statement params: Query parameters connection_name: The connection name, or None for default limit: Maximum number of rows to return

Returns: List[Dict[str, Any]]: The query results

Raises: DatabaseError: If execution fails"""
```
```python
    async def get_all_field_mappings(self, connection_id) -> List[Dict[(str, Any)]]:
        """Get all field mappings, optionally filtered by connection ID.

Args: connection_id: The connection ID to filter by

Returns: List[Dict[str, Any]]: List of field mappings"""
```
```python
    async def get_all_history_schedules(self) -> List[Dict[(str, Any)]]:
        """Get all history tracking schedules.  Returns: List[Dict[str, Any]]: List of schedules"""
```
```python
    async def get_all_validation_rules(self, connection_id, table_name) -> List[Dict[(str, Any)]]:
        """Get all validation rules, optionally filtered.

Args: connection_id: The connection ID to filter by table_name: The table name to filter by

Returns: List[Dict[str, Any]]: List of validation rules"""
```
```python
    async def get_async_engine(self, connection_name) -> Optional[AsyncEngine]:
        """Get the SQLAlchemy async engine for a connection.

Args: connection_name: The connection name, or None for default

Returns: Optional[AsyncEngine]: The SQLAlchemy async engine, or None if not available"""
```
```python
    async def get_connection_names(self) -> List[str]:
        """Get a list of connection names.  Returns: List[str]: List of connection names"""
```
```python
    async def get_engine(self, connection_name) -> Optional[Engine]:
        """Get the SQLAlchemy engine for a connection.

Args: connection_name: The connection name, or None for default

Returns: Optional[Engine]: The SQLAlchemy engine, or None if not available"""
```
```python
    async def get_field_mapping(self, connection_id, table_name) -> Optional[Dict[(str, Any)]]:
        """Get a field mapping for a table.

Args: connection_id: The connection ID table_name: The table name

Returns: Optional[Dict[str, Any]]: The field mapping, or None if not found"""
```
```python
    async def get_history_data(self, snapshot_id) -> Optional[Dict[(str, Any)]]:
        """Get history data for a snapshot.

Args: snapshot_id: The snapshot ID

Returns: Optional[Dict[str, Any]]: The history data, or None if not found"""
```
```python
    async def get_history_entries(self, schedule_id, limit) -> List[Dict[(str, Any)]]:
        """Get history entries, optionally filtered by schedule ID.

Args: schedule_id: The schedule ID to filter by limit: Maximum number of entries to return

Returns: List[Dict[str, Any]]: List of history entries"""
```
```python
    async def get_history_schedule(self, schedule_id) -> Optional[Dict[(str, Any)]]:
        """Get a history tracking schedule.

Args: schedule_id: The schedule ID

Returns: Optional[Dict[str, Any]]: The schedule, or None if not found"""
```
```python
    def get_supported_connection_types(self) -> List[str]:
        """Get list of supported database connection types.

Returns: List of supported connection type strings"""
```
```python
    async def get_table_columns(self, table_name, connection_name, schema) -> List[Dict[(str, Any)]]:
        """Get column information for a table.

Args: table_name: The table name connection_name: The connection name, or None for default schema: Schema/database name

Returns: List[Dict[str, Any]]: List of column metadata

Raises: DatabaseError: If operation fails"""
```
```python
    async def get_tables(self, connection_name, schema) -> List[Dict[(str, Any)]]:
        """Get a list of tables for a connection.

Args: connection_name: The connection name, or None for default schema: Schema/database name to filter tables

Returns: List[Dict[str, Any]]: List of table metadata

Raises: DatabaseError: If operation fails"""
```
```python
    async def get_validation_rule(self, rule_id) -> Optional[Dict[(str, Any)]]:
        """Get a validation rule.

Args: rule_id: The rule ID

Returns: Optional[Dict[str, Any]]: The rule, or None if not found"""
```
```python
    async def has_connection(self, name) -> bool:
        """Check if a connection exists.

Args: name: The connection name

Returns: bool: True if the connection exists"""
```
```python
    async def initialize(self) -> None:
        """Initialize the Database Manager.

This method sets up the database manager, establishes the default connection, and initializes utility features if configured.

Raises: DatabaseManagerInitializationError: If critical initialization fails."""
```
```python
    async def register_connection(self, config) -> None:
        """Register a new database connection.

Args: config: The connection configuration

Raises: DatabaseError: If registration fails"""
```
```python
    def register_connector_type(self, connection_type, connector_class) -> None:
        """Register a connector class for a connection type.

Args: connection_type: The connection type name connector_class: The connector class to register"""
```
```python
@asynccontextmanager
    async def session(self, connection_name) -> AsyncGenerator[(Session, None)]:
        """Get a synchronous session for a connection.

Args: connection_name: The connection name, or None for default

Yields: Session: A SQLAlchemy session

Raises: DatabaseError: If session creation fails"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the database manager.  Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the database manager.  Returns: Dict[str, Any]: Status information"""
```
```python
    async def test_connection_config(self, config) -> Tuple[(bool, Optional[str])]:
        """Test a database connection configuration without registering it.

Args: config: Database connection configuration to test

Returns: Tuple of (success, error_message)"""
```
```python
    async def unregister_connection(self, name) -> bool:
        """Unregister a database connection.

Args: name: The connection name

Returns: bool: True if successful, False otherwise

Raises: DatabaseError: If trying to unregister the default connection"""
```
```python
    async def update_history_schedule(self, schedule_id, **updates) -> Dict[(str, Any)]:
        """Update a history tracking schedule.

Args: schedule_id: The schedule ID **updates: Fields to update

Returns: Dict[str, Any]: The updated schedule

Raises: DatabaseError: If schedule update fails"""
```
```python
    async def update_validation_rule(self, rule_id, **updates) -> Dict[(str, Any)]:
        """Update a validation rule.

Args: rule_id: The rule ID **updates: Fields to update

Returns: Dict[str, Any]: The updated rule

Raises: DatabaseError: If rule update fails"""
```
```python
    def validate_connection_config(self, config) -> Tuple[(bool, Optional[str])]:
        """Validate a database connection configuration.

Args: config: Configuration to validate

Returns: Tuple of (is_valid, error_message)"""
```
```python
    async def validate_data(self, connection_id, table_name, data) -> List[Dict[(str, Any)]]:
        """Validate data against all rules for a table.

Args: connection_id: The connection ID table_name: The table name data: The data to validate

Returns: List[Dict[str, Any]]: Validation results

Raises: ValidationError: If validation fails"""
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
    async def file_exists(self, path) -> bool:
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
from colorlog import ColoredFormatter
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, EventBusError
```

**Classes:**
```python
class ClickablePathFormatter(ColoredFormatter):
    """Colours only timestamp/level but emits the file path as a posix-style string so PyCharm will hyperlink it."""
```
*Methods:*
```python
    def format(self, record):
```

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

Attributes: id: Unique user ID user: Username email: Email address hashed_password: Hashed password roles: List of user roles active: Whether the user is active created_at: When the user was created last_login: When the user last logged in metadata: Additional metadata"""
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
        """Shut down the task manager.

This method ensures all tasks are properly cancelled and cleaned up during application shutdown.

Raises: ManagerShutdownError: If the shutdown process fails critically."""
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

#### Package: database
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database`

**__init__.py:**
*Core database package for Qorzen.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/__init__.py`

**Imports:**
```python
from qorzen.core.database_manager import DatabaseManager
```

**Global Variables:**
```python
__all__ = __all__ = ["DatabaseManager"]
```

##### Package: connectors
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/connectors`

**__init__.py:**
*Database connectors for the Database Manager.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/connectors/__init__.py`

**Imports:**
```python
from qorzen.core.database.connectors.base import BaseDatabaseConnector
from qorzen.core.database.connectors.sqlite import SQLiteConnector
from qorzen.core.database.connectors.odbc import ODBCConnector
from qorzen.core.database.connectors.as400 import AS400Connector
```

**Global Variables:**
```python
__all__ = __all__ = [
    "BaseDatabaseConnector",
    "SQLiteConnector",
    "ODBCConnector",
    "AS400Connector"
]
```

###### Module: as400
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/connectors/as400.py`

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
from base import BaseDatabaseConnector
```

**Classes:**
```python
class AS400Connector(BaseDatabaseConnector):
    """Connector for AS400/iSeries databases."""
```
*Methods:*
```python
    def __init__(self, config, logger, security_manager) -> None:
        """Initialize the AS400 connector.

Args: config: The connection configuration logger: Logger instance security_manager: Optional security manager

Raises: ImportError: If JPype is not installed"""
```
```python
    async def connect(self) -> None:
        """Connect to the AS400 database.

Raises: DatabaseError: If connection fails SecurityError: If connection is denied due to permissions"""
```
```python
    async def disconnect(self) -> None:
        """Disconnect from the AS400 database.  Raises: DatabaseError: If disconnection fails"""
```
```python
    async def execute_query(self, query, params, limit) -> Dict[(str, Any)]:
        """Execute a query with parameters.

Args: query: The SQL query params: Query parameters limit: Maximum number of rows to return

Returns: Dict[str, Any]: The query results

Raises: DatabaseError: If query execution fails SecurityError: If query execution is denied due to permissions"""
```
```python
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get connection information.  Returns: Dict[str, Any]: Connection information"""
```
```python
    async def get_table_columns(self, table_name, schema) -> List[Dict[(str, Any)]]:
        """Get the columns of a table.

Args: table_name: The table name schema: Schema/database name

Returns: List[Dict[str, Any]]: List of column metadata

Raises: DatabaseError: If operation fails"""
```
```python
    async def get_tables(self, schema) -> List[Dict[(str, Any)]]:
        """Get a list of tables in the database.

Args: schema: Schema/database name to filter tables

Returns: List[Dict[str, Any]]: List of table metadata

Raises: DatabaseError: If operation fails"""
```

###### Module: base
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/connectors/base.py`

**Imports:**
```python
from __future__ import annotations
import abc
import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Protocol, TypeVar, cast
```

**Global Variables:**
```python
T = T = TypeVar('T', bound='BaseConnectionConfig')
```

**Classes:**
```python
class BaseDatabaseConnector(abc.ABC):
    """Base class for all database connectors."""
```
*Methods:*
```python
    def __init__(self, config, logger, security_manager) -> None:
        """Initialize the database connector.

Args: config: The connection configuration logger: Logger instance security_manager: Optional security manager"""
```
```python
    async def cancel_query(self) -> bool:
        """Cancel the currently executing query.  Returns: bool: True if cancellation was successful"""
```
```python
@property
    def config(self) -> Any:
        """Get the connection configuration.  Returns: Any: The connection configuration"""
```
```python
@abc.abstractmethod
    async def connect(self) -> None:
        """Connect to the database.  Raises: DatabaseError: If connection fails"""
```
```python
@property
    def database_manager(self) -> Optional[Any]:
        """Get the database manager.  Returns: Optional[Any]: The database manager"""
```
```python
@abc.abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the database.  Raises: DatabaseError: If disconnection fails"""
```
```python
@abc.abstractmethod
    async def execute_query(self, query, params, limit) -> Dict[(str, Any)]:
        """Execute a query with parameters.

Args: query: The SQL query params: Query parameters limit: Maximum number of rows to return

Returns: Dict[str, Any]: The query results

Raises: DatabaseError: If query execution fails"""
```
```python
@abc.abstractmethod
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get connection information.  Returns: Dict[str, Any]: Connection information"""
```
```python
@abc.abstractmethod
    async def get_table_columns(self, table_name, schema) -> List[Dict[(str, Any)]]:
        """Get the columns of a table.

Args: table_name: The table name schema: Schema/database name

Returns: List[Dict[str, Any]]: List of column metadata

Raises: DatabaseError: If operation fails"""
```
```python
@abc.abstractmethod
    async def get_tables(self, schema) -> List[Dict[(str, Any)]]:
        """Get a list of tables in the database.

Args: schema: Schema/database name to filter tables

Returns: List[Dict[str, Any]]: List of table metadata

Raises: DatabaseError: If operation fails"""
```
```python
@property
    def is_connected(self) -> bool:
        """Check if the connector is connected to the database.  Returns: bool: True if connected"""
```
```python
    def set_database_manager(self, db_manager) -> None:
        """Set the database manager for this connector.  Args: db_manager: The database manager"""
```
```python
    async def test_connection(self) -> Tuple[(bool, Optional[str])]:
        """Test the database connection.  Returns: Tuple[bool, Optional[str]]: (success, error_message)"""
```

###### Module: odbc
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/connectors/odbc.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from base import BaseDatabaseConnector
```

**Classes:**
```python
class ODBCConnector(BaseDatabaseConnector):
    """Connector for ODBC databases including FileMaker."""
```
*Methods:*
```python
    def __init__(self, config, logger, security_manager) -> None:
        """Initialize the ODBC connector.

Args: config: The connection configuration logger: Logger instance security_manager: Optional security manager

Raises: ImportError: If pyodbc is not installed"""
```
```python
    async def connect(self) -> None:
        """Connect to the ODBC database.

Raises: DatabaseError: If connection fails SecurityError: If connection is denied due to permissions"""
```
```python
    async def disconnect(self) -> None:
        """Disconnect from the ODBC database.  Raises: DatabaseError: If disconnection fails"""
```
```python
    async def execute_query(self, query, params, limit) -> Dict[(str, Any)]:
        """Execute a query with parameters.

Args: query: The SQL query params: Query parameters limit: Maximum number of rows to return

Returns: Dict[str, Any]: The query results

Raises: DatabaseError: If query execution fails SecurityError: If query execution is denied due to permissions"""
```
```python
    def get_connection_info(self) -> Dict[(str, Any)]:
        """Get connection information.  Returns: Dict[str, Any]: Connection information"""
```
```python
    async def get_table_columns(self, table_name, schema) -> List[Dict[(str, Any)]]:
        """Get the columns of a table.

Args: table_name: The table name schema: Schema/database name

Returns: List[Dict[str, Any]]: List of column metadata

Raises: DatabaseError: If operation fails"""
```
```python
    async def get_tables(self, schema) -> List[Dict[(str, Any)]]:
        """Get a list of tables in the database.

Args: schema: Schema/database name to filter tables

Returns: List[Dict[str, Any]]: List of table metadata

Raises: DatabaseError: If operation fails"""
```

###### Module: sqlite
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/connectors/sqlite.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, AsyncGenerator
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from qorzen.utils.exceptions import DatabaseError, SecurityError, ConfigurationError
from base import BaseDatabaseConnector
```

**Classes:**
```python
class AsyncCompatibleSession(object):
    """A wrapper around synchronous SQLite session to provide async interface."""
```
*Methods:*
```python
    async def __aenter__(self) -> 'AsyncCompatibleSession':
        """Async context manager entry point."""
```
```python
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit point."""
```
```python
    def __init__(self, sync_session, loop) -> None:
        """Initialize the async-compatible session wrapper.

Args: sync_session: The synchronous SQLite session loop: The asyncio event loop for executing synchronous operations"""
```
```python
    async def close(self) -> None:
        """Close the session asynchronously."""
```
```python
    async def commit(self) -> None:
        """Commit the session asynchronously."""
```
```python
    async def execute(self, statement, *args, **kwargs) -> Any:
        """Execute a statement asynchronously.

Args: statement: The SQL statement to execute *args: Positional arguments **kwargs: Keyword arguments

Returns: The result of the execution"""
```
```python
    async def rollback(self) -> None:
        """Rollback the session asynchronously."""
```

```python
class SQLiteConnector(BaseDatabaseConnector):
```
*Methods:*
```python
    def __init__(self, config, logger, security_manager) -> None:
```
```python
    async def async_session(self) -> AsyncGenerator[(AsyncCompatibleSession, None)]:
        """Provide an async-compatible session for SQLite.

This method bridges the gap between synchronous SQLite and async code by wrapping a synchronous session in an async-compatible interface.

Yields: AsyncCompatibleSession: An async-compatible session wrapper

Raises: DatabaseError: If the connection is not initialized or session creation fails"""
```
```python
    async def connect(self) -> None:
```
```python
    async def disconnect(self) -> None:
```
```python
    async def execute_query(self, query, params, limit) -> Dict[(str, Any)]:
```
```python
    def get_connection_info(self) -> Dict[(str, Any)]:
```
```python
    async def get_table_columns(self, table_name, schema) -> List[Dict[(str, Any)]]:
```
```python
    async def get_tables(self, schema) -> List[Dict[(str, Any)]]:
```

##### Package: utils
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/utils`

**__init__.py:**
*Utility modules for the Database Manager.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/utils/__init__.py`

**Imports:**
```python
from qorzen.core.database.utils.field_mapper import FieldMapperManager, standardize_field_name
from qorzen.core.database.utils.history_manager import HistoryManager
from qorzen.core.database.utils.validation_engine import ValidationEngine, ValidationRuleType, create_range_rule, create_pattern_rule, create_not_null_rule, create_length_rule, create_enumeration_rule
```

**Global Variables:**
```python
__all__ = __all__ = [
    "FieldMapperManager",
    "standardize_field_name",
    "HistoryManager",
    "ValidationEngine",
    "ValidationRuleType",
    "create_range_rule",
    "create_pattern_rule",
    "create_not_null_rule",
    "create_length_rule",
    "create_enumeration_rule"
]
```

###### Module: field_mapper
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/utils/field_mapper.py`

**Imports:**
```python
from __future__ import annotations
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from sqlalchemy import text
from qorzen.utils.exceptions import DatabaseError
```

**Functions:**
```python
def standardize_field_name(field_name) -> str:
    """Convert a field name to a standardized format.

This converts camelCase or other formats to snake_case.

Args: field_name: The original field name

Returns: str: The standardized field name"""
```

**Classes:**
```python
class FieldMapperManager(object):
    """Manager for field mapping operations."""
```
*Methods:*
```python
    def __init__(self, database_manager, logger) -> None:
        """Initialize the field mapper manager.

Args: database_manager: The database manager instance logger: Logger instance"""
```
```python
    async def apply_mapping_to_query(self, query, mapping) -> str:
        """Apply a mapping to a SQL query.

Args: query: The SQL query mapping: The field mapping

Returns: str: The modified query with field mappings applied"""
```
```python
    async def apply_mapping_to_results(self, result, mapping) -> Dict[(str, Any)]:
        """Apply a mapping to query results.

Args: result: The query result mapping: The field mapping

Returns: Dict[str, Any]: The modified result with mapped field names"""
```
```python
    async def create_mapping(self, connection_id, table_name, mappings, description) -> Dict[(str, Any)]:
        """Create a field mapping.

Args: connection_id: The database connection ID table_name: The table name mappings: Dictionary of original field names to mapped names description: Optional description

Returns: Dict[str, Any]: The created mapping

Raises: DatabaseError: If mapping creation fails"""
```
```python
    async def create_mapping_from_fields(self, connection_id, table_name, field_names, description) -> Dict[(str, Any)]:
        """Create a field mapping from a list of field names.

Args: connection_id: The database connection ID table_name: The table name field_names: List of field names to map description: Optional description

Returns: Dict[str, Any]: The created mapping

Raises: DatabaseError: If mapping creation fails"""
```
```python
    async def delete_mapping(self, mapping_id) -> bool:
        """Delete a field mapping.

Args: mapping_id: The mapping ID

Returns: bool: True if successful

Raises: DatabaseError: If mapping deletion fails"""
```
```python
    async def get_all_mappings(self, connection_id) -> List[Dict[(str, Any)]]:
        """Get all field mappings.

Args: connection_id: Optional connection ID to filter by

Returns: List[Dict[str, Any]]: List of mappings

Raises: DatabaseError: If operation fails"""
```
```python
    async def get_mapping(self, connection_id, table_name) -> Optional[Dict[(str, Any)]]:
        """Get a field mapping for a table.

Args: connection_id: The database connection ID table_name: The table name

Returns: Optional[Dict[str, Any]]: The mapping, or None if not found

Raises: DatabaseError: If operation fails"""
```
```python
    async def get_mapping_by_id(self, mapping_id) -> Optional[Dict[(str, Any)]]:
        """Get a field mapping by ID.

Args: mapping_id: The mapping ID

Returns: Optional[Dict[str, Any]]: The mapping, or None if not found

Raises: DatabaseError: If operation fails"""
```
```python
    async def initialize(self) -> None:
        """Initialize the field mapper.

This method sets up the field mapper and creates necessary tables. It gracefully handles cases where async sessions aren't supported.

Raises: DatabaseError: If initialization fails and is critical."""
```
```python
    async def shutdown(self) -> None:
        """Shut down the field mapper system."""
```
```python
@staticmethod
    def standardize_field_name(field_name) -> str:
        """Convert a field name to a standardized format.

This converts camelCase or other formats to snake_case.

Args: field_name: The original field name

Returns: str: The standardized field name"""
```
```python
    async def update_mapping(self, mapping_id, mappings, description) -> Dict[(str, Any)]:
        """Update an existing field mapping.

Args: mapping_id: The mapping ID mappings: Dictionary of original field names to mapped names description: Optional description

Returns: Dict[str, Any]: The updated mapping

Raises: DatabaseError: If mapping update fails"""
```

###### Module: history_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/utils/history_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from sqlalchemy import text
from qorzen.utils.exceptions import DatabaseError
```

**Classes:**
```python
class HistoryManager(object):
    """Manager for database history tracking operations."""
```
*Methods:*
```python
    def __init__(self, database_manager, logger, history_connection_id) -> None:
        """Initialize the history manager.

Args: database_manager: The database manager instance logger: Logger instance history_connection_id: Connection ID for storing history data"""
```
```python
    async def create_schedule(self, connection_id, query_id, frequency, name, description, retention_days) -> Dict[(str, Any)]:
        """Create a history collection schedule.

Args: connection_id: The connection ID to collect from query_id: The query ID to execute frequency: Frequency expression (e.g., '1h', '1d', '7d') name: Schedule name description: Optional description retention_days: Number of days to retain history

Returns: Dict[str, Any]: The created schedule

Raises: DatabaseError: If schedule creation fails"""
```
```python
    async def delete_history_data(self, snapshot_id) -> bool:
        """Delete history data for a snapshot.

Args: snapshot_id: The snapshot ID

Returns: bool: True if successful

Raises: DatabaseError: If deletion fails"""
```
```python
    async def delete_schedule(self, schedule_id) -> bool:
        """Delete a history collection schedule.

Args: schedule_id: The schedule ID

Returns: bool: True if successful

Raises: DatabaseError: If schedule deletion fails"""
```
```python
    async def execute_schedule_now(self, schedule_id) -> Dict[(str, Any)]:
        """Execute a history collection schedule immediately.

Args: schedule_id: The schedule ID

Returns: Dict[str, Any]: The execution result

Raises: DatabaseError: If execution fails"""
```
```python
    async def get_all_schedules(self) -> List[Dict[(str, Any)]]:
        """Get all history collection schedules.

Returns: List[Dict[str, Any]]: List of schedules

Raises: DatabaseError: If getting schedules fails"""
```
```python
    async def get_history_data(self, snapshot_id) -> Optional[Dict[(str, Any)]]:
        """Get history data for a snapshot.

Args: snapshot_id: The snapshot ID

Returns: Optional[Dict[str, Any]]: The history data, or None if not found

Raises: DatabaseError: If getting data fails"""
```
```python
    async def get_history_entries(self, schedule_id, limit) -> List[Dict[(str, Any)]]:
        """Get history entries, optionally filtered by schedule ID.

Args: schedule_id: Optional schedule ID to filter by limit: Maximum number of entries to return

Returns: List[Dict[str, Any]]: List of history entries

Raises: DatabaseError: If getting entries fails"""
```
```python
    async def get_schedule(self, schedule_id) -> Optional[Dict[(str, Any)]]:
        """Get a history collection schedule.

Args: schedule_id: The schedule ID

Returns: Optional[Dict[str, Any]]: The schedule, or None if not found

Raises: DatabaseError: If getting schedule fails"""
```
```python
    async def initialize(self) -> None:
        """Initialize the history manager.

This method sets up the history tracking system and creates necessary tables. It handles database systems that don't support async sessions.

Raises: DatabaseError: If initialization fails and is critical."""
```
```python
    async def shutdown(self) -> None:
        """Shut down the history manager."""
```
```python
    async def start_schedule(self, schedule) -> None:
        """Start a history collection schedule.

Args: schedule: The schedule to start

Raises: DatabaseError: If starting schedule fails"""
```
```python
    async def stop_schedule(self, schedule_id) -> None:
        """Stop a history collection schedule.

Args: schedule_id: The schedule ID

Raises: DatabaseError: If stopping schedule fails"""
```
```python
    async def update_schedule(self, schedule_id, **updates) -> Dict[(str, Any)]:
        """Update a history collection schedule.

Args: schedule_id: The schedule ID **updates: Fields to update

Returns: Dict[str, Any]: The updated schedule

Raises: DatabaseError: If schedule update fails"""
```

###### Module: validation_engine
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database/utils/validation_engine.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import datetime
import json
import re
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Callable
from sqlalchemy import text
from qorzen.utils.exceptions import DatabaseError, ValidationError
```

**Functions:**
```python
async def create_enumeration_rule(validation_engine, connection_id, table_name, field_name, allowed_values, name, description, error_message) -> Dict[(str, Any)]:
    """Create an enumeration validation rule.

Args: validation_engine: The validation engine connection_id: The connection ID table_name: The table name field_name: The field name allowed_values: List of allowed values name: Optional rule name description: Optional description error_message: Optional error message

Returns: Dict[str, Any]: The created rule

Raises: DatabaseError: If rule creation fails"""
```

```python
async def create_length_rule(validation_engine, connection_id, table_name, field_name, min_length, max_length, name, description, error_message) -> Dict[(str, Any)]:
    """Create a length validation rule.

Args: validation_engine: The validation engine connection_id: The connection ID table_name: The table name field_name: The field name min_length: Optional minimum length max_length: Optional maximum length name: Optional rule name description: Optional description error_message: Optional error message

Returns: Dict[str, Any]: The created rule

Raises: DatabaseError: If rule creation fails"""
```

```python
async def create_not_null_rule(validation_engine, connection_id, table_name, field_name, name, description, error_message) -> Dict[(str, Any)]:
    """Create a not-null validation rule.

Args: validation_engine: The validation engine connection_id: The connection ID table_name: The table name field_name: The field name name: Optional rule name description: Optional description error_message: Optional error message

Returns: Dict[str, Any]: The created rule

Raises: DatabaseError: If rule creation fails"""
```

```python
async def create_pattern_rule(validation_engine, connection_id, table_name, field_name, pattern, name, description, error_message) -> Dict[(str, Any)]:
    """Create a pattern validation rule.

Args: validation_engine: The validation engine connection_id: The connection ID table_name: The table name field_name: The field name pattern: Regular expression pattern name: Optional rule name description: Optional description error_message: Optional error message

Returns: Dict[str, Any]: The created rule

Raises: DatabaseError: If rule creation fails"""
```

```python
async def create_range_rule(validation_engine, connection_id, table_name, field_name, min_value, max_value, name, description, error_message) -> Dict[(str, Any)]:
    """Create a range validation rule.

Args: validation_engine: The validation engine connection_id: The connection ID table_name: The table name field_name: The field name min_value: Optional minimum value max_value: Optional maximum value name: Optional rule name description: Optional description error_message: Optional error message

Returns: Dict[str, Any]: The created rule

Raises: DatabaseError: If rule creation fails"""
```

**Classes:**
```python
class ValidationEngine(object):
    """Engine for data validation operations."""
```
*Methods:*
```python
    def __init__(self, database_manager, logger, validation_connection_id) -> None:
        """Initialize the validation engine.

Args: database_manager: The database manager instance logger: Logger instance validation_connection_id: Connection ID for storing validation data"""
```
```python
    async def create_rule(self, rule_type, connection_id, table_name, field_name, parameters, error_message, name, description) -> Dict[(str, Any)]:
        """Create a validation rule.

Args: rule_type: Type of validation rule connection_id: The connection ID table_name: The table name field_name: The field name parameters: Rule parameters error_message: Error message when validation fails name: Optional rule name description: Optional description

Returns: Dict[str, Any]: The created rule

Raises: DatabaseError: If rule creation fails ValueError: If rule parameters are invalid"""
```
```python
    async def delete_rule(self, rule_id) -> bool:
        """Delete a validation rule.

Args: rule_id: The rule ID

Returns: bool: True if successful

Raises: DatabaseError: If rule deletion fails"""
```
```python
    async def get_all_rules(self, connection_id, table_name) -> List[Dict[(str, Any)]]:
        """Get all validation rules, optionally filtered.

Args: connection_id: The connection ID to filter by table_name: The table name to filter by

Returns: List[Dict[str, Any]]: List of validation rules

Raises: DatabaseError: If getting rules fails"""
```
```python
    async def get_rule(self, rule_id) -> Optional[Dict[(str, Any)]]:
        """Get a validation rule.

Args: rule_id: The rule ID

Returns: Optional[Dict[str, Any]]: The rule, or None if not found

Raises: DatabaseError: If getting rule fails"""
```
```python
    async def get_validation_results(self, rule_id, limit) -> List[Dict[(str, Any)]]:
        """Get validation results, optionally filtered by rule ID.

Args: rule_id: Optional rule ID to filter by limit: Maximum number of results to return

Returns: List[Dict[str, Any]]: List of validation results

Raises: DatabaseError: If getting results fails"""
```
```python
    async def initialize(self) -> None:
        """Initialize the validation engine.

This method sets up the validation engine and creates necessary tables. It gracefully handles cases where async sessions aren't supported."""
```
```python
    async def shutdown(self) -> None:
        """Shut down the validation engine."""
```
```python
    async def update_rule(self, rule_id, **updates) -> Dict[(str, Any)]:
        """Update a validation rule.

Args: rule_id: The rule ID **updates: Fields to update

Returns: Dict[str, Any]: The updated rule

Raises: DatabaseError: If rule update fails ValueError: If rule parameters are invalid"""
```
```python
    async def validate_all_rules(self, connection_id, table_name, data) -> List[Dict[(str, Any)]]:
        """Validate data against all rules for a table.

Args: connection_id: The connection ID table_name: The table name data: The data to validate

Returns: List[Dict[str, Any]]: Validation results

Raises: ValidationError: If validation fails"""
```
```python
    async def validate_data(self, rule, data) -> Dict[(str, Any)]:
        """Validate data against a rule.

Args: rule: The validation rule data: The data to validate

Returns: Dict[str, Any]: Validation result

Raises: ValidationError: If validation fails"""
```

```python
class ValidationRuleType(str, Enum):
    """Types of validation rules."""
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

#### Package: database_connector_plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin`

**__init__.py:**
*Database Connector Plugin Package.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/__init__.py`

**Imports:**
```python
from __future__ import annotations
```

**Global Variables:**
```python
__version__ = '2.0.0'
__author__ = 'Qorzen Team'
__description__ = 'Advanced database connectivity and management plugin'
```

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code`

**__init__.py:**
*Database Connector Plugin Core Code.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/__init__.py`

**Imports:**
```python
from __future__ import annotations
from plugin import DatabaseConnectorPlugin
```

**Global Variables:**
```python
__all__ = __all__ = ["DatabaseConnectorPlugin"]
```

###### Module: models
*Data models for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/models.py`

**Imports:**
```python
from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
```

**Classes:**
```python
class ColumnInfo(BaseModel):
    """Model for database column information."""
```

```python
class ConnectionType(str, Enum):
    """Supported database connection types."""
```
*Class attributes:*
```python
POSTGRESQL = 'postgresql'
MYSQL = 'mysql'
SQLITE = 'sqlite'
ORACLE = 'oracle'
MSSQL = 'mssql'
AS400 = 'as400'
ODBC = 'odbc'
```

```python
class DatabaseConnection(BaseModel):
    """Model for database connection configuration."""
```
*Methods:*
```python
@validator('name')
    def validate_name(cls, v) -> str:
        """Validate connection name is not empty."""
```
```python
@validator('port')
    def validate_port(cls, v) -> Optional[int]:
        """Validate port is in valid range."""
```

```python
class ExportFormat(str, Enum):
    """Supported export formats for query results."""
```
*Class attributes:*
```python
CSV = 'csv'
JSON = 'json'
XML = 'xml'
EXCEL = 'excel'
TSV = 'tsv'
HTML = 'html'
```

```python
class ExportSettings(BaseModel):
    """Model for export configuration settings."""
```

```python
class FieldMapping(BaseModel):
    """Model for database field mappings."""
```
*Methods:*
```python
@validator('table_name')
    def validate_table_name(cls, v) -> str:
        """Validate table name is not empty."""
```

```python
class HistorySchedule(BaseModel):
    """Model for history collection schedules."""
```
*Methods:*
```python
@validator('frequency')
    def validate_frequency(cls, v) -> str:
        """Validate frequency format."""
```
```python
@validator('name')
    def validate_name(cls, v) -> str:
        """Validate schedule name is not empty."""
```
```python
@validator('retention_days')
    def validate_retention_days(cls, v) -> int:
        """Validate retention days is positive."""
```

```python
class PluginSettings(BaseModel):
    """Model for plugin configuration settings."""
```
*Methods:*
```python
@validator('max_recent_connections')
    def validate_max_recent_connections(cls, v) -> int:
        """Validate max recent connections is positive."""
```
```python
@validator('query_limit')
    def validate_query_limit(cls, v) -> int:
        """Validate query limit is positive."""
```

```python
class QueryResult(BaseModel):
    """Model for query execution results."""
```

```python
class SavedQuery(BaseModel):
    """Model for saved database queries."""
```
*Methods:*
```python
@validator('name')
    def validate_name(cls, v) -> str:
        """Validate query name is not empty."""
```
```python
@validator('query_text')
    def validate_query_text(cls, v) -> str:
        """Validate query text is not empty."""
```

```python
class TableInfo(BaseModel):
    """Model for database table information."""
```

```python
class ValidationRule(BaseModel):
    """Model for data validation rules."""
```
*Methods:*
```python
@validator('field_name')
    def validate_field_name(cls, v) -> str:
        """Validate field name is not empty."""
```
```python
@validator('name')
    def validate_name(cls, v) -> str:
        """Validate rule name is not empty."""
```

```python
class ValidationRuleType(str, Enum):
    """Types of validation rules."""
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
*Main plugin module for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qorzen.core.database_manager import DatabaseConnectionConfig, ConnectionType
from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.lifecycle import PluginLifecycleState, get_plugin_state, set_plugin_state, signal_ui_ready
from qorzen.utils.exceptions import PluginError
from models import DatabaseConnection, SavedQuery, PluginSettings, QueryResult, FieldMapping, ValidationRule, HistorySchedule, ExportSettings, ExportFormat
from ui.main_widget import DatabasePluginWidget
from services.export_service import ExportService
from services.query_service import QueryService
```

**Classes:**
```python
class DatabaseConnectorPlugin(BasePlugin):
    """Advanced Database Connector Plugin.

Provides comprehensive database management capabilities including: - Connection management with multiple database types - Advanced query editor with syntax highlighting - Results visualization and export - Field mapping management - Data validation rules - Historical data tracking"""
```
*Class attributes:*
```python
name = 'database_connector_plugin'
version = '2.0.0'
description = 'Advanced database connectivity and management plugin'
author = 'Qorzen Team'
display_name = 'Database Connector'
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the plugin."""
```
```python
    async def create_connection(self, connection) -> str:
        """Create a new database connection.

Args: connection: The connection configuration

Returns: The connection ID"""
```
```python
    async def create_field_mapping(self, connection_id, table_name, mappings, description) -> Dict[(str, Any)]:
        """Create a field mapping."""
```
```python
    async def create_history_schedule(self, connection_id, query_id, frequency, name, description, retention_days) -> Dict[(str, Any)]:
        """Create a history schedule."""
```
```python
    async def create_validation_rule(self, rule_type, connection_id, table_name, field_name, parameters, error_message, name, description) -> Dict[(str, Any)]:
        """Create a validation rule."""
```
```python
    async def delete_connection(self, connection_id) -> bool:
        """Delete a database connection.

Args: connection_id: The connection ID to delete

Returns: True if deleted successfully"""
```
```python
    async def delete_field_mapping(self, mapping_id) -> bool:
        """Delete a field mapping."""
```
```python
    async def delete_query(self, query_id) -> bool:
        """Delete a saved query.

Args: query_id: The query ID to delete

Returns: True if deleted successfully"""
```
```python
    async def execute_query(self, connection_id, query, parameters, limit, apply_mapping) -> QueryResult:
        """Execute a database query.

Args: connection_id: The connection ID to use query: The SQL query to execute parameters: Query parameters limit: Row limit for results apply_mapping: Whether to apply field mappings

Returns: Query execution results"""
```
```python
    async def export_results(self, results, format, file_path, settings) -> str:
        """Export query results to a file.

Args: results: The query results to export format: The export format file_path: The output file path settings: Export settings

Returns: The exported file path"""
```
```python
    async def get_connections(self) -> List[DatabaseConnection]:
        """Get all saved database connections."""
```
```python
    async def get_field_mappings(self, connection_id) -> List[Dict[(str, Any)]]:
        """Get field mappings."""
```
```python
    async def get_history_schedules(self) -> List[Dict[(str, Any)]]:
        """Get history schedules."""
```
```python
    async def get_saved_queries(self, connection_id) -> List[SavedQuery]:
        """Get saved queries, optionally filtered by connection."""
```
```python
    async def get_settings(self) -> PluginSettings:
        """Get plugin settings."""
```
```python
    async def get_table_columns(self, connection_id, table_name, schema) -> List[Dict[(str, Any)]]:
        """Get columns from a database table."""
```
```python
    async def get_tables(self, connection_id, schema) -> List[Dict[(str, Any)]]:
        """Get tables from a database connection."""
```
```python
    async def get_validation_rules(self, connection_id, table_name) -> List[Dict[(str, Any)]]:
        """Get validation rules."""
```
```python
    async def initialize(self, application_core, **kwargs) -> None:
        """Initialize the plugin with application core services.

Args: application_core: The application core instance **kwargs: Additional initialization parameters"""
```
```python
    async def on_ui_ready(self, ui_integration) -> None:
        """Setup UI components when the UI is ready.  Args: ui_integration: The UI integration interface"""
```
```python
    async def save_query(self, query) -> str:
        """Save a database query.  Args: query: The query to save  Returns: The query ID"""
```
```python
    async def setup_ui(self, ui_integration) -> None:
        """Set up UI components (legacy method).  Args: ui_integration: The UI integration instance"""
```
```python
    async def shutdown(self) -> None:
        """Shutdown the plugin."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get plugin status."""
```
```python
    async def test_connection(self, connection_id) -> Tuple[(bool, Optional[str])]:
        """Test a database connection.

Args: connection_id: The connection ID to test

Returns: Tuple of (success, error_message)"""
```
```python
    async def update_connection(self, connection) -> None:
        """Update an existing database connection.  Args: connection: The updated connection configuration"""
```
```python
    async def update_settings(self, settings) -> None:
        """Update plugin settings."""
```
```python
    async def validate_data(self, connection_id, table_name, data) -> List[Dict[(str, Any)]]:
        """Validate data against rules."""
```

###### Package: services
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/services`

**__init__.py:**
*Database Connector Plugin Services.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/services/__init__.py`

**Imports:**
```python
from __future__ import annotations
from export_service import ExportService
from query_service import QueryService
```

**Global Variables:**
```python
__all__ = __all__ = ["ExportService", "QueryService"]
```

####### Module: export_service
*Export service for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/services/export_service.py`

**Imports:**
```python
from __future__ import annotations
import csv
import io
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional
from models import QueryResult, ExportSettings, ExportFormat
```

**Classes:**
```python
class ExportService(object):
    """Service for exporting query results to various formats.

Supports exporting to CSV, JSON, XML, Excel, TSV, and HTML formats with configurable settings for formatting and encoding."""
```
*Methods:*
```python
    def __init__(self, file_manager, logger) -> None:
        """Initialize the export service.

Args: file_manager: The file manager instance logger: Logger instance"""
```
```python
    async def export_results(self, results, format, file_path, settings) -> str:
        """Export query results to the specified format.

Args: results: The query results to export format: The export format file_path: The output file path settings: Export settings

Returns: The actual file path written

Raises: Exception: If export fails"""
```
```python
    def get_file_extension(self, format) -> str:
        """Get the file extension for a given format.

Args: format: The export format

Returns: File extension with dot"""
```
```python
    def get_mime_type(self, format) -> str:
        """Get the MIME type for a given format.  Args: format: The export format  Returns: MIME type string"""
```
```python
    def get_supported_formats(self) -> List[ExportFormat]:
        """Get list of supported export formats.  Returns: List of supported formats"""
```

####### Module: query_service
*Query service for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/services/query_service.py`

**Imports:**
```python
from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Optional
from qorzen.utils.exceptions import DatabaseError
```

**Classes:**
```python
class QueryService(object):
    """Service for executing and managing database queries.

Provides functionality for query execution, SQL formatting, query validation, and execution state management."""
```
*Methods:*
```python
    def __init__(self, database_manager, logger) -> None:
        """Initialize the query service.

Args: database_manager: The database manager instance logger: Logger instance"""
```
```python
    def estimate_result_size(self, query) -> str:
        """Provide a rough estimate of result size based on query structure.

Args: query: The SQL query

Returns: Size estimate description"""
```
```python
    async def execute_query(self, connection_name, query, parameters, limit, apply_mapping) -> Dict[(str, Any)]:
        """Execute a database query.

Args: connection_name: The connection name to use query: The SQL query to execute parameters: Query parameters limit: Row limit for results apply_mapping: Whether to apply field mappings

Returns: Query execution results

Raises: DatabaseError: If query execution fails"""
```
```python
    def extract_table_names(self, query) -> List[str]:
        """Extract table names from a SQL query.

Args: query: The SQL query

Returns: List of table names found in the query"""
```
```python
    def format_sql(self, query) -> str:
        """Format a SQL query for better readability.

Args: query: The SQL query to format

Returns: Formatted SQL query"""
```
```python
    def get_query_type(self, query) -> str:
        """Determine the type of SQL query.

Args: query: The SQL query

Returns: Query type (SELECT, INSERT, UPDATE, DELETE, etc.)"""
```
```python
    async def get_table_columns(self, connection_name, table_name, schema) -> List[Dict[(str, Any)]]:
        """Get columns from a database table.

Args: connection_name: The connection name table_name: The table name schema: Optional schema name

Returns: List of column information"""
```
```python
    async def get_tables(self, connection_name, schema) -> List[Dict[(str, Any)]]:
        """Get tables from a database connection.

Args: connection_name: The connection name schema: Optional schema name

Returns: List of table information"""
```
```python
    def is_read_only_query(self, query) -> bool:
        """Check if a query is read-only (doesn't modify data).

Args: query: The SQL query

Returns: True if query is read-only"""
```
```python
    def suggest_query_improvements(self, query) -> List[str]:
        """Suggest improvements for a SQL query.

Args: query: The SQL query

Returns: List of improvement suggestions"""
```
```python
    async def test_connection(self, connection_name) -> bool:
        """Test if a database connection is working.

Args: connection_name: The connection name to test

Returns: True if connection is working"""
```

###### Package: ui
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui`

**__init__.py:**
*Database Connector Plugin User Interface Components.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/__init__.py`

**Imports:**
```python
from __future__ import annotations
from main_widget import DatabasePluginWidget
from main_tab import MainTab
from results_tab import ResultsTab
from field_mapping_tab import FieldMappingTab
from validation_tab import ValidationTab
from history_tab import HistoryTab
from connection_dialog import ConnectionDialog
from query_dialog import QueryDialog
```

**Global Variables:**
```python
__all__ = __all__ = [
    "DatabasePluginWidget",
    "MainTab",
    "ResultsTab",
    "FieldMappingTab",
    "ValidationTab",
    "HistoryTab",
    "ConnectionDialog",
    "QueryDialog"
]
```

####### Module: connection_dialog
*Connection dialog for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/connection_dialog.py`

**Imports:**
```python
from __future__ import annotations
from datetime import datetime
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit, QSpinBox, QComboBox, QCheckBox, QTextEdit, QPushButton, QDialogButtonBox, QTabWidget, QWidget, QLabel, QFileDialog, QMessageBox
from models import DatabaseConnection, ConnectionType
```

**Classes:**
```python
class ConnectionDialog(QDialog):
    """Dialog for creating and editing database connections.

Provides a comprehensive interface for configuring database connections with support for various database types and advanced settings."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the connection dialog.  Args: parent: Parent widget"""
```
```python
    def accept(self) -> None:
        """Accept the dialog after validation."""
```
```python
    def get_connection(self) -> DatabaseConnection:
        """Get the connection from the dialog.

Returns: The configured connection

Raises: ValueError: If validation fails"""
```
```python
    def set_connection(self, connection) -> None:
        """Set the connection to edit.  Args: connection: The connection to edit"""
```

####### Module: field_mapping_tab
*Field mapping tab for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/field_mapping_tab.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QFrame, QMenu, QInputDialog
from models import FieldMapping
```

**Classes:**
```python
class FieldMappingDialog(QDialog):
    """Dialog for creating and editing field mappings."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the field mapping dialog."""
```
```python
    def get_mapping_data(self) -> Tuple[(str, str, str, Dict[(str, str)])]:
        """Get the mapping data from the dialog."""
```
```python
    async def set_connections(self, connections) -> None:
        """Set available connections."""
```

```python
class FieldMappingTab(QWidget):
    """Field mapping tab for managing database field mappings.

Provides functionality for: - Creating field mappings between database columns and standard names - Viewing and editing existing mappings - Applying mappings to query results - Bulk mapping operations"""
```
*Class attributes:*
```python
operation_started =     operation_started = Signal(str)  # message
operation_finished =     operation_finished = Signal()
status_changed =     status_changed = Signal(str)  # message
```
*Methods:*
```python
    def __init__(self, plugin, logger, concurrency_manager, parent) -> None:
        """Initialize the field mapping tab.

Args: plugin: The plugin instance logger: Logger instance concurrency_manager: Concurrency manager parent: Parent widget"""
```
```python
    def cleanup(self) -> None:
        """Cleanup resources."""
```
```python
    async def refresh(self) -> None:
        """Refresh all data in the tab."""
```

####### Module: history_tab
*History tab for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/history_tab.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QFrame, QMenu, QSpinBox, QTabWidget, QProgressBar, QCheckBox, QCalendarWidget, QDateEdit
from models import HistorySchedule
```

**Classes:**
```python
class HistoryScheduleDialog(QDialog):
    """Dialog for creating and editing history schedules."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the history schedule dialog."""
```
```python
    def get_schedule(self) -> HistorySchedule:
        """Get the schedule from the dialog."""
```
```python
    def set_connections(self, connections) -> None:
        """Set available connections."""
```
```python
    def set_queries(self, queries) -> None:
        """Set available queries."""
```
```python
    def set_schedule(self, schedule) -> None:
        """Set the schedule to edit."""
```

```python
class HistoryTab(QWidget):
    """History tab for managing historical data tracking.

Provides functionality for: - Creating and managing history collection schedules - Viewing historical data snapshots - Configuring data retention policies - Analyzing historical trends"""
```
*Class attributes:*
```python
operation_started =     operation_started = Signal(str)  # message
operation_finished =     operation_finished = Signal()
status_changed =     status_changed = Signal(str)  # message
```
*Methods:*
```python
    def __init__(self, plugin, logger, concurrency_manager, parent) -> None:
        """Initialize the history tab.

Args: plugin: The plugin instance logger: Logger instance concurrency_manager: Concurrency manager parent: Parent widget"""
```
```python
    def cleanup(self) -> None:
        """Cleanup resources."""
```
```python
    async def refresh(self) -> None:
        """Refresh all data in the tab."""
```

####### Module: main_tab
*Main tab for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/main_tab.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QPushButton, QComboBox, QLabel, QTextEdit, QPlainTextEdit, QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QMessageBox, QDialog, QFormLayout, QLineEdit, QSpinBox, QCheckBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QFrame, QScrollArea, QGridLayout
from models import DatabaseConnection, SavedQuery, ConnectionType, QueryResult
from connection_dialog import ConnectionDialog
from query_dialog import QueryDialog
```

**Classes:**
```python
class MainTab(QWidget):
    """Main tab containing connection management and query editor.

Provides functionality for: - Managing database connections - Query editor with syntax highlighting - Query execution and management - Database schema browsing"""
```
*Class attributes:*
```python
query_executed =     query_executed = Signal(object)  # QueryResult
operation_started =     operation_started = Signal(str)  # message
operation_finished =     operation_finished = Signal()
status_changed =     status_changed = Signal(str)  # message
```
*Methods:*
```python
    def __init__(self, plugin, logger, concurrency_manager, event_bus_manager, parent) -> None:
        """Initialize the main tab.

Args: plugin: The plugin instance logger: Logger instance concurrency_manager: Concurrency manager event_bus_manager: Event bus manager parent: Parent widget"""
```
```python
    def cleanup(self) -> None:
        """Cleanup resources."""
```
```python
    def get_current_connection_id(self) -> Optional[str]:
        """Get the current connection ID."""
```
```python
    def get_query_text(self) -> str:
        """Get the query editor text."""
```
```python
    async def refresh(self) -> None:
        """Refresh all data in the tab."""
```
```python
    def set_query_text(self, text) -> None:
        """Set the query editor text."""
```

```python
class SQLHighlighter(QSyntaxHighlighter):
    """SQL syntax highlighter for the query editor."""
```
*Methods:*
```python
    def __init__(self, document) -> None:
        """Initialize the highlighter."""
```
```python
    def highlightBlock(self, text) -> None:
        """Highlight a block of text."""
```

####### Module: main_widget
*Main widget for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/main_widget.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QMessageBox, QProgressBar, QLabel, QHBoxLayout, QFrame
from main_tab import MainTab
from results_tab import ResultsTab
from field_mapping_tab import FieldMappingTab
from validation_tab import ValidationTab
from history_tab import HistoryTab
```

**Classes:**
```python
class DatabasePluginWidget(QWidget):
    """Main widget for the Database Connector Plugin.

Contains tabbed interface with: - Main tab: Connection management and query editor - Results tab: Query results display and export - Field Mapping tab: Field mapping management - Validation tab: Data validation rules - History tab: Historical data tracking"""
```
*Methods:*
```python
    def __init__(self, plugin, logger, concurrency_manager, event_bus_manager, parent) -> None:
        """Initialize the main widget.

Args: plugin: The plugin instance logger: Logger instance concurrency_manager: Concurrency manager event_bus_manager: Event bus manager parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
```
```python
    def get_current_tab_index(self) -> int:
        """Get the current tab index.  Returns: Current tab index"""
```
```python
    def get_field_mapping_tab(self) -> Optional[FieldMappingTab]:
        """Get the field mapping tab instance."""
```
```python
    def get_history_tab(self) -> Optional[HistoryTab]:
        """Get the history tab instance."""
```
```python
    def get_main_tab(self) -> Optional[MainTab]:
        """Get the main tab instance."""
```
```python
    def get_results_tab(self) -> Optional[ResultsTab]:
        """Get the results tab instance."""
```
```python
    def get_validation_tab(self) -> Optional[ValidationTab]:
        """Get the validation tab instance."""
```
```python
    async def refresh_all_tabs(self) -> None:
        """Refresh data in all tabs."""
```
```python
    def switch_to_tab(self, index) -> None:
        """Switch to a specific tab.  Args: index: Tab index to switch to"""
```

####### Module: query_dialog
*Query dialog for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/query_dialog.py`

**Imports:**
```python
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit, QTextEdit, QPlainTextEdit, QPushButton, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QMessageBox, QSplitter, QWidget
from models import SavedQuery
```

**Classes:**
```python
class QueryDialog(QDialog):
    """Dialog for creating and editing saved queries.

Provides interface for: - Query metadata (name, description) - SQL query text with basic formatting - Tag management - Query validation"""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the query dialog.  Args: parent: Parent widget"""
```
```python
    def accept(self) -> None:
        """Accept the dialog after validation."""
```
```python
    def get_query(self) -> SavedQuery:
        """Get the query from the dialog.

Returns: The configured query

Raises: ValueError: If validation fails"""
```
```python
    def set_connection_id(self, connection_id) -> None:
        """Set the connection ID.  Args: connection_id: The connection ID"""
```
```python
    def set_query(self, query) -> None:
        """Set the query to edit.  Args: query: The query to edit"""
```
```python
    def set_query_text(self, query_text) -> None:
        """Set the query text.  Args: query_text: The SQL query text"""
```

####### Module: results_tab
*Results tab for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/results_tab.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QSpinBox, QCheckBox, QTextEdit, QSplitter, QFrame, QMessageBox, QFileDialog, QProgressBar, QMenu
from models import QueryResult, ExportFormat, ExportSettings
```

**Classes:**
```python
class ResultsTab(QWidget):
    """Results tab for displaying query results and export functionality.

Provides: - Query results display in table format - Export to multiple formats - Result statistics and metadata - Row count and execution time display"""
```
*Class attributes:*
```python
operation_started =     operation_started = Signal(str)  # message
operation_finished =     operation_finished = Signal()
status_changed =     status_changed = Signal(str)  # message
```
*Methods:*
```python
    def __init__(self, plugin, logger, concurrency_manager, parent) -> None:
        """Initialize the results tab.

Args: plugin: The plugin instance logger: Logger instance concurrency_manager: Concurrency manager parent: Parent widget"""
```
```python
    def cleanup(self) -> None:
        """Cleanup resources."""
```
```python
    def clear_results(self) -> None:
        """Clear the current results."""
```
```python
    def get_current_result(self) -> Optional[QueryResult]:
        """Get the current query result."""
```
```python
    async def refresh(self) -> None:
        """Refresh the current results display."""
```
```python
    def show_results(self, result) -> None:
        """Display query results.  Args: result: The query result to display"""
```

####### Module: validation_tab
*Validation tab for the Database Connector Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/database_connector_plugin/code/ui/validation_tab.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QComboBox, QLineEdit, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QFrame, QMenu, QSpinBox, QDoubleSpinBox, QCheckBox, QTabWidget, QProgressBar, QScrollArea
from models import ValidationRule, ValidationRuleType
```

**Classes:**
```python
class ValidationRuleDialog(QDialog):
    """Dialog for creating and editing validation rules."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the validation rule dialog."""
```
```python
    def get_rule(self) -> ValidationRule:
        """Get the rule from the dialog."""
```
```python
    def set_connections(self, connections) -> None:
        """Set available connections."""
```
```python
    def set_rule(self, rule) -> None:
        """Set the rule to edit."""
```

```python
class ValidationTab(QWidget):
    """Validation tab for managing data validation rules.

Provides functionality for: - Creating and managing validation rules - Running validation checks on database data - Viewing validation results - Managing rule templates"""
```
*Class attributes:*
```python
operation_started =     operation_started = Signal(str)  # message
operation_finished =     operation_finished = Signal()
status_changed =     status_changed = Signal(str)  # message
```
*Methods:*
```python
    def __init__(self, plugin, logger, concurrency_manager, parent) -> None:
        """Initialize the validation tab.

Args: plugin: The plugin instance logger: Logger instance concurrency_manager: Concurrency manager parent: Parent widget"""
```
```python
    def cleanup(self) -> None:
        """Cleanup resources."""
```
```python
    async def refresh(self) -> None:
        """Refresh all data in the tab."""
```

#### Package: media_processor_plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/__init__.py`

**Imports:**
```python
from __future__ import annotations
from code.plugin import MediaProcessorPlugin
```

**Global Variables:**
```python
__version__ = '1.0.0'
__all__ = __all__ = ["MediaProcessorPlugin"]
```

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code`

**__init__.py:**
*Media Processor Plugin for Qorzen.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/__init__.py`

**Imports:**
```python
from plugin import MediaProcessorPlugin
```

**Global Variables:**
```python
__version__ = '1.0.0'
```

###### Module: plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
from processors.optimized_processor import OptimizedProcessor
from ui.ai_manager_dialog import AIModelManagerDialog
from utils.ai_background_remover import AIBackgroundRemover
from utils.font_manager import FontManager
import asyncio
import logging
import os
import pathlib
from typing import Any, Dict, List, Optional, Set, Union, cast
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QMessageBox, QWidget
from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.config_manager import ConfigManager
from qorzen.plugin_system.interface import BasePlugin
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState, signal_ui_ready
from qorzen.ui.ui_integration import UIIntegration
from models.processing_config import ProcessingConfig, BackgroundRemovalConfig, OutputFormat
from ui.main_widget import MediaProcessorWidget
from ui.batch_dialog import BatchProcessingDialog
from ui.config_editor import ConfigEditorDialog
from processors.media_processor import MediaProcessor
from processors.batch_processor import BatchProcessor
from utils.exceptions import MediaProcessingError
```

**Classes:**
```python
class MediaProcessorPlugin(BasePlugin):
    """Plugin for advanced media processing with background removal and batch operations.

This plugin provides: - Image processing with background removal capabilities - Multiple configurable output formats - Batch processing with progress tracking - Save/load processing configurations"""
```
*Class attributes:*
```python
name = 'media_processor'
version = '1.0.0'
description = 'Advanced media processing with background removal, batch processing, and multiple output formats'
author = 'Qorzen Developer'
display_name = 'Media Processor'
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the media processor plugin."""
```
```python
    def get_icon(self) -> Optional[str]:
        """Get the plugin icon path."""
```
```python
    def get_main_widget(self) -> Optional[QWidget]:
        """Get the main widget instance."""
```
```python
    async def initialize(self, application_core, **kwargs) -> None:
        """Initialize the plugin.

Args: application_core: The main application core **kwargs: Additional keyword arguments"""
```
```python
    async def on_ui_ready(self, ui_integration) -> None:
        """Set up UI components when the UI system is ready.  Args: ui_integration: The UI integration service"""
```
```python
    async def setup_ui(self, ui_integration) -> None:
        """Set up UI (compat method).  Args: ui_integration: The UI integration service"""
```
```python
    async def shutdown(self) -> None:
        """Shut down the plugin and clean up resources."""
```

###### Package: models
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/models`

**__init__.py:**
*Data models for the Media Processor Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/models/__init__.py`

**Imports:**
```python
from processing_config import ProcessingConfig, BackgroundRemovalConfig, BackgroundRemovalMethod, OutputFormat, ImageFormat, ResizeMode, WatermarkType, WatermarkPosition
```

####### Module: isnet_model
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/models/isnet_model.py`

**Imports:**
```python
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F
```

**Functions:**
```python
def conv_bn_relu(in_ch, out_ch, kernel_size, stride, padding, dilation) -> nn.Sequential:
    """Convenience function for conv-bn-relu blocks.

Args: in_ch: Input channels out_ch: Output channels kernel_size: Kernel size stride: Stride padding: Padding dilation: Dilation

Returns: nn.Sequential: Sequential module with the given components"""
```

**Classes:**
```python
class ISNetDIS(nn.Module):
    """ISNet for Dichotomous Image Segmentation."""
```
*Methods:*
```python
    def __init__(self, in_ch, out_ch, depth) -> None:
        """Initialize the ISNetDIS model.

Args: in_ch: Input channels out_ch: Output channels depth: Base channel depth"""
```
```python
    def forward(self, x) -> tuple:
        """Forward pass.  Args: x: Input tensor  Returns: Tuple of output tensor and side outputs"""
```

```python
class ISNetDecoder(nn.Module):
    """ISNet decoder block."""
```
*Methods:*
```python
    def __init__(self, depth) -> None:
        """Initialize the ISNet decoder.  Args: depth: Base channel depth"""
```
```python
    def forward(self, features) -> torch.Tensor:
        """Forward pass.  Args: features: Tuple of feature maps from the encoder  Returns: Output tensor"""
```

```python
class ISNetEncoder(nn.Module):
    """ISNet encoder block."""
```
*Methods:*
```python
    def __init__(self, in_ch, depth) -> None:
        """Initialize the ISNet encoder.  Args: in_ch: Input channels depth: Base channel depth"""
```
```python
    def forward(self, x) -> tuple:
        """Forward pass.  Args: x: Input tensor  Returns: Tuple of feature maps at different scales"""
```

```python
class ResidualConv(nn.Module):
    """Residual convolution block."""
```
*Methods:*
```python
    def __init__(self, in_ch, out_ch) -> None:
        """Initialize the ResidualConv block.  Args: in_ch: Input channels out_ch: Output channels"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

####### Module: modnet_model
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/models/modnet_model.py`

**Imports:**
```python
from __future__ import annotations
from typing import Union
import torch
import torch.nn as nn
import torch.nn.functional as F
```

**Classes:**
```python
class ConvBlock(nn.Module):
    """Basic convolutional block."""
```
*Methods:*
```python
    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, dilation, groups, bias, norm, activation) -> None:
        """Initialize the ConvBlock.

Args: in_channels: Input channels out_channels: Output channels kernel_size: Kernel size stride: Stride padding: Padding dilation: Dilation groups: Groups bias: Whether to include bias norm: Normalization type (bn, in, ibn) activation: Activation type (relu, leaky_relu, tanh, sigmoid, none)"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class IBNorm(nn.Module):
    """Instance-Batch Normalization."""
```
*Methods:*
```python
    def __init__(self, dim) -> None:
        """Initialize IBNorm.  Args: dim: Number of features"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class MODNet(nn.Module):
    """MODNet for portrait matting."""
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the MODNet model."""
```
```python
    def forward(self, x, inference) -> Union[(torch.Tensor, tuple)]:
        """Forward pass.

Args: x: Input tensor inference: Whether in inference mode

Returns: Predicted alpha matte or tuple of (matte, fgr, pha) in training mode"""
```

```python
class MODNetBackbone(nn.Module):
    """MODNet backbone network (MobileNetV2-based)."""
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the backbone network."""
```
```python
    def forward(self, x) -> tuple:
        """Forward pass.  Returns: Tuple of feature maps at different scales."""
```

```python
class MODNetDecoder(nn.Module):
    """MODNet decoder network for matting."""
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the decoder network."""
```
```python
    def forward(self, features) -> torch.Tensor:
        """Forward pass.  Args: features: Tuple of feature maps from the encoder  Returns: Alpha matte tensor"""
```

```python
class ResBlock(nn.Module):
    """Residual block with bottleneck architecture."""
```
*Methods:*
```python
    def __init__(self, in_channels, out_channels, stride, padding, dilation, norm) -> None:
        """Initialize the ResBlock.

Args: in_channels: Input channels out_channels: Output channels stride: Stride padding: Padding dilation: Dilation norm: Normalization type"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

####### Module: processing_config
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/models/processing_config.py`

**Imports:**
```python
from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field, model_validator, field_validator
```

**Classes:**
```python
class BackgroundRemovalConfig(BaseModel):
    """Configuration for background removal operations."""
```
*Methods:*
```python
@property
    def as_dict(self) -> Dict[(str, Any)]:
        """Convert the model to a dictionary."""
```
```python
@field_validator('chroma_color')
    def validate_chroma_color(cls, v) -> Optional[str]:
        """Validate chroma key color format."""
```

```python
class BackgroundRemovalMethod(str, Enum):
    """Methods for removing backgrounds from images."""
```
*Class attributes:*
```python
CHROMA_KEY = 'chroma_key'
ALPHA_MATTING = 'alpha_matting'
ML_MODEL = 'ml_model'
SMART_SELECTION = 'smart_selection'
MANUAL_MASK = 'manual_mask'
NONE = 'none'
```

```python
class ImageFormat(str, Enum):
    """Supported output image formats."""
```
*Class attributes:*
```python
JPEG = 'jpeg'
PNG = 'png'
TIFF = 'tiff'
BMP = 'bmp'
WEBP = 'webp'
PSD = 'psd'
PDF = 'pdf'
```

```python
class OutputFormat(BaseModel):
    """Configuration for an output format."""
```
*Methods:*
```python
@property
    def as_dict(self) -> Dict[(str, Any)]:
        """Convert the model to a dictionary."""
```
```python
@field_validator('background_color', 'padding_color')
    def validate_colors(cls, v) -> Optional[str]:
        """Validate color format."""
```
```python
@model_validator(mode='before')
    def validate_resize_mode_requirements(cls, values) -> Dict[(str, Any)]:
        """Validate that the required parameters are present for the selected resize mode."""
```

```python
class ProcessingConfig(BaseModel):
    """Complete configuration for media processing."""
```
*Methods:*
```python
@property
    def as_dict(self) -> Dict[(str, Any)]:
        """Convert the model to a dictionary."""
```
```python
@model_validator(mode='before')
    def set_updated_time(cls, values) -> Dict[(str, Any)]:
        """Set the updated_at time to current time."""
```
```python
@field_validator('output_formats')
    def validate_output_formats(cls, v) -> List[OutputFormat]:
        """Validate that there is at least one output format."""
```

```python
class ResizeMode(str, Enum):
    """Methods for resizing images."""
```
*Class attributes:*
```python
NONE = 'none'
WIDTH = 'width'
HEIGHT = 'height'
EXACT = 'exact'
MAX_DIMENSION = 'max_dimension'
MIN_DIMENSION = 'min_dimension'
PERCENTAGE = 'percentage'
```

```python
class WatermarkConfig(BaseModel):
    """Configuration for watermark application."""
```
*Methods:*
```python
@model_validator(mode='before')
    def check_watermark_type_requirements(cls, values) -> Dict[(str, Any)]:
        """Validate that required fields are present for the selected watermark type."""
```

```python
class WatermarkPosition(str, Enum):
    """Positions for watermark placement."""
```
*Class attributes:*
```python
TOP_LEFT = 'top_left'
TOP_CENTER = 'top_center'
TOP_RIGHT = 'top_right'
MIDDLE_LEFT = 'middle_left'
MIDDLE_CENTER = 'middle_center'
MIDDLE_RIGHT = 'middle_right'
BOTTOM_LEFT = 'bottom_left'
BOTTOM_CENTER = 'bottom_center'
BOTTOM_RIGHT = 'bottom_right'
TILED = 'tiled'
CUSTOM = 'custom'
```

```python
class WatermarkType(str, Enum):
    """Types of watermarks that can be applied."""
```
*Class attributes:*
```python
NONE = 'none'
TEXT = 'text'
IMAGE = 'image'
```

####### Module: u2net_model
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/models/u2net_model.py`

**Imports:**
```python
from __future__ import annotations
from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
```

**Classes:**
```python
class ConvBNReLU(nn.Module):
    """Conv-BN-ReLU block."""
```
*Methods:*
```python
    def __init__(self, in_ch, out_ch, kernel_size, dilation) -> None:
        """Initialize the ConvBNReLU block.

Args: in_ch: Input channels out_ch: Output channels kernel_size: Kernel size dilation: Dilation rate"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class REBNCONV(nn.Module):
    """ReLU-Conv-BN block."""
```
*Methods:*
```python
    def __init__(self, in_ch, out_ch, kernel_size, dilation, stride, padding) -> None:
        """Initialize the REBNCONV block.

Args: in_ch: Input channels out_ch: Output channels kernel_size: Kernel size dilation: Dilation rate stride: Stride padding: Padding (calculated if None)"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class RSU4(nn.Module):
    """RSU-4 module."""
```
*Methods:*
```python
    def __init__(self, in_ch, mid_ch, out_ch) -> None:
        """Initialize the RSU-4 module.

Args: in_ch: Input channels mid_ch: Middle channels out_ch: Output channels"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class RSU4F(nn.Module):
    """RSU-4F module."""
```
*Methods:*
```python
    def __init__(self, in_ch, mid_ch, out_ch) -> None:
        """Initialize the RSU-4F module.

Args: in_ch: Input channels mid_ch: Middle channels out_ch: Output channels"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class RSU5(nn.Module):
    """RSU-5 module."""
```
*Methods:*
```python
    def __init__(self, in_ch, mid_ch, out_ch) -> None:
        """Initialize the RSU-5 module.

Args: in_ch: Input channels mid_ch: Middle channels out_ch: Output channels"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class RSU6(nn.Module):
    """RSU-6 module."""
```
*Methods:*
```python
    def __init__(self, in_ch, mid_ch, out_ch) -> None:
        """Initialize the RSU-6 module.

Args: in_ch: Input channels mid_ch: Middle channels out_ch: Output channels"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class RSU7(nn.Module):
    """RSU-7 module."""
```
*Methods:*
```python
    def __init__(self, in_ch, mid_ch, out_ch) -> None:
        """Initialize the RSU-7 module.

Args: in_ch: Input channels mid_ch: Middle channels out_ch: Output channels"""
```
```python
    def forward(self, x) -> torch.Tensor:
        """Forward pass."""
```

```python
class U2NET(nn.Module):
    """U^2-Net architecture."""
```
*Methods:*
```python
    def __init__(self, in_ch, out_ch) -> None:
        """Initialize the U^2-Net model.

Args: in_ch: Input channels (3 for RGB images) out_ch: Output channels (1 for binary segmentation)"""
```
```python
    def forward(self, x) -> tuple:
        """Forward pass.  Returns: Tuple of output tensors at different scales."""
```

```python
class U2NETP(nn.Module):
    """U^2-Net-P architecture (the lightweight version of U^2-Net)."""
```
*Methods:*
```python
    def __init__(self, in_ch, out_ch) -> None:
        """Initialize the U^2-Net-P model.

Args: in_ch: Input channels (3 for RGB images) out_ch: Output channels (1 for binary segmentation)"""
```
```python
    def forward(self, x) -> tuple:
        """Forward pass.  Returns: Tuple of output tensors at different scales."""
```

###### Package: processors
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/processors`

**__init__.py:**
*Processing components for the Media Processor Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/processors/__init__.py`

**Imports:**
```python
from media_processor import MediaProcessor
from batch_processor import BatchProcessor
```

####### Module: batch_processor
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/processors/batch_processor.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import datetime
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from models.processing_config import ProcessingConfig
from utils.exceptions import MediaProcessingError, BatchProcessingError
from utils.path_resolver import generate_batch_folder_name
from media_processor import MediaProcessor
```

**Classes:**
```python
class BatchProcessor(object):
    """Handles batch processing of multiple media files.

This class: - Manages batch processing tasks - Tracks progress - Handles cancellation and pause/resume - Reports status via events"""
```
*Methods:*
```python
    def __init__(self, media_processor, task_manager, event_bus_manager, concurrency_manager, logger, processing_config) -> None:
        """Initialize the batch processor.

Args: media_processor: The media processor for individual files task_manager: The task manager service event_bus_manager: The event bus service concurrency_manager: The concurrency manager service logger: The logger instance processing_config: Configuration for processing"""
```
```python
    async def cancel_job(self, job_id) -> bool:
        """Cancel a running batch job.

Args: job_id: The job ID to cancel

Returns: True if job was cancelled, False otherwise"""
```
```python
    async def get_active_jobs(self) -> List[str]:
        """Get list of active job IDs.  Returns: List of active job IDs"""
```
```python
    async def get_job_status(self, job_id) -> Dict[(str, Any)]:
        """Get the status of a batch job.

Args: job_id: The job ID

Returns: Dictionary with job status information

Raises: BatchProcessingError: If job not found"""
```
```python
    async def start_batch_job(self, file_paths, config, output_dir, overwrite) -> str:
        """Start a batch processing job.

Args: file_paths: List of file paths to process config: Processing configuration to apply output_dir: Optional override for output directory overwrite: Whether to overwrite existing files

Returns: Job ID for the batch job

Raises: BatchProcessingError: If job cannot be started"""
```

####### Module: media_processor
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/processors/media_processor.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import io
from io import BytesIO
from PIL.Image import Resampling
from blib2to3.pygram import initialize
from utils.ai_background_remover import AIBackgroundRemover
from utils.config_manager import ConfigManager
from utils.font_manager import FontManager
import os
import pathlib
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, BinaryIO, cast
import PIL
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import piexif
from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager
from models.processing_config import ProcessingConfig, BackgroundRemovalConfig, BackgroundRemovalMethod, OutputFormat, ResizeMode, ImageFormat, WatermarkType, WatermarkPosition
from utils.exceptions import MediaProcessingError, ImageProcessingError
from utils.path_resolver import resolve_output_path, generate_filename
```

**Classes:**
```python
class MediaProcessor(object):
    """Core processor for media files.

This class handles: - Loading media files - Background removal with various techniques - Applying output formats - Saving processed media"""
```
*Methods:*
```python
    def __init__(self, file_manager, task_manager, logger, processing_config, background_removal_config) -> None:
        """Initialize the media processor.

Args: file_manager: The file manager service task_manager: The task manager service logger: The logger instance processing_config: Configuration for processing background_removal_config: Configuration for background removal"""
```
```python
    async def apply_format(self, image, format_config) -> Image.Image:
        """Apply output format configuration to an image.

Args: image: The input image format_config: Output format configuration

Returns: The formatted image

Raises: MediaProcessingError: If formatting fails"""
```
```python
    async def create_preview(self, image_path, config, size) -> bytes:
        """Create a preview image applying the specified configuration.

Args: image_path: Path to the input image config: Configuration to apply (full config, format, or bg removal) size: Maximum dimension for preview (0 for no resizing)

Returns: Preview image as bytes

Raises: MediaProcessingError: If preview generation fails"""
```
```python
    async def create_preview_from_image(self, image, format_config, size) -> bytes:
        """Create a preview directly from an image without loading from disk.

Args: image: Input PIL Image format_config: Format configuration size: Maximum dimension for preview scaling (0 for no scaling)

Returns: bytes: Preview image data"""
```
```python
    async def load_image(self, image_path) -> Image.Image:
        """Load an image with enhanced format support.

Args: image_path: Path to the image file

Returns: Image.Image: PIL Image object

Raises: MediaProcessingError: If image cannot be loaded"""
```
```python
    async def load_image_from_bytes(self, image_data) -> Image.Image:
        """Load an image from bytes.

Args: image_data: Image data as bytes

Returns: Image.Image: PIL Image object

Raises: MediaProcessingError: If image cannot be loaded"""
```
```python
    async def load_processing_config(self, config_path) -> ProcessingConfig:
        """Load a processing configuration from disk.

Args: config_path: Path to the configuration file

Returns: The loaded processing configuration

Raises: MediaProcessingError: If loading fails"""
```
```python
    async def process_image(self, image_path, config, output_dir, overwrite) -> List[str]:
        """Process a single image using the specified configuration.

Args: image_path: Path to the input image config: Processing configuration to apply output_dir: Optional override for output directory overwrite: Whether to overwrite existing files

Returns: List of paths to the generated output files

Raises: MediaProcessingError: If processing fails"""
```
```python
    async def remove_background(self, image, config) -> Image.Image:
        """Remove the background from an image using the specified configuration.

Args: image: The input image config: Background removal configuration

Returns: The image with background removed

Raises: MediaProcessingError: If background removal fails"""
```
```python
    async def save_image(self, image, output_path, format_config, overwrite) -> str:
        """Save image with enhanced EXIF metadata handling.

Args: image: The PIL Image to save output_path: Path where the image should be saved format_config: Configuration for the output format overwrite: Whether to overwrite existing files

Returns: The path where the image was saved"""
```
```python
    async def save_processing_config(self, config, config_path) -> str:
        """Save a processing configuration to disk.

Args: config: The processing configuration to save config_path: Path where to save the configuration

Returns: The path where the configuration was saved

Raises: MediaProcessingError: If saving fails"""
```

####### Module: optimized_processor
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/processors/optimized_processor.py`

**Imports:**
```python
from __future__ import annotations
import os
import tempfile
from typing import Dict, List, Optional, Set, Tuple, Any, Union, cast
from pathlib import Path
import asyncio
from PIL import Image
from models.processing_config import ProcessingConfig, BackgroundRemovalConfig, OutputFormat
from utils.exceptions import MediaProcessingError
```

**Classes:**
```python
class OptimizedProcessor(object):
    """Media processor that uses intermediate images to optimize processing.

This processor extends the standard MediaProcessor to support reusing intermediate processed images, avoiding redundant operations."""
```
*Methods:*
```python
    def __init__(self, media_processor, logger, use_intermediate) -> None:
        """Initialize the optimized processor.

Args: media_processor: The base MediaProcessor instance logger: Logger instance use_intermediate: Whether to use intermediate images"""
```
```python
    async def batch_process_images(self, image_paths, config, output_dir, overwrite, progress_callback) -> Dict[(str, List[str])]:
        """Process multiple images with optimization using intermediate images.

Args: image_paths: List of input image paths config: Processing configuration output_dir: Output directory (or None for default) overwrite: Whether to overwrite existing files progress_callback: Optional callback for progress updates

Returns: Dict[str, List[str]]: Dictionary mapping input paths to output paths"""
```
```python
    def enable_intermediate_images(self, enabled) -> None:
        """Enable or disable using intermediate images.  Args: enabled: Whether to enable intermediate images"""
```
```python
    async def process_image(self, image_path, config, output_dir, overwrite) -> List[str]:
        """Process an image with optimization using intermediate images.

Args: image_path: Path to the input image config: Processing configuration output_dir: Output directory (or None for default) overwrite: Whether to overwrite existing files

Returns: List[str]: List of output file paths"""
```

```python
class ProcessingOptimizer(object):
    """Analyzer for determining the optimal processing strategy.

This class analyzes processing configurations to determine the most efficient processing strategy, identifying shared operations."""
```
*Methods:*
```python
    def __init__(self, logger) -> None:
        """Initialize the processing optimizer.  Args: logger: Logger instance"""
```
```python
    def should_use_intermediate(self, config) -> bool:
        """Determine if intermediate image processing should be used.

Args: config: Processing configuration

Returns: bool: True if intermediate processing is recommended"""
```

###### Package: ui
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui`

**__init__.py:**
*UI components for the Media Processor Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/__init__.py`

**Imports:**
```python
from main_widget import MediaProcessorWidget
from batch_dialog import BatchProcessingDialog
from config_editor import ConfigEditorDialog
from format_editor import FormatEditorDialog
from preview_widget import ImagePreviewWidget
```

####### Module: ai_manager_dialog
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/ai_manager_dialog.py`

**Imports:**
```python
from __future__ import annotations
import os
import asyncio
from typing import Dict, List, Optional, Any, cast
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QListWidget, QListWidgetItem, QTabWidget, QWidget, QMessageBox, QGroupBox, QFormLayout, QSpacerItem, QSizePolicy, QCheckBox
from utils.ai_background_remover import AIBackgroundRemover, ModelDetails, ModelType
```

**Classes:**
```python
class AIModelManagerDialog(QDialog):
    """Dialog for managing AI models.

Allows downloading, viewing, and activating AI models for background removal."""
```
*Class attributes:*
```python
modelDownloaded =     modelDownloaded = Signal(str)
```
*Methods:*
```python
    def __init__(self, ai_background_remover, config_manager, logger, parent) -> None:
        """Initialize the dialog.

Args: ai_background_remover: AI background remover instance config_manager: Configuration manager instance logger: Logger instance parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
```

```python
class ModelDownloadWorker(QObject):
    """Worker for downloading models in a separate thread."""
```
*Class attributes:*
```python
progressChanged =     progressChanged = Signal(int, str)
finished =     finished = Signal(bool, str)
```
*Methods:*
```python
    def __init__(self, ai_background_remover, model_id) -> None:
        """Initialize the worker.

Args: ai_background_remover: AI background remover instance model_id: Model ID to download"""
```
```python
@Slot()
    async def download(self) -> None:
        """Download the model."""
```

####### Module: batch_dialog
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/batch_dialog.py`

**Imports:**
```python
from __future__ import annotations
from output_preview_table import OutputPreviewTable
import asyncio
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea, QWidget, QCheckBox, QGroupBox
from models.processing_config import ProcessingConfig
from processors.batch_processor import BatchProcessor
from utils.exceptions import BatchProcessingError
```

**Classes:**
```python
class BatchProcessingDialog(QDialog):
    """Dialog for batch processing of media files.

Shows: - Progress of batch processing - Controls for pause/resume/cancel - Detailed status info - Error reporting"""
```
*Class attributes:*
```python
processingComplete =     processingComplete = Signal(dict)  # results dictionary
```
*Methods:*
```python
    def __init__(self, batch_processor, file_paths, config, output_dir, overwrite, logger, parent) -> None:
        """Initialize the batch processing dialog.

Args: batch_processor: The batch processor file_paths: List of files to process config: Processing configuration output_dir: Optional override for output directory overwrite: Whether to overwrite existing files logger: Logger instance parent: Parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
```

####### Module: config_editor
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/config_editor.py`

**Imports:**
```python
from __future__ import annotations
import os
import time
from typing import Any, Dict, List, Optional, Set, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox, QPushButton, QTabWidget, QWidget, QListView, QDialogButtonBox, QGroupBox, QFrame, QScrollArea, QSizePolicy, QSlider, QToolButton, QMessageBox, QFileDialog
from models.processing_config import ProcessingConfig, BackgroundRemovalConfig, BackgroundRemovalMethod, OutputFormat
from format_editor import FormatEditorDialog
from processors.media_processor import MediaProcessor
```

**Classes:**
```python
class ConfigEditorDialog(QDialog):
    """Dialog for editing processing configurations.

Allows editing: - General configuration settings - Background removal options - Managing output formats - Batch processing options"""
```
*Class attributes:*
```python
configUpdated =     configUpdated = Signal(str)  # config_id
```
*Methods:*
```python
    def __init__(self, media_processor, file_manager, logger, plugin_config, config, parent) -> None:
        """Initialize the configuration editor dialog.

Args: media_processor: The media processor file_manager: File manager for saving/loading configs logger: Logger instance plugin_config: Plugin configuration config: Optional processing configuration to edit parent: Parent widget"""
```
```python
    def accept(self) -> None:
        """Handle dialog acceptance (OK button)."""
```
```python
    def get_config(self) -> ProcessingConfig:
        """Get the edited configuration.  Returns: Updated processing configuration"""
```
```python
    def reject(self) -> None:
        """Handle dialog rejection (Cancel button)."""
```

####### Module: format_editor
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/format_editor.py`

**Imports:**
```python
from __future__ import annotations
from format_preview_widget import FormatPreviewWidget
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QColor, QIcon, QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton, QTabWidget, QWidget, QColorDialog, QFileDialog, QDialogButtonBox, QGroupBox, QRadioButton, QButtonGroup, QScrollArea, QSizePolicy, QSlider, QToolButton, QFrame, QSplitter
from models.processing_config import OutputFormat, ImageFormat, ResizeMode, WatermarkType, WatermarkPosition
```

**Classes:**
```python
class ColorButton(QPushButton):
    """Button for selecting colors with preview."""
```
*Class attributes:*
```python
colorChanged =     colorChanged = Signal(QColor)
```
*Methods:*
```python
    def __init__(self, color, parent) -> None:
        """Initialize the color button.  Args: color: Initial color in hex format parent: Parent widget"""
```
```python
    def get_color(self) -> QColor:
        """Get the selected color.  Returns: Selected color"""
```
```python
    def get_hex_color(self) -> str:
        """Get the color as hex string.  Returns: Color in hex format (#RRGGBB)"""
```
```python
    def set_color(self, color) -> None:
        """Set the button color.  Args: color: New color as hex string or QColor"""
```

```python
class FormatEditorDialog(QDialog):
    """Dialog for editing output format settings.

Allows editing: - Format type and quality - Size and cropping - Background settings - Watermarks - Naming and organization"""
```
*Methods:*
```python
    def __init__(self, format_config, logger, parent) -> None:
        """Initialize the format editor dialog.

Args: format_config: Output format configuration to edit logger: Logger instance parent: Parent widget"""
```
```python
    def accept(self) -> None:
        """Handle dialog acceptance (OK button)."""
```
```python
    def get_format(self) -> OutputFormat:
        """Get the edited format configuration.  Returns: Updated output format configuration"""
```
```python
    def showEvent(self, event) -> None:
        """Handle dialog show event.  Args: event: Show event"""
```

####### Module: format_preview_widget
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/format_preview_widget.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import time
from typing import Optional, Dict, Any, Callable, Union
from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox, QPushButton, QProgressBar, QFrame, QSizePolicy
from models.processing_config import OutputFormat, BackgroundRemovalConfig
from utils.exceptions import MediaProcessingError
from ui.preview_widget import ImagePreviewWidget
```

**Classes:**
```python
class FormatPreviewWidget(QWidget):
    """Widget for providing live preview of format changes.

This widget displays a preview of the current image with format settings applied, and can automatically update when settings change or provide manual refresh option."""
```
*Class attributes:*
```python
previewRequested =     previewRequested = Signal()
```
*Methods:*
```python
    def __init__(self, media_processor, logger, preview_file_path, parent) -> None:
        """Initialize the format preview widget.

Args: media_processor: Instance of MediaProcessor logger: Logger instance preview_file_path: Path to the image to preview parent: Parent widget"""
```
```python
    def set_background_removal(self, bg_removal_config) -> None:
        """Set the background removal configuration.

Args: bg_removal_config: Background removal configuration"""
```
```python
    def set_format(self, format_config) -> None:
        """Set the format configuration to preview.  Args: format_config: Format configuration"""
```
```python
    def set_preview_image(self, file_path) -> None:
        """Set the image to use for preview.  Args: file_path: Path to the image file"""
```
```python
    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget.  Returns: QSize: Recommended size"""
```

####### Module: main_widget
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/main_widget.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QSplitter, QListWidget, QListWidgetItem, QFileDialog, QComboBox, QGroupBox, QCheckBox, QMessageBox, QScrollArea, QToolButton, QMenu, QApplication, QFrame, QDialog
from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from models.processing_config import ProcessingConfig, OutputFormat, BackgroundRemovalConfig
from processors.media_processor import MediaProcessor
from processors.batch_processor import BatchProcessor
from utils.exceptions import MediaProcessingError
from batch_dialog import BatchProcessingDialog
from config_editor import ConfigEditorDialog
from format_editor import FormatEditorDialog
from preview_widget import ImagePreviewWidget
```

**Classes:**
```python
class MediaProcessorWidget(QWidget):
    """Main widget for the Media Processor.

This widget provides: - File selection (single or batch) - Processing configuration selection/editing - Preview of processing - Output format configuration - Batch processing controls"""
```
*Class attributes:*
```python
processingStarted =     processingStarted = Signal()
processingFinished =     processingFinished = Signal(bool, str)  # success, message
configChanged =     configChanged = Signal(str)  # config_id
```
*Methods:*
```python
    def __init__(self, media_processor, batch_processor, file_manager, event_bus_manager, concurrency_manager, task_manager, logger, plugin_config, parent) -> None:
        """Initialize the Media Processor widget.

Args: media_processor: The media processor batch_processor: The batch processor file_manager: The file manager event_bus_manager: The event bus manager concurrency_manager: The concurrency manager task_manager: The task manager logger: The logger plugin_config: Plugin configuration parent: Parent widget"""
```
```python
    def dragEnterEvent(self, event) -> None:
        """Handle drag enter event for drag and drop."""
```
```python
    def dropEvent(self, event) -> None:
        """Handle drop event for drag and drop."""
```

####### Module: output_preview_table
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/output_preview_table.py`

**Imports:**
```python
from __future__ import annotations
import os
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize, QPoint
from PySide6.QtGui import QColor, QIcon, QStandardItemModel, QStandardItem, QAction
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeView, QHeaderView, QCheckBox, QFrame, QSplitter, QWidget, QFileDialog, QMessageBox, QMenu, QProgressBar
from models.processing_config import ProcessingConfig
from utils.path_resolver import resolve_output_path
```

**Classes:**
```python
class OutputPreviewTable(QDialog):
    """Dialog showing a preview of output files before processing begins.

Displays a table with expected outputs, status, and allows for adjustments."""
```
*Class attributes:*
```python
processingConfirmed =     processingConfirmed = Signal(bool)  # True if confirmed, False if cancelled
```
*Methods:*
```python
    def __init__(self, file_paths, config, output_dir, overwrite, logger, parent) -> None:
        """Initialize the output preview table.

Args: file_paths: List of input file paths config: Processing configuration output_dir: Output directory (or None for default) overwrite: Whether to overwrite existing files logger: Logger instance parent: Parent widget"""
```
```python
    def get_output_dir(self) -> str:
        """Get the selected output directory.  Returns: str: Output directory"""
```
```python
    def get_overwrite(self) -> bool:
        """Get the overwrite setting.  Returns: bool: Whether to overwrite existing files"""
```
```python
    def reject(self) -> None:
        """Handle dialog rejection (cancel)."""
```

```python
class OutputStatus(Enum):
    """Status of output files."""
```
*Class attributes:*
```python
NEW = 'new'
OVERWRITE = 'overwrite'
INCREMENT = 'increment'
```

####### Module: preview_widget
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/ui/preview_widget.py`

**Imports:**
```python
from __future__ import annotations
import io
import os
from typing import Optional, Union
from PySide6.QtCore import Qt, Signal, Slot, QSize, QRectF, QPointF, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QBrush, QColor, QResizeEvent, QPaintEvent, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy
```

**Classes:**
```python
class ImagePreviewWidget(QWidget):
    """Widget for displaying image previews with zoom controls.

Features: - Image loading from file or bytes - Zoom in/out with mouse wheel - Pan with mouse drag - Status and error messages - Loading indicator"""
```
*Class attributes:*
```python
zoomChanged =     zoomChanged = Signal(float)  # Current zoom level
```
*Methods:*
```python
    def __init__(self, logger, parent) -> None:
        """Initialize the image preview widget.  Args: logger: Optional logger instance parent: Parent widget"""
```
```python
    def clear(self) -> None:
        """Clear the image and reset the widget."""
```
```python
    def get_image(self) -> Optional[QImage]:
        """Get the current image.  Returns: The current image, or None if no image is loaded"""
```
```python
    def load_image(self, file_path) -> bool:
        """Load an image from a file path.

Args: file_path: Path to the image file

Returns: True if loaded successfully, False otherwise"""
```
```python
    def load_image_data(self, data) -> bool:
        """Load an image from raw bytes.

Args: data: Image data as bytes

Returns: True if loaded successfully, False otherwise"""
```
```python
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move event for panning.  Args: event: Mouse event"""
```
```python
    def mousePressEvent(self, event) -> None:
        """Handle mouse press event for panning.  Args: event: Mouse event"""
```
```python
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release event for panning.  Args: event: Mouse event"""
```
```python
    def paintEvent(self, event) -> None:
        """Handle paint event to draw the image and status.  Args: event: Paint event"""
```
```python
    def reset_view(self) -> None:
        """Reset zoom and panning to default values."""
```
```python
    def resizeEvent(self, event) -> None:
        """Handle resize event.  Args: event: Resize event"""
```
```python
    def set_error(self, error_text) -> None:
        """Set an error message.  Args: error_text: Error message to display"""
```
```python
    def set_loading(self, loading) -> None:
        """Set the loading state.  Args: loading: Whether the widget is in loading state"""
```
```python
    def set_status(self, status_text) -> None:
        """Set a status message.  Args: status_text: Status message to display"""
```
```python
    def set_zoom(self, zoom_factor) -> None:
        """Set the zoom factor.  Args: zoom_factor: New zoom factor"""
```
```python
    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget.  Returns: Recommended size"""
```
```python
    def wheelEvent(self, event) -> None:
        """Handle wheel event for zooming.  Args: event: Wheel event"""
```

###### Package: utils
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/utils`

**__init__.py:**
*Utility functions for the Media Processor Plugin.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/utils/__init__.py`

**Imports:**
```python
from exceptions import MediaProcessingError, ImageProcessingError, BatchProcessingError, ConfigurationError, BackgroundRemovalError, OutputFormatError, FileIOError
from path_resolver import resolve_output_path, generate_filename, generate_batch_folder_name, get_unique_output_path
from image_utils import get_image_info, is_transparent, convert_to_format, fit_image_to_size, create_gradient_mask, apply_threshold_mask, auto_contrast_mask, generate_thumbnail
```

####### Module: ai_background_remover
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/utils/ai_background_remover.py`

**Imports:**
```python
from __future__ import annotations
import os
import asyncio
import urllib.request
import zipfile
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union, cast, Callable
from enum import Enum
import numpy as np
from pathlib import Path
import json
from PIL import Image, ImageFilter
import torch
import torchvision.transforms as transforms
from models.processing_config import BackgroundRemovalConfig
from utils.exceptions import BackgroundRemovalError
```

**Classes:**
```python
class AIBackgroundRemover(object):
    """Background removal implementation using deep learning models.

This class handles downloading, loading, and applying AI models for background removal tasks."""
```
*Methods:*
```python
    def __init__(self, file_manager, config_manager, logger):
        """Initialize the AI background remover.

Args: file_manager: File manager instance config_manager: Configuration manager instance logger: Logger instance"""
```
```python
    async def download_model(self, model_id, progress_callback) -> bool:
        """Download a model file.

Args: model_id: The model identifier progress_callback: Optional callback for progress updates

Returns: bool: True if download was successful"""
```
```python
    async def get_model_info(self, model_id) -> Dict[(str, Any)]:
        """Get information about a model.

Args: model_id: The model identifier

Returns: Dict[str, Any]: Model information"""
```
```python
    async def initialize(self) -> bool:
        """Initialize the background remover. Sets up model directory and checks for downloaded models.

Returns: bool: True if initialization was successful"""
```
```python
    async def is_model_downloaded(self, model_id) -> bool:
        """Check if a specific model is downloaded.

Args: model_id: The model identifier

Returns: bool: True if the model is downloaded"""
```
```python
    async def remove_background(self, image, config) -> Image.Image:
        """Remove background from an image using AI models.

Args: image: Input image config: Background removal configuration

Returns: Image.Image: Image with background removed"""
```

```python
class ModelDetails(object):
    """Details about available models."""
```
*Class attributes:*
```python
MODELS =     MODELS = {
        ModelType.U2NET: {
            "name": "U2Net",
            "description": "Original U2Net model for salient object detection",
            "url": "https://github.com/xuebinqin/U-2-Net/releases/download/U2NetHumanSeg/u2net_human_seg.pth",
            "size": 173475292,  # ~173MB
            "hash": "bc788c85e60baed816ffd6e2b2c6ae8a2b0afa57e335a14cc323cf1edf79abde"
        },
        ModelType.U2NETP: {
            "name": "U2Net-Lite",
            "description": "Lightweight version of U2Net (4.7MB)",
            "url": "https://github.com/xuebinqin/U-2-Net/releases/download/U2NetP/u2netp.pth",
            "size": 4710256,  # ~4.7MB
            "hash": "8cb63ecf8d9a4b62be6abf8e5c8a52d9ebeb7fcb9c64d4a561b5682f2a734af6"
        },
        ModelType.ISNET: {
            "name": "ISNet",
            "description": "ISNet for high-quality human segmentation",
            "url": "https://github.com/xuebinqin/DIS/releases/download/1.1/isnet.pth",
            "size": 176320856,  # ~176MB
            "hash": "a1ca63c02e6c4e371a0a3e6a75223ca2e1b1755caa095f6b334f17f6b4292969"
        },
        ModelType.MODNET: {
            "name": "MODNet",
            "description": "MODNet for real-time portrait matting",
            "url": "https://github.com/ZHKKKe/MODNet/releases/download/v1.0/modnet_photographic_portrait_matting.pth",
            "size": 24002228,  # ~24MB
            "hash": "815b64834ba6942c84c7b1c7ea36ebcbcb80b3e2c88b2d3eb25e7cc3fdb9453c"
        }
    }
```

```python
class ModelType(str, Enum):
    """Types of supported segmentation models."""
```
*Class attributes:*
```python
U2NET = 'u2net'
U2NETP = 'u2netp'
ISNET = 'isnet'
MODNET = 'modnet'
```

####### Module: config_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/utils/config_manager.py`

**Imports:**
```python
from __future__ import annotations
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from pathlib import Path
from models.processing_config import ProcessingConfig
```

**Classes:**
```python
class ConfigManager(object):
    """Manages the storage and retrieval of format configurations and plugin settings."""
```
*Class attributes:*
```python
CONFIG_DIR = 'media_processor'
FORMATS_FILE = 'format_configs.json'
SETTINGS_FILE = 'settings.json'
```
*Methods:*
```python
    def __init__(self, file_manager, logger):
        """Initialize the config manager.

Args: file_manager: The file manager instance from Qorzen core logger: Logger instance"""
```
```python
    def add_or_update_config(self, config) -> bool:
        """Add or update a configuration.

Args: config: The configuration to add or update

Returns: bool: True if successful"""
```
```python
    def get_all_configs(self) -> Dict[(str, ProcessingConfig)]:
        """Get all loaded configurations.  Returns: Dict[str, ProcessingConfig]: Dictionary of configurations"""
```
```python
    def get_config(self, config_id) -> Optional[ProcessingConfig]:
        """Get a configuration by ID.

Args: config_id: The configuration ID

Returns: Optional[ProcessingConfig]: The configuration or None if not found"""
```
```python
    def get_setting(self, key, default) -> Any:
        """Get a setting value.

Args: key: The setting key default: Default value if setting not found

Returns: Any: The setting value or default"""
```
```python
    async def initialize(self) -> bool:
        """Initialize the configuration system. Creates necessary directories and loads existing configurations.

Returns: bool: True if initialization was successful"""
```
```python
    async def load_configurations(self) -> Dict[(str, ProcessingConfig)]:
        """Load saved format configurations from disk.

Returns: Dict[str, ProcessingConfig]: Dictionary of loaded configurations"""
```
```python
    async def load_settings(self) -> Dict[(str, Any)]:
        """Load plugin settings from disk.  Returns: Dict[str, Any]: Plugin settings"""
```
```python
    def remove_config(self, config_id) -> bool:
        """Remove a configuration.

Args: config_id: The ID of the configuration to remove

Returns: bool: True if successful"""
```
```python
    async def save_configurations(self) -> bool:
        """Save all configurations to disk.  Returns: bool: True if save was successful"""
```
```python
    async def save_settings(self) -> bool:
        """Save plugin settings to disk.  Returns: bool: True if save was successful"""
```
```python
    def set_setting(self, key, value) -> bool:
        """Set a setting value.

Args: key: The setting key value: The setting value

Returns: bool: True if successful"""
```

####### Module: exceptions
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/utils/exceptions.py`

**Imports:**
```python
from __future__ import annotations
from typing import Optional
```

**Classes:**
```python
class BackgroundRemovalError(ImageProcessingError):
    """Exception raised when background removal fails."""
```
*Methods:*
```python
    def __init__(self, message, file_path, method) -> None:
        """Initialize the exception.

Args: message: Error message file_path: Optional path to the file that caused the error method: Optional background removal method that failed"""
```

```python
class BatchProcessingError(MediaProcessingError):
    """Exception raised when a batch processing operation fails."""
```
*Methods:*
```python
    def __init__(self, message, job_id) -> None:
        """Initialize the exception.  Args: message: Error message job_id: Optional ID of the batch job"""
```

```python
class ConfigurationError(MediaProcessingError):
    """Exception raised when there's an error in processing configuration."""
```
*Methods:*
```python
    def __init__(self, message, config_id) -> None:
        """Initialize the exception.  Args: message: Error message config_id: Optional ID of the configuration"""
```

```python
class FileIOError(MediaProcessingError):
    """Exception raised when file I/O operations fail."""
```
*Methods:*
```python
    def __init__(self, message, file_path, is_input) -> None:
        """Initialize the exception.

Args: message: Error message file_path: Optional path to the file that caused the error is_input: True if reading, False if writing"""
```

```python
class ImageProcessingError(MediaProcessingError):
    """Exception raised when processing a specific image fails."""
```
*Methods:*
```python
    def __init__(self, message, file_path, format_id) -> None:
        """Initialize the exception.

Args: message: Error message file_path: Optional path to the file that caused the error format_id: Optional ID of the format being applied"""
```

```python
class MediaProcessingError(Exception):
    """Base exception for errors in media processing."""
```
*Methods:*
```python
    def __init__(self, message, file_path) -> None:
        """Initialize the exception.

Args: message: Error message file_path: Optional path to the file that caused the error"""
```

```python
class OutputFormatError(ImageProcessingError):
    """Exception raised when applying an output format fails."""
```
*Methods:*
```python
    def __init__(self, message, file_path, format_id, format_name) -> None:
        """Initialize the exception.

Args: message: Error message file_path: Optional path to the file that caused the error format_id: Optional ID of the format being applied format_name: Optional name of the format being applied"""
```

####### Module: font_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/utils/font_manager.py`

**Imports:**
```python
from __future__ import annotations
import os
import sys
import platform
from typing import Dict, List, Optional, Set, Tuple, Any, Union, cast
from pathlib import Path
import asyncio
from PIL import ImageFont, Image, ImageDraw
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem, QFileDialog, QLineEdit, QDialog, QTabWidget, QScrollArea, QGroupBox, QFormLayout, QSpinBox
```

**Classes:**
```python
class FontManager(object):
    """Font manager for handling font loading, selection, and rendering.

Provides cross-platform font capabilities and loading from absolute paths."""
```
*Methods:*
```python
    def __init__(self, logger) -> None:
        """Initialize the font manager.  Args: logger: Logger instance"""
```
```python
    def add_custom_font(self, name, path) -> bool:
        """Add a custom font from path.

Args: name: Font name path: Path to font file

Returns: bool: True if font was added successfully"""
```
```python
    def get_custom_fonts(self) -> Dict[(str, str)]:
        """Get dictionary of custom fonts.  Returns: Dict[str, str]: Dictionary mapping font names to paths"""
```
```python
    def get_font(self, font_name, size) -> ImageFont.FreeTypeFont:
        """Get a PIL font object from name and size.

Args: font_name: Font name size: Font size in points

Returns: ImageFont.FreeTypeFont: PIL font object

Raises: ValueError: If font cannot be loaded"""
```
```python
    def get_system_fonts(self) -> List[str]:
        """Get list of available system fonts.  Returns: List[str]: List of font names"""
```
```python
    def remove_custom_font(self, name) -> bool:
        """Remove a custom font.  Args: name: Font name  Returns: bool: True if font was removed"""
```
```python
    def render_font_preview(self, font_name, size, text, width, height, color, background) -> Optional[bytes]:
        """Generate a preview image of a font.

Args: font_name: Name of the font size: Font size in points text: Text to render width: Width of preview image height: Height of preview image color: Text color (RGB) background: Background color (RGB)

Returns: Optional[bytes]: PNG image data or None on error"""
```

```python
class FontSelector(QWidget):
    """Widget for selecting and previewing fonts.

Provides a UI for choosing system fonts or custom font files."""
```
*Class attributes:*
```python
fontSelected =     fontSelected = Signal(str)
```
*Methods:*
```python
    def __init__(self, font_manager, logger, initial_font, parent) -> None:
        """Initialize the font selector.

Args: font_manager: Font manager instance logger: Logger instance initial_font: Initial font selection parent: Parent widget"""
```
```python
    def get_selected_font(self) -> str:
        """Get the selected font name.  Returns: str: Selected font name"""
```

```python
class FontSelectorDialog(QDialog):
    """Dialog for selecting a font.  Provides a dialog wrapper around the FontSelector widget."""
```
*Methods:*
```python
    def __init__(self, font_manager, logger, initial_font, parent) -> None:
        """Initialize the font selector dialog.

Args: font_manager: Font manager instance logger: Logger instance initial_font: Initial font selection parent: Parent widget"""
```
```python
    def get_selected_font(self) -> str:
        """Get the selected font name.  Returns: str: Selected font name"""
```

####### Module: image_utils
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/utils/image_utils.py`

**Imports:**
```python
from __future__ import annotations
from PIL.Image import Resampling
import io
import os
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageOps, ImageFilter
from io import BytesIO
```

**Functions:**
```python
def apply_threshold_mask(image, threshold_min, threshold_max, feather) -> Image.Image:
    """Apply a threshold-based alpha mask to an image.

Args: image: PIL Image object threshold_min: Minimum brightness threshold (0-255) threshold_max: Maximum brightness threshold (0-255) feather: Amount of feathering to apply to the mask

Returns: Image with alpha mask applied"""
```

```python
def auto_contrast_mask(mask, cutoff) -> Image.Image:
    """Apply auto contrast to a mask to improve edge definition.

Args: mask: PIL Image mask (L mode) cutoff: Percentage to cut off from histogram (0.0-1.0)

Returns: Enhanced mask"""
```

```python
def convert_to_format(image, format_name, quality, transparent) -> bytes:
    """Convert an image to the specified format.

Args: image: PIL Image object format_name: Target format name (e.g., "PNG", "JPEG") quality: Quality setting (1-100) transparent: Whether to preserve transparency

Returns: Image data as bytes"""
```

```python
def create_gradient_mask(width, height, center_opacity, edge_opacity, radius_factor) -> Image.Image:
    """Create a radial gradient mask image.

Args: width: Width of the mask height: Height of the mask center_opacity: Opacity at the center (0.0-1.0) edge_opacity: Opacity at the edges (0.0-1.0) radius_factor: Factor to determine gradient radius (0.0-1.0)

Returns: Gradient mask as PIL Image"""
```

```python
def fit_image_to_size(image, max_width, max_height, maintain_aspect) -> Image.Image:
    """Resize an image to fit within the specified dimensions.

Args: image: PIL Image object max_width: Maximum width max_height: Maximum height maintain_aspect: Whether to maintain aspect ratio

Returns: Resized image"""
```

```python
def generate_thumbnail(image, size, maintain_aspect) -> Image.Image:
    """Generate a thumbnail from an image.

Args: image: PIL Image object size: Maximum size as single value or (width, height) tuple maintain_aspect: Whether to maintain aspect ratio

Returns: Thumbnail image"""
```

```python
def get_image_info(file_path) -> Dict[(str, Any)]:
    """Get information about an image file.

Args: file_path: Path to the image file

Returns: Dictionary with image information

Raises: IOError: If the file cannot be opened or is not a valid image"""
```

```python
def is_transparent(image) -> bool:
    """Check if an image has transparency.

Args: image: PIL Image object

Returns: True if image has transparency, False otherwise"""
```

####### Module: path_resolver
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/media_processor_plugin/code/utils/path_resolver.py`

**Imports:**
```python
from __future__ import annotations
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from exceptions import MediaProcessingError
```

**Functions:**
```python
def generate_batch_folder_name(template) -> str:
    """Generate a folder name for batch processing.

Args: template: Folder name template with placeholders

Returns: Generated folder name

Supported template placeholders: {date} - Current date in YYYY-MM-DD format {time} - Current time in HH-MM-SS format {timestamp} - Unix timestamp {random} - Random 8-character string"""
```

```python
def generate_filename(template, base_name, extension, prefix, suffix) -> str:
    """Generate a filename based on a template.

Args: template: Filename template with placeholders base_name: Base filename without extension extension: File extension (without dot) prefix: Optional prefix to add suffix: Optional suffix to add

Returns: Generated filename

Supported template placeholders: {name} - Original filename without extension {ext} - File extension {date} - Current date in YYYY-MM-DD format {time} - Current time in HH-MM-SS format {timestamp} - Unix timestamp {random} - Random 8-character string {counter} - Will be replaced with a counter if file exists

Example: "{name}_{date}.{ext}" -> "image_2023-05-17.png""""
```

```python
def get_unique_output_path(base_path) -> str:
    """Ensure a path is unique by adding a counter if needed.

Args: base_path: The base file path

Returns: A unique file path"""
```

```python
def resolve_output_path(input_path, output_dir, format_config, file_exists_handler) -> str:
    """Resolve the output path for a processed file.

Args: input_path: Path to the input file output_dir: Base output directory format_config: Output format configuration file_exists_handler: Optional callback for handling existing files

Returns: Resolved output path"""
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
from qorzen.ui.settings_manager import SettingsManager
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

#### Module: settings_manager
*processed_project/qorzen_stripped/ui/settings_manager.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/settings_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, TypedDict, Protocol
from PySide6.QtCore import QAbstractItemModel, QModelIndex, QPersistentModelIndex, QTimer, Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont, QIcon, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSpinBox, QSplitter, QStackedWidget, QTabWidget, QTextEdit, QTreeView, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QMessageBox, QProgressBar, QSlider, QFileDialog, QColorDialog, QFontDialog
```

**Classes:**
```python
class BooleanSettingWidget(SettingWidget):
    """Widget for boolean settings."""
```
*Methods:*
```python
    def get_value(self) -> bool:
```
```python
    def set_value(self, value) -> None:
```
```python
    def setup_ui(self) -> None:
```

```python
class ChoiceSettingWidget(SettingWidget):
    """Widget for choice settings."""
```
*Methods:*
```python
    def get_value(self) -> Any:
```
```python
    def set_value(self, value) -> None:
```
```python
    def setup_ui(self) -> None:
```

```python
class FloatSettingWidget(SettingWidget):
    """Widget for float settings."""
```
*Methods:*
```python
    def get_value(self) -> float:
```
```python
    def set_value(self, value) -> None:
```
```python
    def setup_ui(self) -> None:
```

```python
class IntegerSettingWidget(SettingWidget):
    """Widget for integer settings."""
```
*Methods:*
```python
    def get_value(self) -> int:
```
```python
    def set_value(self, value) -> None:
```
```python
    def setup_ui(self) -> None:
```

```python
class JsonSettingWidget(SettingWidget):
    """Widget for JSON/dict settings."""
```
*Methods:*
```python
    def get_value(self) -> Any:
```
```python
    def set_value(self, value) -> None:
```
```python
    def setup_ui(self) -> None:
```

```python
class PathSettingWidget(SettingWidget):
    """Widget for file/directory path settings."""
```
*Methods:*
```python
    def get_value(self) -> str:
```
```python
    def set_value(self, value) -> None:
```
```python
    def setup_ui(self) -> None:
```

```python
class SettingCategory(str, Enum):
    """Categories for organizing settings."""
```
*Class attributes:*
```python
APPLICATION = 'Application'
DATABASE = 'Database'
LOGGING = 'Logging'
SECURITY = 'Security'
API = 'API'
PLUGINS = 'Plugins'
MONITORING = 'Monitoring'
FILES = 'Files'
CLOUD = 'Cloud'
NETWORKING = 'Networking'
PERFORMANCE = 'Performance'
UI = 'User Interface'
ADVANCED = 'Advanced'
```

```python
@dataclass
class SettingDefinition(object):
    """Definition of a configurable setting."""
```

```python
class SettingType(str, Enum):
    """Types of settings that can be configured."""
```
*Class attributes:*
```python
STRING = 'string'
INTEGER = 'integer'
FLOAT = 'float'
BOOLEAN = 'boolean'
LIST = 'list'
DICT = 'dict'
PATH = 'path'
COLOR = 'color'
FONT = 'font'
PASSWORD = 'password'
CHOICE = 'choice'
JSON = 'json'
```

```python
class SettingWidget(QWidget):
    """Base class for setting input widgets."""
```
*Class attributes:*
```python
valueChanged =     valueChanged = Signal(object)
```
*Methods:*
```python
    def __init__(self, setting_def, parent):
```
```python
    def get_value(self) -> Any:
        """Get the current value from the widget."""
```
```python
    def set_value(self, value) -> None:
        """Set the value in the widget."""
```
```python
    def setup_ui(self) -> None:
        """Setup the widget UI."""
```
```python
    def validate(self) -> tuple[(bool, str)]:
        """Validate the current value."""
```

```python
class SettingsManager(QWidget):
    """Main settings manager widget."""
```
*Class attributes:*
```python
settingChanged =     settingChanged = Signal(str, object)  # key, value
settingsSaved =     settingsSaved = Signal()
```
*Methods:*
```python
    def __init__(self, app_core, parent):
```
```python
    async def load_current_values(self) -> None:
        """Load current values from configuration."""
```
```python
    def load_setting_definitions(self) -> None:
        """Load all setting definitions from the managers."""
```
```python
    def setup_ui(self) -> None:
        """Setup the main UI layout."""
```

```python
class StringSettingWidget(SettingWidget):
    """Widget for string settings."""
```
*Methods:*
```python
    def get_value(self) -> str:
```
```python
    def set_value(self, value) -> None:
```
```python
    def setup_ui(self) -> None:
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
class ValidationError(QorzenError):
    """Exception raised for validation-related errors."""
```
*Methods:*
```python
    def __init__(self, message, *args, **kwargs) -> None:
        """Initialize a ValidationError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. **kwargs: Additional keyword arguments to pass to the parent Exception."""
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

