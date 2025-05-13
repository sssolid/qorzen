from __future__ import annotations
import argparse
import asyncio
import importlib
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast


async def setup_environment() -> None:
    """Set up the environment for the application."""
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    os.environ.setdefault('PYTHONUNBUFFERED', '1')


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Qorzen - Modular Platform')
    parser.add_argument('--config', type=str, help='Path to configuration file', default=None)
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no UI)', default=False)
    parser.add_argument('--debug', action='store_true', help='Enable debug mode', default=False)

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build the application')
    build_parser.add_argument('--platform', type=str, default='current')
    build_parser.add_argument('--type', type=str, default='onedir')
    build_parser.add_argument('--output-dir', type=str, default='dist')
    build_parser.add_argument('--clean', action='store_true')
    build_parser.add_argument('--create-installer', action='store_true')

    return parser.parse_args()


async def start_ui(args: argparse.Namespace) -> int:
    """Start the application with a graphical user interface.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    try:
        # Import Qt-related modules here to avoid circular imports
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPixmap, QIcon
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QSplashScreen
        import qorzen.resources_rc

        # Import core modules
        from qorzen.core.app import ApplicationCore
        from qorzen.core.error_handler import ErrorHandler, set_global_error_handler, \
            install_global_exception_hook
        from qorzen.ui.main_window import MainWindow
        from qorzen.ui.ui_integration import UIIntegration

        # Create application first to ensure we have an event loop
        app = QApplication.instance() or QApplication(sys.argv)

        # Set the application icon
        QIcon.setThemeName('breeze')
        icon_path = Path('resources/logos/qorzen.ico').resolve().as_posix()
        app.setWindowIcon(QIcon(icon_path))

        # Show splash screen
        splash_path = Path('resources/logos/qorzen.png').resolve().as_posix()
        splash = QSplashScreen(QPixmap(splash_path), Qt.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()

        # Function to update progress
        def update_progress(message: str, percent: int) -> None:
            splash.showMessage(f'{message} ({percent}%)', Qt.AlignBottom | Qt.AlignCenter, Qt.white)
            app.processEvents()

        # Create application core
        app_core = ApplicationCore(config_path=args.config)

        # Initialize application core
        await app_core.initialize(progress_callback=update_progress)

        # Setup error handling
        event_bus = app_core.get_manager('event_bus_manager')
        logger_manager = app_core.get_manager('logging_manager')
        config_manager = app_core.get_manager('config_manager')

        error_handler = ErrorHandler(event_bus, logger_manager, config_manager)
        set_global_error_handler(error_handler)
        install_global_exception_hook()

        # Create main window
        main_window = MainWindow(app_core)

        # Setup UI integration
        concurrency_manager = app_core.get_manager('concurrency_manager')
        ui_integration = UIIntegration(main_window, concurrency_manager, logger_manager)

        # Set UI integration in application core
        app_core.set_ui_integration(ui_integration)

        # Install signal handlers for clean shutdown
        app_core.setup_signal_handlers()

        # Show main window
        main_window.show()
        splash.finish(main_window)

        # Create a task to run the application
        async def run_app() -> int:
            # Wait for the application to exit
            exit_future = asyncio.Future()
            app.aboutToQuit.connect(lambda: exit_future.set_result(0))

            # Wait for shutdown or application exit
            done, pending = await asyncio.wait(
                [app_core.wait_for_shutdown(), exit_future],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel any pending tasks
            for task in pending:
                task.cancel()

            # Shutdown application core if not already done
            await app_core.shutdown()

            # Return the exit code
            return exit_future.result() if exit_future.done() else 0

        # Run Qt event loop with asyncio
        loop = asyncio.get_event_loop()

        # Create a task to monitor the asyncio loop
        async def monitor_tasks() -> None:
            while True:
                await asyncio.sleep(0.1)
                app.processEvents()

        monitor_task = asyncio.create_task(monitor_tasks())

        # Run the application until it exits
        exit_code = 0
        try:
            exit_code = await run_app()
        finally:
            # Clean up
            monitor_task.cancel()

        return exit_code
    except Exception as e:
        print(f'Error starting UI: {e}')
        traceback.print_exc()
        return 1


async def run_headless(args: argparse.Namespace) -> int:
    """Run the application in headless mode.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    try:
        # Import core modules
        from qorzen.core.app import ApplicationCore
        from qorzen.core.error_handler import ErrorHandler, set_global_error_handler, \
            install_global_exception_hook

        # Create application core
        app_core = ApplicationCore(config_path=args.config)

        # Initialize application core
        await app_core.initialize()

        # Setup error handling
        event_bus = app_core.get_manager('event_bus_manager')
        logger_manager = app_core.get_manager('logging_manager')
        config_manager = app_core.get_manager('config_manager')

        error_handler = ErrorHandler(event_bus, logger_manager, config_manager)
        set_global_error_handler(error_handler)
        install_global_exception_hook()

        # Install signal handlers for clean shutdown
        app_core.setup_signal_handlers()

        print('Qorzen running in headless mode. Press Ctrl+C to exit.')

        # Wait for shutdown signal
        await app_core.wait_for_shutdown()

        # Shutdown application core
        await app_core.shutdown()

        return 0
    except Exception as e:
        print(f'Error running headless: {e}')
        traceback.print_exc()
        return 1


async def handle_build_command(args: argparse.Namespace) -> int:
    """Handle the build command.

    Args:
        args: Command line arguments

    Returns:
        Exit code
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


async def main_async() -> int:
    """Main entry point for the application (async version).

    Returns:
        Exit code
    """
    await setup_environment()
    args = parse_arguments()

    try:
        if args.command == 'build':
            return await handle_build_command(args)

        if args.headless:
            return await run_headless(args)
        else:
            return await start_ui(args)
    except Exception as e:
        print(f'Error starting Qorzen: {e}')
        traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point for the application.

    Returns:
        Exit code
    """
    # Create an event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # No event loop exists, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run the async main function
    return loop.run_until_complete(main_async())


if __name__ == '__main__':
    sys.exit(main())