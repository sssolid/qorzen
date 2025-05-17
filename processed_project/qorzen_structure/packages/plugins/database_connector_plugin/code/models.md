# Module: plugins.database_connector_plugin.code.models

**Path:** `plugins/database_connector_plugin/code/models.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import datetime
import enum
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union, cast, Literal
from pydantic import BaseModel, Field, SecretStr, validator, root_validator
```

## Classes

| Class | Description |
| --- | --- |
| `AS400ConnectionConfig` |  |
| `BaseConnectionConfig` |  |
| `ColumnMetadata` |  |
| `Config` |  |
| `ConnectionType` |  |
| `FieldMapping` |  |
| `HistoryEntry` |  |
| `HistorySchedule` |  |
| `ODBCConnectionConfig` |  |
| `PluginSettings` |  |
| `QueryHistoryEntry` |  |
| `QueryResult` |  |
| `SQLConnectionConfig` |  |
| `SavedQuery` |  |
| `TableMetadata` |  |
| `ValidationResult` |  |
| `ValidationRule` |  |
| `ValidationRuleType` |  |

### Class: `AS400ConnectionConfig`
**Inherits from:** BaseConnectionConfig

#### Methods

| Method | Description |
| --- | --- |
| `validate_allowed_lists` |  |
| `validate_port` |  |

##### `validate_allowed_lists`
```python
@validator('allowed_tables', 'allowed_libraries')
def validate_allowed_lists(cls, v) -> Optional[List[str]]:
```

##### `validate_port`
```python
@validator('port')
def validate_port(cls, v) -> Optional[int]:
```

### Class: `BaseConnectionConfig`
**Inherits from:** BaseModel

### Class: `ColumnMetadata`
**Decorators:**
- `@dataclass`

### Class: `Config`

#### Attributes

| Name | Value |
| --- | --- |
| `validate_assignment` | `True` |

### Class: `ConnectionType`
**Inherits from:** str, enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `AS400` | `'as400'` |
| `ODBC` | `'odbc'` |
| `MYSQL` | `'mysql'` |
| `POSTGRES` | `'postgres'` |
| `SQLITE` | `'sqlite'` |
| `ORACLE` | `'oracle'` |
| `MSSQL` | `'mssql'` |

### Class: `FieldMapping`
**Inherits from:** BaseModel

### Class: `HistoryEntry`
**Inherits from:** BaseModel

### Class: `HistorySchedule`
**Inherits from:** BaseModel

### Class: `ODBCConnectionConfig`
**Inherits from:** BaseConnectionConfig

#### Methods

| Method | Description |
| --- | --- |
| `validate_connection_info` |  |
| `validate_port` |  |

##### `validate_connection_info`
```python
@root_validator
def validate_connection_info(cls, values) -> Dict[(str, Any)]:
```

##### `validate_port`
```python
@validator('port')
def validate_port(cls, v) -> Optional[int]:
```

### Class: `PluginSettings`
**Inherits from:** BaseModel

### Class: `QueryHistoryEntry`
**Inherits from:** BaseModel

### Class: `QueryResult`
**Decorators:**
- `@dataclass`

### Class: `SQLConnectionConfig`
**Inherits from:** BaseConnectionConfig

#### Methods

| Method | Description |
| --- | --- |
| `validate_port` |  |

##### `validate_port`
```python
@validator('port')
def validate_port(cls, v) -> Optional[int]:
```

### Class: `SavedQuery`
**Inherits from:** BaseModel

### Class: `TableMetadata`
**Decorators:**
- `@dataclass`

### Class: `ValidationResult`
**Inherits from:** BaseModel

### Class: `ValidationRule`
**Inherits from:** BaseModel

### Class: `ValidationRuleType`
**Inherits from:** str, enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `RANGE` | `'range'` |
| `PATTERN` | `'pattern'` |
| `NOT_NULL` | `'not_null'` |
| `UNIQUE` | `'unique'` |
| `LENGTH` | `'length'` |
| `REFERENCE` | `'reference'` |
| `ENUMERATION` | `'enumeration'` |
| `CUSTOM` | `'custom'` |
