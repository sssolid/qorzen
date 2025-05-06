from __future__ import annotations

import importlib
import inspect
from typing import Any, Callable, Dict, List, Optional, Union, Type, cast

from qorzen.plugin_system.manifest import PluginLifecycleHook, PluginManifest


class LifecycleHookError(Exception):
    """Exception raised when there's an error executing a lifecycle hook."""

    def __init__(self, hook: PluginLifecycleHook, plugin_name: str, message: str):
        self.hook = hook
        self.plugin_name = plugin_name
        self.message = message
        super().__init__(f"Error executing {hook.value} hook for plugin {plugin_name}: {message}")


class LifecycleManager:
    """Manager for plugin lifecycle hooks."""

    def __init__(self, logger: Optional[Callable[[str, str], None]] = None):
        self.logger = logger or (lambda msg, level: None)

    def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        if self.logger:
            self.logger(message, level)

    def execute_hook(
            self,
            hook: PluginLifecycleHook,
            plugin_name: str,
            manifest: PluginManifest,
            plugin_instance: Optional[Any] = None,
            **context: Any
    ) -> Any:
        """
        Execute a lifecycle hook.

        Args:
            hook: The hook to execute
            plugin_name: The name of the plugin
            manifest: The plugin manifest
            plugin_instance: The plugin instance, if available
            **context: Additional context for the hook

        Returns:
            The result of the hook execution

        Raises:
            LifecycleHookError: If there's an error executing the hook
        """
        # Check if the hook is defined in the manifest
        if hook not in manifest.lifecycle_hooks:
            self.log(f"No {hook.value} hook defined for plugin {plugin_name}", "debug")
            return None

        hook_path = manifest.lifecycle_hooks[hook]

        try:
            # If the hook is a method on the plugin instance
            if plugin_instance is not None and "." not in hook_path:
                if hasattr(plugin_instance, hook_path):
                    hook_method = getattr(plugin_instance, hook_path)
                    if callable(hook_method):
                        self.log(f"Executing {hook.value} hook method {hook_path} for plugin {plugin_name}", "debug")
                        return hook_method(context=context)
                    else:
                        raise LifecycleHookError(
                            hook, plugin_name, f"Hook {hook_path} is not callable"
                        )
                else:
                    raise LifecycleHookError(
                        hook, plugin_name, f"Hook method {hook_path} not found on plugin instance"
                    )

            # If the hook is a module.function path
            module_name, function_name = hook_path.rsplit(".", 1)

            try:
                # Try to import relative to the plugin
                try:
                    module = importlib.import_module(f"{plugin_name}.{module_name}")
                except ImportError:
                    # Try absolute import
                    module = importlib.import_module(module_name)

                hook_function = getattr(module, function_name)
                if not callable(hook_function):
                    raise LifecycleHookError(
                        hook, plugin_name, f"Hook {function_name} in module {module_name} is not callable"
                    )

                self.log(f"Executing {hook.value} hook function {hook_path} for plugin {plugin_name}", "debug")

                # Call the hook function with context
                if plugin_instance is not None:
                    return hook_function(plugin_instance, context=context)
                else:
                    return hook_function(context=context)

            except ImportError as e:
                raise LifecycleHookError(
                    hook, plugin_name, f"Failed to import module {module_name}: {str(e)}"
                ) from e
            except AttributeError as e:
                raise LifecycleHookError(
                    hook, plugin_name, f"Hook function {function_name} not found in module {module_name}: {str(e)}"
                ) from e

        except LifecycleHookError:
            raise
        except Exception as e:
            raise LifecycleHookError(
                hook, plugin_name, f"Unexpected error: {str(e)}"
            ) from e

    def find_plugin_hooks(self, plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
        """
        Find lifecycle hooks defined on a plugin instance.

        Args:
            plugin_instance: The plugin instance

        Returns:
            A dictionary mapping hooks to method names
        """
        hooks = {}

        # Check for methods with hook naming patterns
        for name, method in inspect.getmembers(plugin_instance, predicate=inspect.ismethod):
            # Check for direct hook names
            for hook in PluginLifecycleHook:
                if name == hook.value:
                    hooks[hook] = name
                    continue

                # Check for on_* prefix
                if name == f"on_{hook.value}":
                    hooks[hook] = name
                    continue

                # Check for hook_* prefix
                if name == f"hook_{hook.value}":
                    hooks[hook] = name
                    continue

        return hooks


# Create a singleton instance
lifecycle_manager = LifecycleManager()


def execute_hook(
        hook: PluginLifecycleHook,
        plugin_name: str,
        manifest: PluginManifest,
        plugin_instance: Optional[Any] = None,
        **context: Any
) -> Any:
    """
    Execute a lifecycle hook.

    Args:
        hook: The hook to execute
        plugin_name: The name of the plugin
        manifest: The plugin manifest
        plugin_instance: The plugin instance, if available
        **context: Additional context for the hook

    Returns:
        The result of the hook execution

    Raises:
        LifecycleHookError: If there's an error executing the hook
    """
    return lifecycle_manager.execute_hook(
        hook=hook,
        plugin_name=plugin_name,
        manifest=manifest,
        plugin_instance=plugin_instance,
        **context
    )


def set_logger(logger: Callable[[str, str], None]) -> None:
    """Set the logger for the lifecycle manager."""
    lifecycle_manager.logger = logger


def find_plugin_hooks(plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
    """
    Find lifecycle hooks defined on a plugin instance.

    Args:
        plugin_instance: The plugin instance

    Returns:
        A dictionary mapping hooks to method names
    """
    return lifecycle_manager.find_plugin_hooks(plugin_instance)