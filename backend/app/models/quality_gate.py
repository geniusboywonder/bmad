"""Quality Gate Models for quality validation and gating.

This module defines the data models for quality gates, validation criteria,
and quality metrics for the BMAD Enterprise AI Platform.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4


class QualityGateType(Enum):
    """Types of quality gates."""
    PHASE_GATE = "phase_gate"
    MILESTONE_GATE = "milestone_gate"
    APPROVAL_GATE = "approval_gate"
    VALIDATION_GATE = "validation_gate"
    DEPLOYMENT_GATE = "deployment_gate"


class QualityGateStatus(Enum):
    """Status of quality gates."""
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    WAIVED = "waived"


class QualityCriteria(BaseModel):
    """Quality criteria for validation."""
    
    name: str
    description: str
    weight: float = 1.0
    threshold: float = 0.8
    required: bool = True
    validation_type: str = "automatic"  # automatic, manual, hybrid


class QualityMetric(BaseModel):
    """Quality metric measurement."""
    
    name: str
    value: float
    unit: str = "score"
    description: Optional[str] = None
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class QualityGate(BaseModel):
    """Quality gate model for validation checkpoints."""
    
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    phase: str
    gate_type: QualityGateType
    status: QualityGateStatus = QualityGateStatus.PENDING
    
    name: str
    description: str
    
    # Criteria and metrics
    criteria: List[QualityCriteria] = Field(default_factory=list)
    metrics: List[QualityMetric] = Field(default_factory=list)
    
    # Scoring
    overall_score: Optional[float] = None
    passing_score: float = 0.8
    warning_score: float = 0.7
    
    # Validation results
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    validation_details: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    validated_by: Optional[str] = None
    
    # Waiver information
    waived: bool = False
    waiver_reason: Optional[str] = None
    waived_by: Optional[str] = None
    waived_at: Optional[datetime] = None
    
    model_config = ConfigDict(use_enum_values=True)


class QualityGateResult(BaseModel):
    """Result of quality gate evaluation."""
    
    gate_id: UUID
    status: QualityGateStatus
    overall_score: float
    
    # Detailed results
    criteria_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    metric_results: Dict[str, float] = Field(default_factory=dict)
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    
    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluator: Optional[str] = None


class QualityReport(BaseModel):
    """Quality report for a project or phase."""
    
    project_id: UUID
    phase: Optional[str] = None
    
    # Gate summaries
    total_gates: int = 0
    passed_gates: int = 0
    failed_gates: int = 0
    warning_gates: int = 0
    waived_gates: int = 0
    
    # Overall metrics
    overall_quality_score: Optional[float] = None
    quality_trend: Optional[str] = None  # improving, declining, stable
    
    # Detailed results
    gate_results: List[QualityGateResult] = Field(default_factory=list)
    
    # Recommendations
    summary_recommendations: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    report_period: Optional[str] = None