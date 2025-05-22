from __future__ import annotations
'\nAI Model Manager Dialog for downloading and managing AI models.\n\nThis module provides a user interface for downloading, managing, and activating\nthe AI models used for background removal.\n'
import os
import asyncio
from typing import Dict, List, Optional, Any, cast
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QListWidget, QListWidgetItem, QTabWidget, QWidget, QMessageBox, QGroupBox, QFormLayout, QSpacerItem, QSizePolicy, QCheckBox
from ..utils.ai_background_remover import AIBackgroundRemover, ModelDetails, ModelType
class ModelDownloadWorker(QObject):
    progressChanged = Signal(int, str)
    finished = Signal(bool, str)
    def __init__(self, ai_background_remover: AIBackgroundRemover, model_id: str) -> None:
        super().__init__()
        self._ai_background_remover = ai_background_remover
        self._model_id = model_id
    @Slot()
    async def download(self) -> None:
        try:
            async def progress_callback(percent: int, message: str) -> None:
                self.progressChanged.emit(percent, message)
            await self._ai_background_remover.download_model(self._model_id, progress_callback)
            self.finished.emit(True, f'Model {self._model_id} downloaded successfully.')
        except Exception as e:
            self.finished.emit(False, f'Error downloading model: {str(e)}')
class AIModelManagerDialog(QDialog):
    modelDownloaded = Signal(str)
    def __init__(self, ai_background_remover: AIBackgroundRemover, config_manager: Any, logger: Any, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._ai_background_remover = ai_background_remover
        self._config_manager = config_manager
        self._logger = logger
        self._download_thread: Optional[QThread] = None
        self._download_worker: Optional[ModelDownloadWorker] = None
        self._current_model: Optional[str] = None
        self._init_ui()
        self.setWindowTitle('AI Model Manager')
        self.resize(600, 500)
        asyncio.create_task(self._update_model_list())
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        header_layout = QVBoxLayout()
        title_label = QLabel('AI Model Manager')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        header_layout.addWidget(title_label)
        desc_label = QLabel('Download and manage AI models for background removal. These models provide high-quality background removal capabilities.')
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)
        layout.addLayout(header_layout)
        tab_widget = QTabWidget()
        models_tab = QWidget()
        models_layout = QVBoxLayout(models_tab)
        self._model_list = QListWidget()
        self._model_list.setAlternatingRowColors(True)
        self._model_list.currentItemChanged.connect(self._on_model_selected)
        models_layout.addWidget(self._model_list)
        details_group = QGroupBox('Model Details')
        details_layout = QFormLayout(details_group)
        self._model_name_label = QLabel('')
        details_layout.addRow('Name:', self._model_name_label)
        self._model_desc_label = QLabel('')
        self._model_desc_label.setWordWrap(True)
        details_layout.addRow('Description:', self._model_desc_label)
        self._model_size_label = QLabel('')
        details_layout.addRow('Size:', self._model_size_label)
        self._model_status_label = QLabel('')
        details_layout.addRow('Status:', self._model_status_label)
        models_layout.addWidget(details_group)
        download_layout = QHBoxLayout()
        self._download_btn = QPushButton('Download')
        self._download_btn.clicked.connect(self._on_download)
        self._download_btn.setEnabled(False)
        download_layout.addWidget(self._download_btn)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        download_layout.addWidget(self._progress_bar, 1)
        models_layout.addLayout(download_layout)
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        use_gpu_check = QCheckBox('Use GPU for inference (if available)')
        use_gpu_check.setChecked(True)
        settings_layout.addWidget(use_gpu_check)
        auto_download_check = QCheckBox('Automatically download models when needed')
        auto_download_check.setChecked(False)
        settings_layout.addWidget(auto_download_check)
        mem_limit_group = QGroupBox('Memory Usage Limits')
        mem_layout = QVBoxLayout(mem_limit_group)
        mem_limit_desc = QLabel('These settings control how much memory the AI models can use. Lower values use less memory but may be slower.')
        mem_limit_desc.setWordWrap(True)
        mem_layout.addWidget(mem_limit_desc)
        memory_opt_layout = QHBoxLayout()
        memory_opt_layout.addWidget(QLabel('Memory Optimization:'))
        memory_opt_btns = [QPushButton('Low Memory'), QPushButton('Balanced'), QPushButton('Performance')]
        for btn in memory_opt_btns:
            memory_opt_layout.addWidget(btn)
        mem_layout.addLayout(memory_opt_layout)
        settings_layout.addWidget(mem_limit_group)
        settings_layout.addStretch()
        tab_widget.addTab(models_tab, 'Available Models')
        tab_widget.addTab(settings_tab, 'Settings')
        layout.addWidget(tab_widget, 1)
        self._status_label = QLabel('Ready')
        layout.addWidget(self._status_label)
        buttons_layout = QHBoxLayout()
        self._close_btn = QPushButton('Close')
        self._close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self._close_btn)
        layout.addLayout(buttons_layout)
    async def _update_model_list(self) -> None:
        self._model_list.clear()
        for model_id, model_info in ModelDetails.MODELS.items():
            item = QListWidgetItem(model_info['name'])
            item.setData(Qt.UserRole, model_id)
            is_downloaded = await self._ai_background_remover.is_model_downloaded(model_id)
            desc = model_info['description']
            size_mb = model_info['size'] / (1024 * 1024)
            tooltip = f'{desc}\nSize: {size_mb:.1f} MB'
            if is_downloaded:
                tooltip += '\nStatus: Downloaded'
            else:
                tooltip += '\nStatus: Not downloaded'
            item.setToolTip(tooltip)
            if is_downloaded:
                item.setIcon(QIcon.fromTheme('dialog-ok-apply'))
            self._model_list.addItem(item)
    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_model_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if not current:
            self._download_btn.setEnabled(False)
            self._model_name_label.setText('')
            self._model_desc_label.setText('')
            self._model_size_label.setText('')
            self._model_status_label.setText('')
            return
        model_id = current.data(Qt.UserRole)
        self._current_model = model_id
        asyncio.create_task(self._update_model_details(model_id))
    async def _update_model_details(self, model_id: str) -> None:
        model_info = await self._ai_background_remover.get_model_info(model_id)
        self._model_name_label.setText(model_info['name'])
        self._model_desc_label.setText(model_info['description'])
        size_mb = model_info['size'] / (1024 * 1024)
        self._model_size_label.setText(f'{size_mb:.1f} MB')
        is_downloaded = model_info.get('downloaded', False)
        if is_downloaded:
            self._model_status_label.setText('Downloaded')
            self._model_status_label.setStyleSheet('color: green;')
            self._download_btn.setText('Redownload')
        else:
            self._model_status_label.setText('Not downloaded')
            self._model_status_label.setStyleSheet('color: red;')
            self._download_btn.setText('Download')
        self._download_btn.setEnabled(True)
    @Slot()
    def _on_download(self) -> None:
        if not self._current_model:
            return
        self._download_btn.setEnabled(False)
        self._model_list.setEnabled(False)
        self._close_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(True)
        model_id = self._current_model
        self._status_label.setText(f'Downloading model {model_id}...')
        self._download_thread = QThread()
        self._download_worker = ModelDownloadWorker(self._ai_background_remover, model_id)
        self._download_worker.progressChanged.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.moveToThread(self._download_thread)
        self._download_thread.started.connect(lambda: asyncio.create_task(self._download_worker.download()))
        self._download_thread.start()
    @Slot(int, str)
    def _on_download_progress(self, percent: int, message: str) -> None:
        self._progress_bar.setValue(percent)
        self._status_label.setText(message)
    @Slot(bool, str)
    def _on_download_finished(self, success: bool, message: str) -> None:
        if self._download_thread:
            self._download_thread.quit()
            self._download_thread.wait()
            self._download_thread = None
            self._download_worker = None
        self._progress_bar.setVisible(False)
        self._model_list.setEnabled(True)
        self._close_btn.setEnabled(True)
        self._status_label.setText(message)
        if success:
            asyncio.create_task(self._update_model_list())
            if self._current_model:
                self.modelDownloaded.emit(self._current_model)
        else:
            QMessageBox.critical(self, 'Download Error', message)
            self._download_btn.setEnabled(True)
    def closeEvent(self, event: Any) -> None:
        if self._download_thread and self._download_thread.isRunning():
            result = QMessageBox.question(self, 'Download in Progress', 'A model download is in progress. Do you want to cancel it?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if result == QMessageBox.Yes:
                if self._download_thread:
                    self._download_thread.quit()
                    self._download_thread.wait()
                    self._download_thread = None
                    self._download_worker = None
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()