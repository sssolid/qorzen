from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, cast
from qasync import asyncSlot

from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel, QMenu,
    QPushButton, QSizePolicy, QSpinBox, QTabWidget, QToolButton, QVBoxLayout, QWidget
)

from qorzen.core.event_bus_manager import EventBusManager
from .database_handler import DatabaseHandler
from .events import VCdbEventType


class FilterWidget(QWidget):
    """Base widget for handling filter selections."""

    valueChanged = Signal(str, list)

    def __init__(
            self,
            filter_type: str,
            filter_name: str,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize filter widget.

        Args:
            filter_type: Type of filter
            filter_name: Display name for filter
            parent: Parent widget
        """
        super().__init__(parent)
        self._filter_type = filter_type
        self._filter_name = filter_name

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._label = QLabel(filter_name)
        self._label.setMinimumWidth(100)
        self._layout.addWidget(self._label)

        self._clear_btn = QToolButton()
        self._clear_btn.setText('×')
        self._clear_btn.setToolTip(f'Clear {filter_name} filter')
        self._clear_btn.clicked.connect(self.clear)
        self._layout.addWidget(self._clear_btn)

    def get_filter_type(self) -> str:
        """Get the type of filter.

        Returns:
            Filter type identifier
        """
        return self._filter_type

    def get_filter_name(self) -> str:
        """Get the display name of filter.

        Returns:
            Filter display name
        """
        return self._filter_name

    def get_selected_values(self) -> List[int]:
        """Get selected filter values.

        Returns:
            List of selected values
        """
        return []

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """Set available filter values.

        Args:
            values: List of available values
        """
        pass

    @Slot()
    def clear(self) -> None:
        """Clear selected filter values."""
        pass


class ComboBoxFilter(FilterWidget):
    """Filter widget with combo box selection."""

    def __init__(
            self,
            filter_type: str,
            filter_name: str,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize combo box filter.

        Args:
            filter_type: Type of filter
            filter_name: Display name for filter
            parent: Parent widget
        """
        super().__init__(filter_type, filter_name, parent)

        self._combo = QComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._combo.setMinimumWidth(150)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)

        # Disable mouse wheel to prevent accidental changes
        self._combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._combo.wheelEvent = lambda event: event.ignore()

        self._layout.insertWidget(1, self._combo)

    def get_selected_values(self) -> List[int]:
        """Get selected filter values.

        Returns:
            List of selected values
        """
        if self._combo.currentIndex() <= 0:
            return []

        value_id = self._combo.currentData(Qt.ItemDataRole.UserRole)
        if value_id is not None:
            return [int(value_id)]

        return []

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """Set available filter values.

        Args:
            values: List of available values with id, name, and count
        """
        current_id = None
        if self._combo.currentIndex() > 0:
            current_id = self._combo.currentData(Qt.ItemDataRole.UserRole)

        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem('Any', None)

        for value in values:
            self._combo.addItem(f"{value['name']} ({value['count']})", value['id'])

        if current_id is not None:
            index = self._combo.findData(current_id)
            if index > 0:
                self._combo.setCurrentIndex(index)
            else:
                self._combo.setCurrentIndex(0)
        else:
            self._combo.setCurrentIndex(0)

        self._combo.blockSignals(False)

    @Slot(int)
    def _on_selection_changed(self, index: int) -> None:
        """Handle selection change in combo box.

        Args:
            index: Selected index
        """
        selected_values = self.get_selected_values()
        self.valueChanged.emit(self._filter_type, selected_values)

    @Slot()
    def clear(self) -> None:
        """Clear selected filter values."""
        self._combo.setCurrentIndex(0)


class YearRangeFilter(FilterWidget):
    """Filter widget for year range selection."""

    def __init__(
            self,
            filter_type: str,
            filter_name: str,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize year range filter.

        Args:
            filter_type: Type of filter
            filter_name: Display name for filter
            parent: Parent widget
        """
        super().__init__(filter_type, filter_name, parent)

        self._start_label = QLabel('From:')
        self._start_year = QSpinBox()
        self._start_year.setRange(1900, 2100)
        self._start_year.setValue(1900)
        self._start_year.valueChanged.connect(self._on_value_changed)

        # Disable mouse wheel to prevent accidental changes
        self._start_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._start_year.wheelEvent = lambda event: event.ignore()

        self._end_label = QLabel('To:')
        self._end_year = QSpinBox()
        self._end_year.setRange(1900, 2100)
        self._end_year.setValue(2100)
        self._end_year.valueChanged.connect(self._on_value_changed)

        # Disable mouse wheel to prevent accidental changes
        self._end_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._end_year.wheelEvent = lambda event: event.ignore()

        self._layout.insertWidget(1, self._start_label)
        self._layout.insertWidget(2, self._start_year)
        self._layout.insertWidget(3, self._end_label)
        self._layout.insertWidget(4, self._end_year)

    def get_selected_values(self) -> List[int]:
        """Get selected year range.

        Returns:
            List with start and end year
        """
        start_year = self._start_year.value()
        end_year = self._end_year.value()

        if start_year > end_year:
            return []

        return [start_year, end_year]

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """Set available year values.

        Args:
            values: List of available years
        """
        if not values:
            return

        years = [int(v['name']) for v in values]
        if not years:
            return

        min_year = min(years)
        max_year = max(years)

        self._start_year.blockSignals(True)
        self._end_year.blockSignals(True)

        self._start_year.setRange(min_year, max_year)
        self._end_year.setRange(min_year, max_year)

        if self._start_year.value() < min_year or self._start_year.value() > max_year:
            self._start_year.setValue(min_year)

        if self._end_year.value() < min_year or self._end_year.value() > max_year:
            self._end_year.setValue(max_year)

        self._start_year.blockSignals(False)
        self._end_year.blockSignals(False)

    @Slot(int)
    def _on_value_changed(self, value: int) -> None:
        """Handle value change in year spinboxes.

        Args:
            value: New value
        """
        selected_values = self.get_selected_values()
        self.valueChanged.emit(self._filter_type, selected_values)

    @Slot()
    def clear(self) -> None:
        """Reset year range to min/max values."""
        self._start_year.blockSignals(True)
        self._end_year.blockSignals(True)

        min_value = self._start_year.minimum()
        max_value = self._end_year.maximum()

        self._start_year.setValue(min_value)
        self._end_year.setValue(max_value)

        self._start_year.blockSignals(False)
        self._end_year.blockSignals(False)

        self.valueChanged.emit(self._filter_type, self.get_selected_values())


class FilterPanel(QGroupBox):
    """Panel containing a set of filter widgets."""

    filterChanged = Signal(str, str, list)
    removeRequested = Signal(str)

    def __init__(
            self,
            panel_id: str,
            database_handler: DatabaseHandler,
            event_bus_manager: EventBusManager,
            logger: logging.Logger,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize filter panel.

        Args:
            panel_id: Unique identifier for panel
            database_handler: Handler for database operations
            event_bus_manager: Manager for event bus operations
            logger: Logger for messages
            parent: Parent widget
        """
        super().__init__(parent)

        self._panel_id = panel_id
        self._database_handler = database_handler
        self._event_bus_manager = event_bus_manager
        self._logger = logger

        self._available_filters = database_handler.get_available_filters()
        self._filters: Dict[str, FilterWidget] = {}
        self._current_values: Dict[str, List[int]] = {}
        self._auto_populate_filters = False
        self._is_refreshing = False

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Set up header with title and buttons
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.setTitle(f'Filter Group {panel_id[-4:]}')

        self._add_filter_btn = QPushButton('Add Filter')
        self._add_filter_btn.clicked.connect(self._show_add_filter_menu)
        header_layout.addWidget(self._add_filter_btn)

        self._clear_all_btn = QPushButton('Clear All')
        self._clear_all_btn.clicked.connect(self._clear_all_filters)
        header_layout.addWidget(self._clear_all_btn)

        self._remove_btn = QPushButton('Remove Group')
        self._remove_btn.clicked.connect(self._remove_panel)
        header_layout.addWidget(self._remove_btn)

        header_layout.addStretch()
        self._layout.addLayout(header_layout)

        # Auto-populate checkbox
        auto_populate_layout = QHBoxLayout()
        self._auto_populate_checkbox = QCheckBox('Auto-populate other filters')
        self._auto_populate_checkbox.setChecked(False)
        self._auto_populate_checkbox.stateChanged.connect(self._on_auto_populate_changed)
        auto_populate_layout.addWidget(self._auto_populate_checkbox)
        auto_populate_layout.addStretch()
        self._layout.addLayout(auto_populate_layout)

        # Container for filter widgets
        self._filters_layout = QVBoxLayout()
        self._filters_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._filters_layout)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(line)

        asyncio.create_task(self.initialize())

    def closeEvent(self, event):
        self._event_bus_manager.unsubscribe(subscriber_id=f'filter_panel_{self._panel_id}', )

    async def initialize(self) -> None:
        # Add mandatory filters
        for filter_def in self._available_filters:
            if filter_def.get('mandatory', False):
                await self._add_filter(filter_def['id'], filter_def['name'])

        await self._event_bus_manager.subscribe(
            event_type=VCdbEventType.filters_refreshed(),
            subscriber_id=f'filter_panel_{self._panel_id}',
            callback=self._on_filters_refreshed
        )

    def get_panel_id(self) -> str:
        """Get panel identifier.

        Returns:
            Panel identifier
        """
        return self._panel_id

    def get_current_values(self) -> Dict[str, List[int]]:
        """Get current filter values.

        Returns:
            Dictionary of filter values
        """
        return self._current_values.copy()

    async def set_filter_values(self, filter_type: str, values: List[Dict[str, Any]]) -> None:
        """Set available values for a filter.

        Args:
            filter_type: Type of filter
            values: List of available values
        """
        if filter_type not in self._filters:
            return

        self._logger.debug(f'Setting filter values for {filter_type}: {len(values)} values')
        self._filters[filter_type].set_available_values(values)

    async def _add_filter(self, filter_type: str, filter_name: str) -> None:
        """Add a filter widget to the panel.

        Args:
            filter_type: Type of filter
            filter_name: Display name for filter
        """
        if filter_type in self._filters:
            return

        if filter_type == 'year_range':
            filter_widget = YearRangeFilter(filter_type, filter_name, self)
        else:
            filter_widget = ComboBoxFilter(filter_type, filter_name, self)

        filter_widget.valueChanged.connect(self._on_filter_value_changed)
        self._filters_layout.addWidget(filter_widget)
        self._filters[filter_type] = filter_widget

        # Refresh filter values
        await self._refresh_filter_values(filter_type)

    async def _refresh_filter_values(self, filter_type: str) -> None:
        """Refresh values for a specific filter.

        Args:
            filter_type: Type of filter to refresh
        """
        if filter_type not in self._filters or self._is_refreshing:
            return

        try:
            exclude_filters = {filter_type}
            if filter_type == 'year_range':
                exclude_filters.add('year')
            elif filter_type == 'year':
                exclude_filters.add('year_range')

            self._logger.debug(f'Refreshing filter values for {filter_type}')

            # Use the database handler to get filter values
            values = await self._database_handler.get_filter_values(
                filter_type if filter_type != 'year_range' else 'year',
                self._current_values,
                exclude_filters
            )

            self._filters[filter_type].set_available_values(values)
        except Exception as e:
            self._logger.error(f'Error refreshing filter values for {filter_type}: {str(e)}')

    def refresh_all_filters(self) -> None:
        """Refresh all filters in the panel."""
        self._logger.debug(f'Refreshing all filters, auto-populate: {self._auto_populate_filters}')
        for filter_type in self._filters:
            self._refresh_filter_values(filter_type)

    async def _on_filters_refreshed(self, event: Any) -> None:
        """Handle filter refresh events.

        Args:
            event: Event containing filter refresh information
        """
        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})

        if panel_id == self._panel_id:
            self._logger.debug(f'Received filter refresh for panel {panel_id}')
            await self.update_filter_values(filter_values)

    @Slot(str, list)
    def _on_filter_value_changed(self, filter_type: str, values: List[int]) -> None:
        """Handle filter value changes.

        Args:
            filter_type: Type of filter
            values: Selected values
        """
        self._logger.debug(f'Filter value changed: {filter_type} = {values}')

        # Update current values
        if not values:
            if filter_type in self._current_values:
                del self._current_values[filter_type]
        else:
            self._current_values[filter_type] = values

        self._logger.debug(f'Updated filter state: {self._current_values}')

        # Emit signal
        self.filterChanged.emit(self._panel_id, filter_type, values)

        # Publish event
        self._logger.debug(f'Publishing filter changed event: auto_populate={self._auto_populate_filters}')
        asyncio.create_task(
            self._event_bus_manager.publish(
                event_type=VCdbEventType.filter_changed(),
                source='vcdb_explorer_filter_panel',
                payload={
                    'panel_id': self._panel_id,
                    'filter_type': filter_type,
                    'values': values,
                    'current_filters': self._current_values.copy(),
                    'auto_populate': self._auto_populate_filters
                }
            )
        )

    @asyncSlot(int)
    async def _on_auto_populate_changed(self, state: int) -> None:
        """Handle auto-populate checkbox state change.

        Args:
            state: New checkbox state
        """
        self._logger.debug(f'Auto-populate checkbox raw state: {state}')
        is_checked = state == 2  # Qt.CheckState.Checked
        self._logger.debug(f'Auto-populate checkbox interpreted as: {is_checked}')

        if is_checked != self._auto_populate_filters:
            self._logger.debug(f'Auto-populate state changed from {self._auto_populate_filters} to {is_checked}')
            self._auto_populate_filters = is_checked

            if self._auto_populate_filters:
                self._logger.debug('Auto-populate ENABLED - triggering filter refresh')
                if self._current_values:
                    for filter_type, values in self._current_values.items():
                        self._logger.debug(f'Publishing filter changed event for {filter_type}: {values}')
                        await self._event_bus_manager.publish(
                            event_type=VCdbEventType.filter_changed(),
                            source='vcdb_explorer_filter_panel',
                            payload={
                                'panel_id': self._panel_id,
                                'filter_type': filter_type,
                                'values': values,
                                'current_filters': self._current_values.copy(),
                                'auto_populate': True
                            }
                        )
                else:
                    self._logger.debug('No current filter values, sending empty refresh')
                    await self._event_bus_manager.publish(
                        event_type=VCdbEventType.filter_changed(),
                        source='vcdb_explorer_filter_panel',
                        payload={
                            'panel_id': self._panel_id,
                            'filter_type': 'none',
                            'values': [],
                            'current_filters': {},
                            'auto_populate': True
                        }
                    )
            else:
                self._logger.debug('Auto-populate DISABLED')

    @Slot()
    def _show_add_filter_menu(self) -> None:
        """Show menu to add a new filter."""
        menu = QMenu(self)

        for filter_def in self._available_filters:
            filter_id = filter_def['id']
            if filter_id in self._filters:
                continue

            action = menu.addAction(filter_def['name'])
            action.setData(filter_id)

        if not menu.isEmpty():
            menu.triggered.connect(lambda action: self._add_filter(action.data(), action.text()))
            menu.popup(self._add_filter_btn.mapToGlobal(self._add_filter_btn.rect().bottomLeft()))

    @Slot()
    def _clear_all_filters(self) -> None:
        """Clear all filters in the panel."""
        for filter_widget in self._filters.values():
            filter_widget.clear()

    @Slot()
    def _remove_panel(self) -> None:
        """Request removal of this panel."""
        self.removeRequested.emit(self._panel_id)

    async def update_filter_values(self, filter_values: Dict[str, List[Dict[str, Any]]]) -> None:
        """Update filter values from filter refresh event.

        Args:
            filter_values: Dictionary of filter values
        """
        self._is_refreshing = True
        try:
            for filter_type, values in filter_values.items():
                if filter_type in self._filters:
                    await self.set_filter_values(filter_type, values)
        finally:
            self._is_refreshing = False


class FilterPanelManager(QWidget):
    """Manager for multiple filter panels."""

    filtersChanged = Signal()

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus_manager: EventBusManager,
            logger: logging.Logger,
            max_panels: int = 5,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize filter panel manager.

        Args:
            database_handler: Handler for database operations
            event_bus_manager: Manager for event bus operations
            logger: Logger for messages
            max_panels: Maximum number of filter panels
            parent: Parent widget
        """
        super().__init__(parent)

        self._database_handler = database_handler
        self._event_bus_manager = event_bus_manager
        self._logger = logger
        self._max_panels = max_panels

        self._panels: Dict[str, FilterPanel] = {}
        self._available_filters = database_handler.get_available_filters()

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Set up header
        header_layout = QHBoxLayout()

        title = QLabel('Query Filters')
        title.setStyleSheet('font-weight: bold; font-size: 14px;')
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._add_panel_btn = QPushButton('Add Filter Group')
        self._add_panel_btn.clicked.connect(self._add_panel)
        header_layout.addWidget(self._add_panel_btn)

        self._layout.addLayout(header_layout)

        # Tab widget for filter panels
        self._tab_widget = QTabWidget()
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self._layout.addWidget(self._tab_widget)

        asyncio.create_task(self._subscribe_to_events())

        # Create initial panel
        self._add_panel()

    def closeEvent(self, event):
        self._event_bus_manager.unsubscribe(subscriber_id='filter_panel_manager')

    async def _subscribe_to_events(self) -> None:
        """Subscribe to events."""
        await self._event_bus_manager.subscribe(
            event_type=VCdbEventType.filters_refreshed(),
            subscriber_id='filter_panel_manager',
            callback=self._on_filters_refreshed
        )

    def _add_panel(self) -> None:
        """Add a new filter panel."""
        if len(self._panels) >= self._max_panels:
            self._logger.warning(f'Maximum number of filter panels ({self._max_panels}) reached')
            return

        panel_id = str(uuid.uuid4())
        panel = FilterPanel(panel_id, self._database_handler, self._event_bus_manager, self._logger)
        panel.filterChanged.connect(self._on_filter_changed)
        panel.removeRequested.connect(self._remove_panel)

        tab_index = self._tab_widget.addTab(panel, f'Filter Group {len(self._panels) + 1}')
        self._tab_widget.setCurrentIndex(tab_index)

        self._panels[panel_id] = panel
        self._add_panel_btn.setEnabled(len(self._panels) < self._max_panels)

    def _remove_panel(self, panel_id: str) -> None:
        """Remove a filter panel.

        Args:
            panel_id: ID of panel to remove
        """
        if panel_id not in self._panels:
            return

        # Don't remove the last panel
        if len(self._panels) <= 1:
            return

        panel = self._panels[panel_id]

        # Remove from tab widget
        for i in range(self._tab_widget.count()):
            if self._tab_widget.widget(i) == panel:
                self._tab_widget.removeTab(i)
                break

        # Clean up
        panel.deleteLater()
        del self._panels[panel_id]

        # Update tab titles
        for i in range(self._tab_widget.count()):
            self._tab_widget.setTabText(i, f'Filter Group {i + 1}')

        self._add_panel_btn.setEnabled(len(self._panels) < self._max_panels)

        # Notify of filter change
        self.filtersChanged.emit()

    @Slot(int)
    def _on_tab_close_requested(self, index: int) -> None:
        """Handle tab close request.

        Args:
            index: Index of tab to close
        """
        widget = self._tab_widget.widget(index)
        for panel_id, panel in self._panels.items():
            if panel == widget:
                self._remove_panel(panel_id)
                break

    @Slot(str, str, list)
    def _on_filter_changed(self, panel_id: str, filter_type: str, values: List[int]) -> None:
        """Handle filter value changes.

        Args:
            panel_id: ID of panel with changed filter
            filter_type: Type of filter
            values: Selected values
        """
        self._logger.debug(f'Filter changed in panel {panel_id}: {filter_type} = {values}')
        self.filtersChanged.emit()

    async def _on_filters_refreshed(self, event: Any) -> None:
        """Handle filter refresh events.

        Args:
            event: Event containing filter refresh information
        """
        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})

        if panel_id in self._panels:
            self._logger.debug(f'Updating filter values for panel {panel_id}')
            await self._panels[panel_id].update_filter_values(filter_values)

    def get_all_filters(self) -> List[Dict[str, List[int]]]:
        """Get all filter values from all panels.

        Returns:
            List of filter dictionaries, one per panel
        """
        filters = [panel.get_current_values() for panel in self._panels.values()]
        self._logger.debug(f'Collected filters from {len(self._panels)} panels: {filters}')
        return filters

    def refresh_all_panels(self) -> None:
        """Refresh all filter panels."""
        self._logger.debug('Refreshing all panels')
        for panel in self._panels.values():
            panel.refresh_all_filters()

    async def update_filter_values(self, panel_id: str, filter_values: Dict[str, List[Dict[str, Any]]]) -> None:
        """Update filter values for a specific panel.

        Args:
            panel_id: ID of panel to update
            filter_values: Dictionary of filter values
        """
        if panel_id in self._panels:
            await self._panels[panel_id].update_filter_values(filter_values)
