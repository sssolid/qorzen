"""
Media Processor Plugin for Qorzen.

This plugin provides advanced image processing capabilities including background removal,
batch processing, and configurable output formats for various media files.
"""

# Import core components
from .plugin import MediaProcessorPlugin

# Import submodules for access
from . import models
from . import processors
from . import ui
from . import utils

__version__ = "1.0.0"