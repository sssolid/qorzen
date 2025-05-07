from __future__ import annotations

"""
Data visualization component for AS400 Connector Plugin.

This module provides visualization capabilities for AS400 query results,
enabling users to create charts and graphs from their data.
"""

import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from PySide6.QtCore import (
    QAbstractTableModel,
    QItemSelection,
    QItemSelectionModel,
    QModelIndex,
    QObject,
    QPoint,
    QSize,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from qorzen.plugins.as400_connector_plugin.code.models import ColumnMetadata, QueryResult


class ChartConfigWidget(QWidget):
    """
    Widget for configuring chart settings.

    This widget allows users to select columns for X and Y axes,
    chart type, and other visualization settings.
    """

    chartConfigChanged = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the chart configuration widget."""
        super().__init__(parent)

        self._columns: List[ColumnMetadata] = []
        self._numeric_columns: List[str] = []
        self._date_columns: List[str] = []
        self._text_columns: List[str] = []

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Chart type selector
        chart_type_group = QGroupBox("Chart Type")
        chart_type_layout = QVBoxLayout(chart_type_group)

        self._chart_type_combo = QComboBox()
        self._chart_type_combo.addItems([
            "Line Chart",
            "Bar Chart",
            "Pie Chart",
            "Scatter Plot",
            "Area Chart"
        ])
        self._chart_type_combo.currentIndexChanged.connect(self._on_config_changed)

        chart_type_layout.addWidget(self._chart_type_combo)
        layout.addWidget(chart_type_group)

        # X-axis selector
        x_axis_group = QGroupBox("X-Axis")
        x_axis_layout = QVBoxLayout(x_axis_group)

        self._x_axis_combo = QComboBox()
        self._x_axis_combo.currentIndexChanged.connect(self._on_config_changed)

        x_axis_layout.addWidget(self._x_axis_combo)
        layout.addWidget(x_axis_group)

        # Y-axis selector
        y_axis_group = QGroupBox("Y-Axis")
        y_axis_layout = QVBoxLayout(y_axis_group)

        self._y_axis_combo = QComboBox()
        self._y_axis_combo.currentIndexChanged.connect(self._on_config_changed)

        y_axis_layout.addWidget(self._y_axis_combo)
        layout.addWidget(y_axis_group)

        # Aggregation options
        agg_group = QGroupBox("Aggregation")
        agg_layout = QVBoxLayout(agg_group)

        self._agg_combo = QComboBox()
        self._agg_combo.addItems([
            "None",
            "Sum",
            "Average",
            "Count",
            "Minimum",
            "Maximum"
        ])
        self._agg_combo.currentIndexChanged.connect(self._on_config_changed)

        agg_layout.addWidget(self._agg_combo)
        layout.addWidget(agg_group)

        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self._show_legend_cb = QCheckBox("Show Legend")
        self._show_legend_cb.setChecked(True)
        self._show_legend_cb.stateChanged.connect(self._on_config_changed)

        self._show_labels_cb = QCheckBox("Show Data Labels")
        self._show_labels_cb.setChecked(False)
        self._show_labels_cb.stateChanged.connect(self._on_config_changed)

        options_layout.addWidget(self._show_legend_cb)
        options_layout.addWidget(self._show_labels_cb)
        layout.addWidget(options_group)

        # Limit data points
        limit_group = QGroupBox("Data Limits")
        limit_layout = QHBoxLayout(limit_group)

        limit_layout.addWidget(QLabel("Max Data Points:"))

        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(1, 1000)
        self._limit_spin.setValue(50)
        self._limit_spin.valueChanged.connect(self._on_config_changed)

        limit_layout.addWidget(self._limit_spin)
        layout.addWidget(limit_group)

        # Apply button
        self._apply_button = QPushButton("Apply")
        self._apply_button.clicked.connect(self.chartConfigChanged)
        layout.addWidget(self._apply_button)

        layout.addStretch()

    def set_columns(self, columns: List[ColumnMetadata]) -> None:
        """
        Set the available columns for chart configuration.

        Args:
            columns: The list of columns from the query result
        """
        self._columns = columns

        # Categorize columns by data type
        self._numeric_columns = []
        self._date_columns = []
        self._text_columns = []

        for col in columns:
            col_type = col.type_name.upper()
            if col_type in ("INT", "INTEGER", "SMALLINT", "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL"):
                self._numeric_columns.append(col.name)
            elif col_type in ("DATE", "TIME", "TIMESTAMP", "DATETIME"):
                self._date_columns.append(col.name)
            else:
                self._text_columns.append(col.name)

        # Update combo boxes
        self._x_axis_combo.clear()
        self._y_axis_combo.clear()

        # X-axis can be date, text, or numeric
        for col_name in self._date_columns + self._text_columns + self._numeric_columns:
            self._x_axis_combo.addItem(col_name)

        # Y-axis should be numeric
        self._y_axis_combo.addItems(self._numeric_columns)

        # Enable/disable based on available columns
        self._x_axis_combo.setEnabled(self._x_axis_combo.count() > 0)
        self._y_axis_combo.setEnabled(self._y_axis_combo.count() > 0)

        self._apply_button.setEnabled(
            self._x_axis_combo.count() > 0 and self._y_axis_combo.count() > 0
        )

    def _on_config_changed(self) -> None:
        """Handle configuration changes."""
        # Update UI based on chart type
        chart_type = self.get_chart_type()

        # Pie charts only need one dimension
        self._y_axis_combo.setEnabled(chart_type != "Pie Chart")

        # Scatter plots don't use aggregation
        self._agg_combo.setEnabled(chart_type != "Scatter Plot")

        # Enable Apply button if we have enough data for the selected chart type
        if chart_type == "Pie Chart":
            self._apply_button.setEnabled(self._x_axis_combo.count() > 0)
        else:
            self._apply_button.setEnabled(
                self._x_axis_combo.count() > 0 and self._y_axis_combo.count() > 0
            )

    def get_chart_type(self) -> str:
        """Return the selected chart type."""
        return self._chart_type_combo.currentText()

    def get_x_axis(self) -> str:
        """Return the selected X-axis column."""
        return self._x_axis_combo.currentText()

    def get_y_axis(self) -> str:
        """Return the selected Y-axis column."""
        return self._y_axis_combo.currentText()

    def get_aggregation(self) -> str:
        """Return the selected aggregation method."""
        return self._agg_combo.currentText()

    def show_legend(self) -> bool:
        """Return whether to show the legend."""
        return self._show_legend_cb.isChecked()

    def show_data_labels(self) -> bool:
        """Return whether to show data labels."""
        return self._show_labels_cb.isChecked()

    def get_data_limit(self) -> int:
        """Return the maximum number of data points to display."""
        return self._limit_spin.value()


class ChartWidget(QWidget):
    """
    Widget for displaying a chart.

    This widget renders the chart based on the configuration and data.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the chart widget."""
        super().__init__(parent)

        self._result: Optional[QueryResult] = None
        self._chart_type: str = "Line Chart"
        self._x_axis: Optional[str] = None
        self._y_axis: Optional[str] = None
        self._aggregation: str = "None"
        self._show_legend: bool = True
        self._show_data_labels: bool = False
        self._data_limit: int = 50

        # Set fixed size for the chart area
        self.setMinimumSize(400, 300)

        # Enable painting
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")

    def set_config(self,
                   chart_type: str,
                   x_axis: str,
                   y_axis: str,
                   aggregation: str,
                   show_legend: bool,
                   show_data_labels: bool,
                   data_limit: int) -> None:
        """
        Set the chart configuration.

        Args:
            chart_type: The type of chart to display
            x_axis: The column to use for X-axis
            y_axis: The column to use for Y-axis
            aggregation: The aggregation method to apply
            show_legend: Whether to show the legend
            show_data_labels: Whether to show data labels
            data_limit: Maximum number of data points to display
        """
        self._chart_type = chart_type
        self._x_axis = x_axis
        self._y_axis = y_axis
        self._aggregation = aggregation
        self._show_legend = show_legend
        self._show_data_labels = show_data_labels
        self._data_limit = data_limit

        # Update the chart
        self.update()

    def set_data(self, result: QueryResult) -> None:
        """
        Set the data for the chart.

        Args:
            result: The query result containing the data
        """
        self._result = result

        # Update the chart
        self.update()

    def paintEvent(self, event: Any) -> None:
        """
        Paint the chart.

        Args:
            event: The paint event
        """
        if not self._result or not self._x_axis:
            self._paint_placeholder()
            return

        # Process data for the chart
        if self._chart_type == "Pie Chart":
            self._paint_pie_chart()
        elif self._chart_type == "Bar Chart":
            self._paint_bar_chart()
        elif self._chart_type == "Line Chart":
            self._paint_line_chart()
        elif self._chart_type == "Scatter Plot":
            self._paint_scatter_plot()
        elif self._chart_type == "Area Chart":
            self._paint_area_chart()
        else:
            self._paint_placeholder()

    def _paint_placeholder(self) -> None:
        """Paint a placeholder when no chart can be displayed."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        # Draw text
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(QFont("Arial", 14))

        if not self._result:
            message = "No data available for visualization"
        elif not self._x_axis:
            message = "Configure chart settings to visualize data"
        else:
            message = "Chart type not supported"

        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, message)

    def _paint_pie_chart(self) -> None:
        """Paint a pie chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # This is a placeholder. In a real implementation, you would:
        # 1. Process the data (aggregate values by category)
        # 2. Calculate percentages
        # 3. Assign colors
        # 4. Draw pie slices
        # 5. Add labels and legend

        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))
        painter.setBrush(QColor(200, 200, 200))

        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) * 0.8

        # Draw text explaining this is a placeholder
        painter.setFont(QFont("Arial", 10))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Pie Chart Visualization\n(Placeholder - would use actual data in production)"
        )

    def _paint_bar_chart(self) -> None:
        """Paint a bar chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # This is a placeholder. In a real implementation, you would:
        # 1. Process the data (calculate bar heights)
        # 2. Set up scales for axes
        # 3. Draw axes and grid
        # 4. Draw bars with appropriate colors
        # 5. Add labels and legend

        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))

        # Draw text explaining this is a placeholder
        painter.setFont(QFont("Arial", 10))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Bar Chart Visualization\n(Placeholder - would use actual data in production)"
        )

    def _paint_line_chart(self) -> None:
        """Paint a line chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # This is a placeholder. In a real implementation, you would:
        # 1. Process the data (sort by x-axis, calculate points)
        # 2. Set up scales for axes
        # 3. Draw axes and grid
        # 4. Draw lines connecting points
        # 5. Add labels and legend

        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))

        # Draw text explaining this is a placeholder
        painter.setFont(QFont("Arial", 10))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Line Chart Visualization\n(Placeholder - would use actual data in production)"
        )

    def _paint_scatter_plot(self) -> None:
        """Paint a scatter plot."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # This is a placeholder. In a real implementation, you would:
        # 1. Process the data (calculate point positions)
        # 2. Set up scales for axes
        # 3. Draw axes and grid
        # 4. Draw points with appropriate colors
        # 5. Add labels and legend

        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))

        # Draw text explaining this is a placeholder
        painter.setFont(QFont("Arial", 10))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Scatter Plot Visualization\n(Placeholder - would use actual data in production)"
        )

    def _paint_area_chart(self) -> None:
        """Paint an area chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # This is a placeholder. In a real implementation, you would:
        # 1. Process the data (sort by x-axis, calculate points)
        # 2. Set up scales for axes
        # 3. Draw axes and grid
        # 4. Draw filled areas
        # 5. Add labels and legend

        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))

        # Draw text explaining this is a placeholder
        painter.setFont(QFont("Arial", 10))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Area Chart Visualization\n(Placeholder - would use actual data in production)"
        )


class VisualizationView(QWidget):
    """
    Main view for data visualization.

    This widget combines the chart configuration panel and the chart display.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the visualization view."""
        super().__init__(parent)

        self._result: Optional[QueryResult] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)

        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))

        export_action = QAction("Export Chart", self)
        export_action.setToolTip("Export chart as image")
        export_action.triggered.connect(self._export_chart)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        self._status_label = QLabel("No data loaded")
        toolbar.addWidget(self._status_label)

        main_layout.addWidget(toolbar)

        # Create splitter for config and chart
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Config panel
        self._config_widget = ChartConfigWidget()
        self._config_widget.chartConfigChanged.connect(self._update_chart)

        # Chart display
        self._chart_widget = ChartWidget()

        splitter.addWidget(self._config_widget)
        splitter.addWidget(self._chart_widget)

        # Set initial sizes
        splitter.setSizes([200, 600])

        main_layout.addWidget(splitter)

    def set_query_result(self, result: QueryResult) -> None:
        """
        Set the query result to visualize.

        Args:
            result: The QueryResult to visualize
        """
        self._result = result

        # Update the config widget with available columns
        self._config_widget.set_columns(result.columns)

        # Update chart with data
        self._chart_widget.set_data(result)

        # Update status
        self._status_label.setText(
            f"Loaded {result.row_count} rows for visualization"
        )

    def _update_chart(self) -> None:
        """Update the chart based on current configuration."""
        if not self._result:
            return

        # Get configuration
        chart_type = self._config_widget.get_chart_type()
        x_axis = self._config_widget.get_x_axis()
        y_axis = self._config_widget.get_y_axis()
        aggregation = self._config_widget.get_aggregation()
        show_legend = self._config_widget.show_legend()
        show_data_labels = self._config_widget.show_data_labels()
        data_limit = self._config_widget.get_data_limit()

        # Update chart
        self._chart_widget.set_config(
            chart_type,
            x_axis,
            y_axis,
            aggregation,
            show_legend,
            show_data_labels,
            data_limit
        )

        # Update status
        self._status_label.setText(
            f"Visualizing {x_axis} vs {y_axis} ({aggregation})"
            if aggregation != "None" and chart_type != "Pie Chart"
            else f"Visualizing {x_axis}"
            if chart_type == "Pie Chart"
            else f"Visualizing {x_axis} vs {y_axis}"
        )

    def _export_chart(self) -> None:
        """Export the current chart as an image."""
        from PySide6.QtGui import QPixmap

        # Capture the chart as an image
        pixmap = QPixmap(self._chart_widget.size())
        self._chart_widget.render(pixmap)

        # Ask for file name
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            "",
            "PNG Images (*.png);;JPEG Images (*.jpg);;BMP Images (*.bmp)"
        )

        if file_path:
            # Save the image
            if not pixmap.save(file_path):
                QMessageBox.critical(
                    self,
                    "Export Error",
                    "Failed to save chart image"
                )
            else:
                self._status_label.setText(f"Chart exported to {file_path}")