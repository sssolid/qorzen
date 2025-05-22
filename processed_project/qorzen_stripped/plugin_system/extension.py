from __future__ import annotations
import importlib
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, Protocol, cast
from dataclasses import dataclass, field
from qorzen.plugin_system.manifest import PluginExtensionPoint, PluginManifest
class ExtensionImplementation(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...
class ExtensionPointNotFoundError(Exception):
    def __init__(self, provider: str, extension_id: str):
        self.provider = provider
        self.extension_id = extension_id
        super().__init__(f"Extension point '{extension_id}' not found from provider '{provider}'")
class ExtensionPointVersionError(Exception):
    def __init__(self, provider: str, extension_id: str, required: str, available: str):
        self.provider = provider
        self.extension_id = extension_id
        self.required = required
        self.available = available
        super().__init__(f"Extension point '{extension_id}' from provider '{provider}' has incompatible version: required {required}, available {available}")
class ExtensionInterface:
    def __init__(self, provider: str, extension_point: PluginExtensionPoint, provider_instance: Any=None):
        self.provider = provider
        self.extension_id = extension_point.id
        self.name = extension_point.name
        self.description = extension_point.description
        self.interface = extension_point.interface
        self.version = extension_point.version
        self.parameters = extension_point.parameters
        self.provider_instance = provider_instance
        self.implementations: Dict[str, ExtensionImplementation] = {}
    def register_implementation(self, plugin_name: str, implementation: ExtensionImplementation) -> None:
        self.implementations[plugin_name] = implementation
    def unregister_implementation(self, plugin_name: str) -> None:
        if plugin_name in self.implementations:
            del self.implementations[plugin_name]
    def get_implementation(self, plugin_name: str) -> Optional[ExtensionImplementation]:
        return self.implementations.get(plugin_name)
    def get_all_implementations(self) -> Dict[str, ExtensionImplementation]:
        return self.implementations.copy()
    def __call__(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        results = {}
        for plugin_name, implementation in self.implementations.items():
            try:
                results[plugin_name] = implementation(*args, **kwargs)
            except Exception as e:
                results[plugin_name] = {'error': str(e)}
        return results
@dataclass
class ExtensionRegistry:
    extension_points: Dict[str, Dict[str, ExtensionInterface]] = field(default_factory=dict)
    pending_uses: Dict[str, List[Tuple[str, str, str, bool]]] = field(default_factory=dict)
    logger: Optional[Callable[[str, str], None]] = None
    def __post_init__(self) -> None:
        if self.logger is None:
            self.logger = lambda msg, level: None
    def log(self, message: str, level: str='info') -> None:
        if self.logger:
            self.logger(message, level)
    def register_extension_point(self, provider: str, extension_point: PluginExtensionPoint, provider_instance: Any=None) -> None:
        if provider not in self.extension_points:
            self.extension_points[provider] = {}
        extension_id = extension_point.id
        self.extension_points[provider][extension_id] = ExtensionInterface(provider=provider, extension_point=extension_point, provider_instance=provider_instance)
        self.log(f"Registered extension point '{extension_id}' from provider '{provider}'", 'debug')
        key = f'{provider}.{extension_id}'
        if key in self.pending_uses:
            for consumer, consumer_id, version, required in self.pending_uses[key]:
                self._check_and_resolve_pending_use(provider, extension_id, consumer, consumer_id, version, required)
            del self.pending_uses[key]
    def unregister_extension_point(self, provider: str, extension_id: str) -> None:
        if provider in self.extension_points and extension_id in self.extension_points[provider]:
            del self.extension_points[provider][extension_id]
            if not self.extension_points[provider]:
                del self.extension_points[provider]
            self.log(f"Unregistered extension point '{extension_id}' from provider '{provider}'", 'debug')
    def register_extension_use(self, consumer: str, consumer_id: str, provider: str, extension_id: str, version: str, implementation: ExtensionImplementation, required: bool=True) -> None:
        if provider in self.extension_points and extension_id in self.extension_points[provider]:
            extension = self.extension_points[provider][extension_id]
            if not self._is_version_compatible(extension.version, version):
                if required:
                    raise ExtensionPointVersionError(provider, extension_id, version, extension.version)
                else:
                    self.log(f"Skipping incompatible extension point '{extension_id}' from provider '{provider}': required {version}, available {extension.version}", 'warning')
                    return
            extension.register_implementation(consumer, implementation)
            self.log(f"Registered implementation of extension point '{extension_id}' from provider '{provider}' by consumer '{consumer}'", 'debug')
        elif required:
            self.log(f"Extension point '{extension_id}' from provider '{provider}' not found, adding to pending uses", 'debug')
            key = f'{provider}.{extension_id}'
            if key not in self.pending_uses:
                self.pending_uses[key] = []
            self.pending_uses[key].append((consumer, consumer_id, version, required))
        else:
            self.log(f"Optional extension point '{extension_id}' from provider '{provider}' not found, skipping", 'debug')
    def unregister_extension_use(self, consumer: str, provider: str, extension_id: str) -> None:
        if provider in self.extension_points and extension_id in self.extension_points[provider]:
            extension = self.extension_points[provider][extension_id]
            extension.unregister_implementation(consumer)
            self.log(f"Unregistered implementation of extension point '{extension_id}' from provider '{provider}' by consumer '{consumer}'", 'debug')
    def get_extension_point(self, provider: str, extension_id: str) -> Optional[ExtensionInterface]:
        if provider in self.extension_points and extension_id in self.extension_points[provider]:
            return self.extension_points[provider][extension_id]
        return None
    def get_all_extension_points(self) -> Dict[str, Dict[str, ExtensionInterface]]:
        return self.extension_points.copy()
    def get_provider_extension_points(self, provider: str) -> Dict[str, ExtensionInterface]:
        return self.extension_points.get(provider, {}).copy()
    def register_plugin_extensions(self, plugin_name: str, plugin_instance: Any, manifest: PluginManifest) -> None:
        for extension_point in manifest.extension_points:
            self.register_extension_point(provider=plugin_name, extension_point=extension_point, provider_instance=plugin_instance)
        for extension_use in manifest.extension_uses:
            provider = extension_use.provider
            extension_id = extension_use.id
            version = extension_use.version
            required = extension_use.required
            implementation = self._find_extension_implementation(plugin_instance, plugin_name, provider, extension_id)
            if implementation:
                self.register_extension_use(consumer=plugin_name, consumer_id=f'{plugin_name}.{provider}.{extension_id}', provider=provider, extension_id=extension_id, version=version, implementation=implementation, required=required)
            elif required:
                raise ValueError(f"Required extension implementation for '{extension_id}' from provider '{provider}' not found in plugin '{plugin_name}'")
    def unregister_plugin_extensions(self, plugin_name: str) -> None:
        if plugin_name in self.extension_points:
            for extension_id in list(self.extension_points[plugin_name].keys()):
                self.unregister_extension_point(plugin_name, extension_id)
        for provider in list(self.extension_points.keys()):
            for extension_id in list(self.extension_points.get(provider, {}).keys()):
                extension = self.extension_points[provider][extension_id]
                if plugin_name in extension.implementations:
                    self.unregister_extension_use(plugin_name, provider, extension_id)
        for key, uses in list(self.pending_uses.items()):
            self.pending_uses[key] = [use for use in uses if use[0] != plugin_name]
            if not self.pending_uses[key]:
                del self.pending_uses[key]
    def _is_version_compatible(self, available: str, required: str) -> bool:
        try:
            import semver
        except ImportError:
            raise ImportError("The 'semver' package is required for version comparison")
        try:
            available_ver = semver.Version.parse(available)
            required_ver = semver.Version.parse(required)
            if available_ver.major != required_ver.major:
                return False
            return available_ver >= required_ver
        except ValueError:
            return False
    def _find_extension_implementation(self, plugin_instance: Any, plugin_name: str, provider: str, extension_id: str) -> Optional[ExtensionImplementation]:
        provider_snake = provider.replace('-', '_').replace('.', '_')
        extension_snake = extension_id.replace('-', '_').replace('.', '_')
        method_names = [f'{provider_snake}_{extension_snake}', f'implement_{provider_snake}_{extension_snake}', f'extension_{provider_snake}_{extension_snake}']
        for name in method_names:
            if hasattr(plugin_instance, name) and callable(getattr(plugin_instance, name)):
                return cast(ExtensionImplementation, getattr(plugin_instance, name))
        return None
    def _check_and_resolve_pending_use(self, provider: str, extension_id: str, consumer: str, consumer_id: str, version: str, required: bool) -> None:
        from qorzen.core.plugin_manager import PluginManager
        plugin_manager = None
        for module_name in ['qorzen.core.app', 'qorzen.core']:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, 'ApplicationCore'):
                    app_core = getattr(module, 'ApplicationCore')
                    if hasattr(app_core, 'get_manager'):
                        plugin_manager = app_core().get_manager('plugin_manager')
                        break
            except (ImportError, AttributeError):
                continue
        if plugin_manager is None:
            self.log(f"Could not resolve pending use of extension point '{extension_id}' from provider '{provider}' by consumer '{consumer}': plugin manager not found", 'warning')
            return
        consumer_info = plugin_manager.get_plugin_info(consumer)
        if not consumer_info or 'instance' not in consumer_info:
            self.log(f"Could not resolve pending use of extension point '{extension_id}' from provider '{provider}' by consumer '{consumer}': consumer plugin instance not found", 'warning')
            return
        consumer_instance = consumer_info['instance']
        implementation = self._find_extension_implementation(consumer_instance, consumer, provider, extension_id)
        if implementation:
            self.register_extension_use(consumer=consumer, consumer_id=consumer_id, provider=provider, extension_id=extension_id, version=version, implementation=implementation, required=required)
        elif required:
            self.log(f"Could not resolve pending use of extension point '{extension_id}' from provider '{provider}' by consumer '{consumer}': implementation not found", 'warning')
extension_registry = ExtensionRegistry()
def register_extension_point(provider: str, id: str, name: str, description: str, interface: str, version: str='1.0.0', parameters: Optional[Dict[str, Any]]=None, provider_instance: Any=None) -> ExtensionInterface:
    extension_point = PluginExtensionPoint(id=id, name=name, description=description, interface=interface, version=version, parameters=parameters or {})
    extension_registry.register_extension_point(provider=provider, extension_point=extension_point, provider_instance=provider_instance)
    return extension_registry.get_extension_point(provider, id)
def get_extension_point(provider: str, extension_id: str) -> Optional[ExtensionInterface]:
    return extension_registry.get_extension_point(provider, extension_id)
def call_extension_point(provider: str, extension_id: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    extension = extension_registry.get_extension_point(provider, extension_id)
    if extension is None:
        raise ExtensionPointNotFoundError(provider, extension_id)
    return extension(*args, **kwargs)
def register_plugin_extensions(plugin_name: str, plugin_instance: Any, manifest: PluginManifest) -> None:
    extension_registry.register_plugin_extensions(plugin_name=plugin_name, plugin_instance=plugin_instance, manifest=manifest)
def unregister_plugin_extensions(plugin_name: str) -> None:
    extension_registry.unregister_plugin_extensions(plugin_name)