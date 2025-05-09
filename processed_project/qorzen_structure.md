# qorzen Project Structure
Generated on 2025-05-09 20:38:23

## Table of Contents
1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Packages and Modules](#packages-and-modules)

## Project Overview
- Project Name: qorzen
- Root Path: /home/runner/work/qorzen/qorzen/qorzen
- Packages: 6
- Top-level Modules: 5

## Directory Structure
```
qorzen/
├── core/
│   ├── __init__.py
│   ├── api_manager.py
│   ├── app.py
│   ├── base.py
│   ├── cloud_manager.py
│   ├── config_manager.py
│   ├── database_manager.py
│   ├── event_bus_manager.py
│   ├── event_model.py
│   ├── file_manager.py
│   ├── logging_manager.py
│   ├── monitoring_manager.py
│   ├── plugin_error_handler.py
│   ├── plugin_manager.py
│   ├── remote_manager.py
│   ├── security_manager.py
│   └── thread_manager.py
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
│   ├── repository.py
│   ├── signing.py
│   └── tools.py
├── plugins/
│   ├── aces_validator/
│   │   └── __init__.py
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
│   ├── event_monitor_plugin/
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── example_plugin/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   ├── hooks.py
│   │   │   └── plugin.py
│   │   ├── Manifest.json
│   │   ├── README.md
│   │   └── __init__.py
│   ├── system_monitor/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   ├── hooks.py
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
│   ├── integration.py
│   ├── logs.py
│   ├── panel_ui.py
│   └── plugins.py
├── utils/
│   ├── __init__.py
│   └── exceptions.py
├── __init__.py
├── __main__.py
├── __version__.py
├── main.py
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
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer
import qorzen.resources_rc
```

**Functions:**
```python
def handle_build_command(args) -> int:
    """Handle the build command.  Args: args: The command line arguments  Returns: The exit code"""
```

```python
def main() -> int:
    """Main entry point for the application.  Returns: The exit code"""
```

```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.  Returns: The parsed arguments"""
```

```python
def run_headless(args) -> int:
    """Run the application in headless mode.

Args: args: The command line arguments

Returns: The exit code"""
```

```python
def run_steps(steps, on_complete, on_error) -> None:
    """Run a sequence of steps asynchronously.

Args: steps: The steps to run on_complete: Callback for when all steps complete successfully on_error: Callback for when a step fails"""
```

```python
def setup_environment() -> None:
    """Set up the environment for running the application."""
```

```python
def start_ui(args) -> int:
    """Start the application UI.

Args: args: The command line arguments

Returns: The application exit code"""
```

### Module: resources_rc
Path: `/home/runner/work/qorzen/qorzen/qorzen/resources_rc.py`

**Imports:**
```python
from PySide6 import QtCore
```

**Global Variables:**
```python
qt_resource_data = b'\x00\x00\x01g<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M520-600v-240h320v240H520ZM120-440v-400h320v400H120Zm400 320v-400h320v400H520Zm-400 0v-240h320v240H120Zm80-400h160v-240H200v240Zm400 320h160v-240H600v240Zm0-480h160v-80H600v80ZM200-200h160v-80H200v80Zm160-320Zm240-160Zm0 240ZM360-280Z"/></svg>\x00\x00\x03\xe0<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M472-120q-73-1-137.5-13.5t-112-34Q175-189 147.5-218T120-280q0 33 27.5 62t75 50.5q47.5 21.5 112 34T472-120Zm-71-204q-30-3-58-8t-53.5-12q-25.5-7-48-15.5T200-379q19 11 41.5 19.5t48 15.5q25.5 7 53.5 12t58 8Zm79-275q86 0 177.5-26T760-679q-11-29-100.5-55T480-760q-91 0-178.5 25.5T200-679q15 29 104.5 54.5T480-599Zm-61 396q10 23 23 44t30 39q-73-1-137.5-13.5t-112-34Q175-189 147.5-218T120-280v-400q0-33 28.5-62t77.5-51q49-22 114.5-34.5T480-840q74 0 139.5 12.5T734-793q49 22 77.5 51t28.5 62q0 33-28.5 62T734-567q-49 22-114.5 34.5T480-520q-85 0-157-15t-123-44v101q40 37 100 54t121 22q-8 15-13 34.5t-7 43.5q-60-7-111.5-20T200-379v99q14 25 77 47t142 30ZM864-40 756-148q-22 13-46 20.5t-50 7.5q-75 0-127.5-52.5T480-300q0-75 52.5-127.5T660-480q75 0 127.5 52.5T840-300q0 26-7.5 50T812-204L920-96l-56 56ZM660-200q42 0 71-29t29-71q0-42-29-71t-71-29q-42 0-71 29t-29 71q0 42 29 71t71 29Z"/></svg>\x00\x00\x01\x96<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M400-400h160v-80H400v80Zm0-120h320v-80H400v80Zm0-120h320v-80H400v80Zm-80 400q-33 0-56.5-23.5T240-320v-480q0-33 23.5-56.5T320-880h480q33 0 56.5 23.5T880-800v480q0 33-23.5 56.5T800-240H320Zm0-80h480v-480H320v480ZM160-80q-33 0-56.5-23.5T80-160v-560h80v560h560v80H160Zm160-720v480-480Z"/></svg>\x00\x00\x02b<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M352-120H200q-33 0-56.5-23.5T120-200v-152q48 0 84-30.5t36-77.5q0-47-36-77.5T120-568v-152q0-33 23.5-56.5T200-800h160q0-42 29-71t71-29q42 0 71 29t29 71h160q33 0 56.5 23.5T800-720v160q42 0 71 29t29 71q0 42-29 71t-71 29v160q0 33-23.5 56.5T720-120H568q0-50-31.5-85T460-240q-45 0-76.5 35T352-120Zm-152-80h85q24-66 77-93t98-27q45 0 98 27t77 93h85v-240h80q8 0 14-6t6-14q0-8-6-14t-14-6h-80v-240H480v-80q0-8-6-14t-14-6q-8 0-14 6t-6 14v80H200v88q54 20 87 67t33 105q0 57-33 104t-87 68v88Zm260-260Z"/></svg>\x00\x00\x02\xd9<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M480-120q-151 0-255.5-46.5T120-280v-400q0-66 105.5-113T480-840q149 0 254.5 47T840-680v400q0 67-104.5 113.5T480-120Zm0-479q89 0 179-25.5T760-679q-11-29-100.5-55T480-760q-91 0-178.5 25.5T200-679q14 30 101.5 55T480-599Zm0 199q42 0 81-4t74.5-11.5q35.5-7.5 67-18.5t57.5-25v-120q-26 14-57.5 25t-67 18.5Q600-528 561-524t-81 4q-42 0-82-4t-75.5-11.5Q287-543 256-554t-56-25v120q25 14 56 25t66.5 18.5Q358-408 398-404t82 4Zm0 200q46 0 93.5-7t87.5-18.5q40-11.5 67-26t32-29.5v-98q-26 14-57.5 25t-67 18.5Q600-328 561-324t-81 4q-42 0-82-4t-75.5-11.5Q287-343 256-354t-56-25v99q5 15 31.5 29t66.5 25.5q40 11.5 88 18.5t94 7Z"/></svg>'
qt_resource_name = b"\x00\x08\x0f_\xad3\x00u\x00i\x00_\x00i\x00c\x00o\x00n\x00s\x00\r\r\x94\x89\xc7\x00d\x00a\x00s\x00h\x00b\x00o\x00a\x00r\x00d\x00.\x00s\x00v\x00g\x00\x13\x01\xbb\x8c\xa7\x00d\x00a\x00t\x00a\x00b\x00a\x00s\x00e\x00-\x00s\x00e\x00a\x00r\x00c\x00h\x00.\x00s\x00v\x00g\x00\x11\x07)\xce'\x00l\x00i\x00b\x00r\x00a\x00r\x00y\x00-\x00b\x00o\x00o\x00k\x00s\x00.\x00s\x00v\x00g\x00\r\t\xd4\xd0G\x00e\x00x\x00t\x00e\x00n\x00s\x00i\x00o\x00n\x00.\x00s\x00v\x00g\x00\x0c\x05\xc9\x15\xc7\x00d\x00a\x00t\x00a\x00b\x00a\x00s\x00e\x00.\x00s\x00v\x00g"
qt_resource_struct = b'\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x05\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x006\x00\x00\x00\x00\x00\x01\x00\x00\x01k\x00\x00\x01\x96\x9bo*`\x00\x00\x00\xaa\x00\x00\x00\x00\x00\x01\x00\x00\tO\x00\x00\x01\x96\x9bm\xdap\x00\x00\x00b\x00\x00\x00\x00\x00\x01\x00\x00\x05O\x00\x00\x01\x96\x9btq\xf0\x00\x00\x00\x8a\x00\x00\x00\x00\x00\x01\x00\x00\x06\xe9\x00\x00\x01\x96\xb5\xbd<@\x00\x00\x00\x16\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x01\x96\xb5\xa50\x00'
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
from qorzen.core.cloud_manager import CloudManager
from qorzen.core.config_manager import ConfigManager
from qorzen.core.database_manager import Base, DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.file_manager import FileManager
from qorzen.core.api_manager import APIManager
from qorzen.core.logging_manager import LoggingManager
from qorzen.core.monitoring_manager import ResourceMonitoringManager
from qorzen.core.plugin_manager import PluginManager
from qorzen.core.remote_manager import RemoteServicesManager
from qorzen.core.security_manager import SecurityManager
from qorzen.core.thread_manager import ThreadManager
```

#### Module: api_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/api_manager.py`

**Imports:**
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

**Global Variables:**
```python
fastapi = None
FastAPI =     FastAPI = object
APIRouter =     APIRouter = object
BaseModel =     BaseModel = object
Field =     Field = lambda *args, **kwargs: None  # noqa
```

**Classes:**
```python
class APIManager(QorzenManager):
    """Manages the REST API for Qorzen.

The API Manager is responsible for setting up and running the REST API server, registering API endpoints, and handling authentication and authorization for API requests. It uses FastAPI to provide a modern, high-performance API with automatic documentation."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, security_manager, event_bus_manager, thread_manager, registry) -> None:
        """Initialize the API Manager.

Args: config_manager: The Configuration Manager for API settings. logger_manager: The Logging Manager for logging. security_manager: The Security Manager for authentication and authorization. event_bus_manager: The Event Bus Manager for publishing API events. thread_manager: The Thread Manager for running the API server. registry: Optional registry of manager instances for API access."""
```
```python
    def initialize(self) -> None:
        """Initialize the API Manager.

Sets up the FastAPI application, registers API endpoints, and starts the server.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def register_api_endpoint(self, path, method, endpoint, tags, response_model, dependencies, summary, description) -> bool:
        """Register a custom API endpoint.

Args: path: The URL path for the endpoint. method: The HTTP method (GET, POST, etc.). endpoint: The function that handles the endpoint. tags: Optional list of tags for the endpoint. response_model: Optional Pydantic model for the response. dependencies: Optional list of dependencies for the endpoint. summary: Optional summary for the endpoint. description: Optional description for the endpoint.

Returns: bool: True if the endpoint was registered, False otherwise."""
```
```python
    def shutdown(self) -> None:
        """Shut down the API Manager.

Stops the API server and cleans up resources.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the API Manager.

Returns: Dict[str, Any]: Status information about the API Manager."""
```

```python
class AlertResponse(BaseModel):
    """Model for alert information response."""
```

```python
class PluginResponse(BaseModel):
    """Model for plugin information response."""
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
    """Model for token payload."""
```

```python
class UserCreate(BaseModel):
    """Model for user creation request body."""
```

```python
class UserLogin(BaseModel):
    """Model for user login request body."""
```

```python
class UserResponse(BaseModel):
    """Model for user information response."""
```

```python
class UserUpdate(BaseModel):
    """Model for user update request body."""
```

#### Module: app
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/app.py`

**Imports:**
```python
from __future__ import annotations
import atexit
import importlib
import signal
import sys
import traceback
from pathlib import Path
import logging
from typing import Any, Dict, List, Optional, Type, cast, Callable
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.ui.integration import MainWindowIntegration
from qorzen.core import ResourceMonitoringManager
from qorzen.core import APIManager
from qorzen.core import ConfigManager
from qorzen.core import EventBusManager
from qorzen.core import LoggingManager
from qorzen.core import ThreadManager
from qorzen.core import FileManager
from qorzen.core import DatabaseManager
from qorzen.core import PluginManager
from qorzen.core import RemoteServicesManager
from qorzen.core import SecurityManager
from qorzen.core import CloudManager
from qorzen.plugin_system.integration import IntegratedPluginInstaller
from qorzen.plugin_system.repository import PluginRepositoryManager
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.extension import extension_registry
from qorzen.plugin_system.lifecycle import set_logger as set_lifecycle_logger
from qorzen.utils.exceptions import ManagerInitializationError, QorzenError
```

**Global Variables:**
```python
logger = logger = logging.getLogger(__name__)
```

**Classes:**
```python
class ApplicationCore(object):
    """Core application class for Qorzen.

This class manages the lifecycle of the application, initializing and shutting down all managers and providing access to them."""
```
*Methods:*
```python
    def __init__(self, config_path) -> None:
        """Initialize the application core.  Args: config_path: Optional path to configuration file"""
```
```python
    def finalize_initialization(self):
```
```python
    def get_initialization_steps(self, progress_callback):
```
```python
    def get_manager(self, name) -> Optional[QorzenManager]:
        """Get a manager by name.  Args: name: Manager name  Returns: Manager instance or None if not found"""
```
```python
    def set_main_window(self, main_window) -> None:
        """Set the main window and publish UI ready event.  Args: main_window: Main window instance"""
```
```python
    def shutdown(self) -> None:
        """Shut down the application.  Shuts down all managers in reverse initialization order."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get application status.  Returns: Dictionary with status information"""
```

#### Module: base
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/base.py`

**Imports:**
```python
from __future__ import annotations
import abc
from typing import Any, Dict, Optional, Protocol, TypeVar, runtime_checkable
```

**Global Variables:**
```python
T = T = TypeVar("T", bound="BaseManager")
```

**Classes:**
```python
@runtime_checkable
class BaseManager(Protocol):
    """Protocol defining the interface that all managers must implement.

All core managers in Qorzen must adhere to this interface to ensure consistent initialization, status reporting, and lifecycle management."""
```
*Methods:*
```python
    def initialize(self) -> None:
        """Initialize the manager and its resources.

This method should be called after the manager is instantiated to set up any required resources, connections, or state. Managers should not perform heavy initialization in __init__ but should defer it to this method.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def shutdown(self) -> None:
        """Gracefully shut down the manager and release resources.

This method should properly close connections, stop threads, and release any resources held by the manager to prevent leaks or corruption.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Return the current status of the manager.

Returns: Dict[str, Any]: A dictionary containing status information such as: - 'name': The name of the manager - 'initialized': Whether the manager is properly initialized - 'healthy': Whether the manager is functioning correctly - Additional manager-specific status fields"""
```

```python
class QorzenManager(abc.ABC):
    """Abstract base class for all Qorzen managers.

This class provides a concrete implementation of common functionality that all managers should have, serving as a base class for specific managers."""
```
*Methods:*
```python
    def __init__(self, name) -> None:
        """Initialize the manager with a name.

Args: name: The name of the manager, used for logging and identification."""
```
```python
@property
    def healthy(self) -> bool:
        """Check if the manager is healthy.  Returns: bool: True if the manager is healthy, False otherwise."""
```
```python
@abc.abstractmethod
    def initialize(self) -> None:
        """Initialize the manager and its resources.

Implementations should set self._initialized to True when successful.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
@property
    def initialized(self) -> bool:
        """Check if the manager is initialized.

Returns: bool: True if the manager is initialized, False otherwise."""
```
```python
@property
    def name(self) -> str:
        """Get the name of the manager.  Returns: str: The manager name."""
```
```python
@abc.abstractmethod
    def shutdown(self) -> None:
        """Gracefully shut down the manager and release resources.

Implementations should set self._initialized to False when successful.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Return the current status of the manager.

Returns: Dict[str, Any]: A dictionary containing status information."""
```

#### Module: cloud_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/cloud_manager.py`

**Imports:**
```python
from __future__ import annotations
import abc
import importlib
import inspect
import os
import sys
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError
```

**Global Variables:**
```python
T = T = TypeVar("T")
```

**Classes:**
```python
class AWSStorageService(BaseCloudService):
    """AWS S3 storage service."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """Initialize the AWS S3 storage service.

Args: config: Configuration dictionary for the service. logger: Logger instance for the service."""
```
```python
    def delete_file(self, remote_path) -> bool:
        """Delete a file from S3.

Args: remote_path: Path to the file in S3.

Returns: bool: True if the deletion was successful, False otherwise."""
```
```python
    def download_file(self, remote_path, local_path) -> bool:
        """Download a file from S3.

Args: remote_path: Path to the file in S3. local_path: Path where the file should be stored locally.

Returns: bool: True if the download was successful, False otherwise."""
```
```python
    def initialize(self) -> None:
        """Initialize the AWS S3 storage service."""
```
```python
    def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """List files in an S3 directory.

Args: remote_path: Path to the directory in S3.

Returns: List[Dict[str, Any]]: List of file information dictionaries."""
```
```python
    def shutdown(self) -> None:
        """Shut down the AWS S3 storage service."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the AWS S3 storage service.

Returns: Dict[str, Any]: Status information about the AWS S3 storage service."""
```
```python
    def upload_file(self, local_path, remote_path) -> bool:
        """Upload a file to S3.

Args: local_path: Path to the local file to upload. remote_path: Path where the file should be stored in S3.

Returns: bool: True if the upload was successful, False otherwise."""
```

```python
class AzureBlobStorageService(BaseCloudService):
    """Azure Blob Storage service."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """Initialize the Azure Blob Storage service.

Args: config: Configuration dictionary for the service. logger: Logger instance for the service."""
```
```python
    def delete_file(self, remote_path) -> bool:
        """Delete a file from Azure Blob Storage.

Args: remote_path: Path to the file in Azure Blob Storage.

Returns: bool: True if the deletion was successful, False otherwise."""
```
```python
    def download_file(self, remote_path, local_path) -> bool:
        """Download a file from Azure Blob Storage.

Args: remote_path: Path to the file in Azure Blob Storage. local_path: Path where the file should be stored locally.

Returns: bool: True if the download was successful, False otherwise."""
```
```python
    def initialize(self) -> None:
        """Initialize the Azure Blob Storage service."""
```
```python
    def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """List files in an Azure Blob Storage directory.

Args: remote_path: Path to the directory in Azure Blob Storage.

Returns: List[Dict[str, Any]]: List of file information dictionaries."""
```
```python
    def shutdown(self) -> None:
        """Shut down the Azure Blob Storage service."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the Azure Blob Storage service.

Returns: Dict[str, Any]: Status information about the Azure Blob Storage service."""
```
```python
    def upload_file(self, local_path, remote_path) -> bool:
        """Upload a file to Azure Blob Storage.

Args: local_path: Path to the local file to upload. remote_path: Path where the file should be stored in Azure Blob Storage.

Returns: bool: True if the upload was successful, False otherwise."""
```

```python
class BaseCloudService(abc.ABC):
    """Base class for cloud services."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """Initialize the cloud service.

Args: config: Configuration dictionary for the service. logger: Logger instance for the service."""
```
```python
@abc.abstractmethod
    def initialize(self) -> None:
        """Initialize the cloud service."""
```
```python
@abc.abstractmethod
    def shutdown(self) -> None:
        """Shut down the cloud service."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the cloud service.

Returns: Dict[str, Any]: Status information about the cloud service."""
```

```python
class CloudManager(QorzenManager):
    """Manages cloud interactions and provides cloud-agnostic services.

The Cloud Manager is responsible for abstracting away cloud-specific details and providing a unified interface for cloud services like storage, databases, and messaging. It supports multiple cloud providers (AWS, Azure, GCP) and on-premise deployments."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, file_manager) -> None:
        """Initialize the Cloud Manager.

Args: config_manager: The Configuration Manager for cloud settings. logger_manager: The Logging Manager for logging. file_manager: Optional File Manager for local file operations."""
```
```python
    def delete_file(self, remote_path) -> bool:
        """Delete a file from cloud storage.

Args: remote_path: Path to the file in the cloud.

Returns: bool: True if the deletion was successful, False otherwise.

Raises: ValueError: If cloud storage is not enabled or initialized."""
```
```python
    def download_file(self, remote_path, local_path) -> bool:
        """Download a file from cloud storage.

Args: remote_path: Path to the file in the cloud. local_path: Path where the file should be stored locally.

Returns: bool: True if the download was successful, False otherwise.

Raises: ValueError: If cloud storage is not enabled or initialized."""
```
```python
    def get_cloud_provider(self) -> str:
        """Get the current cloud provider.  Returns: str: The current cloud provider (aws, azure, gcp, none)."""
```
```python
    def get_service(self, service_name) -> Optional[CloudService]:
        """Get a cloud service by name.

Args: service_name: The name of the service to get.

Returns: Optional[CloudService]: The cloud service, or None if not found."""
```
```python
    def get_storage_backend(self) -> str:
        """Get the current storage backend.

Returns: str: The current storage backend (local, s3, azure_blob, gcp_storage)."""
```
```python
    def initialize(self) -> None:
        """Initialize the Cloud Manager.

Sets up cloud services based on configuration.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def is_cloud_provider(self, provider) -> bool:
        """Check if the current cloud provider matches the specified provider.

Args: provider: The provider to check against (string or CloudProvider enum).

Returns: bool: True if the current provider matches, False otherwise."""
```
```python
    def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """List files in a cloud storage directory.

Args: remote_path: Path to the directory in the cloud.

Returns: List[Dict[str, Any]]: List of file information dictionaries.

Raises: ValueError: If cloud storage is not enabled or initialized."""
```
```python
    def shutdown(self) -> None:
        """Shut down the Cloud Manager.

Shuts down all cloud services and cleans up resources.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the Cloud Manager.

Returns: Dict[str, Any]: Status information about the Cloud Manager."""
```
```python
    def upload_file(self, local_path, remote_path) -> bool:
        """Upload a file to cloud storage.

Args: local_path: Path to the local file to upload. remote_path: Path where the file should be stored in the cloud.

Returns: bool: True if the upload was successful, False otherwise.

Raises: ValueError: If cloud storage is not enabled or initialized."""
```

```python
class CloudProvider(Enum):
    """Supported cloud providers."""
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
    def initialize(self) -> None:
        """Initialize the cloud service."""
```
```python
    def shutdown(self) -> None:
        """Shut down the cloud service."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the cloud service.

Returns: Dict[str, Any]: Status information about the cloud service."""
```

```python
class CloudStorageService(Protocol):
    """Protocol defining the interface for cloud storage services."""
```
*Methods:*
```python
    def delete_file(self, remote_path) -> bool:
        """Delete a file from cloud storage.

Args: remote_path: Path to the file in the cloud.

Returns: bool: True if the deletion was successful, False otherwise."""
```
```python
    def download_file(self, remote_path, local_path) -> bool:
        """Download a file from cloud storage.

Args: remote_path: Path to the file in the cloud. local_path: Path where the file should be stored locally.

Returns: bool: True if the download was successful, False otherwise."""
```
```python
    def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """List files in a cloud storage directory.

Args: remote_path: Path to the directory in the cloud.

Returns: List[Dict[str, Any]]: List of file information dictionaries."""
```
```python
    def upload_file(self, local_path, remote_path) -> bool:
        """Upload a file to cloud storage.

Args: local_path: Path to the local file to upload. remote_path: Path where the file should be stored in the cloud.

Returns: bool: True if the upload was successful, False otherwise."""
```

```python
class GCPStorageService(BaseCloudService):
    """Google Cloud Storage service."""
```
*Methods:*
```python
    def __init__(self, config, logger) -> None:
        """Initialize the Google Cloud Storage service.

Args: config: Configuration dictionary for the service. logger: Logger instance for the service."""
```
```python
    def delete_file(self, remote_path) -> bool:
        """Delete a file from GCP Storage.

Args: remote_path: Path to the file in GCP Storage.

Returns: bool: True if the deletion was successful, False otherwise."""
```
```python
    def download_file(self, remote_path, local_path) -> bool:
        """Download a file from GCP Storage.

Args: remote_path: Path to the file in GCP Storage. local_path: Path where the file should be stored locally.

Returns: bool: True if the download was successful, False otherwise."""
```
```python
    def initialize(self) -> None:
        """Initialize the Google Cloud Storage service."""
```
```python
    def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """List files in a GCP Storage directory.

Args: remote_path: Path to the directory in GCP Storage.

Returns: List[Dict[str, Any]]: List of file information dictionaries."""
```
```python
    def shutdown(self) -> None:
        """Shut down the Google Cloud Storage service."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the GCP Storage service.

Returns: Dict[str, Any]: Status information about the GCP Storage service."""
```
```python
    def upload_file(self, local_path, remote_path) -> bool:
        """Upload a file to GCP Storage.

Args: local_path: Path to the local file to upload. remote_path: Path where the file should be stored in GCP Storage.

Returns: bool: True if the upload was successful, False otherwise."""
```

```python
class LocalStorageService(BaseCloudService):
    """Local file system storage service."""
```
*Methods:*
```python
    def __init__(self, config, logger, file_manager) -> None:
        """Initialize the local storage service.

Args: config: Configuration dictionary for the service. logger: Logger instance for the service. file_manager: File Manager instance for file operations."""
```
```python
    def delete_file(self, remote_path) -> bool:
        """Delete a file from local storage.

Args: remote_path: Path to the file in local storage.

Returns: bool: True if the deletion was successful, False otherwise."""
```
```python
    def download_file(self, remote_path, local_path) -> bool:
        """Download a file from local storage.

Args: remote_path: Path to the file in local storage. local_path: Path where the file should be stored locally.

Returns: bool: True if the download was successful, False otherwise."""
```
```python
    def initialize(self) -> None:
        """Initialize the local storage service."""
```
```python
    def list_files(self, remote_path) -> List[Dict[(str, Any)]]:
        """List files in a local storage directory.

Args: remote_path: Path to the directory in local storage.

Returns: List[Dict[str, Any]]: List of file information dictionaries."""
```
```python
    def shutdown(self) -> None:
        """Shut down the local storage service."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the local storage service.

Returns: Dict[str, Any]: Status information about the local storage service."""
```
```python
    def upload_file(self, local_path, remote_path) -> bool:
        """Upload a file to local storage.

Args: local_path: Path to the local file to upload. remote_path: Path where the file should be stored in local storage.

Returns: bool: True if the upload was successful, False otherwise."""
```

```python
class StorageBackend(Enum):
    """Supported storage backends."""
```
*Class attributes:*
```python
LOCAL = 'local'
S3 = 's3'
AZURE_BLOB = 'azure_blob'
GCP_STORAGE = 'gcp_storage'
```

#### Module: config_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/config_manager.py`

**Imports:**
```python
from __future__ import annotations
import json
import os
import pathlib
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, Union
import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ConfigurationError, ManagerInitializationError
```

**Classes:**
```python
class ConfigManager(QorzenManager):
    """Manages application configuration loading, access, and updates.

The Configuration Manager is responsible for loading configuration from various sources (files, environment variables, defaults), providing access to configuration values, and handling dynamic configuration changes."""
```
*Methods:*
```python
    def __init__(self, config_path, env_prefix) -> None:
        """Initialize the Configuration Manager.

Args: config_path: Path to the configuration file. If None, the manager will look for a file at a default location or use only environment variables and defaults. env_prefix: Prefix for environment variables to consider for configuration."""
```
```python
    def get(self, key, default) -> Any:
        """Get a configuration value by its dot-notation key.

Args: key: The key to look up, in dot notation (e.g., "database.host"). default: Value to return if the key is not found.

Returns: Any: The configuration value, or the default if not found."""
```
```python
    def initialize(self) -> None:
        """Initialize the Configuration Manager.

Loads configuration from files and environment variables, validates it against the schema, and sets up file watchers.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def register_listener(self, key, callback) -> None:
        """Register a callback to be notified when a configuration value changes.

Args: key: The configuration key to watch (in dot notation). callback: A function to call when the value changes."""
```
```python
    def set(self, key, value) -> None:
        """Set a configuration value by its dot-notation key.

Args: key: The key to set, in dot notation (e.g., "database.host"). value: The value to set.

Raises: ConfigurationError: If the key is invalid or the value fails validation."""
```
```python
    def shutdown(self) -> None:
        """Shut down the Configuration Manager.  Saves the current configuration to file if needed."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the Configuration Manager.

Returns: Dict[str, Any]: Status information about the Configuration Manager."""
```
```python
    def unregister_listener(self, key, callback) -> None:
        """Unregister a configuration change listener.

Args: key: The configuration key being watched. callback: The callback function to remove."""
```

```python
class ConfigSchema(BaseModel):
    """Schema definition for the Qorzen configuration.

This class defines the structure and validation rules for the configuration. It uses Pydantic for validation and type checking."""
```
*Methods:*
```python
@model_validator(mode='after')
    def validate_api_port(self) -> 'ConfigSchema':
        """Ensure `api.port` is a valid integer."""
```
```python
@model_validator(mode='after')
    def validate_jwt_secret(self) -> 'ConfigSchema':
        """Validate that the JWT secret is set if API is enabled.

Returns: ConfigSchema: The validated model instance.

Raises: ValueError: If JWT secret is not set but API is enabled."""
```

#### Module: database_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/database_manager.py`

**Imports:**
```python
from __future__ import annotations
import contextlib
import functools
import threading
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, TypeVar, Union, cast
import sqlalchemy
from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import DatabaseError, ManagerInitializationError, ManagerShutdownError
```

**Global Variables:**
```python
T = T = TypeVar('T')
R = R = TypeVar('R')
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
class DatabaseConnection(object):
    """A database connection instance."""
```
*Methods:*
```python
    def __init__(self, config) -> None:
        """Initialize a database connection.  Args: config: The connection configuration"""
```

```python
class DatabaseConnectionConfig(object):
    """Configuration for a database connection."""
```
*Methods:*
```python
    def __init__(self, name, db_type, host, port, database, user, password, pool_size, max_overflow, pool_recycle, echo) -> None:
        """Initialize database connection configuration.

Args: name: The name of the connection db_type: The database type (postgresql, mysql, sqlite, etc.) host: The database host port: The database port database: The database name user: The database user password: The database password pool_size: The connection pool size max_overflow: The maximum overflow connections pool_recycle: The connection recycle time in seconds echo: Whether to echo SQL statements"""
```

```python
class DatabaseManager(QorzenManager):
    """Manager for database connections and operations."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager) -> None:
        """Initialize the database manager.

Args: config_manager: The configuration manager logger_manager: The logger manager"""
```
```python
    async def async_session(self, connection_name) -> AsyncSession:
        """Get an async database session.

Args: connection_name: The name of the connection to use, or None for the default

Returns: An async SQLAlchemy session

Raises: DatabaseError: If there's an error getting the session"""
```
```python
    def check_connection(self, connection_name) -> bool:
        """Check if a database connection is healthy.

Args: connection_name: The name of the connection to check, or None for the default

Returns: True if the connection is healthy, False otherwise"""
```
```python
    def create_tables(self, connection_name) -> None:
        """Create database tables for the Base metadata.

Args: connection_name: The name of the connection to use, or None for the default

Raises: DatabaseError: If there's an error creating the tables"""
```
```python
    async def create_tables_async(self, connection_name) -> None:
        """Create database tables for the Base metadata asynchronously.

Args: connection_name: The name of the connection to use, or None for the default

Raises: DatabaseError: If there's an error creating the tables"""
```
```python
    def execute(self, statement, connection_name) -> List[Dict[(str, Any)]]:
        """Execute a database statement.

Args: statement: The statement to execute connection_name: The name of the connection to use, or None for the default

Returns: A list of result rows as dictionaries

Raises: DatabaseError: If there's an error executing the statement"""
```
```python
    async def execute_async(self, statement, connection_name) -> List[Dict[(str, Any)]]:
        """Execute a database statement asynchronously.

Args: statement: The statement to execute connection_name: The name of the connection to use, or None for the default

Returns: A list of result rows as dictionaries

Raises: DatabaseError: If there's an error executing the statement"""
```
```python
    def execute_raw(self, sql, params, connection_name) -> List[Dict[(str, Any)]]:
        """Execute a raw SQL statement.

Args: sql: The SQL statement to execute params: Parameters for the statement connection_name: The name of the connection to use, or None for the default

Returns: A list of result rows as dictionaries

Raises: DatabaseError: If there's an error executing the statement"""
```
```python
    def get_async_engine(self, connection_name) -> Optional[AsyncEngine]:
        """Get the async database engine for a connection.

Args: connection_name: The name of the connection, or None for the default

Returns: The async database engine, or None if not available"""
```
```python
    def get_connection_names(self) -> List[str]:
        """Get the names of all registered connections.  Returns: A list of connection names"""
```
```python
    def get_engine(self, connection_name) -> Optional[Engine]:
        """Get the database engine for a connection.

Args: connection_name: The name of the connection, or None for the default

Returns: The database engine, or None if not available"""
```
```python
    def has_connection(self, name) -> bool:
        """Check if a connection exists.

Args: name: The name of the connection to check

Returns: True if the connection exists, False otherwise"""
```
```python
    def initialize(self) -> None:
        """Initialize the database manager."""
```
```python
    def register_connection(self, config) -> None:
        """Register a new database connection.

Args: config: The connection configuration

Raises: DatabaseError: If there's an error registering the connection"""
```
```python
@contextlib.contextmanager
    def session(self, connection_name) -> Generator[(Session, None, None)]:
        """Get a database session.

Args: connection_name: The name of the connection to use, or None for the default

Yields: A SQLAlchemy session

Raises: DatabaseError: If there's an error getting the session"""
```
```python
    def shutdown(self) -> None:
        """Shut down the database manager."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the database manager.  Returns: A dictionary with status information"""
```
```python
    def unregister_connection(self, name) -> bool:
        """Unregister a database connection.

Args: name: The name of the connection to unregister

Returns: True if the connection was unregistered, False otherwise

Raises: DatabaseError: If attempting to unregister the default connection"""
```

#### Module: event_bus_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/event_bus_manager.py`

**Imports:**
```python
from __future__ import annotations
import concurrent.futures
import queue
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import Event, EventSubscription, EventHandler, EventType
from qorzen.utils.exceptions import EventBusError, ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
class EventBusManager(QorzenManager):
    """Manager for the application event bus.

This manager handles event publishing and subscription, allowing components to communicate via a pub/sub pattern."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, thread_manager) -> None:
        """Initialize the event bus manager.

Args: config_manager: Configuration manager logger_manager: Logger manager"""
```
```python
    def initialize(self) -> None:
        """Initialize the event bus manager.  Raises: ManagerInitializationError: If initialization fails"""
```
```python
    def publish(self, event_type, source, payload, correlation_id, synchronous) -> str:
        """Publish an event to the event bus.

Args: event_type: Type of the event (enum or string) source: Source of the event payload: Event payload data correlation_id: ID for tracking related events synchronous: If True, process event synchronously

Returns: The event ID

Raises: EventBusError: If the event cannot be published"""
```
```python
    def shutdown(self) -> None:
        """Shut down the event bus manager.  Raises: ManagerShutdownError: If shutdown fails"""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the event bus manager.  Returns: Dictionary with status information"""
```
```python
    def subscribe(self, event_type, callback, subscriber_id, filter_criteria) -> str:
        """Subscribe to events.

Args: event_type: Type of events to subscribe to callback: Function to call when an event occurs subscriber_id: Optional ID for the subscriber filter_criteria: Optional criteria to filter events

Returns: The subscriber ID

Raises: EventBusError: If subscription fails"""
```
```python
    def unsubscribe(self, subscriber_id, event_type) -> bool:
        """Unsubscribe from events.

Args: subscriber_id: The subscriber ID to unsubscribe event_type: Optional event type to unsubscribe from

Returns: True if unsubscribed successfully, False otherwise"""
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
import hashlib
import os
import pathlib
import shutil
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import FileError, ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
@dataclass
class FileInfo(object):
    """Information about a file."""
```

```python
class FileManager(QorzenManager):
    """Manages file system interactions for the application.

The File Manager is responsible for handling file system operations such as reading, writing, and managing directories. It provides a standardized way for other components to interact with the file system and ensures proper error handling, locking, and organization of files."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager) -> None:
        """Initialize the File Manager.

Args: config_manager: The Configuration Manager to use for file settings. logger_manager: The Logging Manager to use for logging."""
```
```python
    def compute_file_hash(self, path, directory_type) -> str:
        """Compute the SHA-256 hash of a file's contents.

Args: path: The path to the file. directory_type: The type of directory to use as the base.

Returns: str: The hexadecimal hash of the file.

Raises: FileError: If the hash cannot be computed."""
```
```python
    def copy_file(self, source_path, dest_path, source_dir_type, dest_dir_type, overwrite) -> None:
        """Copy a file from one location to another.

Args: source_path: The path to the source file. dest_path: The path to the destination file. source_dir_type: The type of directory to use as the base for the source. dest_dir_type: The type of directory to use as the base for the destination. overwrite: Whether to overwrite the destination file if it exists.

Raises: FileError: If the file cannot be copied."""
```
```python
    def create_backup(self, path, directory_type) -> str:
        """Create a backup of a file in the backup directory.

Args: path: The path to the file to back up. directory_type: The type of directory to use as the base.

Returns: str: The path to the backup file, relative to the backup directory.

Raises: FileError: If the backup cannot be created."""
```
```python
    def create_temp_file(self, prefix, suffix) -> Tuple[(str, BinaryIO)]:
        """Create a temporary file in the temp directory.

Args: prefix: Optional prefix for the filename. suffix: Optional suffix for the filename.

Returns: Tuple[str, BinaryIO]: The path to the temp file and an open file object.

Raises: FileError: If the temporary file cannot be created."""
```
```python
    def delete_file(self, path, directory_type) -> None:
        """Delete a file.

Args: path: The path to the file, relative to the specified directory. directory_type: The type of directory to use as the base.

Raises: FileError: If the file cannot be deleted."""
```
```python
    def ensure_directory(self, path, directory_type) -> pathlib.Path:
        """Ensure that a directory exists, creating it if necessary.

Args: path: The path to the directory, relative to the specified directory. directory_type: The type of directory to use as the base. One of: "base", "temp", "plugin_data", "backup".

Returns: pathlib.Path: The absolute path to the directory.

Raises: FileError: If the directory cannot be created."""
```
```python
    def get_file_info(self, path, directory_type) -> FileInfo:
        """Get information about a file.

Args: path: The path to the file, relative to the specified directory. directory_type: The type of directory to use as the base.

Returns: FileInfo: Information about the file.

Raises: FileError: If the file information cannot be retrieved."""
```
```python
    def get_file_path(self, path, directory_type) -> pathlib.Path:
        """Get the absolute path for a file, relative to a specified directory.

Args: path: The path to the file, relative to the specified directory. directory_type: The type of directory to use as the base. One of: "base", "temp", "plugin_data", "backup".

Returns: pathlib.Path: The absolute path to the file.

Raises: FileError: If the directory type is invalid or the manager is not initialized."""
```
```python
    def initialize(self) -> None:
        """Initialize the File Manager.

Creates necessary directories and sets up file paths based on configuration.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def list_files(self, path, directory_type, recursive, include_dirs, pattern) -> List[FileInfo]:
        """List files in a directory.

Args: path: The path to the directory, relative to the specified directory. directory_type: The type of directory to use as the base. recursive: Whether to list files in subdirectories recursively. include_dirs: Whether to include directories in the results. pattern: Optional glob pattern to filter files by name.

Returns: List[FileInfo]: Information about the files in the directory.

Raises: FileError: If the directory cannot be listed."""
```
```python
    def move_file(self, source_path, dest_path, source_dir_type, dest_dir_type, overwrite) -> None:
        """Move a file from one location to another.

Args: source_path: The path to the source file. dest_path: The path to the destination file. source_dir_type: The type of directory to use as the base for the source. dest_dir_type: The type of directory to use as the base for the destination. overwrite: Whether to overwrite the destination file if it exists.

Raises: FileError: If the file cannot be moved."""
```
```python
    def read_binary(self, path, directory_type) -> bytes:
        """Read binary data from a file.

Args: path: The path to the file, relative to the specified directory. directory_type: The type of directory to use as the base.

Returns: bytes: The binary content of the file.

Raises: FileError: If the file cannot be read."""
```
```python
    def read_text(self, path, directory_type) -> str:
        """Read text from a file.

Args: path: The path to the file, relative to the specified directory. directory_type: The type of directory to use as the base.

Returns: str: The text content of the file.

Raises: FileError: If the file cannot be read."""
```
```python
    def shutdown(self) -> None:
        """Shut down the File Manager.

Clears file locks and cleans up resources.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the File Manager.

Returns: Dict[str, Any]: Status information about the File Manager."""
```
```python
    def write_binary(self, path, content, directory_type, create_dirs) -> None:
        """Write binary data to a file.

Args: path: The path to the file, relative to the specified directory. content: The binary content to write. directory_type: The type of directory to use as the base. create_dirs: Whether to create parent directories if they don't exist.

Raises: FileError: If the file cannot be written."""
```
```python
    def write_text(self, path, content, directory_type, create_dirs) -> None:
        """Write text to a file.

Args: path: The path to the file, relative to the specified directory. content: The text content to write. directory_type: The type of directory to use as the base. create_dirs: Whether to create parent directories if they don't exist.

Raises: FileError: If the file cannot be written."""
```

```python
class FileType(Enum):
    """Types of files that the File Manager can handle."""
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
import logging
import logging.handlers
import os
import pathlib
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, cast
import structlog
from pythonjsonlogger import jsonlogger
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, EventBusError
```

**Classes:**
```python
class EventBusLogHandler(logging.Handler):
```
*Methods:*
```python
    def __init__(self, event_bus_manager):
```
```python
    def emit(self, record):
```

```python
class ExcludeLoggerFilter(logging.Filter):
```
*Methods:*
```python
    def __init__(self, excluded_logger_name):
```
```python
    def filter(self, record):
```

```python
class LoggingManager(QorzenManager):
    """Manages application logging configuration and access.

The Logging Manager provides a unified logging interface for all components in the Qorzen system. It configures Python's logging module with appropriate handlers based on configuration, and provides methods for components to obtain loggers specialized for their domain."""
```
*Class attributes:*
```python
LOG_LEVELS =     LOG_LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
```
*Methods:*
```python
    def __init__(self, config_manager) -> None:
        """Initialize the Logging Manager.

Args: config_manager: The Configuration Manager to use for logging settings."""
```
```python
    def get_logger(self, name) -> Union[(logging.Logger, Any)]:
        """Get a logger for a specific component.

Args: name: The name of the component requesting a logger.

Returns: Union[logging.Logger, Any]: A logger instance configured for the component. If structlog is enabled, returns a structured logger."""
```
```python
    def initialize(self) -> None:
        """Initialize the Logging Manager.

Sets up logging based on the configuration, creating handlers for console, file, database, and ELK as configured.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def set_event_bus_manager(self, event_bus_manager):
```
```python
    def shutdown(self) -> None:
        """Shut down the Logging Manager.

Closes all log handlers and performs any necessary cleanup.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the Logging Manager.

Returns: Dict[str, Any]: Status information about the Logging Manager."""
```

#### Module: monitoring_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/monitoring_manager.py`

**Imports:**
```python
from __future__ import annotations
import datetime
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
import psutil
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
from qorzen.core.base import QorzenManager
from qorzen.core.thread_manager import TaskProgressReporter, ThreadExecutionContext
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError
```

**Classes:**
```python
@dataclass
class Alert(object):
    """Represents a monitoring alert."""
```

```python
class AlertLevel(Enum):
    """Alert severity levels."""
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
    """Manages monitoring of system resources and application metrics.

The Resource Monitoring Manager is responsible for collecting and exposing metrics about system resources (CPU, memory, disk) and application-specific metrics. It provides integrations with Prometheus for metrics collection and can generate alerts when metrics exceed defined thresholds."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, event_bus_manager, thread_manager) -> None:
        """Initialize the Resource Monitoring Manager.

Args: config_manager: The Configuration Manager for settings. logger_manager: The Logging Manager for logging. event_bus_manager: The Event Bus Manager for publishing alerts. thread_manager: The Thread Manager for scheduling metric collection."""
```
```python
    def generate_diagnostic_report(self) -> Dict[(str, Any)]:
        """Generate a diagnostic report with system and application metrics.

Returns: Dict[str, Any]: A diagnostic report with current metrics and status."""
```
```python
    def get_alerts(self, include_resolved, level, metric_name) -> List[Dict[(str, Any)]]:
        """Get active alerts, optionally filtered.

Args: include_resolved: Whether to include resolved alerts. level: Optional filter by alert level. metric_name: Optional filter by metric name.

Returns: List[Dict[str, Any]]: List of alert information dictionaries."""
```
```python
    def initialize(self) -> None:
        """Initialize the Resource Monitoring Manager.

Starts the Prometheus HTTP server and sets up metric collection tasks.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def register_counter(self, name, description, labels) -> Any:
        """Register a new counter metric.

Args: name: The name of the metric. description: Description of what the metric measures. labels: Optional list of label names for the metric.

Returns: Any: The Prometheus counter object.

Raises: ValueError: If the metric name is already registered."""
```
```python
    def register_gauge(self, name, description, labels) -> Any:
        """Register a new gauge metric.

Args: name: The name of the metric. description: Description of what the metric measures. labels: Optional list of label names for the metric.

Returns: Any: The Prometheus gauge object.

Raises: ValueError: If the metric name is already registered."""
```
```python
    def register_histogram(self, name, description, labels, buckets) -> Any:
        """Register a new histogram metric.

Args: name: The name of the metric. description: Description of what the metric measures. labels: Optional list of label names for the metric. buckets: Optional list of bucket boundaries.

Returns: Any: The Prometheus histogram object.

Raises: ValueError: If the metric name is already registered."""
```
```python
    def register_summary(self, name, description, labels) -> Any:
        """Register a new summary metric.

Args: name: The name of the metric. description: Description of what the metric measures. labels: Optional list of label names for the metric.

Returns: Any: The Prometheus summary object.

Raises: ValueError: If the metric name is already registered."""
```
```python
    def shutdown(self) -> None:
        """Shut down the Resource Monitoring Manager.

Stops metrics collection and cleans up resources.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the Resource Monitoring Manager.

Returns: Dict[str, Any]: Status information about the Resource Monitoring Manager."""
```

#### Module: plugin_error_handler
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/plugin_error_handler.py`

**Imports:**
```python
from __future__ import annotations
import logging
import sys
import traceback
import threading
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox
from qorzen.core.event_model import Event, EventType
from qorzen.plugin_system.lifecycle import get_plugin_state, set_plugin_state, PluginLifecycleState
```

**Classes:**
```python
class PluginErrorHandler(QObject):
    """Handler for plugin errors.

This class intercepts and handles errors from plugins, providing proper error reporting and recovery mechanisms."""
```
*Class attributes:*
```python
pluginError =     pluginError = Signal(str, str, object, str)  # plugin_name, error_message, severity, traceback
pluginReloadRequested =     pluginReloadRequested = Signal(str)  # plugin_name
```
*Methods:*
```python
    def __init__(self, event_bus_manager, plugin_manager, parent) -> None:
        """Initialize the plugin error handler.

Args: event_bus_manager: The event bus manager. plugin_manager: The plugin manager. parent: The parent QObject."""
```
```python
    def cleanup(self) -> None:
        """Clean up resources."""
```
```python
    def clear_plugin_errors(self, plugin_name) -> None:
        """Clear plugin errors.

Args: plugin_name: The name of the plugin to clear errors for, or None for all."""
```
```python
    def get_plugin_errors(self, plugin_name) -> Dict[(str, List[Dict[(str, Any)]])]:
        """Get plugin errors.

Args: plugin_name: The name of the plugin to get errors for, or None for all.

Returns: Dictionary of plugin name to list of error dictionaries."""
```

```python
class PluginErrorSeverity(Enum):
    """Severity levels for plugin errors."""
```
*Class attributes:*
```python
LOW =     LOW = auto()
MEDIUM =     MEDIUM = auto()
HIGH =     HIGH = auto()
CRITICAL =     CRITICAL = auto()
```

#### Module: plugin_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/plugin_manager.py`

**Imports:**
```python
from __future__ import annotations
import importlib
import importlib.metadata
import importlib.util
import inspect
import os
import pathlib
import pkgutil
import sys
import threading
import time
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType, Event
from qorzen.core.thread_manager import ThreadExecutionContext, TaskProgressReporter
from qorzen.ui.integration import UIIntegration, MainWindowIntegration
from qorzen.plugin_system.interface import PluginInterface
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook
from qorzen.plugin_system.lifecycle import execute_hook, set_logger as set_lifecycle_logger, get_lifecycle_manager, register_ui_integration, cleanup_ui, get_plugin_state, set_plugin_state, PluginLifecycleState, wait_for_ui_ready, signal_ui_ready, set_thread_manager
from qorzen.plugin_system.extension import register_plugin_extensions, unregister_plugin_extensions, extension_registry
from qorzen.plugin_system.config_schema import ConfigSchema
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, PluginError
```

**Classes:**
```python
@dataclass
class PluginInfo(object):
    """Information about a plugin."""
```
*Methods:*
```python
    def __post_init__(self) -> None:
```

```python
class PluginManager(QorzenManager):
    """Manager for discovering, loading, and managing plugins."""
```
*Methods:*
```python
    def __init__(self, application_core, config_manager, logger_manager, event_bus_manager, file_manager, thread_manager, database_manager, remote_service_manager, security_manager, api_manager, cloud_manager) -> None:
        """Initialize the plugin manager."""
```
```python
    def disable_plugin(self, plugin_name) -> bool:
        """Disable a plugin."""
```
```python
    def enable_plugin(self, plugin_name) -> bool:
        """Enable a plugin."""
```
```python
    def get_all_plugins(self) -> Dict[(str, PluginInfo)]:
        """Get all discovered plugins."""
```
```python
    def initialize(self) -> None:
        """Initialize the plugin manager."""
```
```python
    def install_plugin(self, package_path, force, skip_verification, enable, resolve_dependencies, install_dependencies) -> bool:
        """Install a plugin package."""
```
```python
    def load_plugin(self, plugin_name) -> bool:
        """Load a plugin."""
```
```python
    def reload_plugin(self, plugin_name) -> bool:
        """Reload a plugin."""
```
```python
    def shutdown(self) -> None:
        """Shut down the plugin manager."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get plugin manager status."""
```
```python
    def uninstall_plugin(self, plugin_name, keep_data, check_dependents) -> bool:
        """Uninstall a plugin."""
```
```python
    def unload_plugin(self, plugin_name) -> bool:
        """Unload a plugin."""
```
```python
    def update_plugin(self, package_path, skip_verification, resolve_dependencies, install_dependencies) -> bool:
        """Update a plugin."""
```

```python
class PluginState(str, Enum):
    """Legacy plugin states used for backward compatibility."""
```
*Class attributes:*
```python
DISCOVERED = 'discovered'
LOADED = 'loaded'
ACTIVE = 'active'
INACTIVE = 'inactive'
FAILED = 'failed'
DISABLED = 'disabled'
```

#### Module: remote_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/remote_manager.py`

**Imports:**
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

**Classes:**
```python
class AsyncHTTPService(RemoteService):
    """Asynchronous HTTP/HTTPS remote service implementation."""
```
*Methods:*
```python
    def __init__(self, name, base_url, protocol, **kwargs) -> None:
        """Initialize an async HTTP service.

Args: name: Unique name of the service. base_url: Base URL of the service. protocol: The protocol (HTTP or HTTPS). **kwargs: Additional arguments passed to RemoteService."""
```
```python
    def check_health(self) -> bool:
        """Check if the service is healthy.  Returns: bool: True if the service is healthy, False otherwise."""
```
```python
    async def check_health_async(self) -> bool:
        """Check if the service is healthy asynchronously.

Returns: bool: True if the service is healthy, False otherwise."""
```
```python
    def close(self) -> None:
        """Close the async HTTP client."""
```
```python
    async def close_async(self) -> None:
        """Close the async HTTP client."""
```
```python
    async def delete(self, path, **kwargs) -> httpx.Response:
        """Make a DELETE request to the service asynchronously.

Args: path: Path relative to the base URL. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
    async def get(self, path, params, **kwargs) -> httpx.Response:
        """Make a GET request to the service asynchronously.

Args: path: Path relative to the base URL. params: Query parameters. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
    async def patch(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Make a PATCH request to the service asynchronously.

Args: path: Path relative to the base URL. data: Request body data. json_data: JSON request body. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
    async def post(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Make a POST request to the service asynchronously.

Args: path: Path relative to the base URL. data: Request body data. json_data: JSON request body. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
    async def put(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Make a PUT request to the service asynchronously.

Args: path: Path relative to the base URL. data: Request body data. json_data: JSON request body. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
@retry(retry=retry_if_exception_type(httpx.HTTPError), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def request(self, method, path, params, data, json_data, headers, timeout) -> httpx.Response:
        """Make an HTTP request to the service asynchronously.

Args: method: HTTP method (GET, POST, etc.). path: Path relative to the base URL. params: Query parameters. data: Request body data. json_data: JSON request body. headers: Additional headers for this request. timeout: Request timeout in seconds (overrides default).

Returns: httpx.Response: The HTTP response.

Raises: httpx.HTTPError: If the request fails."""
```

```python
class HTTPService(RemoteService):
    """HTTP/HTTPS remote service implementation."""
```
*Methods:*
```python
    def __init__(self, name, base_url, protocol, **kwargs) -> None:
        """Initialize an HTTP service.

Args: name: Unique name of the service. base_url: Base URL of the service. protocol: The protocol (HTTP or HTTPS). **kwargs: Additional arguments passed to RemoteService."""
```
```python
    def check_health(self) -> bool:
        """Check if the service is healthy.  Returns: bool: True if the service is healthy, False otherwise."""
```
```python
    def close(self) -> None:
        """Close the HTTP client."""
```
```python
    def delete(self, path, **kwargs) -> httpx.Response:
        """Make a DELETE request to the service.

Args: path: Path relative to the base URL. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
    def get(self, path, params, **kwargs) -> httpx.Response:
        """Make a GET request to the service.

Args: path: Path relative to the base URL. params: Query parameters. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
    def patch(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Make a PATCH request to the service.

Args: path: Path relative to the base URL. data: Request body data. json_data: JSON request body. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
    def post(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Make a POST request to the service.

Args: path: Path relative to the base URL. data: Request body data. json_data: JSON request body. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
    def put(self, path, data, json_data, **kwargs) -> httpx.Response:
        """Make a PUT request to the service.

Args: path: Path relative to the base URL. data: Request body data. json_data: JSON request body. **kwargs: Additional arguments passed to request().

Returns: httpx.Response: The HTTP response."""
```
```python
@retry(retry=retry_if_exception_type(httpx.HTTPError), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def request(self, method, path, params, data, json_data, headers, timeout) -> httpx.Response:
        """Make an HTTP request to the service.

Args: method: HTTP method (GET, POST, etc.). path: Path relative to the base URL. params: Query parameters. data: Request body data. json_data: JSON request body. headers: Additional headers for this request. timeout: Request timeout in seconds (overrides default).

Returns: httpx.Response: The HTTP response.

Raises: httpx.HTTPError: If the request fails."""
```

```python
class RemoteService(object):
    """Base class for remote services."""
```
*Methods:*
```python
    def __init__(self, name, protocol, base_url, timeout, max_retries, retry_delay, retry_max_delay, headers, auth, config, logger) -> None:
        """Initialize a remote service.

Args: name: Unique name of the service. protocol: The protocol used to communicate with the service. base_url: Base URL of the service. timeout: Request timeout in seconds. max_retries: Maximum number of retry attempts for failed requests. retry_delay: Initial delay between retries in seconds. retry_max_delay: Maximum delay between retries in seconds. headers: Default headers to include in requests. auth: Authentication configuration. config: Additional service-specific configuration. logger: Logger instance for the service."""
```
```python
    def check_health(self) -> bool:
        """Check if the service is healthy.  Returns: bool: True if the service is healthy, False otherwise."""
```
```python
    def get_client(self) -> Any:
        """Get the client instance for this service.  Returns: Any: The client instance."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the service.  Returns: Dict[str, Any]: Status information."""
```

```python
class RemoteServicesManager(QorzenManager):
    """Manages integration with external or remote services.

The Remote Services Manager is responsible for handling interactions with external services and APIs. It provides a unified interface for making requests to remote services, handles authentication, retries, and circuit breaking, and monitors the health of connected services."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, event_bus_manager, thread_manager) -> None:
        """Initialize the Remote Services Manager.

Args: config_manager: The Configuration Manager for service settings. logger_manager: The Logging Manager for logging. event_bus_manager: The Event Bus Manager for service events. thread_manager: The Thread Manager for service-related background tasks."""
```
```python
    def check_all_services_health(self) -> Dict[(str, bool)]:
        """Check the health of all registered services.

Returns: Dict[str, bool]: Dictionary of service name to health status."""
```
```python
    def check_service_health(self, service_name) -> bool:
        """Check the health of a specific service.

Args: service_name: Name of the service to check.

Returns: bool: True if the service is healthy, False otherwise."""
```
```python
    def get_all_services(self) -> Dict[(str, RemoteService)]:
        """Get all registered services.

Returns: Dict[str, RemoteService]: Dictionary of service name to service."""
```
```python
    def get_async_http_service(self, service_name) -> Optional[AsyncHTTPService]:
        """Get a registered async HTTP service by name.

Args: service_name: Name of the service.

Returns: Optional[AsyncHTTPService]: The async HTTP service, or None if not found or not an async HTTP service."""
```
```python
    def get_http_service(self, service_name) -> Optional[HTTPService]:
        """Get a registered HTTP service by name.

Args: service_name: Name of the service.

Returns: Optional[HTTPService]: The HTTP service, or None if not found or not an HTTP service."""
```
```python
    def get_service(self, service_name) -> Optional[RemoteService]:
        """Get a registered service by name.

Args: service_name: Name of the service.

Returns: Optional[RemoteService]: The service, or None if not found."""
```
```python
    def initialize(self) -> None:
        """Initialize the Remote Services Manager.

Sets up remote services based on configuration.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def make_request(self, service_name, method, path, **kwargs) -> Any:
        """Make a request to a remote service.

Args: service_name: Name of the service to call. method: HTTP method (GET, POST, etc.). path: Path relative to the service base URL. **kwargs: Additional arguments for the request.

Returns: Any: The response from the service.

Raises: ValueError: If the service is not found or the request fails."""
```
```python
    async def make_request_async(self, service_name, method, path, **kwargs) -> Any:
        """Make an asynchronous request to a remote service.

Args: service_name: Name of the service to call. method: HTTP method (GET, POST, etc.). path: Path relative to the service base URL. **kwargs: Additional arguments for the request.

Returns: Any: The response from the service.

Raises: ValueError: If the service is not found or the request fails."""
```
```python
    def register_service(self, service) -> None:
        """Register a remote service.

Args: service: The service to register.

Raises: ValueError: If a service with the same name is already registered."""
```
```python
    def shutdown(self) -> None:
        """Shut down the Remote Services Manager.

Closes connections to all remote services and cleans up resources.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the Remote Services Manager.

Returns: Dict[str, Any]: Status information about the Remote Services Manager."""
```
```python
    def unregister_service(self, service_name) -> bool:
        """Unregister a remote service.

Args: service_name: Name of the service to unregister.

Returns: bool: True if the service was unregistered, False otherwise."""
```

```python
class ServiceProtocol(Enum):
    """Supported service protocols."""
```
*Class attributes:*
```python
HTTP = 'http'
HTTPS = 'https'
GRPC = 'grpc'
SOAP = 'soap'
CUSTOM = 'custom'
```

#### Module: security_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/security_manager.py`

**Imports:**
```python
from __future__ import annotations
import datetime
import hashlib
import os
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
import jwt
from passlib.context import CryptContext
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, SecurityError
```

**Classes:**
```python
@dataclass
class AuthToken(object):
    """Represents an authentication token."""
```

```python
@dataclass
class Permission(object):
    """Represents a system permission that can be granted to roles."""
```

```python
class SecurityManager(QorzenManager):
    """Manages authentication, authorization, and security features.

The Security Manager handles user authentication, role-based access control (RBAC), token management, and other security-related functionality for the Qorzen system."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager, event_bus_manager, db_manager) -> None:
        """Initialize the Security Manager.

Args: config_manager: The Configuration Manager for security settings. logger_manager: The Logging Manager for logging. event_bus_manager: The Event Bus Manager for security events. db_manager: Optional Database Manager for persistent storage."""
```
```python
    def authenticate_user(self, username_or_email, password) -> Optional[Dict[(str, Any)]]:
        """Authenticate a user with username/email and password.

Args: username_or_email: User's login name or email address. password: User's password.

Returns: Optional[Dict[str, Any]]: User information and tokens if authentication succeeds, None if authentication fails."""
```
```python
    def create_user(self, username, email, password, roles, metadata) -> Optional[str]:
        """Create a new user.

Args: username: User's login name. email: User's email address. password: User's password. roles: List of roles to assign to the user. metadata: Optional additional user metadata.

Returns: Optional[str]: The ID of the created user, or None if creation failed.

Raises: SecurityError: If the user cannot be created."""
```
```python
    def delete_user(self, user_id) -> bool:
        """Delete a user.

Args: user_id: The ID of the user to delete.

Returns: bool: True if the user was deleted, False otherwise.

Raises: SecurityError: If the deletion fails."""
```
```python
    def get_all_permissions(self) -> List[Dict[(str, Any)]]:
        """Get information about all permissions.

Returns: List[Dict[str, Any]]: List of permission information dictionaries."""
```
```python
    def get_all_users(self) -> List[Dict[(str, Any)]]:
        """Get information about all users.

Returns: List[Dict[str, Any]]: List of user information dictionaries."""
```
```python
    def get_user_info(self, user_id) -> Optional[Dict[(str, Any)]]:
        """Get information about a user.

Args: user_id: The ID of the user to get information for.

Returns: Optional[Dict[str, Any]]: Information about the user, or None if the user is not found."""
```
```python
    def has_permission(self, user_id, resource, action) -> bool:
        """Check if a user has permission to perform an action on a resource.

Args: user_id: The ID of the user to check. resource: The resource to check permission for. action: The action to check permission for.

Returns: bool: True if the user has permission, False otherwise."""
```
```python
    def has_role(self, user_id, role) -> bool:
        """Check if a user has a specific role.

Args: user_id: The ID of the user to check. role: The role to check for.

Returns: bool: True if the user has the role, False otherwise."""
```
```python
    def initialize(self) -> None:
        """Initialize the Security Manager.

Sets up security configurations, creates default users and permissions if needed.

Raises: ManagerInitializationError: If initialization fails."""
```
```python
    def refresh_token(self, refresh_token) -> Optional[Dict[(str, Any)]]:
        """Generate a new access token using a refresh token.

Args: refresh_token: The refresh token to use for generating a new access token.

Returns: Optional[Dict[str, Any]]: New access token info, or None if token is invalid."""
```
```python
    def revoke_token(self, token) -> bool:
        """Revoke a token by adding it to the blacklist.

Args: token: The token to revoke.

Returns: bool: True if the token was revoked, False otherwise."""
```
```python
    def shutdown(self) -> None:
        """Shut down the Security Manager.

Cleans up resources and prepares for shutdown.

Raises: ManagerShutdownError: If shutdown fails."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the Security Manager.

Returns: Dict[str, Any]: Status information about the Security Manager."""
```
```python
    def update_user(self, user_id, updates) -> bool:
        """Update user information.

Args: user_id: The ID of the user to update. updates: Dict of fields to update. Can include: - username - email - password - roles - active - metadata

Returns: bool: True if the user was updated, False otherwise.

Raises: SecurityError: If the update fails."""
```
```python
    def verify_token(self, token) -> Optional[Dict[(str, Any)]]:
        """Verify a JWT token and return its payload.

Args: token: The JWT token to verify.

Returns: Optional[Dict[str, Any]]: The decoded token payload, or None if verification fails."""
```

```python
@dataclass
class User(object):
    """Represents a user in the system."""
```

```python
class UserRole(Enum):
    """User roles for role-based access control."""
```
*Class attributes:*
```python
ADMIN = 'admin'
OPERATOR = 'operator'
USER = 'user'
VIEWER = 'viewer'
```

#### Module: thread_manager
Path: `/home/runner/work/qorzen/qorzen/qorzen/core/thread_manager.py`

**Imports:**
```python
from __future__ import annotations
import asyncio
import concurrent.futures
import functools
import logging
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union, cast
from PySide6.QtCore import QMetaObject, QObject, Qt, Signal, Slot
from pydantic import BaseModel, Field
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, ThreadManagerError
```

**Global Variables:**
```python
T = T = TypeVar("T")
R = R = TypeVar("R")
```

**Classes:**
```python
class Config(object):
```
*Class attributes:*
```python
arbitrary_types_allowed = True
```

```python
class QtTaskBridge(QObject):
    """Bridges between threaded tasks and Qt's signal/slot system."""
```
*Class attributes:*
```python
taskCompleted =     taskCompleted = Signal(str, object)
taskFailed =     taskFailed = Signal(str, str, str)  # task_id, error_message, error_traceback
taskProgress =     taskProgress = Signal(str, int, str)  # task_id, progress_percent, status_message
executeOnMainThread =     executeOnMainThread = Signal(object, tuple, dict, object)  # func, args, kwargs, callback_event
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the Qt task bridge.  Args: parent: The parent QObject"""
```

```python
@dataclass
class TaskInfo(object):
    """Information about a task being executed."""
```

```python
class TaskPriority(int, Enum):
    """Priority levels for task execution."""
```
*Class attributes:*
```python
LOW = 0
NORMAL = 50
HIGH = 100
CRITICAL = 200
```

```python
class TaskProgressReporter(object):
    """Helper class for reporting task progress."""
```
*Methods:*
```python
    def __init__(self, task_id, task_bridge, execution_context, thread_manager) -> None:
        """Initialize the progress reporter.

Args: task_id: The ID of the task task_bridge: The Qt task bridge execution_context: The execution context of the task thread_manager: The thread manager"""
```
```python
    def report_progress(self, percent, message) -> None:
        """Report task progress.

Args: percent: The progress percentage (0-100) message: Optional status message"""
```

```python
class TaskResult(BaseModel):
    """Represents the result of a completed task."""
```

```python
class TaskStatus(str, Enum):
    """Represents the current status of a task."""
```
*Class attributes:*
```python
PENDING = 'pending'
RUNNING = 'running'
COMPLETED = 'completed'
FAILED = 'failed'
CANCELLED = 'cancelled'
```

```python
class ThreadExecutionContext(Enum):
    """Defines where a task should be executed."""
```
*Class attributes:*
```python
WORKER_THREAD =     WORKER_THREAD = auto()  # Execute in worker thread pool
MAIN_THREAD =     MAIN_THREAD = auto()  # Execute in the main Qt thread
CURRENT_THREAD =     CURRENT_THREAD = auto()  # Execute in the current thread
```

```python
class ThreadManager(QorzenManager):
    """Manages thread execution for background processing and UI updates."""
```
*Methods:*
```python
    def __init__(self, config_manager, logger_manager) -> None:
        """Initialize the thread manager.

Args: config_manager: The configuration manager logger_manager: The logger manager"""
```
```python
    def cancel_periodic_task(self, task_id) -> bool:
        """Cancel a periodic task.

Args: task_id: The ID of the periodic task

Returns: True if the task was cancelled, False otherwise"""
```
```python
    def cancel_task(self, task_id) -> bool:
        """Cancel a pending task.

Args: task_id: The ID of the task to cancel

Returns: True if the task was cancelled, False otherwise"""
```
```python
    def execute_on_main_thread_sync(self, func, *args, **kwargs) -> T:
        """Execute a function on the main thread and wait for its completion.

Args: func: The function to execute *args: Positional arguments for the function **kwargs: Keyword arguments for the function

Returns: The result of the function call

Raises: Any exception raised by the function"""
```
```python
    def get_task_info(self, task_id) -> Optional[Dict[(str, Any)]]:
        """Get information about a task.

Args: task_id: The ID of the task

Returns: A dictionary of task information, or None if the task is not found"""
```
```python
    def get_task_result(self, task_id, timeout) -> Any:
        """Get the result of a completed task.

Args: task_id: The ID of the task timeout: Optional timeout in seconds

Returns: The result of the task

Raises: ThreadManagerError: If the task is not found, failed, cancelled, or has no future concurrent.futures.TimeoutError: If the timeout is reached"""
```
```python
    def initialize(self) -> None:
        """Initialize the thread manager."""
```
```python
    def is_main_thread(self) -> bool:
        """Check if the current thread is the main Qt thread.

Returns: True if called from the main thread, False otherwise"""
```
```python
    def run_on_main_thread(self, func, *args, **kwargs) -> None:
        """Run a function on the main Qt thread.

Args: func: The function to run *args: Positional arguments for the function **kwargs: Keyword arguments for the function"""
```
```python
    def schedule_periodic_task(self, interval, func, task_id, *args, **kwargs) -> str:
        """Schedule a task to run periodically.

Args: interval: The interval in seconds between executions func: The function to execute periodically *args: Positional arguments for the function task_id: Optional task ID (one will be generated if not provided) **kwargs: Keyword arguments for the function

Returns: The task ID

Raises: ThreadManagerError: If the thread manager is not initialized"""
```
```python
    def shutdown(self) -> None:
        """Shut down the thread manager."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the thread manager.  Returns: A dictionary containing status information"""
```
```python
    def submit_async_task(self, coro_func, name, submitter, priority, on_completed, on_failed, *args, **kwargs) -> str:
        """Submit an async task for execution.

Args: coro_func: The async coroutine function to execute *args: Positional arguments for the function name: Optional name for the task submitter: Identifier for who submitted the task priority: Task priority on_completed: Callback for when the task completes successfully on_failed: Callback for when the task fails **kwargs: Keyword arguments for the function

Returns: The task ID"""
```
```python
    def submit_main_thread_task(self, func, on_completed, on_failed, name, priority, *args, **kwargs) -> str:
        """Submit a task to be executed on the main thread.

Args: func: The function to execute *args: Positional arguments for the function on_completed: Callback for when the task completes successfully on_failed: Callback for when the task fails name: Optional name for the task priority: Task priority **kwargs: Keyword arguments for the function

Returns: The task ID"""
```
```python
    def submit_qt_task(self, func, on_completed, on_failed, name, submitter, priority, *args, **kwargs) -> str:
        """Submit a task that updates the UI when complete.

Args: func: The function to execute *args: Positional arguments for the function on_completed: Callback for when the task completes successfully on_failed: Callback for when the task fails name: Optional name for the task submitter: Identifier for who submitted the task priority: Task priority **kwargs: Keyword arguments for the function

Returns: The task ID"""
```
```python
    def submit_task(self, func, name, submitter, priority, execution_context, metadata, result_handler, *args, **kwargs) -> str:
        """Submit a task for execution.

Args: func: The function to execute *args: Positional arguments for the function name: Optional name for the task submitter: Identifier for who submitted the task priority: Task priority execution_context: Where to execute the task metadata: Additional metadata for the task result_handler: Optional callback for handling the task result **kwargs: Keyword arguments for the function

Returns: The task ID

Raises: ThreadManagerError: If the thread manager is not initialized"""
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
*Plugin packaging system for Qorzen.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/__init__.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.plugin_system.manifest import PluginManifest, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, PluginVerifier
from qorzen.plugin_system.installer import PluginInstaller
from qorzen.plugin_system.tools import create_plugin_template, package_plugin
```

**Global Variables:**
```python
__all__ = __all__ = [
    "PluginManifest",
    "PluginCapability",
    "PluginPackage",
    "PackageFormat",
    "PluginSigner",
    "PluginVerifier",
    "PluginInstaller",
    "create_plugin_template",
    "package_plugin",
]
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
import os
import json
import tempfile
import threading
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, cast
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
    """Enhanced plugin installer with dependency resolution and lifecycle hooks.

This class integrates the plugin installer with dependency resolution, repository management, and lifecycle hooks to provide a complete plugin installation experience."""
```
*Methods:*
```python
    def __init__(self, plugins_dir, repository_manager, verifier, logger, core_version):
        """Initialize the integrated plugin installer.

Args: plugins_dir: Directory where plugins are installed. repository_manager: Manager for plugin repositories. verifier: Verifier for plugin signatures. logger: Callback for logging. core_version: Version of the core application."""
```
```python
    def disable_plugin(self, plugin_name) -> bool:
        """Disable a plugin.

Args: plugin_name: The name of the plugin.

Returns: True if the plugin was disabled, False otherwise."""
```
```python
    def enable_plugin(self, plugin_name) -> bool:
        """Enable a plugin.

Args: plugin_name: The name of the plugin.

Returns: True if the plugin was enabled, False otherwise."""
```
```python
    def get_enabled_plugins(self) -> Dict[(str, InstalledPlugin)]:
        """Get all enabled plugins.  Returns: Dictionary of plugin name to enabled plugin."""
```
```python
    def get_installed_plugin(self, plugin_name) -> Optional[InstalledPlugin]:
        """Get an installed plugin by name.

Args: plugin_name: The name of the plugin.

Returns: The installed plugin or None if not found."""
```
```python
    def get_installed_plugins(self) -> Dict[(str, InstalledPlugin)]:
        """Get all installed plugins.  Returns: Dictionary of plugin name to installed plugin."""
```
```python
    def get_loading_order(self) -> List[str]:
        """Get the loading order for plugins based on dependencies.

Returns: List of plugin names in the order they should be loaded."""
```
```python
    def install_plugin(self, package_path, force, skip_verification, enable, resolve_dependencies, install_dependencies) -> InstalledPlugin:
        """Install a plugin.

Args: package_path: Path to the plugin package. force: Whether to force installation even if the plugin is already installed. skip_verification: Whether to skip signature verification. enable: Whether to enable the plugin after installation. resolve_dependencies: Whether to resolve dependencies. install_dependencies: Whether to install missing dependencies.

Returns: The installed plugin.

Raises: PluginInstallationError: If the installation fails."""
```
```python
    def is_plugin_installed(self, plugin_name) -> bool:
        """Check if a plugin is installed.

Args: plugin_name: The name of the plugin.

Returns: True if the plugin is installed, False otherwise."""
```
```python
    def log(self, message, level) -> None:
        """Log a message.  Args: message: The message to log. level: The log level."""
```
```python
    def resolve_dependencies(self, package_path, repository_url) -> Dict[(str, Union[(str, bool)])]:
        """Resolve dependencies for a plugin package.

Args: package_path: Path to the plugin package. repository_url: URL of the repository to use for dependency resolution.

Returns: Dictionary of dependency name to repository name or status.

Raises: PluginInstallationError: If dependency resolution fails."""
```
```python
    def uninstall_plugin(self, plugin_name, keep_data, check_dependents) -> bool:
        """Uninstall a plugin.

Args: plugin_name: The name of the plugin. keep_data: Whether to keep plugin data. check_dependents: Whether to check for dependent plugins.

Returns: True if the plugin was uninstalled, False otherwise.

Raises: PluginInstallationError: If the uninstallation fails."""
```
```python
    def update_plugin(self, package_path, skip_verification, resolve_dependencies, install_dependencies) -> InstalledPlugin:
        """Update a plugin.

Args: package_path: Path to the plugin package. skip_verification: Whether to skip signature verification. resolve_dependencies: Whether to resolve dependencies. install_dependencies: Whether to install missing dependencies.

Returns: The updated plugin.

Raises: PluginInstallationError: If the update fails."""
```

```python
class PluginIntegrationError(Exception):
    """Exception raised for plugin integration errors."""
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
import threading
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Generic, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from qorzen.ui.integration import UIIntegration
from qorzen.core import RemoteServicesManager, SecurityManager, APIManager, CloudManager, LoggingManager, ConfigManager, DatabaseManager, EventBusManager, FileManager, ThreadManager
```

**Classes:**
```python
class BasePlugin(QObject):
    """Base class for all plugins.

Implements the PluginInterface protocol and provides common functionality for all plugins."""
```
*Class attributes:*
```python
initialized =     initialized = Signal()
ui_ready =     ui_ready = Signal()
shutdown_started =     shutdown_started = Signal()
shutdown_completed =     shutdown_completed = Signal()
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the plugin."""
```
```python
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, database_manager, remote_services_manager, security_manager, api_manager, cloud_manager, **kwargs) -> None:
        """Initialize the plugin with core services.

Args: event_bus: The event bus manager for publishing/subscribing to events. logger_provider: The logging manager for creating loggers. config_provider: The configuration manager for accessing configuration. file_manager: The file manager for file operations. thread_manager: The thread manager for thread operations. database_manager: The database manager for database operations. remote_services_manager: The remote services manager for remote services. security_manager: The security manager for security operations. api_manager: The API manager for API operations. cloud_manager: The cloud manager for cloud operations. **kwargs: Additional keyword arguments."""
```
```python
    def on_ui_ready(self, ui_integration) -> None:
        """Called when the UI is ready and the plugin can add UI components.

Args: ui_integration: The UI integration object for adding UI components."""
```
```python
    def shutdown(self) -> None:
        """Called when the plugin is being unloaded."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the status of the plugin.  Returns: A dictionary with plugin status information."""
```

```python
@runtime_checkable
class PluginInterface(Protocol):
    """Interface that all plugins must implement.

This protocol defines the required attributes and methods that a plugin must have to be properly loaded by the PluginManager."""
```
*Methods:*
```python
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, database_manager, remote_services_manager, security_manager, api_manager, cloud_manager, **kwargs) -> None:
        """Initialize the plugin with core services.

Args: event_bus: The event bus manager for publishing/subscribing to events. logger_provider: The logging manager for creating loggers. config_provider: The configuration manager for accessing configuration. file_manager: The file manager for file operations. thread_manager: The thread manager for thread operations. database_manager: The database manager for database operations. remote_services_manager: The remote services manager for remote services. security_manager: The security manager for security operations. api_manager: The API manager for API operations. cloud_manager: The cloud manager for cloud operations. **kwargs: Additional keyword arguments."""
```
```python
    def on_ui_ready(self, ui_integration) -> None:
        """Called when the UI is ready and the plugin can add UI components.

Args: ui_integration: The UI integration object for adding UI components."""
```
```python
    def shutdown(self) -> None:
        """Called when the plugin is being unloaded."""
```

#### Module: lifecycle
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugin_system/lifecycle.py`

**Imports:**
```python
from __future__ import annotations
import importlib
import inspect
import threading
import weakref
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union, Type, Protocol, runtime_checkable, cast
from qorzen.plugin_system.manifest import PluginLifecycleHook, PluginManifest
from qorzen.ui.integration import UIIntegration
```

**Functions:**
```python
def cleanup_ui(plugin_name) -> None:
    """Clean up UI components for a plugin."""
```

```python
def execute_hook(hook, plugin_name, manifest, plugin_instance, context, **kwargs) -> Any:
    """Execute a lifecycle hook for a plugin."""
```

```python
def find_plugin_hooks(plugin_instance) -> Dict[(PluginLifecycleHook, str)]:
    """Find all lifecycle hook methods defined in a plugin instance."""
```

```python
def get_lifecycle_manager() -> LifecycleManager:
    """Get the singleton instance of the lifecycle manager."""
```

```python
def get_plugin_state(plugin_name) -> PluginLifecycleState:
    """Get the current state of a plugin."""
```

```python
def get_ui_integration(plugin_name) -> Optional[UIIntegration]:
    """Get the UI integration for a plugin."""
```

```python
def register_ui_integration(plugin_name, ui_integration, main_window) -> None:
    """Register UI integration for a plugin."""
```

```python
def set_logger(logger) -> None:
    """Set the logger for the lifecycle manager."""
```

```python
def set_plugin_state(plugin_name, state) -> None:
    """Set the state of a plugin."""
```

```python
def set_thread_manager(thread_manager) -> None:
    """Set the thread manager for the lifecycle manager."""
```

```python
def signal_ui_ready(plugin_name) -> None:
    """Signal that UI is ready for a plugin."""
```

```python
def wait_for_ui_ready(plugin_name, timeout) -> bool:
    """Wait for UI to be ready for a plugin."""
```

**Classes:**
```python
class LifecycleHookError(Exception):
    """Exception raised when a lifecycle hook execution fails."""
```
*Methods:*
```python
    def __init__(self, hook, plugin_name, message):
```

```python
class LifecycleManager(object):
    """Manager for plugin lifecycle and hooks."""
```
*Methods:*
```python
    def __init__(self, logger_manager):
```
```python
    def cleanup_ui(self, plugin_name) -> None:
        """Clean up UI components for a plugin."""
```
```python
    def execute_hook(self, hook, plugin_name, manifest, plugin_instance, context) -> Any:
        """Execute a lifecycle hook for a plugin."""
```
```python
    def find_plugin_hooks(self, plugin_instance) -> Dict[(PluginLifecycleHook, str)]:
        """Find all lifecycle hook methods defined in a plugin instance."""
```
```python
    def get_plugin_state(self, plugin_name) -> PluginLifecycleState:
        """Get the current state of a plugin."""
```
```python
    def get_ui_integration(self, plugin_name) -> Optional[UIIntegration]:
        """Get the UI integration for a plugin."""
```
```python
    def log(self, message, level) -> None:
        """Log a message."""
```
```python
    def register_ui_integration(self, plugin_name, ui_integration, main_window) -> None:
        """Register UI integration for a plugin."""
```
```python
    def set_logger(self, logger) -> None:
        """Set the logger."""
```
```python
    def set_plugin_state(self, plugin_name, state) -> None:
        """Set the state of a plugin."""
```
```python
    def set_thread_manager(self, thread_manager) -> None:
        """Set the thread manager for thread-safe operations."""
```
```python
    def signal_ui_ready(self, plugin_name) -> None:
        """Signal that UI is ready for a plugin."""
```
```python
    def wait_for_ui_ready(self, plugin_name, timeout) -> bool:
        """Wait for UI to be ready for a plugin."""
```

```python
@runtime_checkable
class PluginInterface(Protocol):
    """Interface that plugins must implement."""
```
*Methods:*
```python
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs) -> None:
        """Ellipsis"""
```
```python
    def on_ui_ready(self, ui_integration) -> None:
        """Ellipsis"""
```
```python
    def shutdown(self) -> None:
        """Ellipsis"""
```

```python
class PluginLifecycleState(Enum):
    """Lifecycle states for plugins."""
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

### Package: plugins
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins`

**__init__.py:**
*Plugin system for extending the Qorzen platform functionality.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/__init__.py`

**Imports:**
```python
from importlib.metadata import entry_points
```

#### Package: aces_validator
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/aces_validator`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/aces_validator/__init__.py`

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
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, database_manager, security_manager, **kwargs) -> None:
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
    def __init__(self, event_bus, logger, config, file_manager, thread_manager, security_manager, parent) -> None:
        """Initialize the AS400 tab.

Args: event_bus: The event bus manager for event handling logger: Logger for logging events config: Configuration manager for settings file_manager: Optional file manager for file operations thread_manager: Optional thread manager for background tasks security_manager: Optional security manager for security operations parent: Optional parent widget"""
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

#### Package: event_monitor_plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/event_monitor_plugin`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/event_monitor_plugin/__init__.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.plugins.event_monitor_plugin.plugin import EventMonitorPlugin
```

**Global Variables:**
```python
__version__ = '1.0.0'
__author__ = 'Qorzen Team'
__all__ = __all__ = ["EventMonitorPlugin", "__version__", "__author__"]
```

##### Module: plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/event_monitor_plugin/plugin.py`

**Imports:**
```python
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox, QCheckBox, QTabWidget
```

**Classes:**
```python
class EventMonitorPlugin(object):
    """Plugin for monitoring events and diagnosing UI integration issues."""
```
*Class attributes:*
```python
name = 'event_monitor'
version = '1.0.0'
description = 'Monitors events and helps diagnose plugin integration issues'
author = 'Support'
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the plugin."""
```
```python
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs) -> None:
        """Initialize the plugin with the provided managers."""
```
```python
    def shutdown(self) -> None:
        """Shut down the plugin."""
```

#### Package: example_plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/example_plugin`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/example_plugin/__init__.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.plugins.example_plugin.code.plugin import ExamplePlugin
```

**Global Variables:**
```python
__version__ = '1.0.0'
__author__ = 'Qorzen Team'
__all__ = __all__ = ["ExamplePlugin", "__version__", "__author__"]
```

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/example_plugin/code`

**__init__.py:**
*Example Plugin code module.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/example_plugin/code/__init__.py`

###### Module: hooks
*Example Plugin - Lifecycle hooks.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/example_plugin/code/hooks.py`

**Imports:**
```python
from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path
```

**Functions:**
```python
def post_install(context) -> None:
    """Post-install hook.

Called after the plugin is installed. Use this to set up initial plugin data or resources.

Args: context: Installation context information"""
```

```python
def post_uninstall(context) -> None:
    """Post-uninstall hook.

Called after the plugin is uninstalled. Use this to clean up any remaining resources or external dependencies.

Args: context: Uninstallation context information"""
```

```python
def post_update(context) -> None:
    """Post-update hook.

Called after the plugin is updated. Use this to migrate data to new formats or structures.

Args: context: Update context information"""
```

```python
def pre_install(context) -> None:
    """Pre-install hook.

Called before the plugin is installed. Use this to check requirements or prepare the environment for installation.

Args: context: Installation context information"""
```

```python
def pre_uninstall(context) -> None:
    """Pre-uninstall hook.

Called before the plugin is uninstalled. Use this to back up data or perform cleanup.

Args: context: Uninstallation context information"""
```

```python
def pre_update(context) -> None:
    """Pre-update hook.

Called before the plugin is updated. Use this to prepare for the update, such as backing up data or settings.

Args: context: Update context information"""
```

###### Module: plugin
*Example Plugin - Main plugin class and entry point.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/example_plugin/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
from PySide6.QtCore import Qt, QObject, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QTabWidget, QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QColorDialog, QFileDialog
from PySide6.QtGui import QColor, QIcon
from qorzen.plugin_system.extension import register_extension_point, call_extension_point, get_extension_point
```

**Classes:**
```python
class ExamplePlugin(QObject):
    """Main plugin class for Example Plugin.

This class demonstrates the features of the enhanced plugin system and serves as a template for developing new plugins."""
```
*Class attributes:*
```python
name = 'example_plugin'
version = '1.0.0'
description = 'An example plugin showcasing the enhanced plugin system features'
author = 'Qorzen Team'
ui_update_signal =     ui_update_signal = Signal(dict)
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the plugin."""
```
```python
    def example_plugin_text_transform(self, text, options) -> str:
        """Alternative implementation of our own extension point."""
```
```python
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs) -> None:
        """Initialize the plugin with the provided managers.

Args: event_bus: Event bus manager for pub/sub communication logger_provider: Logger provider for plugin-specific loggers config_provider: Configuration provider for settings file_manager: File manager for file operations thread_manager: Thread manager for background tasks **kwargs: Additional managers or dependencies"""
```
```python
    def on_post_disable(self, context) -> None:
        """Post-disable lifecycle hook.

Called after the plugin is disabled.

Args: context: Context information including managers"""
```
```python
    def on_post_enable(self, context) -> None:
        """Post-enable lifecycle hook.

Called after the plugin is enabled.

Args: context: Context information including managers"""
```
```python
    def on_pre_disable(self, context) -> None:
        """Pre-disable lifecycle hook.

Called before the plugin is disabled.

Args: context: Context information including managers"""
```
```python
    def on_pre_enable(self, context) -> None:
        """Pre-enable lifecycle hook.

Called before the plugin is enabled.

Args: context: Context information including managers"""
```
```python
    def shutdown(self) -> None:
        """Shut down the plugin.  Clean up resources and unsubscribe from events."""
```
```python
    def text_transform(self, text, options) -> str:
        """Text transform extension point implementation.

This is our own implementation of the text.transform extension point, which adds a prefix to the text.

Args: text: The text to transform options: Optional transformation options

Returns: The transformed text"""
```
```python
    def ui_widget(self, parent) -> QWidget:
        """UI widget extension point implementation.

This is our own implementation of the ui.widget extension point, which provides a simple UI widget.

Args: parent: The parent widget

Returns: A widget to be displayed in the UI"""
```

#### Package: system_monitor
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/system_monitor`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/system_monitor/__init__.py`

**Imports:**
```python
from __future__ import annotations
from qorzen.plugins.system_monitor.code.plugin import SystemMonitorPlugin
```

**Global Variables:**
```python
__version__ = '0.2.0'
__author__ = 'Ryan Serra'
__all__ = __all__ = ["__version__", "__author__", "SystemMonitorPlugin"]
```

##### Package: code
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/system_monitor/code`

**__init__.py:**
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/system_monitor/code/__init__.py`

###### Module: hooks
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/system_monitor/code/hooks.py`

**Imports:**
```python
from __future__ import annotations
import os
import shutil
import time
from typing import Dict, Any, Optional, cast
```

**Functions:**
```python
def post_disable(context) -> None:
    """Post-disable hook.

This hook is called after the plugin is disabled. It performs any necessary cleanup after disabling the plugin.

Args: context: Hook context"""
```

```python
def post_enable(context) -> None:
    """Post-enable hook.

This hook is called after the plugin is enabled. It initializes the UI integration and triggers the plugin's UI setup.

Args: context: Hook context"""
```

```python
def post_install(context) -> None:
    """Post-installation hook.

This hook is called after the plugin is installed. It performs any necessary tasks after the installation is complete.

Args: context: Hook context"""
```

```python
def post_uninstall(context) -> None:
    """Post-uninstall hook.

This hook is called after the plugin is uninstalled. It performs any necessary clean-up after removing the plugin.

Args: context: Hook context"""
```

```python
def post_update(context) -> None:
    """Post-update hook.

This hook is called after the plugin is updated. It performs any necessary tasks after the update process is complete.

Args: context: Hook context"""
```

```python
def pre_install(context) -> None:
    """Pre-installation hook.

This hook is called before the plugin is installed. It performs any necessary tasks before the installation process begins.

Args: context: Hook context"""
```

```python
def pre_uninstall(context) -> None:
    """Pre-uninstall hook.

This hook is called before the plugin is uninstalled. It performs any necessary clean-up before removing the plugin.

Args: context: Hook context"""
```

```python
def pre_update(context) -> None:
    """Pre-update hook.

This hook is called before the plugin is updated. It performs any necessary tasks before the update process begins.

Args: context: Hook context"""
```

###### Module: plugin
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/system_monitor/code/plugin.py`

**Imports:**
```python
from __future__ import annotations
import logging
import time
import threading
from typing import Any, Dict, List, Optional, cast
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QMenu, QToolBar
from PySide6.QtCore import QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QColor, QPalette
from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, TabComponent
from qorzen.plugin_system.interface import BasePlugin
```

**Classes:**
```python
class ResourceWidget(QWidget):
    """Widget for displaying a system resource with progress bar."""
```
*Methods:*
```python
    def __init__(self, title, parent) -> None:
        """Initialize the resource widget.  Args: title: The title of the resource. parent: The parent widget."""
```
```python
    def update_value(self, value) -> None:
        """Update the displayed value.  Args: value: The value to display (0-100)."""
```

```python
class SystemMonitorPlugin(BasePlugin):
    """Plugin for monitoring system resources."""
```
*Class attributes:*
```python
name = 'system_monitor'
version = '1.0.0'
description = 'Real-time system resource monitoring'
author = 'Qorzen Team'
dependencies =     dependencies = []
```
*Methods:*
```python
    def __init__(self) -> None:
        """Initialize the system monitor plugin."""
```
```python
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs) -> None:
        """Initialize the plugin with required components.

Args: event_bus: The event bus. logger_provider: The logger provider. config_provider: The configuration provider. file_manager: The file manager. thread_manager: The thread manager. **kwargs: Additional components."""
```
```python
    def on_ui_ready(self, ui_integration) -> None:
        """Set up UI components when UI is ready.  Args: ui_integration: The UI integration."""
```
```python
    def shutdown(self) -> None:
        """Shutdown the plugin and clean up resources."""
```
```python
    def status(self) -> Dict[(str, Any)]:
        """Get the plugin status.  Returns: The plugin status dictionary."""
```

```python
class SystemMonitorTab(QWidget):
    """Tab for the system monitor plugin."""
```
*Class attributes:*
```python
update_signal =     update_signal = Signal(dict)
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the system monitor tab.  Args: parent: The parent widget."""
```
```python
    def get_widget(self) -> QWidget:
        """Get the widget for this tab.  Returns: The widget for this tab."""
```
```python
    def on_tab_deselected(self) -> None:
        """Called when this tab is deselected."""
```
```python
    def on_tab_selected(self) -> None:
        """Called when this tab is selected."""
```
```python
    def update_metrics(self, metrics) -> None:
        """Update the displayed metrics.  Args: metrics: The metrics to display."""
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
import csv
import logging
import os
import tempfile
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QRegularExpression, QSize, QSortFilterProxyModel, Qt, Signal, Slot, QThread, QTimer, QPoint, QObject
from PySide6.QtGui import QAction, QClipboard, QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QProgressBar, QProgressDialog, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter, QTableView, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget, QGridLayout, QApplication, QRadioButton
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event, EventType
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
        """Initialize column selection dialog.

Args: available_columns: List of available columns with id and name selected_columns: List of currently selected column IDs parent: Parent widget"""
```
```python
    def get_selected_columns(self) -> List[str]:
        """Get selected column IDs in displayed order.  Returns: List of selected column IDs"""
```

```python
class DataTableWidget(QWidget):
    """Widget for displaying query results in a table."""
```
*Class attributes:*
```python
queryStarted =     queryStarted = Signal()
queryFinished =     queryFinished = Signal()
```
*Methods:*
```python
    def __del__(self) -> None:
        """Clean up event subscriptions."""
```
```python
    def __init__(self, database_handler, event_bus, logger, parent) -> None:
        """Initialize data table widget.

Args: database_handler: Database handler for queries event_bus: Event bus for communication logger: Logger instance parent: Parent widget"""
```
```python
    def execute_query(self, filter_panels) -> None:
        """Execute a query with the given filter panels. All UI operations must happen on the main thread.

Args: filter_panels: List of filter criteria from filter panels"""
```
```python
    def get_callback_id(self) -> str:
        """Get callback ID for event subscription.  Returns: Callback ID"""
```
```python
    def get_page_size(self) -> int:
        """Get current page size.  Returns: Page size"""
```
```python
    def get_selected_columns(self) -> List[str]:
        """Get currently selected columns.  Returns: List of selected column IDs"""
```

```python
class ExportOptionsDialog(QDialog):
    """Dialog for export options."""
```
*Methods:*
```python
    def __init__(self, format_type, current_count, total_count, parent) -> None:
        """Initialize export options dialog.

Args: format_type: Export format type ("csv" or "excel") current_count: Number of records in current page total_count: Total number of records matching query parent: Parent widget"""
```
```python
    def export_all(self) -> bool:
        """Check if all results should be exported.

Returns: True if all results should be exported, False for current page only"""
```

```python
class QueryResultModel(QAbstractTableModel):
    """Table model for query results."""
```
*Methods:*
```python
    def __init__(self, columns, column_map, parent) -> None:
        """Initialize query result model.

Args: columns: List of column IDs column_map: Mapping from column IDs to display names parent: Parent widget"""
```
```python
    def columnCount(self, parent) -> int:
        """Get number of columns.  Args: parent: Parent index  Returns: Number of columns"""
```
```python
    def data(self, index, role) -> Any:
        """Get data for a cell.

Args: index: Cell index role: Data role

Returns: Cell data for the requested role"""
```
```python
    def get_all_data(self) -> List[Dict[(str, Any)]]:
        """Get all visible data.  Returns: List of all visible row data dictionaries"""
```
```python
    def get_row_data(self, row) -> Dict[(str, Any)]:
        """Get data for a specific row.  Args: row: Row index  Returns: Row data dictionary"""
```
```python
    def get_total_count(self) -> int:
        """Get total row count (may include non-visible rows).  Returns: Total row count"""
```
```python
    def headerData(self, section, orientation, role) -> Any:
        """Get header data.

Args: section: Section index orientation: Header orientation role: Data role

Returns: Header data for the requested role"""
```
```python
    def rowCount(self, parent) -> int:
        """Get number of rows.  Args: parent: Parent index  Returns: Number of rows"""
```
```python
    def set_columns(self, columns) -> None:
        """Set columns for the model.  Args: columns: List of column IDs"""
```
```python
    def set_data(self, data, total_count) -> None:
        """Set data for the model.

Args: data: List of row data dictionaries total_count: Total number of matching rows (may be more than visible)"""
```

```python
class QuerySignals(QObject):
```
*Class attributes:*
```python
started =     started = Signal()
completed =     completed = Signal(object)
failed =     failed = Signal(str)
progress =     progress = Signal(int, int)
```

```python
class TableFilterWidget(QWidget):
    """Widget for filtering table data."""
```
*Class attributes:*
```python
filterChanged =     filterChanged = Signal(dict)
```
*Methods:*
```python
    def __init__(self, columns, column_map, parent) -> None:
        """Initialize table filter widget.

Args: columns: List of column IDs column_map: Mapping from column IDs to display names parent: Parent widget"""
```
```python
    def get_filters(self) -> Dict[(str, Any)]:
        """Get current filters.  Returns: Dictionary of current filters"""
```
```python
    def set_columns(self, columns) -> None:
        """Set available columns.  Args: columns: List of column IDs"""
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
        """Initialize year range filter widget.  Args: parent: Parent widget"""
```
```python
    def get_filter(self) -> Dict[(str, Any)]:
        """Get current filter values.  Returns: Filter dictionary or empty dict if no filter active"""
```

###### Module: database_handler
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/database_handler.py`

**Imports:**
```python
from __future__ import annotations
import logging
import threading
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, cast
import sqlalchemy
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import Select
from qorzen.core.database_manager import DatabaseConnectionConfig, DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event, EventType
from qorzen.core.thread_manager import ThreadManager, TaskResult
from qorzen.utils.exceptions import DatabaseError
from events import VCdbEventType
from models import Aspiration, BaseVehicle, BedConfig, BedLength, BedType, BodyNumDoors, BodyStyleConfig, BodyType, BrakeABS, BrakeConfig, BrakeSystem, BrakeType, Class, CylinderHeadType, DriveType, ElecControlled, EngineBase2, EngineBlock, EngineBoreStroke, EngineConfig2, EngineDesignation, EngineVersion, FuelDeliveryConfig, FuelDeliverySubType, FuelDeliveryType, FuelSystemControlType, FuelSystemDesign, FuelType, IgnitionSystemType, Make, Mfr, MfrBodyCode, Model, PowerOutput, PublicationStage, Region, SpringType, SpringTypeConfig, SteeringConfig, SteeringSystem, SteeringType, SubModel, Transmission, TransmissionBase, TransmissionControlType, TransmissionMfrCode, TransmissionNumSpeeds, TransmissionType, Valves, Vehicle, VehicleToBodyConfig, VehicleToBodyStyleConfig, VehicleToBedConfig, VehicleToBrakeConfig, VehicleToClass, VehicleToDriveType, VehicleToEngineConfig, VehicleToMfrBodyCode, VehicleToSpringTypeConfig, VehicleToSteeringConfig, VehicleToTransmission, VehicleToWheelBase, VehicleType, VehicleTypeGroup, WheelBase, Year
```

**Classes:**
```python
class DatabaseHandler(object):
    """Handler for VCDB database operations."""
```
*Class attributes:*
```python
CONNECTION_NAME = 'vcdb_explorer'
```
*Methods:*
```python
    def __init__(self, database_manager, event_bus, thread_manager, logger) -> None:
        """Initialize the DatabaseHandler.

Args: database_manager: Database manager for connection handling event_bus: Event bus for inter-component communication thread_manager: Thread manager for background tasks logger: Logger for this component"""
```
```python
    def configure(self, host, port, database, user, password, db_type, pool_size, max_overflow, pool_recycle, echo) -> None:
        """Configure the database connection.

Args: host: Database host address port: Database port database: Database name user: Database username password: Database password db_type: Database type (default: postgresql) pool_size: Connection pool size (default: 5) max_overflow: Maximum pool overflow (default: 10) pool_recycle: Connection recycle time in seconds (default: 3600) echo: Whether to echo SQL statements (default: False)"""
```
```python
    def execute_query(self, filter_panels, columns, page, page_size, sort_by, sort_desc, table_filters) -> Tuple[(List[Dict[(str, Any)]], int)]:
        """Execute a query with the given parameters.

Args: filter_panels: Filter panel configurations columns: Columns to include in the result page: Page number (default: 1) page_size: Page size (default: 100) sort_by: Column to sort by (default: None) sort_desc: Sort direction (default: False) table_filters: Additional table filters (default: None)

Returns: Tuple of (results, total_count)

Raises: DatabaseHandlerError: If not initialized or a database error occurs"""
```
```python
    def get_available_columns(self) -> List[Dict[(str, str)]]:
        """Get available columns for query results."""
```
```python
    def get_available_filters(self) -> List[Dict[(str, str)]]:
        """Get available filter types."""
```
```python
    def get_filter_values(self, filter_type, current_filters, exclude_filters) -> List[Dict[(str, Any)]]:
        """Get available values for a specific filter type."""
```
```python
@contextmanager
    def session(self) -> Generator[(Session, None, None)]:
        """Create a database session context manager.

Yields: A database session

Raises: DatabaseHandlerError: If not initialized or a database error occurs"""
```
```python
    def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
```

```python
class DatabaseHandlerError(Exception):
    """Exception raised for errors in the DatabaseHandler."""
```
*Methods:*
```python
    def __init__(self, message, details) -> None:
        """Initialize the error with a message and optional details.

Args: message: The error message details: Optional details about the error"""
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
    """VCdb Explorer plugin-specific event types."""
```
*Methods:*
```python
@staticmethod
    def filter_changed() -> str:
        """Event emitted when a filter has been changed."""
```
```python
@staticmethod
    def filters_refreshed() -> str:
        """Event emitted when filters have been refreshed."""
```
```python
@staticmethod
    def query_execute() -> str:
        """Event emitted to request query execution."""
```
```python
@staticmethod
    def query_results() -> str:
        """Event emitted when query results are available."""
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
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
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
    """Handles exporting data to various formats."""
```
*Methods:*
```python
    def __init__(self, logger) -> None:
        """Initialize data exporter.  Args: logger: Logger instance"""
```
```python
    def export_all_data(self, database_callback, filter_panels, columns, column_map, file_path, format_type, max_rows, table_filters, sort_by, sort_desc, progress_callback) -> int:
        """Export all matching data to a file.

Args: database_callback: Function to execute database queries filter_panels: List of filter panel selections columns: List of column IDs to export column_map: Mapping from column IDs to display names file_path: Target file path format_type: Export format ('csv' or 'excel') max_rows: Maximum number of rows to export table_filters: Additional table filters sort_by: Column to sort by sort_desc: Sort descending if True progress_callback: Callback for progress updates

Returns: Number of rows exported

Raises: ExportError: If export fails"""
```
```python
    def export_csv(self, data, columns, column_map, file_path) -> None:
        """Export data to CSV file.

Args: data: List of row data dictionaries columns: List of column IDs to export column_map: Mapping from column IDs to display names file_path: Target file path

Raises: ExportError: If export fails"""
```
```python
    def export_excel(self, data, columns, column_map, file_path, sheet_name) -> None:
        """Export data to Excel file.

Args: data: List of row data dictionaries columns: List of column IDs to export column_map: Mapping from column IDs to display names file_path: Target file path sheet_name: Name of the Excel sheet

Raises: ExportError: If export fails or Excel export is not available"""
```

```python
class ExportError(Exception):
    """Exception raised for errors during data export."""
```
*Methods:*
```python
    def __init__(self, message, details) -> None:
        """Initialize export error.  Args: message: Error message details: Additional error details"""
```

###### Module: filter_panel
Path: `/home/runner/work/qorzen/qorzen/qorzen/plugins/vcdb_explorer/code/filter_panel.py`

**Imports:**
```python
from __future__ import annotations
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel, QMenu, QPushButton, QSizePolicy, QSpinBox, QTabWidget, QToolButton, QVBoxLayout, QWidget
from qorzen.core.event_bus_manager import EventBusManager
from database_handler import DatabaseHandler
from events import VCdbEventType
```

**Classes:**
```python
class ComboBoxFilter(FilterWidget):
    """Combo box filter widget."""
```
*Methods:*
```python
    def __init__(self, filter_type, filter_name, parent) -> None:
        """Initialize combo box filter.

Args: filter_type: Type of filter filter_name: Display name of filter parent: Parent widget"""
```
```python
@Slot()
    def clear(self) -> None:
        """Clear the filter selection."""
```
```python
    def get_selected_values(self) -> List[int]:
        """Get selected filter values.  Returns: List containing the selected value ID if any, otherwise empty"""
```
```python
    def set_available_values(self, values) -> None:
        """Set available filter values.  Args: values: List of available values with id, name, and count"""
```

```python
class FilterPanel(QGroupBox):
    """Panel containing a group of filters."""
```
*Class attributes:*
```python
filterChanged =     filterChanged = Signal(str, str, list)
removeRequested =     removeRequested = Signal(str)
```
*Methods:*
```python
    def __del__(self) -> None:
        """Clean up event subscriptions."""
```
```python
    def __init__(self, panel_id, database_handler, event_bus, logger, parent) -> None:
        """Initialize filter panel.

Args: panel_id: Unique panel identifier database_handler: Database handler for filter values event_bus: Event bus for communication logger: Logger instance parent: Parent widget"""
```
```python
    def get_current_values(self) -> Dict[(str, List[int])]:
        """Get current filter values.  Returns: Dictionary of filter types to selected values"""
```
```python
    def get_panel_id(self) -> str:
        """Get panel ID.  Returns: Panel identifier"""
```
```python
    def refresh_all_filters(self) -> None:
        """Refresh all filters."""
```
```python
    def set_filter_values(self, filter_type, values) -> None:
        """Set available values for a filter.

Args: filter_type: Type of filter values: List of available values with id, name, and count"""
```
```python
    def update_filter_values(self, filter_values) -> None:
        """Update filter values from external source.

Args: filter_values: Dictionary of filter types to available values"""
```

```python
class FilterPanelManager(QWidget):
    """Manager for multiple filter panels."""
```
*Class attributes:*
```python
filtersChanged =     filtersChanged = Signal()
```
*Methods:*
```python
    def __del__(self) -> None:
        """Clean up event subscriptions."""
```
```python
    def __init__(self, database_handler, event_bus, logger, max_panels, parent) -> None:
        """Initialize the filter panel manager.

Args: database_handler: Database handler for filter values event_bus: Event bus for communication logger: Logger instance max_panels: Maximum number of panels allowed parent: Parent widget"""
```
```python
    def get_all_filters(self) -> List[Dict[(str, List[int])]]:
        """Get all active filter values from all panels.  Returns: List of filter dictionaries, one per panel"""
```
```python
    def refresh_all_panels(self) -> None:
        """Refresh all panels."""
```
```python
    def update_filter_values(self, panel_id, filter_values) -> None:
        """Update filter values for a specific panel.

Args: panel_id: ID of panel to update filter_values: Filter values to set"""
```

```python
class FilterWidget(QWidget):
    """Base class for filter widgets."""
```
*Class attributes:*
```python
valueChanged =     valueChanged = Signal(str, list)
```
*Methods:*
```python
    def __init__(self, filter_type, filter_name, parent) -> None:
        """Initialize the filter widget.

Args: filter_type: Type of filter filter_name: Display name of filter parent: Parent widget"""
```
```python
@Slot()
    def clear(self) -> None:
        """Clear the filter selection."""
```
```python
    def get_filter_name(self) -> str:
        """Get the filter display name.  Returns: Filter display name"""
```
```python
    def get_filter_type(self) -> str:
        """Get the filter type.  Returns: Filter type identifier"""
```
```python
    def get_selected_values(self) -> List[int]:
        """Get selected filter values.  Returns: List of selected value IDs"""
```
```python
    def set_available_values(self, values) -> None:
        """Set available filter values.  Args: values: List of available values with id, name, and count"""
```

```python
class YearRangeFilter(FilterWidget):
    """Year range filter widget."""
```
*Methods:*
```python
    def __init__(self, filter_type, filter_name, parent) -> None:
        """Initialize year range filter.

Args: filter_type: Type of filter filter_name: Display name of filter parent: Parent widget"""
```
```python
@Slot()
    def clear(self) -> None:
        """Clear the filter selection."""
```
```python
    def get_selected_values(self) -> List[int]:
        """Get selected year range.  Returns: List containing start and end years if valid, otherwise empty"""
```
```python
    def set_available_values(self, values) -> None:
        """Set available year values.  Args: values: List of available years with id, name, and count"""
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
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from PySide6.QtCore import Qt, QThread, Slot, QTimer
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QMessageBox, QProgressDialog, QPushButton, QSplitter, QVBoxLayout, QWidget
from PySide6.QtGui import QAction, QIcon
from qorzen.core import RemoteServicesManager, SecurityManager, APIManager, CloudManager, LoggingManager, ConfigManager, DatabaseManager, EventBusManager, FileManager, ThreadManager
from qorzen.core.thread_manager import ThreadExecutionContext, TaskResult
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration
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
```
```python
    def get_icon(self) -> Optional[str]:
        """Get the icon path for the plugin."""
```
```python
    def get_main_widget(self) -> Optional[QWidget]:
        """Get the main widget for the plugin."""
```
```python
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, database_manager, remote_services_manager, security_manager, api_manager, cloud_manager, **kwargs) -> None:
        """Initialize the plugin with core services."""
```
```python
    def on_ui_ready(self, ui_integration) -> None:
        """Set up UI components when the UI is ready."""
```
```python
    def shutdown(self) -> None:
        """Shut down the plugin."""
```

```python
class VCdbExplorerWidget(QWidget):
```
*Methods:*
```python
    def __del__(self) -> None:
```
```python
    def __init__(self, database_handler, event_bus, thread_manager, logger, export_settings, parent) -> None:
```
```python
    def refresh_filters(self) -> None:
```

### Package: ui
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui`

**__init__.py:**
*User interface components for the Qorzen platform.*
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/__init__.py`

**Imports:**
```python
from qorzen.ui.panel_ui import MainWindow
```

#### Module: dashboard
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/dashboard.py`

**Imports:**
```python
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
```

**Classes:**
```python
class DashboardWidget(QWidget):
    """Main dashboard widget displaying system status and metrics."""
```
*Methods:*
```python
    def __init__(self, app_core, parent) -> None:
        """Initialize the dashboard widget.  Args: app_core: The application core parent: The parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle widget close events.  Args: event: The event"""
```
```python
    def hideEvent(self, event) -> None:
        """Handle widget hide events.  Args: event: The event"""
```
```python
    def showEvent(self, event) -> None:
        """Handle widget show events.  Args: event: The event"""
```

```python
class MetricsWidget(QWidget):
    """Widget for displaying system metrics."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the metrics widget.  Args: parent: The parent widget"""
```
```python
    def update_metrics(self, metrics) -> None:
        """Update the displayed metrics.  Args: metrics: The metrics data"""
```

```python
class SystemStatusTreeWidget(QTreeWidget):
    """Tree widget for displaying system status information."""
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the system status tree widget.  Args: parent: The parent widget"""
```
```python
    def get_item_path(self, item) -> str:
        """Get the path of an item in the tree.

Args: item: The tree widget item

Returns: A string representing the item's path"""
```
```python
    def restore_expanded_state(self) -> None:
        """Restore the expanded state of items in the tree."""
```
```python
    def save_expanded_state(self) -> None:
        """Save the expanded state of items in the tree."""
```
```python
    def update_system_status(self, status) -> None:
        """Update the system status display.  Args: status: The system status information"""
```

#### Module: integration
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/integration.py`

**Imports:**
```python
from __future__ import annotations
import abc
import threading
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Set, TypeVar, Generic, Union, cast
from PySide6.QtWidgets import QWidget, QMenu, QToolBar, QDockWidget
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
```

**Global Variables:**
```python
T = T = TypeVar('T')
```

**Classes:**
```python
class ComponentTracker(Generic[T]):
    """Thread-safe tracker for UI components."""
```
*Methods:*
```python
    def __init__(self) -> None:
```
```python
    def add(self, plugin_id, component_type, component) -> None:
        """Add a component to the tracker."""
```
```python
    def get_all(self, plugin_id) -> Dict[(str, List[T])]:
        """Get all components for a plugin."""
```
```python
    def get_by_type(self, plugin_id, component_type) -> List[T]:
        """Get components of a specific type for a plugin."""
```
```python
    def has_plugin(self, plugin_id) -> bool:
        """Check if a plugin has any components."""
```
```python
    def remove_all(self, plugin_id) -> None:
        """Remove all components for a plugin."""
```

```python
class DockComponent(UIComponent):
    """Interface for dock components."""
```
*Methods:*
```python
    def get_dock_widget(self) -> QWidget:
        """Ellipsis"""
```

```python
class MainWindowIntegration(UIIntegration):
    """Implementation of UIIntegration for the MainWindow."""
```
*Methods:*
```python
    def __init__(self, main_window) -> None:
```
```python
    def add_dock_widget(self, plugin_id, dock, title, area) -> QDockWidget:
        """Add a dock widget to the main window."""
```
```python
    def add_menu(self, plugin_id, title, parent_menu) -> QMenu:
        """Add a menu to the menu bar or a parent menu."""
```
```python
    def add_menu_action(self, plugin_id, menu, text, callback, icon) -> QAction:
        """Add an action to a menu."""
```
```python
    def add_page(self, plugin_id, widget, name, icon, text, group) -> int:
        """Add a page to the panel layout."""
```
```python
    def add_toolbar(self, plugin_id, title) -> QToolBar:
        """Add a toolbar to the main window."""
```
```python
    def add_toolbar_action(self, plugin_id, toolbar, text, callback, icon) -> QAction:
        """Add an action to a toolbar."""
```
```python
    def cleanup_plugin(self, plugin_id) -> None:
        """Clean up all UI components for a plugin."""
```
```python
    def find_menu(self, menu_title) -> Optional[QMenu]:
        """Find a menu by title."""
```
```python
    def remove_page(self, plugin_id, name) -> None:
        """Remove a page from the panel layout."""
```
```python
    def select_page(self, name) -> None:
        """Select a page in the panel layout."""
```

```python
class MenuComponent(UIComponent):
    """Interface for menu components."""
```
*Methods:*
```python
    def get_actions(self) -> List[QAction]:
        """Ellipsis"""
```

```python
class ToolbarComponent(UIComponent):
    """Interface for toolbar components."""
```
*Methods:*
```python
    def get_actions(self) -> List[QAction]:
        """Ellipsis"""
```

```python
class UIComponent(Protocol):
    """Interface for UI components."""
```
*Methods:*
```python
    def get_widget(self) -> QWidget:
        """Ellipsis"""
```

```python
class UIIntegration(abc.ABC):
    """UI Integration interface for plugins to interact with the main UI."""
```
*Methods:*
```python
@abc.abstractmethod
    def add_dock_widget(self, plugin_id, dock, title, area) -> QDockWidget:
        """Add a dock widget to the main window."""
```
```python
@abc.abstractmethod
    def add_menu(self, plugin_id, title, parent_menu) -> QMenu:
        """Add a menu to the menu bar or a parent menu."""
```
```python
@abc.abstractmethod
    def add_menu_action(self, plugin_id, menu, text, callback, icon) -> QAction:
        """Add an action to a menu."""
```
```python
@abc.abstractmethod
    def add_page(self, plugin_id, widget, name, icon, text, group) -> int:
        """Add a page to the panel layout."""
```
```python
@abc.abstractmethod
    def add_toolbar(self, plugin_id, title) -> QToolBar:
        """Add a toolbar to the main window."""
```
```python
@abc.abstractmethod
    def add_toolbar_action(self, plugin_id, toolbar, text, callback, icon) -> QAction:
        """Add an action to a toolbar."""
```
```python
@abc.abstractmethod
    def cleanup_plugin(self, plugin_id) -> None:
        """Clean up all UI components for a plugin."""
```
```python
@abc.abstractmethod
    def find_menu(self, menu_title) -> Optional[QMenu]:
        """Find a menu by title."""
```
```python
@abc.abstractmethod
    def remove_page(self, plugin_id, name) -> None:
        """Remove a page from the panel layout."""
```
```python
@abc.abstractmethod
    def select_page(self, name) -> None:
        """Select a page in the panel layout."""
```

#### Module: logs
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/logs.py`

**Imports:**
```python
from __future__ import annotations
import json
import time
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QTimer, Signal, Slot, QSize
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableView, QTextEdit, QToolBar, QVBoxLayout, QWidget
```

**Classes:**
```python
class LogEntry(object):
    """Represents a log entry in the log view."""
```
*Methods:*
```python
    def __init__(self, timestamp, level, logger, message, event, task, raw_data) -> None:
        """Initialize a log entry.

Args: timestamp: The timestamp string level: The log level logger: The logger name message: The log message event: Optional event name task: Optional task name raw_data: Optional raw log data"""
```
```python
@classmethod
    def from_event_payload(cls, payload) -> 'LogEntry':
        """Create a log entry from an event payload.

Args: payload: The event payload

Returns: A new LogEntry instance"""
```

```python
class LogLevel(Enum):
    """Log levels with colors."""
```
*Class attributes:*
```python
DEBUG =     DEBUG = (QColor(108, 117, 125), "DEBUG")  # Gray
INFO =     INFO = (QColor(23, 162, 184), "INFO")  # Blue
WARNING =     WARNING = (QColor(255, 193, 7), "WARNING")  # Yellow
ERROR =     ERROR = (QColor(220, 53, 69), "ERROR")  # Red
CRITICAL =     CRITICAL = (QColor(136, 14, 79), "CRITICAL")  # Purple
```
*Methods:*
```python
@classmethod
    def from_string(cls, level_str) -> 'LogLevel':
        """Get a log level from a string.

Args: level_str: The log level string

Returns: The corresponding LogLevel enum value"""
```

```python
class LogTableModel(QAbstractTableModel):
    """Model for the log table view."""
```
*Class attributes:*
```python
COLUMNS =     COLUMNS = ['Timestamp', 'Level', 'Logger', 'Message', 'Event', 'Task']
```
*Methods:*
```python
    def __init__(self, parent) -> None:
        """Initialize the log table model.  Args: parent: The parent widget"""
```
```python
    def add_log(self, log_entry) -> None:
        """Add a log entry to the model.  Args: log_entry: The log entry to add"""
```
```python
    def clear_logs(self) -> None:
        """Clear all logs from the model."""
```
```python
    def columnCount(self, parent) -> int:
        """Get the number of columns in the model.

Args: parent: The parent index

Returns: The number of columns"""
```
```python
    def data(self, index, role) -> Any:
        """Get data for a specific index and role.

Args: index: The model index role: The data role

Returns: The requested data"""
```
```python
    def get_unique_loggers(self) -> List[str]:
        """Get a list of unique logger names in the logs.  Returns: A list of unique logger names"""
```
```python
    def headerData(self, section, orientation, role) -> Any:
        """Get header data.

Args: section: The section index orientation: The header orientation role: The data role

Returns: The header data"""
```
```python
    def rowCount(self, parent) -> int:
        """Get the number of rows in the model.  Args: parent: The parent index  Returns: The number of rows"""
```
```python
    def set_filter_level(self, level) -> None:
        """Set the level filter.  Args: level: The log level filter, or None for all levels"""
```
```python
    def set_filter_logger(self, logger) -> None:
        """Set the logger filter.  Args: logger: The logger name filter"""
```
```python
    def set_filter_text(self, text) -> None:
        """Set the text filter.  Args: text: The filter text"""
```

```python
class LogsView(QWidget):
    """Widget for displaying and filtering logs."""
```
*Methods:*
```python
    def __init__(self, event_bus, parent) -> None:
        """Initialize the logs view.  Args: event_bus: The event bus parent: The parent widget"""
```
```python
    def closeEvent(self, event) -> None:
        """Handle widget close events.  Args: event: The event"""
```
```python
    def hideEvent(self, event) -> None:
        """Handle widget hide events.  Args: event: The event"""
```
```python
    def showEvent(self, event) -> None:
        """Handle widget show events.  Args: event: The event"""
```

#### Module: panel_ui
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/panel_ui.py`

**Imports:**
```python
from __future__ import annotations
import os
import sys
import time
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QMenuBar, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QStackedWidget, QVBoxLayout, QWidget
```

**Classes:**
```python
class ContentArea(QStackedWidget):
```
*Methods:*
```python
    def __init__(self, parent) -> None:
```
```python
    def add_page(self, widget, name) -> int:
```
```python
    def get_page_by_name(self, name) -> Optional[QWidget]:
```

```python
class MainWindow(QMainWindow):
```
*Methods:*
```python
    def __init__(self, app_core) -> None:
```
```python
    def closeEvent(self, event) -> None:
```
```python
    def get_menu(self, menu_name) -> Optional[QMenu]:
        """Get a menu by name, if it exists."""
```

```python
class PanelLayout(QWidget):
```
*Methods:*
```python
    def __init__(self, parent, app_core) -> None:
```
```python
    def add_page(self, widget, name, icon, text, group) -> int:
```
```python
    def add_separator(self) -> None:
```
```python
    def select_page(self, page_name) -> None:
```

```python
class Sidebar(QFrame):
```
*Class attributes:*
```python
pageChangeRequested =     pageChangeRequested = Signal(int)
```
*Methods:*
```python
    def __init__(self, parent) -> None:
```
```python
    def add_button(self, icon, text, page_index, group, checkable) -> SidebarButton:
```
```python
    def add_separator(self) -> None:
```
```python
    def select_page(self, page_index) -> None:
```

```python
class SidebarButton(QPushButton):
```
*Methods:*
```python
    def __init__(self, icon, text, parent, checkable) -> None:
```

#### Module: plugins
Path: `/home/runner/work/qorzen/qorzen/qorzen/ui/plugins.py`

**Imports:**
```python
from __future__ import annotations
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget
from qorzen.core.plugin_manager import PluginInfo
```

**Classes:**
```python
class PluginCard(QFrame):
    """A card widget displaying information about a plugin."""
```
*Class attributes:*
```python
stateChangeRequested =     stateChangeRequested = Signal(str, bool)  # plugin_name, enable
reloadRequested =     reloadRequested = Signal(str)  # plugin_name
infoRequested =     infoRequested = Signal(str)  # plugin_name
```
*Methods:*
```python
    def __init__(self, plugin_name, plugin_info, parent) -> None:
        """Initialize the plugin card.

Args: plugin_name: The name of the plugin plugin_info: Information about the plugin parent: The parent widget"""
```
```python
    def update_info(self, plugin_info) -> None:
        """Update the plugin information displayed in the card.

Args: plugin_info: New information about the plugin"""
```

```python
class PluginState(Enum):
    """Represents the current state of a plugin."""
```
*Class attributes:*
```python
DISCOVERED =     DISCOVERED = auto()  # Plugin is discovered but not loaded
LOADED =     LOADED = auto()  # Plugin is loaded and ready
ACTIVE =     ACTIVE = auto()  # Plugin is active and running
INACTIVE =     INACTIVE = auto()  # Plugin is loaded but not active
FAILED =     FAILED = auto()  # Plugin failed to load or crashed
DISABLED =     DISABLED = auto()  # Plugin is explicitly disabled
```

```python
class PluginsView(QWidget):
    """Widget for displaying and managing plugins."""
```
*Class attributes:*
```python
pluginStateChangeRequested =     pluginStateChangeRequested = Signal(str, bool)  # plugin_name, enable
pluginReloadRequested =     pluginReloadRequested = Signal(str)  # plugin_name
pluginInfoRequested =     pluginInfoRequested = Signal(str)  # plugin_name
```
*Methods:*
```python
    def __init__(self, plugin_manager, parent) -> None:
        """Initialize the plugins view.  Args: plugin_manager: The plugin manager parent: The parent widget"""
```
```python
    def cleanup(self) -> None:
        """Clean up resources."""
```
```python
    def update_plugin_state(self, plugin_name, state) -> None:
        """Update the state of a plugin card.  Args: plugin_name: The name of the plugin state: The new state"""
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
    """Base exception for all manager-related errors."""
```
*Methods:*
```python
    def __init__(self, message, manager_name, *args, **kwargs) -> None:
        """Initialize a ManagerError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. manager_name: The name of the manager that raised the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
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
class QorzenError(Exception):
    """Base exception for all Qorzen errors.

All custom exceptions in the Qorzen system should inherit from this class to ensure consistent error handling and logging."""
```
*Methods:*
```python
    def __init__(self, message, code, details, *args, **kwargs) -> None:
        """Initialize a QorzenError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. code: An optional error code for programmatic identification. details: An optional dictionary with additional error details. **kwargs: Additional keyword arguments to pass to the parent Exception."""
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
class ThreadManagerError(QorzenError):
    """Exception raised for thread management-related errors."""
```
*Methods:*
```python
    def __init__(self, message, thread_id, *args, **kwargs) -> None:
        """Initialize a ThreadManagerError.

Args: message: A descriptive error message. *args: Additional positional arguments to pass to the parent Exception. thread_id: The ID of the thread that caused the error. **kwargs: Additional keyword arguments to pass to the parent Exception."""
```

