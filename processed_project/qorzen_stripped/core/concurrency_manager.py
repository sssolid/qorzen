from __future__ import annotations
import asyncio
import concurrent.futures
import functools
import logging
import os
import threading
import traceback
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, ThreadManagerError
T = TypeVar('T')
R = TypeVar('R')
class TaskPriority(int):
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200
class ConcurrencyManager(QorzenManager):
    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        super().__init__(name='concurrency_manager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('concurrency_manager')
        self._thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._process_pool: Optional[concurrent.futures.ProcessPoolExecutor] = None
        self._io_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._main_thread_id: int = threading.get_ident()
        self._main_thread_loop: Optional[asyncio.AbstractEventLoop] = None
        self._max_workers: int = 4
        self._max_io_workers: int = 8
        self._max_process_workers: int = 2
        self._thread_name_prefix: str = 'qorzen-worker'
    async def initialize(self) -> None:
        try:
            thread_config = await self._config_manager.get('thread_pool', {})
            self._max_workers = await self._config_manager.get('thread_pool.worker_threads', 4)
            self._max_io_workers = await self._config_manager.get('thread_pool.io_threads', 8)
            self._max_process_workers = await self._config_manager.get('thread_pool.process_workers', 2)
            self._thread_name_prefix = thread_config.get('thread_name_prefix', 'qorzen-worker')
            self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix=f'{self._thread_name_prefix}-cpu-')
            self._io_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self._max_io_workers, thread_name_prefix=f'{self._thread_name_prefix}-io-')
            if thread_config.get('enable_process_pool', True):
                self._process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=self._max_process_workers)
            self._main_thread_loop = asyncio.get_running_loop()
            await self._config_manager.register_listener('thread_pool', self._on_config_changed)
            self._logger.info(f'Concurrency Manager initialized with {self._max_workers} workers')
            self._initialized = True
            self._healthy = True
        except Exception as e:
            self._logger.error(f'Failed to initialize Concurrency Manager: {str(e)}')
            raise ManagerInitializationError(f'Failed to initialize ConcurrencyManager: {str(e)}', manager_name=self.name) from e
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            self._logger.info('Shutting down Concurrency Manager')
            if self._thread_pool:
                self._thread_pool.shutdown(wait=True, cancel_futures=True)
            if self._io_pool:
                self._io_pool.shutdown(wait=True, cancel_futures=True)
            if self._process_pool:
                self._process_pool.shutdown(wait=True)
            await self._config_manager.unregister_listener('thread_pool', self._on_config_changed)
            self._initialized = False
            self._healthy = False
            self._logger.info('Concurrency Manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down Concurrency Manager: {str(e)}')
            raise ManagerShutdownError(f'Failed to shut down ConcurrencyManager: {str(e)}', manager_name=self.name) from e
    def is_main_thread(self) -> bool:
        return threading.get_ident() == self._main_thread_id
    async def run_in_thread(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        if not self._initialized or not self._thread_pool:
            raise ThreadManagerError('Concurrency Manager not initialized', thread_id=None)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._thread_pool, functools.partial(func, *args, **kwargs))
    async def run_io_task(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        if not self._initialized or not self._io_pool:
            raise ThreadManagerError('Concurrency Manager not initialized', thread_id=None)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._io_pool, functools.partial(func, *args, **kwargs))
    async def run_in_process(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        if not self._initialized or not self._process_pool:
            raise ThreadManagerError('Process pool not available', thread_id=None)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._process_pool, functools.partial(func, *args, **kwargs))
    async def run_on_main_thread(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        if not self._initialized or not self._main_thread_loop:
            raise ThreadManagerError('Concurrency Manager not initialized', thread_id=None)
        if self.is_main_thread():
            return func(*args, **kwargs)
        else:
            future = concurrent.futures.Future()
            def main_thread_wrapper():
                try:
                    result = func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
            self._main_thread_loop.call_soon_threadsafe(main_thread_wrapper)
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, future.result)
    def _on_config_changed(self, key: str, value: Any) -> None:
        if key == 'thread_pool.worker_threads':
            self._logger.warning('Thread pool size changes require restart to take effect', extra={'current_size': self._max_workers, 'new_size': value})
        elif key == 'thread_pool.io_threads':
            self._logger.warning('IO thread pool size changes require restart to take effect', extra={'current_size': self._max_io_workers, 'new_size': value})
        elif key == 'thread_pool.process_workers':
            self._logger.warning('Process pool size changes require restart to take effect', extra={'current_size': self._max_process_workers, 'new_size': value})
    def status(self) -> Dict[str, Any]:
        status = super().status()
        if self._initialized:
            thread_pool_status = {'max_workers': self._max_workers, 'is_main_thread': self.is_main_thread(), 'io_workers': self._max_io_workers, 'process_workers': self._max_process_workers if self._process_pool else 0, 'process_pool_enabled': self._process_pool is not None}
            status.update({'thread_pool': thread_pool_status})
        return status