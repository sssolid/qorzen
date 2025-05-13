from __future__ import annotations
import asyncio
import logging
import networkx as nx
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast

from qorzen.core.base import QorzenManager, BaseManager
from qorzen.utils.exceptions import DependencyError, ManagerInitializationError, ManagerShutdownError

T = TypeVar('T', bound=BaseManager)


class DependencyManager(QorzenManager):
    """Manager for handling dependencies between system components.

    This manager tracks dependencies between different managers
    and ensures they are initialized and shut down in the correct order.
    It uses a directed acyclic graph (DAG) to represent dependencies.
    """

    def __init__(self, logger_manager: Any = None) -> None:
        """Initialize the dependency manager.

        Args:
            logger_manager: Optional logger manager for logging
        """
        super().__init__(name='dependency_manager')
        self._managers: Dict[str, BaseManager] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._graph = nx.DiGraph()
        self._logger = logger_manager.get_logger('dependency_manager') if logger_manager else logging.getLogger(
            'dependency_manager')
        self._initialization_lock = asyncio.Lock()
        self._shutdown_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the dependency manager.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            self._logger.info('Initializing dependency manager')
            self._initialized = True
            self._healthy = True
            self._logger.info('Dependency manager initialized successfully')
        except Exception as e:
            self._logger.error(f'Failed to initialize dependency manager: {str(e)}')
            raise ManagerInitializationError(f'Failed to initialize DependencyManager: {str(e)}',
                                             manager_name=self.name) from e

    async def shutdown(self) -> None:
        """Shutdown the dependency manager and all managed components.

        Shuts down components in reverse dependency order.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        async with self._shutdown_lock:
            try:
                self._logger.info('Shutting down dependency manager and managed components')

                # Get the shutdown order (reverse of initialization order)
                shutdown_order = self._get_shutdown_order()
                self._logger.debug(f'Shutdown order: {shutdown_order}')

                # Shutdown each manager in order
                for manager_name in shutdown_order:
                    manager = self._managers.get(manager_name)
                    if manager and manager.initialized:
                        try:
                            self._logger.debug(f'Shutting down {manager_name}')
                            await manager.shutdown()
                        except Exception as e:
                            self._logger.error(f'Error shutting down {manager_name}: {str(e)}')
                            # Continue with other shutdowns despite the error

                self._managers.clear()
                self._dependencies.clear()
                self._graph.clear()
                self._initialized = False
                self._healthy = False
                self._logger.info('Dependency manager shut down successfully')
            except Exception as e:
                self._logger.error(f'Failed to shut down dependency manager: {str(e)}')
                raise ManagerShutdownError(f'Failed to shut down DependencyManager: {str(e)}',
                                           manager_name=self.name) from e

    def register_manager(self, manager: BaseManager, dependencies: Optional[List[str]] = None) -> None:
        """Register a manager with its dependencies.

        Args:
            manager: The manager to register
            dependencies: List of manager names this manager depends on

        Raises:
            DependencyError: If a dependency is not found or there's a circular dependency
        """
        if not self._initialized:
            raise DependencyError('DependencyManager not initialized')

        manager_name = manager.name
        self._logger.debug(f'Registering manager {manager_name}')

        # Add to managers dictionary
        self._managers[manager_name] = manager

        # Add to dependency graph
        self._graph.add_node(manager_name)

        # Add dependencies if any
        if dependencies:
            self._dependencies[manager_name] = set(dependencies)

            for dep in dependencies:
                if dep not in self._managers:
                    raise DependencyError(f'Dependency {dep} not found for {manager_name}')

                # Add edge from dependency to the manager
                # (A→B means B depends on A)
                self._graph.add_edge(dep, manager_name)

            # Check for cycles after adding edges
            try:
                # This will raise NetworkXUnfeasible if there's a cycle
                list(nx.topological_sort(self._graph))
            except nx.NetworkXUnfeasible:
                # Find and report the cycles
                cycles = list(nx.simple_cycles(self._graph))
                # Remove the edges we just added
                for dep in dependencies:
                    self._graph.remove_edge(dep, manager_name)
                # Remove from managers dictionary
                del self._managers[manager_name]
                # Remove from dependencies dictionary
                if manager_name in self._dependencies:
                    del self._dependencies[manager_name]
                # Raise error
                raise DependencyError(f'Circular dependencies detected: {cycles}')

    def get_manager(self, name: str) -> Optional[BaseManager]:
        """Get a manager by name.

        Args:
            name: The name of the manager to retrieve

        Returns:
            The manager instance or None if not found
        """
        return self._managers.get(name)

    def get_manager_typed(self, name: str, manager_type: Type[T]) -> Optional[T]:
        """Get a manager by name with type checking.

        Args:
            name: The name of the manager to retrieve
            manager_type: The expected type of the manager

        Returns:
            The manager instance or None if not found or type doesn't match
        """
        manager = self._managers.get(name)
        if manager and isinstance(manager, manager_type):
            return cast(T, manager)
        return None

    async def initialize_all(self) -> None:
        """Initialize all managers in dependency order.

        Raises:
            DependencyError: If there's a cycle in the dependency graph
            ManagerInitializationError: If a manager fails to initialize
        """
        if not self._initialized:
            raise DependencyError('DependencyManager not initialized')

        async with self._initialization_lock:
            # Check for cycles
            try:
                init_order = list(nx.topological_sort(self._graph))
            except nx.NetworkXUnfeasible:
                cycles = list(nx.simple_cycles(self._graph))
                raise DependencyError(f'Circular dependencies detected: {cycles}')

            self._logger.debug(f'Initialization order: {init_order}')

            # Initialize managers in order
            for manager_name in init_order:
                manager = self._managers.get(manager_name)
                if manager and not manager.initialized:
                    try:
                        self._logger.debug(f'Initializing {manager_name}')
                        await manager.initialize()
                    except Exception as e:
                        self._logger.error(f'Failed to initialize {manager_name}: {str(e)}')
                        raise ManagerInitializationError(
                            f'Failed to initialize {manager_name}: {str(e)}',
                            manager_name=manager_name
                        ) from e

    def _get_shutdown_order(self) -> List[str]:
        """Get the order for shutting down managers.

        Returns:
            List of manager names in shutdown order
        """
        try:
            # Get initialization order
            init_order = list(nx.topological_sort(self._graph))
            # Reverse it for shutdown
            return list(reversed(init_order))
        except nx.NetworkXUnfeasible:
            # Handle case where graph has cycles (shouldn't happen if we check during registration)
            self._logger.warning('Dependency graph has cycles, using simple reverse order')
            return list(reversed(list(self._managers.keys())))

    def status(self) -> Dict[str, Any]:
        """Get the status of the dependency manager.

        Returns:
            Dictionary containing status information
        """
        base_status = super().status()

        # Add status for all managed components
        manager_statuses = {}
        for name, manager in self._managers.items():
            try:
                manager_statuses[name] = {
                    'initialized': manager.initialized,
                    'healthy': manager.healthy if hasattr(manager, 'healthy') else None,
                    'dependencies': list(self._dependencies.get(name, set()))
                }
            except Exception as e:
                manager_statuses[name] = {
                    'error': f'Failed to get status: {str(e)}'
                }

        base_status.update({
            'managers': manager_statuses,
            'total_managers': len(self._managers)
        })

        return base_status