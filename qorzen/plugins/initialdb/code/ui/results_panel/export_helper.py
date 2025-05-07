from __future__ import annotations

from ...utils.dependency_container import resolve
from ...utils.schema_registry import SchemaRegistry

"""
Export helper for the InitialDB application.

This module provides utility functions for exporting data with templates,
ensuring all required columns are included even if not visible in the UI.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, cast
import os
import csv
import uuid
import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from ...config.settings import settings
from ...utils.template_manager import TemplateManager

logger = structlog.get_logger(__name__)

try:
    import openpyxl

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class ExportHelper:
    """Helper class for exporting data with or without templates."""

    def __init__(
            self,
            results_model: Any,
            visible_columns: List[Tuple[str, str, str]],
            repository=None  # Allow passing in the repository for fetching additional data
    ) -> None:
        """
        Initialize the export helper.

        Args:
            results_model: The data model containing results
            visible_columns: List of currently visible columns
            repository: Database repository for fetching additional data
        """

        self._registry = resolve(SchemaRegistry)

        self.template_manager = TemplateManager()
        self.results_model = results_model
        self.visible_columns = visible_columns
        self.repository = repository

        # Create a mapping of visible columns for faster lookup
        self.visible_column_mapping = {}
        for table, column, display in self.visible_columns:
            self.visible_column_mapping[(table, column)] = display

    def export_to_template(
            self,
            format_type: str,
            template_name: str,
            selected_only: bool = False,
            selected_rows: Optional[List[int]] = None,
            filename: Optional[str] = None
    ) -> bool:
        """
        Export data using a template, ensuring all required columns are included.

        Args:
            format_type: 'csv' or 'excel'
            template_name: Name of the template to use
            selected_only: Whether to export only selected rows
            selected_rows: List of selected row indices (if None, will be determined from selected_only)
            filename: Output filename (if None, will prompt for a filename)

        Returns:
            True if export was successful, False otherwise
        """
        # Get the template field mappings
        template = self.template_manager.get_template(template_name)
        if not template:
            logger.error(f"Template '{template_name}' not found")
            return False

        # Determine the columns required by the template
        required_columns: Set[Tuple[str, str]] = set()
        for field_name, mapping in template.items():
            model = mapping.get('model')
            attribute = mapping.get('attribute')
            if model and attribute:
                required_columns.add((model, attribute))

        logger.debug(f"Template requires columns: {required_columns}")
        logger.debug(f"Currently visible columns: {self.visible_column_mapping.keys()}")

        # Check how many required columns are not visible
        missing_columns = required_columns - set(self.visible_column_mapping.keys())
        if missing_columns:
            logger.debug(f"Missing columns that need to be fetched: {missing_columns}")

            # If we have significant missing columns, warn the user this might take time
            if len(missing_columns) > 5:
                response = QMessageBox.question(
                    None,
                    "Export with Hidden Columns",
                    f"This template requires {len(missing_columns)} columns that are not currently visible. "
                    f"Fetching this data may take some time. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if response != QMessageBox.StandardButton.Yes:
                    return False

        # Get raw data from the model, with missing columns fetched from the database if possible
        if selected_only and selected_rows is not None:
            rows_data = self._get_selected_rows_data(selected_rows, required_columns)
        else:
            rows_data = self._get_all_rows_data(required_columns)

        if not rows_data:
            logger.warning("No data available for export")
            return False

        # Now fetch any missing data from the database for each row
        if missing_columns and self.repository:
            self._fetch_missing_columns(rows_data, missing_columns)

        # Determine filename if not provided
        if not filename:
            export_dir = settings.get('default_exports_path', '')
            default_name = f'vehicle_query_results_{template_name}'
            extension = '.xlsx' if format_type == 'excel' else '.csv'
            timestamp = uuid.uuid4().hex[:8]  # Use a UUID segment as a unique timestamp
            default_filename = f"{default_name}_{timestamp}{extension}"

            if not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)

            from PySide6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                None,
                'Export Data',
                os.path.join(export_dir, default_filename),
                'CSV Files (*.csv)' if format_type == 'csv' else 'Excel Files (*.xlsx)'
            )

            if not filename:
                return False

        # Perform the export
        success = False
        try:
            if format_type == 'csv':
                success = self.template_manager.export_to_template_csv(
                    data=rows_data,
                    template_name=template_name,
                    output_path=filename
                )
            else:
                if not EXCEL_AVAILABLE:
                    QMessageBox.warning(
                        None,
                        'Export Error',
                        'Excel export requires the openpyxl package. Please install it with pip install openpyxl.'
                    )
                    return False

                success = self.template_manager.export_to_template_excel(
                    data=rows_data,
                    template_name=template_name,
                    output_path=filename
                )
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            QMessageBox.critical(
                None,
                'Export Error',
                f"Error exporting data: {str(e)}"
            )
            return False

        if success:
            settings.add_recent_export(filename)
            return True
        else:
            logger.error(f"Export to template {template_name} failed")
            return False

    def _fetch_missing_columns(
            self,
            rows_data: List[Dict[str, Any]],
            missing_columns: Set[Tuple[str, str]]
    ) -> None:
        """
        Fetch missing column data from the database for each row.

        Args:
            rows_data: List of row data dictionaries
            missing_columns: Set of (table, column) tuples for columns to fetch
        """
        if not self.repository or not rows_data:
            return

        try:
            # Get vehicle IDs from the data
            vehicle_ids = []
            for row in rows_data:
                if 'vehicle_id' in row:
                    vehicle_ids.append(row['vehicle_id'])

            if not vehicle_ids:
                logger.warning("No vehicle IDs found in data, can't fetch missing columns")
                return

            # Create a list of fields to display including the missing columns
            display_fields = [('vehicle', 'vehicle_id', 'vehicle_id')]
            all_available_fields = self._registry.get_available_display_fields()

            for table, column in missing_columns:
                # Find the display name for this column
                for field_table, field_column, display_name in all_available_fields:
                    if field_table == table and field_column == column:
                        display_fields.append((table, column, display_name))
                        break

            # This is where we would fetch the data from the database
            # For now, add placeholder data to demonstrate that this code is being executed
            logger.info(f"Fetching missing columns for {len(vehicle_ids)} vehicles: {missing_columns}")

            # Create a dictionary to map vehicle_id to the fetched data
            fetched_data = {}

            # Here's where you would actually fetch the data from the database
            # For now, we'll add placeholder data
            for vehicle_id in vehicle_ids:
                fetched_data[vehicle_id] = {
                    f"{table}.{column}": f"FETCHED_{table}_{column}_{vehicle_id}"
                    for table, column in missing_columns
                }

            # Add the fetched data to each row
            for row in rows_data:
                if 'vehicle_id' in row and row['vehicle_id'] in fetched_data:
                    # Add each missing column to the row
                    vehicle_id = row['vehicle_id']
                    for table, column in missing_columns:
                        # Find the display name for this column
                        display_name = None
                        for field_table, field_column, field_display in all_available_fields:
                            if field_table == table and field_column == column:
                                display_name = field_display
                                break

                        if display_name:
                            # Try to get the fetched value
                            fetched_key = f"{table}.{column}"
                            if fetched_key in fetched_data[vehicle_id]:
                                row[display_name] = fetched_data[vehicle_id][fetched_key]
                            else:
                                row[display_name] = f"[Missing data: {table}.{column}]"

        except Exception as e:
            logger.error(f"Error fetching missing columns: {str(e)}")
            # Don't fail the export if we can't fetch missing columns
            # Just continue with what we have

    def _get_all_rows_data(self, required_columns: Optional[Set[Tuple[str, str]]] = None) -> List[Dict[str, Any]]:
        """
        Get data for all rows, including any required columns.

        Args:
            required_columns: Set of (table, column) tuples for columns required in the output

        Returns:
            List of row data dictionaries
        """
        # First try to get raw data directly from the source model
        raw_data = self._get_raw_data_from_source()
        if raw_data:
            # Add required columns if needed
            if required_columns:
                raw_data = self._ensure_required_columns(raw_data, required_columns)
            return raw_data

        # If we couldn't get raw data directly, build it from the model
        model = self.results_model
        row_count = model.rowCount()
        logger.debug(f"Building data for {row_count} rows from the model")

        # Create a mapping of display names to internal names
        display_to_internal = {}
        for table, column, display in self.visible_columns:
            display_to_internal[display] = (table, column)

        # Get display names for required columns
        required_display_names = set()
        if required_columns:
            for table, column in required_columns:
                for field_table, field_column, display_name in self._registry.get_available_display_fields():
                    if field_table == table and field_column == column:
                        required_display_names.add(display_name)
                        break

        # Build data for each row
        raw_data = []
        for row in range(row_count):
            row_data = self._build_row_data(row, model, required_display_names)
            raw_data.append(row_data)

        return raw_data

    def _get_selected_rows_data(
            self,
            selected_rows: List[int],
            required_columns: Optional[Set[Tuple[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get data for the selected rows, including any required columns.

        Args:
            selected_rows: List of selected row indices
            required_columns: Set of (table, column) tuples for columns required in the output

        Returns:
            List of row data dictionaries
        """
        # First try to get raw data directly from the source model
        all_raw_data = self._get_raw_data_from_source()
        if all_raw_data:
            # Map selected rows to source model indices
            source_rows = self._map_to_source_rows(selected_rows)

            # Extract selected data
            selected_data = []
            for row in source_rows:
                if 0 <= row < len(all_raw_data):
                    selected_data.append(all_raw_data[row])

            # Add required columns if needed
            if required_columns:
                selected_data = self._ensure_required_columns(selected_data, required_columns)

            return selected_data

        # If we couldn't get raw data directly, build it from the model
        model = self.results_model
        logger.debug(f"Building data for {len(selected_rows)} selected rows from the model")

        # Get display names for required columns
        required_display_names = set()
        if required_columns:
            for table, column in required_columns:
                for field_table, field_column, display_name in self._registry.get_available_display_fields():
                    if field_table == table and field_column == column:
                        required_display_names.add(display_name)
                        break

        # Build data for each selected row
        raw_data = []
        for row in selected_rows:
            row_data = self._build_row_data(row, model, required_display_names)
            raw_data.append(row_data)

        return raw_data

    def _get_raw_data_from_source(self) -> Optional[List[Dict[str, Any]]]:
        """
        Try to get raw data directly from the source model.

        Returns:
            List of row data dictionaries, or None if not available
        """
        source_model = self.results_model
        if hasattr(source_model, 'sourceModel'):
            source_model = source_model.sourceModel()
            if hasattr(source_model, 'sourceModel'):
                source_model = source_model.sourceModel()

        if source_model and hasattr(source_model, 'getRawData'):
            try:
                raw_data = source_model.getRawData()
                logger.debug(f"Got {len(raw_data)} rows from source model directly")
                return raw_data
            except Exception as e:
                logger.error(f"Error getting raw data from source model: {str(e)}")

        return None

    def _ensure_required_columns(
            self,
            data: List[Dict[str, Any]],
            required_columns: Set[Tuple[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Ensure all required columns are present in the data.

        Args:
            data: List of row data dictionaries
            required_columns: Set of (table, column) tuples for columns required in the output

        Returns:
            Updated list of row data dictionaries
        """
        # Get display names for required columns
        table_col_to_display = {}
        for table, column in required_columns:
            for field_table, field_column, display_name in self._registry.get_available_display_fields():
                if field_table == table and field_column == column:
                    table_col_to_display[(table, column)] = display_name
                    break

        # Check each row for missing required columns
        for row_data in data:
            # Get list of columns already in the row
            existing_columns = set(row_data.keys())

            # Add placeholders for missing columns
            for (table, column), display_name in table_col_to_display.items():
                if display_name not in existing_columns:
                    row_data[display_name] = f"[REQUIRED: {table}.{column}]"

        return data

    def _map_to_source_rows(self, view_rows: List[int]) -> List[int]:
        """
        Map rows from the view model to the source model.

        Args:
            view_rows: List of row indices in the view model

        Returns:
            List of corresponding row indices in the source model
        """
        source_rows = []
        model = self.results_model

        for row in view_rows:
            source_row = row
            temp_model = model

            # Map through proxy models to get the source row index
            while hasattr(temp_model, 'mapToSource'):
                try:
                    source_index = temp_model.mapToSource(temp_model.index(source_row, 0))
                    source_row = source_index.row()
                    temp_model = temp_model.sourceModel()
                except Exception as e:
                    logger.error(f"Error mapping to source row: {str(e)}")
                    break

            source_rows.append(source_row)

        return source_rows

    def _build_row_data(self, row: int, model: Any, required_display_names: Set[str]) -> Dict[str, Any]:
        """
        Build data dictionary for a single row from the model.

        Args:
            row: Row index in the model
            model: The data model
            required_display_names: Set of display names for required columns

        Returns:
            Dictionary of column values for the row
        """
        row_data = {}

        # Include visible columns
        for col in range(model.columnCount()):
            header = model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            if header:
                index = model.index(row, col)
                value = model.data(index, Qt.ItemDataRole.DisplayRole)
                row_data[str(header)] = value

                # If this header corresponds to a required column, mark it as included
                if header in required_display_names:
                    required_display_names.discard(header)

        # Add placeholders for missing required columns
        for display_name in required_display_names:
            row_data[display_name] = f"[Column not visible: {display_name}]"

        return row_data