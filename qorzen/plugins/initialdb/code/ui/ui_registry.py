from __future__ import annotations

"""
UI registry for the InitialDB application.

This module provides a registry for UI components and their factories,
allowing for flexible UI configuration and different UI modes.
"""

from enum import Enum, auto
from typing import Any, Callable, Dict, Optional, Type, cast

import structlog
from PySide6.QtWidgets import QMainWindow, QWidget

logger = structlog.get_logger(__name__)


class UIMode(Enum):
    """Available UI modes for the application."""

    CLASSIC = auto()  # Classic mode with static layout
    IDE = auto()  # IDE-like mode with dockable panels


class UIRegistry:
    """Registry for UI components and factories."""

    _instance: Optional[UIRegistry] = None

    @classmethod
    def instance(cls) -> "UIRegistry":
        """
        Get the singleton instance of the UI registry.

        Returns:
            The UIRegistry instance
        """
        if cls._instance is None:
            cls._instance = UIRegistry()
        return cls._instance

    def __init__(self) -> None:
        """Initialize the UI registry."""
        self._main_window_factories: Dict[UIMode, Callable[[], QMainWindow]] = {}
        self._current_mode = UIMode.CLASSIC

    def register_main_window(
            self, mode: UIMode, factory: Callable[[], QMainWindow]
    ) -> None:
        """
        Register a main window factory for a UI mode.

        Args:
            mode: The UI mode
            factory: Factory function that creates the main window
        """
        self._main_window_factories[mode] = factory
        logger.debug(f"Registered main window for mode: {mode.name}")

    def set_mode(self, mode: UIMode) -> None:
        """
        Set the current UI mode.

        Args:
            mode: The UI mode to set

        Raises:
            ValueError: If the mode is not registered
        """
        if mode not in self._main_window_factories:
            raise ValueError(f"UI mode {mode.name} is not registered")

        self._current_mode = mode
        logger.info(f"UI mode set to: {mode.name}")

    def get_mode(self) -> UIMode:
        """
        Get the current UI mode.

        Returns:
            The current UI mode
        """
        return self._current_mode

    def create_main_window(self) -> QMainWindow:
        """
        Create a main window using the current UI mode.

        Returns:
            The created main window

        Raises:
            ValueError: If no factory is registered for the current mode
        """
        if self._current_mode not in self._main_window_factories:
            raise ValueError(f"No factory registered for UI mode: {self._current_mode.name}")

        factory = self._main_window_factories[self._current_mode]
        logger.debug(f"Creating main window for mode: {self._current_mode.name}")
        return factory()


def init_ui_registry() -> None:
    """Initialize the UI registry with default components."""
    registry = UIRegistry.instance()

    # Register the main window
    from .main_window import MainWindow
    registry.register_main_window(UIMode.IDE, lambda: MainWindow())

    # Default to IDE mode
    registry.set_mode(UIMode.IDE)

    logger.info("UI registry initialized")


def create_main_window() -> QMainWindow:
    """
    Create a main window using the current UI mode.

    Returns:
        The created main window
    """
    return UIRegistry.instance().create_main_window()