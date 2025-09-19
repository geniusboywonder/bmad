"""Quality Gate Service for HITL triggers and quality validation.

This service provides quality gate functionality for the HITL system,
including quality thresholds, validation criteria, and gate decisions.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class QualityGateStatus(Enum):
    """Quality gate status enumeration."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    PENDING = "pending"


class QualityGateResult:
    """Result of a quality gate evaluation."""
    
    def __init__(self, status: QualityGateStatus, score: float, details: Dict[str, Any]):
        self.status = status
        self.score = score
        self.details = details
        self.timestamp = None


class QualityGateService:
    """Service for managing quality gates and validation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.quality_thresholds = self.config.get('quality_thresholds', {
            'minimum_score': 0.8,
            'warning_threshold': 0.7,
            'critical_threshold': 0.9
        })
        logger.info("Quality Gate Service initialized", thresholds=self.quality_thresholds)
    
    async def evaluate_quality_gate(
        self, 
        phase: str, 
        artifacts: List[Dict[str, Any]], 
        metrics: Dict[str, float]
    ) -> QualityGateResult:
        """Evaluate a quality gate for a specific phase."""
        logger.info("Evaluating quality gate", phase=phase, artifact_count=len(artifacts))
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(artifacts, metrics)
        
        # Determine gate status
        status = self._determine_gate_status(quality_score)
        
        # Compile evaluation details
        details = {
            'phase': phase,
            'quality_score': quality_score,
            'artifact_count': len(artifacts),
            'metrics': metrics,
            'thresholds': self.quality_thresholds
        }
        
        result = QualityGateResult(status, quality_score, details)
        
        logger.info("Quality gate evaluated", 
                   phase=phase, 
                   status=status.value, 
                   score=quality_score)
        
        return result
    
    def _calculate_quality_score(
        self, 
        artifacts: List[Dict[str, Any]], 
        metrics: Dict[str, float]
    ) -> float:
        """Calculate overall quality score from artifacts and metrics."""
        if not artifacts and not metrics:
            return 0.0
        
        # Simple scoring algorithm - can be enhanced
        artifact_score = min(len(artifacts) / 3.0, 1.0)  # Expect at least 3 artifacts
        
        if metrics:
            metrics_score = sum(metrics.values()) / len(metrics)
        else:
            metrics_score = 0.5  # Default if no metrics
        
        # Weighted average
        overall_score = (artifact_score * 0.4) + (metrics_score * 0.6)
        
        return min(overall_score, 1.0)
    
    def _determine_gate_status(self, quality_score: float) -> QualityGateStatus:
        """Determine gate status based on quality score."""
        if quality_score >= self.quality_thresholds['minimum_score']:
            return QualityGateStatus.PASS
        elif quality_score >= self.quality_thresholds['warning_threshold']:
            return QualityGateStatus.WARNING
        else:
            return QualityGateStatus.FAIL
    
    async def get_quality_metrics(self, phase: str) -> Dict[str, float]:
        """Get quality metrics for a specific phase."""
        # Placeholder implementation
        return {
            'completeness': 0.85,
            'accuracy': 0.90,
            'consistency': 0.80,
            'coverage': 0.75
        }
    
    async def validate_phase_completion(
        self, 
        phase: str, 
        artifacts: List[Dict[str, Any]]
    ) -> bool:
        """Validate if a phase is ready for completion."""
        metrics = await self.get_quality_metrics(phase)
        result = await self.evaluate_quality_gate(phase, artifacts, metrics)
        
        return result.status in [QualityGateStatus.PASS, QualityGateStatus.WARNING]
    
    def get_quality_requirements(self, phase: str) -> Dict[str, Any]:
        """Get quality requirements for a specific phase."""
        requirements = {
            'analysis': {
                'min_artifacts': 2,
                'required_types': ['requirements', 'analysis'],
                'min_score': 0.8
            },
            'design': {
                'min_artifacts': 3,
                'required_types': ['architecture', 'design', 'specifications'],
                'min_score': 0.85
            },
            'implementation': {
                'min_artifacts': 4,
                'required_types': ['code', 'tests', 'documentation'],
                'min_score': 0.9
            },
            'testing': {
                'min_artifacts': 3,
                'required_types': ['test_results', 'coverage', 'validation'],
                'min_score': 0.95
            },
            'deployment': {
                'min_artifacts': 2,
                'required_types': ['deployment_config', 'monitoring'],
                'min_score': 0.9
            }
        }
        
        return requirements.get(phase, {
            'min_artifacts': 1,
            'required_types': [],
            'min_score': 0.8
        })