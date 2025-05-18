from __future__ import annotations

"""
Format editor dialog for the Media Processor Plugin.

This module provides a dialog for editing output format configurations,
including size, background, watermarks, and other settings.
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QColor, QIcon, QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QTabWidget, QWidget, QColorDialog, QFileDialog,
    QDialogButtonBox, QGroupBox, QRadioButton, QButtonGroup, QScrollArea,
    QSizePolicy, QSlider, QToolButton, QFrame
)

from ..models.processing_config import (
    OutputFormat,
    ImageFormat,
    ResizeMode,
    WatermarkType,
    WatermarkPosition
)


class ColorButton(QPushButton):
    """Button for selecting colors with preview."""

    colorChanged = Signal(QColor)

    def __init__(
            self,
            color: Optional[str] = None,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the color button.

        Args:
            color: Initial color in hex format
            parent: Parent widget
        """
        super().__init__(parent)

        self._color = QColor("#FFFFFF")
        if color:
            self._color = QColor(color)

        self.setFixedSize(32, 32)
        self.clicked.connect(self._on_clicked)
        self._update_style()

    def _update_style(self) -> None:
        """Update button style to show selected color."""
        r, g, b, a = self._color.getRgb()

        # Calculate contrasting text color
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = "#000000" if brightness > 128 else "#FFFFFF"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({r}, {g}, {b}, {a});
                border: 1px solid #888888;
                border-radius: 4px;
                color: {text_color};
            }}
            QPushButton:hover {{
                border: 2px solid #0078D7;
            }}
        """)

    def _on_clicked(self) -> None:
        """Handle button click to show color dialog."""
        color = QColorDialog.getColor(
            self._color,
            self,
            "Select Color",
            QColorDialog.ShowAlphaChannel
        )

        if color.isValid():
            self._color = color
            self._update_style()
            self.colorChanged.emit(self._color)

    def get_color(self) -> QColor:
        """
        Get the selected color.

        Returns:
            Selected color
        """
        return self._color

    def set_color(self, color: Union[str, QColor]) -> None:
        """
        Set the button color.

        Args:
            color: New color as hex string or QColor
        """
        if isinstance(color, str):
            self._color = QColor(color)
        else:
            self._color = color

        self._update_style()
        self.colorChanged.emit(self._color)

    def get_hex_color(self) -> str:
        """
        Get the color as hex string.

        Returns:
            Color in hex format (#RRGGBB)
        """
        return self._color.name()


class FormatEditorDialog(QDialog):
    """
    Dialog for editing output format settings.

    Allows editing:
    - Format type and quality
    - Size and cropping
    - Background settings
    - Watermarks
    - Naming and organization
    """

    def __init__(
            self,
            format_config: OutputFormat,
            logger: Any,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the format editor dialog.

        Args:
            format_config: Output format configuration to edit
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)

        self._format_config = format_config
        self._logger = logger

        # Create a deep copy of the format config
        import copy
        self._edited_format = copy.deepcopy(format_config)

        # Initialize UI
        self._init_ui()

        # Load config values into UI
        self._load_values()

        # Set window title
        self.setWindowTitle(f"Edit Format: {format_config.name}")

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create tab widget for organizing settings
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Basic settings tab
        basic_tab = self._create_basic_tab()
        tab_widget.addTab(basic_tab, "Basic Settings")

        # Size and cropping tab
        size_tab = self._create_size_tab()
        tab_widget.addTab(size_tab, "Size & Cropping")

        # Background tab
        background_tab = self._create_background_tab()
        tab_widget.addTab(background_tab, "Background")

        # Watermark tab
        watermark_tab = self._create_watermark_tab()
        tab_widget.addTab(watermark_tab, "Watermark")

        # File tab (naming, subdir, etc)
        file_tab = self._create_file_tab()
        tab_widget.addTab(file_tab, "File Settings")

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Set dialog size
        self.resize(600, 500)

    def _create_basic_tab(self) -> QWidget:
        """
        Create the basic settings tab.

        Returns:
            Widget containing basic format settings
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Format name
        name_layout = QHBoxLayout()
        name_label = QLabel("Format Name:")
        self._name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self._name_edit, 1)  # 1 = stretch factor
        layout.addLayout(name_layout)

        # Settings group
        settings_group = QGroupBox("Format Settings")
        settings_layout = QFormLayout(settings_group)

        # File format
        self._format_combo = QComboBox()
        for format_type in ImageFormat:
            self._format_combo.addItem(
                format_type.value.upper(),
                format_type.value
            )
        settings_layout.addRow("File Format:", self._format_combo)

        # Quality
        self._quality_slider = QSlider(Qt.Horizontal)
        self._quality_slider.setMinimum(1)
        self._quality_slider.setMaximum(100)
        self._quality_slider.setTickPosition(QSlider.TicksBelow)
        self._quality_slider.setTickInterval(10)

        self._quality_label = QLabel("90")
        self._quality_slider.valueChanged.connect(
            lambda v: self._quality_label.setText(str(v))
        )

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self._quality_slider)
        quality_layout.addWidget(self._quality_label)

        settings_layout.addRow("Quality:", quality_layout)

        # Image adjustments
        adj_group = QGroupBox("Image Adjustments")
        adj_layout = QFormLayout(adj_group)

        # Brightness
        self._brightness_spin = QDoubleSpinBox()
        self._brightness_spin.setRange(0.0, 2.0)
        self._brightness_spin.setSingleStep(0.1)
        self._brightness_spin.setDecimals(1)
        adj_layout.addRow("Brightness:", self._brightness_spin)

        # Contrast
        self._contrast_spin = QDoubleSpinBox()
        self._contrast_spin.setRange(0.0, 2.0)
        self._contrast_spin.setSingleStep(0.1)
        self._contrast_spin.setDecimals(1)
        adj_layout.addRow("Contrast:", self._contrast_spin)

        # Saturation
        self._saturation_spin = QDoubleSpinBox()
        self._saturation_spin.setRange(0.0, 2.0)
        self._saturation_spin.setSingleStep(0.1)
        self._saturation_spin.setDecimals(1)
        adj_layout.addRow("Saturation:", self._saturation_spin)

        # Sharpness
        self._sharpness_spin = QDoubleSpinBox()
        self._sharpness_spin.setRange(0.0, 2.0)
        self._sharpness_spin.setSingleStep(0.1)
        self._sharpness_spin.setDecimals(1)
        adj_layout.addRow("Sharpness:", self._sharpness_spin)

        # Add groups to layout
        layout.addWidget(settings_group)
        layout.addWidget(adj_group)

        # Add vertical spacer
        layout.addStretch()

        return tab

    def _create_size_tab(self) -> QWidget:
        """
        Create the size and cropping tab.

        Returns:
            Widget containing size and cropping settings
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Resize group
        resize_group = QGroupBox("Resize")
        resize_layout = QVBoxLayout(resize_group)

        # Resize mode
        mode_form = QFormLayout()
        self._resize_mode_combo = QComboBox()
        for resize_mode in ResizeMode:
            self._resize_mode_combo.addItem(
                resize_mode.value.replace('_', ' ').title(),
                resize_mode.value
            )
        mode_form.addRow("Resize Mode:", self._resize_mode_combo)

        # Connect resize mode changes
        self._resize_mode_combo.currentIndexChanged.connect(self._on_resize_mode_changed)

        resize_layout.addLayout(mode_form)

        # Size settings
        size_layout = QHBoxLayout()

        # Width
        width_layout = QVBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        self._width_spin = QSpinBox()
        self._width_spin.setRange(1, 10000)
        self._width_spin.setSuffix(" px")
        width_layout.addWidget(self._width_spin)
        size_layout.addLayout(width_layout)

        # Height
        height_layout = QVBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        self._height_spin = QSpinBox()
        self._height_spin.setRange(1, 10000)
        self._height_spin.setSuffix(" px")
        height_layout.addWidget(self._height_spin)
        size_layout.addLayout(height_layout)

        # Percentage
        percentage_layout = QVBoxLayout()
        percentage_layout.addWidget(QLabel("Percentage:"))
        self._percentage_spin = QSpinBox()
        self._percentage_spin.setRange(1, 1000)
        self._percentage_spin.setSuffix(" %")
        percentage_layout.addWidget(self._percentage_spin)
        size_layout.addLayout(percentage_layout)

        resize_layout.addLayout(size_layout)

        # Maintain aspect ratio
        self._maintain_aspect_check = QCheckBox("Maintain aspect ratio")
        resize_layout.addWidget(self._maintain_aspect_check)

        # Crop group
        crop_group = QGroupBox("Cropping")
        crop_layout = QVBoxLayout(crop_group)

        # Enable cropping
        self._crop_check = QCheckBox("Enable cropping")
        self._crop_check.toggled.connect(self._on_crop_toggle)
        crop_layout.addWidget(self._crop_check)

        # Crop settings
        crop_settings = QWidget()
        crop_form = QFormLayout(crop_settings)

        # Crop values
        self._crop_left_spin = QSpinBox()
        self._crop_left_spin.setRange(0, 10000)
        self._crop_left_spin.setSuffix(" px")
        crop_form.addRow("Left:", self._crop_left_spin)

        self._crop_top_spin = QSpinBox()
        self._crop_top_spin.setRange(0, 10000)
        self._crop_top_spin.setSuffix(" px")
        crop_form.addRow("Top:", self._crop_top_spin)

        self._crop_right_spin = QSpinBox()
        self._crop_right_spin.setRange(0, 10000)
        self._crop_right_spin.setSuffix(" px")
        crop_form.addRow("Right:", self._crop_right_spin)

        self._crop_bottom_spin = QSpinBox()
        self._crop_bottom_spin.setRange(0, 10000)
        self._crop_bottom_spin.setSuffix(" px")
        crop_form.addRow("Bottom:", self._crop_bottom_spin)

        crop_layout.addWidget(crop_settings)

        # Padding group
        padding_group = QGroupBox("Padding")
        padding_layout = QVBoxLayout(padding_group)

        # Enable padding
        self._padding_check = QCheckBox("Enable padding")
        self._padding_check.toggled.connect(self._on_padding_toggle)
        padding_layout.addWidget(self._padding_check)

        # Padding settings
        padding_settings = QWidget()
        padding_form = QFormLayout(padding_settings)

        # Padding values
        self._padding_left_spin = QSpinBox()
        self._padding_left_spin.setRange(0, 1000)
        self._padding_left_spin.setSuffix(" px")
        padding_form.addRow("Left:", self._padding_left_spin)

        self._padding_top_spin = QSpinBox()
        self._padding_top_spin.setRange(0, 1000)
        self._padding_top_spin.setSuffix(" px")
        padding_form.addRow("Top:", self._padding_top_spin)

        self._padding_right_spin = QSpinBox()
        self._padding_right_spin.setRange(0, 1000)
        self._padding_right_spin.setSuffix(" px")
        padding_form.addRow("Right:", self._padding_right_spin)

        self._padding_bottom_spin = QSpinBox()
        self._padding_bottom_spin.setRange(0, 1000)
        self._padding_bottom_spin.setSuffix(" px")
        padding_form.addRow("Bottom:", self._padding_bottom_spin)

        # Padding color
        padding_color_layout = QHBoxLayout()
        padding_color_layout.addWidget(QLabel("Color:"))
        self._padding_color_btn = ColorButton()
        padding_color_layout.addWidget(self._padding_color_btn)
        padding_color_layout.addStretch()

        padding_form.addRow("", padding_color_layout)
        padding_layout.addWidget(padding_settings)

        # Rotation
        rotation_group = QGroupBox("Rotation")
        rotation_layout = QFormLayout(rotation_group)

        self._rotation_spin = QDoubleSpinBox()
        self._rotation_spin.setRange(-360, 360)
        self._rotation_spin.setSingleStep(1)
        self._rotation_spin.setDecimals(1)
        self._rotation_spin.setSuffix("°")
        rotation_layout.addRow("Angle:", self._rotation_spin)

        # Add all groups to layout
        layout.addWidget(resize_group)
        layout.addWidget(crop_group)
        layout.addWidget(padding_group)
        layout.addWidget(rotation_group)

        return tab

    def _create_background_tab(self) -> QWidget:
        """
        Create the background settings tab.

        Returns:
            Widget containing background settings
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Background group
        bg_group = QGroupBox("Background Settings")
        bg_layout = QVBoxLayout(bg_group)

        # Background type
        self._transparent_check = QCheckBox("Transparent Background")
        self._transparent_check.toggled.connect(self._on_transparent_toggle)
        bg_layout.addWidget(self._transparent_check)

        # Background color
        bg_color_layout = QHBoxLayout()
        bg_color_layout.addWidget(QLabel("Background Color:"))
        self._bg_color_btn = ColorButton()
        bg_color_layout.addWidget(self._bg_color_btn)
        bg_color_layout.addStretch()

        bg_layout.addLayout(bg_color_layout)

        # Add description for format compatibility
        compat_label = QLabel(
            "Note: Transparency is only supported in PNG, WEBP, and TIFF formats."
        )
        compat_label.setWordWrap(True)
        compat_label.setStyleSheet("color: #666;")
        bg_layout.addWidget(compat_label)

        # Add to layout
        layout.addWidget(bg_group)

        # Add vertical spacer
        layout.addStretch()

        return tab

    def _create_watermark_tab(self) -> QWidget:
        """
        Create the watermark settings tab.

        Returns:
            Widget containing watermark settings
        """
        tab = QWidget()

        # Create a scroll area for the watermark settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        # Create the content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        # Watermark group
        wm_group = QGroupBox("Watermark Settings")
        wm_layout = QVBoxLayout(wm_group)

        # Watermark type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Watermark Type:"))
        self._wm_type_combo = QComboBox()
        self._wm_type_combo.addItem("None", WatermarkType.NONE.value)
        self._wm_type_combo.addItem("Text", WatermarkType.TEXT.value)
        self._wm_type_combo.addItem("Image", WatermarkType.IMAGE.value)
        self._wm_type_combo.currentIndexChanged.connect(self._on_watermark_type_changed)
        type_layout.addWidget(self._wm_type_combo)

        wm_layout.addLayout(type_layout)

        # Text watermark settings
        self._text_wm_widget = QWidget()
        text_wm_layout = QFormLayout(self._text_wm_widget)

        self._wm_text_edit = QLineEdit()
        text_wm_layout.addRow("Text:", self._wm_text_edit)

        self._wm_font_combo = QComboBox()
        from PySide6.QtGui import QFontDatabase
        for family in QFontDatabase().families():
            self._wm_font_combo.addItem(family)
        text_wm_layout.addRow("Font:", self._wm_font_combo)

        self._wm_font_size_spin = QSpinBox()
        self._wm_font_size_spin.setRange(1, 500)
        self._wm_font_size_spin.setSuffix(" pt")
        text_wm_layout.addRow("Font Size:", self._wm_font_size_spin)

        text_font_color_layout = QHBoxLayout()
        self._wm_font_color_btn = ColorButton()
        text_font_color_layout.addWidget(self._wm_font_color_btn)
        text_font_color_layout.addStretch()
        text_wm_layout.addRow("Font Color:", text_font_color_layout)

        text_outline_layout = QHBoxLayout()
        self._wm_outline_check = QCheckBox("Enable Outline")
        self._wm_outline_check.toggled.connect(self._on_outline_toggle)
        text_outline_layout.addWidget(self._wm_outline_check)
        text_wm_layout.addRow("", text_outline_layout)

        self._outline_settings = QWidget()
        outline_layout = QFormLayout(self._outline_settings)

        self._wm_outline_width_spin = QSpinBox()
        self._wm_outline_width_spin.setRange(1, 20)
        self._wm_outline_width_spin.setSuffix(" px")
        outline_layout.addRow("Outline Width:", self._wm_outline_width_spin)

        outline_color_layout = QHBoxLayout()
        self._wm_outline_color_btn = ColorButton()
        outline_color_layout.addWidget(self._wm_outline_color_btn)
        outline_color_layout.addStretch()
        outline_layout.addRow("Outline Color:", outline_color_layout)

        text_wm_layout.addRow("", self._outline_settings)

        wm_layout.addWidget(self._text_wm_widget)

        # Image watermark settings
        self._image_wm_widget = QWidget()
        image_wm_layout = QFormLayout(self._image_wm_widget)

        image_path_layout = QHBoxLayout()
        self._wm_image_edit = QLineEdit()
        self._wm_image_edit.setReadOnly(True)
        image_path_layout.addWidget(self._wm_image_edit, 1)

        self._wm_image_btn = QToolButton()
        self._wm_image_btn.setText("...")
        self._wm_image_btn.clicked.connect(self._on_browse_watermark)
        image_path_layout.addWidget(self._wm_image_btn)

        image_wm_layout.addRow("Image:", image_path_layout)

        wm_layout.addWidget(self._image_wm_widget)

        # Common watermark settings
        self._common_wm_widget = QWidget()
        common_wm_layout = QFormLayout(self._common_wm_widget)

        self._wm_position_combo = QComboBox()
        for pos in WatermarkPosition:
            pos_name = pos.value.replace('_', ' ').title()
            self._wm_position_combo.addItem(pos_name, pos.value)
        self._wm_position_combo.currentIndexChanged.connect(self._on_wm_position_changed)
        common_wm_layout.addRow("Position:", self._wm_position_combo)

        # Custom position settings
        self._custom_pos_widget = QWidget()
        custom_pos_layout = QFormLayout(self._custom_pos_widget)

        self._wm_pos_x_spin = QDoubleSpinBox()
        self._wm_pos_x_spin.setRange(0, 1)
        self._wm_pos_x_spin.setSingleStep(0.05)
        self._wm_pos_x_spin.setDecimals(2)
        custom_pos_layout.addRow("X Position (0-1):", self._wm_pos_x_spin)

        self._wm_pos_y_spin = QDoubleSpinBox()
        self._wm_pos_y_spin.setRange(0, 1)
        self._wm_pos_y_spin.setSingleStep(0.05)
        self._wm_pos_y_spin.setDecimals(2)
        custom_pos_layout.addRow("Y Position (0-1):", self._wm_pos_y_spin)

        common_wm_layout.addRow("", self._custom_pos_widget)

        self._wm_opacity_spin = QDoubleSpinBox()
        self._wm_opacity_spin.setRange(0, 1)
        self._wm_opacity_spin.setSingleStep(0.1)
        self._wm_opacity_spin.setDecimals(1)
        common_wm_layout.addRow("Opacity:", self._wm_opacity_spin)

        self._wm_scale_spin = QDoubleSpinBox()
        self._wm_scale_spin.setRange(0.01, 1)
        self._wm_scale_spin.setSingleStep(0.05)
        self._wm_scale_spin.setDecimals(2)
        common_wm_layout.addRow("Scale:", self._wm_scale_spin)

        self._wm_margin_spin = QSpinBox()
        self._wm_margin_spin.setRange(0, 200)
        self._wm_margin_spin.setSuffix(" px")
        common_wm_layout.addRow("Margin:", self._wm_margin_spin)

        self._wm_rotation_spin = QDoubleSpinBox()
        self._wm_rotation_spin.setRange(-360, 360)
        self._wm_rotation_spin.setSingleStep(1)
        self._wm_rotation_spin.setDecimals(1)
        self._wm_rotation_spin.setSuffix("°")
        common_wm_layout.addRow("Rotation:", self._wm_rotation_spin)

        wm_layout.addWidget(self._common_wm_widget)

        # Add to layout
        layout.addWidget(wm_group)

        # Add vertical spacer
        layout.addStretch()

        # Set content widget for scroll area
        scroll.setWidget(content)

        # Set scroll area as tab widget
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)

        return tab

    def _create_file_tab(self) -> QWidget:
        """
        Create the file settings tab.

        Returns:
            Widget containing file naming and path settings
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # File naming group
        naming_group = QGroupBox("File Naming")
        naming_layout = QFormLayout(naming_group)

        # Prefix
        self._prefix_edit = QLineEdit()
        naming_layout.addRow("Prefix:", self._prefix_edit)

        # Suffix
        self._suffix_edit = QLineEdit()
        naming_layout.addRow("Suffix:", self._suffix_edit)

        # Naming template
        self._template_edit = QLineEdit()
        naming_layout.addRow("Template:", self._template_edit)

        # Template help
        template_help = QLabel(
            "Available placeholders: {name}, {ext}, {date}, {time}, {timestamp}, {random}, {counter}"
        )
        template_help.setWordWrap(True)
        template_help.setStyleSheet("color: #666;")
        naming_layout.addRow("", template_help)

        # Output directory group
        dir_group = QGroupBox("Output Directory")
        dir_layout = QFormLayout(dir_group)

        # Subdirectory
        self._subdir_edit = QLineEdit()
        dir_layout.addRow("Subdirectory:", self._subdir_edit)

        # Subdir help
        subdir_help = QLabel(
            "Files will be saved to this subdirectory within the main output directory."
        )
        subdir_help.setWordWrap(True)
        subdir_help.setStyleSheet("color: #666;")
        dir_layout.addRow("", subdir_help)

        # Add groups to layout
        layout.addWidget(naming_group)
        layout.addWidget(dir_group)

        # Add vertical spacer
        layout.addStretch()

        return tab

    def _load_values(self) -> None:
        """Load values from format config into UI controls."""
        # Basic tab
        self._name_edit.setText(self._edited_format.name)

        # File format
        format_index = self._format_combo.findData(self._edited_format.format.value)
        if format_index >= 0:
            self._format_combo.setCurrentIndex(format_index)

        # Quality
        self._quality_slider.setValue(self._edited_format.quality)

        # Image adjustments
        self._brightness_spin.setValue(self._edited_format.brightness)
        self._contrast_spin.setValue(self._edited_format.contrast)
        self._saturation_spin.setValue(self._edited_format.saturation)
        self._sharpness_spin.setValue(self._edited_format.sharpness)

        # Size tab
        # Resize mode
        resize_index = self._resize_mode_combo.findData(self._edited_format.resize_mode.value)
        if resize_index >= 0:
            self._resize_mode_combo.setCurrentIndex(resize_index)

        # Width/height/percentage
        if self._edited_format.width is not None:
            self._width_spin.setValue(self._edited_format.width)
        if self._edited_format.height is not None:
            self._height_spin.setValue(self._edited_format.height)
        if self._edited_format.percentage is not None:
            self._percentage_spin.setValue(self._edited_format.percentage)

        # Maintain aspect ratio
        self._maintain_aspect_check.setChecked(self._edited_format.maintain_aspect_ratio)

        # Cropping
        self._crop_check.setChecked(self._edited_format.crop_enabled)
        if self._edited_format.crop_left is not None:
            self._crop_left_spin.setValue(self._edited_format.crop_left)
        if self._edited_format.crop_top is not None:
            self._crop_top_spin.setValue(self._edited_format.crop_top)
        if self._edited_format.crop_right is not None:
            self._crop_right_spin.setValue(self._edited_format.crop_right)
        if self._edited_format.crop_bottom is not None:
            self._crop_bottom_spin.setValue(self._edited_format.crop_bottom)

        # Padding
        self._padding_check.setChecked(self._edited_format.padding_enabled)
        self._padding_left_spin.setValue(self._edited_format.padding_left)
        self._padding_top_spin.setValue(self._edited_format.padding_top)
        self._padding_right_spin.setValue(self._edited_format.padding_right)
        self._padding_bottom_spin.setValue(self._edited_format.padding_bottom)

        # Padding color
        if self._edited_format.padding_color:
            self._padding_color_btn.set_color(self._edited_format.padding_color)
        else:
            # Use background color as fallback
            self._padding_color_btn.set_color(
                self._edited_format.background_color or "#FFFFFF"
            )

        # Rotation
        self._rotation_spin.setValue(self._edited_format.rotation_angle)

        # Background tab
        self._transparent_check.setChecked(self._edited_format.transparent_background)
        if self._edited_format.background_color:
            self._bg_color_btn.set_color(self._edited_format.background_color)

        # Watermark tab
        # Type
        watermark_type = self._edited_format.watermark.type
        type_index = self._wm_type_combo.findData(watermark_type.value)
        if type_index >= 0:
            self._wm_type_combo.setCurrentIndex(type_index)

        # Text watermark
        if self._edited_format.watermark.text:
            self._wm_text_edit.setText(self._edited_format.watermark.text)

        # Font
        font_index = self._wm_font_combo.findText(
            self._edited_format.watermark.font_name
        )
        if font_index >= 0:
            self._wm_font_combo.setCurrentIndex(font_index)

        self._wm_font_size_spin.setValue(self._edited_format.watermark.font_size)

        if self._edited_format.watermark.font_color:
            self._wm_font_color_btn.set_color(self._edited_format.watermark.font_color)

        # Outline
        has_outline = (
                self._edited_format.watermark.outline_width > 0 and
                self._edited_format.watermark.outline_color is not None
        )
        self._wm_outline_check.setChecked(has_outline)

        if self._edited_format.watermark.outline_color:
            self._wm_outline_color_btn.set_color(
                self._edited_format.watermark.outline_color
            )

        self._wm_outline_width_spin.setValue(
            max(1, self._edited_format.watermark.outline_width)
        )

        # Image watermark
        if self._edited_format.watermark.image_path:
            self._wm_image_edit.setText(self._edited_format.watermark.image_path)

        # Position
        position_index = self._wm_position_combo.findData(
            self._edited_format.watermark.position.value
        )
        if position_index >= 0:
            self._wm_position_combo.setCurrentIndex(position_index)

        # Custom position
        if self._edited_format.watermark.custom_position_x is not None:
            self._wm_pos_x_spin.setValue(self._edited_format.watermark.custom_position_x)
        if self._edited_format.watermark.custom_position_y is not None:
            self._wm_pos_y_spin.setValue(self._edited_format.watermark.custom_position_y)

        # Common settings
        self._wm_opacity_spin.setValue(self._edited_format.watermark.opacity)
        self._wm_scale_spin.setValue(self._edited_format.watermark.scale)
        self._wm_margin_spin.setValue(self._edited_format.watermark.margin)
        self._wm_rotation_spin.setValue(self._edited_format.watermark.rotation)

        # File settings tab
        if self._edited_format.prefix:
            self._prefix_edit.setText(self._edited_format.prefix)
        if self._edited_format.suffix:
            self._suffix_edit.setText(self._edited_format.suffix)
        if self._edited_format.naming_template:
            self._template_edit.setText(self._edited_format.naming_template)
        if self._edited_format.subdir:
            self._subdir_edit.setText(self._edited_format.subdir)

        # Update UI state based on loaded values
        self._on_resize_mode_changed()
        self._on_crop_toggle(self._edited_format.crop_enabled)
        self._on_padding_toggle(self._edited_format.padding_enabled)
        self._on_transparent_toggle(self._edited_format.transparent_background)
        self._on_watermark_type_changed()
        self._on_outline_toggle(has_outline)
        self._on_wm_position_changed()

    def _save_values(self) -> None:
        """Save values from UI controls to format config."""
        # Basic tab
        self._edited_format.name = self._name_edit.text()

        # File format
        format_data = self._format_combo.currentData()
        if format_data:
            self._edited_format.format = ImageFormat(format_data)

        # Quality
        self._edited_format.quality = self._quality_slider.value()

        # Image adjustments
        self._edited_format.brightness = self._brightness_spin.value()
        self._edited_format.contrast = self._contrast_spin.value()
        self._edited_format.saturation = self._saturation_spin.value()
        self._edited_format.sharpness = self._sharpness_spin.value()

        # Size tab
        # Resize mode
        resize_data = self._resize_mode_combo.currentData()
        if resize_data:
            self._edited_format.resize_mode = ResizeMode(resize_data)

        # Size settings
        self._edited_format.width = self._width_spin.value() if self._width_spin.isEnabled() else None
        self._edited_format.height = self._height_spin.value() if self._height_spin.isEnabled() else None
        self._edited_format.percentage = self._percentage_spin.value() if self._percentage_spin.isEnabled() else None
        self._edited_format.maintain_aspect_ratio = self._maintain_aspect_check.isChecked()

        # Cropping
        self._edited_format.crop_enabled = self._crop_check.isChecked()
        if self._edited_format.crop_enabled:
            self._edited_format.crop_left = self._crop_left_spin.value()
            self._edited_format.crop_top = self._crop_top_spin.value()
            self._edited_format.crop_right = self._crop_right_spin.value()
            self._edited_format.crop_bottom = self._crop_bottom_spin.value()

        # Padding
        self._edited_format.padding_enabled = self._padding_check.isChecked()
        if self._edited_format.padding_enabled:
            self._edited_format.padding_left = self._padding_left_spin.value()
            self._edited_format.padding_top = self._padding_top_spin.value()
            self._edited_format.padding_right = self._padding_right_spin.value()
            self._edited_format.padding_bottom = self._padding_bottom_spin.value()
            self._edited_format.padding_color = self._padding_color_btn.get_hex_color()

        # Rotation
        self._edited_format.rotation_angle = self._rotation_spin.value()

        # Background tab
        self._edited_format.transparent_background = self._transparent_check.isChecked()
        if not self._edited_format.transparent_background:
            self._edited_format.background_color = self._bg_color_btn.get_hex_color()

        # Watermark tab
        # Type
        watermark_type_data = self._wm_type_combo.currentData()
        if watermark_type_data:
            self._edited_format.watermark.type = WatermarkType(watermark_type_data)

        # Text watermark
        if self._edited_format.watermark.type == WatermarkType.TEXT:
            self._edited_format.watermark.text = self._wm_text_edit.text()
            self._edited_format.watermark.font_name = self._wm_font_combo.currentText()
            self._edited_format.watermark.font_size = self._wm_font_size_spin.value()
            self._edited_format.watermark.font_color = self._wm_font_color_btn.get_hex_color()

            if self._wm_outline_check.isChecked():
                self._edited_format.watermark.outline_width = self._wm_outline_width_spin.value()
                self._edited_format.watermark.outline_color = self._wm_outline_color_btn.get_hex_color()
            else:
                self._edited_format.watermark.outline_width = 0
                self._edited_format.watermark.outline_color = None

        # Image watermark
        if self._edited_format.watermark.type == WatermarkType.IMAGE:
            self._edited_format.watermark.image_path = self._wm_image_edit.text()

        # Position
        position_data = self._wm_position_combo.currentData()
        if position_data:
            self._edited_format.watermark.position = WatermarkPosition(position_data)

        # Custom position
        if self._edited_format.watermark.position == WatermarkPosition.CUSTOM:
            self._edited_format.watermark.custom_position_x = self._wm_pos_x_spin.value()
            self._edited_format.watermark.custom_position_y = self._wm_pos_y_spin.value()
        else:
            self._edited_format.watermark.custom_position_x = None
            self._edited_format.watermark.custom_position_y = None

        # Common settings
        self._edited_format.watermark.opacity = self._wm_opacity_spin.value()
        self._edited_format.watermark.scale = self._wm_scale_spin.value()
        self._edited_format.watermark.margin = self._wm_margin_spin.value()
        self._edited_format.watermark.rotation = self._wm_rotation_spin.value()

        # File settings tab
        self._edited_format.prefix = self._prefix_edit.text() or None
        self._edited_format.suffix = self._suffix_edit.text() or None
        self._edited_format.naming_template = self._template_edit.text() or None
        self._edited_format.subdir = self._subdir_edit.text() or None

    def accept(self) -> None:
        """Handle dialog acceptance (OK button)."""
        # Save values from UI to format config
        self._save_values()

        # Call parent accept method
        super().accept()

    def get_format(self) -> OutputFormat:
        """
        Get the edited format configuration.

        Returns:
            Updated output format configuration
        """
        return self._edited_format

    @Slot(int)
    def _on_resize_mode_changed(self, index: int = -1) -> None:
        """
        Handle resize mode change.

        Args:
            index: Selected resize mode combo index (unused)
        """
        resize_mode = self._resize_mode_combo.currentData()

        # Enable/disable controls based on resize mode
        self._width_spin.setEnabled(
            resize_mode in (
                ResizeMode.WIDTH.value,
                ResizeMode.EXACT.value,
                ResizeMode.MAX_DIMENSION.value,
                ResizeMode.MIN_DIMENSION.value
            )
        )

        self._height_spin.setEnabled(
            resize_mode in (
                ResizeMode.HEIGHT.value,
                ResizeMode.EXACT.value,
                ResizeMode.MAX_DIMENSION.value,
                ResizeMode.MIN_DIMENSION.value
            )
        )

        self._percentage_spin.setEnabled(
            resize_mode == ResizeMode.PERCENTAGE.value
        )

        self._maintain_aspect_check.setEnabled(
            resize_mode in (
                ResizeMode.WIDTH.value,
                ResizeMode.HEIGHT.value,
                ResizeMode.EXACT.value
            )
        )

    @Slot(bool)
    def _on_crop_toggle(self, enabled: bool) -> None:
        """
        Handle crop checkbox toggle.

        Args:
            enabled: Whether cropping is enabled
        """
        for widget in self._crop_left_spin.parent().findChildren(QWidget):
            if widget != self._crop_check:
                widget.setEnabled(enabled)

    @Slot(bool)
    def _on_padding_toggle(self, enabled: bool) -> None:
        """
        Handle padding checkbox toggle.

        Args:
            enabled: Whether padding is enabled
        """
        for widget in self._padding_left_spin.parent().findChildren(QWidget):
            if widget != self._padding_check:
                widget.setEnabled(enabled)

    @Slot(bool)
    def _on_transparent_toggle(self, transparent: bool) -> None:
        """
        Handle transparent background checkbox toggle.

        Args:
            transparent: Whether background is transparent
        """
        self._bg_color_btn.setEnabled(not transparent)

    @Slot(int)
    def _on_watermark_type_changed(self, index: int = -1) -> None:
        """
        Handle watermark type change.

        Args:
            index: Selected watermark type combo index (unused)
        """
        wm_type = self._wm_type_combo.currentData()

        # Show/hide appropriate watermark settings
        self._text_wm_widget.setVisible(wm_type == WatermarkType.TEXT.value)
        self._image_wm_widget.setVisible(wm_type == WatermarkType.IMAGE.value)
        self._common_wm_widget.setVisible(wm_type != WatermarkType.NONE.value)

    @Slot(bool)
    def _on_outline_toggle(self, enabled: bool) -> None:
        """
        Handle watermark outline checkbox toggle.

        Args:
            enabled: Whether outline is enabled
        """
        self._outline_settings.setVisible(enabled)

    @Slot()
    def _on_browse_watermark(self) -> None:
        """Handle browse watermark image button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Watermark Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )

        if file_path:
            self._wm_image_edit.setText(file_path)

    @Slot(int)
    def _on_wm_position_changed(self, index: int = -1) -> None:
        """
        Handle watermark position change.

        Args:
            index: Selected position combo index (unused)
        """
        position = self._wm_position_combo.currentData()

        # Show/hide custom position settings
        self._custom_pos_widget.setVisible(position == WatermarkPosition.CUSTOM.value)