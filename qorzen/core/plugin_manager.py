from __future__ import annotations
import importlib
import importlib.metadata
import importlib.util
import inspect
import os
import pathlib
import pkgutil
import sys
import threading
import time
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, cast

from qorzen.core.base import QorzenManager
from qorzen.core.event_model import EventType, Event
from qorzen.ui.integration import UIIntegration, MainWindowIntegration
from qorzen.plugin_system.interface import PluginInterface
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook
from qorzen.plugin_system.lifecycle import (
    execute_hook,
    set_logger as set_lifecycle_logger,
    get_lifecycle_manager,
    register_ui_integration,
    cleanup_ui
)
from qorzen.plugin_system.extension import register_plugin_extensions, unregister_plugin_extensions, extension_registry
from qorzen.plugin_system.config_schema import ConfigSchema
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, PluginError


class PluginState(str, Enum):
    """Plugin state enum."""
    DISCOVERED = 'discovered'
    LOADED = 'loaded'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    FAILED = 'failed'
    DISABLED = 'disabled'


@dataclass
class PluginInfo:
    """Information about a plugin."""
    name: str
    version: str
    description: str
    author: str
    state: PluginState = PluginState.DISCOVERED
    dependencies: List[str] = field(default_factory=list)
    path: Optional[str] = None
    instance: Optional[Any] = None
    error: Optional[str] = None
    load_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    manifest: Optional[PluginManifest] = None
    config_schema: Optional[ConfigSchema] = None

    def __post_init__(self) -> None:
        """Post-initialization setup."""
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class PluginManager(QorzenManager):
    """Manager for the plugin system.

    This manager handles plugin discovery, loading, and lifecycle management.
    """

    def __init__(self, application_core: Any, config_manager: Any, logger_manager: Any,
                 event_bus_manager: Any, file_manager: Any, thread_manager: Any,
                 database_manager: Any, remote_service_manager: Any, security_manager: Any,
                 api_manager: Any, cloud_manager: Any) -> None:
        """Initialize the plugin manager.

        Args:
            application_core: The application core
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
        self._plugins_lock = threading.RLock()
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
        self.plugin_installer: Optional[Any] = None
        self.plugin_verifier: Optional[Any] = None
        self.repository_manager: Optional[Any] = None
        self._ui_integration: Optional[UIIntegration] = None
        # Add flag to track configuration updates
        self._is_updating_config = False
        get_lifecycle_manager().set_logger(self._logger)

    def initialize(self) -> None:
        """Initialize the plugin manager.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            # Load configuration
            plugin_config = self._config_manager.get('plugins', {})
            plugin_dir = plugin_config.get('directory', 'plugins')
            self._plugin_dir = pathlib.Path(plugin_dir)
            self._auto_load = plugin_config.get('autoload', True)
            self._enabled_plugins = plugin_config.get('enabled', [])
            self._disabled_plugins = plugin_config.get('disabled', [])
            self._repository_config_path = self._plugin_dir / 'repositories.json'

            # Create plugin directory if it doesn't exist
            os.makedirs(self._plugin_dir, exist_ok=True)

            # Initialize packaging system
            self._init_packaging_system(plugin_config)

            # Subscribe to plugin events
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_INSTALLED,
                callback=self._on_plugin_install_event,
                subscriber_id='plugin_manager'
            )
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_UNINSTALLED,
                callback=self._on_plugin_uninstall_event,
                subscriber_id='plugin_manager'
            )
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_ENABLED,
                callback=self._on_plugin_enable_event,
                subscriber_id='plugin_manager'
            )
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_DISABLED,
                callback=self._on_plugin_disable_event,
                subscriber_id='plugin_manager'
            )
            self._event_bus.subscribe(
                event_type=EventType.PLUGIN_UPDATED,
                callback=self._on_plugin_update_event,
                subscriber_id='plugin_manager'
            )

            # Subscribe to UI ready event
            self._event_bus.subscribe(
                event_type=EventType.UI_READY,
                callback=self._on_ui_ready_event,
                subscriber_id='plugin_manager_ui_ready'
            )

            # Discover plugins
            self._discover_entry_point_plugins()
            self._discover_directory_plugins()
            self._discover_packaged_plugins()

            # Register for configuration changes
            self._config_manager.register_listener('plugins', self._on_config_changed)

            self._logger.info(f'Plugin Manager initialized with {len(self._plugins)} plugins discovered')
            self._initialized = True
            self._healthy = True

            # Publish initialization event
            self._event_bus.publish(
                event_type=EventType.PLUGIN_MANAGER_INITIALIZED,
                source='plugin_manager',
                payload={'plugin_count': len(self._plugins)}
            )

            # Load enabled plugins
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
            plugin_config: Plugin configuration
        """
        package_config = plugin_config.get('packaging', {})
        trusted_keys_dir = package_config.get('trusted_keys_dir', 'keys')
        self._trusted_keys_dir = self._plugin_dir / trusted_keys_dir
        os.makedirs(self._trusted_keys_dir, exist_ok=True)

        # Initialize plugin verifier
        from qorzen.plugin_system.signing import PluginVerifier
        self.plugin_verifier = PluginVerifier()

        # Load trusted keys
        if self._trusted_keys_dir.exists():
            try:
                count = self.plugin_verifier.load_trusted_keys(self._trusted_keys_dir)
                self._logger.info(f'Loaded {count} trusted keys for plugin verification')
            except Exception as e:
                self._logger.warning(f'Failed to load trusted keys: {str(e)}')

        # Initialize repository manager
        try:
            from qorzen.plugin_system.repository import PluginRepositoryManager
            self.repository_manager = PluginRepositoryManager(
                config_file=self._repository_config_path if self._repository_config_path.exists() else None,
                logger=self._package_logger
            )
            repos_count = len(self.repository_manager.repositories)
            self._logger.info(f'Initialized repository manager with {repos_count} repositories')
        except Exception as e:
            self._logger.warning(f'Failed to initialize repository manager: {str(e)}')
            self.repository_manager = None

        # Initialize plugin installer
        try:
            from qorzen.plugin_system.integration import IntegratedPluginInstaller
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
            from qorzen.plugin_system.installer import PluginInstaller
            self.plugin_installer = PluginInstaller(
                plugins_dir=self._plugin_dir,
                verifier=self.plugin_verifier,
                logger=self._package_logger
            )
            self._logger.info('Initialized basic plugin installer (without repository support)')

    def _get_core_version(self) -> str:
        """Get the version of the core application.

        Returns:
            Core version string
        """
        try:
            from qorzen.__version__ import __version__
            return __version__
        except ImportError:
            return '0.1.0'

    def _package_logger(self, message: str, level: str = 'info') -> None:
        """Logger for the packaging system.

        Args:
            message: Message to log
            level: Log level
        """
        if level.lower() == 'info':
            self._logger.info(message)
        elif level.lower() == 'warning':
            self._logger.warning(message)
        elif level.lower() == 'error':
            self._logger.error(message)
        else:
            self._logger.debug(message)

    def _on_ui_ready_event(self, event: Event) -> None:
        main_window = event.payload.get('main_window')
        if not main_window:
            self._logger.warning('UI ready event missing main_window')
            return

        # Avoid recreating UI integration
        if self._ui_integration is not None:
            self._logger.debug('UI integration already exists, updating with new main window')
            # Just update the reference if needed, don't re-register everything
            return

        self._ui_integration = MainWindowIntegration(main_window)
        self._logger.info('Created UI integration')

        # Add tracking to prevent duplicate UI setup for plugins
        if not hasattr(self, '_ui_setup_plugins'):
            self._ui_setup_plugins = set()

        active_plugins = [(name, info) for name, info in self._plugins.items()
                          if info.state == PluginState.ACTIVE and info.instance is not None]

        for name, info in active_plugins:
            # Skip if UI already set up for this plugin
            if name in self._ui_setup_plugins:
                self._logger.debug(f"UI already set up for plugin '{name}', skipping")
                continue

            try:
                register_ui_integration(name, self._ui_integration)
                if hasattr(info.instance, 'on_ui_ready'):
                    self._logger.debug(f"Calling on_ui_ready for plugin '{name}'")
                    info.instance.on_ui_ready(self._ui_integration)
                    self._ui_setup_plugins.add(name)  # Mark UI as set up
                else:
                    self._logger.debug(f"Plugin '{name}' does not support on_ui_ready")
            except Exception as e:
                self._logger.error(f"Error initializing UI for plugin '{name}': {str(e)}")

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

        # Add plugin directory to path
        plugin_dir_str = str(self._plugin_dir.absolute())
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)

        try:
            for item in self._plugin_dir.iterdir():
                # Skip non-directories and special directories
                if not item.is_dir():
                    continue
                if item.name.startswith('.') or item.name in ('__pycache__', 'backups'):
                    continue

                # Check for plugin files
                init_file = item / '__init__.py'
                plugin_file = item / 'plugin.py'
                manifest_file = item / 'manifest.json'

                # Try to load from manifest
                if manifest_file.exists():
                    try:
                        manifest = PluginManifest.load(manifest_file)
                        plugin_class = None
                        module_name = item.name
                        entry_point = manifest.entry_point

                        # Try to load entry point
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
                                        f'Failed to load entry point {entry_point} for plugin {manifest.name}: {str(e)}',
                                        extra={'plugin': manifest.name, 'entry_point': entry_point}
                                    )
                        else:
                            try:
                                module = importlib.import_module(f'{module_name}.{entry_point}')
                                plugin_class = self._find_plugin_class(module)
                            except Exception as e:
                                self._logger.warning(
                                    f'Failed to import module {entry_point} for plugin {manifest.name}: {str(e)}',
                                    extra={'plugin': manifest.name, 'entry_point': entry_point}
                                )

                        # Create plugin info if class found
                        if plugin_class:
                            plugin_info = self._extract_plugin_metadata(
                                plugin_class,
                                manifest.name,
                                path=str(item),
                                manifest=manifest
                            )

                            # Check for config schema
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
                                        f'Failed to load config schema for plugin {manifest.name}: {str(e)}',
                                        extra={'plugin': manifest.name}
                                    )

                            # Add to plugins if not already discovered
                            if plugin_info.name not in self._plugins:
                                self._plugins[plugin_info.name] = plugin_info
                                self._logger.debug(
                                    f"Discovered plugin '{plugin_info.name}' from manifest",
                                    extra={
                                        'plugin': plugin_info.name,
                                        'version': plugin_info.version,
                                        'path': str(item)
                                    }
                                )
                        else:
                            self._logger.warning(
                                f'No plugin class found for manifest {manifest.name}',
                                extra={'plugin': manifest.name}
                            )
                    except Exception as e:
                        self._logger.error(
                            f"Failed to load manifest for plugin directory '{item.name}': {str(e)}",
                            extra={'directory': str(item)}
                        )
                        continue

                # Try to load from Python files
                if init_file.exists() or plugin_file.exists():
                    try:
                        module_name = item.name

                        # Load module
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

                        # Find plugin class
                        plugin_class = self._find_plugin_class(module)
                        if not plugin_class:
                            if not manifest_file.exists():
                                self._logger.warning(
                                    f'No plugin class found in {module_name}',
                                    extra={'module': module_name}
                                )
                            continue

                        # Create plugin info
                        plugin_info = self._extract_plugin_metadata(
                            plugin_class,
                            module_name,
                            path=str(item)
                        )

                        # Add to plugins if not already discovered
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
        """Discover plugins from the packaging system."""
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

                    # Load config schema if available
                    if manifest.config_schema:
                        try:
                            from qorzen.plugin_system.config_schema import ConfigSchema
                            plugin_info.config_schema = ConfigSchema(**manifest.config_schema)
                        except Exception as e:
                            self._logger.warning(
                                f'Failed to parse config schema for plugin {name}: {str(e)}',
                                extra={'plugin': name}
                            )

                    # Add to plugins
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
            Plugin class or None if not found
        """
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'name') and hasattr(obj, 'version') and hasattr(obj, 'description'):
                # Skip BasePlugin class
                if obj.__name__ == 'BasePlugin':
                    continue
                return obj
        return None

    def _extract_plugin_metadata(self, plugin_class: Type, default_name: str,
                                 path: Optional[str] = None, entry_point_name: Optional[str] = None,
                                 manifest: Optional[PluginManifest] = None) -> PluginInfo:
        """Extract metadata from a plugin class.

        Args:
            plugin_class: Plugin class
            default_name: Default name to use if not specified
            path: Optional path to the plugin
            entry_point_name: Optional entry point name
            manifest: Optional plugin manifest

        Returns:
            Plugin info
        """
        name = getattr(plugin_class, 'name', default_name)
        version = getattr(plugin_class, 'version', '0.1.0')
        description = getattr(plugin_class, 'description', 'No description')
        author = getattr(plugin_class, 'author', 'Unknown')
        dependencies = getattr(plugin_class, 'dependencies', [])

        # Make sure state is properly stored in the PluginInfo object, not just in metadata
        metadata = {
            'class': plugin_class.__name__,
            'module': plugin_class.__module__,
            'entry_point': entry_point_name
        }

        # Create PluginInfo with the correct state
        plugin_info = PluginInfo(
            name=name,
            version=version,
            description=description,
            author=author,
            state=PluginState.DISCOVERED,  # Explicitly set state here
            dependencies=dependencies,
            path=path,
            metadata=metadata,
            manifest=manifest
        )

        return plugin_info

    def _load_enabled_plugins(self) -> None:
        """Load all enabled plugins."""
        if not self.plugin_installer:
            # Legacy loading without dependency resolution
            # First load plugins with no dependencies
            for plugin_name, plugin_info in self._plugins.items():
                if not plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                    self.load_plugin(plugin_name)

            # Then load plugins with dependencies
            for plugin_name, plugin_info in self._plugins.items():
                if plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                    self.load_plugin(plugin_name)
        else:
            # Load plugins in dependency order
            try:
                # Get manifests for enabled plugins
                plugin_manifests = {}
                for plugin_name, plugin_info in self._plugins.items():
                    if self._is_plugin_enabled(plugin_name) and plugin_info.manifest:
                        plugin_manifests[plugin_name] = plugin_info.manifest

                # Get loading order
                loading_order = self.plugin_installer.get_loading_order()

                # Load plugins in order
                for plugin_name in loading_order:
                    if plugin_name in self._plugins and self._is_plugin_enabled(plugin_name):
                        self.load_plugin(plugin_name)
            except Exception as e:
                self._logger.error(f'Failed to load plugins in dependency order: {str(e)}')
                self._logger.warning('Falling back to legacy plugin loading method')

                # Fall back to legacy loading
                for plugin_name, plugin_info in self._plugins.items():
                    if not plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                        self.load_plugin(plugin_name)

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
        # Check disabled list
        if plugin_name in self._disabled_plugins:
            return False

        # Check enabled list
        if plugin_name in self._enabled_plugins:
            return True

        # Check plugin installer
        if self.plugin_installer:
            plugin = self.plugin_installer.get_installed_plugin(plugin_name)
            if plugin:
                return plugin.enabled

        # Default to auto_load setting
        return self._auto_load

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if the plugin was loaded successfully, False otherwise

        Raises:
            PluginError: If the plugin cannot be loaded
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        plugin_info = self._plugins[plugin_name]

        # Check if already loaded
        if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
            self._logger.debug(
                f"Plugin '{plugin_name}' is already loaded",
                extra={'plugin': plugin_name}
            )
            return True

        # Check if plugin is being loaded (prevent duplicate loading)
        if hasattr(plugin_info, '_loading') and plugin_info._loading:
            self._logger.debug(f"Plugin '{plugin_name}' is already being loaded", extra={'plugin': plugin_name})
            return True

        # Check if disabled
        if plugin_name in self._disabled_plugins:
            self._logger.warning(
                f"Plugin '{plugin_name}' is disabled and cannot be loaded",
                extra={'plugin': plugin_name}
            )
            return False

        # Set loading flag
        setattr(plugin_info, '_loading', True)

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
                        f"Failed to load plugin '{plugin_name}': Dependency '{dependency}' could not be loaded",
                        extra={'plugin': plugin_name, 'dependency': dependency}
                    )
                    return False

        try:
            # Execute pre-enable hook if available
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

            # Load the plugin class
            if plugin_info.manifest:
                plugin_class = self._load_packaged_plugin(plugin_info)
            else:
                plugin_class = self._get_plugin_class(plugin_info)

            # Create instance
            plugin_info.instance = plugin_class()

            # Check if it implements the PluginInterface
            from qorzen.plugin_system.interface import PluginInterface
            if not isinstance(plugin_info.instance, PluginInterface):
                self._logger.warning(
                    f"Plugin '{plugin_name}' does not implement PluginInterface",
                    extra={'plugin': plugin_name}
                )

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

            # Register extensions if available
            if plugin_info.manifest:
                register_plugin_extensions(
                    plugin_name=plugin_name,
                    plugin_instance=plugin_info.instance,
                    manifest=plugin_info.manifest
                )

            # Set up UI integration if available
            if self._ui_integration and hasattr(plugin_info.instance, 'on_ui_ready'):
                # Register UI integration with lifecycle manager
                register_ui_integration(plugin_name, self._ui_integration)

                # Call on_ui_ready
                plugin_info.instance.on_ui_ready(self._ui_integration)

            # Update plugin state
            plugin_info.state = PluginState.ACTIVE
            plugin_info.load_time = time.time()

            # Add a flag to prevent immediate unloading
            plugin_info.recently_loaded = True

            self._logger.info(
                f"Loaded plugin '{plugin_name}' v{plugin_info.version}",
                extra={'plugin': plugin_name, 'version': plugin_info.version}
            )

            # Execute post-enable hook if available
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
                event_type=EventType.PLUGIN_LOADED,
                source='plugin_manager',
                payload={
                    'plugin_name': plugin_name,
                    'version': plugin_info.version,
                    'description': plugin_info.description,
                    'author': plugin_info.author,
                    'no_auto_unload': True
                }
            )

            # Set a timer to clear the recently_loaded flag
            if self._thread_manager:
                self._thread_manager.submit_task(
                    lambda: self._clear_recent_load_flag(plugin_name),
                    name=f"clear_recent_load_{plugin_name}",
                    submitter='plugin_manager'
                )

            return True

        except Exception as e:
            # Clear loading flag on error
            setattr(plugin_info, '_loading', False)

            plugin_info.state = PluginState.FAILED
            plugin_info.error = str(e)

            self._logger.error(
                f"Failed to load plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

            self._event_bus.publish(
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={
                    'plugin_name': plugin_name,
                    'error': str(e)
                }
            )

            raise PluginError(
                f"Failed to load plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def _clear_recent_load_flag(self, plugin_name: str) -> None:
        """Clear the recently_loaded flag after a delay."""
        import time
        # Wait for 5 seconds before clearing the flag
        time.sleep(5)

        with self._plugin_lock:  # Assume you have a lock for thread safety
            if plugin_name in self._plugins:
                plugin_info = self._plugins[plugin_name]
                if hasattr(plugin_info, 'recently_loaded'):
                    delattr(plugin_info, 'recently_loaded')

    def _load_packaged_plugin(self, plugin_info: PluginInfo) -> Type:
        """Load a plugin from a package.

        Args:
            plugin_info: Plugin information

        Returns:
            Plugin class

        Raises:
            PluginError: If the plugin cannot be loaded
        """
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

        # Add plugin path to Python path
        plugin_path = plugin_path.resolve()
        if str(plugin_path) not in sys.path:
            sys.path.insert(0, str(plugin_path))

        # Load module
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

        # Find plugin class
        plugin_class = self._find_plugin_class(module)
        if not plugin_class:
            raise PluginError(f'No plugin class found in module: {module_name}')

        return plugin_class

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if the plugin was unloaded successfully, False otherwise

        Raises:
            PluginError: If the plugin cannot be unloaded
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

        plugin_info = self._plugins[plugin_name]

        # Prevent unloading during UI setup
        if hasattr(plugin_info, '_ui_setup_in_progress') and plugin_info._ui_setup_in_progress:
            self._logger.warning(f"Cannot unload plugin '{plugin_name}' during UI setup",
                                 extra={'plugin': plugin_name})
            return False

        # Check if already unloaded
        if plugin_info.state not in (PluginState.LOADED, PluginState.ACTIVE):
            self._logger.debug(
                f"Plugin '{plugin_name}' is not loaded",
                extra={'plugin': plugin_name}
            )
            return True

        # Check for dependencies
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
            # Execute pre-disable hook if available
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

            # Unregister extensions if available
            if plugin_info.manifest:
                unregister_plugin_extensions(plugin_name)

            # Shut down the plugin
            if plugin_info.instance and hasattr(plugin_info.instance, 'shutdown'):
                plugin_info.instance.shutdown()

            # Clean up UI components
            cleanup_ui(plugin_name)

            # Update plugin state
            plugin_info.state = PluginState.INACTIVE
            plugin_info.instance = None

            self._logger.info(
                f"Unloaded plugin '{plugin_name}'",
                extra={'plugin': plugin_name}
            )

            # Execute post-disable hook if available
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
                event_type=EventType.PLUGIN_UNLOADED,
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
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={
                    'plugin_name': plugin_name,
                    'error': str(e)
                }
            )

            raise PluginError(
                f"Failed to unload plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if the plugin was reloaded successfully, False otherwise

        Raises:
            PluginError: If the plugin cannot be reloaded
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        try:
            # Unload the plugin
            if not self.unload_plugin(plugin_name):
                return False

            # Reload the module if possible
            plugin_info = self._plugins[plugin_name]
            if plugin_info.metadata.get('module'):
                module_name = plugin_info.metadata['module']
                if '.' in module_name:
                    base_module_name = module_name.split('.')[0]
                else:
                    base_module_name = module_name

                if base_module_name in sys.modules:
                    importlib.reload(sys.modules[base_module_name])

            # Load the plugin
            return self.load_plugin(plugin_name)

        except Exception as e:
            self._logger.error(
                f"Failed to reload plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

            self._event_bus.publish(
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={
                    'plugin_name': plugin_name,
                    'error': str(e)
                }
            )

            raise PluginError(
                f"Failed to reload plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if the plugin was enabled successfully, False otherwise

        Raises:
            PluginError: If the plugin cannot be enabled
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)
        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

            # Prevent duplicate enabling
        if plugin_name in self._enabled_plugins:
            self._logger.debug(f"Plugin '{plugin_name}' is already enabled", extra={'plugin': plugin_name})
            return True

            # Rest of the method remains the same
        if self.plugin_installer and self.plugin_installer.is_plugin_installed(plugin_name):
            self.plugin_installer.enable_plugin(plugin_name)
        if plugin_name in self._disabled_plugins:
            self._disabled_plugins.remove(plugin_name)
        if plugin_name not in self._enabled_plugins:
            self._enabled_plugins.append(plugin_name)

            # Use a flag to prevent recursive event handling
        self._is_updating_config = True
        try:
            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)
        finally:
            self._is_updating_config = False

        self._logger.info(f"Enabled plugin '{plugin_name}'", extra={'plugin': plugin_name})
        self._event_bus.publish(event_type=EventType.PLUGIN_ENABLED, source='plugin_manager',
                                payload={'plugin_name': plugin_name})
        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if the plugin was disabled successfully, False otherwise

        Raises:
            PluginError: If the plugin cannot be disabled
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)
        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

            # Check if already disabled to prevent circular calls
        if plugin_name in self._disabled_plugins:
            self._logger.debug(f"Plugin '{plugin_name}' is already disabled", extra={'plugin': plugin_name})
            return True

        plugin_info = self._plugins[plugin_name]
        if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
            if not self.unload_plugin(plugin_name):
                raise PluginError(f"Cannot disable plugin '{plugin_name}': Failed to unload it",
                                  plugin_name=plugin_name)

        if self.plugin_installer and self.plugin_installer.is_plugin_installed(plugin_name):
            self.plugin_installer.disable_plugin(plugin_name)

        if plugin_name in self._enabled_plugins:
            self._enabled_plugins.remove(plugin_name)

        if plugin_name not in self._disabled_plugins:
            self._disabled_plugins.append(plugin_name)

        plugin_info.state = PluginState.DISABLED

        # Use a flag to prevent recursive event handling
        self._is_updating_config = True
        try:
            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)
        finally:
            self._is_updating_config = False

        self._logger.info(f"Disabled plugin '{plugin_name}'", extra={'plugin': plugin_name})
        self._event_bus.publish(event_type=EventType.PLUGIN_DISABLED, source='plugin_manager',
                                payload={'plugin_name': plugin_name})
        return True

    def install_plugin(self, package_path: Union[str, Path], force: bool = False,
                       skip_verification: bool = False, enable: bool = True,
                       resolve_dependencies: bool = True, install_dependencies: bool = True) -> bool:
        """Install a plugin.

        Args:
            package_path: Path to the plugin package
            force: Force installation even if already installed
            skip_verification: Skip signature verification
            enable: Enable the plugin after installation
            resolve_dependencies: Resolve dependencies
            install_dependencies: Install dependencies

        Returns:
            True if the plugin was installed successfully, False otherwise

        Raises:
            PluginError: If the plugin cannot be installed
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        try:
            # Install the plugin
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
                installed_plugin = self.plugin_installer.install_plugin(
                    package_path=package_path,
                    force=force,
                    skip_verification=skip_verification,
                    enable=enable
                )

            # Get manifest
            manifest = installed_plugin.manifest
            plugin_name = manifest.name

            # Create plugin info
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

            # Load config schema if available
            if manifest.config_schema:
                try:
                    from qorzen.plugin_system.config_schema import ConfigSchema
                    plugin_info.config_schema = ConfigSchema(**manifest.config_schema)
                except Exception as e:
                    self._logger.warning(
                        f'Failed to parse config schema for plugin {plugin_name}: {str(e)}',
                        extra={'plugin': plugin_name}
                    )

            # Add to plugins
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

            # Update configuration
            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)

            self._logger.info(
                f"Installed plugin '{manifest.name}' v{manifest.version}",
                extra={'plugin': manifest.name, 'version': manifest.version}
            )

            # Publish event
            self._event_bus.publish(
                event_type=EventType.PLUGIN_INSTALLED,
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
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={'error': str(e)}
            )

            raise PluginError(f'Failed to install plugin: {str(e)}') from e

    def uninstall_plugin(self, plugin_name: str, keep_data: bool = False,
                         check_dependents: bool = True) -> bool:
        """Uninstall a plugin.

        Args:
            plugin_name: Name of the plugin
            keep_data: Keep plugin data
            check_dependents: Check for dependent plugins

        Returns:
            True if the plugin was uninstalled successfully, False otherwise

        Raises:
            PluginError: If the plugin cannot be uninstalled
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

        try:
            # Uninstall the plugin
            if hasattr(self.plugin_installer, 'uninstall_plugin') and hasattr(self.plugin_installer,
                                                                              '_get_dependent_plugins'):
                success = self.plugin_installer.uninstall_plugin(
                    plugin_name=plugin_name,
                    keep_data=keep_data,
                    check_dependents=check_dependents
                )
            else:
                success = self.plugin_installer.uninstall_plugin(
                    plugin_name=plugin_name,
                    keep_data=keep_data
                )

            if success:
                # Remove from plugins
                del self._plugins[plugin_name]

                # Update enabled/disabled lists
                if plugin_name in self._enabled_plugins:
                    self._enabled_plugins.remove(plugin_name)
                if plugin_name in self._disabled_plugins:
                    self._disabled_plugins.remove(plugin_name)

                # Update configuration
                self._config_manager.set('plugins.enabled', self._enabled_plugins)
                self._config_manager.set('plugins.disabled', self._disabled_plugins)

                self._logger.info(
                    f"Uninstalled plugin '{plugin_name}'",
                    extra={'plugin': plugin_name}
                )

                # Publish event
                self._event_bus.publish(
                    event_type=EventType.PLUGIN_UNINSTALLED,
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
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={
                    'plugin_name': plugin_name,
                    'error': str(e)
                }
            )

            raise PluginError(
                f"Failed to uninstall plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def update_plugin(self, package_path: Union[str, Path],
                      skip_verification: bool = False,
                      resolve_dependencies: bool = True,
                      install_dependencies: bool = True) -> bool:
        """Update a plugin.

        Args:
            package_path: Path to the plugin package
            skip_verification: Skip signature verification
            resolve_dependencies: Resolve dependencies
            install_dependencies: Install dependencies

        Returns:
            True if the plugin was updated successfully, False otherwise

        Raises:
            PluginError: If the plugin cannot be updated
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        try:
            # Update the plugin
            if hasattr(self.plugin_installer, 'update_plugin') and hasattr(self.plugin_installer,
                                                                           'resolve_dependencies'):
                updated_plugin = self.plugin_installer.update_plugin(
                    package_path=package_path,
                    skip_verification=skip_verification,
                    resolve_dependencies=resolve_dependencies,
                    install_dependencies=install_dependencies
                )
            else:
                updated_plugin = self.plugin_installer.update_plugin(
                    package_path=package_path,
                    skip_verification=skip_verification
                )

            # Get manifest
            manifest = updated_plugin.manifest
            plugin_name = manifest.name

            # Create plugin info
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

            # Load config schema if available
            if manifest.config_schema:
                try:
                    from qorzen.plugin_system.config_schema import ConfigSchema
                    plugin_info.config_schema = ConfigSchema(**manifest.config_schema)
                except Exception as e:
                    self._logger.warning(
                        f'Failed to parse config schema for plugin {plugin_name}: {str(e)}',
                        extra={'plugin': plugin_name}
                    )

            # Update plugins
            self._plugins[plugin_name] = plugin_info

            # Update enabled/disabled lists
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

            # Update configuration
            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)

            self._logger.info(
                f"Updated plugin '{manifest.name}' to v{manifest.version}",
                extra={'plugin': manifest.name, 'version': manifest.version}
            )

            # Publish event
            self._event_bus.publish(
                event_type=EventType.PLUGIN_UPDATED,
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
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={'error': str(e)}
            )

            raise PluginError(f'Failed to update plugin: {str(e)}') from e

    def _get_plugin_class(self, plugin_info: PluginInfo) -> Type:
        """Get the plugin class from metadata.

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

    def _on_plugin_install_event(self, event: Event) -> None:
        """Handle plugin install event.

        Args:
            event: The event object
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
            # Get installation options
            force = payload.get('force', False)
            skip_verification = payload.get('skip_verification', False)
            enable = payload.get('enable', True)
            resolve_dependencies = payload.get('resolve_dependencies', True)
            install_dependencies = payload.get('install_dependencies', True)

            # Install the plugin
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

    def _on_plugin_uninstall_event(self, event: Event) -> None:
        """Handle plugin uninstall event.

        Args:
            event: The event object
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
            # Get uninstallation options
            keep_data = payload.get('keep_data', False)
            check_dependents = payload.get('check_dependents', True)

            # Uninstall the plugin
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

    def _on_plugin_enable_event(self, event: Event) -> None:
        payload = event.payload
        plugin_name = payload.get('plugin_name')
        if not plugin_name:
            self._logger.error('Invalid plugin enable event: Missing plugin_name', extra={'event_id': event.event_id})
            return

        # Check if plugin is already enabled to avoid infinite loop
        if plugin_name in self._enabled_plugins:
            # Plugin is already in enabled list, just load it if not loaded
            try:
                plugin_info = self._plugins[plugin_name]
                if plugin_info.state not in (PluginState.LOADED, PluginState.ACTIVE):
                    self.load_plugin(plugin_name)
            except Exception as e:
                self._logger.error(f"Failed to load already enabled plugin '{plugin_name}': {str(e)}",
                                   extra={'plugin': plugin_name, 'error': str(e)})
            return

        # Normal flow for newly enabled plugins
        try:
            success = self.enable_plugin(plugin_name)
            if success:
                self.load_plugin(plugin_name)
        except Exception as e:
            self._logger.error(f"Failed to enable plugin '{plugin_name}': {str(e)}",
                               extra={'plugin': plugin_name, 'error': str(e)})

    def _on_plugin_disable_event(self, event: Event) -> None:
        """Handle plugin disable event.

        Args:
            event: The event object
        """
        payload = event.payload
        plugin_name = payload.get('plugin_name')
        if not plugin_name:
            self._logger.error('Invalid plugin disable event: Missing plugin_name', extra={'event_id': event.event_id})
            return

        # Check if plugin is already disabled to avoid infinite loop
        if plugin_name in self._disabled_plugins:
            self._logger.debug(f"Plugin '{plugin_name}' is already disabled", extra={'plugin': plugin_name})
            return

        # Only proceed with disabling if not already disabled
        try:
            self.disable_plugin(plugin_name)
        except Exception as e:
            self._logger.error(f"Failed to disable plugin '{plugin_name}': {str(e)}",
                               extra={'plugin': plugin_name, 'error': str(e)})

    def _on_plugin_update_event(self, event: Event) -> None:
        """Handle plugin update event.

        Args:
            event: The event object
        """
        payload = event.payload
        package_path = payload.get('package_path')

        if not package_path:
            self._logger.error(
                'Invalid plugin update event: Missing package_path',
                extra={'event_id': event.event_id}
            )
            return

        try:
            # Get update options
            skip_verification = payload.get('skip_verification', False)
            resolve_dependencies = payload.get('resolve_dependencies', True)
            install_dependencies = payload.get('install_dependencies', True)

            # Update the plugin
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
        """Handle configuration changes.

        Args:
            key: Configuration key
            value: Configuration value
        """
        if hasattr(self, '_is_updating_config') and self._is_updating_config:
            return

        if key == 'plugins.autoload':
            self._auto_load = value
            self._logger.info(f'Plugin autoload set to {value}', extra={'autoload': value})
        elif key == 'plugins.enabled':
            # Prevent recursive calls by checking what's changing
            added = [p for p in value if p not in self._enabled_plugins]
            self._enabled_plugins = value
            self._logger.info(f'Updated enabled plugins list: {value}', extra={'enabled': value})
            # Don't trigger enable events from config changes to prevent loops
        elif key == 'plugins.disabled':
            self._disabled_plugins = value
            self._logger.info(f'Updated disabled plugins list: {value}', extra={'disabled': value})
        elif key == 'plugins.directory':
            self._logger.warning('Changing plugin directory requires restart to take effect',
                                 extra={'directory': value})

    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """Get all plugins."""

        return self._plugins

    def shutdown(self) -> None:
        """Shut down the plugin manager.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Plugin Manager')

            # Get list of active plugins
            active_plugins = [
                name for name, info in self._plugins.items()
                if info.state in (PluginState.LOADED, PluginState.ACTIVE)
            ]

            # Try to get sorted list of plugins based on dependencies
            if self.plugin_installer and hasattr(self.plugin_installer, 'get_loading_order'):
                try:
                    loading_order = self.plugin_installer.get_loading_order()
                    sorted_plugins = [name for name in reversed(loading_order) if name in active_plugins]

                    # Add any remaining plugins
                    for name in active_plugins:
                        if name not in sorted_plugins:
                            sorted_plugins.append(name)
                except Exception as e:
                    self._logger.warning(
                        f'Error sorting plugins for shutdown: {str(e)}, falling back to legacy method'
                    )
                    # Fall back to legacy method
                    sorted_plugins = []
                    remaining_plugins = active_plugins.copy()

                    # First unload plugins with no dependents
                    for plugin_name in active_plugins:
                        if not any((
                                plugin_name in self._plugins[other].dependencies
                                for other in active_plugins if other != plugin_name
                        )):
                            sorted_plugins.append(plugin_name)
                            remaining_plugins.remove(plugin_name)

                    # Add remaining plugins
                    sorted_plugins.extend(remaining_plugins)

                    # Reverse to unload in reverse dependency order
                    sorted_plugins.reverse()
            else:
                # Legacy method
                sorted_plugins = []
                remaining_plugins = active_plugins.copy()

                # First unload plugins with no dependents
                for plugin_name in active_plugins:
                    if not any((
                            plugin_name in self._plugins[other].dependencies
                            for other in active_plugins if other != plugin_name
                    )):
                        sorted_plugins.append(plugin_name)
                        remaining_plugins.remove(plugin_name)

                # Add remaining plugins
                sorted_plugins.extend(remaining_plugins)

                # Reverse to unload in reverse dependency order
                sorted_plugins.reverse()

            # Unload plugins in order
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
                self._event_bus.unsubscribe('plugin_manager_ui_ready')

            # Clear lifecycle manager logger
            get_lifecycle_manager().set_logger(None)

            # Unregister from configuration changes
            self._config_manager.unregister_listener('plugins', self._on_config_changed)

            # Update state
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
            Status information
        """
        status = super().status()

        if self._initialized:
            # Count plugins by state
            plugin_counts = {state.value: 0 for state in PluginState}
            for plugin_info in self._plugins.values():
                plugin_counts[plugin_info.state.value] += 1

            # Get packaging status
            packaging_status = {
                'installed_plugins': len(self.plugin_installer.get_installed_plugins()) if self.plugin_installer else 0,
                'trusted_keys': len(self.plugin_verifier.trusted_keys) if self.plugin_verifier else 0,
                'repositories': len(self.repository_manager.repositories) if self.repository_manager else 0
            }

            # Add status information
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
                    'registered_points': sum((len(exts) for exts in extension_registry.extension_points.values())),
                    'pending_uses': sum((len(uses) for uses in extension_registry.pending_uses.values()))
                },
                'ui_integration': self._ui_integration is not None
            })

        return status