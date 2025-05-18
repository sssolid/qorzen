from __future__ import annotations

"""
Batch processing dialog for media processing.

This module contains the dialog UI for batch processing media files,
showing progress, allowing pause/resume, and providing detailed status.
"""

import asyncio
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QListWidget, QListWidgetItem, QDialogButtonBox,
    QFrame, QScrollArea, QWidget, QCheckBox, QGroupBox
)

from ..models.processing_config import ProcessingConfig
from ..processors.batch_processor import BatchProcessor
from ..utils.exceptions import BatchProcessingError


class BatchProcessingDialog(QDialog):
    """
    Dialog for batch processing of media files.

    Shows:
    - Progress of batch processing
    - Controls for pause/resume/cancel
    - Detailed status info
    - Error reporting
    """

    # Signals
    processingComplete = Signal(dict)  # results dictionary

    def __init__(
            self,
            batch_processor: BatchProcessor,
            file_paths: List[str],
            config: ProcessingConfig,
            output_dir: Optional[str] = None,
            overwrite: bool = False,
            logger: Any = None,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the batch processing dialog.

        Args:
            batch_processor: The batch processor
            file_paths: List of files to process
            config: Processing configuration
            output_dir: Optional override for output directory
            overwrite: Whether to overwrite existing files
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)

        self._batch_processor = batch_processor
        self._file_paths = file_paths
        self._config = config
        self._output_dir = output_dir
        self._overwrite = overwrite
        self._logger = logger

        # Initialize state
        self._job_id = None
        self._paused = False
        self._cancelled = False
        self._completed = False
        self._minimized = False
        self._error = False

        # Status tracking
        self._processed_files = 0
        self._failed_files = 0
        self._skipped_files = 0
        self._current_file = ""
        self._update_timer = None

        # Set up UI
        self._init_ui()

        # Start batch job
        self._start_batch_job()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        # Set window properties
        self.setWindowTitle("Batch Processing")
        self.setMinimumSize(600, 400)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title and description
        title_label = QLabel("Batch Processing")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)

        self._status_label = QLabel(f"Processing {len(self._file_paths)} files...")
        main_layout.addWidget(self._status_label)

        # Add horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Overall progress
        progress_layout.addWidget(QLabel("Overall Progress:"))
        self._overall_progress = QProgressBar()
        self._overall_progress.setMinimum(0)
        self._overall_progress.setMaximum(100)
        self._overall_progress.setValue(0)
        progress_layout.addWidget(self._overall_progress)

        # Current file progress
        progress_layout.addWidget(QLabel("Current File:"))
        self._current_file_label = QLabel("Waiting to start...")
        self._current_file_label.setWordWrap(True)
        progress_layout.addWidget(self._current_file_label)

        # Statistics
        stats_layout = QHBoxLayout()

        self._processed_label = QLabel("Processed: 0")
        stats_layout.addWidget(self._processed_label)

        self._failed_label = QLabel("Failed: 0")
        stats_layout.addWidget(self._failed_label)

        self._skipped_label = QLabel("Skipped: 0")
        stats_layout.addWidget(self._skipped_label)

        self._time_label = QLabel("Time: 00:00:00")
        stats_layout.addWidget(self._time_label)

        progress_layout.addLayout(stats_layout)

        main_layout.addWidget(progress_group)

        # Details section
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)

        # Create scroll area for details
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(120)

        # Create list widget for file details
        self._file_list = QListWidget()
        scroll_area.setWidget(self._file_list)
        details_layout.addWidget(scroll_area)

        main_layout.addWidget(details_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self._pause_btn = QPushButton("Pause")
        self._pause_btn.clicked.connect(self._on_pause_resume)
        button_layout.addWidget(self._pause_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_btn)

        self._minimize_btn = QPushButton("Minimize")
        self._minimize_btn.clicked.connect(self._on_minimize)
        button_layout.addWidget(self._minimize_btn)

        main_layout.addLayout(button_layout)

        # Add extra space at the bottom
        main_layout.addStretch()

        # Set up timer for status updates
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000)  # Update every second
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start()

    def _start_batch_job(self) -> None:
        """Start the batch processing job."""
        # Start in a separate task to avoid blocking UI
        asyncio.create_task(self._start_batch_job_async())

    async def _start_batch_job_async(self) -> None:
        """Asynchronously start the batch processing job."""
        try:
            # Start batch job
            self._job_id = await self._batch_processor.start_batch_job(
                self._file_paths,
                self._config,
                self._output_dir,
                self._overwrite
            )

            # Log start
            self._logger.info(f"Started batch job {self._job_id} with {len(self._file_paths)} files")

            # Update UI
            self._status_label.setText(f"Processing job {self._job_id}...")

            # Subscribe to batch events
            await self._subscribe_to_events()

        except Exception as e:
            self._logger.error(f"Error starting batch job: {str(e)}")
            self._error = True

            # Update UI to show error
            self._status_label.setText(f"Error: {str(e)}")
            self._overall_progress.setValue(0)

            # Add error to file list
            self._add_status_message(f"Error starting batch job: {str(e)}", error=True)

            # Disable pause button
            self._pause_btn.setEnabled(False)

    async def _subscribe_to_events(self) -> None:
        """Subscribe to batch processing events."""
        if not hasattr(self._batch_processor, "_event_bus_manager"):
            self._logger.warning("Batch processor has no event bus manager, cannot subscribe to events")
            return

        event_bus = self._batch_processor._event_bus_manager

        # Subscribe to file processing events
        await event_bus.subscribe(
            event_type="media_processor/file_processed",
            callback=self._on_file_processed,
            subscriber_id=f"batch_dialog_{self._job_id}"
        )

        # Subscribe to file error events
        await event_bus.subscribe(
            event_type="media_processor/file_error",
            callback=self._on_file_error,
            subscriber_id=f"batch_dialog_{self._job_id}"
        )

        # Subscribe to batch completion event
        await event_bus.subscribe(
            event_type="media_processor/batch_completed",
            callback=self._on_batch_completed,
            subscriber_id=f"batch_dialog_{self._job_id}"
        )

        # Subscribe to batch cancel event
        await event_bus.subscribe(
            event_type="media_processor/batch_cancelled",
            callback=self._on_batch_cancelled,
            subscriber_id=f"batch_dialog_{self._job_id}"
        )

        # Subscribe to batch error event
        await event_bus.subscribe(
            event_type="media_processor/batch_failed",
            callback=self._on_batch_failed,
            subscriber_id=f"batch_dialog_{self._job_id}"
        )

    async def _unsubscribe_from_events(self) -> None:
        """Unsubscribe from batch processing events."""
        if not hasattr(self._batch_processor, "_event_bus_manager"):
            return

        event_bus = self._batch_processor._event_bus_manager

        # Unsubscribe from all events
        await event_bus.unsubscribe(
            subscriber_id=f"batch_dialog_{self._job_id}"
        )

    async def _on_file_processed(self, event: Any) -> None:
        """
        Handle file processed event.

        Args:
            event: Event data
        """
        payload = event.payload
        job_id = payload.get("job_id")

        # Check if event is for our job
        if job_id != self._job_id:
            return

        file_path = payload.get("file_path", "")
        output_paths = payload.get("output_paths", [])
        file_index = payload.get("file_index", 0)
        total_files = payload.get("total_files", 0)
        percent_complete = payload.get("percent_complete", 0)

        # Update statistics
        self._processed_files += 1

        # Run UI updates on the main thread
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, "_concurrency_manager"):
            concurrency_manager = batch_processor._concurrency_manager

        if concurrency_manager and not concurrency_manager.is_main_thread():
            await concurrency_manager.run_on_main_thread(
                lambda: self._update_ui_for_processed_file(
                    file_path, output_paths, percent_complete
                )
            )
        else:
            self._update_ui_for_processed_file(
                file_path, output_paths, percent_complete
            )

    def _update_ui_for_processed_file(
            self,
            file_path: str,
            output_paths: List[str],
            percent_complete: int
    ) -> None:
        """
        Update UI for processed file.

        Args:
            file_path: Path to processed file
            output_paths: List of output file paths
            percent_complete: Overall completion percentage
        """
        # Update progress
        self._overall_progress.setValue(percent_complete)

        # Update statistics label
        self._processed_label.setText(f"Processed: {self._processed_files}")

        # Add to file list
        file_name = os.path.basename(file_path)
        message = f"✅ Processed: {file_name}"

        if output_paths:
            message += f" ({len(output_paths)} outputs)"

        self._add_status_message(message)

    async def _on_file_error(self, event: Any) -> None:
        """
        Handle file error event.

        Args:
            event: Event data
        """
        payload = event.payload
        job_id = payload.get("job_id")

        # Check if event is for our job
        if job_id != self._job_id:
            return

        file_path = payload.get("file_path", "")
        error = payload.get("error", "Unknown error")
        file_index = payload.get("file_index", 0)
        total_files = payload.get("total_files", 0)

        # Update statistics
        self._failed_files += 1

        # Run UI updates on the main thread
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, "_concurrency_manager"):
            concurrency_manager = batch_processor._concurrency_manager

        if concurrency_manager and not concurrency_manager.is_main_thread():
            await concurrency_manager.run_on_main_thread(
                lambda: self._update_ui_for_file_error(file_path, error)
            )
        else:
            self._update_ui_for_file_error(file_path, error)

    def _update_ui_for_file_error(self, file_path: str, error: str) -> None:
        """
        Update UI for file error.

        Args:
            file_path: Path to file with error
            error: Error message
        """
        # Update statistics label
        self._failed_label.setText(f"Failed: {self._failed_files}")

        # Add to file list
        file_name = os.path.basename(file_path)
        self._add_status_message(
            f"❌ Error processing: {file_name} - {error}",
            error=True
        )

    async def _on_batch_completed(self, event: Any) -> None:
        """
        Handle batch completed event.

        Args:
            event: Event data
        """
        payload = event.payload
        job_id = payload.get("job_id")

        # Check if event is for our job
        if job_id != self._job_id:
            return

        stats = payload.get("stats", {})
        output_dir = payload.get("output_dir", "")

        # Run UI updates on the main thread
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, "_concurrency_manager"):
            concurrency_manager = batch_processor._concurrency_manager

        if concurrency_manager and not concurrency_manager.is_main_thread():
            await concurrency_manager.run_on_main_thread(
                lambda: self._update_ui_for_batch_completed(stats, output_dir)
            )
        else:
            self._update_ui_for_batch_completed(stats, output_dir)

        # Unsubscribe from events
        await self._unsubscribe_from_events()

    def _update_ui_for_batch_completed(self, stats: Dict[str, Any], output_dir: str) -> None:
        """
        Update UI for batch completion.

        Args:
            stats: Batch statistics
            output_dir: Output directory
        """
        self._completed = True

        # Update progress to 100%
        self._overall_progress.setValue(100)

        # Update status
        self._status_label.setText("Processing completed successfully!")

        # Update current file label
        self._current_file_label.setText("All files processed")

        # Update statistics
        total = stats.get("total", 0)
        processed = stats.get("processed", 0)
        failed = stats.get("failed", 0)
        skipped = stats.get("skipped", 0)
        time_seconds = stats.get("time_seconds", 0)

        self._processed_label.setText(f"Processed: {processed}")
        self._failed_label.setText(f"Failed: {failed}")
        self._skipped_label.setText(f"Skipped: {skipped}")

        # Format time
        time_str = self._format_time(time_seconds)
        self._time_label.setText(f"Time: {time_str}")

        # Add completion message
        self._add_status_message(f"✅ Batch processing completed! Processed {processed} files in {time_str}")
        if output_dir:
            self._add_status_message(f"Output files saved to: {output_dir}")

        # Update buttons
        self._pause_btn.setEnabled(False)
        self._cancel_btn.setText("Close")

        # Emit signal
        self.processingComplete.emit({
            "job_id": self._job_id,
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "time_seconds": time_seconds,
            "output_dir": output_dir
        })

    async def _on_batch_cancelled(self, event: Any) -> None:
        """
        Handle batch cancelled event.

        Args:
            event: Event data
        """
        payload = event.payload
        job_id = payload.get("job_id")

        # Check if event is for our job
        if job_id != self._job_id:
            return

        stats = payload.get("stats", {})

        # Run UI updates on the main thread
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, "_concurrency_manager"):
            concurrency_manager = batch_processor._concurrency_manager

        if concurrency_manager and not concurrency_manager.is_main_thread():
            await concurrency_manager.run_on_main_thread(
                lambda: self._update_ui_for_batch_cancelled(stats)
            )
        else:
            self._update_ui_for_batch_cancelled(stats)

        # Unsubscribe from events
        await self._unsubscribe_from_events()

    def _update_ui_for_batch_cancelled(self, stats: Dict[str, Any]) -> None:
        """
        Update UI for batch cancellation.

        Args:
            stats: Batch statistics
        """
        self._cancelled = True

        # Update status
        self._status_label.setText("Processing cancelled")

        # Update current file label
        self._current_file_label.setText("Processing cancelled")

        # Update statistics
        total = stats.get("total", 0)
        processed = stats.get("processed", 0)
        failed = stats.get("failed", 0)
        skipped = stats.get("skipped", 0)

        self._processed_label.setText(f"Processed: {processed}")
        self._failed_label.setText(f"Failed: {failed}")
        self._skipped_label.setText(f"Skipped: {skipped}")

        # Add cancellation message
        self._add_status_message("❌ Batch processing cancelled by user")

        # Update buttons
        self._pause_btn.setEnabled(False)
        self._cancel_btn.setText("Close")

    async def _on_batch_failed(self, event: Any) -> None:
        """
        Handle batch failed event.

        Args:
            event: Event data
        """
        payload = event.payload
        job_id = payload.get("job_id")

        # Check if event is for our job
        if job_id != self._job_id:
            return

        error = payload.get("error", "Unknown error")
        stats = payload.get("stats", {})

        # Run UI updates on the main thread
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, "_concurrency_manager"):
            concurrency_manager = batch_processor._concurrency_manager

        if concurrency_manager and not concurrency_manager.is_main_thread():
            await concurrency_manager.run_on_main_thread(
                lambda: self._update_ui_for_batch_failed(error, stats)
            )
        else:
            self._update_ui_for_batch_failed(error, stats)

        # Unsubscribe from events
        await self._unsubscribe_from_events()

    def _update_ui_for_batch_failed(self, error: str, stats: Dict[str, Any]) -> None:
        """
        Update UI for batch failure.

        Args:
            error: Error message
            stats: Batch statistics
        """
        self._error = True

        # Update status
        self._status_label.setText(f"Error: {error}")

        # Update current file label
        self._current_file_label.setText("Processing failed")

        # Update statistics
        processed = stats.get("processed", 0)
        failed = stats.get("failed", 0)
        skipped = stats.get("skipped", 0)

        self._processed_label.setText(f"Processed: {processed}")
        self._failed_label.setText(f"Failed: {failed}")
        self._skipped_label.setText(f"Skipped: {skipped}")

        # Add error message
        self._add_status_message(f"❌ Batch processing failed: {error}", error=True)

        # Update buttons
        self._pause_btn.setEnabled(False)
        self._cancel_btn.setText("Close")

    def _add_status_message(self, message: str, error: bool = False) -> None:
        """
        Add a status message to the file list.

        Args:
            message: The message to add
            error: Whether this is an error message
        """
        item = QListWidgetItem(message)
        if error:
            item.setForeground(Qt.red)
        self._file_list.addItem(item)

        # Scroll to bottom
        self._file_list.scrollToBottom()

    def _update_status(self) -> None:
        """Update status display with latest job information."""
        if not self._job_id or self._completed or self._cancelled or self._error:
            return

        # Update in a separate task to avoid blocking UI
        asyncio.create_task(self._update_status_async())

    async def _update_status_async(self) -> None:
        """Asynchronously update status display."""
        if not self._job_id:
            return

        try:
            # Get job status
            status = await self._batch_processor.get_job_status(self._job_id)

            # Run UI updates on the main thread
            batch_processor = self._batch_processor
            concurrency_manager = None
            if hasattr(batch_processor, "_concurrency_manager"):
                concurrency_manager = batch_processor._concurrency_manager

            if concurrency_manager and not concurrency_manager.is_main_thread():
                await concurrency_manager.run_on_main_thread(
                    lambda: self._update_status_ui(status)
                )
            else:
                self._update_status_ui(status)

        except Exception as e:
            self._logger.error(f"Error updating status: {str(e)}")

    def _update_status_ui(self, status: Dict[str, Any]) -> None:
        """
        Update UI with job status.

        Args:
            status: Job status information
        """
        # Update progress
        progress = status.get("progress", {})
        percent_complete = progress.get("percent_complete", 0)
        self._overall_progress.setValue(percent_complete)

        # Update current file
        current_item = progress.get("current_item")
        if current_item:
            self._current_file = current_item
            self._current_file_label.setText(f"Processing: {os.path.basename(current_item)}")

        # Update statistics
        total = progress.get("total", 0)
        completed = progress.get("completed", 0)
        failed = progress.get("failed", 0)
        skipped = progress.get("skipped", 0)

        self._processed_files = completed
        self._failed_files = failed
        self._skipped_files = skipped

        self._processed_label.setText(f"Processed: {completed}")
        self._failed_label.setText(f"Failed: {failed}")
        self._skipped_label.setText(f"Skipped: {skipped}")

        # Update elapsed time
        elapsed_seconds = status.get("elapsed_seconds", 0)
        time_str = self._format_time(elapsed_seconds)
        self._time_label.setText(f"Time: {time_str}")

        # Check job status
        job_status = status.get("status")

        if job_status == "cancelled":
            self._cancelled = True
            self._status_label.setText("Processing cancelled")
            self._current_file_label.setText("Processing cancelled")
            self._pause_btn.setEnabled(False)
            self._cancel_btn.setText("Close")

        elif job_status == "completed":
            self._completed = True
            self._status_label.setText("Processing completed")
            self._current_file_label.setText("All files processed")
            self._pause_btn.setEnabled(False)
            self._cancel_btn.setText("Close")

    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to HH:MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @Slot()
    def _on_pause_resume(self) -> None:
        """Handle pause/resume button click."""
        if self._paused:
            # Resume processing
            self._paused = False
            self._pause_btn.setText("Pause")
            self._status_label.setText(f"Processing job {self._job_id}...")

            # TODO: Implement resume functionality in batch processor

        else:
            # Pause processing
            self._paused = True
            self._pause_btn.setText("Resume")
            self._status_label.setText("Processing paused")

            # TODO: Implement pause functionality in batch processor

    @Slot()
    def _on_cancel(self) -> None:
        """Handle cancel/close button click."""
        if self._completed or self._cancelled or self._error:
            # If job is already done, just close the dialog
            self.accept()
            return

        # Confirm cancellation
        from PySide6.QtWidgets import QMessageBox
        result = QMessageBox.question(
            self,
            "Cancel Processing",
            "Are you sure you want to cancel the current batch processing job?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result == QMessageBox.Yes:
            # Cancel the batch job
            self._cancel_batch_job()

    def _cancel_batch_job(self) -> None:
        """Cancel the current batch job."""
        if not self._job_id:
            return

        # Cancel in a separate task to avoid blocking UI
        asyncio.create_task(self._cancel_batch_job_async())

    async def _cancel_batch_job_async(self) -> None:
        """Asynchronously cancel the batch job."""
        if not self._job_id:
            return

        try:
            # Cancel job
            result = await self._batch_processor.cancel_job(self._job_id)

            if result:
                # Mark as cancelled
                self._cancelled = True

                # Update UI
                batch_processor = self._batch_processor
                concurrency_manager = None
                if hasattr(batch_processor, "_concurrency_manager"):
                    concurrency_manager = batch_processor._concurrency_manager

                if concurrency_manager and not concurrency_manager.is_main_thread():
                    await concurrency_manager.run_on_main_thread(self._update_ui_after_cancel)
                else:
                    self._update_ui_after_cancel()

            else:
                self._logger.warning(f"Failed to cancel job {self._job_id}")

        except Exception as e:
            self._logger.error(f"Error cancelling job: {str(e)}")

    def _update_ui_after_cancel(self) -> None:
        """Update UI after cancellation."""
        # Update status
        self._status_label.setText("Processing cancelled")
        self._current_file_label.setText("Processing cancelled")

        # Add cancellation message
        self._add_status_message("❌ Batch processing cancelled by user")

        # Update buttons
        self._pause_btn.setEnabled(False)
        self._cancel_btn.setText("Close")

    @Slot()
    def _on_minimize(self) -> None:
        """Handle minimize button click."""
        if self._minimized:
            # Restore
            self.showNormal()
            self._minimized = False
            self._minimize_btn.setText("Minimize")
        else:
            # Minimize
            self.showMinimized()
            self._minimized = True
            self._minimize_btn.setText("Restore")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle dialog close event."""
        if not self._completed and not self._cancelled and not self._error and self._job_id:
            # Confirm cancellation
            from PySide6.QtWidgets import QMessageBox
            result = QMessageBox.question(
                self,
                "Cancel Processing",
                "Closing this dialog will cancel the processing job. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if result == QMessageBox.Yes:
                # Cancel the batch job
                self._cancel_batch_job()
                event.accept()
            else:
                event.ignore()
        else:
            # Allow closing
            event.accept()

        # Clean up timer
        if self._update_timer:
            self._update_timer.stop()