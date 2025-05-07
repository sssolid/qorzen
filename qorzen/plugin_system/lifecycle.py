from __future__ import annotations

import importlib
import inspect
import weakref
from typing import Any, Callable, Dict, List, Optional, Union, Type, Protocol, runtime_checkable, cast

from qorzen.plugin_system.manifest import PluginLifecycleHook, PluginManifest
from qorzen.ui.integration import UIIntegration


@runtime_checkable
class PluginInterface(Protocol):
    """Interface that all plugins must implement."""
    name: str
    version: str
    description: str

    def initialize(
            self,
            event_bus: Any,
            logger_provider: Any,
            config_provider: Any,
            file_manager: Any,
            thread_manager: Any,
            **kwargs: Any
    ) -> None:
        """Initialize the plugin with required components."""
        ...

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Called when the UI is ready and the plugin can add UI components."""
        ...

    def shutdown(self) -> None:
        """Shutdown the plugin and clean up resources."""
        ...


class LifecycleHookError(Exception):
    """Exception raised when a lifecycle hook execution fails."""

    def __init__(self, hook: PluginLifecycleHook, plugin_name: str, message: str):
        self.hook = hook
        self.plugin_name = plugin_name
        self.message = message
        super().__init__(
            f'Error executing {hook.value} hook for plugin {plugin_name}: {message}'
        )


class LifecycleManager:
    """Manages plugin lifecycle hooks and UI integration."""

    def __init__(self, logger_manager: Optional[Any] = None):
        """Initialize the lifecycle manager.

        Args:
            logger_manager: The logger manager to use for logging.
        """
        self._logger_manager = logger_manager
        self._logger = None
        if logger_manager:
            self._logger = logger_manager.get_logger('lifecycle_manager')

        # Store UI integrations as a dictionary using plugin name as key
        # Use strong references to ensure Qt objects aren't garbage collected
        self._ui_integrations: Dict[str, UIIntegration] = {}

        # Keep a reference to the main window to prevent it from being garbage collected
        self._main_window_ref: Optional[Any] = None

        # Track active hooks to prevent recursive calls
        self._active_hooks: Dict[str, set] = {}

    def set_logger(self, logger: Any) -> None:
        """Set the logger for the lifecycle manager.

        Args:
            logger: The logger to use.
        """
        self._logger = logger

    def log(self, message: str, level: str = 'info') -> None:
        """Log a message.

        Args:
            message: The message to log.
            level: The log level to use.
        """
        if self._logger:
            log_method = getattr(self._logger, level, None)
            if callable(log_method):
                log_method(message)

    def register_ui_integration(
            self, plugin_name: str, ui_integration: UIIntegration, main_window: Optional[Any] = None
    ) -> None:
        """Register a UI integration for a plugin.

        Args:
            plugin_name: The name of the plugin.
            ui_integration: The UI integration to register.
            main_window: The main window reference, if available.
        """
        self._ui_integrations[plugin_name] = ui_integration

        # If the main window is provided, store a reference to it
        if main_window is not None:
            self._main_window_ref = main_window

        self.log(f"Registered UI integration for plugin '{plugin_name}'", 'debug')

    def get_ui_integration(self, plugin_name: str) -> Optional[UIIntegration]:
        """Get the UI integration for a plugin.

        Args:
            plugin_name: The name of the plugin.

        Returns:
            The UI integration for the plugin, or None if not found.
        """
        return self._ui_integrations.get(plugin_name)

    def cleanup_ui(self, plugin_name: str) -> None:
        """Clean up UI components for a plugin.

        Args:
            plugin_name: The name of the plugin.
        """
        ui_integration = self._ui_integrations.get(plugin_name)
        if ui_integration:
            # Make sure to handle exceptions during cleanup
            try:
                ui_integration.cleanup_plugin(plugin_name)
                del self._ui_integrations[plugin_name]
                self.log(f"Cleaned up UI integration for plugin '{plugin_name}'", 'debug')
            except Exception as e:
                self.log(
                    f"Error during UI cleanup for plugin '{plugin_name}': {str(e)}",
                    'error'
                )

    def execute_hook(
            self,
            hook: PluginLifecycleHook,
            plugin_name: str,
            manifest: PluginManifest,
            plugin_instance: Optional[Any] = None,
            context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a lifecycle hook for a plugin.

        Args:
            hook: The lifecycle hook to execute.
            plugin_name: The name of the plugin.
            manifest: The plugin manifest.
            plugin_instance: The plugin instance, if available.
            context: Additional context to pass to the hook.

        Returns:
            The result of the hook execution.

        Raises:
            LifecycleHookError: If the hook execution fails.
        """
        context = context or {}

        # Check if hook is defined in manifest
        if hook not in manifest.lifecycle_hooks:
            self.log(f'No {hook.value} hook defined for plugin {plugin_name}', 'debug')
            return None

        # Get hook path from manifest
        hook_path = manifest.lifecycle_hooks[hook]

        # Prevent recursive hook execution
        hook_key = f"{plugin_name}:{hook.value}"
        if hook_key not in self._active_hooks:
            self._active_hooks[hook_key] = set()

        if hook_path in self._active_hooks[hook_key]:
            self.log(
                f'Recursive hook detected: {hook.value} for plugin {plugin_name}',
                'warning'
            )
            return None

        self._active_hooks[hook_key].add(hook_path)

        try:
            # Case 1: Hook is a method on the plugin instance
            if plugin_instance is not None and '.' not in hook_path:
                if hasattr(plugin_instance, hook_path):
                    hook_method = getattr(plugin_instance, hook_path)
                    if callable(hook_method):
                        self.log(
                            f'Executing {hook.value} hook method {hook_path} for plugin {plugin_name}',
                            'debug'
                        )

                        # Add UI integration to context if available
                        if 'ui_integration' not in context and plugin_name in self._ui_integrations:
                            context['ui_integration'] = self._ui_integrations[plugin_name]

                        return hook_method(context=context)
                    else:
                        raise LifecycleHookError(
                            hook, plugin_name, f'Hook {hook_path} is not callable'
                        )
                else:
                    raise LifecycleHookError(
                        hook, plugin_name, f'Hook method {hook_path} not found on plugin instance'
                    )

            # Case 2: Hook is in a separate module
            module_name, function_name = hook_path.rsplit('.', 1)
            try:
                # Try to import as a submodule of the plugin
                try:
                    module = importlib.import_module(f'{plugin_name}.{module_name}')
                except ImportError:
                    # If that fails, try importing directly
                    module = importlib.import_module(module_name)

                hook_function = getattr(module, function_name)
                if not callable(hook_function):
                    raise LifecycleHookError(
                        hook,
                        plugin_name,
                        f'Hook {function_name} in module {module_name} is not callable'
                    )

                self.log(
                    f'Executing {hook.value} hook function {hook_path} for plugin {plugin_name}',
                    'debug'
                )

                # Add plugin instance and UI integration to context
                if plugin_instance is not None:
                    context['plugin_instance'] = plugin_instance

                if 'ui_integration' not in context and plugin_name in self._ui_integrations:
                    context['ui_integration'] = self._ui_integrations[plugin_name]

                return hook_function(context=context)

            except ImportError as e:
                raise LifecycleHookError(
                    hook,
                    plugin_name,
                    f'Failed to import module {module_name}: {str(e)}'
                ) from e

            except AttributeError as e:
                raise LifecycleHookError(
                    hook,
                    plugin_name,
                    f'Hook function {function_name} not found in module {module_name}: {str(e)}'
                ) from e

        except LifecycleHookError:
            raise

        except Exception as e:
            raise LifecycleHookError(
                hook, plugin_name, f'Unexpected error: {str(e)}'
            ) from e

        finally:
            # Remove hook from active hooks
            if hook_key in self._active_hooks:
                self._active_hooks[hook_key].remove(hook_path)
                if not self._active_hooks[hook_key]:
                    del self._active_hooks[hook_key]

    def find_plugin_hooks(self, plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
        """Find lifecycle hooks defined in a plugin instance.

        Args:
            plugin_instance: The plugin instance to inspect.

        Returns:
            A dictionary of lifecycle hooks and their method names.
        """
        hooks = {}

        for name, method in inspect.getmembers(plugin_instance, predicate=inspect.ismethod):
            for hook in PluginLifecycleHook:
                # Match exact hook name
                if name == hook.value:
                    hooks[hook] = name
                    continue

                # Match "on_<hook_name>" pattern
                if name == f'on_{hook.value}':
                    hooks[hook] = name
                    continue

                # Match "hook_<hook_name>" pattern
                if name == f'hook_{hook.value}':
                    hooks[hook] = name
                    continue

        return hooks


# Module-level singleton
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get the singleton lifecycle manager instance.

    Returns:
        The lifecycle manager instance.
    """
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager(None)
    return _lifecycle_manager


def set_logger(logger: Any) -> None:
    """Set the logger for the lifecycle manager.

    Args:
        logger: The logger to use.
    """
    get_lifecycle_manager().set_logger(logger)


def execute_hook(
        hook: PluginLifecycleHook,
        plugin_name: str,
        manifest: PluginManifest,
        plugin_instance: Optional[Any] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
) -> Any:
    """Execute a lifecycle hook for a plugin.

    Args:
        hook: The lifecycle hook to execute.
        plugin_name: The name of the plugin.
        manifest: The plugin manifest.
        plugin_instance: The plugin instance, if available.
        context: Additional context to pass to the hook.
        **kwargs: Additional keyword arguments to add to the context.

    Returns:
        The result of the hook execution.
    """
    if context is None:
        context = kwargs
    else:
        context.update(kwargs)

    return get_lifecycle_manager().execute_hook(
        hook=hook,
        plugin_name=plugin_name,
        manifest=manifest,
        plugin_instance=plugin_instance,
        context=context
    )


def find_plugin_hooks(plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
    """Find lifecycle hooks defined in a plugin instance.

    Args:
        plugin_instance: The plugin instance to inspect.

    Returns:
        A dictionary of lifecycle hooks and their method names.
    """
    return get_lifecycle_manager().find_plugin_hooks(plugin_instance)


def register_ui_integration(
        plugin_name: str, ui_integration: UIIntegration, main_window: Optional[Any] = None
) -> None:
    """Register a UI integration for a plugin.

    Args:
        plugin_name: The name of the plugin.
        ui_integration: The UI integration to register.
        main_window: The main window reference, if available.
    """
    get_lifecycle_manager().register_ui_integration(
        plugin_name, ui_integration, main_window
    )


def get_ui_integration(plugin_name: str) -> Optional[UIIntegration]:
    """Get the UI integration for a plugin.

    Args:
        plugin_name: The name of the plugin.

    Returns:
        The UI integration for the plugin, or None if not found.
    """
    return get_lifecycle_manager().get_ui_integration(plugin_name)


def cleanup_ui(plugin_name: str) -> None:
    """Clean up UI components for a plugin.

    Args:
        plugin_name: The name of the plugin.
    """
    get_lifecycle_manager().cleanup_ui(plugin_name)