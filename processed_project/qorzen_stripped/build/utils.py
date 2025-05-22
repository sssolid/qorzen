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
    try:
        from qorzen.__version__ import __version__
        return __version__
    except ImportError:
        return '0.1.0'
def find_dependencies(entry_point: Union[str, pathlib.Path], exclude_modules: Optional[List[str]]=None) -> List[str]:
    import modulefinder
    exclude_modules = exclude_modules or []
    exclude_set = set(exclude_modules)
    finder = modulefinder.ModuleFinder()
    finder.run_script(str(entry_point))
    dependencies = []
    stdlib_path = pathlib.Path(sys.modules['os'].__file__).parent.parent
    for name, module in finder.modules.items():
        if name in exclude_set:
            continue
        if module.__file__:
            module_path = pathlib.Path(module.__file__)
            if stdlib_path in module_path.parents:
                continue
        if not module.__file__:
            continue
        dependencies.append(name)
    return sorted(dependencies)
def collect_resources(base_dir: Union[str, pathlib.Path], include_patterns: Optional[List[str]]=None, exclude_patterns: Optional[List[str]]=None) -> Dict[pathlib.Path, str]:
    base_dir = pathlib.Path(base_dir)
    include_patterns = include_patterns or ['**/*.png', '**/*.jpg', '**/*.ico', '**/*.css', '**/*.json', '**/*.yaml', '**/*.yml']
    exclude_patterns = exclude_patterns or ['**/__pycache__/**', '**/*.pyc', '**/*.pyo', '**/*.pyd', '**/*.py', '.git/**']
    resources = {}
    include_regexes = [re.compile(fnmatch_to_regex(pattern)) for pattern in include_patterns]
    exclude_regexes = [re.compile(fnmatch_to_regex(pattern)) for pattern in exclude_patterns]
    for root, dirs, files in os.walk(base_dir):
        root_path = pathlib.Path(root)
        rel_path = root_path.relative_to(base_dir)
        for file in files:
            file_path = root_path / file
            rel_file_path = rel_path / file
            str_path = str(rel_file_path)
            included = any((regex.match(str_path) for regex in include_regexes))
            excluded = any((regex.match(str_path) for regex in exclude_regexes))
            if included and (not excluded):
                dest = str(rel_path)
                resources[file_path] = dest
    return resources
def fnmatch_to_regex(pattern: str) -> str:
    pattern = pattern.replace('.', '\\.')
    pattern = pattern.replace('**/', '.*')
    pattern = pattern.replace('**', '.*')
    pattern = pattern.replace('*', '[^/]*')
    pattern = pattern.replace('?', '[^/]')
    return f'^{pattern}$'
def get_installed_packages() -> Dict[str, str]:
    packages = {}
    try:
        import pkg_resources
        for dist in pkg_resources.working_set:
            packages[dist.project_name] = dist.version
    except ImportError:
        for dist in importlib.metadata.distributions():
            packages[dist.metadata['Name']] = dist.version
    return packages
def check_pyinstaller_availability() -> bool:
    try:
        import PyInstaller
        return True
    except ImportError:
        return False
def verify_build(build_path: Union[str, pathlib.Path], config: BuildConfig) -> bool:
    build_path = pathlib.Path(build_path)
    if not build_path.exists():
        return False
    if config.build_type == 'onefile':
        return build_path.is_file() and os.access(build_path, os.X_OK)
    if config.build_type == 'onedir':
        if config.platform == 'windows':
            executable = build_path / f'{config.name}.exe'
        else:
            executable = build_path / config.name
        if not executable.exists() or not os.access(executable, os.X_OK):
            return False
        required_files = ['_internal']
        for file in required_files:
            if not (build_path / file).exists():
                return False
    return True
def create_installer(build_path: Union[str, pathlib.Path], config: BuildConfig, installer_type: str='inno') -> pathlib.Path:
    build_path = pathlib.Path(build_path)
    if installer_type == 'inno':
        if platform.system() != 'Windows':
            raise NotImplementedError('Inno Setup is only available on Windows')
        inno_path = shutil.which('iscc')
        if not inno_path:
            raise FileNotFoundError('Inno Setup Compiler (iscc) not found in PATH')
        script_path = build_path.parent / f'{config.name}.iss'
        with open(script_path, 'w') as f:
            f.write(f'\n            [Setup]\n            AppName={config.name}\n            AppVersion={config.version}\n            DefaultDirName={pf} \\{config.name}\n            DefaultGroupName={config.name}\n            OutputDir={build_path.parent}\n            OutputBaseFilename={config.name}_Setup_{config.version}\n\n            [Files]\n            Source: "{build_path}\\*"; DestDir: "{app} "; Flags: ignoreversion recursesubdirs\n\n            [Icons]\n            Name: "{group} \\{config.name}"; Filename: "{app} \\{config.name}.exe"\n            Name: "{commondesktop} \\{config.name}"; Filename: "{app} \\{config.name}.exe"\n            ')
        subprocess.run([inno_path, str(script_path)], check=True)
        installer_path = build_path.parent / f'{config.name}_Setup_{config.version}.exe'
        if installer_path.exists():
            return installer_path
        else:
            raise FileNotFoundError(f'Installer not found at {installer_path}')
    elif installer_type == 'dmg':
        if platform.system() != 'Darwin':
            raise NotImplementedError('DMG creation is only available on macOS')
        dmg_path = build_path.parent / f'{config.name}_{config.version}.dmg'
        subprocess.run(['hdiutil', 'create', '-volname', config.name, '-srcfolder', str(build_path), '-ov', '-format', 'UDZO', str(dmg_path)], check=True)
        if dmg_path.exists():
            return dmg_path
        else:
            raise FileNotFoundError(f'DMG not found at {dmg_path}')
    else:
        raise NotImplementedError(f"Installer type '{installer_type}' not supported")