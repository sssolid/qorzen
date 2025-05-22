# Module: plugins.vcdb_explorer.code.models

**Path:** `plugins/vcdb_explorer/code/models.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from sqlalchemy.sql import func
import uuid
```

## Global Variables
```python
VCdbBase = VCdbBase = declarative_base()
```

## Classes

| Class | Description |
| --- | --- |
| `Abbreviation` |  |
| `Aspiration` |  |
| `Attachment` |  |
| `AttachmentType` |  |
| `BaseVehicle` |  |
| `BedConfig` |  |
| `BedLength` |  |
| `BedType` |  |
| `BodyNumDoors` |  |
| `BodyStyleConfig` |  |
| `BodyType` |  |
| `BrakeABS` |  |
| `BrakeConfig` |  |
| `BrakeSystem` |  |
| `BrakeType` |  |
| `ChangeAttributeStates` |  |
| `ChangeDetails` |  |
| `ChangeReasons` |  |
| `ChangeTableNames` |  |
| `Changes` |  |
| `Class` |  |
| `ConfigurationError` |  |
| `CylinderHeadType` |  |
| `DatabaseConnectionError` |  |
| `DriveType` |  |
| `ElecControlled` |  |
| `EngineBase` |  |
| `EngineBase2` |  |
| `EngineBlock` |  |
| `EngineBoreStroke` |  |
| `EngineConfig` |  |
| `EngineConfig2` |  |
| `EngineDesignation` |  |
| `EngineVIN` |  |
| `EngineVersion` |  |
| `EnglishPhrase` |  |
| `ExportError` |  |
| `FuelDeliveryConfig` |  |
| `FuelDeliverySubType` |  |
| `FuelDeliveryType` |  |
| `FuelSystemControlType` |  |
| `FuelSystemDesign` |  |
| `FuelType` |  |
| `IgnitionSystemType` |  |
| `InvalidFilterError` |  |
| `Language` |  |
| `LanguageTranslation` |  |
| `LanguageTranslationAttachment` |  |
| `Make` |  |
| `Mfr` |  |
| `MfrBodyCode` |  |
| `Model` |  |
| `PowerOutput` |  |
| `PublicationStage` |  |
| `QueryExecutionError` |  |
| `Region` |  |
| `SpringType` |  |
| `SpringTypeConfig` |  |
| `SteeringConfig` |  |
| `SteeringSystem` |  |
| `SteeringType` |  |
| `SubModel` |  |
| `Transmission` |  |
| `TransmissionBase` |  |
| `TransmissionControlType` |  |
| `TransmissionMfrCode` |  |
| `TransmissionNumSpeeds` |  |
| `TransmissionType` |  |
| `VCdbChanges` |  |
| `Valves` |  |
| `Vehicle` |  |
| `VehicleToBedConfig` |  |
| `VehicleToBodyConfig` |  |
| `VehicleToBodyStyleConfig` |  |
| `VehicleToBrakeConfig` |  |
| `VehicleToClass` |  |
| `VehicleToDriveType` |  |
| `VehicleToEngineConfig` |  |
| `VehicleToMfrBodyCode` |  |
| `VehicleToSpringTypeConfig` |  |
| `VehicleToSteeringConfig` |  |
| `VehicleToTransmission` |  |
| `VehicleToWheelBase` |  |
| `VehicleType` |  |
| `VehicleTypeGroup` |  |
| `Version` |  |
| `WheelBase` |  |
| `Year` |  |

### Class: `Abbreviation`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'abbreviation'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Aspiration`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'aspiration'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Attachment`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'attachment'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `AttachmentType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'attachment_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BaseVehicle`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'base_vehicle'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BedConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'bed_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BedLength`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'bed_length'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BedType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'bed_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BodyNumDoors`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'body_num_doors'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BodyStyleConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'body_style_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BodyType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'body_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BrakeABS`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'brake_abs'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BrakeConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'brake_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BrakeSystem`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'brake_system'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `BrakeType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'brake_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `ChangeAttributeStates`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'change_attribute_states'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `ChangeDetails`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'change_details'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `ChangeReasons`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'change_reasons'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `ChangeTableNames`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'change_table_names'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Changes`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'changes'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Class`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'class'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `ConfigurationError`
**Inherits from:** Exception

### Class: `CylinderHeadType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'cylinder_head_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `DatabaseConnectionError`
**Inherits from:** Exception

### Class: `DriveType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'drive_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `ElecControlled`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'elec_controlled'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineBase`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_base'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineBase2`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_base2'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineBlock`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_block'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineBoreStroke`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_bore_stroke'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineConfig2`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_config2'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineDesignation`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_designation'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineVIN`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_vin'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EngineVersion`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'engine_version'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `EnglishPhrase`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'english_phrase'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `ExportError`
**Inherits from:** Exception

### Class: `FuelDeliveryConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'fuel_delivery_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `FuelDeliverySubType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'fuel_delivery_sub_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `FuelDeliveryType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'fuel_delivery_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `FuelSystemControlType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'fuel_system_control_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `FuelSystemDesign`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'fuel_system_design'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `FuelType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'fuel_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `IgnitionSystemType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'ignition_system_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `InvalidFilterError`
**Inherits from:** Exception

### Class: `Language`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'language'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `LanguageTranslation`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'language_translation'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `LanguageTranslationAttachment`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'language_translation_attachment'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Make`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'make'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Mfr`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'mfr'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `MfrBodyCode`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'mfr_body_code'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Model`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'model'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `PowerOutput`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'power_output'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `PublicationStage`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'publication_stage'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `QueryExecutionError`
**Inherits from:** Exception

### Class: `Region`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'region'` |
| `__table_args__` | `    __table_args__ = (
        UniqueConstraint("region_id", name="uq_region_id"),
        {"schema": "vcdb"}
    )` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `SpringType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'spring_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `SpringTypeConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'spring_type_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `SteeringConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'steering_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `SteeringSystem`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'steering_system'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `SteeringType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'steering_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `SubModel`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'sub_model'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Transmission`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'transmission'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `TransmissionBase`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'transmission_base'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `TransmissionControlType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'transmission_control_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `TransmissionMfrCode`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'transmission_mfr_code'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `TransmissionNumSpeeds`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'transmission_num_speeds'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `TransmissionType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'transmission_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VCdbChanges`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vcdb_changes'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Valves`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'valves'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Vehicle`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |
| `make` `@property` |  |
| `model` `@property` |  |
| `year` `@property` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

##### `make`
```python
@property
def make(self) -> Make:
```

##### `model`
```python
@property
def model(self) -> str:
```

##### `year`
```python
@property
def year(self) -> Optional[int]:
```

### Class: `VehicleToBedConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_bed_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToBodyConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_body_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToBodyStyleConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_body_style_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToBrakeConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_brake_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToClass`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_class'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToDriveType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_drive_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToEngineConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_engine_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToMfrBodyCode`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_mfr_body_code'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToSpringTypeConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_spring_type_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToSteeringConfig`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_steering_config'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToTransmission`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_transmission'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleToWheelBase`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_to_wheel_base'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleType`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_type'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `VehicleTypeGroup`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'vehicle_type_group'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Version`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'version'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `WheelBase`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'wheel_base'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```

### Class: `Year`
**Inherits from:** VCdbBase

#### Attributes

| Name | Value |
| --- | --- |
| `__tablename__` | `'year'` |
| `__table_args__` | `    __table_args__ = {"schema": "vcdb"}` |

#### Methods

| Method | Description |
| --- | --- |
| `__repr__` |  |

##### `__repr__`
```python
def __repr__(self) -> str:
```
