"""
Debug plugin class that has no dependencies.
This is a minimal implementation to test the plugin loading.
"""

from __future__ import annotations
from typing import Any, Dict, Optional


# NO IMPORTS FROM PYSIDE OR QT!

class DebugExamplePlugin:
    """
    Minimal plugin class for debugging purposes.
    """
    # Plugin metadata (exactly as required)
    name = "example_plugin"
    version = "1.0.0"
    description = "An example plugin showcasing the enhanced plugin system features"
    author = "Qorzen Team"

    def __init__(self) -> None:
        """Initialize the plugin."""
        print("DEBUG: DebugExamplePlugin.__init__ called")
        self.event_bus = None
        self.logger = None
        self.config_provider = None
        self.file_manager = None
        self.thread_manager = None
        self._initialized = False

    def initialize(
            self,
            event_bus: Any,
            logger_provider: Any,
            config_provider: Any,
            file_manager: Any,
            thread_manager: Any,
            **kwargs: Any
    ) -> None:
        """Initialize the plugin with the provided managers."""
        print("DEBUG: DebugExamplePlugin.initialize called")
        self.event_bus = event_bus
        self.logger = logger_provider.get_logger("example_plugin")
        self.logger.info("Debug plugin initialized")
        self._initialized = True

    def shutdown(self) -> None:
        """Shut down the plugin."""
        print("DEBUG: DebugExamplePlugin.shutdown called")
        if hasattr(self, 'logger') and self.logger:
            self.logger.info("Debug plugin shut down")
        self._initialized = False


# Print debugging information to help diagnose the issue
print("DEBUG: debug_plugin.py module loaded")
print(f"DEBUG: DebugExamplePlugin attributes:")
print(f"  name: {DebugExamplePlugin.name}")
print(f"  version: {DebugExamplePlugin.version}")
print(f"  description: {DebugExamplePlugin.description}")
print(f"  author: {DebugExamplePlugin.author}")
print(f"  initialize: {hasattr(DebugExamplePlugin, 'initialize')}")
print(f"  shutdown: {hasattr(DebugExamplePlugin, 'shutdown')}")