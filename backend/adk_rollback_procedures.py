#!/usr/bin/env python3
"""ADK Rollback Procedures for BMAD System.

This module provides comprehensive rollback procedures for the ADK migration,
ensuring safe and reliable reversion to legacy implementations when needed.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import structlog

from adk_feature_flags import feature_flags
from adk_agent_factory import clear_agent_cache

logger = structlog.get_logger(__name__)


class RollbackTrigger(Enum):
    """Triggers for rollback procedures."""
    MANUAL = "manual"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_RATE_SPIKE = "error_rate_spike"
    USER_COMPLAINTS = "user_complaints"
    SYSTEM_FAILURE = "system_failure"
    EMERGENCY_STOP = "emergency_stop"


class RollbackScope(Enum):
    """Scope of rollback procedures."""
    SINGLE_AGENT = "single_agent"
    MULTIPLE_AGENTS = "multiple_agents"
    GLOBAL_ROLLBACK = "global_rollback"
    EMERGENCY_STOP = "emergency_stop"


class ADKRollbackManager:
    """Manages rollback procedures for ADK migration."""

    def __init__(self):
        self.rollback_history = []
        self.monitoring_thresholds = {
            "response_time_warning": 3.0,  # seconds
            "response_time_critical": 5.0,  # seconds
            "error_rate_warning": 0.05,     # 5%
            "error_rate_critical": 0.10,    # 10%
            "user_complaints_threshold": 20  # complaints per hour
        }

    async def execute_rollback(self, scope: RollbackScope, trigger: RollbackTrigger,
                              reason: str, affected_agents: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute rollback procedure based on scope and trigger."""
        logger.warning(f"Initiating rollback: {scope.value} triggered by {trigger.value}",
                      reason=reason, affected_agents=affected_agents)

        rollback_start_time = time.time()

        # Record rollback initiation
        rollback_record = {
            "rollback_id": f"rollback_{int(time.time())}",
            "scope": scope.value,
            "trigger": trigger.value,
            "reason": reason,
            "affected_agents": affected_agents or [],
            "initiated_at": datetime.now().isoformat(),
            "status": "in_progress"
        }

        try:
            # Execute rollback based on scope
            if scope == RollbackScope.SINGLE_AGENT:
                result = await self._rollback_single_agent(affected_agents[0] if affected_agents else None)
            elif scope == RollbackScope.MULTIPLE_AGENTS:
                result = await self._rollback_multiple_agents(affected_agents or [])
            elif scope == RollbackScope.GLOBAL_ROLLBACK:
                result = await self._rollback_global()
            elif scope == RollbackScope.EMERGENCY_STOP:
                result = await self._emergency_stop()
            else:
                raise ValueError(f"Unknown rollback scope: {scope}")

            # Update rollback record
            rollback_record.update({
                "status": "completed",
                "result": result,
                "completed_at": datetime.now().isoformat(),
                "duration": time.time() - rollback_start_time
            })

            logger.info(f"Rollback completed successfully: {scope.value}",
                       duration=rollback_record["duration"])

        except Exception as e:
            rollback_record.update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat(),
                "duration": time.time() - rollback_start_time
            })
            logger.error(f"Rollback failed: {e}")

        # Store rollback record
        self.rollback_history.append(rollback_record)

        return rollback_record

    async def _rollback_single_agent(self, agent_type: str) -> Dict[str, Any]:
        """Rollback a single agent type to legacy implementation."""
        logger.info(f"Rolling back single agent: {agent_type}")

        # Disable ADK for this agent type
        feature_flags.disable_adk_for_agent(agent_type)

        # Clear agent cache for this agent type
        clear_agent_cache(pattern=agent_type)

        # Verify rollback
        verification_result = await self._verify_agent_rollback(agent_type)

        return {
            "agent_type": agent_type,
            "rollback_type": "single_agent",
            "cache_cleared": True,
            "feature_flag_updated": True,
            "verification": verification_result
        }

    async def _rollback_multiple_agents(self, agent_types: List[str]) -> Dict[str, Any]:
        """Rollback multiple agent types to legacy implementation."""
        logger.info(f"Rolling back multiple agents: {agent_types}")

        results = {}
        for agent_type in agent_types:
            result = await self._rollback_single_agent(agent_type)
            results[agent_type] = result

        return {
            "agent_types": agent_types,
            "rollback_type": "multiple_agents",
            "individual_results": results,
            "all_successful": all(r.get("verification", {}).get("success", False) for r in results.values())
        }

    async def _rollback_global(self) -> Dict[str, Any]:
        """Execute global rollback to legacy implementations."""
        logger.warning("Executing global rollback - all agents reverting to legacy")

        # Enable global rollback mode
        feature_flags.enable_global_rollback()

        # Clear all agent caches
        clear_agent_cache()

        # Get all agent types
        all_agent_types = ["analyst", "architect", "developer", "tester", "deployer"]

        # Verify rollback for all agents
        verification_results = {}
        for agent_type in all_agent_types:
            verification_results[agent_type] = await self._verify_agent_rollback(agent_type)

        return {
            "rollback_type": "global_rollback",
            "all_agent_types": all_agent_types,
            "cache_cleared": True,
            "global_rollback_enabled": True,
            "verification_results": verification_results,
            "all_verified": all(v.get("success", False) for v in verification_results.values())
        }

    async def _emergency_stop(self) -> Dict[str, Any]:
        """Execute emergency stop - immediate reversion to legacy."""
        logger.critical("EMERGENCY STOP ACTIVATED - Immediate rollback to legacy implementations")

        # Activate emergency stop
        feature_flags.emergency_stop()

        # Clear all caches immediately
        clear_agent_cache()

        # Get emergency status
        emergency_status = {
            "emergency_stop_activated": True,
            "all_caches_cleared": True,
            "legacy_agents_active": True,
            "timestamp": datetime.now().isoformat()
        }

        logger.critical("Emergency stop completed", **emergency_status)
        return emergency_status

    async def _verify_agent_rollback(self, agent_type: str) -> Dict[str, Any]:
        """Verify that an agent has been successfully rolled back."""
        try:
            # Check feature flag status
            adk_enabled = feature_flags.is_adk_enabled_for_agent(agent_type)
            flag_status = "ADK disabled" if not adk_enabled else "ADK still enabled"

            # Check agent implementation selection
            from adk_agent_factory import create_agent
            test_agent = create_agent(agent_type, "test_user", "test_project")
            implementation = getattr(test_agent, '_implementation', 'unknown')
            is_legacy = implementation.startswith("BMAD")

            verification_result = {
                "agent_type": agent_type,
                "success": not adk_enabled and is_legacy,
                "feature_flag_status": flag_status,
                "implementation_detected": implementation,
                "using_legacy": is_legacy,
                "verified_at": datetime.now().isoformat()
            }

            if verification_result["success"]:
                logger.info(f"Rollback verification successful for {agent_type}")
            else:
                logger.warning(f"Rollback verification failed for {agent_type}",
                             feature_flag_status=flag_status, implementation=implementation)

            return verification_result

        except Exception as e:
            logger.error(f"Rollback verification failed for {agent_type}: {e}")
            return {
                "agent_type": agent_type,
                "success": False,
                "error": str(e),
                "verified_at": datetime.now().isoformat()
            }

    def check_rollback_triggers(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any rollback triggers are met based on current metrics."""
        triggers = []

        # Check response time
        avg_response_time = metrics.get("average_response_time", 0)
        if avg_response_time > self.monitoring_thresholds["response_time_critical"]:
            triggers.append({
                "trigger": RollbackTrigger.PERFORMANCE_DEGRADATION,
                "scope": RollbackScope.GLOBAL_ROLLBACK,
                "reason": f"Critical response time: {avg_response_time}s > {self.monitoring_thresholds['response_time_critical']}s",
                "severity": "critical"
            })
        elif avg_response_time > self.monitoring_thresholds["response_time_warning"]:
            triggers.append({
                "trigger": RollbackTrigger.PERFORMANCE_DEGRADATION,
                "scope": RollbackScope.MULTIPLE_AGENTS,
                "reason": f"Warning response time: {avg_response_time}s > {self.monitoring_thresholds['response_time_warning']}s",
                "severity": "warning"
            })

        # Check error rate
        error_rate = metrics.get("error_rate", 0)
        if error_rate > self.monitoring_thresholds["error_rate_critical"]:
            triggers.append({
                "trigger": RollbackTrigger.ERROR_RATE_SPIKE,
                "scope": RollbackScope.GLOBAL_ROLLBACK,
                "reason": f"Critical error rate: {error_rate:.1%} > {self.monitoring_thresholds['error_rate_critical']:.1%}",
                "severity": "critical"
            })
        elif error_rate > self.monitoring_thresholds["error_rate_warning"]:
            triggers.append({
                "trigger": RollbackTrigger.ERROR_RATE_SPIKE,
                "scope": RollbackScope.MULTIPLE_AGENTS,
                "reason": f"Warning error rate: {error_rate:.1%} > {self.monitoring_thresholds['error_rate_warning']:.1%}",
                "severity": "warning"
            })

        # Check user complaints
        user_complaints = metrics.get("user_complaints_per_hour", 0)
        if user_complaints > self.monitoring_thresholds["user_complaints_threshold"]:
            triggers.append({
                "trigger": RollbackTrigger.USER_COMPLAINTS,
                "scope": RollbackScope.GLOBAL_ROLLBACK,
                "reason": f"High user complaints: {user_complaints} > {self.monitoring_thresholds['user_complaints_threshold']} per hour",
                "severity": "critical"
            })

        return triggers

    def get_rollback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get rollback history."""
        return self.rollback_history[-limit:] if self.rollback_history else []

    def get_rollback_statistics(self) -> Dict[str, Any]:
        """Get rollback statistics."""
        if not self.rollback_history:
            return {"total_rollbacks": 0, "message": "No rollback history available"}

        total_rollbacks = len(self.rollback_history)
        successful_rollbacks = sum(1 for r in self.rollback_history if r.get("status") == "completed")
        failed_rollbacks = total_rollbacks - successful_rollbacks

        # Group by scope
        scope_stats = {}
        for rollback in self.rollback_history:
            scope = rollback.get("scope", "unknown")
            scope_stats[scope] = scope_stats.get(scope, 0) + 1

        # Group by trigger
        trigger_stats = {}
        for rollback in self.rollback_history:
            trigger = rollback.get("trigger", "unknown")
            trigger_stats[trigger] = trigger_stats.get(trigger, 0) + 1

        return {
            "total_rollbacks": total_rollbacks,
            "successful_rollbacks": successful_rollbacks,
            "failed_rollbacks": failed_rollbacks,
            "success_rate": successful_rollbacks / total_rollbacks if total_rollbacks > 0 else 0,
            "scope_breakdown": scope_stats,
            "trigger_breakdown": trigger_stats,
            "most_recent_rollback": self.rollback_history[-1] if self.rollback_history else None
        }


# Global rollback manager instance
rollback_manager = ADKRollbackManager()


async def execute_rollback(scope: RollbackScope, trigger: RollbackTrigger, reason: str,
                          affected_agents: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience function to execute rollback."""
    return await rollback_manager.execute_rollback(scope, trigger, reason, affected_agents)


def check_rollback_triggers(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience function to check rollback triggers."""
    return rollback_manager.check_rollback_triggers(metrics)


def get_rollback_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Convenience function to get rollback history."""
    return rollback_manager.get_rollback_history(limit)


def get_rollback_statistics() -> Dict[str, Any]:
    """Convenience function to get rollback statistics."""
    return rollback_manager.get_rollback_statistics()


if __name__ == "__main__":
    # Example usage
    print("🚀 ADK Rollback Procedures Demo")
    print("=" * 50)

    # Simulate metrics that would trigger rollback
    test_metrics = {
        "average_response_time": 6.0,  # Above critical threshold
        "error_rate": 0.12,            # Above critical threshold
        "user_complaints_per_hour": 25 # Above threshold
    }

    # Check for rollback triggers
    triggers = check_rollback_triggers(test_metrics)

    print("Rollback Triggers Detected:")
    for trigger in triggers:
        print(f"  • {trigger['trigger'].value}: {trigger['reason']}")
        print(f"    Severity: {trigger['severity']}")
        print(f"    Scope: {trigger['scope'].value}")
        print()

    # Get rollback statistics
    stats = get_rollback_statistics()
    print(f"Rollback Statistics: {stats}")

    print("\n✅ Rollback procedures configured successfully")
