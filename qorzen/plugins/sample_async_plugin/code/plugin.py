from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional
from qorzen.plugin_system.interface import BasePlugin


class SampleAsyncPlugin(BasePlugin):
    name = 'sample_async_plugin'
    version = '1.0.0'
    description = 'Sample asynchronous plugin demonstrating the new plugin system'
    author = 'Qorzen'
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self._counter = 0
        self._timer_task = None

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        try:
            await super().initialize(application_core, **kwargs)

            if self._logger:
                self._logger.info(f'{self.name} v{self.version} initializing...')

            # Register tasks if task manager available
            if self._task_manager:
                await self.register_task('increment_counter', self._increment_counter)
                await self.register_task('get_counter', self._get_counter)

            # Start the background timer task
            self._timer_task = asyncio.create_task(self._timer_loop())

            if self._logger:
                self._logger.info(f'{self.name} initialized successfully')

        except Exception as e:
            if self._logger:
                self._logger.error(f"Error initializing {self.name}: {str(e)}", exc_info=True)
            raise

    async def on_ui_ready(self, ui_integration: Any) -> None:
        try:
            await super().on_ui_ready(ui_integration)

            if self._logger:
                self._logger.info('Setting up UI components')

            # Add menu item
            menu_id = await ui_integration.add_menu_item(
                plugin_id=self.name,
                title='Sample Plugin',
                callback=self._on_menu_clicked,
                parent_menu='Plugins'
            )

            # Register the UI component
            await self.register_ui_component(menu_id, 'menu_item')

            if self._logger:
                self._logger.info('UI components set up successfully')

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error setting up UI: {e}', exc_info=True)

    async def _timer_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(10)
                self._counter += 1

                if self._logger:
                    self._logger.debug(f'Timer incremented counter to {self._counter}')

                # Publish an event if possible
                if self._event_bus_manager:
                    try:
                        await self._event_bus_manager.publish(
                            event_type=f'plugin/{self.name}/counter_updated',
                            source=self.name,
                            payload={'counter': self._counter}
                        )
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(f"Failed to publish event: {str(e)}")

        except asyncio.CancelledError:
            if self._logger:
                self._logger.debug('Timer task cancelled')
            raise
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error in timer loop: {e}', exc_info=True)

    async def _increment_counter(self, amount: int = 1) -> int:
        self._counter += amount
        if self._logger:
            self._logger.info(f'Counter incremented by {amount} to {self._counter}')
        return self._counter

    async def _get_counter(self) -> int:
        return self._counter

    async def _on_menu_clicked(self) -> None:
        if self._logger:
            self._logger.info('Menu item clicked')

        if self._task_manager:
            try:
                await self.execute_task('increment_counter', 5)

                # Show notification if UI integration is available
                ui = self._application_core.get_ui_integration() if self._application_core else None
                if ui:
                    await ui.show_notification(
                        plugin_id=self.name,
                        message=f'Counter incremented to {self._counter}',
                        title='Sample Plugin',
                        notification_type='info'
                    )
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error executing task: {str(e)}", exc_info=True)

    async def shutdown(self) -> None:
        if self._logger:
            self._logger.info(f'{self.name} shutting down...')

        # Cancel timer task
        if self._timer_task and (not self._timer_task.done()):
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass

        # Call parent shutdown
        try:
            await super().shutdown()
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error during shutdown: {str(e)}", exc_info=True)

        if self._logger:
            self._logger.info(f'{self.name} shutdown complete')