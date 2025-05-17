from __future__ import annotations

"""
Events module for Application Launcher plugin.

This module defines the event types used by the Application Launcher plugin
for inter-component communication.
"""

from enum import Enum
from typing import Dict, Any, Optional


class AppLauncherEventType(str, Enum):
    """Event types for the Application Launcher plugin."""

    APP_ADDED = "application_launcher:app_added"
    APP_UPDATED = "application_launcher:app_updated"
    APP_REMOVED = "application_launcher:app_removed"
    APP_LAUNCHED = "application_launcher:app_launched"
    APP_TERMINATED = "application_launcher:app_terminated"
    APP_COMPLETED = "application_launcher:app_completed"
    OUTPUT_DETECTED = "application_launcher:output_detected"

    @classmethod
    def app_added(cls) -> str:
        """Get app added event type."""
        return cls.APP_ADDED.value

    @classmethod
    def app_updated(cls) -> str:
        """Get app updated event type."""
        return cls.APP_UPDATED.value

    @classmethod
    def app_removed(cls) -> str:
        """Get app removed event type."""
        return cls.APP_REMOVED.value

    @classmethod
    def app_launched(cls) -> str:
        """Get app launched event type."""
        return cls.APP_LAUNCHED.value

    @classmethod
    def app_terminated(cls) -> str:
        """Get app terminated event type."""
        return cls.APP_TERMINATED.value

    @classmethod
    def app_completed(cls) -> str:
        """Get app completed event type."""
        return cls.APP_COMPLETED.value

    @classmethod
    def output_detected(cls) -> str:
        """Get output detected event type."""
        return cls.OUTPUT_DETECTED.value


def create_app_added_event(app_id: str, app_name: str) -> Dict[str, Any]:
    """
    Create payload for app added event.

    Args:
        app_id: The application ID
        app_name: The application name

    Returns:
        Event payload dictionary
    """
    return {
        "app_id": app_id,
        "app_name": app_name,
        "timestamp": __import__("time").time()
    }


def create_app_launched_event(
        app_id: str,
        app_name: str,
        command_line: str,
        working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create payload for app launched event.

    Args:
        app_id: The application ID
        app_name: The application name
        command_line: The command line used to launch the app
        working_dir: Working directory, if specified

    Returns:
        Event payload dictionary
    """
    return {
        "app_id": app_id,
        "app_name": app_name,
        "command_line": command_line,
        "working_dir": working_dir,
        "timestamp": __import__("time").time()
    }


def create_app_completed_event(
        app_id: str,
        app_name: str,
        exit_code: int,
        runtime_seconds: float,
        output_files: list
) -> Dict[str, Any]:
    """
    Create payload for app completed event.

    Args:
        app_id: The application ID
        app_name: The application name
        exit_code: The process exit code
        runtime_seconds: Runtime in seconds
        output_files: List of output files produced

    Returns:
        Event payload dictionary
    """
    return {
        "app_id": app_id,
        "app_name": app_name,
        "exit_code": exit_code,
        "success": exit_code == 0,
        "runtime_seconds": runtime_seconds,
        "output_files": output_files,
        "timestamp": __import__("time").time()
    }