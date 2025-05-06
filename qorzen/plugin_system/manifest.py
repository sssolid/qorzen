"""Plugin manifest definition and validation.

This module defines the schema for plugin metadata and provides utilities
for creating, validating, and manipulating plugin manifests.
"""

from __future__ import annotations

import enum
import datetime
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any

import pydantic
from pydantic import Field, validator


class PluginCapability(str, enum.Enum):
    """Capabilities that a plugin can request.

    These capabilities define what a plugin is allowed to do within the system.
    Plugins must explicitly request capabilities, and users must approve them
    during installation.
    """

    # Basic capabilities
    CONFIG_READ = "config.read"
    CONFIG_WRITE = "config.write"
    UI_EXTEND = "ui.extend"
    EVENT_SUBSCRIBE = "event.subscribe"
    EVENT_PUBLISH = "event.publish"

    # File system capabilities
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"

    # Network capabilities
    NETWORK_CONNECT = "network.connect"

    # Database capabilities
    DATABASE_READ = "database.read"
    DATABASE_WRITE = "database.write"

    # System capabilities (high privilege)
    SYSTEM_EXEC = "system.exec"
    SYSTEM_MONITOR = "system.monitor"

    # Integration capabilities
    PLUGIN_COMMUNICATE = "plugin.communicate"

    @classmethod
    def get_description(cls, capability: PluginCapability) -> str:
        """Get a human-readable description of a capability.

        Args:
            capability: The capability to describe

        Returns:
            Human-readable description of the capability
        """
        descriptions = {
            cls.CONFIG_READ: "Read application configuration settings",
            cls.CONFIG_WRITE: "Modify application configuration settings",
            cls.UI_EXTEND: "Add elements to the user interface",
            cls.EVENT_SUBSCRIBE: "Subscribe to application events",
            cls.EVENT_PUBLISH: "Publish events to the application event bus",
            cls.FILE_READ: "Read files from the file system",
            cls.FILE_WRITE: "Write files to the file system",
            cls.NETWORK_CONNECT: "Connect to external services over the network",
            cls.DATABASE_READ: "Read data from the application database",
            cls.DATABASE_WRITE: "Write data to the application database",
            cls.SYSTEM_EXEC: "Execute system commands (high privilege)",
            cls.SYSTEM_MONITOR: "Monitor system resources and performance",
            cls.PLUGIN_COMMUNICATE: "Communicate with other plugins",
        }
        return descriptions.get(capability, "Unknown capability")

    @classmethod
    def get_risk_level(cls, capability: PluginCapability) -> str:
        """Get the risk level associated with a capability.

        Args:
            capability: The capability to check

        Returns:
            Risk level: "low", "medium", or "high"
        """
        high_risk = {cls.SYSTEM_EXEC, cls.DATABASE_WRITE, cls.FILE_WRITE}
        medium_risk = {cls.CONFIG_WRITE, cls.NETWORK_CONNECT, cls.DATABASE_READ}

        if capability in high_risk:
            return "high"
        elif capability in medium_risk:
            return "medium"
        else:
            return "low"


class PluginAuthor(pydantic.BaseModel):
    """Information about a plugin author.

    Attributes:
        name: Author's name
        email: Author's email address
        url: Author's website URL
        organization: Optional organization the author belongs to
    """

    name: str
    email: str
    url: Optional[str] = None
    organization: Optional[str] = None

    @validator('email')
    def validate_email(cls, v: str) -> str:
        """Validate that the email address is properly formatted.

        Args:
            v: Email address to validate

        Returns:
            Validated email address

        Raises:
            ValueError: If the email address format is invalid
        """
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email address format")
        return v

    @validator('url')
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the URL is properly formatted.

        Args:
            v: URL to validate

        Returns:
            Validated URL

        Raises:
            ValueError: If the URL format is invalid
        """
        if v is None:
            return None

        url_regex = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9._~:/?#[\]@!$&'()*+,;=%-]*)?$"
        if not re.match(url_regex, v):
            raise ValueError("Invalid URL format")
        return v


class PluginDependency(pydantic.BaseModel):
    """A dependency on another plugin or the core application.

    Attributes:
        name: Name of the dependency (plugin name or "core")
        version: Version requirement (semver format)
        optional: Whether this dependency is optional
        url: Optional URL where the dependency can be downloaded
    """

    name: str
    version: str
    optional: bool = False
    url: Optional[str] = None

    @validator('version')
    def validate_version(cls, v: str) -> str:
        """Validate that the version is in semantic versioning format.

        Args:
            v: Version string to validate

        Returns:
            Validated version string

        Raises:
            ValueError: If the version format is invalid
        """
        # Basic semver validation with optional comparisons
        semver_regex = r"^(=|>=|<=|>|<|~=|!=|^)?(\d+)\.(\d+)\.(\d+)(-[0-9a-zA-Z.-]+)?(\+[0-9a-zA-Z.-]+)?$"
        if not re.match(semver_regex, v):
            raise ValueError("Version must be in semantic versioning format (e.g., '>=1.2.3')")
        return v


class PluginManifest(pydantic.BaseModel):
    """Manifest containing metadata for a Qorzen plugin.

    This class defines the schema for plugin metadata, including version,
    dependencies, capabilities, and other important information.

    Attributes:
        name: Unique identifier for the plugin
        display_name: Human-readable name for the plugin
        version: Plugin version in semantic versioning format
        description: Brief description of the plugin
        author: Plugin author information
        license: License identifier (e.g., MIT, GPL-3.0)
        homepage: URL to the plugin's homepage or repository
        capabilities: Capabilities requested by the plugin
        dependencies: Other plugins or components that this plugin depends on
        entry_point: Path to the main module or class
        min_core_version: Minimum required version of the Qorzen core
        max_core_version: Maximum supported version of the Qorzen core
        created_at: When the plugin was first created
        updated_at: When the plugin was last updated
        tags: Tags for categorizing the plugin
        icon: Path to the plugin's icon file
        readme: Path to the plugin's readme file
        changelog: Path to the plugin's changelog file
        signature: Digital signature for this manifest
        uuid: Unique ID for this specific plugin version
    """

    name: str
    display_name: str
    version: str
    description: str
    author: PluginAuthor
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

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate that the plugin name is valid.

        Args:
            v: Plugin name to validate

        Returns:
            Validated plugin name

        Raises:
            ValueError: If the plugin name format is invalid
        """
        name_regex = r"^[a-z][a-z0-9_-]{2,63}$"
        if not re.match(name_regex, v):
            raise ValueError(
                "Plugin name must be 3-64 characters, start with a lowercase letter, "
                "and contain only lowercase letters, numbers, underscores, and hyphens"
            )
        return v

    @validator('version')
    def validate_version(cls, v: str) -> str:
        """Validate that the version is in semantic versioning format.

        Args:
            v: Version string to validate

        Returns:
            Validated version string

        Raises:
            ValueError: If the version format is invalid
        """
        semver_regex = r"^(\d+)\.(\d+)\.(\d+)(-[0-9a-zA-Z.-]+)?(\+[0-9a-zA-Z.-]+)?$"
        if not re.match(semver_regex, v):
            raise ValueError("Version must be in semantic versioning format (e.g., '1.2.3')")
        return v

    @validator('min_core_version', 'max_core_version')
    def validate_core_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the core version is in semantic versioning format.

        Args:
            v: Core version string to validate

        Returns:
            Validated core version string

        Raises:
            ValueError: If the core version format is invalid
        """
        if v is None:
            return None

        semver_regex = r"^(\d+)\.(\d+)\.(\d+)(-[0-9a-zA-Z.-]+)?(\+[0-9a-zA-Z.-]+)?$"
        if not re.match(semver_regex, v):
            raise ValueError("Core version must be in semantic versioning format (e.g., '1.2.3')")
        return v

    @validator('license')
    def validate_license(cls, v: str) -> str:
        """Validate that the license identifier is a known SPDX identifier.

        Args:
            v: License identifier to validate

        Returns:
            Validated license identifier

        Raises:
            ValueError: If the license identifier is not recognized
        """
        # This is a simplified list of common SPDX license identifiers
        common_licenses = {
            "MIT", "Apache-2.0", "GPL-3.0", "GPL-2.0", "LGPL-3.0", "LGPL-2.1",
            "BSD-3-Clause", "BSD-2-Clause", "MPL-2.0", "AGPL-3.0", "Unlicense",
            "proprietary", "custom"
        }

        if v not in common_licenses:
            # Just warn about uncommon licenses, don't reject them
            # since there are many valid SPDX identifiers
            cls._warn(f"License '{v}' is not a common SPDX identifier")

        return v

    @classmethod
    def _warn(cls, msg: str) -> None:
        """Helper method to issue warnings during validation."""
        import warnings
        warnings.warn(msg)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the manifest to a dictionary.

        Returns:
            Dictionary representation of the manifest
        """
        data = self.dict(exclude={"signature"})

        # Convert enum values to strings
        if "capabilities" in data:
            data["capabilities"] = [str(cap) for cap in data["capabilities"]]

        # Convert datetime objects to ISO format strings
        if "created_at" in data and isinstance(data["created_at"], datetime.datetime):
            data["created_at"] = data["created_at"].isoformat()
        if "updated_at" in data and isinstance(data["updated_at"], datetime.datetime):
            data["updated_at"] = data["updated_at"].isoformat()

        return data

    def to_json(self) -> str:
        """Convert the manifest to a JSON string.

        Returns:
            JSON string representation of the manifest
        """
        import json
        return json.dumps(self.to_dict(), indent=2)

    def save(self, path: Union[str, Path]) -> None:
        """Save the manifest to a file.

        Args:
            path: Path where the manifest will be saved
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Union[str, Path]) -> PluginManifest:
        """Load a manifest from a file.

        Args:
            path: Path to the manifest file

        Returns:
            Loaded manifest

        Raises:
            FileNotFoundError: If the manifest file does not exist
            ValueError: If the manifest file is invalid
        """
        import json

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Convert string capabilities back to enum values
            if "capabilities" in data:
                data["capabilities"] = [
                    PluginCapability(cap) for cap in data["capabilities"]
                ]

            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid manifest file: {e}")
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid manifest data: {e}")

    def get_capability_risks(self) -> Dict[str, List[str]]:
        """Get a breakdown of capabilities by risk level.

        Returns:
            Dictionary mapping risk levels to lists of capabilities
        """
        risks: Dict[str, List[str]] = {
            "high": [],
            "medium": [],
            "low": []
        }

        for capability in self.capabilities:
            risk_level = PluginCapability.get_risk_level(capability)
            risks[risk_level].append(capability.value)

        return risks

    def satisfies_dependency(self, dependency: PluginDependency) -> bool:
        """Check if this plugin satisfies the given dependency.

        Args:
            dependency: Dependency to check

        Returns:
            True if this plugin satisfies the dependency, False otherwise
        """
        if dependency.name != self.name:
            return False

        import re
        import semver

        # Parse the dependency version requirement
        version_req = dependency.version
        match = re.match(r"^(=|>=|<=|>|<|~=|!=|\^)?(.+)$", version_req)
        if not match:
            return False

        operator, version = match.groups()
        operator = operator or "="  # Default to exact match

        try:
            plugin_version = semver.Version.parse(self.version)
            dependency_version = semver.Version.parse(version)

            if operator == "=":
                return plugin_version == dependency_version
            elif operator == ">":
                return plugin_version > dependency_version
            elif operator == ">=":
                return plugin_version >= dependency_version
            elif operator == "<":
                return plugin_version < dependency_version
            elif operator == "<=":
                return plugin_version <= dependency_version
            elif operator == "!=":
                return plugin_version != dependency_version
            elif operator == "~=":
                # Compatible release (~= 1.2.3 means >= 1.2.3, < 1.3.0)
                return (
                        plugin_version >= dependency_version and
                        plugin_version.major == dependency_version.major and
                        plugin_version.minor == dependency_version.minor
                )
            elif operator == "^":
                # Compatible release (^1.2.3 means >= 1.2.3, < 2.0.0)
                return (
                        plugin_version >= dependency_version and
                        plugin_version.major == dependency_version.major
                )
            else:
                return False
        except ValueError:
            return False

    def is_compatible_with_core(self, core_version: str) -> bool:
        """Check if this plugin is compatible with the given core version.

        Args:
            core_version: Core version to check compatibility with

        Returns:
            True if the plugin is compatible, False otherwise
        """
        import semver

        try:
            core_ver = semver.Version.parse(core_version)
            min_ver = semver.Version.parse(self.min_core_version)

            # Check minimum core version
            if core_ver < min_ver:
                return False

            # Check maximum core version if specified
            if self.max_core_version:
                max_ver = semver.Version.parse(self.max_core_version)
                if core_ver > max_ver:
                    return False

            return True
        except ValueError:
            return False