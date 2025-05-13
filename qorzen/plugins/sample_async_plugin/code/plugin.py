from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from qorzen.plugin_system.interface import BasePlugin


class SampleAsyncPlugin(BasePlugin):
    """Sample implementation of an asynchronous plugin."""

    name = "sample_async_plugin"
    version = "1.0.0"
    description = "Sample asynchronous plugin demonstrating the new plugin system"
    author = "Qorzen"
    dependencies = []

    def __init__(self) -> None:
        """Initialize the sample plugin."""
        super().__init__()
        self._counter = 0
        self._timer_task = None

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin with the application core.

        Args:
            application_core: The application core instance
            **kwargs: Additional initialization parameters
        """
        await super().initialize(application_core, **kwargs)

        if self._logger:
            self._logger.info(f"{self.name} v{self.version} initializing...")

        # Register a task
        if self._task_manager:
            await self.register_task("increment_counter", self._increment_counter)
            await self.register_task("get_counter", self._get_counter)

        # Start a background timer task
        self._timer_task = asyncio.create_task(self._timer_loop())

        if self._logger:
            self._logger.info(f"{self.name} initialized successfully")

    async def on_ui_ready(self, ui_integration: Any) -> None:
        """
        Set up UI components when the UI is ready.

        Args:
            ui_integration: The UI integration instance
        """
        await super().on_ui_ready(ui_integration)

        if self._logger:
            self._logger.info("Setting up UI components")

        try:
            # Add a menu item
            menu_id = await ui_integration.add_menu_item(
                plugin_id=self.name,
                title="Sample Plugin",
                callback=self._on_menu_clicked,
                parent_menu="Plugins"
            )

            # Register the menu item with our UI registry
            await self.register_ui_component(menu_id, "menu_item")

            if self._logger:
                self._logger.info("UI components set up successfully")

        except Exception as e:
            if self._logger:
                self._logger.error(f"Error setting up UI: {e}")

    async def _timer_loop(self) -> None:
        """Background timer that runs every 10 seconds."""
        try:
            while True:
                await asyncio.sleep(10)
                self._counter += 1

                if self._logger:
                    self._logger.debug(f"Timer incremented counter to {self._counter}")

                if self._event_bus_manager:
                    await self._event_bus_manager.publish(
                        event_type=f"plugin/{self.name}/counter_updated",
                        source=self.name,
                        payload={"counter": self._counter}
                    )

        except asyncio.CancelledError:
            if self._logger:
                self._logger.debug("Timer task cancelled")
            raise
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error in timer loop: {e}")

    async def _increment_counter(self, amount: int = 1) -> int:
        """
        Increment the counter.

        Args:
            amount: Amount to increment by

        Returns:
            int: The new counter value
        """
        self._counter += amount

        if self._logger:
            self._logger.info(f"Counter incremented by {amount} to {self._counter}")

        return self._counter

    async def _get_counter(self) -> int:
        """
        Get the current counter value.

        Returns:
            int: The current counter value
        """
        return self._counter

    async def _on_menu_clicked(self) -> None:
        """Handle menu item click."""
        if self._logger:
            self._logger.info("Menu item clicked")

        # Execute the increment_counter task
        if self._task_manager:
            await self.execute_task("increment_counter", 5)

            # Show notification through the UI
            ui = self._application_core.get_ui_integration()
            if ui:
                await ui.show_notification(
                    plugin_id=self.name,
                    message=f"Counter incremented to {self._counter}",
                    title="Sample Plugin",
                    notification_type="info"
                )

    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        if self._logger:
            self._logger.info(f"{self.name} shutting down...")

        # Cancel the timer task
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass

        await super().shutdown()

        if self._logger:
            self._logger.info(f"{self.name} shutdown complete")