#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VCdb Explorer Plugin for Qorzen framework.

This plugin provides an interface for querying and exploring VCdb (Vehicle Component Database)
data, with advanced filtering, data table views, and export capabilities.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSplitter,
    QFrame, QMessageBox, QProgressDialog, QFileDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer

from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration, TabComponent

from .database import VCdbDatabase, DatabaseError
from .filter_panel import FilterPanelManager
from .data_table import DataTableWidget
from .export import DataExporter, ExportError


class VCdbExplorerTab(QWidget):
    """Main tab component for the VCdb Explorer plugin."""

    def __init__(
            self,
            database: VCdbDatabase,
            logger: logging.Logger,
            export_settings: Dict[str, Any],
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the VCdb Explorer tab.

        Args:
            database: VCdb database instance
            logger: Logger instance
            export_settings: Export configuration settings
            parent: Parent widget
        """
        super().__init__(parent)
        self._database = database
        self._logger = logger
        self._export_settings = export_settings

        # Set up layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Create title
        title = QLabel("VCdb Explorer")
        title.setStyleSheet("font-weight: bold; font-size: 18px;")
        title.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(title)

        # Create data exporter
        self._exporter = DataExporter(logger)

        # Create components
        self._create_ui_components()

        # Connect signals
        self._connect_signals()

    def get_widget(self) -> QWidget:
        """Get the widget for this tab.

        Returns:
            The tab widget
        """
        return self

    def on_tab_selected(self) -> None:
        """Called when the tab is selected."""
        pass

    def on_tab_deselected(self) -> None:
        """Called when the tab is deselected."""
        pass

    def _create_ui_components(self) -> None:
        """Create the UI components."""
        # Create main splitter
        self._main_splitter = QSplitter(Qt.Vertical)

        # Create filter panels
        self._filter_panel_manager = FilterPanelManager(
            self._database,
            self._logger,
            max_panels=self._export_settings.get("max_filter_panels", 5)
        )

        # Create filter section
        filter_section = QWidget()
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(self._filter_panel_manager)

        # Add run query button
        query_button_layout = QHBoxLayout()
        query_button_layout.addStretch()

        self._run_query_btn = QPushButton("Run Query")
        self._run_query_btn.setMinimumWidth(150)
        self._run_query_btn.clicked.connect(self._execute_query)
        query_button_layout.addWidget(self._run_query_btn)

        query_button_layout.addStretch()
        filter_layout.addLayout(query_button_layout)

        filter_section.setLayout(filter_layout)

        # Create results table
        self._data_table = DataTableWidget(
            self._database,
            self._logger,
            self
        )
        self._data_table.set_run_query_callback(self._execute_query)

        # Add components to splitter
        self._main_splitter.addWidget(filter_section)
        self._main_splitter.addWidget(self._data_table)

        # Set initial sizes (40% filters, 60% results)
        self._main_splitter.setSizes([400, 600])

        # Add to main layout
        self._layout.addWidget(self._main_splitter)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        # Connect filter panel changes to trigger query
        self._filter_panel_manager.filtersChanged.connect(self._on_filters_changed)

    @Slot()
    def _on_filters_changed(self) -> None:
        """Handle filter changes."""
        # We don't auto-execute the query when filters change
        # This would be too resource-intensive and is managed by the Run Query button
        pass

    @Slot()
    def _execute_query(self) -> None:
        """Execute the query with current filters."""
        try:
            # Get all filter panels
            filter_panels = self._filter_panel_manager.get_all_filters()

            # Check if we have any filters
            if not any(filter_panels):
                if QMessageBox.question(
                        self,
                        "No Filters",
                        "You haven't set any filters. This could return a large number of results. Continue?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                ) != QMessageBox.Yes:
                    return

            # Execute query and update table
            self._data_table.execute_query(filter_panels)

        except DatabaseError as e:
            QMessageBox.critical(
                self,
                "Query Error",
                f"Error executing query: {str(e)}"
            )
            self._logger.error(f"Query execution error: {str(e)}")


class VCdbExplorerPlugin(BasePlugin):
    """VCdb Explorer Plugin implementation."""

    name = "vcdb_explorer"
    version = "1.0.0"
    description = "Advanced query tool for exploring Vehicle Component Database"
    author = "Qorzen Developer"
    dependencies = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._tab: Optional[VCdbExplorerTab] = None
        self._database: Optional[VCdbDatabase] = None

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
        self._load_config()

        # Create data directory
        # self._data_dir = self._file_manager.get_plugin_data_dir(self.name)

        # Initialize database
        self._initialize_database()

        self._logger.info(f"{self.name} plugin initialized")

    def _load_config(self) -> None:
        """Load plugin configuration."""
        # Database connection settings
        # TODO: This does not resolve correctly, FIX IT
        self._db_config = {
            'host': self._config.get(f"plugins.{self.name}.database.host", "localhost"),
            'port': self._config.get(f"plugins.{self.name}.database.port", 5432),
            'database': self._config.get(f"plugins.{self.name}.database.name", "vcdb"),
            'user': self._config.get(f"plugins.{self.name}.database.user", "postgres"),
            'password': self._config.get(f"plugins.{self.name}.database.password", ""),
        }

        # UI settings
        self._ui_config = {
            'max_filter_panels': self._config.get(f"plugins.{self.name}.ui.max_filter_panels", 5),
            'default_page_size': self._config.get(f"plugins.{self.name}.ui.default_page_size", 100),
        }

        # Export settings
        self._export_config = {
            'max_rows': self._config.get(f"plugins.{self.name}.export.max_rows", 10000),
        }

        self._logger.debug("Configuration loaded")

    def _initialize_database(self) -> None:
        """Initialize the database connection."""
        try:
            self._database = VCdbDatabase(
                host=self._db_config['host'],
                port=self._db_config['port'],
                database=self._db_config['database'],
                user=self._db_config['user'],
                password=self._db_config['password'],
                logger=self._logger
            )

            self._database.initialize()
            self._logger.info("Database connection initialized")

        except DatabaseError as e:
            self._logger.error(f"Failed to initialize database: {str(e)}")
            # We'll show an error in the UI when it's created

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Handle UI integration.

        Called when the UI is ready for the plugin to add UI elements.

        Args:
            ui_integration: Interface for adding UI components
        """
        self._logger.info("Setting up UI components")

        # Create database status message if there's an error
        if not self._database or not getattr(self._database, '_initialized', False):
            error_widget = QWidget()
            error_layout = QVBoxLayout()

            error_label = QLabel("Database Connection Error")
            error_label.setStyleSheet("font-weight: bold; color: red; font-size: 16px;")
            error_layout.addWidget(error_label)

            message = QLabel(
                "Could not connect to the VCdb database. Please check your configuration."
            )
            error_layout.addWidget(message)

            # Config button
            config_btn = QPushButton("Open Configuration")
            # Connect to configuration UI (would depend on the framework)
            error_layout.addWidget(config_btn)

            error_layout.addStretch()
            error_widget.setLayout(error_layout)

            # Add as tab
            ui_integration.add_tab(
                plugin_id=self.name,
                tab=error_widget,
                title="VCdb Explorer"
            )

            self._logger.warning("Added error tab due to database connection failure")
            return

        # Create the main tab
        self._tab = VCdbExplorerTab(
            self._database,
            self._logger,
            self._export_config,
            None  # parent will be set by the framework
        )

        # Add the tab
        ui_integration.add_tab(
            plugin_id=self.name,
            tab=self._tab,
            title="VCdb Explorer"
        )

        # Add menu items
        tools_menu = ui_integration.find_menu("&Tools")
        if tools_menu:
            menu = ui_integration.add_menu(
                plugin_id=self.name,
                title="VCdb Explorer",
                parent_menu=tools_menu
            )

            ui_integration.add_menu_action(
                plugin_id=self.name,
                menu=menu,
                text="Run Query",
                callback=self._run_query
            )

            ui_integration.add_menu_action(
                plugin_id=self.name,
                menu=menu,
                text="Open Documentation",
                callback=self._open_documentation
            )

        self._logger.info("UI components set up")

    def _run_query(self) -> None:
        """Run the current query (called from menu)."""
        if self._tab:
            self._tab._execute_query()

    def _open_documentation(self) -> None:
        """Open the plugin documentation."""
        # Implementation would depend on the framework
        self._logger.info("Documentation requested")

    def shutdown(self) -> None:
        """Shut down the plugin.

        Clean up resources when the plugin is being unloaded.
        """
        self._logger.info(f"Shutting down {self.name} plugin")

        # Close database connection
        if self._database:
            try:
                self._database.shutdown()
            except Exception as e:
                self._logger.error(f"Error shutting down database: {str(e)}")

        # Clean up UI references
        self._tab = None

        # Call parent shutdown
        super().shutdown()

        self._logger.info(f"{self.name} plugin shutdown complete")