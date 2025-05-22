# Module: plugins.database_connector_plugin.code.models

**Path:** `plugins/database_connector_plugin/code/models.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
```

## Classes

| Class | Description |
| --- | --- |
| `ColumnInfo` |  |
| `ConnectionType` |  |
| `DatabaseConnection` |  |
| `ExportFormat` |  |
| `ExportSettings` |  |
| `FieldMapping` |  |
| `HistorySchedule` |  |
| `PluginSettings` |  |
| `QueryResult` |  |
| `SavedQuery` |  |
| `TableInfo` |  |
| `ValidationRule` |  |
| `ValidationRuleType` |  |

### Class: `ColumnInfo`
**Inherits from:** BaseModel

### Class: `ConnectionType`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `POSTGRESQL` | `'postgresql'` |
| `MYSQL` | `'mysql'` |
| `SQLITE` | `'sqlite'` |
| `ORACLE` | `'oracle'` |
| `MSSQL` | `'mssql'` |
| `AS400` | `'as400'` |
| `ODBC` | `'odbc'` |

### Class: `DatabaseConnection`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_name` |  |
| `validate_port` |  |

##### `validate_name`
```python
@validator('name')
def validate_name(cls, v) -> str:
```

##### `validate_port`
```python
@validator('port')
def validate_port(cls, v) -> Optional[int]:
```

### Class: `ExportFormat`
**Inherits from:** str, Enum

#### Attributes

| Name | Value |
| --- | --- |
| `CSV` | `'csv'` |
| `JSON` | `'json'` |
| `XML` | `'xml'` |
| `EXCEL` | `'excel'` |
| `TSV` | `'tsv'` |
| `HTML` | `'html'` |

### Class: `ExportSettings`
**Inherits from:** BaseModel

### Class: `FieldMapping`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_table_name` |  |

##### `validate_table_name`
```python
@validator('table_name')
def validate_table_name(cls, v) -> str:
```

### Class: `HistorySchedule`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_frequency` |  |
| `validate_name` |  |
| `validate_retention_days` |  |

##### `validate_frequency`
```python
@validator('frequency')
def validate_frequency(cls, v) -> str:
```

##### `validate_name`
```python
@validator('name')
def validate_name(cls, v) -> str:
```

##### `validate_retention_days`
```python
@validator('retention_days')
def validate_retention_days(cls, v) -> int:
```

### Class: `PluginSettings`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_max_recent_connections` |  |
| `validate_query_limit` |  |

##### `validate_max_recent_connections`
```python
@validator('max_recent_connections')
def validate_max_recent_connections(cls, v) -> int:
```

##### `validate_query_limit`
```python
@validator('query_limit')
def validate_query_limit(cls, v) -> int:
```

### Class: `QueryResult`
**Inherits from:** BaseModel

### Class: `SavedQuery`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_name` |  |
| `validate_query_text` |  |

##### `validate_name`
```python
@validator('name')
def validate_name(cls, v) -> str:
```

##### `validate_query_text`
```python
@validator('query_text')
def validate_query_text(cls, v) -> str:
```

### Class: `TableInfo`
**Inherits from:** BaseModel

### Class: `ValidationRule`
**Inherits from:** BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_field_name` |  |
| `validate_name` |  |

##### `validate_field_name`
```python
@validator('field_name')
def validate_field_name(cls, v) -> str:
```

##### `validate_name`
```python
@validator('name')
def validate_name(cls, v) -> str:
```

### Class: `ValidationRuleType`
**Inherits from:** str, Enum

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
