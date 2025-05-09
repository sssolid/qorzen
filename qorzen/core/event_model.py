from __future__ import annotations
import dataclasses
import datetime
import enum
import uuid
from typing import Any, Dict, Optional, Union, Callable, List, TypeVar, Generic
from pydantic import BaseModel, Field


class EventType(str, enum.Enum):
    """Standard event types in the system."""
    # System events
    SYSTEM_STARTED = "system/started"

    # UI events
    UI_READY = "ui/ready"
    UI_UPDATE = "ui/update"
    UI_COMPONENT_ADDED = "ui/component/added"

    # Log events
    LOG_MESSAGE = "log/message"
    LOG_ERROR = "log/error"
    LOG_EXCEPTION = "log/exception"
    LOG_WARNING = "log/warning"
    LOG_DEBUG = "log/debug"
    LOG_INFO = "log/info"
    LOG_TRACE = "log/trace"
    LOG_CRITICAL = "log/critical"
    LOG_EVENT = "log/event"

    # Plugin events
    PLUGIN_LOADED = "plugin/loaded"
    PLUGIN_UNLOADED = "plugin/unloaded"
    PLUGIN_ENABLED = "plugin/enabled"
    PLUGIN_DISABLED = "plugin/disabled"
    PLUGIN_INSTALLED = "plugin/installed"
    PLUGIN_UNINSTALLED = "plugin/uninstalled"
    PLUGIN_UPDATED = "plugin/updated"
    PLUGIN_ERROR = "plugin/error"
    PLUGIN_INITIALIZED = "plugin/initialized"
    PLUGIN_MANAGER_INITIALIZED = "plugin_manager/initialized"

    # Monitoring events
    MONITORING_METRICS = "monitoring/metrics"
    MONITORING_ALERT = "monitoring/alert"

    # Config events
    CONFIG_CHANGED = "config/changed"

    # Custom events - for backward compatibility
    CUSTOM = "custom"

    @classmethod
    def requires_main_thread(cls, event_type: str) -> bool:
        """Determine if an event type should be handled on the main thread."""
        # UI events need main thread
        if event_type.startswith("ui/"):
            return True

        # Log events that might update UI
        if event_type.startswith("log/"):
            return True

        # Other specific events that need main thread
        main_thread_events = {
            "monitoring/alert",
            "plugin/error",
            "plugin/loaded",  # Could trigger UI updates
            "plugin/unloaded"  # Could trigger UI updates
        }

        return event_type in main_thread_events

    @classmethod
    def plugin_specific(cls, plugin_name: str, event_name: str) -> str:
        """Create a plugin-specific event type."""
        return f"plugin/{plugin_name}/{event_name}"


T = TypeVar('T')


class EventPayload(BaseModel, Generic[T]):
    """Base class for all event payloads with type information."""
    data: T


class Event(BaseModel):
    """Event model with type information."""
    event_type: str = Field(..., description='The type of the event, used for routing')
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description='Unique identifier for the event')
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now,
                                         description='When the event was created')
    source: str = Field(..., description='The source component that generated the event')
    payload: Dict[str, Any] = Field(default_factory=dict, description='The event data')
    correlation_id: Optional[str] = Field(None, description='ID for tracking related events')

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime.datetime: lambda dt: dt.isoformat(),
            uuid.UUID: lambda id: str(id)
        }

    @classmethod
    def create(cls, event_type: Union[EventType, str], source: str,
               payload: Optional[Dict[str, Any]] = None,
               correlation_id: Optional[str] = None) -> Event:
        """Create a new event with the given parameters.

        Args:
            event_type: The type of event (enum or string)
            source: The source component generating the event
            payload: Optional event data
            correlation_id: Optional ID for tracking related events

        Returns:
            A new Event instance
        """
        if isinstance(event_type, EventType):
            event_type = event_type.value

        return cls(
            event_type=event_type,
            source=source,
            payload=payload or {},
            correlation_id=correlation_id
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return self.dict()

    def __str__(self) -> str:
        return f'Event(type={self.event_type}, id={self.event_id}, source={self.source})'


# Type alias for event handlers
EventHandler = Callable[[Event], None]


@dataclasses.dataclass
class EventSubscription:
    """Event subscription with typed handler."""
    subscriber_id: str
    event_type: str
    callback: EventHandler
    filter_criteria: Optional[Dict[str, Any]] = None

    def matches_event(self, event: Event) -> bool:
        """Check if event matches this subscription.

        Args:
            event: The event to check

        Returns:
            True if the event matches this subscription
        """
        if event.event_type != self.event_type and self.event_type != '*':
            return False

        if not self.filter_criteria:
            return True

        for key, value in self.filter_criteria.items():
            if key not in event.payload or event.payload[key] != value:
                return False

        return True