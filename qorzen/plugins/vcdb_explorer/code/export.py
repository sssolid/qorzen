#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VCdb Explorer export module.

This module provides functionality for exporting query results to various formats.
"""

from __future__ import annotations

import csv
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, cast
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class ExportError(Exception):
    """Exception raised for export-related errors."""
    pass


class DataExporter:
    """Handles exporting of data to various formats."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the data exporter.

        Args:
            logger: Logger instance
        """
        self._logger = logger

    def export_csv(
            self,
            data: List[Dict[str, Any]],
            columns: List[str],
            column_map: Dict[str, str],
            file_path: str
    ) -> None:
        """Export data to a CSV file.

        Args:
            data: List of data dictionaries
            columns: List of column IDs to export
            column_map: Dictionary mapping column IDs to display names
            file_path: Path to the output file

        Raises:
            ExportError: If export fails
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                # Create CSV writer
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=columns,
                    extrasaction='ignore'
                )

                # Write header with display names
                writer.writerow({col: column_map.get(col, col) for col in columns})

                # Write data rows
                for row in data:
                    # Convert all values to strings
                    clean_row = {}
                    for col in columns:
                        value = row.get(col, "")
                        clean_row[col] = str(value) if value is not None else ""

                    writer.writerow(clean_row)

            self._logger.info(f"Exported {len(data)} rows to CSV: {file_path}")

        except Exception as e:
            self._logger.error(f"Failed to export CSV: {str(e)}")
            raise ExportError(f"Failed to export CSV: {str(e)}") from e

    def export_excel(
            self,
            data: List[Dict[str, Any]],
            columns: List[str],
            column_map: Dict[str, str],
            file_path: str,
            sheet_name: Optional[str] = None
    ) -> None:
        """Export data to an Excel file.

        Args:
            data: List of data dictionaries
            columns: List of column IDs to export
            column_map: Dictionary mapping column IDs to display names
            file_path: Path to the output file
            sheet_name: Optional name for the worksheet

        Raises:
            ExportError: If export fails or openpyxl is not available
        """
        if not EXCEL_AVAILABLE:
            raise ExportError("Excel export is not available. Please install openpyxl.")

        try:
            # Create workbook and sheet
            wb = openpyxl.Workbook()
            ws = wb.active

            # Set sheet name
            if not sheet_name:
                sheet_name = "VCdb Results"
            ws.title = sheet_name

            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.cell(row=1, column=1, value=f"Generated: {timestamp}")
            ws.cell(row=1, column=1).font = Font(italic=True)

            # Create header style
            header_font = Font(bold=True)
            header_fill = PatternFill(
                start_color="DDDDDD",
                end_color="DDDDDD",
                fill_type="solid"
            )
            header_alignment = Alignment(horizontal="center")

            # Add header row (row 2)
            for col_idx, col_id in enumerate(columns, 1):
                cell = ws.cell(row=2, column=col_idx, value=column_map.get(col_id, col_id))
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment

            # Add data rows
            for row_idx, row_data in enumerate(data, 3):  # Start at row 3
                for col_idx, col_id in enumerate(columns, 1):
                    value = row_data.get(col_id, "")
                    ws.cell(row=row_idx, column=col_idx, value=value)

            # Auto-size columns
            for col_idx, _ in enumerate(columns, 1):
                col_letter = openpyxl.utils.get_column_letter(col_idx)
                max_length = 0

                # Find the maximum content length in this column
                for row_idx in range(2, len(data) + 3):  # Skip timestamp row
                    cell = ws.cell(row=row_idx, column=col_idx)
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))

                # Set width with some padding
                adjusted_width = max(max_length + 2, 10)  # Min width 10
                ws.column_dimensions[col_letter].width = min(adjusted_width, 50)  # Max width 50

            # Freeze header row
            ws.freeze_panes = "A3"

            # Save the workbook
            wb.save(file_path)

            self._logger.info(f"Exported {len(data)} rows to Excel: {file_path}")

        except Exception as e:
            self._logger.error(f"Failed to export Excel: {str(e)}")
            raise ExportError(f"Failed to export Excel: {str(e)}") from e

    def export_all_data(
            self,
            database_callback: callable,
            filter_panels: List[Dict[str, List[int]]],
            columns: List[str],
            column_map: Dict[str, str],
            file_path: str,
            format_type: str,
            max_rows: int = 10000,
            table_filters: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            sort_desc: bool = False,
            progress_callback: Optional[callable] = None
    ) -> int:
        """Export all query results, potentially fetching data in batches.

        This is used for exporting large result sets that might not fit in memory.

        Args:
            database_callback: Function that returns (results, total_count)
            filter_panels: List of filter dictionaries
            columns: List of column IDs to export
            column_map: Dictionary mapping column IDs to display names
            file_path: Path to the output file
            format_type: Export format ('csv' or 'excel')
            max_rows: Maximum number of rows to export
            table_filters: Additional filters to apply to the result table
            sort_by: Column to sort by
            sort_desc: Whether to sort in descending order
            progress_callback: Optional callback for progress updates

        Returns:
            Number of rows exported

        Raises:
            ExportError: If export fails
        """
        try:
            # Get total count first
            _, total_count = database_callback(
                filter_panels=filter_panels,
                columns=columns,
                page=1,
                page_size=1,  # Just need the count
                sort_by=sort_by,
                sort_desc=sort_desc,
                table_filters=table_filters
            )

            # Limit to max_rows
            total_to_export = min(total_count, max_rows)

            if total_to_export == 0:
                self._logger.warning("No data to export")
                return 0

            # For CSV, we'll append to the file
            if format_type == 'csv':
                with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                    # Create CSV writer
                    writer = csv.DictWriter(
                        csv_file,
                        fieldnames=columns,
                        extrasaction='ignore'
                    )

                    # Write header with display names
                    writer.writerow({col: column_map.get(col, col) for col in columns})

                    # Fetch and write data in batches
                    batch_size = 1000
                    rows_exported = 0

                    for page in range(1, (total_to_export + batch_size - 1) // batch_size + 1):
                        # Fetch batch
                        results, _ = database_callback(
                            filter_panels=filter_panels,
                            columns=columns,
                            page=page,
                            page_size=batch_size,
                            sort_by=sort_by,
                            sort_desc=sort_desc,
                            table_filters=table_filters
                        )

                        # Write batch
                        for row in results:
                            # Convert all values to strings
                            clean_row = {}
                            for col in columns:
                                value = row.get(col, "")
                                clean_row[col] = str(value) if value is not None else ""

                            writer.writerow(clean_row)
                            rows_exported += 1

                            # Update progress
                            if progress_callback:
                                progress_callback(rows_exported, total_to_export)

                            # Check if we've hit the limit
                            if rows_exported >= total_to_export:
                                break

                self._logger.info(f"Exported {rows_exported} rows to CSV: {file_path}")
                return rows_exported

            # For Excel, we need to keep the workbook in memory
            elif format_type == 'excel' and EXCEL_AVAILABLE:
                # Create workbook and sheet
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "VCdb Results"

                # Add timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ws.cell(row=1, column=1, value=f"Generated: {timestamp}")
                ws.cell(row=1, column=1).font = Font(italic=True)

                # Create header style
                header_font = Font(bold=True)
                header_fill = PatternFill(
                    start_color="DDDDDD",
                    end_color="DDDDDD",
                    fill_type="solid"
                )
                header_alignment = Alignment(horizontal="center")

                # Add header row (row 2)
                for col_idx, col_id in enumerate(columns, 1):
                    cell = ws.cell(row=2, column=col_idx, value=column_map.get(col_id, col_id))
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment

                # Fetch and write data in batches
                batch_size = 1000
                rows_exported = 0
                excel_row = 3  # Start at row 3

                for page in range(1, (total_to_export + batch_size - 1) // batch_size + 1):
                    # Fetch batch
                    results, _ = database_callback(
                        filter_panels=filter_panels,
                        columns=columns,
                        page=page,
                        page_size=batch_size,
                        sort_by=sort_by,
                        sort_desc=sort_desc,
                        table_filters=table_filters
                    )

                    # Write batch
                    for row_data in results:
                        for col_idx, col_id in enumerate(columns, 1):
                            value = row_data.get(col_id, "")
                            ws.cell(row=excel_row, column=col_idx, value=value)

                        excel_row += 1
                        rows_exported += 1

                        # Update progress
                        if progress_callback:
                            progress_callback(rows_exported, total_to_export)

                        # Check if we've hit the limit
                        if rows_exported >= total_to_export:
                            break

                # Auto-size columns (just check the first 100 rows for performance)
                for col_idx, _ in enumerate(columns, 1):
                    col_letter = openpyxl.utils.get_column_letter(col_idx)
                    max_length = 0

                    # Find the maximum content length in this column
                    for row_idx in range(2, min(excel_row, 102)):  # Skip timestamp row, check max 100 rows
                        cell = ws.cell(row=row_idx, column=col_idx)
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))

                    # Set width with some padding
                    adjusted_width = max(max_length + 2, 10)  # Min width 10
                    ws.column_dimensions[col_letter].width = min(adjusted_width, 50)  # Max width 50

                # Freeze header row
                ws.freeze_panes = "A3"

                # Save the workbook
                wb.save(file_path)

                self._logger.info(f"Exported {rows_exported} rows to Excel: {file_path}")
                return rows_exported

            else:
                raise ExportError(f"Unsupported export format: {format_type}")

        except Exception as e:
            self._logger.error(f"Failed to export data: {str(e)}")
            raise ExportError(f"Failed to export data: {str(e)}") from e