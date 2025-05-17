from __future__ import annotations
import asyncio
import logging
import networkx as nx
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast
from qorzen.core.base import QorzenManager, BaseManager
from qorzen.utils.exceptions import DependencyError, ManagerInitializationError, ManagerShutdownError, DatabaseManagerInitializationError
T = TypeVar('T', bound=BaseManager)
class DependencyManager(QorzenManager):
    def __init__(self, logger_manager: Any=None) -> None:
        super().__init__(name='dependency_manager')
        self._managers: Dict[str, BaseManager] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._graph = nx.DiGraph()
        self._logger = logger_manager.get_logger('dependency_manager') if logger_manager else logging.getLogger('dependency_manager')
        self._initialization_lock = asyncio.Lock()
        self._shutdown_lock = asyncio.Lock()
    async def initialize(self) -> None:
        try:
            self._logger.info('Initializing dependency manager')
            self._initialized = True
            self._healthy = True
            self._logger.info('Dependency manager initialized successfully')
        except Exception as e:
            self._logger.error(f'Failed to initialize dependency manager: {str(e)}')
            raise ManagerInitializationError(f'Failed to initialize DependencyManager: {str(e)}', manager_name=self.name) from e
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        async with self._shutdown_lock:
            try:
                self._logger.info('Shutting down dependency manager and managed components')
                shutdown_order = self._get_shutdown_order()
                self._logger.debug(f'Shutdown order: {shutdown_order}')
                for manager_name in shutdown_order:
                    manager = self._managers.get(manager_name)
                    if manager and manager.initialized:
                        try:
                            self._logger.debug(f'Shutting down {manager_name}')
                            await manager.shutdown()
                        except Exception as e:
                            self._logger.error(f'Error shutting down {manager_name}: {str(e)}')
                self._managers.clear()
                self._dependencies.clear()
                self._graph.clear()
                self._initialized = False
                self._healthy = False
                self._logger.info('Dependency manager shut down successfully')
            except Exception as e:
                self._logger.error(f'Failed to shut down dependency manager: {str(e)}')
                raise ManagerShutdownError(f'Failed to shut down DependencyManager: {str(e)}', manager_name=self.name) from e
    def register_manager(self, manager: BaseManager, dependencies: Optional[List[str]]=None) -> None:
        if not self._initialized:
            raise DependencyError('DependencyManager not initialized')
        manager_name = manager.name
        self._logger.debug(f'Registering manager {manager_name}')
        self._managers[manager_name] = manager
        self._graph.add_node(manager_name)
        if dependencies:
            self._dependencies[manager_name] = set(dependencies)
            for dep in dependencies:
                if dep not in self._managers:
                    raise DependencyError(f'Dependency {dep} not found for {manager_name}')
                self._graph.add_edge(dep, manager_name)
            try:
                list(nx.topological_sort(self._graph))
            except nx.NetworkXUnfeasible:
                cycles = list(nx.simple_cycles(self._graph))
                for dep in dependencies:
                    self._graph.remove_edge(dep, manager_name)
                del self._managers[manager_name]
                if manager_name in self._dependencies:
                    del self._dependencies[manager_name]
                raise DependencyError(f'Circular dependencies detected: {cycles}')
    def get_manager(self, name: str) -> Optional[BaseManager]:
        return self._managers.get(name)
    def get_manager_typed(self, name: str, manager_type: Type[T]) -> Optional[T]:
        manager = self._managers.get(name)
        if manager and isinstance(manager, manager_type):
            return cast(T, manager)
        return None
    async def initialize_all(self) -> None:
        if not self._initialized:
            raise DependencyError('DependencyManager not initialized')
        async with self._initialization_lock:
            try:
                init_order = list(nx.topological_sort(self._graph))
            except nx.NetworkXUnfeasible:
                cycles = list(nx.simple_cycles(self._graph))
                raise DependencyError(f'Circular dependencies detected: {cycles}')
            self._logger.debug(f'Initialization order: {init_order}')
            for manager_name in init_order:
                manager = self._managers.get(manager_name)
                if manager and (not manager.initialized):
                    try:
                        self._logger.debug(f'Initializing {manager_name}')
                        await manager.initialize()
                    except DatabaseManagerInitializationError as e:
                        self._logger.error(f'Failed to initialize {manager_name}: {str(e)}')
                        pass
                    except Exception as e:
                        self._logger.error(f'Failed to initialize {manager_name}: {str(e)}')
                        raise ManagerInitializationError(f'Failed to initialize {manager_name}: {str(e)}', manager_name=manager_name) from e
    def _get_shutdown_order(self) -> List[str]:
        try:
            init_order = list(nx.topological_sort(self._graph))
            return list(reversed(init_order))
        except nx.NetworkXUnfeasible:
            self._logger.warning('Dependency graph has cycles, using simple reverse order')
            return list(reversed(list(self._managers.keys())))
    def status(self) -> Dict[str, Any]:
        base_status = super().status()
        manager_statuses = {}
        for name, manager in self._managers.items():
            try:
                manager_statuses[name] = {'initialized': manager.initialized, 'healthy': manager.healthy if hasattr(manager, 'healthy') else None, 'dependencies': list(self._dependencies.get(name, set()))}
            except Exception as e:
                manager_statuses[name] = {'error': f'Failed to get status: {str(e)}'}
        base_status.update({'managers': manager_statuses, 'total_managers': len(self._managers)})
        return base_status