# Module: main

**Path:** `main.py`

[Back to Project Index](../index.md)

## Imports
```python
from __future__ import annotations
import argparse
import asyncio
import importlib
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast
```

## Functions

| Function | Description |
| --- | --- |
| `handle_build_command` |  |
| `main` |  |
| `main_async` |  |
| `parse_arguments` |  |
| `run_headless` |  |
| `setup_environment` |  |
| `start_ui` |  |

### `handle_build_command`
```python
async def handle_build_command(args) -> int:
```

### `main`
```python
def main() -> int:
```

### `main_async`
```python
async def main_async() -> int:
```

### `parse_arguments`
```python
def parse_arguments() -> argparse.Namespace:
```

### `run_headless`
```python
async def run_headless(args) -> int:
```

### `setup_environment`
```python
async def setup_environment() -> None:
```

### `start_ui`
```python
async def start_ui(args) -> int:
```
