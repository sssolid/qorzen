from __future__ import annotations

"""
Pydantic schema models for the InitialDB application.

This module provides the data transfer objects and validation schemas
used throughout the application.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, ClassVar
import uuid

from pydantic import BaseModel, Field, model_validator


class FilterDTO(BaseModel):
    """Data transfer object for filter criteria."""

    # Year filters
    year_ids: List[int] = Field(default_factory=list)
    year_range_start: Optional[int] = None
    year_range_end: Optional[int] = None
    use_year_range: bool = False

    # Basic vehicle filters
    make_ids: List[int] = Field(default_factory=list)
    model_ids: List[int] = Field(default_factory=list)
    sub_model_ids: List[int] = Field(default_factory=list)
    vehicle_type_ids: List[int] = Field(default_factory=list)
    vehicle_type_group_ids: List[int] = Field(default_factory=list)
    region_ids: List[int] = Field(default_factory=list)

    # Engine filters
    engine_block_ids: List[int] = Field(default_factory=list)
    engine_liters: List[str] = Field(default_factory=list)
    engine_ccs: List[str] = Field(default_factory=list)
    engine_cids: List[str] = Field(default_factory=list)
    engine_cylinders: List[str] = Field(default_factory=list)
    engine_block_types: List[str] = Field(default_factory=list)
    cylinder_head_type_ids: List[int] = Field(default_factory=list)
    valves_ids: List[int] = Field(default_factory=list)
    eng_bore_ins: List[str] = Field(default_factory=list)
    eng_stroke_ins: List[str] = Field(default_factory=list)
    engine_designation_ids: List[int] = Field(default_factory=list)
    engine_version_ids: List[int] = Field(default_factory=list)
    engine_vin_ids: List[int] = Field(default_factory=list)
    ignition_system_type_ids: List[int] = Field(default_factory=list)
    engine_mfr_ids: List[int] = Field(default_factory=list)
    power_output_ids: List[int] = Field(default_factory=list)

    # Fuel filters
    fuel_type_ids: List[int] = Field(default_factory=list)
    fuel_delivery_type_ids: List[int] = Field(default_factory=list)
    fuel_delivery_sub_type_ids: List[int] = Field(default_factory=list)
    fuel_system_control_type_ids: List[int] = Field(default_factory=list)
    fuel_system_design_ids: List[int] = Field(default_factory=list)
    aspiration_ids: List[int] = Field(default_factory=list)

    # Body filters
    mfr_body_code_ids: List[int] = Field(default_factory=list)
    body_num_doors_ids: List[int] = Field(default_factory=list)
    body_type_ids: List[int] = Field(default_factory=list)
    bed_type_ids: List[int] = Field(default_factory=list)
    bed_length_ids: List[int] = Field(default_factory=list)
    wheel_base_ids: List[int] = Field(default_factory=list)

    # Drive and suspension filters
    drive_type_ids: List[int] = Field(default_factory=list)
    spring_type_ids: List[int] = Field(default_factory=list)
    front_spring_type_ids: List[int] = Field(default_factory=list)
    rear_spring_type_ids: List[int] = Field(default_factory=list)

    # Brake filters
    brake_abs_ids: List[int] = Field(default_factory=list)
    brake_system_ids: List[int] = Field(default_factory=list)
    brake_type_ids: List[int] = Field(default_factory=list)
    front_brake_type_ids: List[int] = Field(default_factory=list)
    rear_brake_type_ids: List[int] = Field(default_factory=list)

    # Steering filters
    steering_system_ids: List[int] = Field(default_factory=list)
    steering_type_ids: List[int] = Field(default_factory=list)

    # Transmission filters
    transmission_control_type_ids: List[int] = Field(default_factory=list)
    transmission_mfr_code_ids: List[int] = Field(default_factory=list)
    transmission_type_ids: List[int] = Field(default_factory=list)
    transmission_num_speeds_ids: List[int] = Field(default_factory=list)
    transmission_mfr_ids: List[int] = Field(default_factory=list)
    elec_controlled_ids: List[int] = Field(default_factory=list)

    # Tracking active filters
    active_filters: Dict[str, Any] = Field(default_factory=dict)

    # Mapping between singular and plural fields
    _field_mappings: ClassVar[Dict[str, str]] = {}

    def __init__(self, **data: Any):
        """Initialize the filter DTO with data.

        Handles mapping between singular and plural field names.

        Args:
            **data: Field values
        """
        # Initialize field mappings if not already done
        if not FilterDTO._field_mappings:
            for field_name in FilterDTO.__annotations__:
                if field_name.endswith('_ids'):
                    singular = field_name[:-1]
                    FilterDTO._field_mappings[singular] = field_name
                elif field_name.endswith('s') and field_name != 'active_filters':
                    singular = field_name[:-1]
                    FilterDTO._field_mappings[singular] = field_name

        # Process singular values into plural lists
        for singular, plural in FilterDTO._field_mappings.items():
            if singular in data and plural in data:
                singular_value = data[singular]
                plural_values = data[plural]
                if singular_value is not None and singular_value not in plural_values:
                    plural_values.append(singular_value)
                    data[plural] = plural_values
            elif singular in data and plural not in data:
                data[plural] = [data[singular]]

        # Set singular values from plural lists
        for singular, plural in FilterDTO._field_mappings.items():
            if plural in data and singular not in data:
                values = data[plural]
                data[singular] = values[0] if values else None

        super().__init__(**data)

    def __getattr__(self, name: str) -> Any:
        """Get attribute, supporting singular forms of plural fields.

        Args:
            name: Attribute name

        Returns:
            Attribute value

        Raises:
            AttributeError: If attribute doesn't exist
        """
        if name in FilterDTO._field_mappings:
            plural = FilterDTO._field_mappings[name]
            plural_values = getattr(self, plural)
            return plural_values[0] if plural_values else None
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute, supporting singular forms of plural fields.

        Args:
            name: Attribute name
            value: Attribute value
        """
        if name in FilterDTO._field_mappings:
            plural = FilterDTO._field_mappings[name]
            plural_values = getattr(self, plural)

            if value is None:
                super().__setattr__(plural, [])
            elif not plural_values:
                super().__setattr__(plural, [value])
            elif value != plural_values[0]:
                plural_values[0] = value
                super().__setattr__(plural, plural_values)

            # Update active filters
            active_filters = self.active_filters
            if value is None:
                if plural in active_filters:
                    active_filters[plural] = []
            elif plural not in active_filters:
                active_filters[plural] = [value]
            elif value not in active_filters[plural]:
                active_filters[plural] = [value] + active_filters[plural][1:]

            super().__setattr__('active_filters', active_filters)
        else:
            super().__setattr__(name, value)

    @model_validator(mode='after')
    def sync_single_and_multi_values(self) -> 'FilterDTO':
        """Synchronize singular and plural filter values.

        Returns:
            Validated FilterDTO
        """
        active = {}

        # Add non-empty plural fields to active filters
        for singular, plural in FilterDTO._field_mappings.items():
            plural_values = getattr(self, plural, [])
            if plural_values:
                active[plural] = plural_values

        # Add year range to active filters if enabled
        if self.use_year_range and self.year_range_start is not None and self.year_range_end is not None:
            active['year_range'] = {'start': self.year_range_start, 'end': self.year_range_end}

        self.active_filters = active
        return self

    def is_filter_active(self, filter_name: str) -> bool:
        """Check if a filter is active.

        Args:
            filter_name: Filter field name

        Returns:
            True if filter is active, False otherwise
        """
        if filter_name.endswith('_id'):
            list_field = f'{filter_name}s'
            return list_field in self.active_filters and bool(self.active_filters[list_field])
        return filter_name in self.active_filters and bool(self.active_filters[filter_name])

    def get_filter_values(self, filter_name: str) -> List[Any]:
        """Get values for a filter.

        Args:
            filter_name: Filter field name

        Returns:
            List of filter values
        """
        if filter_name.endswith('_id'):
            list_field = f'{filter_name}s'
            return self.active_filters.get(list_field, [])
        return self.active_filters.get(filter_name, [])

    def add_filter_value(self, filter_name: str, value: Any) -> None:
        """Add a value to a filter.

        Args:
            filter_name: Filter field name
            value: Value to add
        """
        if filter_name.endswith('_id'):
            list_field = f'{filter_name}s'
            if list_field not in self.active_filters:
                self.active_filters[list_field] = []

            if value not in self.active_filters[list_field]:
                self.active_filters[list_field].append(value)
                field_values = getattr(self, list_field)

                if value not in field_values:
                    field_values.append(value)

                setattr(self, filter_name, value if len(field_values) == 1 else field_values[0])
        else:
            if filter_name not in self.active_filters:
                self.active_filters[filter_name] = []

            if value not in self.active_filters[filter_name]:
                self.active_filters[filter_name].append(value)

    def remove_filter_value(self, filter_name: str, value: Any) -> None:
        """Remove a value from a filter.

        Args:
            filter_name: Filter field name
            value: Value to remove
        """
        if filter_name.endswith('_id'):
            list_field = f'{filter_name}s'
            if list_field in self.active_filters and value in self.active_filters[list_field]:
                self.active_filters[list_field].remove(value)
                field_values = getattr(self, list_field)

                if value in field_values:
                    field_values.remove(value)

                if field_values:
                    setattr(self, filter_name, field_values[0])
                else:
                    setattr(self, filter_name, None)
        elif filter_name in self.active_filters and value in self.active_filters[filter_name]:
            self.active_filters[filter_name].remove(value)

    def clear_filter(self, filter_name: str) -> None:
        """Clear all values for a filter.

        Args:
            filter_name: Filter field name
        """
        if filter_name.endswith('_id'):
            list_field = f'{filter_name}s'
            if list_field in self.active_filters:
                self.active_filters[list_field] = []

            setattr(self, list_field, [])
            setattr(self, filter_name, None)
        elif filter_name in self.active_filters:
            self.active_filters[filter_name] = []


class DisplayField(BaseModel):
    """Model for display field configuration."""

    table: str
    field: str
    display_name: str
    visible: bool = True
    order: int


class DisplayConfiguration(BaseModel):
    """Model for display configuration."""

    fields: List[DisplayField] = Field(default_factory=list)


class VehicleSearchParameters(BaseModel):
    """Model for vehicle search parameters."""

    year: Optional[int] = Field(None, description="Filter by year")
    make: Optional[str] = Field(None, description="Filter by make name")
    model: Optional[str] = Field(None, description="Filter by model name")
    sub_model: Optional[str] = Field(None, description="Filter by sub_model name")
    body_type: Optional[str] = Field(None, description="Filter by body type")
    engine_config: Optional[int] = Field(None, description="Filter by engine configuration ID")
    transmission_type: Optional[int] = Field(None, description="Filter by transmission type ID")
    page: int = Field(1, description="Page number", ge=1)
    page_size: int = Field(20, description="Page size", ge=1, le=100)


class SavedQueryDTO(BaseModel):
    """Data transfer object for saved queries."""

    id: str
    name: str
    description: Optional[str] = None
    filters: Union[Dict[str, Any], FilterDTO]
    visible_columns: List[tuple[str, str, str]]
    is_multi_query: bool = False


class VehicleResultDTO(BaseModel):
    """Data transfer object for vehicle search results."""

    vehicle_id: int
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    sub_model: Optional[str] = None
    region: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_type_group: Optional[str] = None
    engine_liter: Optional[str] = None
    engine_cc: Optional[str] = None
    engine_cid: Optional[str] = None
    engine_cylinders: Optional[str] = None
    engine_block_type: Optional[str] = None
    cylinder_head_type: Optional[str] = None
    valves: Optional[str] = None
    eng_bore_in: Optional[str] = None
    eng_bore_metric: Optional[str] = None
    eng_stroke_in: Optional[str] = None
    eng_stroke_metric: Optional[str] = None
    engine_designation: Optional[str] = None
    engine_version: Optional[str] = None
    engine_vin: Optional[str] = None
    engine_manufacturer: Optional[str] = None
    horsepower: Optional[str] = None
    kilowatt: Optional[str] = None
    mfr_body_code: Optional[str] = None
    body_num_doors: Optional[str] = None
    body_type: Optional[str] = None
    bed_length: Optional[str] = None
    bed_length_metric: Optional[str] = None
    bed_type: Optional[str] = None
    wheel_base: Optional[str] = None
    wheel_base_metric: Optional[str] = None
    drive_type: Optional[str] = None
    front_spring_type: Optional[str] = None
    rear_spring_type: Optional[str] = None
    brake_abs: Optional[str] = None
    brake_system: Optional[str] = None
    front_brake_type: Optional[str] = None
    rear_brake_type: Optional[str] = None
    steering_system: Optional[str] = None
    steering_type: Optional[str] = None
    transmission_control_type: Optional[str] = None
    transmission_mfr_code: Optional[str] = None
    transmission_type: Optional[str] = None
    transmission_num_speeds: Optional[str] = None
    elec_controlled: Optional[str] = None
    transmission_manufacturer: Optional[str] = None
    fuel_type: Optional[str] = None
    fuel_delivery_type: Optional[str] = None
    fuel_delivery_sub_type: Optional[str] = None
    fuel_system_control_type: Optional[str] = None
    fuel_system_design: Optional[str] = None
    ignition_system_type: Optional[str] = None
    source: Optional[str] = None

    # Allow additional fields
    model_config = {'extra': 'allow'}


class VehicleSearchResponse(BaseModel):
    """Model for paginated vehicle search response."""

    items: List[VehicleResultDTO] = Field(..., description="List of vehicles")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")