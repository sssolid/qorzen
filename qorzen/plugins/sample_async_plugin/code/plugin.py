#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from qorzen.plugin_system.interface import BasePlugin


class SampleAsyncPlugin(BasePlugin):
    """
    Fixed version of the Sample Async Plugin to ensure it loads and stays loaded.
    """
    name = 'sample_async_plugin'
    version = '1.0.0'
    description = 'Sample asynchronous plugin demonstrating the new plugin system'
    author = 'Qorzen'
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self._counter = 0
        self._timer_task = None
        self._menu_added = False
        self._ui_integration = None

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin with improved error handling.
        """
        try:
            await super().initialize(application_core, **kwargs)
            if self._logger:
                self._logger.info(f'{self.name} v{self.version} initializing...')

            if self._task_manager:
                await self.register_task('increment_counter', self._increment_counter)
                await self.register_task('get_counter', self._get_counter)

            # Store the UI integration if available
            self._ui_integration = application_core.get_ui_integration()

            # Start the timer with safe error handling
            self._timer_task = asyncio.create_task(self._timer_loop())

            if self._logger:
                self._logger.info(f'{self.name} initialized successfully')
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error initializing {self.name}: {str(e)}', exc_info=True)
            raise

    async def on_ui_ready(self, ui_integration: Any) -> None:
        """
        Set up UI components when UI is ready, with error handling.
        """
        try:
            await super().on_ui_ready(ui_integration)

            # Store UI integration for later use
            self._ui_integration = ui_integration

            if self._logger:
                self._logger.info('Setting up UI components')

            # Add menu item with explicit error handling
            try:
                menu_id = await ui_integration.add_menu_item(
                    plugin_id=self.name,  # Use name instead of plugin_id which might be inconsistent
                    title='Sample Plugin',
                    callback=self._on_menu_clicked,
                    parent_menu='Plugins'
                )

                await self.register_ui_component(menu_id, 'menu_item')
                self._menu_added = True

                if self._logger:
                    self._logger.info(f'UI menu item created with id: {menu_id}')
            except Exception as menu_error:
                if self._logger:
                    self._logger.error(f'Failed to add menu item: {str(menu_error)}', exc_info=True)

            if self._logger:
                self._logger.info('UI components set up successfully')
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error setting up UI: {e}', exc_info=True)

    async def setup_ui(self, ui_integration: Any) -> None:
        """
        Alternative UI setup method that might be called instead of on_ui_ready.
        """
        # Store for later use
        self._ui_integration = ui_integration

        # Log that this method was called
        if self._logger:
            self._logger.info('setup_ui method called')

        # Call our primary UI setup method
        await self.on_ui_ready(ui_integration)

    async def _timer_loop(self) -> None:
        """
        Background timer loop with robust error handling to prevent crashes.
        """
        try:
            while True:
                await asyncio.sleep(10)
                self._counter += 1

                if self._logger:
                    self._logger.debug(f'Timer incremented counter to {self._counter}')

                # Attempt to publish event with safe error handling
                if self._event_bus_manager:
                    try:
                        await self._event_bus_manager.publish(
                            event_type=f'plugin/{self.name}/counter_updated',
                            source=self.name,
                            payload={'counter': self._counter}
                        )
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(f'Failed to publish event: {str(e)}')

                # If menu wasn't added yet and we have UI integration, try again
                if not self._menu_added and self._ui_integration:
                    try:
                        menu_id = await self._ui_integration.add_menu_item(
                            plugin_id=self.name,
                            title='Sample Plugin (retry)',
                            callback=self._on_menu_clicked,
                            parent_menu='Plugins'
                        )
                        await self.register_ui_component(menu_id, 'menu_item')
                        self._menu_added = True
                        if self._logger:
                            self._logger.info(f'UI menu item created on retry with id: {menu_id}')
                    except Exception as menu_error:
                        if self._logger:
                            self._logger.warning(f'Failed to add menu item on retry: {str(menu_error)}')

        except asyncio.CancelledError:
            if self._logger:
                self._logger.debug('Timer task cancelled')
            raise
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error in timer loop: {e}', exc_info=True)

            # Restart the timer loop after a delay
            if self._logger:
                self._logger.info('Restarting timer loop after error')
            await asyncio.sleep(5)
            if not self._timer_task or self._timer_task.done():
                self._timer_task = asyncio.create_task(self._timer_loop())

    async def _increment_counter(self, amount: int = 1) -> int:
        """Increment the counter by the specified amount."""
        self._counter += amount
        if self._logger:
            self._logger.info(f'Counter incremented by {amount} to {self._counter}')
        return self._counter

    async def _get_counter(self) -> int:
        """Get the current counter value."""
        return self._counter

    async def _on_menu_clicked(self) -> None:
        """Handle menu item click with robust error handling."""
        if self._logger:
            self._logger.info('Menu item clicked')

        try:
            if self._task_manager:
                try:
                    await self.execute_task('increment_counter', 5)

                    # Use the stored UI integration or try to get it again
                    ui = self._ui_integration
                    if not ui and self._application_core:
                        ui = self._application_core.get_ui_integration()

                    if ui:
                        await ui.show_notification(
                            plugin_id=self.name,
                            message=f'Counter incremented to {self._counter}',
                            title='Sample Plugin',
                            notification_type='info'
                        )
                except Exception as e:
                    if self._logger:
                        self._logger.error(f'Error executing task: {str(e)}', exc_info=True)
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error in menu click handler: {str(e)}', exc_info=True)

    async def shutdown(self) -> None:
        """Clean shutdown with proper cancellation of background tasks."""
        if self._logger:
            self._logger.info(f'{self.name} shutting down...')

        # Cancel timer task if running
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                if self._logger:
                    self._logger.warning(f'Error canceling timer task: {str(e)}')

        # Call parent shutdown
        try:
            await super().shutdown()
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error during shutdown: {str(e)}', exc_info=True)

        if self._logger:
            self._logger.info(f'{self.name} shutdown complete')