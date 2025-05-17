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
def create_plugin_template(output_dir: Union[str, Path], plugin_name: str, display_name: Optional[str]=None, description: str='A Qorzen plugin', author_name: str='Your Name', author_email: str='your.email@example.com', author_url: Optional[str]=None, version: str='0.1.0', license: str='MIT', force: bool=False) -> Path:
    output_dir = Path(output_dir)
    if not plugin_name:
        raise ValueError('Plugin name cannot be empty')
    import re
    if not re.match('^[a-z][a-z0-9_-]{2,63}$', plugin_name):
        raise ValueError('Plugin name must be 3-64 characters, start with a lowercase letter, and contain only lowercase letters, numbers, underscores, and hyphens')
    if output_dir.exists() and (not force):
        raise ValueError(f'Output directory already exists: {output_dir}')
    output_dir.mkdir(parents=True, exist_ok=True)
    plugin_dir = output_dir / plugin_name
    if plugin_dir.exists() and (not force):
        raise ValueError(f'Plugin directory already exists: {plugin_dir}')
    plugin_dir.mkdir(exist_ok=True)
    dirs = [plugin_dir / 'code', plugin_dir / 'resources', plugin_dir / 'docs', plugin_dir / 'tests']
    for d in dirs:
        d.mkdir(exist_ok=True)
    display_name = display_name or plugin_name.replace('-', ' ').replace('_', ' ').title()
    author = PluginAuthor(name=author_name, email=author_email, url=author_url)
    manifest = PluginManifest(name=plugin_name, display_name=display_name, version=version, description=description, author=author, license=license, entry_point='plugin.py', min_core_version='0.1.0', capabilities=[], dependencies=[], created_at=datetime.datetime.now(), updated_at=datetime.datetime.now(), tags=[])
    manifest_path = plugin_dir / 'manifest.json'
    manifest.save(manifest_path)
    plugin_py_template = f'''"""Qorzen plugin: {display_name}.\n\n{description}\n"""\n\nfrom __future__ import annotations\n\nfrom typing import Any, Dict, List, Optional, Union\n\n\nclass {plugin_name.replace('-', '_').title()}Plugin:\n    """Main plugin class for {display_name}.\n\n    This class is the entry point for the plugin and is instantiated\n    by the Qorzen plugin manager.\n    """\n\n    # Plugin metadata (used by the plugin discovery mechanism)\n    name = "{plugin_name}"\n    version = "{version}"\n    description = "{description}"\n    author = "{author_name}"\n\n    def __init__(self) -> None:\n        """Initialize the plugin."""\n        self.initialized = False\n        self.event_bus_manager = None\n        self.logger = None\n        self.config_provider = None\n        self.file_manager = None\n        self.thread_manager = None\n\n    def initialize(\n        self,\n        event_bus_manager: Any,\n        logger_provider: Any,\n        config_provider: Any,\n        file_manager: Any,\n        thread_manager: Any\n    ) -> None:\n        """Initialize the plugin with the provided managers.\n\n        Args:\n            event_bus_manager: Event bus manager for subscribing to and publishing events\n            logger_provider: Logger provider for creating plugin-specific loggers\n            config_provider: Configuration provider for accessing application config\n            file_manager: File manager for file operations\n            thread_manager: Thread manager for background tasks\n        """\n        self.event_bus_manager = event_bus_manager\n        self.logger = logger_provider.get_logger("{plugin_name}")\n        self.config_provider = config_provider\n        self.file_manager = file_manager\n        self.thread_manager = thread_manager\n\n        self.logger.info(f"{display_name} plugin initialized")\n        self.initialized = True\n\n        # Subscribe to events\n        self.event_bus_manager.subscribe(\n            event_type="ui/ready",\n            callback=self._on_ui_ready,\n            subscriber_id="{plugin_name}"\n        )\n\n    def _on_ui_ready(self, event: Any) -> None:\n        """Handle UI ready event.\n\n        Args:\n            event: Event object\n        """\n        self.logger.info(f"{display_name} received UI ready event")\n\n        # Integrate with the UI\n        # Example: Add menu items, toolbar buttons, etc.\n        main_window = event.payload.get("main_window")\n        if main_window:\n            self.logger.info("Main window available for UI integration")\n\n    def shutdown(self) -> None:\n        """Shut down the plugin.\n\n        This method is called when the plugin is being unloaded.\n        """\n        if self.event_bus_manager:\n            self.event_bus_manager.unsubscribe("{plugin_name}")\n\n        if self.logger:\n            self.logger.info(f"{display_name} plugin shutting down")\n\n        self.initialized = False\n'''
    plugin_py_path = plugin_dir / 'code' / 'plugin.py'
    with open(plugin_py_path, 'w') as f:
        f.write(plugin_py_template)
    readme_template = f'# {display_name}\n\n{description}\n\n## Installation\n\n1. Download the plugin package\n2. Open Qorzen\n3. Go to Settings > Plugins\n4. Click "Install from file" and select the plugin package\n5. Restart Qorzen\n\n## Features\n\n- Feature 1\n- Feature 2\n- Feature 3\n\n## Usage\n\nDescribe how to use the plugin.\n\n## Configuration\n\nDescribe any configuration options for the plugin.\n\n## License\n\n{license}\n\n## Author\n\n{author_name} ({author_email})\n'
    readme_path = plugin_dir / 'docs' / 'README.md'
    with open(readme_path, 'w') as f:
        f.write(readme_template)
    license_template = ''
    if license.lower() == 'mit':
        current_year = datetime.datetime.now().year
        license_template = f'MIT License\n\nCopyright (c) {current_year} {author_name}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n'
    if license_template:
        license_path = plugin_dir / 'LICENSE'
        with open(license_path, 'w') as f:
            f.write(license_template)
    test_template = f'''"""Tests for the {display_name} plugin."""\n\nfrom __future__ import annotations\n\nimport unittest\nfrom unittest import mock\n\n\nclass Test{plugin_name.replace('-', '_').title()}Plugin(unittest.TestCase):\n    """Test cases for the {display_name} plugin."""\n\n    def setUp(self) -> None:\n        """Set up test fixtures."""\n        from code.plugin import {plugin_name.replace('-', '_').title()}Plugin\n\n        # Create mock dependencies\n        self.event_bus_manager = mock.MagicMock()\n        self.logger = mock.MagicMock()\n        self.logger_provider = mock.MagicMock()\n        self.logger_provider.get_logger.return_value = self.logger\n        self.config_provider = mock.MagicMock()\n        self.file_manager = mock.MagicMock()\n        self.thread_manager = mock.MagicMock()\n\n        # Initialize plugin\n        self.plugin = {plugin_name.replace('-', '_').title()}Plugin()\n        self.plugin.initialize(\n            self.event_bus,\n            self.logger_provider,\n            self.config_provider,\n            self.file_manager,\n            self.thread_manager\n        )\n\n    def tearDown(self) -> None:\n        """Tear down test fixtures."""\n        self.plugin.shutdown()\n\n    def test_initialization(self) -> None:\n        """Test plugin initialization."""\n        self.assertTrue(self.plugin.initialized)\n        self.logger.info.assert_called()\n        self.event_bus_manager.subscribe.assert_called()\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
    test_path = plugin_dir / 'tests' / f"test_{plugin_name.replace('-', '_')}.py"
    with open(test_path, 'w') as f:
        f.write(test_template)
    return plugin_dir
def package_plugin(plugin_dir: Union[str, Path], output_path: Optional[Union[str, Path]]=None, format: PackageFormat=PackageFormat.ZIP, signing_key: Optional[Union[SigningKey, Path]]=None, include_patterns: Optional[List[str]]=None, exclude_patterns: Optional[List[str]]=None) -> Path:
    plugin_dir = Path(plugin_dir)
    if not plugin_dir.exists() or not plugin_dir.is_dir():
        raise ValueError(f'Plugin directory not found: {plugin_dir}')
    manifest_path = plugin_dir / 'manifest.json'
    if not manifest_path.exists():
        raise ValueError(f'Manifest file not found: {manifest_path}')
    try:
        manifest = PluginManifest.load(manifest_path)
    except Exception as e:
        raise ValueError(f'Failed to load manifest: {e}')
    if output_path is None:
        if format == PackageFormat.ZIP:
            output_path = f'{manifest.name}-{manifest.version}.zip'
        elif format == PackageFormat.WHEEL:
            output_path = f'{manifest.name}-{manifest.version}.whl'
        else:
            output_path = f'{manifest.name}-{manifest.version}'
    output_path = Path(output_path)
    if signing_key is not None:
        if isinstance(signing_key, Path) or isinstance(signing_key, str):
            try:
                key = PluginSigner.load_key(signing_key)
            except Exception as e:
                raise ValueError(f'Failed to load signing key: {e}')
        else:
            key = signing_key
        signer = PluginSigner(key)
        signer.sign_manifest(manifest)
        manifest.save(manifest_path)
    try:
        package = PluginPackage.create(source_dir=plugin_dir, output_path=output_path, manifest=manifest, format=format, include_patterns=include_patterns, exclude_patterns=exclude_patterns)
        print(f'Created {format.value} package at: {output_path}')
        return output_path
    except Exception as e:
        raise ValueError(f'Failed to create package: {e}')
def test_plugin(plugin_dir: Union[str, Path], mock_env: bool=True, test_pattern: str='test_*.py') -> bool:
    plugin_dir = Path(plugin_dir)
    if not plugin_dir.exists() or not plugin_dir.is_dir():
        raise ValueError(f'Plugin directory not found: {plugin_dir}')
    test_dir = plugin_dir / 'tests'
    if not test_dir.exists() or not test_dir.is_dir():
        raise ValueError(f'Test directory not found: {test_dir}')
    manifest_path = plugin_dir / 'manifest.json'
    if not manifest_path.exists():
        raise ValueError(f'Manifest file not found: {manifest_path}')
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for item in plugin_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, temp_path / item.name)
            else:
                shutil.copy2(item, temp_path / item.name)
        import unittest
        import sys
        sys.path.insert(0, str(temp_path))
        try:
            test_loader = unittest.TestLoader()
            test_suite = test_loader.discover(str(temp_path / 'tests'), pattern=test_pattern)
            test_runner = unittest.TextTestRunner(verbosity=2)
            result = test_runner.run(test_suite)
            return result.wasSuccessful()
        finally:
            sys.path.remove(str(temp_path))
def validate_plugin(plugin_dir: Union[str, Path]) -> Dict[str, List[str]]:
    plugin_dir = Path(plugin_dir)
    issues = {'errors': [], 'warnings': [], 'info': []}
    if not plugin_dir.exists() or not plugin_dir.is_dir():
        issues['errors'].append(f'Plugin directory not found: {plugin_dir}')
        return issues
    manifest_path = plugin_dir / 'manifest.json'
    if not manifest_path.exists():
        issues['errors'].append(f'Manifest file not found: {manifest_path}')
    else:
        try:
            manifest = PluginManifest.load(manifest_path)
            if not manifest.name:
                issues['errors'].append('Plugin name is empty')
            if not manifest.version:
                issues['errors'].append('Plugin version is empty')
            if not manifest.description:
                issues['warnings'].append('Plugin description is empty')
            if not manifest.entry_point:
                issues['errors'].append('Plugin entry point is empty')
            capabilities = manifest.capabilities
            if not capabilities:
                issues['info'].append('Plugin has no capabilities declared')
            else:
                high_risk = False
                for capability in capabilities:
                    if PluginCapability.get_risk_level(capability) == 'high':
                        high_risk = True
                if high_risk:
                    issues['warnings'].append('Plugin requests high-risk capabilities')
            dependencies = manifest.dependencies
            if dependencies:
                for dep in dependencies:
                    if not dep.name:
                        issues['errors'].append('Dependency name is empty')
                    if not dep.version:
                        issues['warnings'].append(f'No version specified for dependency: {dep.name}')
        except Exception as e:
            issues['errors'].append(f'Failed to load manifest: {e}')
    for dir_name in ['code', 'docs', 'resources']:
        dir_path = plugin_dir / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            issues['warnings'].append(f'Missing directory: {dir_name}')
    code_dir = plugin_dir / 'code'
    if code_dir.exists() and code_dir.is_dir():
        entry_points = ['plugin.py', '__init__.py', 'main.py']
        found = False
        for entry_point in entry_points:
            if (code_dir / entry_point).exists():
                found = True
                break
        if not found:
            issues['warnings'].append('No entry point file found in code directory')
    readme_paths = [plugin_dir / 'README.md', plugin_dir / 'docs' / 'README.md', plugin_dir / 'README.rst', plugin_dir / 'docs' / 'README.rst', plugin_dir / 'README.txt', plugin_dir / 'docs' / 'README.txt']
    readme_found = False
    for path in readme_paths:
        if path.exists():
            readme_found = True
            break
    if not readme_found:
        issues['warnings'].append('No README file found')
    license_found = False
    license_paths = [plugin_dir / 'LICENSE', plugin_dir / 'LICENSE.txt', plugin_dir / 'LICENSE.md']
    for path in license_paths:
        if path.exists():
            license_found = True
            break
    if not license_found:
        issues['warnings'].append('No LICENSE file found')
    tests_dir = plugin_dir / 'tests'
    if not tests_dir.exists() or not tests_dir.is_dir():
        issues['warnings'].append('No tests directory found')
    else:
        test_files = list(tests_dir.glob('test_*.py'))
        if not test_files:
            issues['warnings'].append('No test files found in tests directory')
    return issues
def create_plugin_signing_key(name: str, output_path: Union[str, Path]) -> SigningKey:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    signer = PluginSigner()
    key = signer.key
    signer.save_key(output_path, include_private=True)
    return key