"""
Example Plugin - Main plugin class and entry point.

This plugin demonstrates the features of the enhanced Qorzen plugin system, including:
- Extension points
- Lifecycle hooks
- Configuration schema
- UI integration
- Event-based communication
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from PySide6.QtCore import Qt, QObject, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTabWidget, QGroupBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QColorDialog, QFileDialog
)
from PySide6.QtGui import QColor, QIcon

# Import extension point framework
from qorzen.plugin_system.extension import (
    register_extension_point,
    call_extension_point,
    get_extension_point
)


class ExamplePlugin(QObject):
    """
    Main plugin class for Example Plugin.

    This class demonstrates the features of the enhanced plugin system
    and serves as a template for developing new plugins.
    """

    # Plugin metadata (used by the plugin discovery mechanism)
    name = "example_plugin"
    version = "1.0.0"
    description = "An example plugin showcasing the enhanced plugin system features"
    author = "Qorzen Team"

    # Signal to safely update UI from non-UI threads
    ui_update_signal = Signal(dict)

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()

        # Will be set during initialize()
        self.event_bus_manager = None
        self.logger = None
        self.config_provider = None
        self.file_manager = None
        self.thread_manager = None

        # Internal state
        self._initialized = False
        self._config: Dict[str, Any] = {}
        self._main_window = None
        self._tab = None
        self._tab_index: Optional[int] = None
        self._menu_items: List[Any] = []

        # Connect the UI update signal to a slot
        self.ui_update_signal.connect(self._handle_ui_update)

    def initialize(
        self,
        event_bus_manager: Any,
        logger_provider: Any,
        config_provider: Any,
        file_manager: Any,
        thread_manager: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize the plugin with the provided managers.

        Args:
            event_bus_manager: Event bus manager for pub/sub communication
            logger_provider: Logger provider for plugin-specific loggers
            config_provider: Configuration provider for settings
            file_manager: File manager for file operations
            thread_manager: Thread manager for background tasks
            **kwargs: Additional managers or dependencies
        """
        self.event_bus_manager = event_bus_manager
        self.logger = logger_provider.get_logger("example_plugin")
        self.config_provider = config_provider
        self.file_manager = file_manager
        self.thread_manager = thread_manager

        # Load plugin configuration
        self._load_config()

        # Register as a subscriber to various events
        self._register_event_listeners()

        # Register extension points
        self._register_extension_points()

        self.logger.info(f"Example Plugin v{self.version} initialized")
        self._initialized = True

        # Publish an event to signal initialization
        self.event_bus_manager.publish(
            event_type="example_plugin/initialized",
            source="example_plugin",
            payload={"version": self.version}
        )

    def _load_config(self) -> None:
        """Load plugin configuration from config provider."""
        try:
            # Get plugin configuration with defaults from schema
            self._config = self.config_provider.get('plugins.example_plugin', {})

            # Log configuration
            self.logger.debug(f"Loaded configuration: {self._config}")

            # Check if we need to enable logging
            if self._config.get('enable_logging', True):
                log_level_name = self._config.get('log_level', 'info').upper()

                self.logger.info(f"Set log level to {log_level_name}")

            # Create data directory if needed
            if self.file_manager:
                plugin_data_dir = self.file_manager.get_file_path(
                    "example_plugin",
                    directory_type="plugin_data"
                )
                self.file_manager.ensure_directory(plugin_data_dir.as_posix())
                self.logger.debug(f"Plugin data directory: {plugin_data_dir}")

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}", exc_info=True)

    def _register_event_listeners(self) -> None:
        """Register plugin as a listener for various events."""
        # UI-related events
        self.event_bus_manager.subscribe(
            event_type="ui/ready",
            callback=self._on_ui_ready,
            subscriber_id="example_plugin"
        )

        # Configuration changes
        self.event_bus_manager.subscribe(
            event_type="config/changed",
            callback=self._on_config_changed,
            subscriber_id="example_plugin"
        )

        # Subscribe to other plugins' events
        self.event_bus_manager.subscribe(
            event_type="*/initialized",
            callback=self._on_plugin_initialized,
            subscriber_id="example_plugin"
        )

        # Custom events for this plugin
        self.event_bus_manager.subscribe(
            event_type="example_plugin/transform_text",
            callback=self._on_transform_text_event,
            subscriber_id="example_plugin"
        )

    def _register_extension_points(self) -> None:
        """Register extension points provided by this plugin."""
        # Text transformer extension point
        register_extension_point(
            provider="example_plugin",
            id="text.transform",
            name="Text Transformer",
            description="Transform text in various ways",
            interface="func(text: str, options: Optional[Dict[str, Any]] = None) -> str",
            version="1.0.0",
            provider_instance=self
        )

        # UI widget provider extension point
        register_extension_point(
            provider="example_plugin",
            id="ui.widget",
            name="UI Widget Provider",
            description="Provide a UI widget for integration in other plugins",
            interface="func(parent: QWidget) -> QWidget",
            version="1.0.0",
            provider_instance=self
        )

        self.logger.debug("Registered extension points")

    def _on_ui_ready(self, event: Any) -> None:
        """
        Handle UI ready event.

        Args:
            event: Event object containing UI information
        """
        main_window = event.payload.get("main_window")
        if not main_window:
            self.logger.error("No main window in UI ready event")
            return

        self._main_window = main_window

        # Add UI components in the main thread
        self._add_ui_components()

        self.logger.info("UI components added")

    def _add_ui_components(self) -> None:
        """Add UI components to the main window."""
        if not self._main_window:
            return

        # Add plugin tab
        self._add_plugin_tab()

        # Add menu items
        self._add_menu_items()

    def _add_plugin_tab(self) -> None:
        """Add a tab for the plugin to the main window."""
        if not self._main_window:
            return

        try:
            # Create the tab widget
            self._tab = QWidget()
            main_layout = QVBoxLayout(self._tab)

            # Create a tab with multiple sections
            tabs = QTabWidget()
            main_layout.addWidget(tabs)

            # Add demo tab
            demo_tab = self._create_demo_tab()
            tabs.addTab(demo_tab, "Demo")

            # Add settings tab
            settings_tab = self._create_settings_tab()
            tabs.addTab(settings_tab, "Settings")

            # Add extension points tab
            extensions_tab = self._create_extensions_tab()
            tabs.addTab(extensions_tab, "Extensions")

            # Add the tab to the main window
            central_tabs = self._main_window._central_tabs
            if central_tabs:
                self._tab_index = central_tabs.addTab(self._tab, "Example Plugin")

        except Exception as e:
            self.logger.error(f"Error adding plugin tab: {e}", exc_info=True)

    def _create_demo_tab(self) -> QWidget:
        """Create the demo tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_label = QLabel("Example Plugin Demo")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "This example plugin demonstrates the features of the enhanced "
            "Qorzen plugin system. Use the controls below to try out different features."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Text transformation section
        transform_group = QGroupBox("Text Transformation")
        transform_layout = QVBoxLayout(transform_group)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input:"))
        self.text_input = QLineEdit("Hello, World!")
        input_layout.addWidget(self.text_input)
        transform_layout.addLayout(input_layout)

        transform_type_layout = QHBoxLayout()
        transform_type_layout.addWidget(QLabel("Transform:"))
        self.transform_type = QComboBox()
        self.transform_type.addItems(["Uppercase", "Lowercase", "Reverse", "Shuffle"])
        transform_type_layout.addWidget(self.transform_type)
        transform_layout.addLayout(transform_type_layout)

        transform_button = QPushButton("Transform")
        transform_button.clicked.connect(self._on_transform_button_clicked)
        transform_layout.addWidget(transform_button)

        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output:"))
        self.text_output = QLineEdit()
        self.text_output.setReadOnly(True)
        output_layout.addWidget(self.text_output)
        transform_layout.addLayout(output_layout)

        layout.addWidget(transform_group)

        # Event publishing section
        event_group = QGroupBox("Event Publishing")
        event_layout = QVBoxLayout(event_group)

        event_desc = QLabel(
            "Publish an event to the event bus. Other plugins can subscribe to these events."
        )
        event_desc.setWordWrap(True)
        event_layout.addWidget(event_desc)

        event_type_layout = QHBoxLayout()
        event_type_layout.addWidget(QLabel("Event Type:"))
        self.event_type = QComboBox()
        self.event_type.addItems([
            "example_plugin/custom_event",
            "example_plugin/notification",
            "example_plugin/data_update"
        ])
        self.event_type.setEditable(True)
        event_type_layout.addWidget(self.event_type)
        event_layout.addLayout(event_type_layout)

        payload_layout = QHBoxLayout()
        payload_layout.addWidget(QLabel("Payload:"))
        self.event_payload = QLineEdit('{"message": "Hello from Example Plugin!"}')
        payload_layout.addWidget(self.event_payload)
        event_layout.addLayout(payload_layout)

        publish_button = QPushButton("Publish Event")
        publish_button.clicked.connect(self._on_publish_event_clicked)
        event_layout.addWidget(publish_button)

        self.event_result = QLabel("Event publishing result will appear here")
        self.event_result.setWordWrap(True)
        event_layout.addWidget(self.event_result)

        layout.addWidget(event_group)

        # Add a spacer at the bottom
        layout.addStretch(1)

        return tab

    def _create_settings_tab(self) -> QWidget:
        """Create the settings tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_label = QLabel("Plugin Settings")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "This panel demonstrates integration with the configuration system. "
            "Changes made here will be saved to the application configuration."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Credentials group
        creds_group = QGroupBox("Credentials")
        creds_layout = QVBoxLayout(creds_group)

        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit(self._config.get("username", ""))
        username_layout.addWidget(self.username_input)
        creds_layout.addLayout(username_layout)

        apikey_layout = QHBoxLayout()
        apikey_layout.addWidget(QLabel("API Key:"))
        self.apikey_input = QLineEdit(self._config.get("api_key", ""))
        self.apikey_input.setEchoMode(QLineEdit.Password)
        apikey_layout.addWidget(self.apikey_input)
        creds_layout.addLayout(apikey_layout)

        layout.addWidget(creds_group)

        # Advanced settings group
        adv_group = QGroupBox("Advanced Settings")
        adv_layout = QVBoxLayout(adv_group)

        logging_layout = QHBoxLayout()
        self.enable_logging = QCheckBox("Enable Logging")
        self.enable_logging.setChecked(self._config.get("enable_logging", True))
        logging_layout.addWidget(self.enable_logging)
        adv_layout.addLayout(logging_layout)

        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("Log Level:"))
        self.log_level = QComboBox()
        self.log_level.addItems(["debug", "info", "warning", "error"])
        current_level = self._config.get("log_level", "info")
        self.log_level.setCurrentText(current_level)
        log_level_layout.addWidget(self.log_level)
        adv_layout.addLayout(log_level_layout)

        retries_layout = QHBoxLayout()
        retries_layout.addWidget(QLabel("Max Retries:"))
        self.max_retries = QSpinBox()
        self.max_retries.setRange(0, 10)
        self.max_retries.setValue(self._config.get("max_retries", 3))
        retries_layout.addWidget(self.max_retries)
        adv_layout.addLayout(retries_layout)

        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout (seconds):"))
        self.timeout = QDoubleSpinBox()
        self.timeout.setRange(1.0, 120.0)
        self.timeout.setValue(self._config.get("timeout", 30.0))
        timeout_layout.addWidget(self.timeout)
        adv_layout.addLayout(timeout_layout)

        layout.addWidget(adv_group)

        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout(appearance_group)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme = QComboBox()
        self.theme.addItems(["system", "light", "dark", "custom"])
        current_theme = self._config.get("theme", "system")
        self.theme.setCurrentText(current_theme)
        theme_layout.addWidget(self.theme)
        appearance_layout.addLayout(theme_layout)

        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Custom Theme Color:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 30)
        current_color = self._config.get("custom_theme_color", "#3498db")
        self.color_button.setStyleSheet(f"background-color: {current_color}; border: 1px solid black;")
        self.color_button.clicked.connect(self._on_color_button_clicked)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch(1)
        appearance_layout.addLayout(color_layout)

        layout.addWidget(appearance_group)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self._on_save_settings_clicked)
        layout.addWidget(save_button)

        # Update UI state based on current settings
        self.enable_logging.toggled.connect(self._update_logging_controls)
        self.theme.currentTextChanged.connect(self._update_theme_controls)

        # Initial UI state update
        self._update_logging_controls(self.enable_logging.isChecked())
        self._update_theme_controls(self.theme.currentText())

        # Add a spacer at the bottom
        layout.addStretch(1)

        return tab

    def _create_extensions_tab(self) -> QWidget:
        """Create the extensions tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header_label = QLabel("Extension Points")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "This panel demonstrates the extension point system. Other plugins can "
            "implement these extension points to extend functionality."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Text transformer extension
        transform_group = QGroupBox("Text Transformer Extension")
        transform_layout = QVBoxLayout(transform_group)

        transform_desc = QLabel(
            "The text transformer extension point allows other plugins to provide "
            "text transformation functions."
        )
        transform_desc.setWordWrap(True)
        transform_layout.addWidget(transform_desc)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input:"))
        self.ext_text_input = QLineEdit("Hello, World!")
        input_layout.addWidget(self.ext_text_input)
        transform_layout.addLayout(input_layout)

        ext_button = QPushButton("Call Extensions")
        ext_button.clicked.connect(self._on_call_extensions_clicked)
        transform_layout.addWidget(ext_button)

        self.extensions_result = QLabel("No extensions have been called yet")
        self.extensions_result.setWordWrap(True)
        transform_layout.addWidget(self.extensions_result)

        layout.addWidget(transform_group)

        # UI widget extension
        widget_group = QGroupBox("UI Widget Extension")
        widget_layout = QVBoxLayout(widget_group)

        widget_desc = QLabel(
            "The UI widget extension point allows other plugins to provide "
            "UI widgets that can be integrated into this plugin."
        )
        widget_desc.setWordWrap(True)
        widget_layout.addWidget(widget_desc)

        # Container for extension widgets
        self.widget_container = QWidget()
        self.widget_container_layout = QVBoxLayout(self.widget_container)
        self.widget_container_layout.addWidget(
            QLabel("No widget extensions are currently available")
        )
        widget_layout.addWidget(self.widget_container)

        refresh_button = QPushButton("Refresh Widgets")
        refresh_button.clicked.connect(self._load_extension_widgets)
        widget_layout.addWidget(refresh_button)

        layout.addWidget(widget_group)

        # Load extension widgets
        self._load_extension_widgets()

        # Add a spacer at the bottom
        layout.addStretch(1)

        return tab

    def _add_menu_items(self) -> None:
        """Add menu items to the main window."""
        if not self._main_window:
            return

        try:
            # Find the Tools menu
            tools_menu = None
            for action in self._main_window.menuBar().actions():
                if action.text() == '&Tools':
                    tools_menu = action.menu()
                    break

            if not tools_menu:
                self.logger.warning("Tools menu not found")
                return

            # Create a submenu for the plugin
            from PySide6.QtWidgets import QMenu, QAction

            example_menu = QMenu("Example Plugin", self._main_window)

            # Add actions to the submenu
            action1 = QAction("Show Demo", self._main_window)
            action1.triggered.connect(self._on_show_demo_action)
            example_menu.addAction(action1)

            action2 = QAction("Settings...", self._main_window)
            action2.triggered.connect(self._on_show_settings_action)
            example_menu.addAction(action2)

            example_menu.addSeparator()

            action3 = QAction("About Example Plugin", self._main_window)
            action3.triggered.connect(self._on_about_action)
            example_menu.addAction(action3)

            # Add the submenu to the Tools menu
            tools_menu.addSeparator()
            tools_menu.addMenu(example_menu)

            # Store references to menu items
            self._menu_items = [action1, action2, action3, example_menu]

        except Exception as e:
            self.logger.error(f"Error adding menu items: {e}", exc_info=True)

    def _on_show_demo_action(self) -> None:
        """Handle the Show Demo menu action."""
        if self._tab and self._main_window and hasattr(self._main_window, "_central_tabs"):
            # Switch to the plugin's tab
            self._main_window._central_tabs.setCurrentWidget(self._tab)

            # Set focus to the demo tab
            if hasattr(self._tab, "setCurrentIndex"):
                self._tab.setCurrentIndex(0)

    def _on_show_settings_action(self) -> None:
        """Handle the Settings menu action."""
        if self._tab and self._main_window and hasattr(self._main_window, "_central_tabs"):
            # Switch to the plugin's tab
            self._main_window._central_tabs.setCurrentWidget(self._tab)

            # Set focus to the settings tab
            if hasattr(self._tab, "setCurrentIndex"):
                self._tab.setCurrentIndex(1)

    def _on_about_action(self) -> None:
        """Handle the About menu action."""
        try:
            from PySide6.QtWidgets import QMessageBox

            about_text = f"""
            <h1>Example Plugin</h1>
            <p>Version: {self.version}</p>
            <p>Author: {self.author}</p>
            <p>This plugin demonstrates the features of the enhanced Qorzen plugin system.</p>
            """

            QMessageBox.about(self._main_window, "About Example Plugin", about_text)

        except Exception as e:
            self.logger.error(f"Error showing about dialog: {e}", exc_info=True)

    def _on_transform_button_clicked(self) -> None:
        """Handle the Transform button click in the demo tab."""
        try:
            # Get input text
            input_text = self.text_input.text()
            transform_type = self.transform_type.currentText().lower()

            # Perform transformation based on selected type
            if transform_type == "uppercase":
                result = input_text.upper()
            elif transform_type == "lowercase":
                result = input_text.lower()
            elif transform_type == "reverse":
                result = input_text[::-1]
            elif transform_type == "shuffle":
                import random
                chars = list(input_text)
                random.shuffle(chars)
                result = ''.join(chars)
            else:
                result = input_text

            # Update the output field
            self.text_output.setText(result)

            # Also publish an event
            self.event_bus_manager.publish(
                event_type="example_plugin/transform_text",
                source="example_plugin",
                payload={
                    "input": input_text,
                    "transform_type": transform_type,
                    "output": result
                }
            )

        except Exception as e:
            self.logger.error(f"Error transforming text: {e}", exc_info=True)
            self.text_output.setText(f"Error: {str(e)}")

    def _on_publish_event_clicked(self) -> None:
        """Handle the Publish Event button click."""
        try:
            # Get event data
            event_type = self.event_type.currentText()

            try:
                import json
                payload = json.loads(self.event_payload.text())
            except json.JSONDecodeError:
                # If not valid JSON, use as string
                payload = {"message": self.event_payload.text()}

            # Publish the event
            self.event_bus_manager.publish(
                event_type=event_type,
                source="example_plugin",
                payload=payload
            )

            # Update result
            self.event_result.setText(
                f"Event published: {event_type} with payload: {payload}"
            )
            self.event_result.setStyleSheet("color: green;")

        except Exception as e:
            self.logger.error(f"Error publishing event: {e}", exc_info=True)
            self.event_result.setText(f"Error publishing event: {str(e)}")
            self.event_result.setStyleSheet("color: red;")

    def _on_save_settings_clicked(self) -> None:
        """Handle the Save Settings button click."""
        try:
            # Collect settings from UI
            settings = {
                "username": self.username_input.text(),
                "api_key": self.apikey_input.text(),
                "enable_logging": self.enable_logging.isChecked(),
                "log_level": self.log_level.currentText(),
                "max_retries": self.max_retries.value(),
                "timeout": self.timeout.value(),
                "theme": self.theme.currentText(),
            }

            # Add custom theme color if using custom theme
            if settings["theme"] == "custom":
                color = self.color_button.palette().color(self.color_button.backgroundRole())
                settings["custom_theme_color"] = color.name()

            # Save settings to config provider
            for key, value in settings.items():
                self.config_provider.set(f"plugins.example_plugin.{key}", value)

            # Update internal config
            self._config = self.config_provider.get('plugins.example_plugin', {})

            # Show confirmation
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self._tab,
                "Settings Saved",
                "Plugin settings have been saved successfully."
            )

            # Apply settings
            self._apply_settings()

        except Exception as e:
            self.logger.error(f"Error saving settings: {e}", exc_info=True)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self._tab,
                "Error",
                f"Failed to save settings: {str(e)}"
            )

    def _apply_settings(self) -> None:
        """Apply the current settings."""
        # Apply logging settings
        if self._config.get('enable_logging', True):
            log_level_name = self._config.get('log_level', 'info').upper()

            self.logger.info(f"Applied log level: {log_level_name}")

        # Apply theme settings (in a real plugin this would affect UI appearance)
        theme = self._config.get('theme', 'system')
        self.logger.info(f"Applied theme: {theme}")

        # Publish event about settings change
        self.event_bus_manager.publish(
            event_type="example_plugin/settings_changed",
            source="example_plugin",
            payload={"settings": self._config}
        )

    def _on_color_button_clicked(self) -> None:
        """Handle the custom theme color button click."""
        try:
            from PySide6.QtWidgets import QColorDialog

            # Get current color
            current_color = self.color_button.palette().color(self.color_button.backgroundRole())

            # Open color dialog
            color = QColorDialog.getColor(current_color, self._tab, "Select Custom Theme Color")

            if color.isValid():
                # Update button color
                self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

        except Exception as e:
            self.logger.error(f"Error selecting color: {e}", exc_info=True)

    def _update_logging_controls(self, enabled: bool) -> None:
        """Update logging-related controls based on the enable_logging checkbox."""
        self.log_level.setEnabled(enabled)

    def _update_theme_controls(self, theme: str) -> None:
        """Update theme-related controls based on the selected theme."""
        self.color_button.setEnabled(theme == "custom")

    def _on_call_extensions_clicked(self) -> None:
        """Handle the Call Extensions button click."""
        try:
            # Get input text
            input_text = self.ext_text_input.text()

            # Call the extension point
            results = call_extension_point(
                provider="example_plugin",
                extension_id="text.transform",
                text=input_text
            )

            # Display results
            if not results:
                self.extensions_result.setText("No extension implementations found")
                return

            result_text = "Extension results:\n"
            for plugin_name, result in results.items():
                result_text += f"- {plugin_name}: {result}\n"

            self.extensions_result.setText(result_text)

        except Exception as e:
            self.logger.error(f"Error calling extensions: {e}", exc_info=True)
            self.extensions_result.setText(f"Error: {str(e)}")

    def _load_extension_widgets(self) -> None:
        """Load UI widgets from implementing plugins."""
        try:
            # Clear existing widgets
            while self.widget_container_layout.count():
                item = self.widget_container_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Get the extension point
            extension = get_extension_point("example_plugin", "ui.widget")
            if not extension or not extension.implementations:
                self.widget_container_layout.addWidget(
                    QLabel("No widget extensions are currently available")
                )
                return

            # Call each implementation to get widgets
            for plugin_name, implementation in extension.implementations.items():
                try:
                    # Create a group for each plugin's widget
                    group = QGroupBox(f"Widget from {plugin_name}")
                    group_layout = QVBoxLayout(group)

                    # Get the widget from the implementation
                    widget = implementation(self.widget_container)
                    if widget:
                        group_layout.addWidget(widget)
                    else:
                        group_layout.addWidget(QLabel("Widget implementation returned None"))

                    self.widget_container_layout.addWidget(group)

                except Exception as e:
                    self.logger.error(
                        f"Error loading widget from {plugin_name}: {e}",
                        exc_info=True
                    )
                    error_widget = QLabel(f"Error loading widget: {str(e)}")
                    error_widget.setStyleSheet("color: red;")
                    self.widget_container_layout.addWidget(error_widget)

        except Exception as e:
            self.logger.error(f"Error loading extension widgets: {e}", exc_info=True)
            self.widget_container_layout.addWidget(
                QLabel(f"Error loading extensions: {str(e)}")
            )

    def _on_config_changed(self, event: Any) -> None:
        """
        Handle configuration changes.

        Args:
            event: Event object containing configuration change information
        """
        # Check if this is our config that changed
        config_path = event.payload.get('path', '')
        if config_path.startswith('plugins.example_plugin'):
            self.logger.debug(f"Configuration changed: {config_path}")

            # Reload our config
            self._config = self.config_provider.get('plugins.example_plugin', {})

            # Apply settings
            self._apply_settings()

            # Update UI if needed
            if self._tab:
                self.ui_update_signal.emit({"type": "config_changed"})

    def _on_plugin_initialized(self, event: Any) -> None:
        """
        Handle plugin initialized events from other plugins.

        Args:
            event: Event object containing initialization information
        """
        plugin_name = event.source
        if plugin_name != "example_plugin":
            self.logger.info(f"Plugin initialized: {plugin_name}")

            # Check if this is a good time to refresh our extension points
            if self._tab:
                self.ui_update_signal.emit({"type": "refresh_extensions"})

    def _on_transform_text_event(self, event: Any) -> None:
        """
        Handle transform text events.

        Args:
            event: Event object containing text transformation information
        """
        payload = event.payload
        self.logger.debug(f"Received transform_text event: {payload}")

        # In a real plugin, we could do additional processing here
        pass

    @Slot(dict)
    def _handle_ui_update(self, data: Dict[str, Any]) -> None:
        """
        Handle UI updates from different threads.

        Args:
            data: Update data containing the update type and parameters
        """
        update_type = data.get("type", "")

        if update_type == "config_changed":
            # Update UI controls to reflect new configuration
            if hasattr(self, "username_input"):
                self.username_input.setText(self._config.get("username", ""))
            if hasattr(self, "apikey_input"):
                self.apikey_input.setText(self._config.get("api_key", ""))
            if hasattr(self, "enable_logging"):
                self.enable_logging.setChecked(self._config.get("enable_logging", True))
            if hasattr(self, "log_level"):
                self.log_level.setCurrentText(self._config.get("log_level", "info"))
            if hasattr(self, "max_retries"):
                self.max_retries.setValue(self._config.get("max_retries", 3))
            if hasattr(self, "timeout"):
                self.timeout.setValue(self._config.get("timeout", 30.0))
            if hasattr(self, "theme"):
                self.theme.setCurrentText(self._config.get("theme", "system"))
            if hasattr(self, "color_button"):
                color = self._config.get("custom_theme_color", "#3498db")
                self.color_button.setStyleSheet(f"background-color: {color}; border: 1px solid black;")

        elif update_type == "refresh_extensions":
            # Refresh extension points
            if hasattr(self, "_load_extension_widgets"):
                self._load_extension_widgets()

    # Extension point implementation methods
    def text_transform(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Text transform extension point implementation.

        This is our own implementation of the text.transform extension point,
        which adds a prefix to the text.

        Args:
            text: The text to transform
            options: Optional transformation options

        Returns:
            The transformed text
        """
        options = options or {}
        prefix = options.get("prefix", "[Example] ")
        return f"{prefix}{text}"

    # Implement extension point as a method with standard naming pattern
    def example_plugin_text_transform(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Alternative implementation of our own extension point."""
        return self.text_transform(text, options)

    def ui_widget(self, parent: QWidget) -> QWidget:
        """
        UI widget extension point implementation.

        This is our own implementation of the ui.widget extension point,
        which provides a simple UI widget.

        Args:
            parent: The parent widget

        Returns:
            A widget to be displayed in the UI
        """
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)

        label = QLabel("This is a widget from Example Plugin itself")
        layout.addWidget(label)

        button = QPushButton("Click Me")
        button.clicked.connect(lambda: label.setText("Button clicked!"))
        layout.addWidget(button)

        return widget

    # Lifecycle hook methods
    def on_pre_enable(self, context: Dict[str, Any]) -> None:
        """
        Pre-enable lifecycle hook.

        Called before the plugin is enabled.

        Args:
            context: Context information including managers
        """
        # This method is called directly from plugin_manager.py
        if self.logger:
            self.logger.info("Pre-enable hook called")

    def on_post_enable(self, context: Dict[str, Any]) -> None:
        """
        Post-enable lifecycle hook.

        Called after the plugin is enabled.

        Args:
            context: Context information including managers
        """
        # This method is called directly from plugin_manager.py
        if self.logger:
            self.logger.info("Post-enable hook called")

    def on_pre_disable(self, context: Dict[str, Any]) -> None:
        """
        Pre-disable lifecycle hook.

        Called before the plugin is disabled.

        Args:
            context: Context information including managers
        """
        # This method is called directly from plugin_manager.py
        if self.logger:
            self.logger.info("Pre-disable hook called")

    def on_post_disable(self, context: Dict[str, Any]) -> None:
        """
        Post-disable lifecycle hook.

        Called after the plugin is disabled.

        Args:
            context: Context information including managers
        """
        # This method is called directly from plugin_manager.py
        if self.logger:
            self.logger.info("Post-disable hook called")

    def shutdown(self) -> None:
        """
        Shut down the plugin.

        Clean up resources and unsubscribe from events.
        """
        self.logger.info("Shutting down Example Plugin")

        # Unsubscribe from events
        if self.event_bus_manager:
            self.event_bus_manager.unsubscribe(subscriber_id="example_plugin")

        # Clean up resources (if any)

        self._initialized = False
        self.logger.info("Example Plugin shut down successfully")