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
    """Task priority levels."""
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


class ConcurrencyManager(QorzenManager):
    """Manager for hybrid concurrency (async + threads).

    This manager provides a unified interface for running tasks
    using both async/await and thread-based concurrency.
    """

    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        """Initialize the concurrency manager.

        Args:
            config_manager: Configuration manager
            logger_manager: Logger manager
        """
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
        """Initialize the concurrency manager.

        Sets up thread pools and process pools based on configuration.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            thread_config = self._config_manager.get('thread_pool', {})
            self._max_workers = thread_config.get('worker_threads', 4)
            self._max_io_workers = thread_config.get('io_threads', 8)
            self._max_process_workers = thread_config.get('process_workers', max(1, (os.cpu_count() or 2) - 1))
            self._thread_name_prefix = thread_config.get('thread_name_prefix', 'qorzen-worker')

            # Create thread pools
            self._thread_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix=f"{self._thread_name_prefix}-cpu-"
            )

            self._io_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._max_io_workers,
                thread_name_prefix=f"{self._thread_name_prefix}-io-"
            )

            # Create process pool if enabled
            if thread_config.get('enable_process_pool', True):
                self._process_pool = concurrent.futures.ProcessPoolExecutor(
                    max_workers=self._max_process_workers
                )

            # Store the main thread's event loop
            self._main_thread_loop = asyncio.get_running_loop()

            self._config_manager.register_listener('thread_pool', self._on_config_changed)
            self._logger.info(f'Concurrency Manager initialized with {self._max_workers} workers')
            self._initialized = True
            self._healthy = True
        except Exception as e:
            self._logger.error(f'Failed to initialize Concurrency Manager: {str(e)}')
            raise ManagerInitializationError(f'Failed to initialize ConcurrencyManager: {str(e)}',
                                             manager_name=self.name) from e

    async def shutdown(self) -> None:
        """Shutdown the concurrency manager.

        Gracefully shuts down thread pools and process pools.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Concurrency Manager')

            # Shutdown thread pools
            if self._thread_pool:
                self._thread_pool.shutdown(wait=True, cancel_futures=True)

            if self._io_pool:
                self._io_pool.shutdown(wait=True, cancel_futures=True)

            # Shutdown process pool
            if self._process_pool:
                self._process_pool.shutdown(wait=True)

            self._config_manager.unregister_listener('thread_pool', self._on_config_changed)
            self._initialized = False
            self._healthy = False
            self._logger.info('Concurrency Manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down Concurrency Manager: {str(e)}')
            raise ManagerShutdownError(f'Failed to shut down ConcurrencyManager: {str(e)}',
                                       manager_name=self.name) from e

    def is_main_thread(self) -> bool:
        """Check if the current thread is the main thread.

        Returns:
            True if the current thread is the main thread, False otherwise
        """
        return threading.get_ident() == self._main_thread_id

    async def run_in_thread(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run a function in a worker thread.

        This is suitable for CPU-bound tasks that would block the event loop.

        Args:
            func: The function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ThreadManagerError: If the thread execution fails
        """
        if not self._initialized or not self._thread_pool:
            raise ThreadManagerError('Concurrency Manager not initialized', thread_id=None)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._thread_pool,
            functools.partial(func, *args, **kwargs)
        )

    async def run_io_task(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run an I/O-bound function in a dedicated I/O thread pool.

        This is suitable for I/O operations like file access, network calls, etc.

        Args:
            func: The function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ThreadManagerError: If the thread execution fails
        """
        if not self._initialized or not self._io_pool:
            raise ThreadManagerError('Concurrency Manager not initialized', thread_id=None)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._io_pool,
            functools.partial(func, *args, **kwargs)
        )

    async def run_in_process(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run a function in a separate process.

        This is suitable for CPU-intensive tasks that can be parallelized.

        Args:
            func: The function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ThreadManagerError: If the process execution fails
        """
        if not self._initialized or not self._process_pool:
            raise ThreadManagerError('Process pool not available', thread_id=None)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._process_pool,
            functools.partial(func, *args, **kwargs)
        )

    async def run_on_main_thread(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run a function on the main thread.

        This is essential for UI operations that must run on the main/UI thread.

        Args:
            func: The function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ThreadManagerError: If the execution fails
        """
        if not self._initialized or not self._main_thread_loop:
            raise ThreadManagerError('Concurrency Manager not initialized', thread_id=None)

        if self.is_main_thread():
            # Already on the main thread, just call the function
            return func(*args, **kwargs)
        else:
            # Use a Future to get the result from the main thread
            future = concurrent.futures.Future()

            def main_thread_wrapper():
                try:
                    result = func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)

            # Schedule the execution on the main thread's event loop
            self._main_thread_loop.call_soon_threadsafe(main_thread_wrapper)

            # Wait for the result
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, future.result)

    def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: The configuration key that changed
            value: The new value
        """
        if key == 'thread_pool.worker_threads':
            self._logger.warning('Thread pool size changes require restart to take effect',
                                 extra={'current_size': self._max_workers, 'new_size': value})
        elif key == 'thread_pool.io_threads':
            self._logger.warning('IO thread pool size changes require restart to take effect',
                                 extra={'current_size': self._max_io_workers, 'new_size': value})
        elif key == 'thread_pool.process_workers':
            self._logger.warning('Process pool size changes require restart to take effect',
                                 extra={'current_size': self._max_process_workers, 'new_size': value})

    def status(self) -> Dict[str, Any]:
        """Get the status of the concurrency manager.

        Returns:
            Dictionary containing status information
        """
        status = super().status()
        if self._initialized:
            thread_pool_status = {
                'max_workers': self._max_workers,
                'is_main_thread': self.is_main_thread(),
                'io_workers': self._max_io_workers,
                'process_workers': self._max_process_workers if self._process_pool else 0,
                'process_pool_enabled': self._process_pool is not None
            }

            status.update({
                'thread_pool': thread_pool_status
            })
        return status