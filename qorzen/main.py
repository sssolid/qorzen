#!/usr/bin/env python
"""
Qorzen - Main Application Entry Point

This module provides the entry point for starting the Qorzen application,
initializing all core managers, and launching the UI.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, Optional, Any


def setup_environment() -> None:
    """Set up the environment for the application."""
    # Add the parent directory to the path so we can import qorzen
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))

    # Set up any required environment variables
    os.environ.setdefault("PYTHONUNBUFFERED", "1")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Qorzen - Modular Platform")

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
        default=None,
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no UI)",
        default=False,
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
        default=False,
    )

    return parser.parse_args()


def start_ui(app_core: Any, args: argparse.Namespace) -> None:
    """Start the user interface.

    Args:
        app_core: The Application Core instance.
        args: Command line arguments.
    """
    try:
        from qorzen.ui.main_window import start_ui as ui_start
        from qorzen.ui.main_window import QorzenMainWindow
        from PySide6.QtWidgets import QApplication

        # Create the QApplication instance
        app = QApplication.instance() or QApplication(sys.argv)

        # Create the main window
        main_window = QorzenMainWindow(app_core)

        # Set the main window reference in the app core
        # This will trigger the ui/ready event for plugins
        app_core.set_main_window(main_window)

        # Show the window and run the application
        main_window.show()
        sys.exit(app.exec())
    except ImportError as e:
        print(f"Error importing UI module: {e}")
        print("Running in headless mode.")


def main() -> int:
    """Main entry point for the application.

    Returns:
        int: Exit code (0 for success, non-zero for error).
    """
    # Set up environment
    setup_environment()

    # Parse command line arguments
    args = parse_arguments()

    try:
        # Import core modules
        from qorzen.core.app import ApplicationCore

        # Create and initialize the application core
        app_core = ApplicationCore(config_path=args.config)
        app_core.initialize()

        # Start the UI if not in headless mode
        if not args.headless:
            start_ui(app_core, args)

        # The main thread should block until the application is ready to exit
        # (this could be a signal handler or event waiting)
        if args.headless:
            print("Qorzen running in headless mode. Press Ctrl+C to exit.")
            try:
                # In headless mode, we just wait for a keyboard interrupt
                import signal

                # Setup signal handling
                def signal_handler(sig, frame):
                    print("\nShutting down Qorzen...")
                    app_core.shutdown()
                    sys.exit(0)

                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)

                # Wait indefinitely
                signal.pause()
            except KeyboardInterrupt:
                print("\nShutting down Qorzen...")
                app_core.shutdown()

        return 0

    except Exception as e:
        print(f"Error starting Qorzen: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
