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
    manifest: PluginManifest
    install_path: Path
    installed_at: datetime.datetime
    enabled: bool = True
    plugin_data: Dict[str, Any] = None
    def __post_init__(self) -> None:
        if self.plugin_data is None:
            self.plugin_data = {}
    def to_dict(self) -> Dict[str, Any]:
        return {'manifest': self.manifest.to_dict(), 'install_path': str(self.install_path), 'installed_at': self.installed_at.isoformat(), 'enabled': self.enabled, 'plugin_data': self.plugin_data}
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InstalledPlugin:
        manifest = PluginManifest(**data['manifest'])
        install_path = Path(data['install_path'])
        installed_at = datetime.datetime.fromisoformat(data['installed_at'])
        enabled = data.get('enabled', True)
        plugin_data = data.get('plugin_data', {})
        return cls(manifest=manifest, install_path=install_path, installed_at=installed_at, enabled=enabled, plugin_data=plugin_data)
class PluginInstallationError(Exception):
    pass
class PluginInstaller:
    def __init__(self, plugins_dir: Union[str, Path], verifier: Optional[PluginVerifier]=None, logger: Optional[Callable[[str, str], None]]=None) -> None:
        self.plugins_dir = Path(plugins_dir)
        self.verifier = verifier or PluginVerifier()
        self.logger = logger or (lambda msg, level: print(f'[{level.upper()}] {msg}'))
        self.installed_plugins: Dict[str, InstalledPlugin] = {}
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.plugins_dir / 'installed_plugins.json'
        self.load_installed_plugins()
    def log(self, message: str, level: str='info') -> None:
        self.logger(message, level)
    def load_installed_plugins(self) -> None:
        if not self.metadata_file.exists():
            return
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
            for plugin_name, plugin_data in data.items():
                try:
                    installed_plugin = InstalledPlugin.from_dict(plugin_data)
                    self.installed_plugins[plugin_name] = installed_plugin
                except Exception as e:
                    self.log(f'Failed to load plugin metadata for {plugin_name}: {e}', 'warning')
            self.log(f'Loaded {len(self.installed_plugins)} installed plugins')
        except Exception as e:
            self.log(f'Failed to load installed plugins metadata: {e}', 'error')
    def save_installed_plugins(self) -> None:
        try:
            data = {}
            for plugin_name, plugin in self.installed_plugins.items():
                data[plugin_name] = plugin.to_dict()
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', dir=self.plugins_dir, delete=False) as tmp:
                json.dump(data, tmp, indent=2)
                tmp_path = Path(tmp.name)
            shutil.move(tmp_path, self.metadata_file)
        except Exception as e:
            self.log(f'Failed to save installed plugins metadata: {e}', 'error')
    def get_plugin_dir(self, plugin_name: str) -> Path:
        return self.plugins_dir / plugin_name
    def is_plugin_installed(self, plugin_name: str) -> bool:
        return plugin_name in self.installed_plugins
    def get_installed_plugin(self, plugin_name: str) -> Optional[InstalledPlugin]:
        return self.installed_plugins.get(plugin_name)
    def install_plugin(self, package_path: Union[str, Path], force: bool=False, skip_verification: bool=False, enable: bool=True) -> InstalledPlugin:
        try:
            package = PluginPackage.load(package_path)
            if not package.manifest:
                raise PluginInstallationError('Package has no manifest')
            plugin_name = package.manifest.name
            plugin_version = package.manifest.version
            if self.is_plugin_installed(plugin_name) and (not force):
                installed = self.get_installed_plugin(plugin_name)
                if installed and installed.manifest.version == plugin_version:
                    self.log(f'Plugin {plugin_name} v{plugin_version} is already installed', 'info')
                    return installed
                elif installed:
                    raise PluginInstallationError(f'Plugin {plugin_name} is already installed with version {installed.manifest.version}. Use force=True to overwrite.')
            if not skip_verification and self.verifier:
                self.log(f'Verifying signature for plugin {plugin_name}', 'debug')
                if not self.verifier.verify_package(package):
                    raise PluginInstallationError(f'Plugin package signature verification failed for {plugin_name}')
            plugin_dir = self.get_plugin_dir(plugin_name)
            if plugin_dir.exists():
                if force:
                    self._backup_plugin(plugin_name)
                    shutil.rmtree(plugin_dir)
                else:
                    raise PluginInstallationError(f'Plugin directory already exists: {plugin_dir}')
            plugin_dir.mkdir(parents=True, exist_ok=True)
            self.log(f'Extracting plugin {plugin_name} to {plugin_dir}', 'debug')
            package.extract(plugin_dir)
            installed_plugin = InstalledPlugin(manifest=package.manifest, install_path=plugin_dir, installed_at=datetime.datetime.now(), enabled=enable)
            self.installed_plugins[plugin_name] = installed_plugin
            self.save_installed_plugins()
            self.log(f'Successfully installed plugin {plugin_name} v{plugin_version}', 'info')
            return installed_plugin
        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f'Failed to install plugin: {e}')
            self.log(str(e), 'error')
            raise
    def update_plugin(self, package_path: Union[str, Path], skip_verification: bool=False) -> InstalledPlugin:
        try:
            package = PluginPackage.load(package_path)
            if not package.manifest:
                raise PluginInstallationError('Package has no manifest')
            plugin_name = package.manifest.name
            plugin_version = package.manifest.version
            if not self.is_plugin_installed(plugin_name):
                raise PluginInstallationError(f'Plugin {plugin_name} is not installed, cannot update')
            current_plugin = self.get_installed_plugin(plugin_name)
            if not current_plugin:
                raise PluginInstallationError(f'Failed to get information about installed plugin {plugin_name}')
            current_version = current_plugin.manifest.version
            import semver
            try:
                current_ver = semver.Version.parse(current_version)
                new_ver = semver.Version.parse(plugin_version)
                if new_ver <= current_ver:
                    self.log(f'New version ({plugin_version}) is not newer than current version ({current_version}), updating anyway', 'warning')
            except Exception:
                self.log(f'Failed to compare versions {current_version} and {plugin_version}, continuing with update', 'warning')
            return self.install_plugin(package_path=package_path, force=True, skip_verification=skip_verification, enable=current_plugin.enabled)
        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f'Failed to update plugin: {e}')
            self.log(str(e), 'error')
            raise
    def uninstall_plugin(self, plugin_name: str, keep_data: bool=False) -> bool:
        try:
            if not self.is_plugin_installed(plugin_name):
                self.log(f'Plugin {plugin_name} is not installed', 'warning')
                return False
            plugin = self.get_installed_plugin(plugin_name)
            if not plugin:
                raise PluginInstallationError(f'Failed to get information about installed plugin {plugin_name}')
            dependencies = self._get_dependent_plugins(plugin_name)
            if dependencies:
                dep_names = ', '.join(dependencies)
                raise PluginInstallationError(f'Cannot uninstall plugin {plugin_name} because other plugins depend on it: {dep_names}')
            self._backup_plugin(plugin_name)
            plugin_dir = self.get_plugin_dir(plugin_name)
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
            del self.installed_plugins[plugin_name]
            self.save_installed_plugins()
            self.log(f'Successfully uninstalled plugin {plugin_name}', 'info')
            return True
        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f'Failed to uninstall plugin: {e}')
            self.log(str(e), 'error')
            raise
    def enable_plugin(self, plugin_name: str) -> bool:
        if not self.is_plugin_installed(plugin_name):
            self.log(f'Plugin {plugin_name} is not installed', 'warning')
            return False
        plugin = self.get_installed_plugin(plugin_name)
        if not plugin:
            self.log(f'Failed to get information about installed plugin {plugin_name}', 'error')
            return False
        if plugin.enabled:
            self.log(f'Plugin {plugin_name} is already enabled', 'info')
            return True
        plugin.enabled = True
        self.save_installed_plugins()
        self.log(f'Successfully enabled plugin {plugin_name}', 'info')
        return True
    def disable_plugin(self, plugin_name: str) -> bool:
        if not self.is_plugin_installed(plugin_name):
            self.log(f'Plugin {plugin_name} is not installed', 'warning')
            return False
        plugin = self.get_installed_plugin(plugin_name)
        if not plugin:
            self.log(f'Failed to get information about installed plugin {plugin_name}', 'error')
            return False
        if not plugin.enabled:
            self.log(f'Plugin {plugin_name} is already disabled', 'info')
            return True
        dependencies = self._get_dependent_plugins(plugin_name)
        if dependencies:
            dep_names = ', '.join(dependencies)
            self.log(f'Warning: Disabling plugin {plugin_name} may affect these dependent plugins: {dep_names}', 'warning')
        plugin.enabled = False
        self.save_installed_plugins()
        self.log(f'Successfully disabled plugin {plugin_name}', 'info')
        return True
    def get_installed_plugins(self) -> Dict[str, InstalledPlugin]:
        return self.installed_plugins.copy()
    def get_enabled_plugins(self) -> Dict[str, InstalledPlugin]:
        return {name: plugin for name, plugin in self.installed_plugins.items() if plugin.enabled}
    def _backup_plugin(self, plugin_name: str) -> Optional[Path]:
        try:
            plugin = self.get_installed_plugin(plugin_name)
            if not plugin:
                return None
            plugin_dir = self.get_plugin_dir(plugin_name)
            if not plugin_dir.exists():
                return None
            backups_dir = self.plugins_dir / 'backups'
            backups_dir.mkdir(exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'{plugin_name}_v{plugin.manifest.version}_{timestamp}.zip'
            backup_path = backups_dir / backup_filename
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    package = PluginPackage.create(source_dir=plugin_dir, output_path=backup_path, manifest=plugin.manifest)
                    return backup_path
                except Exception as e:
                    self.log(f'Failed to create backup package: {e}', 'warning')
                    backup_path = backups_dir / f'{plugin_name}_{timestamp}'
                    shutil.copytree(plugin_dir, backup_path)
                    return backup_path
        except Exception as e:
            self.log(f'Failed to backup plugin {plugin_name}: {e}', 'warning')
            return None
    def _get_dependent_plugins(self, plugin_name: str) -> List[str]:
        dependent_plugins = []
        for name, plugin in self.installed_plugins.items():
            if name == plugin_name:
                continue
            for dependency in plugin.manifest.dependencies:
                if dependency.name == plugin_name:
                    dependent_plugins.append(name)
                    break
        return dependent_plugins
    def resolve_dependencies(self, package_path: Union[str, Path], repository_url: Optional[str]=None) -> Dict[str, Union[str, bool]]:
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
                    if installed and installed.manifest.satisfies_dependency(dependency):
                        result[dep_name] = True
                    else:
                        result[dep_name] = False
                else:
                    result[dep_name] = False
                    if repository_url and dependency.url:
                        pass
            return result
        except Exception as e:
            if not isinstance(e, PluginInstallationError):
                e = PluginInstallationError(f'Failed to resolve dependencies: {e}')
            self.log(str(e), 'error')
            raise