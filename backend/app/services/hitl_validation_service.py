"""
HITL Validation Service - Consolidated validation and phase gate management.

Handles quality validation, risk assessment, and phase gate management.
Consolidates functionality from validation_engine.py and phase_gate_manager.py.
"""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.models.hitl import HitlStatus, HitlAction, HitlRequest
from app.models.context import ArtifactType
from app.models.task import TaskStatus
from app.database.models import (
    HitlRequestDB, ProjectDB, TaskDB, ContextArtifactDB
)
from app.services.audit_service import AuditService
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class HitlValidationService:
    """
    Consolidated HITL validation service handling quality assessment and phase gates.
    
    Combines validation engine and phase gate management into a single,
    focused service following SOLID principles.
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

    # ========== TASK OUTPUT VALIDATION ==========

    async def validate_task_output(
        self,
        task_id: UUID,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate task output quality and completeness."""
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

    async def validate_agent_confidence(
        self,
        agent_type: str,
        task_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate agent confidence and output reliability."""
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
        """Assess risk factors that might require HITL intervention."""
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

    # ========== PHASE GATE MANAGEMENT ==========

    async def create_phase_gate_hitl(
        self,
        project_id: UUID,
        phase: str,
        gate_type: str = "approval",
        deliverables: Optional[List[Dict[str, Any]]] = None
    ) -> HitlRequestDB:
        """Create a phase gate HITL request for project phase completion approval."""
        logger.info(
            "Creating phase gate HITL request",
            project_id=str(project_id),
            phase=phase,
            gate_type=gate_type
        )

        # Validate phase gate requirements
        validation_result = await self.validate_phase_gate_requirements(project_id, phase)

        # Generate appropriate question and options
        question = self._generate_phase_gate_question(phase, gate_type, deliverables or [])
        options = self._get_phase_gate_options(gate_type)

        # Create HITL request
        hitl_request = HitlRequestDB(
            id=uuid4(),
            project_id=project_id,
            task_id=None,  # Phase gates are project-level
            agent_type="orchestrator",
            question=question,
            options=options,
            context_data={
                "phase": phase,
                "gate_type": gate_type,
                "deliverables": deliverables or [],
                "validation_result": validation_result,
                "auto_generated": True
            },
            status=HitlStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),  # 48h for phase gates
            metadata={
                "hitl_type": "phase_gate",
                "phase": phase,
                "gate_type": gate_type
            }
        )

        self.db.add(hitl_request)
        self.db.commit()

        # Log audit event
        await self.audit_service.log_event(
            event_type="phase_gate_hitl_created",
            project_id=project_id,
            metadata={
                "hitl_request_id": str(hitl_request.id),
                "phase": phase,
                "gate_type": gate_type,
                "validation_result": validation_result
            }
        )

        # Emit WebSocket event
        await self._emit_phase_gate_hitl_event(hitl_request)

        return hitl_request

    async def validate_phase_gate_requirements(
        self,
        project_id: UUID,
        phase: str
    ) -> Dict[str, Any]:
        """Validate phase gate requirements for project phase."""
        logger.info(
            "Validating phase gate requirements",
            project_id=str(project_id),
            phase=phase
        )

        validation_result = {
            "phase": phase,
            "overall_status": "pending",
            "deliverables": {},
            "quality_metrics": {},
            "risks": {},
            "recommendations": []
        }

        # Validate deliverables
        deliverables_result = await self._validate_phase_deliverables(project_id, phase)
        validation_result["deliverables"] = deliverables_result

        # Validate quality metrics
        quality_result = await self._validate_phase_quality(project_id, phase)
        validation_result["quality_metrics"] = quality_result

        # Validate risks
        risks_result = await self._validate_phase_risks(project_id, phase)
        validation_result["risks"] = risks_result

        # Determine overall status
        validation_result["overall_status"] = self._determine_overall_validation_status(
            deliverables_result, quality_result, risks_result
        )

        # Generate recommendations
        validation_result["recommendations"] = self._generate_phase_recommendations(
            phase, deliverables_result, quality_result, risks_result
        )

        return validation_result

    async def process_phase_gate_response(
        self,
        request_id: UUID,
        action: HitlAction,
        user_id: str,
        amendments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process phase gate response and handle phase transitions."""
        logger.info(
            "Processing phase gate response",
            request_id=str(request_id),
            action=action.value,
            user_id=user_id
        )

        # Get the HITL request
        hitl_request = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.id == request_id
        ).first()

        if not hitl_request:
            raise ValueError(f"HITL request {request_id} not found")

        if hitl_request.metadata.get("hitl_type") != "phase_gate":
            raise ValueError(f"Request {request_id} is not a phase gate request")

        phase = hitl_request.context_data.get("phase")
        gate_type = hitl_request.context_data.get("gate_type")

        # Update request status
        hitl_request.status = HitlStatus.APPROVED if action == HitlAction.APPROVE else HitlStatus.REJECTED
        hitl_request.user_response = action.value
        hitl_request.user_id = user_id
        hitl_request.responded_at = datetime.now(timezone.utc)

        if amendments:
            hitl_request.amendments = amendments

        self.db.commit()

        # Process phase transition if approved
        transition_result = None
        if action == HitlAction.APPROVE:
            transition_result = await self._process_phase_gate_transition(
                hitl_request.project_id, phase, gate_type
            )

        # Store amendments if provided
        if amendments and action == HitlAction.AMEND:
            await self._store_phase_gate_amendments(
                hitl_request.project_id, phase, amendments
            )

        # Log audit event
        await self.audit_service.log_event(
            event_type="phase_gate_response_processed",
            project_id=hitl_request.project_id,
            metadata={
                "hitl_request_id": str(request_id),
                "phase": phase,
                "gate_type": gate_type,
                "action": action.value,
                "user_id": user_id,
                "has_amendments": amendments is not None,
                "transition_result": transition_result
            }
        )

        return {
            "status": "success",
            "action": action.value,
            "phase": phase,
            "gate_type": gate_type,
            "transition_result": transition_result,
            "message": f"Phase gate {action.value.lower()} for {phase} phase"
        }

    async def get_phase_gate_status(self, project_id: UUID) -> Dict[str, Any]:
        """Get phase gate status for all phases in a project."""
        # Get all phase gate HITL requests for the project
        phase_gate_requests = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.project_id == project_id,
            HitlRequestDB.metadata.contains({"hitl_type": "phase_gate"})
        ).all()

        # Organize by phase
        phases = {}
        for request in phase_gate_requests:
            phase = request.context_data.get("phase", "unknown")
            gate_type = request.context_data.get("gate_type", "approval")

            if phase not in phases:
                phases[phase] = {
                    "phase": phase,
                    "gates": {},
                    "overall_status": "pending"
                }

            phases[phase]["gates"][gate_type] = {
                "request_id": str(request.id),
                "status": request.status.value,
                "created_at": request.created_at,
                "responded_at": request.responded_at,
                "user_id": request.user_id
            }

        # Determine overall phase status
        for phase_data in phases.values():
            approval_gate = phase_data["gates"].get("approval")
            if approval_gate and approval_gate["status"] == "approved":
                phase_data["overall_status"] = "completed"
            elif any(gate["status"] == "rejected" for gate in phase_data["gates"].values()):
                phase_data["overall_status"] = "rejected"
            elif any(gate["status"] == "pending" for gate in phase_data["gates"].values()):
                phase_data["overall_status"] = "pending"

        return {
            "project_id": str(project_id),
            "phases": phases,
            "total_phases": len(phases),
            "completed_phases": len([p for p in phases.values() if p["overall_status"] == "completed"]),
            "pending_phases": len([p for p in phases.values() if p["overall_status"] == "pending"])
        }

    async def auto_create_phase_gates(self, project_id: UUID) -> List[UUID]:
        """Auto-create phase gates for standard SDLC phases."""
        standard_phases = [
            {"name": "requirements", "deliverables": ["plan", "requirements_doc", "acceptance_criteria"]},
            {"name": "design", "deliverables": ["plan", "system_design", "api_specification"]},
            {"name": "implementation", "deliverables": ["plan", "source_code", "unit_tests"]},
            {"name": "testing", "deliverables": ["plan", "test_results", "bug_reports"]},
            {"name": "deployment", "deliverables": ["plan", "deployment_package", "deployment_guide"]}
        ]

        created_requests = []

        for phase_config in standard_phases:
            try:
                hitl_request = await self.create_phase_gate_hitl(
                    project_id,
                    phase_config["name"],
                    "approval",
                    phase_config["deliverables"]
                )
                created_requests.append(hitl_request.id)
            except Exception as e:
                logger.error(
                    "Failed to create auto phase gate",
                    project_id=str(project_id),
                    phase=phase_config["name"],
                    error=str(e)
                )

        logger.info(
            "Auto-created phase gates",
            project_id=str(project_id),
            created_count=len(created_requests)
        )

        return created_requests

    # ========== PRIVATE VALIDATION METHODS ==========

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

    # ========== PRIVATE HELPER METHODS ==========

    def _get_required_fields_for_agent(self, agent_type: str) -> List[str]:
        """Get required output fields for agent type."""
        agent_requirements = {
            "coder": ["code", "tests", "documentation"],
            "tester": ["test_results", "coverage_report", "issues"],
            "deployer": ["deployment_status", "logs", "configuration"],
            "analyst": ["requirements", "analysis", "recommendations"]
        }
        return agent_requirements.get(agent_type, [])

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

    # Risk assessment methods (simplified implementations)
    async def _assess_technical_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess technical risks."""
        return {"risk_score": 0.3, "risk_factors": [], "description": "Technical risks assessment"}

    async def _assess_quality_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality risks."""
        return {"risk_score": 0.2, "risk_factors": [], "description": "Quality risks assessment"}

    async def _assess_timeline_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess timeline risks."""
        return {"risk_score": 0.4, "risk_factors": [], "description": "Timeline risks assessment"}

    async def _assess_security_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess security risks."""
        return {"risk_score": 0.1, "risk_factors": [], "description": "Security risks assessment"}

    async def _assess_compliance_risks(self, project_id: UUID, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compliance risks."""
        return {"risk_score": 0.15, "risk_factors": [], "description": "Compliance risks assessment"}

    def _generate_risk_mitigation_recommendations(self, risk_categories: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []

        for category, data in risk_categories.items():
            if data["risk_score"] >= 0.7:
                recommendations.append(f"Address high {category} risks immediately")
            elif data["risk_score"] >= 0.5:
                recommendations.append(f"Monitor {category} risks closely")

        return recommendations

    # Phase gate helper methods
    def _generate_phase_gate_question(self, phase: str, gate_type: str, deliverables: List[Dict[str, Any]]) -> str:
        """Generate appropriate question for phase gate approval."""
        if gate_type == "approval":
            base_question = f"Please review and approve the completion of the {phase} phase."
        elif gate_type == "review":
            base_question = f"Please review the deliverables for the {phase} phase."
        elif gate_type == "milestone":
            base_question = f"Please confirm the {phase} milestone has been reached."
        else:
            base_question = f"Please evaluate the {phase} phase."

        if deliverables:
            deliverable_summary = self._summarize_deliverables(deliverables)
            base_question += f"\n\nDeliverables to review:\n{deliverable_summary}"

        base_question += "\n\nPlease review the validation results and decide whether to proceed to the next phase."

        return base_question

    def _summarize_deliverables(self, deliverables: List[Dict[str, Any]]) -> str:
        """Create a summary of deliverables for the question."""
        if not deliverables:
            return "No specific deliverables defined."

        summary_lines = []
        for deliverable in deliverables:
            if isinstance(deliverable, str):
                summary_lines.append(f"• {deliverable}")
            elif isinstance(deliverable, dict):
                name = deliverable.get("name", "Unknown")
                description = deliverable.get("description", "")
                line = f"• {name}"
                if description:
                    line += f": {description}"
                summary_lines.append(line)

        return "\n".join(summary_lines)

    def _get_phase_gate_options(self, gate_type: str) -> List[str]:
        """Get appropriate options for phase gate type."""
        if gate_type == "approval":
            return [
                "Approve - All requirements met, proceed to next phase",
                "Reject - Requirements not met, return to current phase",
                "Amend - Approve with specific amendments or conditions"
            ]
        elif gate_type == "review":
            return [
                "Accept - Deliverables meet quality standards",
                "Reject - Deliverables need rework",
                "Amend - Accept with recommended improvements"
            ]
        elif gate_type == "milestone":
            return [
                "Confirm - Milestone achieved successfully",
                "Reject - Milestone not achieved",
                "Amend - Milestone achieved with noted issues"
            ]
        else:
            return ["Approve", "Reject", "Amend"]

    async def _emit_phase_gate_hitl_event(self, hitl_request: HitlRequestDB) -> None:
        """Emit WebSocket event for phase gate HITL creation."""
        try:
            event = WebSocketEvent(
                type=EventType.HITL_REQUEST_CREATED,
                project_id=hitl_request.project_id,
                data={
                    "hitl_request_id": str(hitl_request.id),
                    "phase": hitl_request.context_data.get("phase"),
                    "gate_type": hitl_request.context_data.get("gate_type"),
                    "question": hitl_request.question,
                    "options": hitl_request.options,
                    "expires_at": hitl_request.expires_at.isoformat() if hitl_request.expires_at else None
                }
            )

            await websocket_manager.broadcast_to_project(
                hitl_request.project_id,
                event.model_dump()
            )

        except Exception as e:
            logger.error(
                "Failed to emit phase gate HITL event",
                hitl_request_id=str(hitl_request.id),
                error=str(e)
            )

    async def _validate_phase_deliverables(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Validate phase deliverables completion."""
        expected_deliverables = self._get_expected_deliverables_for_phase(phase)

        # Get actual artifacts for the project
        artifacts = self.db.query(ContextArtifactDB).filter(
            ContextArtifactDB.project_id == project_id
        ).all()

        deliverable_status = {}

        for expected in expected_deliverables:
            found_artifacts = [
                artifact for artifact in artifacts
                if self._matches_deliverable(artifact, expected)
            ]

            deliverable_status[expected["name"]] = {
                "expected": expected,
                "found": len(found_artifacts),
                "artifacts": [str(artifact.id) for artifact in found_artifacts],
                "status": "complete" if found_artifacts else "missing"
            }

        completion_rate = len([d for d in deliverable_status.values() if d["status"] == "complete"]) / len(expected_deliverables) if expected_deliverables else 1.0

        return {
            "phase": phase,
            "deliverables": deliverable_status,
            "completion_rate": completion_rate,
            "status": "complete" if completion_rate >= 0.8 else "incomplete"
        }

    def _get_expected_deliverables_for_phase(self, phase: str) -> List[Dict[str, Any]]:
        """Get expected deliverables for a specific phase."""
        deliverables_map = {
            "requirements": [
                {"name": "requirements_document", "type": ArtifactType.REQUIREMENTS, "required": True},
                {"name": "acceptance_criteria", "type": ArtifactType.REQUIREMENTS, "required": True}
            ],
            "design": [
                {"name": "system_design", "type": ArtifactType.SYSTEM_ARCHITECTURE, "required": True},
                {"name": "api_specification", "type": ArtifactType.API_SPECIFICATION, "required": True}
            ],
            "implementation": [
                {"name": "source_code", "type": ArtifactType.SOURCE_CODE, "required": True},
                {"name": "unit_tests", "type": ArtifactType.TEST_RESULTS, "required": True}
            ],
            "testing": [
                {"name": "test_results", "type": ArtifactType.TEST_RESULTS, "required": True},
                {"name": "bug_reports", "type": ArtifactType.BUG_REPORT, "required": False}
            ],
            "deployment": [
                {"name": "deployment_package", "type": ArtifactType.DEPLOYMENT_PACKAGE, "required": True},
                {"name": "deployment_guide", "type": ArtifactType.DOCUMENTATION, "required": True}
            ]
        }

        return deliverables_map.get(phase.lower(), [])

    def _matches_deliverable(self, artifact, expected: Dict[str, Any]) -> bool:
        """Check if artifact matches expected deliverable."""
        return artifact.artifact_type == expected["type"]

    async def _validate_phase_quality(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Validate quality metrics for phase."""
        # This is a simplified quality validation
        # In a real system, this would analyze code quality, test coverage, etc.

        quality_metrics = {
            "code_quality": 0.85,
            "test_coverage": 0.75,
            "documentation_completeness": 0.80,
            "review_completion": 0.90
        }

        overall_quality = sum(quality_metrics.values()) / len(quality_metrics)

        return {
            "phase": phase,
            "metrics": quality_metrics,
            "overall_quality": overall_quality,
            "status": "good" if overall_quality >= 0.8 else "needs_improvement"
        }

    async def _validate_phase_risks(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Validate risk factors for phase."""
        # This is a simplified risk assessment
        # In a real system, this would analyze various risk factors

        risks = {
            "technical_debt": "low",
            "security_vulnerabilities": "medium",
            "performance_issues": "low",
            "scalability_concerns": "medium"
        }

        high_risks = [k for k, v in risks.items() if v == "high"]
        risk_level = "high" if high_risks else "medium" if any(v == "medium" for v in risks.values()) else "low"

        return {
            "phase": phase,
            "risks": risks,
            "risk_level": risk_level,
            "high_priority_risks": high_risks
        }

    def _determine_overall_validation_status(self, deliverables_result, quality_result, risks_result) -> str:
        """Determine overall validation status from individual results."""
        if (deliverables_result["status"] == "complete" and
            quality_result["status"] == "good" and
            risks_result["risk_level"] == "low"):
            return "ready"
        elif deliverables_result["status"] == "incomplete":
            return "incomplete"
        elif quality_result["status"] == "needs_improvement":
            return "quality_issues"
        elif risks_result["risk_level"] == "high":
            return "high_risk"
        else:
            return "review_required"

    def _generate_phase_recommendations(self, phase, deliverables_result, quality_result, risks_result) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        if deliverables_result["status"] == "incomplete":
            missing = [name for name, data in deliverables_result["deliverables"].items() if data["status"] == "missing"]
            recommendations.append(f"Complete missing deliverables: {', '.join(missing)}")

        if quality_result["status"] == "needs_improvement":
            low_quality = [metric for metric, score in quality_result["metrics"].items() if score < 0.8]
            recommendations.append(f"Improve quality metrics: {', '.join(low_quality)}")

        if risks_result["risk_level"] == "high":
            recommendations.append(f"Address high-priority risks: {', '.join(risks_result['high_priority_risks'])}")

        if not recommendations:
            recommendations.append("All validation criteria met. Ready to proceed to next phase.")

        return recommendations

    async def _process_phase_gate_transition(self, project_id: UUID, phase: str, gate_type: str) -> Dict[str, Any]:
        """Process phase transition after gate approval."""
        # Update project status or phase tracking
        # This would integrate with project management system

        return {
            "phase_completed": phase,
            "gate_type": gate_type,
            "transition_time": datetime.now(timezone.utc),
            "next_phase": self._get_next_phase(phase)
        }

    def _get_next_phase(self, current_phase: str) -> str:
        """Get the next phase in the SDLC."""
        phase_order = ["requirements", "design", "implementation", "testing", "deployment"]
        try:
            current_index = phase_order.index(current_phase.lower())
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass
        return "completed"

    async def _store_phase_gate_amendments(self, project_id: UUID, phase: str, amendments: Dict[str, Any]) -> None:
        """Store phase gate amendments for future reference."""
        await self.audit_service.log_event(
            event_type="phase_gate_amendments_stored",
            project_id=project_id,
            metadata={
                "phase": phase,
                "amendments": amendments,
                "stored_at": datetime.now(timezone.utc).isoformat()
            }
        )