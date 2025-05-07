from __future__ import annotations

"""
Table models for the InitialDB application.

This module provides custom table models for displaying vehicle data in Qt tables,
with support for sorting, filtering, and data conversion.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, cast
import structlog
from PySide6.QtCore import Qt, QModelIndex, QSortFilterProxyModel, QAbstractTableModel

logger = structlog.get_logger(__name__)


class VehicleResultsTableModel(QAbstractTableModel):
    """
    Table model for vehicle query results.

    This model displays vehicle data in a table format, with columns for
    various vehicle attributes such as year, make, model, etc.
    """

    def __init__(self, parent=None):
        """
        Initialize the vehicle results table model.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
        self._headers: List[str] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        Args:
            parent: Parent index

        Returns:
            Number of rows
        """
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of columns in the model.

        Args:
            parent: Parent index

        Returns:
            Number of columns
        """
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get data for a specific index and role.

        Args:
            index: Model index
            role: Data role

        Returns:
            Data for the specified index and role
        """
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._data) or col < 0 or col >= len(self._headers):
            return None

        column_name = self._headers[col]

        if role == Qt.ItemDataRole.DisplayRole:
            # Get the value for this cell
            value = self._data[row].get(column_name)

            # Format None or empty values
            if value is None:
                return ""

            # Format boolean values
            if isinstance(value, bool):
                return "Yes" if value else "No"

            # Return value as string
            return str(value)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get header data.

        Args:
            section: Section index
            orientation: Header orientation
            role: Data role

        Returns:
            Header data
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and section < len(self._headers):
                return self._headers[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)

        return None

    def setData(self, data: List[Dict[str, Any]]) -> None:
        """
        Set the model data.

        Args:
            data: List of data dictionaries
        """
        self.beginResetModel()

        # Store the data
        self._data = data

        # Extract headers from the data
        if data and len(data) > 0:
            logger.debug(f"Setting data with {len(data)} rows")
            self._headers = list(data[0].keys())
            logger.debug(f"Extracted headers: {self._headers}")
        else:
            self._headers = []

        self.endResetModel()

    def clearData(self) -> None:
        """Clear all data from the model."""
        self.beginResetModel()
        self._data = []
        self._headers = []
        self.endResetModel()

    def getRawData(self) -> List[Dict[str, Any]]:
        """
        Get the raw data from the model.

        Returns:
            List of data dictionaries
        """
        return self._data

    def getHeaders(self) -> List[str]:
        """
        Get the column headers.

        Returns:
            List of column headers
        """
        return self._headers


class SortableVehicleTableModel(QSortFilterProxyModel):
    """
    Sortable proxy model for vehicle data.

    This model adds sorting capabilities to the VehicleResultsTableModel.
    """

    def __init__(self, parent=None):
        """
        Initialize the sortable vehicle table model.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """
        Compare two items for sorting.

        Args:
            left: Left index
            right: Right index

        Returns:
            True if left is less than right
        """
        # Get the data for both indexes
        left_data = self.sourceModel().data(left, Qt.ItemDataRole.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.ItemDataRole.DisplayRole)

        # Handle None values
        if left_data is None:
            return False
        if right_data is None:
            return True

        # Try to convert both to float for numeric comparison
        try:
            left_num = float(left_data)
            right_num = float(right_data)
            return left_num < right_num
        except (ValueError, TypeError):
            # Fall back to string comparison
            return str(left_data) < str(right_data)