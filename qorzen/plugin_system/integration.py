from __future__ import annotations

import os
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable

from qorzen.plugin_system.dependency import DependencyResolver, DependencyError
from qorzen.plugin_system.installer import PluginInstaller, PluginInstallationError, InstalledPlugin
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.repository import PluginRepositoryManager, PluginRepositoryError
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.lifecycle import execute_hook, LifecycleHookError


class PluginIntegrationError(Exception):
    """Exception raised when there's an error in plugin integration."""
    pass


class IntegratedPluginInstaller:
    """
    Plugin installer integrated with repository and dependency resolution.

    This class extends the basic plugin installer with repository integration
    and automatic dependency resolution.
    """

    def __init__(
            self,
            plugins_dir: Union[str, Path],
            repository_manager: Optional[PluginRepositoryManager] = None,
            verifier: Optional[PluginVerifier] = None,
            logger: Optional[Callable[[str, str], None]] = None,
            core_version: str = "0.1.0"
    ):
        self.plugins_dir = Path(plugins_dir)
        self.repository_manager = repository_manager
        self.logger = logger or (lambda msg, level: print(f"[{level.upper()}] {msg}"))

        # Create basic installer
        self.installer = PluginInstaller(
            plugins_dir=plugins_dir,
            verifier=verifier,
            logger=logger
        )

        # Create dependency resolver
        self.dependency_resolver = DependencyResolver(
            repository_manager=repository_manager,
            logger=logger
        )
        self.dependency_resolver.set_plugins_dir(plugins_dir)
        self.dependency_resolver.set_core_version(core_version)

        # Sync installed plugins with dependency resolver
        self._sync_installed_plugins()

    def _sync_installed_plugins(self) -> None:
        """Sync installed plugins with dependency resolver."""
        installed_plugins = {}
        for name, plugin in self.installer.get_installed_plugins().items():
            installed_plugins[name] = plugin.manifest
        self.dependency_resolver.set_installed_plugins(installed_plugins)

    def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        self.logger(message, level)

    def get_installed_plugins(self) -> Dict[str, InstalledPlugin]:
        """Get all installed plugins."""
        return self.installer.get_installed_plugins()

    def get_enabled_plugins(self) -> Dict[str, InstalledPlugin]:
        """Get all enabled plugins."""
        return self.installer.get_enabled_plugins()

    def get_installed_plugin(self, plugin_name: str) -> Optional[InstalledPlugin]:
        """Get an installed plugin by name."""
        return self.installer.get_installed_plugin(plugin_name)

    def is_plugin_installed(self, plugin_name: str) -> bool:
        """Check if a plugin is installed."""
        return self.installer.is_plugin_installed(plugin_name)

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        return self.installer.enable_plugin(plugin_name)

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        return self.installer.disable_plugin(plugin_name)

    def install_plugin(
            self,
            package_path: Union[str, Path],
            force: bool = False,
            skip_verification: bool = False,
            enable: bool = True,
            resolve_dependencies: bool = True,
            install_dependencies: bool = True
    ) -> InstalledPlugin:
        """
        Install a plugin with dependency resolution.

        Args:
            package_path: Path to the plugin package
            force: Whether to overwrite existing plugins
            skip_verification: Whether to skip signature verification
            enable: Whether to enable the plugin after installation
            resolve_dependencies: Whether to resolve dependencies
            install_dependencies: Whether to install missing dependencies

        Returns:
            The installed plugin

        Raises:
            PluginInstallationError: If there's an error during installation
            DependencyError: If there's an error resolving dependencies
        """
        # Load the package to get the manifest
        package = PluginPackage.load(package_path)
        if not package.manifest:
            raise PluginInstallationError("Package has no manifest")

        manifest = package.manifest
        plugin_name = manifest.name

        # Execute pre-install hook if defined
        try:
            if PluginLifecycleHook.PRE_INSTALL in manifest.lifecycle_hooks:
                # Extract to temporary directory to get hook code
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    package.extract(temp_path)

                    # Add to sys.path temporarily
                    import sys
                    original_path = sys.path.copy()
                    sys.path.insert(0, str(temp_path))

                    try:
                        # Execute the hook
                        execute_hook(
                            hook=PluginLifecycleHook.PRE_INSTALL,
                            plugin_name=plugin_name,
                            manifest=manifest,
                            context={
                                "package_path": str(package_path),
                                "force": force,
                                "skip_verification": skip_verification,
                                "enable": enable,
                                "resolve_dependencies": resolve_dependencies,
                                "install_dependencies": install_dependencies,
                                "plugins_dir": str(self.plugins_dir)
                            }
                        )
                    finally:
                        # Restore sys.path
                        sys.path = original_path
        except LifecycleHookError as e:
            raise PluginInstallationError(f"Pre-install hook failed: {str(e)}")

        # Resolve dependencies if requested
        if resolve_dependencies:
            try:
                dependencies = self.dependency_resolver.resolve_dependencies(
                    plugin_manifest=manifest,
                    resolve_transitives=True,
                    fetch_missing=False
                )

                # Check for missing dependencies
                missing_deps = [
                    (name, version) for name, version, is_local in dependencies
                    if not is_local and name != "core"
                ]

                if missing_deps and not install_dependencies:
                    missing_list = ", ".join([f"{name} ({version})" for name, version in missing_deps])
                    raise PluginInstallationError(
                        f"Plugin {plugin_name} has missing dependencies: {missing_list}. "
                        f"Use install_dependencies=True to install them automatically."
                    )

                # Install missing dependencies if requested
                if missing_deps and install_dependencies:
                    if not self.repository_manager:
                        raise PluginInstallationError(
                            f"Plugin {plugin_name} has missing dependencies, but no repository "
                            f"manager is available to install them."
                        )

                    self.log(f"Installing {len(missing_deps)} dependencies for plugin {plugin_name}", "info")

                    for dep_name, dep_version in missing_deps:
                        try:
                            # Find the dependency in a repository
                            self.log(f"Searching for dependency {dep_name} ({dep_version})", "debug")

                            # Try to find a compatible version
                            compatible_version = None
                            compatible_repo = None

                            for repo_name, repo in self.repository_manager.repositories.items():
                                try:
                                    versions = repo.get_plugin_versions(dep_name)
                                    for version_info in versions:
                                        # Check if this version is compatible
                                        # (simplified check, should use proper version comparison)
                                        if version_info.version == dep_version:
                                            compatible_version = version_info
                                            compatible_repo = repo_name
                                            break

                                    if compatible_version:
                                        break
                                except Exception as e:
                                    self.log(f"Error searching repository {repo_name}: {str(e)}", "warning")

                            if not compatible_version:
                                raise PluginInstallationError(
                                    f"Could not find compatible version of dependency {dep_name} ({dep_version})"
                                )

                            # Download the dependency
                            self.log(f"Downloading dependency {dep_name} ({dep_version}) from {compatible_repo}",
                                     "info")
                            download_path = self.repository_manager.get_repository(compatible_repo).download_plugin(
                                plugin_name=dep_name,
                                version=dep_version
                            )

                            # Install the dependency
                            self.log(f"Installing dependency {dep_name} ({dep_version})", "info")
                            self.installer.install_plugin(
                                package_path=download_path,
                                force=force,
                                skip_verification=skip_verification,
                                enable=enable
                            )

                        except Exception as e:
                            raise PluginInstallationError(
                                f"Failed to install dependency {dep_name} ({dep_version}): {str(e)}"
                            ) from e

            except DependencyError as e:
                raise PluginInstallationError(f"Dependency error: {str(e)}") from e

        # Install the plugin
        installed_plugin = self.installer.install_plugin(
            package_path=package_path,
            force=force,
            skip_verification=skip_verification,
            enable=enable
        )

        # Update installed plugins in dependency resolver
        self._sync_installed_plugins()

        # Execute post-install hook if defined
        try:
            if PluginLifecycleHook.POST_INSTALL in manifest.lifecycle_hooks:
                execute_hook(
                    hook=PluginLifecycleHook.POST_INSTALL,
                    plugin_name=plugin_name,
                    manifest=manifest,
                    context={
                        "package_path": str(package_path),
                        "force": force,
                        "skip_verification": skip_verification,
                        "enable": enable,
                        "resolve_dependencies": resolve_dependencies,
                        "install_dependencies": install_dependencies,
                        "plugins_dir": str(self.plugins_dir),
                        "install_path": str(installed_plugin.install_path)
                    }
                )
        except LifecycleHookError as e:
            self.log(f"Post-install hook failed: {str(e)}", "warning")

        return installed_plugin

    def uninstall_plugin(
            self,
            plugin_name: str,
            keep_data: bool = False,
            check_dependents: bool = True
    ) -> bool:
        """
        Uninstall a plugin.

        Args:
            plugin_name: The name of the plugin to uninstall
            keep_data: Whether to keep plugin data
            check_dependents: Whether to check for dependents

        Returns:
            True if successful, False otherwise

        Raises:
            PluginInstallationError: If there's an error during uninstallation
        """
        # Check if the plugin is installed
        if not self.is_plugin_installed(plugin_name):
            return False

        installed_plugin = self.get_installed_plugin(plugin_name)
        if not installed_plugin:
            return False

        manifest = installed_plugin.manifest

        # Check for dependents if requested
        if check_dependents:
            dependents = self._get_dependent_plugins(plugin_name)
            if dependents:
                dep_names = ", ".join(dependents)
                raise PluginInstallationError(
                    f"Cannot uninstall plugin {plugin_name} because other plugins depend on it: {dep_names}"
                )

        # Execute pre-uninstall hook if defined
        try:
            if PluginLifecycleHook.PRE_UNINSTALL in manifest.lifecycle_hooks:
                execute_hook(
                    hook=PluginLifecycleHook.PRE_UNINSTALL,
                    plugin_name=plugin_name,
                    manifest=manifest,
                    context={
                        "keep_data": keep_data,
                        "check_dependents": check_dependents,
                        "plugins_dir": str(self.plugins_dir),
                        "install_path": str(installed_plugin.install_path)
                    }
                )
        except LifecycleHookError as e:
            raise PluginInstallationError(f"Pre-uninstall hook failed: {str(e)}")

        # Uninstall the plugin
        result = self.installer.uninstall_plugin(
            plugin_name=plugin_name,
            keep_data=keep_data
        )

        if result:
            # Update installed plugins in dependency resolver
            self._sync_installed_plugins()

            # Execute post-uninstall hook if defined
            try:
                if PluginLifecycleHook.POST_UNINSTALL in manifest.lifecycle_hooks:
                    execute_hook(
                        hook=PluginLifecycleHook.POST_UNINSTALL,
                        plugin_name=plugin_name,
                        manifest=manifest,
                        context={
                            "keep_data": keep_data,
                            "check_dependents": check_dependents,
                            "plugins_dir": str(self.plugins_dir),
                            "success": result
                        }
                    )
            except LifecycleHookError as e:
                self.log(f"Post-uninstall hook failed: {str(e)}", "warning")

        return result

    def update_plugin(
            self,
            package_path: Union[str, Path],
            skip_verification: bool = False,
            resolve_dependencies: bool = True,
            install_dependencies: bool = True
    ) -> InstalledPlugin:
        """
        Update a plugin.

        Args:
            package_path: Path to the plugin package
            skip_verification: Whether to skip signature verification
            resolve_dependencies: Whether to resolve dependencies
            install_dependencies: Whether to install missing dependencies

        Returns:
            The updated plugin

        Raises:
            PluginInstallationError: If there's an error during update
        """
        # Load the package to get the manifest
        package = PluginPackage.load(package_path)
        if not package.manifest:
            raise PluginInstallationError("Package has no manifest")

        manifest = package.manifest
        plugin_name = manifest.name

        # Check if the plugin is installed
        if not self.is_plugin_installed(plugin_name):
            raise PluginInstallationError(f"Plugin {plugin_name} is not installed, cannot update")

        installed_plugin = self.get_installed_plugin(plugin_name)
        if not installed_plugin:
            raise PluginInstallationError(f"Failed to get information about installed plugin {plugin_name}")

        current_version = installed_plugin.manifest.version
        new_version = manifest.version

        # Execute pre-update hook if defined
        try:
            if PluginLifecycleHook.PRE_UPDATE in installed_plugin.manifest.lifecycle_hooks:
                execute_hook(
                    hook=PluginLifecycleHook.PRE_UPDATE,
                    plugin_name=plugin_name,
                    manifest=installed_plugin.manifest,
                    context={
                        "package_path": str(package_path),
                        "skip_verification": skip_verification,
                        "resolve_dependencies": resolve_dependencies,
                        "install_dependencies": install_dependencies,
                        "plugins_dir": str(self.plugins_dir),
                        "install_path": str(installed_plugin.install_path),
                        "current_version": current_version,
                        "new_version": new_version
                    }
                )
        except LifecycleHookError as e:
            raise PluginInstallationError(f"Pre-update hook failed: {str(e)}")

        # Check version
        try:
            import semver
            try:
                current_ver = semver.Version.parse(current_version)
                new_ver = semver.Version.parse(new_version)
                if new_ver <= current_ver:
                    self.log(
                        f"New version ({new_version}) is not newer than current version ({current_version}), "
                        f"updating anyway",
                        "warning"
                    )
            except Exception:
                self.log(
                    f"Failed to compare versions {current_version} and {new_version}, "
                    f"continuing with update",
                    "warning"
                )
        except ImportError:
            self.log("semver package not available, skipping version check", "warning")

        # Install the plugin with force=True to overwrite the existing one
        updated_plugin = self.install_plugin(
            package_path=package_path,
            force=True,
            skip_verification=skip_verification,
            enable=installed_plugin.enabled,
            resolve_dependencies=resolve_dependencies,
            install_dependencies=install_dependencies
        )

        # Execute post-update hook if defined
        try:
            if PluginLifecycleHook.POST_UPDATE in manifest.lifecycle_hooks:
                execute_hook(
                    hook=PluginLifecycleHook.POST_UPDATE,
                    plugin_name=plugin_name,
                    manifest=manifest,
                    context={
                        "package_path": str(package_path),
                        "skip_verification": skip_verification,
                        "resolve_dependencies": resolve_dependencies,
                        "install_dependencies": install_dependencies,
                        "plugins_dir": str(self.plugins_dir),
                        "install_path": str(updated_plugin.install_path),
                        "current_version": current_version,
                        "new_version": new_version,
                        "success": True
                    }
                )
        except LifecycleHookError as e:
            self.log(f"Post-update hook failed: {str(e)}", "warning")

        return updated_plugin

    def resolve_dependencies(
            self,
            package_path: Union[str, Path],
            repository_url: Optional[str] = None
    ) -> Dict[str, Union[str, bool]]:
        """
        Resolve dependencies for a plugin package.

        Args:
            package_path: Path to the plugin package
            repository_url: Optional repository URL to use for dependency resolution

        Returns:
            A dictionary mapping dependency names to results

        Raises:
            PluginInstallationError: If there's an error resolving dependencies
        """
        try:
            # Load the package to get the manifest
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
                if dep_name == 'core':
                    result[dep_name] = True
                    continue

                if self.is_plugin_installed(dep_name):
                    installed = self.get_installed_plugin(dep_name)
                    if installed and self._is_version_compatible(
                            installed.manifest.version,
                            dependency.version,
                            dependency
                    ):
                        result[dep_name] = True
                    else:
                        result[dep_name] = False
                else:
                    result[dep_name] = False

                    # Check if dependency is available in repositories
                    if repository_url or self.repository_manager:
                        try:
                            if repository_url:
                                # Not implemented, would need to add temporary repository
                                pass
                            elif self.repository_manager:
                                # Search all repositories
                                found = False
                                for repo_name, repo in self.repository_manager.repositories.items():
                                    try:
                                        # Find versions in repository
                                        versions = repo.get_plugin_versions(dep_name)
                                        if versions:
                                            # Check for compatible version
                                            for version_info in versions:
                                                if self._is_version_compatible(
                                                        version_info.version,
                                                        dependency.version,
                                                        dependency
                                                ):
                                                    result[dep_name] = repo_name
                                                    found = True
                                                    break

                                        if found:
                                            break
                                    except Exception as e:
                                        self.log(f"Error searching repository {repo_name}: {str(e)}", "warning")
                        except Exception as e:
                            self.log(f"Error checking repositories for dependency {dep_name}: {str(e)}", "warning")

            return result
        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f"Failed to resolve dependencies: {str(e)}")
            self.log(str(e), "error")
            raise

    def get_loading_order(self) -> List[str]:
        """
        Get the order in which plugins should be loaded.

        Returns:
            A list of plugin names in the order they should be loaded
        """
        # Get all installed plugins
        installed_plugins = self.get_installed_plugins()

        # Create a dictionary of plugin manifests
        plugin_manifests = {}
        for name, plugin in installed_plugins.items():
            if plugin.enabled:
                plugin_manifests[name] = plugin.manifest

        # Resolve the loading order
        try:
            order = self.dependency_resolver.resolve_plugin_order(plugin_manifests)
            return order
        except Exception as e:
            self.log(f"Error resolving plugin loading order: {str(e)}", "error")
            # Fall back to alphabetical order
            return sorted(plugin_manifests.keys())

    def _get_dependent_plugins(self, plugin_name: str) -> List[str]:
        """
        Get plugins that depend on a specific plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            A list of plugin names that depend on the specified plugin
        """
        dependent_plugins = []
        for name, plugin in self.get_installed_plugins().items():
            if name == plugin_name:
                continue
            for dependency in plugin.manifest.dependencies:
                if dependency.name == plugin_name:
                    dependent_plugins.append(name)
                    break
        return dependent_plugins

    def _is_version_compatible(
            self,
            available_version: str,
            required_version: str,
            dependency: Optional[PluginDependency] = None
    ) -> bool:
        """Check if the available version is compatible with the required version."""
        try:
            import semver
        except ImportError:
            self.log(
                "The 'semver' package is required for version comparison. "
                "Assuming versions are compatible.",
                "warning"
            )
            return True

        try:
            import re
            version_req = required_version
            match = re.match(r'^(=|>=|<=|>|<|~=|!=|\^)?(.+)$', version_req)
            if not match:
                return False

            operator, version = match.groups()
            operator = operator or '='

            available_ver = semver.Version.parse(available_version)
            required_ver = semver.Version.parse(version)

            if operator == '=':
                return available_ver == required_ver
            elif operator == '>':
                return available_ver > required_ver
            elif operator == '>=':
                return available_ver >= required_ver
            elif operator == '<':
                return available_ver < required_ver
            elif operator == '<=':
                return available_ver <= required_ver
            elif operator == '!=':
                return available_ver != required_ver
            elif operator == '~=':
                return (available_ver >= required_ver and
                        available_ver.major == required_ver.major and
                        available_ver.minor == required_ver.minor)
            elif operator == '^':
                return (available_ver >= required_ver and
                        available_ver.major == required_ver.major)
            else:
                return False
        except Exception as e:
            self.log(f"Error comparing versions: {str(e)}", "warning")
            return False