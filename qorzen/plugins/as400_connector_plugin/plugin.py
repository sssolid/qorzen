from __future__ import annotations

"""
Main plugin class for AS400 Connector.

This module provides the entry point for the AS400 Connector Plugin, handling
initialization, configuration, and UI integration with the Qorzen platform.
"""

import os
from typing import Any, Dict, List, Optional, Set, cast
from pathlib import Path

from PySide6.QtWidgets import QAction, QMenu

from qorzen.plugins.as400_connector_plugin.ui.as400_tab import AS400Tab


class AS400ConnectorPlugin:
    """AS400 Connector Plugin for Qorzen platform."""

    # Plugin metadata - required by plugin manager
    name = "as400_connector_plugin"
    version = "0.1.0"
    description = "Connect and query AS400/iSeries databases"
    author = "Qorzen Team"
    dependencies = []  # No dependencies on other plugins

    def __init__(self) -> None:
        """Initialize the AS400 connector plugin."""
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
        self._tab: Optional[AS400Tab] = None
        self._tab_index: Optional[int] = None

    def initialize(
            self,
            event_bus: Any,
            logger_provider: Any,
            config_provider: Any,
            file_manager: Any = None,
            thread_manager: Any = None,
            security_manager: Any = None,
    ) -> None:
        """
        Initialize the plugin with required Qorzen managers.

        Args:
            event_bus: The event bus manager for event handling
            logger_provider: The logger manager for logging
            config_provider: The configuration manager for settings
            file_manager: Optional file manager
            thread_manager: Optional thread manager
            security_manager: Optional security manager
        """
        self._event_bus = event_bus
        self._logger = logger_provider.get_logger(f"plugin.{self.name}")
        self._config = config_provider
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._security_manager = security_manager

        self._logger.info(f"Initializing {self.name} plugin v{self.version}")

        # Create plugin data directory if it doesn't exist
        if self._file_manager:
            try:
                plugin_data_dir = self._file_manager.get_file_path(
                    self.name, directory_type="plugin_data"
                )
                os.makedirs(plugin_data_dir, exist_ok=True)
                self._logger.debug(
                    f"Plugin data directory: {plugin_data_dir}"
                )
            except Exception as e:
                self._logger.warning(
                    f"Failed to create plugin data directory: {str(e)}"
                )

        # Subscribe to events
        self._subscriber_id = self._event_bus.subscribe(
            event_type="ui/main_window_created",
            callback=self._on_main_window_created,
            subscriber_id=f"{self.name}_ui_subscriber",
        )

        # Subscribe to configuration changes
        self._event_bus.subscribe(
            event_type="config/changed",
            callback=self._on_config_changed,
            subscriber_id=f"{self.name}_config_subscriber",
        )

        self._initialized = True
        self._logger.info(f"{self.name} plugin initialized")
        self._event_bus.publish(
            event_type="plugin/initialized",
            source=self.name,
            payload={
                "plugin_name": self.name,
                "version": self.version,
                "has_ui": True,
            },
        )

    def _on_main_window_created(self, event: Any) -> None:
        """
        Handle main window creation event to add UI components.

        Args:
            event: The event containing the main window
        """
        try:
            main_window = event.payload.get("main_window")
            if not main_window:
                self._logger.error("Main window not provided in event payload")
                return

            self._main_window = main_window
            self._logger.debug("Main window reference received")

            # Add the AS400 tab to the main UI
            self._add_tab_to_ui()

            # Add menu items
            self._add_menu_items()

            # Publish UI added event
            self._event_bus.publish(
                event_type=f"plugin/{self.name}/ui_added",
                source=self.name,
                payload={"tab_index": self._tab_index},
            )
        except Exception as e:
            self._logger.error(f"Error handling main window creation: {str(e)}")

    def _add_tab_to_ui(self) -> None:
        """Add the AS400 connector tab to the main UI."""
        if not self._main_window:
            return

        try:
            # Create the AS400 tab
            self._tab = AS400Tab(
                event_bus=self._event_bus,
                logger=self._logger,
                config=self._config,
                file_manager=self._file_manager,
                thread_manager=self._thread_manager,
                security_manager=self._security_manager,
                parent=self._main_window,
            )

            # Add tab to main window's central tab widget
            central_tabs = self._main_window._central_tabs
            if central_tabs:
                self._tab_index = central_tabs.addTab(
                    self._tab, "AS400 Connector"
                )
                self._logger.info(
                    f"Added AS400 tab at index {self._tab_index}"
                )
            else:
                self._logger.error("Central tabs widget not found in main window")
        except Exception as e:
            self._logger.error(f"Error adding AS400 tab to UI: {str(e)}")

    def _add_menu_items(self) -> None:
        """Add AS400 connector menu items to the main menu bar."""
        if not self._main_window:
            return

        try:
            # Add to Tools menu
            tools_menu = None
            for action in self._main_window.menuBar().actions():
                if action.text() == "&Tools":
                    tools_menu = action.menu()
                    break

            if tools_menu:
                # Create submenu for AS400 Connector
                as400_menu = QMenu("AS400 Connector", self._main_window)

                # Add actions to submenu
                connect_action = QAction("Connect to AS400...", self._main_window)
                connect_action.triggered.connect(self._open_connection_dialog)
                as400_menu.addAction(connect_action)

                manage_connections_action = QAction("Manage Connections", self._main_window)
                manage_connections_action.triggered.connect(self._manage_connections)
                as400_menu.addAction(manage_connections_action)

                as400_menu.addSeparator()

                import_action = QAction("Import Queries...", self._main_window)
                import_action.triggered.connect(self._import_queries)
                as400_menu.addAction(import_action)

                export_action = QAction("Export Queries...", self._main_window)
                export_action.triggered.connect(self._export_queries)
                as400_menu.addAction(export_action)

                tools_menu.addSeparator()
                tools_menu.addMenu(as400_menu)

                # Store references to menu items
                self._menu_items.extend([
                    connect_action,
                    manage_connections_action,
                    import_action,
                    export_action
                ])

                self._logger.debug("Added AS400 menu items to Tools menu")
            else:
                self._logger.warning("Tools menu not found in main window")
        except Exception as e:
            self._logger.error(f"Error adding menu items: {str(e)}")

    def _open_connection_dialog(self) -> None:
        """Open the AS400 connection dialog."""
        if self._tab:
            self._tab.open_connection_dialog()
            # Switch to the AS400 tab
            if self._main_window and self._tab_index is not None:
                self._main_window._central_tabs.setCurrentIndex(self._tab_index)

    def _manage_connections(self) -> None:
        """Open the connection management dialog."""
        if self._tab:
            self._tab.open_connection_manager()
            # Switch to the AS400 tab
            if self._main_window and self._tab_index is not None:
                self._main_window._central_tabs.setCurrentIndex(self._tab_index)

    def _import_queries(self) -> None:
        """Import saved queries from a file."""
        if self._tab:
            self._tab.import_queries()

    def _export_queries(self) -> None:
        """Export saved queries to a file."""
        if self._tab:
            self._tab.export_queries()

    def _on_config_changed(self, event: Any) -> None:
        """
        Handle configuration change events.

        Args:
            event: The configuration change event
        """
        if not event.payload.get("key", "").startswith(f"plugins.{self.name}"):
            return

        self._logger.info(
            f"Configuration changed: {event.payload.get('key')} = {event.payload.get('value')}"
        )

        # Forward config changes to the tab if it exists
        if self._tab:
            self._tab.handle_config_change(
                event.payload.get("key"), event.payload.get("value")
            )

    def shutdown(self) -> None:
        """Shut down the plugin and release resources."""
        if not self._initialized:
            return

        self._logger.info(f"Shutting down {self.name} plugin")

        # Clean up UI components
        if self._main_window:
            # Remove tab
            if self._tab and self._tab_index is not None:
                central_tabs = self._main_window._central_tabs
                if central_tabs:
                    central_tabs.removeTab(self._tab_index)
                    self._logger.debug(f"Removed AS400 tab at index {self._tab_index}")

            # Remove menu items
            for action in self._menu_items:
                if action and action.menu():
                    menu = action.menu()
                    menu.clear()
                    menu.deleteLater()
                else:
                    if action and action.parent():
                        action.parent().removeAction(action)

        # Unsubscribe from events
        if self._event_bus:
            if self._subscriber_id:
                self._event_bus.unsubscribe(self._subscriber_id)
            self._event_bus.unsubscribe(f"{self.name}_config_subscriber")
            self._event_bus.publish(
                event_type="plugin/shutdown",
                source=self.name,
                payload={"plugin_name": self.name},
                synchronous=True,
            )

        self._initialized = False
        self._logger.info(f"{self.name} plugin shut down")

    def status(self) -> Dict[str, Any]:
        """
        Get the current status of the plugin.

        Returns:
            Dictionary with plugin status information
        """
        return {
            "name": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "has_ui": True,
            "ui_components": {
                "tab_added": self._tab is not None,
                "tab_index": self._tab_index,
                "menu_items_count": len(self._menu_items),
            },
            "subscriptions": ["ui/main_window_created", "config/changed"],
        }