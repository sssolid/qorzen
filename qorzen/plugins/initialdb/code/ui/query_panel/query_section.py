from __future__ import annotations

"""
Query section component for the InitialDB application.

This module provides an individual query section with its own filter panel,
allowing users to create multiple independent queries that can be combined.
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple, cast

import structlog
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QIcon, QFont

from ...adapters.vehicle_service_adapter import VehicleServiceAdapter
from ...models.schema import FilterDTO
from ...utils.async_manager import async_slot
from .filter_panel import FilterPanel

logger = structlog.get_logger(__name__)


class QuerySection(QFrame):
    """
    An individual query section with its own filter panel.

    This class represents a collapsible query section that contains a filter panel
    and allows users to create and execute queries independently.
    """

    executeQueryRequested = pyqtSignal(str)
    removeRequested = pyqtSignal(str)
    filterChanged = pyqtSignal(str, FilterDTO)

    def __init__(
            self,
            section_id: str,
            service_adapter: VehicleServiceAdapter,
            title: str = "Query",
            parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize a query section.

        Args:
            section_id: Unique identifier for this section
            service_adapter: The vehicle service adapter
            title: The title of the section
            parent: The parent widget
        """
        super().__init__(parent)

        self.section_id = section_id
        self.service_adapter = service_adapter
        self.title = title
        self.is_expanded = True

        self._connect_signals()
        self._init_ui()

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        try:
            # Connect service adapter signals
            try:
                self.service_adapter.signals.operationCompleted.disconnect(self._on_operation_completed)
            except (TypeError, RuntimeError):
                pass

            try:
                self.service_adapter.signals.operationFailed.disconnect(self._on_operation_failed)
            except (TypeError, RuntimeError):
                pass

            self.service_adapter.signals.operationCompleted.connect(self._on_operation_completed)
            self.service_adapter.signals.operationFailed.connect(self._on_operation_failed)

        except Exception as e:
            logger.error(f"Error connecting signals in QuerySection: {e}")

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set up the frame appearance
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setStyleSheet(
            """
            QFrame {
                border: 2px solid #4b7dbd;    /* blue border */
                border-radius: 6px;           /* rounded corners */
            }
        """
        )

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create header frame
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        header_frame.setStyleSheet("background-color: #3b913f;")
        header_layout = QHBoxLayout(header_frame)

        # Toggle button for collapsing
        self.toggle_button = QToolButton()
        self.toggle_button.setText("▼")
        self.toggle_button.setToolTip("Collapse")
        self.toggle_button.clicked.connect(self._toggle_expansion)
        header_layout.addWidget(self.toggle_button)

        # Title label
        title_font = QFont()
        title_font.setBold(True)
        self.title_label = QLabel(self.title)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Remove button
        remove_button = QToolButton()
        remove_button.setText("✕")
        remove_button.setToolTip("Remove this query")
        remove_button.clicked.connect(self._request_removal)
        header_layout.addWidget(remove_button)

        main_layout.addWidget(header_frame)

        # Create content container
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Create filter panel
        self.filter_panel = FilterPanel(parent=self)
        self.filter_panel.executeQueryRequested.connect(self._on_execute_requested)
        self.filter_panel.filterChanged.connect(self._on_filter_changed)

        self.content_layout.addWidget(self.filter_panel)
        main_layout.addWidget(self.content_container)

    def _toggle_expansion(self) -> None:
        """Toggle the expansion state of the section."""
        self.is_expanded = not self.is_expanded
        self.content_container.setVisible(self.is_expanded)

        if self.is_expanded:
            self.toggle_button.setText("▼")
            self.toggle_button.setToolTip("Collapse")
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        else:
            self.toggle_button.setText("▶")
            self.toggle_button.setToolTip("Expand")
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.adjustSize()
        if self.parent():
            self.parent().adjustSize()

    def _request_removal(self) -> None:
        """Request removal of this section."""
        self.removeRequested.emit(self.section_id)

    @pyqtSlot()
    def _on_execute_requested(self) -> None:
        """Handle execute query request from the filter panel."""
        self.executeQueryRequested.emit(self.section_id)

    @pyqtSlot(FilterDTO)
    def _on_filter_changed(self, filter_dto: FilterDTO) -> None:
        """
        Handle filter changes from the filter panel.

        Args:
            filter_dto: The updated filter DTO
        """
        self.filterChanged.emit(self.section_id, filter_dto)

    @pyqtSlot(object)
    def _on_operation_completed(self, operation: Any) -> None:
        """
        Handle completed operations.

        Args:
            operation: The completed operation
        """
        try:
            logger.debug(f"Operation completed: {operation.operation_id}")
        except Exception as e:
            logger.error(f"Error in operation completed handler: {e}")

    @pyqtSlot(object, Exception)
    def _on_operation_failed(self, operation: Any, error: Exception) -> None:
        """
        Handle failed operations.

        Args:
            operation: The failed operation
            error: The error that occurred
        """
        try:
            logger.error(f"Operation failed: {operation.operation_id}, Error: {str(error)}")
        except Exception as e:
            logger.error(f"Error in operation failed handler: {e}")

    def get_filter_dto(self) -> FilterDTO:
        """
        Get the current filter DTO.

        Returns:
            The filter DTO
        """
        return self.filter_panel.get_filter_dto()

    def set_filter_dto(self, filter_dto: FilterDTO) -> None:
        """
        Set the filter DTO.

        Args:
            filter_dto: The filter DTO to set
        """
        self.filter_panel.set_filter_dto(filter_dto)
        self.filterChanged.emit(self.section_id, filter_dto)

    def set_title(self, title: str) -> None:
        """
        Set the title of the section.

        Args:
            title: The new title
        """
        self.title = title
        self.title_label.setText(title)