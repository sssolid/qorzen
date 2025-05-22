from __future__ import annotations
import atexit
import asyncio
import logging
import logging.handlers
import os
import pathlib
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, cast, Callable, Awaitable
import structlog
from pythonjsonlogger import jsonlogger
from colorlog import ColoredFormatter
from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, EventBusError
class ClickablePathFormatter(ColoredFormatter):
    def format(self, record):
        record.clickable_path = pathlib.Path(record.pathname).as_posix()
        return super().format(record)
class ExcludeLoggerFilter(logging.Filter):
    def __init__(self, excluded_logger_name: str) -> None:
        super().__init__()
        self.excluded_logger_name = excluded_logger_name
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith(self.excluded_logger_name)
class EventBusManagerLogHandler(logging.Handler):
    def __init__(self, event_bus_manager: Any) -> None:
        super().__init__()
        self._event_bus_manager = event_bus_manager
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._running = False
    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self.formatter:
                timestamp = self.formatter.formatTime(record)
                message = self.format(record)
            else:
                timestamp = record.created
                message = record.getMessage()
            event_payload = {'timestamp': timestamp, 'level': record.levelname, 'message': message}
            try:
                self._queue.put_nowait((EventType.LOG_EVENT, 'logging_manager', event_payload))
            except asyncio.QueueFull:
                self.handleError(record)
        except Exception:
            self.handleError(record)
    async def start_processing(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._process_logs())
    async def stop_processing(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    async def _process_logs(self) -> None:
        while self._running:
            try:
                event_type, source, payload = await self._queue.get()
                try:
                    await self._event_bus_manager.publish(event_type=event_type, source=source, payload=payload)
                except Exception:
                    pass
                finally:
                    self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                continue
class LoggingManager(QorzenManager):
    LOG_LEVELS = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR, 'critical': logging.CRITICAL}
    def __init__(self, config_manager: Any) -> None:
        super().__init__(name='logging_manager')
        self._config_manager = config_manager
        self._root_logger: Optional[logging.Logger] = None
        self._file_handler: Optional[logging.Handler] = None
        self._console_handler: Optional[logging.Handler] = None
        self._database_handler: Optional[logging.Handler] = None
        self._elk_handler: Optional[logging.Handler] = None
        self._log_directory: Optional[pathlib.Path] = None
        self._enable_structlog = False
        self._handlers: List[logging.Handler] = []
        self._event_bus_manager = None
        self._event_bus_handler: Optional[EventBusManagerLogHandler] = None
    async def initialize(self) -> None:
        try:
            logging_config = await self._config_manager.get('logging', {})
            log_level_str = logging_config.get('level', 'INFO').lower()
            log_level = self.LOG_LEVELS.get(log_level_str, logging.INFO)
            log_format = logging_config.get('format', 'json').lower()
            self._root_logger = logging.getLogger()
            self._root_logger.setLevel(log_level)
            for handler in list(self._root_logger.handlers):
                self._root_logger.removeHandler(handler)
            if not logging_config:
                self._root_logger.error('Logging configuration not found in configuration')
            if not hasattr(logging_config, 'level'):
                self._root_logger.warning('Missing logging level in configuration. Using INFO level.')
            if not hasattr(logging_config, 'format'):
                self._root_logger.warning('Missing logging format in configuration. Using JSON format.')
            if log_format == 'json':
                self._enable_structlog = True
                formatter = self._create_json_formatter(fmt='%(asctime)s %(name)s %(levelname)s %(filename)s:%(lineno)d %(message)s')
            elif ColoredFormatter:
                fmt = '%(asctime)s [%(log_color)s%(levelname)-8s%(reset)s] File "%(clickable_path)s", line %(lineno)d - Message: %(log_color)s%(message)s%(reset)s'
                formatter = ClickablePathFormatter(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S', reset=True, log_colors={'DEBUG': 'white', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'bold_red'})
            else:
                fmt = '%(asctime)s [%(clickable_path)s:%(lineno)d] %(levelname)s: %(message)s'
                formatter = logging.Formatter(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S')
            console_config = logging_config.get('console', {})
            if not hasattr(console_config, 'enabled'):
                self._root_logger.warning('Missing logging console enabled configuration. Using console logging disabled.')
            if not hasattr(console_config, 'level'):
                self._root_logger.warning('Missing logging console level configuration. Using console logging disabled.')
            if console_config.get('enabled', False):
                console_level_str = console_config.get('level', 'INFO').lower()
                console_level = self.LOG_LEVELS.get(console_level_str, logging.INFO)
                self._console_handler = logging.StreamHandler(sys.stdout)
                self._console_handler.setLevel(console_level)
                self._console_handler.setFormatter(formatter)
                self._root_logger.addHandler(self._console_handler)
                self._handlers.append(self._console_handler)
            file_config = logging_config.get('file', {})
            if not hasattr(logging_config, 'file'):
                self._root_logger.warning('Missing logging file configuration. Using file logging disabled.')
            if not hasattr(file_config, 'enabled'):
                self._root_logger.warning('Missing logging file enabled configuration. Using file logging disabled.')
            if not hasattr(file_config, 'path'):
                self._root_logger.warning('Missing logging file path configuration. Using file logging disabled.')
            if not hasattr(file_config, 'rotation_size'):
                self._root_logger.warning('Missing logging file rotation size configuration. Using file logging disabled.')
            if not hasattr(file_config, 'retention_count'):
                self._root_logger.warning('Missing logging file retention count configuration. Using file logging disabled.')
            if file_config.get('enabled', False):
                file_path = file_config.get('path', 'logs/qorzen.log')
                rotation_size = file_config.get('rotation_size', 10)
                retention_count = file_config.get('retention_count', 30)
                max_bytes = rotation_size * 1024 * 1024
                backup_count = retention_count
                self._file_handler = logging.handlers.RotatingFileHandler(file_path, maxBytes=max_bytes, backupCount=backup_count)
                self._file_handler.setLevel(log_level)
                self._file_handler.setFormatter(formatter)
                self._root_logger.addHandler(self._file_handler)
                self._handlers.append(self._file_handler)
            if logging_config.get('database', {}).get('enabled', False):
                pass
            if logging_config.get('elk', {}).get('enabled', False):
                pass
            if self._enable_structlog:
                self._configure_structlog()
            await self._config_manager.register_listener('logging', self._on_config_changed)
            atexit.register(self._sync_shutdown)
            self._root_logger.info('Logging Manager initialized', extra={'manager': 'AsyncLoggingManager', 'event': 'initialization'})
            self._initialized = True
            self._healthy = True
        except Exception as e:
            raise ManagerInitializationError(f'Failed to initialize AsyncLoggingManager: {str(e)}', manager_name=self.name) from e
    def _create_json_formatter(self, fmt: str='%(asctime)s %(name)s %(levelname)s %(message)s') -> logging.Formatter:
        return jsonlogger.JsonFormatter(fmt=fmt, datefmt='%Y-%m-%dT%H:%M:%S%z', json_ensure_ascii=False)
    def _configure_structlog(self) -> None:
        structlog.configure(processors=[structlog.stdlib.filter_by_level, structlog.processors.TimeStamper(fmt='iso'), structlog.stdlib.add_logger_name, structlog.stdlib.add_log_level, structlog.processors.StackInfoRenderer(), structlog.processors.format_exc_info, structlog.processors.UnicodeDecoder(), structlog.stdlib.ProcessorFormatter.wrap_for_formatter], context_class=dict, logger_factory=structlog.stdlib.LoggerFactory(), wrapper_class=structlog.stdlib.BoundLogger, cache_logger_on_first_use=True)
    def get_logger(self, name: str) -> Union[logging.Logger, Any]:
        if not self._initialized:
            return logging.getLogger(name)
        if self._enable_structlog:
            return structlog.get_logger(name)
        else:
            return logging.getLogger(name)
    async def set_event_bus_manager(self, event_bus_manager: Any) -> None:
        self._event_bus_manager = event_bus_manager
        logging_config = await self._config_manager.get('logging', {})
        log_level_str = logging_config.get('level', 'INFO').lower()
        log_level = self.LOG_LEVELS.get(log_level_str, logging.INFO)
        log_format = logging_config.get('format', 'json').lower()
        if log_format == 'json':
            formatter = self._create_json_formatter()
        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if logging_config.get('ui', {}).get('enabled', True) and self._event_bus_manager:
            self._event_bus_handler = EventBusManagerLogHandler(self._event_bus_manager)
            self._event_bus_handler.addFilter(ExcludeLoggerFilter('event_bus_manager'))
            self._event_bus_handler.setLevel(log_level)
            self._event_bus_handler.setFormatter(formatter)
            self._root_logger.addHandler(self._event_bus_handler)
            self._handlers.append(self._event_bus_handler)
            await self._event_bus_handler.start_processing()
    async def _on_config_changed(self, key: str, value: Any) -> None:
        if not key.startswith('logging.'):
            return
        sub_key = key.split('.', 1)[1] if '.' in key else ''
        if sub_key == 'level' or key == 'logging':
            log_level_str = value.lower() if isinstance(value, str) else 'info'
            log_level = self.LOG_LEVELS.get(log_level_str, logging.INFO)
            if self._root_logger:
                self._root_logger.setLevel(log_level)
                if self._file_handler:
                    self._file_handler.setLevel(log_level)
        elif sub_key.startswith('console.') and self._console_handler:
            if sub_key.endswith('.level'):
                log_level_str = value.lower() if isinstance(value, str) else 'info'
                log_level = self.LOG_LEVELS.get(log_level_str, logging.INFO)
                self._console_handler.setLevel(log_level)
            elif sub_key.endswith('.enabled'):
                if not value and self._console_handler in self._root_logger.handlers:
                    self._root_logger.removeHandler(self._console_handler)
                elif value and self._console_handler not in self._root_logger.handlers:
                    self._root_logger.addHandler(self._console_handler)
        elif sub_key.startswith('file.') and self._file_handler:
            if sub_key.endswith('.level'):
                log_level_str = value.lower() if isinstance(value, str) else 'info'
                log_level = self.LOG_LEVELS.get(log_level_str, logging.INFO)
                self._file_handler.setLevel(log_level)
            elif sub_key.endswith('.enabled'):
                if not value and self._file_handler in self._root_logger.handlers:
                    self._root_logger.removeHandler(self._file_handler)
                elif value and self._file_handler not in self._root_logger.handlers:
                    self._root_logger.addHandler(self._file_handler)
    def _sync_shutdown(self) -> None:
        if not self._initialized:
            return
        if sys.version_info >= (3, 7):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.shutdown())
            finally:
                loop.close()
        else:
            self._sync_shutdown_fallback()
    def _sync_shutdown_fallback(self) -> None:
        if self._root_logger:
            self._root_logger.info('Shutting down Logging Manager (sync fallback)', extra={'manager': 'AsyncLoggingManager', 'event': 'shutdown'})
        for handler in self._handlers:
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass
        self._initialized = False
        self._healthy = False
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            if self._root_logger:
                self._root_logger.info('Shutting down Logging Manager', extra={'manager': 'AsyncLoggingManager', 'event': 'shutdown'})
            if self._event_bus_handler:
                await self._event_bus_handler.stop_processing()
                self._root_logger.removeHandler(self._event_bus_handler)
                self._event_bus_handler.close()
            for handler in self._handlers:
                try:
                    handler.flush()
                    handler.close()
                except Exception:
                    pass
            if self._config_manager and hasattr(self._config_manager, 'unregister_listener'):
                await self._config_manager.unregister_listener('logging', self._on_config_changed)
            try:
                atexit.unregister(self._sync_shutdown)
            except Exception:
                pass
            self._initialized = False
            self._healthy = False
        except Exception as e:
            raise ManagerShutdownError(f'Failed to shut down AsyncLoggingManager: {str(e)}', manager_name=self.name) from e
    def status(self) -> Dict[str, Any]:
        status = super().status()
        if self._initialized:
            status.update({'log_directory': str(self._log_directory) if self._log_directory else None, 'handlers': {'console': self._console_handler is not None and self._console_handler in self._root_logger.handlers if self._root_logger else False, 'file': self._file_handler is not None and self._file_handler in self._root_logger.handlers if self._root_logger else False, 'database': self._database_handler is not None, 'elk': self._elk_handler is not None, 'event_bus_manager': self._event_bus_manager_handler is not None}, 'structured_logging': self._enable_structlog})
        return status