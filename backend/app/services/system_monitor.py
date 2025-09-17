"""
System Monitor Service for BMAD Core Template System

This module provides comprehensive system monitoring and performance analytics
for the BMAD backend, including resource usage, performance metrics, and
health trend analysis.
"""

import asyncio
import time
import psutil
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import structlog

from .llm_monitoring import LLMUsageTracker

logger = structlog.get_logger(__name__)


@dataclass
class SystemMetrics:
    """System performance metrics snapshot."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # CPU metrics
    cpu_percent: float = 0.0
    cpu_count: int = 0
    cpu_freq_current: Optional[float] = None
    cpu_freq_min: Optional[float] = None
    cpu_freq_max: Optional[float] = None

    # Memory metrics
    memory_total: int = 0
    memory_available: int = 0
    memory_percent: float = 0.0
    memory_used: int = 0

    # Disk metrics
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0
    disk_percent: float = 0.0

    # Network metrics
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    network_packets_sent: int = 0
    network_packets_recv: int = 0

    # Process metrics
    process_count: int = 0
    thread_count: int = 0
    open_files: int = 0
    connections: int = 0


@dataclass
class ApplicationMetrics:
    """Application-specific performance metrics."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Request metrics
    total_requests: int = 0
    active_requests: int = 0
    queued_requests: int = 0
    failed_requests: int = 0

    # Response time metrics
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    thread_count: int = 0
    open_connections: int = 0

    # Error metrics
    error_rate: float = 0.0
    error_count: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)

    # Cache metrics
    cache_hit_rate: float = 0.0
    cache_size: int = 0
    cache_evictions: int = 0


@dataclass
class PerformanceAlert:
    """Performance alert configuration and state."""
    alert_id: str
    name: str
    description: str
    metric: str
    threshold: float
    operator: str  # 'gt', 'lt', 'gte', 'lte', 'eq'
    severity: str  # 'low', 'medium', 'high', 'critical'
    enabled: bool = True
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class SystemMonitor:
    """
    Comprehensive system monitoring service for BMAD backend.

    This service provides real-time monitoring of system resources,
    application performance, and trend analysis with alerting capabilities.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the system monitor.

        Args:
            config: Configuration dictionary with monitoring parameters
        """
        self.collection_interval = config.get("collection_interval", 30)  # seconds
        self.retention_period = config.get("retention_period", 3600)  # 1 hour
        self.enable_alerting = config.get("enable_alerting", True)
        self.alert_cooldown = config.get("alert_cooldown", 300)  # 5 minutes

        # Metrics storage
        self.system_metrics: deque[SystemMetrics] = deque(maxlen=120)  # 1 hour at 30s intervals
        self.application_metrics: deque[ApplicationMetrics] = deque(maxlen=120)

        # Alert configuration
        self.alerts: Dict[str, PerformanceAlert] = {}
        self.active_alerts: Dict[str, datetime] = {}

        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_collection = datetime.now(timezone.utc)

        # Dependencies
        self.llm_tracker = LLMUsageTracker()

        # Initialize default alerts
        self._setup_default_alerts()

        logger.info("System monitor initialized",
                   collection_interval=self.collection_interval,
                   retention_period=self.retention_period)

    def start_monitoring(self) -> None:
        """Start the monitoring system."""
        if self.is_monitoring:
            logger.warning("Monitoring already running")
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("System monitoring started")

    def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        if not self.is_monitoring:
            logger.warning("Monitoring not running")
            return

        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("System monitoring stopped")

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics
            network = psutil.net_io_counters()

            # Process metrics
            process_count = len(psutil.pids())
            thread_count = sum(len(psutil.Process(pid).threads()) for pid in psutil.pids()[:10])  # Sample first 10
            open_files = sum(len(psutil.Process(pid).open_files()) for pid in psutil.pids()[:10])
            connections = sum(len(psutil.Process(pid).connections()) for pid in psutil.pids()[:10])

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq_current=cpu_freq.current if cpu_freq else None,
                cpu_freq_min=cpu_freq.min if cpu_freq else None,
                cpu_freq_max=cpu_freq.max if cpu_freq else None,
                memory_total=memory.total,
                memory_available=memory.available,
                memory_percent=memory.percent,
                memory_used=memory.used,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_free=disk.free,
                disk_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                network_packets_sent=network.packets_sent,
                network_packets_recv=network.packets_recv,
                process_count=process_count,
                thread_count=thread_count,
                open_files=open_files,
                connections=connections
            )

            self.system_metrics.append(metrics)
            return metrics

        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
            return SystemMetrics()

    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific performance metrics."""
        try:
            # Get current process info
            process = psutil.Process()

            # Memory usage
            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / 1024 / 1024

            # CPU usage
            cpu_usage = process.cpu_percent()

            # Thread count
            thread_count = process.num_threads()

            # Open connections (simplified)
            try:
                connections = len(process.connections())
            except:
                connections = 0

            # Get LLM usage stats
            llm_stats = self.llm_tracker.get_session_stats()

            metrics = ApplicationMetrics(
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage,
                thread_count=thread_count,
                open_connections=connections,
                total_requests=llm_stats.get('requests_tracked', 0),
                failed_requests=llm_stats.get('errors_tracked', 0),
                error_rate=llm_stats.get('error_rate', 0.0)
            )

            # Calculate error rate
            if metrics.total_requests > 0:
                metrics.error_rate = metrics.failed_requests / metrics.total_requests

            self.application_metrics.append(metrics)
            return metrics

        except Exception as e:
            logger.error("Failed to collect application metrics", error=str(e))
            return ApplicationMetrics()

    def get_current_status(self) -> Dict[str, Any]:
        """Get current system and application status."""
        system_metrics = self.system_metrics[-1] if self.system_metrics else self.collect_system_metrics()
        app_metrics = self.application_metrics[-1] if self.application_metrics else self.collect_application_metrics()

        # Calculate health score
        health_score = self._calculate_health_score(system_metrics, app_metrics)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_score": health_score,
            "health_status": self._get_health_status(health_score),
            "system_metrics": {
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "disk_percent": system_metrics.disk_percent,
                "process_count": system_metrics.process_count
            },
            "application_metrics": {
                "memory_usage_mb": app_metrics.memory_usage_mb,
                "cpu_usage_percent": app_metrics.cpu_usage_percent,
                "thread_count": app_metrics.thread_count,
                "total_requests": app_metrics.total_requests,
                "error_rate": app_metrics.error_rate
            },
            "active_alerts": list(self.active_alerts.keys())
        }

    def get_performance_report(self, hours: int = 1) -> Dict[str, Any]:
        """Generate performance report for the specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Filter metrics
        recent_system = [m for m in self.system_metrics if m.timestamp >= cutoff_time]
        recent_app = [m for m in self.application_metrics if m.timestamp >= cutoff_time]

        if not recent_system or not recent_app:
            return {"error": "Insufficient data for performance report"}

        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_system) / len(recent_system)
        avg_memory = sum(m.memory_percent for m in recent_system) / len(recent_system)
        avg_disk = sum(m.disk_percent for m in recent_system) / len(recent_system)

        avg_app_memory = sum(m.memory_usage_mb for m in recent_app) / len(recent_app)
        avg_app_cpu = sum(m.cpu_usage_percent for m in recent_app) / len(recent_app)
        total_requests = sum(m.total_requests for m in recent_app)
        total_errors = sum(m.failed_requests for m in recent_app)

        # Calculate trends
        cpu_trend = self._calculate_trend([m.cpu_percent for m in recent_system])
        memory_trend = self._calculate_trend([m.memory_percent for m in recent_system])

        return {
            "time_period_hours": hours,
            "data_points": len(recent_system),
            "system_averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_percent": round(avg_memory, 2),
                "disk_percent": round(avg_disk, 2)
            },
            "application_averages": {
                "memory_usage_mb": round(avg_app_memory, 2),
                "cpu_usage_percent": round(avg_app_cpu, 2),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": round(total_errors / max(total_requests, 1), 4)
            },
            "trends": {
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend
            },
            "performance_score": self._calculate_performance_score(avg_cpu, avg_memory, total_errors / max(total_requests, 1))
        }

    def add_alert(self, alert: PerformanceAlert) -> None:
        """Add a performance alert."""
        self.alerts[alert.alert_id] = alert
        logger.info("Performance alert added", alert_id=alert.alert_id, name=alert.name)

    def remove_alert(self, alert_id: str) -> bool:
        """Remove a performance alert."""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self.active_alerts.pop(alert_id, None)
            logger.info("Performance alert removed", alert_id=alert_id)
            return True
        return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        active = []
        for alert_id, triggered_time in self.active_alerts.items():
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                active.append({
                    "alert_id": alert_id,
                    "name": alert.name,
                    "severity": alert.severity,
                    "triggered_at": triggered_time.isoformat(),
                    "description": alert.description
                })
        return active

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check all alerts and return triggered ones."""
        triggered_alerts = []

        if not self.system_metrics or not self.application_metrics:
            return triggered_alerts

        current_system = self.system_metrics[-1]
        current_app = self.application_metrics[-1]

        for alert in self.alerts.values():
            if not alert.enabled:
                continue

            # Check cooldown
            if alert.last_triggered:
                cooldown_end = alert.last_triggered + timedelta(minutes=alert.cooldown_minutes)
                if datetime.now(timezone.utc) < cooldown_end:
                    continue

            # Get current value
            current_value = self._get_metric_value(alert.metric, current_system, current_app)

            # Check threshold
            triggered = self._check_threshold(current_value, alert.threshold, alert.operator)

            if triggered:
                alert.last_triggered = datetime.now(timezone.utc)
                alert.trigger_count += 1
                self.active_alerts[alert.alert_id] = alert.last_triggered

                triggered_alerts.append({
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity,
                    "description": alert.description,
                    "metric": alert.metric,
                    "current_value": current_value,
                    "threshold": alert.threshold,
                    "operator": alert.operator,
                    "triggered_at": alert.last_triggered.isoformat()
                })

                logger.warning("Performance alert triggered",
                              alert_id=alert.alert_id,
                              name=alert.name,
                              current_value=current_value,
                              threshold=alert.threshold)

        return triggered_alerts

    def get_resource_usage_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get resource usage trends over time."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Filter data
        system_data = [m for m in self.system_metrics if m.timestamp >= cutoff_time]
        app_data = [m for m in self.application_metrics if m.timestamp >= cutoff_time]

        if not system_data:
            return {"error": "No system metrics data available"}

        # Group by hour
        hourly_system = defaultdict(list)
        hourly_app = defaultdict(list)

        for metric in system_data:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_system[hour_key].append(metric)

        for metric in app_data:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_app[hour_key].append(metric)

        # Calculate hourly averages
        trends = {
            "time_range": f"{hours} hours",
            "hourly_data": []
        }

        for hour in sorted(hourly_system.keys()):
            system_metrics = hourly_system[hour]
            app_metrics = hourly_app.get(hour, [])

            if system_metrics:
                avg_cpu = sum(m.cpu_percent for m in system_metrics) / len(system_metrics)
                avg_memory = sum(m.memory_percent for m in system_metrics) / len(system_metrics)

                data_point = {
                    "timestamp": hour.isoformat(),
                    "system": {
                        "cpu_percent": round(avg_cpu, 2),
                        "memory_percent": round(avg_memory, 2)
                    }
                }

                if app_metrics:
                    avg_app_memory = sum(m.memory_usage_mb for m in app_metrics) / len(app_metrics)
                    avg_app_cpu = sum(m.cpu_usage_percent for m in app_metrics) / len(app_metrics)

                    data_point["application"] = {
                        "memory_usage_mb": round(avg_app_memory, 2),
                        "cpu_usage_percent": round(avg_app_cpu, 2),
                        "requests": sum(m.total_requests for m in app_metrics),
                        "errors": sum(m.failed_requests for m in app_metrics)
                    }

                trends["hourly_data"].append(data_point)

        return trends

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Monitoring loop started")

        while self.is_monitoring:
            try:
                # Collect metrics
                self.collect_system_metrics()
                self.collect_application_metrics()

                # Check alerts
                if self.enable_alerting:
                    self.check_alerts()

                # Clean up old data
                self._cleanup_old_data()

            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))

            # Wait for next collection
            time.sleep(self.collection_interval)

        logger.info("Monitoring loop stopped")

    def _setup_default_alerts(self) -> None:
        """Set up default performance alerts."""
        default_alerts = [
            PerformanceAlert(
                alert_id="high_cpu",
                name="High CPU Usage",
                description="CPU usage is above 80%",
                metric="cpu_percent",
                threshold=80.0,
                operator="gt",
                severity="medium"
            ),
            PerformanceAlert(
                alert_id="high_memory",
                name="High Memory Usage",
                description="Memory usage is above 85%",
                metric="memory_percent",
                threshold=85.0,
                operator="gt",
                severity="medium"
            ),
            PerformanceAlert(
                alert_id="high_error_rate",
                name="High Error Rate",
                description="Application error rate is above 5%",
                metric="error_rate",
                threshold=0.05,
                operator="gt",
                severity="high"
            ),
            PerformanceAlert(
                alert_id="low_disk_space",
                name="Low Disk Space",
                description="Disk usage is above 90%",
                metric="disk_percent",
                threshold=90.0,
                operator="gt",
                severity="high"
            )
        ]

        for alert in default_alerts:
            self.alerts[alert.alert_id] = alert

    def _calculate_health_score(self, system: SystemMetrics, app: ApplicationMetrics) -> float:
        """Calculate overall system health score (0-100)."""
        score = 100.0

        # CPU health (30% weight)
        if system.cpu_percent > 80:
            score -= (system.cpu_percent - 80) * 0.3
        elif system.cpu_percent > 90:
            score -= (system.cpu_percent - 90) * 0.6

        # Memory health (30% weight)
        if system.memory_percent > 80:
            score -= (system.memory_percent - 80) * 0.3
        elif system.memory_percent > 90:
            score -= (system.memory_percent - 90) * 0.6

        # Disk health (20% weight)
        if system.disk_percent > 85:
            score -= (system.disk_percent - 85) * 0.5
        elif system.disk_percent > 95:
            score -= (system.disk_percent - 95) * 1.0

        # Application health (20% weight)
        if app.error_rate > 0.05:
            score -= app.error_rate * 2000  # 10% error rate = -20 points

        return max(0.0, min(100.0, score))

    def _get_health_status(self, score: float) -> str:
        """Get health status based on score."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "stable"

        # Simple linear trend
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        diff = second_avg - first_avg
        threshold = abs(first_avg) * 0.05  # 5% change threshold

        if diff > threshold:
            return "increasing"
        elif diff < -threshold:
            return "decreasing"
        else:
            return "stable"

    def _calculate_performance_score(self, cpu: float, memory: float, error_rate: float) -> float:
        """Calculate performance score (0-100)."""
        # Lower resource usage and error rate = higher score
        cpu_score = max(0, 100 - cpu)
        memory_score = max(0, 100 - memory)
        error_score = max(0, 100 - (error_rate * 1000))  # 1% error rate = 90 score

        return (cpu_score + memory_score + error_score) / 3

    def _get_metric_value(self, metric: str, system: SystemMetrics, app: ApplicationMetrics) -> float:
        """Get metric value from current metrics."""
        if metric == "cpu_percent":
            return system.cpu_percent
        elif metric == "memory_percent":
            return system.memory_percent
        elif metric == "disk_percent":
            return system.disk_percent
        elif metric == "error_rate":
            return app.error_rate
        elif metric == "memory_usage_mb":
            return app.memory_usage_mb
        else:
            return 0.0

    def _check_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value meets threshold condition."""
        if operator == "gt":
            return value > threshold
        elif operator == "lt":
            return value < threshold
        elif operator == "gte":
            return value >= threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "eq":
            return value == threshold
        else:
            return False

    def _cleanup_old_data(self) -> None:
        """Clean up old metrics data."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.retention_period)

        # Remove old system metrics
        while self.system_metrics and self.system_metrics[0].timestamp < cutoff_time:
            self.system_metrics.popleft()

        # Remove old application metrics
        while self.application_metrics and self.application_metrics[0].timestamp < cutoff_time:
            self.application_metrics.popleft()

        # Clean up expired alerts
        expired_alerts = []
        for alert_id, triggered_time in self.active_alerts.items():
            if datetime.now(timezone.utc) - triggered_time > timedelta(minutes=30):
                expired_alerts.append(alert_id)

        for alert_id in expired_alerts:
            self.active_alerts.pop(alert_id, None)
