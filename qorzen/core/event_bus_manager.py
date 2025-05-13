from __future__ import annotations
import concurrent.futures
import queue
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast

from qorzen.core.base import QorzenManager
from qorzen.core.event_model import Event, EventSubscription, EventHandler, EventType
from qorzen.utils.exceptions import EventBusError, ManagerInitializationError, ManagerShutdownError


class EventBusManager(QorzenManager):
    """Manager for the application event bus.

    This manager handles event publishing and subscription, allowing components
    to communicate via a pub/sub pattern.
    """

    def __init__(self, config_manager: Any, logger_manager: Any, thread_manager: Any) -> None:
        """Initialize the event bus manager.

        Args:
            config_manager: Configuration manager
            logger_manager: Logger manager
        """
        super().__init__(name='event_bus_manager')
        self._config_manager = config_manager
        self._logger_manager = logger_manager
        self._logger = logger_manager.get_logger('event_bus')
        self._thread_manager = thread_manager

        # Threading and queuing
        self._thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._max_queue_size = 1000
        self._publish_timeout = 5.0

        # Subscriptions
        self._subscriptions: Dict[str, Dict[str, EventSubscription]] = {}
        self._subscription_lock = threading.RLock()

        # Event queue
        self._event_queue: Optional[queue.Queue] = None
        self._worker_threads: List[threading.Thread] = []
        self._running = False
        self._stop_event = threading.Event()

    def initialize(self) -> None:
        """Initialize the event bus manager.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            # Load configuration
            event_bus_config = self._config_manager.get('event_bus_manager', {})
            thread_pool_size = event_bus_config.get('thread_pool_size', 4)
            self._max_queue_size = event_bus_config.get('max_queue_size', 1000)
            self._publish_timeout = event_bus_config.get('publish_timeout', 5.0)

            # Initialize thread pool and event queue
            self._thread_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=thread_pool_size,
                thread_name_prefix='event-worker'
            )
            self._event_queue = queue.Queue(maxsize=self._max_queue_size)
            self._running = True

            # Start worker threads
            for i in range(thread_pool_size):
                worker = threading.Thread(
                    target=self._event_worker,
                    name=f'event-worker-{i}',
                    daemon=True
                )
                worker.start()
                self._worker_threads.append(worker)

            # Register for configuration changes
            self._config_manager.register_listener('event_bus', self._on_config_changed)

            self._logger.info('Event Bus Manager initialized')
            self._initialized = True
            self._healthy = True

        except Exception as e:
            self._logger.error(f'Failed to initialize Event Bus Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize EventBusManager: {str(e)}',
                manager_name=self.name
            ) from e

    # In event_bus_manager.py
    def _event_worker(self) -> None:
        while self._running and (not self._stop_event.is_set()):
            try:
                event, subscriptions = self._event_queue.get(timeout=0.1)
                try:
                    # Check if this event needs main thread handling
                    needs_main_thread = EventType.requires_main_thread(event.event_type)

                    for subscription in subscriptions:
                        try:
                            # Process UI-related events on the main thread
                            if needs_main_thread and self._thread_manager:
                                self._thread_manager.run_on_main_thread(
                                    lambda s=subscription, e=event: s.callback(e)
                                )
                            else:
                                # Process other events normally
                                subscription.callback(event)
                        except Exception as e:
                            self._logger.error(f'Error in event handler for {event.event_type}: {str(e)}',
                                               extra={'event_id': event.event_id,
                                                      'subscription_id': subscription.subscriber_id,
                                                      'error': str(e)})
                finally:
                    self._event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self._logger.error(f'Unexpected error in event worker: {str(e)}')

    def publish(self, event_type: Union[EventType, str], source: str,
                payload: Optional[Dict[str, Any]] = None,
                correlation_id: Optional[str] = None,
                synchronous: bool = False) -> str:
        """Publish an event to the event bus.

        Args:
            event_type: Type of the event (enum or string)
            source: Source of the event
            payload: Event payload data
            correlation_id: ID for tracking related events
            synchronous: If True, process event synchronously

        Returns:
            The event ID

        Raises:
            EventBusError: If the event cannot be published
        """
        if not self._initialized:
            raise EventBusError('Cannot publish events before initialization',
                                event_type=str(event_type))

        # Create the event
        if isinstance(event_type, EventType):
            event_type = event_type.value
        event = Event.create(
            event_type=event_type,
            source=source,
            payload=payload or {},
            correlation_id=correlation_id
        )

        # Find matching subscriptions
        matching_subs = self._get_matching_subscriptions(event)

        if not matching_subs:
            self._logger.debug(
                f'No subscribers for event {event.event_type}',
                extra={'event_id': event.event_id}
            )
            return event.event_id

        # Process the event
        if synchronous:
            self._process_event_sync(event, matching_subs)
        else:
            try:
                if self._event_queue is None:
                    raise EventBusError('Event queue is not initialized',
                                        event_type=str(event_type))

                self._event_queue.put(
                    (event, matching_subs),
                    block=True,
                    timeout=self._publish_timeout
                )
            except queue.Full:
                self._logger.error(
                    f'Event queue is full, cannot publish event {event.event_type}',
                    extra={'event_id': event.event_id}
                )
                raise EventBusError(
                    f'Event queue is full, cannot publish event {event.event_type}',
                    event_type=str(event_type)
                )

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

    def _process_event_sync(self, event: Event, subscriptions: List[EventSubscription]) -> None:
        """Process an event synchronously.

        Args:
            event: The event to process
            subscriptions: List of matching subscriptions
        """
        for subscription in subscriptions:
            try:
                subscription.callback(event)
            except Exception as e:
                self._logger.error(
                    f'Error in event handler for {event.event_type}: {str(e)}',
                    extra={
                        'event_id': event.event_id,
                        'subscription_id': subscription.subscriber_id,
                        'error': str(e)
                    }
                )

    def subscribe(self, event_type: Union[EventType, str],
                  callback: EventHandler,
                  subscriber_id: Optional[str] = None,
                  filter_criteria: Optional[Dict[str, Any]] = None) -> str:
        """Subscribe to events.

        Args:
            event_type: Type of events to subscribe to
            callback: Function to call when an event occurs
            subscriber_id: Optional ID for the subscriber
            filter_criteria: Optional criteria to filter events

        Returns:
            The subscriber ID

        Raises:
            EventBusError: If subscription fails
        """
        if not self._initialized:
            raise EventBusError('Cannot subscribe to events before initialization',
                                event_type=str(event_type))

        # Convert EventType enum to string if needed
        if isinstance(event_type, EventType):
            event_type_str = event_type.value
        else:
            event_type_str = event_type

        # Generate subscriber ID if not provided
        if subscriber_id is None:
            subscriber_id = str(uuid.uuid4())

        # Create subscription
        subscription = EventSubscription(
            subscriber_id=subscriber_id,
            event_type=event_type_str,
            callback=callback,
            filter_criteria=filter_criteria
        )

        # Add to subscriptions
        with self._subscription_lock:
            if event_type_str not in self._subscriptions:
                self._subscriptions[event_type_str] = {}

            self._subscriptions[event_type_str][subscriber_id] = subscription

        self._logger.debug(
            f'Subscription added for {event_type_str}',
            extra={
                'subscriber_id': subscriber_id,
                'has_filter': filter_criteria is not None
            }
        )

        return subscriber_id

    def unsubscribe(self, subscriber_id: str, event_type: Optional[Union[EventType, str]] = None) -> bool:
        """Unsubscribe from events.

        Args:
            subscriber_id: The subscriber ID to unsubscribe
            event_type: Optional event type to unsubscribe from

        Returns:
            True if unsubscribed successfully, False otherwise
        """
        if not self._initialized:
            return False

        # Convert EventType enum to string if needed
        event_type_str = None
        if event_type is not None:
            if isinstance(event_type, EventType):
                event_type_str = event_type.value
            else:
                event_type_str = event_type

        removed = False
        with self._subscription_lock:
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
            self._logger.debug(f"Unsubscribed {subscriber_id} from {event_type_str or 'all events'}")

        return removed

    def _get_matching_subscriptions(self, event: Event) -> List[EventSubscription]:
        """Get subscriptions matching an event.

        Args:
            event: The event to match

        Returns:
            List of matching subscriptions
        """
        matching: List[EventSubscription] = []

        with self._subscription_lock:
            # Check for subscriptions to this event type
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

    def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: Configuration key
            value: New configuration value
        """
        if key == 'event_bus.max_queue_size':
            self._logger.warning(
                'Cannot change event queue size at runtime, restart required',
                extra={'current_size': self._max_queue_size, 'new_size': value}
            )
        elif key == 'event_bus.publish_timeout':
            self._publish_timeout = float(value)
            self._logger.info(f'Updated event publish timeout to {self._publish_timeout} seconds')
        elif key == 'event_bus.thread_pool_size':
            self._logger.warning(
                'Cannot change thread pool size at runtime, restart required',
                extra={'current_size': len(self._worker_threads), 'new_size': value}
            )

    def shutdown(self) -> None:
        """Shut down the event bus manager.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Event Bus Manager')

            # Stop event processing
            self._running = False
            self._stop_event.set()

            # Wait for event queue to empty
            if self._event_queue is not None:
                try:
                    self._event_queue.join(timeout=5.0)
                except Exception:
                    pass

            # Shut down thread pool
            if self._thread_pool is not None:
                self._thread_pool.shutdown(wait=True, cancel_futures=True)

            # Clear subscriptions
            with self._subscription_lock:
                self._subscriptions.clear()

            # Unregister from configuration changes
            self._config_manager.unregister_listener('event_bus', self._on_config_changed)

            # Update state
            self._initialized = False
            self._healthy = False

            self._logger.info('Event Bus Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Event Bus Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down EventBusManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the event bus manager.

        Returns:
            Dictionary with status information
        """
        status = super().status()

        if self._initialized:
            with self._subscription_lock:
                total_subscriptions = sum((len(subs) for subs in self._subscriptions.values()))
                unique_subscribers: Set[str] = set()

                for subs in self._subscriptions.values():
                    unique_subscribers.update(subs.keys())

            queue_size = self._event_queue.qsize() if self._event_queue else 0
            queue_full = queue_size >= self._max_queue_size if self._event_queue else False

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
                'threads': {
                    'worker_count': len(self._worker_threads),
                    'running': self._running
                }
            })

        return status