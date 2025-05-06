"""
Example Plugin - Lifecycle hooks.

This module contains the implementation of various lifecycle hooks
for the Example Plugin, demonstrating how to use the lifecycle hook system.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


def pre_install(context: Dict[str, Any]) -> None:
    """
    Pre-install hook.

    Called before the plugin is installed. Use this to check requirements
    or prepare the environment for installation.

    Args:
        context: Installation context information
    """
    print("Example Plugin: Pre-install hook called")
    print(f"Installation context: {json.dumps(context, indent=2)}")

    # Check for prerequisites or perform system checks
    # In a real plugin, you might check for:
    # - Required dependencies
    # - Sufficient disk space
    # - Compatible OS version
    # - Database requirements
    # - etc.

    # For demonstration purposes, we'll just print some info
    package_path = context.get("package_path", "")
    force = context.get("force", False)
    skip_verification = context.get("skip_verification", False)

    print(f"Installing from: {package_path}")
    print(f"Force install: {force}")
    print(f"Skip verification: {skip_verification}")

    # You could raise an exception here to abort installation
    # if a critical requirement is not met
    # Example:
    # if not some_requirement_met:
    #     raise ValueError("Installation requirement not met: ...")


def post_install(context: Dict[str, Any]) -> None:
    """
    Post-install hook.

    Called after the plugin is installed. Use this to set up
    initial plugin data or resources.

    Args:
        context: Installation context information
    """
    print("Example Plugin: Post-install hook called")

    # Create example data or config files
    install_path = context.get("install_path", "")
    if install_path:
        # Create a data directory if it doesn't exist
        data_dir = Path(install_path) / "data"
        os.makedirs(data_dir, exist_ok=True)

        # Create an example data file
        example_file = data_dir / "example_data.json"
        with open(example_file, "w") as f:
            json.dump({
                "created_by": "post_install hook",
                "version": "1.0.0",
                "data": {
                    "example": "This is example data created during installation"
                }
            }, f, indent=2)

        print(f"Created example data file: {example_file}")

    # Log successful installation
    print("Example Plugin installation completed successfully")


def pre_uninstall(context: Dict[str, Any]) -> None:
    """
    Pre-uninstall hook.

    Called before the plugin is uninstalled. Use this to back up
    data or perform cleanup.

    Args:
        context: Uninstallation context information
    """
    print("Example Plugin: Pre-uninstall hook called")

    # Check if we should keep data
    keep_data = context.get("keep_data", False)
    print(f"Keep data: {keep_data}")

    if not keep_data:
        # Warn about data loss
        print("WARNING: All plugin data will be removed!")

        # In a real plugin, you might want to create a backup
        install_path = context.get("install_path", "")
        if install_path:
            data_dir = Path(install_path) / "data"
            if data_dir.exists():
                # Example: Create a backup of the data
                # backup_path = Path(install_path).parent / "backups" / f"example_plugin-data-backup.zip"
                # os.makedirs(backup_path.parent, exist_ok=True)
                # shutil.make_archive(str(backup_path).replace(".zip", ""), "zip", data_dir)
                # print(f"Created data backup at: {backup_path}")
                print(f"Would back up data from: {data_dir}")


def post_uninstall(context: Dict[str, Any]) -> None:
    """
    Post-uninstall hook.

    Called after the plugin is uninstalled. Use this to clean up
    any remaining resources or external dependencies.

    Args:
        context: Uninstallation context information
    """
    print("Example Plugin: Post-uninstall hook called")

    # Check if uninstallation was successful
    success = context.get("success", False)
    print(f"Uninstallation successful: {success}")

    # In a real plugin, you might want to:
    # - Remove temporary files
    # - Clean up registry entries (on Windows)
    # - Remove user data if requested
    # - Remove environment variables
    # - etc.

    print("Example Plugin uninstallation completed")


def pre_update(context: Dict[str, Any]) -> None:
    """
    Pre-update hook.

    Called before the plugin is updated. Use this to prepare for the update,
    such as backing up data or settings.

    Args:
        context: Update context information
    """
    print("Example Plugin: Pre-update hook called")

    # Get current and new versions
    current_version = context.get("current_version", "unknown")
    new_version = context.get("new_version", "unknown")
    print(f"Updating from version {current_version} to {new_version}")

    # In a real plugin, you might:
    # - Backup current configuration
    # - Prepare for data migration
    # - Check compatibility of user data
    # - etc.

    # Example of version-specific update logic
    if current_version == "0.9.0" and new_version == "1.0.0":
        print("Performing special update steps for 0.9.0 -> 1.0.0 update")
        # Perform version-specific migration steps


def post_update(context: Dict[str, Any]) -> None:
    """
    Post-update hook.

    Called after the plugin is updated. Use this to migrate data to
    new formats or structures.

    Args:
        context: Update context information
    """
    print("Example Plugin: Post-update hook called")

    # Check if update was successful
    success = context.get("success", False)
    if not success:
        print("Update did not complete successfully")
        return

    # Get current and new versions
    current_version = context.get("current_version", "unknown")
    new_version = context.get("new_version", "unknown")

    # Perform data migrations or updates based on version
    install_path = context.get("install_path", "")
    if install_path:
        data_dir = Path(install_path) / "data"
        os.makedirs(data_dir, exist_ok=True)

        # Update example data file with new version info
        example_file = data_dir / "example_data.json"
        if example_file.exists():
            try:
                with open(example_file, "r") as f:
                    data = json.load(f)

                # Update the data
                data["updated_by"] = "post_update hook"
                data["version"] = new_version
                data["update_info"] = {
                    "previous_version": current_version,
                    "update_date": context.get("update_date", "unknown")
                }

                # Write back the updated data
                with open(example_file, "w") as f:
                    json.dump(data, f, indent=2)

                print(f"Updated example data file: {example_file}")

            except Exception as e:
                print(f"Error updating example data file: {e}")
        else:
            # Create a new file if it doesn't exist
            with open(example_file, "w") as f:
                json.dump({
                    "created_by": "post_update hook",
                    "version": new_version,
                    "data": {
                        "example": "This is example data created during update"
                    }
                }, f, indent=2)

            print(f"Created example data file: {example_file}")

    print(f"Example Plugin updated successfully to version {new_version}")

# Here you could define additional lifecycle hook functions:
#
# def on_data_migration(context: Dict[str, Any]) -> None:
#     """Migrate data between versions."""
#     pass
#
# def on_first_run(context: Dict[str, Any]) -> None:
#     """Run on the first execution after installation."""
#     pass
#
# def on_plugin_config_migration(context: Dict[str, Any]) -> None:
#     """Migrate plugin configuration between versions."""
#     pass