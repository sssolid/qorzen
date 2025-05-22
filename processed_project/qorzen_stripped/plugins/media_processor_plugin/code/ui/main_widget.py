from __future__ import annotations
'\nMain widget for the Media Processor Plugin.\n\nThis module contains the main interface widget for the Media Processor,\nproviding UI for media selection, processing, and configuration.\n'
import asyncio
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QSplitter, QListWidget, QListWidgetItem, QFileDialog, QComboBox, QGroupBox, QCheckBox, QMessageBox, QScrollArea, QToolButton, QMenu, QApplication, QFrame, QDialog
from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.concurrency_manager import ConcurrencyManager
from ..models.processing_config import ProcessingConfig, OutputFormat, BackgroundRemovalConfig
from ..processors.media_processor import MediaProcessor
from ..processors.batch_processor import BatchProcessor
from ..utils.exceptions import MediaProcessingError
from .batch_dialog import BatchProcessingDialog
from .config_editor import ConfigEditorDialog
from .format_editor import FormatEditorDialog
from .preview_widget import ImagePreviewWidget
class MediaProcessorWidget(QWidget):
    processingStarted = Signal()
    processingFinished = Signal(bool, str)
    configChanged = Signal(str)
    def __init__(self, media_processor: MediaProcessor, batch_processor: BatchProcessor, file_manager: FileManager, event_bus_manager: EventBusManager, concurrency_manager: ConcurrencyManager, task_manager: TaskManager, logger: Any, plugin_config: Dict[str, Any], parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._media_processor = media_processor
        self._batch_processor = batch_processor
        self._file_manager = file_manager
        self._event_bus_manager = event_bus_manager
        self._concurrency_manager = concurrency_manager
        self._task_manager = task_manager
        self._logger = logger
        self._plugin_config = plugin_config
        self._selected_files: List[str] = []
        self._current_file_index: int = -1
        self._current_config: Optional[ProcessingConfig] = None
        self._available_configs: Dict[str, ProcessingConfig] = {}
        self._processing = False
        asyncio.create_task(self._load_configs_async())
        self._init_ui()
        self._create_default_config()
        self.setAcceptDrops(True)
    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        title_label = QLabel('Media Processor')
        title_label.setStyleSheet('font-size: 18px; font-weight: bold;')
        main_layout.addWidget(title_label)
        description_label = QLabel('Process images with background removal and multiple output formats.')
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        self._splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self._splitter, 1)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        file_group = QGroupBox('Input Files')
        file_layout = QVBoxLayout(file_group)
        self._file_list = QListWidget()
        self._file_list.setMinimumWidth(200)
        self._file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._file_list.itemSelectionChanged.connect(self._on_file_selection_changed)
        file_layout.addWidget(self._file_list)
        file_buttons_layout = QHBoxLayout()
        self._add_files_btn = QPushButton('Add Files')
        self._add_files_btn.clicked.connect(self._on_add_files)
        file_buttons_layout.addWidget(self._add_files_btn)
        self._add_folder_btn = QPushButton('Add Folder')
        self._add_folder_btn.clicked.connect(self._on_add_folder)
        file_buttons_layout.addWidget(self._add_folder_btn)
        self._remove_files_btn = QPushButton('Remove')
        self._remove_files_btn.clicked.connect(self._on_remove_files)
        file_buttons_layout.addWidget(self._remove_files_btn)
        file_layout.addLayout(file_buttons_layout)
        left_layout.addWidget(file_group)
        config_group = QGroupBox('Processing Configuration')
        config_layout = QVBoxLayout(config_group)
        config_header_layout = QHBoxLayout()
        config_header_layout.addWidget(QLabel('Configuration:'))
        self._config_combo = QComboBox()
        self._config_combo.currentIndexChanged.connect(self._on_config_selected)
        config_header_layout.addWidget(self._config_combo, 1)
        self._edit_config_btn = QToolButton()
        self._edit_config_btn.setText('...')
        self._edit_config_btn.clicked.connect(self._on_edit_config)
        config_header_layout.addWidget(self._edit_config_btn)
        config_layout.addLayout(config_header_layout)
        config_buttons_layout = QHBoxLayout()
        self._new_config_btn = QPushButton('New')
        self._new_config_btn.clicked.connect(self._on_new_config)
        config_buttons_layout.addWidget(self._new_config_btn)
        self._save_config_btn = QPushButton('Save')
        self._save_config_btn.clicked.connect(self._on_save_config)
        config_buttons_layout.addWidget(self._save_config_btn)
        self._load_config_btn = QPushButton('Load')
        self._load_config_btn.clicked.connect(self._on_load_config)
        config_buttons_layout.addWidget(self._load_config_btn)
        config_layout.addLayout(config_buttons_layout)
        left_layout.addWidget(config_group)
        process_group = QGroupBox('Processing')
        process_layout = QVBoxLayout(process_group)
        self._process_selected_btn = QPushButton('Process Selected Files')
        self._process_selected_btn.clicked.connect(self._on_process_selected)
        process_layout.addWidget(self._process_selected_btn)
        self._process_all_btn = QPushButton('Process All Files')
        self._process_all_btn.clicked.connect(self._on_process_all)
        process_layout.addWidget(self._process_all_btn)
        process_layout.addWidget(QLabel('Output Directory:'))
        output_dir_layout = QHBoxLayout()
        self._output_dir_edit = QLabel('(Default)')
        self._output_dir_edit.setFrameShape(QFrame.Panel)
        self._output_dir_edit.setFrameShadow(QFrame.Sunken)
        self._output_dir_edit.setMinimumHeight(24)
        output_dir_layout.addWidget(self._output_dir_edit, 1)
        self._browse_output_btn = QToolButton()
        self._browse_output_btn.setText('...')
        self._browse_output_btn.clicked.connect(self._on_browse_output)
        output_dir_layout.addWidget(self._browse_output_btn)
        process_layout.addLayout(output_dir_layout)
        self._overwrite_checkbox = QCheckBox('Overwrite existing files')
        process_layout.addWidget(self._overwrite_checkbox)
        left_layout.addWidget(process_group)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        preview_group = QGroupBox('Preview')
        preview_layout = QVBoxLayout(preview_group)
        self._preview_widget = ImagePreviewWidget(self._logger)
        self._preview_widget.setMinimumSize(400, 300)
        preview_layout.addWidget(self._preview_widget)
        preview_controls_layout = QHBoxLayout()
        self._prev_file_btn = QPushButton('Previous')
        self._prev_file_btn.clicked.connect(self._on_previous_file)
        preview_controls_layout.addWidget(self._prev_file_btn)
        self._file_counter_label = QLabel('0/0')
        preview_controls_layout.addWidget(self._file_counter_label, 1, Qt.AlignCenter)
        self._next_file_btn = QPushButton('Next')
        self._next_file_btn.clicked.connect(self._on_next_file)
        preview_controls_layout.addWidget(self._next_file_btn)
        preview_layout.addLayout(preview_controls_layout)
        preview_options_layout = QHBoxLayout()
        self._preview_original_btn = QPushButton('Original')
        self._preview_original_btn.setCheckable(True)
        self._preview_original_btn.setChecked(True)
        self._preview_original_btn.clicked.connect(lambda: self._update_preview_mode('original'))
        preview_options_layout.addWidget(self._preview_original_btn)
        self._preview_background_btn = QPushButton('No Background')
        self._preview_background_btn.setCheckable(True)
        self._preview_background_btn.clicked.connect(lambda: self._update_preview_mode('background'))
        preview_options_layout.addWidget(self._preview_background_btn)
        self._preview_output_btn = QPushButton('Format')
        self._preview_output_btn.setCheckable(True)
        self._preview_output_btn.clicked.connect(lambda: self._update_preview_mode('output'))
        preview_options_layout.addWidget(self._preview_output_btn)
        preview_layout.addLayout(preview_options_layout)
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('Output Format:'))
        self._format_combo = QComboBox()
        self._format_combo.currentIndexChanged.connect(self._on_format_selected)
        format_layout.addWidget(self._format_combo, 1)
        self._edit_format_btn = QToolButton()
        self._edit_format_btn.setText('...')
        self._edit_format_btn.clicked.connect(self._on_edit_format)
        format_layout.addWidget(self._edit_format_btn)
        preview_layout.addLayout(format_layout)
        right_layout.addWidget(preview_group)
        details_group = QGroupBox('Output Details')
        details_layout = QVBoxLayout(details_group)
        self._details_scroll = QScrollArea()
        self._details_scroll.setWidgetResizable(True)
        self._details_scroll.setMinimumHeight(150)
        self._details_widget = QWidget()
        self._details_layout = QVBoxLayout(self._details_widget)
        self._details_layout.setAlignment(Qt.AlignTop)
        self._details_scroll.setWidget(self._details_widget)
        details_layout.addWidget(self._details_scroll)
        right_layout.addWidget(details_group)
        self._splitter.addWidget(left_panel)
        self._splitter.addWidget(right_panel)
        self._splitter.setSizes([300, 700])
        self._status_label = QLabel('Ready')
        main_layout.addWidget(self._status_label)
        self._update_ui_state()
    def _create_default_config(self) -> None:
        if not self._available_configs:
            from ..models.processing_config import ProcessingConfig, BackgroundRemovalConfig, OutputFormat, BackgroundRemovalMethod, ImageFormat, ResizeMode
            default_format = OutputFormat(name='PNG (Transparent)', format=ImageFormat.PNG, transparent_background=True, resize_mode=ResizeMode.NONE)
            default_config = ProcessingConfig(name='Default Configuration', description='Default processing configuration with transparent PNG output', background_removal=BackgroundRemovalConfig(method=BackgroundRemovalMethod.ALPHA_MATTING), output_formats=[default_format])
            self._available_configs[default_config.id] = default_config
            self._current_config = default_config
            self._update_config_combo()
            self._update_format_combo()
    async def _load_configs_async(self) -> None:
        try:
            self._logger.debug('Loading configurations...')
            asyncio.create_task(self._update_ui_with_configs())
        except Exception as e:
            self._logger.error(f'Error loading configurations: {str(e)}')
    async def _update_ui_with_configs(self) -> None:
        if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
            await self._concurrency_manager.run_on_main_thread(lambda: asyncio.create_task(self._update_ui_with_configs()))
            return
        self._update_config_combo()
        self._update_format_combo()
        self._update_ui_state()
    def _update_config_combo(self) -> None:
        self._config_combo.blockSignals(True)
        self._config_combo.clear()
        for config_id, config in self._available_configs.items():
            self._config_combo.addItem(config.name, config_id)
        if self._current_config:
            index = self._config_combo.findData(self._current_config.id)
            if index >= 0:
                self._config_combo.setCurrentIndex(index)
        self._config_combo.blockSignals(False)
    def _update_format_combo(self) -> None:
        self._format_combo.blockSignals(True)
        self._format_combo.clear()
        if self._current_config and self._current_config.output_formats:
            for format_config in self._current_config.output_formats:
                self._format_combo.addItem(format_config.name, format_config.id)
            self._format_combo.setCurrentIndex(0)
        self._format_combo.blockSignals(False)
    def _update_ui_state(self) -> None:
        has_files = bool(self._selected_files)
        has_selection = bool(self._file_list.selectedItems())
        self._remove_files_btn.setEnabled(has_selection)
        self._process_selected_btn.setEnabled(has_selection and (not self._processing))
        self._process_all_btn.setEnabled(has_files and (not self._processing))
        has_multiple_files = len(self._selected_files) > 1
        current_valid = 0 <= self._current_file_index < len(self._selected_files)
        self._prev_file_btn.setEnabled(current_valid and self._current_file_index > 0)
        self._next_file_btn.setEnabled(current_valid and self._current_file_index < len(self._selected_files) - 1)
        if has_files:
            self._file_counter_label.setText(f'{(self._current_file_index + 1 if current_valid else 0)}/{len(self._selected_files)}')
        else:
            self._file_counter_label.setText('0/0')
        has_config = self._current_config is not None
        self._edit_config_btn.setEnabled(has_config)
        self._save_config_btn.setEnabled(has_config)
        has_formats = has_config and bool(self._current_config.output_formats)
        self._format_combo.setEnabled(has_formats)
        self._edit_format_btn.setEnabled(has_formats and self._format_combo.currentIndex() >= 0)
        self._preview_background_btn.setEnabled(has_config and current_valid)
        self._preview_output_btn.setEnabled(has_formats and current_valid)
        if self._processing:
            self._add_files_btn.setEnabled(False)
            self._add_folder_btn.setEnabled(False)
            self._remove_files_btn.setEnabled(False)
            self._process_selected_btn.setEnabled(False)
            self._process_all_btn.setEnabled(False)
            self._edit_config_btn.setEnabled(False)
            self._new_config_btn.setEnabled(False)
            self._save_config_btn.setEnabled(False)
            self._load_config_btn.setEnabled(False)
    def _update_preview_mode(self, mode: str) -> None:
        self._preview_original_btn.setChecked(mode == 'original')
        self._preview_background_btn.setChecked(mode == 'background')
        self._preview_output_btn.setChecked(mode == 'output')
        asyncio.create_task(self._generate_preview(mode))
    async def _generate_preview(self, mode: str) -> None:
        if not self._selected_files or self._current_file_index < 0:
            self._preview_widget.clear()
            return
        try:
            current_file = self._selected_files[self._current_file_index]
            if mode == 'original':
                self._preview_widget.set_loading(True)
                self._preview_widget.load_image(current_file)
                self._preview_widget.set_loading(False)
            elif mode == 'background' and self._current_config:
                self._preview_widget.set_loading(True)
                preview_data = await self._media_processor.create_preview(current_file, self._current_config.background_removal, size=800)
                self._preview_widget.load_image_data(preview_data)
                self._preview_widget.set_loading(False)
            elif mode == 'output' and self._current_config and self._current_config.output_formats:
                self._preview_widget.set_loading(True)
                format_index = self._format_combo.currentIndex()
                if format_index >= 0 and format_index < len(self._current_config.output_formats):
                    format_config = self._current_config.output_formats[format_index]
                    preview_data = await self._media_processor.create_preview(current_file, format_config, size=800)
                    self._preview_widget.load_image_data(preview_data)
                self._preview_widget.set_loading(False)
        except Exception as e:
            self._logger.error(f'Error generating preview: {str(e)}')
            self._preview_widget.set_error(f'Error: {str(e)}')
            self._preview_widget.set_loading(False)
    def _update_output_details(self) -> None:
        for i in reversed(range(self._details_layout.count())):
            item = self._details_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        if not self._selected_files or self._current_file_index < 0 or (not self._current_config):
            self._details_layout.addWidget(QLabel('No output details available'))
            return
        current_file = self._selected_files[self._current_file_index]
        filename = os.path.basename(current_file)
        file_label = QLabel(f'<b>Input:</b> {filename}')
        file_label.setWordWrap(True)
        self._details_layout.addWidget(file_label)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self._details_layout.addWidget(line)
        for i, format_config in enumerate(self._current_config.output_formats):
            name, ext = os.path.splitext(filename)
            format_ext = format_config.format.value
            if format_config.naming_template:
                from ..utils.path_resolver import generate_filename
                output_name = generate_filename(format_config.naming_template, name, format_ext, format_config.prefix, format_config.suffix)
            else:
                prefix = format_config.prefix or ''
                suffix = format_config.suffix or ''
                output_name = f'{prefix}{name}{suffix}.{format_ext}'
            output_dir = self._current_config.output_directory or '(Default Output Directory)'
            if format_config.subdir:
                output_dir = os.path.join(output_dir, format_config.subdir)
            format_label = QLabel(f'<b>Output Format {i + 1}:</b> {format_config.name}')
            format_label.setStyleSheet('margin-top: 10px;')
            self._details_layout.addWidget(format_label)
            path_label = QLabel(f'<b>Output Path:</b> {os.path.join(output_dir, output_name)}')
            path_label.setWordWrap(True)
            self._details_layout.addWidget(path_label)
            details = []
            details.append(f'Format: {format_config.format.value.upper()}')
            if format_config.transparent_background:
                details.append('Background: Transparent')
            elif format_config.background_color:
                details.append(f'Background: {format_config.background_color}')
            if format_config.resize_mode.value != 'none':
                details.append(f'Resize: {format_config.resize_mode.value}')
                if format_config.width:
                    details.append(f'Width: {format_config.width}px')
                if format_config.height:
                    details.append(f'Height: {format_config.height}px')
                if format_config.percentage:
                    details.append(f'Scale: {format_config.percentage}%')
            details_text = ', '.join(details)
            details_label = QLabel(f'<b>Settings:</b> {details_text}')
            details_label.setWordWrap(True)
            self._details_layout.addWidget(details_label)
    @Slot()
    def _on_add_files(self) -> None:
        file_formats = self._plugin_config.get('formats', {}).get('allowed_input', [])
        filter_str = f"Images ({' '.join(['*.' + fmt for fmt in file_formats])})"
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Select Image Files', '', filter_str)
        if file_paths:
            self._add_files(file_paths)
    @Slot()
    def _on_add_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder with Images', '')
        if folder_path:
            file_formats = self._plugin_config.get('formats', {}).get('allowed_input', [])
            image_files = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1][1:].lower()
                    if ext in file_formats:
                        image_files.append(os.path.join(root, file))
            if image_files:
                self._add_files(image_files)
            else:
                QMessageBox.information(self, 'No Images Found', f'No supported image files found in {folder_path}')
    def _add_files(self, file_paths: List[str]) -> None:
        for file_path in file_paths:
            existing_items = self._file_list.findItems(file_path, Qt.MatchExactly)
            if not existing_items:
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                item.setToolTip(file_path)
                self._file_list.addItem(item)
                self._selected_files.append(file_path)
        if self._current_file_index < 0 and self._selected_files:
            self._current_file_index = 0
            self._file_list.setCurrentRow(0)
        self._update_ui_state()
        self._update_output_details()
        asyncio.create_task(self._generate_preview('original' if self._preview_original_btn.isChecked() else 'background' if self._preview_background_btn.isChecked() else 'output'))
    @Slot()
    def _on_remove_files(self) -> None:
        selected_items = self._file_list.selectedItems()
        if not selected_items:
            return
        paths_to_remove = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            paths_to_remove.append(file_path)
        for item in selected_items:
            self._file_list.takeItem(self._file_list.row(item))
        for path in paths_to_remove:
            if path in self._selected_files:
                self._selected_files.remove(path)
        self._current_file_index = self._file_list.currentRow()
        self._update_ui_state()
        self._update_output_details()
        if self._current_file_index >= 0:
            asyncio.create_task(self._generate_preview('original' if self._preview_original_btn.isChecked() else 'background' if self._preview_background_btn.isChecked() else 'output'))
        else:
            self._preview_widget.clear()
    @Slot()
    def _on_file_selection_changed(self) -> None:
        selected_items = self._file_list.selectedItems()
        if not selected_items:
            return
        self._current_file_index = self._file_list.currentRow()
        self._update_ui_state()
        self._update_output_details()
        asyncio.create_task(self._generate_preview('original' if self._preview_original_btn.isChecked() else 'background' if self._preview_background_btn.isChecked() else 'output'))
    @Slot()
    def _on_previous_file(self) -> None:
        if self._current_file_index > 0:
            self._current_file_index -= 1
            self._file_list.setCurrentRow(self._current_file_index)
    @Slot()
    def _on_next_file(self) -> None:
        if self._current_file_index < len(self._selected_files) - 1:
            self._current_file_index += 1
            self._file_list.setCurrentRow(self._current_file_index)
    @Slot(int)
    def _on_config_selected(self, index: int) -> None:
        if index < 0:
            return
        config_id = self._config_combo.itemData(index)
        if config_id in self._available_configs:
            self._current_config = self._available_configs[config_id]
            self._update_format_combo()
            self._update_ui_state()
            self._update_output_details()
            if self._preview_background_btn.isChecked() or self._preview_output_btn.isChecked():
                asyncio.create_task(self._generate_preview('background' if self._preview_background_btn.isChecked() else 'output'))
            self.configChanged.emit(config_id)
    @Slot(int)
    def _on_format_selected(self, index: int) -> None:
        if self._preview_output_btn.isChecked():
            asyncio.create_task(self._generate_preview('output'))
        self._update_output_details()
    @Slot()
    def _on_edit_config(self) -> None:
        if not self._current_config:
            return
        config_editor = ConfigEditorDialog(self._media_processor, self._file_manager, self._logger, self._plugin_config, self._current_config, self)
        config_editor.configUpdated.connect(self._on_config_updated)
        config_editor.exec()
    @Slot()
    def _on_new_config(self) -> None:
        from ..models.processing_config import ProcessingConfig, BackgroundRemovalConfig, OutputFormat, ImageFormat
        new_config = ProcessingConfig(name='New Configuration', description='New processing configuration', background_removal=BackgroundRemovalConfig(), output_formats=[OutputFormat(name='Default Output', format=ImageFormat.PNG)])
        self._available_configs[new_config.id] = new_config
        self._current_config = new_config
        self._update_config_combo()
        self._update_format_combo()
        self._update_ui_state()
        self._update_output_details()
        self._on_edit_config()
    @Slot()
    def _on_save_config(self) -> None:
        if not self._current_config:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Configuration', f'{self._current_config.name}.json', 'Configuration Files (*.json)')
        if not file_path:
            return
        asyncio.create_task(self._save_config_to_file(self._current_config, file_path))
    async def _save_config_to_file(self, config: ProcessingConfig, file_path: str) -> None:
        try:
            saved_path = await self._media_processor.save_processing_config(config, file_path)
            if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.information(self, 'Configuration Saved', f'Configuration saved to {saved_path}'))
            else:
                QMessageBox.information(self, 'Configuration Saved', f'Configuration saved to {saved_path}')
        except Exception as e:
            self._logger.error(f'Error saving configuration: {str(e)}')
            if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.critical(self, 'Error', f'Error saving configuration: {str(e)}'))
            else:
                QMessageBox.critical(self, 'Error', f'Error saving configuration: {str(e)}')
    @Slot()
    def _on_load_config(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, 'Load Configuration', '', 'Configuration Files (*.json)')
        if not file_path:
            return
        asyncio.create_task(self._load_config_from_file(file_path))
    async def _load_config_from_file(self, file_path: str) -> None:
        try:
            config = await self._media_processor.load_processing_config(file_path)
            self._available_configs[config.id] = config
            self._current_config = config
            if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
                await self._concurrency_manager.run_on_main_thread(self._update_ui_after_config_load)
            else:
                self._update_ui_after_config_load()
        except Exception as e:
            self._logger.error(f'Error loading configuration: {str(e)}')
            if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.critical(self, 'Error', f'Error loading configuration: {str(e)}'))
            else:
                QMessageBox.critical(self, 'Error', f'Error loading configuration: {str(e)}')
    def _update_ui_after_config_load(self) -> None:
        self._update_config_combo()
        self._update_format_combo()
        self._update_ui_state()
        self._update_output_details()
        if self._preview_background_btn.isChecked() or self._preview_output_btn.isChecked():
            asyncio.create_task(self._generate_preview('background' if self._preview_background_btn.isChecked() else 'output'))
    @Slot(str)
    def _on_config_updated(self, config_id: str) -> None:
        self._update_config_combo()
        self._update_format_combo()
        self._update_ui_state()
        self._update_output_details()
        if self._preview_background_btn.isChecked() or self._preview_output_btn.isChecked():
            asyncio.create_task(self._generate_preview('background' if self._preview_background_btn.isChecked() else 'output'))
    @Slot()
    def _on_edit_format(self) -> None:
        if not self._current_config or not self._current_config.output_formats:
            return
        format_index = self._format_combo.currentIndex()
        if format_index < 0 or format_index >= len(self._current_config.output_formats):
            return
        format_config = self._current_config.output_formats[format_index]
        format_editor = FormatEditorDialog(format_config, self._logger, self)
        if format_editor.exec() == QDialog.Accepted:
            updated_format = format_editor.get_format()
            self._current_config.output_formats[format_index] = updated_format
            self._update_format_combo()
            for i in range(self._format_combo.count()):
                if self._format_combo.itemData(i) == updated_format.id:
                    self._format_combo.setCurrentIndex(i)
                    break
            self._update_output_details()
            if self._preview_output_btn.isChecked():
                asyncio.create_task(self._generate_preview('output'))
    @Slot()
    def _on_browse_output(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Output Directory', '')
        if folder_path:
            self._output_dir_edit.setText(folder_path)
            if self._current_config:
                self._current_config.output_directory = folder_path
                self._update_output_details()
    @Slot()
    def _on_process_selected(self) -> None:
        selected_items = self._file_list.selectedItems()
        if not selected_items or not self._current_config:
            return
        file_paths = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            file_paths.append(file_path)
        self._process_files(file_paths)
    @Slot()
    def _on_process_all(self) -> None:
        if not self._selected_files or not self._current_config:
            return
        self._process_files(self._selected_files)
    def _process_files(self, file_paths: List[str]) -> None:
        if not file_paths or not self._current_config:
            return
        if len(file_paths) == 1:
            asyncio.create_task(self._process_single_file(file_paths[0]))
            return
        output_dir = self._current_config.output_directory
        if self._output_dir_edit.text() != '(Default)':
            output_dir = self._output_dir_edit.text()
        batch_dialog = BatchProcessingDialog(self._batch_processor, file_paths, self._current_config, output_dir, self._overwrite_checkbox.isChecked(), self._logger, self)
        batch_dialog.exec()
    async def _process_single_file(self, file_path: str) -> None:
        if not self._current_config:
            return
        self._processing = True
        self._update_ui_state()
        self._status_label.setText(f'Processing {os.path.basename(file_path)}...')
        self.processingStarted.emit()
        try:
            output_dir = self._current_config.output_directory
            if self._output_dir_edit.text() != '(Default)':
                output_dir = self._output_dir_edit.text()
            output_paths = await self._media_processor.process_image(file_path, self._current_config, output_dir, self._overwrite_checkbox.isChecked())
            output_files_str = '\n'.join(output_paths)
            if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.information(self, 'Processing Complete', f'Successfully processed {os.path.basename(file_path)}.\n\nOutput files:\n{output_files_str}'))
            else:
                QMessageBox.information(self, 'Processing Complete', f'Successfully processed {os.path.basename(file_path)}.\n\nOutput files:\n{output_files_str}')
            self.processingFinished.emit(True, f'Successfully processed {os.path.basename(file_path)}')
        except Exception as e:
            self._logger.error(f'Error processing file: {str(e)}')
            if self._concurrency_manager and (not self._concurrency_manager.is_main_thread()):
                await self._concurrency_manager.run_on_main_thread(lambda: QMessageBox.critical(self, 'Error', f'Error processing file: {str(e)}'))
            else:
                QMessageBox.critical(self, 'Error', f'Error processing file: {str(e)}')
            self.processingFinished.emit(False, f'Error: {str(e)}')
        finally:
            self._processing = False
            self._update_ui_state()
            self._status_label.setText('Ready')
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isdir(file_path):
                    file_formats = self._plugin_config.get('formats', {}).get('allowed_input', [])
                    for root, _, files in os.walk(file_path):
                        for file in files:
                            ext = os.path.splitext(file)[1][1:].lower()
                            if ext in file_formats:
                                file_paths.append(os.path.join(root, file))
                elif os.path.isfile(file_path):
                    ext = os.path.splitext(file_path)[1][1:].lower()
                    file_formats = self._plugin_config.get('formats', {}).get('allowed_input', [])
                    if ext in file_formats:
                        file_paths.append(file_path)
            if file_paths:
                self._add_files(file_paths)
            event.acceptProposedAction()