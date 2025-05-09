from __future__ import annotations
import enum
import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, BinaryIO, Any
from qorzen.plugin_system.manifest import PluginManifest
class PackageFormat(str, enum.Enum):
    ZIP = 'zip'
    WHEEL = 'wheel'
    DIRECTORY = 'directory'
class PackageError(Exception):
    pass
class PluginPackage:
    MANIFEST_PATH = 'manifest.json'
    CODE_DIR = 'code'
    RESOURCES_DIR = 'resources'
    DOCS_DIR = 'docs'
    def __init__(self, manifest: Optional[PluginManifest]=None, format: PackageFormat=PackageFormat.ZIP, path: Optional[Union[str, Path]]=None) -> None:
        self.manifest = manifest
        self.format = format
        self.path = Path(path) if path else None
        self._temp_dir: Optional[Path] = None
        self._extracted_path: Optional[Path] = None
        self._file_hashes: Dict[str, str] = {}
    def __del__(self) -> None:
        self.cleanup()
    def cleanup(self) -> None:
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
            self._extracted_path = None
    @classmethod
    def create(cls, source_dir: Union[str, Path], output_path: Union[str, Path], manifest: Optional[PluginManifest]=None, format: PackageFormat=PackageFormat.ZIP, include_patterns: Optional[List[str]]=None, exclude_patterns: Optional[List[str]]=None) -> PluginPackage:
        source_dir = Path(source_dir)
        output_path = Path(output_path)
        if not source_dir.exists() or not source_dir.is_dir():
            raise PackageError(f'Source directory not found: {source_dir}')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if manifest is None:
            manifest_path = source_dir / cls.MANIFEST_PATH
            if not manifest_path.exists():
                raise PackageError(f'Manifest file not found: {manifest_path}')
            try:
                manifest = PluginManifest.load(manifest_path)
            except Exception as e:
                raise PackageError(f'Failed to load manifest: {e}')
        temp_dir = Path(tempfile.mkdtemp(prefix='qorzen_plugin_'))
        try:
            package_structure = {cls.CODE_DIR: temp_dir / cls.CODE_DIR, cls.RESOURCES_DIR: temp_dir / cls.RESOURCES_DIR, cls.DOCS_DIR: temp_dir / cls.DOCS_DIR}
            for dir_path in package_structure.values():
                dir_path.mkdir(parents=True, exist_ok=True)
            include_patterns = include_patterns or ['**/*']
            exclude_patterns = exclude_patterns or ['**/__pycache__/**', '**/*.pyc', '**/*.pyo', '**/*.pyd', '**/.git/**', '**/.vscode/**', '**/.idea/**', '**/venv/**', '**/env/**', '**/build/**', '**/dist/**', '**/*.egg-info/**']
            file_hashes = {}
            import glob
            for pattern in include_patterns:
                for file_path in source_dir.glob(pattern):
                    if file_path.is_dir():
                        continue
                    rel_path = file_path.relative_to(source_dir)
                    if any((rel_path.match(exclude) for exclude in exclude_patterns)):
                        continue
                    if cls._is_code_file(file_path):
                        dest_dir = package_structure[cls.CODE_DIR]
                    elif cls._is_resource_file(file_path):
                        dest_dir = package_structure[cls.RESOURCES_DIR]
                    elif cls._is_doc_file(file_path):
                        dest_dir = package_structure[cls.DOCS_DIR]
                    else:
                        continue
                    dest_path = dest_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)
                    file_hash = cls._calculate_file_hash(file_path)
                    file_hashes[str(rel_path)] = file_hash
            manifest_path = temp_dir / cls.MANIFEST_PATH
            manifest.save(manifest_path)
            hash_path = temp_dir / 'files.json'
            with open(hash_path, 'w') as f:
                json.dump(file_hashes, f, indent=2)
            if format == PackageFormat.ZIP:
                cls._create_zip_package(temp_dir, output_path)
            elif format == PackageFormat.WHEEL:
                cls._create_wheel_package(temp_dir, output_path, manifest)
            elif format == PackageFormat.DIRECTORY:
                if output_path.exists() and output_path.is_dir():
                    shutil.rmtree(output_path)
                shutil.copytree(temp_dir, output_path)
            else:
                raise PackageError(f'Unsupported package format: {format}')
            package = cls(manifest=manifest, format=format, path=output_path)
            package._file_hashes = file_hashes
            return package
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    @classmethod
    def load(cls, path: Union[str, Path]) -> PluginPackage:
        path = Path(path)
        if not path.exists():
            raise PackageError(f'Package not found: {path}')
        if path.is_dir():
            format = PackageFormat.DIRECTORY
        elif path.suffix.lower() == '.zip':
            format = PackageFormat.ZIP
        elif path.suffix.lower() == '.whl':
            format = PackageFormat.WHEEL
        else:
            raise PackageError(f'Unsupported package format: {path}')
        temp_dir = Path(tempfile.mkdtemp(prefix='qorzen_plugin_'))
        try:
            if format == PackageFormat.ZIP:
                cls._extract_zip_package(path, temp_dir)
            elif format == PackageFormat.WHEEL:
                cls._extract_wheel_package(path, temp_dir)
            elif format == PackageFormat.DIRECTORY:
                temp_dir = path
            manifest_path = temp_dir / cls.MANIFEST_PATH
            if not manifest_path.exists():
                raise PackageError(f'Manifest file not found in package: {path}')
            try:
                manifest = PluginManifest.load(manifest_path)
            except Exception as e:
                raise PackageError(f'Failed to load manifest: {e}')
            file_hashes = {}
            hash_path = temp_dir / 'files.json'
            if hash_path.exists():
                try:
                    with open(hash_path, 'r') as f:
                        file_hashes = json.load(f)
                except Exception:
                    pass
            package = cls(manifest=manifest, format=format, path=path)
            package._temp_dir = temp_dir
            package._extracted_path = temp_dir
            package._file_hashes = file_hashes
            return package
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise PackageError(f'Failed to load package: {e}') from e
    def extract(self, output_dir: Union[str, Path]) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if self._extracted_path and self._extracted_path.exists():
            for item in self._extracted_path.iterdir():
                dest = output_dir / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            return output_dir
        if not self.path or not self.path.exists():
            raise PackageError('Package path not set or does not exist')
        if self.format == PackageFormat.ZIP:
            self._extract_zip_package(self.path, output_dir)
        elif self.format == PackageFormat.WHEEL:
            self._extract_wheel_package(self.path, output_dir)
        elif self.format == PackageFormat.DIRECTORY:
            for item in self.path.iterdir():
                dest = output_dir / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            raise PackageError(f'Unsupported package format: {self.format}')
        return output_dir
    def verify_integrity(self) -> bool:
        if not self._extracted_path or not self._extracted_path.exists():
            return False
        if not self._file_hashes:
            return True
        for rel_path, expected_hash in self._file_hashes.items():
            file_path = self._extracted_path / rel_path
            if not file_path.exists():
                return False
            actual_hash = self._calculate_file_hash(file_path)
            if actual_hash != expected_hash:
                return False
        return True
    def get_code_dir(self) -> Optional[Path]:
        if not self._extracted_path or not self._extracted_path.exists():
            return None
        code_dir = self._extracted_path / self.CODE_DIR
        return code_dir if code_dir.exists() else None
    def get_resources_dir(self) -> Optional[Path]:
        if not self._extracted_path or not self._extracted_path.exists():
            return None
        resources_dir = self._extracted_path / self.RESOURCES_DIR
        return resources_dir if resources_dir.exists() else None
    def get_docs_dir(self) -> Optional[Path]:
        if not self._extracted_path or not self._extracted_path.exists():
            return None
        docs_dir = self._extracted_path / self.DOCS_DIR
        return docs_dir if docs_dir.exists() else None
    @staticmethod
    def _is_code_file(path: Path) -> bool:
        code_extensions = {'.py', '.pyi', '.pyx', '.pxd', '.pxi', '.c', '.cpp', '.h', '.hpp', '.js', '.ts', '.jsx', '.tsx'}
        return path.suffix.lower() in code_extensions
    @staticmethod
    def _is_resource_file(path: Path) -> bool:
        resource_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.bmp', '.webp', '.css', '.scss', '.sass', '.less', '.json', '.yaml', '.yml', '.xml', '.html', '.htm', '.txt', '.csv', '.tsv', '.md'}
        return path.suffix.lower() in resource_extensions
    @staticmethod
    def _is_doc_file(path: Path) -> bool:
        doc_extensions = {'.md', '.rst', '.txt', '.pdf', '.html', '.htm'}
        doc_names = {'readme', 'license', 'changelog', 'changes', 'history', 'contributing', 'authors', 'contributors', 'api', 'usage', 'install', 'installation'}
        if path.suffix.lower() in doc_extensions:
            parts = path.parts
            for part in parts:
                part_lower = part.lower()
                if part_lower in ('docs', 'doc', 'documentation'):
                    return True
            stem_lower = path.stem.lower()
            return stem_lower in doc_names
        return False
    @staticmethod
    def _calculate_file_hash(path: Path) -> str:
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    @staticmethod
    def _create_zip_package(source_dir: Path, output_path: Path) -> None:
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(source_dir):
                    root_path = Path(root)
                    for file in files:
                        file_path = root_path / file
                        rel_path = file_path.relative_to(source_dir)
                        zf.write(file_path, rel_path)
        except Exception as e:
            raise PackageError(f'Failed to create ZIP package: {e}')
    @staticmethod
    def _extract_zip_package(zip_path: Path, output_dir: Path) -> None:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(output_dir)
        except Exception as e:
            raise PackageError(f'Failed to extract ZIP package: {e}')
    @staticmethod
    def _create_wheel_package(source_dir: Path, output_path: Path, manifest: PluginManifest) -> None:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                package_name = manifest.name.replace('-', '_')
                package_dir = temp_path / package_name
                package_dir.mkdir()
                code_dir = source_dir / PluginPackage.CODE_DIR
                if code_dir.exists():
                    for item in code_dir.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, package_dir / item.name)
                        else:
                            shutil.copy2(item, package_dir / item.name)
                init_py = package_dir / '__init__.py'
                if not init_py.exists():
                    with open(init_py, 'w') as f:
                        f.write(f'"""Qorzen plugin: {manifest.display_name}."""\n\n')
                        f.write(f"__version__ = '{manifest.version}'\n")
                shutil.copy2(source_dir / PluginPackage.MANIFEST_PATH, package_dir / PluginPackage.MANIFEST_PATH)
                setup_py = temp_path / 'setup.py'
                with open(setup_py, 'w') as f:
                    f.write(f'''\nfrom setuptools import setup, find_packages\n\nsetup(\n    name="{manifest.name}",\n    version="{manifest.version}",\n    description="{manifest.description}",\n    author="{manifest.author.name}",\n    author_email="{manifest.author.email}",\n    url="{manifest.homepage or ''}",\n    packages=find_packages(),\n    package_data={'{package_name}': [\"manifest.json\", \"resources/**/*\", \"docs/**/*\"],\n    } ,\n    include_package_data=True,\n    classifiers=[\n        "Programming Language :: Python :: 3",\n        "License :: OSI Approved :: {manifest.license}",\n        "Operating System :: OS Independent",\n        "Framework :: Qorzen",\n    ],\n    python_requires=">=3.8",\n)\n''')
                setup_cfg = temp_path / 'setup.cfg'
                with open(setup_cfg, 'w') as f:
                    f.write('[bdist_wheel]\nuniversal=1\n')
                manifest_in = temp_path / 'MANIFEST.in'
                with open(manifest_in, 'w') as f:
                    f.write('include manifest.json\n')
                    f.write('recursive-include resources *\n')
                    f.write('recursive-include docs *\n')
                resources_dir = source_dir / PluginPackage.RESOURCES_DIR
                if resources_dir.exists():
                    shutil.copytree(resources_dir, package_dir / PluginPackage.RESOURCES_DIR)
                docs_dir = source_dir / PluginPackage.DOCS_DIR
                if docs_dir.exists():
                    shutil.copytree(docs_dir, package_dir / PluginPackage.DOCS_DIR)
                import subprocess
                subprocess.run([sys.executable, 'setup.py', 'bdist_wheel'], cwd=temp_path, check=True, capture_output=True)
                dist_dir = temp_path / 'dist'
                wheel_files = list(dist_dir.glob('*.whl'))
                if not wheel_files:
                    raise PackageError('No wheel file created')
                shutil.copy2(wheel_files[0], output_path)
        except Exception as e:
            raise PackageError(f'Failed to create wheel package: {e}')
    @staticmethod
    def _extract_wheel_package(wheel_path: Path, output_dir: Path) -> None:
        try:
            with zipfile.ZipFile(wheel_path, 'r') as zf:
                zf.extractall(output_dir)
                dist_info_dirs = [d for d in zf.namelist() if d.endswith('.dist-info/') and '/' in d]
                if not dist_info_dirs:
                    raise PackageError('Invalid wheel: No .dist-info directory found')
                dist_info_dir = dist_info_dirs[0]
                package_name = dist_info_dir.split('-')[0]
                package_dir = output_dir / package_name
                if not (output_dir / PluginPackage.MANIFEST_PATH).exists():
                    manifest_candidates = [package_dir / PluginPackage.MANIFEST_PATH, output_dir / package_name / PluginPackage.MANIFEST_PATH]
                    manifest_found = False
                    for candidate in manifest_candidates:
                        if candidate.exists():
                            shutil.copy2(candidate, output_dir / PluginPackage.MANIFEST_PATH)
                            manifest_found = True
                            break
                    if not manifest_found:
                        raise PackageError('Invalid plugin package: No manifest.json found')
                for dir_name in [PluginPackage.CODE_DIR, PluginPackage.RESOURCES_DIR, PluginPackage.DOCS_DIR]:
                    (output_dir / dir_name).mkdir(exist_ok=True)
                if package_dir.exists():
                    for item in package_dir.iterdir():
                        if item.is_file() and item.suffix in ('.py', '.pyi', '.pyx', '.pxd', '.pxi'):
                            shutil.copy2(item, output_dir / PluginPackage.CODE_DIR / item.name)
                resources_src = package_dir / PluginPackage.RESOURCES_DIR
                if resources_src.exists():
                    for item in resources_src.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, output_dir / PluginPackage.RESOURCES_DIR / item.name)
                        else:
                            shutil.copy2(item, output_dir / PluginPackage.RESOURCES_DIR / item.name)
                docs_src = package_dir / PluginPackage.DOCS_DIR
                if docs_src.exists():
                    for item in docs_src.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, output_dir / PluginPackage.DOCS_DIR / item.name)
                        else:
                            shutil.copy2(item, output_dir / PluginPackage.DOCS_DIR / item.name)
        except Exception as e:
            raise PackageError(f'Failed to extract wheel package: {e}')