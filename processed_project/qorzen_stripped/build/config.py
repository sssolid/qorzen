from __future__ import annotations
import enum
import os
import pathlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union
import pydantic
class BuildPlatform(str, enum.Enum):
    WINDOWS = 'windows'
    MACOS = 'macos'
    LINUX = 'linux'
    CURRENT = 'current'
class BuildType(str, enum.Enum):
    ONEFILE = 'onefile'
    ONEDIR = 'onedir'
    CONSOLE = 'console'
    WINDOWED = 'windowed'
class BuildConfig(pydantic.BaseModel):
    name: str = 'Qorzen'
    version: str = '0.1.0'
    platform: BuildPlatform = BuildPlatform.CURRENT
    build_type: BuildType = BuildType.ONEDIR
    console: bool = False
    icon_path: Optional[pathlib.Path] = None
    include_paths: List[pathlib.Path] = field(default_factory=list)
    exclude_paths: List[pathlib.Path] = field(default_factory=list)
    hidden_imports: List[str] = field(default_factory=list)
    entry_point: pathlib.Path = pathlib.Path('qorzen/main.py')
    output_dir: pathlib.Path = pathlib.Path('dist')
    clean: bool = True
    upx: bool = True
    upx_exclude: List[str] = field(default_factory=list)
    debug: bool = False
    additional_data: Dict[pathlib.Path, str] = field(default_factory=dict)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    class Config:
        arbitrary_types_allowed = True
    @pydantic.validator('icon_path', pre=True)
    def validate_icon_path(cls, v):
        if v is None:
            return None
        path = pathlib.Path(v)
        if not path.exists():
            raise ValueError(f'Icon file not found: {path}')
        return path
    @pydantic.validator('entry_point', pre=True)
    def validate_entry_point(cls, v):
        path = pathlib.Path(v)
        if not path.exists():
            raise ValueError(f'Entry point script not found: {path}')
        return path
    @pydantic.validator('include_paths', 'exclude_paths', pre=True, each_item=True)
    def validate_paths(cls, v):
        return pathlib.Path(v)
    @pydantic.validator('output_dir', pre=True)
    def validate_output_dir(cls, v):
        return pathlib.Path(v)
    @pydantic.validator('additional_data', pre=True, each_item=True)
    def validate_additional_data(cls, v, values, **kwargs):
        if isinstance(v, tuple) and len(v) == 2:
            return (pathlib.Path(v[0]), v[1])
        if isinstance(v, dict) and len(v) == 1:
            key = next(iter(v.keys()))
            return (pathlib.Path(key), v[key])
        raise ValueError(f'Invalid additional data format: {v}')
    def to_pyinstaller_args(self) -> List[str]:
        args = []
        if self.build_type == BuildType.ONEFILE:
            args.append('--onefile')
        else:
            args.append('--onedir')
        if self.console:
            args.append('--console')
        else:
            args.append('--windowed')
        if self.icon_path:
            args.extend(['--icon', str(self.icon_path)])
        args.extend(['--name', self.name])
        args.extend(['--distpath', str(self.output_dir)])
        if self.debug:
            args.append('--debug')
        if self.upx:
            args.append('--upx-dir')
            args.append('upx')
        else:
            args.append('--noupx')
        for item in self.upx_exclude:
            args.extend(['--upx-exclude', item])
        for module in self.hidden_imports:
            args.extend(['--hidden-import', module])
        for src_path, dest_path in self.additional_data.items():
            args.extend(['--add-data', f'{src_path}{os.pathsep}{dest_path}'])
        for name, value in self.environment_vars.items():
            args.extend(['--env', f'{name}={value}'])
        for path in self.include_paths:
            args.extend(['--paths', str(path)])
        for path in self.exclude_paths:
            args.extend(['--exclude-module', str(path)])
        args.append(str(self.entry_point))
        return args
    def get_output_path(self) -> pathlib.Path:
        if self.build_type == BuildType.ONEFILE:
            if self.platform == BuildPlatform.WINDOWS:
                return self.output_dir / f'{self.name}.exe'
            else:
                return self.output_dir / self.name
        else:
            return self.output_dir / self.name
    @classmethod
    def from_dict(cls, config_dict: Dict) -> BuildConfig:
        return cls(**config_dict)
    @classmethod
    def from_json_file(cls, json_path: Union[str, pathlib.Path]) -> BuildConfig:
        import json
        with open(json_path, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    def to_dict(self) -> Dict:
        config_dict = self.dict()
        for key, value in config_dict.items():
            if isinstance(value, list) and value and isinstance(value[0], pathlib.Path):
                config_dict[key] = [str(p) for p in value]
            elif isinstance(value, pathlib.Path):
                config_dict[key] = str(value)
            elif isinstance(value, dict) and any((isinstance(k, pathlib.Path) for k in value.keys())):
                config_dict[key] = {str(k): v for k, v in value.items()}
        return config_dict
    def to_json_file(self, json_path: Union[str, pathlib.Path]) -> None:
        import json
        with open(json_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)