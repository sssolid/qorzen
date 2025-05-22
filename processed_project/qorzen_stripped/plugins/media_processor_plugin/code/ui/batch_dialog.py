from __future__ import annotations
from .output_preview_table import OutputPreviewTable
'\nBatch processing dialog for media processing.\n\nThis module contains the dialog UI for batch processing media files,\nshowing progress, allowing pause/resume, and providing detailed status.\n'
import asyncio
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea, QWidget, QCheckBox, QGroupBox
from ..models.processing_config import ProcessingConfig
from ..processors.batch_processor import BatchProcessor
from ..utils.exceptions import BatchProcessingError
class BatchProcessingDialog(QDialog):
    processingComplete = Signal(dict)
    def __init__(self, batch_processor: BatchProcessor, file_paths: List[str], config: ProcessingConfig, output_dir: Optional[str]=None, overwrite: bool=False, logger: Any=None, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._batch_processor = batch_processor
        self._file_paths = file_paths
        self._config = config
        self._output_dir = output_dir
        self._overwrite = overwrite
        self._logger = logger
        self._job_id = None
        self._paused = False
        self._cancelled = False
        self._completed = False
        self._minimized = False
        self._error = False
        self._processed_files = 0
        self._failed_files = 0
        self._skipped_files = 0
        self._current_file = ''
        self._update_timer = None
        self._init_ui()
        self._start_batch_job()
    def _init_ui(self) -> None:
        self.setWindowTitle('Batch Processing')
        self.setMinimumSize(600, 400)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        title_label = QLabel('Batch Processing')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        main_layout.addWidget(title_label)
        self._status_label = QLabel(f'Processing {len(self._file_paths)} files...')
        main_layout.addWidget(self._status_label)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        progress_group = QGroupBox('Progress')
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.addWidget(QLabel('Overall Progress:'))
        self._overall_progress = QProgressBar()
        self._overall_progress.setMinimum(0)
        self._overall_progress.setMaximum(100)
        self._overall_progress.setValue(0)
        progress_layout.addWidget(self._overall_progress)
        progress_layout.addWidget(QLabel('Current File:'))
        self._current_file_label = QLabel('Waiting to start...')
        self._current_file_label.setWordWrap(True)
        progress_layout.addWidget(self._current_file_label)
        stats_layout = QHBoxLayout()
        self._processed_label = QLabel('Processed: 0')
        stats_layout.addWidget(self._processed_label)
        self._failed_label = QLabel('Failed: 0')
        stats_layout.addWidget(self._failed_label)
        self._skipped_label = QLabel('Skipped: 0')
        stats_layout.addWidget(self._skipped_label)
        self._time_label = QLabel('Time: 00:00:00')
        stats_layout.addWidget(self._time_label)
        progress_layout.addLayout(stats_layout)
        main_layout.addWidget(progress_group)
        details_group = QGroupBox('Details')
        details_layout = QVBoxLayout(details_group)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(120)
        self._file_list = QListWidget()
        scroll_area.setWidget(self._file_list)
        details_layout.addWidget(scroll_area)
        main_layout.addWidget(details_group)
        button_layout = QHBoxLayout()
        self._pause_btn = QPushButton('Pause')
        self._pause_btn.clicked.connect(self._on_pause_resume)
        button_layout.addWidget(self._pause_btn)
        self._cancel_btn = QPushButton('Cancel')
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_btn)
        self._minimize_btn = QPushButton('Minimize')
        self._minimize_btn.clicked.connect(self._on_minimize)
        button_layout.addWidget(self._minimize_btn)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000)
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start()
    def _start_batch_job(self) -> None:
        if hasattr(self, '_file_paths') and hasattr(self, '_config'):
            self._show_output_preview()
        else:
            asyncio.create_task(self._start_batch_job_async())
    def _show_output_preview(self) -> None:
        preview_dialog = OutputPreviewTable(self._file_paths, self._config, self._output_dir, self._overwrite, self._logger, self)
        preview_dialog.processingConfirmed.connect(self._on_preview_confirmed)
        preview_dialog.exec()
    @Slot(bool)
    def _on_preview_confirmed(self, confirmed: bool) -> None:
        if not confirmed:
            self.reject()
            return
        if hasattr(self, '_update_settings_from_preview'):
            self._update_settings_from_preview()
        if hasattr(self, '_original_start_batch_job'):
            self._original_start_batch_job()
    def _update_settings_from_preview(self) -> None:
        for child in self.children():
            if isinstance(child, OutputPreviewTable):
                self._output_dir = child.get_output_dir()
                self._overwrite = child.get_overwrite()
                if hasattr(self, '_status_label'):
                    self._status_label.setText(f'Processing job with output directory: {self._output_dir}')
                break
    async def _start_batch_job_async(self) -> None:
        try:
            self._job_id = await self._batch_processor.start_batch_job(self._file_paths, self._config, self._output_dir, self._overwrite)
            self._logger.info(f'Started batch job {self._job_id} with {len(self._file_paths)} files')
            self._status_label.setText(f'Processing job {self._job_id}...')
            await self._subscribe_to_events()
        except Exception as e:
            self._logger.error(f'Error starting batch job: {str(e)}')
            self._error = True
            self._status_label.setText(f'Error: {str(e)}')
            self._overall_progress.setValue(0)
            self._add_status_message(f'Error starting batch job: {str(e)}', error=True)
            self._pause_btn.setEnabled(False)
    async def _subscribe_to_events(self) -> None:
        if not hasattr(self._batch_processor, '_event_bus_manager'):
            self._logger.warning('Batch processor has no event bus manager, cannot subscribe to events')
            return
        event_bus = self._batch_processor._event_bus_manager
        await event_bus.subscribe(event_type='media_processor/file_processed', callback=self._on_file_processed, subscriber_id=f'batch_dialog_{self._job_id}')
        await event_bus.subscribe(event_type='media_processor/file_error', callback=self._on_file_error, subscriber_id=f'batch_dialog_{self._job_id}')
        await event_bus.subscribe(event_type='media_processor/batch_completed', callback=self._on_batch_completed, subscriber_id=f'batch_dialog_{self._job_id}')
        await event_bus.subscribe(event_type='media_processor/batch_cancelled', callback=self._on_batch_cancelled, subscriber_id=f'batch_dialog_{self._job_id}')
        await event_bus.subscribe(event_type='media_processor/batch_failed', callback=self._on_batch_failed, subscriber_id=f'batch_dialog_{self._job_id}')
    async def _unsubscribe_from_events(self) -> None:
        if not hasattr(self._batch_processor, '_event_bus_manager'):
            return
        event_bus = self._batch_processor._event_bus_manager
        await event_bus.unsubscribe(subscriber_id=f'batch_dialog_{self._job_id}')
    async def _on_file_processed(self, event: Any) -> None:
        payload = event.payload
        job_id = payload.get('job_id')
        if job_id != self._job_id:
            return
        file_path = payload.get('file_path', '')
        output_paths = payload.get('output_paths', [])
        file_index = payload.get('file_index', 0)
        total_files = payload.get('total_files', 0)
        percent_complete = payload.get('percent_complete', 0)
        self._processed_files += 1
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, '_concurrency_manager'):
            concurrency_manager = batch_processor._concurrency_manager
        if concurrency_manager and (not concurrency_manager.is_main_thread()):
            await concurrency_manager.run_on_main_thread(lambda: self._update_ui_for_processed_file(file_path, output_paths, percent_complete))
        else:
            self._update_ui_for_processed_file(file_path, output_paths, percent_complete)
    def _update_ui_for_processed_file(self, file_path: str, output_paths: List[str], percent_complete: int) -> None:
        self._overall_progress.setValue(percent_complete)
        self._processed_label.setText(f'Processed: {self._processed_files}')
        file_name = os.path.basename(file_path)
        message = f'✅ Processed: {file_name}'
        if output_paths:
            message += f' ({len(output_paths)} outputs)'
        self._add_status_message(message)
    async def _on_file_error(self, event: Any) -> None:
        payload = event.payload
        job_id = payload.get('job_id')
        if job_id != self._job_id:
            return
        file_path = payload.get('file_path', '')
        error = payload.get('error', 'Unknown error')
        file_index = payload.get('file_index', 0)
        total_files = payload.get('total_files', 0)
        self._failed_files += 1
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, '_concurrency_manager'):
            concurrency_manager = batch_processor._concurrency_manager
        if concurrency_manager and (not concurrency_manager.is_main_thread()):
            await concurrency_manager.run_on_main_thread(lambda: self._update_ui_for_file_error(file_path, error))
        else:
            self._update_ui_for_file_error(file_path, error)
    def _update_ui_for_file_error(self, file_path: str, error: str) -> None:
        self._failed_label.setText(f'Failed: {self._failed_files}')
        file_name = os.path.basename(file_path)
        self._add_status_message(f'❌ Error processing: {file_name} - {error}', error=True)
    async def _on_batch_completed(self, event: Any) -> None:
        payload = event.payload
        job_id = payload.get('job_id')
        if job_id != self._job_id:
            return
        stats = payload.get('stats', {})
        output_dir = payload.get('output_dir', '')
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, '_concurrency_manager'):
            concurrency_manager = batch_processor._concurrency_manager
        if concurrency_manager and (not concurrency_manager.is_main_thread()):
            await concurrency_manager.run_on_main_thread(lambda: self._update_ui_for_batch_completed(stats, output_dir))
        else:
            self._update_ui_for_batch_completed(stats, output_dir)
        await self._unsubscribe_from_events()
    def _update_ui_for_batch_completed(self, stats: Dict[str, Any], output_dir: str) -> None:
        self._completed = True
        self._overall_progress.setValue(100)
        self._status_label.setText('Processing completed successfully!')
        self._current_file_label.setText('All files processed')
        total = stats.get('total', 0)
        processed = stats.get('processed', 0)
        failed = stats.get('failed', 0)
        skipped = stats.get('skipped', 0)
        time_seconds = stats.get('time_seconds', 0)
        self._processed_label.setText(f'Processed: {processed}')
        self._failed_label.setText(f'Failed: {failed}')
        self._skipped_label.setText(f'Skipped: {skipped}')
        time_str = self._format_time(time_seconds)
        self._time_label.setText(f'Time: {time_str}')
        self._add_status_message(f'✅ Batch processing completed! Processed {processed} files in {time_str}')
        if output_dir:
            self._add_status_message(f'Output files saved to: {output_dir}')
        self._pause_btn.setEnabled(False)
        self._cancel_btn.setText('Close')
        self.processingComplete.emit({'job_id': self._job_id, 'processed': processed, 'failed': failed, 'skipped': skipped, 'time_seconds': time_seconds, 'output_dir': output_dir})
    async def _on_batch_cancelled(self, event: Any) -> None:
        payload = event.payload
        job_id = payload.get('job_id')
        if job_id != self._job_id:
            return
        stats = payload.get('stats', {})
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, '_concurrency_manager'):
            concurrency_manager = batch_processor._concurrency_manager
        if concurrency_manager and (not concurrency_manager.is_main_thread()):
            await concurrency_manager.run_on_main_thread(lambda: self._update_ui_for_batch_cancelled(stats))
        else:
            self._update_ui_for_batch_cancelled(stats)
        await self._unsubscribe_from_events()
    def _update_ui_for_batch_cancelled(self, stats: Dict[str, Any]) -> None:
        self._cancelled = True
        self._status_label.setText('Processing cancelled')
        self._current_file_label.setText('Processing cancelled')
        total = stats.get('total', 0)
        processed = stats.get('processed', 0)
        failed = stats.get('failed', 0)
        skipped = stats.get('skipped', 0)
        self._processed_label.setText(f'Processed: {processed}')
        self._failed_label.setText(f'Failed: {failed}')
        self._skipped_label.setText(f'Skipped: {skipped}')
        self._add_status_message('❌ Batch processing cancelled by user')
        self._pause_btn.setEnabled(False)
        self._cancel_btn.setText('Close')
    async def _on_batch_failed(self, event: Any) -> None:
        payload = event.payload
        job_id = payload.get('job_id')
        if job_id != self._job_id:
            return
        error = payload.get('error', 'Unknown error')
        stats = payload.get('stats', {})
        batch_processor = self._batch_processor
        concurrency_manager = None
        if hasattr(batch_processor, '_concurrency_manager'):
            concurrency_manager = batch_processor._concurrency_manager
        if concurrency_manager and (not concurrency_manager.is_main_thread()):
            await concurrency_manager.run_on_main_thread(lambda: self._update_ui_for_batch_failed(error, stats))
        else:
            self._update_ui_for_batch_failed(error, stats)
        await self._unsubscribe_from_events()
    def _update_ui_for_batch_failed(self, error: str, stats: Dict[str, Any]) -> None:
        self._error = True
        self._status_label.setText(f'Error: {error}')
        self._current_file_label.setText('Processing failed')
        processed = stats.get('processed', 0)
        failed = stats.get('failed', 0)
        skipped = stats.get('skipped', 0)
        self._processed_label.setText(f'Processed: {processed}')
        self._failed_label.setText(f'Failed: {failed}')
        self._skipped_label.setText(f'Skipped: {skipped}')
        self._add_status_message(f'❌ Batch processing failed: {error}', error=True)
        self._pause_btn.setEnabled(False)
        self._cancel_btn.setText('Close')
    def _add_status_message(self, message: str, error: bool=False) -> None:
        item = QListWidgetItem(message)
        if error:
            item.setForeground(Qt.red)
        self._file_list.addItem(item)
        self._file_list.scrollToBottom()
    def _update_status(self) -> None:
        if not self._job_id or self._completed or self._cancelled or self._error:
            return
        asyncio.create_task(self._update_status_async())
    async def _update_status_async(self) -> None:
        if not self._job_id:
            return
        try:
            status = await self._batch_processor.get_job_status(self._job_id)
            batch_processor = self._batch_processor
            concurrency_manager = None
            if hasattr(batch_processor, '_concurrency_manager'):
                concurrency_manager = batch_processor._concurrency_manager
            if concurrency_manager and (not concurrency_manager.is_main_thread()):
                await concurrency_manager.run_on_main_thread(lambda: self._update_status_ui(status))
            else:
                self._update_status_ui(status)
        except Exception as e:
            self._logger.error(f'Error updating status: {str(e)}')
    def _update_status_ui(self, status: Dict[str, Any]) -> None:
        progress = status.get('progress', {})
        percent_complete = progress.get('percent_complete', 0)
        self._overall_progress.setValue(percent_complete)
        current_item = progress.get('current_item')
        if current_item:
            self._current_file = current_item
            self._current_file_label.setText(f'Processing: {os.path.basename(current_item)}')
        total = progress.get('total', 0)
        completed = progress.get('completed', 0)
        failed = progress.get('failed', 0)
        skipped = progress.get('skipped', 0)
        self._processed_files = completed
        self._failed_files = failed
        self._skipped_files = skipped
        self._processed_label.setText(f'Processed: {completed}')
        self._failed_label.setText(f'Failed: {failed}')
        self._skipped_label.setText(f'Skipped: {skipped}')
        elapsed_seconds = status.get('elapsed_seconds', 0)
        time_str = self._format_time(elapsed_seconds)
        self._time_label.setText(f'Time: {time_str}')
        job_status = status.get('status')
        if job_status == 'cancelled':
            self._cancelled = True
            self._status_label.setText('Processing cancelled')
            self._current_file_label.setText('Processing cancelled')
            self._pause_btn.setEnabled(False)
            self._cancel_btn.setText('Close')
        elif job_status == 'completed':
            self._completed = True
            self._status_label.setText('Processing completed')
            self._current_file_label.setText('All files processed')
            self._pause_btn.setEnabled(False)
            self._cancel_btn.setText('Close')
    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int(seconds % 3600 // 60)
        seconds = int(seconds % 60)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
    @Slot()
    def _on_pause_resume(self) -> None:
        if self._paused:
            self._paused = False
            self._pause_btn.setText('Pause')
            self._status_label.setText(f'Processing job {self._job_id}...')
        else:
            self._paused = True
            self._pause_btn.setText('Resume')
            self._status_label.setText('Processing paused')
    @Slot()
    def _on_cancel(self) -> None:
        if self._completed or self._cancelled or self._error:
            self.accept()
            return
        from PySide6.QtWidgets import QMessageBox
        result = QMessageBox.question(self, 'Cancel Processing', 'Are you sure you want to cancel the current batch processing job?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if result == QMessageBox.Yes:
            self._cancel_batch_job()
    def _cancel_batch_job(self) -> None:
        if not self._job_id:
            return
        asyncio.create_task(self._cancel_batch_job_async())
    async def _cancel_batch_job_async(self) -> None:
        if not self._job_id:
            return
        try:
            result = await self._batch_processor.cancel_job(self._job_id)
            if result:
                self._cancelled = True
                batch_processor = self._batch_processor
                concurrency_manager = None
                if hasattr(batch_processor, '_concurrency_manager'):
                    concurrency_manager = batch_processor._concurrency_manager
                if concurrency_manager and (not concurrency_manager.is_main_thread()):
                    await concurrency_manager.run_on_main_thread(self._update_ui_after_cancel)
                else:
                    self._update_ui_after_cancel()
            else:
                self._logger.warning(f'Failed to cancel job {self._job_id}')
        except Exception as e:
            self._logger.error(f'Error cancelling job: {str(e)}')
    def _update_ui_after_cancel(self) -> None:
        self._status_label.setText('Processing cancelled')
        self._current_file_label.setText('Processing cancelled')
        self._add_status_message('❌ Batch processing cancelled by user')
        self._pause_btn.setEnabled(False)
        self._cancel_btn.setText('Close')
    @Slot()
    def _on_minimize(self) -> None:
        if self._minimized:
            self.showNormal()
            self._minimized = False
            self._minimize_btn.setText('Minimize')
        else:
            self.showMinimized()
            self._minimized = True
            self._minimize_btn.setText('Restore')
    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._completed and (not self._cancelled) and (not self._error) and self._job_id:
            from PySide6.QtWidgets import QMessageBox
            result = QMessageBox.question(self, 'Cancel Processing', 'Closing this dialog will cancel the processing job. Continue?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if result == QMessageBox.Yes:
                self._cancel_batch_job()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        if self._update_timer:
            self._update_timer.stop()