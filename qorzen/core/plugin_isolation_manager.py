from __future__ import annotations
import asyncio
import importlib.util
import inspect
import os
import pathlib
import signal
import sys
import tempfile
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import PluginIsolationError, ManagerInitializationError, ManagerShutdownError


class PluginIsolationLevel(str, Enum):
    """Isolation levels for plugins."""
    NONE = "none"  # No isolation, runs in the same process/thread
    THREAD = "thread"  # Thread isolation (default)
    PROCESS = "process"  # Process isolation for more security


@dataclass
class PluginResourceLimits:
    """Resource limits for a plugin."""
    max_memory_mb: int = 256
    max_cpu_percent: float = 50.0
    max_file_handles: int = 100
    max_network_connections: int = 20
    max_execution_time_seconds: int = 300


@dataclass
class IsolatedPluginInfo:
    """Information about an isolated plugin."""
    plugin_id: str
    name: str
    isolation_level: PluginIsolationLevel
    path: str
    loaded_at: float = field(default_factory=time.time)
    healthy: bool = True
    error: Optional[str] = None
    resource_limits: PluginResourceLimits = field(default_factory=PluginResourceLimits)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginIsolator(ABC):
    """Base class for plugin isolators."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the isolator."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the isolator."""
        pass

    @abstractmethod
    async def run_plugin_method(
            self,
            plugin_id: str,
            method_name: str,
            args: Optional[List[Any]] = None,
            kwargs: Optional[Dict[str, Any]] = None,
            timeout: Optional[float] = None
    ) -> Any:
        """Run a plugin method in isolation.

        Args:
            plugin_id: ID of the plugin
            method_name: Name of the method to run
            args: Positional arguments to pass
            kwargs: Keyword arguments to pass
            timeout: Optional timeout in seconds

        Returns:
            Result of the method call

        Raises:
            PluginIsolationError: If the method call fails
        """
        pass

    @abstractmethod
    async def load_plugin(self, plugin_id: str, plugin_path: str) -> bool:
        """Load a plugin in isolation.

        Args:
            plugin_id: ID to assign to the plugin
            plugin_path: Path to the plugin file or directory

        Returns:
            True if the plugin was loaded successfully

        Raises:
            PluginIsolationError: If loading fails
        """
        pass

    @abstractmethod
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin from isolation.

        Args:
            plugin_id: ID of the plugin to unload

        Returns:
            True if the plugin was unloaded successfully

        Raises:
            PluginIsolationError: If unloading fails
        """
        pass


class ThreadIsolator(PluginIsolator):
    """Thread-based plugin isolator.

    Provides thread-level isolation for plugins. Each plugin method
    runs in a separate thread with timeout support.
    """

    def __init__(self, concurrency_manager: Any, logger: Any) -> None:
        """Initialize the thread isolator.

        Args:
            concurrency_manager: Manager for thread operations
            logger: Logger instance
        """
        self._concurrency_manager = concurrency_manager
        self._logger = logger
        self._plugins: Dict[str, Any] = {}
        self._plugin_info: Dict[str, IsolatedPluginInfo] = {}
        self._method_locks: Dict[str, asyncio.Lock] = {}

    async def initialize(self) -> None:
        """Initialize the thread isolator."""
        self._logger.debug("Initializing thread isolator")
        pass

    async def shutdown(self) -> None:
        """Shutdown the thread isolator."""
        self._logger.debug("Shutting down thread isolator")

        # Unload all plugins
        for plugin_id in list(self._plugins.keys()):
            try:
                await self.unload_plugin(plugin_id)
            except Exception as e:
                self._logger.warning(f"Error unloading plugin {plugin_id} during shutdown: {e}")

        self._plugins.clear()
        self._plugin_info.clear()
        self._method_locks.clear()

    async def run_plugin_method(
            self,
            plugin_id: str,
            method_name: str,
            args: Optional[List[Any]] = None,
            kwargs: Optional[Dict[str, Any]] = None,
            timeout: Optional[float] = None
    ) -> Any:
        """Run a plugin method in a thread.

        Args:
            plugin_id: ID of the plugin
            method_name: Name of the method to run
            args: Positional arguments to pass
            kwargs: Keyword arguments to pass
            timeout: Optional timeout in seconds

        Returns:
            Result of the method call

        Raises:
            PluginIsolationError: If the method call fails
        """
        if plugin_id not in self._plugins:
            raise PluginIsolationError(f"Plugin {plugin_id} not loaded")

        plugin = self._plugins[plugin_id]
        method = getattr(plugin, method_name, None)

        if not method:
            raise PluginIsolationError(f"Method {method_name} not found in plugin {plugin_id}")

        # Get or create lock for this method
        method_key = f"{plugin_id}:{method_name}"
        if method_key not in self._method_locks:
            self._method_locks[method_key] = asyncio.Lock()

        # Use the lock to prevent concurrent calls to the same method
        async with self._method_locks[method_key]:
            try:
                # Run in thread pool with timeout
                if timeout:
                    return await asyncio.wait_for(
                        self._concurrency_manager.run_in_thread(
                            method,
                            *(args or []),
                            **(kwargs or {})
                        ),
                        timeout=timeout
                    )
                else:
                    return await self._concurrency_manager.run_in_thread(
                        method,
                        *(args or []),
                        **(kwargs or {})
                    )
            except asyncio.TimeoutError:
                raise PluginIsolationError(
                    f"Method {method_name} in plugin {plugin_id} timed out after {timeout} seconds"
                )
            except Exception as e:
                self._logger.error(
                    f"Error calling method {method_name} in plugin {plugin_id}: {e}",
                    exc_info=True
                )
                raise PluginIsolationError(
                    f"Error calling method {method_name} in plugin {plugin_id}: {str(e)}"
                ) from e

    async def load_plugin(self, plugin_id: str, plugin_path: str) -> bool:
        """Load a plugin in thread isolation.

        Args:
            plugin_id: ID to assign to the plugin
            plugin_path: Path to the plugin file or directory

        Returns:
            True if the plugin was loaded successfully

        Raises:
            PluginIsolationError: If loading fails
        """
        try:
            self._logger.debug(f"Loading plugin {plugin_id} from {plugin_path}")

            # Check if already loaded
            if plugin_id in self._plugins:
                self._logger.warning(f"Plugin {plugin_id} is already loaded, unloading first")
                await self.unload_plugin(plugin_id)

            # Import the plugin module
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_id}", plugin_path)
            if not spec or not spec.loader:
                raise PluginIsolationError(f"Failed to create module spec for {plugin_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, "name") and hasattr(obj, "version"):
                    plugin_class = obj
                    break

            if not plugin_class:
                raise PluginIsolationError(f"No plugin class found in {plugin_path}")

            # Instantiate the plugin
            plugin = plugin_class()
            self._plugins[plugin_id] = plugin

            # Store plugin info
            self._plugin_info[plugin_id] = IsolatedPluginInfo(
                plugin_id=plugin_id,
                name=getattr(plugin, "name", plugin_id),
                isolation_level=PluginIsolationLevel.THREAD,
                path=plugin_path,
                loaded_at=time.time(),
                healthy=True,
                metadata={
                    "version": getattr(plugin, "version", "unknown"),
                    "description": getattr(plugin, "description", ""),
                    "author": getattr(plugin, "author", "unknown")
                }
            )

            self._logger.info(f"Successfully loaded plugin {plugin_id} in thread isolation")
            return True
        except Exception as e:
            self._logger.error(f"Error loading plugin {plugin_id}: {e}", exc_info=True)

            # Update plugin info if it exists
            if plugin_id in self._plugin_info:
                self._plugin_info[plugin_id].healthy = False
                self._plugin_info[plugin_id].error = str(e)

            # Clean up if needed
            if plugin_id in self._plugins:
                del self._plugins[plugin_id]

            raise PluginIsolationError(f"Failed to load plugin {plugin_id}: {str(e)}") from e

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin from thread isolation.

        Args:
            plugin_id: ID of the plugin to unload

        Returns:
            True if the plugin was unloaded successfully

        Raises:
            PluginIsolationError: If unloading fails
        """
        if plugin_id not in self._plugins:
            self._logger.warning(f"Plugin {plugin_id} is not loaded")
            return False

        try:
            self._logger.debug(f"Unloading plugin {plugin_id}")

            plugin = self._plugins[plugin_id]

            # Call shutdown method if it exists
            if hasattr(plugin, "shutdown"):
                try:
                    # Run shutdown in thread with timeout
                    await asyncio.wait_for(
                        self._concurrency_manager.run_in_thread(plugin.shutdown),
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    self._logger.warning(f"Shutdown of plugin {plugin_id} timed out")
                except Exception as e:
                    self._logger.warning(f"Error during shutdown of plugin {plugin_id}: {e}")

            # Remove from dictionaries
            del self._plugins[plugin_id]
            if plugin_id in self._plugin_info:
                del self._plugin_info[plugin_id]

            # Remove method locks
            for key in list(self._method_locks.keys()):
                if key.startswith(f"{plugin_id}:"):
                    del self._method_locks[key]

            self._logger.info(f"Successfully unloaded plugin {plugin_id}")
            return True
        except Exception as e:
            self._logger.error(f"Error unloading plugin {plugin_id}: {e}", exc_info=True)
            raise PluginIsolationError(f"Failed to unload plugin {plugin_id}: {str(e)}") from e


class PluginIsolationManager(QorzenManager):
    """Manager for handling plugin isolation.

    Provides a unified interface for loading, unloading, and interacting
    with plugins using different isolation strategies.
    """

    def __init__(
            self,
            concurrency_manager: Any,
            logger_manager: Any,
            config_manager: Any,
            name: str = "plugin_isolation_manager"
    ) -> None:
        """Initialize the isolation manager.

        Args:
            concurrency_manager: Manager for concurrency operations
            logger_manager: Manager for logging
            config_manager: Manager for configuration
            name: Name of this manager
        """
        super().__init__(name=name)
        self._concurrency_manager = concurrency_manager
        self._logger = logger_manager.get_logger("plugin_isolation")
        self._config_manager = config_manager

        self._isolators: Dict[PluginIsolationLevel, PluginIsolator] = {}
        self._plugin_isolations: Dict[str, PluginIsolationLevel] = {}
        self._default_isolation_level = PluginIsolationLevel.THREAD

    async def initialize(self) -> None:
        """Initialize the isolation manager.

        Creates and initializes isolators for different isolation levels.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            self._logger.info("Initializing plugin isolation manager")

            # Get configuration
            plugin_config = await self._config_manager.get("plugins", {})
            isolation_config = plugin_config.get("isolation", {})

            # Set default isolation level
            default_level = isolation_config.get("default_level", "thread")
            try:
                self._default_isolation_level = PluginIsolationLevel(default_level)
            except ValueError:
                self._logger.warning(
                    f"Invalid default isolation level '{default_level}', "
                    f"using {self._default_isolation_level}"
                )

            # Create isolators
            self._isolators[PluginIsolationLevel.THREAD] = ThreadIsolator(
                self._concurrency_manager,
                self._logger
            )

            # TODO: Implement process isolator if needed
            # if PluginIsolationLevel.PROCESS in self._isolators:
            #     self._isolators[PluginIsolationLevel.PROCESS] = ProcessIsolator(...)

            # Initialize isolators
            for level, isolator in self._isolators.items():
                self._logger.debug(f"Initializing {level} isolator")
                await isolator.initialize()

            self._initialized = True
            self._healthy = True
            self._logger.info("Plugin isolation manager initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize plugin isolation manager: {e}", exc_info=True)
            raise ManagerInitializationError(
                f"Failed to initialize {self.name}: {str(e)}",
                manager_name=self.name
            ) from e

    async def shutdown(self) -> None:
        """Shutdown the isolation manager.

        Shuts down all isolators and unloads all plugins.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info("Shutting down plugin isolation manager")

            # Shutdown isolators
            for level, isolator in self._isolators.items():
                try:
                    self._logger.debug(f"Shutting down {level} isolator")
                    await isolator.shutdown()
                except Exception as e:
                    self._logger.error(f"Error shutting down {level} isolator: {e}")

            self._isolators.clear()
            self._plugin_isolations.clear()
            self._initialized = False
            self._healthy = False
            self._logger.info("Plugin isolation manager shut down successfully")
        except Exception as e:
            self._logger.error(f"Failed to shut down plugin isolation manager: {e}", exc_info=True)
            raise ManagerShutdownError(
                f"Failed to shut down {self.name}: {str(e)}",
                manager_name=self.name
            ) from e

    async def load_plugin(
            self,
            plugin_id: str,
            plugin_path: str,
            isolation_level: Optional[PluginIsolationLevel] = None
    ) -> bool:
        """Load a plugin with the specified isolation level.

        Args:
            plugin_id: ID to assign to the plugin
            plugin_path: Path to the plugin file or directory
            isolation_level: Isolation level to use, or None for default

        Returns:
            True if the plugin was loaded successfully

        Raises:
            PluginIsolationError: If loading fails
        """
        if not self._initialized:
            raise PluginIsolationError("Plugin isolation manager not initialized")

        # Use default isolation level if not specified
        if isolation_level is None:
            isolation_level = self._default_isolation_level

        # Check if the specified isolation level is supported
        if isolation_level not in self._isolators:
            raise PluginIsolationError(f"Isolation level {isolation_level} not supported")

        # Unload the plugin if it's already loaded
        if plugin_id in self._plugin_isolations:
            existing_level = self._plugin_isolations[plugin_id]
            if existing_level != isolation_level:
                self._logger.debug(
                    f"Plugin {plugin_id} is already loaded with {existing_level} isolation, "
                    f"unloading before reloading with {isolation_level}"
                )
                await self.unload_plugin(plugin_id)
            else:
                self._logger.debug(f"Plugin {plugin_id} is already loaded, unloading first")
                await self.unload_plugin(plugin_id)

        # Get the appropriate isolator
        isolator = self._isolators[isolation_level]

        # Load the plugin
        try:
            success = await isolator.load_plugin(plugin_id, plugin_path)

            if success:
                self._plugin_isolations[plugin_id] = isolation_level
                self._logger.info(
                    f"Successfully loaded plugin {plugin_id} with {isolation_level} isolation"
                )

            return success
        except Exception as e:
            self._logger.error(f"Failed to load plugin {plugin_id}: {e}", exc_info=True)
            raise PluginIsolationError(f"Failed to load plugin {plugin_id}: {str(e)}") from e

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_id: ID of the plugin to unload

        Returns:
            True if the plugin was unloaded successfully

        Raises:
            PluginIsolationError: If unloading fails
        """
        if not self._initialized:
            raise PluginIsolationError("Plugin isolation manager not initialized")

        if plugin_id not in self._plugin_isolations:
            self._logger.warning(f"Plugin {plugin_id} is not loaded")
            return False

        isolation_level = self._plugin_isolations[plugin_id]
        isolator = self._isolators[isolation_level]

        try:
            success = await isolator.unload_plugin(plugin_id)

            if success:
                del self._plugin_isolations[plugin_id]
                self._logger.info(f"Successfully unloaded plugin {plugin_id}")

            return success
        except Exception as e:
            self._logger.error(f"Failed to unload plugin {plugin_id}: {e}", exc_info=True)
            raise PluginIsolationError(f"Failed to unload plugin {plugin_id}: {str(e)}") from e

    async def run_plugin_method(
            self,
            plugin_id: str,
            method_name: str,
            args: Optional[List[Any]] = None,
            kwargs: Optional[Dict[str, Any]] = None,
            timeout: Optional[float] = None
    ) -> Any:
        """Run a plugin method with the appropriate isolation.

        Args:
            plugin_id: ID of the plugin
            method_name: Name of the method to run
            args: Positional arguments to pass
            kwargs: Keyword arguments to pass
            timeout: Optional timeout in seconds

        Returns:
            Result of the method call

        Raises:
            PluginIsolationError: If the method call fails
        """
        if not self._initialized:
            raise PluginIsolationError("Plugin isolation manager not initialized")

        if plugin_id not in self._plugin_isolations:
            raise PluginIsolationError(f"Plugin {plugin_id} not loaded")

        isolation_level = self._plugin_isolations[plugin_id]
        isolator = self._isolators[isolation_level]

        try:
            method_start = time.time()
            result = await isolator.run_plugin_method(
                plugin_id,
                method_name,
                args or [],
                kwargs or {},
                timeout
            )
            method_duration = time.time() - method_start

            if method_duration > 1.0:  # Log slow plugin calls
                self._logger.debug(
                    f"Plugin {plugin_id} method {method_name} took {method_duration:.2f} seconds"
                )

            return result
        except Exception as e:
            self._logger.error(
                f"Error running method {method_name} in plugin {plugin_id}: {e}",
                exc_info=True
            )
            raise PluginIsolationError(
                f"Error running method {method_name} in plugin {plugin_id}: {str(e)}"
            ) from e

    def get_plugin_isolation_level(self, plugin_id: str) -> Optional[PluginIsolationLevel]:
        """Get the isolation level of a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            The isolation level or None if the plugin is not loaded
        """
        return self._plugin_isolations.get(plugin_id)

    def is_plugin_loaded(self, plugin_id: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            plugin_id: ID of the plugin

        Returns:
            True if the plugin is loaded
        """
        return plugin_id in self._plugin_isolations

    def get_loaded_plugins(self) -> Dict[str, PluginIsolationLevel]:
        """Get all loaded plugins and their isolation levels.

        Returns:
            Dictionary mapping plugin IDs to isolation levels
        """
        return self._plugin_isolations.copy()

    def status(self) -> Dict[str, Any]:
        """Get the status of the isolation manager.

        Returns:
            Dictionary containing status information
        """
        status = super().status()

        if self._initialized:
            # Count plugins by isolation level
            isolation_counts = {level.value: 0 for level in PluginIsolationLevel}
            for level in self._plugin_isolations.values():
                isolation_counts[level.value] += 1

            status.update({
                "plugins": {
                    "total": len(self._plugin_isolations),
                    "by_isolation": isolation_counts
                },
                "isolators": {
                    level.value: True for level in self._isolators.keys()
                },
                "default_isolation": self._default_isolation_level.value
            })

        return status