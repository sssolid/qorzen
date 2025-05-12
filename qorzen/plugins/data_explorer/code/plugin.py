# qorzen/plugins/data_explorer/plugin.py
from __future__ import annotations

import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableView, QFileDialog, QTabWidget, QSplitter, QLineEdit, QMessageBox
)
from PySide6.QtGui import QIcon

from qorzen.plugin_system.interface import BasePlugin
from qorzen.ui.integration import UIIntegration
from qorzen.plugins.data_explorer.code.widgets.visualizer import DataVisualizerWidget
from qorzen.plugins.data_explorer.code.widgets.data_table import DataTableModel, FilteredDataTableView
from qorzen.plugins.data_explorer.code.analysis import (
    DataStatsCalculator,
    CorrelationAnalyzer,
    TrendDetector
)


class DataExplorerPlugin(BasePlugin):
    """
    Data Explorer Plugin for exploratory data analysis.

    This plugin demonstrates how the new threading system handles all concerns
    automatically without the plugin needing to worry about threading issues.
    """

    name = "data_explorer"
    version = "1.0.0"
    description = "Explore and analyze data with visualizations and statistics"
    author = "Qorzen Team"
    display_name = "Data Explorer"

    def __init__(self) -> None:
        """Initialize the data explorer plugin."""
        super().__init__()
        self._plugin_lock = threading.RLock()
        self._data_frames: Dict[str, pd.DataFrame] = {}
        self._current_dataset: Optional[str] = None
        self._main_widget: Optional[QWidget] = None
        self._visualizer: Optional[DataVisualizerWidget] = None
        self._data_table_view: Optional[FilteredDataTableView] = None
        self._stats_widget: Optional[QWidget] = None
        self._dataset_selector: Optional[QComboBox] = None
        self._running_tasks = set()

        self._icon_path = None

    def initialize(self, service_locator: Any, **kwargs: Any) -> None:
        """Initialize plugin with proper lifecycle management."""
        # Create our thread safety lock
        self._plugin_lock = threading.RLock()
        self._running_tasks = set()
        self._lifecycle_state = "initializing"

        # Call base implementation to set up managers
        super().initialize(service_locator, **kwargs)

        # Log initialization
        self._logger.info(f"Plugin {self.name} initializing")

        # Register tasks without using background initialization
        # to avoid threading complexities
        self.register_task(
            "load_dataset",
            self._load_dataset_task,
            long_running=True,
            description="Load and parse a dataset"
        )

        self.register_task(
            "analyze_dataset",
            self._analyze_dataset_task,
            long_running=True,
            description="Perform statistical analysis on dataset"
        )

        self.register_task(
            "create_visualization",
            self._create_visualization_task,
            long_running=True,
            description="Create data visualization"
        )

        self.register_task(
            "detect_trends",
            self._detect_trends_task,
            long_running=True,
            description="Detect trends in data"
        )

        # Register shutdown handler
        self._event_bus.subscribe(
            event_type="system/shutdown",
            callback=lambda event: self.shutdown(),
            subscriber_id=f"{self.name}_system_shutdown"
        )

        # Update lifecycle state
        self._lifecycle_state = "initialized"
        self._logger.info(f"Plugin {self.name} initialized")

        # Signal initialization complete
        self.initialized.emit()

    def on_ui_ready(self, ui_integration: UIIntegration) -> None:
        """
        Set up UI when the main UI is ready.

        Args:
            ui_integration: UI integration object
        """
        super().on_ui_ready(ui_integration)

        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                # Use a lambda to avoid "unresolved reference" errors
                app.aboutToQuit.connect(lambda: self._handle_app_quit())
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to connect to aboutToQuit signal: {str(e)}")

        self._lifecycle_state = "ui_initializing"
        self._logger.info(f"Plugin {self.name} UI initialization starting")

        # Create main widget
        self._main_widget = QWidget()
        main_layout = QVBoxLayout(self._main_widget)

        # Create toolbar with controls
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # Add dataset selection controls
        toolbar_layout.addWidget(QLabel("Dataset:"))
        self._dataset_selector = QComboBox()
        self._dataset_selector.setMinimumWidth(200)
        self._dataset_selector.currentIndexChanged.connect(self._on_dataset_changed)
        toolbar_layout.addWidget(self._dataset_selector)

        # Add load button
        load_button = QPushButton("Load Dataset")
        load_button.clicked.connect(self._on_load_dataset_clicked)
        toolbar_layout.addWidget(load_button)

        # Add analyze button
        analyze_button = QPushButton("Analyze")
        analyze_button.clicked.connect(self._on_analyze_clicked)
        toolbar_layout.addWidget(analyze_button)

        # Add trend detection button
        trend_button = QPushButton("Detect Trends")
        trend_button.clicked.connect(self._on_detect_trends_clicked)
        toolbar_layout.addWidget(trend_button)

        # Add spacer
        toolbar_layout.addStretch()

        # Add toolbar to main layout
        main_layout.addWidget(toolbar)

        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create tabs for different views
        tabs = QTabWidget()

        # Create table view tab
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Add filter input
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Enter filter expression...")
        filter_layout.addWidget(filter_input)
        table_layout.addLayout(filter_layout)

        # Add table view
        self._data_table_view = FilteredDataTableView()
        self._data_table_view.set_filter_input(filter_input)
        table_layout.addWidget(self._data_table_view)

        # Add table tab to tabs
        tabs.addTab(table_tab, "Data Table")

        # Create visualizer tab
        viz_tab = QWidget()
        viz_layout = QVBoxLayout(viz_tab)
        viz_layout.setContentsMargins(0, 0, 0, 0)
        self._visualizer = DataVisualizerWidget()
        viz_layout.addWidget(self._visualizer)
        tabs.addTab(viz_tab, "Visualizations")

        # Add tabs to splitter
        splitter.addWidget(tabs)

        # Create statistics panel
        self._stats_widget = QWidget()
        stats_layout = QVBoxLayout(self._stats_widget)
        stats_layout.addWidget(QLabel("<h3>Statistics</h3>"))
        self._stats_content = QLabel("No data loaded")
        stats_layout.addWidget(self._stats_content)
        stats_layout.addStretch()

        # Add stats widget to splitter
        splitter.addWidget(self._stats_widget)

        # Set splitter sizes
        splitter.setSizes([700, 300])

        # Add splitter to main layout
        main_layout.addWidget(splitter)

        icon = QIcon(self._icon_path) if self._icon_path else QIcon()
        # Add widget to UI
        page = ui_integration.add_page(
            "data_explorer",
            self._main_widget,
            "Data Explorer",
            icon,
            "Data Explorer"
        )
        self.register_ui_component(page, "page")

        # Add menu
        menu = ui_integration.add_menu("data_explorer", "Data Explorer")

        # Add menu actions
        load_action = menu.addAction("Load Dataset")
        load_action.triggered.connect(self._on_load_dataset_clicked)
        self.register_ui_component(load_action, "action")

        export_action = menu.addAction("Export Results")
        export_action.triggered.connect(self._on_export_clicked)
        self.register_ui_component(export_action, "action")

        self.register_ui_component(menu, "menu")

        # Update lifecycle state
        self._lifecycle_state = "ui_ready"
        self._logger.info(f"Plugin {self.name} UI ready")

        # Signal UI is ready
        self.ui_ready.emit()

    def execute_task(self, task_name: str, *args: Any, **kwargs: Any) -> Optional[str]:
        """
        Execute a registered task and track it properly.

        This overrides the BasePlugin execute_task to add task tracking.
        """
        task_id = super().execute_task(task_name, *args, **kwargs)

        if task_id:
            with self._plugin_lock:
                self._running_tasks.add(task_id)

            # Set up cleanup without using QTimer
            def on_task_completion(event):
                event_task_id = event.payload.get("task_id")
                if event_task_id == task_id:
                    with self._plugin_lock:
                        self._running_tasks.discard(task_id)
                    # Unsubscribe to avoid memory leaks
                    self._event_bus.unsubscribe(subscriber_id=f"{self.name}_cleanup_{task_id}")

            # Subscribe to both completion and failure events
            for event_type in ["task/completed", "task/failed", "task/cancelled"]:
                self._event_bus.subscribe(
                    event_type=event_type,
                    callback=on_task_completion,
                    subscriber_id=f"{self.name}_cleanup_{task_id}"
                )

        return task_id

    def _on_load_dataset_clicked(self) -> None:
        """Handle load dataset button click."""
        # Open file dialog to select dataset
        file_path, _ = QFileDialog.getOpenFileName(
            self._main_widget,
            "Select Dataset",
            "",
            "Data Files (*.csv *.xlsx *.xls *.json);;All Files (*.*)"
        )

        if file_path:
            # Use the execute_task method provided by BasePlugin
            # This executes the registered task "load_dataset" with the file_path parameter
            task_id = self.execute_task("load_dataset", file_path)

            # Show loading indicator (safely on main thread)
            def show_loading_indicator():
                status_label = QLabel(f"Loading dataset... (Task ID: {task_id})")
                self._main_widget.layout().addWidget(status_label)

                # Use event_bus safely without timers
                def on_task_event(event):
                    if (event.event_type == "task/completed" and
                            event.payload.get("task_id") == task_id):
                        status_label.setText("Dataset loaded successfully!")
                        status_label.deleteLater()

                # Subscribe to task events
                self._event_bus.subscribe(
                    event_type="task/completed",
                    callback=on_task_event,
                    subscriber_id=f"{self.name}_load_{task_id}"
                )

            # Ensure UI updates happen on main thread
            if self._thread_manager:
                if not self._thread_manager.is_main_thread():
                    self._thread_manager.run_on_main_thread(show_loading_indicator)
                else:
                    show_loading_indicator()

    def _on_dataset_changed(self, index: int) -> None:
        """
        Handle dataset selection change.

        Args:
            index: Selected index
        """
        if index < 0 or self._dataset_selector is None:
            return

        dataset_name = self._dataset_selector.currentText()
        if not dataset_name or dataset_name not in self._data_frames:
            return

        # Update the current dataset
        self._current_dataset = dataset_name
        df = self._data_frames[dataset_name]

        # Update table view
        model = DataTableModel(df)
        self._data_table_view.setModel(model)

        # Update visualizer
        self._visualizer.set_dataframe(df, dataset_name)

        # Update stats panel with basic information
        self._update_stats_basic(df)

    def _on_analyze_clicked(self) -> None:
        """Handle analyze button click."""
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            QMessageBox.warning(
                self._main_widget,
                "No Dataset",
                "Please load a dataset first."
            )
            return

        # Execute analysis task
        self.execute_task("analyze_dataset", self._current_dataset)

    def _on_detect_trends_clicked(self) -> None:
        """Handle detect trends button click."""
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            QMessageBox.warning(
                self._main_widget,
                "No Dataset",
                "Please load a dataset first."
            )
            return

        # Execute trend detection task
        self.execute_task("detect_trends", self._current_dataset)

    def _on_export_clicked(self) -> None:
        """Handle export results button click."""
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            QMessageBox.warning(
                self._main_widget,
                "No Dataset",
                "Please load a dataset first."
            )
            return

        # Show export dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self._main_widget,
            "Export Results",
            f"{self._current_dataset}_analysis.html",
            "HTML Files (*.html);;CSV Files (*.csv);;All Files (*.*)"
        )

        if not file_path:
            return

        # Export results based on file type
        if file_path.lower().endswith('.html'):
            self._export_html_report(file_path)
        elif file_path.lower().endswith('.csv'):
            self._export_csv_results(file_path)
        else:
            QMessageBox.warning(
                self._main_widget,
                "Export Error",
                "Unsupported file format."
            )

    def _export_html_report(self, file_path: str) -> None:
        """
        Export analysis as HTML report.

        Args:
            file_path: Path to save HTML report
        """
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            return

        df = self._data_frames[self._current_dataset]

        # Generate HTML content with analysis results
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
                {"".join(f"<tr><td>{col}</td><td>{dtype}</td></tr>" for col, dtype in df.dtypes.items())}
            </table>

            <h2>Sample Data</h2>
            {df.head(10).to_html()}
        </body>
        </html>
        """

        # Write content to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            QMessageBox.information(
                self._main_widget,
                "Export Successful",
                f"Report exported to {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self._main_widget,
                "Export Error",
                f"Failed to export report: {str(e)}"
            )

    def _export_csv_results(self, file_path: str) -> None:
        """
        Export data as CSV.

        Args:
            file_path: Path to save CSV file
        """
        if not self._current_dataset or self._current_dataset not in self._data_frames:
            return

        df = self._data_frames[self._current_dataset]

        try:
            df.to_csv(file_path, index=False)
            QMessageBox.information(
                self._main_widget,
                "Export Successful",
                f"Data exported to {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self._main_widget,
                "Export Error",
                f"Failed to export data: {str(e)}"
            )

    def _update_stats_basic(self, df: pd.DataFrame) -> None:
        """
        Update stats panel with basic dataset information.

        Args:
            df: DataFrame to get stats from
        """
        if self._stats_content is None:
            return

        # Get basic stats
        num_rows = len(df)
        num_cols = len(df.columns)
        memory_usage = df.memory_usage().sum() / 1024 ** 2  # MB

        # Count null values
        null_counts = df.isnull().sum()
        total_nulls = null_counts.sum()

        # Get data types
        dtypes = df.dtypes.value_counts()
        dtype_str = ", ".join(f"{dtype}: {count}" for dtype, count in dtypes.items())

        # Format stats text
        stats_text = f"""
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
        """

        # Add column details
        for col in df.columns:
            dtype = df[col].dtype
            nulls = null_counts[col]
            stats_text += f"<tr><td>{col}</td><td>{dtype}</td><td>{nulls:,}</td></tr>"

        stats_text += "</table>"

        # Set text to stats widget
        self._stats_content.setText(stats_text)

    def _update_stats_detailed(self, dataset_name: str, stats_data: Dict[str, Any]) -> None:
        """
        Update stats panel with detailed analysis results.

        Args:
            dataset_name: Dataset name
            stats_data: Analysis results
        """
        if self._stats_content is None or dataset_name != self._current_dataset:
            return

        # Format stats text
        stats_text = f"""
        <h3>Dataset Analysis: {dataset_name}</h3>
        """

        # Add general statistics
        if "summary" in stats_data:
            summary = stats_data["summary"]
            stats_text += f"""
            <h4>Summary Statistics</h4>
            <table style="width:100%">
            <tr><th>Metric</th><th>Value</th></tr>
            """

            for metric, value in summary.items():
                stats_text += f"<tr><td>{metric}</td><td>{value}</td></tr>"

            stats_text += "</table>"

        # Add correlation highlights
        if "correlations" in stats_data:
            correlations = stats_data["correlations"]
            stats_text += f"""
            <h4>Notable Correlations</h4>
            <table style="width:100%">
            <tr><th>Variables</th><th>Correlation</th><th>Strength</th></tr>
            """

            for corr_item in correlations:
                var1 = corr_item["var1"]
                var2 = corr_item["var2"]
                corr_value = corr_item["value"]
                strength = corr_item["strength"]

                # Color code based on strength
                color = "#ffffff"
                if strength == "Strong Positive":
                    color = "#d4edda"
                elif strength == "Strong Negative":
                    color = "#f8d7da"
                elif strength == "Moderate Positive":
                    color = "#e2efda"
                elif strength == "Moderate Negative":
                    color = "#ffe6e6"

                stats_text += f'<tr style="background-color:{color}"><td>{var1} / {var2}</td><td>{corr_value:.3f}</td><td>{strength}</td></tr>'

            stats_text += "</table>"

        # Add trends if available
        if "trends" in stats_data:
            trends = stats_data["trends"]
            stats_text += f"""
            <h4>Detected Trends</h4>
            <ul>
            """

            for trend in trends:
                stats_text += f"<li>{trend}</li>"

            stats_text += "</ul>"

        # Set text to stats widget
        self._stats_content.setText(stats_text)

    # ===== Task implementations =====

    def _load_dataset_task(self, file_path: str, progress_reporter: Any) -> str:
        """
        Task to load a dataset from file.

        Args:
            file_path: Path to dataset file
            progress_reporter: Progress reporter

        Returns:
            Dataset name
        """
        # Report starting
        progress_reporter.report_progress(0, "Starting dataset load...")

        # Get file name for dataset name
        dataset_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            # Load data based on file type
            progress_reporter.report_progress(10, "Reading file...")

            if file_ext in ['.csv']:
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            progress_reporter.report_progress(50, "Processing data...")

            # Basic preprocessing
            # - Convert object columns with mostly numbers to numeric
            for col in df.select_dtypes(include=['object']).columns:
                try:
                    numeric_values = pd.to_numeric(df[col], errors='coerce')
                    if numeric_values.notnull().mean() > 0.5:  # More than 50% convertible
                        df[col] = numeric_values
                except:
                    pass

            # Store the dataframe
            self._data_frames[dataset_name] = df

            progress_reporter.report_progress(80, "Updating UI...")

            # Update UI safely on main thread
            def update_ui():
                if self._dataset_selector:
                    # Check if dataset already exists
                    found = False
                    for i in range(self._dataset_selector.count()):
                        if self._dataset_selector.itemText(i) == dataset_name:
                            found = True
                            self._dataset_selector.setCurrentIndex(i)
                            break

                    # Add if not found
                    if not found:
                        self._dataset_selector.addItem(dataset_name)
                        self._dataset_selector.setCurrentText(dataset_name)

            # Ensure UI updates happen on main thread
            if self._thread_manager:
                self._thread_manager.execute_on_main_thread_sync(update_ui)

            progress_reporter.report_progress(100, "Dataset loaded successfully")

            return dataset_name

        except Exception as e:
            self._logger.error(f"Error loading dataset: {str(e)}")
            progress_reporter.report_progress(100, f"Error: {str(e)}")
            raise

    def _analyze_dataset_task(self, dataset_name: str, progress_reporter: Any) -> Dict[str, Any]:
        """
        Task to analyze a dataset.

        Args:
            dataset_name: Dataset to analyze
            progress_reporter: Progress reporter

        Returns:
            Analysis results
        """
        if dataset_name not in self._data_frames:
            raise ValueError(f"Dataset not found: {dataset_name}")

        df = self._data_frames[dataset_name]

        # Report starting
        progress_reporter.report_progress(0, "Starting analysis...")

        # Create results container
        results: Dict[str, Any] = {}

        try:
            # Calculate basic statistics
            progress_reporter.report_progress(10, "Calculating statistics...")

            # Use data stats calculator
            stats_calculator = DataStatsCalculator(df)
            summary_stats = stats_calculator.calculate_summary()
            results["summary"] = summary_stats

            # Calculate correlations
            progress_reporter.report_progress(40, "Analyzing correlations...")

            # Use correlation analyzer
            corr_analyzer = CorrelationAnalyzer(df)
            correlation_results = corr_analyzer.find_notable_correlations()
            results["correlations"] = correlation_results

            # Update visualization with new plots
            progress_reporter.report_progress(70, "Creating visualizations...")

            # Create plots (this is a separate task, but we trigger it from here)
            self.execute_task("create_visualization", dataset_name)

            # Update stats panel
            progress_reporter.report_progress(90, "Updating UI...")
            self._update_stats_detailed(dataset_name, results)

            progress_reporter.report_progress(100, "Analysis complete")

            return results

        except Exception as e:
            self._logger.error(f"Error analyzing dataset: {str(e)}")
            progress_reporter.report_progress(100, f"Error: {str(e)}")
            raise

    def _create_visualization_task(self, dataset_name: str, progress_reporter: Any) -> bool:
        """
        Task to create visualizations for a dataset.

        Args:
            dataset_name: Dataset to visualize
            progress_reporter: Progress reporter

        Returns:
            Success status
        """
        if dataset_name not in self._data_frames:
            raise ValueError(f"Dataset not found: {dataset_name}")

        df = self._data_frames[dataset_name]

        # Report starting
        progress_reporter.report_progress(0, "Creating visualizations...")

        try:
            # Use the visualizer to create plots
            if self._visualizer:
                progress_reporter.report_progress(20, "Creating summary plots...")

                # This will create plots in the visualizer widget
                # Notice we don't need to worry about threading - everything just works!
                self._visualizer.create_distribution_plots(df, dataset_name)

                progress_reporter.report_progress(50, "Creating correlation heatmap...")
                self._visualizer.create_correlation_heatmap(df, dataset_name)

                progress_reporter.report_progress(80, "Creating scatter plots...")
                self._visualizer.create_scatter_plots(df, dataset_name)

                progress_reporter.report_progress(100, "Visualizations complete")

            return True

        except Exception as e:
            self._logger.error(f"Error creating visualizations: {str(e)}")
            progress_reporter.report_progress(100, f"Error: {str(e)}")
            raise

    def _detect_trends_task(self, dataset_name: str, progress_reporter: Any) -> Dict[str, Any]:
        """
        Task to detect trends in a dataset.

        Args:
            dataset_name: Dataset to analyze
            progress_reporter: Progress reporter

        Returns:
            Trend analysis results
        """
        if dataset_name not in self._data_frames:
            raise ValueError(f"Dataset not found: {dataset_name}")

        df = self._data_frames[dataset_name]

        # Report starting
        progress_reporter.report_progress(0, "Starting trend detection...")

        # Create results container
        results: Dict[str, Any] = {}

        try:
            # Use trend detector
            progress_reporter.report_progress(20, "Analyzing patterns...")

            trend_detector = TrendDetector(df)
            trends = trend_detector.detect_trends()
            results["trends"] = trends

            # Create trend visualizations
            progress_reporter.report_progress(50, "Creating trend visualizations...")

            if self._visualizer:
                self._visualizer.create_trend_plots(df, dataset_name, trends)

            # Update stats panel
            progress_reporter.report_progress(80, "Updating stats panel...")

            # Get existing stats data
            existing_stats = {}
            if self._current_dataset == dataset_name:
                existing_stats = {"trends": trends}
                self._update_stats_detailed(dataset_name, existing_stats)

            progress_reporter.report_progress(100, "Trend detection complete")

            # Show trend results
            if self._main_widget:
                QMessageBox.information(
                    self._main_widget,
                    "Trend Detection Results",
                    f"Detected {len(trends)} trends in the dataset.\n\n" +
                    "\n".join(f"- {trend}" for trend in trends[:5]) +
                    ("\n..." if len(trends) > 5 else "")
                )

            return results

        except Exception as e:
            self._logger.error(f"Error detecting trends: {str(e)}")
            progress_reporter.report_progress(100, f"Error: {str(e)}")
            raise

    def _handle_app_quit(self) -> None:
        """Handle application quit signal."""
        self._logger.info(f"Plugin {self.name} handling application quit")
        # Perform any urgent cleanup needed before app exits
        self._data_frames.clear()

    def _handle_system_shutdown(self, event: Any) -> None:
        """Handle system shutdown event."""
        self._logger.info(f"Plugin {self.name} received system shutdown")
        self.shutdown()

    def shutdown(self) -> None:
        """Proper shutdown with lifecycle management."""
        # Update lifecycle state
        if hasattr(self, '_logger') and self._logger:
            self._logger.info(f"Plugin {self.name} shutting down")

        # Signal shutdown starting
        self.shutdown_started.emit()

        # Unsubscribe from events
        if hasattr(self, '_event_bus') and self._event_bus:
            subscriber_id = f"{self.name}_system_shutdown"
            self._event_bus.unsubscribe(subscriber_id=subscriber_id)

        # Cancel any running tasks
        with self._plugin_lock:  # Use our correctly defined lock
            for task_id in list(self._running_tasks):
                if hasattr(self, '_task_manager') and self._task_manager:
                    self._task_manager.cancel_task(task_id)
            self._running_tasks.clear()

        # Clear data
        self._data_frames.clear()

        # Clean up UI if needed on main thread
        if hasattr(self, '_ui_registry') and self._ui_registry:
            if hasattr(self, '_thread_manager') and self._thread_manager and \
                    not self._thread_manager.is_main_thread():
                self._thread_manager.execute_on_main_thread_sync(self._ui_registry.cleanup)
            else:
                self._ui_registry.cleanup()

        # Call base implementation
        super().shutdown()
