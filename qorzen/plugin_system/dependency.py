from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from qorzen.plugin_system.manifest import PluginManifest, PluginDependency
from qorzen.plugin_system.repository import PluginRepositoryManager


class DependencyError(Exception):
    """Base class for dependency resolution errors."""
    pass


class CircularDependencyError(DependencyError):
    """Error raised when a circular dependency is detected."""

    def __init__(self, dependency_chain: List[str]):
        self.dependency_chain = dependency_chain
        cycle = " -> ".join(dependency_chain)
        super().__init__(f"Circular dependency detected: {cycle}")


class MissingDependencyError(DependencyError):
    """Error raised when a required dependency is missing."""

    def __init__(self, plugin_name: str, dependency_name: str, required_version: str):
        self.plugin_name = plugin_name
        self.dependency_name = dependency_name
        self.required_version = required_version
        super().__init__(
            f"Missing dependency: {plugin_name} requires {dependency_name} "
            f"version {required_version}"
        )


class IncompatibleVersionError(DependencyError):
    """Error raised when a dependency has an incompatible version."""

    def __init__(
            self,
            plugin_name: str,
            dependency_name: str,
            required_version: str,
            available_version: str
    ):
        self.plugin_name = plugin_name
        self.dependency_name = dependency_name
        self.required_version = required_version
        self.available_version = available_version
        super().__init__(
            f"Incompatible version: {plugin_name} requires {dependency_name} "
            f"version {required_version}, but {available_version} is available"
        )


@dataclass
class DependencyNode:
    """Node in the dependency graph."""

    name: str
    version: str
    dependencies: List[PluginDependency] = field(default_factory=list)
    manifest: Optional[PluginManifest] = None
    repository: Optional[str] = None
    local_path: Optional[Path] = None

    @property
    def is_local(self) -> bool:
        """Check if the plugin is available locally."""
        return self.local_path is not None

    @property
    def is_core(self) -> bool:
        """Check if the plugin is the core system."""
        return self.name == "core"


@dataclass
class DependencyGraph:
    """Dependency graph for resolving plugin dependencies."""

    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    resolved: List[str] = field(default_factory=list)
    edges: Dict[str, List[str]] = field(default_factory=dict)

    def add_node(self, node: DependencyNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.name] = node
        if node.name not in self.edges:
            self.edges[node.name] = []

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add an edge between nodes."""
        if from_node not in self.edges:
            self.edges[from_node] = []
        if to_node not in self.edges[from_node]:
            self.edges[from_node].append(to_node)

    def get_dependencies(self, node_name: str) -> List[str]:
        """Get the dependencies of a node."""
        return self.edges.get(node_name, [])

    def resolve(self) -> List[str]:
        """Resolve the dependency graph, returning the nodes in dependency order."""
        self.resolved = []
        for node_name in self.nodes:
            if node_name not in self.resolved:
                self._resolve_node(node_name, [])
        return self.resolved

    def _resolve_node(self, node_name: str, resolved_path: List[str]) -> None:
        """Resolve a node's dependencies."""
        # Check for circular dependencies
        if node_name in resolved_path:
            cycle_path = resolved_path[resolved_path.index(node_name):] + [node_name]
            raise CircularDependencyError(cycle_path)

        # Skip if already resolved
        if node_name in self.resolved:
            return

        # Skip if node doesn't exist (should not happen)
        if node_name not in self.nodes:
            return

        # Add to path
        new_path = resolved_path + [node_name]

        # Resolve dependencies first
        for dep in self.get_dependencies(node_name):
            if dep not in self.resolved:
                self._resolve_node(dep, new_path)

        # Add to resolved list
        self.resolved.append(node_name)


class DependencyResolver:
    """Resolver for plugin dependencies."""

    def __init__(
            self,
            repository_manager: Optional[PluginRepositoryManager] = None,
            logger: Optional[Callable[[str, str], None]] = None
    ):
        self.repository_manager = repository_manager
        self.logger = logger or (lambda msg, level: None)
        self.plugins_dir: Optional[Path] = None
        self.installed_plugins: Dict[str, PluginManifest] = {}
        self.core_version: str = "0.1.0"

    def set_plugins_dir(self, plugins_dir: Union[str, Path]) -> None:
        """Set the plugins directory."""
        self.plugins_dir = Path(plugins_dir)

    def set_core_version(self, version: str) -> None:
        """Set the core version."""
        self.core_version = version

    def set_installed_plugins(self, plugins: Dict[str, PluginManifest]) -> None:
        """Set the installed plugins."""
        self.installed_plugins = plugins

    def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        if self.logger:
            self.logger(message, level)

    def resolve_dependencies(
            self,
            plugin_manifest: PluginManifest,
            resolve_transitives: bool = True,
            fetch_missing: bool = False
    ) -> List[Tuple[str, str, bool]]:
        """
        Resolve plugin dependencies.

        Args:
            plugin_manifest: The manifest of the plugin to resolve dependencies for
            resolve_transitives: Whether to resolve transitive dependencies
            fetch_missing: Whether to fetch missing dependencies from repositories

        Returns:
            A list of tuples (plugin_name, version, is_local) for dependencies
            in the order they should be loaded

        Raises:
            DependencyError: If there's an error resolving dependencies
        """
        # Build the dependency graph
        graph = DependencyGraph()

        # Add the plugin as the root node
        root_node = DependencyNode(
            name=plugin_manifest.name,
            version=plugin_manifest.version,
            dependencies=plugin_manifest.dependencies,
            manifest=plugin_manifest
        )
        graph.add_node(root_node)

        # Add the core as a node
        core_node = DependencyNode(name="core", version=self.core_version)
        graph.add_node(core_node)

        # Process the plugin's dependencies
        self._process_dependencies(
            graph=graph,
            node=root_node,
            resolve_transitives=resolve_transitives,
            fetch_missing=fetch_missing,
            visited=set()
        )

        # Resolve the graph
        try:
            resolved = graph.resolve()
        except CircularDependencyError as e:
            self.log(f"Circular dependency detected: {' -> '.join(e.dependency_chain)}", "error")
            raise

        # Convert to result format, excluding the root plugin
        result = []
        for name in resolved:
            if name != plugin_manifest.name:
                node = graph.nodes[name]
                result.append((name, node.version, node.is_local))

        return result

    def _process_dependencies(
            self,
            graph: DependencyGraph,
            node: DependencyNode,
            resolve_transitives: bool,
            fetch_missing: bool,
            visited: Set[str]
    ) -> None:
        """Process the dependencies of a node."""
        # Mark as visited to avoid duplicate processing
        visited.add(node.name)

        for dependency in node.dependencies:
            dep_name = dependency.name
            dep_version = dependency.version
            dep_optional = dependency.optional
            dep_url = dependency.url

            # Skip if it's an optional dependency and we're not fetching missing ones
            if dep_optional and not fetch_missing:
                continue

            # Skip core dependency (it's always available)
            if dep_name == "core":
                graph.add_edge(node.name, "core")
                continue

            # Check if already in the graph
            if dep_name in graph.nodes:
                dep_node = graph.nodes[dep_name]

                # Check version compatibility
                if not self._is_version_compatible(
                        dep_node.version,
                        dep_version,
                        dependency
                ):
                    if dep_optional:
                        self.log(
                            f"Optional dependency {dep_name} version {dep_version} is "
                            f"incompatible with available version {dep_node.version}",
                            "warning"
                        )
                        continue
                    else:
                        raise IncompatibleVersionError(
                            node.name, dep_name, dep_version, dep_node.version
                        )

                # Add the edge
                graph.add_edge(node.name, dep_name)
                continue

            # Check if it's installed
            if dep_name in self.installed_plugins:
                dep_manifest = self.installed_plugins[dep_name]

                # Check version compatibility
                if not self._is_version_compatible(
                        dep_manifest.version,
                        dep_version,
                        dependency
                ):
                    if dep_optional:
                        self.log(
                            f"Optional dependency {dep_name} version {dep_version} is "
                            f"incompatible with installed version {dep_manifest.version}",
                            "warning"
                        )
                        continue
                    else:
                        raise IncompatibleVersionError(
                            node.name, dep_name, dep_version, dep_manifest.version
                        )

                # Add the dependency node
                dep_node = DependencyNode(
                    name=dep_name,
                    version=dep_manifest.version,
                    dependencies=dep_manifest.dependencies,
                    manifest=dep_manifest,
                    local_path=self.plugins_dir / dep_name if self.plugins_dir else None
                )
                graph.add_node(dep_node)
                graph.add_edge(node.name, dep_name)

                # Process transitive dependencies
                if resolve_transitives and dep_name not in visited:
                    self._process_dependencies(
                        graph=graph,
                        node=dep_node,
                        resolve_transitives=resolve_transitives,
                        fetch_missing=fetch_missing,
                        visited=visited
                    )

                continue

            # Try to fetch the dependency if missing
            if fetch_missing and self.repository_manager:
                try:
                    # Determine which repository to use
                    if dep_url:
                        # Parse the URL to extract repository and package info
                        repo_name, package_info = self._parse_dependency_url(dep_url)
                        if repo_name:
                            # Use the specified repository
                            repo = self.repository_manager.get_repository(repo_name)
                            # Extract version from package_info if available
                            if "@" in package_info:
                                pkg_name, version = package_info.split("@", 1)
                                download_path = repo.download_plugin(
                                    plugin_name=pkg_name,
                                    version=version
                                )
                            else:
                                download_path = repo.download_plugin(
                                    plugin_name=package_info
                                )
                        else:
                            # Direct URL to package
                            raise NotImplementedError(
                                "Direct URL downloads not implemented yet"
                            )
                    else:
                        # Use the default repository
                        download_path = self.repository_manager.download_plugin(
                            plugin_name=dep_name
                        )

                    # Load the downloaded package
                    from qorzen.plugin_system.package import PluginPackage
                    package = PluginPackage.load(download_path)

                    if not package.manifest:
                        raise ValueError(f"Downloaded package for {dep_name} has no manifest")

                    dep_manifest = package.manifest

                    # Check version compatibility
                    if not self._is_version_compatible(
                            dep_manifest.version,
                            dep_version,
                            dependency
                    ):
                        if dep_optional:
                            self.log(
                                f"Optional dependency {dep_name} version {dep_version} is "
                                f"incompatible with downloaded version {dep_manifest.version}",
                                "warning"
                            )
                            continue
                        else:
                            raise IncompatibleVersionError(
                                node.name, dep_name, dep_version, dep_manifest.version
                            )

                    # Add the dependency node
                    dep_node = DependencyNode(
                        name=dep_name,
                        version=dep_manifest.version,
                        dependencies=dep_manifest.dependencies,
                        manifest=dep_manifest,
                        repository=repo_name if 'repo_name' in locals() else None,
                        local_path=download_path
                    )
                    graph.add_node(dep_node)
                    graph.add_edge(node.name, dep_name)

                    # Process transitive dependencies
                    if resolve_transitives and dep_name not in visited:
                        self._process_dependencies(
                            graph=graph,
                            node=dep_node,
                            resolve_transitives=resolve_transitives,
                            fetch_missing=fetch_missing,
                            visited=visited
                        )

                    continue

                except Exception as e:
                    self.log(f"Failed to fetch dependency {dep_name}: {str(e)}", "error")
                    if not dep_optional:
                        raise MissingDependencyError(
                            node.name, dep_name, dep_version
                        ) from e

            # Dependency not found
            if not dep_optional:
                raise MissingDependencyError(node.name, dep_name, dep_version)
            else:
                self.log(
                    f"Optional dependency {dep_name} version {dep_version} not found",
                    "warning"
                )

    def _is_version_compatible(
            self,
            available_version: str,
            required_version: str,
            dependency: PluginDependency
    ) -> bool:
        """Check if the available version is compatible with the required version."""
        try:
            import semver
        except ImportError:
            self.log(
                "The 'semver' package is required for version comparison. "
                "Assuming versions are compatible.",
                "warning"
            )
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
                return (available_ver >= required_ver and
                        available_ver.major == required_ver.major)
            else:
                return False
        except Exception as e:
            self.log(f"Error comparing versions: {str(e)}", "warning")
            return False

    def _parse_dependency_url(self, url: str) -> Tuple[Optional[str], str]:
        """
        Parse a dependency URL.

        Format can be:
        - repo:plugin_name[@version]
        - http://url/to/package.zip

        Returns:
            A tuple (repository_name, package_info) or (None, direct_url)
        """
        if url.startswith("http://") or url.startswith("https://"):
            # Direct URL
            return None, url

        if ":" in url:
            # Repository format
            repo, package = url.split(":", 1)
            return repo, package

        # Default repository format
        return "default", url

    def get_dependency_graph(
            self,
            plugin_manifests: Dict[str, PluginManifest]
    ) -> DependencyGraph:
        """
        Build a dependency graph for multiple plugins.

        Args:
            plugin_manifests: A dictionary mapping plugin names to manifests

        Returns:
            A dependency graph
        """
        graph = DependencyGraph()

        # Add the core as a node
        core_node = DependencyNode(name="core", version=self.core_version)
        graph.add_node(core_node)

        # Add all plugins as nodes
        for name, manifest in plugin_manifests.items():
            node = DependencyNode(
                name=name,
                version=manifest.version,
                dependencies=manifest.dependencies,
                manifest=manifest,
                local_path=self.plugins_dir / name if self.plugins_dir else None
            )
            graph.add_node(node)

            # Add edges for dependencies
            for dep in manifest.dependencies:
                dep_name = dep.name
                if dep_name in plugin_manifests or dep_name == "core":
                    graph.add_edge(name, dep_name)

        return graph

    def resolve_plugin_order(
            self,
            plugin_manifests: Dict[str, PluginManifest]
    ) -> List[str]:
        """
        Resolve the order in which plugins should be loaded.

        Args:
            plugin_manifests: A dictionary mapping plugin names to manifests

        Returns:
            A list of plugin names in the order they should be loaded

        Raises:
            CircularDependencyError: If a circular dependency is detected
        """
        graph = self.get_dependency_graph(plugin_manifests)

        try:
            resolved = graph.resolve()
        except CircularDependencyError as e:
            self.log(f"Circular dependency detected: {' -> '.join(e.dependency_chain)}", "error")
            raise

        # Filter out the core node
        return [name for name in resolved if name != "core"]