from __future__ import annotations
import asyncio
import hashlib
import os
import pathlib
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Optional, Set, Tuple, Union, cast, AsyncIterator
import aiofiles
import aiofiles.os
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import FileError, ManagerInitializationError, ManagerShutdownError
class FileType(Enum):
    UNKNOWN = 'unknown'
    TEXT = 'text'
    BINARY = 'binary'
    IMAGE = 'image'
    DOCUMENT = 'document'
    AUDIO = 'audio'
    VIDEO = 'video'
    CONFIG = 'config'
    LOG = 'log'
    DATA = 'data'
    TEMP = 'temp'
    BACKUP = 'backup'
@dataclass
class FileInfo:
    path: str
    name: str
    size: int
    created_at: float
    modified_at: float
    file_type: FileType
    is_directory: bool
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
class FileManager(QorzenManager):
    def __init__(self, config_manager: Any, logger_manager: Any) -> None:
        super().__init__(name='file_manager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('file_manager')
        self._base_directory: Optional[pathlib.Path] = None
        self._temp_directory: Optional[pathlib.Path] = None
        self._plugin_data_directory: Optional[pathlib.Path] = None
        self._backup_directory: Optional[pathlib.Path] = None
        self._file_type_mapping: Dict[str, FileType] = {'.txt': FileType.TEXT, '.md': FileType.TEXT, '.csv': FileType.TEXT, '.json': FileType.TEXT, '.xml': FileType.TEXT, '.html': FileType.TEXT, '.htm': FileType.TEXT, '.css': FileType.TEXT, '.js': FileType.TEXT, '.py': FileType.TEXT, '.yaml': FileType.CONFIG, '.yml': FileType.CONFIG, '.ini': FileType.CONFIG, '.conf': FileType.CONFIG, '.cfg': FileType.CONFIG, '.toml': FileType.CONFIG, '.log': FileType.LOG, '.db': FileType.DATA, '.sqlite': FileType.DATA, '.sqlite3': FileType.DATA, '.parquet': FileType.DATA, '.avro': FileType.DATA, '.jpg': FileType.IMAGE, '.jpeg': FileType.IMAGE, '.png': FileType.IMAGE, '.gif': FileType.IMAGE, '.bmp': FileType.IMAGE, '.svg': FileType.IMAGE, '.webp': FileType.IMAGE, '.pdf': FileType.DOCUMENT, '.doc': FileType.DOCUMENT, '.docx': FileType.DOCUMENT, '.xls': FileType.DOCUMENT, '.xlsx': FileType.DOCUMENT, '.ppt': FileType.DOCUMENT, '.pptx': FileType.DOCUMENT, '.odt': FileType.DOCUMENT, '.ods': FileType.DOCUMENT, '.mp3': FileType.AUDIO, '.wav': FileType.AUDIO, '.flac': FileType.AUDIO, '.ogg': FileType.AUDIO, '.aac': FileType.AUDIO, '.mp4': FileType.VIDEO, '.avi': FileType.VIDEO, '.mkv': FileType.VIDEO, '.mov': FileType.VIDEO, '.webm': FileType.VIDEO}
        self._file_locks: Dict[str, asyncio.Lock] = {}
        self._max_concurrent_locks: int = 100
        self._locks_lock = asyncio.Lock()
    async def initialize(self) -> None:
        try:
            file_config = await self._config_manager.get('files', {})
            if not file_config:
                self._logger.error('File configuration not found in configuration')
            if not hasattr(file_config, 'base_directory'):
                self._logger.warning('No base directory specified in configuration. Using default.')
            if not hasattr(file_config, 'temp_directory'):
                self._logger.warning('No temp directory specified in configuration. Using default.')
            if not hasattr(file_config, 'plugin_data_directory'):
                self._logger.warning('No plugin data directory specified in configuration. Using default.')
            if not hasattr(file_config, 'backup_directory'):
                self._logger.warning('No backup directory specified in configuration. Using default.')
            if not hasattr(file_config, 'max_concurrent_locks'):
                self._logger.warning('No max concurrent locks specified in configuration. Using default.')
            base_dir = file_config.get('base_directory', 'data')
            temp_dir = file_config.get('temp_directory', 'data/temp')
            plugin_data_dir = file_config.get('plugin_data_directory', 'data/plugins')
            backup_dir = file_config.get('backup_directory', 'data/backups')
            self._max_concurrent_locks = file_config.get('max_concurrent_locks', 100)
            self._base_directory = pathlib.Path(base_dir).absolute()
            self._temp_directory = pathlib.Path(temp_dir).absolute()
            self._plugin_data_directory = pathlib.Path(plugin_data_dir).absolute()
            self._backup_directory = pathlib.Path(backup_dir).absolute()
            await self._create_directory(self._base_directory)
            await self._create_directory(self._temp_directory)
            await self._create_directory(self._plugin_data_directory)
            await self._create_directory(self._backup_directory)
            await self._config_manager.register_listener('files', self._on_config_changed)
            self._logger.info(f'File Manager initialized with base directory: {self._base_directory}')
            self._initialized = True
            self._healthy = True
        except Exception as e:
            self._logger.error(f'Failed to initialize File Manager: {str(e)}')
            raise ManagerInitializationError(f'Failed to initialize AsyncFileManager: {str(e)}', manager_name=self.name) from e
    async def _create_directory(self, path: pathlib.Path) -> None:
        if not path.exists():
            await aiofiles.os.makedirs(path, exist_ok=True)
    async def file_exists(self, path: str) -> bool:
        path_obj = pathlib.Path(path)
        if await aiofiles.os.path.exists(path_obj):
            return True
        else:
            return False
    def get_file_path(self, path: str, directory_type: str='base') -> pathlib.Path:
        if not self._initialized:
            raise FileError('File Manager not initialized', file_path=path)
        if directory_type == 'base':
            base_dir = self._base_directory
        elif directory_type == 'temp':
            base_dir = self._temp_directory
        elif directory_type == 'plugin_data':
            base_dir = self._plugin_data_directory
        elif directory_type == 'backup':
            base_dir = self._backup_directory
        else:
            raise FileError(f'Invalid directory type: {directory_type}', file_path=path)
        path_obj = pathlib.Path(path)
        if path_obj.is_absolute():
            for allowed_dir in [self._base_directory, self._temp_directory, self._plugin_data_directory, self._backup_directory]:
                if str(path_obj).startswith(str(allowed_dir)):
                    return path_obj
            raise FileError(f'Path is outside of allowed directories: {path}', file_path=path)
        return base_dir / path
    async def ensure_directory(self, path: str, directory_type: str='base') -> pathlib.Path:
        try:
            full_path = self.get_file_path(path, directory_type)
            await aiofiles.os.makedirs(full_path, exist_ok=True)
            return full_path
        except Exception as e:
            raise FileError(f'Failed to create directory: {str(e)}', file_path=path) from e
    async def read_text(self, path: str, directory_type: str='base') -> str:
        try:
            full_path = self.get_file_path(path, directory_type)
            lock = await self._get_file_lock(str(full_path))
            async with lock:
                async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                    return await f.read()
        except Exception as e:
            raise FileError(f'Failed to read text file: {str(e)}', file_path=str(full_path) if 'full_path' in locals() else path) from e
    async def write_text(self, path: str, content: str, directory_type: str='base', create_dirs: bool=True) -> None:
        try:
            full_path = self.get_file_path(path, directory_type)
            if create_dirs:
                await aiofiles.os.makedirs(full_path.parent, exist_ok=True)
            lock = await self._get_file_lock(str(full_path))
            async with lock:
                temp_path = str(full_path) + '.tmp'
                async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
                await aiofiles.os.replace(temp_path, full_path)
        except Exception as e:
            raise FileError(f'Failed to write text file: {str(e)}', file_path=str(full_path) if 'full_path' in locals() else path) from e
    async def read_binary(self, path: str, directory_type: str='base') -> bytes:
        try:
            full_path = self.get_file_path(path, directory_type)
            lock = await self._get_file_lock(str(full_path))
            async with lock:
                async with aiofiles.open(full_path, 'rb') as f:
                    return await f.read()
        except Exception as e:
            raise FileError(f'Failed to read binary file: {str(e)}', file_path=str(full_path) if 'full_path' in locals() else path) from e
    async def write_binary(self, path: str, content: bytes, directory_type: str='base', create_dirs: bool=True) -> None:
        try:
            full_path = self.get_file_path(path, directory_type)
            if create_dirs:
                await aiofiles.os.makedirs(full_path.parent, exist_ok=True)
            lock = await self._get_file_lock(str(full_path))
            async with lock:
                temp_path = str(full_path) + '.tmp'
                async with aiofiles.open(temp_path, 'wb') as f:
                    await f.write(content)
                await aiofiles.os.replace(temp_path, full_path)
        except Exception as e:
            raise FileError(f'Failed to write binary file: {str(e)}', file_path=str(full_path) if 'full_path' in locals() else path) from e
    async def list_files(self, path: str='', directory_type: str='base', recursive: bool=False, include_dirs: bool=True, pattern: Optional[str]=None) -> List[FileInfo]:
        try:
            full_path = self.get_file_path(path, directory_type)
            if not await aiofiles.os.path.isdir(full_path):
                raise FileError(f'Path is not a directory: {full_path}', file_path=str(full_path))
            result: List[FileInfo] = []
            async def process_path(p: pathlib.Path) -> None:
                try:
                    stat = await aiofiles.os.stat(p)
                    is_dir = await aiofiles.os.path.isdir(p)
                    if is_dir and (not include_dirs):
                        return
                    file_info = FileInfo(path=str(p), name=p.name, size=stat.st_size, created_at=stat.st_ctime, modified_at=stat.st_mtime, file_type=self._get_file_type(p), is_directory=is_dir, metadata={})
                    result.append(file_info)
                except Exception as e:
                    self._logger.warning(f'Failed to get info for {p}: {str(e)}', extra={'file_path': str(p)})
            if recursive:
                for root, dirs, files in os.walk(full_path):
                    root_path = pathlib.Path(root)
                    for file in files:
                        file_path = root_path / file
                        if pattern and (not file_path.match(pattern)):
                            continue
                        await process_path(file_path)
                    if include_dirs:
                        for dir_name in dirs:
                            dir_path = root_path / dir_name
                            if pattern and (not dir_path.match(pattern)):
                                continue
                            await process_path(dir_path)
            else:
                async for entry in aiofiles.os.scandir(full_path):
                    entry_path = pathlib.Path(entry.path)
                    if pattern and (not entry_path.match(pattern)):
                        continue
                    await process_path(entry_path)
            return result
        except FileError:
            raise
        except Exception as e:
            raise FileError(f'Failed to list directory: {str(e)}', file_path=str(full_path) if 'full_path' in locals() else path) from e
    async def get_file_info(self, path: str, directory_type: str='base') -> FileInfo:
        try:
            full_path = self.get_file_path(path, directory_type)
            if not await aiofiles.os.path.exists(full_path):
                raise FileError(f'File does not exist: {full_path}', file_path=str(full_path))
            stat = await aiofiles.os.stat(full_path)
            is_dir = await aiofiles.os.path.isdir(full_path)
            return FileInfo(path=str(full_path), name=full_path.name, size=stat.st_size, created_at=stat.st_ctime, modified_at=stat.st_mtime, file_type=self._get_file_type(full_path), is_directory=is_dir, metadata={})
        except FileError:
            raise
        except Exception as e:
            raise FileError(f'Failed to get file info: {str(e)}', file_path=str(full_path) if 'full_path' in locals() else path) from e
    async def delete_file(self, path: str, directory_type: str='base') -> None:
        try:
            full_path = self.get_file_path(path, directory_type)
            if not await aiofiles.os.path.exists(full_path):
                raise FileError(f'File does not exist: {full_path}', file_path=str(full_path))
            lock = await self._get_file_lock(str(full_path))
            async with lock:
                if await aiofiles.os.path.isdir(full_path):
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, shutil.rmtree, full_path)
                else:
                    await aiofiles.os.remove(full_path)
            await self._release_file_lock(str(full_path))
        except FileError:
            raise
        except Exception as e:
            raise FileError(f'Failed to delete file: {str(e)}', file_path=str(full_path) if 'full_path' in locals() else path) from e
    async def copy_file(self, source_path: str, dest_path: str, source_dir_type: str='base', dest_dir_type: str='base', overwrite: bool=False) -> None:
        try:
            source_full_path = self.get_file_path(source_path, source_dir_type)
            dest_full_path = self.get_file_path(dest_path, dest_dir_type)
            if not await aiofiles.os.path.exists(source_full_path):
                raise FileError(f'Source file does not exist: {source_full_path}', file_path=str(source_full_path))
            if await aiofiles.os.path.exists(dest_full_path) and (not overwrite):
                raise FileError(f'Destination file already exists: {dest_full_path}', file_path=str(dest_full_path))
            await aiofiles.os.makedirs(dest_full_path.parent, exist_ok=True)
            source_lock = await self._get_file_lock(str(source_full_path))
            dest_lock = await self._get_file_lock(str(dest_full_path))
            if id(source_lock) < id(dest_lock):
                first_lock, second_lock = (source_lock, dest_lock)
            else:
                first_lock, second_lock = (dest_lock, source_lock)
            async with first_lock:
                async with second_lock:
                    is_dir = await aiofiles.os.path.isdir(source_full_path)
                    if is_dir:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, lambda: shutil.copytree(source_full_path, dest_full_path, dirs_exist_ok=overwrite))
                    else:
                        async with aiofiles.open(source_full_path, 'rb') as src_file:
                            async with aiofiles.open(dest_full_path, 'wb') as dest_file:
                                chunk_size = 64 * 1024
                                while True:
                                    chunk = await src_file.read(chunk_size)
                                    if not chunk:
                                        break
                                    await dest_file.write(chunk)
                        source_stat = await aiofiles.os.stat(source_full_path)
                        await aiofiles.os.chmod(dest_full_path, source_stat.st_mode)
                        os.utime(dest_full_path, (source_stat.st_atime, source_stat.st_mtime))
        except FileError:
            raise
        except Exception as e:
            raise FileError(f'Failed to copy file: {str(e)}', file_path=f'{source_path} -> {dest_path}') from e
    async def move_file(self, source_path: str, dest_path: str, source_dir_type: str='base', dest_dir_type: str='base', overwrite: bool=False) -> None:
        try:
            source_full_path = self.get_file_path(source_path, source_dir_type)
            dest_full_path = self.get_file_path(dest_path, dest_dir_type)
            if not await aiofiles.os.path.exists(source_full_path):
                raise FileError(f'Source file does not exist: {source_full_path}', file_path=str(source_full_path))
            if await aiofiles.os.path.exists(dest_full_path) and (not overwrite):
                raise FileError(f'Destination file already exists: {dest_full_path}', file_path=str(dest_full_path))
            await aiofiles.os.makedirs(dest_full_path.parent, exist_ok=True)
            source_lock = await self._get_file_lock(str(source_full_path))
            dest_lock = await self._get_file_lock(str(dest_full_path))
            if id(source_lock) < id(dest_lock):
                first_lock, second_lock = (source_lock, dest_lock)
            else:
                first_lock, second_lock = (dest_lock, source_lock)
            async with first_lock:
                async with second_lock:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, shutil.move, str(source_full_path), str(dest_full_path))
            await self._release_file_lock(str(source_full_path))
            await self._release_file_lock(str(dest_full_path))
        except FileError:
            raise
        except Exception as e:
            raise FileError(f'Failed to move file: {str(e)}', file_path=f'{source_path} -> {dest_path}') from e
    async def create_backup(self, path: str, directory_type: str='base') -> str:
        try:
            source_full_path = self.get_file_path(path, directory_type)
            if not await aiofiles.os.path.exists(source_full_path):
                raise FileError(f'Source file does not exist: {source_full_path}', file_path=str(source_full_path))
            backup_name = f'{source_full_path.stem}_{int(time.time())}{source_full_path.suffix}'
            rel_path = None
            if directory_type == 'base':
                rel_path = source_full_path.relative_to(self._base_directory)
            elif directory_type == 'temp':
                rel_path = source_full_path.relative_to(self._temp_directory)
            elif directory_type == 'plugin_data':
                rel_path = source_full_path.relative_to(self._plugin_data_directory)
            elif directory_type == 'backup':
                rel_path = source_full_path.relative_to(self._backup_directory)
            backup_path = rel_path.parent / backup_name
            await self.copy_file(source_path=str(source_full_path), dest_path=str(backup_path), source_dir_type=directory_type, dest_dir_type='backup', overwrite=True)
            return str(backup_path)
        except FileError:
            raise
        except Exception as e:
            raise FileError(f'Failed to create backup: {str(e)}', file_path=path) from e
    async def create_temp_file(self, prefix: str='', suffix: str='') -> Tuple[str, BinaryIO]:
        try:
            temp_name = f'{prefix}{int(time.time())}_{os.urandom(4).hex()}{suffix}'
            temp_path = self.get_file_path(temp_name, 'temp')
            await aiofiles.os.makedirs(temp_path.parent, exist_ok=True)
            file_obj = open(temp_path, 'wb+')
            return (str(temp_path), file_obj)
        except Exception as e:
            raise FileError(f'Failed to create temporary file: {str(e)}', file_path=temp_name if 'temp_name' in locals() else f'{prefix}*{suffix}') from e
    async def compute_file_hash(self, path: str, directory_type: str='base') -> str:
        try:
            full_path = self.get_file_path(path, directory_type)
            if not await aiofiles.os.path.exists(full_path):
                raise FileError(f'Cannot compute hash for non-existent file: {full_path}', file_path=str(full_path))
            is_dir = await aiofiles.os.path.isdir(full_path)
            if is_dir:
                raise FileError(f'Cannot compute hash for directory: {full_path}', file_path=str(full_path))
            lock = await self._get_file_lock(str(full_path))
            async with lock:
                hasher = hashlib.sha256()
                async with aiofiles.open(full_path, 'rb') as f:
                    chunk_size = 64 * 1024
                    while True:
                        chunk = await f.read(chunk_size)
                        if not chunk:
                            break
                        hasher.update(chunk)
                return hasher.hexdigest()
        except FileError:
            raise
        except Exception as e:
            raise FileError(f'Failed to compute file hash: {str(e)}', file_path=str(full_path) if 'full_path' in locals() else path) from e
    def _get_file_type(self, path: pathlib.Path) -> FileType:
        if path.is_dir():
            return FileType.UNKNOWN
        extension = path.suffix.lower()
        return self._file_type_mapping.get(extension, FileType.UNKNOWN)
    async def _get_file_lock(self, path: str) -> asyncio.Lock:
        async with self._locks_lock:
            if self._max_concurrent_locks < len(self._file_locks):
                raise Exception('max_concurrent_locks_count', 'max_concurrent_locks_count')
            if path not in self._file_locks:
                self._file_locks[path] = asyncio.Lock()
            return self._file_locks[path]
    async def _release_file_lock(self, path: str) -> None:
        async with self._locks_lock:
            if path in self._file_locks:
                if not os.path.exists(path):
                    del self._file_locks[path]
    async def _on_config_changed(self, key: str, value: Any) -> None:
        if key.startswith('files.'):
            self._logger.warning(f'Configuration change to {key} requires restart to take full effect')
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            self._logger.info('Shutting down File Manager')
            async with self._locks_lock:
                self._file_locks.clear()
            await self._config_manager.unregister_listener('files', self._on_config_changed)
            self._initialized = False
            self._healthy = False
            self._logger.info('File Manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down File Manager: {str(e)}')
            raise ManagerShutdownError(f'Failed to shut down AsyncFileManager: {str(e)}', manager_name=self.name) from e
    def status(self) -> Dict[str, Any]:
        status = super().status()
        if self._initialized:
            try:
                total, used, free = shutil.disk_usage(self._base_directory)
                disk_percent = used / total * 100 if total > 0 else 0
            except:
                total = used = free = 0
                disk_percent = 0
            lock_count = len(self._file_locks)
            status.update({'directories': {'base': str(self._base_directory), 'temp': str(self._temp_directory), 'plugin_data': str(self._plugin_data_directory), 'backup': str(self._backup_directory)}, 'disk_usage': {'total_gb': round(total / 1024 ** 3, 2), 'used_gb': round(used / 1024 ** 3, 2), 'free_gb': round(free / 1024 ** 3, 2), 'percent_used': round(disk_percent, 2)}, 'active_locks': lock_count})
        return status