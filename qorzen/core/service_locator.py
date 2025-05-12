from __future__ import annotations

import functools
import inspect
import threading
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast, get_type_hints

T = TypeVar("T")


class ManagerType(Enum):
    """Enumeration of different manager types available in the system."""
    CONFIG = auto()
    LOGGING = auto()
    EVENT_BUS = auto()
    THREAD = auto()
    FILE = auto()
    DATABASE = auto()
    REMOTE_SERVICES = auto()
    SECURITY = auto()
    API = auto()
    CLOUD = auto()
    TASK = auto()
    MONITORING = auto()
    PLUGIN = auto()


class ServiceLocator:
    """
    Service locator pattern implementation for Qorzen managers.

    This class provides a centralized way to access different managers
    without direct dependencies, making the system more modular and easier
    to maintain.
    """

    def __init__(self) -> None:
        """Initialize an empty service locator."""
        self._services: Dict[ManagerType, Any] = {}
        self._services_by_name: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def register(self, manager_type: ManagerType, service: Any, name: Optional[str] = None) -> None:
        """
        Register a service with the locator.

        Args:
            manager_type: The type of manager being registered
            service: The service instance to register
            name: Optional name for the service for string-based lookups
        """
        with self._lock:
            self._services[manager_type] = service
            if name:
                self._services_by_name[name] = service

    def get(self, manager_type: ManagerType) -> Any:
        """
        Get a service by its manager type.

        Args:
            manager_type: The type of manager to retrieve

        Returns:
            The requested service instance

        Raises:
            KeyError: If the requested service is not registered
        """
        with self._lock:
            return self._services[manager_type]

    def get_by_name(self, name: str) -> Any:
        """
        Get a service by its registered name.

        Args:
            name: The name of the service to retrieve

        Returns:
            The requested service instance

        Raises:
            KeyError: If the requested service is not registered
        """
        with self._lock:
            return self._services_by_name[name]

    def get_all(self) -> Dict[str, Any]:
        """
        Get all registered services by their names.

        Returns:
            Dictionary of all services with their names as keys
        """
        with self._lock:
            return self._services_by_name.copy()


# Global instance used as default
_default_locator: Optional[ServiceLocator] = None
_locator_lock = threading.RLock()


def get_default_locator() -> ServiceLocator:
    """
    Get the default global ServiceLocator instance.

    Returns:
        The default ServiceLocator instance
    """
    global _default_locator
    with _locator_lock:
        if _default_locator is None:
            _default_locator = ServiceLocator()
        return _default_locator


def inject(*manager_types: ManagerType, locator: Optional[ServiceLocator] = None) -> Callable:
    """
    Decorator to inject manager dependencies into functions or methods.

    Args:
        *manager_types: ManagerType enums to inject
        locator: Optional custom locator to use (uses default if None)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal locator
            if locator is None:
                locator = get_default_locator()

            # Get type annotations to match managers to parameter names
            type_hints = get_type_hints(func)
            param_names = list(inspect.signature(func).parameters.keys())

            # Add manager instances to kwargs if not already provided
            for manager_type in manager_types:
                try:
                    service = locator.get(manager_type)

                    # Find parameter that would accept this service
                    service_type = type(service)
                    for param_name, hint_type in type_hints.items():
                        if param_name in kwargs:
                            continue  # Already provided

                        # Check if parameter would accept this service
                        try:
                            if param_name in param_names and issubclass(service_type, hint_type):
                                kwargs[param_name] = service
                                break
                        except TypeError:
                            # Not a class type, skip
                            pass

                except (KeyError, TypeError):
                    # Service not available, continue
                    pass

            return func(*args, **kwargs)

        return wrapper

    return decorator