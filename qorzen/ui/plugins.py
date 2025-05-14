from __future__ import annotations

import asyncio
import os
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget, QFileDialog,
    QMessageBox
)

from qorzen.core.plugin_manager import PluginInfo
from qorzen.ui.ui_component import AsyncTaskSignals


class PluginState(Enum):
    """Enum for possible plugin states."""
    DISCOVERED = auto()
    LOADED = auto()
    ACTIVE = auto()
    INACTIVE = auto()
    FAILED = auto()
    DISABLED = auto()


class PluginCard(QFrame):
    stateChangeRequested = Signal(str, bool)
    reloadRequested = Signal(str)
    infoRequested = Signal(str)

    def __init__(self, plugin_id: str, plugin_info: PluginInfo, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.plugin_id = plugin_id
        self.plugin_info = plugin_info
        # Flag to track user-initiated state changes
        self._user_action_in_progress = False

        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setMinimumHeight(120)
        self.setMaximumHeight(180)
        self._setup_ui()
        self._update_state(plugin_info.state.value)

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(64, 64)
        self.logo_label.setScaledContents(True)
        self._set_plugin_logo()
        main_layout.addWidget(self.logo_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        name_layout = QHBoxLayout()
        self.name_label = QLabel(f'<b>{self.plugin_info.display_name}</b>')
        self.name_label.setStyleSheet('font-size: 14px;')
        name_layout.addWidget(self.name_label)
        self.version_label = QLabel(f"v{getattr(self.plugin_info.manifest, 'version', None) or '0.0.0'}")
        self.version_label.setStyleSheet('color: #666;')
        name_layout.addWidget(self.version_label)
        name_layout.addStretch()
        self.status_label = QLabel('Status: Unknown')
        self.status_label.setStyleSheet('font-weight: bold; color: #666;')
        name_layout.addWidget(self.status_label)
        info_layout.addLayout(name_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        info_layout.addWidget(separator)

        self.description_label = QLabel(
            getattr(self.plugin_info.manifest, 'description', None) or 'No description available.')
        self.description_label.setWordWrap(True)
        info_layout.addWidget(self.description_label)

        self.author_label = QLabel(f"Author: {getattr(self.plugin_info.manifest, 'author', None) or 'Unknown'}")
        self.author_label.setStyleSheet('color: #666; font-size: 11px;')
        info_layout.addWidget(self.author_label)

        info_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        main_layout.addLayout(info_layout, 1)

        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(8)

        self.enable_checkbox = QCheckBox('Enabled')
        self.enable_checkbox.setChecked(self._is_plugin_enabled())
        self.enable_checkbox.toggled.connect(self._on_toggle_state)
        controls_layout.addWidget(self.enable_checkbox)

        self.reload_button = QPushButton('Reload')
        self.reload_button.clicked.connect(self._on_reload_clicked)
        controls_layout.addWidget(self.reload_button)

        self.info_button = QPushButton('Details')
        self.info_button.clicked.connect(self._on_info_clicked)
        controls_layout.addWidget(self.info_button)

        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

    def _set_plugin_logo(self) -> None:
        if self.plugin_info.manifest is None:
            self.logo_label.setText('📦')
            self.logo_label.setAlignment(Qt.AlignCenter)
            self.logo_label.setStyleSheet('font-size: 36px;')
            return

        plugin_dir = Path(self.plugin_info.path) if self.plugin_info.path else None
        relative_logo_path = self.plugin_info.manifest.logo_path if self.plugin_info.manifest else None

        if plugin_dir and relative_logo_path:
            full_logo_path = plugin_dir / relative_logo_path
            if full_logo_path.exists():
                pixmap = QPixmap(str(full_logo_path))
                self.logo_label.setPixmap(pixmap)
                return

        # Default logo if no logo found
        self.logo_label.setText('📦')
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet('font-size: 36px;')

    def _is_plugin_enabled(self) -> bool:
        state = self.plugin_info.state

        return state in (PluginState.ACTIVE, PluginState.LOADED)

    def _update_state(self, state: str) -> None:
        state = state.lower()
        if state == 'active':
            self.status_label.setText('Status: Active')
            self.status_label.setStyleSheet('font-weight: bold; color: #28a745;')
            self.setStyleSheet('QFrame { border: 1px solid #28a745; }')
        elif state == 'loaded':
            self.status_label.setText('Status: Loaded')
            self.status_label.setStyleSheet('font-weight: bold; color: #17a2b8;')
            self.setStyleSheet('QFrame { border: 1px solid #17a2b8; }')
        elif state == 'failed':
            self.status_label.setText('Status: Failed')
            self.status_label.setStyleSheet('font-weight: bold; color: #dc3545;')
            self.setStyleSheet('QFrame { border: 1px solid #dc3545; }')
        elif state == 'disabled':
            self.status_label.setText('Status: Disabled')
            self.status_label.setStyleSheet('font-weight: bold; color: #6c757d;')
            self.setStyleSheet('QFrame { border: 1px solid #6c757d; }')
        elif state == 'inactive':
            self.status_label.setText('Status: Inactive')
            self.status_label.setStyleSheet('font-weight: bold; color: #fd7e14;')
            self.setStyleSheet('QFrame { border: 1px solid #fd7e14; }')
        elif state == 'loading':
            self.status_label.setText('Status: Loading...')
            self.status_label.setStyleSheet('font-weight: bold; color: #17a2b8;')
            self.setStyleSheet('QFrame { border: 1px solid #17a2b8; }')
        elif state == 'disabling':
            self.status_label.setText('Status: Disabling...')
            self.status_label.setStyleSheet('font-weight: bold; color: #fd7e14;')
            self.setStyleSheet('QFrame { border: 1px solid #fd7e14; }')
        else:
            self.status_label.setText('Status: Discovered')
            self.status_label.setStyleSheet('font-weight: bold; color: #6c757d;')
            self.setStyleSheet('QFrame { border: 1px solid #6c757d; }')

        # Only update checkbox state if not in the middle of a user action
        if not self._user_action_in_progress:
            # Temporarily block signals to prevent triggering another state change
            self.enable_checkbox.blockSignals(True)
            self.enable_checkbox.setChecked(state in ('active', 'loaded', 'loading'))
            self.enable_checkbox.blockSignals(False)

        self.reload_button.setEnabled(state in ('active', 'loaded', 'failed', 'inactive'))

    def _on_toggle_state(self, checked: bool) -> None:
        # Set flag to indicate a user-initiated action is in progress
        self._user_action_in_progress = True

        # Disable checkbox until operation completes to prevent multiple clicks
        self.enable_checkbox.setEnabled(False)

        # Signal the desired state change
        self.stateChangeRequested.emit(self.plugin_id, checked)

        # Clear flag and re-enable checkbox after a short delay (operation should be done by then)
        QTimer.singleShot(500, self._reset_action_state)

    def _reset_action_state(self) -> None:
        self._user_action_in_progress = False
        self.enable_checkbox.setEnabled(True)

    def _on_reload_clicked(self) -> None:
        self.reloadRequested.emit(self.plugin_id)

    def _on_info_clicked(self) -> None:
        self.infoRequested.emit(self.plugin_id)

    def update_info(self, plugin_info: PluginInfo) -> None:
        self.plugin_info = plugin_info
        self.name_label.setText(f'<b>{self.plugin_info.display_name}</b>')
        self.version_label.setText(f"v{getattr(plugin_info.manifest, 'version', None) or '0.0.0'}")
        self.description_label.setText(
            getattr(plugin_info.manifest, 'description', None) or 'No description available.')
        self.author_label.setText(f"Author: {getattr(plugin_info.manifest, 'author', None) or 'Unknown'}")
        self._update_state(plugin_info.metadata.get('state', 'discovered'))


class PluginsView(QWidget):
    """Main view for managing plugins."""
    pluginStateChangeRequested = Signal(str, bool)
    pluginReloadRequested = Signal(str)
    pluginInfoRequested = Signal(str)

    def __init__(self, plugin_manager: Any, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the plugins view.

        Args:
            plugin_manager: Reference to the plugin manager
            parent: Parent widget
        """
        super().__init__(parent)
        # Tasks tracking
        self._running_tasks: Dict[str, asyncio.Task] = {}

        self._plugin_manager = plugin_manager
        self._plugin_cards: Dict[str, PluginCard] = {}
        self._setup_ui()
        self._load_plugins()

        # Setup async task signals
        self._async_signals = AsyncTaskSignals()
        self._async_signals.result_ready.connect(self._on_async_result)
        self._async_signals.error.connect(self._on_async_error)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_plugins)
        self._refresh_timer.start(5000)

    def _setup_ui(self) -> None:
        """Set up the plugins view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header section
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel("Installed Plugins")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self.refresh_button)

        self.install_button = QPushButton("Install New")
        self.install_button.clicked.connect(self._on_install_clicked)
        header_layout.addWidget(self.install_button)

        main_layout.addWidget(header_widget)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Plugins container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        self.plugins_container = QWidget()
        self.plugins_layout = QVBoxLayout(self.plugins_container)
        self.plugins_layout.setContentsMargins(10, 10, 10, 10)
        self.plugins_layout.setSpacing(10)
        self.plugins_layout.addStretch()

        scroll_area.setWidget(self.plugins_container)
        main_layout.addWidget(scroll_area)

    def _load_plugins(self) -> None:
        """Load and display plugins from the plugin manager."""
        self._start_async_task("load_plugins", self._async_load_plugins)

    async def _async_load_plugins(self) -> Dict[str, PluginInfo]:
        """
        Asynchronously load plugins.

        Returns:
            Dictionary of plugin information
        """
        if not self._plugin_manager:
            return {}

        try:
            plugins = await self._plugin_manager.get_plugins()
            return plugins
        except Exception as e:
            import traceback
            print(f"Error loading plugins: {str(e)}")
            print(traceback.format_exc())
            raise

    def _on_async_result(self, result_data: Dict[str, Any]) -> None:
        """
        Handle results from async operations.

        Args:
            result_data: Result data including task_id and result
        """
        task_id = result_data.get("task_id", "")
        result = result_data.get("result")

        if task_id == "load_plugins":
            self._clear_plugin_cards()
            plugins = result
            for name, info in plugins.items():
                self._add_plugin_card(name, info)
        elif task_id == "refresh_plugins":
            plugins = result
            for name, info in plugins.items():
                if name in self._plugin_cards:
                    self._plugin_cards[name].update_info(info)
                else:
                    self._add_plugin_card(name, info)

            # Remove plugin cards that no longer exist
            for name in list(self._plugin_cards.keys()):
                if name not in plugins:
                    card = self._plugin_cards.pop(name)
                    self.plugins_layout.removeWidget(card)
                    card.deleteLater()
        elif task_id == "install_plugin":
            success = result
            if success:
                self._start_async_task("refresh_after_install", self._async_refresh_plugins)

    def _on_async_error(self, error_msg: str, traceback_str: str) -> None:
        """
        Handle errors from async operations.

        Args:
            error_msg: Error message
            traceback_str: Exception traceback
        """
        QMessageBox.critical(self, "Error",
                             f"An error occurred: {error_msg}\n\n{traceback_str}")

    def _add_plugin_card(self, plugin_name: str, plugin_info: PluginInfo) -> None:
        """
        Add a plugin card to the view.

        Args:
            plugin_name: Plugin name
            plugin_info: Plugin information
        """
        card = PluginCard(plugin_name, plugin_info, self)
        card.stateChangeRequested.connect(self._on_plugin_state_change_requested)
        card.reloadRequested.connect(self._on_plugin_reload_requested)
        card.infoRequested.connect(self._on_plugin_info_requested)
        self.plugins_layout.insertWidget(self.plugins_layout.count() - 1, card)
        self._plugin_cards[plugin_name] = card

    def _clear_plugin_cards(self) -> None:
        """Remove all plugin cards from the view."""
        for card in self._plugin_cards.values():
            self.plugins_layout.removeWidget(card)
            card.deleteLater()
        self._plugin_cards.clear()

    def _refresh_plugins(self) -> None:
        """Refresh the plugin display."""
        if "refresh_plugins" not in self._running_tasks:
            self._start_async_task("refresh_plugins", self._async_refresh_plugins)

    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        # Cancel any existing refresh task
        if "refresh_plugins" in self._running_tasks:
            task = self._running_tasks["refresh_plugins"]
            if not task.done():
                task.cancel()

        self._start_async_task("refresh_plugins", self._async_refresh_plugins)

    async def _async_refresh_plugins(self) -> Dict[str, PluginInfo]:
        """
        Asynchronously refresh plugins.

        Returns:
            Dictionary of updated plugin information
        """
        if not self._plugin_manager:
            return {}

        try:
            plugins = await self._plugin_manager.get_plugins()
            return plugins
        except Exception as e:
            import traceback
            print(f"Error refreshing plugins: {str(e)}")
            print(traceback.format_exc())
            raise

    def _on_install_clicked(self) -> None:
        """Handle install button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Plugin Package",
            "",
            "Plugin Packages (*.zip *.whl *.tar.gz);;All Files (*)"
        )

        if file_path:
            self._start_async_task(
                "install_plugin",
                self._async_install_plugin,
                file_path
            )

    async def _async_install_plugin(self, file_path: str) -> bool:
        """
        Asynchronously install a plugin.

        Args:
            file_path: Path to the plugin package

        Returns:
            True if installation was successful
        """
        if not self._plugin_manager:
            return False

        try:
            await self._plugin_manager.install_plugin(file_path)
            return True
        except Exception as e:
            raise Exception(f"Failed to install plugin: {str(e)}")

    def _on_plugin_state_change_requested(self, plugin_id: str, enable: bool) -> None:
        """
        Handle plugin state change request.

        Args:
            plugin_id: Plugin ID
            enable: Whether to enable the plugin
        """
        # Forward signal to main
        self.pluginStateChangeRequested.emit(plugin_id, enable)

    def _on_plugin_reload_requested(self, plugin_name: str) -> None:
        """
        Handle plugin reload request.

        Args:
            plugin_name: Plugin name
        """
        # Forward signal to main
        self.pluginReloadRequested.emit(plugin_name)

    def _on_plugin_info_requested(self, plugin_name: str) -> None:
        """
        Handle plugin info request.

        Args:
            plugin_name: Plugin name
        """
        # Forward signal to main
        self.pluginInfoRequested.emit(plugin_name)

    def update_plugin_state_ui(self, plugin_name: str, state: str) -> None:
        """
        Update the UI to reflect plugin state changes.
        Prevents triggering additional state changes.

        Args:
            plugin_name: Name of the plugin
            state: New state string (e.g., "active", "loading", "disabled", "error")
        """
        # Find the plugin card
        for plugin_id, card in self._plugin_cards.items():
            if card.plugin_name == plugin_name:
                # Update the card state without triggering additional events
                # Temporarily disconnect signals
                try:
                    old_signal = card.enable_checkbox.toggled.disconnect()
                except Exception:
                    old_signal = None

                # Update the UI
                card._update_state(state)

                # For checkboxes, only update if needed to avoid triggering events
                is_active = state in ('active', 'loaded', 'loading')
                if card.enable_checkbox.isChecked() != is_active:
                    card.enable_checkbox.setChecked(is_active)

                # Reconnect signals
                if old_signal:
                    card.enable_checkbox.toggled.connect(card._on_toggle_state)

                break

    def _start_async_task(
            self,
            task_id: str,
            coroutine_func: Any,
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Start an asynchronous task.

        Args:
            task_id: Unique task identifier
            coroutine_func: Async function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        # Cancel existing task with same ID if it exists
        if task_id in self._running_tasks and not self._running_tasks[task_id].done():
            self._running_tasks[task_id].cancel()

        task = asyncio.create_task(self._execute_async_task(
            task_id, coroutine_func, *args, **kwargs
        ))
        self._running_tasks[task_id] = task

    async def _execute_async_task(
            self,
            task_id: str,
            coroutine_func: Any,
            *args: Any,
            **kwargs: Any
    ) -> None:
        """
        Execute an asynchronous task and handle signals.

        Args:
            task_id: Task identifier
            coroutine_func: Async function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        try:
            result = await coroutine_func(*args, **kwargs)
            # Use QtCore.Qt.QueuedConnection for thread safety
            self._async_signals.result_ready.emit({
                "task_id": task_id,
                "result": result
            })
        except asyncio.CancelledError:
            # Task was cancelled, no need to emit signals
            pass
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            self._async_signals.error.emit(str(e), tb_str)
        finally:
            # Clean up the task reference
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    def cleanup(self) -> None:
        """Clean up resources when the view is closed."""
        self._refresh_timer.stop()

        # Cancel all running tasks
        for task in self._running_tasks.values():
            if not task.done():
                task.cancel()