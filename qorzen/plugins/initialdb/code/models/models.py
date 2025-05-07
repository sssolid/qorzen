from __future__ import annotations

"""
VCdb (Vehicle Component Database) models.

This module defines the SQLAlchemy models that correspond to the VCdb database schema.
These models represent vehicle information and their components according to
Auto Care Association standards.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from sqlalchemy.sql import func
import uuid

VCdbBase = declarative_base()


class DatabaseConnectionError(Exception):
    """Raised when a database connection cannot be established."""
    pass


class QueryExecutionError(Exception):
    """Raised when a query fails to execute."""
    pass


class InvalidFilterError(Exception):
    """Raised when an invalid filter is provided."""
    pass


class ExportError(Exception):
    """Raised when an export operation fails."""
    pass


class ConfigurationError(Exception):
    """Raised when there is an error in the configuration."""
    pass


class Abbreviation(VCdbBase):
    """Abbreviation model representing abbreviations used in the system."""
    __tablename__ = "abbreviation"
    __table_args__ = {"schema": "vcdb"}

    abbreviation: Mapped[str] = mapped_column(String(3), primary_key=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(20), nullable=False)
    long_description: Mapped[str] = mapped_column(String(200), nullable=False)

    def __repr__(self) -> str:
        return f"<Abbreviation {self.abbreviation}>"


class Make(VCdbBase):
    """Make model representing vehicle manufacturers."""
    __tablename__ = "make"
    __table_args__ = {"schema": "vcdb"}

    make_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    make_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    vehicles: Mapped[List["Vehicle"]] = relationship(
        "Vehicle",
        secondary="vcdb.base_vehicle",
        primaryjoin="Make.make_id == BaseVehicle.make_id",
        secondaryjoin="BaseVehicle.base_vehicle_id == Vehicle.base_vehicle_id",
        viewonly=True
    )
    base_vehicles: Mapped[List["BaseVehicle"]] = relationship("BaseVehicle", back_populates="make")

    def __repr__(self) -> str:
        return f"<Make {self.make_name} ({self.make_id})>"


class VehicleTypeGroup(VCdbBase):
    """VehicleTypeGroup model representing groups of vehicle types."""
    __tablename__ = "vehicle_type_group"
    __table_args__ = {"schema": "vcdb"}

    vehicle_type_group_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                       index=True)
    vehicle_type_group_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    vehicle_types: Mapped[List["VehicleType"]] = relationship("VehicleType", back_populates="vehicle_type_group")

    def __repr__(self) -> str:
        return f"<VehicleTypeGroup {self.vehicle_type_group_name} ({self.vehicle_type_group_id})>"


class VehicleType(VCdbBase):
    """VehicleType model representing types of vehicles."""
    __tablename__ = "vehicle_type"
    __table_args__ = {"schema": "vcdb"}

    vehicle_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    vehicle_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vehicle_type_group_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle_type_group.vehicle_type_group_id"),
        nullable=True
    )

    models: Mapped[List["Model"]] = relationship("Model", back_populates="vehicle_type")
    vehicle_type_group: Mapped[Optional["VehicleTypeGroup"]] = relationship("VehicleTypeGroup",
                                                                            back_populates="vehicle_types")

    def __repr__(self) -> str:
        return f"<VehicleType {self.vehicle_type_name} ({self.vehicle_type_id})>"


class Model(VCdbBase):
    """Model model representing vehicle models."""
    __tablename__ = "model"
    __table_args__ = {"schema": "vcdb"}

    model_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vehicle_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle_type.vehicle_type_id"),
        nullable=False,
        index=True
    )

    base_vehicles: Mapped[List["BaseVehicle"]] = relationship("BaseVehicle", back_populates="model")
    vehicle_type: Mapped["VehicleType"] = relationship("VehicleType", back_populates="models")

    def __repr__(self) -> str:
        return f"<Model {self.model_name} ({self.model_id})>"


class SubModel(VCdbBase):
    """SubModel model representing vehicle sub_models."""
    __tablename__ = "sub_model"
    __table_args__ = {"schema": "vcdb"}

    sub_model_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    sub_model_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", back_populates="sub_model")

    def __repr__(self) -> str:
        return f"<SubModel {self.sub_model_name} ({self.sub_model_id})>"


class Region(VCdbBase):
    """Region model representing geographical regions."""
    __tablename__ = "region"
    __table_args__ = (
        UniqueConstraint("region_id", name="uq_region_id"),
        {"schema": "vcdb"}
    )

    region_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("vcdb.region.region_id"),
        nullable=True
    )
    region_abbr: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    region_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    parent: Mapped[Optional["Region"]] = relationship("Region", remote_side=[region_id], back_populates="children")
    children: Mapped[List["Region"]] = relationship("Region", back_populates="parent", cascade="all, delete-orphan")
    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", back_populates="region")

    def __repr__(self) -> str:
        return f"<Region {self.region_name} ({self.region_id})>"


class Year(VCdbBase):
    """Year model representing vehicle production years."""
    __tablename__ = "year"
    __table_args__ = {"schema": "vcdb"}

    year_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)

    base_vehicles: Mapped[List["BaseVehicle"]] = relationship("BaseVehicle", back_populates="year")

    def __repr__(self) -> str:
        return f"<Year {self.year_id}>"


class PublicationStage(VCdbBase):
    """PublicationStage model representing stages of publication."""
    __tablename__ = "publication_stage"
    __table_args__ = {"schema": "vcdb"}

    publication_stage_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                      index=True)
    publication_stage_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", back_populates="publication_stage")

    def __repr__(self) -> str:
        return f"<PublicationStage {self.publication_stage_name} ({self.publication_stage_id})>"


class BaseVehicle(VCdbBase):
    """BaseVehicle model representing base vehicle configurations."""
    __tablename__ = "base_vehicle"
    __table_args__ = {"schema": "vcdb"}

    base_vehicle_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    year_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.year.year_id"),
        nullable=False,
        index=True
    )
    make_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.make.make_id"),
        nullable=False,
        index=True
    )
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.model.model_id"),
        nullable=False,
        index=True
    )

    year: Mapped["Year"] = relationship("Year", back_populates="base_vehicles")
    make: Mapped["Make"] = relationship("Make", back_populates="base_vehicles")
    model: Mapped["Model"] = relationship("Model", back_populates="base_vehicles")
    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", back_populates="base_vehicle")

    def __repr__(self) -> str:
        return f"<BaseVehicle {self.base_vehicle_id}>"


class Vehicle(VCdbBase):
    """Vehicle model representing specific vehicle configurations."""
    __tablename__ = "vehicle"
    __table_args__ = {"schema": "vcdb"}

    vehicle_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    base_vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.base_vehicle.base_vehicle_id"),
        nullable=False,
        index=True
    )
    sub_model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.sub_model.sub_model_id"),
        nullable=False,
        index=True
    )
    region_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.region.region_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    publication_stage_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.publication_stage.publication_stage_id"),
        nullable=False,
        default=4,
        index=True
    )
    publication_stage_source: Mapped[str] = mapped_column(String(100), nullable=False)
    publication_stage_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    base_vehicle: Mapped["BaseVehicle"] = relationship("BaseVehicle", back_populates="vehicles")
    sub_model: Mapped["SubModel"] = relationship("SubModel", back_populates="vehicles")
    region: Mapped["Region"] = relationship("Region", back_populates="vehicles")
    publication_stage: Mapped["PublicationStage"] = relationship("PublicationStage", back_populates="vehicles")

    drive_types: Mapped[List["DriveType"]] = relationship("DriveType", secondary="vcdb.vehicle_to_drive_type")
    brake_configs: Mapped[List["BrakeConfig"]] = relationship("BrakeConfig", secondary="vcdb.vehicle_to_brake_config")
    bed_configs: Mapped[List["BedConfig"]] = relationship("BedConfig", secondary="vcdb.vehicle_to_bed_config")
    body_style_configs: Mapped[List["BodyStyleConfig"]] = relationship("BodyStyleConfig",
                                                                       secondary="vcdb.vehicle_to_body_style_config")
    mfr_body_codes: Mapped[List["MfrBodyCode"]] = relationship("MfrBodyCode", secondary="vcdb.vehicle_to_mfr_body_code")
    engine_configs: Mapped[List["EngineConfig2"]] = relationship(
        "EngineConfig2",
        secondary="vcdb.vehicle_to_engine_config",
        primaryjoin="Vehicle.vehicle_id == VehicleToEngineConfig.vehicle_id",
        secondaryjoin="VehicleToEngineConfig.engine_config_id == EngineConfig2.engine_config_id"
    )
    spring_type_configs: Mapped[List["SpringTypeConfig"]] = relationship("SpringTypeConfig",
                                                                         secondary="vcdb.vehicle_to_spring_type_config")
    steering_configs: Mapped[List["SteeringConfig"]] = relationship("SteeringConfig",
                                                                    secondary="vcdb.vehicle_to_steering_config")
    transmissions: Mapped[List["Transmission"]] = relationship("Transmission", secondary="vcdb.vehicle_to_transmission")
    wheel_bases: Mapped[List["WheelBase"]] = relationship("WheelBase", secondary="vcdb.vehicle_to_wheel_base")
    classes: Mapped[List["Class"]] = relationship("Class", secondary="vcdb.vehicle_to_class", back_populates="vehicles")
    body_configs: Mapped[List["VehicleToBodyConfig"]] = relationship("VehicleToBodyConfig", back_populates="vehicle")

    @property
    def make(self) -> Make:
        """Get the make of the vehicle."""
        return self.base_vehicle.make

    @property
    def year(self) -> Optional[int]:
        """Get the year of the vehicle."""
        if self.base_vehicle and self.base_vehicle.year:
            return self.base_vehicle.year.year_id
        return None

    @property
    def model(self) -> str:
        """Get the model name of the vehicle."""
        return self.base_vehicle.model.model_name

    def __repr__(self) -> str:
        return f"<Vehicle {self.vehicle_id}>"


class DriveType(VCdbBase):
    """DriveType model representing types of drive systems."""
    __tablename__ = "drive_type"
    __table_args__ = {"schema": "vcdb"}

    drive_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    drive_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<DriveType {self.drive_type_name} ({self.drive_type_id})>"


class VehicleToDriveType(VCdbBase):
    """VehicleToDriveType model representing the relationship between vehicles and drive types."""
    __tablename__ = "vehicle_to_drive_type"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_drive_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                          index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    drive_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.drive_type.drive_type_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToDriveType {self.vehicle_to_drive_type_id}>"


class BrakeType(VCdbBase):
    """BrakeType model representing types of brake systems."""
    __tablename__ = "brake_type"
    __table_args__ = {"schema": "vcdb"}

    brake_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    brake_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    front_brake_configs: Mapped[List["BrakeConfig"]] = relationship(
        "BrakeConfig",
        primaryjoin="BrakeType.brake_type_id == BrakeConfig.front_brake_type_id",
        back_populates="front_brake_type"
    )
    rear_brake_configs: Mapped[List["BrakeConfig"]] = relationship(
        "BrakeConfig",
        primaryjoin="BrakeType.brake_type_id == BrakeConfig.rear_brake_type_id",
        back_populates="rear_brake_type"
    )

    def __repr__(self) -> str:
        return f"<BrakeType {self.brake_type_name} ({self.brake_type_id})>"


class BrakeSystem(VCdbBase):
    """BrakeSystem model representing brake system configurations."""
    __tablename__ = "brake_system"
    __table_args__ = {"schema": "vcdb"}

    brake_system_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    brake_system_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    brake_configs: Mapped[List["BrakeConfig"]] = relationship("BrakeConfig", back_populates="brake_system")

    def __repr__(self) -> str:
        return f"<BrakeSystem {self.brake_system_name} ({self.brake_system_id})>"


class BrakeABS(VCdbBase):
    """BrakeABS model representing anti-lock brake systems."""
    __tablename__ = "brake_abs"
    __table_args__ = {"schema": "vcdb"}

    brake_abs_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    brake_abs_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    brake_configs: Mapped[List["BrakeConfig"]] = relationship("BrakeConfig", back_populates="brake_abs")

    def __repr__(self) -> str:
        return f"<BrakeABS {self.brake_abs_name} ({self.brake_abs_id})>"


class BrakeConfig(VCdbBase):
    """BrakeConfig model representing complete brake system configurations."""
    __tablename__ = "brake_config"
    __table_args__ = {"schema": "vcdb"}

    brake_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    front_brake_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.brake_type.brake_type_id"),
        nullable=False,
        index=True
    )
    rear_brake_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.brake_type.brake_type_id"),
        nullable=False,
        index=True
    )
    brake_system_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.brake_system.brake_system_id"),
        nullable=False,
        index=True
    )
    brake_abs_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.brake_abs.brake_abs_id"),
        nullable=False,
        index=True
    )

    front_brake_type: Mapped["BrakeType"] = relationship(
        "BrakeType",
        primaryjoin="BrakeConfig.front_brake_type_id == BrakeType.brake_type_id",
        back_populates="front_brake_configs"
    )
    rear_brake_type: Mapped["BrakeType"] = relationship(
        "BrakeType",
        primaryjoin="BrakeConfig.rear_brake_type_id == BrakeType.brake_type_id",
        back_populates="rear_brake_configs"
    )
    brake_system: Mapped["BrakeSystem"] = relationship("BrakeSystem", back_populates="brake_configs")
    brake_abs: Mapped["BrakeABS"] = relationship("BrakeABS", back_populates="brake_configs")

    def __repr__(self) -> str:
        return f"<BrakeConfig {self.brake_config_id}>"


class VehicleToBrakeConfig(VCdbBase):
    """VehicleToBrakeConfig model representing the relationship between vehicles and brake configurations."""
    __tablename__ = "vehicle_to_brake_config"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_brake_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                            index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    brake_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.brake_config.brake_config_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToBrakeConfig {self.vehicle_to_brake_config_id}>"


class BedType(VCdbBase):
    """BedType model representing types of vehicle beds."""
    __tablename__ = "bed_type"
    __table_args__ = {"schema": "vcdb"}

    bed_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    bed_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    bed_configs: Mapped[List["BedConfig"]] = relationship("BedConfig", back_populates="bed_type")

    def __repr__(self) -> str:
        return f"<BedType {self.bed_type_name} ({self.bed_type_id})>"


class BedLength(VCdbBase):
    """BedLength model representing lengths of vehicle beds."""
    __tablename__ = "bed_length"
    __table_args__ = {"schema": "vcdb"}

    bed_length_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    bed_length: Mapped[str] = mapped_column(String(10), nullable=False)
    bed_length_metric: Mapped[str] = mapped_column(String(10), nullable=False)

    bed_configs: Mapped[List["BedConfig"]] = relationship("BedConfig", back_populates="bed_length")

    def __repr__(self) -> str:
        return f"<BedLength {self.bed_length} ({self.bed_length_id})>"


class BedConfig(VCdbBase):
    """BedConfig model representing complete bed configurations."""
    __tablename__ = "bed_config"
    __table_args__ = {"schema": "vcdb"}

    bed_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    bed_length_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.bed_length.bed_length_id"),
        nullable=False,
        index=True
    )
    bed_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.bed_type.bed_type_id"),
        nullable=False,
        index=True
    )

    bed_length: Mapped["BedLength"] = relationship("BedLength", back_populates="bed_configs")
    bed_type: Mapped["BedType"] = relationship("BedType", back_populates="bed_configs")

    def __repr__(self) -> str:
        return f"<BedConfig {self.bed_config_id}>"


class VehicleToBedConfig(VCdbBase):
    """VehicleToBedConfig model representing the relationship between vehicles and bed configurations."""
    __tablename__ = "vehicle_to_bed_config"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_bed_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                          index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    bed_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.bed_config.bed_config_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToBedConfig {self.vehicle_to_bed_config_id}>"


class BodyType(VCdbBase):
    """BodyType model representing types of vehicle bodies."""
    __tablename__ = "body_type"
    __table_args__ = {"schema": "vcdb"}

    body_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    body_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    body_style_configs: Mapped[List["BodyStyleConfig"]] = relationship("BodyStyleConfig", back_populates="body_type")

    def __repr__(self) -> str:
        return f"<BodyType {self.body_type_name} ({self.body_type_id})>"


class BodyNumDoors(VCdbBase):
    """BodyNumDoors model representing number of doors on vehicle bodies."""
    __tablename__ = "body_num_doors"
    __table_args__ = {"schema": "vcdb"}

    body_num_doors_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    body_num_doors: Mapped[str] = mapped_column(String(3), nullable=False)

    body_style_configs: Mapped[List["BodyStyleConfig"]] = relationship("BodyStyleConfig",
                                                                       back_populates="body_num_doors")

    def __repr__(self) -> str:
        return f"<BodyNumDoors {self.body_num_doors} ({self.body_num_doors_id})>"


class BodyStyleConfig(VCdbBase):
    """BodyStyleConfig model representing complete body style configurations."""
    __tablename__ = "body_style_config"
    __table_args__ = {"schema": "vcdb"}

    body_style_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                      index=True)
    body_num_doors_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.body_num_doors.body_num_doors_id"),
        nullable=False,
        index=True
    )
    body_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.body_type.body_type_id"),
        nullable=False,
        index=True
    )

    body_num_doors: Mapped["BodyNumDoors"] = relationship("BodyNumDoors", back_populates="body_style_configs")
    body_type: Mapped["BodyType"] = relationship("BodyType", back_populates="body_style_configs")

    def __repr__(self) -> str:
        return f"<BodyStyleConfig {self.body_style_config_id}>"


class VehicleToBodyStyleConfig(VCdbBase):
    """VehicleToBodyStyleConfig model representing the relationship between vehicles and body style configurations."""
    __tablename__ = "vehicle_to_body_style_config"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_body_style_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                                 index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    body_style_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.body_style_config.body_style_config_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToBodyStyleConfig {self.vehicle_to_body_style_config_id}>"


class MfrBodyCode(VCdbBase):
    """MfrBodyCode model representing manufacturer-specific body codes."""
    __tablename__ = "mfr_body_code"
    __table_args__ = {"schema": "vcdb"}

    mfr_body_code_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    mfr_body_code_name: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<MfrBodyCode {self.mfr_body_code_name} ({self.mfr_body_code_id})>"


class VehicleToMfrBodyCode(VCdbBase):
    """VehicleToMfrBodyCode model representing the relationship between vehicles and manufacturer body codes."""
    __tablename__ = "vehicle_to_mfr_body_code"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_mfr_body_code_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                             index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    mfr_body_code_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.mfr_body_code.mfr_body_code_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToMfrBodyCode {self.vehicle_to_mfr_body_code_id}>"


class EngineBlock(VCdbBase):
    """EngineBlock model representing engine block specifications."""
    __tablename__ = "engine_block"
    __table_args__ = {"schema": "vcdb"}

    engine_block_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    liter: Mapped[str] = mapped_column(String(6), nullable=False)
    cc: Mapped[str] = mapped_column(String(8), nullable=False)
    cid: Mapped[str] = mapped_column(String(7), nullable=False)
    cylinders: Mapped[str] = mapped_column(String(2), nullable=False)
    block_type: Mapped[str] = mapped_column(String(2), nullable=False)

    engine_bases: Mapped[List["EngineBase2"]] = relationship("EngineBase2", back_populates="engine_block")
    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="engine_block")

    def __repr__(self) -> str:
        return f"<EngineBlock {self.liter}L {self.cylinders}cyl ({self.engine_block_id})>"


class EngineBoreStroke(VCdbBase):
    """EngineBoreStroke model representing engine bore and stroke specifications."""
    __tablename__ = "engine_bore_stroke"
    __table_args__ = {"schema": "vcdb"}

    engine_bore_stroke_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                       index=True)
    eng_bore_in: Mapped[str] = mapped_column(String(10), nullable=False)
    eng_bore_metric: Mapped[str] = mapped_column(String(10), nullable=False)
    eng_stroke_in: Mapped[str] = mapped_column(String(10), nullable=False)
    eng_stroke_metric: Mapped[str] = mapped_column(String(10), nullable=False)

    engine_bases: Mapped[List["EngineBase2"]] = relationship("EngineBase2", back_populates="engine_bore_stroke")
    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="engine_bore_stroke")

    def __repr__(self) -> str:
        return f"<EngineBoreStroke {self.eng_bore_in}x{self.eng_stroke_in} ({self.engine_bore_stroke_id})>"


class EngineBase(VCdbBase):
    """EngineBase model representing base engine specifications for ACES 3."""
    __tablename__ = "engine_base"
    __table_args__ = {"schema": "vcdb"}

    engine_base_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    liter: Mapped[str] = mapped_column(String(6), nullable=False)
    cc: Mapped[str] = mapped_column(String(8), nullable=False)
    cid: Mapped[str] = mapped_column(String(7), nullable=False)
    cylinders: Mapped[str] = mapped_column(String(2), nullable=False)
    block_type: Mapped[str] = mapped_column(String(2), nullable=False)
    eng_bore_in: Mapped[str] = mapped_column(String(10), nullable=False)
    eng_bore_metric: Mapped[str] = mapped_column(String(10), nullable=False)
    eng_stroke_in: Mapped[str] = mapped_column(String(10), nullable=False)
    eng_stroke_metric: Mapped[str] = mapped_column(String(10), nullable=False)

    def __repr__(self) -> str:
        return f"<EngineBase {self.engine_base_id}>"


class EngineBase2(VCdbBase):
    """EngineBase2 model representing base engine specifications for ACES 4."""
    __tablename__ = "engine_base2"
    __table_args__ = {"schema": "vcdb"}

    engine_base_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    engine_block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_block.engine_block_id"),
        nullable=False,
        index=True
    )
    engine_bore_stroke_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_bore_stroke.engine_bore_stroke_id"),
        nullable=False,
        index=True
    )

    engine_block: Mapped["EngineBlock"] = relationship("EngineBlock", back_populates="engine_bases")
    engine_bore_stroke: Mapped["EngineBoreStroke"] = relationship("EngineBoreStroke", back_populates="engine_bases")
    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="engine_base")

    def __repr__(self) -> str:
        return f"<EngineBase2 {self.engine_base_id}>"


class Aspiration(VCdbBase):
    """Aspiration model representing engine aspiration methods."""
    __tablename__ = "aspiration"
    __table_args__ = {"schema": "vcdb"}

    aspiration_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    aspiration_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="aspiration")

    def __repr__(self) -> str:
        return f"<Aspiration {self.aspiration_name} ({self.aspiration_id})>"


class FuelType(VCdbBase):
    """FuelType model representing types of fuel used in engines."""
    __tablename__ = "fuel_type"
    __table_args__ = {"schema": "vcdb"}

    fuel_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    fuel_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="fuel_type")

    def __repr__(self) -> str:
        return f"<FuelType {self.fuel_type_name} ({self.fuel_type_id})>"


class CylinderHeadType(VCdbBase):
    """CylinderHeadType model representing types of cylinder heads in engines."""
    __tablename__ = "cylinder_head_type"
    __table_args__ = {"schema": "vcdb"}

    cylinder_head_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                       index=True)
    cylinder_head_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="cylinder_head_type")

    def __repr__(self) -> str:
        return f"<CylinderHeadType {self.cylinder_head_type_name} ({self.cylinder_head_type_id})>"


class EngineDesignation(VCdbBase):
    """EngineDesignation model representing engine designation specifications."""
    __tablename__ = "engine_designation"
    __table_args__ = {"schema": "vcdb"}

    engine_designation_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                       index=True)
    engine_designation_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="engine_designation")

    def __repr__(self) -> str:
        return f"<EngineDesignation {self.engine_designation_name} ({self.engine_designation_id})>"


class EngineVIN(VCdbBase):
    """EngineVIN model representing engine VIN codes."""
    __tablename__ = "engine_vin"
    __table_args__ = {"schema": "vcdb"}

    engine_vin_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    engine_vin_name: Mapped[str] = mapped_column(String(5), nullable=False, index=True)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="engine_vin")

    def __repr__(self) -> str:
        return f"<EngineVIN {self.engine_vin_name} ({self.engine_vin_id})>"


class EngineVersion(VCdbBase):
    """EngineVersion model representing engine version specifications."""
    __tablename__ = "engine_version"
    __table_args__ = {"schema": "vcdb"}

    engine_version_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="engine_version")

    def __repr__(self) -> str:
        return f"<EngineVersion {self.engine_version} ({self.engine_version_id})>"


class Valves(VCdbBase):
    """Valves model representing engine valve configurations."""
    __tablename__ = "valves"
    __table_args__ = {"schema": "vcdb"}

    valves_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    valves_per_engine: Mapped[str] = mapped_column(String(3), nullable=False)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="valves")

    def __repr__(self) -> str:
        return f"<Valves {self.valves_per_engine} ({self.valves_id})>"


class FuelDeliveryType(VCdbBase):
    """FuelDeliveryType model representing types of fuel delivery systems."""
    __tablename__ = "fuel_delivery_type"
    __table_args__ = {"schema": "vcdb"}

    fuel_delivery_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                       index=True)
    fuel_delivery_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    fuel_delivery_configs: Mapped[List["FuelDeliveryConfig"]] = relationship("FuelDeliveryConfig",
                                                                             back_populates="fuel_delivery_type")

    def __repr__(self) -> str:
        return f"<FuelDeliveryType {self.fuel_delivery_type_name} ({self.fuel_delivery_type_id})>"


class FuelDeliverySubType(VCdbBase):
    """FuelDeliverySubType model representing subtypes of fuel delivery systems."""
    __tablename__ = "fuel_delivery_sub_type"
    __table_args__ = {"schema": "vcdb"}

    fuel_delivery_sub_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                          index=True)
    fuel_delivery_sub_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    fuel_delivery_configs: Mapped[List["FuelDeliveryConfig"]] = relationship("FuelDeliveryConfig",
                                                                             back_populates="fuel_delivery_sub_type")

    def __repr__(self) -> str:
        return f"<FuelDeliverySubType {self.fuel_delivery_sub_type_name} ({self.fuel_delivery_sub_type_id})>"


class FuelSystemControlType(VCdbBase):
    """FuelSystemControlType model representing types of fuel system control mechanisms."""
    __tablename__ = "fuel_system_control_type"
    __table_args__ = {"schema": "vcdb"}

    fuel_system_control_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                             index=True)
    fuel_system_control_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    fuel_delivery_configs: Mapped[List["FuelDeliveryConfig"]] = relationship("FuelDeliveryConfig",
                                                                             back_populates="fuel_system_control_type")

    def __repr__(self) -> str:
        return f"<FuelSystemControlType {self.fuel_system_control_type_name} ({self.fuel_system_control_type_id})>"


class FuelSystemDesign(VCdbBase):
    """FuelSystemDesign model representing designs of fuel systems."""
    __tablename__ = "fuel_system_design"
    __table_args__ = {"schema": "vcdb"}

    fuel_system_design_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                       index=True)
    fuel_system_design_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    fuel_delivery_configs: Mapped[List["FuelDeliveryConfig"]] = relationship("FuelDeliveryConfig",
                                                                             back_populates="fuel_system_design")

    def __repr__(self) -> str:
        return f"<FuelSystemDesign {self.fuel_system_design_name} ({self.fuel_system_design_id})>"


class FuelDeliveryConfig(VCdbBase):
    """FuelDeliveryConfig model representing complete fuel delivery system configurations."""
    __tablename__ = "fuel_delivery_config"
    __table_args__ = {"schema": "vcdb"}

    fuel_delivery_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                         index=True)
    fuel_delivery_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_delivery_type.fuel_delivery_type_id"),
        nullable=False,
        index=True
    )
    fuel_delivery_sub_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_delivery_sub_type.fuel_delivery_sub_type_id"),
        nullable=False,
        index=True
    )
    fuel_system_control_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_system_control_type.fuel_system_control_type_id"),
        nullable=False,
        index=True
    )
    fuel_system_design_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_system_design.fuel_system_design_id"),
        nullable=False,
        index=True
    )

    fuel_delivery_type: Mapped["FuelDeliveryType"] = relationship("FuelDeliveryType",
                                                                  back_populates="fuel_delivery_configs")
    fuel_delivery_sub_type: Mapped["FuelDeliverySubType"] = relationship("FuelDeliverySubType",
                                                                        back_populates="fuel_delivery_configs")
    fuel_system_control_type: Mapped["FuelSystemControlType"] = relationship("FuelSystemControlType",
                                                                             back_populates="fuel_delivery_configs")
    fuel_system_design: Mapped["FuelSystemDesign"] = relationship("FuelSystemDesign",
                                                                  back_populates="fuel_delivery_configs")
    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="fuel_delivery_config")

    def __repr__(self) -> str:
        return f"<FuelDeliveryConfig {self.fuel_delivery_config_id}>"


class PowerOutput(VCdbBase):
    """PowerOutput model representing engine power output specifications."""
    __tablename__ = "power_output"
    __table_args__ = {"schema": "vcdb"}

    power_output_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    horse_power: Mapped[str] = mapped_column(String(10), nullable=False)
    kilowatt_power: Mapped[str] = mapped_column(String(10), nullable=False)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="power_output")

    def __repr__(self) -> str:
        return f"<PowerOutput {self.horse_power}hp/{self.kilowatt_power}kw ({self.power_output_id})>"


class Mfr(VCdbBase):
    """Mfr model representing manufacturers."""
    __tablename__ = "mfr"
    __table_args__ = {"schema": "vcdb"}

    mfr_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    mfr_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="engine_mfr")
    transmission_configs: Mapped[List["Transmission"]] = relationship("Transmission", back_populates="transmission_mfr")

    def __repr__(self) -> str:
        return f"<Mfr {self.mfr_name} ({self.mfr_id})>"


class IgnitionSystemType(VCdbBase):
    """IgnitionSystemType model representing types of ignition systems."""
    __tablename__ = "ignition_system_type"
    __table_args__ = {"schema": "vcdb"}

    ignition_system_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                         index=True)
    ignition_system_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    engine_configs: Mapped[List["EngineConfig2"]] = relationship("EngineConfig2", back_populates="ignition_system_type")

    def __repr__(self) -> str:
        return f"<IgnitionSystemType {self.ignition_system_type_name} ({self.ignition_system_type_id})>"


class EngineConfig(VCdbBase):
    """EngineConfig model representing complete engine configurations for ACES 3."""
    __tablename__ = "engine_config"
    __table_args__ = {"schema": "vcdb"}

    engine_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    engine_base_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_base.engine_base_id"),
        nullable=False,
        index=True
    )
    engine_designation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_designation.engine_designation_id"),
        nullable=False,
        index=True
    )
    engine_vin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_vin.engine_vin_id"),
        nullable=False,
        index=True
    )
    valves_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.valves.valves_id"),
        nullable=False,
        index=True
    )
    fuel_delivery_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_delivery_config.fuel_delivery_config_id"),
        nullable=False,
        index=True
    )
    aspiration_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.aspiration.aspiration_id"),
        nullable=False,
        index=True
    )
    cylinder_head_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.cylinder_head_type.cylinder_head_type_id"),
        nullable=False,
        index=True
    )
    fuel_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_type.fuel_type_id"),
        nullable=False,
        index=True
    )
    ignition_system_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.ignition_system_type.ignition_system_type_id"),
        nullable=False,
        index=True
    )
    engine_mfr_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.mfr.mfr_id"),
        nullable=False,
        index=True
    )
    engine_version_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_version.engine_version_id"),
        nullable=False,
        index=True
    )
    power_output_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.power_output.power_output_id"),
        nullable=False,
        default=1,
        index=True
    )

    def __repr__(self) -> str:
        return f"<EngineConfig {self.engine_config_id}>"


class EngineConfig2(VCdbBase):
    """EngineConfig2 model representing complete engine configurations for ACES 4."""
    __tablename__ = "engine_config2"
    __table_args__ = {"schema": "vcdb"}

    engine_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    engine_base_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_base2.engine_base_id"),
        nullable=False,
        index=True
    )
    engine_block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_block.engine_block_id"),
        nullable=False,
        index=True
    )
    engine_bore_stroke_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_bore_stroke.engine_bore_stroke_id"),
        nullable=False,
        index=True
    )
    engine_designation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_designation.engine_designation_id"),
        nullable=False,
        index=True
    )
    engine_vin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_vin.engine_vin_id"),
        nullable=False,
        index=True
    )
    valves_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.valves.valves_id"),
        nullable=False,
        index=True
    )
    fuel_delivery_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_delivery_config.fuel_delivery_config_id"),
        nullable=False,
        index=True
    )
    aspiration_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.aspiration.aspiration_id"),
        nullable=False,
        index=True
    )
    cylinder_head_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.cylinder_head_type.cylinder_head_type_id"),
        nullable=False,
        index=True
    )
    fuel_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_type.fuel_type_id"),
        nullable=False,
        index=True
    )
    ignition_system_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.ignition_system_type.ignition_system_type_id"),
        nullable=False,
        index=True
    )
    engine_mfr_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.mfr.mfr_id"),
        nullable=False,
        index=True
    )
    engine_version_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_version.engine_version_id"),
        nullable=False,
        index=True
    )
    power_output_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.power_output.power_output_id"),
        nullable=False,
        default=1,
        index=True
    )

    engine_base: Mapped["EngineBase2"] = relationship("EngineBase2", back_populates="engine_configs")
    engine_block: Mapped["EngineBlock"] = relationship("EngineBlock", back_populates="engine_configs")
    engine_bore_stroke: Mapped["EngineBoreStroke"] = relationship("EngineBoreStroke", back_populates="engine_configs")
    engine_designation: Mapped["EngineDesignation"] = relationship("EngineDesignation", back_populates="engine_configs")
    engine_vin: Mapped["EngineVIN"] = relationship("EngineVIN", back_populates="engine_configs")
    valves: Mapped["Valves"] = relationship("Valves", back_populates="engine_configs")
    fuel_delivery_config: Mapped["FuelDeliveryConfig"] = relationship("FuelDeliveryConfig",
                                                                      back_populates="engine_configs")
    aspiration: Mapped["Aspiration"] = relationship("Aspiration", back_populates="engine_configs")
    cylinder_head_type: Mapped["CylinderHeadType"] = relationship("CylinderHeadType", back_populates="engine_configs")
    fuel_type: Mapped["FuelType"] = relationship("FuelType", back_populates="engine_configs")
    ignition_system_type: Mapped["IgnitionSystemType"] = relationship("IgnitionSystemType",
                                                                      back_populates="engine_configs")
    engine_mfr: Mapped["Mfr"] = relationship("Mfr", back_populates="engine_configs")
    engine_version: Mapped["EngineVersion"] = relationship("EngineVersion", back_populates="engine_configs")
    power_output: Mapped["PowerOutput"] = relationship("PowerOutput", back_populates="engine_configs")

    def __repr__(self) -> str:
        return f"<EngineConfig2 {self.engine_config_id}>"


class VehicleToEngineConfig(VCdbBase):
    """VehicleToEngineConfig model representing the relationship between vehicles and engine configurations."""
    __tablename__ = "vehicle_to_engine_config"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_engine_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                             index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    engine_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_config2.engine_config_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToEngineConfig {self.vehicle_to_engine_config_id}>"


class SpringType(VCdbBase):
    """SpringType model representing types of vehicle springs."""
    __tablename__ = "spring_type"
    __table_args__ = {"schema": "vcdb"}

    spring_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    spring_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    front_spring_configs: Mapped[List["SpringTypeConfig"]] = relationship(
        "SpringTypeConfig",
        primaryjoin="SpringType.spring_type_id == SpringTypeConfig.front_spring_type_id",
        back_populates="front_spring_type"
    )
    rear_spring_configs: Mapped[List["SpringTypeConfig"]] = relationship(
        "SpringTypeConfig",
        primaryjoin="SpringType.spring_type_id == SpringTypeConfig.rear_spring_type_id",
        back_populates="rear_spring_type"
    )

    def __repr__(self) -> str:
        return f"<SpringType {self.spring_type_name} ({self.spring_type_id})>"


class SpringTypeConfig(VCdbBase):
    """SpringTypeConfig model representing complete spring type configurations."""
    __tablename__ = "spring_type_config"
    __table_args__ = {"schema": "vcdb"}

    spring_type_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                       index=True)
    front_spring_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.spring_type.spring_type_id"),
        nullable=False,
        index=True
    )
    rear_spring_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.spring_type.spring_type_id"),
        nullable=False,
        index=True
    )

    front_spring_type: Mapped["SpringType"] = relationship(
        "SpringType",
        primaryjoin="SpringTypeConfig.front_spring_type_id == SpringType.spring_type_id",
        back_populates="front_spring_configs"
    )
    rear_spring_type: Mapped["SpringType"] = relationship(
        "SpringType",
        primaryjoin="SpringTypeConfig.rear_spring_type_id == SpringType.spring_type_id",
        back_populates="rear_spring_configs"
    )

    def __repr__(self) -> str:
        return f"<SpringTypeConfig {self.spring_type_config_id}>"


class VehicleToSpringTypeConfig(VCdbBase):
    """VehicleToSpringTypeConfig model representing the relationship between vehicles and spring type configurations."""
    __tablename__ = "vehicle_to_spring_type_config"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_spring_type_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False,
                                                                  unique=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    spring_type_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.spring_type_config.spring_type_config_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToSpringTypeConfig {self.vehicle_to_spring_type_config_id}>"


class SteeringType(VCdbBase):
    """SteeringType model representing types of steering systems."""
    __tablename__ = "steering_type"
    __table_args__ = {"schema": "vcdb"}

    steering_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    steering_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    steering_configs: Mapped[List["SteeringConfig"]] = relationship("SteeringConfig", back_populates="steering_type")

    def __repr__(self) -> str:
        return f"<SteeringType {self.steering_type_name} ({self.steering_type_id})>"


class SteeringSystem(VCdbBase):
    """SteeringSystem model representing steering system configurations."""
    __tablename__ = "steering_system"
    __table_args__ = {"schema": "vcdb"}

    steering_system_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    steering_system_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    steering_configs: Mapped[List["SteeringConfig"]] = relationship("SteeringConfig", back_populates="steering_system")

    def __repr__(self) -> str:
        return f"<SteeringSystem {self.steering_system_name} ({self.steering_system_id})>"


class SteeringConfig(VCdbBase):
    """SteeringConfig model representing complete steering configurations."""
    __tablename__ = "steering_config"
    __table_args__ = {"schema": "vcdb"}

    steering_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    steering_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.steering_type.steering_type_id"),
        nullable=False,
        index=True
    )
    steering_system_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.steering_system.steering_system_id"),
        nullable=False,
        index=True
    )

    steering_type: Mapped["SteeringType"] = relationship("SteeringType", back_populates="steering_configs")
    steering_system: Mapped["SteeringSystem"] = relationship("SteeringSystem", back_populates="steering_configs")

    def __repr__(self) -> str:
        return f"<SteeringConfig {self.steering_config_id}>"


class VehicleToSteeringConfig(VCdbBase):
    """VehicleToSteeringConfig model representing the relationship between vehicles and steering configurations."""
    __tablename__ = "vehicle_to_steering_config"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_steering_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                               index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    steering_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.steering_config.steering_config_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToSteeringConfig {self.vehicle_to_steering_config_id}>"


class TransmissionType(VCdbBase):
    """TransmissionType model representing types of transmissions."""
    __tablename__ = "transmission_type"
    __table_args__ = {"schema": "vcdb"}

    transmission_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                      index=True)
    transmission_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    transmission_bases: Mapped[List["TransmissionBase"]] = relationship("TransmissionBase",
                                                                        back_populates="transmission_type")

    def __repr__(self) -> str:
        return f"<TransmissionType {self.transmission_type_name} ({self.transmission_type_id})>"


class TransmissionNumSpeeds(VCdbBase):
    """TransmissionNumSpeeds model representing number of speeds in transmissions."""
    __tablename__ = "transmission_num_speeds"
    __table_args__ = {"schema": "vcdb"}

    transmission_num_speeds_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                            index=True)
    transmission_num_speeds: Mapped[str] = mapped_column(String(3), nullable=False, index=True)

    transmission_bases: Mapped[List["TransmissionBase"]] = relationship("TransmissionBase",
                                                                        back_populates="transmission_num_speeds")

    def __repr__(self) -> str:
        return f"<TransmissionNumSpeeds {self.transmission_num_speeds} ({self.transmission_num_speeds_id})>"


class TransmissionControlType(VCdbBase):
    """TransmissionControlType model representing types of transmission control systems."""
    __tablename__ = "transmission_control_type"
    __table_args__ = {"schema": "vcdb"}

    transmission_control_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                              index=True)
    transmission_control_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    transmission_bases: Mapped[List["TransmissionBase"]] = relationship("TransmissionBase",
                                                                        back_populates="transmission_control_type")

    def __repr__(self) -> str:
        return f"<TransmissionControlType {self.transmission_control_type_name} ({self.transmission_control_type_id})>"


class TransmissionBase(VCdbBase):
    """TransmissionBase model representing base transmission configurations."""
    __tablename__ = "transmission_base"
    __table_args__ = {"schema": "vcdb"}

    transmission_base_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                      index=True)
    transmission_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.transmission_type.transmission_type_id"),
        nullable=False,
        index=True
    )
    transmission_num_speeds_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.transmission_num_speeds.transmission_num_speeds_id"),
        nullable=False,
        index=True
    )
    transmission_control_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.transmission_control_type.transmission_control_type_id"),
        nullable=False,
        index=True
    )

    transmission_type: Mapped["TransmissionType"] = relationship("TransmissionType",
                                                                 back_populates="transmission_bases")
    transmission_num_speeds: Mapped["TransmissionNumSpeeds"] = relationship("TransmissionNumSpeeds",
                                                                            back_populates="transmission_bases")
    transmission_control_type: Mapped["TransmissionControlType"] = relationship("TransmissionControlType",
                                                                                back_populates="transmission_bases")
    transmissions: Mapped[List["Transmission"]] = relationship("Transmission", back_populates="transmission_base")

    def __repr__(self) -> str:
        return f"<TransmissionBase {self.transmission_base_id}>"


class TransmissionMfrCode(VCdbBase):
    """TransmissionMfrCode model representing manufacturer codes for transmissions."""
    __tablename__ = "transmission_mfr_code"
    __table_args__ = {"schema": "vcdb"}

    transmission_mfr_code_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                          index=True)
    transmission_mfr_code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    transmissions: Mapped[List["Transmission"]] = relationship("Transmission", back_populates="transmission_mfr_code")

    def __repr__(self) -> str:
        return f"<TransmissionMfrCode {self.transmission_mfr_code} ({self.transmission_mfr_code_id})>"


class ElecControlled(VCdbBase):
    """ElecControlled model representing electrically controlled components."""
    __tablename__ = "elec_controlled"
    __table_args__ = {"schema": "vcdb"}

    elec_controlled_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    elec_controlled: Mapped[str] = mapped_column(String(3), nullable=False, index=True)

    transmissions: Mapped[List["Transmission"]] = relationship("Transmission", back_populates="elec_controlled")

    def __repr__(self) -> str:
        return f"<ElecControlled {self.elec_controlled} ({self.elec_controlled_id})>"


class Transmission(VCdbBase):
    """Transmission model representing complete transmission configurations."""
    __tablename__ = "transmission"
    __table_args__ = {"schema": "vcdb"}

    transmission_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    transmission_base_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.transmission_base.transmission_base_id"),
        nullable=False,
        index=True
    )
    transmission_mfr_code_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.transmission_mfr_code.transmission_mfr_code_id"),
        nullable=False,
        index=True
    )
    transmission_elec_controlled_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.elec_controlled.elec_controlled_id"),
        nullable=False,
        index=True
    )
    transmission_mfr_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.mfr.mfr_id"),
        nullable=False,
        index=True
    )

    transmission_base: Mapped["TransmissionBase"] = relationship("TransmissionBase", back_populates="transmissions")
    transmission_mfr_code: Mapped["TransmissionMfrCode"] = relationship("TransmissionMfrCode",
                                                                        back_populates="transmissions")
    elec_controlled: Mapped["ElecControlled"] = relationship("ElecControlled", back_populates="transmissions")
    transmission_mfr: Mapped["Mfr"] = relationship("Mfr", back_populates="transmission_configs")

    def __repr__(self) -> str:
        return f"<Transmission {self.transmission_id}>"


class VehicleToTransmission(VCdbBase):
    """VehicleToTransmission model representing the relationship between vehicles and transmissions."""
    __tablename__ = "vehicle_to_transmission"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_transmission_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                            index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    transmission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.transmission.transmission_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToTransmission {self.vehicle_to_transmission_id}>"


class WheelBase(VCdbBase):
    """WheelBase model representing wheel base specifications."""
    __tablename__ = "wheel_base"
    __table_args__ = {"schema": "vcdb"}

    wheel_base_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    wheel_base: Mapped[str] = mapped_column(String(10), nullable=False)
    wheel_base_metric: Mapped[str] = mapped_column(String(10), nullable=False)

    def __repr__(self) -> str:
        return f"<WheelBase {self.wheel_base} ({self.wheel_base_id})>"


class VehicleToWheelBase(VCdbBase):
    """VehicleToWheelBase model representing the relationship between vehicles and wheel bases."""
    __tablename__ = "vehicle_to_wheel_base"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_wheel_base_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                          index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    wheel_base_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.wheel_base.wheel_base_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToWheelBase {self.vehicle_to_wheel_base_id}>"


class Class(VCdbBase):
    """Class model representing vehicle classifications."""
    __tablename__ = "class"
    __table_args__ = {"schema": "vcdb"}

    class_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    class_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", secondary="vcdb.vehicle_to_class",
                                                     back_populates="classes")

    def __repr__(self) -> str:
        return f"<Class {self.class_name} ({self.class_id})>"


class VehicleToClass(VCdbBase):
    """VehicleToClass model representing the relationship between vehicles and classes."""
    __tablename__ = "vehicle_to_class"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_class_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    class_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.class.class_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleToClass {self.vehicle_to_class_id}>"


class VehicleToBodyConfig(VCdbBase):
    """VehicleToBodyConfig model representing the relationship between vehicles and body configurations."""
    __tablename__ = "vehicle_to_body_config"
    __table_args__ = {"schema": "vcdb"}

    vehicle_to_body_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                           index=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False,
        index=True
    )
    wheel_base_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.wheel_base.wheel_base_id"),
        nullable=False,
        index=True
    )
    bed_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.bed_config.bed_config_id"),
        nullable=False,
        index=True
    )
    body_style_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.body_style_config.body_style_config_id"),
        nullable=False,
        index=True
    )
    mfr_body_code_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.mfr_body_code.mfr_body_code_id"),
        nullable=False,
        index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="body_configs")

    def __repr__(self) -> str:
        return f"<VehicleToBodyConfig {self.vehicle_to_body_config_id}>"


class ChangeAttributeStates(VCdbBase):
    """ChangeAttributeStates model representing states of attribute changes."""
    __tablename__ = "change_attribute_states"
    __table_args__ = {"schema": "vcdb"}

    change_attribute_state_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                           index=True)
    change_attribute_state: Mapped[str] = mapped_column(String(255), nullable=False)

    change_details: Mapped[List["ChangeDetails"]] = relationship("ChangeDetails",
                                                                 back_populates="change_attribute_state")

    def __repr__(self) -> str:
        return f"<ChangeAttributeStates {self.change_attribute_state} ({self.change_attribute_state_id})>"


class ChangeReasons(VCdbBase):
    """ChangeReasons model representing reasons for changes."""
    __tablename__ = "change_reasons"
    __table_args__ = {"schema": "vcdb"}

    change_reason_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    change_reason: Mapped[str] = mapped_column(String(255), nullable=False)

    changes: Mapped[List["Changes"]] = relationship("Changes", back_populates="change_reason")

    def __repr__(self) -> str:
        return f"<ChangeReasons {self.change_reason} ({self.change_reason_id})>"


class ChangeTableNames(VCdbBase):
    """ChangeTableNames model representing names of tables that can be changed."""
    __tablename__ = "change_table_names"
    __table_args__ = {"schema": "vcdb"}

    table_name_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    change_details: Mapped[List["ChangeDetails"]] = relationship("ChangeDetails", back_populates="table_name")

    def __repr__(self) -> str:
        return f"<ChangeTableNames {self.table_name} ({self.table_name_id})>"


class Changes(VCdbBase):
    """Changes model representing change records."""
    __tablename__ = "changes"
    __table_args__ = {"schema": "vcdb"}

    change_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    request_id: Mapped[int] = mapped_column(Integer, nullable=False)
    change_reason_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.change_reasons.change_reason_id"),
        nullable=False,
        index=True
    )
    rev_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    change_reason: Mapped["ChangeReasons"] = relationship("ChangeReasons", back_populates="changes")
    change_details: Mapped[List["ChangeDetails"]] = relationship("ChangeDetails", back_populates="change")

    def __repr__(self) -> str:
        return f"<Changes {self.change_id}>"


class ChangeDetails(VCdbBase):
    """ChangeDetails model representing details of changes."""
    __tablename__ = "change_details"
    __table_args__ = {"schema": "vcdb"}

    change_detail_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    change_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.changes.change_id"),
        nullable=False,
        index=True
    )
    change_attribute_state_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.change_attribute_states.change_attribute_state_id"),
        nullable=False,
        index=True
    )
    table_name_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.change_table_names.table_name_id"),
        nullable=False,
        index=True
    )
    primary_key_column_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    primary_key_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_key_after: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    column_value_before: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    column_value_after: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    change: Mapped["Changes"] = relationship("Changes", back_populates="change_details")
    change_attribute_state: Mapped["ChangeAttributeStates"] = relationship("ChangeAttributeStates",
                                                                           back_populates="change_details")
    table_name: Mapped["ChangeTableNames"] = relationship("ChangeTableNames", back_populates="change_details")

    def __repr__(self) -> str:
        return f"<ChangeDetails {self.change_detail_id}>"


class Version(VCdbBase):
    """Version model representing VCdb version information."""
    __tablename__ = "version"
    __table_args__ = {"schema": "vcdb"}

    version_date: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Version {self.version_date}>"


class VCdbChanges(VCdbBase):
    """VCdbChanges model representing changes to the VCdb."""
    __tablename__ = "vcdb_changes"
    __table_args__ = {"schema": "vcdb"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    version_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    table_name: Mapped[str] = mapped_column(String(30), nullable=False)
    action: Mapped[str] = mapped_column(String(1), nullable=False)

    def __repr__(self) -> str:
        return f"<VCdbChanges {self.table_name} {self.id} {self.action}>"


class AttachmentType(VCdbBase):
    """AttachmentType model representing types of attachments."""
    __tablename__ = "attachment_type"
    __table_args__ = {"schema": "vcdb"}

    attachment_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    attachment_type_name: Mapped[str] = mapped_column(String(20), nullable=False)

    attachments: Mapped[List["Attachment"]] = relationship("Attachment", back_populates="attachment_type")

    def __repr__(self) -> str:
        return f"<AttachmentType {self.attachment_type_name} ({self.attachment_type_id})>"


class Attachment(VCdbBase):
    """Attachment model representing file attachments."""
    __tablename__ = "attachment"
    __table_args__ = {"schema": "vcdb"}

    attachment_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    attachment_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.attachment_type.attachment_type_id"),
        nullable=False,
        index=True
    )
    attachment_file_name: Mapped[str] = mapped_column(String(50), nullable=False)
    attachment_url: Mapped[str] = mapped_column(String(100), nullable=False)
    attachment_description: Mapped[str] = mapped_column(String(50), nullable=False)

    attachment_type: Mapped["AttachmentType"] = relationship("AttachmentType", back_populates="attachments")
    language_translation_attachments: Mapped[List["LanguageTranslationAttachment"]] = relationship(
        "LanguageTranslationAttachment",
        back_populates="attachment"
    )

    def __repr__(self) -> str:
        return f"<Attachment {self.attachment_file_name} ({self.attachment_id})>"


class EnglishPhrase(VCdbBase):
    """EnglishPhrase model representing English phrases for translation."""
    __tablename__ = "english_phrase"
    __table_args__ = {"schema": "vcdb"}

    english_phrase_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    english_phrase: Mapped[str] = mapped_column(String(100), nullable=False)

    language_translations: Mapped[List["LanguageTranslation"]] = relationship(
        "LanguageTranslation",
        back_populates="english_phrase"
    )

    def __repr__(self) -> str:
        return f"<EnglishPhrase {self.english_phrase} ({self.english_phrase_id})>"


class Language(VCdbBase):
    """Language model representing languages for translation."""
    __tablename__ = "language"
    __table_args__ = {"schema": "vcdb"}

    language_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True, index=True)
    language_name: Mapped[str] = mapped_column(String(20), nullable=False)
    dialect_name: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    language_translations: Mapped[List["LanguageTranslation"]] = relationship(
        "LanguageTranslation",
        back_populates="language"
    )

    def __repr__(self) -> str:
        return f"<Language {self.language_name} ({self.language_id})>"


class LanguageTranslation(VCdbBase):
    """LanguageTranslation model representing translations of phrases into different languages."""
    __tablename__ = "language_translation"
    __table_args__ = {"schema": "vcdb"}

    language_translation_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True,
                                                         index=True)
    english_phrase_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.english_phrase.english_phrase_id"),
        nullable=False,
        index=True
    )
    language_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.language.language_id"),
        nullable=False,
        index=True
    )
    translation: Mapped[str] = mapped_column(String(150), nullable=False)

    english_phrase: Mapped["EnglishPhrase"] = relationship("EnglishPhrase", back_populates="language_translations")
    language: Mapped["Language"] = relationship("Language", back_populates="language_translations")
    language_translation_attachments: Mapped[List["LanguageTranslationAttachment"]] = relationship(
        "LanguageTranslationAttachment",
        back_populates="language_translation"
    )

    def __repr__(self) -> str:
        return f"<LanguageTranslation {self.language_translation_id}>"


class LanguageTranslationAttachment(VCdbBase):
    """LanguageTranslationAttachment model representing attachments for language translations."""
    __tablename__ = "language_translation_attachment"
    __table_args__ = {"schema": "vcdb"}

    language_translation_attachment_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False,
                                                                    unique=True, index=True)
    language_translation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.language_translation.language_translation_id"),
        nullable=False,
        index=True
    )
    attachment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.attachment.attachment_id"),
        nullable=False,
        index=True
    )

    language_translation: Mapped["LanguageTranslation"] = relationship(
        "LanguageTranslation",
        back_populates="language_translation_attachments"
    )
    attachment: Mapped["Attachment"] = relationship("Attachment", back_populates="language_translation_attachments")

    def __repr__(self) -> str:
        return f"<LanguageTranslationAttachment {self.language_translation_attachment_id}>"