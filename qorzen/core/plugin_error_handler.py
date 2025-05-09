from __future__ import annotations
import logging
import sys
import traceback
import threading
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox
from qorzen.core.event_model import Event, EventType
from qorzen.plugin_system.lifecycle import (
    get_plugin_state, set_plugin_state,
    PluginLifecycleState
)


class PluginErrorSeverity(Enum):
    """Severity levels for plugin errors."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class PluginErrorHandler(QObject):
    """Handler for plugin errors.

    This class intercepts and handles errors from plugins, providing
    proper error reporting and recovery mechanisms.
    """

    # Signals
    pluginError = Signal(str, str, object, str)  # plugin_name, error_message, severity, traceback
    pluginReloadRequested = Signal(str)  # plugin_name

    def __init__(self, event_bus_manager: Any, plugin_manager: Any, parent: Optional[QObject] = None) -> None:
        """Initialize the plugin error handler.

        Args:
            event_bus_manager: The event bus manager.
            plugin_manager: The plugin manager.
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._event_bus = event_bus_manager
        self._plugin_manager = plugin_manager
        self._logger = logging.getLogger('plugin_error_handler')

        # Subscribe to plugin error events
        if self._event_bus:
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_ERROR,
                callback=self._on_plugin_error,
                subscriber_id='plugin_error_handler'
            )

        # Connect signals
        self.pluginError.connect(self._handle_plugin_error, Qt.ConnectionType.QueuedConnection)
        self.pluginReloadRequested.connect(self._reload_plugin, Qt.ConnectionType.QueuedConnection)

        # Store plugin errors
        self._plugin_errors: Dict[str, List[Tuple[str, PluginErrorSeverity, str]]] = {}
        self._plugin_errors_lock = threading.RLock()

        # Install global exception handler
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_exception_handler

    def _global_exception_handler(self, exc_type: type, exc_value: Exception, exc_traceback: Any) -> None:
        """Global exception handler.

        Args:
            exc_type: The exception type.
            exc_value: The exception value.
            exc_traceback: The exception traceback.
        """
        # Get the traceback as a string
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Try to find the plugin that caused the exception
        frame = sys._getframe()
        plugin_name = None

        while frame:
            module_name = frame.f_globals.get('__name__', '')

            # Check if the module is a plugin
            if module_name.startswith('plugins.') or 'plugin_' in module_name:
                parts = module_name.split('.')
                if len(parts) > 1:
                    plugin_name = parts[1]
                break

            frame = frame.f_back

        # If we found a plugin, handle the error as a plugin error
        if plugin_name:
            self._logger.error(
                f'Unhandled exception in plugin {plugin_name}: {str(exc_value)}',
                extra={'plugin_name': plugin_name, 'traceback': tb_str}
            )

            # Update plugin lifecycle state
            try:
                set_plugin_state(plugin_name, PluginLifecycleState.FAILED)
            except Exception:
                # Ignore errors from the lifecycle manager
                pass

            # Emit the error signal
            self.pluginError.emit(plugin_name, str(exc_value), PluginErrorSeverity.HIGH, tb_str)
        else:
            # If not a plugin error, use the original excepthook
            self._original_excepthook(exc_type, exc_value, exc_traceback)

    def _on_plugin_error(self, event: Event) -> None:
        """Handle plugin error events.

        Args:
            event: The event.
        """
        # Get error details from the event
        payload = event.payload
        plugin_name = payload.get('plugin_name', 'unknown')
        error_message = payload.get('error', str(payload))
        traceback_str = payload.get('traceback', '')

        # Determine error severity
        severity = self._determine_error_severity(error_message)

        # Update plugin lifecycle state
        try:
            set_plugin_state(plugin_name, PluginLifecycleState.FAILED)
        except Exception:
            # Ignore errors from the lifecycle manager
            pass

        # Emit the error signal
        self.pluginError.emit(plugin_name, error_message, severity, traceback_str)

    def _determine_error_severity(self, error_message: str) -> PluginErrorSeverity:
        """Determine the severity of an error message.

        Args:
            error_message: The error message.

        Returns:
            The error severity.
        """
        # Define keywords for different severity levels
        critical_keywords = [
            'segmentation fault', 'access violation', 'memory error',
            'stack overflow', 'fatal error', 'recursion depth exceeded'
        ]

        high_keywords = [
            'cannot import', 'module not found', 'no attribute',
            'failed to load', 'initialization error'
        ]

        medium_keywords = [
            'timeout', 'connection error', 'permission denied',
            'resource not available'
        ]

        # Check for keywords in the error message
        for keyword in critical_keywords:
            if keyword.lower() in error_message.lower():
                return PluginErrorSeverity.CRITICAL

        for keyword in high_keywords:
            if keyword.lower() in error_message.lower():
                return PluginErrorSeverity.HIGH

        for keyword in medium_keywords:
            if keyword.lower() in error_message.lower():
                return PluginErrorSeverity.MEDIUM

        return PluginErrorSeverity.LOW

    @Slot(str, str, object, str)
    def _handle_plugin_error(self, plugin_name: str, error_message: str, severity: PluginErrorSeverity,
                             traceback_str: str) -> None:
        """Handle a plugin error.

        Args:
            plugin_name: The name of the plugin.
            error_message: The error message.
            severity: The error severity.
            traceback_str: The traceback string.
        """
        # Store the error
        with self._plugin_errors_lock:
            if plugin_name not in self._plugin_errors:
                self._plugin_errors[plugin_name] = []

            self._plugin_errors[plugin_name].append((error_message, severity, traceback_str))

        # Log the error
        self._logger.error(
            f'Plugin error in {plugin_name}: {error_message}',
            extra={'plugin_name': plugin_name, 'severity': severity.name, 'traceback': traceback_str}
        )

        # Handle the error based on severity
        if severity == PluginErrorSeverity.CRITICAL:
            # Unload the plugin
            self._unload_plugin_safely(plugin_name)

            # Show an error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('Critical Plugin Error')
            msg_box.setText(f"The plugin '{plugin_name}' has encountered a critical error and has been unloaded.")
            msg_box.setInformativeText(f'Error: {error_message}')
            msg_box.setDetailedText(traceback_str)
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Retry)

            result = msg_box.exec()

            if result == QMessageBox.Retry:
                self.pluginReloadRequested.emit(plugin_name)

        elif severity == PluginErrorSeverity.HIGH:
            # Show an error message with options
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('Plugin Error')
            msg_box.setText(f"The plugin '{plugin_name}' has encountered an error.")
            msg_box.setInformativeText(f'Error: {error_message}\n\nDo you want to unload the plugin?')
            msg_box.setDetailedText(traceback_str)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Retry)

            result = msg_box.exec()

            if result == QMessageBox.Yes:
                self._unload_plugin_safely(plugin_name)
            elif result == QMessageBox.Retry:
                if self._unload_plugin_safely(plugin_name):
                    self.pluginReloadRequested.emit(plugin_name)

        elif severity == PluginErrorSeverity.MEDIUM:
            # Show a warning message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('Plugin Warning')
            msg_box.setText(f"The plugin '{plugin_name}' has encountered an issue.")
            msg_box.setInformativeText(f'Warning: {error_message}')
            msg_box.setDetailedText(traceback_str)
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Help)

            result = msg_box.exec()

            if result == QMessageBox.Help:
                self._show_plugin_error_details(plugin_name)

        else:
            # Low severity errors don't need user interaction
            pass

    def _unload_plugin_safely(self, plugin_name: str) -> bool:
        """Safely unload a plugin.

        Args:
            plugin_name: The name of the plugin.

        Returns:
            True if the plugin was unloaded, False otherwise.
        """
        # Check if we have a plugin manager
        if not self._plugin_manager:
            return False

        try:
            # Try to unload the plugin
            success = self._plugin_manager.unload_plugin(plugin_name)

            if success:
                self._logger.info(f'Successfully unloaded plugin: {plugin_name}')

                # Update plugin lifecycle state
                try:
                    set_plugin_state(plugin_name, PluginLifecycleState.INACTIVE)
                except Exception:
                    # Ignore errors from the lifecycle manager
                    pass
            else:
                self._logger.warning(f'Failed to unload plugin: {plugin_name}')

            return success
        except Exception as e:
            self._logger.error(
                f'Error while unloading plugin {plugin_name}: {str(e)}',
                extra={'plugin_name': plugin_name, 'traceback': traceback.format_exc()}
            )
            return False

    @Slot(str)
    def _reload_plugin(self, plugin_name: str) -> None:
        """Reload a plugin.

        Args:
            plugin_name: The name of the plugin.
        """
        # Check if we have a plugin manager
        if not self._plugin_manager:
            return

        try:
            # Try to reload the plugin
            success = self._plugin_manager.reload_plugin(plugin_name)

            if success:
                self._logger.info(f'Successfully reloaded plugin: {plugin_name}')

                # Clear errors for the plugin
                with self._plugin_errors_lock:
                    if plugin_name in self._plugin_errors:
                        del self._plugin_errors[plugin_name]

                # Update plugin lifecycle state
                try:
                    set_plugin_state(plugin_name, PluginLifecycleState.ACTIVE)
                except Exception:
                    # Ignore errors from the lifecycle manager
                    pass

                # Show a success message
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle('Plugin Reloaded')
                msg_box.setText(f"The plugin '{plugin_name}' has been successfully reloaded.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
            else:
                self._logger.warning(f'Failed to reload plugin: {plugin_name}')

                # Show an error message
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle('Plugin Reload Failed')
                msg_box.setText(f"Failed to reload plugin '{plugin_name}'.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
        except Exception as e:
            self._logger.error(
                f'Error while reloading plugin {plugin_name}: {str(e)}',
                extra={'plugin_name': plugin_name, 'traceback': traceback.format_exc()}
            )

            # Show an error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('Plugin Reload Error')
            msg_box.setText(f"Error while reloading plugin '{plugin_name}'.")
            msg_box.setInformativeText(f'Error: {str(e)}')
            msg_box.setDetailedText(traceback.format_exc())
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

    def _show_plugin_error_details(self, plugin_name: str) -> None:
        """Show detailed error information for a plugin.

        Args:
            plugin_name: The name of the plugin.
        """
        with self._plugin_errors_lock:
            if plugin_name not in self._plugin_errors:
                return

            errors = self._plugin_errors[plugin_name]

            if not errors:
                return

            # Build the detailed text
            detailed_text = f'Plugin: {plugin_name}\n\n'

            for i, (error_message, severity, traceback_str) in enumerate(errors, 1):
                detailed_text += f'Error {i} (Severity: {severity.name}):\n'
                detailed_text += f'{error_message}\n\n'

                if traceback_str:
                    detailed_text += f'Traceback:\n{traceback_str}\n\n'

                detailed_text += '-' * 50 + '\n\n'

            # Show the error details
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle(f'Error Details: {plugin_name}')
            msg_box.setText(f"Error history for plugin '{plugin_name}':")
            msg_box.setDetailedText(detailed_text)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

    def get_plugin_errors(self, plugin_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get plugin errors.

        Args:
            plugin_name: The name of the plugin to get errors for, or None for all.

        Returns:
            Dictionary of plugin name to list of error dictionaries.
        """
        result = {}

        with self._plugin_errors_lock:
            if plugin_name:
                if plugin_name in self._plugin_errors:
                    result[plugin_name] = [
                        {'message': error_message, 'severity': severity.name, 'traceback': traceback_str}
                        for error_message, severity, traceback_str in self._plugin_errors[plugin_name]
                    ]
            else:
                for plugin, errors in self._plugin_errors.items():
                    result[plugin] = [
                        {'message': error_message, 'severity': severity.name, 'traceback': traceback_str}
                        for error_message, severity, traceback_str in errors
                    ]

        return result

    def clear_plugin_errors(self, plugin_name: Optional[str] = None) -> None:
        """Clear plugin errors.

        Args:
            plugin_name: The name of the plugin to clear errors for, or None for all.
        """
        with self._plugin_errors_lock:
            if plugin_name:
                if plugin_name in self._plugin_errors:
                    del self._plugin_errors[plugin_name]
            else:
                self._plugin_errors.clear()

    def cleanup(self) -> None:
        """Clean up resources."""
        # Restore original excepthook
        sys.excepthook = self._original_excepthook

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(subscriber_id='plugin_error_handler')