from __future__ import annotations
'\nBatch processor for media files.\n\nThis module handles processing multiple media files in batch mode,\nwith progress tracking and background execution.\n'
import asyncio
import datetime
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from ..models.processing_config import ProcessingConfig
from ..utils.exceptions import MediaProcessingError, BatchProcessingError
from ..utils.path_resolver import generate_batch_folder_name
from .media_processor import MediaProcessor
class BatchProcessor:
    def __init__(self, media_processor: MediaProcessor, task_manager: TaskManager, event_bus_manager: EventBusManager, concurrency_manager: ConcurrencyManager, logger: Any, processing_config: Dict[str, Any]) -> None:
        self._media_processor = media_processor
        self._task_manager = task_manager
        self._event_bus_manager = event_bus_manager
        self._concurrency_manager = concurrency_manager
        self._logger = logger
        self._processing_config = processing_config
        self._max_concurrent_jobs = processing_config.get('max_concurrent_jobs', 4)
        self._active_jobs: Dict[str, Dict[str, Any]] = {}
        self._job_stats: Dict[str, Dict[str, int]] = {}
        self._logger.info(f'Batch processor initialized with max {self._max_concurrent_jobs} concurrent jobs')
    async def start_batch_job(self, file_paths: List[str], config: ProcessingConfig, output_dir: Optional[str]=None, overwrite: bool=False) -> str:
        try:
            if not file_paths:
                raise BatchProcessingError('No files provided for batch processing')
            job_id = str(uuid.uuid4())
            if output_dir is None:
                base_output_dir = config.output_directory or self._processing_config.get('default_output_dir', 'output')
                if config.create_subfolder_for_batch:
                    batch_folder = generate_batch_folder_name(config.batch_subfolder_template)
                    output_dir = os.path.join(base_output_dir, batch_folder)
                else:
                    output_dir = base_output_dir
            os.makedirs(output_dir, exist_ok=True)
            self._active_jobs[job_id] = {'file_paths': file_paths, 'config': config, 'output_dir': output_dir, 'overwrite': overwrite, 'started_at': datetime.datetime.now(), 'status': 'starting', 'cancelled': False, 'task_id': None}
            self._job_stats[job_id] = {'total': len(file_paths), 'completed': 0, 'failed': 0, 'skipped': 0, 'current_index': 0}
            task_id = await self._task_manager.submit_task(func=self._process_batch, job_id=job_id, name=f'batch_media_processing_{job_id}', category=TaskCategory.BACKGROUND, priority=TaskPriority.NORMAL, metadata={'job_id': job_id, 'file_count': len(file_paths), 'output_dir': output_dir}, cancellable=True)
            self._active_jobs[job_id]['task_id'] = task_id
            self._active_jobs[job_id]['status'] = 'running'
            await self._event_bus_manager.publish(event_type='media_processor/batch_started', source='batch_processor', payload={'job_id': job_id, 'task_id': task_id, 'file_count': len(file_paths), 'output_dir': output_dir})
            self._logger.info(f'Started batch job {job_id} with {len(file_paths)} files')
            return job_id
        except Exception as e:
            self._logger.error(f'Error starting batch job: {str(e)}')
            raise BatchProcessingError(f'Error starting batch job: {str(e)}')
    async def _process_batch(self, job_id: str, progress_reporter: Any=None) -> Dict[str, Any]:
        if job_id not in self._active_jobs:
            raise BatchProcessingError(f'Batch job {job_id} not found')
        job_info = self._active_jobs[job_id]
        job_stats = self._job_stats[job_id]
        file_paths = job_info['file_paths']
        config = job_info['config']
        output_dir = job_info['output_dir']
        overwrite = job_info['overwrite']
        results: Dict[str, Any] = {'job_id': job_id, 'total_files': len(file_paths), 'processed_files': 0, 'failed_files': 0, 'skipped_files': 0, 'output_paths': [], 'errors': [], 'start_time': job_info['started_at'], 'end_time': None, 'total_time_seconds': 0}
        start_time = time.time()
        current_file_index = 0
        total_files = len(file_paths)
        semaphore = asyncio.Semaphore(self._max_concurrent_jobs)
        async def process_file(file_index: int, file_path: str) -> None:
            nonlocal current_file_index
            async with semaphore:
                if job_info['cancelled']:
                    job_stats['skipped'] += 1
                    results['skipped_files'] += 1
                    return
                try:
                    if progress_reporter:
                        percent = int(file_index / total_files * 100)
                        await progress_reporter.report_progress(percent, f'Processing file {file_index + 1} of {total_files}: {os.path.basename(file_path)}')
                    output_paths = await self._media_processor.process_image(file_path, config, output_dir, overwrite)
                    results['output_paths'].extend(output_paths)
                    results['processed_files'] += 1
                    job_stats['completed'] += 1
                    await self._event_bus_manager.publish(event_type='media_processor/file_processed', source='batch_processor', payload={'job_id': job_id, 'file_path': file_path, 'output_paths': output_paths, 'file_index': file_index, 'total_files': total_files, 'percent_complete': int((file_index + 1) / total_files * 100)})
                except Exception as e:
                    self._logger.error(f'Error processing file {file_path}: {str(e)}')
                    results['errors'].append({'file_path': file_path, 'error': str(e)})
                    results['failed_files'] += 1
                    job_stats['failed'] += 1
                    await self._event_bus_manager.publish(event_type='media_processor/file_error', source='batch_processor', payload={'job_id': job_id, 'file_path': file_path, 'error': str(e), 'file_index': file_index, 'total_files': total_files})
        try:
            tasks = []
            for i, file_path in enumerate(file_paths):
                task = asyncio.create_task(process_file(i, file_path))
                tasks.append(task)
                job_stats['current_index'] = i
            await asyncio.gather(*tasks)
            end_time = time.time()
            results['total_time_seconds'] = end_time - start_time
            results['end_time'] = datetime.datetime.now()
            job_info['status'] = 'completed'
            await self._event_bus_manager.publish(event_type='media_processor/batch_completed', source='batch_processor', payload={'job_id': job_id, 'stats': {'total': results['total_files'], 'processed': results['processed_files'], 'failed': results['failed_files'], 'skipped': results['skipped_files'], 'time_seconds': results['total_time_seconds']}, 'output_dir': output_dir})
            if progress_reporter:
                await progress_reporter.report_progress(100, f"Completed processing {results['processed_files']} files with {results['failed_files']} failures")
            self._logger.info(f"Batch job {job_id} completed: {results['processed_files']} processed, {results['failed_files']} failed, {results['skipped_files']} skipped")
            return results
        except asyncio.CancelledError:
            job_info['status'] = 'cancelled'
            job_info['cancelled'] = True
            self._logger.info(f'Batch job {job_id} cancelled')
            await self._event_bus_manager.publish(event_type='media_processor/batch_cancelled', source='batch_processor', payload={'job_id': job_id, 'stats': {'total': results['total_files'], 'processed': results['processed_files'], 'failed': results['failed_files'], 'skipped': total_files - results['processed_files'] - results['failed_files']}})
            raise
        except Exception as e:
            job_info['status'] = 'failed'
            self._logger.error(f'Batch job {job_id} failed: {str(e)}')
            await self._event_bus_manager.publish(event_type='media_processor/batch_failed', source='batch_processor', payload={'job_id': job_id, 'error': str(e), 'stats': {'total': results['total_files'], 'processed': results['processed_files'], 'failed': results['failed_files'], 'skipped': results['skipped_files']}})
            raise BatchProcessingError(f'Batch processing failed: {str(e)}')
        finally:
            asyncio.create_task(self._cleanup_job(job_id, delay=60))
    async def cancel_job(self, job_id: str) -> bool:
        if job_id not in self._active_jobs:
            self._logger.warning(f'Batch job {job_id} not found for cancellation')
            return False
        job_info = self._active_jobs[job_id]
        if job_info['status'] in ('completed', 'failed', 'cancelled'):
            self._logger.warning(f"Batch job {job_id} already in terminal state: {job_info['status']}")
            return False
        job_info['cancelled'] = True
        job_info['status'] = 'cancelling'
        task_id = job_info.get('task_id')
        if task_id and self._task_manager:
            try:
                result = await self._task_manager.cancel_task(task_id)
                self._logger.info(f'Cancelled task {task_id} for batch job {job_id}: {result}')
                return True
            except Exception as e:
                self._logger.error(f'Error cancelling task {task_id} for batch job {job_id}: {str(e)}')
                return False
        return False
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        if job_id not in self._active_jobs:
            raise BatchProcessingError(f'Batch job {job_id} not found')
        job_info = self._active_jobs[job_id]
        job_stats = self._job_stats.get(job_id, {})
        task_info = None
        task_id = job_info.get('task_id')
        if task_id and self._task_manager:
            try:
                task_info = await self._task_manager.get_task_info(task_id)
            except Exception as e:
                self._logger.warning(f'Error getting task info for job {job_id}: {str(e)}')
        total = job_stats.get('total', 0)
        completed = job_stats.get('completed', 0)
        failed = job_stats.get('failed', 0)
        skipped = job_stats.get('skipped', 0)
        current_index = job_stats.get('current_index', 0)
        percent_complete = 0
        if total > 0:
            percent_complete = int((completed + failed + skipped) / total * 100)
        current_item = None
        if job_info['status'] == 'running' and current_index < len(job_info['file_paths']):
            current_item = job_info['file_paths'][current_index]
        started_at = job_info.get('started_at')
        elapsed_seconds = 0
        if started_at:
            elapsed_seconds = (datetime.datetime.now() - started_at).total_seconds()
        remaining_seconds = None
        if job_info['status'] == 'running' and completed > 0 and (elapsed_seconds > 0):
            items_per_second = completed / elapsed_seconds
            if items_per_second > 0:
                remaining_items = total - (completed + failed + skipped)
                remaining_seconds = remaining_items / items_per_second
        status = {'job_id': job_id, 'status': job_info['status'], 'cancelled': job_info['cancelled'], 'started_at': job_info.get('started_at'), 'elapsed_seconds': elapsed_seconds, 'remaining_seconds': remaining_seconds, 'progress': {'total': total, 'completed': completed, 'failed': failed, 'skipped': skipped, 'percent_complete': percent_complete, 'current_item': current_item}, 'output_dir': job_info.get('output_dir'), 'task_id': task_id, 'task_info': task_info}
        return status
    async def get_active_jobs(self) -> List[str]:
        return list(self._active_jobs.keys())
    async def _cleanup_job(self, job_id: str, delay: int=60) -> None:
        if delay > 0:
            await asyncio.sleep(delay)
        if job_id in self._active_jobs:
            del self._active_jobs[job_id]
        if job_id in self._job_stats:
            del self._job_stats[job_id]
        self._logger.debug(f'Cleaned up batch job {job_id}')