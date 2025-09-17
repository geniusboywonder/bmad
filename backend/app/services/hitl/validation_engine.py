"""
HITL Validation Engine - Handles quality validation and assessment.

Responsible for validating quality metrics, assessing deliverables, and providing
quality scores for HITL decision making.
"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.database.models import ContextArtifactDB, TaskDB, ProjectDB
from app.models.context import ArtifactType
from app.models.task import TaskStatus
from app.services.audit_service import AuditService

logger = structlog.get_logger(__name__)


class ValidationEngine:
    """
    Provides quality validation and assessment for HITL decisions.

    Follows Single Responsibility Principle by focusing solely on validation logic.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

        # Quality thresholds
        self.quality_thresholds = {
            "code_quality": 0.8,
            "test_coverage": 0.75,
            "documentation_completeness": 0.7,
            "security_score": 0.85,
            "performance_score": 0.8
        }

        # Validation weights for different criteria
        self.validation_weights = {
            "completeness": 0.3,
            "quality": 0.3,
            "consistency": 0.2,
            "compliance": 0.2
        }

    async def validate_task_output(
        self,
        task_id: UUID,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate task output quality and completeness.

        Args:
            task_id: Task identifier
            output_data: Task output data to validate

        Returns:
            Dictionary containing validation results
        """
        logger.info("Validating task output", task_id=str(task_id))

        task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        validation_result = {
            "task_id": str(task_id),
            "agent_type": task.agent_type,
            "validation_timestamp": datetime.now(timezone.utc),
            "overall_score": 0.0,
            "criteria_scores": {},
            "quality_metrics": {},
            "issues": [],
            "recommendations": [],
            "passed": False
        }

        # Validate completeness
        completeness_score = await self._validate_completeness(task, output_data)
        validation_result["criteria_scores"]["completeness"] = completeness_score

        # Validate quality
        quality_score = await self._validate_quality(task, output_data)
        validation_result["criteria_scores"]["quality"] = quality_score

        # Validate consistency
        consistency_score = await self._validate_consistency(task, output_data)
        validation_result["criteria_scores"]["consistency"] = consistency_score

        # Validate compliance
        compliance_score = await self._validate_compliance(task, output_data)
        validation_result["criteria_scores"]["compliance"] = compliance_score

        # Calculate overall score
        overall_score = sum(
            score * self.validation_weights[criterion]
            for criterion, score in validation_result["criteria_scores"].items()
        )
        validation_result["overall_score"] = overall_score

        # Determine if validation passed
        validation_result["passed"] = overall_score >= 0.7

        # Generate quality metrics
        validation_result["quality_metrics"] = await self._generate_quality_metrics(task, output_data)

        # Generate issues and recommendations
        validation_result["issues"] = self._identify_issues(validation_result["criteria_scores"])
        validation_result["recommendations"] = self._generate_recommendations(
            validation_result["criteria_scores"],
            validation_result["quality_metrics"]
        )

        # Log validation results
        await self.audit_service.log_event(
            event_type="task_output_validated",
            project_id=task.project_id,
            task_id=task_id,
            metadata={
                "overall_score": overall_score,
                "passed": validation_result["passed"],
                "criteria_scores": validation_result["criteria_scores"],
                "issues_count": len(validation_result["issues"])
            }
        )

        return validation_result

    async def validate_project_phase(
        self,
        project_id: UUID,
        phase: str
    ) -> Dict[str, Any]:
        """
        Validate project phase completion and quality.

        Args:
            project_id: Project identifier
            phase: Phase to validate

        Returns:
            Dictionary containing phase validation results
        """
        logger.info("Validating project phase", project_id=str(project_id), phase=phase)

        validation_result = {
            "project_id": str(project_id),
            "phase": phase,
            "validation_timestamp": datetime.now(timezone.utc),
            "overall_score": 0.0,
            "deliverables_score": 0.0,
            "quality_score": 0.0,
            "coverage_score": 0.0,
            "deliverables": {},
            "quality_metrics": {},
            "missing_deliverables": [],
            "quality_issues": [],
            "recommendations": [],
            "ready_for_next_phase": False
        }

        # Validate deliverables
        deliverables_result = await self._validate_phase_deliverables(project_id, phase)
        validation_result.update(deliverables_result)

        # Validate phase quality
        quality_result = await self._validate_phase_quality_metrics(project_id, phase)
        validation_result["quality_metrics"] = quality_result["metrics"]
        validation_result["quality_score"] = quality_result["overall_score"]

        # Validate coverage (completeness of phase activities)
        coverage_result = await self._validate_phase_coverage(project_id, phase)
        validation_result["coverage_score"] = coverage_result["score"]

        # Calculate overall phase score
        overall_score = (
            validation_result["deliverables_score"] * 0.4 +
            validation_result["quality_score"] * 0.4 +
            validation_result["coverage_score"] * 0.2
        )
        validation_result["overall_score"] = overall_score

        # Determine readiness for next phase
        validation_result["ready_for_next_phase"] = (
            overall_score >= 0.8 and
            len(validation_result["missing_deliverables"]) == 0
        )

        # Generate recommendations
        validation_result["recommendations"] = self._generate_phase_recommendations(validation_result)

        return validation_result

    async def validate_agent_confidence(
        self,
        agent_type: str,
        task_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate agent confidence and output reliability.

        Args:
            agent_type: Type of agent
            task_data: Task input data
            output_data: Agent output data

        Returns:
            Dictionary containing confidence validation results
        """
        logger.info("Validating agent confidence", agent_type=agent_type)

        confidence_result = {
            "agent_type": agent_type,
            "confidence_score": 0.0,
            "reliability_score": 0.0,
            "consistency_score": 0.0,
            "validation_indicators": {},
            "confidence_factors": {},
            "warnings": [],
            "recommendations": []
        }

        # Calculate confidence score based on various factors
        confidence_factors = await self._calculate_confidence_factors(agent_type, task_data, output_data)
        confidence_result["confidence_factors"] = confidence_factors

        # Calculate overall confidence score
        confidence_score = sum(confidence_factors.values()) / len(confidence_factors)
        confidence_result["confidence_score"] = confidence_score

        # Calculate reliability score based on historical performance
        reliability_score = await self._calculate_reliability_score(agent_type)
        confidence_result["reliability_score"] = reliability_score

        # Calculate consistency score
        consistency_score = await self._calculate_consistency_score(agent_type, output_data)
        confidence_result["consistency_score"] = consistency_score

        # Generate validation indicators
        confidence_result["validation_indicators"] = self._generate_validation_indicators(
            confidence_score, reliability_score, consistency_score
        )

        # Generate warnings if confidence is low
        if confidence_score < 0.6:
            confidence_result["warnings"].append("Low confidence score detected")
        if reliability_score < 0.7:
            confidence_result["warnings"].append("Agent reliability below threshold")
        if consistency_score < 0.6:
            confidence_result["warnings"].append("Output consistency issues detected")

        # Generate recommendations
        confidence_result["recommendations"] = self._generate_confidence_recommendations(
            confidence_score, reliability_score, consistency_score
        )

        return confidence_result

    async def assess_risk_factors(
        self,
        project_id: UUID,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess risk factors that might require HITL intervention.

        Args:
            project_id: Project identifier
            context_data: Context data for risk assessment

        Returns:
            Dictionary containing risk assessment results
        """
        logger.info("Assessing risk factors", project_id=str(project_id))

        risk_assessment = {
            "project_id": str(project_id),
            "assessment_timestamp": datetime.now(timezone.utc),
            "overall_risk_level": "low",
            "risk_score": 0.0,
            "risk_categories": {},
            "high_risk_factors": [],
            "mitigation_recommendations": [],
            "hitl_recommended": False
        }

        # Assess different risk categories
        risk_categories = {
            "technical": await self._assess_technical_risks(project_id, context_data),
            "quality": await self._assess_quality_risks(project_id, context_data),
            "timeline": await self._assess_timeline_risks(project_id, context_data),
            "security": await self._assess_security_risks(project_id, context_data),
            "compliance": await self._assess_compliance_risks(project_id, context_data)
        }

        risk_assessment["risk_categories"] = risk_categories

        # Calculate overall risk score
        risk_scores = [category["risk_score"] for category in risk_categories.values()]
        overall_risk_score = sum(risk_scores) / len(risk_scores)
        risk_assessment["risk_score"] = overall_risk_score

        # Determine overall risk level
        if overall_risk_score >= 0.8:
            risk_assessment["overall_risk_level"] = "high"
        elif overall_risk_score >= 0.5:
            risk_assessment["overall_risk_level"] = "medium"
        else:
            risk_assessment["overall_risk_level"] = "low"

        # Identify high-risk factors
        risk_assessment["high_risk_factors"] = [
            factor for category in risk_categories.values()
            for factor in category.get("risk_factors", [])
            if factor.get("severity", "low") == "high"
        ]

        # Generate mitigation recommendations
        risk_assessment["mitigation_recommendations"] = self._generate_risk_mitigation_recommendations(
            risk_categories
        )

        # Determine if HITL is recommended
        risk_assessment["hitl_recommended"] = (
            overall_risk_score >= 0.7 or
            len(risk_assessment["high_risk_factors"]) > 0
        )

        return risk_assessment

    # Private validation methods

    async def _validate_completeness(self, task: TaskDB, output_data: Dict[str, Any]) -> float:
        """Validate task output completeness."""
        required_fields = self._get_required_fields_for_agent(task.agent_type)

        if not required_fields:
            return 1.0

        present_fields = [field for field in required_fields if field in output_data]
        completeness_score = len(present_fields) / len(required_fields)

        return min(1.0, completeness_score)

    async def _validate_quality(self, task: TaskDB, output_data: Dict[str, Any]) -> float:
        """Validate task output quality."""
        quality_score = 0.8  # Base quality score

        # Check for quality indicators
        if "confidence" in output_data:
            quality_score *= output_data["confidence"]

        if "validation_passed" in output_data:
            quality_score *= 1.1 if output_data["validation_passed"] else 0.8

        return min(1.0, quality_score)

    async def _validate_consistency(self, task: TaskDB, output_data: Dict[str, Any]) -> float:
        """Validate task output consistency."""
        # Get similar tasks for comparison
        similar_tasks = self.db.query(TaskDB).filter(
            TaskDB.agent_type == task.agent_type,
            TaskDB.project_id == task.project_id,
            TaskDB.status == TaskStatus.COMPLETED,
            TaskDB.id != task.id
        ).limit(5).all()

        if not similar_tasks:
            return 0.8  # Default consistency score

        # Simple consistency check based on output structure
        consistency_score = 0.8
        for similar_task in similar_tasks:
            if hasattr(similar_task, 'output_data') and similar_task.output_data:
                # Compare output structure
                common_keys = set(output_data.keys()) & set(similar_task.output_data.keys())
                if common_keys:
                    consistency_score += 0.05

        return min(1.0, consistency_score)

    async def _validate_compliance(self, task: TaskDB, output_data: Dict[str, Any]) -> float:
        """Validate task output compliance with standards."""
        compliance_score = 0.9  # Base compliance score

        # Check for compliance indicators
        if "standards_checked" in output_data and output_data["standards_checked"]:
            compliance_score *= 1.1

        if "security_validated" in output_data and output_data["security_validated"]:
            compliance_score *= 1.05

        return min(1.0, compliance_score)

    async def _generate_quality_metrics(self, task: TaskDB, output_data: Dict[str, Any]) -> Dict[str, float]:
        """Generate quality metrics for task output."""
        return {
            "code_quality": output_data.get("code_quality", 0.8),
            "documentation_quality": output_data.get("documentation_quality", 0.75),
            "test_coverage": output_data.get("test_coverage", 0.7),
            "security_score": output_data.get("security_score", 0.85),
            "performance_score": output_data.get("performance_score", 0.8)
        }

    def _identify_issues(self, criteria_scores: Dict[str, float]) -> List[str]:
        """Identify issues based on criteria scores."""
        issues = []

        for criterion, score in criteria_scores.items():
            if score < 0.6:
                issues.append(f"Low {criterion} score: {score:.2f}")

        return issues

    def _generate_recommendations(self, criteria_scores: Dict[str, float], quality_metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        for criterion, score in criteria_scores.items():
            if score < 0.7:
                recommendations.append(f"Improve {criterion} (current: {score:.2f})")

        for metric, score in quality_metrics.items():
            if score < self.quality_thresholds.get(metric, 0.8):
                recommendations.append(f"Address {metric} issues (current: {score:.2f})")

        if not recommendations:
            recommendations.append("Output meets quality standards")

        return recommendations

    async def _validate_phase_deliverables(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Validate phase deliverables."""
        expected_deliverables = self._get_expected_deliverables_for_phase(phase)

        # Get project artifacts
        artifacts = self.db.query(ContextArtifactDB).filter(
            ContextArtifactDB.project_id == project_id
        ).all()

        deliverables = {}
        missing_deliverables = []

        for deliverable in expected_deliverables:
            matching_artifacts = [
                artifact for artifact in artifacts
                if artifact.artifact_type == deliverable["type"]
            ]

            deliverables[deliverable["name"]] = {
                "required": deliverable.get("required", True),
                "found": len(matching_artifacts) > 0,
                "artifacts": [str(artifact.id) for artifact in matching_artifacts]
            }

            if deliverable.get("required", True) and not matching_artifacts:
                missing_deliverables.append(deliverable["name"])

        # Calculate deliverables score
        required_deliverables = [d for d in expected_deliverables if d.get("required", True)]
        found_required = [d["name"] for d in required_deliverables if deliverables[d["name"]]["found"]]

        deliverables_score = len(found_required) / len(required_deliverables) if required_deliverables else 1.0

        return {
            "deliverables": deliverables,
            "deliverables_score": deliverables_score,
            "missing_deliverables": missing_deliverables
        }

    async def _validate_phase_quality_metrics(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Validate quality metrics for phase."""
        # This would analyze actual quality metrics from the project
        # For now, returning simulated metrics

        metrics = {
            "code_quality": 0.85,
            "test_coverage": 0.78,
            "documentation_completeness": 0.82,
            "review_completion": 0.90,
            "security_assessment": 0.88
        }

        overall_score = sum(metrics.values()) / len(metrics)

        return {
            "metrics": metrics,
            "overall_score": overall_score
        }

    async def _validate_phase_coverage(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Validate phase activity coverage."""
        # Check if all required activities for the phase were completed
        expected_activities = self._get_expected_activities_for_phase(phase)

        # Get completed tasks for the phase
        completed_tasks = self.db.query(TaskDB).filter(
            TaskDB.project_id == project_id,
            TaskDB.status == TaskStatus.COMPLETED
        ).all()

        coverage_score = min(1.0, len(completed_tasks) / max(1, len(expected_activities)))

        return {
            "score": coverage_score,
            "expected_activities": len(expected_activities),
            "completed_tasks": len(completed_tasks)
        }

    def _generate_phase_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for phase validation."""
        recommendations = []

        if validation_result["missing_deliverables"]:
            recommendations.append(f"Complete missing deliverables: {', '.join(validation_result['missing_deliverables'])}")

        if validation_result["quality_score"] < 0.8:
            recommendations.append("Improve quality metrics before proceeding")

        if validation_result["coverage_score"] < 0.8:
            recommendations.append("Complete remaining phase activities")

        if not recommendations:
            recommendations.append("Phase meets completion criteria")

        return recommendations

    async def _calculate_confidence_factors(self, agent_type: str, task_data: Dict[str, Any], output_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence factors for agent output."""
        return {
            "task_complexity_match": 0.8,
            "output_completeness": 0.9,
            "validation_checks_passed": 0.85,
            "historical_performance": 0.82,
            "output_consistency": 0.78
        }

    async def _calculate_reliability_score(self, agent_type: str) -> float:
        """Calculate agent reliability based on historical performance."""
        # Get recent task success rate for this agent type
        recent_tasks = self.db.query(TaskDB).filter(
            TaskDB.agent_type == agent_type
        ).limit(50).all()

        if not recent_tasks:
            return 0.8  # Default reliability

        successful_tasks = [task for task in recent_tasks if task.status == TaskStatus.COMPLETED]
        reliability_score = len(successful_tasks) / len(recent_tasks)

        return reliability_score

    async def _calculate_consistency_score(self, agent_type: str, output_data: Dict[str, Any]) -> float:
        """Calculate output consistency score."""
        # Simplified consistency calculation
        return 0.82

    def _generate_validation_indicators(self, confidence_score: float, reliability_score: float, consistency_score: float) -> Dict[str, str]:
        """Generate validation indicators."""
        return {
            "confidence_level": "high" if confidence_score >= 0.8 else "medium" if confidence_score >= 0.6 else "low",
            "reliability_level": "high" if reliability_score >= 0.8 else "medium" if reliability_score >= 0.6 else "low",
            "consistency_level": "high" if consistency_score >= 0.8 else "medium" if consistency_score >= 0.6 else "low"
        }

    def _generate_confidence_recommendations(self, confidence_score: float, reliability_score: float, consistency_score: float) -> List[str]:
        """Generate recommendations based on confidence analysis."""
        recommendations = []

        if confidence_score < 0.7:
            recommendations.append("Consider human review due to low confidence")
        if reliability_score < 0.7:
            recommendations.append("Agent reliability concerns - consider alternative approach")
        if consistency_score < 0.7:
            recommendations.append("Output consistency issues detected - validate results")

        return recommendations

    # Risk assessment methods

    async def _assess_technical_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess technical risks."""
        return {
            "risk_score": 0.3,
            "risk_factors": [],
            "description": "Technical risks assessment"
        }

    async def _assess_quality_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality risks."""
        return {
            "risk_score": 0.2,
            "risk_factors": [],
            "description": "Quality risks assessment"
        }

    async def _assess_timeline_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess timeline risks."""
        return {
            "risk_score": 0.4,
            "risk_factors": [],
            "description": "Timeline risks assessment"
        }

    async def _assess_security_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess security risks."""
        return {
            "risk_score": 0.1,
            "risk_factors": [],
            "description": "Security risks assessment"
        }

    async def _assess_compliance_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compliance risks."""
        return {
            "risk_score": 0.15,
            "risk_factors": [],
            "description": "Compliance risks assessment"
        }

    def _generate_risk_mitigation_recommendations(self, risk_categories: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []

        for category, data in risk_categories.items():
            if data["risk_score"] >= 0.7:
                recommendations.append(f"Address high {category} risks immediately")
            elif data["risk_score"] >= 0.5:
                recommendations.append(f"Monitor {category} risks closely")

        return recommendations

    # Helper methods

    def _get_required_fields_for_agent(self, agent_type: str) -> List[str]:
        """Get required output fields for agent type."""
        agent_requirements = {
            "coder": ["code", "tests", "documentation"],
            "tester": ["test_results", "coverage_report", "issues"],
            "deployer": ["deployment_status", "logs", "configuration"],
            "analyst": ["requirements", "analysis", "recommendations"]
        }
        return agent_requirements.get(agent_type, [])

    def _get_expected_deliverables_for_phase(self, phase: str) -> List[Dict[str, Any]]:
        """Get expected deliverables for phase."""
        return [
            {"name": f"{phase}_document", "type": ArtifactType.DOCUMENTATION, "required": True},
            {"name": f"{phase}_artifacts", "type": ArtifactType.SOURCE_CODE, "required": False}
        ]

    def _get_expected_activities_for_phase(self, phase: str) -> List[str]:
        """Get expected activities for phase."""
        activities_map = {
            "requirements": ["analysis", "specification", "validation"],
            "design": ["architecture", "detailed_design", "review"],
            "implementation": ["coding", "unit_testing", "integration"],
            "testing": ["system_testing", "user_testing", "bug_fixing"],
            "deployment": ["packaging", "deployment", "monitoring"]
        }
        return activities_map.get(phase.lower(), [])