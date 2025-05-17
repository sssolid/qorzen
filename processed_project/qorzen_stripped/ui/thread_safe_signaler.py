from __future__ import annotations
import threading
from typing import Any, Callable, Optional, TypeVar
from PySide6.QtCore import QObject, Signal, Slot, Qt
T = TypeVar('T')
class ThreadSafeSignaler(QObject):
    signal_no_args = Signal()
    signal_int = Signal(int)
    signal_str = Signal(str)
    signal_int_str = Signal(int, str)
    signal_obj = Signal(object)
    signal_multi = Signal(object, object, object)
    def __init__(self, thread_manager: Any) -> None:
        super().__init__()
        self._thread_manager = thread_manager
    def emit_safely(self, signal: Signal, *args: Any) -> None:
        def do_emit():
            signal.emit(*args)
        if self._thread_manager.is_main_thread():
            do_emit()
        else:
            self._thread_manager.run_on_main_thread(do_emit)