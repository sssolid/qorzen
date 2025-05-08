from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, cast

from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel,
    QMenu, QPushButton, QSizePolicy, QSpinBox, QTabWidget,
    QToolButton, QVBoxLayout, QWidget
)

from qorzen.core.event_bus_manager import EventBusManager

from .database_handler import DatabaseHandler
from .events import VCdbEventType


class FilterWidget(QWidget):
    """Base class for filter widgets."""

    valueChanged = Signal(str, list)

    def __init__(self, filter_type: str, filter_name: str, parent: Optional[QWidget] = None) -> None:
        """Initialize a filter widget.

        Args:
            filter_type: The type of filter
            filter_name: The display name of the filter
            parent: The parent widget
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
        """Get the filter type.

        Returns:
            The filter type
        """
        return self._filter_type

    def get_filter_name(self) -> str:
        """Get the filter name.

        Returns:
            The filter name
        """
        return self._filter_name

    def get_selected_values(self) -> List[int]:
        """Get the selected values.

        Returns:
            A list of selected value IDs
        """
        return []

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """Set the available values for the filter.

        Args:
            values: A list of value dictionaries with id, name, and count
        """
        pass

    @Slot()
    def clear(self) -> None:
        """Clear the filter selection."""
        pass


class ComboBoxFilter(FilterWidget):
    """A combo box filter widget."""

    def __init__(self, filter_type: str, filter_name: str, parent: Optional[QWidget] = None) -> None:
        """Initialize a combo box filter.

        Args:
            filter_type: The type of filter
            filter_name: The display name of the filter
            parent: The parent widget
        """
        super().__init__(filter_type, filter_name, parent)

        self._combo = QComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._combo.setMinimumWidth(150)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        self._combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._combo.wheelEvent = lambda event: event.ignore()
        self._layout.insertWidget(1, self._combo)

    def get_selected_values(self) -> List[int]:
        """Get the selected values.

        Returns:
            A list containing the selected value ID, or an empty list if none
        """
        if self._combo.currentIndex() <= 0:
            return []

        value_id = self._combo.currentData(Qt.ItemDataRole.UserRole)
        if value_id is not None:
            return [int(value_id)]

        return []

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """Set the available values for the filter.

        Args:
            values: A list of value dictionaries with id, name, and count
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
        """Handle selection changed event.

        Args:
            index: The index of the selected item
        """
        selected_values = self.get_selected_values()
        self.valueChanged.emit(self._filter_type, selected_values)

    @Slot()
    def clear(self) -> None:
        """Clear the filter selection."""
        self._combo.setCurrentIndex(0)


class YearRangeFilter(FilterWidget):
    """A year range filter widget."""

    def __init__(self, filter_type: str, filter_name: str, parent: Optional[QWidget] = None) -> None:
        """Initialize a year range filter.

        Args:
            filter_type: The type of filter
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
        self._start_year.wheelEvent = lambda event: event.ignore()

        self._end_label = QLabel('To:')
        self._end_year = QSpinBox()
        self._end_year.setRange(1900, 2100)
        self._end_year.setValue(2100)
        self._end_year.valueChanged.connect(self._on_value_changed)
        self._end_year.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._end_year.wheelEvent = lambda event: event.ignore()

        self._layout.insertWidget(1, self._start_label)
        self._layout.insertWidget(2, self._start_year)
        self._layout.insertWidget(3, self._end_label)
        self._layout.insertWidget(4, self._end_year)

    def get_selected_values(self) -> List[int]:
        """Get the selected values.

        Returns:
            A list containing the start and end years, or an empty list if invalid
        """
        start_year = self._start_year.value()
        end_year = self._end_year.value()

        if start_year > end_year:
            return []

        return [start_year, end_year]

    def set_available_values(self, values: List[Dict[str, Any]]) -> None:
        """Set the available values for the filter.

        Args:
            values: A list of value dictionaries with id, name, and count
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
        """Handle value changed event.

        Args:
            value: The new value
        """
        selected_values = self.get_selected_values()
        self.valueChanged.emit(self._filter_type, selected_values)

    @Slot()
    def clear(self) -> None:
        """Clear the filter selection."""
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
    """A panel of filters."""

    filterChanged = Signal(str, str, list)
    removeRequested = Signal(str)

    def __init__(
            self,
            panel_id: str,
            database_handler: DatabaseHandler,
            event_bus: EventBusManager,
            logger: logging.Logger,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize a filter panel.

        Args:
            panel_id: The unique ID of the panel
            database_handler: The database handler
            event_bus: The event bus
            logger: The logger
            parent: The parent widget
        """
        super().__init__(parent)

        self._panel_id = panel_id
        self._database_handler = database_handler
        self._event_bus = event_bus
        self._logger = logger

        self._available_filters = database_handler.get_available_filters()
        self._filters: Dict[str, FilterWidget] = {}
        self._current_values: Dict[str, List[int]] = {}
        self._auto_populate_filters = False
        self._is_refreshing = False

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

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

        auto_populate_layout = QHBoxLayout()
        self._auto_populate_checkbox = QCheckBox('Auto-populate other filters')
        self._auto_populate_checkbox.setChecked(False)
        self._auto_populate_checkbox.stateChanged.connect(self._on_auto_populate_changed)
        auto_populate_layout.addWidget(self._auto_populate_checkbox)
        auto_populate_layout.addStretch()
        self._layout.addLayout(auto_populate_layout)

        self._filters_layout = QVBoxLayout()
        self._filters_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._filters_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(line)

        # Add mandatory filters
        for filter_def in self._available_filters:
            if filter_def.get('mandatory', False):
                self._add_filter(filter_def['id'], filter_def['name'])

        # Subscribe to filters refreshed event
        self._event_bus.subscribe(
            event_type=VCdbEventType.filters_refreshed(),
            callback=self._on_filters_refreshed,
            subscriber_id=f'filter_panel_{panel_id}'
        )

    def __del__(self) -> None:
        """Clean up resources when the panel is deleted."""
        try:
            self._event_bus.unsubscribe(subscriber_id=f'filter_panel_{self._panel_id}')
        except Exception:
            pass

    def get_panel_id(self) -> str:
        """Get the panel ID.

        Returns:
            The panel ID
        """
        return self._panel_id

    def get_current_values(self) -> Dict[str, List[int]]:
        """Get the current filter values.

        Returns:
            A dictionary of filter types and their selected values
        """
        return self._current_values.copy()

    def set_filter_values(self, filter_type: str, values: List[Dict[str, Any]]) -> None:
        """Set the available values for a filter.

        Args:
            filter_type: The type of filter
            values: A list of value dictionaries with id, name, and count
        """
        if filter_type not in self._filters:
            return

        self._logger.debug(f'Setting filter values for {filter_type}: {len(values)} values')
        self._filters[filter_type].set_available_values(values)

    def _add_filter(self, filter_type: str, filter_name: str) -> None:
        """Add a filter to the panel.

        Args:
            filter_type: The type of filter
            filter_name: The display name of the filter
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

        self._refresh_filter_values(filter_type)

    def _refresh_filter_values(self, filter_type: str) -> None:
        """Refresh the values for a filter.

        Args:
            filter_type: The type of filter
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
            values = self._database_handler.get_filter_values(
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

    def _on_filters_refreshed(self, event: Any) -> None:
        """Handle filters refreshed event.

        Args:
            event: The event
        """
        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})

        if panel_id == self._panel_id:
            self._logger.debug(f'Received filter refresh for panel {panel_id}')
            self.update_filter_values(filter_values)

    @Slot(str, list)
    def _on_filter_value_changed(self, filter_type: str, values: List[int]) -> None:
        """Handle filter value changed event.

        Args:
            filter_type: The type of filter
            values: The selected values
        """
        self._logger.debug(f'Filter value changed: {filter_type} = {values}')

        if not values:
            if filter_type in self._current_values:
                del self._current_values[filter_type]
        else:
            self._current_values[filter_type] = values

        self.filterChanged.emit(self._panel_id, filter_type, values)

        if self._auto_populate_filters:
            self._logger.debug(f'Auto-populating other filters after {filter_type} change')

            # Publish filter changed event
            self._event_bus.publish(
                event_type=VCdbEventType.filter_changed(),
                source='vcdb_explorer_filter_panel',
                payload={
                    'panel_id': self._panel_id,
                    'filter_type': filter_type,
                    'values': values,
                    'current_filters': self._current_values,
                    'auto_populate': self._auto_populate_filters
                }
            )

    @Slot(int)
    def _on_auto_populate_changed(self, state: int) -> None:
        """Handle auto-populate checkbox state changed.

        Args:
            state: The new state
        """
        self._auto_populate_filters = state == Qt.CheckState.Checked
        self._logger.debug(f'Auto-populate changed to: {self._auto_populate_filters}')

        if self._auto_populate_filters and self._current_values:
            for filter_type, values in self._current_values.items():
                # Publish filter changed event for each current filter
                self._event_bus.publish(
                    event_type=VCdbEventType.filter_changed(),
                    source='vcdb_explorer_filter_panel',
                    payload={
                        'panel_id': self._panel_id,
                        'filter_type': filter_type,
                        'values': values,
                        'current_filters': self._current_values,
                        'auto_populate': self._auto_populate_filters
                    }
                )

    @Slot()
    def _show_add_filter_menu(self) -> None:
        """Show the add filter menu."""
        menu = QMenu(self)

        for filter_def in self._available_filters:
            filter_id = filter_def['id']
            if filter_id in self._filters:
                continue

            action = menu.addAction(filter_def['name'])
            action.setData(filter_id)

        if not menu.isEmpty():
            menu.triggered.connect(
                lambda action: self._add_filter(action.data(), action.text())
            )
            menu.popup(self._add_filter_btn.mapToGlobal(self._add_filter_btn.rect().bottomLeft()))

    @Slot()
    def _clear_all_filters(self) -> None:
        """Clear all filters in the panel."""
        for filter_widget in self._filters.values():
            filter_widget.clear()

    @Slot()
    def _remove_panel(self) -> None:
        """Request removal of the panel."""
        self.removeRequested.emit(self._panel_id)

    def update_filter_values(self, filter_values: Dict[str, List[Dict[str, Any]]]) -> None:
        """Update the filter values.

        Args:
            filter_values: A dictionary of filter types and their available values
        """
        self._is_refreshing = True
        try:
            for filter_type, values in filter_values.items():
                if filter_type in self._filters:
                    self.set_filter_values(filter_type, values)
        finally:
            self._is_refreshing = False


class FilterPanelManager(QWidget):
    """Manager for filter panels."""

    filtersChanged = Signal()

    def __init__(
            self,
            database_handler: DatabaseHandler,
            event_bus: EventBusManager,
            logger: logging.Logger,
            max_panels: int = 5,
            parent: Optional[QWidget] = None
    ) -> None:
        """Initialize a filter panel manager.

        Args:
            database_handler: The database handler
            event_bus: The event bus
            logger: The logger
            max_panels: The maximum number of panels
            parent: The parent widget
        """
        super().__init__(parent)

        self._database_handler = database_handler
        self._event_bus = event_bus
        self._logger = logger
        self._max_panels = max_panels
        self._panels: Dict[str, FilterPanel] = {}
        self._available_filters = database_handler.get_available_filters()

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        header_layout = QHBoxLayout()

        title = QLabel('Query Filters')
        title.setStyleSheet('font-weight: bold; font-size: 14px;')
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._add_panel_btn = QPushButton('Add Filter Group')
        self._add_panel_btn.clicked.connect(self._add_panel)
        header_layout.addWidget(self._add_panel_btn)

        self._layout.addLayout(header_layout)

        self._tab_widget = QTabWidget()
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self._layout.addWidget(self._tab_widget)

        # Subscribe to filters refreshed event
        self._event_bus.subscribe(
            event_type=VCdbEventType.filters_refreshed(),
            callback=self._on_filters_refreshed,
            subscriber_id='filter_panel_manager'
        )

        # Add initial panel
        self._add_panel()

    def __del__(self) -> None:
        """Clean up resources when the manager is deleted."""
        try:
            self._event_bus.unsubscribe(subscriber_id='filter_panel_manager')
        except Exception:
            pass

    def _add_panel(self) -> None:
        """Add a new filter panel."""
        if len(self._panels) >= self._max_panels:
            self._logger.warning(f'Maximum number of filter panels ({self._max_panels}) reached')
            return

        panel_id = str(uuid.uuid4())

        panel = FilterPanel(
            panel_id,
            self._database_handler,
            self._event_bus,
            self._logger
        )

        panel.filterChanged.connect(self._on_filter_changed)
        panel.removeRequested.connect(self._remove_panel)

        tab_index = self._tab_widget.addTab(panel, f'Filter Group {len(self._panels) + 1}')
        self._tab_widget.setCurrentIndex(tab_index)

        self._panels[panel_id] = panel
        self._add_panel_btn.setEnabled(len(self._panels) < self._max_panels)

    def _remove_panel(self, panel_id: str) -> None:
        """Remove a filter panel.

        Args:
            panel_id: The ID of the panel to remove
        """
        if panel_id not in self._panels:
            return

        if len(self._panels) <= 1:
            return

        panel = self._panels[panel_id]

        for i in range(self._tab_widget.count()):
            if self._tab_widget.widget(i) == panel:
                self._tab_widget.removeTab(i)
                break

        panel.deleteLater()
        del self._panels[panel_id]

        for i in range(self._tab_widget.count()):
            self._tab_widget.setTabText(i, f'Filter Group {i + 1}')

        self._add_panel_btn.setEnabled(len(self._panels) < self._max_panels)
        self.filtersChanged.emit()

    @Slot(int)
    def _on_tab_close_requested(self, index: int) -> None:
        """Handle tab close requested.

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
        """Handle filter changed.

        Args:
            panel_id: The ID of the panel containing the filter
            filter_type: The type of filter
            values: The selected values
        """
        self._logger.debug(f'Filter changed in panel {panel_id}: {filter_type} = {values}')
        self.filtersChanged.emit()

    @Slot(Any)
    def _on_filters_refreshed(self, event: Any) -> None:
        """Handle filters refreshed event.

        Args:
            event: The event
        """
        payload = event.payload
        panel_id = payload.get('panel_id')
        filter_values = payload.get('filter_values', {})

        if panel_id in self._panels:
            self._logger.debug(f'Updating filter values for panel {panel_id}')
            self._panels[panel_id].update_filter_values(filter_values)

    def get_all_filters(self) -> List[Dict[str, List[int]]]:
        """Get all filter configurations.

        Returns:
            A list of filter dictionaries
        """
        return [panel.get_current_values() for panel in self._panels.values()]

    def refresh_all_panels(self) -> None:
        """Refresh all panels."""
        self._logger.debug('Refreshing all panels')
        for panel in self._panels.values():
            panel.refresh_all_filters()

    def update_filter_values(self, panel_id: str, filter_values: Dict[str, List[Dict[str, Any]]]) -> None:
        """Update filter values for a panel.

        Args:
            panel_id: The ID of the panel
            filter_values: A dictionary of filter types and their available values
        """
        if panel_id in self._panels:
            self._panels[panel_id].update_filter_values(filter_values)