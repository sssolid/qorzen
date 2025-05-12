# qorzen/plugins/data_explorer/widgets/visualizer.py
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QScrollArea, QLabel, QTabWidget, QSplitter
)


class MatplotlibCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for embedding in Qt."""

    def __init__(self, width: int = 5, height: int = 4, dpi: int = 100) -> None:
        """
        Initialize matplotlib canvas.

        Args:
            width: Figure width in inches
            height: Figure height in inches
            dpi: Figure resolution
        """
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class DataVisualizerWidget(QWidget):
    """Widget for visualizing data with charts and plots."""

    def __init__(self) -> None:
        """Initialize data visualizer widget."""
        super().__init__()

        # Store current dataframe
        self._df: Optional[pd.DataFrame] = None
        self._dataset_name: Optional[str] = None

        # Set up layout
        main_layout = QVBoxLayout(self)

        # Create tabs for different visualization types
        self._tabs = QTabWidget()

        # Create tab for distribution plots
        self._distrib_tab = QWidget()
        distrib_layout = QVBoxLayout(self._distrib_tab)

        # Add controls for distribution plots
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Column:"))
        self._column_selector = QComboBox()
        self._column_selector.currentIndexChanged.connect(self._on_column_changed)
        controls_layout.addWidget(self._column_selector)

        controls_layout.addWidget(QLabel("Plot Type:"))
        self._plot_type = QComboBox()
        self._plot_type.addItems(["Histogram", "Box Plot", "Violin Plot", "KDE Plot"])
        self._plot_type.currentIndexChanged.connect(self._on_plot_type_changed)
        controls_layout.addWidget(self._plot_type)

        controls_layout.addStretch()
        distrib_layout.addLayout(controls_layout)

        # Create canvas for distribution plots
        self._distrib_canvas = MatplotlibCanvas()
        distrib_layout.addWidget(self._distrib_canvas)

        # Add distribution tab
        self._tabs.addTab(self._distrib_tab, "Distributions")

        # Create tab for correlation plots
        self._corr_tab = QWidget()
        corr_layout = QVBoxLayout(self._corr_tab)

        # Create canvas for correlation heatmap
        self._corr_canvas = MatplotlibCanvas()
        corr_layout.addWidget(self._corr_canvas)

        # Add correlation tab
        self._tabs.addTab(self._corr_tab, "Correlations")

        # Create tab for scatter plots
        self._scatter_tab = QWidget()
        scatter_layout = QVBoxLayout(self._scatter_tab)

        # Add controls for scatter plots
        scatter_controls = QHBoxLayout()
        scatter_controls.addWidget(QLabel("X Column:"))
        self._x_column = QComboBox()
        scatter_controls.addWidget(self._x_column)

        scatter_controls.addWidget(QLabel("Y Column:"))
        self._y_column = QComboBox()
        scatter_controls.addWidget(self._y_column)

        update_button = QPushButton("Update Plot")
        update_button.clicked.connect(self._update_scatter_plot)
        scatter_controls.addWidget(update_button)

        scatter_controls.addStretch()
        scatter_layout.addLayout(scatter_controls)

        # Create canvas for scatter plots
        self._scatter_canvas = MatplotlibCanvas()
        scatter_layout.addWidget(self._scatter_canvas)

        # Add scatter tab
        self._tabs.addTab(self._scatter_tab, "Scatter Plots")

        # Create tab for trend plots
        self._trend_tab = QWidget()
        trend_layout = QVBoxLayout(self._trend_tab)

        # Create canvas for trend plots
        self._trend_canvas = MatplotlibCanvas()
        trend_layout.addWidget(self._trend_canvas)

        # Add trend tab
        self._tabs.addTab(self._trend_tab, "Trends")

        # Add tabs to main layout
        main_layout.addWidget(self._tabs)

    def set_dataframe(self, df: pd.DataFrame, dataset_name: str) -> None:
        """
        Set dataframe for visualization.

        Args:
            df: DataFrame to visualize
            dataset_name: Dataset name
        """
        self._df = df
        self._dataset_name = dataset_name

        # Update column selectors
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        self._column_selector.clear()
        self._column_selector.addItems(numeric_columns)

        self._x_column.clear()
        self._x_column.addItems(numeric_columns)

        self._y_column.clear()
        self._y_column.addItems(numeric_columns)
        if len(numeric_columns) > 1:
            self._y_column.setCurrentIndex(1)

    def create_distribution_plots(self, df: pd.DataFrame, dataset_name: str) -> None:
        """
        Create distribution plots for the dataset.

        Args:
            df: DataFrame to visualize
            dataset_name: Dataset name
        """
        self._df = df
        self._dataset_name = dataset_name

        # Set columns in selector
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        self._column_selector.clear()
        self._column_selector.addItems(numeric_columns)

        # Create initial plot
        if numeric_columns:
            self._plot_distribution(numeric_columns[0])

    def create_correlation_heatmap(self, df: pd.DataFrame, dataset_name: str) -> None:
        """
        Create correlation heatmap for the dataset.

        Args:
            df: DataFrame to visualize
            dataset_name: Dataset name
        """
        self._df = df
        self._dataset_name = dataset_name

        # Get numeric columns
        numeric_df = df.select_dtypes(include=['number'])

        if len(numeric_df.columns) < 2:
            # Not enough numeric columns for correlation
            self._corr_canvas.axes.clear()
            self._corr_canvas.axes.text(
                0.5, 0.5,
                "Not enough numeric columns for correlation analysis",
                horizontalalignment='center',
                verticalalignment='center'
            )
            self._corr_canvas.draw()
            return

        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()

        # Plot heatmap
        self._corr_canvas.axes.clear()
        im = self._corr_canvas.axes.imshow(
            corr_matrix,
            cmap='coolwarm',
            vmin=-1,
            vmax=1
        )

        # Add colorbar
        self._corr_canvas.figure.colorbar(im)

        # Add labels
        self._corr_canvas.axes.set_title(f"Correlation Matrix: {dataset_name}")

        # Add column names
        col_names = corr_matrix.columns

        # Add ticks and labels
        self._corr_canvas.axes.set_xticks(np.arange(len(col_names)))
        self._corr_canvas.axes.set_yticks(np.arange(len(col_names)))
        self._corr_canvas.axes.set_xticklabels(col_names, rotation=45, ha="right")
        self._corr_canvas.axes.set_yticklabels(col_names)

        # Loop over data and add text annotations
        for i in range(len(col_names)):
            for j in range(len(col_names)):
                text = self._corr_canvas.axes.text(
                    j, i,
                    f"{corr_matrix.iloc[i, j]:.2f}",
                    ha="center",
                    va="center",
                    color="black" if abs(corr_matrix.iloc[i, j]) < 0.7 else "white"
                )

        self._corr_canvas.draw()

    def create_scatter_plots(self, df: pd.DataFrame, dataset_name: str) -> None:
        """
        Create scatter plots for the dataset.

        Args:
            df: DataFrame to visualize
            dataset_name: Dataset name
        """
        self._df = df
        self._dataset_name = dataset_name

        # Set columns in selectors
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

        self._x_column.clear()
        self._x_column.addItems(numeric_columns)

        self._y_column.clear()
        self._y_column.addItems(numeric_columns)

        # Select different columns for x and y if possible
        if len(numeric_columns) > 1:
            self._y_column.setCurrentIndex(1)

        # Create initial scatter plot
        self._update_scatter_plot()

    def create_trend_plots(self, df: pd.DataFrame, dataset_name: str,
                           trends: List[str]) -> None:
        """
        Create trend plots for the dataset.

        Args:
            df: DataFrame to visualize
            dataset_name: Dataset name
            trends: List of detected trends
        """
        self._df = df
        self._dataset_name = dataset_name

        # Clear the canvas
        self._trend_canvas.axes.clear()

        # Select tab
        self._tabs.setCurrentWidget(self._trend_tab)

        # Get numeric columns for trend visualization
        numeric_cols = df.select_dtypes(include=['number']).columns

        if len(numeric_cols) < 2:
            self._trend_canvas.axes.text(
                0.5, 0.5,
                "Not enough numeric columns for trend visualization",
                horizontalalignment='center',
                verticalalignment='center'
            )
            self._trend_canvas.draw()
            return

        # Find column that might represent time or sequence
        time_cols = [col for col in numeric_cols if 'time' in col.lower()
                     or 'date' in col.lower() or 'year' in col.lower()
                     or 'month' in col.lower() or 'day' in col.lower()
                     or 'id' in col.lower() or 'index' in col.lower()]

        if time_cols:
            x_col = time_cols[0]
        else:
            # Use first column as x
            x_col = numeric_cols[0]

        # Get other numeric columns for y
        y_cols = [col for col in numeric_cols if col != x_col][:3]  # Limit to 3 columns

        # Plot trends
        for i, y_col in enumerate(y_cols):
            # Sort by x column
            sorted_df = df.sort_values(by=x_col)

            # Plot actual data
            self._trend_canvas.axes.scatter(
                sorted_df[x_col],
                sorted_df[y_col],
                alpha=0.5,
                label=f"{y_col} (actual)"
            )

            # Try to fit a trend line
            try:
                # Check if we have enough data for polynomial fit
                if len(sorted_df) >= 3:
                    # Fit polynomial
                    z = np.polyfit(sorted_df[x_col], sorted_df[y_col], 2)
                    p = np.poly1d(z)

                    # Plot trend line
                    x_line = np.linspace(
                        sorted_df[x_col].min(),
                        sorted_df[x_col].max(),
                        100
                    )
                    y_line = p(x_line)

                    self._trend_canvas.axes.plot(
                        x_line,
                        y_line,
                        '-',
                        linewidth=2,
                        label=f"{y_col} (trend)"
                    )
            except Exception as e:
                # Just skip trend line if there's an error
                pass

        # Add trend annotations
        if trends:
            trend_text = "\n".join(trends[:3])
            if len(trends) > 3:
                trend_text += f"\n...and {len(trends) - 3} more"

            # Add text box with trends
            self._trend_canvas.axes.text(
                0.05, 0.95,
                trend_text,
                transform=self._trend_canvas.axes.transAxes,
                verticalalignment='top',
                bbox={'boxstyle': 'round', 'facecolor': 'wheat', 'alpha': 0.5}
            )

        # Finish the plot
        self._trend_canvas.axes.set_xlabel(x_col)
        self._trend_canvas.axes.set_ylabel("Values")
        self._trend_canvas.axes.set_title(f"Trends: {dataset_name}")
        self._trend_canvas.axes.legend()
        self._trend_canvas.axes.grid(True, linestyle='--', alpha=0.7)

        self._trend_canvas.draw()

    def _plot_distribution(self, column_name: str) -> None:
        """
        Plot distribution for a column.

        Args:
            column_name: Column to plot
        """
        if self._df is None or column_name not in self._df.columns:
            return

        # Clear the axes
        self._distrib_canvas.axes.clear()

        # Get plot type
        plot_type = self._plot_type.currentText()

        # Get data
        data = self._df[column_name].dropna()

        # Plot based on type
        if plot_type == "Histogram":
            self._distrib_canvas.axes.hist(data, bins=30, alpha=0.7, color='skyblue')
            self._distrib_canvas.axes.set_ylabel("Frequency")
        elif plot_type == "Box Plot":
            self._distrib_canvas.axes.boxplot(data, vert=False)
            self._distrib_canvas.axes.set_ylabel(column_name)
        elif plot_type == "Violin Plot":
            self._distrib_canvas.axes.violinplot(data, vert=False, showmeans=True)
            self._distrib_canvas.axes.set_ylabel(column_name)
        elif plot_type == "KDE Plot":
            # Simple KDE approximation
            from scipy import stats

            x = np.linspace(data.min(), data.max(), 1000)
            kde = stats.gaussian_kde(data)
            y = kde(x)

            self._distrib_canvas.axes.plot(x, y, color='skyblue')
            self._distrib_canvas.axes.fill_between(x, y, alpha=0.3, color='skyblue')
            self._distrib_canvas.axes.set_ylabel("Density")

        # Set title and labels
        self._distrib_canvas.axes.set_title(f"{plot_type}: {column_name}")
        self._distrib_canvas.axes.set_xlabel(column_name)

        # Add stats text
        mean_val = data.mean()
        median_val = data.median()
        std_val = data.std()
        min_val = data.min()
        max_val = data.max()

        stats_text = (
            f"Mean: {mean_val:.2f}\n"
            f"Median: {median_val:.2f}\n"
            f"Std Dev: {std_val:.2f}\n"
            f"Min: {min_val:.2f}\n"
            f"Max: {max_val:.2f}\n"
            f"Count: {len(data)}"
        )

        self._distrib_canvas.axes.text(
            0.05, 0.95,
            stats_text,
            transform=self._distrib_canvas.axes.transAxes,
            verticalalignment='top',
            bbox={'boxstyle': 'round', 'facecolor': 'wheat', 'alpha': 0.5}
        )

        # Draw the plot
        self._distrib_canvas.draw()

    def _update_scatter_plot(self) -> None:
        """Update scatter plot with current x and y columns."""
        if self._df is None:
            return

        x_col = self._x_column.currentText()
        y_col = self._y_column.currentText()

        if not x_col or not y_col or x_col not in self._df.columns or y_col not in self._df.columns:
            return

        # Clear the axes
        self._scatter_canvas.axes.clear()

        # Get data
        x_data = self._df[x_col].values
        y_data = self._df[y_col].values

        # Plot scatter
        self._scatter_canvas.axes.scatter(x_data, y_data, alpha=0.7, color='skyblue')

        # Add trendline
        try:
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)

            # Create line points
            x_line = np.linspace(min(x_data), max(x_data), 100)
            y_line = p(x_line)

            # Plot trendline
            self._scatter_canvas.axes.plot(x_line, y_line, 'r--')

            # Add R^2 value
            y_mean = np.mean(y_data)
            ss_tot = np.sum((y_data - y_mean) ** 2)
            ss_res = np.sum((y_data - p(x_data)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)

            # Add correlation
            correlation = np.corrcoef(x_data, y_data)[0, 1]

            # Add stats text
            stats_text = (
                f"Correlation: {correlation:.3f}\n"
                f"R²: {r_squared:.3f}\n"
                f"Equation: y = {z[0]:.3f}x + {z[1]:.3f}"
            )

            self._scatter_canvas.axes.text(
                0.05, 0.95,
                stats_text,
                transform=self._scatter_canvas.axes.transAxes,
                verticalalignment='top',
                bbox={'boxstyle': 'round', 'facecolor': 'wheat', 'alpha': 0.5}
            )

        except Exception:
            # Skip trendline if there's an error
            pass

        # Set title and labels
        self._scatter_canvas.axes.set_title(f"Scatter Plot: {x_col} vs {y_col}")
        self._scatter_canvas.axes.set_xlabel(x_col)
        self._scatter_canvas.axes.set_ylabel(y_col)
        self._scatter_canvas.axes.grid(True, linestyle='--', alpha=0.7)

        # Draw the plot
        self._scatter_canvas.draw()

    @Slot(int)
    def _on_column_changed(self, index: int) -> None:
        """
        Handle column selection change.

        Args:
            index: New column index
        """
        if index < 0 or self._column_selector.count() == 0:
            return

        column_name = self._column_selector.currentText()
        self._plot_distribution(column_name)

    @Slot(int)
    def _on_plot_type_changed(self, index: int) -> None:
        """
        Handle plot type selection change.

        Args:
            index: New plot type index
        """
        if self._column_selector.count() == 0:
            return

        column_name = self._column_selector.currentText()
        self._plot_distribution(column_name)