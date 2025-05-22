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
    def __init__(self, config_manager: Any, logger_manager: Any, thread_manager: Any) -> None:
        super().__init__(name='event_bus_manager')
        self._config_manager = config_manager
        self._logger_manager = logger_manager
        self._logger = logger_manager.get_logger('event_bus_manager')
        self._thread_manager = thread_manager
        self._max_queue_size: int = 1000
        self._publish_timeout: float = 5.0
        self._subscriptions: Dict[str, Dict[str, EventSubscription]] = {}
        self._subscription_lock = asyncio.Lock()
        self._event_queue: Optional[asyncio.Queue[Tuple[Event, List[EventSubscription]]]] = None
        self._worker_tasks: List[asyncio.Task] = []
        self._running: bool = False
        self._stop_event = asyncio.Event()
    async def initialize(self) -> None:
        try:
            event_bus_config = await self._config_manager.get('event_bus_manager', {})
            if not event_bus_config:
                self._logger.error('Event Bus configuration not found in configuration')
            if not hasattr(event_bus_config, 'max_queue_size'):
                self._logger.warning('Event Bus configuration max_queue_size not found in configuration')
            if not hasattr(event_bus_config, 'publish_timeout'):
                self._logger.warning('Event Bus configuration publish_timeout not found in configuration')
            if not hasattr(event_bus_config, 'thread_pool_size'):
                self._logger.warning('Event Bus configuration thread_pool_size not found in configuration')
            self._max_queue_size = event_bus_config.get('max_queue_size', 1000)
            self._publish_timeout = event_bus_config.get('publish_timeout', 5.0)
            thread_pool_size = event_bus_config.get('thread_pool_size', 4)
            self._event_queue = asyncio.Queue(maxsize=self._max_queue_size)
            self._running = True
            for i in range(thread_pool_size):
                worker = asyncio.create_task(self._event_worker(i), name=f'event-worker-{i}')
                self._worker_tasks.append(worker)
            await self._config_manager.register_listener('event_bus_manager', self._on_config_changed)
            self._logger.info('Event Bus Manager initialized')
            self._initialized = True
            self._healthy = True
        except Exception as e:
            self._logger.error(f'Failed to initialize Event Bus Manager: {str(e)}')
            raise ManagerInitializationError(f'Failed to initialize AsyncEventBusManager: {str(e)}', manager_name=self.name) from e
    async def _event_worker(self, worker_id: int) -> None:
        self._logger.debug(f'Event worker {worker_id} started')
        while self._running and (not self._stop_event.is_set()):
            try:
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
                            def dispatch() -> None:
                                if inspect.iscoroutinefunction(callback):
                                    asyncio.create_task(callback(event))
                                else:
                                    callback(event)
                            await self._thread_manager.run_on_main_thread(dispatch)
                        elif inspect.iscoroutinefunction(callback):
                            task = asyncio.create_task(callback(event), name=f'event-{event.event_type}-{subscription.subscriber_id}')
                            background_tasks.append(task)
                        else:
                            callback(event)
                    except Exception as e:
                        self._logger.error(f'Error in event handler for {event.event_type}: {e}', extra={'event_id': event.event_id, 'subscription_id': subscription.subscriber_id, 'error': str(e)})
                if background_tasks:
                    results = await asyncio.gather(*background_tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, Exception):
                            self._logger.error(f'Unhandled exception in async handler: {result}')
            finally:
                self._event_queue.task_done()
        self._logger.debug(f'Event worker {worker_id} stopped')
    async def publish(self, event_type: Union[EventType, str], source: str, payload: Optional[Dict[str, Any]]=None, correlation_id: Optional[str]=None, synchronous: bool=False) -> str:
        if not self._initialized:
            raise EventBusError('Cannot publish events before initialization', event_type=str(event_type))
        if isinstance(event_type, EventType):
            event_type = event_type.value
        event = Event.create(event_type=event_type, source=source, payload=payload or {}, correlation_id=correlation_id)
        matching_subs = await self._get_matching_subscriptions(event)
        if not matching_subs:
            self._logger.debug(f'No subscribers for event {event.event_type}', extra={'event_id': event.event_id})
            return event.event_id
        if synchronous:
            await self._process_event_sync(event, matching_subs)
        else:
            try:
                if self._event_queue is None:
                    raise EventBusError('Event queue is not initialized', event_type=str(event_type))
                try:
                    await asyncio.wait_for(self._event_queue.put((event, matching_subs)), timeout=self._publish_timeout)
                except asyncio.TimeoutError:
                    self._logger.error(f'Event queue is full, cannot publish event {event.event_type}', extra={'event_id': event.event_id})
                    raise EventBusError(f'Event queue is full, cannot publish event {event.event_type}', event_type=str(event_type))
            except EventBusError:
                raise
            except Exception as e:
                self._logger.error(f'Error publishing event {event.event_type}: {str(e)}', extra={'event_id': event.event_id})
                raise EventBusError(f'Error publishing event {event.event_type}: {str(e)}', event_type=str(event_type)) from e
        self._logger.debug(f'Published event {event.event_type}', extra={'event_id': event.event_id, 'source': source, 'subscribers': len(matching_subs), 'synchronous': synchronous})
        return event.event_id
    async def _process_event_sync(self, event: Event, subscriptions: List[EventSubscription]) -> None:
        tasks = []
        for subscription in subscriptions:
            try:
                callback = subscription.callback
                if asyncio.iscoroutinefunction(callback):
                    task = asyncio.create_task(callback(event))
                    tasks.append(task)
                else:
                    callback(event)
            except Exception as e:
                self._logger.error(f'Error in event handler for {event.event_type}: {str(e)}', extra={'event_id': event.event_id, 'subscription_id': subscription.subscriber_id, 'error': str(e)})
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    async def subscribe(self, event_type: Union[EventType, str], callback: EventHandler, subscriber_id: Optional[str]=None, filter_criteria: Optional[Dict[str, Any]]=None) -> str:
        if not self._initialized:
            raise EventBusError('Cannot subscribe to events before initialization', event_type=str(event_type))
        if isinstance(event_type, EventType):
            event_type_str = event_type.value
        else:
            event_type_str = event_type
        if subscriber_id is None:
            subscriber_id = str(uuid.uuid4())
        subscription = EventSubscription(subscriber_id=subscriber_id, event_type=event_type_str, callback=callback, filter_criteria=filter_criteria)
        async with self._subscription_lock:
            if event_type_str not in self._subscriptions:
                self._subscriptions[event_type_str] = {}
            self._subscriptions[event_type_str][subscriber_id] = subscription
        self._logger.debug(f'Subscription added for {event_type_str}', extra={'subscriber_id': subscriber_id, 'has_filter': filter_criteria is not None})
        return subscriber_id
    async def unsubscribe(self, subscriber_id: str, event_type: Optional[Union[EventType, str]]=None) -> bool:
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
                if event_type_str in self._subscriptions and subscriber_id in self._subscriptions[event_type_str]:
                    del self._subscriptions[event_type_str][subscriber_id]
                    removed = True
                    if not self._subscriptions[event_type_str]:
                        del self._subscriptions[event_type_str]
            else:
                for evt_type in list(self._subscriptions.keys()):
                    if subscriber_id in self._subscriptions[evt_type]:
                        del self._subscriptions[evt_type][subscriber_id]
                        removed = True
                        if not self._subscriptions[evt_type]:
                            del self._subscriptions[evt_type]
        if removed:
            self._logger.debug(f"Unsubscribed {subscriber_id} from {event_type_str or 'all events'}")
        return removed
    async def _get_matching_subscriptions(self, event: Event) -> List[EventSubscription]:
        matching: List[EventSubscription] = []
        async with self._subscription_lock:
            if event.event_type in self._subscriptions:
                for subscription in self._subscriptions[event.event_type].values():
                    if subscription.matches_event(event):
                        matching.append(subscription)
            if '*' in self._subscriptions:
                for subscription in self._subscriptions['*'].values():
                    if subscription.matches_event(event):
                        matching.append(subscription)
        return matching
    async def _on_config_changed(self, key: str, value: Any) -> None:
        if key == 'event_bus_manager.max_queue_size':
            self._logger.warning('Cannot change event queue size at runtime, restart required', extra={'current_size': self._max_queue_size, 'new_size': value})
        elif key == 'event_bus_manager.publish_timeout':
            self._publish_timeout = float(value)
            self._logger.info(f'Updated event publish timeout to {self._publish_timeout} seconds')
        elif key == 'event_bus_manager.thread_pool_size':
            self._logger.warning('Cannot change worker pool size at runtime, restart required', extra={'current_size': len(self._worker_tasks), 'new_size': value})
    async def shutdown(self) -> None:
        if not self._initialized:
            return
        try:
            self._logger.info('Shutting down Event Bus Manager')
            self._running = False
            self._stop_event.set()
            if self._event_queue is not None:
                try:
                    await asyncio.wait_for(self._event_queue.join(), timeout=5.0)
                except asyncio.TimeoutError:
                    self._logger.warning('Event queue not fully processed during shutdown')
                except Exception as e:
                    self._logger.error(f'Error waiting for event queue: {str(e)}')
            for task in self._worker_tasks:
                task.cancel()
            if self._worker_tasks:
                await asyncio.gather(*self._worker_tasks, return_exceptions=True)
            self._worker_tasks.clear()
            async with self._subscription_lock:
                self._subscriptions.clear()
            await self._config_manager.unregister_listener('event_bus_manager', self._on_config_changed)
            self._initialized = False
            self._healthy = False
            self._logger.info('Event Bus Manager shut down successfully')
        except Exception as e:
            self._logger.error(f'Failed to shut down Event Bus Manager: {str(e)}')
            raise ManagerShutdownError(f'Failed to shut down AsyncEventBusManager: {str(e)}', manager_name=self.name) from e
    def status(self) -> Dict[str, Any]:
        status = super().status()
        if self._initialized:
            total_subscriptions = 0
            unique_subscribers: Set[str] = set()
            for subs in self._subscriptions.values():
                total_subscriptions += len(subs)
                unique_subscribers.update(subs.keys())
            queue_size = 0
            queue_full = False
            if self._event_queue:
                queue_size = self._event_queue.qsize()
                queue_full = self._event_queue.full()
            status.update({'subscriptions': {'total': total_subscriptions, 'unique_subscribers': len(unique_subscribers), 'event_types': len(self._subscriptions)}, 'queue': {'size': queue_size, 'capacity': self._max_queue_size, 'full': queue_full}, 'workers': {'count': len(self._worker_tasks), 'running': self._running}})
        return status