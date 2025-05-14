from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Awaitable, cast

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QProgressBar, QListWidget, QListWidgetItem
)

from qorzen.core.task_manager import TaskCategory, TaskPriority
from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.ui_component import AsyncQWidget


class CounterWidget(AsyncQWidget):
    """Widget for displaying the counter information from the sample plugin."""

    def __init__(self, plugin: "SampleAsyncPlugin", parent: Optional[QWidget] = None) -> None:
        """Initialize the counter widget.

        Args:
            plugin: The sample plugin instance
            parent: Optional parent widget
        """
        super().__init__(parent, plugin._thread_manager)
        self._plugin = plugin
        self._setup_ui()
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(1000)  # Update every second

        # Initialize display
        self._update_display()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("Sample Async Plugin Dashboard")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Counter display section
        counter_frame = QFrame()
        counter_frame.setFrameShape(QFrame.StyledPanel)
        counter_frame.setFrameShadow(QFrame.Raised)
        counter_layout = QVBoxLayout(counter_frame)

        # Counter value with large display
        counter_label = QLabel("Current Counter Value:")
        counter_layout.addWidget(counter_label)

        self._counter_value = QLabel("0")
        self._counter_value.setStyleSheet("font-size: 48px; font-weight: bold; color: #0078d7; padding: 10px;")
        self._counter_value.setAlignment(Qt.AlignCenter)
        counter_layout.addWidget(self._counter_value)

        # Counter update time
        self._last_update_label = QLabel("Last update: Never")
        self._last_update_label.setAlignment(Qt.AlignCenter)
        counter_layout.addWidget(self._last_update_label)

        main_layout.addWidget(counter_frame)

        # Button controls
        button_layout = QHBoxLayout()

        self._increment_button = QPushButton("Increment Counter")
        self._increment_button.setMinimumHeight(40)
        self._increment_button.clicked.connect(self._on_increment_clicked)
        button_layout.addWidget(self._increment_button)

        self._increment_by_10_button = QPushButton("Increment by 10")
        self._increment_by_10_button.setMinimumHeight(40)
        self._increment_by_10_button.clicked.connect(self._on_increment_by_10_clicked)
        button_layout.addWidget(self._increment_by_10_button)

        main_layout.addLayout(button_layout)

        # Task status section
        status_label = QLabel("Plugin Status")
        status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(status_label)

        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_layout = QVBoxLayout(status_frame)

        # Timer task status
        timer_label = QLabel("Timer Task:")
        status_layout.addWidget(timer_label)

        self._timer_status = QLabel("Unknown")
        self._timer_status.setStyleSheet("color: gray; font-weight: bold;")
        status_layout.addWidget(self._timer_status)

        # Update history
        history_label = QLabel("Update History:")
        status_layout.addWidget(history_label)

        self._history_list = QListWidget()
        self._history_list.setMaximumHeight(150)
        status_layout.addWidget(self._history_list)

        main_layout.addWidget(status_frame)
        main_layout.addStretch()

    def _update_display(self) -> None:
        """Update the displayed counter value and status."""
        # Get the current counter value from the plugin
        self.run_async_task(
            self._plugin._get_counter,
            task_id="get_counter",
            on_result=self._on_counter_updated
        )

        # Update timer task status
        if self._plugin._timer_task_id:
            self._timer_status.setText("Running")
            self._timer_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self._timer_status.setText("Not started")
            self._timer_status.setStyleSheet("color: gray; font-weight: bold;")

    def _on_counter_updated(self, counter_value: int) -> None:
        """Handle counter value update.

        Args:
            counter_value: The current counter value
        """
        prev_value = self._counter_value.text()
        current_value = str(counter_value)

        # Only update if the value has changed
        if prev_value != current_value:
            self._counter_value.setText(current_value)
            current_time = datetime.now().strftime("%H:%M:%S")
            self._last_update_label.setText(f"Last update: {current_time}")

            # Add to history
            history_item = QListWidgetItem(
                f"{current_time}: Counter updated to {counter_value}"
            )
            self._history_list.insertItem(0, history_item)

            # Keep history at a reasonable size
            while self._history_list.count() > 20:
                self._history_list.takeItem(self._history_list.count() - 1)

    def _on_increment_clicked(self) -> None:
        """Handle increment button click."""
        self._increment_button.setEnabled(False)
        self.run_async_task(
            self._plugin._increment_counter,
            1,
            task_id="increment_counter",
            on_result=self._on_increment_done,
            on_error=self._on_task_error,
            on_finished=lambda: self._increment_button.setEnabled(True)
        )

    def _on_increment_by_10_clicked(self) -> None:
        """Handle increment by 10 button click."""
        self._increment_by_10_button.setEnabled(False)
        self.run_async_task(
            self._plugin._increment_counter,
            10,
            task_id="increment_by_10",
            on_result=self._on_increment_done,
            on_error=self._on_task_error,
            on_finished=lambda: self._increment_by_10_button.setEnabled(True)
        )

    def _on_increment_done(self, new_value: int) -> None:
        """Handle successful increment operation.

        Args:
            new_value: The new counter value
        """
        # Update display immediately
        self._on_counter_updated(new_value)

    def _on_task_error(self, error_msg: str, traceback_str: str) -> None:
        """Handle task error.

        Args:
            error_msg: Error message
            traceback_str: Traceback string
        """
        if self._plugin._logger:
            self._plugin._logger.error(
                f"Error in counter widget: {error_msg}",
                extra={"traceback": traceback_str}
            )

        # Add to history
        current_time = datetime.now().strftime("%H:%M:%S")
        history_item = QListWidgetItem(
            f"{current_time}: Error - {error_msg}"
        )
        history_item.setForeground(Qt.red)
        self._history_list.insertItem(0, history_item)

    def closeEvent(self, event: Any) -> None:
        """Handle widget close event.

        Args:
            event: The close event
        """
        self._update_timer.stop()
        super().closeEvent(event)


class SampleAsyncPlugin(BasePlugin):
    """Sample asynchronous plugin demonstrating the new plugin system."""

    name = 'sample_async_plugin'
    version = '1.0.0'
    description = 'Sample asynchronous plugin demonstrating the new plugin system'
    author = 'Qorzen'
    dependencies = []

    def __init__(self) -> None:
        """Initialize the sample plugin."""
        super().__init__()
        self._counter = 0
        self._timer_task_id = None
        self._counter_widget = None
        self._counter_page_id = None
        self._menu_item_id = None
        self._event_subscribers = []
        self._task_ids = []
        self._shutdown = False
        self._ui_integration = None

    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        """Initialize the plugin.

        Args:
            application_core: The application core
            **kwargs: Additional arguments
        """
        try:
            await super().initialize(application_core, **kwargs)

            if self._logger:
                self._logger.info(f'{self.name} v{self.version} initializing...')

            # Start the timer task
            if self._task_manager:
                # Submit the timer task and store the task ID
                self._timer_task_id = await self._task_manager.submit_async_task(
                    func=self._timer_loop,
                    name='plugin_timer_loop',
                    plugin_id=self.plugin_id,
                    category=TaskCategory.PLUGIN
                )
                if self._timer_task_id:
                    self._task_ids.append(self._timer_task_id)
                    if self._logger:
                        self._logger.debug(f"Timer task started with ID: {self._timer_task_id}")

            # Subscribe to counter update events
            if self._event_bus_manager:
                sub_id = await self._event_bus_manager.subscribe(
                    event_type=f'plugin/{self.name}/counter_updated',
                    callback=self._on_counter_updated,
                    subscriber_id=f'{self.name}_counter_listener'
                )
                self._event_subscribers.append(sub_id)

            if self._logger:
                self._logger.info(f'{self.name} initialized successfully')

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error initializing {self.name}: {str(e)}', exc_info=True)
            raise

    async def on_ui_ready(self, ui_integration: Any) -> None:
        """Handle UI ready event.

        Args:
            ui_integration: The UI integration instance
        """
        try:
            self._ui_integration = ui_integration
            await super().on_ui_ready(ui_integration)

            if self._logger:
                self._logger.info('Setting up UI components')

            try:
                # Add menu item
                self._menu_item_id = await ui_integration.add_menu_item(
                    plugin_id=self.plugin_id,
                    title='Sample Plugin',
                    callback=self._on_menu_clicked,
                    parent_menu='Plugins'
                )

                # Create and add the counter page
                await self._setup_counter_page(ui_integration)

            except Exception as ui_error:
                if self._logger:
                    self._logger.error(f'Failed to set up UI: {str(ui_error)}', exc_info=True)

            if self._logger:
                self._logger.info('UI components set up successfully')

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error setting up UI: {e}', exc_info=True)

    async def setup_ui(self, ui_integration: Any) -> None:
        """Set up the UI components.

        Args:
            ui_integration: The UI integration instance
        """
        if self._logger:
            self._logger.info('setup_ui method called')

        await self.on_ui_ready(ui_integration)

    async def _setup_counter_page(self, ui_integration: Any) -> None:
        """Set up the counter page.

        Args:
            ui_integration: The UI integration instance
        """
        if self._counter_page_id:
            return  # Page already created

        try:
            # Create the counter widget
            self._counter_widget = CounterWidget(self)

            # Add the page
            self._counter_page_id = await ui_integration.add_page(
                plugin_id=self.plugin_id,
                page_component=self._counter_widget,
                title='Sample Plugin Counter',
                icon=':/ui_icons/trending-up.svg'  # Use a built-in icon
            )

            if self._logger:
                self._logger.info(f'Counter page created with id: {self._counter_page_id}')

        except Exception as e:
            if self._logger:
                self._logger.error(f'Failed to create counter page: {str(e)}', exc_info=True)

    async def _timer_loop(self) -> None:
        """Background timer loop that increments the counter periodically."""
        try:
            while True:
                await asyncio.sleep(1)
                self._counter += 1

                if self._logger:
                    self._logger.debug(f'Timer incremented counter to {self._counter}')

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

        except asyncio.CancelledError:
            if self._logger:
                self._logger.debug('Timer task cancelled')
            raise

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error in timer loop: {e}', exc_info=True)

            # Attempt to restart after error
            if self._logger:
                self._logger.info('Restarting timer loop after error')

            await asyncio.sleep(5)

            # Only restart if not shutting down
            if not self._shutdown and self._task_manager:
                try:
                    new_task_id = await self._task_manager.submit_async_task(
                        func=self._timer_loop,
                        name='plugin_timer_loop',
                        plugin_id=self.plugin_id,
                        category=TaskCategory.PLUGIN
                    )
                    if new_task_id:
                        self._timer_task_id = new_task_id
                        self._task_ids.append(new_task_id)
                        if self._logger:
                            self._logger.debug(f"Timer task restarted with ID: {new_task_id}")
                except Exception as restart_error:
                    if self._logger:
                        self._logger.error(f"Failed to restart timer task: {restart_error}")

    async def _increment_counter(self, amount: int = 1) -> int:
        """Increment the counter by the specified amount.

        Args:
            amount: Amount to increment by (default: 1)

        Returns:
            The new counter value
        """
        self._counter += amount

        if self._logger:
            self._logger.info(f'Counter incremented by {amount} to {self._counter}')

        # Publish counter update event
        if self._event_bus_manager:
            try:
                await self._event_bus_manager.publish(
                    event_type=f'plugin/{self.name}/counter_updated',
                    source=self.name,
                    payload={'counter': self._counter, 'increment': amount}
                )
            except Exception as e:
                if self._logger:
                    self._logger.warning(f'Failed to publish counter update event: {str(e)}')

        return self._counter

    async def _get_counter(self) -> int:
        """Get the current counter value.

        Returns:
            The current counter value
        """
        return self._counter

    async def _on_counter_updated(self, event: Any) -> None:
        """Handle counter update event.

        Args:
            event: The event object
        """
        # This method is called when the counter is updated
        # Could be used for additional processing if needed
        pass

    async def _on_menu_clicked(self) -> None:
        """Handle menu item click."""
        if self._logger:
            self._logger.info('Menu item clicked')

        try:
            # Directly use the _increment_counter method
            new_value = await self._increment_counter(5)

            # Show notification
            ui = self._ui_integration
            if not ui and self._application_core:
                ui = self._application_core.get_ui_integration()

            if ui:
                await ui.show_notification(
                    plugin_id=self.plugin_id,
                    message=f'Counter incremented to {self._counter}',
                    title='Sample Plugin',
                    notification_type='info'
                )

            # If we have a counter page, try to navigate to it
            if self._counter_page_id and ui and hasattr(ui, '_main_window'):
                if hasattr(ui._main_window, 'select_page'):
                    ui._main_window.select_page(self._counter_page_id)

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error in menu click handler: {str(e)}', exc_info=True)

    async def shutdown(self) -> None:
        """Shut down the plugin."""
        if self._logger:
            self._logger.info(f'{self.name} shutting down...')

        # Mark as shutting down to prevent task restart attempts
        self._shutdown = True

        # Cancel all tasks
        if self._task_manager:
            for task_id in self._task_ids:
                try:
                    await self._task_manager.cancel_task(task_id)
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f'Error cancelling task {task_id}: {str(e)}')

        # Unsubscribe from events
        if self._event_bus_manager:
            for subscriber_id in self._event_subscribers:
                try:
                    await self._event_bus_manager.unsubscribe(subscriber_id=subscriber_id)
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f'Error unsubscribing from events: {str(e)}')

            self._event_subscribers = []

        # Allow the parent class to handle any remaining cleanup
        try:
            await super().shutdown()
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error during shutdown: {str(e)}', exc_info=True)

        if self._logger:
            self._logger.info(f'{self.name} shutdown complete')