from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QCheckBox, QTabWidget
)


class EventMonitorPlugin:
    """Plugin for monitoring events and diagnosing UI integration issues."""

    name = "event_monitor"
    version = "1.0.0"
    description = "Monitors events and helps diagnose plugin integration issues"
    author = "Support"

    def __init__(self) -> None:
        """Initialize the plugin."""
        self.initialized = False
        self.event_bus_manager = None
        self.logger = None
        self.config_provider = None
        self.file_manager = None
        self.thread_manager = None
        self.plugin_manager = None
        self._main_window = None
        self._tab = None
        self._tab_index = None
        self._event_log = []
        self._event_subscriptions = []

    def initialize(
            self,
            event_bus_manager: Any,
            logger_provider: Any,
            config_provider: Any,
            file_manager: Any,
            thread_manager: Any,
            **kwargs: Any
    ) -> None:
        """Initialize the plugin with the provided managers."""
        self.event_bus_manager = event_bus_manager
        self.logger = logger_provider.get_logger("event_monitor")
        self.config_provider = config_provider
        self.file_manager = file_manager
        self.thread_manager = thread_manager
        self.plugin_manager = kwargs.get("plugin_manager")

        self._subscribe_to_events()
        self.initialized = True
        self.logger.info("Event Monitor plugin initialized")

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events."""
        if not self.event_bus_manager:
            return

        # Subscribe to all events by using wildcard
        subscription_id = self.event_bus_manager.subscribe(
            event_type="*",
            callback=self._on_any_event,
            subscriber_id="event_monitor_all"
        )
        self._event_subscriptions.append(subscription_id)

        # Subscribe to UI ready event specifically to add our UI
        subscription_id = self.event_bus_manager.subscribe(
            event_type="ui/ready",
            callback=self._on_ui_ready,
            subscriber_id="event_monitor_ui"
        )
        self._event_subscriptions.append(subscription_id)

        self.logger.info("Subscribed to events")

    def _on_any_event(self, event: Any) -> None:
        """Handle any event by logging it."""
        try:
            # Skip our own events to avoid recursive logging
            if event.source == "event_monitor":
                return

            # Format the event for logging
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            event_info = {
                "timestamp": timestamp,
                "type": event.event_type,
                "source": event.source,
                "id": event.event_id,
                "payload": event.payload
            }

            # Add to our internal log
            self._event_log.append(event_info)

            # Log it for debugging
            self.logger.debug(
                f"Event: {event.event_type} from {event.source}"
            )

            # Update UI if it exists
            if hasattr(self, "event_text") and self.event_text:
                # Limit to last 100 events to avoid performance issues
                if len(self._event_log) > 100:
                    self._event_log = self._event_log[-100:]

                # Format and display in UI
                self._update_event_display()
        except Exception as e:
            self.logger.error(f"Error handling event: {str(e)}")

    def _update_event_display(self) -> None:
        """Update the event display in the UI."""
        if not hasattr(self, "event_text") or not self.event_text:
            return

        try:
            text = ""
            for event in reversed(self._event_log):
                text += f"{event['timestamp']} - {event['type']} from {event['source']}\n"

                # Add payload details for certain event types
                if event['type'] in ["ui/ready", "plugin/loaded", "plugin/error"]:
                    payload_str = str(event['payload']).replace("{", "{\n  ").replace("}", "\n}").replace(", ", ",\n  ")
                    text += f"  Payload: {payload_str}\n"

                text += "---\n"

            self.event_text.setText(text)
        except Exception as e:
            self.logger.error(f"Error updating event display: {str(e)}")

    def _on_ui_ready(self, event: Any) -> None:
        """Handle UI ready event to add our tab."""
        try:
            self.logger.info("UI ready event received")
            main_window = event.payload.get("main_window")
            if not main_window:
                self.logger.error("Main window not found in UI ready event")
                return

            self._main_window = main_window
            self._add_ui_components()
        except Exception as e:
            self.logger.error(f"Error in UI ready handler: {str(e)}")

    def _add_ui_components(self) -> None:
        """Add UI components to the main window."""
        if not self._main_window:
            return

        try:
            # Create the tab
            self._tab = QTabWidget()

            # Create events tab
            events_tab = QWidget()
            events_layout = QVBoxLayout(events_tab)

            # Header
            header = QLabel("Event Monitor")
            header.setStyleSheet("font-size: 16px; font-weight: bold;")
            events_layout.addWidget(header)

            # Event log
            log_group = QGroupBox("Event Log")
            log_layout = QVBoxLayout(log_group)

            self.event_text = QTextEdit()
            self.event_text.setReadOnly(True)
            self.event_text.setLineWrapMode(QTextEdit.NoWrap)
            log_layout.addWidget(self.event_text)

            # Controls
            controls_layout = QHBoxLayout()

            clear_button = QPushButton("Clear Log")
            clear_button.clicked.connect(self._clear_event_log)
            controls_layout.addWidget(clear_button)

            refresh_button = QPushButton("Refresh")
            refresh_button.clicked.connect(self._update_event_display)
            controls_layout.addWidget(refresh_button)

            log_layout.addLayout(controls_layout)
            events_layout.addWidget(log_group)

            # Add events tab
            self._tab.addTab(events_tab, "Events")

            # Create diagnostics tab
            diag_tab = QWidget()
            diag_layout = QVBoxLayout(diag_tab)

            # Header
            diag_header = QLabel("Plugin UI Integration Diagnostics")
            diag_header.setStyleSheet("font-size: 16px; font-weight: bold;")
            diag_layout.addWidget(diag_header)

            # Diagnostics
            info_group = QGroupBox("Plugin Information")
            info_layout = QVBoxLayout(info_group)

            self.plugin_info_text = QTextEdit()
            self.plugin_info_text.setReadOnly(True)
            info_layout.addWidget(self.plugin_info_text)

            refresh_info_button = QPushButton("Refresh Plugin Info")
            refresh_info_button.clicked.connect(self._refresh_plugin_info)
            info_layout.addWidget(refresh_info_button)

            diag_layout.addWidget(info_group)

            # UI test group
            ui_test_group = QGroupBox("UI Integration Tests")
            ui_test_layout = QVBoxLayout(ui_test_group)

            send_ui_ready_button = QPushButton("Re-send UI Ready Event")
            send_ui_ready_button.clicked.connect(self._send_ui_ready_event)
            ui_test_layout.addWidget(send_ui_ready_button)

            fix_plugin_menu_button = QPushButton("Fix Plugin Menu Integration")
            fix_plugin_menu_button.clicked.connect(self._fix_plugin_menu_integration)
            ui_test_layout.addWidget(fix_plugin_menu_button)

            diag_layout.addWidget(ui_test_group)

            # Add diagnostics tab
            self._tab.addTab(diag_tab, "Diagnostics")

            # Add to main window tabs
            central_tabs = self._main_window._central_tabs
            if central_tabs:
                self._tab_index = central_tabs.addTab(self._tab, "Event Monitor")
                self.logger.info(f"Added tab at index {self._tab_index}")

                # Set our tab as current
                central_tabs.setCurrentIndex(self._tab_index)
            else:
                self.logger.error("Central tabs widget not found in main window")

            # Initial refresh
            self._update_event_display()
            self._refresh_plugin_info()

        except Exception as e:
            self.logger.error(f"Error adding UI components: {str(e)}")

    def _clear_event_log(self) -> None:
        """Clear the event log."""
        self._event_log = []
        if hasattr(self, "event_text") and self.event_text:
            self.event_text.clear()

    def _refresh_plugin_info(self) -> None:
        """Refresh the plugin information display."""
        if not hasattr(self, "plugin_info_text") or not self.plugin_info_text:
            return

        try:
            text = "PLUGIN MANAGER STATUS\n"
            text += "=====================\n\n"

            if not self.plugin_manager:
                text += "Plugin manager not available\n"
            else:
                # Get all plugins
                all_plugins = self.plugin_manager.get_all_plugins()

                text += f"Total plugins: {len(all_plugins)}\n\n"

                for plugin in all_plugins:
                    name = plugin.get("name", "Unknown")
                    version = plugin.get("version", "Unknown")
                    state = plugin.get("state", "Unknown")
                    error = plugin.get("error", "")

                    text += f"Plugin: {name} v{version}\n"
                    text += f"State: {state}\n"
                    if error:
                        text += f"Error: {error}\n"

                    # Instance check for UI integration
                    instance = plugin.get("instance")
                    if instance:
                        text += "Has instance: YES\n"

                        # Check if it's added to UI
                        if hasattr(instance, "_tab_index") and instance._tab_index is not None:
                            text += f"UI Tab Index: {instance._tab_index}\n"
                        else:
                            text += "UI Tab Index: None\n"

                        # Check menu items
                        if hasattr(instance, "_menu_items") and instance._menu_items:
                            text += f"Menu Items: {len(instance._menu_items)}\n"
                        else:
                            text += "Menu Items: None\n"
                    else:
                        text += "Has instance: NO\n"

                    text += "\n---\n\n"

            self.plugin_info_text.setText(text)
        except Exception as e:
            self.logger.error(f"Error refreshing plugin info: {str(e)}")
            self.plugin_info_text.setText(f"Error: {str(e)}")

    def _send_ui_ready_event(self) -> None:
        """Re-send the UI ready event."""
        if not self.event_bus_manager or not self._main_window:
            self.logger.error("Event bus or main window not available")
            return

        try:
            self.logger.info("Manually sending UI ready event")
            self.event_bus_manager.publish(
                event_type="ui/ready",
                source="event_monitor",
                payload={"main_window": self._main_window}
            )
        except Exception as e:
            self.logger.error(f"Error sending UI ready event: {str(e)}")

    def _fix_plugin_menu_integration(self) -> None:
        """Fix issues with plugin menu integration."""
        if not self._main_window:
            self.logger.error("Main window not available")
            return

        try:
            # Check for Tools menu
            tools_menu = None
            for action in self._main_window.menuBar().actions():
                if action.text() == '&Tools':
                    tools_menu = action.menu()
                    break

            if not tools_menu:
                self.logger.error("Tools menu not found")
                return

            # Reinstall plugin menu items
            if self.plugin_manager:
                all_plugins = self.plugin_manager.get_all_plugins()
                for plugin in all_plugins:
                    instance = plugin.get("instance")
                    if instance and hasattr(instance, "_add_menu_items"):
                        name = plugin.get("name", "Unknown")
                        try:
                            self.logger.info(f"Re-adding menu items for {name}")
                            instance._add_menu_items()
                        except Exception as e:
                            self.logger.error(f"Error re-adding menu items for {name}: {str(e)}")

            self.logger.info("Attempted to fix plugin menu integration")
        except Exception as e:
            self.logger.error(f"Error fixing plugin menu integration: {str(e)}")

    def shutdown(self) -> None:
        """Shut down the plugin."""
        if not self.initialized:
            return

        try:
            self.logger.info("Shutting down Event Monitor plugin")

            # Unsubscribe from events
            if self.event_bus_manager:
                for subscription_id in self._event_subscriptions:
                    self.event_bus_manager.unsubscribe(subscription_id)

            self.initialized = False
            self.logger.info("Event Monitor plugin shut down")
        except Exception as e:
            self.logger.error(f"Error shutting down plugin: {str(e)}")