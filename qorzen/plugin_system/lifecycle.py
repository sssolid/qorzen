from __future__ import annotations

import abc
import importlib
import inspect
import threading
import weakref
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union, Type, Protocol, runtime_checkable, cast

from qorzen.plugin_system.manifest import PluginLifecycleHook, PluginManifest
from qorzen.ui.integration import UIIntegration


class PluginLifecycleState(Enum):
    """States a plugin can be in during its lifecycle."""
    DISCOVERED = auto()  # Plugin has been found but not loaded
    LOADING = auto()  # Plugin is in the process of loading
    INITIALIZING = auto()  # Plugin is initializing
    INITIALIZED = auto()  # Plugin has been initialized but UI not set up
    UI_READY = auto()  # Plugin UI components are set up
    ACTIVE = auto()  # Plugin is fully active
    DISABLING = auto()  # Plugin is in the process of being disabled
    INACTIVE = auto()  # Plugin is inactive
    FAILED = auto()  # Plugin failed to load or operate


@runtime_checkable
class PluginInterface(Protocol):
    """Interface that all plugins should implement."""
    name: str
    version: str
    description: str

    def initialize(self, event_bus: Any, logger_provider: Any, config_provider: Any,
                   file_manager: Any, thread_manager: Any, **kwargs: Any) -> None:
        """Initialize the plugin with required services."""
        ...

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """Called when the UI system is ready for plugin integration."""
        ...

    def shutdown(self) -> None:
        """Clean up resources when the plugin is being shut down."""
        ...


class LifecycleHookError(Exception):
    """Error raised when a lifecycle hook fails."""

    def __init__(self, hook: PluginLifecycleHook, plugin_name: str, message: str):
        self.hook = hook
        self.plugin_name = plugin_name
        self.message = message
        super().__init__(
            f'Error executing {hook.value} hook for plugin {plugin_name}: {message}'
        )


class LifecycleManager:
    """
    Manages the lifecycle of plugins.

    This class tracks plugin states, manages UI integration, and executes
    lifecycle hooks at appropriate times.
    """

    def __init__(self, logger_manager: Optional[Any] = None):
        """
        Initialize the lifecycle manager.

        Args:
            logger_manager: Optional logger manager for logging
        """
        self._logger_manager = logger_manager
        self._logger = None
        if logger_manager:
            self._logger = logger_manager.get_logger('lifecycle_manager')

        self._ui_integrations: Dict[str, UIIntegration] = {}
        self._main_window_ref: Optional[weakref.ReferenceType] = None
        self._active_hooks: Dict[str, set] = {}
        self._plugin_states: Dict[str, PluginLifecycleState] = {}
        self._plugin_states_lock = threading.RLock()
        self._ui_integrations_lock = threading.RLock()
        self._hooks_lock = threading.RLock()
        self._ui_ready_events: Dict[str, threading.Event] = {}
        self._thread_manager: Optional[Any] = None
        self._plugin_manager: Optional[Any] = None
        self._ui_setup_plugins: set = set()
        self._ui_lock = threading.RLock()

    def set_thread_manager(self, thread_manager: Any) -> None:
        """
        Set the thread manager.

        Args:
            thread_manager: The thread manager to use
        """
        self._thread_manager = thread_manager

    def set_plugin_manager(self, plugin_manager: Any) -> None:
        """
        Set the plugin manager.

        Args:
            plugin_manager: The plugin manager to use
        """
        self._plugin_manager = plugin_manager

    def set_logger(self, logger: Any) -> None:
        """
        Set the logger.

        Args:
            logger: The logger to use
        """
        self._logger = logger

    def log(self, message: str, level: str = 'info') -> None:
        """
        Log a message.

        Args:
            message: The message to log
            level: The log level (default: 'info')
        """
        if self._logger:
            log_method = getattr(self._logger, level, None)
            if callable(log_method):
                log_method(message)

    def get_plugin_state(self, plugin_name: str) -> PluginLifecycleState:
        """
        Get the state of a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            The current state of the plugin
        """
        with self._plugin_states_lock:
            return self._plugin_states.get(plugin_name, PluginLifecycleState.DISCOVERED)

    def set_plugin_state(self, plugin_name: str, state: PluginLifecycleState) -> None:
        """
        Set the state of a plugin.

        Args:
            plugin_name: The name of the plugin
            state: The new state for the plugin
        """
        with self._plugin_states_lock:
            old_state = self._plugin_states.get(plugin_name, PluginLifecycleState.DISCOVERED)
            self._plugin_states[plugin_name] = state

        if self._logger:
            self._logger.debug(f"Plugin '{plugin_name}' state changed: {old_state.name} -> {state.name}")

    def wait_for_ui_ready(self, plugin_name: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for a plugin's UI to be ready.

        Args:
            plugin_name: The name of the plugin
            timeout: Optional timeout in seconds (None = wait forever)

        Returns:
            True if the UI is ready, False if timed out
        """
        with self._ui_integrations_lock:
            if plugin_name not in self._ui_ready_events:
                self._ui_ready_events[plugin_name] = threading.Event()
            event = self._ui_ready_events[plugin_name]

        return event.wait(timeout)

    def signal_ui_ready(self, plugin_name: str) -> None:
        """
        Signal that a plugin's UI is ready.

        Args:
            plugin_name: The name of the plugin
        """
        with self._ui_integrations_lock:
            if plugin_name not in self._ui_ready_events:
                self._ui_ready_events[plugin_name] = threading.Event()
            self._ui_ready_events[plugin_name].set()

    def register_ui_integration(self, plugin_name: str, ui_integration: UIIntegration,
                                main_window: Optional[Any] = None) -> None:
        """
        Register UI integration for a plugin.

        Args:
            plugin_name: The name of the plugin
            ui_integration: The UI integration to register
            main_window: Optional main window reference
        """
        with self._ui_integrations_lock:
            if plugin_name in self._ui_integrations:
                self.log(f"UI integration already registered for plugin '{plugin_name}'", 'debug')
                return

            self._ui_integrations[plugin_name] = ui_integration
            if main_window:
                self._main_window_ref = weakref.ref(main_window)

    def get_ui_integration(self, plugin_name: str) -> Optional[UIIntegration]:
        """
        Get the UI integration for a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            The UI integration if registered, None otherwise
        """
        with self._ui_integrations_lock:
            return self._ui_integrations.get(plugin_name)

    def cleanup_ui(self, plugin_name: str) -> bool:
        """
        Clean up UI components for a plugin.

        This must be called on the main thread.

        Args:
            plugin_name: The name of the plugin

        Returns:
            True if successful, False otherwise
        """
        # Make sure we're on the main thread
        if self._thread_manager and (not self._thread_manager.is_main_thread()):
            return self._thread_manager.execute_on_main_thread_sync(self.cleanup_ui, plugin_name)

        try:
            # Clean up UI registry if present
            if self._plugin_manager:
                with getattr(self._plugin_manager, '_plugins_lock', threading.RLock()):
                    plugin_info = getattr(self._plugin_manager, '_plugins', {}).get(plugin_name)
                    if plugin_info and plugin_info.instance:
                        if hasattr(plugin_info.instance, '_ui_registry'):
                            plugin_info.instance._ui_registry.cleanup()

            # Clean up UI integration
            with self._ui_integrations_lock:
                ui_integration = self._ui_integrations.get(plugin_name)
                if ui_integration:
                    try:
                        # Make sure we explicitly remove the page by name
                        try:
                            ui_integration.remove_page(plugin_name, plugin_name)
                        except Exception as e:
                            self.log(f"Error removing page for plugin '{plugin_name}': {str(e)}", 'error')

                        ui_integration.cleanup_plugin(plugin_name)
                        del self._ui_integrations[plugin_name]
                        self.log(f"Cleaned up UI integration for plugin '{plugin_name}'", 'debug')
                    except Exception as e:
                        self.log(f"Error during UI cleanup for plugin '{plugin_name}': {str(e)}", 'error')

            # Clear UI ready event
            with self._ui_integrations_lock:
                if plugin_name in self._ui_ready_events:
                    self._ui_ready_events[plugin_name].clear()

            # Remove from UI setup plugins
            with self._ui_lock:
                if plugin_name in self._ui_setup_plugins:
                    self._ui_setup_plugins.remove(plugin_name)

            return True

        except Exception as e:
            self.log(f"Error in cleanup_ui for plugin '{plugin_name}': {str(e)}", 'error')
            return False

    def execute_hook(self, hook: PluginLifecycleHook, plugin_name: str,
                     manifest: PluginManifest, plugin_instance: Optional[Any] = None,
                     context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a lifecycle hook for a plugin.

        Args:
            hook: The lifecycle hook to execute
            plugin_name: The name of the plugin
            manifest: The plugin's manifest
            plugin_instance: Optional plugin instance
            context: Optional context to pass to the hook

        Returns:
            The result of the hook execution
        """
        context = context or {}

        # Check if the hook is defined
        if hook not in manifest.lifecycle_hooks:
            self.log(f'No {hook.value} hook defined for plugin {plugin_name}', 'debug')
            return None

        hook_path = manifest.lifecycle_hooks[hook]
        hook_key = f'{plugin_name}:{hook.value}'

        # Check for recursive hooks
        with self._hooks_lock:
            if hook_key not in self._active_hooks:
                self._active_hooks[hook_key] = set()

            if hook_path in self._active_hooks[hook_key]:
                self.log(f'Recursive hook detected: {hook.value} for plugin {plugin_name}', 'warning')
                return None

            self._active_hooks[hook_key].add(hook_path)

        try:
            # Handle UI hooks that must run on the main thread
            ui_hooks = [PluginLifecycleHook.POST_ENABLE, PluginLifecycleHook.PRE_DISABLE]
            if hook in ui_hooks and self._thread_manager and (not self._thread_manager.is_main_thread()):
                return self._thread_manager.execute_on_main_thread_sync(
                    self.execute_hook, hook, plugin_name, manifest, plugin_instance, context
                )

            # Handle method hooks on the plugin instance
            if plugin_instance is not None and '.' not in hook_path:
                if hasattr(plugin_instance, hook_path):
                    hook_method = getattr(plugin_instance, hook_path)
                    if callable(hook_method):
                        self.log(
                            f'Executing {hook.value} hook method {hook_path} for plugin {plugin_name}',
                            'debug'
                        )

                        with self._ui_integrations_lock:
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

            # Handle module hooks
            module_name, function_name = hook_path.rsplit('.', 1)
            try:
                try:
                    module = importlib.import_module(f'{plugin_name}.{module_name}')
                except ImportError:
                    module = importlib.import_module(module_name)

                hook_function = getattr(module, function_name)
                if not callable(hook_function):
                    raise LifecycleHookError(
                        hook, plugin_name,
                        f'Hook {function_name} in module {module_name} is not callable'
                    )

                self.log(
                    f'Executing {hook.value} hook function {hook_path} for plugin {plugin_name}',
                    'debug'
                )

                if plugin_instance is not None:
                    context['plugin_instance'] = plugin_instance

                with self._ui_integrations_lock:
                    if 'ui_integration' not in context and plugin_name in self._ui_integrations:
                        context['ui_integration'] = self._ui_integrations[plugin_name]

                return hook_function(context=context)

            except ImportError as e:
                raise LifecycleHookError(
                    hook, plugin_name, f'Failed to import module {module_name}: {str(e)}'
                ) from e
            except AttributeError as e:
                raise LifecycleHookError(
                    hook, plugin_name,
                    f'Hook function {function_name} not found in module {module_name}: {str(e)}'
                ) from e

        except LifecycleHookError:
            raise
        except Exception as e:
            raise LifecycleHookError(
                hook, plugin_name, f'Unexpected error: {str(e)}'
            ) from e
        finally:
            # Clean up active hooks
            with self._hooks_lock:
                if hook_key in self._active_hooks and hook_path in self._active_hooks[hook_key]:
                    self._active_hooks[hook_key].remove(hook_path)
                    if not self._active_hooks[hook_key]:
                        del self._active_hooks[hook_key]

    def find_plugin_hooks(self, plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
        """
        Find lifecycle hooks implemented by a plugin.

        Args:
            plugin_instance: The plugin instance to inspect

        Returns:
            Dictionary mapping lifecycle hooks to method names
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


# Global lifecycle manager instance
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """
    Get the global lifecycle manager instance.

    Returns:
        The lifecycle manager instance
    """
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager(None)
    return _lifecycle_manager


def set_thread_manager(thread_manager: Any) -> None:
    """
    Set the thread manager for the lifecycle manager.

    Args:
        thread_manager: The thread manager to use
    """
    get_lifecycle_manager().set_thread_manager(thread_manager)


def set_plugin_manager(plugin_manager: Any) -> None:
    """
    Set the plugin manager for the lifecycle manager.

    Args:
        plugin_manager: The plugin manager to use
    """
    get_lifecycle_manager().set_plugin_manager(plugin_manager)


def set_logger(logger: Any) -> None:
    """
    Set the logger for the lifecycle manager.

    Args:
        logger: The logger to use
    """
    get_lifecycle_manager().set_logger(logger)


def execute_hook(hook: PluginLifecycleHook, plugin_name: str, manifest: PluginManifest,
                 plugin_instance: Optional[Any] = None, *, context: Optional[Dict[str, Any]] = None,
                 **kwargs: Any) -> Any:
    """
    Execute a lifecycle hook for a plugin.

    Args:
        hook: The lifecycle hook to execute
        plugin_name: The name of the plugin
        manifest: The plugin's manifest
        plugin_instance: Optional plugin instance
        context: Optional context dictionary
        **kwargs: Additional context key-value pairs

    Returns:
        The result of the hook execution
    """
    if context is None:
        context = kwargs
    else:
        context.update(kwargs)

    return get_lifecycle_manager().execute_hook(
        hook=hook, plugin_name=plugin_name, manifest=manifest,
        plugin_instance=plugin_instance, context=context
    )


def find_plugin_hooks(plugin_instance: Any) -> Dict[PluginLifecycleHook, str]:
    """
    Find lifecycle hooks implemented by a plugin.

    Args:
        plugin_instance: The plugin instance to inspect

    Returns:
        Dictionary mapping lifecycle hooks to method names
    """
    return get_lifecycle_manager().find_plugin_hooks(plugin_instance)


def register_ui_integration(plugin_name: str, ui_integration: UIIntegration,
                            main_window: Optional[Any] = None) -> None:
    """
    Register UI integration for a plugin.

    Args:
        plugin_name: The name of the plugin
        ui_integration: The UI integration to register
        main_window: Optional main window reference
    """
    get_lifecycle_manager().register_ui_integration(plugin_name, ui_integration, main_window)


def get_ui_integration(plugin_name: str) -> Optional[UIIntegration]:
    """
    Get the UI integration for a plugin.

    Args:
        plugin_name: The name of the plugin

    Returns:
        The UI integration if registered, None otherwise
    """
    return get_lifecycle_manager().get_ui_integration(plugin_name)


def cleanup_ui(plugin_name: str) -> bool:
    """
    Clean up UI components for a plugin.

    Args:
        plugin_name: The name of the plugin

    Returns:
        True if successful, False otherwise
    """
    return get_lifecycle_manager().cleanup_ui(plugin_name)


def get_plugin_state(plugin_name: str) -> PluginLifecycleState:
    """
    Get the state of a plugin.

    Args:
        plugin_name: The name of the plugin

    Returns:
        The current state of the plugin
    """
    return get_lifecycle_manager().get_plugin_state(plugin_name)


def set_plugin_state(plugin_name: str, state: PluginLifecycleState) -> None:
    """
    Set the state of a plugin.

    Args:
        plugin_name: The name of the plugin
        state: The new state for the plugin
    """
    get_lifecycle_manager().set_plugin_state(plugin_name, state)


def wait_for_ui_ready(plugin_name: str, timeout: Optional[float] = None) -> bool:
    """
    Wait for a plugin's UI to be ready.

    Args:
        plugin_name: The name of the plugin
        timeout: Optional timeout in seconds (None = wait forever)

    Returns:
        True if the UI is ready, False if timed out
    """
    return get_lifecycle_manager().wait_for_ui_ready(plugin_name, timeout)


def signal_ui_ready(plugin_name: str) -> None:
    """
    Signal that a plugin's UI is ready.

    Args:
        plugin_name: The name of the plugin
    """
    get_lifecycle_manager().signal_ui_ready(plugin_name)