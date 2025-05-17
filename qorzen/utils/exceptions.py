from __future__ import annotations

from typing import Any, Dict, Optional


class QorzenError(Exception):
    """Base exception for all Qorzen errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """
        Initialize exception.

        Args:
            message: Error message
            **kwargs: Additional error information
        """
        self.message = message
        self.details = kwargs
        super().__init__(message)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.message}"


class ApplicationError(QorzenError):
    """Exception raised for application-related errors."""

    def __init__(
            self, message: str, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize an ApplicationError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            config_key: The configuration key that caused the error.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        super().__init__(message, *args, details=details, **kwargs)


class ManagerError(QorzenError):
    """Base exception for manager-related errors."""

    def __init__(self, message: str, manager_name: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize manager error.

        Args:
            message: Error message
            manager_name: Name of the affected manager
            **kwargs: Additional error information
        """
        super().__init__(message, manager_name=manager_name, **kwargs)
        self.manager_name = manager_name

    def __str__(self) -> str:
        """String representation."""
        if self.manager_name:
            return f"{self.message} (Manager: {self.manager_name})"
        return super().__str__()


class ManagerInitializationError(ManagerError):
    """Exception raised when a manager fails to initialize."""

    pass


class DatabaseManagerInitializationError(ManagerError):
    """Exception raised when a database manager fails to initialize."""

    pass


class ManagerShutdownError(ManagerError):
    """Exception raised when a manager fails to shut down cleanly."""

    pass


class DependencyError(QorzenError):
    """Exception raised for dependency manager errors."""

    def __init__(
            self, message: str, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a DependencyError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            config_key: The configuration key that caused the error.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        super().__init__(message, *args, details=details, **kwargs)


class ConfigurationError(QorzenError):
    """Exception raised for configuration-related errors."""

    def __init__(
            self, message: str, *args: Any, config_key: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize a ConfigurationError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            config_key: The configuration key that caused the error.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, *args, details=details, **kwargs)


class EventBusError(QorzenError):
    """Exception raised for event bus-related errors."""

    def __init__(
            self, message: str, *args: Any, event_type: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize an EventBusError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            event_type: The event type that caused the error.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        if event_type:
            details["event_type"] = event_type
        super().__init__(message, *args, details=details, **kwargs)


class PluginError(QorzenError):
    """Exception raised for plugin-related errors."""

    def __init__(
            self, message: str, *args: Any, plugin_name: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize a PluginError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            plugin_name: The name of the plugin that caused the error.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        if plugin_name:
            details["plugin_name"] = plugin_name
        super().__init__(message, *args, details=details, **kwargs)


class PluginIsolationError(QorzenError):
    """Exception raised when a plugin fails to isolate itself.

    Args:
        message: A descriptive error message.
        *args: Additional positional arguments to pass to the parent Exception.
        plugin_name: The name of the plugin that caused the error.
        **kwargs: Additional keyword arguments to pass to the parent Exception.
    """

    def __init__(self, message: str, *args: Any, plugin_name: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize a PluginIsolationError."""
        details = kwargs.pop("details", {})
        if plugin_name:
            details["plugin_name"] = plugin_name
        super().__init__(message, *args, details=details, **kwargs)


class DatabaseError(QorzenError):
    """Exception raised for database-related errors."""

    def __init__(
            self, message: str, *args: Any, query: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize a DatabaseError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            query: The database query that caused the error.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        if query:
            details["query"] = query
        super().__init__(message, *args, details=details, **kwargs)


class SecurityError(QorzenError):
    """Exception raised for security-related errors."""

    def __init__(
            self,
            message: str,
            *args: Any,
            user_id: Optional[str] = None,
            permission: Optional[str] = None,
            **kwargs: Any,
    ) -> None:
        """Initialize a SecurityError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            user_id: The ID of the user related to the security error.
            permission: The permission that was being checked.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        if user_id:
            details["user_id"] = user_id
        if permission:
            details["permission"] = permission
        super().__init__(message, *args, details=details, **kwargs)


class ThreadManagerError(ManagerError):
    """Error in thread manager."""

    def __init__(self, message: str, thread_id: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize thread manager error.

        Args:
            message: Error message
            thread_id: Identifier of affected thread
            **kwargs: Additional error information
        """
        super().__init__(message, manager_name="ThreadManager", thread_id=thread_id, **kwargs)
        self.thread_id = thread_id

    def __str__(self) -> str:
        """String representation."""
        if self.thread_id:
            return f"{self.message} (Thread: {self.thread_id})"
        return super().__str__()


class ThreadingError(QorzenError):
    """Error related to threading."""

    def __init__(self, message: str, thread_name: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize threading error.

        Args:
            message: Error message
            thread_name: Name of affected thread
            **kwargs: Additional error information
        """
        super().__init__(message, thread_name=thread_name, **kwargs)
        self.thread_name = thread_name

    def __str__(self) -> str:
        """String representation."""
        if self.thread_name:
            return f"{self.message} (Thread: {self.thread_name})"
        return super().__str__()


class WrongThreadError(ThreadingError):
    """Error when accessing UI elements from wrong thread."""

    def __init__(self, message: str = "UI operation attempted from wrong thread",
                 **kwargs: Any) -> None:
        """
        Initialize wrong thread error.

        Args:
            message: Error message
            **kwargs: Additional error information
        """
        super().__init__(message, **kwargs)


class TaskError(QorzenError):
    """Error related to task execution."""

    def __init__(self, message: str, task_name: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize threading error.

        Args:
            message: Error message
            task_name: Name of affected thread
            **kwargs: Additional error information
        """
        super().__init__(message, task_name=task_name, **kwargs)
        self.task_name = task_name

    def __str__(self) -> str:
        """String representation."""
        if self.task_name:
            return f"{self.message} (Task: {self.task_name})"
        return super().__str__()


class FileError(QorzenError):
    """Exception raised for file-related errors."""

    def __init__(
            self, message: str, *args: Any, file_path: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize a FileError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            file_path: The path of the file that caused the error.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, *args, details=details, **kwargs)


class APIError(QorzenError):
    """Exception raised for API-related errors."""

    def __init__(
            self,
            message: str,
            *args: Any,
            status_code: Optional[int] = None,
            endpoint: Optional[str] = None,
            **kwargs: Any,
    ) -> None:
        """Initialize an APIError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            status_code: The HTTP status code associated with the error.
            endpoint: The API endpoint that caused the error.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        if status_code:
            details["status_code"] = status_code
        if endpoint:
            details["endpoint"] = endpoint
        super().__init__(message, *args, details=details, **kwargs)


class UIError(QorzenError):
    """Exception raised for UI-related errors."""

    def __init__(
            self,
            message: str,
            *args: Any,
            element_id: Optional[str] = None,
            element_type: Optional[str] = None,
            operation: Optional[str] = None,
            **kwargs: Any
    ) -> None:
        """
        Initialize UIError.

        Args:
            message: Error message
            *args: Additional positional arguments
            element_id: The ID of the UI element where the error occurred
            element_type: The type of the UI element where the error occurred
            operation: The UI operation that caused the error
            **kwargs: Additional keyword arguments
        """
        details = kwargs.pop('details', {})
        if element_id:
            details['element_id'] = element_id
        if element_type:
            details['element_type'] = element_type
        if operation:
            details['operation'] = operation
        super().__init__(message, *args, details=details, **kwargs)


class AsyncOperationError(QorzenError):
    """Exception raised for errors in asynchronous operations."""

    def __init__(
            self,
            message: str,
            *args: Any,
            operation: Optional[str] = None,
            operation_id: Optional[str] = None,
            **kwargs: Any
    ) -> None:
        """
        Initialize AsyncOperationError.

        Args:
            message: Error message
            *args: Additional positional arguments
            operation: The asynchronous operation that caused the error
            operation_id: The ID of the asynchronous operation
            **kwargs: Additional keyword arguments
        """
        details = kwargs.pop('details', {})
        if operation:
            details['operation'] = operation
        if operation_id:
            details['operation_id'] = operation_id
        super().__init__(message, *args, details=details, **kwargs)


class ValidationError(QorzenError):
    """Exception raised for validation-related errors."""

    def __init__(
            self, message: str, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a ValidationError.

        Args:
            message: A descriptive error message.
            *args: Additional positional arguments to pass to the parent Exception.
            **kwargs: Additional keyword arguments to pass to the parent Exception.
        """
        details = kwargs.pop("details", {})
        super().__init__(message, *args, details=details, **kwargs)