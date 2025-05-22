from __future__ import annotations
import abc
import asyncio
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Set, Callable, Awaitable
from PySide6.QtCore import QObject
@runtime_checkable
class PluginInterface(Protocol):
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    async def initialize(self, application_core: Any) -> None:
        ...
    async def on_ui_ready(self, ui_integration: Any) -> None:
        ...
    async def shutdown(self) -> None:
        ...
class BasePlugin(QObject):
    name: str = 'base_plugin'
    version: str = '0.0.0'
    description: str = 'Base plugin'
    author: str = 'Unknown'
    display_name: Optional[str] = None
    dependencies: List[str] = []
    plugin_id: str = None
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False
        self._ui_initialized = False
        self._shutdown = False
        self._lock = asyncio.Lock()
        self._application_core = None
        self._event_bus_manager = None
        self._logger = None
        self._config_manager = None
        self._file_manager = None
        self._thread_manager = None
        self._database_manager = None
        self._remote_service_manager = None
        self._security_manager = None
        self._api_manager = None
        self._cloud_manager = None
        self._task_manager = None
        self._registered_tasks: Set[str] = set()
        self._ui_registry = None
    async def initialize(self, application_core: Any, **kwargs: Any) -> None:
        async with self._lock:
            if self._initialized:
                return
            try:
                self._application_core = application_core
                if hasattr(application_core, 'get_manager'):
                    self._event_bus_manager = application_core.get_manager('event_bus_manager')
                    logger_manager = application_core.get_manager('logging_manager')
                    if logger_manager:
                        self._logger = logger_manager.get_logger(self.name)
                        if self._logger:
                            self._logger.debug(f'Plugin {self.name} v{self.version} initializing...')
                    self._config_manager = application_core.get_manager('config_manager')
                    self._file_manager = application_core.get_manager('file_manager')
                    self._thread_manager = application_core.get_manager('concurrency_manager')
                    self._database_manager = application_core.get_manager('database_manager')
                    self._remote_service_manager = application_core.get_manager('remote_services')
                    self._security_manager = application_core.get_manager('security_manager')
                    self._api_manager = application_core.get_manager('api_manager')
                    self._cloud_manager = application_core.get_manager('cloud_manager')
                    self._task_manager = application_core.get_manager('task_manager')
                try:
                    from qorzen.plugin_system.ui_registry import UIComponentRegistry
                    self._ui_registry = UIComponentRegistry(self.name, thread_manager=self._thread_manager)
                except (ImportError, Exception) as e:
                    if self._logger:
                        self._logger.warning(f'Could not initialize UI registry: {str(e)}')
                    self._ui_registry = None
                self._initialized = True
                if self._logger:
                    self._logger.info(f'{self.name} v{self.version} initialized successfully')
            except Exception as e:
                if self._logger:
                    self._logger.error(f'Error during plugin initialization: {str(e)}', exc_info=True)
                raise
    async def on_ui_ready(self, ui_integration: Any) -> None:
        async with self._lock:
            self._ui_initialized = True
            if self._logger:
                self._logger.debug(f'{self.name} UI ready event received')
    async def register_task(self, task_name: str, function: Callable, **properties: Any) -> None:
        if not self._task_manager:
            if self._logger:
                self._logger.warning(f"Task manager not available, can't register task {task_name}")
            return
        await self._task_manager.register_task(self.name, task_name, function, **properties)
        self._registered_tasks.add(task_name)
        if self._logger:
            self._logger.debug(f'Registered task: {task_name}')
    async def execute_task(self, task_name: str, *args: Any, **kwargs: Any) -> Optional[str]:
        if not self._task_manager:
            if self._logger:
                self._logger.warning(f"Task manager not available, can't execute task {task_name}")
            return None
        if task_name not in self._registered_tasks:
            if self._logger:
                self._logger.warning(f'Task not registered: {task_name}')
            return None
        return await self._task_manager.execute_task(self.name, task_name, *args, **kwargs)
    async def register_ui_component(self, component: Any, component_type: str='widget') -> Any:
        if self._ui_registry:
            return self._ui_registry.register(component, component_type)
        return component
    def get_registered_tasks(self) -> Set[str]:
        return self._registered_tasks.copy()
    async def shutdown(self) -> None:
        async with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
            if self._ui_registry:
                await self._ui_registry.cleanup()
            self._registered_tasks.clear()
            self._initialized = False
            self._ui_initialized = False
            if self._logger:
                self._logger.info(f'{self.name} shutdown complete')
    async def status(self) -> Dict[str, Any]:
        async with self._lock:
            return {'name': self.name, 'version': self.version, 'description': self.description, 'initialized': self._initialized, 'ui_initialized': self._ui_initialized, 'shutdown': self._shutdown}