from __future__ import annotations

"""
AI Model Manager Dialog for downloading and managing AI models.

This module provides a user interface for downloading, managing, and activating
the AI models used for background removal.
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, cast

from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QListWidget, QListWidgetItem, QTabWidget, QWidget, QMessageBox,
    QGroupBox, QFormLayout, QSpacerItem, QSizePolicy, QCheckBox
)

from ..utils.ai_background_remover import AIBackgroundRemover, ModelDetails, ModelType


class ModelDownloadWorker(QObject):
    """Worker for downloading models in a separate thread."""

    progressChanged = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(
            self,
            ai_background_remover: AIBackgroundRemover,
            model_id: str
    ) -> None:
        """
        Initialize the worker.

        Args:
            ai_background_remover: AI background remover instance
            model_id: Model ID to download
        """
        super().__init__()
        self._ai_background_remover = ai_background_remover
        self._model_id = model_id

    @Slot()
    async def download(self) -> None:
        """Download the model."""
        try:
            # Progress callback
            async def progress_callback(percent: int, message: str) -> None:
                self.progressChanged.emit(percent, message)

            # Download the model
            await self._ai_background_remover.download_model(
                self._model_id,
                progress_callback
            )

            self.finished.emit(True, f"Model {self._model_id} downloaded successfully.")

        except Exception as e:
            self.finished.emit(False, f"Error downloading model: {str(e)}")


class AIModelManagerDialog(QDialog):
    """
    Dialog for managing AI models.

    Allows downloading, viewing, and activating AI models for background removal.
    """

    modelDownloaded = Signal(str)

    def __init__(
            self,
            ai_background_remover: AIBackgroundRemover,
            config_manager: Any,
            logger: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the dialog.

        Args:
            ai_background_remover: AI background remover instance
            config_manager: Configuration manager instance
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._ai_background_remover = ai_background_remover
        self._config_manager = config_manager
        self._logger = logger

        self._download_thread: Optional[QThread] = None
        self._download_worker: Optional[ModelDownloadWorker] = None
        self._current_model: Optional[str] = None

        self._init_ui()
        self.setWindowTitle("AI Model Manager")
        self.resize(600, 500)

        # Initialize model list
        asyncio.create_task(self._update_model_list())

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QVBoxLayout()
        title_label = QLabel("AI Model Manager")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)

        desc_label = QLabel(
            "Download and manage AI models for background removal. "
            "These models provide high-quality background removal capabilities."
        )
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)

        layout.addLayout(header_layout)

        # Tabs
        tab_widget = QTabWidget()

        # Models tab
        models_tab = QWidget()
        models_layout = QVBoxLayout(models_tab)

        # Model list
        self._model_list = QListWidget()
        self._model_list.setAlternatingRowColors(True)
        self._model_list.currentItemChanged.connect(self._on_model_selected)
        models_layout.addWidget(self._model_list)

        # Model details
        details_group = QGroupBox("Model Details")
        details_layout = QFormLayout(details_group)

        self._model_name_label = QLabel("")
        details_layout.addRow("Name:", self._model_name_label)

        self._model_desc_label = QLabel("")
        self._model_desc_label.setWordWrap(True)
        details_layout.addRow("Description:", self._model_desc_label)

        self._model_size_label = QLabel("")
        details_layout.addRow("Size:", self._model_size_label)

        self._model_status_label = QLabel("")
        details_layout.addRow("Status:", self._model_status_label)

        models_layout.addWidget(details_group)

        # Download controls
        download_layout = QHBoxLayout()

        self._download_btn = QPushButton("Download")
        self._download_btn.clicked.connect(self._on_download)
        self._download_btn.setEnabled(False)
        download_layout.addWidget(self._download_btn)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        download_layout.addWidget(self._progress_bar, 1)

        models_layout.addLayout(download_layout)

        # Settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        use_gpu_check = QCheckBox("Use GPU for inference (if available)")
        use_gpu_check.setChecked(True)
        settings_layout.addWidget(use_gpu_check)

        auto_download_check = QCheckBox("Automatically download models when needed")
        auto_download_check.setChecked(False)
        settings_layout.addWidget(auto_download_check)

        mem_limit_group = QGroupBox("Memory Usage Limits")
        mem_layout = QVBoxLayout(mem_limit_group)

        mem_limit_desc = QLabel(
            "These settings control how much memory the AI models can use. "
            "Lower values use less memory but may be slower."
        )
        mem_limit_desc.setWordWrap(True)
        mem_layout.addWidget(mem_limit_desc)

        memory_opt_layout = QHBoxLayout()
        memory_opt_layout.addWidget(QLabel("Memory Optimization:"))

        memory_opt_btns = [
            QPushButton("Low Memory"),
            QPushButton("Balanced"),
            QPushButton("Performance")
        ]
        for btn in memory_opt_btns:
            memory_opt_layout.addWidget(btn)

        mem_layout.addLayout(memory_opt_layout)
        settings_layout.addWidget(mem_limit_group)

        settings_layout.addStretch()

        # Add tabs
        tab_widget.addTab(models_tab, "Available Models")
        tab_widget.addTab(settings_tab, "Settings")

        layout.addWidget(tab_widget, 1)

        # Status
        self._status_label = QLabel("Ready")
        layout.addWidget(self._status_label)

        # Buttons
        buttons_layout = QHBoxLayout()

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self._close_btn)

        layout.addLayout(buttons_layout)

    async def _update_model_list(self) -> None:
        """Update the model list with available models."""
        self._model_list.clear()

        for model_id, model_info in ModelDetails.MODELS.items():
            item = QListWidgetItem(model_info["name"])
            item.setData(Qt.UserRole, model_id)

            # Check if model is downloaded
            is_downloaded = await self._ai_background_remover.is_model_downloaded(model_id)

            # Set tooltip with description
            desc = model_info["description"]
            size_mb = model_info["size"] / (1024 * 1024)
            tooltip = f"{desc}\nSize: {size_mb:.1f} MB"
            if is_downloaded:
                tooltip += "\nStatus: Downloaded"
            else:
                tooltip += "\nStatus: Not downloaded"

            item.setToolTip(tooltip)

            # Set icon based on status
            if is_downloaded:
                # Set icon for downloaded model
                item.setIcon(QIcon.fromTheme("dialog-ok-apply"))

            self._model_list.addItem(item)

    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_model_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """
        Handle model selection.

        Args:
            current: Current selection
            previous: Previous selection
        """
        if not current:
            self._download_btn.setEnabled(False)
            self._model_name_label.setText("")
            self._model_desc_label.setText("")
            self._model_size_label.setText("")
            self._model_status_label.setText("")
            return

        model_id = current.data(Qt.UserRole)
        self._current_model = model_id

        # Update UI with model details
        asyncio.create_task(self._update_model_details(model_id))

    async def _update_model_details(self, model_id: str) -> None:
        """
        Update the model details display.

        Args:
            model_id: Model ID
        """
        model_info = await self._ai_background_remover.get_model_info(model_id)

        self._model_name_label.setText(model_info["name"])
        self._model_desc_label.setText(model_info["description"])

        size_mb = model_info["size"] / (1024 * 1024)
        self._model_size_label.setText(f"{size_mb:.1f} MB")

        is_downloaded = model_info.get("downloaded", False)

        if is_downloaded:
            self._model_status_label.setText("Downloaded")
            self._model_status_label.setStyleSheet("color: green;")
            self._download_btn.setText("Redownload")
        else:
            self._model_status_label.setText("Not downloaded")
            self._model_status_label.setStyleSheet("color: red;")
            self._download_btn.setText("Download")

        self._download_btn.setEnabled(True)

    @Slot()
    def _on_download(self) -> None:
        """Handle download button click."""
        if not self._current_model:
            return

        # Disable UI during download
        self._download_btn.setEnabled(False)
        self._model_list.setEnabled(False)
        self._close_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(True)

        # Start download in a separate thread
        model_id = self._current_model
        self._status_label.setText(f"Downloading model {model_id}...")

        # Create worker in a thread
        self._download_thread = QThread()
        self._download_worker = ModelDownloadWorker(
            self._ai_background_remover,
            model_id
        )

        # Connect signals
        self._download_worker.progressChanged.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)

        # Move worker to thread
        self._download_worker.moveToThread(self._download_thread)

        # Start thread and download
        self._download_thread.started.connect(
            lambda: asyncio.create_task(self._download_worker.download())
        )
        self._download_thread.start()

    @Slot(int, str)
    def _on_download_progress(self, percent: int, message: str) -> None:
        """
        Handle download progress updates.

        Args:
            percent: Download progress percentage
            message: Progress message
        """
        self._progress_bar.setValue(percent)
        self._status_label.setText(message)

    @Slot(bool, str)
    def _on_download_finished(self, success: bool, message: str) -> None:
        """
        Handle download completion.

        Args:
            success: Whether download was successful
            message: Result message
        """
        # Stop thread
        if self._download_thread:
            self._download_thread.quit()
            self._download_thread.wait()
            self._download_thread = None
            self._download_worker = None

        # Update UI
        self._progress_bar.setVisible(False)
        self._model_list.setEnabled(True)
        self._close_btn.setEnabled(True)
        self._status_label.setText(message)

        if success:
            # Update model list
            asyncio.create_task(self._update_model_list())

            # Emit signal
            if self._current_model:
                self.modelDownloaded.emit(self._current_model)
        else:
            # Show error message
            QMessageBox.critical(self, "Download Error", message)

            # Re-enable download button
            self._download_btn.setEnabled(True)

    def closeEvent(self, event: Any) -> None:
        """Handle dialog close event."""
        # Check if download is in progress
        if self._download_thread and self._download_thread.isRunning():
            result = QMessageBox.question(
                self,
                "Download in Progress",
                "A model download is in progress. Do you want to cancel it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if result == QMessageBox.Yes:
                # Cancel download
                if self._download_thread:
                    self._download_thread.quit()
                    self._download_thread.wait()
                    self._download_thread = None
                    self._download_worker = None

                event.accept()
            else:
                event.ignore()
        else:
            event.accept()