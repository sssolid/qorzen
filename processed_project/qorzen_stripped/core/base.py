from __future__ import annotations
import abc
import asyncio
import logging
from typing import Any, Dict, Optional, Protocol, TypeVar, runtime_checkable
T = TypeVar('T', bound='AsyncBaseManager')
@runtime_checkable
class BaseManager(Protocol):
    async def initialize(self) -> None:
        ...
    async def shutdown(self) -> None:
        ...
    def status(self) -> Dict[str, Any]:
        ...
class QorzenManager(abc.ABC):
    def __init__(self, name: str) -> None:
        self._name: str = name
        self._initialized: bool = False
        self._healthy: bool = False
        self._logger: Optional[logging.Logger] = None
    @abc.abstractmethod
    async def initialize(self) -> None:
        pass
    @abc.abstractmethod
    async def shutdown(self) -> None:
        pass
    def status(self) -> Dict[str, Any]:
        return {'name': self._name, 'initialized': self._initialized, 'healthy': self._healthy}
    @property
    def name(self) -> str:
        return self._name
    @property
    def initialized(self) -> bool:
        return self._initialized
    @property
    def healthy(self) -> bool:
        return self._healthy
    def set_logger(self, logger: logging.Logger) -> None:
        self._logger = logger