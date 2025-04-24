import asyncio
from typing import Optional

from PySide6.QtCore import QObject, QThread, Qt, QMetaObject, Q_ARG
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QProgressDialog
import asyncio


class ThreadSafeHelper:
    """Helper class for thread-safe UI operations."""

    @staticmethod
    def run_on_ui_thread(obj: QObject, method_name: str, *args, blocking: bool = False) -> bool:
        """Run a method on the UI thread safely.

        Args:
            obj: The QObject with the method to call
            method_name: The name of the method to call
            *args: Arguments to pass to the method
            blocking: Whether to block until the method completes

        Returns:
            bool: True if the method was successfully invoked
        """
        # Prepare argument list for QMetaObject
        q_args = []
        for arg in args:
            # Convert arguments to QGenericArgument
            if isinstance(arg, str):
                q_args.append(Q_ARG(str, arg))
            elif isinstance(arg, int):
                q_args.append(Q_ARG(int, arg))
            elif isinstance(arg, float):
                q_args.append(Q_ARG(float, arg))
            elif isinstance(arg, bool):
                q_args.append(Q_ARG(bool, arg))
            elif isinstance(arg, list):
                q_args.append(Q_ARG(list, arg))
            elif isinstance(arg, dict):
                q_args.append(Q_ARG(dict, arg))
            elif isinstance(arg, QObject):
                q_args.append(Q_ARG(type(arg), arg))
            else:
                # For other types, use their actual type
                q_args.append(Q_ARG(type(arg), arg))

        # Choose connection type
        connection_type = Qt.ConnectionType.BlockingQueuedConnection if blocking else Qt.ConnectionType.QueuedConnection

        # Invoke the method
        return QMetaObject.invokeMethod(
            obj,
            method_name,
            connection_type,
            *q_args
        )

    @staticmethod
    def update_progress(progress_dialog: QProgressDialog, value: int, text: Optional[str] = None) -> bool:
        """Update a progress dialog safely from any thread.

        Args:
            progress_dialog: The progress dialog to update
            value: The progress value to set
            text: Optional new label text

        Returns:
            bool: True if the update was successful
        """
        if not progress_dialog:
            return False

        success = True
        # Update value
        success = success and QMetaObject.invokeMethod(
            progress_dialog,
            "setValue",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(int, value)
        )

        # Update text if provided
        if text:
            success = success and QMetaObject.invokeMethod(
                progress_dialog,
                "setLabelText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, text)
            )

        return success

    @staticmethod
    def show_message_box(
            parent: QWidget,
            title: str,
            text: str,
            icon: QMessageBox.Icon = QMessageBox.Icon.Information,
            buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok
    ) -> int:
        """Show a message box safely from any thread.

        Args:
            parent: Parent widget
            title: Dialog title
            text: Dialog message
            icon: Dialog icon
            buttons: Dialog buttons

        Returns:
            int: Button clicked (as int)
        """
        # Create a future to get the result
        result_future = asyncio.Future()

        def show_dialog() -> None:
            try:
                ret = QMessageBox.critical(parent, title, text,
                                           buttons) if icon == QMessageBox.Icon.Critical else QMessageBox.information(
                    parent, title, text, buttons)
                result_future.set_result(ret)
            except Exception as e:
                result_future.set_exception(e)

        # Invoke on UI thread
        QMetaObject.invokeMethod(
            parent,
            show_dialog,
            Qt.ConnectionType.QueuedConnection
        )

        # For non-blocking usage, return 0 immediately
        if QThread.currentThread() != QApplication.instance().thread():
            return 0

        # For blocking usage, wait for result with a timeout
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(asyncio.wait_for(result_future, timeout=5.0))
        except (asyncio.TimeoutError, RuntimeError):
            return 0