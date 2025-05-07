from __future__ import annotations

"""
Schema registry for the InitialDB application.

This module provides a centralized registry of database schema information,
including tables, columns, relationships, and display names.
It serves as a single source of truth for schema-related information
throughout the application.
"""

import functools
import re
from functools import cache
from typing import Any, Dict, List, Optional, Set, Tuple, Type, cast

import structlog
from sqlalchemy.inspection import inspect

from ..models.base_class import Base

logger = structlog.get_logger(__name__)

# Constants
EXCLUDED_TABLES = {
    "change_attribute_states",
    "change_details",
    "change_reasons",
    "change_table_names",
    "changes",
    "version",
    "vcdb_changes",
    "attachment",
    "attachment_type",
    "english_phrase",
    "language",
    "language_translation",
    "language_translation_attachment",
}

# Set of allowed filters as (table_name, column_name) tuples
ALLOWED_FILTERS: set[tuple[str, str]] = {
    ("year", "year_id"),
    ("make", "make_id"),
    ("model", "model_id"),
    ("sub_model", "sub_model_id"),
    ("region", "region_id"),
    ("vehicle_type", "vehicle_type_id"),
    ("vehicle_type_group", "vehicle_type_group_id"),
    ("publication_stage", "publication_stage_id"),
    ("engine_block", "engine_block_id"),
    ("engine_block", "liter"),
    ("engine_block", "cc"),
    ("engine_block", "cid"),
    ("engine_block", "cylinders"),
    ("engine_block", "block_type"),
    ("aspiration", "aspiration_id"),
    ("fuel_type", "fuel_type_id"),
    # ... (other allowed filters)
}


class SchemaRegistry:
    """
    Central registry for database schema information.

    This class provides access to schema metadata including tables, columns,
    relationships, and display names. It serves as a single source of truth
    for schema-related information throughout the application.
    """

    def __init__(self) -> None:
        """Initialize the schema registry."""
        logger.info("Initializing schema registry")

        self._models_by_tablename: Dict[str, Type[Base]] = {}
        self._display_names: Dict[Tuple[str, str], str] = {}
        self._filter_value_column_map: Dict[Tuple[str, str], str] = {}
        self._relationship_mapping: Dict[str, List[str]] = {}
        self._model_primary_keys: Dict[str, str] = {}
        self._query_paths: Dict[Tuple[str, str], List[str]] = {}

        # Load the models
        self._load_model_classes()
        self._init_display_names()
        self._init_filter_value_map()
        self._init_relationship_mapping()
        self._init_query_paths()

        logger.info(f"Schema registry initialized with {len(self._models_by_tablename)} models")

    def _load_model_classes(self) -> None:
        """Load all model classes from the models module."""
        from ..models import models

        for attr_name in dir(models):
            attr = getattr(models, attr_name)
            if isinstance(attr, type) and hasattr(attr, "__table__") and hasattr(attr, "__tablename__"):
                self._models_by_tablename[attr.__tablename__] = attr
                self._model_primary_keys[attr.__tablename__] = self._get_primary_key(attr)

        logger.debug(
            "Loaded model classes",
            count=len(self._models_by_tablename),
            tables=list(self._models_by_tablename.keys()),
        )

    def _get_primary_key(self, model_class: Type[Base]) -> str:
        """
        Get the primary key column name for a model.

        Args:
            model_class: The SQLAlchemy model class

        Returns:
            The name of the primary key column
        """
        for column in model_class.__table__.columns:
            if column.primary_key:
                return column.name
        return "id"

    def _init_display_names(self) -> None:
        """Initialize display names for all tables and columns."""
        for table_name, model_class in self._models_by_tablename.items():
            if table_name in EXCLUDED_TABLES:
                continue

            for column in model_class.__table__.columns:
                clean_name = self._clean_display_name(model_class.__name__, column.name)
                self._display_names[table_name, column.name] = clean_name

    def _clean_display_name(self, model_name: str, column_name: str) -> str:
        """
        Create a clean, human-readable display name for a column.

        Args:
            model_name: The name of the model class
            column_name: The name of the column

        Returns:
            A clean, human-readable display name
        """
        if column_name.endswith("_id") and column_name != "id":
            column_name = column_name[:-3]

        if column_name == "id":
            return f"{model_name} ID"

        column_words = column_name.replace("_", " ").title()
        base_model_name = re.sub(r"(Config|Type|Base)$", "", model_name)

        if base_model_name.lower() in column_name.lower():
            return column_words

        return f"{base_model_name} {column_words}"

    def _init_filter_value_map(self) -> None:
        """Initialize the mapping from ID columns to display value columns."""
        # Define overrides for specific columns
        overrides = {
            ("year", "year_id"): "year_id",
            ("valves", "valves_id"): "valves_per_engine",
            ("body_num_doors", "body_num_doors_id"): "body_num_doors",
            ("transmission_num_speeds", "transmission_num_speeds_id"): "transmission_num_speeds",
            ("mfr_body_code", "mfr_body_code_id"): "mfr_body_code_name",
            ("transmission_mfr_code", "transmission_mfr_code_id"): "transmission_mfr_code",
            ("engine_vin", "engine_vin_id"): "engine_vin_name",
            ("elec_controlled", "elec_controlled_id"): "elec_controlled",
            ("power_output", "power_output_id"): "horse_power",
            ("make", "make_id"): "make_name",
            ("model", "model_id"): "model_name",
            # ... more overrides
        }

        self._filter_value_column_map = dict(overrides)

        # For columns without explicit overrides, try to determine the value column
        for table_name, model_class in self._models_by_tablename.items():
            if table_name in EXCLUDED_TABLES:
                continue

            for column in model_class.__table__.columns:
                if column.primary_key or column.name.endswith("_id"):
                    key = (table_name, column.name)
                    if key not in self._filter_value_column_map:
                        columns = [c.name for c in model_class.__table__.columns]

                        # Try to find a sensible display column
                        if "name" in columns:
                            self._filter_value_column_map[key] = "name"
                        elif f"{table_name}_name" in columns:
                            self._filter_value_column_map[key] = f"{table_name}_name"
                        elif column.name.endswith("_id") and column.name.replace("_id", "_name") in columns:
                            self._filter_value_column_map[key] = column.name.replace("_id", "_name")
                        else:
                            self._filter_value_column_map[key] = column.name

    def _init_relationship_mapping(self) -> None:
        """Initialize the relationship mapping between tables."""
        # This is simplified for brevity - you would need to reconstruct this
        # based on the actual relationships in your models
        self._relationship_mapping = {
            "vehicle": [
                "base_vehicle", "sub_model", "region", "publication_stage",
                "drive_types", "brake_configs", "bed_configs", "body_style_configs",
                "mfr_body_codes", "engine_configs", "spring_type_configs",
                "steering_configs", "transmissions", "wheel_bases", "classes"
            ],
            "base_vehicle": ["year", "make", "model"],
            "model": ["vehicle_type"],
            # ... more relationships
        }

    def _init_query_paths(self) -> None:
        """Initialize query paths for each table and column."""
        # This is simplified for brevity - you would need to reconstruct this
        # based on the actual query paths needed for your schema
        vehicle_centric_paths = {
            ("vehicle", "vehicle_id"): [],
            ("base_vehicle", "base_vehicle_id"): ["base_vehicle"],
            ("year", "year_id"): ["base_vehicle", "year"],
            ("make", "make_id"): ["base_vehicle", "make"],
            ("model", "model_id"): ["base_vehicle", "model"],
            # Add explicit path for sub_model
            ("sub_model", "sub_model_id"): ["vehicle", "sub_model"],
            ("sub_model", "sub_model_name"): ["vehicle", "sub_model"],
            # ... more paths
        }
        self._query_paths = vehicle_centric_paths

    @cache
    def get_model_for_table(self, table_name: str) -> Optional[Type[Base]]:
        """
        Get the model class for a table name.

        Args:
            table_name: The name of the database table

        Returns:
            The SQLAlchemy model class for the table, or None if not found
        """
        return self._models_by_tablename.get(table_name)

    @cache
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Get all column names for a table.

        Args:
            table_name: The name of the database table

        Returns:
            A list of column names for the table
        """
        model = self.get_model_for_table(table_name)
        if not model:
            return []
        return [column.name for column in model.__table__.columns]

    @cache
    def get_primary_key(self, table_name: str) -> Optional[str]:
        """
        Get the primary key column name for a table.

        Args:
            table_name: The name of the database table

        Returns:
            The name of the primary key column, or None if not found
        """
        return self._model_primary_keys.get(table_name)

    def get_display_name(self, table_name: str, column_name: str) -> str:
        """
        Get the display name for a table column.

        Args:
            table_name: The name of the database table
            column_name: The name of the column

        Returns:
            A human-readable display name for the column
        """
        key = (table_name, column_name)
        if key in self._display_names:
            return self._display_names[key]

        model_class = self.get_model_for_table(table_name)
        if model_class:
            return self._clean_display_name(model_class.__name__, column_name)

        return f"{table_name.title()} {column_name.title().replace('_', ' ')}"

    def get_filter_value_column(self, table_name: str, id_column: str) -> str:
        """
        Get the display value column corresponding to an ID column.

        Args:
            table_name: The name of the database table
            id_column: The name of the ID column

        Returns:
            The name of the corresponding display value column
        """
        key = (table_name, id_column)
        if key in self._filter_value_column_map:
            return self._filter_value_column_map[key]

        # Try to derive a sensible value column name
        if id_column.endswith("_id"):
            name_column = id_column.replace("_id", "_name")
            model_class = self.get_model_for_table(table_name)
            if model_class and hasattr(model_class, name_column):
                self._filter_value_column_map[key] = name_column
                return name_column

        return id_column

    def get_table_relationships(self, table_name: str) -> List[str]:
        """
        Get the related tables for a table.

        Args:
            table_name: The name of the database table

        Returns:
            A list of related table names
        """
        return self._relationship_mapping.get(table_name, []).copy()

    def get_join_path(self, table_name: str, column_name: str) -> List[str]:
        """
        Get the join path from the Vehicle table to another table.

        Args:
            table_name: The name of the target table
            column_name: The name of the target column

        Returns:
            A list of table names representing the join path
        """
        key = (table_name, column_name)
        if key in self._query_paths:
            return self._query_paths[key].copy()

        # Try using the primary key
        primary_key = self.get_primary_key(table_name)
        if primary_key:
            key = (table_name, primary_key)
            if key in self._query_paths:
                return self._query_paths[key].copy()

        # Fallback to a heuristic approach
        logger.warning(f"No join path defined for {table_name}.{column_name}. Using default path.")

        if table_name in ["make", "model", "year"]:
            return ["base_vehicle", table_name]

        if f"vehicle_to_{table_name}" in self._models_by_tablename:
            return [f"vehicle_to_{table_name}", table_name]

        return []

    def get_available_display_fields(self) -> List[Tuple[str, str, str]]:
        """
        Get all available display fields.

        Returns:
            A list of (table_name, column_name, display_name) tuples
        """
        display_fields = []

        for table_name, model_class in self._models_by_tablename.items():
            if table_name in EXCLUDED_TABLES:
                continue

            for column in model_class.__table__.columns:
                if column.primary_key and (not (table_name == "vehicle" and column.name == "vehicle_id")):
                    continue

                display_name = self.get_display_name(table_name, column.name)
                display_fields.append((table_name, column.name, display_name))

        return display_fields

    def get_available_filters(self) -> List[Tuple[str, str, str]]:
        """
        Get all available filter fields.

        Returns:
            A list of (table_name, column_name, display_name) tuples
        """
        filters: List[Tuple[str, str, str]] = []

        for table_name, model_class in self._models_by_tablename.items():
            if table_name in EXCLUDED_TABLES:
                continue

            for column in model_class.__table__.columns:
                key = (table_name, column.name)
                if key not in ALLOWED_FILTERS:
                    continue

                display_name = self.get_display_name(table_name, column.name)
                filters.append((table_name, column.name, display_name))

        return filters

    def group_filters_by_category(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """
        Group available filters by category.

        Returns:
            A dictionary mapping category names to lists of
            (table_name, column_name, display_name) tuples
        """
        all_filters = self.get_available_filters()
        groups = {
            "Basic Vehicle Info": [],
            "Engine": [],
            "Transmission": [],
            "Body": [],
            "Chassis": [],
            "Brakes": [],
            "Fuel System": [],
            "Other": [],
        }

        for table, column, display_name in all_filters:
            if table in ["year", "make", "model", "sub_model", "vehicle", "region", "vehicle_type",
                         "vehicle_type_group"]:
                groups["Basic Vehicle Info"].append((table, column, display_name))
            elif table.startswith("engine") or table in ["cylinder_head_type", "valves", "power_output",
                                                         "ignition_system_type"]:
                groups["Engine"].append((table, column, display_name))
            elif table.startswith("transmission") or table in ["elec_controlled"]:
                groups["Transmission"].append((table, column, display_name))
            elif table.startswith("body") or table in ["mfr_body_code", "bed_type", "bed_length"]:
                groups["Body"].append((table, column, display_name))
            elif table in ["wheel_base", "spring_type", "drive_type"]:
                groups["Chassis"].append((table, column, display_name))
            elif table.startswith("brake"):
                groups["Brakes"].append((table, column, display_name))
            elif table.startswith("fuel") or table in ["aspiration"]:
                groups["Fuel System"].append((table, column, display_name))
            else:
                groups["Other"].append((table, column, display_name))

        return {k: v for k, v in groups.items() if v}

    def group_display_fields_by_category(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """
        Group available display fields by category.

        Returns:
            A dictionary mapping category names to lists of
            (table_name, column_name, display_name) tuples
        """
        all_display_fields = self.get_available_display_fields()
        groups = {
            "Basic Vehicle Info": [],
            "Engine": [],
            "Transmission": [],
            "Body": [],
            "Chassis": [],
            "Brakes": [],
            "Fuel System": [],
            "Other": [],
        }

        for table, column, display_name in all_display_fields:
            if table in ["year", "make", "model", "sub_model", "vehicle", "region", "vehicle_type",
                         "vehicle_type_group"]:
                groups["Basic Vehicle Info"].append((table, column, display_name))
            elif table.startswith("engine") or table in ["cylinder_head_type", "valves", "power_output",
                                                         "ignition_system_type"]:
                groups["Engine"].append((table, column, display_name))
            elif table.startswith("transmission") or table in ["elec_controlled"]:
                groups["Transmission"].append((table, column, display_name))
            elif table.startswith("body") or table in ["mfr_body_code", "bed_type", "bed_length"]:
                groups["Body"].append((table, column, display_name))
            elif table in ["wheel_base", "spring_type", "drive_type"]:
                groups["Chassis"].append((table, column, display_name))
            elif table.startswith("brake"):
                groups["Brakes"].append((table, column, display_name))
            elif table.startswith("fuel") or table in ["aspiration"]:
                groups["Fuel System"].append((table, column, display_name))
            else:
                groups["Other"].append((table, column, display_name))

        return {k: v for k, v in groups.items() if v}

    def get_default_display_fields(self) -> List[Tuple[str, str, str]]:
        """
        Get the default display fields.

        Returns:
            A list of (table_name, column_name, display_name) tuples for the default display fields
        """
        default_fields = [
            ("year", "year_id", self.get_display_name("year", "year_id")),
            ("make", "make_name", self.get_display_name("make", "make_name")),
            ("model", "model_name", self.get_display_name("model", "model_name")),
            ("sub_model", "sub_model_name", self.get_display_name("sub_model", "sub_model_name")),
            ("engine_block", "liter", self.get_display_name("engine_block", "liter")),
            ("engine_block", "cylinders", self.get_display_name("engine_block", "cylinders")),
        ]
        return default_fields

    def get_default_filters(self) -> List[Tuple[str, str, str]]:
        """
        Get the default filters.

        Returns:
            A list of (table_name, column_name, display_name) tuples for the default filters
        """
        default_filters = [
            ("year", "year_id", self.get_display_name("year", "year_id")),
            ("make", "make_id", self.get_display_name("make", "make_id")),
            ("model", "model_id", self.get_display_name("model", "model_id")),
            ("sub_model", "sub_model_id", self.get_display_name("sub_model", "sub_model_id")),
        ]
        return default_filters

    def clear_caches(self) -> None:
        """Clear all cached results."""
        for method_name in dir(self):
            method = getattr(self, method_name)
            if hasattr(method, "cache_clear"):
                method.cache_clear()

    def cleanup(self) -> None:
        """Clean up the registry resources."""
        logger.info("Cleaning up schema registry")
        self.clear_caches()
        self._models_by_tablename.clear()
        self._display_names.clear()
        self._filter_value_column_map.clear()
        self._relationship_mapping.clear()
        self._model_primary_keys.clear()
        self._query_paths.clear()
        logger.info("Schema registry cleaned up")