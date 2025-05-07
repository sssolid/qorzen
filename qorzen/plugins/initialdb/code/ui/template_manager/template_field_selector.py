from __future__ import annotations

from initialdb.utils.dependency_container import resolve
from initialdb.utils.schema_registry import SchemaRegistry

"""
Template field selector widget for the InitialDB application.

This module provides a widget for selecting model and attribute fields
when creating template mappings in the template manager.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, cast
import structlog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QComboBox,
    QLabel, QPushButton, QDialog, QDialogButtonBox
)

logger = structlog.get_logger(__name__)


class FieldSelectorDialog(QDialog):
    """Dialog for selecting a model and attribute field."""

    def __init__(
            self,
            parent: Optional[QWidget] = None,
            initial_model: str = "",
            initial_attribute: str = ""
    ) -> None:
        """
        Initialize the field selector dialog.

        Args:
            parent: The parent widget
            initial_model: Initial model value
            initial_attribute: Initial attribute value
        """
        super().__init__(parent)

        self._registry = resolve(SchemaRegistry)

        self.setWindowTitle("Select Field Mapping")
        self.setMinimumWidth(400)

        self.model_value = initial_model
        self.attribute_value = initial_attribute

        self.selector = TemplateFieldSelector(
            self,
            initial_model=initial_model,
            initial_attribute=initial_attribute
        )
        self.selector.valueChanged.connect(self._on_values_changed)

        layout = QVBoxLayout(self)
        layout.addWidget(self.selector)

        # Create explicit buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Style the dialog to clearly show modal state
        self.setModal(True)

    def _on_values_changed(self, model: str, attribute: str) -> None:
        """
        Store the selected values.

        Args:
            model: The selected model
            attribute: The selected attribute
        """
        self.model_value = model
        self.attribute_value = attribute

    def get_values(self) -> Tuple[str, str]:
        """
        Get the selected values.

        Returns:
            A tuple containing the model and attribute values
        """
        return self.model_value, self.attribute_value


class TemplateFieldSelector(QWidget):
    """Widget for selecting model and attribute fields in template mappings."""

    valueChanged = pyqtSignal(str, str)

    def __init__(
            self, parent: Optional[QWidget] = None,
            initial_model: str = "",
            initial_attribute: str = ""
    ) -> None:
        """
        Initialize the template field selector widget.

        Args:
            parent: The parent widget
            initial_model: Initial model value
            initial_attribute: Initial attribute value
        """
        super().__init__(parent)

        self._registry = resolve(SchemaRegistry)

        self.available_fields = self._registry.get_available_display_fields()
        self.model_map: Dict[str, List[Tuple[str, str]]] = {}
        self._populate_model_map()
        self._init_ui()
        self.set_values(initial_model, initial_attribute)

    def _populate_model_map(self) -> None:
        """Populate the model to attributes map from available fields."""
        for table, column, display in self.available_fields:
            if table not in self.model_map:
                self.model_map[table] = []
            self.model_map[table].append((column, display))

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Model dropdown
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItem("")
        models = sorted(self.model_map.keys())
        for model in models:
            self.model_combo.addItem(model)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(QLabel("Model:"))
        layout.addWidget(self.model_combo)

        # Attribute dropdown
        self.attribute_combo = QComboBox()
        self.attribute_combo.setEditable(True)
        self.attribute_combo.addItem("")
        self.attribute_combo.currentTextChanged.connect(self._on_attribute_changed)
        layout.addWidget(QLabel("Attribute:"))
        layout.addWidget(self.attribute_combo)

    def _on_model_changed(self, model: str) -> None:
        """
        Handle model selection changes.

        Args:
            model: The selected model name
        """
        self.attribute_combo.clear()
        self.attribute_combo.addItem("")

        if model in self.model_map:
            attributes = self.model_map[model]
            for column, display in sorted(attributes, key=lambda x: x[1]):
                self.attribute_combo.addItem(display, userData=column)

        self.valueChanged.emit(model, self.attribute_combo.currentText())

    def _on_attribute_changed(self, attribute: str) -> None:
        """
        Handle attribute selection changes.

        Args:
            attribute: The selected attribute display name
        """
        model = self.model_combo.currentText()
        self.valueChanged.emit(model, attribute)

    def get_values(self) -> Tuple[str, str]:
        """
        Get the currently selected model and attribute values.

        Returns:
            A tuple containing the model and attribute values
        """
        model = self.model_combo.currentText()
        attribute = self.attribute_combo.currentText()
        return model, attribute

    def set_values(self, model: str, attribute: str) -> None:
        """
        Set the model and attribute values.

        Args:
            model: The model value to set
            attribute: The attribute value to set
        """
        # Block signals to prevent triggering change events during setup
        self.model_combo.blockSignals(True)
        self.attribute_combo.blockSignals(True)

        # Set model
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        else:
            self.model_combo.setCurrentText(model)

        # Update attribute combo with available attributes for the selected model
        self.attribute_combo.clear()
        self.attribute_combo.addItem("")
        if model in self.model_map:
            for column, display in sorted(self.model_map[model], key=lambda x: x[1]):
                self.attribute_combo.addItem(display, userData=column)

        # Set attribute
        index = self.attribute_combo.findText(attribute)
        if index >= 0:
            self.attribute_combo.setCurrentIndex(index)
        else:
            self.attribute_combo.setCurrentText(attribute)

        # Unblock signals
        self.model_combo.blockSignals(False)
        self.attribute_combo.blockSignals(False)