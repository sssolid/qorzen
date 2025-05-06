# Qorzen Plugin Development Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Plugin Structure](#plugin-structure)
3. [Plugin Lifecycle](#plugin-lifecycle)
4. [Core Managers and Services](#core-managers-and-services)
5. [Event-Driven Architecture](#event-driven-architecture)
6. [Configuration Management](#configuration-management)
7. [File Operations](#file-operations)
8. [Database Access](#database-access)
9. [Thread Management](#thread-management)
10. [Security Integration](#security-integration)
11. [API Extensions](#api-extensions)
12. [Remote Services](#remote-services)
13. [Cloud Storage Integration](#cloud-storage-integration)
14. [UI Integration](#ui-integration)
15. [Best Practices](#best-practices)
16. [Troubleshooting](#troubleshooting)
17. [Plugin Template](#plugin-template)

## Introduction

Qorzen is a modular, extensible platform built around a core set of managers that provide various capabilities. Plugins extend this core functionality, enabling developers to add new features without modifying the core codebase.

This guide explains how to develop plugins for the Qorzen framework, detailing the plugin structure, lifecycle, and how to interact with core services.

## Plugin Structure

### Directory Structure

A Qorzen plugin must follow this directory structure:

```
plugins/
└── your_plugin_name/
    ├── __init__.py
    ├── plugin.py          # Main plugin class
    ├── routes/            # Optional: API routes
    │   └── __init__.py
    ├── models/            # Optional: Data models
    │   └── __init__.py
    ├── services/          # Optional: Business logic
    │   └── __init__.py
    └── ui/                # Optional: UI components
        └── __init__.py
```

### Create the `__init__.py` File

```python
# yourplugin/__init__.py
from __future__ import annotations
from yourplugin.plugin import YourPluginName

__version__ = "0.1.0"
__author__ = "Your Name"

__all__ = ["__version__", "__author__", "YourPluginName"]
```

### Plugin Base Class

Every plugin must include a main class that defines its metadata and lifecycle methods:

```python
# plugin.py
from __future__ import annotations
import os
from logging import Logger
from typing import Any, Dict, List, Optional
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction


from qorzen.core import FileManager, ThreadManager, EventBusManager, ConfigManager

from qorzen.plugins.yourplugin.config.settings import YOUR_SETTING


class YourPluginName(QObject):
    ui_ready_signal = Signal(object)
    
    # Required metadata
    name = "your_plugin_name"
    version = "0.1.0"
    description = "Description of your plugin"
    author = "Your Name"
    
    # Optional metadata
    dependencies = []  # List of other plugin names this plugin depends on
    
    # Instance variables for manager references
    def __init__(self) -> None:
       super().__init__()
        self._event_bus = None
        self._logger = None
        self._config = None
        self._file_manager = None
        self._thread_manager = None
        self._initialized = False
        
        self._menu_items: List[QAction] = []
        self._tab = None
        self._tab_index: Optional[int] = None

        # Connect signal to slot
        self.ui_ready_signal.connect(self._handle_ui_ready_on_main_thread)
    
    def initialize(self, 
                   event_bus: Any, 
                   logger_provider: Any, 
                   config_provider: Any, 
                   file_manager: Any, 
                   thread_manager: Any,
                   **kwargs: Any) -> None:
        """Initialize the plugin with Qorzen core services."""
        # Store references to core services
        self._event_bus: EventBusManager = event_bus
        self._logger: Logger = logger_provider.get_logger(self.name)
        self._config: ConfigManager = config_provider
        self._file_manager: FileManager = file_manager
        self._thread_manager: ThreadManager = thread_manager
        
        # Your initialization code here
        self._logger.info(f"Initializing {self.name} v{self.version} plugin")
        
        # Create plugin data directory if needed
        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type='plugin_data')
                self._file_manager.ensure_directory(plugin_data_dir.as_posix())
                self._logger.debug(f'Plugin data directory: {plugin_data_dir}')
            except Exception as e:
                self._logger.warning(f'Failed to create plugin data directory: {str(e)}')
        
        # Subscribe to events
        self._event_bus.subscribe(
            event_type="some_event_type",
            callback=self._on_some_event,
            subscriber_id=f"{self.name}_subscriber"
        )
        
        # Register API routes
        # Register UI components
        # Initialize database models
        
        self._initialized = True
        self._logger.info(f'{self.name} plugin initialized')

        # Publish initialization event
        self._event_bus.publish(
            event_type='plugin/initialized',
            source=self.name,
            payload={'plugin_name': self.name, 'version': self.version, 'has_ui': True}
        )
    
    def _load_settings(self) -> None:
        """Load plugin settings from configuration."""
        try:
            # Check if your_setting string is already in config, if not set default
            your_setting = self._config.get(f'plugins.{self.name}.your_setting', None)
            if your_setting is None:
                self._config.set(f'plugins.{self.name}.your_setting', YOUR_SETTING)
        except Exception as e:
            self._logger.error(f'Error loading settings: {str(e)}')
    
    def _on_ui_ready_event(self, event: Any) -> None:
        """Handler for ui/ready event."""
        try:
            main_window = event.payload.get('main_window')
            if not main_window:
                self._logger.error('Main window not provided in event payload')
                return
            
            # Use signal to handle UI updates on the main thread
            self.ui_ready_signal.emit(main_window)
        except Exception as e:
            self._logger.error(f'Error in UI ready event handler: {str(e)}')
    
    @Slot(object)
    def _handle_ui_ready_on_main_thread(self, main_window: Any) -> None:
        """Set up UI components on the main thread."""
        try:
            self._logger.debug('Setting up UI components')
            self._main_window = main_window
            
            # Add plugin tab to main window
            self._add_tab_to_ui()
            
            # Add menu items
            self._add_menu_items()
            
            # Publish UI added event
            self._event_bus.publish(
                event_type=f'plugin/{self.name}/ui_added', 
                source=self.name, 
                payload={'tab_index': self._tab_index}
            )
        except Exception as e:
            self._logger.error(f'Error handling UI setup: {str(e)}')
    
    def shutdown(self) -> None:
        """Clean up resources when plugin is being unloaded."""
        if not self._initialized:
            return
            
        self._logger.info(f"Shutting down {self.name} plugin")
        
        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f"{self.name}_subscriber")
        
        # Close any open resources
        
        self._initialized = False
        self._logger.info(f"{self.name} plugin shut down successfully")

    def status(self) -> Dict[str, Any]:
        """Return the status of the plugin."""
        return {
            'name': self.name,
            'version': self.version,
            'initialized': self._initialized,
            'has_ui': True,
            'ui_components': {
                'tab_added': self._tab is not None,
                'tab_index': self._tab_index,
                'menu_items_count': len(self._menu_items)
            },
            'subscriptions': ['some_event_type']
        }
```

## Plugin Lifecycle

### States
A plugin can be in one of the following states:

- **DISCOVERED**: Plugin was found but not loaded yet
- **LOADED**: Plugin class was instantiated
- **ACTIVE**: Plugin was successfully initialized
- **INACTIVE**: Plugin was loaded but not active (e.g., after shutdown)
- **FAILED**: Plugin could not be loaded or initialized
- **DISABLED**: Plugin is explicitly disabled in configuration

### Lifecycle Methods

#### 1. `__init__()` 
- Called when the plugin is first loaded
- Store instance variables but don't access core services yet

#### 2. `initialize(event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs)`
- Called by the PluginManager when activating the plugin
- Receives references to core services
- Set up event subscriptions
- Initialize resources
- Register extension points

#### 3. `shutdown()`
- Called when the plugin is being unloaded
- Unsubscribe from events
- Release resources
- Clean up any persistent state

## Core Managers and Services

### Overview of Available Managers

The following core managers are automatically provided to your plugin during initialization:

| Manager | Purpose | Access In Plugin |
|---------|---------|-----------------|
| EventBusManager | Send/receive events | `self._event_bus` |
| LoggingManager | Structured logging | `self._logger` |
| ConfigManager | Configuration access | `self._config` |
| FileManager | File system operations | `self._file_manager` |
| ThreadManager | Background task execution | `self._thread_manager` |
| DatabaseManager | Data persistence | Available via kwargs or event |
| SecurityManager | Authentication/authorization | Available via kwargs or event |
| APIManager | REST API extensions | Available via kwargs or event |
| RemoteServicesManager | External service communication | Available via kwargs or event |
| ResourceMonitoringManager | System resource monitoring | Available via kwargs or event |
| CloudManager | Cloud storage integration | Available via kwargs or event |

### Access Additional Managers

To access additional managers beyond the five automatically provided:

```python
def initialize(self, 
               event_bus: Any, 
               logger_provider: Any, 
               config_provider: Any, 
               file_manager: Any, 
               thread_manager: Any,
               **kwargs: Any) -> None:
    
    # Basic managers
    self._event_bus = event_bus
    self._logger = logger_provider.get_logger(self.name)
    self._config = config_provider
    self._file_manager = file_manager
    self._thread_manager = thread_manager
    
    # Additional managers
    if 'database_manager' in kwargs:
        self._db_manager = kwargs['database_manager']
    else:
        # Alternative way to get managers
        app_core = kwargs.get('app_core')
        if app_core:
            self._db_manager = app_core.get_manager('database_manager')
            self._security_manager = app_core.get_manager('security_manager')
            self._api_manager = app_core.get_manager('api_manager')
```

## Event-Driven Architecture

The Qorzen platform uses an event-driven architecture for communication between components. This enables loose coupling and makes your plugin more maintainable.

### Subscribe to Events

```python
def initialize(self, event_bus: Any, **kwargs: Any) -> None:
    self._event_bus = event_bus
    
    # Subscribe to specific event
    self._event_bus.subscribe(
        event_type="user/login", 
        callback=self._on_user_login,
        subscriber_id=f"{self.name}_user_login_handler"
    )
    
    # Subscribe to all events of a category using wildcard
    self._event_bus.subscribe(
        event_type="file/*", 
        callback=self._on_file_event,
        subscriber_id=f"{self.name}_file_events_handler"
    )
    
    # Subscribe with filter criteria
    self._event_bus.subscribe(
        event_type="user/created",
        callback=self._on_admin_created,
        subscriber_id=f"{self.name}_admin_created_handler",
        filter_criteria={"roles": ["admin"]}
    )

def _on_user_login(self, event: Any) -> None:
    """Handle user login events."""
    user_id = event.payload.get("user_id")
    self._logger.info(f"User {user_id} logged in")
    
def _on_file_event(self, event: Any) -> None:
    """Handle any file-related event."""
    self._logger.debug(f"File event: {event.event_type}")
    
def _on_admin_created(self, event: Any) -> None:
    """Handle admin user creation events."""
    self._logger.info(f"Admin user created: {event.payload.get('username')}")
```

### Publish Events

```python
def process_something(self, data: Dict[str, Any]) -> None:
    # Do some processing
    result = self._some_business_logic(data)
    
    # Publish an event with the result
    self._event_bus.publish(
        event_type=f"{self.name}/processing_completed",
        source=self.name,
        payload={
            "input_data": data,
            "result": result,
            "timestamp": datetime.datetime.now().isoformat()
        }
    )
```

### Common Event Types

| Event Category    | Examples                                                | Usage |
|-------------------|---------------------------------------------------------|-------|
| `ui/*`            | `ui/ready`                                              | UI events |
| `user/*`          | `user/login`, `user/logout`, `user/created`             | User account events |
| `file/*`          | `file/uploaded`, `file/deleted`                         | File operations |
| `plugin/*`        | `plugin/initialized`, `plugin/loaded`, `plugin/unloaded` | Plugin lifecycle |
| `system/*`        | `system/started`, `system/shutdown`                     | System lifecycle |
| `api/*`           | `api/request`, `api/response`                           | API interactions |
| `config/*`        | `config/changed`                                        | Configuration changes |
| `{plugin_name}/*` | `your_plugin/custom_event`                              | Plugin-specific events |

## Configuration Management

### Access Configuration

```python
def initialize(self, config_provider: Any, **kwargs: Any) -> None:
    self._config = config_provider
    
    # Get plugin-specific config (with default)
    plugin_config = self._config.get(f"plugins.{self.name}", {})
    
    # Get individual setting with default
    self._api_key = plugin_config.get("api_key", "default_key")
    self._endpoint = plugin_config.get("endpoint", "https://example.com/api")
    self._debug_mode = plugin_config.get("debug", False)
    
    # Get system config
    db_config = self._config.get("database", {})
    api_config = self._config.get("api", {})
```

### Change Configuration

```python
def update_setting(self, key: str, value: Any) -> None:
    """Update a plugin setting."""
    config_key = f"plugins.{self.name}.{key}"
    
    try:
        self._config.set(config_key, value)
        self._logger.info(f"Updated config {config_key} to {value}")
    except Exception as e:
        self._logger.error(f"Failed to update config {config_key}: {str(e)}")
```

### Subscribe to Configuration Changes

```python
def initialize(self, config_provider: Any, **kwargs: Any) -> None:
    self._config = config_provider
    
    # Register for config changes
    self._config.register_listener(f"plugins.{self.name}", self._on_config_changed)

def _on_config_changed(self, key: str, value: Any) -> None:
    """Handle configuration changes."""
    self._logger.debug(f"Config changed: {key} = {value}")
    
    if key == f"plugins.{self.name}.api_key":
        self._api_key = value
        self._reinitialize_api_client()
    elif key == f"plugins.{self.name}.endpoint":
        self._endpoint = value
        self._reinitialize_api_client()
```

## File Operations

The FileManager provides safe access to the file system with proper locking mechanisms.

### Read and Write Files

```python
def initialize(self, file_manager: Any, **kwargs: Any) -> None:
    self._file_manager = file_manager
    
    # Create plugin data directory
    self._data_dir = f"{self.name}/data"
    self._file_manager.ensure_directory(self._data_dir, directory_type="plugin_data")
    
    # Write a file
    config_data = json.dumps({"initialized": True, "timestamp": time.time()})
    self._file_manager.write_text(
        f"{self._data_dir}/config.json",
        content=config_data,
        directory_type="plugin_data",
        create_dirs=True
    )
    
    # Read a file
    try:
        content = self._file_manager.read_text(
            f"{self._data_dir}/config.json",
            directory_type="plugin_data"
        )
        self._cached_config = json.loads(content)
    except Exception as e:
        self._logger.warning(f"Failed to read config file: {str(e)}")
        self._cached_config = {}
```

### List and Manage Files

```python
def list_plugin_files(self) -> List[Dict[str, Any]]:
    """List all files in plugin data directory."""
    try:
        files = self._file_manager.list_files(
            path=self._data_dir,
            directory_type="plugin_data",
            recursive=True
        )
        return [
            {
                "name": file.name,
                "path": file.path,
                "size": file.size,
                "modified_at": file.modified_at,
                "is_directory": file.is_directory
            }
            for file in files
        ]
    except Exception as e:
        self._logger.error(f"Failed to list files: {str(e)}")
        return []

def backup_plugin_data(self) -> Optional[str]:
    """Create a backup of plugin data directory."""
    try:
        backup_path = self._file_manager.create_backup(
            path=self._data_dir,
            directory_type="plugin_data"
        )
        self._logger.info(f"Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        self._logger.error(f"Failed to create backup: {str(e)}")
        return None
```

## Database Access

### Connect to Database

```python
def initialize(self, **kwargs: Any) -> None:
    # Get database manager
    self._db_manager = kwargs.get('database_manager')
    if not self._db_manager:
        self._logger.error("Database manager not available")
        return
        
    # Create tables if they don't exist
    self._ensure_tables()

def _ensure_tables(self) -> None:
    """Create plugin database tables if they don't exist."""
    # Import the Base class from the database_manager
    from qorzen.core.database_manager import Base
    
    # Define your models
    class PluginModel(Base):
        __tablename__ = f"{self.name}_items"
        
        id = Column(Integer, primary_key=True)
        name = Column(String(255), nullable=False)
        data = Column(JSON, nullable=True)
        created_at = Column(DateTime, default=func.now())
        
    # Create the tables
    try:
        with self._db_manager.session() as session:
            Base.metadata.create_all(self._db_manager.get_engine())
        self._logger.info("Plugin database tables created or verified")
    except Exception as e:
        self._logger.error(f"Failed to create database tables: {str(e)}")
```

### Query and Manipulate Data

```python
def create_item(self, name: str, data: Dict[str, Any]) -> Optional[int]:
    """Create a new item in the database."""
    if not self._db_manager:
        return None
        
    try:
        with self._db_manager.session() as session:
            item = PluginModel(name=name, data=data)
            session.add(item)
            session.commit()
            return item.id
    except Exception as e:
        self._logger.error(f"Failed to create item: {str(e)}")
        return None

def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve an item from the database."""
    if not self._db_manager:
        return None
        
    try:
        with self._db_manager.session() as session:
            query = select(PluginModel).where(PluginModel.id == item_id)
            result = session.execute(query).scalar_one_or_none()
            
            if result:
                return {
                    "id": result.id,
                    "name": result.name,
                    "data": result.data,
                    "created_at": result.created_at.isoformat()
                }
            return None
    except Exception as e:
        self._logger.error(f"Failed to get item: {str(e)}")
        return None
```

### Use Async Database Operations

```python
async def get_items_async(self, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve items using async database operations."""
    if not self._db_manager:
        return []
        
    try:
        async with await self._db_manager.async_session() as session:
            query = select(PluginModel).limit(limit)
            result = await session.execute(query)
            items = result.scalars().all()
            
            return [
                {
                    "id": item.id,
                    "name": item.name,
                    "data": item.data,
                    "created_at": item.created_at.isoformat()
                }
                for item in items
            ]
    except Exception as e:
        self._logger.error(f"Failed to get items async: {str(e)}")
        return []
```

## Thread Management

The ThreadManager helps you execute tasks in the background without blocking the main thread.

### Execute Background Tasks

```python
def initialize(self, thread_manager: Any, **kwargs: Any) -> None:
    self._thread_manager = thread_manager
    
    # Start a background task
    self._thread_manager.submit_task(
        func=self._background_processing,
        name=f"{self.name}_background_processing",
        submitter=self.name
    )

def _background_processing(self) -> None:
    """Execute background processing logic."""
    self._logger.info("Starting background processing")
    
    try:
        # Do some CPU-intensive work
        for i in range(10):
            time.sleep(1)  # Simulate work
            self._logger.debug(f"Background processing step {i+1}/10")
            
        self._logger.info("Background processing completed")
    except Exception as e:
        self._logger.error(f"Background processing failed: {str(e)}")
```

### Schedule Periodic Tasks

```python
def initialize(self, thread_manager: Any, **kwargs: Any) -> None:
    self._thread_manager = thread_manager
    
    # Schedule a task to run every 5 minutes
    self._cleanup_task_id = self._thread_manager.schedule_periodic_task(
        interval=300,  # 5 minutes in seconds
        func=self._cleanup_old_data,
        task_id=f"{self.name}_cleanup_task"
    )
    
    # Schedule a task to run every hour
    self._sync_task_id = self._thread_manager.schedule_periodic_task(
        interval=3600,  # 1 hour in seconds
        func=self._sync_with_remote_service,
        task_id=f"{self.name}_sync_task"
    )

def _cleanup_old_data(self) -> None:
    """Clean up old temporary data."""
    self._logger.info("Cleaning up old data")
    # Your cleanup logic here

def shutdown(self) -> None:
    """Clean up resources when plugin is being unloaded."""
    # Cancel periodic tasks
    if hasattr(self, '_cleanup_task_id') and self._thread_manager:
        self._thread_manager.cancel_periodic_task(self._cleanup_task_id)
        
    if hasattr(self, '_sync_task_id') and self._thread_manager:
        self._thread_manager.cancel_periodic_task(self._sync_task_id)
```

### Execute Async Tasks

```python
def process_data_async(self, data: Dict[str, Any]) -> str:
    """Process data asynchronously and return a task ID."""
    task_id = self._thread_manager.submit_async_task(
        coro_func=self._async_processing,
        data=data,
        name=f"{self.name}_async_processing",
        submitter=self.name
    )
    
    return task_id

async def _async_processing(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute asynchronous processing logic."""
    self._logger.info(f"Starting async processing of {len(data)} items")
    
    results = []
    for item in data.get("items", []):
        # Simulate async work
        await asyncio.sleep(0.1)
        results.append({"id": item["id"], "processed": True})
        
    return {"status": "completed", "results": results}

def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
    """Get the result of an async task."""
    try:
        result = self._thread_manager.get_task_result(task_id)
        return result
    except Exception as e:
        self._logger.error(f"Failed to get task result: {str(e)}")
        return None
```

## Security Integration

### User Authentication

```python
def initialize(self, **kwargs: Any) -> None:
    self._security_manager = kwargs.get('security_manager')
    if not self._security_manager:
        self._logger.warning("Security manager not available")

def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user and return user information."""
    if not self._security_manager:
        return None
        
    try:
        user_data = self._security_manager.authenticate_user(username, password)
        return user_data
    except Exception as e:
        self._logger.error(f"Authentication failed: {str(e)}")
        return None

def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token and return payload."""
    if not self._security_manager:
        return None
        
    try:
        payload = self._security_manager.verify_token(token)
        return payload
    except Exception as e:
        self._logger.error(f"Token verification failed: {str(e)}")
        return None
```

### Permissions and Access Control

```python
def check_permission(self, user_id: str, resource: str, action: str) -> bool:
    """Check if a user has permission to access a resource."""
    if not self._security_manager:
        return False
        
    try:
        return self._security_manager.has_permission(user_id, resource, action)
    except Exception as e:
        self._logger.error(f"Permission check failed: {str(e)}")
        return False

def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Get user information."""
    if not self._security_manager:
        return None
        
    try:
        return self._security_manager.get_user_info(user_id)
    except Exception as e:
        self._logger.error(f"Failed to get user info: {str(e)}")
        return None
```

## API Extensions

Extend the Qorzen REST API with your plugin's endpoints.

### Register API Routes

```python
def initialize(self, **kwargs: Any) -> None:
    self._api_manager = kwargs.get('api_manager')
    if not self._api_manager:
        self._logger.warning("API manager not available")
        return
        
    # Register API routes
    self._register_api_routes()

def _register_api_routes(self) -> None:
    """Register plugin API routes."""
    if not self._api_manager:
        return
        
    # Get current user dependency
    from fastapi import Depends
    get_current_user = self._api_manager._get_current_user
    
    # Register GET endpoint
    self._api_manager.register_api_endpoint(
        path=f"/api/v1/plugins/{self.name}/items",
        method="get",
        endpoint=self.api_get_items,
        tags=[self.name],
        dependencies=[Depends(get_current_user)]
    )
    
    # Register POST endpoint
    self._api_manager.register_api_endpoint(
        path=f"/api/v1/plugins/{self.name}/items",
        method="post",
        endpoint=self.api_create_item,
        tags=[self.name],
        dependencies=[Depends(get_current_user)]
    )
    
    self._logger.info(f"Registered API endpoints for {self.name}")

async def api_get_items(self, limit: int = 10, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """API endpoint to get items."""
    try:
        items = await self.get_items_async(limit)
        return {"items": items, "count": len(items)}
    except Exception as e:
        self._logger.error(f"API error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def api_create_item(self, item: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """API endpoint to create an item."""
    try:
        item_id = self.create_item(item.get("name"), item.get("data", {}))
        if not item_id:
            raise HTTPException(status_code=500, detail="Failed to create item")
            
        return {"id": item_id, "created": True}
    except Exception as e:
        self._logger.error(f"API error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Remote Services

Communicate with external services using the RemoteServicesManager.

### Register and Use Remote Services

```python
def initialize(self, **kwargs: Any) -> None:
    self._remote_manager = kwargs.get('remote_services_manager')
    if not self._remote_manager:
        self._logger.warning("Remote services manager not available")
        return
        
    # Register a remote service
    self._register_remote_service()

def _register_remote_service(self) -> None:
    """Register an external API as a remote service."""
    if not self._remote_manager:
        return
    
    # Get service configuration
    service_config = self._config.get(f"plugins.{self.name}.remote_service", {})
    service_url = service_config.get("url", "https://api.example.com")
    api_key = service_config.get("api_key", "")
    
    try:
        # Construct the service configuration
        service_def = {
            "type": "http",
            "protocol": "https",
            "base_url": service_url,
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            "timeout": 30.0,
            "max_retries": 3,
            "verify_ssl": True
        }
        
        # Register the service with the platform
        self._event_bus.publish(
            event_type="remote_service/register",
            source=self.name,
            payload={
                "service_name": f"{self.name}_api",
                "service_config": service_def
            }
        )
        
        self._logger.info(f"Registered remote service at {service_url}")
    except Exception as e:
        self._logger.error(f"Failed to register remote service: {str(e)}")

def call_remote_api(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Call the remote API."""
    if not self._remote_manager:
        return None
        
    service_name = f"{self.name}_api"
    
    try:
        kwargs = {}
        if data and method in ["POST", "PUT", "PATCH"]:
            kwargs["json_data"] = data
            
        response = self._remote_manager.make_request(
            service_name=service_name,
            method=method,
            path=endpoint,
            **kwargs
        )
        
        return response
    except Exception as e:
        self._logger.error(f"Remote API call failed: {str(e)}")
        return None
```

### Async Remote Service Calls

```python
async def call_remote_api_async(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Call the remote API asynchronously."""
    if not self._remote_manager:
        return None
        
    service_name = f"{self.name}_api"
    
    try:
        kwargs = {}
        if data and method in ["POST", "PUT", "PATCH"]:
            kwargs["json_data"] = data
            
        response = await self._remote_manager.make_request_async(
            service_name=service_name,
            method=method,
            path=endpoint,
            **kwargs
        )
        
        return response
    except Exception as e:
        self._logger.error(f"Async remote API call failed: {str(e)}")
        return None
```

## Cloud Storage Integration

Use the CloudManager to store and retrieve files from cloud storage.

### Cloud Storage Operations

```python
def initialize(self, **kwargs: Any) -> None:
    self._cloud_manager = kwargs.get('cloud_manager')
    if not self._cloud_manager:
        self._logger.warning("Cloud manager not available")
        return

def upload_to_cloud(self, local_path: str, remote_path: str) -> bool:
    """Upload a file to cloud storage."""
    if not self._cloud_manager:
        return False
        
    try:
        # Ensure remote path is prefixed with plugin name
        remote_path = f"{self.name}/{remote_path}"
        
        # Upload the file
        success = self._cloud_manager.upload_file(local_path, remote_path)
        
        if success:
            self._logger.info(f"Uploaded {local_path} to cloud: {remote_path}")
        else:
            self._logger.error(f"Failed to upload {local_path} to cloud")
            
        return success
    except Exception as e:
        self._logger.error(f"Cloud upload failed: {str(e)}")
        return False

def download_from_cloud(self, remote_path: str, local_path: str) -> bool:
    """Download a file from cloud storage."""
    if not self._cloud_manager:
        return False
        
    try:
        # Ensure remote path is prefixed with plugin name
        remote_path = f"{self.name}/{remote_path}"
        
        # Download the file
        success = self._cloud_manager.download_file(remote_path, local_path)
        
        if success:
            self._logger.info(f"Downloaded {remote_path} from cloud to {local_path}")
        else:
            self._logger.error(f"Failed to download {remote_path} from cloud")
            
        return success
    except Exception as e:
        self._logger.error(f"Cloud download failed: {str(e)}")
        return False

def list_cloud_files(self, prefix: str = "") -> List[Dict[str, Any]]:
    """List files in cloud storage."""
    if not self._cloud_manager:
        return []
        
    try:
        # Ensure prefix is prefixed with plugin name
        remote_prefix = f"{self.name}/{prefix}"
        
        # List files
        files = self._cloud_manager.list_files(remote_prefix)
        
        return files
    except Exception as e:
        self._logger.error(f"Failed to list cloud files: {str(e)}")
        return []
```

## UI Integration

Integrate your plugin with the Qorzen UI.

### Register UI Components

```python
def initialize(self, event_bus: Any, **kwargs: Any) -> None:
    self._event_bus = event_bus
    
    # Register UI components when UI is ready
    self._event_bus.subscribe(
        event_type="ui/ready",
        callback=self._register_ui_components,
        subscriber_id=f"{self.name}_ui_ready_handler"
    )

def _register_ui_components(self, event: Any) -> None:
    """Register plugin UI components when UI is ready."""
    main_window = event.payload.get("main_window")
    if not main_window:
        self._logger.warning("Cannot register UI components: main_window not provided")
        return
        
    try:
        # Create plugin tab
        self._create_plugin_tab(main_window)
        
        self._logger.info("Registered UI components")
    except Exception as e:
        self._logger.error(f"Failed to register UI components: {str(e)}")

def _create_plugin_tab(self, main_window: Any) -> None:
    """Create a plugin tab in the main window."""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem
    
    # Create tab widget
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Add title
    title = QLabel(f"{self.name} Plugin")
    title.setStyleSheet("font-size: 16pt; font-weight: bold;")
    layout.addWidget(title)
    
    # Add description
    description = QLabel(self.description)
    layout.addWidget(description)
    
    # Add button
    refresh_button = QPushButton("Refresh Data")
    refresh_button.clicked.connect(self._refresh_ui_data)
    layout.addWidget(refresh_button)
    
    # Add table
    self._data_table = QTableWidget(0, 3)
    self._data_table.setHorizontalHeaderLabels(["ID", "Name", "Created"])
    layout.addWidget(self._data_table)
    
    # Add to main window
    main_window._central_tabs.addTab(tab, self.name)
    
    # Initialize table data
    self._refresh_ui_data()

def _refresh_ui_data(self) -> None:
    """Refresh the UI data table."""
    if not hasattr(self, '_data_table'):
        return
        
    try:
        # Get data
        items = self.get_items()
        
        # Update table
        self._data_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            self._data_table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
            self._data_table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self._data_table.setItem(row, 2, QTableWidgetItem(item["created_at"]))
            
        self._data_table.resizeColumnsToContents()
    except Exception as e:
        self._logger.error(f"Failed to refresh UI data: {str(e)}")
```

## Best Practices

### Defensive Coding

Always check if core services are available before using them:

```python
def some_method(self) -> None:
    if not self._initialized:
        self._logger.error("Plugin not initialized")
        return
        
    if not self._db_manager:
        self._logger.error("Database manager not available")
        return
```

### Error Handling

Use proper exception handling and logging:

```python
try:
    # Your code here
    result = self._some_operation()
    return result
except SomeSpecificError as e:
    self._logger.warning(f"Operation failed: {str(e)}")
    return None
except Exception as e:
    self._logger.error(f"Unexpected error: {str(e)}")
    return None
```

### Resource Cleanup

Ensure all resources are properly cleaned up:

```python
def shutdown(self) -> None:
    """Clean up resources when plugin is being unloaded."""
    if not self._initialized:
        return
        
    self._logger.info(f"Shutting down {self.name} plugin")
    
    # Unsubscribe from events
    if self._event_bus:
        self._event_bus.unsubscribe(f"{self.name}_subscriber")
    
    # Cancel periodic tasks
    if self._thread_manager:
        if hasattr(self, '_cleanup_task_id'):
            self._thread_manager.cancel_periodic_task(self._cleanup_task_id)
    
    # Close file handles
    # Close database connections
    # Unregister API routes
    
    self._initialized = False
    self._logger.info(f"{self.name} plugin shut down successfully")
```

### Versioning

Use semantic versioning for your plugin:

```python
class YourPlugin:
    name = "your_plugin_name"
    version = "1.0.0"  # MAJOR.MINOR.PATCH
```

### Documentation

Document your plugin thoroughly:

```python
"""
YourPlugin - Description of your plugin

This plugin provides the following features:
1. Feature A - Description
2. Feature B - Description

Configuration options:
- api_key: API key for external service
- endpoint: API endpoint URL
- debug: Enable debug mode

Events published:
- your_plugin/event_a: Description
- your_plugin/event_b: Description

Events subscribed to:
- system/started: Description
- user/login: Description
"""
```

## Troubleshooting

### Common Issues

1. **Plugin Not Loading**
   - Check dependencies are installed
   - Ensure plugin class has required metadata (name, version, description, author)
   - Check for syntax errors

2. **Core Services Not Available**
   - Verify services are properly initialized in `initialize()`
   - Check for typos in service names

3. **Event Subscriptions Not Working**
   - Verify event types match exactly
   - Check subscriber IDs are unique

4. **Database Errors**
   - Verify database connection is active
   - Check SQL syntax
   - Ensure tables exist

### Debugging Techniques

1. **Enable Debug Logging**

```python
def initialize(self, logger_provider: Any, **kwargs: Any) -> None:
    self._logger = logger_provider.get_logger(self.name)
    
    # Set debug level for detailed logging
    # Note: This requires debug logging to be enabled in system config
    self._logger.debug(f"Initializing {self.name} plugin with debug logging")
```

2. **Use Status Reporting**

```python
def get_status(self) -> Dict[str, Any]:
    """Return plugin status information."""
    return {
        "name": self.name,
        "version": self.version,
        "initialized": self._initialized,
        "event_bus_available": self._event_bus is not None,
        "db_available": self._db_manager is not None,
        "config": self._config.get(f"plugins.{self.name}", {}) if self._config else {},
        "items_count": len(self.get_items()) if self._initialized else 0,
        "last_error": getattr(self, "_last_error", None)
    }
```

## Plugin Template

Here's a complete plugin template that you can use as a starting point:

```python
# plugin.py
from __future__ import annotations
import asyncio
import datetime
import json
import time
from typing import Any, Dict, List, Optional, Union

class ExamplePlugin:
    # Required metadata
    name = "example_plugin"
    version = "0.1.0"
    description = "An example plugin for the Qorzen platform"
    author = "Your Name"
    
    # Optional metadata
    dependencies = []  # List of other plugin names this plugin depends on
    
    def __init__(self) -> None:
        # Core service references
        self._event_bus = None
        self._logger = None
        self._config = None
        self._file_manager = None
        self._thread_manager = None
        self._db_manager = None
        self._security_manager = None
        self._api_manager = None
        self._cloud_manager = None
        
        # Plugin state
        self._initialized = False
        self._data_dir = f"{self.name}/data"
        self._periodic_task_ids = []
        
    def initialize(self, 
                   event_bus: Any, 
                   logger_provider: Any, 
                   config_provider: Any, 
                   file_manager: Any, 
                   thread_manager: Any,
                   **kwargs: Any) -> None:
        """Initialize the plugin with Qorzen core services."""
        # Store references to core services
        self._event_bus = event_bus
        self._logger = logger_provider.get_logger(self.name)
        self._config = config_provider
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        
        # Get additional managers
        self._db_manager = kwargs.get('database_manager')
        self._security_manager = kwargs.get('security_manager')
        self._api_manager = kwargs.get('api_manager')
        self._cloud_manager = kwargs.get('cloud_manager')
        
        # Log initialization
        self._logger.info(f"Initializing {self.name} v{self.version} plugin")
        
        # Get plugin configuration
        plugin_config = self._config.get(f"plugins.{self.name}", {})
        self._debug_mode = plugin_config.get("debug", False)
        
        if self._debug_mode:
            self._logger.debug("Debug mode enabled")
        
        # Create plugin data directory
        try:
            self._file_manager.ensure_directory(self._data_dir, directory_type="plugin_data")
        except Exception as e:
            self._logger.error(f"Failed to create data directory: {str(e)}")
        
        # Subscribe to events
        self._event_bus.subscribe(
            event_type="system/started",
            callback=self._on_system_started,
            subscriber_id=f"{self.name}_system_started"
        )
        
        self._event_bus.subscribe(
            event_type="user/login",
            callback=self._on_user_login,
            subscriber_id=f"{self.name}_user_login"
        )
        
        # Register UI components when UI is ready
        self._event_bus.subscribe(
            event_type="ui/ready",
            callback=self._register_ui_components,
            subscriber_id=f"{self.name}_ui_ready"
        )
        
        # Schedule periodic tasks
        task_id = self._thread_manager.schedule_periodic_task(
            interval=60,  # 1 minute
            func=self._periodic_task,
            task_id=f"{self.name}_periodic_task"
        )
        self._periodic_task_ids.append(task_id)
        
        # Register API endpoints
        if self._api_manager:
            self._register_api_endpoints()
        
        # Mark as initialized
        self._initialized = True
        self._logger.info(f"{self.name} plugin initialized successfully")
        
        # Publish initialization event
        self._event_bus.publish(
            event_type=f"{self.name}/initialized",
            source=self.name,
            payload={"version": self.version, "timestamp": datetime.datetime.now().isoformat()}
        )
    
    def shutdown(self) -> None:
        """Clean up resources when plugin is being unloaded."""
        if not self._initialized:
            return
            
        self._logger.info(f"Shutting down {self.name} plugin")
        
        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f"{self.name}_system_started")
            self._event_bus.unsubscribe(f"{self.name}_user_login")
            self._event_bus.unsubscribe(f"{self.name}_ui_ready")
        
        # Cancel periodic tasks
        if self._thread_manager:
            for task_id in self._periodic_task_ids:
                self._thread_manager.cancel_periodic_task(task_id)
        
        # Write state to disk
        try:
            state = {"shutdown_time": datetime.datetime.now().isoformat()}
            self._file_manager.write_text(
                f"{self._data_dir}/shutdown_state.json",
                content=json.dumps(state),
                directory_type="plugin_data"
            )
        except Exception as e:
            self._logger.error(f"Failed to write shutdown state: {str(e)}")
        
        self._initialized = False
        self._logger.info(f"{self.name} plugin shut down successfully")
    
    def _on_system_started(self, event: Any) -> None:
        """Handle system start event."""
        self._logger.info("System started event received")
        
        # Start a background task
        self._thread_manager.submit_task(
            func=self._background_task,
            name=f"{self.name}_init_task",
            submitter=self.name
        )
    
    def _on_user_login(self, event: Any) -> None:
        """Handle user login event."""
        user_id = event.payload.get("user_id")
        username = event.payload.get("username")
        
        self._logger.info(f"User login detected: {username} ({user_id})")
        
        # Log login to plugin data
        try:
            logins_file = f"{self._data_dir}/logins.jsonl"
            
            # Append to logins file
            login_record = {
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            content = json.dumps(login_record) + "\n"
            
            # Create file if it doesn't exist
            try:
                self._file_manager.read_text(logins_file, directory_type="plugin_data")
                append = True
            except:
                append = False
            
            if append:
                # Read existing content
                existing_content = self._file_manager.read_text(logins_file, directory_type="plugin_data")
                # Write updated content
                self._file_manager.write_text(
                    logins_file,
                    content=existing_content + content,
                    directory_type="plugin_data"
                )
            else:
                # Create new file
                self._file_manager.write_text(
                    logins_file,
                    content=content,
                    directory_type="plugin_data"
                )
                
            self._logger.debug(f"Logged user login: {username}")
        except Exception as e:
            self._logger.error(f"Failed to log user login: {str(e)}")
    
    def _background_task(self) -> None:
        """Execute background initialization task."""
        self._logger.info("Starting background initialization task")
        
        try:
            # Simulate work
            time.sleep(2)
            
            # Update initialization state
            init_state = {
                "initialized": True,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self._file_manager.write_text(
                f"{self._data_dir}/init_state.json",
                content=json.dumps(init_state),
                directory_type="plugin_data"
            )
            
            self._logger.info("Background initialization task completed")
        except Exception as e:
            self._logger.error(f"Background initialization task failed: {str(e)}")
    
    def _periodic_task(self) -> None:
        """Execute periodic maintenance task."""
        if not self._initialized:
            return
            
        self._logger.debug("Running periodic task")
        
        try:
            # Update status file
            status = {
                "name": self.name,
                "version": self.version,
                "last_update": datetime.datetime.now().isoformat(),
                "healthy": True
            }
            
            self._file_manager.write_text(
                f"{self._data_dir}/status.json",
                content=json.dumps(status),
                directory_type="plugin_data"
            )
        except Exception as e:
            self._logger.error(f"Periodic task failed: {str(e)}")
    
    def _register_ui_components(self, event: Any) -> None:
        """Register UI components when UI is ready."""
        self._logger.info("UI ready event received")
        
        main_window = event.payload.get("main_window")
        if not main_window:
            self._logger.warning("Cannot register UI components: main_window not provided")
            return
            
        try:
            # Import Qt components
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
            
            # Create plugin tab
            tab = QWidget()
            layout = QVBoxLayout(tab)
            
            # Add plugin information
            title = QLabel(f"{self.name} Plugin")
            title.setStyleSheet("font-size: 16pt; font-weight: bold;")
            layout.addWidget(title)
            
            description = QLabel(self.description)
            layout.addWidget(description)
            
            version = QLabel(f"Version: {self.version}")
            layout.addWidget(version)
            
            author = QLabel(f"Author: {self.author}")
            layout.addWidget(author)
            
            # Add action button
            action_button = QPushButton("Do Something")
            action_button.clicked.connect(self._ui_action)
            layout.addWidget(action_button)
            
            # Add spacer
            layout.addStretch()
            
            # Add tab to main window
            main_window._central_tabs.addTab(tab, self.name.capitalize())
            
            self._logger.info("UI components registered")
        except Exception as e:
            self._logger.error(f"Failed to register UI components: {str(e)}")
    
    def _ui_action(self) -> None:
        """Handle UI action button click."""
        self._logger.info("UI action triggered")
        
        try:
            # Publish event
            self._event_bus.publish(
                event_type=f"{self.name}/action",
                source=self.name,
                payload={"timestamp": datetime.datetime.now().isoformat()}
            )
            
            # Do something
            self._thread_manager.submit_task(
                func=self._background_action,
                name=f"{self.name}_ui_action",
                submitter=self.name
            )
        except Exception as e:
            self._logger.error(f"UI action failed: {str(e)}")
    
    def _background_action(self) -> None:
        """Execute background action task."""
        self._logger.info("Starting background action task")
        
        try:
            # Simulate work
            time.sleep(1)
            
            # Log action
            action_log = {
                "action": "ui_action",
                "timestamp": datetime.datetime.now().isoformat(),
                "success": True
            }
            
            self._file_manager.write_text(
                f"{self._data_dir}/actions.jsonl",
                content=json.dumps(action_log) + "\n",
                directory_type="plugin_data",
                create_dirs=True
            )
            
            self._logger.info("Background action task completed")
        except Exception as e:
            self._logger.error(f"Background action task failed: {str(e)}")
    
    def _register_api_endpoints(self) -> None:
        """Register plugin API endpoints."""
        if not self._api_manager:
            return
            
        try:
            # Get current user dependency
            from fastapi import Depends, HTTPException
            get_current_user = self._api_manager._get_current_user
            
            # Register GET endpoint
            self._api_manager.register_api_endpoint(
                path=f"/api/v1/plugins/{self.name}/status",
                method="get",
                endpoint=self.api_get_status,
                tags=[self.name],
                summary=f"Get {self.name} plugin status",
                description=f"Returns the current status of the {self.name} plugin"
            )
            
            # Register POST endpoint with authentication
            self._api_manager.register_api_endpoint(
                path=f"/api/v1/plugins/{self.name}/action",
                method="post",
                endpoint=self.api_trigger_action,
                tags=[self.name],
                dependencies=[Depends(get_current_user)],
                summary=f"Trigger {self.name} plugin action",
                description=f"Triggers an action in the {self.name} plugin"
            )
            
            self._logger.info("API endpoints registered")
        except Exception as e:
            self._logger.error(f"Failed to register API endpoints: {str(e)}")
    
    async def api_get_status(self) -> Dict[str, Any]:
        """API endpoint to get plugin status."""
        try:
            return {
                "name": self.name,
                "version": self.version,
                "initialized": self._initialized,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            self._logger.error(f"API error: {str(e)}")
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def api_trigger_action(self, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """API endpoint to trigger plugin action."""
        try:
            # Check user permission
            if self._security_manager:
                user_id = current_user.get("id")
                has_permission = self._security_manager.has_permission(
                    user_id, f"plugins.{self.name}", "manage"
                )
                
                if not has_permission:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=403, detail="Permission denied")
            
            # Start background task
            task_id = self._thread_manager.submit_task(
                func=self._api_action_task,
                data=data,
                name=f"{self.name}_api_action",
                submitter=self.name
            )
            
            return {
                "task_id": task_id,
                "accepted": True,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            self._logger.error(f"API error: {str(e)}")
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def _api_action_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API action task."""
        self._logger.info(f"Starting API action task with data: {data}")
        
        try:
            # Simulate work
            time.sleep(1)
            
            # Log action
            action_log = {
                "action": "api_action",
                "data": data,
                "timestamp": datetime.datetime.now().isoformat(),
                "success": True
            }
            
            self._file_manager.write_text(
                f"{self._data_dir}/api_actions.jsonl",
                content=json.dumps(action_log) + "\n",
                directory_type="plugin_data",
                create_dirs=True
            )
            
            self._logger.info("API action task completed")
            
            return {
                "success": True,
                "data": data,
                "processed_at": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            self._logger.error(f"API action task failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_status(self) -> Dict[str, Any]:
        """Return plugin status information."""
        return {
            "name": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "timestamp": datetime.datetime.now().isoformat()
        }
```

This template provides a complete starting point for developing a plugin with the Qorzen framework. You can customize it based on your specific requirements and use cases.