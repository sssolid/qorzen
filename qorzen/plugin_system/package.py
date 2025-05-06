"""Plugin package management for Qorzen.

This module provides utilities for creating, extracting, and managing
plugin packages. It defines the package format and structure, and
provides tools for working with plugin packages.
"""

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
    """Format for plugin packages.

    These formats determine how the plugin is packaged and distributed.
    """

    ZIP = "zip"  # Standard ZIP archive
    WHEEL = "wheel"  # Python wheel package
    DIRECTORY = "directory"  # Uncompressed directory (for development)


class PackageError(Exception):
    """Exception raised for errors in plugin packaging."""

    pass


class PluginPackage:
    """Plugin package handler.

    This class provides methods for creating, extracting, and managing
    plugin packages.

    Attributes:
        manifest: Plugin manifest
        format: Package format
        path: Path to the package file or directory
    """

    # Standard plugin package structure
    MANIFEST_PATH = "manifest.json"
    CODE_DIR = "code"
    RESOURCES_DIR = "resources"
    DOCS_DIR = "docs"

    def __init__(
            self,
            manifest: Optional[PluginManifest] = None,
            format: PackageFormat = PackageFormat.ZIP,
            path: Optional[Union[str, Path]] = None
    ) -> None:
        """Initialize a plugin package.

        Args:
            manifest: Plugin manifest
            format: Package format
            path: Path to the package file or directory
        """
        self.manifest = manifest
        self.format = format
        self.path = Path(path) if path else None
        self._temp_dir: Optional[Path] = None
        self._extracted_path: Optional[Path] = None
        self._file_hashes: Dict[str, str] = {}

    def __del__(self) -> None:
        """Clean up temporary files when the object is destroyed."""
        self.cleanup()

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
            self._extracted_path = None

    @classmethod
    def create(
            cls,
            source_dir: Union[str, Path],
            output_path: Union[str, Path],
            manifest: Optional[PluginManifest] = None,
            format: PackageFormat = PackageFormat.ZIP,
            include_patterns: Optional[List[str]] = None,
            exclude_patterns: Optional[List[str]] = None
    ) -> PluginPackage:
        """Create a plugin package from a source directory.

        Args:
            source_dir: Directory containing the plugin source code
            output_path: Path where the package will be created
            manifest: Plugin manifest (if None, will be loaded from source_dir)
            format: Package format
            include_patterns: Glob patterns for files to include
            exclude_patterns: Glob patterns for files to exclude

        Returns:
            Created plugin package

        Raises:
            PackageError: If package creation fails
        """
        source_dir = Path(source_dir)
        output_path = Path(output_path)

        # Ensure source directory exists
        if not source_dir.exists() or not source_dir.is_dir():
            raise PackageError(f"Source directory not found: {source_dir}")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load manifest if not provided
        if manifest is None:
            manifest_path = source_dir / cls.MANIFEST_PATH
            if not manifest_path.exists():
                raise PackageError(f"Manifest file not found: {manifest_path}")
            try:
                manifest = PluginManifest.load(manifest_path)
            except Exception as e:
                raise PackageError(f"Failed to load manifest: {e}")

        # Create temporary directory for packaging
        temp_dir = Path(tempfile.mkdtemp(prefix="qorzen_plugin_"))

        try:
            # Define standard directories
            package_structure = {
                cls.CODE_DIR: temp_dir / cls.CODE_DIR,
                cls.RESOURCES_DIR: temp_dir / cls.RESOURCES_DIR,
                cls.DOCS_DIR: temp_dir / cls.DOCS_DIR,
            }

            # Create directories
            for dir_path in package_structure.values():
                dir_path.mkdir(parents=True, exist_ok=True)

            # Copy relevant files
            include_patterns = include_patterns or ["**/*"]
            exclude_patterns = exclude_patterns or [
                "**/__pycache__/**",
                "**/*.pyc",
                "**/*.pyo",
                "**/*.pyd",
                "**/.git/**",
                "**/.vscode/**",
                "**/.idea/**",
                "**/venv/**",
                "**/env/**",
                "**/build/**",
                "**/dist/**",
                "**/*.egg-info/**"
            ]

            file_hashes = {}

            import glob
            for pattern in include_patterns:
                for file_path in source_dir.glob(pattern):
                    # Skip directories and excluded files
                    if file_path.is_dir():
                        continue

                    # Check exclude patterns
                    rel_path = file_path.relative_to(source_dir)
                    if any(rel_path.match(exclude) for exclude in exclude_patterns):
                        continue

                    # Determine destination directory
                    if cls._is_code_file(file_path):
                        dest_dir = package_structure[cls.CODE_DIR]
                    elif cls._is_resource_file(file_path):
                        dest_dir = package_structure[cls.RESOURCES_DIR]
                    elif cls._is_doc_file(file_path):
                        dest_dir = package_structure[cls.DOCS_DIR]
                    else:
                        # Skip files that don't fit into any category
                        continue

                    # Copy file
                    dest_path = dest_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)

                    # Calculate file hash
                    file_hash = cls._calculate_file_hash(file_path)
                    file_hashes[str(rel_path)] = file_hash

            # Save manifest
            manifest_path = temp_dir / cls.MANIFEST_PATH
            manifest.save(manifest_path)

            # Save file hashes
            hash_path = temp_dir / "files.json"
            with open(hash_path, "w") as f:
                json.dump(file_hashes, f, indent=2)

            # Create package based on format
            if format == PackageFormat.ZIP:
                cls._create_zip_package(temp_dir, output_path)
            elif format == PackageFormat.WHEEL:
                cls._create_wheel_package(temp_dir, output_path, manifest)
            elif format == PackageFormat.DIRECTORY:
                # Just copy everything to the output directory
                if output_path.exists() and output_path.is_dir():
                    shutil.rmtree(output_path)
                shutil.copytree(temp_dir, output_path)
            else:
                raise PackageError(f"Unsupported package format: {format}")

            # Create and return package object
            package = cls(manifest=manifest, format=format, path=output_path)
            package._file_hashes = file_hashes
            return package

        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    @classmethod
    def load(cls, path: Union[str, Path]) -> PluginPackage:
        """Load a plugin package from a file or directory.

        Args:
            path: Path to the package file or directory

        Returns:
            Loaded plugin package

        Raises:
            PackageError: If package loading fails
        """
        path = Path(path)

        # Ensure path exists
        if not path.exists():
            raise PackageError(f"Package not found: {path}")

        # Determine format based on path
        if path.is_dir():
            format = PackageFormat.DIRECTORY
        elif path.suffix.lower() == ".zip":
            format = PackageFormat.ZIP
        elif path.suffix.lower() == ".whl":
            format = PackageFormat.WHEEL
        else:
            raise PackageError(f"Unsupported package format: {path}")

        # Create temporary directory for extraction
        temp_dir = Path(tempfile.mkdtemp(prefix="qorzen_plugin_"))

        try:
            # Extract package
            if format == PackageFormat.ZIP:
                cls._extract_zip_package(path, temp_dir)
            elif format == PackageFormat.WHEEL:
                cls._extract_wheel_package(path, temp_dir)
            elif format == PackageFormat.DIRECTORY:
                # No extraction needed for directory format
                temp_dir = path

            # Load manifest
            manifest_path = temp_dir / cls.MANIFEST_PATH
            if not manifest_path.exists():
                raise PackageError(f"Manifest file not found in package: {path}")

            try:
                manifest = PluginManifest.load(manifest_path)
            except Exception as e:
                raise PackageError(f"Failed to load manifest: {e}")

            # Load file hashes
            file_hashes = {}
            hash_path = temp_dir / "files.json"
            if hash_path.exists():
                try:
                    with open(hash_path, "r") as f:
                        file_hashes = json.load(f)
                except Exception:
                    # Non-critical error, can continue without hashes
                    pass

            # Create package object
            package = cls(manifest=manifest, format=format, path=path)
            package._temp_dir = temp_dir
            package._extracted_path = temp_dir
            package._file_hashes = file_hashes

            return package

        except Exception as e:
            # Clean up temporary directory on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise PackageError(f"Failed to load package: {e}") from e

    def extract(self, output_dir: Union[str, Path]) -> Path:
        """Extract the package to a directory.

        Args:
            output_dir: Directory where the package will be extracted

        Returns:
            Path to the extracted package

        Raises:
            PackageError: If package extraction fails
        """
        output_dir = Path(output_dir)

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # If already extracted, just copy from the extracted path
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

        # Extract based on format
        if not self.path or not self.path.exists():
            raise PackageError("Package path not set or does not exist")

        if self.format == PackageFormat.ZIP:
            self._extract_zip_package(self.path, output_dir)
        elif self.format == PackageFormat.WHEEL:
            self._extract_wheel_package(self.path, output_dir)
        elif self.format == PackageFormat.DIRECTORY:
            # Copy directory
            for item in self.path.iterdir():
                dest = output_dir / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            raise PackageError(f"Unsupported package format: {self.format}")

        return output_dir

    def verify_integrity(self) -> bool:
        """Verify the integrity of the package files.

        This checks that all files in the package match their expected hashes.

        Returns:
            True if all files match their hashes, False otherwise
        """
        if not self._extracted_path or not self._extracted_path.exists():
            return False

        if not self._file_hashes:
            # Can't verify without hashes
            return True

        # Check each file
        for rel_path, expected_hash in self._file_hashes.items():
            file_path = self._extracted_path / rel_path

            if not file_path.exists():
                return False

            actual_hash = self._calculate_file_hash(file_path)
            if actual_hash != expected_hash:
                return False

        return True

    def get_code_dir(self) -> Optional[Path]:
        """Get the path to the code directory in the extracted package.

        Returns:
            Path to the code directory, or None if not extracted
        """
        if not self._extracted_path or not self._extracted_path.exists():
            return None

        code_dir = self._extracted_path / self.CODE_DIR
        return code_dir if code_dir.exists() else None

    def get_resources_dir(self) -> Optional[Path]:
        """Get the path to the resources directory in the extracted package.

        Returns:
            Path to the resources directory, or None if not extracted
        """
        if not self._extracted_path or not self._extracted_path.exists():
            return None

        resources_dir = self._extracted_path / self.RESOURCES_DIR
        return resources_dir if resources_dir.exists() else None

    def get_docs_dir(self) -> Optional[Path]:
        """Get the path to the docs directory in the extracted package.

        Returns:
            Path to the docs directory, or None if not extracted
        """
        if not self._extracted_path or not self._extracted_path.exists():
            return None

        docs_dir = self._extracted_path / self.DOCS_DIR
        return docs_dir if docs_dir.exists() else None

    @staticmethod
    def _is_code_file(path: Path) -> bool:
        """Check if a file is a code file.

        Args:
            path: Path to the file

        Returns:
            True if the file is a code file, False otherwise
        """
        code_extensions = {
            ".py", ".pyi", ".pyx", ".pxd", ".pxi", ".c", ".cpp", ".h", ".hpp",
            ".js", ".ts", ".jsx", ".tsx"
        }
        return path.suffix.lower() in code_extensions

    @staticmethod
    def _is_resource_file(path: Path) -> bool:
        """Check if a file is a resource file.

        Args:
            path: Path to the file

        Returns:
            True if the file is a resource file, False otherwise
        """
        resource_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".bmp", ".webp",
            ".css", ".scss", ".sass", ".less", ".json", ".yaml", ".yml",
            ".xml", ".html", ".htm", ".txt", ".csv", ".tsv", ".md"
        }
        return path.suffix.lower() in resource_extensions

    @staticmethod
    def _is_doc_file(path: Path) -> bool:
        """Check if a file is a documentation file.

        Args:
            path: Path to the file

        Returns:
            True if the file is a documentation file, False otherwise
        """
        doc_extensions = {
            ".md", ".rst", ".txt", ".pdf", ".html", ".htm"
        }
        doc_names = {
            "readme", "license", "changelog", "changes", "history",
            "contributing", "authors", "contributors", "api", "usage",
            "install", "installation"
        }

        if path.suffix.lower() in doc_extensions:
            # Check if the file is in a doc-related directory
            parts = path.parts
            for part in parts:
                part_lower = part.lower()
                if part_lower in ("docs", "doc", "documentation"):
                    return True

            # Check if the file name is doc-related
            stem_lower = path.stem.lower()
            return stem_lower in doc_names

        return False

    @staticmethod
    def _calculate_file_hash(path: Path) -> str:
        """Calculate a SHA-256 hash of a file.

        Args:
            path: Path to the file

        Returns:
            Hex digest of the file hash
        """
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _create_zip_package(source_dir: Path, output_path: Path) -> None:
        """Create a ZIP package from a directory.

        Args:
            source_dir: Directory to package
            output_path: Path where the ZIP file will be created

        Raises:
            PackageError: If ZIP creation fails
        """
        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(source_dir):
                    root_path = Path(root)
                    for file in files:
                        file_path = root_path / file
                        rel_path = file_path.relative_to(source_dir)
                        zf.write(file_path, rel_path)
        except Exception as e:
            raise PackageError(f"Failed to create ZIP package: {e}")

    @staticmethod
    def _extract_zip_package(zip_path: Path, output_dir: Path) -> None:
        """Extract a ZIP package to a directory.

        Args:
            zip_path: Path to the ZIP file
            output_dir: Directory where the package will be extracted

        Raises:
            PackageError: If ZIP extraction fails
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(output_dir)
        except Exception as e:
            raise PackageError(f"Failed to extract ZIP package: {e}")

    @staticmethod
    def _create_wheel_package(source_dir: Path, output_path: Path, manifest: PluginManifest) -> None:
        """Create a wheel package from a directory.

        Args:
            source_dir: Directory to package
            output_path: Path where the wheel file will be created
            manifest: Plugin manifest

        Raises:
            PackageError: If wheel creation fails
        """
        try:
            # This is a simplified implementation that creates a basic wheel
            # For a more complete implementation, consider using setuptools

            # Create temporary directory for wheel structure
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Create package directory
                package_name = manifest.name.replace("-", "_")
                package_dir = temp_path / package_name
                package_dir.mkdir()

                # Copy code files
                code_dir = source_dir / PluginPackage.CODE_DIR
                if code_dir.exists():
                    for item in code_dir.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, package_dir / item.name)
                        else:
                            shutil.copy2(item, package_dir / item.name)

                # Create __init__.py if it doesn't exist
                init_py = package_dir / "__init__.py"
                if not init_py.exists():
                    with open(init_py, "w") as f:
                        f.write(f"""\"\"\"Qorzen plugin: {manifest.display_name}.\"\"\"\n\n""")
                        f.write(f"__version__ = '{manifest.version}'\n")

                # Copy manifest and other metadata
                shutil.copy2(source_dir / PluginPackage.MANIFEST_PATH, package_dir / PluginPackage.MANIFEST_PATH)

                # Create setup.py
                setup_py = temp_path / "setup.py"
                with open(setup_py, "w") as f:
                    f.write(f"""
from setuptools import setup, find_packages

setup(
    name="{manifest.name}",
    version="{manifest.version}",
    description="{manifest.description}",
    author="{manifest.author.name}",
    author_email="{manifest.author.email}",
    url="{manifest.homepage or ''}",
    packages=find_packages(),
    package_data={{
        "{package_name}": ["manifest.json", "resources/**/*", "docs/**/*"],
    }},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: {manifest.license}",
        "Operating System :: OS Independent",
        "Framework :: Qorzen",
    ],
    python_requires=">=3.8",
)
""")

                # Create setup.cfg
                setup_cfg = temp_path / "setup.cfg"
                with open(setup_cfg, "w") as f:
                    f.write("[bdist_wheel]\nuniversal=1\n")

                # Create MANIFEST.in to include resources and docs
                manifest_in = temp_path / "MANIFEST.in"
                with open(manifest_in, "w") as f:
                    f.write("include manifest.json\n")
                    f.write("recursive-include resources *\n")
                    f.write("recursive-include docs *\n")

                # Copy resources and docs directories
                resources_dir = source_dir / PluginPackage.RESOURCES_DIR
                if resources_dir.exists():
                    shutil.copytree(resources_dir, package_dir / PluginPackage.RESOURCES_DIR)

                docs_dir = source_dir / PluginPackage.DOCS_DIR
                if docs_dir.exists():
                    shutil.copytree(docs_dir, package_dir / PluginPackage.DOCS_DIR)

                # Build wheel
                import subprocess
                subprocess.run(
                    [sys.executable, "setup.py", "bdist_wheel"],
                    cwd=temp_path,
                    check=True,
                    capture_output=True,
                )

                # Find and copy wheel file
                dist_dir = temp_path / "dist"
                wheel_files = list(dist_dir.glob("*.whl"))
                if not wheel_files:
                    raise PackageError("No wheel file created")

                shutil.copy2(wheel_files[0], output_path)

        except Exception as e:
            raise PackageError(f"Failed to create wheel package: {e}")

    @staticmethod
    def _extract_wheel_package(wheel_path: Path, output_dir: Path) -> None:
        """Extract a wheel package to a directory.

        Args:
            wheel_path: Path to the wheel file
            output_dir: Directory where the package will be extracted

        Raises:
            PackageError: If wheel extraction fails
        """
        try:
            # Wheels are just ZIP files with a specific structure
            with zipfile.ZipFile(wheel_path, "r") as zf:
                # Extract everything
                zf.extractall(output_dir)

                # Find the package directory (inside *.dist-info)
                dist_info_dirs = [d for d in zf.namelist() if d.endswith('.dist-info/') and '/' in d]
                if not dist_info_dirs:
                    raise PackageError("Invalid wheel: No .dist-info directory found")

                dist_info_dir = dist_info_dirs[0]
                package_name = dist_info_dir.split('-')[0]

                # Ensure proper structure for Qorzen plugins
                package_dir = output_dir / package_name

                # Move files to standard Qorzen plugin structure
                if not (output_dir / PluginPackage.MANIFEST_PATH).exists():
                    # Look for manifest in the package
                    manifest_candidates = [
                        package_dir / PluginPackage.MANIFEST_PATH,
                        output_dir / package_name / PluginPackage.MANIFEST_PATH,
                    ]

                    manifest_found = False
                    for candidate in manifest_candidates:
                        if candidate.exists():
                            shutil.copy2(candidate, output_dir / PluginPackage.MANIFEST_PATH)
                            manifest_found = True
                            break

                    if not manifest_found:
                        raise PackageError("Invalid plugin package: No manifest.json found")

                # Create standard directories
                for dir_name in [PluginPackage.CODE_DIR, PluginPackage.RESOURCES_DIR, PluginPackage.DOCS_DIR]:
                    (output_dir / dir_name).mkdir(exist_ok=True)

                # Move code files to code directory
                if package_dir.exists():
                    # Copy all Python files and other code files
                    for item in package_dir.iterdir():
                        if item.is_file() and item.suffix in ('.py', '.pyi', '.pyx', '.pxd', '.pxi'):
                            shutil.copy2(item, output_dir / PluginPackage.CODE_DIR / item.name)

                # Move resources directory if it exists
                resources_src = package_dir / PluginPackage.RESOURCES_DIR
                if resources_src.exists():
                    for item in resources_src.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, output_dir / PluginPackage.RESOURCES_DIR / item.name)
                        else:
                            shutil.copy2(item, output_dir / PluginPackage.RESOURCES_DIR / item.name)

                # Move docs directory if it exists
                docs_src = package_dir / PluginPackage.DOCS_DIR
                if docs_src.exists():
                    for item in docs_src.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, output_dir / PluginPackage.DOCS_DIR / item.name)
                        else:
                            shutil.copy2(item, output_dir / PluginPackage.DOCS_DIR / item.name)

        except Exception as e:
            raise PackageError(f"Failed to extract wheel package: {e}")