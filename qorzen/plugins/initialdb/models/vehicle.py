from __future__ import annotations

"""
Database models for vehicle component information.

This module provides a clean, consolidated set of SQLAlchemy models for accessing
vehicle component database (VCdb) information, with simplified relationships and
standardized base classes.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, cast
import uuid

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Table,
    UniqueConstraint, JSON, Text, func, select
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship, declarative_base,
    DeclarativeBase, Session
)


# Base class for all models
class Base(DeclarativeBase):
    """Base class for all database models with common functionality."""

    __abstract__ = True
    __table_args__ = {"schema": "vcdb"}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary containing model attributes.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result


# Create type alias for model to simplify annotations
T = TypeVar('T', bound=Base)


# Vehicle-related models
class Year(Base):
    """Year model representing vehicle years."""

    __tablename__ = "year"

    year_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Relationships
    base_vehicles = relationship("BaseVehicle", back_populates="year")

    def __repr__(self) -> str:
        return f"<Year {self.year_id}>"


class Make(Base):
    """Make model representing vehicle manufacturers."""

    __tablename__ = "make"

    make_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    make_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Relationships
    base_vehicles = relationship("BaseVehicle", back_populates="make")

    def __repr__(self) -> str:
        return f"<Make {self.make_name} ({self.make_id})>"


class VehicleType(Base):
    """VehicleType model representing types of vehicles."""

    __tablename__ = "vehicle_type"

    vehicle_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vehicle_type_group_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle_type_group.vehicle_type_group_id"),
        nullable=True
    )

    # Relationships
    models = relationship("Model", back_populates="vehicle_type")
    vehicle_type_group = relationship("VehicleTypeGroup", back_populates="vehicle_types")

    def __repr__(self) -> str:
        return f"<VehicleType {self.vehicle_type_name} ({self.vehicle_type_id})>"


class VehicleTypeGroup(Base):
    """VehicleTypeGroup model representing groups of vehicle types."""

    __tablename__ = "vehicle_type_group"

    vehicle_type_group_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_type_group_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Relationships
    vehicle_types = relationship("VehicleType", back_populates="vehicle_type_group")

    def __repr__(self) -> str:
        return f"<VehicleTypeGroup {self.vehicle_type_group_name} ({self.vehicle_type_group_id})>"


class Model(Base):
    """Model representing vehicle models."""

    __tablename__ = "model"

    model_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vehicle_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle_type.vehicle_type_id"),
        nullable=False
    )

    # Relationships
    base_vehicles = relationship("BaseVehicle", back_populates="model")
    vehicle_type = relationship("VehicleType", back_populates="models")

    def __repr__(self) -> str:
        return f"<Model {self.model_name} ({self.model_id})>"


class SubModel(Base):
    """SubModel representing vehicle sub-models."""

    __tablename__ = "sub_model"

    sub_model_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sub_model_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="sub_model")

    def __repr__(self) -> str:
        return f"<SubModel {self.sub_model_name} ({self.sub_model_id})>"


class Region(Base):
    """Region representing geographical regions for vehicles."""

    __tablename__ = "region"

    region_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    region_abbr: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("vcdb.region.region_id"),
        nullable=True
    )

    # Relationships
    parent = relationship("Region", remote_side=[region_id], back_populates="children")
    children = relationship("Region", back_populates="parent")
    vehicles = relationship("Vehicle", back_populates="region")

    def __repr__(self) -> str:
        return f"<Region {self.region_name} ({self.region_id})>"


class BaseVehicle(Base):
    """
    BaseVehicle representing core vehicle information (year, make, model).
    """

    __tablename__ = "base_vehicle"

    base_vehicle_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.year.year_id"),
        nullable=False
    )
    make_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.make.make_id"),
        nullable=False
    )
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.model.model_id"),
        nullable=False
    )

    # Relationships
    year = relationship("Year", back_populates="base_vehicles")
    make = relationship("Make", back_populates="base_vehicles")
    model = relationship("Model", back_populates="base_vehicles")
    vehicles = relationship("Vehicle", back_populates="base_vehicle")

    def __repr__(self) -> str:
        return f"<BaseVehicle {self.base_vehicle_id}>"


class PublicationStage(Base):
    """PublicationStage representing stages of vehicle data publication."""

    __tablename__ = "publication_stage"

    publication_stage_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    publication_stage_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="publication_stage")

    def __repr__(self) -> str:
        return f"<PublicationStage {self.publication_stage_name} ({self.publication_stage_id})>"


# Engine-related models
class EngineBlock(Base):
    """EngineBlock representing engine block data."""

    __tablename__ = "engine_block"

    engine_block_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    liter: Mapped[str] = mapped_column(String(6), nullable=False)
    cc: Mapped[str] = mapped_column(String(8), nullable=False)
    cid: Mapped[str] = mapped_column(String(7), nullable=False)
    cylinders: Mapped[str] = mapped_column(String(2), nullable=False)
    block_type: Mapped[str] = mapped_column(String(2), nullable=False)

    # Relationships
    engine_configs = relationship("EngineConfig", back_populates="engine_block")

    def __repr__(self) -> str:
        return f"<EngineBlock {self.liter}L {self.cylinders}cyl ({self.engine_block_id})>"


class FuelType(Base):
    """FuelType representing types of fuel."""

    __tablename__ = "fuel_type"

    fuel_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fuel_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    # Relationships
    engine_configs = relationship("EngineConfig", back_populates="fuel_type")

    def __repr__(self) -> str:
        return f"<FuelType {self.fuel_type_name} ({self.fuel_type_id})>"


class Aspiration(Base):
    """Aspiration representing engine aspiration types."""

    __tablename__ = "aspiration"

    aspiration_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aspiration_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    # Relationships
    engine_configs = relationship("EngineConfig", back_populates="aspiration")

    def __repr__(self) -> str:
        return f"<Aspiration {self.aspiration_name} ({self.aspiration_id})>"


class EngineConfig(Base):
    """
    EngineConfig representing complete engine configuration.

    This is a simplified version of the original EngineConfig2 model.
    """

    __tablename__ = "engine_config2"

    engine_config_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engine_block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_block.engine_block_id"),
        nullable=False
    )
    fuel_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.fuel_type.fuel_type_id"),
        nullable=False
    )
    aspiration_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.aspiration.aspiration_id"),
        nullable=False
    )

    # Relationships
    engine_block = relationship("EngineBlock", back_populates="engine_configs")
    fuel_type = relationship("FuelType", back_populates="engine_configs")
    aspiration = relationship("Aspiration", back_populates="engine_configs")
    vehicles = relationship(
        "Vehicle",
        secondary="vcdb.vehicle_to_engine_config",
        back_populates="engine_configs"
    )

    def __repr__(self) -> str:
        return f"<EngineConfig {self.engine_config_id}>"


# Transmission-related models
class TransmissionType(Base):
    """TransmissionType representing types of transmissions."""

    __tablename__ = "transmission_type"

    transmission_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transmission_type_name: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<TransmissionType {self.transmission_type_name} ({self.transmission_type_id})>"


class Transmission(Base):
    """Transmission representing complete transmission configurations."""

    __tablename__ = "transmission"

    transmission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Additional fields would be here, simplified for this example

    # Relationships
    vehicles = relationship(
        "Vehicle",
        secondary="vcdb.vehicle_to_transmission",
        back_populates="transmissions"
    )

    def __repr__(self) -> str:
        return f"<Transmission {self.transmission_id}>"


# Body-related models
class BodyType(Base):
    """BodyType representing types of vehicle bodies."""

    __tablename__ = "body_type"

    body_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body_type_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<BodyType {self.body_type_name} ({self.body_type_id})>"


class BodyStyleConfig(Base):
    """BodyStyleConfig representing body style configurations."""

    __tablename__ = "body_style_config"

    body_style_config_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.body_type.body_type_id"),
        nullable=False
    )
    # Additional fields would be here, simplified for this example

    # Relationships
    vehicles = relationship(
        "Vehicle",
        secondary="vcdb.vehicle_to_body_style_config",
        back_populates="body_style_configs"
    )

    def __repr__(self) -> str:
        return f"<BodyStyleConfig {self.body_style_config_id}>"


# Main Vehicle model
class Vehicle(Base):
    """
    Vehicle representing a complete vehicle configuration.

    This model is the central entity that ties together all vehicle components
    and specifications.
    """

    __tablename__ = "vehicle"

    vehicle_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.base_vehicle.base_vehicle_id"),
        nullable=False
    )
    sub_model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.sub_model.sub_model_id"),
        nullable=False
    )
    region_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.region.region_id"),
        nullable=False
    )
    publication_stage_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.publication_stage.publication_stage_id"),
        nullable=False,
        default=4
    )
    source: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    publication_stage_source: Mapped[str] = mapped_column(String(100), nullable=False)
    publication_stage_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    # Relationships
    base_vehicle = relationship("BaseVehicle", back_populates="vehicles")
    sub_model = relationship("SubModel", back_populates="vehicles")
    region = relationship("Region", back_populates="vehicles")
    publication_stage = relationship("PublicationStage", back_populates="vehicles")

    # Many-to-many relationships
    engine_configs = relationship(
        "EngineConfig",
        secondary="vcdb.vehicle_to_engine_config",
        back_populates="vehicles"
    )
    transmissions = relationship(
        "Transmission",
        secondary="vcdb.vehicle_to_transmission",
        back_populates="vehicles"
    )
    body_style_configs = relationship(
        "BodyStyleConfig",
        secondary="vcdb.vehicle_to_body_style_config",
        back_populates="vehicles"
    )

    @property
    def make(self) -> Make:
        """Get the vehicle's make."""
        return self.base_vehicle.make

    @property
    def model(self) -> Model:
        """Get the vehicle's model."""
        return self.base_vehicle.model

    @property
    def year(self) -> int:
        """Get the vehicle's year."""
        return self.base_vehicle.year.year_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert vehicle to dictionary including nested attributes."""
        result = super().to_dict()

        # Add nested attributes
        if self.base_vehicle:
            result["year"] = self.base_vehicle.year.year_id if self.base_vehicle.year else None
            result["make"] = self.base_vehicle.make.make_name if self.base_vehicle.make else None
            result["model"] = self.base_vehicle.model.model_name if self.base_vehicle.model else None

        if self.sub_model:
            result["sub_model"] = self.sub_model.sub_model_name

        if self.region:
            result["region"] = self.region.region_name

        # Add engine info from the first engine config if available
        if self.engine_configs and len(self.engine_configs) > 0:
            engine = self.engine_configs[0]
            if engine.engine_block:
                result["engine_liter"] = engine.engine_block.liter
                result["engine_cylinders"] = engine.engine_block.cylinders

            if engine.fuel_type:
                result["fuel_type"] = engine.fuel_type.fuel_type_name

            if engine.aspiration:
                result["aspiration"] = engine.aspiration.aspiration_name

        return result

    def __repr__(self) -> str:
        return f"<Vehicle {self.vehicle_id}>"


# Join tables
class VehicleToEngineConfig(Base):
    """Join table between Vehicle and EngineConfig."""

    __tablename__ = "vehicle_to_engine_config"

    vehicle_to_engine_config_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False
    )
    engine_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.engine_config2.engine_config_id"),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<VehicleToEngineConfig {self.vehicle_to_engine_config_id}>"


class VehicleToTransmission(Base):
    """Join table between Vehicle and Transmission."""

    __tablename__ = "vehicle_to_transmission"

    vehicle_to_transmission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False
    )
    transmission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.transmission.transmission_id"),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<VehicleToTransmission {self.vehicle_to_transmission_id}>"


class VehicleToBodyStyleConfig(Base):
    """Join table between Vehicle and BodyStyleConfig."""

    __tablename__ = "vehicle_to_body_style_config"

    vehicle_to_body_style_config_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.vehicle.vehicle_id"),
        nullable=False
    )
    body_style_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vcdb.body_style_config.body_style_config_id"),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<VehicleToBodyStyleConfig {self.vehicle_to_body_style_config_id}>"


# Custom exceptions
class DatabaseConnectionError(Exception):
    """Exception raised for database connection issues."""
    pass


class QueryExecutionError(Exception):
    """Exception raised for query execution issues."""
    pass


class InvalidFilterError(Exception):
    """Exception raised for invalid filter specifications."""
    pass