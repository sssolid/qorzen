from __future__ import annotations

import abc
import asyncio
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Set, Callable, Awaitable

from PySide6.QtCore import QObject


@runtime_checkable
class PluginInterface(Protocol):
    """Protocol defining the expected interface for plugins."""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]

    async def initialize(self, application_core: Any) -> None:
        """Initialize the plugin asynchronously."""
        ...

    async def on_ui_ready(self, ui_integration: Any) -> None:
        """Called when the UI is ready for plugin integration."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the plugin asynchronously."""
        ...


class BasePlugin(QObject):
    """Base class for plugins providing common functionality."""
    name: str = 'base_plugin'
    version: str = '0.0.0'
    description: str = 'Base plugin'
    author: str = 'Unknown'
    display_name: Optional[str] = None
    dependencies: List[str] = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self._initialized = False
        self._ui_initialized = False
        self._shutdown = False
        self._lock = asyncio.Lock()
        self._application_core = None

        # Manager references
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

    async def initialize(self, application_core: Any) -> None:
        """
        Initialize the plugin asynchronously with the application core.

        Args:
            application_core: The main application core instance
        """
        async with self._lock:
            if self._initialized:
                return

            self._application_core = application_core

            # Get all required managers from the application core
            self._event_bus_manager = application_core.get_manager('event_bus_manager')
            logger_manager = application_core.get_manager('logging_manager')
            if logger_manager:
                self._logger = logger_manager.get_logger(self.name)
            self._config_manager = application_core.get_manager('config_manager')
            self._file_manager = application_core.get_manager('file_manager')
            self._thread_manager = application_core.get_manager('concurrency_manager')
            self._database_manager = application_core.get_manager('database_manager')
            self._remote_service_manager = application_core.get_manager('remote_services')
            self._security_manager = application_core.get_manager('security_manager')
            self._api_manager = application_core.get_manager('api_manager')
            self._cloud_manager = application_core.get_manager('cloud_manager')
            self._task_manager = application_core.get_manager('task_manager')

            # Initialize UI component registry
            from qorzen.plugin_system.ui_registry import UIComponentRegistry
            self._ui_registry = UIComponentRegistry(self.name, thread_manager=self._thread_manager)

            self._initialized = True

            if self._logger:
                self._logger.info(f"{self.name} v{self.version} initialized successfully")

    async def on_ui_ready(self, ui_integration: Any) -> None:
        """
        Called when the UI is ready for plugin integration.

        Args:
            ui_integration: The UI integration instance
        """
        async with self._lock:
            self._ui_initialized = True

            if self._logger:
                self._logger.debug(f"{self.name} UI ready event received")

    async def register_task(self, task_name: str, function: Callable, **properties: Any) -> None:
        """
        Register a task with the task manager.

        Args:
            task_name: The name of the task
            function: The function to execute
            **properties: Additional task properties
        """
        if not self._task_manager:
            if self._logger:
                self._logger.warning(f"Task manager not available, can't register task {task_name}")
            return

        await self._task_manager.register_task(self.name, task_name, function, **properties)
        self._registered_tasks.add(task_name)

        if self._logger:
            self._logger.debug(f'Registered task: {task_name}')

    async def execute_task(self, task_name: str, *args: Any, **kwargs: Any) -> Optional[str]:
        """
        Execute a registered task.

        Args:
            task_name: The name of the task to execute
            *args: Positional arguments for the task
            **kwargs: Keyword arguments for the task

        Returns:
            Optional[str]: The task ID if execution was successful, None otherwise
        """
        if not self._task_manager:
            if self._logger:
                self._logger.warning(f"Task manager not available, can't execute task {task_name}")
            return None

        if task_name not in self._registered_tasks:
            if self._logger:
                self._logger.warning(f'Task not registered: {task_name}')
            return None

        return await self._task_manager.execute_task(self.name, task_name, *args, **kwargs)

    async def register_ui_component(self, component: Any, component_type: str = 'widget') -> Any:
        """
        Register a UI component.

        Args:
            component: The UI component to register
            component_type: The type of component

        Returns:
            Any: The registered component
        """
        if self._ui_registry:
            return self._ui_registry.register(component, component_type)
        return component

    def get_registered_tasks(self) -> Set[str]:
        """
        Get the set of registered tasks.

        Returns:
            Set[str]: The set of registered task names
        """
        return self._registered_tasks.copy()

    async def shutdown(self) -> None:
        """Shutdown the plugin asynchronously."""
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
                self._logger.info(f"{self.name} shutdown complete")

    async def status(self) -> Dict[str, Any]:
        """
        Get the current status of the plugin.

        Returns:
            Dict[str, Any]: The plugin status information
        """
        async with self._lock:
            return {
                'name': self.name,
                'version': self.version,
                'description': self.description,
                'initialized': self._initialized,
                'ui_initialized': self._ui_initialized,
                'shutdown': self._shutdown
            }