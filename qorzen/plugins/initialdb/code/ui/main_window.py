from __future__ import annotations

import uuid
from datetime import datetime

"""
Main window for the InitialDB application with an IDE-like interface.

This module provides a modern, customizable main window with dockable panels
that users can rearrange to their preference, similar to an IDE.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import structlog
from PyQt6.QtCore import (
    QByteArray, QPoint, QSettings, QSize, Qt, pyqtSignal, pyqtSlot
)
from PyQt6.QtGui import QAction, QCloseEvent, QIcon, QCursor
from PyQt6.QtWidgets import (
    QApplication, QDockWidget, QFileDialog, QMainWindow, QMenu,
    QMenuBar, QMessageBox, QStatusBar, QTabWidget, QToolBar, QWidget, QDialog, QInputDialog
)
from qasync import asyncSlot

from ..config.settings import settings as app_settings
from ..models.schema import FilterDTO, SavedQueryDTO
from ..services.vehicle_service import VehicleService
from ..utils.dependency_container import resolve
from ..utils.schema_registry import SchemaRegistry
from ..utils.template_manager import TemplateManager
from ..utils.update_manager import UpdateManager
from .panels import BottomPanel, LeftPanel, RightPanel
from .settings_dialog.settings_dialog import SettingsDialog

logger = structlog.get_logger(__name__)


class MainWindow(QMainWindow):
    """Main window with IDE-like interface and dockable panels."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the main window.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        # Load dependencies
        self._registry = resolve(SchemaRegistry)
        self._vehicle_service = resolve(VehicleService)

        self.template_manager = TemplateManager()

        self.setWindowTitle('InitialDB')
        self.resize(1280, 800)

        # Setup UI Components
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_update_manager()

        # Connect signals
        self._connect_signals()

        # Load saved layout
        self._load_window_state()

        # Start with a default query tab
        self._create_results_tab("Query Results")

        logger.info("Main window initialized")

    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        # Set central widget to None - we'll use dock widgets
        self.setCentralWidget(None)

        # Create panels
        self._setup_panels()

    def _setup_panels(self) -> None:
        """Set up the dockable panels."""
        # Left Panel (Navigation)
        self.left_panel = LeftPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_panel)

        # Right Panel (Results)
        self.right_panel = RightPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_panel)

        # Bottom Panel (Information)
        self.update_manager = UpdateManager(
            parent_widget=self,
            status_bar=self.statusBar(),
            help_menu=None  # We'll add this later
        )
        self.bottom_panel = BottomPanel(self.update_manager, self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_panel)

        # Default layout
        self.resizeDocks(
            [self.left_panel, self.right_panel],
            [300, 700],
            Qt.Orientation.Horizontal
        )
        self.resizeDocks(
            [self.bottom_panel],
            [200],
            Qt.Orientation.Vertical
        )

    def _setup_menu(self) -> None:
        """Set up the application menu bar."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu('&File')

        new_query_action = QAction('&New Query', self)
        new_query_action.setShortcut('Ctrl+N')
        new_query_action.triggered.connect(self._new_query)
        file_menu.addAction(new_query_action)

        save_query_action = QAction('&Save Query...', self)
        save_query_action.setShortcut('Ctrl+S')
        save_query_action.triggered.connect(self._save_current_query)
        file_menu.addAction(save_query_action)

        file_menu.addSeparator()

        # Export submenu
        export_submenu = QMenu('&Export', self)

        export_csv_action = QAction('Export to &CSV...', self)
        export_csv_action.triggered.connect(lambda: self._export_data('csv'))
        export_submenu.addAction(export_csv_action)

        try:
            import openpyxl
            EXCEL_AVAILABLE = True
        except ImportError:
            EXCEL_AVAILABLE = False

        export_excel_action = QAction('Export to &Excel...', self)
        export_excel_action.triggered.connect(lambda: self._export_data('excel'))
        export_excel_action.setEnabled(EXCEL_AVAILABLE)
        export_submenu.addAction(export_excel_action)

        export_submenu.addSeparator()

        # Add template exports
        template_names = self.template_manager.get_template_names()
        if template_names:
            for template_name in template_names:
                template_submenu = QMenu(template_name, self)

                csv_template_action = QAction('Export to CSV', self)
                csv_template_action.triggered.connect(
                    lambda checked, t=template_name: self._export_to_template('csv', t)
                )
                template_submenu.addAction(csv_template_action)

                excel_template_action = QAction('Export to Excel', self)
                excel_template_action.triggered.connect(
                    lambda checked, t=template_name: self._export_to_template('excel', t)
                )
                excel_template_action.setEnabled(EXCEL_AVAILABLE)
                template_submenu.addAction(excel_template_action)

                export_submenu.addMenu(template_submenu)

        file_menu.addMenu(export_submenu)
        file_menu.addSeparator()

        settings_action = QAction('&Settings...', self)
        settings_action.triggered.connect(self._show_settings_dialog)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menu_bar.addMenu('&View')

        # Panel visibility actions
        left_panel_action = QAction('Navigation Panel', self)
        left_panel_action.setCheckable(True)
        left_panel_action.setChecked(True)
        left_panel_action.triggered.connect(
            lambda checked: self.left_panel.setVisible(checked)
        )
        view_menu.addAction(left_panel_action)

        right_panel_action = QAction('Results Panel', self)
        right_panel_action.setCheckable(True)
        right_panel_action.setChecked(True)
        right_panel_action.triggered.connect(
            lambda checked: self.right_panel.setVisible(checked)
        )
        view_menu.addAction(right_panel_action)

        bottom_panel_action = QAction('Information Panel', self)
        bottom_panel_action.setCheckable(True)
        bottom_panel_action.setChecked(True)
        bottom_panel_action.triggered.connect(
            lambda checked: self.bottom_panel.setVisible(checked)
        )
        view_menu.addAction(bottom_panel_action)

        view_menu.addSeparator()

        # Layout actions
        reset_layout_action = QAction('Reset Layout', self)
        reset_layout_action.triggered.connect(self._reset_layout)
        view_menu.addAction(reset_layout_action)

        save_layout_action = QAction('Save Layout...', self)
        save_layout_action.triggered.connect(self._save_layout)
        view_menu.addAction(save_layout_action)

        load_layout_action = QAction('Load Layout...', self)
        load_layout_action.triggered.connect(self._load_layout)
        view_menu.addAction(load_layout_action)

        view_menu.addSeparator()

        columns_action = QAction('Select &Columns...', self)
        columns_action.setShortcut('Ctrl+Shift+C')
        columns_action.triggered.connect(self._show_column_selection)
        view_menu.addAction(columns_action)

        # Query Menu
        query_menu = menu_bar.addMenu('&Query')

        execute_action = QAction('&Execute Query', self)
        execute_action.setShortcut('F5')
        execute_action.triggered.connect(self._execute_query)
        query_menu.addAction(execute_action)

        reset_action = QAction('&Reset All Filters', self)
        reset_action.triggered.connect(self._reset_filters)
        query_menu.addAction(reset_action)

        query_menu.addSeparator()

        query_manager_action = QAction('Query &Manager...', self)
        query_manager_action.setShortcut('Ctrl+M')
        query_manager_action.triggered.connect(self._show_query_manager)
        query_menu.addAction(query_manager_action)

        query_menu.addSeparator()

        # Saved queries submenu
        self.saved_queries_menu = QMenu('&Saved Queries', self)
        query_menu.addMenu(self.saved_queries_menu)

        # Templates Menu
        template_menu = menu_bar.addMenu('&Templates')

        manage_templates_action = QAction('&Manage Templates...', self)
        manage_templates_action.triggered.connect(self._show_template_manager)
        template_menu.addAction(manage_templates_action)

        template_menu.addSeparator()

        # Add template actions
        if template_names:
            for template_name in template_names:
                template_submenu = QMenu(template_name, self)

                export_csv_action = QAction('Export to CSV', self)
                export_csv_action.triggered.connect(
                    lambda checked, t=template_name: self._export_to_template('csv', t)
                )
                template_submenu.addAction(export_csv_action)

                export_excel_action = QAction('Export to Excel', self)
                export_excel_action.triggered.connect(
                    lambda checked, t=template_name: self._export_to_template('excel', t)
                )
                export_excel_action.setEnabled(EXCEL_AVAILABLE)
                template_submenu.addAction(export_excel_action)

                template_menu.addMenu(template_submenu)
        else:
            no_templates_action = QAction('No templates available', self)
            no_templates_action.setEnabled(False)
            template_menu.addAction(no_templates_action)

        # Help Menu
        self.help_menu = menu_bar.addMenu('&Help')

        about_action = QAction('&About', self)
        about_action.triggered.connect(self._show_about_dialog)
        self.help_menu.addAction(about_action)

        check_updates_action = QAction('Check for &Updates', self)
        check_updates_action.triggered.connect(
            lambda: self.update_manager.check_for_updates(force=True)
        )
        self.help_menu.addAction(check_updates_action)

    def _setup_toolbar(self) -> None:
        """Set up the application toolbar."""
        toolbar = QToolBar('Main Toolbar', self)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Query actions
        execute_action = QAction('Execute Query', self)
        execute_action.setShortcut('F5')
        execute_action.triggered.connect(self._execute_query)
        toolbar.addAction(execute_action)

        toolbar.addSeparator()

        reset_action = QAction('Reset Filters', self)
        reset_action.triggered.connect(self._reset_filters)
        toolbar.addAction(reset_action)

        add_query_action = QAction('Add Query', self)
        add_query_action.triggered.connect(self._add_query_section)
        toolbar.addAction(add_query_action)

        toolbar.addSeparator()

        # Management actions
        query_manager_action = QAction('Query Manager', self)
        query_manager_action.triggered.connect(self._show_query_manager)
        toolbar.addAction(query_manager_action)

        columns_action = QAction('Select Columns', self)
        columns_action.triggered.connect(self._show_column_selection)
        toolbar.addAction(columns_action)

        toolbar.addSeparator()

        # Save/export actions
        save_query_action = QAction('Save Query', self)
        save_query_action.triggered.connect(self._save_current_query)
        toolbar.addAction(save_query_action)

        # Export button with dropdown menu
        export_action = QAction('Export', self)
        export_action.triggered.connect(self._show_export_menu)
        toolbar.addAction(export_action)

    def _setup_status_bar(self) -> None:
        """Set up the application status bar."""
        self.statusBar().showMessage('Ready')

    def _setup_update_manager(self) -> None:
        """Set up the update manager."""
        # Add update manager to help menu
        self.update_manager._help_menu = self.help_menu
        self.update_manager.add_to_menu(self.help_menu)

    def _connect_signals(self) -> None:
        """Connect component signals."""
        # Left panel signals
        self.left_panel.query_executed.connect(self._on_query_results)
        self.left_panel.query_loaded.connect(self._on_query_loaded)

        # Right panel signals
        self.right_panel.tab_added.connect(self._on_tab_added)
        self.right_panel.tab_closed.connect(self._on_tab_closed)
        self.right_panel.tab_selected.connect(self._on_tab_selected)

    def _load_window_state(self) -> None:
        """Load saved window state and geometry."""
        if app_settings.get('remember_window_size', True):
            size_str = app_settings.get('window_size')
            if size_str:
                try:
                    size = QSize()
                    size_data = json.loads(size_str)
                    size.setWidth(size_data[0])
                    size.setHeight(size_data[1])
                    self.resize(size)
                except (ValueError, IndexError, TypeError):
                    logger.warning("Failed to parse saved window size")

        if app_settings.get('remember_window_position', True):
            pos_str = app_settings.get('window_position')
            if pos_str:
                try:
                    pos = QPoint()
                    pos_data = json.loads(pos_str)
                    pos.setX(pos_data[0])
                    pos.setY(pos_data[1])
                    self.move(pos)
                except (ValueError, IndexError, TypeError):
                    logger.warning("Failed to parse saved window position")

        if app_settings.get('remember_window_state', True):
            state_str = app_settings.get('window_state')
            if state_str:
                try:
                    state = QByteArray.fromBase64(state_str.encode('utf-8'))
                    self.restoreState(state)
                except Exception as e:
                    logger.warning(f"Failed to restore window state: {e}")

    def _save_window_state(self) -> None:
        """Save current window state and geometry."""
        # Save window size
        if app_settings.get('remember_window_size', True):
            size = self.size()
            app_settings.set('window_size', json.dumps([size.width(), size.height()]))

        # Save window position
        if app_settings.get('remember_window_position', True):
            pos = self.pos()
            app_settings.set('window_position', json.dumps([pos.x(), pos.y()]))

        # Save window state
        if app_settings.get('remember_window_state', True):
            state = self.saveState().toBase64().data().decode('utf-8')
            app_settings.set('window_state', state)

    def _reset_layout(self) -> None:
        """Reset the UI layout to default."""
        # Confirm with user
        result = QMessageBox.question(
            self,
            'Reset Layout',
            'Are you sure you want to reset the layout to default?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        # Save panel visibility state before reset
        panel_visibility = {}
        for dock_widget in self.findChildren(QDockWidget):
            panel_visibility[dock_widget.objectName()] = dock_widget.isVisible()

        # Ensure all panels are visible first (prevents issues with hidden panels)
        self.left_panel.setVisible(True)
        self.right_panel.setVisible(True)
        self.bottom_panel.setVisible(True)

        # Reset dock positions
        self.removeDockWidget(self.left_panel)
        self.removeDockWidget(self.right_panel)
        self.removeDockWidget(self.bottom_panel)

        # Add them back in the default locations
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_panel)

        # Reset sizes
        self.resizeDocks(
            [self.left_panel, self.right_panel],
            [300, 700],
            Qt.Orientation.Horizontal
        )
        self.resizeDocks(
            [self.bottom_panel],
            [200],
            Qt.Orientation.Vertical
        )

        # Restore panel visibility states
        for dock_widget in self.findChildren(QDockWidget):
            object_name = dock_widget.objectName()
            if object_name in panel_visibility:
                dock_widget.setVisible(panel_visibility[object_name])

        # Update view menu actions to match actual state
        view_menu = None
        for action in self.menuBar().actions():
            if action.text() == '&View':
                view_menu = action.menu()
                break

        if view_menu:
            for action in view_menu.actions():
                if not action.isCheckable():
                    continue

                # Match checkable actions with corresponding panels
                action_text = action.text()
                if "Navigation Panel" in action_text and hasattr(self, "left_panel"):
                    action.setChecked(self.left_panel.isVisible())
                elif "Results Panel" in action_text and hasattr(self, "right_panel"):
                    action.setChecked(self.right_panel.isVisible())
                elif "Information Panel" in action_text and hasattr(self, "bottom_panel"):
                    action.setChecked(self.bottom_panel.isVisible())

        self.statusBar().showMessage('Layout reset to default', 3000)

    def _save_layout(self) -> None:
        """Save the current UI layout."""
        layout_name, ok = QInputDialog.getText(
            self, 'Save Layout', 'Layout name:'
        )

        if not ok or not layout_name:
            return

        # Save the layout
        layout_state = {
            'window_state': self.saveState().toBase64().data().decode('utf-8'),
            'layout_name': layout_name,
            'saved_at': datetime.now().isoformat()
        }

        app_settings.save_layout(layout_name, layout_state)
        self.statusBar().showMessage(f'Layout "{layout_name}" saved', 3000)

    def _load_layout(self) -> None:
        """Load a saved UI layout."""
        # Get available layouts
        layouts = app_settings.get_available_layouts()

        if not layouts:
            QMessageBox.information(
                self,
                'No Layouts',
                'No saved layouts available.',
                QMessageBox.StandardButton.Ok
            )
            return

        # Show dialog to select layout
        layout_name, ok = QInputDialog.getItem(
            self, 'Load Layout', 'Select layout:', layouts, 0, False
        )

        if not ok or not layout_name:
            return

        # Load the layout
        layout_state = app_settings.load_layout(layout_name)
        if not layout_state or 'window_state' not in layout_state:
            QMessageBox.warning(
                self,
                'Load Failed',
                f'Failed to load layout "{layout_name}".',
                QMessageBox.StandardButton.Ok
            )
            return

        try:
            state = QByteArray.fromBase64(layout_state['window_state'].encode('utf-8'))
            self.restoreState(state)
            self.statusBar().showMessage(f'Layout "{layout_name}" loaded', 3000)
        except Exception as e:
            logger.error(f"Failed to restore layout: {e}")
            QMessageBox.warning(
                self,
                'Load Failed',
                f'Failed to load layout "{layout_name}": {str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def _show_settings_dialog(self) -> None:
        """Show the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    def _on_settings_changed(self) -> None:
        """Handle settings changes."""
        # Refresh UI components that depend on settings
        self.statusBar().showMessage('Settings updated', 3000)

        # Update the template menu
        self._update_template_menus()

    def _update_template_menus(self) -> None:
        """Update template menus with current templates."""
        # Refresh template manager
        self.template_manager = TemplateManager()

        # Find and update template menu
        template_menu = None
        for action in self.menuBar().actions():
            if action.text() == '&Templates':
                template_menu = action.menu()
                break

        if template_menu:
            template_menu.clear()

            # Add manage action
            manage_templates_action = QAction('&Manage Templates...', self)
            manage_templates_action.triggered.connect(self._show_template_manager)
            template_menu.addAction(manage_templates_action)

            template_menu.addSeparator()

            # Add template submenus
            template_names = self.template_manager.get_template_names()
            if template_names:
                for template_name in template_names:
                    template_submenu = QMenu(template_name, self)

                    export_csv_action = QAction('Export to CSV', self)
                    export_csv_action.triggered.connect(
                        lambda checked, t=template_name: self._export_to_template('csv', t)
                    )
                    template_submenu.addAction(export_csv_action)

                    try:
                        import openpyxl
                        EXCEL_AVAILABLE = True
                    except ImportError:
                        EXCEL_AVAILABLE = False

                    export_excel_action = QAction('Export to Excel', self)
                    export_excel_action.triggered.connect(
                        lambda checked, t=template_name: self._export_to_template('excel', t)
                    )
                    export_excel_action.setEnabled(EXCEL_AVAILABLE)
                    template_submenu.addAction(export_excel_action)

                    template_menu.addMenu(template_submenu)
            else:
                no_templates_action = QAction('No templates available', self)
                no_templates_action.setEnabled(False)
                template_menu.addAction(no_templates_action)

    def _show_about_dialog(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            self,
            'About InitialDB',
            f"InitialDB\n\nVersion {app_settings.get('app_version', '0.2.0')}\n\n" +
            'A tool for querying vehicle data with multi-selection support and template-based exports.'
        )

    def _show_export_menu(self) -> None:
        """Show the export menu."""
        # Get current result tab
        tab_info = self.right_panel.get_current_tab()
        if not tab_info:
            QMessageBox.information(
                self,
                'No Results',
                'No results tab is currently open.',
                QMessageBox.StandardButton.Ok
            )
            return

        tab_id, widget = tab_info
        if not hasattr(widget, '_export_data'):
            QMessageBox.information(
                self,
                'Not Exportable',
                'The current tab does not contain exportable data.',
                QMessageBox.StandardButton.Ok
            )
            return

        # Create export menu
        menu = QMenu(self)

        # Standard export options
        csv_action = QAction('Export to CSV...', self)
        csv_action.triggered.connect(lambda: widget._export_data('csv'))
        menu.addAction(csv_action)

        try:
            import openpyxl
            EXCEL_AVAILABLE = True
        except ImportError:
            EXCEL_AVAILABLE = False

        excel_action = QAction('Export to Excel...', self)
        excel_action.triggered.connect(lambda: widget._export_data('excel'))
        excel_action.setEnabled(EXCEL_AVAILABLE)
        menu.addAction(excel_action)

        menu.addSeparator()

        # Template export options
        template_names = self.template_manager.get_template_names()
        if template_names:
            for template_name in template_names:
                template_submenu = QMenu(template_name, self)

                csv_template_action = QAction('Export to CSV', self)
                csv_template_action.triggered.connect(
                    lambda checked, t=template_name: widget._export_to_template('csv', t)
                )
                template_submenu.addAction(csv_template_action)

                excel_template_action = QAction('Export to Excel', self)
                excel_template_action.triggered.connect(
                    lambda checked, t=template_name: widget._export_to_template('excel', t)
                )
                excel_template_action.setEnabled(EXCEL_AVAILABLE)
                template_submenu.addAction(excel_template_action)

                menu.addMenu(template_submenu)

        # Show the menu at cursor position
        menu.exec(QCursor.pos())

    def _export_data(self, format_type: str) -> None:
        """
        Export the current results data.

        Args:
            format_type: The export format ('csv' or 'excel')
        """
        # Get current result tab
        tab_info = self.right_panel.get_current_tab()
        if not tab_info:
            QMessageBox.information(
                self,
                'No Results',
                'No results tab is currently open.',
                QMessageBox.StandardButton.Ok
            )
            return

        tab_id, widget = tab_info
        if hasattr(widget, '_export_data'):
            widget._export_data(format_type)
        else:
            QMessageBox.information(
                self,
                'Not Exportable',
                'The current tab does not contain exportable data.',
                QMessageBox.StandardButton.Ok
            )

    def _export_to_template(self, format_type: str, template_name: str) -> None:
        """
        Export the current results data using a template.

        Args:
            format_type: The export format ('csv' or 'excel')
            template_name: The template name
        """
        # Get current result tab
        tab_info = self.right_panel.get_current_tab()
        if not tab_info:
            QMessageBox.information(
                self,
                'No Results',
                'No results tab is currently open.',
                QMessageBox.StandardButton.Ok
            )
            return

        tab_id, widget = tab_info
        if hasattr(widget, '_export_to_template'):
            widget._export_to_template(format_type, template_name)
        else:
            QMessageBox.information(
                self,
                'Not Exportable',
                'The current tab does not contain exportable data.',
                QMessageBox.StandardButton.Ok
            )

    def _new_query(self) -> None:
        """Create a new query, resetting all filters."""
        result = QMessageBox.question(
            self,
            'New Query',
            'This will clear all current queries and filters. Continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if result != QMessageBox.StandardButton.Yes:
            return

        # Reset the query panel
        query_panel = self.left_panel.get_query_panel()
        query_panel._reset_all_filters()

        # Create a new results tab
        self._create_results_tab("New Query")

        self.statusBar().showMessage('New query created', 3000)

    @asyncSlot()
    async def _save_current_query(self) -> None:
        """Save the current query."""
        # Show save query dialog
        # This is a placeholder for the actual SaveQueryDialog
        # We create a simple input dialog for now
        name, ok = QInputDialog.getText(self, "Save Query", "Query name:")
        if not ok or not name:
            return

        desc, ok = QInputDialog.getText(self, "Save Query", "Description (optional):")
        if not ok:
            return

        # Create a SavedQueryDTO with the entered values
        query_dto = SavedQueryDTO(
            id=str(uuid.uuid4()),
            name=name,
            description=desc,
            filters={},
            visible_columns=[],
            is_multi_query=True
        )

    def _create_results_tab(self, title: Optional[str] = None) -> tuple[str, "ResultsPanel"]:
        """
        Create a new results tab.

        Args:
            title: Optional tab title

        Returns:
            Tuple of (tab_id, results_panel)
        """
        return self.right_panel.create_results_tab(title)

    @asyncSlot()
    async def _execute_query(self) -> None:
        """Execute the current query."""
        # Get filter DTOs from query panel
        query_panel = self.left_panel.get_query_panel()
        filter_dtos = query_panel.get_all_filter_dtos()

        # Get visible columns from current results tab or create a new one
        tab_info = self.right_panel.get_current_tab()
        visible_columns = None
        results_panel = None

        if tab_info:
            tab_id, widget = tab_info
            if hasattr(widget, 'get_visible_columns'):
                visible_columns = widget.get_visible_columns()
                results_panel = widget

        if not results_panel:
            tab_id, results_panel = self._create_results_tab("Query Results")

        # Ensure vehicle_id is included
        if visible_columns:
            if not any((col[1] == 'vehicle_id' for col in visible_columns)):
                visible_columns.append(('vehicle', 'vehicle_id', 'vehicle_id'))

        # Update status
        self.statusBar().showMessage('Executing queries...')

        # Clear current results
        results_panel.clear_results()

        try:
            # Execute query
            results = await self._vehicle_service.get_vehicles_from_multiple_filters(
                filter_sets=filter_dtos,
                display_fields=visible_columns
            )

            # Show results
            self._on_query_results(results)

        except Exception as e:
            logger.error(f'Error executing query: {str(e)}')
            self.statusBar().showMessage(f'Query error: {str(e)}')
            QMessageBox.critical(
                self,
                'Query Error',
                f'Error executing query: {str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def _on_query_results(self, results: List[Dict[str, Any]]) -> None:
        """
        Handle query results.

        Args:
            results: The query results
        """
        # Get or create results tab
        tab_info = self.right_panel.get_current_tab()
        results_panel = None

        if tab_info:
            tab_id, widget = tab_info
            if hasattr(widget, 'set_results'):
                results_panel = widget

        if not results_panel:
            tab_id, results_panel = self._create_results_tab("Query Results")

        # Set results
        results_panel.set_results(results)

        # Update status
        self.statusBar().showMessage(f'Query completed: {len(results)} results')

    def _reset_filters(self) -> None:
        """Reset all filters in the query panel."""
        query_panel = self.left_panel.get_query_panel()
        query_panel._reset_all_filters()
        self.statusBar().showMessage('Filters reset', 3000)

    def _add_query_section(self) -> None:
        """Add a new query section to the query panel."""
        query_panel = self.left_panel.get_query_panel()
        query_panel.add_query_section()

    def _show_query_manager(self) -> None:
        """Show the query manager dialog."""
        # TODO: Implement query manager dialog
        QMessageBox.information(
            self,
            'Query Manager',
            'Query manager not implemented yet.',
            QMessageBox.StandardButton.Ok
        )

    def _show_column_selection(self) -> None:
        """Show the column selection dialog."""
        # Get current result tab
        tab_info = self.right_panel.get_current_tab()
        if not tab_info:
            QMessageBox.information(
                self,
                'No Results',
                'No results tab is currently open.',
                QMessageBox.StandardButton.Ok
            )
            return

        tab_id, widget = tab_info
        if hasattr(widget, 'show_column_selection_dialog'):
            widget.show_column_selection_dialog()
        else:
            QMessageBox.information(
                self,
                'Not Supported',
                'Column selection is not supported for the current tab.',
                QMessageBox.StandardButton.Ok
            )

    def _show_template_manager(self) -> None:
        """Show the template manager dialog."""
        from initialdb.ui.template_manager.template_manager_dialog import TemplateManagerDialog
        dialog = TemplateManagerDialog(self)
        dialog.exec()

        # Refresh template manager
        self.template_manager = TemplateManager()
        self._update_template_menus()

    @asyncSlot()
    async def _load_saved_queries(self) -> None:
        """Load saved queries for the menu."""
        try:
            saved_queries = await self._vehicle_service.get_saved_queries()
            self._update_saved_queries_menu(saved_queries)
        except Exception as e:
            logger.error(f'Error loading saved queries: {str(e)}')

    def _update_saved_queries_menu(self, queries: Dict[str, SavedQueryDTO]) -> None:
        """
        Update the saved queries menu.

        Args:
            queries: Dictionary of saved queries
        """
        self.saved_queries_menu.clear()

        if not queries:
            no_queries_action = QAction('No saved queries', self)
            no_queries_action.setEnabled(False)
            self.saved_queries_menu.addAction(no_queries_action)
            return

        for name, query in queries.items():
            query_action = QAction(name, self)
            if query.description:
                query_action.setToolTip(query.description)

            query_action.triggered.connect(
                lambda checked=False, name=name: self._on_load_query_requested(name)
            )
            self.saved_queries_menu.addAction(query_action)

    @asyncSlot()
    async def _on_load_query_requested(self, query_name: str) -> None:
        """
        Handle load query request.

        Args:
            query_name: The name of the query to load
        """
        try:
            self.statusBar().showMessage(f'Loading query: {query_name}...')
            QApplication.processEvents()

            query_dto = await self._vehicle_service.load_query(query_name)
            if not query_dto:
                self.statusBar().showMessage('Failed to load query')
                QMessageBox.warning(
                    self,
                    'Load Query',
                    f'Failed to load query "{query_name}"',
                    QMessageBox.StandardButton.Ok
                )
                return

            self._on_query_loaded(query_dto)

        except Exception as e:
            logger.error(f"Error loading query '{query_name}': {str(e)}")
            self.statusBar().showMessage('Error loading query')
            QMessageBox.critical(
                self,
                'Load Error',
                f'Error loading query: {str(e)}',
                QMessageBox.StandardButton.Ok
            )

    def _on_query_loaded(self, query_dto: SavedQueryDTO) -> None:
        """
        Handle loaded query.

        Args:
            query_dto: The loaded query DTO
        """
        # Create new query
        self._new_query()

        # Set visible columns if available
        if query_dto.visible_columns:
            # Get or create results tab
            tab_info = self.right_panel.get_current_tab()
            results_panel = None

            if tab_info:
                tab_id, widget = tab_info
                if hasattr(widget, 'set_visible_columns'):
                    results_panel = widget

            if not results_panel:
                tab_id, results_panel = self._create_results_tab(query_dto.name)

            results_panel.set_visible_columns(query_dto.visible_columns)

        # Set filters
        query_panel = self.left_panel.get_query_panel()

        if query_dto.is_multi_query and isinstance(query_dto.filters, dict):
            query_panel.set_all_filter_dtos(query_dto.filters)
        else:
            # Single query case
            sections = list(query_panel.query_sections.keys())
            if sections:
                first_section = sections[0]
                filter_dto = query_dto.filters
                if not isinstance(filter_dto, FilterDTO):
                    filter_dto = FilterDTO(**filter_dto)

                query_panel.query_sections[first_section].set_filter_dto(filter_dto)

        self.statusBar().showMessage(f'Query loaded: {query_dto.name}', 3000)

    def _on_tab_added(self, tab_id: str, title: str) -> None:
        """
        Handle tab added event.

        Args:
            tab_id: The tab ID
            title: The tab title
        """
        self.statusBar().showMessage(f'Tab added: {title}', 3000)

    def _on_tab_closed(self, tab_id: str) -> None:
        """
        Handle tab closed event.

        Args:
            tab_id: The tab ID
        """
        self.statusBar().showMessage('Tab closed', 3000)

    def _on_tab_selected(self, tab_id: str) -> None:
        """
        Handle tab selected event.

        Args:
            tab_id: The tab ID
        """
        pass  # No action needed

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close event.

        Args:
            event: The close event
        """
        # Save window state
        self._save_window_state()

        # Clean up update manager
        if hasattr(self, 'update_manager'):
            self.update_manager.cleanup()

        # Clean up vehicle service
        try:
            self._vehicle_service.dispose()
        except Exception as e:
            logger.error(f'Error disposing vehicle service: {str(e)}')

        # Accept the close event
        event.accept()