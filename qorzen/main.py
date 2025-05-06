"""Main entry point for the Qorzen application.

This module provides the main entry point for the Qorzen application,
including parsing command-line arguments and initializing the application core.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, Optional, Any

from PySide6.QtWidgets import QSplashScreen
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


def setup_environment() -> None:
    """Set up the application environment.

    This ensures that the application can import its modules and sets
    necessary environment variables.
    """
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    os.environ.setdefault('PYTHONUNBUFFERED', '1')


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Qorzen - Modular Platform')
    parser.add_argument('--config', type=str, help='Path to configuration file', default=None)
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no UI)', default=False)
    parser.add_argument('--debug', action='store_true', help='Enable debug mode', default=False)

    # Add build subcommand
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    build_parser = subparsers.add_parser('build', help='Build the application')
    build_parser.add_argument('--platform', type=str, help='Target platform (windows, macos, linux, current)',
                              default='current')
    build_parser.add_argument('--type', type=str, help='Build type (onefile, onedir)', default='onedir')
    build_parser.add_argument('--output-dir', type=str, help='Output directory', default='dist')
    build_parser.add_argument('--clean', action='store_true', help='Clean output directory before building')
    build_parser.add_argument('--create-installer', action='store_true',
                              help='Create an installer for the built application')

    return parser.parse_args()


def start_ui(app_core: Any, args: argparse.Namespace) -> None:
    """Start the application UI.

    Args:
        app_core: Application core instance
        args: Command-line arguments
    """
    try:
        from qorzen.ui.main_window import start_ui as ui_start
        from qorzen.ui.main_window import QorzenMainWindow
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)

        splash_path = Path("resources/logos/qorzen_256x256.png").resolve().as_posix()
        pix = QPixmap(str(splash_path))
        splash = QSplashScreen(pix, Qt.WindowStaysOnTopHint)
        splash.show()

        icon_path = Path("resources/logos/qorzen.ico").resolve().as_posix()
        print(icon_path)
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))
        main_window = QorzenMainWindow(app_core)
        app_core.set_main_window(main_window)
        main_window.show()
        splash.close()
        sys.exit(app.exec())
    except ImportError as e:
        print(f'Error importing UI module: {e}')
        print('Running in headless mode.')


def handle_build_command(args: argparse.Namespace) -> int:
    """Handle the build command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        from qorzen.build.cli import main as build_cli

        # Convert the args namespace to a list of command-line arguments for the build CLI
        build_args = [
            f"--platform={args.platform}",
            f"--build-type={args.type}",
            f"--output-dir={args.output_dir}",
        ]

        if args.clean:
            build_args.append("--clean")

        if args.create_installer:
            build_args.append("--create-installer")

        return build_cli(build_args)
    except ImportError as e:
        print(f"Error importing build module: {e}")
        print("Make sure you have installed the build dependencies with 'pip install qorzen[build]'")
        return 1


def main() -> int:
    """Main entry point for the application.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    setup_environment()
    args = parse_arguments()

    # Handle build command if specified
    if args.command == 'build':
        return handle_build_command(args)

    try:
        from qorzen.core.app import ApplicationCore
        app_core = ApplicationCore(config_path=args.config)
        app_core.initialize()
        if not args.headless:
            start_ui(app_core, args)
        if args.headless:
            print('Qorzen running in headless mode. Press Ctrl+C to exit.')
            try:
                import signal
                def signal_handler(sig, frame):
                    print('\nShutting down Qorzen...')
                    app_core.shutdown()
                    sys.exit(0)

                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)
                signal.pause()
            except KeyboardInterrupt:
                print('\nShutting down Qorzen...')
                app_core.shutdown()
        return 0
    except Exception as e:
        print(f'Error starting Qorzen: {e}')
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())