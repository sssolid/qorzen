from __future__ import annotations
from typing import Any, Dict, Optional
class QorzenError(Exception):
    def __init__(self, message: str, *args: Any, code: Optional[str]=None, details: Optional[Dict[str, Any]]=None, **kwargs: Any) -> None:
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message, *args, **kwargs)
class ManagerError(QorzenError):
    def __init__(self, message: str, *args: Any, manager_name: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if manager_name:
            details['manager_name'] = manager_name
        super().__init__(message, *args, details=details, **kwargs)
class ManagerInitializationError(ManagerError):
    pass
class ManagerShutdownError(ManagerError):
    pass
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
class ThreadManagerError(QorzenError):
    def __init__(self, message: str, *args: Any, thread_id: Optional[str]=None, **kwargs: Any) -> None:
        details = kwargs.pop('details', {})
        if thread_id:
            details['thread_id'] = thread_id
        super().__init__(message, *args, details=details, **kwargs)
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