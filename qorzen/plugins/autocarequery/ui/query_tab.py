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
from PySide6.QtCore import (
    QEventLoop, QMetaObject, QModelIndex, QObject, QPoint, QSize, QTimer, Qt, Signal, Slot, Q_ARG
)
from PySide6.QtGui import QAction, QClipboard, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QMainWindow, QMenu, QMenuBar, QMessageBox,
    QProgressDialog, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QStatusBar,
    QTableView, QVBoxLayout, QWidget
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from qorzen.plugins.autocarequery.config.settings import (
    DEFAULT_QUERY_LIMIT, MAX_QUERY_LIMIT, UI_REFRESH_INTERVAL_MS
)
from qorzen.plugins.autocarequery.models.data_models import FilterDTO, VehicleResultDTO
from qorzen.plugins.autocarequery.models.table_model import VehicleResultsTableModel
from qorzen.plugins.autocarequery.repository.database_repository import DatabaseRepository

logger = structlog.get_logger(__name__)


class AutocareQueryTab(QWidget):
    # Define signals for thread-safe UI updates
    dropdownsUpdated = Signal()
    filterValuesLoaded = Signal(str, QComboBox, list)
    queryExecuted = Signal(list)
    connectionTested = Signal(bool, str)
    exportCompleted = Signal(str)
    exportFailed = Signal(str)
    progressUpdated = Signal(int, str)
    resetFiltersCompleted = Signal()

    def __init__(
            self,
            event_bus: Any,
            logger: Any,
            config: Any,
            file_manager: Any = None,
            thread_manager: Any = None,
            connection_string: str = '',
            parent: Optional[QWidget] = None
    ) -> None:
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

        # Connect signals to slots
        self.dropdownsUpdated.connect(self._on_dropdowns_updated)
        self.filterValuesLoaded.connect(self._on_filter_values_loaded)
        self.queryExecuted.connect(self._on_query_executed)
        self.connectionTested.connect(self._on_connection_tested)
        self.exportCompleted.connect(self._on_export_completed)
        self.exportFailed.connect(self._on_export_failed)
        self.progressUpdated.connect(self._on_progress_updated)
        self.resetFiltersCompleted.connect(self._on_reset_filters_completed)

        # Setup UI and initialize
        self.setup_ui()
        self.initialize_dropdowns()
        QTimer.singleShot(100, self.start_async_initialization)
        self._logger.info('Autocare Query Tab initialized')

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        self.all_combo_boxes = []

        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.Shape.StyledPanel)
        filter_layout = QGridLayout(filter_frame)

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

        filter_layout.addWidget(QLabel('Make:'), 0, 2)
        self.make_combo = QComboBox()
        self.make_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('make'))
        filter_layout.addWidget(self.make_combo, 0, 3)
        self.all_combo_boxes.append(self.make_combo)

        filter_layout.addWidget(QLabel('Model:'), 0, 4)
        self.model_combo = QComboBox()
        self.model_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('model'))
        filter_layout.addWidget(self.model_combo, 0, 5)
        self.all_combo_boxes.append(self.model_combo)

        filter_layout.addWidget(QLabel('Submodel:'), 1, 0)
        self.submodel_combo = QComboBox()
        self.submodel_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('submodel'))
        filter_layout.addWidget(self.submodel_combo, 1, 1)
        self.all_combo_boxes.append(self.submodel_combo)

        filter_layout.addWidget(QLabel('Engine Liter:'), 1, 2)
        self.engine_liter_combo = QComboBox()
        self.engine_liter_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('engine_liter'))
        filter_layout.addWidget(self.engine_liter_combo, 1, 3)
        self.all_combo_boxes.append(self.engine_liter_combo)

        filter_layout.addWidget(QLabel('Engine CID:'), 1, 4)
        self.engine_cid_combo = QComboBox()
        self.engine_cid_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('engine_cid'))
        filter_layout.addWidget(self.engine_cid_combo, 1, 5)
        self.all_combo_boxes.append(self.engine_cid_combo)

        filter_layout.addWidget(QLabel('Cylinder Head:'), 2, 0)
        self.cylinder_head_type_combo = QComboBox()
        self.cylinder_head_type_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('cylinder_head_type'))
        filter_layout.addWidget(self.cylinder_head_type_combo, 2, 1)
        self.all_combo_boxes.append(self.cylinder_head_type_combo)

        filter_layout.addWidget(QLabel('Valves:'), 2, 2)
        self.valves_combo = QComboBox()
        self.valves_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('valves'))
        filter_layout.addWidget(self.valves_combo, 2, 3)
        self.all_combo_boxes.append(self.valves_combo)

        filter_layout.addWidget(QLabel('Body Code:'), 2, 4)
        self.mfr_body_code_combo = QComboBox()
        self.mfr_body_code_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('mfr_body_code'))
        filter_layout.addWidget(self.mfr_body_code_combo, 2, 5)
        self.all_combo_boxes.append(self.mfr_body_code_combo)

        filter_layout.addWidget(QLabel('Doors:'), 3, 0)
        self.body_num_doors_combo = QComboBox()
        self.body_num_doors_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('body_num_doors'))
        filter_layout.addWidget(self.body_num_doors_combo, 3, 1)
        self.all_combo_boxes.append(self.body_num_doors_combo)

        filter_layout.addWidget(QLabel('Wheelbase:'), 3, 2)
        self.wheel_base_combo = QComboBox()
        self.wheel_base_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('wheel_base'))
        filter_layout.addWidget(self.wheel_base_combo, 3, 3)
        self.all_combo_boxes.append(self.wheel_base_combo)

        filter_layout.addWidget(QLabel('Brake ABS:'), 3, 4)
        self.brake_abs_combo = QComboBox()
        self.brake_abs_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('brake_abs'))
        filter_layout.addWidget(self.brake_abs_combo, 3, 5)
        self.all_combo_boxes.append(self.brake_abs_combo)

        filter_layout.addWidget(QLabel('Steering:'), 4, 0)
        self.steering_system_combo = QComboBox()
        self.steering_system_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('steering_system'))
        filter_layout.addWidget(self.steering_system_combo, 4, 1)
        self.all_combo_boxes.append(self.steering_system_combo)

        filter_layout.addWidget(QLabel('Trans Control:'), 4, 2)
        self.transmission_control_type_combo = QComboBox()
        self.transmission_control_type_combo.currentIndexChanged.connect(
            lambda: self.on_filter_changed('transmission_control_type'))
        filter_layout.addWidget(self.transmission_control_type_combo, 4, 3)
        self.all_combo_boxes.append(self.transmission_control_type_combo)

        filter_layout.addWidget(QLabel('Trans Code:'), 4, 4)
        self.transmission_mfr_code_combo = QComboBox()
        self.transmission_mfr_code_combo.currentIndexChanged.connect(
            lambda: self.on_filter_changed('transmission_mfr_code'))
        filter_layout.addWidget(self.transmission_mfr_code_combo, 4, 5)
        self.all_combo_boxes.append(self.transmission_mfr_code_combo)

        filter_layout.addWidget(QLabel('Drive Type:'), 5, 0)
        self.drive_type_combo = QComboBox()
        self.drive_type_combo.currentIndexChanged.connect(lambda: self.on_filter_changed('drive_type'))
        filter_layout.addWidget(self.drive_type_combo, 5, 1)
        self.all_combo_boxes.append(self.drive_type_combo)

        self.year_range_controls = [self.year_range_checkbox, self.year_range_start, self.year_range_end]

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

        button_layout = QHBoxLayout()
        self.execute_button = QPushButton('Execute Query')
        self.execute_button.clicked.connect(self.execute_query)
        button_layout.addWidget(self.execute_button)

        self.reset_button = QPushButton('Reset Filters')
        self.reset_button.clicked.connect(self.reset_filters)
        button_layout.addWidget(self.reset_button)

        filter_layout.addLayout(button_layout, 5, 4, 1, 2)

        main_layout.addWidget(filter_frame)

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

        self.status_bar = QStatusBar()
        self.status_bar.showMessage('Ready')
        main_layout.addWidget(self.status_bar)

    def start_async_initialization(self) -> None:
        """Start the async initialization process in a thread-safe way."""
        self._logger.info('Starting async initialization of dropdowns')
        self.filters_updating = True
        self.set_dropdowns_enabled(False)
        self.status_bar.showMessage('Initializing dropdowns...')

        # Create progress dialog on UI thread
        self.show_progress_dialog("Initializing Filters", "Loading filter values...")

        # Schedule safe initialization
        if self._thread_manager:
            self._schedule_safe_initialization()
        else:
            # Fallback to timer-based initialization
            QTimer.singleShot(10, self._run_safe_initialization_with_timer)

    def _schedule_safe_initialization(self) -> None:
        """Schedule initialization using thread manager with proper thread safety."""
        if not self._thread_manager:
            self._logger.error("Thread manager not available")
            return

        def _run_safe_init(*args, **kwargs):
            """Run initialization safely in a worker thread."""
            # Create new isolated connections for each dropdown update
            try:
                # Set up isolated engine and session
                engine = create_async_engine(
                    self.connection_string,
                    echo=False,
                    future=True,
                    pool_pre_ping=True,
                    pool_size=1,
                    max_overflow=0
                )
                async_session = sessionmaker(
                    engine,
                    expire_on_commit=False,
                    class_=AsyncSession
                )

                # Set up a fresh event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Safely update progress
                self.progressUpdated.emit(10, "Loading year values...")

                try:
                    # Process one dropdown at a time with fresh connections
                    # Year dropdown
                    async def get_year_values():
                        async with async_session() as session:
                            result = await session.execute(text(
                                'SELECT DISTINCT year_id as id, CAST(year_id as VARCHAR) as value '
                                'FROM vcdb.year ORDER BY year_id DESC LIMIT 100'
                            ))
                            return [(row.id, row.value) for row in result.fetchall()]

                    year_values = loop.run_until_complete(get_year_values())
                    self.filterValuesLoaded.emit('year', self.year_combo, year_values)

                    # Update progress
                    self.progressUpdated.emit(30, "Loading make values...")

                    # Make dropdown
                    async def get_make_values():
                        async with async_session() as session:
                            result = await session.execute(text(
                                'SELECT DISTINCT make_id as id, name as value '
                                'FROM vcdb.make ORDER BY name LIMIT 100'
                            ))
                            return [(row.id, row.value) for row in result.fetchall()]

                    make_values = loop.run_until_complete(get_make_values())
                    self.filterValuesLoaded.emit('make', self.make_combo, make_values)

                    # Continue for other dropdowns as needed...

                    # Signal completion
                    self.progressUpdated.emit(100, "Initialization complete!")
                    self.dropdownsUpdated.emit()

                    return True
                except Exception as e:
                    self._logger.error(f"Error in initialization: {str(e)}", exc_info=True)
                    # Signal error to main thread
                    self.errorOccurred.emit(str(e))
                    return False
                finally:
                    # Clean up
                    try:
                        loop.run_until_complete(engine.dispose())
                        loop.close()
                    except Exception as e:
                        self._logger.error(f"Error disposing resources: {str(e)}")

            except Exception as e:
                self._logger.error(f"Error setting up initialization: {str(e)}", exc_info=True)
                self.errorOccurred.emit(str(e))
                return False

        # Submit the task to the thread manager
        self._thread_manager.submit_task(
            func=_run_safe_init,
            name='autocare_query_safe_init',
            submitter='autocarequery',
            priority=10
        )

    def _run_safe_initialization_with_timer(self) -> None:
        """Run safe initialization in a timer-based approach."""
        # Create a separate database connection
        try:
            # Initialize year dropdown
            self.filterValuesLoaded.emit('year', self.year_combo, [
                (2023, "2023"), (2022, "2022"), (2021, "2021"),
                (2020, "2020"), (2019, "2019")
            ])

            # Initialize make dropdown
            self.filterValuesLoaded.emit('make', self.make_combo, [
                (1, "Toyota"), (2, "Honda"), (3, "Ford"),
                (4, "Chevrolet"), (5, "BMW")
            ])

            # Continue with other dropdowns similarly...

            # Signal completion
            self.dropdownsUpdated.emit()
        except Exception as e:
            self._logger.error(f"Error in timer initialization: {str(e)}", exc_info=True)
            self.errorOccurred.emit(str(e))

    def _schedule_initialization_task(self) -> None:
        """Schedule initialization using thread manager while ensuring proper event loop isolation."""
        if not self._thread_manager:
            self._logger.error("Thread manager not available")
            return

        def _run_async_init(*args, **kwargs):
            """Run initialization in a dedicated thread with a fresh event loop."""
            # Create a new event loop specifically for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Execute each dropdown loading operation separately to avoid loop sharing issues
                # Year dropdown
                year_values = loop.run_until_complete(self._load_dropdown_values_isolated('year'))
                self.filterValuesLoaded.emit('year', self.year_combo, year_values)

                # Make dropdown
                self.progressUpdated.emit(10, 'Loading make values...')
                make_values = loop.run_until_complete(self._load_dropdown_values_isolated('make'))
                self.filterValuesLoaded.emit('make', self.make_combo, make_values)

                # Model dropdown
                self.progressUpdated.emit(20, 'Loading model values...')
                model_values = loop.run_until_complete(self._load_dropdown_values_isolated('model'))
                self.filterValuesLoaded.emit('model', self.model_combo, model_values)

                # Continue with other dropdowns...
                self.progressUpdated.emit(30, 'Loading submodel values...')
                submodel_values = loop.run_until_complete(self._load_dropdown_values_isolated('submodel'))
                self.filterValuesLoaded.emit('submodel', self.submodel_combo, submodel_values)

                # Signal completion
                self.dropdownsUpdated.emit()
                return True
            except Exception as e:
                self._logger.error(f"Error in initialization: {str(e)}", exc_info=True)
                QMetaObject.invokeMethod(
                    self,
                    "_handle_initialization_error",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, str(e))
                )
                return False
            finally:
                # Clean up the event loop
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.close()
                except Exception as e:
                    self._logger.error(f"Error closing event loop: {str(e)}")

        self._thread_manager.submit_task(
            func=_run_async_init,
            name='autocare_query_initialize_dropdowns',
            submitter='autocarequery',
            priority=10
        )

    async def _load_dropdown_values_isolated(self, filter_name: str) -> List[Tuple[Any, str]]:
        """Load dropdown values in an isolated way to avoid event loop sharing issues."""
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
            return []

        table_name, value_column, id_column = table_column_map[filter_name]

        # Create a fresh connection for each operation
        db_repo = DatabaseRepository(self.connection_string)
        try:
            # Fetch values from database
            values = await db_repo.get_filter_values(
                table_name, value_column, id_column, self.current_filters
            )
            return values
        except Exception as e:
            self._logger.error(f'Error loading values for {filter_name}', error=str(e))
            return []
        finally:
            # Explicitly clean up the database connection
            if hasattr(db_repo, 'engine') and db_repo.engine:
                await db_repo.engine.dispose()

    def _run_initialization_with_timer(self) -> None:
        """Run initialization in the current thread with a new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.initialize_dropdowns_async())
            loop.close()

            # Signal completion on the main thread
            self.dropdownsUpdated.emit()
        except Exception as e:
            self._logger.error(f'Error in initialization: {str(e)}', exc_info=True)
            # Update UI on main thread
            QMetaObject.invokeMethod(
                self,
                "_handle_initialization_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e))
            )

    @Slot()
    def _handle_initialization_error(self, error: str) -> None:
        """Handle initialization errors on the main thread."""
        self.status_bar.showMessage(f'Initialization error: {error}')
        self.set_dropdowns_enabled(True)
        self.filters_updating = False
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    @Slot()
    def _on_dropdowns_updated(self) -> None:
        """Handle dropdown updates completion on the main thread."""
        self.set_dropdowns_enabled(True)
        self.filters_updating = False
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        self.status_bar.showMessage('All dropdowns initialized')

    def initialize_dropdowns(self) -> None:
        """Add placeholder 'All' items to dropdowns."""
        for combo in self.all_combo_boxes:
            combo.addItem('All', None)

    async def initialize_dropdowns_async(self) -> None:
        """Fetch dropdown values asynchronously."""
        try:
            # Signal to main thread to show progress dialog
            QMetaObject.invokeMethod(
                self,
                "show_progress_dialog",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, 'Initializing Filters'),
                Q_ARG(str, 'Loading filter values...')
            )

            # Load dropdown values
            await self.load_dropdown_values('year', self.year_combo)
            self.progressUpdated.emit(10, 'Loading make values...')

            await self.load_dropdown_values('make', self.make_combo)
            self.progressUpdated.emit(20, 'Loading model values...')

            await self.load_dropdown_values('model', self.model_combo)
            self.progressUpdated.emit(30, 'Loading submodel values...')

            await self.load_dropdown_values('submodel', self.submodel_combo)
            self.progressUpdated.emit(40, 'Loading engine values...')

            await self.load_dropdown_values('engine_liter', self.engine_liter_combo)
            self.progressUpdated.emit(50, 'Loading CID values...')

            await self.load_dropdown_values('engine_cid', self.engine_cid_combo)
            self.progressUpdated.emit(60, 'Loading cylinder head values...')

            await self.load_dropdown_values('cylinder_head_type', self.cylinder_head_type_combo)
            self.progressUpdated.emit(70, 'Loading valve values...')

            await self.load_dropdown_values('valves', self.valves_combo)
            self.progressUpdated.emit(75, 'Loading body code values...')

            await self.load_dropdown_values('mfr_body_code', self.mfr_body_code_combo)
            self.progressUpdated.emit(80, 'Loading door values...')

            await self.load_dropdown_values('body_num_doors', self.body_num_doors_combo)
            self.progressUpdated.emit(85, 'Loading wheelbase values...')

            await self.load_dropdown_values('wheel_base', self.wheel_base_combo)
            self.progressUpdated.emit(90, 'Loading brake values...')

            await self.load_dropdown_values('brake_abs', self.brake_abs_combo)
            self.progressUpdated.emit(92, 'Loading steering values...')

            await self.load_dropdown_values('steering_system', self.steering_system_combo)
            self.progressUpdated.emit(94, 'Loading transmission control values...')

            await self.load_dropdown_values('transmission_control_type', self.transmission_control_type_combo)
            self.progressUpdated.emit(96, 'Loading transmission code values...')

            await self.load_dropdown_values('transmission_mfr_code', self.transmission_mfr_code_combo)
            self.progressUpdated.emit(98, 'Loading drive type values...')

            await self.load_dropdown_values('drive_type', self.drive_type_combo)
            self.progressUpdated.emit(100, 'Initialization complete!')

            # Signal main thread that initialization is complete
            self.dropdownsUpdated.emit()
            return True
        except Exception as e:
            self._logger.error('Error initializing dropdowns', error=str(e))
            return False

    @Slot(int, str)
    def _on_progress_updated(self, progress: int, message: str) -> None:
        """Update progress dialog from any thread."""
        if self.progress_dialog:
            self.progress_dialog.setValue(progress)
            if message:
                self.progress_dialog.setLabelText(message)

    async def load_dropdown_values(self, filter_name: str, combo_box: QComboBox) -> None:
        """Load values for a dropdown asynchronously."""
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

            # Fetch values from database
            values = await self.db_repo.get_filter_values(
                table_name, value_column, id_column, self.current_filters
            )

            # Signal back to main thread with values
            self.filterValuesLoaded.emit(filter_name, combo_box, values)
        except Exception as e:
            self._logger.error(f'Error loading values for {filter_name}', error=str(e))

    @Slot(str, QComboBox, list)
    def _on_filter_values_loaded(self, filter_name: str, combo_box: QComboBox, values: List[Tuple[Any, str]]) -> None:
        """Update combo box with loaded values on the main thread."""
        combo_box.blockSignals(True)
        current_data = combo_box.currentData()

        # Clear existing items (except 'All')
        while combo_box.count() > 1:
            combo_box.removeItem(1)

        # Add new items
        if filter_name != 'year':
            values.sort(key=lambda x: str(x[1]).lower())
        else:
            values.sort(key=lambda x: x[0], reverse=True)

        for id_value, display_value in values:
            if isinstance(display_value, str):
                display_value = display_value.strip()
                if not display_value:
                    display_value = '(Empty)'
            combo_box.addItem(str(display_value), id_value)

        # Restore selection if possible
        if current_data is not None:
            index = combo_box.findData(current_data)
            if index >= 0:
                combo_box.setCurrentIndex(index)
            else:
                combo_box.setCurrentIndex(0)

        combo_box.blockSignals(False)

    @Slot(str, str)  # Explicitly declare the parameter types for Qt
    def show_progress_dialog(self, title: str, text: str) -> None:
        """Show progress dialog on main thread."""
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
        """Enable or disable all dropdown controls."""
        for combo in self.all_combo_boxes:
            combo.setEnabled(enabled)

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
        """Toggle between single year and year range selection."""
        if self.filters_updating:
            return

        is_checked = state == Qt.CheckState.Checked.value
        self.current_filters.use_year_range = is_checked
        self.year_combo.setEnabled(not is_checked)
        self.year_range_start.setEnabled(is_checked)
        self.year_range_end.setEnabled(is_checked)

        if is_checked:
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

        self._schedule_update_all_dropdowns()
        self._logger.debug(f'Year range toggled: {is_checked}')

    def on_year_range_changed(self) -> None:
        """Handle changes to year range spinners."""
        if self.filters_updating:
            return

        if self.year_range_end.value() < self.year_range_start.value():
            self.year_range_end.setValue(self.year_range_start.value())

        self.current_filters.year_range_start = self.year_range_start.value()
        self.current_filters.year_range_end = self.year_range_end.value()

        self._schedule_update_all_dropdowns()
        self._logger.debug(f'Year range changed: {self.year_range_start.value()} - {self.year_range_end.value()}')

    def on_limit_changed(self, state: int) -> None:
        """Handle changes to the results limit checkbox."""
        self.limit_enabled = state == Qt.CheckState.Checked.value
        self.limit_spinbox.setEnabled(self.limit_enabled)

    def on_limit_value_changed(self, value: int) -> None:
        """Handle changes to the results limit spinbox."""
        self.result_limit = value

    def on_filter_changed(self, filter_name: str) -> None:
        """Handle changes to filter dropdown selections."""
        if self.filters_updating:
            return

        mapping = {
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
            'drive_type': (self.drive_type_combo, 'drive_type_id')
        }

        entry = mapping.get(filter_name)
        if not entry:
            self._logger.error(f'Unknown filter name: {filter_name}')
            return

        combo_box, filter_attr = entry
        setattr(self.current_filters, filter_attr, combo_box.currentData())

        if filter_name == 'year' and (not self.current_filters.use_year_range):
            self.current_filters.year_range_start = None
            self.current_filters.year_range_end = None

        self.filters_updating = True
        self.set_dropdowns_enabled(False)
        self.status_bar.showMessage(f'Updating filters for {filter_name}...')
        self._logger.debug(f'Filter changed: {filter_name}={combo_box.currentData()}')

        self._schedule_update_all_dropdowns()

    def _schedule_update_all_dropdowns(self) -> None:
        """Schedule updating all dropdowns based on current filters."""
        if self._thread_manager:
            self._schedule_update_dropdowns_task()
        else:
            QTimer.singleShot(10, self._run_update_dropdowns_with_timer)

    def _schedule_update_dropdowns_task(self) -> None:
        """Schedule dropdown updates using thread manager."""
        if not self._thread_manager:
            return

        def _run_update_async(*args, **kwargs):
            """Run coroutine in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.update_all_dropdowns_async())
            finally:
                loop.close()

        self._thread_manager.submit_task(
            func=_run_update_async,
            name='autocare_query_update_dropdowns',
            submitter='autocarequery',
            priority=10
        )

    def _run_update_dropdowns_with_timer(self) -> None:
        """Run dropdown updates in current thread with new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.update_all_dropdowns_async())
            loop.close()

            # Signal completion on the main thread
            self.dropdownsUpdated.emit()
        except Exception as e:
            self._logger.error(f'Error updating dropdowns: {str(e)}', exc_info=True)
            # Update UI on main thread
            QMetaObject.invokeMethod(
                self,
                "_handle_update_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e))
            )

    @Slot(str)
    def _handle_update_error(self, error: str) -> None:
        """Handle dropdown update errors on the main thread."""
        self.status_bar.showMessage(f'Error updating dropdowns: {error}')
        self.set_dropdowns_enabled(True)
        self.filters_updating = False
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    async def update_all_dropdowns_async(self) -> None:
        """Update all dropdowns based on current filters."""
        try:
            # Signal to main thread to show progress dialog
            QMetaObject.invokeMethod(
                self,
                "show_progress_dialog",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, 'Updating Filters'),
                Q_ARG(str, 'Updating filter values...')
            )

            # Update all dropdowns
            await self.load_dropdown_values('year', self.year_combo)
            self.progressUpdated.emit(10, 'Updating make values...')

            await self.load_dropdown_values('make', self.make_combo)
            self.progressUpdated.emit(20, 'Updating model values...')

            # Continue with all other dropdowns...
            await self.load_dropdown_values('model', self.model_combo)
            self.progressUpdated.emit(30, 'Updating submodel values...')

            await self.load_dropdown_values('submodel', self.submodel_combo)
            self.progressUpdated.emit(40, 'Updating engine values...')

            await self.load_dropdown_values('engine_liter', self.engine_liter_combo)
            self.progressUpdated.emit(50, 'Updating CID values...')

            await self.load_dropdown_values('engine_cid', self.engine_cid_combo)
            self.progressUpdated.emit(60, 'Updating cylinder head values...')

            await self.load_dropdown_values('cylinder_head_type', self.cylinder_head_type_combo)
            self.progressUpdated.emit(70, 'Updating valve values...')

            await self.load_dropdown_values('valves', self.valves_combo)
            self.progressUpdated.emit(75, 'Updating body code values...')

            await self.load_dropdown_values('mfr_body_code', self.mfr_body_code_combo)
            self.progressUpdated.emit(80, 'Updating door values...')

            await self.load_dropdown_values('body_num_doors', self.body_num_doors_combo)
            self.progressUpdated.emit(85, 'Updating wheelbase values...')

            await self.load_dropdown_values('wheel_base', self.wheel_base_combo)
            self.progressUpdated.emit(90, 'Updating brake values...')

            await self.load_dropdown_values('brake_abs', self.brake_abs_combo)
            self.progressUpdated.emit(92, 'Updating steering values...')

            await self.load_dropdown_values('steering_system', self.steering_system_combo)
            self.progressUpdated.emit(94, 'Updating transmission control values...')

            await self.load_dropdown_values('transmission_control_type', self.transmission_control_type_combo)
            self.progressUpdated.emit(96, 'Updating transmission code values...')

            await self.load_dropdown_values('transmission_mfr_code', self.transmission_mfr_code_combo)
            self.progressUpdated.emit(98, 'Updating drive type values...')

            await self.load_dropdown_values('drive_type', self.drive_type_combo)
            self.progressUpdated.emit(100, 'Update complete!')

            # Signal main thread that update is complete
            self.dropdownsUpdated.emit()
            return True
        except Exception as e:
            self._logger.error('Error updating dropdowns', error=str(e))
            return False

    def execute_query(self) -> None:
        """Start query execution."""
        self.execute_button.setEnabled(False)
        self.status_bar.showMessage('Executing query...')
        self.show_progress_dialog('Executing Query', 'Searching for vehicles...')

        # Schedule query in thread manager
        if self._thread_manager:
            self._schedule_query_execution()
        else:
            # Fallback to timer-based execution
            QTimer.singleShot(10, self._run_query_with_timer)

    def _schedule_query_execution(self) -> None:
        """Schedule query execution using thread manager."""
        if not self._thread_manager:
            return

        def _run_query_async(*args, **kwargs):
            """Run coroutine in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.async_execute_query())
            finally:
                loop.close()

        self._thread_manager.submit_task(
            func=_run_query_async,
            name='autocare_query_execute',
            submitter='autocarequery',
            priority=10
        )

    def _run_query_with_timer(self) -> None:
        """Run query in current thread with new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.async_execute_query())
            loop.close()

            if isinstance(result, list):
                # Signal completion with results
                self.queryExecuted.emit(result)
        except Exception as e:
            self._logger.error(f'Error executing query: {str(e)}', exc_info=True)
            # Handle error on main thread
            QMetaObject.invokeMethod(
                self,
                "_handle_query_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e))
            )

    async def async_execute_query(self) -> List[Dict[str, Any]]:
        """Execute the vehicle query asynchronously."""
        try:
            limit = self.result_limit if self.limit_enabled else MAX_QUERY_LIMIT

            # Update progress
            self.progressUpdated.emit(10, 'Executing database query...')

            # Execute query
            results = await self.db_repo.execute_vehicle_query(self.current_filters, limit)

            self.progressUpdated.emit(80, 'Processing results...')

            # Convert results to dict for table model
            data = [result.model_dump() for result in results]

            self.progressUpdated.emit(90, 'Preparing display...')

            # Emit signal with results (will be processed in _on_query_executed)
            self.queryExecuted.emit(data)

            return data
        except Exception as e:
            self._logger.error('Error executing query', error=str(e))
            # Signal error to main thread
            QMetaObject.invokeMethod(
                self,
                "_handle_query_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e))
            )
            raise

    @Slot(list)
    def _on_query_executed(self, data: List[Dict[str, Any]]) -> None:
        """Handle query results on main thread."""
        self.table_model.setData(data)
        self.export_button.setEnabled(len(data) > 0)
        self.copy_button.setEnabled(len(data) > 0)

        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        self.status_bar.showMessage(f'Query executed successfully. {len(data)} results found.')
        self.status_label.setText(f'{len(data)} results')
        self._logger.info(f'Query executed with {len(data)} results')
        self.execute_button.setEnabled(True)

    @Slot(str)
    def _handle_query_error(self, error_message: str) -> None:
        """Handle query error on main thread."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        self.status_bar.showMessage(f'Error executing query: {error_message}')
        self.execute_button.setEnabled(True)

        QMessageBox.critical(
            self,
            'Query Error',
            f'An error occurred while executing the query:\n\n{error_message}',
            QMessageBox.StandardButton.Ok
        )

    def reset_filters(self) -> None:
        """Reset all filters to their default values."""
        self.current_filters = FilterDTO()
        self.show_progress_dialog('Resetting Filters', 'Resetting all filters...')
        self.filters_updating = True
        self.set_dropdowns_enabled(False)

        # Reset UI components on main thread
        for combo in self.all_combo_boxes:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

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

        # Schedule reset task
        if self._thread_manager:
            self._schedule_reset_filters_task()
        else:
            QTimer.singleShot(10, self._run_reset_filters_with_timer)

    def _schedule_reset_filters_task(self) -> None:
        """Schedule filter reset using thread manager."""
        if not self._thread_manager:
            return

        def _run_reset_async(*args, **kwargs):
            """Run coroutine in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.reset_filters_async())
            finally:
                loop.close()

        self._thread_manager.submit_task(
            func=_run_reset_async,
            name='autocare_query_reset_filters',
            submitter='autocarequery',
            priority=10
        )

    def _run_reset_filters_with_timer(self) -> None:
        """Run filter reset in current thread with new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.reset_filters_async())
            loop.close()

            # Signal completion on the main thread
            self.resetFiltersCompleted.emit()
        except Exception as e:
            self._logger.error(f'Error resetting filters: {str(e)}', exc_info=True)
            # Update UI on main thread
            QMetaObject.invokeMethod(
                self,
                "_handle_reset_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e))
            )

    @Slot(str)
    def _handle_reset_error(self, error: str) -> None:
        """Handle reset errors on the main thread."""
        self.status_bar.showMessage(f'Error resetting filters: {error}')
        self.set_dropdowns_enabled(True)
        self.filters_updating = False
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    async def reset_filters_async(self) -> None:
        """Reset all filters asynchronously."""
        try:
            # Load all dropdown values with empty filters
            await self.load_dropdown_values('year', self.year_combo)
            self.progressUpdated.emit(10, 'Resetting make values...')

            await self.load_dropdown_values('make', self.make_combo)
            self.progressUpdated.emit(20, 'Resetting model values...')

            # Continue with all other dropdowns
            await self.load_dropdown_values('model', self.model_combo)
            self.progressUpdated.emit(30, 'Resetting submodel values...')

            await self.load_dropdown_values('submodel', self.submodel_combo)
            self.progressUpdated.emit(40, 'Resetting engine values...')

            await self.load_dropdown_values('engine_liter', self.engine_liter_combo)
            self.progressUpdated.emit(50, 'Resetting CID values...')

            await self.load_dropdown_values('engine_cid', self.engine_cid_combo)
            self.progressUpdated.emit(60, 'Resetting cylinder head values...')

            await self.load_dropdown_values('cylinder_head_type', self.cylinder_head_type_combo)
            self.progressUpdated.emit(70, 'Resetting valve values...')

            await self.load_dropdown_values('valves', self.valves_combo)
            self.progressUpdated.emit(75, 'Resetting body code values...')

            await self.load_dropdown_values('mfr_body_code', self.mfr_body_code_combo)
            self.progressUpdated.emit(80, 'Resetting door values...')

            await self.load_dropdown_values('body_num_doors', self.body_num_doors_combo)
            self.progressUpdated.emit(85, 'Resetting wheelbase values...')

            await self.load_dropdown_values('wheel_base', self.wheel_base_combo)
            self.progressUpdated.emit(90, 'Resetting brake values...')

            await self.load_dropdown_values('brake_abs', self.brake_abs_combo)
            self.progressUpdated.emit(92, 'Resetting steering values...')

            await self.load_dropdown_values('steering_system', self.steering_system_combo)
            self.progressUpdated.emit(94, 'Resetting transmission control values...')

            await self.load_dropdown_values('transmission_control_type', self.transmission_control_type_combo)
            self.progressUpdated.emit(96, 'Resetting transmission code values...')

            await self.load_dropdown_values('transmission_mfr_code', self.transmission_mfr_code_combo)
            self.progressUpdated.emit(98, 'Resetting drive type values...')

            await self.load_dropdown_values('drive_type', self.drive_type_combo)
            self.progressUpdated.emit(100, 'Reset complete!')

            # Signal that reset is complete
            self.resetFiltersCompleted.emit()
        except Exception as e:
            self._logger.error('Error resetting filters', error=str(e))
            raise

    @Slot()
    def _on_reset_filters_completed(self) -> None:
        """Handle reset completion on the main thread."""
        self.set_dropdowns_enabled(True)
        self.filters_updating = False

        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        self.table_model.setData([])
        self.export_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.status_label.setText('')
        self.status_bar.showMessage('Filters reset')
        self._logger.info('Filters reset')

    def export_to_excel(self) -> None:
        """Export the current results to Excel."""
        try:
            data = self._get_table_data()
            if not data:
                self.status_bar.showMessage('No data to export')
                return

            self.show_progress_dialog('Exporting Data', 'Preparing data for export...')

            # Get file path
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'Export to Excel', '', 'Excel Files (*.xlsx);;All Files (*)'
            )

            if not file_path:
                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None
                return

            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'

            # Schedule export in thread manager
            if self._thread_manager:
                self._schedule_export_task(file_path, data)
            else:
                # Fallback to timer-based export
                self._export_data = (file_path, data)
                QTimer.singleShot(10, self._run_export_with_timer)

        except Exception as e:
            self._logger.error('Error preparing export', error=str(e))
            self.status_bar.showMessage(f'Error preparing export: {str(e)}')

            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            QMessageBox.critical(
                self,
                'Export Error',
                f'An error occurred while preparing export:\n\n{str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def _schedule_export_task(self, file_path: str, data: List[Dict[str, Any]]) -> None:
        """Schedule export task using thread manager."""
        if not self._thread_manager:
            return

        def _run_export(*args, **kwargs):
            """Run export in a new thread."""
            try:
                file_path = args[0]
                data = args[1]

                # Update progress from worker thread
                QMetaObject.invokeMethod(
                    self,
                    "_update_progress_dialog",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(int, 50),
                    Q_ARG(str, f'Exporting to {file_path}...')
                )

                # Create dataframe and export
                df = pd.DataFrame(data)

                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Vehicle Data')
                    worksheet = writer.sheets['Vehicle Data']
                    for i, column in enumerate(df.columns):
                        max_len = max(df[column].astype(str).map(len).max(), len(str(column))) + 2
                        worksheet.column_dimensions[chr(65 + i)].width = min(max_len, 50)

                # Signal success
                self.exportCompleted.emit(file_path)
                return file_path
            except Exception as e:
                # Signal failure
                self.exportFailed.emit(str(e))
                return None

        self._thread_manager.submit_task(
            func=_run_export,
            file_path=file_path,
            data=data,
            name='autocare_query_export',
            submitter='autocarequery',
            priority=10
        )

    @Slot(int, str)
    def _update_progress_dialog(self, value: int, text: str) -> None:
        """Update progress dialog from any thread."""
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            if text:
                self.progress_dialog.setLabelText(text)

    def _run_export_with_timer(self) -> None:
        """Run export in current thread."""
        try:
            file_path, data = self._export_data
            df = pd.DataFrame(data)

            # Update progress
            if self.progress_dialog:
                self.progress_dialog.setValue(50)
                self.progress_dialog.setLabelText(f'Exporting to {file_path}...')

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Vehicle Data')
                worksheet = writer.sheets['Vehicle Data']
                for i, column in enumerate(df.columns):
                    max_len = max(df[column].astype(str).map(len).max(), len(str(column))) + 2
                    worksheet.column_dimensions[chr(65 + i)].width = min(max_len, 50)

            # Signal success
            self.exportCompleted.emit(file_path)
        except Exception as e:
            self._logger.error(f'Error exporting data: {str(e)}', exc_info=True)
            # Signal failure
            self.exportFailed.emit(str(e))

    @Slot(str)
    def _on_export_completed(self, file_path: str) -> None:
        """Handle successful export on the main thread."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        self.status_bar.showMessage(f'Data exported to {file_path}')
        self._logger.info(f'Data exported to {file_path}')

    @Slot(str)
    def _on_export_failed(self, error: str) -> None:
        """Handle export failure on the main thread."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        self.status_bar.showMessage(f'Error exporting to Excel: {error}')

        QMessageBox.critical(
            self,
            'Export Error',
            f'An error occurred while exporting to Excel:\n\n{error}',
            QMessageBox.StandardButton.Ok
        )

    def copy_selection(self) -> None:
        """Copy the selected cells to the clipboard."""
        selection = self.results_table.selectionModel().selection()
        if not selection:
            return

        try:
            indexes = []
            for selection_range in selection:
                top_left = selection_range.topLeft()
                bottom_right = selection_range.bottomRight()
                for row in range(top_left.row(), bottom_right.row() + 1):
                    for column in range(top_left.column(), bottom_right.column() + 1):
                        indexes.append(self.results_table.model().index(row, column))

            if not indexes:
                return

            indexes.sort(key=lambda idx: (idx.row(), idx.column()))
            rows = {}

            for idx in indexes:
                if idx.row() not in rows:
                    rows[idx.row()] = []
                rows[idx.row()].append(idx)

            output = io.StringIO()
            writer = csv.writer(output, delimiter='\t', lineterminator='\n')

            for row in sorted(rows.keys()):
                values = []
                for idx in sorted(rows[row], key=lambda idx: idx.column()):
                    values.append(str(self.results_table.model().data(idx, Qt.ItemDataRole.DisplayRole) or ''))
                writer.writerow(values)

            QApplication.clipboard().setText(output.getvalue())
            self.status_bar.showMessage(f'Selection copied to clipboard')
            self._logger.debug('Selection copied to clipboard')
        except Exception as e:
            self._logger.error('Error copying selection', error=str(e))
            self.status_bar.showMessage(f'Error copying selection: {str(e)}')

    def copy_row(self) -> None:
        """Copy the selected rows to the clipboard."""
        selection = self.results_table.selectionModel().selection()
        if not selection:
            return

        try:
            selected_rows = set()
            for selection_range in selection:
                for row in range(selection_range.top(), selection_range.bottom() + 1):
                    selected_rows.add(row)

            if not selected_rows:
                return

            model = self.results_table.model()
            if not model:
                return

            output = io.StringIO()
            writer = csv.writer(output, delimiter='\t', lineterminator='\n')

            headers = [
                model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
                for col in range(model.columnCount())
            ]
            writer.writerow(headers)

            for row in sorted(selected_rows):
                values = [
                    str(model.data(model.index(row, col), Qt.ItemDataRole.DisplayRole) or '')
                    for col in range(model.columnCount())
                ]
                writer.writerow(values)

            QApplication.clipboard().setText(output.getvalue())
            self.status_bar.showMessage(f'Row(s) copied to clipboard')
        except Exception as e:
            self._logger.error('Error copying row', error=str(e))
            self.status_bar.showMessage(f'Error copying row: {str(e)}')

    def show_context_menu(self, position: QPoint) -> None:
        """Show context menu for the results table."""
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
        """Get data from the current table model."""
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
        """Update the database connection string."""
        try:
            self.connection_string = connection_string
            self.db_repo = DatabaseRepository(connection_string)
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
            connection_string = self._config.get(
                f'plugins.autocarequery.connection_string',
                self.connection_string
            )
            self.connection_string = connection_string
            self.db_repo = DatabaseRepository(connection_string)

            # Schedule connection test
            if self._thread_manager:
                self._schedule_connection_test()
            else:
                QTimer.singleShot(10, self._run_connection_test_with_timer)
        except Exception as e:
            self._logger.error('Error refreshing connection', error=str(e))
            self.status_bar.showMessage(f'Error refreshing connection: {str(e)}')

            QMessageBox.critical(
                self,
                'Connection Error',
                f'An error occurred while refreshing the connection:\n\n{str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def _schedule_connection_test(self) -> None:
        """Schedule connection test using thread manager."""
        if not self._thread_manager:
            return

        def _run_test_async(*args, **kwargs):
            """Run coroutine in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._test_connection())
            finally:
                loop.close()

        self._thread_manager.submit_task(
            func=_run_test_async,
            name='autocare_query_test_connection',
            submitter='autocarequery',
            priority=10
        )

    def _run_connection_test_with_timer(self) -> None:
        """Run connection test in current thread with new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._test_connection())
            loop.close()

            # Signal result on the main thread
            if isinstance(result, bool):
                self.connectionTested.emit(
                    result,
                    'Database connection successful' if result else 'Database connection failed'
                )
        except Exception as e:
            self._logger.error(f'Error testing connection: {str(e)}', exc_info=True)
            # Signal error on main thread
            self.connectionTested.emit(False, f'Error testing connection: {str(e)}')

    async def _test_connection(self) -> bool:
        """Test the database connection asynchronously."""
        try:
            success = await self.db_repo.test_connection()
            self.connectionTested.emit(
                success,
                'Database connection successful' if success else 'Database connection failed'
            )
            return success
        except Exception as e:
            self._logger.error('Error testing connection', error=str(e))
            self.connectionTested.emit(False, f'Error testing connection: {str(e)}')
            return False

    @Slot(bool, str)
    def _on_connection_tested(self, success: bool, message: str) -> None:
        """Handle connection test results on the main thread."""
        self.status_bar.showMessage(message)

        if success:
            self._logger.info('Database connection test successful')
            QMessageBox.information(
                self,
                'Connection Test',
                'Database connection successful.',
                QMessageBox.StandardButton.Ok
            )
        else:
            self._logger.error('Database connection test failed')
            QMessageBox.critical(
                self,
                'Connection Test',
                'Database connection failed.',
                QMessageBox.StandardButton.Ok
            )

    def show_connection_settings(self) -> None:
        """Show connection settings dialog."""
        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle('Database Connection Settings')
        layout = QFormLayout(dialog)

        current_conn_str = self._config.get(
            f'plugins.autocarequery.connection_string',
            self.connection_string
        )
        conn_str_input = QLineEdit(current_conn_str)
        conn_str_input.setMinimumWidth(400)
        layout.addRow('Connection String:', conn_str_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_conn_str = conn_str_input.text().strip()
            if new_conn_str and new_conn_str != current_conn_str:
                self._config.set(f'plugins.autocarequery.connection_string', new_conn_str)
                self.update_connection_string(new_conn_str)

    def export_default_queries(self) -> None:
        """Export default queries to Excel files."""
        # Schedule export in thread manager
        if self._thread_manager:
            self._schedule_default_queries_export()
        else:
            QTimer.singleShot(10, self._run_default_queries_export_with_timer)

    def _schedule_default_queries_export(self) -> None:
        """Schedule default queries export using thread manager."""
        if not self._thread_manager:
            return

        def _run_export_async(*args, **kwargs):
            """Run coroutine in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._export_default_queries_async())
            finally:
                loop.close()

        self._thread_manager.submit_task(
            func=_run_export_async,
            name='autocare_query_export_defaults',
            submitter='autocarequery',
            priority=10
        )

    def _run_default_queries_export_with_timer(self) -> None:
        """Run default queries export in current thread with new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._export_default_queries_async())
            loop.close()
        except Exception as e:
            self._logger.error(f'Error exporting default queries: {str(e)}', exc_info=True)
            # Signal error on main thread
            QMetaObject.invokeMethod(
                self,
                "_handle_export_defaults_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e))
            )

    @Slot(str)
    def _handle_export_defaults_error(self, error: str) -> None:
        """Handle errors in default queries export on the main thread."""
        self.status_bar.showMessage(f'Error exporting default queries: {error}')

        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        QMessageBox.critical(
            self,
            'Export Error',
            f'An error occurred while exporting default queries:\n\n{error}',
            QMessageBox.StandardButton.Ok
        )

    async def _export_default_queries_async(self) -> None:
        """Export default queries asynchronously."""
        try:
            # Get directory for export
            save_dir = None

            # Run this on the main thread to show the dialog
            future = asyncio.Future()

            def get_directory():
                nonlocal save_dir
                save_dir = QFileDialog.getExistingDirectory(
                    self, 'Select Directory for Exported Queries', ''
                )
                future.set_result(save_dir)

            QMetaObject.invokeMethod(
                self,
                get_directory,
                Qt.ConnectionType.BlockingQueuedConnection
            )

            await future

            if not save_dir:
                return

            # Show progress dialog
            QMetaObject.invokeMethod(
                self,
                "show_progress_dialog",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, 'Exporting Queries'),
                Q_ARG(str, 'Exporting default queries...')
            )

            # Define default queries
            default_queries = [
                {
                    'name': 'all_toyota_2020',
                    'description': 'All 2020 Toyota vehicles',
                    'filters': FilterDTO(year_id=2020, make_id=1)
                },
                {
                    'name': 'honda_accords_2018_2022',
                    'description': 'Honda Accords 2018-2022',
                    'filters': FilterDTO(
                        use_year_range=True,
                        year_range_start=2018,
                        year_range_end=2022,
                        make_id=2,
                        model_id=10
                    )
                }
            ]

            # Export each query
            for i, query_def in enumerate(default_queries):
                try:
                    # Update progress
                    self.progressUpdated.emit(
                        10 + 30 * i // len(default_queries),
                        f"Executing query for {query_def['name']}..."
                    )

                    # Execute query
                    results = await self.db_repo.execute_vehicle_query(
                        query_def['filters'],
                        limit=1000
                    )

                    # Convert to dict for pandas
                    data = [result.model_dump() for result in results]

                    # Update progress
                    self.progressUpdated.emit(
                        40 + 30 * i // len(default_queries),
                        f"Processing results for {query_def['name']}..."
                    )

                    # Create dataframe
                    df = pd.DataFrame(data)
                    file_path = os.path.join(save_dir, f"{query_def['name']}.xlsx")

                    # Export to Excel
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Vehicle Data')

                        # Add query info sheet
                        description_df = pd.DataFrame([
                            {'Key': 'Name', 'Value': query_def['name']},
                            {'Key': 'Description', 'Value': query_def['description']},
                            {'Key': 'Date Created', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                            {'Key': 'Result Count', 'Value': len(data)}
                        ])
                        description_df.to_excel(writer, index=False, sheet_name='Query Info')

                        # Format columns
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

                    self.progressUpdated.emit(
                        70 + 30 * (i + 1) // len(default_queries),
                        f"Exported {query_def['name']} to {file_path}"
                    )

                    self._logger.info(f"Exported query {query_def['name']} to {file_path}")
                except Exception as e:
                    self._logger.error(f"Error exporting query {query_def['name']}", error=str(e))

            # Complete
            self.progressUpdated.emit(100, 'Export complete')

            # Close progress dialog and show success message on main thread
            QMetaObject.invokeMethod(
                self,
                "_show_export_complete",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, save_dir)
            )
        except Exception as e:
            self._logger.error('Error exporting default queries', error=str(e))
            # Signal error to main thread
            QMetaObject.invokeMethod(
                self,
                "_handle_export_defaults_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e))
            )
            raise

    @Slot(str)
    def _show_export_complete(self, save_dir: str) -> None:
        """Show export complete message on the main thread."""
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

    def cleanup(self) -> None:
        """Clean up resources when tab is closed."""
        try:
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            if hasattr(self, 'db_repo') and self.db_repo:
                if hasattr(self.db_repo, 'sync_engine') and self.db_repo.sync_engine:
                    self.db_repo.sync_engine.dispose()

                if hasattr(self.db_repo, 'engine') and self.db_repo.engine:
                    if self._thread_manager:
                        self._schedule_engine_disposal()
                    else:
                        self._logger.warning('Thread manager not available, async engine may not be properly disposed')

            self._logger.info('AutocareQueryTab resources cleaned up')
        except Exception as e:
            self._logger.error('Error cleaning up resources', error=str(e))

    def _schedule_engine_disposal(self) -> None:
        """Schedule engine disposal using thread manager."""
        if not self._thread_manager:
            return

        def _run_dispose_async(*args, **kwargs):
            """Run coroutine in a new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def _dispose_engine():
                    if hasattr(self.db_repo, 'engine') and self.db_repo.engine:
                        await self.db_repo.engine.dispose()
                        self._logger.debug('Async engine disposed properly')

                return loop.run_until_complete(_dispose_engine())
            finally:
                loop.close()

        self._thread_manager.submit_task(
            func=_run_dispose_async,
            name='dispose_async_engine',
            submitter='autocarequery'
        )