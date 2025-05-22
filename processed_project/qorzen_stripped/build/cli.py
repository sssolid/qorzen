from __future__ import annotations
import argparse
import json
import pathlib
import sys
import time
from typing import List, Optional
from qorzen.build.builder import Builder, BuildError
from qorzen.build.config import BuildConfig, BuildPlatform, BuildType
from qorzen.build.utils import check_pyinstaller_availability, get_application_version
def parse_args(args: Optional[List[str]]=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build and package the Qorzen application', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--name', type=str, default='Qorzen', help='Name of the application (used for output filenames)')
    parser.add_argument('--version', type=str, default=get_application_version(), help='Version string for the application')
    parser.add_argument('--platform', type=str, choices=[p.value for p in BuildPlatform], default=BuildPlatform.CURRENT.value, help='Target platform for the build')
    parser.add_argument('--build-type', type=str, choices=[t.value for t in BuildType], default=BuildType.ONEDIR.value, help='Type of build to create')
    parser.add_argument('--console', action='store_true', help='Include a console window')
    parser.add_argument('--icon', type=str, help='Path to the application icon file')
    parser.add_argument('--entry-point', type=str, default='qorzen/main.py', help='Main entry point script for the application')
    parser.add_argument('--output-dir', type=str, default='dist', help='Directory where build artifacts will be placed')
    parser.add_argument('--clean', action='store_true', help='Clean the output directory before building')
    parser.add_argument('--no-upx', action='store_true', help='Disable UPX compression')
    parser.add_argument('--debug', action='store_true', help='Include debug information in the build')
    parser.add_argument('--include-path', action='append', default=[], help='Additional path to include in the build (can be specified multiple times)')
    parser.add_argument('--exclude-path', action='append', default=[], help='Path to exclude from the build (can be specified multiple times)')
    parser.add_argument('--hidden-import', action='append', default=[], help='Python module to include that may not be detected (can be specified multiple times)')
    parser.add_argument('--config', type=str, help='Path to a JSON configuration file')
    parser.add_argument('--save-config', type=str, help='Save the configuration to a JSON file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--create-installer', action='store_true', help='Create an installer for the built application')
    return parser.parse_args(args)
def create_config_from_args(args: argparse.Namespace) -> BuildConfig:
    if args.config:
        config = BuildConfig.from_json_file(args.config)
    else:
        config = BuildConfig()
    config.name = args.name
    config.version = args.version
    config.platform = BuildPlatform(args.platform)
    config.build_type = BuildType(args.build_type)
    config.console = args.console
    config.entry_point = pathlib.Path(args.entry_point)
    config.output_dir = pathlib.Path(args.output_dir)
    config.clean = args.clean
    config.upx = not args.no_upx
    config.debug = args.debug
    if args.icon:
        config.icon_path = pathlib.Path(args.icon)
    if args.include_path:
        config.include_paths = [pathlib.Path(p) for p in args.include_path]
    if args.exclude_path:
        config.exclude_paths = [pathlib.Path(p) for p in args.exclude_path]
    if args.hidden_import:
        config.hidden_imports = args.hidden_import
    return config
def main(args: Optional[List[str]]=None) -> int:
    args = parse_args(args)
    if not check_pyinstaller_availability():
        print('ERROR: PyInstaller is not installed.')
        print("Please install it with 'pip install pyinstaller'")
        return 1
    try:
        config = create_config_from_args(args)
    except Exception as e:
        print(f'ERROR: Failed to create build configuration: {str(e)}')
        return 1
    if args.save_config:
        try:
            config.to_json_file(args.save_config)
            print(f'Saved build configuration to {args.save_config}')
        except Exception as e:
            print(f'ERROR: Failed to save build configuration: {str(e)}')
            return 1
    if args.verbose:
        def logger(message: str) -> None:
            print(message)
    else:
        def logger(message: str) -> None:
            if message.startswith('[INFO]') or message.startswith('[ERROR]'):
                print(message)
    builder = Builder(config, logger)
    try:
        start_time = time.time()
        output_path = builder.build()
        build_time = time.time() - start_time
        print(f'\nBuild completed successfully in {build_time:.1f} seconds')
        print(f'Output: {output_path}')
        if args.create_installer:
            from qorzen.build.utils import create_installer
            try:
                installer_path = create_installer(output_path, config)
                print(f'Installer created: {installer_path}')
            except Exception as e:
                print(f'WARNING: Failed to create installer: {str(e)}')
        return 0
    except BuildError as e:
        print(f'\nERROR: Build failed: {str(e)}')
        return 1
    except Exception as e:
        print(f'\nERROR: Unexpected error: {str(e)}')
        import traceback
        traceback.print_exc()
        return 1
if __name__ == '__main__':
    sys.exit(main())