from __future__ import annotations
import logging
import sys
import threading
import traceback
from typing import Any, Callable, Optional, List, Dict, Set
from PySide6.QtCore import QObject

original_excepthook = sys.excepthook
original_stderr_write = sys.stderr.write
logger = logging.getLogger('thread_debug')

# Expanded list of common Qt threading warnings
QT_THREADING_VIOLATIONS = [
    'QObject::setParent: Cannot set parent, new parent is in a different thread',
    'QObject::startTimer: Timers can only be used with threads started with QThread',
    'QObject: Cannot create children for a parent that is in a different thread',
    'QSocketNotifier: Socket notifiers cannot be enabled or disabled from another thread',
    'QWidget::repaint: Recursive repaint detected',
    'QPixmap: It is not safe to use pixmaps outside the GUI thread',
    'Cannot send events to objects owned by a different thread',
    'QObject::connect: Cannot queue arguments of type',
    'QObject::installEventFilter: Cannot filter events for objects in a different thread'
]

tracked_warnings: List[Dict[str, Any]] = []
violation_counts: Dict[str, int] = {}
object_creation_threads: Dict[int, int] = {}  # Maps QObject address to thread ID


class QtThreadMonitor:
    """Enhanced monitoring of Qt threading violations."""

    @staticmethod
    def register_qobject(obj: QObject) -> None:
        """Register a QObject and its creation thread."""
        if not isinstance(obj, QObject):
            return
        object_creation_threads[id(obj)] = threading.get_ident()

    @staticmethod
    def check_qobject_thread(obj: QObject) -> bool:
        """Check if a QObject is being accessed from its creation thread."""
        if not isinstance(obj, QObject):
            return True

        obj_id = id(obj)
        current_thread = threading.get_ident()

        if obj_id in object_creation_threads:
            creation_thread = object_creation_threads[obj_id]
            if current_thread != creation_thread:
                stack = traceback.extract_stack()
                logger.warning(
                    f"QObject accessed from wrong thread. Created in {creation_thread}, "
                    f"accessed from {current_thread}. Object: {obj.__class__.__name__}"
                )
                logger.debug(f"Stack trace:\n{''.join(traceback.format_list(stack))}")
                return False
        return True


def enhanced_stderr_write(text: str) -> int:
    """Enhanced stderr handler that tracks Qt threading violations."""
    for warning in QT_THREADING_VIOLATIONS:
        if warning in text:
            stack = traceback.extract_stack()
            relevant_stack = stack[:-3]  # Skip stderr.write frames
            stack_trace = ''.join(traceback.format_list(relevant_stack))

            # Record violation type
            violation_type = next((v for v in QT_THREADING_VIOLATIONS if v in text), "Other Qt threading violation")

            # Update counts
            violation_counts[violation_type] = violation_counts.get(violation_type, 0) + 1

            # Log the violation
            logger.error(f'Qt Threading Violation: {text.strip()}\nStack Trace:\n{stack_trace}')

            # Track detailed info for later analysis
            tracked_warnings.append({
                'warning': text.strip(),
                'stack_trace': stack_trace,
                'thread_id': threading.get_ident(),
                'thread_name': threading.current_thread().name,
                'violation_type': violation_type,
                'timestamp': logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))
            })
            break

    return original_stderr_write(text)


def monkey_patch_qobject() -> None:
    """Monkey patch QObject to track thread violations."""
    original_init = QObject.__init__

    def enhanced_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        QtThreadMonitor.register_qobject(self)

    QObject.__init__ = enhanced_init


def install_enhanced_thread_debug(enable_logging: bool = True) -> None:
    """Install enhanced Qt thread debugging."""
    if enable_logging:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    sys.stderr.write = enhanced_stderr_write
    monkey_patch_qobject()

    logger.info("Enhanced Qt threading debug installed")


def uninstall_enhanced_thread_debug() -> None:
    """Remove enhanced thread debugging."""
    sys.stderr.write = original_stderr_write
    # We can't easily undo the QObject monkey patching

    # Generate summary report
    logger.info(f"Thread debugging disabled. Summary of violations:")
    for violation, count in violation_counts.items():
        logger.info(f"- {violation}: {count} occurrences")


def get_violation_statistics() -> Dict[str, Any]:
    """Get statistics about threading violations."""
    return {
        'total_violations': len(tracked_warnings),
        'violation_types': violation_counts,
        'detailed_warnings': tracked_warnings
    }


def clear_tracked_warnings() -> None:
    """Clear the stored warnings."""
    tracked_warnings.clear()
    violation_counts.clear()