from __future__ import annotations

"""
VCdb filter panel modules.

This module provides UI components for filtering vehicle component data, 
including filter widgets, filter panels, and a filter panel manager.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, cast

from qasync import asyncSlot
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel,
    QMenu, QPushButton, QSizePolicy, QSpinBox, QTabWidget, QToolButton,
    QVBoxLayout, QWidget, QProgressBar, QApplication
)

from qorzen.core.event_bus_manager import EventBusManager
from .database_handler import DatabaseHandler
from .events import VCdbEventType


class FilterWidget(QWidget):
    """Base class for filter widgets that allow selecting values for filtering."""

    valueChanged = Signal(str, list)

    def __init__(self, filter_type: str, filter_name: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the filter widget.

        Args:
            filter_type: The type identifier for this filter
            filter_name: The display name of the filter
            parent: The parent widget
        """
        super().__init__(parent)
        self._filter_type = filter_type
        self._filter_name = filter_name
        self._loading = False

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
        """Get the filter type identifier."""
        return self._filter_type

    def get_filter_name(self) -> str:
        """Get the display name of the filter."""
        return self._filter_name

    def get_selected_values(self) -> List[int]:
        """Get the currently selected values for this filter."""
        return []

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """
        Set the available values for this filter.

        Args:
            values: List of value dictionaries with 'id', 'name', and 'count' keys
        """
        pass

    def set_loading(self, loading: bool) -> None:
        """
        Set the loading state of the filter.

        Args:
            loading: True if the filter is loading data, False otherwise
        """
        self._loading = loading
        self.setEnabled(not loading)

    @Slot()
    def clear(self) -> None:
        """Clear the current filter selection."""
        pass


class ComboBoxFilter(FilterWidget):
    """Filter widget using a combo box for selection."""

    def __init__(self, filter_type: str, filter_name: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the combo box filter.

        Args:
            filter_type: The type identifier for this filter
            filter_name: The display name of the filter
            parent: The parent widget
        """
        super().__init__(filter_type, filter_name, parent)

        self._combo = QComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._combo.setMinimumWidth(150)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        self._combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._combo.wheelEvent = lambda event: event.ignore()  # type: ignore
        self._layout.insertWidget(1, self._combo)

        self._loading_indicator = QProgressBar()
        self._loading_indicator.setRange(0, 0)
        self._loading_indicator.setMaximumWidth(100)
        self._loading_indicator.setMaximumHeight(10)
        self._loading_indicator.setVisible(False)
        self._layout.insertWidget(2, self._loading_indicator)

    def get_selected_values(self) -> List[int]:
        """Get the currently selected value ID from the combo box."""
        if self._combo.currentIndex() <= 0:
            return []

        value_id = self._combo.currentData(Qt.ItemDataRole.UserRole)
        if value_id is not None:
            return [int(value_id)]
        return []

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """
        Set the available values in the combo box.

        Args:
            values: List of value dictionaries with 'id', 'name', and 'count' keys
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

    def set_loading(self, loading: bool) -> None:
        """Set the loading state and update the loading indicator."""
        super().set_loading(loading)
        self._loading_indicator.setVisible(loading)

    @Slot(int)
    def _on_selection_changed(self, index: int) -> None:
        """Handle selection change in the combo box."""
        selected_values = self.get_selected_values()
        self.valueChanged.emit(self._filter_type, selected_values)

    @Slot()
    def clear(self) -> None:
        """Clear the selection by setting it to the 'Any' option."""
        self._combo.setCurrentIndex(0)


class YearRangeFilter(FilterWidget):
    """Filter widget for selecting a year range."""

    def __init__(self, filter_type: str, filter_name: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the year range filter.

        Args:
            filter_type: The type identifier for this filter
            filter_name: The display name of the filter
            parent: The parent widget
        """
        super().__init__(filter_type, filter_name, parent)

        self._start_label = QLabel('From:')
        self._start_year = QSpinBox()
        self._start_year.setRange(1900, 2100)
        self._start_year.setValue(1900)
        self._start_year.valueChanged.connect(self._on_value_changed)
        self._start_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._start_year.wheelEvent = lambda event: event.ignore()  # type: ignore

        self._end_label = QLabel('To:')
        self._end_year = QSpinBox()
        self._end_year.setRange(1900, 2100)
        self._end_year.setValue(2100)
        self._end_year.valueChanged.connect(self._on_value_changed)
        self._end_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._end_year.wheelEvent = lambda event: event.ignore()  # type: ignore

        self._layout.insertWidget(1, self._start_label)
        self._layout.insertWidget(2, self._start_year)
        self._layout.insertWidget(3, self._end_label)
        self._layout.insertWidget(4, self._end_year)

    def get_selected_values(self) -> List[int]:
        """
        Get the selected year range as a list of two integers.

        Returns:
            A list containing [start_year, end_year] or an empty list if invalid
        """
        start_year = self._start_year.value()
        end_year = self._end_year.value()

        if start_year > end_year:
            return []

        return [start_year, end_year]

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """
        Set the available years for the range spinboxes.

        Args:
            values: List of value dictionaries with 'id', 'name', and 'count' keys
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
        """Handle value changes in either spinbox."""
        # Add a small delay to prevent multiple updates when both values change
        QTimer.singleShot(50, self._emit_value_changed)

    def _emit_value_changed(self) -> None:
        """Emit the valueChanged signal with the current values."""
        selected_values = self.get_selected_values()
        self.valueChanged.emit(self._filter_type, selected_values)

    @Slot()
    def clear(self) -> None:
        """Reset the year range to the full available range."""
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
    """A panel containing multiple filters that can be applied together."""

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
        """
        Initialize the filter panel.

        Args:
            panel_id: Unique identifier for this panel
            database_handler: Handler for database operations
            event_bus_manager: Manager for event bus operations
            logger: Logger instance
            parent: Parent widget
        """
        super().__init__(parent)

        self._auto_populate_filters = False
        self._refresh_pending = False

        self._panel_id = panel_id
        self._database_handler = database_handler
        self._event_bus_manager = event_bus_manager
        self._logger = logger

        self._available_filters = database_handler.get_available_filters()
        self._filters: Dict[str, FilterWidget] = {}
        self._current_values: Dict[str, List[int]] = {}

        self._auto_populate_filters = False
        self._is_refreshing = False
        self._refresh_pending = False

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Header layout with buttons
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

        self._refresh_btn = QPushButton('Refresh')
        self._refresh_btn.clicked.connect(self._refresh_filters)
        header_layout.addWidget(self._refresh_btn)

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

        # Filters container
        self._filters_layout = QVBoxLayout()
        self._filters_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._filters_layout)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(line)

        # Initialize the panel
        asyncio.create_task(self.initialize())

    def closeEvent(self, event: Any) -> None:
        """Handle the close event by unsubscribing from events."""
        self._event_bus_manager.unsubscribe(subscriber_id=f'filter_panel_{self._panel_id}')

    async def initialize(self) -> None:
        """Initialize the panel by adding mandatory filters and subscribing to events."""
        # Add mandatory filters
        for filter_def in self._available_filters:
            if filter_def.get('mandatory', False):
                await self._add_filter(filter_def['id'], filter_def['name'])

        # Subscribe to filter refresh events
        await self._event_bus_manager.subscribe(
            event_type=VCdbEventType.filters_refreshed(),
            subscriber_id=f'filter_panel_{self._panel_id}',
            callback=self._on_filters_refreshed
        )

    def get_panel_id(self) -> str:
        """Get the panel's unique identifier."""
        return self._panel_id

    def get_current_values(self) -> Dict[str, List[int]]:
        """Get the current filter values for all filters in this panel."""
        return self._current_values.copy()

    async def set_filter_values(self, filter_type: str, values: List[Dict[str, Any]]) -> None:
        """
        Set the available values for a specific filter.

        Args:
            filter_type: The type of filter to update
            values: The available values for the filter
        """
        if filter_type not in self._filters:
            return

        self._logger.debug(f'Setting filter values for {filter_type}: {len(values)} values')
        self._filters[filter_type].set_loading(False)
        self._filters[filter_type].set_available_values(values)

    async def _add_filter(self, filter_type: str, filter_name: str) -> None:
        """
        Add a new filter to the panel.

        Args:
            filter_type: The type identifier for the filter
            filter_name: The display name of the filter
        """
        if filter_type in self._filters:
            return

        # Create the appropriate filter widget based on type
        if filter_type == 'year_range':
            filter_widget = YearRangeFilter(filter_type, filter_name, self)
        else:
            filter_widget = ComboBoxFilter(filter_type, filter_name, self)

        filter_widget.valueChanged.connect(self._on_filter_value_changed)
        self._filters_layout.addWidget(filter_widget)
        self._filters[filter_type] = filter_widget

        # Start loading values for this filter
        filter_widget.set_loading(True)
        await self._refresh_filter_values(filter_type)

    async def _refresh_filter_values(self, filter_type: str) -> None:
        """
        Refresh the available values for a specific filter.

        Args:
            filter_type: The type of filter to refresh
        """
        if filter_type not in self._filters or self._is_refreshing:
            return

        try:
            # Handle year_range special case
            exclude_filters = {filter_type}
            if filter_type == 'year_range':
                exclude_filters.add('year')
            elif filter_type == 'year':
                exclude_filters.add('year_range')

            self._logger.debug(f'Refreshing filter values for {filter_type}')

            # Show loading indicator
            self._filters[filter_type].set_loading(True)

            # Fetch filter values
            values = await self._database_handler.get_filter_values(
                filter_type=filter_type if filter_type != 'year_range' else 'year',
                current_filters=self._current_values,
                exclude_filters=exclude_filters
            )

            # Update the filter with the fetched values
            await self.set_filter_values(filter_type, values)

        except Exception as e:
            self._logger.error(f'Error refreshing filter values for {filter_type}: {str(e)}')
            if filter_type in self._filters:
                self._filters[filter_type].set_loading(False)

    @Slot()
    def _refresh_filters(self) -> None:
        """Manually refresh all filters."""
        self._logger.debug(f'Manually refreshing all filters, auto-populate: {self._auto_populate_filters}')

        # Mark all filters as loading
        for filter_widget in self._filters.values():
            filter_widget.set_loading(True)

        self._refresh_pending = True

        # Publish a filter change event to trigger refresh
        asyncio.create_task(self._event_bus_manager.publish(
            event_type=VCdbEventType.filter_changed(),
            source='vcdb_explorer_filter_panel',
            payload={
                'panel_id': self._panel_id,
                'filter_type': 'refresh_all',
                'values': [],
                'current_filters': self._current_values.copy(),
                'auto_populate': True
            }
        ))

    def refresh_all_filters(self) -> None:
        # mark loading
        for w in self._filters.values():
            w.set_loading(True)
        self._refresh_pending = True

        # publish exactly one refresh_all
        asyncio.create_task(
            self._event_bus_manager.publish(
                event_type=VCdbEventType.filter_changed(),
                source='vcdb_explorer_filter_panel',
                payload={
                    'panel_id': self._panel_id,
                    'filter_type': 'refresh_all',
                    'values': None,
                    'current_filters': self._current_values.copy(),
                    'auto_populate': False
                }
            )
        )

    async def _on_filters_refreshed(self, event):
        # Ignore if it’s for a different panel
        if event.payload.get('panel_id') != self._panel_id:
            return

        # We asked for exactly one—consume it
        if self._refresh_pending:
            self._refresh_pending = False
        else:
            # If it wasn’t our “refresh_all”, still proceed.
            pass

        # Now update the UI exactly once
        await self.update_filter_values(event.payload['filter_values'])

    @Slot(str, list)
    def _on_filter_value_changed(self, filter_type: str, values: List[int]) -> None:
        """
        Handle value changes in filters.

        Args:
            filter_type: The type of filter that changed
            values: The new values for the filter
        """
        self._logger.debug(f'Filter value changed: {filter_type} = {values}')

        # Update the current values
        if not values:
            if filter_type in self._current_values:
                del self._current_values[filter_type]
        else:
            self._current_values[filter_type] = values

        self._logger.debug(f'Updated filter state: {self._current_values}')

        # Emit the filter changed signal
        self.filterChanged.emit(self._panel_id, filter_type, values)

        # Publish the filter changed event
        self._logger.debug(f'Publishing filter changed event: auto_populate={self._auto_populate_filters}')
        asyncio.create_task(self._event_bus_manager.publish(
            event_type=VCdbEventType.filter_changed(),
            source='vcdb_explorer_filter_panel',
            payload={
                'panel_id': self._panel_id,
                'filter_type': filter_type,
                'values': values,
                'current_filters': self._current_values.copy(),
                'auto_populate': self._auto_populate_filters
            }
        ))

    @asyncSlot(int)
    async def _on_auto_populate_changed(self, state: int) -> None:
        is_checked = (state == 2)
        # No‑op if nothing changed
        if is_checked == self._auto_populate_filters:
            return

        self._auto_populate_filters = is_checked

        # Only trigger when turning ON *and* we have existing selections
        if not (self._auto_populate_filters and self._current_values):
            return

        self._logger.debug('Auto‑populate ENABLED → scheduling full refresh')

        # Show all spinners
        for w in self._filters.values():
            w.set_loading(True)

        self.refresh_all_filters()

    @Slot()
    def _show_add_filter_menu(self) -> None:
        """Show the menu for adding a new filter."""
        menu = QMenu(self)

        # Add menu items for available filters that aren't already added
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
        self._is_refreshing = True
        try:
            for filter_type, values in filter_values.items():
                if filter_type not in self._filters:
                    continue
                # update one at a time…
                await self.set_filter_values(filter_type, values)
                # let Qt repaint before continuing:
                await asyncio.sleep(0)
        finally:
            self._is_refreshing = False


class FilterPanelManager(QWidget):
    """Manager for multiple filter panels working together."""

    filtersChanged = Signal()

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus_manager: EventBusManager,
            logger: logging.Logger,
            max_panels: int = 5,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the filter panel manager.

        Args:
            database_handler: Handler for database operations
            event_bus_manager: Manager for event bus operations
            logger: Logger instance
            max_panels: Maximum number of filter panels allowed
            parent: Parent widget
        """
        super().__init__(parent)

        self._database_handler = database_handler
        self._event_bus_manager = event_bus_manager
        self._logger = logger
        self._max_panels = max_panels

        self._panels: Dict[str, FilterPanel] = {}
        self._available_filters = database_handler.get_available_filters()
        self._refreshing = False

        # Main layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # Header layout
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

        # Initialize
        asyncio.create_task(self._subscribe_to_events())
        self._add_panel()  # Add the first panel

    def closeEvent(self, event: Any) -> None:
        """Handle the close event by unsubscribing from events."""
        self._event_bus_manager.unsubscribe(subscriber_id='filter_panel_manager')

    async def _subscribe_to_events(self) -> None:
        """Subscribe to filter refresh events."""
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

        # Create a new panel with a unique ID
        panel_id = str(uuid.uuid4())
        panel = FilterPanel(
            panel_id,
            self._database_handler,
            self._event_bus_manager,
            self._logger
        )

        # Connect signals
        panel.filterChanged.connect(self._on_filter_changed)
        panel.removeRequested.connect(self._remove_panel)

        # Add to tab widget
        tab_index = self._tab_widget.addTab(panel, f'Filter Group {len(self._panels) + 1}')
        self._tab_widget.setCurrentIndex(tab_index)

        # Store the panel
        self._panels[panel_id] = panel

        # Update UI state
        self._add_panel_btn.setEnabled(len(self._panels) < self._max_panels)

    def _remove_panel(self, panel_id: str) -> None:
        """
        Remove a filter panel.

        Args:
            panel_id: The ID of the panel to remove
        """
        if panel_id not in self._panels:
            return

        if len(self._panels) <= 1:
            return  # Don't remove the last panel

        panel = self._panels[panel_id]

        # Remove from tab widget
        for i in range(self._tab_widget.count()):
            if self._tab_widget.widget(i) == panel:
                self._tab_widget.removeTab(i)
                break

        # Clean up
        panel.deleteLater()
        del self._panels[panel_id]

        # Renumber tabs
        for i in range(self._tab_widget.count()):
            self._tab_widget.setTabText(i, f'Filter Group {i + 1}')

        # Update UI state
        self._add_panel_btn.setEnabled(len(self._panels) < self._max_panels)

        # Notify of changes
        self.filtersChanged.emit()

    @Slot(int)
    def _on_tab_close_requested(self, index: int) -> None:
        """
        Handle tab close request.

        Args:
            index: The index of the tab to close
        """
        widget = self._tab_widget.widget(index)
        for panel_id, panel in self._panels.items():
            if panel == widget:
                self._remove_panel(panel_id)
                break

    @Slot(str, str, list)
    def _on_filter_changed(self, panel_id: str, filter_type: str, values: List[int]) -> None:
        """
        Handle filter value changes.

        Args:
            panel_id: The ID of the panel containing the changed filter
            filter_type: The type of filter that changed
            values: The new values for the filter
        """
        self._logger.debug(f'Filter changed in panel {panel_id}: {filter_type} = {values}')
        self.filtersChanged.emit()

    async def _on_filters_refreshed(self, event: Any) -> None:
        """
        Handle filters refreshed event.

        Args:
            event: The event object containing refresh information
        """
        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})

        if panel_id in self._panels:
            self._logger.debug(f'Updating filter values for panel {panel_id}')
            await self._panels[panel_id].update_filter_values(filter_values)

    def get_all_filters(self) -> List[Dict[str, List[int]]]:
        """
        Get all current filter values from all panels.

        Returns:
            A list of filter dictionaries, one per panel
        """
        filters = [panel.get_current_values() for panel in self._panels.values()]
        self._logger.debug(f'Collected filters from {len(self._panels)} panels: {filters}')
        return filters

    def refresh_all_panels(self) -> None:
        """Refresh all filter panels."""
        self._logger.debug('Refreshing all panels')
        self._refreshing = True
        for panel in self._panels.values():
            panel.refresh_all_filters()

    async def update_filter_values(self, panel_id: str, filter_values: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Update filter values for a specific panel.

        Args:
            panel_id: The ID of the panel to update
            filter_values: The new filter values
        """
        if panel_id in self._panels:
            await self._panels[panel_id].update_filter_values(filter_values)