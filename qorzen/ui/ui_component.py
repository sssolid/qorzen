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
    """Signals for async task communication."""
    started = Signal()
    result_ready = Signal(object)
    error = Signal(str, str)
    finished = Signal()


class AsyncQWidget(QWidget):
    """Base widget class with async task support."""

    def __init__(self, parent: Optional[QWidget] = None, concurrency_manager: Optional[Any] = None) -> None:
        """Initialize AsyncQWidget."""
        super().__init__(parent)
        self._signals = AsyncTaskSignals()
        self._signals.result_ready.connect(self._on_task_result, Qt.QueuedConnection)
        self._signals.error.connect(self._on_task_error, Qt.QueuedConnection)
        self._signals.finished.connect(self._on_task_finished, Qt.QueuedConnection)

        self._logger = logging.getLogger(f'ui.async.{self.__class__.__name__}')
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._concurrency_manager = concurrency_manager

    def run_async_task(
            self,
            coroutine_func: Callable[..., Awaitable[Any]],
            *args: Any,
            task_id: Optional[str] = None,
            on_result: Optional[Callable[[Any], None]] = None,
            on_error: Optional[Callable[[str, str], None]] = None,
            on_finished: Optional[Callable[[], None]] = None,
            **kwargs: Any
    ) -> str:
        """Run an async task from a UI component.

        This method is synchronous and returns immediately, running the coroutine
        in the background. The task is tracked and automatically managed.

        Args:
            coroutine_func: The coroutine function to run
            *args: Arguments to pass to the coroutine
            task_id: Optional ID for the task
            on_result: Optional callback for when the task completes successfully
            on_error: Optional callback for when the task fails
            on_finished: Optional callback for when the task finishes (success or failure)
            **kwargs: Keyword arguments to pass to the coroutine

        Returns:
            The task ID
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        # If task already running, cancel it
        if task_id in self._running_tasks and not self._running_tasks[task_id].done():
            self._running_tasks[task_id].cancel()

        async def _task_wrapper() -> None:
            try:
                # Call the coroutine
                result = await coroutine_func(*args, **kwargs)

                # Signal the result
                self._signals.result_ready.emit({
                    'task_id': task_id,
                    'result': result,
                    'on_result': on_result
                })

                # Call on_result directly if provided
                if on_result is not None:
                    try:
                        on_result(result)
                    except Exception as e:
                        self._logger.error(
                            f'Error in result callback for task {task_id}: {e}',
                            extra={'task_id': task_id, 'error': str(e)}
                        )

            except asyncio.CancelledError:
                # Task was cancelled, clean up silently
                pass

            except Exception as e:
                # Handle any other exceptions
                tb_str = traceback.format_exc()
                self._logger.error(
                    f'Error in async task {task_id}: {e}',
                    extra={'task_id': task_id, 'error': str(e), 'traceback': tb_str}
                )

                # Signal the error
                self._signals.error.emit(str(e), tb_str)

                # Call on_error if provided
                if on_error is not None:
                    try:
                        on_error(str(e), tb_str)
                    except Exception as cb_error:
                        self._logger.error(
                            f'Error in error callback: {cb_error}',
                            extra={'error': str(cb_error)}
                        )

            finally:
                # Clean up and signal completion
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]

                # Call on_finished if provided
                if on_finished is not None:
                    try:
                        on_finished()
                    except Exception as cb_error:
                        self._logger.error(
                            f'Error in finished callback: {cb_error}',
                            extra={'error': str(cb_error)}
                        )

                # Signal that the task is finished
                self._signals.finished.emit()

        # Create and store the task
        self._signals.started.emit()
        task = asyncio.create_task(_task_wrapper(), name=f'ui_task_{task_id}')
        self._running_tasks[task_id] = task

        return task_id

    @Slot(object)
    def _on_task_result(self, result_data: Dict[str, Any]) -> None:
        """Handle task result signal."""
        task_id = result_data.get('task_id')
        result = result_data.get('result')
        on_result = result_data.get('on_result')

        if on_result is not None and callable(on_result):
            try:
                on_result(result)
            except Exception as e:
                self._logger.error(
                    f'Error in result callback for task {task_id}: {e}',
                    extra={'task_id': task_id, 'error': str(e)}
                )

    @Slot(str, str)
    def _on_task_error(self, error_msg: str, traceback_str: str) -> None:
        """Handle task error signal."""
        # Default implementation does nothing
        pass

    @Slot()
    def _on_task_finished(self) -> None:
        """Handle task finished signal."""
        # Default implementation does nothing
        pass

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task by ID."""
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False

    def cancel_all_tasks(self) -> int:
        """Cancel all running tasks."""
        cancelled = 0
        for task_id in list(self._running_tasks.keys()):
            if self.cancel_task(task_id):
                cancelled += 1
        return cancelled

    def is_task_running(self, task_id: str) -> bool:
        """Check if a task is running."""
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            return not task.done()
        return False

    def get_running_tasks_count(self) -> int:
        """Get the number of running tasks."""
        return len([t for t in self._running_tasks.values() if not t.done()])

    def closeEvent(self, event: QEvent) -> None:
        """Handle widget close event."""
        self.cancel_all_tasks()
        super().closeEvent(event)


T = TypeVar('T')


def run_async(coro: Awaitable[T]) -> T:
    """Run a coroutine synchronously.

    This function is meant for simple, one-off async operations that need
    to be run synchronously from a UI event handler.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)