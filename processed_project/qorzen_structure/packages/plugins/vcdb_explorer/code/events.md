# Module: plugins.vcdb_explorer.code.events

**Path:** `plugins/vcdb_explorer/code/events.py`

[Back to Project Index](../../../../index.md)

## Imports
```python
from __future__ import annotations
from qorzen.core.event_model import EventType
```

## Classes

| Class | Description |
| --- | --- |
| `VCdbEventType` |  |

### Class: `VCdbEventType`

#### Methods

| Method | Description |
| --- | --- |
| `filter_changed` |  |
| `filters_refreshed` |  |
| `query_execute` |  |
| `query_results` |  |

##### `filter_changed`
```python
@staticmethod
def filter_changed() -> str:
```

##### `filters_refreshed`
```python
@staticmethod
def filters_refreshed() -> str:
```

##### `query_execute`
```python
@staticmethod
def query_execute() -> str:
```

##### `query_results`
```python
@staticmethod
def query_results() -> str:
```
