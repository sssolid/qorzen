from __future__ import annotations

import logging
import sys
import traceback
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from qorzen.core.event_model import Event, EventType


class PluginErrorSeverity(Enum):
    """Defines the severity of a plugin error."""

    LOW = auto()  # Non-critical error that doesn't affect functionality
    MEDIUM = auto()  # Error that affects some functionality but not critical features
    HIGH = auto()  # Serious error that affects critical functionality
    CRITICAL = auto()  # Fatal error that requires plugin unloading


class PluginErrorHandler(QObject):
    """Handles errors in plugins to prevent them from crashing the main application."""

    # Signal emitted when a plugin error occurs
    pluginError = Signal(str, str, object, str)  # plugin_name, error_message, severity, traceback

    # Signal emitted when a plugin needs to be reloaded
    pluginReloadRequested = Signal(str)  # plugin_name

    def __init__(
            self,
            event_bus_manager: Any,
            plugin_manager: Any,
            parent: Optional[QObject] = None
    ) -> None:
        """Initialize the plugin error handler.

        Args:
            event_bus_manager: The event bus manager
            plugin_manager: The plugin manager
            parent: The parent QObject
        """
        super().__init__(parent)
        self._event_bus = event_bus_manager
        self._plugin_manager = plugin_manager
        self._logger = logging.getLogger("plugin_error_handler")

        # Register for plugin error events
        if self._event_bus:
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_ERROR,
                callback=self._on_plugin_error,
                subscriber_id="plugin_error_handler"
            )

        # Connect signals to slots
        self.pluginError.connect(self._handle_plugin_error, Qt.ConnectionType.QueuedConnection)
        self.pluginReloadRequested.connect(self._reload_plugin, Qt.ConnectionType.QueuedConnection)

        # Track plugins with errors
        self._plugin_errors: Dict[str, List[Tuple[str, PluginErrorSeverity, str]]] = {}

        # Install global exception hook to catch unhandled exceptions
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_exception_handler

    def _global_exception_handler(self, exc_type: type, exc_value: Exception, exc_traceback: Any) -> None:
        """Global exception handler to catch unhandled exceptions.

        Args:
            exc_type: The exception type
            exc_value: The exception value
            exc_traceback: The exception traceback
        """
        # Convert the traceback to a string
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Try to determine if the exception is from a plugin
        frame = sys._getframe()
        plugin_name = None

        while frame:
            module_name = frame.f_globals.get("__name__", "")
            if module_name.startswith("plugins.") or "plugin_" in module_name:
                # Extract plugin name from module name
                parts = module_name.split(".")
                if len(parts) > 1:
                    plugin_name = parts[1]
                break
            frame = frame.f_back

        if plugin_name:
            # Handle as a plugin error
            self._logger.error(
                f"Unhandled exception in plugin {plugin_name}: {str(exc_value)}",
                extra={"plugin_name": plugin_name, "traceback": tb_str}
            )

            # Emit signal to handle the error
            self.pluginError.emit(
                plugin_name,
                str(exc_value),
                PluginErrorSeverity.HIGH,
                tb_str
            )
        else:
            # Not a plugin error, pass to original handler
            self._original_excepthook(exc_type, exc_value, exc_traceback)

    def _on_plugin_error(self, event: Event) -> None:
        """Handle a plugin error event from the event bus.

        Args:
            event: The plugin error event
        """
        payload = event.payload
        plugin_name = payload.get("plugin_name", "unknown")
        error_message = payload.get("error", str(payload))

        # Determine severity based on the error
        severity = self._determine_error_severity(error_message)

        # Get traceback if available
        traceback_str = payload.get("traceback", "")

        # Handle the error
        self.pluginError.emit(plugin_name, error_message, severity, traceback_str)

    def _determine_error_severity(self, error_message: str) -> PluginErrorSeverity:
        """Determine the severity of an error based on its message.

        Args:
            error_message: The error message

        Returns:
            The error severity
        """
        # Check for critical errors
        critical_keywords = [
            "segmentation fault",
            "access violation",
            "memory error",
            "stack overflow",
            "fatal error"
        ]

        # Check for high severity errors
        high_keywords = [
            "cannot import",
            "module not found",
            "no attribute",
            "failed to load",
            "initialization error"
        ]

        # Check for medium severity errors
        medium_keywords = [
            "timeout",
            "connection error",
            "permission denied",
            "resource not available"
        ]

        # Check error message against keywords
        for keyword in critical_keywords:
            if keyword.lower() in error_message.lower():
                return PluginErrorSeverity.CRITICAL

        for keyword in high_keywords:
            if keyword.lower() in error_message.lower():
                return PluginErrorSeverity.HIGH

        for keyword in medium_keywords:
            if keyword.lower() in error_message.lower():
                return PluginErrorSeverity.MEDIUM

        # Default to low severity
        return PluginErrorSeverity.LOW

    @Slot(str, str, object, str)
    def _handle_plugin_error(
            self,
            plugin_name: str,
            error_message: str,
            severity: PluginErrorSeverity,
            traceback_str: str
    ) -> None:
        """Handle a plugin error.

        Args:
            plugin_name: The name of the plugin
            error_message: The error message
            severity: The error severity
            traceback_str: The error traceback
        """
        # Add error to tracking
        if plugin_name not in self._plugin_errors:
            self._plugin_errors[plugin_name] = []

        self._plugin_errors[plugin_name].append((error_message, severity, traceback_str))

        # Log the error
        self._logger.error(
            f"Plugin error in {plugin_name}: {error_message}",
            extra={"plugin_name": plugin_name, "severity": severity.name, "traceback": traceback_str}
        )

        # Handle based on severity
        if severity == PluginErrorSeverity.CRITICAL:
            # Immediately unload the plugin to prevent further issues
            self._unload_plugin_safely(plugin_name)

            # Show error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Critical Plugin Error")
            msg_box.setText(f"The plugin '{plugin_name}' has encountered a critical error and has been unloaded.")
            msg_box.setInformativeText(f"Error: {error_message}")
            msg_box.setDetailedText(traceback_str)
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Retry)

            # Ask if the user wants to reload the plugin
            result = msg_box.exec()
            if result == QMessageBox.Retry:
                self.pluginReloadRequested.emit(plugin_name)

        elif severity == PluginErrorSeverity.HIGH:
            # For high severity, ask the user if they want to unload the plugin
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Plugin Error")
            msg_box.setText(f"The plugin '{plugin_name}' has encountered an error.")
            msg_box.setInformativeText(f"Error: {error_message}\n\nDo you want to unload the plugin?")
            msg_box.setDetailedText(traceback_str)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Retry)

            result = msg_box.exec()
            if result == QMessageBox.Yes:
                self._unload_plugin_safely(plugin_name)
            elif result == QMessageBox.Retry:
                # Unload and reload
                if self._unload_plugin_safely(plugin_name):
                    self.pluginReloadRequested.emit(plugin_name)

        elif severity == PluginErrorSeverity.MEDIUM:
            # For medium severity, just notify the user
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Plugin Warning")
            msg_box.setText(f"The plugin '{plugin_name}' has encountered an issue.")
            msg_box.setInformativeText(f"Warning: {error_message}")
            msg_box.setDetailedText(traceback_str)
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Help)

            result = msg_box.exec()
            if result == QMessageBox.Help:
                # Show more detailed info in another dialog
                self._show_plugin_error_details(plugin_name)

        else:  # LOW severity
            # For low severity, just log it
            # Optionally show a non-modal notification
            pass

    def _unload_plugin_safely(self, plugin_name: str) -> bool:
        """Safely unload a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            True if the plugin was successfully unloaded, False otherwise
        """
        if not self._plugin_manager:
            return False

        try:
            # Try to unload the plugin
            success = self._plugin_manager.unload_plugin(plugin_name)

            if success:
                self._logger.info(f"Successfully unloaded plugin: {plugin_name}")
            else:
                self._logger.warning(f"Failed to unload plugin: {plugin_name}")

            return success
        except Exception as e:
            # Something went wrong while unloading
            self._logger.error(
                f"Error while unloading plugin {plugin_name}: {str(e)}",
                extra={"plugin_name": plugin_name, "traceback": traceback.format_exc()}
            )
            return False

    @Slot(str)
    def _reload_plugin(self, plugin_name: str) -> None:
        """Reload a plugin.

        Args:
            plugin_name: The name of the plugin
        """
        if not self._plugin_manager:
            return

        try:
            # Try to reload the plugin
            success = self._plugin_manager.reload_plugin(plugin_name)

            if success:
                self._logger.info(f"Successfully reloaded plugin: {plugin_name}")

                # Clear errors for this plugin
                if plugin_name in self._plugin_errors:
                    del self._plugin_errors[plugin_name]

                # Show success message
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle("Plugin Reloaded")
                msg_box.setText(f"The plugin '{plugin_name}' has been successfully reloaded.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
            else:
                self._logger.warning(f"Failed to reload plugin: {plugin_name}")

                # Show error message
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Plugin Reload Failed")
                msg_box.setText(f"Failed to reload plugin '{plugin_name}'.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
        except Exception as e:
            # Something went wrong while reloading
            self._logger.error(
                f"Error while reloading plugin {plugin_name}: {str(e)}",
                extra={"plugin_name": plugin_name, "traceback": traceback.format_exc()}
            )

            # Show error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Plugin Reload Error")
            msg_box.setText(f"Error while reloading plugin '{plugin_name}'.")
            msg_box.setInformativeText(f"Error: {str(e)}")
            msg_box.setDetailedText(traceback.format_exc())
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

    def _show_plugin_error_details(self, plugin_name: str) -> None:
        """Show detailed information about plugin errors.

        Args:
            plugin_name: The name of the plugin
        """
        if plugin_name not in self._plugin_errors:
            return

        errors = self._plugin_errors[plugin_name]
        if not errors:
            return

        # Create detailed text with all errors
        detailed_text = f"Plugin: {plugin_name}\n\n"

        for i, (error_message, severity, traceback_str) in enumerate(errors, 1):
            detailed_text += f"Error {i} (Severity: {severity.name}):\n"
            detailed_text += f"{error_message}\n\n"
            if traceback_str:
                detailed_text += f"Traceback:\n{traceback_str}\n\n"
            detailed_text += "-" * 50 + "\n\n"

        # Show in a dialog
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(f"Error Details: {plugin_name}")
        msg_box.setText(f"Error history for plugin '{plugin_name}':")
        msg_box.setDetailedText(detailed_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def get_plugin_errors(self, plugin_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get a list of errors for a plugin or all plugins.

        Args:
            plugin_name: Optional name of a specific plugin

        Returns:
            A dictionary mapping plugin names to lists of error information
        """
        result = {}

        if plugin_name:
            # Return errors for a specific plugin
            if plugin_name in self._plugin_errors:
                result[plugin_name] = [
                    {
                        "message": error_message,
                        "severity": severity.name,
                        "traceback": traceback_str
                    }
                    for error_message, severity, traceback_str in self._plugin_errors[plugin_name]
                ]
        else:
            # Return errors for all plugins
            for plugin, errors in self._plugin_errors.items():
                result[plugin] = [
                    {
                        "message": error_message,
                        "severity": severity.name,
                        "traceback": traceback_str
                    }
                    for error_message, severity, traceback_str in errors
                ]

        return result

    def clear_plugin_errors(self, plugin_name: Optional[str] = None) -> None:
        """Clear errors for a plugin or all plugins.

        Args:
            plugin_name: Optional name of a specific plugin
        """
        if plugin_name:
            # Clear errors for a specific plugin
            if plugin_name in self._plugin_errors:
                del self._plugin_errors[plugin_name]
        else:
            # Clear all errors
            self._plugin_errors.clear()

    def cleanup(self) -> None:
        """Clean up resources used by the error handler."""
        # Restore original exception hook
        sys.excepthook = self._original_excepthook

        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe(subscriber_id="plugin_error_handler")