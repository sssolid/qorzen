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
    NONE = 'none'
    THREAD = 'thread'
    PROCESS = 'process'
@dataclass
class PluginResourceLimits:
    max_memory_mb: int = 256
    max_cpu_percent: float = 50.0
    max_file_handles: int = 100
    max_network_connections: int = 20
    max_execution_time_seconds: int = 300
@dataclass
class IsolatedPluginInfo:
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
    @abstractmethod
    async def initialize(self) -> None:
        pass
    @abstractmethod
    async def shutdown(self) -> None:
        pass
    @abstractmethod
    async def run_plugin_method(self, plugin_id: str, method_name: str, args: Optional[List[Any]]=None, kwargs: Optional[Dict[str, Any]]=None, timeout: Optional[float]=None) -> Any:
        pass
    @abstractmethod
    async def load_plugin(self, plugin_id: str, plugin_path: str) -> bool:
        pass
    @abstractmethod
    async def unload_plugin(self, plugin_id: str) -> bool:
        pass
class ThreadIsolator(PluginIsolator):
    def __init__(self, concurrency_manager: Any, logger: Any) -> None:
        self._concurrency_manager = concurrency_manager
        self._logger = logger
        self._plugins: Dict[str, Any] = {}
        self._plugin_info: Dict[str, IsolatedPluginInfo] = {}
        self._method_locks: Dict[str, asyncio.Lock] = {}
    async def initialize(self) -> None:
        self._logger.debug('Initializing thread isolator')
        pass
    async def shutdown(self) -> None:
        self._logger.debug('Shutting down thread isolator')
        for plugin_id in list(self._plugins.keys()):
            try:
                await self.unload_plugin(plugin_id)
            except Exception as e:
                self._logger.warning(f'Error unloading plugin {plugin_id} during shutdown: {e}')
        self._plugins.clear()
        self._plugin_info.clear()
        self._method_locks.clear()
    async def run_plugin_method(self, plugin_id: str, method_name: str, args: Optional[List[Any]]=None, kwargs: Optional[Dict[str, Any]]=None, timeout: Optional[float]=None) -> Any:
        if plugin_id not in self._plugins:
            raise PluginIsolationError(f'Plugin {plugin_id} not loaded')
        plugin = self._plugins[plugin_id]
        method = getattr(plugin, method_name, None)
        if not method:
            raise PluginIsolationError(f'Method {method_name} not found in plugin {plugin_id}')
        method_key = f'{plugin_id}:{method_name}'
        if method_key not in self._method_locks:
            self._method_locks[method_key] = asyncio.Lock()
        async with self._method_locks[method_key]:
            try:
                if timeout:
                    return await asyncio.wait_for(self._concurrency_manager.run_in_thread(method, *(args or []), **kwargs or {}), timeout=timeout)
                else:
                    return await self._concurrency_manager.run_in_thread(method, *(args or []), **kwargs or {})
            except asyncio.TimeoutError:
                raise PluginIsolationError(f'Method {method_name} in plugin {plugin_id} timed out after {timeout} seconds')
            except Exception as e:
                self._logger.error(f'Error calling method {method_name} in plugin {plugin_id}: {e}', exc_info=True)
                raise PluginIsolationError(f'Error calling method {method_name} in plugin {plugin_id}: {str(e)}') from e
    async def load_plugin(self, plugin_id: str, plugin_path: str) -> bool:
        try:
            self._logger.debug(f'Loading plugin {plugin_id} from {plugin_path}')
            if plugin_id in self._plugins:
                self._logger.warning(f'Plugin {plugin_id} is already loaded, unloading first')
                await self.unload_plugin(plugin_id)
            spec = importlib.util.spec_from_file_location(f'plugin_{plugin_id}', plugin_path)
            if not spec or not spec.loader:
                raise PluginIsolationError(f'Failed to create module spec for {plugin_path}')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, 'name') and hasattr(obj, 'version'):
                    plugin_class = obj
                    break
            if not plugin_class:
                raise PluginIsolationError(f'No plugin class found in {plugin_path}')
            plugin = plugin_class()
            self._plugins[plugin_id] = plugin
            self._plugin_info[plugin_id] = IsolatedPluginInfo(plugin_id=plugin_id, name=getattr(plugin, 'name', plugin_id), isolation_level=PluginIsolationLevel.THREAD, path=plugin_path, loaded_at=time.time(), healthy=True, metadata={'version': getattr(plugin, 'version', 'unknown'), 'description': getattr(plugin, 'description', ''), 'author': getattr(plugin, 'author', 'unknown')})
            self._logger.info(f'Successfully loaded plugin {plugin_id} in thread isolation')
            return True
        except Exception as e:
            self._logger.error(f'Error loading plugin {plugin_id}: {e}', exc_info=True)
            if plugin_id in self._plugin_info:
                self._plugin_info[plugin_id].healthy = False
                self._plugin_info[plugin_id].error = str(e)
            if plugin_id in self._plugins:
                del self._plugins[plugin_id]
            raise PluginIsolationError(f'Failed to load plugin {plugin_id}: {str(e)}') from e
    async def unload_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self._plugins:
            self._logger.warning(f'Plugin {plugin_id} is not loaded')
            return False
        try:
            self._logger.debug(f'Unloading plugin {plugin_id}')
            plugin = self._plugins[plugin_id]
            if hasattr(plugin, 'shutdown'):
                try:
                    await asyncio.wait_for(self._concurrency_manager.run_in_thread(plugin.shutdown), timeout=10.0)
                except asyncio.TimeoutError:
                    self._logger.warning(f'Shutdown of plugin {plugin_id} timed out')
                except Exception as e:
                    self._logger.warning(f'Error during shutdown of plugin {plugin_id}: {e}')
            del self._plugins[plugin_id]
            if plugin_id in self._plugin_info:
                del self._plugin_info[plugin_id]
            for key in list(self._method_locks.keys()):
                if key.startswith(f'{plugin_id}:'):
                    del self._method_locks[key]
            self._logger.info(f'Successfully unloaded plugin {plugin_id}')
            return True
        except Exception as e:
            self._logger.error(f'Error unloading plugin {plugin_id}: {e}', exc_info=True)
            raise PluginIsolationError(f'Failed to unload plugin {plugin_id}: {str(e)}') from e
class PluginIsolationManager(QorzenManager):
    def __init__(self, concurrency_manager: Any, logger_manager: Any, config_manager: Any, name: str='plugin_isolation_manager') -> None:
        super().__init__(name=name)
        self._concurrency_manager = concurrency_manager
        self._logger = logger_manager.get_logger('plugin_isolation')
        self._config_manager = config_manager
        self._isolators: Dict[PluginIsolationLevel, PluginIsolator] = {}
        self._plugin_isolations: Dict[str, PluginIsolationLevel] = {}
        self._default_isolation_level = PluginIsolationLevel.THREAD
    async def initialize(self) -> None:
        try:
            self._logger.info('Initializing plugin isolation manager')
            plugin_config = await self._config_manager.get('plugins', {})
            if not hasattr(plugin_config, 'isolation'):
                self._logger.warning('Plugin isolation configuration not found in configuration')
            isolation_config = plugin_config.get('isolation', {})
            if not hasattr(isolation_config, 'default_level'):
                self._logger.warning('Default isolation level not found in configuration')
            default_level = isolation_config.get('default_level', 'thread')
            try:
                self._default_isolation_level = PluginIsolationLevel(default_level)
            except ValueError:
                self._logger.warning(f"Invalid default isolation level '{default_level}', using {self._default_isolation_level}")
            self._isolators[PluginIsolationLevel.THREAD] = ThreadIsolator(self._concurrency_manager, self._logger)
            for level, isolator in self._isolators.items():
                self._logger.debug(f'Initializing {level} isolator')
                await isolator.initialize()
            self._initialized = True
            self._healthy = True
            self._logger.info('Plugin isolation manager initialized successfully')
        except Exception as e:
            self._logger.error(f'Failed to initialize plugin isolation manager: {e}', exc_info=True)
            raise ManagerInitializationError(f'Failed to initialize {self.name}: {str(e)}', manager_name=self.name) from e
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            self._logger.info('Shutting down plugin isolation manager')
            for level, isolator in self._isolators.items():
                try:
                    self._logger.debug(f'Shutting down {level} isolator')
                    await isolator.shutdown()
                except Exception as e:
                    self._logger.error(f'Error shutting down {level} isolator: {e}')
            self._isolators.clear()
            self._plugin_isolations.clear()
            self._initialized = False
            self._healthy = False
            self._logger.info('Plugin isolation manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down plugin isolation manager: {e}', exc_info=True)
            raise ManagerShutdownError(f'Failed to shut down {self.name}: {str(e)}', manager_name=self.name) from e
    async def load_plugin(self, plugin_id: str, plugin_path: str, isolation_level: Optional[PluginIsolationLevel]=None) -> bool:
        if not self._initialized:
            raise PluginIsolationError('Plugin isolation manager not initialized')
        if isolation_level is None:
            isolation_level = self._default_isolation_level
        if isolation_level not in self._isolators:
            raise PluginIsolationError(f'Isolation level {isolation_level} not supported')
        if plugin_id in self._plugin_isolations:
            existing_level = self._plugin_isolations[plugin_id]
            if existing_level != isolation_level:
                self._logger.debug(f'Plugin {plugin_id} is already loaded with {existing_level} isolation, unloading before reloading with {isolation_level}')
                await self.unload_plugin(plugin_id)
            else:
                self._logger.debug(f'Plugin {plugin_id} is already loaded, unloading first')
                await self.unload_plugin(plugin_id)
        isolator = self._isolators[isolation_level]
        try:
            success = await isolator.load_plugin(plugin_id, plugin_path)
            if success:
                self._plugin_isolations[plugin_id] = isolation_level
                self._logger.info(f'Successfully loaded plugin {plugin_id} with {isolation_level} isolation')
            return success
        except Exception as e:
            self._logger.error(f'Failed to load plugin {plugin_id}: {e}', exc_info=True)
            raise PluginIsolationError(f'Failed to load plugin {plugin_id}: {str(e)}') from e
    async def unload_plugin(self, plugin_id: str) -> bool:
        if not self._initialized:
            raise PluginIsolationError('Plugin isolation manager not initialized')
        if plugin_id not in self._plugin_isolations:
            self._logger.warning(f'Plugin {plugin_id} is not loaded')
            return False
        isolation_level = self._plugin_isolations[plugin_id]
        isolator = self._isolators[isolation_level]
        try:
            success = await isolator.unload_plugin(plugin_id)
            if success:
                del self._plugin_isolations[plugin_id]
                self._logger.info(f'Successfully unloaded plugin {plugin_id}')
            return success
        except Exception as e:
            self._logger.error(f'Failed to unload plugin {plugin_id}: {e}', exc_info=True)
            raise PluginIsolationError(f'Failed to unload plugin {plugin_id}: {str(e)}') from e
    async def run_plugin_method(self, plugin_id: str, method_name: str, args: Optional[List[Any]]=None, kwargs: Optional[Dict[str, Any]]=None, timeout: Optional[float]=None) -> Any:
        if not self._initialized:
            raise PluginIsolationError('Plugin isolation manager not initialized')
        if plugin_id not in self._plugin_isolations:
            raise PluginIsolationError(f'Plugin {plugin_id} not loaded')
        isolation_level = self._plugin_isolations[plugin_id]
        isolator = self._isolators[isolation_level]
        try:
            method_start = time.time()
            result = await isolator.run_plugin_method(plugin_id, method_name, args or [], kwargs or {}, timeout)
            method_duration = time.time() - method_start
            if method_duration > 1.0:
                self._logger.debug(f'Plugin {plugin_id} method {method_name} took {method_duration:.2f} seconds')
            return result
        except Exception as e:
            self._logger.error(f'Error running method {method_name} in plugin {plugin_id}: {e}', exc_info=True)
            raise PluginIsolationError(f'Error running method {method_name} in plugin {plugin_id}: {str(e)}') from e
    def get_plugin_isolation_level(self, plugin_id: str) -> Optional[PluginIsolationLevel]:
        return self._plugin_isolations.get(plugin_id)
    def is_plugin_loaded(self, plugin_id: str) -> bool:
        return plugin_id in self._plugin_isolations
    def get_loaded_plugins(self) -> Dict[str, PluginIsolationLevel]:
        return self._plugin_isolations.copy()
    def status(self) -> Dict[str, Any]:
        status = super().status()
        if self._initialized:
            isolation_counts = {level.value: 0 for level in PluginIsolationLevel}
            for level in self._plugin_isolations.values():
                isolation_counts[level.value] += 1
            status.update({'plugins': {'total': len(self._plugin_isolations), 'by_isolation': isolation_counts}, 'isolators': {level.value: True for level in self._isolators.keys()}, 'default_isolation': self._default_isolation_level.value})
        return status