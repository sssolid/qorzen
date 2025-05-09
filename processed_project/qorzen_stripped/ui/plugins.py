from __future__ import annotations
import os
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget
from qorzen.core.plugin_manager import PluginInfo
class PluginState(Enum):
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
    def __init__(self, plugin_name: str, plugin_info: PluginInfo, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self.plugin_name = plugin_name
        self.plugin_info = plugin_info
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setMinimumHeight(120)
        self.setMaximumHeight(180)
        self._setup_ui()
        self._update_state(plugin_info.metadata.get('state', 'discovered'))
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
        self.name_label = QLabel(f'<b>{self.plugin_name}</b>')
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
        self.description_label = QLabel(getattr(self.plugin_info.manifest, 'description', None) or 'No description available.')
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
        plugin_dir = Path(self.plugin_info.path)
        relative_logo_path = self.plugin_info.manifest.logo_path
        full_logo_path = plugin_dir / relative_logo_path
        if full_logo_path and os.path.exists(full_logo_path):
            pixmap = QPixmap(full_logo_path)
            self.logo_label.setPixmap(pixmap)
    def _is_plugin_enabled(self) -> bool:
        state = self.plugin_info.metadata.get('state', '').lower()
        return state in ('active', 'loaded') or self.plugin_info.metadata.get('enabled', False)
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
        else:
            self.status_label.setText('Status: Discovered')
            self.status_label.setStyleSheet('font-weight: bold; color: #6c757d;')
            self.setStyleSheet('QFrame { border: 1px solid #6c757d; }')
        self.enable_checkbox.setChecked(state in ('active', 'loaded'))
        self.reload_button.setEnabled(state in ('active', 'loaded', 'failed', 'inactive'))
    def _on_toggle_state(self, checked: bool) -> None:
        self.stateChangeRequested.emit(self.plugin_name, checked)
    def _on_reload_clicked(self) -> None:
        self.reloadRequested.emit(self.plugin_name)
    def _on_info_clicked(self) -> None:
        self.infoRequested.emit(self.plugin_name)
    def update_info(self, plugin_info: PluginInfo) -> None:
        self.plugin_info = plugin_info
        self.name_label.setText(f'<b>{self.plugin_name}</b>')
        self.version_label.setText(f"v{getattr(plugin_info.manifest, 'version', None) or '0.0.0'}")
        self.description_label.setText(getattr(plugin_info.manifest, 'description', None) or 'No description available.')
        self.author_label.setText(f"Author: {getattr(plugin_info.manifest, 'author', None) or 'Unknown'}")
        self._update_state(plugin_info.metadata.get('state', 'discovered'))
class PluginsView(QWidget):
    pluginStateChangeRequested = Signal(str, bool)
    pluginReloadRequested = Signal(str)
    pluginInfoRequested = Signal(str)
    def __init__(self, plugin_manager: Any, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._plugin_manager = plugin_manager
        self._plugin_cards: Dict[str, PluginCard] = {}
        self._setup_ui()
        self._load_plugins()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_plugins)
        self._refresh_timer.start(5000)
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
        self.refresh_button.clicked.connect(self._refresh_plugins)
        header_layout.addWidget(self.refresh_button)
        self.install_button = QPushButton('Install New')
        self.install_button.clicked.connect(self._install_plugin)
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
        if not self._plugin_manager:
            return
        try:
            plugins = self._plugin_manager.get_all_plugins()
            self._clear_plugin_cards()
            for name, info in plugins.items():
                self._add_plugin_card(name, info)
        except Exception as e:
            import traceback
            print(f'Error loading plugins: {str(e)}')
            print(traceback.format_exc())
    def _add_plugin_card(self, plugin_name: str, plugin_info: PluginInfo) -> None:
        card = PluginCard(plugin_name, plugin_info, self)
        card.stateChangeRequested.connect(self.pluginStateChangeRequested)
        card.reloadRequested.connect(self.pluginReloadRequested)
        card.infoRequested.connect(self.pluginInfoRequested)
        self.plugins_layout.insertWidget(self.plugins_layout.count() - 1, card)
        self._plugin_cards[plugin_name] = card
    def _clear_plugin_cards(self) -> None:
        for card in self._plugin_cards.values():
            self.plugins_layout.removeWidget(card)
            card.deleteLater()
        self._plugin_cards.clear()
    def _refresh_plugins(self) -> None:
        if not self._plugin_manager:
            return
        try:
            plugins = self._plugin_manager.get_all_plugins()
            for name, info in plugins.items():
                if name in self._plugin_cards:
                    self._plugin_cards[name].update_info(info)
                else:
                    self._add_plugin_card(name, info)
            for name in list(self._plugin_cards.keys()):
                if name not in plugins:
                    card = self._plugin_cards.pop(name)
                    self.plugins_layout.removeWidget(card)
                    card.deleteLater()
        except Exception as e:
            import traceback
            print(f'Error refreshing plugins: {str(e)}')
            print(traceback.format_exc())
    def _install_plugin(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Plugin Package', '', 'Plugin Packages (*.zip *.whl *.tar.gz);;All Files (*)')
        if file_path:
            if self._plugin_manager:
                try:
                    self._plugin_manager.install_plugin(file_path)
                    self._refresh_plugins()
                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, 'Installation Error', f'Failed to install plugin: {str(e)}')
    def update_plugin_state(self, plugin_name: str, state: str) -> None:
        if plugin_name in self._plugin_cards:
            self._plugin_cards[plugin_name]._update_state(state)
    def cleanup(self) -> None:
        self._refresh_timer.stop()