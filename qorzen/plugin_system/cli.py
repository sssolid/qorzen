"""Command-line interface for the Qorzen plugin system.

This module provides a command-line interface for plugin creation,
packaging, signing, and validation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from qorzen.plugin_system.manifest import PluginManifest, PluginCapability
from qorzen.plugin_system.package import PluginPackage, PackageFormat
from qorzen.plugin_system.signing import PluginSigner, PluginVerifier
from qorzen.plugin_system.tools import (
    create_plugin_template,
    package_plugin,
    test_plugin,
    validate_plugin,
    create_plugin_signing_key,
)


def create_command(args: argparse.Namespace) -> int:
    """Handle the create command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        output_dir = Path(args.output_dir)

        # Create plugin template
        plugin_dir = create_plugin_template(
            output_dir=output_dir,
            plugin_name=args.name,
            display_name=args.display_name,
            description=args.description,
            author_name=args.author_name,
            author_email=args.author_email,
            author_url=args.author_url,
            version=args.version,
            license=args.license,
            force=args.force
        )

        print(f"Created plugin template at: {plugin_dir}")
        print(f"To package the plugin, run: qorzen-plugin package {plugin_dir}")

        return 0

    except Exception as e:
        print(f"Error creating plugin template: {e}", file=sys.stderr)
        return 1


def package_command(args: argparse.Namespace) -> int:
    """Handle the package command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        plugin_dir = Path(args.plugin_dir)

        # Validate the plugin first
        if not args.skip_validation:
            print(f"Validating plugin: {plugin_dir}")
            issues = validate_plugin(plugin_dir)

            # Print validation issues
            has_errors = False

            for level, messages in issues.items():
                if messages:
                    if level == "errors":
                        has_errors = True

                    print(f"{level.upper()}:")
                    for msg in messages:
                        print(f"  - {msg}")

            # Exit if there are errors
            if has_errors and not args.force:
                print("Plugin validation failed with errors. Use --force to package anyway.")
                return 1

        # Determine signing key
        signing_key = None
        if args.sign:
            if args.key:
                signing_key = Path(args.key)
            else:
                print("No signing key specified. Use --key to specify a signing key.")
                return 1

        # Package the plugin
        output_path = args.output if args.output else None

        format_type = PackageFormat.ZIP
        if args.format == "wheel":
            format_type = PackageFormat.WHEEL
        elif args.format == "directory":
            format_type = PackageFormat.DIRECTORY

        package_path = package_plugin(
            plugin_dir=plugin_dir,
            output_path=output_path,
            format=format_type,
            signing_key=signing_key,
            include_patterns=args.include,
            exclude_patterns=args.exclude
        )

        print(f"Created plugin package: {package_path}")

        return 0

    except Exception as e:
        print(f"Error packaging plugin: {e}", file=sys.stderr)
        return 1


def sign_command(args: argparse.Namespace) -> int:
    """Handle the sign command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        package_path = Path(args.package)

        # Load the key
        if not args.key:
            print("No signing key specified. Use --key to specify a signing key.")
            return 1

        key_path = Path(args.key)
        if not key_path.exists():
            print(f"Signing key not found: {key_path}")
            return 1

        try:
            key = PluginSigner.load_key(key_path)
        except Exception as e:
            print(f"Error loading signing key: {e}")
            return 1

        # Check if it's a package or directory
        if package_path.is_dir():
            # Find manifest file
            manifest_path = package_path / "manifest.json"
            if not manifest_path.exists():
                print(f"Manifest file not found: {manifest_path}")
                return 1

            try:
                manifest = PluginManifest.load(manifest_path)
            except Exception as e:
                print(f"Error loading manifest: {e}")
                return 1

            # Sign the manifest
            signer = PluginSigner(key)
            signer.sign_manifest(manifest)

            # Save the signed manifest
            manifest.save(manifest_path)

            print(f"Signed manifest: {manifest_path}")

        else:
            # Load the package
            try:
                package = PluginPackage.load(package_path)
            except Exception as e:
                print(f"Error loading package: {e}")
                return 1

            if not package.manifest:
                print(f"Package has no manifest")
                return 1

            # Sign the package
            signer = PluginSigner(key)
            signer.sign_package(package)

            # Save the updated package
            if package.format == PackageFormat.DIRECTORY:
                # No need to save for directory format
                pass
            else:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    package.extract(temp_path)

                    # Create a new package from the extracted directory
                    new_package = PluginPackage.create(
                        source_dir=temp_path,
                        output_path=package_path,
                        format=package.format
                    )

            print(f"Signed package: {package_path}")

        return 0

    except Exception as e:
        print(f"Error signing plugin: {e}", file=sys.stderr)
        return 1


def verify_command(args: argparse.Namespace) -> int:
    """Handle the verify command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        package_path = Path(args.package)

        # Create verifier
        verifier = PluginVerifier()

        # Load trusted keys
        if args.trusted_keys:
            trusted_keys_dir = Path(args.trusted_keys)
            if not trusted_keys_dir.exists() or not trusted_keys_dir.is_dir():
                print(f"Trusted keys directory not found: {trusted_keys_dir}")
                return 1

            count = verifier.load_trusted_keys(trusted_keys_dir)
            print(f"Loaded {count} trusted keys from {trusted_keys_dir}")

        if args.key:
            key_path = Path(args.key)
            if not key_path.exists():
                print(f"Trusted key not found: {key_path}")
                return 1

            try:
                key = PluginSigner.load_key(key_path)
                verifier.add_trusted_key(key)
                print(f"Added trusted key: {key.name} ({key.fingerprint})")
            except Exception as e:
                print(f"Error loading trusted key: {e}")
                return 1

        if not verifier.trusted_keys:
            print("Warning: No trusted keys loaded. Signature verification will fail.")

        # Load the package
        try:
            package = PluginPackage.load(package_path)
        except Exception as e:
            print(f"Error loading package: {e}")
            return 1

        if not package.manifest:
            print(f"Package has no manifest")
            return 1

        # Verify the package
        is_valid = verifier.verify_package(package)

        if is_valid:
            print(f"Package signature is valid: {package_path}")

            # Print manifest information
            manifest = package.manifest
            print("\nPlugin Information:")
            print(f"  Name: {manifest.name}")
            print(f"  Display Name: {manifest.display_name}")
            print(f"  Version: {manifest.version}")
            print(f"  Description: {manifest.description}")
            print(f"  Author: {manifest.author.name} <{manifest.author.email}>")
            print(f"  License: {manifest.license}")

            # Print capabilities
            if manifest.capabilities:
                print("\nRequested Capabilities:")
                for capability in manifest.capabilities:
                    risk = PluginCapability.get_risk_level(capability)
                    desc = PluginCapability.get_description(capability)
                    print(f"  - {capability} ({risk} risk): {desc}")

            # Print dependencies
            if manifest.dependencies:
                print("\nDependencies:")
                for dep in manifest.dependencies:
                    print(f"  - {dep.name} {dep.version}{' (optional)' if dep.optional else ''}")

            return 0
        else:
            print(f"Package signature verification failed: {package_path}")
            return 1

    except Exception as e:
        print(f"Error verifying plugin: {e}", file=sys.stderr)
        return 1


def validate_command(args: argparse.Namespace) -> int:
    """Handle the validate command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        plugin_dir = Path(args.plugin_dir)

        # Validate the plugin
        issues = validate_plugin(plugin_dir)

        # Print validation issues
        has_errors = False

        for level, messages in issues.items():
            if messages:
                if level == "errors":
                    has_errors = True

                print(f"{level.upper()}:")
                for msg in messages:
                    print(f"  - {msg}")

        # Return status
        return 1 if has_errors else 0

    except Exception as e:
        print(f"Error validating plugin: {e}", file=sys.stderr)
        return 1


def test_command(args: argparse.Namespace) -> int:
    """Handle the test command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        plugin_dir = Path(args.plugin_dir)

        # Run tests
        success = test_plugin(
            plugin_dir=plugin_dir,
            mock_env=not args.no_mock,
            test_pattern=args.pattern
        )

        return 0 if success else 1

    except Exception as e:
        print(f"Error testing plugin: {e}", file=sys.stderr)
        return 1


def generate_key_command(args: argparse.Namespace) -> int:
    """Handle the generate-key command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        output_path = Path(args.output)

        # Check if output file already exists
        if output_path.exists() and not args.force:
            print(f"Output file already exists: {output_path}")
            print("Use --force to overwrite")
            return 1

        # Create the key
        key = create_plugin_signing_key(args.name, output_path)

        print(f"Created signing key: {args.name}")
        print(f"Fingerprint: {key.fingerprint}")
        print(f"Saved key to: {output_path}")

        return 0

    except Exception as e:
        print(f"Error generating signing key: {e}", file=sys.stderr)
        return 1


def install_command(args: argparse.Namespace) -> int:
    """Handle the install command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import the installer here to avoid circular imports
        from qorzen.plugin_system.installer import PluginInstaller, PluginInstallationError

        package_path = Path(args.package)
        plugins_dir = Path(args.plugins_dir)

        # Create plugin installer
        installer = PluginInstaller(plugins_dir)

        # Load trusted keys for verification
        verifier = PluginVerifier()
        if args.trusted_keys:
            trusted_keys_dir = Path(args.trusted_keys)
            if trusted_keys_dir.exists() and trusted_keys_dir.is_dir():
                count = verifier.load_trusted_keys(trusted_keys_dir)
                print(f"Loaded {count} trusted keys from {trusted_keys_dir}")

        if not verifier.trusted_keys and not args.skip_verification:
            print("Warning: No trusted keys loaded. Skipping signature verification.")
            args.skip_verification = True

        installer.verifier = verifier

        # Install the plugin
        try:
            plugin = installer.install_plugin(
                package_path=package_path,
                force=args.force,
                skip_verification=args.skip_verification,
                enable=not args.disable
            )

            print(f"Successfully installed plugin: {plugin.manifest.display_name} v{plugin.manifest.version}")
            print(f"Installed to: {plugin.install_path}")
            return 0

        except PluginInstallationError as e:
            print(f"Error installing plugin: {e}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error installing plugin: {e}", file=sys.stderr)
        return 1


def list_command(args: argparse.Namespace) -> int:
    """Handle the list command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import the installer here to avoid circular imports
        from qorzen.plugin_system.installer import PluginInstaller

        plugins_dir = Path(args.plugins_dir)

        # Create plugin installer
        installer = PluginInstaller(plugins_dir)

        # Get installed plugins
        if args.all:
            plugins = installer.get_installed_plugins()
        else:
            plugins = installer.get_enabled_plugins()

        # Print plugin information
        if not plugins:
            print("No plugins installed.")
            return 0

        print(f"Installed plugins ({len(plugins)}):")
        for name, plugin in plugins.items():
            status = "Enabled" if plugin.enabled else "Disabled"
            print(f"  - {plugin.manifest.display_name} v{plugin.manifest.version} [{status}]")
            print(f"    {plugin.manifest.description}")
            print(f"    Installed: {plugin.installed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Path: {plugin.install_path}")
            print()

        return 0

    except Exception as e:
        print(f"Error listing plugins: {e}", file=sys.stderr)
        return 1


def uninstall_command(args: argparse.Namespace) -> int:
    """Handle the uninstall command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import the installer here to avoid circular imports
        from qorzen.plugin_system.installer import PluginInstaller, PluginInstallationError

        plugins_dir = Path(args.plugins_dir)

        # Create plugin installer
        installer = PluginInstaller(plugins_dir)

        # Uninstall the plugin
        try:
            success = installer.uninstall_plugin(
                plugin_name=args.name,
                keep_data=args.keep_data
            )

            if success:
                print(f"Successfully uninstalled plugin: {args.name}")
                return 0
            else:
                print(f"Plugin {args.name} is not installed.")
                return 1

        except PluginInstallationError as e:
            print(f"Error uninstalling plugin: {e}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error uninstalling plugin: {e}", file=sys.stderr)
        return 1


def enable_command(args: argparse.Namespace) -> int:
    """Handle the enable command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import the installer here to avoid circular imports
        from qorzen.plugin_system.installer import PluginInstaller

        plugins_dir = Path(args.plugins_dir)

        # Create plugin installer
        installer = PluginInstaller(plugins_dir)

        # Enable the plugin
        success = installer.enable_plugin(args.name)

        if success:
            print(f"Successfully enabled plugin: {args.name}")
            return 0
        else:
            print(f"Failed to enable plugin: {args.name}")
            return 1

    except Exception as e:
        print(f"Error enabling plugin: {e}", file=sys.stderr)
        return 1


def disable_command(args: argparse.Namespace) -> int:
    """Handle the disable command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import the installer here to avoid circular imports
        from qorzen.plugin_system.installer import PluginInstaller

        plugins_dir = Path(args.plugins_dir)

        # Create plugin installer
        installer = PluginInstaller(plugins_dir)

        # Disable the plugin
        success = installer.disable_plugin(args.name)

        if success:
            print(f"Successfully disabled plugin: {args.name}")
            return 0
        else:
            print(f"Failed to disable plugin: {args.name}")
            return 1

    except Exception as e:
        print(f"Error disabling plugin: {e}", file=sys.stderr)
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the command-line interface.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Qorzen Plugin System CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new plugin template")
    create_parser.add_argument("name", help="Plugin name (e.g., my-plugin)")
    create_parser.add_argument("--output-dir", default=".", help="Output directory")
    create_parser.add_argument("--display-name", help="Human-readable plugin name")
    create_parser.add_argument("--description", default="A Qorzen plugin", help="Plugin description")
    create_parser.add_argument("--author-name", default="Your Name", help="Author name")
    create_parser.add_argument("--author-email", default="your.email@example.com", help="Author email")
    create_parser.add_argument("--author-url", help="Author website URL")
    create_parser.add_argument("--version", default="0.1.0", help="Initial plugin version")
    create_parser.add_argument("--license", default="MIT", help="License identifier")
    create_parser.add_argument("--force", action="store_true", help="Overwrite existing files")

    # Package command
    package_parser = subparsers.add_parser("package", help="Package a plugin for distribution")
    package_parser.add_argument("plugin_dir", help="Plugin directory")
    package_parser.add_argument("--output", "-o", help="Output path")
    package_parser.add_argument("--format", choices=["zip", "wheel", "directory"], default="zip", help="Package format")
    package_parser.add_argument("--sign", action="store_true", help="Sign the package")
    package_parser.add_argument("--key", help="Path to signing key")
    package_parser.add_argument("--include", action="append", default=None,
                                help="Include pattern (can be specified multiple times)")
    package_parser.add_argument("--exclude", action="append", default=None,
                                help="Exclude pattern (can be specified multiple times)")
    package_parser.add_argument("--skip-validation", action="store_true", help="Skip plugin validation")
    package_parser.add_argument("--force", action="store_true", help="Force packaging even if validation fails")

    # Sign command
    sign_parser = subparsers.add_parser("sign", help="Sign a plugin package or manifest")
    sign_parser.add_argument("package", help="Plugin package or directory")
    sign_parser.add_argument("--key", required=True, help="Path to signing key")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a plugin package signature")
    verify_parser.add_argument("package", help="Plugin package")
    verify_parser.add_argument("--key", help="Path to trusted key")
    verify_parser.add_argument("--trusted-keys", help="Directory containing trusted keys")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a plugin directory")
    validate_parser.add_argument("plugin_dir", help="Plugin directory")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run plugin tests")
    test_parser.add_argument("plugin_dir", help="Plugin directory")
    test_parser.add_argument("--no-mock", action="store_true", help="Don't use mocked environment")
    test_parser.add_argument("--pattern", default="test_*.py", help="Test file pattern")

    # Generate key command
    key_parser = subparsers.add_parser("generate-key", help="Generate a plugin signing key")
    key_parser.add_argument("name", help="Key name")
    key_parser.add_argument("--output", "-o", required=True, help="Output path")
    key_parser.add_argument("--force", action="store_true", help="Overwrite existing key file")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install a plugin")
    install_parser.add_argument("package", help="Plugin package")
    install_parser.add_argument("--plugins-dir", default="plugins", help="Plugins directory")
    install_parser.add_argument("--force", action="store_true", help="Force installation (overwrite existing)")
    install_parser.add_argument("--skip-verification", action="store_true", help="Skip signature verification")
    install_parser.add_argument("--trusted-keys", help="Directory containing trusted keys")
    install_parser.add_argument("--disable", action="store_true", help="Disable the plugin after installation")

    # List command
    list_parser = subparsers.add_parser("list", help="List installed plugins")
    list_parser.add_argument("--plugins-dir", default="plugins", help="Plugins directory")
    list_parser.add_argument("--all", action="store_true", help="Include disabled plugins")

    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a plugin")
    uninstall_parser.add_argument("name", help="Plugin name")
    uninstall_parser.add_argument("--plugins-dir", default="plugins", help="Plugins directory")
    uninstall_parser.add_argument("--keep-data", action="store_true", help="Keep plugin data")

    # Enable command
    enable_parser = subparsers.add_parser("enable", help="Enable a plugin")
    enable_parser.add_argument("name", help="Plugin name")
    enable_parser.add_argument("--plugins-dir", default="plugins", help="Plugins directory")

    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable a plugin")
    disable_parser.add_argument("name", help="Plugin name")
    disable_parser.add_argument("--plugins-dir", default="plugins", help="Plugins directory")

    # Parse arguments
    args = parser.parse_args(args)

    # Execute command
    if args.command == "create":
        return create_command(args)
    elif args.command == "package":
        return package_command(args)
    elif args.command == "sign":
        return sign_command(args)
    elif args.command == "verify":
        return verify_command(args)
    elif args.command == "validate":
        return validate_command(args)
    elif args.command == "test":
        return test_command(args)
    elif args.command == "generate-key":
        return generate_key_command(args)
    elif args.command == "install":
        return install_command(args)
    elif args.command == "list":
        return list_command(args)
    elif args.command == "uninstall":
        return uninstall_command(args)
    elif args.command == "enable":
        return enable_command(args)
    elif args.command == "disable":
        return disable_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    import tempfile

    sys.exit(main())