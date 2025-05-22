from __future__ import annotations
import abc
import importlib
import inspect
import os
import sys
import asyncio
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, Union, cast
from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError
class CloudProvider(str, Enum):
    NONE = 'none'
    AWS = 'aws'
    AZURE = 'azure'
    GCP = 'gcp'
class StorageBackend(str, Enum):
    LOCAL = 'local'
    S3 = 's3'
    AZURE_BLOB = 'azure_blob'
    GCP_STORAGE = 'gcp_storage'
T = TypeVar('T')
class CloudService(Protocol):
    async def initialize(self) -> None:
        ...
    async def shutdown(self) -> None:
        ...
    async def status(self) -> Dict[str, Any]:
        ...
class CloudStorageService(Protocol):
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        ...
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        ...
    async def delete_file(self, remote_path: str) -> bool:
        ...
    async def list_files(self, remote_path: str='') -> List[Dict[str, Any]]:
        ...
class BaseCloudService(abc.ABC):
    def __init__(self, config: Dict[str, Any], logger: Any) -> None:
        self._config = config
        self._logger = logger
        self._initialized = False
    @abc.abstractmethod
    async def initialize(self) -> None:
        pass
    @abc.abstractmethod
    async def shutdown(self) -> None:
        pass
    async def status(self) -> Dict[str, Any]:
        return {'initialized': self._initialized}
class LocalStorageService(BaseCloudService):
    def __init__(self, config: Dict[str, Any], logger: Any, file_manager: Any) -> None:
        super().__init__(config, logger)
        self._file_manager = file_manager
        self._base_directory: Optional[str] = None
    async def initialize(self) -> None:
        try:
            self._base_directory = self._config.get('base_directory', 'data/storage')
            if self._file_manager:
                await self._file_manager.ensure_directory(self._base_directory)
            else:
                os.makedirs(self._base_directory, exist_ok=True)
            self._initialized = True
            self._logger.info(f'Local storage service initialized with base directory: {self._base_directory}')
        except Exception as e:
            self._logger.error(f'Failed to initialize local storage service: {str(e)}')
            raise
    async def shutdown(self) -> None:
        self._initialized = False
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        if not self._initialized:
            self._logger.error('Local storage service not initialized')
            return False
        try:
            if self._file_manager:
                await self._file_manager.copy_file(source_path=local_path, dest_path=os.path.join(self._base_directory, remote_path), source_dir_type='base', dest_dir_type='base', overwrite=True)
            else:
                import shutil
                dest_path = os.path.join(self._base_directory, remote_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: shutil.copy2(local_path, dest_path))
            return True
        except Exception as e:
            self._logger.error(f'Failed to upload file: {str(e)}')
            return False
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self._initialized:
            self._logger.error('Local storage service not initialized')
            return False
        try:
            if self._file_manager:
                await self._file_manager.copy_file(source_path=os.path.join(self._base_directory, remote_path), dest_path=local_path, source_dir_type='base', dest_dir_type='base', overwrite=True)
            else:
                import shutil
                source_path = os.path.join(self._base_directory, remote_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: shutil.copy2(source_path, local_path))
            return True
        except Exception as e:
            self._logger.error(f'Failed to download file: {str(e)}')
            return False
    async def delete_file(self, remote_path: str) -> bool:
        if not self._initialized:
            self._logger.error('Local storage service not initialized')
            return False
        try:
            if self._file_manager:
                await self._file_manager.delete_file(path=os.path.join(self._base_directory, remote_path), directory_type='base')
            else:
                path = os.path.join(self._base_directory, remote_path)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, os.remove, path)
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete file: {str(e)}')
            return False
    async def list_files(self, remote_path: str='') -> List[Dict[str, Any]]:
        if not self._initialized:
            self._logger.error('Local storage service not initialized')
            return []
        try:
            if self._file_manager:
                files = await self._file_manager.list_files(path=os.path.join(self._base_directory, remote_path), directory_type='base', recursive=True)
                return [{'name': file.name, 'path': os.path.relpath(file.path, self._base_directory), 'size': file.size, 'modified_at': file.modified_at, 'is_directory': file.is_directory} for file in files]
            else:
                loop = asyncio.get_running_loop()
                async def get_files() -> List[Dict[str, Any]]:
                    result = []
                    dir_path = os.path.join(self._base_directory, remote_path)
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, self._base_directory)
                            stat = os.stat(file_path)
                            result.append({'name': file, 'path': rel_path, 'size': stat.st_size, 'modified_at': stat.st_mtime, 'is_directory': False})
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            rel_path = os.path.relpath(dir_path, self._base_directory)
                            stat = os.stat(dir_path)
                            result.append({'name': dir_name, 'path': rel_path, 'size': 0, 'modified_at': stat.st_mtime, 'is_directory': True})
                    return result
                return await loop.run_in_executor(None, get_files)
        except Exception as e:
            self._logger.error(f'Failed to list files: {str(e)}')
            return []
    async def status(self) -> Dict[str, Any]:
        status = await super().status()
        if self._initialized:
            try:
                import shutil
                total, used, free = shutil.disk_usage(self._base_directory)
                disk_percent = used / total * 100 if total > 0 else 0
                status.update({'base_directory': self._base_directory, 'disk_usage': {'total_gb': round(total / 1024 ** 3, 2), 'used_gb': round(used / 1024 ** 3, 2), 'free_gb': round(free / 1024 ** 3, 2), 'percent_used': round(disk_percent, 2)}})
            except Exception:
                pass
        return status
class AWSStorageService(BaseCloudService):
    def __init__(self, config: Dict[str, Any], logger: Any) -> None:
        super().__init__(config, logger)
        self._s3_client = None
        self._bucket: Optional[str] = None
        self._prefix: Optional[str] = None
    async def initialize(self) -> None:
        try:
            try:
                import boto3
            except ImportError:
                self._logger.error("Failed to import boto3. Please install with 'pip install boto3'")
                raise
            self._bucket = self._config.get('bucket')
            if not self._bucket:
                raise ValueError('S3 bucket name is required')
            self._prefix = self._config.get('prefix', '')
            loop = asyncio.get_running_loop()
            self._s3_client = await loop.run_in_executor(None, lambda: boto3.client('s3', aws_access_key_id=self._config.get('aws_access_key_id'), aws_secret_access_key=self._config.get('aws_secret_access_key'), region_name=self._config.get('region_name')))
            await loop.run_in_executor(None, lambda: self._s3_client.head_bucket(Bucket=self._bucket))
            self._initialized = True
            self._logger.info(f'AWS S3 storage service initialized with bucket: {self._bucket}')
        except Exception as e:
            self._logger.error(f'Failed to initialize AWS S3 storage service: {str(e)}')
            raise
    async def shutdown(self) -> None:
        self._s3_client = None
        self._initialized = False
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        if not self._initialized or not self._s3_client:
            self._logger.error('AWS S3 storage service not initialized')
            return False
        try:
            s3_key = self._get_s3_key(remote_path)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._s3_client.upload_file(local_path, self._bucket, s3_key))
            return True
        except Exception as e:
            self._logger.error(f'Failed to upload file to S3: {str(e)}')
            return False
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self._initialized or not self._s3_client:
            self._logger.error('AWS S3 storage service not initialized')
            return False
        try:
            s3_key = self._get_s3_key(remote_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._s3_client.download_file(self._bucket, s3_key, local_path))
            return True
        except Exception as e:
            self._logger.error(f'Failed to download file from S3: {str(e)}')
            return False
    async def delete_file(self, remote_path: str) -> bool:
        if not self._initialized or not self._s3_client:
            self._logger.error('AWS S3 storage service not initialized')
            return False
        try:
            s3_key = self._get_s3_key(remote_path)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._s3_client.delete_object(Bucket=self._bucket, Key=s3_key))
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete file from S3: {str(e)}')
            return False
    async def list_files(self, remote_path: str='') -> List[Dict[str, Any]]:
        if not self._initialized or not self._s3_client:
            self._logger.error('AWS S3 storage service not initialized')
            return []
        try:
            s3_prefix = self._get_s3_key(remote_path)
            if s3_prefix and (not s3_prefix.endswith('/')):
                s3_prefix += '/'
            result = []
            loop = asyncio.get_running_loop()
            paginator = self._s3_client.get_paginator('list_objects_v2')
            async def process_pages():
                for page in paginator.paginate(Bucket=self._bucket, Prefix=s3_prefix):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            if obj['Key'] == s3_prefix:
                                continue
                            is_directory = obj['Key'].endswith('/')
                            rel_path = self._get_relative_path(obj['Key'])
                            result.append({'name': os.path.basename(rel_path.rstrip('/')), 'path': rel_path, 'size': obj['Size'], 'modified_at': obj['LastModified'].timestamp(), 'is_directory': is_directory, 'etag': obj.get('ETag', '').strip('"')})
            await loop.run_in_executor(None, process_pages)
            return result
        except Exception as e:
            self._logger.error(f'Failed to list files in S3: {str(e)}')
            return []
    def _get_s3_key(self, path: str) -> str:
        path = path.strip('/')
        if self._prefix:
            return f"{self._prefix.strip('/')}/{path}" if path else self._prefix.strip('/')
        return path
    def _get_relative_path(self, s3_key: str) -> str:
        if self._prefix:
            prefix = self._prefix.strip('/')
            if s3_key.startswith(prefix):
                return s3_key[len(prefix):].lstrip('/')
        return s3_key
    async def status(self) -> Dict[str, Any]:
        status = await super().status()
        if self._initialized:
            status.update({'bucket': self._bucket, 'prefix': self._prefix, 'region': self._config.get('region_name')})
        return status
class AzureBlobStorageService(BaseCloudService):
    def __init__(self, config: Dict[str, Any], logger: Any) -> None:
        super().__init__(config, logger)
        self._blob_service_client = None
        self._container_client = None
        self._container: Optional[str] = None
        self._prefix: Optional[str] = None
    async def initialize(self) -> None:
        try:
            try:
                from azure.storage.blob import BlobServiceClient
            except ImportError:
                self._logger.error("Failed to import azure-storage-blob. Please install with 'pip install azure-storage-blob'")
                raise
            connection_string = self._config.get('connection_string')
            account_name = self._config.get('account_name')
            account_key = self._config.get('account_key')
            if not connection_string and (not (account_name and account_key)):
                raise ValueError('Either connection_string or account_name and account_key must be provided')
            self._container = self._config.get('container')
            if not self._container:
                raise ValueError('Azure Blob Storage container name is required')
            self._prefix = self._config.get('prefix', '')
            loop = asyncio.get_running_loop()
            if connection_string:
                self._blob_service_client = await loop.run_in_executor(None, lambda: BlobServiceClient.from_connection_string(connection_string))
            else:
                from azure.storage.blob import BlobServiceClient
                account_url = f'https://{account_name}.blob.core.windows.net'
                self._blob_service_client = await loop.run_in_executor(None, lambda: BlobServiceClient(account_url=account_url, credential=account_key))
            self._container_client = await loop.run_in_executor(None, lambda: self._blob_service_client.get_container_client(self._container))
            container_exists = await loop.run_in_executor(None, lambda: self._container_client.exists())
            if not container_exists:
                await loop.run_in_executor(None, lambda: self._container_client.create_container())
            self._initialized = True
            self._logger.info(f'Azure Blob Storage service initialized with container: {self._container}')
        except Exception as e:
            self._logger.error(f'Failed to initialize Azure Blob Storage service: {str(e)}')
            raise
    async def shutdown(self) -> None:
        if self._blob_service_client:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._blob_service_client.close())
        self._blob_service_client = None
        self._container_client = None
        self._initialized = False
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        if not self._initialized or not self._container_client:
            self._logger.error('Azure Blob Storage service not initialized')
            return False
        try:
            blob_name = self._get_blob_name(remote_path)
            loop = asyncio.get_running_loop()
            blob_client = await loop.run_in_executor(None, lambda: self._container_client.get_blob_client(blob_name))
            async def upload_blob():
                with open(local_path, 'rb') as data:
                    blob_client.upload_blob(data, overwrite=True)
            await loop.run_in_executor(None, upload_blob)
            return True
        except Exception as e:
            self._logger.error(f'Failed to upload file to Azure Blob Storage: {str(e)}')
            return False
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self._initialized or not self._container_client:
            self._logger.error('Azure Blob Storage service not initialized')
            return False
        try:
            blob_name = self._get_blob_name(remote_path)
            loop = asyncio.get_running_loop()
            blob_client = await loop.run_in_executor(None, lambda: self._container_client.get_blob_client(blob_name))
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            async def download_blob():
                with open(local_path, 'wb') as download_file:
                    blob_data = blob_client.download_blob()
                    download_file.write(blob_data.readall())
            await loop.run_in_executor(None, download_blob)
            return True
        except Exception as e:
            self._logger.error(f'Failed to download file from Azure Blob Storage: {str(e)}')
            return False
    async def delete_file(self, remote_path: str) -> bool:
        if not self._initialized or not self._container_client:
            self._logger.error('Azure Blob Storage service not initialized')
            return False
        try:
            blob_name = self._get_blob_name(remote_path)
            loop = asyncio.get_running_loop()
            blob_client = await loop.run_in_executor(None, lambda: self._container_client.get_blob_client(blob_name))
            await loop.run_in_executor(None, lambda: blob_client.delete_blob())
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete file from Azure Blob Storage: {str(e)}')
            return False
    async def list_files(self, remote_path: str='') -> List[Dict[str, Any]]:
        if not self._initialized or not self._container_client:
            self._logger.error('Azure Blob Storage service not initialized')
            return []
        try:
            blob_prefix = self._get_blob_name(remote_path)
            if blob_prefix and (not blob_prefix.endswith('/')):
                blob_prefix += '/'
            result = []
            loop = asyncio.get_running_loop()
            async def list_blobs():
                blobs = self._container_client.list_blobs(name_starts_with=blob_prefix)
                for blob in blobs:
                    if blob.name == blob_prefix:
                        continue
                    is_directory = blob.name.endswith('/')
                    rel_path = self._get_relative_path(blob.name)
                    result.append({'name': os.path.basename(rel_path.rstrip('/')), 'path': rel_path, 'size': blob.size, 'modified_at': blob.last_modified.timestamp(), 'is_directory': is_directory, 'etag': blob.etag})
            await loop.run_in_executor(None, list_blobs)
            return result
        except Exception as e:
            self._logger.error(f'Failed to list files in Azure Blob Storage: {str(e)}')
            return []
    def _get_blob_name(self, path: str) -> str:
        path = path.strip('/')
        if self._prefix:
            return f"{self._prefix.strip('/')}/{path}" if path else self._prefix.strip('/')
        return path
    def _get_relative_path(self, blob_name: str) -> str:
        if self._prefix:
            prefix = self._prefix.strip('/')
            if blob_name.startswith(prefix):
                return blob_name[len(prefix):].lstrip('/')
        return blob_name
    async def status(self) -> Dict[str, Any]:
        status = await super().status()
        if self._initialized:
            status.update({'container': self._container, 'prefix': self._prefix, 'account_name': self._config.get('account_name')})
        return status
class GCPStorageService(BaseCloudService):
    def __init__(self, config: Dict[str, Any], logger: Any) -> None:
        super().__init__(config, logger)
        self._storage_client = None
        self._bucket_client = None
        self._bucket: Optional[str] = None
        self._prefix: Optional[str] = None
    async def initialize(self) -> None:
        try:
            try:
                from google.cloud import storage
            except ImportError:
                self._logger.error("Failed to import google-cloud-storage. Please install with 'pip install google-cloud-storage'")
                raise
            self._bucket = self._config.get('bucket')
            if not self._bucket:
                raise ValueError('GCP Storage bucket name is required')
            self._prefix = self._config.get('prefix', '')
            loop = asyncio.get_running_loop()
            self._storage_client = await loop.run_in_executor(None, lambda: storage.Client())
            self._bucket_client = await loop.run_in_executor(None, lambda: self._storage_client.bucket(self._bucket))
            bucket_exists = await loop.run_in_executor(None, lambda: self._bucket_client.exists())
            if not bucket_exists:
                raise ValueError(f'GCP Storage bucket {self._bucket} does not exist')
            self._initialized = True
            self._logger.info(f'GCP Storage service initialized with bucket: {self._bucket}')
        except Exception as e:
            self._logger.error(f'Failed to initialize GCP Storage service: {str(e)}')
            raise
    async def shutdown(self) -> None:
        self._storage_client = None
        self._bucket_client = None
        self._initialized = False
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        if not self._initialized or not self._bucket_client:
            self._logger.error('GCP Storage service not initialized')
            return False
        try:
            blob_name = self._get_blob_name(remote_path)
            loop = asyncio.get_running_loop()
            blob = await loop.run_in_executor(None, lambda: self._bucket_client.blob(blob_name))
            await loop.run_in_executor(None, lambda: blob.upload_from_filename(local_path))
            return True
        except Exception as e:
            self._logger.error(f'Failed to upload file to GCP Storage: {str(e)}')
            return False
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self._initialized or not self._bucket_client:
            self._logger.error('GCP Storage service not initialized')
            return False
        try:
            blob_name = self._get_blob_name(remote_path)
            loop = asyncio.get_running_loop()
            blob = await loop.run_in_executor(None, lambda: self._bucket_client.blob(blob_name))
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            await loop.run_in_executor(None, lambda: blob.download_to_filename(local_path))
            return True
        except Exception as e:
            self._logger.error(f'Failed to download file from GCP Storage: {str(e)}')
            return False
    async def delete_file(self, remote_path: str) -> bool:
        if not self._initialized or not self._bucket_client:
            self._logger.error('GCP Storage service not initialized')
            return False
        try:
            blob_name = self._get_blob_name(remote_path)
            loop = asyncio.get_running_loop()
            blob = await loop.run_in_executor(None, lambda: self._bucket_client.blob(blob_name))
            await loop.run_in_executor(None, lambda: blob.delete())
            return True
        except Exception as e:
            self._logger.error(f'Failed to delete file from GCP Storage: {str(e)}')
            return False
    async def list_files(self, remote_path: str='') -> List[Dict[str, Any]]:
        if not self._initialized or not self._bucket_client:
            self._logger.error('GCP Storage service not initialized')
            return []
        try:
            blob_prefix = self._get_blob_name(remote_path)
            if blob_prefix and (not blob_prefix.endswith('/')):
                blob_prefix += '/'
            result = []
            loop = asyncio.get_running_loop()
            async def list_blobs():
                blobs = self._bucket_client.list_blobs(prefix=blob_prefix)
                for blob in blobs:
                    if blob.name == blob_prefix:
                        continue
                    is_directory = blob.name.endswith('/')
                    rel_path = self._get_relative_path(blob.name)
                    result.append({'name': os.path.basename(rel_path.rstrip('/')), 'path': rel_path, 'size': blob.size, 'modified_at': blob.updated.timestamp() if blob.updated else None, 'is_directory': is_directory, 'etag': blob.etag})
            await loop.run_in_executor(None, list_blobs)
            return result
        except Exception as e:
            self._logger.error(f'Failed to list files in GCP Storage: {str(e)}')
            return []
    def _get_blob_name(self, path: str) -> str:
        path = path.strip('/')
        if self._prefix:
            return f"{self._prefix.strip('/')}/{path}" if path else self._prefix.strip('/')
        return path
    def _get_relative_path(self, blob_name: str) -> str:
        if self._prefix:
            prefix = self._prefix.strip('/')
            if blob_name.startswith(prefix):
                return blob_name[len(prefix):].lstrip('/')
        return blob_name
    async def status(self) -> Dict[str, Any]:
        status = await super().status()
        if self._initialized:
            status.update({'bucket': self._bucket, 'prefix': self._prefix, 'project': self._storage_client.project if self._storage_client else None})
        return status
class CloudManager(QorzenManager):
    def __init__(self, config_manager: Any, logger_manager: Any, file_manager: Optional[Any]=None) -> None:
        super().__init__(name='cloud_manager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('cloud_manager')
        self._file_manager = file_manager
        self._provider = CloudProvider.NONE
        self._storage_backend = StorageBackend.LOCAL
        self._storage_service: Optional[CloudStorageService] = None
        self._services: Dict[str, CloudService] = {}
    async def initialize(self) -> None:
        try:
            cloud_config = await self._config_manager.get('cloud', {})
            if not cloud_config:
                self._logger.error('Cloud configuration not found in configuration')
            provider_str = cloud_config.get('provider', 'none').lower()
            try:
                self._provider = CloudProvider(provider_str)
            except ValueError:
                self._logger.warning(f'Invalid cloud provider: {provider_str}, defaulting to NONE')
                self._provider = CloudProvider.NONE
            if not hasattr(cloud_config, 'storage'):
                self._logger.warning('Cloud storage configuration not found in configuration')
            if not hasattr(cloud_config, 'enabled'):
                self._logger.warning('Cloud storage enabled flag not found in configuration')
            storage_config = cloud_config.get('storage', {})
            storage_enabled = storage_config.get('enabled', False)
            if storage_enabled:
                if not hasattr(storage_config, 'type'):
                    self._logger.warning('Cloud storage type not found in configuration')
                storage_type = storage_config.get('type', 'local').lower()
                try:
                    self._storage_backend = StorageBackend(storage_type)
                except ValueError:
                    self._logger.warning(f'Invalid storage backend: {storage_type}, defaulting to LOCAL')
                    self._storage_backend = StorageBackend.LOCAL
                await self._initialize_storage_service(storage_config)
            await self._config_manager.register_listener('cloud', self._on_config_changed)
            self._initialized = True
            self._healthy = True
            self._logger.info(f'Cloud Manager initialized with provider: {self._provider.value}, storage backend: {self._storage_backend.value}')
        except Exception as e:
            self._logger.error(f'Failed to initialize Cloud Manager: {str(e)}')
            raise ManagerInitializationError(f'Failed to initialize CloudManager: {str(e)}', manager_name=self.name) from e
    async def _initialize_storage_service(self, config: Dict[str, Any]) -> None:
        if self._storage_backend == StorageBackend.LOCAL:
            self._storage_service = LocalStorageService(config, self._logger, self._file_manager)
        elif self._storage_backend == StorageBackend.S3:
            self._storage_service = AWSStorageService(config, self._logger)
        elif self._storage_backend == StorageBackend.AZURE_BLOB:
            self._storage_service = AzureBlobStorageService(config, self._logger)
        elif self._storage_backend == StorageBackend.GCP_STORAGE:
            self._storage_service = GCPStorageService(config, self._logger)
        else:
            raise ValueError(f'Unsupported storage backend: {self._storage_backend}')
        await self._storage_service.initialize()
        self._services['storage'] = self._storage_service
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        if not self._initialized:
            raise ValueError('Cloud Manager not initialized')
        if not self._storage_service:
            raise ValueError('Cloud storage not enabled or initialized')
        return await self._storage_service.upload_file(local_path, remote_path)
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self._initialized:
            raise ValueError('Cloud Manager not initialized')
        if not self._storage_service:
            raise ValueError('Cloud storage not enabled or initialized')
        return await self._storage_service.download_file(remote_path, local_path)
    async def delete_file(self, remote_path: str) -> bool:
        if not self._initialized:
            raise ValueError('Cloud Manager not initialized')
        if not self._storage_service:
            raise ValueError('Cloud storage not enabled or initialized')
        return await self._storage_service.delete_file(remote_path)
    async def list_files(self, remote_path: str='') -> List[Dict[str, Any]]:
        if not self._initialized:
            raise ValueError('Cloud Manager not initialized')
        if not self._storage_service:
            raise ValueError('Cloud storage not enabled or initialized')
        return await self._storage_service.list_files(remote_path)
    def is_cloud_provider(self, provider: Union[str, CloudProvider]) -> bool:
        if not self._initialized:
            return False
        if isinstance(provider, str):
            try:
                provider = CloudProvider(provider.lower())
            except ValueError:
                return False
        return self._provider == provider
    def get_cloud_provider(self) -> str:
        if not self._initialized:
            return 'unknown'
        return self._provider.value
    def get_storage_backend(self) -> str:
        if not self._initialized:
            return 'unknown'
        return self._storage_backend.value
    async def get_service(self, service_name: str) -> Optional[CloudService]:
        if not self._initialized:
            return None
        return self._services.get(service_name)
    async def _on_config_changed(self, key: str, value: Any) -> None:
        if key.startswith('cloud.'):
            self._logger.warning(f'Configuration change to {key} requires restart to take effect', extra={'key': key})
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            self._logger.info('Shutting down Cloud Manager')
            for service_name, service in list(self._services.items()):
                try:
                    await service.shutdown()
                    self._logger.debug(f'Shut down {service_name} service')
                except Exception as e:
                    self._logger.error(f'Failed to shut down {service_name} service: {str(e)}')
            self._services.clear()
            self._storage_service = None
            await self._config_manager.unregister_listener('cloud', self._on_config_changed)
            self._initialized = False
            self._healthy = False
            self._logger.info('Cloud Manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down Cloud Manager: {str(e)}')
            raise ManagerShutdownError(f'Failed to shut down CloudManager: {str(e)}', manager_name=self.name) from e
    async def status(self) -> Dict[str, Any]:
        status = await super().status()
        if self._initialized:
            service_statuses = {}
            for service_name, service in self._services.items():
                service_statuses[service_name] = await service.status()
            status.update({'provider': self._provider.value, 'storage': {'backend': self._storage_backend.value, 'enabled': self._storage_service is not None}, 'services': service_statuses})
        return status