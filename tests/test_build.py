"""Tests for the Qorzen build system.

This module contains unit tests for the build system, including
configuration handling, builder functionality, and utilities.
"""

from __future__ import annotations

import json
import os
import pathlib
import platform
import tempfile
from typing import Dict, List, Optional, Set, Union
from unittest import mock

import pytest

from qorzen.build.config import BuildConfig, BuildPlatform, BuildType
from qorzen.build.builder import Builder, BuildError
from qorzen.build.utils import (
    find_dependencies,
    get_application_version,
    verify_build,
    fnmatch_to_regex,
    collect_resources,
)


class TestBuildConfig:
    """Tests for the BuildConfig class."""

    def test_defaults(self):
        """Test that default values are set correctly."""
        config = BuildConfig()
        assert config.name == "Qorzen"
        assert config.version == "0.1.0"
        assert config.platform == BuildPlatform.CURRENT
        assert config.build_type == BuildType.ONEDIR
        assert config.console is False
        assert config.icon_path is None

    def test_to_pyinstaller_args(self):
        """Test converting config to PyInstaller arguments."""
        config = BuildConfig(
            name="TestApp",
            version="1.2.3",
            platform=BuildPlatform.WINDOWS,
            build_type=BuildType.ONEFILE,
            console=True,
            entry_point=pathlib.Path(__file__),  # Use this test file as entry point
            output_dir=pathlib.Path("dist/test"),
            hidden_imports=["PySide6.QtCore"],
        )
        args = config.to_pyinstaller_args()

        # Check key arguments
        assert "--onefile" in args
        assert "--console" in args
        assert "--name" in args
        assert args[args.index("--name") + 1] == "TestApp"
        assert "--distpath" in args
        assert args[args.index("--distpath") + 1] == "dist/test"
        assert "--hidden-import" in args
        assert args[args.index("--hidden-import") + 1] == "PySide6.QtCore"
        assert __file__ in args  # Entry point should be included

    def test_serialization(self):
        """Test serializing and deserializing config."""
        config = BuildConfig(
            name="TestApp",
            version="1.2.3",
            platform=BuildPlatform.WINDOWS,
            build_type=BuildType.ONEFILE,
            console=True,
            entry_point=pathlib.Path(__file__),
            output_dir=pathlib.Path("dist/test"),
        )

        # Convert to dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "TestApp"
        assert config_dict["version"] == "1.2.3"
        assert config_dict["platform"] == "windows"
        assert config_dict["build_type"] == "onefile"
        assert config_dict["console"] is True
        assert config_dict["entry_point"] == __file__
        assert config_dict["output_dir"] == "dist/test"

        # Convert back to BuildConfig
        new_config = BuildConfig.from_dict(config_dict)
        assert new_config.name == "TestApp"
        assert new_config.version == "1.2.3"
        assert new_config.platform == BuildPlatform.WINDOWS
        assert new_config.build_type == BuildType.ONEFILE
        assert new_config.console is True
        assert str(new_config.entry_point) == __file__
        assert str(new_config.output_dir) == "dist/test"

    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        config = BuildConfig(
            name="TestApp",
            version="1.2.3",
            platform=BuildPlatform.WINDOWS,
            build_type=BuildType.ONEFILE,
            console=True,
            entry_point=pathlib.Path(__file__),
            output_dir=pathlib.Path("dist/test"),
        )

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Save config to JSON file
            config.to_json_file(tmp_path)

            # Read JSON file directly
            with open(tmp_path, "r") as f:
                config_dict = json.load(f)

            assert config_dict["name"] == "TestApp"
            assert config_dict["version"] == "1.2.3"

            # Load config from JSON file
            new_config = BuildConfig.from_json_file(tmp_path)
            assert new_config.name == "TestApp"
            assert new_config.version == "1.2.3"

        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestBuilder:
    """Tests for the Builder class."""

    def test_initialization(self):
        """Test builder initialization."""
        config = BuildConfig()
        logger = mock.MagicMock()

        builder = Builder(config, logger)

        assert builder.config == config
        assert builder.logger == logger
        assert builder.temp_dir is None

    @mock.patch("qorzen.build.builder.tempfile.mkdtemp")
    @mock.patch("qorzen.build.builder.pathlib.Path.mkdir")
    def test_prepare_build_environment(self, mock_mkdir, mock_mkdtemp):
        """Test build environment preparation."""
        # Mock mkdtemp to return a predictable path
        mock_mkdtemp.return_value = "/tmp/qorzen_build_12345"

        config = BuildConfig(platform=BuildPlatform.CURRENT)
        logger = mock.MagicMock()

        builder = Builder(config, logger)
        builder.prepare_build_environment()

        # Check that temporary directory was created
        assert str(builder.temp_dir) == "/tmp/qorzen_build_12345"

        # Check that platform was resolved
        assert config.platform != BuildPlatform.CURRENT
        assert config.platform in (BuildPlatform.WINDOWS, BuildPlatform.MACOS, BuildPlatform.LINUX)

    @mock.patch("qorzen.build.builder.subprocess.Popen")
    def test_run_pyinstaller_error(self, mock_popen):
        """Test PyInstaller execution with errors."""
        # Mock subprocess to simulate error
        process_mock = mock.MagicMock()
        process_mock.returncode = 1
        process_mock.stdout.read.return_value = ""
        process_mock.stderr.read.return_value = "Error: Something went wrong"
        mock_popen.return_value = process_mock

        config = BuildConfig()
        logger = mock.MagicMock()

        builder = Builder(config, logger)
        builder.temp_dir = pathlib.Path("/tmp/qorzen_build_12345")

        # Should return error code from process
        assert builder.run_pyinstaller() == 1


class TestUtils:
    """Tests for build utility functions."""

    def test_fnmatch_to_regex(self):
        """Test conversion of fnmatch patterns to regex."""
        patterns = [
            ("*.py", r"^[^/]*\.py$"),
            ("**/*.py", r"^.*[^/]*\.py$"),
            ("lib/*.txt", r"^lib/[^/]*\.txt$"),
            ("lib/**/data.json", r"^lib/.*/data\.json$"),
        ]

        for pattern, expected in patterns:
            assert fnmatch_to_regex(pattern) == expected

    def test_collect_resources(self):
        """Test resource collection."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create some test files
            files = [
                "icon.png",
                "data.json",
                "lib/helper.py",
                "lib/data/config.yaml",
                "lib/data/image.jpg",
                "lib/__pycache__/helper.cpython-310.pyc",
            ]

            for file in files:
                file_path = os.path.join(tmp_dir, file)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write("test content")

            # Test resource collection
            resources = collect_resources(
                tmp_dir,
                include_patterns=["**/*.png", "**/*.json", "**/*.yaml", "**/*.jpg"],
                exclude_patterns=["**/__pycache__/**", "**/*.py", "**/*.pyc"],
            )

            # Convert to set of relative paths for easier testing
            resource_paths = {
                os.path.relpath(str(path), tmp_dir) for path in resources.keys()
            }

            # Check that the right files were collected
            assert "icon.png" in resource_paths
            assert "data.json" in resource_paths
            assert "lib/data/config.yaml" in resource_paths
            assert "lib/data/image.jpg" in resource_paths

            # Check that excluded files were not collected
            assert "lib/helper.py" not in resource_paths
            assert "lib/__pycache__/helper.cpython-310.pyc" not in resource_paths


if __name__ == "__main__":
    pytest.main(["-v", __file__])