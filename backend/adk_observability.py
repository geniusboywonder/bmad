#!/usr/bin/env python3
"""ADK Observability Integration for BMAD System.

This module integrates ADK observability features with BMAD's existing monitoring
and logging infrastructure, providing comprehensive system visibility.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
import json
import psutil
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger(__name__)


@dataclass
class ObservabilityMetrics:
    """Comprehensive observability metrics."""
    timestamp: datetime
    agent_type: str
    implementation: str
    response_time: float
    cpu_usage: float
    memory_usage: float
    cache_hit_rate: float
    error_rate: float
    throughput: float
    active_connections: int
    queue_depth: int
    custom_metrics: Dict[str, Any]


@dataclass
class SystemHealth:
    """System health assessment."""
    overall_status: str
    component_status: Dict[str, str]
    performance_score: float
    reliability_score: float
    recommendations: List[str]
    critical_issues: List[str]


class ADKObservabilityManager:
    """Manages observability integration between ADK and BMAD."""

    def __init__(self):
        self.metrics_history = []
        self.health_checks = []
        self.alerts = []
        self.performance_baselines = {}
        self.monitoring_config = {
            "metrics_collection_interval": 30,  # seconds
            "health_check_interval": 60,       # seconds
            "alert_thresholds": {
                "response_time_critical": 5.0,
                "error_rate_critical": 0.10,
                "cpu_usage_critical": 90.0,
                "memory_usage_critical": 85.0
            },
            "retention_period_days": 30
        }

    async def collect_comprehensive_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive metrics from all system components."""
        start_time = time.time()

        try:
            # Collect system metrics
            system_metrics = await self._collect_system_metrics()

            # Collect agent metrics
            agent_metrics = await self._collect_agent_metrics()

            # Collect ADK-specific metrics
            adk_metrics = await self._collect_adk_metrics()

            # Collect BMAD-specific metrics
            bmad_metrics = await self._collect_bmad_metrics()

            # Combine all metrics
            comprehensive_metrics = {
                "collection_timestamp": datetime.now().isoformat(),
                "collection_duration": time.time() - start_time,
                "system_metrics": system_metrics,
                "agent_metrics": agent_metrics,
                "adk_metrics": adk_metrics,
                "bmad_metrics": bmad_metrics,
                "aggregated_metrics": self._aggregate_metrics([
                    system_metrics, agent_metrics, adk_metrics, bmad_metrics
                ])
            }

            # Store metrics history
            self.metrics_history.append(comprehensive_metrics)

            # Clean up old metrics
            self._cleanup_old_metrics()

            logger.info("Comprehensive metrics collected",
                       duration=comprehensive_metrics["collection_duration"],
                       agent_count=len(agent_metrics))

            return comprehensive_metrics

        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return {
                "error": str(e),
                "collection_timestamp": datetime.now().isoformat(),
                "collection_duration": time.time() - start_time
            }

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total

            # Network metrics
            network = psutil.net_io_counters()
            bytes_sent = network.bytes_sent
            bytes_recv = network.bytes_recv

            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else None
                },
                "memory": {
                    "usage_percent": memory_percent,
                    "used_bytes": memory_used,
                    "total_bytes": memory_total
                },
                "disk": {
                    "usage_percent": disk_percent,
                    "used_bytes": disk_used,
                    "total_bytes": disk_total
                },
                "network": {
                    "bytes_sent": bytes_sent,
                    "bytes_recv": bytes_recv
                },
                "system_load": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }

        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return {"error": str(e)}

    async def _collect_agent_metrics(self) -> Dict[str, Any]:
        """Collect metrics from agent instances."""
        try:
            from adk_agent_factory import agent_factory

            agent_metrics = {}

            for cache_key, agent in agent_factory.agent_cache.items():
                try:
                    agent_metric = await self._collect_single_agent_metrics(agent, cache_key)
                    if agent_metric:
                        agent_metrics[cache_key] = agent_metric
                except Exception as e:
                    logger.warning(f"Failed to collect metrics for agent {cache_key}: {e}")

            return {
                "total_agents": len(agent_metrics),
                "active_agents": len([m for m in agent_metrics.values() if m.get("active", False)]),
                "agent_details": agent_metrics,
                "cache_statistics": agent_factory.get_cache_stats()
            }

        except Exception as e:
            logger.error(f"Agent metrics collection failed: {e}")
            return {"error": str(e)}

    async def _collect_single_agent_metrics(self, agent, cache_key: str) -> Optional[Dict[str, Any]]:
        """Collect metrics for a single agent."""
        try:
            agent_type = getattr(agent, '_agent_type', 'unknown')
            implementation = getattr(agent, '_implementation', 'unknown')

            # Basic agent metrics
            metrics = {
                "agent_type": agent_type,
                "implementation": implementation,
                "active": True,
                "created_at": getattr(agent, '_created_at', None),
                "fallback_mode": getattr(agent, '_fallback_mode', False),
                "emergency_mode": getattr(agent, '_emergency_mode', False)
            }

            # Performance metrics (would be collected from actual usage)
            metrics.update({
                "response_time_avg": getattr(agent, '_avg_response_time', 1.5),
                "error_rate": getattr(agent, '_error_rate', 0.02),
                "throughput": getattr(agent, '_throughput', 10),
                "cache_hit_rate": getattr(agent, '_cache_hit_rate', 0.85)
            })

            return metrics

        except Exception as e:
            logger.error(f"Single agent metrics collection failed for {cache_key}: {e}")
            return None

    async def _collect_adk_metrics(self) -> Dict[str, Any]:
        """Collect ADK-specific metrics."""
        try:
            # ADK model performance metrics
            from adk_advanced_features import multi_model_manager

            model_performance = multi_model_manager.get_model_performance_report()

            # ADK tool usage metrics
            tool_metrics = await self._collect_adk_tool_metrics()

            return {
                "model_performance": model_performance,
                "tool_usage": tool_metrics,
                "adk_system_health": {
                    "models_available": len(multi_model_manager.available_models),
                    "active_models": len([m for m in model_performance.values()
                                        if isinstance(m, dict) and not m.get("error")]),
                    "tool_execution_rate": tool_metrics.get("execution_rate", 0)
                }
            }

        except Exception as e:
            logger.error(f"ADK metrics collection failed: {e}")
            return {"error": str(e)}

    async def _collect_adk_tool_metrics(self) -> Dict[str, Any]:
        """Collect ADK tool usage metrics."""
        # In a real implementation, this would collect actual tool usage data
        return {
            "total_tool_executions": 150,
            "successful_executions": 142,
            "failed_executions": 8,
            "execution_rate": 0.95,
            "popular_tools": ["google_search", "requirements_analyzer", "code_generator"],
            "avg_execution_time": 1.2
        }

    async def _collect_bmad_metrics(self) -> Dict[str, Any]:
        """Collect BMAD-specific metrics."""
        try:
            # HITL metrics
            hitl_metrics = await self._collect_hitl_metrics()

            # Context Store metrics
            context_metrics = await self._collect_context_store_metrics()

            # WebSocket metrics
            websocket_metrics = await self._collect_websocket_metrics()

            # Audit Trail metrics
            audit_metrics = await self._collect_audit_metrics()

            return {
                "hitl_metrics": hitl_metrics,
                "context_store_metrics": context_metrics,
                "websocket_metrics": websocket_metrics,
                "audit_trail_metrics": audit_metrics,
                "bmad_system_health": {
                    "hitl_active": hitl_metrics.get("active_sessions", 0) > 0,
                    "context_store_healthy": context_metrics.get("health_status") == "healthy",
                    "websocket_connections": websocket_metrics.get("active_connections", 0),
                    "audit_trail_active": audit_metrics.get("events_logged_today", 0) > 0
                }
            }

        except Exception as e:
            logger.error(f"BMAD metrics collection failed: {e}")
            return {"error": str(e)}

    async def _collect_hitl_metrics(self) -> Dict[str, Any]:
        """Collect HITL system metrics."""
        # In a real implementation, this would query the HITL service
        return {
            "active_sessions": 5,
            "pending_approvals": 12,
            "approved_today": 45,
            "rejected_today": 3,
            "avg_response_time": 2.3
        }

    async def _collect_context_store_metrics(self) -> Dict[str, Any]:
        """Collect Context Store metrics."""
        # In a real implementation, this would query the context store
        return {
            "total_artifacts": 1250,
            "active_contexts": 89,
            "storage_used_mb": 450,
            "health_status": "healthy",
            "avg_retrieval_time": 0.15
        }

    async def _collect_websocket_metrics(self) -> Dict[str, Any]:
        """Collect WebSocket metrics."""
        # In a real implementation, this would query the WebSocket service
        return {
            "active_connections": 23,
            "total_connections_today": 156,
            "messages_sent": 1247,
            "messages_received": 1189,
            "avg_latency": 0.08
        }

    async def _collect_audit_metrics(self) -> Dict[str, Any]:
        """Collect Audit Trail metrics."""
        # In a real implementation, this would query the audit service
        return {
            "events_logged_today": 2341,
            "total_events": 45678,
            "storage_used_mb": 120,
            "retention_days": 365,
            "query_performance": 0.95
        }

    def _aggregate_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metrics from multiple sources."""
        aggregated = {
            "total_sources": len(metrics_list),
            "collection_timestamp": datetime.now().isoformat(),
            "summary": {}
        }

        # Aggregate system-level metrics
        cpu_usage_values = []
        memory_usage_values = []

        for metrics in metrics_list:
            if "cpu" in metrics and "usage_percent" in metrics["cpu"]:
                cpu_usage_values.append(metrics["cpu"]["usage_percent"])
            if "memory" in metrics and "usage_percent" in metrics["memory"]:
                memory_usage_values.append(metrics["memory"]["usage_percent"])

        if cpu_usage_values:
            aggregated["summary"]["avg_cpu_usage"] = sum(cpu_usage_values) / len(cpu_usage_values)
        if memory_usage_values:
            aggregated["summary"]["avg_memory_usage"] = sum(memory_usage_values) / len(memory_usage_values)

        return aggregated

    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.monitoring_config["retention_period_days"])

        # Clean up metrics history
        self.metrics_history = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["collection_timestamp"]) > cutoff_date
        ]

        # Clean up health checks
        self.health_checks = [
            h for h in self.health_checks
            if h.get("timestamp", datetime.min) > cutoff_date
        ]

    async def perform_health_check(self) -> SystemHealth:
        """Perform comprehensive system health check."""
        try:
            # Get latest metrics
            latest_metrics = await self.collect_comprehensive_metrics()

            # Assess component health
            component_status = await self._assess_component_health(latest_metrics)

            # Calculate performance score
            performance_score = self._calculate_performance_score(latest_metrics)

            # Calculate reliability score
            reliability_score = self._calculate_reliability_score(latest_metrics)

            # Generate recommendations
            recommendations = self._generate_health_recommendations(component_status)

            # Identify critical issues
            critical_issues = self._identify_critical_issues(component_status)

            # Determine overall status
            overall_status = self._determine_overall_status(
                component_status, performance_score, reliability_score
            )

            health = SystemHealth(
                overall_status=overall_status,
                component_status=component_status,
                performance_score=performance_score,
                reliability_score=reliability_score,
                recommendations=recommendations,
                critical_issues=critical_issues
            )

            # Store health check
            self.health_checks.append({
                "timestamp": datetime.now(),
                "health": health.__dict__
            })

            logger.info(f"Health check completed: {overall_status}")
            return health

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return SystemHealth(
                overall_status="error",
                component_status={"error": str(e)},
                performance_score=0.0,
                reliability_score=0.0,
                recommendations=["Investigate health check failure"],
                critical_issues=["Health check system failure"]
            )

    async def _assess_component_health(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Assess health of individual system components."""
        component_status = {}

        # Assess system components
        system_metrics = metrics.get("system_metrics", {})
        if system_metrics.get("error"):
            component_status["system"] = "error"
        elif system_metrics.get("cpu", {}).get("usage_percent", 0) > 90:
            component_status["system"] = "critical"
        elif system_metrics.get("memory", {}).get("usage_percent", 0) > 85:
            component_status["system"] = "warning"
        else:
            component_status["system"] = "healthy"

        # Assess agent components
        agent_metrics = metrics.get("agent_metrics", {})
        if agent_metrics.get("error"):
            component_status["agents"] = "error"
        elif agent_metrics.get("active_agents", 0) == 0:
            component_status["agents"] = "critical"
        elif agent_metrics.get("active_agents", 0) < agent_metrics.get("total_agents", 0) * 0.8:
            component_status["agents"] = "warning"
        else:
            component_status["agents"] = "healthy"

        # Assess ADK components
        adk_metrics = metrics.get("adk_metrics", {})
        if adk_metrics.get("error"):
            component_status["adk"] = "error"
        elif adk_metrics.get("adk_system_health", {}).get("models_available", 0) == 0:
            component_status["adk"] = "critical"
        else:
            component_status["adk"] = "healthy"

        # Assess BMAD components
        bmad_metrics = metrics.get("bmad_metrics", {})
        if bmad_metrics.get("error"):
            component_status["bmad"] = "error"
        else:
            bmad_health = bmad_metrics.get("bmad_system_health", {})
            if not bmad_health.get("hitl_active", False):
                component_status["hitl"] = "warning"
            else:
                component_status["hitl"] = "healthy"

            if not bmad_health.get("context_store_healthy", False):
                component_status["context_store"] = "warning"
            else:
                component_status["context_store"] = "healthy"

            component_status["websocket"] = "healthy" if bmad_health.get("websocket_connections", 0) > 0 else "warning"
            component_status["audit_trail"] = "healthy" if bmad_health.get("audit_trail_active", False) else "warning"

        return component_status

    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100.0

        # System performance penalties
        system_metrics = metrics.get("system_metrics", {})
        if system_metrics.get("cpu", {}).get("usage_percent", 0) > 80:
            score -= 20
        if system_metrics.get("memory", {}).get("usage_percent", 0) > 80:
            score -= 20

        # Agent performance penalties
        agent_metrics = metrics.get("agent_metrics", {})
        if agent_metrics.get("active_agents", 0) < agent_metrics.get("total_agents", 0) * 0.9:
            score -= 15

        return max(0.0, min(100.0, score))

    def _calculate_reliability_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall reliability score (0-100)."""
        score = 100.0

        # Component health penalties
        component_status = metrics.get("component_status", {})
        for component, status in component_status.items():
            if status == "error":
                score -= 25
            elif status == "critical":
                score -= 15
            elif status == "warning":
                score -= 5

        return max(0.0, min(100.0, score))

    def _generate_health_recommendations(self, component_status: Dict[str, str]) -> List[str]:
        """Generate health recommendations based on component status."""
        recommendations = []

        for component, status in component_status.items():
            if status == "error":
                recommendations.append(f"Investigate and resolve {component} errors immediately")
            elif status == "critical":
                recommendations.append(f"Address critical issues in {component} urgently")
            elif status == "warning":
                recommendations.append(f"Monitor and optimize {component} performance")

        if not recommendations:
            recommendations.append("All systems operating normally")

        return recommendations

    def _identify_critical_issues(self, component_status: Dict[str, str]) -> List[str]:
        """Identify critical issues requiring immediate attention."""
        critical_issues = []

        for component, status in component_status.items():
            if status in ["error", "critical"]:
                critical_issues.append(f"{component} is in {status} state")

        return critical_issues

    def _determine_overall_status(self, component_status: Dict[str, str],
                                performance_score: float, reliability_score: float) -> str:
        """Determine overall system status."""
        # Check for critical components
        critical_components = ["system", "agents", "hitl", "audit_trail"]
        critical_statuses = [component_status.get(comp, "unknown") for comp in critical_components]

        if any(status in ["error", "critical"] for status in critical_statuses):
            return "critical"
        elif any(status == "warning" for status in critical_statuses):
            return "warning"
        elif performance_score < 70 or reliability_score < 70:
            return "warning"
        else:
            return "healthy"

    def generate_observability_report(self) -> Dict[str, Any]:
        """Generate comprehensive observability report."""
        latest_health = self.health_checks[-1] if self.health_checks else None

        return {
            "report_generated": datetime.now().isoformat(),
            "period_covered": {
                "start": self.metrics_history[0]["collection_timestamp"] if self.metrics_history else None,
                "end": self.metrics_history[-1]["collection_timestamp"] if self.metrics_history else None
            },
            "current_health": latest_health["health"] if latest_health else None,
            "metrics_summary": self._generate_metrics_summary(),
            "trends_analysis": self._generate_trends_analysis(),
            "alerts_summary": self._generate_alerts_summary(),
            "recommendations": self._generate_observability_recommendations()
        }

    def _generate_metrics_summary(self) -> Dict[str, Any]:
        """Generate metrics summary."""
        if not self.metrics_history:
            return {"message": "No metrics available"}

        latest = self.metrics_history[-1]
        return {
            "total_collections": len(self.metrics_history),
            "latest_collection": latest["collection_timestamp"],
            "system_metrics": latest.get("system_metrics", {}),
            "agent_metrics": latest.get("agent_metrics", {}),
            "adk_metrics": latest.get("adk_metrics", {}),
            "bmad_metrics": latest.get("bmad_metrics", {})
        }

    def _generate_trends_analysis(self) -> Dict[str, Any]:
        """Generate trends analysis."""
        if len(self.metrics_history) < 2:
            return {"message": "Insufficient data for trend analysis"}

        # Analyze trends in key metrics
        trends = {}

        # CPU usage trend
        cpu_values = [m["system_metrics"]["cpu"]["usage_percent"]
                     for m in self.metrics_history[-10:]
                     if "system_metrics" in m and "cpu" in m["system_metrics"]]
        if cpu_values:
            trends["cpu_usage"] = "increasing" if cpu_values[-1] > cpu_values[0] * 1.1 else "stable"

        # Memory usage trend
        memory_values = [m["system_metrics"]["memory"]["usage_percent"]
                        for m in self.metrics_history[-10:]
                        if "system_metrics" in m and "memory" in m["system_metrics"]]
        if memory_values:
            trends["memory_usage"] = "increasing" if memory_values[-1] > memory_values[0] * 1.1 else "stable"

        return trends

    def _generate_alerts_summary(self) -> Dict[str, Any]:
        """Generate alerts summary."""
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len([a for a in self.alerts if not a.get("resolved", False)]),
            "critical_alerts": len([a for a in self.alerts
                                  if a.get("severity") == "critical" and not a.get("resolved", False)]),
            "recent_alerts": self.alerts[-5:] if self.alerts else []
        }

    def _generate_observability_recommendations(self) -> List[str]:
        """Generate observability recommendations."""
        recommendations = []

        if not self.metrics_history:
            recommendations.append("Enable metrics collection for better observability")
        elif len(self.metrics_history) < 10:
            recommendations.append("Increase metrics retention for better trend analysis")

        latest_health = self.health_checks[-1] if self.health_checks else None
        if latest_health:
            health_data = latest_health["health"]
            if health_data["overall_status"] != "healthy":
                recommendations.append("Address system health issues identified in latest check")

        return recommendations if recommendations else ["Observability systems operating normally"]


# Global observability manager instance
observability_manager = ADKObservabilityManager()


async def collect_observability_metrics() -> Dict[str, Any]:
    """Convenience function to collect observability metrics."""
    return await observability_manager.collect_comprehensive_metrics()


async def perform_system_health_check() -> SystemHealth:
    """Convenience function to perform system health check."""
    return await observability_manager.perform_health_check()


def generate_observability_report() -> Dict[str, Any]:
    """Convenience function to generate observability report."""
    return observability_manager.generate_observability_report()


if __name__ == "__main__":
    print("🚀 ADK Observability Integration Demo")
    print("=" * 50)

    async def run_demo():
        # Collect comprehensive metrics
        print("📊 Collecting Observability Metrics...")
        metrics = await collect_observability_metrics()
        print(f"Metrics collected from {metrics.get('aggregated_metrics', {}).get('total_sources', 0)} sources")

        # Perform health check
        print("\n🏥 Performing System Health Check...")
        health = await perform_system_health_check()
        print(f"Overall Health: {health.overall_status}")
        print(f"Performance Score: {health.performance_score:.1f}")
        print(f"Reliability Score: {health.reliability_score:.1f}")

        if health.critical_issues:
            print("Critical Issues:")
            for issue in health.critical_issues:
                print(f"  • {issue}")

        # Generate observability report
        print("\n📈 Generating Observability Report...")
        report = generate_observability_report()
        print(f"Report generated for period: {report.get('period_covered', {})}")

        print("\n✅ Observability integration demo completed")

    asyncio.run(run_demo())
