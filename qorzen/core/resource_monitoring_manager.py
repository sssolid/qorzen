from __future__ import annotations

import asyncio
import datetime
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, cast

import psutil
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

from qorzen.core.base import QorzenManager
from qorzen.utils.exceptions import ManagerInitializationError, ManagerShutdownError


class AlertLevel(Enum):
    """Alert severity levels.

    Attributes:
        INFO: Informational alert
        WARNING: Warning alert
        ERROR: Error alert
        CRITICAL: Critical alert
    """
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


@dataclass
class Alert:
    """System alert information.

    Attributes:
        id: Unique alert ID
        level: Alert severity level
        message: Alert message
        source: Alert source
        timestamp: When the alert was created
        metric_name: Optional name of the related metric
        metric_value: Optional value of the related metric
        threshold: Optional threshold that triggered the alert
        resolved: Whether the alert is resolved
        resolved_at: When the alert was resolved
        metadata: Additional metadata
    """
    id: str
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime.datetime
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[datetime.datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceMonitoringManager(QorzenManager):
    """Asynchronous resource monitoring manager.

    This manager monitors system resources, collects metrics,
    and generates alerts when thresholds are exceeded.

    Attributes:
        _config_manager: Configuration manager
        _logger: Logger instance
        _event_bus_manager: Event bus manager
        _thread_manager: Thread management system
        _metrics: Dictionary of prometheus metrics
        _prometheus_server_port: Port for the prometheus server
        _alert_thresholds: Threshold values for alerts
        _alerts: Dictionary of active alerts
        _resolved_alerts: Queue of resolved alerts
    """

    def __init__(
            self,
            config_manager: Any,
            logger_manager: Any,
            event_bus_manager: Any,
            thread_manager: Any
    ) -> None:
        """Initialize the resource monitoring manager.

        Args:
            config_manager: Configuration manager
            logger_manager: Logging manager
            event_bus_manager: Event bus manager
            thread_manager: Thread management system
        """
        super().__init__(name='resource_monitoring_manager')
        self._config_manager = config_manager
        self._logger = logger_manager.get_logger('resource_monitoring_manager')
        self._event_bus_manager = event_bus_manager
        self._thread_manager = thread_manager

        # Prometheus metrics
        self._metrics: Dict[str, Any] = {}
        self._prometheus_server_port: Optional[int] = None
        self._cpu_percent_gauge: Optional[Gauge] = None
        self._memory_percent_gauge: Optional[Gauge] = None
        self._disk_percent_gauge: Optional[Gauge] = None

        # Alert system
        self._alert_thresholds: Dict[str, float] = {
            'cpu_percent': 80.0,
            'memory_percent': 80.0,
            'disk_percent': 90.0
        }
        self._alerts: Dict[str, Alert] = {}
        self._resolved_alerts: deque = deque(maxlen=100)
        self._alerts_lock = asyncio.Lock()

        # Collection configuration
        self._metrics_interval_seconds = 10
        self._collection_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self) -> None:
        """Initialize the resource monitoring manager asynchronously.

        Sets up metrics collection and prometheus server.

        Raises:
            ManagerInitializationError: If initialization fails
        """
        try:
            monitoring_config = await self._config_manager.get('monitoring', {})

            # Check if monitoring is enabled
            enabled = monitoring_config.get('enabled', True)
            if not enabled:
                self._logger.info('Resource Monitoring is disabled in configuration')
                self._initialized = True
                self._healthy = True
                return

            # Configure prometheus
            prometheus_config = monitoring_config.get('prometheus', {})
            prometheus_enabled = prometheus_config.get('enabled', True)
            prometheus_port = prometheus_config.get('port', 9090)

            # Set alert thresholds
            alert_thresholds = monitoring_config.get('alert_thresholds', {})
            self._alert_thresholds.update(alert_thresholds)

            # Set metrics collection interval
            self._metrics_interval_seconds = monitoring_config.get('metrics_interval_seconds', 10)

            # Initialize prometheus metrics
            if prometheus_enabled:
                self._cpu_percent_gauge = Gauge('system_cpu_percent', 'System CPU usage percentage')
                self._memory_percent_gauge = Gauge('system_memory_percent', 'System memory usage percentage')
                self._disk_percent_gauge = Gauge('system_disk_percent', 'System disk usage percentage')

                self._metrics['app_uptime_seconds'] = Gauge('app_uptime_seconds', 'Application uptime in seconds')
                self._metrics['events_total'] = Counter('events_total', 'Total number of events processed',
                                                        ['event_type', 'source'])
                self._metrics['event_processing_seconds'] = Histogram('event_processing_seconds',
                                                                      'Event processing time in seconds',
                                                                      ['event_type'])

                # Start prometheus server
                start_http_server(prometheus_port)
                self._prometheus_server_port = prometheus_port
                self._logger.info(f'Started Prometheus metrics server on port {prometheus_port}')

            # Subscribe to all events for metrics
            await self._event_bus_manager.subscribe(
                event_type='*',
                callback=self._on_event,
                subscriber_id='monitoring_manager'
            )

            # Register configuration listener
            await self._config_manager.register_listener('monitoring', self._on_config_changed)

            # Start metric collection tasks
            await self._schedule_metric_collection()

            # Publish initialization event
            await self._event_bus_manager.publish(
                event_type='monitoring/initialized',
                source='monitoring_manager',
                payload={'prometheus_port': self._prometheus_server_port}
            )

            self._initialized = True
            self._healthy = True

            self._logger.info('Resource Monitoring Manager initialized')

        except Exception as e:
            self._logger.error(f'Failed to initialize Resource Monitoring Manager: {str(e)}')
            raise ManagerInitializationError(
                f'Failed to initialize AsyncResourceMonitoringManager: {str(e)}',
                manager_name=self.name
            ) from e

    async def _schedule_metric_collection(self) -> None:
        """Schedule tasks for collecting metrics."""
        # Cancel any existing tasks
        for task in self._collection_tasks.values():
            task.cancel()
        self._collection_tasks.clear()

        # Create system metrics collection task
        system_metrics_task = asyncio.create_task(
            self._collect_system_metrics_loop(),
            name='system_metrics_collection'
        )
        self._collection_tasks['system_metrics'] = system_metrics_task

        # Create uptime metrics collection task
        uptime_task = asyncio.create_task(
            self._collect_uptime_metrics_loop(),
            name='uptime_metrics_collection'
        )
        self._collection_tasks['uptime'] = uptime_task

    async def _collect_system_metrics_loop(self) -> None:
        """Continuously collect system metrics."""
        while self._initialized and self._healthy:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self._metrics_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f'Error in system metrics collection loop: {str(e)}')
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _collect_uptime_metrics_loop(self) -> None:
        """Continuously collect uptime metrics."""
        while self._initialized and self._healthy:
            try:
                await self._collect_uptime_metrics()
                await asyncio.sleep(60)  # Update uptime every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f'Error in uptime metrics collection loop: {str(e)}')
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _collect_system_metrics(self) -> None:
        """Collect system resource metrics.

        Gathers CPU, memory, and disk usage and updates prometheus metrics.
        """
        try:
            # Run CPU collection in executor (it's blocking)
            loop = asyncio.get_running_loop()
            cpu_percent = await loop.run_in_executor(None, psutil.cpu_percent, 1)

            # Update CPU gauge
            if self._cpu_percent_gauge:
                if self._thread_manager and not self._thread_manager.is_main_thread():
                    await self._thread_manager.run_on_main_thread(
                        lambda: self._cpu_percent_gauge.set(cpu_percent)
                    )
                else:
                    self._cpu_percent_gauge.set(cpu_percent)

            # Get memory info
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Update memory gauge
            if self._memory_percent_gauge:
                if self._thread_manager and not self._thread_manager.is_main_thread():
                    await self._thread_manager.run_on_main_thread(
                        lambda: self._memory_percent_gauge.set(memory_percent)
                    )
                else:
                    self._memory_percent_gauge.set(memory_percent)

            # Get disk info
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Update disk gauge
            if self._disk_percent_gauge:
                if self._thread_manager and not self._thread_manager.is_main_thread():
                    await self._thread_manager.run_on_main_thread(
                        lambda: self._disk_percent_gauge.set(disk_percent)
                    )
                else:
                    self._disk_percent_gauge.set(disk_percent)

            # Check alert thresholds
            await self._check_threshold('cpu_percent', cpu_percent)
            await self._check_threshold('memory_percent', memory_percent)
            await self._check_threshold('disk_percent', disk_percent)

            # Publish metrics event
            await self._event_bus_manager.publish(
                event_type='monitoring/metrics',
                source='monitoring_manager',
                payload={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'timestamp': time.time()
                }
            )

        except Exception as e:
            self._logger.error(f'Error collecting system metrics: {str(e)}')

    async def _collect_uptime_metrics(self) -> None:
        """Collect application uptime metrics."""
        try:
            # Get process uptime
            process = psutil.Process()
            uptime_seconds = time.time() - process.create_time()

            # Update uptime gauge
            if 'app_uptime_seconds' in self._metrics:
                if self._thread_manager and not self._thread_manager.is_main_thread():
                    await self._thread_manager.run_on_main_thread(
                        lambda: self._metrics['app_uptime_seconds'].set(uptime_seconds)
                    )
                else:
                    self._metrics['app_uptime_seconds'].set(uptime_seconds)

        except Exception as e:
            self._logger.error(f'Error collecting uptime metrics: {str(e)}')

    async def _check_threshold(self, metric_name: str, value: float) -> None:
        """Check if a metric exceeds its threshold and create alerts if needed.

        Args:
            metric_name: Name of the metric
            value: Current value
        """
        if metric_name not in self._alert_thresholds:
            return

        threshold = self._alert_thresholds[metric_name]

        if value >= threshold * 1.25:
            # Critical alert
            await self._create_alert(
                level=AlertLevel.CRITICAL,
                message=f"{metric_name.replace('_', ' ').title()} is critically high: {value:.1f}%",
                source='monitoring_manager',
                metric_name=metric_name,
                metric_value=value,
                threshold=threshold
            )
        elif value >= threshold:
            # Warning alert
            await self._create_alert(
                level=AlertLevel.WARNING,
                message=f"{metric_name.replace('_', ' ').title()} is high: {value:.1f}%",
                source='monitoring_manager',
                metric_name=metric_name,
                metric_value=value,
                threshold=threshold
            )
        else:
            # No alert, resolve any existing alerts for this metric
            await self._resolve_alerts_for_metric(metric_name)

    async def _create_alert(
            self,
            level: AlertLevel,
            message: str,
            source: str,
            metric_name: Optional[str] = None,
            metric_value: Optional[float] = None,
            threshold: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new alert or update an existing one.

        Args:
            level: Alert severity level
            message: Alert message
            source: Alert source
            metric_name: Name of the related metric
            metric_value: Value of the related metric
            threshold: Threshold that triggered the alert
            metadata: Additional metadata

        Returns:
            Alert ID
        """
        import uuid

        # Check if an alert for this metric already exists
        if metric_name:
            async with self._alerts_lock:
                for existing_alert in self._alerts.values():
                    if (
                            existing_alert.metric_name == metric_name
                            and existing_alert.level == level
                            and not existing_alert.resolved
                    ):
                        # Update existing alert
                        existing_alert.timestamp = datetime.datetime.now()
                        existing_alert.metric_value = metric_value

                        self._logger.debug(
                            f'Updated existing alert for {metric_name}: {message}',
                            extra={'alert_id': existing_alert.id, 'level': level.value}
                        )

                        return existing_alert.id

        # Create new alert
        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            level=level,
            message=message,
            source=source,
            timestamp=datetime.datetime.now(),
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold,
            metadata=metadata or {}
        )

        # Store alert
        async with self._alerts_lock:
            self._alerts[alert_id] = alert

        # Log alert based on level
        log_method = {
            AlertLevel.INFO: self._logger.info,
            AlertLevel.WARNING: self._logger.warning,
            AlertLevel.ERROR: self._logger.error,
            AlertLevel.CRITICAL: self._logger.critical
        }.get(level, self._logger.warning)

        log_method(
            f'Alert: {message}',
            extra={
                'alert_id': alert_id,
                'level': level.value,
                'metric_name': metric_name,
                'metric_value': metric_value,
                'threshold': threshold
            }
        )

        # Publish alert event
        await self._event_bus_manager.publish(
            event_type='monitoring/alert',
            source='monitoring_manager',
            payload={
                'alert_id': alert_id,
                'level': level.value,
                'message': message,
                'timestamp': alert.timestamp.isoformat(),
                'metric_name': metric_name,
                'metric_value': metric_value,
                'threshold': threshold
            }
        )

        return alert_id

    async def _resolve_alerts_for_metric(self, metric_name: str) -> None:
        """Resolve all alerts for a metric.

        Args:
            metric_name: Name of the metric
        """
        async with self._alerts_lock:
            for alert_id, alert in list(self._alerts.items()):
                if alert.metric_name == metric_name and not alert.resolved:
                    # Mark alert as resolved
                    alert.resolved = True
                    alert.resolved_at = datetime.datetime.now()

                    # Move to resolved alerts queue
                    self._resolved_alerts.append(alert)
                    del self._alerts[alert_id]

                    self._logger.info(
                        f'Resolved alert for {metric_name}',
                        extra={'alert_id': alert_id, 'level': alert.level.value}
                    )

                    # Publish alert resolved event
                    await self._event_bus_manager.publish(
                        event_type='monitoring/alert_resolved',
                        source='monitoring_manager',
                        payload={
                            'alert_id': alert_id,
                            'metric_name': metric_name,
                            'resolved_at': alert.resolved_at.isoformat()
                        }
                    )

    async def _on_event(self, event: Any) -> None:
        """Handle events for metrics collection.

        Args:
            event: The event to record
        """
        if 'events_total' in self._metrics:
            if self._thread_manager and not self._thread_manager.is_main_thread():
                await self._thread_manager.run_on_main_thread(
                    lambda: self._metrics['events_total'].labels(
                        event_type=event.event_type,
                        source=event.source
                    ).inc()
                )
            else:
                self._metrics['events_total'].labels(
                    event_type=event.event_type,
                    source=event.source
                ).inc()

    async def _on_config_changed(self, key: str, value: Any) -> None:
        """Handle configuration changes.

        Args:
            key: Configuration key
            value: New value
        """
        if key == 'monitoring.enabled':
            self._logger.warning(
                'Changing monitoring.enabled requires restart to take effect',
                extra={'enabled': value}
            )
        elif key.startswith('monitoring.alert_thresholds.'):
            threshold_name = key.split('.')[-1]
            if threshold_name in self._alert_thresholds:
                self._alert_thresholds[threshold_name] = float(value)
                self._logger.info(
                    f'Updated alert threshold for {threshold_name}: {value}',
                    extra={'threshold': threshold_name, 'value': value}
                )
        elif key == 'monitoring.metrics_interval_seconds':
            old_interval = self._metrics_interval_seconds
            self._metrics_interval_seconds = value
            self._logger.info(
                f'Updated metrics interval: {value}s',
                extra={'old_interval': old_interval, 'new_interval': value}
            )

            # Restart metric collection tasks with new interval
            await self._schedule_metric_collection()

    async def register_gauge(
            self,
            name: str,
            description: str,
            labels: Optional[List[str]] = None
    ) -> Any:
        """Register a new gauge metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names

        Returns:
            The created gauge

        Raises:
            ValueError: If registration fails
        """
        if not self._initialized:
            raise ValueError('AsyncResourceMonitoringManager is not initialized')

        if name in self._metrics:
            raise ValueError(f"Metric '{name}' is already registered")

        gauge = Gauge(name, description, labels or [])
        self._metrics[name] = gauge

        return gauge

    async def register_counter(
            self,
            name: str,
            description: str,
            labels: Optional[List[str]] = None
    ) -> Any:
        """Register a new counter metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names

        Returns:
            The created counter

        Raises:
            ValueError: If registration fails
        """
        if not self._initialized:
            raise ValueError('AsyncResourceMonitoringManager is not initialized')

        if name in self._metrics:
            raise ValueError(f"Metric '{name}' is already registered")

        counter = Counter(name, description, labels or [])
        self._metrics[name] = counter

        return counter

    async def register_histogram(
            self,
            name: str,
            description: str,
            labels: Optional[List[str]] = None,
            buckets: Optional[List[float]] = None
    ) -> Any:
        """Register a new histogram metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names
            buckets: Optional histogram buckets

        Returns:
            The created histogram

        Raises:
            ValueError: If registration fails
        """
        if not self._initialized:
            raise ValueError('AsyncResourceMonitoringManager is not initialized')

        if name in self._metrics:
            raise ValueError(f"Metric '{name}' is already registered")

        histogram = Histogram(name, description, labels or [], buckets=buckets)
        self._metrics[name] = histogram

        return histogram

    async def register_summary(
            self,
            name: str,
            description: str,
            labels: Optional[List[str]] = None
    ) -> Any:
        """Register a new summary metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names

        Returns:
            The created summary

        Raises:
            ValueError: If registration fails
        """
        if not self._initialized:
            raise ValueError('AsyncResourceMonitoringManager is not initialized')

        if name in self._metrics:
            raise ValueError(f"Metric '{name}' is already registered")

        summary = Summary(name, description, labels or [])
        self._metrics[name] = summary

        return summary

    async def get_alerts(
            self,
            include_resolved: bool = False,
            level: Optional[AlertLevel] = None,
            metric_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get alerts matching criteria.

        Args:
            include_resolved: Whether to include resolved alerts
            level: Optional filter by alert level
            metric_name: Optional filter by metric name

        Returns:
            List of alerts as dictionaries
        """
        result = []

        async with self._alerts_lock:
            # Get active alerts
            for alert in self._alerts.values():
                if (level is None or alert.level == level) and (
                        metric_name is None or alert.metric_name == metric_name):
                    result.append({
                        'id': alert.id,
                        'level': alert.level.value,
                        'message': alert.message,
                        'source': alert.source,
                        'timestamp': alert.timestamp.isoformat(),
                        'metric_name': alert.metric_name,
                        'metric_value': alert.metric_value,
                        'threshold': alert.threshold,
                        'resolved': alert.resolved,
                        'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                        'metadata': alert.metadata
                    })

            # Get resolved alerts if requested
            if include_resolved:
                for alert in self._resolved_alerts:
                    if (level is None or alert.level == level) and (
                            metric_name is None or alert.metric_name == metric_name):
                        result.append({
                            'id': alert.id,
                            'level': alert.level.value,
                            'message': alert.message,
                            'source': alert.source,
                            'timestamp': alert.timestamp.isoformat(),
                            'metric_name': alert.metric_name,
                            'metric_value': alert.metric_value,
                            'threshold': alert.threshold,
                            'resolved': alert.resolved,
                            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                            'metadata': alert.metadata
                        })

        # Sort by timestamp, newest first
        result.sort(key=lambda x: x['timestamp'], reverse=True)

        return result

    async def generate_diagnostic_report(self) -> Dict[str, Any]:
        """Generate a diagnostic report of system status.

        Returns:
            Dictionary with diagnostic information
        """
        if not self._initialized:
            return {'error': 'MonitoringManager not initialized'}

        try:
            # Run CPU collection in executor (it's blocking)
            loop = asyncio.get_running_loop()
            cpu_percent = await loop.run_in_executor(None, psutil.cpu_percent, 1)

            # Get memory and disk info
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Get process info
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = await loop.run_in_executor(None, process.cpu_percent, 1)

            # Build report
            report = {
                'timestamp': datetime.datetime.now().isoformat(),
                'system': {
                    'cpu': {
                        'percent': cpu_percent
                    },
                    'memory': {
                        'total_mb': memory.total / (1024 * 1024),
                        'available_mb': memory.available / (1024 * 1024),
                        'used_mb': memory.used / (1024 * 1024),
                        'percent': memory.percent
                    },
                    'disk': {
                        'total_gb': disk.total / (1024 * 1024 * 1024),
                        'free_gb': disk.free / (1024 * 1024 * 1024),
                        'used_gb': disk.used / (1024 * 1024 * 1024),
                        'percent': disk.percent
                    }
                },
                'process': {
                    'pid': process.pid,
                    'cpu_percent': process_cpu,
                    'memory_mb': process_memory.rss / (1024 * 1024),
                    'uptime_seconds': time.time() - process.create_time(),
                    'threads': process.num_threads()
                },
                'alerts': {
                    'active': len(self._alerts),
                    'resolved': len(self._resolved_alerts)
                },
                'thresholds': self._alert_thresholds
            }

            return report

        except Exception as e:
            self._logger.error(f'Error generating diagnostic report: {str(e)}')
            return {'error': f'Failed to generate report: {str(e)}'}

    async def shutdown(self) -> None:
        """Shut down the resource monitoring manager asynchronously.

        Cancels collection tasks and unregisters listeners.

        Raises:
            ManagerShutdownError: If shutdown fails
        """
        if not self._initialized:
            return

        try:
            self._logger.info('Shutting down Resource Monitoring Manager')

            # Cancel all collection tasks
            for task in self._collection_tasks.values():
                task.cancel()

            # Wait for tasks to cancel
            if self._collection_tasks:
                await asyncio.gather(*self._collection_tasks.values(), return_exceptions=True)

            self._collection_tasks.clear()

            # Unsubscribe from events
            await self._event_bus_manager.unsubscribe(subscriber_id='monitoring_manager')

            # Unregister config listener
            await self._config_manager.unregister_listener('monitoring', self._on_config_changed)

            self._initialized = False
            self._healthy = False

            self._logger.info('Resource Monitoring Manager shut down successfully')

        except Exception as e:
            self._logger.error(f'Failed to shut down Resource Monitoring Manager: {str(e)}')
            raise ManagerShutdownError(
                f'Failed to shut down AsyncResourceMonitoringManager: {str(e)}',
                manager_name=self.name
            ) from e

    def status(self) -> Dict[str, Any]:
        """Get the status of the resource monitoring manager.

        Returns:
            Dictionary with status information
        """
        status = super().status()

        if self._initialized:
            status.update({
                'prometheus': {
                    'enabled': self._prometheus_server_port is not None,
                    'port': self._prometheus_server_port,
                    'metrics_count': len(self._metrics)
                },
                'alerts': {
                    'active': len(self._alerts),
                    'resolved': len(self._resolved_alerts)
                },
                'metrics_interval': self._metrics_interval_seconds,
                'collection_tasks': len(self._collection_tasks)
            })

            # Add current metrics if available
            try:
                status['current_metrics'] = {
                    'cpu_percent': psutil.cpu_percent(interval=None),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent
                }
            except:
                pass

        return status