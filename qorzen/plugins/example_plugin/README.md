# Example Plugin

This is a comprehensive example plugin that demonstrates the capabilities of the enhanced Qorzen plugin system.

## Features

This plugin showcases:

- **Configuration Schema** - Define and validate plugin settings
- **Extension Points** - Allow other plugins to extend functionality
- **Lifecycle Hooks** - Execution at key points in the plugin lifecycle
- **UI Integration** - Tabs, menus, and interactive components
- **Event System** - Publishing and subscribing to events

## Installation

1. Download the plugin package
2. Open Qorzen
3. Go to Settings > Plugins
4. Click "Install from file" and select the plugin package
5. Restart Qorzen

## Usage

After installation, you can:

1. Access the plugin from the "Example Plugin" tab in the main interface
2. Use features in the "Demo" section
3. Configure settings in the "Settings" section
4. Explore extension points in the "Extensions" section
5. Access plugin functions from the Tools menu

## Extension Points

This plugin provides two extension points:

### Text Transformer

This extension point allows other plugins to provide text transformation functions.

**Interface**: `func(text: str, options: Optional[Dict[str, Any]] = None) -> str`

To implement this extension point in your plugin:

```python
def example_plugin_text_transform(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
    """
    Implementation of the text.transform extension point from example_plugin.
    
    Args:
        text: The text to transform
        options: Optional transformation options
            
    Returns:
        The transformed text
    """
    return text.upper()  # Example: convert to uppercase
```

### UI Widget Provider

This extension point allows other plugins to provide UI widgets that can be integrated into this plugin.

**Interface**: `func(parent: QWidget) -> QWidget`

To implement this extension point in your plugin:

```python
def example_plugin_ui_widget(self, parent: QWidget) -> QWidget:
    """
    Implementation of the ui.widget extension point from example_plugin.
    
    Args:
        parent: The parent widget
            
    Returns:
        A widget to be displayed in the UI
    """
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
    
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    
    label = QLabel("This is a widget from my plugin")
    layout.addWidget(label)
    
    button = QPushButton("Click Me")
    button.clicked.connect(lambda: label.setText("Button clicked!"))
    layout.addWidget(button)
    
    return widget
```

## Configuration

The plugin provides a comprehensive configuration schema that demonstrates various field types:

- **Text fields** - For username and other text inputs
- **Password fields** - For secure API keys
- **Checkboxes** - For boolean settings
- **Dropdowns** - For selecting from predefined options
- **Numeric fields** - For integer and float values
- **Color pickers** - For selecting colors

Configuration is organized into logical groups and includes validation rules.

## Lifecycle Hooks

This plugin demonstrates all available lifecycle hooks:

- `pre_install` - Called before installation
- `post_install` - Called after installation
- `pre_uninstall` - Called before uninstallation
- `post_uninstall` - Called after uninstallation
- `pre_enable` - Called before enabling
- `post_enable` - Called after enabling
- `pre_disable` - Called before disabling
- `post_disable` - Called after disabling
- `pre_update` - Called before updating
- `post_update` - Called after updating

## Events

The plugin publishes and subscribes to various events:

### Published Events

- `example_plugin/initialized` - When the plugin is initialized
- `example_plugin/transform_text` - When text is transformed
- `example_plugin/settings_changed` - When settings are updated
- Custom events via the demo interface

### Subscribed Events

- `ui/ready` - When the UI is ready
- `config/changed` - When configuration changes
- `*/initialized` - When any plugin is initialized
- `example_plugin/transform_text` - Text transformation events

## Developing with the Example Plugin

This plugin serves as a template for your own plugins. You can use it to:

1. Understand the plugin lifecycle
2. Learn how to create and use extension points
3. Implement proper configuration handling
4. Build effective user interfaces
5. Work with the event system

## License

MIT

## Author

Qorzen Team