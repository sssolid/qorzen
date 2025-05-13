from __future__ import annotations
import asyncio
import importlib
import inspect
import os
import pathlib
import sys
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union, cast, Tuple

from qorzen.core.base import QorzenManager
from qorzen.core.error_handler import ErrorHandler, ErrorSeverity, create_error_boundary
from qorzen.utils.exceptions import PluginError, ManagerInitializationError, ManagerShutdownError


class PluginState(str, Enum):
    """States of a plugin."""
    DISCOVERED = "discovered"  # Plugin is discovered but not loaded
    LOADING = "loading"  # Plugin is being loaded
    ACTIVE = "active"  # Plugin is loaded and active
    INACTIVE = "inactive"  # Plugin is loaded but inactive
    FAILED = "failed"  # Plugin failed to load or crashed
    DISABLED = "disabled"  # Plugin is disabled by user
    INCOMPATIBLE = "incompatible"  # Plugin is incompatible with current system


@dataclass
class PluginManifest:
    """Plugin manifest information."""
    name: str
    display_name: str
    version: str
    description: str
    author: str
    logo_path: str
    homepage: Optional[str] = None
    license: Optional[str] = None
    min_core_version: Optional[str] = None
    max_core_version: Optional[str] = None
    entry_point: str = "plugin.py"
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    ui_integration: bool = True
    settings_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PluginManifest:
        """Create a manifest from a dictionary.

        Args:
            data: Dictionary with manifest data

        Returns:
            Plugin manifest
        """
        return cls(
            name=data.get('name', ''),
            display_name=data.get('display_name', ''),
            version=data.get('version', '0.1.0'),
            description=data.get('description', ''),
            author=data.get('author', 'Unknown'),
            homepage=data.get('homepage'),
            license=data.get('license'),
            min_core_version=data.get('min_core_version'),
            max_core_version=data.get('max_core_version'),
            entry_point=data.get('entry_point', 'plugin.py'),
            dependencies=data.get('dependencies', []),
            capabilities=data.get('capabilities', []),
            resources=data.get('resources', {}),
            ui_integration=data.get('ui_integration', True),
            settings_schema=data.get('settings_schema'),
            metadata=data.get('metadata', {})
        )

    @classmethod
    def load(cls, path: Union[str, pathlib.Path]) -> Optional[PluginManifest]:
        """Load a manifest from a file.

        Args:
            path: Path to the manifest file

        Returns:
            Plugin manifest or None if loading fails
        """
        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception:
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the manifest to a dictionary.

        Returns:
            Dictionary representation of the manifest
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'homepage': self.homepage,
            'license': self.license,
            'min_core_version': self.min_core_version,
            'max_core_version': self.max_core_version,
            'entry_point': self.entry_point,
            'dependencies': self.dependencies,
            'capabilities': self.capabilities,
            'resources': self.resources,
            'ui_integration': self.ui_integration,
            'settings_schema': self.settings_schema,
            'metadata': self.metadata
        }


@dataclass
class PluginInfo:
    """Information about a plugin."""
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    state: PluginState = PluginState.DISCOVERED
    path: Optional[str] = None
    manifest: Optional[PluginManifest] = None
    dependencies: List[str] = field(default_factory=list)
    error: Optional[str] = None
    load_time: Optional[float] = None
    instance: Optional[Any] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginManager(QorzenManager):
    """Asynchronous plugin manager.

    Manages the lifecycle of plugins, including discovery, loading,
    unloading, and dependency management.
    """

    def __init__(
            self,
            application_core: Any,
            config_manager: Any,
            logger_manager: Any,
            event_bus_manager: Any,
            file_manager: Any,
            task_manager: Any,
            plugin_isolation_manager: Any
    ) -> None:
        """Initialize the plugin manager.

        Args:
            application_core: The application core
            config_manager: Configuration manager
            logger_manager: Logger manager
            event_bus_manager: Event bus manager
            file_manager: File manager
            task_manager: Task manager
            plugin_isolation_manager: Plugin isolation manager
        """
        super().__init__(name='plugin_manager')
        self._application_core = application_core
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('plugin_manager')
        self._event_bus_manager = event_bus_manager
        self._file_manager = file_manager
        self._task_manager = task_manager
        self._plugin_isolation = plugin_isolation_manager

        # Plugin storage
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_instances: Dict[str, Any] = {}
        self._plugin_paths: Dict[str, str] = {}
        self._plugins_lock = asyncio.Lock()

        # Configuration
        self._plugin_dir: Optional[pathlib.Path] = None
        self._auto_load = True
        self._enabled_plugins: List[str] = []
        self._disabled_plugins: List[str] = []
        self._entry_point_group = 'qorzen.plugins'

        # Error handling
        self._error_handler: Optional[ErrorHandler] = None

        # UI integration
        self._ui_integration = None
        self._ui_ready = asyncio.Event()
        self._ui_plugins: Set[str] = set()

    async def initialize(self) -> None:
        """Initialize the plugin manager.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            self._logger.info('Initializing plugin manager')

            # Setup error handler
            if hasattr(self._event_bus_manager, 'error_handler'):
                self._error_handler = self._event_bus_manager.error_handler
                self._error_handler.initialize()

            # Load configuration
            plugin_config = await self._config_manager.get('plugins', {})
            plugin_dir = plugin_config.get('directory', 'plugins')
            self._plugin_dir = pathlib.Path(plugin_dir)
            self._auto_load = plugin_config.get('autoload', True)
            self._enabled_plugins = plugin_config.get('enabled', [])
            self._disabled_plugins = plugin_config.get('disabled', [])

            # Create plugin directory if it doesn't exist
            os.makedirs(self._plugin_dir, exist_ok=True)

            # Register event listeners
            await self._event_bus_manager.subscribe(
                event_type='plugin/installed',
                callback=self._on_plugin_installed,
                subscriber_id='plugin_manager'
            )

            await self._event_bus_manager.subscribe(
                event_type='plugin/uninstalled',
                callback=self._on_plugin_uninstalled,
                subscriber_id='plugin_manager'
            )

            await self._event_bus_manager.subscribe(
                event_type='plugin/enabled',
                callback=self._on_plugin_enabled,
                subscriber_id='plugin_manager'
            )

            await self._event_bus_manager.subscribe(
                event_type='plugin/disabled',
                callback=self._on_plugin_disabled,
                subscriber_id='plugin_manager'
            )

            await self._event_bus_manager.subscribe(
                event_type='ui/ready',
                callback=self._on_ui_ready,
                subscriber_id='plugin_manager'
            )

            # Register configuration listener
            await self._config_manager.register_listener('plugins', self._on_config_changed)

            # Discover plugins
            await self._discover_plugins()

            self._initialized = True
            self._healthy = True

            # Load enabled plugins if autoload is enabled
            if self._auto_load:
                asyncio.create_task(self._load_enabled_plugins())

            self._logger.info(f'Plugin manager initialized with {len(self._plugins)} plugins discovered')

            # Publish initialization event
            await self._event_bus_manager.publish(
                event_type='plugin_manager/initialized',
                source='plugin_manager',
                payload={'plugin_count': len(self._plugins)}
            )

        except Exception as e:
            self._logger.error(f'Failed to initialize plugin manager: {str(e)}', exc_info=True)
            raise ManagerInitializationError(
                f'Failed to initialize PluginManager: {str(e)}',
                manager_name=self.name
            ) from e

    async def _discover_plugins(self) -> None:
        """Discover available plugins.

        This includes plugins in the plugin directory, entry points,
        and installed packages.
        """
        self._logger.debug('Discovering plugins')

        # Discover entry point plugins
        await self._discover_entry_point_plugins()

        # Discover directory plugins
        await self._discover_directory_plugins()

        # Discover installed plugins
        await self._discover_installed_plugins()

    async def _discover_entry_point_plugins(self) -> None:
        """Discover plugins from entry points."""
        try:
            import importlib.metadata
            entry_points = importlib.metadata.entry_points(group=self._entry_point_group)

            for entry_point in entry_points:
                plugin_id = f"entry_{entry_point.name}"

                try:
                    plugin_class = entry_point.load()
                    plugin_info = await self._extract_plugin_metadata(
                        plugin_class=plugin_class,
                        default_name=entry_point.name,
                        plugin_id=plugin_id,
                        metadata={'entry_point': entry_point.name}
                    )

                    async with self._plugins_lock:
                        self._plugins[plugin_id] = plugin_info

                    self._logger.debug(
                        f"Discovered plugin '{plugin_info.name}' from entry point",
                        extra={'plugin_id': plugin_id, 'version': plugin_info.version}
                    )
                except Exception as e:
                    self._logger.error(
                        f"Failed to discover plugin from entry point '{entry_point.name}': {str(e)}",
                        extra={'entry_point': entry_point.name}
                    )
        except Exception as e:
            self._logger.error(f'Failed to discover entry point plugins: {str(e)}')

    async def _discover_directory_plugins(self) -> None:
        """Discover plugins from the plugin directory."""
        if not self._plugin_dir or not self._plugin_dir.exists():
            self._logger.warning(f'Plugin directory does not exist: {self._plugin_dir}')
            return

        # Add plugin directory to path if not already
        plugin_dir_str = str(self._plugin_dir.absolute())
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)

        try:
            # Loop through each directory in the plugin directory
            for item in self._plugin_dir.iterdir():
                if not item.is_dir():
                    continue

                if item.name.startswith('.') or item.name in ('__pycache__', 'backups'):
                    continue

                # Check for manifest file
                manifest_file = item / 'manifest.json'
                if manifest_file.exists():
                    await self._discover_plugin_from_manifest(item)
                else:
                    # Try to discover from module
                    await self._discover_plugin_from_module(item)
        except Exception as e:
            self._logger.error(f'Failed to discover directory plugins: {str(e)}', exc_info=True)

    async def _discover_plugin_from_manifest(self, plugin_dir: pathlib.Path) -> None:
        """Discover a plugin from a manifest file.

        Args:
            plugin_dir: Directory containing the plugin
        """
        manifest_file = plugin_dir / 'manifest.json'
        try:
            manifest = PluginManifest.load(manifest_file)
            if not manifest:
                self._logger.warning(f'Failed to load manifest from {manifest_file}')
                return

            plugin_id = f"manifest_{manifest.name}"

            # Look for entry point module
            entry_point = manifest.entry_point
            entry_path = plugin_dir / entry_point

            if not entry_path.exists() and '.' in entry_point:
                # Try as a module path instead of a file path
                module_name = f"{plugin_dir.name}.{entry_point}"
                try:
                    importlib.import_module(module_name)
                    # If we got here, the module exists
                except ImportError:
                    self._logger.warning(
                        f"Failed to import module {module_name} for plugin {manifest.name}",
                        extra={'plugin': manifest.name, 'module': module_name}
                    )
                    return

            # Create plugin info
            plugin_info = PluginInfo(
                plugin_id=plugin_id,
                name=manifest.name,
                version=manifest.version,
                description=manifest.description,
                author=manifest.author,
                state=PluginState.DISCOVERED,
                path=str(plugin_dir),
                manifest=manifest,
                dependencies=manifest.dependencies,
                capabilities=manifest.capabilities,
                metadata={
                    'manifest': True,
                    'display_name': manifest.display_name,
                    'license': manifest.license,
                    'homepage': manifest.homepage,
                    'entry_point': manifest.entry_point,
                    'ui_integration': manifest.ui_integration
                }
            )

            # Store plugin info
            async with self._plugins_lock:
                self._plugins[plugin_id] = plugin_info
                self._plugin_paths[plugin_id] = str(plugin_dir)

            self._logger.debug(
                f"Discovered plugin '{plugin_info.name}' from manifest",
                extra={
                    'plugin_id': plugin_id,
                    'version': plugin_info.version,
                    'path': str(plugin_dir)
                }
            )
        except Exception as e:
            self._logger.error(
                f"Failed to discover plugin from manifest in {plugin_dir.name}: {str(e)}",
                extra={'directory': str(plugin_dir)}
            )

    async def _discover_plugin_from_module(self, plugin_dir: pathlib.Path) -> None:
        """Discover a plugin from a Python module.

        Args:
            plugin_dir: Directory containing the plugin
        """
        init_file = plugin_dir / '__init__.py'
        plugin_file = plugin_dir / 'plugin.py'

        if not init_file.exists() and not plugin_file.exists():
            return

        try:
            module_name = plugin_dir.name

            if init_file.exists():
                module = importlib.import_module(module_name)
            elif plugin_file.exists():
                spec = importlib.util.spec_from_file_location(
                    f'{module_name}.plugin',
                    plugin_file
                )
                if not spec or not spec.loader:
                    return
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                return

            # Find the plugin class
            plugin_class = None
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, 'name') and hasattr(obj, 'version') and hasattr(obj, 'description'):
                    plugin_class = obj
                    break

            if not plugin_class:
                return

            plugin_id = f"module_{module_name}"

            # Create plugin info from class attributes
            plugin_info = await self._extract_plugin_metadata(
                plugin_class=plugin_class,
                default_name=module_name,
                plugin_id=plugin_id,
                path=str(plugin_dir)
            )

            # Store plugin info
            async with self._plugins_lock:
                self._plugins[plugin_id] = plugin_info
                self._plugin_paths[plugin_id] = str(plugin_dir)

            self._logger.debug(
                f"Discovered plugin '{plugin_info.name}' from module",
                extra={
                    'plugin_id': plugin_id,
                    'version': plugin_info.version,
                    'path': str(plugin_dir)
                }
            )
        except Exception as e:
            self._logger.error(
                f"Failed to discover plugin from module in {plugin_dir.name}: {str(e)}",
                extra={'directory': str(plugin_dir)}
            )

    async def _discover_installed_plugins(self) -> None:
        """Discover plugins that have been installed via packages."""
        # This is a placeholder for future package-based plugin support
        pass

    async def _extract_plugin_metadata(
            self,
            plugin_class: Type,
            default_name: str,
            plugin_id: str,
            path: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> PluginInfo:
        """Extract metadata from a plugin class.

        Args:
            plugin_class: The plugin class
            default_name: Default name if not specified in class
            plugin_id: ID for the plugin
            path: Optional path to the plugin
            metadata: Optional additional metadata

        Returns:
            Plugin information
        """
        name = getattr(plugin_class, 'name', default_name)
        version = getattr(plugin_class, 'version', '0.1.0')
        description = getattr(plugin_class, 'description', 'No description')
        author = getattr(plugin_class, 'author', 'Unknown')
        dependencies = getattr(plugin_class, 'dependencies', [])
        capabilities = getattr(plugin_class, 'capabilities', [])

        # Build metadata
        plugin_metadata = {
            'class': plugin_class.__name__,
            'module': plugin_class.__module__
        }

        if metadata:
            plugin_metadata.update(metadata)

        # Create plugin info
        plugin_info = PluginInfo(
            plugin_id=plugin_id,
            name=name,
            version=version,
            description=description,
            author=author,
            state=PluginState.DISCOVERED,
            path=path,
            dependencies=dependencies,
            capabilities=capabilities,
            metadata=plugin_metadata
        )

        return plugin_info

    async def _load_enabled_plugins(self) -> None:
        """Load all enabled plugins."""
        self._logger.info('Loading enabled plugins')

        # Get the list of enabled plugins
        enabled_plugins = []
        async with self._plugins_lock:
            for plugin_id, plugin_info in self._plugins.items():
                if self._is_plugin_enabled(plugin_info.name):
                    enabled_plugins.append((plugin_id, plugin_info))

        # Sort plugins by dependencies
        sorted_plugins = await self._sort_plugins_by_dependencies(enabled_plugins)

        # Load plugins in order
        for plugin_id, _ in sorted_plugins:
            try:
                await self.load_plugin(plugin_id)
            except Exception as e:
                self._logger.error(
                    f"Failed to load plugin {plugin_id}: {str(e)}",
                    extra={'plugin_id': plugin_id, 'error': str(e)}
                )

    async def _sort_plugins_by_dependencies(
            self,
            plugins: List[Tuple[str, PluginInfo]]
    ) -> List[Tuple[str, PluginInfo]]:
        """Sort plugins by dependencies using topological sort.

        Args:
            plugins: List of (plugin_id, plugin_info) tuples

        Returns:
            Sorted list of (plugin_id, plugin_info) tuples
        """
        # Build dependency graph
        graph = {}
        for plugin_id, plugin_info in plugins:
            graph[plugin_id] = set()

            # Add dependencies
            for dep in plugin_info.dependencies:
                # Find the plugin ID for this dependency name
                dep_id = None
                for pid, pinfo in plugins:
                    if pinfo.name == dep:
                        dep_id = pid
                        break

                if dep_id:
                    graph[plugin_id].add(dep_id)

        # Perform topological sort
        result = []
        temp_marks = set()
        perm_marks = set()

        def visit(node):
            if node in perm_marks:
                return
            if node in temp_marks:
                # Circular dependency detected
                self._logger.warning(f"Circular dependency detected involving {node}")
                return

            temp_marks.add(node)

            # Visit dependencies
            for dep in graph.get(node, set()):
                visit(dep)

            temp_marks.remove(node)
            perm_marks.add(node)

            # Add to result
            for plugin_id, plugin_info in plugins:
                if plugin_id == node:
                    result.append((plugin_id, plugin_info))
                    break

        # Visit all nodes
        for plugin_id, _ in plugins:
            if plugin_id not in perm_marks:
                visit(plugin_id)

        return result

    async def load_plugin(self, plugin_id: str) -> bool:
        """Load a plugin.

        Args:
            plugin_id: ID of the plugin to load

        Returns:
            True if the plugin was loaded successfully, False otherwise

        Raises:
            PluginError: If loading fails
        """
        if not self._initialized:
            raise PluginError('Plugin manager not initialized')

        async with self._plugins_lock:
            if plugin_id not in self._plugins:
                raise PluginError(f"Plugin '{plugin_id}' not found")

            plugin_info = self._plugins[plugin_id]

            # Check if already loaded
            if plugin_info.state in (PluginState.ACTIVE, PluginState.LOADING):
                self._logger.debug(f"Plugin '{plugin_id}' is already loaded or loading")
                return True

            # Check if disabled
            if self._is_plugin_disabled(plugin_info.name):
                self._logger.info(f"Plugin '{plugin_id}' is disabled, skipping load")
                plugin_info.state = PluginState.DISABLED
                return False

            # Mark as loading
            plugin_info.state = PluginState.LOADING

        # Create error boundary for plugin loading
        error_boundary = create_error_boundary(
            source='plugin_loading',
            plugin_id=plugin_id
        ) if self._error_handler else None

        try:
            # Load dependencies first
            await self._load_plugin_dependencies(plugin_id)

            # Load the plugin
            if plugin_info.manifest:
                success = await self._load_plugin_from_manifest(plugin_id)
            else:
                success = await self._load_plugin_from_module(plugin_id)

            if not success:
                return False

            # Mark as active
            async with self._plugins_lock:
                plugin_info.state = PluginState.ACTIVE
                plugin_info.load_time = time.time()

            # Publish plugin loaded event
            await self._event_bus_manager.publish(
                event_type='plugin/loaded',
                source='plugin_manager',
                payload={
                    'plugin_id': plugin_id,
                    'name': plugin_info.name,
                    'version': plugin_info.version,
                    'description': plugin_info.description,
                    'author': plugin_info.author
                }
            )

            self._logger.info(
                f"Loaded plugin '{plugin_info.name}' v{plugin_info.version}",
                extra={'plugin_id': plugin_id}
            )

            return True
        except Exception as e:
            # Mark as failed
            async with self._plugins_lock:
                plugin_info.state = PluginState.FAILED
                plugin_info.error = str(e)

            self._logger.error(
                f"Failed to load plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)},
                exc_info=True
            )

            # Publish plugin error event
            await self._event_bus_manager.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={
                    'plugin_id': plugin_id,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )

            raise PluginError(f"Failed to load plugin '{plugin_id}': {str(e)}") from e

    async def _load_plugin_dependencies(self, plugin_id: str) -> None:
        """Load all dependencies for a plugin.

        Args:
            plugin_id: ID of the plugin

        Raises:
            PluginError: If a dependency cannot be loaded
        """
        async with self._plugins_lock:
            plugin_info = self._plugins[plugin_id]
            dependencies = plugin_info.dependencies

        # Load each dependency
        for dep_name in dependencies:
            if dep_name == 'core':
                # Core dependency is always satisfied
                continue

            # Find the plugin ID for this dependency
            dep_id = None
            async with self._plugins_lock:
                for pid, pinfo in self._plugins.items():
                    if pinfo.name == dep_name:
                        dep_id = pid
                        break

            if not dep_id:
                raise PluginError(
                    f"Dependency '{dep_name}' not found for plugin '{plugin_id}'"
                )

            # Check if already loaded
            async with self._plugins_lock:
                dep_info = self._plugins[dep_id]
                if dep_info.state == PluginState.ACTIVE:
                    continue

            # Load the dependency
            success = await self.load_plugin(dep_id)
            if not success:
                raise PluginError(
                    f"Failed to load dependency '{dep_name}' for plugin '{plugin_id}'"
                )

    async def _load_plugin_from_manifest(self, plugin_id: str) -> bool:
        """Load a plugin from a manifest file.

        Args:
            plugin_id: ID of the plugin

        Returns:
            True if the plugin was loaded successfully, False otherwise

        Raises:
            PluginError: If loading fails
        """
        async with self._plugins_lock:
            plugin_info = self._plugins[plugin_id]
            manifest = plugin_info.manifest
            plugin_path = plugin_info.path

        if not manifest or not plugin_path:
            raise PluginError(f"Plugin '{plugin_id}' has no manifest or path")

        # Check path exists
        plugin_dir = pathlib.Path(plugin_path)
        if not plugin_dir.exists():
            raise PluginError(f"Plugin directory not found: {plugin_path}")

        # Get entry point module
        entry_point = manifest.entry_point
        entry_path = None

        # Check if entry point is a file path or module path
        if entry_point.endswith('.py'):
            entry_path = plugin_dir / entry_point
            if not entry_path.exists():
                raise PluginError(f"Entry point file not found: {entry_point}")

            # Import from file
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_id}",
                entry_path
            )
            if not spec or not spec.loader:
                raise PluginError(f"Failed to create module spec for {entry_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            # Import as module
            if '.' in entry_point:
                # Relative to plugin dir
                module_name = f"{plugin_dir.name}.{entry_point}"
            else:
                # Direct module name
                module_name = entry_point

            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                raise PluginError(f"Failed to import plugin module: {str(e)}") from e

        # Find the plugin class
        plugin_class = None
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, "name") and hasattr(obj, "version"):
                plugin_class = obj
                break

        if not plugin_class:
            raise PluginError(f"No plugin class found in {entry_point}")

        # Create an instance
        plugin_instance = plugin_class()

        # Initialize the plugin
        if hasattr(plugin_instance, "initialize"):
            await self._initialize_plugin(plugin_instance, plugin_id)

        # Store the instance
        async with self._plugins_lock:
            self._plugin_instances[plugin_id] = plugin_instance

        # Set up UI integration if needed
        if manifest.ui_integration and hasattr(plugin_instance, "setup_ui"):
            # Setup UI if it's ready, otherwise wait for UI ready event
            if self._ui_ready.is_set():
                await self._setup_plugin_ui(plugin_id)
            else:
                self._ui_plugins.add(plugin_id)

        return True

    async def _load_plugin_from_module(self, plugin_id: str) -> bool:
        """Load a plugin from a Python module.

        Args:
            plugin_id: ID of the plugin

        Returns:
            True if the plugin was loaded successfully, False otherwise

        Raises:
            PluginError: If loading fails
        """
        async with self._plugins_lock:
            plugin_info = self._plugins[plugin_id]

        # Get the plugin class
        module_name = plugin_info.metadata.get('module')
        class_name = plugin_info.metadata.get('class')

        if not module_name or not class_name:
            raise PluginError(f"Plugin '{plugin_id}' has invalid metadata")

        try:
            # Import the module
            module = importlib.import_module(module_name)

            # Get the plugin class
            plugin_class = getattr(module, class_name)

            # Create an instance
            plugin_instance = plugin_class()

            # Initialize the plugin
            if hasattr(plugin_instance, "initialize"):
                await self._initialize_plugin(plugin_instance, plugin_id)

            # Store the instance
            async with self._plugins_lock:
                self._plugin_instances[plugin_id] = plugin_instance

            # Set up UI integration if needed
            if hasattr(plugin_instance, "setup_ui"):
                # Setup UI if it's ready, otherwise wait for UI ready event
                if self._ui_ready.is_set():
                    await self._setup_plugin_ui(plugin_id)
                else:
                    self._ui_plugins.add(plugin_id)

            return True
        except Exception as e:
            raise PluginError(
                f"Failed to load plugin '{plugin_id}' from module: {str(e)}"
            ) from e

    async def _initialize_plugin(self, plugin_instance: Any, plugin_id: str) -> None:
        """Initialize a plugin.

        Args:
            plugin_instance: Plugin instance
            plugin_id: ID of the plugin

        Raises:
            PluginError: If initialization fails
        """
        try:
            # Check for async or sync initialize method
            initialize_method = getattr(plugin_instance, "initialize")

            # Create an error boundary for the initialize method
            error_boundary = create_error_boundary(
                source='plugin_initialization',
                plugin_id=plugin_id
            ) if self._error_handler else None

            if error_boundary:
                # Initialize with error boundary
                if asyncio.iscoroutinefunction(initialize_method):
                    await error_boundary.run(
                        initialize_method,
                        self._application_core,
                        severity=ErrorSeverity.HIGH
                    )
                else:
                    await error_boundary.run(
                        lambda: initialize_method(self._application_core),
                        severity=ErrorSeverity.HIGH
                    )
            else:
                # Initialize without error boundary
                if asyncio.iscoroutinefunction(initialize_method):
                    await initialize_method(self._application_core)
                else:
                    initialize_method(self._application_core)
        except Exception as e:
            raise PluginError(
                f"Failed to initialize plugin '{plugin_id}': {str(e)}"
            ) from e

    async def _setup_plugin_ui(self, plugin_id: str) -> None:
        """Set up UI integration for a plugin.

        Args:
            plugin_id: ID of the plugin

        Raises:
            PluginError: If UI setup fails
        """
        if not self._ui_integration:
            return

        async with self._plugins_lock:
            if plugin_id not in self._plugin_instances:
                return

            plugin_instance = self._plugin_instances[plugin_id]

            if not hasattr(plugin_instance, "setup_ui"):
                return

        # Create an error boundary for the setup_ui method
        error_boundary = create_error_boundary(
            source='plugin_ui_setup',
            plugin_id=plugin_id
        ) if self._error_handler else None

        try:
            setup_ui_method = getattr(plugin_instance, "setup_ui")

            if error_boundary:
                # Setup UI with error boundary
                if asyncio.iscoroutinefunction(setup_ui_method):
                    await error_boundary.run(
                        setup_ui_method,
                        self._ui_integration,
                        severity=ErrorSeverity.MEDIUM
                    )
                else:
                    await error_boundary.run(
                        lambda: setup_ui_method(self._ui_integration),
                        severity=ErrorSeverity.MEDIUM
                    )
            else:
                # Setup UI without error boundary
                if asyncio.iscoroutinefunction(setup_ui_method):
                    await setup_ui_method(self._ui_integration)
                else:
                    setup_ui_method(self._ui_integration)
        except Exception as e:
            self._logger.error(
                f"Failed to set up UI for plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)},
                exc_info=True
            )

            # Don't re-raise, UI setup errors shouldn't prevent plugin loading

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_id: ID of the plugin to unload

        Returns:
            True if the plugin was unloaded successfully, False otherwise

        Raises:
            PluginError: If unloading fails
        """
        if not self._initialized:
            raise PluginError('Plugin manager not initialized')

        async with self._plugins_lock:
            if plugin_id not in self._plugins:
                raise PluginError(f"Plugin '{plugin_id}' not found")

            plugin_info = self._plugins[plugin_id]

            # Check if already unloaded
            if plugin_info.state not in (PluginState.ACTIVE, PluginState.LOADING):
                self._logger.debug(f"Plugin '{plugin_id}' is not loaded")
                return True

            # Check if it's a dependency for other plugins
            for other_id, other_info in self._plugins.items():
                if other_id != plugin_id and other_info.state == PluginState.ACTIVE:
                    if plugin_info.name in other_info.dependencies:
                        raise PluginError(
                            f"Cannot unload plugin '{plugin_id}' because it's a "
                            f"dependency for '{other_id}'"
                        )

        # Create error boundary for plugin unloading
        error_boundary = create_error_boundary(
            source='plugin_unloading',
            plugin_id=plugin_id
        ) if self._error_handler else None

        try:
            # Get plugin instance
            plugin_instance = None
            async with self._plugins_lock:
                if plugin_id in self._plugin_instances:
                    plugin_instance = self._plugin_instances[plugin_id]

            # Call shutdown method if available
            if plugin_instance and hasattr(plugin_instance, "shutdown"):
                shutdown_method = getattr(plugin_instance, "shutdown")

                if error_boundary:
                    # Shutdown with error boundary
                    if asyncio.iscoroutinefunction(shutdown_method):
                        await error_boundary.run(
                            shutdown_method,
                            severity=ErrorSeverity.MEDIUM
                        )
                    else:
                        await error_boundary.run(
                            shutdown_method,
                            severity=ErrorSeverity.MEDIUM
                        )
                else:
                    # Shutdown without error boundary
                    if asyncio.iscoroutinefunction(shutdown_method):
                        await shutdown_method()
                    else:
                        shutdown_method()

            # Clean up UI integration
            if self._ui_integration and plugin_id in self._ui_plugins:
                await self._cleanup_plugin_ui(plugin_id)

            # Remove plugin instance
            async with self._plugins_lock:
                if plugin_id in self._plugin_instances:
                    del self._plugin_instances[plugin_id]

                plugin_info.state = PluginState.INACTIVE
                plugin_info.instance = None

            # Publish plugin unloaded event
            await self._event_bus_manager.publish(
                event_type='plugin/unloaded',
                source='plugin_manager',
                payload={'plugin_id': plugin_id, 'name': plugin_info.name}
            )

            self._logger.info(
                f"Unloaded plugin '{plugin_info.name}'",
                extra={'plugin_id': plugin_id}
            )

            return True
        except Exception as e:
            self._logger.error(
                f"Failed to unload plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)},
                exc_info=True
            )

            # Publish plugin error event
            await self._event_bus_manager.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={
                    'plugin_id': plugin_id,
                    'error': f"Failed to unload plugin: {str(e)}",
                    'traceback': traceback.format_exc()
                }
            )

            raise PluginError(f"Failed to unload plugin '{plugin_id}': {str(e)}") from e

    async def _cleanup_plugin_ui(self, plugin_id: str) -> None:
        """Clean up UI integration for a plugin.

        Args:
            plugin_id: ID of the plugin
        """
        if not self._ui_integration:
            return

        try:
            # Remove plugin from UI plugins set
            self._ui_plugins.discard(plugin_id)

            # Clear UI elements for plugin
            if hasattr(self._ui_integration, "clear_plugin_elements"):
                await self._ui_integration.clear_plugin_elements(plugin_id)
        except Exception as e:
            self._logger.error(
                f"Error cleaning up UI for plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)}
            )

    async def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin.

        Args:
            plugin_id: ID of the plugin to enable

        Returns:
            True if the plugin was enabled, False otherwise

        Raises:
            PluginError: If enabling fails
        """
        if not self._initialized:
            raise PluginError('Plugin manager not initialized')

        async with self._plugins_lock:
            if plugin_id not in self._plugins:
                raise PluginError(f"Plugin '{plugin_id}' not found")

            plugin_info = self._plugins[plugin_id]

            # Check if already enabled
            if self._is_plugin_enabled(plugin_info.name):
                self._logger.debug(f"Plugin '{plugin_id}' is already enabled")
                return True

            # Add to enabled plugins list
            plugin_name = plugin_info.name
            if plugin_name not in self._enabled_plugins:
                self._enabled_plugins.append(plugin_name)

            # Remove from disabled plugins list
            if plugin_name in self._disabled_plugins:
                self._disabled_plugins.remove(plugin_name)

            # Update configuration
            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)

            # Update plugin state
            if plugin_info.state == PluginState.DISABLED:
                plugin_info.state = PluginState.DISCOVERED

        # Publish plugin enabled event
        await self._event_bus_manager.publish(
            event_type='plugin/enabled',
            source='plugin_manager',
            payload={'plugin_id': plugin_id, 'name': plugin_info.name}
        )

        self._logger.info(
            f"Enabled plugin '{plugin_info.name}'",
            extra={'plugin_id': plugin_id}
        )

        # Load the plugin if auto-load is enabled
        if self._auto_load:
            asyncio.create_task(self.load_plugin(plugin_id))

        return True

    async def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_id: ID of the plugin to disable

        Returns:
            True if the plugin was disabled, False otherwise

        Raises:
            PluginError: If disabling fails
        """
        if not self._initialized:
            raise PluginError('Plugin manager not initialized')

        async with self._plugins_lock:
            if plugin_id not in self._plugins:
                raise PluginError(f"Plugin '{plugin_id}' not found")

            plugin_info = self._plugins[plugin_id]

            # Check if already disabled
            if self._is_plugin_disabled(plugin_info.name):
                self._logger.debug(f"Plugin '{plugin_id}' is already disabled")
                return True

            # Unload the plugin if it's active
            if plugin_info.state in (PluginState.ACTIVE, PluginState.LOADING):
                try:
                    await self.unload_plugin(plugin_id)
                except Exception as e:
                    self._logger.error(
                        f"Error unloading plugin '{plugin_id}' during disable: {str(e)}",
                        extra={'plugin_id': plugin_id, 'error': str(e)}
                    )
                    # Continue with disabling

            # Remove from enabled plugins list
            plugin_name = plugin_info.name
            if plugin_name in self._enabled_plugins:
                self._enabled_plugins.remove(plugin_name)

            # Add to disabled plugins list
            if plugin_name not in self._disabled_plugins:
                self._disabled_plugins.append(plugin_name)

            # Update configuration
            self._config_manager.set('plugins.enabled', self._enabled_plugins)
            self._config_manager.set('plugins.disabled', self._disabled_plugins)

            # Update plugin state
            plugin_info.state = PluginState.DISABLED

        # Publish plugin disabled event
        await self._event_bus_manager.publish(
            event_type='plugin/disabled',
            source='plugin_manager',
            payload={'plugin_id': plugin_id, 'name': plugin_info.name}
        )

        self._logger.info(
            f"Disabled plugin '{plugin_info.name}'",
            extra={'plugin_id': plugin_id}
        )

        return True

    async def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin.

        Args:
            plugin_id: ID of the plugin to reload

        Returns:
            True if the plugin was reloaded successfully, False otherwise

        Raises:
            PluginError: If reloading fails
        """
        if not self._initialized:
            raise PluginError('Plugin manager not initialized')

        try:
            # Unload the plugin
            await self.unload_plugin(plugin_id)

            # Reload any modules
            async with self._plugins_lock:
                plugin_info = self._plugins[plugin_id]
                module_name = plugin_info.metadata.get('module')

                if module_name:
                    # Reload the module
                    if module_name in sys.modules:
                        module = sys.modules[module_name]
                        importlib.reload(module)

                        # Reload parent module if it exists
                        if '.' in module_name:
                            parent_name = module_name.split('.')[0]
                            if parent_name in sys.modules:
                                importlib.reload(sys.modules[parent_name])

            # Load the plugin
            return await self.load_plugin(plugin_id)
        except Exception as e:
            self._logger.error(
                f"Failed to reload plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)},
                exc_info=True
            )

            # Publish plugin error event
            await self._event_bus_manager.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={
                    'plugin_id': plugin_id,
                    'error': f"Failed to reload plugin: {str(e)}",
                    'traceback': traceback.format_exc()
                }
            )

            raise PluginError(f"Failed to reload plugin '{plugin_id}': {str(e)}") from e

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

        return self._auto_load

    def _is_plugin_disabled(self, plugin_name: str) -> bool:
        """Check if a plugin is disabled.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if the plugin is disabled, False otherwise
        """
        return plugin_name in self._disabled_plugins

    async def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: Configuration key
            value: New value
        """
        if key == 'plugins.autoload':
            self._auto_load = value
            self._logger.info(f'Plugin autoload set to {value}')
        elif key == 'plugins.enabled':
            self._enabled_plugins = value
            self._logger.debug(f'Updated enabled plugins list: {value}')
        elif key == 'plugins.disabled':
            self._disabled_plugins = value
            self._logger.debug(f'Updated disabled plugins list: {value}')
        elif key == 'plugins.directory':
            self._logger.warning('Changing plugin directory requires restart to take effect')

    async def _on_ui_ready(self, event: Any) -> None:
        """Handle UI ready event.

        Args:
            event: Event data
        """
        self._logger.debug('Received UI ready event')

        # Get UI integration
        ui_integration = event.payload.get('ui_integration')
        if not ui_integration:
            return

        self._ui_integration = ui_integration

        # Signal UI ready
        self._ui_ready.set()

        # Set up UI for pending plugins
        for plugin_id in list(self._ui_plugins):
            asyncio.create_task(self._setup_plugin_ui(plugin_id))

    async def _on_plugin_installed(self, event: Any) -> None:
        """Handle plugin installed event.

        Args:
            event: Event data
        """
        plugin_id = event.payload.get('plugin_id')
        plugin_path = event.payload.get('path')

        if not plugin_id or not plugin_path:
            return

        self._logger.debug(f'Handling plugin installed event for {plugin_id}')

        # Refresh plugin discovery
        await self._discover_plugins()

        # Enable and load the plugin if requested
        auto_enable = event.payload.get('auto_enable', True)
        if auto_enable:
            try:
                await self.enable_plugin(plugin_id)
            except Exception as e:
                self._logger.error(
                    f"Failed to enable installed plugin '{plugin_id}': {str(e)}",
                    extra={'plugin_id': plugin_id, 'error': str(e)}
                )

    async def _on_plugin_uninstalled(self, event: Any) -> None:
        """Handle plugin uninstalled event.

        Args:
            event: Event data
        """
        plugin_id = event.payload.get('plugin_id')
        if not plugin_id:
            return

        self._logger.debug(f'Handling plugin uninstalled event for {plugin_id}')

        # Unload the plugin if it's loaded
        try:
            await self.unload_plugin(plugin_id)
        except Exception:
            pass

        # Remove the plugin from our lists
        async with self._plugins_lock:
            if plugin_id in self._plugins:
                plugin_name = self._plugins[plugin_id].name

                # Remove from enabled/disabled lists
                if plugin_name in self._enabled_plugins:
                    self._enabled_plugins.remove(plugin_name)

                if plugin_name in self._disabled_plugins:
                    self._disabled_plugins.remove(plugin_name)

                # Update configuration
                self._config_manager.set('plugins.enabled', self._enabled_plugins)
                self._config_manager.set('plugins.disabled', self._disabled_plugins)

                # Remove from plugin lists
                del self._plugins[plugin_id]

                if plugin_id in self._plugin_instances:
                    del self._plugin_instances[plugin_id]

                if plugin_id in self._plugin_paths:
                    del self._plugin_paths[plugin_id]

                self._ui_plugins.discard(plugin_id)

    async def _on_plugin_enabled(self, event: Any) -> None:
        """Handle plugin enabled event.

        Args:
            event: Event data
        """
        plugin_id = event.payload.get('plugin_id')
        if not plugin_id:
            return

        self._logger.debug(f'Handling plugin enabled event for {plugin_id}')

        try:
            await self.enable_plugin(plugin_id)
        except Exception as e:
            self._logger.error(
                f"Failed to handle plugin enabled event for '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)}
            )

    async def _on_plugin_disabled(self, event: Any) -> None:
        """Handle plugin disabled event.

        Args:
            event: Event data
        """
        plugin_id = event.payload.get('plugin_id')
        if not plugin_id:
            return

        self._logger.debug(f'Handling plugin disabled event for {plugin_id}')

        try:
            await self.disable_plugin(plugin_id)
        except Exception as e:
            self._logger.error(
                f"Failed to handle plugin disabled event for '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)}
            )

    async def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get information about a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            Plugin information or None if not found
        """
        async with self._plugins_lock:
            return self._plugins.get(plugin_id)

    async def get_plugins(
            self,
            state: Optional[Union[PluginState, List[PluginState]]] = None
    ) -> Dict[str, PluginInfo]:
        """Get all plugins, optionally filtered by state.

        Args:
            state: Optional state or list of states to filter by

        Returns:
            Dictionary of plugin IDs to plugin information
        """
        # Convert single state to list for consistent handling
        states = None
        if state is not None:
            if isinstance(state, list):
                states = state
            else:
                states = [state]

        async with self._plugins_lock:
            if states:
                return {
                    pid: pinfo for pid, pinfo in self._plugins.items()
                    if pinfo.state in states
                }
            else:
                return self._plugins.copy()

    async def get_plugin_instance(self, plugin_id: str) -> Optional[Any]:
        """Get a plugin instance.

        Args:
            plugin_id: ID of the plugin

        Returns:
            Plugin instance or None if not found
        """
        async with self._plugins_lock:
            return self._plugin_instances.get(plugin_id)

    async def shutdown(self) -> None:
        """Shutdown the plugin manager.

        Unloads all plugins and cleans up resources.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down plugin manager')

            # Get list of loaded plugins
            loaded_plugins = []
            async with self._plugins_lock:
                for plugin_id, plugin_info in self._plugins.items():
                    if plugin_info.state in (PluginState.ACTIVE, PluginState.LOADING):
                        loaded_plugins.append(plugin_id)

            # Sort plugins for unloading (reverse dependency order)
            for plugin_id in reversed(loaded_plugins):
                try:
                    await self.unload_plugin(plugin_id)
                except Exception as e:
                    self._logger.error(
                        f"Error unloading plugin '{plugin_id}' during shutdown: {str(e)}",
                        extra={'plugin_id': plugin_id, 'error': str(e)}
                    )

            # Unregister event listeners
            await self._event_bus_manager.unsubscribe(subscriber_id='plugin_manager')

            # Unregister configuration listener
            await self._config_manager.unregister_listener('plugins', self._on_config_changed)

            # Clear plugin data
            async with self._plugins_lock:
                self._plugins.clear()
                self._plugin_instances.clear()
                self._plugin_paths.clear()
                self._ui_plugins.clear()

            self._initialized = False
            self._healthy = False
            self._logger.info('Plugin manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down plugin manager: {str(e)}', exc_info=True)
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
            state_counts = {state.value: 0 for state in PluginState}

            for plugin_info in self._plugins.values():
                state_counts[plugin_info.state.value] += 1

            status.update({
                'plugins': {
                    'total': len(self._plugins),
                    'by_state': state_counts,
                    'loaded': len(self._plugin_instances),
                    'ui_integration': len(self._ui_plugins)
                },
                'config': {
                    'auto_load': self._auto_load,
                    'plugin_dir': str(self._plugin_dir) if self._plugin_dir else None,
                    'enabled_count': len(self._enabled_plugins),
                    'disabled_count': len(self._disabled_plugins)
                },
                'ui_ready': self._ui_ready.is_set()
            })

        return status