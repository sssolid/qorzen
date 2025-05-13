from __future__ import annotations
import abc
import asyncio
import logging
from typing import Any, Dict, Optional, Protocol, TypeVar, runtime_checkable

T = TypeVar('T', bound='AsyncBaseManager')


@runtime_checkable
class BaseManager(Protocol):
    """Protocol defining basic async manager functionality."""

    async def initialize(self) -> None:
        """Initialize the manager asynchronously."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the manager asynchronously."""
        ...

    def status(self) -> Dict[str, Any]:
        """Return the current status of the manager."""
        ...


class QorzenManager(abc.ABC):
    """Base class for asynchronous managers in the Qorzen framework."""

    def __init__(self, name: str) -> None:
        """Initialize the async manager with a name.

        Args:
            name: The name of the manager
        """
        self._name: str = name
        self._initialized: bool = False
        self._healthy: bool = False
        self._logger: Optional[logging.Logger] = None

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the manager asynchronously.

        This method should be implemented by subclasses to perform
        initialization tasks like loading configuration, setting up
        connections, etc.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the manager asynchronously.

        This method should be implemented by subclasses to perform
        cleanup tasks like closing connections, releasing resources, etc.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        pass

    def status(self) -> Dict[str, Any]:
        """Get the current status of the manager.

        Returns:
            Dictionary containing status information
        """
        return {
            'name': self._name,
            'initialized': self._initialized,
            'healthy': self._healthy
        }

    @property
    def name(self) -> str:
        """Get the manager's name."""
        return self._name

    @property
    def initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized

    @property
    def healthy(self) -> bool:
        """Check if the manager is healthy."""
        return self._healthy

    def set_logger(self, logger: logging.Logger) -> None:
        """Set the logger for this manager.

        Args:
            logger: Logger instance to use
        """
        self._logger = logger