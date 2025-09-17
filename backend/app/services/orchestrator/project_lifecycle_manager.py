"""Project lifecycle management service - handles project state transitions and lifecycle events."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.task import Task, TaskStatus
from app.database.models import TaskDB, ProjectDB
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)

# SDLC Phases configuration (extracted from original orchestrator)
SDLC_PHASES = {
    "discovery": {
        "name": "Discovery",
        "description": "Requirements gathering and initial analysis",
        "agent_sequence": ["analyst"],
        "completion_criteria": ["user_input_analyzed", "requirements_gathered"],
        "estimated_duration_hours": 4,
        "max_duration_hours": 6,
        "time_pressure_threshold": 0.8,
        "parallel_execution": False,
        "time_based_decisions": {
            "overtime_action": "escalate_to_hitl",
            "efficiency_bonus": "reduce_analysis_depth"
        },
        "next_phase": "plan"
    },
    "plan": {
        "name": "Plan",
        "description": "Technical planning and architecture design",
        "agent_sequence": ["architect"],
        "completion_criteria": ["architecture_defined", "technical_plan_created"],
        "estimated_duration_hours": 8,
        "max_duration_hours": 12,
        "time_pressure_threshold": 0.75,
        "parallel_execution": False,
        "time_based_decisions": {
            "overtime_action": "simplify_architecture",
            "efficiency_bonus": "add_performance_optimization"
        },
        "next_phase": "design"
    },
    "design": {
        "name": "Design",
        "description": "Detailed design and API specification",
        "agent_sequence": ["architect", "analyst"],
        "completion_criteria": ["api_specs_defined", "data_models_created", "design_reviewed"],
        "estimated_duration_hours": 12,
        "max_duration_hours": 18,
        "time_pressure_threshold": 0.7,
        "parallel_execution": True,
        "time_based_decisions": {
            "overtime_action": "prioritize_critical_components",
            "efficiency_bonus": "enhance_design_quality"
        },
        "next_phase": "build"
    },
    "build": {
        "name": "Build",
        "description": "Code implementation and development",
        "agent_sequence": ["coder"],
        "completion_criteria": ["code_implemented", "unit_tests_passed", "code_reviewed"],
        "estimated_duration_hours": 24,
        "max_duration_hours": 36,
        "time_pressure_threshold": 0.6,
        "parallel_execution": False,
        "time_based_decisions": {
            "overtime_action": "focus_on_core_features",
            "efficiency_bonus": "add_advanced_features"
        },
        "next_phase": "validate"
    },
    "validate": {
        "name": "Validate",
        "description": "Testing and quality assurance",
        "agent_sequence": ["tester"],
        "completion_criteria": ["tests_executed", "quality_gates_passed", "performance_validated"],
        "estimated_duration_hours": 8,
        "max_duration_hours": 12,
        "time_pressure_threshold": 0.8,
        "parallel_execution": False,
        "time_based_decisions": {
            "overtime_action": "prioritize_critical_tests",
            "efficiency_bonus": "comprehensive_testing"
        },
        "next_phase": "launch"
    },
    "launch": {
        "name": "Launch",
        "description": "Deployment and production release",
        "agent_sequence": ["deployer"],
        "completion_criteria": ["deployment_verified", "production_tests_passed", "rollback_plan_ready"],
        "estimated_duration_hours": 4,
        "max_duration_hours": 8,
        "time_pressure_threshold": 0.9,
        "parallel_execution": False,
        "time_based_decisions": {
            "overtime_action": "staged_rollout",
            "efficiency_bonus": "full_production_deployment"
        },
        "next_phase": None
    }
}


class ProjectLifecycleManager:
    """Manages project state transitions and lifecycle events."""

    def __init__(self, db: Session):
        self.db = db
        self.current_project_phases = {}  # Track current phase per project

    def create_project(self, name: str, description: str = None) -> UUID:
        """Create new project with initial state."""
        project = ProjectDB(
            name=name,
            description=description,
            status="active"
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        # Initialize to discovery phase
        self.set_current_phase(project.id, "discovery")

        logger.info("Project created", project_id=project.id, name=name)

        return project.id

    def get_current_phase(self, project_id: UUID) -> str:
        """Get the current SDLC phase for a project."""
        return self.current_project_phases.get(str(project_id), "discovery")

    def set_current_phase(self, project_id: UUID, phase: str):
        """Set the current SDLC phase for a project."""
        if phase not in SDLC_PHASES:
            raise ValueError(f"Invalid phase: {phase}")
        self.current_project_phases[str(project_id)] = phase
        logger.info("Project phase updated", project_id=project_id, phase=phase)

    def validate_phase_completion(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """
        Validate if a phase has met its completion criteria.

        Args:
            project_id: UUID of the project
            phase: Phase to validate

        Returns:
            Dict with validation results
        """
        if phase not in SDLC_PHASES:
            return {"valid": False, "error": f"Invalid phase: {phase}"}

        phase_config = SDLC_PHASES[phase]
        completion_criteria = phase_config["completion_criteria"]

        # Get project tasks for this phase
        project_tasks = self.get_project_tasks(project_id)
        phase_tasks = [task for task in project_tasks if task.agent_type in phase_config["agent_sequence"]]

        # Check completion criteria
        completed_criteria = []
        missing_criteria = []

        for criterion in completion_criteria:
            if self._check_completion_criterion(project_id, phase, criterion, phase_tasks):
                completed_criteria.append(criterion)
            else:
                missing_criteria.append(criterion)

        all_completed = len(missing_criteria) == 0
        completion_percentage = len(completed_criteria) / len(completion_criteria) * 100

        result = {
            "valid": all_completed,
            "phase": phase,
            "completion_percentage": completion_percentage,
            "completed_criteria": completed_criteria,
            "missing_criteria": missing_criteria,
            "total_criteria": len(completion_criteria),
            "project_id": str(project_id)
        }

        logger.info("Phase validation completed",
                   project_id=project_id,
                   phase=phase,
                   valid=all_completed,
                   completion_percentage=completion_percentage)

        return result

    def transition_to_next_phase(self, project_id: UUID) -> Dict[str, Any]:
        """
        Transition project to the next SDLC phase if current phase is completed.

        Args:
            project_id: UUID of the project

        Returns:
            Dict with transition results
        """
        current_phase = self.get_current_phase(project_id)

        # Validate current phase completion
        validation_result = self.validate_phase_completion(project_id, current_phase)

        if not validation_result["valid"]:
            return {
                "success": False,
                "error": "Current phase not completed",
                "current_phase": current_phase,
                "validation_result": validation_result
            }

        # Get next phase
        next_phase = SDLC_PHASES[current_phase].get("next_phase")

        if not next_phase:
            return {
                "success": False,
                "error": "Project is in final phase",
                "current_phase": current_phase,
                "validation_result": validation_result
            }

        # Transition to next phase
        self.set_current_phase(project_id, next_phase)

        result = {
            "success": True,
            "previous_phase": current_phase,
            "current_phase": next_phase,
            "validation_result": validation_result
        }

        logger.info("Phase transition completed",
                   project_id=project_id,
                   previous_phase=current_phase,
                   current_phase=next_phase)

        return result

    def get_phase_progress(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive progress information for all phases.

        Args:
            project_id: UUID of the project

        Returns:
            Dict with progress information
        """
        current_phase = self.get_current_phase(project_id)
        all_phases_progress = {}

        for phase_name in SDLC_PHASES.keys():
            validation_result = self.validate_phase_completion(project_id, phase_name)
            all_phases_progress[phase_name] = {
                "completed": validation_result["valid"],
                "completion_percentage": validation_result["completion_percentage"],
                "is_current": phase_name == current_phase,
                "phase_config": SDLC_PHASES[phase_name]
            }

        # Calculate overall project progress
        total_phases = len(SDLC_PHASES)
        completed_phases = sum(1 for phase in all_phases_progress.values() if phase["completed"])
        overall_progress = (completed_phases / total_phases) * 100

        result = {
            "project_id": str(project_id),
            "current_phase": current_phase,
            "overall_progress": overall_progress,
            "completed_phases": completed_phases,
            "total_phases": total_phases,
            "phases": all_phases_progress
        }

        return result

    def get_project_tasks(self, project_id: UUID) -> List[Task]:
        """Get all tasks for a project."""
        db_tasks = self.db.query(TaskDB).filter(TaskDB.project_id == project_id).all()

        tasks = []
        for db_task in db_tasks:
            task = Task(
                id=db_task.id,
                project_id=db_task.project_id,
                agent_type=db_task.agent_type,
                instructions=db_task.instructions,
                status=TaskStatus(db_task.status),
                context_ids=[UUID(cid) for cid in db_task.context_ids] if db_task.context_ids else [],
                result=db_task.result,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at
            )
            tasks.append(task)

        return tasks

    def _check_completion_criterion(self, project_id: UUID, phase: str, criterion: str, phase_tasks: List[Task]) -> bool:
        """
        Check if a specific completion criterion is met.

        Args:
            project_id: UUID of the project
            phase: Current phase
            criterion: Criterion to check
            phase_tasks: Tasks for this phase

        Returns:
            Boolean indicating if criterion is met
        """
        # Basic completion logic - can be extended
        if criterion == "user_input_analyzed":
            return any(task.status == TaskStatus.COMPLETED and "analyze" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "requirements_gathered":
            return any(task.status == TaskStatus.COMPLETED and "requirements" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "architecture_defined":
            return any(task.status == TaskStatus.COMPLETED and "architecture" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "technical_plan_created":
            return any(task.status == TaskStatus.COMPLETED and "plan" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "api_specs_defined":
            return any(task.status == TaskStatus.COMPLETED and "api" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "data_models_created":
            return any(task.status == TaskStatus.COMPLETED and "model" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "design_reviewed":
            return any(task.status == TaskStatus.COMPLETED and "review" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "code_implemented":
            return any(task.status == TaskStatus.COMPLETED and "implement" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "unit_tests_passed":
            return any(task.status == TaskStatus.COMPLETED and "test" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "code_reviewed":
            return any(task.status == TaskStatus.COMPLETED and "review" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "tests_executed":
            return any(task.status == TaskStatus.COMPLETED and "test" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "quality_gates_passed":
            return any(task.status == TaskStatus.COMPLETED and "quality" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "performance_validated":
            return any(task.status == TaskStatus.COMPLETED and "performance" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "deployment_verified":
            return any(task.status == TaskStatus.COMPLETED and "deploy" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "production_tests_passed":
            return any(task.status == TaskStatus.COMPLETED and "production" in task.instructions.lower()
                      for task in phase_tasks)
        elif criterion == "rollback_plan_ready":
            return any(task.status == TaskStatus.COMPLETED and "rollback" in task.instructions.lower()
                      for task in phase_tasks)

        # Default: check if any related task is completed
        return any(task.status == TaskStatus.COMPLETED for task in phase_tasks)