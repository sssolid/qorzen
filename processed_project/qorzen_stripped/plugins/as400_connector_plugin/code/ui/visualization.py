from __future__ import annotations
'\nData visualization component for AS400 Connector Plugin.\n\nThis module provides visualization capabilities for AS400 query results,\nenabling users to create charts and graphs from their data.\n'
import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import QAbstractTableModel, QItemSelection, QItemSelectionModel, QModelIndex, QObject, QPoint, QSize, Qt, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFrame, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSizePolicy, QSpinBox, QSplitter, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget
from qorzen.plugins.as400_connector_plugin.code.models import ColumnMetadata, QueryResult
class ChartConfigWidget(QWidget):
    chartConfigChanged = Signal()
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._columns: List[ColumnMetadata] = []
        self._numeric_columns: List[str] = []
        self._date_columns: List[str] = []
        self._text_columns: List[str] = []
        self._init_ui()
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        chart_type_group = QGroupBox('Chart Type')
        chart_type_layout = QVBoxLayout(chart_type_group)
        self._chart_type_combo = QComboBox()
        self._chart_type_combo.addItems(['Line Chart', 'Bar Chart', 'Pie Chart', 'Scatter Plot', 'Area Chart'])
        self._chart_type_combo.currentIndexChanged.connect(self._on_config_changed)
        chart_type_layout.addWidget(self._chart_type_combo)
        layout.addWidget(chart_type_group)
        x_axis_group = QGroupBox('X-Axis')
        x_axis_layout = QVBoxLayout(x_axis_group)
        self._x_axis_combo = QComboBox()
        self._x_axis_combo.currentIndexChanged.connect(self._on_config_changed)
        x_axis_layout.addWidget(self._x_axis_combo)
        layout.addWidget(x_axis_group)
        y_axis_group = QGroupBox('Y-Axis')
        y_axis_layout = QVBoxLayout(y_axis_group)
        self._y_axis_combo = QComboBox()
        self._y_axis_combo.currentIndexChanged.connect(self._on_config_changed)
        y_axis_layout.addWidget(self._y_axis_combo)
        layout.addWidget(y_axis_group)
        agg_group = QGroupBox('Aggregation')
        agg_layout = QVBoxLayout(agg_group)
        self._agg_combo = QComboBox()
        self._agg_combo.addItems(['None', 'Sum', 'Average', 'Count', 'Minimum', 'Maximum'])
        self._agg_combo.currentIndexChanged.connect(self._on_config_changed)
        agg_layout.addWidget(self._agg_combo)
        layout.addWidget(agg_group)
        options_group = QGroupBox('Options')
        options_layout = QVBoxLayout(options_group)
        self._show_legend_cb = QCheckBox('Show Legend')
        self._show_legend_cb.setChecked(True)
        self._show_legend_cb.stateChanged.connect(self._on_config_changed)
        self._show_labels_cb = QCheckBox('Show Data Labels')
        self._show_labels_cb.setChecked(False)
        self._show_labels_cb.stateChanged.connect(self._on_config_changed)
        options_layout.addWidget(self._show_legend_cb)
        options_layout.addWidget(self._show_labels_cb)
        layout.addWidget(options_group)
        limit_group = QGroupBox('Data Limits')
        limit_layout = QHBoxLayout(limit_group)
        limit_layout.addWidget(QLabel('Max Data Points:'))
        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(1, 1000)
        self._limit_spin.setValue(50)
        self._limit_spin.valueChanged.connect(self._on_config_changed)
        limit_layout.addWidget(self._limit_spin)
        layout.addWidget(limit_group)
        self._apply_button = QPushButton('Apply')
        self._apply_button.clicked.connect(self.chartConfigChanged)
        layout.addWidget(self._apply_button)
        layout.addStretch()
    def set_columns(self, columns: List[ColumnMetadata]) -> None:
        self._columns = columns
        self._numeric_columns = []
        self._date_columns = []
        self._text_columns = []
        for col in columns:
            col_type = col.type_name.upper()
            if col_type in ('INT', 'INTEGER', 'SMALLINT', 'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL'):
                self._numeric_columns.append(col.name)
            elif col_type in ('DATE', 'TIME', 'TIMESTAMP', 'DATETIME'):
                self._date_columns.append(col.name)
            else:
                self._text_columns.append(col.name)
        self._x_axis_combo.clear()
        self._y_axis_combo.clear()
        for col_name in self._date_columns + self._text_columns + self._numeric_columns:
            self._x_axis_combo.addItem(col_name)
        self._y_axis_combo.addItems(self._numeric_columns)
        self._x_axis_combo.setEnabled(self._x_axis_combo.count() > 0)
        self._y_axis_combo.setEnabled(self._y_axis_combo.count() > 0)
        self._apply_button.setEnabled(self._x_axis_combo.count() > 0 and self._y_axis_combo.count() > 0)
    def _on_config_changed(self) -> None:
        chart_type = self.get_chart_type()
        self._y_axis_combo.setEnabled(chart_type != 'Pie Chart')
        self._agg_combo.setEnabled(chart_type != 'Scatter Plot')
        if chart_type == 'Pie Chart':
            self._apply_button.setEnabled(self._x_axis_combo.count() > 0)
        else:
            self._apply_button.setEnabled(self._x_axis_combo.count() > 0 and self._y_axis_combo.count() > 0)
    def get_chart_type(self) -> str:
        return self._chart_type_combo.currentText()
    def get_x_axis(self) -> str:
        return self._x_axis_combo.currentText()
    def get_y_axis(self) -> str:
        return self._y_axis_combo.currentText()
    def get_aggregation(self) -> str:
        return self._agg_combo.currentText()
    def show_legend(self) -> bool:
        return self._show_legend_cb.isChecked()
    def show_data_labels(self) -> bool:
        return self._show_labels_cb.isChecked()
    def get_data_limit(self) -> int:
        return self._limit_spin.value()
class ChartWidget(QWidget):
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._result: Optional[QueryResult] = None
        self._chart_type: str = 'Line Chart'
        self._x_axis: Optional[str] = None
        self._y_axis: Optional[str] = None
        self._aggregation: str = 'None'
        self._show_legend: bool = True
        self._show_data_labels: bool = False
        self._data_limit: int = 50
        self.setMinimumSize(400, 300)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet('background-color: white;')
    def set_config(self, chart_type: str, x_axis: str, y_axis: str, aggregation: str, show_legend: bool, show_data_labels: bool, data_limit: int) -> None:
        self._chart_type = chart_type
        self._x_axis = x_axis
        self._y_axis = y_axis
        self._aggregation = aggregation
        self._show_legend = show_legend
        self._show_data_labels = show_data_labels
        self._data_limit = data_limit
        self.update()
    def set_data(self, result: QueryResult) -> None:
        self._result = result
        self.update()
    def paintEvent(self, event: Any) -> None:
        if not self._result or not self._x_axis:
            self._paint_placeholder()
            return
        if self._chart_type == 'Pie Chart':
            self._paint_pie_chart()
        elif self._chart_type == 'Bar Chart':
            self._paint_bar_chart()
        elif self._chart_type == 'Line Chart':
            self._paint_line_chart()
        elif self._chart_type == 'Scatter Plot':
            self._paint_scatter_plot()
        elif self._chart_type == 'Area Chart':
            self._paint_area_chart()
        else:
            self._paint_placeholder()
    def _paint_placeholder(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(QFont('Arial', 14))
        if not self._result:
            message = 'No data available for visualization'
        elif not self._x_axis:
            message = 'Configure chart settings to visualize data'
        else:
            message = 'Chart type not supported'
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, message)
    def _paint_pie_chart(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))
        painter.setBrush(QColor(200, 200, 200))
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) * 0.8
        painter.setFont(QFont('Arial', 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Pie Chart Visualization\n(Placeholder - would use actual data in production)')
    def _paint_bar_chart(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont('Arial', 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Bar Chart Visualization\n(Placeholder - would use actual data in production)')
    def _paint_line_chart(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont('Arial', 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Line Chart Visualization\n(Placeholder - would use actual data in production)')
    def _paint_scatter_plot(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont('Arial', 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Scatter Plot Visualization\n(Placeholder - would use actual data in production)')
    def _paint_area_chart(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont('Arial', 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Area Chart Visualization\n(Placeholder - would use actual data in production)')
class VisualizationView(QWidget):
    def __init__(self, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._result: Optional[QueryResult] = None
        self._init_ui()
    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        export_action = QAction('Export Chart', self)
        export_action.setToolTip('Export chart as image')
        export_action.triggered.connect(self._export_chart)
        toolbar.addAction(export_action)
        toolbar.addSeparator()
        self._status_label = QLabel('No data loaded')
        toolbar.addWidget(self._status_label)
        main_layout.addWidget(toolbar)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._config_widget = ChartConfigWidget()
        self._config_widget.chartConfigChanged.connect(self._update_chart)
        self._chart_widget = ChartWidget()
        splitter.addWidget(self._config_widget)
        splitter.addWidget(self._chart_widget)
        splitter.setSizes([200, 600])
        main_layout.addWidget(splitter)
    def set_query_result(self, result: QueryResult) -> None:
        self._result = result
        self._config_widget.set_columns(result.columns)
        self._chart_widget.set_data(result)
        self._status_label.setText(f'Loaded {result.row_count} rows for visualization')
    def _update_chart(self) -> None:
        if not self._result:
            return
        chart_type = self._config_widget.get_chart_type()
        x_axis = self._config_widget.get_x_axis()
        y_axis = self._config_widget.get_y_axis()
        aggregation = self._config_widget.get_aggregation()
        show_legend = self._config_widget.show_legend()
        show_data_labels = self._config_widget.show_data_labels()
        data_limit = self._config_widget.get_data_limit()
        self._chart_widget.set_config(chart_type, x_axis, y_axis, aggregation, show_legend, show_data_labels, data_limit)
        self._status_label.setText(f'Visualizing {x_axis} vs {y_axis} ({aggregation})' if aggregation != 'None' and chart_type != 'Pie Chart' else f'Visualizing {x_axis}' if chart_type == 'Pie Chart' else f'Visualizing {x_axis} vs {y_axis}')
    def _export_chart(self) -> None:
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(self._chart_widget.size())
        self._chart_widget.render(pixmap)
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(self, 'Export Chart', '', 'PNG Images (*.png);;JPEG Images (*.jpg);;BMP Images (*.bmp)')
        if file_path:
            if not pixmap.save(file_path):
                QMessageBox.critical(self, 'Export Error', 'Failed to save chart image')
            else:
                self._status_label.setText(f'Chart exported to {file_path}')