from __future__ import annotations
'\nCustom exceptions for media processing.\n\nThis module defines the exception hierarchy for the media processor plugin.\n'
from typing import Optional
class MediaProcessingError(Exception):
    def __init__(self, message: str, file_path: Optional[str]=None) -> None:
        self.file_path = file_path
        self.message = message
        super().__init__(message)
class ImageProcessingError(MediaProcessingError):
    def __init__(self, message: str, file_path: Optional[str]=None, format_id: Optional[str]=None) -> None:
        self.format_id = format_id
        super().__init__(message, file_path)
class BatchProcessingError(MediaProcessingError):
    def __init__(self, message: str, job_id: Optional[str]=None) -> None:
        self.job_id = job_id
        super().__init__(message)
class ConfigurationError(MediaProcessingError):
    def __init__(self, message: str, config_id: Optional[str]=None) -> None:
        self.config_id = config_id
        super().__init__(message)
class BackgroundRemovalError(ImageProcessingError):
    def __init__(self, message: str, file_path: Optional[str]=None, method: Optional[str]=None) -> None:
        self.method = method
        super().__init__(message, file_path)
class OutputFormatError(ImageProcessingError):
    def __init__(self, message: str, file_path: Optional[str]=None, format_id: Optional[str]=None, format_name: Optional[str]=None) -> None:
        self.format_name = format_name
        super().__init__(message, file_path, format_id)
class FileIOError(MediaProcessingError):
    def __init__(self, message: str, file_path: Optional[str]=None, is_input: bool=True) -> None:
        self.is_input = is_input
        super().__init__(message, file_path)