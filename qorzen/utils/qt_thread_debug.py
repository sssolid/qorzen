from __future__ import annotations

import logging
import sys
import traceback
from typing import Any, Callable, Optional, List, Dict

original_excepthook = sys.excepthook

# Store the original stderr.write
original_stderr_write = sys.stderr.write

logger = logging.getLogger("thread_debug")

QT_THREADING_WARNINGS = [
    "QObject::setParent: Cannot set parent, new parent is in a different thread",
    "QObject::startTimer: Timers can only be used with threads started with QThread",
    "QObject: Cannot create children for a parent that is in a different thread",
    "QSocketNotifier: Socket notifiers cannot be enabled or disabled from another thread"
]

tracked_warnings: List[Dict[str, Any]] = []


def debug_stderr_write(text: str) -> int:
    """
    Intercept stderr writes to catch and log Qt threading warnings.

    Args:
        text: The text being written to stderr

    Returns:
        Result of the original write operation
    """
    # Check if the text contains any Qt threading warnings
    for warning in QT_THREADING_WARNINGS:
        if warning in text:
            # Get the current stack trace
            stack = traceback.extract_stack()
            # Remove the last few frames which are just this handler
            relevant_stack = stack[:-3]

            # Format and log the warning with stack trace
            stack_trace = "".join(traceback.format_list(relevant_stack))

            logger.error(f"Qt Threading Warning: {text.strip()}\nStack Trace:\n{stack_trace}")

            # Store for later analysis
            tracked_warnings.append({
                "warning": text.strip(),
                "stack_trace": stack_trace
            })

            break

    # Call the original write function
    return original_stderr_write(text)


def install_qt_thread_debug(enable_logging: bool = True) -> None:
    """
    Install the Qt threading debug interceptor.

    Args:
        enable_logging: Whether to enable logging of Qt threading warnings
    """
    # Set up logging if requested
    if enable_logging:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    # Install the interceptor
    sys.stderr.write = debug_stderr_write


def uninstall_qt_thread_debug() -> None:
    """Remove the Qt threading debug interceptor."""
    sys.stderr.write = original_stderr_write


def get_tracked_warnings() -> List[Dict[str, Any]]:
    """
    Get the list of tracked Qt threading warnings.

    Returns:
        List of dictionaries containing warning messages and stack traces
    """
    return tracked_warnings.copy()


def clear_tracked_warnings() -> None:
    """Clear the list of tracked Qt threading warnings."""
    tracked_warnings.clear()