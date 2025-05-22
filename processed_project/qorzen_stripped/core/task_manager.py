from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, TaskError
T = TypeVar('T')
class TaskStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200
class TaskCategory(str, Enum):
    CORE = 'core'
    PLUGIN = 'plugin'
    UI = 'ui'
    IO = 'io'
    BACKGROUND = 'background'
    USER = 'user'
@dataclass
class TaskProgress:
    percent: int = 0
    message: str = ''
    updated_at: float = field(default_factory=time.time)
@dataclass
class TaskInfo:
    task_id: str
    name: str
    category: TaskCategory
    plugin_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    progress: TaskProgress = field(default_factory=TaskProgress)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cancellable: bool = True
class TaskManager(QorzenManager):
    def __init__(self, concurrency_manager: Any, event_bus_manager: Any, logger_manager: Any, config_manager: Any) -> None:
        super().__init__(name='task_manager')
        self._concurrency_manager = concurrency_manager
        self._event_bus_manager = event_bus_manager
        self._logger = logger_manager.get_logger('task_manager')
        self._config_manager = config_manager
        self._tasks: Dict[str, TaskInfo] = {}
        self._task_futures: Dict[str, asyncio.Task] = {}
        self._task_lock = asyncio.Lock()
        self._task_events: Dict[str, asyncio.Event] = {}
        self._max_concurrent_tasks = 20
        self._keep_completed_tasks = 100
        self._task_timeout = 300.0
    async def initialize(self) -> None:
        try:
            self._logger.info('Initializing task manager')
            tasks_config = await self._config_manager.get('tasks', {})
            if not tasks_config:
                self._logger.error('Tasks configuration not found in configuration')
            if not hasattr(tasks_config, 'max_concurrent_tasks'):
                self._logger.warning('Missing "max_concurrent_tasks" in "tasks" configuration')
            if not hasattr(tasks_config, 'keep_completed_tasks'):
                self._logger.warning('Missing "keep_completed_tasks" in "tasks" configuration')
            if not hasattr(tasks_config, 'default_timeout'):
                self._logger.warning('Missing "default_timeout" in "tasks" configuration')
            self._max_concurrent_tasks = tasks_config.get('max_concurrent_tasks', 20)
            self._keep_completed_tasks = tasks_config.get('keep_completed_tasks', 100)
            self._task_timeout = tasks_config.get('default_timeout', 300.0)
            await self._config_manager.register_listener('tasks', self._on_config_changed)
            self._initialized = True
            self._healthy = True
            self._logger.info('Task manager initialized successfully')
        except Exception as e:
            self._logger.error(f'Failed to initialize task manager: {str(e)}')
            raise ManagerInitializationError(f'Failed to initialize TaskManager: {str(e)}', manager_name=self.name) from e
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            self._logger.info('Shutting down task manager')
            self._shutting_down = True
            async with self._task_lock:
                running_tasks = [task_id for task_id, task_info in self._tasks.items() if task_info.status == TaskStatus.RUNNING and task_info.cancellable]
            for task_id in running_tasks:
                try:
                    try:
                        await asyncio.wait_for(self.cancel_task(task_id), timeout=1.0)
                    except asyncio.TimeoutError:
                        self._logger.warning(f'Timeout cancelling task {task_id} during shutdown')
                except Exception as e:
                    self._logger.warning(f'Error cancelling task {task_id} during shutdown: {e}')
            for task_id, future in list(self._task_futures.items()):
                if not future.done():
                    try:
                        self._logger.debug(f'Force cancelling task future {task_id}')
                        future.cancel()
                        try:
                            await asyncio.wait_for(asyncio.shield(asyncio.create_task(future)), timeout=0.5)
                        except (asyncio.TimeoutError, asyncio.CancelledError):
                            pass
                    except Exception as e:
                        self._logger.warning(f'Error cancelling future for task {task_id}: {e}')
            await self._config_manager.unregister_listener('tasks', self._on_config_changed)
            async with self._task_lock:
                self._tasks.clear()
            self._task_futures.clear()
            self._task_events.clear()
            self._initialized = False
            self._healthy = False
            self._logger.info('Task manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down task manager: {str(e)}')
            raise ManagerShutdownError(f'Failed to shut down TaskManager: {str(e)}', manager_name=self.name) from e
    async def submit_task(self, func: Callable[..., T], *args: Any, name: str='unnamed_task', category: TaskCategory=TaskCategory.CORE, plugin_id: Optional[str]=None, priority: TaskPriority=TaskPriority.NORMAL, metadata: Optional[Dict[str, Any]]=None, timeout: Optional[float]=None, cancellable: bool=True, **kwargs: Any) -> str:
        if not self._initialized:
            raise TaskError('Task manager not initialized')
        task_id = str(uuid.uuid4())
        task_info = TaskInfo(task_id=task_id, name=name, category=category, plugin_id=plugin_id, priority=priority, status=TaskStatus.PENDING, progress=TaskProgress(), created_at=time.time(), metadata=metadata or {}, cancellable=cancellable)
        async with self._task_lock:
            running_count = sum((1 for info in self._tasks.values() if info.status == TaskStatus.RUNNING))
            if running_count >= self._max_concurrent_tasks:
                raise TaskError(f'Too many concurrent tasks ({running_count} >= {self._max_concurrent_tasks})')
            self._tasks[task_id] = task_info
        progress_reporter = self._create_progress_reporter(task_id)
        is_async = asyncio.iscoroutinefunction(func)
        self._task_events[task_id] = asyncio.Event()
        task_future = asyncio.create_task(self._execute_task(task_id=task_id, func=func, args=args, kwargs={**kwargs, 'progress_reporter': progress_reporter} if 'progress_reporter' in kwargs else kwargs, is_async=is_async, timeout=timeout or self._task_timeout), name=f'task_{task_id}')
        self._task_futures[task_id] = task_future
        await self._publish_task_event('task/submitted', task_id, task_info)
        return task_id
    async def submit_async_task(self, func: Callable[..., T], *args: Any, name: str='unnamed_async_task', category: TaskCategory=TaskCategory.CORE, plugin_id: Optional[str]=None, priority: TaskPriority=TaskPriority.NORMAL, metadata: Optional[Dict[str, Any]]=None, timeout: Optional[float]=None, cancellable: bool=True, **kwargs: Any) -> str:
        if not asyncio.iscoroutinefunction(func):
            raise TaskError('Function must be asynchronous (use "async def")')
        return await self.submit_task(*args, func=func, name=name, category=category, plugin_id=plugin_id, priority=priority, metadata=metadata, timeout=timeout, cancellable=cancellable, **kwargs)
    async def cancel_task(self, task_id: str) -> bool:
        if not self._initialized:
            raise TaskError('Task manager not initialized')
        async with self._task_lock:
            if task_id not in self._tasks:
                raise TaskError(f'Task {task_id} not found')
            task_info = self._tasks[task_id]
            if task_info.status != TaskStatus.RUNNING:
                self._logger.debug(f'Task {task_id} is not running (status: {task_info.status})')
                return False
            if not task_info.cancellable:
                raise TaskError(f'Task {task_id} cannot be cancelled')
        future = self._task_futures.get(task_id)
        if future and (not future.done()):
            future.cancel()
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = time.time()
            event = self._task_events.get(task_id)
            if event:
                event.set()
            await self._publish_task_event('task/cancelled', task_id, task_info)
            self._logger.info(f'Task {task_id} ({task_info.name}) cancelled')
            return True
        return False
    async def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        async with self._task_lock:
            return self._tasks.get(task_id)
    async def get_tasks(self, status: Optional[Union[TaskStatus, List[TaskStatus]]]=None, category: Optional[Union[TaskCategory, List[TaskCategory]]]=None, plugin_id: Optional[str]=None, limit: int=100) -> List[TaskInfo]:
        async with self._task_lock:
            status_list = [status] if isinstance(status, TaskStatus) else status if status else None
            category_list = [category] if isinstance(category, TaskCategory) else category if category else None
            filtered_tasks = []
            for task_info in self._tasks.values():
                if status_list and task_info.status not in status_list:
                    continue
                if category_list and task_info.category not in category_list:
                    continue
                if plugin_id and task_info.plugin_id != plugin_id:
                    continue
                filtered_tasks.append(task_info)
            filtered_tasks.sort(key=lambda t: (-t.priority.value, t.created_at))
            return filtered_tasks[:limit]
    async def wait_for_task(self, task_id: str, timeout: Optional[float]=None) -> TaskInfo:
        if not self._initialized:
            raise TaskError('Task manager not initialized')
        task_info = await self.get_task_info(task_id)
        if not task_info:
            raise TaskError(f'Task {task_id} not found')
        if task_info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return task_info
        event = self._task_events.get(task_id)
        if not event:
            raise TaskError(f'Task event for {task_id} not found')
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TaskError(f'Timeout waiting for task {task_id}')
        updated_task_info = await self.get_task_info(task_id)
        if not updated_task_info:
            raise TaskError(f'Task {task_id} not found after completion')
        return updated_task_info
    async def _execute_task(self, task_id: str, func: Callable, args: tuple, kwargs: dict, is_async: bool, timeout: float) -> Any:
        async with self._task_lock:
            task_info = self._tasks[task_id]
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = time.time()
        await self._publish_task_event('task/started', task_id, task_info)
        try:
            if is_async:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                result = await asyncio.wait_for(self._concurrency_manager.run_in_thread(func, *args, **kwargs), timeout=timeout)
            async with self._task_lock:
                task_info = self._tasks[task_id]
                task_info.status = TaskStatus.COMPLETED
                task_info.completed_at = time.time()
                task_info.result = result
            await self._publish_task_event('task/completed', task_id, task_info)
            return result
        except asyncio.CancelledError:
            async with self._task_lock:
                task_info = self._tasks[task_id]
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = time.time()
            await self._publish_task_event('task/cancelled', task_id, task_info)
            raise
        except asyncio.TimeoutError:
            async with self._task_lock:
                task_info = self._tasks[task_id]
                task_info.status = TaskStatus.FAILED
                task_info.completed_at = time.time()
                task_info.error = f'Task timed out after {timeout} seconds'
            await self._publish_task_event('task/failed', task_id, task_info)
            self._logger.warning(f'Task {task_id} ({task_info.name}) timed out after {timeout} seconds')
            raise TaskError(f'Task {task_id} timed out')
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            async with self._task_lock:
                task_info = self._tasks[task_id]
                task_info.status = TaskStatus.FAILED
                task_info.completed_at = time.time()
                task_info.error = str(e)
                task_info.traceback = tb_str
            await self._publish_task_event('task/failed', task_id, task_info)
            self._logger.error(f'Task {task_id} ({task_info.name}) failed: {str(e)}', extra={'task_id': task_id, 'error': str(e), 'traceback': tb_str})
            raise TaskError(f'Task {task_id} failed: {str(e)}') from e
        finally:
            if task_id in self._task_futures:
                del self._task_futures[task_id]
            event = self._task_events.get(task_id)
            if event:
                event.set()
            asyncio.create_task(self._cleanup_tasks())
    async def _cleanup_tasks(self) -> None:
        async with self._task_lock:
            completed_tasks = [task_id for task_id, task_info in self._tasks.items() if task_info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)]
            if len(completed_tasks) > self._keep_completed_tasks:
                completed_tasks.sort(key=lambda task_id: self._tasks[task_id].completed_at or 0)
                to_remove = completed_tasks[:-self._keep_completed_tasks]
                for task_id in to_remove:
                    del self._tasks[task_id]
                    if task_id in self._task_events:
                        del self._task_events[task_id]
                self._logger.debug(f'Cleaned up {len(to_remove)} completed tasks')
    def _create_progress_reporter(self, task_id: str) -> Any:
        class ProgressReporter:
            def __init__(self, task_id: str, manager: TaskManager):
                self.task_id = task_id
                self.manager = manager
            async def report_progress(self, percent: int, message: str='') -> None:
                await self.manager._update_task_progress(self.task_id, percent, message)
            def report(self, percent: int, message: str='') -> None:
                asyncio.create_task(self.report_progress(percent, message))
        return ProgressReporter(task_id, self)
    async def _update_task_progress(self, task_id: str, percent: int, message: str) -> None:
        if not self._initialized or task_id not in self._tasks:
            return
        percent = max(0, min(100, percent))
        async with self._task_lock:
            task_info = self._tasks.get(task_id)
            if not task_info or task_info.status != TaskStatus.RUNNING:
                return
            task_info.progress = TaskProgress(percent=percent, message=message, updated_at=time.time())
        await self._publish_task_event('task/progress', task_id, task_info)
    async def _publish_task_event(self, event_type: str, task_id: str, task_info: TaskInfo) -> None:
        if not self._event_bus_manager or not hasattr(self._event_bus_manager, 'publish'):
            return
        payload = {'task_id': task_id, 'name': task_info.name, 'category': task_info.category.value, 'plugin_id': task_info.plugin_id, 'status': task_info.status.value, 'progress': {'percent': task_info.progress.percent, 'message': task_info.progress.message}}
        if task_info.started_at:
            payload['started_at'] = task_info.started_at
        if task_info.completed_at:
            payload['completed_at'] = task_info.completed_at
            payload['duration'] = task_info.completed_at - (task_info.started_at or task_info.created_at)
        if task_info.status == TaskStatus.FAILED and task_info.error:
            payload['error'] = task_info.error
        if task_info.status == TaskStatus.COMPLETED and task_info.result is not None:
            try:
                result_str = str(task_info.result)
                if len(result_str) <= 1024:
                    payload['result'] = task_info.result
            except Exception:
                pass
        await self._event_bus_manager.publish(event_type=event_type, source='task_manager', payload=payload)
    def _on_config_changed(self, key: str, value: Any) -> None:
        if key == 'tasks.max_concurrent_tasks':
            self._max_concurrent_tasks = int(value)
            self._logger.info(f'Updated max concurrent tasks to {self._max_concurrent_tasks}')
        elif key == 'tasks.keep_completed_tasks':
            self._keep_completed_tasks = int(value)
            self._logger.info(f'Updated keep completed tasks to {self._keep_completed_tasks}')
        elif key == 'tasks.default_timeout':
            self._task_timeout = float(value)
            self._logger.info(f'Updated default task timeout to {self._task_timeout}')
    def status(self) -> Dict[str, Any]:
        status = super().status()
        if self._initialized:
            status_counts = {status.value: 0 for status in TaskStatus}
            category_counts = {category.value: 0 for category in TaskCategory}
            plugin_tasks = set()
            for task_info in self._tasks.values():
                status_counts[task_info.status.value] += 1
                category_counts[task_info.category.value] += 1
                if task_info.plugin_id:
                    plugin_tasks.add(task_info.plugin_id)
            status.update({'tasks': {'total': len(self._tasks), 'by_status': status_counts, 'by_category': category_counts, 'plugins_with_tasks': len(plugin_tasks)}, 'config': {'max_concurrent_tasks': self._max_concurrent_tasks, 'keep_completed_tasks': self._keep_completed_tasks, 'default_timeout': self._task_timeout}})
        return status