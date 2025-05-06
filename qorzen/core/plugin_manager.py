from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import inspect
import os
import pathlib
import pkgutil
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, cast

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, PluginError

# Import the enhanced plugin system components
from qorzen.plugin_system.integration import IntegratedPluginInstaller
from qorzen.plugin_system.repository import PluginRepositoryManager
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook
from qorzen.plugin_system.lifecycle import execute_hook, set_logger as set_lifecycle_logger, get_lifecycle_manager
from qorzen.plugin_system.extension import (
    register_plugin_extensions,
    unregister_plugin_extensions,
    extension_registry
)
from qorzen.plugin_system.config_schema import ConfigSchema


class PluginState(Enum):
    DISCOVERED = 'discovered'
    LOADED = 'loaded'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    FAILED = 'failed'
    DISABLED = 'disabled'


@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    author: str
    state: PluginState = PluginState.DISCOVERED
    dependencies: List[str] = None
    path: Optional[str] = None
    instance: Optional[Any] = None
    error: Optional[str] = None
    load_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    manifest: Optional[PluginManifest] = None
    config_schema: Optional[ConfigSchema] = None

    def __post_init__(self) -> None:
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class PluginManager(QorzenManager):
    def __init__(
        self,
        application_core: Any,
        config_manager: Any,
        logger_manager: Any,
        event_bus_manager: Any,
        file_manager: Any,
        thread_manager: Any,
        database_manager: Any,
        remote_service_manager: Any,
        security_manager: Any,
        api_manager: Any,
        cloud_manager: Any
    ) -> None:
        super().__init__(name='PluginManager')
        self._application_core = application_core
        self._config_manager = config_manager
        self._logger_manager = logger_manager
        self._logger = logger_manager.get_logger('plugin_manager')
        self._event_bus = event_bus_manager
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self._database_manager = database_manager
        self._remote_services_manager = remote_service_manager
        self._security_manager = security_manager
        self._api_manager = api_manager
        self._cloud_manager = cloud_manager

        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_dir: Optional[pathlib.Path] = None
        self._entry_point_group = 'qorzen.plugins'
        self._auto_load = True
        self._enabled_plugins: List[str] = []
        self._disabled_plugins: List[str] = []
        self._repository_config_path: Optional[Path] = None

        # Enhanced plugin installer with repository support
        self.plugin_installer: Optional[IntegratedPluginInstaller] = None
        self.plugin_verifier: Optional[PluginVerifier] = None
        self.repository_manager: Optional[PluginRepositoryManager] = None

        # Set up lifecycle logger
        get_lifecycle_manager().set_logger(self._logger)

    def initialize(self) -> None:
        try:
            plugin_config = self._config_manager.get('plugins', {})
            plugin_dir = plugin_config.get('directory', 'plugins')
            self._plugin_dir = pathlib.Path(plugin_dir)
            self._auto_load = plugin_config.get('autoload', True)
            self._enabled_plugins = plugin_config.get('enabled', [])
            self._disabled_plugins = plugin_config.get('disabled', [])
            self._repository_config_path = self._plugin_dir / 'repositories.json'

            os.makedirs(self._plugin_dir, exist_ok=True)
            self._init_packaging_system(plugin_config)

            self._event_bus.subscribe(
                event_type='plugin/install',
                callback=self._on_plugin_install_event,
                subscriber_id='plugin_manager'
            )
            self._event_bus.subscribe(
                event_type='plugin/uninstall',
                callback=self._on_plugin_uninstall_event,
                subscriber_id='plugin_manager'
            )
            self._event_bus.subscribe(
                event_type='plugin/enable',
                callback=self._on_plugin_enable_event,
                subscriber_id='plugin_manager'
            )
            self._event_bus.subscribe(
                event_type='plugin/disable',
                callback=self._on_plugin_disable_event,
                subscriber_id='plugin_manager'
            )
            self._event_bus.subscribe(
                event_type='plugin/update',
                callback=self._on_plugin_update_event,
                subscriber_id='plugin_manager'
            )

            # Discover plugins from various sources
            self._discover_entry_point_plugins()
            self._discover_directory_plugins()
            self._discover_packaged_plugins()

            self._config_manager.register_listener('plugins', self._on_config_changed)

            self._logger.info(f'Plugin Manager initialized with {len(self._plugins)} plugins discovered')
            self._initialized = True
            self._healthy = True

            self._event_bus.publish(
                event_type='plugin_manager/initialized',
                source='plugin_manager',
                payload={'plugin_count': len(self._plugins)}
            )

            if self._auto_load:
                self._load_enabled_plugins()
        except Exception as e:
            self._logger.error(f'Failed to initialize Plugin Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize PluginManager: {str(e)}',
                manager_name=self.name
            ) from e

    def _init_packaging_system(self, plugin_config: Dict[str, Any]) -> None:
        """Initialize the plugin packaging system with repository support."""
        package_config = plugin_config.get('packaging', {})
        trusted_keys_dir = package_config.get('trusted_keys_dir', 'keys')
        self._trusted_keys_dir = self._plugin_dir / trusted_keys_dir
        os.makedirs(self._trusted_keys_dir, exist_ok=True)

        # Initialize plugin verifier
        self.plugin_verifier = PluginVerifier()
        if self._trusted_keys_dir.exists():
            try:
                count = self.plugin_verifier.load_trusted_keys(self._trusted_keys_dir)
                self._logger.info(f'Loaded {count} trusted keys for plugin verification')
            except Exception as e:
                self._logger.warning(f'Failed to load trusted keys: {str(e)}')

        # Initialize repository manager
        try:
            self.repository_manager = PluginRepositoryManager(
                config_file=self._repository_config_path if self._repository_config_path.exists() else None,
                logger=self._package_logger
            )
            repos_count = len(self.repository_manager.repositories)
            self._logger.info(f'Initialized repository manager with {repos_count} repositories')
        except Exception as e:
            self._logger.warning(f'Failed to initialize repository manager: {str(e)}')
            self.repository_manager = None

        # Initialize enhanced plugin installer with repository support
        try:
            self.plugin_installer = IntegratedPluginInstaller(
                plugins_dir=self._plugin_dir,
                repository_manager=self.repository_manager,
                verifier=self.plugin_verifier,
                logger=self._package_logger,
                core_version=self._get_core_version()
            )
            self._logger.info('Initialized enhanced plugin installer')
        except Exception as e:
            self._logger.warning(f'Failed to initialize enhanced plugin installer: {str(e)}')
            # Fall back to basic installer
            from qorzen.plugin_system.installer import PluginInstaller
            self.plugin_installer = PluginInstaller(
                plugins_dir=self._plugin_dir,
                verifier=self.plugin_verifier,
                logger=self._package_logger
            )
            self._logger.info('Initialized basic plugin installer (without repository support)')

    def _get_core_version(self) -> str:
        """Get the core application version."""
        try:
            from qorzen.__version__ import __version__
            return __version__
        except ImportError:
            return "0.1.0"  # Default version if not available

    def _package_logger(self, message: str, level: str='info') -> None:
        """Logger for plugin packaging components."""
        if level.lower() == 'info':
            self._logger.info(message)
        elif level.lower() == 'warning':
            self._logger.warning(message)
        elif level.lower() == 'error':
            self._logger.error(message)
        else:
            self._logger.debug(message)

    def _discover_entry_point_plugins(self) -> None:
        """Discover plugins from entry points."""
        try:
            entry_points = importlib.metadata.entry_points().select(group=self._entry_point_group)
            for entry_point in entry_points:
                try:
                    plugin_class = entry_point.load()
                    plugin_info = self._extract_plugin_metadata(
                        plugin_class,
                        entry_point.name,
                        entry_point_name=entry_point.name
                    )
                    self._plugins[plugin_info.name] = plugin_info
                    self._logger.debug(
                        f"Discovered plugin '{plugin_info.name}' from entry point",
                        extra={'plugin': plugin_info.name, 'version': plugin_info.version}
                    )
                except Exception as e:
                    self._logger.error(
                        f"Failed to discover plugin from entry point '{entry_point.name}': {str(e)}",
                        extra={'entry_point': entry_point.name}
                    )
        except Exception as e:
            self._logger.error(f'Failed to discover entry point plugins: {str(e)}')

    def _discover_directory_plugins(self) -> None:
        """Discover plugins from the plugins directory."""
        if not self._plugin_dir or not self._plugin_dir.exists():
            self._logger.warning(f'Plugin directory does not exist: {self._plugin_dir}')
            return

        plugin_dir_str = str(self._plugin_dir.absolute())
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)

        try:
            for item in self._plugin_dir.iterdir():
                if not item.is_dir():
                    continue

                if item.name.startswith('.') or item.name in ('__pycache__', 'backups'):
                    continue

                init_file = item / '__init__.py'
                plugin_file = item / 'plugin.py'
                manifest_file = item / 'manifest.json'

                # First check for manifest.json
                if manifest_file.exists():
                    try:
                        manifest = PluginManifest.load(manifest_file)

                        # Find plugin class based on manifest
                        plugin_class = None
                        module_name = item.name
                        entry_point = manifest.entry_point

                        if entry_point.endswith('.py'):
                            entry_path = item / 'code' / entry_point
                            if entry_path.exists():
                                try:
                                    spec = importlib.util.spec_from_file_location(
                                        f"{module_name}.code.{entry_point.replace('.py', '')}",
                                        entry_path
                                    )
                                    if spec and spec.loader:
                                        module = importlib.util.module_from_spec(spec)
                                        spec.loader.exec_module(module)
                                        plugin_class = self._find_plugin_class(module)
                                except Exception as e:
                                    self._logger.warning(
                                        f"Failed to load entry point {entry_point} for plugin {manifest.name}: {str(e)}",
                                        extra={'plugin': manifest.name, 'entry_point': entry_point}
                                    )
                        else:
                            # Try to import as module
                            try:
                                module = importlib.import_module(f"{module_name}.{entry_point}")
                                plugin_class = self._find_plugin_class(module)
                            except Exception as e:
                                self._logger.warning(
                                    f"Failed to import module {entry_point} for plugin {manifest.name}: {str(e)}",
                                    extra={'plugin': manifest.name, 'entry_point': entry_point}
                                )

                        if plugin_class:
                            plugin_info = self._extract_plugin_metadata(
                                plugin_class,
                                manifest.name,
                                path=str(item),
                                manifest=manifest
                            )

                            # Parse config schema if available
                            config_schema_path = item / 'config_schema.json'
                            if config_schema_path.exists():
                                try:
                                    import json
                                    with open(config_schema_path, 'r') as f:
                                        schema_data = json.load(f)
                                    from qorzen.plugin_system.config_schema import ConfigSchema
                                    plugin_info.config_schema = ConfigSchema(**schema_data)
                                except Exception as e:
                                    self._logger.warning(
                                        f"Failed to load config schema for plugin {manifest.name}: {str(e)}",
                                        extra={'plugin': manifest.name}
                                    )

                            if plugin_info.name not in self._plugins:
                                self._plugins[plugin_info.name] = plugin_info
                                self._logger.debug(
                                    f"Discovered plugin '{plugin_info.name}' from manifest",
                                    extra={'plugin': plugin_info.name, 'version': plugin_info.version, 'path': str(item)}
                                )
                        else:
                            self._logger.warning(
                                f"No plugin class found for manifest {manifest.name}",
                                extra={'plugin': manifest.name}
                            )
                    except Exception as e:
                        self._logger.error(
                            f"Failed to load manifest for plugin directory '{item.name}': {str(e)}",
                            extra={'directory': str(item)}
                        )
                        continue

                # Try legacy method (no manifest)
                if init_file.exists() or plugin_file.exists():
                    try:
                        module_name = item.name
                        if init_file.exists():
                            module = importlib.import_module(module_name)
                        elif plugin_file.exists():
                            spec = importlib.util.spec_from_file_location(f'{module_name}.plugin', plugin_file)
                            if not spec or not spec.loader:
                                continue
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                        else:
                            continue

                        plugin_class = self._find_plugin_class(module)
                        if not plugin_class:
                            if not manifest_file.exists():  # Only log if no manifest was found
                                self._logger.warning(
                                    f'No plugin class found in {module_name}',
                                    extra={'module': module_name}
                                )
                            continue

                        plugin_info = self._extract_plugin_metadata(
                            plugin_class,
                            module_name,
                            path=str(item)
                        )

                        if plugin_info.name not in self._plugins:
                            self._plugins[plugin_info.name] = plugin_info
                            self._logger.debug(
                                f"Discovered plugin '{plugin_info.name}' from directory",
                                extra={'plugin': plugin_info.name, 'version': plugin_info.version, 'path': str(item)}
                            )
                    except Exception as e:
                        self._logger.error(
                            f"Failed to discover plugin from directory '{item.name}': {str(e)}",
                            extra={'directory': str(item)}
                        )
        except Exception as e:
            self._logger.error(f'Failed to discover directory plugins: {str(e)}')

    def _discover_packaged_plugins(self) -> None:
        """Discover plugins from the plugin installer's database."""
        if not self.plugin_installer:
            return

        try:
            installed_plugins = self.plugin_installer.get_installed_plugins()
            for name, plugin in installed_plugins.items():
                if name in self._plugins:
                    continue

                try:
                    manifest = plugin.manifest
                    plugin_info = PluginInfo(
                        name=manifest.name,
                        version=manifest.version,
                        description=manifest.description,
                        author=manifest.author.name,
                        state=PluginState.DISCOVERED,
                        dependencies=[dep.name for dep in manifest.dependencies],
                        path=str(plugin.install_path),
                        metadata={
                            'manifest': True,
                            'display_name': manifest.display_name,
                            'license': manifest.license,
                            'homepage': manifest.homepage,
                            'capabilities': [cap.value for cap in manifest.capabilities],
                            'entry_point': manifest.entry_point,
                            'min_core_version': manifest.min_core_version,
                            'max_core_version': manifest.max_core_version,
                            'installed_at': plugin.installed_at.isoformat(),
                            'enabled': plugin.enabled
                        },
                        manifest=manifest
                    )

                    # Load config schema if available in metadata
                    if manifest.config_schema:
                        try:
                            from qorzen.plugin_system.config_schema import ConfigSchema
                            plugin_info.config_schema = ConfigSchema(**manifest.config_schema)
                        except Exception as e:
                            self._logger.warning(
                                f"Failed to parse config schema for plugin {name}: {str(e)}",
                                extra={'plugin': name}
                            )

                    self._plugins[name] = plugin_info

                    if plugin.enabled and name not in self._enabled_plugins:
                        self._enabled_plugins.append(name)
                    elif not plugin.enabled and name not in self._disabled_plugins:
                        self._disabled_plugins.append(name)

                    self._logger.debug(
                        f"Discovered installed plugin '{name}' v{manifest.version}",
                        extra={'plugin': name, 'version': manifest.version, 'enabled': plugin.enabled}
                    )
                except Exception as e:
                    self._logger.error(
                        f"Failed to process installed plugin '{name}': {str(e)}",
                        extra={'plugin': name, 'error': str(e)}
                    )
        except Exception as e:
            self._logger.error(f'Failed to discover installed plugins: {str(e)}')

    def _find_plugin_class(self, module: Any) -> Optional[Type]:
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'name') and hasattr(obj, 'version') and hasattr(obj, 'description'):
                return obj
        return None

    def _extract_plugin_metadata(
        self,
        plugin_class: Type,
        default_name: str,
        path: Optional[str] = None,
        entry_point_name: Optional[str] = None,
        manifest: Optional[PluginManifest] = None
    ) -> PluginInfo:
        """Extract metadata from a plugin class."""
        name = getattr(plugin_class, 'name', default_name)
        version = getattr(plugin_class, 'version', '0.1.0')
        description = getattr(plugin_class, 'description', 'No description')
        author = getattr(plugin_class, 'author', 'Unknown')
        dependencies = getattr(plugin_class, 'dependencies', [])

        metadata = {
            'class': plugin_class.__name__,
            'module': plugin_class.__module__,
            'entry_point': entry_point_name
        }

        plugin_info = PluginInfo(
            name=name,
            version=version,
            description=description,
            author=author,
            state=PluginState.DISCOVERED,
            dependencies=dependencies,
            path=path,
            metadata=metadata,
            manifest=manifest
        )

        return plugin_info

    def _load_enabled_plugins(self) -> None:
        """Load all enabled plugins in dependency order."""
        if not self.plugin_installer:
            # Legacy method - load plugins without dependency resolution
            for plugin_name, plugin_info in self._plugins.items():
                if not plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                    self.load_plugin(plugin_name)

            for plugin_name, plugin_info in self._plugins.items():
                if plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                    self.load_plugin(plugin_name)
        else:
            # Enhanced method - use dependency resolver
            try:
                # Get all manifests of enabled plugins
                plugin_manifests = {}
                for plugin_name, plugin_info in self._plugins.items():
                    if self._is_plugin_enabled(plugin_name) and plugin_info.manifest:
                        plugin_manifests[plugin_name] = plugin_info.manifest

                # Get the loading order
                loading_order = self.plugin_installer.get_loading_order()

                # Load plugins in the correct order
                for plugin_name in loading_order:
                    if plugin_name in self._plugins and self._is_plugin_enabled(plugin_name):
                        self.load_plugin(plugin_name)
            except Exception as e:
                self._logger.error(f"Failed to load plugins in dependency order: {str(e)}")

                # Fall back to legacy method
                self._logger.warning("Falling back to legacy plugin loading method")
                for plugin_name, plugin_info in self._plugins.items():
                    if not plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                        self.load_plugin(plugin_name)

                for plugin_name, plugin_info in self._plugins.items():
                    if plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                        self.load_plugin(plugin_name)

    def _is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled."""
        if plugin_name in self._disabled_plugins:
            return False

        if plugin_name in self._enabled_plugins:
            return True

        if self.plugin_installer:
            plugin = self.plugin_installer.get_installed_plugin(plugin_name)
            if plugin:
                return plugin.enabled

        return self._auto_load

    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin.

        Args:
            plugin_name: The name of the plugin to load

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error loading the plugin
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        plugin_info = self._plugins[plugin_name]

        if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
            self._logger.debug(
                f"Plugin '{plugin_name}' is already loaded",
                extra={'plugin': plugin_name}
            )
            return True

        if plugin_name in self._disabled_plugins:
            self._logger.warning(
                f"Plugin '{plugin_name}' is disabled and cannot be loaded",
                extra={'plugin': plugin_name}
            )
            return False

        # Check dependencies
        for dependency in plugin_info.dependencies:
            if dependency == 'core':
                continue

            if dependency not in self._plugins:
                plugin_info.state = PluginState.FAILED
                plugin_info.error = f"Dependency '{dependency}' not found"
                self._logger.error(
                    f"Failed to load plugin '{plugin_name}': Dependency '{dependency}' not found",
                    extra={'plugin': plugin_name, 'dependency': dependency}
                )
                return False

            dependency_info = self._plugins[dependency]
            if dependency_info.state not in (PluginState.LOADED, PluginState.ACTIVE):
                if not self.load_plugin(dependency):
                    plugin_info.state = PluginState.FAILED
                    plugin_info.error = f"Failed to load dependency '{dependency}'"
                    self._logger.error(
                        f"Failed to load plugin '{plugin_name}': "
                        f"Dependency '{dependency}' could not be loaded",
                        extra={'plugin': plugin_name, 'dependency': dependency}
                    )
                    return False

        try:
            # Execute pre-enable lifecycle hook if available
            if plugin_info.manifest and PluginLifecycleHook.PRE_ENABLE in plugin_info.manifest.lifecycle_hooks:
                try:
                    execute_hook(
                        hook=PluginLifecycleHook.PRE_ENABLE,
                        plugin_name=plugin_name,
                        manifest=plugin_info.manifest,
                        context={
                            'plugin_manager': self,
                            'config_manager': self._config_manager,
                            'logger_manager': self._logger_manager,
                            'event_bus': self._event_bus,
                            'file_manager': self._file_manager,
                            'thread_manager': self._thread_manager,
                            'database_manager': self._database_manager,
                            'remote_services_manager': self._remote_services_manager,
                            'security_manager': self._security_manager,
                            'api_manager': self._api_manager,
                            'cloud_manager': self._cloud_manager
                        }
                    )
                except Exception as e:
                    self._logger.warning(
                        f"Pre-enable hook failed for plugin '{plugin_name}': {str(e)}",
                        extra={'plugin': plugin_name, 'error': str(e)}
                    )

            # Get the plugin class and instantiate it
            if plugin_info.manifest:
                plugin_class = self._load_packaged_plugin(plugin_info)
            else:
                plugin_class = self._get_plugin_class(plugin_info)

            plugin_info.instance = plugin_class()

            # Initialize the plugin
            if hasattr(plugin_info.instance, 'initialize'):
                plugin_info.instance.initialize(
                    event_bus=self._event_bus,
                    logger_provider=self._logger_manager,
                    config_provider=self._config_manager,
                    file_manager=self._file_manager,
                    thread_manager=self._thread_manager,
                    database_manager=self._database_manager,
                    remote_services_manager=self._remote_services_manager,
                    security_manager=self._security_manager,
                    api_manager=self._api_manager,
                    cloud_manager=self._cloud_manager
                )

            # Register extension points and uses
            if plugin_info.manifest:
                register_plugin_extensions(
                    plugin_name=plugin_name,
                    plugin_instance=plugin_info.instance,
                    manifest=plugin_info.manifest
                )

            # Update state
            plugin_info.state = PluginState.ACTIVE
            plugin_info.load_time = time.time()

            self._logger.info(
                f"Loaded plugin '{plugin_name}' v{plugin_info.version}",
                extra={'plugin': plugin_name, 'version': plugin_info.version}
            )

            # Execute post-enable lifecycle hook if available
            if plugin_info.manifest and PluginLifecycleHook.POST_ENABLE in plugin_info.manifest.lifecycle_hooks:
                try:
                    execute_hook(
                        hook=PluginLifecycleHook.POST_ENABLE,
                        plugin_name=plugin_name,
                        manifest=plugin_info.manifest,
                        plugin_instance=plugin_info.instance,
                        context={
                            'app_core': self._application_core,
                            'plugin_manager': self,
                            'config_manager': self._config_manager,
                            'logger_manager': self._logger_manager,
                            'event_bus': self._event_bus,
                            'file_manager': self._file_manager,
                            'thread_manager': self._thread_manager,
                            'database_manager': self._database_manager,
                            'remote_services_manager': self._remote_services_manager,
                            'security_manager': self._security_manager,
                            'api_manager': self._api_manager,
                            'cloud_manager': self._cloud_manager
                        }
                    )
                except Exception as e:
                    self._logger.warning(
                        f"Post-enable hook failed for plugin '{plugin_name}': {str(e)}",
                        extra={'plugin': plugin_name, 'error': str(e)}
                    )

            # Publish event
            self._event_bus.publish(
                event_type='plugin/loaded',
                source='plugin_manager',
                payload={
                    'plugin_name': plugin_name,
                    'version': plugin_info.version,
                    'description': plugin_info.description,
                    'author': plugin_info.author
                }
            )

            return True

        except Exception as e:
            plugin_info.state = PluginState.FAILED
            plugin_info.error = str(e)

            self._logger.error(
                f"Failed to load plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

            self._event_bus.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={'plugin_name': plugin_name, 'error': str(e)}
            )

            raise PluginError(
                f"Failed to load plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def _load_packaged_plugin(self, plugin_info: PluginInfo) -> Type:
        """Load a plugin class from a packaged plugin."""
        if not plugin_info.manifest or not plugin_info.path:
            raise PluginError('Plugin has no manifest or path')

        manifest = plugin_info.manifest
        plugin_path = pathlib.Path(plugin_info.path)
        code_dir = plugin_path / 'code'
        code_dir = code_dir.resolve()

        if not code_dir.exists():
            raise PluginError(f'Plugin code directory not found: {code_dir}')

        entry_point = manifest.entry_point
        entry_path = code_dir / entry_point

        if not entry_path.exists():
            raise PluginError(f'Plugin entry point not found: {entry_path}')

        plugin_path = plugin_path.resolve()
        if str(plugin_path) not in sys.path:
            sys.path.insert(0, str(plugin_path))

        module_name = f"{plugin_info.name.replace('-', '_')}.code.plugin"

        if entry_point.endswith('.py'):
            spec = importlib.util.spec_from_file_location(module_name, entry_path)
            if not spec or not spec.loader:
                raise PluginError(f'Failed to load plugin module: {entry_path}')

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        else:
            sys.path.insert(0, str(code_dir))
            try:
                module = importlib.import_module(entry_point)
            except ImportError:
                raise PluginError(f'Failed to import plugin module: {entry_point}')

        plugin_class = self._find_plugin_class(module)
        if not plugin_class:
            raise PluginError(f'No plugin class found in module: {module_name}')

        return plugin_class

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_name: The name of the plugin to unload

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error unloading the plugin
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        plugin_info = self._plugins[plugin_name]

        if plugin_info.state not in (PluginState.LOADED, PluginState.ACTIVE):
            self._logger.debug(
                f"Plugin '{plugin_name}' is not loaded",
                extra={'plugin': plugin_name}
            )
            return True

        # Check for dependent plugins
        for other_name, other_info in self._plugins.items():
            if (
                other_name != plugin_name and
                plugin_name in other_info.dependencies and
                other_info.state in (PluginState.LOADED, PluginState.ACTIVE)
            ):
                self._logger.warning(
                    f"Cannot unload plugin '{plugin_name}': Plugin '{other_name}' depends on it",
                    extra={'plugin': plugin_name, 'dependent': other_name}
                )
                return False

        try:
            # Execute pre-disable lifecycle hook if available
            if plugin_info.manifest and PluginLifecycleHook.PRE_DISABLE in plugin_info.manifest.lifecycle_hooks:
                try:
                    execute_hook(
                        hook=PluginLifecycleHook.PRE_DISABLE,
                        plugin_name=plugin_name,
                        manifest=plugin_info.manifest,
                        plugin_instance=plugin_info.instance,
                        context={
                            'plugin_manager': self,
                            'config_manager': self._config_manager,
                            'logger_manager': self._logger_manager,
                            'event_bus': self._event_bus,
                            'file_manager': self._file_manager,
                            'thread_manager': self._thread_manager,
                            'database_manager': self._database_manager,
                            'remote_services_manager': self._remote_services_manager,
                            'security_manager': self._security_manager,
                            'api_manager': self._api_manager,
                            'cloud_manager': self._cloud_manager
                        }
                    )
                except Exception as e:
                    self._logger.warning(
                        f"Pre-disable hook failed for plugin '{plugin_name}': {str(e)}",
                        extra={'plugin': plugin_name, 'error': str(e)}
                    )

            # Unregister extension points
            if plugin_info.manifest:
                unregister_plugin_extensions(plugin_name)

            # Call shutdown method
            if plugin_info.instance and hasattr(plugin_info.instance, 'shutdown'):
                plugin_info.instance.shutdown()

            # Update state
            plugin_info.state = PluginState.INACTIVE
            plugin_info.instance = None

            self._logger.info(
                f"Unloaded plugin '{plugin_name}'",
                extra={'plugin': plugin_name}
            )

            # Execute post-disable lifecycle hook if available
            if plugin_info.manifest and PluginLifecycleHook.POST_DISABLE in plugin_info.manifest.lifecycle_hooks:
                try:
                    execute_hook(
                        hook=PluginLifecycleHook.POST_DISABLE,
                        plugin_name=plugin_name,
                        manifest=plugin_info.manifest,
                        context={
                            'plugin_manager': self,
                            'config_manager': self._config_manager,
                            'logger_manager': self._logger_manager,
                            'event_bus': self._event_bus,
                            'file_manager': self._file_manager,
                            'thread_manager': self._thread_manager,
                            'database_manager': self._database_manager,
                            'remote_services_manager': self._remote_services_manager,
                            'security_manager': self._security_manager,
                            'api_manager': self._api_manager,
                            'cloud_manager': self._cloud_manager
                        }
                    )
                except Exception as e:
                    self._logger.warning(
                        f"Post-disable hook failed for plugin '{plugin_name}': {str(e)}",
                        extra={'plugin': plugin_name, 'error': str(e)}
                    )

            # Publish event
            self._event_bus.publish(
                event_type='plugin/unloaded',
                source='plugin_manager',
                payload={'plugin_name': plugin_name}
            )

            return True

        except Exception as e:
            self._logger.error(
                f"Failed to unload plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

            self._event_bus.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={'plugin_name': plugin_name, 'error': str(e)}
            )

            raise PluginError(
                f"Failed to unload plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin.

        Args:
            plugin_name: The name of the plugin to reload

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error reloading the plugin
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        try:
            if not self.unload_plugin(plugin_name):
                return False

            plugin_info = self._plugins[plugin_name]

            # Reload module if applicable
            if plugin_info.metadata.get('module'):
                module_name = plugin_info.metadata['module']
                if '.' in module_name:
                    base_module_name = module_name.split('.')[0]
                else:
                    base_module_name = module_name

                if base_module_name in sys.modules:
                    importlib.reload(sys.modules[base_module_name])

            return self.load_plugin(plugin_name)

        except Exception as e:
            self._logger.error(
                f"Failed to reload plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

            self._event_bus.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={'plugin_name': plugin_name, 'error': str(e)}
            )

            raise PluginError(
                f"Failed to reload plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_name: The name of the plugin to enable

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error enabling the plugin
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        # Enable in installer
        if self.plugin_installer and self.plugin_installer.is_plugin_installed(plugin_name):
            self.plugin_installer.enable_plugin(plugin_name)

        # Update enabled/disabled lists
        if plugin_name in self._disabled_plugins:
            self._disabled_plugins.remove(plugin_name)

        if plugin_name not in self._enabled_plugins:
            self._enabled_plugins.append(plugin_name)

        self._config_manager.set('plugins.enabled', self._enabled_plugins)
        self._config_manager.set('plugins.disabled', self._disabled_plugins)

        self._logger.info(
            f"Enabled plugin '{plugin_name}'",
            extra={'plugin': plugin_name}
        )

        self._event_bus.publish(
            event_type='plugin/enabled',
            source='plugin_manager',
            payload={'plugin_name': plugin_name}
        )

        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_name: The name of the plugin to disable

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error disabling the plugin
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        plugin_info = self._plugins[plugin_name]

        # Unload if active
        if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
            if not self.unload_plugin(plugin_name):
                raise PluginError(
                    f"Cannot disable plugin '{plugin_name}': Failed to unload it",
                    plugin_name=plugin_name
                )

        # Disable in installer
        if self.plugin_installer and self.plugin_installer.is_plugin_installed(plugin_name):
            self.plugin_installer.disable_plugin(plugin_name)

        # Update enabled/disabled lists
        if plugin_name in self._enabled_plugins:
            self._enabled_plugins.remove(plugin_name)

        if plugin_name not in self._disabled_plugins:
            self._disabled_plugins.append(plugin_name)

        plugin_info.state = PluginState.DISABLED

        self._config_manager.set('plugins.enabled', self._enabled_plugins)
        self._config_manager.set('plugins.disabled', self._disabled_plugins)

        self._logger.info(
            f"Disabled plugin '{plugin_name}'",
            extra={'plugin': plugin_name}
        )

        self._event_bus.publish(
            event_type='plugin/disabled',
            source='plugin_manager',
            payload={'plugin_name': plugin_name}
        )

        return True

    def install_plugin(
        self,
        package_path: Union[str, Path],
        force: bool = False,
        skip_verification: bool = False,
        enable: bool = True,
        resolve_dependencies: bool = True,
        install_dependencies: bool = True
    ) -> bool:
        """
        Install a plugin.

        Args:
            package_path: Path to the plugin package
            force: Whether to overwrite existing plugins
            skip_verification: Whether to skip signature verification
            enable: Whether to enable the plugin after installation
            resolve_dependencies: Whether to resolve dependencies
            install_dependencies: Whether to install missing dependencies

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error during installation
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        try:
            # Use the enhanced installer if available
            if hasattr(self.plugin_installer, 'resolve_dependencies'):
                installed_plugin = self.plugin_installer.install_plugin(
                    package_path=package_path,
                    force=force,
                    skip_verification=skip_verification,
                    enable=enable,
                    resolve_dependencies=resolve_dependencies,
                    install_dependencies=install_dependencies
                )
            else:
                # Fall back to basic installer
                installed_plugin = self.plugin_installer.install_plugin(
                    package_path=package_path,
                    force=force,
                    skip_verification=skip_verification,
                    enable=enable
                )

            manifest = installed_plugin.manifest
            plugin_name = manifest.name

            # Create or update plugin info
            plugin_info = PluginInfo(
                name=manifest.name,
                version=manifest.version,
                description=manifest.description,
                author=manifest.author.name,
                state=PluginState.DISCOVERED,
                dependencies=[dep.name for dep in manifest.dependencies],
                path=str(installed_plugin.install_path),
                metadata={
                    'manifest': True,
                    'display_name': manifest.display_name,
                    'license': manifest.license,
                    'homepage': manifest.homepage,
                    'capabilities': [cap.value for cap in manifest.capabilities],
                    'entry_point': manifest.entry_point,
                    'min_core_version': manifest.min_core_version,
                    'max_core_version': manifest.max_core_version,
                    'installed_at': installed_plugin.installed_at.isoformat(),
                    'enabled': installed_plugin.enabled
                },
                manifest=manifest
            )

            # Parse config schema if available
            if manifest.config_schema:
                try:
                    from qorzen.plugin_system.config_schema import ConfigSchema
                    plugin_info.config_schema = ConfigSchema(**manifest.config_schema)
                except Exception as e:
                    self._logger.warning(
                        f"Failed to parse config schema for plugin {plugin_name}: {str(e)}",
                        extra={'plugin': plugin_name}
                    )

            self._plugins[plugin_name] = plugin_info

            # Update enabled/disabled lists
            if enable:
                if plugin_name not in self._enabled_plugins:
                    self._enabled_plugins.append(plugin_name)
                if plugin_name in self._disabled_plugins:
                    self._disabled_plugins.remove(plugin_name)
            else:
                if plugin_name not in self._disabled_plugins:
                    self._disabled_plugins.append(plugin_name)
                if plugin_name in self._enabled_plugins:
                    self._enabled_plugins.remove(plugin_name)

            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)

            self._logger.info(
                f"Installed plugin '{manifest.name}' v{manifest.version}",
                extra={'plugin': manifest.name, 'version': manifest.version}
            )

            self._event_bus.publish(
                event_type='plugin/installed',
                source='plugin_manager',
                payload={
                    'plugin_name': manifest.name,
                    'version': manifest.version,
                    'description': manifest.description,
                    'author': manifest.author.name,
                    'enabled': enable
                }
            )

            # Load the plugin if enabled
            if enable:
                self.load_plugin(manifest.name)

            return True

        except Exception as e:
            self._logger.error(f'Failed to install plugin: {str(e)}')

            self._event_bus.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={'error': str(e)}
            )

            raise PluginError(f'Failed to install plugin: {str(e)}') from e

    def uninstall_plugin(self, plugin_name: str, keep_data: bool = False, check_dependents: bool = True) -> bool:
        """
        Uninstall a plugin.

        Args:
            plugin_name: The name of the plugin to uninstall
            keep_data: Whether to keep plugin data
            check_dependents: Whether to check for dependents

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error during uninstallation
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        plugin_info = self._plugins[plugin_name]

        # Unload if active
        if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
            if not self.unload_plugin(plugin_name):
                raise PluginError(
                    f"Cannot uninstall plugin '{plugin_name}': Failed to unload it",
                    plugin_name=plugin_name
                )

        # Use the enhanced installer if available
        try:
            if hasattr(self.plugin_installer, 'uninstall_plugin') and hasattr(self.plugin_installer, '_get_dependent_plugins'):
                success = self.plugin_installer.uninstall_plugin(
                    plugin_name=plugin_name,
                    keep_data=keep_data,
                    check_dependents=check_dependents
                )
            else:
                # Fall back to basic installer
                success = self.plugin_installer.uninstall_plugin(
                    plugin_name=plugin_name,
                    keep_data=keep_data
                )

            if success:
                # Remove from plugins dict
                del self._plugins[plugin_name]

                # Update enabled/disabled lists
                if plugin_name in self._enabled_plugins:
                    self._enabled_plugins.remove(plugin_name)
                if plugin_name in self._disabled_plugins:
                    self._disabled_plugins.remove(plugin_name)

                self._config_manager.set('plugins.enabled', self._enabled_plugins)
                self._config_manager.set('plugins.disabled', self._disabled_plugins)

                self._logger.info(
                    f"Uninstalled plugin '{plugin_name}'",
                    extra={'plugin': plugin_name}
                )

                self._event_bus.publish(
                    event_type='plugin/uninstalled',
                    source='plugin_manager',
                    payload={'plugin_name': plugin_name}
                )

            return success

        except Exception as e:
            self._logger.error(
                f"Failed to uninstall plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

            self._event_bus.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={'plugin_name': plugin_name, 'error': str(e)}
            )

            raise PluginError(
                f"Failed to uninstall plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def update_plugin(
        self,
        package_path: Union[str, Path],
        skip_verification: bool = False,
        resolve_dependencies: bool = True,
        install_dependencies: bool = True
    ) -> bool:
        """
        Update a plugin.

        Args:
            package_path: Path to the plugin package
            skip_verification: Whether to skip signature verification
            resolve_dependencies: Whether to resolve dependencies
            install_dependencies: Whether to install missing dependencies

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error during update
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        try:
            # Use the enhanced installer if available
            if hasattr(self.plugin_installer, 'update_plugin') and hasattr(self.plugin_installer, 'resolve_dependencies'):
                updated_plugin = self.plugin_installer.update_plugin(
                    package_path=package_path,
                    skip_verification=skip_verification,
                    resolve_dependencies=resolve_dependencies,
                    install_dependencies=install_dependencies
                )
            else:
                # Fall back to basic installer
                updated_plugin = self.plugin_installer.update_plugin(
                    package_path=package_path,
                    skip_verification=skip_verification
                )

            manifest = updated_plugin.manifest
            plugin_name = manifest.name

            # Update plugin info
            plugin_info = PluginInfo(
                name=manifest.name,
                version=manifest.version,
                description=manifest.description,
                author=manifest.author.name,
                state=PluginState.DISCOVERED,
                dependencies=[dep.name for dep in manifest.dependencies],
                path=str(updated_plugin.install_path),
                metadata={
                    'manifest': True,
                    'display_name': manifest.display_name,
                    'license': manifest.license,
                    'homepage': manifest.homepage,
                    'capabilities': [cap.value for cap in manifest.capabilities],
                    'entry_point': manifest.entry_point,
                    'min_core_version': manifest.min_core_version,
                    'max_core_version': manifest.max_core_version,
                    'installed_at': updated_plugin.installed_at.isoformat(),
                    'enabled': updated_plugin.enabled
                },
                manifest=manifest
            )

            # Parse config schema if available
            if manifest.config_schema:
                try:
                    from qorzen.plugin_system.config_schema import ConfigSchema
                    plugin_info.config_schema = ConfigSchema(**manifest.config_schema)
                except Exception as e:
                    self._logger.warning(
                        f"Failed to parse config schema for plugin {plugin_name}: {str(e)}",
                        extra={'plugin': plugin_name}
                    )

            self._plugins[plugin_name] = plugin_info

            # Update enabled/disabled lists based on updated plugin
            if updated_plugin.enabled:
                if plugin_name not in self._enabled_plugins:
                    self._enabled_plugins.append(plugin_name)
                if plugin_name in self._disabled_plugins:
                    self._disabled_plugins.remove(plugin_name)
            else:
                if plugin_name not in self._disabled_plugins:
                    self._disabled_plugins.append(plugin_name)
                if plugin_name in self._enabled_plugins:
                    self._enabled_plugins.remove(plugin_name)

            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)

            self._logger.info(
                f"Updated plugin '{manifest.name}' to v{manifest.version}",
                extra={'plugin': manifest.name, 'version': manifest.version}
            )

            self._event_bus.publish(
                event_type='plugin/updated',
                source='plugin_manager',
                payload={
                    'plugin_name': manifest.name,
                    'version': manifest.version,
                    'description': manifest.description,
                    'author': manifest.author.name,
                    'enabled': updated_plugin.enabled
                }
            )

            # Reload the plugin if enabled
            if updated_plugin.enabled:
                if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
                    self.reload_plugin(manifest.name)
                else:
                    self.load_plugin(manifest.name)

            return True

        except Exception as e:
            self._logger.error(f'Failed to update plugin: {str(e)}')

            self._event_bus.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={'error': str(e)}
            )

            raise PluginError(f'Failed to update plugin: {str(e)}') from e

    def add_trusted_key(self, key_path: Union[str, Path]) -> bool:
        """
        Add a trusted key for plugin verification.

        Args:
            key_path: Path to the key file

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error adding the key
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_verifier:
            raise PluginError('Plugin verifier not available')

        try:
            from qorzen.plugin_system.signing import PluginSigner

            key_path = Path(key_path)
            if not key_path.exists():
                raise PluginError(f'Key file not found: {key_path}')

            key = PluginSigner.load_key(key_path)
            self.plugin_verifier.add_trusted_key(key)

            if self._trusted_keys_dir:
                dest_path = self._trusted_keys_dir / f'{key.name}_{key.fingerprint[:8]}.json'
                signer = PluginSigner(key)
                signer.save_key(dest_path, include_private=False)

            self._logger.info(
                f'Added trusted key: {key.name} ({key.fingerprint})',
                extra={'key_name': key.name, 'fingerprint': key.fingerprint}
            )

            return True

        except Exception as e:
            self._logger.error(f'Failed to add trusted key: {str(e)}')
            raise PluginError(f'Failed to add trusted key: {str(e)}') from e

    def remove_trusted_key(self, fingerprint: str) -> bool:
        """
        Remove a trusted key.

        Args:
            fingerprint: The fingerprint of the key to remove

        Returns:
            True if successful, False otherwise

        Raises:
            PluginError: If there's an error removing the key
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_verifier:
            raise PluginError('Plugin verifier not available')

        success = self.plugin_verifier.remove_trusted_key(fingerprint)

        if success:
            if self._trusted_keys_dir:
                for key_file in self._trusted_keys_dir.glob(f'*_{fingerprint[:8]}.json'):
                    try:
                        key_file.unlink()
                    except Exception as e:
                        self._logger.warning(
                            f'Failed to delete key file: {str(e)}',
                            extra={'key_file': str(key_file)}
                        )

            self._logger.info(f'Removed trusted key: {fingerprint[:8]}')

        return success

    def get_trusted_keys(self) -> List[Dict[str, Any]]:
        """
        Get all trusted keys.

        Returns:
            A list of trusted keys
        """
        if not self._initialized or not self.plugin_verifier:
            return []

        return [
            {
                'name': key.name,
                'fingerprint': key.fingerprint,
                'created_at': key.created_at.isoformat()
            }
            for key in self.plugin_verifier.trusted_keys
        ]

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            A dictionary of plugin information, or None if the plugin is not found
        """
        if not self._initialized or plugin_name not in self._plugins:
            return None

        plugin_info = self._plugins[plugin_name]

        info = {
            'name': plugin_info.name,
            'version': plugin_info.version,
            'description': plugin_info.description,
            'author': plugin_info.author,
            'state': plugin_info.state.value,
            'dependencies': plugin_info.dependencies,
            'path': plugin_info.path,
            'error': plugin_info.error,
            'load_time': plugin_info.load_time,
            'enabled': self._is_plugin_enabled(plugin_name),
            'instance': plugin_info.instance
        }

        if plugin_info.metadata:
            for key, value in plugin_info.metadata.items():
                if key not in info and key != 'instance':
                    info[key] = value

        if plugin_info.manifest:
            manifest = plugin_info.manifest
            info['display_name'] = manifest.display_name
            info['license'] = manifest.license
            info['homepage'] = manifest.homepage
            info['capabilities'] = [cap.value for cap in manifest.capabilities]
            info['min_core_version'] = manifest.min_core_version
            info['max_core_version'] = manifest.max_core_version
            info['has_config_schema'] = manifest.config_schema is not None
            info['extension_points'] = [
                {
                    'id': ext.id,
                    'name': ext.name,
                    'description': ext.description
                }
                for ext in manifest.extension_points
            ]
            info['extension_uses'] = [
                {
                    'provider': ext.provider,
                    'id': ext.id,
                    'version': ext.version,
                    'required': ext.required
                }
                for ext in manifest.extension_uses
            ]
            info['has_lifecycle_hooks'] = bool(manifest.lifecycle_hooks)

        if plugin_info.config_schema:
            info['config_schema_available'] = True

        return info

    def get_plugin_config_schema(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration schema for a plugin.

        Args:
            plugin_name: The name of the plugin

        Returns:
            The configuration schema, or None if not available
        """
        if not self._initialized or plugin_name not in self._plugins:
            return None

        plugin_info = self._plugins[plugin_name]

        # First check for schema in plugin_info
        if plugin_info.config_schema:
            return plugin_info.config_schema.to_dict()

        # Then check manifest
        if plugin_info.manifest and plugin_info.manifest.config_schema:
            return plugin_info.manifest.config_schema

        return None

    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """
        Get information about all plugins.

        Returns:
            A list of plugin information dictionaries
        """
        if not self._initialized:
            return []

        return [
            self.get_plugin_info(plugin_name)
            for plugin_name in self._plugins
            if self.get_plugin_info(plugin_name) is not None
        ]

    def get_active_plugins(self) -> List[Dict[str, Any]]:
        """
        Get information about all active plugins.

        Returns:
            A list of plugin information dictionaries for active plugins
        """
        if not self._initialized:
            return []

        return [
            self.get_plugin_info(plugin_name)
            for plugin_name, plugin_info in self._plugins.items()
            if plugin_info.state == PluginState.ACTIVE and self.get_plugin_info(plugin_name) is not None
        ]

    def _get_plugin_class(self, plugin_info: PluginInfo) -> Type:
        """Get the plugin class from plugin info."""
        module_name = plugin_info.metadata.get('module')
        class_name = plugin_info.metadata.get('class')

        if not module_name or not class_name:
            raise PluginError(
                f"Invalid plugin metadata for '{plugin_info.name}'",
                plugin_name=plugin_info.name
            )

        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            return plugin_class
        except Exception as e:
            raise PluginError(
                f"Failed to get plugin class for '{plugin_info.name}': {str(e)}",
                plugin_name=plugin_info.name
            ) from e

    def _on_plugin_install_event(self, event: Any) -> None:
        """Handle plugin install event."""
        payload = event.payload
        package_path = payload.get('package_path')

        if not package_path:
            self._logger.error(
                'Invalid plugin installation event: Missing package_path',
                extra={'event_id': event.event_id}
            )
            return

        try:
            force = payload.get('force', False)
            skip_verification = payload.get('skip_verification', False)
            enable = payload.get('enable', True)
            resolve_dependencies = payload.get('resolve_dependencies', True)
            install_dependencies = payload.get('install_dependencies', True)

            self.install_plugin(
                package_path=package_path,
                force=force,
                skip_verification=skip_verification,
                enable=enable,
                resolve_dependencies=resolve_dependencies,
                install_dependencies=install_dependencies
            )
        except Exception as e:
            self._logger.error(
                f'Failed to install plugin: {str(e)}',
                extra={'package_path': package_path, 'error': str(e)}
            )

    def _on_plugin_uninstall_event(self, event: Any) -> None:
        """Handle plugin uninstall event."""
        payload = event.payload
        plugin_name = payload.get('plugin_name')

        if not plugin_name:
            self._logger.error(
                'Invalid plugin uninstallation event: Missing plugin_name',
                extra={'event_id': event.event_id}
            )
            return

        try:
            keep_data = payload.get('keep_data', False)
            check_dependents = payload.get('check_dependents', True)

            self.uninstall_plugin(
                plugin_name=plugin_name,
                keep_data=keep_data,
                check_dependents=check_dependents
            )
        except Exception as e:
            self._logger.error(
                f"Failed to uninstall plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

    def _on_plugin_enable_event(self, event: Any) -> None:
        """Handle plugin enable event."""
        payload = event.payload
        plugin_name = payload.get('plugin_name')

        if not plugin_name:
            self._logger.error(
                'Invalid plugin enable event: Missing plugin_name',
                extra={'event_id': event.event_id}
            )
            return

        try:
            success = self.enable_plugin(plugin_name)
            if success:
                self.load_plugin(plugin_name)
        except Exception as e:
            self._logger.error(
                f"Failed to enable plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

    def _on_plugin_disable_event(self, event: Any) -> None:
        """Handle plugin disable event."""
        payload = event.payload
        plugin_name = payload.get('plugin_name')

        if not plugin_name:
            self._logger.error(
                'Invalid plugin disable event: Missing plugin_name',
                extra={'event_id': event.event_id}
            )
            return

        try:
            self.disable_plugin(plugin_name)
        except Exception as e:
            self._logger.error(
                f"Failed to disable plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

    def _on_plugin_update_event(self, event: Any) -> None:
        """Handle plugin update event."""
        payload = event.payload
        package_path = payload.get('package_path')

        if not package_path:
            self._logger.error(
                'Invalid plugin update event: Missing package_path',
                extra={'event_id': event.event_id}
            )
            return

        try:
            skip_verification = payload.get('skip_verification', False)
            resolve_dependencies = payload.get('resolve_dependencies', True)
            install_dependencies = payload.get('install_dependencies', True)

            self.update_plugin(
                package_path=package_path,
                skip_verification=skip_verification,
                resolve_dependencies=resolve_dependencies,
                install_dependencies=install_dependencies
            )
        except Exception as e:
            self._logger.error(
                f'Failed to update plugin: {str(e)}',
                extra={'package_path': package_path, 'error': str(e)}
            )

    def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes."""
        if key == 'plugins.autoload':
            self._auto_load = value
            self._logger.info(
                f'Plugin autoload set to {value}',
                extra={'autoload': value}
            )
        elif key == 'plugins.enabled':
            self._enabled_plugins = value
            self._logger.info(
                f'Updated enabled plugins list: {value}',
                extra={'enabled': value}
            )
        elif key == 'plugins.disabled':
            self._disabled_plugins = value
            self._logger.info(
                f'Updated disabled plugins list: {value}',
                extra={'disabled': value}
            )
        elif key == 'plugins.directory':
            self._logger.warning(
                'Changing plugin directory requires restart to take effect',
                extra={'directory': value}
            )

    def shutdown(self) -> None:
        """Shut down the plugin manager."""
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Plugin Manager')

            # Get active plugins in dependency-safe order
            active_plugins = [
                name for name, info in self._plugins.items()
                if info.state in (PluginState.LOADED, PluginState.ACTIVE)
            ]

            # Sort plugins to unload in reverse dependency order
            if self.plugin_installer and hasattr(self.plugin_installer, 'get_loading_order'):
                try:
                    loading_order = self.plugin_installer.get_loading_order()
                    # Reverse the order for unloading
                    sorted_plugins = [
                        name for name in reversed(loading_order)
                        if name in active_plugins
                    ]

                    # Add any remaining plugins
                    for name in active_plugins:
                        if name not in sorted_plugins:
                            sorted_plugins.append(name)
                except Exception as e:
                    self._logger.warning(
                        f"Error sorting plugins for shutdown: {str(e)}, falling back to legacy method"
                    )
                    # Legacy fallback
                    sorted_plugins = []
                    remaining_plugins = active_plugins.copy()

                    # First, find plugins with no dependents
                    for plugin_name in active_plugins:
                        if not any(
                            (plugin_name in self._plugins[other].dependencies
                            for other in active_plugins
                            if other != plugin_name)
                        ):
                            sorted_plugins.append(plugin_name)
                            remaining_plugins.remove(plugin_name)

                    # Add remaining plugins
                    sorted_plugins.extend(remaining_plugins)

                    # Reverse for unloading
                    sorted_plugins.reverse()
            else:
                # Legacy fallback
                sorted_plugins = []
                remaining_plugins = active_plugins.copy()

                # First, find plugins with no dependents
                for plugin_name in active_plugins:
                    if not any(
                        (plugin_name in self._plugins[other].dependencies
                        for other in active_plugins
                        if other != plugin_name)
                    ):
                        sorted_plugins.append(plugin_name)
                        remaining_plugins.remove(plugin_name)

                # Add remaining plugins
                sorted_plugins.extend(remaining_plugins)

                # Reverse for unloading
                sorted_plugins.reverse()

            # Unload plugins in the correct order
            for plugin_name in sorted_plugins:
                try:
                    self.unload_plugin(plugin_name)
                except Exception as e:
                    self._logger.error(
                        f"Error unloading plugin '{plugin_name}' during shutdown: {str(e)}",
                        extra={'plugin': plugin_name, 'error': str(e)}
                    )

            # Unregister from events
            if self._event_bus:
                self._event_bus.unsubscribe('plugin_manager')

            # Clean up extension registry
            extension_registry.logger = None

            # Unregister config listener
            self._config_manager.unregister_listener('plugins', self._on_config_changed)

            self._initialized = False
            self._healthy = False

            self._logger.info('Plugin Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Plugin Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down PluginManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the plugin manager."""
        status = super().status()

        if self._initialized:
            plugin_counts = {state.value: 0 for state in PluginState}
            for plugin_info in self._plugins.values():
                plugin_counts[plugin_info.state.value] += 1

            packaging_status = {
                'installed_plugins': len(self.plugin_installer.get_installed_plugins()) if self.plugin_installer else 0,
                'trusted_keys': len(self.plugin_verifier.trusted_keys) if self.plugin_verifier else 0,
                'repositories': len(self.repository_manager.repositories) if self.repository_manager else 0
            }

            status.update({
                'plugins': {
                    'total': len(self._plugins),
                    'active': plugin_counts[PluginState.ACTIVE.value],
                    'loaded': plugin_counts[PluginState.LOADED.value],
                    'failed': plugin_counts[PluginState.FAILED.value],
                    'disabled': plugin_counts[PluginState.DISABLED.value]
                },
                'config': {
                    'auto_load': self._auto_load,
                    'plugin_dir': str(self._plugin_dir) if self._plugin_dir else None,
                    'enabled_count': len(self._enabled_plugins),
                    'disabled_count': len(self._disabled_plugins)
                },
                'packaging': packaging_status,
                'extensions': {
                    'registered_points': sum(len(exts) for exts in extension_registry.extension_points.values()),
                    'pending_uses': sum(len(uses) for uses in extension_registry.pending_uses.values())
                }
            })

        return status