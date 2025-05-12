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
from qorzen.core.service_locator import ServiceLocator, ManagerType
from qorzen.core.thread_manager import ThreadExecutionContext, TaskProgressReporter, TaskPriority
from qorzen.ui.integration import UIIntegration, MainWindowIntegration
from qorzen.plugin_system.interface import PluginInterface
from qorzen.plugin_system.manifest import PluginManifest, PluginLifecycleHook
from qorzen.plugin_system.lifecycle import (
    execute_hook, set_logger as set_lifecycle_logger,
    get_lifecycle_manager, register_ui_integration, cleanup_ui,
    get_plugin_state, set_plugin_state, PluginLifecycleState,
    wait_for_ui_ready, signal_ui_ready, set_thread_manager
)
from qorzen.plugin_system.extension import (
    register_plugin_extensions, unregister_plugin_extensions, extension_registry
)
from qorzen.plugin_system.config_schema import ConfigSchema
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError, PluginError


class PluginState(str, Enum):
    """Enumeration of possible plugin states."""
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
        """Initialize optional fields with default values if not provided."""
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class PluginManager(QorzenManager):
    """
    Manager responsible for plugin lifecycle operations.

    This manager handles discovering, loading, unloading, and managing plugins,
    as well as their dependencies and extensions.
    """

    def __init__(self, application_core: Any, service_locator: ServiceLocator) -> None:
        """
        Initialize the plugin manager.

        Args:
            application_core: Core application instance
            service_locator: Service locator with registered managers
        """
        super().__init__(name="PluginManager")

        # Locks for thread safety
        self._plugins_lock = threading.RLock()
        self._ui_lock = threading.RLock()

        # Core components
        self._application_core = application_core
        self._service_locator = service_locator

        # Get essential managers from the service locator
        self._config_manager = service_locator.get(ManagerType.CONFIG)
        self._logger_manager = service_locator.get(ManagerType.LOGGING)
        self._logger = self._logger_manager.get_logger('plugin_manager')
        self._event_bus = service_locator.get(ManagerType.EVENT_BUS)
        self._file_manager = service_locator.get(ManagerType.FILE)
        self._thread_manager = service_locator.get(ManagerType.THREAD)
        self._database_manager = service_locator.get(ManagerType.DATABASE)
        self._remote_services_manager = service_locator.get(ManagerType.REMOTE_SERVICES)
        self._security_manager = service_locator.get(ManagerType.SECURITY)
        self._api_manager = service_locator.get(ManagerType.API)
        self._cloud_manager = service_locator.get(ManagerType.CLOUD)
        self._task_manager = service_locator.get(ManagerType.TASK)

        # Plugin system components
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_dir: Optional[pathlib.Path] = None
        self._entry_point_group = 'qorzen.plugins'
        self._auto_load = True
        self._enabled_plugins: List[str] = []
        self._disabled_plugins: List[str] = []
        self._repository_config_path: Optional[Path] = None
        self._ui_setup_plugins: Set[str] = set()

        # Plugin system components to be initialized later
        self.plugin_installer: Optional[Any] = None
        self.plugin_verifier: Optional[Any] = None
        self.repository_manager: Optional[Any] = None
        self._ui_integration: Optional[UIIntegration] = None

        # State tracking
        self._is_updating_config = False

        # Set up lifecycle manager
        set_lifecycle_logger(self._logger)
        set_thread_manager(self._thread_manager)

    def initialize(self) -> None:
        """Initialize the plugin manager."""
        try:
            # Get plugin configuration
            plugin_config = self._config_manager.get('plugins', {})
            plugin_dir = plugin_config.get('directory', 'plugins')
            self._plugin_dir = pathlib.Path(plugin_dir)
            self._auto_load = plugin_config.get('autoload', True)
            self._enabled_plugins = plugin_config.get('enabled', [])
            self._disabled_plugins = plugin_config.get('disabled', [])
            self._repository_config_path = self._plugin_dir / 'repositories.json'

            # Ensure plugin directory exists
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
            self._event_bus.subscribe(
                event_type=EventType.UI_READY,
                callback=self._on_ui_ready_event,
                subscriber_id='plugin_manager_ui_ready'
            )

            # Discover plugins
            self._discover_entry_point_plugins()
            self._discover_directory_plugins()
            self._discover_packaged_plugins()

            # Register configuration listener
            self._config_manager.register_listener('plugins', self._on_config_changed)

            self._logger.info(
                f'Plugin Manager initialized with {len(self._plugins)} plugins discovered'
            )

            self._initialized = True
            self._healthy = True

            # Publish initialization event
            self._event_bus.publish(
                event_type=EventType.PLUGIN_MANAGER_INITIALIZED,
                source='plugin_manager',
                payload={'plugin_count': len(self._plugins)}
            )

            # Load enabled plugins if auto-load is enabled
            if self._auto_load:
                self._load_enabled_plugins()

        except Exception as e:
            self._logger.error(f'Failed to initialize Plugin Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize PluginManager: {str(e)}',
                manager_name=self.name
            ) from e

    def _init_packaging_system(self, plugin_config: Dict[str, Any]) -> None:
        """Initialize the plugin packaging system."""
        package_config = plugin_config.get('packaging', {})
        trusted_keys_dir = package_config.get('trusted_keys_dir', 'keys')
        self._trusted_keys_dir = self._plugin_dir / trusted_keys_dir
        os.makedirs(self._trusted_keys_dir, exist_ok=True)

        # Initialize plugin verifier
        from qorzen.plugin_system.signing import PluginVerifier
        self.plugin_verifier = PluginVerifier()
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
        """Get the core application version."""
        try:
            from qorzen.__version__ import __version__
            return __version__
        except ImportError:
            return '0.1.0'

    def _package_logger(self, message: str, level: str = 'info') -> None:
        """Logger function for packaging system components."""
        if level.lower() == 'info':
            self._logger.info(message)
        elif level.lower() == 'warning':
            self._logger.warning(message)
        elif level.lower() == 'error':
            self._logger.error(message)
        else:
            self._logger.debug(message)

    def _on_ui_ready_event(self, event: Event) -> None:
        """Handle UI ready event."""
        main_window = event.payload.get('main_window')
        if not main_window:
            self._logger.warning('UI ready event missing main_window')
            return

        with self._ui_lock:
            if self._ui_integration is not None:
                self._logger.debug('UI integration already exists, updating with new main window')
                return

            # Create UI integration
            self._ui_integration = MainWindowIntegration(main_window)
            self._logger.info('Created UI integration')

            # Initialize UI for active plugins
            active_plugins = []
            with self._plugins_lock:
                active_plugins = [
                    (name, info) for name, info in self._plugins.items()
                    if info.state == PluginState.ACTIVE and info.instance is not None
                ]

            for name, info in active_plugins:
                self._setup_plugin_ui(name, info)

    def _setup_plugin_ui(self, plugin_name: str, plugin_info: PluginInfo, progress_reporter: Optional[TaskProgressReporter]) -> None:
        """Set up UI for a plugin."""
        with self._ui_lock:
            if plugin_name in self._ui_setup_plugins:
                self._logger.debug(f"UI already set up for plugin '{plugin_name}', skipping")
                return

            # Get the plugin's lifecycle state
            lifecycle_state = get_plugin_state(plugin_name)
            if lifecycle_state in (PluginLifecycleState.UI_READY, PluginLifecycleState.LOADING):
                self._logger.debug(f"Plugin '{plugin_name}' UI setup already in progress, skipping")
                return

            # Set lifecycle state
            set_plugin_state(plugin_name, PluginLifecycleState.LOADING)

        # Register UI integration
        if not self._ui_integration:
            self._logger.warning(f"Cannot set up UI for plugin '{plugin_name}': UI integration not available")
            return

        try:
            # Register UI integration for the plugin
            register_ui_integration(plugin_name, self._ui_integration)

            # Call on_ui_ready if supported
            if hasattr(plugin_info.instance, 'on_ui_ready'):
                self._logger.debug(f"Calling on_ui_ready for plugin '{plugin_name}'")

                # Ensure execution on main thread
                if self._thread_manager.is_main_thread():
                    plugin_info.instance.on_ui_ready(self._ui_integration)
                else:
                    self._thread_manager.execute_on_main_thread_sync(
                        plugin_info.instance.on_ui_ready,
                        self._ui_integration
                    )

                with self._ui_lock:
                    self._ui_setup_plugins.add(plugin_name)

                # Wait for up to 5 seconds for the plugin to signal UI ready
                wait_for_ui_ready(plugin_name, 5.0)
            else:
                self._logger.debug(f"Plugin '{plugin_name}' does not support on_ui_ready")
                signal_ui_ready(plugin_name)

        except Exception as e:
            self._logger.error(f"Error initializing UI for plugin '{plugin_name}': {str(e)}")

            # Reset lifecycle state on error
            set_plugin_state(plugin_name, PluginLifecycleState.FAILED)
            signal_ui_ready(plugin_name)

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

                    with self._plugins_lock:
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

                # Check for manifest-based plugin
                if manifest_file.exists():
                    try:
                        manifest = PluginManifest.load(manifest_file)
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

                        if plugin_class:
                            plugin_info = self._extract_plugin_metadata(
                                plugin_class,
                                manifest.name,
                                path=str(item),
                                manifest=manifest
                            )

                            # Load config schema if available
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

                            with self._plugins_lock:
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

                # Check for module-based plugin
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
                            if not manifest_file.exists():
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

                        with self._plugins_lock:
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
        """Discover installed packaged plugins."""
        if not self.plugin_installer:
            return

        try:
            installed_plugins = self.plugin_installer.get_installed_plugins()
            for name, plugin in installed_plugins.items():
                with self._plugins_lock:
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

                    with self._plugins_lock:
                        self._plugins[name] = plugin_info

                    # Update enabled/disabled lists
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
        """Find a plugin class in a module."""
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, 'name') and hasattr(obj, 'version') and hasattr(obj, 'description'):
                if obj.__name__ == 'BasePlugin':
                    continue
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
        """Load all enabled plugins in proper dependency order."""
        if not self.plugin_installer:
            # Legacy loading
            for plugin_name, plugin_info in self._plugins.items():
                if not plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                    self.load_plugin(plugin_name)

            for plugin_name, plugin_info in self._plugins.items():
                if plugin_info.dependencies and self._is_plugin_enabled(plugin_name):
                    self.load_plugin(plugin_name)
        else:
            # Enhanced loading with dependency resolution
            try:
                plugin_manifests = {}
                with self._plugins_lock:
                    for plugin_name, plugin_info in self._plugins.items():
                        if self._is_plugin_enabled(plugin_name) and plugin_info.manifest:
                            plugin_manifests[plugin_name] = plugin_info.manifest

                loading_order = self.plugin_installer.get_loading_order()
                for plugin_name in loading_order:
                    with self._plugins_lock:
                        if plugin_name in self._plugins and self._is_plugin_enabled(plugin_name):
                            self.load_plugin(plugin_name)
            except Exception as e:
                self._logger.error(f'Failed to load plugins in dependency order: {str(e)}')
                self._logger.warning('Falling back to legacy plugin loading method')

                # Legacy loading fallback
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
        Load a plugin by name.

        Args:
            plugin_name: Name of the plugin to load

        Returns:
            True if successfully loaded, False otherwise

        Raises:
            PluginError: If the plugin cannot be loaded
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        with self._plugins_lock:
            if plugin_name not in self._plugins:
                raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

            plugin_info = self._plugins[plugin_name]

            if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
                self._logger.debug(f"Plugin '{plugin_name}' is already loaded", extra={'plugin': plugin_name})
                return True

            lifecycle_state = get_plugin_state(plugin_name)
            if lifecycle_state in (PluginLifecycleState.LOADING, PluginLifecycleState.INITIALIZING,
                                   PluginLifecycleState.INITIALIZED, PluginLifecycleState.ACTIVE):
                self._logger.debug(f"Plugin '{plugin_name}' is already being loaded",
                                   extra={'plugin': plugin_name, 'state': lifecycle_state.name})
                return True

            if plugin_name in self._disabled_plugins:
                self._logger.warning(f"Plugin '{plugin_name}' is disabled and cannot be loaded",
                                     extra={'plugin': plugin_name})
                return False

            set_plugin_state(plugin_name, PluginLifecycleState.LOADING)

        # Check dependencies and load them if necessary
        for dependency in plugin_info.dependencies:
            if dependency == 'core':
                continue

            with self._plugins_lock:
                if dependency not in self._plugins:
                    plugin_info.state = PluginState.FAILED
                    plugin_info.error = f"Dependency '{dependency}' not found"
                    set_plugin_state(plugin_name, PluginLifecycleState.FAILED)
                    self._logger.error(
                        f"Failed to load plugin '{plugin_name}': Dependency '{dependency}' not found",
                        extra={'plugin': plugin_name, 'dependency': dependency}
                    )
                    return False

                dependency_info = self._plugins[dependency]

            if dependency_info.state not in (PluginState.LOADED, PluginState.ACTIVE):
                if not self.load_plugin(dependency):
                    with self._plugins_lock:
                        plugin_info.state = PluginState.FAILED
                        plugin_info.error = f"Failed to load dependency '{dependency}'"
                        set_plugin_state(plugin_name, PluginLifecycleState.FAILED)

                    self._logger.error(
                        f"Failed to load plugin '{plugin_name}': Dependency '{dependency}' could not be loaded",
                        extra={'plugin': plugin_name, 'dependency': dependency}
                    )
                    return False

        try:
            # Execute pre-enable hook if available
            with self._plugins_lock:
                if plugin_info.manifest and PluginLifecycleHook.PRE_ENABLE in plugin_info.manifest.lifecycle_hooks:
                    try:
                        execute_hook(
                            hook=PluginLifecycleHook.PRE_ENABLE,
                            plugin_name=plugin_name,
                            manifest=plugin_info.manifest,
                            context={
                                'application_core': self._application_core,
                                'service_locator': self._service_locator
                            }
                        )
                    except Exception as e:
                        self._logger.warning(
                            f"Pre-enable hook failed for plugin '{plugin_name}': {str(e)}",
                            extra={'plugin': plugin_name, 'error': str(e)}
                        )

            # Load the plugin class and create an instance
            with self._plugins_lock:
                if plugin_info.manifest:
                    plugin_class = self._load_packaged_plugin(plugin_info)
                else:
                    plugin_class = self._get_plugin_class(plugin_info)

                plugin_info.instance = plugin_class()

            # Initialize the plugin using the service locator
            set_plugin_state(plugin_name, PluginLifecycleState.INITIALIZING)

            # Check if the plugin implements PluginInterface
            from qorzen.plugin_system.interface import PluginInterface
            if not isinstance(plugin_info.instance, PluginInterface):
                self._logger.warning(
                    f"Plugin '{plugin_name}' does not implement PluginInterface",
                    extra={'plugin': plugin_name}
                )

            # Initialize the plugin
            if hasattr(plugin_info.instance, 'initialize'):
                # Pass the service locator instead of individual managers
                plugin_info.instance.initialize(
                    service_locator=self._service_locator,
                    application_core=self._application_core
                )

            # Register plugin extensions
            with self._plugins_lock:
                if plugin_info.manifest:
                    from qorzen.plugin_system.extension import register_plugin_extensions
                    register_plugin_extensions(
                        plugin_name=plugin_name,
                        plugin_instance=plugin_info.instance,
                        manifest=plugin_info.manifest
                    )

            # Set up UI if needed
            with self._ui_lock:
                if self._ui_integration and hasattr(plugin_info.instance, 'on_ui_ready'):
                    self._thread_manager.submit_task(
                        self._setup_plugin_ui,
                        plugin_name,
                        plugin_info,
                        name=f'setup_ui_{plugin_name}',
                        submitter='plugin_manager',
                        execution_context=ThreadExecutionContext.MAIN_THREAD
                    )

            # Update plugin state
            with self._plugins_lock:
                plugin_info.state = PluginState.ACTIVE
                plugin_info.load_time = time.time()
                plugin_info.metadata['state'] = PluginState.ACTIVE.value

            set_plugin_state(plugin_name, PluginLifecycleState.INITIALIZED)

            # Execute post-enable hook if available
            with self._plugins_lock:
                if plugin_info.manifest and PluginLifecycleHook.POST_ENABLE in plugin_info.manifest.lifecycle_hooks:
                    try:
                        execute_hook(
                            hook=PluginLifecycleHook.POST_ENABLE,
                            plugin_name=plugin_name,
                            manifest=plugin_info.manifest,
                            plugin_instance=plugin_info.instance,
                            context={
                                'application_core': self._application_core,
                                'service_locator': self._service_locator
                            }
                        )
                    except Exception as e:
                        self._logger.warning(
                            f"Post-enable hook failed for plugin '{plugin_name}': {str(e)}",
                            extra={'plugin': plugin_name, 'error': str(e)}
                        )

            self._logger.info(
                f"Loaded plugin '{plugin_name}' v{plugin_info.version}",
                extra={'plugin': plugin_name, 'version': plugin_info.version}
            )

            # Publish plugin loaded event
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

            return True

        except Exception as e:
            # Handle errors during plugin loading
            with self._plugins_lock:
                plugin_info.state = PluginState.FAILED
                plugin_info.error = str(e)
                plugin_info.metadata['state'] = PluginState.FAILED.value

            set_plugin_state(plugin_name, PluginLifecycleState.FAILED)

            self._logger.error(
                f"Failed to load plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

            self._event_bus.publish(
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={'plugin_name': plugin_name, 'error': str(e)}
            )

            raise PluginError(
                f"Failed to load plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def _load_packaged_plugin(self, plugin_info: PluginInfo) -> Type:
        """Load a packaged plugin."""
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
            plugin_name: Name of the plugin to unload

        Returns:
            True if successfully unloaded, False otherwise

        Raises:
            PluginError: If the plugin cannot be unloaded
        """
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        with self._plugins_lock:
            if plugin_name not in self._plugins:
                raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

            plugin_info = self._plugins[plugin_name]
            lifecycle_state = get_plugin_state(plugin_name)

            if lifecycle_state == PluginLifecycleState.UI_READY:
                self._logger.warning(
                    f"Cannot unload plugin '{plugin_name}' during UI setup",
                    extra={'plugin': plugin_name}
                )
                return False

            if plugin_info.state not in (PluginState.LOADED, PluginState.ACTIVE):
                self._logger.debug(
                    f"Plugin '{plugin_name}' is not loaded",
                    extra={'plugin': plugin_name}
                )
                return True

        # Check for dependencies on this plugin
        for other_name, other_info in self._plugins.items():
            if (other_name != plugin_name and
                    plugin_name in other_info.dependencies and
                    (other_info.state in (PluginState.LOADED, PluginState.ACTIVE))):
                self._logger.warning(
                    f"Cannot unload plugin '{plugin_name}': Plugin '{other_name}' depends on it",
                    extra={'plugin': plugin_name, 'dependent': other_name}
                )
                return False

        try:
            # Set plugin state to disabling
            set_plugin_state(plugin_name, PluginLifecycleState.DISABLING)

            # Execute pre-disable hook if available
            with self._plugins_lock:
                if plugin_info.manifest and PluginLifecycleHook.PRE_DISABLE in plugin_info.manifest.lifecycle_hooks:
                    try:
                        execute_hook(
                            hook=PluginLifecycleHook.PRE_DISABLE,
                            plugin_name=plugin_name,
                            manifest=plugin_info.manifest,
                            plugin_instance=plugin_info.instance,
                            context={
                                'service_locator': self._service_locator,
                                'application_core': self._application_core
                            }
                        )
                    except Exception as e:
                        self._logger.warning(
                            f"Pre-disable hook failed for plugin '{plugin_name}': {str(e)}",
                            extra={'plugin': plugin_name, 'error': str(e)}
                        )

            # Unregister plugin extensions
            with self._plugins_lock:
                if plugin_info.manifest:
                    from qorzen.plugin_system.extension import unregister_plugin_extensions
                    unregister_plugin_extensions(plugin_name)

            # Shutdown the plugin
            if plugin_info.instance and hasattr(plugin_info.instance, 'shutdown'):
                if self._thread_manager.is_main_thread():
                    plugin_info.instance.shutdown()
                else:
                    self._thread_manager.execute_on_main_thread_sync(plugin_info.instance.shutdown)

            # Clean up UI components
            from qorzen.plugin_system.lifecycle import cleanup_ui
            cleanup_ui(plugin_name)

            # Update plugin state
            with self._plugins_lock:
                plugin_info.state = PluginState.INACTIVE
                plugin_info.metadata['state'] = PluginState.INACTIVE.value
                plugin_info.instance = None

            with self._ui_lock:
                if plugin_name in self._ui_setup_plugins:
                    self._ui_setup_plugins.remove(plugin_name)

            set_plugin_state(plugin_name, PluginLifecycleState.INACTIVE)

            self._logger.info(f"Unloaded plugin '{plugin_name}'", extra={'plugin': plugin_name})

            # Execute post-disable hook if available
            with self._plugins_lock:
                if plugin_info.manifest and PluginLifecycleHook.POST_DISABLE in plugin_info.manifest.lifecycle_hooks:
                    try:
                        execute_hook(
                            hook=PluginLifecycleHook.POST_DISABLE,
                            plugin_name=plugin_name,
                            manifest=plugin_info.manifest,
                            context={
                                'service_locator': self._service_locator,
                                'application_core': self._application_core
                            }
                        )
                    except Exception as e:
                        self._logger.warning(
                            f"Post-disable hook failed for plugin '{plugin_name}': {str(e)}",
                            extra={'plugin': plugin_name, 'error': str(e)}
                        )

            # Publish plugin unloaded event
            self._event_bus.publish(
                event_type=EventType.PLUGIN_UNLOADED,
                source='plugin_manager',
                payload={'plugin_name': plugin_name}
            )

            return True

        except Exception as e:
            # Handle errors during plugin unloading
            self._logger.error(
                f"Failed to unload plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

            set_plugin_state(plugin_name, PluginLifecycleState.FAILED)

            self._event_bus.publish(
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={'plugin_name': plugin_name, 'error': str(e)}
            )

            raise PluginError(
                f"Failed to unload plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin."""
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        try:
            if not self.unload_plugin(plugin_name):
                return False

            with self._plugins_lock:
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
                event_type=EventType.PLUGIN_ERROR,
                source='plugin_manager',
                payload={'plugin_name': plugin_name, 'error': str(e)}
            )

            raise PluginError(
                f"Failed to reload plugin '{plugin_name}': {str(e)}",
                plugin_name=plugin_name
            ) from e

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        with self._plugins_lock:
            if plugin_name not in self._plugins:
                raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

            if plugin_name in self._enabled_plugins:
                self._logger.debug(f"Plugin '{plugin_name}' is already enabled", extra={'plugin': plugin_name})
                return True

        # Update plugin installer
        if self.plugin_installer and self.plugin_installer.is_plugin_installed(plugin_name):
            self.plugin_installer.enable_plugin(plugin_name)

        # Update enabled/disabled lists
        if plugin_name in self._disabled_plugins:
            self._disabled_plugins.remove(plugin_name)

        if plugin_name not in self._enabled_plugins:
            self._enabled_plugins.append(plugin_name)

        # Update configuration
        self._is_updating_config = True
        try:
            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)
        finally:
            self._is_updating_config = False

        # Log and publish event
        self._logger.info(f"Enabled plugin '{plugin_name}'", extra={'plugin': plugin_name})

        self._event_bus.publish(
            event_type=EventType.PLUGIN_ENABLED,
            source='plugin_manager',
            payload={'plugin_name': plugin_name}
        )

        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        with self._plugins_lock:
            if plugin_name not in self._plugins:
                raise PluginError(f"Plugin '{plugin_name}' not found", plugin_name=plugin_name)

            if plugin_name in self._disabled_plugins:
                self._logger.debug(f"Plugin '{plugin_name}' is already disabled", extra={'plugin': plugin_name})
                return True

            plugin_info = self._plugins[plugin_name]

        # Unload if active
        if plugin_info.state in (PluginState.LOADED, PluginState.ACTIVE):
            if not self.unload_plugin(plugin_name):
                raise PluginError(f"Cannot disable plugin '{plugin_name}': Failed to unload it",
                                  plugin_name=plugin_name)

        # Update plugin installer
        if self.plugin_installer and self.plugin_installer.is_plugin_installed(plugin_name):
            self.plugin_installer.disable_plugin(plugin_name)

        # Update enabled/disabled lists
        if plugin_name in self._enabled_plugins:
            self._enabled_plugins.remove(plugin_name)

        if plugin_name not in self._disabled_plugins:
            self._disabled_plugins.append(plugin_name)

        # Update state
        with self._plugins_lock:
            plugin_info.state = PluginState.DISABLED
            plugin_info.metadata['state'] = PluginState.DISABLED.value

        # Update configuration
        self._is_updating_config = True
        try:
            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)
        finally:
            self._is_updating_config = False

        # Log and publish event
        self._logger.info(f"Disabled plugin '{plugin_name}'", extra={'plugin': plugin_name})

        self._event_bus.publish(
            event_type=EventType.PLUGIN_DISABLED,
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
        """Install a plugin package."""
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        try:
            # Install plugin
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

            # Create plugin info
            manifest = installed_plugin.manifest
            plugin_name = manifest.name
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

            # Store plugin info
            with self._plugins_lock:
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

            # Log installation
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

            # Load if enabled
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

    def uninstall_plugin(
            self,
            plugin_name: str,
            keep_data: bool = False,
            check_dependents: bool = True
    ) -> bool:
        """Uninstall a plugin."""
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized', plugin_name=plugin_name)

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        with self._plugins_lock:
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
            # Uninstall plugin
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
                # Remove from plugin registry
                with self._plugins_lock:
                    del self._plugins[plugin_name]

                # Update enabled/disabled lists
                if plugin_name in self._enabled_plugins:
                    self._enabled_plugins.remove(plugin_name)
                if plugin_name in self._disabled_plugins:
                    self._disabled_plugins.remove(plugin_name)

                # Update configuration
                self._config_manager.set('plugins.enabled', self._enabled_plugins)
                self._config_manager.set('plugins.disabled', self._disabled_plugins)

                # Log uninstallation
                self._logger.info(f"Uninstalled plugin '{plugin_name}'", extra={'plugin': plugin_name})

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
        """Update a plugin."""
        if not self._initialized:
            raise PluginError('Plugin Manager not initialized')

        if not self.plugin_installer:
            raise PluginError('Plugin installer not available')

        try:
            # Update plugin
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

            # Create new plugin info
            manifest = updated_plugin.manifest
            plugin_name = manifest.name
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

            # Store plugin info
            with self._plugins_lock:
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

            # Log update
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

            # Reload if active
            with self._plugins_lock:
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
        """Get the plugin class from a plugin info."""
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
        """Handle plugin installation event."""
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

    def _on_plugin_uninstall_event(self, event: Event) -> None:
        """Handle plugin uninstallation event."""
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

    def _on_plugin_enable_event(self, event: Event) -> None:
        payload = event.payload
        plugin_name = payload.get('plugin_name')
        if not plugin_name:
            self._logger.error('Invalid plugin enable event: Missing plugin_name', extra={'event_id': event.event_id})
            return

        if plugin_name in self._enabled_plugins:
            try:
                with self._plugins_lock:
                    plugin_info = self._plugins[plugin_name]
                    if plugin_info.state not in (PluginState.LOADED, PluginState.ACTIVE):
                        # Create a wrapper function that ignores the progress_reporter
                        def load_plugin_wrapper(plugin_name_to_load, progress_reporter=None):
                            return self.load_plugin(plugin_name_to_load)

                        # Load plugin asynchronously
                        self._thread_manager.submit_task(
                            load_plugin_wrapper,
                            plugin_name,
                            name=f'load_plugin_{plugin_name}',
                            submitter='plugin_manager',
                            priority=TaskPriority.HIGH,
                            execution_context=ThreadExecutionContext.WORKER_THREAD
                        )
            except Exception as e:
                self._logger.error(f"Failed to load already enabled plugin '{plugin_name}': {str(e)}",
                                   extra={'plugin': plugin_name, 'error': str(e)})
            return

        try:
            success = self.enable_plugin(plugin_name)
            if success:
                # Create a wrapper function that ignores the progress_reporter
                def load_plugin_wrapper(plugin_name_to_load, progress_reporter=None):
                    return self.load_plugin(plugin_name_to_load)

                # Load plugin asynchronously
                self._thread_manager.submit_task(
                    load_plugin_wrapper,
                    plugin_name,
                    name=f'load_plugin_{plugin_name}',
                    submitter='plugin_manager',
                    priority=TaskPriority.HIGH,
                    execution_context=ThreadExecutionContext.WORKER_THREAD
                )
        except Exception as e:
            self._logger.error(f"Failed to enable plugin '{plugin_name}': {str(e)}",
                               extra={'plugin': plugin_name, 'error': str(e)})

    def _on_plugin_disable_event(self, event: Event) -> None:
        """Handle plugin disable event."""
        payload = event.payload
        plugin_name = payload.get('plugin_name')

        if not plugin_name:
            self._logger.error(
                'Invalid plugin disable event: Missing plugin_name',
                extra={'event_id': event.event_id}
            )
            return

        if plugin_name in self._disabled_plugins:
            self._logger.debug(f"Plugin '{plugin_name}' is already disabled", extra={'plugin': plugin_name})
            return

        try:
            self.disable_plugin(plugin_name)
        except Exception as e:
            self._logger.error(
                f"Failed to disable plugin '{plugin_name}': {str(e)}",
                extra={'plugin': plugin_name, 'error': str(e)}
            )

    def _on_plugin_update_event(self, event: Event) -> None:
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
        if hasattr(self, '_is_updating_config') and self._is_updating_config:
            return

        if key == 'plugins.autoload':
            self._auto_load = value
            self._logger.info(f'Plugin autoload set to {value}', extra={'autoload': value})
        elif key == 'plugins.enabled':
            added = [p for p in value if p not in self._enabled_plugins]
            self._enabled_plugins = value
            self._logger.info(f'Updated enabled plugins list: {value}', extra={'enabled': value})
        elif key == 'plugins.disabled':
            self._disabled_plugins = value
            self._logger.info(f'Updated disabled plugins list: {value}', extra={'disabled': value})
        elif key == 'plugins.directory':
            self._logger.warning(
                'Changing plugin directory requires restart to take effect',
                extra={'directory': value}
            )

    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """Get all discovered plugins."""
        with self._plugins_lock:
            return self._plugins.copy()

    def shutdown(self) -> None:
        """Shut down the plugin manager."""
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Plugin Manager')

            # Get active plugins
            active_plugins = []
            with self._plugins_lock:
                active_plugins = [name for name, info in self._plugins.items()
                                  if info.state in (PluginState.LOADED, PluginState.ACTIVE)]

            # Sort by dependencies for safe shutdown
            if self.plugin_installer and hasattr(self.plugin_installer, 'get_loading_order'):
                try:
                    loading_order = self.plugin_installer.get_loading_order()
                    sorted_plugins = [name for name in reversed(loading_order) if name in active_plugins]

                    # Add any missing plugins
                    for name in active_plugins:
                        if name not in sorted_plugins:
                            sorted_plugins.append(name)
                except Exception as e:
                    self._logger.warning(
                        f'Error sorting plugins for shutdown: {str(e)}, falling back to legacy method'
                    )
                    sorted_plugins = self._sort_plugins_for_shutdown(active_plugins)
            else:
                sorted_plugins = self._sort_plugins_for_shutdown(active_plugins)

            # Unload plugins in reverse dependency order
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

            # Clean up
            get_lifecycle_manager().set_logger(None)
            self._config_manager.unregister_listener('plugins', self._on_config_changed)

            # Mark as uninitialized
            self._initialized = False
            self._healthy = False

            self._logger.info('Plugin Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Plugin Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down PluginManager: {str(e)}',
                manager_name=self.name
            ) from e

    def _sort_plugins_for_shutdown(self, plugin_names: List[str]) -> List[str]:
        """Sort plugins for shutdown based on dependencies."""
        sorted_plugins = []
        remaining_plugins = plugin_names.copy()

        # First include plugins that aren't dependencies for others
        for plugin_name in plugin_names:
            if not any((plugin_name in self._plugins[other].dependencies
                        for other in plugin_names if other != plugin_name)):
                sorted_plugins.append(plugin_name)
                remaining_plugins.remove(plugin_name)

        # Then add the rest
        sorted_plugins.extend(remaining_plugins)

        # Reverse for shutdown order (least dependent first)
        sorted_plugins.reverse()

        return sorted_plugins

    def status(self) -> Dict[str, Any]:
        """
        Get the current status of the plugin manager.

        Returns:
            Dictionary with status information
        """
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
                },
                'ui_integration': self._ui_integration is not None
            })

        return status