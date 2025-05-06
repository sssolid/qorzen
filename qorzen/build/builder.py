"""Builder for creating Qorzen application packages.

This module contains the Builder class that handles the actual build process,
including configuring PyInstaller, managing build artifacts, and verifying
build results.
"""

from __future__ import annotations

import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Dict, List, Optional, Tuple, Union

from qorzen.build.config import BuildConfig, BuildPlatform, BuildType
from qorzen.build.utils import find_dependencies, get_application_version, verify_build


class BuildError(Exception):
    """Exception raised for errors during the build process."""

    pass


class Builder:
    """Builder for creating Qorzen application packages.

    This class handles the actual build process, including configuring PyInstaller,
    managing build artifacts, and verifying build results.

    Attributes:
        config: Build configuration
        logger: Logger instance for logging build progress
        temp_dir: Temporary directory for build artifacts
    """

    def __init__(
            self, config: BuildConfig, logger: Optional[Callable] = None
    ) -> None:
        """Initialize the Builder with the given configuration.

        Args:
            config: Build configuration
            logger: Optional logger function for logging build progress
        """
        self.config = config
        self.logger = logger or print
        self.temp_dir = None

    def log(self, message: str, level: str = "info") -> None:
        """Log a message with the specified level.

        Args:
            message: Message to log
            level: Log level (info, warning, error, debug)
        """
        if self.logger:
            self.logger(f"[{level.upper()}] {message}")

    def prepare_build_environment(self) -> None:
        """Prepare the build environment.

        This method creates the necessary directories and files for the build.
        """
        # Create output directory if it doesn't exist
        if not self.config.output_dir.exists():
            self.config.output_dir.mkdir(parents=True)
        elif self.config.clean:
            self.log(f"Cleaning output directory: {self.config.output_dir}")
            for item in self.config.output_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

        # Create temporary directory for build artifacts
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="qorzen_build_"))
        self.log(f"Created temporary build directory: {self.temp_dir}")

        # Resolve platform if set to CURRENT
        if self.config.platform == BuildPlatform.CURRENT:
            system = platform.system().lower()
            if system == "windows":
                self.config.platform = BuildPlatform.WINDOWS
            elif system == "darwin":
                self.config.platform = BuildPlatform.MACOS
            elif system == "linux":
                self.config.platform = BuildPlatform.LINUX
            else:
                raise BuildError(f"Unsupported platform: {system}")
            self.log(f"Resolved current platform to: {self.config.platform.value}")

    def run_pyinstaller(self) -> int:
        """Run PyInstaller with the configured arguments.

        Returns:
            Return code from PyInstaller process
        """
        try:
            import PyInstaller  # noqa: F401
        except ImportError:
            raise BuildError(
                "PyInstaller is not installed. Install it with 'pip install pyinstaller'"
            )

        # Convert build config to PyInstaller arguments
        args = self.config.to_pyinstaller_args()

        # Add work directory argument
        work_dir = self.temp_dir / "workdir"
        work_dir.mkdir(exist_ok=True)
        args.extend(["--workpath", str(work_dir)])

        # Add spec directory argument
        spec_dir = self.temp_dir / "spec"
        spec_dir.mkdir(exist_ok=True)
        args.extend(["--specpath", str(spec_dir)])

        # Construct command
        cmd = [sys.executable, "-m", "PyInstaller"] + args

        self.log(f"Running PyInstaller with arguments: {' '.join(args)}")

        # Run PyInstaller
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Stream output
        for line in process.stdout:
            self.log(line.strip(), "debug")

        # Wait for process to complete
        process.wait()

        # Get any remaining stderr output
        stderr = process.stderr.read()
        if stderr:
            self.log(f"PyInstaller stderr: {stderr}", "warning")

        return process.returncode

    def post_process_build(self) -> None:
        """Perform post-processing on the build artifacts.

        This can include:
        - Copying additional files not handled by PyInstaller
        - Fixing permissions
        - Creating launchers or shortcuts
        - Adding metadata files
        """
        output_path = self.config.get_output_path()

        if not output_path.exists():
            raise BuildError(f"Build failed: Output not found at {output_path}")

        self.log(f"Post-processing build artifacts at: {output_path}")

        # Create version file
        version_file = output_path / "version.txt" if output_path.is_dir() else output_path.parent / "version.txt"
        with open(version_file, "w") as f:
            f.write(f"{self.config.name} v{self.config.version}\n")
            f.write(f"Built on: {platform.system()} {platform.release()}\n")
            f.write(f"Python: {platform.python_version()}\n")

        self.log(f"Created version file: {version_file}")

        # Set executable permissions on Unix
        if self.config.platform in (BuildPlatform.LINUX, BuildPlatform.MACOS):
            executable = output_path
            if output_path.is_dir():
                executable = output_path / self.config.name

            if executable.exists():
                executable.chmod(executable.stat().st_mode | 0o111)  # Add executable bit
                self.log(f"Set executable permissions on: {executable}")

    def verify_build(self) -> bool:
        """Verify that the build was successful and correct.

        Returns:
            True if verification passed, False otherwise
        """
        output_path = self.config.get_output_path()

        if not output_path.exists():
            self.log(f"Build verification failed: Output not found at {output_path}", "error")
            return False

        self.log(f"Verifying build artifacts at: {output_path}")

        # Check if executable exists and is runnable
        if self.config.build_type == BuildType.ONEDIR:
            if self.config.platform == BuildPlatform.WINDOWS:
                executable = output_path / f"{self.config.name}.exe"
            else:
                executable = output_path / self.config.name

            if not executable.exists():
                self.log(f"Build verification failed: Executable not found at {executable}", "error")
                return False

        # Additional verification could include:
        # - Checking for required files
        # - Verifying the executable runs correctly
        # - Checking size and structure
        # - Running automated tests on the built application

        self.log("Build verification completed successfully")
        return True

    def cleanup(self) -> None:
        """Clean up temporary files and directories used during the build."""
        if self.temp_dir and self.temp_dir.exists():
            self.log(f"Cleaning up temporary directory: {self.temp_dir}")
            shutil.rmtree(self.temp_dir)

    def build(self) -> pathlib.Path:
        """Build the application according to the configuration.

        This is the main entry point for the build process.

        Returns:
            Path to the built application

        Raises:
            BuildError: If the build fails for any reason
        """
        try:
            self.log(f"Starting build of {self.config.name} v{self.config.version}")
            self.log(f"Target platform: {self.config.platform.value}")
            self.log(f"Build type: {self.config.build_type.value}")

            # Prepare environment
            self.prepare_build_environment()

            # Run PyInstaller
            return_code = self.run_pyinstaller()
            if return_code != 0:
                raise BuildError(f"PyInstaller failed with return code {return_code}")

            # Post-process build
            self.post_process_build()

            # Verify build
            if not self.verify_build():
                raise BuildError("Build verification failed")

            output_path = self.config.get_output_path()
            self.log(f"Build completed successfully: {output_path}")
            return output_path

        except Exception as e:
            self.log(f"Build failed: {str(e)}", "error")
            raise BuildError(f"Build failed: {str(e)}") from e

        finally:
            self.cleanup()

    @classmethod
    def create_default_build(cls, logger: Optional[Callable] = None) -> pathlib.Path:
        """Create a build with default configuration.

        This is a convenience method for quickly building the application.

        Args:
            logger: Optional logger function for logging build progress

        Returns:
            Path to the built application
        """
        config = BuildConfig()
        builder = cls(config, logger)
        return builder.build()