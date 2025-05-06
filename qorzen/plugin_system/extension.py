from __future__ import annotations

import importlib
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, Protocol, cast
from dataclasses import dataclass, field

from qorzen.plugin_system.manifest import PluginExtensionPoint, PluginManifest


class ExtensionImplementation(Protocol):
    """Protocol defining the interface for an extension implementation."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the extension implementation."""
        ...


class ExtensionPointNotFoundError(Exception):
    """Exception raised when an extension point is not found."""

    def __init__(self, provider: str, extension_id: str):
        self.provider = provider
        self.extension_id = extension_id
        super().__init__(f"Extension point '{extension_id}' not found from provider '{provider}'")


class ExtensionPointVersionError(Exception):
    """Exception raised when there's a version incompatibility with an extension point."""

    def __init__(self, provider: str, extension_id: str, required: str, available: str):
        self.provider = provider
        self.extension_id = extension_id
        self.required = required
        self.available = available
        super().__init__(
            f"Extension point '{extension_id}' from provider '{provider}' "
            f"has incompatible version: required {required}, available {available}"
        )


class ExtensionInterface:
    """Represents an extension point interface that plugins can implement."""

    def __init__(
            self,
            provider: str,
            extension_point: PluginExtensionPoint,
            provider_instance: Any = None
    ):
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
        """Register an implementation for this extension point."""
        self.implementations[plugin_name] = implementation

    def unregister_implementation(self, plugin_name: str) -> None:
        """Unregister an implementation for this extension point."""
        if plugin_name in self.implementations:
            del self.implementations[plugin_name]

    def get_implementation(self, plugin_name: str) -> Optional[ExtensionImplementation]:
        """Get a specific implementation by plugin name."""
        return self.implementations.get(plugin_name)

    def get_all_implementations(self) -> Dict[str, ExtensionImplementation]:
        """Get all implementations for this extension point."""
        return self.implementations.copy()

    def __call__(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Call all implementations and return the results."""
        results = {}
        for plugin_name, implementation in self.implementations.items():
            try:
                results[plugin_name] = implementation(*args, **kwargs)
            except Exception as e:
                results[plugin_name] = {"error": str(e)}
        return results


@dataclass
class ExtensionRegistry:
    """Registry of all extension points and their implementations."""

    extension_points: Dict[str, Dict[str, ExtensionInterface]] = field(default_factory=dict)
    pending_uses: Dict[str, List[Tuple[str, str, str, bool]]] = field(default_factory=dict)
    logger: Optional[Callable[[str, str], None]] = None

    def __post_init__(self) -> None:
        """Initialize the registry."""
        if self.logger is None:
            self.logger = lambda msg, level: None

    def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        if self.logger:
            self.logger(message, level)

    def register_extension_point(
            self,
            provider: str,
            extension_point: PluginExtensionPoint,
            provider_instance: Any = None
    ) -> None:
        """Register an extension point."""
        if provider not in self.extension_points:
            self.extension_points[provider] = {}

        extension_id = extension_point.id
        self.extension_points[provider][extension_id] = ExtensionInterface(
            provider=provider,
            extension_point=extension_point,
            provider_instance=provider_instance
        )

        self.log(
            f"Registered extension point '{extension_id}' from provider '{provider}'",
            "debug"
        )

        # Check for pending uses
        key = f"{provider}.{extension_id}"
        if key in self.pending_uses:
            for consumer, consumer_id, version, required in self.pending_uses[key]:
                self._check_and_resolve_pending_use(
                    provider, extension_id, consumer, consumer_id, version, required
                )
            # Remove processed pending uses
            del self.pending_uses[key]

    def unregister_extension_point(self, provider: str, extension_id: str) -> None:
        """Unregister an extension point."""
        if provider in self.extension_points and extension_id in self.extension_points[provider]:
            del self.extension_points[provider][extension_id]
            if not self.extension_points[provider]:
                del self.extension_points[provider]
            self.log(
                f"Unregistered extension point '{extension_id}' from provider '{provider}'",
                "debug"
            )

    def register_extension_use(
            self,
            consumer: str,
            consumer_id: str,
            provider: str,
            extension_id: str,
            version: str,
            implementation: ExtensionImplementation,
            required: bool = True
    ) -> None:
        """Register a plugin's use of an extension point."""
        # Check if the extension point exists
        if (provider in self.extension_points and
                extension_id in self.extension_points[provider]):

            extension = self.extension_points[provider][extension_id]
            # Check version compatibility
            if not self._is_version_compatible(extension.version, version):
                if required:
                    raise ExtensionPointVersionError(
                        provider, extension_id, version, extension.version
                    )
                else:
                    self.log(
                        f"Skipping incompatible extension point '{extension_id}' "
                        f"from provider '{provider}': required {version}, "
                        f"available {extension.version}",
                        "warning"
                    )
                    return

            # Register the implementation
            extension.register_implementation(consumer, implementation)
            self.log(
                f"Registered implementation of extension point '{extension_id}' "
                f"from provider '{provider}' by consumer '{consumer}'",
                "debug"
            )
        else:
            # If the extension point doesn't exist, add to pending uses
            if required:
                self.log(
                    f"Extension point '{extension_id}' from provider '{provider}' "
                    f"not found, adding to pending uses",
                    "debug"
                )
                key = f"{provider}.{extension_id}"
                if key not in self.pending_uses:
                    self.pending_uses[key] = []
                self.pending_uses[key].append((consumer, consumer_id, version, required))
            else:
                self.log(
                    f"Optional extension point '{extension_id}' from provider '{provider}' "
                    f"not found, skipping",
                    "debug"
                )

    def unregister_extension_use(
            self,
            consumer: str,
            provider: str,
            extension_id: str
    ) -> None:
        """Unregister a plugin's use of an extension point."""
        if (provider in self.extension_points and
                extension_id in self.extension_points[provider]):
            extension = self.extension_points[provider][extension_id]
            extension.unregister_implementation(consumer)
            self.log(
                f"Unregistered implementation of extension point '{extension_id}' "
                f"from provider '{provider}' by consumer '{consumer}'",
                "debug"
            )

    def get_extension_point(
            self,
            provider: str,
            extension_id: str
    ) -> Optional[ExtensionInterface]:
        """Get an extension point by provider and ID."""
        if provider in self.extension_points and extension_id in self.extension_points[provider]:
            return self.extension_points[provider][extension_id]
        return None

    def get_all_extension_points(self) -> Dict[str, Dict[str, ExtensionInterface]]:
        """Get all registered extension points."""
        return self.extension_points.copy()

    def get_provider_extension_points(self, provider: str) -> Dict[str, ExtensionInterface]:
        """Get all extension points for a specific provider."""
        return self.extension_points.get(provider, {}).copy()

    def register_plugin_extensions(
            self,
            plugin_name: str,
            plugin_instance: Any,
            manifest: PluginManifest
    ) -> None:
        """Register all extension points and uses for a plugin."""
        # Register extension points
        for extension_point in manifest.extension_points:
            self.register_extension_point(
                provider=plugin_name,
                extension_point=extension_point,
                provider_instance=plugin_instance
            )

        # Register extension uses
        for extension_use in manifest.extension_uses:
            provider = extension_use.provider
            extension_id = extension_use.id
            version = extension_use.version
            required = extension_use.required

            # Try to find the implementation in the plugin
            implementation = self._find_extension_implementation(
                plugin_instance, plugin_name, provider, extension_id
            )

            if implementation:
                self.register_extension_use(
                    consumer=plugin_name,
                    consumer_id=f"{plugin_name}.{provider}.{extension_id}",
                    provider=provider,
                    extension_id=extension_id,
                    version=version,
                    implementation=implementation,
                    required=required
                )
            elif required:
                raise ValueError(
                    f"Required extension implementation for '{extension_id}' "
                    f"from provider '{provider}' not found in plugin '{plugin_name}'"
                )

    def unregister_plugin_extensions(self, plugin_name: str) -> None:
        """Unregister all extension points and uses for a plugin."""
        # Unregister extension points
        if plugin_name in self.extension_points:
            for extension_id in list(self.extension_points[plugin_name].keys()):
                self.unregister_extension_point(plugin_name, extension_id)

        # Unregister extension uses
        for provider in list(self.extension_points.keys()):
            for extension_id in list(self.extension_points.get(provider, {}).keys()):
                extension = self.extension_points[provider][extension_id]
                if plugin_name in extension.implementations:
                    self.unregister_extension_use(plugin_name, provider, extension_id)

        # Clean up pending uses
        for key, uses in list(self.pending_uses.items()):
            self.pending_uses[key] = [
                use for use in uses if use[0] != plugin_name
            ]
            if not self.pending_uses[key]:
                del self.pending_uses[key]

    def _is_version_compatible(self, available: str, required: str) -> bool:
        """Check if the available version is compatible with the required version."""
        try:
            import semver
        except ImportError:
            raise ImportError("The 'semver' package is required for version comparison")

        try:
            available_ver = semver.Version.parse(available)
            required_ver = semver.Version.parse(required)

            # Major version must match
            if available_ver.major != required_ver.major:
                return False

            # Available version must be equal or higher
            return available_ver >= required_ver
        except ValueError:
            return False

    def _find_extension_implementation(
            self,
            plugin_instance: Any,
            plugin_name: str,
            provider: str,
            extension_id: str
    ) -> Optional[ExtensionImplementation]:
        """
        Find the implementation of an extension point in a plugin.

        The implementation can be in the following forms:
        1. A method named {provider}_{extension_id} on the plugin instance
        2. A method named implement_{provider}_{extension_id} on the plugin instance
        3. A method named extension_{provider}_{extension_id} on the plugin instance
        """
        # Convert names to snake_case
        provider_snake = provider.replace('-', '_').replace('.', '_')
        extension_snake = extension_id.replace('-', '_').replace('.', '_')

        # Check for method names in different formats
        method_names = [
            f"{provider_snake}_{extension_snake}",
            f"implement_{provider_snake}_{extension_snake}",
            f"extension_{provider_snake}_{extension_snake}"
        ]

        for name in method_names:
            if hasattr(plugin_instance, name) and callable(getattr(plugin_instance, name)):
                return cast(ExtensionImplementation, getattr(plugin_instance, name))

        return None

    def _check_and_resolve_pending_use(
            self,
            provider: str,
            extension_id: str,
            consumer: str,
            consumer_id: str,
            version: str,
            required: bool
    ) -> None:
        """Check if a pending use can be resolved and register it."""
        # Get the plugin manager
        from qorzen.core.plugin_manager import PluginManager
        plugin_manager = None

        # Try to get the plugin manager from imported modules
        for module_name in ["qorzen.core.app", "qorzen.core"]:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "ApplicationCore"):
                    app_core = getattr(module, "ApplicationCore")
                    if hasattr(app_core, "get_manager"):
                        plugin_manager = app_core().get_manager("plugin_manager")
                        break
            except (ImportError, AttributeError):
                continue

        if plugin_manager is None:
            self.log(
                f"Could not resolve pending use of extension point '{extension_id}' "
                f"from provider '{provider}' by consumer '{consumer}': "
                f"plugin manager not found",
                "warning"
            )
            return

        # Get the consumer plugin instance
        consumer_info = plugin_manager.get_plugin_info(consumer)
        if not consumer_info or "instance" not in consumer_info:
            self.log(
                f"Could not resolve pending use of extension point '{extension_id}' "
                f"from provider '{provider}' by consumer '{consumer}': "
                f"consumer plugin instance not found",
                "warning"
            )
            return

        consumer_instance = consumer_info["instance"]

        # Find the implementation
        implementation = self._find_extension_implementation(
            consumer_instance, consumer, provider, extension_id
        )

        if implementation:
            self.register_extension_use(
                consumer=consumer,
                consumer_id=consumer_id,
                provider=provider,
                extension_id=extension_id,
                version=version,
                implementation=implementation,
                required=required
            )
        elif required:
            self.log(
                f"Could not resolve pending use of extension point '{extension_id}' "
                f"from provider '{provider}' by consumer '{consumer}': "
                f"implementation not found",
                "warning"
            )


# Create a singleton instance of the registry
extension_registry = ExtensionRegistry()


def register_extension_point(
        provider: str,
        id: str,
        name: str,
        description: str,
        interface: str,
        version: str = "1.0.0",
        parameters: Optional[Dict[str, Any]] = None,
        provider_instance: Any = None
) -> ExtensionInterface:
    """
    Register an extension point.

    Args:
        provider: The name of the plugin providing the extension point
        id: The unique identifier for the extension point
        name: The human-readable name of the extension point
        description: A description of the extension point
        interface: The interface definition (e.g., function signature or class)
        version: The version of the extension point
        parameters: Additional parameters for the extension point
        provider_instance: The instance of the provider plugin

    Returns:
        The registered extension interface
    """
    extension_point = PluginExtensionPoint(
        id=id,
        name=name,
        description=description,
        interface=interface,
        version=version,
        parameters=parameters or {}
    )

    extension_registry.register_extension_point(
        provider=provider,
        extension_point=extension_point,
        provider_instance=provider_instance
    )

    return extension_registry.get_extension_point(provider, id)


def get_extension_point(provider: str, extension_id: str) -> Optional[ExtensionInterface]:
    """
    Get an extension point.

    Args:
        provider: The name of the plugin providing the extension point
        extension_id: The unique identifier for the extension point

    Returns:
        The extension interface, or None if not found
    """
    return extension_registry.get_extension_point(provider, extension_id)


def call_extension_point(
        provider: str,
        extension_id: str,
        *args: Any,
        **kwargs: Any
) -> Dict[str, Any]:
    """
    Call all implementations of an extension point.

    Args:
        provider: The name of the plugin providing the extension point
        extension_id: The unique identifier for the extension point
        *args: Positional arguments to pass to the implementations
        **kwargs: Keyword arguments to pass to the implementations

    Returns:
        A dictionary mapping plugin names to results

    Raises:
        ExtensionPointNotFoundError: If the extension point is not found
    """
    extension = extension_registry.get_extension_point(provider, extension_id)
    if extension is None:
        raise ExtensionPointNotFoundError(provider, extension_id)

    return extension(*args, **kwargs)


def register_plugin_extensions(
        plugin_name: str,
        plugin_instance: Any,
        manifest: PluginManifest
) -> None:
    """
    Register all extension points and uses for a plugin.

    Args:
        plugin_name: The name of the plugin
        plugin_instance: The instance of the plugin
        manifest: The plugin manifest
    """
    extension_registry.register_plugin_extensions(
        plugin_name=plugin_name,
        plugin_instance=plugin_instance,
        manifest=manifest
    )


def unregister_plugin_extensions(plugin_name: str) -> None:
    """
    Unregister all extension points and uses for a plugin.

    Args:
        plugin_name: The name of the plugin
    """
    extension_registry.unregister_plugin_extensions(plugin_name)