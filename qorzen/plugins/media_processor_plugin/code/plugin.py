from __future__ import annotations

"""
Media Processor Plugin.

This plugin provides advanced image processing capabilities including background removal,
batch processing, and configurable output formats for various media files.
"""

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
from qorzen.plugin_system.lifecycle import (
    get_plugin_state,
    set_plugin_state,
    PluginLifecycleState,
    signal_ui_ready
)
from qorzen.ui.ui_integration import UIIntegration

from .models.processing_config import ProcessingConfig, BackgroundRemovalConfig, OutputFormat
from .ui.main_widget import MediaProcessorWidget
from .ui.batch_dialog import BatchProcessingDialog
from .ui.config_editor import ConfigEditorDialog
from .processors.media_processor import MediaProcessor
from .processors.batch_processor import BatchProcessor
from .utils.exceptions import MediaProcessingError


class MediaProcessorPlugin(BasePlugin):
    """
    Plugin for advanced media processing with background removal and batch operations.

    This plugin provides:
    - Image processing with background removal capabilities
    - Multiple configurable output formats
    - Batch processing with progress tracking
    - Save/load processing configurations
    """

    name = "media_processor"
    version = "1.0.0"
    description = "Advanced media processing with background removal, batch processing, and multiple output formats"
    author = "Qorzen Developer"
    display_name = "Media Processor"
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the media processor plugin."""
        super().__init__()
        self._logger: Optional[logging.Logger] = None
        self._main_widget: Optional[MediaProcessorWidget] = None
        self._event_bus_manager: Optional[EventBusManager] = None
        self._concurrency_manager: Optional[ConcurrencyManager] = None
        self._task_manager: Optional[TaskManager] = None
        self._file_manager: Optional[FileManager] = None
        self._config_manager: Optional[ConfigManager] = None

        self._media_processor: Optional[MediaProcessor] = None
        self._batch_processor: Optional[BatchProcessor] = None

        self._plugin_config: Dict[str, Any] = {}
        self._ui_components_created = False
        self._icon_path: Optional[str] = None

        # Track active batch processing jobs
        self._active_jobs: Set[str] = set()

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin.

        Args:
            application_core: The main application core
            **kwargs: Additional keyword arguments
        """
        await super().initialize(application_core, **kwargs)

        # Set up logger
        self._logger = self._logger or logging.getLogger(self.name)
        self._logger.info(f"Initializing {self.name} plugin")

        # Get core services
        self._event_bus_manager = self._event_bus_manager or application_core.get_manager("event_bus_manager")
        self._concurrency_manager = self._concurrency_manager or application_core.get_manager("concurrency_manager")
        self._task_manager = self._task_manager or application_core.get_manager("task_manager")
        self._file_manager = self._file_manager or application_core.get_manager("file_manager")
        self._config_manager = self._config_manager or application_core.get_manager("config_manager")

        # Load plugin configuration
        await self._load_config()

        # Find plugin directory and resources
        plugin_dir = await self._find_plugin_directory()
        if plugin_dir:
            icon_path = os.path.join(plugin_dir, "resources", "icon.png")
            if os.path.exists(icon_path):
                self._icon_path = icon_path
                self._logger.debug(f"Found plugin icon at: {icon_path}")

        # Initialize processors
        self._media_processor = MediaProcessor(
            self._file_manager,
            self._task_manager,
            self._logger,
            self._plugin_config.get("processing", {}),
            self._plugin_config.get("background_removal", {})
        )

        self._batch_processor = BatchProcessor(
            self._media_processor,
            self._task_manager,
            self._event_bus_manager,
            self._concurrency_manager,
            self._logger,
            self._plugin_config.get("processing", {})
        )

        # Subscribe to events
        await self._event_bus_manager.subscribe(
            event_type="media_processor/job_completed",
            callback=self._on_job_completed,
            subscriber_id="media_processor_plugin"
        )

        await self._event_bus_manager.subscribe(
            event_type="media_processor/job_error",
            callback=self._on_job_error,
            subscriber_id="media_processor_plugin"
        )

        # Signal initialization
        await set_plugin_state(self.name, PluginLifecycleState.INITIALIZED)
        self._logger.info(f"{self.name} plugin initialized successfully")

    async def _find_plugin_directory(self) -> Optional[str]:
        """Find the plugin directory path."""
        import inspect
        try:
            module_path = inspect.getmodule(self).__file__
            if module_path:
                return os.path.dirname(os.path.abspath(module_path))
        except (AttributeError, TypeError):
            pass
        return None

    async def _load_config(self) -> None:
        """Load the plugin configuration."""
        if not self._config_manager:
            return

        self._plugin_config = {
            "processing": await self._config_manager.get(f"plugins.{self.name}.processing", {}),
            "background_removal": await self._config_manager.get(f"plugins.{self.name}.background_removal", {}),
            "formats": await self._config_manager.get(f"plugins.{self.name}.formats", {}),
            "ui": await self._config_manager.get(f"plugins.{self.name}.ui", {})
        }

        if self._logger:
            self._logger.debug("Plugin configuration loaded")

    async def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """
        Set up UI components when the UI system is ready.

        Args:
            ui_integration: The UI integration service
        """
        if self._logger:
            self._logger.info("Setting up UI components")

        current_state = await get_plugin_state(self.name)
        if current_state == PluginLifecycleState.UI_READY:
            self._logger.debug("UI setup already in progress, avoiding recursive call")
            return

        # If called from non-main thread, delegate to main thread
        if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
            self._logger.debug("on_ui_ready called from non-main thread, delegating to main thread")
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self.on_ui_ready(ui_integration))
            )
            return

        # Avoid duplicate UI creation
        if hasattr(self, "_ui_components_created") and self._ui_components_created:
            self._logger.debug("UI components already created, skipping duplicate creation")
            await signal_ui_ready(self.name)
            return

        try:
            await set_plugin_state(self.name, PluginLifecycleState.UI_READY)

            # Add menu items
            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Media",
                title="Process Media",
                callback=lambda: asyncio.create_task(self._open_main_interface())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Media",
                title="Processing Configurations",
                callback=lambda: asyncio.create_task(self._open_config_editor())
            )

            await ui_integration.add_menu_item(
                plugin_id=self.plugin_id,
                parent_menu="Media",
                title="Active Jobs",
                callback=lambda: asyncio.create_task(self._show_active_jobs())
            )

            # Create main widget
            try:
                if not self._main_widget:
                    self._main_widget = MediaProcessorWidget(
                        self._media_processor,
                        self._batch_processor,
                        self._file_manager,
                        self._event_bus_manager,
                        self._concurrency_manager,
                        self._task_manager,
                        self._logger,
                        self._plugin_config,
                        None
                    )

                # Add as page
                await ui_integration.add_page(
                    plugin_id=self.plugin_id,
                    page_component=self._main_widget,
                    icon=self._icon_path,
                    title=self.display_name or self.name
                )

                if self._logger:
                    self._logger.info("UI components set up successfully")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to set up UI components: {str(e)}")

            self._ui_components_created = True
            await set_plugin_state(self.name, PluginLifecycleState.ACTIVE)
            await signal_ui_ready(self.name)

        except Exception as e:
            self._logger.error(f"Error setting up UI: {str(e)}")
            await set_plugin_state(self.name, PluginLifecycleState.FAILED)

    async def _open_main_interface(self) -> None:
        """Open the main interface if not already visible."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_main_interface())
            )
            return

        if self._main_widget:
            # If using as page, could activate the page here
            # For now, we'll just ensure it's visible
            self._main_widget.show()
            self._main_widget.raise_()

    async def _open_config_editor(self) -> None:
        """Open the configuration editor dialog."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._open_config_editor())
            )
            return

        config_editor = ConfigEditorDialog(
            self._media_processor,
            self._file_manager,
            self._logger,
            self._plugin_config,
            parent=self._main_widget
        )
        config_editor.exec()

    async def _show_active_jobs(self) -> None:
        """Show dialog with active processing jobs."""
        if not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._show_active_jobs())
            )
            return

        if not self._active_jobs:
            QMessageBox.information(
                self._main_widget,
                "Active Jobs",
                "No active media processing jobs."
            )
            return

        active_jobs_text = "\n".join([f"• Job ID: {job_id}" for job_id in self._active_jobs])
        QMessageBox.information(
            self._main_widget,
            "Active Jobs",
            f"Active media processing jobs:\n{active_jobs_text}"
        )

    async def _on_job_completed(self, event: Any) -> None:
        """
        Handle job completed event.

        Args:
            event: The event object containing job information
        """
        job_id = event.payload.get("job_id")
        if job_id in self._active_jobs:
            self._active_jobs.remove(job_id)

        self._logger.info(f"Job completed: {job_id}")

    async def _on_job_error(self, event: Any) -> None:
        """
        Handle job error event.

        Args:
            event: The event object containing error information
        """
        job_id = event.payload.get("job_id")
        error_message = event.payload.get("error", "Unknown error")

        if job_id in self._active_jobs:
            self._active_jobs.remove(job_id)

        self._logger.error(f"Job error: {job_id} - {error_message}")

    async def setup_ui(self, ui_integration: Any) -> None:
        """
        Set up UI (compat method).

        Args:
            ui_integration: The UI integration service
        """
        if self._logger:
            self._logger.info("setup_ui method called")
        await self.on_ui_ready(ui_integration)

    def get_main_widget(self) -> Optional[QWidget]:
        """Get the main widget instance."""
        return self._main_widget

    def get_icon(self) -> Optional[str]:
        """Get the plugin icon path."""
        return self._icon_path

    async def shutdown(self) -> None:
        """Shut down the plugin and clean up resources."""
        if self._logger:
            self._logger.info(f"Shutting down {self.name} plugin")

        await set_plugin_state(self.name, PluginLifecycleState.DISABLING)

        # Cancel active jobs
        for job_id in list(self._active_jobs):
            if self._task_manager:
                try:
                    await self._task_manager.cancel_task(job_id)
                except Exception as e:
                    if self._logger:
                        self._logger.error(f"Error cancelling task {job_id}: {str(e)}")

        # Clean up event subscriptions
        if self._event_bus_manager:
            await self._event_bus_manager.unsubscribe(subscriber_id="media_processor_plugin")

        # Clean up UI resources
        self._main_widget = None

        await super().shutdown()
        await set_plugin_state(self.name, PluginLifecycleState.INACTIVE)

        if self._logger:
            self._logger.info(f"{self.name} plugin shutdown complete")