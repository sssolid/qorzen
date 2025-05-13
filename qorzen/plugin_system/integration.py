from __future__ import annotations

import asyncio
import os
import tempfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, cast

import re
import semver

from qorzen.plugin_system.dependency import DependencyResolver, DependencyError
from qorzen.plugin_system.installer import PluginInstaller, PluginInstallationError, InstalledPlugin
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook, PluginDependency
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.repository import PluginRepositoryManager, PluginRepositoryError
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.lifecycle import execute_hook, LifecycleHookError, PluginLifecycleState, \
    set_plugin_state


class PluginIntegrationError(Exception):
    """
    Exception raised for errors in the plugin integration process.

    Attributes:
        message: The error message
        plugin_name: Optional name of the affected plugin
        cause: Optional original exception that caused this error
    """

    def __init__(self, message: str, plugin_name: Optional[str] = None, cause: Optional[Exception] = None):
        self.message = message
        self.plugin_name = plugin_name
        self.cause = cause
        error_message = message
        if plugin_name:
            error_message = f'{message} (Plugin: {plugin_name})'
        super().__init__(error_message)


class IntegratedPluginInstaller:
    """
    Handles plugin installation, updates, and dependency management asynchronously.
    Integrates with the plugin lifecycle system.
    """

    def __init__(self, plugins_dir: Union[str, Path],
                 repository_manager: Optional[PluginRepositoryManager] = None,
                 verifier: Optional[PluginVerifier] = None,
                 logger: Optional[Callable[[str, str], None]] = None,
                 core_version: str = '0.1.0'):
        """
        Initialize the async integrated plugin installer.

        Args:
            plugins_dir: Directory where plugins are installed
            repository_manager: Optional repository manager for downloading plugins
            verifier: Optional verifier for plugin package verification
            logger: Optional logger function
            core_version: The core application version
        """
        self.plugins_dir = Path(plugins_dir)
        self.repository_manager = repository_manager
        self.logger = logger or (lambda msg, level: print(f'[{level.upper()}] {msg}'))
        self.core_version = core_version
        self.installer = PluginInstaller(plugins_dir=plugins_dir, verifier=verifier, logger=logger)
        self.dependency_resolver = DependencyResolver(repository_manager=repository_manager, logger=logger)
        self.dependency_resolver.set_plugins_dir(plugins_dir)
        self.dependency_resolver.set_core_version(core_version)
        self._lock = asyncio.Lock()
        self._sync_installed_plugins()

    def _sync_installed_plugins(self) -> None:
        """Synchronize installed plugins with the dependency resolver."""
        installed_plugins = {}
        for name, plugin in self.installer.get_installed_plugins().items():
            installed_plugins[name] = plugin.manifest
        self.dependency_resolver.set_installed_plugins(installed_plugins)

    def log(self, message: str, level: str = 'info') -> None:
        """Log a message with the specified level."""
        self.logger(message, level)

    def get_installed_plugins(self) -> Dict[str, InstalledPlugin]:
        """
        Get all installed plugins.

        Returns:
            Dict[str, InstalledPlugin]: Dictionary of installed plugins
        """
        return self.installer.get_installed_plugins()

    def get_enabled_plugins(self) -> Dict[str, InstalledPlugin]:
        """
        Get all enabled plugins.

        Returns:
            Dict[str, InstalledPlugin]: Dictionary of enabled plugins
        """
        return self.installer.get_enabled_plugins()

    def get_installed_plugin(self, plugin_name: str) -> Optional[InstalledPlugin]:
        """
        Get information about an installed plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            Optional[InstalledPlugin]: The installed plugin if found, None otherwise
        """
        return self.installer.get_installed_plugin(plugin_name)

    def is_plugin_installed(self, plugin_name: str) -> bool:
        """
        Check if a plugin is installed.

        Args:
            plugin_name: The name of the plugin

        Returns:
            bool: True if the plugin is installed
        """
        return self.installer.is_plugin_installed(plugin_name)

    async def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            bool: True if the plugin was enabled
        """
        async with self._lock:
            result = self.installer.enable_plugin(plugin_name)
            if result:
                try:
                    await set_plugin_state(plugin_name, PluginLifecycleState.DISCOVERED)
                except Exception:
                    pass
            return result

    async def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            bool: True if the plugin was disabled
        """
        async with self._lock:
            result = self.installer.disable_plugin(plugin_name)
            if result:
                try:
                    await set_plugin_state(plugin_name, PluginLifecycleState.INACTIVE)
                except Exception:
                    pass
            return result

    async def install_plugin(self, package_path: Union[str, Path],
                             force: bool = False,
                             skip_verification: bool = False,
                             enable: bool = True,
                             resolve_dependencies: bool = True,
                             install_dependencies: bool = True) -> InstalledPlugin:
        """
        Install a plugin from a package.

        Args:
            package_path: Path to the plugin package
            force: Force installation even if already installed
            skip_verification: Skip package verification
            enable: Enable the plugin after installation
            resolve_dependencies: Resolve plugin dependencies
            install_dependencies: Install missing dependencies

        Returns:
            InstalledPlugin: Information about the installed plugin

        Raises:
            PluginInstallationError: If installation fails
        """
        async with self._lock:
            package = PluginPackage.load(package_path)
            if not package.manifest:
                raise PluginInstallationError('Package has no manifest')

            manifest = package.manifest
            plugin_name = manifest.name

            try:
                if PluginLifecycleHook.PRE_INSTALL in manifest.lifecycle_hooks:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        package.extract(temp_path)
                        import sys
                        original_path = sys.path.copy()
                        sys.path.insert(0, str(temp_path))
                        try:
                            await execute_hook(
                                hook=PluginLifecycleHook.PRE_INSTALL,
                                plugin_name=plugin_name,
                                manifest=manifest,
                                context={
                                    'package_path': str(package_path),
                                    'force': force,
                                    'skip_verification': skip_verification,
                                    'enable': enable,
                                    'resolve_dependencies': resolve_dependencies,
                                    'install_dependencies': install_dependencies,
                                    'plugins_dir': str(self.plugins_dir)
                                }
                            )
                        finally:
                            sys.path = original_path
            except LifecycleHookError as e:
                raise PluginInstallationError(f'Pre-install hook failed: {str(e)}')

            if resolve_dependencies:
                try:
                    dependencies = self.dependency_resolver.resolve_dependencies(
                        plugin_manifest=manifest,
                        resolve_transitives=True,
                        fetch_missing=False
                    )

                    missing_deps = [(name, version) for name, version, is_local in dependencies
                                    if not is_local and name != 'core']

                    if missing_deps and not install_dependencies:
                        missing_list = ', '.join([f'{name} ({version})' for name, version in missing_deps])
                        raise PluginInstallationError(
                            f'Plugin {plugin_name} has missing dependencies: {missing_list}. '
                            f'Use install_dependencies=True to install them automatically.'
                        )

                    if missing_deps and install_dependencies:
                        if not self.repository_manager:
                            raise PluginInstallationError(
                                f'Plugin {plugin_name} has missing dependencies, but no repository manager '
                                f'is available to install them.'
                            )

                        self.log(f'Installing {len(missing_deps)} dependencies for plugin {plugin_name}', 'info')

                        for dep_name, dep_version in missing_deps:
                            try:
                                self.log(f'Searching for dependency {dep_name} ({dep_version})', 'debug')
                                compatible_version = None
                                compatible_repo = None

                                for repo_name, repo in self.repository_manager.repositories.items():
                                    try:
                                        versions = repo.get_plugin_versions(dep_name)
                                        for version_info in versions:
                                            if version_info.version == dep_version:
                                                compatible_version = version_info
                                                compatible_repo = repo_name
                                                break
                                        if compatible_version:
                                            break
                                    except Exception as e:
                                        self.log(f'Error searching repository {repo_name}: {str(e)}', 'warning')

                                if not compatible_version:
                                    raise PluginInstallationError(
                                        f'Could not find compatible version of dependency {dep_name} ({dep_version})'
                                    )

                                self.log(
                                    f'Downloading dependency {dep_name} ({dep_version}) from {compatible_repo}',
                                    'info'
                                )
                                download_path = self.repository_manager.get_repository(compatible_repo).download_plugin(
                                    plugin_name=dep_name,
                                    version=dep_version
                                )

                                self.log(f'Installing dependency {dep_name} ({dep_version})', 'info')
                                self.installer.install_plugin(
                                    package_path=download_path,
                                    force=force,
                                    skip_verification=skip_verification,
                                    enable=enable
                                )
                            except Exception as e:
                                raise PluginInstallationError(
                                    f'Failed to install dependency {dep_name} ({dep_version}): {str(e)}'
                                ) from e
                except DependencyError as e:
                    raise PluginInstallationError(f'Dependency error: {str(e)}') from e

            installed_plugin = self.installer.install_plugin(
                package_path=package_path,
                force=force,
                skip_verification=skip_verification,
                enable=enable
            )

            self._sync_installed_plugins()

            try:
                await set_plugin_state(plugin_name, PluginLifecycleState.DISCOVERED)
            except Exception:
                pass

            try:
                if PluginLifecycleHook.POST_INSTALL in manifest.lifecycle_hooks:
                    await execute_hook(
                        hook=PluginLifecycleHook.POST_INSTALL,
                        plugin_name=plugin_name,
                        manifest=manifest,
                        context={
                            'package_path': str(package_path),
                            'force': force,
                            'skip_verification': skip_verification,
                            'enable': enable,
                            'resolve_dependencies': resolve_dependencies,
                            'install_dependencies': install_dependencies,
                            'plugins_dir': str(self.plugins_dir),
                            'install_path': str(installed_plugin.install_path)
                        }
                    )
            except LifecycleHookError as e:
                self.log(f'Post-install hook failed: {str(e)}', 'warning')

            return installed_plugin

    async def uninstall_plugin(self, plugin_name: str,
                               keep_data: bool = False,
                               check_dependents: bool = True) -> bool:
        """
        Uninstall a plugin.

        Args:
            plugin_name: The name of the plugin
            keep_data: Keep plugin data after uninstallation
            check_dependents: Check for and prevent uninstallation if other plugins depend on this one

        Returns:
            bool: True if the plugin was uninstalled

        Raises:
            PluginInstallationError: If uninstallation fails
        """
        async with self._lock:
            if not self.is_plugin_installed(plugin_name):
                return False

            installed_plugin = self.get_installed_plugin(plugin_name)
            if not installed_plugin:
                return False

            manifest = installed_plugin.manifest

            if check_dependents:
                dependents = self._get_dependent_plugins(plugin_name)
                if dependents:
                    dep_names = ', '.join(dependents)
                    raise PluginInstallationError(
                        f'Cannot uninstall plugin {plugin_name} because other plugins depend on it: {dep_names}'
                    )

            try:
                if PluginLifecycleHook.PRE_UNINSTALL in manifest.lifecycle_hooks:
                    await execute_hook(
                        hook=PluginLifecycleHook.PRE_UNINSTALL,
                        plugin_name=plugin_name,
                        manifest=manifest,
                        context={
                            'keep_data': keep_data,
                            'check_dependents': check_dependents,
                            'plugins_dir': str(self.plugins_dir),
                            'install_path': str(installed_plugin.install_path)
                        }
                    )
            except LifecycleHookError as e:
                raise PluginInstallationError(f'Pre-uninstall hook failed: {str(e)}')

            result = self.installer.uninstall_plugin(plugin_name=plugin_name, keep_data=keep_data)

            if result:
                self._sync_installed_plugins()

                try:
                    await set_plugin_state(plugin_name, PluginLifecycleState.INACTIVE)
                except Exception:
                    pass

                try:
                    if PluginLifecycleHook.POST_UNINSTALL in manifest.lifecycle_hooks:
                        await execute_hook(
                            hook=PluginLifecycleHook.POST_UNINSTALL,
                            plugin_name=plugin_name,
                            manifest=manifest,
                            context={
                                'keep_data': keep_data,
                                'check_dependents': check_dependents,
                                'plugins_dir': str(self.plugins_dir),
                                'success': result
                            }
                        )
                except LifecycleHookError as e:
                    self.log(f'Post-uninstall hook failed: {str(e)}', 'warning')

            return result

    async def update_plugin(self, package_path: Union[str, Path],
                            skip_verification: bool = False,
                            resolve_dependencies: bool = True,
                            install_dependencies: bool = True) -> InstalledPlugin:
        """
        Update a plugin from a package.

        Args:
            package_path: Path to the plugin package
            skip_verification: Skip package verification
            resolve_dependencies: Resolve plugin dependencies
            install_dependencies: Install missing dependencies

        Returns:
            InstalledPlugin: Information about the updated plugin

        Raises:
            PluginInstallationError: If update fails
        """
        async with self._lock:
            package = PluginPackage.load(package_path)
            if not package.manifest:
                raise PluginInstallationError('Package has no manifest')

            manifest = package.manifest
            plugin_name = manifest.name

            if not self.is_plugin_installed(plugin_name):
                raise PluginInstallationError(f'Plugin {plugin_name} is not installed, cannot update')

            installed_plugin = self.get_installed_plugin(plugin_name)
            if not installed_plugin:
                raise PluginInstallationError(f'Failed to get information about installed plugin {plugin_name}')

            current_version = installed_plugin.manifest.version
            new_version = manifest.version

            try:
                if PluginLifecycleHook.PRE_UPDATE in installed_plugin.manifest.lifecycle_hooks:
                    await execute_hook(
                        hook=PluginLifecycleHook.PRE_UPDATE,
                        plugin_name=plugin_name,
                        manifest=installed_plugin.manifest,
                        context={
                            'package_path': str(package_path),
                            'skip_verification': skip_verification,
                            'resolve_dependencies': resolve_dependencies,
                            'install_dependencies': install_dependencies,
                            'plugins_dir': str(self.plugins_dir),
                            'install_path': str(installed_plugin.install_path),
                            'current_version': current_version,
                            'new_version': new_version
                        }
                    )
            except LifecycleHookError as e:
                raise PluginInstallationError(f'Pre-update hook failed: {str(e)}')

            try:
                import semver
                try:
                    current_ver = semver.Version.parse(current_version)
                    new_ver = semver.Version.parse(new_version)
                    if new_ver <= current_ver:
                        self.log(
                            f'New version ({new_version}) is not newer than current version '
                            f'({current_version}), updating anyway',
                            'warning'
                        )
                except Exception:
                    self.log(
                        f'Failed to compare versions {current_version} and {new_version}, '
                        f'continuing with update',
                        'warning'
                    )
            except ImportError:
                self.log('semver package not available, skipping version check', 'warning')

            updated_plugin = await self.install_plugin(
                package_path=package_path,
                force=True,
                skip_verification=skip_verification,
                enable=installed_plugin.enabled,
                resolve_dependencies=resolve_dependencies,
                install_dependencies=install_dependencies
            )

            try:
                if PluginLifecycleHook.POST_UPDATE in manifest.lifecycle_hooks:
                    await execute_hook(
                        hook=PluginLifecycleHook.POST_UPDATE,
                        plugin_name=plugin_name,
                        manifest=manifest,
                        context={
                            'package_path': str(package_path),
                            'skip_verification': skip_verification,
                            'resolve_dependencies': resolve_dependencies,
                            'install_dependencies': install_dependencies,
                            'plugins_dir': str(self.plugins_dir),
                            'install_path': str(updated_plugin.install_path),
                            'current_version': current_version,
                            'new_version': new_version,
                            'success': True
                        }
                    )
            except LifecycleHookError as e:
                self.log(f'Post-update hook failed: {str(e)}', 'warning')

            return updated_plugin

    async def resolve_dependencies(self, package_path: Union[str, Path],
                                   repository_url: Optional[str] = None) -> Dict[str, Union[str, bool]]:
        """
        Resolve dependencies for a plugin package.

        Args:
            package_path: Path to the plugin package
            repository_url: Optional specific repository URL

        Returns:
            Dict[str, Union[str, bool]]: Dictionary of dependencies and their status

        Raises:
            PluginInstallationError: If dependency resolution fails
        """
        try:
            package = PluginPackage.load(package_path)
            if not package.manifest:
                raise PluginInstallationError('Package has no manifest')

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
                            installed.manifest.version, dependency.version, dependency
                    ):
                        result[dep_name] = True
                    else:
                        result[dep_name] = False
                else:
                    result[dep_name] = False

                    if repository_url or self.repository_manager:
                        try:
                            if repository_url:
                                pass  # Implement specific repository URL handling if needed
                            elif self.repository_manager:
                                found = False
                                for repo_name, repo in self.repository_manager.repositories.items():
                                    try:
                                        versions = repo.get_plugin_versions(dep_name)
                                        if versions:
                                            for version_info in versions:
                                                if self._is_version_compatible(
                                                        version_info.version, dependency.version, dependency
                                                ):
                                                    result[dep_name] = repo_name
                                                    found = True
                                                    break
                                        if found:
                                            break
                                    except Exception as e:
                                        self.log(f'Error searching repository {repo_name}: {str(e)}', 'warning')
                        except Exception as e:
                            self.log(f'Error checking repositories for dependency {dep_name}: {str(e)}', 'warning')

            return result
        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f'Failed to resolve dependencies: {str(e)}')
            self.log(str(e), 'error')
            raise e

    async def get_loading_order(self) -> List[str]:
        """
        Get the order in which plugins should be loaded based on dependencies.

        Returns:
            List[str]: Ordered list of plugin names
        """
        async with self._lock:
            installed_plugins = self.get_installed_plugins()
            plugin_manifests = {}
            for name, plugin in installed_plugins.items():
                if plugin.enabled:
                    plugin_manifests[name] = plugin.manifest

            try:
                order = self.dependency_resolver.resolve_plugin_order(plugin_manifests)
                return order
            except Exception as e:
                self.log(f'Error resolving plugin loading order: {str(e)}', 'error')
                return sorted(plugin_manifests.keys())

    def _get_dependent_plugins(self, plugin_name: str) -> List[str]:
        """
        Get a list of plugins that depend on a specific plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            List[str]: List of dependent plugin names
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

    def _is_version_compatible(self, available_version: str, required_version: str,
                               dependency: Optional[PluginDependency] = None) -> bool:
        """
        Check if an available version is compatible with a required version.

        Args:
            available_version: The available version
            required_version: The required version (may include comparison operators)
            dependency: Optional dependency information

        Returns:
            bool: True if versions are compatible
        """
        try:
            import semver
        except ImportError:
            self.log("The 'semver' package is required for version comparison. "
                     "Assuming versions are compatible.", 'warning')
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
                return available_ver >= required_ver and available_ver.major == required_ver.major
            else:
                return False
        except Exception as e:
            self.log(f'Error comparing versions: {str(e)}', 'warning')
            return False