from __future__ import annotations

"""
Query loader utility for the InitialDB application.

This module provides robust utilities for loading saved queries and properly
converting between IDs and display values to ensure correct presentation.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
import structlog

from ..models.schema import FilterDTO, SavedQueryDTO
from .dependency_container import resolve
from .schema_registry import SchemaRegistry

logger = structlog.get_logger(__name__)


class QueryLoadingError(Exception):
    """Exception raised for errors during query loading."""
    pass


class FilterValueResolver:
    """Utility to resolve filter values between IDs and display values."""

    @staticmethod
    def get_display_value(table: str, column: str, value_id: Any) -> str:
        """Get the display value for a given ID.

        Args:
            table: The database table name
            column: The column name
            value_id: The ID value to resolve

        Returns:
            The corresponding display value
        """
        registry = resolve(SchemaRegistry)

        try:
            # Get the appropriate display column
            value_column = registry.get_filter_value_column(table, column)
            if not value_column:
                # If no mapping exists, just return the ID as a string
                return str(value_id)

            # Look up the display value if possible
            # In a real implementation, this might query the database
            # For now, we'll just return the ID as a string
            return str(value_id)
        except Exception as e:
            logger.error(f"Error resolving display value for {table}.{column}.{value_id}: {e}")
            return str(value_id)

    @staticmethod
    def get_id_value(table: str, column: str, display_value: str) -> Any:
        """Get the ID value for a given display value.

        Args:
            table: The database table name
            column: The column name
            display_value: The display value to resolve

        Returns:
            The corresponding ID value
        """
        try:
            # In a real implementation, this might query the database
            # For now, we'll just try to convert to int or return as is
            try:
                return int(display_value)
            except (ValueError, TypeError):
                return display_value
        except Exception as e:
            logger.error(f"Error resolving ID value for {table}.{column}.{display_value}: {e}")
            return display_value


class QueryLoader:
    """Utility for loading and saving queries with proper value resolution."""

    @staticmethod
    async def load_query(query_path: Union[str, Path]) -> Optional[SavedQueryDTO]:
        """Load a query from a file with proper value resolution.

        Args:
            query_path: Path to the query file

        Returns:
            The loaded SavedQueryDTO or None if loading fails

        Raises:
            QueryLoadingError: If the query file cannot be loaded or parsed
        """
        try:
            query_path = Path(query_path) if isinstance(query_path, str) else query_path

            if not query_path.exists():
                logger.warning(f"Query file does not exist: {query_path}")
                return None

            with open(query_path, 'r', encoding='utf-8') as f:
                query_dict = json.load(f)

            # Convert filters if needed
            if 'filters' in query_dict:
                filters_data = query_dict['filters']

                # Handle both dict-based filters and FilterDTO-based filters
                if isinstance(filters_data, dict):
                    # If it's a multi-query with multiple filter sets
                    if query_dict.get('is_multi_query', False):
                        processed_filters = {}
                        for section_id, section_filters in filters_data.items():
                            if isinstance(section_filters, dict):
                                # Convert display values to IDs as needed
                                processed_section = await QueryLoader._process_filter_values(section_filters)
                                processed_filters[section_id] = processed_section
                            else:
                                processed_filters[section_id] = section_filters
                        query_dict['filters'] = processed_filters
                    else:
                        # Single filter set
                        query_dict['filters'] = await QueryLoader._process_filter_values(filters_data)

            # Create and return the DTO
            return SavedQueryDTO(**query_dict)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse query file {query_path}: {str(e)}"
            logger.error(error_msg)
            raise QueryLoadingError(error_msg) from e
        except Exception as e:
            error_msg = f"Error loading query from {query_path}: {str(e)}"
            logger.error(error_msg)
            raise QueryLoadingError(error_msg) from e

    @staticmethod
    async def _process_filter_values(filter_data: Dict[str, Any]) -> FilterDTO:
        """Process filter values to ensure proper ID values.

        Args:
            filter_data: The raw filter data

        Returns:
            A properly processed FilterDTO
        """
        # Create a fresh FilterDTO
        filter_dto = FilterDTO()

        # For each field that could have display values that need to be converted to IDs
        for field_name, values in filter_data.items():
            # Skip fields that don't need conversion
            if field_name in ('active_filters', 'use_year_range', 'year_range_start', 'year_range_end'):
                setattr(filter_dto, field_name, values)
                continue

            # Handle list fields (multiple selections)
            if field_name.endswith('_ids') and isinstance(values, list):
                # This field already contains IDs, we can set it directly
                setattr(filter_dto, field_name, values)
                continue

            # For other fields, we need to check if they need conversion
            if values is not None:
                if isinstance(values, list):
                    # Set the list values directly
                    setattr(filter_dto, field_name, values)
                else:
                    # Single value, set it normally
                    setattr(filter_dto, field_name, values)

        # Ensure all relations are properly set
        filter_dto = await QueryLoader._validate_filter_dto(filter_dto)

        return filter_dto

    @staticmethod
    async def _validate_filter_dto(filter_dto: FilterDTO) -> FilterDTO:
        """Validate and ensure consistency in a FilterDTO.

        Args:
            filter_dto: The FilterDTO to validate

        Returns:
            The validated FilterDTO
        """
        # Ensure year filter is consistent
        if filter_dto.use_year_range:
            # If using year range, clear year_ids
            filter_dto.year_ids = []
        elif filter_dto.year_ids:
            # If using year_ids, ensure range is cleared
            filter_dto.year_range_start = None
            filter_dto.year_range_end = None

        # Run any validation defined in the model
        # if hasattr(filter_dto, 'model_validate'):
        #     filter_dto = filter_dto.model_validate()

        return filter_dto

    @staticmethod
    async def save_query(
            query: SavedQueryDTO,
            query_dir: Union[str, Path],
            overwrite: bool = True
    ) -> bool:
        """Save a query to a file.

        Args:
            query: The query to save
            query_dir: Directory where queries are stored
            overwrite: Whether to overwrite existing queries

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            query_dir = Path(query_dir) if isinstance(query_dir, str) else query_dir

            # Create directory if it doesn't exist
            os.makedirs(query_dir, exist_ok=True)

            # Generate the query path
            query_path = query_dir / f"{query.name}.json"

            # Check if file exists and we're not supposed to overwrite
            if query_path.exists() and not overwrite:
                logger.warning(f"Query file exists and overwrite=False: {query_path}")
                return False

            # Convert to dictionary for serialization
            if hasattr(query, 'model_dump'):
                query_dict = query.model_dump()
            else:
                query_dict = query.dict()

            # Write to file
            with open(query_path, 'w', encoding='utf-8') as f:
                json.dump(query_dict, f, indent=2, default=str)

            logger.info(f"Saved query to {query_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving query {query.name}: {str(e)}")
            return False


class BatchQueryLoader:
    """Utility for loading multiple queries at once."""

    @staticmethod
    async def load_all_queries(query_dir: Union[str, Path]) -> Dict[str, SavedQueryDTO]:
        """Load all queries from a directory.

        Args:
            query_dir: Directory where queries are stored

        Returns:
            Dictionary mapping query names to SavedQueryDTO objects
        """
        query_dir = Path(query_dir) if isinstance(query_dir, str) else query_dir

        if not query_dir.exists() or not query_dir.is_dir():
            logger.warning(f"Query directory does not exist: {query_dir}")
            return {}

        result = {}
        tasks = []

        # Collect paths to all JSON files
        for query_file in query_dir.glob("*.json"):
            tasks.append(QueryLoader.load_query(query_file))

        # Wait for all queries to load
        if not tasks:
            return {}

        # Load queries concurrently
        query_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, query_result in enumerate(query_results):
            if isinstance(query_result, Exception):
                logger.error(f"Error loading query {i}: {str(query_result)}")
                continue

            if query_result is not None:
                result[query_result.name] = query_result

        return result


# Create convenience functions for use elsewhere
async def load_query(query_path: Union[str, Path]) -> Optional[SavedQueryDTO]:
    """Load a query from a file.

    Args:
        query_path: Path to the query file

    Returns:
        The loaded SavedQueryDTO or None if loading fails
    """
    return await QueryLoader.load_query(query_path)


async def load_all_queries(query_dir: Union[str, Path]) -> Dict[str, SavedQueryDTO]:
    """Load all queries from a directory.

    Args:
        query_dir: Directory where queries are stored

    Returns:
        Dictionary mapping query names to SavedQueryDTO objects
    """
    return await BatchQueryLoader.load_all_queries(query_dir)


async def save_query(query: SavedQueryDTO, query_dir: Union[str, Path], overwrite: bool = True) -> bool:
    """Save a query to a file.

    Args:
        query: The query to save
        query_dir: Directory where queries are stored
        overwrite: Whether to overwrite existing queries

    Returns:
        True if saved successfully, False otherwise
    """
    return await QueryLoader.save_query(query, query_dir, overwrite)