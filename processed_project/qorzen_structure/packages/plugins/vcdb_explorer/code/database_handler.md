# Module: plugins.vcdb_explorer.code.database_handler

**Path:** `plugins/vcdb_explorer/code/database_handler.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import logging
import threading
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, cast
import sqlalchemy
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import Select
from qorzen.core.database_manager import DatabaseConnectionConfig, DatabaseManager
from qorzen.core.event_bus_manager import EventBusManager
from qorzen.core.event_model import Event, EventType
from qorzen.core.thread_manager import ThreadManager, TaskResult
from qorzen.utils.exceptions import DatabaseError
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
| `configure` |  |
| `execute_query` |  |
| `get_available_columns` |  |
| `get_available_filters` |  |
| `get_filter_values` |  |
| `session` |  |
| `shutdown` |  |

##### `__init__`
```python
def __init__(self, database_manager, event_bus, thread_manager, logger) -> None:
```

##### `configure`
```python
def configure(self, host, port, database, user, password, db_type, pool_size, max_overflow, pool_recycle, echo) -> None:
```

##### `execute_query`
```python
def execute_query(self, filter_panels, columns, page, page_size, sort_by, sort_desc, table_filters) -> Tuple[(List[Dict[(str, Any)]], int)]:
```

##### `get_available_columns`
```python
def get_available_columns(self) -> List[Dict[(str, str)]]:
```

##### `get_available_filters`
```python
def get_available_filters(self) -> List[Dict[(str, str)]]:
```

##### `get_filter_values`
```python
def get_filter_values(self, filter_type, current_filters, exclude_filters) -> List[Dict[(str, Any)]]:
```

##### `session`
```python
@contextmanager
def session(self) -> Generator[(Session, None, None)]:
```

##### `shutdown`
```python
def shutdown(self) -> None:
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
