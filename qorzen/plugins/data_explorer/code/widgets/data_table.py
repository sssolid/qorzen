# qorzen/plugins/data_explorer/widgets/data_table.py
from __future__ import annotations

from typing import Any, List, Optional, Union, cast

import numpy as np
import pandas as pd
from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel,
    Signal, Slot, QRegularExpression
)
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QTableView, QHeaderView, QLineEdit


class DataTableModel(QAbstractTableModel):
    """Model for displaying pandas DataFrame in a QTableView."""

    def __init__(self, dataframe: Optional[pd.DataFrame] = None) -> None:
        """
        Initialize data table model.

        Args:
            dataframe: DataFrame to display
        """
        super().__init__()
        self._df = dataframe if dataframe is not None else pd.DataFrame()

        # Format function for displaying values
        self._format_func = lambda x: (
            f"{x:.4f}" if isinstance(x, float)
            else str(x) if x is not None and not pd.isna(x)
            else ""
        )

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get number of rows.

        Args:
            parent: Parent index

        Returns:
            Row count
        """
        return len(self._df) if self._df is not None else 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get number of columns.

        Args:
            parent: Parent index

        Returns:
            Column count
        """
        return len(self._df.columns) if self._df is not None else 0

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get data for table cell.

        Args:
            index: Cell index
            role: Data role

        Returns:
            Cell data
        """
        if not index.isValid() or self._df is None:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            # Get value from dataframe
            value = self._df.iloc[index.row(), index.column()]
            # Format value for display
            return self._format_func(value)

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Color missing values
            value = self._df.iloc[index.row(), index.column()]
            if pd.isna(value):
                return QBrush(QColor(255, 235, 235))  # Light red for missing values

        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get header data.

        Args:
            section: Header section
            orientation: Header orientation
            role: Data role

        Returns:
            Header data
        """
        if role != Qt.ItemDataRole.DisplayRole or self._df is None:
            return None

        if orientation == Qt.Orientation.Horizontal:
            # Return column name
            return str(self._df.columns[section])
        else:
            # Return row index
            return str(self._df.index[section])

    def set_dataframe(self, dataframe: pd.DataFrame) -> None:
        """
        Set new dataframe.

        Args:
            dataframe: New DataFrame
        """
        self.beginResetModel()
        self._df = dataframe
        self.endResetModel()


class DataFilterProxyModel(QSortFilterProxyModel):
    """Filter proxy model for pandas dataframe."""

    def __init__(self) -> None:
        """Initialize filter proxy model."""
        super().__init__()
        self._filter_expr = ""

    def set_filter(self, expression: str) -> None:
        """
        Set filter expression.

        Args:
            expression: Filter expression
        """
        self._filter_expr = expression
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Check if row matches filter.

        Args:
            source_row: Source row index
            source_parent: Parent index

        Returns:
            Whether row matches filter
        """
        if not self._filter_expr:
            return True

        # Get source model
        model = self.sourceModel()
        if model is None:
            return True

        # Check if any column contains the filter expression
        for col in range(model.columnCount()):
            index = model.index(source_row, col)
            value = model.data(index, Qt.ItemDataRole.DisplayRole)
            if value and self._filter_expr.lower() in str(value).lower():
                return True

        return False


class FilteredDataTableView(QTableView):
    """Table view with filtering capabilities."""

    def __init__(self) -> None:
        """Initialize filtered table view."""
        super().__init__()

        # Set up proxy model
        self._proxy_model = DataFilterProxyModel()
        self.setModel(self._proxy_model)

        # Set up table view properties
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(True)

        # Track filter input
        self._filter_input: Optional[QLineEdit] = None

    def set_filter_input(self, line_edit: QLineEdit) -> None:
        """
        Set filter input widget.

        Args:
            line_edit: Line edit widget for filtering
        """
        self._filter_input = line_edit

        # Connect filter input to proxy model
        line_edit.textChanged.connect(self._on_filter_changed)

    def setModel(self, model: QAbstractTableModel) -> None:
        """
        Set model for table view.

        Args:
            model: Table model
        """
        if isinstance(model, QSortFilterProxyModel):
            super().setModel(model)
        else:
            # Set source model for proxy
            self._proxy_model.setSourceModel(model)
            super().setModel(self._proxy_model)

    @Slot(str)
    def _on_filter_changed(self, text: str) -> None:
        """
        Handle filter text change.

        Args:
            text: New filter text
        """
        self._proxy_model.set_filter(text)