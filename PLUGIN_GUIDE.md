# Qorzen Plugin Development Guide

## Overview

This guide will walk you through creating a plugin for the Qorzen platform. Plugins allow you to extend the functionality of the base application with your own features, including UI components, data processing, and integration with external systems.

## Plugin Structure

A basic plugin requires the following structure:

```
myplugin/
├── __init__.py
├── plugin.py
└── ... (other modules as needed)
```

### Essential Files

1. **__init__.py** - Exports your plugin class
2. **plugin.py** - Contains your main plugin class

## Creating a Plugin

### Step 1: Create the `__init__.py` File

```python
# myplugin/__init__.py
from __future__ import annotations
from myplugin.plugin import MyPlugin

__all__ = ['MyPlugin']
```

### Step 2: Create the `plugin.py` File

```python
# myplugin/plugin.py
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Set, cast
from pathlib import Path
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QObject, Signal, Slot

class MyPlugin(QObject):
    ui_ready_signal = Signal(object)
    
    # Plugin metadata - required
    name = "myplugin"  # Must match directory name
    version = "0.1.0"
    description = "Description of your plugin"
    author = "Your Name"
    dependencies = []  # List other plugin names if needed
    
    def __init__(self) -> None:
        super().__init__()
        self._event_bus = None
        self._logger = None
        self._config = None
        self._file_manager = None
        self._thread_manager = None
        self._security_manager = None
        self._main_window = None
        self._subscriber_id = None
        self._initialized = False
        self._menu_items: List[QAction] = []
        self._tab = None
        self._tab_index: Optional[int] = None
        
        # Connect signal to slot
        self.ui_ready_signal.connect(self._handle_ui_ready_on_main_thread)
    
    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any, 
                  file_manager: Any=None, thread_manager: Any=None, security_manager: Any=None) -> None:
        """
        Initialize the plugin with core services.
        
        This is called by the plugin manager when the plugin is loaded.
        """
        self._event_bus = event_bus
        self._logger = logger_provider.get_logger(f'plugin.{self.name}')
        self._config = config_provider
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._security_manager = security_manager
        
        self._logger.info(f'Initializing {self.name} plugin v{self.version}')
        
        # Create plugin data directory if needed
        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type='plugin_data')
                os.makedirs(plugin_data_dir, exist_ok=True)
                self._logger.debug(f'Plugin data directory: {plugin_data_dir}')
            except Exception as e:
                self._logger.warning(f'Failed to create plugin data directory: {str(e)}')
        
        # Subscribe to events
        self._subscriber_id = self._event_bus.subscribe(
            event_type='ui/ready', 
            callback=self._on_ui_ready_event, 
            subscriber_id=f'{self.name}_ui_subscriber'
        )
        
        self._event_bus.subscribe(
            event_type='config/changed', 
            callback=self._on_config_changed, 
            subscriber_id=f'{self.name}_config_subscriber'
        )
        
        self._initialized = True
        self._logger.info(f'{self.name} plugin initialized')
        
        # Publish initialization event
        self._event_bus.publish(
            event_type='plugin/initialized', 
            source=self.name, 
            payload={'plugin_name': self.name, 'version': self.version, 'has_ui': True}
        )
    
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
    
    def _add_tab_to_ui(self) -> None:
        """Add a tab to the main window."""
        if not self._main_window:
            return
            
        try:
            # Create your tab widget here
            # Example:
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            
            self._tab = QWidget()
            layout = QVBoxLayout(self._tab)
            layout.addWidget(QLabel(f"This is the {self.name} plugin tab"))
            
            # Add tab to main window
            central_tabs = self._main_window._central_tabs
            if central_tabs:
                self._tab_index = central_tabs.addTab(self._tab, self.name)
                self._logger.info(f'Added tab at index {self._tab_index}')
            else:
                self._logger.error('Central tabs widget not found in main window')
        except Exception as e:
            self._logger.error(f'Error adding tab to UI: {str(e)}')
    
    def _add_menu_items(self) -> None:
        """Add menu items to the main window."""
        if not self._main_window:
            return
            
        try:
            # Find Tools menu
            tools_menu = None
            for action in self._main_window.menuBar().actions():
                if action.text() == '&Tools':
                    tools_menu = action.menu()
                    break
                    
            if tools_menu:
                # Create plugin menu
                plugin_menu = QMenu(self.name, self._main_window)
                
                # Add actions to the menu
                action1 = QAction('Action 1', self._main_window)
                action1.triggered.connect(self._action1_handler)
                plugin_menu.addAction(action1)
                
                action2 = QAction('Action 2', self._main_window)
                action2.triggered.connect(self._action2_handler)
                plugin_menu.addAction(action2)
                
                # Add separator and plugin menu to Tools menu
                tools_menu.addSeparator()
                tools_menu.addMenu(plugin_menu)
                
                # Store menu items for cleanup
                self._menu_items.extend([action1, action2])
                
                self._logger.debug('Added menu items to Tools menu')
            else:
                self._logger.warning('Tools menu not found in main window')
        except Exception as e:
            self._logger.error(f'Error adding menu items: {str(e)}')
    
    def _action1_handler(self) -> None:
        """Handler for Action 1."""
        self._logger.info('Action 1 triggered')
        # Implement action handler
    
    def _action2_handler(self) -> None:
        """Handler for Action 2."""
        self._logger.info('Action 2 triggered')
        # Implement action handler
    
    def _on_config_changed(self, event: Any) -> None:
        """Handler for configuration changes."""
        key = event.payload.get('key', '')
        if not key.startswith(f'plugins.{self.name}'):
            return
            
        value = event.payload.get('value')
        self._logger.info(f"Configuration changed: {key} = {value}")
        
        # Handle configuration change
    
    def shutdown(self) -> None:
        """
        Clean up resources when the plugin is unloaded.
        
        This is called by the plugin manager when the plugin is unloaded.
        """
        if not self._initialized:
            return
            
        self._logger.info(f'Shutting down {self.name} plugin')
        
        # Remove UI components
        if self._main_window:
            # Remove tab
            if self._tab and self._tab_index is not None:
                central_tabs = self._main_window._central_tabs
                if central_tabs:
                    central_tabs.removeTab(self._tab_index)
                    self._logger.debug(f'Removed tab at index {self._tab_index}')
            
            # Remove menu items
            for action in self._menu_items:
                if action and action.menu():
                    menu = action.menu()
                    menu.clear()
                    menu.deleteLater()
                elif action and action.parent():
                    action.parent().removeAction(action)
        
        # Unsubscribe from events
        if self._event_bus:
            if self._subscriber_id:
                self._event_bus.unsubscribe(self._subscriber_id)
            self._event_bus.unsubscribe(f'{self.name}_config_subscriber')
            
            # Publish shutdown event
            self._event_bus.publish(
                event_type='plugin/shutdown', 
                source=self.name, 
                payload={'plugin_name': self.name}, 
                synchronous=True
            )
        
        self._initialized = False
        self._logger.info(f'{self.name} plugin shut down')
    
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
            'subscriptions': ['ui/ready', 'config/changed']
        }
```

## Plugin Installation

Plugins can be installed in two ways:

1. **Directory Installation**: Place your plugin directory in the Qorzen `plugins/` directory.
2. **Entry Point Installation**: Distribute your plugin as a Python package with an entry point.

### Entry Point Installation

To distribute your plugin as a Python package, add this to your `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name="myplugin",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'qorzen.plugins': [
            'myplugin = myplugin:MyPlugin',
        ],
    },
)
```

## Core Services

During plugin initialization, several core services are provided:

1. **event_bus**: For publishing and subscribing to events
2. **logger_provider**: For logging plugin activities
3. **config_provider**: For accessing and modifying configuration
4. **file_manager**: For file operations
5. **thread_manager**: For task scheduling and threading
6. **security_manager**: For authentication and authorization

### Using the Event Bus

```python
# Subscribe to an event
subscriber_id = self._event_bus.subscribe(
    event_type='some/event',
    callback=self._event_handler,
    subscriber_id=f'{self.name}_subscriber'
)

# Publish an event
self._event_bus.publish(
    event_type='my/event',
    source=self.name,
    payload={'key': 'value'}
)

# Event handler
def _event_handler(self, event):
    self._logger.info(f"Received event: {event.event_type}")
    payload = event.payload
    # Process event payload
```

### Using the Logger

```python
# Get logger in initialize method
self._logger = logger_provider.get_logger(f'plugin.{self.name}')

# Logging examples
self._logger.debug("Debug message")
self._logger.info("Info message")
self._logger.warning("Warning message")
self._logger.error("Error message", extra={'key': 'value'})
```

### Using the Configuration Provider

```python
# Get configuration value
config_value = self._config.get(f'plugins.{self.name}.some_setting', default_value)

# Set configuration value
self._config.set(f'plugins.{self.name}.some_setting', new_value)

# Handle configuration changes
def _on_config_changed(self, event):
    key = event.payload.get('key')
    value = event.payload.get('value')
    if key == f'plugins.{self.name}.some_setting':
        # Update plugin based on new configuration
        pass
```

### Using the File Manager

```python
# Get path to plugin data directory
plugin_data_dir = self._file_manager.get_file_path(self.name, directory_type='plugin_data')

# Read text file
text_content = self._file_manager.read_text('myfile.txt', directory_type='plugin_data')

# Write text file
self._file_manager.write_text('myfile.txt', 'Hello World', directory_type='plugin_data')

# List files
files = self._file_manager.list_files('', directory_type='plugin_data')
```

### Using the Thread Manager

```python
# Submit a task
task_id = self._thread_manager.submit_task(
    func=self._my_function,
    arg1='value1',
    name='task_name',
    submitter=self.name
)

# Schedule a periodic task
task_id = self._thread_manager.schedule_periodic_task(
    interval=60.0,  # seconds
    func=self._periodic_function,
    task_id='my_periodic_task'
)

# Cancel a task
self._thread_manager.cancel_task(task_id)

# Cancel a periodic task
self._thread_manager.cancel_periodic_task(task_id)
```

## UI Integration

Qorzen provides two main ways to integrate your plugin UI:

1. **Adding a Tab**: Add a tab to the main window's central tab widget
2. **Adding Menu Items**: Add menu items to the Tools menu

### Creating a Custom Tab

For more complex tabs, create a separate class:

```python
# mytab.py
from __future__ import annotations
from typing import Any, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class MyTab(QWidget):
    def __init__(self, event_bus: Any, logger: Any, config: Any, 
                file_manager: Any = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._event_bus = event_bus
        self._logger = logger
        self._config = config
        self._file_manager = file_manager
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Add widgets to layout
        title_label = QLabel("My Plugin Tab")
        layout.addWidget(title_label)
        
        button = QPushButton("Click Me")
        button.clicked.connect(self._on_button_clicked)
        layout.addWidget(button)
        
        layout.addStretch()
    
    def _on_button_clicked(self) -> None:
        self._logger.info("Button clicked")
        # Implement button action
```

And then in your plugin class:

```python
from myplugin.mytab import MyTab

def _add_tab_to_ui(self) -> None:
    if not self._main_window:
        return
        
    try:
        self._tab = MyTab(
            event_bus=self._event_bus,
            logger=self._logger,
            config=self._config,
            file_manager=self._file_manager,
            parent=self._main_window
        )
        
        central_tabs = self._main_window._central_tabs
        if central_tabs:
            self._tab_index = central_tabs.addTab(self._tab, "My Plugin")
            self._logger.info(f'Added tab at index {self._tab_index}')
        else:
            self._logger.error('Central tabs widget not found in main window')
    except Exception as e:
        self._logger.error(f'Error adding tab to UI: {str(e)}')
```

## Plugin Lifecycle

1. **Discovery**: Plugin Manager finds your plugin
2. **Loading**: Plugin Manager instantiates your plugin class
3. **Initialization**: Plugin Manager calls your `initialize()` method
4. **UI Integration**: Your plugin responds to 'ui/ready' event
5. **Active**: Your plugin is running and responding to events
6. **Unloading**: Plugin Manager calls your `shutdown()` method

## Best Practices

1. **Clean Up Resources**: Always clean up resources in the `shutdown()` method
2. **Handle Exceptions**: Wrap all code in try-except blocks to prevent crashes
3. **Use the Logger**: Log all significant actions for debugging
4. **Follow Naming Conventions**: Use consistent naming for events and settings
5. **Separate UI Logic**: Keep UI code separate from business logic
6. **Use Type Hints**: Add type hints to all methods and parameters
7. **Validate Input**: Validate all input data before processing
8. **Store Plugin Data**: Use file_manager with 'plugin_data' directory type
9. **Use Signals and Slots**: For thread-safe UI updates
10. **Document Your Plugin**: Add docstrings to all classes and methods

## Important Events to Monitor

- **ui/ready**: When the main window is ready for UI integration
- **config/changed**: When configuration changes occur
- **plugin/initialized**: When a plugin is initialized
- **plugin/loaded**: When a plugin is loaded
- **plugin/unloaded**: When a plugin is unloaded
- **plugin/error**: When a plugin encounters an error

## Common Patterns

### Loading and Saving Plugin Data

```python
def _load_data(self) -> None:
    try:
        file_path = f'{self.name}/data.json'
        if self._file_manager.get_file_info(file_path, 'plugin_data'):
            json_data = self._file_manager.read_text(file_path, 'plugin_data')
            self._data = json.loads(json_data)
    except Exception as e:
        self._logger.error(f'Failed to load plugin data: {str(e)}')
        self._data = {}

def _save_data(self) -> None:
    try:
        file_path = f'{self.name}/data.json'
        self._file_manager.ensure_directory(self.name, 'plugin_data')
        json_data = json.dumps(self._data, indent=2)
        self._file_manager.write_text(file_path, json_data, 'plugin_data')
    except Exception as e:
        self._logger.error(f'Failed to save plugin data: {str(e)}')
```

### Handling Asynchronous Tasks

```python
def _start_async_task(self) -> None:
    self._thread_manager.submit_task(
        func=self._async_task,
        name='long_running_task',
        submitter=self.name
    )

def _async_task(self) -> None:
    try:
        # Perform long-running task
        # ...
        
        # Signal completion on the main thread
        self._event_bus.publish(
            event_type=f'plugin/{self.name}/task_completed',
            source=self.name,
            payload={'result': 'success'}
        )
    except Exception as e:
        self._logger.error(f'Async task failed: {str(e)}')
        self._event_bus.publish(
            event_type=f'plugin/{self.name}/task_failed',
            source=self.name,
            payload={'error': str(e)}
        )
```

## Troubleshooting

### Plugin Not Loading

1. Check the plugin directory name matches the `name` attribute
2. Ensure `__init__.py` correctly exports your plugin class
3. Check for errors in the log
4. Verify all dependencies are installed

### UI Components Not Appearing

1. Ensure you're subscribing to the 'ui/ready' event
2. Check if the main window reference is valid
3. Look for exceptions in the UI creation code
4. Verify the tab is being added to the central tabs widget

### Plugin Crashing

1. Use try-except blocks around all code
2. Check for errors in the log
3. Ensure all resources are properly initialized
4. Check for thread safety issues

## Conclusion

This guide provides the essentials for creating plugins for the Qorzen platform. By following these patterns and best practices, you can extend the functionality of Qorzen with your own features.

Remember that plugins should be self-contained, clean up their resources, and integrate smoothly with the core application. Well-designed plugins enhance the user experience without compromising stability or performance.