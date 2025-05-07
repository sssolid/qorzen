from __future__ import annotations

from initialdb.services.vehicle_service import VehicleService
from initialdb.utils.dependency_container import resolve

"""
Query manager dialog for the InitialDB application.

This module provides a dialog for managing saved and recent queries,
allowing users to view, edit, rename, and delete queries.
"""
import uuid
from typing import Dict, List, Optional, Any, Tuple, cast
import structlog
import asyncio
import json
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QWidget, QListWidget, QListWidgetItem, QDialogButtonBox, QSplitter,
    QTextEdit, QLineEdit, QMessageBox, QMenu, QInputDialog, QFormLayout,
    QGroupBox, QPlainTextEdit, QCheckBox, QToolButton, QSizePolicy
)
from qasync import asyncSlot

from initialdb.config.settings import settings
from initialdb.models.schema import FilterDTO, SavedQueryDTO

logger = structlog.get_logger(__name__)


class QueryManagerDialog(QDialog):
    """
    Dialog for managing saved and recent queries.

    This dialog allows users to browse, select, edit, rename, and delete
    saved queries, as well as view and save recent queries.
    """
    querySelected = pyqtSignal(SavedQueryDTO)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the query manager dialog.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._vehicle_service = resolve(VehicleService)

        self.setWindowTitle('Query Manager')
        self.resize(800, 600)

        self.saved_queries: Dict[str, SavedQueryDTO] = {}
        self.recent_queries: List[Dict[str, Any]] = []

        self._init_ui()
        self._load_queries()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Left panel (list of queries)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        # Saved queries tab
        self.saved_tab = QWidget()
        saved_layout = QVBoxLayout(self.saved_tab)

        self.saved_list = QListWidget()
        self.saved_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.saved_list.customContextMenuRequested.connect(self._show_saved_context_menu)
        self.saved_list.currentItemChanged.connect(self._on_saved_query_selected)

        saved_actions = QHBoxLayout()
        self.saved_rename_btn = QPushButton('Rename')
        self.saved_rename_btn.clicked.connect(self._rename_saved_query)
        saved_actions.addWidget(self.saved_rename_btn)

        self.saved_delete_btn = QPushButton('Delete')
        self.saved_delete_btn.clicked.connect(self._delete_saved_query)
        saved_actions.addWidget(self.saved_delete_btn)

        saved_layout.addWidget(self.saved_list)
        saved_layout.addLayout(saved_actions)

        # Recent queries tab
        self.recent_tab = QWidget()
        recent_layout = QVBoxLayout(self.recent_tab)

        self.recent_list = QListWidget()
        self.recent_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recent_list.customContextMenuRequested.connect(self._show_recent_context_menu)
        self.recent_list.currentItemChanged.connect(self._on_recent_query_selected)

        recent_actions = QHBoxLayout()
        self.recent_save_btn = QPushButton('Save As...')
        self.recent_save_btn.clicked.connect(self._save_recent_query)
        recent_actions.addWidget(self.recent_save_btn)

        recent_layout.addWidget(self.recent_list)
        recent_layout.addLayout(recent_actions)

        self.tabs.addTab(self.saved_tab, 'Saved Queries')
        self.tabs.addTab(self.recent_tab, 'Recent Queries')

        left_layout.addWidget(self.tabs)

        # Right panel (query details)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        details_group = QGroupBox('Query Details')
        details_layout = QVBoxLayout(details_group)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        form_layout.addRow('Name:', self.name_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setReadOnly(True)
        form_layout.addRow('Description:', self.description_edit)

        self.created_label = QLabel()
        form_layout.addRow('Created:', self.created_label)

        self.modified_label = QLabel()
        form_layout.addRow('Last Modified:', self.modified_label)

        self.results_label = QLabel()
        form_layout.addRow('Results Count:', self.results_label)

        details_layout.addLayout(form_layout)

        query_group = QGroupBox('Query Content')
        query_layout = QVBoxLayout(query_group)

        self.query_edit = QPlainTextEdit()
        self.query_edit.setReadOnly(True)
        query_layout.addWidget(self.query_edit)

        right_layout.addWidget(details_group)
        right_layout.addWidget(query_group)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Close)
        button_box.accepted.connect(self._open_selected_query)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Initial button states
        self.saved_rename_btn.setEnabled(False)
        self.saved_delete_btn.setEnabled(False)
        self.recent_save_btn.setEnabled(False)
        button_box.button(QDialogButtonBox.StandardButton.Open).setEnabled(False)
        self.open_button = button_box.button(QDialogButtonBox.StandardButton.Open)

    @asyncSlot()
    async def _load_saved_queries_async(self) -> None:
        """Load saved queries asynchronously."""
        try:
            self.saved_queries = await self._vehicle_service.get_saved_queries()
            self._populate_saved_list()
        except Exception as e:
            logger.error(f'Error loading saved queries: {str(e)}')

    @asyncSlot()
    async def _load_recent_queries_async(self) -> None:
        """Load saved queries asynchronously."""
        try:
            self.recent_queries = await self._vehicle_service.get_recent_queries()
            self._populate_recent_list()
        except Exception as e:
            logger.error(f'Error loading recent queries: {str(e)}')

    # def _load_recent_queries(self) -> None:
    #     """Load recent queries from settings."""
    #     try:
    #         self.recent_queries = settings.get_recent_queries()
    #         self._populate_recent_list()
    #     except Exception as e:
    #         logger.error(f'Error loading recent queries: {str(e)}')

    @asyncSlot()
    async def _load_queries(self) -> None:
        """Load all saved queries."""
        try:
            await self._load_recent_queries_async()
            await self._load_saved_queries_async()
        except Exception as e:
            logger.error(f"Error loading saved queries: {str(e)}")

    # def _load_queries(self) -> None:
    #     """Load both saved and recent queries."""
    #     self._load_recent_queries()
    #     asyncio.create_task(self._load_saved_queries_async())

    def _populate_saved_list(self) -> None:
        """Populate the saved queries list widget."""
        self.saved_list.clear()
        for name, query in self.saved_queries.items():
            item = QListWidgetItem(name)
            if query.description:
                item.setToolTip(query.description)
            item.setData(Qt.ItemDataRole.UserRole, query)
            self.saved_list.addItem(item)

    def _populate_recent_list(self) -> None:
        """Populate the recent queries list widget."""
        self.recent_list.clear()
        for idx, query_info in enumerate(self.recent_queries, 1):
            name = query_info.get('name', f'Query {idx}')
            count = query_info.get('count', 0)
            timestamp = query_info.get('timestamp')

            item = QListWidgetItem(f'{name} ({count} results)')

            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    item.setToolTip(f"Run on {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except ValueError:
                    pass

            item.setData(Qt.ItemDataRole.UserRole, query_info)
            self.recent_list.addItem(item)

    def _on_saved_query_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        """
        Handle saved query selection.

        Args:
            current: The newly selected item
            previous: The previously selected item
        """
        if current:
            query = current.data(Qt.ItemDataRole.UserRole)
            if isinstance(query, SavedQueryDTO):
                self._display_query_details(query)
                self.saved_rename_btn.setEnabled(True)
                self.saved_delete_btn.setEnabled(True)
                self.open_button.setEnabled(True)
            else:
                self._clear_query_details()
                self.saved_rename_btn.setEnabled(False)
                self.saved_delete_btn.setEnabled(False)
                self.open_button.setEnabled(False)
        else:
            self._clear_query_details()
            self.saved_rename_btn.setEnabled(False)
            self.saved_delete_btn.setEnabled(False)
            self.open_button.setEnabled(False)

    def _on_recent_query_selected(self, current: Optional[QListWidgetItem],
                                  previous: Optional[QListWidgetItem]) -> None:
        """
        Handle recent query selection.

        Args:
            current: The newly selected item
            previous: The previously selected item
        """
        if current:
            query_info = current.data(Qt.ItemDataRole.UserRole)
            if isinstance(query_info, dict):
                self._display_recent_query_details(query_info)
                self.recent_save_btn.setEnabled(True)
                self.open_button.setEnabled(True)
            else:
                self._clear_query_details()
                self.recent_save_btn.setEnabled(False)
                self.open_button.setEnabled(False)
        else:
            self._clear_query_details()
            self.recent_save_btn.setEnabled(False)
            self.open_button.setEnabled(False)

    def _display_query_details(self, query: SavedQueryDTO) -> None:
        """
        Display details of a saved query.

        Args:
            query: The query to display
        """
        self.name_edit.setText(query.name)
        self.description_edit.setText(query.description or '')
        self.created_label.setText('N/A')
        self.modified_label.setText('N/A')
        self.results_label.setText('N/A')

        try:
            if isinstance(query.filters, dict):
                formatted_filters = json.dumps(query.filters, indent=2)
            else:
                formatted_filters = str(query.filters)

            self.query_edit.setPlainText(formatted_filters)
        except Exception as e:
            self.query_edit.setPlainText(f'Error formatting query: {str(e)}')

    def _display_recent_query_details(self, query_info: Dict[str, Any]) -> None:
        """
        Display details of a recent query.

        Args:
            query_info: The query info to display
        """
        self.name_edit.setText(query_info.get('name', 'Unnamed Query'))
        self.description_edit.setText('')

        timestamp = query_info.get('timestamp')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                self.created_label.setText(dt.strftime('%Y-%m-%d %H:%M:%S'))
                self.modified_label.setText(dt.strftime('%Y-%m-%d %H:%M:%S'))
            except ValueError:
                self.created_label.setText('N/A')
                self.modified_label.setText('N/A')
        else:
            self.created_label.setText('N/A')
            self.modified_label.setText('N/A')

        count = query_info.get('count', 0)
        self.results_label.setText(str(count))

        try:
            filters = query_info.get('filters', {})
            formatted_filters = json.dumps(filters, indent=2)
            self.query_edit.setPlainText(formatted_filters)
        except Exception as e:
            self.query_edit.setPlainText(f'Error formatting query: {str(e)}')

    def _clear_query_details(self) -> None:
        """Clear all query detail fields."""
        self.name_edit.setText('')
        self.description_edit.setText('')
        self.created_label.setText('')
        self.modified_label.setText('')
        self.results_label.setText('')
        self.query_edit.setPlainText('')

    def _show_saved_context_menu(self, position) -> None:
        """
        Show context menu for saved queries.

        Args:
            position: Mouse position
        """
        item = self.saved_list.itemAt(position)
        if not item:
            return

        menu = QMenu()

        open_action = QAction('Open', self)
        open_action.triggered.connect(self._open_selected_query)
        menu.addAction(open_action)

        menu.addSeparator()

        rename_action = QAction('Rename...', self)
        rename_action.triggered.connect(self._rename_saved_query)
        menu.addAction(rename_action)

        duplicate_action = QAction('Duplicate...', self)
        duplicate_action.triggered.connect(self._duplicate_saved_query)
        menu.addAction(duplicate_action)

        menu.addSeparator()

        delete_action = QAction('Delete', self)
        delete_action.triggered.connect(self._delete_saved_query)
        menu.addAction(delete_action)

        menu.exec(self.saved_list.mapToGlobal(position))

    def _show_recent_context_menu(self, position) -> None:
        """
        Show context menu for recent queries.

        Args:
            position: Mouse position
        """
        item = self.recent_list.itemAt(position)
        if not item:
            return

        menu = QMenu()

        open_action = QAction('Open', self)
        open_action.triggered.connect(self._open_selected_query)
        menu.addAction(open_action)

        menu.addSeparator()

        save_action = QAction('Save As...', self)
        save_action.triggered.connect(self._save_recent_query)
        menu.addAction(save_action)

        menu.exec(self.recent_list.mapToGlobal(position))

    @asyncSlot()
    async def _rename_saved_query(self) -> None:
        """Rename the selected saved query."""
        item = self.saved_list.currentItem()
        if not item:
            return

        query = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(query, SavedQueryDTO):
            return

        new_name, ok = QInputDialog.getText(
            self, 'Rename Query', 'Enter new name:',
            QLineEdit.EchoMode.Normal, query.name
        )

        if ok and new_name and (new_name != query.name):
            if new_name in self.saved_queries:
                QMessageBox.warning(
                    self, 'Duplicate Name',
                    f"A query named '{new_name}' already exists."
                )
                return

            old_name = query.name
            query.name = new_name

            try:
                # Delete the old query and save with the new name
                await self._vehicle_service.delete_query(old_name)
                await self._vehicle_service.save_query(query)

                # Refresh the list
                self.saved_queries = await self._vehicle_service.get_saved_queries()
                self._populate_saved_list()
            except Exception as e:
                logger.error(f'Error renaming query: {str(e)}')
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to rename query: {str(e)}'
                )

    @asyncSlot()
    async def _duplicate_saved_query(self) -> None:
        """Duplicate the selected saved query."""
        item = self.saved_list.currentItem()
        if not item:
            return

        query = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(query, SavedQueryDTO):
            return

        new_name, ok = QInputDialog.getText(
            self, 'Duplicate Query',
            'Enter name for the duplicate:',
            QLineEdit.EchoMode.Normal,
            f'Copy of {query.name}'
        )

        if ok and new_name:
            if new_name in self.saved_queries:
                QMessageBox.warning(
                    self, 'Duplicate Name',
                    f"A query named '{new_name}' already exists."
                )
                return

            new_query = SavedQueryDTO(
                id=str(uuid.uuid4()),
                name=new_name,
                description=query.description,
                filters=query.filters,
                visible_columns=query.visible_columns,
                is_multi_query=query.is_multi_query
            )

            try:
                await self._vehicle_service.save_query(new_query)

                # Refresh the list
                self.saved_queries = await self._vehicle_service.get_saved_queries()
                self._populate_saved_list()
            except Exception as e:
                logger.error(f'Error duplicating query: {str(e)}')
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to duplicate query: {str(e)}'
                )

    @asyncSlot()
    async def _delete_saved_query(self) -> None:
        """Delete the selected saved query."""
        item = self.saved_list.currentItem()
        if not item:
            return

        query = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(query, SavedQueryDTO):
            return

        result = QMessageBox.question(
            self, 'Confirm Delete',
            f"Are you sure you want to delete the query '{query.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            try:
                await self._vehicle_service.delete_query(query.name)

                # Refresh the list
                self.saved_queries = await self._vehicle_service.get_saved_queries()
                self._populate_saved_list()
            except Exception as e:
                logger.error(f'Error deleting query: {str(e)}')
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to delete query: {str(e)}'
                )

    @asyncSlot()
    async def _save_recent_query(self) -> None:
        """Save a recent query as a permanent saved query."""
        item = self.recent_list.currentItem()
        if not item:
            return

        query_info = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(query_info, dict):
            return

        name, ok = QInputDialog.getText(
            self, 'Save Query',
            'Enter name for the saved query:',
            QLineEdit.EchoMode.Normal,
            query_info.get('name', 'Unnamed Query')
        )

        if ok and name:
            if name in self.saved_queries:
                result = QMessageBox.question(
                    self, 'Duplicate Name',
                    f"A query named '{name}' already exists. Do you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if result != QMessageBox.StandardButton.Yes:
                    return

            saved_query = SavedQueryDTO(
                id=str(uuid.uuid4()),
                name=name,
                description='Saved from recent queries',
                filters=query_info.get('filters', {}),
                visible_columns=query_info.get('columns', []),
                is_multi_query=True
            )

            try:
                await self._vehicle_service.save_query(saved_query)

                # Refresh the list
                self.saved_queries = await self._vehicle_service.get_saved_queries()
                self._populate_saved_list()

                # Switch to saved queries tab
                self.tabs.setCurrentIndex(0)
            except Exception as e:
                logger.error(f'Error saving query: {str(e)}')
                QMessageBox.warning(
                    self, 'Error',
                    f'Failed to save query: {str(e)}'
                )

    def _open_selected_query(self) -> None:
        """Open the currently selected query."""
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:
            item = self.saved_list.currentItem()
            if not item:
                return

            query = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(query, SavedQueryDTO):
                self.querySelected.emit(query)
                self.accept()
        elif current_tab == 1:
            item = self.recent_list.currentItem()
            if not item:
                return

            query_info = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(query_info, dict):
                saved_query = SavedQueryDTO(
                    id=str(uuid.uuid4()),
                    name=query_info.get('name', 'Unnamed Query'),
                    description='',
                    filters=query_info.get('filters', {}),
                    visible_columns=query_info.get('columns', []),
                    is_multi_query=True
                )
                self.querySelected.emit(saved_query)
                self.accept()