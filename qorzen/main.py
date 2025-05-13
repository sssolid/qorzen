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
    """Set up the Python environment for Qorzen."""
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    os.environ.setdefault('PYTHONUNBUFFERED', '1')


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
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


async def start_ui(args: argparse.Namespace) -> int:
    try:
        # Import needed modules
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPixmap, QIcon
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QSplashScreen
        import qorzen.resources_rc
        from qorzen.core.app import ApplicationCore
        from qorzen.core.error_handler import ErrorHandler, set_global_error_handler, install_global_exception_hook
        from qorzen.ui.main_window import MainWindow
        from qorzen.ui.ui_integration import UIIntegration

        # Create Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        QIcon.setThemeName('breeze')

        # Set application icon
        icon_path = Path('resources/logos/qorzen.ico').resolve().as_posix()
        app.setWindowIcon(QIcon(icon_path))

        # Show splash screen
        splash_path = Path('resources/logos/qorzen.png').resolve().as_posix()
        splash = QSplashScreen(QPixmap(splash_path), Qt.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()

        def update_progress(message: str, percent: int) -> None:
            splash.showMessage(f'{message} ({percent}%)', Qt.AlignBottom | Qt.AlignCenter, Qt.white)
            app.processEvents()

        # Initialize application core
        app_core = ApplicationCore(config_path=args.config)
        await app_core.initialize(progress_callback=update_progress)

        # Set up managers
        event_bus = app_core.get_manager('event_bus_manager')
        logger_manager = app_core.get_manager('logging_manager')
        await logger_manager.set_event_bus_manager(event_bus)

        config_manager = app_core.get_manager('config_manager')

        # Set up error handling
        error_handler = ErrorHandler(event_bus, logger_manager, config_manager)
        set_global_error_handler(error_handler)
        install_global_exception_hook()

        # Create main window and UI integration
        main_window = MainWindow(app_core)
        concurrency_manager = app_core.get_manager('concurrency_manager')
        ui_integration = UIIntegration(main_window, concurrency_manager, logger_manager)
        app_core.set_ui_integration(ui_integration)
        app_core.setup_signal_handlers()

        main_window.show()
        splash.finish(main_window)

        # Set up exit handling
        exit_code = 0
        shutdown_signal = asyncio.Event()
        app_shutdown_signal = asyncio.Event()

        def on_app_quit():
            app_shutdown_signal.set()

        app.aboutToQuit.connect(on_app_quit)

        # Set up periodic UI event processing
        async def process_events():
            while not shutdown_signal.is_set():
                app.processEvents()
                await asyncio.sleep(0.01)  # 10ms sleep to reduce CPU load

        # Set up the task to wait for application shutdown
        async def wait_for_shutdown():
            # Set up tasks
            process_task = asyncio.create_task(process_events())
            core_shutdown_task = asyncio.create_task(app_core.wait_for_shutdown())

            # Wait for either the app to quit or core to signal shutdown
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(app_shutdown_signal.wait()),
                    core_shutdown_task
                ],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Signal all tasks to stop
            shutdown_signal.set()

            # Clean up pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Clean up the UI event processing
            process_task.cancel()
            try:
                await process_task
            except asyncio.CancelledError:
                pass

            # Clean shutdown
            await app_core.shutdown()
            if hasattr(app_core, '_ui_integration') and app_core._ui_integration:
                await app_core._ui_integration.shutdown()

            return 0

        # Run the application
        return await wait_for_shutdown()

    except Exception as e:
        print(f'Error starting UI: {e}')
        traceback.print_exc()
        return 1


async def run_headless(args: argparse.Namespace) -> int:
    try:
        from qorzen.core.app import ApplicationCore
        from qorzen.core.error_handler import ErrorHandler, set_global_error_handler, install_global_exception_hook

        app_core = ApplicationCore(config_path=args.config)
        await app_core.initialize()

        event_bus = app_core.get_manager('event_bus_manager')
        logger_manager = app_core.get_manager('logging_manager')
        config_manager = app_core.get_manager('config_manager')

        error_handler = ErrorHandler(event_bus, logger_manager, config_manager)
        set_global_error_handler(error_handler)
        install_global_exception_hook()

        app_core.setup_signal_handlers()

        print('Qorzen running in headless mode. Press Ctrl+C to exit.')
        await app_core.wait_for_shutdown()
        await app_core.shutdown()

        return 0

    except Exception as e:
        print(f'Error running headless: {e}')
        traceback.print_exc()
        return 1


async def handle_build_command(args: argparse.Namespace) -> int:
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
    # Create and configure event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Handle better shutdown
    try:
        return loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        print("\nStopped by user.")
        return 0
    except Exception as e:
        print(f"Unhandled exception: {e}")
        traceback.print_exc()
        return 1
    finally:
        # Clean shutdown of event loop
        try:
            # Cancel pending tasks
            tasks = asyncio.all_tasks(loop)
            if tasks:
                for task in tasks:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        except Exception as e:
            print(f"Error during event loop shutdown: {e}")
            return 1


if __name__ == '__main__':
    sys.exit(main())