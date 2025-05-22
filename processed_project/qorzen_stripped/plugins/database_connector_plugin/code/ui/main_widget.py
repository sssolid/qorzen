from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QMessageBox, QProgressBar, QLabel, QHBoxLayout, QFrame
from .main_tab import MainTab
from .results_tab import ResultsTab
from .field_mapping_tab import FieldMappingTab
from .validation_tab import ValidationTab
from .history_tab import HistoryTab
class DatabasePluginWidget(QWidget):
    def __init__(self, plugin: Any, logger: logging.Logger, concurrency_manager: Any, event_bus_manager: Any, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._plugin = plugin
        self._logger = logger
        self._concurrency_manager = concurrency_manager
        self._event_bus_manager = event_bus_manager
        self._tab_widget: Optional[QTabWidget] = None
        self._main_tab: Optional[MainTab] = None
        self._results_tab: Optional[ResultsTab] = None
        self._field_mapping_tab: Optional[FieldMappingTab] = None
        self._validation_tab: Optional[ValidationTab] = None
        self._history_tab: Optional[HistoryTab] = None
        self._status_bar: Optional[QFrame] = None
        self._status_label: Optional[QLabel] = None
        self._progress_bar: Optional[QProgressBar] = None
        self._setup_ui()
        self._setup_connections()
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start(5000)
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._tab_widget = QTabWidget()
        self._main_tab = MainTab(plugin=self._plugin, logger=self._logger, concurrency_manager=self._concurrency_manager, event_bus_manager=self._event_bus_manager, parent=self)
        self._results_tab = ResultsTab(plugin=self._plugin, logger=self._logger, concurrency_manager=self._concurrency_manager, parent=self)
        self._field_mapping_tab = FieldMappingTab(plugin=self._plugin, logger=self._logger, concurrency_manager=self._concurrency_manager, parent=self)
        self._validation_tab = ValidationTab(plugin=self._plugin, logger=self._logger, concurrency_manager=self._concurrency_manager, parent=self)
        self._history_tab = HistoryTab(plugin=self._plugin, logger=self._logger, concurrency_manager=self._concurrency_manager, parent=self)
        self._tab_widget.addTab(self._main_tab, 'Connections & Queries')
        self._tab_widget.addTab(self._results_tab, 'Results')
        self._tab_widget.addTab(self._field_mapping_tab, 'Field Mapping')
        self._tab_widget.addTab(self._validation_tab, 'Validation')
        self._tab_widget.addTab(self._history_tab, 'History')
        layout.addWidget(self._tab_widget)
        self._create_status_bar()
        layout.addWidget(self._status_bar)
    def _create_status_bar(self) -> None:
        self._status_bar = QFrame()
        self._status_bar.setFrameStyle(QFrame.Shape.StyledPanel)
        self._status_bar.setMaximumHeight(30)
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(5, 2, 5, 2)
        self._status_label = QLabel('Ready')
        self._status_label.setMinimumWidth(200)
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximumWidth(200)
        self._progress_bar.setVisible(False)
        status_layout.addWidget(self._progress_bar)
    def _setup_connections(self) -> None:
        if not all([self._main_tab, self._results_tab, self._field_mapping_tab, self._validation_tab, self._history_tab]):
            return
        self._main_tab.query_executed.connect(self._results_tab.show_results)
        self._main_tab.query_executed.connect(lambda: self.switch_to_tab(1))
        self._main_tab.operation_started.connect(self._show_progress)
        self._main_tab.operation_finished.connect(self._hide_progress)
        self._main_tab.status_changed.connect(self._update_status_message)
        self._results_tab.operation_started.connect(self._show_progress)
        self._results_tab.operation_finished.connect(self._hide_progress)
        self._results_tab.status_changed.connect(self._update_status_message)
        self._field_mapping_tab.operation_started.connect(self._show_progress)
        self._field_mapping_tab.operation_finished.connect(self._hide_progress)
        self._field_mapping_tab.status_changed.connect(self._update_status_message)
        self._validation_tab.operation_started.connect(self._show_progress)
        self._validation_tab.operation_finished.connect(self._hide_progress)
        self._validation_tab.status_changed.connect(self._update_status_message)
        self._history_tab.operation_started.connect(self._show_progress)
        self._history_tab.operation_finished.connect(self._hide_progress)
        self._history_tab.status_changed.connect(self._update_status_message)
    def switch_to_tab(self, index: int) -> None:
        if self._tab_widget and 0 <= index < self._tab_widget.count():
            self._tab_widget.setCurrentIndex(index)
    def get_current_tab_index(self) -> int:
        return self._tab_widget.currentIndex() if self._tab_widget else 0
    def _show_progress(self, message: str='Working...') -> None:
        if self._progress_bar and self._status_label:
            self._status_label.setText(message)
            self._progress_bar.setVisible(True)
            self._progress_bar.setRange(0, 0)
    def _hide_progress(self) -> None:
        if self._progress_bar:
            self._progress_bar.setVisible(False)
        self._update_status_message('Ready')
    def _update_status_message(self, message: str) -> None:
        if self._status_label:
            self._status_label.setText(message)
    def _update_status(self) -> None:
        try:
            if not self._plugin:
                return
            status = self._plugin.status()
            if self._progress_bar and (not self._progress_bar.isVisible()):
                connections_count = status.get('connections', {}).get('total', 0)
                active_connections = status.get('connections', {}).get('active', 0)
                saved_queries = status.get('queries', {}).get('saved', 0)
                status_text = f'Connections: {active_connections}/{connections_count} | Saved Queries: {saved_queries}'
                self._update_status_message(status_text)
        except Exception as e:
            self._logger.warning(f'Failed to update status: {e}')
    async def refresh_all_tabs(self) -> None:
        try:
            self._show_progress('Refreshing data...')
            tasks = []
            if self._main_tab:
                tasks.append(self._main_tab.refresh())
            if self._results_tab:
                tasks.append(self._results_tab.refresh())
            if self._field_mapping_tab:
                tasks.append(self._field_mapping_tab.refresh())
            if self._validation_tab:
                tasks.append(self._validation_tab.refresh())
            if self._history_tab:
                tasks.append(self._history_tab.refresh())
            await asyncio.gather(*tasks, return_exceptions=True)
            self._hide_progress()
            self._logger.info('All tabs refreshed successfully')
        except Exception as e:
            self._hide_progress()
            self._logger.error(f'Failed to refresh tabs: {e}')
            self._show_error('Refresh Error', f'Failed to refresh data: {e}')
    def _show_error(self, title: str, message: str) -> None:
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.exec()
        except Exception as e:
            self._logger.error(f'Failed to show error dialog: {e}')
    def _show_info(self, title: str, message: str) -> None:
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.exec()
        except Exception as e:
            self._logger.error(f'Failed to show info dialog: {e}')
    def _show_warning(self, title: str, message: str) -> None:
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.exec()
        except Exception as e:
            self._logger.error(f'Failed to show warning dialog: {e}')
    def closeEvent(self, event) -> None:
        try:
            if self._update_timer:
                self._update_timer.stop()
            if self._main_tab:
                self._main_tab.cleanup()
            if self._results_tab:
                self._results_tab.cleanup()
            if self._field_mapping_tab:
                self._field_mapping_tab.cleanup()
            if self._validation_tab:
                self._validation_tab.cleanup()
            if self._history_tab:
                self._history_tab.cleanup()
            self._logger.debug('Database plugin widget closed')
        except Exception as e:
            self._logger.error(f'Error during widget cleanup: {e}')
        super().closeEvent(event)
    def get_main_tab(self) -> Optional[MainTab]:
        return self._main_tab
    def get_results_tab(self) -> Optional[ResultsTab]:
        return self._results_tab
    def get_field_mapping_tab(self) -> Optional[FieldMappingTab]:
        return self._field_mapping_tab
    def get_validation_tab(self) -> Optional[ValidationTab]:
        return self._validation_tab
    def get_history_tab(self) -> Optional[HistoryTab]:
        return self._history_tab