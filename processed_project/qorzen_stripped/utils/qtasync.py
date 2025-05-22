from __future__ import annotations
import asyncio
import functools
import sys
import threading
from typing import Any, Callable, Dict, Optional, Set, Tuple, TypeVar, cast, Coroutine, Awaitable
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QEventLoop, Qt
from PySide6.QtWidgets import QApplication
T = TypeVar('T')
class QtAsyncBridge(QObject):
    task_result = Signal(object)
    task_error = Signal(str, str)
    def __init__(self) -> None:
        super().__init__()
        self._main_thread_id = threading.get_ident()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._setup_event_processor()
    def _setup_event_processor(self) -> None:
        self._event_timer = QTimer()
        self._event_timer.timeout.connect(self._process_events)
        self._event_timer.start(5)
    @Slot()
    def _process_events(self) -> None:
        loop = asyncio.get_event_loop()
        loop.call_soon(lambda: None)
    def run_coroutine(self, coro: Coroutine[Any, Any, T], task_id: Optional[str]=None, on_result: Optional[Callable[[T], None]]=None, on_error: Optional[Callable[[str, str], None]]=None) -> str:
        if task_id is None:
            import uuid
            task_id = str(uuid.uuid4())
        if task_id in self._running_tasks and (not self._running_tasks[task_id].done()):
            self._running_tasks[task_id].cancel()
        result_handler = on_result or (lambda x: None)
        error_handler = on_error or (lambda e, tb: None)
        if not on_result:
            self.task_result.connect(lambda result_data: result_handler(result_data) if result_data.get('task_id') == task_id else None)
        if not on_error:
            self.task_error.connect(lambda err, tb, tid=task_id: error_handler(err, tb) if tid == task_id else None)
        task = asyncio.create_task(self._task_wrapper(coro, task_id, result_handler, error_handler), name=f'qt_async_{task_id}')
        self._running_tasks[task_id] = task
        return task_id
    async def _task_wrapper(self, coro: Coroutine[Any, Any, T], task_id: str, result_handler: Callable[[T], None], error_handler: Callable[[str, str], None]) -> None:
        try:
            result = await coro
            self.task_result.emit({'task_id': task_id, 'result': result})
            try:
                result_handler(result)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                self.task_error.emit(str(e), tb)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.task_error.emit(str(e), tb)
            try:
                error_handler(str(e), tb)
            except Exception:
                pass
        finally:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    def cancel_task(self, task_id: str) -> bool:
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False
    def cancel_all_tasks(self) -> int:
        cancelled = 0
        for task_id, task in list(self._running_tasks.items()):
            if not task.done():
                task.cancel()
                cancelled += 1
        return cancelled
    def is_main_thread(self) -> bool:
        return threading.get_ident() == self._main_thread_id
    def shutdown(self) -> None:
        if hasattr(self, '_event_timer'):
            self._event_timer.stop()
        self.cancel_all_tasks()
_bridge: Optional[QtAsyncBridge] = None
def get_bridge() -> QtAsyncBridge:
    global _bridge
    if _bridge is None:
        _bridge = QtAsyncBridge()
    return _bridge
def run_coroutine(coro: Coroutine[Any, Any, T], task_id: Optional[str]=None, on_result: Optional[Callable[[T], None]]=None, on_error: Optional[Callable[[str, str], None]]=None) -> str:
    bridge = get_bridge()
    return bridge.run_coroutine(coro, task_id, on_result, on_error)
def cancel_task(task_id: str) -> bool:
    bridge = get_bridge()
    return bridge.cancel_task(task_id)
def is_main_thread() -> bool:
    bridge = get_bridge()
    return bridge.is_main_thread()
def shutdown_bridge() -> None:
    global _bridge
    if _bridge is not None:
        _bridge.shutdown()
        _bridge = None
def run_until_complete(coro: Coroutine[Any, Any, T]) -> T:
    if QApplication.instance() and is_main_thread():
        loop = QEventLoop()
        result: Optional[T] = None
        error: Optional[Exception] = None
        def on_done(task: asyncio.Task) -> None:
            nonlocal result, error
            try:
                result = task.result()
            except Exception as e:
                error = e
            finally:
                loop.quit()
        task = asyncio.create_task(coro)
        task.add_done_callback(on_done)
        loop.exec()
        if error:
            raise error
        return result
    else:
        return asyncio.run(coro)