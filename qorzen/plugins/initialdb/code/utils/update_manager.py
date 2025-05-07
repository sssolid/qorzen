#!/usr/bin/env python
# initialdb/utils/update_manager.py
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QAction

"""
Update manager for the InitialDB application.

This module integrates the app_updater package with the application,
providing update checking, downloading, and installation capabilities.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, cast

import structlog
from PyQt6.QtWidgets import QWidget, QMenu, QStatusBar

from app_updater import UpdateController, UpdateStatus, Version
from ..config.settings import settings, APP_NAME

logger = structlog.get_logger(__name__)

# Initialize application version settings if not present
if "app_version" not in settings._settings:
    settings.set("app_version", "0.1.0")

if "update_url" not in settings._settings:
    settings.set("update_url", "http://localhost:5000")

# Add other update-related settings with defaults
UPDATE_DEFAULTS = {
    "update_check_automatically": True,
    "update_check_interval_hours": 24,
    "update_download_automatically": False,
    "update_install_automatically": False,
    "update_allow_beta_updates": False,
    "update_skipped_versions": []
}

for key, default_value in UPDATE_DEFAULTS.items():
    if key not in settings._settings:
        settings.set(key, default_value)


class UpdateManager(QObject):
    """Manager for application updates."""

    update_status_changed = pyqtSignal(object, object)  # (UpdateStatus, Optional[str])
    sync_settings_requested = pyqtSignal()

    def __init__(
            self,
            parent_widget: QWidget,
            status_bar: QStatusBar,
            help_menu: Optional[QMenu]
    ) -> None:
        """Initialize the update manager.

        Args:
            parent_widget: Parent widget for dialogs
            status_bar: Status bar for update notifications
            help_menu: Help menu for update actions
        """
        super().__init__(parent_widget)
        self._parent = parent_widget
        self._status_bar = status_bar
        self._help_menu = help_menu

        # Create update controller
        self._controller = UpdateController(
            app_name=APP_NAME,
            current_version=settings.get("app_version"),
            update_url=settings.get("update_url"),
            parent_widget=parent_widget,
            config_dir=self._get_config_dir()
        )

        # Integrate with UI
        # self._controller.add_to_status_bar(status_bar)
        self._controller.add_to_menu(help_menu)

        # Configure update settings from application settings
        self._sync_settings_to_updater()

        # Connect signals for synchronizing settings
        self.update_status_changed.connect(self._on_status_changed)
        self.sync_settings_requested.connect(self._sync_settings_from_updater)
        self._controller.update_service.on_status_changed = self.update_status_changed

        logger.info("Update manager initialized",
                    current_version=settings.get("app_version"),
                    update_url=settings.get("update_url"))

    def _get_config_dir(self) -> Path:
        """Get the configuration directory for the updater.

        Returns:
            Path to the configuration directory
        """
        # Use the application's existing config directory
        base_dir = Path(os.path.expanduser("~")) / ".initialdb"
        update_dir = base_dir / "updates"
        os.makedirs(update_dir, exist_ok=True)
        return update_dir

    def _sync_settings_to_updater(self) -> None:
        """Synchronize application settings to updater settings."""
        config = self._controller.update_service.config
        updater_settings = config.settings

        # Update settings from application settings
        updater_settings.check_automatically = settings.get("update_check_automatically", True)
        updater_settings.check_interval_hours = settings.get("update_check_interval_hours", 24)
        updater_settings.download_automatically = settings.get("update_download_automatically", False)
        updater_settings.install_automatically = settings.get("update_install_automatically", False)
        updater_settings.allow_beta_updates = settings.get("update_allow_beta_updates", False)
        updater_settings.skipped_versions = settings.get("update_skipped_versions", [])

        # Parse last check time if available
        last_check_str = settings.get("update_last_check_time")
        if last_check_str:
            try:
                updater_settings.last_check_time = datetime.fromisoformat(last_check_str)
            except (ValueError, TypeError):
                updater_settings.last_check_time = None

        # Save settings to updater's config
        config.save_settings()

        logger.debug("Synchronized settings to updater",
                     check_auto=updater_settings.check_automatically,
                     check_interval=updater_settings.check_interval_hours)

    def _sync_settings_from_updater(self) -> None:
        """Synchronize updater settings to application settings."""
        config = self._controller.update_service.config
        updater_settings = config.settings

        # Update application settings from updater settings
        settings.set("update_check_automatically", updater_settings.check_automatically)
        settings.set("update_check_interval_hours", updater_settings.check_interval_hours)
        settings.set("update_download_automatically", updater_settings.download_automatically)
        settings.set("update_install_automatically", updater_settings.install_automatically)
        settings.set("update_allow_beta_updates", updater_settings.allow_beta_updates)
        settings.set("update_skipped_versions", updater_settings.skipped_versions)

        # Save last check time if available
        if updater_settings.last_check_time:
            settings.set("update_last_check_time", updater_settings.last_check_time.isoformat())

        logger.debug("Synchronized settings from updater")

    def _on_status_changed(self, status: UpdateStatus, message: Optional[str]) -> None:
        """Handle update status changes.

        Args:
            status: The new update status
            message: Optional status message
        """
        # Save settings when status changes to keep them in sync
        if status in (UpdateStatus.AVAILABLE, UpdateStatus.NOT_AVAILABLE):
            self._sync_settings_from_updater()

        logger.debug("Update status changed",
                     status=status.name,
                     message=message)

    def add_to_menu(self, menu: Optional[QMenu] = None) -> None:
        """
        Add update items to menu, ensuring no duplicates.

        Args:
            menu: The menu to add items to, or None to use the help_menu
        """
        target_menu = menu or self._help_menu
        if not target_menu:
            logger.warning("No menu provided or available to add update item.")
            return

        # Check for existing actions to prevent duplicates
        check_updates_exists = False
        for action in target_menu.actions():
            if "Check for Updates" in action.text():
                check_updates_exists = True
                # Update the existing action to use our handler
                try:
                    action.triggered.disconnect()
                except (TypeError, RuntimeError):
                    # It's fine if it wasn't connected
                    pass
                action.triggered.connect(
                    lambda: self.check_for_updates(force=True)
                )
                break

        # Only add new action if one doesn't already exist
        if not check_updates_exists:
            # Add a separator if the menu isn't empty
            if target_menu.actions():
                target_menu.addSeparator()

            # Add the check for updates action
            check_action = QAction('Check for &Updates', self._parent)
            check_action.triggered.connect(
                lambda: self.check_for_updates(force=True)
            )
            target_menu.addAction(check_action)

        # The controller will add its own items - make sure they know
        # about our custom handling to avoid duplicates
        if hasattr(self._controller, '_add_to_menu'):
            self._controller._add_to_menu_original = self._controller._add_to_menu

            def custom_add_to_menu(menu_or_self, menu_param=None):
                # Controller has multiple add_to_menu signatures
                # Just skip adding the check for updates action
                pass

            self._controller._add_to_menu = custom_add_to_menu

    def check_for_updates(self, force: bool = False) -> None:
        """Check for updates.

        Args:
            force: Force check even if automatic checks are disabled
        """
        self._controller.update_service.check_for_updates(force=force)

    def cleanup(self) -> None:
        """Clean up resources."""
        # Sync settings before cleanup
        self._sync_settings_from_updater()

        # Clean up the controller
        self._controller.cleanup()

        logger.debug("Update manager cleaned up")