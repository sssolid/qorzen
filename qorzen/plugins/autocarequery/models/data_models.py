from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship

# Base class for SQLAlchemy models
Base = declarative_base()


class DatabaseConnectionError(Exception):
    """Exception raised when there's an issue connecting to the database."""
    pass


class QueryExecutionError(Exception):
    """Exception raised when there's an issue executing a query."""
    pass


class InvalidFilterError(Exception):
    """Exception raised when a filter is invalid."""
    pass


class ExportError(Exception):
    """Exception raised when there's an issue exporting data."""
    pass


class BaseModelClass(Base):
    """Base model class for all database tables."""
    __abstract__ = True

    id = Column(String, primary_key=True)
    created_at = Column(String)
    updated_at = Column(String)
    is_deleted = Column(String)
    created_by_id = Column(String, nullable=True)
    updated_by_id = Column(String, nullable=True)


class Year(BaseModelClass):
    """Model for the year table."""
    __tablename__ = 'year'

    year_id = Column(Integer, nullable=False)


class Make(BaseModelClass):
    """Model for the make table."""
    __tablename__ = 'make'

    make_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)


class Model(BaseModelClass):
    """Model for the model table."""
    __tablename__ = 'model'

    model_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    vehicle_type_id = Column(Integer, ForeignKey('vehicle_type.vehicle_type_id'), nullable=False)


class Submodel(BaseModelClass):
    """Model for the submodel table."""
    __tablename__ = 'submodel'

    submodel_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)


class EngineBase(BaseModelClass):
    """Model for the engine_base table."""
    __tablename__ = 'engine_base'

    engine_base_id = Column(Integer, nullable=False)
    liter = Column(String, nullable=False)
    cc = Column(String, nullable=False)
    cid = Column(String, nullable=False)
    cylinders = Column(String, nullable=False)
    block_type = Column(String, nullable=False)
    eng_bore_in = Column(String, nullable=False)
    eng_bore_metric = Column(String, nullable=False)
    eng_stroke_in = Column(String, nullable=False)
    eng_stroke_metric = Column(String, nullable=False)


class EngineBlock(BaseModelClass):
    """Model for the engine_block table."""
    __tablename__ = 'engine_block'

    engine_block_id = Column(Integer, nullable=False)
    liter = Column(String, nullable=False)
    cc = Column(String, nullable=False)
    cid = Column(String, nullable=False)
    cylinders = Column(String, nullable=False)
    block_type = Column(String, nullable=False)


class CylinderHeadType(BaseModelClass):
    """Model for the cylinder_head_type table."""
    __tablename__ = 'cylinder_head_type'

    cylinder_head_type_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)


class Valves(BaseModelClass):
    """Model for the valves table."""
    __tablename__ = 'valves'

    valves_id = Column(Integer, nullable=False)
    valves_per_engine = Column(String, nullable=False)


class MfrBodyCode(BaseModelClass):
    """Model for the mfr_body_code table."""
    __tablename__ = 'mfr_body_code'

    mfr_body_code_id = Column(Integer, nullable=False)
    code = Column(String, nullable=False)


class BodyNumDoors(BaseModelClass):
    """Model for the body_num_doors table."""
    __tablename__ = 'body_num_doors'

    body_num_doors_id = Column(Integer, nullable=False)
    num_doors = Column(String, nullable=False)


class WheelBase(BaseModelClass):
    """Model for the wheel_base table."""
    __tablename__ = 'wheel_base'

    wheel_base_id = Column(Integer, nullable=False)
    wheel_base = Column(String, nullable=False)
    wheel_base_metric = Column(String, nullable=False)


class BrakeAbs(BaseModelClass):
    """Model for the brake_abs table."""
    __tablename__ = 'brake_abs'

    brake_abs_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)


class SteeringSystem(BaseModelClass):
    """Model for the steering_system table."""
    __tablename__ = 'steering_system'

    steering_system_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)


class TransmissionControlType(BaseModelClass):
    """Model for the transmission_control_type table."""
    __tablename__ = 'transmission_control_type'

    transmission_control_type_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)


class TransmissionMfrCode(BaseModelClass):
    """Model for the transmission_mfr_code table."""
    __tablename__ = 'transmission_mfr_code'

    transmission_mfr_code_id = Column(Integer, nullable=False)
    code = Column(String, nullable=False)


class DriveType(BaseModelClass):
    """Model for the drive_type table."""
    __tablename__ = 'drive_type'

    drive_type_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)


class BaseVehicle(BaseModelClass):
    """Model for the base_vehicle table."""
    __tablename__ = 'base_vehicle'

    base_vehicle_id = Column(Integer, nullable=False)
    year_id = Column(Integer, ForeignKey('year.year_id'), nullable=False)
    make_id = Column(Integer, ForeignKey('make.make_id'), nullable=False)
    model_id = Column(Integer, ForeignKey('model.model_id'), nullable=False)


class Vehicle(BaseModelClass):
    """Model for the vehicle table."""
    __tablename__ = 'vehicle'

    vehicle_id = Column(Integer, nullable=False)
    base_vehicle_id = Column(Integer, ForeignKey('base_vehicle.base_vehicle_id'), nullable=False)
    submodel_id = Column(Integer, ForeignKey('submodel.submodel_id'), nullable=False)
    region_id = Column(Integer, nullable=False)
    source = Column(String, nullable=True)
    publication_stage_id = Column(Integer, nullable=False)
    publication_stage_source = Column(String, nullable=False)
    publication_stage_date = Column(String, nullable=False)


class VehicleToEngineConfig(BaseModelClass):
    """Model for the vehicle_to_engine_config table."""
    __tablename__ = 'vehicle_to_engine_config'

    vehicle_to_engine_config_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.vehicle_id'), nullable=False)
    engine_config_id = Column(Integer, nullable=False)
    source = Column(String, nullable=True)


class VehicleToMfrBodyCode(BaseModelClass):
    """Model for the vehicle_to_mfr_body_code table."""
    __tablename__ = 'vehicle_to_mfr_body_code'

    vehicle_to_mfr_body_code_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.vehicle_id'), nullable=False)
    mfr_body_code_id = Column(Integer, ForeignKey('mfr_body_code.mfr_body_code_id'), nullable=False)
    source = Column(String, nullable=True)


class VehicleToBodyStyleConfig(BaseModelClass):
    """Model for the vehicle_to_body_style_config table."""
    __tablename__ = 'vehicle_to_body_style_config'

    vehicle_to_body_style_config_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.vehicle_id'), nullable=False)
    body_style_config_id = Column(Integer, nullable=False)
    source = Column(String, nullable=True)


class VehicleToWheelBase(BaseModelClass):
    """Model for the vehicle_to_wheel_base table."""
    __tablename__ = 'vehicle_to_wheel_base'

    vehicle_to_wheel_base_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.vehicle_id'), nullable=False)
    wheel_base_id = Column(Integer, ForeignKey('wheel_base.wheel_base_id'), nullable=False)
    source = Column(String, nullable=True)


class VehicleToBrakeConfig(BaseModelClass):
    """Model for the vehicle_to_brake_config table."""
    __tablename__ = 'vehicle_to_brake_config'

    vehicle_to_brake_config_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.vehicle_id'), nullable=False)
    brake_config_id = Column(Integer, nullable=False)
    source = Column(String, nullable=True)


class VehicleToSteeringConfig(BaseModelClass):
    """Model for the vehicle_to_steering_config table."""
    __tablename__ = 'vehicle_to_steering_config'

    vehicle_to_steering_config_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.vehicle_id'), nullable=False)
    steering_config_id = Column(Integer, nullable=False)
    source = Column(String, nullable=True)


class VehicleToTransmission(BaseModelClass):
    """Model for the vehicle_to_transmission table."""
    __tablename__ = 'vehicle_to_transmission'

    vehicle_to_transmission_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.vehicle_id'), nullable=False)
    transmission_id = Column(Integer, nullable=False)
    source = Column(String, nullable=True)


class VehicleToDriveType(BaseModelClass):
    """Model for the vehicle_to_drive_type table."""
    __tablename__ = 'vehicle_to_drive_type'

    vehicle_to_drive_type_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.vehicle_id'), nullable=False)
    drive_type_id = Column(Integer, ForeignKey('drive_type.drive_type_id'), nullable=False)
    source = Column(String, nullable=True)


class FilterDTO(BaseModel):
    """Data transfer object for filter criteria."""

    year_id: Optional[int] = None
    year_range_start: Optional[int] = None
    year_range_end: Optional[int] = None
    use_year_range: bool = False
    make_id: Optional[int] = None
    model_id: Optional[int] = None
    submodel_id: Optional[int] = None
    engine_liter: Optional[str] = None
    engine_cid: Optional[str] = None
    cylinder_head_type_id: Optional[int] = None
    valves_id: Optional[int] = None
    mfr_body_code_id: Optional[int] = None
    body_num_doors_id: Optional[int] = None
    wheel_base_id: Optional[int] = None
    brake_abs_id: Optional[int] = None
    steering_system_id: Optional[int] = None
    transmission_control_type_id: Optional[int] = None
    transmission_mfr_code_id: Optional[int] = None
    drive_type_id: Optional[int] = None

    class Config:
        frozen = False


class VehicleResultDTO(BaseModel):
    """Data transfer object for vehicle query results."""

    vehicle_id: int
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    submodel: Optional[str] = None
    engine_liter: Optional[str] = None
    engine_cylinders: Optional[str] = None
    engine_block_type: Optional[str] = None
    engine_cc: Optional[str] = None
    engine_cid: Optional[str] = None
    cylinder_head_type: Optional[str] = None
    valves: Optional[str] = None
    mfr_body_code: Optional[str] = None
    body_num_doors: Optional[str] = None
    wheel_base: Optional[str] = None
    wheel_base_metric: Optional[str] = None
    brake_abs: Optional[str] = None
    steering_system: Optional[str] = None
    transmission_control_type: Optional[str] = None
    transmission_mfr_code: Optional[str] = None
    drive_type: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        frozen = True