"""Plugin installation and management.

This module provides utilities for installing, updating, and removing
plugin packages in the Qorzen system.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from qorzen.plugin_system.manifest import PluginManifest, PluginDependency
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginVerifier


@dataclass
class InstalledPlugin:
    """Information about an installed plugin.

    Attributes:
        manifest: Plugin manifest
        install_path: Path to the installed plugin directory
        installed_at: When the plugin was installed
        enabled: Whether the plugin is enabled
        plugin_data: Plugin-specific data
    """

    manifest: PluginManifest
    install_path: Path
    installed_at: datetime.datetime
    enabled: bool = True
    plugin_data: Dict[str, Any] = None

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.plugin_data is None:
            self.plugin_data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary.

        Returns:
            Dictionary representation of the installed plugin
        """
        return {
            "manifest": self.manifest.to_dict(),
            "install_path": str(self.install_path),
            "installed_at": self.installed_at.isoformat(),
            "enabled": self.enabled,
            "plugin_data": self.plugin_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InstalledPlugin:
        """Create an InstalledPlugin from a dictionary.

        Args:
            data: Dictionary with installed plugin data

        Returns:
            InstalledPlugin instance
        """
        manifest = PluginManifest(**data["manifest"])
        install_path = Path(data["install_path"])
        installed_at = datetime.datetime.fromisoformat(data["installed_at"])
        enabled = data.get("enabled", True)
        plugin_data = data.get("plugin_data", {})

        return cls(
            manifest=manifest,
            install_path=install_path,
            installed_at=installed_at,
            enabled=enabled,
            plugin_data=plugin_data
        )


class PluginInstallationError(Exception):
    """Exception raised for errors during plugin installation."""

    pass


class PluginInstaller:
    """Handler for installing and managing plugins.

    This class provides utilities for installing, updating, and removing
    plugin packages in the Qorzen system.

    Attributes:
        plugins_dir: Directory where plugins are installed
        verifier: Plugin verifier for signature verification
        installed_plugins: Dictionary of installed plugins by name
    """

    def __init__(
            self,
            plugins_dir: Union[str, Path],
            verifier: Optional[PluginVerifier] = None,
            logger: Optional[Callable[[str, str], None]] = None
    ) -> None:
        """Initialize the plugin installer.

        Args:
            plugins_dir: Directory where plugins will be installed
            verifier: Plugin verifier for signature verification
            logger: Logger function for recording installation events
        """
        self.plugins_dir = Path(plugins_dir)
        self.verifier = verifier or PluginVerifier()
        self.logger = logger or (lambda msg, level: print(f"[{level.upper()}] {msg}"))
        self.installed_plugins: Dict[str, InstalledPlugin] = {}

        # Create plugins directory if it doesn't exist
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        # Create installed plugins metadata file
        self.metadata_file = self.plugins_dir / "installed_plugins.json"

        # Load installed plugins
        self.load_installed_plugins()

    def log(self, message: str, level: str = "info") -> None:
        """Log a message.

        Args:
            message: Message to log
            level: Log level (info, warning, error, debug)
        """
        self.logger(message, level)

    def load_installed_plugins(self) -> None:
        """Load information about installed plugins.

        This reads the installed plugins metadata file and populates
        the installed_plugins dictionary.
        """
        if not self.metadata_file.exists():
            # No plugins installed yet
            return

        try:
            with open(self.metadata_file, "r") as f:
                data = json.load(f)

            for plugin_name, plugin_data in data.items():
                try:
                    installed_plugin = InstalledPlugin.from_dict(plugin_data)
                    self.installed_plugins[plugin_name] = installed_plugin
                except Exception as e:
                    self.log(f"Failed to load plugin metadata for {plugin_name}: {e}", "warning")

            self.log(f"Loaded {len(self.installed_plugins)} installed plugins")

        except Exception as e:
            self.log(f"Failed to load installed plugins metadata: {e}", "error")

    def save_installed_plugins(self) -> None:
        """Save information about installed plugins.

        This writes the installed plugins metadata to the metadata file.
        """
        try:
            data = {}
            for plugin_name, plugin in self.installed_plugins.items():
                data[plugin_name] = plugin.to_dict()

            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".json",
                    dir=self.plugins_dir,
                    delete=False
            ) as tmp:
                json.dump(data, tmp, indent=2)
                tmp_path = Path(tmp.name)

            # Replace the original file
            shutil.move(tmp_path, self.metadata_file)

        except Exception as e:
            self.log(f"Failed to save installed plugins metadata: {e}", "error")

    def get_plugin_dir(self, plugin_name: str) -> Path:
        """Get the directory for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Path to the plugin directory
        """
        return self.plugins_dir / plugin_name

    def is_plugin_installed(self, plugin_name: str) -> bool:
        """Check if a plugin is installed.

        Args:
            plugin_name: Name of the plugin to check

        Returns:
            True if the plugin is installed, False otherwise
        """
        return plugin_name in self.installed_plugins

    def get_installed_plugin(self, plugin_name: str) -> Optional[InstalledPlugin]:
        """Get information about an installed plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Installed plugin information, or None if not installed
        """
        return self.installed_plugins.get(plugin_name)

    def install_plugin(
            self,
            package_path: Union[str, Path],
            force: bool = False,
            skip_verification: bool = False,
            enable: bool = True
    ) -> InstalledPlugin:
        """Install a plugin from a package.

        Args:
            package_path: Path to the plugin package
            force: Whether to force installation (overwrite existing)
            skip_verification: Whether to skip signature verification
            enable: Whether to enable the plugin after installation

        Returns:
            Installed plugin information

        Raises:
            PluginInstallationError: If installation fails
        """
        try:
            # Load the package
            package = PluginPackage.load(package_path)

            if not package.manifest:
                raise PluginInstallationError("Package has no manifest")

            plugin_name = package.manifest.name
            plugin_version = package.manifest.version

            # Check if plugin is already installed
            if self.is_plugin_installed(plugin_name) and not force:
                installed = self.get_installed_plugin(plugin_name)
                if installed and installed.manifest.version == plugin_version:
                    self.log(f"Plugin {plugin_name} v{plugin_version} is already installed", "info")
                    return installed
                elif installed:
                    raise PluginInstallationError(
                        f"Plugin {plugin_name} is already installed with version "
                        f"{installed.manifest.version}. Use force=True to overwrite."
                    )

            # Verify package signature if not skipped
            if not skip_verification and self.verifier:
                self.log(f"Verifying signature for plugin {plugin_name}", "debug")
                if not self.verifier.verify_package(package):
                    raise PluginInstallationError(
                        f"Plugin package signature verification failed for {plugin_name}"
                    )

            # Create plugin directory
            plugin_dir = self.get_plugin_dir(plugin_name)
            if plugin_dir.exists():
                if force:
                    # Backup and remove existing plugin
                    self._backup_plugin(plugin_name)
                    shutil.rmtree(plugin_dir)
                else:
                    raise PluginInstallationError(
                        f"Plugin directory already exists: {plugin_dir}"
                    )

            plugin_dir.mkdir(parents=True, exist_ok=True)

            # Extract package to plugin directory
            self.log(f"Extracting plugin {plugin_name} to {plugin_dir}", "debug")
            package.extract(plugin_dir)

            # Create installed plugin metadata
            installed_plugin = InstalledPlugin(
                manifest=package.manifest,
                install_path=plugin_dir,
                installed_at=datetime.datetime.now(),
                enabled=enable
            )

            # Add to installed plugins
            self.installed_plugins[plugin_name] = installed_plugin

            # Save installed plugins metadata
            self.save_installed_plugins()

            self.log(f"Successfully installed plugin {plugin_name} v{plugin_version}", "info")

            return installed_plugin

        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f"Failed to install plugin: {e}")
            self.log(str(e), "error")
            raise

    def update_plugin(
            self,
            package_path: Union[str, Path],
            skip_verification: bool = False
    ) -> InstalledPlugin:
        """Update an installed plugin.

        Args:
            package_path: Path to the updated plugin package
            skip_verification: Whether to skip signature verification

        Returns:
            Updated plugin information

        Raises:
            PluginInstallationError: If update fails
        """
        # Load the package to get the plugin name
        try:
            package = PluginPackage.load(package_path)

            if not package.manifest:
                raise PluginInstallationError("Package has no manifest")

            plugin_name = package.manifest.name
            plugin_version = package.manifest.version

            # Check if plugin is installed
            if not self.is_plugin_installed(plugin_name):
                raise PluginInstallationError(
                    f"Plugin {plugin_name} is not installed, cannot update"
                )

            # Get current plugin information
            current_plugin = self.get_installed_plugin(plugin_name)
            if not current_plugin:
                raise PluginInstallationError(
                    f"Failed to get information about installed plugin {plugin_name}"
                )

            current_version = current_plugin.manifest.version

            # Compare versions
            import semver
            try:
                current_ver = semver.Version.parse(current_version)
                new_ver = semver.Version.parse(plugin_version)

                if new_ver <= current_ver:
                    self.log(
                        f"New version ({plugin_version}) is not newer than current "
                        f"version ({current_version}), updating anyway",
                        "warning"
                    )

            except Exception:
                self.log(
                    f"Failed to compare versions {current_version} and {plugin_version}, "
                    f"continuing with update",
                    "warning"
                )

            # Install the new version (force overwrite)
            return self.install_plugin(
                package_path=package_path,
                force=True,
                skip_verification=skip_verification,
                enable=current_plugin.enabled
            )

        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f"Failed to update plugin: {e}")
            self.log(str(e), "error")
            raise

    def uninstall_plugin(self, plugin_name: str, keep_data: bool = False) -> bool:
        """Uninstall a plugin.

        Args:
            plugin_name: Name of the plugin to uninstall
            keep_data: Whether to keep plugin data

        Returns:
            True if the plugin was uninstalled, False otherwise

        Raises:
            PluginInstallationError: If uninstallation fails
        """
        try:
            # Check if plugin is installed
            if not self.is_plugin_installed(plugin_name):
                self.log(f"Plugin {plugin_name} is not installed", "warning")
                return False

            # Get plugin information
            plugin = self.get_installed_plugin(plugin_name)
            if not plugin:
                raise PluginInstallationError(
                    f"Failed to get information about installed plugin {plugin_name}"
                )

            # Check if other plugins depend on this one
            dependencies = self._get_dependent_plugins(plugin_name)
            if dependencies:
                dep_names = ", ".join(dependencies)
                raise PluginInstallationError(
                    f"Cannot uninstall plugin {plugin_name} because other plugins "
                    f"depend on it: {dep_names}"
                )

            # Backup the plugin before removal
            self._backup_plugin(plugin_name)

            # Remove plugin directory
            plugin_dir = self.get_plugin_dir(plugin_name)
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)

            # Remove from installed plugins
            del self.installed_plugins[plugin_name]

            # Save installed plugins metadata
            self.save_installed_plugins()

            self.log(f"Successfully uninstalled plugin {plugin_name}", "info")

            return True

        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f"Failed to uninstall plugin: {e}")
            self.log(str(e), "error")
            raise

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin.

        Args:
            plugin_name: Name of the plugin to enable

        Returns:
            True if the plugin was enabled, False otherwise
        """
        # Check if plugin is installed
        if not self.is_plugin_installed(plugin_name):
            self.log(f"Plugin {plugin_name} is not installed", "warning")
            return False

        # Get plugin information
        plugin = self.get_installed_plugin(plugin_name)
        if not plugin:
            self.log(f"Failed to get information about installed plugin {plugin_name}", "error")
            return False

        # Check if plugin is already enabled
        if plugin.enabled:
            self.log(f"Plugin {plugin_name} is already enabled", "info")
            return True

        # Enable the plugin
        plugin.enabled = True

        # Save installed plugins metadata
        self.save_installed_plugins()

        self.log(f"Successfully enabled plugin {plugin_name}", "info")

        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_name: Name of the plugin to disable

        Returns:
            True if the plugin was disabled, False otherwise
        """
        # Check if plugin is installed
        if not self.is_plugin_installed(plugin_name):
            self.log(f"Plugin {plugin_name} is not installed", "warning")
            return False

        # Get plugin information
        plugin = self.get_installed_plugin(plugin_name)
        if not plugin:
            self.log(f"Failed to get information about installed plugin {plugin_name}", "error")
            return False

        # Check if plugin is already disabled
        if not plugin.enabled:
            self.log(f"Plugin {plugin_name} is already disabled", "info")
            return True

        # Check if other plugins depend on this one
        dependencies = self._get_dependent_plugins(plugin_name)
        if dependencies:
            dep_names = ", ".join(dependencies)
            self.log(
                f"Warning: Disabling plugin {plugin_name} may affect these "
                f"dependent plugins: {dep_names}",
                "warning"
            )

        # Disable the plugin
        plugin.enabled = False

        # Save installed plugins metadata
        self.save_installed_plugins()

        self.log(f"Successfully disabled plugin {plugin_name}", "info")

        return True

    def get_installed_plugins(self) -> Dict[str, InstalledPlugin]:
        """Get information about all installed plugins.

        Returns:
            Dictionary of installed plugins by name
        """
        return self.installed_plugins.copy()

    def get_enabled_plugins(self) -> Dict[str, InstalledPlugin]:
        """Get information about enabled plugins.

        Returns:
            Dictionary of enabled plugins by name
        """
        return {
            name: plugin for name, plugin in self.installed_plugins.items()
            if plugin.enabled
        }

    def _backup_plugin(self, plugin_name: str) -> Optional[Path]:
        """Create a backup of a plugin before modifications.

        Args:
            plugin_name: Name of the plugin to backup

        Returns:
            Path to the backup file, or None if backup failed
        """
        try:
            plugin = self.get_installed_plugin(plugin_name)
            if not plugin:
                return None

            plugin_dir = self.get_plugin_dir(plugin_name)
            if not plugin_dir.exists():
                return None

            # Create backups directory if it doesn't exist
            backups_dir = self.plugins_dir / "backups"
            backups_dir.mkdir(exist_ok=True)

            # Create backup file name with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{plugin_name}_v{plugin.manifest.version}_{timestamp}.zip"
            backup_path = backups_dir / backup_filename

            # Create backup as ZIP file
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Package the current plugin installation
                    package = PluginPackage.create(
                        source_dir=plugin_dir,
                        output_path=backup_path,
                        manifest=plugin.manifest
                    )
                    return backup_path
                except Exception as e:
                    self.log(f"Failed to create backup package: {e}", "warning")

                    # Fall back to simple directory copy if packaging fails
                    backup_path = backups_dir / f"{plugin_name}_{timestamp}"
                    shutil.copytree(plugin_dir, backup_path)
                    return backup_path

        except Exception as e:
            self.log(f"Failed to backup plugin {plugin_name}: {e}", "warning")
            return None

    def _get_dependent_plugins(self, plugin_name: str) -> List[str]:
        """Get a list of plugins that depend on a given plugin.

        Args:
            plugin_name: Name of the plugin to check

        Returns:
            List of plugin names that depend on the given plugin
        """
        dependent_plugins = []

        for name, plugin in self.installed_plugins.items():
            if name == plugin_name:
                continue

            # Check if this plugin depends on the given plugin
            for dependency in plugin.manifest.dependencies:
                if dependency.name == plugin_name:
                    dependent_plugins.append(name)
                    break

        return dependent_plugins

    def resolve_dependencies(
            self,
            package_path: Union[str, Path],
            repository_url: Optional[str] = None
    ) -> Dict[str, Union[str, bool]]:
        """Resolve dependencies for a plugin package.

        Args:
            package_path: Path to the plugin package
            repository_url: URL of the plugin repository

        Returns:
            Dictionary mapping dependency names to status or package path

        Raises:
            PluginInstallationError: If dependency resolution fails
        """
        try:
            # Load the package
            package = PluginPackage.load(package_path)

            if not package.manifest:
                raise PluginInstallationError("Package has no manifest")

            plugin_name = package.manifest.name
            dependencies = package.manifest.dependencies

            if not dependencies:
                return {}

            result = {}

            for dependency in dependencies:
                dep_name = dependency.name

                # Skip "core" dependency
                if dep_name == "core":
                    result[dep_name] = True
                    continue

                # Check if dependency is already installed
                if self.is_plugin_installed(dep_name):
                    installed = self.get_installed_plugin(dep_name)
                    if installed and installed.manifest.satisfies_dependency(dependency):
                        result[dep_name] = True
                    else:
                        # Installed version doesn't satisfy dependency
                        result[dep_name] = False
                else:
                    # Dependency not installed
                    result[dep_name] = False

                    # Try to download from repository if URL provided
                    if repository_url and dependency.url:
                        # This would integrate with the repository client
                        # to download dependencies automatically
                        pass

            return result

        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f"Failed to resolve dependencies: {e}")
            self.log(str(e), "error")
            raise