"""
Usage Metrics Model for BMAD Core Template System

This module defines models for tracking and analyzing LLM usage metrics,
costs, and performance data across different providers and agents.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OTHER = "other"


class MetricType(str, Enum):
    """Types of metrics that can be tracked."""
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    RETRY_COUNT = "retry_count"


class UsageRecord(BaseModel):
    """
    Individual usage record for LLM requests.

    This model captures detailed metrics for each LLM API call,
    enabling comprehensive cost tracking and performance analysis.
    """

    record_id: str = Field(default_factory=lambda: str(UUID.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Context information
    project_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    workflow_id: Optional[str] = None
    agent_type: str
    agent_id: Optional[str] = None

    # LLM provider and model details
    provider: LLMProvider
    model: str
    model_version: Optional[str] = None

    # Token usage metrics
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0  # For providers that support caching

    # Cost metrics
    total_cost: float = 0.0
    input_cost: float = 0.0
    output_cost: float = 0.0
    cached_cost: float = 0.0

    # Performance metrics
    response_time_ms: float = 0.0
    time_to_first_token_ms: Optional[float] = None
    tokens_per_second: Optional[float] = None

    # Request metadata
    request_type: str = "chat_completion"  # chat_completion, embedding, etc.
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    prompt_length: Optional[int] = None

    # Success and error tracking
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    retry_success: bool = False

    # Additional metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None

    # Custom tags for categorization
    tags: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )

    def dict(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = super().dict(**kwargs)
        # Ensure datetime and UUID fields are properly serialized
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        if isinstance(data.get('project_id'), UUID):
            data['project_id'] = str(data['project_id'])
        if isinstance(data.get('task_id'), UUID):
            data['task_id'] = str(data['task_id'])
        return data

    def calculate_efficiency_score(self) -> float:
        """Calculate efficiency score based on cost per token."""
        if self.total_tokens == 0:
            return 0.0

        cost_per_token = self.total_cost / self.total_tokens

        # Normalize to 0-1 scale (lower cost per token = higher efficiency)
        # Assuming $0.001 per token is baseline (100% efficiency)
        baseline_cost = 0.001
        efficiency = max(0.0, min(1.0, baseline_cost / cost_per_token))

        return efficiency

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get detailed cost breakdown."""
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "cached_cost": self.cached_cost,
            "total_cost": self.total_cost,
            "cost_per_token": self.total_cost / self.total_tokens if self.total_tokens > 0 else 0.0
        }

    def get_token_breakdown(self) -> Dict[str, int]:
        """Get detailed token breakdown."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "total_tokens": self.total_tokens,
            "new_tokens": self.total_tokens - self.cached_tokens
        }

    def is_high_cost(self, threshold: float = 0.1) -> bool:
        """Check if this request is considered high cost."""
        return self.total_cost >= threshold

    def is_slow_response(self, threshold_ms: float = 5000) -> bool:
        """Check if this request had a slow response."""
        return self.response_time_ms >= threshold_ms

    def is_high_token_usage(self, threshold: int = 4000) -> bool:
        """Check if this request used a high number of tokens."""
        return self.total_tokens >= threshold


class UsageAggregate(BaseModel):
    """
    Aggregated usage metrics for analysis and reporting.

    This model provides summarized metrics across multiple usage records,
    enabling trend analysis and cost optimization insights.
    """

    aggregate_id: str = Field(default_factory=lambda: str(UUID.uuid4()))
    time_period_start: datetime
    time_period_end: datetime
    aggregation_level: str = "hourly"  # hourly, daily, weekly, monthly

    # Context filters
    project_id: Optional[UUID] = None
    agent_type: Optional[str] = None
    provider: Optional[LLMProvider] = None
    model: Optional[str] = None

    # Aggregated metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Token metrics
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0

    # Cost metrics
    total_cost: float = 0.0
    input_cost: float = 0.0
    output_cost: float = 0.0
    cached_cost: float = 0.0

    # Performance metrics
    avg_response_time_ms: float = 0.0
    min_response_time_ms: Optional[float] = None
    max_response_time_ms: Optional[float] = None
    p95_response_time_ms: Optional[float] = None

    # Error analysis
    error_count: int = 0
    error_types: Dict[str, int] = Field(default_factory=dict)
    retry_count: int = 0
    avg_retry_count: float = 0.0

    # Efficiency metrics
    avg_cost_per_token: float = 0.0
    avg_tokens_per_request: float = 0.0
    success_rate: float = 0.0
    efficiency_score: float = 0.0

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    record_count: int = 0  # Number of individual records aggregated

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )

    def dict(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = super().dict(**kwargs)
        # Ensure datetime and UUID fields are properly serialized
        for date_field in ['time_period_start', 'time_period_end', 'created_at']:
            if isinstance(data.get(date_field), datetime):
                data[date_field] = data[date_field].isoformat()
        if isinstance(data.get('project_id'), UUID):
            data['project_id'] = str(data['project_id'])
        return data

    def calculate_rates(self) -> Dict[str, float]:
        """Calculate various rates and percentages."""
        if self.total_requests == 0:
            return {
                "success_rate": 0.0,
                "error_rate": 0.0,
                "retry_rate": 0.0
            }

        return {
            "success_rate": self.successful_requests / self.total_requests,
            "error_rate": self.failed_requests / self.total_requests,
            "retry_rate": self.retry_count / self.total_requests if self.retry_count > 0 else 0.0
        }

    def get_cost_efficiency(self) -> Dict[str, float]:
        """Get cost efficiency metrics."""
        if self.total_tokens == 0:
            return {
                "cost_per_token": 0.0,
                "tokens_per_dollar": 0.0
            }

        cost_per_token = self.total_cost / self.total_tokens
        tokens_per_dollar = self.total_tokens / self.total_cost if self.total_cost > 0 else 0.0

        return {
            "cost_per_token": cost_per_token,
            "tokens_per_dollar": tokens_per_dollar
        }

    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        return {
            "avg_response_time_ms": self.avg_response_time_ms,
            "min_response_time_ms": self.min_response_time_ms or 0.0,
            "max_response_time_ms": self.max_response_time_ms or 0.0,
            "p95_response_time_ms": self.p95_response_time_ms or self.avg_response_time_ms
        }


class CostOptimizationRecommendation(BaseModel):
    """
    Cost optimization recommendation based on usage analysis.

    This model represents actionable recommendations for reducing costs
    and improving efficiency in LLM usage.
    """

    recommendation_id: str = Field(default_factory=lambda: str(UUID.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Context
    project_id: Optional[UUID] = None
    agent_type: Optional[str] = None

    # Recommendation details
    title: str
    description: str
    recommendation_type: str  # model_switch, prompt_optimization, caching, etc.

    # Impact assessment
    estimated_savings_percent: float = 0.0
    estimated_savings_absolute: float = 0.0
    confidence_level: float = 0.0  # 0.0 to 1.0

    # Implementation details
    implementation_effort: str = "medium"  # low, medium, high
    implementation_steps: List[str] = Field(default_factory=list)

    # Supporting data
    current_cost: float = 0.0
    projected_cost: float = 0.0
    affected_requests: int = 0

    # Metadata
    data_source: str = "usage_analysis"
    priority: str = "medium"  # low, medium, high, critical

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )

    def dict(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = super().dict(**kwargs)
        # Ensure datetime and UUID fields are properly serialized
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        if isinstance(data.get('project_id'), UUID):
            data['project_id'] = str(data['project_id'])
        return data

    def get_roi_estimate(self) -> Dict[str, Any]:
        """Get return on investment estimate."""
        if self.current_cost == 0:
            return {"roi_percent": 0.0, "payback_period_months": 0.0}

        monthly_savings = self.estimated_savings_absolute
        roi_percent = (monthly_savings / self.current_cost) * 100

        # Estimate payback period based on implementation effort
        effort_multipliers = {"low": 1, "medium": 2, "high": 4}
        base_payback_months = 1
        payback_period_months = base_payback_months * effort_multipliers.get(self.implementation_effort, 2)

        return {
            "roi_percent": roi_percent,
            "payback_period_months": payback_period_months,
            "monthly_savings": monthly_savings
        }


class UsageAlert(BaseModel):
    """
    Alert for unusual usage patterns or cost anomalies.

    This model represents alerts that can be triggered based on
    usage monitoring and anomaly detection.
    """

    alert_id: str = Field(default_factory=lambda: str(UUID.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Alert context
    project_id: Optional[UUID] = None
    agent_type: Optional[str] = None

    # Alert details
    alert_type: str  # cost_spike, error_rate, performance_degradation, etc.
    severity: str = "medium"  # low, medium, high, critical
    title: str
    description: str

    # Alert data
    threshold_value: float = 0.0
    actual_value: float = 0.0
    baseline_value: Optional[float] = None

    # Affected metrics
    affected_metric: MetricType
    time_window_minutes: int = 60

    # Resolution status
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    # Metadata
    alert_source: str = "usage_monitor"
    tags: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )

    def dict(self, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = super().dict(**kwargs)
        # Ensure datetime and UUID fields are properly serialized
        for date_field in ['timestamp', 'resolved_at']:
            if isinstance(data.get(date_field), datetime):
                data[date_field] = data[date_field].isoformat()
        if isinstance(data.get('project_id'), UUID):
            data['project_id'] = str(data['project_id'])
        return data

    def resolve(self, notes: str = "") -> None:
        """Mark alert as resolved."""
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        self.resolution_notes = notes

    def get_age_minutes(self) -> float:
        """Get age of alert in minutes."""
        resolved_time = self.resolved_at if self.resolved else datetime.now(timezone.utc)
        return (resolved_time - self.timestamp).total_seconds() / 60

    def is_critical(self) -> bool:
        """Check if alert is critical."""
        return self.severity == "critical"

    def get_deviation_percent(self) -> float:
        """Get percentage deviation from baseline."""
        if not self.baseline_value or self.baseline_value == 0:
            return 0.0

        return ((self.actual_value - self.baseline_value) / self.baseline_value) * 100


class ProviderPricing(BaseModel):
    """
    Pricing information for LLM providers.

    This model stores current pricing information for different providers
    and models to enable accurate cost calculations.
    """

    provider: LLMProvider
    model: str
    model_version: Optional[str] = None

    # Pricing per 1K tokens
    input_price_per_1k: float = 0.0
    output_price_per_1k: float = 0.0
    cached_input_price_per_1k: Optional[float] = None

    # Additional costs
    request_price: float = 0.0  # Per request cost
    image_price_per_unit: Optional[float] = None  # For vision models

    # Metadata
    effective_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    currency: str = "USD"
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "provider_api"

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

    def calculate_cost(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0) -> Dict[str, float]:
        """Calculate cost for given token usage."""
        input_cost = (input_tokens / 1000.0) * self.input_price_per_1k
        output_cost = (output_tokens / 1000.0) * self.output_price_per_1k

        cached_cost = 0.0
        if self.cached_input_price_per_1k:
            cached_cost = (cached_tokens / 1000.0) * self.cached_input_price_per_1k

        total_cost = input_cost + output_cost + cached_cost + self.request_price

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "cached_cost": cached_cost,
            "request_cost": self.request_price,
            "total_cost": total_cost
        }

    def is_current(self, days_valid: int = 30) -> bool:
        """Check if pricing information is current."""
        age_days = (datetime.now(timezone.utc) - self.last_updated).days
        return age_days <= days_valid
