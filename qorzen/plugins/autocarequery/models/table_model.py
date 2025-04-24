from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class VehicleResultsTableModel(QAbstractTableModel):
    """Table model for displaying vehicle query results."""

    def __init__(self, data: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Initialize the table model.

        Args:
            data: List of dictionaries containing vehicle data
        """
        super().__init__()
        self._data = data if data is not None else []
        self._headers: List[str] = []

        if self._data and len(self._data) > 0:
            self._headers = list(self._data[0].keys())

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model."""
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns in the model."""
        if self._data and len(self._data) > 0:
            return len(self._headers)
        return 0

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return the data at the given index."""
        if not index.isValid() or not 0 <= index.row() < len(self._data):
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data[index.row()].get(self._headers[index.column()], '')
            return str(value) if value is not None else ''

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return the header data for the given section."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self._headers):
                return ' '.join(word.capitalize() for word in self._headers[section].split('_'))

        return super().headerData(section, orientation, role)

    def setData(self, data: List[Dict[str, Any]]) -> None:
        """Set new data for the model."""
        self.beginResetModel()
        self._data = data

        if self._data and len(self._data) > 0:
            self._headers = list(self._data[0].keys())
        else:
            self._headers = []

        self.endResetModel()