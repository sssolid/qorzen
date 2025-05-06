"""Plugin manager with packaging system integration.

This module enhances the original plugin manager with integration for
the plugin packaging system, adding capabilities for installation,
verification, and management of packaged plugins.
"""

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
from qorzen.plugin_system.installer import PluginInstaller, InstalledPlugin
from qorzen.plugin_system.manifest import PluginManifest
from qorzen.plugin_system.package import PluginPackage
from qorzen.plugin_system.signing import PluginVerifier
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, PluginError
from tests.unit.core.test_cloud_manager import cloud_manager


class PluginState(Enum):
    """State of a plugin in the plugin manager."""

    DISCOVERED = 'discovered'
    LOADED = 'loaded'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    FAILED = 'failed'
    DISABLED = 'disabled'


@dataclass
class PluginInfo:
    """Information about a plugin.

    Attributes:
        name: Plugin identifier
        version: Plugin version
        description: Brief description
        author: Plugin author
        state: Current plugin state
        dependencies: List of plugin dependencies
        path: Path to the plugin directory
        instance: Plugin instance if loaded
        error: Error message if loading failed
        load_time: When the plugin was loaded
        metadata: Additional plugin metadata
        manifest: Plugin manifest if installed from a package
    """

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

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class PluginManager(QorzenManager):
    """Enhanced plugin manager with packaging system integration.

    This class extends the original plugin manager with capabilities
    for installation, verification, and management of packaged plugins.

    Attributes:
        plugin_installer: Plugin installer for package management
        plugin_verifier: Plugin verifier for signature verification
    """

    def __init__(
            self,
            config_manager: Any,
            logger_manager: Any,
            event_bus_manager: Any,
            file_manager: Any,
            thread_manager: Any,
            database_manager: Any,
            remote_service_manager: Any,
            security_manager: Any,
            api_manager: Any,
            cloud_manager: Any,
    ) -> None:
        """Initialize the plugin manager.

        Args:
            config_manager: Configuration manager
            logger_manager: Logger manager
            event_bus_manager: Event bus manager
            file_manager: File manager
            thread_manager: Thread manager
            database_manager: Database manager
            remote_service_manager: Remote service manager
            security_manager: Security manager
            api_manager: API manager
            cloud_manager: Cloud manager
        """
        super().__init__(name='PluginManager')
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

        # Plugin packaging system integration
        self.plugin_installer: Optional[PluginInstaller] = None
        self.plugin_verifier: Optional[PluginVerifier] = None
        self._trusted_keys_dir: Optional[pathlib.Path] = None

    def initialize(self) -> None:
        """Initialize the plugin manager.

        This loads configuration, discovers plugins, and sets up
        event handlers.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            plugin_config = self._config_manager.get('plugins', {})
            plugin_dir = plugin_config.get('directory', 'plugins')
            self._plugin_dir = pathlib.Path(plugin_dir)
            self._auto_load = plugin_config.get('autoload', True)
            self._enabled_plugins = plugin_config.get('enabled', [])
            self._disabled_plugins = plugin_config.get('disabled', [])

            # Create plugin directories
            os.makedirs(self._plugin_dir, exist_ok=True)

            # Initialize plugin packaging system
            self._init_packaging_system(plugin_config)

            # Subscribe to events
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

            # Discover plugins
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
        """Initialize the plugin packaging system.

        Args:
            plugin_config: Plugin configuration dictionary
        """
        package_config = plugin_config.get('packaging', {})

        # Set up trusted keys directory
        trusted_keys_dir = package_config.get('trusted_keys_dir', 'keys')
        self._trusted_keys_dir = self._plugin_dir / trusted_keys_dir
        os.makedirs(self._trusted_keys_dir, exist_ok=True)

        # Create plugin verifier
        self.plugin_verifier = PluginVerifier()

        # Load trusted keys
        if self._trusted_keys_dir.exists():
            try:
                count = self.plugin_verifier.load_trusted_keys(self._trusted_keys_dir)
                self._logger.info(f'Loaded {count} trusted keys for plugin verification')
            except Exception as e:
                self._logger.warning(f'Failed to load trusted keys: {str(e)}')

        # Create plugin installer
        self.plugin_installer = PluginInstaller(
            plugins_dir=self._plugin_dir,
            verifier=self.plugin_verifier,
            logger=self._package_logger
        )

    def _package_logger(self, message: str, level: str = "info") -> None:
        """Logger function for the plugin installer.

        Args:
            message: Log message
            level: Log level
        """
        if level.lower() == "info":
            self._logger.info(message)
        elif level.lower() == "warning":
            self._logger.warning(message)
        elif level.lower() == "error":
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
        """Discover plugins from the plugin directory."""
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

                # Skip special directories
                if item.name.startswith('.') or item.name in ('__pycache__', 'backups'):
                    continue

                # Check for Python module structure
                init_file = item / '__init__.py'
                plugin_file = item / 'plugin.py'

                if init_file.exists() or plugin_file.exists():
                    try:
                        module_name = item.name
                        if init_file.exists():
                            module = importlib.import_module(module_name)
                        elif plugin_file.exists():
                            spec = importlib.util.spec_from_file_location(
                                f'{module_name}.plugin',
                                plugin_file
                            )
                            if not spec or not spec.loader:
                                continue

                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                        else:
                            continue

                        plugin_class = self._find_plugin_class(module)
                        if not plugin_class:
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
                                extra={
                                    'plugin': plugin_info.name,
                                    'version': plugin_info.version,
                                    'path': str(item)
                                }
                            )

                    except Exception as e:
                        self._logger.error(
                            f"Failed to discover plugin from directory '{item.name}': {str(e)}",
                            extra={'directory': str(item)}
                        )

        except Exception as e:
            self._logger.error(f'Failed to discover directory plugins: {str(e)}')

    def _discover_packaged_plugins(self) -> None:
        """Discover plugins from installed packages."""
        if not self.plugin_installer:
            return

        try:
            installed_plugins = self.plugin_installer.get_installed_plugins()

            for name, plugin in installed_plugins.items():
                # Skip if already discovered
                if name in self._plugins:
                    continue

                try:
                    # Convert manifest to plugin info
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

                    # Add plugin info
                    self._plugins[name] = plugin_info

                    # Update enabled/disabled lists
                    if plugin.enabled and name not in self._enabled_plugins:
                        self._enabled_plugins.append(name)
                    elif not plugin.enabled and name not in self._disabled_plugins:
                        self._disabled_plugins.append(name)

                    self._logger.debug(
                        f"Discovered installed plugin '{name}' v{manifest.version}",
                        extra={
                            'plugin': name,
                            'version': manifest.version,
                            'enabled': plugin.enabled
                        }
                    )

                except Exception as e:
                    self._logger.error(
                        f"Failed to process installed plugin '{name}': {str(e)}",
                        extra={'plugin': name, 'error': str(e)}
                    )

        except Exception as e:
            self._logger.error(f'Failed to discover installed plugins: {str(e)}')

    def _find_plugin_class(self, module: Any) -> Optional[Type]:
        """Find a plugin class in a module.

        Args:
            module: Module to search

        Returns:
            Plugin class if found, None otherwise
        """
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'name') and hasattr(obj, 'version') and hasattr(obj, 'description'):
                return obj

        return None

    def _extract_plugin_metadata(
            self,
            plugin_class: Type,
            default_name: str,
            path: Optional[str] = None,
            entry_point_name: Optional[str] = None
    ) -> PluginInfo:
        """Extract metadata from a plugin class.

        Args:
            plugin_class: Plugin class
            default_name: Default name to use if not specified
            path: Path to the plugin directory
            entry_point_name: Entry point name if from entry points

        Returns:
            Plugin information
        """
        name = getattr(plugin_class, 'name', default_name)
        version = getattr(plugin_class, 'version', '0.1.0')
        description = getattr(plugin_class, 'description', 'No description')
        author = getattr(plugin_class, 'author', 'Unknown')
        dependencies = getattr(plugin_class, 'dependencies', [])

        plugin_info = PluginInfo(
            name=name,
            version=version,
            description=description,
            author=author,
            state=PluginState.DISCOVERED,
            dependencies=dependencies,
            path=path,
            metadata={
                'class': plugin_class.__name__,
                'module': plugin_class.__module__,
                'entry_point': entry_point_name
            }
        )

        return plugin_info

    def _load_enabled_plugins(self) -> None:
        """Load all enabled plugins."""
        # Load plugins without dependencies first
        for plugin_name, plugin_info in self._plugins.items():
            if not plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                self.load_plugin(plugin_name)

        # Then load plugins with dependencies
        for plugin_name, plugin_info in self._plugins.items():
            if plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                self.load_plugin(plugin_name)

    def _is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if the plugin is enabled, False otherwise
        """
        if plugin_name in self._disabled_plugins:
            return False

        if plugin_name in self._enabled_plugins:
            return True

        # For packaged plugins, also check the installer
        if self.plugin_installer:
            plugin = self.plugin_installer.get_installed_plugin(plugin_name)
            if plugin:
                return plugin.enabled

        return self._auto_load

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin.

        Args:
            plugin_name: Name of the plugin to load

        Returns:
            True if the plugin was loaded successfully, False otherwise

        Raises:
            PluginError: If plugin loading fails
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

        # Check and load dependencies
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
                        f"Failed to load plugin '{plugin_name}': Dependency '{dependency}' could not be loaded",
                        extra={'plugin': plugin_name, 'dependency': dependency}
                    )
                    return False

        try:
            # Get plugin class
            if plugin_info.manifest:
                # Load packaged plugin
                plugin_class = self._load_packaged_plugin(plugin_info)
            else:
                # Load regular plugin
                plugin_class = self._get_plugin_class(plugin_info)

            # Instantiate plugin
            plugin_info.instance = plugin_class()

            # Initialize plugin
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

            plugin_info.state = PluginState.ACTIVE
            plugin_info.load_time = time.time()

            self._logger.info(
                f"Loaded plugin '{plugin_name}' v{plugin_info.version}",
                extra={'plugin': plugin_name, 'version': plugin_info.version}
            )

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
        """Load a plugin from a package.

        Args:
            plugin_info: Plugin information

        Returns:
            Plugin class

        Raises:
            PluginError: If plugin loading fails
        """
        if not plugin_info.manifest or not plugin_info.path:
            raise PluginError("Plugin has no manifest or path")

        manifest = plugin_info.manifest
        plugin_path = pathlib.Path(plugin_info.path)

        # Get code directory
        code_dir = plugin_path / "code"
        if not code_dir.exists():
            raise PluginError(f"Plugin code directory not found: {code_dir}")

        # Find entry point
        entry_point = manifest.entry_point
        entry_path = code_dir / entry_point

        if not entry_path.exists():
            raise PluginError(f"Plugin entry point not found: {entry_path}")

        # Add plugin directory to sys.path
        if str(plugin_path) not in sys.path:
            sys.path.insert(0, str(plugin_path))

        # Import plugin module
        module_name = f"{plugin_info.name.replace('-', '_')}_plugin"

        if entry_point.endswith('.py'):
            # Load from .py file
            spec = importlib.util.spec_from_file_location(module_name, entry_path)
            if not spec or not spec.loader:
                raise PluginError(f"Failed to load plugin module: {entry_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        else:
            # Try to load as a package
            sys.path.insert(0, str(code_dir))
            try:
                module = importlib.import_module(entry_point)
            except ImportError:
                raise PluginError(f"Failed to import plugin module: {entry_point}")

        # Find plugin class
        plugin_class = self._find_plugin_class(module)
        if not plugin_class:
            raise PluginError(f"No plugin class found in module: {module_name}")

        return plugin_class

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if the plugin was unloaded successfully, False otherwise

        Raises:
            PluginError: If plugin unloading fails
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

        # Check dependencies - don't unload if other plugins depend on this
        for other_name, other_info in self._plugins.items():
            if other_name != plugin_name and plugin_name in other_info.dependencies and (
                    other_info.state in (PluginState.LOADED, PluginState.ACTIVE)
            ):
                self._logger.warning(
                    f"Cannot unload plugin '{plugin_name}': Plugin '{other_name}' depends on it",
                    extra={'plugin': plugin_name, 'dependent': other_name}
                )
                return False

        try:
            # Shutdown plugin
            if plugin_info.instance and hasattr(plugin_info.instance, 'shutdown'):
                plugin_info.instance.shutdown()

            plugin_info.state = PluginState.INACTIVE
            plugin_info.instance = None

            self._logger.info(
                f"Unloaded plugin '{plugin_name}'",
                extra={'plugin': plugin_name}
            )

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
        """Reload a plugin.

        Args:
            plugin_name: Name of the plugin to reload

        Returns:
            True if the plugin was reloaded successfully, False otherwise

        Raises:
            PluginError: If plugin reloading fails
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        try:
            # Unload the plugin
            if not self.unload_plugin(plugin_name):
                return False

            # Reload the module
            plugin_info = self._plugins[plugin_name]

            if plugin_info.metadata.get('module'):
                module_name = plugin_info.metadata['module']
                if '.' in module_name:
                    base_module_name = module_name.split('.')[0]
                else:
                    base_module_name = module_name

                if base_module_name in sys.modules:
                    importlib.reload(sys.modules[base_module_name])

            # Load the plugin again
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
        """Enable a plugin.

        Args:
            plugin_name: Name of the plugin to enable

        Returns:
            True if the plugin was enabled, False otherwise
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        # Update plugin installer if available
        if self.plugin_installer and self.plugin_installer.is_plugin_installed(plugin_name):
            self.plugin_installer.enable_plugin(plugin_name)

        # Update enabled/disabled lists
        if plugin_name in self._disabled_plugins:
            self._disabled_plugins.remove(plugin_name)

        if plugin_name not in self._enabled_plugins:
            self._enabled_plugins.append(plugin_name)

        self._config_manager.set('plugins.enabled', self._enabled_plugins)
        self._config_manager.set('plugins.disabled', self._disabled_plugins)

        self._logger.info(f"Enabled plugin '{plugin_name}'", extra={'plugin': plugin_name})

        self._event_bus.publish(
            event_type='plugin/enabled',
            source='plugin_manager',
            payload={'plugin_name': plugin_name}
        )

        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_name: Name of the plugin to disable

        Returns:
            True if the plugin was disabled, False otherwise
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        plugin_info = self._plugins[plugin_name]

        # Unload the plugin if it's loaded
        if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
            if not self.unload_plugin(plugin_name):
                raise PluginError(
                    f"Cannot disable plugin '{plugin_name}': Failed to unload it",
                    plugin_name=plugin_name
                )

        # Update plugin installer if available
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

        self._logger.info(f"Disabled plugin '{plugin_name}'", extra={'plugin': plugin_name})

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
            enable: bool = True
    ) -> bool:
        """Install a plugin from a package.

        Args:
            package_path: Path to the plugin package
            force: Whether to force installation (overwrite existing)
            skip_verification: Whether to skip signature verification
            enable: Whether to enable the plugin after installation

        Returns:
            True if the plugin was installed successfully, False otherwise

        Raises:
            PluginError: If plugin installation fails
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        try:
            # Install the plugin
            installed_plugin = self.plugin_installer.install_plugin(
                package_path=package_path,
                force=force,
                skip_verification=skip_verification,
                enable=enable
            )

            # Add the plugin to our registry
            manifest = installed_plugin.manifest
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

            self._plugins[manifest.name] = plugin_info

            # Update enabled/disabled lists
            if enable:
                if manifest.name not in self._enabled_plugins:
                    self._enabled_plugins.append(manifest.name)
                if manifest.name in self._disabled_plugins:
                    self._disabled_plugins.remove(manifest.name)
            else:
                if manifest.name not in self._disabled_plugins:
                    self._disabled_plugins.append(manifest.name)
                if manifest.name in self._enabled_plugins:
                    self._enabled_plugins.remove(manifest.name)

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
            self._logger.error(f"Failed to install plugin: {str(e)}")

            self._event_bus.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={'error': str(e)}
            )

            raise PluginError(f"Failed to install plugin: {str(e)}") from e

    def uninstall_plugin(self, plugin_name: str, keep_data: bool = False) -> bool:
        """Uninstall a plugin.

        Args:
            plugin_name: Name of the plugin to uninstall
            keep_data: Whether to keep plugin data

        Returns:
            True if the plugin was uninstalled successfully, False otherwise

        Raises:
            PluginError: If plugin uninstallation fails
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        # Unload the plugin first
        plugin_info = self._plugins[plugin_name]
        if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
            if not self.unload_plugin(plugin_name):
                raise PluginError(
                    f"Cannot uninstall plugin '{plugin_name}': Failed to unload it",
                    plugin_name=plugin_name
                )

        try:
            # Uninstall the plugin
            success = self.plugin_installer.uninstall_plugin(
                plugin_name=plugin_name,
                keep_data=keep_data
            )

            if not success:
                return False

            # Remove from our registry
            del self._plugins[plugin_name]

            # Update enabled/disabled lists
            if plugin_name in self._enabled_plugins:
                self._enabled_plugins.remove(plugin_name)

            if plugin_name in self._disabled_plugins:
                self._disabled_plugins.remove(plugin_name)

            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)

            self._logger.info(f"Uninstalled plugin '{plugin_name}'", extra={'plugin': plugin_name})

            self._event_bus.publish(
                event_type='plugin/uninstalled',
                source='plugin_manager',
                payload={'plugin_name': plugin_name}
            )

            return True

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

    def add_trusted_key(self, key_path: Union[str, Path]) -> bool:
        """Add a trusted key for plugin verification.

        Args:
            key_path: Path to the key file

        Returns:
            True if the key was added successfully, False otherwise
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_verifier:
            raise PluginError('Plugin verifier not available')

        try:
            from qorzen.plugin_system.signing import PluginSigner

            key_path = Path(key_path)
            if not key_path.exists():
                raise PluginError(f"Key file not found: {key_path}")

            # Load the key
            key = PluginSigner.load_key(key_path)

            # Add to verifier
            self.plugin_verifier.add_trusted_key(key)

            # Copy to trusted keys directory
            if self._trusted_keys_dir:
                dest_path = self._trusted_keys_dir / f"{key.name}_{key.fingerprint[:8]}.json"
                signer = PluginSigner(key)
                signer.save_key(dest_path, include_private=False)

            self._logger.info(
                f"Added trusted key: {key.name} ({key.fingerprint})",
                extra={'key_name': key.name, 'fingerprint': key.fingerprint}
            )

            return True

        except Exception as e:
            self._logger.error(f"Failed to add trusted key: {str(e)}")
            raise PluginError(f"Failed to add trusted key: {str(e)}") from e

    def remove_trusted_key(self, fingerprint: str) -> bool:
        """Remove a trusted key.

        Args:
            fingerprint: Fingerprint of the key to remove

        Returns:
            True if the key was removed, False otherwise
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_verifier:
            raise PluginError('Plugin verifier not available')

        # Remove from verifier
        success = self.plugin_verifier.remove_trusted_key(fingerprint)

        if success:
            # Remove from trusted keys directory
            if self._trusted_keys_dir:
                for key_file in self._trusted_keys_dir.glob(f"*_{fingerprint[:8]}.json"):
                    try:
                        key_file.unlink()
                    except Exception as e:
                        self._logger.warning(
                            f"Failed to delete key file: {str(e)}",
                            extra={'key_file': str(key_file)}
                        )

            self._logger.info(f"Removed trusted key: {fingerprint[:8]}")

        return success

    def get_trusted_keys(self) -> List[Dict[str, Any]]:
        """Get a list of trusted keys.

        Returns:
            List of trusted keys
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
        """Get information about a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin information or None if not found
        """
        if not self._initialized or plugin_name not in self._plugins:
            return None

        plugin_info = self._plugins[plugin_name]

        # Convert to dictionary
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
            'enabled': self._is_plugin_enabled(plugin_name)
        }

        # Add metadata
        if plugin_info.metadata:
            for key, value in plugin_info.metadata.items():
                if key not in info:
                    info[key] = value

        # Add manifest information
        if plugin_info.manifest:
            manifest = plugin_info.manifest
            info['display_name'] = manifest.display_name
            info['license'] = manifest.license
            info['homepage'] = manifest.homepage
            info['capabilities'] = [cap.value for cap in manifest.capabilities]
            info['min_core_version'] = manifest.min_core_version
            info['max_core_version'] = manifest.max_core_version

        return info

    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """Get information about all plugins.

        Returns:
            List of plugin information dictionaries
        """
        if not self._initialized:
            return []

        return [
            self.get_plugin_info(plugin_name) for plugin_name in self._plugins
            if self.get_plugin_info(plugin_name) is not None
        ]

    def get_active_plugins(self) -> List[Dict[str, Any]]:
        """Get information about active plugins.

        Returns:
            List of active plugin information dictionaries
        """
        if not self._initialized:
            return []

        return [
            self.get_plugin_info(plugin_name) for plugin_name, plugin_info in self._plugins.items()
            if plugin_info.state == PluginState.ACTIVE
               and self.get_plugin_info(plugin_name) is not None
        ]

    def _get_plugin_class(self, plugin_info: PluginInfo) -> Type:
        """Get the plugin class for a plugin.

        Args:
            plugin_info: Plugin information

        Returns:
            Plugin class

        Raises:
            PluginError: If the plugin class cannot be loaded
        """
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
        """Handle plugin installation events.

        Args:
            event: Event object
        """
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

            self.install_plugin(
                package_path=package_path,
                force=force,
                skip_verification=skip_verification,
                enable=enable
            )
        except Exception as e:
            self._logger.error(
                f'Failed to install plugin: {str(e)}',
                extra={'package_path': package_path, 'error': str(e)}
            )

    def _on_plugin_uninstall_event(self, event: Any) -> None:
        """Handle plugin uninstallation events.

        Args:
            event: Event object
        """
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

            self.uninstall_plugin(plugin_name=plugin_name, keep_data=keep_data)
        except Exception as e:
            self._logger.error(
                f"Failed to uninstall plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

    def _on_plugin_enable_event(self, event: Any) -> None:
        """Handle plugin enable events.

        Args:
            event: Event object
        """
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
        """Handle plugin disable events.

        Args:
            event: Event object
        """
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

    def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: Configuration key
            value: New value
        """
        if key == 'plugins.autoload':
            self._auto_load = value
            self._logger.info(f'Plugin autoload set to {value}', extra={'autoload': value})
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
        """Shut down the plugin manager.

        This unloads all plugins in the reverse order of their dependencies.
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Plugin Manager')

            # Unload active plugins in reverse dependency order
            active_plugins = [
                name for name, info in self._plugins.items()
                if info.state in (PluginState.LOADED, PluginState.ACTIVE)
            ]

            # Sort plugins by dependencies
            sorted_plugins = []
            remaining_plugins = active_plugins.copy()

            # First, add plugins that nothing depends on
            for plugin_name in active_plugins:
                if not any(
                        plugin_name in self._plugins[other].dependencies
                        for other in active_plugins if other != plugin_name
                ):
                    sorted_plugins.append(plugin_name)
                    remaining_plugins.remove(plugin_name)

            # Add remaining plugins
            sorted_plugins.extend(remaining_plugins)

            # Reverse to unload in opposite order of dependencies
            sorted_plugins.reverse()

            for plugin_name in sorted_plugins:
                try:
                    self.unload_plugin(plugin_name)
                except Exception as e:
                    self._logger.error(
                        f"Error unloading plugin '{plugin_name}' during shutdown: {str(e)}",
                        extra={'plugin': plugin_name, 'error': str(e)}
                    )

            # Unsubscribe from events
            if self._event_bus:
                self._event_bus.unsubscribe('plugin_manager')

            # Unregister from configuration changes
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
        """Get the status of the plugin manager.

        Returns:
            Dictionary with plugin manager status
        """
        status = super().status()

        if self._initialized:
            # Count plugins by state
            plugin_counts = {state.value: 0 for state in PluginState}
            for plugin_info in self._plugins.values():
                plugin_counts[plugin_info.state.value] += 1

            # Add plugin packaging info
            packaging_status = {
                'installed_plugins': len(self.plugin_installer.get_installed_plugins()) if self.plugin_installer else 0,
                'trusted_keys': len(self.plugin_verifier.trusted_keys) if self.plugin_verifier else 0
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
                'packaging': packaging_status
            })

        return status