from __future__ import annotations
'\nOutput preview table for displaying expected outputs before processing.\n\nThis module provides a dialog for showing the output paths, status (overwrite, increment, new),\nand allowing users to review and adjust output settings before processing.\n'
import os
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize, QPoint
from PySide6.QtGui import QColor, QIcon, QStandardItemModel, QStandardItem, QAction
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeView, QHeaderView, QCheckBox, QFrame, QSplitter, QWidget, QFileDialog, QMessageBox, QMenu, QProgressBar
from ..models.processing_config import ProcessingConfig
from ..utils.path_resolver import resolve_output_path
class OutputStatus(Enum):
    NEW = 'new'
    OVERWRITE = 'overwrite'
    INCREMENT = 'increment'
class OutputPreviewTable(QDialog):
    processingConfirmed = Signal(bool)
    def __init__(self, file_paths: List[str], config: ProcessingConfig, output_dir: Optional[str], overwrite: bool, logger: Any, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._file_paths = file_paths
        self._config = config
        self._output_dir = output_dir or config.output_directory
        self._overwrite = overwrite
        self._logger = logger
        self._output_info: List[Dict[str, Any]] = []
        self._cancelled: bool = False
        self._init_ui()
        self.setWindowTitle('Output Preview')
        self.resize(900, 600)
        asyncio.create_task(self._analyze_outputs())
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        header_layout = QVBoxLayout()
        title_label = QLabel('Output File Preview')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        header_layout.addWidget(title_label)
        desc_label = QLabel('Review the output files that will be created. You can change the output directory or adjust overwrite settings before processing.')
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)
        layout.addLayout(header_layout)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel('Output Directory:'))
        self._output_dir_label = QLabel(self._output_dir or 'Default')
        self._output_dir_label.setStyleSheet('font-weight: bold;')
        dir_layout.addWidget(self._output_dir_label, 1)
        self._change_dir_btn = QPushButton('Change...')
        self._change_dir_btn.clicked.connect(self._on_change_dir)
        dir_layout.addWidget(self._change_dir_btn)
        layout.addLayout(dir_layout)
        stats_layout = QHBoxLayout()
        self._total_label = QLabel('Total files: 0')
        stats_layout.addWidget(self._total_label)
        self._new_label = QLabel('New: 0')
        self._new_label.setStyleSheet('color: green;')
        stats_layout.addWidget(self._new_label)
        self._overwrite_label = QLabel('Overwrite: 0')
        self._overwrite_label.setStyleSheet('color: red;')
        stats_layout.addWidget(self._overwrite_label)
        self._increment_label = QLabel('Increment: 0')
        self._increment_label.setStyleSheet('color: blue;')
        stats_layout.addWidget(self._increment_label)
        stats_layout.addStretch()
        self._overwrite_check = QCheckBox('Overwrite existing files')
        self._overwrite_check.setChecked(self._overwrite)
        self._overwrite_check.toggled.connect(self._on_overwrite_toggled)
        stats_layout.addWidget(self._overwrite_check)
        layout.addLayout(stats_layout)
        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(['Input File', 'Output File', 'Status', 'Format'])
        self._tree_view = QTreeView()
        self._tree_view.setModel(self._model)
        self._tree_view.setAlternatingRowColors(True)
        self._tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self._tree_view.setSortingEnabled(True)
        self._tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree_view.customContextMenuRequested.connect(self._on_context_menu)
        header = self._tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self._tree_view, 1)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)
        buttons_layout = QHBoxLayout()
        self._cancel_btn = QPushButton('Cancel')
        self._cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self._cancel_btn)
        buttons_layout.addStretch()
        self._process_btn = QPushButton('Process')
        self._process_btn.clicked.connect(self._on_process)
        self._process_btn.setEnabled(False)
        buttons_layout.addWidget(self._process_btn)
        layout.addLayout(buttons_layout)
    async def _analyze_outputs(self) -> None:
        if not self._file_paths or not self._config:
            return
        self._process_btn.setEnabled(False)
        self._output_info = []
        total_operations = len(self._file_paths) * len(self._config.output_formats)
        current_operation = 0
        for input_path in self._file_paths:
            input_item = QStandardItem(os.path.basename(input_path))
            input_item.setToolTip(input_path)
            input_icon = QStandardItem()
            input_icon.setIcon(QIcon.fromTheme('document'))
            for format_config in self._config.output_formats:
                try:
                    output_dir = self._output_dir or self._config.output_directory
                    output_path = resolve_output_path(input_path, output_dir, format_config)
                    file_exists = os.path.exists(output_path)
                    if file_exists:
                        if self._overwrite:
                            status = OutputStatus.OVERWRITE
                        else:
                            base_name, ext = os.path.splitext(output_path)
                            counter = 1
                            incremented_path = f'{base_name}_{counter}{ext}'
                            while os.path.exists(incremented_path):
                                counter += 1
                                incremented_path = f'{base_name}_{counter}{ext}'
                            output_path = incremented_path
                            status = OutputStatus.INCREMENT
                    else:
                        status = OutputStatus.NEW
                    output_info = {'input_path': input_path, 'output_path': output_path, 'format_name': format_config.name, 'format_id': format_config.id, 'status': status}
                    self._output_info.append(output_info)
                    output_file_item = QStandardItem(os.path.basename(output_path))
                    output_file_item.setToolTip(output_path)
                    status_item = QStandardItem(status.value.title())
                    if status == OutputStatus.NEW:
                        status_item.setForeground(QColor('green'))
                    elif status == OutputStatus.OVERWRITE:
                        status_item.setForeground(QColor('red'))
                    else:
                        status_item.setForeground(QColor('blue'))
                    format_item = QStandardItem(format_config.name)
                    row = [QStandardItem(os.path.basename(input_path)), output_file_item, status_item, format_item]
                    row[0].setToolTip(input_path)
                    self._model.appendRow(row)
                except Exception as e:
                    self._logger.error(f'Error analyzing output for {input_path}: {str(e)}')
                current_operation += 1
                progress = int(current_operation / total_operations * 100)
                await self._update_progress(progress)
        await self._update_stats()
        self._process_btn.setEnabled(len(self._output_info) > 0)
        self._progress_bar.setValue(100)
    async def _update_progress(self, value: int) -> None:
        self._progress_bar.setValue(value)
        await asyncio.sleep(0)
    async def _update_stats(self) -> None:
        if not self._output_info:
            return
        new_count = 0
        overwrite_count = 0
        increment_count = 0
        for info in self._output_info:
            if info['status'] == OutputStatus.NEW:
                new_count += 1
            elif info['status'] == OutputStatus.OVERWRITE:
                overwrite_count += 1
            elif info['status'] == OutputStatus.INCREMENT:
                increment_count += 1
        total_count = len(self._output_info)
        self._total_label.setText(f'Total operations: {total_count}')
        self._new_label.setText(f'New: {new_count}')
        self._overwrite_label.setText(f'Overwrite: {overwrite_count}')
        self._increment_label.setText(f'Increment: {increment_count}')
    @Slot()
    def _on_change_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, 'Select Output Directory', self._output_dir or '')
        if dir_path:
            self._output_dir = dir_path
            self._output_dir_label.setText(dir_path)
            self._model.clear()
            self._model.setHorizontalHeaderLabels(['Input File', 'Output File', 'Status', 'Format'])
            asyncio.create_task(self._analyze_outputs())
    @Slot(bool)
    def _on_overwrite_toggled(self, checked: bool) -> None:
        if self._overwrite != checked:
            self._overwrite = checked
            self._model.clear()
            self._model.setHorizontalHeaderLabels(['Input File', 'Output File', 'Status', 'Format'])
            asyncio.create_task(self._analyze_outputs())
    @Slot(QPoint)
    def _on_context_menu(self, pos) -> None:
        indexes = self._tree_view.selectedIndexes()
        if not indexes:
            return
        menu = QMenu(self)
        open_folder_action = QAction('Open Containing Folder', self)
        open_folder_action.triggered.connect(self._on_open_folder)
        menu.addAction(open_folder_action)
        menu.exec_(self._tree_view.viewport().mapToGlobal(pos))
    @Slot()
    def _on_open_folder(self) -> None:
        indexes = self._tree_view.selectedIndexes()
        if not indexes:
            return
        row = indexes[0].row()
        output_file = self._model.item(row, 1).toolTip()
        if output_file:
            output_dir = os.path.dirname(output_file)
            import subprocess
            import platform
            try:
                if platform.system() == 'Windows':
                    os.startfile(output_dir)
                elif platform.system() == 'Darwin':
                    subprocess.Popen(['open', output_dir])
                else:
                    subprocess.Popen(['xdg-open', output_dir])
            except Exception as e:
                self._logger.error(f'Error opening folder: {str(e)}')
                QMessageBox.warning(self, 'Error', f'Could not open folder: {str(e)}')
    @Slot()
    def _on_process(self) -> None:
        if not self._output_info:
            return
        overwrite_count = sum((1 for info in self._output_info if info['status'] == OutputStatus.OVERWRITE))
        if overwrite_count > 0 and self._overwrite:
            result = QMessageBox.warning(self, 'Confirm Overwrite', f'This will overwrite {overwrite_count} existing files. Continue?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if result != QMessageBox.Yes:
                return
        self.processingConfirmed.emit(True)
        self.accept()
    def reject(self) -> None:
        self.processingConfirmed.emit(False)
        super().reject()
    def get_output_dir(self) -> str:
        return self._output_dir
    def get_overwrite(self) -> bool:
        return self._overwrite