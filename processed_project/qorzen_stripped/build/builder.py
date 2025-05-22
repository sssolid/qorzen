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
    pass
class Builder:
    def __init__(self, config: BuildConfig, logger: Optional[Callable]=None) -> None:
        self.config = config
        self.logger = logger or print
        self.temp_dir = None
    def log(self, message: str, level: str='info') -> None:
        if self.logger:
            self.logger(f'[{level.upper()}] {message}')
    def prepare_build_environment(self) -> None:
        if not self.config.output_dir.exists():
            self.config.output_dir.mkdir(parents=True)
        elif self.config.clean:
            self.log(f'Cleaning output directory: {self.config.output_dir}')
            for item in self.config.output_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix='qorzen_build_'))
        self.log(f'Created temporary build directory: {self.temp_dir}')
        if self.config.platform == BuildPlatform.CURRENT:
            system = platform.system().lower()
            if system == 'windows':
                self.config.platform = BuildPlatform.WINDOWS
            elif system == 'darwin':
                self.config.platform = BuildPlatform.MACOS
            elif system == 'linux':
                self.config.platform = BuildPlatform.LINUX
            else:
                raise BuildError(f'Unsupported platform: {system}')
            self.log(f'Resolved current platform to: {self.config.platform.value}')
    def run_pyinstaller(self) -> int:
        try:
            import PyInstaller
        except ImportError:
            raise BuildError("PyInstaller is not installed. Install it with 'pip install pyinstaller'")
        args = self.config.to_pyinstaller_args()
        work_dir = self.temp_dir / 'workdir'
        work_dir.mkdir(exist_ok=True)
        args.extend(['--workpath', str(work_dir)])
        spec_dir = self.temp_dir / 'spec'
        spec_dir.mkdir(exist_ok=True)
        args.extend(['--specpath', str(spec_dir)])
        cmd = [sys.executable, '-m', 'PyInstaller'] + args
        self.log(f"Running PyInstaller with arguments: {' '.join(args)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
        for line in process.stdout:
            self.log(line.strip(), 'debug')
        process.wait()
        stderr = process.stderr.read()
        if stderr:
            self.log(f'PyInstaller stderr: {stderr}', 'warning')
        return process.returncode
    def post_process_build(self) -> None:
        output_path = self.config.get_output_path()
        if not output_path.exists():
            raise BuildError(f'Build failed: Output not found at {output_path}')
        self.log(f'Post-processing build artifacts at: {output_path}')
        version_file = output_path / 'version.txt' if output_path.is_dir() else output_path.parent / 'version.txt'
        with open(version_file, 'w') as f:
            f.write(f'{self.config.name} v{self.config.version}\n')
            f.write(f'Built on: {platform.system()} {platform.release()}\n')
            f.write(f'Python: {platform.python_version()}\n')
        self.log(f'Created version file: {version_file}')
        if self.config.platform in (BuildPlatform.LINUX, BuildPlatform.MACOS):
            executable = output_path
            if output_path.is_dir():
                executable = output_path / self.config.name
            if executable.exists():
                executable.chmod(executable.stat().st_mode | 73)
                self.log(f'Set executable permissions on: {executable}')
    def verify_build(self) -> bool:
        output_path = self.config.get_output_path()
        if not output_path.exists():
            self.log(f'Build verification failed: Output not found at {output_path}', 'error')
            return False
        self.log(f'Verifying build artifacts at: {output_path}')
        if self.config.build_type == BuildType.ONEDIR:
            if self.config.platform == BuildPlatform.WINDOWS:
                executable = output_path / f'{self.config.name}.exe'
            else:
                executable = output_path / self.config.name
            if not executable.exists():
                self.log(f'Build verification failed: Executable not found at {executable}', 'error')
                return False
        self.log('Build verification completed successfully')
        return True
    def cleanup(self) -> None:
        if self.temp_dir and self.temp_dir.exists():
            self.log(f'Cleaning up temporary directory: {self.temp_dir}')
            shutil.rmtree(self.temp_dir)
    def build(self) -> pathlib.Path:
        try:
            self.log(f'Starting build of {self.config.name} v{self.config.version}')
            self.log(f'Target platform: {self.config.platform.value}')
            self.log(f'Build type: {self.config.build_type.value}')
            self.prepare_build_environment()
            return_code = self.run_pyinstaller()
            if return_code != 0:
                raise BuildError(f'PyInstaller failed with return code {return_code}')
            self.post_process_build()
            if not self.verify_build():
                raise BuildError('Build verification failed')
            output_path = self.config.get_output_path()
            self.log(f'Build completed successfully: {output_path}')
            return output_path
        except Exception as e:
            self.log(f'Build failed: {str(e)}', 'error')
            raise BuildError(f'Build failed: {str(e)}') from e
        finally:
            self.cleanup()
    @classmethod
    def create_default_build(cls, logger: Optional[Callable]=None) -> pathlib.Path:
        config = BuildConfig()
        builder = cls(config, logger)
        return builder.build()