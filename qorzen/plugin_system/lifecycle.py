from __future__ import annotations
import importlib
import inspect
from typing import Any, Callable, Dict, List, Optional, Union, Type, Protocol, runtime_checkable, cast

from qorzen.plugin_system.manifest import PluginLifecycleHook, PluginManifest
from qorzen.ui.integration import UIIntegration


@runtime_checkable
class PluginInterface(Protocol):
    """Interface for plugin classes."""
    name: str
    version: str
    description: str

    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any,
                   file_manager: Any, thread_manager: Any, **kwargs: Any) -> None:
        """Initialize the plugin."""
        ...

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Called when UI is ready."""
        ...

    def shutdown(self) -> None:
        """Shut down the plugin."""
        ...


class LifecycleHookError(Exception):
    """Exception raised when a lifecycle hook fails."""

    def __init__(self, hook: PluginLifecycleHook, plugin_name: str, message: str):
        self.hook = hook
        self.plugin_name = plugin_name
        self.message = message
        super().__init__(f'Error executing {hook.value} hook for plugin {plugin_name}: {message}')


class LifecycleManager:
    """Manages plugin lifecycle hooks."""

    def __init__(self, logger_manager: Optional[Any] = None):
        """Initialize the lifecycle manager.

        Args:
            logger_manager: Optional logger manager
        """
        self._logger_manager = logger_manager
        self._logger = None
        if logger_manager:
            self._logger = logger_manager.get_logger('lifecycle_manager')

        # Store UI integration for each plugin
        self._ui_integrations: Dict[str, UIIntegration] = {}

    def set_logger(self, logger: Any) -> None:
        """Set the logger.

        Args:
            logger: Logger to use
        """
        self._logger = logger

    def log(self, message: str, level: str = 'info') -> None:
        """Log a message.

        Args:
            message: Message to log
            level: Log level
        """
        if self._logger:
            log_method = getattr(self._logger, level, None)
            if callable(log_method):
                log_method(message)

    def register_ui_integration(self, plugin_name: str, ui_integration: UIIntegration) -> None:
        """Register UI integration for a plugin.

        Args:
            plugin_name: Name of the plugin
            ui_integration: UI integration instance
        """
        self._ui_integrations[plugin_name] = ui_integration
        self.log(f"Registered UI integration for plugin '{plugin_name}'", "debug")

    def get_ui_integration(self, plugin_name: str) -> Optional[UIIntegration]:
        """Get UI integration for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            UI integration instance or None if not found
        """
        return self._ui_integrations.get(plugin_name)

    def cleanup_ui(self, plugin_name: str) -> None:
        """Clean up UI components for a plugin.

        Args:
            plugin_name: Name of the plugin
        """
        ui_integration = self._ui_integrations.get(plugin_name)
        if ui_integration:
            ui_integration.cleanup_plugin(plugin_name)
            del self._ui_integrations[plugin_name]
            self.log(f"Cleaned up UI integration for plugin '{plugin_name}'", "debug")

    def execute_hook(self, hook: PluginLifecycleHook, plugin_name: str, manifest: PluginManifest,
                     plugin_instance: Optional[Any] = None, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a lifecycle hook.

        Args:
            hook: Lifecycle hook to execute
            plugin_name: Name of the plugin
            manifest: Plugin manifest
            plugin_instance: Optional plugin instance
            context: Optional context

        Returns:
            Result of the hook execution

        Raises:
            LifecycleHookError: If the hook execution fails
        """
        context = context or {}

        if hook not in manifest.lifecycle_hooks:
            self.log(f'No {hook.value} hook defined for plugin {plugin_name}', 'debug')
            return None

        hook_path = manifest.lifecycle_hooks[hook]
        try:
            # Method on the plugin instance
            if plugin_instance is not None and '.' not in hook_path:
                if hasattr(plugin_instance, hook_path):
                    hook_method = getattr(plugin_instance, hook_path)
                    if callable(hook_method):
                        self.log(f'Executing {hook.value} hook method {hook_path} for plugin {plugin_name}', 'debug')
                        # Add UI integration to context if available
                        if "ui_integration" not in context and plugin_name in self._ui_integrations:
                            context["ui_integration"] = self._ui_integrations[plugin_name]
                        return hook_method(context=context)
                    else:
                        raise LifecycleHookError(hook, plugin_name, f'Hook {hook_path} is not callable')
                else:
                    raise LifecycleHookError(hook, plugin_name, f'Hook method {hook_path} not found on plugin instance')

            # Function in a module
            module_name, function_name = hook_path.rsplit('.', 1)
            try:
                # Try plugin-specific module first
                try:
                    module = importlib.import_module(f'{plugin_name}.{module_name}')
                except ImportError:
                    # Try absolute module path
                    module = importlib.import_module(module_name)

                hook_function = getattr(module, function_name)
                if not callable(hook_function):
                    raise LifecycleHookError(hook, plugin_name,
                                             f'Hook {function_name} in module {module_name} is not callable')

                self.log(f'Executing {hook.value} hook function {hook_path} for plugin {plugin_name}', 'debug')

                # Add plugin instance and UI integration to context if available
                if plugin_instance is not None:
                    context['plugin_instance'] = plugin_instance

                if "ui_integration" not in context and plugin_name in self._ui_integrations:
                    context["ui_integration"] = self._ui_integrations[plugin_name]

                return hook_function(context=context)
            except ImportError as e:
                raise LifecycleHookError(hook, plugin_name, f'Failed to import module {module_name}: {str(e)}') from e
            except AttributeError as e:
                raise LifecycleHookError(hook, plugin_name,
                                         f'Hook function {function_name} not found in module {module_name}: {str(e)}') from e
        except LifecycleHookError:
            raise
        except Exception as e:
            raise LifecycleHookError(hook, plugin_name, f'Unexpected error: {str(e)}') from e

    def find_plugin_hooks(self, plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
        """Find lifecycle hooks in a plugin instance.

        Args:
            plugin_instance: Plugin instance

        Returns:
            Dictionary mapping hooks to method names
        """
        hooks = {}
        for name, method in inspect.getmembers(plugin_instance, predicate=inspect.ismethod):
            for hook in PluginLifecycleHook:
                if name == hook.value:
                    hooks[hook] = name
                    continue

                if name == f'on_{hook.value}':
                    hooks[hook] = name
                    continue

                if name == f'hook_{hook.value}':
                    hooks[hook] = name
                    continue

        return hooks


# Singleton lifecycle manager
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get the singleton lifecycle manager.

    Returns:
        Lifecycle manager instance
    """
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager(None)
    return _lifecycle_manager


def set_logger(logger: Any) -> None:
    """Set the logger for the lifecycle manager.

    Args:
        logger: Logger to use
    """
    get_lifecycle_manager().set_logger(logger)


def execute_hook(hook: PluginLifecycleHook, plugin_name: str, manifest: PluginManifest,
                 plugin_instance: Optional[Any] = None, *, context: Optional[Dict[str, Any]] = None,
                 **kwargs: Any) -> Any:
    """Execute a lifecycle hook.

    Args:
        hook: Lifecycle hook to execute
        plugin_name: Name of the plugin
        manifest: Plugin manifest
        plugin_instance: Optional plugin instance
        context: Optional context
        **kwargs: Additional context

    Returns:
        Result of the hook execution
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
    """Find lifecycle hooks in a plugin instance.

    Args:
        plugin_instance: Plugin instance

    Returns:
        Dictionary mapping hooks to method names
    """
    return get_lifecycle_manager().find_plugin_hooks(plugin_instance)


def register_ui_integration(plugin_name: str, ui_integration: UIIntegration) -> None:
    """Register UI integration for a plugin.

    Args:
        plugin_name: Name of the plugin
        ui_integration: UI integration instance
    """
    get_lifecycle_manager().register_ui_integration(plugin_name, ui_integration)


def get_ui_integration(plugin_name: str) -> Optional[UIIntegration]:
    """Get UI integration for a plugin.

    Args:
        plugin_name: Name of the plugin

    Returns:
        UI integration instance or None if not found
    """
    return get_lifecycle_manager().get_ui_integration(plugin_name)


def cleanup_ui(plugin_name: str) -> None:
    """Clean up UI components for a plugin.

    Args:
        plugin_name: Name of the plugin
    """
    get_lifecycle_manager().cleanup_ui(plugin_name)