"""
SDLC Orchestrator - Handles SDLC-specific workflow logic.

Responsible for managing Software Development Life Cycle specific workflows,
phases, and orchestration patterns.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import structlog

from app.models.workflow_state import WorkflowExecutionStateModel, WorkflowExecutionState

logger = structlog.get_logger(__name__)


class SdlcOrchestrator:
    """
    Orchestrates SDLC-specific workflows and phases.

    Follows Single Responsibility Principle by focusing solely on SDLC logic.
    """

    def __init__(self, db: Session):
        self.db = db
        # Lazy import to avoid circular dependency
        self._execution_engine = None
        self._event_dispatcher = None
        self._state_manager = None

    @property
    def execution_engine(self):
        """Lazy-loaded execution engine to avoid circular imports."""
        if self._execution_engine is None:
            from .execution_engine import ExecutionEngine
            self._execution_engine = ExecutionEngine(self.db)
        return self._execution_engine

    @property
    def event_dispatcher(self):
        """Lazy-loaded event dispatcher to avoid circular imports."""
        if self._event_dispatcher is None:
            from .event_dispatcher import EventDispatcher
            self._event_dispatcher = EventDispatcher(self.db)
        return self._event_dispatcher

    @property
    def state_manager(self):
        """Lazy-loaded state manager to avoid circular imports."""
        if self._state_manager is None:
            from .state_manager import StateManager
            self._state_manager = StateManager(self.db)
        return self._state_manager

    async def execute_sdlc_workflow(
        self,
        project_id: UUID,
        requirements: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete SDLC workflow.

        Args:
            project_id: Project identifier
            requirements: Project requirements
            execution_id: Optional custom execution ID

        Returns:
            Dictionary containing SDLC execution results
        """
        if not execution_id:
            execution_id = str(uuid4())

        logger.info(
            "Starting SDLC workflow execution",
            project_id=str(project_id),
            execution_id=execution_id
        )

        try:
            # Create SDLC workflow definition
            sdlc_workflow_definition = self._create_sdlc_workflow_definition(requirements)

            # Initialize context with requirements
            initial_context = {
                "requirements": requirements,
                "project_type": requirements.get("project_type", "web_application"),
                "sdlc_phase": "requirements",
                "sdlc_execution_id": execution_id
            }

            # Create execution state
            execution = self.state_manager.create_execution_state(
                execution_id=execution_id,
                workflow_id="sdlc_workflow",
                project_id=project_id,
                workflow_definition=sdlc_workflow_definition,
                initial_context=initial_context
            )

            # Update state to running
            execution = self.state_manager.update_execution_state(
                execution_id,
                state=WorkflowExecutionState.RUNNING
            )

            # Execute SDLC phases
            result = await self._execute_sdlc_phases(execution)

            return {
                "execution_id": execution_id,
                "status": "started",
                "message": "SDLC workflow execution started successfully",
                "phases": self._get_sdlc_phases(),
                "result": result
            }

        except Exception as e:
            logger.error(
                "Failed to start SDLC workflow execution",
                project_id=str(project_id),
                execution_id=execution_id,
                error=str(e)
            )

            # Mark execution as failed
            self.state_manager.fail_execution(
                execution_id,
                f"Failed to start SDLC workflow: {str(e)}"
            )

            raise

    def get_sdlc_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get SDLC workflow status.

        Args:
            execution_id: Workflow execution identifier

        Returns:
            SDLC status dictionary or None if not found
        """
        execution = self.state_manager.get_execution_state(execution_id)
        if not execution:
            return None

        # Get current SDLC phase
        current_phase = execution.context_data.get("sdlc_phase", "unknown")

        # Calculate phase progress
        phases = self._get_sdlc_phases()
        phase_index = phases.index(current_phase) if current_phase in phases else 0
        phase_progress = (phase_index / len(phases)) * 100

        # Get phase-specific metrics
        phase_metrics = self._calculate_sdlc_metrics({
            "current_phase": current_phase,
            "step_results": execution.step_results,
            "context_data": execution.context_data
        })

        return {
            "execution_id": execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "state": execution.state.value,
            "current_phase": current_phase,
            "phase_progress": phase_progress,
            "total_phases": len(phases),
            "completed_steps": len(execution.step_results),
            "total_steps": len(execution.workflow_definition.get("steps", [])),
            "phase_metrics": phase_metrics,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
            "phases": phases
        }

    async def advance_sdlc_phase(
        self,
        execution_id: str,
        next_phase: str,
        phase_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Advance to next SDLC phase.

        Args:
            execution_id: Workflow execution identifier
            next_phase: Next phase to advance to
            phase_results: Results from current phase

        Returns:
            Dictionary containing phase advancement results
        """
        execution = self.state_manager.get_execution_state(execution_id)
        if not execution:
            raise ValueError(f"SDLC workflow execution not found: {execution_id}")

        current_phase = execution.context_data.get("sdlc_phase", "unknown")

        logger.info(
            "Advancing SDLC phase",
            execution_id=execution_id,
            current_phase=current_phase,
            next_phase=next_phase
        )

        # Validate phase transition
        if not self._validate_phase_transition(current_phase, next_phase):
            raise ValueError(f"Invalid phase transition from {current_phase} to {next_phase}")

        # Update context with phase results and new phase
        updated_context = {
            "sdlc_phase": next_phase,
            f"{current_phase}_results": phase_results,
            "phase_transition_timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Update execution state
        execution = self.state_manager.update_execution_state(
            execution_id,
            context_data=updated_context
        )

        # Calculate phase metrics
        metrics = self._calculate_sdlc_metrics(phase_results)

        # Emit phase event
        await self.event_dispatcher.emit_sdlc_phase_event(
            execution, next_phase, phase_results, metrics
        )

        return {
            "execution_id": execution_id,
            "previous_phase": current_phase,
            "current_phase": next_phase,
            "phase_results": phase_results,
            "metrics": metrics,
            "advanced_at": datetime.now(timezone.utc).isoformat()
        }

    async def validate_phase_completion(
        self,
        execution_id: str,
        phase: str,
        deliverables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate SDLC phase completion.

        Args:
            execution_id: Workflow execution identifier
            phase: Phase to validate
            deliverables: Phase deliverables

        Returns:
            Dictionary containing validation results
        """
        logger.info(
            "Validating SDLC phase completion",
            execution_id=execution_id,
            phase=phase
        )

        validation_result = {
            "execution_id": execution_id,
            "phase": phase,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "deliverables_valid": False,
            "quality_score": 0.0,
            "completion_score": 0.0,
            "overall_score": 0.0,
            "issues": [],
            "recommendations": [],
            "ready_for_next_phase": False
        }

        # Validate deliverables
        deliverable_validation = self._validate_phase_deliverables(phase, deliverables)
        validation_result.update(deliverable_validation)

        # Calculate quality score
        quality_score = self._calculate_phase_quality_score(phase, deliverables)
        validation_result["quality_score"] = quality_score

        # Calculate completion score
        completion_score = self._calculate_phase_completion_score(phase, deliverables)
        validation_result["completion_score"] = completion_score

        # Calculate overall score
        overall_score = (
            (0.4 * validation_result["deliverables_valid"]) +
            (0.3 * quality_score) +
            (0.3 * completion_score)
        )
        validation_result["overall_score"] = overall_score

        # Determine readiness for next phase
        validation_result["ready_for_next_phase"] = (
            validation_result["deliverables_valid"] and
            overall_score >= 0.7
        )

        # Generate recommendations
        validation_result["recommendations"] = self._generate_phase_recommendations(
            phase, validation_result
        )

        return validation_result

    # Private helper methods

    def _create_sdlc_workflow_definition(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create SDLC workflow definition based on requirements."""
        project_type = requirements.get("project_type", "web_application")
        complexity = requirements.get("complexity", "medium")

        # Base SDLC workflow definition
        workflow_definition = {
            "id": "sdlc_workflow",
            "name": "Software Development Life Cycle",
            "description": "Complete SDLC workflow from requirements to deployment",
            "type": "sdlc",
            "project_type": project_type,
            "complexity": complexity,
            "steps": self._get_sdlc_steps(project_type, complexity),
            "phases": self._get_sdlc_phases(),
            "metadata": {
                "created_for_project": True,
                "auto_generated": True,
                "requirements_based": True
            }
        }

        return workflow_definition

    def _get_sdlc_phases(self) -> List[str]:
        """Get standard SDLC phases."""
        return [
            "requirements",
            "design",
            "implementation",
            "testing",
            "deployment",
            "maintenance"
        ]

    def _get_sdlc_steps(self, project_type: str, complexity: str) -> List[Dict[str, Any]]:
        """Get SDLC steps based on project type and complexity."""
        base_steps = [
            {
                "name": "requirements_analysis",
                "phase": "requirements",
                "agent_type": "analyst",
                "description": "Analyze and document requirements",
                "expected_outputs": ["requirements_document", "acceptance_criteria"]
            },
            {
                "name": "system_design",
                "phase": "design",
                "agent_type": "architect",
                "description": "Design system architecture",
                "expected_outputs": ["system_design", "api_specification"]
            },
            {
                "name": "code_implementation",
                "phase": "implementation",
                "agent_type": "coder",
                "description": "Implement system code",
                "expected_outputs": ["source_code", "unit_tests"]
            },
            {
                "name": "system_testing",
                "phase": "testing",
                "agent_type": "tester",
                "description": "Test system functionality",
                "expected_outputs": ["test_results", "bug_reports"]
            },
            {
                "name": "deployment",
                "phase": "deployment",
                "agent_type": "deployer",
                "description": "Deploy system to production",
                "expected_outputs": ["deployment_package", "deployment_logs"]
            }
        ]

        # Add complexity-specific steps
        if complexity == "high":
            # Add additional steps for high complexity
            base_steps.insert(2, {
                "name": "detailed_design",
                "phase": "design",
                "agent_type": "architect",
                "description": "Create detailed component design",
                "expected_outputs": ["detailed_design", "component_specifications"]
            })

        return base_steps

    async def _execute_sdlc_phases(self, execution: WorkflowExecutionStateModel) -> Dict[str, Any]:
        """Execute SDLC phases sequentially."""
        phases = self._get_sdlc_phases()
        phase_results = {}

        for phase in phases:
            if execution.state != WorkflowExecutionState.RUNNING:
                break

            logger.info(
                "Executing SDLC phase",
                execution_id=execution.execution_id,
                phase=phase
            )

            # Execute phase steps
            phase_result = await self._execute_phase_steps(execution, phase)
            phase_results[phase] = phase_result

            # Advance to next phase
            if phase != phases[-1]:  # Not the last phase
                next_phase = phases[phases.index(phase) + 1]
                await self.advance_sdlc_phase(
                    execution.execution_id,
                    next_phase,
                    phase_result
                )

        return {
            "phases_executed": list(phase_results.keys()),
            "phase_results": phase_results,
            "overall_metrics": self._calculate_sdlc_metrics(phase_results)
        }

    async def _execute_phase_steps(
        self,
        execution: WorkflowExecutionStateModel,
        phase: str
    ) -> Dict[str, Any]:
        """Execute steps for a specific SDLC phase."""
        steps = execution.workflow_definition.get("steps", [])
        phase_steps = [step for step in steps if step.get("phase") == phase]

        phase_result = {
            "phase": phase,
            "steps_executed": 0,
            "steps_total": len(phase_steps),
            "step_results": [],
            "phase_success": True,
            "started_at": datetime.now(timezone.utc).isoformat()
        }

        for step in phase_steps:
            try:
                # This would integrate with the actual step execution
                # For now, simulating step execution
                step_result = {
                    "step_name": step["name"],
                    "agent_type": step["agent_type"],
                    "success": True,
                    "outputs": step.get("expected_outputs", []),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }

                phase_result["step_results"].append(step_result)
                phase_result["steps_executed"] += 1

            except Exception as e:
                logger.error(
                    "SDLC phase step failed",
                    execution_id=execution.execution_id,
                    phase=phase,
                    step=step["name"],
                    error=str(e)
                )
                phase_result["phase_success"] = False
                break

        phase_result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return phase_result

    def _validate_phase_transition(self, current_phase: str, next_phase: str) -> bool:
        """Validate if phase transition is allowed."""
        phases = self._get_sdlc_phases()

        if current_phase not in phases or next_phase not in phases:
            return False

        current_index = phases.index(current_phase)
        next_index = phases.index(next_phase)

        # Allow forward progression or staying in same phase
        return next_index >= current_index

    def _validate_phase_deliverables(self, phase: str, deliverables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate phase deliverables."""
        expected_deliverables = self._get_expected_deliverables(phase)

        missing_deliverables = []
        for expected in expected_deliverables:
            if expected not in deliverables:
                missing_deliverables.append(expected)

        return {
            "deliverables_valid": len(missing_deliverables) == 0,
            "missing_deliverables": missing_deliverables,
            "provided_deliverables": list(deliverables.keys())
        }

    def _get_expected_deliverables(self, phase: str) -> List[str]:
        """Get expected deliverables for phase."""
        deliverables_map = {
            "requirements": ["requirements_document", "acceptance_criteria", "user_stories"],
            "design": ["system_design", "api_specification", "database_design"],
            "implementation": ["source_code", "unit_tests", "documentation"],
            "testing": ["test_results", "test_coverage", "bug_reports"],
            "deployment": ["deployment_package", "deployment_guide", "configuration"],
            "maintenance": ["maintenance_plan", "documentation_updates"]
        }
        return deliverables_map.get(phase, [])

    def _calculate_phase_quality_score(self, phase: str, deliverables: Dict[str, Any]) -> float:
        """Calculate quality score for phase."""
        # Simplified quality scoring
        base_score = 0.8

        # Adjust based on deliverable completeness
        expected = self._get_expected_deliverables(phase)
        if expected:
            completeness = len(deliverables) / len(expected)
            base_score *= completeness

        return min(1.0, base_score)

    def _calculate_phase_completion_score(self, phase: str, deliverables: Dict[str, Any]) -> float:
        """Calculate completion score for phase."""
        # Simplified completion scoring
        expected = self._get_expected_deliverables(phase)
        if not expected:
            return 1.0

        provided = len(deliverables)
        return min(1.0, provided / len(expected))

    def _calculate_sdlc_metrics(self, phase_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate SDLC metrics from phase results."""
        if not phase_results:
            return {"overall_score": 0.0}

        # Calculate various metrics
        metrics = {
            "overall_score": 0.85,  # Simplified
            "phase_completion_rate": 0.9,
            "quality_average": 0.88,
            "timeline_adherence": 0.82,
            "deliverable_completeness": 0.91
        }

        return metrics

    def _generate_phase_recommendations(self, phase: str, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for phase."""
        recommendations = []

        if not validation_result["deliverables_valid"]:
            missing = validation_result.get("missing_deliverables", [])
            recommendations.append(f"Complete missing deliverables: {', '.join(missing)}")

        if validation_result["quality_score"] < 0.8:
            recommendations.append("Improve deliverable quality before proceeding")

        if validation_result["completion_score"] < 0.8:
            recommendations.append("Complete remaining phase activities")

        if not recommendations:
            recommendations.append("Phase completion criteria met")

        return recommendations