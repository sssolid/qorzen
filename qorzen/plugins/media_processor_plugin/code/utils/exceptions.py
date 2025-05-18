from __future__ import annotations

"""
Custom exceptions for media processing.

This module defines the exception hierarchy for the media processor plugin.
"""

from typing import Optional


class MediaProcessingError(Exception):
    """Base exception for errors in media processing."""

    def __init__(self, message: str, file_path: Optional[str] = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            file_path: Optional path to the file that caused the error
        """
        self.file_path = file_path
        self.message = message
        super().__init__(message)


class ImageProcessingError(MediaProcessingError):
    """Exception raised when processing a specific image fails."""

    def __init__(self, message: str, file_path: Optional[str] = None, format_id: Optional[str] = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            file_path: Optional path to the file that caused the error
            format_id: Optional ID of the format being applied
        """
        self.format_id = format_id
        super().__init__(message, file_path)


class BatchProcessingError(MediaProcessingError):
    """Exception raised when a batch processing operation fails."""

    def __init__(self, message: str, job_id: Optional[str] = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            job_id: Optional ID of the batch job
        """
        self.job_id = job_id
        super().__init__(message)


class ConfigurationError(MediaProcessingError):
    """Exception raised when there's an error in processing configuration."""

    def __init__(self, message: str, config_id: Optional[str] = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            config_id: Optional ID of the configuration
        """
        self.config_id = config_id
        super().__init__(message)


class BackgroundRemovalError(ImageProcessingError):
    """Exception raised when background removal fails."""

    def __init__(
            self,
            message: str,
            file_path: Optional[str] = None,
            method: Optional[str] = None
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            file_path: Optional path to the file that caused the error
            method: Optional background removal method that failed
        """
        self.method = method
        super().__init__(message, file_path)


class OutputFormatError(ImageProcessingError):
    """Exception raised when applying an output format fails."""

    def __init__(
            self,
            message: str,
            file_path: Optional[str] = None,
            format_id: Optional[str] = None,
            format_name: Optional[str] = None
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            file_path: Optional path to the file that caused the error
            format_id: Optional ID of the format being applied
            format_name: Optional name of the format being applied
        """
        self.format_name = format_name
        super().__init__(message, file_path, format_id)


class FileIOError(MediaProcessingError):
    """Exception raised when file I/O operations fail."""

    def __init__(
            self,
            message: str,
            file_path: Optional[str] = None,
            is_input: bool = True
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            file_path: Optional path to the file that caused the error
            is_input: True if reading, False if writing
        """
        self.is_input = is_input
        super().__init__(message, file_path)