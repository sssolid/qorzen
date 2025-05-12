from __future__ import annotations

import abc
import threading
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypeVar, Generic, TYPE_CHECKING, Set, \
    Callable

from PySide6.QtCore import QObject, Signal

from qorzen.core.service_locator import ServiceLocator, ManagerType, inject

if TYPE_CHECKING:
    from qorzen.ui.integration import UIIntegration
    from qorzen.core import TaskManager, RemoteServicesManager, SecurityManager, APIManager, CloudManager, \
        LoggingManager, ConfigManager, DatabaseManager, EventBusManager, FileManager, ThreadManager


@runtime_checkable
class PluginInterface(Protocol):
    """Protocol defining the interface that all plugins must implement."""

    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]

    def initialize(self, service_locator: ServiceLocator, **kwargs: Any) -> None:
        """
        Initialize the plugin with the service locator.

        Args:
            service_locator: Provides access to all system services
            **kwargs: Additional initialization parameters
        """
        ...

    def on_ui_ready(self, ui_integration: 'UIIntegration') -> None:
        """
        Called when the UI is ready for plugin integration.

        Args:
            ui_integration: UI integration interface for the plugin
        """
        ...

    def shutdown(self) -> None:
        """Perform cleanup operations before plugin is unloaded."""
        ...


class BasePlugin(QObject):
    """Base class for Qorzen plugins with common functionality."""

    name: str = 'base_plugin'
    version: str = '0.0.0'
    description: str = 'Base plugin'
    author: str = 'Unknown'
    display_name: Optional[str] = None
    dependencies: List[str] = []

    # Signals
    initialized = Signal()
    ui_ready = Signal()
    shutdown_started = Signal()
    shutdown_completed = Signal()

    def __init__(self) -> None:
        """Initialize the plugin base."""
        super().__init__()
        self._initialized = False
        self._ui_initialized = False
        self._shutdown = False
        self._lock = threading.RLock()

        # Services - will be initialized later
        self._service_locator: Optional[ServiceLocator] = None
        self._event_bus: Optional['EventBusManager'] = None
        self._logger: Optional[Any] = None
        self._config: Optional['ConfigManager'] = None
        self._file_manager: Optional['FileManager'] = None
        self._thread_manager: Optional['ThreadManager'] = None
        self._database_manager: Optional['DatabaseManager'] = None
        self._remote_service_manager: Optional['RemoteServicesManager'] = None
        self._security_manager: Optional['SecurityManager'] = None
        self._api_manager: Optional['APIManager'] = None
        self._cloud_manager: Optional['CloudManager'] = None
        self._task_manager: Optional['TaskManager'] = None

        self._registered_tasks: Set[str] = set()
        self._ui_registry = None

    def initialize(self, service_locator: ServiceLocator, **kwargs: Any) -> None:
        """
        Initialize the plugin with services from the service locator.

        Args:
            service_locator: Service locator containing all system services
            **kwargs: Additional initialization parameters
        """
        with self._lock:
            if self._initialized:
                return

            self._service_locator = service_locator

            # Get essential services
            try:
                self._event_bus = service_locator.get(ManagerType.EVENT_BUS)

                logger_provider = service_locator.get(ManagerType.LOGGING)
                if logger_provider:
                    self._logger = logger_provider.get_logger(self.name)

                self._config = service_locator.get(ManagerType.CONFIG)
                self._file_manager = service_locator.get(ManagerType.FILE)
                self._thread_manager = service_locator.get(ManagerType.THREAD)
                self._database_manager = service_locator.get(ManagerType.DATABASE)
                self._remote_service_manager = service_locator.get(ManagerType.REMOTE_SERVICES)
                self._security_manager = service_locator.get(ManagerType.SECURITY)
                self._api_manager = service_locator.get(ManagerType.API)
                self._cloud_manager = service_locator.get(ManagerType.CLOUD)
                self._task_manager = service_locator.get(ManagerType.TASK)

            except KeyError as e:
                if self._logger:
                    self._logger.warning(f"Could not find required service: {e}")

            # Get application core from kwargs
            self._application_core = kwargs.get('application_core')

            # Initialize UI registry with thread manager
            from qorzen.plugin_system.ui_registry import UIComponentRegistry
            self._ui_registry = UIComponentRegistry(self.name, thread_manager=self._thread_manager)

            self._initialized = True

        self.initialized.emit()

    def on_ui_ready(self, ui_integration: 'UIIntegration') -> None:
        """
        Called when the UI is ready for plugin integration.

        Args:
            ui_integration: UI integration interface for the plugin
        """
        with self._lock:
            self._ui_initialized = True
        self.ui_ready.emit()

    def register_task(self, task_name: str, function: Callable, **properties: Any) -> None:
        """
        Register a task with the task manager.

        Args:
            task_name: Name of the task
            function: Function to execute
            **properties: Task properties
        """
        if not self._task_manager:
            if self._logger:
                self._logger.warning(f"Task manager not available, can't register task {task_name}")
            return

        self._task_manager.register_task(self.name, task_name, function, **properties)
        self._registered_tasks.add(task_name)

        if self._logger:
            self._logger.debug(f'Registered task: {task_name}')

    def execute_task(self, task_name: str, *args: Any, **kwargs: Any) -> Optional[str]:
        """
        Execute a registered task.

        Args:
            task_name: Name of the task to execute
            *args: Arguments for the task
            **kwargs: Keyword arguments for the task

        Returns:
            Task ID if successful, None otherwise
        """
        if not self._task_manager:
            if self._logger:
                self._logger.warning(f"Task manager not available, can't execute task {task_name}")
            return None

        if task_name not in self._registered_tasks:
            if self._logger:
                self._logger.warning(f'Task not registered: {task_name}')
            return None

        return self._task_manager.execute_task(self.name, task_name, *args, **kwargs)

    def register_ui_component(self, component: Any, component_type: str = 'widget') -> Any:
        """
        Register a UI component with the UI registry.

        Args:
            component: UI component to register
            component_type: Type of component

        Returns:
            Registered component
        """
        if self._ui_registry:
            return self._ui_registry.register(component, component_type)
        return component

    def get_registered_tasks(self) -> Set[str]:
        """
        Get the set of registered task names.

        Returns:
            Set of registered task names
        """
        return self._registered_tasks.copy()

    def shutdown(self) -> None:
        """Perform cleanup operations before plugin is unloaded."""
        with self._lock:
            if self._shutdown:
                return

            self._shutdown = True
            self.shutdown_started.emit()

            if self._ui_registry:
                self._ui_registry.cleanup()

            self._registered_tasks.clear()
            self._initialized = False
            self._ui_initialized = False

        self.shutdown_completed.emit()

    def status(self) -> Dict[str, Any]:
        """
        Get the current status of the plugin.

        Returns:
            Dictionary with plugin status information
        """
        with self._lock:
            return {
                'name': self.name,
                'version': self.version,
                'description': self.description,
                'initialized': self._initialized,
                'ui_initialized': self._ui_initialized,
                'shutdown': self._shutdown
            }