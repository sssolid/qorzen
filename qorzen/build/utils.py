"""Utility functions for the Qorzen build system.

This module contains utility functions used by the build system, including
path manipulation, dependency analysis, resource collection, and build verification.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import os
import pathlib
import pkgutil
import platform
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Set, Tuple, Union

from qorzen.build.config import BuildConfig


def get_application_version() -> str:
    """Get the version of the Qorzen application.

    Returns:
        Version string of the application.
    """
    try:
        from qorzen.__version__ import __version__
        return __version__
    except ImportError:
        return "0.1.0"  # Default version if not found


def find_dependencies(
        entry_point: Union[str, pathlib.Path], exclude_modules: Optional[List[str]] = None
) -> List[str]:
    """Find Python dependencies for the given entry point.

    This analyzes imports in the entry point script and its imported modules
    to find all dependencies that need to be included in the build.

    Args:
        entry_point: Path to the entry point script
        exclude_modules: List of module names to exclude from the dependencies

    Returns:
        List of module names that are dependencies of the entry point
    """
    import modulefinder

    exclude_modules = exclude_modules or []
    exclude_set = set(exclude_modules)

    # Create a module finder and analyze the entry point
    finder = modulefinder.ModuleFinder()
    finder.run_script(str(entry_point))

    # Extract module names, excluding standard library modules
    dependencies = []
    stdlib_path = pathlib.Path(sys.modules["os"].__file__).parent.parent

    for name, module in finder.modules.items():
        # Skip excluded modules
        if name in exclude_set:
            continue

        # Skip standard library modules
        if module.__file__:
            module_path = pathlib.Path(module.__file__)
            if stdlib_path in module_path.parents:
                continue

        # Skip built-in modules
        if not module.__file__:
            continue

        # Add to dependencies
        dependencies.append(name)

    return sorted(dependencies)


def collect_resources(
        base_dir: Union[str, pathlib.Path],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
) -> Dict[pathlib.Path, str]:
    """Collect resource files that need to be included in the build.

    Args:
        base_dir: Base directory to search for resources
        include_patterns: List of glob patterns for files to include
        exclude_patterns: List of glob patterns for files to exclude

    Returns:
        Dictionary mapping file paths to their destination in the package
    """
    base_dir = pathlib.Path(base_dir)
    include_patterns = include_patterns or ["**/*.png", "**/*.jpg", "**/*.ico", "**/*.css", "**/*.json", "**/*.yaml",
                                            "**/*.yml"]
    exclude_patterns = exclude_patterns or ["**/__pycache__/**", "**/*.pyc", "**/*.pyo", "**/*.pyd", "**/*.py",
                                            ".git/**"]

    resources = {}

    # Convert patterns to regex
    include_regexes = [re.compile(fnmatch_to_regex(pattern)) for pattern in include_patterns]
    exclude_regexes = [re.compile(fnmatch_to_regex(pattern)) for pattern in exclude_patterns]

    # Walk the directory tree
    for root, dirs, files in os.walk(base_dir):
        root_path = pathlib.Path(root)
        rel_path = root_path.relative_to(base_dir)

        # Process each file
        for file in files:
            file_path = root_path / file
            rel_file_path = rel_path / file
            str_path = str(rel_file_path)

            # Check if file matches include pattern and not exclude pattern
            included = any(regex.match(str_path) for regex in include_regexes)
            excluded = any(regex.match(str_path) for regex in exclude_regexes)

            if included and not excluded:
                # Use relative path as destination
                dest = str(rel_path)
                resources[file_path] = dest

    return resources


def fnmatch_to_regex(pattern: str) -> str:
    """Convert a fnmatch/glob pattern to a regex pattern.

    Args:
        pattern: Fnmatch/glob pattern

    Returns:
        Regex pattern string
    """
    pattern = pattern.replace(".", r"\.")
    pattern = pattern.replace("**/", ".*")
    pattern = pattern.replace("**", ".*")
    pattern = pattern.replace("*", "[^/]*")
    pattern = pattern.replace("?", "[^/]")
    return f"^{pattern}$"


def get_installed_packages() -> Dict[str, str]:
    """Get a dictionary of installed Python packages and their versions.

    Returns:
        Dictionary mapping package names to versions
    """
    packages = {}

    try:
        import pkg_resources
        for dist in pkg_resources.working_set:
            packages[dist.project_name] = dist.version
    except ImportError:
        # Fall back to importlib.metadata if pkg_resources is not available
        for dist in importlib.metadata.distributions():
            packages[dist.metadata["Name"]] = dist.version

    return packages


def check_pyinstaller_availability() -> bool:
    """Check if PyInstaller is available in the current environment.

    Returns:
        True if PyInstaller is available, False otherwise
    """
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def verify_build(build_path: Union[str, pathlib.Path], config: BuildConfig) -> bool:
    """Verify that a build is complete and correct.

    Args:
        build_path: Path to the build directory or file
        config: Build configuration used to create the build

    Returns:
        True if the build is valid, False otherwise
    """
    build_path = pathlib.Path(build_path)

    # Check if the build exists
    if not build_path.exists():
        return False

    # For one-file builds, verify the executable exists
    if config.build_type == "onefile":
        return build_path.is_file() and os.access(build_path, os.X_OK)

    # For one-dir builds, verify the directory contains all required files
    if config.build_type == "onedir":
        # Check executable
        if config.platform == "windows":
            executable = build_path / f"{config.name}.exe"
        else:
            executable = build_path / config.name

        if not executable.exists() or not os.access(executable, os.X_OK):
            return False

        # Check for other required files
        required_files = ["_internal"]
        for file in required_files:
            if not (build_path / file).exists():
                return False

    return True


def create_installer(
        build_path: Union[str, pathlib.Path],
        config: BuildConfig,
        installer_type: str = "inno"
) -> pathlib.Path:
    """Create an installer for the built application.

    Args:
        build_path: Path to the build directory or file
        config: Build configuration
        installer_type: Type of installer to create (inno, nsis, etc.)

    Returns:
        Path to the created installer

    Raises:
        NotImplementedError: If the installer type is not supported
    """
    build_path = pathlib.Path(build_path)

    if installer_type == "inno":
        if platform.system() != "Windows":
            raise NotImplementedError("Inno Setup is only available on Windows")

        # Check if Inno Setup is installed
        inno_path = shutil.which("iscc")
        if not inno_path:
            raise FileNotFoundError("Inno Setup Compiler (iscc) not found in PATH")

        # Create a temporary Inno Setup script
        script_path = build_path.parent / f"{config.name}.iss"
        with open(script_path, "w") as f:
            f.write(f"""
            [Setup]
            AppName={config.name}
            AppVersion={config.version}
            DefaultDirName={{pf}}\\{config.name}
            DefaultGroupName={config.name}
            OutputDir={build_path.parent}
            OutputBaseFilename={config.name}_Setup_{config.version}

            [Files]
            Source: "{build_path}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs

            [Icons]
            Name: "{{group}}\\{config.name}"; Filename: "{{app}}\\{config.name}.exe"
            Name: "{{commondesktop}}\\{config.name}"; Filename: "{{app}}\\{config.name}.exe"
            """)

        # Run Inno Setup Compiler
        subprocess.run([inno_path, str(script_path)], check=True)

        # Return path to the created installer
        installer_path = build_path.parent / f"{config.name}_Setup_{config.version}.exe"
        if installer_path.exists():
            return installer_path
        else:
            raise FileNotFoundError(f"Installer not found at {installer_path}")

    elif installer_type == "dmg":
        if platform.system() != "Darwin":
            raise NotImplementedError("DMG creation is only available on macOS")

        # Create DMG (simple approach using hdiutil)
        dmg_path = build_path.parent / f"{config.name}_{config.version}.dmg"
        subprocess.run(["hdiutil", "create", "-volname", config.name,
                        "-srcfolder", str(build_path), "-ov", "-format",
                        "UDZO", str(dmg_path)], check=True)

        if dmg_path.exists():
            return dmg_path
        else:
            raise FileNotFoundError(f"DMG not found at {dmg_path}")

    else:
        raise NotImplementedError(f"Installer type '{installer_type}' not supported")