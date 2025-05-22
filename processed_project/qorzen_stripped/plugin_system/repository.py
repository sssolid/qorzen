from __future__ import annotations
import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import httpx
from qorzen.plugin_system.manifest import PluginManifest
from qorzen.plugin_system.package import PluginPackage, PackageFormat
class PluginRepositoryError(Exception):
    pass
class PluginSearchResult:
    def __init__(self, name: str, display_name: str, version: str, description: str, author: str, downloads: int=0, rating: float=0.0, capabilities: Optional[List[str]]=None, tags: Optional[List[str]]=None) -> None:
        self.name = name
        self.display_name = display_name
        self.version = version
        self.description = description
        self.author = author
        self.downloads = downloads
        self.rating = rating
        self.capabilities = capabilities or []
        self.tags = tags or []
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PluginSearchResult:
        return cls(name=data['name'], display_name=data.get('display_name', data['name']), version=data['version'], description=data.get('description', ''), author=data.get('author', 'Unknown'), downloads=data.get('downloads', 0), rating=data.get('rating', 0.0), capabilities=data.get('capabilities', []), tags=data.get('tags', []))
    def to_dict(self) -> Dict[str, Any]:
        return {'name': self.name, 'display_name': self.display_name, 'version': self.version, 'description': self.description, 'author': self.author, 'downloads': self.downloads, 'rating': self.rating, 'capabilities': self.capabilities, 'tags': self.tags}
class PluginVersionInfo:
    def __init__(self, name: str, version: str, release_date: datetime.datetime, release_notes: str, download_url: str, size_bytes: int, sha256: str, dependencies: Optional[List[Dict[str, str]]]=None) -> None:
        self.name = name
        self.version = version
        self.release_date = release_date
        self.release_notes = release_notes
        self.download_url = download_url
        self.size_bytes = size_bytes
        self.sha256 = sha256
        self.dependencies = dependencies or []
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PluginVersionInfo:
        return cls(name=data['name'], version=data['version'], release_date=datetime.datetime.fromisoformat(data['release_date']), release_notes=data.get('release_notes', ''), download_url=data['download_url'], size_bytes=data.get('size_bytes', 0), sha256=data.get('sha256', ''), dependencies=data.get('dependencies', []))
    def to_dict(self) -> Dict[str, Any]:
        return {'name': self.name, 'version': self.version, 'release_date': self.release_date.isoformat(), 'release_notes': self.release_notes, 'download_url': self.download_url, 'size_bytes': self.size_bytes, 'sha256': self.sha256, 'dependencies': self.dependencies}
class PluginRepository:
    def __init__(self, name: str, url: str, api_key: Optional[str]=None, timeout: float=30.0, logger: Optional[Callable[[str, str], None]]=None) -> None:
        self.name = name
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logger or (lambda msg, level: print(f'[{level.upper()}] {msg}'))
        self._client = httpx.Client(timeout=timeout)
    def __del__(self) -> None:
        self._client.close()
    def log(self, message: str, level: str='info') -> None:
        self.logger(message, level)
    def search(self, query: str='', tags: Optional[List[str]]=None, sort_by: str='relevance', limit: int=20, offset: int=0) -> List[PluginSearchResult]:
        try:
            params = {'q': query, 'sort': sort_by, 'limit': limit, 'offset': offset}
            if tags:
                params['tags'] = ','.join(tags)
            headers = self._get_headers()
            response = self._client.get(f'{self.url}/api/v1/plugins', params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get('results', []):
                try:
                    result = PluginSearchResult.from_dict(item)
                    results.append(result)
                except Exception as e:
                    self.log(f'Error parsing search result: {e}', 'warning')
            return results
        except httpx.RequestError as e:
            raise PluginRepositoryError(f'Failed to connect to repository: {e}')
        except httpx.HTTPStatusError as e:
            raise PluginRepositoryError(f'Repository returned error: {e.response.status_code} - {e.response.text}')
        except Exception as e:
            raise PluginRepositoryError(f'Failed to search repository: {e}')
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        try:
            headers = self._get_headers()
            response = self._client.get(f'{self.url}/api/v1/plugins/{plugin_name}', headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise PluginRepositoryError(f'Failed to connect to repository: {e}')
        except httpx.HTTPStatusError as e:
            raise PluginRepositoryError(f'Repository returned error: {e.response.status_code} - {e.response.text}')
        except Exception as e:
            raise PluginRepositoryError(f'Failed to get plugin info: {e}')
    def get_plugin_versions(self, plugin_name: str) -> List[PluginVersionInfo]:
        try:
            headers = self._get_headers()
            response = self._client.get(f'{self.url}/api/v1/plugins/{plugin_name}/versions', headers=headers)
            response.raise_for_status()
            data = response.json()
            versions = []
            for item in data.get('versions', []):
                try:
                    version = PluginVersionInfo.from_dict(item)
                    versions.append(version)
                except Exception as e:
                    self.log(f'Error parsing version info: {e}', 'warning')
            return versions
        except httpx.RequestError as e:
            raise PluginRepositoryError(f'Failed to connect to repository: {e}')
        except httpx.HTTPStatusError as e:
            raise PluginRepositoryError(f'Repository returned error: {e.response.status_code} - {e.response.text}')
        except Exception as e:
            raise PluginRepositoryError(f'Failed to get plugin versions: {e}')
    def download_plugin(self, plugin_name: str, version: Optional[str]=None, output_path: Optional[Union[str, Path]]=None) -> Path:
        try:
            if version:
                download_url = self._get_version_download_url(plugin_name, version)
            else:
                versions = self.get_plugin_versions(plugin_name)
                if not versions:
                    raise PluginRepositoryError(f'No versions available for plugin {plugin_name}')
                versions.sort(key=lambda v: v.release_date, reverse=True)
                download_url = versions[0].download_url
                version = versions[0].version
            if output_path is None:
                output_path = Path(f'{plugin_name}-{version}.zip')
            else:
                output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            headers = self._get_headers()
            self.log(f'Downloading plugin {plugin_name} v{version} from {download_url}', 'debug')
            with self._client.stream('GET', download_url, headers=headers) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 1024 * 1024:
                            percent = downloaded / total_size * 100 if total_size > 0 else 0
                            self.log(f'Download progress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB)', 'debug')
            if version:
                try:
                    version_info = self._get_version_info(plugin_name, version)
                    if version_info and version_info.sha256:
                        self.log(f'Verifying download hash', 'debug')
                        file_hash = self._calculate_file_hash(output_path)
                        if file_hash != version_info.sha256:
                            raise PluginRepositoryError(f'Hash verification failed. Expected {version_info.sha256}, got {file_hash}')
                except Exception as e:
                    self.log(f'Hash verification error: {e}', 'warning')
            self.log(f'Downloaded plugin {plugin_name} v{version} to {output_path}')
            return output_path
        except httpx.RequestError as e:
            raise PluginRepositoryError(f'Failed to connect to repository: {e}')
        except httpx.HTTPStatusError as e:
            raise PluginRepositoryError(f'Repository returned error: {e.response.status_code} - {e.response.text}')
        except Exception as e:
            if isinstance(e, PluginRepositoryError):
                raise
            raise PluginRepositoryError(f'Failed to download plugin: {e}')
    def publish_plugin(self, package_path: Union[str, Path], release_notes: str='', public: bool=True) -> Dict[str, Any]:
        if not self.api_key:
            raise PluginRepositoryError('API key required for publishing')
        try:
            package_path = Path(package_path)
            package = PluginPackage.load(package_path)
            if not package.manifest:
                raise PluginRepositoryError('Package has no manifest')
            file_hash = self._calculate_file_hash(package_path)
            metadata = {'name': package.manifest.name, 'version': package.manifest.version, 'display_name': package.manifest.display_name, 'description': package.manifest.description, 'author': package.manifest.author.name, 'release_notes': release_notes, 'public': public, 'sha256': file_hash}
            headers = self._get_headers()
            response = self._client.post(f'{self.url}/api/v1/plugins/upload', json=metadata, headers=headers)
            response.raise_for_status()
            upload_data = response.json()
            upload_url = upload_data.get('upload_url')
            if not upload_url:
                raise PluginRepositoryError('No upload URL provided by repository')
            with open(package_path, 'rb') as f:
                files = {'file': (package_path.name, f, 'application/zip')}
                upload_response = self._client.post(upload_url, files=files, headers=headers)
                upload_response.raise_for_status()
            publish_response = self._client.post(f'{self.url}/api/v1/plugins/{package.manifest.name}/versions/{package.manifest.version}/publish', headers=headers)
            publish_response.raise_for_status()
            return publish_response.json()
        except httpx.RequestError as e:
            raise PluginRepositoryError(f'Failed to connect to repository: {e}')
        except httpx.HTTPStatusError as e:
            raise PluginRepositoryError(f'Repository returned error: {e.response.status_code} - {e.response.text}')
        except Exception as e:
            if isinstance(e, PluginRepositoryError):
                raise
            raise PluginRepositoryError(f'Failed to publish plugin: {e}')
    def _get_headers(self) -> Dict[str, str]:
        headers = {'User-Agent': 'QorzenPluginClient/0.1.0', 'Accept': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    def _get_version_download_url(self, plugin_name: str, version: str) -> str:
        version_info = self._get_version_info(plugin_name, version)
        if not version_info:
            raise PluginRepositoryError(f'Version {version} not found for plugin {plugin_name}')
        return version_info.download_url
    def _get_version_info(self, plugin_name: str, version: str) -> Optional[PluginVersionInfo]:
        versions = self.get_plugin_versions(plugin_name)
        for ver in versions:
            if ver.version == version:
                return ver
        return None
    @staticmethod
    def _calculate_file_hash(path: Path) -> str:
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
class PluginRepositoryManager:
    def __init__(self, config_file: Optional[Union[str, Path]]=None, logger: Optional[Callable[[str, str], None]]=None) -> None:
        self.repositories: Dict[str, PluginRepository] = {}
        self.default_repository: Optional[str] = None
        self.logger = logger or (lambda msg, level: print(f'[{level.upper()}] {msg}'))
        if config_file:
            self.load_config(config_file)
    def log(self, message: str, level: str='info') -> None:
        self.logger(message, level)
    def load_config(self, config_file: Union[str, Path]) -> None:
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                raise PluginRepositoryError(f'Configuration file not found: {config_path}')
            with open(config_path, 'r') as f:
                config = json.load(f)
            repositories = config.get('repositories', [])
            for repo_config in repositories:
                name = repo_config.get('name')
                url = repo_config.get('url')
                if not name or not url:
                    self.log(f'Invalid repository configuration: {repo_config}', 'warning')
                    continue
                repository = PluginRepository(name=name, url=url, api_key=repo_config.get('api_key'), timeout=repo_config.get('timeout', 30.0), logger=self.logger)
                self.add_repository(repository)
            self.default_repository = config.get('default_repository')
            if self.default_repository and self.default_repository not in self.repositories:
                self.log(f'Default repository not found: {self.default_repository}', 'warning')
                self.default_repository = None
            if not self.default_repository and self.repositories:
                self.default_repository = next(iter(self.repositories.keys()))
            self.log(f'Loaded {len(self.repositories)} repositories from {config_path}')
        except json.JSONDecodeError as e:
            raise PluginRepositoryError(f'Invalid JSON in configuration file: {e}')
        except Exception as e:
            if isinstance(e, PluginRepositoryError):
                raise
            raise PluginRepositoryError(f'Failed to load repository configuration: {e}')
    def save_config(self, config_file: Union[str, Path]) -> None:
        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {'repositories': [], 'default_repository': self.default_repository}
            for name, repository in self.repositories.items():
                repo_config = {'name': repository.name, 'url': repository.url, 'timeout': repository.timeout}
                if repository.api_key:
                    repo_config['api_key'] = repository.api_key
                config['repositories'].append(repo_config)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            self.log(f'Saved repository configuration to {config_path}')
        except Exception as e:
            raise PluginRepositoryError(f'Failed to save repository configuration: {e}')
    def add_repository(self, repository: PluginRepository) -> None:
        if repository.name in self.repositories:
            raise PluginRepositoryError(f'Repository already exists: {repository.name}')
        self.repositories[repository.name] = repository
        if not self.default_repository:
            self.default_repository = repository.name
        self.log(f'Added repository: {repository.name} ({repository.url})')
    def remove_repository(self, name: str) -> bool:
        if name not in self.repositories:
            return False
        del self.repositories[name]
        if self.default_repository == name:
            self.default_repository = next(iter(self.repositories.keys())) if self.repositories else None
        self.log(f'Removed repository: {name}')
        return True
    def get_repository(self, name: Optional[str]=None) -> PluginRepository:
        repo_name = name or self.default_repository
        if not repo_name:
            raise PluginRepositoryError('No repository specified and no default repository set')
        if repo_name not in self.repositories:
            raise PluginRepositoryError(f'Repository not found: {repo_name}')
        return self.repositories[repo_name]
    def search(self, query: str='', tags: Optional[List[str]]=None, repository: Optional[str]=None, sort_by: str='relevance', limit: int=20, offset: int=0) -> Dict[str, List[PluginSearchResult]]:
        if not self.repositories:
            raise PluginRepositoryError('No repositories available')
        results = {}
        if repository:
            try:
                repo = self.get_repository(repository)
                results[repository] = repo.search(query=query, tags=tags, sort_by=sort_by, limit=limit, offset=offset)
            except Exception as e:
                self.log(f'Error searching repository {repository}: {e}', 'warning')
                results[repository] = []
        else:
            for name, repo in self.repositories.items():
                try:
                    repo_results = repo.search(query=query, tags=tags, sort_by=sort_by, limit=limit, offset=offset)
                    results[name] = repo_results
                except Exception as e:
                    self.log(f'Error searching repository {name}: {e}', 'warning')
                    results[name] = []
        return results
    def download_plugin(self, plugin_name: str, version: Optional[str]=None, repository: Optional[str]=None, output_path: Optional[Union[str, Path]]=None) -> Path:
        repo = self.get_repository(repository)
        return repo.download_plugin(plugin_name=plugin_name, version=version, output_path=output_path)
    def publish_plugin(self, package_path: Union[str, Path], release_notes: str='', public: bool=True, repository: Optional[str]=None) -> Dict[str, Any]:
        repo = self.get_repository(repository)
        return repo.publish_plugin(package_path=package_path, release_notes=release_notes, public=public)