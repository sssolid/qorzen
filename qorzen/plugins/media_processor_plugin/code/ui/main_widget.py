from __future__ import annotations

"""
Main widget for the Media Processor Plugin.

This module contains the main interface widget for the Media Processor,
providing UI for media selection, processing, and configuration.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QImage
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QSplitter, QListWidget, QListWidgetItem,
    QFileDialog, QComboBox, QGroupBox, QCheckBox, QMessageBox,
    QScrollArea, QToolButton, QMenu, QApplication, QFrame, QDialog
)

from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager

from ..models.processing_config import ProcessingConfig, OutputFormat, BackgroundRemovalConfig
from ..processors.media_processor import MediaProcessor
from ..processors.batch_processor import BatchProcessor
from ..utils.exceptions import MediaProcessingError
from .batch_dialog import BatchProcessingDialog
from .config_editor import ConfigEditorDialog
from .format_editor import FormatEditorDialog
from .preview_widget import ImagePreviewWidget


class MediaProcessorWidget(QWidget):
    """
    Main widget for the Media Processor.

    This widget provides:
    - File selection (single or batch)
    - Processing configuration selection/editing
    - Preview of processing
    - Output format configuration
    - Batch processing controls
    """

    # Signals
    processingStarted = Signal()
    processingFinished = Signal(bool, str)  # success, message
    configChanged = Signal(str)  # config_id

    def __init__(
            self,
            media_processor: MediaProcessor,
            batch_processor: BatchProcessor,
            file_manager: FileManager,
            event_bus_manager: EventBusManager,
            concurrency_manager: ConcurrencyManager,
            task_manager: TaskManager,
            logger: Any,
            plugin_config: Dict[str, Any],
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the Media Processor widget.

        Args:
            media_processor: The media processor
            batch_processor: The batch processor
            file_manager: The file manager
            event_bus_manager: The event bus manager
            concurrency_manager: The concurrency manager
            task_manager: The task manager
            logger: The logger
            plugin_config: Plugin configuration
            parent: Parent widget
        """
        super().__init__(parent)

        self._media_processor = media_processor
        self._batch_processor = batch_processor
        self._file_manager = file_manager
        self._event_bus_manager = event_bus_manager
        self._concurrency_manager = concurrency_manager
        self._task_manager = task_manager
        self._logger = logger
        self._plugin_config = plugin_config

        # Initialize state
        self._selected_files: List[str] = []
        self._current_file_index: int = -1
        self._current_config: Optional[ProcessingConfig] = None
        self._available_configs: Dict[str, ProcessingConfig] = {}
        self._processing = False

        # Load configs
        asyncio.create_task(self._load_configs_async())

        # Set up UI
        self._init_ui()

        # Load default config
        self._create_default_config()

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title and description
        title_label = QLabel("Media Processor")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)

        description_label = QLabel(
            "Process images with background removal and multiple output formats."
        )
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        # Add horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Main content area with splitter
        self._splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self._splitter, 1)  # 1 = stretch factor

        # Left panel: Files and configuration
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # File selection
        file_group = QGroupBox("Input Files")
        file_layout = QVBoxLayout(file_group)

        # File list
        self._file_list = QListWidget()
        self._file_list.setMinimumWidth(200)
        self._file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._file_list.itemSelectionChanged.connect(self._on_file_selection_changed)
        file_layout.addWidget(self._file_list)

        # File buttons
        file_buttons_layout = QHBoxLayout()
        self._add_files_btn = QPushButton("Add Files")
        self._add_files_btn.clicked.connect(self._on_add_files)
        file_buttons_layout.addWidget(self._add_files_btn)

        self._add_folder_btn = QPushButton("Add Folder")
        self._add_folder_btn.clicked.connect(self._on_add_folder)
        file_buttons_layout.addWidget(self._add_folder_btn)

        self._remove_files_btn = QPushButton("Remove")
        self._remove_files_btn.clicked.connect(self._on_remove_files)
        file_buttons_layout.addWidget(self._remove_files_btn)

        file_layout.addLayout(file_buttons_layout)
        left_layout.addWidget(file_group)

        # Configuration selection
        config_group = QGroupBox("Processing Configuration")
        config_layout = QVBoxLayout(config_group)

        config_header_layout = QHBoxLayout()
        config_header_layout.addWidget(QLabel("Configuration:"))

        self._config_combo = QComboBox()
        self._config_combo.currentIndexChanged.connect(self._on_config_selected)
        config_header_layout.addWidget(self._config_combo, 1)

        self._edit_config_btn = QToolButton()
        self._edit_config_btn.setText("...")
        self._edit_config_btn.clicked.connect(self._on_edit_config)
        config_header_layout.addWidget(self._edit_config_btn)

        config_layout.addLayout(config_header_layout)

        # Config management buttons
        config_buttons_layout = QHBoxLayout()
        self._new_config_btn = QPushButton("New")
        self._new_config_btn.clicked.connect(self._on_new_config)
        config_buttons_layout.addWidget(self._new_config_btn)

        self._save_config_btn = QPushButton("Save")
        self._save_config_btn.clicked.connect(self._on_save_config)
        config_buttons_layout.addWidget(self._save_config_btn)

        self._load_config_btn = QPushButton("Load")
        self._load_config_btn.clicked.connect(self._on_load_config)
        config_buttons_layout.addWidget(self._load_config_btn)

        config_layout.addLayout(config_buttons_layout)
        left_layout.addWidget(config_group)

        # Process buttons
        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout(process_group)

        self._process_selected_btn = QPushButton("Process Selected Files")
        self._process_selected_btn.clicked.connect(self._on_process_selected)
        process_layout.addWidget(self._process_selected_btn)

        self._process_all_btn = QPushButton("Process All Files")
        self._process_all_btn.clicked.connect(self._on_process_all)
        process_layout.addWidget(self._process_all_btn)

        process_layout.addWidget(QLabel("Output Directory:"))

        output_dir_layout = QHBoxLayout()
        self._output_dir_edit = QLabel("(Default)")
        self._output_dir_edit.setFrameShape(QFrame.Panel)
        self._output_dir_edit.setFrameShadow(QFrame.Sunken)
        self._output_dir_edit.setMinimumHeight(24)
        output_dir_layout.addWidget(self._output_dir_edit, 1)

        self._browse_output_btn = QToolButton()
        self._browse_output_btn.setText("...")
        self._browse_output_btn.clicked.connect(self._on_browse_output)
        output_dir_layout.addWidget(self._browse_output_btn)

        process_layout.addLayout(output_dir_layout)

        self._overwrite_checkbox = QCheckBox("Overwrite existing files")
        process_layout.addWidget(self._overwrite_checkbox)

        left_layout.addWidget(process_group)

        # Right panel: Preview and details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_widget = ImagePreviewWidget(self._logger)
        self._preview_widget.setMinimumSize(400, 300)
        preview_layout.addWidget(self._preview_widget)

        # Preview controls
        preview_controls_layout = QHBoxLayout()

        self._prev_file_btn = QPushButton("Previous")
        self._prev_file_btn.clicked.connect(self._on_previous_file)
        preview_controls_layout.addWidget(self._prev_file_btn)

        self._file_counter_label = QLabel("0/0")
        preview_controls_layout.addWidget(self._file_counter_label, 1, Qt.AlignCenter)

        self._next_file_btn = QPushButton("Next")
        self._next_file_btn.clicked.connect(self._on_next_file)
        preview_controls_layout.addWidget(self._next_file_btn)

        preview_layout.addLayout(preview_controls_layout)

        # Preview options
        preview_options_layout = QHBoxLayout()

        self._preview_original_btn = QPushButton("Original")
        self._preview_original_btn.setCheckable(True)
        self._preview_original_btn.setChecked(True)
        self._preview_original_btn.clicked.connect(lambda: self._update_preview_mode("original"))
        preview_options_layout.addWidget(self._preview_original_btn)

        self._preview_background_btn = QPushButton("No Background")
        self._preview_background_btn.setCheckable(True)
        self._preview_background_btn.clicked.connect(lambda: self._update_preview_mode("background"))
        preview_options_layout.addWidget(self._preview_background_btn)

        self._preview_output_btn = QPushButton("Format")
        self._preview_output_btn.setCheckable(True)
        self._preview_output_btn.clicked.connect(lambda: self._update_preview_mode("output"))
        preview_options_layout.addWidget(self._preview_output_btn)

        preview_layout.addLayout(preview_options_layout)

        # Format selection for preview
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))

        self._format_combo = QComboBox()
        self._format_combo.currentIndexChanged.connect(self._on_format_selected)
        format_layout.addWidget(self._format_combo, 1)

        self._edit_format_btn = QToolButton()
        self._edit_format_btn.setText("...")
        self._edit_format_btn.clicked.connect(self._on_edit_format)
        format_layout.addWidget(self._edit_format_btn)

        preview_layout.addLayout(format_layout)

        right_layout.addWidget(preview_group)

        # Output details
        details_group = QGroupBox("Output Details")
        details_layout = QVBoxLayout(details_group)

        self._details_scroll = QScrollArea()
        self._details_scroll.setWidgetResizable(True)
        self._details_scroll.setMinimumHeight(150)

        self._details_widget = QWidget()
        self._details_layout = QVBoxLayout(self._details_widget)
        self._details_layout.setAlignment(Qt.AlignTop)

        self._details_scroll.setWidget(self._details_widget)
        details_layout.addWidget(self._details_scroll)

        right_layout.addWidget(details_group)

        # Add panels to splitter
        self._splitter.addWidget(left_panel)
        self._splitter.addWidget(right_panel)
        self._splitter.setSizes([300, 700])  # Initial sizes

        # Status bar
        self._status_label = QLabel("Ready")
        main_layout.addWidget(self._status_label)

        # Initialize UI state
        self._update_ui_state()

    def _create_default_config(self) -> None:
        """Create a default processing configuration if none exists."""
        if not self._available_configs:
            # Create a basic default configuration
            from ..models.processing_config import (
                ProcessingConfig,
                BackgroundRemovalConfig,
                OutputFormat,
                BackgroundRemovalMethod,
                ImageFormat,
                ResizeMode
            )

            # Create a default output format
            default_format = OutputFormat(
                name="PNG (Transparent)",
                format=ImageFormat.PNG,
                transparent_background=True,
                resize_mode=ResizeMode.NONE
            )

            # Create a default configuration
            default_config = ProcessingConfig(
                name="Default Configuration",
                description="Default processing configuration with transparent PNG output",
                background_removal=BackgroundRemovalConfig(
                    method=BackgroundRemovalMethod.ALPHA_MATTING
                ),
                output_formats=[default_format]
            )

            # Add to available configs
            self._available_configs[default_config.id] = default_config

            # Set as current config
            self._current_config = default_config

            # Update UI
            self._update_config_combo()
            self._update_format_combo()

    async def _load_configs_async(self) -> None:
        """Load available configurations asynchronously."""
        try:
            # TODO: Add proper configuration storage/loading
            # This would load saved configurations from disk
            self._logger.debug("Loading configurations...")

            # For now, we'll just use the default config
            asyncio.create_task(self._update_ui_with_configs())

        except Exception as e:
            self._logger.error(f"Error loading configurations: {str(e)}")

    async def _update_ui_with_configs(self) -> None:
        """Update UI with loaded configurations."""
        # Run UI updates on main thread
        if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
            await self._concurrency_manager.run_on_main_thread(
                lambda: asyncio.create_task(self._update_ui_with_configs())
            )
            return

        # Update UI components
        self._update_config_combo()
        self._update_format_combo()
        self._update_ui_state()

    def _update_config_combo(self) -> None:
        """Update configuration combo box with available configurations."""
        self._config_combo.blockSignals(True)
        self._config_combo.clear()

        for config_id, config in self._available_configs.items():
            self._config_combo.addItem(config.name, config_id)

        # Select current config if available
        if self._current_config:
            index = self._config_combo.findData(self._current_config.id)
            if index >= 0:
                self._config_combo.setCurrentIndex(index)

        self._config_combo.blockSignals(False)

    def _update_format_combo(self) -> None:
        """Update format combo box with formats from current configuration."""
        self._format_combo.blockSignals(True)
        self._format_combo.clear()

        if self._current_config and self._current_config.output_formats:
            for format_config in self._current_config.output_formats:
                self._format_combo.addItem(format_config.name, format_config.id)

            # Select first format
            self._format_combo.setCurrentIndex(0)

        self._format_combo.blockSignals(False)

    def _update_ui_state(self) -> None:
        """Update UI state based on current selection and configuration."""
        # Update file-related controls
        has_files = bool(self._selected_files)
        has_selection = bool(self._file_list.selectedItems())

        self._remove_files_btn.setEnabled(has_selection)
        self._process_selected_btn.setEnabled(has_selection and not self._processing)
        self._process_all_btn.setEnabled(has_files and not self._processing)

        # Update navigation controls
        has_multiple_files = len(self._selected_files) > 1
        current_valid = 0 <= self._current_file_index < len(self._selected_files)

        self._prev_file_btn.setEnabled(current_valid and self._current_file_index > 0)
        self._next_file_btn.setEnabled(current_valid and self._current_file_index < len(self._selected_files) - 1)

        # Update file counter
        if has_files:
            self._file_counter_label.setText(
                f"{self._current_file_index + 1 if current_valid else 0}/{len(self._selected_files)}"
            )
        else:
            self._file_counter_label.setText("0/0")

        # Update configuration controls
        has_config = self._current_config is not None
        self._edit_config_btn.setEnabled(has_config)
        self._save_config_btn.setEnabled(has_config)

        # Update format controls
        has_formats = has_config and bool(self._current_config.output_formats)
        self._format_combo.setEnabled(has_formats)
        self._edit_format_btn.setEnabled(has_formats and self._format_combo.currentIndex() >= 0)

        # Update preview controls
        self._preview_background_btn.setEnabled(has_config and current_valid)
        self._preview_output_btn.setEnabled(has_formats and current_valid)

        # If processing, disable all buttons
        if self._processing:
            self._add_files_btn.setEnabled(False)
            self._add_folder_btn.setEnabled(False)
            self._remove_files_btn.setEnabled(False)
            self._process_selected_btn.setEnabled(False)
            self._process_all_btn.setEnabled(False)
            self._edit_config_btn.setEnabled(False)
            self._new_config_btn.setEnabled(False)
            self._save_config_btn.setEnabled(False)
            self._load_config_btn.setEnabled(False)

    def _update_preview_mode(self, mode: str) -> None:
        """
        Update the preview mode.

        Args:
            mode: Preview mode ("original", "background", or "output")
        """
        # Update button states
        self._preview_original_btn.setChecked(mode == "original")
        self._preview_background_btn.setChecked(mode == "background")
        self._preview_output_btn.setChecked(mode == "output")

        # Generate preview based on mode
        asyncio.create_task(self._generate_preview(mode))

    async def _generate_preview(self, mode: str) -> None:
        """
        Generate preview image based on the selected mode.

        Args:
            mode: Preview mode ("original", "background", or "output")
        """
        if not self._selected_files or self._current_file_index < 0:
            self._preview_widget.clear()
            return

        try:
            current_file = self._selected_files[self._current_file_index]

            if mode == "original":
                # Show original image
                self._preview_widget.set_loading(True)
                self._preview_widget.load_image(current_file)
                self._preview_widget.set_loading(False)

            elif mode == "background" and self._current_config:
                # Show image with background removed
                self._preview_widget.set_loading(True)

                # Run in background to avoid UI freezing
                preview_data = await self._media_processor.create_preview(
                    current_file,
                    self._current_config.background_removal,
                    size=800  # Limit preview size
                )

                self._preview_widget.load_image_data(preview_data)
                self._preview_widget.set_loading(False)

            elif mode == "output" and self._current_config and self._current_config.output_formats:
                # Show image with selected output format
                self._preview_widget.set_loading(True)

                # Get selected format
                format_index = self._format_combo.currentIndex()
                if format_index >= 0 and format_index < len(self._current_config.output_formats):
                    format_config = self._current_config.output_formats[format_index]

                    # Run in background to avoid UI freezing
                    preview_data = await self._media_processor.create_preview(
                        current_file,
                        format_config,
                        size=800  # Limit preview size
                    )

                    self._preview_widget.load_image_data(preview_data)

                self._preview_widget.set_loading(False)

        except Exception as e:
            self._logger.error(f"Error generating preview: {str(e)}")
            self._preview_widget.set_error(f"Error: {str(e)}")
            self._preview_widget.set_loading(False)

    def _update_output_details(self) -> None:
        """Update output details display for current file and configuration."""
        # Clear existing details
        for i in reversed(range(self._details_layout.count())):
            item = self._details_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        if not self._selected_files or self._current_file_index < 0 or not self._current_config:
            # No file or config selected
            self._details_layout.addWidget(QLabel("No output details available"))
            return

        current_file = self._selected_files[self._current_file_index]
        filename = os.path.basename(current_file)

        # Add file info
        file_label = QLabel(f"<b>Input:</b> {filename}")
        file_label.setWordWrap(True)
        self._details_layout.addWidget(file_label)

        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self._details_layout.addWidget(line)

        # Add output details for each format
        for i, format_config in enumerate(self._current_config.output_formats):
            # Determine output path
            name, ext = os.path.splitext(filename)
            format_ext = format_config.format.value

            if format_config.naming_template:
                from ..utils.path_resolver import generate_filename
                output_name = generate_filename(
                    format_config.naming_template,
                    name,
                    format_ext,
                    format_config.prefix,
                    format_config.suffix
                )
            else:
                prefix = format_config.prefix or ""
                suffix = format_config.suffix or ""
                output_name = f"{prefix}{name}{suffix}.{format_ext}"

            # Determine output directory
            output_dir = self._current_config.output_directory or "(Default Output Directory)"
            if format_config.subdir:
                output_dir = os.path.join(output_dir, format_config.subdir)

            # Create label with format details
            format_label = QLabel(f"<b>Output Format {i + 1}:</b> {format_config.name}")
            format_label.setStyleSheet("margin-top: 10px;")
            self._details_layout.addWidget(format_label)

            path_label = QLabel(f"<b>Output Path:</b> {os.path.join(output_dir, output_name)}")
            path_label.setWordWrap(True)
            self._details_layout.addWidget(path_label)

            # Add more details about the format
            details = []
            details.append(f"Format: {format_config.format.value.upper()}")

            if format_config.transparent_background:
                details.append("Background: Transparent")
            elif format_config.background_color:
                details.append(f"Background: {format_config.background_color}")

            if format_config.resize_mode.value != "none":
                details.append(f"Resize: {format_config.resize_mode.value}")
                if format_config.width:
                    details.append(f"Width: {format_config.width}px")
                if format_config.height:
                    details.append(f"Height: {format_config.height}px")
                if format_config.percentage:
                    details.append(f"Scale: {format_config.percentage}%")

            # Join details with commas
            details_text = ", ".join(details)
            details_label = QLabel(f"<b>Settings:</b> {details_text}")
            details_label.setWordWrap(True)
            self._details_layout.addWidget(details_label)

    @Slot()
    def _on_add_files(self) -> None:
        """Handle add files button click."""
        file_formats = self._plugin_config.get("formats", {}).get("allowed_input", [])
        filter_str = f"Images ({' '.join(['*.' + fmt for fmt in file_formats])})"

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            filter_str
        )

        if file_paths:
            self._add_files(file_paths)

    @Slot()
    def _on_add_folder(self) -> None:
        """Handle add folder button click."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Images",
            ""
        )

        if folder_path:
            # Collect image files from the folder
            file_formats = self._plugin_config.get("formats", {}).get("allowed_input", [])
            image_files = []

            for root, _, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1][1:].lower()
                    if ext in file_formats:
                        image_files.append(os.path.join(root, file))

            if image_files:
                self._add_files(image_files)
            else:
                QMessageBox.information(
                    self,
                    "No Images Found",
                    f"No supported image files found in {folder_path}"
                )

    def _add_files(self, file_paths: List[str]) -> None:
        """
        Add files to the file list.

        Args:
            file_paths: List of file paths to add
        """
        # Add to list widget
        for file_path in file_paths:
            # Check if already added
            existing_items = self._file_list.findItems(
                file_path,
                Qt.MatchExactly
            )

            if not existing_items:
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                item.setToolTip(file_path)
                self._file_list.addItem(item)

                # Add to selected files
                self._selected_files.append(file_path)

        # Select first file if none selected
        if self._current_file_index < 0 and self._selected_files:
            self._current_file_index = 0
            self._file_list.setCurrentRow(0)

        # Update UI
        self._update_ui_state()
        self._update_output_details()

        # Update preview
        asyncio.create_task(self._generate_preview(
            "original" if self._preview_original_btn.isChecked() else
            "background" if self._preview_background_btn.isChecked() else
            "output"
        ))

    @Slot()
    def _on_remove_files(self) -> None:
        """Handle remove files button click."""
        selected_items = self._file_list.selectedItems()
        if not selected_items:
            return

        # Collect file paths to remove
        paths_to_remove = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            paths_to_remove.append(file_path)

        # Remove from file list
        for item in selected_items:
            self._file_list.takeItem(self._file_list.row(item))

        # Remove from selected files
        for path in paths_to_remove:
            if path in self._selected_files:
                self._selected_files.remove(path)

        # Update current index
        self._current_file_index = self._file_list.currentRow()

        # Update UI
        self._update_ui_state()
        self._update_output_details()

        # Update preview
        if self._current_file_index >= 0:
            asyncio.create_task(self._generate_preview(
                "original" if self._preview_original_btn.isChecked() else
                "background" if self._preview_background_btn.isChecked() else
                "output"
            ))
        else:
            self._preview_widget.clear()

    @Slot()
    def _on_file_selection_changed(self) -> None:
        """Handle file selection change."""
        selected_items = self._file_list.selectedItems()
        if not selected_items:
            return

        # Get current selected index
        self._current_file_index = self._file_list.currentRow()

        # Update UI
        self._update_ui_state()
        self._update_output_details()

        # Update preview
        asyncio.create_task(self._generate_preview(
            "original" if self._preview_original_btn.isChecked() else
            "background" if self._preview_background_btn.isChecked() else
            "output"
        ))

    @Slot()
    def _on_previous_file(self) -> None:
        """Navigate to previous file."""
        if self._current_file_index > 0:
            self._current_file_index -= 1
            self._file_list.setCurrentRow(self._current_file_index)

    @Slot()
    def _on_next_file(self) -> None:
        """Navigate to next file."""
        if self._current_file_index < len(self._selected_files) - 1:
            self._current_file_index += 1
            self._file_list.setCurrentRow(self._current_file_index)

    @Slot(int)
    def _on_config_selected(self, index: int) -> None:
        """
        Handle configuration selection change.

        Args:
            index: Selected index in combo box
        """
        if index < 0:
            return

        config_id = self._config_combo.itemData(index)
        if config_id in self._available_configs:
            self._current_config = self._available_configs[config_id]

            # Update format combo
            self._update_format_combo()

            # Update UI
            self._update_ui_state()
            self._update_output_details()

            # Update preview if in appropriate mode
            if self._preview_background_btn.isChecked() or self._preview_output_btn.isChecked():
                asyncio.create_task(self._generate_preview(
                    "background" if self._preview_background_btn.isChecked() else "output"
                ))

            # Signal config changed
            self.configChanged.emit(config_id)

    @Slot(int)
    def _on_format_selected(self, index: int) -> None:
        """
        Handle format selection change.

        Args:
            index: Selected index in combo box
        """
        # Update preview if in output mode
        if self._preview_output_btn.isChecked():
            asyncio.create_task(self._generate_preview("output"))

        # Update details
        self._update_output_details()

    @Slot()
    def _on_edit_config(self) -> None:
        """Handle edit configuration button click."""
        if not self._current_config:
            return

        # Create configuration editor dialog
        config_editor = ConfigEditorDialog(
            self._media_processor,
            self._file_manager,
            self._logger,
            self._plugin_config,
            self._current_config,
            self
        )

        # Connect signals
        config_editor.configUpdated.connect(self._on_config_updated)

        # Show dialog
        config_editor.exec()

    @Slot()
    def _on_new_config(self) -> None:
        """Handle new configuration button click."""
        # Create a new configuration
        from ..models.processing_config import (
            ProcessingConfig,
            BackgroundRemovalConfig,
            OutputFormat,
            ImageFormat
        )

        new_config = ProcessingConfig(
            name="New Configuration",
            description="New processing configuration",
            background_removal=BackgroundRemovalConfig(),
            output_formats=[
                OutputFormat(
                    name="Default Output",
                    format=ImageFormat.PNG
                )
            ]
        )

        # Add to available configs
        self._available_configs[new_config.id] = new_config

        # Set as current config
        self._current_config = new_config

        # Update UI
        self._update_config_combo()
        self._update_format_combo()
        self._update_ui_state()
        self._update_output_details()

        # Open editor
        self._on_edit_config()

    @Slot()
    def _on_save_config(self) -> None:
        """Handle save configuration button click."""
        if not self._current_config:
            return

        # Create file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            f"{self._current_config.name}.json",
            "Configuration Files (*.json)"
        )

        if not file_path:
            return

        # Save configuration
        asyncio.create_task(self._save_config_to_file(self._current_config, file_path))

    async def _save_config_to_file(self, config: ProcessingConfig, file_path: str) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save
            file_path: Path to save to
        """
        try:
            # Save configuration
            saved_path = await self._media_processor.save_processing_config(config, file_path)

            # Show success message
            if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(
                    lambda: QMessageBox.information(
                        self,
                        "Configuration Saved",
                        f"Configuration saved to {saved_path}"
                    )
                )
            else:
                QMessageBox.information(
                    self,
                    "Configuration Saved",
                    f"Configuration saved to {saved_path}"
                )

        except Exception as e:
            self._logger.error(f"Error saving configuration: {str(e)}")

            # Show error message
            if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(
                    lambda: QMessageBox.critical(
                        self,
                        "Error",
                        f"Error saving configuration: {str(e)}"
                    )
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error saving configuration: {str(e)}"
                )

    @Slot()
    def _on_load_config(self) -> None:
        """Handle load configuration button click."""
        # Create file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Configuration",
            "",
            "Configuration Files (*.json)"
        )

        if not file_path:
            return

        # Load configuration
        asyncio.create_task(self._load_config_from_file(file_path))

    async def _load_config_from_file(self, file_path: str) -> None:
        """
        Load configuration from file.

        Args:
            file_path: Path to load from
        """
        try:
            # Load configuration
            config = await self._media_processor.load_processing_config(file_path)

            # Add to available configs
            self._available_configs[config.id] = config

            # Set as current config
            self._current_config = config

            # Update UI
            if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(self._update_ui_after_config_load)
            else:
                self._update_ui_after_config_load()

        except Exception as e:
            self._logger.error(f"Error loading configuration: {str(e)}")

            # Show error message
            if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(
                    lambda: QMessageBox.critical(
                        self,
                        "Error",
                        f"Error loading configuration: {str(e)}"
                    )
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error loading configuration: {str(e)}"
                )

    def _update_ui_after_config_load(self) -> None:
        """Update UI after loading a configuration."""
        # Update UI
        self._update_config_combo()
        self._update_format_combo()
        self._update_ui_state()
        self._update_output_details()

        # Update preview if in appropriate mode
        if self._preview_background_btn.isChecked() or self._preview_output_btn.isChecked():
            asyncio.create_task(self._generate_preview(
                "background" if self._preview_background_btn.isChecked() else "output"
            ))

    @Slot(str)
    def _on_config_updated(self, config_id: str) -> None:
        """
        Handle configuration update.

        Args:
            config_id: ID of updated configuration
        """
        # Refresh UI
        self._update_config_combo()
        self._update_format_combo()
        self._update_ui_state()
        self._update_output_details()

        # Update preview if in appropriate mode
        if self._preview_background_btn.isChecked() or self._preview_output_btn.isChecked():
            asyncio.create_task(self._generate_preview(
                "background" if self._preview_background_btn.isChecked() else "output"
            ))

    @Slot()
    def _on_edit_format(self) -> None:
        """Handle edit format button click."""
        if not self._current_config or not self._current_config.output_formats:
            return

        # Get selected format
        format_index = self._format_combo.currentIndex()
        if format_index < 0 or format_index >= len(self._current_config.output_formats):
            return

        format_config = self._current_config.output_formats[format_index]

        # Create format editor dialog
        format_editor = FormatEditorDialog(
            format_config,
            self._logger,
            self
        )

        # Show dialog
        if format_editor.exec() == QDialog.Accepted:
            # Get updated format
            updated_format = format_editor.get_format()

            # Update format in config
            self._current_config.output_formats[format_index] = updated_format

            # Refresh UI
            self._update_format_combo()

            # Find the updated format in combo and select it
            for i in range(self._format_combo.count()):
                if self._format_combo.itemData(i) == updated_format.id:
                    self._format_combo.setCurrentIndex(i)
                    break

            # Update details
            self._update_output_details()

            # Update preview if in output mode
            if self._preview_output_btn.isChecked():
                asyncio.create_task(self._generate_preview("output"))

    @Slot()
    def _on_browse_output(self) -> None:
        """Handle browse output directory button click."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            ""
        )

        if folder_path:
            # Update output directory display
            self._output_dir_edit.setText(folder_path)

            # If config exists, update its output directory
            if self._current_config:
                self._current_config.output_directory = folder_path

                # Update output details
                self._update_output_details()

    @Slot()
    def _on_process_selected(self) -> None:
        """Handle process selected files button click."""
        selected_items = self._file_list.selectedItems()
        if not selected_items or not self._current_config:
            return

        # Collect selected file paths
        file_paths = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            file_paths.append(file_path)

        # Process files
        self._process_files(file_paths)

    @Slot()
    def _on_process_all(self) -> None:
        """Handle process all files button click."""
        if not self._selected_files or not self._current_config:
            return

        # Process all files
        self._process_files(self._selected_files)

    def _process_files(self, file_paths: List[str]) -> None:
        """
        Process the selected files.

        Args:
            file_paths: List of file paths to process
        """
        if not file_paths or not self._current_config:
            return

        # If only one file, process directly
        if len(file_paths) == 1:
            asyncio.create_task(self._process_single_file(file_paths[0]))
            return

        # For multiple files, show batch dialog
        output_dir = self._current_config.output_directory
        if self._output_dir_edit.text() != "(Default)":
            output_dir = self._output_dir_edit.text()

        # Create batch dialog
        batch_dialog = BatchProcessingDialog(
            self._batch_processor,
            file_paths,
            self._current_config,
            output_dir,
            self._overwrite_checkbox.isChecked(),
            self._logger,
            self
        )

        # Show dialog
        batch_dialog.exec()

    async def _process_single_file(self, file_path: str) -> None:
        """
        Process a single file.

        Args:
            file_path: Path to the file to process
        """
        if not self._current_config:
            return

        # Update UI state
        self._processing = True
        self._update_ui_state()
        self._status_label.setText(f"Processing {os.path.basename(file_path)}...")

        # Signal processing started
        self.processingStarted.emit()

        try:
            # Get output directory
            output_dir = self._current_config.output_directory
            if self._output_dir_edit.text() != "(Default)":
                output_dir = self._output_dir_edit.text()

            # Process the file
            output_paths = await self._media_processor.process_image(
                file_path,
                self._current_config,
                output_dir,
                self._overwrite_checkbox.isChecked()
            )

            # Show success message
            output_files_str = "\n".join(output_paths)
            if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(
                    lambda: QMessageBox.information(
                        self,
                        "Processing Complete",
                        f"Successfully processed {os.path.basename(file_path)}.\n\n"
                        f"Output files:\n{output_files_str}"
                    )
                )
            else:
                QMessageBox.information(
                    self,
                    "Processing Complete",
                    f"Successfully processed {os.path.basename(file_path)}.\n\n"
                    f"Output files:\n{output_files_str}"
                )

            # Signal processing finished
            self.processingFinished.emit(True, f"Successfully processed {os.path.basename(file_path)}")

        except Exception as e:
            self._logger.error(f"Error processing file: {str(e)}")

            # Show error message
            if self._concurrency_manager and not self._concurrency_manager.is_main_thread():
                await self._concurrency_manager.run_on_main_thread(
                    lambda: QMessageBox.critical(
                        self,
                        "Error",
                        f"Error processing file: {str(e)}"
                    )
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error processing file: {str(e)}"
                )

            # Signal processing finished with error
            self.processingFinished.emit(False, f"Error: {str(e)}")

        finally:
            # Update UI state
            self._processing = False
            self._update_ui_state()
            self._status_label.setText("Ready")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event for drag and drop."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event for drag and drop."""
        if event.mimeData().hasUrls():
            # Get file paths from URLs
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()

                if os.path.isdir(file_path):
                    # If directory, add all image files
                    file_formats = self._plugin_config.get("formats", {}).get("allowed_input", [])
                    for root, _, files in os.walk(file_path):
                        for file in files:
                            ext = os.path.splitext(file)[1][1:].lower()
                            if ext in file_formats:
                                file_paths.append(os.path.join(root, file))

                elif os.path.isfile(file_path):
                    # Check file extension
                    ext = os.path.splitext(file_path)[1][1:].lower()
                    file_formats = self._plugin_config.get("formats", {}).get("allowed_input", [])

                    if ext in file_formats:
                        file_paths.append(file_path)

            if file_paths:
                self._add_files(file_paths)

            event.acceptProposedAction()