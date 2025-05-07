# Qorzen Developer Guide

## Introduction

Welcome to the Qorzen Developer Guide. This comprehensive document provides detailed information about the Qorzen platform architecture, its core components, and how they interact. By the end of this guide, you will have a solid understanding of the system and be able to extend, modify, or troubleshoot any part of it.

Qorzen is a modular, extensible platform built with Python, featuring a plugin-based architecture and a robust set of core services. The system is designed to be highly configurable, maintainable, and scalable.

## System Architecture

Qorzen follows a manager-based architecture, where specialized components (managers) provide specific functionality to the system. All managers derive from a common base and follow consistent initialization and shutdown patterns. The platform uses an event-driven approach for inter-component communication, allowing loose coupling between components.

```
    ┌─────────────────────────────────────────┐
    │             ApplicationCore              │
    └─────────────────────────────────────────┘
            │                             ▲
            ▼                             │
    ┌─────────────────────────────────────────┐
    │              ConfigManager              │
    └─────────────────────────────────────────┘
            │                             ▲
            ▼                             │
    ┌─────────────────────────────────────────┐
    │           Core Manager System           │
    │  ┌───────────┐ ┌───────────┐ ┌───────┐  │
    │  │EventBus   │ │Logging    │ │Thread │  │
    │  └───────────┘ └───────────┘ └───────┘  │
    └─────────────────────────────────────────┘
            │                             ▲
            ▼                             │
    ┌─────────────────────────────────────────┐
    │          Service Managers               │
    │  ┌───────────┐ ┌───────────┐ ┌───────┐  │
    │  │Database   │ │File       │ │API    │  │
    │  └───────────┘ └───────────┘ └───────┘  │
    │  ┌───────────┐ ┌───────────┐ ┌───────┐  │
    │  │Security   │ │Remote     │ │Cloud  │  │
    │  └───────────┘ └───────────┘ └───────┘  │
    │  ┌───────────┐ ┌───────────┐           │
    │  │Monitoring │ │Plugin     │           │
    │  └───────────┘ └───────────┘           │
    └─────────────────────────────────────────┘
            │                             ▲
            ▼                             │
    ┌─────────────────────────────────────────┐
    │              Plugin System              │
    │  ┌───────────┐ ┌───────────┐ ┌───────┐  │
    │  │Plugin 1   │ │Plugin 2   │ │Plugin N│  │
    │  └───────────┘ └───────────┘ └───────┘  │
    └─────────────────────────────────────────┘
```

## Core Foundation

### QorzenManager

All managers in the system extend the `QorzenManager` abstract base class, which provides:

```python
class QorzenManager(abc.ABC):
    def __init__(self, name: str) -> None:
        self._name: str = name
        self._initialized: bool = False
        self._healthy: bool = False
    
    @abc.abstractmethod
    def initialize(self) -> None:
        pass
        
    @abc.abstractmethod
    def shutdown(self) -> None:
        pass
        
    def status(self) -> Dict[str, Any]:
        return {
            'name': self._name,
            'initialized': self._initialized,
            'healthy': self._healthy
        }
```

Every manager must implement:
- `initialize()` - Sets up the manager and its resources
- `shutdown()` - Cleans up resources properly
- `status()` - Reports health and operational metrics

## Application Bootstrap

The system bootstrap process follows this order:

1. `ConfigManager` loads first to provide configuration
2. `LoggingManager` initializes next for logging capabilities
3. `EventBusManager` sets up the event pub/sub system
4. `ThreadManager` provides thread pool and task scheduling
5. Other managers initialize based on dependencies
6. `PluginManager` loads last to enable plugins to use all core services

```python
# ApplicationCore initialization sequence
config_manager = ConfigManager(config_path=self._config_path)
config_manager.initialize()

logging_manager = LoggingManager(config_manager)
logging_manager.initialize()

event_bus_manager = EventBusManager(config_manager, logging_manager)
event_bus_manager.initialize()

thread_manager = ThreadManager(config_manager, logging_manager)
thread_manager.initialize()

# ... other managers follow
```

## Core Components

Let's examine each core component in detail:

### ConfigManager

**Purpose**: Manages application configuration from files, environment variables, and runtime updates.

**Key Features**:
- Loads configuration from YAML or JSON files
- Applies environment variable overrides
- Provides notification system for config changes
- Supports hierarchical configuration structure
- Validates configuration against schema

**Usage Example**:
```python
# Get configuration
db_host = config_manager.get('database.host', 'localhost')

# Set configuration (triggers listeners)
config_manager.set('database.pool_size', 10)

# Register for configuration changes
config_manager.register_listener('database', 
                               lambda key, value: print(f"Config changed: {key}={value}"))
```

**Integration Points**:
- All managers receive ConfigManager in their constructor
- ConfigManager triggers events when configuration changes

### LoggingManager

**Purpose**: Provides centralized, structured logging facilities.

**Key Features**:
- Configurable log levels and formats
- Log rotation and retention policies
- File and console output
- Structured JSON logging
- Integration with event bus for log streaming

**Usage Example**:
```python
# Get logger for a component
logger = logging_manager.get_logger('my_component')

# Log messages at different levels
logger.info("Operation completed", extra={"operation_id": op_id})
logger.error("Failed to process item", extra={"item_id": item_id})
```

**Integration Points**:
- All managers receive LoggingManager in their constructor
- LoggingManager publishes log events to EventBusManager

### EventBusManager

**Purpose**: Provides a decoupled pub/sub event system for inter-component communication.

**Key Features**:
- Topic-based publish/subscribe
- Asynchronous event delivery
- Event filtering
- Correlation IDs for tracking related events
- Event type hierarchy

**Usage Example**:
```python
# Subscribe to events
event_bus.subscribe(
    event_type=EventType.DATABASE_CONNECTED,
    callback=self._handle_db_connection,
    subscriber_id='my_component'
)

# Publish events
event_bus.publish(
    event_type=EventType.FILE_CREATED,
    source='file_manager',
    payload={'path': file_path, 'size': file_size}
)
```

**Integration Points**:
- Used by all managers for signaling state changes
- Integrates with UI for reactive updates

### ThreadManager

**Purpose**: Manages thread pools and provides structured concurrency for async tasks.

**Key Features**:
- Thread pool management
- Task scheduling and cancellation
- Periodic task execution
- Task progress reporting
- QT integration for UI thread safety

**Usage Example**:
```python
# Submit a background task
task_id = thread_manager.submit_task(
    func=process_data,
    data_chunk,
    name="data-processing",
    submitter="worker_service"
)

# Schedule a periodic task
timer_id = thread_manager.schedule_periodic_task(
    interval=60.0,
    func=check_updates,
    task_id="update-checker"
)

# Cancel a task
thread_manager.cancel_task(task_id)
```

**Integration Points**:
- Used by managers for background processing
- Integrates with UI thread for Qt applications

### DatabaseManager

**Purpose**: Provides database connectivity, connection pooling, and query execution.

**Key Features**:
- SQLAlchemy integration
- Connection pooling
- Transaction management
- Support for multiple database types
- Query metrics and monitoring
- Async database operations

**Usage Example**:
```python
# Use session context manager for transactions
with database_manager.session() as session:
    session.add(new_record)
    # Auto-commits at context exit, rolls back on exception

# Execute a raw query
results = database_manager.execute_raw(
    "SELECT * FROM users WHERE status = :status", 
    params={"status": "active"}
)

# Use async connection
async with database_manager.async_session() as session:
    result = await session.execute(select(User).filter_by(id=user_id))
```

**Integration Points**:
- Provides Base class for all database models
- Used by other managers for data persistence
- Emits events for database state changes

### FileManager

**Purpose**: Provides safe, managed access to the file system.

**Key Features**:
- Path resolution and security
- File read/write operations
- Directory operations
- Temporary file management
- File locking for concurrent access
- Backup creation

**Usage Example**:
```python
# Read text file
content = file_manager.read_text('config/settings.json')

# Write binary file
file_manager.write_binary('data/image.png', image_data)

# List files in directory
files = file_manager.list_files('data/logs', recursive=True, pattern='*.log')

# Create backup
backup_path = file_manager.create_backup('config/settings.json')
```

**Integration Points**:
- Used by other managers for file operations
- Integrates with plugin system for data storage

### SecurityManager

**Purpose**: Handles authentication, authorization, and security policies.

**Key Features**:
- User management (create, update, delete)
- Authentication with JWT tokens
- Permission-based authorization
- Password policy enforcement
- Token management (refresh, revoke)
- Role-based access control

**Usage Example**:
```python
# Authenticate user
user_data = security_manager.authenticate_user('username', 'password')
# Returns tokens and user info or None if failed

# Check permissions
if security_manager.has_permission(user_id, 'system', 'manage'):
    # Allow system management actions
    
# Create user
user_id = security_manager.create_user(
    username='new_user',
    email='user@example.com',
    password='secure_password',
    roles=[UserRole.USER]
)
```

**Integration Points**:
- Used by APIManager for endpoint security
- Used by plugins for access control
- Emits events for security-related activities

### APIManager

**Purpose**: Provides REST API capabilities for external integration.

**Key Features**:
- FastAPI integration
- OpenAPI documentation
- JWT authentication
- Rate limiting
- CORS configuration
- Versioned API endpoints

**Usage Example**:
```python
# Register a custom API endpoint
api_manager.register_api_endpoint(
    path="/api/v1/custom/endpoint",
    method="get",
    endpoint=my_endpoint_function,
    tags=["Custom"],
    response_model=CustomResponse
)

# Define an endpoint function
async def my_endpoint_function(current_user: Dict[str, Any] = Depends(api_manager._get_current_user)):
    return {"message": "Hello, world!"}
```

**Integration Points**:
- Provides authentication via SecurityManager
- Accesses data via DatabaseManager
- Allows plugins to register custom endpoints

### ResourceMonitoringManager

**Purpose**: Monitors system resources and provides alerts.

**Key Features**:
- CPU, memory, disk monitoring
- Customizable alert thresholds
- Prometheus metrics
- Alert management
- Diagnostic reporting

**Usage Example**:
```python
# Register a custom gauge metric
cpu_gauge = monitoring_manager.register_gauge(
    name='custom_cpu_usage',
    description='Custom CPU usage metric',
    labels=['component']
)

# Set metric value
cpu_gauge.labels(component='worker').set(cpu_percent)

# Get active alerts
alerts = monitoring_manager.get_alerts(include_resolved=False)

# Generate diagnostic report
diagnostic_report = monitoring_manager.generate_diagnostic_report()
```

**Integration Points**:
- Publishes metrics to EventBusManager
- Used by HealthCheck endpoints in API
- Monitors system for all components

### RemoteServicesManager

**Purpose**: Manages connections to external services and APIs.

**Key Features**:
- HTTP/HTTPS client management
- Service health checking
- Authentication handling
- Retry mechanisms
- Async request support

**Usage Example**:
```python
# Register a remote service
remote_manager.register_service(HTTPService(
    name='example-api',
    base_url='https://api.example.com',
    timeout=30.0,
    auth={'type': 'bearer', 'token': api_token}
))

# Make a request to a service
response = remote_manager.make_request(
    service_name='example-api',
    method='GET',
    path='/users',
    params={'active': True}
)

# Check service health
is_healthy = remote_manager.check_service_health('example-api')
```

**Integration Points**:
- Used by other managers for external API calls
- Used by plugins to access remote services
- Emits events for service state changes

### CloudManager

**Purpose**: Provides abstracted access to cloud storage providers.

**Key Features**:
- Multiple cloud provider support (AWS, Azure, GCP)
- Uniform file operations across providers
- Local storage fallback
- File transfer operations

**Usage Example**:
```python
# Upload a file to cloud storage
cloud_manager.upload_file(
    local_path='data/reports/monthly.pdf',
    remote_path='reports/2023/monthly.pdf'
)

# Download a file from cloud storage
cloud_manager.download_file(
    remote_path='templates/invoice.docx',
    local_path='temp/invoice-template.docx'
)

# List files in cloud storage
files = cloud_manager.list_files('backups/')
```

**Integration Points**:
- Used by FileManager for cloud persistence
- Used by plugins for cloud storage access
- Used for backup and restore operations

### PluginManager

**Purpose**: Manages plugin discovery, loading, and lifecycle.

**Key Features**:
- Plugin discovery from multiple sources
- Dependency resolution
- Plugin lifecycle management
- Version compatibility checking
- Installation and uninstallation
- Plugin configuration

**Usage Example**:
```python
# Load a plugin
plugin_manager.load_plugin('example-plugin')

# Unload a plugin
plugin_manager.unload_plugin('example-plugin')

# Install a plugin from package
plugin_manager.install_plugin(
    package_path='plugins/example-plugin-1.0.0.zip',
    skip_verification=False
)

# Get information about all plugins
plugins = plugin_manager.get_all_plugins()
```

**Integration Points**:
- Provides plugins access to all core managers
- Manages extension points for system functionality
- Handles UI integration for plugins

## Plugin System

Qorzen features a robust plugin system that allows developers to extend functionality without modifying the core codebase. This section explains the plugin architecture, how to create plugins, and how to integrate with the application's core services.

### Plugin System Overview

The Qorzen plugin system consists of several components:

1. **Plugin Manager**: Handles discovery, loading, and lifecycle management of plugins
2. **Plugin Manifest**: Defines metadata, capabilities, and dependencies
3. **Plugin Package**: Encapsulates plugin code and resources
4. **Extension Points**: Allow plugins to extend system functionality
5. **UI Integration**: Enable plugins to modify the user interface
6. **Lifecycle Hooks**: Provide control over plugin installation and state changes

### Plugin Structure

A typical Qorzen plugin has the following structure:

```
my-plugin/
├── manifest.json           # Plugin metadata and capabilities
├── code/                   # Python code
│   ├── __init__.py         # Plugin package initialization
│   ├── plugin.py           # Main plugin implementation
│   └── hooks.py            # Lifecycle hooks
├── resources/              # Static resources (images, styles, etc.)
│   └── icons/
├── docs/                   # Documentation
│   └── README.md
└── tests/                  # Unit tests
    └── test_plugin.py
```

### Creating a New Plugin

To create a new plugin, you can use the built-in plugin template generation tool:

```bash
# Using the Qorzen CLI
qorzen-plugin create my-plugin \
    --display-name "My Plugin" \
    --description "A sample plugin for Qorzen" \
    --author-name "Your Name" \
    --author-email "your.email@example.com"

# Using the Python API
from qorzen.plugin_system.tools import create_plugin_template

plugin_dir = create_plugin_template(
    output_dir="plugins",
    plugin_name="my-plugin",
    display_name="My Plugin",
    description="A sample plugin for Qorzen",
    author_name="Your Name",
    author_email="your.email@example.com"
)
```

This creates a skeleton plugin with all the necessary files and directory structure.

### Plugin Manifest

The manifest.json file defines the plugin's metadata, capabilities, and dependencies:

```json
{
  "name": "my-plugin",                    // Unique plugin identifier
  "display_name": "My Plugin",            // Human-readable name
  "version": "1.0.0",                     // Semantic version
  "description": "A sample plugin for Qorzen",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "url": "https://example.com",         // Optional
    "organization": "Your Org"            // Optional
  },
  "license": "MIT",
  "homepage": "https://example.com/my-plugin",
  "capabilities": [                       // Required capabilities
    "ui.extend",
    "event.subscribe",
    "event.publish",
    "config.read"
  ],
  "dependencies": [                       // Other plugins this depends on
    {
      "name": "core",
      "version": ">=0.1.0"
    }
  ],
  "entry_point": "plugin.py",            // Main plugin file
  "min_core_version": "0.1.0",           // Minimum Qorzen version
  "max_core_version": null,              // Optional maximum version
  "tags": ["utility", "ui"],             // Categorization
  "extension_points": [],                // Extension points provided
  "extension_uses": [],                  // Extension points used
  "lifecycle_hooks": {                   // Lifecycle event handlers
    "pre_install": "my_plugin.code.hooks.pre_install",
    "post_install": "my_plugin.code.hooks.post_install"
  },
  "config_schema": {                     // Configuration schema
    "fields": [
      {
        "name": "refresh_interval",
        "type": "integer",
        "label": "Refresh Interval (seconds)",
        "description": "How often to refresh data",
        "default_value": 60,
        "required": true
      }
    ]
  }
}
```

### Main Plugin Implementation

The `plugin.py` file contains the main plugin class, which must implement the `PluginInterface` protocol or extend `BasePlugin`:

```python
from __future__ import annotations
from typing import Any, Dict, List, Optional

from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration

class MyPlugin(BasePlugin):
    """Main plugin class for My Plugin.
    
    This class implements the core functionality of the plugin.
    """
    
    name = "my-plugin"
    version = "1.0.0"
    description = "A sample plugin for Qorzen"
    author = "Your Name"
    dependencies = []
    
    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._timer = None
    
    def initialize(
        self,
        event_bus: Any,
        logger_provider: Any,
        config_provider: Any,
        file_manager: Any,
        thread_manager: Any,
        **kwargs: Any
    ) -> None:
        """Initialize the plugin with the provided managers.
        
        Args:
            event_bus: Event bus for pub/sub
            logger_provider: For creating loggers
            config_provider: Access to configuration
            file_manager: File system operations
            thread_manager: Task scheduling
            **kwargs: Additional dependencies
        """
        super().initialize(
            event_bus, logger_provider, config_provider, 
            file_manager, thread_manager, **kwargs
        )
        
        # Get plugin-specific logger
        self._logger = logger_provider.get_logger(self.name)
        self._logger.info(f"Initializing {self.name} plugin")
        
        # Load configuration
        self._refresh_interval = self._config.get(
            f"plugins.{self.name}.refresh_interval", 
            60
        )
        
        # Subscribe to events
        self._event_bus.subscribe(
            event_type="system/started",
            callback=self._on_system_started,
            subscriber_id=f"{self.name}_system_started"
        )
        
        # Create data directory
        self._data_dir = self._file_manager.get_plugin_data_dir(self.name)
        
        # Start background task
        self._timer = self._thread_manager.schedule_periodic_task(
            interval=self._refresh_interval,
            func=self._refresh_data,
            task_id=f"{self.name}_refresh"
        )
        
        self._logger.info(f"{self.name} plugin initialized")
    
    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Handle UI integration.
        
        Called when the UI is ready for the plugin to add UI elements.
        
        Args:
            ui_integration: Interface for adding UI components
        """
        self._logger.info("Adding UI components")
        
        # Add plugin tab
        self._tab = MyPluginTab()
        ui_integration.add_tab(
            plugin_id=self.name,
            tab=self._tab,
            title="My Plugin"
        )
        
        # Add toolbar
        toolbar = ui_integration.add_toolbar(
            plugin_id=self.name,
            title="My Plugin"
        )
        ui_integration.add_toolbar_action(
            plugin_id=self.name,
            toolbar=toolbar,
            text="Refresh",
            callback=self._refresh_data
        )
        
        # Add menu items
        tools_menu = ui_integration.find_menu("&Tools")
        if tools_menu:
            menu = ui_integration.add_menu(
                plugin_id=self.name,
                title="My Plugin",
                parent_menu=tools_menu
            )
            ui_integration.add_menu_action(
                plugin_id=self.name,
                menu=menu,
                text="Refresh Data",
                callback=self._refresh_data
            )
    
    def _on_system_started(self, event: Any) -> None:
        """Handle system started event."""
        self._logger.info("System started event received")
        self._refresh_data()
    
    def _refresh_data(self) -> None:
        """Refresh plugin data."""
        self._logger.debug("Refreshing data")
        try:
            # Perform data operations
            result = {"timestamp": time.time(), "data": [1, 2, 3]}
            
            # Publish event with results
            if self._event_bus:
                self._event_bus.publish(
                    event_type=f"{self.name}/data_refreshed",
                    source=self.name,
                    payload=result
                )
                
            self._logger.debug("Data refresh completed")
        except Exception as e:
            self._logger.error(f"Error refreshing data: {str(e)}")
    
    def shutdown(self) -> None:
        """Shut down the plugin.
        
        Clean up resources when the plugin is being unloaded.
        """
        self._logger.info(f"Shutting down {self.name} plugin")
        
        # Cancel timer
        if self._timer:
            self._thread_manager.cancel_task(self._timer)
            
        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f"{self.name}_system_started")
        
        # Call parent shutdown
        super().shutdown()
        
        self._logger.info(f"{self.name} plugin shutdown complete")
```

### Plugin Capabilities

Qorzen defines a set of capabilities that plugins can request. These capabilities are security boundaries that control what a plugin can do:

| Capability | Description | Risk |
|------------|-------------|------|
| `config.read` | Read application configuration | Low |
| `config.write` | Modify application configuration | Medium |
| `ui.extend` | Add elements to the user interface | Low |
| `event.subscribe` | Subscribe to application events | Low |
| `event.publish` | Publish events to the event bus | Low |
| `file.read` | Read files from the file system | Low |
| `file.write` | Write files to the file system | High |
| `network.connect` | Connect to external services | Medium |
| `database.read` | Read data from the application database | Medium |
| `database.write` | Write data to the application database | High |
| `system.exec` | Execute system commands | High |
| `system.monitor` | Monitor system resources | Low |
| `plugin.communicate` | Communicate with other plugins | Low |

When installing plugins, users will be informed of the required capabilities and their risk levels.

### Plugin Lifecycle Hooks

Lifecycle hooks allow plugins to execute code during specific events in their lifecycle:

| Hook | Description |
|------|-------------|
| `pre_install` | Before the plugin is installed |
| `post_install` | After the plugin is installed |
| `pre_uninstall` | Before the plugin is uninstalled |
| `post_uninstall` | After the plugin is uninstalled |
| `pre_enable` | Before the plugin is enabled |
| `post_enable` | After the plugin is enabled |
| `pre_disable` | Before the plugin is disabled |
| `post_disable` | After the plugin is disabled |
| `pre_update` | Before the plugin is updated |
| `post_update` | After the plugin is updated |

Lifecycle hooks are defined in the manifest and implemented in a Python module:

```python
from __future__ import annotations
from typing import Dict, Any

def pre_install(context: Dict[str, Any]) -> None:
    """Run before the plugin is installed.
    
    Args:
        context: Installation context containing references to core services
    """
    logger = context.get("logger_manager").get_logger("my-plugin")
    logger.info("Pre-install hook executing")
    
    # Check for dependencies
    try:
        import required_package
        logger.info(f"Found required_package version {required_package.__version__}")
    except ImportError:
        logger.warning("required_package not installed")

def post_install(context: Dict[str, Any]) -> None:
    """Run after the plugin is installed.
    
    Args:
        context: Installation context
    """
    plugins_dir = context.get("plugins_dir")
    install_path = context.get("install_path")
    logger = context.get("logger_manager").get_logger("my-plugin")
    
    logger.info("Post-install hook executing")
    
    # Create data directory
    if install_path:
        data_dir = os.path.join(install_path, "data")
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Created data directory at {data_dir}")
    
    # Set default configuration
    config_manager = context.get("config_manager")
    if config_manager:
        default_config = {
            "refresh_interval": 60,
            "enable_logging": True
        }
        
        for key, value in default_config.items():
            config_path = f"plugins.my-plugin.{key}"
            if config_manager.get(config_path) is None:
                config_manager.set(config_path, value)
```

### Extension Points

Qorzen's extension point system allows plugins to expose functionality that other plugins can use:

1. **Defining an Extension Point**

```python
# In the providing plugin
from qorzen.plugin_system.extension import register_extension_point

class MyPlugin(BasePlugin):
    def initialize(self, event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs):
        # Initialize the plugin
        super().initialize(event_bus, logger_provider, config_provider, file_manager, thread_manager, **kwargs)
        
        # Register extension point
        register_extension_point(
            provider=self.name,
            id="data_processor",
            name="Data Processor",
            description="Process data items from the provider",
            interface="process_item(item: Dict) -> Dict",
            version="1.0.0",
            provider_instance=self
        )

    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data and return the result."""
        # This will be called by extension point implementations
        return {"processed": True, **data}
```

2. **Using an Extension Point**

```python
# In the consuming plugin's manifest.json
{
  "name": "consumer-plugin",
  "extension_uses": [
    {
      "provider": "my-plugin",
      "id": "data_processor",
      "version": "1.0.0",
      "required": true
    }
  ]
}

# In the consuming plugin's code
class ConsumerPlugin(BasePlugin):
    # Implementation method must match the name pattern:
    # {provider}_{extension_id}
    def my_plugin_data_processor(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Implement the data_processor extension point.
        
        This will be automatically discovered and registered.
        """
        # Process the item
        item["consumer_processed"] = True
        return item
```

### UI Integration

Plugins can extend the user interface through the `UIIntegration` interface:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Slot

class MyPluginTab(QWidget):
    """Main tab for the My Plugin."""
    
    update_signal = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        
        # Create UI elements
        title_label = QLabel("My Plugin")
        self._layout.addWidget(title_label)
        
        self._status_label = QLabel("Waiting for data...")
        self._layout.addWidget(self._status_label)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._on_refresh_clicked)
        self._layout.addWidget(refresh_button)
        
        # Connect signal for thread-safe updates
        self.update_signal.connect(self._update_ui)
    
    def get_widget(self) -> QWidget:
        """Return the widget for this component."""
        return self
    
    def on_tab_selected(self) -> None:
        """Called when the tab is selected."""
        pass
    
    def on_tab_deselected(self) -> None:
        """Called when the tab is deselected."""
        pass
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update with new data.
        
        Thread-safe update via signal.
        """
        self.update_signal.emit(data)
    
    @Slot()
    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        # Logic to refresh data goes here
        
    @Slot(dict)
    def _update_ui(self, data: Dict[str, Any]) -> None:
        """Update UI with new data."""
        self._status_label.setText(f"Data updated: {data}")
```

In your plugin's `on_ui_ready` method, you can add various UI components:

```python
def on_ui_ready(self, ui_integration: UIIntegration) -> None:
    """Set up UI components."""
    
    # Add a tab
    self._tab = MyPluginTab()
    ui_integration.add_tab(
        plugin_id=self.name,
        tab=self._tab,
        title="My Plugin"
    )
    
    # Add a toolbar
    toolbar = ui_integration.add_toolbar(
        plugin_id=self.name,
        title="My Plugin"
    )
    
    # Add toolbar actions
    ui_integration.add_toolbar_action(
        plugin_id=self.name,
        toolbar=toolbar,
        text="Refresh",
        callback=self._refresh_data
    )
    
    # Add menu items
    tools_menu = ui_integration.find_menu("&Tools")
    if tools_menu:
        menu = ui_integration.add_menu(
            plugin_id=self.name,
            title="My Plugin",
            parent_menu=tools_menu
        )
        
        # Add menu actions
        ui_integration.add_menu_action(
            plugin_id=self.name,
            menu=menu,
            text="Refresh Data",
            callback=self._refresh_data
        )
    
    # Add a dock widget
    dock_widget = DockWidgetComponent()
    ui_integration.add_dock_widget(
        plugin_id=self.name,
        dock=dock_widget,
        title="My Plugin Dock",
        area="right"  # left, right, top, bottom
    )
```

### Plugin Configuration

Qorzen provides a schema-based configuration system for plugins. The schema is defined in the manifest:

```json
"config_schema": {
  "fields": [
    {
      "name": "refresh_interval",
      "type": "integer",
      "label": "Refresh Interval (seconds)",
      "description": "How often to refresh data",
      "default_value": 60,
      "required": true,
      "order": 1,
      "group": "general",
      "validation_rules": [
        {
          "rule_type": "min",
          "parameters": {"value": 5},
          "error_message": "Refresh interval must be at least 5 seconds"
        },
        {
          "rule_type": "max",
          "parameters": {"value": 3600},
          "error_message": "Refresh interval cannot exceed 1 hour"
        }
      ]
    },
    {
      "name": "enable_logging",
      "type": "boolean",
      "label": "Enable Logging",
      "description": "Whether to log operations",
      "default_value": true,
      "order": 2,
      "group": "general"
    }
  ],
  "groups": [
    {
      "name": "general",
      "label": "General Settings",
      "description": "General plugin settings",
      "order": 1,
      "collapsed": false
    }
  ]
}
```

Field types include:
- `string` - Text input
- `integer` - Numeric input (integers)
- `float` - Numeric input (decimal)
- `boolean` - Toggle/checkbox
- `select` - Dropdown selection
- `multiselect` - Multiple selection
- `color` - Color picker
- `file` - File picker
- `directory` - Directory picker
- `password` - Masked password input
- `json` - JSON editor
- `code` - Code editor
- `datetime` - Date and time picker
- `date` - Date picker
- `time` - Time picker

Accessing configuration in your plugin:

```python
# Get configuration with default fallback
refresh_interval = self._config.get(f"plugins.{self.name}.refresh_interval", 60)

# Update configuration
self._config.set(f"plugins.{self.name}.refresh_interval", 30)

# Listen for configuration changes
self._config.register_listener(
    f"plugins.{self.name}", 
    self._on_config_changed
)

def _on_config_changed(self, key: str, value: Any) -> None:
    """Handle configuration changes."""
    if key == f"plugins.{self.name}.refresh_interval":
        self._refresh_interval = value
        if self._timer:
            # Restart timer with new interval
            self._thread_manager.cancel_task(self._timer)
            self._timer = self._thread_manager.schedule_periodic_task(
                interval=self._refresh_interval,
                func=self._refresh_data,
                task_id=f"{self.name}_refresh"
            )
```

### Plugin Packaging

Once your plugin is ready, you can package it for distribution:

```bash
# Using the CLI
qorzen-plugin package /path/to/my-plugin --format zip

# Using the Python API
from qorzen.plugin_system.tools import package_plugin

package_path = package_plugin(
    plugin_dir="/path/to/my-plugin",
    format=PackageFormat.ZIP,
    signing_key="/path/to/signing_key.json"  # Optional
)
```

### Plugin Installation

Users can install your plugin using:

```bash
# Using the CLI
qorzen-plugin install my-plugin-1.0.0.zip

# Using the Python API
from qorzen.plugin_system.installer import PluginInstaller

installer = PluginInstaller(plugins_dir="plugins")
installer.install_plugin(
    package_path="my-plugin-1.0.0.zip",
    skip_verification=False
)
```

### Plugin Dependencies

Plugins can depend on other plugins, which will be automatically resolved during installation:

```json
"dependencies": [
  {
    "name": "core",
    "version": ">=0.1.0"
  },
  {
    "name": "utility-plugin",
    "version": "^1.2.0",
    "optional": false
  },
  {
    "name": "optional-plugin",
    "version": ">=1.0.0",
    "optional": true
  }
]
```

Version specifiers follow semver conventions:
- `>=1.0.0` - Version 1.0.0 or later
- `>1.0.0` - Version greater than 1.0.0
- `=1.0.0` - Exactly version 1.0.0
- `^1.0.0` - Compatible with 1.0.0 (same major version)
- `~1.0.0` - Compatible with 1.0.0 (same minor version)

### Plugin Repository

Qorzen supports plugin repositories for discovering and sharing plugins:

```python
from qorzen.plugin_system.repository import PluginRepositoryManager

# Set up repository manager
repo_manager = PluginRepositoryManager()
repo_manager.add_repository(
    name="main-repo",
    url="https://plugins.example.com"
)

# Search for plugins
results = repo_manager.search(query="utility")

# Download and install a plugin
package_path = repo_manager.download_plugin(
    plugin_name="utility-plugin",
    version="1.0.0"
)

# Install the downloaded plugin
installer = PluginInstaller(plugins_dir="plugins")
installer.install_plugin(package_path)
```

## Complete Example Plugin

Here's a complete example of a system monitoring plugin that uses many of the features described above:

### 1. Plugin Structure

```
system_monitor/
├── manifest.json
├── code/
│   ├── __init__.py
│   ├── plugin.py
│   └── hooks.py
├── resources/
│   └── icons/
│       └── monitor.png
└── docs/
    └── README.md
```

### 2. Manifest

```json
{
  "name": "system_monitor",
  "display_name": "System Monitor",
  "version": "1.0.0",
  "description": "Real-time system resource monitoring plugin",
  "author": {
    "name": "Qorzen Team",
    "email": "developers@qorzen.com",
    "url": "https://qorzen.com",
    "organization": "Qorzen"
  },
  "license": "MIT",
  "homepage": "https://qorzen.com/plugins/system_monitor",
  "capabilities": [
    "ui.extend",
    "event.subscribe",
    "event.publish",
    "config.read",
    "system.monitor"
  ],
  "dependencies": [
    {
      "name": "core",
      "version": ">=0.1.0"
    }
  ],
  "entry_point": "plugin.py",
  "min_core_version": "0.1.0",
  "tags": ["monitoring", "performance", "system", "resources"],
  "extension_uses": [],
  "lifecycle_hooks": {
    "pre_install": "system_monitor.code.hooks.pre_install",
    "post_install": "system_monitor.code.hooks.post_install",
    "pre_uninstall": "system_monitor.code.hooks.pre_uninstall",
    "post_uninstall": "system_monitor.code.hooks.post_uninstall",
    "pre_update": "system_monitor.code.hooks.pre_update",
    "post_update": "system_monitor.code.hooks.post_update",
    "post_enable": "system_monitor.code.hooks.post_enable",
    "post_disable": "system_monitor.code.hooks.post_disable"
  },
  "config_schema": {
    "fields": [
      {
        "name": "update_interval",
        "type": "float",
        "label": "Update Interval (seconds)",
        "description": "How frequently to update metrics",
        "required": true,
        "default_value": 5.0,
        "order": 1,
        "group": "monitoring",
        "validation_rules": [
          {
            "rule_type": "min",
            "parameters": {"value": 1.0},
            "error_message": "Update interval must be at least 1 second"
          },
          {
            "rule_type": "max",
            "parameters": {"value": 60.0},
            "error_message": "Update interval cannot exceed 60 seconds"
          }
        ]
      },
      {
        "name": "enable_logging",
        "type": "boolean",
        "label": "Enable Metric Logging",
        "description": "Whether to log metrics to a history file",
        "default_value": true,
        "order": 2,
        "group": "monitoring"
      },
      {
        "name": "alert_thresholds.cpu",
        "type": "integer",
        "label": "CPU Alert Threshold (%)",
        "description": "CPU usage percentage that triggers an alert",
        "default_value": 90,
        "order": 1,
        "group": "alerts",
        "validation_rules": [
          {
            "rule_type": "min",
            "parameters": {"value": 50},
            "error_message": "Threshold must be at least 50%"
          },
          {
            "rule_type": "max",
            "parameters": {"value": 100},
            "error_message": "Threshold cannot exceed 100%"
          }
        ]
      },
      {
        "name": "alert_thresholds.memory",
        "type": "integer",
        "label": "Memory Alert Threshold (%)",
        "description": "Memory usage percentage that triggers an alert",
        "default_value": 85,
        "order": 2,
        "group": "alerts"
      }
    ],
    "groups": [
      {
        "name": "monitoring",
        "label": "Monitoring Settings",
        "description": "Settings for the monitoring system",
        "order": 1,
        "collapsed": false
      },
      {
        "name": "alerts",
        "label": "Alert Thresholds",
        "description": "Thresholds for generating alerts",
        "order": 2,
        "collapsed": false
      }
    ]
  }
}
```

### 3. Plugin Implementation

```python
from __future__ import annotations
"""
System Monitor Plugin for Qorzen framework.

This plugin provides real-time monitoring of system resources and performance metrics.
It displays CPU, memory, disk, and network usage in a dedicated tab in the UI.
"""

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

class ResourceWidget(QWidget):
    def __init__(self, title: str, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)
        
        self._title_label = QLabel(title)
        self._title_label.setMinimumWidth(100)
        self._layout.addWidget(self._title_label)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._layout.addWidget(self._progress_bar)
        
        self._value_label = QLabel("0%")
        self._value_label.setMinimumWidth(50)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._layout.addWidget(self._value_label)
    
    def update_value(self, value: float) -> None:
        progress_value = min(100, max(0, int(value)))
        self._progress_bar.setValue(progress_value)
        self._value_label.setText(f"{value:.1f}%")
        self._set_color(value)
    
    def _set_color(self, value: float) -> None:
        if value < 60:
            self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        elif value < 80:
            self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
        else:
            self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")


class SystemMonitorTab(QWidget, TabComponent):
    update_signal = Signal(dict)
    
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        
        title_label = QLabel("System Resource Monitor")
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        self._layout.addWidget(title_label)
        
        self._cpu_widget = ResourceWidget("CPU Usage")
        self._memory_widget = ResourceWidget("Memory Usage")
        self._disk_widget = ResourceWidget("Disk Usage")
        self._network_widget = ResourceWidget("Network Usage")
        
        self._layout.addWidget(self._cpu_widget)
        self._layout.addWidget(self._memory_widget)
        self._layout.addWidget(self._disk_widget)
        self._layout.addWidget(self._network_widget)
        
        self._layout.addStretch()
        
        self._status_label = QLabel("Monitoring system resources...")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._status_label)
        
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_timer_tick)
        self.update_signal.connect(self._update_ui)
        
        self._last_update_time = time.time()
    
    def get_widget(self) -> QWidget:
        return self
    
    def on_tab_selected(self) -> None:
        self._update_timer.start(1000)
    
    def on_tab_deselected(self) -> None:
        self._update_timer.stop()
    
    def update_metrics(self, metrics: Dict[str, float]) -> None:
        self.update_signal.emit(metrics)
    
    @Slot()
    def _update_timer_tick(self) -> None:
        now = time.time()
        elapsed = now - self._last_update_time
        self._status_label.setText(f"Last update: {elapsed:.1f} seconds ago")
    
    @Slot(dict)
    def _update_ui(self, metrics: Dict[str, float]) -> None:
        if "cpu" in metrics:
            self._cpu_widget.update_value(metrics["cpu"])
        if "memory" in metrics:
            self._memory_widget.update_value(metrics["memory"])
        if "disk" in metrics:
            self._disk_widget.update_value(metrics["disk"])
        if "network" in metrics:
            self._network_widget.update_value(metrics["network"])
        
        self._last_update_time = time.time()
        self._status_label.setText("Last update: just now")


class SystemMonitorPlugin(BasePlugin):
    name = "system_monitor"
    version = "1.0.0"
    description = "Real-time system resource monitoring"
    author = "Qorzen Team"
    dependencies = []
    
    def __init__(self) -> None:
        super().__init__()
        self._tab: Optional[SystemMonitorTab] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._metrics: Dict[str, float] = {
            "cpu": 0.0,
            "memory": 0.0,
            "disk": 0.0,
            "network": 0.0
        }
        self._toolbar: Optional[QToolBar] = None
        self._menu: Optional[QMenu] = None
        self._actions: List[Any] = []
    
    def initialize(
        self,
        event_bus: Any,
        logger_provider: Any,
        config_provider: Any,
        file_manager: Any,
        thread_manager: Any,
        **kwargs: Any
    ) -> None:
        super().initialize(
            event_bus, logger_provider, config_provider, 
            file_manager, thread_manager, **kwargs
        )
        
        self._resource_manager = kwargs.get("resource_manager")
        self._logger = logger_provider.get_logger(self.name)
        self._logger.info(f"Initializing {self.name} v{self.version} plugin")
        
        # Load configuration
        self._load_config()
        
        # Subscribe to events
        self._event_bus.subscribe(
            event_type=EventType.SYSTEM_STARTED,
            callback=self._on_system_started,
            subscriber_id=f"{self.name}_system_started"
        )
        
        # Start monitoring thread
        self._start_monitoring()
        
        self._initialized = True
        self._logger.info(f"{self.name} plugin initialized")
    
    def _load_config(self) -> None:
        self._update_interval = self._config.get(
            f"plugins.{self.name}.update_interval", 
            5.0
        )
        self._logger.debug(f"Update interval: {self._update_interval}s")
    
    def _on_system_started(self, event: Event) -> None:
        self._logger.info("System started event received")
        self._publish_metrics()
    
    def _start_monitoring(self) -> None:
        self._logger.info("Starting resource monitoring thread")
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name=f"{self.name}_monitor",
            daemon=True
        )
        self._monitor_thread.start()
    
    def _monitoring_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                self._update_metrics()
                self._publish_metrics()
                
                # Update UI if tab exists
                if self._tab:
                    self._tab.update_metrics(self._metrics)
                
                self._stop_event.wait(self._update_interval)
        except Exception as e:
            self._logger.error(f"Error in monitoring loop: {str(e)}")
    
    def _update_metrics(self) -> None:
        try:
            if self._resource_manager:
                # Use the built-in resource manager if available
                diagnostics = self._resource_manager.generate_diagnostic_report()
                if "system" in diagnostics:
                    system_data = diagnostics["system"]
                    if "cpu" in system_data:
                        self._metrics["cpu"] = system_data["cpu"].get("percent", 0.0)
                    if "memory" in system_data:
                        self._metrics["memory"] = system_data["memory"].get("percent", 0.0)
                    if "disk" in system_data:
                        self._metrics["disk"] = system_data["disk"].get("percent", 0.0)
                    if "network" in system_data:
                        self._metrics["network"] = system_data["network"].get("percent", 0.0)
            else:
                # Fall back to direct metrics gathering
                self._update_basic_metrics()
        except Exception as e:
            self._logger.error(f"Error updating metrics: {str(e)}")
    
    def _update_basic_metrics(self) -> None:
        try:
            # Try to use psutil if available
            import psutil
            
            self._metrics["cpu"] = psutil.cpu_percent(interval=0.5)
            
            memory = psutil.virtual_memory()
            self._metrics["memory"] = memory.percent
            
            disk = psutil.disk_usage("/")
            self._metrics["disk"] = disk.percent
            
            # Network is more complex, use a placeholder
            self._metrics["network"] = 30.0
            
        except ImportError:
            # Fallback to random values if psutil is not available
            import random
            self._metrics = {
                "cpu": random.uniform(20, 80),
                "memory": random.uniform(30, 70),
                "disk": random.uniform(40, 60),
                "network": random.uniform(10, 50)
            }
    
    def _publish_metrics(self) -> None:
        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/metrics",
                source=self.name,
                payload=self._metrics.copy()
            )
    
    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        self._logger.info("Setting up UI components")
        
        # Create and add the tab
        self._tab = SystemMonitorTab()
        tab_index = ui_integration.add_tab(
            plugin_id=self.name,
            tab=self._tab,
            title="System Monitor"
        )
        self._logger.debug(f"Added System Monitor tab at index {tab_index}")
        
        # Add toolbar
        try:
            self._toolbar = ui_integration.add_toolbar(
                plugin_id=self.name,
                title="Monitor"
            )
            
            action = ui_integration.add_toolbar_action(
                plugin_id=self.name,
                toolbar=self._toolbar,
                text="Refresh",
                callback=self._refresh_metrics
            )
            self._actions.append(action)
        except Exception as e:
            self._logger.warning(f"Error adding toolbar: {str(e)}")
        
        # Add menu items
        try:
            tools_menu = ui_integration.find_menu("&Tools")
            if tools_menu:
                self._menu = ui_integration.add_menu(
                    plugin_id=self.name,
                    title="System Monitor",
                    parent_menu=tools_menu
                )
                
                action1 = ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=self._menu,
                    text="Refresh Metrics",
                    callback=self._refresh_metrics
                )
                
                action2 = ui_integration.add_menu_action(
                    plugin_id=self.name,
                    menu=self._menu,
                    text="Generate Report",
                    callback=self._generate_report
                )
                
                self._actions.extend([action1, action2])
        except Exception as e:
            self._logger.warning(f"Error adding menu items: {str(e)}")
        
        # Update the tab with current metrics
        self._tab.update_metrics(self._metrics)
    
    def _refresh_metrics(self) -> None:
        self._logger.info("Manually refreshing metrics")
        self._update_metrics()
        if self._tab:
            self._tab.update_metrics(self._metrics)
        self._publish_metrics()
    
    def _generate_report(self) -> None:
        self._logger.info("Generating system report")
        report = "\n".join([f"{k.upper()}: {v:.1f}%" for k, v in self._metrics.items()])
        self._logger.info(f"System Report:\n{report}")
        
        if self._event_bus:
            self._event_bus.publish(
                event_type=f"{self.name}/report",
                source=self.name,
                payload={
                    "report": report,
                    "timestamp": time.time(),
                    "metrics": self._metrics.copy()
                }
            )
    
    def shutdown(self) -> None:
        self._logger.info(f"Shutting down {self.name} plugin")
        
        # Stop monitoring thread
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(f"{self.name}_system_started")
        
        # Clean up UI references
        self._toolbar = None
        self._menu = None
        self._actions.clear()
        
        # Call parent shutdown
        super().shutdown()
        
        self._logger.info(f"{self.name} plugin shut down successfully")
    
    def status(self) -> Dict[str, Any]:
        status = super().status()
        status.update({
            "metrics": self._metrics,
            "update_interval": self._update_interval,
            "monitoring_active": self._monitor_thread is not None and self._monitor_thread.is_alive(),
            "ui_components": {
                "tab_created": self._tab is not None
            }
        })
        return status
```

### 4. Lifecycle Hooks

```python
from __future__ import annotations
"""
Lifecycle hooks for the System Monitor plugin.

This module contains hooks for different lifecycle events of the plugin,
such as installation, updates, enabling/disabling, etc.
"""

import os
import shutil
import time
from typing import Dict, Any, Optional, cast

def pre_install(context: Dict[str, Any]) -> None:
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("system_monitor")
    
    if logger:
        logger.info("Running pre-install hook for System Monitor plugin")
    
    # Check for dependencies
    try:
        import psutil
        if logger:
            logger.info(f"Found psutil version {psutil.__version__}")
    except ImportError:
        if logger:
            logger.warning("psutil not installed, plugin will use fallback metrics")

def post_install(context: Dict[str, Any]) -> None:
    plugins_dir = context.get("plugins_dir")
    install_path = context.get("install_path")
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("system_monitor")
    
    if logger:
        logger.info("Running post-install hook for System Monitor plugin")
    
    # Create data directory
    if install_path:
        data_dir = os.path.join(install_path, "data")
        os.makedirs(data_dir, exist_ok=True)
        if logger:
            logger.info(f"Created data directory at {data_dir}")
    
    # Set up default configuration
    config_manager = context.get("config_manager")
    if config_manager:
        default_config = {
            "update_interval": 5.0,
            "enable_logging": True,
            "log_history": True,
            "history_retention_days": 7,
            "alert_thresholds": {
                "cpu": 90,
                "memory": 85,
                "disk": 95,
                "network": 80
            }
        }
        
        for key, value in default_config.items():
            config_path = f"plugins.system_monitor.{key}"
            if config_manager.get(config_path) is None:
                config_manager.set(config_path, value)
        
        if logger:
            logger.info("Installed default plugin configuration")

def pre_uninstall(context: Dict[str, Any]) -> None:
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("system_monitor")
    
    if logger:
        logger.info("Running pre-uninstall hook for System Monitor plugin")
    
    # Back up data if keep_data is true
    keep_data = context.get("keep_data", False)
    install_path = context.get("install_path")
    
    if keep_data and install_path:
        data_dir = os.path.join(install_path, "data")
        if os.path.exists(data_dir):
            backup_dir = os.path.join(
                os.path.dirname(install_path),
                f"system_monitor_data_backup_{int(time.time())}"
            )
            
            if logger:
                logger.info(f"Backing up data to {backup_dir}")
            
            try:
                shutil.copytree(data_dir, backup_dir)
                if logger:
                    logger.info("Data backup complete")
            except Exception as e:
                if logger:
                    logger.error(f"Error backing up data: {str(e)}")

def post_uninstall(context: Dict[str, Any]) -> None:
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("system_monitor")
    
    if logger:
        logger.info("Running post-uninstall hook for System Monitor plugin")
    
    # Clean up configuration
    config_manager = context.get("config_manager")
    if config_manager:
        try:
            if config_manager.get("plugins.system_monitor") is not None:
                if logger:
                    logger.info("Would remove plugin configuration here")
        except Exception as e:
            if logger:
                logger.error(f"Error cleaning up configuration: {str(e)}")

def pre_update(context: Dict[str, Any]) -> None:
    current_version = context.get("current_version", "0.0.0")
    new_version = context.get("new_version", "0.0.0")
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("system_monitor")
    
    if logger:
        logger.info(f"Running pre-update hook for System Monitor plugin (updating from v{current_version} to v{new_version})")
    
    # Perform version-specific migrations
    if current_version == "1.0.0" and new_version == "1.1.0":
        if logger:
            logger.info("Would migrate data from v1.0.0 format to v1.1.0 format here")

def post_update(context: Dict[str, Any]) -> None:
    current_version = context.get("current_version", "0.0.0")
    new_version = context.get("new_version", "0.0.0")
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("system_monitor")
    
    if logger:
        logger.info(f"Running post-update hook for System Monitor plugin (updated from v{current_version} to v{new_version})")
    
    # Add new configuration options for the new version
    config_manager = context.get("config_manager")
    if config_manager:
        if new_version == "1.1.0":
            new_configs = {
                "plugins.system_monitor.feature_new_in_1_1": True,
                "plugins.system_monitor.alert_thresholds.gpu": 80
            }
            
            for path, value in new_configs.items():
                if config_manager.get(path) is None:
                    config_manager.set(path, value)
                    if logger:
                        logger.info(f"Added new configuration: {path} = {value}")

def post_enable(context: Dict[str, Any]) -> None:
    # Hook called when the plugin is enabled
    pass

def post_disable(context: Dict[str, Any]) -> None:
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("system_monitor")
    
    if logger:
        logger.info("Running post-disable hook for System Monitor plugin")
```

## Common Patterns

### Initialization and Shutdown

All managers follow a consistent initialization and shutdown pattern:

```python
# Initialization
def initialize(self) -> None:
    try:
        # Setup resources
        # Register event handlers
        # Start background tasks
        
        self._initialized = True
        self._healthy = True
        self._logger.info(f'{self.name} initialized')
    except Exception as e:
        self._logger.error(f'Failed to initialize {self.name}: {str(e)}')
        raise ManagerInitializationError(f'Failed to initialize {self.name}: {str(e)}', 
                                     manager_name=self.name) from e

# Shutdown
def shutdown(self) -> None:
    if not self._initialized:
        return
        
    try:
        # Release resources
        # Unregister event handlers
        # Stop background tasks
        
        self._initialized = False
        self._healthy = False
        self._logger.info(f'{self.name} shut down successfully')
    except Exception as e:
        self._logger.error(f'Failed to shut down {self.name}: {str(e)}')
        raise ManagerShutdownError(f'Failed to shut down {self.name}: {str(e)}', 
                               manager_name=self.name) from e
```

### Configuration Change Handling

Managers can listen for and respond to configuration changes:

```python
def _on_config_changed(self, key: str, value: Any) -> None:
    if key == 'service.port':
        if self._server_running:
            self._logger.warning('Port change requires restart')
        else:
            self._port = value
            self._logger.info(f'Updated port to {value}')
    elif key == 'service.workers':
        self._update_worker_count(value)
```

### Event Publishing

Managers publish events to notify the system of significant state changes:

```python
# Inform system of state change
self._event_bus.publish(
    event_type=EventType.USER_CREATED,
    source='security_manager',
    payload={
        'user_id': user_id,
        'username': username,
        'email': email,
        'roles': [role.value for role in roles]
    }
)
```

### Status Reporting

Managers provide detailed status information:

```python
def status(self) -> Dict[str, Any]:
    status = super().status()
    if self._initialized:
        status.update({
            'connections': {
                'active': len(self._active_connections),
                'idle': len(self._idle_connections),
            },
            'tasks': {
                'pending': self._pending_tasks,
                'completed': self._completed_tasks,
            },
            'metrics': {
                'avg_response_time_ms': self._avg_response_time_ms,
            }
        })
    return status
```

## Best Practices

1. **Manager Dependencies**: When one manager depends on another, pass the dependency in the constructor.

2. **Consistent Error Handling**: Use custom exceptions from qorzen.utils.exceptions.

3. **Configuration Access**: Always use the ConfigManager to access configuration.

4. **Logging**: Use the LoggingManager to get component-specific loggers.

5. **Thread Safety**: Use locks for shared state access.

6. **Resource Cleanup**: Ensure all resources are properly released in shutdown().

7. **Event Documentation**: Document all events published by a component.

8. **Configuration Documentation**: Document all configuration options.

9. **Status Reporting**: Provide detailed status information for monitoring.

10. **Unit Testing**: All managers should have comprehensive unit tests.

11. **Plugin Capabilities**: Request only the capabilities your plugin actually needs.

12. **Plugin Dependencies**: Clearly specify version requirements for dependencies.

13. **UI Integration**: Always handle tab selection/deselection events.

14. **Thread-Safe UI Updates**: Use signals/slots for thread-safe UI updates.

15. **Configuration Validation**: Define proper validation rules for your configuration schema.

16. **Error Handling**: Catch and log errors in background threads.

17. **Lifecycle Hooks**: Implement lifecycle hooks for proper resource management.

## Extension Points

The Qorzen platform provides several extension points:

1. **Event Subscription**: Components can subscribe to events to react to system changes.

2. **API Endpoints**: Custom API endpoints can be registered with APIManager.

3. **Plugins**: The plugin system allows adding new functionality without modifying core code.

4. **Configuration Listeners**: Components can respond to configuration changes.

5. **Custom Metrics**: Add monitoring metrics via ResourceMonitoringManager.

6. **Extension Points**: Plugins can expose functionality for other plugins to use.

7. **UI Extension**: Add tabs, toolbars, menus, and dock widgets to the main interface.

## Troubleshooting

### Manager Initialization Issues

If a manager fails to initialize:

1. Check configuration settings for that manager
2. Verify dependencies are initialized
3. Check logs for specific error messages
4. Ensure required external services are available

### Event System Problems

If events aren't being delivered:

1. Verify EventBusManager is initialized
2. Check subscription registration
3. Verify event types match exactly
4. Check for event queue capacity issues

### Database Connectivity

If database operations fail:

1. Verify connection string
2. Check database server status
3. Look for connection pool exhaustion
4. Check SQL query syntax

### Plugin Issues

If plugins fail to load:

1. Check plugin dependencies
2. Verify plugin compatibility
3. Look for missing resources
4. Check for API version mismatches
5. Examine initialization errors in logs
6. Verify required capabilities are approved

### UI Integration Problems

If plugin UI elements don't appear:

1. Check if on_ui_ready is implemented
2. Verify UI components are properly created
3. Check for exceptions during UI component creation
4. Verify TabComponent interface is implemented correctly

## Conclusion

The Qorzen platform provides a robust, modular foundation for building extensible applications. By understanding the core managers and the plugin system, you can effectively extend the application's functionality without modifying the core codebase.

The plugin system enables you to create reusable, maintainable components that integrate seamlessly with the application. By following the patterns and best practices outlined in this guide, you can ensure your plugins are reliable, performant, and well-integrated with the rest of the system.

Remember that all managers and plugins follow consistent patterns for initialization, shutdown, and status reporting. The event-driven architecture allows for loose coupling between components, making the system more maintainable and testable.