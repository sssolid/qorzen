from __future__ import annotations
import asyncio
import logging
import traceback
import uuid
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union, cast, Awaitable
from PySide6.QtCore import QObject, Signal, Slot, Qt, QEvent
from PySide6.QtWidgets import QWidget
T = TypeVar('T')
class AsyncTaskSignals(QObject):
    started = Signal()
    result_ready = Signal(object)
    error = Signal(str, str)
    finished = Signal()
class AsyncQWidget(QWidget):
    def __init__(self, parent: Optional[QWidget]=None, concurrency_manager: Optional[Any]=None) -> None:
        super().__init__(parent)
        self._signals = AsyncTaskSignals()
        self._signals.result_ready.connect(self._on_task_result, Qt.QueuedConnection)
        self._signals.error.connect(self._on_task_error, Qt.QueuedConnection)
        self._signals.finished.connect(self._on_task_finished, Qt.QueuedConnection)
        self._logger = logging.getLogger(f'ui.async.{self.__class__.__name__}')
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._concurrency_manager = concurrency_manager
    def run_async_task(self, coroutine_func: Callable[..., Awaitable[Any]], *args: Any, task_id: Optional[str]=None, on_result: Optional[Callable[[Any], None]]=None, on_error: Optional[Callable[[str, str], None]]=None, on_finished: Optional[Callable[[], None]]=None, **kwargs: Any) -> str:
        if task_id is None:
            task_id = str(uuid.uuid4())
        if task_id in self._running_tasks and (not self._running_tasks[task_id].done()):
            self._running_tasks[task_id].cancel()
        async def _task_wrapper() -> None:
            try:
                result = await coroutine_func(*args, **kwargs)
                self._signals.result_ready.emit({'task_id': task_id, 'result': result, 'on_result': on_result})
                if on_result is not None:
                    try:
                        on_result(result)
                    except Exception as e:
                        self._logger.error(f'Error in result callback for task {task_id}: {e}', extra={'task_id': task_id, 'error': str(e)})
            except asyncio.CancelledError:
                pass
            except Exception as e:
                tb_str = traceback.format_exc()
                self._logger.error(f'Error in async task {task_id}: {e}', extra={'task_id': task_id, 'error': str(e), 'traceback': tb_str})
                self._signals.error.emit(str(e), tb_str)
                if on_error is not None:
                    try:
                        on_error(str(e), tb_str)
                    except Exception as cb_error:
                        self._logger.error(f'Error in error callback: {cb_error}', extra={'error': str(cb_error)})
            finally:
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]
                if on_finished is not None:
                    try:
                        on_finished()
                    except Exception as cb_error:
                        self._logger.error(f'Error in finished callback: {cb_error}', extra={'error': str(cb_error)})
                self._signals.finished.emit()
        self._signals.started.emit()
        task = asyncio.create_task(_task_wrapper(), name=f'ui_task_{task_id}')
        self._running_tasks[task_id] = task
        return task_id
    @Slot(object)
    def _on_task_result(self, result_data: Dict[str, Any]) -> None:
        task_id = result_data.get('task_id')
        result = result_data.get('result')
        on_result = result_data.get('on_result')
        if on_result is not None and callable(on_result):
            try:
                on_result(result)
            except Exception as e:
                self._logger.error(f'Error in result callback for task {task_id}: {e}', extra={'task_id': task_id, 'error': str(e)})
    @Slot(str, str)
    def _on_task_error(self, error_msg: str, traceback_str: str) -> None:
        pass
    @Slot()
    def _on_task_finished(self) -> None:
        pass
    def cancel_task(self, task_id: str) -> bool:
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False
    def cancel_all_tasks(self) -> int:
        cancelled = 0
        for task_id in list(self._running_tasks.keys()):
            if self.cancel_task(task_id):
                cancelled += 1
        return cancelled
    def is_task_running(self, task_id: str) -> bool:
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            return not task.done()
        return False
    def get_running_tasks_count(self) -> int:
        return len([t for t in self._running_tasks.values() if not t.done()])
    def closeEvent(self, event: QEvent) -> None:
        self.cancel_all_tasks()
        super().closeEvent(event)
T = TypeVar('T')
def run_async(coro: Awaitable[T]) -> T:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)