from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer

# Import resources
import qorzen.resources_rc


def setup_environment() -> None:
    """Set up the environment for running the application."""
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    os.environ.setdefault('PYTHONUNBUFFERED', '1')


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        The parsed arguments
    """
    parser = argparse.ArgumentParser(description='Qorzen - Modular Platform')
    parser.add_argument('--config', type=str, help='Path to configuration file', default=None)
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no UI)', default=False)
    parser.add_argument('--debug', action='store_true', help='Enable debug mode', default=False)

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    build_parser = subparsers.add_parser('build', help='Build the application')
    build_parser.add_argument('--platform', type=str, default='current')
    build_parser.add_argument('--type', type=str, default='onedir')
    build_parser.add_argument('--output-dir', type=str, default='dist')
    build_parser.add_argument('--clean', action='store_true')
    build_parser.add_argument('--create-installer', action='store_true')

    return parser.parse_args()


def run_steps(steps: List[Callable[[], None]], on_complete: Callable[[], None],
              on_error: Callable[[str], None]) -> None:
    """Run a sequence of steps asynchronously.

    Args:
        steps: The steps to run
        on_complete: Callback for when all steps complete successfully
        on_error: Callback for when a step fails
    """
    if not steps:
        on_complete()
        return

    try:
        step = steps.pop(0)
        step()
        QTimer.singleShot(0, lambda: run_steps(steps, on_complete, on_error))
    except Exception as e:
        on_error(str(e))


def start_ui(args: argparse.Namespace) -> int:
    """
    Start the application UI.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    from qorzen.ui.panel_ui import MainWindow
    from qorzen.core.app import ApplicationCore
    from qorzen.utils.qt_thread_debug import install_enhanced_thread_debug, uninstall_enhanced_thread_debug

    # Install Qt threading debug if debugging is enabled
    if args.debug:
        install_enhanced_thread_debug(enable_logging=True)
        print("Installed Qt threading debug - threading issues will be logged")

    app = QApplication.instance() or QApplication(sys.argv)
    QIcon.setThemeName('breeze')

    splash_path = Path('resources/logos/qorzen.png').resolve().as_posix()
    splash = QSplashScreen(QPixmap(splash_path), Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    app_core = ApplicationCore(config_path=args.config)

    def update_progress(message: str, percent: int) -> None:
        splash.showMessage(f'{message} ({percent}%)', Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        app.processEvents()

    def on_complete() -> None:
        try:
            app_core.finalize_initialization()
        except Exception as e:
            print(f'Finalization failed: {e}')
            traceback.print_exc()
            splash.close()
            app.exit(1)
            return

        icon_path = Path('resources/logos/qorzen.ico').resolve().as_posix()
        app.setWindowIcon(QIcon(icon_path))

        main_window = MainWindow(app_core)
        app_core.set_main_window(main_window)
        main_window.show()
        splash.finish(main_window)

    def on_error(err: str) -> None:
        print(f'Initialization failed: {err}')
        traceback.print_exc()
        splash.close()
        app.exit(1)

    steps = app_core.get_initialization_steps(update_progress)
    QTimer.singleShot(0, lambda: run_steps(steps, on_complete, on_error))

    # Run the app and clean up debugging when done
    exit_code = app.exec()

    # Clean up Qt threading debug
    if args.debug:
        uninstall_enhanced_thread_debug()

    return exit_code


def handle_build_command(args: argparse.Namespace) -> int:
    """Handle the build command.

    Args:
        args: The command line arguments

    Returns:
        The exit code
    """
    try:
        from qorzen.build.cli import main as build_cli

        build_args = [
            f'--platform={args.platform}',
            f'--build-type={args.type}',
            f'--output-dir={args.output_dir}'
        ]

        if args.clean:
            build_args.append('--clean')

        if args.create_installer:
            build_args.append('--create-installer')

        return build_cli(build_args)

    except ImportError as e:
        print(f'Error importing build module: {e}')
        print("Make sure you have installed the build dependencies with 'pip install qorzen[build]'")
        return 1


def run_headless(args: argparse.Namespace) -> int:
    """Run the application in headless mode.

    Args:
        args: The command line arguments

    Returns:
        The exit code
    """
    from qorzen.core.app import ApplicationCore

    app_core = ApplicationCore(config_path=args.config)
    app_core.finalize_initialization()

    print('Qorzen running in headless mode. Press Ctrl+C to exit.')

    import signal

    def signal_handler(sig: int, frame: Any) -> None:
        """Handle signal to gracefully shut down.

        Args:
            sig: The signal number
            frame: The current stack frame
        """
        print('\nShutting down Qorzen...')
        app_core.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        signal.pause()
    except KeyboardInterrupt:
        print('\nShutting down Qorzen...')
        app_core.shutdown()

    return 0


def main() -> int:
    """Main entry point for the application.

    Returns:
        The exit code
    """
    # Set up environment
    setup_environment()

    # Parse arguments
    args = parse_arguments()

    try:
        # Handle specific commands
        if args.command == 'build':
            return handle_build_command(args)

        # Run in UI or headless mode
        if not args.headless:
            return start_ui(args)
        else:
            return run_headless(args)

    except Exception as e:
        print(f'Error starting Qorzen: {e}')
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())