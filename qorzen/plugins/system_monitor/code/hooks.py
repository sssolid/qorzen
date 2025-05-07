from __future__ import annotations

"""
Lifecycle hooks for the System Monitor plugin.

This module contains hooks for different lifecycle events of the plugin,
such as installation, updates, enabling/disabling, etc.
"""
import os
import shutil
import time
from typing import Dict, Any, Optional, cast


def pre_install(context: Dict[str, Any]) -> None:
    """Pre-installation hook.

    This hook is called before the plugin is installed. It performs
    any necessary tasks before the installation process begins.

    Args:
        context: Hook context
    """
    # Get logger if available
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')

    if logger:
        logger.info("Running pre-install hook for System Monitor plugin")

    # Check for psutil dependency
    try:
        import psutil
        if logger:
            logger.info(f"Found psutil version {psutil.__version__}")
    except ImportError:
        if logger:
            logger.warning("psutil not installed, plugin will use fallback metrics")


def post_install(context: Dict[str, Any]) -> None:
    """Post-installation hook.

    This hook is called after the plugin is installed. It performs
    any necessary tasks after the installation is complete.

    Args:
        context: Hook context
    """
    # Get context data
    plugins_dir = context.get('plugins_dir')
    install_path = context.get('install_path')

    # Get logger if available
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')

    if logger:
        logger.info("Running post-install hook for System Monitor plugin")

    # Create data directory for metrics history
    if install_path:
        data_dir = os.path.join(install_path, 'data')
        os.makedirs(data_dir, exist_ok=True)

        if logger:
            logger.info(f"Created data directory at {data_dir}")

    # Create default configuration if not exists
    config_manager = context.get('config_manager')
    if config_manager:
        default_config = {
            'update_interval': 5.0,
            'enable_logging': True,
            'log_history': True,
            'history_retention_days': 7,
            'alert_thresholds': {
                'cpu': 90,
                'memory': 85,
                'disk': 95,
                'network': 80
            }
        }

        # Add default config
        for key, value in default_config.items():
            config_path = f"plugins.system_monitor.{key}"
            if config_manager.get(config_path) is None:
                config_manager.set(config_path, value)

        if logger:
            logger.info("Installed default plugin configuration")


def pre_uninstall(context: Dict[str, Any]) -> None:
    """Pre-uninstall hook.

    This hook is called before the plugin is uninstalled. It performs
    any necessary clean-up before removing the plugin.

    Args:
        context: Hook context
    """
    # Get logger if available
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')

    if logger:
        logger.info("Running pre-uninstall hook for System Monitor plugin")

    # Back up metrics data if needed
    keep_data = context.get('keep_data', False)
    install_path = context.get('install_path')

    if keep_data and install_path:
        data_dir = os.path.join(install_path, 'data')
        if os.path.exists(data_dir):
            backup_dir = os.path.join(
                os.path.dirname(install_path),
                f'system_monitor_data_backup_{int(time.time())}'
            )

            if logger:
                logger.info(f"Backing up data to {backup_dir}")

            try:
                shutil.copytree(data_dir, backup_dir)
                if logger:
                    logger.info("Data backup complete")
            except Exception as e:
                if logger:
                    logger.error(f"Error backing up data: {str(e)}")


def post_uninstall(context: Dict[str, Any]) -> None:
    """Post-uninstall hook.

    This hook is called after the plugin is uninstalled. It performs
    any necessary clean-up after removing the plugin.

    Args:
        context: Hook context
    """
    # Get logger if available
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')

    if logger:
        logger.info("Running post-uninstall hook for System Monitor plugin")

    # Clean up configuration
    config_manager = context.get('config_manager')
    if config_manager:
        # Remove plugin configuration if it exists
        try:
            if config_manager.get("plugins.system_monitor") is not None:
                # In a real implementation, we would remove the configuration
                # but for this example, we'll just log the action
                if logger:
                    logger.info("Would remove plugin configuration here")
        except Exception as e:
            if logger:
                logger.error(f"Error cleaning up configuration: {str(e)}")


def pre_update(context: Dict[str, Any]) -> None:
    """Pre-update hook.

    This hook is called before the plugin is updated. It performs
    any necessary tasks before the update process begins.

    Args:
        context: Hook context
    """
    # Get update information
    current_version = context.get('current_version', '0.0.0')
    new_version = context.get('new_version', '0.0.0')

    # Get logger if available
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')

    if logger:
        logger.info(
            f"Running pre-update hook for System Monitor plugin (updating from v{current_version} to v{new_version})")

    # Check for data migration needs
    # For demonstration, we'll just log potential migrations
    if current_version == '1.0.0' and new_version == '1.1.0':
        if logger:
            logger.info("Would migrate data from v1.0.0 format to v1.1.0 format here")


def post_update(context: Dict[str, Any]) -> None:
    """Post-update hook.

    This hook is called after the plugin is updated. It performs
    any necessary tasks after the update process is complete.

    Args:
        context: Hook context
    """
    # Get update information
    current_version = context.get('current_version', '0.0.0')
    new_version = context.get('new_version', '0.0.0')

    # Get logger if available
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')

    if logger:
        logger.info(
            f"Running post-update hook for System Monitor plugin (updated from v{current_version} to v{new_version})")

    # Update configuration with any new defaults
    config_manager = context.get('config_manager')
    if config_manager:
        # For demonstration, add a new config value if we're updating to v1.1.0
        if new_version == '1.1.0':
            new_configs = {
                'plugins.system_monitor.feature_new_in_1_1': True,
                'plugins.system_monitor.alert_thresholds.gpu': 80
            }

            for path, value in new_configs.items():
                if config_manager.get(path) is None:
                    config_manager.set(path, value)
                    if logger:
                        logger.info(f"Added new configuration: {path} = {value}")


def post_enable(context: Dict[str, Any]) -> None:
    """Post-enable hook.

    This hook is called after the plugin is enabled. It initializes the UI integration
    and triggers the plugin's UI setup.

    Args:
        context: Hook context
    """
    ...
    # # Get required objects from context
    # app_core = context.get('app_core')
    # plugin_instance = context.get('plugin_instance')
    # ui_integration = context.get('ui_integration')
    #
    # # Get logger if available
    # logger_manager = context.get('logger_manager')
    # logger = None
    # if logger_manager:
    #     logger = logger_manager.get_logger('system_monitor')
    #
    # if logger:
    #     logger.info("Running post-enable hook for System Monitor plugin")
    #
    # # If we have UI integration available but no main window, wait for UI ready event
    # # Usually the plugin manager handles this, but this is a fallback just in case
    # if not ui_integration and app_core and hasattr(app_core, '_main_window') and app_core._main_window:
    #     from qorzen.ui.integration import MainWindowIntegration
    #     from qorzen.plugin_system.lifecycle import register_ui_integration
    #
    #     # Create and register UI integration
    #     ui_integration = MainWindowIntegration(app_core._main_window)
    #     register_ui_integration('system_monitor', ui_integration)
    #
    #     # Call on_ui_ready if plugin instance available
    #     if plugin_instance and hasattr(plugin_instance, 'on_ui_ready'):
    #         if logger:
    #             logger.debug("Calling on_ui_ready on plugin instance")
    #         plugin_instance.on_ui_ready(ui_integration)


def post_disable(context: Dict[str, Any]) -> None:
    """Post-disable hook.

    This hook is called after the plugin is disabled. It performs any
    necessary cleanup after disabling the plugin.

    Args:
        context: Hook context
    """
    # Get logger if available
    logger_manager = context.get('logger_manager')
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger('system_monitor')

    if logger:
        logger.info("Running post-disable hook for System Monitor plugin")

    # UI components are already cleaned up by the plugin manager
    # Save any persistent state if needed

    # Add any additional cleanup here