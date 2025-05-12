# qorzen/core/qt_safe_widget.py
from __future__ import annotations

import functools
import threading
from typing import Any, Callable, Dict, Optional, Set, Type, TypeVar, cast

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QWidget

from qorzen.core.thread_safe_core import ThreadDispatcher, ThreadType, ensure_main_thread

T = TypeVar('T', bound=QObject)


class QtSafeWidget:
    """
    Mixin class that makes Qt widgets thread-safe.

    This class handles all thread concerns automatically so that plugins
    never need to worry about threading issues.
    """

    def __init__(self) -> None:
        """Initialize the thread-safe widget."""
        self._thread_dispatcher = ThreadDispatcher.instance()
        self._main_thread_id = threading.get_ident()

    def __getattribute__(self, name: str) -> Any:
        """
        Override attribute access to ensure all methods run on main thread.

        Args:
            name: Attribute name to access

        Returns:
            Attribute or thread-safe wrapper
        """
        # Get the attribute normally
        attr = super().__getattribute__(name)

        # Don't proxify private attributes or non-methods
        if name.startswith('_') or not callable(attr):
            return attr

        # If we're already on the main thread, no need for proxying
        if threading.get_ident() == self._main_thread_id:
            return attr

        # Create a thread-safe wrapper for the method
        @functools.wraps(attr)
        def thread_safe_method(*args: Any, **kwargs: Any) -> Any:
            return self._thread_dispatcher.execute_on_thread(
                attr,
                thread_type=ThreadType.MAIN,
                *args,
                **kwargs
            ).result()

        return thread_safe_method


def safe_qt_class(cls: Type[T]) -> Type[T]:
    """
    Decorator to make any Qt class thread-safe.

    Args:
        cls: Qt class to make thread-safe

    Returns:
        Thread-safe Qt class
    """
    # Store original __getattribute__
    original_getattribute = cls.__getattribute__

    # Thread dispatcher
    dispatcher = ThreadDispatcher.instance()

    # Define new __getattribute__
    def safe_getattribute(self: QObject, name: str) -> Any:
        # Get the attribute normally
        attr = original_getattribute(self, name)

        # Don't proxify private attributes or non-methods
        if name.startswith('_') or not callable(attr):
            return attr

        # If we're already on the main thread, no need for proxying
        if dispatcher.is_main_thread():
            return attr

        # Create a thread-safe wrapper for the method
        @functools.wraps(attr)
        def thread_safe_method(*args: Any, **kwargs: Any) -> Any:
            return dispatcher.execute_on_thread(
                attr,
                thread_type=ThreadType.MAIN,
                *args,
                **kwargs
            ).result()

        return thread_safe_method

    # Replace __getattribute__
    cls.__getattribute__ = safe_getattribute

    return cls