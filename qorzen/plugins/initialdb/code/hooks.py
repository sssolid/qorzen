from __future__ import annotations
from typing import Dict, Any, Optional, cast
from qorzen.ui.integration import UIIntegration, MainWindowIntegration
from qorzen.core.event_model import EventType, Event
from qorzen.plugin_system.lifecycle import register_ui_integration


def post_enable(context: Dict[str, Any]) -> None:
    """Post-enable hook for InitialDB plugin.

    This hook is called after the plugin is enabled. It initializes the UI integration
    and triggers the plugin's UI setup.

    Args:
        context: Hook context containing app_core, plugin_instance, etc.
    """
    # Get required objects from context
    app_core = context.get('app_core')
    plugin_instance = context.get('plugin_instance')
    event_bus = context.get('event_bus')

    if not app_core or not plugin_instance:
        return

    # Check if main window is available
    if hasattr(app_core, '_main_window') and app_core._main_window:
        # Create UI integration for the main window
        ui_integration = MainWindowIntegration(app_core._main_window)

        # Register UI integration with lifecycle manager
        plugin_name = getattr(plugin_instance, 'name', 'initialdb')
        register_ui_integration(plugin_name, ui_integration)

        # If plugin has on_ui_ready method, call it directly
        if hasattr(plugin_instance, 'on_ui_ready'):
            plugin_instance.on_ui_ready(ui_integration)
        else:
            # Legacy support: set main_window property and publish UI ready event
            plugin_instance._main_window = app_core._main_window

            if event_bus:
                event_bus.publish(
                    event_type=EventType.UI_READY.value,
                    source=f'hook:{plugin_name}',
                    payload={'main_window': app_core._main_window}
                )


def post_disable(context: Dict[str, Any]) -> None:
    """Post-disable hook for InitialDB plugin.

    This hook is called after the plugin is disabled. It cleans up any UI components
    created by the plugin.

    Args:
        context: Hook context
    """
    # Get plugin instance from context
    plugin_instance = context.get('plugin_instance')

    if not plugin_instance:
        return

    # Clean up main window reference (legacy support)
    if hasattr(plugin_instance, '_main_window'):
        plugin_instance._main_window = None


def pre_uninstall(context: Dict[str, Any]) -> None:
    """Pre-uninstall hook for InitialDB plugin.

    This hook is called before the plugin is uninstalled. It performs
    any necessary cleanup before the plugin is removed.

    Args:
        context: Hook context
    """
    # Any pre-uninstall cleanup can be added here
    pass


def post_uninstall(context: Dict[str, Any]) -> None:
    """Post-uninstall hook for InitialDB plugin.

    This hook is called after the plugin is uninstalled. It performs
    any necessary cleanup after the plugin is removed.

    Args:
        context: Hook context
    """
    # Any post-uninstall cleanup can be added here
    pass


def pre_update(context: Dict[str, Any]) -> None:
    """Pre-update hook for InitialDB plugin.

    This hook is called before the plugin is updated. It performs any necessary
    tasks before the update process begins.

    Args:
        context: Hook context
    """
    # Get information about the update
    current_version = context.get('current_version', '0.0.0')
    new_version = context.get('new_version', '0.0.0')

    # Log information about the update
    logger = context.get('logger_manager')
    if logger:
        plugin_logger = logger.get_logger('initialdb')
        plugin_logger.info(f"Preparing to update from v{current_version} to v{new_version}")


def post_update(context: Dict[str, Any]) -> None:
    """Post-update hook for InitialDB plugin.

    This hook is called after the plugin is updated. It performs any necessary
    tasks after the update process is complete.

    Args:
        context: Hook context
    """
    # Get information about the update
    current_version = context.get('current_version', '0.0.0')
    new_version = context.get('new_version', '0.0.0')

    # Log information about the update
    logger = context.get('logger_manager')
    if logger:
        plugin_logger = logger.get_logger('initialdb')
        plugin_logger.info(f"Successfully updated from v{current_version} to v{new_version}")


def pre_install(context: Dict[str, Any]) -> None:
    """Pre-install hook for InitialDB plugin.

    This hook is called before the plugin is installed. It performs any
    necessary tasks before the installation process begins.

    Args:
        context: Hook context
    """
    # Any pre-installation tasks can be added here
    pass


def post_install(context: Dict[str, Any]) -> None:
    """Post-install hook for InitialDB plugin.

    This hook is called after the plugin is installed. It performs any
    necessary tasks after the installation is complete.

    Args:
        context: Hook context
    """
    # Any post-installation tasks can be added here
    pass