from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
import queue
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast, Awaitable

from qorzen.core.base import QorzenManager
from qorzen.core.event_model import Event, EventSubscription, EventHandler, EventType
from qorzen.utils.exceptions import EventBusError, ManagerInitializationError, ManagerShutdownError


class EventBusManager(QorzenManager):
    """Asynchronous event bus manager for the application.

    This manager handles event subscription, publication, and routing
    in an asynchronous manner. It supports filtering, prioritization,
    and main thread dispatching.

    Attributes:
        _config_manager: The configuration manager
        _logger: The logger instance
        _thread_manager: The thread manager
        _max_queue_size: Maximum size of the event queue
        _publish_timeout: Timeout for event publishing
        _subscriptions: Dictionary of event subscriptions
        _event_queue: Queue for pending events
        _running: Flag indicating whether the manager is running
        _stop_event: Event to signal workers to stop
    """

    def __init__(
            self,
            config_manager: Any,
            logger_manager: Any,
            thread_manager: Any
    ) -> None:
        """Initialize the event bus manager.

        Args:
            config_manager: The configuration manager
            logger_manager: The logging manager
            thread_manager: The thread management system
        """
        super().__init__(name='event_bus_manager')
        self._config_manager = config_manager
        self._logger_manager = logger_manager
        self._logger = logger_manager.get_logger('event_bus_manager')
        self._thread_manager = thread_manager

        self._max_queue_size: int = 1000
        self._publish_timeout: float = 5.0

        # Subscriptions are keyed by event_type, then by subscriber_id
        self._subscriptions: Dict[str, Dict[str, EventSubscription]] = {}
        self._subscription_lock = asyncio.Lock()

        # Event processing queue and task management
        self._event_queue: Optional[asyncio.Queue[Tuple[Event, List[EventSubscription]]]] = None
        self._worker_tasks: List[asyncio.Task] = []
        self._running: bool = False
        self._stop_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize the event bus manager asynchronously.

        Sets up the event queue and worker tasks.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            event_bus_config = await self._config_manager.get('event_bus_manager', {})
            if not event_bus_config:
                self._logger.error("Event Bus configuration not found in configuration")

            if not hasattr(event_bus_config, 'max_queue_size'):
                self._logger.warning("Event Bus configuration max_queue_size not found in configuration")
            if not hasattr(event_bus_config, 'publish_timeout'):
                self._logger.warning("Event Bus configuration publish_timeout not found in configuration")
            if not hasattr(event_bus_config, 'thread_pool_size'):
                self._logger.warning("Event Bus configuration thread_pool_size not found in configuration")

            self._max_queue_size = event_bus_config.get('max_queue_size', 1000)
            self._publish_timeout = event_bus_config.get('publish_timeout', 5.0)
            thread_pool_size = event_bus_config.get('thread_pool_size', 4)

            # Create the event queue
            self._event_queue = asyncio.Queue(maxsize=self._max_queue_size)

            # Start event worker tasks
            self._running = True
            for i in range(thread_pool_size):
                worker = asyncio.create_task(
                    self._event_worker(i),
                    name=f'event-worker-{i}'
                )
                self._worker_tasks.append(worker)

            # Register configuration listener
            await self._config_manager.register_listener('event_bus_manager', self._on_config_changed)

            self._logger.info('Event Bus Manager initialized')
            self._initialized = True
            self._healthy = True

        except Exception as e:
            self._logger.error(f'Failed to initialize Event Bus Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize AsyncEventBusManager: {str(e)}',
                manager_name=self.name
            ) from e

    async def _event_worker(self, worker_id: int) -> None:
        """Worker task for processing events from the queue."""
        self._logger.debug(f"Event worker {worker_id} started")

        while self._running and not self._stop_event.is_set():
            try:
                # Pull an event off the queue, or time out quickly so we can exit
                try:
                    event, subscriptions = await self._event_queue.get()
                except asyncio.TimeoutError:
                    continue

                needs_main = EventType.requires_main_thread(event.event_type)
                background_tasks: list[asyncio.Task] = []

                for subscription in subscriptions:
                    callback = subscription.callback

                    try:
                        if needs_main and self._thread_manager:
                            # Dispatch on the Qt/main thread
                            def dispatch() -> None:
                                if inspect.iscoroutinefunction(callback):
                                    # schedule the coroutine so it actually runs
                                    asyncio.create_task(callback(event))
                                else:
                                    callback(event)

                            await self._thread_manager.run_on_main_thread(dispatch)

                        else:
                            # Off–main‑thread delivery
                            if inspect.iscoroutinefunction(callback):
                                task = asyncio.create_task(
                                    callback(event),
                                    name=f"event-{event.event_type}-{subscription.subscriber_id}"
                                )
                                background_tasks.append(task)
                            else:
                                callback(event)

                    except Exception as e:
                        self._logger.error(
                            f"Error in event handler for {event.event_type}: {e}",
                            extra={
                                "event_id": event.event_id,
                                "subscription_id": subscription.subscriber_id,
                                "error": str(e),
                            }
                        )

                # Wait for any off‑main‑thread handlers to finish
                if background_tasks:
                    results = await asyncio.gather(*background_tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, Exception):
                            self._logger.error(f"Unhandled exception in async handler: {result}")

            finally:
                # Always mark the queue item done, even on error
                self._event_queue.task_done()

        self._logger.debug(f"Event worker {worker_id} stopped")

    async def publish(
            self,
            event_type: Union[EventType, str],
            source: str,
            payload: Optional[Dict[str, Any]] = None,
            correlation_id: Optional[str] = None,
            synchronous: bool = False
    ) -> str:
        """Publish an event asynchronously.

        Args:
            event_type: Type of the event
            source: Source of the event
            payload: Event data
            correlation_id: ID for correlating related events
            synchronous: Whether to process the event synchronously

        Returns:
            The event ID

        Raises:
            EventBusError: If publishing fails
        """
        if not self._initialized:
            raise EventBusError(
                'Cannot publish events before initialization',
                event_type=str(event_type)
            )

        if isinstance(event_type, EventType):
            event_type = event_type.value

        # Create the event
        event = Event.create(
            event_type=event_type,
            source=source,
            payload=payload or {},
            correlation_id=correlation_id
        )

        # Get matching subscriptions
        matching_subs = await self._get_matching_subscriptions(event)

        if not matching_subs:
            self._logger.debug(
                f'No subscribers for event {event.event_type}',
                extra={'event_id': event.event_id}
            )
            return event.event_id

        if synchronous:
            # Process event synchronously
            await self._process_event_sync(event, matching_subs)
        else:
            try:
                if self._event_queue is None:
                    raise EventBusError(
                        'Event queue is not initialized',
                        event_type=str(event_type)
                    )

                # Put the event in the queue with timeout
                try:
                    await asyncio.wait_for(
                        self._event_queue.put((event, matching_subs)),
                        timeout=self._publish_timeout
                    )
                except asyncio.TimeoutError:
                    self._logger.error(
                        f'Event queue is full, cannot publish event {event.event_type}',
                        extra={'event_id': event.event_id}
                    )
                    raise EventBusError(
                        f'Event queue is full, cannot publish event {event.event_type}',
                        event_type=str(event_type)
                    )
            except EventBusError:
                raise
            except Exception as e:
                self._logger.error(
                    f'Error publishing event {event.event_type}: {str(e)}',
                    extra={'event_id': event.event_id}
                )
                raise EventBusError(
                    f'Error publishing event {event.event_type}: {str(e)}',
                    event_type=str(event_type)
                ) from e

        self._logger.debug(
            f'Published event {event.event_type}',
            extra={
                'event_id': event.event_id,
                'source': source,
                'subscribers': len(matching_subs),
                'synchronous': synchronous
            }
        )

        return event.event_id

    async def _process_event_sync(
            self,
            event: Event,
            subscriptions: List[EventSubscription]
    ) -> None:
        """Process an event synchronously.

        Args:
            event: The event to process
            subscriptions: List of subscriptions to notify
        """
        tasks = []

        for subscription in subscriptions:
            try:
                callback = subscription.callback

                # Check if callback is async
                if asyncio.iscoroutinefunction(callback):
                    # Schedule the coroutine
                    task = asyncio.create_task(callback(event))
                    tasks.append(task)
                else:
                    # Run sync callback
                    callback(event)
            except Exception as e:
                self._logger.error(
                    f'Error in event handler for {event.event_type}: {str(e)}',
                    extra={
                        'event_id': event.event_id,
                        'subscription_id': subscription.subscriber_id,
                        'error': str(e)
                    }
                )

        # Wait for all async tasks if there are any
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def subscribe(
            self,
            event_type: Union[EventType, str],
            callback: EventHandler,
            subscriber_id: Optional[str] = None,
            filter_criteria: Optional[Dict[str, Any]] = None
    ) -> str:
        """Subscribe to an event type asynchronously.

        Args:
            event_type: Type of events to subscribe to
            callback: Callback function or coroutine for handling events
            subscriber_id: ID of the subscriber (generated if not provided)
            filter_criteria: Optional criteria for filtering events

        Returns:
            The subscriber ID

        Raises:
            EventBusError: If subscription fails
        """
        if not self._initialized:
            raise EventBusError(
                'Cannot subscribe to events before initialization',
                event_type=str(event_type)
            )

        if isinstance(event_type, EventType):
            event_type_str = event_type.value
        else:
            event_type_str = event_type

        if subscriber_id is None:
            subscriber_id = str(uuid.uuid4())

        subscription = EventSubscription(
            subscriber_id=subscriber_id,
            event_type=event_type_str,
            callback=callback,
            filter_criteria=filter_criteria
        )

        async with self._subscription_lock:
            if event_type_str not in self._subscriptions:
                self._subscriptions[event_type_str] = {}

            self._subscriptions[event_type_str][subscriber_id] = subscription

        self._logger.debug(
            f'Subscription added for {event_type_str}',
            extra={'subscriber_id': subscriber_id, 'has_filter': filter_criteria is not None}
        )

        return subscriber_id

    async def unsubscribe(
            self,
            subscriber_id: str,
            event_type: Optional[Union[EventType, str]] = None
    ) -> bool:
        """Unsubscribe from events asynchronously.

        Args:
            subscriber_id: ID of the subscriber
            event_type: Optional specific event type to unsubscribe from

        Returns:
            True if unsubscribed, False otherwise
        """
        if not self._initialized:
            return False

        event_type_str = None
        if event_type is not None:
            if isinstance(event_type, EventType):
                event_type_str = event_type.value
            else:
                event_type_str = event_type

        removed = False

        async with self._subscription_lock:
            if event_type_str is not None:
                # Unsubscribe from specific event type
                if event_type_str in self._subscriptions and subscriber_id in self._subscriptions[event_type_str]:
                    del self._subscriptions[event_type_str][subscriber_id]
                    removed = True

                    # Clean up empty event types
                    if not self._subscriptions[event_type_str]:
                        del self._subscriptions[event_type_str]
            else:
                # Unsubscribe from all event types
                for evt_type in list(self._subscriptions.keys()):
                    if subscriber_id in self._subscriptions[evt_type]:
                        del self._subscriptions[evt_type][subscriber_id]
                        removed = True

                        # Clean up empty event types
                        if not self._subscriptions[evt_type]:
                            del self._subscriptions[evt_type]

        if removed:
            self._logger.debug(
                f"Unsubscribed {subscriber_id} from {event_type_str or 'all events'}"
            )

        return removed

    async def _get_matching_subscriptions(self, event: Event) -> List[EventSubscription]:
        """Get subscriptions matching an event asynchronously.

        Args:
            event: The event to match

        Returns:
            List of matching subscriptions
        """
        matching: List[EventSubscription] = []

        async with self._subscription_lock:
            # Check for exact event type matches
            if event.event_type in self._subscriptions:
                for subscription in self._subscriptions[event.event_type].values():
                    if subscription.matches_event(event):
                        matching.append(subscription)

            # Check for wildcard subscriptions
            if '*' in self._subscriptions:
                for subscription in self._subscriptions['*'].values():
                    if subscription.matches_event(event):
                        matching.append(subscription)

        return matching

    async def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes asynchronously.

        Args:
            key: The configuration key that changed
            value: The new value
        """
        if key == 'event_bus_manager.max_queue_size':
            self._logger.warning(
                'Cannot change event queue size at runtime, restart required',
                extra={'current_size': self._max_queue_size, 'new_size': value}
            )
        elif key == 'event_bus_manager.publish_timeout':
            self._publish_timeout = float(value)
            self._logger.info(
                f'Updated event publish timeout to {self._publish_timeout} seconds'
            )
        elif key == 'event_bus_manager.thread_pool_size':
            self._logger.warning(
                'Cannot change worker pool size at runtime, restart required',
                extra={'current_size': len(self._worker_tasks), 'new_size': value}
            )

    async def shutdown(self) -> None:
        """Shut down the event bus manager asynchronously.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Event Bus Manager')

            # Stop accepting new events
            self._running = False
            self._stop_event.set()

            # Wait for queue to be processed
            if self._event_queue is not None:
                try:
                    await asyncio.wait_for(self._event_queue.join(), timeout=5.0)
                except asyncio.TimeoutError:
                    self._logger.warning('Event queue not fully processed during shutdown')
                except Exception as e:
                    self._logger.error(f'Error waiting for event queue: {str(e)}')

            # Cancel all worker tasks
            for task in self._worker_tasks:
                task.cancel()

            # Wait for all tasks to be cancelled
            if self._worker_tasks:
                await asyncio.gather(*self._worker_tasks, return_exceptions=True)

            self._worker_tasks.clear()

            # Clear subscriptions
            async with self._subscription_lock:
                self._subscriptions.clear()

            # Unregister config listener
            await self._config_manager.unregister_listener('event_bus_manager', self._on_config_changed)

            self._initialized = False
            self._healthy = False

            self._logger.info('Event Bus Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Event Bus Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down AsyncEventBusManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the event bus manager.

        Returns:
            Dictionary with status information
        """
        status = super().status()

        if self._initialized:
            # Get subscription stats
            total_subscriptions = 0
            unique_subscribers: Set[str] = set()

            for subs in self._subscriptions.values():
                total_subscriptions += len(subs)
                unique_subscribers.update(subs.keys())

            # Get queue stats
            queue_size = 0
            queue_full = False

            if self._event_queue:
                queue_size = self._event_queue.qsize()
                queue_full = self._event_queue.full()

            status.update({
                'subscriptions': {
                    'total': total_subscriptions,
                    'unique_subscribers': len(unique_subscribers),
                    'event_types': len(self._subscriptions)
                },
                'queue': {
                    'size': queue_size,
                    'capacity': self._max_queue_size,
                    'full': queue_full
                },
                'workers': {
                    'count': len(self._worker_tasks),
                    'running': self._running
                }
            })

        return status