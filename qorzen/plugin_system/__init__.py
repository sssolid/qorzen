"""Plugin packaging system for Qorzen.

This package provides a comprehensive system for creating, signing, distributing,
and installing plugins for the Qorzen platform.

Modules:
    manifest: Plugin manifest definition and validation
    package: Tools for creating and managing plugin packages
    signing: Utilities for signing and verifying plugin packages
    installer: Plugin installation and management
    repository: Plugin repository client and management
    tools: Developer tools for plugin creation and testing
"""

from __future__ import annotations

from qorzen.plugin_system.manifest import PluginManifest, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, PluginVerifier
from qorzen.plugin_system.installer import PluginInstaller
from qorzen.plugin_system.tools import create_plugin_template, package_plugin

__all__ = [
    "PluginManifest",
    "PluginCapability",
    "PluginPackage",
    "PackageFormat",
    "PluginSigner",
    "PluginVerifier",
    "PluginInstaller",
    "create_plugin_template",
    "package_plugin",
]