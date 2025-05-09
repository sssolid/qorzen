# Module: main

**Path:** `main.py`

[Back to Project Index](../index.md)

## Imports
```python
from __future__ import annotations
import argparse
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer
import qorzen.resources_rc
```

## Functions

| Function | Description |
| --- | --- |
| `handle_build_command` |  |
| `main` |  |
| `parse_arguments` |  |
| `run_headless` |  |
| `run_steps` |  |
| `setup_environment` |  |
| `start_ui` |  |

### `handle_build_command`
```python
def handle_build_command(args) -> int:
```

### `main`
```python
def main() -> int:
```

### `parse_arguments`
```python
def parse_arguments() -> argparse.Namespace:
```

### `run_headless`
```python
def run_headless(args) -> int:
```

### `run_steps`
```python
def run_steps(steps, on_complete, on_error) -> None:
```

### `setup_environment`
```python
def setup_environment() -> None:
```

### `start_ui`
```python
def start_ui(args) -> int:
```
