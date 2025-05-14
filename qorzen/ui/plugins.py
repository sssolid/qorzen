from __future__ import annotations
import asyncio
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot, QObject
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox
)

from qorzen.core.plugin_manager import PluginInfo, PluginState


class PluginCard(QFrame):
    stateChangeRequested = Signal(str, bool)
    reloadRequested = Signal(str)
    infoRequested = Signal(str)

    def __init__(self, plugin_id: str, plugin_info: PluginInfo, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.plugin_id = plugin_id
        self.plugin_info = plugin_info
        self._user_action_in_progress = False
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setMinimumHeight(120)
        self.setMaximumHeight(180)
        self._setup_ui()
        self._update_state(plugin_info.state)

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

        self.logo_label.setText('📦')
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet('font-size: 36px;')

    def _is_plugin_enabled(self) -> bool:
        state = self.plugin_info.state
        return state in (PluginState.ACTIVE, PluginState.LOADING)

    def _update_state(self, state: Union[str, PluginState]) -> None:
        # Handle both string and enum state values
        state_str = state.value if isinstance(state, PluginState) else str(state).lower()

        if state_str == 'active':
            self.status_label.setText('Status: Active')
            self.status_label.setStyleSheet('font-weight: bold; color: #28a745;')
            self.setStyleSheet('QFrame { border: 1px solid #28a745; }')
        elif state_str == 'loaded':
            self.status_label.setText('Status: Loaded')
            self.status_label.setStyleSheet('font-weight: bold; color: #17a2b8;')
            self.setStyleSheet('QFrame { border: 1px solid #17a2b8; }')
        elif state_str == 'failed':
            self.status_label.setText('Status: Failed')
            self.status_label.setStyleSheet('font-weight: bold; color: #dc3545;')
            self.setStyleSheet('QFrame { border: 1px solid #dc3545; }')
        elif state_str == 'disabled':
            self.status_label.setText('Status: Disabled')
            self.status_label.setStyleSheet('font-weight: bold; color: #6c757d;')
            self.setStyleSheet('QFrame { border: 1px solid #6c757d; }')
        elif state_str == 'inactive':
            self.status_label.setText('Status: Inactive')
            self.status_label.setStyleSheet('font-weight: bold; color: #fd7e14;')
            self.setStyleSheet('QFrame { border: 1px solid #fd7e14; }')
        elif state_str == 'loading':
            self.status_label.setText('Status: Loading...')
            self.status_label.setStyleSheet('font-weight: bold; color: #17a2b8;')
            self.setStyleSheet('QFrame { border: 1px solid #17a2b8; }')
        elif state_str == 'disabling':
            self.status_label.setText('Status: Disabling...')
            self.status_label.setStyleSheet('font-weight: bold; color: #fd7e14;')
            self.setStyleSheet('QFrame { border: 1px solid #fd7e14; }')
        else:
            self.status_label.setText('Status: Discovered')
            self.status_label.setStyleSheet('font-weight: bold; color: #6c757d;')
            self.setStyleSheet('QFrame { border: 1px solid #6c757d; }')

        if not self._user_action_in_progress:
            self.enable_checkbox.blockSignals(True)
            self.enable_checkbox.setChecked(state_str in ('active', 'loaded', 'loading'))
            self.enable_checkbox.blockSignals(False)

        self.reload_button.setEnabled(state_str in ('active', 'loaded', 'failed', 'inactive'))

    def _on_toggle_state(self, checked: bool) -> None:
        self._user_action_in_progress = True
        self.enable_checkbox.setEnabled(False)
        self.stateChangeRequested.emit(self.plugin_id, checked)
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
        # Fixed: get state directly from plugin_info.state instead of metadata
        self._update_state(plugin_info.state)


class AsyncTaskSignals(QObject):
    started = Signal()
    result_ready = Signal(object)
    error = Signal(str, str)
    finished = Signal()


class PluginsView(QWidget):
    pluginStateChangeRequested = Signal(str, bool)
    pluginReloadRequested = Signal(str)
    pluginInfoRequested = Signal(str)

    def __init__(self, plugin_manager: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._plugin_manager = plugin_manager
        self._plugin_cards: Dict[str, PluginCard] = {}
        self._setup_ui()
        self._load_plugins()
        self._async_signals = AsyncTaskSignals()
        self._async_signals.result_ready.connect(self._on_async_result)
        self._async_signals.error.connect(self._on_async_error)

        # Set a longer refresh interval to avoid frequent state changes
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_plugins)
        self._refresh_timer.start(10000)  # Changed from 5000 to 10000 ms

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel('Installed Plugins')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self.refresh_button)

        self.install_button = QPushButton('Install New')
        self.install_button.clicked.connect(self._on_install_clicked)
        header_layout.addWidget(self.install_button)

        main_layout.addWidget(header_widget)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

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
        self._start_async_task('load_plugins', self._async_load_plugins)

    async def _async_load_plugins(self) -> Dict[str, PluginInfo]:
        if not self._plugin_manager:
            return {}
        try:
            plugins = await self._plugin_manager.get_plugins()
            return plugins
        except Exception as e:
            import traceback
            print(f'Error loading plugins: {str(e)}')
            print(traceback.format_exc())
            raise

    def _on_async_result(self, result_data: Dict[str, Any]) -> None:
        task_id = result_data.get('task_id', '')
        result = result_data.get('result')
        if task_id == 'load_plugins':
            self._clear_plugin_cards()
            plugins = result
            for plugin_id, info in plugins.items():
                self._add_plugin_card(plugin_id, info)
        elif task_id == 'refresh_plugins':
            plugins = result
            for plugin_id, info in plugins.items():
                if plugin_id in self._plugin_cards:
                    # Only update UI components, preserve state if it's active
                    current_state = self._plugin_cards[plugin_id].plugin_info.state
                    self._plugin_cards[plugin_id].update_info(info)
                else:
                    self._add_plugin_card(plugin_id, info)

            # Remove cards for plugins that no longer exist
            for plugin_id in list(self._plugin_cards.keys()):
                if plugin_id not in plugins:
                    card = self._plugin_cards.pop(plugin_id)
                    self.plugins_layout.removeWidget(card)
                    card.deleteLater()
        elif task_id == 'install_plugin':
            success = result
            if success:
                self._start_async_task('refresh_after_install', self._async_refresh_plugins)

    def _on_async_error(self, error_msg: str, traceback_str: str) -> None:
        QMessageBox.critical(self, 'Error', f'An error occurred: {error_msg}\n\n{traceback_str}')

    def _add_plugin_card(self, plugin_id: str, plugin_info: PluginInfo) -> None:
        card = PluginCard(plugin_id, plugin_info, self)
        card.stateChangeRequested.connect(self._on_plugin_state_change_requested)
        card.reloadRequested.connect(self._on_plugin_reload_requested)
        card.infoRequested.connect(self._on_plugin_info_requested)
        self.plugins_layout.insertWidget(self.plugins_layout.count() - 1, card)
        self._plugin_cards[plugin_id] = card

    def _clear_plugin_cards(self) -> None:
        for card in self._plugin_cards.values():
            self.plugins_layout.removeWidget(card)
            card.deleteLater()
        self._plugin_cards.clear()

    def _refresh_plugins(self) -> None:
        if 'refresh_plugins' not in self._running_tasks:
            self._start_async_task('refresh_plugins', self._async_refresh_plugins)

    def _on_refresh_clicked(self) -> None:
        if 'refresh_plugins' in self._running_tasks:
            task = self._running_tasks['refresh_plugins']
            if not task.done():
                task.cancel()
        self._start_async_task('refresh_plugins', self._async_refresh_plugins)

    async def _async_refresh_plugins(self) -> Dict[str, PluginInfo]:
        if not self._plugin_manager:
            return {}
        try:
            plugins = await self._plugin_manager.get_plugins()
            return plugins
        except Exception as e:
            import traceback
            print(f'Error refreshing plugins: {str(e)}')
            print(traceback.format_exc())
            raise

    def _on_install_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Plugin Package', '',
                                                   'Plugin Packages (*.zip *.whl *.tar.gz);;All Files (*)')
        if file_path:
            self._start_async_task('install_plugin', self._async_install_plugin, file_path)

    async def _async_install_plugin(self, file_path: str) -> bool:
        if not self._plugin_manager:
            return False
        try:
            await self._plugin_manager.install_plugin(file_path)
            return True
        except Exception as e:
            raise Exception(f'Failed to install plugin: {str(e)}')

    def _on_plugin_state_change_requested(self, plugin_id: str, enable: bool) -> None:
        self.pluginStateChangeRequested.emit(plugin_id, enable)

    def _on_plugin_reload_requested(self, plugin_id: str) -> None:
        self.pluginReloadRequested.emit(plugin_id)

    def _on_plugin_info_requested(self, plugin_id: str) -> None:
        self.pluginInfoRequested.emit(plugin_id)

    def update_plugin_state_ui(self, plugin_name: str, state: Union[str, PluginState]) -> None:
        """Update the UI state of a plugin by its name."""
        for plugin_id, card in self._plugin_cards.items():
            if hasattr(card, 'plugin_info') and card.plugin_info.name == plugin_name:
                try:
                    old_signal = card.enable_checkbox.toggled.disconnect()
                except Exception:
                    old_signal = None

                card._update_state(state)

                # Convert state to string for checking if it's active
                state_str = state.value if isinstance(state, PluginState) else str(state).lower()
                is_active = state_str in ('active', 'loaded', 'loading')

                if card.enable_checkbox.isChecked() != is_active:
                    card.enable_checkbox.setChecked(is_active)

                if old_signal:
                    card.enable_checkbox.toggled.connect(card._on_toggle_state)
                break

    def _start_async_task(self, task_id: str, coroutine_func: Any, *args: Any, **kwargs: Any) -> None:
        if task_id in self._running_tasks and (not self._running_tasks[task_id].done()):
            self._running_tasks[task_id].cancel()
        task = asyncio.create_task(self._execute_async_task(task_id, coroutine_func, *args, **kwargs))
        self._running_tasks[task_id] = task

    async def _execute_async_task(self, task_id: str, coroutine_func: Any, *args: Any, **kwargs: Any) -> None:
        try:
            result = await coroutine_func(*args, **kwargs)
            self._async_signals.result_ready.emit({'task_id': task_id, 'result': result})
        except asyncio.CancelledError:
            pass
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            self._async_signals.error.emit(str(e), tb_str)
        finally:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    def cleanup(self) -> None:
        self._refresh_timer.stop()
        for task in self._running_tasks.values():
            if not task.done():
                task.cancel()