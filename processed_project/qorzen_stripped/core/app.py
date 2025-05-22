from __future__ import annotations
import asyncio
import importlib
import inspect
import logging
import os
import signal
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, cast, T
from qorzen.core.base import QorzenManager, BaseManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.core.dependency_manager import DependencyManager
from qorzen.core.task_manager import TaskManager, TaskCategory
from qorzen.core.plugin_isolation_manager import PluginIsolationManager, PluginIsolationLevel
from qorzen.utils.exceptions import ApplicationError
class ApplicationCore:
    def __init__(self, config_path: Optional[str]=None) -> None:
        self._config_path = config_path
        self._managers: Dict[str, BaseManager] = {}
        self._initialized = False
        self._logger: Optional[logging.Logger] = None
        self._dependency_manager: Optional[DependencyManager] = None
        self._shutdown_event = asyncio.Event()
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._ui_integration = None
    async def initialize(self, progress_callback: Optional[callable]=None) -> None:
        try:
            self._main_loop = asyncio.get_running_loop()
            await self._init_dependency_manager()
            await self._init_config_manager()
            await self._init_logging_manager()
            await self._init_concurrency_manager()
            await self._init_event_bus_manager()
            await self._init_file_manager()
            await self._init_resource_monitoring_manager()
            await self._init_database_manager()
            await self._init_security_manager()
            await self._init_api_manager()
            await self._init_cloud_manager()
            await self._init_task_manager()
            await self._init_plugin_isolation_manager()
            await self._init_plugin_manager()
            await self._dependency_manager.initialize_all()
            self._initialized = True
            if self._logger:
                self._logger.info('Qorzen initialization complete')
            event_bus_manager = self.get_manager('event_bus_manager')
            if event_bus_manager:
                await event_bus_manager.publish(event_type='system/started', source='app_core', payload={'version': self._get_version()})
        except Exception as e:
            if self._logger:
                self._logger.error(f'Failed to initialize Qorzen: {str(e)}', exc_info=True)
            else:
                print(f'Failed to initialize Qorzen: {str(e)}')
                traceback.print_exc()
            raise ApplicationError(f'Failed to initialize application: {str(e)}') from e
    async def _init_dependency_manager(self) -> None:
        self._dependency_manager = DependencyManager()
        await self._dependency_manager.initialize()
        self._managers['dependency_manager'] = self._dependency_manager
    async def _init_config_manager(self) -> None:
        from qorzen.core.config_manager import ConfigManager
        config_manager = ConfigManager(config_path=self._config_path)
        self._dependency_manager.register_manager(config_manager)
        self._managers['config_manager'] = config_manager
    async def _init_logging_manager(self) -> None:
        from qorzen.core.logging_manager import LoggingManager
        config_manager = self.get_manager('config_manager')
        logging_manager = LoggingManager(config_manager)
        self._dependency_manager.register_manager(logging_manager, dependencies=['config_manager'])
        self._managers['logging_manager'] = logging_manager
        self._managers.get('config_manager').set_logger(logging_manager)
        self._logger = logging_manager.get_logger('app_core')
    async def _init_concurrency_manager(self) -> None:
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        concurrency_manager = ConcurrencyManager(config_manager, logging_manager)
        self._dependency_manager.register_manager(concurrency_manager, dependencies=['config_manager', 'logging_manager'])
        self._managers['concurrency_manager'] = concurrency_manager
    async def _init_event_bus_manager(self) -> None:
        from qorzen.core.event_bus_manager import EventBusManager
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        concurrency_manager = self.get_manager('concurrency_manager')
        event_bus_manager = EventBusManager(config_manager, logging_manager, concurrency_manager)
        self._dependency_manager.register_manager(event_bus_manager, dependencies=['config_manager', 'logging_manager', 'concurrency_manager'])
        self._managers['event_bus_manager'] = event_bus_manager
    async def _init_file_manager(self) -> None:
        from qorzen.core.file_manager import FileManager
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        file_manager = FileManager(config_manager, logging_manager)
        self._dependency_manager.register_manager(file_manager, dependencies=['config_manager', 'logging_manager'])
        self._managers['file_manager'] = file_manager
    async def _init_resource_monitoring_manager(self) -> None:
        from qorzen.core.resource_monitoring_manager import ResourceMonitoringManager
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        event_bus_manager = self.get_manager('event_bus_manager')
        concurrency_manager = self.get_manager('concurrency_manager')
        resource_monitoring_manager = ResourceMonitoringManager(config_manager, logging_manager, event_bus_manager, concurrency_manager)
        self._dependency_manager.register_manager(resource_monitoring_manager, dependencies=['config_manager', 'logging_manager', 'event_bus_manager', 'concurrency_manager'])
        self._managers['resource_monitoring_manager'] = resource_monitoring_manager
    async def _init_database_manager(self) -> None:
        from qorzen.core.database_manager import DatabaseManager
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        database_manager = DatabaseManager(config_manager, logging_manager)
        self._dependency_manager.register_manager(database_manager, dependencies=['config_manager', 'logging_manager'])
        self._managers['database_manager'] = database_manager
    async def _init_security_manager(self) -> None:
        from qorzen.core.security_manager import SecurityManager
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        event_bus_manager = self.get_manager('event_bus_manager')
        database_manager = self.get_manager('database_manager')
        security_manager = SecurityManager(config_manager, logging_manager, event_bus_manager, database_manager)
        self._dependency_manager.register_manager(security_manager, dependencies=['config_manager', 'logging_manager', 'event_bus_manager', 'database_manager'])
        self._managers['security_manager'] = security_manager
    async def _init_api_manager(self) -> None:
        from qorzen.core.api_manager import APIManager
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        security_manager = self.get_manager('security_manager')
        event_bus_manager = self.get_manager('event_bus_manager')
        concurrency_manager = self.get_manager('concurrency_manager')
        api_manager = APIManager(config_manager, logging_manager, security_manager, event_bus_manager, concurrency_manager)
        self._dependency_manager.register_manager(api_manager, dependencies=['config_manager', 'logging_manager', 'security_manager', 'event_bus_manager', 'concurrency_manager'])
        self._managers['api_manager'] = api_manager
    async def _init_cloud_manager(self) -> None:
        from qorzen.core.cloud_manager import CloudManager
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        file_manager = self.get_manager('file_manager')
        cloud_manager = CloudManager(config_manager, logging_manager, file_manager)
        self._dependency_manager.register_manager(cloud_manager, dependencies=['config_manager', 'logging_manager', 'file_manager'])
        self._managers['cloud_manager'] = cloud_manager
    async def _init_task_manager(self) -> None:
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        event_bus_manager = self.get_manager('event_bus_manager')
        concurrency_manager = self.get_manager('concurrency_manager')
        task_manager = TaskManager(concurrency_manager, event_bus_manager, logging_manager, config_manager)
        self._dependency_manager.register_manager(task_manager, dependencies=['config_manager', 'logging_manager', 'event_bus_manager', 'concurrency_manager'])
        self._managers['task_manager'] = task_manager
    async def _init_plugin_isolation_manager(self) -> None:
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        concurrency_manager = self.get_manager('concurrency_manager')
        plugin_isolation_manager = PluginIsolationManager(concurrency_manager, logging_manager, config_manager)
        self._dependency_manager.register_manager(plugin_isolation_manager, dependencies=['config_manager', 'logging_manager', 'concurrency_manager'])
        self._managers['plugin_isolation'] = plugin_isolation_manager
    async def _init_plugin_manager(self) -> None:
        from qorzen.core.plugin_manager import PluginManager
        config_manager = self.get_manager('config_manager')
        logging_manager = self.get_manager('logging_manager')
        event_bus_manager = self.get_manager('event_bus_manager')
        file_manager = self.get_manager('file_manager')
        task_manager = self.get_manager('task_manager')
        plugin_isolation = self.get_manager('plugin_isolation_manager')
        plugin_manager = PluginManager(application_core=self, config_manager=config_manager, logger_manager=logging_manager, event_bus_manager=event_bus_manager, file_manager=file_manager, task_manager=task_manager, plugin_isolation_manager=plugin_isolation)
        self._dependency_manager.register_manager(plugin_manager, dependencies=['config_manager', 'logging_manager', 'event_bus_manager', 'file_manager', 'task_manager', 'plugin_isolation_manager'])
        self._managers['plugin_manager'] = plugin_manager
    def get_manager(self, name: str) -> Optional[BaseManager]:
        return self._managers.get(name)
    def get_manager_typed(self, name: str, manager_type: Type[T]) -> Optional[T]:
        manager = self._managers.get(name)
        if manager and isinstance(manager, manager_type):
            return cast(T, manager)
        return None
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            if self._logger:
                self._logger.info('Shutting down Qorzen')
            try:
                event_bus_manager = self.get_manager('event_bus_manager')
                if event_bus_manager:
                    await asyncio.wait_for(event_bus_manager.publish(event_type='system/shutting_down', source='app_core'), timeout=2.0)
            except (asyncio.TimeoutError, Exception) as e:
                if self._logger:
                    self._logger.warning(f'Error publishing shutdown event: {str(e)}')
            plugin_manager = self.get_manager('plugin_manager')
            if plugin_manager:
                try:
                    await asyncio.wait_for(plugin_manager.shutdown(), timeout=10.0)
                except asyncio.TimeoutError:
                    if self._logger:
                        self._logger.warning('Timeout shutting down plugin manager')
                except Exception as e:
                    if self._logger:
                        self._logger.error(f'Error shutting down plugin manager: {str(e)}')
            if self._dependency_manager:
                try:
                    await asyncio.wait_for(self._dependency_manager.shutdown(), timeout=15.0)
                except asyncio.TimeoutError:
                    if self._logger:
                        self._logger.warning('Timeout during dependency manager shutdown')
                    for name, manager in list(self._managers.items()):
                        if hasattr(manager, '_initialized') and getattr(manager, '_initialized', False):
                            try:
                                self._logger.warning(f'Force shutting down {name}')
                                setattr(manager, '_initialized', False)
                                setattr(manager, '_healthy', False)
                            except Exception:
                                pass
                except Exception as e:
                    if self._logger:
                        self._logger.error(f'Error during dependency manager shutdown: {str(e)}')
            self._managers.clear()
            self._initialized = False
            self._shutdown_event.set()
            if self._logger:
                self._logger.info('Qorzen shutdown complete')
            def force_exit():
                import os, sys, time
                time.sleep(2)
                print('Forcing exit after timeout')
                os._exit(0)
            import threading
            exit_thread = threading.Thread(target=force_exit, daemon=True)
            exit_thread.start()
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error during shutdown: {str(e)}', exc_info=True)
            else:
                print(f'Error during shutdown: {str(e)}')
                traceback.print_exc()
            self._shutdown_event.set()
            raise ApplicationError(f'Failed to shutdown application: {str(e)}') from e
    def set_ui_integration(self, ui_integration: Any) -> None:
        self._ui_integration = ui_integration
        event_bus_manager = self.get_manager('event_bus_manager')
        if event_bus_manager and self._initialized:
            asyncio.create_task(event_bus_manager.publish(event_type='ui/ready', source='app_core', payload={'ui_integration': ui_integration}))
            if self._logger:
                self._logger.info('UI ready event published for plugins')
    def get_ui_integration(self) -> Any:
        return self._ui_integration
    def is_initialized(self) -> bool:
        return self._initialized
    def _get_version(self) -> str:
        try:
            from qorzen.__version__ import __version__ as app_version
            return app_version
        except ImportError:
            return '0.1.0'
    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()
    def setup_signal_handlers(self) -> None:
        if sys.platform != 'win32':
            signal.signal(signal.SIGINT, lambda sig, frame: asyncio.create_task(self._signal_handler(sig)))
    async def _signal_handler(self, sig: int) -> None:
        if self._logger:
            self._logger.info(f'Received signal {sig}, shutting down')
        await self.shutdown()
    async def submit_core_task(self, func: callable, *args: Any, name: str='core_task', **kwargs: Any) -> str:
        if not self._initialized:
            raise ApplicationError('Application core not initialized')
        task_manager = self.get_manager('task_manager')
        if not task_manager:
            raise ApplicationError('Task manager not available')
        try:
            return await task_manager.submit_task(*args, func=func, name=name, category=TaskCategory.CORE, **kwargs)
        except Exception as e:
            if self._logger:
                self._logger.error(f'Failed to submit core task: {str(e)}', exc_info=True)
            raise ApplicationError(f'Failed to submit core task: {str(e)}') from e
    async def status_async(self) -> Dict[str, Any]:
        status = {'name': 'AsyncApplicationCore', 'initialized': self._initialized, 'version': self._get_version(), 'ui_integration': self._ui_integration is not None, 'managers': {}}
        for name, manager in self._managers.items():
            try:
                if inspect.iscoroutinefunction(manager.status):
                    mgr_status = await manager.status()
                else:
                    result = manager.status()
                    mgr_status = await result if inspect.isawaitable(result) else result
                status['managers'][name] = mgr_status
            except Exception as e:
                status['managers'][name] = {'error': f'Failed to get status: {e}', 'initialized': getattr(manager, 'initialized', False), 'healthy': getattr(manager, 'healthy', False)}
        return status
    def status(self) -> Dict[str, Any]:
        status = {'name': 'AsyncApplicationCore', 'initialized': self._initialized, 'version': self._get_version(), 'ui_integration': self._ui_integration is not None, 'managers': {}}
        for name, manager in self._managers.items():
            try:
                status['managers'][name] = manager.status()
            except Exception as e:
                status['managers'][name] = {'error': f'Failed to get status: {str(e)}', 'initialized': getattr(manager, 'initialized', False), 'healthy': getattr(manager, 'healthy', False)}
        return status