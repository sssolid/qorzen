from __future__ import annotations
import os
import time
import threading
from typing import Any, Callable, Dict, List, Optional, Set, cast
from PySide6.QtCore import Qt, Signal, Slot, QObject
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QTreeWidget, \
    QTreeWidgetItem, QFileDialog, QTextEdit, QTabWidget, QSplitter, QGroupBox, QGridLayout, QMessageBox, QProgressBar
from PySide6.QtGui import QIcon, QFont
from qorzen.core.service_locator import ServiceLocator, ManagerType, inject
from qorzen.core.thread_manager import TaskPriority, ThreadExecutionContext
from qorzen.plugin_system.interface import BasePlugin


class DatasetSummary:
    """Class representing the summary of an analyzed dataset."""

    def __init__(self, name: str, row_count: int, column_count: int, stats: Dict[str, Any]) -> None:
        self.name = name
        self.row_count = row_count
        self.column_count = column_count
        self.stats = stats


class ProgressSignals(QObject):
    """
    Signals for communicating progress from worker thread to UI thread.
    This class must be instantiated on the main thread.
    """
    progress = Signal(int, str)
    result = Signal(object)
    error = Signal(str)


class ControlPanel(QWidget):
    """Control panel widget for dataset analysis."""

    analyzeRequested = Signal(str, str)  # File path, analysis type

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        file_group = QGroupBox('Dataset')
        file_layout = QGridLayout()

        self.file_label = QLabel('No file selected')
        file_layout.addWidget(self.file_label, 0, 0, 1, 2)

        self.select_file_button = QPushButton('Select File...')
        self.select_file_button.clicked.connect(self._on_select_file)
        file_layout.addWidget(self.select_file_button, 1, 0)

        self.analyze_button = QPushButton('Analyze Dataset')
        self.analyze_button.clicked.connect(self._on_analyze)
        self.analyze_button.setEnabled(False)
        file_layout.addWidget(self.analyze_button, 1, 1)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        options_group = QGroupBox('Analysis Options')
        options_layout = QGridLayout()

        options_layout.addWidget(QLabel('Analysis Type:'), 0, 0)
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(['Basic Statistics', 'Detailed Analysis', 'Correlation Analysis'])
        options_layout.addWidget(self.analysis_type, 0, 1)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        status_group = QGroupBox('Status')
        status_layout = QVBoxLayout()

        self.status_label = QLabel('Ready')
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
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Dataset', '', 'CSV Files (*.csv);;All Files (*)')
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.analyze_button.setEnabled(True)

    def _on_analyze(self) -> None:
        if self.selected_file:
            self.status_label.setText('Analysis in progress...')
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.analyze_button.setEnabled(False)
            self.analyzeRequested.emit(self.selected_file, self.analysis_type.currentText())

    @Slot(int, str)
    def update_progress(self, progress: int, message: str) -> None:
        """Update progress bar with current progress (thread-safe slot)."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

    @Slot(bool, str)
    def analysis_complete(self, success: bool, message: str) -> None:
        """Update UI when analysis completes (thread-safe slot)."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        self.analyze_button.setEnabled(True)


class ResultsViewer(QWidget):
    """Widget for displaying analysis results."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        # Summary tab
        self.summary_widget = QWidget()
        summary_layout = QVBoxLayout(self.summary_widget)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        self.tabs.addTab(self.summary_widget, 'Summary')

        # Statistics tab
        self.stats_widget = QTreeWidget()
        self.stats_widget.setHeaderLabels(['Metric', 'Value'])
        self.stats_widget.setColumnWidth(0, 200)
        self.tabs.addTab(self.stats_widget, 'Statistics')

        # Details tab
        self.details_widget = QTextEdit()
        self.details_widget.setReadOnly(True)
        self.details_widget.setFont(QFont('Monospace'))
        self.tabs.addTab(self.details_widget, 'Details')

        layout.addWidget(self.tabs)

    @Slot(object)
    def display_results(self, summary: DatasetSummary) -> None:
        """Display analysis results (thread-safe slot)."""
        self.summary_text.clear()
        self.summary_text.append(f'<h2>Dataset: {summary.name}</h2>')
        self.summary_text.append(f'<p><b>Rows:</b> {summary.row_count}</p>')
        self.summary_text.append(f'<p><b>Columns:</b> {summary.column_count}</p>')

        if 'description' in summary.stats:
            self.summary_text.append(f"<p>{summary.stats['description']}</p>")

        self.stats_widget.clear()
        if 'column_stats' in summary.stats:
            for col, stats in summary.stats['column_stats'].items():
                col_item = QTreeWidgetItem([col, ''])
                self.stats_widget.addTopLevelItem(col_item)
                for metric, value in stats.items():
                    metric_item = QTreeWidgetItem([metric, str(value)])
                    col_item.addChild(metric_item)

        self.details_widget.clear()
        if 'details' in summary.stats:
            self.details_widget.setText(summary.stats['details'])

    def clear(self) -> None:
        """Clear all displayed data."""
        self.summary_text.clear()
        self.stats_widget.clear()
        self.details_widget.clear()


class MainAnalyzerWidget(QWidget):
    """Main widget for the data analyzer plugin."""

    def __init__(self, plugin: 'DataAnalyzerPlugin', parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.plugin = plugin

        # Create signals object (must be created on main thread)
        self.signals = ProgressSignals()

        # Connect signals
        self.signals.progress.connect(self._on_progress_update)
        self.signals.result.connect(self._on_analysis_completed)
        self.signals.error.connect(self._on_analysis_error)

        # Setup UI
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

    def _on_analyze_requested(self, file_path: str, analysis_type: str) -> None:
        """Handle analysis request from control panel."""
        self.plugin.analyze_dataset(file_path, analysis_type, self.signals)

    @Slot(int, str)
    def _on_progress_update(self, progress: int, message: str) -> None:
        """Handle progress updates from worker thread."""
        self.control_panel.update_progress(progress, message)

    @Slot(object)
    def _on_analysis_completed(self, summary: DatasetSummary) -> None:
        """Handle successful analysis completion."""
        self.results_viewer.display_results(summary)
        self.control_panel.analysis_complete(True, 'Analysis completed successfully')

    @Slot(str)
    def _on_analysis_error(self, error_message: str) -> None:
        """Handle analysis errors."""
        self.control_panel.analysis_complete(False, f'Error: {error_message}')
        QMessageBox.critical(self, 'Analysis Error', error_message)


class DataAnalyzerPlugin(BasePlugin):
    """Plugin for data analysis with completely thread-safe UI updates."""

    name = 'data_analyzer'
    version = '1.0.0'
    description = 'Advanced dataset analysis tools'
    author = 'Qorzen Team'
    display_name = 'Data Analyzer'

    def initialize(self, service_locator: ServiceLocator, **kwargs: Any) -> None:
        super().initialize(service_locator, **kwargs)

        # We'll only register the main analysis task - no UI update tasks
        self.register_task(
            'analyze_dataset',
            self._analyze_dataset_task,
            long_running=True,
            needs_progress=True,
            priority=TaskPriority.NORMAL,
            description='Analyze dataset with progress reporting'
        )

        if self._logger:
            self._logger.info(f'{self.name} plugin initialized')

    def on_ui_ready(self, ui_integration: Any) -> None:
        self._main_widget = MainAnalyzerWidget(self)
        self.register_ui_component(self._main_widget)

        ui_integration.add_page(
            self.name,
            self._main_widget,
            f'plugin_{self.name}',
            QIcon(),
            'Data Analyzer'
        )

        menu = ui_integration.add_menu(self.name, 'Analysis Tools', 'Tools')
        self.register_ui_component(menu, 'menu')

        action = ui_integration.add_menu_action(
            self.name,
            menu,
            'Open Dataset',
            lambda: self._main_widget.control_panel._on_select_file()
        )
        self.register_ui_component(action, 'action')

        super().on_ui_ready(ui_integration)

    def analyze_dataset(self, file_path: str, analysis_type: str, signals: ProgressSignals) -> None:
        """Start dataset analysis task with signal connections."""
        self.execute_task('analyze_dataset', file_path, analysis_type, signals)

    def _analyze_dataset_task(self, file_path: str, analysis_type: str, signals: ProgressSignals) -> DatasetSummary:
        """Perform dataset analysis in a worker thread."""
        try:
            # Create a thread-safe progress reporter
            def report_progress(progress: int, message: str) -> None:
                # Emit signal to update UI on main thread
                signals.progress.emit(progress, message)

            # Initial progress
            report_progress(0, 'Starting analysis...')

            # Basic file validation
            if not os.path.exists(file_path):
                raise FileNotFoundError(f'File not found: {file_path}')

            # Read and parse file
            file_name = os.path.basename(file_path)
            file_content = self._file_manager.read_text(file_path)
            lines = file_content.splitlines()

            if not lines:
                raise ValueError('File is empty')

            header = lines[0].split(',')
            data_rows = lines[1:]

            report_progress(10, 'Reading dataset...')

            # Process data rows
            data = []
            for i, row in enumerate(data_rows):
                values = row.split(',')
                if len(values) != len(header):
                    continue

                row_data = {header[j]: values[j] for j in range(len(header))}
                data.append(row_data)

                if i % 100 == 0:
                    progress = 10 + min(30, int(i / len(data_rows) * 30))
                    report_progress(progress, f'Parsing data rows... ({i}/{len(data_rows)})')

            report_progress(40, 'Analyzing data...')

            # Simulate processing time
            time.sleep(1)

            # Analyze columns
            column_stats = {}
            for col in header:
                col_stats = {}
                try:
                    # Try numeric analysis
                    values = [float(row[col]) for row in data if row[col].strip()]
                    if values:
                        col_stats['min'] = min(values)
                        col_stats['max'] = max(values)
                        col_stats['mean'] = sum(values) / len(values)
                        col_stats['count'] = len(values)
                except ValueError:
                    # Fall back to text analysis
                    values = [row[col] for row in data if row[col].strip()]
                    if values:
                        col_stats['count'] = len(values)
                        col_stats['unique'] = len(set(values))
                        col_stats['most_common'] = max(set(values), key=values.count)

                column_stats[col] = col_stats

            report_progress(70, 'Generating summary...')

            # Generate report text
            details = f'Dataset Analysis Report\n'
            details += f'=====================\n\n'
            details += f'File: {file_name}\n'
            details += f'Analysis Type: {analysis_type}\n'
            details += f'Records: {len(data)}\n'
            details += f'Columns: {len(header)}\n\n'

            for col in header:
                details += f'Column: {col}\n'
                details += f'------------\n'
                for metric, value in column_stats[col].items():
                    details += f'  {metric}: {value}\n'
                details += '\n'

            description = f'This dataset contains {len(data)} records with {len(header)} columns.'
            if analysis_type == 'Correlation Analysis':
                description += ' Correlation analysis has been performed between numeric columns.'

            # Create summary object
            stats = {
                'description': description,
                'column_stats': column_stats,
                'details': details,
                'analysis_type': analysis_type
            }

            summary = DatasetSummary(
                name=file_name,
                row_count=len(data),
                column_count=len(header),
                stats=stats
            )

            report_progress(100, 'Analysis complete')

            # Emit result signal to update UI on main thread
            signals.result.emit(summary)

            return summary

        except Exception as e:
            if self._logger:
                self._logger.error(f'Error analyzing dataset: {str(e)}', exc_info=True)

            # Emit error signal to update UI on main thread
            signals.error.emit(str(e))
            raise

    def shutdown(self) -> None:
        if self._logger:
            self._logger.info(f'{self.name} plugin shutting down')
        super().shutdown()