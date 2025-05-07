from __future__ import annotations

from PyQt6.QtCore import Qt

from ..services.vehicle_service import VehicleService

"""
Application bootstrap module for the InitialDB application.

This module handles the initialization of the application, registering
all required dependencies with the dependency container and ensuring
proper lifecycle management.
"""

import atexit
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import structlog
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen

from ..config.settings import settings
from .async_manager import AsyncManager
from .database_helper import DatabaseHelper
from .dependency_container import DependencyContainer, DependencyScope, register, resolve
from .schema_registry import SchemaRegistry

logger = structlog.get_logger(__name__)


class AppBootstrap:
    """
    Bootstrap manager for the InitialDB application.

    This class handles the initialization and cleanup of the application,
    registering dependencies, setting up logging, and managing the application
    lifecycle.
    """

    _instance: Optional[AppBootstrap] = None

    @classmethod
    def instance(cls) -> AppBootstrap:
        """Get the singleton instance of the bootstrap manager."""
        if cls._instance is None:
            cls._instance = AppBootstrap()
        return cls._instance

    def __init__(self) -> None:
        """Initialize the bootstrap manager."""
        self._initialized = False
        self._qt_app: Optional[QApplication] = None
        self._splash: Optional[QSplashScreen] = None

        logger.info("AppBootstrap initialized")

    def setup_logging(self) -> None:
        """Set up logging for the application."""
        log_file = Path.home() / "initialdb.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            handlers=[
                logging.FileHandler(str(log_file), mode="a", encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )

        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            logger_factory=structlog.stdlib.LoggerFactory(),
        )

        logger.info("Logging initialized", log_path=str(log_file))

    def get_resource_path(self, relative: str) -> Path:
        """
        Get the absolute path to a resource file.

        Args:
            relative: The relative path to the resource

        Returns:
            The absolute path to the resource
        """
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS) / relative
        return Path(__file__).parent.parent.parent / relative

    def init_qt_application(self) -> QApplication:
        """
        Initialize the Qt application.

        Returns:
            The Qt application instance
        """
        app = QApplication(sys.argv)
        app.setApplicationName("InitialDB")
        app.setStyle("Fusion")

        icon_path = self.get_resource_path("resources/initialdb.ico")
        if icon_path.exists():
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(str(icon_path)))

        self._qt_app = app
        return app

    def show_splash_screen(self) -> Optional[QSplashScreen]:
        """
        Show the application splash screen.

        Returns:
            The splash screen instance, or None if no splash screen is shown
        """
        if self._qt_app is None:
            return None

        splash_path = self.get_resource_path("resources/splash.png")
        if splash_path.exists():
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QPixmap

            pix = QPixmap(str(splash_path))
            splash = QSplashScreen(pix, Qt.WindowType.WindowStaysOnTopHint)
            splash.show()
            self._qt_app.processEvents()

            logger.debug("Splash screen shown")
            self._splash = splash
            return splash

        return None

    def register_dependencies(self) -> None:
        """Register all application dependencies with the dependency container."""
        container = DependencyContainer.instance()

        # First register AsyncManager
        async_manager = AsyncManager.instance()
        async_manager.initialize()
        register(AsyncManager, lambda: async_manager, DependencyScope.SINGLETON)

        # Register SchemaRegistry
        register(SchemaRegistry, SchemaRegistry, DependencyScope.SINGLETON)

        # Register DatabaseHelper
        connection_string = settings.get("connection_string")
        if not connection_string:
            raise ValueError("Database connection string not configured")

        def create_db_helper() -> DatabaseHelper:
            return DatabaseHelper(connection_string)

        register(DatabaseHelper, create_db_helper, DependencyScope.SINGLETON)

        # Register VehicleService
        from ..services.vehicle_service import init_vehicle_service
        init_vehicle_service()

        # Register other services as needed

        logger.info("Dependencies registered")

    def register_cleanup(self) -> None:
        """Register cleanup handlers for application shutdown."""
        # Register the cleanup handler with atexit
        atexit.register(self.cleanup)

        # Register Qt application cleanup
        if self._qt_app:
            self._qt_app.aboutToQuit.connect(self.cleanup)

        logger.info("Cleanup handlers registered")

    def cleanup(self) -> None:
        """Clean up all application resources."""
        logger.info("Cleaning up application resources")

        # Clean up dependencies
        DependencyContainer.instance().cleanup()

        logger.info("Application cleanup complete")

    async def test_database_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if the connection is successful, False otherwise
        """
        try:
            _vehicle_service = resolve(VehicleService)

            return await _vehicle_service.test_connection_direct()

        except Exception as e:
            logger.error(f"Error testing database connection: {e}", exc_info=True)
            return False

    async def bootstrap_async(self) -> bool:
        try:
            settings.initialize_display_settings()
            connection_ok = await self.test_database_connection()

            # Initialize UI registry
            from ..ui.ui_registry import init_ui_registry
            init_ui_registry()

            if self._splash and self._splash.isVisible():
                self._splash.close()
                self._splash = None
            if not connection_ok:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle('Connection Error')
                msg_box.setText('Could not connect to database. Please check your settings.')
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
                msg_box.exec()
                # if self._qt_app:
                #     self._qt_app.quit()
                # return False
            self._initialized = True
            return True

        except Exception as e:
            logger.error("Bootstrap error", exc_info=True)

            # Close splash screen if it exists
            if self._splash and self._splash.isVisible():
                self._splash.close()
                self._splash = None

            # Show error message
            QMessageBox.critical(None, "Startup Error", f"Error during startup: {e}")

            if self._qt_app:
                self._qt_app.quit()

            return False

    def bootstrap(self) -> bool:
        """
        Bootstrap the application synchronously.

        Returns:
            True if the bootstrap was successful, False otherwise
        """
        try:
            # Set up logging
            self.setup_logging()

            # Initialize Qt application
            self.init_qt_application()

            # Show splash screen
            self.show_splash_screen()

            # Register dependencies
            self.register_dependencies()

            # Register cleanup handlers
            self.register_cleanup()

            # Create async bootstrap task
            async_manager = AsyncManager.instance()
            operation_id = async_manager.run_coroutine(self.bootstrap_async())

            # Return true to indicate successful initialization,
            # actual bootstrap will continue asynchronously
            return True

        except Exception as e:
            logger.error("Bootstrap error", exc_info=True)

            # Close splash screen if it exists
            if self._splash and self._splash.isVisible():
                self._splash.close()
                self._splash = None

            # Show error message
            QMessageBox.critical(None, "Startup Error", f"Error during startup: {e}")

            if self._qt_app:
                self._qt_app.quit()

            return False


async def init_application_async() -> Optional[QApplication]:
    bootstrap = AppBootstrap.instance()
    bootstrap.setup_logging()
    app = bootstrap.init_qt_application()
    bootstrap.show_splash_screen()
    bootstrap.register_dependencies()
    bootstrap.register_cleanup()

    success = await bootstrap.bootstrap_async()
    if success:
        return app
    return None
