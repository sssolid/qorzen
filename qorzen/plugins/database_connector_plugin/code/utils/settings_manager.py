from __future__ import annotations

"""
Settings manager for the Database Connector Plugin.

This module provides utilities for loading and saving plugin settings
to the plugin's data directory rather than the main config.yaml.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, cast

from qorzen.utils.exceptions import PluginError


class SettingsManager:
    """Manages plugin settings stored in the plugin's data directory."""

    def __init__(
            self,
            plugin_name: str,
            file_manager: Any,
            logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize the settings manager.

        Args:
            plugin_name: Name of the plugin
            file_manager: File manager instance for file operations
            logger: Optional logger for logging messages
        """
        self.plugin_name = plugin_name
        self._file_manager = file_manager
        self._logger = logger or logging.getLogger(plugin_name)

    async def load_settings(self, settings_class: Any) -> Any:
        """
        Load settings from the plugin's data directory.

        Args:
            settings_class: Pydantic model class to use for settings

        Returns:
            Instance of settings_class populated with saved settings
        """
        try:
            if not self._file_manager:
                self._logger.warning("No file manager available, using default settings")
                return settings_class()

            file_path = f"{self.plugin_name}/settings.json"

            try:
                file_info = await self._file_manager.get_file_info(file_path, "plugin_data")
                if not file_info:
                    self._logger.info("No settings file found, using default settings")
                    return settings_class()
            except Exception as e:
                self._logger.debug(f"Error checking settings file: {str(e)}")
                return settings_class()

            json_data = await self._file_manager.read_text(file_path, "plugin_data")
            settings_dict = json.loads(json_data)
            settings = settings_class(**settings_dict)
            self._logger.debug("Loaded plugin settings successfully")
            return settings
        except Exception as e:
            self._logger.error(f"Failed to load settings: {str(e)}")
            return settings_class()

    async def save_settings(self, settings: Any) -> None:
        """
        Save settings to the plugin's data directory.

        Args:
            settings: Settings instance to save
        """
        try:
            if not self._file_manager:
                self._logger.warning("No file manager available, settings not saved")
                return

            file_path = f"{self.plugin_name}/settings.json"
            await self._file_manager.ensure_directory(self.plugin_name, "plugin_data")

            settings_dict = settings.dict()
            json_data = json.dumps(settings_dict, indent=2, default=str)

            await self._file_manager.write_text(file_path, json_data, "plugin_data")
            self._logger.debug("Saved plugin settings successfully")
        except Exception as e:
            self._logger.error(f"Failed to save settings: {str(e)}")
            raise PluginError(f"Failed to save settings: {str(e)}")