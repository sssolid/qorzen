"""Developer tools for Qorzen plugins.

This module provides utilities for plugin developers, including
template creation, testing tools, and packaging utilities.
"""

from __future__ import annotations

import datetime
import inspect
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from qorzen.plugin_system.manifest import PluginManifest, PluginAuthor, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, SigningKey


def create_plugin_template(
        output_dir: Union[str, Path],
        plugin_name: str,
        display_name: Optional[str] = None,
        description: str = "A Qorzen plugin",
        author_name: str = "Your Name",
        author_email: str = "your.email@example.com",
        author_url: Optional[str] = None,
        version: str = "0.1.0",
        license: str = "MIT",
        force: bool = False
) -> Path:
    """Create a new plugin template.

    This generates a basic plugin structure with the necessary files
    for a Qorzen plugin.

    Args:
        output_dir: Directory where the plugin template will be created
        plugin_name: Unique identifier for the plugin
        display_name: Human-readable name for the plugin
        description: Brief description of the plugin
        author_name: Plugin author's name
        author_email: Plugin author's email
        author_url: Plugin author's website URL
        version: Initial plugin version
        license: License identifier
        force: Whether to overwrite existing files

    Returns:
        Path to the created plugin template directory

    Raises:
        ValueError: If the plugin name is invalid or output directory exists
    """
    output_dir = Path(output_dir)

    # Validate plugin name
    if not plugin_name:
        raise ValueError("Plugin name cannot be empty")

    # Ensure plugin name matches expected format
    import re
    if not re.match(r"^[a-z][a-z0-9_-]{2,63}$", plugin_name):
        raise ValueError(
            "Plugin name must be 3-64 characters, start with a lowercase letter, "
            "and contain only lowercase letters, numbers, underscores, and hyphens"
        )

    # Ensure output directory doesn't exist or force is True
    if output_dir.exists() and not force:
        raise ValueError(f"Output directory already exists: {output_dir}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create plugin structure
    plugin_dir = output_dir / plugin_name
    if plugin_dir.exists() and not force:
        raise ValueError(f"Plugin directory already exists: {plugin_dir}")

    plugin_dir.mkdir(exist_ok=True)

    # Create directories
    dirs = [
        plugin_dir / "code",
        plugin_dir / "resources",
        plugin_dir / "docs",
        plugin_dir / "tests"
    ]

    for d in dirs:
        d.mkdir(exist_ok=True)

    # Create manifest
    display_name = display_name or plugin_name.replace("-", " ").replace("_", " ").title()

    author = PluginAuthor(
        name=author_name,
        email=author_email,
        url=author_url
    )

    manifest = PluginManifest(
        name=plugin_name,
        display_name=display_name,
        version=version,
        description=description,
        author=author,
        license=license,
        entry_point="plugin.py",
        min_core_version="0.1.0",
        capabilities=[],
        dependencies=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        tags=[]
    )

    manifest_path = plugin_dir / "manifest.json"
    manifest.save(manifest_path)

    # Create plugin.py template
    plugin_py_template = f'''"""Qorzen plugin: {display_name}.

{description}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union


class {plugin_name.replace("-", "_").title()}Plugin:
    """Main plugin class for {display_name}.

    This class is the entry point for the plugin and is instantiated
    by the Qorzen plugin manager.
    """

    # Plugin metadata (used by the plugin discovery mechanism)
    name = "{plugin_name}"
    version = "{version}"
    description = "{description}"
    author = "{author_name}"

    def __init__(self) -> None:
        """Initialize the plugin."""
        self.initialized = False
        self.event_bus = None
        self.logger = None
        self.config_provider = None
        self.file_manager = None
        self.thread_manager = None

    def initialize(
        self,
        event_bus_manager: Any,
        logger_provider: Any,
        config_provider: Any,
        file_manager: Any,
        thread_manager: Any
    ) -> None:
        """Initialize the plugin with the provided managers.

        Args:
            event_bus_manager: Event bus manager for subscribing to and publishing events
            logger_provider: Logger provider for creating plugin-specific loggers
            config_provider: Configuration provider for accessing application config
            file_manager: File manager for file operations
            thread_manager: Thread manager for background tasks
        """
        self.event_bus = event_bus
        self.logger = logger_provider.get_logger("{plugin_name}")
        self.config_provider = config_provider
        self.file_manager = file_manager
        self.thread_manager = thread_manager

        self.logger.info(f"{display_name} plugin initialized")
        self.initialized = True

        # Subscribe to events
        self.event_bus_manager.subscribe(
            event_type="ui/ready",
            callback=self._on_ui_ready,
            subscriber_id="{plugin_name}"
        )

    def _on_ui_ready(self, event: Any) -> None:
        """Handle UI ready event.

        Args:
            event: Event object
        """
        self.logger.info(f"{display_name} received UI ready event")

        # Integrate with the UI
        # Example: Add menu items, toolbar buttons, etc.
        main_window = event.payload.get("main_window")
        if main_window:
            self.logger.info("Main window available for UI integration")

    def shutdown(self) -> None:
        """Shut down the plugin.

        This method is called when the plugin is being unloaded.
        """
        if self.event_bus_manager:
            self.event_bus_manager.unsubscribe("{plugin_name}")

        if self.logger:
            self.logger.info(f"{display_name} plugin shutting down")

        self.initialized = False
'''

    plugin_py_path = plugin_dir / "code" / "plugin.py"
    with open(plugin_py_path, "w") as f:
        f.write(plugin_py_template)

    # Create README.md
    readme_template = f'''# {display_name}

{description}

## Installation

1. Download the plugin package
2. Open Qorzen
3. Go to Settings > Plugins
4. Click "Install from file" and select the plugin package
5. Restart Qorzen

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

Describe how to use the plugin.

## Configuration

Describe any configuration options for the plugin.

## License

{license}

## Author

{author_name} ({author_email})
'''

    readme_path = plugin_dir / "docs" / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_template)

    # Create LICENSE file based on license type
    license_template = ""
    if license.lower() == "mit":
        current_year = datetime.datetime.now().year
        license_template = f'''MIT License

Copyright (c) {current_year} {author_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

    if license_template:
        license_path = plugin_dir / "LICENSE"
        with open(license_path, "w") as f:
            f.write(license_template)

    # Create a simple test file
    test_template = f'''"""Tests for the {display_name} plugin."""

from __future__ import annotations

import unittest
from unittest import mock


class Test{plugin_name.replace("-", "_").title()}Plugin(unittest.TestCase):
    """Test cases for the {display_name} plugin."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        from code.plugin import {plugin_name.replace("-", "_").title()}Plugin

        # Create mock dependencies
        self.event_bus = mock.MagicMock()
        self.logger = mock.MagicMock()
        self.logger_provider = mock.MagicMock()
        self.logger_provider.get_logger.return_value = self.logger
        self.config_provider = mock.MagicMock()
        self.file_manager = mock.MagicMock()
        self.thread_manager = mock.MagicMock()

        # Initialize plugin
        self.plugin = {plugin_name.replace("-", "_").title()}Plugin()
        self.plugin.initialize(
            self.event_bus,
            self.logger_provider,
            self.config_provider,
            self.file_manager,
            self.thread_manager
        )

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        self.plugin.shutdown()

    def test_initialization(self) -> None:
        """Test plugin initialization."""
        self.assertTrue(self.plugin.initialized)
        self.logger.info.assert_called()
        self.event_bus_manager.subscribe.assert_called()


if __name__ == "__main__":
    unittest.main()
'''

    test_path = plugin_dir / "tests" / f"test_{plugin_name.replace('-', '_')}.py"
    with open(test_path, "w") as f:
        f.write(test_template)

    return plugin_dir


def package_plugin(
        plugin_dir: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        format: PackageFormat = PackageFormat.ZIP,
        signing_key: Optional[Union[SigningKey, Path]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
) -> Path:
    """Package a plugin directory into a distributable package.

    Args:
        plugin_dir: Directory containing the plugin
        output_path: Path where the package will be created
        format: Package format
        signing_key: Signing key or path to a key file
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude

    Returns:
        Path to the created package

    Raises:
        ValueError: If plugin directory is invalid
    """
    plugin_dir = Path(plugin_dir)

    # Check if plugin directory exists
    if not plugin_dir.exists() or not plugin_dir.is_dir():
        raise ValueError(f"Plugin directory not found: {plugin_dir}")

    # Check for manifest file
    manifest_path = plugin_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Manifest file not found: {manifest_path}")

    # Load manifest
    try:
        manifest = PluginManifest.load(manifest_path)
    except Exception as e:
        raise ValueError(f"Failed to load manifest: {e}")

    # Determine output path if not provided
    if output_path is None:
        if format == PackageFormat.ZIP:
            output_path = f"{manifest.name}-{manifest.version}.zip"
        elif format == PackageFormat.WHEEL:
            output_path = f"{manifest.name}-{manifest.version}.whl"
        else:
            output_path = f"{manifest.name}-{manifest.version}"

    output_path = Path(output_path)

    # Sign manifest if signing key provided
    if signing_key is not None:
        if isinstance(signing_key, Path) or isinstance(signing_key, str):
            try:
                key = PluginSigner.load_key(signing_key)
            except Exception as e:
                raise ValueError(f"Failed to load signing key: {e}")
        else:
            key = signing_key

        signer = PluginSigner(key)
        signer.sign_manifest(manifest)

        # Save signed manifest back to file
        manifest.save(manifest_path)

    # Create package
    try:
        package = PluginPackage.create(
            source_dir=plugin_dir,
            output_path=output_path,
            manifest=manifest,
            format=format,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )

        print(f"Created {format.value} package at: {output_path}")
        return output_path

    except Exception as e:
        raise ValueError(f"Failed to create package: {e}")


def test_plugin(
        plugin_dir: Union[str, Path],
        mock_env: bool = True,
        test_pattern: str = "test_*.py"
) -> bool:
    """Run tests for a plugin.

    Args:
        plugin_dir: Directory containing the plugin
        mock_env: Whether to use a mocked Qorzen environment
        test_pattern: Pattern for test files

    Returns:
        True if all tests pass, False otherwise
    """
    plugin_dir = Path(plugin_dir)

    # Check if plugin directory exists
    if not plugin_dir.exists() or not plugin_dir.is_dir():
        raise ValueError(f"Plugin directory not found: {plugin_dir}")

    # Find test directory
    test_dir = plugin_dir / "tests"
    if not test_dir.exists() or not test_dir.is_dir():
        raise ValueError(f"Test directory not found: {test_dir}")

    # Check for manifest file
    manifest_path = plugin_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Manifest file not found: {manifest_path}")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Copy plugin files to temporary directory
        for item in plugin_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, temp_path / item.name)
            else:
                shutil.copy2(item, temp_path / item.name)

        # Run tests
        import unittest

        # Add temporary directory to Python path
        import sys
        sys.path.insert(0, str(temp_path))

        try:
            # Discover and run tests
            test_loader = unittest.TestLoader()
            test_suite = test_loader.discover(str(temp_path / "tests"), pattern=test_pattern)

            test_runner = unittest.TextTestRunner(verbosity=2)
            result = test_runner.run(test_suite)

            return result.wasSuccessful()

        finally:
            # Remove temporary directory from Python path
            sys.path.remove(str(temp_path))


def validate_plugin(plugin_dir: Union[str, Path]) -> Dict[str, List[str]]:
    """Validate a plugin directory.

    This checks for common issues and best practices.

    Args:
        plugin_dir: Directory containing the plugin

    Returns:
        Dictionary of validation issues by category (errors, warnings, info)
    """
    plugin_dir = Path(plugin_dir)

    # Result categories
    issues = {
        "errors": [],
        "warnings": [],
        "info": []
    }

    # Check if plugin directory exists
    if not plugin_dir.exists() or not plugin_dir.is_dir():
        issues["errors"].append(f"Plugin directory not found: {plugin_dir}")
        return issues

    # Check for manifest file
    manifest_path = plugin_dir / "manifest.json"
    if not manifest_path.exists():
        issues["errors"].append(f"Manifest file not found: {manifest_path}")
    else:
        # Load and validate manifest
        try:
            manifest = PluginManifest.load(manifest_path)

            # Check plugin name
            if not manifest.name:
                issues["errors"].append("Plugin name is empty")

            # Check version
            if not manifest.version:
                issues["errors"].append("Plugin version is empty")

            # Check description
            if not manifest.description:
                issues["warnings"].append("Plugin description is empty")

            # Check entry point
            if not manifest.entry_point:
                issues["errors"].append("Plugin entry point is empty")

            # Check capabilities
            capabilities = manifest.capabilities
            if not capabilities:
                issues["info"].append("Plugin has no capabilities declared")
            else:
                high_risk = False
                for capability in capabilities:
                    if PluginCapability.get_risk_level(capability) == "high":
                        high_risk = True

                if high_risk:
                    issues["warnings"].append("Plugin requests high-risk capabilities")

            # Check dependencies
            dependencies = manifest.dependencies
            if dependencies:
                for dep in dependencies:
                    if not dep.name:
                        issues["errors"].append("Dependency name is empty")
                    if not dep.version:
                        issues["warnings"].append(f"No version specified for dependency: {dep.name}")

        except Exception as e:
            issues["errors"].append(f"Failed to load manifest: {e}")

    # Check for required directories
    for dir_name in ["code", "docs", "resources"]:
        dir_path = plugin_dir / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            issues["warnings"].append(f"Missing directory: {dir_name}")

    # Check for entry point file
    code_dir = plugin_dir / "code"
    if code_dir.exists() and code_dir.is_dir():
        # Look for common entry point files
        entry_points = ["plugin.py", "__init__.py", "main.py"]
        found = False
        for entry_point in entry_points:
            if (code_dir / entry_point).exists():
                found = True
                break

        if not found:
            issues["warnings"].append("No entry point file found in code directory")

    # Check for README
    readme_paths = [
        plugin_dir / "README.md",
        plugin_dir / "docs" / "README.md",
        plugin_dir / "README.rst",
        plugin_dir / "docs" / "README.rst",
        plugin_dir / "README.txt",
        plugin_dir / "docs" / "README.txt"
    ]

    readme_found = False
    for path in readme_paths:
        if path.exists():
            readme_found = True
            break

    if not readme_found:
        issues["warnings"].append("No README file found")

    # Check for LICENSE
    license_found = False
    license_paths = [
        plugin_dir / "LICENSE",
        plugin_dir / "LICENSE.txt",
        plugin_dir / "LICENSE.md"
    ]

    for path in license_paths:
        if path.exists():
            license_found = True
            break

    if not license_found:
        issues["warnings"].append("No LICENSE file found")

    # Check for tests
    tests_dir = plugin_dir / "tests"
    if not tests_dir.exists() or not tests_dir.is_dir():
        issues["warnings"].append("No tests directory found")
    else:
        test_files = list(tests_dir.glob("test_*.py"))
        if not test_files:
            issues["warnings"].append("No test files found in tests directory")

    return issues


def create_plugin_signing_key(name: str, output_path: Union[str, Path]) -> SigningKey:
    """Create a new plugin signing key.

    Args:
        name: Name for the key
        output_path: Path where the key will be saved

    Returns:
        Created signing key
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    signer = PluginSigner()
    key = signer.key

    # Save the key
    signer.save_key(output_path, include_private=True)

    return key