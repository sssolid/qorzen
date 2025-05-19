from __future__ import annotations

"""
Configuration management utilities for Media Processor Plugin.

This module provides functionality for automatic saving and loading of 
configuration data, ensuring persistence across sessions.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from pathlib import Path

from ..models.processing_config import ProcessingConfig


class ConfigManager:
    """
    Manages the storage and retrieval of format configurations and plugin settings.
    """

    CONFIG_DIR = "media_processor"
    FORMATS_FILE = "format_configs.json"
    SETTINGS_FILE = "settings.json"

    def __init__(self, file_manager: Any, logger: Any):
        """
        Initialize the config manager.

        Args:
            file_manager: The file manager instance from Qorzen core
            logger: Logger instance
        """
        self._file_manager = file_manager
        self._logger = logger
        self._config_dir: Optional[str] = None
        self._formats_file: Optional[str] = None
        self._settings_file: Optional[str] = None
        self._loaded_configs: Dict[str, ProcessingConfig] = {}
        self._settings: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """
        Initialize the configuration system. Creates necessary directories and
        loads existing configurations.

        Returns:
            bool: True if initialization was successful
        """
        try:
            # Ensure the configuration directory exists
            self._config_dir = await self._file_manager.ensure_directory(self.CONFIG_DIR, "plugin_data")

            if not self._config_dir:
                self._logger.error("Failed to create or access plugin data directory")
                return False

            # Set up paths
            self._formats_file = os.path.join(self._config_dir, self.FORMATS_FILE)
            self._settings_file = os.path.join(self._config_dir, self.SETTINGS_FILE)

            # Load configurations
            await self.load_configurations()
            await self.load_settings()

            self._logger.info(f"Config manager initialized with directory: {self._config_dir}")
            return True

        except Exception as e:
            self._logger.error(f"Config manager initialization failed: {str(e)}")
            return False

    async def load_configurations(self) -> Dict[str, ProcessingConfig]:
        """
        Load saved format configurations from disk.

        Returns:
            Dict[str, ProcessingConfig]: Dictionary of loaded configurations
        """
        if not self._formats_file:
            self._logger.warning("Formats file path not set")
            return {}

        try:
            if await self._file_manager.file_exists(self._formats_file):
                data = await self._file_manager.read_text(self._formats_file)
                config_dicts = json.loads(data)

                for config_dict in config_dicts:
                    try:
                        config = ProcessingConfig(**config_dict)
                        self._loaded_configs[config.id] = config
                    except Exception as e:
                        self._logger.warning(f"Failed to load config: {str(e)}")

                self._logger.info(f"Loaded {len(self._loaded_configs)} configurations")
            else:
                self._logger.info("No saved configurations found")

        except Exception as e:
            self._logger.error(f"Error loading configurations: {str(e)}")

        return self._loaded_configs

    async def save_configurations(self) -> bool:
        """
        Save all configurations to disk.

        Returns:
            bool: True if save was successful
        """
        if not self._formats_file:
            self._logger.warning("Formats file path not set")
            return False

        try:
            configs_list = [config.model_dump() for config in self._loaded_configs.values()]
            data = json.dumps(configs_list, default=str, indent=2)
            success = await self._file_manager.write_text(self._formats_file, data)

            if success:
                self._logger.info(f"Saved {len(self._loaded_configs)} configurations")
                return True
            else:
                self._logger.warning("Failed to save configurations")
                return False

        except Exception as e:
            self._logger.error(f"Error saving configurations: {str(e)}")
            return False

    async def load_settings(self) -> Dict[str, Any]:
        """
        Load plugin settings from disk.

        Returns:
            Dict[str, Any]: Plugin settings
        """
        if not self._settings_file:
            self._logger.warning("Settings file path not set")
            return {}

        try:
            if await self._file_manager.file_exists(self._settings_file):
                data = await self._file_manager.read_text(self._settings_file)
                self._settings = json.loads(data)
                self._logger.info("Settings loaded successfully")
            else:
                self._logger.info("No saved settings found, using defaults")
                # Initialize with defaults
                self._settings = {
                    "real_time_preview": True,
                    "preview_quality": "medium",
                    "auto_save_configs": True,
                    "use_intermediate_image": False,
                    "downloaded_models": []
                }

        except Exception as e:
            self._logger.error(f"Error loading settings: {str(e)}")
            # Initialize with defaults on error
            self._settings = {
                "real_time_preview": True,
                "preview_quality": "medium",
                "auto_save_configs": True,
                "use_intermediate_image": False,
                "downloaded_models": []
            }

        return self._settings

    async def save_settings(self) -> bool:
        """
        Save plugin settings to disk.

        Returns:
            bool: True if save was successful
        """
        if not self._settings_file:
            self._logger.warning("Settings file path not set")
            return False

        try:
            data = json.dumps(self._settings, indent=2)
            success = await self._file_manager.write_text(self._settings_file, data)

            if success:
                self._logger.info("Settings saved successfully")
                return True
            else:
                self._logger.warning("Failed to save settings")
                return False

        except Exception as e:
            self._logger.error(f"Error saving settings: {str(e)}")
            return False

    def get_config(self, config_id: str) -> Optional[ProcessingConfig]:
        """
        Get a configuration by ID.

        Args:
            config_id: The configuration ID

        Returns:
            Optional[ProcessingConfig]: The configuration or None if not found
        """
        return self._loaded_configs.get(config_id)

    def get_all_configs(self) -> Dict[str, ProcessingConfig]:
        """
        Get all loaded configurations.

        Returns:
            Dict[str, ProcessingConfig]: Dictionary of configurations
        """
        return self._loaded_configs

    def add_or_update_config(self, config: ProcessingConfig) -> bool:
        """
        Add or update a configuration.

        Args:
            config: The configuration to add or update

        Returns:
            bool: True if successful
        """
        try:
            self._loaded_configs[config.id] = config

            if self._settings.get("auto_save_configs", True):
                asyncio.create_task(self.save_configurations())

            return True
        except Exception as e:
            self._logger.error(f"Error adding/updating configuration: {str(e)}")
            return False

    def remove_config(self, config_id: str) -> bool:
        """
        Remove a configuration.

        Args:
            config_id: The ID of the configuration to remove

        Returns:
            bool: True if successful
        """
        try:
            if config_id in self._loaded_configs:
                del self._loaded_configs[config_id]

                if self._settings.get("auto_save_configs", True):
                    asyncio.create_task(self.save_configurations())

                return True
            return False
        except Exception as e:
            self._logger.error(f"Error removing configuration: {str(e)}")
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: The setting key
            default: Default value if setting not found

        Returns:
            Any: The setting value or default
        """
        return self._settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a setting value.

        Args:
            key: The setting key
            value: The setting value

        Returns:
            bool: True if successful
        """
        try:
            self._settings[key] = value
            asyncio.create_task(self.save_settings())
            return True
        except Exception as e:
            self._logger.error(f"Error setting value: {str(e)}")
            return False