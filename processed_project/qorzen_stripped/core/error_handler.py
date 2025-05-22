from __future__ import annotations
import asyncio
import inspect
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast
from qorzen.utils import EventBusError
T = TypeVar('T')
class ErrorSeverity(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'
@dataclass
class ErrorInfo:
    error_id: str
    message: str
    source: str
    severity: ErrorSeverity
    plugin_id: Optional[str] = None
    component: Optional[str] = None
    traceback: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    handled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
class ErrorBoundary:
    def __init__(self, error_handler: Any, source: str, plugin_id: Optional[str]=None, component: Optional[str]=None) -> None:
        self._error_handler = error_handler
        self._source = source
        self._plugin_id = plugin_id
        self._component = component
    async def run(self, func: Callable[..., T], *args: Any, severity: ErrorSeverity=ErrorSeverity.MEDIUM, **kwargs: Any) -> Optional[T]:
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            tb = traceback.format_exc()
            handled = await self._error_handler.handle_error(message=str(e), source=self._source, severity=severity, plugin_id=self._plugin_id, component=self._component, traceback=tb)
            if not handled:
                raise
            return None
    def wrap(self, severity: ErrorSeverity=ErrorSeverity.MEDIUM) -> Callable[[Callable[..., T]], Callable[..., T]]:
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                return await self.run(func, *args, severity=severity, **kwargs)
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                return self.run(func, *args, severity=severity, **kwargs)
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        return decorator
class ErrorHandler:
    def __init__(self, event_bus_manager: Any, logger_manager: Any, config_manager: Optional[Any]=None) -> None:
        self._event_bus_manager = event_bus_manager
        self._logger = logger_manager.get_logger('error_handler')
        self._config_manager = config_manager
        self._errors: Dict[str, ErrorInfo] = {}
        self._error_subscribers: List[Callable[[ErrorInfo], Any]] = []
        self._error_strategies: Dict[str, Callable[[ErrorInfo], bool]] = {}
        self._error_lock = asyncio.Lock()
        self._max_errors = 1000
        self._default_severity_handling = {ErrorSeverity.LOW: True, ErrorSeverity.MEDIUM: True, ErrorSeverity.HIGH: False, ErrorSeverity.CRITICAL: False}
    async def initialize(self) -> None:
        if self._config_manager:
            error_config = await self._config_manager.get('error_handling', {})
            if not error_config:
                self._logger.error('Error Handler configuration not found in configuration')
            if not hasattr(error_config, 'max_errors'):
                self._logger.warning('Error Handler configuration max_errors not found in configuration')
            if not hasattr(error_config, 'handle_low'):
                self._logger.warning('Error Handler configuration handle_low not found in configuration')
            if not hasattr(error_config, 'handle_medium'):
                self._logger.warning('Error Handler configuration handle_medium not found in configuration')
            if not hasattr(error_config, 'handle_high'):
                self._logger.warning('Error Handler configuration handle_high not found in configuration')
            if not hasattr(error_config, 'handle_critical'):
                self._logger.warning('Error Handler configuration handle_critical not found in configuration')
            self._max_errors = error_config.get('max_errors', 1000)
            self._default_severity_handling = {ErrorSeverity.LOW: error_config.get('handle_low', True), ErrorSeverity.MEDIUM: error_config.get('handle_medium', True), ErrorSeverity.HIGH: error_config.get('handle_high', False), ErrorSeverity.CRITICAL: error_config.get('handle_critical', False)}
    async def handle_error(self, message: str, source: str, severity: ErrorSeverity=ErrorSeverity.MEDIUM, plugin_id: Optional[str]=None, component: Optional[str]=None, traceback: Optional[str]=None, metadata: Optional[Dict[str, Any]]=None) -> bool:
        error_id = str(uuid.uuid4())
        error_info = ErrorInfo(error_id=error_id, message=message, source=source, severity=severity, plugin_id=plugin_id, component=component, traceback=traceback, metadata=metadata or {})
        log_level = {ErrorSeverity.LOW: 'warning', ErrorSeverity.MEDIUM: 'warning', ErrorSeverity.HIGH: 'error', ErrorSeverity.CRITICAL: 'critical'}.get(severity, 'error')
        log_func = getattr(self._logger, log_level)
        source_str = f'{source}' + (f':{plugin_id}' if plugin_id else '')
        if component:
            source_str += f':{component}'
        log_func(f'Error in {source_str}: {message}', extra={'error_id': error_id, 'source': source, 'severity': severity, 'plugin_id': plugin_id, 'component': component})
        if traceback:
            self._logger.debug(f'Traceback for error {error_id}:\n{traceback}')
        async with self._error_lock:
            if len(self._errors) >= self._max_errors:
                error_ids = list(self._errors.keys())
                error_ids.sort(key=lambda eid: self._errors[eid].timestamp)
                to_remove = error_ids[:max(1, len(error_ids) // 10)]
                for eid in to_remove:
                    del self._errors[eid]
            self._errors[error_id] = error_info
        strategy_key = f'{source}:{plugin_id}:{component}' if component else f'{source}:{plugin_id}' if plugin_id else source
        strategy = self._error_strategies.get(strategy_key)
        if strategy:
            should_handle = strategy(error_info)
            error_info.handled = should_handle
        else:
            should_handle = self._default_severity_handling.get(severity, False)
            error_info.handled = should_handle
        await self._publish_error_event(error_info)
        for subscriber in self._error_subscribers:
            try:
                result = subscriber(error_info)
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                self._logger.warning(f'Error in error subscriber: {e}', exc_info=True)
        return should_handle
    async def register_error_strategy(self, source: str, strategy: Callable[[ErrorInfo], bool], plugin_id: Optional[str]=None, component: Optional[str]=None) -> None:
        strategy_key = f'{source}:{plugin_id}:{component}' if component else f'{source}:{plugin_id}' if plugin_id else source
        self._error_strategies[strategy_key] = strategy
    async def unregister_error_strategy(self, source: str, plugin_id: Optional[str]=None, component: Optional[str]=None) -> bool:
        strategy_key = f'{source}:{plugin_id}:{component}' if component else f'{source}:{plugin_id}' if plugin_id else source
        if strategy_key in self._error_strategies:
            del self._error_strategies[strategy_key]
            return True
        return False
    async def register_error_subscriber(self, subscriber: Callable[[ErrorInfo], Any]) -> None:
        if subscriber not in self._error_subscribers:
            self._error_subscribers.append(subscriber)
    async def unregister_error_subscriber(self, subscriber: Callable[[ErrorInfo], Any]) -> bool:
        if subscriber in self._error_subscribers:
            self._error_subscribers.remove(subscriber)
            return True
        return False
    async def get_error(self, error_id: str) -> Optional[ErrorInfo]:
        async with self._error_lock:
            return self._errors.get(error_id)
    async def get_errors(self, source: Optional[str]=None, severity: Optional[Union[ErrorSeverity, List[ErrorSeverity]]]=None, plugin_id: Optional[str]=None, component: Optional[str]=None, handled: Optional[bool]=None, limit: int=100) -> List[ErrorInfo]:
        severities = None
        if severity is not None:
            if isinstance(severity, list):
                severities = severity
            else:
                severities = [severity]
        async with self._error_lock:
            filtered_errors = []
            for error_info in self._errors.values():
                if source is not None and error_info.source != source:
                    continue
                if severities is not None and error_info.severity not in severities:
                    continue
                if plugin_id is not None and error_info.plugin_id != plugin_id:
                    continue
                if component is not None and error_info.component != component:
                    continue
                if handled is not None and error_info.handled != handled:
                    continue
                filtered_errors.append(error_info)
            filtered_errors.sort(key=lambda e: e.timestamp, reverse=True)
            return filtered_errors[:limit]
    async def clear_errors(self, error_ids: Optional[List[str]]=None, source: Optional[str]=None, plugin_id: Optional[str]=None) -> int:
        async with self._error_lock:
            if error_ids:
                count = 0
                for error_id in error_ids:
                    if error_id in self._errors:
                        del self._errors[error_id]
                        count += 1
                return count
            to_remove = []
            for error_id, error_info in self._errors.items():
                if source is not None and error_info.source != source:
                    continue
                if plugin_id is not None and error_info.plugin_id != plugin_id:
                    continue
                to_remove.append(error_id)
            for error_id in to_remove:
                del self._errors[error_id]
            return len(to_remove)
    async def _publish_error_event(self, error_info: ErrorInfo) -> None:
        if not hasattr(self._event_bus_manager, 'publish'):
            return
        payload = {'error_id': error_info.error_id, 'message': error_info.message, 'source': error_info.source, 'severity': error_info.severity, 'plugin_id': error_info.plugin_id, 'component': error_info.component, 'timestamp': error_info.timestamp, 'handled': error_info.handled}
        if error_info.traceback:
            payload['traceback'] = error_info.traceback
        if error_info.metadata:
            payload['metadata'] = error_info.metadata
        event_type = {ErrorSeverity.LOW: 'error/low', ErrorSeverity.MEDIUM: 'error/medium', ErrorSeverity.HIGH: 'error/high', ErrorSeverity.CRITICAL: 'error/critical'}.get(error_info.severity, 'error/unknown')
        await self._event_bus_manager.publish(event_type=event_type, source='error_handler', payload=payload)
    def create_boundary(self, source: str, plugin_id: Optional[str]=None, component: Optional[str]=None) -> ErrorBoundary:
        return ErrorBoundary(error_handler=self, source=source, plugin_id=plugin_id, component=component)
    def status(self) -> Dict[str, Any]:
        total_errors = len(self._errors)
        severity_counts = {severity.value: 0 for severity in ErrorSeverity}
        source_counts = {}
        plugin_counts = {}
        for error_info in self._errors.values():
            severity_counts[error_info.severity.value] += 1
            source = error_info.source
            if source not in source_counts:
                source_counts[source] = 0
            source_counts[source] += 1
            if error_info.plugin_id:
                plugin_id = error_info.plugin_id
                if plugin_id not in plugin_counts:
                    plugin_counts[plugin_id] = 0
                plugin_counts[plugin_id] += 1
        return {'total_errors': total_errors, 'by_severity': severity_counts, 'by_source': source_counts, 'by_plugin': plugin_counts, 'subscribers': len(self._error_subscribers), 'strategies': len(self._error_strategies)}
_global_error_handler: Optional[ErrorHandler] = None
def set_global_error_handler(handler: ErrorHandler) -> None:
    global _global_error_handler
    _global_error_handler = handler
def get_global_error_handler() -> Optional[ErrorHandler]:
    return _global_error_handler
def create_error_boundary(source: str, plugin_id: Optional[str]=None, component: Optional[str]=None) -> ErrorBoundary:
    if _global_error_handler is None:
        raise RuntimeError('Global error handler not set')
    return _global_error_handler.create_boundary(source=source, plugin_id=plugin_id, component=component)
def safe_async(source: str, severity: ErrorSeverity=ErrorSeverity.MEDIUM, plugin_id: Optional[str]=None, component: Optional[str]=None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if _global_error_handler is None:
                raise RuntimeError('Global error handler not set')
            boundary = _global_error_handler.create_boundary(source=source, plugin_id=plugin_id, component=component)
            return await boundary.run(func, *args, severity=severity, **kwargs)
        return wrapper
    return decorator
def safe_sync(source: str, severity: ErrorSeverity=ErrorSeverity.MEDIUM, plugin_id: Optional[str]=None, component: Optional[str]=None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if _global_error_handler is None:
                raise RuntimeError('Global error handler not set')
            boundary = _global_error_handler.create_boundary(source=source, plugin_id=plugin_id, component=component)
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(boundary.run(func, *args, severity=severity, **kwargs))
        return wrapper
    return decorator
def install_global_exception_hook() -> None:
    original_excepthook = sys.excepthook
    def global_exception_hook(exc_type, exc_value, exc_tb):
        if _global_error_handler is not None:
            tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            async def handle_unhandled_error() -> None:
                try:
                    await _global_error_handler.handle_error(message=str(exc_value), source='unhandled', severity=ErrorSeverity.CRITICAL, traceback=tb_str)
                except EventBusError:
                    pass
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(handle_unhandled_error())
            except RuntimeError:
                asyncio.run(handle_unhandled_error())
        original_excepthook(exc_type, exc_value, exc_tb)
    sys.excepthook = global_exception_hook