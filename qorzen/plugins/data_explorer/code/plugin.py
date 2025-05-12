from __future__ import annotations

import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTableView, QFileDialog, QTabWidget, QSplitter,
    QLineEdit, QMessageBox
)
from PySide6.QtGui import QIcon

from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration
from qorzen.plugins.data_explorer.code.widgets.visualizer import DataVisualizerWidget
from qorzen.plugins.data_explorer.code.widgets.data_table import DataTableModel, FilteredDataTableView
from qorzen.plugins.data_explorer.code.analysis import DataStatsCalculator, CorrelationAnalyzer, TrendDetector


class DataExplorerPlugin(BasePlugin):
    """
    Data Explorer Plugin for analyzing and visualizing datasets.

    This plugin allows users to load, analyze, and visualize datasets
    in various formats using Python data analysis tools.
    """
    name = 'data_explorer'
    version = '1.0.1'
    description = 'Explore and analyze data with visualizations and statistics'
    author = 'Qorzen Team'
    display_name = 'Data Explorer'

    def __init__(self) -> None:
        """Initialize the plugin with default values."""
        super().__init__()
        self._plugin_lock = threading.RLock()
        self._data_frames: Dict[str, pd.DataFrame] = {}
        self._current_dataset: Optional[str] = None
        self._main_widget: Optional[QWidget] = None
        self._visualizer: Optional[DataVisualizerWidget] = None
        self._data_table_view: Optional[FilteredDataTableView] = None
        self._stats_widget: Optional[QWidget] = None
        self._dataset_selector: Optional[QComboBox] = None
        self._running_tasks: set = set()
        self._icon_path = None
        self._stats_content: Optional[QLabel] = None
        self._loading_label: Optional[QLabel] = None
        self._ui_initialized = False
        self._status_label: Optional[QLabel] = None

    def initialize(self, service_locator: Any, **kwargs: Any) -> None:
        """
        Initialize the plugin with service locator and additional arguments.

        Args:
            service_locator: The service locator for accessing core services
            **kwargs: Additional arguments passed to the plugin
        """
        self._plugin_lock = threading.RLock()
        self._running_tasks = set()

        super().initialize(service_locator, **kwargs)

        if self._logger:
            self._logger.info(f'Plugin {self.name} initializing')

        # Register tasks for data operations only (not UI)
        self.register_task('load_dataset', self._load_dataset_task,
                           long_running=True,
                           description='Load and parse a dataset')

        self.register_task('analyze_dataset', self._analyze_dataset_task,
                           long_running=True,
                           description='Perform statistical analysis on dataset')

        self.register_task('create_visualization', self._create_visualization_task,
                           long_running=True,
                           description='Create data visualization')

        self.register_task('detect_trends', self._detect_trends_task,
                           long_running=True,
                           description='Detect trends in data')

        # Subscribe to system shutdown event
        if self._event_bus:
            self._event_bus.subscribe(
                event_type='system/shutdown',
                callback=self._handle_system_shutdown,
                subscriber_id=f'{self.name}_system_shutdown'
            )

        if self._logger:
            self._logger.info(f'Plugin {self.name} initialized')

        self.initialized.emit()

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """
        Called when the UI system is ready for the plugin to integrate its UI components.

        This method creates all UI components on the main thread.

        Args:
            ui_integration: The UI integration interface for adding UI components
        """
        super().on_ui_ready(ui_integration)

        if self._logger:
            self._logger.info(f'Plugin {self.name} UI initialization starting')

        try:
            # Connect to app quit signal if available
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.aboutToQuit.connect(self._handle_app_quit)

            # Create main widget and layout
            self._main_widget = QWidget()
            main_layout = QVBoxLayout(self._main_widget)

            # Create the toolbar
            toolbar = QWidget()
            toolbar_layout = QHBoxLayout(toolbar)
            toolbar_layout.setContentsMargins(0, 0, 0, 0)

            toolbar_layout.addWidget(QLabel('Dataset:'))
            self._dataset_selector = QComboBox()
            self._dataset_selector.setMinimumWidth(200)
            self._dataset_selector.currentIndexChanged.connect(self._on_dataset_changed)
            toolbar_layout.addWidget(self._dataset_selector)

            load_button = QPushButton('Load Dataset')
            load_button.clicked.connect(self._on_load_dataset_clicked)
            toolbar_layout.addWidget(load_button)

            analyze_button = QPushButton('Analyze')
            analyze_button.clicked.connect(self._on_analyze_clicked)
            toolbar_layout.addWidget(analyze_button)

            trend_button = QPushButton('Detect Trends')
            trend_button.clicked.connect(self._on_detect_trends_clicked)
            toolbar_layout.addWidget(trend_button)

            toolbar_layout.addStretch()
            main_layout.addWidget(toolbar)

            # Main content setup - split view
            splitter = QSplitter(Qt.Orientation.Horizontal)

            # Tab widget setup
            tabs = QTabWidget()

            # Table tab
            table_tab = QWidget()
            table_layout = QVBoxLayout(table_tab)
            table_layout.setContentsMargins(0, 0, 0, 0)

            # Filter setup
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel('Filter:'))
            filter_input = QLineEdit()
            filter_input.setPlaceholderText('Enter filter expression...')
            filter_layout.addWidget(filter_input)
            table_layout.addLayout(filter_layout)

            # Data table setup
            self._data_table_view = FilteredDataTableView()
            self._data_table_view.set_filter_input(filter_input)
            table_layout.addWidget(self._data_table_view)

            tabs.addTab(table_tab, 'Data Table')

            # Visualization tab
            viz_tab = QWidget()
            viz_layout = QVBoxLayout(viz_tab)
            viz_layout.setContentsMargins(0, 0, 0, 0)
            self._visualizer = DataVisualizerWidget()
            viz_layout.addWidget(self._visualizer)

            tabs.addTab(viz_tab, 'Visualizations')

            splitter.addWidget(tabs)

            # Stats widget setup
            self._stats_widget = QWidget()
            stats_layout = QVBoxLayout(self._stats_widget)
            stats_layout.addWidget(QLabel('<h3>Statistics</h3>'))
            self._stats_content = QLabel('No data loaded')
            stats_layout.addWidget(self._stats_content)
            stats_layout.addStretch()

            splitter.addWidget(self._stats_widget)
            splitter.setSizes([700, 300])

            main_layout.addWidget(splitter)

            # Status label for task notifications
            self._status_label = QLabel('')
            self._status_label.setStyleSheet('color: blue;')
            self._status_label.setVisible(False)
            main_layout.addWidget(self._status_label)

            # Add the page with the fully built UI
            icon = QIcon(self._icon_path) if self._icon_path else QIcon()
            ui_integration.add_page(
                'data_explorer',
                self._main_widget,
                name='data_explorer',
                icon=icon,
                text='Data Explorer'
            )

            # Add menu
            menu = ui_integration.add_menu('data_explorer', 'Data Explorer')
            load_action = ui_integration.add_menu_action(
                'data_explorer',
                menu,
                'Load Dataset',
                self._on_load_dataset_clicked
            )
            export_action = ui_integration.add_menu_action(
                'data_explorer',
                menu,
                'Export Results',
                self._on_export_clicked
            )

            # Register UI components
            self.register_ui_component(self._main_widget, 'page')
            self.register_ui_component(menu, 'menu')
            self.register_ui_component(load_action, 'action')
            self.register_ui_component(export_action, 'action')

            self._ui_initialized = True

            if self._logger:
                self._logger.info(f'Plugin {self.name} UI initialization complete')

            self.ui_ready.emit()

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error in on_ui_ready: {str(e)}', exc_info=True)

            # Create a simple error widget if the UI failed to initialize
            if not self._main_widget:
                self._main_widget = QWidget()
                error_layout = QVBoxLayout(self._main_widget)
                error_label = QLabel(f"Error initializing UI: {str(e)}")
                error_label.setStyleSheet("color: red; font-weight: bold;")
                error_layout.addWidget(error_label)

                # Still add the page with the error message
                icon = QIcon(self._icon_path) if self._icon_path else QIcon()
                ui_integration.add_page(
                    'data_explorer',
                    self._main_widget,
                    name='data_explorer',
                    icon=icon,
                    text='Data Explorer'
                )
                self.register_ui_component(self._main_widget, 'page')

    def _initialize_ui_components(self) -> None:
        """
        Initialize the complete UI components.

        This method is no longer used - UI is fully built in on_ui_ready.
        """
        pass

    def _on_load_dataset_clicked(self) -> None:
        """
        Handle the Load Dataset button click.

        Opens a file dialog to select a dataset file and then starts a task to load it.
        """
        if self._logger:
            self._logger.debug("Load Dataset button clicked")

        try:
            # Show file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self._main_widget,
                'Select Dataset',
                '',
                'Data Files (*.csv *.xlsx *.xls *.json);;All Files (*.*)'
            )

            if file_path:
                if self._logger:
                    self._logger.info(f"User selected file: {file_path}")

                # Show loading status
                if self._status_label:
                    self._status_label.setText(f"Loading dataset: {os.path.basename(file_path)}...")
                    self._status_label.setVisible(True)

                # Launch the task to load the dataset
                task_id = self.execute_task('load_dataset', file_path)

                if self._logger:
                    self._logger.debug(f"Started load_dataset task with ID: {task_id}")

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error handling load dataset button click: {str(e)}', exc_info=True)

            QMessageBox.critical(
                self._main_widget,
                'Error',
                f'Failed to load dataset: {str(e)}'
            )

    def _on_dataset_changed(self, index: int) -> None:
        """
        Handle dataset selection change.

        Args:
            index: The index of the selected dataset
        """
        if index < 0 or self._dataset_selector is None:
            return

        dataset_name = self._dataset_selector.currentText()
        if not dataset_name or dataset_name not in self._data_frames:
            return

        self._current_dataset = dataset_name
        df = self._data_frames[dataset_name]

        # Update the data table
        if self._data_table_view:
            model = DataTableModel(df)
            self._data_table_view.setModel(model)

        # Update the visualizer
        if self._visualizer:
            self._visualizer.set_dataframe(df, dataset_name)

        # Update statistics
        self._update_stats_basic(df)

    def _on_analyze_clicked(self) -> None:
        """Handle the Analyze button click."""
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            QMessageBox.warning(
                self._main_widget,
                'No Dataset',
                'Please load a dataset first.'
            )
            return

        # Show status
        if self._status_label:
            self._status_label.setText(f"Analyzing dataset: {self._current_dataset}...")
            self._status_label.setVisible(True)

        # Start analysis task
        task_id = self.execute_task('analyze_dataset', self._current_dataset)

        if self._logger:
            self._logger.debug(f"Started analyze_dataset task with ID: {task_id}")

    def _on_detect_trends_clicked(self) -> None:
        """Handle the Detect Trends button click."""
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            QMessageBox.warning(
                self._main_widget,
                'No Dataset',
                'Please load a dataset first.'
            )
            return

        # Show status
        if self._status_label:
            self._status_label.setText(f"Detecting trends in dataset: {self._current_dataset}...")
            self._status_label.setVisible(True)

        # Start trend detection task
        task_id = self.execute_task('detect_trends', self._current_dataset)

        if self._logger:
            self._logger.debug(f"Started detect_trends task with ID: {task_id}")

    def _on_export_clicked(self) -> None:
        """Handle the Export Results button click."""
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            QMessageBox.warning(
                self._main_widget,
                'No Dataset',
                'Please load a dataset first.'
            )
            return

        # Show export dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self._main_widget,
            'Export Results',
            f'{self._current_dataset}_analysis.html',
            'HTML Files (*.html);;CSV Files (*.csv);;All Files (*.*)'
        )

        if not file_path:
            return

        # Export based on file type
        if file_path.lower().endswith('.html'):
            self._export_html_report(file_path)
        elif file_path.lower().endswith('.csv'):
            self._export_csv_results(file_path)
        else:
            QMessageBox.warning(
                self._main_widget,
                'Export Error',
                'Unsupported file format.'
            )

    def execute_task(self, task_name: str, *args: Any, **kwargs: Any) -> Optional[str]:
        """
        Execute a task and track it.

        This overrides the BasePlugin method to add tracking of running tasks
        and status updates.

        Args:
            task_name: The name of the task to execute
            *args: Arguments to pass to the task
            **kwargs: Keyword arguments to pass to the task

        Returns:
            The task ID if successful, None otherwise
        """
        # Call the parent implementation
        task_id = super().execute_task(task_name, *args, **kwargs)

        if task_id:
            with self._plugin_lock:
                self._running_tasks.add(task_id)

            # Set up event handlers to track task completion
            if self._event_bus:
                # Common handler for task completion
                def on_task_completion(event: Any) -> None:
                    if event.payload.get('task_id') == task_id:
                        with self._plugin_lock:
                            self._running_tasks.discard(task_id)

                        # Hide status label when task is done
                        if self._status_label:
                            QTimer.singleShot(2000, lambda: self._hide_status_label())

                        # Unsubscribe from events
                        if self._event_bus:
                            self._event_bus.unsubscribe(subscriber_id=f'{self.name}_task_{task_id}')

                # Subscribe to task completion events
                for event_type in ['task/completed', 'task/failed', 'task/cancelled']:
                    self._event_bus.subscribe(
                        event_type=event_type,
                        callback=on_task_completion,
                        subscriber_id=f'{self.name}_task_{task_id}'
                    )

        return task_id

    def _hide_status_label(self) -> None:
        """Hide the status label."""
        if self._status_label:
            self._status_label.setVisible(False)

    def _load_dataset_task(self, file_path: str, progress_reporter: Any) -> str:
        """
        Task to load a dataset from a file.

        Args:
            file_path: Path to the dataset file
            progress_reporter: Reporter to report task progress

        Returns:
            The name of the loaded dataset
        """
        progress_reporter.report_progress(0, 'Starting dataset load...')

        dataset_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            progress_reporter.report_progress(10, 'Reading file...')

            # Load the dataset based on file type
            if file_ext in ['.csv']:
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
            else:
                raise ValueError(f'Unsupported file format: {file_ext}')

            progress_reporter.report_progress(50, 'Processing data...')

            # Try to convert string columns to numeric if they contain mostly numbers
            for col in df.select_dtypes(include=['object']).columns:
                try:
                    numeric_values = pd.to_numeric(df[col], errors='coerce')
                    if numeric_values.notnull().mean() > 0.5:
                        df[col] = numeric_values
                except Exception:
                    pass

            # Store the dataframe
            self._data_frames[dataset_name] = df

            progress_reporter.report_progress(80, 'Updating UI...')

            # Update the UI on the main thread using QTimer.singleShot
            QTimer.singleShot(0, lambda: self._update_ui_after_load(dataset_name))

            progress_reporter.report_progress(100, 'Dataset loaded successfully')

            return dataset_name

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error loading dataset: {str(e)}', exc_info=True)

            progress_reporter.report_progress(100, f'Error: {str(e)}')

            # Show error in UI
            QTimer.singleShot(0, lambda: self._show_error_message(
                'Load Error', f'Failed to load dataset: {str(e)}'
            ))

            raise

    def _show_error_message(self, title: str, message: str) -> None:
        """
        Show an error message dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        QMessageBox.critical(self._main_widget, title, message)

    def _update_ui_after_load(self, dataset_name: str) -> None:
        """
        Update the UI after loading a dataset.

        Args:
            dataset_name: The name of the loaded dataset
        """
        # Update the dataset selector
        if self._dataset_selector:
            # Check if this dataset is already in the selector
            found = False
            for i in range(self._dataset_selector.count()):
                if self._dataset_selector.itemText(i) == dataset_name:
                    found = True
                    self._dataset_selector.setCurrentIndex(i)
                    break

            # Add it if not found
            if not found:
                self._dataset_selector.addItem(dataset_name)
                self._dataset_selector.setCurrentText(dataset_name)

        # Update status label
        if self._status_label:
            self._status_label.setText(f"Dataset '{dataset_name}' loaded successfully")
            QTimer.singleShot(3000, lambda: self._hide_status_label())

    def _analyze_dataset_task(self, dataset_name: str, progress_reporter: Any) -> Dict[str, Any]:
        """
        Task to analyze a dataset.

        Args:
            dataset_name: The name of the dataset to analyze
            progress_reporter: Reporter to report task progress

        Returns:
            A dictionary with analysis results
        """
        if dataset_name not in self._data_frames:
            raise ValueError(f'Dataset not found: {dataset_name}')

        df = self._data_frames[dataset_name]
        progress_reporter.report_progress(0, 'Starting analysis...')

        results: Dict[str, Any] = {}

        try:
            progress_reporter.report_progress(10, 'Calculating statistics...')

            # Calculate summary statistics
            stats_calculator = DataStatsCalculator(df)
            summary_stats = stats_calculator.calculate_summary()
            results['summary'] = summary_stats

            progress_reporter.report_progress(40, 'Analyzing correlations...')

            # Analyze correlations
            corr_analyzer = CorrelationAnalyzer(df)
            correlation_results = corr_analyzer.find_notable_correlations()
            results['correlations'] = correlation_results

            progress_reporter.report_progress(70, 'Creating visualizations...')

            # Create visualizations (as a separate task)
            self.execute_task('create_visualization', dataset_name)

            progress_reporter.report_progress(90, 'Updating UI...')

            # Update the statistics panel on the main thread
            QTimer.singleShot(0, lambda: self._update_stats_detailed(dataset_name, results))

            progress_reporter.report_progress(100, 'Analysis complete')

            return results

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error analyzing dataset: {str(e)}', exc_info=True)

            progress_reporter.report_progress(100, f'Error: {str(e)}')

            # Show error in UI
            QTimer.singleShot(0, lambda: self._show_error_message(
                'Analysis Error', f'Failed to analyze dataset: {str(e)}'
            ))

            raise

    def _create_visualization_task(self, dataset_name: str, progress_reporter: Any) -> bool:
        """
        Task to create visualizations for a dataset.

        Args:
            dataset_name: The name of the dataset to visualize
            progress_reporter: Reporter to report task progress

        Returns:
            True if successful, False otherwise
        """
        if dataset_name not in self._data_frames:
            raise ValueError(f'Dataset not found: {dataset_name}')

        df = self._data_frames[dataset_name]
        progress_reporter.report_progress(0, 'Creating visualizations...')

        try:
            if not self._visualizer:
                progress_reporter.report_progress(100, 'Visualizer not initialized')
                return False

            # Create visualizations on the main thread using proper closure capture
            progress_reporter.report_progress(20, 'Creating distribution plots...')
            data_frame = df  # Create local variables for lambda capture
            ds_name = dataset_name
            QTimer.singleShot(0, lambda: self._visualizer.create_distribution_plots(data_frame, ds_name))

            progress_reporter.report_progress(50, 'Creating correlation heatmap...')
            QTimer.singleShot(0, lambda: self._visualizer.create_correlation_heatmap(data_frame, ds_name))

            progress_reporter.report_progress(80, 'Creating scatter plots...')
            QTimer.singleShot(0, lambda: self._visualizer.create_scatter_plots(data_frame, ds_name))

            progress_reporter.report_progress(100, 'Visualizations complete')

            return True

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error creating visualizations: {str(e)}', exc_info=True)

            progress_reporter.report_progress(100, f'Error: {str(e)}')

            raise

    def _detect_trends_task(self, dataset_name: str, progress_reporter: Any) -> Dict[str, Any]:
        """
        Task to detect trends in a dataset.

        Args:
            dataset_name: The name of the dataset to analyze
            progress_reporter: Reporter to report task progress

        Returns:
            A dictionary with trend results
        """
        if dataset_name not in self._data_frames:
            raise ValueError(f'Dataset not found: {dataset_name}')

        df = self._data_frames[dataset_name]
        progress_reporter.report_progress(0, 'Starting trend detection...')

        results: Dict[str, Any] = {}

        try:
            progress_reporter.report_progress(20, 'Analyzing patterns...')

            # Detect trends
            trend_detector = TrendDetector(df)
            trends = trend_detector.detect_trends()
            results['trends'] = trends

            progress_reporter.report_progress(50, 'Creating trend visualizations...')

            # Create trend plots on the main thread
            if self._visualizer:
                QTimer.singleShot(0, lambda df=df, name=dataset_name, trends=trends:
                self._visualizer.create_trend_plots(df, name, trends))

            progress_reporter.report_progress(80, 'Updating stats panel...')

            # Update statistics and show results on the main thread
            trends_copy = trends.copy()  # Create a local copy for lambda capture
            ds_name = dataset_name
            QTimer.singleShot(0, lambda: self._show_trend_results(ds_name, trends_copy))

            progress_reporter.report_progress(100, 'Trend detection complete')

            return results

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error detecting trends: {str(e)}', exc_info=True)

            progress_reporter.report_progress(100, f'Error: {str(e)}')

            # Show error in UI
            QTimer.singleShot(0, lambda: self._show_error_message(
                'Trend Detection Error', f'Failed to detect trends: {str(e)}'
            ))

            raise

    def _show_trend_results(self, dataset_name: str, trends: List[str]) -> None:
        """
        Show trend results in the UI.

        Args:
            dataset_name: The name of the dataset
            trends: List of detected trends
        """
        # Update the statistics panel
        if self._current_dataset == dataset_name:
            self._update_stats_detailed(dataset_name, {'trends': trends})

        # Show results in a message box
        trends_text = '\n'.join(trends[:5])
        if len(trends) > 5:
            trends_text += '\n...'

        QMessageBox.information(
            self._main_widget,
            'Trend Detection Results',
            f'Detected {len(trends)} trends in the dataset.\n\n{trends_text}'
        )

    def _update_stats_basic(self, df: pd.DataFrame) -> None:
        """
        Update the statistics panel with basic statistics.

        Args:
            df: The dataframe to summarize
        """
        if self._stats_content is None:
            return

        # Calculate basic statistics
        num_rows = len(df)
        num_cols = len(df.columns)
        memory_usage = df.memory_usage().sum() / 1024 ** 2
        null_counts = df.isnull().sum()
        total_nulls = null_counts.sum()
        dtypes = df.dtypes.value_counts()
        dtype_str = ', '.join((f'{dtype}: {count}' for dtype, count in dtypes.items()))

        # Format the statistics as HTML
        stats_text = f'''
        <h3>Dataset Overview</h3>
        <b>Name:</b> {self._current_dataset}<br>
        <b>Rows:</b> {num_rows:,}<br>
        <b>Columns:</b> {num_cols}<br>
        <b>Memory Usage:</b> {memory_usage:.2f} MB<br>
        <b>Missing Values:</b> {total_nulls:,}<br>
        <b>Data Types:</b> {dtype_str}<br>

        <h3>Column Information</h3>
        <table style="width:100%">
        <tr><th>Column</th><th>Type</th><th>Missing</th></tr>
        '''

        # Add column information
        for col in df.columns:
            dtype = df[col].dtype
            nulls = null_counts[col]
            stats_text += f'<tr><td>{col}</td><td>{dtype}</td><td>{nulls:,}</td></tr>'

        stats_text += '</table>'

        # Set the text
        self._stats_content.setText(stats_text)

    def _update_stats_detailed(self, dataset_name: str, stats_data: Dict[str, Any]) -> None:
        """
        Update the statistics panel with detailed statistics.

        Args:
            dataset_name: The name of the dataset
            stats_data: Dictionary with statistics data
        """
        if self._stats_content is None or dataset_name != self._current_dataset:
            return

        # Format the statistics as HTML
        stats_text = f'''
        <h3>Dataset Analysis: {dataset_name}</h3>
        '''

        # Add summary statistics
        if 'summary' in stats_data:
            summary = stats_data['summary']
            stats_text += f'''
            <h4>Summary Statistics</h4>
            <table style="width:100%">
            <tr><th>Metric</th><th>Value</th></tr>
            '''

            for metric, value in summary.items():
                stats_text += f'<tr><td>{metric}</td><td>{value}</td></tr>'

            stats_text += '</table>'

        # Add correlation information
        if 'correlations' in stats_data:
            correlations = stats_data['correlations']
            stats_text += f'''
            <h4>Notable Correlations</h4>
            <table style="width:100%">
            <tr><th>Variables</th><th>Correlation</th><th>Strength</th></tr>
            '''

            for corr_item in correlations:
                var1 = corr_item['var1']
                var2 = corr_item['var2']
                corr_value = corr_item['value']
                strength = corr_item['strength']

                # Set background color based on correlation strength
                color = '#ffffff'
                if strength == 'Strong Positive':
                    color = '#d4edda'
                elif strength == 'Strong Negative':
                    color = '#f8d7da'
                elif strength == 'Moderate Positive':
                    color = '#e2efda'
                elif strength == 'Moderate Negative':
                    color = '#ffe6e6'

                stats_text += f'<tr style="background-color:{color}"><td>{var1} / {var2}</td><td>{corr_value:.3f}</td><td>{strength}</td></tr>'

            stats_text += '</table>'

        # Add trend information
        if 'trends' in stats_data:
            trends = stats_data['trends']
            stats_text += f'''
            <h4>Detected Trends</h4>
            <ul>
            '''

            for trend in trends:
                stats_text += f'<li>{trend}</li>'

            stats_text += '</ul>'

        # Set the text
        self._stats_content.setText(stats_text)

    def _export_html_report(self, file_path: str) -> None:
        """
        Export analysis results as an HTML report.

        Args:
            file_path: Path to save the HTML file
        """
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            return

        df = self._data_frames[self._current_dataset]

        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <title>Data Analysis: {self._current_dataset}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                h1, h2, h3 {{ color: #2c3e50; }}
            </style>
        </head>
        <body>
            <h1>Data Analysis Report: {self._current_dataset}</h1>
            <h2>Dataset Information</h2>
            <ul>
                <li>Rows: {len(df)}</li>
                <li>Columns: {len(df.columns)}</li>
                <li>Memory Usage: {df.memory_usage().sum() / 1024 ** 2:.2f} MB</li>
            </ul>

            <h2>Data Summary</h2>
            {df.describe().to_html()}

            <h2>Column Types</h2>
            <table>
                <tr><th>Column</th><th>Type</th></tr>
                {''.join((f'<tr><td>{col}</td><td>{dtype}</td></tr>' for col, dtype in df.dtypes.items()))}
            </table>

            <h2>Sample Data</h2>
            {df.head(10).to_html()}
        </body>
        </html>
        """

        try:
            # Write the HTML to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            QMessageBox.information(
                self._main_widget,
                'Export Successful',
                f'Report exported to {file_path}'
            )

        except Exception as e:
            QMessageBox.critical(
                self._main_widget,
                'Export Error',
                f'Failed to export report: {str(e)}'
            )

    def _export_csv_results(self, file_path: str) -> None:
        """
        Export dataset as a CSV file.

        Args:
            file_path: Path to save the CSV file
        """
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            return

        df = self._data_frames[self._current_dataset]

        try:
            # Export to CSV
            df.to_csv(file_path, index=False)

            QMessageBox.information(
                self._main_widget,
                'Export Successful',
                f'Data exported to {file_path}'
            )

        except Exception as e:
            QMessageBox.critical(
                self._main_widget,
                'Export Error',
                f'Failed to export data: {str(e)}'
            )

    def _handle_app_quit(self) -> None:
        """Handle application quit event."""
        if self._logger:
            self._logger.info(f'Plugin {self.name} handling application quit')

        # Clean up resources
        self._data_frames.clear()

    def _handle_system_shutdown(self, event: Any) -> None:
        """
        Handle system shutdown event.

        Args:
            event: The event object
        """
        if self._logger:
            self._logger.info(f'Plugin {self.name} received system shutdown')

        self.shutdown()

    def shutdown(self) -> None:
        """
        Shut down the plugin and clean up resources.

        This method ensures all UI components are properly removed and
        all tasks are cancelled.
        """
        if hasattr(self, '_logger') and self._logger:
            self._logger.info(f'Plugin {self.name} shutting down')

        self.shutdown_started.emit()

        # Unsubscribe from system events
        if hasattr(self, '_event_bus') and self._event_bus:
            subscriber_id = f'{self.name}_system_shutdown'
            self._event_bus.unsubscribe(subscriber_id=subscriber_id)

        # Cancel running tasks
        with self._plugin_lock:
            for task_id in list(self._running_tasks):
                if hasattr(self, '_task_manager') and self._task_manager:
                    self._task_manager.cancel_task(task_id)
            self._running_tasks.clear()

        # Clear data
        self._data_frames.clear()

        # Call parent implementation to clean up UI components
        super().shutdown()