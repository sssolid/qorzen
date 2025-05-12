from __future__ import annotations
import threading
from typing import Any, Callable, Optional, TypeVar
from PySide6.QtCore import QObject, Signal, Slot, Qt

T = TypeVar('T')


class ThreadSafeSignaler(QObject):
    """
    A utility class that helps safely emit Qt signals across threads.
    Always create this object on the main thread, then pass it to worker threads.
    """
    # Generic signals for different parameter types
    signal_no_args = Signal()
    signal_int = Signal(int)
    signal_str = Signal(str)
    signal_int_str = Signal(int, str)
    signal_obj = Signal(object)
    signal_multi = Signal(object, object, object)  # For up to 3 generic objects

    def __init__(self, thread_manager: Any) -> None:
        """
        Initialize with a thread manager to ensure main thread execution.

        Args:
            thread_manager: The ThreadManager instance for main thread delegation
        """
        super().__init__()
        self._thread_manager = thread_manager

    def emit_safely(self, signal: Signal, *args: Any) -> None:
        """
        Safely emit a signal, ensuring it happens on the main thread.

        Args:
            signal: The signal to emit
            *args: Arguments to pass to the signal
        """

        def do_emit():
            signal.emit(*args)

        if self._thread_manager.is_main_thread():
            do_emit()
        else:
            self._thread_manager.run_on_main_thread(do_emit)