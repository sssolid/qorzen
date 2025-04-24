from __future__ import annotations

import asyncio
import csv
import io
import os
import sys
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

import pandas as pd
import qasync
import structlog
from PySide6.QtCore import (QEventLoop, QModelIndex, QObject, QPoint, QSize, QTimer, Qt,
                            Signal, Slot)
from PySide6.QtGui import QAction, QClipboard, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QFrame,
                               QGridLayout, QHBoxLayout, QHeaderView, QLabel, QMainWindow,
                               QMenu, QMenuBar, QMessageBox, QProgressDialog, QPushButton,
                               QScrollArea, QSizePolicy, QSpinBox, QStatusBar, QTableView,
                               QVBoxLayout, QWidget)

from qorzen.plugins.autocarequery.config.settings import DEFAULT_QUERY_LIMIT, MAX_QUERY_LIMIT, UI_REFRESH_INTERVAL_MS
from qorzen.plugins.autocarequery.models.data_models import FilterDTO, VehicleResultDTO
from qorzen.plugins.autocarequery.models.table_model import VehicleResultsTableModel
from qorzen.plugins.autocarequery.repository.database_repository import DatabaseRepository

logger = structlog.get_logger(__name__)


class AutocareQueryTab(QWidget):
    """Main tab widget for the Autocare Query Plugin."""

    def __init__(
            self,
            event_bus: Any,
            logger: Any,
            config: Any,
            file_manager: Any = None,
            thread_manager: Any = None,
            connection_string: str = "",
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the query tab.

        Args:
            event_bus: Event bus for publishing and subscribing to events
            logger: Logger for the plugin
            config: Configuration provider
            file_manager: File manager for file operations
            thread_manager: Thread manager for async operations
            connection_string: Database connection string
            parent: Parent widget
        """
        super().__init__(parent)

        self._event_bus = event_bus
        self._logger = logger
        self._config = config
        self._file_manager = file_manager
        self._thread_manager = thread_manager
        self.connection_string = connection_string

        self.db_repo = DatabaseRepository(connection_string)
        self.current_filters = FilterDTO()
        self.filters_updating = False
        self.result_limit = DEFAULT_QUERY_LIMIT
        self.limit_enabled = True
        self.progress_dialog = None

        # Setup UI components
        self.setup_ui()

        # Initialize combo boxes with "All" option
        self.initialize_dropdowns()

        # Schedule async initialization
        QTimer.singleShot(100, self.start_async_initialization)

        self._logger.info('Autocare Query Tab initialized')

    def setup_ui(self) -> None:
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        self.all_combo_boxes = []

        # Create filter frame
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.Shape.StyledPanel)
        filter_layout = QGridLayout(filter_frame)

        # Year filter with range option
        year_frame = QFrame()
        year_layout = QHBoxLayout(year_frame)
        year_layout.setContentsMargins(0, 0, 0, 0)
        year_layout.addWidget(QLabel('Year:'))
        self.year_combo = QComboBox()
        self.year_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('year'))
        year_layout.addWidget(self.year_combo)
        self.all_combo_boxes.append(self.year_combo)

        self.year_range_checkbox = QCheckBox('Use Range')
        self.year_range_checkbox.setChecked(False)
        self.year_range_checkbox.stateChanged.connect(self.on_year_range_toggle)
        year_layout.addWidget(self.year_range_checkbox)

        self.year_range_start = QSpinBox()
        self.year_range_start.setRange(1900, 2050)
        self.year_range_start.setValue(2010)
        self.year_range_start.setEnabled(False)
        self.year_range_start.valueChanged.connect(self.on_year_range_changed)
        year_layout.addWidget(self.year_range_start)

        year_layout.addWidget(QLabel('to'))

        self.year_range_end = QSpinBox()
        self.year_range_end.setRange(1900, 2050)
        self.year_range_end.setValue(2025)
        self.year_range_end.setEnabled(False)
        self.year_range_end.valueChanged.connect(self.on_year_range_changed)
        year_layout.addWidget(self.year_range_end)

        filter_layout.addWidget(year_frame, 0, 0, 1, 2)

        # Make filter
        filter_layout.addWidget(QLabel('Make:'), 0, 2)
        self.make_combo = QComboBox()
        self.make_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('make'))
        filter_layout.addWidget(self.make_combo, 0, 3)
        self.all_combo_boxes.append(self.make_combo)

        # Model filter
        filter_layout.addWidget(QLabel('Model:'), 0, 4)
        self.model_combo = QComboBox()
        self.model_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('model'))
        filter_layout.addWidget(self.model_combo, 0, 5)
        self.all_combo_boxes.append(self.model_combo)

        # Submodel filter
        filter_layout.addWidget(QLabel('Submodel:'), 1, 0)
        self.submodel_combo = QComboBox()
        self.submodel_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('submodel'))
        filter_layout.addWidget(self.submodel_combo, 1, 1)
        self.all_combo_boxes.append(self.submodel_combo)

        # Engine Liter filter
        filter_layout.addWidget(QLabel('Engine Liter:'), 1, 2)
        self.engine_liter_combo = QComboBox()
        self.engine_liter_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('engine_liter'))
        filter_layout.addWidget(self.engine_liter_combo, 1, 3)
        self.all_combo_boxes.append(self.engine_liter_combo)

        # Engine CID filter
        filter_layout.addWidget(QLabel('Engine CID:'), 1, 4)
        self.engine_cid_combo = QComboBox()
        self.engine_cid_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('engine_cid'))
        filter_layout.addWidget(self.engine_cid_combo, 1, 5)
        self.all_combo_boxes.append(self.engine_cid_combo)

        # Cylinder Head Type filter
        filter_layout.addWidget(QLabel('Cylinder Head:'), 2, 0)
        self.cylinder_head_type_combo = QComboBox()
        self.cylinder_head_type_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('cylinder_head_type'))
        filter_layout.addWidget(self.cylinder_head_type_combo, 2, 1)
        self.all_combo_boxes.append(self.cylinder_head_type_combo)

        # Valves filter
        filter_layout.addWidget(QLabel('Valves:'), 2, 2)
        self.valves_combo = QComboBox()
        self.valves_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('valves'))
        filter_layout.addWidget(self.valves_combo, 2, 3)
        self.all_combo_boxes.append(self.valves_combo)

        # Body Code filter
        filter_layout.addWidget(QLabel('Body Code:'), 2, 4)
        self.mfr_body_code_combo = QComboBox()
        self.mfr_body_code_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('mfr_body_code'))
        filter_layout.addWidget(self.mfr_body_code_combo, 2, 5)
        self.all_combo_boxes.append(self.mfr_body_code_combo)

        # Doors filter
        filter_layout.addWidget(QLabel('Doors:'), 3, 0)
        self.body_num_doors_combo = QComboBox()
        self.body_num_doors_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('body_num_doors'))
        filter_layout.addWidget(self.body_num_doors_combo, 3, 1)
        self.all_combo_boxes.append(self.body_num_doors_combo)

        # Wheelbase filter
        filter_layout.addWidget(QLabel('Wheelbase:'), 3, 2)
        self.wheel_base_combo = QComboBox()
        self.wheel_base_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('wheel_base'))
        filter_layout.addWidget(self.wheel_base_combo, 3, 3)
        self.all_combo_boxes.append(self.wheel_base_combo)

        # Brake ABS filter
        filter_layout.addWidget(QLabel('Brake ABS:'), 3, 4)
        self.brake_abs_combo = QComboBox()
        self.brake_abs_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('brake_abs'))
        filter_layout.addWidget(self.brake_abs_combo, 3, 5)
        self.all_combo_boxes.append(self.brake_abs_combo)

        # Steering filter
        filter_layout.addWidget(QLabel('Steering:'), 4, 0)
        self.steering_system_combo = QComboBox()
        self.steering_system_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('steering_system'))
        filter_layout.addWidget(self.steering_system_combo, 4, 1)
        self.all_combo_boxes.append(self.steering_system_combo)

        # Transmission Control filter
        filter_layout.addWidget(QLabel('Trans Control:'), 4, 2)
        self.transmission_control_type_combo = QComboBox()
        self.transmission_control_type_combo.currentIndexChanged.connect(
            lambda: self.on_filter_changed('transmission_control_type'))
        filter_layout.addWidget(self.transmission_control_type_combo, 4, 3)
        self.all_combo_boxes.append(self.transmission_control_type_combo)

        # Transmission Code filter
        filter_layout.addWidget(QLabel('Trans Code:'), 4, 4)
        self.transmission_mfr_code_combo = QComboBox()
        self.transmission_mfr_code_combo.currentIndexChanged.connect(
            lambda: self.on_filter_changed('transmission_mfr_code'))
        filter_layout.addWidget(self.transmission_mfr_code_combo, 4, 5)
        self.all_combo_boxes.append(self.transmission_mfr_code_combo)

        # Drive Type filter
        filter_layout.addWidget(QLabel('Drive Type:'), 5, 0)
        self.drive_type_combo = QComboBox()
        self.drive_type_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('drive_type'))
        filter_layout.addWidget(self.drive_type_combo, 5, 1)
        self.all_combo_boxes.append(self.drive_type_combo)

        # Store year range controls for enabling/disabling
        self.year_range_controls = [self.year_range_checkbox, self.year_range_start, self.year_range_end]

        # Results limit controls
        limit_layout = QHBoxLayout()
        self.limit_checkbox = QCheckBox('Limit Results:')
        self.limit_checkbox.setChecked(self.limit_enabled)
        self.limit_checkbox.stateChanged.connect(self.on_limit_changed)
        limit_layout.addWidget(self.limit_checkbox)

        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setRange(100, MAX_QUERY_LIMIT)
        self.limit_spinbox.setSingleStep(100)
        self.limit_spinbox.setValue(self.result_limit)
        self.limit_spinbox.setEnabled(self.limit_enabled)
        self.limit_spinbox.valueChanged.connect(self.on_limit_value_changed)
        limit_layout.addWidget(self.limit_spinbox)

        filter_layout.addLayout(limit_layout, 5, 2, 1, 2)

        # Query control buttons
        button_layout = QHBoxLayout()
        self.execute_button = QPushButton('Execute Query')
        self.execute_button.clicked.connect(self.execute_query)
        button_layout.addWidget(self.execute_button)

        self.reset_button = QPushButton('Reset Filters')
        self.reset_button.clicked.connect(self.reset_filters)
        button_layout.addWidget(self.reset_button)

        filter_layout.addLayout(button_layout, 5, 4, 1, 2)

        main_layout.addWidget(filter_frame)

        # Results display
        results_frame = QFrame()
        results_frame.setFrameShape(QFrame.Shape.StyledPanel)
        results_layout = QVBoxLayout(results_frame)

        self.results_table = QTableView()
        self.results_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.results_table.setSortingEnabled(True)
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)

        self.table_model = VehicleResultsTableModel()
        self.results_table.setModel(self.table_model)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setStretchLastSection(True)

        results_layout.addWidget(self.results_table)

        # Export controls
        export_layout = QHBoxLayout()
        self.export_button = QPushButton('Export to Excel')
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setEnabled(False)
        export_layout.addWidget(self.export_button)

        self.copy_button = QPushButton('Copy Selected')
        self.copy_button.clicked.connect(self.copy_selection)
        self.copy_button.setEnabled(False)
        export_layout.addWidget(self.copy_button)

        self.status_label = QLabel('')
        export_layout.addWidget(self.status_label)
        export_layout.addStretch()

        results_layout.addLayout(export_layout)

        main_layout.addWidget(results_frame, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage('Ready')
        main_layout.addWidget(self.status_bar)

    def start_async_initialization(self) -> None:
        """Start async initialization of dropdowns."""
        self._logger.info("Starting async initialization of dropdowns")

        # Make sure to set the initial state properly
        self.filters_updating = True
        self.set_dropdowns_enabled(False)
        self.status_bar.showMessage('Initializing dropdowns...')

        # Schedule initialization to run after the UI has fully initialized
        QTimer.singleShot(200, self._schedule_initialization)

    def _schedule_initialization(self) -> None:
        """Schedule the initialization with either thread manager or direct call."""
        if self._thread_manager:
            self._thread_manager.submit_task(
                func=self.initialize_dropdowns_async,
                name='autocare_query_initialize_dropdowns',
                submitter='autocarequery',
                priority=10
            )
        else:
            # Use direct execution with QTimer to keep UI responsive
            QTimer.singleShot(10, lambda: self._run_initialization_with_timer())

    def _run_initialization_with_timer(self) -> None:
        """Run initialization with a timer to keep UI responsive."""
        try:
            # Create and run event loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run the initialization
            loop.run_until_complete(self.initialize_dropdowns_async())
            loop.close()
        except Exception as e:
            self._logger.error(f"Error in initialization: {str(e)}", exc_info=True)
            self.status_bar.showMessage(f'Initialization error: {str(e)}')

    def run_async_task(self, coro_func: Callable, *args: Any, **kwargs: Any) -> str:
        """
        Run an async coroutine in the ThreadManager’s pool by wrapping it
        in a blocking asyncio.run call. Guarantees all DB work happens
        off the UI thread and in a fresh event loop per task.
        """
        if not self._thread_manager:
            raise RuntimeError("ThreadManager not available – make sure it’s initialized and passed in.")

        task_name = f"autocare_query_{coro_func.__name__}"

        # This wrapper will run your coroutine in a brand-new event loop,
        # entirely inside the worker thread.
        def _run_coro_blocking(*args, **kwargs):
            return asyncio.run(coro_func(*args, **kwargs))

        # Submit to your ThreadManager
        task_id = self._thread_manager.submit_task(
            func=_run_coro_blocking,
            *args,
            name=task_name,
            submitter="autocarequery",
            **kwargs
        )

        # Attach logging callback if you want to know when it’s done
        try:
            info = self._thread_manager.get_task_info(task_id)
            future = self._thread_manager._tasks[task_id].future  # direct access just to attach callback
            future.add_done_callback(self.async_task_done)
        except Exception:
            # swallow if anything’s missing
            pass

        return task_id

    def async_task_done(self, future: Any) -> None:
        """
        Handle async task completion.

        Args:
            future: Completed future object
        """
        try:
            # Get the result to check for exceptions
            result = None
            if hasattr(future, 'result'):
                result = future.result()

            # Additional logging
            self._logger.debug(f"Async task completed successfully")
            return result
        except asyncio.CancelledError:
            self._logger.info("Async task was cancelled")
        except Exception as e:
            self._logger.error(f'Error in async task: {str(e)}', exc_info=True)

            # Update UI on the main thread
            # Use QTimer.singleShot to ensure UI updates happen on the main thread
            QTimer.singleShot(0, lambda: self._handle_async_error(str(e)))
        finally:
            # Always reset UI state if needed
            if self.filters_updating:
                # Use QTimer.singleShot to ensure UI updates happen on the main thread
                QTimer.singleShot(0, lambda: self._reset_ui_state())

    def _handle_async_error(self, error_message: str) -> None:
        """Handle async error by updating UI on the main thread."""
        self.status_bar.showMessage(f'Error: {error_message}')
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def _reset_ui_state(self) -> None:
        """Reset UI state after async operations."""
        self.set_dropdowns_enabled(True)
        self.filters_updating = False
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def initialize_dropdowns(self) -> None:
        """Initialize dropdown menus with default 'All' option."""
        for combo in self.all_combo_boxes:
            combo.addItem('All', None)

    async def initialize_dropdowns_async(self) -> None:
        """Asynchronously load dropdown values from the database."""
        try:
            self.show_progress_dialog('Initializing Filters', 'Loading filter values...')
            self.filters_updating = True
            self.set_dropdowns_enabled(False)

            # Load all dropdown values
            await self.load_dropdown_values('year', self.year_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(10)

            await self.load_dropdown_values('make', self.make_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(20)

            await self.load_dropdown_values('model', self.model_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(30)

            await self.load_dropdown_values('submodel', self.submodel_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(40)

            await self.load_dropdown_values('engine_liter', self.engine_liter_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(50)

            await self.load_dropdown_values('engine_cid', self.engine_cid_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(60)

            await self.load_dropdown_values('cylinder_head_type', self.cylinder_head_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(70)

            await self.load_dropdown_values('valves', self.valves_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(75)

            await self.load_dropdown_values('mfr_body_code', self.mfr_body_code_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(80)

            await self.load_dropdown_values('body_num_doors', self.body_num_doors_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(85)

            await self.load_dropdown_values('wheel_base', self.wheel_base_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(90)

            await self.load_dropdown_values('brake_abs', self.brake_abs_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(92)

            await self.load_dropdown_values('steering_system', self.steering_system_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(94)

            await self.load_dropdown_values('transmission_control_type', self.transmission_control_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(96)

            await self.load_dropdown_values('transmission_mfr_code', self.transmission_mfr_code_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(98)

            await self.load_dropdown_values('drive_type', self.drive_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(100)

            self.set_dropdowns_enabled(True)
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            self.filters_updating = False
            self.status_bar.showMessage('All dropdowns initialized')
        except Exception as e:
            self._logger.error('Error initializing dropdowns', error=str(e))
            self.status_bar.showMessage(f'Error initializing dropdowns: {str(e)}')
            self.set_dropdowns_enabled(True)
            self.filters_updating = False
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

    async def load_dropdown_values(self, filter_name: str, combo_box: QComboBox) -> None:
        """
        Load values for a specific dropdown from the database.

        Args:
            filter_name: Name of the filter
            combo_box: Dropdown widget to populate
        """
        try:
            table_column_map = {
                'year': ('year', 'year_id', 'year_id'),
                'make': ('make', 'name', 'make_id'),
                'model': ('model', 'name', 'model_id'),
                'submodel': ('submodel', 'name', 'submodel_id'),
                'engine_liter': ('engine_block', 'liter', 'liter'),
                'engine_cid': ('engine_block', 'cid', 'cid'),
                'cylinder_head_type': ('cylinder_head_type', 'name', 'cylinder_head_type_id'),
                'valves': ('valves', 'valves_per_engine', 'valves_id'),
                'mfr_body_code': ('mfr_body_code', 'code', 'mfr_body_code_id'),
                'body_num_doors': ('body_num_doors', 'num_doors', 'body_num_doors_id'),
                'wheel_base': ('wheel_base', 'wheel_base', 'wheel_base_id'),
                'brake_abs': ('brake_abs', 'name', 'brake_abs_id'),
                'steering_system': ('steering_system', 'name', 'steering_system_id'),
                'transmission_control_type': ('transmission_control_type', 'name', 'transmission_control_type_id'),
                'transmission_mfr_code': ('transmission_mfr_code', 'code', 'transmission_mfr_code_id'),
                'drive_type': ('drive_type', 'name', 'drive_type_id')
            }

            if filter_name not in table_column_map:
                self._logger.error(f'Unknown filter name: {filter_name}')
                return

            table_name, value_column, id_column = table_column_map[filter_name]
            values = await self.db_repo.get_filter_values(table_name, value_column,
                                                          id_column, self.current_filters)

            combo_box.blockSignals(True)
            current_index = combo_box.currentIndex()
            current_data = combo_box.currentData()

            while combo_box.count() > 1:  # Keep the "All" option
                combo_box.removeItem(1)

            # Sort values appropriately - year in descending order, others alphabetically
            if filter_name != 'year':
                values.sort(key=lambda x: str(x[1]).lower())
            else:
                values.sort(key=lambda x: x[0], reverse=True)

            # Add values to combo box
            for id_value, display_value in values:
                if isinstance(display_value, str):
                    display_value = display_value.strip()
                    if not display_value:
                        display_value = '(Empty)'
                combo_box.addItem(str(display_value), id_value)

            # Restore previous selection if possible
            if current_data is not None:
                index = combo_box.findData(current_data)
                if index >= 0:
                    combo_box.setCurrentIndex(index)
                else:
                    combo_box.setCurrentIndex(0)

            combo_box.blockSignals(False)
        except Exception as e:
            self._logger.error(f'Error loading values for {filter_name}', error=str(e))
            self.status_bar.showMessage(f'Error loading values for {filter_name}: {str(e)}')

    def show_progress_dialog(self, title: str, text: str) -> None:
        """
        Show a progress dialog.

        Args:
            title: Dialog title
            text: Dialog message
        """
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        self.progress_dialog = QProgressDialog(text, 'Cancel', 0, 100, self)
        self.progress_dialog.setWindowTitle(title)
        self.progress_dialog.setMinimumDuration(500)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setValue(0)
        self.progress_dialog.canceled.connect(self.on_progress_canceled)
        self.progress_dialog.show()
        QApplication.processEvents()

    def on_progress_canceled(self) -> None:
        """Handle progress dialog cancellation."""
        self._logger.info('Operation canceled by user')
        self.set_dropdowns_enabled(True)
        self.filters_updating = False
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def set_dropdowns_enabled(self, enabled: bool) -> None:
        """
        Enable or disable all dropdown controls.

        Args:
            enabled: Whether to enable or disable controls
        """
        for combo in self.all_combo_boxes:
            combo.setEnabled(enabled)

        # Handle year range controls separately
        for control in self.year_range_controls:
            if not (control == self.year_range_start or control == self.year_range_end) or (
                    self.year_range_checkbox.isChecked() and enabled):
                control.setEnabled(enabled)

        if not self.year_range_checkbox.isChecked():
            self.year_range_start.setEnabled(False)
            self.year_range_end.setEnabled(False)

        self.execute_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)

    def on_year_range_toggle(self, state: int) -> None:
        """
        Handle year range checkbox toggle.

        Args:
            state: Checkbox state
        """
        if self.filters_updating:
            return

        is_checked = state == Qt.CheckState.Checked.value
        self.current_filters.use_year_range = is_checked
        self.year_combo.setEnabled(not is_checked)
        self.year_range_start.setEnabled(is_checked)
        self.year_range_end.setEnabled(is_checked)

        if is_checked:
            # If a year was selected, use it as starting point for the range
            if self.current_filters.year_id is not None:
                year_val = self.current_filters.year_id
                self.year_range_start.setValue(year_val - 5)
                self.year_range_end.setValue(year_val + 5)

            self.current_filters.year_id = None
            self.current_filters.year_range_start = self.year_range_start.value()
            self.current_filters.year_range_end = self.year_range_end.value()
        else:
            self.current_filters.year_range_start = None
            self.current_filters.year_range_end = None

        self.run_async_task(self.update_all_dropdowns_async)
        self._logger.debug(f'Year range toggled: {is_checked}')

    def on_year_range_changed(self) -> None:
        """Handle year range value changes."""
        if self.filters_updating:
            return

        # Ensure end is not less than start
        if self.year_range_end.value() < self.year_range_start.value():
            self.year_range_end.setValue(self.year_range_start.value())

        self.current_filters.year_range_start = self.year_range_start.value()
        self.current_filters.year_range_end = self.year_range_end.value()

        self.run_async_task(self.update_all_dropdowns_async)
        self._logger.debug(f'Year range changed: {self.year_range_start.value()} - {self.year_range_end.value()}')

    def on_limit_changed(self, state: int) -> None:
        """
        Handle results limit checkbox toggle.

        Args:
            state: Checkbox state
        """
        self.limit_enabled = state == Qt.CheckState.Checked.value
        self.limit_spinbox.setEnabled(self.limit_enabled)

    def on_limit_value_changed(self, value: int) -> None:
        """
        Handle results limit value change.

        Args:
            value: New limit value
        """
        self.result_limit = value

    def _get_filter_mapping(self) -> dict[str, tuple[QComboBox, str]]:
        """
        Returns a map of filter names to (combo_box, FilterDTO attribute).
        Centralizes the mapping so it’s easy to extend or adjust.
        """
        return {
            'year': (self.year_combo, 'year_id'),
            'make': (self.make_combo, 'make_id'),
            'model': (self.model_combo, 'model_id'),
            'submodel': (self.submodel_combo, 'submodel_id'),
            'engine_liter': (self.engine_liter_combo, 'engine_liter'),
            'engine_cid': (self.engine_cid_combo, 'engine_cid'),
            'cylinder_head_type': (self.cylinder_head_type_combo, 'cylinder_head_type_id'),
            'valves': (self.valves_combo, 'valves_id'),
            'mfr_body_code': (self.mfr_body_code_combo, 'mfr_body_code_id'),
            'body_num_doors': (self.body_num_doors_combo, 'body_num_doors_id'),
            'wheel_base': (self.wheel_base_combo, 'wheel_base_id'),
            'brake_abs': (self.brake_abs_combo, 'brake_abs_id'),
            'steering_system': (self.steering_system_combo, 'steering_system_id'),
            'transmission_control_type': (self.transmission_control_type_combo, 'transmission_control_type_id'),
            'transmission_mfr_code': (self.transmission_mfr_code_combo, 'transmission_mfr_code_id'),
            'drive_type': (self.drive_type_combo, 'drive_type_id'),
        }

    def on_filter_changed(self, filter_name: str) -> None:
        """Handle any filter dropdown changing, using a centralized lookup."""
        if self.filters_updating:
            return

        mapping = self._get_filter_mapping()
        entry = mapping.get(filter_name)
        if not entry:
            self._logger.error(f'Unknown filter name: {filter_name}')
            return

        combo_box, filter_attr = entry
        setattr(self.current_filters, filter_attr, combo_box.currentData())

        # special case: if selecting a single year, clear any active range
        if filter_name == 'year' and not self.current_filters.use_year_range:
            self.current_filters.year_range_start = None
            self.current_filters.year_range_end = None

        # trigger async reload of all filters
        self.filters_updating = True
        self.set_dropdowns_enabled(False)
        self.status_bar.showMessage(f'Updating filters for {filter_name}...')
        self._logger.debug(f'Filter changed: {filter_name}={combo_box.currentData()}')

        self.run_async_task(self.update_all_dropdowns_async)

    async def update_all_dropdowns_async(self) -> None:
        """Asynchronously update all dropdown values based on current filters."""
        try:
            self.filters_updating = True
            self.show_progress_dialog('Updating Filters', 'Updating filter values...')
            self.set_dropdowns_enabled(False)
            self.status_bar.showMessage('Updating filters...')

            # Update all dropdown values
            await self.load_dropdown_values('year', self.year_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(10)

            await self.load_dropdown_values('make', self.make_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(20)

            await self.load_dropdown_values('model', self.model_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(30)

            await self.load_dropdown_values('submodel', self.submodel_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(40)

            await self.load_dropdown_values('engine_liter', self.engine_liter_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(50)

            await self.load_dropdown_values('engine_cid', self.engine_cid_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(60)

            await self.load_dropdown_values('cylinder_head_type', self.cylinder_head_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(70)

            await self.load_dropdown_values('valves', self.valves_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(75)

            await self.load_dropdown_values('mfr_body_code', self.mfr_body_code_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(80)

            await self.load_dropdown_values('body_num_doors', self.body_num_doors_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(85)

            await self.load_dropdown_values('wheel_base', self.wheel_base_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(90)

            await self.load_dropdown_values('brake_abs', self.brake_abs_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(92)

            await self.load_dropdown_values('steering_system', self.steering_system_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(94)

            await self.load_dropdown_values('transmission_control_type', self.transmission_control_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(96)

            await self.load_dropdown_values('transmission_mfr_code', self.transmission_mfr_code_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(98)

            await self.load_dropdown_values('drive_type', self.drive_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(100)

            self.set_dropdowns_enabled(True)
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            self.filters_updating = False
            self.status_bar.showMessage('Filters updated')
        except Exception as e:
            self._logger.error('Error updating dropdowns', error=str(e))
            self.status_bar.showMessage(f'Error updating dropdowns: {str(e)}')
            self.set_dropdowns_enabled(True)
            self.filters_updating = False
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

    def execute_query(self) -> None:
        """Execute the vehicle query with current filters."""
        self.execute_button.setEnabled(False)
        self.status_bar.showMessage('Executing query...')
        self.show_progress_dialog('Executing Query', 'Searching for vehicles...')
        self.run_async_task(self.async_execute_query)

    async def async_execute_query(self) -> None:
        """Asynchronously execute the vehicle query."""
        try:
            limit = self.result_limit if self.limit_enabled else MAX_QUERY_LIMIT

            # Execute the query
            results = await self.db_repo.execute_vehicle_query(self.current_filters, limit)

            if self.progress_dialog:
                self.progress_dialog.setValue(80)
                self.progress_dialog.setLabelText('Processing results...')

            # Convert results to dict format for the table model
            data = [result.model_dump() for result in results]

            if self.progress_dialog:
                self.progress_dialog.setValue(90)
                self.progress_dialog.setLabelText('Updating display...')

            # Update the table model with results
            self.table_model.setData(data)

            # Update button states
            self.export_button.setEnabled(len(data) > 0)
            self.copy_button.setEnabled(len(data) > 0)

            if self.progress_dialog:
                self.progress_dialog.setValue(100)

            # Update status
            self.status_bar.showMessage(f'Query executed successfully. {len(data)} results found.')
            self.status_label.setText(f'{len(data)} results')

            self._logger.info(f'Query executed with {len(data)} results')

            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
        except Exception as e:
            self._logger.error('Error executing query', error=str(e))
            self.status_bar.showMessage(f'Error executing query: {str(e)}')

            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            QMessageBox.critical(
                self,
                'Query Error',
                f'An error occurred while executing the query:\n\n{str(e)}',
                QMessageBox.StandardButton.Ok
            )
        finally:
            self.execute_button.setEnabled(True)

    def reset_filters(self) -> None:
        """Reset all filters to default state."""
        self.current_filters = FilterDTO()
        self.show_progress_dialog('Resetting Filters', 'Resetting all filters...')
        self.filters_updating = True
        self.set_dropdowns_enabled(False)

        # Reset all combo boxes to first item (All)
        for combo in self.all_combo_boxes:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

        # Reset year range controls
        self.year_range_checkbox.blockSignals(True)
        self.year_range_checkbox.setChecked(False)
        self.year_range_checkbox.blockSignals(False)

        self.year_range_start.blockSignals(True)
        self.year_range_start.setValue(2010)
        self.year_range_start.setEnabled(False)
        self.year_range_start.blockSignals(False)

        self.year_range_end.blockSignals(True)
        self.year_range_end.setValue(2025)
        self.year_range_end.setEnabled(False)
        self.year_range_end.blockSignals(False)

        self.run_async_task(self.reset_filters_async)

    async def reset_filters_async(self) -> None:
        """Asynchronously reset all filters and reload dropdowns."""
        try:
            # Reload all dropdown values
            await self.load_dropdown_values('year', self.year_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(10)

            await self.load_dropdown_values('make', self.make_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(20)

            await self.load_dropdown_values('model', self.model_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(30)

            await self.load_dropdown_values('submodel', self.submodel_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(40)

            await self.load_dropdown_values('engine_liter', self.engine_liter_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(50)

            await self.load_dropdown_values('engine_cid', self.engine_cid_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(60)

            await self.load_dropdown_values('cylinder_head_type', self.cylinder_head_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(70)

            await self.load_dropdown_values('valves', self.valves_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(75)

            await self.load_dropdown_values('mfr_body_code', self.mfr_body_code_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(80)

            await self.load_dropdown_values('body_num_doors', self.body_num_doors_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(85)

            await self.load_dropdown_values('wheel_base', self.wheel_base_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(90)

            await self.load_dropdown_values('brake_abs', self.brake_abs_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(92)

            await self.load_dropdown_values('steering_system', self.steering_system_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(94)

            await self.load_dropdown_values('transmission_control_type', self.transmission_control_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(96)

            await self.load_dropdown_values('transmission_mfr_code', self.transmission_mfr_code_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(98)

            await self.load_dropdown_values('drive_type', self.drive_type_combo)
            if self.progress_dialog:
                self.progress_dialog.setValue(100)

            self.set_dropdowns_enabled(True)
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            self.filters_updating = False

            # Clear results table
            self.table_model.setData([])
            self.export_button.setEnabled(False)
            self.copy_button.setEnabled(False)
            self.status_label.setText('')

            self.status_bar.showMessage('Filters reset')
            self._logger.info('Filters reset')
        except Exception as e:
            self._logger.error('Error resetting filters', error=str(e))
            self.status_bar.showMessage(f'Error resetting filters: {str(e)}')
            self.set_dropdowns_enabled(True)
            self.filters_updating = False
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

    def export_to_excel(self) -> None:
        """Export query results to Excel."""
        try:
            data = self._get_table_data()
            if not data:
                self.status_bar.showMessage('No data to export')
                return

            self.show_progress_dialog('Exporting Data', 'Preparing data for export...')
            if self.progress_dialog:
                self.progress_dialog.setValue(10)

            # Convert to pandas DataFrame
            df = pd.DataFrame(data)
            if self.progress_dialog:
                self.progress_dialog.setValue(30)

            # Get file path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                'Export to Excel',
                '',
                'Excel Files (*.xlsx);;All Files (*)'
            )

            if not file_path:
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                return

            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'

            if self.progress_dialog:
                self.progress_dialog.setValue(50)
                self.progress_dialog.setLabelText(f'Exporting to {file_path}...')

            # Write to Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Vehicle Data')

                # Adjust column widths
                worksheet = writer.sheets['Vehicle Data']
                for i, column in enumerate(df.columns):
                    max_len = max(
                        df[column].astype(str).map(len).max(),
                        len(str(column))
                    ) + 2
                    worksheet.column_dimensions[chr(65 + i)].width = min(max_len, 50)

            if self.progress_dialog:
                self.progress_dialog.setValue(100)

            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            self.status_bar.showMessage(f'Data exported to {file_path}')
            self._logger.info(f'Data exported to {file_path}')
        except Exception as e:
            self._logger.error('Error exporting to Excel', error=str(e))
            self.status_bar.showMessage(f'Error exporting to Excel: {str(e)}')

            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            QMessageBox.critical(
                self,
                'Export Error',
                f'An error occurred while exporting to Excel:\n\n{str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def copy_selection(self) -> None:
        """Copy selected cells to clipboard."""
        selection = self.results_table.selectionModel().selection()
        if not selection:
            return

        try:
            # Get all selected indexes
            indexes = []
            for selection_range in selection:
                top_left = selection_range.topLeft()
                bottom_right = selection_range.bottomRight()

                for row in range(top_left.row(), bottom_right.row() + 1):
                    for column in range(top_left.column(), bottom_right.column() + 1):
                        indexes.append(self.results_table.model().index(row, column))

            if not indexes:
                return

            # Sort indexes by row and column
            indexes.sort(key=lambda idx: (idx.row(), idx.column()))

            # Group indexes by row
            rows = {}
            for idx in indexes:
                if idx.row() not in rows:
                    rows[idx.row()] = []
                rows[idx.row()].append(idx)

            # Write to CSV string
            output = io.StringIO()
            writer = csv.writer(output, delimiter='\t', lineterminator='\n')

            for row in sorted(rows.keys()):
                values = []
                for idx in sorted(rows[row], key=lambda idx: idx.column()):
                    values.append(str(self.results_table.model().data(idx, Qt.ItemDataRole.DisplayRole) or ''))
                writer.writerow(values)

            # Copy to clipboard
            QApplication.clipboard().setText(output.getvalue())
            self.status_bar.showMessage(f'Selection copied to clipboard')
            self._logger.debug('Selection copied to clipboard')
        except Exception as e:
            self._logger.error('Error copying selection', error=str(e))
            self.status_bar.showMessage(f'Error copying selection: {str(e)}')

    def copy_row(self) -> None:
        """Copy entire row(s) to clipboard."""
        selection = self.results_table.selectionModel().selection()
        if not selection:
            return

        try:
            # Get selected rows
            selected_rows = set()
            for selection_range in selection:
                for row in range(selection_range.top(), selection_range.bottom() + 1):
                    selected_rows.add(row)

            if not selected_rows:
                return

            model = self.results_table.model()
            if not model:
                return

            # Write to CSV string
            output = io.StringIO()
            writer = csv.writer(output, delimiter='\t', lineterminator='\n')

            # Write headers
            headers = [
                model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
                for col in range(model.columnCount())
            ]
            writer.writerow(headers)

            # Write row values
            for row in sorted(selected_rows):
                values = [
                    str(model.data(model.index(row, col), Qt.ItemDataRole.DisplayRole) or '')
                    for col in range(model.columnCount())
                ]
                writer.writerow(values)

            # Copy to clipboard
            QApplication.clipboard().setText(output.getvalue())
            self.status_bar.showMessage(f'Row(s) copied to clipboard')
        except Exception as e:
            self._logger.error('Error copying row', error=str(e))
            self.status_bar.showMessage(f'Error copying row: {str(e)}')

    def show_context_menu(self, position: QPoint) -> None:
        """
        Show context menu for results table.

        Args:
            position: Position to show the menu
        """
        if self.results_table.model().rowCount() == 0:
            return

        context_menu = QMenu(self)

        copy_action = QAction('Copy Selected', self)
        copy_action.triggered.connect(self.copy_selection)
        context_menu.addAction(copy_action)

        copy_row_action = QAction('Copy Entire Row', self)
        copy_row_action.triggered.connect(self.copy_row)
        context_menu.addAction(copy_row_action)

        export_action = QAction('Export to Excel', self)
        export_action.triggered.connect(self.export_to_excel)
        context_menu.addAction(export_action)

        context_menu.exec(self.results_table.mapToGlobal(position))

    def _get_table_data(self) -> List[Dict[str, Any]]:
        """
        Get all data from the table model.

        Returns:
            List of dictionaries containing row data
        """
        model = self.results_table.model()
        if not model:
            return []

        data = []
        for row in range(model.rowCount()):
            row_data = {}
            for column in range(model.columnCount()):
                header = model._headers[column]
                value = model.data(model.index(row, column), Qt.ItemDataRole.DisplayRole)
                row_data[header] = value
            data.append(row_data)

        return data

    def update_connection_string(self, connection_string: str) -> None:
        """
        Update the database connection string.

        Args:
            connection_string: New connection string
        """
        try:
            # Update repository with new connection string
            self.connection_string = connection_string
            self.db_repo = DatabaseRepository(connection_string)

            # Reset filters to reload with new connection
            self.reset_filters()

            self.status_bar.showMessage('Database connection updated')
            self._logger.info('Database connection updated')
        except Exception as e:
            self._logger.error('Error updating connection string', error=str(e))
            self.status_bar.showMessage(f'Error updating connection string: {str(e)}')
            QMessageBox.critical(
                self,
                'Connection Error',
                f'An error occurred while updating the connection:\n\n{str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def refresh_database_connection(self) -> None:
        """Refresh the database connection."""
        try:
            # Get current connection string from config
            connection_string = self._config.get(
                f'plugins.autocarequery.connection_string',
                self.connection_string
            )

            # Update repository with connection string
            self.connection_string = connection_string
            self.db_repo = DatabaseRepository(connection_string)

            # Test connection
            self.run_async_task(self._test_connection)
        except Exception as e:
            self._logger.error('Error refreshing connection', error=str(e))
            self.status_bar.showMessage(f'Error refreshing connection: {str(e)}')
            QMessageBox.critical(
                self,
                'Connection Error',
                f'An error occurred while refreshing the connection:\n\n{str(e)}',
                QMessageBox.StandardButton.Ok
            )

    async def _test_connection(self) -> None:
        """Test the database connection."""
        try:
            success = await self.db_repo.test_connection()
            if success:
                self.status_bar.showMessage('Database connection successful')
                self._logger.info('Database connection test successful')
                QMessageBox.information(
                    self,
                    'Connection Test',
                    'Database connection successful.',
                    QMessageBox.StandardButton.Ok
                )
            else:
                self.status_bar.showMessage('Database connection failed')
                self._logger.error('Database connection test failed')
                QMessageBox.critical(
                    self,
                    'Connection Test',
                    'Database connection failed.',
                    QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            self._logger.error('Error testing connection', error=str(e))
            self.status_bar.showMessage(f'Error testing connection: {str(e)}')
            QMessageBox.critical(
                self,
                'Connection Test',
                f'An error occurred while testing the connection:\n\n{str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def show_connection_settings(self) -> None:
        """Show dialog to edit connection settings."""
        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle('Database Connection Settings')
        layout = QFormLayout(dialog)

        # Get current connection string
        current_conn_str = self._config.get(
            f'plugins.autocarequery.connection_string',
            self.connection_string
        )

        # Create connection string input
        conn_str_input = QLineEdit(current_conn_str)
        conn_str_input.setMinimumWidth(400)
        layout.addRow('Connection String:', conn_str_input)

        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        # Show dialog and handle result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_conn_str = conn_str_input.text().strip()
            if new_conn_str and new_conn_str != current_conn_str:
                # Save to config
                self._config.set(f'plugins.autocarequery.connection_string', new_conn_str)

                # Update connection
                self.update_connection_string(new_conn_str)

    def export_default_queries(self) -> None:
        """Export some default queries to files."""
        self.run_async_task(self._export_default_queries_async)

    async def _export_default_queries_async(self) -> None:
        """Asynchronously export default queries to files."""
        try:
            # Create dialog to get save directory
            save_dir = QFileDialog.getExistingDirectory(
                self,
                'Select Directory for Exported Queries',
                ''
            )

            if not save_dir:
                return

            # Define some default queries
            default_queries = [
                {
                    'name': 'all_toyota_2020',
                    'description': 'All 2020 Toyota vehicles',
                    'filters': FilterDTO(year_id=2020, make_id=1)  # Assuming Toyota is make_id=1
                },
                {
                    'name': 'honda_accords_2018_2022',
                    'description': 'Honda Accords 2018-2022',
                    'filters': FilterDTO(
                        use_year_range=True,
                        year_range_start=2018,
                        year_range_end=2022,
                        make_id=2,  # Assuming Honda is make_id=2
                        model_id=10  # Assuming Accord is model_id=10
                    )
                }
            ]

            # Show progress dialog
            self.show_progress_dialog('Exporting Queries', 'Exporting default queries...')
            self.progress_dialog.setValue(10)

            # Execute and export each query
            for i, query_def in enumerate(default_queries):
                try:
                    # Execute query
                    results = await self.db_repo.execute_vehicle_query(
                        query_def['filters'],
                        limit=1000
                    )

                    # Convert to DataFrame
                    data = [result.model_dump() for result in results]
                    df = pd.DataFrame(data)

                    # Save to Excel
                    file_path = os.path.join(save_dir, f"{query_def['name']}.xlsx")
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Vehicle Data')

                        # Add description sheet
                        description_df = pd.DataFrame([
                            {'Key': 'Name', 'Value': query_def['name']},
                            {'Key': 'Description', 'Value': query_def['description']},
                            {'Key': 'Date Created', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                            {'Key': 'Result Count', 'Value': len(data)}
                        ])
                        description_df.to_excel(writer, index=False, sheet_name='Query Info')

                        # Adjust column widths
                        for sheet_name in writer.sheets:
                            worksheet = writer.sheets[sheet_name]
                            for idx, col in enumerate(worksheet.columns):
                                max_len = 0
                                column = col[0].column_letter
                                for cell in col:
                                    try:
                                        if cell.value:
                                            max_len = max(max_len, len(str(cell.value)))
                                    except:
                                        pass
                                adjusted_width = (max_len + 2) * 1.2
                                worksheet.column_dimensions[column].width = min(adjusted_width, 50)

                    self.progress_dialog.setValue(10 + (85 * (i + 1) // len(default_queries)))
                    self._logger.info(f'Exported query {query_def["name"]} to {file_path}')
                except Exception as e:
                    self._logger.error(f'Error exporting query {query_def["name"]}', error=str(e))

            self.progress_dialog.setValue(100)

            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            self.status_bar.showMessage(f'Default queries exported to {save_dir}')
            QMessageBox.information(
                self,
                'Export Complete',
                f'Default queries have been exported to:\n{save_dir}',
                QMessageBox.StandardButton.Ok
            )
        except Exception as e:
            self._logger.error('Error exporting default queries', error=str(e))
            self.status_bar.showMessage(f'Error exporting default queries: {str(e)}')

            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            QMessageBox.critical(
                self,
                'Export Error',
                f'An error occurred while exporting default queries:\n\n{str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Close any open progress dialog
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            # Clean up sync engine connection immediately
            if hasattr(self, 'db_repo') and self.db_repo:
                if hasattr(self.db_repo, 'sync_engine') and self.db_repo.sync_engine:
                    self.db_repo.sync_engine.dispose()

                # Run async cleanup in background for async engine
                if hasattr(self.db_repo, 'engine') and self.db_repo.engine:
                    # Use run_async_task for async engine disposal
                    # This will create a task but not block shutdown
                    if self._thread_manager:
                        self._thread_manager.submit_task(
                            func=self._dispose_async_engine,
                            name='dispose_async_engine',
                            submitter='autocarequery'
                        )
                    # If no thread manager, we can't properly await this
                    # Just log a warning
                    else:
                        self._logger.warning('Thread manager not available, async engine may not be properly disposed')

            self._logger.info('AutocareQueryTab resources cleaned up')
        except Exception as e:
            self._logger.error('Error cleaning up resources', error=str(e))

    async def _dispose_async_engine(self) -> None:
        """Properly dispose the async engine."""
        try:
            if hasattr(self, 'db_repo') and self.db_repo:
                if hasattr(self.db_repo, 'engine') and self.db_repo.engine:
                    await self.db_repo.engine.dispose()
                    self._logger.debug('Async engine disposed properly')
        except Exception as e:
            self._logger.error(f'Error disposing async engine: {str(e)}')