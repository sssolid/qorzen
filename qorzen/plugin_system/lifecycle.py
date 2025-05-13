from __future__ import annotations

import abc
import asyncio
import importlib
import inspect
import weakref
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

from qorzen.plugin_system.manifest import PluginLifecycleHook, PluginManifest
from qorzen.ui.ui_integration import UIIntegration
from qorzen.core.dependency_manager import DependencyManager


class PluginLifecycleState(Enum):
    """States in a plugin's lifecycle."""
    DISCOVERED = auto()
    LOADING = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    UI_READY = auto()
    ACTIVE = auto()
    DISABLING = auto()
    INACTIVE = auto()
    FAILED = auto()


class LifecycleHookError(Exception):
    """Exception raised when a lifecycle hook fails."""

    def __init__(self, hook: PluginLifecycleHook, plugin_name: str, message: str):
        self.hook = hook
        self.plugin_name = plugin_name
        self.message = message
        super().__init__(f'Error executing {hook.value} hook for plugin {plugin_name}: {message}')


class LifecycleManager:
    """
    Manages the lifecycle of plugins asynchronously.
    Handles state transitions, UI integration, and lifecycle hooks.
    """

    def __init__(self, logger_manager: Optional[Any] = None):
        """
        Initialize the async lifecycle manager.

        Args:
            logger_manager: Optional logger manager for logging
        """
        self._logger_manager = logger_manager
        self._logger = None
        if logger_manager:
            self._logger = logger_manager.get_logger('lifecycle_manager')
        self._ui_integrations: Dict[str, UIIntegration] = {}
        self._main_window_ref = None
        self._active_hooks: Dict[str, set] = {}
        self._plugin_states: Dict[str, PluginLifecycleState] = {}
        self._plugin_states_lock = asyncio.Lock()
        self._ui_integrations_lock = asyncio.Lock()
        self._hooks_lock = asyncio.Lock()
        self._ui_ready_events: Dict[str, asyncio.Event] = {}
        self._thread_manager: Optional[Any] = None
        self._plugin_manager: Optional[Any] = None
        self._ui_setup_plugins: set = set()
        self._ui_lock = asyncio.Lock()

    def set_thread_manager(self, thread_manager: Any) -> None:
        """Set the thread manager used for main thread operations."""
        self._thread_manager = thread_manager

    def set_plugin_manager(self, plugin_manager: Any) -> None:
        """Set the plugin manager reference."""
        self._plugin_manager = plugin_manager

    def set_logger(self, logger: Any) -> None:
        """Set the logger instance."""
        self._logger = logger

    def log(self, message: str, level: str = 'info') -> None:
        """Log a message with the specified level."""
        if self._logger:
            log_method = getattr(self._logger, level, None)
            if callable(log_method):
                log_method(message)

    async def get_plugin_state(self, plugin_name: str) -> PluginLifecycleState:
        """
        Get the current state of a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            PluginLifecycleState: The current state of the plugin
        """
        async with self._plugin_states_lock:
            return self._plugin_states.get(plugin_name, PluginLifecycleState.DISCOVERED)

    async def set_plugin_state(self, plugin_name: str, state: PluginLifecycleState) -> None:
        """
        Set the state of a plugin.

        Args:
            plugin_name: The name of the plugin
            state: The new state to set
        """
        async with self._plugin_states_lock:
            old_state = self._plugin_states.get(plugin_name, PluginLifecycleState.DISCOVERED)
            self._plugin_states[plugin_name] = state
        if self._logger:
            self._logger.debug(f"Plugin '{plugin_name}' state changed: {old_state.name} -> {state.name}")

    async def wait_for_ui_ready(self, plugin_name: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for the UI to be ready for a plugin.

        Args:
            plugin_name: The name of the plugin
            timeout: Optional timeout in seconds

        Returns:
            bool: True if the UI is ready, False if timed out
        """
        async with self._ui_integrations_lock:
            if plugin_name not in self._ui_ready_events:
                self._ui_ready_events[plugin_name] = asyncio.Event()
            event = self._ui_ready_events[plugin_name]

        if timeout is None:
            await event.wait()
            return True
        else:
            try:
                await asyncio.wait_for(event.wait(), timeout)
                return True
            except asyncio.TimeoutError:
                return False

    async def signal_ui_ready(self, plugin_name: str) -> None:
        """
        Signal that the UI is ready for a plugin.

        Args:
            plugin_name: The name of the plugin
        """
        async with self._ui_integrations_lock:
            if plugin_name not in self._ui_ready_events:
                self._ui_ready_events[plugin_name] = asyncio.Event()
            self._ui_ready_events[plugin_name].set()

    async def register_ui_integration(self, plugin_name: str, ui_integration: UIIntegration,
                                      main_window: Optional[Any] = None) -> None:
        """
        Register a UI integration for a plugin.

        Args:
            plugin_name: The name of the plugin
            ui_integration: The UI integration instance
            main_window: Optional main window reference
        """
        async with self._ui_integrations_lock:
            if plugin_name in self._ui_integrations:
                self.log(f"UI integration already registered for plugin '{plugin_name}'", 'debug')
                return
            self._ui_integrations[plugin_name] = ui_integration
            if main_window:
                self._main_window_ref = weakref.ref(main_window)

    async def get_ui_integration(self, plugin_name: str) -> Optional[UIIntegration]:
        """
        Get the UI integration for a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            Optional[UIIntegration]: The UI integration instance if found
        """
        async with self._ui_integrations_lock:
            return self._ui_integrations.get(plugin_name)

    async def cleanup_ui(self, plugin_name: str) -> bool:
        """
        Clean up UI components for a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            bool: True if cleanup was successful
        """
        if self._thread_manager and not self._thread_manager.is_main_thread():
            return await self._thread_manager.run_on_main_thread(self.cleanup_ui, plugin_name)

        try:
            if self._plugin_manager:
                async with getattr(self._plugin_manager, '_plugins_lock', asyncio.Lock()):
                    plugin_info = getattr(self._plugin_manager, '_plugins', {}).get(plugin_name)
                    if plugin_info and plugin_info.instance:
                        if hasattr(plugin_info.instance, '_ui_registry'):
                            await plugin_info.instance._ui_registry.cleanup()

            async with self._ui_integrations_lock:
                ui_integration = self._ui_integrations.get(plugin_name)
                if ui_integration:
                    try:
                        try:
                            await ui_integration.remove_page(plugin_name, plugin_name)
                        except Exception as e:
                            self.log(f"Error removing page for plugin '{plugin_name}': {str(e)}", 'error')
                        await ui_integration.cleanup_plugin(plugin_name)
                        del self._ui_integrations[plugin_name]
                        self.log(f"Cleaned up UI integration for plugin '{plugin_name}'", 'debug')
                    except Exception as e:
                        self.log(f"Error during UI cleanup for plugin '{plugin_name}': {str(e)}", 'error')

            async with self._ui_integrations_lock:
                if plugin_name in self._ui_ready_events:
                    self._ui_ready_events[plugin_name].clear()

            async with self._ui_lock:
                if plugin_name in self._ui_setup_plugins:
                    self._ui_setup_plugins.remove(plugin_name)

            return True
        except Exception as e:
            self.log(f"Error in cleanup_ui for plugin '{plugin_name}': {str(e)}", 'error')
            return False

    async def execute_hook(self, hook: PluginLifecycleHook, plugin_name: str,
                           manifest: PluginManifest, plugin_instance: Optional[Any] = None,
                           context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a lifecycle hook for a plugin.

        Args:
            hook: The lifecycle hook to execute
            plugin_name: The name of the plugin
            manifest: The plugin manifest
            plugin_instance: Optional plugin instance
            context: Optional context dictionary

        Returns:
            Any: The result of the hook execution

        Raises:
            LifecycleHookError: If the hook execution fails
        """
        context = context or {}
        if hook not in manifest.lifecycle_hooks:
            self.log(f'No {hook.value} hook defined for plugin {plugin_name}', 'debug')
            return None

        hook_path = manifest.lifecycle_hooks[hook]
        hook_key = f'{plugin_name}:{hook.value}'

        async with self._hooks_lock:
            if hook_key not in self._active_hooks:
                self._active_hooks[hook_key] = set()
            if hook_path in self._active_hooks[hook_key]:
                self.log(f'Recursive hook detected: {hook.value} for plugin {plugin_name}', 'warning')
                return None
            self._active_hooks[hook_key].add(hook_path)

        try:
            ui_hooks = [PluginLifecycleHook.POST_ENABLE, PluginLifecycleHook.PRE_DISABLE]
            if hook in ui_hooks and self._thread_manager and not self._thread_manager.is_main_thread():
                return await self._thread_manager.run_on_main_thread(self.execute_hook, hook, plugin_name,
                                                                     manifest, plugin_instance, context)

            if plugin_instance is not None and '.' not in hook_path:
                if hasattr(plugin_instance, hook_path):
                    hook_method = getattr(plugin_instance, hook_path)
                    if callable(hook_method):
                        self.log(f'Executing {hook.value} hook method {hook_path} for plugin {plugin_name}', 'debug')
                        async with self._ui_integrations_lock:
                            if 'ui_integration' not in context and plugin_name in self._ui_integrations:
                                context['ui_integration'] = self._ui_integrations[plugin_name]

                        if asyncio.iscoroutinefunction(hook_method):
                            return await hook_method(context=context)
                        else:
                            return hook_method(context=context)
                    else:
                        raise LifecycleHookError(hook, plugin_name, f'Hook {hook_path} is not callable')
                else:
                    raise LifecycleHookError(hook, plugin_name, f'Hook method {hook_path} not found on plugin instance')

            module_name, function_name = hook_path.rsplit('.', 1)
            try:
                try:
                    module = importlib.import_module(f'{plugin_name}.{module_name}')
                except ImportError:
                    module = importlib.import_module(module_name)

                hook_function = getattr(module, function_name)
                if not callable(hook_function):
                    raise LifecycleHookError(hook, plugin_name,
                                             f'Hook {function_name} in module {module_name} is not callable')

                self.log(f'Executing {hook.value} hook function {hook_path} for plugin {plugin_name}', 'debug')

                if plugin_instance is not None:
                    context['plugin_instance'] = plugin_instance

                async with self._ui_integrations_lock:
                    if 'ui_integration' not in context and plugin_name in self._ui_integrations:
                        context['ui_integration'] = self._ui_integrations[plugin_name]

                if asyncio.iscoroutinefunction(hook_function):
                    return await hook_function(context=context)
                else:
                    return hook_function(context=context)

            except ImportError as e:
                raise LifecycleHookError(hook, plugin_name,
                                         f'Failed to import module {module_name}: {str(e)}') from e
            except AttributeError as e:
                raise LifecycleHookError(hook, plugin_name,
                                         f'Hook function {function_name} not found in module {module_name}: {str(e)}') from e

        except LifecycleHookError:
            raise
        except Exception as e:
            raise LifecycleHookError(hook, plugin_name, f'Unexpected error: {str(e)}') from e
        finally:
            async with self._hooks_lock:
                if hook_key in self._active_hooks and hook_path in self._active_hooks[hook_key]:
                    self._active_hooks[hook_key].remove(hook_path)
                    if not self._active_hooks[hook_key]:
                        del self._active_hooks[hook_key]

    async def find_plugin_hooks(self, plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
        """
        Find hooks defined in a plugin instance.

        Args:
            plugin_instance: The plugin instance

        Returns:
            Dict[PluginLifecycleHook, str]: Dictionary mapping hooks to method names
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


# Global instance and helper functions
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """
    Get the global lifecycle manager instance.
    Creates a new instance if one doesn't exist.

    Returns:
        AsyncLifecycleManager: The global lifecycle manager instance
    """
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager(None)
    return _lifecycle_manager


def set_thread_manager(thread_manager: Any) -> None:
    """Set the thread manager for the global lifecycle manager."""
    get_lifecycle_manager().set_thread_manager(thread_manager)


def set_plugin_manager(plugin_manager: Any) -> None:
    """Set the plugin manager for the global lifecycle manager."""
    get_lifecycle_manager().set_plugin_manager(plugin_manager)


def set_logger(logger: Any) -> None:
    """Set the logger for the global lifecycle manager."""
    get_lifecycle_manager().set_logger(logger)


async def execute_hook(hook: PluginLifecycleHook, plugin_name: str,
                       manifest: PluginManifest, plugin_instance: Optional[Any] = None,
                       *, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
    """
    Execute a lifecycle hook for a plugin using the global lifecycle manager.

    Args:
        hook: The lifecycle hook to execute
        plugin_name: The name of the plugin
        manifest: The plugin manifest
        plugin_instance: Optional plugin instance
        context: Optional context dictionary
        **kwargs: Additional context parameters

    Returns:
        Any: The result of the hook execution
    """
    if context is None:
        context = kwargs
    else:
        context.update(kwargs)
    return await get_lifecycle_manager().execute_hook(
        hook=hook, plugin_name=plugin_name, manifest=manifest,
        plugin_instance=plugin_instance, context=context
    )


async def find_plugin_hooks(plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
    """Find hooks defined in a plugin instance using the global lifecycle manager."""
    return await get_lifecycle_manager().find_plugin_hooks(plugin_instance)


async def register_ui_integration(plugin_name: str, ui_integration: UIIntegration,
                                  main_window: Optional[Any] = None) -> None:
    """Register a UI integration for a plugin using the global lifecycle manager."""
    await get_lifecycle_manager().register_ui_integration(plugin_name, ui_integration, main_window)


async def get_ui_integration(plugin_name: str) -> Optional[UIIntegration]:
    """Get the UI integration for a plugin using the global lifecycle manager."""
    return await get_lifecycle_manager().get_ui_integration(plugin_name)


async def cleanup_ui(plugin_name: str) -> bool:
    """Clean up UI components for a plugin using the global lifecycle manager."""
    return await get_lifecycle_manager().cleanup_ui(plugin_name)


async def get_plugin_state(plugin_name: str) -> PluginLifecycleState:
    """Get the current state of a plugin using the global lifecycle manager."""
    return await get_lifecycle_manager().get_plugin_state(plugin_name)


async def set_plugin_state(plugin_name: str, state: PluginLifecycleState) -> None:
    """Set the state of a plugin using the global lifecycle manager."""
    await get_lifecycle_manager().set_plugin_state(plugin_name, state)


async def wait_for_ui_ready(plugin_name: str, timeout: Optional[float] = None) -> bool:
    """Wait for the UI to be ready for a plugin using the global lifecycle manager."""
    return await get_lifecycle_manager().wait_for_ui_ready(plugin_name, timeout)


async def signal_ui_ready(plugin_name: str) -> None:
    """Signal that the UI is ready for a plugin using the global lifecycle manager."""
    await get_lifecycle_manager().signal_ui_ready(plugin_name)