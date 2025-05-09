from __future__ import annotations
'\nLifecycle hooks for the System Monitor plugin.\n\nThis module contains hooks for different lifecycle events of the plugin,\nsuch as installation, updates, enabling/disabling, etc.\n'
import os
import shutil
import time
from typing import Dict, Any, Optional, cast
def pre_install(context: Dict[str, Any]) -> None:
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')
    if logger:
        logger.info('Running pre-install hook for System Monitor plugin')
    try:
        import psutil
        if logger:
            logger.info(f'Found psutil version {psutil.__version__}')
    except ImportError:
        if logger:
            logger.warning('psutil not installed, plugin will use fallback metrics')
def post_install(context: Dict[str, Any]) -> None:
    plugins_dir = context.get('plugins_dir')
    install_path = context.get('install_path')
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')
    if logger:
        logger.info('Running post-install hook for System Monitor plugin')
    if install_path:
        data_dir = os.path.join(install_path, 'data')
        os.makedirs(data_dir, exist_ok=True)
        if logger:
            logger.info(f'Created data directory at {data_dir}')
    config_manager = context.get('config_manager')
    if config_manager:
        default_config = {'update_interval': 5.0, 'enable_logging': True, 'log_history': True, 'history_retention_days': 7, 'alert_thresholds': {'cpu': 90, 'memory': 85, 'disk': 95, 'network': 80}}
        for key, value in default_config.items():
            config_path = f'plugins.system_monitor.{key}'
            if config_manager.get(config_path) is None:
                config_manager.set(config_path, value)
        if logger:
            logger.info('Installed default plugin configuration')
def pre_uninstall(context: Dict[str, Any]) -> None:
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')
    if logger:
        logger.info('Running pre-uninstall hook for System Monitor plugin')
    keep_data = context.get('keep_data', False)
    install_path = context.get('install_path')
    if keep_data and install_path:
        data_dir = os.path.join(install_path, 'data')
        if os.path.exists(data_dir):
            backup_dir = os.path.join(os.path.dirname(install_path), f'system_monitor_data_backup_{int(time.time())}')
            if logger:
                logger.info(f'Backing up data to {backup_dir}')
            try:
                shutil.copytree(data_dir, backup_dir)
                if logger:
                    logger.info('Data backup complete')
            except Exception as e:
                if logger:
                    logger.error(f'Error backing up data: {str(e)}')
def post_uninstall(context: Dict[str, Any]) -> None:
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')
    if logger:
        logger.info('Running post-uninstall hook for System Monitor plugin')
    config_manager = context.get('config_manager')
    if config_manager:
        try:
            if config_manager.get('plugins.system_monitor') is not None:
                if logger:
                    logger.info('Would remove plugin configuration here')
        except Exception as e:
            if logger:
                logger.error(f'Error cleaning up configuration: {str(e)}')
def pre_update(context: Dict[str, Any]) -> None:
    current_version = context.get('current_version', '0.0.0')
    new_version = context.get('new_version', '0.0.0')
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')
    if logger:
        logger.info(f'Running pre-update hook for System Monitor plugin (updating from v{current_version} to v{new_version})')
    if current_version == '1.0.0' and new_version == '1.1.0':
        if logger:
            logger.info('Would migrate data from v1.0.0 format to v1.1.0 format here')
def post_update(context: Dict[str, Any]) -> None:
    current_version = context.get('current_version', '0.0.0')
    new_version = context.get('new_version', '0.0.0')
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')
    if logger:
        logger.info(f'Running post-update hook for System Monitor plugin (updated from v{current_version} to v{new_version})')
    config_manager = context.get('config_manager')
    if config_manager:
        if new_version == '1.1.0':
            new_configs = {'plugins.system_monitor.feature_new_in_1_1': True, 'plugins.system_monitor.alert_thresholds.gpu': 80}
            for path, value in new_configs.items():
                if config_manager.get(path) is None:
                    config_manager.set(path, value)
                    if logger:
                        logger.info(f'Added new configuration: {path} = {value}')
def post_enable(context: Dict[str, Any]) -> None:
    ...
def post_disable(context: Dict[str, Any]) -> None:
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')
    if logger:
        logger.info('Running post-disable hook for System Monitor plugin')