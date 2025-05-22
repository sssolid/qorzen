from __future__ import annotations
from typing import Any, Dict, Optional
class QorzenError(Exception):
    def __init__(self, message: str, **kwargs: Any) -> None:
        self.message = message
        self.details = kwargs
        super().__init__(message)
    def __str__(self) -> str:
        return f'{self.message}'
class ApplicationError(QorzenError):
    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        super().__init__(message, *args, details=details, **kwargs)
class ManagerError(QorzenError):
    def __init__(self, message: str, manager_name: Optional[str]=None, **kwargs: Any) -> None:
        super().__init__(message, manager_name=manager_name, **kwargs)
        self.manager_name = manager_name
    def __str__(self) -> str:
        if self.manager_name:
            return f'{self.message} (Manager: {self.manager_name})'
        return super().__str__()
class ManagerInitializationError(ManagerError):
    pass
class DatabaseManagerInitializationError(ManagerError):
    pass
class ManagerShutdownError(ManagerError):
    pass
class DependencyError(QorzenError):
    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        super().__init__(message, *args, details=details, **kwargs)
class ConfigurationError(QorzenError):
    def __init__(self, message: str, *args: Any, config_key: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if config_key:
            details['config_key'] = config_key
        super().__init__(message, *args, details=details, **kwargs)
class EventBusError(QorzenError):
    def __init__(self, message: str, *args: Any, event_type: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if event_type:
            details['event_type'] = event_type
        super().__init__(message, *args, details=details, **kwargs)
class PluginError(QorzenError):
    def __init__(self, message: str, *args: Any, plugin_name: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if plugin_name:
            details['plugin_name'] = plugin_name
        super().__init__(message, *args, details=details, **kwargs)
class PluginIsolationError(QorzenError):
    def __init__(self, message: str, *args: Any, plugin_name: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if plugin_name:
            details['plugin_name'] = plugin_name
        super().__init__(message, *args, details=details, **kwargs)
class DatabaseError(QorzenError):
    def __init__(self, message: str, *args: Any, query: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if query:
            details['query'] = query
        super().__init__(message, *args, details=details, **kwargs)
class SecurityError(QorzenError):
    def __init__(self, message: str, *args: Any, user_id: Optional[str]=None, permission: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if user_id:
            details['user_id'] = user_id
        if permission:
            details['permission'] = permission
        super().__init__(message, *args, details=details, **kwargs)
class ThreadManagerError(ManagerError):
    def __init__(self, message: str, thread_id: Optional[str]=None, **kwargs: Any) -> None:
        super().__init__(message, manager_name='ThreadManager', thread_id=thread_id, **kwargs)
        self.thread_id = thread_id
    def __str__(self) -> str:
        if self.thread_id:
            return f'{self.message} (Thread: {self.thread_id})'
        return super().__str__()
class ThreadingError(QorzenError):
    def __init__(self, message: str, thread_name: Optional[str]=None, **kwargs: Any) -> None:
        super().__init__(message, thread_name=thread_name, **kwargs)
        self.thread_name = thread_name
    def __str__(self) -> str:
        if self.thread_name:
            return f'{self.message} (Thread: {self.thread_name})'
        return super().__str__()
class WrongThreadError(ThreadingError):
    def __init__(self, message: str='UI operation attempted from wrong thread', **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
class TaskError(QorzenError):
    def __init__(self, message: str, task_name: Optional[str]=None, **kwargs: Any) -> None:
        super().__init__(message, task_name=task_name, **kwargs)
        self.task_name = task_name
    def __str__(self) -> str:
        if self.task_name:
            return f'{self.message} (Task: {self.task_name})'
        return super().__str__()
class FileError(QorzenError):
    def __init__(self, message: str, *args: Any, file_path: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if file_path:
            details['file_path'] = file_path
        super().__init__(message, *args, details=details, **kwargs)
class APIError(QorzenError):
    def __init__(self, message: str, *args: Any, status_code: Optional[int]=None, endpoint: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if status_code:
            details['status_code'] = status_code
        if endpoint:
            details['endpoint'] = endpoint
        super().__init__(message, *args, details=details, **kwargs)
class UIError(QorzenError):
    def __init__(self, message: str, *args: Any, element_id: Optional[str]=None, element_type: Optional[str]=None, operation: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if element_id:
            details['element_id'] = element_id
        if element_type:
            details['element_type'] = element_type
        if operation:
            details['operation'] = operation
        super().__init__(message, *args, details=details, **kwargs)
class AsyncOperationError(QorzenError):
    def __init__(self, message: str, *args: Any, operation: Optional[str]=None, operation_id: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if operation:
            details['operation'] = operation
        if operation_id:
            details['operation_id'] = operation_id
        super().__init__(message, *args, details=details, **kwargs)
class ValidationError(QorzenError):
    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        super().__init__(message, *args, details=details, **kwargs)