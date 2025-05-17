# Module: plugin_system.config_schema

**Path:** `plugin_system/config_schema.py`

[Back to Project Index](../../index.md)

## Imports
```python
from __future__ import annotations
import enum
from typing import Any, Dict, List, Literal, Optional, Union, TypedDict, get_args, get_origin
import pydantic
from pydantic import Field, validator
```

## Functions

| Function | Description |
| --- | --- |
| `convert_pydantic_to_schema` |  |

### `convert_pydantic_to_schema`
```python
def convert_pydantic_to_schema(model_class) -> ConfigSchema:
```

## Classes

| Class | Description |
| --- | --- |
| `ConfigField` |  |
| `ConfigFieldType` |  |
| `ConfigGroup` |  |
| `ConfigSchema` |  |
| `ValidationRule` |  |

### Class: `ConfigField`
**Inherits from:** pydantic.BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `validate_default_value` |  |
| `validate_options` |  |

##### `validate_default_value`
```python
@validator('default_value')
def validate_default_value(cls, v, values):
```

##### `validate_options`
```python
@validator('options')
def validate_options(cls, v, values):
```

### Class: `ConfigFieldType`
**Inherits from:** str, enum.Enum

#### Attributes

| Name | Value |
| --- | --- |
| `STRING` | `'string'` |
| `INTEGER` | `'integer'` |
| `FLOAT` | `'float'` |
| `BOOLEAN` | `'boolean'` |
| `SELECT` | `'select'` |
| `MULTISELECT` | `'multiselect'` |
| `COLOR` | `'color'` |
| `FILE` | `'file'` |
| `DIRECTORY` | `'directory'` |
| `PASSWORD` | `'password'` |
| `JSON` | `'json'` |
| `CODE` | `'code'` |
| `DATETIME` | `'datetime'` |
| `DATE` | `'date'` |
| `TIME` | `'time'` |

### Class: `ConfigGroup`
**Inherits from:** pydantic.BaseModel

### Class: `ConfigSchema`
**Inherits from:** pydantic.BaseModel

#### Methods

| Method | Description |
| --- | --- |
| `get_default_values` |  |
| `to_dict` |  |
| `validate_config` |  |

##### `get_default_values`
```python
def get_default_values(self) -> Dict[(str, Any)]:
```

##### `to_dict`
```python
def to_dict(self) -> Dict[(str, Any)]:
```

##### `validate_config`
```python
def validate_config(self, config) -> Dict[(str, Any)]:
```

### Class: `ValidationRule`
**Inherits from:** pydantic.BaseModel
