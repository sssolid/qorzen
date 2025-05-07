from __future__ import annotations

"""
Lifecycle hooks for the InitialDB plugin.

This module contains hooks for different lifecycle events of the plugin,
such as installation, updates, enabling/disabling, etc.
"""

import os
import logging
from typing import Dict, Any, Optional, cast


def pre_install(context: Dict[str, Any]) -> None:
    """Run before the plugin is installed.

    Args:
        context: Installation context containing references to core services
    """
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("initialdb")

    if logger:
        logger.info("Running pre-install hook for InitialDB plugin")

    # Check for SQLAlchemy dependency
    try:
        import sqlalchemy
        if logger:
            logger.info(f"Found SQLAlchemy version {sqlalchemy.__version__}")
    except ImportError:
        if logger:
            logger.warning("SQLAlchemy not installed, required for plugin operation")


def post_install(context: Dict[str, Any]) -> None:
    """Run after the plugin is installed.

    Args:
        context: Installation context
    """
    plugins_dir = context.get("plugins_dir")
    install_path = context.get("install_path")
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("initialdb")

    if logger:
        logger.info("Running post-install hook for InitialDB plugin")

    # Create data directories
    if install_path:
        data_dir = os.path.join(install_path, "data")
        exports_dir = os.path.join(data_dir, "exports")
        templates_dir = os.path.join(data_dir, "templates")

        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(exports_dir, exist_ok=True)
        os.makedirs(templates_dir, exist_ok=True)

        if logger:
            logger.info(f"Created data directories at {data_dir}")

    # Set up default configuration
    config_manager = context.get("config_manager")
    if config_manager:
        try:
            default_config = {
                "connection_string": "postgresql+asyncpg://initialdb:password@localhost:5432/crown_nexus",
                "default_query_limit": 1000,
                "max_query_limit": 10000,
                "ui_refresh_interval_ms": 500,
                "enable_caching": True,
                "cache_timeout": 300,
                "exports_dir": "exports",
                "templates_dir": "templates",
                "log_level": "info"
            }

            for key, value in default_config.items():
                config_path = f"plugins.initialdb.{key}"
                if config_manager.get(config_path) is None:
                    config_manager.set(config_path, value)

            if logger:
                logger.info("Installed default plugin configuration")
        except Exception as e:
            if logger:
                logger.warning(f"Error setting configuration: {e}")
                logger.warning("Using fallback configuration")

            # Fallback with minimal configuration
            default_config = {
                "connection_string": "sqlite:///data/initialdb/vehicles.db",
                "default_query_limit": 1000,
                "max_query_limit": 10000
            }

            for key, value in default_config.items():
                config_path = f"plugins.initialdb.{key}"
                if config_manager.get(config_path) is None:
                    config_manager.set(config_path, value)


def pre_uninstall(context: Dict[str, Any]) -> None:
    """Run before the plugin is uninstalled.

    Args:
        context: Uninstallation context
    """
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("initialdb")

    if logger:
        logger.info("Running pre-uninstall hook for InitialDB plugin")

    # Backup data if requested
    keep_data = context.get("keep_data", False)
    install_path = context.get("install_path")

    if keep_data and install_path:
        data_dir = os.path.join(install_path, "data")
        if os.path.exists(data_dir):
            import shutil
            import time

            backup_dir = os.path.join(
                os.path.dirname(install_path),
                f"initialdb_data_backup_{int(time.time())}"
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
    """Run after the plugin is uninstalled.

    Args:
        context: Uninstallation context
    """
    logger_manager = context.get("logger_manager")
    logger = None
    if logger_manager:
        logger = logger_manager.get_logger("initialdb")

    if logger:
        logger.info("Running post-uninstall hook for InitialDB plugin")

    # Clean up configuration (optional)
    config_manager = context.get("config_manager")
    if config_manager:
        try:
            # We're just logging here as we may not want to actually remove the config
            if logger:
                logger.info("Plugin configuration preserved for future reinstall")
        except Exception as e:
            if logger:
                logger.error(f"Error cleaning up configuration: {str(e)}")


def pre_update(context: Dict[str, Any]) -> None:
    """Run before the plugin is updated.

    Args:
        context: Update context
    """
    current_version = context.get("current_version", "0.0.0")
    new_version = context.get("new_version", "0.0.0")
    logger_manager = context.get("logger_manager")

    if logger_manager:
        plugin_logger = logger_manager.get_logger("initialdb")
        plugin_logger.info(f"Preparing to update from v{current_version} to v{new_version}")

        # Example of version-specific migration
        if current_version == "0.1.0" and new_version == "0.2.0":
            plugin_logger.info("Performing migration from v0.1.0 to v0.2.0")
            # Any migration tasks would go here


def post_update(context: Dict[str, Any]) -> None:
    """Run after the plugin is updated.

    Args:
        context: Update context
    """
    current_version = context.get("current_version", "0.0.0")
    new_version = context.get("new_version", "0.0.0")
    logger_manager = context.get("logger_manager")

    if logger_manager:
        plugin_logger = logger_manager.get_logger("initialdb")
        plugin_logger.info(f"Successfully updated from v{current_version} to v{new_version}")

        # Add new configuration options for the new version
        config_manager = context.get("config_manager")
        if config_manager:
            if new_version == "0.2.0":
                new_configs = {
                    "plugins.initialdb.enable_caching": True,
                    "plugins.initialdb.cache_timeout": 300
                }

                for path, value in new_configs.items():
                    if config_manager.get(path) is None:
                        config_manager.set(path, value)
                        plugin_logger.info(f"Added new configuration: {path} = {value}")


def post_enable(context: Dict[str, Any]) -> None:
    """Run after the plugin is enabled.

    Args:
        context: Enable context
    """
    plugin_instance = context.get("plugin_instance")
    event_bus = context.get("event_bus")
    logger_manager = context.get("logger_manager")

    if logger_manager:
        logger = logger_manager.get_logger("initialdb")
        logger.info("Plugin enabled, registering UI integration")

    # Publish event to notify other components
    if event_bus and logger_manager:
        event_bus.publish(
            event_type="initialdb/enabled",
            source="lifecycle_hooks",
            payload={"status": "enabled"}
        )


def post_disable(context: Dict[str, Any]) -> None:
    """Run after the plugin is disabled.

    Args:
        context: Disable context
    """
    plugin_instance = context.get("plugin_instance")
    if not plugin_instance:
        return

    logger_manager = context.get("logger_manager")
    if logger_manager:
        logger = logger_manager.get_logger("initialdb")
        logger.info("Plugin disabled, cleaning up UI integration")

    # Clean up UI references
    if hasattr(plugin_instance, "_main_window"):
        plugin_instance._main_window = None

    if hasattr(plugin_instance, "_tab"):
        plugin_instance._tab = None

    if hasattr(plugin_instance, "_menu_items"):
        plugin_instance._menu_items.clear()