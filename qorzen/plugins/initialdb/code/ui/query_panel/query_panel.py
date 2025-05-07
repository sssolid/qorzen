from __future__ import annotations

from initialdb.services.vehicle_service import VehicleService
from initialdb.utils.dependency_container import resolve
from initialdb.utils.schema_registry import SchemaRegistry

"""
Async multi-query panel component for the InitialDB application.

This module provides a panel that can contain multiple query sections,
allowing users to create and combine independent queries, using
the vehicle_service singleton directly.
"""
import uuid
from typing import Dict, Optional
import structlog
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton,
    QLabel, QScrollArea, QMessageBox
)
from PyQt6.QtGui import QIcon
from qasync import asyncSlot

from initialdb.models.schema import FilterDTO
from initialdb.adapters.vehicle_service_adapter import VehicleServiceAdapter
from initialdb.ui.query_panel.query_section import QuerySection

logger = structlog.get_logger(__name__)


class MultiQueryPanel(QWidget):
    """
    Panel for managing multiple query sections.

    This panel allows users to create and combine multiple independent queries.
    """
    executeQueryRequested = pyqtSignal(object)
    filterChanged = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the multi-query panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._registry = resolve(SchemaRegistry)
        self._vehicle_service = resolve(VehicleService)

        self.service_adapter = VehicleServiceAdapter()
        self.query_sections: Dict[str, QuerySection] = {}
        self.filter_dtos: Dict[str, FilterDTO] = {}

        self._init_ui()
        self.add_query_section()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Header with title and add button
        header_layout = QHBoxLayout()
        title_label = QLabel('Query Builder')
        title_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        add_query_button = QPushButton('Add Query')
        add_query_button.setIcon(QIcon.fromTheme('list-add'))
        add_query_button.clicked.connect(self.add_query_section)
        header_layout.addWidget(add_query_button)

        main_layout.addLayout(header_layout)

        # Scrollable area for query sections
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_widget = QWidget()
        self.sections_layout = QVBoxLayout(self.scroll_widget)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(10)
        self.sections_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll_area)

        # Bottom buttons
        buttons_layout = QHBoxLayout()

        reset_all_button = QPushButton('Reset All Filters')
        reset_all_button.clicked.connect(self._reset_all_filters)
        buttons_layout.addWidget(reset_all_button)

        buttons_layout.addStretch()

        execute_all_button = QPushButton('Execute All Queries')
        execute_all_button.setIcon(QIcon.fromTheme('system-search'))
        execute_all_button.clicked.connect(self._execute_all_queries)
        execute_all_button.setDefault(True)
        buttons_layout.addWidget(execute_all_button)

        main_layout.addLayout(buttons_layout)

    def add_query_section(self) -> str:
        """
        Add a new query section.

        Returns:
            The ID of the new section
        """
        section_id = str(uuid.uuid4())
        section_num = len(self.query_sections) + 1

        query_section = QuerySection(
            section_id=section_id,
            service_adapter=self.service_adapter,
            title=f'Query {section_num}',
            parent=self.scroll_widget
        )

        query_section.executeQueryRequested.connect(lambda sid: self._execute_single_query(sid))
        query_section.removeRequested.connect(self._remove_query_section)
        query_section.filterChanged.connect(self._on_filter_changed)

        self.sections_layout.insertWidget(self.sections_layout.count() - 1, query_section)
        self.query_sections[section_id] = query_section
        self.filter_dtos[section_id] = FilterDTO()

        self._update_section_titles()
        query_section.filter_panel._reset_filters()

        logger.debug(f'Added query section {section_id}')
        return section_id

    def _update_section_titles(self) -> None:
        """Update titles of all query sections to reflect their order."""
        sections = [section for section in self.query_sections.values()]
        for i, section in enumerate(sections, 1):
            section.set_title(f'Query {i}')

    def _remove_query_section(self, section_id: str) -> None:
        """
        Remove a query section.

        Args:
            section_id: ID of the section to remove
        """
        if len(self.query_sections) <= 1:
            QMessageBox.information(
                self, 'Cannot Remove',
                'At least one query section must be present.'
            )
            return

        if section_id in self.query_sections:
            section = self.query_sections.pop(section_id)
            self.filter_dtos.pop(section_id, None)

            self.sections_layout.removeWidget(section)
            section.deleteLater()

            self._update_section_titles()
            self.filterChanged.emit(self.filter_dtos)

            logger.debug(f'Removed query section {section_id}')

    def _on_filter_changed(self, section_id: str, filter_dto: FilterDTO) -> None:
        """
        Handle filter changes in a query section.

        Args:
            section_id: ID of the section with changed filters
            filter_dto: The new filter state
        """
        self.filter_dtos[section_id] = filter_dto
        self.filterChanged.emit(self.filter_dtos)

    @asyncSlot()
    async def _execute_single_query(self, section_id: str) -> None:
        """
        Execute a single query section.

        Args:
            section_id: ID of the section to execute
        """
        if section_id in self.filter_dtos:
            try:
                from ...config.settings import settings

                # Get default display fields if needed
                display_fields = self._registry.get_default_display_fields()
                if any(field[1] == 'vehicle_id' for field in display_fields):
                    display_fields.append(('vehicle', 'vehicle_id', 'Vehicle ID'))

                limit = settings.get('query_limit', 1000)

                # Execute the query using the vehicle_service
                results = await self._vehicle_service.get_vehicles(
                    filters=self.filter_dtos[section_id],
                    display_fields=display_fields
                )

                # Emit the results
                self.executeQueryRequested.emit({section_id: results})
            except Exception as e:
                logger.error(f"Error executing query for section {section_id}: {str(e)}")
                QMessageBox.critical(
                    self, "Query Error",
                    f"Error executing query: {str(e)}"
                )

    @asyncSlot()
    async def _execute_all_queries(self) -> None:
        """Execute all query sections and combine results."""
        if not self.filter_dtos:
            QMessageBox.information(
                self, 'No Queries',
                'No query sections available to execute.'
            )
            return

        # Check if there are any active filters
        has_active_filters = False
        for filter_dto in self.filter_dtos.values():
            if (bool(filter_dto.year_ids) or
                    bool(filter_dto.make_ids) or
                    bool(filter_dto.model_ids) or
                    bool(filter_dto.sub_model_ids) or
                    (filter_dto.use_year_range and filter_dto.year_range_start is not None)):
                has_active_filters = True
                break

        if not has_active_filters:
            result = QMessageBox.question(
                self, 'Execute Query',
                'No filters are active. This may return a large number of results. Continue?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.No:
                return

        try:
            # Get display fields
            from ...config.settings import settings
            display_fields = self._registry.get_default_display_fields()

            # Make sure vehicle_id is included
            if not any(field[1] == 'vehicle_id' for field in display_fields):
                display_fields.append(('vehicle', 'vehicle_id', 'Vehicle ID'))

            limit = settings.get('query_limit', 1000)

            # Execute the query using the vehicle_service
            results = await self._vehicle_service.get_vehicles_from_multiple_filters(
                filter_sets=self.filter_dtos,
                display_fields=display_fields
            )

            # Emit the results
            self.executeQueryRequested.emit(results)
        except Exception as e:
            logger.error(f"Error executing combined queries: {str(e)}")
            QMessageBox.critical(
                self, "Query Error",
                f"Error executing queries: {str(e)}"
            )

    def _reset_all_filters(self) -> None:
        """Reset filters in all query sections."""
        for section in self.query_sections.values():
            section.filter_panel._reset_filters()

    def get_all_filter_dtos(self) -> Dict[str, FilterDTO]:
        """
        Get filter DTOs from all sections.

        Returns:
            Dictionary mapping section IDs to filter DTOs
        """
        return self.filter_dtos

    def clear_all_filters(self) -> None:
        """Clear all filters in all sections."""
        for section in self.query_sections.values():
            section.filter_panel._reset_filters()