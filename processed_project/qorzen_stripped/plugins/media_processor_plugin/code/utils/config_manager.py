from __future__ import annotations
'\nConfiguration management utilities for Media Processor Plugin.\n\nThis module provides functionality for automatic saving and loading of \nconfiguration data, ensuring persistence across sessions.\n'
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from pathlib import Path
from ..models.processing_config import ProcessingConfig
class ConfigManager:
    CONFIG_DIR = 'media_processor'
    FORMATS_FILE = 'format_configs.json'
    SETTINGS_FILE = 'settings.json'
    def __init__(self, file_manager: Any, logger: Any):
        self._file_manager = file_manager
        self._logger = logger
        self._config_dir: Optional[str] = None
        self._formats_file: Optional[str] = None
        self._settings_file: Optional[str] = None
        self._loaded_configs: Dict[str, ProcessingConfig] = {}
        self._settings: Dict[str, Any] = {}
    async def initialize(self) -> bool:
        try:
            self._config_dir = await self._file_manager.ensure_directory(self.CONFIG_DIR, 'plugin_data')
            if not self._config_dir:
                self._logger.error('Failed to create or access plugin data directory')
                return False
            self._formats_file = os.path.join(self._config_dir, self.FORMATS_FILE)
            self._settings_file = os.path.join(self._config_dir, self.SETTINGS_FILE)
            await self.load_configurations()
            await self.load_settings()
            self._logger.info(f'Config manager initialized with directory: {self._config_dir}')
            return True
        except Exception as e:
            self._logger.error(f'Config manager initialization failed: {str(e)}')
            return False
    async def load_configurations(self) -> Dict[str, ProcessingConfig]:
        if not self._formats_file:
            self._logger.warning('Formats file path not set')
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
                        self._logger.warning(f'Failed to load config: {str(e)}')
                self._logger.info(f'Loaded {len(self._loaded_configs)} configurations')
            else:
                self._logger.info('No saved configurations found')
        except Exception as e:
            self._logger.error(f'Error loading configurations: {str(e)}')
        return self._loaded_configs
    async def save_configurations(self) -> bool:
        if not self._formats_file:
            self._logger.warning('Formats file path not set')
            return False
        try:
            configs_list = [config.model_dump() for config in self._loaded_configs.values()]
            data = json.dumps(configs_list, default=str, indent=2)
            success = await self._file_manager.write_text(self._formats_file, data)
            if success:
                self._logger.info(f'Saved {len(self._loaded_configs)} configurations')
                return True
            else:
                self._logger.warning('Failed to save configurations')
                return False
        except Exception as e:
            self._logger.error(f'Error saving configurations: {str(e)}')
            return False
    async def load_settings(self) -> Dict[str, Any]:
        if not self._settings_file:
            self._logger.warning('Settings file path not set')
            return {}
        try:
            if await self._file_manager.file_exists(self._settings_file):
                data = await self._file_manager.read_text(self._settings_file)
                self._settings = json.loads(data)
                self._logger.info('Settings loaded successfully')
            else:
                self._logger.info('No saved settings found, using defaults')
                self._settings = {'real_time_preview': True, 'preview_quality': 'medium', 'auto_save_configs': True, 'use_intermediate_image': False, 'downloaded_models': []}
        except Exception as e:
            self._logger.error(f'Error loading settings: {str(e)}')
            self._settings = {'real_time_preview': True, 'preview_quality': 'medium', 'auto_save_configs': True, 'use_intermediate_image': False, 'downloaded_models': []}
        return self._settings
    async def save_settings(self) -> bool:
        if not self._settings_file:
            self._logger.warning('Settings file path not set')
            return False
        try:
            data = json.dumps(self._settings, indent=2)
            success = await self._file_manager.write_text(self._settings_file, data)
            if success:
                self._logger.info('Settings saved successfully')
                return True
            else:
                self._logger.warning('Failed to save settings')
                return False
        except Exception as e:
            self._logger.error(f'Error saving settings: {str(e)}')
            return False
    def get_config(self, config_id: str) -> Optional[ProcessingConfig]:
        return self._loaded_configs.get(config_id)
    def get_all_configs(self) -> Dict[str, ProcessingConfig]:
        return self._loaded_configs
    def add_or_update_config(self, config: ProcessingConfig) -> bool:
        try:
            self._loaded_configs[config.id] = config
            if self._settings.get('auto_save_configs', True):
                asyncio.create_task(self.save_configurations())
            return True
        except Exception as e:
            self._logger.error(f'Error adding/updating configuration: {str(e)}')
            return False
    def remove_config(self, config_id: str) -> bool:
        try:
            if config_id in self._loaded_configs:
                del self._loaded_configs[config_id]
                if self._settings.get('auto_save_configs', True):
                    asyncio.create_task(self.save_configurations())
                return True
            return False
        except Exception as e:
            self._logger.error(f'Error removing configuration: {str(e)}')
            return False
    def get_setting(self, key: str, default: Any=None) -> Any:
        return self._settings.get(key, default)
    def set_setting(self, key: str, value: Any) -> bool:
        try:
            self._settings[key] = value
            asyncio.create_task(self.save_settings())
            return True
        except Exception as e:
            self._logger.error(f'Error setting value: {str(e)}')
            return False