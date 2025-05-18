from __future__ import annotations

"""
Configuration editor dialog for the Media Processor Plugin.

This module provides a dialog for editing processing configurations,
managing output formats, and setting background removal options.
"""

import os
import time
from typing import Any, Dict, List, Optional, Set, Union, cast

from PySide6.QtCore import Qt, Signal, Slot, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    QPushButton, QTabWidget, QWidget, QListView,
    QDialogButtonBox, QGroupBox, QFrame, QScrollArea,
    QSizePolicy, QSlider, QToolButton, QMessageBox, QFileDialog
)

from ..models.processing_config import (
    ProcessingConfig,
    BackgroundRemovalConfig,
    BackgroundRemovalMethod,
    OutputFormat
)
from .format_editor import FormatEditorDialog
from ..processors.media_processor import MediaProcessor


class ConfigEditorDialog(QDialog):
    """
    Dialog for editing processing configurations.

    Allows editing:
    - General configuration settings
    - Background removal options
    - Managing output formats
    - Batch processing options
    """

    # Signals
    configUpdated = Signal(str)  # config_id

    def __init__(
            self,
            media_processor: MediaProcessor,
            file_manager: Any,
            logger: Any,
            plugin_config: Dict[str, Any],
            config: Optional[ProcessingConfig] = None,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the configuration editor dialog.

        Args:
            media_processor: The media processor
            file_manager: File manager for saving/loading configs
            logger: Logger instance
            plugin_config: Plugin configuration
            config: Optional processing configuration to edit
            parent: Parent widget
        """
        super().__init__(parent)

        self._media_processor = media_processor
        self._file_manager = file_manager
        self._logger = logger
        self._plugin_config = plugin_config

        # Create a new config if none provided
        if config is None:
            from ..models.processing_config import (
                ProcessingConfig,
                BackgroundRemovalConfig,
                OutputFormat,
                ImageFormat
            )

            config = ProcessingConfig(
                name="New Configuration",
                description="",
                background_removal=BackgroundRemovalConfig(),
                output_formats=[
                    OutputFormat(
                        name="Default Output",
                        format=ImageFormat.PNG
                    )
                ]
            )

        self._config = config

        # Create a deep copy of the config
        import copy
        self._edited_config = copy.deepcopy(config)

        # Formats model for list view
        self._formats_model = QStandardItemModel()

        # Initialize UI
        self._init_ui()

        # Load config values into UI
        self._load_values()

        # Set window title
        self.setWindowTitle(f"Edit Configuration: {config.name}")

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create tab widget for organizing settings
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # General tab
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "General")

        # Background removal tab
        bg_tab = self._create_background_tab()
        tab_widget.addTab(bg_tab, "Background Removal")

        # Output formats tab
        formats_tab = self._create_formats_tab()
        tab_widget.addTab(formats_tab, "Output Formats")

        # Batch options tab
        batch_tab = self._create_batch_tab()
        tab_widget.addTab(batch_tab, "Batch Options")

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Set dialog size
        self.resize(700, 500)

    def _create_general_tab(self) -> QWidget:
        """
        Create the general settings tab.

        Returns:
            Widget containing general configuration settings
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # General group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)

        # Name
        self._name_edit = QLineEdit()
        general_layout.addRow("Name:", self._name_edit)

        # Description
        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(80)
        general_layout.addRow("Description:", self._description_edit)

        # Output directory
        dir_layout = QHBoxLayout()
        self._output_dir_edit = QLineEdit()
        dir_layout.addWidget(self._output_dir_edit, 1)

        self._browse_dir_btn = QToolButton()
        self._browse_dir_btn.setText("...")
        self._browse_dir_btn.clicked.connect(self._on_browse_dir)
        dir_layout.addWidget(self._browse_dir_btn)

        general_layout.addRow("Output Directory:", dir_layout)

        # Add to layout
        layout.addWidget(general_group)

        # Add vertical spacer
        layout.addStretch()

        return tab

    def _create_background_tab(self) -> QWidget:
        """
        Create the background removal settings tab.

        Returns:
            Widget containing background removal settings
        """
        tab = QScrollArea()
        tab.setWidgetResizable(True)

        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)

        # Method group
        method_group = QGroupBox("Background Removal Method")
        method_layout = QVBoxLayout(method_group)

        # Method selection
        self._bg_method_combo = QComboBox()
        for method in BackgroundRemovalMethod:
            method_name = method.value.replace('_', ' ').title()
            self._bg_method_combo.addItem(method_name, method.value)

        self._bg_method_combo.currentIndexChanged.connect(self._on_bg_method_changed)
        method_layout.addWidget(self._bg_method_combo)

        # Method description
        self._method_description = QLabel()
        self._method_description.setWordWrap(True)
        self._method_description.setStyleSheet("color: #666;")
        method_layout.addWidget(self._method_description)

        # Add method group to layout
        layout.addWidget(method_group)

        # Chroma key settings
        self._chroma_key_group = QGroupBox("Chroma Key Settings")
        chroma_layout = QFormLayout(self._chroma_key_group)

        # Color selection
        color_layout = QHBoxLayout()
        self._chroma_color_btn = QPushButton()
        self._chroma_color_btn.setFixedSize(32, 32)
        self._chroma_color_btn.clicked.connect(self._on_chroma_color)
        color_layout.addWidget(self._chroma_color_btn)
        color_layout.addStretch()
        chroma_layout.addRow("Key Color:", color_layout)

        # Tolerance
        self._chroma_tolerance_slider = QSlider(Qt.Horizontal)
        self._chroma_tolerance_slider.setMinimum(0)
        self._chroma_tolerance_slider.setMaximum(255)
        self._chroma_tolerance_slider.setTickPosition(QSlider.TicksBelow)
        self._chroma_tolerance_slider.setTickInterval(10)

        self._chroma_tolerance_label = QLabel("30")
        self._chroma_tolerance_slider.valueChanged.connect(
            lambda v: self._chroma_tolerance_label.setText(str(v))
        )

        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(self._chroma_tolerance_slider)
        tolerance_layout.addWidget(self._chroma_tolerance_label)

        chroma_layout.addRow("Tolerance:", tolerance_layout)

        layout.addWidget(self._chroma_key_group)

        # Alpha matting settings
        self._alpha_matting_group = QGroupBox("Alpha Matting Settings")
        alpha_layout = QFormLayout(self._alpha_matting_group)

        # Foreground threshold
        self._alpha_fg_slider = QSlider(Qt.Horizontal)
        self._alpha_fg_slider.setMinimum(0)
        self._alpha_fg_slider.setMaximum(255)
        self._alpha_fg_slider.setTickPosition(QSlider.TicksBelow)
        self._alpha_fg_slider.setTickInterval(10)

        self._alpha_fg_label = QLabel("240")
        self._alpha_fg_slider.valueChanged.connect(
            lambda v: self._alpha_fg_label.setText(str(v))
        )

        fg_layout = QHBoxLayout()
        fg_layout.addWidget(self._alpha_fg_slider)
        fg_layout.addWidget(self._alpha_fg_label)

        alpha_layout.addRow("Foreground Threshold:", fg_layout)

        # Background threshold
        self._alpha_bg_slider = QSlider(Qt.Horizontal)
        self._alpha_bg_slider.setMinimum(0)
        self._alpha_bg_slider.setMaximum(255)
        self._alpha_bg_slider.setTickPosition(QSlider.TicksBelow)
        self._alpha_bg_slider.setTickInterval(10)

        self._alpha_bg_label = QLabel("10")
        self._alpha_bg_slider.valueChanged.connect(
            lambda v: self._alpha_bg_label.setText(str(v))
        )

        bg_layout = QHBoxLayout()
        bg_layout.addWidget(self._alpha_bg_slider)
        bg_layout.addWidget(self._alpha_bg_label)

        alpha_layout.addRow("Background Threshold:", bg_layout)

        layout.addWidget(self._alpha_matting_group)

        # ML model settings
        self._ml_model_group = QGroupBox("ML Model Settings")
        ml_layout = QFormLayout(self._ml_model_group)

        # Model selection
        self._ml_model_combo = QComboBox()
        self._ml_model_combo.addItem("U2Net", "u2net")
        self._ml_model_combo.addItem("DeepLabV3", "deeplabv3")
        self._ml_model_combo.addItem("MobileNetV2", "mobilenetv2")
        ml_layout.addRow("Model:", self._ml_model_combo)

        # Confidence threshold
        self._ml_threshold_slider = QSlider(Qt.Horizontal)
        self._ml_threshold_slider.setMinimum(1)
        self._ml_threshold_slider.setMaximum(100)
        self._ml_threshold_slider.setTickPosition(QSlider.TicksBelow)
        self._ml_threshold_slider.setTickInterval(10)

        self._ml_threshold_label = QLabel("50%")
        self._ml_threshold_slider.valueChanged.connect(
            lambda v: self._ml_threshold_label.setText(f"{v}%")
        )

        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(self._ml_threshold_slider)
        threshold_layout.addWidget(self._ml_threshold_label)

        ml_layout.addRow("Confidence Threshold:", threshold_layout)

        layout.addWidget(self._ml_model_group)

        # Smart selection settings
        self._smart_selection_group = QGroupBox("Smart Selection Settings")
        smart_layout = QFormLayout(self._smart_selection_group)

        # Brush size
        self._smart_brush_spin = QSpinBox()
        self._smart_brush_spin.setRange(1, 100)
        self._smart_brush_spin.setSuffix(" px")
        smart_layout.addRow("Brush Size:", self._smart_brush_spin)

        # Feather amount
        self._smart_feather_spin = QSpinBox()
        self._smart_feather_spin.setRange(0, 20)
        self._smart_feather_spin.setSuffix(" px")
        smart_layout.addRow("Feather Amount:", self._smart_feather_spin)

        layout.addWidget(self._smart_selection_group)

        # Manual mask settings
        self._manual_mask_group = QGroupBox("Manual Mask Settings")
        manual_layout = QFormLayout(self._manual_mask_group)

        # Mask path
        mask_layout = QHBoxLayout()
        self._mask_path_edit = QLineEdit()
        mask_layout.addWidget(self._mask_path_edit, 1)

        self._browse_mask_btn = QToolButton()
        self._browse_mask_btn.setText("...")
        self._browse_mask_btn.clicked.connect(self._on_browse_mask)
        mask_layout.addWidget(self._browse_mask_btn)

        manual_layout.addRow("Mask File:", mask_layout)

        layout.addWidget(self._manual_mask_group)

        # Post-processing group
        post_group = QGroupBox("Post-Processing")
        post_layout = QFormLayout(post_group)

        # Edge feather
        self._edge_feather_spin = QSpinBox()
        self._edge_feather_spin.setRange(0, 20)
        self._edge_feather_spin.setSuffix(" px")
        post_layout.addRow("Edge Feathering:", self._edge_feather_spin)

        # Refine edge
        self._refine_edge_check = QCheckBox("Enable")
        post_layout.addRow("Edge Refinement:", self._refine_edge_check)

        # Denoise
        self._denoise_check = QCheckBox("Enable")
        post_layout.addRow("Denoise Mask:", self._denoise_check)

        layout.addWidget(post_group)

        # Set content widget
        tab.setWidget(content)

        return tab

    def _create_formats_tab(self) -> QWidget:
        """
        Create the output formats settings tab.

        Returns:
            Widget containing output format settings
        """
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Left side: formats list
        list_layout = QVBoxLayout()

        # List title
        list_layout.addWidget(QLabel("Output Formats:"))

        # Formats list
        self._formats_list = QListView()
        self._formats_list.setModel(self._formats_model)
        self._formats_list.setSelectionMode(QListView.SingleSelection)
        self._formats_list.setEditTriggers(QListView.NoEditTriggers)
        self._formats_list.selectionModel().selectionChanged.connect(
            self._on_format_selection_changed
        )
        list_layout.addWidget(self._formats_list)

        # Formats buttons
        buttons_layout = QHBoxLayout()

        self._add_format_btn = QPushButton("Add")
        self._add_format_btn.clicked.connect(self._on_add_format)
        buttons_layout.addWidget(self._add_format_btn)

        self._edit_format_btn = QPushButton("Edit")
        self._edit_format_btn.clicked.connect(self._on_edit_format)
        buttons_layout.addWidget(self._edit_format_btn)

        self._remove_format_btn = QPushButton("Remove")
        self._remove_format_btn.clicked.connect(self._on_remove_format)
        buttons_layout.addWidget(self._remove_format_btn)

        list_layout.addLayout(buttons_layout)

        # Right side: format details
        details_layout = QVBoxLayout()

        # Details title
        details_layout.addWidget(QLabel("Format Details:"))

        # Details scroll area
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)

        self._format_details_widget = QWidget()
        self._format_details_layout = QVBoxLayout(self._format_details_widget)
        details_scroll.setWidget(self._format_details_widget)

        details_layout.addWidget(details_scroll)

        # Add layouts to main layout
        layout.addLayout(list_layout, 1)
        layout.addLayout(details_layout, 2)

        return tab

    def _create_batch_tab(self) -> QWidget:
        """
        Create the batch processing options tab.

        Returns:
            Widget containing batch processing settings
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Folder group
        folder_group = QGroupBox("Batch Output Organization")
        folder_layout = QVBoxLayout(folder_group)

        # Create subfolder
        self._batch_subfolder_check = QCheckBox("Create a subfolder for each batch")
        self._batch_subfolder_check.toggled.connect(self._on_subfolder_toggle)
        folder_layout.addWidget(self._batch_subfolder_check)

        # Subfolder template
        subfolder_layout = QFormLayout()
        self._subfolder_template_edit = QLineEdit()
        subfolder_layout.addRow("Subfolder Template:", self._subfolder_template_edit)

        # Template help
        template_help = QLabel(
            "Available placeholders: {date}, {time}, {timestamp}, {random}"
        )
        template_help.setWordWrap(True)
        template_help.setStyleSheet("color: #666;")
        subfolder_layout.addRow("", template_help)

        folder_layout.addLayout(subfolder_layout)
        layout.addWidget(folder_group)

        # Add vertical spacer
        layout.addStretch()

        return tab

    def _update_method_description(self) -> None:
        """Update the method description based on selected method."""
        method = self._bg_method_combo.currentData()

        descriptions = {
            BackgroundRemovalMethod.CHROMA_KEY.value:
                "Removes background based on color similarity. Works best with solid color backgrounds.",

            BackgroundRemovalMethod.ALPHA_MATTING.value:
                "Uses brightness values to determine foreground/background. Works well with high contrast images.",

            BackgroundRemovalMethod.ML_MODEL.value:
                "Uses machine learning to identify foreground subjects. Works with complex backgrounds.",

            BackgroundRemovalMethod.SMART_SELECTION.value:
                "Interactive selection tools for complex images. Requires manual guidance.",

            BackgroundRemovalMethod.MANUAL_MASK.value:
                "Uses a pre-created mask image to define transparency. Requires external mask creation."
        }

        if method in descriptions:
            self._method_description.setText(descriptions[method])
        else:
            self._method_description.setText("")

    def _update_method_ui(self) -> None:
        """Update visible UI controls based on selected method."""
        method = self._bg_method_combo.currentData()

        # Hide all method-specific groups
        self._chroma_key_group.setVisible(False)
        self._alpha_matting_group.setVisible(False)
        self._ml_model_group.setVisible(False)
        self._smart_selection_group.setVisible(False)
        self._manual_mask_group.setVisible(False)

        # Show appropriate group for selected method
        if method == BackgroundRemovalMethod.CHROMA_KEY.value:
            self._chroma_key_group.setVisible(True)
        elif method == BackgroundRemovalMethod.ALPHA_MATTING.value:
            self._alpha_matting_group.setVisible(True)
        elif method == BackgroundRemovalMethod.ML_MODEL.value:
            self._ml_model_group.setVisible(True)
        elif method == BackgroundRemovalMethod.SMART_SELECTION.value:
            self._smart_selection_group.setVisible(True)
        elif method == BackgroundRemovalMethod.MANUAL_MASK.value:
            self._manual_mask_group.setVisible(True)

    def _update_formats_list(self) -> None:
        """Update the formats list with current output formats."""
        self._formats_model.clear()

        for format_config in self._edited_config.output_formats:
            item = QStandardItem(format_config.name)
            item.setData(format_config.id, Qt.UserRole)
            self._formats_model.appendRow(item)

    def _update_format_details(self, format_id: Optional[str] = None) -> None:
        """
        Update the format details panel.

        Args:
            format_id: ID of format to display details for
        """
        # Clear existing details
        for i in reversed(range(self._format_details_layout.count())):
            item = self._format_details_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        if not format_id:
            # No format selected
            self._format_details_layout.addWidget(
                QLabel("Select a format to view details")
            )
            return

        # Find the format
        selected_format = None
        for fmt in self._edited_config.output_formats:
            if fmt.id == format_id:
                selected_format = fmt
                break

        if not selected_format:
            return

        # Display format details
        name_label = QLabel(f"<b>{selected_format.name}</b>")
        name_label.setStyleSheet("font-size: 14px;")
        self._format_details_layout.addWidget(name_label)

        details_lines = [
            f"Format: {selected_format.format.value.upper()}",
            f"Quality: {selected_format.quality}%"
        ]

        # Background
        if selected_format.transparent_background:
            details_lines.append("Background: Transparent")
        elif selected_format.background_color:
            details_lines.append(f"Background: {selected_format.background_color}")

        # Size
        if selected_format.resize_mode.value != "none":
            resize_details = f"Resize: {selected_format.resize_mode.value.replace('_', ' ').title()}"
            if selected_format.width:
                resize_details += f", Width: {selected_format.width}px"
            if selected_format.height:
                resize_details += f", Height: {selected_format.height}px"
            if selected_format.percentage:
                resize_details += f", Scale: {selected_format.percentage}%"
            details_lines.append(resize_details)

        # Cropping
        if selected_format.crop_enabled:
            details_lines.append("Cropping: Enabled")

        # Padding
        if selected_format.padding_enabled:
            details_lines.append("Padding: Enabled")

        # Rotation
        if selected_format.rotation_angle != 0:
            details_lines.append(f"Rotation: {selected_format.rotation_angle}°")

        # Watermark
        if selected_format.watermark.type.value != "none":
            details_lines.append(
                f"Watermark: {selected_format.watermark.type.value.title()}"
            )

        # File naming
        file_naming = "File naming: "
        if selected_format.prefix:
            file_naming += f"Prefix: '{selected_format.prefix}', "
        if selected_format.suffix:
            file_naming += f"Suffix: '{selected_format.suffix}', "
        if selected_format.naming_template:
            file_naming += f"Template: '{selected_format.naming_template}'"

        if file_naming != "File naming: ":
            details_lines.append(file_naming)

        # Output subdirectory
        if selected_format.subdir:
            details_lines.append(f"Subdirectory: {selected_format.subdir}")

        # Add details to layout
        for line in details_lines:
            self._format_details_layout.addWidget(QLabel(line))

        # Add spacer
        self._format_details_layout.addStretch()

    def _load_values(self) -> None:
        """Load values from config into UI controls."""
        # General tab
        self._name_edit.setText(self._edited_config.name)
        if self._edited_config.description:
            self._description_edit.setText(self._edited_config.description)
        if self._edited_config.output_directory:
            self._output_dir_edit.setText(self._edited_config.output_directory)

        # Background removal tab
        # Method selection
        bg_config = self._edited_config.background_removal
        method_index = self._bg_method_combo.findData(bg_config.method.value)
        if method_index >= 0:
            self._bg_method_combo.setCurrentIndex(method_index)

        # Update method description and UI
        self._update_method_description()
        self._update_method_ui()

        # Chroma key settings
        if bg_config.chroma_color:
            from PySide6.QtGui import QColor
            self._chroma_color_btn.setStyleSheet(
                f"background-color: {bg_config.chroma_color};"
            )
        self._chroma_tolerance_slider.setValue(bg_config.chroma_tolerance)

        # Alpha matting settings
        self._alpha_fg_slider.setValue(bg_config.alpha_foreground_threshold)
        self._alpha_bg_slider.setValue(bg_config.alpha_background_threshold)

        # ML model settings
        model_index = self._ml_model_combo.findData(bg_config.model_name)
        if model_index >= 0:
            self._ml_model_combo.setCurrentIndex(model_index)

        threshold_percent = int(bg_config.confidence_threshold * 100)
        self._ml_threshold_slider.setValue(threshold_percent)

        # Smart selection settings
        self._smart_brush_spin.setValue(bg_config.smart_brush_size)
        self._smart_feather_spin.setValue(bg_config.smart_feather_amount)

        # Manual mask settings
        if bg_config.mask_path:
            self._mask_path_edit.setText(bg_config.mask_path)

        # Post-processing settings
        self._edge_feather_spin.setValue(bg_config.edge_feather)
        self._refine_edge_check.setChecked(bg_config.refine_edge)
        self._denoise_check.setChecked(bg_config.denoise)

        # Output formats tab
        self._update_formats_list()

        # Batch tab
        self._batch_subfolder_check.setChecked(self._edited_config.create_subfolder_for_batch)
        self._subfolder_template_edit.setText(self._edited_config.batch_subfolder_template)
        self._subfolder_template_edit.setEnabled(self._edited_config.create_subfolder_for_batch)

        # Update UI state
        self._edit_format_btn.setEnabled(False)
        self._remove_format_btn.setEnabled(False)

    def _save_values(self) -> None:
        """Save values from UI controls to configuration."""
        # General tab
        self._edited_config.name = self._name_edit.text()
        self._edited_config.description = self._description_edit.toPlainText()
        self._edited_config.output_directory = self._output_dir_edit.text() or None

        # Background removal tab
        bg_config = self._edited_config.background_removal

        # Method
        method_data = self._bg_method_combo.currentData()
        if method_data:
            bg_config.method = BackgroundRemovalMethod(method_data)

        # Chroma key settings
        bg_style = self._chroma_color_btn.styleSheet()
        import re
        color_match = re.search(r'background-color: ([^;]+);', bg_style)
        if color_match:
            bg_config.chroma_color = color_match.group(1)

        bg_config.chroma_tolerance = self._chroma_tolerance_slider.value()

        # Alpha matting settings
        bg_config.alpha_foreground_threshold = self._alpha_fg_slider.value()
        bg_config.alpha_background_threshold = self._alpha_bg_slider.value()

        # ML model settings
        bg_config.model_name = self._ml_model_combo.currentData()
        bg_config.confidence_threshold = self._ml_threshold_slider.value() / 100.0

        # Smart selection settings
        bg_config.smart_brush_size = self._smart_brush_spin.value()
        bg_config.smart_feather_amount = self._smart_feather_spin.value()

        # Manual mask settings
        bg_config.mask_path = self._mask_path_edit.text() or None

        # Post-processing settings
        bg_config.edge_feather = self._edge_feather_spin.value()
        bg_config.refine_edge = self._refine_edge_check.isChecked()
        bg_config.denoise = self._denoise_check.isChecked()

        # Batch tab
        self._edited_config.create_subfolder_for_batch = self._batch_subfolder_check.isChecked()
        self._edited_config.batch_subfolder_template = self._subfolder_template_edit.text()

        # Update timestamp
        from datetime import datetime
        self._edited_config.updated_at = datetime.now()

    def accept(self) -> None:
        """Handle dialog acceptance (OK button)."""
        # Validate
        if not self._name_edit.text():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Configuration name cannot be empty"
            )
            return

        if not self._edited_config.output_formats:
            QMessageBox.warning(
                self,
                "Validation Error",
                "At least one output format is required"
            )
            return

        # Save values from UI to config
        self._save_values()

        # Update original config with edited values
        import copy
        self._config = copy.deepcopy(self._edited_config)

        # Emit configuration updated signal
        self.configUpdated.emit(self._config.id)

        # Call parent accept method
        super().accept()

    def reject(self) -> None:
        """Handle dialog rejection (Cancel button)."""
        # Confirm if there are unsaved changes
        if self._has_unsaved_changes():
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to discard them?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if result != QMessageBox.Yes:
                return

        # Call parent reject method
        super().reject()

    def _has_unsaved_changes(self) -> bool:
        """
        Check if there are unsaved changes.

        Returns:
            True if there are unsaved changes, False otherwise
        """
        # Simple checks for common changes
        if self._name_edit.text() != self._config.name:
            return True

        if self._description_edit.toPlainText() != (self._config.description or ""):
            return True

        if self._output_dir_edit.text() != (self._config.output_directory or ""):
            return True

        if self._edited_config.output_formats != self._config.output_formats:
            return True

        # For more complex changes, we'd need deeper comparison
        return False

    @Slot(int)
    def _on_bg_method_changed(self, index: int) -> None:
        """
        Handle background removal method change.

        Args:
            index: Selected method combo index
        """
        self._update_method_description()
        self._update_method_ui()

    @Slot()
    def _on_chroma_color(self) -> None:
        """Handle chroma color button click."""
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor

        # Get current color
        bg_style = self._chroma_color_btn.styleSheet()
        import re
        color_match = re.search(r'background-color: ([^;]+);', bg_style)
        current_color = QColor("#00FF00")  # Default to green
        if color_match:
            current_color = QColor(color_match.group(1))

        # Show color dialog
        color = QColorDialog.getColor(
            current_color,
            self,
            "Select Chroma Key Color"
        )

        if color.isValid():
            self._chroma_color_btn.setStyleSheet(
                f"background-color: {color.name()};"
            )

    @Slot()
    def _on_browse_mask(self) -> None:
        """Handle browse mask button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Mask Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )

        if file_path:
            self._mask_path_edit.setText(file_path)

    @Slot()
    def _on_browse_dir(self) -> None:
        """Handle browse output directory button click."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self._output_dir_edit.text()
        )

        if dir_path:
            self._output_dir_edit.setText(dir_path)

    @Slot()
    def _on_format_selection_changed(self) -> None:
        """Handle format selection change in list view."""
        selected_indexes = self._formats_list.selectedIndexes()
        has_selection = bool(selected_indexes)

        self._edit_format_btn.setEnabled(has_selection)
        self._remove_format_btn.setEnabled(has_selection)

        if has_selection:
            # Get selected format ID
            selected_index = selected_indexes[0]
            format_id = self._formats_model.data(selected_index, Qt.UserRole)

            # Update details panel
            self._update_format_details(format_id)
        else:
            # Clear details panel
            self._update_format_details(None)

    @Slot()
    def _on_add_format(self) -> None:
        """Handle add format button click."""
        # Create a new default format
        from ..models.processing_config import OutputFormat, ImageFormat

        new_format = OutputFormat(
            name=f"Format {len(self._edited_config.output_formats) + 1}",
            format=ImageFormat.PNG
        )

        # Add to config
        self._edited_config.output_formats.append(new_format)

        # Update list
        self._update_formats_list()

        # Select and edit the new format
        last_row = self._formats_model.rowCount() - 1
        self._formats_list.setCurrentIndex(self._formats_model.index(last_row, 0))
        self._on_edit_format()

    @Slot()
    def _on_edit_format(self) -> None:
        """Handle edit format button click."""
        selected_indexes = self._formats_list.selectedIndexes()
        if not selected_indexes:
            return

        # Get selected format ID
        selected_index = selected_indexes[0]
        format_id = self._formats_model.data(selected_index, Qt.UserRole)

        # Find the format
        selected_format = None
        for i, fmt in enumerate(self._edited_config.output_formats):
            if fmt.id == format_id:
                selected_format = fmt
                selected_index = i
                break

        if not selected_format:
            return

        # Create and show format editor dialog
        format_editor = FormatEditorDialog(
            selected_format,
            self._logger,
            self
        )

        if format_editor.exec() == QDialog.Accepted:
            # Get updated format
            updated_format = format_editor.get_format()

            # Update format in config
            self._edited_config.output_formats[selected_index] = updated_format

            # Update formats list
            self._update_formats_list()

            # Re-select the format
            for row in range(self._formats_model.rowCount()):
                index = self._formats_model.index(row, 0)
                if self._formats_model.data(index, Qt.UserRole) == updated_format.id:
                    self._formats_list.setCurrentIndex(index)
                    break

            # Update details
            self._update_format_details(updated_format.id)

    @Slot()
    def _on_remove_format(self) -> None:
        """Handle remove format button click."""
        selected_indexes = self._formats_list.selectedIndexes()
        if not selected_indexes:
            return

        # Get selected format ID
        selected_index = selected_indexes[0]
        format_id = self._formats_model.data(selected_index, Qt.UserRole)

        # Confirm removal
        result = QMessageBox.question(
            self,
            "Remove Format",
            "Are you sure you want to remove this format?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result != QMessageBox.Yes:
            return

        # Remove the format
        self._edited_config.output_formats = [
            fmt for fmt in self._edited_config.output_formats
            if fmt.id != format_id
        ]

        # Update formats list
        self._update_formats_list()

        # Clear details
        self._update_format_details(None)

        # Update button states
        self._edit_format_btn.setEnabled(False)
        self._remove_format_btn.setEnabled(False)

    @Slot(bool)
    def _on_subfolder_toggle(self, enabled: bool) -> None:
        """
        Handle subfolder checkbox toggle.

        Args:
            enabled: Whether subfolder creation is enabled
        """
        self._subfolder_template_edit.setEnabled(enabled)

    def get_config(self) -> ProcessingConfig:
        """
        Get the edited configuration.

        Returns:
            Updated processing configuration
        """
        return self._edited_config