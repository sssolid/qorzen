from __future__ import annotations

"""
Live preview widget for Format Editor Dialog.

This module provides a real-time preview of format changes within the
format editor dialog, allowing users to see the effect of their changes.
"""

import asyncio
import time
from typing import Optional, Dict, Any, Callable, Union
from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox,
    QPushButton, QProgressBar, QFrame, QSizePolicy
)

from ..models.processing_config import OutputFormat, BackgroundRemovalConfig
from ..utils.exceptions import MediaProcessingError
from ..ui.preview_widget import ImagePreviewWidget


class FormatPreviewWidget(QWidget):
    """
    Widget for providing live preview of format changes.

    This widget displays a preview of the current image with format settings
    applied, and can automatically update when settings change or provide
    manual refresh option.
    """

    previewRequested = Signal()

    def __init__(
            self,
            media_processor: Any,
            logger: Any,
            preview_file_path: Optional[str] = None,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the format preview widget.

        Args:
            media_processor: Instance of MediaProcessor
            logger: Logger instance
            preview_file_path: Path to the image to preview
            parent: Parent widget
        """
        super().__init__(parent)
        self._media_processor = media_processor
        self._logger = logger
        self._preview_file_path = preview_file_path

        self._current_format: Optional[OutputFormat] = None
        self._bg_removal_config: Optional[BackgroundRemovalConfig] = None
        self._auto_preview: bool = True
        self._preview_timer: Optional[QTimer] = None
        self._preview_delay: int = 500  # ms
        self._previous_preview_time: float = 0
        self._preview_throttle_time: float = 0.5  # seconds

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Preview options
        options_layout = QHBoxLayout()

        self._auto_preview_check = QCheckBox("Auto Preview")
        self._auto_preview_check.setChecked(self._auto_preview)
        self._auto_preview_check.toggled.connect(self._on_auto_preview_toggled)
        options_layout.addWidget(self._auto_preview_check)

        self._quality_combo = QComboBox()
        self._quality_combo.addItem("Low", "low")
        self._quality_combo.addItem("Medium", "medium")
        self._quality_combo.addItem("High", "high")
        self._quality_combo.setCurrentIndex(1)  # Default to medium
        self._quality_combo.currentIndexChanged.connect(self._on_quality_changed)
        options_layout.addWidget(QLabel("Quality:"))
        options_layout.addWidget(self._quality_combo)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        self._refresh_btn.setEnabled(not self._auto_preview)
        options_layout.addWidget(self._refresh_btn)

        layout.addLayout(options_layout)

        # Preview area
        self._preview_widget = ImagePreviewWidget(self._logger)
        self._preview_widget.setMinimumSize(400, 300)
        layout.addWidget(self._preview_widget, 1)

        # Status bar
        status_layout = QHBoxLayout()

        self._status_label = QLabel("Ready")
        status_layout.addWidget(self._status_label, 1)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        status_layout.addWidget(self._progress_bar)

        layout.addLayout(status_layout)

        # Set up the preview timer
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._update_preview)

        # Initial status
        if not self._preview_file_path:
            self._preview_widget.set_status("No preview image selected")
            self._status_label.setText("Select an image to preview")
        else:
            self._preview_widget.load_image(self._preview_file_path)

    def set_preview_image(self, file_path: str) -> None:
        """
        Set the image to use for preview.

        Args:
            file_path: Path to the image file
        """
        self._preview_file_path = file_path
        self._preview_widget.load_image(file_path)
        self._status_label.setText("Preview image loaded")

        if self._current_format and self._auto_preview:
            self._schedule_preview_update()

    def set_format(self, format_config: OutputFormat) -> None:
        """
        Set the format configuration to preview.

        Args:
            format_config: Format configuration
        """
        self._current_format = format_config

        if self._preview_file_path and self._auto_preview:
            self._schedule_preview_update()

    def set_background_removal(self, bg_removal_config: BackgroundRemovalConfig) -> None:
        """
        Set the background removal configuration.

        Args:
            bg_removal_config: Background removal configuration
        """
        self._bg_removal_config = bg_removal_config

        if self._preview_file_path and self._auto_preview:
            self._schedule_preview_update()

    def _schedule_preview_update(self) -> None:
        """Schedule a preview update with throttling."""
        if not self._preview_timer:
            return

        current_time = time.time()
        time_since_last_preview = current_time - self._previous_preview_time

        # Skip scheduling if we recently did a preview and timer is already running
        if (time_since_last_preview < self._preview_throttle_time and
                self._preview_timer.isActive()):
            return

        # Stop any existing timer and start a new one
        self._preview_timer.stop()
        self._preview_timer.start(self._preview_delay)

    @Slot()
    def _update_preview(self) -> None:
        """Update the preview image with current format settings."""
        if not self._preview_file_path or not self._current_format:
            return

        self._previous_preview_time = time.time()
        self._status_label.setText("Generating preview...")
        self._preview_widget.set_loading(True)

        # Get preview size based on quality setting
        quality_setting = self._quality_combo.currentData()
        preview_size = 600  # Default medium
        if quality_setting == "low":
            preview_size = 400
        elif quality_setting == "high":
            preview_size = 800

        # Start the preview generation
        asyncio.create_task(self._generate_preview(preview_size))

    async def _generate_preview(self, size: int) -> None:
        """
        Generate the preview image asynchronously.

        Args:
            size: Maximum dimension of the preview
        """
        try:
            if not self._preview_file_path or not self._current_format:
                return

            # Apply background removal if configured
            if self._bg_removal_config:
                preview_data = await self._media_processor.create_preview(
                    self._preview_file_path,
                    self._bg_removal_config,
                    size=size
                )
                # Create a temp image from the background-removed data
                temp_image = await self._media_processor.load_image_from_bytes(preview_data)

                # Apply the format to this intermediate image
                format_preview_data = await self._media_processor.create_preview_from_image(
                    temp_image,
                    self._current_format,
                    size=size
                )
            else:
                # Direct format application
                format_preview_data = await self._media_processor.create_preview(
                    self._preview_file_path,
                    self._current_format,
                    size=size
                )

            # Update UI with preview
            await self._update_ui_with_preview(format_preview_data)

        except Exception as e:
            self._logger.error(f"Error generating preview: {str(e)}")

            # Update UI with error
            if hasattr(self._media_processor, "_concurrency_manager"):
                await self._media_processor._concurrency_manager.run_on_main_thread(
                    lambda: self._show_preview_error(str(e))
                )
            else:
                self._show_preview_error(str(e))

    async def _update_ui_with_preview(self, preview_data: bytes) -> None:
        """
        Update the UI with the generated preview.

        Args:
            preview_data: The preview image data
        """
        # Run UI updates on the main thread
        if hasattr(self._media_processor, "_concurrency_manager"):
            await self._media_processor._concurrency_manager.run_on_main_thread(
                lambda: self._apply_preview_to_ui(preview_data)
            )
        else:
            self._apply_preview_to_ui(preview_data)

    def _apply_preview_to_ui(self, preview_data: bytes) -> None:
        """
        Apply the preview data to the UI.

        Args:
            preview_data: The preview image data
        """
        self._preview_widget.load_image_data(preview_data)
        self._preview_widget.set_loading(False)
        self._status_label.setText("Preview updated")

    def _show_preview_error(self, error_message: str) -> None:
        """
        Show an error message in the preview.

        Args:
            error_message: Error message to display
        """
        self._preview_widget.set_error(f"Error: {error_message}")
        self._preview_widget.set_loading(False)
        self._status_label.setText("Preview error")

    @Slot(bool)
    def _on_auto_preview_toggled(self, checked: bool) -> None:
        """
        Handle the auto preview toggle.

        Args:
            checked: Whether auto preview is checked
        """
        self._auto_preview = checked
        self._refresh_btn.setEnabled(not checked)

        if checked and self._preview_file_path and self._current_format:
            self._schedule_preview_update()

    @Slot()
    def _on_refresh_clicked(self) -> None:
        """Handle manual refresh button click."""
        if self._preview_file_path and self._current_format:
            self._update_preview()

    @Slot(int)
    def _on_quality_changed(self, index: int) -> None:
        """
        Handle preview quality change.

        Args:
            index: Index of the selected quality
        """
        if self._auto_preview and self._preview_file_path and self._current_format:
            self._schedule_preview_update()

    def sizeHint(self) -> QSize:
        """
        Get the recommended size for the widget.

        Returns:
            QSize: Recommended size
        """
        return QSize(500, 400)