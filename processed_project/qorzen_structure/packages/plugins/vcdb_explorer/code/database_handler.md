# Module: plugins.vcdb_explorer.code.database_handler

**Path:** `plugins/vcdb_explorer/code/database_handler.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
from sqlalchemy.orm.util import AliasedInsp, AliasedClass
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable
from functools import lru_cache
import sqlalchemy
from sqlalchemy import func, or_, select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Join
from qorzen.core.database_manager import DatabaseConnectionConfig, DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event
from qorzen.core.task_manager import TaskManager, TaskCategory, TaskPriority
from qorzen.core.concurrency_manager import ConcurrencyManager
from qorzen.utils.exceptions import DatabaseError, TaskError
from events import VCdbEventType
from models import Aspiration, BaseVehicle, BedConfig, BedLength, BedType, BodyNumDoors, BodyStyleConfig, BodyType, BrakeABS, BrakeConfig, BrakeSystem, BrakeType, Class, CylinderHeadType, DriveType, ElecControlled, EngineBase2, EngineBlock, EngineBoreStroke, EngineConfig2, EngineDesignation, EngineVersion, FuelDeliveryConfig, FuelDeliverySubType, FuelDeliveryType, FuelSystemControlType, FuelSystemDesign, FuelType, IgnitionSystemType, Make, Mfr, MfrBodyCode, Model, PowerOutput, PublicationStage, Region, SpringType, SpringTypeConfig, SteeringConfig, SteeringSystem, SteeringType, SubModel, Transmission, TransmissionBase, TransmissionControlType, TransmissionMfrCode, TransmissionNumSpeeds, TransmissionType, Valves, Vehicle, VehicleToBodyConfig, VehicleToBodyStyleConfig, VehicleToBedConfig, VehicleToBrakeConfig, VehicleToClass, VehicleToDriveType, VehicleToEngineConfig, VehicleToMfrBodyCode, VehicleToSpringTypeConfig, VehicleToSteeringConfig, VehicleToTransmission, VehicleToWheelBase, VehicleType, VehicleTypeGroup, WheelBase, Year
```

## Classes

| Class | Description |
| --- | --- |
| `DatabaseHandler` |  |
| `DatabaseHandlerError` |  |

### Class: `DatabaseHandler`

#### Attributes

| Name | Value |
| --- | --- |
| `CONNECTION_NAME` | `'vcdb_explorer'` |

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |
| `cancel_query` `async` |  |
| `configure` `async` |  |
| `get_available_columns` |  |
| `get_available_filters` |  |
| `get_filter_values` `async` |  |
| `initialize` `async` |  |
| `shutdown` `async` |  |

##### `__init__`
```python
def __init__(self, database_manager, event_bus_manager, task_manager, concurrency_manager, logger) -> None:
```

##### `cancel_query`
```python
async def cancel_query(self, callback_id) -> bool:
```

##### `configure`
```python
async def configure(self, host, port, database, user, password, db_type, pool_size, max_overflow, pool_recycle, echo) -> None:
```

##### `get_available_columns`
```python
def get_available_columns(self) -> List[Dict[(str, str)]]:
```

##### `get_available_filters`
```python
def get_available_filters(self) -> List[Dict[(str, Any)]]:
```

##### `get_filter_values`
```python
async def get_filter_values(self, filter_type, current_filters, exclude_filters) -> List[Dict[(str, Any)]]:
```

##### `initialize`
```python
async def initialize(self) -> None:
```

##### `shutdown`
```python
async def shutdown(self) -> None:
```

### Class: `DatabaseHandlerError`
**Inherits from:** Exception

#### Methods

| Method | Description |
| --- | --- |
| `__init__` |  |

##### `__init__`
```python
def __init__(self, message, details) -> None:
```
