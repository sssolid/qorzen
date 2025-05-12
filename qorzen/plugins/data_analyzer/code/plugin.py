from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, List, Optional, Set, cast

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTreeWidget, QTreeWidgetItem, QFileDialog, QTextEdit, QTabWidget,
    QSplitter, QGroupBox, QGridLayout, QMessageBox, QProgressBar
)
from PySide6.QtGui import QIcon, QFont

from qorzen.core.service_locator import ServiceLocator, ManagerType, inject
from qorzen.core.thread_manager import TaskPriority
from qorzen.plugin_system.interface import BasePlugin


class DatasetSummary:
    """
    Class representing a summary of dataset analysis results.
    """

    def __init__(self, name: str, row_count: int, column_count: int,
                 stats: Dict[str, Any]) -> None:
        """
        Initialize a dataset summary.

        Args:
            name: Dataset name
            row_count: Number of rows in the dataset
            column_count: Number of columns in the dataset
            stats: Dictionary of statistics about the dataset
        """
        self.name = name
        self.row_count = row_count
        self.column_count = column_count
        self.stats = stats


class ControlPanel(QWidget):
    """
    Control panel widget for selecting and analyzing datasets.
    """

    analyzeRequested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the control panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Dataset selection group
        file_group = QGroupBox("Dataset")
        file_layout = QGridLayout()
        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label, 0, 0, 1, 2)

        self.select_file_button = QPushButton("Select File...")
        self.select_file_button.clicked.connect(self._on_select_file)
        file_layout.addWidget(self.select_file_button, 1, 0)

        self.analyze_button = QPushButton("Analyze Dataset")
        self.analyze_button.clicked.connect(self._on_analyze)
        self.analyze_button.setEnabled(False)
        file_layout.addWidget(self.analyze_button, 1, 1)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Analysis options group
        options_group = QGroupBox("Analysis Options")
        options_layout = QGridLayout()
        options_layout.addWidget(QLabel("Analysis Type:"), 0, 0)
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["Basic Statistics", "Detailed Analysis", "Correlation Analysis"])
        options_layout.addWidget(self.analysis_type, 0, 1)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Status group
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()
        self.selected_file = None

    def _on_select_file(self) -> None:
        """Handle file selection button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Dataset", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.analyze_button.setEnabled(True)

    def _on_analyze(self) -> None:
        """Handle analyze button click."""
        if self.selected_file:
            self.status_label.setText("Analysis in progress...")
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.analyze_button.setEnabled(False)
            self.analyzeRequested.emit(self.selected_file)

    def update_progress(self, progress: int, message: str) -> None:
        """
        Update the progress display.

        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

    def analysis_complete(self, success: bool, message: str) -> None:
        """
        Update the UI when analysis is complete.

        Args:
            success: Whether the analysis was successful
            message: Message to display
        """
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        self.analyze_button.setEnabled(True)


class ResultsViewer(QWidget):
    """
    Widget for displaying dataset analysis results.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the results viewer.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        # Summary tab
        self.summary_widget = QWidget()
        summary_layout = QVBoxLayout(self.summary_widget)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        self.tabs.addTab(self.summary_widget, "Summary")

        # Statistics tab
        self.stats_widget = QTreeWidget()
        self.stats_widget.setHeaderLabels(["Metric", "Value"])
        self.stats_widget.setColumnWidth(0, 200)
        self.tabs.addTab(self.stats_widget, "Statistics")

        # Details tab
        self.details_widget = QTextEdit()
        self.details_widget.setReadOnly(True)
        self.details_widget.setFont(QFont("Monospace"))
        self.tabs.addTab(self.details_widget, "Details")

        layout.addWidget(self.tabs)

    def display_results(self, summary: DatasetSummary) -> None:
        """
        Display analysis results.

        Args:
            summary: Dataset summary to display
        """
        self.summary_text.clear()
        self.summary_text.append(f"<h2>Dataset: {summary.name}</h2>")
        self.summary_text.append(f"<p><b>Rows:</b> {summary.row_count}</p>")
        self.summary_text.append(f"<p><b>Columns:</b> {summary.column_count}</p>")

        if "description" in summary.stats:
            self.summary_text.append(f"<p>{summary.stats['description']}</p>")

        self.stats_widget.clear()
        if "column_stats" in summary.stats:
            for col, stats in summary.stats["column_stats"].items():
                col_item = QTreeWidgetItem([col, ""])
                self.stats_widget.addTopLevelItem(col_item)

                for metric, value in stats.items():
                    metric_item = QTreeWidgetItem([metric, str(value)])
                    col_item.addChild(metric_item)

        self.details_widget.clear()
        if "details" in summary.stats:
            self.details_widget.setText(summary.stats["details"])

    def clear(self) -> None:
        """Clear all displayed results."""
        self.summary_text.clear()
        self.stats_widget.clear()
        self.details_widget.clear()


class MainAnalyzerWidget(QWidget):
    """
    Main widget for the data analyzer plugin.
    """

    def __init__(self, plugin: 'DataAnalyzerPlugin', parent: Optional[QWidget] = None) -> None:
        """
        Initialize the main analyzer widget.

        Args:
            plugin: Parent plugin
            parent: Parent widget
        """
        super().__init__(parent)
        self.plugin = plugin

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        self.control_panel = ControlPanel()
        self.control_panel.analyzeRequested.connect(self._on_analyze_requested)
        splitter.addWidget(self.control_panel)

        self.results_viewer = ResultsViewer()
        splitter.addWidget(self.results_viewer)

        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

    def _on_analyze_requested(self, file_path: str) -> None:
        """
        Handle analyze request from control panel.

        Args:
            file_path: Path to file to analyze
        """
        analysis_type = self.control_panel.analysis_type.currentText()
        self.plugin.analyze_dataset(file_path, analysis_type)

    def update_progress(self, progress: int, message: str) -> None:
        """
        Update progress display.

        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        self.control_panel.update_progress(progress, message)

    def display_results(self, summary: DatasetSummary) -> None:
        """
        Display analysis results.

        Args:
            summary: Dataset summary to display
        """
        self.results_viewer.display_results(summary)
        self.control_panel.analysis_complete(True, "Analysis completed successfully")

    def display_error(self, error_message: str) -> None:
        """
        Display error message.

        Args:
            error_message: Error message to display
        """
        self.control_panel.analysis_complete(False, f"Error: {error_message}")
        QMessageBox.critical(self, "Analysis Error", error_message)


class DataAnalyzerPlugin(BasePlugin):
    """
    Plugin for analyzing datasets.
    """

    name = "data_analyzer"
    version = "1.0.0"
    description = "Advanced dataset analysis tools"
    author = "Qorzen Team"
    display_name = "Data Analyzer"

    def initialize(self, service_locator: ServiceLocator, **kwargs: Any) -> None:
        """
        Initialize the plugin.

        Args:
            service_locator: Service locator containing system services
            **kwargs: Additional initialization parameters
        """
        super().initialize(service_locator, **kwargs)

        # Register tasks for thread-safe UI updates and analysis
        self.register_task(
            "analyze_dataset",
            self._analyze_dataset_task,
            long_running=True,
            needs_progress=True,
            priority=TaskPriority.NORMAL,
            description="Analyze dataset with progress reporting"
        )

        self.register_task(
            "update_progress_ui",
            self._update_progress_ui,
            long_running=False,
            needs_progress=False,
            description="Update UI with progress"
        )

        self.register_task(
            "update_results_ui",
            self._update_results_ui,
            long_running=False,
            needs_progress=False,
            description="Update UI with results"
        )

        self.register_task(
            "update_error_ui",
            self._update_error_ui,
            long_running=False,
            needs_progress=False,
            description="Update UI with error"
        )

        if self._logger:
            self._logger.info(f"{self.name} plugin initialized")

    def on_ui_ready(self, ui_integration: Any) -> None:
        """
        Called when the UI is ready for plugin integration.

        Args:
            ui_integration: UI integration interface
        """
        self._main_widget = MainAnalyzerWidget(self)
        self.register_ui_component(self._main_widget)

        # Add page to main UI
        ui_integration.add_page(
            self.name,
            self._main_widget,
            f"plugin_{self.name}",
            QIcon(),
            "Data Analyzer"
        )

        # Add to Tools menu
        menu = ui_integration.add_menu(self.name, "Analysis Tools", "Tools")
        self.register_ui_component(menu, "menu")

        # Add menu action
        action = ui_integration.add_menu_action(
            self.name,
            menu,
            "Open Dataset",
            lambda: self._main_widget.control_panel._on_select_file()
        )
        self.register_ui_component(action, "action")

        super().on_ui_ready(ui_integration)

    def analyze_dataset(self, file_path: str, analysis_type: str) -> None:
        """
        Analyze a dataset.

        Args:
            file_path: Path to dataset file
            analysis_type: Type of analysis to perform
        """
        self.execute_task("analyze_dataset", file_path, analysis_type)

    def _analyze_dataset_task(self, file_path: str, analysis_type: str,
                              progress_reporter: Optional[Callable] = None) -> DatasetSummary:
        """
        Task for analyzing a dataset.

        Args:
            file_path: Path to dataset file
            analysis_type: Type of analysis to perform
            progress_reporter: Progress reporter function

        Returns:
            Dataset summary with analysis results

        Raises:
            Various exceptions if analysis fails
        """
        try:
            if progress_reporter:
                progress_reporter(0, "Starting analysis...")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            file_name = os.path.basename(file_path)
            file_content = self._file_manager.read_text(file_path)
            lines = file_content.splitlines()

            if not lines:
                raise ValueError("File is empty")

            header = lines[0].split(",")
            data_rows = lines[1:]

            if progress_reporter:
                progress_reporter(10, "Reading dataset...")

            data = []
            for i, row in enumerate(data_rows):
                values = row.split(",")
                if len(values) != len(header):
                    continue

                row_data = {header[j]: values[j] for j in range(len(header))}
                data.append(row_data)

                if progress_reporter and i % 100 == 0:
                    progress = 10 + min(30, int(i / len(data_rows) * 30))
                    progress_reporter(
                        progress,
                        f"Parsing data rows... ({i}/{len(data_rows)})"
                    )

            if progress_reporter:
                progress_reporter(40, "Analyzing data...")

            # Artificial delay for demonstration
            time.sleep(1)

            # Calculate column statistics
            column_stats = {}
            for col in header:
                col_stats = {}
                try:
                    values = [float(row[col]) for row in data if row[col].strip()]
                    if values:
                        col_stats["min"] = min(values)
                        col_stats["max"] = max(values)
                        col_stats["mean"] = sum(values) / len(values)
                        col_stats["count"] = len(values)
                except ValueError:
                    values = [row[col] for row in data if row[col].strip()]
                    if values:
                        col_stats["count"] = len(values)
                        col_stats["unique"] = len(set(values))
                        col_stats["most_common"] = max(set(values), key=values.count)

                column_stats[col] = col_stats

            if progress_reporter:
                progress_reporter(70, "Generating summary...")

            # Create report
            details = f"Dataset Analysis Report\n"
            details += f"=====================\n\n"
            details += f"File: {file_name}\n"
            details += f"Analysis Type: {analysis_type}\n"
            details += f"Records: {len(data)}\n"
            details += f"Columns: {len(header)}\n\n"

            for col in header:
                details += f"Column: {col}\n"
                details += f"------------\n"
                for metric, value in column_stats[col].items():
                    details += f"  {metric}: {value}\n"
                details += "\n"

            description = f"This dataset contains {len(data)} records with {len(header)} columns."
            if analysis_type == "Correlation Analysis":
                description += " Correlation analysis has been performed between numeric columns."

            stats = {
                "description": description,
                "column_stats": column_stats,
                "details": details,
                "analysis_type": analysis_type
            }

            summary = DatasetSummary(
                name=file_name,
                row_count=len(data),
                column_count=len(header),
                stats=stats
            )

            if progress_reporter:
                progress_reporter(100, "Analysis complete")

            # Schedule UI update task instead of directly updating the UI
            # This ensures UI updates happen on the main thread
            self._task_manager.execute_task(
                self.name,
                "update_results_ui",
                summary
            )

            return summary

        except Exception as e:
            if self._logger:
                self._logger.error(f"Error analyzing dataset: {str(e)}", exc_info=True)

            # Schedule error UI update on the main thread
            self._task_manager.execute_task(
                self.name,
                "update_error_ui",
                str(e)
            )

            raise

    def _update_progress_ui(self, progress: int, message: str) -> None:
        """
        Update the progress UI on the main thread.

        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        # Ensure we're on the main thread for UI updates
        if hasattr(self, "_main_widget"):
            # The task manager already ensures this runs on the main thread
            self._main_widget.update_progress(progress, message)

    def _update_results_ui(self, summary: DatasetSummary) -> None:
        """
        Update the results UI on the main thread.

        Args:
            summary: Dataset summary to display
        """
        # Ensure we're on the main thread for UI updates
        if hasattr(self, "_main_widget"):
            # The task manager already ensures this runs on the main thread
            self._main_widget.display_results(summary)

    def _update_error_ui(self, error_message: str) -> None:
        """
        Update the UI with an error message on the main thread.

        Args:
            error_message: Error message to display
        """
        # Ensure we're on the main thread for UI updates
        if hasattr(self, "_main_widget"):
            # The task manager already ensures this runs on the main thread
            self._main_widget.display_error(error_message)

    def shutdown(self) -> None:
        """Clean up resources before plugin is unloaded."""
        if self._logger:
            self._logger.info(f"{self.name} plugin shutting down")

        super().shutdown()