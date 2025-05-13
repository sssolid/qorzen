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

T = TypeVar('T')


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    LOW = "low"  # Minor issues, can be ignored
    MEDIUM = "medium"  # Issues that should be addressed but aren't critical
    HIGH = "high"  # Serious issues that could affect functionality
    CRITICAL = "critical"  # Critical issues that require immediate attention


@dataclass
class ErrorInfo:
    """Information about an error."""
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
    """Error boundary for async functions.

    Provides a way to safely execute async functions and handle
    any exceptions that occur.
    """

    def __init__(
            self,
            error_handler: Any,
            source: str,
            plugin_id: Optional[str] = None,
            component: Optional[str] = None
    ) -> None:
        """Initialize the error boundary.

        Args:
            error_handler: Error handler to use
            source: Source of errors (e.g., 'plugin', 'core')
            plugin_id: Optional plugin ID if from a plugin
            component: Optional component name
        """
        self._error_handler = error_handler
        self._source = source
        self._plugin_id = plugin_id
        self._component = component

    async def run(
            self,
            func: Callable[..., T],
            *args: Any,
            severity: ErrorSeverity = ErrorSeverity.MEDIUM,
            **kwargs: Any
    ) -> Optional[T]:
        """Run a function safely.

        Args:
            func: Function to run
            *args: Arguments to pass to the function
            severity: Severity of errors that occur
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function or None if an error occurred

        Raises:
            Exception: If the error handler decides to re-raise
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except asyncio.CancelledError:
            # Don't catch cancellation
            raise
        except Exception as e:
            # Create traceback
            tb = traceback.format_exc()

            # Handle the error
            handled = await self._error_handler.handle_error(
                message=str(e),
                source=self._source,
                severity=severity,
                plugin_id=self._plugin_id,
                component=self._component,
                traceback=tb
            )

            # Re-raise if not handled
            if not handled:
                raise

            return None

    def wrap(
            self,
            severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Create a decorator to wrap functions with error handling.

        Args:
            severity: Severity of errors that occur

        Returns:
            Decorator function
        """

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
    """Error handler for async applications.

    Provides error handling services for the application, including
    error logging, reporting, and management.
    """

    def __init__(
            self,
            event_bus_manager: Any,
            logger_manager: Any,
            config_manager: Optional[Any] = None
    ) -> None:
        """Initialize the error handler.

        Args:
            event_bus_manager: Event bus manager
            logger_manager: Logger manager
            config_manager: Optional config manager
        """
        self._event_bus_manager = event_bus_manager
        self._logger = logger_manager.get_logger('error_handler')
        self._config_manager = config_manager

        self._errors: Dict[str, ErrorInfo] = {}
        self._error_subscribers: List[Callable[[ErrorInfo], Any]] = []
        self._error_strategies: Dict[str, Callable[[ErrorInfo], bool]] = {}
        self._error_lock = asyncio.Lock()

        # Configure settings
        if config_manager:
            error_config = config_manager.get('error_handling', {})
            self._max_errors = error_config.get('max_errors', 1000)
            self._default_severity_handling = {
                ErrorSeverity.LOW: error_config.get('handle_low', True),
                ErrorSeverity.MEDIUM: error_config.get('handle_medium', True),
                ErrorSeverity.HIGH: error_config.get('handle_high', False),
                ErrorSeverity.CRITICAL: error_config.get('handle_critical', False)
            }
        else:
            self._max_errors = 1000
            self._default_severity_handling = {
                ErrorSeverity.LOW: True,
                ErrorSeverity.MEDIUM: True,
                ErrorSeverity.HIGH: False,
                ErrorSeverity.CRITICAL: False
            }

    async def handle_error(
            self,
            message: str,
            source: str,
            severity: ErrorSeverity = ErrorSeverity.MEDIUM,
            plugin_id: Optional[str] = None,
            component: Optional[str] = None,
            traceback: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Handle an error.

        Args:
            message: Error message
            source: Source of the error (e.g., 'plugin', 'core')
            severity: Severity of the error
            plugin_id: Optional plugin ID if from a plugin
            component: Optional component name
            traceback: Optional traceback information
            metadata: Optional additional metadata

        Returns:
            True if the error was handled, False if it should be re-raised
        """
        # Generate an error ID
        error_id = str(uuid.uuid4())

        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            message=message,
            source=source,
            severity=severity,
            plugin_id=plugin_id,
            component=component,
            traceback=traceback,
            metadata=metadata or {}
        )

        # Log the error
        log_level = {
            ErrorSeverity.LOW: 'warning',
            ErrorSeverity.MEDIUM: 'warning',
            ErrorSeverity.HIGH: 'error',
            ErrorSeverity.CRITICAL: 'critical'
        }.get(severity, 'error')

        log_func = getattr(self._logger, log_level)
        source_str = f"{source}" + (f":{plugin_id}" if plugin_id else "")
        if component:
            source_str += f":{component}"

        log_func(
            f"Error in {source_str}: {message}",
            extra={
                'error_id': error_id,
                'source': source,
                'severity': severity,
                'plugin_id': plugin_id,
                'component': component
            }
        )

        if traceback:
            self._logger.debug(
                f"Traceback for error {error_id}:\n{traceback}"
            )

        # Store the error
        async with self._error_lock:
            # Check if we have too many errors
            if len(self._errors) >= self._max_errors:
                # Remove oldest errors
                error_ids = list(self._errors.keys())
                error_ids.sort(
                    key=lambda eid: self._errors[eid].timestamp
                )
                to_remove = error_ids[:max(1, len(error_ids) // 10)]
                for eid in to_remove:
                    del self._errors[eid]

            # Store the error
            self._errors[error_id] = error_info

        # Check if we have a strategy for this type of error
        strategy_key = f"{source}:{plugin_id}:{component}" if component else f"{source}:{plugin_id}" if plugin_id else source
        strategy = self._error_strategies.get(strategy_key)
        if strategy:
            # Use the strategy to determine if we should handle the error
            should_handle = strategy(error_info)
            error_info.handled = should_handle
        else:
            # Use default handling based on severity
            should_handle = self._default_severity_handling.get(severity, False)
            error_info.handled = should_handle

        # Publish an error event
        await self._publish_error_event(error_info)

        # Notify subscribers
        for subscriber in self._error_subscribers:
            try:
                result = subscriber(error_info)
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                self._logger.warning(
                    f"Error in error subscriber: {e}",
                    exc_info=True
                )

        return should_handle

    async def register_error_strategy(
            self,
            source: str,
            strategy: Callable[[ErrorInfo], bool],
            plugin_id: Optional[str] = None,
            component: Optional[str] = None
    ) -> None:
        """Register a strategy for handling errors.

        Args:
            source: Source of errors to handle
            strategy: Function that takes an ErrorInfo and returns True if
                      the error should be handled, False if it should be raised
            plugin_id: Optional plugin ID to limit the strategy to
            component: Optional component name to limit the strategy to
        """
        strategy_key = f"{source}:{plugin_id}:{component}" if component else f"{source}:{plugin_id}" if plugin_id else source
        self._error_strategies[strategy_key] = strategy

    async def unregister_error_strategy(
            self,
            source: str,
            plugin_id: Optional[str] = None,
            component: Optional[str] = None
    ) -> bool:
        """Unregister an error strategy.

        Args:
            source: Source of errors
            plugin_id: Optional plugin ID
            component: Optional component name

        Returns:
            True if a strategy was unregistered, False otherwise
        """
        strategy_key = f"{source}:{plugin_id}:{component}" if component else f"{source}:{plugin_id}" if plugin_id else source
        if strategy_key in self._error_strategies:
            del self._error_strategies[strategy_key]
            return True
        return False

    async def register_error_subscriber(
            self,
            subscriber: Callable[[ErrorInfo], Any]
    ) -> None:
        """Register a subscriber to be notified of errors.

        Args:
            subscriber: Function to call with ErrorInfo when an error occurs
        """
        if subscriber not in self._error_subscribers:
            self._error_subscribers.append(subscriber)

    async def unregister_error_subscriber(
            self,
            subscriber: Callable[[ErrorInfo], Any]
    ) -> bool:
        """Unregister an error subscriber.

        Args:
            subscriber: Subscriber to unregister

        Returns:
            True if the subscriber was unregistered, False otherwise
        """
        if subscriber in self._error_subscribers:
            self._error_subscribers.remove(subscriber)
            return True
        return False

    async def get_error(self, error_id: str) -> Optional[ErrorInfo]:
        """Get information about an error.

        Args:
            error_id: ID of the error

        Returns:
            Error information or None if not found
        """
        async with self._error_lock:
            return self._errors.get(error_id)

    async def get_errors(
            self,
            source: Optional[str] = None,
            severity: Optional[Union[ErrorSeverity, List[ErrorSeverity]]] = None,
            plugin_id: Optional[str] = None,
            component: Optional[str] = None,
            handled: Optional[bool] = None,
            limit: int = 100
    ) -> List[ErrorInfo]:
        """Get errors matching criteria.

        Args:
            source: Filter by source
            severity: Filter by severity or severities
            plugin_id: Filter by plugin ID
            component: Filter by component
            handled: Filter by handled status
            limit: Maximum number of errors to return

        Returns:
            List of error information
        """
        # Convert single severity to list for consistent handling
        severities = None
        if severity is not None:
            if isinstance(severity, list):
                severities = severity
            else:
                severities = [severity]

        async with self._error_lock:
            # Filter errors
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

            # Sort by timestamp (newest first)
            filtered_errors.sort(key=lambda e: e.timestamp, reverse=True)

            # Apply limit
            return filtered_errors[:limit]

    async def clear_errors(
            self,
            error_ids: Optional[List[str]] = None,
            source: Optional[str] = None,
            plugin_id: Optional[str] = None
    ) -> int:
        """Clear errors.

        Args:
            error_ids: Specific error IDs to clear, or None for all
            source: Filter by source
            plugin_id: Filter by plugin ID

        Returns:
            Number of errors cleared
        """
        async with self._error_lock:
            if error_ids:
                # Clear specific errors
                count = 0
                for error_id in error_ids:
                    if error_id in self._errors:
                        del self._errors[error_id]
                        count += 1
                return count

            # Clear based on filters
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
        """Publish an error event.

        Args:
            error_info: Error information
        """
        if not hasattr(self._event_bus, 'publish'):
            return

        # Create payload
        payload = {
            'error_id': error_info.error_id,
            'message': error_info.message,
            'source': error_info.source,
            'severity': error_info.severity,
            'plugin_id': error_info.plugin_id,
            'component': error_info.component,
            'timestamp': error_info.timestamp,
            'handled': error_info.handled
        }

        # Include traceback for internal use
        if error_info.traceback:
            payload['traceback'] = error_info.traceback

        # Add metadata
        if error_info.metadata:
            payload['metadata'] = error_info.metadata

        # Determine event type based on severity
        event_type = {
            ErrorSeverity.LOW: 'error/low',
            ErrorSeverity.MEDIUM: 'error/medium',
            ErrorSeverity.HIGH: 'error/high',
            ErrorSeverity.CRITICAL: 'error/critical'
        }.get(error_info.severity, 'error/unknown')

        # Publish the event
        await self._event_bus_manager.publish(
            event_type=event_type,
            source='error_handler',
            payload=payload
        )

    def create_boundary(
            self,
            source: str,
            plugin_id: Optional[str] = None,
            component: Optional[str] = None
    ) -> ErrorBoundary:
        """Create an error boundary.

        Args:
            source: Source of errors (e.g., 'plugin', 'core')
            plugin_id: Optional plugin ID if from a plugin
            component: Optional component name

        Returns:
            Error boundary
        """
        return ErrorBoundary(
            error_handler=self,
            source=source,
            plugin_id=plugin_id,
            component=component
        )

    def status(self) -> Dict[str, Any]:
        """Get the status of the error handler.

        Returns:
            Status information
        """
        total_errors = len(self._errors)

        # Count errors by severity
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

        return {
            'total_errors': total_errors,
            'by_severity': severity_counts,
            'by_source': source_counts,
            'by_plugin': plugin_counts,
            'subscribers': len(self._error_subscribers),
            'strategies': len(self._error_strategies)
        }


# Define a global error handler for easier access
_global_error_handler: Optional[ErrorHandler] = None


def set_global_error_handler(handler: ErrorHandler) -> None:
    """Set the global error handler.

    Args:
        handler: Error handler to use globally
    """
    global _global_error_handler
    _global_error_handler = handler


def get_global_error_handler() -> Optional[ErrorHandler]:
    """Get the global error handler.

    Returns:
        Global error handler or None if not set
    """
    return _global_error_handler


def create_error_boundary(
        source: str,
        plugin_id: Optional[str] = None,
        component: Optional[str] = None
) -> ErrorBoundary:
    """Create an error boundary using the global error handler.

    Args:
        source: Source of errors (e.g., 'plugin', 'core')
        plugin_id: Optional plugin ID if from a plugin
        component: Optional component name

    Returns:
        Error boundary

    Raises:
        RuntimeError: If the global error handler is not set
    """
    if _global_error_handler is None:
        raise RuntimeError("Global error handler not set")

    return _global_error_handler.create_boundary(
        source=source,
        plugin_id=plugin_id,
        component=component
    )


def safe_async(
        source: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        plugin_id: Optional[str] = None,
        component: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to make an async function safe using the global error handler.

    Args:
        source: Source of errors (e.g., 'plugin', 'core')
        severity: Severity of errors that occur
        plugin_id: Optional plugin ID if from a plugin
        component: Optional component name

    Returns:
        Decorator function

    Raises:
        RuntimeError: If the global error handler is not set
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if _global_error_handler is None:
                raise RuntimeError("Global error handler not set")

            boundary = _global_error_handler.create_boundary(
                source=source,
                plugin_id=plugin_id,
                component=component
            )

            return await boundary.run(
                func,
                *args,
                severity=severity,
                **kwargs
            )

        return wrapper

    return decorator


def safe_sync(
        source: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        plugin_id: Optional[str] = None,
        component: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to make a sync function safe using the global error handler.

    Args:
        source: Source of errors (e.g., 'plugin', 'core')
        severity: Severity of errors that occur
        plugin_id: Optional plugin ID if from a plugin
        component: Optional component name

    Returns:
        Decorator function

    Raises:
        RuntimeError: If the global error handler is not set
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if _global_error_handler is None:
                raise RuntimeError("Global error handler not set")

            boundary = _global_error_handler.create_boundary(
                source=source,
                plugin_id=plugin_id,
                component=component
            )

            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                boundary.run(
                    func,
                    *args,
                    severity=severity,
                    **kwargs
                )
            )

        return wrapper

    return decorator


# Install an exception hook to catch unhandled exceptions
def install_global_exception_hook() -> None:
    """Install a global exception hook to catch unhandled exceptions."""
    original_excepthook = sys.excepthook

    def global_exception_hook(exc_type: type, exc_value: Exception, exc_tb: Any) -> None:
        # Only handle if we have a global error handler
        if _global_error_handler is not None:
            tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

            # Create an async function to handle the error
            async def handle_unhandled_error() -> None:
                await _global_error_handler.handle_error(
                    message=str(exc_value),
                    source='unhandled',
                    severity=ErrorSeverity.CRITICAL,
                    traceback=tb_str
                )

            # Run the async function in the event loop
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(handle_unhandled_error())
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(handle_unhandled_error())

        # Call the original excepthook
        original_excepthook(exc_type, exc_value, exc_tb)

    # Set the new exception hook
    sys.excepthook = global_exception_hook
