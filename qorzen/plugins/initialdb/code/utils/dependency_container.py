from __future__ import annotations

"""
Dependency container for the InitialDB application.

This module provides a clean, type-safe dependency injection system to replace
the previous app_singleton_manager approach, preventing circular imports and
ensuring proper lifecycle management.
"""

import inspect
import logging
import threading
from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar, cast, get_type_hints

import structlog

T = TypeVar("T")
logger = structlog.get_logger(__name__)


class DependencyScope(Enum):
    """Defines the lifecycle scope of registered dependencies."""

    SINGLETON = "singleton"  # One instance per container
    TRANSIENT = "transient"  # New instance each time requested
    SCOPED = "scoped"  # One instance per scope (e.g., per session)


class DependencyRegistration(Generic[T]):
    """Registration information for a dependency."""

    def __init__(
            self,
            dependency_type: Type[T],
            factory: Callable[[], T],
            scope: DependencyScope,
    ) -> None:
        self.dependency_type = dependency_type
        self.factory = factory
        self.scope = scope
        self.instance: Optional[T] = None


class DependencyContainer:
    """Type-safe dependency container for managing application dependencies."""

    _instance: Optional[DependencyContainer] = None
    _lock = threading.RLock()

    @classmethod
    def instance(cls) -> "DependencyContainer":
        """Get the singleton instance of the dependency container."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = DependencyContainer()
            return cls._instance

    def __init__(self) -> None:
        """Initialize the dependency container."""
        self._registrations: Dict[Type[Any], DependencyRegistration[Any]] = {}
        self._instances: Dict[Type[Any], Any] = {}
        self._initializing: Dict[Type[Any], bool] = {}
        logger.info("Dependency container initialized")

    def register(
            self,
            dependency_type: Type[T],
            factory: Optional[Callable[[], T]] = None,
            scope: DependencyScope = DependencyScope.SINGLETON,
    ) -> None:
        """
        Register a dependency with the container.

        Args:
            dependency_type: The type of the dependency to register
            factory: Optional factory function to create the dependency
            scope: The lifecycle scope of the dependency
        """
        with self._lock:
            if dependency_type in self._registrations:
                logger.warning(f"Dependency {dependency_type.__name__} already registered, overwriting")

            if factory is None:
                # Use the constructor as the factory
                factory = dependency_type

            self._registrations[dependency_type] = DependencyRegistration(
                dependency_type=dependency_type,
                factory=factory,
                scope=scope,
            )
            print(f"Registering {dependency_type.__name__} with scope {scope.value}")
            logger.debug(f"Registered dependency: {dependency_type.__name__} with scope {scope.value}")

    def resolve(self, dependency_type: Type[T]) -> T:
        """
        Resolve a dependency by type.

        Args:
            dependency_type: The type of dependency to resolve

        Returns:
            An instance of the requested dependency

        Raises:
            KeyError: If the dependency is not registered
            RuntimeError: If there's a circular dependency detected
        """
        with self._lock:
            # Check if dependency is registered
            if dependency_type not in self._registrations:
                raise KeyError(f"Dependency {dependency_type.__name__} is not registered")

            registration = self._registrations[dependency_type]

            # For transient dependencies, always create a new instance
            if registration.scope == DependencyScope.TRANSIENT:
                return self._create_instance(registration)

            # For singleton dependencies, return existing instance or create a new one
            if dependency_type in self._instances:
                return cast(T, self._instances[dependency_type])

            # Detect circular dependencies
            if dependency_type in self._initializing:
                raise RuntimeError(
                    f"Circular dependency detected for {dependency_type.__name__}"
                )

            # Create new instance
            self._initializing[dependency_type] = True
            try:
                instance = self._create_instance(registration)
                self._instances[dependency_type] = instance
                return instance
            finally:
                self._initializing.pop(dependency_type, None)

    def _create_instance(self, registration: DependencyRegistration[T]) -> T:
        """
        Create a new instance using the factory function.

        Handles automatic dependency injection for constructor parameters.
        """
        factory = registration.factory
        if not callable(factory):
            raise TypeError(f"Factory for {registration.dependency_type.__name__} is not callable")

        if inspect.isclass(factory):
            # Auto-inject dependencies for class constructor
            sig = inspect.signature(factory.__init__)
            type_hints = get_type_hints(factory.__init__)
            args: Dict[str, Any] = {}

            for param_name, param in sig.parameters.items():
                # Skip self and params with default values
                if param_name == "self" or param.default != inspect.Parameter.empty:
                    continue

                param_type = type_hints.get(param_name)
                if param_type and param_type in self._registrations:
                    args[param_name] = self.resolve(param_type)

            return factory(**args)
        else:
            # Simple factory function without parameters
            return factory()

    def cleanup(self) -> None:
        """Clean up all dependencies with a cleanup method."""
        with self._lock:
            # Create a copy of the instances to avoid modification during iteration
            instances = list(self._instances.items())

            for dependency_type, instance in reversed(instances):
                try:
                    if hasattr(instance, "cleanup") and callable(instance.cleanup):
                        instance.cleanup()
                        logger.debug(f"Cleaned up {dependency_type.__name__}")
                    elif hasattr(instance, "dispose") and callable(instance.dispose):
                        instance.dispose()
                        logger.debug(f"Disposed {dependency_type.__name__}")
                    elif hasattr(instance, "close") and callable(instance.close):
                        instance.close()
                        logger.debug(f"Closed {dependency_type.__name__}")
                except Exception as e:
                    logger.error(f"Error cleaning up {dependency_type.__name__}: {e}")

            self._instances.clear()
            logger.info("All dependencies cleaned up")

    @property
    def is_initialized(self) -> bool:
        """Check if the container has been initialized."""
        return bool(self._registrations)


# Global convenience functions to access the container
def register(
        dependency_type: Type[T],
        factory: Optional[Callable[[], T]] = None,
        scope: DependencyScope = DependencyScope.SINGLETON,
) -> None:
    """Register a dependency with the global container."""
    DependencyContainer.instance().register(dependency_type, factory, scope)


def resolve(dependency_type: Type[T]) -> T:
    """Resolve a dependency from the global container."""
    return DependencyContainer.instance().resolve(dependency_type)


def cleanup() -> None:
    """Clean up all dependencies in the global container."""
    DependencyContainer.instance().cleanup()