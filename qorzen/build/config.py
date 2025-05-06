"""Build configuration for Qorzen application.

This module contains the configuration classes and utilities for defining
how the Qorzen application should be built and packaged.
"""

from __future__ import annotations

import enum
import os
import pathlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union

import pydantic


class BuildPlatform(str, enum.Enum):
    """Target platforms for building the application."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    CURRENT = "current"  # Build for the current platform


class BuildType(str, enum.Enum):
    """Types of builds that can be created."""

    ONEFILE = "onefile"  # Single executable file
    ONEDIR = "onedir"  # Directory containing executable and dependencies
    CONSOLE = "console"  # Console application (shows console window)
    WINDOWED = "windowed"  # GUI application (no console window)


class BuildConfig(pydantic.BaseModel):
    """Configuration for building the Qorzen application.

    This class defines all the parameters needed to build the application
    for a specific platform and build type.

    Attributes:
        name: Name of the application (used for output filenames)
        version: Version string for the application
        platform: Target platform for the build
        build_type: Type of build to create
        console: Whether to include a console window
        icon_path: Path to the application icon file
        include_paths: Additional paths to include in the build
        exclude_paths: Paths to exclude from the build
        hidden_imports: Python modules to include that may not be detected
        entry_point: Main entry point script for the application
        output_dir: Directory where build artifacts will be placed
        clean: Whether to clean the output directory before building
        upx: Whether to use UPX compression on the executable
        upx_exclude: Files to exclude from UPX compression
        debug: Whether to include debug information in the build
        additional_data: Additional data files to include (path: destination)
        environment_vars: Environment variables to set in the package
    """

    name: str = "Qorzen"
    version: str = "0.1.0"
    platform: BuildPlatform = BuildPlatform.CURRENT
    build_type: BuildType = BuildType.ONEDIR
    console: bool = False
    icon_path: Optional[pathlib.Path] = None
    include_paths: List[pathlib.Path] = field(default_factory=list)
    exclude_paths: List[pathlib.Path] = field(default_factory=list)
    hidden_imports: List[str] = field(default_factory=list)
    entry_point: pathlib.Path = pathlib.Path("qorzen/main.py")
    output_dir: pathlib.Path = pathlib.Path("dist")
    clean: bool = True
    upx: bool = True
    upx_exclude: List[str] = field(default_factory=list)
    debug: bool = False
    additional_data: Dict[pathlib.Path, str] = field(default_factory=dict)
    environment_vars: Dict[str, str] = field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    @pydantic.validator("icon_path", pre=True)
    def validate_icon_path(cls, v):
        """Validate and convert icon path to pathlib.Path."""
        if v is None:
            return None
        path = pathlib.Path(v)
        if not path.exists():
            raise ValueError(f"Icon file not found: {path}")
        return path

    @pydantic.validator("entry_point", pre=True)
    def validate_entry_point(cls, v):
        """Validate and convert entry point to pathlib.Path."""
        path = pathlib.Path(v)
        if not path.exists():
            raise ValueError(f"Entry point script not found: {path}")
        return path

    @pydantic.validator("include_paths", "exclude_paths", pre=True, each_item=True)
    def validate_paths(cls, v):
        """Validate and convert paths to pathlib.Path."""
        return pathlib.Path(v)

    @pydantic.validator("output_dir", pre=True)
    def validate_output_dir(cls, v):
        """Validate and convert output directory to pathlib.Path."""
        return pathlib.Path(v)

    @pydantic.validator("additional_data", pre=True, each_item=True)
    def validate_additional_data(cls, v, values, **kwargs):
        """Validate and convert additional data paths."""
        if isinstance(v, tuple) and len(v) == 2:
            return (pathlib.Path(v[0]), v[1])
        if isinstance(v, dict) and len(v) == 1:
            key = next(iter(v.keys()))
            return (pathlib.Path(key), v[key])
        raise ValueError(f"Invalid additional data format: {v}")

    def to_pyinstaller_args(self) -> List[str]:
        """Convert the build configuration to PyInstaller command-line arguments.

        Returns:
            List of command-line arguments for PyInstaller.
        """
        args = []

        # Basic configuration
        if self.build_type == BuildType.ONEFILE:
            args.append("--onefile")
        else:
            args.append("--onedir")

        if self.console:
            args.append("--console")
        else:
            args.append("--windowed")

        if self.icon_path:
            args.extend(["--icon", str(self.icon_path)])

        # Add version info
        args.extend(["--name", self.name])

        # Output directory
        args.extend(["--distpath", str(self.output_dir)])

        # Debug options
        if self.debug:
            args.append("--debug")

        # UPX options
        if self.upx:
            args.append("--upx-dir")
            # Default to looking in PATH for UPX
            args.append("upx")
        else:
            args.append("--noupx")

        for item in self.upx_exclude:
            args.extend(["--upx-exclude", item])

        # Hidden imports
        for module in self.hidden_imports:
            args.extend(["--hidden-import", module])

        # Additional data files
        for src_path, dest_path in self.additional_data.items():
            args.extend(["--add-data", f"{src_path}{os.pathsep}{dest_path}"])

        # Environment variables
        for name, value in self.environment_vars.items():
            args.extend(["--env", f"{name}={value}"])

        # Include and exclude paths
        for path in self.include_paths:
            args.extend(["--paths", str(path)])

        for path in self.exclude_paths:
            args.extend(["--exclude-module", str(path)])

        # Entry point
        args.append(str(self.entry_point))

        return args

    def get_output_path(self) -> pathlib.Path:
        """Get the path to the built application.

        Returns:
            Path to the built application executable or directory.
        """
        if self.build_type == BuildType.ONEFILE:
            if self.platform == BuildPlatform.WINDOWS:
                return self.output_dir / f"{self.name}.exe"
            else:
                return self.output_dir / self.name
        else:
            return self.output_dir / self.name

    @classmethod
    def from_dict(cls, config_dict: Dict) -> BuildConfig:
        """Create a BuildConfig from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values.

        Returns:
            BuildConfig instance.
        """
        return cls(**config_dict)

    @classmethod
    def from_json_file(cls, json_path: Union[str, pathlib.Path]) -> BuildConfig:
        """Load a BuildConfig from a JSON file.

        Args:
            json_path: Path to the JSON configuration file.

        Returns:
            BuildConfig instance.
        """
        import json

        with open(json_path, "r") as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    def to_dict(self) -> Dict:
        """Convert the BuildConfig to a dictionary.

        Returns:
            Dictionary representation of the BuildConfig.
        """
        config_dict = self.dict()

        # Convert Path objects to strings for serialization
        for key, value in config_dict.items():
            if isinstance(value, list) and value and isinstance(value[0], pathlib.Path):
                config_dict[key] = [str(p) for p in value]
            elif isinstance(value, pathlib.Path):
                config_dict[key] = str(value)
            elif isinstance(value, dict) and any(isinstance(k, pathlib.Path) for k in value.keys()):
                config_dict[key] = {str(k): v for k, v in value.items()}

        return config_dict

    def to_json_file(self, json_path: Union[str, pathlib.Path]) -> None:
        """Save the BuildConfig to a JSON file.

        Args:
            json_path: Path where the JSON configuration file will be saved.
        """
        import json

        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)