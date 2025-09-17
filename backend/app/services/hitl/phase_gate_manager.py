"""
HITL Phase Gate Manager - Handles phase gate validation and management.

Responsible for managing phase gate approvals and validating phase completion requirements.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import structlog

from app.models.hitl import HitlStatus, HitlAction, HitlRequest
from app.database.models import HitlRequestDB, ProjectDB, TaskDB, ContextArtifactDB
from app.models.context import ArtifactType
from app.services.audit_service import AuditService
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class PhaseGateManager:
    """
    Manages phase gate validations and approvals for project phases.

    Follows Single Responsibility Principle by focusing solely on phase gate management.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    async def create_phase_gate_hitl(
        self,
        project_id: UUID,
        phase: str,
        gate_type: str = "approval",
        deliverables: Optional[List[Dict[str, Any]]] = None
    ) -> HitlRequestDB:
        """
        Create a phase gate HITL request for project phase completion approval.

        Args:
            project_id: Project identifier
            phase: Phase being completed
            gate_type: Type of gate (approval, review, milestone)
            deliverables: Optional list of deliverables to validate

        Returns:
            Created HITL request
        """
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
        """
        Validate phase gate requirements for project phase.

        Args:
            project_id: Project identifier
            phase: Phase to validate

        Returns:
            Dictionary containing validation results
        """
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
        """
        Process phase gate response and handle phase transitions.

        Args:
            request_id: HITL request identifier
            action: User action (APPROVE, REJECT, AMEND)
            user_id: User who provided the response
            amendments: Optional amendments for phase requirements

        Returns:
            Dictionary containing processing results
        """
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
        """
        Get phase gate status for all phases in a project.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary containing phase gate status information
        """
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
        """
        Auto-create phase gates for standard SDLC phases.

        Args:
            project_id: Project identifier

        Returns:
            List of created HITL request IDs
        """
        standard_phases = [
            {"name": "requirements", "deliverables": ["requirements_doc", "acceptance_criteria"]},
            {"name": "design", "deliverables": ["system_design", "api_specification"]},
            {"name": "implementation", "deliverables": ["source_code", "unit_tests"]},
            {"name": "testing", "deliverables": ["test_results", "bug_reports"]},
            {"name": "deployment", "deliverables": ["deployment_package", "deployment_guide"]}
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

    # Private helper methods

    def _generate_phase_gate_question(
        self,
        phase: str,
        gate_type: str,
        deliverables: List[Dict[str, Any]]
    ) -> str:
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
            return [
                "Approve",
                "Reject",
                "Amend"
            ]

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