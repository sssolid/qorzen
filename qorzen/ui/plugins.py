from __future__ import annotations

import os
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget
)

from qorzen.core.plugin_manager import PluginInfo


class PluginState(Enum):
    """Represents the current state of a plugin."""

    DISCOVERED = auto()  # Plugin is discovered but not loaded
    LOADED = auto()  # Plugin is loaded and ready
    ACTIVE = auto()  # Plugin is active and running
    INACTIVE = auto()  # Plugin is loaded but not active
    FAILED = auto()  # Plugin failed to load or crashed
    DISABLED = auto()  # Plugin is explicitly disabled


class PluginCard(QFrame):
    """A card widget displaying information about a plugin."""

    # Signal emitted when the plugin state should be changed
    stateChangeRequested = Signal(str, bool)  # plugin_name, enable

    # Signal emitted when the plugin should be reloaded
    reloadRequested = Signal(str)  # plugin_name

    # Signal emitted when more information is requested
    infoRequested = Signal(str)  # plugin_name

    def __init__(
            self,
            plugin_name: str,
            plugin_info: PluginInfo,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the plugin card.

        Args:
            plugin_name: The name of the plugin
            plugin_info: Information about the plugin
            parent: The parent widget
        """
        super().__init__(parent)

        self.plugin_name = plugin_name
        self.plugin_info = plugin_info

        # Set up the card appearance
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setMinimumHeight(120)
        self.setMaximumHeight(180)

        # Create layout
        self._setup_ui()

        # Set initial state
        self._update_state(plugin_info.metadata.get("state", "discovered"))

    def _setup_ui(self) -> None:
        """Set up the UI components of the card."""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Icon/logo area
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(64, 64)
        self.logo_label.setScaledContents(True)
        self._set_plugin_logo()
        main_layout.addWidget(self.logo_label)

        # Info area
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        # Plugin name and version
        name_layout = QHBoxLayout()
        self.name_label = QLabel(f"<b>{self.plugin_name}</b>")
        self.name_label.setStyleSheet("font-size: 14px;")
        name_layout.addWidget(self.name_label)

        self.version_label = QLabel(f"v{getattr(self.plugin_info.manifest, 'version', None) or '0.0.0'}")
        self.version_label.setStyleSheet("color: #666;")
        name_layout.addWidget(self.version_label)

        name_layout.addStretch()

        # Status indicator
        self.status_label = QLabel("Status: Unknown")
        self.status_label.setStyleSheet("font-weight: bold; color: #666;")
        name_layout.addWidget(self.status_label)

        info_layout.addLayout(name_layout)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        info_layout.addWidget(separator)

        # Description
        self.description_label = QLabel(getattr(self.plugin_info.manifest, "description", None) or "No description available.")
        self.description_label.setWordWrap(True)
        info_layout.addWidget(self.description_label)

        # Author
        self.author_label = QLabel(f"Author: {getattr(self.plugin_info.manifest, 'author', None) or 'Unknown'}")
        self.author_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(self.author_label)

        # Add a spacer
        info_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        main_layout.addLayout(info_layout, 1)  # Give the info area more stretch

        # Controls area
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(8)

        # Enable/disable toggle
        self.enable_checkbox = QCheckBox("Enabled")
        self.enable_checkbox.setChecked(self._is_plugin_enabled())
        self.enable_checkbox.toggled.connect(self._on_toggle_state)
        controls_layout.addWidget(self.enable_checkbox)

        # Reload button
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self._on_reload_clicked)
        controls_layout.addWidget(self.reload_button)

        # Info button
        self.info_button = QPushButton("Details")
        self.info_button.clicked.connect(self._on_info_clicked)
        controls_layout.addWidget(self.info_button)

        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

    def _set_plugin_logo(self) -> None:
        """Set the plugin logo or a default icon."""
        if self.plugin_info.manifest is None:
            # Use a default plugin icon
            self.logo_label.setText("📦")
            self.logo_label.setAlignment(Qt.AlignCenter)
            self.logo_label.setStyleSheet("font-size: 36px;")
            return

        plugin_dir = Path(self.plugin_info.path)
        relative_logo_path = self.plugin_info.manifest.logo_path
        full_logo_path = plugin_dir / relative_logo_path

        if full_logo_path and os.path.exists(full_logo_path):
            # Use the custom logo
            pixmap = QPixmap(full_logo_path)
            self.logo_label.setPixmap(pixmap)

    def _is_plugin_enabled(self) -> bool:
        """Check if the plugin is enabled.

        Returns:
            True if the plugin is enabled, False otherwise
        """
        state = self.plugin_info.metadata.get("state", "").lower()
        return state in ("active", "loaded") or self.plugin_info.metadata.get("metadata", {}).get("enabled", False)

    def _update_state(self, state: str) -> None:
        """Update the UI based on the plugin state.

        Args:
            state: The current state of the plugin
        """
        state = state.lower()

        # Update status label
        if state == "active":
            self.status_label.setText("Status: Active")
            self.status_label.setStyleSheet("font-weight: bold; color: #28a745;")  # Green
            self.setStyleSheet("QFrame { border: 1px solid #28a745; }")
        elif state == "loaded":
            self.status_label.setText("Status: Loaded")
            self.status_label.setStyleSheet("font-weight: bold; color: #17a2b8;")  # Cyan
            self.setStyleSheet("QFrame { border: 1px solid #17a2b8; }")
        elif state == "failed":
            self.status_label.setText("Status: Failed")
            self.status_label.setStyleSheet("font-weight: bold; color: #dc3545;")  # Red
            self.setStyleSheet("QFrame { border: 1px solid #dc3545; }")
        elif state == "disabled":
            self.status_label.setText("Status: Disabled")
            self.status_label.setStyleSheet("font-weight: bold; color: #6c757d;")  # Gray
            self.setStyleSheet("QFrame { border: 1px solid #6c757d; }")
        elif state == "inactive":
            self.status_label.setText("Status: Inactive")
            self.status_label.setStyleSheet("font-weight: bold; color: #fd7e14;")  # Orange
            self.setStyleSheet("QFrame { border: 1px solid #fd7e14; }")
        else:  # discovered or unknown
            self.status_label.setText("Status: Discovered")
            self.status_label.setStyleSheet("font-weight: bold; color: #6c757d;")  # Gray
            self.setStyleSheet("QFrame { border: 1px solid #6c757d; }")

        # Update checkbox
        self.enable_checkbox.setChecked(state in ("active", "loaded"))

        # Update UI state
        self.reload_button.setEnabled(state in ("active", "loaded", "failed", "inactive"))

    def _on_toggle_state(self, checked: bool) -> None:
        """Handle toggle of the enable checkbox.

        Args:
            checked: Whether the checkbox is checked
        """
        self.stateChangeRequested.emit(self.plugin_name, checked)

    def _on_reload_clicked(self) -> None:
        """Handle click of the reload button."""
        self.reloadRequested.emit(self.plugin_name)

    def _on_info_clicked(self) -> None:
        """Handle click of the info button."""
        self.infoRequested.emit(self.plugin_name)

    def update_info(self, plugin_info: PluginInfo) -> None:
        """Update the plugin information displayed in the card.

        Args:
            plugin_info: New information about the plugin
        """
        self.plugin_info = plugin_info

        # Update UI elements
        self.name_label.setText(f"<b>{self.plugin_name}</b>")
        self.version_label.setText(f"v{getattr(plugin_info.manifest, 'version', None) or '0.0.0'}")
        self.description_label.setText(getattr(plugin_info.manifest, 'description', None) or "No description available.")
        self.author_label.setText(f"Author: {getattr(plugin_info.manifest, 'author', None) or 'Unknown'}")

        # Update state
        self._update_state(plugin_info.metadata.get("state", "discovered"))


class PluginsView(QWidget):
    """Widget for displaying and managing plugins."""

    # Signal emitted when a plugin state should be changed
    pluginStateChangeRequested = Signal(str, bool)  # plugin_name, enable

    # Signal emitted when a plugin should be reloaded
    pluginReloadRequested = Signal(str)  # plugin_name

    # Signal emitted when plugin information is requested
    pluginInfoRequested = Signal(str)  # plugin_name

    def __init__(
            self,
            plugin_manager: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the plugins view.

        Args:
            plugin_manager: The plugin manager
            parent: The parent widget
        """
        super().__init__(parent)

        self._plugin_manager = plugin_manager
        self._plugin_cards: Dict[str, PluginCard] = {}

        # Set up UI
        self._setup_ui()

        # Load plugins
        self._load_plugins()

        # Set up auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_plugins)
        self._refresh_timer.start(5000)  # Refresh every 5 seconds

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header area
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Installed Plugins")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_plugins)
        header_layout.addWidget(self.refresh_button)

        # Install button
        self.install_button = QPushButton("Install New")
        self.install_button.clicked.connect(self._install_plugin)
        header_layout.addWidget(self.install_button)

        main_layout.addWidget(header_widget)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Scroll area for plugin cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Container for plugin cards
        self.plugins_container = QWidget()
        self.plugins_layout = QVBoxLayout(self.plugins_container)
        self.plugins_layout.setContentsMargins(10, 10, 10, 10)
        self.plugins_layout.setSpacing(10)
        self.plugins_layout.addStretch()

        scroll_area.setWidget(self.plugins_container)
        main_layout.addWidget(scroll_area)

    def _load_plugins(self) -> None:
        """Load and display installed plugins."""
        if not self._plugin_manager:
            return

        try:
            # Get all plugins
            plugins = self._plugin_manager.get_all_plugins()

            # Clear existing cards
            self._clear_plugin_cards()

            # Create a card for each plugin
            for name, info in plugins.items():
                self._add_plugin_card(name, info)

        except Exception as e:
            import traceback
            print(f"Error loading plugins: {str(e)}")
            print(traceback.format_exc())

    def _add_plugin_card(self, plugin_name: str, plugin_info: PluginInfo) -> None:
        """Add a plugin card to the view.

        Args:
            plugin_name: The name of the plugin
            plugin_info: Information about the plugin
        """
        # Create card
        card = PluginCard(plugin_name, plugin_info, self)

        # Connect signals
        card.stateChangeRequested.connect(self.pluginStateChangeRequested)
        card.reloadRequested.connect(self.pluginReloadRequested)
        card.infoRequested.connect(self.pluginInfoRequested)

        # Add to layout (before the stretch)
        self.plugins_layout.insertWidget(self.plugins_layout.count() - 1, card)

        # Store reference
        self._plugin_cards[plugin_name] = card

    def _clear_plugin_cards(self) -> None:
        """Clear all plugin cards from the view."""
        # Remove all cards
        for card in self._plugin_cards.values():
            self.plugins_layout.removeWidget(card)
            card.deleteLater()

        self._plugin_cards.clear()

    def _refresh_plugins(self) -> None:
        """Refresh the plugin list and update UI."""
        if not self._plugin_manager:
            return

        try:
            # Get all plugins
            plugins = self._plugin_manager.get_all_plugins()

            # Update existing cards and add new ones
            for name, info in plugins.items():
                if name in self._plugin_cards:
                    # Update existing card
                    self._plugin_cards[name].update_info(info)
                else:
                    # Add new card
                    self._add_plugin_card(name, info)

            # Remove cards for plugins that no longer exist
            for name in list(self._plugin_cards.keys()):
                if name not in plugins:
                    card = self._plugin_cards.pop(name)
                    self.plugins_layout.removeWidget(card)
                    card.deleteLater()

        except Exception as e:
            import traceback
            print(f"Error refreshing plugins: {str(e)}")
            print(traceback.format_exc())

    def _install_plugin(self) -> None:
        """Handle installing a new plugin."""
        from PySide6.QtWidgets import QFileDialog

        # Open file dialog to select plugin package
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Plugin Package",
            "",
            "Plugin Packages (*.zip *.whl *.tar.gz);;All Files (*)"
        )

        if file_path:
            # Emit signal to install plugin
            if self._plugin_manager:
                try:
                    self._plugin_manager.install_plugin(file_path)
                    self._refresh_plugins()
                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.critical(
                        self,
                        "Installation Error",
                        f"Failed to install plugin: {str(e)}"
                    )

    def update_plugin_state(self, plugin_name: str, state: str) -> None:
        """Update the state of a plugin card.

        Args:
            plugin_name: The name of the plugin
            state: The new state
        """
        if plugin_name in self._plugin_cards:
            self._plugin_cards[plugin_name]._update_state(state)

    def cleanup(self) -> None:
        """Clean up resources."""
        self._refresh_timer.stop()