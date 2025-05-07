from __future__ import annotations

"""
Widget implementations for the InitialDB settings dialog.

This module provides specialized widgets for different types of settings,
with appropriate editors and validators.
"""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast

import structlog
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIntValidator, QDoubleValidator
from PyQt6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QFileDialog, QFontDialog,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget,
    QScrollArea, QDoubleSpinBox, QListWidget, QListWidgetItem
)

from .models import Setting, SettingType

logger = structlog.get_logger(__name__)


class SettingWidget(QWidget):
    """Base class for all setting widgets."""

    value_changed = pyqtSignal(str, object)

    def __init__(self, setting: Setting, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the setting widget.

        Args:
            setting: The setting this widget represents
            parent: The parent widget
        """
        super().__init__(parent)
        self.setting = setting
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with name and description
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 4)

        name_label = QLabel(setting.name)
        name_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(name_label)

        if setting.description:
            desc_label = QLabel(setting.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666;")
            header_layout.addWidget(desc_label)

        layout.addWidget(header)

        # Editor widget
        editor_widget = self._create_editor_widget()
        layout.addWidget(editor_widget)

        # Validation message area
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: #e74c3c;")
        self.validation_label.setVisible(False)
        layout.addWidget(self.validation_label)

        # Restart required indicator
        if setting.restart_required:
            restart_label = QLabel("(Requires restart)")
            restart_label.setStyleSheet("color: #e67e22; font-style: italic;")
            layout.addWidget(restart_label)

        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)

    def _create_editor_widget(self) -> QWidget:
        """
        Create the editor widget for this setting.

        This must be implemented by subclasses.

        Returns:
            The editor widget
        """
        raise NotImplementedError("Subclasses must implement _create_editor_widget")

    def get_value(self) -> Any:
        """
        Get the current value from the editor.

        This must be implemented by subclasses.

        Returns:
            The current value
        """
        raise NotImplementedError("Subclasses must implement get_value")

    def set_value(self, value: Any) -> None:
        """
        Set the value in the editor.

        This must be implemented by subclasses.

        Args:
            value: The value to set
        """
        raise NotImplementedError("Subclasses must implement set_value")

    def validate(self) -> tuple[bool, str]:
        """
        Validate the current value.

        Returns:
            Tuple of (is_valid, error_message)
        """
        value = self.get_value()
        valid, message = self.setting.validate(value)
        self.validation_label.setText(message)
        self.validation_label.setVisible(bool(message))
        return valid, message

    def _value_changed(self) -> None:
        """Handle value changed event."""
        self.value_changed.emit(self.setting.key, self.get_value())
        self.validate()


class StringSettingWidget(SettingWidget):
    """Widget for editing string settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a line edit for string settings."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.edit = QLineEdit()
        self.edit.setText(str(self.setting.current_value))
        self.edit.textChanged.connect(self._value_changed)
        layout.addWidget(self.edit)

        return container

    def get_value(self) -> str:
        """Get the current text value."""
        return self.edit.text()

    def set_value(self, value: str) -> None:
        """Set the text in the editor."""
        self.edit.setText(str(value))


class PasswordSettingWidget(StringSettingWidget):
    """Widget for editing password settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a password line edit."""
        widget = super()._create_editor_widget()
        self.edit.setEchoMode(QLineEdit.EchoMode.Password)

        # Add toggle visibility button
        container = cast(QWidget, widget)
        layout = cast(QHBoxLayout, container.layout())

        self.toggle_btn = QPushButton("Show")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self._toggle_visibility)

        layout.addWidget(self.toggle_btn)

        return container

    def _toggle_visibility(self, checked: bool) -> None:
        """Toggle password visibility."""
        if checked:
            self.edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("Hide")
        else:
            self.edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("Show")


class IntSettingWidget(SettingWidget):
    """Widget for editing integer settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a spin box for integer settings."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.spin_box = QSpinBox()
        self.spin_box.setRange(-2147483647, 2147483647)  # Qt's integer range
        self.spin_box.setValue(int(self.setting.current_value))
        self.spin_box.valueChanged.connect(self._value_changed)
        layout.addWidget(self.spin_box)

        return container

    def get_value(self) -> int:
        """Get the current integer value."""
        return self.spin_box.value()

    def set_value(self, value: int) -> None:
        """Set the value in the spin box."""
        self.spin_box.setValue(int(value))


class FloatSettingWidget(SettingWidget):
    """Widget for editing float settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a double spin box for float settings."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.spin_box = QDoubleSpinBox()
        self.spin_box.setDecimals(4)
        self.spin_box.setRange(-999999999, 999999999)
        self.spin_box.setValue(float(self.setting.current_value))
        self.spin_box.valueChanged.connect(self._value_changed)
        layout.addWidget(self.spin_box)

        return container

    def get_value(self) -> float:
        """Get the current float value."""
        return self.spin_box.value()

    def set_value(self, value: float) -> None:
        """Set the value in the double spin box."""
        self.spin_box.setValue(float(value))


class BoolSettingWidget(SettingWidget):
    """Widget for editing boolean settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a checkbox for boolean settings."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox("Enabled")
        self.checkbox.setChecked(bool(self.setting.current_value))
        self.checkbox.toggled.connect(self._value_changed)
        layout.addWidget(self.checkbox)

        return container

    def get_value(self) -> bool:
        """Get the current checkbox state."""
        return self.checkbox.isChecked()

    def set_value(self, value: bool) -> None:
        """Set the checkbox state."""
        self.checkbox.setChecked(bool(value))


class ColorSettingWidget(SettingWidget):
    """Widget for editing color settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a color picker for color settings."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.color_value = QColor(self.setting.current_value)

        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setFrameShape(QFrame.Shape.Box)
        self.color_preview.setStyleSheet(f"background-color: {self.color_value.name()};")
        layout.addWidget(self.color_preview)

        self.color_label = QLabel(self.color_value.name())
        layout.addWidget(self.color_label)

        self.select_btn = QPushButton("Select Color")
        self.select_btn.clicked.connect(self._select_color)
        layout.addWidget(self.select_btn)

        layout.addStretch()

        return container

    def _select_color(self) -> None:
        """Open the color dialog."""
        color = QColorDialog.getColor(self.color_value, self, "Select Color")
        if color.isValid():
            self.color_value = color
            self.color_preview.setStyleSheet(f"background-color: {color.name()};")
            self.color_label.setText(color.name())
            self._value_changed()

    def get_value(self) -> str:
        """Get the current color as a string."""
        return self.color_value.name()

    def set_value(self, value: str) -> None:
        """Set the color value."""
        self.color_value = QColor(value)
        self.color_preview.setStyleSheet(f"background-color: {self.color_value.name()};")
        self.color_label.setText(self.color_value.name())


class FontSettingWidget(SettingWidget):
    """Widget for editing font settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a font picker for font settings."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.font_value = QFont()
        self.font_value.fromString(str(self.setting.current_value))

        self.font_label = QLabel(f"{self.font_value.family()}, {self.font_value.pointSize()}pt")
        layout.addWidget(self.font_label)

        self.select_btn = QPushButton("Select Font")
        self.select_btn.clicked.connect(self._select_font)
        layout.addWidget(self.select_btn)

        layout.addStretch()

        return container

    def _select_font(self) -> None:
        """Open the font dialog."""
        font, ok = QFontDialog.getFont(self.font_value, self, "Select Font")
        if ok:
            self.font_value = font
            self.font_label.setText(f"{font.family()}, {font.pointSize()}pt")
            self._value_changed()

    def get_value(self) -> str:
        """Get the current font as a string."""
        return self.font_value.toString()

    def set_value(self, value: str) -> None:
        """Set the font value."""
        self.font_value = QFont()
        self.font_value.fromString(str(value))
        self.font_label.setText(f"{self.font_value.family()}, {self.font_value.pointSize()}pt")


class PathSettingWidget(SettingWidget):
    """Widget for editing file or directory path settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a path picker for path settings."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.path_edit = QLineEdit()
        self.path_edit.setText(str(self.setting.current_value))
        self.path_edit.textChanged.connect(self._value_changed)
        layout.addWidget(self.path_edit)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_path)
        layout.addWidget(self.browse_btn)

        return container

    def _browse_path(self) -> None:
        """Open file or directory browser dialog."""
        current_path = self.path_edit.text()

        # Choose appropriate dialog based on if path exists and is file or directory
        if os.path.isfile(current_path):
            path, _ = QFileDialog.getOpenFileName(self, "Select File", current_path)
        elif os.path.isdir(current_path):
            path = QFileDialog.getExistingDirectory(self, "Select Directory", current_path)
        else:
            # Default to directory selection if path doesn't exist
            path = QFileDialog.getExistingDirectory(self, "Select Directory", os.path.dirname(current_path))

        if path:
            self.path_edit.setText(path)

    def get_value(self) -> str:
        """Get the current path."""
        return self.path_edit.text()

    def set_value(self, value: str) -> None:
        """Set the path value."""
        self.path_edit.setText(str(value))


class ChoiceSettingWidget(SettingWidget):
    """Widget for editing choices settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a combobox for choices settings."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.combo = QComboBox()

        # Add all available choices to the combobox
        for value, label in self.setting.choices:
            self.combo.addItem(label, value)

        # Set the current value
        current_val = self.setting.current_value
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == current_val:
                self.combo.setCurrentIndex(i)
                break

        self.combo.currentIndexChanged.connect(self._value_changed)
        layout.addWidget(self.combo)

        return container

    def get_value(self) -> Any:
        """Get the current selected value."""
        return self.combo.currentData()

    def set_value(self, value: Any) -> None:
        """Set the selected value."""
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == value:
                self.combo.setCurrentIndex(i)
                break


class MultiSelectSettingWidget(SettingWidget):
    """Widget for editing multi-select settings."""

    def _create_editor_widget(self) -> QWidget:
        """Create a list widget for multi-select settings."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(150)

        # Add all available choices to the list widget
        current_values = self.setting.current_value if isinstance(self.setting.current_value, list) else []

        for value, label in self.setting.choices:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, value)
            item.setCheckState(
                Qt.CheckState.Checked if value in current_values else Qt.CheckState.Unchecked
            )
            self.list_widget.addItem(item)

        self.list_widget.itemChanged.connect(self._value_changed)
        layout.addWidget(self.list_widget)

        return container

    def get_value(self) -> list[Any]:
        """Get the current selected values."""
        selected_values = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_values.append(item.data(Qt.ItemDataRole.UserRole))
        return selected_values

    def set_value(self, values: list[Any]) -> None:
        """Set the selected values."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            value = item.data(Qt.ItemDataRole.UserRole)
            item.setCheckState(
                Qt.CheckState.Checked if value in values else Qt.CheckState.Unchecked
            )


class SettingWidgetFactory:
    """Factory for creating setting widgets based on setting type."""

    _widget_map: Dict[SettingType, Type[SettingWidget]] = {
        SettingType.STRING: StringSettingWidget,
        SettingType.INT: IntSettingWidget,
        SettingType.FLOAT: FloatSettingWidget,
        SettingType.BOOL: BoolSettingWidget,
        SettingType.COLOR: ColorSettingWidget,
        SettingType.FONT: FontSettingWidget,
        SettingType.PATH: PathSettingWidget,
        SettingType.CHOICE: ChoiceSettingWidget,
        SettingType.MULTISELECT: MultiSelectSettingWidget,
        SettingType.PASSWORD: PasswordSettingWidget,
    }

    @classmethod
    def create_widget(cls, setting: Setting, parent: Optional[QWidget] = None) -> SettingWidget:
        """
        Create a widget for editing the given setting.

        Args:
            setting: The setting to create a widget for
            parent: The parent widget

        Returns:
            A widget for editing the setting
        """
        widget_class = cls._widget_map.get(setting.setting_type)
        if not widget_class:
            logger.warning(f"No widget available for setting type {setting.setting_type}, using string widget")
            widget_class = StringSettingWidget

        return widget_class(setting, parent)


class CategorySettingsWidget(QScrollArea):
    """Widget for displaying all settings in a category."""

    value_changed = pyqtSignal(str, object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the category settings widget.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.content_widget = QWidget()
        self.setWidget(self.content_widget)

        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(16)

        self.setting_widgets: Dict[str, SettingWidget] = {}

    def set_settings(self, settings: List[Setting]) -> None:
        """
        Set the settings to display.

        Args:
            settings: The list of settings to display
        """
        # Clear existing widgets
        self.clear()

        # Create widgets for each setting
        for setting in settings:
            if not setting.visible:
                continue

            widget = SettingWidgetFactory.create_widget(setting, self.content_widget)
            widget.value_changed.connect(self._on_value_changed)
            self.layout.addWidget(widget)
            self.setting_widgets[setting.key] = widget

        # Add stretch at the end so widgets are aligned to the top
        self.layout.addStretch()

    def clear(self) -> None:
        """Clear all settings widgets."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.setting_widgets.clear()

    def _on_value_changed(self, key: str, value: Any) -> None:
        """Forward the value changed signal."""
        self.value_changed.emit(key, value)

    def get_values(self) -> Dict[str, Any]:
        """
        Get all current setting values.

        Returns:
            Dictionary mapping setting keys to their current values
        """
        values = {}
        for key, widget in self.setting_widgets.items():
            values[key] = widget.get_value()
        return values

    def set_values(self, values: Dict[str, Any]) -> None:
        """
        Set values for multiple settings.

        Args:
            values: Dictionary mapping setting keys to values
        """
        for key, value in values.items():
            if key in self.setting_widgets:
                self.setting_widgets[key].set_value(value)

    def validate_all(self) -> bool:
        """
        Validate all settings.

        Returns:
            True if all settings are valid, False otherwise
        """
        valid = True
        for widget in self.setting_widgets.values():
            is_valid, _ = widget.validate()
            valid = valid and is_valid
        return valid