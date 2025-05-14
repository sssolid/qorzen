from __future__ import annotations
import asyncio
import importlib
import inspect
import os
import pathlib
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union, cast, Tuple
from qorzen.core.base import QorzenManager
from qorzen.core.error_handler import ErrorHandler, ErrorSeverity, create_error_boundary
from qorzen.plugin_system import BasePlugin
from qorzen.plugin_system.plugin_state_manager import PluginStateManager
from qorzen.utils.exceptions import PluginError, ManagerInitializationError, ManagerShutdownError


class PluginState(str, Enum):
    DISCOVERED = 'discovered'
    LOADING = 'loading'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    FAILED = 'failed'
    DISABLED = 'disabled'
    INCOMPATIBLE = 'incompatible'


@dataclass
class PluginManifest:
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
    entry_point: str = 'plugin.py'
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    ui_integration: bool = True
    settings_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PluginManifest:
        return cls(
            name=data.get('name', ''),
            display_name=data.get('display_name', ''),
            version=data.get('version', '0.1.0'),
            description=data.get('description', ''),
            author=data.get('author', 'Unknown'),
            logo_path=data.get('logo_path', ''),
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
        try:
            import json
            import logging
            logger = logging.getLogger('plugin_manifest')
            path_obj = pathlib.Path(path)
            if not path_obj.exists():
                logger.debug(f'Manifest file does not exist: {path}')
                return None

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle author field if it's a dictionary
            if 'author' in data and isinstance(data['author'], dict):
                author_dict = data['author']
                if 'name' in author_dict:
                    data['author'] = author_dict['name']

            # Handle logo path if it's None
            if 'logo_path' in data and data['logo_path'] is None:
                data['logo_path'] = ''

            # Check for required fields
            required_fields = ['name', 'display_name', 'version', 'description', 'author']
            for field in required_fields:
                if field not in data or not data[field]:
                    logger.warning(f'Missing required field in manifest: {field}')

            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger = logging.getLogger('plugin_manifest')
            logger.error(f'Invalid JSON in manifest file {path}: {str(e)}')
            return None
        except Exception as e:
            logger = logging.getLogger('plugin_manifest')
            logger.error(f'Error loading manifest from {path}: {str(e)}')
            return None

    def to_dict(self) -> Dict[str, Any]:
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

    @property
    def display_name(self) -> str:
        if self.manifest and hasattr(self.manifest, 'display_name') and self.manifest.display_name:
            return self.manifest.display_name
        return self.name


class PluginManager(QorzenManager):
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
        super().__init__(name='plugin_manager')
        self._application_core = application_core
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('plugin_manager')
        self._event_bus_manager = event_bus_manager
        self._file_manager = file_manager
        self._task_manager = task_manager
        self._plugin_isolation = plugin_isolation_manager
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_instances: Dict[str, Any] = {}
        self._plugin_paths: Dict[str, str] = {}
        self._plugins_lock = asyncio.Lock()
        self._plugin_dir: Optional[pathlib.Path] = None
        self._auto_load = True
        self._enabled_plugins: List[str] = []
        self._disabled_plugins: List[str] = []
        self._entry_point_group = 'qorzen.plugins'
        self._error_handler: Optional[ErrorHandler] = None
        self._ui_integration = None
        self._ui_ready = asyncio.Event()
        self._ui_plugins: Set[str] = set()
        self._state_manager = PluginStateManager(self, self._logger)

    async def initialize(self) -> None:
        try:
            self._logger.info('Initializing plugin manager')
            if hasattr(self._event_bus_manager, 'error_handler'):
                self._error_handler = self._event_bus_manager.error_handler
                self._error_handler.initialize()

            plugin_config = await self._config_manager.get('plugins', {})
            plugin_dir = plugin_config.get('directory', 'plugins')
            self._plugin_dir = pathlib.Path(plugin_dir)
            self._auto_load = plugin_config.get('autoload', True)
            self._enabled_plugins = plugin_config.get('enabled', [])
            self._disabled_plugins = plugin_config.get('disabled', [])

            os.makedirs(self._plugin_dir, exist_ok=True)

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

            await self._config_manager.register_listener('plugins', self._on_config_changed)
            await self._discover_plugins()

            self._initialized = True
            self._healthy = True

            if self._auto_load:
                asyncio.create_task(self._load_enabled_plugins())

            self._logger.info(f'Plugin manager initialized with {len(self._plugins)} plugins discovered')
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
        self._logger.debug('Discovering plugins')
        await self._discover_entry_point_plugins()
        await self._discover_directory_plugins()
        await self._discover_installed_plugins()

    async def _discover_entry_point_plugins(self) -> None:
        try:
            import importlib.metadata
            entry_points = importlib.metadata.entry_points(group=self._entry_point_group)
            for entry_point in entry_points:
                # Generate a unique plugin ID with UUID suffix
                plugin_id = f'entry_{entry_point.name}_{uuid.uuid4().hex[:8]}'
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

                manifest_file = item / 'manifest.json'
                if manifest_file.exists():
                    await self._discover_plugin_from_manifest(item)
                else:
                    await self._discover_plugin_from_module(item)
        except Exception as e:
            self._logger.error(f'Failed to discover directory plugins: {str(e)}', exc_info=True)

    async def _discover_plugin_from_manifest(self, plugin_dir: pathlib.Path) -> None:
        manifest_file = plugin_dir / 'manifest.json'
        try:
            manifest = PluginManifest.load(manifest_file)
            if not manifest:
                self._logger.warning(f'Failed to load manifest from {manifest_file}')
                return

            # Generate a unique plugin ID with UUID suffix
            plugin_id = f'manifest_{manifest.name}_{uuid.uuid4().hex[:8]}'
            entry_point = manifest.entry_point
            entry_path = plugin_dir / entry_point
            entry_exists = entry_path.exists()

            self._logger.debug(
                f'Discovered plugin from manifest: {manifest.name}, entry point: {entry_point}, exists: {entry_exists}'
            )

            if not entry_path.exists() and '.' in entry_point:
                module_name = f'{plugin_dir.name}.{entry_point}'
                try:
                    importlib.import_module(module_name)
                except ImportError:
                    self._logger.warning(
                        f'Failed to import module {module_name} for plugin {manifest.name}',
                        extra={'plugin': manifest.name, 'module': module_name}
                    )
                    return

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

            async with self._plugins_lock:
                self._plugins[plugin_id] = plugin_info
                self._plugin_paths[plugin_id] = str(plugin_dir)

            self._logger.debug(
                f"Discovered plugin '{plugin_info.name}' from manifest",
                extra={'plugin_id': plugin_id, 'version': plugin_info.version, 'path': str(plugin_dir)}
            )
        except Exception as e:
            self._logger.error(
                f'Failed to discover plugin from manifest in {plugin_dir.name}: {str(e)}',
                extra={'directory': str(plugin_dir)},
                exc_info=True
            )

    async def _discover_plugin_from_module(self, plugin_dir: pathlib.Path) -> None:
        init_file = plugin_dir / '__init__.py'
        plugin_file = plugin_dir / 'plugin.py'

        if not init_file.exists() and not plugin_file.exists():
            return

        try:
            module_name = plugin_dir.name
            if init_file.exists():
                module = importlib.import_module(module_name)
            elif plugin_file.exists():
                spec = importlib.util.spec_from_file_location(f'{module_name}.plugin', plugin_file)
                if not spec or not spec.loader:
                    return
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                return

            plugin_class = None
            if hasattr(module, '__all__'):
                for name in module.__all__:
                    obj = getattr(module, name)
                    if inspect.isclass(obj) and hasattr(obj, 'name') and hasattr(obj, 'version') and hasattr(obj,
                                                                                                             'description'):
                        plugin_class = obj
                        break

            if not plugin_class:
                for name, obj in module.__dict__.items():
                    if inspect.isclass(obj) and hasattr(obj, 'name') and hasattr(obj, 'version') and hasattr(obj,
                                                                                                             'description'):
                        plugin_class = obj
                        break

            if not plugin_class:
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if hasattr(obj, 'name') and hasattr(obj, 'version') and hasattr(obj, 'description'):
                        plugin_class = obj
                        break

            if not plugin_class:
                return

            # Generate a unique plugin ID with UUID suffix
            plugin_id = f'module_{module_name}_{uuid.uuid4().hex[:8]}'
            plugin_info = await self._extract_plugin_metadata(
                plugin_class=plugin_class,
                default_name=module_name,
                plugin_id=plugin_id,
                path=str(plugin_dir)
            )

            async with self._plugins_lock:
                self._plugins[plugin_id] = plugin_info
                self._plugin_paths[plugin_id] = str(plugin_dir)

            self._logger.debug(
                f"Discovered plugin '{plugin_info.name}' from module",
                extra={'plugin_id': plugin_id, 'version': plugin_info.version, 'path': str(plugin_dir)}
            )
        except Exception as e:
            self._logger.error(
                f'Failed to discover plugin from module in {plugin_dir.name}: {str(e)}',
                extra={'directory': str(plugin_dir)}
            )

    async def _discover_installed_plugins(self) -> None:
        pass

    async def _extract_plugin_metadata(
            self,
            plugin_class: Type,
            default_name: str,
            plugin_id: str,
            path: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> PluginInfo:
        name = getattr(plugin_class, 'name', default_name)
        version = getattr(plugin_class, 'version', '0.1.0')
        description = getattr(plugin_class, 'description', 'No description')
        author = getattr(plugin_class, 'author', 'Unknown')
        dependencies = getattr(plugin_class, 'dependencies', [])
        capabilities = getattr(plugin_class, 'capabilities', [])

        plugin_metadata = {
            'class': plugin_class.__name__,
            'module': plugin_class.__module__
        }
        if metadata:
            plugin_metadata.update(metadata)

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
        self._logger.info('Loading enabled plugins')
        enabled_plugins = []
        async with self._plugins_lock:
            for plugin_id, plugin_info in self._plugins.items():
                if self._is_plugin_enabled(plugin_info.name):
                    enabled_plugins.append((plugin_id, plugin_info))

        sorted_plugins = await self._sort_plugins_by_dependencies(enabled_plugins)
        for plugin_id, _ in sorted_plugins:
            try:
                await self.load_plugin(plugin_id)
            except Exception as e:
                self._logger.error(
                    f'Failed to load plugin {plugin_id}: {str(e)}',
                    extra={'plugin_id': plugin_id, 'error': str(e)}
                )

    async def _sort_plugins_by_dependencies(
            self, plugins: List[Tuple[str, PluginInfo]]
    ) -> List[Tuple[str, PluginInfo]]:
        graph = {}
        for plugin_id, plugin_info in plugins:
            graph[plugin_id] = set()
            for dep in plugin_info.dependencies:
                dep_id = None
                for pid, pinfo in plugins:
                    if pinfo.name == dep:
                        dep_id = pid
                        break
                if dep_id:
                    graph[plugin_id].add(dep_id)

        result = []
        temp_marks = set()
        perm_marks = set()

        def visit(node):
            if node in perm_marks:
                return
            if node in temp_marks:
                self._logger.warning(f'Circular dependency detected involving {node}')
                return
            temp_marks.add(node)
            for dep in graph.get(node, set()):
                visit(dep)
            temp_marks.remove(node)
            perm_marks.add(node)
            for plugin_id, plugin_info in plugins:
                if plugin_id == node:
                    result.append((plugin_id, plugin_info))
                    break

        for plugin_id, _ in plugins:
            if plugin_id not in perm_marks:
                visit(plugin_id)

        return result

    async def load_plugin(self, plugin_id: str) -> bool:
        if not self._initialized:
            raise PluginError('Plugin manager not initialized')

        async with self._plugins_lock:
            if plugin_id not in self._plugins:
                raise PluginError(f"Plugin '{plugin_id}' not found")

            plugin_info = self._plugins[plugin_id]
            self._logger.debug(f"Starting to load plugin '{plugin_id}' (current state: {plugin_info.state})")

            if plugin_info.state in (PluginState.ACTIVE, PluginState.LOADING):
                self._logger.debug(f"Plugin '{plugin_id}' is already loaded or loading")
                return True

            if self._is_plugin_disabled(plugin_info.name):
                self._logger.info(f"Plugin '{plugin_id}' is disabled, skipping load")
                plugin_info.state = PluginState.DISABLED
                return False

            plugin_info.state = PluginState.LOADING

        error_boundary = (
            create_error_boundary(source='plugin_loading', plugin_id=plugin_id)
            if self._error_handler
            else None
        )

        try:
            self._logger.debug(f"Loading dependencies for plugin '{plugin_id}'")
            await self._load_plugin_dependencies(plugin_id)

            if plugin_info.manifest:
                self._logger.debug(f"Loading plugin '{plugin_id}' from manifest")
                success = await self._load_plugin_from_manifest(plugin_id)
            else:
                self._logger.debug(f"Loading plugin '{plugin_id}' from module")
                success = await self._load_plugin_from_module(plugin_id)

            if not success:
                self._logger.warning(f"Failed to load plugin '{plugin_id}'")
                return False

            async with self._plugins_lock:
                plugin_info.state = PluginState.ACTIVE
                plugin_info.load_time = time.time()

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
            self._logger.error(
                f"Failed to load plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)},
                exc_info=True
            )

            async with self._plugins_lock:
                plugin_info.state = PluginState.FAILED
                plugin_info.error = str(e)

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
        async with self._plugins_lock:
            plugin_info = self._plugins[plugin_id]
            dependencies = plugin_info.dependencies

        for dep_name in dependencies:
            if dep_name == 'core':
                continue

            dep_id = None
            async with self._plugins_lock:
                for pid, pinfo in self._plugins.items():
                    if pinfo.name == dep_name:
                        dep_id = pid
                        break

            if not dep_id:
                raise PluginError(f"Dependency '{dep_name}' not found for plugin '{plugin_id}'")

            async with self._plugins_lock:
                dep_info = self._plugins[dep_id]
                if dep_info.state == PluginState.ACTIVE:
                    continue

            success = await self.load_plugin(dep_id)
            if not success:
                raise PluginError(f"Failed to load dependency '{dep_name}' for plugin '{plugin_id}'")

    async def _load_plugin_from_manifest(self, plugin_id: str) -> bool:
        async with self._plugins_lock:
            plugin_info = self._plugins[plugin_id]
            manifest = plugin_info.manifest
            plugin_path = plugin_info.path

        if not manifest or not plugin_path:
            raise PluginError(f"Plugin '{plugin_id}' has no manifest or path")

        plugin_dir = pathlib.Path(plugin_path)
        if not plugin_dir.exists():
            raise PluginError(f'Plugin directory not found: {plugin_path}')

        entry_point = manifest.entry_point
        self._logger.debug(f"Loading plugin '{plugin_id}' with entry point: {entry_point}")

        entry_path = None
        module = None

        if entry_point.endswith('.py'):
            if '/' in entry_point or '\\' in entry_point:
                entry_path = plugin_dir / entry_point.replace('/', os.sep).replace('\\', os.sep)
                if not entry_path.exists():
                    raise PluginError(f'Entry point file not found: {entry_path}')

                module_name = f"{plugin_dir.name}.{entry_point.replace('/', '.').replace('\\', '.').replace('.py', '')}"
                try:
                    module = importlib.import_module(module_name)
                    self._logger.debug(f'Imported plugin module: {module_name}')
                except ImportError:
                    self._logger.debug(f'Module import failed, loading directly from file: {entry_path}')
                    spec = importlib.util.spec_from_file_location(f'plugin_{plugin_id}', entry_path)
                    if not spec or not spec.loader:
                        raise PluginError(f'Failed to create module spec for {entry_path}')
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            else:
                entry_path = plugin_dir / entry_point
                if not entry_path.exists():
                    raise PluginError(f'Entry point file not found: {entry_point}')

                spec = importlib.util.spec_from_file_location(f'plugin_{plugin_id}', entry_path)
                if not spec or not spec.loader:
                    raise PluginError(f'Failed to create module spec for {entry_path}')
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        else:
            if '.' in entry_point:
                module_name = f'{plugin_dir.name}.{entry_point}'
            else:
                module_name = entry_point

            try:
                module = importlib.import_module(module_name)
                self._logger.debug(f'Imported plugin module: {module_name}')
            except ImportError as e:
                raise PluginError(f'Failed to import plugin module: {str(e)}') from e

        if not module:
            raise PluginError(f'Failed to load module for plugin {plugin_id}')

        plugin_class = None
        if hasattr(module, '__all__'):
            for name in module.__all__:
                if name in module.__dict__:
                    obj = module.__dict__[name]
                    if inspect.isclass(obj) and hasattr(obj, 'name') and hasattr(obj, 'version'):
                        plugin_class = obj
                        self._logger.debug(f'Found plugin class from __all__: {name}')
                        break

        if not plugin_class:
            # new
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # pick only subclasses of BasePlugin, excluding BasePlugin itself
                if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                    plugin_class = obj
                    self._logger.debug(f'Found plugin subclass: {name}')
                    break

        if not plugin_class:
            raise PluginError(f'No plugin class found in {entry_point}')

        try:
            self._logger.debug(f'Creating instance of plugin class: {plugin_class.__name__}')
            plugin_instance = plugin_class()

            if hasattr(plugin_instance, 'plugin_id'):
                plugin_instance.plugin_id = plugin_id

            if hasattr(plugin_instance, 'initialize'):
                self._logger.debug(f'Initializing plugin: {plugin_id}')
                await self._initialize_plugin(plugin_instance, plugin_id)

            async with self._plugins_lock:
                self._plugin_instances[plugin_id] = plugin_instance

            if manifest.ui_integration and hasattr(plugin_instance, 'setup_ui'):
                if self._ui_ready.is_set():
                    self._logger.debug(f'Setting up UI for plugin: {plugin_id}')
                    await self._setup_plugin_ui(plugin_id)
                else:
                    self._logger.debug(f'UI not ready, queuing plugin for UI setup: {plugin_id}')
                    self._ui_plugins.add(plugin_id)

            return True
        except Exception as e:
            self._logger.error(f'Error initializing plugin {plugin_id}: {str(e)}', exc_info=True)
            raise PluginError(f'Failed to initialize plugin {plugin_id}: {str(e)}') from e

    async def _load_plugin_from_module(self, plugin_id: str) -> bool:
        async with self._plugins_lock:
            plugin_info = self._plugins[plugin_id]

        module_name = plugin_info.metadata.get('module')
        class_name = plugin_info.metadata.get('class')

        if not module_name or not class_name:
            raise PluginError(f"Plugin '{plugin_id}' has invalid metadata")

        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            plugin_instance = plugin_class()

            if hasattr(plugin_instance, 'initialize'):
                await self._initialize_plugin(plugin_instance, plugin_id)

            async with self._plugins_lock:
                self._plugin_instances[plugin_id] = plugin_instance

            if hasattr(plugin_instance, 'setup_ui'):
                if self._ui_ready.is_set():
                    await self._setup_plugin_ui(plugin_id)
                else:
                    self._ui_plugins.add(plugin_id)

            return True
        except Exception as e:
            raise PluginError(f"Failed to load plugin '{plugin_id}' from module: {str(e)}") from e

    async def _initialize_plugin(self, plugin_instance: Any, plugin_id: str) -> None:
        try:
            initialize_method = getattr(plugin_instance, 'initialize')
            error_boundary = (
                create_error_boundary(source='plugin_initialization', plugin_id=plugin_id)
                if self._error_handler
                else None
            )

            if error_boundary:
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
            elif asyncio.iscoroutinefunction(initialize_method):
                await initialize_method(self._application_core)
            else:
                initialize_method(self._application_core)
        except Exception as e:
            raise PluginError(f"Failed to initialize plugin '{plugin_id}': {str(e)}") from e

    async def _setup_plugin_ui(self, plugin_id: str) -> None:
        if not self._ui_integration:
            return

        async with self._plugins_lock:
            if plugin_id not in self._plugin_instances:
                return

            plugin_instance = self._plugin_instances[plugin_id]
            if not hasattr(plugin_instance, 'setup_ui'):
                return

        error_boundary = (
            create_error_boundary(source='plugin_ui_setup', plugin_id=plugin_id)
            if self._error_handler
            else None
        )

        try:
            setup_ui_method = getattr(plugin_instance, 'setup_ui')

            if error_boundary:
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
            elif asyncio.iscoroutinefunction(setup_ui_method):
                await setup_ui_method(self._ui_integration)
            else:
                setup_ui_method(self._ui_integration)
            self._ui_plugins.add(plugin_id)
        except Exception as e:
            self._logger.error(
                f"Failed to set up UI for plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)},
                exc_info=True
            )

    async def unload_plugin(self, plugin_id: str) -> bool:
        if not self._initialized:
            raise PluginError('Plugin manager not initialized')

        async with self._plugins_lock:
            if plugin_id not in self._plugins:
                raise PluginError(f"Plugin '{plugin_id}' not found")

            plugin_info = self._plugins[plugin_id]
            if plugin_info.state not in (PluginState.ACTIVE, PluginState.LOADING):
                self._logger.debug(f"Plugin '{plugin_id}' is not loaded")
                return True

            # Check if other plugins depend on this one
            for other_id, other_info in self._plugins.items():
                if other_id != plugin_id and other_info.state == PluginState.ACTIVE:
                    if plugin_info.name in other_info.dependencies:
                        raise PluginError(
                            f"Cannot unload plugin '{plugin_id}' because it's a dependency for '{other_id}'"
                        )

        error_boundary = (
            create_error_boundary(source='plugin_unloading', plugin_id=plugin_id)
            if self._error_handler
            else None
        )

        try:
            plugin_instance = None
            async with self._plugins_lock:
                if plugin_id in self._plugin_instances:
                    plugin_instance = self._plugin_instances[plugin_id]

            if plugin_instance and hasattr(plugin_instance, 'shutdown'):
                shutdown_method = getattr(plugin_instance, 'shutdown')

                if error_boundary:
                    if asyncio.iscoroutinefunction(shutdown_method):
                        await error_boundary.run(shutdown_method, severity=ErrorSeverity.MEDIUM)
                    else:
                        await error_boundary.run(shutdown_method, severity=ErrorSeverity.MEDIUM)
                elif asyncio.iscoroutinefunction(shutdown_method):
                    await shutdown_method()
                else:
                    shutdown_method()

            if self._ui_integration and plugin_id in self._ui_plugins:
                await self._cleanup_plugin_ui(plugin_id)

            async with self._plugins_lock:
                if plugin_id in self._plugin_instances:
                    del self._plugin_instances[plugin_id]
                plugin_info.state = PluginState.INACTIVE
                plugin_info.instance = None

            await self._event_bus_manager.publish(
                event_type='plugin/unloaded',
                source='plugin_manager',
                payload={'plugin_id': plugin_id, 'name': plugin_info.name}
            )

            self._logger.info(f"Unloaded plugin '{plugin_info.name}'", extra={'plugin_id': plugin_id})
            return True
        except Exception as e:
            self._logger.error(
                f"Failed to unload plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)},
                exc_info=True
            )
            await self._event_bus_manager.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={
                    'plugin_id': plugin_id,
                    'error': f'Failed to unload plugin: {str(e)}',
                    'traceback': traceback.format_exc()
                }
            )
            raise PluginError(f"Failed to unload plugin '{plugin_id}': {str(e)}") from e

    async def _cleanup_plugin_ui(self, plugin_id: str) -> None:
        if not self._ui_integration:
            return

        try:
            self._ui_plugins.discard(plugin_id)
            if hasattr(self._ui_integration, 'clear_plugin_elements'):
                await self._ui_integration.clear_plugin_elements(plugin_id)
        except Exception as e:
            self._logger.error(
                f"Error cleaning up UI for plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)}
            )

    async def enable_plugin(self, plugin_id: str) -> bool:
        ret = await self._state_manager.transition(plugin_id, 'active')
        name = self._plugins[plugin_id].name

        # FIXED: Ensure plugin is in enabled list and not in disabled list
        if name not in self._enabled_plugins:
            self._enabled_plugins.append(name)
            await self._config_manager.set('plugins.enabled', self._enabled_plugins)

        if name in self._disabled_plugins:
            self._disabled_plugins.remove(name)
            await self._config_manager.set('plugins.disabled', self._disabled_plugins)

        return ret

    async def disable_plugin(self, plugin_id: str) -> bool:
        ret = await self._state_manager.transition(plugin_id, 'disabled')
        name = self._plugins[plugin_id].name

        # FIXED: Previously this had the logic reversed
        if name in self._enabled_plugins:
            self._enabled_plugins.remove(name)
            await self._config_manager.set('plugins.enabled', self._enabled_plugins)

        if name not in self._disabled_plugins:
            self._disabled_plugins.append(name)
            await self._config_manager.set('plugins.disabled', self._disabled_plugins)

        return ret

    async def reload_plugin(self, plugin_id: str) -> bool:
        if not self._initialized:
            raise PluginError('Plugin manager not initialized')

        try:
            await self.unload_plugin(plugin_id)

            async with self._plugins_lock:
                plugin_info = self._plugins[plugin_id]
                module_name = plugin_info.metadata.get('module')
                if module_name:
                    if module_name in sys.modules:
                        module = sys.modules[module_name]
                        importlib.reload(module)
                        if '.' in module_name:
                            parent_name = module_name.split('.')[0]
                            if parent_name in sys.modules:
                                importlib.reload(sys.modules[parent_name])

            return await self.load_plugin(plugin_id)
        except Exception as e:
            self._logger.error(
                f"Failed to reload plugin '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)},
                exc_info=True
            )
            await self._event_bus_manager.publish(
                event_type='plugin/error',
                source='plugin_manager',
                payload={
                    'plugin_id': plugin_id,
                    'error': f'Failed to reload plugin: {str(e)}',
                    'traceback': traceback.format_exc()
                }
            )
            raise PluginError(f"Failed to reload plugin '{plugin_id}': {str(e)}") from e

    def _is_plugin_enabled(self, plugin_name: str) -> bool:
        if plugin_name in self._disabled_plugins:
            return False
        if plugin_name in self._enabled_plugins:
            return True
        return self._auto_load

    def _is_plugin_disabled(self, plugin_name: str) -> bool:
        return plugin_name in self._disabled_plugins

    async def _on_config_changed(self, key: str, value: Any) -> None:
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
        self._logger.debug('Received UI ready event')
        ui_integration = event.payload.get('ui_integration')
        if not ui_integration:
            return

        self._ui_integration = ui_integration
        self._ui_ready.set()

        for plugin_id in list(self._ui_plugins):
            asyncio.create_task(self._setup_plugin_ui(plugin_id))

    async def _on_plugin_installed(self, event: Any) -> None:
        plugin_id = event.payload.get('plugin_id')
        plugin_path = event.payload.get('path')
        if not plugin_id or not plugin_path:
            return

        self._logger.debug(f'Handling plugin installed event for {plugin_id}')
        await self._discover_plugins()

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
        plugin_id = event.payload.get('plugin_id')
        if not plugin_id:
            return

        self._logger.debug(f'Handling plugin uninstalled event for {plugin_id}')
        try:
            await self.unload_plugin(plugin_id)
        except Exception:
            pass

        async with self._plugins_lock:
            if plugin_id in self._plugins:
                plugin_name = self._plugins[plugin_id].name
                if plugin_name in self._enabled_plugins:
                    self._enabled_plugins.remove(plugin_name)
                if plugin_name in self._disabled_plugins:
                    self._disabled_plugins.remove(plugin_name)
                await self._config_manager.set('plugins.enabled', self._enabled_plugins)
                await self._config_manager.set('plugins.disabled', self._disabled_plugins)
                del self._plugins[plugin_id]
                if plugin_id in self._plugin_instances:
                    del self._plugin_instances[plugin_id]
                if plugin_id in self._plugin_paths:
                    del self._plugin_paths[plugin_id]
                self._ui_plugins.discard(plugin_id)

    # Fix for the event handler recursion issue
    async def _on_plugin_enabled(self, event: Any) -> None:
        plugin_id = event.payload.get('plugin_id')
        if not plugin_id or event.source == 'plugin_manager':
            # Skip if the event came from this plugin manager to avoid recursion
            return

        self._logger.debug(f'Handling plugin enabled event for {plugin_id}')
        try:
            await self.enable_plugin(plugin_id)
            await self._config_manager.set('plugins.enabled', self._enabled_plugins)
            await self._config_manager.set('plugins.disabled', self._disabled_plugins)
        except Exception as e:
            self._logger.error(
                f"Failed to handle plugin enabled event for '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)}
            )

    # Fix for the event handler recursion issue
    async def _on_plugin_disabled(self, event: Any) -> None:
        plugin_id = event.payload.get('plugin_id')
        if not plugin_id or event.source == 'plugin_manager':
            # Skip if the event came from this plugin manager to avoid recursion
            return

        self._logger.debug(f'Handling plugin disabled event for {plugin_id}')
        try:
            await self.disable_plugin(plugin_id)
            await self._config_manager.set('plugins.enabled', self._enabled_plugins)
            await self._config_manager.set('plugins.disabled', self._disabled_plugins)
        except Exception as e:
            self._logger.error(
                f"Failed to handle plugin disabled event for '{plugin_id}': {str(e)}",
                extra={'plugin_id': plugin_id, 'error': str(e)}
            )

    async def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        async with self._plugins_lock:
            return self._plugins.get(plugin_id)

    async def get_plugins(
            self, state: Optional[Union[PluginState, List[PluginState]]] = None
    ) -> Dict[str, PluginInfo]:
        states = None
        if state is not None:
            if isinstance(state, list):
                states = state
            else:
                states = [state]

        async with self._plugins_lock:
            if states:
                return {
                    pid: pinfo
                    for pid, pinfo in self._plugins.items()
                    if pinfo.state in states
                }
            else:
                return self._plugins.copy()

    async def get_plugin_instance(self, plugin_id: str) -> Optional[Any]:
        async with self._plugins_lock:
            return self._plugin_instances.get(plugin_id)

    async def shutdown(self) -> None:
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down plugin manager')

            loaded_plugins = []
            async with self._plugins_lock:
                for plugin_id, plugin_info in self._plugins.items():
                    if plugin_info.state in (PluginState.ACTIVE, PluginState.LOADING):
                        loaded_plugins.append(plugin_id)

            for plugin_id in reversed(loaded_plugins):
                try:
                    await self.unload_plugin(plugin_id)
                except Exception as e:
                    self._logger.error(
                        f"Error unloading plugin '{plugin_id}' during shutdown: {str(e)}",
                        extra={'plugin_id': plugin_id, 'error': str(e)}
                    )

            await self._event_bus_manager.unsubscribe(subscriber_id='plugin_manager')
            await self._config_manager.unregister_listener('plugins', self._on_config_changed)

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
        status = super().status()
        if self._initialized:
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