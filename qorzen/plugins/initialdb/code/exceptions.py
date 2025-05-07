from __future__ import annotations

"""
Exceptions for the InitialDB plugin.

This module defines custom exceptions used throughout the plugin.
"""


class DatabaseConnectionError(Exception):
    """Raised when the plugin cannot connect to the database."""

    def __init__(self, message: str):
        """Initialize with error message.

        Args:
            message: Error description
        """
        super().__init__(message)


class QueryExecutionError(Exception):
    """Raised when there is an error executing a database query."""

    def __init__(self, message: str):
        """Initialize with error message.

        Args:
            message: Error description
        """
        super().__init__(message)


class InvalidFilterError(Exception):
    """Raised when invalid filter parameters are provided."""

    def __init__(self, message: str):
        """Initialize with error message.

        Args:
            message: Error description
        """
        super().__init__(message)


class ExportError(Exception):
    """Raised when data export fails."""

    def __init__(self, message: str):
        """Initialize with error message.

        Args:
            message: Error description
        """
        super().__init__(message)


class ConfigurationError(Exception):
    """Raised when there is an error with the plugin configuration."""

    def __init__(self, message: str):
        """Initialize with error message.

        Args:
            message: Error description
        """
        super().__init__(message)