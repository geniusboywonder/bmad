"""LLM usage tracking and cost monitoring service.

This module provides comprehensive monitoring of LLM usage patterns, costs,
and performance metrics for operational oversight and optimization.
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID
import structlog
import json
import re

logger = structlog.get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GOOGLE = "google"


@dataclass
class UsageMetrics:
    """Individual LLM request metrics."""
    timestamp: datetime
    agent_type: str
    project_id: Optional[UUID]
    task_id: Optional[UUID] 
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    response_time_ms: float = 0.0
    estimated_cost: float = 0.0
    success: bool = True
    error_type: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        data = asdict(self)
        # Convert UUID and datetime to strings
        data['timestamp'] = self.timestamp.isoformat()
        if data['project_id']:
            data['project_id'] = str(data['project_id'])
        if data['task_id']:
            data['task_id'] = str(data['task_id'])
        return data


@dataclass 
class CostBreakdown:
    """Cost analysis breakdown."""
    total_cost: float
    cost_by_agent: Dict[str, float]
    cost_by_model: Dict[str, float]
    token_usage: Dict[str, int]
    request_count: int
    success_rate: float
    average_response_time: float
    time_period: Dict[str, str]  # start/end timestamps


@dataclass
class UsageReport:
    """Comprehensive usage report."""
    project_id: Optional[UUID]
    date_range: Dict[str, datetime]
    cost_breakdown: CostBreakdown
    top_agents_by_usage: List[Dict[str, Any]]
    top_agents_by_cost: List[Dict[str, Any]]
    hourly_distribution: Dict[str, Dict[str, Any]]
    error_analysis: Dict[str, Any]
    recommendations: List[str]


class LLMUsageTracker:
    """Comprehensive LLM usage tracking and cost monitoring.
    
    This class provides detailed monitoring including:
    - Token consumption and cost calculation
    - Performance metrics and response times
    - Agent-specific usage attribution
    - Error patterns and retry statistics
    - Cost optimization recommendations
    """
    
    # OpenAI pricing per 1K tokens (as of 2024)
    OPENAI_PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03}, 
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
    }
    
    # Anthropic pricing per 1K tokens (as of 2024)
    ANTHROPIC_PRICING = {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
    }
    
    # Google pricing per 1K tokens (as of 2024)
    GOOGLE_PRICING = {
        "gemini-pro": {"input": 0.00025, "output": 0.0005},
        "gemini-pro-vision": {"input": 0.00025, "output": 0.0005}
    }
    
    def __init__(self, enable_tracking: bool = True):
        """Initialize usage tracker.
        
        Args:
            enable_tracking: Whether to track usage (for testing/debugging)
        """
        self.enable_tracking = enable_tracking
        self.usage_history: List[UsageMetrics] = []
        self.session_stats = {
            'requests_tracked': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'errors_tracked': 0
        }
    
    async def track_request(
        self,
        agent_type: str,
        tokens_used: int,
        response_time: float,
        cost: float,
        success: bool = True,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        error_type: Optional[str] = None,
        retry_count: int = 0
    ):
        """Track individual LLM request metrics.
        
        Args:
            agent_type: Type of agent making the request
            tokens_used: Total tokens consumed
            response_time: Response time in milliseconds
            cost: Estimated cost in USD
            success: Whether request was successful
            project_id: Associated project UUID
            task_id: Associated task UUID
            provider: LLM provider name
            model: Model name used
            input_tokens: Input tokens (if available)
            output_tokens: Output tokens (if available)
            error_type: Type of error if failed
            retry_count: Number of retries attempted
        """
        if not self.enable_tracking:
            return
        
        # Estimate input/output split if not provided
        if input_tokens is None or output_tokens is None:
            input_tokens, output_tokens = self._estimate_token_split(
                tokens_used, response_time
            )
        
        metrics = UsageMetrics(
            timestamp=datetime.now(timezone.utc),
            agent_type=agent_type,
            project_id=project_id,
            task_id=task_id,
            provider=provider,
            model=model,
            tokens_used=tokens_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_time_ms=response_time,
            estimated_cost=cost,
            success=success,
            error_type=error_type,
            retry_count=retry_count
        )
        
        self.usage_history.append(metrics)
        
        # Update session stats
        self.session_stats['requests_tracked'] += 1
        self.session_stats['total_tokens'] += tokens_used
        self.session_stats['total_cost'] += cost
        if not success:
            self.session_stats['errors_tracked'] += 1
        
        # Log the metrics
        logger.info("LLM request tracked",
                   **metrics.to_dict())
        
        # Log summary for significant costs
        if cost > 0.01:  # More than 1 cent
            logger.warning("High-cost LLM request",
                         agent_type=agent_type,
                         cost=cost,
                         tokens=tokens_used,
                         model=model)
    
    async def calculate_costs(
        self,
        input_tokens: int,
        output_tokens: int,
        provider: str = "openai",
        model: str = "gpt-4o-mini"
    ) -> float:
        """Calculate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: LLM provider
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        pricing_table = self._get_pricing_table(provider)
        
        if model not in pricing_table:
            logger.warning("Unknown model for cost calculation",
                         provider=provider,
                         model=model,
                         available_models=list(pricing_table.keys()))
            # Use default pricing
            model = list(pricing_table.keys())[0]
        
        model_pricing = pricing_table[model]
        
        # Calculate cost per 1K tokens
        input_cost = (input_tokens / 1000.0) * model_pricing["input"]
        output_cost = (output_tokens / 1000.0) * model_pricing["output"]
        
        total_cost = input_cost + output_cost
        
        logger.debug("Cost calculation",
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    input_cost=input_cost,
                    output_cost=output_cost,
                    total_cost=total_cost)
        
        return round(total_cost, 6)  # Round to microsent precision
    
    async def generate_usage_report(
        self,
        project_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageReport:
        """Generate comprehensive usage report.
        
        Args:
            project_id: Filter by project (None for all projects)
            start_date: Start of date range (None for all time)
            end_date: End of date range (None for now)
            
        Returns:
            Detailed usage report
        """
        # Set default date range
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=30)  # Last 30 days
        
        # Filter usage history
        filtered_usage = [
            metric for metric in self.usage_history
            if (project_id is None or metric.project_id == project_id) and
               start_date <= metric.timestamp <= end_date
        ]
        
        if not filtered_usage:
            logger.warning("No usage data found for report",
                         project_id=project_id,
                         start_date=start_date,
                         end_date=end_date)
            
            return self._generate_empty_report(project_id, start_date, end_date)
        
        # Generate cost breakdown
        cost_breakdown = self._analyze_costs(filtered_usage, start_date, end_date)
        
        # Analyze agent usage patterns
        top_agents_by_usage = self._top_agents_by_metric(
            filtered_usage, lambda m: m.tokens_used, "tokens"
        )
        top_agents_by_cost = self._top_agents_by_metric(
            filtered_usage, lambda m: m.estimated_cost, "cost"
        )
        
        # Hourly distribution analysis
        hourly_dist = self._analyze_hourly_distribution(filtered_usage)
        
        # Error analysis
        error_analysis = self._analyze_errors(filtered_usage)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            filtered_usage, cost_breakdown, error_analysis
        )
        
        report = UsageReport(
            project_id=project_id,
            date_range={"start": start_date, "end": end_date},
            cost_breakdown=cost_breakdown,
            top_agents_by_usage=top_agents_by_usage,
            top_agents_by_cost=top_agents_by_cost,
            hourly_distribution=hourly_dist,
            error_analysis=error_analysis,
            recommendations=recommendations
        )
        
        logger.info("Usage report generated",
                   project_id=project_id,
                   date_range_days=(end_date - start_date).days,
                   total_requests=len(filtered_usage),
                   total_cost=cost_breakdown.total_cost)
        
        return report
    
    async def detect_usage_anomalies(
        self,
        lookback_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Detect unusual usage patterns or cost spikes.
        
        Args:
            lookback_hours: How far back to analyze
            
        Returns:
            List of detected anomalies
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        recent_usage = [
            m for m in self.usage_history
            if m.timestamp >= cutoff_time
        ]
        
        anomalies = []
        
        if not recent_usage:
            return anomalies
        
        # Check for cost spikes
        avg_cost = sum(m.estimated_cost for m in recent_usage) / len(recent_usage)
        cost_threshold = avg_cost * 5  # 5x average
        
        for metric in recent_usage:
            if metric.estimated_cost > cost_threshold:
                anomalies.append({
                    "type": "cost_spike",
                    "timestamp": metric.timestamp.isoformat(),
                    "agent_type": metric.agent_type,
                    "cost": metric.estimated_cost,
                    "threshold": cost_threshold,
                    "severity": "high" if metric.estimated_cost > cost_threshold * 2 else "medium"
                })
        
        # Check for high error rates
        error_rate = sum(1 for m in recent_usage if not m.success) / len(recent_usage)
        if error_rate > 0.2:  # >20% error rate
            anomalies.append({
                "type": "high_error_rate",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_rate": error_rate,
                "threshold": 0.2,
                "severity": "high" if error_rate > 0.5 else "medium",
                "total_requests": len(recent_usage)
            })
        
        # Check for unusual token usage
        avg_tokens = sum(m.tokens_used for m in recent_usage) / len(recent_usage)
        token_threshold = avg_tokens * 10  # 10x average
        
        for metric in recent_usage:
            if metric.tokens_used > token_threshold:
                anomalies.append({
                    "type": "token_usage_spike",
                    "timestamp": metric.timestamp.isoformat(),
                    "agent_type": metric.agent_type,
                    "tokens_used": metric.tokens_used,
                    "threshold": token_threshold,
                    "severity": "medium"
                })
        
        if anomalies:
            logger.warning("Usage anomalies detected",
                         anomaly_count=len(anomalies),
                         lookback_hours=lookback_hours)
        
        return anomalies
    
    def estimate_tokens(self, text: str, is_input: bool = True) -> int:
        """Estimate token count from text.
        
        Simple approximation: ~4 characters per token for English text.
        This is less accurate than tiktoken but much faster.
        
        Args:
            text: Text to estimate tokens for
            is_input: Whether this is input text (affects estimation)
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Basic approximation: 4 characters per token
        char_count = len(text)
        token_estimate = max(1, char_count // 4)
        
        # Adjust for code vs natural language
        if self._appears_to_be_code(text):
            # Code tends to have more tokens per character
            token_estimate = int(token_estimate * 1.3)
        
        return token_estimate
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        stats = self.session_stats.copy()
        
        # Calculate rates
        if stats['requests_tracked'] > 0:
            stats['error_rate'] = stats['errors_tracked'] / stats['requests_tracked']
            stats['average_cost_per_request'] = stats['total_cost'] / stats['requests_tracked']
            stats['average_tokens_per_request'] = stats['total_tokens'] / stats['requests_tracked']
        else:
            stats['error_rate'] = 0.0
            stats['average_cost_per_request'] = 0.0
            stats['average_tokens_per_request'] = 0.0
        
        return stats
    
    def reset_session_stats(self):
        """Reset session statistics."""
        self.session_stats = {
            'requests_tracked': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'errors_tracked': 0
        }
    
    def _get_pricing_table(self, provider: str) -> Dict[str, Dict[str, float]]:
        """Get pricing table for provider."""
        if provider.lower() == "openai":
            return self.OPENAI_PRICING
        elif provider.lower() == "anthropic":
            return self.ANTHROPIC_PRICING
        elif provider.lower() == "google":
            return self.GOOGLE_PRICING
        else:
            logger.warning("Unknown provider, using OpenAI pricing", provider=provider)
            return self.OPENAI_PRICING
    
    def _estimate_token_split(self, total_tokens: int, response_time: float) -> Tuple[int, int]:
        """Estimate input/output token split."""
        # Heuristic: longer response times usually mean more output tokens
        # Typical split is 70% input, 30% output for most use cases
        
        if response_time > 5000:  # > 5 seconds, likely lots of output
            input_ratio = 0.4
        elif response_time > 2000:  # > 2 seconds
            input_ratio = 0.6
        else:  # Fast response
            input_ratio = 0.8
        
        input_tokens = int(total_tokens * input_ratio)
        output_tokens = total_tokens - input_tokens
        
        return input_tokens, output_tokens
    
    def _appears_to_be_code(self, text: str) -> bool:
        """Simple heuristic to detect if text contains code."""
        code_indicators = [
            '{', '}', ';', 'function', 'class', 'def ', 'import ',
            'const ', 'var ', 'let ', '===', '!==', '->', '=>'
        ]
        
        return any(indicator in text for indicator in code_indicators)
    
    def _analyze_costs(
        self,
        usage_data: List[UsageMetrics],
        start_date: datetime,
        end_date: datetime
    ) -> CostBreakdown:
        """Analyze cost breakdown from usage data."""
        total_cost = sum(m.estimated_cost for m in usage_data)
        
        # Cost by agent
        cost_by_agent = {}
        for metric in usage_data:
            agent = metric.agent_type
            cost_by_agent[agent] = cost_by_agent.get(agent, 0.0) + metric.estimated_cost
        
        # Cost by model
        cost_by_model = {}
        for metric in usage_data:
            model = metric.model
            cost_by_model[model] = cost_by_model.get(model, 0.0) + metric.estimated_cost
        
        # Token usage
        token_usage = {
            "total": sum(m.tokens_used for m in usage_data),
            "input": sum(m.input_tokens for m in usage_data),
            "output": sum(m.output_tokens for m in usage_data)
        }
        
        # Success rate
        successful_requests = sum(1 for m in usage_data if m.success)
        success_rate = successful_requests / len(usage_data) if usage_data else 0.0
        
        # Average response time
        avg_response_time = sum(m.response_time_ms for m in usage_data) / len(usage_data) if usage_data else 0.0
        
        return CostBreakdown(
            total_cost=total_cost,
            cost_by_agent=cost_by_agent,
            cost_by_model=cost_by_model,
            token_usage=token_usage,
            request_count=len(usage_data),
            success_rate=success_rate,
            average_response_time=avg_response_time,
            time_period={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )
    
    def _top_agents_by_metric(
        self,
        usage_data: List[UsageMetrics],
        metric_func,
        metric_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top agents by specified metric."""
        agent_metrics = {}
        
        for metric in usage_data:
            agent = metric.agent_type
            if agent not in agent_metrics:
                agent_metrics[agent] = {
                    "agent_type": agent,
                    "total_value": 0,
                    "request_count": 0
                }
            
            agent_metrics[agent]["total_value"] += metric_func(metric)
            agent_metrics[agent]["request_count"] += 1
        
        # Calculate averages and sort
        for agent_data in agent_metrics.values():
            agent_data[f"average_{metric_name}"] = (
                agent_data["total_value"] / agent_data["request_count"]
            )
        
        sorted_agents = sorted(
            agent_metrics.values(),
            key=lambda x: x["total_value"],
            reverse=True
        )
        
        return sorted_agents[:limit]
    
    def _analyze_hourly_distribution(self, usage_data: List[UsageMetrics]) -> Dict[str, Dict[str, Any]]:
        """Analyze usage distribution by hour of day."""
        hourly_stats = {}
        
        for metric in usage_data:
            hour = metric.timestamp.hour
            hour_key = f"{hour:02d}:00"
            
            if hour_key not in hourly_stats:
                hourly_stats[hour_key] = {
                    "request_count": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "error_count": 0
                }
            
            hourly_stats[hour_key]["request_count"] += 1
            hourly_stats[hour_key]["total_cost"] += metric.estimated_cost
            hourly_stats[hour_key]["total_tokens"] += metric.tokens_used
            if not metric.success:
                hourly_stats[hour_key]["error_count"] += 1
        
        return hourly_stats
    
    def _analyze_errors(self, usage_data: List[UsageMetrics]) -> Dict[str, Any]:
        """Analyze error patterns."""
        error_types = {}
        failed_requests = [m for m in usage_data if not m.success]
        
        for metric in failed_requests:
            error_type = metric.error_type or "unknown"
            if error_type not in error_types:
                error_types[error_type] = {
                    "count": 0,
                    "agents_affected": set(),
                    "avg_retry_count": 0
                }
            
            error_types[error_type]["count"] += 1
            error_types[error_type]["agents_affected"].add(metric.agent_type)
            error_types[error_type]["avg_retry_count"] += metric.retry_count
        
        # Convert sets to lists for JSON serialization
        for error_data in error_types.values():
            error_data["agents_affected"] = list(error_data["agents_affected"])
            if error_data["count"] > 0:
                error_data["avg_retry_count"] /= error_data["count"]
        
        return {
            "total_errors": len(failed_requests),
            "error_rate": len(failed_requests) / len(usage_data) if usage_data else 0.0,
            "error_types": error_types
        }
    
    def _generate_recommendations(
        self,
        usage_data: List[UsageMetrics],
        cost_breakdown: CostBreakdown,
        error_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Cost optimization
        if cost_breakdown.total_cost > 1.0:  # > $1
            recommendations.append(
                f"Consider model optimization - total cost is ${cost_breakdown.total_cost:.2f}. "
                f"Evaluate if cheaper models could be used for some agents."
            )
        
        # Error rate concerns
        if error_analysis["error_rate"] > 0.1:  # > 10%
            recommendations.append(
                f"High error rate detected ({error_analysis['error_rate']:.1%}). "
                f"Review error patterns and consider implementing circuit breakers."
            )
        
        # Response time optimization
        if cost_breakdown.average_response_time > 10000:  # > 10 seconds
            recommendations.append(
                f"Average response time is {cost_breakdown.average_response_time/1000:.1f}s. "
                f"Consider prompt optimization or model selection review."
            )
        
        # Token usage efficiency
        avg_tokens_per_request = cost_breakdown.token_usage["total"] / cost_breakdown.request_count
        if avg_tokens_per_request > 2000:
            recommendations.append(
                f"High average token usage ({avg_tokens_per_request:.0f} tokens/request). "
                f"Review prompt lengths and response requirements."
            )
        
        return recommendations
    
    def _generate_empty_report(
        self,
        project_id: Optional[UUID],
        start_date: datetime,
        end_date: datetime
    ) -> UsageReport:
        """Generate empty report when no data is found."""
        empty_cost_breakdown = CostBreakdown(
            total_cost=0.0,
            cost_by_agent={},
            cost_by_model={},
            token_usage={"total": 0, "input": 0, "output": 0},
            request_count=0,
            success_rate=0.0,
            average_response_time=0.0,
            time_period={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )
        
        return UsageReport(
            project_id=project_id,
            date_range={"start": start_date, "end": end_date},
            cost_breakdown=empty_cost_breakdown,
            top_agents_by_usage=[],
            top_agents_by_cost=[],
            hourly_distribution={},
            error_analysis={"total_errors": 0, "error_rate": 0.0, "error_types": {}},
            recommendations=["No usage data available for the specified period."]
        )