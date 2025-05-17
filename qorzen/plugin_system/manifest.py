from __future__ import annotations
import enum
import datetime
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, TYPE_CHECKING

import pydantic
from pydantic import Field, validator

if TYPE_CHECKING:
    from qorzen.plugin_system.config_schema import ConfigSchema

class PluginCapability(str, enum.Enum):
    CONFIG_READ = 'config.read'
    CONFIG_WRITE = 'config.write'
    UI_EXTEND = 'ui.extend'
    EVENT_SUBSCRIBE = 'event.subscribe'
    EVENT_PUBLISH = 'event.publish'
    FILE_READ = 'file.read'
    FILE_WRITE = 'file.write'
    NETWORK_CONNECT = 'network.connect'
    DATABASE_READ = 'database.read'
    DATABASE_WRITE = 'database.write'
    SYSTEM_EXEC = 'system.exec'
    SYSTEM_MONITOR = 'system.monitor'
    PLUGIN_COMMUNICATE = 'plugin.communicate'

    @classmethod
    def get_description(cls, capability: PluginCapability) -> str:
        descriptions = {
            cls.CONFIG_READ: 'Read application configuration settings',
            cls.CONFIG_WRITE: 'Modify application configuration settings',
            cls.UI_EXTEND: 'Add elements to the user interface',
            cls.EVENT_SUBSCRIBE: 'Subscribe to application events',
            cls.EVENT_PUBLISH: 'Publish events to the application event bus',
            cls.FILE_READ: 'Read files from the file system',
            cls.FILE_WRITE: 'Write files to the file system',
            cls.NETWORK_CONNECT: 'Connect to external services over the network',
            cls.DATABASE_READ: 'Read data from the application database',
            cls.DATABASE_WRITE: 'Write data to the application database',
            cls.SYSTEM_EXEC: 'Execute system commands (high privilege)',
            cls.SYSTEM_MONITOR: 'Monitor system resources and performance',
            cls.PLUGIN_COMMUNICATE: 'Communicate with other plugins'
        }
        return descriptions.get(capability, 'Unknown capability')

    @classmethod
    def get_risk_level(cls, capability: PluginCapability) -> str:
        high_risk = {cls.SYSTEM_EXEC, cls.DATABASE_WRITE, cls.FILE_WRITE}
        medium_risk = {cls.CONFIG_WRITE, cls.NETWORK_CONNECT, cls.DATABASE_READ}

        if capability in high_risk:
            return 'high'
        elif capability in medium_risk:
            return 'medium'
        else:
            return 'low'


class PluginAuthor(pydantic.BaseModel):
    name: str
    email: str
    url: Optional[str] = None
    organization: Optional[str] = None

    @validator('email')
    def validate_email(cls, v: str) -> str:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Invalid email address format')
        return v

    @validator('url')
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        url_regex = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9._~:/?#[\]@!$&'()*+,;=%-]*)?$"
        if not re.match(url_regex, v):
            raise ValueError('Invalid URL format')
        return v


class PluginDependency(pydantic.BaseModel):
    name: str
    version: str
    optional: bool = False
    url: Optional[str] = None

    @validator('version')
    def validate_version(cls, v: str) -> str:
        semver_regex = r'^(=|>=|<=|>|<|~=|!=|\^)?(\d+)\.(\d+)\.(\d+)(-[0-9a-zA-Z.-]+)?(\+[0-9a-zA-Z.-]+)?$'
        if not re.match(semver_regex, v):
            raise ValueError("Version must be in semantic versioning format (e.g., '>=1.2.3')")
        return v


class PluginExtensionPoint(pydantic.BaseModel):
    """Definition of an extension point provided by the plugin."""

    id: str
    name: str
    description: str
    interface: str
    version: str = "1.0.0"
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @validator('id')
    def validate_id(cls, v: str) -> str:
        id_regex = r'^[a-z][a-z0-9_\.]{2,63}$'
        if not re.match(id_regex, v):
            raise ValueError('Extension point ID must be 3-64 characters, start with a lowercase letter, and contain only lowercase letters, numbers, underscores, and dots')
        return v

    @validator('version')
    def validate_version(cls, v: str) -> str:
        semver_regex = r'^(\d+)\.(\d+)\.(\d+)(-[0-9a-zA-Z.-]+)?(\+[0-9a-zA-Z.-]+)?$'
        if not re.match(semver_regex, v):
            raise ValueError("Version must be in semantic versioning format (e.g., '1.2.3')")
        return v


class PluginExtensionUse(pydantic.BaseModel):
    """Definition of an extension point that the plugin uses."""

    provider: str
    id: str
    version: str = "1.0.0"
    required: bool = True

    @validator('version')
    def validate_version(cls, v: str) -> str:
        semver_regex = r'^(\d+)\.(\d+)\.(\d+)(-[0-9a-zA-Z.-]+)?(\+[0-9a-zA-Z.-]+)?$'
        if not re.match(semver_regex, v):
            raise ValueError("Version must be in semantic versioning format (e.g., '1.2.3')")
        return v


class PluginLifecycleHook(str, enum.Enum):
    """Enumeration of plugin lifecycle hooks."""

    PRE_INSTALL = "pre_install"
    POST_INSTALL = "post_install"
    PRE_UNINSTALL = "pre_uninstall"
    POST_UNINSTALL = "post_uninstall"
    PRE_ENABLE = "pre_enable"
    POST_ENABLE = "post_enable"
    PRE_DISABLE = "pre_disable"
    POST_DISABLE = "post_disable"
    PRE_UPDATE = "pre_update"
    POST_UPDATE = "post_update"


class PluginManifest(pydantic.BaseModel):
    name: str
    display_name: str
    version: str
    description: str
    author: PluginAuthor
    logo_path: str
    icon_path: str
    license: str
    homepage: Optional[str] = None
    capabilities: List[PluginCapability] = Field(default_factory=list)
    dependencies: List[PluginDependency] = Field(default_factory=list)
    entry_point: str
    min_core_version: str
    max_core_version: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    tags: List[str] = Field(default_factory=list)
    icon: Optional[str] = None
    readme: Optional[str] = None
    changelog: Optional[str] = None
    signature: Optional[str] = None
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # New fields for enhanced plugin system
    config_schema: Optional[Dict[str, Any]] = None
    extension_points: List[PluginExtensionPoint] = Field(default_factory=list)
    extension_uses: List[PluginExtensionUse] = Field(default_factory=list)
    lifecycle_hooks: Dict[PluginLifecycleHook, str] = Field(default_factory=dict)
    data_migrations: List[Dict[str, Any]] = Field(default_factory=list)

    @validator('name')
    def validate_name(cls, v: str) -> str:
        name_regex = r'^[a-z][a-z0-9_-]{2,63}$'
        if not re.match(name_regex, v):
            raise ValueError('Plugin name must be 3-64 characters, start with a lowercase letter, and contain only lowercase letters, numbers, underscores, and hyphens')
        return v

    @validator('version')
    def validate_version(cls, v: str) -> str:
        semver_regex = r'^(\d+)\.(\d+)\.(\d+)(-[0-9a-zA-Z.-]+)?(\+[0-9a-zA-Z.-]+)?$'
        if not re.match(semver_regex, v):
            raise ValueError("Version must be in semantic versioning format (e.g., '1.2.3')")
        return v

    @validator('min_core_version', 'max_core_version')
    def validate_core_version(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        semver_regex = r'^(\d+)\.(\d+)\.(\d+)(-[0-9a-zA-Z.-]+)?(\+[0-9a-zA-Z.-]+)?$'
        if not re.match(semver_regex, v):
            raise ValueError("Core version must be in semantic versioning format (e.g., '1.2.3')")
        return v

    @validator('license')
    def validate_license(cls, v: str) -> str:
        common_licenses = {
            'MIT', 'Apache-2.0', 'GPL-3.0', 'GPL-2.0', 'LGPL-3.0', 'LGPL-2.1',
            'BSD-3-Clause', 'BSD-2-Clause', 'MPL-2.0', 'AGPL-3.0', 'Unlicense',
            'proprietary', 'custom'
        }
        if v not in common_licenses:
            cls._warn(f"License '{v}' is not a common SPDX identifier")
        return v

    @validator('lifecycle_hooks')
    def validate_lifecycle_hooks(cls, v: Dict[PluginLifecycleHook, str]) -> Dict[PluginLifecycleHook, str]:
        """Validate that lifecycle hook values are valid callable paths."""
        for hook, path in v.items():
            parts = path.split('.')
            if len(parts) < 2:
                raise ValueError(f"Lifecycle hook path '{path}' must be a full module.function path")
        return v

    @classmethod
    def _warn(cls, msg: str) -> None:
        import warnings
        warnings.warn(msg)

    def to_dict(self) -> Dict[str, Any]:
        data = self.dict(exclude={'signature'})
        if 'capabilities' in data:
            data['capabilities'] = [str(cap) for cap in data['capabilities']]
        if 'created_at' in data and isinstance(data['created_at'], datetime.datetime):
            data['created_at'] = data['created_at'].isoformat()
        if 'updated_at' in data and isinstance(data['updated_at'], datetime.datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        if 'lifecycle_hooks' in data:
            data['lifecycle_hooks'] = {str(hook): path for hook, path in data['lifecycle_hooks'].items()}
        return data

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2)

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Union[str, Path]) -> PluginManifest:
        import json
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'Manifest file not found: {path}')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            if 'capabilities' in data:
                data['capabilities'] = [PluginCapability(cap) for cap in data['capabilities']]
            if 'lifecycle_hooks' in data:
                try:
                    data['lifecycle_hooks'] = {PluginLifecycleHook(hook): path for hook, path in data['lifecycle_hooks'].items()}
                except ValueError:
                    # Handle older manifests that might not have proper enum values
                    data['lifecycle_hooks'] = {}
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid manifest file: {e}')
        except pydantic.ValidationError as e:
            raise ValueError(f'Invalid manifest data: {e}')

    def get_capability_risks(self) -> Dict[str, List[str]]:
        risks: Dict[str, List[str]] = {'high': [], 'medium': [], 'low': []}
        for capability in self.capabilities:
            risk_level = PluginCapability.get_risk_level(capability)
            risks[risk_level].append(capability.value)
        return risks

    def satisfies_dependency(self, dependency: PluginDependency) -> bool:
        if dependency.name != self.name:
            return False

        import re
        try:
            import semver
        except ImportError:
            raise ImportError("The 'semver' package is required for version comparison")

        version_req = dependency.version
        match = re.match(r'^(=|>=|<=|>|<|~=|!=|\^)?(.+)$', version_req)
        if not match:
            return False

        operator, version = match.groups()
        operator = operator or '='

        try:
            plugin_version = semver.Version.parse(self.version)
            dependency_version = semver.Version.parse(version)

            if operator == '=':
                return plugin_version == dependency_version
            elif operator == '>':
                return plugin_version > dependency_version
            elif operator == '>=':
                return plugin_version >= dependency_version
            elif operator == '<':
                return plugin_version < dependency_version
            elif operator == '<=':
                return plugin_version <= dependency_version
            elif operator == '!=':
                return plugin_version != dependency_version
            elif operator == '~=':
                return (plugin_version >= dependency_version and
                        plugin_version.major == dependency_version.major and
                        plugin_version.minor == dependency_version.minor)
            elif operator == '^':
                return (plugin_version >= dependency_version and
                        plugin_version.major == dependency_version.major)
            else:
                return False
        except ValueError:
            return False

    def is_compatible_with_core(self, core_version: str) -> bool:
        try:
            import semver
        except ImportError:
            raise ImportError("The 'semver' package is required for version comparison")

        try:
            core_ver = semver.Version.parse(core_version)
            min_ver = semver.Version.parse(self.min_core_version)

            if core_ver < min_ver:
                return False

            if self.max_core_version:
                max_ver = semver.Version.parse(self.max_core_version)
                if core_ver > max_ver:
                    return False

            return True
        except ValueError:
            return False

    def set_config_schema(self, schema: "ConfigSchema") -> None:
        """Set the configuration schema for the plugin."""
        self.config_schema = schema.to_dict()

    def has_extension_point(self, extension_id: str) -> bool:
        """Check if the plugin provides a specific extension point."""
        return any(ext.id == extension_id for ext in self.extension_points)

    def get_extension_point(self, extension_id: str) -> Optional[PluginExtensionPoint]:
        """Get an extension point by ID."""
        for ext in self.extension_points:
            if ext.id == extension_id:
                return ext
        return None